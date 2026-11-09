#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reassemble signed release binaries and verify their published SHA-256 hashes."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import shutil

p=argparse.ArgumentParser();p.add_argument('asset_dir',type=Path);p.add_argument('output',type=Path)
args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
manifest=json.loads((Path(__file__).parent/'release-assets.json').read_text())
for file in manifest['files']:
 name=file['name']
 if Path(name).name!=name: raise ValueError('Invalid artifact filename')
 destination=args.output/name
 transport=args.output/(name+'.transport')
 with transport.open('wb') as output:
  for part in file['parts']:
   if Path(part).name!=part: raise ValueError('Invalid part filename')
   with (args.asset_dir/part).open('rb') as source: shutil.copyfileobj(source,output)
 if file.get('compression')=='gzip':
  with gzip.open(transport,'rb') as source,destination.open('wb') as output: shutil.copyfileobj(source,output)
  transport.unlink()
 else: transport.rename(destination)
 with destination.open('rb') as source: actual=hashlib.file_digest(source,'sha256').hexdigest()
 if actual!=file['sha256'] or destination.stat().st_size!=file['size']:
  destination.unlink();raise ValueError('Artifact checksum mismatch: '+name)
 if name.endswith('.AppImage'): destination.chmod(0o755)
 print('Verified:',name)
