# Reel · Ya abrimos nuestra Skool

Estilo 2. Es el mismo mensaje del short de Claudito, ahora con la estética editorial de The BIM Co-Work (crema · negro · magenta, Inter 900, eyebrows numerados, lámina tipo PPT) y **los renders del estudio como fondo**.
9:16 · 1080×1920 · 30 fps · 15,9 s · H.264 + AAC.

→ Entrega: [`final/reel-ya-abrimos-nuestra-skool.mp4`](final/reel-ya-abrimos-nuestra-skool.mp4) · portadas: [`final/portada-anuncio.png`](final/portada-anuncio.png) · [`final/portada-cierre.png`](final/portada-cierre.png)

## Guion

| Lámina | Tiempo | Fondo | Texto |
|---|---|---|---|
| 01 · Anuncio | 0,0 – 3,9 s | Axonometría de la vivienda sobre papel crema, con acercamiento lento | `Ya abrimos nuestra` + logo Skool + filete magenta |
| 02 · Bienvenida | 3,9 – 7,8 s | Render de la terraza animado en Higgsfield, con velo oscuro | `Bienvenidos.` · THE BIM CO-WORK × skool · `Formación BIM + IA → ahora en Skool` |
| 03 · En marcha | 7,8 – 11,3 s | Axonometría en corte sobre papel crema | `Ya estamos listos.` · `AXO · CORTE 01` |
| Cierre | 11,3 – 15,9 s | Barrido a negro → render de la fachada animado en Higgsfield | Barra magenta · `Vamos con todo.` · THE BIM CO-WORK × skool · `→ thebimcowork.cl` |

Detalles de lámina, como en las PPT: sello TBC y contador `01 / 04` en la cabecera, filetes, marcas de registro `+` y un pie en mono. La lámina cambia a tinta crema sobre las fotos.
Sobre fondo oscuro el wordmark Skool va en una tinta (blanco), sin caja.

## Cómo se hizo

1. **Renders animados en Higgsfield**: Kling 3.0 Pro, 9:16, 5 s, sin audio, fotograma inicial = recorte 9:16 del render.
   - Terraza (`assets/renders/terraza.png`): dolly lento. Job `2496d20f-db53-4312-aaaa-ad90fcaed0ce`.
   - Fachada (`assets/renders/fachada.png`): subida lenta con los pastos en movimiento. Job `42875ac7-a895-4efb-8935-cac335f4fd73`. Se declinó el preset de efectos que sugirió Higgsfield para mantener el render tal cual.
   - El reel final también quedó en la biblioteca de Higgsfield: media `d10527b0-a6db-4eab-8c39-4098d48ace9e`.
2. **Láminas** en HTML/CSS con las tipografías reales (Inter y JetBrains Mono): `scripts/reel.html`. Las axonometrías se multiplican sobre el crema, con opacidad baja.
3. **Render** cuadro a cuadro en Chromium con Playwright: `scripts/render.cjs`. Los cuadros de Kling se inyectan como capas.
4. **Audio original** (`scripts/audio.py`):
   - pad Cmaj9 → Am9 → Fmaj9 → G6/9 → Cmaj9
   - notas tipo cristal
   - ticks, barridos y campana final, sincronizados con la animación
   - nivel medio fijo de −19 dB (suave)

**Prompts Kling**

- *Terraza:* Slow cinematic dolly-in along a modern concrete building terrace: floor-to-ceiling glass doors, warm timber deck, cozy interior with a grey sofa and bookshelves, warm late-afternoon sunlight casting long shadows across the deck. Smooth, steady camera movement with gentle parallax; the light shifts subtly. Photorealistic architectural visualization, calm and premium. No people, no text, no new objects, the architecture keeps its exact design.
- *Fachada:* Slow cinematic upward dolly along the diagonal exposed-concrete columns of a modern residential building, ornamental grasses swaying gently in the breeze, city towers in the background, soft overcast daylight, natural muted tones. Smooth steady camera with subtle parallax. Photorealistic architectural visualization, calm and premium. No people, no text, no new objects; the architecture keeps its exact design.

## Regenerar

```bash
pip install numpy scipy          # además: Node 18+ con Playwright/Chromium y ffmpeg
python scripts/make_reel.py      # descarga fuentes y clips, renderiza, mezcla y exporta final/
python scripts/make_reel.py --audio-only   # solo re-mezcla el audio sobre el último render
```

- **Textos**: secciones de `scripts/reel.html`.
- **Tiempos**: objeto `T` en el mismo archivo; el audio se ajusta solo.
- **Fondos**: `assets/renders/` y las capas `LAYERS`.

## Fuentes y marcas

- **Renders, axonometrías y logo The BIM Co-Work**: assets del estudio (Drive).
- **Logo Skool**: wordmark tomado de skool.com, uso referencial (a color sobre claro, en una tinta sobre oscuro).
- **Tipografías**: Inter y JetBrains Mono (SIL Open Font License), descargadas de Google Fonts al construir.
