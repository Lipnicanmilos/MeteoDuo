# ⛅ MeteoDuo

Predpovede počasia z viacerých zdrojov vedľa seba — pre ľubovoľnú slovenskú obec, na 1 / 3 / 10 dní.

| Ľavý panel | Stred | Pravý panel |
|---|---|---|
| **yr.no** (MET Norway) — hodinová predpoveď: teplota, zrážky, vietor | Vybraná obec + denný súhrn | **SHMÚ** — meteogramy (ALADIN, A-LAEF, EPS, ECMWF) |

Pod panelmi:

- **Porovnanie modelov** — spoločná tabuľka deň po dni: yr.no (MET Norway),
  ECMWF (model, ktorý predvolene zobrazuje Windy aj 10-dňový meteogram SHMÚ),
  ICON (DWD) a GFS (NOAA). Δ badge upozorní na veľký rozptyl medzi modelmi
  (teplota ≥ 2 °C, zrážky ≥ 3 mm).
- **Windy** — interaktívna mapa (oficiálny embed widget) so značkou na
  vybranej obci a bodovou predpoveďou.

## Funkcie

- Prepínač rozsahu **1 deň / 3 dni / 10 dní** (pri 1 dni hodinovka po hodine,
  pri 10 dňoch sa automaticky zvolí 10-dňový ECMWF meteogram SHMÚ)
- **4 typy SHMÚ meteogramov** prepínateľné čipmi: ALADIN (3 dni),
  A-LAEF ansámbel (3 dni), ECMWF EPS ansámbel (8 dní), ECMWF (10 dní)
- **Obľúbené obce** — hviezdička + čipy na rýchle prepínanie (localStorage)
- **Lupa** na meteograme (hover, desktop) a **lightbox** (klik = zväčšenie
  na stred obrazovky, Esc/klik zatvorí)
- Responzívne mobilné zobrazenie (panely pod sebou)

## Architektúra

- **Backend:** FastAPI (Python) — `app/`
  - `/api/cities` — zoznam 1068 slovenských obcí (podľa číselníka SHMÚ)
  - `/api/forecast/{city_id}` — geokódovanie (Open-Meteo) + yr.no predpoveď
    + 3 modely (ECMWF, ICON, GFS) cez Open-Meteo jedným requestom
  - `/api/meteogram/{city_id}?type=aladin|laef|egram8|mgram10` — proxy
    najnovšieho meteogramu zo shmu.sk
- **Frontend:** React 18 cez CDN, JSX v `static/app.jsx` — kompiluje ho
  server (dukpy/Babel v Pythone, žiadny Node) na route `/app.js`;
  prekompiluje sa automaticky pri zmene zdroja

## Lokálne spustenie

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Windows
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8901
```

Aplikácia beží na http://localhost:8901.

## Nasadenie (Cloud Run / AWS)

Kontajner je čisto pythonovský — žiadny Node/build krok:

```bash
docker build -t meteoduo .
docker run -p 8080:8080 meteoduo
```

Otvorené úlohy sú v [TODO.md](TODO.md).

## Zdroje dát a licencie

- Predpoveď: [MET Norway](https://api.met.no) — Locationforecast 2.0, licencia
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (rovnaké dáta zobrazuje yr.no)
- Modely ECMWF / ICON / GFS: [Open-Meteo](https://open-meteo.com/) — CC BY 4.0
- Meteogramy: [SHMÚ](https://www.shmu.sk) — verejne dostupné meteogramy pre územie SR
- Mapa: [Windy](https://www.windy.com) — oficiálny embed widget
- Geokódovanie: [Open-Meteo Geocoding API](https://open-meteo.com/)

MeteoDuo dáta iba zobrazuje; nie je ich autorom a nenesie zodpovednosť za ich presnosť.
