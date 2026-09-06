const CACHE = "vokabeln-v2";
const DATEIEN = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(DATEIEN)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(k =>
    Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(t => t || fetch(e.request)));
});
