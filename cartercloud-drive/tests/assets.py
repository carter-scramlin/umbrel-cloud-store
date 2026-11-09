#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Static bundle integrity and encoding negotiation, including older clients."""
import gzip
import os
import subprocess
import urllib.request

BASE = os.environ.get('DRIVE_TEST_URL', 'http://127.0.0.1:18390')


def fetch(path, encoding):
    with urllib.request.urlopen(urllib.request.Request(BASE + path,
            headers={'Accept-Encoding': encoding}), timeout=60) as response:
        assert response.status == 200
        return response.read(), response.headers


def check_assets():
    assert 'brotli/' in subprocess.check_output(['curl', '--version'], text=True), 'curl needs Brotli support'
    for path in ['/dist/core-common.js?v=drive-test', '/core/css/server.css?v=drive-test',
                 '/custom_apps/umbreldrive/css/drive.css?v=drive-test']:
        plain, identity = fetch(path, 'identity')
        gz, gzip_headers = fetch(path, 'gzip')
        br, brotli_headers = fetch(path, 'br, gzip')
        assert identity.get('Content-Encoding') is None
        assert gzip_headers.get('Content-Encoding') == 'gzip'
        assert brotli_headers.get('Content-Encoding') == 'br', 'Brotli missing or double compressed'
        assert 'accept-encoding' in brotli_headers.get('Vary', '').lower()
        assert 'immutable' in brotli_headers.get('Cache-Control', '')
        assert gzip.decompress(gz) == plain
        decoded = subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                     '--compressed', '--header', 'Accept-Encoding: br', BASE + path])
        assert decoded == plain, 'Brotli changed the decoded asset'
        assert len(br) < len(gz)
        print(f'PASS: {path.split("?")[0]} identity={len(plain)} gzip={len(gz)} br={len(br)} bytes')
    # Dynamic application endpoints retain the upstream encoding path.
    _, status_headers = fetch('/status.php', 'br, gzip')
    assert status_headers.get('Content-Encoding') != 'br'


if __name__ == '__main__':
    check_assets()
