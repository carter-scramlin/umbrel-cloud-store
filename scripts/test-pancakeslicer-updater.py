#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import yaml

spec = importlib.util.spec_from_file_location("updater", Path(__file__).with_name("update-pancakeslicer.py"))
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)
DIGEST = "sha256:" + "a" * 64


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = Path(self.tmp.name) / "app"
        shutil.copytree(updater.APP, self.app)
        self.current = yaml.safe_load((self.app / "umbrel-app.yml").read_text())["version"]
        self.next = "99.0.0"

    def apply(self, tag=None, **extra):
        return updater.update({"tag_name": tag or "v" + self.next, **extra}, lambda tag: DIGEST, self.app)

    def test_new_release_updates_image_version_and_notes_together(self):
        self.assertTrue(self.apply())
        manifest = yaml.safe_load((self.app / "umbrel-app.yml").read_text())
        compose = yaml.safe_load((self.app / "docker-compose.yml").read_text())
        self.assertEqual(manifest["version"], self.next)
        self.assertIn("/releases/tag/v" + self.next, manifest["releaseNotes"])
        self.assertEqual(compose["services"]["server"]["image"], f"{updater.IMAGE}:{self.next}@{DIGEST}")
        self.assertFalse(self.apply())

    def test_same_old_draft_and_prerelease_do_not_change_files(self):
        before = {p.name: p.read_bytes() for p in self.app.iterdir() if p.is_file()}
        for tag, extra in [("v" + self.current, {}), ("v0.0.1", {}), (None, {"draft": True}), (None, {"prerelease": True})]:
            self.assertFalse(self.apply(tag, **extra))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.app.iterdir() if p.is_file()})

    def test_malformed_tag_rejected(self):
        with self.assertRaises(ValueError):
            self.apply("v1.0.0-rc1")

    def test_unavailable_image_leaves_both_files_unchanged(self):
        before = (self.app / "umbrel-app.yml").read_bytes()
        compose = (self.app / "docker-compose.yml").read_bytes()
        def missing(tag):
            raise ValueError("image not yet published")
        with self.assertRaises(ValueError):
            updater.update({"tag_name": "v" + self.next}, missing, self.app)
        self.assertEqual(before, (self.app / "umbrel-app.yml").read_bytes())
        self.assertEqual(compose, (self.app / "docker-compose.yml").read_bytes())

    def test_multiarchitecture_required(self):
        for arches, good in [(["amd64"], False), (["amd64", "arm64"], True)]:
            raw = json.dumps({"manifests": [{"platform": {"os": "linux", "architecture": arch}} for arch in arches]}).encode()
            with patch.object(updater, "request", side_effect=[b'{"token":"test"}', raw]):
                if good:
                    self.assertRegex(updater.image_digest("1.0.0"), r"^sha256:[0-9a-f]{64}$")
                else:
                    with self.assertRaises(ValueError):
                        updater.image_digest("1.0.0")


if __name__ == "__main__":
    unittest.main()
