#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Umbrel Files uses 1000:1000. Change the container account, not the selected files.
set -eu
sed -i 's/^www-data:x:33:33:/www-data:x:1000:1000:/' /etc/passwd
sed -i 's/^www-data:x:33:/www-data:x:1000:/' /etc/group
[ "$(id -u www-data)" = 1000 ] && [ "$(id -g www-data)" = 1000 ]
