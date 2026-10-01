"""`ANIM_*` validation rules for structured shot animation (`shot_animation` artifacts).

Two layers:

* `lint_tracks(tracks, ...)` is pure: it needs only the parsed anim file (plus, optionally, the
  facts about its shot). It checks vocabulary, frame ranges, ordering, blends, prop transitions,
  holds, camera and events, and returns `(level, code, where, message)` tuples.
* `check_animation(project, loaded)` adds the project context (file name, shot exists, frame
  count from the resolver's frame table, vocabulary canon drift) for `fm validate`.

The resolver refuses to build `motion` for an anim file with any ERROR here: an unknown ref
fails loudly, nothing is guessed.
"""
from __future__ import annotations

import json
from typing import Iterable

from . import animvocab as V
from .schemas.animation import AnimationTracks, anim_artifact_id, anim_path

Issue = tuple[str, str, str, str]  # level, code, where inside the file, message

_PROP_VALUE_FIELDS = ("state", "loc", "arm", "attach", "pip", "tilt_deg", "swing_deg", "bounce_f")
_UI_NEEDS_DUR = ("dip", "key_press", "text", "pulse", "slide", "heart", "progress", "photo_scale")


def _shot_key(shot_id: str) -> tuple[int, int]:
    from .scopes import shot_key
    return shot_key(shot_id)


def _increasing(keys, where: str, out: list[Issue]) -> None:
    for a, b in zip(keys, keys[1:]):
        if b.f <= a.f:
            out.append(("ERROR", "ANIM_ORDER", where, f"frames must strictly increase (f{a.f} then f{b.f})"))
            return


def crank_tops(move, frames: int) -> list[int]:
    """Shot-local frames at which the handle is at 12 o'clock (derived `handle_top` events).
    With `start_f` the first top is `first_top_f` itself (SC04_SH050: turning from f30, first click f56);
    without it the cycle was already running, so tops are `first_top_f` +/- k*24 inside the shot."""
    if move.gait != "crank_turn" or move.first_top_f is None:
        return []
    hi = move.stop_f if move.stop_f is not None else frames - 1
    hi = min(hi, frames - 1)
    f = move.first_top_f
    if move.start_f is None:                    # already turning before the shot: walk back to the first top >= 0
        while f - V.CRANK_CYCLE_F >= 0:
            f -= V.CRANK_CYCLE_F
        while f < 0:
            f += V.CRANK_CYCLE_F
    out = []
    while f <= hi:
        out.append(f)
        f += V.CRANK_CYCLE_F
    return out


def lint_tracks(t: AnimationTracks, *, frame_count: int | None = None,
                shot_characters: Iterable[str] | None = None,
                shot_movement: str | None = None) -> list[Issue]:  # noqa: C901 - a checklist by design
    out: list[Issue] = []
    add = lambda lvl, code, where, msg: out.append((lvl, code, where, msg))  # noqa: E731
    if t.is_stub:
        add("INFO", "ANIM_STUB", "", "stub anim file (no tracks): the shot keeps its prose animation block")
        return out
    if t.frames is None or t.vocab_version is None:
        add("ERROR", "ANIM_INCOMPLETE", "", "`frames` and `vocab_version` are required once a file carries tracks")
        return out
    nf = t.frames
    if t.vocab_version not in V.ACCEPTED_VOCAB_VERSIONS:
        add("ERROR", "ANIM_VOCAB_VERSION", "vocab_version",
            f"written against vocabulary v{t.vocab_version}, the current vocabulary is v{V.VOCAB_VERSION} "
            f"(accepted: {', '.join(f'v{v}' for v in V.ACCEPTED_VOCAB_VERSIONS)})")
    v2 = t.vocab_version is not None and t.vocab_version >= 2

    def need_v2(where: str, what: str) -> None:
        if not v2:
            add("ERROR", "ANIM_VOCAB_VERSION", where, f"{what} needs vocab_version 2 (this file says {t.vocab_version})")
    if frame_count is not None and nf != frame_count:
        add("ERROR", "ANIM_FRAMES", "frames", f"frames is {nf} but the resolved shot has {frame_count}")
    if not t.rationale:
        add("WARN", "ANIM_RATIONALE", "rationale", "missing: say why this motion serves the shot")

    def rng(f: int, where: str, span: int = 1) -> None:
        if f < 0 or f + span - 1 > nf - 1:
            add("ERROR", "ANIM_RANGE", where, f"frame {f}{f'+{span}' if span > 1 else ''} is outside 0..{nf - 1}")

    def enum(value, allowed, where, what) -> bool:
        if value not in allowed:
            add("ERROR", "ANIM_VOCAB", where, f"{what} '{value}' is not in the vocabulary ({', '.join(sorted(allowed))})")
            return False
        return True

    chars = set(shot_characters) if shot_characters is not None else None
    turn = _shot_key(V.COMIC_ENDS_BEFORE)
    for cid, ct in t.characters.items():
        w = f"characters.{cid}"
        if chars is not None and cid not in chars:
            add("ERROR", "ANIM_CHARACTER", w, f"'{cid}' is not a character of this shot")
        if cid not in V.POSES:
            add("ERROR", "ANIM_VOCAB", w, f"no pose vocabulary for character '{cid}'")
            continue
        # pose
        _increasing(ct.pose, f"{w}.pose", out)
        for i, k in enumerate(ct.pose):
            kw = f"{w}.pose[{i}]"
            rng(k.f, kw)
            if enum(k.ref, V.POSES[cid], kw, "pose ref") and V.v2_only_pose(cid, k.ref):
                need_v2(kw, f"pose '{k.ref}'")
            enum(k.ease, V.EASES, kw, "ease")
            b = k.blend_f or 0
            if i == 0 and b:
                add("ERROR", "ANIM_BLEND", kw, "the first pose key has nothing to blend from (blend_f must be 0)")
            if b and k.ease in ("hold", "step"):
                add("ERROR", "ANIM_BLEND", kw, f"ease '{k.ease}' cannot have blend_f")
            limit = ct.pose[i + 1].f if i + 1 < len(ct.pose) else nf - 1
            if k.f + b > limit:
                add("ERROR", "ANIM_BLEND", kw, f"blend f{k.f}+{b} runs past the next key at f{limit}")
        # move
        mv = ct.move
        mw = f"{w}.move"
        if enum(mv.gait, V.GAITS, mw, "gait"):
            loco = V.GAITS[mv.gait]["locomotion"]
            if loco and len(mv.path) < 2:
                add("ERROR", "ANIM_PATH", mw, f"gait '{mv.gait}' needs a path of at least two waypoints")
            if not loco and mv.path:
                add("ERROR", "ANIM_PATH", mw, f"gait '{mv.gait}' takes no path")
            for a, b in zip(mv.path, mv.path[1:]):
                if b.f <= a.f:
                    add("ERROR", "ANIM_ORDER", mw + ".path", "waypoint frames must strictly increase")
                    break
            for j, p in enumerate(mv.path):
                rng(p.f, f"{mw}.path[{j}]")
            if mv.gait == "crank_turn":
                if mv.first_top_f is None:
                    add("ERROR", "ANIM_PATH", mw, "crank_turn needs first_top_f (the handle-top phase)")
                elif mv.first_top_f > nf - 1 or (mv.start_f is not None and mv.first_top_f < mv.start_f):
                    add("ERROR", "ANIM_RANGE", mw, "first_top_f must be <= frames-1, and not before start_f")
                for nm in ("start_f", "stop_f"):
                    v = getattr(mv, nm)
                    if v is not None:
                        rng(v, f"{mw}.{nm}")
            elif mv.first_top_f is not None or mv.start_f is not None or mv.stop_f is not None:
                add("ERROR", "ANIM_PATH", mw, "start_f, first_top_f and stop_f belong to gait crank_turn only")
        # face
        _increasing(ct.face, f"{w}.face", out)
        for i, k in enumerate(ct.face):
            kw = f"{w}.face[{i}]"
            rng(k.f, kw)
            if enum(k.ref, V.face_names(cid), kw, "face ref"):
                if V.v2_only_face(cid, k.ref):
                    need_v2(kw, f"face '{k.ref}'")
                if k.ref in V.comic_faces(cid) and _shot_key(t.shot_id) >= turn:
                    add("ERROR", "ANIM_FACE_AFTER_TURN", kw,
                        f"comic-set face '{k.ref}' is illegal from {V.COMIC_ENDS_BEFORE} on (tone.the_turn)")
        # look, breath
        _increasing(ct.look, f"{w}.look", out)
        for i, k in enumerate(ct.look):
            rng(k.f, f"{w}.look[{i}]")
            enum(k.target, V.LOOK_TARGETS, f"{w}.look[{i}]", "look target")
        # lids (v2)
        if ct.lids:
            need_v2(f"{w}.lids", "a lids track")
        _increasing(ct.lids, f"{w}.lids", out)
        for i, k in enumerate(ct.lids):
            kw = f"{w}.lids[{i}]"
            rng(k.f, kw)
            enum(k.ref, V.LIDS, kw, "lids ref")
            enum(k.ease, V.EASES, kw, "ease")
            d = k.dur_f or 0
            if d and k.ease in ("hold", "step"):
                add("ERROR", "ANIM_LIDS", kw, f"ease '{k.ease}' cannot have dur_f")
            limit = ct.lids[i + 1].f if i + 1 < len(ct.lids) else nf
            if k.f + d > limit:
                add("ERROR", "ANIM_LIDS", kw, f"dur_f runs f{k.f}+{d} past the next lids key (or the shot end) at f{limit}")
        for i, k in enumerate(ct.look):                      # a lids key may not fall inside a look `closed` span
            if k.target == "closed":
                end = ct.look[i + 1].f if i + 1 < len(ct.look) else nf
                for lk in ct.lids:
                    if k.f <= lk.f < end:
                        add("ERROR", "ANIM_LIDS", f"{w}.lids", f"lids key at f{lk.f} falls inside the look 'closed' span "
                            f"f{k.f}-{end - 1} (use one or the other)")
        _increasing(ct.breath, f"{w}.breath", out)
        for i, k in enumerate(ct.breath):
            kw = f"{w}.breath[{i}]"
            rng(k.f, kw, k.dur_f or 1)
            enum(k.ref, V.BREATHS, kw, "breath ref")

    # props
    for prop, keys in t.props.items():
        w = f"props.{prop}"
        if not enum(prop, V.PROPS, w, "prop"):
            continue
        spec = V.PROPS[prop]
        if prop in V.V2_PROPS:
            need_v2(w, f"prop '{prop}'")
        _increasing(keys, w, out)
        running: dict[str, str] = {}
        for i, k in enumerate(keys):
            kw = f"{w}[{i}]"
            rng(k.f, kw, k.dur_f or 1)
            if k.ease is not None:
                enum(k.ease, V.EASES, kw, "ease")
            given = {n: getattr(k, n) for n in _PROP_VALUE_FIELDS if getattr(k, n) is not None}
            if not given:
                add("ERROR", "ANIM_PROP", kw, "a prop key must set at least one value field "
                    f"({', '.join(spec['fields'])})")
            for n, v in given.items():
                allowed = spec["fields"].get(n)
                if allowed is None:
                    add("ERROR", "ANIM_PROP", kw, f"field '{n}' is not legal for {prop} (legal: {', '.join(spec['fields'])})")
                elif n in V.V2_PROP_FIELDS.get(prop, ()):
                    need_v2(kw, f"{prop}.{n}")
                elif isinstance(allowed, tuple):
                    if enum(v, allowed, kw, f"{prop}.{n}"):
                        if v in V.V2_PROP_VALUES.get((prop, n), ()):
                            need_v2(kw, f"{prop}.{n} '{v}'")
                        prev = running.get(n)
                        legal = spec["transitions"].get(n)
                        if prev is not None and legal and v != prev and v not in legal.get(prev, ()):
                            add("ERROR", "ANIM_PROP_TRANSITION", kw,
                                f"{prop}.{n}: {prev} -> {v} is not a legal transition "
                                f"(from {prev}: {', '.join(legal.get(prev, ())) or 'none'})")
                        running[n] = v

    # ui timeline
    for i, e in enumerate(t.ui_timeline):
        w = f"ui_timeline[{i}]"
        rng(e.f, w, e.dur_f or 1)
        if not enum(e.event, V.UI_EVENTS, w, "ui event"):
            continue
        if e.event in _UI_NEEDS_DUR and e.dur_f is None:
            add("ERROR", "ANIM_UI", w, f"event '{e.event}' needs dur_f")
        if e.event == "key_press" and e.key not in V.UI_KEYS:
            add("ERROR", "ANIM_UI", w, f"key_press needs key in {', '.join(V.UI_KEYS)}")
        if e.event == "text" and (e.line is None or e.chars is None):
            add("ERROR", "ANIM_UI", w, "text needs line and chars")
        if e.event == "slide" and e.to not in V.UI_SCREENS:
            add("ERROR", "ANIM_UI", w, f"slide needs `to` in {', '.join(V.UI_SCREENS)}")
        if e.event == "photo_scale" and (e.from_pct is None or e.to_pct is None):
            add("ERROR", "ANIM_UI", w, "photo_scale needs from_pct and to_pct")

    # camera
    cam = t.camera
    if enum(cam.move, V.CAMERA_MOVES, "camera.move", "camera move"):
        if cam.move == "dolly_in":
            if cam.start_f is None or cam.end_f is None or cam.dist_m is None:
                add("ERROR", "ANIM_CAMERA", "camera", "dolly_in needs start_f, end_f and dist_m")
            else:
                rng(cam.start_f, "camera.start_f")
                rng(cam.end_f, "camera.end_f")
                if cam.end_f <= cam.start_f:
                    add("ERROR", "ANIM_CAMERA", "camera", "end_f must be after start_f")
                for nm in ("ease_in_f", "ease_out_f"):
                    r = getattr(cam, nm)
                    if r is not None and not (cam.start_f <= r[0] <= r[1] <= cam.end_f):
                        add("ERROR", "ANIM_CAMERA", f"camera.{nm}", "ease range must lie inside start_f..end_f")
        if shot_movement is not None:
            moving = "dolly" in shot_movement or "push" in shot_movement
            if moving != (cam.move != "none"):
                add("ERROR", "ANIM_CAMERA", "camera.move",
                    f"anim camera move '{cam.move}' disagrees with the shot's camera.movement '{shot_movement}'")

    # holds
    for i, h in enumerate(t.holds):
        w = f"holds[{i}]"
        rng(h.f0, w)
        rng(h.f1, w)
        if h.f1 < h.f0:
            add("ERROR", "ANIM_HOLD", w, "f1 is before f0")
            continue
        if h.min_f is not None and h.f1 - h.f0 + 1 < h.min_f:
            add("ERROR", "ANIM_HOLD", w, f"hold lasts {h.f1 - h.f0 + 1} frames, minimum is {h.min_f}")
        who = [h.character] if h.character else list(t.characters)
        if h.character and h.character not in t.characters:
            add("ERROR", "ANIM_HOLD", w, f"unknown character '{h.character}'")
            continue
        if h.scope in ("body", "all"):
            for cid in who:
                ks = t.characters[cid].pose
                for j, k in enumerate(ks):
                    if h.f0 < k.f <= h.f1:
                        add("ERROR", "ANIM_HOLD", w, f"{cid} has a pose key at f{k.f} inside the body hold f{h.f0}-{h.f1}")
                    elif k.f <= h.f0 < k.f + (k.blend_f or 0):
                        add("ERROR", "ANIM_HOLD", w, f"{cid}'s blend at f{k.f} is still running at f{h.f0}")
        if h.scope in ("face", "all"):
            for cid in who:
                for k in t.characters[cid].face:
                    if h.f0 < k.f <= h.f1:
                        add("ERROR", "ANIM_HOLD", w, f"{cid} has a face key at f{k.f} inside the hold f{h.f0}-{h.f1}")
        if h.scope == "all":                                  # `face` does not block lids (a blink keeps the face)
            for cid in who:
                for k in t.characters[cid].lids:
                    if h.f0 < k.f <= h.f1:
                        add("ERROR", "ANIM_HOLD", w, f"{cid} has a lids key at f{k.f} inside the hold f{h.f0}-{h.f1}")
        if h.scope in ("phone", "all"):
            for prop, keys in t.props.items():
                if prop.startswith("phone_"):
                    for k in keys:
                        if h.f0 < k.f <= h.f1:
                            add("ERROR", "ANIM_HOLD", w, f"{prop} changes at f{k.f} inside the hold f{h.f0}-{h.f1}")

    # events
    seen: set[str] = set()
    for i, e in enumerate(t.events):
        w = f"events[{i}]"
        rng(e.f, w)
        enum(e.kind, V.EVENT_KINDS, w, "event kind")
        if e.id in seen:
            add("ERROR", "ANIM_EVENTS", w, f"duplicate event id '{e.id}'")
        seen.add(e.id)
    for cid, ct in t.characters.items():
        if ct.move.gait == "crank_turn" and any(e.id == "handle_top" for e in t.events):
            add("ERROR", "ANIM_EVENTS", f"characters.{cid}.move",
                "handle_top events are derived from crank_turn; do not write them by hand")

    # preview frames
    for i, f in enumerate(t.preview_frames):
        rng(f, f"preview_frames[{i}]")
    if len(set(t.preview_frames)) != len(t.preview_frames):
        add("ERROR", "ANIM_RANGE", "preview_frames", "duplicate frames")
    return out


# ------------------------------------------------------------------ project level
def _norm(obj):
    return json.loads(json.dumps(obj, sort_keys=True))


def check_animation(project, loaded) -> list[tuple[str, str, str, str]]:
    """(level, code, where, message) for every anim file, vocabulary canon drift included."""
    from .resolve import film_format, frame_table
    out: list[tuple[str, str, str, str]] = []
    by_shot: dict[str, list] = {}
    for item in loaded.artifacts.values():
        if item.meta.kind == "shot_animation" and item.parsed is not None:
            by_shot.setdefault(item.parsed.shot_id, []).append(item)
    table = None
    if by_shot and loaded.shots:
        table = frame_table(loaded, film_format(loaded)["fps"])
    for sid, items in sorted(by_shot.items()):
        for item in items:
            t: AnimationTracks = item.parsed
            where = project.rel(item.path)
            if item.path.name != f"{sid}.anim.yaml" or item.meta.id != anim_artifact_id(sid):
                out.append(("ERROR", "ANIM_FILENAME", where,
                            f"file must be {anim_path(sid)} with fm.id '{anim_artifact_id(sid)}'"))
            shot = loaded.shots.get(sid)
            if shot is None:
                out.append(("ERROR", "ANIM_SHOT_MISSING", where, f"no shot '{sid}'"))
                continue
            for lvl, code, w, msg in lint_tracks(
                    t, frame_count=(table or {}).get(sid, {}).get("frames"),
                    shot_characters=[c.id for c in shot.spec.characters],
                    shot_movement=(shot.spec.camera.movement if shot.spec.camera and shot.spec.camera.movement
                                   else None)):
                out.append((lvl, code, f"{where}:{w}" if w else where, msg))
        if len(items) > 1:
            out.append(("ERROR", "ANIM_FILENAME", sid, f"{len(items)} anim files for one shot"))
    # vocabulary canon: the proposals must match the module
    want = {e["id"]: e for e in V.canon_entry_dicts()}
    have = {cid: it for cid, it in loaded.canon.items() if cid.startswith("animation.vocab.")}
    for cid, it in sorted(have.items()):
        w = project.rel(it.path)
        if cid not in want:
            if not cid.startswith("animation.vocab.v2"):   # v2 spec entries are hand-written proposals
                out.append(("WARN", "ANIM_VOCAB_CANON", w, f"{cid} is not part of the vocabulary module"))
        elif _norm(it.entry.value) != _norm(want[cid]["value"]):
            out.append(("WARN", "ANIM_VOCAB_CANON", w,
                        f"{cid} differs from core/fm/animvocab.py (regenerate the proposal or bump VOCAB_VERSION)"))
    if by_shot and not have:
        out.append(("INFO", "ANIM_VOCAB_CANON", "canon/animation.yaml",
                    "anim files exist but no animation.vocab.* canon is proposed yet"))
    return out
