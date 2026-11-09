<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
// CLI only: configure a local external mount, then index out-of-band Files edits.
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
define('OC_CONSOLE', true);
require_once '/var/www/html/lib/base.php';

use OCA\Files_External\Lib\StorageConfig;
use OCA\Files_External\Service\BackendService;
use OCA\Files_External\Service\GlobalStoragesService;
use OCP\IConfig;
use OCP\IUserManager;
use OCP\Server;

$config = Server::get(IConfig::class);
$storages = Server::get(GlobalStoragesService::class);
$id = (int)$config->getAppValue('umbreldrive', 'files_mount_id', '0');
$mount = null;
if ($id) {
    try { $mount = $storages->getStorage($id); }
    catch (\OCP\Files\NotFoundException) { /* Removed in administration settings. */ }
}
$path = '/umbrel-files';
$available = is_dir($path) && is_readable($path);
$stat = $available ? stat($path) : false;
$identity = $stat ? hash('sha256', $stat['dev'] . ':' . $stat['ino']) : '';
$previous = $config->getAppValue('umbreldrive', 'files_identity', '');
// A replacement folder gets a distinct storage ID: old shares must never expose it.
if ($mount && (!$available || $previous !== $identity)) {
    $storages->removeStorage($id);
    $mount = null;
    $config->deleteAppValue('umbreldrive', 'files_mount_id');
}
if (!$available) {
    $config->setAppValue('umbreldrive', 'files_status', 'disconnected');
    exit(0);
}
if (!Server::get(IUserManager::class)->userExists('umbrel')) {
    $config->setAppValue('umbreldrive', 'files_status', 'owner-missing');
    exit(0);
}
// Local storage accepts a symlink as its root, and blocks symlink traversal within
// it. This private, stable alias gives each selected folder its own cache identity.
$aliases = '/tmp/umbrel-drive-files';
if (!is_dir($aliases) && !mkdir($aliases, 0700)) { throw new \RuntimeException('Cannot prepare Files bridge'); }
$alias = $aliases . '/' . $identity;
if (!is_link($alias) && !symlink($path, $alias)) { throw new \RuntimeException('Cannot prepare Files alias'); }
if (readlink($alias) !== $path) { throw new \RuntimeException('Unexpected Files alias'); }
if (!$mount) {
    // Never obscure a personal folder or an independently configured mount.
    $home = Server::get(\OCP\Files\IRootFolder::class)->getUserFolder('umbrel');
    if ($home->nodeExists('Umbrel Files')) {
        $config->setAppValue('umbreldrive', 'files_status', 'name-conflict');
        exit(0);
    }
    $backend = Server::get(BackendService::class);
    $mount = new StorageConfig();
    $mount->setMountPoint('/Umbrel Files');
    $mount->setBackend($backend->getBackend('local'));
    $mount->setAuthMechanism($backend->getAuthMechanism('null::null'));
    $mount->setBackendOptions(['datadir' => $alias]);
    $mount->setApplicableUsers(['umbrel']);
    $mount->setApplicableGroups([]);
    $mount->setMountOptions(['enable_sharing' => true, 'filesystem_check_changes' => 1]);
    $mount = $storages->addStorage($mount);
    $config->setAppValue('umbreldrive', 'files_mount_id', (string)$mount->getId());
    $config->setAppValue('umbreldrive', 'files_identity', $identity);
    echo "Umbrel Files connected for the umbrel account.\n";
}
$config->setAppValue('umbreldrive', 'files_status', is_writable($path) ? 'connected' : 'read-only');
if (in_array('--scan', $argv, true)) {
    // Use the stock scanner so clients receive the same ETags and DAV metadata
    // as regular Drive uploads. Avoid logging names from the user's library.
    $process = proc_open([PHP_BINARY, '/var/www/html/occ', 'files:scan',
        '--path=/umbrel/files/Umbrel Files', '--quiet'],
        [0 => ['pipe', 'r'], 1 => STDOUT, 2 => STDERR], $pipes);
    if (!is_resource($process)) { throw new \RuntimeException('Cannot start Files indexer'); }
    fclose($pipes[0]);
    exit(proc_close($process));
}
