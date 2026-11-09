#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Carter Cloud
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply Umbrel Drive branding to the exact source revisions in sources.json."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / 'sources.json').read_text())
REPO = 'https://github.com/carter-scramlin/umbrel-cloud-store'
APP_ID = 'io.github.carterscramlin.umbreldrive'


def verify(root, kind):
    actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != SPEC[kind]['commit']:
        raise SystemExit(f'Expected {SPEC[kind]["commit"]}; got {actual}. Review changes before updating the pin.')


def icon(size):
    image = Image.new('RGBA', (size, size))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            pixels[x, y] = tuple(int(a + (b - a) * t) for a, b in zip((155, 138, 255), (81, 69, 233))) + (255,)
    mask = Image.new('L', (size, size))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size * .23, fill=255)
    image.putalpha(mask)
    d = ImageDraw.Draw(image)
    for points in [[(201, 173), (311, 173), (256, 274)], [(127, 305), (182, 204), (237, 305)],
                   [(275, 305), (330, 204), (385, 305)], [(183, 321), (329, 321), (307, 355), (205, 355)]]:
        d.polygon([(int(x * size / 512), int(y * size / 512)) for x, y in points], fill='white')
    return image


def cmake_value(text, key, value):
    pattern = rf'(set\(\s*{key}\s+)"[^"]*"'
    changed, count = re.subn(pattern, lambda m: m[1] + json.dumps(value), text)
    if not count:
        raise ValueError(f'Upstream CMake setting missing: {key}')
    return changed


def desktop(root):
    verify(root, 'linux')
    config = root / 'NEXTCLOUD.cmake'
    text = config.read_text()
    values = dict(APPLICATION_NAME='Umbrel Drive', APPLICATION_SHORTNAME='UmbrelDrive',
                  APPLICATION_EXECUTABLE='umbrel-drive', APPLICATION_DOMAIN='github.com/carter-scramlin',
                  APPLICATION_VENDOR='Carter Cloud', APPLICATION_REV_DOMAIN='io.github.carterscramlin',
                  APPLICATION_REV_DOMAIN_DBUS='umbreldrive.carterscramlin.github.io',
                  APPLICATION_HELP_URL=REPO + '/tree/main/cartercloud-drive', APPLICATION_UPDATE_URL=REPO + '/releases',
                  APPLICATION_VIRTUALFILE_SUFFIX='umbreldrive', LINUX_PACKAGE_SHORTNAME='umbreldrive',
                  NEXTCLOUD_BACKGROUND_COLOR='#635bff')
    for key, value in values.items():
        text = cmake_value(text, key, value)
    text = text.replace('option( WITH_PROVIDERS "Build with providers list" ON )',
                        'option( WITH_PROVIDERS "Build with providers list" OFF )')
    config.write_text(text)
    svg = (HERE.parent / 'server/umbreldrive/img/logo.svg').read_text()
    icons = root / 'theme/colored'
    for name in ['io.github.carterscramlin.umbreldrive', 'UmbrelDrive']:
        (icons / f'{name}-icon.svg').write_text(svg)
        for size in [16, 24, 32, 48, 64, 128, 256, 512, 1024]:
            icon(size).save(icons / f'{size}-{name}-icon.png')
    (icons / 'wizard_logo.svg').write_text(svg)
    # This hint is not a fixed endpoint: users can connect to their own HTTPS host.
    theme = root / 'src/libsync/nextcloudtheme.cpp'
    theme.write_text(theme.read_text().replace('https://try.nextcloud.com', 'https://umbrel.local:8390'))


def android(root):
    verify(root, 'android')
    gradle = root / 'app/build.gradle.kts'
    text = gradle.read_text().replace('applicationId = "com.nextcloud.client"', f'applicationId = "{APP_ID}"')
    gradle.write_text(text)
    setup = root / 'app/src/main/res/values/setup.xml'
    text = setup.read_text()
    values = dict(app_name='Umbrel Drive', account_type=APP_ID, authority=APP_ID + '.provider',
                  users_and_groups_search_authority=APP_ID + '.search',
                  users_and_groups_share_with=APP_ID + '.action.SHARE_WITH',
                  document_provider_authority=APP_ID + '.documents', file_provider_authority=APP_ID + '.files',
                  image_cache_provider_authority=APP_ID + '.imageCache',
                  db_file='umbreldrive.db', db_name='umbreldrive', data_folder='UmbrelDrive',
                  default_display_name_for_root_folder='Umbrel Drive', name_for_branded_user_agent='UmbrelDrive',
                  sourcecode_url=REPO + '/tree/main/cartercloud-drive/clients',
                  url_help=REPO + '/tree/main/cartercloud-drive',
                  help_link=REPO + '/tree/main/cartercloud-drive',
                  report_issue_empty_link=REPO + '/issues', report_issue_link=REPO + '/issues/new',
                  url_app_download=REPO + '/releases', suggested_server='https://umbrel.local:8390',
                  privacy_url=REPO + '/blob/main/cartercloud-drive/PRIVACY.md',
                  login_data_own_scheme='umbreldrive', primary='#635bff', primary_dark='#5148ec',
                  color_accent='#635bff', login_text_hint_color='#d4cfff',
                  show_provider_or_own_installation='false', disable_intro='true',
                  recommend_enabled='false', participate_enabled='false', show_whats_new='false',
                  splashScreenBold='Umbrel Drive', splashScreenNormal='Your files. Right at home.')
    for key, value in values.items():
        pattern = rf'(<(?:string|bool|color) name="{key}"[^>]*>).*?(</(?:string|bool|color)>)'
        text, count = re.subn(pattern, lambda m: m[1] + value + m[2], text, flags=re.S)
        if count != 1:
            raise ValueError(f'Upstream Android setting changed: {key}')
    setup.write_text(text)
    ET.fromstring(text)
    res = root / 'app/src/main/res'
    for folder, size in dict(mdpi=48, hdpi=72, xhdpi=96, xxhdpi=144, xxxhdpi=192).items():
        icon(size).save(res / f'mipmap-{folder}/ic_launcher.png')
        circle = icon(size)
        mask = Image.new('L', (size, size))
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        circle.putalpha(mask)
        circle.save(res / f'mipmap-{folder}/ic_launcher_round.png')
    adaptive = res / 'mipmap-anydpi/ic_launcher.xml'
    (adaptive.parent / 'ic_launcher_round.xml').write_text(adaptive.read_text())
    manifest = root / 'app/src/main/AndroidManifest.xml'
    manifest.write_text(manifest.read_text().replace('android:roundIcon="@mipmap/ic_launcher"',
                                                     'android:roundIcon="@mipmap/ic_launcher_round"'))
    vector = '''<?xml version="1.0" encoding="utf-8"?>
<!-- SPDX-FileCopyrightText: 2026 Carter Cloud -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="512" android:viewportHeight="512">
 <path android:fillColor="#ffffff" android:pathData="M201,173L311,173L256,274ZM127,305L182,204L237,305ZM275,305L330,204L385,305ZM183,321L329,321L307,355L205,355Z"/>
</vector>
'''
    for name in ['ic_launcher_foreground.xml', 'nextcloud_logo.xml']:
        (res / 'drawable' / name).write_text(vector)
    (res / 'drawable/ic_launcher_background.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<!-- SPDX-FileCopyrightText: 2026 Carter Cloud -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"><solid android:color="#635bff"/></shape>
''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=['linux', 'android'])
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    (desktop if args.kind == 'linux' else android)(args.source.resolve())
