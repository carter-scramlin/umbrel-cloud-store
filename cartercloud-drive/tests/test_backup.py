# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import http.server
import threading
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('backup', Path(__file__).parents[1]/'clients/backup.py')
module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class TestBackup(unittest.TestCase):
    def test_snapshot_excludes_symlinks_preserves_empty_folders_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'empty').mkdir();(root/'note.txt').write_bytes(b'hello')
            (root/'ignored.tmp').write_bytes(b'skip');(root/'link').symlink_to('/etc/passwd')
            backup=module.Backup.__new__(module.Backup)
            backup.config={'folder':str(root),'device':'test-device','exclude':['*.tmp']}
            requests=[]
            def record(path, method, data=None, size=None):
                content=data.read() if hasattr(data,'read') else data
                requests.append((path,method,content,size));return 201
            backup.request=record
            result=backup.run()
            puts=[r for r in requests if r[1]=='PUT']
            self.assertEqual(len(puts),2)
            self.assertEqual(puts[0][2],b'hello')
            self.assertEqual(puts[0][3],5)
            self.assertEqual(result[0]['sha256'],'2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824')
            self.assertTrue(any(r[0].endswith('/files/empty') for r in requests))
            self.assertTrue(puts[-1][0].endswith('/.umbrel-backup-complete.json'))
            self.assertEqual(json.loads(puts[-1][2])['files'],result)
            self.assertTrue(all(r[1] in ('MKCOL','PUT') for r in requests))

    def test_interrupted_upload_never_marks_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'one').write_text('one')
            b=module.Backup.__new__(module.Backup);b.config={'folder':directory,'device':'test'}
            seen=[]
            def fail(path,method,data=None,size=None):
                seen.append(path)
                if method=='PUT': raise RuntimeError('network interruption')
            b.request=fail
            with self.assertRaisesRegex(RuntimeError,'network interruption'): b.run()
            self.assertFalse(any('complete.json' in x for x in seen))

    def test_requires_https_and_refuses_embedded_credentials(self):
        for url in ['http://umbrel.local','https://user:secret@example.com','https://example.com/?token=secret','https://example.com:0','https://example.com:65536']:
            with self.assertRaises(ValueError): module.Backup({'url':url})

    def test_http_requires_boolean_opt_in(self):
        for flag in [False, 'true', 'false', 1, None]:
            with self.assertRaises(ValueError):
                module.Backup({'url':'http://127.0.0.1:8391', 'allow_http':flag})

    def test_explicit_http_sends_authenticated_no_overwrite_request(self):
        seen=[]
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_PUT(self):
                seen.append((self.path, self.headers.get('Authorization'),
                    self.headers.get('If-None-Match'), self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(201);self.end_headers()
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            b=module.Backup({'url':f'http://127.0.0.1:{server.server_port}', 'user':'test-user',
                'password':'disposable-test-secret', 'allow_http':True})
            self.assertEqual(b.request('folder/café.txt','PUT',b'hello',5),201)
            self.assertEqual(seen, [('/remote.php/dav/files/test-user/folder/caf%C3%A9.txt',
                'Basic dGVzdC11c2VyOmRpc3Bvc2FibGUtdGVzdC1zZWNyZXQ=', '*', b'hello')])
        finally:
            server.shutdown();server.server_close();worker.join(timeout=3)

    def test_rejects_cross_host_redirect(self):
        with self.assertRaises(RuntimeError):
            module.NoRedirects().redirect_request(None,None,302,'',{},'https://evil.example')


if __name__=='__main__': unittest.main(verbosity=2)
