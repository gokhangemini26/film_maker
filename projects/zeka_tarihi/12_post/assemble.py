"""Assemble the rendered scenes into one continuous programme.

Each scene i covers [START_i, END_i) of the film timeline; SC01's render runs a little past its cut
(frame 703), so every scene is trimmed to the next scene's START. Audio pre-mixes are joined, then
loudness-normalised once (-14 LUFS, -1.5 dBTP) so there is no level jump between scenes.
python 12_post/assemble.py SC01 SC02 [--out 13_delivery/name.mp4]
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
sys.path.insert(0, str(PROJ.parents[1] / "two_d"))
from fm_2d import audio as A  # noqa: E402

FPS = 30


def scene_bounds(name):
    spec = importlib.util.spec_from_file_location(name, PROJ / "10_2d" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, "START", 0.0), m.DURATION


def video_of(name):
    for cand in (f"{name}_video.mp4", f"{name}_v1.mp4"):
        p = PROJ / "11_render" / name / cand
        if p.exists():
            return p
    raise FileNotFoundError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    bounds = [scene_bounds(s) for s in a.scenes]
    # each scene ends where the next starts (frame-exact)
    ends = [bounds[i + 1][0] for i in range(len(bounds) - 1)] + [bounds[-1][1]]
    frames = [(round(b[0] * FPS), round(e * FPS)) for b, e in zip(bounds, ends)]
    audio = []
    for s, (f0, f1) in zip(a.scenes, frames):
        st = A.read_wav(HERE / "audio" / f"{s}_mix_pre.wav")
        audio.append(st[: int((f1 - f0) / FPS * A.SR)])
    full = np.concatenate(audio)
    tmpwav = HERE / "audio" / "assembled_pre.wav"
    A.write_wav(tmpwav, full)
    out = Path(a.out) if a.out else PROJ / "13_delivery" / f"zeka_tarihi_{a.scenes[0]}-{a.scenes[-1]}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    filt = []
    for i, (s, (f0, f1)) in enumerate(zip(a.scenes, frames)):
        cmd += ["-i", str(video_of(s))]
        filt.append(f"[{i}:v]trim=start_frame=0:end_frame={f1 - f0},setpts=PTS-STARTPTS[v{i}]")
    cmd += ["-i", str(tmpwav)]
    filt.append("".join(f"[v{i}]" for i in range(len(a.scenes))) + f"concat=n={len(a.scenes)}:v=1:a=0[v]")
    filt.append(f"[{len(a.scenes)}:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    cmd += ["-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow",
            "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print("wrote", out, "frames", frames)


if __name__ == "__main__":
    main()
