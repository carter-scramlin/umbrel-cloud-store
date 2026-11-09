#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run only against the isolated Docker test instance; creates disposable users."""
import base64
from datetime import date, timedelta
from pathlib import Path
import json
import os
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.environ.get('DRIVE_TEST_URL', 'http://127.0.0.1:18390')
ADMIN = os.environ.get('DRIVE_TEST_PASSWORD') or Path(os.environ['DRIVE_TEST_PASSWORD_FILE']).read_text().strip()
NS = {'d':'DAV:', 'oc':'http://owncloud.org/ns', 'nc':'http://nextcloud.org/ns'}
USER = 'drive-test-' + str(int(time.time()))
PASSWORD = 'Testing-only-VeryLong-' + str(time.time_ns())


def request(path, method='GET', data=None, user=USER, password=PASSWORD, headers=None):
    h={'OCS-APIRequest':'true'}
    if user:
        h['Authorization']='Basic '+base64.b64encode(f'{user}:{password}'.encode()).decode()
    h.update(headers or {})
    if isinstance(data,dict):
        data=urllib.parse.urlencode(data).encode();h['Content-Type']='application/x-www-form-urlencoded'
    if isinstance(data,str): data=data.encode()
    req=urllib.request.Request(BASE+path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status,response.read(),response.headers
    except urllib.error.HTTPError as response:
        result = response.code,response.read(),response.headers
        response.close()
        return result


class DriveIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        status, body, _=request('/ocs/v2.php/cloud/users?format=json','POST',{'userid':USER,'password':PASSWORD},'umbrel',ADMIN)
        assert status==200,body
        assert json.loads(body)['ocs']['meta']['statuscode'] in (100,200),body
        cls.root='/remote.php/dav/files/'+USER+'/'

    @classmethod
    def tearDownClass(cls):
        request('/ocs/v2.php/cloud/users/'+USER+'?format=json','DELETE',user='umbrel',password=ADMIN)

    def test_01_branding_and_auth(self):
        s,b,_=request('/status.php',user=None);self.assertEqual(s,200);self.assertTrue(json.loads(b)['installed'])
        s,b,_=request(self.root,'PROPFIND',user=None);self.assertEqual(s,401)
        s,b,_=request('/ocs/v2.php/cloud/capabilities?format=json');self.assertEqual(s,200)
        data=json.loads(b)['ocs']['data']['capabilities'];self.assertEqual(data['theming']['name'],'Umbrel Drive')
        self.assertIn('files_sharing',data)

    def test_02_upload_conflict_download_move_copy(self):
        self.assertEqual(request(self.root+'Integration','MKCOL')[0],201)
        path=self.root+'Integration/hello%20world.txt'
        self.assertEqual(request(path,'PUT',b'first',headers={'If-None-Match':'*'})[0],201)
        s,b,h=request(path);self.assertEqual((s,b),(200,b'first'));etag=h['ETag']
        self.assertEqual(request(path,'PUT',b'data loss',headers={'If-Match':'"wrong"'})[0],412)
        self.assertEqual(request(path,'PUT',b'second',headers={'If-Match':etag})[0],204)
        destination=BASE+self.root+'Integration/copy.txt'
        self.assertEqual(request(path,'COPY',headers={'Destination':destination,'Overwrite':'F'})[0],201)
        self.assertEqual(request(self.root+'Integration/copy.txt','MOVE',headers={'Destination':BASE+self.root+'Integration/moved.txt','Overwrite':'F'})[0],201)
        self.assertEqual(request(self.root+'Integration/moved.txt')[1],b'second')

    def test_03_trash_restore_and_versions(self):
        path=self.root+'Integration/moved.txt'
        s,b,_=request(path,'PROPFIND','<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:fileid/></d:prop></d:propfind>',headers={'Depth':'0','Content-Type':'application/xml'});self.assertEqual(s,207)
        fileid=ET.fromstring(b).find('.//oc:fileid',NS).text
        version_path=self.root+'Integration/hello%20world.txt'
        s,b,_=request(version_path,'PROPFIND','<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:fileid/></d:prop></d:propfind>',headers={'Depth':'0','Content-Type':'application/xml'})
        version_id=ET.fromstring(b).find('.//oc:fileid',NS).text
        endpoint='/remote.php/dav/versions/'+USER+'/versions/'+version_id
        s,b,_=request(endpoint,'PROPFIND',headers={'Depth':'1'})
        self.assertEqual(s,207)
        hrefs=[e.text for e in ET.fromstring(b).findall('.//d:href',NS) if e.text.rstrip('/') != endpoint]
        self.assertTrue(hrefs, 'An overwritten file must have a previous version')
        version=hrefs[0]
        self.assertEqual(request(version)[1],b'first')
        self.assertEqual(request(version,'MOVE',headers={'Destination':BASE+'/remote.php/dav/versions/'+USER+'/restore/hello%20world.txt'})[0],201)
        self.assertEqual(request(version_path)[1],b'first')
        self.assertEqual(request(path,'DELETE')[0],204)
        s,b,_=request('/remote.php/dav/trashbin/'+USER+'/trash','PROPFIND','<d:propfind xmlns:d="DAV:" xmlns:nc="http://nextcloud.org/ns"><d:prop><nc:trashbin-filename/><nc:trashbin-original-location/></d:prop></d:propfind>',headers={'Depth':'1','Content-Type':'application/xml'})
        self.assertEqual(s,207);xml=ET.fromstring(b)
        entries=[e for e in xml.findall('d:response',NS) if e.find('.//nc:trashbin-filename',NS) is not None]
        item=next(e for e in entries if e.find('.//nc:trashbin-filename',NS).text=='moved.txt')
        href=item.find('d:href',NS).text
        self.assertEqual(request(href,'MOVE',headers={'Destination':BASE+'/remote.php/dav/trashbin/'+USER+'/restore/moved.txt'})[0],201)
        self.assertEqual(request(path)[1],b'second')

    def test_04_expiring_password_share_revoke(self):
        api='/ocs/v2.php/apps/files_sharing/api/v1/shares'
        s,b,_=request(api+'?format=json','POST',{'path':'/Integration/hello world.txt','shareType':3,'permissions':1,'password':'Share-Only-VeryLong-12345','expireDate':(date.today()+timedelta(days=7)).isoformat()})
        self.assertEqual(s,200,b);share=json.loads(b)['ocs']['data'];self.assertTrue(share['token'])
        s,b,_=request('/s/'+share['token'],user=None);self.assertEqual(s,200);self.assertIn(b'password',b.lower())
        self.assertEqual(request(api+'/'+str(share['id'])+'?format=json','DELETE')[0],200)
        self.assertEqual(request('/s/'+share['token'],user=None)[0],404)

    def test_05_upload_request_and_groups(self):
        api='/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'
        s,b,_=request(api,'POST',{'path':'/Integration','shareType':3,'permissions':4})
        self.assertEqual(s,200,b);self.assertEqual(json.loads(b)['ocs']['data']['permissions'],4)
        s,b,_=request('/ocs/v2.php/cloud/users/'+USER+'?format=json',user='umbrel',password=ADMIN)
        self.assertEqual(s,200);self.assertEqual(json.loads(b)['ocs']['data']['id'],USER)

    def test_06_setup_requires_login(self):
        # Basic auth is accepted by DAV/OCS; interactive routes use browser login.
        s,b,_=request('/apps/umbreldrive/',user=None)
        self.assertEqual(s,401);self.assertIn(b'not logged in',b)

    def test_07_account_isolation_and_quota(self):
        self.assertIn(request('/remote.php/dav/files/umbrel/Readme.md')[0],(403,404))
        endpoint='/ocs/v2.php/cloud/users/'+USER+'?format=json'
        s,b,_=request(endpoint,'PUT',{'key':'quota','value':'1 MB'},'umbrel',ADMIN)
        self.assertEqual(s,200,b)
        s,b,_=request(self.root+'too-large.bin','PUT',b'x'*(2*1024*1024))
        self.assertEqual(s,507,b[:300])


if __name__=='__main__': unittest.main(verbosity=2)
