"""Resolver side of structured animation: an anim file -> the `motion` block of a resolved shot.

Pure and deterministic: same anim file, same bytes. Free-text `note` / `rationale` fields are left
out on purpose (they are for humans; the resolved file is for builders), so editing prose in an
anim file never changes what a builder sees. Frames keep their shot-local number `f` and gain the
absolute film frame `f_abs = frames.start + f`.
"""
from __future__ import annotations

from typing import Any

from . import animvocab as V
from .animcheck import crank_tops
from .schemas.animation import AnimationTracks

SCHEMA = "fm.motion/1"
_DROP = {"note", "rationale"}


def _key(k, start: int) -> dict[str, Any]:
    d = {n: v for n, v in k.model_dump(mode="json", exclude_none=True).items() if n not in _DROP}
    d["f_abs"] = start + k.f
    return d


_ALL_FIELDS = ("state", "loc", "arm", "attach", "pip", "tilt_deg", "swing_deg", "bounce_f")


def _prop_info(prop: str) -> dict[str, Any]:
    """Vocabulary facts a builder needs about a prop that the keys alone do not say: which fields chain across cuts
    (e.g. the charging cable's source `loc` chains, `posed`/`hidden` is framing), whether it persists between shots, and
    the value of each field before the first key."""
    spec = V.PROPS.get(prop, {})
    return {
        "fields": sorted(spec.get("fields", {})),
        "persistent": bool(spec.get("persistent", False)),
        "chained_fields": list(V.prop_chained_fields(prop, _ALL_FIELDS)) if spec.get("persistent") else [],
        "before_first_key": dict(spec.get("before_first_key", {})),
    }


def build_motion(t: AnimationTracks, frame_start: int, source_ref: str) -> dict[str, Any]:
    n = t.frames or 0
    chars: dict[str, Any] = {}
    pose_frames: set[int] = set()
    events = [{"f": e.f, "f_abs": frame_start + e.f, "id": e.id, "kind": e.kind, "source": "anim"}
              for e in t.events]
    for cid, ct in sorted(t.characters.items()):
        mv = {k: v for k, v in ct.move.model_dump(mode="json", exclude_none=True).items()
              if k not in _DROP and k != "path"}
        mv["path"] = [{"f": p.f, "f_abs": frame_start + p.f, "x": p.x, "y": p.y} for p in ct.move.path]
        tops = crank_tops(ct.move, n)
        if ct.move.gait == "crank_turn":
            mv["handle_tops"] = [{"f": f, "f_abs": frame_start + f} for f in tops]
            events += [{"f": f, "f_abs": frame_start + f, "id": "handle_top", "kind": "sound",
                        "source": "derived:crank_turn"} for f in tops]
        chars[cid] = {
            "pose": [_key(k, frame_start) for k in ct.pose],
            "move": mv,
            "face": [_key(k, frame_start) for k in ct.face],
            "look": [_key(k, frame_start) for k in ct.look],
            "breath": [_key(k, frame_start) for k in ct.breath],
            "lids": [_key(k, frame_start) for k in ct.lids],                      # vocabulary v2: blinks / heavy lids
        }
        pose_frames |= {k.f for k in ct.pose}
    cam = {k: v for k, v in t.camera.model_dump(mode="json", exclude_none=True).items() if k not in _DROP}
    for k in ("start_f", "end_f"):
        if k in cam:
            cam[k.replace("_f", "_f_abs")] = frame_start + cam[k]
    holds = [{k: v for k, v in h.model_dump(mode="json", exclude_none=True).items() if k not in _DROP}
             for h in t.holds]
    events.sort(key=lambda e: (e["f"], e["id"]))
    preview = sorted(set(t.preview_frames)) if t.preview_frames else sorted(pose_frames | {max(0, n - 1)})
    return {
        "schema": SCHEMA, "vocab_version": t.vocab_version, "source": source_ref,
        "frames": n, "frame_start": frame_start,
        "characters": chars,
        "props": {p: [_key(k, frame_start) for k in keys] for p, keys in sorted(t.props.items())},
        "prop_info": {p: _prop_info(p) for p in sorted(t.props)},
        "camera": cam, "holds": holds, "events": events,
        "preview_frames": preview,
    }


def vocab_canon_refs(t: AnimationTracks) -> set[str]:
    """`canon:animation.vocab.*` entries this anim file relies on (a vocabulary edit re-resolves exactly these shots)."""
    out: set[str] = set()
    for cid, ct in t.characters.items():
        if ct.pose:
            out |= {f"canon:animation.vocab.pose.{cid}", "canon:animation.vocab.ease"}
        if ct.face:
            out.add("canon:animation.vocab.face")
        if ct.look:
            out.add("canon:animation.vocab.look_target")
        if ct.breath:
            out.add("canon:animation.vocab.breath")
        if ct.lids:
            out |= {"canon:animation.vocab.v2.lids", "canon:animation.vocab.ease"}
        if ct.move.gait != "none":
            out.add("canon:animation.vocab.gait")
    if t.props:
        out |= {"canon:animation.vocab.prop_states", "canon:animation.vocab.ease"}
        out |= {f"canon:animation.vocab.v2.prop.{p}" for p in t.props if p in ("charging_cable", "shop_door")}
    if t.ui_timeline:
        out.add("canon:animation.vocab.ui_event")
    if t.events or t.holds or t.camera.move != "none":
        out.add("canon:animation.vocab.event_kind")
    return out
