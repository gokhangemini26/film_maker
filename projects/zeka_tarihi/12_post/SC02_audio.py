"""SC02 sound: narration slice + continuous music bed slice + synced SFX -> 12_post/audio/SC02_mix_pre.wav
Times below are absolute film times; the file starts at SC02.START."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
sys.path.insert(0, str(PROJ.parents[1] / "two_d"))
sys.path.insert(0, str(HERE))
from fm_2d import audio as A  # noqa: E402
import music  # noqa: E402

spec = importlib.util.spec_from_file_location("SC02", PROJ / "10_2d" / "SC02.py")
SC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SC)
C = SC.CUE
T0, T1 = SC.START, SC.DURATION


class M(A.Mix):
    def at(self, t, sig, gain=1.0, pan=0.0):
        self.add(t - T0, sig, gain, pan)


mix = M(T1 - T0)
v = A.read_wav(PROJ / "references/voice/narration_48k.wav").mean(axis=1)
vo = v[int(T0 * A.SR): int((T1 - 0.02) * A.SR)]
vo = vo / max(1e-9, np.abs(A.read_wav(PROJ / "references/voice/narration_48k.wav")[: int(23.42 * A.SR)].mean(1)).max()) * 0.89
mix.add(0, vo, 1.0)
bed = music.slice_bed(T0, T1)
n = min(len(bed), len(mix.L))
mix.L[:n] += bed[:n, 0]
mix.R[:n] += bed[:n, 1]

# SH070
mix.at(23.75, A.whoosh(1.9, 2500, 300, False), 0.8)
mix.at(C["karmasik"], A.shimmer(1.4, 0.07), 1.0)
mix.at(C["sifir"] + 0.05, A.whoosh(0.7, 300, 5000, True), 0.7)
mix.at(C["sifir"] + 0.1, A.chime(523, 1.2, 0.10), 0.7, -0.2)
for i, f in enumerate((523, 587, 659, 784, 880)):
    mix.at(C["bes"] - 0.05 + i * 0.09, A.pop(f, 0.18, 1.3), 0.7, -0.4 + 0.2 * i)
for i in range(5):
    t = C["insa"] + i * 0.16 + 0.28
    mix.at(t, A.thud(70 + i * 8, 0.5, 0.45), 0.8)
    mix.at(t, A.clack(0.15, 0.25), 0.6)
mix.at(29.55, A.whoosh(0.7, 3000, 400, False), 0.7)
for i in range(5):
    mix.at(29.9 + i * 0.07, A.thud(90, 0.4, 0.35), 0.7, -0.6 + 0.3 * i)

# SH080 - each breakthrough
notes = (523, 587, 659, 784, 880)
for i, (sc, ab) in enumerate(zip(SC.STAGE_CUE, SC.ABIL_CUE)):
    mix.at(C[sc] - 0.1, A.pop(notes[i] / 2, 0.25, 1.6), 0.8, -0.5 + 0.25 * i)
    mix.at(C[ab] - 0.05, A.chime(notes[i], 1.1, 0.08), 0.8, -0.5 + 0.25 * i)
mix.at(C["yon"], A.whoosh(0.5, 800, 2500, True), 0.4, -0.5)
mix.at(C["deneme"], A.pop(180, 0.18, 0.7), 0.8, -0.25)       # wrong
mix.at(C["yanilma"], A.chime(1318, 0.6, 0.12), 0.8, -0.25)   # right
for j in range(4):
    mix.at(C["balik"] + 0.3 + j * 0.22, A.pop(1200 + j * 150, 0.08, 1.4), 0.3, -0.25)
mix.at(C["hayal"] + 0.1, A.shimmer(1.1, 0.06), 1.0)
mix.at(C["memeli"], A.pop(2200, 0.1, 1.25), 0.4)
mix.at(C["memeli"] + 0.12, A.pop(2400, 0.08, 1.25), 0.35)
mix.at(C["baskasi"] + 0.5, A.chime(988, 0.8, 0.10), 0.8, 0.25)
for j in range(8):
    mix.at(C["konus"] + 0.15 + j * 0.08, A.clack(0.04, 0.12), 0.6, 0.5)
mix.at(C["uzanan"] + 0.2, A.whoosh(1.4, 300, 4000, True), 0.6)
mix.at(C["harika"], A.shimmer(1.4, 0.09), 1.0)
mix.at(C["harika"] + 0.1, A.chime(1046, 1.5, 0.10) + A.chime(1318, 1.5, 0.07), 0.8)

# SH090
mix.at(42.2, A.whoosh(0.8, 300, 5000, True), 0.7)
mix.at(C["kafa"], A.shimmer(1.2, 0.06), 1.0)
for i in range(5):
    mix.at(45.0 + i * 0.32, A.chime(notes[i], 1.0, 0.09), 0.8, 0.3)
mix.at(C["canli"] - 0.3, A.whoosh(1.0, 2500, 300, False), 0.6)
mix.at(C["canli"], A.thud(110, 0.3, 0.3) + A.clack(0.3, 0.25)[: int(0.3 * A.SR)], 0.8, -0.3)
mix.at(C["canli"] + 0.18, A.thud(110, 0.3, 0.3) + A.clack(0.3, 0.25)[: int(0.3 * A.SR)], 0.8, 0.3)
mix.at(48.7, A.servo(1.0, 0.09), 0.9, 0.6)
mix.at(C["miyiz"] - 0.25, A.boing(0.5, 0.3), 0.8, 0.5)
mix.at(C["evet"] - 0.12, A.thud(60, 0.9, 0.8), 0.8)
mix.at(C["evet"] - 0.1, A.chime(784, 1.5, 0.12) + A.chime(988, 1.5, 0.09) + A.chime(1175, 1.5, 0.07), 0.9)

st = mix.stereo()
pk = np.abs(st).max()
st = st / pk * 0.95 if pk > 0.95 else st
out = HERE / "audio"
A.write_wav(out / "SC02_mix_pre.wav", st)
print("wrote", out / "SC02_mix_pre.wav")
