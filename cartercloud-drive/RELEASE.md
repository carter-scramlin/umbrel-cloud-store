# Umbrel Drive 1.1.3 — faster file browsing

Open everyday files in a small browser built for Umbrel Drive. Folder navigation
stays on the page and requests only the needed metadata. The initial browser loads
about 28 KB of decoded JavaScript/CSS, instead of the full workspace's multi-megabyte
bundles. Content-hashed assets keep browser caching safe across updates.

Browse and search the current folder, sort, upload files up to 256 MiB, create
folders, rename, move, copy, favorite, and create/revoke read-only share links.
Uploads do not replace existing files, and move/copy operations preserve conflicts.
Images can be previewed on demand. No mass thumbnail generation runs during browsing.
The same server handles authentication, file permissions, versions and native sync.

**Full workspace** remains available for advanced sharing, version history, trash
and recovery, team administration, office/viewer tools, and resumable large-file
uploads. Its original URLs remain valid. Android and Linux client binaries remain
version 1.0.0. This update does not change Android integration.

Reopen Umbrel Drive from Umbrel to enter the faster browser. Existing bookmarks to
/apps/files/... still open the full workspace. Accounts, app passwords, private data
and selected Umbrel Files folders are preserved. Files written through native Files
continue to follow their own recovery rules and automatic indexing interval.

The opt-in full-workspace timing probe (`drivePerf=1`) and the fast browser's Speed
info display measure row readiness locally. No timing telemetry leaves your server.
See the repository's 1.1.3 speed verification record for methods, results and limits.
This remains a community preview; it does not claim complete Synology feature parity.
