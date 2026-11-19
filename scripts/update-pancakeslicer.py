#!/usr/bin/env python3
"""Publish stable releases only after their complete multi-architecture image exists."""
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "cartercloud-pancakeslicer"
IMAGE = "ghcr.io/zimengxiong/pancakeslicer"


def request(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "CarterCloud-PancakeSlicer", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def version(value):
    if not re.fullmatch(r"v?\d+\.\d+\.\d+", value):
        raise ValueError(f"Not a stable version: {value!r}")
    return tuple(map(int, value.removeprefix("v").split(".")))


def image_digest(tag):
    token = json.loads(request("https://ghcr.io/token?service=ghcr.io&scope=repository:zimengxiong/pancakeslicer:pull"))["token"]
    raw = request(f"https://ghcr.io/v2/zimengxiong/pancakeslicer/manifests/{tag}", {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json",
    })
    index = json.loads(raw)
    platforms = {(m.get("platform", {}).get("os"), m.get("platform", {}).get("architecture")) for m in index.get("manifests", [])}
    if not {("linux", "amd64"), ("linux", "arm64")} <= platforms:
        raise ValueError("Release image must support both linux/amd64 and linux/arm64")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def update(release, digest_lookup=image_digest, app=APP):
    if release.get("draft") or release.get("prerelease"):
        return False
    tag = release["tag_name"]
    new = version(tag)
    manifest_path = app / "umbrel-app.yml"
    manifest = manifest_path.read_text()
    current = re.search(r'^version: "([^"]+)"$', manifest, re.M).group(1)
    if new <= version(current):
        return False
    target = tag.removeprefix("v")
    digest = digest_lookup(target)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid image digest")
    compose_path = app / "docker-compose.yml"
    compose, count = re.subn(re.escape(IMAGE) + r':[^\s]+', f"{IMAGE}:{target}@{digest}", compose_path.read_text())
    if count != 1:
        raise ValueError("Expected exactly one PancakeSlicer image")
    manifest = re.sub(r'^version: "[^"]+"$', f'version: "{target}"', manifest, flags=re.M)
    # A bounded, YAML-escaped summary keeps upstream text out of executable workflow code.
    notes = f"PancakeSlicer {target}. Release details: https://github.com/ZimengXiong/PancakeSlicer/releases/tag/{tag}"
    manifest, count = re.subn(r'^releaseNotes:.*?(?=^developer:)', "releaseNotes: " + json.dumps(notes) + "\n", manifest, flags=re.M | re.S)
    if count != 1:
        raise ValueError("Expected one releaseNotes section")
    compose_path.write_text(compose)
    manifest_path.write_text(manifest)
    print(f"Prepared PancakeSlicer {target} ({digest})")
    return True


if __name__ == "__main__":
    headers = {}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    release = json.loads(request("https://api.github.com/repos/ZimengXiong/PancakeSlicer/releases/latest", headers))
    changed = update(release)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"changed={str(changed).lower()}\n")
    if not changed:
        print("No newer stable release.")
