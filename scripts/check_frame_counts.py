"""Read-only check: frames on disk per shot vs the resolved frame table (09_resolved/film.json).

Usage: python scripts/check_frame_counts.py [project] [frames_root] [--min-bytes N]
  frames_root defaults to 10_blender/playblast (use 11_render/final for a final render, once a tool produces it).
Counts only NNNN.png (0-based shot frame index, 0..count-1), reports missing indices and empty files, and exits 1 on any gap.
It writes nothing and is not an `fm` check: it never records state and is not G8 evidence by itself.
"""
import json
import re
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith("--")]
project = args[0] if args else "last_signal"
root = Path(__file__).resolve().parents[1] / "projects" / project
frames_root = root / (args[1] if len(args) > 1 else "10_blender/playblast")
min_bytes = int(sys.argv[sys.argv.index("--min-bytes") + 1]) if "--min-bytes" in sys.argv else 1
film = json.loads((root / "09_resolved" / "film.json").read_text(encoding="utf-8"))
pat = re.compile(r"^(\d{4})\.png$")
bad, total = [], 0
for sid, row in film["shots"].items():
    n = int(row["frames"])
    d = frames_root / sid
    have = {}
    if d.is_dir():
        have = {int(m[1]): p for p in d.iterdir() if (m := pat.match(p.name))}
    missing = [i for i in range(n) if i not in have]
    empty = [i for i, p in have.items() if i < n and p.stat().st_size < min_bytes]
    extra = sorted(i for i in have if i >= n)
    total += n - len(missing)
    if missing or empty or extra:
        bad.append(sid)
        print(f"{sid}: {n - len(missing)}/{n} frames; missing {missing[:6]}{'...' if len(missing) > 6 else ''}; empty {empty[:6]}; extra {extra[:6]}")
print(f"{total}/{film['total_frames']} frames present under {frames_root}; {len(bad)} shot(s) incomplete")
sys.exit(1 if bad else 0)
