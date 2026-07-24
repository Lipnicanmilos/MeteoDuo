"""MeteoDuo — dve predpovede vedľa seba (yr.no / MET Norway + SHMÚ ALADIN)."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import dukpy
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.services import geocode, openmeteo, shmu, wallpaper, warnings, yr

DEFAULT_CITY = "32737"  # Bratislava (centrum) — predvolené mesto pre tapetu

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
app.add_middleware(GZipMiddleware, minimum_size=1024)  # app.js, cities, forecast
app.mount("/icons", StaticFiles(directory=STATIC_DIR / "icons"), name="icons")
# React je self-hostovaný — z unpkg bol jedinou cudzou závislosťou na kritickej
# ceste a jeho výpadok by znamenal prázdnu stránku
app.mount("/vendor", StaticFiles(directory=STATIC_DIR / "vendor"), name="vendor")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/radar")
async def radar():
    return FileResponse(STATIC_DIR / "radar.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # prehliadače si ho pýtajú aj pri <link rel="icon"> na PNG — bez tejto
    # routy je z každej návštevy 404 (a po zapnutí logovania šum v CloudWatch)
    return FileResponse(STATIC_DIR / "favicon.ico", media_type="image/x-icon",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/windy")
async def windy():
    return FileResponse(STATIC_DIR / "windy.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/blesky")
async def blesky():
    return FileResponse(STATIC_DIR / "blesky.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/widget")
async def widget():
    # landing na stiahnutie natívneho Android widgetu (APK z GitHub Releases)
    return FileResponse(STATIC_DIR / "widget.html",
                        headers={"Cache-Control": "no-cache"})


APK_URL = ("https://github.com/Lipnicanmilos/MeteoDuo/releases/download/"
           "widget-latest/meteoduo-widget.apk")


@app.get("/download/meteoduo-widget.apk")
async def download_widget_apk():
    """APK proxujeme z GitHub Releases cez vlastnú doménu.

    Niektoré mobilné siete/prehliadače zamrznú pri redirect na
    release-assets.githubusercontent.com — servírovaním z tej istej domény,
    na ktorej appka beží, sa tomu vyhneme. (APK ~2 MB < 6 MB Lambda limit.)
    """
    try:
        r = await app.state.http.get(APK_URL, timeout=30)
        r.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(502, "APK sa nepodarilo načítať z GitHubu")
    return Response(
        content=r.content,
        media_type="application/vnd.android.package-archive",
        headers={
            "Content-Disposition": 'attachment; filename="meteoduo-widget.apk"',
            "Content-Length": str(len(r.content)),
            "Cache-Control": "public, max-age=300",
        },
    )


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
            try:
                APP_JS.write_text(js, encoding="utf-8")
            except OSError:
                # read-only filesystem (AWS Lambda) — cache na disk nejde,
                # skompilovaný JS pošleme priamo z pamäte
                return Response(content=js,
                                media_type="application/javascript",
                                headers={"Cache-Control": "no-cache"})
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

    # Najstarší z časov stiahnutia — zdroje majú vlastné cache, ktoré môžu
    # expirovať v rôznych momentoch. Radšej podhodnotiť čerstvosť než nadhodnotiť.
    fetched_at = None
    if coords:
        stamps = [s for s in (yr.cached_at(*coords), openmeteo.cached_at(*coords)) if s]
        if stamps:
            fetched_at = min(stamps).isoformat()

    return {
        "fetched_at": fetched_at,   # ISO UTC, kedy sa dáta reálne stiahli zo zdrojov
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


@app.get("/wallpaper.png")
async def wallpaper_png(city: str = DEFAULT_CITY, w: int = 1170, h: int = 2532):
    """PNG tapeta s aktuálnym počasím pre mobil.

    Dá sa stiahnuť priamo v appke, alebo z tejto URL periodicky ťahať cez
    iOS Skratky / Android Tasker a nastaviť ako (skoro-živú) tapetu.
    """
    if city not in shmu.CITY_IDS:
        city = DEFAULT_CITY
    w = max(320, min(w, 2000))
    h = max(480, min(h, 3200))

    client = app.state.http
    name = shmu.CITY_NAMES[city]
    coords = shmu.CITY_COORDS.get(city) or await geocode.geocode(client, name)

    yr_data, updated = None, None
    if coords:
        try:
            yr_data = await yr.fetch_forecast(client, *coords)
            updated = yr.cached_at(*coords)
        except httpx.HTTPError:
            yr_data = None  # render vypíše zástupné pomlčky namiesto pádu

    png = await asyncio.to_thread(
        wallpaper.render, name, yr_data, width=w, height=h, updated=updated
    )
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=900"})


@app.get("/health")
async def health():
    return {"status": "ok"}
