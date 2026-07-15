# TODO

## Otvorené

- [ ] **Nasadenie** — Cloud Run alebo AWS; Dockerfile je hotový, appka zatiaľ
      beží len lokálne. Po nasadení skontrolovať User-Agent limity API
      (MET Norway vyžaduje identifikáciu) a prípadne pridať rate-limit.
- [ ] **Migrácia na Vite** (voliteľné) — frontend zámerne beží cez React CDN
      a JSX kompiluje server (dukpy), bez Node/build kroku; zvážiť pri raste appky.

## Hotové

- [x] **Súradnice + okres v cities.json** — scripts/geocode_cities.py (súradnice),
      scripts/assign_okres.py (okres pre výstrahy); API geokódovanie je len fallback
- [x] **Serverová kompilácia JSX** — JSX v static/app.jsx, kompiluje server cez
      dukpy (Babel v Pythone) na /app.js s auto-rekompiláciou; Babel z prehliadača preč
- [x] **PWA** — manifest.webmanifest + sw.js (network-first, posledná predpoveď
      offline; CDN cache-first), ikony cez Pillow (scripts/make_icons.py)
- [x] **Výstrahy SHMÚ / Meteoalarm** ⚠️ — warnings.py (JSON feed, na úrovni okresu),
      farebný prúžok + badge pri obci
- [x] **Východ/západ slnka + UV index** — openmeteo.fetch_daily, v denných kartách
      🌅/🌇 + farebný UV pill (škála WHO)
- [x] **Sparkline grafy** — SVG trend teploty a zrážok pre každý model nad tabuľkou
- [x] **Zdieľateľná URL** — ?obec=&dni= (init z URL + sync cez history.replaceState)
- [x] **Tmavý režim** — prepínač auto/svetlý/tmavý, CSS premenné + prefers-color-scheme
- [x] Fullscreen radar na /radar (Windy embed, overlay=radar, centrovaný na obec)
- [x] Prepínač rozsahu 1 / 3 / 10 dní
- [x] Porovnanie 4 modelov (yr.no, ECMWF, ICON, GFS) v spoločnej tabuľke
- [x] 4 typy SHMÚ meteogramov (ALADIN, A-LAEF, EPS 8 d, ECMWF 10 d)
- [x] Windy panel (embed widget)
- [x] Obľúbené obce (localStorage)
- [x] Lupa + lightbox na meteograme
- [x] Responzívne mobilné zobrazenie
