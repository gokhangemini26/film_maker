"""Contact sheet of the pinned stills: one labelled tile per shot, 5 per row.
Usage: python scripts/contact_sheet.py [project] [out.png]   (default out: projects/<p>/10_blender/contact_sheet.png)
Read-only on the stills; writes only the sheet. Not recorded in project state."""
import glob
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "blender"))
from fm_blender import framesel  # noqa: E402

proj = sys.argv[1] if len(sys.argv) > 1 else "last_signal"
out = sys.argv[2] if len(sys.argv) > 2 else str(root / "projects" / proj / "10_blender" / "contact_sheet.png")
ps = sorted(glob.glob(str(root / "projects" / proj / "10_blender" / "previews" / "SC*.png")))
if not ps:
    sys.exit("no stills in 10_blender/previews")
framesel.contact_strip(ps, out, labels=[os.path.basename(p)[:-4] for p in ps], per_row=5, tile_w=384, title=f"{proj} stills")
print(f"{len(ps)} stills -> {out}")
