# Umbrel Drive 1.1.0 verification

Verified on 2026-11-08 (America/New_York). This is community software powered by
Nextcloud, not an official Umbrel product or a complete Synology Drive clone.

The [release workflow](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42561397340)
passed for runtime commit `45303a8131d47612fcd673bb383bd463fda3aa1b` and published
[server 1.1.0 and native client downloads](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.0).
The signed Android APK and Linux AppImage are unchanged from client version 1.0.0.

## Native Umbrel Files integration

- Installed version 1.0.0 through the community App Store on an amd64 device running
  umbrelOS 2.1.0-beta.1, then updated to 1.1.0 through Umbrel's app lifecycle.
  Both operations reached ready without reported operation failures.
- The native app settings exposed the declared Umbrel Files folder slot for both
  the web and background services. Selecting a newly created Home folder triggered
  the automatic restart and the server logged a successful owner-account connection.
- An authenticated Drive DAV upload appeared as an ordinary file in native Umbrel
  Files. A rename through the native Files API was picked up by Drive, with the
  original contents intact. The disposable fixture was moved to native Files Trash.
- The live API check used a process-local TLS certificate pin and hostname/IP
  validation. No device/browser/system certificate-trust settings were changed.
  Live HTTPS browser testing was blocked because that browser profile does not
  trust the Umbrel CA; its warning was not bypassed. Install the Umbrel certificate
  using its own HTTPS settings before connecting browsers and native clients.

## Automated server checks

- Seven existing API workflow tests passed for authentication, branding, file
  operations, stale ETags, revisions, trash, sharing, file requests, and quotas.
- The selected-folder test passed round trips, UID/GID 1000 writes, automatic
  indexing of outside edits/renames/deletions, ancestor metadata updates, and
  owner-only access with explicit sharing to a second account.
- The folder lifecycle test passed no-folder startup, connecting folder A,
  switching to folder B, and disconnecting. An old public link did not expose a
  same-named file in B. Neither original folder was deleted, and private Drive
  files survived the restart sequence.
- Backup safety tests, source packaging tests, and runtime-bundle validation
  passed. The first CI attempt caught Python-version differences in gzip envelopes;
  the corrected check compares the canonical uncompressed payload.
- Umbrel's package linter reported zero errors. Its sole warning concerns Redis's
  intentional `no-new-privileges` security hardening.
- Local browser checks confirmed the connection-status page and its connected-
  folder shortcut, including an ordinary file created outside Drive.

## Remaining limits

See [feature coverage](../cartercloud-drive/FEATURES.md) and the
[native build record](../cartercloud-drive/TESTING.md). Physical Android background
behavior, real Linux file-manager integration, arm64 runtime, large libraries,
network-share failure recovery, and complete backup restoration remain unverified.
Native Umbrel Files and Drive accounts/sharing are separate. Direct Files edits
bypass Drive versions; recover native Files deletions in its own Trash. Back up
connected folders alongside the app's database and private metadata.
