"""One continuous ambient music bed for the whole film (deterministic), sliced per scene.

Harmony follows the arc: warm minor (hook, biology) -> brighter (five breakthroughs) -> cooler, suspended
(AI forgetting) -> open, rising (sixth breakthrough).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "two_d"))
from fm_2d import audio as A  # noqa: E402

TOTAL = 126.0
CHORD_S = 2.95
PROG = (
    # SC01 0-23.4: Am F C G | Am F C E
    [[45, 57, 64, 69], [41, 57, 65, 69], [48, 60, 64, 67], [43, 55, 62, 71],
     [45, 57, 64, 72], [41, 60, 65, 69], [48, 60, 67, 76], [40, 59, 64, 68]] +
    # SC02 23.4-51.4: C G Am F (x2), Dm G C E
    [[48, 60, 64, 67], [43, 59, 62, 67], [45, 57, 64, 72], [41, 57, 65, 72]] * 2 +
    [[50, 62, 65, 69], [43, 59, 62, 71]] +
    # SC03 51.4-82: Dm Bb F C ... suspended, cooler
    [[50, 62, 65, 69], [46, 58, 65, 69], [41, 60, 65, 67], [48, 60, 62, 67]] * 3 +
    # SC04 82-126: F G Am C ... lift
    [[41, 57, 65, 72], [43, 59, 67, 74], [45, 60, 64, 72], [48, 64, 67, 76]] * 4
)
OUT = HERE / "audio" / "music_bed.wav"


def build():
    A.rng = np.random.default_rng(1234)
    n = int(TOTAL / CHORD_S) + 1
    chords = (PROG * 3)[:n]
    lo = A.pad(n * CHORD_S + 1.5, chords, amp=0.10)
    A.rng = np.random.default_rng(99)
    hi = A.pad(n * CHORD_S + 1.5, [[c + 12 for c in ch] for ch in chords], amp=0.035)
    L = int(TOTAL * A.SR)
    st = np.stack([lo[:L] * 1.0 + hi[:L] * 0.7, lo[:L] * 0.85 + hi[:L] * 1.0], axis=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    A.write_wav(OUT, st)
    return st


def slice_bed(t0, t1, fade_in=0.0, fade_out=0.0):
    if not OUT.exists():
        build()
    st = A.read_wav(OUT)
    seg = st[int(t0 * A.SR): int(t1 * A.SR)].copy()
    t = np.arange(len(seg)) / A.SR
    g = np.ones(len(seg))
    if fade_in:
        g *= np.minimum(1, t / fade_in)
    if fade_out:
        g *= np.minimum(1, (len(seg) / A.SR - t) / fade_out)
    return seg * g[:, None]


if __name__ == "__main__":
    build()
    print("wrote", OUT)
