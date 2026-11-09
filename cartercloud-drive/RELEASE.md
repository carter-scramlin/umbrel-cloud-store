# Umbrel Drive 1.1.2 — smaller browser downloads

Modern HTTPS browsers can download public static scripts and styles using Brotli.
The largest initial script is 1,056,952 bytes instead of 1,217,320 bytes with gzip
(13.2% smaller). Decoded contents are byte-identical. Older clients retain gzip or
uncompressed responses, and versioned browser caching is unchanged. Dynamic pages,
DAV, user downloads, and access controls retain upstream behavior.

Devices & Files now explains how to open Drive in the official Umbrel Android app:
connect to the Umbrel host without a port, then select Apps → Umbrel Drive. Drive
still requires its own sign-in. Native Umbrel Photos backup is separate from the
Drive Android client's offline files and media uploads. Physical-phone compatibility
remains to be verified; this is not a claim of native Drive sync in the official app.

Accounts, credentials, selected folders, and private Drive files are preserved.
Native Linux and Android binaries remain version 1.0.0. The earlier shared-network
browser-session fix remains covered by CI. The integration/feature roadmap in
`docs/umbrel-drive-roadmap.md` identifies future work; those features are not shipped
by this patch. This remains a community preview, not an official Umbrel product.
