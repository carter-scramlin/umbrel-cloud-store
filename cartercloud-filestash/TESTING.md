# Filestash package verification

Package: `cartercloud-filestash`, version `0.6.20261022`.
Tested 2026-10-22 on Linux amd64 with Docker Engine 29.8.0 and Compose v5.5.1.
The image reports `v0.6.20261022` in its admin console.

## Verified

- Official Umbrel package linter, including public image checks: zero errors.
- Each pinned image index contains Linux amd64 and arm64 manifests.
- Package app ID, proxy host/port, persistence paths, folder-access service and
  target, and unique host port pass the manifest/Compose checks.
- Fresh start opens the administrator setup page in a real browser.
- First-run administrator creation and subsequent administrator login through
  the gateway API; Local storage authentication using that password.
- Folder creation, upload, byte-for-byte download, rename, directory listing,
  deletion, and filename search.
- A writable test share can be created, listed, browsed in the browser, and
  downloaded anonymously through Filestash's sharing controls.
- Collabora discovery and browser editor served through the same gateway.
- A test ODT opens in the browser, accepts edits, and saves through WOPI.
  The edited text was verified inside the persisted ODT archive on disk.
- After recreating all three containers, the existing administrator password,
  text file, saved Office document, and shared link continue to work.
- Requests with HTTP/HTTPS forwarding receive matching ws/wss editor URLs,
  preserving the external Host header. WebSocket upgrade and WOPI callback
  routing were exercised by the browser document-editing test.
- Collabora's hashed and un-hashed admin-page routes and admin WebSocket return
  404 at the gateway.

The isolated test stack used the exact packaged images, gateway configuration,
capability and environment settings, and Umbrel-style container names. Only
the Umbrel-managed app_proxy entry was replaced by a localhost port binding;
test bind mounts were relabeled for SELinux. No real user files were used.

## Intentional linter warnings

- `image.latest`: Filestash currently publishes current builds under `latest`;
  the other public tags are older builds or trial variants. A multi-platform
  SHA-256 pin prevents this install from following later upstream changes.
- `access.cap_add`: Collabora uses `MKNOD` for its document-process sandbox.
  The package does not use privileged mode or a host Docker socket.

## Still requires target-device verification

This package has not been installed through a live Umbrel app lifecycle.
Before treating it as production-verified, install from Carter Cloud on
umbrelOS 2.0+, open through Umbrel with login protection, and check HTTP and
HTTPS access. Verify the Files folder picker, a readable/writable selected
folder, app-data relocation, restart, and Umbrel backup/restore. This first
release has no prior Filestash package upgrade path to test.

ARM runtime, a live Umbrel TLS/auth boundary, spreadsheet/presentation-specific
editing, simultaneous collaboration, every supported media format, OAuth
providers, remote storage requiring credentials, and optional paid plugins
were not individually tested. Their upstream features remain available as
provided by the pinned images and the user's configuration/licenses.

## Maintenance

Keep the app ID, service names, port, and folder-access ID stable. Update image
tags/digests deliberately and bump the manifest version. Keep new durable
state below `data/`. Umbrel copies Compose during upgrades, so gateway config
is embedded there instead of in an extra file that updates might omit.

Repeat the browser Office save test when upgrading Filestash or Collabora;
the relative discovery rewrite and ws/wss HTML rewrite depend on their
upstream formats. Test an actual Umbrel update with existing files and shares
before releasing later versions. Back up all app-owned state and separately
selected folders; never reset or uninstall to perform an ordinary update.
