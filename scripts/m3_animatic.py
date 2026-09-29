"""Silent animatic: each preview still held for its resolved frame count, cut in film order (ffmpeg concat).
Usage: python scripts/m3_animatic.py <stills_dir> <out.mp4> [project]"""
import json, os, subprocess, sys, tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stills, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
project = sys.argv[3] if len(sys.argv) > 3 else "last_signal"
film = json.load(open(os.path.join(root, "projects", project, "09_resolved", "film.json"), encoding="utf-8"))
fps = film["format"]["fps"]
lines = []
for sid, sh in sorted(film["shots"].items(), key=lambda kv: kv[1]["start"]):
    lines.append(f"file '{os.path.join(stills, sid + '.png')}'\nduration {sh['frames'] / fps:.5f}")
lines.append(lines[-1].split("\n")[0])
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
    f.write("\n".join(lines))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f.name, "-vf",
                f"fps={fps},scale=1280:-2,format=yuv420p", "-c:v", "libx264", "-crf", "20", out], check=True)
print("wrote", out)
