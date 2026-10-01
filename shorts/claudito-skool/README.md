# Short · Claudito abre la Skool

YouTube Short vertical en estética de plataforma 8-bit (estilo 1).
9:16 · 1080×1920 · 24 fps · 14,7 s · H.264 + AAC.

→ Entrega: [`final/claudito-abre-la-skool.mp4`](final/claudito-abre-la-skool.mp4) · portada: [`final/portada.png`](final/portada.png)

## Guion

| # | Tiempo | Plano |
|---|---|---|
| 01 | 0,0 – 3,4 s | Claudito camina por el nivel. HUD: `CLAUDITO · ×00 · MUNDO 1-1 · TIEMPO 300`. Se agacha y salta. |
| 02 | 3,4 s | Golpea desde abajo el bloque = logo **The BIM Co-Work**. |
| 03 | 3,5 – 7,4 s | Del bloque sale el logo **Skool** con destellos · `1000` puntos · moneda `×01`. Claudito cae y celebra. |
| 04 | 7,4 – 8,2 s | Cierre en iris sobre Claudito. |
| 05 | 8,2 – 14,7 s | Pantalla final: `ABRIMOS NUESTRA` [skool] · `BIENVENIDOS` · `YA ESTAMOS LISTOS` · `✦ ¡VAMOS CON TODO! ✦`. |

## Cómo se hizo

1. **Fotogramas clave** en pixel art original (lienzo 180×320 escalado ×6) con los logos reales → `scripts/keyframes.py` → `keyframes/`.
2. **Animación en Higgsfield** · Kling 3.0 Pro · 9:16 · sin audio · fotograma inicial + final.
3. **Montaje** → `scripts/assemble.py`: recorta pausas, corta en el golpe, estabiliza el bloque, compone el logo Skool nítido saliendo desde detrás del bloque, HUD, iris y pantalla final.
4. **Audio** → `scripts/chiptune.py`: música, fanfarria y efectos 8-bit sintetizados para este short (originales). Música en registro medio, filtrada y por debajo de los efectos (ganancias `MUSIC_*` en `assemble.py`).

### Generaciones Higgsfield

| Clip | Fotogramas | Duración | Job | Estado |
|---|---|---|---|---|
| A · camina, salta, golpea | K0 → K1 | 5 s | `d8d418af-2394-4a2e-b3f5-1c060237551a` | usado |
| B · cae y celebra | K1 → K3 | 4 s | `6cf60d98-cfc0-4c7f-b9d6-42d680e53c5a` | usado |
| B (1er intento) · logo sale del bloque | K1 → K2 | 5 s | `abce57e8-b5a2-4f34-a664-228165c72af5` | descartado: Kling deformaba el logo Skool al salir |

Gasto: 8,75 + 8,75 + 7 = **24,5 créditos** (saldo 123,75 → 99,25).
Media IDs en Higgsfield: K0 `f6f133c3-…` · K1 `a86ca42a-…` · K2 `b1981ea9-…` · K3 `78d0b30a-…` · video final v2 `247cdb12-2fc0-4e14-a416-80e2d575ab04` (v1: `ec124b2e-0d7e-4253-a640-07449f21e34a`).

Por el descarte del primer clip B, el logo Skool no lo dibuja Kling: se compone en postproducción con el wordmark oficial, así sale exacto.

### Prompts (Kling 3.0)

**Clip A** — *Retro 8-bit pixel art platformer video game, 2D side view, locked static camera with no pan and no zoom. The little orange pixel creature with two black eyes, tiny side arms and four tiny legs walks to the right across the brick ground with quick bouncy little steps, stops under the floating white 'THE BIM CO-WORK' logo block, then jumps straight up and bumps its head against the bottom of the block, which pops up slightly from the hit. Classic NES game animation, crisp chunky pixels, flat colors. Sky, clouds, hills, bush and green pipe stay perfectly still. The logo block keeps its exact black-and-white design and text.*

**Clip B** — *Retro 8-bit pixel art platformer video game, 2D side view, locked static camera with no pan and no zoom. Immediately from the very first frame, the little orange pixel creature drops straight down from under the white 'THE BIM CO-WORK' logo block and lands on the brick ground with a small squash, then hops happily once and raises its tiny arms to celebrate. The logo block jiggles from the hit and settles back in its place. The sky above the block stays empty, nothing appears there. Classic NES game animation, crisp chunky pixels, flat colors. Sky, clouds, hills, bush and green pipe stay perfectly still; the logo block keeps its exact black-and-white design and text.*

## Regenerar

```bash
pip install -r requirements.txt
python scripts/keyframes.py   # K0..K3
python scripts/assemble.py    # descarga los clips de Kling y monta final/
```

Para cambiar textos, tiempos o colores de la pantalla final: constantes `CARD_*` en `scripts/assemble.py`. Volumen y brillo de la música: `MUSIC_GAIN`, `MUSIC_BED_GAIN`, `MUSIC_CUTOFF`.

## Fuentes y marcas

- **Claudito**: sprite inspirado en la mascota pixel de Claude Code.
- **Estética**: plataforma 8-bit genérica dibujada para este short; sin personajes, música ni efectos de Nintendo.
- **Logo The BIM Co-Work**: `assets/logo-tbc.png` (Drive de la marca).
- **Logo Skool**: `assets/skool-logo.svg`, wordmark tomado de skool.com, uso referencial.
- **Tipografía**: Press Start 2P (SIL Open Font License); se descarga de Google Fonts al ejecutar.
