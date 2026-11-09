# Privacy

Umbrel Drive stores your files, metadata, accounts, and logs on your Umbrel.
Carter Cloud does not operate an account service or collect analytics for this
package. Authentication and device app passwords are handled by your server.

This distribution is based on Nextcloud. Its software update checks and app
catalog contact Nextcloud infrastructure. Apps you enable can contact external
services; review their privacy policies. Public sharing sends files to people
with whom you share a link. Federated sharing connects to the server you choose.
Android document scanning, location features, and optional integrations follow
upstream Nextcloud behavior and the permissions you grant.

Android push credentials registered for the upstream package do not apply to
this independently signed package. Background uploads and manual refresh work
without the upstream push service; instant push notifications are not promised.

The Linux backup helper connects only to the server URL you configure, validates
TLS certificates, and refuses redirects. It stores a device app password in a
local file readable only by your account. You can revoke it in Security settings.
