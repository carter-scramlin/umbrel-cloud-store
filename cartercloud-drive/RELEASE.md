# Umbrel Drive 1.0.0 — community preview

A Nextcloud-based edition with an Umbrel-inspired file browser, native Linux and
Android clients, team folders, file versions, trash, sharing, and scheduled Linux
upload-only backups. Installs alongside the original preview without migrating
or overwriting it.

Downloads:
- **Linux x86_64:** `Umbrel-Drive-1.0.0-linux-x86_64.AppImage`
- **Android 9+:** `Umbrel-Drive-1.0.0-android.apk` (dedicated community signature)
- **Optional Linux file-manager extensions:** `Umbrel-Drive-1.0.0-shell-integration.zip`
- **Complete branded client sources:** the Linux and Android source archives
- **Checksums:** `SHA256SUMS`

The Linux client was compiled and checked under a virtual X11/D-Bus session;
its native sync engine uploaded a file and downloaded a server-side edit.
The Android generic release compiled, passed release lint, and its APK signature
and zip alignment were verified. Physical Android-device QA remains outstanding.
Server API and backup-helper checks are documented in the app's TESTING.md.

This is not full Synology Drive parity. See the
[feature matrix](https://github.com/carter-scramlin/umbrel-cloud-store/blob/main/cartercloud-drive/FEATURES.md),
including the limits around Android folder-pair sync, push notifications,
on-demand Linux files, office editing, search indexing, and proprietary Synology
integrations. This is community software, not an official Umbrel product.
