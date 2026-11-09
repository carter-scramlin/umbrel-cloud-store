# Umbrel Drive: Android integration, performance, and feature plan

Prepared 9 November 2026 against community server 1.1.1, the 1.1.2 patch,
Nextcloud 35.0.2, and umbrelOS 2.1.0-beta.1. Planned work below is not shipped
unless explicitly identified as part of 1.1.2. This remains a community app.

## Decision

Use the **official Umbrel Android app as the front door**: open Drive from Apps,
and reach the connected folder from Home → Files → View all. Keep the separate
Drive client for offline files and Drive uploads. This is feasible without changing
the official APK; it still needs a physical-phone compatibility test.

The official app supports Android 11+ and umbrelOS 2.0+. Pair it to the Umbrel host
without a port, then launch Drive from its installed-app list. The official app's
photo backup targets Umbrel Photos, not a configurable Nextcloud/WebDAV server.
Its Files entry opens native Umbrel Files. These are documented capabilities,
not a claim that our package has passed phone QA.
[Umbrel Android guide](https://umbrel.com/support/getting-started/umbrel-for-android).

Source review corroborates the launch and WebView path. The reviewed source is
pinned to [Umbrel c43beed](https://github.com/getumbrel/umbrel/tree/c43beed964074d08865d648ca9ac3359826a14ff/clients/android).
The exact Play build may differ from this source revision.

| Integration | Feasibility and proposed behavior | Dependency |
|---|---|---|
| Open Drive inside official Apps | Existing app-launch mechanism; retain port 8390 and HTTPS metadata. Sign in once with the separate Drive account. | Phone QA; no official APK change expected |
| Same documents in native Files and Drive | Already implemented for the selected folder. Native Files and Drive reference the same ordinary files; private Drive folders remain separate. | Owner must select the folder; member permissions are separate |
| Official photo backups visible in Drive | Add a second optional **read-only** folder slot, selected through Umbrel's picker, for the owner's Photos folder. Index originals in place. Do not duplicate uploads or make Drive delete the backup source. | New server feature, mount lifecycle/isolation tests; user selection |
| One sign-in for Umbrel and Drive | Requires a supported, scoped identity exchange and explicit account mapping. The official app's OS session does not authenticate Nextcloud automatically. | Confirm an upstream extension contract; otherwise keep separate login |
| Native Drive offline files, background folder pairs, or push in official app | No supported third-party sync extension was found in the reviewed code. A web app cannot supply a native WorkManager sync engine or Android document provider to another signed APK. | Upstream Umbrel participation or a separately maintained client |

The photo integration should start owner-only. Per-member Photos access must wait
for account/permission mapping; it must not expose `/Users` or other members'
backups through a broad host mount. The current picker connection can select a
Photos folder, but doing so replaces its existing selection; it is not yet the
second independent slot proposed here. The native backend chooses account-scoped
photo locations in [photos.ts](https://github.com/getumbrel/umbrel/blob/c43beed964074d08865d648ca9ac3359826a14ff/packages/umbreld/source/modules/photos/photos.ts).

## Performance findings and immediate patch

The reported issue is **opening pages and browsing folders**. Initial live
sampling found no sustained CPU or memory pressure. APCu and Redis were enabled;
OPcache was not full, had no out-of-memory restarts, and reported a 99.2% hit rate.
There were 13 indexed entries, so this sample does not establish large-library
performance. Increasing cache allocations or changing database engines would
not address an evidenced bottleneck in this installation.

Seven warm requests per route, with cookie/CSRF authentication and gzip enabled:

| Route | LAN median / maximum | Tailscale median / maximum |
|---|---:|---:|
| Files HTML | 160 / 281 ms | 124 / 193 ms |
| Devices & Files HTML | 142 / 268 ms | 199 / 355 ms |
| Selected-folder listing, DAV Depth 1 | 222 / 368 ms | 164 / 243 ms |

These are HTTP request times from the development machine, including connection
overhead. They are **not** browser time-to-interactive, rendering measurements,
or proof of performance on a large folder. The selected folder was essentially
empty. Network variance was substantial; these values are a baseline, not a speed
guarantee. Live browser profiling was unavailable through the current connector.

The HTML referenced 50 script/style URLs totaling 8,718,508 uncompressed bytes
and 1,898,302 gzip transfer bytes. This inventory includes alternate theme styles;
a browser may fetch or prioritize them differently. The largest script alone was
5,785,882 decoded bytes. Existing gzip and long-lived versioned asset caching
were already enabled.

**1.1.2 change:** negotiate Brotli for the main static bundle directory and static
core/theme CSS, retaining gzip and identity fallback. Locally verified sizes:

| Asset | Gzip bytes | Brotli bytes | Transfer reduction |
|---|---:|---:|---:|
| core-common.js | 1,217,320 | 1,056,952 | 13.2% |
| core/css/server.css | 17,638 | 16,475 | 6.6% |
| Umbrel Drive theme CSS | 1,869 | 1,732 | 7.3% |

Decoded responses match byte for byte. Encoding-specific negotiation, `Vary`,
immutable cache headers, and non-Brotli clients are covered by a regression test.
Dynamic PHP/DAV/download responses retain upstream behavior. This improves cold
asset transfer; it does not reduce decoded JavaScript size or guarantee faster
folder requests. [Apache compression behavior](https://httpd.apache.org/docs/2.4/mod/mod_brotli.html),
[Nextcloud tuning guidance](https://docs.nextcloud.com/server/latest/admin_manual/installation/server_tuning.html).

## Implementation sequence and release gates

1. **Stability and delivery — 1.1.2.** Ship the measured compression change and
   Android connection guidance. Run asset integrity tests, cookie sign-in under
   deliberate shared-network name collisions, file/version/trash/sharing tests,
   Files round trips, and folder replacement/disconnect isolation. Update the
   existing app without uninstalling it. Repeat live authenticated checks.
2. **Official Android compatibility.** Test the current Play app on Android 11
   and a current Android version: pairing, opening Apps → Drive, credentials
   display, Drive login persistence, system Back, upload picker, PDF/photo preview,
   download/share, sign-out, account switching, and reconnect. Repeat on LAN and
   Tailscale. Use the official certificate-pairing flow. Gate: no certificate
   bypass, account leakage, or broken file transfers. Fix community-side issues;
   record any issue requiring an upstream change.
3. **Faster page and folder interaction.** Capture a real browser performance
   trace and distinguish download, JavaScript execution, preview work, and DAV
   calls. Keep folder navigation inside the existing app session. Profile with
   representative nested libraries and 100/1,000/5,000-entry folders; compare
   cold/warm loads, five-client concurrency, and background scans. Proposed LAN
   goals: warm folder display p95 under 500 ms for a 1,000-entry fixture; cold
   usable page under 2 seconds on a specified reference device/network. These
   are acceptance targets, not current results. Reduce/defer optional startup
   modules only after tracing proves they are on the critical path. If upstream
   bundles remain the limit, build a smaller default browser progressively,
   retaining the full interface until sharing, recovery, accessibility, and all
   essential operations have equivalent coverage.
4. **Smarter indexing and updates.** Replace unconditional recursive minute scans
   with a debounced change queue for local storage, bounded batches, a single
   writer, and a periodic repair scan. Keep a polling fallback for network shares
   and dropped events. Evaluate Nextcloud's compatible server push service for
   change notification; mobile push credentials are a separate task. Gate:
   nested native Files edits update ancestor ETags, missed events self-repair,
   scans do not overlap, and folder swaps cannot leak through old links. Target
   local change visibility under 5 seconds during normal operation.
5. **Shared Files, Photos, and recovery.** Add the read-only Photos slot, explicit
   folder status, permission mapping design, and clear recovery entry points.
   Keep native Photos as the only automatic uploader when it is selected. Explain
   whether the user is operating on private Drive storage or connected Files.
   Drive cannot reconstruct an overwritten file after an external edit: whole-
   folder recovery must coordinate snapshots/backups with database metadata,
   rather than promise Drive versioning for edits that bypassed Drive.
6. **Feature releases.** Deliver the prioritized gaps below as separate tested
   releases. Office/search services remain optional so they do not slow the base
   file browser. Add migrations and restore drills before enabling new storage
   or recovery behavior by default. Retain signed client update continuity.

Do not merge development into the official Android application under its name or
claim official status. If an extension contract is necessary, prepare a concrete
upstream proposal; the current plan does not publish or submit one.

## Feature inventory and remaining work

Included capabilities come from the pinned Nextcloud engine. A shipped upstream
feature is not equivalent to physical-device QA. The existing
[feature matrix](https://github.com/carter-scramlin/umbrel-cloud-store/blob/main/cartercloud-drive/FEATURES.md) and
[test record](https://github.com/carter-scramlin/umbrel-cloud-store/blob/main/cartercloud-drive/TESTING.md) remain the detailed baseline.

| Capability | Current coverage | Remaining work / priority |
|---|---|---|
| File operations, list/grid, sorting, favorites, recent files, tags | Included; core operations API tested | Accessibility, keyboard and mobile interaction QA; P1 |
| Protected sharing, expiry, revocation, upload requests | Included and API tested | Central link review/export, access-request inbox and clearer inherited permissions; P1 |
| Team-owned folders and ACLs | Team folders included | First-class setup, lifecycle, storage reporting, member permission tests; P1 |
| File history and trash | Included for Drive-mediated changes | Policy UI, consistent whole-folder rollback and recovery across native edits; P1 |
| Linux two-way/selective sync | Branded native client tested for transfer round trip | Supported distro/shell matrix, conflict UX, resume/large-transfer soak tests; P1 |
| Linux on-demand files | Experimental upstream implementation | Filesystem/kernel QA and safe hydration/eviction; P2 |
| Linux one-way folder tasks | No general one-way upload/download task UI; upload-only backup helper is separate | Add explicit direction/rules and deletion policy; P2 |
| Desktop computer backup | Separate upload-only full-snapshot helper | Incremental storage, retention, scheduling UI and restore wizard; P1 |
| Android offline, camera upload, scanning | Included in separate Drive APK; device QA pending | Real-phone battery/reconnect/offline-edit tests; P1 |
| Arbitrary Android one/two-way folder tasks | Not included | Scoped-storage folder grants, conflict-safe queue, pause/rules and retries; P2; separate client or upstream |
| Android document-provider and remote-wipe support | Upstream client code exists | Validate branded build/account isolation and actual wipe scope; do not count source presence as a tested feature; P1 |
| Reliable push | Independent credentials/service not configured | Separate desktop/browser change push from Android notifications; test transport and revocation; P2 |
| Office documents, spreadsheets, presentations | Plain-text collaboration included; no office service bundled | Integrate compatible office service, preview/edit dispatch and document permission tests; P2 |
| PDF forms, annotations and signatures | Viewing included; editing coverage not established | Verify existing client/OS editors, save-back conflict handling, add missing tools; P2 |
| Search inside documents and scanned images | Filename search included | Optional extraction/OCR index, permission-filtered results, incremental reindex/status; P2 |
| Shortcuts, folder colors, saved collections | Favorites/tags provide partial organization | Native-feeling shortcuts without duplicate files, color metadata and saved filters; P2 |
| Document comments and reviews | Generic comments/activity and Text supplied upstream | Office suggestions, assignments and consistent notifications require editor integration; P2 |
| Ownership transfer | Upstream file-transfer controller exists | Expose appropriately and verify private vs team/external storage semantics; P2 |
| Approval workflows and e-signature requests | Not bundled | Optional workflow/signing service, locked revision and receipt trail; P3 |
| Device administration and policy | App passwords, sessions, TOTP and audit facilities included | Validated device inventory/revocation/wipe, server-enforced transfer rules and useful audit UI; P2 |
| Cross-server replication | WebDAV/federation available; no managed replication UI | Scheduled one/two-way jobs, permissions policy, conflicts and recovery; P3 |
| Watermarks and restricted-download policies | No complete policy engine configured | Evaluate compatible access-control/editor features; do not promise protection for downloaded copies; P3 |
| Optional semantic search and summaries | Not bundled | Permission-aware local model/index, explicit resource budget, source links; P3 |
| Public internet share links | Link permissions work; no public endpoint is automatically configured | Optional trusted HTTPS publishing with explicit scope, correct URLs and abuse controls; P2 |
| Migration from cloud drives or NAS | No turnkey migration wizard | Import/export ordinary files, export proprietary documents, verify counts/hashes and ownership; P2 |
| End-to-end encryption | Not enabled or claimed | Optional encrypted spaces only after client/recovery compatibility testing; full server search and preview cannot operate on opaque content; P3 |
| Backup/disaster recovery | Operator must back up private app state and connected folder | Consistent DB/file backup, retention, integrity verification and a tested restore; P1 |

Comparison boundaries: Synology supplies point-in-time recovery, managed client
rules, mobile sync tasks and multi-site features that require additional work
here. Its on-demand desktop availability is platform-specific; Linux on-demand is
our own compatibility target, not a claim about Synology Linux support. Proprietary
DSM/ShareSync and Synology Office formats are not drop-in protocols for this app.
[Synology specifications](https://www.synology.com/en-us/dsm/7.4/software_spec/synology_drive).

Google Drive adds useful organization and collaboration patterns. We should copy
the useful interactions, while storing ordinary files and compatible metadata;
Google Docs/Sheets/Slides services and proprietary formats are not replicated by
adding buttons. Some comparison features require eligible paid Workspace/AI
plans in Google's product. References:
[organization and shortcuts](https://support.google.com/drive/answer/2375091?hl=en),
[sharing roles](https://support.google.com/drive/answer/7166529?hl=en),
[OCR](https://support.google.com/drive/answer/176692?hl=en),
[approvals](https://support.google.com/drive/answer/9387535?hl=en),
[eSignature](https://support.google.com/drive/answer/12315692?hl=en),
[AI summaries](https://support.google.com/drive/answer/16686465?hl=en).

Priority order: **reliable and fast browsing → official-app compatibility → safe
recovery/backup → office and content search → advanced mobile sync and policies**.
Feature parity is a roadmap, not a claim made by the 1.1.2 patch.

## Delivery record

Server 1.1.2 was published in the Carter Cloud community store and as a
[preview release](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.2).
The [full regression workflow](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42568034065)
passed browser-cookie sessions under deliberate database/cache name collisions,
restart persistence, seven grouped file API tests, static asset integrity, native
Files round trips, selected-folder replacement/disconnect isolation, backup safety,
and source packaging. Native client binaries were verified against their existing
checksums; they were not rebuilt for this server-only patch.

The installed app was updated in place to 1.1.2 and reached ready. Its existing
selected folder remained connected. Live HTTPS cookie/CSRF sign-in and authenticated
Files/setup access passed on both LAN and the normal Umbrel hostname. Through
Umbrel's real HTTPS proxy, the 50 referenced script/style resources transferred
**1,701,962 bytes versus 1,898,302 bytes before (10.3% less)**. Twenty-four resources
negotiated Brotli, and all requests succeeded. The largest script remained 13.2%
smaller; the decoded application code is unchanged.

Repeated page/folder timings varied in both directions: LAN Files HTML median
160 → 137 ms and folder listing 222 → 181 ms; Tailscale HTML 124 → 162 ms and
listing 164 → 230 ms. These small samples do **not** establish a consistent latency
improvement or an update regression. The patch changes static transfer, not the
DAV implementation. Further browser tracing is still necessary to resolve the
reported browsing delay.

## Faster default browser — 1.1.3

The 1.1.3 candidate implements the smaller default file browser described in phase 3,
while retaining the full workspace for advanced tools. The controlled local test
measured a 95.4% lower median first-row readiness time on a 1,004-entry folder. See
[the complete speed report](umbrel-drive-1.1.3-speed.md) for raw samples, definitions
and limits. Android integration remains unchanged and awaits the user's follow-up.
