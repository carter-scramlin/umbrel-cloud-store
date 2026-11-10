#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Create a localhost-only integration environment outside the app package."""
import argparse
from pathlib import Path
import secrets
import os
import shutil
import subprocess
import yaml

p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--port',type=int,default=18390);p.add_argument('--no-files',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parents[1]
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
photos=out/'umbrel-photos';photos.mkdir(exist_ok=True);photos.chmod(0o755)
folder=out/'umbrel-files';folder.mkdir(exist_ok=True);folder.chmod(0o777)
# Exercise the same rendered template and pre-start hook Umbrel uses on updates.
shutil.copyfile(root/'drive-runtime.b64.template',out/'drive-runtime.b64')
subprocess.run(['bash',str(root/'hooks/pre-start')],env={**os.environ,'APP_DATA_DIR':str(out)},check=True)
c=yaml.safe_load((root/'docker-compose.yml').read_text())
c['services'].pop('app_proxy')
c['services']['web']['ports']=[f'127.0.0.1:{args.port}:80']
c['services']['web']['environment']['NEXTCLOUD_TRUSTED_DOMAINS']=f'localhost 127.0.0.1 localhost:{args.port} 127.0.0.1:{args.port}'
for service in c['services'].values():
 service['restart']='no'
 service['volumes']=[v.replace('${APP_DATA_DIR}/data',str(out/'data')).replace('${APP_DATA_DIR}/server',str(out/'server')).replace('${APP_DATA_DIR}',str(root)) for v in service.get('volumes',[])]
if not args.no_files:
 for name in ['web','cron']:
  c['services'][name]['volumes'].append(str(folder)+':/umbrel-files')
  c['services'][name]['volumes'].append(str(photos)+':/umbrel-photos:ro')
(out/'compose.yml').write_text(yaml.safe_dump(c,sort_keys=False))
password=secrets.token_urlsafe(32)
(out/'test.env').write_text('APP_PASSWORD='+password+'\nAPP_DOMAIN=localhost\n')
(out/'test.env').chmod(0o600)
(out/'password.txt').write_text(password);(out/'password.txt').chmod(0o600)
print('Prepared isolated test environment:',out)
