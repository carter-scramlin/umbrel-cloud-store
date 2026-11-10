# Security and supported releases

Umbrel Drive is an independent community distribution. The current 1.2 candidate
is under release validation; 1.1.3 is the previous preview. No long-term support
promise or independent security audit is implied. Keep umbrelOS and native
clients updated, and review Nextcloud security advisories for the pinned server.

Do not post passwords, app passwords, private keys, personal files, public-share
tokens or unredacted logs in issues. Use GitHub private vulnerability reporting
if available; otherwise contact the repository owner privately through a contact
method they publish. This repository does not operate a support mailbox.

## Trust boundaries

Drive and Umbrel accounts are separate. There is no automatic SSO or member
mapping. Only explicitly selected Files/Photos folders are mounted, initially
for the original umbrel Drive account. Members receive access only through an
explicit Drive share. Photos is read-only at both Docker and Drive mount levels.
Folder identity changes remove the old mount before creating its replacement,
so old shares cannot silently expose another selected folder.

Use HTTPS and verify the Umbrel certificate on native clients. The official
mobile app pins the paired Umbrel certificate itself. This project does not turn
off certificate validation or expose a Docker socket. Web mutations use the
server's cookie/CSRF checks; account HTML is not cached and scripts retain CSP
nonces. File names render as text. Uploads and moves refuse overwriting conflicts.

Sync and version history are not backups. Preserve the private app data and each
connected folder. Back up PostgreSQL only with a consistent stopped snapshot or
a coordinated logical dump. Never uninstall an app to troubleshoot or downgrade
its database in place. Validate a restore in a separate installation first.
