# Umbrel Drive 1.2 release readiness

This is a community release candidate, not a declaration of complete Synology or
Google Drive parity or official Umbrel endorsement. Stable promotion is held until
the new browser UI has completed visual and interaction checks. Existing live
1.1.3 data and clients have not been uninstalled or reset.

## 1.2.0-rc.2 additions

This candidate adds **Your Umbrel** for account storage, connected-folder status,
native storage settings and exact remote-host registration. Status reflects the
background indexer's last report. A disconnected or conflicting folder name is
never labeled as a connected library. Folder banners explain shared Files and
read-only Photos; Copy to Umbrel Files preserves the source and refuses conflicts.

Android 1.2.0 and Linux 1.1.0 add saved local/Tailscale address profiles. They use
an installed Tailscale app/service, and do not embed a VPN, collect Tailscale keys,
join a tailnet or modify its access policy. Linux can read CLI connection state;
Android can open/install the official Tailscale app. Profiles apply to new sign-ins;
existing sync accounts retain their address and credentials. Use a Tailscale URL
for sync at home and away; never point two accounts at the same local sync folder.

The original umbrel account can register an exact Tailscale IPv4/IPv6 or .ts.net
host. This is a CSRF-protected setting, hidden from other accounts, with no wildcard
trust. Replacing or clearing removes only a host managed by this setting. It does
not grant network access or prove that Tailscale is connected. HTTP is available on
device port 8391; native clients require explicit HTTP selection. HTTPS remains
8390 with certificate verification. HTTP has no TLS encryption and needs a trusted
transport, such as Tailscale. No router forwarding or public Funnel is configured.

New local checks pass: five owner/member/CSRF/remote-host/copy/HTTP-login API groups, a saved
host/session restart rehearsal, nine JavaScript uploader/context/quota/HTTP-ID cases,
HTTP cookie sign-in and upload, CSP/cache/encoding checks, and source packaging.
Initial JS/CSS total 45,178 decoded bytes (33,879 JS + 11,299 CSS); combined
Brotli is 13,537 bytes. Storage queries run on demand, outside folder loading.
Linux profile/dialog/status Qt tests pass; the dialog was rendered and inspected,
and the packaged AppImage starts with the xcb plugin on Fedora 44 using isolated
configuration. Its visible engine version remains 35.0.3, build 2; package version
is 1.1.0. Eight Android address/transport tests pass. Explicit HTTP uses the standard browser
login flow because Chrome Auth Tab disallows HTTP. Login, poll and returned server
URLs reject a downgrade from an HTTPS origin, even when another profile permits
HTTP. Invalid transport closes the failed sign-in and stops its poller; the raw
Login v2 poll-response debug log was removed. Android release assembly, lint (zero errors), Detekt and Spotless pass. APK signature
v3, 16 KB alignment and same-key upgrade identity pass; version code is 350000292.
APK SHA-256: `4d43f7bfa588070666b1ecd799a2b2070c7814f7a464da886d36e2f297c7ec0d`. The settings UI was subsequently checked on Android 13; see the rc.2 publication verification below. Umbrel package lint at official tooling commit
3a087384be96ea6890a7428f62e28a2203c1ea6e reports zero errors and four warnings
(the existing Redis hardening option and rebuilt upstream Nextcloud/Redis tags).
Tested image digests remain pinned.

The browser retry on 2026-11-10 was rejected by the same saved site-permission block
for 127.0.0.1:18394. No alternate surface is used to bypass it. End-to-end remote/native upload/offline device QA remains a separate gate.
No production update or reset was performed. The Umbrel MCP app-details version
can reflect its cached store catalog; it is not used as runtime-version proof.

The verification history below describes rc.1 unless a new result is stated above.

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

## Remaining stable-release gates for the current candidate

1. Visual/interaction checks of the new 1.2 desktop and phone layouts, keyboard
   navigation, upload progress/cancel/conflict messages, read-only folders, login
   themes, and navigation back to Umbrel. The browser tool rejected localhost:18394
   first as declined and then as a saved site-permission block, even after the owner
   explicitly approved access. No alternate surface is used to bypass that block.
2. Native Drive Android 1.2.0 upload/download/offline smoke tests. Build, lint,
   signature and source packaging passed. Both the initial APK install and the
   same-key upgrade to 1.1.0 succeeded in the VM; local DNS was unavailable,
   so direct LAN IP was tested. Its certificate dialog matches the live Umbrel
   SHA-256, and trust is waiting for the owner’s decision. Browser-source install
   permission was restored to disabled after installation. Android 1.1.0 fixes the
   observed upstream logo and run-on splash branding, builds with lint/Detekt/Spotless,
   and passes signature/alignment checks with the original key. The corrected splash
   and sign-in logo rendered after upgrade. Upload/offline and physical-phone
   background media behavior still require device QA.
3. Green public CI and published checksums must match the current candidate.
   rc.1 publication verification is recorded below; rc.2 must complete its own
   workflow before the store catalog advances. Promote a fresh stable release
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


## rc.1 publication verification

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

[Chrome Auth Tab protocol rules](https://developer.chrome.com/docs/android/custom-tabs/guide-auth-tab),
[Tailscale MagicDNS](https://tailscale.com/docs/features/magicdns).


## Static-analysis scope

The upstream GenericDebug SpotBugs task ran and reported missing analysis classes
(exit 3, tolerated by upstream ignoreFailures). Its partial report contains 352
findings. No finding is reported for the new Java login policy or profile-result
callback; the callback null-return issue discovered during this work was fixed.
Six pre-existing AuthenticatorActivity findings match the earlier upstream-method
baseline. This is not a clean whole-app SpotBugs scan or an independent audit.
The eight focused URL/transport tests and the release lint/Detekt/Spotless checks
passed. Android ignores pending Login v2 poll responses until a valid success;
HTTP and HTTPS never share a partially completed account through profile selection.

The upload-only backup helper accepts explicit --allow-http and rejects non-boolean
configuration flags. Six backup safety tests pass, including a real localhost HTTP
request with authentication and no-overwrite headers. Every redirect remains blocked.


The signed Android APK and Linux AppImage were reconstructed from the public asset
commit `ec41c4d413cf3e026bb7fc7f4c7ad6f706ed1de2` and their complete SHA-256 hashes
matched the local checked packages. Linux 1.1.0 SHA-256:
`ca7b87886b93e4faa4b1ab54f10817e21b837eca16259f999bb331ea82962b59`.
The source build helper now captures the same Linux build-2 and pinned-source
builder workarounds used for the checked AppImage. Native APK/code source overlays
match the corresponding freshly branded trees. The exact candidate must pass the
public release workflow on `umbrel-drive-rc2` before advancing the store's main
branch; the immutable release will then already contain its downloads.


## rc.2 publication verification (2026-11-11)

Public CI [42966057657](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42966057657)
passed for source commit `32fe054db92aebd95dd8fc8224d5c0df0469798d`.
The [1.2.0-rc.2 release](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.2.0-rc.2)
is marked prerelease and contains 16 assets. Its target commit is that same tested
source. Main was advanced to that commit only after publication and public checksum
verification. This supersedes the pre-publication gate described above.

The published SHA256SUMS and GitHub asset digests match the signed Android APK
and Linux AppImage. Both published corresponding native source archives and the
server source ZIP were downloaded and checksum-verified. Android 1.2.0 SHA-256:
`4d43f7bfa588070666b1ecd799a2b2070c7814f7a464da886d36e2f297c7ec0d`.
Linux 1.1.0 SHA-256:
`ca7b87886b93e4faa4b1ab54f10817e21b837eca16259f999bb331ea82962b59`.

Android 13 accepted the published 1.2.0 APK as an update to 1.1.0. The sign-in
Remote access screen rendered with local selection and Allow HTTP unchecked.
Saving an HTTPS Tailscale address and selecting that profile updated the sign-in
address. Reopening the settings retained both the address and selection. The local
profile was then restored as the default for new sign-ins; HTTP remained disabled.
The Browser permission to install unknown apps was restored to disabled immediately
after the update. No native account sign-in, certificate acceptance, upload, offline
transfer, or connection to the tailnet is implied by this settings-only check.

The installed server remains ready with no active operation or last-operation
failure. It was not updated, reset or uninstalled during rc.2 publication. The new
web UI still needs its browser visual/interaction gate; automatic approval review
rejected the same local URL because of the saved browser site-permission setting.
Stable promotion remains pending that gate and end-to-end native transfer QA.
