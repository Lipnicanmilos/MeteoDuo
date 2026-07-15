"""MeteoDuo — dve predpovede vedľa seba (yr.no / MET Norway + SHMÚ ALADIN)."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import dukpy
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.services import geocode, openmeteo, shmu, warnings, yr

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
APP_JSX = STATIC_DIR / "app.jsx"
APP_JS = STATIC_DIR / "app.compiled.js"
_jsx_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(follow_redirects=True)
    yield
    await app.state.http.aclose()


app = FastAPI(title="MeteoDuo", lifespan=lifespan)
app.mount("/icons", StaticFiles(directory=STATIC_DIR / "icons"), name="icons")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/radar")
async def radar():
    return FileResponse(STATIC_DIR / "radar.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/app.js")
async def app_js():
    """JSX kompilované na serveri (dukpy/Babel — bez Node aj bez Babel CDN).

    Prekompiluje sa automaticky, keď je app.jsx novší než cache na disku.
    """
    async with _jsx_lock:
        if (not APP_JS.exists()
                or APP_JS.stat().st_mtime < APP_JSX.stat().st_mtime):
            src = APP_JSX.read_text(encoding="utf-8")
            js = await asyncio.to_thread(dukpy.jsx_compile, src)
            APP_JS.write_text(js, encoding="utf-8")
    return FileResponse(APP_JS, media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest",
                        media_type="application/manifest+json")


@app.get("/sw.js")
async def sw_js():
    # no-cache: nová verzia workera sa musí prejaviť hneď pri ďalšej návšteve
    return FileResponse(STATIC_DIR / "sw.js",
                        media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/api/cities")
async def cities():
    return shmu.CITIES


@app.get("/api/forecast/{city_id}")
async def forecast(city_id: str):
    if city_id not in shmu.CITY_IDS:
        raise HTTPException(404, "Neznáme mesto")

    client = app.state.http
    name = shmu.CITY_NAMES[city_id]

    # súradnice sú predpočítané v cities.json; API geokódovanie je len
    # fallback pre pár bodov bez súradníc
    coords = shmu.CITY_COORDS.get(city_id) or await geocode.geocode(client, name)
    okres = shmu.CITY_OKRES.get(city_id)
    yr_data, yr_error = None, None
    om_data, om_error = None, None
    daily_data = None
    warn_list: list = []
    if coords:
        yr_res, om_res, daily_res, warn_res = await asyncio.gather(
            yr.fetch_forecast(client, *coords),
            openmeteo.fetch_forecast(client, *coords),
            openmeteo.fetch_daily(client, *coords),
            warnings.for_okres(client, okres),
            return_exceptions=True,
        )
        if isinstance(yr_res, Exception):
            yr_error = f"MET Norway API nedostupné ({yr_res.__class__.__name__})"
        else:
            yr_data = yr_res
        if isinstance(om_res, Exception):
            om_error = f"Open-Meteo API nedostupné ({om_res.__class__.__name__})"
        else:
            om_data = om_res
        # slnko/UV a výstrahy sú doplnkové — pri chybe len vynecháme
        if not isinstance(daily_res, Exception):
            daily_data = daily_res
        if not isinstance(warn_res, Exception):
            warn_list = warn_res
    else:
        yr_error = om_error = "Miesto sa nepodarilo geokódovať"

    return {
        "city": {"id": city_id, "name": name, "okres": okres,
                 "lat": coords[0] if coords else None,
                 "lon": coords[1] if coords else None},
        "yr": yr_data,
        "yr_error": yr_error,
        "om_models": om_data,   # {"ecmwf": [...], "icon": [...], "gfs": [...]}
        "om_error": om_error,
        "daily": daily_data,    # [{date, sunrise, sunset, uv_max}]
        "warnings": warn_list,  # [{color, level, icon, type, event, onset, expires}]
        "meteogram_url": f"/api/meteogram/{city_id}",
    }


@app.get("/api/meteogram/{city_id}")
async def meteogram(city_id: str, type: str = "aladin"):
    if city_id not in shmu.CITY_IDS:
        raise HTTPException(404, "Neznáme mesto")
    if type not in shmu.METEOGRAM_TYPES:
        raise HTTPException(400, "Neznámy typ meteogramu")
    try:
        png = await shmu.fetch_meteogram_png(app.state.http, city_id, type)
    except httpx.HTTPError:
        raise HTTPException(502, "SHMÚ nedostupné")
    if png is None:
        raise HTTPException(404, "Meteogram sa nenašiel")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=600"})


@app.get("/health")
async def health():
    return {"status": "ok"}
