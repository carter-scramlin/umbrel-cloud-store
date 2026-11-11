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


## Optional HTTP and remote profiles

The plain HTTP endpoint on device port 8391 is reachable on device interfaces;
HTTPS on 8390 remains the default. HTTP does not encrypt credentials or file bytes.
Use HTTP only over a trusted transport such as Tailscale, whose access policy must
permit the devices. This project neither opens router forwarding nor enables Funnel.
Native clients require explicit HTTP selection and retain HTTPS verification.
Connection profiles only select new sign-ins; they never reuse an existing account's
credentials at a different host. Server remote-host registration is authenticated,
CSRF-protected, limited to the original umbrel account, and restricted to exact
Tailscale IPs and `.ts.net` names. It stores no Tailscale auth keys.
