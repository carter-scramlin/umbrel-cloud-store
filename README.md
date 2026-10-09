# Carter Cloud — Umbrel Community App Store

A community app store containing **Pydio Cells** and **OpenCloud** for umbrelOS.
No Portainer or separate database installation is required.

## Install in Umbrel

1. Open **App Store → menu → Community App Stores** (wording may vary).
2. Add `https://github.com/carter-scramlin/umbrel-cloud-store`.
3. Open **Carter Cloud** and install either app.

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

## Ports

| App | Umbrel launcher | Other host port |
|---|---:|---:|
| Pydio Cells | 8384 | None |
| OpenCloud | 8385 | 9443 (HTTPS) |

Check these are unused on your server before installing.

## Verification and limitations

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

Unofficial community packaging; no affiliation with Umbrel, Pydio, or OpenCloud.
Application software retains its upstream licenses. Packaging is MIT licensed.
