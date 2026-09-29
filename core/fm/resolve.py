"""Resolver: approved shot specs + canon -> fully resolved, engine-ready JSON.

The resolved file is what Blender builders consume. It contains no references
the builder would have to look up: canon references are expanded, hex colours are
converted to sRGB and linear RGB, lens and sensor become a field of view, and
each shot gets its frame range in the film. Output is deterministic (same
input, same bytes) and recorded as a `resolved:<shot>` derived node that
remembers the hashes of everything it was built from, so `fm plan` knows when
it is stale.
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from .deps import build_graph, implicit_shot_deps
from .errors import FMError
from .io import hash_file_bytes, write_json
from .ops import record_derived
from .project import Loaded, Project
from .scopes import resolve_scope, shot_key

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
CANON_REF_RE = re.compile(r"^(?:canon:)?([a-z][a-z0-9_]*(?:\.[a-z0-9][a-z0-9_\-]*)+)$")
RESOLVED_DIR = "09_resolved"
DEFAULT_FORMAT = {"fps": 24, "sensor_width_mm": 36.0, "sensor_height_mm": 20.25,
                  "sensor_fit": "HORIZONTAL", "resolution_px": [1920, 1080], "aspect_ratio": 16 / 9}


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def color(hex_str: str) -> dict[str, Any]:
    h = hex_str.upper()
    srgb = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return {"hex": h, "srgb": [round(v, 6) for v in srgb], "linear": [round(_lin(v), 6) for v in srgb]}


class _Expander:
    def __init__(self, loaded: Loaded):
        self.loaded = loaded
        self.used: set[str] = set()
        self.unresolved: list[str] = []

    def walk(self, obj: Any, *, expand_refs: bool = True) -> Any:
        if isinstance(obj, dict):
            if isinstance(obj.get("hex"), str) and HEX_RE.match(obj["hex"]):   # {hex, role, ...}: merge
                return {**{k: self.walk(v, expand_refs=expand_refs) for k, v in obj.items() if k != "hex"},
                        **color(obj["hex"])}
            return {k: self.walk(v, expand_refs=expand_refs) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.walk(v, expand_refs=expand_refs) for v in obj]
        if isinstance(obj, str):
            if HEX_RE.match(obj):
                return color(obj)
            m = CANON_REF_RE.match(obj)
            if expand_refs and m and m.group(1) in self.loaded.canon:
                cid = m.group(1)
                self.used.add(cid)
                value = self.loaded.canon[cid].entry.value
                return {"$canon": cid, "value": self.walk(value, expand_refs=False)}
        return obj


def film_format(loaded: Loaded) -> dict[str, Any]:
    item = loaded.canon.get("camera.format")
    fmt = dict(DEFAULT_FORMAT)
    if item is not None and isinstance(item.entry.value, dict):
        v = item.entry.value
        for k in fmt:
            if k in v:
                fmt[k] = v[k]
        if "aspect_ratio" not in v and fmt["resolution_px"]:
            fmt["aspect_ratio"] = fmt["resolution_px"][0] / fmt["resolution_px"][1]
    return fmt


def frame_table(loaded: Loaded, fps: float) -> dict[str, dict[str, int]]:
    """Shot id -> {start, frames}. Order is scene order then shot order."""
    shots = sorted(loaded.shots.values(), key=lambda s: shot_key(s.spec.shot_id))
    table, cursor = {}, 0
    for s in shots:
        n = max(1, round(s.spec.duration_s * fps))
        table[s.spec.shot_id] = {"start": cursor, "frames": n}
        cursor += n
    return table


def resolve_shot(project: Project, loaded: Loaded, shot_id: str, table: dict, fmt: dict
                 ) -> tuple[dict[str, Any], list[str]]:
    item = next((s for s in loaded.shots.values() if s.spec.shot_id == shot_id), None)
    if item is None:
        raise FMError(f"unknown shot '{shot_id}'")
    sp = item.spec
    ex = _Expander(loaded)
    fps = fmt["fps"]
    row = table[shot_id]
    cam = sp.camera.model_dump(mode="json", exclude_none=True) if sp.camera else {}
    if cam.get("lens_mm"):
        cam["fov_h_deg"] = round(math.degrees(2 * math.atan(fmt["sensor_width_mm"] / (2 * cam["lens_mm"]))), 4)
    out: dict[str, Any] = {
        "schema": "fm.resolved_shot/1",
        "shot_id": shot_id, "scene_id": sp.scene_id, "sequence_id": sp.sequence_id,
        "frames": {"start": row["start"], "count": row["frames"], "end": row["start"] + row["frames"] - 1,
                   "fps": fps, "duration_s_spec": sp.duration_s},
        "render": {"resolution_px": fmt["resolution_px"], "aspect_ratio": round(fmt["aspect_ratio"], 6)},
        "camera": {**cam, "sensor_width_mm": fmt["sensor_width_mm"],
                   "sensor_height_mm": fmt["sensor_height_mm"], "sensor_fit": fmt["sensor_fit"]},
        "composition": ex.walk(sp.composition.model_dump(mode="json", exclude_none=True)) if sp.composition else {},
        "characters": [],
        "environment": sp.environment.model_dump(mode="json", exclude_none=True) if sp.environment else {},
        "lighting": ex.walk(sp.lighting or {}),
        "color": ex.walk(sp.color or {}),
        "animation": ex.walk(sp.animation or {}, expand_refs=False),
        "assets": list(sp.assets),
    }
    for ch in sp.characters:
        entry = ch.model_dump(mode="json", exclude_none=True)
        wardrobe = {cid.split("characters.%s." % ch.id, 1)[1]: ex.walk(c.entry.value, expand_refs=False)
                    for cid, c in loaded.canon.items() if cid.startswith(f"characters.{ch.id}.")
                    and cid.split(".")[2] in ("wardrobe", "proportions", "representation")}
        for cid in loaded.canon:
            if cid.startswith(f"characters.{ch.id}."):
                ex.used.add(cid)
        entry["canon"] = wardrobe
        out["characters"].append(entry)
    out["provenance"] = {"shot": item.ref, "canon": sorted(ex.used)}
    from_refs = {item.ref, *implicit_shot_deps(loaded, sp), *(f"canon:{c}" for c in ex.used)}
    if "camera.format" in loaded.canon:
        from_refs.add("canon:camera.format")
    return out, sorted(r for r in from_refs if loaded.current_hash(r) is not None)


def resolve(project: Project, scope: str = "film") -> dict[str, Any]:
    """Resolve every shot in SCOPE. Rewrites a file only when its content changed."""
    loaded = project.load()
    graph = build_graph(loaded)
    if not loaded.shots:
        raise FMError("no shots to resolve (STORYBOARD must be produced first)")
    fmt = film_format(loaded)
    table = frame_table(loaded, fmt["fps"])
    sset = resolve_scope(scope, loaded, graph)
    wanted = sorted({r.split(":", 1)[1] for r in sset.closure if r.startswith("shot:")}, key=shot_key)
    if not wanted:
        raise FMError(f"scope '{scope}' contains no shots")
    changed, unchanged = [], []
    (project.dir / RESOLVED_DIR).mkdir(exist_ok=True)
    for sid in wanted:
        data, from_refs = resolve_shot(project, loaded, sid, table, fmt)
        path = project.dir / RESOLVED_DIR / f"{sid}.json"
        before = hash_file_bytes(path) if path.exists() else None
        write_json(path, data)
        after = hash_file_bytes(path)
        rec = loaded.derived.get(f"resolved:{sid}")
        if before == after and rec is not None and {d.ref for d in rec.derived_from} == set(from_refs) \
                and all(loaded.current_hash(d.ref) == d.hash for d in rec.derived_from):
            unchanged.append(sid)
            continue
        record_derived(project, f"resolved:{sid}", from_refs, file=path, producer="fm.resolve")
        changed.append(sid)
    total = sum(v["frames"] for v in table.values())
    return {"scope": scope, "resolved": changed, "unchanged": unchanged,
            "film_frames": total, "film_seconds": round(total / fmt["fps"], 4), "fps": fmt["fps"]}
