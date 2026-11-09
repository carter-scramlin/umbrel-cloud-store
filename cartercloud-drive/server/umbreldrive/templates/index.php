<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
?>
<div class="drive-setup"><div class="drive-inner">
 <div class="drive-top"><div><p class="drive-eyebrow">At home. Everywhere.</p><h1>Your files.<br>All together.</h1><p class="drive-lead">A little space of your own. Keep your files close, your devices in sync, and your favorite moments safe at home.</p></div><img class="drive-art" src="<?php p($_['logo']); ?>" alt="Umbrel Drive" width="180" height="180"></div>
 <div class="drive-server"><strong>Your server address</strong><code><?php p($_['server']); ?></code></div>
 <?php if ($_['owner']): ?>
 <section class="drive-card drive-files-bridge">
  <p class="drive-eyebrow">Works with Umbrel Files</p><h2>One folder. Every device.</h2>
  <?php if (in_array($_['bridgeStatus'], ['connected', 'read-only'], true)): ?>
   <p>Your folder is connected as <strong>Umbrel Files</strong>. Save here from Drive, Linux, or Android and find the same files in Umbrel Files. Changes made in Files are indexed automatically, typically within a minute. Large libraries can take longer.</p>
   <?php if ($_['bridgeStatus'] === 'read-only'): ?><p>The selected folder is currently read-only. Check its permissions and connection in Umbrel Files to enable uploads.</p><?php endif; ?>
   <a class="drive-button" href="<?php p($_['bridgeFiles']); ?>">Open connected folder →</a>
  <?php elseif ($_['bridgeStatus'] === 'name-conflict'): ?>
   <p>A folder or mount named <strong>Umbrel Files</strong> already exists in your Drive. Rename that existing folder in Drive, then return here after the next indexing cycle. Your files have been left in place.</p>
  <?php elseif ($_['bridgeStatus'] === 'owner-missing'): ?>
   <p>The original umbrel Drive account is missing. Restore that account to connect the folder.</p>
  <?php else: ?>
   <p>Choose a folder using Umbrel’s own folder picker. Its contents will appear here as <strong>Umbrel Files</strong>, ready to sync with Linux and Android. Choose Home, an external drive, or a network share.</p>
   <p>Open <strong>Storage → Umbrel Files</strong> in app settings and select your folder. Umbrel applies the connection automatically.</p>
  <?php endif; ?>
  <a class="drive-button drive-secondary" href="<?php p($_['osSettings']); ?>" target="_blank" rel="noreferrer">Choose folder in Umbrel ↗</a>
  <a class="drive-button drive-secondary" href="<?php p($_['osFiles']); ?>" target="_blank" rel="noreferrer">Open Umbrel Files ↗</a>
  <p class="drive-note">Connected for the umbrel Drive account. Share explicitly to give other accounts access. Changes in either app affect the same files. Drive keeps versions of changes made through Drive; edits and deletions made directly in Files use Files’ own recovery tools. Back up the connected folder separately from Drive’s private app data.</p>
 </section>
 <?php endif; ?>
 <div class="drive-grid">
  <section class="drive-card"><div class="drive-os" aria-hidden="true"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg></div><h2>Made for your Linux desktop.</h2><p>Keep folders in sync in the background. Choose what stays on your computer, share from your file manager, and pick up where you left off.</p><a class="drive-button" href="https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.1" target="_blank" rel="noreferrer">Linux client downloads ↗</a></section>
  <section class="drive-card"><div class="drive-os" aria-hidden="true"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/></svg></div><h2>Right there on Android.</h2><p>Browse on the go, keep files available offline, scan documents, and automatically back up your photos when you connect to Wi-Fi.</p><a class="drive-button" href="https://github.com/carter-scramlin/umbrel-cloud-store/releases/tag/umbrel-drive-v1.1.1" target="_blank" rel="noreferrer">Android client downloads ↗</a></section>
 </div>
 <a class="drive-button drive-secondary" href="<?php p($_['files']); ?>">Open my files →</a>
 <div class="drive-steps"><h2>A home for every device.</h2><ol><li><strong>Install the client</strong>Download the Linux AppImage or Android APK. Release notes identify which builds have been verified.</li><li><strong>Connect your Umbrel</strong>Enter the server address above. Sign in in your browser and approve your device.</li><li><strong>Make yourself at home</strong>Choose your folders on Linux, or turn on automatic uploads in Android settings.</li></ol></div>
 <p class="drive-note">Community software by Carter Cloud, powered by Nextcloud. Not an official Umbrel or Synology product. Use a trusted HTTPS address for device connections. Manage connected devices in <a href="<?php p($_['security']); ?>">Security settings</a>. Native builds and source are published in the linked release; upstream Nextcloud clients can also connect to this server.</p>
</div></div>
