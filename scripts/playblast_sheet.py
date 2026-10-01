"""Contact sheet of the playblast: one frame per second, tiled, small JPEG (git-trackable review evidence).
Usage: python scripts/playblast_sheet.py last_signal [every_seconds=1]"""
import subprocess, sys, pathlib, tempfile
from PIL import Image, ImageDraw
slug = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
root = pathlib.Path("projects") / slug
film = root / "10_blender/playblast/film.mp4"
if not film.exists():
    sys.exit(f"missing {film}")
tmp = pathlib.Path(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-v", "error", "-i", str(film), "-vf", f"fps=1/{step},scale=320:-1", str(tmp / "%03d.png")], check=True)
fs = sorted(tmp.glob("*.png"))
cols = 6; ims = [Image.open(f).convert("RGB") for f in fs]
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), "black")
d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y)); d.text((x + 4, y + 4), f"{i*step:.0f}s", fill="yellow")
out = root / "qa/playblast_sheet.jpg"
sheet.save(out, quality=82); print(out, len(ims), "frames", out.stat().st_size // 1024, "KB")
