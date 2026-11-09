#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Carter Cloud
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload-only, dated Linux folder backups for Umbrel Drive. Never deletes files."""
import argparse
import base64
from datetime import datetime, timezone
import fnmatch
import getpass
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Server redirected a backup request. Configure the final HTTPS server address.')


class Backup:
    def __init__(self, config):
        self.config = config
        url = urllib.parse.urlsplit(config['url'])
        if url.scheme != 'https' or not url.netloc or url.username or url.query or url.fragment:
            raise ValueError('Use the final HTTPS server URL without credentials, a query, or a fragment.')
        context = ssl.create_default_context(cafile=config.get('ca_file'))
        self.opener = urllib.request.build_opener(NoRedirects(), urllib.request.HTTPSHandler(context=context))
        self.root = config['url'].rstrip('/') + '/remote.php/dav/files/' + urllib.parse.quote(config['user'], safe='')
        self.auth = 'Basic ' + base64.b64encode((config['user'] + ':' + config['password']).encode()).decode()

    def request(self, path, method, data=None, size=None):
        headers = {'Authorization': self.auth, 'User-Agent':'UmbrelDriveBackup/1.0'}
        if size is not None: headers['Content-Length'] = str(size)
        if method == 'PUT': headers['If-None-Match'] = '*'
        req = urllib.request.Request(self.root + '/' + urllib.parse.quote(path, safe='/'),
                                     method=method, data=data, headers=headers)
        try:
            with self.opener.open(req, timeout=300) as response:
                return response.status
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            if method == 'MKCOL' and status == 405: return status
            raise RuntimeError(f'{method} failed with HTTP {status}: {path}') from None

    def folder(self, path):
        parts = path.split('/')
        for i in range(1, len(parts)+1): self.request('/'.join(parts[:i]), 'MKCOL')

    def run(self):
        local = Path(self.config['folder']).expanduser().resolve(strict=True)
        if not local.is_dir(): raise ValueError('Backup source must be a folder.')
        device = self.config.get('device', socket.gethostname())
        if not device or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in device):
            raise ValueError('Device name must contain only letters, digits, dashes, or underscores.')
        snapshot = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%SZ-') + uuid.uuid4().hex[:8]
        remote = 'Backups/' + device + '/' + snapshot
        self.folder(remote + '/files')
        manifest = []
        for directory, dirs, files in os.walk(local, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(directory)/d).is_symlink())
            relative_dir = Path(directory).relative_to(local).as_posix()
            if relative_dir != '.':
                if any(fnmatch.fnmatch(relative_dir, p) for p in self.config.get('exclude', [])):
                    dirs[:] = []; continue
                self.folder(remote + '/files/' + relative_dir)
            for name in sorted(files):
                path = Path(directory)/name
                if path.is_symlink(): continue
                relative = path.relative_to(local).as_posix()
                if any(fnmatch.fnmatch(relative, p) for p in self.config.get('exclude', [])): continue
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as stream:
                    before = os.fstat(stream.fileno())
                    if not stat.S_ISREG(before.st_mode): continue
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    stream.seek(0)
                    self.request(remote + '/files/' + relative, 'PUT', stream, before.st_size)
                    after = os.fstat(stream.fileno())
                    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        raise RuntimeError(f'Source changed during backup: {relative}. Snapshot is incomplete; retry.')
                manifest.append({'path': relative, 'size': before.st_size, 'sha256': digest})
                print('Backed up:', relative)
        payload = json.dumps({'format':1,'files':manifest}, indent=2).encode()
        self.request(remote + '/.umbrel-backup-complete.json', 'PUT', payload, len(payload))
        print('Backup complete:', remote)
        return manifest


def configure(args):
    config = dict(url=args.url.rstrip('/'), user=args.user, folder=str(args.folder.expanduser().resolve()),
                  device=args.device, exclude=args.exclude, password=getpass.getpass('Device app password: '))
    if args.ca_file: config['ca_file'] = str(args.ca_file.resolve())
    Backup(config)
    args.config.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(args.config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: json.dump(config, f)
    print('Saved private configuration:', args.config)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, default=Path.home()/'.config/umbrel-drive/backup.json')
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('configure')
    c.add_argument('--url', required=True); c.add_argument('--user', required=True)
    c.add_argument('--folder', type=Path, required=True)
    c.add_argument('--device', default=socket.gethostname().split('.')[0])
    c.add_argument('--ca-file', type=Path);c.add_argument('--exclude', action='append', default=[])
    sub.add_parser('run')
    args = p.parse_args()
    if args.command == 'configure': configure(args)
    else:
        if args.config.stat().st_mode & 0o077:
            raise ValueError('Backup configuration must be private: chmod 600 ' + str(args.config))
        Backup(json.loads(args.config.read_text())).run()


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr);sys.exit(1)
