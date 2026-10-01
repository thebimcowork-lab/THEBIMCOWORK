"""Banda sonora original del reel: pad suave, notas tipo cristal y detalles de interfaz.

Lee los tiempos de .cache/cues.json (los exporta render.cjs desde reel.html) para que
cada sonido caiga exactamente con su animacion.

Uso:  python scripts/audio.py   -> .cache/audio.wav
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, lfilter

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
SR = 48000
BPM = 96
TARGET_RMS_DB = -19.0   # nivel medio de la mezcla (suave, bajo la voz de la plataforma)
EIGHTH = 60 / BPM / 2
_NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8,
         "A": 9, "A#": 10, "B": 11}


def freq(name: str) -> float:
    midi = 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n: int, attack: float, release: float, decay: float | None = None) -> np.ndarray:
    t = np.arange(n) / SR
    e = np.ones(n)
    a = max(1, min(n, int(attack * SR)))
    e[:a] = np.linspace(0, 1, a) ** 2
    if decay:
        e *= np.exp(-t / decay)
    r = max(1, min(n, int(release * SR)))
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def sine(f: float, dur: float, vol: float, attack=0.01, release=0.05, decay=None, detune=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * (1 + detune) * t) * env(n, attack, release, decay) * vol


def lowpass(x, cutoff):
    b, a = butter(2, cutoff / (SR / 2), btype="low")
    return lfilter(b, a, x)


def bandpass(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)


class Bus:
    def __init__(self, seconds: float):
        self.x = np.zeros(int(seconds * SR) + SR)

    def add(self, at: float, s: np.ndarray, gain: float = 1.0):
        i = int(at * SR)
        j = min(len(self.x), i + len(s))
        if i < j:
            self.x[i:j] += s[: j - i] * gain


# ---------------------------------------------------------------- musica
CHORDS = {  # bajo, pad, arpegio
    "Cmaj9": ("C2", ["E3", "G3", "B3", "D4"], ["C5", "E5", "G5", "B5", "D6", "B5", "G5", "E5"]),
    "Am9": ("A1", ["C3", "E3", "G3", "B3"], ["A4", "C5", "E5", "G5", "B5", "G5", "E5", "C5"]),
    "Fmaj9": ("F1", ["A3", "C4", "E4", "G4"], ["F4", "A4", "C5", "E5", "G5", "E5", "C5", "A4"]),
    "G69": ("G1", ["B3", "D4", "E4", "A4"], ["G4", "B4", "D5", "E5", "A5", "E5", "D5", "B4"]),
}


def section(pad: Bus, pluck: Bus, bass: Bus, chord: str, t0: float, t1: float, arp=True, step=1):
    root, notes, arpeggio = CHORDS[chord]
    dur = t1 - t0
    for k, n in enumerate(notes):
        for det in (-0.0025, 0.0, 0.0025):
            pad.add(t0, sine(freq(n), dur + 0.9, 0.02, attack=0.7, release=0.9, detune=det))
    bass.add(t0, sine(freq(root), dur + 0.5, 0.16, attack=0.08, release=0.6))
    bass.add(t0, sine(freq(root) * 2, dur + 0.5, 0.05, attack=0.08, release=0.6))
    if arp:
        t, i = t0 + 0.02, 0
        while t < t1 - 0.05:
            f = freq(arpeggio[i % len(arpeggio)])
            pluck.add(t, sine(f, 0.9, 0.05, attack=0.004, release=0.2, decay=0.32)
                      + sine(f * 2, 0.9, 0.012, attack=0.004, release=0.2, decay=0.12))
            t += EIGHTH * step
            i += step


# ---------------------------------------------------------------- efectos
rng = np.random.default_rng(11)


def tick():
    n = int(0.012 * SR)
    return bandpass(rng.uniform(-1, 1, n), 2500, 9000) * env(n, 0.0005, 0.008, 0.004) * 0.35


def stamp():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f = 120 * (60 / 120) ** (t / 0.22)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.08, 0.07) * 0.5
    hit = bandpass(rng.uniform(-1, 1, n), 200, 2500) * env(n, 0.001, 0.05, 0.02) * 0.12
    return thump + hit


def swoosh(dur=0.45, gain=0.12):
    n = int(dur * SR)
    noise = rng.uniform(-1, 1, n)
    lo = bandpass(noise, 300, 1200)
    hi = bandpass(noise, 1200, 5000)
    mix = np.linspace(0, 1, n)
    shape = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return (lo * (1 - mix) + hi * mix) * shape * gain


def shimmer():
    return sum(sine(freq(n), 1.2, v, attack=0.01, release=0.4, decay=0.45)
               for n, v in (("E6", 0.018), ("B6", 0.012), ("G#6", 0.008)))


def bell():
    return sum(sine(freq("C6") * m, 2.4, v, attack=0.004, release=0.6, decay=d)
               for m, v, d in ((1, 0.05, 0.9), (2, 0.02, 0.5), (3, 0.008, 0.3), (4.2, 0.004, 0.2)))


# ---------------------------------------------------------------- mezcla
def main():
    data = json.loads((CACHE / "cues.json").read_text())
    T = data["T"]
    total = T["end"]
    pad, pluck, bass, fx = Bus(total), Bus(total), Bus(total), Bus(total)
    section(pad, pluck, bass, "Cmaj9", 0.0, T["s2"] - 0.15)
    section(pad, pluck, bass, "Am9", T["s2"] - 0.15, T["s3"] - 0.15)
    section(pad, pluck, bass, "Fmaj9", T["s3"] - 0.15, T["wipe"])
    section(pad, pluck, bass, "G69", T["wipe"], T["s4"], arp=False)
    section(pad, pluck, bass, "Cmaj9", T["s4"], total, step=2)
    for c in data["cues"]:
        k, t = c["kind"], c["t"]
        if k == "tick":
            fx.add(t, tick())
        elif k == "stamp":
            fx.add(t + 0.05, stamp())
        elif k == "swoosh":
            fx.add(t - 0.05, swoosh())
        elif k == "wipe":
            fx.add(t, swoosh(0.7, 0.16))
        elif k == "reveal":
            fx.add(t, shimmer())
        elif k == "bell":
            fx.add(t, bell())
    music = lowpass(pad.x, 2200) + lowpass(pluck.x, 5000) * 0.9 + lowpass(bass.x, 400)
    n = int(total * SR)
    mix = music[:n] * 0.85 + fx.x[:n]
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    # sonoridad media fija (suave): no depende de que efecto tenga el pico mas alto
    rms = np.sqrt(np.mean(mix ** 2)) or 1.0
    mix *= 10 ** (TARGET_RMS_DB / 20) / rms
    mix = np.tanh(mix / 0.9) * 0.9
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(str(CACHE / "audio.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    print("OK", CACHE / "audio.wav", f"{total:.2f} s")


if __name__ == "__main__":
    main()
