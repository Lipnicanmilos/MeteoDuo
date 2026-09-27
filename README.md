# ⛅ MeteoDuo

Predpovede počasia z viacerých zdrojov vedľa seba — pre ľubovoľnú slovenskú obec, na 1 / 3 / 10 dní.

**🌐 Naživo: https://meteoduo.onrender.com**

| Ľavý panel | Stred | Pravý panel |
|---|---|---|
| **yr.no** (MET Norway) — hodinová predpoveď: teplota, zrážky, vietor | Vybraná obec + denný súhrn | **SHMÚ** — meteogramy (ALADIN, A-LAEF, EPS, ECMWF) |

Pod panelmi:

- **Porovnanie modelov** — spoločná tabuľka deň po dni: yr.no (MET Norway),
  ECMWF (model, ktorý predvolene zobrazuje Windy aj 10-dňový meteogram SHMÚ),
  ICON (DWD) a GFS (NOAA). Δ badge upozorní na veľký rozptyl medzi modelmi
  (teplota ≥ 2 °C, zrážky ≥ 3 mm). Nad tabuľkou **sparkline** trend teploty
  a zrážok pre každý model.
- **Windy** — interaktívna mapa (oficiálny embed widget) so značkou na
  vybranej obci a bodovou predpoveďou.

## Funkcie

- Prepínač rozsahu **1 deň / 3 dni / 10 dní** (pri 1 dni hodinovka po hodine,
  pri 10 dňoch sa automaticky zvolí 10-dňový ECMWF meteogram SHMÚ)
- **Výstrahy počasia** — farebný prúžok + ikonka pri obci, keď v jej okrese
  platí (alebo o chvíľu začne) výstraha SHMÚ/Meteoalarm (vietor, búrky,
  teploty, poľadovica…), so žltou/oranžovou/červenou úrovňou a platnosťou
- **Východ/západ slnka + UV index** v dennom súhrne (UV farebne podľa škály WHO)
- **4 typy SHMÚ meteogramov** prepínateľné čipmi: ALADIN (3 dni),
  A-LAEF ansámbel (3 dni), ECMWF EPS ansámbel (8 dní), ECMWF (10 dní)
- **Obľúbené obce** — hviezdička + čipy na rýchle prepínanie (localStorage)
- **Zdieľateľná URL** — obec a rozsah sú v adrese (`?obec=32463&dni=10`),
  odkaz otvorí presne ten istý pohľad
- **Tmavý režim** — prepínač automatický / svetlý / tmavý v hlavičke
- **PWA** — inštalovateľná na mobil, posledná predpoveď dostupná offline
- **Mapy na celú obrazovku** — zrážkový **radar** a **Windy** (oficiálny embed),
  **blesky** naživo (Blitzortung)
- **Počasie na plochu telefónu:**
  - **Natívne Android widgety** so živou predpoveďou (stránka `/widget`) —
    dva typy: „**MeteoDuo — počasie**" (aktuálne) a „**MeteoDuo — 24 h**"
    (8-stĺpcová hodinovka). Sám sa obnovuje, renderuje sa natívne (nie je to
    obrázok), s nastavením mesta (vyhľadávanie + obľúbené) a priehľadnosti;
    klik otvorí appku, ⚙ nastavenia. Súčasťou APK je aj appka (WebView) na
    ikonu domovskej obrazovky
  - **Tapeta** s aktuálnym počasím (`/wallpaper.png`) — obrázok generovaný
    serverom (Pillow), layout sa vyberá podľa pomeru strán (tapeta / široký /
    štvorcový widget); dá sa ťahať aj cez iOS Skratky / Android KWGT
- **Lupa** na meteograme (hover, desktop) a **lightbox** (klik = zväčšenie
  na stred obrazovky, Esc/klik zatvorí)
- Responzívne mobilné zobrazenie (panely pod sebou)

## Architektúra

- **Backend:** FastAPI (Python) — `app/`
  - `/api/cities` — zoznam 1068 slovenských obcí (podľa číselníka SHMÚ)
  - `/api/forecast/{city_id}` — yr.no predpoveď + 3 modely (ECMWF, ICON, GFS)
    a denné údaje (slnko/UV) cez Open-Meteo + výstrahy Meteoalarm pre okres obce;
    súradnice a okres sú predpočítané v `cities.json` (geokódovanie je fallback)
  - `/api/meteogram/{city_id}?type=aladin|laef|egram8|mgram10` — proxy
    najnovšieho meteogramu zo shmu.sk
  - `/wallpaper.png?city=&w=&h=` — PNG s aktuálnym počasím (Pillow); layout
    (tapeta / široký / štvorcový widget) sa vyberá podľa pomeru strán
  - `/widget` + `/download/meteoduo-widget.apk` — landing na natívny Android
    widget a proxy stiahnutie APK z GitHub Releases cez vlastnú doménu
  - `/radar`, `/windy`, `/blesky` — mapy na celú obrazovku (Windy / Blitzortung embed)
  - `/manifest.webmanifest`, `/sw.js`, `/icons/*` — PWA (inštalácia + offline cache)
- **Frontend:** React 18 cez CDN, JSX v `static/app.jsx` — kompiluje ho
  server (dukpy/Babel v Pythone, žiadny Node) na route `/app.js`;
  prekompiluje sa automaticky pri zmene zdroja
- **Jednorazové skripty** — `scripts/geocode_cities.py` (súradnice obcí),
  `scripts/assign_okres.py` (okres pre výstrahy), `scripts/make_icons.py`
  (PWA ikony); spúšťajú sa len pri zmene zoznamu obcí
- **Výkon** — gzip kompresia odpovedí; in-memory cache s TTL a evikciou:
  predpovede 15 min, meteogramy (URL aj PNG) 10 min, výstrahy 10 min —
  externé API sa nezaťažujú opakovanými requestami

## Lokálne spustenie

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Windows
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8901
```

Aplikácia beží na http://localhost:8901.

## Nasadenie (Render)

Appka beží na **Render** (free plán) — kontajner podľa `Dockerfile`, konfig
v [`render.yaml`](render.yaml):

- **Docker web služba**, región Frankfurt, health-check `/health`
- **Auto-deploy:** Render sleduje repo a pri každom push do `main` spraví nový
  build a nasadenie (žiadne CI kľúče netreba — deploy rieši Render cez GitHub app)
- Port príde cez `$PORT` (Render), lokálne default 8080
- JSX sa predkompiluje pri builde image (rýchlejší štart)
- **Pozor (free plán):** služba po ~15 min nečinnosti „zaspí"; prvá návšteva
  potom trvá ~50 s, kým sa kontajner naštartuje

Prepojenie repa s Renderom: [render.com](https://render.com) → **New → Blueprint**
→ vybrať repo `MeteoDuo` (Render načíta `render.yaml`) → **Apply**.

Lokálny kontajner:

```bash
docker build -t meteoduo .
docker run -p 8080:8080 -e PORT=8080 meteoduo
```

## Android appka a widgety

Samostatný Kotlin projekt v [`android/`](android/) — ťahá živú predpoveď z
`/api/forecast/{cityId}` a renderuje ju natívne cez RemoteViews:

- **Dva widgety:** aktuálne počasie a 24-hodinová hodinovka (8 stĺpcov).
- **Nastavenie:** vyhľadávanie obce (z `/api/cities`), obľúbené mestá a
  priehľadnosť pozadia — otvoriteľné z widgetu (⚙) hocikedy.
- **Appka (WebView):** ikona v zásuvke otvorí webové MeteoDuo; klik na widget
  ju tiež otvorí.

**Build v cloude** cez GitHub Actions
([`.github/workflows/android.yml`](.github/workflows/android.yml)): push do
`android/**` → **podpísaný release APK** (stabilný keystore vygeneruje a
commitne CI, takže updaty sa inštalujú bez odinštalovania) → release
`widget-latest`. Web stránka `/widget` ho ponúka na stiahnutie cez
`/download/meteoduo-widget.apk` (proxy z vlastnej domény). Odkaz „Widget" sa
v appke zobrazuje len na Androide. Detaily v
[android/README.md](android/README.md).

Otvorené úlohy sú v [TODO.md](TODO.md).

## Zdroje dát a licencie

- Predpoveď: [MET Norway](https://api.met.no) — Locationforecast 2.0, licencia
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (rovnaké dáta zobrazuje yr.no)
- Modely ECMWF / ICON / GFS + slnko/UV: [Open-Meteo](https://open-meteo.com/) — CC BY 4.0
- Meteogramy: [SHMÚ](https://www.shmu.sk) — verejne dostupné meteogramy pre územie SR
- Výstrahy: [Meteoalarm](https://meteoalarm.org) — feed SHMÚ, CC BY 4.0
- Mapa: [Windy](https://www.windy.com) — oficiálny embed widget
- Geokódovanie: [Open-Meteo Geocoding API](https://open-meteo.com/)

MeteoDuo dáta iba zobrazuje; nie je ich autorom a nenesie zodpovednosť za ich presnosť.
