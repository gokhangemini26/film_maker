"""Frame selection and contact strips for `fm blender frames|playblast`: pure python (PIL for the strips), no bpy,
so the `fm` CLI can use them without a Blender."""
from __future__ import annotations

import os
import re


def parse_frames(spec, n):
    """'12,f24,30-34,last' -> sorted unique frame list inside 0..n-1. Bad or out-of-range items raise ValueError."""
    out = []
    for item in [s.strip() for s in str(spec).split(",") if s.strip()]:
        if item == "all":
            out += list(range(n))
        elif item == "last":
            out.append(n - 1)
        elif re.fullmatch(r"f?\d+-f?\d+", item):
            a, b = (int(x.lstrip("f")) for x in item.split("-"))
            out += list(range(a, b + 1))
        elif re.fullmatch(r"f?\d+", item):
            out.append(int(item.lstrip("f")))
        else:
            raise ValueError(f"cannot read frame spec '{item}' (use 12, f24, 30-34, last or all)")
    bad = [x for x in out if not 0 <= x < n]
    if bad:
        raise ValueError(f"frame(s) {bad} outside the shot (0..{n - 1})")
    return sorted(set(out))


def select_frames(shot, *, frames=None, every_key=False, preview_frame=False, first_last=False):
    """The frame numbers to render for `shot` from the CLI options (union of everything asked for)."""
    n = int((shot.get("frames") or {}).get("count") or 1)
    motion = shot.get("motion") or {}
    out = set()
    if frames:
        out |= set(parse_frames(frames, n))
    if every_key:
        out |= {f for f in (motion.get("preview_frames") or []) if 0 <= f < n}
        if not motion.get("preview_frames"):
            out |= {k["f"] for c in (motion.get("characters") or {}).values() for k in c.get("pose", [])} | {n - 1}
    if preview_frame:
        pf = (shot.get("animation") or {}).get("preview_frame")
        out.add(int(pf) if isinstance(pf, (int, float)) and 0 <= pf < n else n // 2)
    if first_last:
        out |= {0, n - 1}
    if not out:
        out |= {n // 2}
    return sorted(out)


def contact_strip(image_paths, out_path, *, labels=None, per_row=None, tile_w=None, title=None):
    """Tile the images (equal size) into one PNG, each stamped with its label (default: the file's frame number)."""
    from PIL import Image, ImageDraw, ImageFont
    imgs = [Image.open(p).convert("RGB") for p in image_paths]
    if not imgs:
        raise ValueError("no images for the contact strip")
    if tile_w:
        imgs = [im.resize((tile_w, int(im.height * tile_w / im.width))) for im in imgs]
    w, h = imgs[0].size
    per_row = per_row or (len(imgs) if len(imgs) <= 4 else 4)
    rows = (len(imgs) + per_row - 1) // per_row
    pad, head = 4, (22 if title else 0)
    sheet = Image.new("RGB", (per_row * w + (per_row + 1) * pad, rows * (h + 18) + (rows + 1) * pad + head), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None
    if title:
        d.text((pad, pad), title, fill=(230, 230, 230), font=font)
    for k, (p, im) in enumerate(zip(image_paths, imgs)):
        r, c = divmod(k, per_row)
        x, y = pad + c * (w + pad), head + pad + r * (h + 18 + pad)
        sheet.paste(im, (x, y + 16))
        lab = labels[k] if labels else "f" + os.path.splitext(os.path.basename(p))[0].lstrip("0").rjust(1, "0")
        d.text((x + 2, y + 2), lab, fill=(255, 220, 120), font=font)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    sheet.save(out_path)
    return out_path


