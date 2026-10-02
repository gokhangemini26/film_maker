"""Render a 2D scene module to H.264 (parallel chunks) and mux its audio.

python two_d/fm_2d/render.py <scene.py> --audio <mix.wav> --out <file.mp4> [--workers 2] [--start 0 --end D]
"""
from __future__ import annotations

import argparse
import importlib.util
import multiprocessing as mp
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skia  # noqa: E402

from fm_2d.core import FPS, H, W, Finisher, new_surface, snapshot  # noqa: E402


def load_scene(path):
    spec = importlib.util.spec_from_file_location("scene", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def worker(args):
    scene_path, f0, f1, out = args
    sc = load_scene(scene_path)
    fin = Finisher()
    surf = new_surface()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-tune", "animation",
           "-pix_fmt", "yuv420p", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        sc.render(cv, f / FPS)
        p.stdin.write(fin(snapshot(surf), f).tobytes())
    p.stdin.close()
    p.wait()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    a = ap.parse_args()
    sc = load_scene(a.scene)
    end = a.end or sc.DURATION
    f0, f1 = int(round(a.start * FPS)), int(round(end * FPS))
    n = f1 - f0
    chunks = max(a.workers * 3, 1)
    bounds = [f0 + n * i // chunks for i in range(chunks + 1)]
    tmp = Path(tempfile.mkdtemp(prefix="fm2d_"))
    jobs = [(a.scene, bounds[i], bounds[i + 1], tmp / f"c{i:03d}.mp4") for i in range(chunks)]
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for i, _ in enumerate(pool.imap(worker, jobs)):
            print(f"chunk {i + 1}/{chunks} done ({time.time() - t0:.0f}s)", flush=True)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{j[3]}'\n" for j in jobs))
    video = tmp / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(video)], check=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.audio:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-ss", str(a.start), "-i", a.audio,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                        str(out)], check=True)
    else:
        video.replace(out)
    print("wrote", out, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
