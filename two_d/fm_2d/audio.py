"""Procedural SFX + ambient music bed for 2D scenes (numpy, 48 kHz stereo).

All sounds are synthesized here (no third-party samples, no licence issues).
"""
from __future__ import annotations

import math
import wave

import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * curve / max(d, 1e-4))
    return e


def lowpass(x, cutoff):
    # one-pole, run forward + backward for zero phase
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for _ in range(2):
        acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc
            y[i] = acc
        x = y[::-1].copy()
    return x


def lp_fast(x, cutoff):
    """FFT brickwall-ish lowpass with soft rolloff (fast for long signals)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def hp_fast(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 - 1 / (1 + (f / max(cutoff, 1)) ** 4)
    return np.fft.irfft(X, len(x))


rng = np.random.default_rng(42)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


# ---------------------------------------------------------------- sounds
def whoosh(dur=0.6, lo=300, hi=3000, up=True):
    n = noise(dur)
    t = _t(dur)
    shape = np.sin(np.pi * t / dur) ** 2
    out = np.zeros_like(n)
    steps = 12
    for k in range(steps):
        seg = slice(int(k * len(n) / steps), int((k + 1) * len(n) / steps))
        fr = k / (steps - 1)
        c = lo + (hi - lo) * (fr if up else 1 - fr)
        out[seg] = lp_fast(n, c)[seg]
    return hp_fast(out, 120) * shape * 0.5


def page_flip():
    d = 0.28
    return hp_fast(lp_fast(noise(d), 5000), 900) * env(int(d * SR), 0.03, 0.12, 3) * 0.35


def pop(freq=660, dur=0.18, bend=1.6):
    t = _t(dur)
    f = freq * (1 + (bend - 1) * np.minimum(1, t / 0.05))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(t), 0.003, 0.08, 4) * 0.35


def chime(freq=880, dur=1.6, amp=0.25):
    t = _t(dur)
    s = sum(np.sin(2 * np.pi * freq * r * t) * g for r, g in ((1, 1), (2.76, 0.4), (5.4, 0.2), (8.93, 0.08)))
    return s * env(len(t), 0.002, dur * 0.5, 3) * amp


def thud(freq=55, dur=0.9, amp=0.9):
    t = _t(dur)
    f = freq * (1 + 1.5 * np.exp(-t * 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.35, 3)
    click = hp_fast(noise(dur), 2000) * env(len(t), 0.001, 0.01, 6) * 0.4
    return (body + click) * amp


def clack(dur=0.25, amp=0.5):
    t = _t(dur)
    s = (np.sin(2 * np.pi * 820 * t) + 0.6 * np.sin(2 * np.pi * 1350 * t)) * env(len(t), 0.001, 0.04, 5)
    s += hp_fast(noise(dur), 1500) * env(len(t), 0.001, 0.01, 6) * 0.5
    return s * amp


def ping(freq=2400, dur=0.6, amp=0.3):
    t = _t(dur)
    s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.31 * t)
    return s * env(len(t), 0.001, 0.25, 4) * amp


def shatter(dur=1.0, amp=0.7):
    t = _t(dur)
    s = hp_fast(noise(dur), 2500) * env(len(t), 0.001, 0.25, 4) * 0.6
    for k in range(14):
        st = int(rng.uniform(0, 0.35) * SR)
        f = rng.uniform(2500, 7000)
        L = int(0.25 * SR)
        tt = np.arange(L) / SR
        tone = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 28) * rng.uniform(0.15, 0.35)
        s[st:st + L] += tone[: max(0, min(L, len(s) - st))]
    s += thud(90, dur, 0.4)[: len(s)]
    return s * amp


def servo(dur=1.0, amp=0.12):
    t = _t(dur)
    f = 180 + 60 * np.sin(2 * np.pi * 7 * t) + 40 * t / dur
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    s = lp_fast(saw, 1600) * np.minimum(1, np.minimum(t / 0.08, (dur - t) / 0.1))
    return s * amp


def boing(dur=0.5, amp=0.35):
    t = _t(dur)
    f = 300 + 500 * (1 - np.exp(-t * 10)) + 30 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.004, 0.25, 3) * amp


def unlock():
    c = clack(0.2, 0.45)
    c2 = np.concatenate([np.zeros(int(0.07 * SR)), clack(0.2, 0.35)])
    out = np.zeros(int(1.8 * SR))
    out[: len(c)] += c
    out[: len(c2)] += c2
    ch = chime(1046, 1.6, 0.18) + chime(1568, 1.6, 0.12)
    out[int(0.1 * SR): int(0.1 * SR) + len(ch)] += ch[: len(out) - int(0.1 * SR)]
    return out


def shimmer(dur=1.6, amp=0.08):
    t = _t(dur)
    s = np.zeros_like(t)
    for f in (2093, 2637, 3136, 3951):
        s += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(5, 11) * t))
    return s * np.sin(np.pi * t / dur) * amp


def rumble(dur=3.0, amp=0.35):
    t = _t(dur)
    s = lp_fast(noise(dur), 140) * 3
    return s * np.sin(np.pi * t / dur) ** 1.5 * amp


def ticks(dur=0.8, n=18, amp=0.18):
    out = np.zeros(int(dur * SR))
    for k in range(n):
        st = int(dur * SR * (1 - (1 - k / n) ** 1.6))
        c = clack(0.05, amp)
        out[st: st + len(c)] += c[: len(out) - st]
    return out


def pad(dur, chords, amp=0.06):
    """Warm ambient pad: detuned saws -> lowpass, slow attack per chord."""
    out = np.zeros(int(dur * SR))
    seg = dur / len(chords)
    for i, ch in enumerate(chords):
        st = int(i * seg * SR)
        L = int((seg + 1.5) * SR)
        t = np.arange(L) / SR
        s = np.zeros(L)
        for midi in ch:
            f = 440 * 2 ** ((midi - 69) / 12)
            for det in (-0.12, 0.0, 0.11):
                ph = 2 * np.pi * f * (1 + det / 100) * t + rng.uniform(0, 6)
                s += (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.3 + np.sin(ph) * 0.7
        s = lp_fast(s, 900)
        e = np.minimum(1, t / 1.2) * np.minimum(1, np.maximum(0, (L / SR - t) / 1.5))
        end = min(len(out), st + L)
        out[st:end] += (s * e)[: end - st]
    return out / max(1e-9, np.abs(out).max()) * amp


# ---------------------------------------------------------------- mixing
class Mix:
    def __init__(self, dur):
        self.L = np.zeros(int(dur * SR))
        self.R = np.zeros(int(dur * SR))

    def add(self, t0, sig, gain=1.0, pan=0.0):
        st = int(t0 * SR)
        if st >= len(self.L):
            return
        if st < 0:
            sig = sig[-st:]
            st = 0
        n = min(len(sig), len(self.L) - st)
        gl = gain * math.cos((pan + 1) * math.pi / 4) * math.sqrt(2)
        gr = gain * math.sin((pan + 1) * math.pi / 4) * math.sqrt(2)
        self.L[st:st + n] += sig[:n] * gl
        self.R[st:st + n] += sig[:n] * gr

    def stereo(self):
        return np.stack([self.L, self.R], axis=1)


def read_wav(path):
    with wave.open(str(path)) as w:
        n = w.getnframes()
        ch = w.getnchannels()
        assert w.getframerate() == SR, "voice must be resampled to 48 kHz"
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    return a.reshape(-1, ch)


def write_wav(path, st):
    st = np.clip(st, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
