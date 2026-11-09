# Umbrel Drive 1.1.3 — speed verification

9 November 2026. This release changes the default browser while retaining the
Nextcloud storage/sync engine and original full workspace. Android integration
is deferred; Linux and Android native binaries remain unchanged at version 1.0.0.

## What changed

The new entry point loads one small script and stylesheet, navigates folders in
place, requests only required DAV metadata, and initially renders 200 rows with
Show more for larger lists. It avoids loading the full workspace's framework,
recommendations, editor and preview modules for ordinary browsing. Previewing an
image is explicit. Assets use content hashes so updates cannot leave old scripts
in a browser's immutable cache.

The fast interface supports folder creation, uploads up to 256 MiB, rename,
move/copy without overwriting, favorites and read-only public-link management.
Full workspace remains accessible for advanced sharing, versions/history, trash,
team administration and resumable/large uploads. No storage migration is performed.

## Browser measurement

A real Codex in-app browser loaded an isolated Nextcloud 35.0.2 / PostgreSQL / Redis
stack with a synthetic folder containing **1,004 entries**: 1,002 small text files
and two folders. This is the development host, not a live-browser trace on the NAS.
The existing full workspace and the new browser used the same backend, credentials,
folder and browser profile. Six page loads of each were alternated. Browser caches
were reused; this is not a controlled empty-cache or throttled-mobile benchmark.

Timing starts at browser navigation and ends when the first expected folder rows
are attached and have nonzero layout. It includes document load, script startup,
metadata request and initial layout. It is not LCP, INP, complete image loading, or
proof of the exact time pixels reach a physical display. The full view virtualizes
rows; the lightweight view renders an initial 200. Measurements come from opt-in
application instrumentation and are exposed in the DOM, not estimated from tool
wall-clock time.

| Trial | Full workspace, ms | Lightweight browser, ms |
|---|---:|---:|
| 1 | 4,366.9 | 251.3 |
| 2 | 6,376.2 | 246.0 |
| 3 | 5,476.9 | 256.9 |
| 4 | 5,472.6 | 255.7 |
| 5 | 5,456.5 | 252.4 |
| 6 | 4,481.9 | 249.6 |
| **Median** | **5,464.6** | **251.9** |

The median decreased **95.4%**:
**5.46 seconds → 0.25 seconds** for this test. All six samples, including slower
runs, are reported. This is a measured improvement in opening the file browser,
not a claim that database queries, native sync, or every advanced feature became
that much faster.

Six fresh in-page navigations back into the same folder measured:
`174.3, 174.2, 168.3, 171.1, 178.7, 156.4` ms.
The median request + parsing + layout time was **172.6 ms**.
Every navigation made a fresh DAV request; there is no application folder-result
cache hiding a network fetch in these numbers. Auto-refresh is separate and runs
only when the visible page is idle.

An earlier prototype waited for requestAnimationFrame before recording completion.
That produced approximately one-second waits in the background test browser.
The final method forces layout directly in both views, avoiding background-frame
throttling. Preliminary figures from the older method are superseded by the six
alternating trials above.

## Verification completed locally

- Real browser: create a folder, upload a file, rename with accented characters,
  `#` and `&`, favorite, copy, move, create/revoke a protected link and delete a
  disposable file. Download URLs and context links point at the correct objects.
- A filename resembling an HTML image element rendered as literal text.
- The default sign-in destination is the fast browser. Anonymous requests are
  denied. Account HTML is no-store, scripts retain CSP nonces, and cookie-based
  writes with an invalid CSRF token fail while valid writes succeed.
- Initial decoded JavaScript/CSS is about **28 KB**, compared with multi-megabyte
  bundles in the full workspace. An automated budget check prevents accidentally
  reintroducing the large common bundle into the fast shell.
- Brotli/gzip/identity decoding produces identical static assets. Existing
  full-workspace static resources remain available and keep their caching behavior.
- Existing-data upgrade, PHP/JavaScript syntax, Apache configuration and package
  checks run before publication. CI gates release publication on the complete
  file/share/version/trash, Files bridge lifecycle, shared-network/session, backup,
  asset and source-packaging regression suite.

The initial upload picker test stalled long enough for its page's CSRF session to
expire. After a reload, a bounded retry uploaded successfully. This did not alter
production data and is not counted as a successful first attempt.

## Live deployment and limits

The [full regression workflow](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42610163187)
passed and [1.1.3 was published](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.3).
Runtime commit: `fb6b8e9c6ec2fb8c64edf2ef355578919b6c2c76`.
The installed app was updated in place and reached **ready, version 1.1.3**. Its
existing Files selection was preserved. Live HTTPS cookie/CSRF sign-in, the default
fast-browser redirect, private no-store HTML, setup/full-workspace access and a
successful selected-folder Depth-1 listing passed on LAN and the usual Umbrel
hostname. TLS verification and hostname checks stayed enabled with a process-local
certificate pin; no browser security warning was bypassed.

The real HTTPS proxy served exactly two initial script/style files totaling
**8,904 Brotli bytes** (28,098 decoded bytes). The previous full-workspace inventory
was 1,701,962 bytes: approximately **99.5% less initial script/style transfer**. This
comparison excludes document HTML, icons/fonts and folder-response data.

Seven live HTTP samples per route, including connection overhead:

| Response on installed 1.1.3 | LAN median | Tailscale median |
|---|---:|---:|
| Fast browser HTML | 81.5 ms | 144.3 ms |
| Retained full-workspace HTML | 168.4 ms | 175.0 ms |
| Connected folder DAV listing | 136.5 ms | 121.3 ms |

These are HTTP measurements, not a live browser render benchmark. The connected
folder was essentially empty. The 1,004-entry browser result above is from the
isolated development environment. The baseline 1.1.2 full-workspace HTML medians
were 109.0 ms on LAN and 184.7 ms over Tailscale, so network/host variance remains
visible; the strongest verified improvement is removal of the large frontend
startup workload. Very large libraries, slow network shares, complex documents,
physical Android behavior and long-duration sync remain outside this benchmark.

Temporary live credentials were deleted after verification, and local test
containers were stopped. The live app remains running.

Reopen Umbrel Drive from Umbrel after updating. Old /apps/files/... bookmarks keep
opening the full workspace. The connected Umbrel Files folder and native clients
use the same backend and data. The existing Files indexing interval is unchanged.
