# PancakeSlicer for Umbrel

Install **PancakeSlicer** from Carter Cloud, then open it from Umbrel on port
**8389**. Requires umbrelOS 2.0 or newer. Keep **Require Umbrel login** enabled.
The upstream web UI and slicing engine run together as UID/GID 65532. Projects,
profiles, printer credentials, preferences, and jobs persist in `data/`.
The first-run helper changes ownership of that directory root only.

LAN printer connections are allowed. Enter the printer IP manually if discovery
does not work across Docker's bridge network. No printer is configured by this
package. Two simultaneous slicing jobs and an 8 GiB container memory ceiling
match upstream defaults; the ceiling does not reserve 8 GiB of RAM.

## Updates

The repository's **PancakeSlicer updates** GitHub Actions workflow checks the
latest stable upstream GitHub release hourly, around minute 23 (GitHub may delay
scheduled runs). It can also be run manually from Actions. It skips drafts,
prereleases, existing versions, and older releases. A new version must have a
published official image for both Linux amd64 and arm64. The checker pins the
multi-platform image digest and updates the manifest version and release link
together. It runs startup, engine qualification, asset, and data persistence
checks on an isolated amd64 Docker stack before committing to `main`.
Failed checks leave the published store unchanged and retry on the next run.

After Umbrel refreshes this community store, an installed older version is
eligible for Umbrel's normal **Update** interface. This is not an immediate
push notification or a forced upgrade. Click Update in Umbrel when ready;
back up app data first. The checker does not access your Umbrel device.
GitHub Actions must stay enabled and allow this workflow to write to `main`.
If branch protection is enabled later, adjust the publication step accordingly.

## Verification

Packaging checks include the official Umbrel linter with image verification,
plus updater regression tests. The runtime test checks the qualified engine,
web UI, printer profile assets, saving preferences, and their survival after
container recreation. Both image architectures are checked; runtime testing
uses amd64. Live Umbrel installation, app proxy/HTTPS, update UI, ARM runtime,
printer connections, and physical printing require verification on the device.

The permission helper intentionally uses `restart: no` because it is a one-shot
dependency. The server's `no-new-privileges` and dropped capabilities follow the
upstream Compose package. Neither service uses privileged mode or the Docker
socket. The server publishes no direct host port; Umbrel's app proxy provides
authenticated access.

Upstream: [PancakeSlicer](https://github.com/ZimengXiong/PancakeSlicer),
[official deployment](https://github.com/ZimengXiong/PancakeSlicer/tree/main/deploy).
Unofficial community packaging. Application software retains its upstream license.
