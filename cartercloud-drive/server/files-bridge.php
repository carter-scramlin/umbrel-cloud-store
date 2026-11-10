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

function configureBridge(string $prefix, string $label, string $path, bool $readOnly): ?string {
    $config = Server::get(IConfig::class);
    $storages = Server::get(GlobalStoragesService::class);
    $id = (int)$config->getAppValue('umbreldrive', $prefix . '_mount_id', '0');
    $mount = null;
    if ($id) {
        try { $mount = $storages->getStorage($id); }
        catch (\OCP\Files\NotFoundException) { /* Removed in administration settings. */ }
    }
    $available = is_dir($path) && is_readable($path);
    $stat = $available ? stat($path) : false;
    $identity = $stat ? hash('sha256', $stat['dev'] . ':' . $stat['ino']) : '';
    $previous = $config->getAppValue('umbreldrive', $prefix . '_identity', '');
    // A replacement folder gets a distinct storage ID: old shares must never expose it.
    if ($mount && (!$available || $previous !== $identity)) {
        $storages->removeStorage($id);
        $mount = null;
        $config->deleteAppValue('umbreldrive', $prefix . '_mount_id');
    }
    if (!$available) {
        $config->setAppValue('umbreldrive', $prefix . '_status', 'disconnected');
        return null;
    }
    if (!Server::get(IUserManager::class)->userExists('umbrel')) {
        $config->setAppValue('umbreldrive', $prefix . '_status', 'owner-missing');
        return null;
    }
    // Local storage accepts a symlink as its root, and blocks symlink traversal within
    // it. This private, stable alias gives each selected folder its own cache identity.
    $aliases = '/tmp/umbrel-drive-' . $prefix;
    if (!is_dir($aliases) && !mkdir($aliases, 0700)) { throw new \RuntimeException('Cannot prepare Files bridge'); }
    $alias = $aliases . '/' . $identity;
    if (!is_link($alias) && !symlink($path, $alias)) { throw new \RuntimeException('Cannot prepare Files alias'); }
    if (readlink($alias) !== $path) { throw new \RuntimeException('Unexpected Files alias'); }
    if (!$mount) {
        // Never obscure a personal folder or an independently configured mount.
        $home = Server::get(\OCP\Files\IRootFolder::class)->getUserFolder('umbrel');
        if ($home->nodeExists($label)) {
            $config->setAppValue('umbreldrive', $prefix . '_status', 'name-conflict');
            return null;
        }
        $backend = Server::get(BackendService::class);
        $mount = new StorageConfig();
        $mount->setMountPoint('/' . $label);
        $mount->setBackend($backend->getBackend('local'));
        $mount->setAuthMechanism($backend->getAuthMechanism('null::null'));
        $mount->setBackendOptions(['datadir' => $alias]);
        $mount->setApplicableUsers(['umbrel']);
        $mount->setApplicableGroups([]);
        $mount->setMountOptions(['enable_sharing' => true, 'filesystem_check_changes' => 1, 'readonly' => $readOnly]);
        $mount = $storages->addStorage($mount);
        $config->setAppValue('umbreldrive', $prefix . '_mount_id', (string)$mount->getId());
        $config->setAppValue('umbreldrive', $prefix . '_identity', $identity);
        echo $label . " connected for the umbrel account.\n";
    }
    $config->setAppValue('umbreldrive', $prefix . '_status', !$readOnly && is_writable($path) ? 'connected' : 'read-only');
    return '/umbrel/files/' . $label;
}

$failed = false;
foreach ([['files', 'Umbrel Files', '/umbrel-files', false], ['photos', 'Umbrel Photos', '/umbrel-photos', true]] as $bridge) {
 try {
  $scanPath = configureBridge(...$bridge);
  if (!$scanPath || !in_array('--scan', $argv, true)) { continue; }
  $process = proc_open([PHP_BINARY, '/var/www/html/occ', 'files:scan', '--path=' . $scanPath, '--quiet'],
      [0 => ['pipe', 'r'], 1 => STDOUT, 2 => STDERR], $pipes);
  if (!is_resource($process)) { throw new \RuntimeException('Cannot start indexer'); }
  fclose($pipes[0]);
  if (proc_close($process) !== 0) { $failed = true; }
 } catch (\Throwable $error) {
  // No user paths or names in background logs. Other bridges can still progress.
  fwrite(STDERR, 'Drive folder connection failed: ' . $bridge[0] . "\n");
  $failed = true;
 }
}
exit($failed ? 1 : 0);
