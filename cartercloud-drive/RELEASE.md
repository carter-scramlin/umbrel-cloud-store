# Umbrel Drive 1.2.0 release candidate

This candidate completes everyday mobile navigation and large browser uploads,
and adds an optional connection to originals backed up by the official Umbrel app.
It is community software powered by Nextcloud, with no claim of Umbrel endorsement
or complete Google/Synology feature parity.

- Mobile Browse Drive menu exposes Files, recovery, sharing, account security,
  device setup, full workspace, and Back to Umbrel. Larger touch targets and
  reduced-motion support improve keyboard and phone use.
- Uploads above 8 MiB use Chunking v2 in 8 MiB parts, with progress, cancellation,
  and up to two retries of a chunk interrupted by a network error. Files up to
  16 GiB are accepted by the browser. Reloading closes the upload; cross-reload
  resume is not implemented. Native clients remain best for long transfers.
- Existing files are never overwritten. Cancellation removes private temporary
  chunks, and failed cleanup expires after 24 hours. Completed files are kept.
  An ambiguous final response is never automatically replayed: check the folder
  before retrying. Favorite updates check per-property DAV results.
- Optional Storage → Umbrel Photos selection mounts photo originals read-only
  for the umbrel Drive account. Use Home/Photos for official mobile backups;
  manage backup and deletion in Umbrel Photos. Other accounts require an explicit
  Drive share. This neither replaces nor broadens the existing Files connection.
- Official Umbrel Android app uses Apps → Umbrel Drive with a separate Drive
  login. A fork is unnecessary for this supported launch path. Offline files and
  Drive auto-upload use the separate native Drive client, version 1.1.0.

Android 1.1.0 also corrects the login logo and splash layout, retains the existing
package/signing identity, and reports its own version. Linux remains 1.0.0.

The 1.1.3 browser speed report remains a historical baseline. This candidate
measured a 130 ms median server response for a 1,004-file folder using a cookie
session; it is not a new browser-rendering benchmark.
See TESTING.md and docs/umbrel-drive-release-readiness.md for this candidate's
results, limitations, and remaining stable-release gates. Accounts, device app
passwords, selected folders and private storage are preserved; no data migration
or uninstall is required. Back up app data and connected folders separately.
