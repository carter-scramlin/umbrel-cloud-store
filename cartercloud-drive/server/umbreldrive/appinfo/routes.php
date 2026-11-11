<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
return ['routes' => [
 ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
 ['name' => 'page#files', 'url' => '/files', 'verb' => 'GET'],
 ['name' => 'page#connections', 'url' => '/connections', 'verb' => 'GET'],
 ['name' => 'page#saveRemote', 'url' => '/remote', 'verb' => 'POST'],
]];
