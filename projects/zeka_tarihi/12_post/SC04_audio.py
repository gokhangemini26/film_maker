"""SC04 sound: narration slice + continuous music bed (faded out at the end) + synced SFX
-> 12_post/audio/SC04_mix_pre.wav. Times are absolute film times; the file starts at SC04.START."""
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

spec = importlib.util.spec_from_file_location("SC04", PROJ / "10_2d" / "SC04.py")
SC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SC)
C = SC.CUE
T0, T1 = SC.START, SC.DURATION


class M(A.Mix):
    def at(self, t, sig, gain=1.0, pan=0.0):
        self.add(t - T0, sig, gain, pan)


mix = M(T1 - T0)
full = A.read_wav(PROJ / "references/voice/narration_48k.wav").mean(axis=1)
norm = 0.89 / max(1e-9, np.abs(full[: int(23.42 * A.SR)]).max())  # same voice gain as SC01-SC03
seg = full[int(T0 * A.SR): int(min(len(full) / A.SR, T1) * A.SR)] * norm
fade = int(0.08 * A.SR)
seg[-fade:] *= np.linspace(1, 0, fade)
mix.add(0, seg, 1.0)

# music bed (planned to 126 s); fade it out over the last two seconds of its length
bed = music.slice_bed(T0, min(music.TOTAL, T1), fade_out=2.2)
n = min(len(bed), len(mix.L))
mix.L[:n] += bed[:n, 0] * 0.9
mix.R[:n] += bed[:n, 1] * 0.9


def bitcrush(sig, steps=8):
    return np.round(sig * steps) / steps


def glitch_sfx(dur=0.35, amp=0.25):
    nz = A.noise(dur)
    t = np.arange(len(nz)) / A.SR
    gate = (np.sin(2 * np.pi * 38 * t) > 0).astype(float)
    tone = np.sign(np.sin(2 * np.pi * 220 * t * (1 + 3 * t)))
    return bitcrush(A.hp_fast(nz, 1500) * 0.4 + tone * 0.3, 6) * gate * A.env(len(nz), 0.002, dur * 0.6, 2) * amp


# SH160 staircase
mix.at(84.28, glitch_sfx(0.3, 0.25), 0.9)
mix.at(84.3, A.whoosh(0.7, 300, 3500, True), 0.6)
for i, f in enumerate((392, 440, 494, 554, 622)):
    mix.at(84.55 + i * 0.08, A.pop(f, 0.2, 1.4), 0.55, -0.4 + i * 0.2)
mix.at(C["altinci"] - 0.1, A.whoosh(0.55, 200, 5000, True), 0.7)
mix.at(C["altinci"] + 0.2, A.chime(1047, 1.6, 0.14), 0.9, 0.3)
mix.at(C["altinci"] + 0.25, A.thud(52, 0.9, 0.7), 0.8)
mix.at(C["sicrama"], A.whoosh(0.6, 400, 2500, True), 0.5, 0.2)
mix.at(C["sicrama"] + 0.62, A.thud(80, 0.5, 0.5), 0.8, 0.4)
mix.at(C["sicrama"] + 0.64, A.ping(2200, 0.6, 0.2), 0.7, 0.4)
mix.at(C["biyoloji"], A.whoosh(1.0, 3000, 200, False), 0.6)
mix.at(C["biyoloji"] + 0.1, A.rumble(1.4, 0.3), 0.8)
mix.at(C["sonuna"] - 0.05, A.pop(220, 0.3, 0.7), 0.9)
mix.at(C["sonuna"], A.thud(46, 1.0, 0.8), 0.8)

# SH170 carbon prison
mix.at(88.45, A.shimmer(1.6, 0.06), 1.0)
mix.at(C["evrim"] + 0.1, A.whoosh(1.3, 500, 3000, True), 0.35)
mix.at(C["kafatasi"], A.servo(1.0, 0.10), 0.9, -0.2)
mix.at(C["kafatasi"] + 0.3, A.clack(0.2, 0.4), 0.7, -0.4)
mix.at(C["kafatasi"] + 0.35, A.clack(0.2, 0.4), 0.7, 0.4)
mix.at(C["kalori"] - 0.05, A.pop(523, 0.25, 1.3), 0.8, 0.5)
mix.at(C["kalori"] + 0.3, A.ticks(1.5, 14, 0.14), 0.8, 0.5)
mix.at(C["kalori"] + 1.7, A.ping(900, 0.4, 0.12), 0.6, 0.5)
mix.at(C["karbon"] - 0.05, A.pop(784, 0.3, 1.4), 0.8, -0.5)
mix.at(C["karbon"], A.shimmer(1.2, 0.05), 0.9, -0.4)
for j in range(6):
    mix.at(C["hapsol"] + j * 0.1, A.clack(0.18, 0.4), 0.7, -0.5 + j * 0.2)
mix.at(C["hapsol"] + 0.7, A.thud(50, 1.0, 0.8), 0.9)

# SH180 break free -> silicon
mix.at(C["zincir"], A.rumble(1.2, 0.3), 0.8)
mix.at(C["zincir"] + 0.4, A.servo(0.9, 0.09), 0.8)
mix.at(SC.SNAP - 0.05, A.shatter(1.2, 0.85), 1.0)
mix.at(SC.SNAP, A.whoosh(0.8, 200, 6000, True), 0.7)
mix.at(SC.SNAP + 0.02, A.thud(42, 1.2, 0.9), 0.9)
mix.at(C["silikon"], A.chime(1318, 1.6, 0.14), 0.9, 0.3)
mix.at(C["silikon"] + 0.05, A.shimmer(1.6, 0.07), 1.0)
mix.at(C["dijital"], A.ticks(1.2, 30, 0.12), 0.8)
mix.at(C["dijital"] + 0.1, A.whoosh(1.0, 600, 5000, True), 0.45)
mix.at(C["kendi"], A.pop(660, 0.25, 1.5), 0.8)
mix.at(C["kopya"], A.pop(740, 0.2, 1.5), 0.75, -0.4)
mix.at(C["kopya"] + 0.01, A.pop(740, 0.2, 1.5), 0.75, 0.4)
mix.at(C["kopya"] + 0.36, A.pop(880, 0.2, 1.5), 0.75, -0.7)
mix.at(C["kopya"] + 0.37, A.pop(880, 0.2, 1.5), 0.75, 0.7)
for dt, pn in ((C["yapay"] - 0.2, -0.55), (C["yapay"] - 0.1, -0.2), (C["yapay"] - 0.1, 0.2), (C["yapay"] - 0.2, 0.55)):
    mix.at(dt, A.pop(1047, 0.18, 1.5), 0.6, pn)
mix.at(C["super"] - 0.05, A.rumble(2.2, 0.4), 1.0)
for f, d in ((523, 0.0), (659, 0.05), (784, 0.1), (1047, 0.15)):
    mix.at(C["super"] + d, A.chime(f, 2.4, 0.11), 0.9, 0.0)
mix.at(C["super"], A.whoosh(1.2, 300, 6000, True), 0.7)
mix.at(C["gecis"], A.ping(1500, 0.5, 0.15), 0.7)

# SH190 the question
mix.at(T["sh190"] if False else SC.T["sh190"], A.shimmer(1.4, 0.04), 0.8)
mix.at(108.6, A.pop(494, 0.3, 1.3), 0.7)
mix.at(C["zekamiz"] - 0.2, A.shimmer(1.8, 0.06), 0.9, -0.3)
mix.at(C["dis"] - 0.1, A.whoosh(2.3, 300, 3500, True), 0.6, 0.0)
mix.at(C["tasimak"], A.ping(1760, 0.8, 0.2), 0.9, 0.4)
mix.at(C["tasimak"] + 0.05, A.chime(1319, 1.8, 0.13), 0.9, 0.4)
mix.at(C["mi"] - 0.05, A.pop(330, 0.4, 0.8), 0.9)
mix.at(C["mi"], A.rumble(1.5, 0.3), 0.8)

# SH200 decode the codes
mix.at(SC.T["sh200"], A.whoosh(0.8, 400, 2500, True), 0.3)
mix.at(C["hizli"] - 0.5, A.ticks(1.9, 36, 0.13), 0.8)
mix.at(C["hizli"] - 0.4, A.whoosh(1.7, 300, 4500, True), 0.4)
mix.at(C["degil"], A.thud(40, 1.1, 0.85), 0.9)
mix.at(C["degil"], A.whoosh(0.7, 3500, 200, False), 0.6)
mix.at(C["degil"] + 0.05, A.clack(0.25, 0.5), 0.8)
mix.at(C["icimiz"] - 0.1, A.shimmer(2.0, 0.07), 1.0)
for c_, f_, p_ in ((C["milyarlarca"] + 0.15, 784, -0.5), (C["milyarlarca"] + 0.6, 698, 0.5),
                   (C["evrimsel"], 587, -0.5), (C["evrimsel"] + 0.4, 523, 0.5)):
    mix.at(c_, A.chime(f_, 1.4, 0.12), 0.8, p_)
mix.at(C["hayatta"] + 0.2, A.whoosh(0.9, 300, 3000, True), 0.35)
mix.at(C["kodlarini"], A.ticks(1.2, 22, 0.09), 0.8)
mix.at(C["cozmek"] + 0.15, A.unlock(), 1.0)
mix.at(C["geciyor"], A.shimmer(2.0, 0.09), 1.0)
mix.at(C["geciyor"], A.whoosh(1.2, 300, 7000, True), 0.7)
for f, d in ((392, 0.0), (523, 0.04), (659, 0.08), (784, 0.12)):
    mix.at(C["geciyor"] + d, A.chime(f, 3.2, 0.12), 0.9)
mix.at(126.1, A.chime(330, 3.0, 0.10), 0.8)

st = mix.stereo()
peak = np.abs(st).max()
st = st / peak * 0.95 if peak > 0.95 else st
out = PROJ / "12_post/audio"
out.mkdir(parents=True, exist_ok=True)
A.write_wav(out / "SC04_mix_pre.wav", st)
print("wrote", out / "SC04_mix_pre.wav", len(st) / A.SR, "s")
