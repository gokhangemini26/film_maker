"""Deterministic visual checks on preview stills (M4, layer 1 of the QA loop).

These catch technical problems a person would spot instantly (blank, blown-out or black frames, colour far from the
shot's dominant colour). They never judge creative correctness: technical validity is not creative evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

from .errors import FMError
from .ops import record_derived
from .project import Project

PREVIEW_DIR = "10_blender/previews"


def _stats(path: Path):
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise FMError("fm qa stills needs Pillow (pip install pillow)") from exc
    im = Image.open(path).convert("RGB")
    im.thumbnail((160, 90))
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    n = len(px)
    lum = [(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b in px]
    mean = sum(lum) / n
    std = (sum((v - mean) ** 2 for v in lum) / n) ** 0.5
    bright = sum(v > 0.97 for v in lum) / n
    rgb = [sum(p[i] for p in px) / n for i in range(3)]
    return {"mean_lum": round(mean, 3), "std_lum": round(std, 3), "clipped_frac": round(bright, 3),
            "mean_rgb": [round(c) for c in rgb]}


def _hex_rgb(h: str):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def check(project: Project) -> dict:
    out = project.dir / PREVIEW_DIR
    rows = []
    for f in sorted((project.dir / "09_resolved").glob("SC*.json")):
        shot = json.loads(f.read_text(encoding="utf-8"))
        sid = shot["shot_id"]
        png = out / f"{sid}.png"
        row = {"shot": sid, "findings": []}
        rows.append(row)
        if not png.exists():
            row["findings"].append(["FAIL", "no preview still"])
            continue
        s = _stats(png)
        row["metrics"] = s
        framing = (shot.get("composition") or {}).get("framing")
        n = int(sid.split("SH")[1])
        blackout_expected = shot["scene_id"] == "SC03" and n >= 50
        if s["std_lum"] < 0.02 and not (blackout_expected and s["mean_lum"] < 0.03):
            # a designed blackout (SC03 SH050+) is legitimately flat and near-black
            row["findings"].append(["FAIL", "flat frame (no visible content)"])
        if s["mean_lum"] < 0.03 and not blackout_expected:
            row["findings"].append(["WARN", "near-black frame"])
        if s["clipped_frac"] > 0.6:
            row["findings"].append(["WARN", f"{s['clipped_frac']:.0%} of the frame is clipped white"])
        elif s["clipped_frac"] > 0.35 and framing != "insert":
            row["findings"].append(["WARN", f"{s['clipped_frac']:.0%} of the frame is clipped white"])
        dom = ((shot.get("color") or {}).get("dominant") or {}).get("value")
        dom_hex = dom.get("dominant", {}).get("hex") if isinstance(dom, dict) and isinstance(dom.get("dominant"), dict) else None
        if dom_hex and not blackout_expected:
            d = sum((a - b) ** 2 for a, b in zip(s["mean_rgb"], _hex_rgb(dom_hex))) ** 0.5
            row["colour_distance_to_dominant"] = round(d)
            if d > 140 and framing != "insert":
                row["findings"].append(["WARN", f"mean colour far from scene dominant {dom_hex} (distance {round(d)})"])
    summary = {"shots": len(rows), "fail": sum(any(x[0] == "FAIL" for x in r["findings"]) for r in rows),
               "warn": sum(any(x[0] == "WARN" for x in r["findings"]) for r in rows)}
    report = {"summary": summary, "rows": rows}
    rp = project.dir / "qa" / "stills_report.json"
    rp.write_text(json.dumps(report, indent=1), encoding="utf-8")
    record_derived(project, "qa:stills", [f"resolved:{r['shot']}" for r in rows if (out / f"{r['shot']}.png").exists()],
                   file=rp, producer="fm.qa.stills")
    return report
