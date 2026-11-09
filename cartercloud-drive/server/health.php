<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
// A working status endpoint alone does not prove browser sessions work.
declare(strict_types=1);
$context = stream_context_create(['http' => [
    'timeout' => 10,
    'header' => 'Host: ' . (getenv('DRIVE_HEALTH_HOST') ?: 'localhost'),
]]);
$status = @file_get_contents('http://127.0.0.1/status.php', false, $context);
$login = @file_get_contents('http://127.0.0.1/login', false, $context);
exit($status && (json_decode($status, true)['installed'] ?? false)
    && is_string($login) && str_contains($login, 'data-requesttoken=') ? 0 : 1);
