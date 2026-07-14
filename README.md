# ⛅ MeteoDuo

Dve predpovede počasia vedľa seba — pre ľubovoľnú slovenskú obec, na 3 dni.

| Ľavý panel | Stred | Pravý panel |
|---|---|---|
| **yr.no** (MET Norway) — hodinová predpoveď: teplota, zrážky, vietor | Vybraná obec + denný súhrn na 3 dni | **SHMÚ** — meteogram modelu ALADIN (aktualizovaný 4× denne) |

## Architektúra

- **Backend:** FastAPI (Python) — `app/`
  - `/api/cities` — zoznam 1068 slovenských obcí (podľa číselníka SHMÚ)
  - `/api/forecast/{city_id}` — geokódovanie (Open-Meteo) + predpoveď z MET Norway Locationforecast 2.0
  - `/api/meteogram/{city_id}` — proxy najnovšieho ALADIN meteogramu zo shmu.sk
- **Frontend:** React 18 cez CDN (bez build kroku) — `static/index.html`

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

## Zdroje dát a licencie

- Predpoveď: [MET Norway](https://api.met.no) — Locationforecast 2.0, licencia
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (rovnaké dáta zobrazuje yr.no)
- Meteogram: [SHMÚ](https://www.shmu.sk) — model ALADIN, verejne dostupné meteogramy pre územie SR
- Geokódovanie: [Open-Meteo Geocoding API](https://open-meteo.com/)

MeteoDuo dáta iba zobrazuje; nie je ich autorom a nenesie zodpovednosť za ich presnosť.
