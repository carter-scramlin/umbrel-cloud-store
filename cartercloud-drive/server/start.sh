#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
. /opt/umbreldrive/user.sh
# Migrate only this app's private Nextcloud tree. Never chown the selected Files folder.
if [ ! -f /var/www/html/.umbrel-uid-1000 ]; then
  find /var/www/html -xdev -uid 33 -exec chown -h 1000:1000 {} +
  touch /var/www/html/.umbrel-uid-1000
  chown 1000:1000 /var/www/html/.umbrel-uid-1000
fi
# A nested app mount makes Docker create custom_apps as root before first-run
# copying. Keep the parent writable for optional app installation.
mkdir -p /var/www/html/custom_apps
chown 1000:1000 /var/www/html/custom_apps
if [ ! -f /var/www/html/custom_apps/groupfolders/appinfo/info.xml ]; then
  archive=$(mktemp)
  trap 'rm -f "$archive"' EXIT HUP INT TERM
  curl --fail --location --retry 3 --proto '=https' --tlsv1.2 \
    https://github.com/nextcloud-releases/groupfolders/releases/download/v23.0.1/groupfolders-v23.0.1.tar.gz \
    --output "$archive"
  echo "3949e6a45947188090c170c6983aae11a1d66134ec317ffe7b7609062f3aecf3  $archive" | sha256sum -c -
  stage=$(mktemp -d /var/www/html/custom_apps/.groupfolders-install-XXXXXX)
  tar -xzf "$archive" --no-same-owner -C "$stage"
  chown -R 1000:1000 "$stage/groupfolders"
  mv "$stage/groupfolders" /var/www/html/custom_apps/groupfolders
  rmdir "$stage"
  rm -f "$archive"
  trap - EXIT HUP INT TERM
fi
exec /entrypoint.sh "$@"
