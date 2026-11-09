<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
$CONFIG = [
 'skeletondirectory' => '/var/www/html/custom_apps/umbreldrive/skeleton',
 'defaultapp' => 'files',
 // Override legacy config.php dbhost before any database-backed command runs.
 'dbhost' => getenv('POSTGRES_HOST') ?: 'cartercloud-drive-db',
 'simpleSignUpLink.shown' => false,
];
