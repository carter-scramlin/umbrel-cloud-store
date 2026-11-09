#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Selected-folder round trips, automatic indexing, sharing, and owner isolation."""
from pathlib import Path
import json
import os
import time
import unittest
import urllib.parse
import uuid

from integration import ADMIN, BASE, PASSWORD, USER, request

FOLDER = Path(os.environ['DRIVE_TEST_FILES_DIR'])
NAME = 'bridge-test-' + uuid.uuid4().hex
ROOT = '/remote.php/dav/files/umbrel/Umbrel%20Files/'


def owner(path, method='GET', data=None, headers=None):
    return request(path, method, data, 'umbrel', ADMIN, headers)


def eventually(predicate, message):
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(2)
    raise AssertionError(message)


class FilesBridge(unittest.TestCase):
    def test_files_round_trip_and_isolation(self):
        local = FOLDER / NAME
        local.mkdir()
        local.chmod(0o777)  # CI's checkout user can differ from Umbrel's UID 1000.
        (local / 'from-files.txt').write_text('Created in Umbrel Files\n')
        path = ROOT + NAME + '/'
        share_id = None
        created_user = False
        try:
            eventually(lambda: owner(path + 'from-files.txt')[0] == 200,
                       'Files-created file was not automatically indexed')
            self.assertEqual(owner(path + 'from-files.txt')[1], b'Created in Umbrel Files\n')
            self.assertEqual(owner(path + 'from-drive.txt', 'PUT', b'Created in Drive\n')[0], 201)
            self.assertEqual((local / 'from-drive.txt').read_bytes(), b'Created in Drive\n')
            self.assertEqual((local / 'from-drive.txt').stat().st_uid, 1000)
            self.assertEqual((local / 'from-drive.txt').stat().st_gid, 1000)
            before = owner(ROOT, 'PROPFIND', headers={'Depth': '0'})[1]
            # Edit deeply without browsing that subfolder: clients poll ancestor ETags.
            time.sleep(2)
            (local / 'from-files.txt').write_text('Changed in Files, different length\n')
            (local / 'from-files.txt').rename(local / 'renamed-in-files.txt')
            eventually(lambda: owner(ROOT, 'PROPFIND', headers={'Depth': '0'})[1] != before,
                       'Ancestor ETag did not change after a Files edit')
            eventually(lambda: owner(path + 'renamed-in-files.txt')[0] == 200,
                       'Files rename was not indexed')
            self.assertEqual(owner(path + 'from-files.txt')[0], 404)
            self.assertEqual(owner(path + 'renamed-in-files.txt')[1], b'Changed in Files, different length\n')
            self.assertEqual(owner(path + 'from-drive.txt', 'MOVE', headers={
                'Destination': BASE + path + 'renamed-in-drive.txt', 'Overwrite': 'F'})[0], 201)
            self.assertTrue((local / 'renamed-in-drive.txt').is_file())
            self.assertFalse((local / 'from-drive.txt').exists())

            status, body, _ = owner('/ocs/v2.php/cloud/users?format=json', 'POST',
                                    {'userid': USER, 'password': PASSWORD})
            self.assertEqual(status, 200, body)
            created_user = True
            self.assertEqual(request('/remote.php/dav/files/' + USER + '/Umbrel%20Files/', 'PROPFIND')[0], 404)
            status, body, _ = owner('/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json', 'POST',
                {'path': '/Umbrel Files/' + NAME, 'shareType': 0, 'shareWith': USER, 'permissions': 1})
            self.assertEqual(status, 200, body)
            share_id = json.loads(body)['ocs']['data']['id']
            self.assertEqual(request('/remote.php/dav/files/' + USER + '/' + NAME + '/renamed-in-drive.txt')[1],
                             b'Created in Drive\n')
            (local / 'renamed-in-files.txt').unlink()
            eventually(lambda: owner(path + 'renamed-in-files.txt')[0] == 404,
                       'Files deletion was not indexed')
            self.assertEqual(owner(path + 'renamed-in-drive.txt', 'DELETE')[0], 204)
            self.assertFalse((local / 'renamed-in-drive.txt').exists())
        finally:
            if share_id:
                owner('/ocs/v2.php/apps/files_sharing/api/v1/shares/' + str(share_id) + '?format=json', 'DELETE')
            if created_user:
                owner('/ocs/v2.php/cloud/users/' + USER + '?format=json', 'DELETE')
            owner(path, 'DELETE')
            # Only our unique disposable fixture is eligible for cleanup.
            if local.exists():
                import shutil
                shutil.rmtree(local)


if __name__ == '__main__':
    unittest.main(verbosity=2)
