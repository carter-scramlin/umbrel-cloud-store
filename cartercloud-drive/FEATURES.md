# Feature coverage

This is a Nextcloud-based community alternative, not a Synology-protocol clone.
"Included" means supplied by the pinned upstream software; it does not mean
that every device and operating-system combination has been tested here.

| Synology Drive capability | Umbrel Drive implementation | Status |
|---|---|---|
| Web file browser, folders, sorting, grid/list | Lightweight list browser by default; full Nextcloud workspace retains grid/list and advanced tools | Included; lightweight uploads ≤16 GiB, larger/resumable transfers in full workspace or clients |
| Official mobile photo originals | Optional separate read-only folder slot, normally Home/Photos | Owner-only until explicitly shared; photo backup/deletion stay in Umbrel Photos |
| Official Umbrel Android app | Open from Apps using its existing WebView; native Files reaches the selected folder | Official Play app paired in Android 13 VM; launch/login verification recorded in release readiness; physical-phone QA pending; separate Drive login |
| Umbrel connection center | Account storage, Files/Photos status and direct native settings links | New in 1.2.0-rc.2; no OS admin token requested |
| Copy to Umbrel Files | Context action copies into the selected writable folder | Keeps source and refuses overwrite conflicts |
| Tailscale connection profiles | Built-in Android/Linux settings and exact host registration on the server | Uses installed Tailscale; new sign-ins only; no automatic account rerouting |
| HTTP connections | Plain HTTP server port 8391; explicit client setting | HTTPS default remains 8390; HTTP needs a trusted transport |
| Native Umbrel Files integration | Folder picker, same files, UID 1000, owner-only local storage mount, automatic indexing | Round-trip and isolation integration tested |
| Name search, favorites, tags, recent files | Files and unified search | Included |
| File previews, photos, PDF viewing | Viewer, Photos, PDF viewer | Included; codec/format limits apply |
| Upload, download, move, copy, rename | WebDAV and Files | API integration tested |
| Large-file transfer | Native clients use Nextcloud chunked upload; PHP limit 16 GiB per request | Proxy limits also apply |
| Revisions and restore | Files Versions | Included; version retention differs from Synology |
| Trash and recovery | Files Trashbin | Included; retention differs from Synology |
| Password/expiry sharing, revocation | OCS sharing | API integration tested |
| File requests / upload-only links | Public folder share with upload-only permissions | API integration tested |
| Users, groups, quotas | Nextcloud administration | Included |
| Group sharing / personal shared folders | Share a folder with a group | Included |
| Centrally owned team folders / ACLs | Nextcloud Team folders (groupfolders) app | Included; Team folders 23.0.1 |
| File locking | Server transactional locks via Redis and bundled Files Lock | Included; advisory locks/client behavior differ |
| Two-way desktop sync, selective sync, conflicts | Native Linux Nextcloud sync engine | Branded client build |
| File manager sharing and status overlays | Upstream Nautilus/Nemo/Caja integration | Requires separately installed integration; not bundled in AppImage |
| Desktop on-demand files | Upstream OpenVFS/suffix plugins | Experimental on Linux; validate filesystem/kernel compatibility |
| Scheduled computer backup | Included Python upload-only snapshot helper + systemd timer | Separate helper; full snapshots, no automatic retention |
| Android browsing, upload, download, sharing | Native Nextcloud Android engine | Branded client build |
| Android offline files | Upstream keep-available-offline feature | Included; verify physical-device behavior |
| Camera/media auto upload | Upstream Android background jobs, Wi-Fi/charging settings | Included; Android battery rules apply |
| Android document scan and image editing | Upstream native tools | Included; verify physical-device behavior |
| Android arbitrary bidirectional folder sync | No general Synology-equivalent folder-pair engine | Not included |
| Android instant push notifications | Upstream package push credentials cannot be reused | Not configured |
| Activity log, devices, app passwords, TOTP | Activity, Security, administration, audit log | Included |
| Full-text content search / OCR | Nextcloud full-text-search apps + indexing services | Additional setup required |
| Collaborative plain-text editing | Nextcloud Text | Included |
| Office documents, spreadsheets, presentations | Nextcloud Office + a compatible Collabora/ONLYOFFICE service | Additional service required |
| Synology Office document formats | No Synology Office conversion engine | Not included |
| Synology ShareSync / DSM integration | WebDAV interoperability and Nextcloud federation are alternatives | No protocol compatibility |
| Watermarks, DRM-style download controls, DLP | No Synology-equivalent policy engine bundled | Not included |
| End-to-end encryption | Not enabled by default; server disks must be protected separately | Not claimed |
| Server backup and disaster recovery | Consistent PostgreSQL dump + whole Nextcloud data/config tree | Operator backup required |

References: [Synology Drive specifications](https://www.synology.com/en-us/dsm/7.4/software_spec/synology_drive),
[Nextcloud WebDAV APIs](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/index.html),
[Nextcloud desktop source](https://github.com/nextcloud/desktop),
[Nextcloud Android source](https://github.com/nextcloud/android).

[Android integration, performance and feature roadmap](../docs/umbrel-drive-roadmap.md) identifies priorities, acceptance gates, and additional Google Drive comparisons.
