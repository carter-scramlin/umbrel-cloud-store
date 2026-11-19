#!/usr/bin/env python3
"""Isolated Docker smoke/persistence check of the packaged services (not Umbrel UI)."""
import json
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="pancakeslicer-test-") as tmp:
        tmp = Path(tmp)
        compose = yaml.safe_load((ROOT / "cartercloud-pancakeslicer/docker-compose.yml").read_text())
        del compose["services"]["app_proxy"]
        for service in compose["services"].values():
            service["volumes"] = [v.replace("${APP_DATA_DIR}", str(tmp)) for v in service.get("volumes", [])]
        path = tmp / "compose.yml"
        path.write_text(yaml.safe_dump(compose))
        cmd = ["docker", "compose", "-p", "pancakeslicer-smoke", "-f", str(path)]

        def run(*args):
            return subprocess.check_output([*cmd, *args], text=True).strip()

        client_image = "python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e"
        client = """import json,sys,urllib.request
path, payload = sys.argv[1:]
req = urllib.request.Request('http://server:6868' + path)
if payload:
    req = urllib.request.Request(req.full_url, data=payload.encode(), method='PUT', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as response:
    sys.stdout.buffer.write(response.read())
"""

        def request(route, payload=""):
            return subprocess.check_output(["docker", "run", "--rm", "--network", "pancakeslicer-smoke_default", client_image, "python", "-c", client, route, payload])

        def ready():
            for _ in range(90):
                try:
                    health = json.loads(request("/api/healthz"))
                    if health.get("artifact_state") == "qualified":
                        return
                except subprocess.CalledProcessError:
                    pass
                time.sleep(2)
            raise RuntimeError("PancakeSlicer failed to become ready")

        try:
            run("up", "-d")
            ready()
            for route, minimum in [("/", 500), ("/profiles/BBL/Bambu%20Lab%20A1%20mini_cover.png", 1000), ("/profiles/BBL/bbl-3dp-A1M.stl", 1000)]:
                assert len(request(route)) >= minimum, route
            value = json.loads(request("/api/preferences"))
            document = {"theme": "dark", "carterCloudPersistenceCheck": True}
            payload = {"operationId": str(uuid.uuid4()), "expectedRevision": value.get("revision", 0), "document": document}
            request("/api/preferences", json.dumps(payload))
            run("up", "-d", "--force-recreate")
            ready()
            saved = json.loads(request("/api/preferences"))
            assert saved["document"] == document, saved
            print("PASS: qualified engine, web UI, printer profile assets, preferences write, and persistence after recreation")
        finally:
            print(run("logs", "--tail", "30"))
            run("down", "--remove-orphans")
            # The nonroot image owns its bind mount; use the helper to clean only test data.
            helper = compose["services"]["permissions"]["image"]
            subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{tmp}/data:/data", helper, "sh", "-ec", "rm -rf /data/* /data/.[!.]* /data/..?*"], check=True)


if __name__ == "__main__":
    main()
