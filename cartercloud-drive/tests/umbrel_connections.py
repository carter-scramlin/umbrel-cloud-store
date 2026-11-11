#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Carter Cloud
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Owner-only connection settings, CSRF, exact tailnet hosts and Files copy safety."""
import html
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
import unittest
from integration import ADMIN, BASE, PASSWORD, USER, request

PATH = '/apps/umbreldrive'


def browser(user, password):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    page = opener.open(BASE + '/login', timeout=30).read().decode()
    token = html.unescape(re.search(r'data-requesttoken="([^"]+)"', page)[1])
    data = urllib.parse.urlencode({'user': user, 'password': password, 'requesttoken': token}).encode()
    page = opener.open(urllib.request.Request(BASE + '/login', data=data,
        headers={'Origin': BASE, 'Referer': BASE + '/login'}), timeout=60).read().decode()
    return opener, html.unescape(re.search(r'data-requesttoken="([^"]+)"', page)[1])


def call(opener, path, data=None, token=None, **headers):
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
    headers.update({'Origin': BASE, 'Referer': BASE + PATH + '/files', 'X-Requested-With': 'XMLHttpRequest'})
    if token is not None:
        headers['requesttoken'] = token
    try:
        with opener.open(urllib.request.Request(BASE + path, data=data, headers=headers), timeout=45) as r:
            return r.status, r.read(), r.headers
    except urllib.error.HTTPError as r:
        try:
            return r.code, r.read(), r.headers
        finally:
            r.close()


class Connections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner, cls.token = browser('umbrel', ADMIN)
        assert request('/ocs/v2.php/cloud/users?format=json', 'POST',
            {'userid': USER, 'password': PASSWORD}, 'umbrel', ADMIN)[0] == 200
        cls.member, cls.member_token = browser(USER, PASSWORD)
        cls.previous = json.loads(call(cls.owner, PATH + '/connections')[1])['remoteAddress']

    @classmethod
    def tearDownClass(cls):
        call(cls.owner, PATH + '/remote', {'address': cls.previous}, cls.token)
        request('/ocs/v2.php/cloud/users/' + USER + '?format=json', 'DELETE', user='umbrel', password=ADMIN)

    def test_01_connection_state_is_private_and_not_cached(self):
        status, body, headers = call(self.owner, PATH + '/connections')
        self.assertEqual(status, 200)
        owner = json.loads(body)
        self.assertTrue(owner['owner'])
        self.assertEqual(set(owner['libraries']), {'files', 'photos'})
        self.assertIn('no-store', headers['Cache-Control'])
        status, body, _ = call(self.member, PATH + '/connections')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {'owner': False, 'libraries': [], 'remoteAddress': ''})
        anonymous = urllib.request.build_opener()
        self.assertIn(call(anonymous, PATH + '/connections')[0], (401, 403))

    def test_02_only_owner_with_csrf_can_register(self):
        data = {'address': 'https://umbrel.tail123.ts.net:8390'}
        self.assertIn(call(self.owner, PATH + '/remote', data, 'invalid')[0], (401, 403, 412))
        self.assertEqual(call(self.member, PATH + '/remote', data, self.member_token)[0], 403)
        before = json.loads(call(self.owner, PATH + '/connections')[1])['remoteAddress']
        for address in ['https://public.example.com', 'https://100.63.1.1:8390', 'https://100.128.1.1:8390',
                'https://evil.ts.net.example.com', 'https://bad..tail.ts.net', 'https://-bad.tail.ts.net', 'https://user:secret@umbrel.tail123.ts.net',
                'https://umbrel.tail123.ts.net/a', 'https://umbrel.tail123.ts.net?q=secret', 'ftp://100.88.1.1',
                'https://100.88.1.1:0', 'https://100.88.1.1:65536']:
            self.assertEqual(call(self.owner, PATH + '/remote', {'address': address}, self.token)[0], 400, address)
        self.assertEqual(json.loads(call(self.owner, PATH + '/connections')[1])['remoteAddress'], before)

    def test_03_register_replace_clear_exact_host(self):
        first = 'drive-' + uuid.uuid4().hex + '.tail-test.ts.net'
        other = 'drive-' + uuid.uuid4().hex + '.tail-test.ts.net'
        for host in [first, other]:
            status, body, _ = call(self.owner, PATH + '/remote', {'address': 'https://' + host + ':8390/'}, self.token)
            self.assertEqual(status, 200, body)
            self.assertEqual(json.loads(body)['address'], 'https://' + host + ':8390')
            self.assertEqual(call(self.owner, PATH + '/connections', Host=host)[0], 200)
        self.assertEqual(call(self.owner, PATH + '/connections', Host=first)[0], 400, 'Replaced managed hostname must be removed')
        self.assertEqual(call(self.owner, PATH + '/remote', {'address': ''}, self.token)[0], 200)
        self.assertEqual(call(self.owner, PATH + '/connections', Host=other)[0], 400)
        for address in ['http://100.88.1.2:8391', 'https://[fd7a:115c:a1e0::1]:8390', 'HTTPS://100.88.1.2:8390']:
            status, body, _ = call(self.owner, PATH + '/remote', {'address': address}, self.token)
            self.assertEqual(status, 200, body)
            self.assertEqual(json.loads(body)['address'], address.replace('HTTPS://', 'https://'))
            self.assertEqual(call(self.owner, PATH + '/connections', Host=urllib.parse.urlsplit(address).netloc)[0], 200)

    def test_04_copy_to_files_preserves_original_and_conflict(self):
        name = 'copy-to-files-' + uuid.uuid4().hex + ' café.txt'
        source = '/remote.php/dav/files/umbrel/' + urllib.parse.quote(name)
        destination = '/remote.php/dav/files/umbrel/Umbrel%20Files/' + urllib.parse.quote(name)
        def owner(path, method='GET', data=None, headers=None):
            return request(path, method, data, 'umbrel', ADMIN, headers)
        try:
            self.assertEqual(owner(source, 'PUT', b'original')[0], 201)
            headers = {'Destination': BASE + destination, 'Overwrite': 'F'}
            self.assertEqual(owner(source, 'COPY', headers=headers)[0], 201)
            self.assertEqual(owner(source)[1], b'original')
            self.assertEqual(owner(destination)[1], b'original')
            self.assertEqual(owner(source, 'PUT', b'new source')[0], 204)
            self.assertIn(owner(source, 'COPY', headers=headers)[0], (409, 412))
            self.assertEqual(owner(destination)[1], b'original')
        finally:
            owner(source, 'DELETE')
            owner(destination, 'DELETE')


    def test_05_http_native_login_flow_waits_for_approval(self):
        status, body, _ = request('/index.php/login/v2', 'POST', b'', user=None)
        self.assertEqual(status, 200)
        flow = json.loads(body)
        self.assertTrue(flow['login'].startswith(BASE + '/'))
        self.assertTrue(flow['poll']['endpoint'].startswith(BASE + '/'))
        poll = urllib.parse.urlsplit(flow['poll']['endpoint']).path
        self.assertEqual(request(poll, 'POST', {'token': flow['poll']['token']}, user=None)[0], 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
