# ⛅ MeteoDuo

Predpovede počasia z viacerých zdrojov vedľa seba — pre ľubovoľnú slovenskú obec, na 1 / 3 / 10 dní.

**🌐 Naživo: https://h3r2z4x75k.execute-api.eu-central-1.amazonaws.com**

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

## Nasadenie (AWS)

Appka beží na AWS: **https://h3r2z4x75k.execute-api.eu-central-1.amazonaws.com**

- **AWS Lambda** (container image, 1024 MB, eu-central-1) + **API Gateway HTTP API**
  ako verejný endpoint — pri malej návštevnosti prakticky zadarmo (free tier)
- **Lambda Web Adapter** v Dockerfile prekladá Lambda udalosti na HTTP pre
  uvicorn; mimo Lambdy sa neaktivuje, image beží normálne aj lokálne
- JSX sa predkompiluje pri builde image (filesystem Lambdy je read-only
  a cold start preskočí pomalú dukpy kompiláciu)
- **CI/CD:** push do `main` → GitHub Actions (OIDC rola, bez uložených AWS
  kľúčov) → build image → ECR → `lambda update-function-code`
  (`.github/workflows/deploy.yml`)
- **Kde to nájsť v AWS konzole:** región **Europe (Frankfurt) / eu-central-1**
  (vpravo hore prepnúť región!) → Lambda `meteoduo` (appka + CloudWatch logy),
  API Gateway `meteoduo` (verejný endpoint), ECR `meteoduo` (Docker images)

Lokálny kontajner:

```bash
docker build -t meteoduo .
docker run -p 8080:8080 meteoduo
```

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
