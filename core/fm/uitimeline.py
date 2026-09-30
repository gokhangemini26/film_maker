"""Phone-screen state per frame: the ONE parser of `look.style.phone_screen.states_by_shot`.

The canon table (compact `{f0: ..., f32: ...}` forms, `flicker`, `ramp_to_1.0_by_f4_ease_out`, ui labels
like `compose_typing_line_1_f0_15`) is expanded here into an explicit state for every frame of a shot.
Builders and QA read the result (`ui_timeline` in the resolved shot) and never re-derive screen state
from numbers or prose. Anything the table cannot say (flicker dips, key presses, typing, the send line)
comes from typed `ui_timeline` events in the shot's anim file and is overlaid here.

Unknown row keys or ui labels raise: nothing is guessed.
"""
from __future__ import annotations

import re
from typing import Any

from . import animvocab as V
from .errors import FMError

SCHEMA = "fm.ui_timeline/1"
ROW_KEYS = {"ui", "pct", "colour", "bolt", "brightness", "icon_blink", "phone", "photo_scale_pct", "after_f24"}
_FKEY = re.compile(r"^f(\d+)$")
_RAMP = re.compile(r"^ramp_to_([0-9.]+)_by_f(\d+)_(ease_out|ease_in|linear)$")


class UiTimelineError(FMError):
    pass


def _ease(name: str, t: float) -> float:
    t = max(0.0, min(1.0, t))
    if name == "ease_out":
        return 1 - (1 - t) ** 2
    if name == "ease_in":
        return t * t
    if name == "ease_in_out":
        return t * t * (3 - 2 * t)
    return t


def _fkeys(v: Any):
    """[(frame, value)] sorted, and the non-frame keys, when V is an f-keyed dict; else None."""
    if not isinstance(v, dict):
        return None
    keys = [(int(m.group(1)), val) for k, val in v.items() if (m := _FKEY.match(k))]
    if not keys:
        return None
    return sorted(keys, key=lambda kv: kv[0]), {k: val for k, val in v.items() if not _FKEY.match(k)}


def _series(value: Any, n: int, *, default: Any = None, where: str = "") -> list:
    """Per-frame values. Scalars are constant; f-keyed dicts are step functions (numeric values interpolate
    when the dict carries `easing`); `ramp_to_X_by_fN_ease` strings ramp from the previous value."""
    fk = _fkeys(value)
    if fk is None:
        if isinstance(value, dict):
            raise UiTimelineError(f"{where}: unsupported table form {value!r}")
        return [value] * n
    keys, extra = fk
    easing = extra.get("easing")
    out = []
    for f in range(n):
        prev = [kv for kv in keys if kv[0] <= f]
        if not prev:
            out.append(default)
            continue
        f0, v0 = prev[-1]
        if isinstance(v0, str):
            m = _RAMP.match(v0)
            if m:
                target, end, ease = float(m.group(1)), int(m.group(2)), m.group(3)
                before = [kv for kv in keys if kv[0] < f0]
                start = before[-1][1] if before and isinstance(before[-1][1], (int, float)) else default
                if start is None:
                    raise UiTimelineError(f"{where}: ramp at f{f0} has no starting value")
                t = (f - f0) / (end - f0) if end > f0 else 1.0
                out.append(round(start + (target - start) * _ease(ease, t), 6))
                continue
        nxt = [kv for kv in keys if kv[0] > f0]
        if easing and nxt and isinstance(v0, (int, float)) and isinstance(nxt[0][1], (int, float)):
            f1, v1 = nxt[0]
            out.append(round(v0 + (v1 - v0) * _ease(easing, (f - f0) / (f1 - f0)), 6))
        else:
            out.append(v0)
    return out


# ------------------------------------------------------------------ ui labels
def _ui_state(label: str, f: int) -> dict:
    """State implied by one ui label at frame f (compact-table vocabulary, closed list)."""
    if label == "map":
        return {"ui": "map"}
    if label == "call":
        return {"ui": "call", "call_state": "idle"}
    if label == "call_unanswered":
        return {"ui": "call", "call_state": "unanswered"}
    if m := re.fullmatch(r"call_ringing_then_unanswered_f(\d+)", label):
        return {"ui": "call", "call_state": "ringing" if f < int(m.group(1)) else "unanswered"}
    if m := re.fullmatch(r"map_to_call_f(\d+)_(\d+)", label):
        a, b = int(m.group(1)), int(m.group(2))
        if f < a:
            return {"ui": "map"}
        if f < b:
            return {"ui": "map", "slide": {"to": "call", "progress": round((f - a) / (b - a), 6)}}
        return {"ui": "call", "call_state": "idle"}
    if m := re.fullmatch(r"compose_(\d)_lines?", label):
        return {"ui": "compose", "lines": int(m.group(1)), "typing": False}
    if m := re.fullmatch(r"compose_typing_line_(\d)(?:_f(\d+)_(\d+))?", label):
        a, b = (int(m.group(2)), int(m.group(3))) if m.group(2) else (0, 10 ** 9)
        return {"ui": "compose", "lines": int(m.group(1)), "typing": a <= f <= b}
    if m := re.fullmatch(r"compose_3_lines_heart_f(\d+)_(\d+)", label):
        return {"ui": "compose", "lines": 3, "typing": False, "heart": int(m.group(1)) <= f <= int(m.group(2))}
    if label == "compose_to_sent":
        return {"ui": "compose", "lines": 3, "typing": False, "to_sent": "pending"}
    if label == "sent":
        return {"ui": "sent", "sent": {"progress": 1.0, "tick": True}}
    if label in ("off", "wake", "received"):
        return {"ui": label}
    raise UiTimelineError(f"unknown ui label '{label}' in states_by_shot")


def _icon(value: Any, n: int, where: str) -> tuple[list[bool], list[bool]]:
    """(icon_blink mode per frame, icon_visible per frame)."""
    period = [(f % 24) < 12 for f in range(n)]
    if value in (None, False):
        return [False] * n, [True] * n
    if value is True:
        return [True] * n, period
    if isinstance(value, dict) and _fkeys(value) is None:
        vis = [True] * n
        for name, span in value.items():
            if not (isinstance(span, list) and len(span) == 2):
                raise UiTimelineError(f"{where}: icon_blink span '{name}' must be [first, last]")
            for f in range(max(0, span[0]), min(n - 1, span[1]) + 1):
                vis[f] = name.startswith("visible")
        return [True] * n, vis
    steps = _series(value, n, default=False, where=where)
    blink = [v is True for v in steps]
    return blink, [period[f] if blink[f] else True for f in range(n)]


# ------------------------------------------------------------------ expansion
def expand_row(row: dict, shot_id: str, n: int, colours: dict | None = None,
               events: list | None = None) -> dict:
    """Expand one shot's row of states_by_shot into per-frame states, then overlay anim `ui_timeline` events."""
    unknown = set(row) - ROW_KEYS
    if unknown:
        raise UiTimelineError(f"{shot_id}: unknown states_by_shot keys {sorted(unknown)}")
    where = shot_id
    phone = row.get("phone", "ren")
    if phone not in V.UI_PHONES:
        raise UiTimelineError(f"{shot_id}: unknown phone '{phone}'")
    ui = _series(row.get("ui"), n, where=f"{where}.ui")
    pct = _series(row.get("pct"), n, where=f"{where}.pct")
    colour = _series(row.get("colour"), n, where=f"{where}.colour")
    bolt = _series(row.get("bolt", False), n, default=False, where=f"{where}.bolt")
    bright_src = row.get("brightness", 1.0)
    bright = _series(bright_src, n, default=1.0, where=f"{where}.brightness")
    flicker = [(v == "flicker") for v in bright] if isinstance(bright_src, (str, dict)) else [False] * n
    bright = [1.0 if isinstance(v, str) else v for v in bright]           # flicker / steady -> 1.0
    blink, visible = _icon(row.get("icon_blink"), n, f"{where}.icon_blink")
    photo = _series(row.get("photo_scale_pct"), n, default=None, where=f"{where}.photo_scale_pct") \
        if row.get("photo_scale_pct") is not None else [None] * n
    off_from = None
    if row.get("after_f24") == "screen_off":
        off_from = 24
    elif "after_f24" in row:
        raise UiTimelineError(f"{shot_id}: after_f24 must be 'screen_off'")
    frames = []
    for f in range(n):
        label = ui[f]
        if label is None:
            raise UiTimelineError(f"{shot_id}: no ui state at f{f}")
        st = _ui_state(label, f)
        fr: dict[str, Any] = {"f": f, "phone": phone, **st,
                              "pct": pct[f], "colour": colour[f],
                              "red": colour[f] == "red" if colour[f] is not None else None,
                              "bolt": bool(bolt[f]), "icon_blink": blink[f], "icon_visible": visible[f],
                              "brightness": bright[f], "flicker": flicker[f]}
        if photo[f] is not None:
            fr["photo_scale_pct"] = photo[f]
        if off_from is not None and f >= off_from:
            fr["screen_off"] = True
        frames.append(fr)
    warnings: list[str] = []
    _overlay(frames, events or [], phone, shot_id, warnings)
    if any(e.event == "slide" and e.to == "sent" for e in (events or [])):
        for fr in frames:
            fr.pop("to_sent", None)
    elif any(fr.get("to_sent") == "pending" for fr in frames):
        warnings.append("compose_to_sent has no slide event to `sent` in the anim file: the swap frame is unknown")
    if any(fr["flicker"] for fr in frames) and not any(e.event == "dip" for e in (events or [])):
        warnings.append("brightness flicker has no `dip` events in the anim file: brightness stays 1.0")
    return {"schema": SCHEMA, "source": "canon:look.style.phone_screen.states_by_shot", "phone": phone,
            "colours": dict(colours or {}), "frames": frames, "warnings": warnings}


def _span(f: int, dur: int | None, n: int) -> range:
    return range(max(0, f), min(n, f + (dur or 1)))


def _overlay(frames: list[dict], events: list, phone: str, shot_id: str, warnings: list[str]) -> None:
    n = len(frames)
    typed: dict[int, list[tuple[int, int, int, int]]] = {}
    for e in sorted(events, key=lambda e: (e.f, e.event != "slide", e.event)):
        if e.phone != phone:
            raise UiTimelineError(f"{shot_id}: ui event '{e.event}' at f{e.f} is for the {e.phone} phone "
                                  f"but this shot's screen is the {phone} phone")
        rg = _span(e.f, e.dur_f, n)
        dur = e.dur_f or 1
        if e.event == "dip":
            for f in rg:
                frames[f]["brightness"] = min(frames[f]["brightness"], e.value if e.value is not None else 0.7)
        elif e.event == "key_press":
            for f in rg:
                frames[f]["key_pressed"] = e.key
        elif e.event == "text":
            typed.setdefault(e.line, []).append((e.f, dur, e.chars, 0))
        elif e.event == "pulse":
            for i, f in enumerate(rg):
                frames[f]["pulse"] = round(i / dur, 6)
        elif e.event == "slide":
            for i, f in enumerate(rg):
                prog = (i + 1) / dur
                if prog < 1:
                    frames[f]["slide"] = {"to": e.to, "progress": round(prog, 6)}
            for f in range(e.f + dur - 1, n):
                fr = frames[f]
                for k in ("slide", "to_sent"):
                    fr.pop(k, None)
                fr["ui"] = e.to
                if e.to == "sent":
                    fr["sent"] = {"progress": 0.0, "tick": False}
                    fr.pop("lines", None)
                    fr.pop("typing", None)
                elif e.to == "compose":
                    fr.setdefault("lines", 1)
        elif e.event == "heart":
            for f in rg:
                frames[f]["heart"] = True
        elif e.event == "progress":
            for i, f in enumerate(rg):
                frames[f].setdefault("sent", {"progress": 0.0, "tick": False})["progress"] = \
                    round(i / (dur - 1), 6) if dur > 1 else 1.0
            for f in range(e.f + dur, n):
                if "sent" in frames[f]:
                    frames[f]["sent"]["progress"] = 1.0
        elif e.event == "tick":
            for f in range(e.f, n):
                if "sent" in frames[f]:
                    frames[f]["sent"]["tick"] = True
        elif e.event == "photo_scale":
            for i, f in enumerate(rg):
                t = i / (dur - 1) if dur > 1 else 1.0
                frames[f]["photo_scale_pct"] = round(e.from_pct + (e.to_pct - e.from_pct) * _ease("ease_out", t), 6)
            for f in range(e.f + dur, n):
                frames[f]["photo_scale_pct"] = e.to_pct
    for line, evs in typed.items():
        for f in range(n):
            chars = 0
            for start, dur, total, _ in sorted(evs):
                if f >= start + dur:
                    chars = max(chars, total)
                elif f >= start:
                    chars = max(chars, round(total * (f - start + 1) / dur))
            if f >= min(s for s, *_ in evs):
                frames[f].setdefault("typed", {})[str(line)] = chars


def expand_shot(states: dict, shot_id: str, n: int, events: list | None = None) -> dict | None:
    """ui_timeline for SHOT_ID from the canon table VALUE, or None when the table has no row for it."""
    row = states.get(shot_id)
    if row is None:
        if events:
            raise UiTimelineError(f"{shot_id}: ui events need a states_by_shot row (none in canon)")
        return None
    return expand_row(row, shot_id, n, states.get("colour_hex"), events)
