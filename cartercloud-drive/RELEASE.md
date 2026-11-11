# Umbrel Drive 1.2.0-rc.2

This community candidate adds integration controls that belong with your Umbrel:

- **Your Umbrel** shows account storage, Files/Photos connection state and setup
  links. Connected-folder banners explain where files live and how recovery works.
- **Copy to Umbrel Files** creates a copy in the connected writable folder without
  moving the source or replacing an existing destination.
- Android 1.2.0 and Linux 1.1.0 add local/Tailscale connection profiles. Android can
  open the Tailscale app; Linux can read its CLI connection state. Profiles apply
  to new sign-ins; existing sync accounts retain their address and credentials.
- The original umbrel Drive account can register an exact Tailscale IP or `.ts.net`
  address from Your Umbrel. Other accounts cannot see or change it. No wildcard
  trust, Tailscale keys, account auto-migration or VPN policy changes are introduced.
- HTTP is available on port 8391 and requires an explicit native-client setting.
  HTTPS remains the default on 8390, with certificate verification retained. The
  upload-only Linux backup helper supports explicit configure --allow-http. Use
  HTTP only over a trusted connection such as Tailscale. No public access service
  or router forwarding is configured.

The chunked uploader, connected Photos support and mobile navigation from rc.1
remain included. See TESTING.md and the release-readiness report for measured
checks and remaining visual/device gates. This is not an official Umbrel product
or a claim of complete Google/Synology feature parity.
