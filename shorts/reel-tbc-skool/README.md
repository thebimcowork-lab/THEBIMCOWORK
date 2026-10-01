# Reel · Ya abrimos nuestra Skool

Estilo 2. El mismo mensaje del short de Claudito, esta vez con la estética editorial de The BIM Co-Work: crema, negro y magenta, Inter 900, tarjetas con sombra dura, eyebrows numerados y cierre en negro, como en las miniaturas y las PPT.
9:16 · 1080×1920 · 30 fps · 15,9 s · H.264 + AAC.

→ Entrega: [`final/reel-ya-abrimos-nuestra-skool.mp4`](final/reel-ya-abrimos-nuestra-skool.mp4) · portadas: [`final/portada-anuncio.png`](final/portada-anuncio.png) · [`final/portada-cierre.png`](final/portada-cierre.png)

## Guion

| Lámina | Tiempo | Contenido |
|---|---|---|
| 01 · Anuncio | 0,0 – 3,9 s | `Ya abrimos nuestra` + logo Skool + filete magenta. |
| 02 · Bienvenida | 3,9 – 7,8 s | `Bienvenidos.` + tarjeta THE BIM CO-WORK × skool · `Formación BIM + IA → ahora en Skool`. |
| 03 · En marcha | 7,8 – 11,3 s | `Ya estamos listos.` + axonometría del taller animada en Higgsfield (`AXO · 01`). |
| Cierre | 11,3 – 15,9 s | Barrido a negro · barra magenta · `Vamos con todo.` · sello TBC × skool · `→ thebimcowork.cl`. |

Detalles de lámina, como en las PPT: sello TBC y contador `01 / 04` en la cabecera, filetes, marcas de registro `+` y un pie en mono.

## Cómo se hizo

1. **Axonometría animada en Higgsfield**: se toma la portada del taller (`assets/axo-taller.webp`), se ajusta a 16:9 y se anima con Kling 3.0 Pro (5 s, sin audio, solo fotograma inicial). El resultado es un acercamiento lento con leve giro.
   - Job `53c74547-8a3b-4f8a-ad06-6c0083dbd3b9` · media `a2d5b76e-6c6c-4262-8167-c6faff284d38` · 8,75 créditos.
   - El reel final también quedó en la biblioteca de Higgsfield: media `2575ca8d-49df-4b11-ba53-9ba16fd038ca`.
2. **Láminas** en HTML/CSS con las tipografías reales (Inter y JetBrains Mono): `scripts/reel.html`.
3. **Render** cuadro a cuadro en Chromium con Playwright (`scripts/render.cjs`). La línea de tiempo vive en `reel.html` y se exporta a `cues.json` para el audio.
4. **Audio original** (`scripts/audio.py`):
   - pad suave Cmaj9 → Am9 → Fmaj9 → G6/9 → Cmaj9
   - notas tipo cristal
   - ticks, golpe de tarjeta, barrido y campana final, sincronizados con la animación

**Prompt Kling:** *Slow, elegant cinematic camera move around a black-and-white architectural axonometric drawing of a timber house on stilts: hidden-line render with thin black lines and soft grey shadows on a pure white background. The camera glides smoothly a few degrees to the right with a gentle push-in, revealing subtle depth and parallax of the volumes. The drawing keeps its exact geometry; lines stay crisp, thin and technical. No color, no text, no people, no new objects, no flicker. Minimal, calm, premium architectural presentation.*

## Regenerar

```bash
pip install numpy scipy        # Node 18+ con Playwright y Chromium, y ffmpeg
python scripts/make_reel.py    # descarga fuentes y clip, renderiza, mezcla y exporta final/
```

Para cambiar textos, edita las secciones de `scripts/reel.html`. Para cambiar tiempos, edita el objeto `T` del mismo archivo; el audio se ajusta solo.

## Fuentes y marcas

- **Tipografías**: Inter y JetBrains Mono (SIL Open Font License), descargadas de Google Fonts al construir.
- **Logo The BIM Co-Work** y **axonometría**: assets de la marca (Drive).
- **Logo Skool**: wordmark tomado de skool.com, uso referencial.
