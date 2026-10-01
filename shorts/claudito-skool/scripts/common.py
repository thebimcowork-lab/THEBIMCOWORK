"""Piezas compartidas del short "Claudito abre la Skool".

Mundo en pixel art NES: lienzo virtual de 180x320 px escalado x6 a 1080x1920 (9:16).
Todo lo que se dibuja aqui es original: paleta tipo plataforma 8-bit, sin personajes
ni assets de Nintendo. Los logos (The BIM Co-Work y Skool) se usan tal cual.
"""
from __future__ import annotations

import io
import re
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = ROOT / ".cache"

VW, VH = 180, 320          # lienzo virtual
SCALE = 6                  # 180x320 -> 1080x1920
W, H = VW * SCALE, VH * SCALE

# Paleta del mundo (tonos NES genericos)
SKY = (92, 148, 252)
WHITE = (252, 252, 252)
BLACK = (0, 0, 0)
CLOUD_SHADE = (60, 188, 252)
HILL = (0, 168, 0)
HILL_SPOT = (0, 104, 0)
BUSH = (128, 208, 16)
PIPE = (0, 168, 0)
PIPE_LIGHT = (128, 208, 16)
BRICK = (200, 76, 12)
BRICK_LIGHT = (252, 188, 176)
GOLD = (248, 184, 0)
GOLD_LIGHT = (252, 228, 160)

# Claudito: naranja Claude + sombras
CLAUDE = (217, 119, 87)
CLAUDE_LIGHT = (240, 164, 132)
CLAUDE_DARK = (170, 82, 54)
EYE = (20, 20, 19)
OUTLINE = (44, 22, 12)

# Marca TBC
TBC_BLACK = (17, 17, 17)
TBC_PINK = (237, 27, 105)

# Geometria de la escena (coordenadas virtuales)
GROUND_Y = 256                     # primera fila de suelo
BLOCK = (68, 162, 44, 44)          # x, y, w, h del bloque-logo TBC
BUMP = 4                           # cuanto sube el bloque al golpearlo
SPRITE_W, SPRITE_H = 34, 22        # Claudito con contorno

# Claudito en "pixeles Clawd" (cada uno = 2x2 px virtuales). E = ojo.
CLAWD = [
    "..############..",
    "..############..",
    "..##E######E##..",
    "..##E######E##..",
    "################",
    "################",
    "..############..",
    "..############..",
    "...#.#....#.#...",
    "...#.#....#.#...",
]
CLAWD_UP = [  # brazos arriba (celebrando)
    "#.############.#",
    "#.############.#",
    "#.##E######E##.#",
    "#.##E######E##.#",
    "################",
    "################",
    "..############..",
    "..############..",
    "...#.#....#.#...",
    "...#.#....#.#...",
]
CLAWD_STEP = [  # paso alternado (patas cruzadas)
    "..############..",
    "..############..",
    "..##E######E##..",
    "..##E######E##..",
    "################",
    "################",
    "..############..",
    "..############..",
    "....#.#..#.#....",
    "....#.#..#.#....",
]


def claudito(pose: list[str] = CLAWD) -> Image.Image:
    """Sprite RGBA de Claudito en px virtuales (34x22 con contorno de 1 px)."""
    rows, cols = len(pose), len(pose[0])
    body = np.zeros((rows * 2, cols * 2), dtype=np.uint8)  # 0 vacio, 1 cuerpo, 2 ojo
    for r, line in enumerate(pose):
        for c, ch in enumerate(line):
            if ch != ".":
                body[r * 2:r * 2 + 2, c * 2:c * 2 + 2] = 2 if ch == "E" else 1
    h, w = body.shape
    img = np.zeros((h + 2, w + 2, 4), dtype=np.uint8)
    mask = np.zeros((h + 2, w + 2), dtype=bool)
    mask[1:-1, 1:-1] = body > 0
    # contorno: dilatacion de 1 px en cruz
    ring = np.zeros_like(mask)
    ring[1:, :] |= mask[:-1, :]
    ring[:-1, :] |= mask[1:, :]
    ring[:, 1:] |= mask[:, :-1]
    ring[:, :-1] |= mask[:, 1:]
    ring &= ~mask
    img[ring] = (*OUTLINE, 255)
    sub = img[1:-1, 1:-1]
    sub[body == 1] = (*CLAUDE, 255)
    sub[body == 2] = (*EYE, 255)
    # luz arriba y sombra abajo del cuerpo (filas 0 y 15 del cuerpo)
    top = body[0] == 1
    sub[0][top] = (*CLAUDE_LIGHT, 255)
    sub[15][body[15] == 1] = (*CLAUDE_DARK, 255)
    return Image.fromarray(img, "RGBA")


def upscale(img: Image.Image, k: int = SCALE) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def _disc_mask(w: int, h: int, discs: list[tuple[float, float, float]]) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.zeros((h, w), dtype=bool)
    for cx, cy, r in discs:
        m |= (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r
    return m


def _outline(mask: np.ndarray) -> np.ndarray:
    ring = np.zeros_like(mask)
    ring[1:, :] |= mask[:-1, :]
    ring[:-1, :] |= mask[1:, :]
    ring[:, 1:] |= mask[:, :-1]
    ring[:, :-1] |= mask[:, 1:]
    return ring & ~mask


def paint(canvas: np.ndarray, x: int, y: int, mask: np.ndarray, color) -> None:
    h, w = mask.shape
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, canvas.shape[1]), min(y + h, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    sub = mask[y0 - y:y1 - y, x0 - x:x1 - x]
    canvas[y0:y1, x0:x1][sub] = color


def cloud(canvas: np.ndarray, x: int, y: int, w: int = 40, color=WHITE, shade=CLOUD_SHADE) -> None:
    h = int(w * 0.45)
    discs = [(w * 0.22, h * 0.68, h * 0.30), (w * 0.42, h * 0.45, h * 0.42),
             (w * 0.62, h * 0.40, h * 0.38), (w * 0.80, h * 0.66, h * 0.30)]
    m = _disc_mask(w, h + 2, discs)
    m[int(h * 0.68):int(h * 0.98), int(w * 0.18):int(w * 0.84)] = True
    big = np.pad(m, 1)
    paint(canvas, x - 1, y - 1, _outline(big), BLACK)
    paint(canvas, x, y, m, color)
    shade_m = m.copy()
    shade_m[: int(h * 0.80)] = False
    paint(canvas, x, y, shade_m, shade)


def bush(canvas: np.ndarray, x: int, base: int, w: int = 34) -> None:
    h = int(w * 0.42)
    discs = [(w * 0.22, h * 0.70, h * 0.36), (w * 0.48, h * 0.52, h * 0.50),
             (w * 0.76, h * 0.70, h * 0.36)]
    m = _disc_mask(w, h, discs)
    m[int(h * 0.7):, int(w * 0.14):int(w * 0.86)] = True
    big = np.pad(m, 1)
    paint(canvas, x - 1, base - h - 1, _outline(big), BLACK)
    paint(canvas, x, base - h, m, BUSH)


def hill(canvas: np.ndarray, cx: int, base: int, w: int, h: int) -> None:
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx + 0.5 - w / 2) / (w / 2)
    ny = (h - (yy + 0.5)) / h
    m = ny <= np.clip(1.0 - nx ** 2, 0, 1) ** 0.55
    big = np.pad(m, 1)
    x = cx - w // 2
    paint(canvas, x - 1, base - h - 1, _outline(big), BLACK)
    paint(canvas, x, base - h, m, HILL)
    for sx, sy in ((0.36, 0.42), (0.58, 0.30), (0.50, 0.62)):
        spot = np.zeros((6, 4), dtype=bool)
        spot[1:5, :] = True
        spot[0, 1:3] = spot[5, 1:3] = True
        paint(canvas, x + int(w * sx), base - h + int(h * sy), spot, HILL_SPOT)


def pipe(canvas: np.ndarray, x: int, top: int, base: int, w: int = 28) -> None:
    lip_h, lip_w = 12, w + 6
    body = np.ones((base - top - lip_h, w), dtype=bool)
    lip = np.ones((lip_h, lip_w), dtype=bool)
    paint(canvas, x - 1, top + lip_h - 1, _outline(np.pad(body, 1)), BLACK)
    paint(canvas, x, top + lip_h, body, PIPE)
    paint(canvas, x - 3 - 1, top - 1, _outline(np.pad(lip, 1)), BLACK)
    paint(canvas, x - 3, top, lip, PIPE)
    for off, wid in ((4, 4), (10, 2)):
        paint(canvas, x + off, top + lip_h, np.ones((base - top - lip_h, wid), bool), PIPE_LIGHT)
        paint(canvas, x - 3 + off, top + 2, np.ones((lip_h - 4, wid), bool), PIPE_LIGHT)


BRICK_TILE = [  # 16x16: L luz, B ladrillo, D mortero
    "LLLLLLLDLLLLLLLD",
    "LBBBBBBDLBBBBBBD",
    "LBBBBBBDLBBBBBBD",
    "LBBBBBBDLBBBBBBD",
    "LBBBBBBDLBBBBBBD",
    "LBBBBBBDLBBBBBBD",
    "LBBBBBBDLBBBBBBD",
    "DDDDDDDDDDDDDDDD",
    "LLLDLLLLLLLDLLLL",
    "BBBDLBBBBBBDLBBB",
    "BBBDLBBBBBBDLBBB",
    "BBBDLBBBBBBDLBBB",
    "BBBDLBBBBBBDLBBB",
    "BBBDLBBBBBBDLBBB",
    "BBBDLBBBBBBDLBBB",
    "DDDDDDDDDDDDDDDD",
]


def ground(canvas: np.ndarray, top: int = GROUND_Y) -> None:
    lut = {"L": BRICK_LIGHT, "B": BRICK, "D": BLACK}
    tile = np.array([[lut[c] for c in row] for row in BRICK_TILE], dtype=np.uint8)
    for ty in range(top, VH, 16):
        for tx in range(0, VW, 16):
            h = min(16, VH - ty)
            w = min(16, VW - tx)
            canvas[ty:ty + h, tx:tx + w] = tile[:h, :w]


SPARKLE_BIG = ["...#...", "...#...", "..###..", "#######", "..###..", "...#...", "...#..."]
SPARKLE_SMALL = ["..#..", "..#..", "#####", "..#..", "..#.."]


def sparkle(canvas: np.ndarray, x: int, y: int, big: bool = True, color=WHITE) -> None:
    pat = SPARKLE_BIG if big else SPARKLE_SMALL
    m = np.array([[c == "#" for c in row] for row in pat])
    paint(canvas, x - m.shape[1] // 2, y - m.shape[0] // 2, m, color)


def world(include_pipe: bool = True) -> np.ndarray:
    """Fondo fijo del nivel (sin Claudito ni bloque)."""
    c = np.zeros((VH, VW, 3), dtype=np.uint8)
    c[:] = SKY
    cloud(c, 10, 62, 38)
    cloud(c, 120, 40, 46)
    hill(c, 22, GROUND_Y, 78, 34)
    hill(c, 150, GROUND_Y, 50, 20)
    bush(c, 112, GROUND_Y, 30)
    if include_pipe:
        pipe(c, 146, 214, GROUND_Y)
    ground(c)
    return c


def _trim(img: Image.Image) -> Image.Image:
    bbox = img.getchannel("A").getbbox()
    return img.crop(bbox) if bbox else img


def tbc_logo(size_px: int, pixel: int = 2) -> Image.Image:
    """Logo TBC (sello con sombra dura) ajustado a un cuadrado de size_px, en B/N pixelado."""
    logo = _trim(Image.open(ASSETS / "logo-tbc.png").convert("RGBA"))
    grid = max(1, size_px // pixel)
    small = logo.resize((grid, grid), Image.LANCZOS)
    a = np.array(small)
    alpha = a[..., 3] > 110
    lum = a[..., :3].mean(axis=2)
    out = np.zeros((grid, grid, 4), dtype=np.uint8)
    out[alpha & (lum >= 128)] = (*WHITE, 255)
    out[alpha & (lum < 128)] = (*BLACK, 255)
    return Image.fromarray(out, "RGBA").resize((grid * pixel, grid * pixel), Image.NEAREST)


def skool_logo(width_px: int, pixel: int = 3, outline_px: int = 2) -> Image.Image:
    """Wordmark Skool pixelado con borde blanco + negro para leerse sobre el cielo."""
    import cairosvg  # solo se necesita al rasterizar el SVG

    svg = (ASSETS / "skool-logo.svg").read_bytes()
    grid_w = width_px // pixel
    raw = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg, output_width=grid_w * 8)))
    raw = _trim(raw.convert("RGBA"))
    grid_h = round(raw.height * grid_w / raw.width)
    small = raw.resize((grid_w, grid_h), Image.LANCZOS)
    a = np.array(small)
    solid = a[..., 3] > 100
    pad = outline_px * 2
    out = np.zeros((grid_h + pad * 2, grid_w + pad * 2, 4), dtype=np.uint8)
    m = np.zeros(out.shape[:2], dtype=bool)
    m[pad:-pad, pad:-pad] = solid
    white_ring = m.copy()
    for _ in range(outline_px):
        white_ring |= _outline(white_ring)
    black_ring = _outline(white_ring)
    out[black_ring] = (*BLACK, 255)
    out[white_ring & ~m] = (*WHITE, 255)
    rgb = a[..., :3].copy()
    out[pad:-pad, pad:-pad][solid] = np.concatenate(
        [rgb[solid], np.full((solid.sum(), 1), 255, np.uint8)], axis=1)
    img = Image.fromarray(out, "RGBA")
    return img.resize((img.width * pixel, img.height * pixel), Image.NEAREST)


def font(size: int) -> ImageFont.FreeTypeFont:
    """Press Start 2P (SIL OFL). Se descarga de Google Fonts a .cache/ si no esta."""
    path = CACHE / "PressStart2P-Regular.ttf"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            "https://fonts.googleapis.com/css?family=Press+Start+2P",
            headers={"User-Agent": "Mozilla/4.0"})
        css = urllib.request.urlopen(req, timeout=30).read().decode()
        url = re.search(r"url\((https://fonts\.gstatic\.com[^)]+)\)", css).group(1)
        path.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    return ImageFont.truetype(str(path), size)


def text_image(text: str, size: int, color, shadow=None, shadow_off: int = 0) -> Image.Image:
    """Texto pixel nitido: se dibuja a 8 px y se escala por entero (size multiplo de 8)."""
    k = max(1, size // 8)
    f = font(8)
    l, t, r, b = f.getbbox(text)
    w, h = r - l, b - t
    off = shadow_off // k if shadow else 0
    img = Image.new("RGBA", (w + off, h + off), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        d.text((-l + off, -t + off), text, font=f, fill=(*shadow, 255))
    d.text((-l, -t), text, font=f, fill=(*color, 255))
    a = np.array(img)
    a[..., 3] = np.where(a[..., 3] > 127, 255, 0)
    return Image.fromarray(a, "RGBA").resize((img.width * k, img.height * k), Image.NEAREST)
