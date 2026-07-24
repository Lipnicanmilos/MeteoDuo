"""Generovanie „weather wallpaper" — PNG tapety s aktuálnym počasím pre mobil.

Ikony počasia kreslíme vektorovo cez ImageDraw (default font nemá farebné
emoji a Noto Color Emoji je na slim image krehké). Text vrátane slovenskej
diakritiky ide cez DejaVu (balík fonts-dejavu-core v Dockerfile), s fallbackom
na systémové fonty pri lokálnom vývoji.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont

# ── fonty ───────────────────────────────────────────────────────────────────
_FONT_PATHS = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",   # Linux / Lambda
        "C:/Windows/Fonts/segoeui.ttf",                       # Windows dev
        "C:/Windows/Fonts/arial.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
}
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    key = (kind, size)
    cached = _font_cache.get(key)
    if cached:
        return cached
    for path in _FONT_PATHS[kind]:
        try:
            f = ImageFont.truetype(path, size)
            _font_cache[key] = f
            return f
        except OSError:
            continue
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f


# ── mapovanie MET Norway symbol_code → (SK popis, druh ikony) ────────────────
_DAY_SK = ["Ne", "Po", "Ut", "St", "Št", "Pi", "So"]  # Python weekday(): Po=0
_DAY_SK_BY_WD = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]


def _condition(symbol_code: str | None) -> tuple[str, str]:
    """Vráti (slovenský popis, druh ikony) z MET Norway symbol_code."""
    if not symbol_code:
        return ("—", "unknown")
    base = symbol_code
    for suf in ("_day", "_night", "_polartwilight"):
        if base.endswith(suf):
            base = base[: -len(suf)]
            break
    # poradie je dôležité: špecifickejšie javy najprv
    checks = [
        ("thunder", "Búrky", "thunder"),
        ("sleet", "Dážď so snehom", "sleet"),
        ("snow", "Sneženie", "snow"),
        ("rainshowers", "Prehánky", "showers"),
        ("showers", "Prehánky", "showers"),
        ("rain", "Dážď", "rain"),
        ("fog", "Hmla", "fog"),
        ("partlycloudy", "Polojasno", "partly"),
        ("cloudy", "Zamračené", "cloudy"),
        ("fair", "Skoro jasno", "fair"),
        ("clearsky", "Jasno", "clear"),
    ]
    for needle, label, kind in checks:
        if needle in base:
            return (label, kind)
    return ("—", "unknown")


def _is_night(symbol_code: str | None, hourly_time: str | None) -> bool:
    if symbol_code:
        if symbol_code.endswith("_night"):
            return True
        if symbol_code.endswith(("_day", "_polartwilight")):
            return False
    # fallback podľa hodiny (UTC ~ SK je +1/+2, na deň/noc stačí hrubý odhad)
    try:
        hour = int((hourly_time or "")[11:13])
        return hour < 6 or hour >= 20
    except (ValueError, IndexError):
        return False


# ── farebné palety (top, bottom) podľa druhu a dennej doby ──────────────────
_PALETTES = {
    "clear":   ((0x2B, 0x5C, 0x8A), (0x5A, 0x93, 0xC7)),
    "fair":    ((0x2F, 0x5F, 0x8C), (0x62, 0x98, 0xC9)),
    "partly":  ((0x44, 0x54, 0x66), (0x74, 0x8A, 0xA0)),
    "cloudy":  ((0x48, 0x52, 0x60), (0x74, 0x80, 0x90)),
    "rain":    ((0x2A, 0x33, 0x40), (0x4C, 0x5A, 0x6B)),
    "showers": ((0x2E, 0x3B, 0x4C), (0x54, 0x67, 0x7C)),
    "thunder": ((0x22, 0x27, 0x33), (0x45, 0x4C, 0x60)),
    "snow":    ((0x54, 0x64, 0x78), (0x93, 0xA6, 0xBB)),
    "sleet":   ((0x4A, 0x58, 0x68), (0x82, 0x93, 0xA6)),
    "fog":     ((0x53, 0x5D, 0x6B), (0x8A, 0x94, 0xA2)),
    "unknown": ((0x33, 0x3B, 0x47), (0x5B, 0x66, 0x76)),
}
_NIGHT = ((0x0A, 0x11, 0x20), (0x1E, 0x29, 0x3B))


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── vektorové ikony počasia ─────────────────────────────────────────────────
SUN = (255, 205, 74)
MOON = (233, 238, 245)
CLOUD = (240, 244, 249)
CLOUD_DARK = (206, 214, 224)
RAIN = (124, 186, 245)
SNOWF = (255, 255, 255)
BOLT = (255, 214, 92)


def _sun(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color=SUN):
    import math
    for i in range(12):
        ang = math.pi * i / 6
        x1 = cx + math.cos(ang) * r * 1.35
        y1 = cy + math.sin(ang) * r * 1.35
        x2 = cx + math.cos(ang) * r * 1.75
        y2 = cy + math.sin(ang) * r * 1.75
        d.line([(x1, y1), (x2, y2)], fill=color, width=max(3, int(r * 0.11)))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def _moon(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, bg: tuple):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOON)
    off = r * 0.55
    d.ellipse([cx - r + off, cy - r - r * 0.15,
               cx + r + off, cy + r - r * 0.15], fill=bg)


def _cloud(d: ImageDraw.ImageDraw, cx: float, cy: float, w: float, color=CLOUD):
    h = w * 0.60
    left, right = cx - w / 2, cx + w / 2
    base_top = cy + h * 0.02
    d.rounded_rectangle([left, base_top, right, cy + h / 2],
                        radius=h * 0.30, fill=color)
    d.ellipse([left, cy - h * 0.05, left + w * 0.50, cy - h * 0.05 + w * 0.50],
              fill=color)
    d.ellipse([cx - w * 0.10, cy - h * 0.42,
               cx - w * 0.10 + w * 0.58, cy - h * 0.42 + w * 0.58], fill=color)
    d.ellipse([right - w * 0.52, cy - h * 0.08,
               right, cy - h * 0.08 + w * 0.50], fill=color)


def _drops(d, cx, cy, w, n=3, color=RAIN):
    step = w * 0.28
    x0 = cx - step * (n - 1) / 2
    for i in range(n):
        x = x0 + i * step
        d.line([(x, cy), (x + w * 0.05, cy + w * 0.22)],
               fill=color, width=max(3, int(w * 0.05)))


def _flakes(d, cx, cy, w, n=3, color=SNOWF):
    step = w * 0.28
    x0 = cx - step * (n - 1) / 2
    r = w * 0.05
    for i in range(n):
        x = x0 + i * step
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=color)


def _bolt(d, cx, cy, w, color=BOLT):
    s = w * 0.5
    pts = [(cx + s * 0.15, cy - s * 0.5), (cx - s * 0.25, cy + s * 0.15),
           (cx + s * 0.02, cy + s * 0.15), (cx - s * 0.15, cy + s * 0.7),
           (cx + s * 0.30, cy - s * 0.05), (cx + s * 0.03, cy - s * 0.05)]
    d.polygon(pts, fill=color)


def _draw_icon(d, kind, cx, cy, size, is_night, bg):
    """Vykreslí ikonu počasia so stredom (cx, cy) a šírkou ~size."""
    r = size * 0.30
    if kind in ("clear", "fair"):
        if is_night:
            _moon(d, cx, cy, r * 1.15, bg)
        else:
            _sun(d, cx, cy, r)
        if kind == "fair":
            _cloud(d, cx + size * 0.16, cy + size * 0.16, size * 0.55)
        return
    if kind == "partly":
        if is_night:
            _moon(d, cx - size * 0.16, cy - size * 0.14, r * 0.85, bg)
        else:
            _sun(d, cx - size * 0.16, cy - size * 0.14, r * 0.7)
        _cloud(d, cx + size * 0.08, cy + size * 0.10, size * 0.72)
        return
    if kind == "cloudy" or kind == "unknown":
        _cloud(d, cx, cy, size * 0.9, CLOUD if kind == "cloudy" else CLOUD_DARK)
        return
    if kind == "fog":
        _cloud(d, cx, cy - size * 0.1, size * 0.85)
        for i in range(3):
            y = cy + size * (0.28 + i * 0.12)
            d.line([(cx - size * 0.38, y), (cx + size * 0.38, y)],
                   fill=CLOUD_DARK, width=max(3, int(size * 0.04)))
        return
    # zrážkové javy: oblak + niečo pod ním
    _cloud(d, cx, cy - size * 0.14, size * 0.85)
    below_y = cy + size * 0.30
    if kind == "rain":
        _drops(d, cx, below_y, size * 0.8, n=3)
    elif kind == "showers":
        _drops(d, cx, below_y, size * 0.8, n=2)
    elif kind == "snow":
        _flakes(d, cx, below_y, size * 0.8, n=3)
    elif kind == "sleet":
        _drops(d, cx - size * 0.12, below_y, size * 0.5, n=1)
        _flakes(d, cx + size * 0.12, below_y, size * 0.5, n=1)
    elif kind == "thunder":
        _bolt(d, cx, below_y, size * 0.8)


# ── text s jemným tieňom ─────────────────────────────────────────────────────
def _text(d, xy, text, font, fill=(255, 255, 255), anchor="mm",
          shadow=(0, 0, 0, 90)):
    x, y = xy
    d.text((x + 2, y + 3), text, font=font, anchor=anchor,
           fill=(0, 0, 0))
    d.text((x, y), text, font=font, anchor=anchor, fill=fill)


def _fmt_temp(t) -> str:
    if t is None:
        return "–"
    return f"{round(t)}°"


# ── hlavný render ────────────────────────────────────────────────────────────
def render(city_name: str, yr_data: dict | None, *, width: int = 1170,
           height: int = 2532, updated: datetime | None = None) -> bytes:
    """Vyrenderuje tapetu a vráti PNG bajty."""
    W, H = width, height
    hourly = (yr_data or {}).get("hourly") or []
    days = (yr_data or {}).get("days") or []
    now_h = hourly[0] if hourly else {}
    symbol = now_h.get("symbol")
    label, kind = _condition(symbol)
    is_night = _is_night(symbol, now_h.get("time"))

    top, bottom = _NIGHT if is_night else _PALETTES.get(kind, _PALETTES["unknown"])

    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=_lerp(top, bottom, y / H))

    mid_bg = _lerp(top, bottom, 0.34)  # farba pozadia v oblasti ikony (pre mesiac)

    # mesto
    _text(d, (W / 2, H * 0.235), city_name, _font("regular", int(W * 0.062)))

    # ikona počasia
    _draw_icon(d, kind, W / 2, H * 0.345, W * 0.34, is_night, mid_bg)

    # teplota (veľká)
    cur_temp = now_h.get("temp")
    _text(d, (W / 2, H * 0.475), _fmt_temp(cur_temp), _font("bold", int(W * 0.27)))

    # popis počasia
    _text(d, (W / 2, H * 0.565), label, _font("regular", int(W * 0.058)))

    # max / min dnes
    if days:
        hi = _fmt_temp(days[0].get("temp_max"))
        lo = _fmt_temp(days[0].get("temp_min"))
        _text(d, (W / 2, H * 0.615), f"↑ {hi}   ↓ {lo}",
              _font("regular", int(W * 0.05)), fill=(226, 232, 240))

    # 3-dňový pás
    if len(days) >= 2:
        strip = days[:3]
        n = len(strip)
        col_w = W * 0.74 / n
        x0 = W * 0.13 + col_w / 2
        y = H * 0.76
        for i, dd in enumerate(strip):
            cx = x0 + i * col_w
            wd = _weekday_label(dd.get("date"), i)
            _text(d, (cx, y), wd, _font("bold", int(W * 0.042)),
                  fill=(226, 232, 240))
            _, k2 = _condition(dd.get("symbol"))
            # pás = denné súhrny → ikony vždy v dennej variante (sln. namiesto mesiaca)
            _draw_icon(d, k2, cx, y + H * 0.045, W * 0.14, False, mid_bg)
            hi = _fmt_temp(dd.get("temp_max"))
            lo = _fmt_temp(dd.get("temp_min"))
            _text(d, (cx, y + H * 0.092), f"{hi} / {lo}",
                  _font("regular", int(W * 0.035)), fill=(203, 213, 225))

    # pätička
    when = (updated or datetime.now(timezone.utc)).astimezone()
    _text(d, (W / 2, H * 0.945),
          f"MeteoDuo · aktualizované {when:%H:%M}",
          _font("regular", int(W * 0.033)), fill=(203, 213, 225))
    _text(d, (W / 2, H * 0.965), "Zdroj: MET Norway (yr.no)",
          _font("regular", int(W * 0.026)), fill=(148, 163, 184))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _weekday_label(date_iso: str | None, index: int) -> str:
    if index == 0:
        return "Dnes"
    if index == 1:
        return "Zajtra"
    try:
        wd = datetime.strptime(date_iso, "%Y-%m-%d").weekday()
        return _DAY_SK_BY_WD[wd]
    except (ValueError, TypeError):
        return ""
