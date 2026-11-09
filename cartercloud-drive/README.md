# Umbrel Drive

Your files. Right at home.

A community drive for umbrelOS with a clean, lavender-accented file browser,
multiple accounts, shared team folders, and native Linux and Android clients.
It uses Nextcloud's storage and sync engines and includes an Umbrel-inspired
theme, device setup page, PostgreSQL, Redis locking, and upload-only Linux backups.

This is a first community release, not a feature-complete Synology clone or an
official Umbrel product. Read [feature coverage](FEATURES.md) before migrating.

## Install on umbrelOS

1. Add or refresh the **Carter Cloud** community store:
   `https://github.com/carter-scramlin/umbrel-cloud-store`.
2. Install **Umbrel Drive** (`cartercloud-drive`, port **8390**).
3. Open the app using the trusted HTTPS app URL provided by Umbrel.
4. Sign in as **umbrel**, using the generated app password shown by Umbrel.
5. Open **Get the apps** from the app menu to connect your devices.

Initial startup downloads the pinned Nextcloud, PostgreSQL, and Redis containers
and a checksum-verified Team folders 23.0.1 archive. Allow several minutes. If
the archive download fails, startup fails instead of silently omitting team folders.
Subsequent startups use the installed app. The server images support amd64 and
arm64; the provided Linux desktop binary is x86_64.

The app uses its own Nextcloud login so native clients and public links can work
without an Umbrel browser session. Use trusted HTTPS. The server trusts only the
Umbrel proxy network; it derives its public address from the incoming request.
If you use a separate reverse proxy, configure its trusted address explicitly and
keep upload limits/timeouts appropriate to your files. No public access is set up
by this package.

## Linux

Download `Umbrel-Drive-1.0.0-linux-x86_64.AppImage` from the
[release](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.0.0).
Make it executable, then launch it:

```sh
chmod +x Umbrel-Drive-1.0.0-linux-x86_64.AppImage
./Umbrel-Drive-1.0.0-linux-x86_64.AppImage
```

Enter the **exact HTTPS app address** from Get the apps. Sign in in the browser,
approve the device, and choose a local folder. Use selective sync to choose folders.
The client preserves upstream conflict handling, bandwidth settings, multiple
accounts, and pause/resume. Its independent identity keeps it separate from an
existing Nextcloud client. If FUSE is unavailable, run it with
`--appimage-extract-and-run`. Linux on-demand-file support is experimental and
requires validating the upstream OpenVFS environment on your filesystem.

Optional file-manager extensions are in `Umbrel-Drive-1.0.0-shell-integration.zip`.
Use the extension for your file manager, install its Python integration dependency
through your distro, and follow the included instructions. The AppImage does not
automatically install shell extensions. The built-in updater is disabled; download
new Umbrel Drive releases explicitly.

## Android

Download and install `Umbrel-Drive-1.0.0-android.apk` from the release. Android may
ask you to allow installation from the browser or file manager you are using.
The APK is signed with a dedicated community key and uses the independent package
ID `io.github.carterscramlin.umbreldrive`. It can coexist with the Nextcloud app.
Android 9 or newer is required. The application retains its upstream version code
and reports the underlying client version 35.0.2.

Enter the server address, sign in in the browser, and approve the device. Use
**Auto upload** to select camera/media folders and Wi-Fi/charging conditions.
Use **Keep available offline** for files needed without a connection. Review
Android battery optimization and file/photo permissions when enabling background
uploads. The APK signature and release build were verified; physical-device
background upload, offline behavior, and document scanning still need device QA.
Independent-package push credentials are not configured.

Only the signed APK is public. The signing key and its password are kept in a
private local signing backup, outside the repository and release. Future APK
updates must use that same key. Do not upload the signing backup.

## Users and team folders

Create users, groups, and quotas in **Administration → Accounts**. Configure
shared, centrally owned folders and ACLs in **Administration → Team folders**.
Users can also share their own folders with users/groups, create password-protected
and expiring links, or create upload-only file requests. Manage device app passwords
and TOTP in **Personal settings → Security**. Audit logging is enabled.

## Scheduled Linux backups

The native client is for two-way synchronization. Use the included Python 3.11+
helper for separate upload-only backups. It never deletes local or remote files.
Each run uploads a full dated snapshot, including empty folders, to
`Backups/DEVICE/TIMESTAMP/files`. A completion manifest records SHA-256 hashes.
Interrupted snapshots do not receive a completion marker. Symlinks are skipped.
This is a file-content backup; Unix ownership, permissions, ACLs, xattrs, and hard
links are not preserved. There is no automatic retention or deduplication.

```sh
install -Dm700 clients/backup.py ~/.local/bin/umbrel-drive-backup
~/.local/bin/umbrel-drive-backup configure \
  --url https://YOUR-APP-HOST --user YOUR-ACCOUNT \
  --folder /path/to/backup --device my-linux-pc --exclude '*.tmp'
~/.local/bin/umbrel-drive-backup run
```

Create a dedicated app password in Security settings and paste it at the prompt.
The helper stores it in a mode-600 config file. To use a private CA, add
`--ca-file /path/to/ca.pem`; certificate validation stays enabled. Restore by
copying a completed snapshot's files through the web or native client.

For daily backups, copy `clients/umbrel-drive-backup.service` and `.timer` into
`~/.config/systemd/user/`, then run:

```sh
systemctl --user daemon-reload
systemctl --user enable --now umbrel-drive-backup.timer
```

## Existing Umbrel Drive Preview data

The original `cartercloud-umbrel-drive` preview remains separate, on port 8388.
This edition does not replace its SQLite database, storage, keys, or clients.
Download or sync a copy of the preview's current files to a staging folder, then
upload that folder to this edition. Check counts and sample hashes before retiring
the preview. Old revision history, links, and device keys do not migrate. Never
point the new server directly at the preview's object store.

## Server backup and restore

Sync is not a server backup. Preserve the **entire** app data directory, including
`data/postgres` and `data/nextcloud`. A simple consistent backup is an Umbrel backup
or filesystem snapshot taken while this app's web, cron, Redis, and PostgreSQL
containers are all stopped. Copying a running PostgreSQL data directory is unsafe.
For online backups, use a PostgreSQL logical dump with a consistent Nextcloud
maintenance window and preserve Nextcloud's data/config/custom_apps alongside it.
Test restores into a separate installation before relying on a backup.

## Build and test

The [client source pins](clients/sources.json), branding script, Docker build
recipes, and complete corresponding source archives are public. The release
pipeline assembles the already-verified native binaries from a separate asset
branch so community-store checkouts of `main` remain small. Checksums are verified
before release publication. The source archives retain upstream license notices.
See [build instructions](clients/BUILDING.md) and [test results](TESTING.md).

Office editing of DOCX/XLSX/PPTX needs a compatible Collabora/ONLYOFFICE service
and a matching Nextcloud integration app. Full-text search/OCR, Synology-specific
formats, ShareSync compatibility, watermarks/DLP, and general Android bidirectional
folder-pair sync are not supplied. The complete limitations are in FEATURES.md.

## Credits and licensing

Server: [Nextcloud Server](https://github.com/nextcloud/server).
Linux: [Nextcloud Desktop](https://github.com/nextcloud/desktop), GPL-2.0-or-later.
Android: [Nextcloud Android](https://github.com/nextcloud/android), mixed GPL/AGPL
licenses as specified in upstream SPDX headers. Team folders:
[nextcloud/groupfolders](https://github.com/nextcloud/groupfolders), AGPL.
New theme and packaging code in this directory: AGPL-3.0-or-later.
The repository's root MIT license does not replace these licenses.
