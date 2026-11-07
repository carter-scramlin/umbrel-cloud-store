"""Umbrel Drive HTTP API and single-account file store."""
import contextlib
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import sqlite3
import sys
import tempfile
import threading
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

HERE = Path(__file__).resolve().parent
MAX_UPLOAD = 2 * 1024**3
SESSION_AGE = 7 * 86400
TOKEN_AGE = 365 * 86400
CHUNK = 1024**2
COOKIE = "umbrel_drive"
STATIC = {"/": "index.html", "/style.css": "style.css", "/drive.js": "drive.js",
          "/manifest.webmanifest": "manifest.webmanifest", "/sw.js": "sw.js",
          "/icon.svg": "icon.svg", "/icon-192.png": "icon-192.png",
          "/icon-512.png": "icon-512.png"}


class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def file_path(value):
    if (not isinstance(value, str) or not value or len(value.encode()) > 1024
            or any(ord(char) < 32 or char in '\\:*?"<>|' for char in value)):
        raise APIError(400, "Invalid file path")
    if any(part in ("", ".", "..") or len(part.encode()) > 255 for part in value.split("/")):
        raise APIError(400, "Invalid path component")
    return value


class Store:
    def __init__(self, root):
        self.root = root
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.blobs = root / "objects"
        self.blobs.mkdir(mode=0o700, exist_ok=True)
        with self.database() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS revisions (
                    id INTEGER PRIMARY KEY, path TEXT NOT NULL, hash TEXT,
                    size INTEGER NOT NULL, time INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS revision_path ON revisions(path, id);
                CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, rev INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS keys (
                    hash TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL,
                    expires INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS shares (
                    hash TEXT PRIMARY KEY, label TEXT NOT NULL, rev INTEGER NOT NULL,
                    expires INTEGER NOT NULL
                );
            """)
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('id',?)", (secrets.token_hex(24),))

    @contextlib.contextmanager
    def database(self):
        with contextlib.closing(sqlite3.connect(self.root / "drive.sqlite", timeout=15)) as db:
            db.row_factory = sqlite3.Row
            with db:
                yield db

    @staticmethod
    def current(db, path):
        return db.execute("SELECT revisions.* FROM files JOIN revisions ON rev=id WHERE files.path=?",
                          (path,)).fetchone()

    def put(self, path, expected, hash_, size, staged=None):
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            return self.write_revision(db, path, expected, hash_, size, staged)

    def move(self, source, expected, destination, destination_revision):
        if source == destination:
            raise APIError(400, "Choose a different destination")
        with self.database() as db:
            db.execute("BEGIN IMMEDIATE")
            original = self.current(db, source)
            if original is None or original["hash"] is None:
                raise APIError(404, "Source file not found")
            existing = self.current(db, destination)
            if existing and existing["hash"] is not None:
                raise APIError(409, "A file already uses the destination")
            self.write_revision(db, source, expected, None, 0)
            return self.write_revision(db, destination, destination_revision,
                                       original["hash"], original["size"])

    def write_revision(self, db, path, expected, hash_, size, staged=None):
        current = self.current(db, path)
        if (current["id"] if current else 0) != expected:
            raise APIError(409, "File changed. Refresh and try again.")
        if hash_ is None and (current is None or current["hash"] is None):
            raise APIError(404, "File is already in Trash or missing")
        if current and current["hash"] == hash_:
            return dict(current)
        if hash_ is not None:
            parts = path.split("/")
            for index in range(1, len(parts)):
                parent = self.current(db, "/".join(parts[:index]))
                if parent and parent["hash"] is not None:
                    raise APIError(409, "A parent path is already a file")
            child = db.execute("""
                SELECT 1 FROM files JOIN revisions ON rev=id
                WHERE files.path > ? AND files.path < ? AND hash IS NOT NULL LIMIT 1
            """, (path + "/", path + "0")).fetchone()
            if child:
                raise APIError(409, "A folder already uses this name")
            destination = self.blobs / hash_
            if staged and not destination.exists():
                os.replace(staged, destination)
                descriptor = os.open(self.blobs, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            if not destination.is_file():
                raise APIError(500, "Stored content is missing")
        cursor = db.execute("INSERT INTO revisions(path,hash,size,time) VALUES (?,?,?,?)",
                            (path, hash_, size, int(time.time())))
        db.execute("INSERT INTO files VALUES (?,?) ON CONFLICT(path) DO UPDATE SET rev=excluded.rev",
                   (path, cursor.lastrowid))
        return dict(self.current(db, path))


class DriveHTTP(ThreadingHTTPServer):
    daemon_threads = True
    slots = threading.BoundedSemaphore(24)

    def __init__(self, address, store, password):
        super().__init__(address, Handler)
        self.store = store
        self.password = digest(password)
        self.login_lock = threading.Lock()
        self.login_failures = []

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.0 closes after each request, including rejected streaming uploads.
    timeout = 60

    @property
    def store(self):
        return self.server.store

    def log_message(self, format, *args):
        # URLs can contain share credentials. Never log request targets.
        return

    def reply(self, status, content=b"", kind="application/json", headers=(), public=False):
        self.start(status, len(content), kind, headers, public)
        self.wfile.write(content)

    def start(self, status, length, kind, headers=(), public=False):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-cache" if public else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'")
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()

    def json(self, data, status=200, headers=()):
        self.reply(status, json.dumps(data).encode(), headers=headers)

    def length(self, limit):
        if self.headers.get("Transfer-Encoding"):
            raise APIError(400, "Content-Length is required")
        values = self.headers.get_all("Content-Length", [])
        if len(values) != 1 or not re.fullmatch(r"[0-9]{1,16}", values[0]):
            raise APIError(411, "Content-Length is required")
        length = int(values[0])
        if length > limit:
            raise APIError(413, "Upload exceeds the size limit")
        return length

    def body(self):
        length = self.length(8192)
        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            raise APIError(400, "Invalid JSON")
        if not isinstance(body, dict):
            raise APIError(400, "Expected a JSON object")
        return body

    def authenticate(self, write=False, session_only=False):
        bearer = self.headers.get("Authorization", "")
        if bearer.startswith("Bearer "):
            value = bearer[7:]
            kind = "device"
        else:
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            value = cookies[COOKIE].value if COOKIE in cookies else ""
            kind = "session"
        if not value or (session_only and kind != "session"):
            raise APIError(401, "Sign in to Umbrel Drive")
        if write and kind == "session" and self.headers.get("X-Drive-Request") != "1":
            raise APIError(403, "Missing request header")
        key = digest(value)
        with self.store.database() as db:
            if not db.execute("SELECT 1 FROM keys WHERE hash=? AND kind=? AND expires>?",
                              (key, kind, int(time.time()))).fetchone():
                raise APIError(401, "Session expired or device key revoked")
        return key

    def login(self):
        if self.headers.get("X-Drive-Request") != "1":
            raise APIError(403, "Missing request header")
        password = self.body().get("password")
        if not isinstance(password, str):
            raise APIError(400, "Password is required")
        with self.server.login_lock:
            now = time.monotonic()
            failures = self.server.login_failures
            failures[:] = [timestamp for timestamp in failures if now - timestamp < 60]
            if len(failures) >= 10:
                raise APIError(429, "Too many attempts. Try again in a minute.")
            if not hmac.compare_digest(digest(password), self.server.password):
                failures.append(now)
                raise APIError(401, "Incorrect app password")
        token = secrets.token_urlsafe(32)
        with self.store.database() as db:
            now = int(time.time())
            db.execute("DELETE FROM keys WHERE expires<=?", (now,))
            db.execute("INSERT INTO keys VALUES (?,?,?,?)",
                       (digest(token), "session", "", now + SESSION_AGE))
        self.json({"ok": True}, headers=(("Set-Cookie", f"{COOKIE}={token}; Path=/; "
                                          f"Max-Age={SESSION_AGE}; HttpOnly; Secure; SameSite=Strict"),))

    def serve_file(self, row, name=None):
        if row is None or row["hash"] is None:
            raise APIError(404, "File not found")
        name = name or row["path"].split("/")[-1]
        with (self.store.blobs / row["hash"]).open("rb") as source:
            self.start(200, row["size"], "application/octet-stream",
                       (("Content-Disposition", "attachment; filename*=UTF-8''" + quote(name, safe="")),
                        ("ETag", '"' + row["hash"] + '"')))
            shutil.copyfileobj(source, self.wfile, CHUNK)

    def upload(self, path, expected):
        length = self.length(MAX_UPLOAD)
        with self.store.database() as db:
            current = self.store.current(db, path)
            if (current["id"] if current else 0) != expected:
                raise APIError(409, "File changed. Refresh and try again.")
        hash_ = hashlib.sha256()
        with tempfile.NamedTemporaryFile(dir=self.store.blobs, prefix=".incoming-", delete=False) as temp:
            staged = Path(temp.name)
            try:
                remaining = length
                while remaining:
                    block = self.rfile.read(min(CHUNK, remaining))
                    if not block:
                        raise APIError(400, "Upload ended early")
                    temp.write(block)
                    hash_.update(block)
                    remaining -= len(block)
                temp.flush()
                os.fsync(temp.fileno())
                row = self.store.put(path, expected, hash_.hexdigest(), length, staged)
            finally:
                staged.unlink(missing_ok=True)
        self.json(row)

    def dispatch(self):
        try:
            self.route()
        except APIError as error:
            self.json({"error": str(error)}, error.status)
        except (ConnectionError, socket.timeout):
            pass
        except (OSError, sqlite3.Error, UnicodeError) as error:
            print(f"Drive request failed: {type(error).__name__}", file=sys.stderr)
            try:
                self.json({"error": "Drive storage is unavailable"}, 500)
            except OSError:
                pass

    do_GET = do_POST = do_PUT = do_DELETE = dispatch

    def route(self):
        try:
            url = urlsplit(self.path)
        except ValueError:
            raise APIError(400, "Invalid URL")
        endpoint = url.path
        method = self.command
        if method == "GET" and endpoint == "/health":
            with self.store.database() as db:
                db.execute("SELECT 1 FROM files LIMIT 1")
            return self.json({"ok": True})
        if method == "GET" and endpoint in STATIC:
            asset = HERE / STATIC[endpoint]
            kind = ("application/manifest+json" if endpoint == "/manifest.webmanifest"
                    else mimetypes.guess_type(asset)[0] or "application/octet-stream")
            return self.reply(200, asset.read_bytes(), kind, public=True)
        if method == "GET" and re.fullmatch(r"/s/[A-Za-z0-9_-]{43}", endpoint):
            with self.store.database() as db:
                row = db.execute("SELECT revisions.* FROM shares JOIN revisions ON rev=id "
                                 "WHERE shares.hash=? AND expires>?",
                                 (digest(endpoint[3:]), int(time.time()))).fetchone()
            return self.serve_file(row)
        if method == "POST" and endpoint == "/api/login":
            return self.login()
        if not endpoint.startswith("/api/"):
            raise APIError(404, "Page not found")
        admin = endpoint in ("/api/devices", "/api/shares", "/api/logout", "/api/linux")
        key = self.authenticate(method != "GET", session_only=admin)
        query = parse_qs(url.query, keep_blank_values=True, max_num_fields=8) if url.query.count("&") < 8 else {}
        with self.store.database() as db:
            if endpoint == "/api/logout" and method == "POST":
                db.execute("DELETE FROM keys WHERE hash=?", (key,))
                db.commit()
                return self.json({"ok": True}, headers=(("Set-Cookie",
                    f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"),))
            if endpoint == "/api/linux" and method == "GET":
                source = HERE.parent / "linux" / "sync.py"
                return self.reply(200, source.read_bytes(), "application/octet-stream",
                                  (("Content-Disposition", "attachment; filename=umbrel-drive-sync.py"),))
            if endpoint == "/api/identity" and method == "GET":
                return self.json({"id": db.execute("SELECT value FROM metadata WHERE key='id'").fetchone()[0]})
            if endpoint == "/api/files" and method == "GET":
                rows = db.execute("SELECT revisions.* FROM files JOIN revisions ON rev=id ORDER BY files.path")
                return self.json([dict(row) for row in rows])
            if endpoint == "/api/devices":
                return self.devices(db, method)
            if endpoint == "/api/shares":
                return self.shares(db, method)
            if endpoint not in ("/api/file", "/api/history", "/api/restore", "/api/move"):
                raise APIError(404, "Endpoint not found")
            path = file_path(query.get("path", [""])[0])
            if endpoint == "/api/history" and method == "GET":
                return self.json([dict(row) for row in db.execute(
                    "SELECT * FROM revisions WHERE path=? ORDER BY id DESC", (path,))])
            if endpoint == "/api/file" and method == "GET":
                revision = query.get("rev", [""])[0]
                row = (db.execute("SELECT * FROM revisions WHERE path=? AND id=?", (path, revision)).fetchone()
                       if revision else self.store.current(db, path))
                return self.serve_file(row)
        expected = self.headers.get("X-Drive-Revision", "")
        if not re.fullmatch(r"[0-9]{1,18}", expected):
            raise APIError(428, "Expected revision is required")
        expected = int(expected)
        if endpoint == "/api/file" and method == "PUT":
            return self.upload(path, expected)
        if endpoint == "/api/file" and method == "DELETE":
            return self.json(self.store.put(path, expected, None, 0))
        if endpoint == "/api/move" and method == "POST":
            body = self.body()
            destination = file_path(body.get("destination"))
            destination_revision = body.get("destinationRevision")
            if type(destination_revision) is not int or not 0 <= destination_revision < 10**18:
                raise APIError(400, "Invalid destination revision")
            return self.json(self.store.move(path, expected, destination, destination_revision))
        if endpoint == "/api/restore" and method == "POST":
            revision = self.body().get("rev")
            if type(revision) is not int or not 0 < revision < 10**18:
                raise APIError(400, "Invalid revision")
            with self.store.database() as db:
                row = db.execute("SELECT * FROM revisions WHERE path=? AND id=? AND hash IS NOT NULL",
                                 (path, revision)).fetchone()
            if row is None:
                raise APIError(404, "Version not found")
            return self.json(self.store.put(path, expected, row["hash"], row["size"]))
        raise APIError(405, HTTPStatus.METHOD_NOT_ALLOWED.phrase)

    def devices(self, db, method):
        if method == "GET":
            return self.json([dict(row) for row in db.execute(
                "SELECT hash AS id,name,expires FROM keys WHERE kind='device' AND expires>? ORDER BY name",
                (int(time.time()),))])
        if method == "POST":
            name = self.body().get("name")
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 64:
                raise APIError(400, "Enter a device name of 1–64 characters")
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO keys VALUES (?,?,?,?)",
                       (digest(token), "device", name.strip(), int(time.time()) + TOKEN_AGE))
            db.commit()
            return self.json({"token": token}, 201)
        if method == "DELETE":
            key = self.body().get("id")
            if not isinstance(key, str):
                raise APIError(400, "Invalid key")
            db.execute("DELETE FROM keys WHERE hash=? AND kind='device'", (key,))
            db.commit()
            return self.json({"ok": True})
        raise APIError(405, "Method not allowed")

    def shares(self, db, method):
        now = int(time.time())
        if method == "GET":
            return self.json([dict(row) for row in db.execute(
                "SELECT hash AS id,label,expires FROM shares WHERE expires>? ORDER BY expires", (now,))])
        if method == "POST":
            body = self.body()
            path = file_path(body.get("path"))
            hours = body.get("hours", 24)
            if type(hours) is not int or not 1 <= hours <= 168:
                raise APIError(400, "Choose an expiry between 1 and 168 hours")
            db.execute("BEGIN IMMEDIATE")
            row = self.store.current(db, path)
            if row is None or row["hash"] is None:
                raise APIError(404, "File not found")
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO shares VALUES (?,?,?,?)",
                       (digest(token), path, row["id"], now + hours * 3600))
            db.commit()
            return self.json({"url": "/s/" + token}, 201)
        if method == "DELETE":
            key = self.body().get("id")
            if not isinstance(key, str):
                raise APIError(400, "Invalid share")
            db.execute("DELETE FROM shares WHERE hash=?", (key,))
            db.commit()
            return self.json({"ok": True})
        raise APIError(405, "Method not allowed")


def main():
    password = os.environ.get("DRIVE_PASSWORD", "")
    if len(password) < 16:
        sys.exit("Set DRIVE_PASSWORD to a generated app password of at least 16 characters.")
    os.umask(0o077)
    store = Store(Path(os.environ.get("DRIVE_DATA", "/data")))
    address = (os.environ.get("DRIVE_BIND", "0.0.0.0"), int(os.environ.get("DRIVE_PORT", "8080")))
    with DriveHTTP(address, store, password) as server:
        print(f"Umbrel Drive listening on {address[0]}:{address[1]}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
