# Umbrel Drive 1.2 release readiness

This is a community release candidate, not a declaration of complete Synology or
Google Drive parity or official Umbrel endorsement. Stable promotion is held until
the new browser UI has completed visual and interaction checks. Existing live
1.1.3 data and clients have not been uninstalled or reset.

## Decisions and shipped changes

Use the official Umbrel Android app's existing Apps launcher instead of maintaining
a fork of its certificate pairing, native login, photo backup, and device discovery.
The official Google Play app was installed on the owner's Android 13 Waydroid VM,
paired with the live Umbrel over LAN HTTPS, signed into the Umbrel account, then
opened Umbrel Drive and signed into the separate Drive account. Both My files and
the selected Umbrel Files folder rendered. No browser certificate warning was
bypassed. The owner explicitly supplied sign-in authorization. Credentials are not
included in this report or source. The credentials-before-open sheet did not fit
this VM's display; its existing Umbrel app setting was changed to hide that sheet.
The credential remains available in app settings.

An optional second Storage folder slot exposes Home/Photos originals read-only in
Drive. This lets official mobile photo backups reach Drive clients without moving
the originals, replacing photo backup, mapping other members' accounts, or changing
the existing writable Files selection. Initially only the umbrel Drive account
receives access; other accounts require an explicit share. The slot starts empty.
Read-only enforcement exists in Docker and Nextcloud. Deletions and photo backup
remain in Umbrel Photos, and connected folders need their own backups.

The small browser now has complete mobile navigation, larger action targets,
permission-aware create/rename/move/delete actions, a Back to Umbrel link, reduced
motion support, and a dark guest-page correction. Uploads above 8 MiB use Chunking
v2, up to 16 GiB per file, with progress and cancellation. Interrupted chunk PUTs
retry at most twice. A final MOVE is never replayed automatically after a lost
response. Existing names are preserved. Temporary chunks are cleaned up on failure
or expire after 24 hours. Uploads do not resume across reloads. Folder drops direct
users to the full workspace or Linux client rather than creating false empty files.
Favorite writes validate individual DAV property statuses. Idle refresh preserves
keyboard focus within file rows and continues for read-only folders.

## Verification completed

- Fresh pinned Nextcloud 35.0.2 / PostgreSQL 17 / Redis 7.4 isolated Docker install;
  update-safe runtime template extraction and app version upgrade; health/login.
- Seven API workflow groups: authentication, file CRUD, ETag conflicts,
  copy/move, versions and trash restore, protected/expiring/revoked links,
  upload requests, groups, quotas and user isolation.
- Four Chunking v2 checks: repeated-chunk exact byte preservation, no-overwrite
  conflicts, cancellation removing private chunks, and a 257 MiB transfer followed
  by a full download and SHA-256 comparison. 16 GiB is the configured limit, not
  a measured transfer size.
- Five fault-injection tests run the shipped JavaScript uploader: chunk boundaries,
  same-chunk retry after a lost response, canceled transfer never publishing,
  ambiguous final response never replaying publication, and safe small/oversized
  uploads. No real user files are involved.
- Writable Files round trip and automatic indexing, ancestor ETag changes,
  UID/GID 1000, explicit sharing and account isolation.
- Read-only photo originals preserve bytes; file replace, create and delete are
  denied, other accounts cannot see the mount, and explicit read-only sharing works.
  DAV permissions omit create-file/create-folder capabilities.
- Folder disconnect/reconnect/replacement prevents an old public link from exposing
  the replacement folder. Private Drive data survives these restarts.
- Full stopped private-app snapshot restored to a separate Docker project, with
  original account credentials, exact canary bytes and sharing metadata verified.
  This is a local restore rehearsal, not a test of Umbrel's encrypted-backup service.
- Cookie/CSRF authentication, no-store account HTML, CSP nonces, Unicode paths,
  content-hashed static assets, and identity/gzip/Brotli byte equivalence.
- Shared-network collision regression and restarts retain working sessions.
- Four Linux backup-helper safety tests and source/shell-extension packaging tests.
- Unmodified official Umbrel Android source c43beed compiled. Its shared kit suite
  reports 445 tests, 3 skipped, 0 failures/errors when run as a normal user. The first
  root-container run failed two filesystem-permission tests because root bypasses
  chmod; a non-root rerun passed. No modified official APK is distributed.
- Umbrel package lint: zero errors. Four warnings: Redis no-new-privileges and
  rebuilt upstream tags for the still-pinned, tested Nextcloud/Redis digests.
  Pins are intentionally unchanged; floating tags are not substituted silently.

## Remaining stable-release gates

1. Visual/interaction checks of the new 1.2 desktop and phone layouts, keyboard
   navigation, upload progress/cancel/conflict messages, read-only folders, login
   themes, and navigation back to Umbrel. The browser tool rejected localhost:18394
   first as declined and then as a saved site-permission block, even after the owner
   explicitly approved access. No alternate surface is used to bypass that block.
2. Native Drive Android 1.1.0 upload/download/offline smoke tests. Build, lint,
   signature and source packaging passed. Both the initial APK install and the
   same-key upgrade to 1.1.0 succeeded in the VM; local DNS was unavailable,
   so direct LAN IP was tested. Its certificate dialog matches the live Umbrel
   SHA-256, and trust is waiting for the owner’s decision. Browser-source install
   permission was restored to disabled after installation. Android 1.1.0 fixes the
   observed upstream logo and run-on splash branding, builds with lint/Detekt/Spotless,
   and passes signature/alignment checks with the original key. The corrected splash
   and sign-in logo rendered after upgrade. Upload/offline and physical-phone
   background media behavior still require device QA.
3. Green public CI for the exact candidate commit and matching release checksums
   is now complete (publication verification below). Promote a fresh stable release
   only after the remaining gates pass. Never rewrite immutable assets.

Linux native binaries remain 1.0.0 and x86_64 only; ARM64 server support comes from
pinned multiarchitecture images, not an ARM64 device test. Android remains Android
9+, while the official Umbrel app requires Android 11+. Drive login and Umbrel
login remain separate. No general Android bidirectional folder-pair sync, push
service, SSO, office server, full-text/OCR service, Synology ShareSync or DLP is
claimed. See FEATURES.md and the feature roadmap for the full comparison.

## Performance evidence

The prior 1.1.3 controlled browser benchmark measured 5.46 s to 0.25 s median
first-row readiness for a 1,004-entry folder; that remains a historical baseline.
The candidate retains narrow Depth-1 DAV requests, 200 rendered rows at a time,
content-hashed small assets and in-page folder navigation. Do not carry the old
95% improvement claim forward as a new measurement of this candidate. Local
candidate asset and API measurements are recorded in TESTING.md after final checks.

## Upstream references

[Official Android behavior](https://umbrel.com/support/getting-started/umbrel-for-android),
[Nextcloud Chunking v2](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/chunking.html),
[Nextcloud release schedule](https://github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule).


## Publication verification

Public CI [42743505981](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42743505981)
passed for candidate commit `37a0d73b1d8bd709654ede1fdebaabe945e72bef`.
The [immutable candidate release](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.2.0-rc.1)
published 16 assets. Android 1.1.0 reconstructed from asset commit
`3e8a3c816e9e49c5586da9a1db22b1c59da5d54f` matches the signed local APK and the
published SHA256SUMS. The published corresponding Android/Linux source archives
and server source ZIP were downloaded and checksum-verified. This completes the
public-CI/checksum gate above. The live Umbrel community-store catalog reports
1.2.0-rc.1, while the installed server remains 1.1.3 and ready.

The target-device observations used umbrelOS 2.1.0-beta.1 on amd64. Other OS/device
combinations are not implied by that result. The original app data and the selected
/Home/Umbrel Drive connection remain in place. No production uninstall, database
reset, preview-data migration or automatic photo-folder selection was performed.


## Native Android upgrade observation

Android accepted the signed 1.1.0 APK as an update to the installed 1.0.0 client.
The corrected splash and the Drive logo on the server-address screen were visually
verified. The browser's permission to install unknown apps was restored to disabled
after installation. During this session the Waydroid guest briefly showed black
screens and its boot animation; it recovered without a forced VM reset. No cause
was established, and this is not evidence of a diagnosed app crash. Native account
sign-in/upload/offline tests remain pending the owner's certificate decision.
