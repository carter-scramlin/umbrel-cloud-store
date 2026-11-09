#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the browser cookie/CSRF login flow, not HTTP Basic authentication."""
import html
import http.cookiejar
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

BASE = os.environ.get('DRIVE_TEST_URL', 'http://127.0.0.1:18390')
PASSWORD = os.environ.get('DRIVE_TEST_PASSWORD') or Path(os.environ['DRIVE_TEST_PASSWORD_FILE']).read_text().strip()


def check_browser(opener=None):
    opener = opener or urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for _ in range(12):
        with opener.open(BASE + '/login', timeout=30) as response:
            assert response.status == 200
            page = response.read().decode()
            assert 'Internal Server Error' not in page
    token = re.search(r'data-requesttoken="([^"]+)"', page)
    assert token, 'Login page did not provide a CSRF token'
    data = urllib.parse.urlencode({'user': 'umbrel', 'password': PASSWORD,
                                  'requesttoken': html.unescape(token[1])}).encode()
    with opener.open(urllib.request.Request(BASE + '/login', data=data,
                     headers={'Referer': BASE + '/login', 'Origin': BASE}), timeout=60) as response:
        assert response.status == 200
        assert '/login' not in response.url, 'Cookie-based login did not complete'
        assert 'Internal Server Error' not in response.read().decode()
    with opener.open(BASE + '/apps/umbreldrive/', timeout=30) as response:
        assert response.status == 200
        page = response.read().decode()
        assert 'One folder. Every device.' in page
        assert 'Your server address' in page
    # This request must retain the browser's authenticated session.
    with opener.open(BASE + '/remote.php/dav/files/umbrel/Readme.md', timeout=30) as response:
        assert response.status == 200
        assert b'Welcome to Umbrel Drive' in response.read()
    print('PASS: repeated login page rendering, cookie/CSRF sign-in, Files access, and setup page')


if __name__ == '__main__':
    check_browser()
