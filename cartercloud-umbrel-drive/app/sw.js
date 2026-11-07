const SHELL = "umbrel-drive-shell-v1";
const ASSETS = ["/", "/style.css", "/drive.js", "/manifest.webmanifest", "/icon.svg", "/icon-192.png", "/icon-512.png"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(ASSETS)));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys
    .filter(key => key.startsWith("umbrel-drive-shell-") && key !== SHELL)
    .map(key => caches.delete(key)))));
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || !ASSETS.includes(url.pathname)) return;
  event.respondWith(fetch(event.request).catch(() => caches.open(SHELL).then(cache => cache.match(url.pathname))));
});
