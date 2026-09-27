# TODO

## Otvorené

- [ ] **Vlastná doména** — Render custom domain (napr. meteoduo.sk); teraz beží
      na onrender.com subdoméne.
- [ ] **Cold start (free plán Render)** — po ~15 min nečinnosti appka zaspí,
      prvá návšteva ~50 s; zvážiť keep-alive ping alebo platený plán, ak bude vadiť.
- [ ] **Testy** — pytest pre digest funkcie (yr._digest, openmeteo._digest_model,
      warnings._digest) s uloženými JSON fixture — ochrana pri zmene formátu API.
- [ ] **Logging** — chyby externých zdrojov v /api/forecast sa teraz zahadzujú
      potichu (zámerne pre UX); logovať ich do Render logs pre diagnostiku.
- [ ] **Migrácia na Vite** (voliteľné) — frontend zámerne beží cez React CDN
      a JSX kompiluje server (dukpy), bez Node/build kroku; zvážiť pri raste appky.

## Hotové

- [x] **Blesková mapa** ⚡ — panel s embedom `map.blitzortung.org` cez celú šírku,
      centrovaný na vybranú obec (`#zoom/lat/lon`), `Advertisment=0` (odstráni
      AdSense) a `Cookies=0`. POZOR: pôvodné zadanie znelo „burky.cz" — tá doména
      dnes hostí spam pre online kasíno. Česká meteo stránka je **bourky.cz**, tá
      má ale CC BY-NC-ND a sama len embeduje Blitzortung, tak ideme rovno na zdroj.
      Časový rozsah sa cez URL nastaviť nedá (žiadny taký parameter neexistuje) —
      slúži naň menu vnútri mapy.
- [x] **User-Agent pre MET Norway** — yr.py:35 ho posiela bezpodmienečne
      (`MeteoDuo/1.0` + URL repozitára); inak by MET vrátil 403
- [x] **Nasadenie na Render** — https://meteoduo.onrender.com (docker web, free
      plán, Frankfurt, render.yaml); auto-deploy z GitHubu pri push do main.
      Predtým beželo na AWS Lambda + API Gateway — účet zrušený (free plan skončil
      24.9.2026), preto migrácia na Render (2026-09-27)
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
- [x] **Opravy z code review** — neúplné posledné dni modelov sa vynechávajú;
      opravené typy výstrah (7/12/13); CAP bez onset/expires nezhodí render;
      gzip; PNG cache meteogramov; evikcia cache; validácia ?obec=;
      klávesnica pre obľúbené čipy; väčšie dotykové ciele na mobile;
      atribúcia všetkých zdrojov vo footeri (CC BY 4.0)
- [x] Fullscreen radar na /radar (Windy embed, overlay=radar, centrovaný na obec)
- [x] Prepínač rozsahu 1 / 3 / 10 dní
- [x] Porovnanie 4 modelov (yr.no, ECMWF, ICON, GFS) v spoločnej tabuľke
- [x] 4 typy SHMÚ meteogramov (ALADIN, A-LAEF, EPS 8 d, ECMWF 10 d)
- [x] Windy panel (embed widget)
- [x] Obľúbené obce (localStorage)
- [x] Lupa + lightbox na meteograme
- [x] Responzívne mobilné zobrazenie
