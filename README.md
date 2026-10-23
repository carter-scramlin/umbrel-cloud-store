# Carter Cloud — Umbrel Community App Store

A community app store containing **Pydio Cells**, **OpenCloud**, and **Filestash** for umbrelOS.
No Portainer or separate database installation is required.

## Install in Umbrel

1. Open **App Store → menu → Community App Stores** (wording may vary).
2. Add `https://github.com/carter-scramlin/umbrel-cloud-store`.
3. Open **Carter Cloud** and install an app.

This repository contains the app store definitions at its root. No separate
Portainer installation is required.

## Pydio Cells

Open the app from Umbrel (`http://umbrel.local:8384` by default). Wait a few
minutes for its database to initialize. Complete the Cells setup wizard:

| Setting | Value |
|---|---|
| Database host | `database` |
| Database port | `3306` |
| Database name | `cells` |
| Database user | `pydio` |
| Database password | The app password shown in Umbrel |

Create your own Cells administrator account in the wizard. The displayed app
password is the **database password**, not a pre-created Cells login.
Persistent configuration, files, and database reside under the app's `data/`.
Cells runs HTTP behind Umbrel's app proxy on the LAN. For access over the
internet, use a HTTPS reverse proxy and update `CELLS_SITE_EXTERNAL` to your
HTTPS URL. Umbrel login protection is disabled for this app to allow native
app authentication and sharing; Cells supplies its own authentication.

This package does not expose the additional gRPC port needed for some desktop
Cells Sync configurations. Configure that separately following the Pydio guide.

## OpenCloud

Opening the app from Umbrel (`http://umbrel.local:8385`) redirects you to
**https://umbrel.local:9443** by default. Accept the self-signed certificate for
your own server, then sign in with `admin` and the app password shown in Umbrel.
Initialization runs once and creates persistent secrets; restarting preserves
existing configuration. Change the admin password after signing in.

Use this exact configured HTTPS hostname, including port, for login. Using the
IP address instead can cause authentication redirects to fail. If your device
cannot resolve `umbrel.local`, choose a hostname that resolves on every client
and on Umbrel. Replace the hostname in **both** `OC_URL` and
`OPENCLOUD_PUBLIC_URL` in OpenCloud's `docker-compose.yml`, commit to GitHub,
and install. These default to Umbrel's `DEVICE_DOMAIN_NAME`, or `umbrel.local`.
Reserve the server's LAN address if you use an IP as the canonical address.

OpenCloud needs HTTPS for browser login. Its HTTPS listener bypasses the
Umbrel login proxy and uses OpenCloud authentication. `OC_INSECURE=true` allows
its internal requests to work with the local self-signed certificate.
For a public domain, set both URL values to `https://cloud.example.com`, place
a trusted HTTPS reverse proxy in front of the server, and configure upstream
TLS accordingly. If terminating TLS and forwarding HTTP, change `PROXY_TLS`
to `false` and the upstream target to HTTP on the exposed port. Do not expose
that HTTP backend directly to the internet.

Files and configuration persist under `data/storage` and `data/config`.
The permissions helper owns only those two directory roots as UID/GID 1000.
Office editing, Collabora, SMTP, and external storage integrations are not
bundled. Both apps can be installed together.

## Filestash

Install **Filestash** from Carter Cloud and open it from Umbrel
(`http://umbrel.local:8386`, or the HTTPS address offered by Umbrel).
Requires umbrelOS 2.0 or newer. Collabora Online is included in the package;
there is no separate Office app, database, or Portainer dependency.

1. Create your Filestash administrator password in the browser.
2. In the admin console, enable **Local** storage. Set its path to `/files/`
   to restrict the connection to the files folder. Use your administrator
   password when connecting, or configure Filestash's own user authentication.
3. Click the Filestash logo to return to the login page and connect.
4. To manage existing files, use **Umbrel → Filestash → App Settings → Files**
   to select a Home folder, external drive, or network share. The selected
   folder replaces the default `/files` mount; existing files are not copied.
5. Enable other storage backends and enter their connection credentials in
   Filestash. OAuth providers also require the provider's application setup.

The default `/files` folder is stored in `data/files`. Configuration, database,
credentials, share links, and installed plugins persist in `data/state`.
Umbrel's **Move app data** setting can relocate these app-owned directories.
A separately selected Files folder stays in its original location and needs
its own backup. Selected folders must allow UID/GID `1000:1000` the intended
read/write access; this package does not recursively change their ownership.

The official image includes its standard storage backends, text/image/PDF
viewers, search, file transfer/management, sharing, and Office integration.
Collabora edits supported documents, spreadsheets, and presentations through
the same origin as Filestash, including WebSockets and authenticated WOPI
callbacks. Office HTTP port 9980 is internal and is not published to the LAN.
Large transfers are streamed without a gateway upload-size limit; any outer
proxy or storage provider may apply its own limits. CODE is the community
Office edition intended for home use and small teams.

Umbrel login protection stays enabled by default. Sharing works for users
who can log in to Umbrel. To allow recipients or WebDAV clients without an
Umbrel login, first configure Filestash authentication and share restrictions,
then turn off **Require Umbrel login** in that app's Umbrel settings. This
removes Umbrel protection for the whole app; Filestash supplies authentication.
Public access needs your own reachable URL and trusted HTTPS. Set Filestash's
public host in its admin settings if you need a fixed canonical URL; leave it
unset for access using multiple LAN hostnames/IPs. External connectors require
your accounts and provider permissions. Optional paid plugins are not licensed
by this community package.

Filestash reports version `v0.6.20261022` in the pinned image. Its current
upstream release channel publishes `latest` without matching stable version
tags, so this package pins its immutable multi-platform digest. Office uses
the version from Filestash's official Compose example, also pinned by digest.
Collabora's `MKNOD` capability is used for its document-process sandbox, as in
upstream container deployments. No privileged mode or Docker socket is used.
All runtime gateway configuration is in Compose so Umbrel updates carry it.

### Filestash verification

On 2026-10-22, the official Umbrel linter passed with image checks and zero
errors. Both Linux amd64 and arm64 image manifests were verified. Intentional
warnings: the pinned Filestash `latest` tag and Collabora's `MKNOD` capability.
Runtime testing used an isolated Docker amd64 stack with Umbrel-style container
names and the packaged gateway. It verified first-run admin creation/login,
local storage login, folder creation, upload/download, rename/list, deletion, search, share-link
creation and anonymous download, Office discovery, and browser Office editing
with saved changes confirmed in persistent storage. HTTP/HTTPS forwarding
emits the matching ws/wss URL. Credentials, files, shares, and saved Office edits
survived recreation of all containers. See `cartercloud-filestash/TESTING.md` for details.

The package has not yet been installed through a live Umbrel lifecycle.
Umbrel login/HTTPS termination, folder selection, and moving app data still
need verification on the target device. ARM runtime, remote services requiring
user credentials, and optional commercial plugins were not exercised.

## Ports

| App | Umbrel launcher | Other host port |
|---|---:|---:|
| Pydio Cells | 8384 | None |
| OpenCloud | 8385 | 9443 (HTTPS) |
| Filestash | 8386 | None |

Check these are unused on your server before installing.

## Pydio Cells and OpenCloud verification and limitations

Docker images are pinned by multi-platform manifest digest and their registry
manifests were checked for Linux amd64 and arm64 support. YAML and app IDs were
validated locally. **The stack has not been run on a live Umbrel or Docker
engine in the build environment.** Treat this as an initial community package
until you verify login, upload, download, restart persistence, and sharing on
your Umbrel. No live-server compatibility claim is made.

For upgrades, back up the app data first and update tags and digests deliberately.
Do not use the Cells in-app binary updater inside an immutable container.
Stop both app services before a filesystem backup; include the database and
all configuration/secrets. Umbrel uninstall may delete app data.

## Troubleshooting

- Empty Cells screen: wait for MariaDB health, then check the server/database logs.
- Cells database connection: use `database`, not localhost or your Umbrel IP.
- OpenCloud login loop: check that the browser URL matches `OC_URL` exactly.
- OpenCloud TLS error: accept the certificate by opening its HTTPS URL directly.
- OpenCloud permissions: inspect the `permissions` service's exit status.
- Port already allocated: choose unused ports and update the manifests and URLs.

## Upstream references

- https://github.com/getumbrel/umbrel-community-app-store
- https://docs.pydio.com/latest/admin-guide/quick-start/cells-installation/docker/
- https://docs.opencloud.eu/docs/admin/getting-started/container/docker/
- https://github.com/opencloud-eu/opencloud-compose
- https://www.filestash.app/docs/install-and-upgrade/
- https://downloads.filestash.app/latest/docker-compose.yml
- https://github.com/mickael-kerjean/filestash

Unofficial community packaging; no affiliation with Umbrel, Pydio, OpenCloud, Filestash, or Collabora.
Application software retains its upstream licenses. Packaging is MIT licensed.
