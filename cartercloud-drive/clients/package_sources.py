#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package complete branded client trees, excluding generated build caches."""
import argparse
import json
from pathlib import Path
import tarfile
import zipfile

p=argparse.ArgumentParser();p.add_argument('linux',type=Path);p.add_argument('android',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();spec=json.loads((Path(__file__).parent/'sources.json').read_text());a.output.mkdir(parents=True,exist_ok=True)
for label,root in [('linux',a.linux),('android',a.android)]:
 version=spec[label].get('clientVersion','1.0.0')
 target=a.output/f'Umbrel-Drive-{version}-{label}-source.tar.gz'
 def filter_member(member):
  if any(p in {'.git','.gradle','.kotlin','.cxx','build','build-client','node_modules'} for p in Path(member.name).parts):return None
  if member.name.endswith(('.AppImage','.log','.apk','.idsig')):return None
  return member
 with tarfile.open(target,'w:gz') as archive:archive.add(root,arcname=f'umbrel-drive-{label}',filter=filter_member)
 print('Packaged:',target.name)
with zipfile.ZipFile(a.output/'Umbrel-Drive-1.0.0-shell-integration.zip','w',zipfile.ZIP_DEFLATED) as archive:
 original=(a.linux/'shell_integration/nautilus/syncstate.py').read_text()
 for name,replacements in [('nautilus.py',[]),('nemo.py',[('autilus','emo')]),('caja.py',[('Nautilus','Caja'),('nautilus','caja')])]:
  lines=[]
  for line in original.splitlines():
   if 'SPDX-' not in line:
    line=line.replace('Nextcloud','UmbrelDrive')
    for before,after in replacements:line=line.replace(before,after)
   lines.append(line)
  archive.writestr(name,'\n'.join(lines)+'\n')
 archive.write(a.linux/'COPYING','COPYING')
 archive.writestr('README.txt','''Umbrel Drive optional file-manager integration\n\nInstall your distro's Python extension package for Nautilus, Nemo, or Caja.\nCopy only the corresponding .py file into:\n  ~/.local/share/nautilus-python/extensions/umbreldrive.py\n  ~/.local/share/nemo-python/extensions/umbreldrive.py\n  ~/.local/share/caja-python/extensions/umbreldrive.py\nUse the directory matching your file manager. Restart that file manager after\ninstallation. Umbrel Drive must be running with the folder already connected.\nSource: nextcloud/desktop at the revision in clients/sources.json.\nGPL-2.0-or-later; original SPDX copyright notices are preserved.\n''')
