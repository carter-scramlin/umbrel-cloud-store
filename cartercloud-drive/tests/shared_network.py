#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model Umbrel's shared network with another app occupying generic DNS names."""
import argparse
import json
from pathlib import Path
import subprocess
import uuid
import yaml

from browser_sessions import check_browser

p = argparse.ArgumentParser()
p.add_argument('--compose', type=Path, required=True)
p.add_argument('--env-file', required=True)
p.add_argument('--project', required=True)
args = p.parse_args()
assert args.project.startswith('umbrel-drive-'), 'Use a disposable Drive test project'
compose = ['docker', 'compose', '--env-file', args.env_file, '-f', str(args.compose), '-p', args.project]
web = subprocess.check_output(compose + ['ps', '-q', 'web'], text=True).strip()
info = json.loads(subprocess.check_output(['docker', 'inspect', web]))[0]
network = next(iter(info['NetworkSettings']['Networks']))
image = yaml.safe_load(args.compose.read_text())['services']['redis']['image']
name = args.project + '-dns-collision-' + uuid.uuid4().hex[:8]
subprocess.run(['docker', 'run', '-d', '--name', name, '--network', network,
                '--network-alias', 'db', '--network-alias', 'redis', image,
                'redis-server', '--requirepass', 'other-app-test-password',
                '--save', '', '--appendonly', 'no'], check=True, stdout=subprocess.DEVNULL)
try:
    script = ('echo json_encode([gethostbynamel("redis"),gethostbynamel("db"),'
              'gethostbynamel("cartercloud-drive-redis"),gethostbynamel("cartercloud-drive-db")]);')
    generic_redis, generic_db, own_redis, own_db = json.loads(subprocess.check_output(
        ['docker', 'exec', web, 'php', '-r', script], text=True))
    assert len(generic_redis) >= 2 and len(generic_db) >= 2, 'Collision fixture is not active'
    assert len(own_redis) == len(own_db) == 1, 'Drive service aliases are ambiguous'
    check_browser()
    subprocess.run(compose + ['up', '-d', '--force-recreate', '--wait', '--wait-timeout', '240', 'web', 'cron'], check=True)
    check_browser()
    print('PASS: browser sessions and restart survive conflicting db/redis names')
finally:
    subprocess.run(['docker', 'rm', '-f', '-v', name], check=True, stdout=subprocess.DEVNULL)
