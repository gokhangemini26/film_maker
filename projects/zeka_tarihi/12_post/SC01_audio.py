"""SC01 sound: narration (master timeline) + ambient pad + synced SFX -> 12_post/audio/SC01_mix.wav"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
ROOT = PROJ.parents[1]
sys.path.insert(0, str(ROOT / "two_d"))
from fm_2d import audio as A  # noqa: E402

spec = importlib.util.spec_from_file_location("SC01", PROJ / "10_2d" / "SC01.py")
SC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SC)
C = SC.CUE

DUR = SC.DURATION
VOICE_END = 23.42  # next sentence ("İlk olarak") starts at 23.48 - belongs to SC02

mix = A.Mix(DUR)

# narration
v = A.read_wav(PROJ / "references/voice/narration_48k.wav")
vo = v[: int(VOICE_END * A.SR)].mean(axis=1)
fade = int(0.04 * A.SR)
vo[-fade:] *= np.linspace(1, 0, fade)
vo = vo / max(1e-9, np.abs(vo).max()) * 0.89
mix.add(0, vo, 1.0)

# music bed: continuous film bed (12_post/music.py), sliced for this scene
sys.path.insert(0, str(HERE))
import music  # noqa: E402

bed = music.slice_bed(0, DUR, fade_in=1.5)
n = min(len(bed), len(mix.L))
mix.L[:n] += bed[:n, 0]
mix.R[:n] += bed[:n, 1]

# SH010
mix.add(0.62, A.page_flip(), 1.0, 0.3)
mix.add(1.34, A.page_flip(), 0.9, 0.35)
mix.add(1.0, A.shimmer(1.8, 0.05), 1.0)
for c, f in ((C["max"], 880), (C["zekanin"] - 0.08, 523), (C["kisa"] - 0.08, 659), (C["tarihi"] - 0.08, 784)):
    mix.add(c, A.pop(f, 0.2, 1.3), 0.7)
mix.add(C["ozet"] - 0.1, A.pop(988, 0.25, 1.5), 0.8)
mix.add(5.55, A.whoosh(0.6, 400, 6000, True), 0.9)

# SH020
mix.add(C["ezip"] - 0.55, A.whoosh(0.55, 300, 4000, True), 0.8, -0.3)
mix.add(C["ezip"], A.thud(48, 1.2, 1.0), 0.9)
mix.add(C["ezip"], A.chime(1318, 0.8, 0.12), 0.8, -0.2)
mix.add(C["ezip"] + 0.6, A.clack(0.25, 0.5), 0.8, 0.1)
mix.add(C["ezip"] + 0.72, A.clack(0.2, 0.3), 0.7, 0.1)
mix.add(SC.T["sh030"] - 0.28, A.whoosh(0.4, 600, 3000, False), 0.7, 0.4)

# SH030
mix.add(SC.T["sh030"], A.servo(0.8, 0.09), 0.8, 0.4)
mix.add(10.0, A.servo(1.3, 0.10), 0.9, 0.2)
mix.add(11.33, A.ping(2600, 0.6, 0.3), 0.8, -0.1)
rx, ry, pc = SC.robot_state(SC.RELEASE)
g, vy = 2600, -160.0
hit = SC.RELEASE + (-vy + math.sqrt(vy * vy + 2 * g * (SC.FLOOR - pc[1]))) / g
mix.add(hit, A.shatter(1.1, 0.8), 0.9, -0.05)
mix.add(11.95, A.boing(0.5, 0.35), 0.8, 0.3)
mix.add(SC.T["sh040"] - 0.5, A.whoosh(0.85, 200, 5000, True), 0.8)

# SH040
mix.add(13.0, A.shimmer(1.6, 0.06), 1.0)
mix.add(C["zeka2"], A.chime(659, 1.4, 0.10), 0.8, -0.2)
mix.add(C["buyuk"] - 0.15, A.pop(392, 0.25, 1.4), 0.8)
mix.add(C["coz"], A.unlock(), 0.9)
mix.add(C["coz"] + 0.05, A.whoosh(0.8, 2000, 300, False), 0.4)

# SH050
mix.add(C["s600"] - 0.25, A.ticks(0.75, 20, 0.2), 0.8, 0.3)
mix.add(C["s600"] + 0.5, A.thud(70, 0.8, 0.5), 0.7, 0.3)
mix.add(C["evrim"], A.whoosh(2.4, 2500, 150, False), 0.8)
mix.add(18.9, A.rumble(3.6, 0.45), 1.0)

# SH060 - fossils light up as the timeline reaches them
for i, (_, _, fy) in enumerate(SC.FOSSILS):
    # find when timeline_tip crosses fy
    ts = np.arange(SC.CUE["evrim"], SC.DURATION, 0.01)
    hits = [x for x in ts if SC.timeline_tip(x) >= fy - 60]
    if hits:
        mix.add(hits[0], A.chime([784, 698, 587, 523][i], 1.4, 0.12), 0.8, [0.4, -0.4, 0.4, 0.3][i])
mix.add(C["tozlu"], A.hp_fast(A.lp_fast(A.noise(2.0), 1800), 300) * np.sin(np.pi * np.arange(int(2.0 * A.SR))
                                                                             / (2.0 * A.SR)) * 0.05, 1.0)

st = mix.stereo()
peak = np.abs(st).max()
st = st / peak * 0.95 if peak > 0.95 else st
out = PROJ / "12_post/audio"
out.mkdir(parents=True, exist_ok=True)
A.write_wav(out / "SC01_mix_pre.wav", st)
print("wrote", out / "SC01_mix_pre.wav", "plate hit at", round(hit, 2))
