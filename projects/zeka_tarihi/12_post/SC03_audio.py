"""SC03 sound: narration slice + continuous music bed + synced SFX -> 12_post/audio/SC03_mix_pre.wav
Times are absolute film times; the file starts at SC03.START."""
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

spec = importlib.util.spec_from_file_location("SC03", PROJ / "10_2d" / "SC03.py")
SC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SC)
C = SC.CUE
T0, T1 = SC.START, SC.DURATION


class M(A.Mix):
    def at(self, t, sig, gain=1.0, pan=0.0):
        self.add(t - T0, sig, gain, pan)


mix = M(T1 - T0)
full = A.read_wav(PROJ / "references/voice/narration_48k.wav").mean(axis=1)
norm = 0.89 / max(1e-9, np.abs(full[: int(23.42 * A.SR)]).max())  # same voice gain as SC01/SC02
mix.add(0, full[int(T0 * A.SR): int((T1 - 0.02) * A.SR)] * norm, 1.0)
bed = music.slice_bed(T0, T1)
n = min(len(bed), len(mix.L))
mix.L[:n] += bed[:n, 0] * 0.9
mix.R[:n] += bed[:n, 1] * 0.9


def bitcrush(sig, steps=8):
    return np.round(sig * steps) / steps


def glitch_sfx(dur=0.35, amp=0.25):
    n = A.noise(dur)
    t = np.arange(len(n)) / A.SR
    gate = (np.sin(2 * np.pi * 38 * t) > 0).astype(float)
    tone = np.sign(np.sin(2 * np.pi * 220 * t * (1 + 3 * t)))
    return bitcrush(A.hp_fast(n, 1500) * 0.4 + tone * 0.3, 6) * gate * A.env(len(n), 0.002, dur * 0.6, 2) * amp


# SH100
mix.at(52.1, A.whoosh(1.6, 300, 2500, True), 0.5, 0.3)
mix.at(C["zayif"] - 0.1, A.pop(330, 0.3, 0.8), 0.8, -0.3)
mix.at(C["zayif"] - 0.05, A.ping(1400, 0.5, 0.18), 0.6, -0.3)
mix.at(C["felaket"] - 0.05, glitch_sfx(0.45, 0.35), 1.0)
mix.at(C["felaket"], A.thud(45, 1.2, 0.8), 0.8)
mix.at(C["unutma"] - 0.05, glitch_sfx(0.4, 0.3), 1.0)
mix.at(57.85, glitch_sfx(0.5, 0.3), 1.0)
mix.at(57.9, A.whoosh(0.5, 400, 5000, True), 0.6)

# SH110
mix.at(C["bizler"] - 0.1, A.whoosh(0.5, 2000, 500, False), 0.5, -0.5)
for lab, ic, c in SC.HUM_CARDS:
    mix.at(c + 0.1, A.whoosh(0.3, 1500, 3500, True), 0.3, -0.5)
    mix.at(c + 0.45, A.pop(880, 0.15, 1.3), 0.6, -0.5)
mix.at(C["chat"] - 0.1, A.whoosh(0.5, 2000, 500, False), 0.5, 0.5)
for j in range(10):
    mix.at(61.3 + j * 0.09, A.clack(0.04, 0.10), 0.5, 0.4)
c1, c2 = SC.ROB_CARDS
mix.at(c1[2] + 0.45, A.pop(660, 0.15, 1.3), 0.6, 0.6)
hit = c2[2] + 0.45
mix.at(hit, A.thud(80, 0.5, 0.6), 0.8, 0.6)
mix.at(hit, glitch_sfx(0.3, 0.25), 0.8, 0.6)
mix.at(hit + 0.05, A.shatter(0.9, 0.35), 0.6, 0.7)
mix.at(C["yaziyor"] - 0.1, A.thud(60, 0.6, 0.6), 0.7, 0.5)
mix.at(SC.T["sh120"] - 0.3, glitch_sfx(0.4, 0.25), 0.8)

# SH120
mix.at(C["surul"] - 0.05, A.pop(523, 0.2, 1.5), 0.7)
mix.at(C["surul"], A.hp_fast(A.noise(1.2), 2500) * A.env(int(1.2 * A.SR), 0.005, 0.5, 3) * 0.2, 0.8)
for j, f in enumerate((784, 988, 1175)):
    mix.at(C["surul"] + 0.05 + j * 0.06, A.chime(f, 1.0, 0.08), 0.8, -0.3 + j * 0.3)
ice = A.hp_fast(A.noise(1.3), 3000) * np.linspace(0.1, 1, int(1.3 * A.SR)) * 0.18
mix.at(C["ogrenme"] + 0.1, ice, 0.9)
for j in range(6):
    mix.at(C["ogrenme"] + 0.2 + j * 0.18, A.ping(3200 + j * 300, 0.4, 0.08), 0.7, -0.4 + j * 0.15)
mix.at(C["dondur"] + 0.3, A.thud(55, 1.0, 0.6), 0.8)
mix.at(C["dondur"] + 0.3, A.chime(1568, 1.6, 0.08) + A.chime(2093, 1.6, 0.05), 0.8)
mix.at(SC.T["sh130"] - 0.3, glitch_sfx(0.4, 0.22), 0.8)

# SH130
mix.at(C["tipki"] - 0.2, A.pop(600, 0.2, 1.4), 0.6, -0.2)
mix.at(C["dunya"] - 0.2, A.whoosh(0.6, 2500, 600, False), 0.4, -0.2)
mix.at(C["dunya"] + 0.4, A.clack(0.15, 0.3), 0.7, -0.2)
mix.at(C["simul"] + 0.1, glitch_sfx(0.6, 0.3), 0.9, -0.2)
mix.at(C["simul"] + 0.12, A.pop(180, 0.25, 0.7), 0.8)
mix.at(SC.T["sh140"] - 0.3, glitch_sfx(0.4, 0.25), 0.8)

# SH140 clock: ticks slowing down, then stop
tt = SC.T["sh140"]
while tt < C["donup"] + 0.15:
    slow = 1 - min(1, max(0, (tt - C["zaman"]) / (C["donup"] + 0.15 - C["zaman"])))
    mix.at(tt, A.clack(0.05, 0.22), 0.6, 0.4)
    tt += 0.25 + 0.5 * (1 - slow)
mix.at(C["donup"] + 0.15, A.chime(1568, 1.8, 0.07), 0.8, 0.4)
mix.at(C["donup"], ice * 0.7, 0.8)
mix.at(C["dahi"] - 0.1, A.shimmer(1.4, 0.07), 1.0)
mix.at(C["dahi"] - 0.1, A.chime(1046, 1.4, 0.08), 0.8, -0.3)

# SH150
mix.at(SC.T["sh150"] - 0.1, A.whoosh(1.0, 2000, 500, False), 0.5)
mix.at(C["icsel"] - 0.1, A.pop(523, 0.25, 1.6), 0.6, -0.4)
mix.at(C["simulasyon"], A.shimmer(1.4, 0.06), 1.0)
mix.at(C["surekli"], A.whoosh(1.2, 600, 2500, True), 0.4, -0.4)
mix.at(C["hata"], A.pop(180, 0.18, 0.7), 0.8, -0.4)
mix.at(C["yaparak"] + 0.1, A.chime(1318, 0.6, 0.12), 0.8, -0.4)
mix.at(C["yoksun"] - 0.1, A.thud(70, 0.6, 0.5), 0.7, 0.5)
mix.at(C["yoksun"] - 0.05, A.pop(220, 0.3, 0.6), 0.7, 0.5)

st = mix.stereo()
pk = np.abs(st).max()
st = st / pk * 0.95 if pk > 0.95 else st
A.write_wav(HERE / "audio" / "SC03_mix_pre.wav", st)
print("wrote SC03_mix_pre.wav")
