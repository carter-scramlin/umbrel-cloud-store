#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real Chunking v2 interoperability, retry, conflict and cancellation checks.

Run only on the isolated test server. Each test uses a disposable Drive account.
"""
import hashlib
import uuid
import unittest
from integration import DriveIntegration, request, BASE, USER


class ChunkUpload(DriveIntegration):
    # Reuse account lifecycle, not the unrelated inherited workflow tests.
    def make_upload(self, name):
        folder = '/remote.php/dav/uploads/' + USER + '/release-' + uuid.uuid4().hex
        headers = {'Destination': BASE + self.root + name, 'OC-Total-Length': str(8 * 1024 * 1024 + 19)}
        self.assertEqual(request(folder, 'MKCOL', headers=headers)[0], 201)
        self.addCleanup(lambda: request(folder, 'DELETE'))
        return folder, headers

    def test_08_chunks_retry_preserve_exact_content(self):
        folder, headers = self.make_upload('chunked%20caf%C3%A9.bin')
        first = b'0123456789abcdef' * (8 * 1024 * 1024 // 16)
        last = b'final nineteen byte'
        self.assertEqual(len(last), 19)
        for _ in range(2):  # A lost response can cause the same chunk to be sent again.
            self.assertIn(request(folder + '/00001', 'PUT', first, headers=headers)[0], (201, 204))
        self.assertEqual(request(folder + '/00002', 'PUT', last, headers=headers)[0], 201)
        self.assertEqual(request(folder + '/.file', 'MOVE', headers={**headers, 'Overwrite': 'F'})[0], 201)
        status, body, _ = request(self.root + 'chunked%20caf%C3%A9.bin')
        self.assertEqual(status, 200)
        self.assertEqual(hashlib.sha256(body).digest(), hashlib.sha256(first + last).digest())
        self.assertEqual(request(folder, 'PROPFIND', headers={'Depth': '0'})[0], 404)

    def test_11_above_previous_browser_limit(self):
        import base64
        import urllib.request
        from integration import PASSWORD
        folder, headers = self.make_upload('large-257-MiB.bin')
        length = 257 * 1024 * 1024
        headers['OC-Total-Length'] = str(length)
        chunk = b'0123456789abcdef' * (8 * 1024 * 1024 // 16)
        digest = hashlib.sha256()
        for offset in range(0, length, len(chunk)):
            data = chunk[:min(len(chunk), length - offset)]
            digest.update(data)
            self.assertEqual(request(folder + '/' + str(offset // len(chunk) + 1).zfill(5), 'PUT', data, headers=headers)[0], 201)
        self.assertEqual(request(folder + '/.file', 'MOVE', headers={**headers, 'Overwrite':'F'})[0], 201)
        auth = base64.b64encode((USER + ':' + PASSWORD).encode()).decode()
        downloaded = hashlib.sha256()
        count = 0
        with urllib.request.urlopen(urllib.request.Request(BASE + self.root + 'large-257-MiB.bin',
                headers={'Authorization':'Basic ' + auth}), timeout=120) as response:
            while data := response.read(1024 * 1024):
                downloaded.update(data)
                count += len(data)
        self.assertEqual(count, length)
        self.assertEqual(downloaded.digest(), digest.digest())

    def test_09_chunked_conflict_cannot_replace_existing_file(self):
        name = 'keep-original.bin'
        self.assertEqual(request(self.root + name, 'PUT', b'original bytes')[0], 201)
        folder, headers = self.make_upload(name)
        self.assertEqual(request(folder + '/00001', 'PUT', b'replacement', headers=headers)[0], 201)
        self.assertIn(request(folder + '/.file', 'MOVE', headers={**headers, 'Overwrite': 'F'})[0], (409, 412))
        self.assertEqual(request(self.root + name)[1], b'original bytes')

    def test_10_cancel_removes_chunks_without_publishing_file(self):
        folder, headers = self.make_upload('canceled.bin')
        self.assertEqual(request(folder + '/00001', 'PUT', b'incomplete', headers=headers)[0], 201)
        self.assertEqual(request(folder, 'DELETE')[0], 204)
        self.assertEqual(request(folder, 'PROPFIND', headers={'Depth': '0'})[0], 404)
        self.assertEqual(request(self.root + 'canceled.bin')[0], 404)


if __name__ == '__main__':
    suite = unittest.TestSuite(ChunkUpload(name) for name in (
        'test_08_chunks_retry_preserve_exact_content',
        'test_09_chunked_conflict_cannot_replace_existing_file',
        'test_10_cancel_removes_chunks_without_publishing_file',
        'test_11_above_previous_browser_limit',
    ))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
