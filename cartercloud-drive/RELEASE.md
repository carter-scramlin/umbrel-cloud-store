# Umbrel Drive 1.1.0 — Files integration

Connect an existing folder using Umbrel’s native **Storage → Umbrel Files** picker.
Use the same ordinary files in Umbrel Files, the Drive browser, and the Linux and
Android clients. Changes made in Files are indexed automatically, typically within
one minute; large libraries and network shares can take longer. The folder is
restricted to the umbrel Drive account until explicitly shared.

This server update preserves existing private Drive files, uses Umbrel’s user ID
for connected-folder writes, and fixes delivery of theme/integration code during
app updates. Changing folders uses separate cache identities so old links cannot
expose same-named files in the replacement. Clearing the selection does not delete
any of the folder’s files.

Native client binaries remain version **1.0.0** and use the same signed Android
APK and Linux AppImage as the earlier release. They are included here unchanged
with their SHA-256 checksums and complete corresponding sources. Server package
version 1.1.0 is in the community store and the server-source archive.

This remains community software powered by Nextcloud, not an official Umbrel
product or full Synology Drive parity. See FEATURES.md for the coverage matrix,
TESTING.md for verification limits, and README.md for backup and recovery behavior.
Android general bidirectional folder-pair sync, independent push credentials,
Synology protocols, and advanced office/OCR services are not included.
