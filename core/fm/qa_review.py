"""`fm qa review-status`: counts and staleness of the preview review (M4)."""
from __future__ import annotations

import re

from .errors import FMError
from .io import read_front_matter
from .project import Project

DEFAULT_REVIEW = "qa/reviews/PREVIEW_REVIEW.md"
_ROW = re.compile(r"^\|\s*(SC\d+_SH\d+)\s*\|\s*\**(PASS|WARN|FAIL)\**\s*\|", re.M)


def review_status(project: Project, rel: str = DEFAULT_REVIEW) -> dict:
    path = project.dir / rel
    if not path.exists():
        raise FMError(f"no review at {rel}")
    meta, body = read_front_matter(path)
    rows = {m.group(1): m.group(2) for m in _ROW.finditer(body)}
    counts = {v: sum(1 for x in rows.values() if x == v) for v in ("PASS", "WARN", "FAIL")}
    fm = meta.get("fm") or {}
    out = {"file": rel, "verdict": meta.get("verdict"), "counts": counts, "shots": len(rows),
           "table_found": bool(rows), "stale": None, "stale_reasons": [], "uncovered_previews": []}
    if not fm:
        out["stale_reasons"].append("no fm block: staleness cannot be checked")
        return out
    loaded = project.load()
    reasons = []
    reviewed = {d["ref"]: d.get("hash") for d in fm.get("derived_from", [])}
    for ref, h in reviewed.items():
        cur = loaded.current_hash(ref)
        if h is None:
            continue
        if cur is None:
            reasons.append(f"{ref} no longer exists")
        elif cur != h:
            reasons.append(f"{ref} changed since the review was stamped")
    item = next((a for a in loaded.artifacts.values() if project.rel(a.path) == rel), None)
    if item is not None and fm.get("stamped_content_hash") not in (None, item.hash):
        reasons.append("review text edited after its last stamp")
    for ref in sorted(loaded.derived):
        if ref.startswith("render:preview_"):
            sid = ref.split("preview_", 1)[1]
            if ref not in reviewed and f"shot:{sid}" not in reviewed:
                out["uncovered_previews"].append(sid)
    # previews whose upstream resolved/shot moved since they were rendered are stale themselves
    from .deps import build_graph
    stale = build_graph(loaded).stale()
    for ref in sorted(stale):
        if ref.startswith("render:preview_"):
            reasons.append(f"{ref} is stale (upstream changed after it was rendered)")
    out["stale_reasons"] = reasons
    out["stale"] = bool(reasons)
    return out
