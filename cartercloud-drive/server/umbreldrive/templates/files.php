<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
?>
<!doctype html>
<html lang="en">
<head data-requesttoken="<?php p($_['requesttoken']); ?>">
 <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
 <meta name="theme-color" content="#f6f7fb"><title>Files · Umbrel Drive</title>
 <link rel="icon" href="<?php p($_['logo']); ?>"><link rel="stylesheet" href="<?php p($_['css']); ?>">
 <?php emit_script_tag($_['js']); ?>
</head>
<body data-uid="<?php p($_['uid']); ?>" data-dav-root="<?php p($_['davRoot']); ?>" data-ocs="<?php p($_['ocs']); ?>" data-file-link="<?php p($_['fileLink']); ?>" data-full="<?php p($_['full']); ?>">
 <a class="skip" href="#file-list">Skip to files</a>
 <aside class="sidebar">
  <a class="brand" href="?dir=/"><img src="<?php p($_['logo']); ?>" alt="" width="36" height="36"><span>Umbrel Drive</span></a>
  <p class="eyebrow">Your space</p>
  <nav aria-label="Drive navigation">
   <a class="nav-item active" href="?dir=/" data-dir="/">▧ <span>My files</span></a>
   <?php if ($_['owner'] && $_['bridgeConnected']): ?><a class="nav-item" href="?dir=/Umbrel%20Files" data-dir="/Umbrel Files">▱ <span>Umbrel Files</span></a><?php elseif ($_['owner']): ?><a class="nav-item" href="<?php p($_['setup']); ?>">▱ <span>Connect Umbrel Files</span></a><?php endif; ?>
   <a class="nav-item" href="<?php p($_['full']); ?>/favorites">☆ <span>Favorites</span></a>
   <a class="nav-item" href="<?php p($_['full']); ?>/recent">◷ <span>Recent</span></a>
   <a class="nav-item" href="<?php p($_['full']); ?>/sharingin">♧ <span>Shared with me</span></a>
   <a class="nav-item" href="<?php p($_['full']); ?>/trashbin">♲ <span>Trash</span></a>
  </nav>
  <div class="sidebar-bottom"><a class="nav-item" href="<?php p($_['setup']); ?>">⌘ <span>Devices &amp; Files</span></a><a class="nav-item" id="full-workspace" href="<?php p($_['full']); ?>">↗ <span>Full workspace</span></a><a class="account" href="<?php p($_['security']); ?>"><span class="avatar"><?php p(mb_substr($_['displayName'], 0, 1)); ?></span><span><?php p($_['displayName']); ?><small>Account &amp; security</small></span></a></div>
 </aside>
 <main>
  <header class="topbar"><div><p class="eyebrow">A little space of your own</p><h1 id="folder-title">My files</h1></div><label class="search"><span aria-hidden="true">⌕</span><input id="search" type="search" aria-label="Search this folder" placeholder="Search this folder" autocomplete="off"></label></header>
  <div class="toolbar"><nav id="breadcrumbs" aria-label="Folder path"></nav><div class="tools"><button id="refresh" class="secondary" title="Refresh folder">↻ <span>Refresh</span></button><button id="new-folder" class="secondary">New folder</button><button id="upload" class="primary">↑ Upload files</button><input id="file-input" type="file" multiple hidden></div></div>
  <section class="files-panel" aria-label="Files">
   <div class="list-heading"><p id="count">Your files, right at home.</p><label>Sort by <select id="sort" aria-label="Sort files"><option value="name">Name</option><option value="modified">Last modified</option><option value="size">Size</option></select></label></div>
   <p id="error" class="error" role="alert" hidden></p>
   <div id="file-list" tabindex="-1" aria-busy="true"><table><thead><tr><th scope="col">Name</th><th scope="col" class="date-column">Modified</th><th scope="col" class="size-column">Size</th><th scope="col"><span class="sr-only">Actions</span></th></tr></thead><tbody id="rows"></tbody></table><div id="empty" class="empty" hidden><div aria-hidden="true">▱</div><h2>Room for something new.</h2><p>Drop files here, upload, or create a folder.</p></div><p id="loading" class="loading" role="status">Opening your files…</p></div>
   <div class="list-footer"><p id="status" role="status" aria-live="polite"></p><button id="more" class="secondary" hidden>Show more files</button><details id="speed-info"><summary>Speed info</summary><output id="drive-metrics">Waiting for the folder…</output></details></div>
  </section>
  <p class="workspace-note">File history, recovery, team folders, and resumable large uploads are available in <a href="<?php p($_['full']); ?>">the full workspace</a>. <a href="<?php p($_['setup']); ?>">Devices &amp; Files</a></p>
 </main>
 <dialog id="action-dialog" aria-labelledby="dialog-title"></dialog>
 <noscript><p class="noscript">JavaScript is needed for this file browser. <a href="<?php p($_['full']); ?>">Open the full workspace</a>.</p></noscript>
</body>
</html>
