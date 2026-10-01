"""Construye el reel completo.

1. Descarga tipografias (Inter, JetBrains Mono) y los clips de Kling si faltan.
2. Extrae a 30 fps los cuadros de los renders animados (terraza y fachada).
3. Renderiza reel.html cuadro a cuadro (render.cjs) y compone la banda sonora (audio.py).
4. Une video + audio en final/ y guarda la portada.

Uso:  python scripts/make_reel.py               (todo)
      python scripts/make_reel.py --audio-only  (reusa .cache/video.mp4 y solo re-mezcla)
"""
from __future__ import annotations

import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
FINAL = ROOT / "final"
OUT = FINAL / "reel-ya-abrimos-nuestra-skool.mp4"
# Renders del estudio animados con Kling 3.0 en Higgsfield (jobs 2496d20f-... y 42875ac7-...)
CLIPS = {
    "terraza": "https://d8j0ntlcm91z4.cloudfront.net/user_3CxhhuSnYKFG2GMytDLMnzLm9ri/"
               "hf_20261001_225154_2496d20f-db53-4312-aaaa-ad90fcaed0ce.mp4",
    "fachada": "https://d8j0ntlcm91z4.cloudfront.net/user_3CxhhuSnYKFG2GMytDLMnzLm9ri/"
               "hf_20261001_225537_42875ac7-a895-4efb-8935-cac335f4fd73.mp4",
}
FONTS = {"Inter": "400,500,600,700,800,900", "JetBrains+Mono": "400,500,700"}


def run(*cmd):
    print("$", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT)


def fetch_fonts():
    folder = CACHE / "fonts"
    folder.mkdir(parents=True, exist_ok=True)
    for family, weights in FONTS.items():
        req = urllib.request.Request(f"https://fonts.googleapis.com/css?family={family}:{weights}",
                                     headers={"User-Agent": "Mozilla/4.0"})
        css = urllib.request.urlopen(req, timeout=30).read().decode()
        for block in re.findall(r"@font-face\s*{[^}]*}", css):
            name = re.search(r"font-family:\s*'([^']+)'", block).group(1).replace(" ", "")
            weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
            path = folder / f"{name}-{weight}.ttf"
            if not path.exists():
                url = re.search(r"url\((https://[^)]+)\)", block).group(1)
                path.write_bytes(urllib.request.urlopen(url, timeout=60).read())


def fetch_clips():
    for name, url in CLIPS.items():
        clip = CACHE / "clips" / f"{name}_kling.mp4"
        if not clip.exists():
            clip.parent.mkdir(parents=True, exist_ok=True)
            clip.write_bytes(urllib.request.urlopen(url, timeout=180).read())
        frames = CACHE / name
        if not frames.exists() or not any(frames.iterdir()):
            frames.mkdir(parents=True, exist_ok=True)
            run("ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", "framerate=fps=30",
                "-q:v", "2", frames / "f_%04d.jpg")


def main():
    FINAL.mkdir(exist_ok=True)
    fetch_fonts()
    fetch_clips()
    silent = CACHE / "video.mp4"
    if "--audio-only" not in sys.argv or not silent.exists():
        run("node", "scripts/render.cjs", silent)
    run(sys.executable, "scripts/audio.py")
    run("ffmpeg", "-v", "error", "-y", "-i", silent, "-i", CACHE / "audio.wav", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT)
    run("ffmpeg", "-v", "error", "-y", "-sseof", "-0.5", "-i", OUT, "-frames:v", "1",
        FINAL / "portada-cierre.png")
    run("ffmpeg", "-v", "error", "-y", "-ss", "3.0", "-i", OUT, "-frames:v", "1",
        FINAL / "portada-anuncio.png")
    print("OK", OUT)


if __name__ == "__main__":
    main()
