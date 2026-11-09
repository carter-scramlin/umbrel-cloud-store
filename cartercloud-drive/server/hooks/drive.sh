#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
cd /var/www/html
cp /usr/src/nextcloud/config/umbreldrive.config.php /var/www/html/config/umbreldrive.config.php
occ() {
  if [ "$(id -u)" = 0 ]; then
    su -p -s /bin/sh www-data -c 'exec php /var/www/html/occ "$@"' -- occ "$@"
  else
    php /var/www/html/occ "$@"
  fi
}
if ! occ status --output=json | grep -q '"installed":true'; then
  exit 0
fi
occ upgrade --no-interaction
occ app:enable umbreldrive
occ app:enable files_external
php /opt/umbreldrive/files-bridge.php
occ app:enable groupfolders
occ app:disable firstrunwizard
occ app:disable nextcloud_announcements
occ app:enable admin_audit
occ theming:config name 'Umbrel Drive'
occ theming:config slogan 'Your files. Right at home.'
occ theming:config url https://github.com/carter-scramlin/umbrel-cloud-store
occ theming:config primary_color '#635bff'
occ theming:config background backgroundColor
occ theming:config background_color '#f5f5fa'
occ theming:config logo /var/www/html/custom_apps/umbreldrive/img/logo.svg
occ config:system:set defaultapp --value=files
occ config:system:set knowledgebaseenabled --type=boolean --value=false
occ background:cron
