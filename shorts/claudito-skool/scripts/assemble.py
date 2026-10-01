"""Monta el short final: 1080x1920 @24 fps, H.264 + AAC.

Entradas (renders de Kling 3.0 en Higgsfield; se descargan solos a .cache/clips/):
  clipA_camina_salta.mp4    K0 -> K1  (camina, se agacha, salta, golpea el bloque)
  clipB2_cae_celebra.mp4    K1 -> K3  (cae, aterriza, celebra)
Encima se compone: logo Skool que sale del bloque, destellos, HUD, iris de cierre,
pantalla final y el audio chiptune.

Uso:  python scripts/assemble.py
"""
from __future__ import annotations

import json
import math
import subprocess
import urllib.request

import numpy as np
from PIL import Image

import chiptune as ct
from common import (ASSETS, BLOCK, CLAWD, CLAWD_UP, GOLD, GOLD_LIGHT, GROUND_Y, ROOT, SCALE,
                    SPARKLE_BIG, SPARKLE_SMALL, TBC_BLACK, TBC_PINK, H, W, claudito, skool_logo,
                    text_image, upscale)

FPS = 24
CLIPS = ROOT / ".cache" / "clips"
FINAL = ROOT / "final"
CLIP_A = CLIPS / "clipA_camina_salta.mp4"
CLIP_B = CLIPS / "clipB2_cae_celebra.mp4"
OUT = FINAL / "claudito-abre-la-skool.mp4"
# Resultados de Kling 3.0 en Higgsfield (jobs d8d418af-... y 6cf60d98-...)
CLIP_URLS = {
    CLIP_A: "https://d8j0ntlcm91z4.cloudfront.net/user_3CxhhuSnYKFG2GMytDLMnzLm9ri/"
            "hf_20261001_184135_d8d418af-2394-4a2e-b3f5-1c060237551a.mp4",
    CLIP_B: "https://d8j0ntlcm91z4.cloudfront.net/user_3CxhhuSnYKFG2GMytDLMnzLm9ri/"
            "hf_20261001_204052_6cf60d98-cfc0-4c7f-b9d6-42d680e53c5a.mp4",
}


def fetch_clips() -> None:
    CLIPS.mkdir(parents=True, exist_ok=True)
    for path, url in CLIP_URLS.items():
        if not path.exists():
            print("descargando", path.name)
            path.write_bytes(urllib.request.urlopen(url, timeout=120).read())

WHITE = (252, 252, 252)
CARD_BG = TBC_BLACK
BX, BY, BW, BH = BLOCK
BLOCK_TOP = BY * SCALE
LOGO_W = 660

HOLD_S = 0.45      # pausa con el logo flotando antes del iris
STABLE_REF = 40    # frame del clip B con el bloque en reposo
STABLE_FROM = 50   # desde aqui Kling hace oscilar el bloque: se fija con el de STABLE_REF
PATCH = (378, 880, 712, 1340)  # x0, y0, x1, y1 del parche del bloque (px reales)
IRIS_S = 0.6
BLACK_S = 0.2
CARD_S = 6.5
POP_S = 0.45


# ---------------------------------------------------------------- lectura de video
def frames(path, size=None):
    w, h = size or (W, H)
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)]
    if size:
        cmd += ["-vf", f"scale={w}:{h}:flags=area"]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = w * h * 3
    try:
        while True:
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()


# ---------------------------------------------------------------- analisis (a 1/4)
Q = 4
GROUND_Q = GROUND_Y * SCALE // Q


def claudito_box(f):
    r, g, b = (f[..., i].astype(int) for i in range(3))
    m = (r > 165) & (g > 65) & (g < 170) & (b > 40) & (b < 145) & (r - g > 45) & (r - b > 65)
    m[GROUND_Q:, :] = False
    ys, xs = np.nonzero(m)
    if len(xs) < 25:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def block_top(f):
    x0, x1 = BX * SCALE // Q + 6, (BX + BW) * SCALE // Q - 6
    y0 = 150
    region = f[y0:GROUND_Q, x0:x1]
    rows = np.nonzero((region.min(axis=2) > 220).mean(axis=1) > 0.5)[0]
    return y0 + int(rows.min()) if len(rows) else None


def claudito_blue(f, box):
    """Azul medio del sprite: cae en seco cuando Kling lo oscurece al agacharse."""
    if box is None:
        return None
    x0, y0, x1, y1 = box
    sub = f[y0:y1 + 1, x0:x1 + 1].astype(int)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    m = (r > 110) & (r - g > 35) & (r - b > 50)
    return float(b[m].mean()) if m.any() else None


def track(path):
    boxes, tops, blues = [], [], []
    for f in frames(path, (W // Q, H // Q)):
        bx = claudito_box(f)
        boxes.append(bx)
        tops.append(block_top(f))
        blues.append(claudito_blue(f, bx))
    return boxes, tops, blues


def analyze():
    a_boxes, a_tops, a_blues = track(CLIP_A)
    b_boxes, b_tops, _ = track(CLIP_B)
    rest = int(np.median([t for t in a_tops[:24] if t is not None]))
    # golpe: primer frame (pasado el primer segundo) con el bloque levantado
    hit = next(i for i in range(FPS, len(a_tops)) if a_tops[i] is not None and a_tops[i] <= rest - 3)
    on_ground = [bx is not None and bx[3] >= GROUND_Q - 3 for bx in a_boxes]
    takeoff = max(i for i in range(hit) if on_ground[i]) + 1
    # quietud antes de agacharse: centro x sin cambios
    cx = [None if bx is None else (bx[0] + bx[2]) / 2 for bx in a_boxes]
    hgt = [None if bx is None else bx[3] - bx[1] for bx in a_boxes]
    still = [i for i in range(1, takeoff)
             if cx[i] is not None and cx[i - 1] is not None and abs(cx[i] - cx[i - 1]) <= 0.5
             and abs(hgt[i] - hgt[i - 1]) <= 1 and on_ground[i]]
    run, best = [], []
    for i in still:
        run = run + [i] if run and i == run[-1] + 1 else [i]
        if len(run) > len(best):
            best = run[:]
    trim = []
    if len(best) > 12:
        calm = np.median([a_blues[i] for i in best[:8]])
        onset = next((i for i in range(best[0], takeoff)
                      if a_blues[i] is not None and a_blues[i] < calm - 15), best[-1] + 1)
        trim = list(range(best[0] + 8, onset - 1))  # deja 8 frames quieto + 2 antes de agacharse
    b_top_min = min(bx[1] for bx in b_boxes[STABLE_FROM:] if bx is not None)
    # clip B: primer frame en que Claudito empieza a caer
    top0 = b_boxes[0][1]
    move = next((i for i, bx in enumerate(b_boxes) if bx is not None and bx[1] > top0 + 2), 0)
    return {
        "a_frames": len(a_boxes), "b_frames": len(b_boxes), "block_rest_q": rest,
        "hit": hit, "takeoff": takeoff, "still_run": [best[0], best[-1]] if best else None,
        "trim_a": [trim[0], trim[-1]] if trim else None, "b_move": move,
        "b_last_box_q": b_boxes[-1], "b_claudito_top_min_q": b_top_min, "b_block_tops_q": b_tops,
    }


# ---------------------------------------------------------------- graficos
def pattern(pat, color, k=SCALE):
    m = np.array([[c == "#" for c in row] for row in pat])
    a = np.zeros((*m.shape, 4), np.uint8)
    a[m] = (*color, 255)
    return Image.fromarray(a, "RGBA").resize((m.shape[1] * k, m.shape[0] * k), Image.NEAREST)


STAR_BIG_W, STAR_BIG_G = pattern(SPARKLE_BIG, WHITE), pattern(SPARKLE_BIG, GOLD)
STAR_SM_W, STAR_SM_G = pattern(SPARKLE_SMALL, WHITE), pattern(SPARKLE_SMALL, GOLD)
COIN = [".####.", "##..##", "#.##.#", "#.##.#", "#.##.#", "#.##.#", "##..##", ".####."]


def coin_icon(k=4):
    m = np.array([[c != "." for c in row] for row in COIN])
    inner = np.array([[c == "." for c in row] for row in COIN]) & ~np.array(
        [[c == "." and (j in (0, 5)) for j, c in enumerate(row)] for row in COIN])
    a = np.zeros((*m.shape, 4), np.uint8)
    a[m] = (*GOLD, 255)
    a[inner & ~m] = (*GOLD_LIGHT, 255)
    return Image.fromarray(a, "RGBA").resize((6 * k, 8 * k), Image.NEAREST)


def paste(base: Image.Image, over: Image.Image, x: int, y: int) -> None:
    x, y = int(x), int(y)
    l, t = max(0, -x), max(0, -y)
    r, b = min(over.width, base.width - x), min(over.height, base.height - y)
    if r <= l or b <= t:
        return
    base.alpha_composite(over.crop((l, t, r, b)), (x + l, y + t))


def snap(v, k=3):
    return int(round(v / k) * k)


def ease_out_back(p, s=1.9):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


_txt = {}


def txt(s, size, color=WHITE, shadow=None):
    key = (s, size, color, shadow)
    if key not in _txt:
        _txt[key] = text_image(s, size, color, shadow=shadow, shadow_off=size // 8 if shadow else 0)
    return _txt[key]


# ---------------------------------------------------------------- HUD estilo 8-bit
_hud = {}
COIN_HUD = coin_icon()


def hud(score: int, coins: int, time_left: int) -> Image.Image:
    key = (score, coins, time_left)
    if key not in _hud:
        im = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        sh = (0, 0, 0)
        for s, x, y in (("CLAUDITO", 60, 150), (f"{score:06d}", 60, 194), ("MUNDO", 600, 150),
                        ("1-1", 632, 194), ("TIEMPO", 820, 150), (f"{time_left:03d}", 868, 194)):
            paste(im, txt(s, 32, WHITE, sh), x, y)
        paste(im, COIN_HUD, 380, 190)
        paste(im, txt(f"×{coins:02d}", 32, WHITE, sh), 412, 194)
        _hud[key] = im
    return _hud[key]


# ---------------------------------------------------------------- logo Skool y destellos
SKOOL = skool_logo(LOGO_W)
SKOOL_X = (W - SKOOL.width) // 2
SKOOL_Y = (BY - 10) * SCALE - SKOOL.height
TWINKLES = [(123, 675, 0.0, True), (975, 603, 0.33, True), (207, 903, 0.6, False),
            (903, 879, 0.15, False), (363, 531, 0.45, False), (747, 507, 0.8, False)]
rng = np.random.default_rng(4)
BURST = [(math.radians(a), d) for a, d in zip(np.linspace(-170, -10, 9) + rng.uniform(-8, 8, 9),
                                              rng.uniform(260, 420, 9))]


def draw_skool(base: Image.Image, dt: float, block_top: int = BLOCK_TOP) -> None:
    """dt = segundos desde que el logo empieza a salir del bloque.

    Mientras sale, el bloque queda delante: se borra lo que cae dentro de su rectangulo.
    """
    if dt < 0:
        return
    if dt < 0.6:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        _draw_skool(layer, dt)
        a = np.array(layer)
        a[block_top:(BY + BH) * SCALE + 12, BX * SCALE - 6:(BX + BW) * SCALE + 12, 3] = 0
        base.alpha_composite(Image.fromarray(a, "RGBA"))
    else:
        _draw_skool(base, dt)


def _draw_skool(base: Image.Image, dt: float) -> None:
    p = min(1.0, dt / POP_S)
    s = 0.18 + 0.82 * ease_out_back(p)
    w, h = max(3, snap(SKOOL.width * s)), max(3, snap(SKOOL.height * s))
    cy0 = BLOCK_TOP - 0.18 * SKOOL.height / 2
    cy1 = SKOOL_Y + SKOOL.height / 2
    cy = cy0 + (cy1 - cy0) * ease_out_cubic(p)
    if p >= 1:
        cy += 6 * math.sin(2 * math.pi * (dt - POP_S) / 1.3)
    img = SKOOL if (w, h) == SKOOL.size else SKOOL.resize((w, h), Image.NEAREST)
    paste(base, img, snap(W / 2 - w / 2), snap(cy - h / 2))
    # estallido de destellos al salir
    if dt < 0.6:
        q = ease_out_cubic(dt / 0.6)
        for k, (ang, dist) in enumerate(BURST):
            x = W / 2 + math.cos(ang) * dist * q
            y = BLOCK_TOP - 20 + math.sin(ang) * dist * q
            star = (STAR_BIG_W if k % 2 else STAR_BIG_G) if dt < 0.3 else (STAR_SM_W if k % 2 else STAR_SM_G)
            paste(base, star, snap(x - star.width / 2, 6), snap(y - star.height / 2, 6))
    # destellos que titilan alrededor
    if p >= 1:
        for x, y, ph, big in TWINKLES:
            phase = ((dt - POP_S) / 0.9 + ph) % 1.0
            if phase < 0.55:
                star = (STAR_BIG_W if big else STAR_SM_G) if phase < 0.3 else STAR_SM_W
                paste(base, star, x - star.width // 2, y - star.height // 2)


def feather(w, h, edge=18):
    ramp_x = np.clip(np.minimum(np.arange(w), np.arange(w)[::-1]) / edge, 0, 1)
    ramp_y = np.clip(np.minimum(np.arange(h), np.arange(h)[::-1]) / edge, 0, 1)
    return (ramp_y[:, None] * ramp_x[None, :])[..., None]


PATCH_ALPHA = feather(PATCH[2] - PATCH[0], PATCH[3] - PATCH[1])


def stabilize(frame: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Pega el bloque en reposo (de otro frame del mismo clip) con bordes difuminados."""
    x0, y0, x1, y1 = PATCH
    out = frame.copy()
    region = out[y0:y1, x0:x1].astype(np.float32)
    out[y0:y1, x0:x1] = (ref[y0:y1, x0:x1] * PATCH_ALPHA + region * (1 - PATCH_ALPHA)).astype(np.uint8)
    return out


# ---------------------------------------------------------------- iris
def iris_mask(cx, cy, radius):
    yy, xx = np.mgrid[0:H // SCALE, 0:W // SCALE]
    inside = (xx * SCALE + 3 - cx) ** 2 + (yy * SCALE + 3 - cy) ** 2 <= radius ** 2
    return np.kron(inside, np.ones((SCALE, SCALE), dtype=bool))


# ---------------------------------------------------------------- pantalla final
def crisp_tbc(width):
    logo = Image.open(ASSETS / "logo-tbc.png").convert("RGBA")
    logo = logo.crop(logo.getchannel("A").getbbox())
    return logo.resize((width, round(logo.height * width / logo.width)), Image.LANCZOS)


CARD_TBC = crisp_tbc(220)
CARD_SKOOL = skool_logo(780)
CARD_SPRITES = {False: upscale(claudito(CLAWD), 7), True: upscale(claudito(CLAWD_UP), 7)}
# Composicion vertical dentro de la zona segura de Shorts (~150-1550 px)
CARD_TBC_Y = 170
CARD_LINES = [  # texto, tamano, color, y, inicio, seg/letra
    ("ABRIMOS", 96, WHITE, 450, 0.30, 0.07),
    ("NUESTRA", 96, WHITE, 566, 0.85, 0.07),
    ("BIENVENIDOS", 72, WHITE, 1010, 2.05, 0.05),
    ("YA ESTAMOS LISTOS", 48, WHITE, 1112, 2.75, 0.045),
]
CARD_SKOOL_CY = 820
CARD_GO = "¡VAMOS CON TODO!"
CARD_GO_SIZE = 56
CARD_GO_CY = 1228
CARD_FEET_Y = 1500
CARD_SKOOL_T = 1.45
CARD_GO_T = 3.75
CARD_TWINKLES = [(110, 820, 0.1, True), (970, 780, 0.5, True), (160, 960, 0.3, False),
                 (920, 950, 0.7, False), (850, 280, 0.2, False), (230, 300, 0.6, False)]
GO_BURST = [(math.radians(a), d) for a, d in ((-15, 300), (15, 260), (-35, 220), (35, 200),
                                              (165, 260), (195, 300), (145, 200), (215, 220))]


def card_frame(tc: float) -> Image.Image:
    im = Image.new("RGBA", (W, H), (*CARD_BG, 255))
    if tc > 0.25 or int(tc * 16) % 2 == 0:
        paste(im, CARD_TBC, (W - CARD_TBC.width) // 2, CARD_TBC_Y)
    for text, size, color, y, t0, per in CARD_LINES:
        n = int((tc - t0) / per) + 1 if tc >= t0 else 0
        if n > 0:
            full = txt(text, size, color)
            part = txt(text[:min(n, len(text))], size, color)
            paste(im, part, (W - full.width) // 2, y)
    if tc >= CARD_SKOOL_T:
        p = min(1.0, (tc - CARD_SKOOL_T) / 0.35)
        s = 0.2 + 0.8 * ease_out_back(p)
        w, h = snap(CARD_SKOOL.width * s), snap(CARD_SKOOL.height * s)
        img = CARD_SKOOL if (w, h) == CARD_SKOOL.size else CARD_SKOOL.resize((max(w, 3), max(h, 3)), Image.NEAREST)
        paste(im, img, snap(W / 2 - w / 2), snap(CARD_SKOOL_CY - h / 2))
        if p >= 1:
            for x, y, ph, big in CARD_TWINKLES:
                phase = ((tc - CARD_SKOOL_T) / 1.1 + ph) % 1.0
                if phase < 0.5:
                    star = (STAR_BIG_W if big else STAR_SM_G) if phase < 0.25 else STAR_SM_W
                    paste(im, star, x - star.width // 2, y - star.height // 2)
    if tc >= CARD_GO_T:
        dt = tc - CARD_GO_T
        # cierre: "¡VAMOS CON TODO!" en magenta, entra con rebote y destellos
        go = txt(CARD_GO, CARD_GO_SIZE, TBC_PINK)
        p = min(1.0, dt / 0.3)
        s = 0.3 + 0.7 * ease_out_back(p)
        w, h = snap(go.width * s), snap(go.height * s)
        img = go if (w, h) == go.size else go.resize((max(w, 3), max(h, 3)), Image.NEAREST)
        paste(im, img, snap(W / 2 - w / 2), snap(CARD_GO_CY - h / 2))
        if p >= 1:
            star = pattern(SPARKLE_SMALL, TBC_PINK, 6)
            sy = CARD_GO_CY - star.height // 2
            paste(im, star, (W - go.width) // 2 - 54, sy)
            paste(im, star, (W + go.width) // 2 + 24, sy)
        if dt < 0.5:
            q = ease_out_cubic(dt / 0.5)
            for k, (ang, dist) in enumerate(GO_BURST):
                side = (W + go.width) / 2 if math.cos(ang) > 0 else (W - go.width) / 2
                x = side + math.cos(ang) * dist * q
                y = CARD_GO_CY + math.sin(ang) * dist * q
                st = (STAR_BIG_W if k % 2 else STAR_BIG_G) if dt < 0.25 else (STAR_SM_W if k % 2 else STAR_SM_G)
                paste(im, st, snap(x - st.width / 2, 6), snap(y - st.height / 2, 6))
        # Claudito entra desde abajo y sigue rebotando (nunca sube sobre el texto)
        if dt < 0.4:
            y = H + 40 + (CARD_FEET_Y - H - 40) * ease_out_cubic(dt / 0.4)
            up = True
        else:
            hop = abs(math.sin(math.pi * (dt - 0.4) / 0.5))
            y = CARD_FEET_Y - 56 * hop
            up = hop > 0.25
        spr = CARD_SPRITES[up]
        paste(im, spr, (W - spr.width) // 2, snap(y - spr.height, 7))
    return im


# ---------------------------------------------------------------- audio
MUSIC_GAIN = 0.42       # tema del nivel, por debajo de los efectos
MUSIC_BED_GAIN = 0.28   # base en la pantalla final
MUSIC_CUTOFF = 3200     # Hz: paso bajo que suaviza la musica


def build_audio(ev: dict, total: float, path):
    tr = ct.Track(total)
    c = ev["card"]
    fan_end = c + CARD_GO_T + ct.FANFARE_S
    # tema del nivel hasta el iris; en la pantalla final vuelve como base suave,
    # se calla durante la fanfarria y retoma desde el compas 1 al terminarla
    for start, end, gain, fade_out in ((0.0, ev["iris"] + 0.4, MUSIC_GAIN, 0.4),
                                       (c, c + CARD_GO_T - 0.02, MUSIC_BED_GAIN, 0.06),
                                       (fan_end, total, MUSIC_BED_GAIN, 0.8)):
        bus = ct.Track(total)
        ct.level_theme(bus, start, end)
        soft = ct.soften(bus.buf, MUSIC_CUTOFF)
        tr.buf += ct.window(soft, start, end, fade_out=fade_out) * gain
    tr.add(ev["jump"], ct.sfx_jump())
    tr.add(ev["hit"], ct.sfx_bump())
    tr.add(ev["pop"], ct.sfx_powerup())
    tr.add(ev["pop"] + POP_S + 0.05, ct.sfx_ding())
    k = 0
    t = ev["pop"] + POP_S + 0.3
    while t < ev["iris"]:
        tr.add(t, ct.sfx_twinkle(k))
        t += 0.3
        k += 1
    tr.add(ev["iris"], ct.sfx_iris())
    for text, _, _, _, t0, per in CARD_LINES:
        for i, ch in enumerate(text):
            if ch != " ":
                tr.add(c + t0 + i * per, ct.sfx_blip())
    tr.add(c + CARD_SKOOL_T, ct.sfx_powerup())
    ct.fanfare(tr, c + CARD_GO_T)
    tr.add(c + CARD_GO_T + 0.05, ct.sfx_jump(), 0.4)
    t, k = fan_end + 0.1, 0
    while t < total - 0.3:
        tr.add(t, ct.sfx_twinkle(k))
        t += 0.45
        k += 1
    ct.save_wav(path, tr.master(total))


# ---------------------------------------------------------------- montaje
def main():
    FINAL.mkdir(exist_ok=True)
    fetch_clips()
    info = analyze()
    print({k: v for k, v in info.items() if k != "b_block_tops_q"})
    assert info["b_claudito_top_min_q"] * Q > PATCH[3], "el parche del bloque tocaria a Claudito"
    trim = set(range(info["trim_a"][0], info["trim_a"][1] + 1)) if info["trim_a"] else set()
    seq = [("A", i) for i in range(info["hit"] + 1) if i not in trim]
    seq += [("B", i) for i in range(max(0, info["b_move"] - 1), info["b_frames"])]
    idx = {s: k for k, s in enumerate(seq)}
    t_jump = idx[("A", info["takeoff"])] / FPS
    t_hit = idx[("A", info["hit"])] / FPS
    t_cut = idx[("B", max(0, info["b_move"] - 1))] / FPS
    t_pop = t_cut + 2 / FPS
    n_hold, n_iris, n_black = round(HOLD_S * FPS), round(IRIS_S * FPS), round(BLACK_S * FPS)
    n_card = round(CARD_S * FPS)
    t_iris = (len(seq) + n_hold) / FPS
    t_card = t_iris + (n_iris + n_black) / FPS
    total_frames = len(seq) + n_hold + n_iris + n_black + n_card
    total = total_frames / FPS
    bx = info["b_last_box_q"]
    iris_c = ((bx[0] + bx[2]) / 2 * Q, (bx[1] + bx[3]) / 2 * Q)
    ev = {"jump": t_jump, "hit": t_hit, "cut": t_cut, "pop": t_pop, "iris": t_iris, "card": t_card}
    print("eventos (s):", {k: round(v, 3) for k, v in ev.items()}, "total:", round(total, 2))

    wav = ROOT / ".cache" / "audio.wav"
    build_audio(ev, total, wav)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow",
         "-crf", "14", "-tune", "animation", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", str(OUT)],
        stdin=subprocess.PIPE)

    pop_done = t_pop + POP_S

    def state(t):
        score = 1000 if t >= pop_done else 0
        coins = 1 if t >= pop_done else 0
        return score, coins, 300 - int(t / 0.4)

    b_tops = info["b_block_tops_q"]

    def platform(img: Image.Image, t: float, b_index=None) -> Image.Image:
        top_q = b_tops[b_index] if b_index is not None else None
        draw_skool(img, t - t_pop, top_q * Q - 4 if top_q else BLOCK_TOP)
        paste(img, hud(*state(t)), 0, 0)
        if pop_done <= t < pop_done + 0.7:
            q = (t - pop_done) / 0.7
            paste(img, txt("1000", 32, WHITE, (0, 0, 0)), 704, snap(1010 - 70 * ease_out_cubic(q), 4))
        return img

    sources = {"A": frames(CLIP_A), "B": frames(CLIP_B)}
    cursor = {"A": -1, "B": -1}
    last, ref = None, None
    k = 0
    for src, i in seq:
        while cursor[src] < i:
            last_raw = next(sources[src])
            cursor[src] += 1
            if src == "B" and cursor[src] == STABLE_REF:
                ref = last_raw.copy()
        if src == "B" and i >= STABLE_FROM:
            last_raw = stabilize(last_raw, ref)
        img = Image.fromarray(last_raw, "RGB").convert("RGBA")
        last, last_b = last_raw, (i if src == "B" else None)
        enc.stdin.write(np.asarray(platform(img, k / FPS, last_b).convert("RGB")).tobytes())
        k += 1
    for g in sources.values():
        g.close()
    for j in range(n_hold + n_iris):
        t = k / FPS
        img = platform(Image.fromarray(last, "RGB").convert("RGBA"), t, last_b)
        arr = np.asarray(img.convert("RGB")).copy()
        if j >= n_hold:
            p = (j - n_hold + 1) / n_iris
            radius = 1400 * (1 - p) ** 1.6
            arr[~iris_mask(*iris_c, radius)] = 0
        enc.stdin.write(arr.tobytes())
        k += 1
    black = np.zeros((H, W, 3), np.uint8).tobytes()
    for _ in range(n_black):
        enc.stdin.write(black)
        k += 1
    for j in range(n_card):
        enc.stdin.write(np.asarray(card_frame(j / FPS).convert("RGB")).tobytes())
        k += 1
    enc.stdin.close()
    enc.wait()
    card_frame(CARD_S - 0.2).convert("RGB").save(FINAL / "portada.png", optimize=True)
    (ROOT / ".cache" / "edl.json").write_text(json.dumps({"analysis": info, "events": ev,
                                                         "frames": total_frames}, indent=1))
    print("OK", OUT, f"{total_frames} frames, {total:.2f} s")


if __name__ == "__main__":
    main()
