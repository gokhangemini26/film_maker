"""`fm qa motion` (alias `fm check anim`): tier 0 deterministic checks on the structured animation (M6, D1).

Spec level only: it reads the anim files (`09_animation/<SHOT>.anim.yaml`), the shot specs, the canon and, when
present, the resolved shots, and never needs Blender. Technical validity is not creative evidence: these checks
catch what a person would catch by reading the anim files side by side (a lid that opens twice, a battery that
jumps at a cut, a camera faster than the cap), not whether the motion is good.

`analyze(Inputs)` is pure (tests build `Inputs` by hand); `check(project)` loads a project, runs it, writes
`qa/motion_report.json` (the shape `qa/stills_report.json` uses: `{summary:{fail,warn,shots}, rows:[{shot,
findings:[[sev,msg]]}]}`, which is what the ANIMATION phase contract reads) and records it as the derived node
`qa:motion`. Film and scene level findings sit in rows named `FILM` / `SCnn`.

Levels: FAIL contradicts canon, the vocabulary or the shot table; WARN is worth a look (and a missing anim file
while M6 is in progress; `strict=True` makes it FAIL).
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import animvocab as V
from .animcheck import crank_tops, lint_tracks
from .errors import FMError
from .motion import build_motion
from .ops import record_derived
from .project import Project
from .schemas.animation import AnimationTracks
from .uitimeline import UiTimelineError, expand_shot

REPORT = "qa/motion_report.json"

CAMERA_CAP_MPS = 0.15            # camera.movement.push_in.max_speed_m_s when the canon is absent
CAMERA_TOLERANCE = 1.02          # dist_m is rounded to cm and frame-edge conventions differ: 2 % slack on the cap
DOLLY_LENGTH_TOL_M = 0.02        # anim dist_m vs |end_position - start_position|
DECLARED_SPEED_TOL = 0.10        # declared camera peak vs the computed one (WARN)
GAIT_MAX_MPS = {"run_phone_out": 5.5, "scramble": 3.0}     # WARN above (run is about 3-5 m/s, characters.ren.movement)
GAIT_DECLARED_TOL = 0.25
MAX_KEY_GAP_F = 48               # two seconds between pose keys with no body hold over the gap is suspicious
SCENE_TOLERANCE = 0.03           # scene frames vs SCENES.yaml est_duration_s * fps (WARN beyond)
FILM_TOLERANCE = 0.05            # film frames vs the brief's duration (WARN beyond)
TRACKED_FIELDS = ("state", "loc", "arm", "attach", "tilt_deg")
_SC = re.compile(r"^SC\d+$")


@dataclass
class ShotInfo:
    shot_id: str
    scene_id: str
    frames: int
    start: int
    tracks: AnimationTracks | None = None
    anim_ref: str | None = None
    characters: list[str] | None = None
    camera: dict = field(default_factory=dict)        # the shot spec's camera block
    animation: dict = field(default_factory=dict)     # the shot spec's prose animation block
    resolved: dict | None = None                      # 09_resolved/<shot>.json, when present


@dataclass
class Inputs:
    shots: list[ShotInfo]                              # film order
    canon: dict[str, Any] = field(default_factory=dict)      # canon id -> value
    scenes: list[tuple[str, float | None]] = field(default_factory=list)   # (scene id, est_duration_s)
    brief_duration_s: float | None = None
    fps: float = 24
    strict: bool = False
    film_total_resolved: int | None = None             # 09_resolved/film.json total_frames, when present


class _Report:
    def __init__(self) -> None:
        self.rows: dict[str, list[list[str]]] = {}

    def add(self, shot: str, sev: str, msg: str) -> None:
        self.rows.setdefault(shot, [])
        if [sev, msg] not in self.rows[shot]:
            self.rows[shot].append([sev, msg])


def _num(scene_id: str) -> int:
    return int(scene_id[2:])


def _dist(a, b) -> float:
    return math.dist(a, b)


def _frames_txt(fs: list[int]) -> str:
    if not fs:
        return ""
    out, lo, prev = [], fs[0], fs[0]
    for f in fs[1:] + [None]:
        if f is not None and f == prev + 1:
            prev = f
            continue
        out.append(f"f{lo}" if lo == prev else f"f{lo}-{prev}")
        if f is not None:
            lo = prev = f
    return ", ".join(out)


# ------------------------------------------------------------------ tier 0 checks
def _present(rep: _Report, s: ShotInfo, strict: bool) -> bool:
    t = s.tracks
    if t is None:
        rep.add(s.shot_id, "FAIL" if strict else "WARN", f"no anim file (09_animation/{s.shot_id}.anim.yaml)")
        return False
    if t.is_stub:
        rep.add(s.shot_id, "FAIL" if strict else "WARN", "anim file is a stub (no tracks)")
        return False
    return True


def _lint(rep: _Report, s: ShotInfo) -> None:
    t = s.tracks
    for lvl, code, where, msg in lint_tracks(t, frame_count=s.frames, shot_characters=s.characters,
                                             shot_movement=s.camera.get("movement")):
        if lvl == "ERROR":
            rep.add(s.shot_id, "FAIL", f"{code} {where or '(file)'}: {msg}")
        elif lvl == "WARN":
            rep.add(s.shot_id, "WARN", f"{code} {where or '(file)'}: {msg}")


def _timing(rep: _Report, s: ShotInfo) -> None:
    t = s.tracks
    if t.frames is not None and t.frames != s.frames:
        rep.add(s.shot_id, "FAIL", f"anim frames {t.frames} != shot table {s.frames}")
    for cid, ct in t.characters.items():
        if ct.move.gait != "none" or len(ct.pose) < 1:
            continue
        marks = [k.f for k in ct.pose] + [s.frames - 1]
        for a, b in zip(marks, marks[1:]):
            if b - a > MAX_KEY_GAP_F:
                covered = any(h.scope in ("body", "all") and h.f0 <= a and h.f1 >= b - 1
                              and (h.character in (None, cid)) for h in t.holds)
                if not covered:
                    rep.add(s.shot_id, "WARN", f"{cid}: no pose key between f{a} and f{b} ({b - a} frames) "
                            f"and no body hold over the gap (limit {MAX_KEY_GAP_F})")


def _resolved(rep: _Report, s: ShotInfo) -> None:
    r = s.resolved
    if r is None:
        return
    n = (r.get("frames") or {}).get("count")
    if n is not None and n != s.frames:
        rep.add(s.shot_id, "FAIL", f"resolved shot has {n} frames but the shot table says {s.frames} (run fm resolve)")
    t = s.tracks
    if t is None or t.is_stub:
        return
    m = r.get("motion")
    if m is None:
        rep.add(s.shot_id, "WARN", "the resolved shot has no motion block (run fm resolve)")
    elif s.anim_ref and json.loads(json.dumps(m)) != json.loads(json.dumps(build_motion(t, s.start, s.anim_ref))):
        rep.add(s.shot_id, "WARN", "resolved motion is out of date with the anim file (run fm resolve)")


# ---- camera
def _camera_cap(canon: dict) -> tuple[float, int | None, str | None]:
    v = canon.get("camera.movement.push_in")
    if isinstance(v, dict):
        return float(v.get("max_speed_m_s", CAMERA_CAP_MPS)), v.get("max_count_film"), v.get("scene")
    return CAMERA_CAP_MPS, None, None


def _camera(rep: _Report, s: ShotInfo, inp: Inputs) -> bool:
    """Returns True when the shot moves the camera."""
    c = s.tracks.camera
    cap, _, cap_scene = _camera_cap(inp.canon)
    if c.move == "none":
        return False
    if cap_scene and _num(s.scene_id) > _num(cap_scene):
        rep.add(s.shot_id, "FAIL", f"camera moves after {cap_scene} (canon camera.movement.push_in: after_send no camera movement)")
    elif cap_scene and s.scene_id != cap_scene:
        rep.add(s.shot_id, "FAIL", f"camera move outside {cap_scene} (canon camera.movement.push_in)")
    a, b = s.camera.get("start_position"), s.camera.get("end_position")
    geo = _dist(a, b) if a and b else None
    if geo is not None and c.dist_m is not None and abs(geo - c.dist_m) > DOLLY_LENGTH_TOL_M:
        rep.add(s.shot_id, "FAIL", f"dolly length: anim dist_m {c.dist_m} but the shot's start/end positions are {geo:.3f} m apart")
    dist = geo if geo is not None else c.dist_m
    if dist is None or c.start_f is None or c.end_f is None or c.end_f <= c.start_f:
        return True                                   # lint reports the malformed camera track
    span = c.end_f - c.start_f
    ein = (c.ease_in_f[1] - c.ease_in_f[0]) if c.ease_in_f else 0
    eout = (c.ease_out_f[1] - c.ease_out_f[0]) if c.ease_out_f else 0
    lin = span - ein - eout
    if lin < 0:
        rep.add(s.shot_id, "FAIL", "camera ease ranges overlap")
        return True
    denom = lin + (ein + eout) / 2                    # velocity ramps linearly in and out, constant between
    peak = dist * inp.fps / denom
    if peak > cap * CAMERA_TOLERANCE:
        rep.add(s.shot_id, "FAIL", f"camera peak speed {peak:.3f} m/s exceeds the {cap} m/s cap "
                f"({dist:.3f} m over f{c.start_f}-{c.end_f})")
    if c.peak_speed_mps is not None:
        if c.peak_speed_mps > cap:
            rep.add(s.shot_id, "FAIL", f"declared camera peak_speed_mps {c.peak_speed_mps} exceeds the {cap} m/s cap")
        elif abs(peak - c.peak_speed_mps) > DECLARED_SPEED_TOL * c.peak_speed_mps:
            rep.add(s.shot_id, "WARN", f"declared camera peak {c.peak_speed_mps} m/s but dist/timing give {peak:.3f} m/s")
    return True


# ---- locomotion
def _locomotion(rep: _Report, s: ShotInfo, inp: Inputs) -> None:
    for cid, ct in s.tracks.characters.items():
        mv = ct.move
        loco = V.GAITS.get(mv.gait, {}).get("locomotion")
        if not loco or len(mv.path) < 2:
            continue
        segs = []
        for p, q in zip(mv.path, mv.path[1:]):
            if q.f > p.f:
                segs.append(math.hypot(q.x - p.x, q.y - p.y) * inp.fps / (q.f - p.f))
        if not segs:
            continue
        peak = max(segs)
        total = sum(math.hypot(q.x - p.x, q.y - p.y) for p, q in zip(mv.path, mv.path[1:]))
        mean = total * inp.fps / max(1, mv.path[-1].f - mv.path[0].f)
        limit = GAIT_MAX_MPS.get(mv.gait)
        if limit and peak > limit:
            rep.add(s.shot_id, "WARN", f"{cid} {mv.gait}: path speed peaks at {peak:.2f} m/s (mean {mean:.2f}), above {limit} m/s")
        if total == 0:
            rep.add(s.shot_id, "WARN", f"{cid} {mv.gait}: the path does not go anywhere")
        if mv.speed_mps and peak and abs(peak - mv.speed_mps) > GAIT_DECLARED_TOL * mv.speed_mps:
            rep.add(s.shot_id, "WARN", f"{cid}: declared speed_mps {mv.speed_mps} but the path gives a peak of {peak:.2f} m/s")


# ---- sound sync text -> events
_SYNC_F = re.compile(r"(?<![\w-])f(-?\d+)(?!\d)(?!\s*-\s*\d)")
_SKIP_BEFORE = ("silence from ", "cut after ", "phase from ", "cut at ")
_EVERY = re.compile(r"every\s+(\d+)\s+frames", re.I)


def _sync_frames(text: str, frames: int) -> list[int]:
    out: list[int] = []
    for m in _SYNC_F.finditer(text):
        before = text[max(0, m.start() - 14):m.start()].lower()
        if before.endswith(_SKIP_BEFORE):
            continue
        f = int(m.group(1))
        out.append(f)
        tail = text[m.end():m.end() + 30]
        ev = _EVERY.search(tail)
        if ev and re.match(r"^[\s,]*then\s+", tail):
            step = int(ev.group(1))
            k = f + step
            while k <= frames - 1:
                out.append(k)
                k += step
    return sorted({f for f in out if 0 <= f <= frames - 1})


def _sound_sync(rep: _Report, s: ShotInfo) -> None:
    text = s.animation.get("sound_sync") if isinstance(s.animation, dict) else None
    if not isinstance(text, str):
        return
    t = s.tracks
    have = {e.f: e for e in t.events}
    for ct in t.characters.values():
        for f in crank_tops(ct.move, s.frames):
            have.setdefault(f, None)
    missing = [f for f in _sync_frames(text, s.frames) if f not in have]
    if missing:
        rep.add(s.shot_id, "WARN", f"sound_sync names {_frames_txt(missing)} but the anim file has no named event there "
                f"(sound_sync: \"{text[:70]}\")")


# ---- props
def _values(keys, fld):
    return [(k.f, getattr(k, fld), k) for k in keys if getattr(k, fld) is not None]


def _state_at(carried: dict, prop: str, fld: str, keys, f: int):
    val = carried.get((prop, fld))
    val = val[0] if val else None
    for k in keys:
        v = getattr(k, fld)
        if v is not None and k.f <= f:
            val = v
    return val


def _props(rep: _Report, s: ShotInfo, carried: dict) -> None:
    """Cross-shot continuity of persistent props (film order). CARRIED maps (prop, field) -> (value, shot, scene)."""
    for prop, keys in s.tracks.props.items():
        spec = V.PROPS.get(prop)
        if spec is None or not spec.get("persistent"):
            continue
        for fld in V.prop_chained_fields(prop, TRACKED_FIELDS):
            vals = _values(keys, fld)
            if not vals:
                continue
            first_f, first_v, first_k = vals[0]
            prev = carried.get((prop, fld))
            if prev is not None:
                pv, pshot, pscene = prev
                same = (abs(pv - first_v) <= 0.5) if isinstance(first_v, (int, float)) else pv == first_v
                if not same:
                    stated = first_f > 0 or bool(first_k.rationale)
                    legal = spec["transitions"].get(fld, {}) if not isinstance(first_v, (int, float)) else {}
                    if not stated and fld == "attach" and pscene != s.scene_id:
                        rep.add(s.shot_id, "WARN", f"{prop}.attach changes between scenes: {pv} at the end of {pshot}, "
                                f"{first_v} at f0 (fine if the gap between scenes explains it; say so in that key's rationale)")
                    elif not stated:
                        rep.add(s.shot_id, "FAIL", f"{prop}.{fld} jumps at the cut: {pv} at the end of {pshot}, {first_v} at f0 "
                                "(no transition; if the cut hides a change, say why in that key's rationale)")
                    elif legal and first_v not in legal.get(pv, ()):
                        rep.add(s.shot_id, "FAIL", f"{prop}.{fld}: {pv} (end of {pshot}) -> {first_v} at f{first_f} "
                                f"is not a legal transition (from {pv}: {', '.join(legal.get(pv, ())) or 'none'})")
            carried[(prop, fld)] = (vals[-1][1], s.shot_id, s.scene_id)


def _canon_expectations(canon: dict) -> list[tuple[str, str, str, str, str, str]]:
    """(canon id, scene, prop, field, value, mode 'all'|'end'|'start') decoded from the continuity canon."""
    out = []

    def add(cid, scene, prop, fld, value, mode):
        out.append((cid, scene, prop, fld, value, mode))

    door = canon.get("continuity.props.passenger_door")
    if isinstance(door, dict):
        for k, tok in door.items():
            if not (isinstance(tok, str) and _SC.match(k)):
                continue
            if tok == "closed":
                add("continuity.props.passenger_door", k, "passenger_door", "state", "closed", "all")
            elif m := re.fullmatch(r"open_(\d+)(?:deg)?", tok):
                add("continuity.props.passenger_door", k, "passenger_door", "state", f"open_{m.group(1)}", "all")
            elif "left_open" in tok or tok.endswith("_open"):
                add("continuity.props.passenger_door", k, "passenger_door", "state", "open_60", "end")
    gb = canon.get("continuity.props.glovebox_and_crank")
    if isinstance(gb, dict):
        cid = "continuity.props.glovebox_and_crank"
        for scope, body in gb.items():
            if not isinstance(body, dict):
                continue
            scene = scope[:4]
            g, cr = str(body.get("glovebox", "")), str(body.get("crank", ""))
            if g.endswith("closed"):
                add(cid, scene, "glovebox_lid", "state", "closed", "end")
            elif g.endswith("left_down") or g == "lid_down":
                add(cid, scene, "glovebox_lid", "state", "open_down", "all" if scope == scene and g == "lid_down" else "end")
            if "back_in_glovebox_folded" in cr:
                add(cid, scene, "crank_charger", "loc", "glovebox", "end")
                add(cid, scene, "crank_charger", "arm", "folded", "end")
            elif cr.startswith("in_lap") and scope.endswith("_end"):
                add(cid, scene, "crank_charger", "loc", "lap", "end")
            elif cr.startswith("in_lap"):
                add(cid, scene, "crank_charger", "loc", "lap", "all")
                if "arm_out" in cr:
                    add(cid, scene, "crank_charger", "arm", "unfolded", "all")
    hp = canon.get("continuity.hana.headphones")
    if isinstance(hp, dict):
        if hp.get("SC05_start") == "on_head":
            add("continuity.hana.headphones", "SC05", "hana_headphones", "state", "head", "start")
        if hp.get("SC05_after_wake") == "around_neck":
            add("continuity.hana.headphones", "SC05", "hana_headphones", "state", "neck", "end")
    return out


def _canon_props(rep: _Report, inp: Inputs) -> None:
    exps = _canon_expectations(inp.canon)
    for cid, scene, prop, fld, want, mode in exps:
        rows = [(s, [(k.f, getattr(k, fld)) for k in s.tracks.props.get(prop, []) if getattr(k, fld) is not None])
                for s in inp.shots if s.scene_id == scene and s.tracks and not s.tracks.is_stub]
        rows = [(s, v) for s, v in rows if v]
        if not rows:
            continue
        in_scene = [s for s in inp.shots if s.scene_id == scene]
        edge = in_scene[0] if mode == "start" else in_scene[-1]
        if mode in ("start", "end") and not (edge.tracks and not edge.tracks.is_stub):
            continue                                   # the scene's first/last shot has no anim yet: cannot judge
        if mode == "all":
            for s, vals in rows:
                bad = [(f, v) for f, v in vals if v != want]
                if bad:
                    rep.add(s.shot_id, "FAIL", f"{prop}.{fld} is {bad[0][1]} at f{bad[0][0]} but canon {cid} says {want} "
                            f"through {scene}")
        elif mode == "start":
            s, vals = rows[0]
            if vals[0][1] != want:
                rep.add(s.shot_id, "FAIL", f"{prop}.{fld} starts {scene} as {vals[0][1]}, canon {cid} says {want}")
        else:
            s, vals = rows[-1]
            if vals[-1][1] != want:
                rep.add(s.shot_id, "FAIL", f"{prop}.{fld} ends {scene} as {vals[-1][1]} (last set in {s.shot_id}), "
                        f"canon {cid} says {want}")
    for s in inp.shots:
        if s.tracks and not s.tracks.is_stub:
            for k in s.tracks.props.get("phone_ren", []):
                if k.attach == "hand_r":
                    rep.add(s.shot_id, "WARN", f"phone_ren attach hand_r at f{k.f}: canon continuity.props.phone_ren "
                            "keeps the phone in his left hand")


# ---- phone screen (ui)
def _battery_allowed(canon: dict, scene: str) -> set[int] | None:
    v = canon.get("continuity.battery")
    if not isinstance(v, dict) or scene not in v:
        return None
    x = v[scene]
    return {int(i) for i in (x if isinstance(x, list) else [x]) if isinstance(i, (int, float))} or None


def _norm(o):
    return json.loads(json.dumps(o))


def _ui(rep: _Report, s: ShotInfo, states: dict, canon: dict, carried_props: dict, last_ren: dict, inp: Inputs) -> None:
    sid, n = s.shot_id, s.frames
    if sid not in states:
        if s.tracks and s.tracks.ui_timeline:
            rep.add(sid, "FAIL", "anim ui_timeline events but no states_by_shot row in canon")
        return
    events = list(s.tracks.ui_timeline) if s.tracks and not s.tracks.is_stub else []
    try:
        base = expand_shot(states, sid, n)
        over = expand_shot(states, sid, n, events)
    except UiTimelineError as exc:
        rep.add(sid, "FAIL", f"ui: {exc}")
        return
    except FMError as exc:
        rep.add(sid, "FAIL", f"ui: {exc}")
        return
    if s.tracks and not s.tracks.is_stub:              # a shot with no anim file is already reported as such
        for w in over["warnings"]:
            rep.add(sid, "WARN", f"ui: {w}")
    bf, of = base["frames"], over["frames"]
    for key in ("phone", "pct", "colour", "bolt", "screen_off"):
        bad = [f for f in range(n) if bf[f].get(key) != of[f].get(key)]
        if bad:
            rep.add(sid, "FAIL", f"ui: anim ui_timeline overlay changes '{key}' vs the states_by_shot table at "
                    f"{_frames_txt(bad)} (the table owns it)")
    bad = [f for f in range(n) if of[f]["brightness"] > bf[f]["brightness"] + 1e-9]
    if bad:
        rep.add(sid, "FAIL", f"ui: overlay raises brightness above the table at {_frames_txt(bad)} (events only dip)")
    r = s.resolved.get("ui_timeline") if s.resolved else None
    if r and r.get("frames") is not None:
        rf = r["frames"]
        if len(rf) != n:
            rep.add(sid, "FAIL", f"ui: resolved ui_timeline has {len(rf)} frames, the shot has {n} (run fm resolve)")
        else:
            bad = [f for f in range(n) if _norm(rf[f]) != _norm(of[f])]
            if bad:
                rep.add(sid, "FAIL", f"ui: resolved ui_timeline differs from canon table + anim events at {_frames_txt(bad)} "
                        "(run fm resolve)")
    if over["phone"] != "ren":
        return
    allowed = _battery_allowed(canon, s.scene_id)
    zero, hidden, badcol, badpct, badbolt = [], [], [], [], []
    crank_scene = str((canon.get("continuity.battery") or {}).get(f"{s.scene_id}_bolt_on", "")) == "while_cranking"
    crank_keys = s.tracks.props.get("crank_charger", []) if s.tracks and not s.tracks.is_stub else []
    for f, fr in enumerate(of):
        if fr.get("screen_off") or fr["ui"] in ("off", "wake", "received"):
            continue
        p = fr["pct"]
        if p is None:
            hidden.append(f)
            continue
        if p == 0:
            zero.append(f)
        if fr["colour"] is not None and (fr["colour"] == "red") != (p <= 4):
            badcol.append(f)
        if allowed is not None and p not in allowed:
            badpct.append(f)
        if fr["bolt"] and crank_scene:
            arm = _state_at(carried_props, "crank_charger", "arm", crank_keys, f)
            if arm == "folded":
                badbolt.append(f)
    if zero:
        rep.add(sid, "FAIL", f"ui: battery shows 0 % at {_frames_txt(zero)} (canon never: zero_percent)")
    if hidden:
        rep.add(sid, "FAIL", f"ui: battery digit missing at {_frames_txt(hidden)} (canon never: digit_hidden)")
    if badcol:
        rep.add(sid, "FAIL", f"ui: battery colour disagrees with the number (red at 4 % and below, charcoal above) at {_frames_txt(badcol)}")
    if badpct:
        rep.add(sid, "FAIL", f"ui: battery {sorted({of[f]['pct'] for f in badpct})} at {_frames_txt(badpct)} is not in "
                f"canon continuity.battery for {s.scene_id} ({sorted(allowed)})")
    if badbolt:
        rep.add(sid, "FAIL", f"ui: bolt shown at {_frames_txt(badbolt)} while the crank arm is folded (canon never: "
                "bolt_while_not_charging)")
    first, last = of[0], of[-1]
    prev = last_ren.get("last")
    if prev and first["pct"] is not None and prev["pct"] is not None and first["pct"] != prev["pct"]:
        okj = False
        m = re.fullmatch(r"SC(\d+)_to_SC(\d+)_(\d+)_to_(\d+)", str((canon.get("continuity.battery") or {}).get("off_screen_change", "")))
        if m and (prev["scene"], s.scene_id) == (f"SC{m.group(1)}", f"SC{m.group(2)}") \
                and (prev["pct"], first["pct"]) == (int(m.group(3)), int(m.group(4))):
            okj = True
        if not okj:
            rep.add(sid, "FAIL", f"ui: battery {prev['pct']} % at the end of {prev['shot']} but {first['pct']} % at f0 "
                    "(the number never changes off screen except the canon exception)")
    last_ren["last"] = {"pct": last["pct"], "shot": sid, "scene": s.scene_id}


# ---- running time
def _running_time(rep: _Report, inp: Inputs, table_total: int) -> None:
    by_scene: dict[str, int] = {}
    for s in inp.shots:
        by_scene[s.scene_id] = by_scene.get(s.scene_id, 0) + s.frames
    for sc, est in inp.scenes:
        if est is None or sc not in by_scene:
            continue
        want = round(est * inp.fps)
        got = by_scene[sc]
        if want and abs(got - want) / want > SCENE_TOLERANCE:
            rep.add(sc, "WARN", f"scene running time {got} f ({got / inp.fps:.1f} s) vs SCENES.yaml {want} f "
                    f"({est:g} s): {got - want:+d} f")
    if inp.film_total_resolved is not None and inp.film_total_resolved != table_total:
        rep.add("FILM", "FAIL", f"09_resolved/film.json says {inp.film_total_resolved} frames but the shot table adds up "
                f"to {table_total} (run fm resolve)")
    if inp.brief_duration_s:
        want = round(inp.brief_duration_s * inp.fps)
        if abs(table_total - want) / want > FILM_TOLERANCE:
            rep.add("FILM", "WARN", f"film is {table_total} f ({table_total / inp.fps:.1f} s), the brief says "
                    f"{inp.brief_duration_s:g} s ({want} f)")


def analyze(inp: Inputs) -> _Report:
    rep = _Report()
    for s in inp.shots:
        rep.rows.setdefault(s.shot_id, [])
    states = inp.canon.get("look.style.phone_screen.states_by_shot")
    states = states if isinstance(states, dict) else None
    carried: dict = {}
    last_ren: dict = {}
    cams: list[ShotInfo] = []
    _, max_count, _ = _camera_cap(inp.canon)
    for s in inp.shots:
        ok = _present(rep, s, inp.strict)
        _resolved(rep, s)
        if not ok:
            carried.clear()                            # unknown state after a shot with no motion data
            if states is not None:
                _ui(rep, s, states, inp.canon, {}, last_ren, inp)
            continue
        _lint(rep, s)
        _timing(rep, s)
        if _camera(rep, s, inp):
            cams.append(s)
        _locomotion(rep, s, inp)
        _sound_sync(rep, s)
        before = dict(carried)
        _props(rep, s, carried)
        if states is not None:
            _ui(rep, s, states, inp.canon, before, last_ren, inp)
    if max_count is not None and len(cams) > max_count:
        rep.add("FILM", "FAIL", f"{len(cams)} camera moves ({', '.join(c.shot_id for c in cams)}), canon "
                f"camera.movement.push_in allows {max_count}")
    _canon_props(rep, inp)
    _running_time(rep, inp, sum(s.frames for s in inp.shots))
    return rep


# ------------------------------------------------------------------ project level
def _brief_duration(loaded) -> float | None:
    f = (loaded.brief.fields.get("duration_s") if loaded.brief else None)
    try:
        return float(f.value) if f is not None and f.value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_inputs(project: Project, loaded=None, strict: bool = False) -> Inputs:
    from .resolve import film_format, frame_table
    loaded = loaded or project.load()
    fps = film_format(loaded)["fps"]
    table = frame_table(loaded, fps)
    anims = loaded.anims
    shots = []
    for sid, row in table.items():
        item = next(x for x in loaded.shots.values() if x.spec.shot_id == sid)
        sp = item.spec
        rp = project.dir / "09_resolved" / f"{sid}.json"
        shots.append(ShotInfo(
            sid, sp.scene_id, row["frames"], row["start"],
            tracks=anims[sid].parsed if sid in anims else None, anim_ref=anims[sid].ref if sid in anims else None,
            characters=[c.id for c in sp.characters],
            camera=sp.camera.model_dump(mode="json", exclude_none=True) if sp.camera else {},
            animation=dict(sp.animation or {}),
            resolved=json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None))
    film = project.dir / "09_resolved" / "film.json"
    total = json.loads(film.read_text(encoding="utf-8")).get("total_frames") if film.exists() else None
    idx = loaded.scene_index
    return Inputs(
        shots=shots, canon={cid: it.entry.value for cid, it in loaded.canon.items()},
        scenes=[(sc.scene_id, sc.est_duration_s) for sc in (idx.scenes if idx else [])],
        brief_duration_s=_brief_duration(loaded), fps=fps, strict=strict,
        film_total_resolved=total)


def check(project: Project, strict: bool = False, record: bool = True) -> dict:
    loaded = project.load()
    inp = build_inputs(project, loaded, strict)
    rep = analyze(inp)
    order = [s.shot_id for s in inp.shots]
    names = order + sorted(k for k in rep.rows if k not in order)
    rows = [{"shot": k, "findings": rep.rows[k]} for k in names if k in rep.rows]
    summary = {"shots": len(order),
               "fail": sum(any(x[0] == "FAIL" for x in r["findings"]) for r in rows),
               "warn": sum(any(x[0] == "WARN" for x in r["findings"]) for r in rows)}
    report = {"summary": summary, "rows": rows}
    rp = project.dir / REPORT
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=1), encoding="utf-8")
    if record:
        refs = [a.ref for a in loaded.anims.values()] + [f"resolved:{s.shot_id}" for s in inp.shots if s.resolved]
        record_derived(project, "qa:motion", [r for r in refs if loaded.current_hash(r) is not None],
                       file=rp, producer="fm.qa.motion")
    return report
