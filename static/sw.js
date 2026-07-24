/* MeteoDuo service worker — offline: statika + posledná načítaná predpoveď.
 *
 * Stratégie:
 *  - /vendor/* (React, self-hostovaný) ... cache-first, mení sa len pri update
 *  - všetko ostatné (HTML, /app.js, /api/*) ... network-first; úspešná
 *    odpoveď sa uloží do cache a pri výpadku siete sa servíruje z nej —
 *    tým je posledná predpoveď (aj meteogram) dostupná offline
 */
// POZOR: pri zmene statiky (index.html, app.jsx, ikony) zdvihni verziu —
// online používatelia dostanú novú verziu aj bez toho (network-first),
// ale offline cache sa prečistí až po bumpe
const CACHE = "meteoduo-v10";

const PRECACHE = [
  "/",
  "/app.js",
  "/manifest.webmanifest",
  "/favicon.ico",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/vendor/react.production.min.js",
  "/vendor/react-dom.production.min.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // knižnice vo /vendor/: cache-first (menia sa len pri ručnom update)
  if (url.origin === location.origin && url.pathname.startsWith("/vendor/")) {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }))
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // vlastný server: network-first, fallback na cache (posledná predpoveď)
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req).then((hit) => {
        if (hit) return hit;
        // offline navigácia na necachovanú URL -> aspoň hlavná stránka
        if (req.mode === "navigate") return caches.match("/");
        return Response.error();
      }))
  );
});
