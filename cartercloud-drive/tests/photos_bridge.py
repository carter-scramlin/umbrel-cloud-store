#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Selected native photo originals: read-only DAV, account isolation and explicit sharing."""
import json
import os
from pathlib import Path
import unittest
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
from integration import ADMIN, PASSWORD, USER, request
from files_bridge import eventually, owner

PHOTOS = Path(os.environ['DRIVE_TEST_PHOTOS_DIR'])


class PhotosBridge(unittest.TestCase):
    def test_readonly_originals_and_explicit_share(self):
        name = 'photo-original-' + uuid.uuid4().hex + '.jpg'
        source = PHOTOS / name
        original = b'disposable photo-original fixture\x00\xff\xd8\xff'
        source.write_bytes(original)
        path = '/remote.php/dav/files/umbrel/Umbrel%20Photos/' + name
        created_user = False
        share_id = None
        try:
            eventually(lambda: owner(path)[0] == 200, 'Native photo original was not indexed')
            self.assertEqual(owner(path)[1], original)
            status, body, _ = owner('/remote.php/dav/files/umbrel/Umbrel%20Photos/', 'PROPFIND', '<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:permissions/></d:prop></d:propfind>', headers={'Depth':'0','Content-Type':'application/xml'})
            self.assertEqual(status, 207)
            permissions = ET.fromstring(body).find('.//{http://owncloud.org/ns}permissions').text or ''
            self.assertNotIn('C', permissions)
            self.assertNotIn('K', permissions)
            self.assertEqual(owner(path, 'PUT', b'replace')[0], 403)
            self.assertEqual(owner(path, 'DELETE')[0], 403)
            self.assertEqual(owner('/remote.php/dav/files/umbrel/Umbrel%20Photos/no-new-file', 'PUT', b'new')[0], 403)
            self.assertEqual(source.read_bytes(), original)
            status, body, _ = owner('/ocs/v2.php/cloud/users?format=json', 'POST', {'userid':USER, 'password':PASSWORD})
            self.assertEqual(status, 200, body)
            created_user = True
            self.assertEqual(request('/remote.php/dav/files/' + USER + '/Umbrel%20Photos/' + name)[0], 404)
            status, body, _ = owner('/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json', 'POST',
                {'path':'/Umbrel Photos/' + name, 'shareType':0, 'shareWith':USER, 'permissions':1})
            self.assertEqual(status, 200, body)
            share_id = json.loads(body)['ocs']['data']['id']
            self.assertEqual(request('/remote.php/dav/files/' + USER + '/' + name)[1], original)
            self.assertEqual(request('/remote.php/dav/files/' + USER + '/' + name, 'PUT', b'other account')[0], 403)
        finally:
            if share_id:
                owner('/ocs/v2.php/apps/files_sharing/api/v1/shares/' + str(share_id) + '?format=json', 'DELETE')
            if created_user:
                owner('/ocs/v2.php/cloud/users/' + USER + '?format=json', 'DELETE')
            source.unlink(missing_ok=True)


if __name__ == '__main__':unittest.main(verbosity=2)
