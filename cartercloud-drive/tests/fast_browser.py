#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lightweight authenticated shell, small assets, and cookie/CSRF DAV writes."""
import html
import http.cookiejar
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = os.environ.get('DRIVE_TEST_URL', 'http://127.0.0.1:18390')
PASSWORD = os.environ.get('DRIVE_TEST_PASSWORD') or Path(os.environ['DRIVE_TEST_PASSWORD_FILE']).read_text().strip()
PATH = '/apps/umbreldrive/files'


def check_fast_browser():
    try:
        with urllib.request.urlopen(BASE + PATH, timeout=30) as response:
            assert '/login' in response.url, 'Anonymous visitors must not see the file browser'
    except urllib.error.HTTPError as failure:
        assert failure.code == 401, failure.code
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with opener.open(BASE + '/login', timeout=30) as response:
        login = response.read().decode()
    token = html.unescape(re.search(r'data-requesttoken="([^"]+)"', login)[1])
    data = urllib.parse.urlencode({'user': 'umbrel', 'password': PASSWORD, 'requesttoken': token}).encode()
    with opener.open(urllib.request.Request(BASE + '/login', data=data,
            headers={'Origin': BASE, 'Referer': BASE + '/login'}), timeout=60) as response:
        assert PATH in response.url, 'Ordinary sign-in should open the lightweight browser'
        page = response.read().decode()
        assert 'nonce-' in response.headers.get('Content-Security-Policy', ''), 'Keep CSP script nonces'
        assert 'no-store' in response.headers.get('Cache-Control', ''), 'Do not cache account HTML'
    assert 'Full workspace' in page and 'Devices &amp; Files' in page
    assert 'data-uid="umbrel"' in page
    assert 'core-common.js' not in page and '/dist/' not in page
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', page)
    styles = re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', page)
    assert len(scripts) == 1 and len(styles) == 1, 'Keep the initial browser independent of large bundles'
    total = 0
    for asset in scripts + styles:
        asset = html.unescape(asset)
        assert asset.startswith('/custom_apps/umbreldrive/') and '?v=' in asset
        with opener.open(BASE + asset, timeout=30) as response:
            total += len(response.read())
            assert 'immutable' in response.headers.get('Cache-Control', '')
    assert total < 100_000, f'Initial decoded JS/CSS budget exceeded: {total}'
    token = html.unescape(re.search(r'data-requesttoken="([^"]+)"', page)[1])
    path = '/remote.php/dav/files/umbrel/' + urllib.parse.quote('fast-browser-check-' + uuid.uuid4().hex + ' café #1 & notes.txt')
    headers = {'Origin': BASE, 'Referer': BASE + PATH, 'X-Requested-With': 'XMLHttpRequest'}
    try:
        try:
            opener.open(urllib.request.Request(BASE + path, data=b'blocked', method='PUT',
                headers={**headers, 'requesttoken': 'invalid', 'If-None-Match': '*'}), timeout=30)
            raise AssertionError('Cookie writes require a valid CSRF token')
        except urllib.error.HTTPError as failure:
            assert failure.code in (401, 403), failure.code
        with opener.open(urllib.request.Request(BASE + path, data=b'Browser cookie upload\n', method='PUT',
                headers={**headers, 'requesttoken': token, 'If-None-Match': '*'}), timeout=30) as response:
            assert response.status == 201
        with opener.open(BASE + path, timeout=30) as response:
            assert response.read() == b'Browser cookie upload\n'
    finally:
        try:
            opener.open(urllib.request.Request(BASE + path, method='DELETE', headers={**headers, 'requesttoken': token}), timeout=30).close()
        except urllib.error.HTTPError as failure:
            if failure.code != 404:
                raise
    print(f'PASS: authenticated fast entry, CSP/cache isolation, {total} decoded asset bytes, cookie/CSRF upload and encoding')


if __name__ == '__main__':
    check_fast_browser()
