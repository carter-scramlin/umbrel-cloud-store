#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Disposable Compose equivalent of Umbrel's folder-choice restart lifecycle."""
import argparse
import json
from pathlib import Path
import subprocess
import yaml

from files_bridge import ROOT, owner

p = argparse.ArgumentParser()
p.add_argument('--compose', type=Path, required=True)
p.add_argument('--env-file', required=True)
p.add_argument('--project', required=True)
p.add_argument('--fixtures', type=Path, required=True)
args = p.parse_args()
compose = yaml.safe_load(args.compose.read_text())
fixture = args.fixtures.resolve()
fixture.mkdir(parents=True, exist_ok=True)
folders = []
for name in ['a', 'b']:
    folder = fixture / name
    folder.mkdir(exist_ok=True)
    folder.chmod(0o777)
    (folder / 'same-name.txt').write_text(name)
    folders.append(folder)


def connect(folder):
    for service in ['web', 'cron']:
        volumes = compose['services'][service]['volumes']
        volumes[:] = [v for v in volumes if not v.endswith(':/umbrel-files')]
        if folder:
            volumes.append(str(folder) + ':/umbrel-files')
    args.compose.write_text(yaml.safe_dump(compose, sort_keys=False))
    subprocess.run(['docker', 'compose', '--env-file', args.env_file,
                    '-f', str(args.compose), '-p', args.project,
                    'up', '-d', '--wait', '--wait-timeout', '240'], check=True)


assert owner('/remote.php/dav/files/umbrel/persistence-test.txt', 'PUT', b'preserved')[0] in (201, 204)
connect(None)
assert owner(ROOT, 'PROPFIND')[0] == 404, 'No selected folder must mean no access'
connect(folders[0])
assert owner(ROOT + 'same-name.txt')[1] == b'a'
status, body, _ = owner('/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json', 'POST',
    {'path': '/Umbrel Files/same-name.txt', 'shareType': 3, 'permissions': 1})
assert status == 200, body
share = json.loads(body)['ocs']['data']
try:
    connect(folders[1])
    assert owner(ROOT + 'same-name.txt')[1] == b'b', 'Replacement folder not connected'
    from integration import request
    status, body, _ = request('/s/' + share['token'] + '/download', user=None)
    assert status != 200, 'Old public share must not expose the replacement folder'
    connect(None)
    assert owner(ROOT, 'PROPFIND')[0] == 404, 'Removing folder access left a mount visible'
    assert owner('/remote.php/dav/files/umbrel/persistence-test.txt')[1] == b'preserved'
    assert (folders[0] / 'same-name.txt').read_text() == 'a'
    assert (folders[1] / 'same-name.txt').read_text() == 'b'
    print('PASS: disconnect, reconnect, replacement-share isolation, and private-data persistence')
finally:
    owner('/ocs/v2.php/apps/files_sharing/api/v1/shares/' + str(share['id']) + '?format=json', 'DELETE')
    owner('/remote.php/dav/files/umbrel/persistence-test.txt', 'DELETE')
