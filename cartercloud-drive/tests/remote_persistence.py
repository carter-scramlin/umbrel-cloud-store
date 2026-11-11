#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Carter Cloud
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A saved exact remote host and its session survive an ordinary app restart."""
import argparse
import json
import subprocess
import time
import uuid
from umbrel_connections import ADMIN, PATH, browser, call

p = argparse.ArgumentParser()
p.add_argument('--compose', required=True)
p.add_argument('--env-file', required=True)
p.add_argument('--project', required=True)
a = p.parse_args()
command = ['docker', 'compose', '--env-file', a.env_file, '-f', a.compose, '-p', a.project]
opener, token = browser('umbrel', ADMIN)
previous = json.loads(call(opener, PATH + '/connections')[1])['remoteAddress']
host = 'restart-' + uuid.uuid4().hex + '.tail-test.ts.net'
try:
    assert call(opener, PATH + '/remote', {'address': 'https://' + host + ':8390'}, token)[0] == 200
    subprocess.run(command + ['restart', 'web'], check=True)
    deadline = time.monotonic() + 180
    while True:
        try:
            status, body, _ = call(opener, PATH + '/connections', Host=host)
            if status == 200:
                assert json.loads(body)['remoteAddress'] == 'https://' + host + ':8390'
                break
        except (OSError, ValueError):
            pass
        if time.monotonic() > deadline:
            raise AssertionError('Saved remote host/session did not survive restart')
        time.sleep(2)
    print('PASS: exact remote host and authenticated session survive restart')
finally:
    # A browser token is masked per page; it remains valid for the same session.
    assert call(opener, PATH + '/remote', {'address': previous}, token)[0] == 200
