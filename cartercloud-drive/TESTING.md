# 1.2.0-rc.2 verification

- Five integration groups pass for owner/member isolation, cookie/CSRF protected
  remote settings, exact Tailscale host registration/replacement/clear (including
  IPv4, IPv6 and scheme normalization), and copy-to-Files preserving source/conflicts.
- A registered host and authenticated owner session survive an ordinary app restart.
- Nine JavaScript checks pass: uploader fault handling plus library boundaries,
  read-only copy restrictions, unknown quota handling and HTTP-compatible random IDs.
- HTTP cookie sign-in/upload, CSP/nonces, no-store account HTML and the one-script/
  one-style budget pass. Decoded JS/CSS totals **45,178 bytes**, with **13,537 Brotli
  bytes**. DAV folder metadata remains unchanged; no new browser timing is claimed.
- Linux 1.1.0 builds and its Qt profile/dialog/status tests pass. The settings dialog
  was rendered and inspected; the AppImage starts with xcb on Fedora 44 using isolated
  XDG configuration. Its engine version stays 35.0.3 (build 2).
- Eight Android address/login-transport tests pass, covering explicit HTTP browser
  selection and no HTTPS downgrade. Release build/lint/Detekt/Spotless and same-key
  signature/16 KB alignment checks pass. SpotBugs remains a partial upstream scan
  because analysis dependencies are missing; see release readiness.
- Six backup-helper tests pass, including explicit HTTP authentication, no-overwrite
  headers, symlink/exclusion safety and refusal of every redirect.
- Source packaging and fresh pinned-source application of both overlays pass.
- Official Umbrel linter commit 3a087384be96ea6890a7428f62e28a2203c1ea6e:
  zero errors, four existing image-digest/hardening warnings. Runtime digests remain
  pinned to the tested images.

The local browser retry remains blocked by a saved site-permission setting. No
alternate surface bypass is used. Android settings UI and WAN/native upload/offline
QA remain unverified for this client update. Earlier verification is scoped below.

# 1.2 release candidate verification

The current candidate's complete results and remaining stable-release gates are
recorded in [release readiness](../docs/umbrel-drive-release-readiness.md).
Android 1.1.0 rebuilt successfully with lint, Detekt and Spotless. Its APK
version code is 350000291, and signature/16 KB alignment checks passed with the
original signing certificate. The APK SHA-256 is
`dfac8c8b70782810573fe826dafe5b922ecd95093319dcf9c127ce8d7a058ad3`.
Native sign-in/upload/offline QA is pending the owner's private-certificate trust
decision; the APK installation and launch were checked for 1.0.0.

New checks cover chunked uploads, no-overwrite conflicts, cancellation, native
photo originals, stopped-snapshot restore, and the official Umbrel Android app.
Final candidate assets total **34,883 decoded bytes**: 24,890 bytes of JavaScript
and 9,993 bytes of CSS; Brotli is **10,790 bytes** combined. The one-script/one-style
100 KB budget, CSP, cache isolation, and cookie/CSRF checks passed. This is an asset
measurement, not a browser paint or folder-readiness benchmark.

A 1,004-file isolated folder returned its complete DAV XML in **130.32 ms median**
over seven cookie/CSRF-authenticated warm requests (one warmup excluded). Samples:
128.94, 130.01, 140.20, 130.32, 133.02, 142.95, 121.31 ms. This measures the
server request/body, not browser rendering, cold cache, live LAN or phone speed.

The 1.0/1.1 verification history below remains scoped to its original versions.

# Verification record — 2026-11-08

## Server and packaging

- Ran the pinned Nextcloud 35.0.2 / PostgreSQL 17 / Redis 7.4 stack in isolated
  local Docker projects, including a completely fresh data directory.
- Fresh startup downloaded Team folders 23.0.1, verified its archive SHA-256,
  enabled it with the theme, and presented the branded initial file view.
- Seven live API tests passed: authentication/branding; file upload/download,
  copy/move and stale-ETag rejection; previous-version download and restoration;
  trash/restoration; password/expiry links and revocation; upload-only links;
  account isolation and an enforced 1 MiB quota.
- A full stop/start of the test stack preserved the account, credentials,
  PostgreSQL state, and the file modified during the native-client test.
- Browser checks confirmed sign-in, file navigation, branded onboarding, and
  the device setup page. Screenshots show the running server, not mockups.
- Four backup-helper tests passed: snapshot contents/hashes and empty folders,
  symlink/exclusion behavior, interrupted-upload completion safety, HTTPS
  validation, and redirect refusal (some assertions are grouped in one test).
- A fresh-source release packaging test passes: all three file-manager modules
  are generated from the canonical upstream source, preserve SPDX notices, and
  omit build caches from corresponding-source archives.
- Python files compile, shell scripts parse, YAML parses, and Git whitespace
  checks pass. An automated GitHub release workflow repeats server/API checks
  and verifies native binary SHA-256 hashes before publishing downloads.

## Linux client

- Compiled the pinned Nextcloud Desktop 35.0.3 source with Umbrel Drive branding
  using the upstream Qt 6.11.2 AppImage builder.
- The AppImage launched under Xvfb with a D-Bus session and reported its branded
  name, pinned Git revision, and Qt version. Initial headless-only attempts failed
  because the package includes the XCB backend; the virtual-desktop check passed.
- The compiled native sync command uploaded a local file, then downloaded a
  server-side edit. Downloaded content was checked. This exercises the same sync
  libraries bundled by the GUI client.
- Nautilus/Nemo/Caja modules are provided separately with original SPDX copyright
  notices. Real desktop shell integration and OpenVFS require distro-specific QA.

## Android client

- `assembleGenericRelease` passed, including release-vital lint, from the pinned
  Nextcloud Android 35.0.2 source after branding.
- `zipalign -c -P 16 4` passed. The signed APK verifies with APK Signature Scheme
  v3, suitable for its Android 9+ minimum. Certificate SHA-256:
  `4ccb80a94c3cffae93bdc2f35e122a09a19bb6bd0917e69c9322846286f57235`.
- Full `lintGenericRelease`, `detekt`, and `spotlessKotlinCheck` passed.
  Launcher round-icon resources were corrected before the final build.
- `spotbugsGplayDebug` ran and reported findings plus missing reference classes
  (including Google cloud messaging, Coil, ConstraintLayout, and some JDK
  collection classes). Its analyzer returned code 3. Upstream configures
  `ignoreFailures = true`, so the Gradle task set completed successfully; this
  is not a clean SpotBugs result and is not presented as one.
- No physical Android device or emulator was used. Camera upload scheduling,
  offline behavior, document scanning, battery restrictions, and device-specific
  interactions remain unverified. Do not interpret build/signature success as
  physical-device QA.

## Limits

The 1.0.0 package was installed through the connected umbrelOS 2.1.0-beta.1
App Store on an amd64 device and reached ready. The integration update is also
checked through a fresh isolated Compose install and an upgrade from 1.0.0.
The browser's local Umbrel HTTPS certificate is not trusted in this automation
profile, so live HTTPS browser interaction remains unverified. Certificate
validation was not bypassed. Android physical-device behavior, backup restoration,
arm64 runtime, large-library/load behavior, and long-running failure recovery
remain unverified. This is a community preview.

## Umbrel Files integration, server 1.1.0

- A real selected-folder fixture passed ordinary-file round trips between the
  filesystem and Drive DAV: creation, content checks, editing, rename, and deletion.
- The background worker detected out-of-band changes and updated ancestor ETags
  without manually running an index command. Drive-created files use UID/GID 1000.
- A second account could not access the folder until it was explicitly shared.
- Umbrel's package linter passes image/platform and manifest checks with zero
  errors. One intentional warning concerns Redis's `no-new-privileges` hardening.
- Runtime source is bundled reproducibly into a top-level template and installed
  by the update-whitelisted pre-start hook. A stale-bundle check runs in CI.
- A fresh no-folder installation, connection to folder A, replacement with folder B,
  and clearing the folder all passed. An old public link did not expose a same-named
  file in folder B, both original folders remained intact, and private Drive files
  survived the restart sequence.
- Browser checks of the integration status and Open connected folder shortcut
  passed against the running local server; a real file created outside Drive was
  visible in the connected folder view.

## Browser failure remediation, server 1.1.1

A shared-network test reproduced 1.1.0 login responses alternating between HTTP
200 and 500 when another Redis used the generic redis alias. The error log showed
Redis authentication/session failures. Isolated Compose testing did not model
this Umbrel deployment condition, and earlier Basic-auth file API checks did not
prove browser-cookie sign-in.

The fix assigns unique service aliases, overrides legacy dbhost configuration
before startup, and makes health checks load the login page. New tests perform
repeated login-page requests, real cookie/CSRF sign-in, authenticated Files access,
and Devices & Files rendering under deliberate db/redis DNS collisions, including
a container restart. Existing 1.1.0 test data and credentials were preserved.

## Browser transfer optimization, server 1.1.2

The isolated existing-data stack was upgraded through the runtime bundle/pre-start
path. Cookie/CSRF sign-in, Files access, and Android connection guidance render
correctly. Static asset tests compare decoded identity, gzip, and Brotli responses
byte for byte, check encoding negotiation/Vary and immutable cache headers, and
verify that dynamic status.php stays on the upstream path. The largest script is
13.2% smaller in transfer than its existing gzip response. Full web interaction
latency and physical-phone compatibility are not established by these checks.
The release workflow repeats shared-network, file workflows, Files bridge lifecycle,
backup, source packaging, and asset-integrity regressions before publication.

See [the measured baseline and roadmap](../docs/umbrel-drive-roadmap.md) for
performance boundaries and features that remain planned.

## Lightweight browser, server 1.1.3

A real local browser exercised folder creation, file upload, Unicode/symbol rename,
favoriting, copy, move, protected link creation/revocation, and deletion
of disposable fixtures. An HTML-looking filename rendered as text. A 1,004-entry
synthetic folder was used for alternating full-workspace/lightweight load trials and
in-page navigation measurements. A stalled upload test initially outlived its CSRF
session; after reloading, the bounded retry completed successfully.

The dedicated regression verifies the authenticated default entry, anonymous denial,
CSP nonces, no-store account HTML, a decoded JS/CSS budget, content-versioned caches,
and cookie writes with valid/invalid CSRF tokens. Brotli/gzip/identity responses remain
byte-identical. Browser timing does not establish Android behavior or the performance
of arbitrary network shares, file formats, or much larger libraries.

See [the 1.1.3 speed report](../docs/umbrel-drive-1.1.3-speed.md) for final measurements.
