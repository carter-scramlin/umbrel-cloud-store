# SPDX-License-Identifier: AGPL-3.0-or-later
import subprocess
import sys
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile


class TestReleasePackaging(unittest.TestCase):
    def test_fresh_sources_produce_all_extensions_and_exclude_build_state(self):
        script=Path(__file__).resolve().parents[1]/'clients/package_sources.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);linux=root/'linux';android=root/'android';output=root/'output'
            source=linux/'shell_integration/nautilus';source.mkdir(parents=True)
            (source/'syncstate.py').write_text("# SPDX-FileCopyrightText: Nextcloud contributors\nfrom gi.repository import GObject, Nautilus\nappname = 'Nextcloud'\nclass MenuExtension_Nextcloud: pass\n")
            (linux/'COPYING').write_text('Test license fixture\n')
            (linux/'build').mkdir();(linux/'build/cache.bin').write_bytes(b'not source')
            (linux/'.git').mkdir();(linux/'.git/config').write_text('not source')
            android.mkdir();(android/'README.md').write_text('Android source fixture')
            subprocess.run([sys.executable,str(script),str(linux),str(android),str(output)],check=True,capture_output=True)
            with zipfile.ZipFile(output/'Umbrel-Drive-1.0.0-shell-integration.zip') as archive:
                for name,api in [('nautilus.py','Nautilus'),('nemo.py','Nemo'),('caja.py','Caja')]:
                    data=archive.read(name).decode()
                    self.assertIn('import GObject, '+api,data)
                    self.assertIn("appname = 'UmbrelDrive'",data)
                    self.assertIn('# SPDX-FileCopyrightText: Nextcloud contributors',data)
            with tarfile.open(output/'Umbrel-Drive-1.0.0-linux-source.tar.gz') as archive:
                names=archive.getnames()
                self.assertTrue(any(n.endswith('/syncstate.py') for n in names))
                self.assertFalse(any('/build/' in n or '/.git/' in n for n in names))


if __name__=='__main__':unittest.main(verbosity=2)
