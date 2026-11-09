#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
cd /var/www/html
tick=0
while :; do
  # One worker, no overlapping scans. A large library can take longer than a minute.
  php /opt/umbreldrive/files-bridge.php --scan || echo 'Umbrel Files indexing failed; retrying next cycle.' >&2
  if [ "$tick" = 0 ]; then
    php -f cron.php || echo 'Drive background jobs failed; retrying next cycle.' >&2
  fi
  tick=$(( (tick + 1) % 5 ))
  sleep 60
done
