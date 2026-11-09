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

A live umbrelOS installation was not modified during development. Community-store
refresh, Umbrel HTTPS/proxy behavior, device access, backup restoration, arm64
runtime behavior, large-file and multi-user load tests, and long-running failure
recovery require target-device validation. This is a community preview.
