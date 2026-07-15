"""Jednorazové vygenerovanie PWA ikon (spusti: python scripts/make_icons.py).

Kreslí sa v 1024×1024 a zmenšuje LANCZOS-om. Kompozícia (slnko + oblak)
je držaná v strede — vojde sa do maskable bezpečnej zóny (vnútorných 80 %),
takže jedna grafika slúži pre purpose "any" aj "maskable".
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
OUT = Path(__file__).resolve().parent.parent / "static" / "icons"

GRAD_FROM = (37, 99, 235)    # --primary #2563eb
GRAD_TO = (14, 165, 233)     # --accent  #0ea5e9
SUN = (253, 224, 71)         # #fde047
SUN_EDGE = (250, 204, 21)    # #facc15
CLOUD = (255, 255, 255)


def gradient(size: int) -> Image.Image:
    """Diagonálny gradient ako CSS linear-gradient(135deg, from, to)."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    denom = 2 * (size - 1)
    for y in range(size):
        for x in range(size):
            t = (x + y) / denom
            px[x, y] = tuple(
                round(a + (b - a) * t) for a, b in zip(GRAD_FROM, GRAD_TO)
            )
    return img


def draw_art(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)

    # slnko — vpravo hore od stredu, s tenkým tmavším okrajom
    sx, sy, sr = 640, 400, 165
    d.ellipse((sx - sr - 8, sy - sr - 8, sx + sr + 8, sy + sr + 8), fill=SUN_EDGE)
    d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=SUN)

    # oblak — tri kruhy + zaoblený základ, prekrýva slnko zľava dole
    d.ellipse((250, 520, 510, 780), fill=CLOUD)          # veľký ľavý
    d.ellipse((430, 460, 660, 690), fill=CLOUD)          # stredný horný
    d.ellipse((560, 550, 760, 750), fill=CLOUD)          # pravý
    d.rounded_rectangle((300, 620, 740, 780), radius=80, fill=CLOUD)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = gradient(SIZE)
    draw_art(base)

    for name, size in [
        ("icon-192.png", 192),
        ("icon-512.png", 512),
        ("apple-touch-icon.png", 180),
    ]:
        base.resize((size, size), Image.LANCZOS).save(OUT / name)
        print(f"{name}  {size}x{size}")


if __name__ == "__main__":
    main()
