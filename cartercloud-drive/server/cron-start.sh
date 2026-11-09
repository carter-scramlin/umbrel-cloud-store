#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
. /opt/umbreldrive/user.sh
exec su -p -s /bin/sh www-data -c /opt/umbreldrive/worker.sh
