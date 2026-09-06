const CACHE = "vokabeln-v3";
const DATEIEN = ["./", "./index.html", "./manifest.webmanifest", "./icon-180.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(DATEIEN)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(k =>
    Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const istSeite = e.request.mode === "navigate" || e.request.destination === "document";
  if (istSeite) {
    e.respondWith(
      fetch(e.request).then(antwort => {
        const kopie = antwort.clone();
        caches.open(CACHE).then(c => c.put("./index.html", kopie));
        return antwort;
      }).catch(() => caches.match("./index.html"))
    );
  } else {
    e.respondWith(caches.match(e.request).then(t => t || fetch(e.request)));
  }
});
