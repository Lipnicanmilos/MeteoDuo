/* MeteoDuo service worker — offline: statika + posledná načítaná predpoveď.
 *
 * Stratégie:
 *  - React CDN (unpkg, verziované URL) ... cache-first, nemenia sa
 *  - všetko ostatné (HTML, /app.js, /api/*) ... network-first; úspešná
 *    odpoveď sa uloží do cache a pri výpadku siete sa servíruje z nej —
 *    tým je posledná predpoveď (aj meteogram) dostupná offline
 */
// POZOR: pri zmene statiky (index.html, app.jsx, ikony) zdvihni verziu —
// online používatelia dostanú novú verziu aj bez toho (network-first),
// ale offline cache sa prečistí až po bumpe
const CACHE = "meteoduo-v4";

const PRECACHE = [
  "/",
  "/app.js",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "https://unpkg.com/react@18/umd/react.production.min.js",
  "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js",
];

self.addEventListener("install", (e) => {
  // ručný fetch + put namiesto addAll: unpkg vracia opaque response (no-cors)
  // a addAll opaque odpovede odmieta (status 0 != ok)
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(PRECACHE.map(
        (u) => fetch(u, { mode: u.startsWith("/") ? "same-origin" : "no-cors" })
          .then((res) => c.put(u, res))
      )))
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

  // CDN knižnice: cache-first (verziované, nemenia sa)
  if (url.origin === "https://unpkg.com") {
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
