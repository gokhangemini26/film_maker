"""Render preview stills in the cloud with the bpy module (one process per shot, 4 in parallel), then a contact sheet.
Usage: python scripts/m3_preview_cloud.py [project] [out_dir] [width] [shot,shot..|all]"""
import glob, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project = sys.argv[1] if len(sys.argv) > 1 else "last_signal"
out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, ".fm_local", "prev"))
width = sys.argv[3] if len(sys.argv) > 3 else "768"
sel = sys.argv[4] if len(sys.argv) > 4 else "all"
resolved = os.path.join(root, "projects", project, "09_resolved")
ids = [os.path.basename(p)[:-5] for p in sorted(glob.glob(os.path.join(resolved, "SC*.json")))]
if sel != "all":
    ids = sel.split(",")
os.makedirs(out, exist_ok=True)
runner = os.path.join(root, "blender", "run_cloud.py")


def one(sid):
    r = subprocess.run([sys.executable, runner, resolved, out, sid, width], capture_output=True, text=True, timeout=300)
    return sid, ("FM_OK" in r.stdout), r.stdout[-300:] + r.stderr[-300:]


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, ids))
bad = [s for s, ok, _ in res if not ok]
print("rendered", len(ids) - len(bad), "failed", bad)
from PIL import Image, ImageDraw
w, h, cols = 384, 216, 5
fs = [os.path.join(out, s + ".png") for s in ids if os.path.exists(os.path.join(out, s + ".png"))]
sheet = Image.new("RGB", (cols * w, ((len(fs) + cols - 1) // cols) * h))
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((w, h))
    ImageDraw.Draw(im).text((4, 4), os.path.basename(f)[:-4], fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(os.path.join(out, "contact_sheet.png"))
