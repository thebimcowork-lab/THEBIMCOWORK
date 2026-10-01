"""Audio 8-bit original sintetizado (pulso, triangulo y ruido estilo NES).

Melodia, fanfarria y efectos compuestos para este short: no reproducen temas ni
sonidos de ningun juego existente.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48000
BPM = 150
BEAT = 60 / BPM

_NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8,
         "A": 9, "A#": 10, "B": 11}


def freq(name: str) -> float:
    pitch, octave = name[:-1], int(name[-1])
    midi = 12 * (octave + 1) + _NOTE[pitch]
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n: int, attack: float = 0.004, release: float = 0.04, decay: float | None = None) -> np.ndarray:
    t = np.arange(n) / SR
    env = np.ones(n)
    a = max(1, int(attack * SR))
    env[:a] = np.linspace(0, 1, a)
    if decay:
        env *= np.exp(-t / decay)
    r = min(n, max(1, int(release * SR)))
    env[-r:] *= np.linspace(1, 0, r)
    return env


def pulse(f0: float, dur: float, duty: float = 0.5, vol: float = 0.25, f1: float | None = None,
          decay: float | None = None, vibrato: float = 0.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.full(n, f0) if f1 is None else f0 * (f1 / f0) ** (t / dur)
    if vibrato:
        f = f * (1 + vibrato * np.sin(2 * np.pi * 6 * t) * np.clip(t / 0.15, 0, 1))
    phase = np.cumsum(f) / SR
    wave_ = np.where((phase % 1.0) < duty, 1.0, -1.0)
    return wave_ * _env(n, decay=decay) * vol


def triangle(f0: float, dur: float, vol: float = 0.35) -> np.ndarray:
    n = int(dur * SR)
    phase = np.cumsum(np.full(n, f0)) / SR
    tri = 4 * np.abs((phase % 1.0) - 0.5) - 1
    tri = np.round(tri * 7.5) / 7.5  # escalones de 4 bits, como el canal triangulo NES
    return tri * _env(n, release=0.02) * vol


def noise(dur: float, vol: float = 0.2, decay: float = 0.05, hold: int = 6, seed: int = 7) -> np.ndarray:
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    steps = rng.choice([-1.0, 1.0], size=n // hold + 1)
    return np.repeat(steps, hold)[:n] * _env(n, attack=0.001, release=0.01, decay=decay) * vol


class Track:
    def __init__(self, seconds: float):
        self.buf = np.zeros(int(seconds * SR) + SR)

    def add(self, at: float, sound: np.ndarray, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(self.buf):
            return
        j = min(len(self.buf), i + len(sound))
        self.buf[i:j] += sound[: j - i] * gain

    def master(self, seconds: float) -> np.ndarray:
        from scipy.signal import lfilter

        x = self.buf[: int(seconds * SR)]
        y = lfilter([1, -1], [1, -0.995], x)          # paso alto: quita DC
        z = soften(y, 6000)                            # redondea el borde del pulso
        peak = np.max(np.abs(z)) or 1.0
        return np.tanh(z / peak) / np.tanh(1.0) * 0.8


def soften(buf: np.ndarray, cutoff: float) -> np.ndarray:
    """Paso bajo de un polo: quita brillo al pulso (la musica suena mas suave)."""
    from scipy.signal import lfilter

    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], buf)


def save_wav(path: Path, mono: np.ndarray) -> None:
    pcm = (np.clip(mono, -1, 1) * 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ---------- Musica: tema del nivel (4 compases, Do mayor, registro medio) ----------
LEAD = [  # (nota, beats)
    ("E4", .5), ("G4", .5), ("C5", 1), ("G4", .5), ("E4", .5), ("G4", 1),
    ("A4", .5), ("G4", .5), ("F4", .5), ("A4", .5), ("C5", 2),
    ("B4", .5), ("A4", .5), ("G4", .5), ("D4", .5), ("G4", 1), ("B3", 1),
    ("C4", .5), ("E4", .5), ("G4", .5), ("E4", .5), ("C4", 1), (None, 1),
]
STABS = ["G3", "A3", "B3", "G3"]          # contratiempos por compas
BASS = [["C3", "G2", "C3", "G2"], ["F2", "C3", "F2", "C3"],
        ["G2", "D3", "G2", "D3"], ["C3", "G2", "C3", "E3"]]


def level_theme(track: Track, start: float, end: float, vol: float = 1.0) -> None:
    bar = 4 * BEAT
    loop = 4 * bar
    t0 = start
    while t0 < end:
        t = t0
        for note, beats in LEAD:
            d = beats * BEAT
            if note and t < end:
                track.add(t, pulse(freq(note), d * 0.92, duty=0.5, vol=0.16 * vol, vibrato=0.004))
            t += d
        for b in range(4):
            tb = t0 + b * bar
            for k in range(4):
                tt = tb + k * BEAT
                if tt < end:
                    track.add(tt, triangle(freq(BASS[b][k]), BEAT * 0.9, vol=0.30 * vol))
                    track.add(tt + BEAT / 2, pulse(freq(STABS[b]), BEAT * 0.22, duty=0.5, vol=0.06 * vol))
                    track.add(tt, noise(0.04, 0.022 * vol, decay=0.012, hold=4, seed=k))
                    if k in (1, 3):
                        track.add(tt, noise(0.12, 0.06 * vol, decay=0.04, hold=8, seed=3))
        t0 += loop


# ---------- Efectos ----------
def sfx_jump() -> np.ndarray:
    return np.concatenate([pulse(220, 0.17, duty=0.5, vol=0.28, f1=700),
                           pulse(700, 0.06, duty=0.5, vol=0.16, decay=0.03)])


def sfx_bump() -> np.ndarray:
    tone = pulse(170, 0.10, duty=0.5, vol=0.36, f1=85)
    hit = noise(0.07, 0.25, decay=0.025, hold=10, seed=1)
    out = np.zeros(max(len(tone), len(hit)))
    out[:len(tone)] += tone
    out[:len(hit)] += hit
    return out


def sfx_powerup() -> np.ndarray:
    seq = ["C4", "E4", "G4", "C5", "E5", "G5", "C6", "G4", "B4", "D5", "G5", "B5", "D6"]
    parts = [pulse(freq(n), 0.045, duty=0.25, vol=0.2) for n in seq]
    return np.concatenate(parts + [pulse(freq("G6"), 0.22, duty=0.25, vol=0.12, decay=0.08)])


def sfx_ding() -> np.ndarray:
    return np.concatenate([pulse(freq("E5"), 0.06, duty=0.5, vol=0.18),
                           pulse(freq("A5"), 0.38, duty=0.5, vol=0.18, decay=0.12)])


def sfx_twinkle(seed: int = 0) -> np.ndarray:
    n = ["C6", "E6", "G6", "D6"][seed % 4]
    return pulse(freq(n), 0.09, duty=0.25, vol=0.07, decay=0.03)


def sfx_iris() -> np.ndarray:
    return pulse(800, 0.5, duty=0.5, vol=0.14, f1=100)


def sfx_blip() -> np.ndarray:
    return pulse(freq("C6"), 0.04, duty=0.5, vol=0.12)


FANFARE_S = 16 * BEAT / 4  # duracion de la fanfarria (16 semicorcheas)


def window(buf: np.ndarray, start: float, end: float, fade_in: float = 0.03,
           fade_out: float = 0.05) -> np.ndarray:
    """Recorta un bus a [start, end] con rampas, para que nada suene fuera de su tramo."""
    env = np.zeros(len(buf))
    a, b = int(start * SR), min(len(buf), int(end * SR))
    env[a:b] = 1.0
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    env[a:a + fi] = np.linspace(0, 1, fi)
    env[max(a, b - fo):b] = np.linspace(1, 0, b - max(a, b - fo))
    return buf * env


def fanfare(track: Track, at: float) -> None:
    s = BEAT / 4  # semicorchea
    lead = [("C4", 1), ("E4", 1), ("G4", 1), ("C5", 3), (None, 1), ("B4", 1), ("C5", 8)]
    t = at
    for note, units in lead:
        d = units * s
        if note:
            track.add(t, pulse(freq(note), d * 0.95, duty=0.5, vol=0.2, vibrato=0.006 if units > 4 else 0))
        t += d
    for note, off, units in (("E3", 3, 3), ("G3", 3, 3), ("G3", 8, 8), ("E4", 8, 8)):
        track.add(at + off * s, pulse(freq(note), units * s * 0.95, duty=0.5, vol=0.07))
    for note, off, units in (("C3", 0, 3), ("C3", 3, 4), ("G2", 7, 1), ("C3", 8, 8)):
        track.add(at + off * s, triangle(freq(note), units * s * 0.95, vol=0.32))
    for off in (0, 3, 8):
        track.add(at + off * s, noise(0.12, 0.09, decay=0.04, hold=5, seed=off))
