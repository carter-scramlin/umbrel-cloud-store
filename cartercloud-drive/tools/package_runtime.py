#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bundle runtime assets into Umbrel's update whitelist. No rendered secrets."""
import base64
import gzip
import io
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def bundle():
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        for path in sorted((ROOT / 'server').rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            info = tarfile.TarInfo(path.relative_to(ROOT / 'server').as_posix())
            content = path.read_bytes()
            info.size = len(content)
            info.mode = 0o755 if path.suffix == '.sh' else 0o644
            archive.addfile(info, io.BytesIO(content))
    return base64.encodebytes(gzip.compress(stream.getvalue(), mtime=0))


if __name__ == '__main__':
    target = ROOT / 'drive-runtime.b64.template'
    result = bundle()
    if '--check' in sys.argv:
        if target.read_bytes() != result:
            raise SystemExit('Runtime bundle is stale: run tools/package_runtime.py')
        print('Runtime bundle matches server sources.')
    else:
        target.write_bytes(result)
