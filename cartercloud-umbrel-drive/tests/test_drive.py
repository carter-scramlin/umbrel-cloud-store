"""Run with python -B -m unittest discover -s tests -v."""
import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

APP = Path(__file__).resolve().parents[1]
PASSWORD = "test-password-never-used-in-production"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, APP / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server = load("server", "app/server.py")
agent = load("agent", "linux/sync.py")


class DriveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = server.Store(self.root / "data")
        self.http = server.DriveHTTP(("127.0.0.1", 0), self.store, PASSWORD)
        self.addCleanup(self.http.server_close)
        self.url = f"http://127.0.0.1:{self.http.server_port}"
        thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.http.shutdown)
        status, headers, _ = self.request("/api/login", "POST", {"password": PASSWORD})
        self.assertEqual(status, 200)
        self.assertIn("Secure; SameSite=Strict", headers["Set-Cookie"])
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, body = self.request("/api/devices", "POST", {"name": "Test Linux"}, session=True)
        self.assertEqual(status, 201)
        self.token = json.loads(body)["token"]
        self.client = agent.Client(self.url, self.token, allow_loopback_http=True)

    def request(self, path, method="GET", body=None, session=False, token=False, expected=None, csrf=True):
        headers = {"X-Drive-Request": "1"} if csrf else {}
        if session:
            headers["Cookie"] = self.cookie
        if token:
            headers["Authorization"] = "Bearer " + self.token
        if expected is not None:
            headers["X-Drive-Revision"] = str(expected)
        if isinstance(body, dict):
            body = json.dumps(body).encode()
        request = Request(self.url + path, data=body, headers=headers, method=method)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def put(self, path, content, revision=0):
        status, _, body = self.request("/api/" + agent.endpoint(path), "PUT", content, token=True, expected=revision)
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def test_revision_trash_share_and_revoke(self):
        self.assertEqual(self.request("/api/files")[0], 401)
        self.assertEqual(self.request("/api/devices", token=True)[0], 401)
        self.assertEqual(self.request("/api/shares", "POST", {"path": "test"}, session=True, csrf=False)[0], 403)
        old = self.put("Notes/file.txt", b"first")
        status, _, body = self.request("/api/shares", "POST", {"path": old["path"]}, session=True)
        self.assertEqual(status, 201)
        link = json.loads(body)["url"]
        new = self.put(old["path"], b"second", old["id"])
        endpoint = "/api/" + agent.endpoint(old["path"])
        self.assertEqual(self.request(endpoint, "DELETE", token=True, expected=old["id"])[0], 409)
        status, _, body = self.request(endpoint, "DELETE", token=True, expected=new["id"])
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(body)["hash"])
        self.assertEqual(self.request(endpoint, token=True)[0], 404)
        self.assertEqual(self.request(link)[2], b"first")
        restore = endpoint.replace("/file?", "/restore?")
        self.assertEqual(self.request(restore, "POST", {"rev": old["id"]}, session=True,
                                      expected=json.loads(body)["id"])[0], 200)
        self.assertEqual(self.request(endpoint, token=True)[2], b"first")
        share = json.loads(self.request("/api/shares", session=True)[2])[0]
        self.assertEqual(self.request("/api/shares", "DELETE", {"id": share["id"]}, session=True)[0], 200)
        self.assertEqual(self.request(link)[0], 404)
        key = json.loads(self.request("/api/devices", session=True)[2])[0]
        self.assertEqual(self.request("/api/devices", "DELETE", {"id": key["id"]}, session=True)[0], 200)
        self.assertEqual(self.request(endpoint, token=True)[0], 401)

    def test_concurrent_writers_and_path_rules(self):
        row = self.put("team/plan.txt", b"original")
        endpoint = "/api/" + agent.endpoint(row["path"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda value: self.request(
                endpoint, "PUT", value, token=True, expected=row["id"])[0], [b"one", b"two"]))
        self.assertEqual(sorted(outcomes), [200, 409])
        for path, status in [("../outside", 400), ("team", 409), ("team/plan.txt/child", 409)]:
            self.assertEqual(self.request("/api/" + agent.endpoint(path), "PUT", b"x",
                                          token=True, expected=0)[0], status)
        reopened = server.Store(self.root / "data")
        with reopened.database() as db:
            current = reopened.current(db, row["path"])
            self.assertIn((reopened.blobs / current["hash"]).read_bytes(), [b"one", b"two"])

    def test_move_preserves_original_history_and_rolls_back_on_collision(self):
        original = self.put("photo.txt", b"first")
        self.put("folder/other.txt", b"existing")
        endpoint = "/api/move?path=photo.txt"
        options = {"session": True, "expected": original["id"]}
        self.assertEqual(self.request(endpoint, "POST", {"destination": "folder", "destinationRevision": 0},
                                      **options)[0], 409)
        self.assertEqual(self.request("/api/file?path=photo.txt", token=True)[2], b"first")
        self.assertEqual(self.request(endpoint, "POST", {"destination": "folder/photo.txt",
                                                        "destinationRevision": 0}, **options)[0], 200)
        self.assertEqual(self.request("/api/file?path=folder%2Fphoto.txt", token=True)[2], b"first")
        self.assertEqual(self.request("/api/file?path=photo.txt", token=True)[0], 404)
        self.assertEqual(self.request(f"/api/file?path=photo.txt&rev={original['id']}", token=True)[2], b"first")

    def job(self, mode="two-way", remote=""):
        folder = self.root / "local"
        folder.mkdir()
        return folder, {"folder": str(folder), "remote": remote, "mode": mode, "exclude": ["*.tmp"]}

    def test_two_way_conflicts_and_deletes(self):
        folder, config = self.job()
        state = self.root / "state.json"
        file = folder / "plan.txt"
        file.write_bytes(b"initial")
        (folder / "skip.tmp").write_bytes(b"excluded")
        agent.sync(self.client, config, state)
        row, = self.client.json("files")
        self.put("plan.txt", b"remote edit", row["id"])
        file.write_bytes(b"local edit")
        agent.sync(self.client, config, state)
        self.assertEqual(file.read_bytes(), b"remote edit")
        agent.sync(self.client, config, state)
        conflict, = folder.glob("*.conflict-*")
        self.assertEqual(conflict.read_bytes(), b"local edit")
        current = next(row for row in self.client.json("files") if row["path"] == "plan.txt")
        self.client.json(agent.endpoint("plan.txt"), "DELETE", expected=current["id"])
        agent.sync(self.client, config, state)
        self.assertFalse(file.exists())
        recovered, = (folder / agent.RECOVERY).glob("*/plan.txt")
        self.assertEqual(recovered.read_bytes(), b"remote edit")
        conflict.unlink()
        agent.sync(self.client, config, state)
        self.assertTrue(all(row["hash"] is None for row in self.client.json("files")))

    def test_backup_keeps_remote_when_local_is_deleted(self):
        folder, config = self.job("backup", "Backup")
        state = self.root / "backup.json"
        file = folder / "photo.txt"
        file.write_bytes(b"photo")
        agent.sync(self.client, config, state)
        file.unlink()
        agent.sync(self.client, config, state)
        row, = self.client.json("files")
        self.assertEqual(row["path"], "Backup/photo.txt")
        self.assertIsNotNone(row["hash"])

    def test_download_preserves_unsynced_local_edits(self):
        folder, config = self.job("download", "Remote")
        state = self.root / "download.json"
        file = folder / "image.txt"
        file.write_bytes(b"local")
        self.put("Remote/image.txt", b"remote")
        agent.sync(self.client, config, state)
        self.assertEqual(file.read_bytes(), b"remote")
        preserved, = (folder / agent.RECOVERY).glob("*/image.txt")
        self.assertEqual(preserved.read_bytes(), b"local")
        state.write_text(json.dumps({"identity": ["different server"], "files": {}}))
        with self.assertRaisesRegex(agent.SyncError, "settings changed"):
            agent.sync(self.client, config, state)


if __name__ == "__main__":
    unittest.main()
