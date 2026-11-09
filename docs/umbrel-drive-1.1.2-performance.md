# Umbrel Drive 1.1.2 — delivery and performance verification

9 November 2026. Runtime commit: `f55ccdddea62247a71ef029c1badf16a00eb795a`.

Published the [1.1.2 preview](https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.2)
and updated the installed app in place. Umbrel reports version 1.1.2, ready.
The connected Files folder was preserved. No data reset or uninstall was used.

## Measured result

The live HTML references 50 script/style resources. With the normal browser
encoding negotiation, total transfer fell from 1,898,302 gzip bytes to 1,701,962
bytes with Brotli/gzip/identity negotiation: **10.3% less data**. The largest bundle
fell from 1,217,320 to 1,056,952 bytes: **13.2% less**. Twenty-four resources used
Brotli through Umbrel's HTTPS app proxy, with no failed resource requests.
This is a resource inventory, including alternate theme styles, rather than a
browser waterfall. It does not measure all lazy-loaded chunks, images or fonts.

| Warm authenticated request | LAN before → after median | Tailscale before → after median |
|---|---:|---:|
| Files HTML | 160 → 137 ms | 124 → 162 ms |
| Devices & Files HTML | 142 → 126 ms | 199 → 211 ms |
| Connected folder DAV listing | 222 → 181 ms | 164 → 230 ms |

Seven samples per route per network. The folder was essentially empty. Timings
include connection overhead and vary substantially. There is no consistent latency
improvement demonstrated here, and no basis to attribute these differences to a
static compression change. This patch reduces downloads; the browser's decoded
JavaScript workload remains the same. Page interactivity and large-folder behavior
still need browser profiling. See the [integration and feature plan](umbrel-drive-roadmap.md).

## Checks completed

- Existing-data local upgrade through the runtime bundle/pre-start path.
- Apache configuration, PHP/shell/Python/YAML syntax, manifest and pinned images.
- Identity/gzip/Brotli decoded asset integrity, negotiation and versioned caching.
- Live HTTPS cookie/CSRF sign-in, authenticated Files access and updated setup page
  over LAN and the normal Umbrel hostname, with TLS and hostname checks enabled
  using a process-local certificate pin.
- Folder selection preservation and successful live Depth-1 listing.
- [Full GitHub regression workflow](https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42568034065):
  shared-network name collisions and restart, seven grouped file tests, Files
  filesystem round trips and isolation, folder replacement/disconnect, backup
  safety and corresponding-source packaging.

The unchanged Android and Linux binaries remain version 1.0.0. The workflow
verified their checksums and repackaged corresponding sources. No physical Android
or official-app compatibility test was performed. Opening from the official app
is supported by documented behavior/source review, while native sync and SSO
remain separate integration work. Temporary live credentials were removed from
the development workspace after verification. Local test containers were stopped;
the live app remains running.
