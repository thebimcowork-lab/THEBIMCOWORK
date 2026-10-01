"""Genera los fotogramas clave 1080x1920 que guian a Kling 3.0 en Higgsfield.

K0  Claudito a la izquierda, bloque-logo TBC flotando al centro.
K1  Impacto: Claudito en el aire golpea el bloque desde abajo (bloque levantado).
K2  El logo Skool ya salio sobre el bloque; Claudito celebra en el suelo.
K3  Igual que K2 pero sin logo ni destellos: guia del clip "cae y celebra"; el logo
    Skool se compone despues, nitido, en assemble.py.

Uso:  python scripts/keyframes.py
"""
from __future__ import annotations

from PIL import Image

from common import (BLOCK, BUMP, CLAWD, CLAWD_UP, GROUND_Y, GOLD, ROOT, SCALE, SPRITE_H,
                    SPRITE_W, W, claudito, skool_logo, sparkle, tbc_logo, upscale, world)

OUT = ROOT / "keyframes"
BX, BY, BW, BH = BLOCK
CLAUDITO_START_X = 8
CLAUDITO_HIT_X = BX + BW // 2 - SPRITE_W // 2


def frame(claudito_xy, pose=CLAWD, bump=0, skool=False) -> Image.Image:
    c = world()
    if skool:
        for x, y, big in ((20, 112, True), (162, 100, True), (34, 150, False),
                          (150, 146, False), (60, 88, False), (124, 84, False)):
            sparkle(c, x, y, big, color=(252, 252, 252) if big else GOLD)
    img = upscale(Image.fromarray(c, "RGB")).convert("RGBA")
    if skool:
        logo = skool_logo(660)
        img.alpha_composite(logo, ((W - logo.width) // 2, (BY - 10) * SCALE - logo.height))
    block = tbc_logo(BW * SCALE)
    img.alpha_composite(block, (BX * SCALE, (BY - bump) * SCALE))
    sprite = upscale(claudito(pose))
    img.alpha_composite(sprite, (claudito_xy[0] * SCALE, claudito_xy[1] * SCALE))
    return img.convert("RGB")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    standing_y = GROUND_Y - SPRITE_H
    k0 = frame((CLAUDITO_START_X, standing_y))
    k1 = frame((CLAUDITO_HIT_X, BY - BUMP + BH), bump=BUMP)
    k2 = frame((CLAUDITO_HIT_X, standing_y), pose=CLAWD_UP, skool=True)
    k3 = frame((CLAUDITO_HIT_X, standing_y), pose=CLAWD_UP)
    for name, im in (("K0_inicio", k0), ("K1_golpe", k1), ("K2_skool", k2),
                     ("K3_celebra", k3)):
        im.save(OUT / f"{name}.png", optimize=True)
        print(OUT / f"{name}.png", im.size)


if __name__ == "__main__":
    main()
