# Umbrel Drive

Umbrel Drive is a single-account community file server for umbrelOS 2.0 with
an umbrelOS-inspired browser interface, a Linux folder-sync agent, and an
installable Android web app. It uses its own storage and does not require
Nextcloud, Synology hardware, or a separate database.

## Set up on Umbrel

1. Open **App Store → Community App Stores** and add or refresh
   `https://github.com/carter-scramlin/umbrel-cloud-store`.
2. Install **Umbrel Drive** from **Carter Cloud**.
3. Open it using the trusted HTTPS app URL shown by Umbrel (port 8388).
   Use the generated **app password** from the Umbrel Drive listing.
4. Start with a test file. Upload it, download it, and restart the app to
   confirm that your Umbrel installation preserves it.

The app uses its own sign-in so sync keys and download links can work without
an Umbrel browser session. Keep the URL on your LAN or behind private remote
access. Use a certificate trusted by each client. If a reverse proxy is
involved, its upload and timeout limits also apply. Clients expect this app
at the root of its own origin.

## Android

Open the same HTTPS URL in Chrome, sign in, and choose **Install app** or
**⋮ → Add to Home screen → Install**. The installed web app supports browsing,
search, downloads, manual batch uploads from Android's file and photo pickers,
sharing, file moves, and history.

Tap **More → Save offline** on a file to store a snapshot, then open **Offline**
to download that snapshot without reaching the server. Open the app online
at least once before using it offline. Offline copies are device-local, can be
evicted by the browser, and are removed when you sign out. Copies do not
refresh automatically. For sensitive files, use a device with a screen lock
and avoid saving files offline on shared devices.

## Fedora and other Linux desktops

Use the web app for file browsing, or install it from a compatible Chromium
browser. For folder sync, open **Devices**, select **Download client**, and
create a device key. The agent requires Python 3.10+ and has no pip dependencies.

```sh
mkdir -p ~/.local/bin ~/UmbrelDrive
install -m 700 ~/Downloads/umbrel-drive-sync.py ~/.local/bin/umbrel-drive-sync
~/.local/bin/umbrel-drive-sync configure \
  --url https://umbrel.local:8388 \
  --folder ~/UmbrelDrive
~/.local/bin/umbrel-drive-sync once
```

Use the exact app URL your browser uses and paste the device key when asked.
If Umbrel uses a private CA, add `--ca-file /path/to/ca.pem` during configure.
Keys expire after one year and can be revoked in **Devices**. The key grants
access to the whole drive and is stored in a user-only config file.

For continuous sync use `~/.local/bin/umbrel-drive-sync watch` (polls every
60 seconds). To start it with your Linux session, create
`~/.config/systemd/user/umbrel-drive.service` containing:

```ini
[Unit]
Description=Umbrel Drive folder sync

[Service]
ExecStart=%h/.local/bin/umbrel-drive-sync watch
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Then run `systemctl --user daemon-reload` and
`systemctl --user enable --now umbrel-drive.service`. Check status with
`journalctl --user -u umbrel-drive.service -f`.

Use `--job NAME` before `configure`, `once`, or `watch` to manage separate
jobs. During configure, use `--remote Photos` for a remote folder,
`--mode backup` for upload-only backup without remote deletions, or
`--mode download` for a download mirror. Repeat `--exclude '*.tmp'` to
exclude paths. Use separate local folders and non-overlapping remote folders
for jobs on the same device. An empty remote prefix represents the entire drive.

Two-way sync sends local deletions to server Trash and moves files deleted on
the server into the local `.umbrel-drive-recovery/` directory. Concurrent edits
preserve the local edit as a separate conflict file and pull the server version.
The first sync treats different files at the same path as a conflict. Download
mirror mode also keeps displaced local files in the recovery directory. Use a
dedicated folder and verify behavior on test files before pointing sync at data
you rely on.

## Storage and feature coverage

- Files are stored in a content-addressed object store under the app's
  persistent `data/` directory. Stop the app and back up the **entire**
  directory, including SQLite and objects. Backups are separate from sync.
- Files have a 2 GiB upload limit. The web client pins files up to 100 MiB
  each. Folders are derived from files and appear on other clients after
  the first upload. Symlinks, permissions, and empty folders do not sync.
- The app retains all previous versions and Trash indefinitely. Keep an eye
  on storage use. Shared links grant download access to one fixed revision,
  even if you move the current file to Trash. Revoke the link to end access
  before it expires.
- This preview covers file browsing, search by name, uploads, downloads, file moves,
  sharing, file history, Trash, offline snapshots, and Linux folder sync
  and backup. It does not implement native Android folder sync or background
  camera backup, Linux file-manager placeholders or shell integration,
  team folders, separate user accounts, file locking, office collaboration,
  or Synology NAS-to-NAS ShareSync.

Local checks exercise the API, file revision safety, Linux sync, and Chromium
workflows. A live Umbrel installation and a physical Android device are still
needed to verify the deployment and Android installation flow.
