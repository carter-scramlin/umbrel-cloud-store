# OctoEverywhere Klipper Companion

Install OctoEverywhere from Carter Cloud, open it on port 8391, and keep Umbrel login protection enabled.

1. Enable ZMOD's Moonraker and Fluidd on the AD5X.
2. Find the printer's LAN IPv4 address on its screen; reserve that address in your router if possible.
3. Open the app, enter the address and select **Save and connect**.
4. Refresh the status page until the pairing URL appears in the logs. Follow it and sign into OctoEverywhere.
5. Use the OctoEverywhere dashboard or mobile app to monitor your printer.

The app connects to standard Moonraker port 7125 and Fluidd port 80. It requires the printer to be reachable from Umbrel and Moonraker to accept the companion connection. This initial package does not provide custom ports or Moonraker API key configuration. No inbound port forwarding or printer-side OctoPrint is required. A camera must be configured for camera-dependent features, and dedicated IFS support is not verified.

The upstream official Docker image uses the published latest channel; version 1.0.0 is the community package version, not the upstream plugin version. Configuration and identity persist in the app data directory. Do not share pairing logs publicly. Changing the IP restarts the companion; uninstalling may delete its identity.

[Official Companion guide](https://blog.octoeverywhere.com/klipper-companion-docker-docker-compose-setup-guide/)

## Verification

The wrapper uses the upstream Docker entrypoint and documented Klipper environment variables. The Python wrapper and YAML were checked locally; actual Docker startup, live Umbrel installation, pairing, and printer control still require verification on the target device.
