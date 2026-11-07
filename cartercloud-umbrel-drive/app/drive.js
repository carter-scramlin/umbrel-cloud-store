"use strict";

const $ = id => document.getElementById(id);
const OFFLINE = "umbrel-drive-pinned-v1";
const pages = {
  files: ["My Drive", "Browse, search, and upload files."],
  offline: ["Offline", "Files saved on this device. Remove a copy here to free up browser storage."],
  trash: ["Trash", "Open a file’s history to restore an earlier version."],
  shares: ["Shared links", "Anyone with a link can download its original revision until it expires or you revoke it."],
  devices: ["Devices", "Create or revoke keys for your Linux sync jobs. Each key can read and write your whole drive."],
};
let view = "files";
let folder = "";
let entries = [];
let virtualFolders = new Set();
let online = false;
let installPrompt;
let rendering = 0;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function button(text, action, className) {
  const element = node("button", text, className);
  element.type = "button";
  element.onclick = () => run(action, element);
  return element;
}

function link(text, href, name) {
  const element = node("a", text, "button");
  element.href = href;
  element.download = name || "";
  return element;
}

function notice(message) {
  $("status").textContent = message;
}

async function run(action, element) {
  if (element) element.disabled = true;
  notice("");
  try {
    await action();
  } catch (error) {
    notice(error.message);
    if ($("dialog").open) {
      $("dialog-body").querySelector('[role="alert"]')?.remove();
      const alert = node("p", error.message);
      alert.setAttribute("role", "alert");
      $("dialog-body").append(alert);
    }
  } finally {
    if (element) element.disabled = false;
  }
}

async function api(endpoint, options = {}) {
  const headers = {"X-Drive-Request": "1", ...options.headers};
  const response = await fetch("/api/" + endpoint, {...options, headers, cache: "no-store"});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const error = new Error(body.error || `Drive request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return response;
}

const data = async (endpoint, options) => (await api(endpoint, options)).json();
const send = (method, body) => ({method, body: JSON.stringify(body)});
const fileURL = (path, revision) => "file?" + new URLSearchParams(revision ? {path, rev: revision} : {path});
const shortName = path => path.split("/").at(-1);
const date = epoch => new Date(epoch * 1000).toLocaleString();
const size = bytes => bytes < 1024 ? `${bytes} B` :
  bytes < 1024**2 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024**2).toFixed(1)} MB`;

function row(title, detail, actions) {
  const element = node("div", "", "row");
  const info = node("div", "", "info");
  info.append(node("strong", title), node("small", detail));
  const controls = node("div", "", "actions");
  controls.append(...actions);
  element.append(info, controls);
  return element;
}

function dialog(title, ...body) {
  $("dialog-title").textContent = title;
  $("dialog-body").replaceChildren(...body);
  if (!$("dialog").open) $("dialog").showModal();
}

function ask(title, label, value, action, submit = "Save", type = "text") {
  const form = node("form");
  const field = node("input");
  field.type = type;
  field.value = value;
  field.required = true;
  const caption = node("label", label);
  caption.append(field);
  const confirm = node("button", submit, "primary");
  form.append(caption, node("p"), confirm);
  form.onsubmit = event => {
    event.preventDefault();
    run(() => action(field.value), confirm);
  };
  dialog(title, form);
  field.focus();
}

function showSecret(title, text, value) {
  const field = node("input");
  field.value = value;
  field.readOnly = true;
  field.setAttribute("aria-label", title);
  dialog(title, node("p", text), field, node("p"), button("Copy", async () => {
    await navigator.clipboard.writeText(value);
    notice("Copied to clipboard.");
  }));
  field.select();
}

function enter(path) {
  folder = path;
  $("search").value = "";
  return render();
}

function fileActions(file) {
  return [
    link("Download", "/api/" + fileURL(file.path, file.id), shortName(file.path)),
    button("More", () => fileMenu(file)),
  ];
}

function fileMenu(file) {
  dialog(shortName(file.path), node("p", file.path), node("div", "", "actions"));
  $("dialog-body").lastChild.append(
    button("Save offline", async () => {
      if (!("caches" in window)) throw new Error("Offline storage requires trusted HTTPS.");
      if (file.size > 100 * 1024**2) throw new Error("Offline copies are limited to 100 MB per file.");
      const response = await api(fileURL(file.path, file.id));
      const cache = await caches.open(OFFLINE);
      await cache.put(offlineURL(file.path), response);
      $("dialog").close();
      notice("Saved on this device for offline access.");
    }),
    button("Rename or move", () => ask("Rename or move file", "Path relative to My Drive", file.path, async destination => {
      const target = entries.find(item => item.path === destination);
      await data("move?" + new URLSearchParams({path: file.path}), {
        ...send("POST", {destination, destinationRevision: target?.id || 0}),
        headers: {"X-Drive-Revision": file.id},
      });
      $("dialog").close();
      await refresh();
      notice("File moved. Earlier versions stay at the old path in Trash.");
    }, "Move file")),
    button("Version history", () => history(file)),
    button("Share link", () => ask("Create a download link", "Expires in hours (1–168)", "24", async hours => {
      const result = await data("shares", send("POST", {path: file.path, hours: Number(hours)}));
      showSecret("Share link", "Anyone with this link can download this revision.", new URL(result.url, location.href).href);
    }, "Create link", "number")),
    button("Move to Trash", async () => {
      if (!confirm(`Move ${shortName(file.path)} to Trash?`)) return;
      await api(fileURL(file.path), {method: "DELETE", headers: {"X-Drive-Revision": file.id}});
      $("dialog").close();
      await refresh();
      notice("Moved to Trash.");
    }),
  );
}

async function history(file) {
  const versions = await data("history?" + new URLSearchParams({path: file.path}));
  dialog("Version history", node("p", file.path), ...versions.map(version => {
    const actions = version.hash ? [
      link("Download", "/api/" + fileURL(file.path, version.id), shortName(file.path)),
      button("Restore", async () => {
        if (!confirm("Restore this file version? Current versions remain in history.")) return;
        await data("restore?" + new URLSearchParams({path: file.path}), {
          ...send("POST", {rev: version.id}), headers: {"X-Drive-Revision": file.id},
        });
        $("dialog").close();
        await refresh();
        notice("Version restored.");
      }),
    ] : [];
    return row(version.hash ? size(version.size) : "Moved to Trash", date(version.time), actions);
  }));
}

function offlineURL(path) {
  return "/offline-copy?" + new URLSearchParams({path});
}

async function offlineRows() {
  if (!("caches" in window)) return [];
  const cache = await caches.open(OFFLINE);
  return (await cache.keys()).map(request => {
    const path = new URL(request.url).searchParams.get("path");
    return row(shortName(path), path, [
      button("Download", async () => {
        const saved = await cache.match(request);
        if (!saved) throw new Error("This offline copy is no longer available.");
        const url = URL.createObjectURL(await saved.blob());
        link("", url, shortName(path)).click();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      }),
      button("Remove copy", async () => {
        await cache.delete(request);
        await render();
      }),
    ]);
  });
}

function fileRows() {
  const search = $("search").value.trim().toLocaleLowerCase();
  const prefix = folder ? folder + "/" : "";
  const active = entries.filter(file => file.hash);
  if (search) return active.filter(file => file.path.toLocaleLowerCase().includes(search))
    .map(file => row(shortName(file.path), file.path, fileActions(file)));

  const dirs = new Set();
  for (const path of [...active.map(file => file.path), ...virtualFolders]) {
    if (!path.startsWith(prefix)) continue;
    const suffix = path.slice(prefix.length);
    if (suffix.includes("/") || virtualFolders.has(path)) dirs.add(suffix.split("/")[0]);
  }
  return [...[...dirs].filter(Boolean).sort().map(name =>
    row("▰  " + name, "Folder", [button("Open", () => enter(prefix + name))])),
    ...active.filter(file => file.path.startsWith(prefix) && !file.path.slice(prefix.length).includes("/"))
      .map(file => row(shortName(file.path), `${size(file.size)} · ${date(file.time)}`, fileActions(file)))];
}

async function render() {
  const ticket = ++rendering;
  $("title").textContent = pages[view][0];
  $("description").textContent = pages[view][1];
  $("toolbar").hidden = view !== "files";
  $("browser-tools").hidden = view !== "files";
  document.querySelectorAll("nav button").forEach(item => {
    item.toggleAttribute("disabled", !online && item.dataset.view !== "offline");
    if (item.dataset.view === view) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  $("items").replaceChildren();
  let rows = [];
  if (view === "files") {
    const crumbs = [button("My Drive", () => enter(""))];
    if (folder) folder.split("/").forEach((part, index, all) => {
      crumbs.push(node("span", "›"), button(part, () => enter(all.slice(0, index + 1).join("/"))));
    });
    $("breadcrumbs").replaceChildren(...crumbs);
    rows = fileRows();
  }
  if (view === "trash") rows = entries.filter(file => !file.hash)
    .map(file => row(shortName(file.path), file.path, [button("Version history", () => history(file))]));
  if (view === "offline") rows = await offlineRows();
  if (view === "devices" || view === "shares") {
    const endpoint = view;
    const list = await data(endpoint);
    rows = list.map(item => row(item.name || item.label, "Expires " + date(item.expires), [button("Revoke", async () => {
      if (!confirm("Revoke access now?")) return;
      await data(endpoint, send("DELETE", {id: item.id}));
      await render();
    })]));
    if (endpoint === "devices") rows.unshift(row("Linux sync", "Set up a background sync job or run one manually.", [
      link("Download client", "/api/linux", "umbrel-drive-sync.py"),
      button("Create device key", () => ask("New device key", "Device name", "", async name => {
        const result = await data("devices", send("POST", {name}));
        showSecret("Device key", "Copy this key now. It will only be shown once.", result.token);
        await render();
      }, "Create key")),
    ]));
  }
  if (ticket === rendering) $("items").replaceChildren(...(rows.length ? rows : [node("p", "Nothing here yet.", "empty")]));
}

function showWorkspace() {
  $("workspace").hidden = false;
  $("welcome").hidden = true;
  $("signout").hidden = false;
}

async function refresh() {
  try {
    entries = await data("files");
  } catch (error) {
    online = false;
    entries = [];
    if (error.status === 401) {
      $("workspace").hidden = true;
      $("signout").hidden = true;
      $("welcome").hidden = false;
    } else {
      showWorkspace();
      view = "offline";
      await render();
      notice("Server unavailable. Showing files saved on this device.");
    }
    return;
  }
  online = true;
  showWorkspace();
  await render();
}

$("login").onsubmit = event => {
  event.preventDefault();
  run(async () => {
    if (!window.isSecureContext) throw new Error("Open Umbrel Drive over trusted HTTPS to sign in.");
    await data("login", send("POST", {password: $("password").value}));
    $("password").value = "";
    view = "files";
    await refresh();
  }, event.submitter);
};

$("signout").onclick = () => run(async () => {
  if ("caches" in window) await caches.delete(OFFLINE);
  await data("logout", send("POST", {}));
  entries = [];
  virtualFolders.clear();
  folder = "";
  $("search").value = "";
  view = "files";
  await refresh();
}, $("signout"));

document.querySelectorAll("nav button").forEach(item => {
  item.onclick = () => run(async () => {
    view = item.dataset.view;
    await refresh();
  }, item);
});

$("search").oninput = () => run(render);
$("folder").onclick = () => ask("New folder", "Folder name", "", async name => {
  if (name === "." || name === ".." || /[\\/:*?"<>|\x00-\x1f]/.test(name)) throw new Error("Choose a valid folder name.");
  const target = folder ? folder + "/" + name : name;
  if (entries.some(file => file.hash && file.path === target)) throw new Error("A file already uses this name.");
  virtualFolders.add(target);
  $("dialog").close();
  await enter(target);
  notice("Upload a file to keep this folder.");
}, "Open folder");
$("upload").onclick = () => $("picker").click();
$("picker").onchange = () => run(async () => {
  const files = [...$("picker").files];
  const destination = folder;
  $("picker").value = "";
  let count = 0;
  try {
    for (const file of files) {
      const path = destination ? destination + "/" + file.name : file.name;
      const current = entries.find(item => item.path === path);
      if (current?.hash && !confirm(`Upload a new version of ${file.name}?`)) continue;
      notice(`Uploading ${file.name}…`);
      const result = await data(fileURL(path), {method: "PUT", body: file,
        headers: {"X-Drive-Revision": current?.id || 0}});
      entries = entries.filter(item => item.path !== path).concat(result);
      count++;
    }
  } finally {
    await refresh();
  }
  notice(`Uploaded ${count} file${count === 1 ? "" : "s"}.`);
}, $("upload"));

window.addEventListener("beforeinstallprompt", event => {
  event.preventDefault();
  installPrompt = event;
  $("install").hidden = false;
});
$("install").onclick = () => run(async () => {
  if (installPrompt) await installPrompt.prompt();
  installPrompt = null;
  $("install").hidden = true;
});
window.addEventListener("online", () => run(refresh));
window.addEventListener("offline", () => run(refresh));
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
run(refresh);
