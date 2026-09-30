"""Cue-sheet resolution and the `AUDIO_*` validation rules (M6 task E4).

`resolve_cues(project, loaded)` turns `12_post/AUDIO_CUES.yaml` into absolute-frame *placements* (the one
description the mixer, `fm qa audio` and `fm validate` all share) plus `(level, code, where, message)` issues.
Nothing here renders sound: rendering is `fm.audiorun`. Cues point at named animation events (anim file `events`,
or the derived `handle_top` events of a `crank_turn`), so retiming a shot moves its sound.

Rules (codes): AUDIO_FILE, AUDIO_FPS, AUDIO_SHOT, AUDIO_DUP_ID, AUDIO_SOURCE, AUDIO_RECIPE, AUDIO_ASSET,
AUDIO_SPEECH, AUDIO_LICENCE, AUDIO_AT, AUDIO_EVENT, AUDIO_EVENT_AMBIGUOUS, AUDIO_EVENT_NTH, AUDIO_OUT_OF_SHOT,
AUDIO_PAST_SHOT, AUDIO_BED, AUDIO_SILENCE, AUDIO_SILENCE_OVERLAP, AUDIO_PLACEHOLDER, AUDIO_UNLISTED_PLACEHOLDER,
AUDIO_HIT, AUDIO_MIX, AUDIO_EMPTY.
"""
from __future__ import annotations

import re
import wave
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .audio import synth
from .io import load_yaml
from .schemas.audio import AUDIO_CUES_ID, AUDIO_CUES_PATH, LAYERS, AudioCues

Issue = tuple[str, str, str, str]  # level, code, where, message
FPS = synth.FPS
SPEECH_TAGS = {"speech", "dialogue", "dialog", "voice", "vocal", "tts"}
GOOD_LICENCES_NOT = {"", "UNKNOWN", "UNSPECIFIED", "TBD"}


@dataclass
class Placement:
    id: str                       # cue id, or `<cue id>#<i>` for an `each` expansion
    kind: str                     # cue | bed
    owner: str                    # the cue/bed id in the file
    shot: str | None
    scene: str | None
    recipe: str | None
    asset: str | None
    layer: str
    start_f: float                # absolute film frame
    end_f: float | None           # absolute film frame (exclusive) when known
    gain_db: float
    pan: float
    fade_in_f: float
    fade_out_f: float
    duration_f: float | None
    seed: int
    params: dict
    xfade_f: float = 0.0
    tail_ok: bool = False
    allowed_in_silence: bool = False
    placeholder: bool = False
    event: str | None = None
    local_f: float | None = None  # shot-local start (cues)
    hits_f: list = field(default_factory=list)  # absolute frames of internal sync landmarks (cue `hits`)

    def to_json(self) -> dict:
        d = asdict(self)
        d.pop("params")
        return d


@dataclass
class SilenceSpan:
    id: str
    from_f: float                 # absolute
    to_f: float
    floor_db: float
    shot: str | None
    scene: str | None


@dataclass
class AudioContext:
    cues: AudioCues | None = None
    item: Any = None
    table: dict = field(default_factory=dict)
    scenes: dict = field(default_factory=dict)      # scene id -> (start, end) absolute
    events: dict = field(default_factory=dict)      # shot id -> [{id, f, kind}]
    total_frames: int = 0
    placements: list[Placement] = field(default_factory=list)
    silence: list[SilenceSpan] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


# ------------------------------------------------------------------ library
def library_dir(repo: Path) -> Path:
    return Path(repo) / "library" / "audio"


def read_asset(repo: Path, asset_id: str) -> dict | None:
    """`library/audio/<id>/asset.yaml` as a dict with `_file` (resolved path or None) and `_dir`, or None."""
    d = library_dir(repo) / asset_id
    man = d / "asset.yaml"
    if not man.is_file():
        return None
    try:
        data = load_yaml(man) or {}
    except Exception:  # noqa: BLE001 - reported as AUDIO_ASSET by the caller
        return None
    if not isinstance(data, dict):
        return None
    f = data.get("file")
    data = dict(data)
    data["_dir"] = d
    data["_file"] = (d / f) if f and (d / f).is_file() else None
    return data


def wav_frames(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / w.getframerate() * FPS
    except Exception:  # noqa: BLE001
        return None


def licence_of(asset: dict | None) -> str:
    return str((asset or {}).get("licence") or (asset or {}).get("license") or "UNKNOWN").strip() or "UNKNOWN"


def default_layer(recipe: str | None) -> str:
    fam = (recipe or "").split(".")[0]
    return fam if fam in ("ui", "amb", "body", "music") else "sfx"


# ------------------------------------------------------------------ shot facts
def shot_scene(loaded, sid: str) -> str:
    return loaded.shots[sid].spec.scene_id


def shot_events(loaded, table: dict) -> dict[str, list[dict]]:
    """shot id -> events (`id`, shot-local `f`, `kind`, `source`), from anim files including derived handle_top."""
    from .motion import build_motion

    out: dict[str, list[dict]] = {}
    for sid, item in loaded.anims.items():
        t = item.parsed
        if t.is_stub or sid not in table:
            continue
        m = build_motion(t, table[sid]["start"], item.ref)
        out[sid] = [{"id": e["id"], "f": e["f"], "kind": e["kind"], "source": e.get("source", "anim")}
                    for e in m["events"]]
    return out


_NEG = re.compile(r"\b(silence|silent|no\s|cut after|nothing)", re.I)
_FRAME = re.compile(r"(?<![A-Za-z0-9_])f(\d+)(?!\d)(\s*[-–]\s*\d+)?")


def sync_points(text: str | None) -> list[int]:
    """Shot-local frames named by a `sound_sync` line (`key turn f3, coughs f5 and f9`). Negative clauses
    (`silence from f33`, `cut after f33`) and range ends (`f8-29`) are not sync points."""
    pts: list[int] = []
    for clause in re.split(r";", text or ""):
        for part in re.split(r",", clause):
            if _NEG.search(part):
                continue
            for m in _FRAME.finditer(part):
                pts.append(int(m.group(1)))
    return sorted(set(pts))


def build_context(project, loaded) -> AudioContext:
    from .resolve import film_format, frame_table

    ctx = AudioContext()
    items = loaded.audio_cues
    if items:
        ctx.item, ctx.cues = items[0], items[0].parsed
    fps = film_format(loaded)["fps"]
    ctx.table = frame_table(loaded, fps) if loaded.shots else {}
    for sid, row in ctx.table.items():
        sc = shot_scene(loaded, sid)
        lo, hi = ctx.scenes.get(sc, (row["start"], row["start"] + row["frames"]))
        ctx.scenes[sc] = (min(lo, row["start"]), max(hi, row["start"] + row["frames"]))
    ctx.total_frames = max((r["start"] + r["frames"] for r in ctx.table.values()), default=0)
    ctx.events = shot_events(loaded, ctx.table)
    return ctx


# ------------------------------------------------------------------ resolution + rules
def _seed(explicit: int | None, pid: str) -> int:
    return int(explicit) if explicit is not None else zlib.crc32(pid.encode("utf-8")) & 0xFFFF


def _source(repo: Path, obj, where: str, issues: list[Issue], what: str) -> tuple[bool, dict | None]:
    """Validate recipe/asset exclusivity and existence. Returns (ok, asset manifest)."""
    if (obj.recipe is None) == (obj.asset is None):
        issues.append(("ERROR", "AUDIO_SOURCE", where,
                       f"{what} needs exactly one of `recipe` or `asset` (has {'both' if obj.recipe else 'neither'})"))
        return False, None
    if obj.recipe is not None:
        if obj.recipe not in synth.REGISTRY:
            near = ", ".join(sorted(synth.REGISTRY)[:6])
            issues.append(("ERROR", "AUDIO_RECIPE", where,
                           f"recipe '{obj.recipe}' is not in the synth registry (`fm audio list`; e.g. {near} ...)"))
            return False, None
        return True, None
    asset = read_asset(repo, obj.asset)
    if asset is None:
        issues.append(("ERROR", "AUDIO_ASSET", where,
                       f"asset '{obj.asset}': no library/audio/{obj.asset}/asset.yaml (file + licence required)"))
        return False, None
    if asset["_file"] is None:
        issues.append(("ERROR", "AUDIO_ASSET", where,
                       f"asset '{obj.asset}': manifest `file` missing or not found in {asset['_dir']}"))
        return False, asset
    tags = {str(t).lower() for t in (asset.get("tags") or [])}
    if tags & SPEECH_TAGS:
        issues.append(("ERROR", "AUDIO_SPEECH", where,
                       f"asset '{obj.asset}' is tagged {sorted(tags & SPEECH_TAGS)}: the film is wordless (tone.wordless)"))
        return False, asset
    if licence_of(asset).upper() in GOOD_LICENCES_NOT:
        issues.append(("WARN", "AUDIO_LICENCE", where,
                       f"asset '{obj.asset}' has licence UNKNOWN: fine as a WARN before G7, blocks final export"))
    return True, asset


def _dur_f(recipe: str | None, asset: dict | None, explicit: float | None) -> float | None:
    if explicit is not None:
        return float(explicit)
    if recipe is not None:
        return synth.REGISTRY[recipe]["default_duration"] * FPS if recipe in synth.REGISTRY else None
    if asset and asset.get("_file"):
        return wav_frames(asset["_file"])
    return None


def resolve_cues(project, loaded) -> AudioContext:  # noqa: C901 - a checklist by design
    ctx = build_context(project, loaded)
    add = ctx.issues.append
    items = loaded.audio_cues
    if not items:
        return ctx
    if len(items) > 1:
        add(("ERROR", "AUDIO_FILE", ", ".join(project.rel(i.path) for i in items),
             f"{len(items)} audio_cues artifacts; the contract is exactly one ({AUDIO_CUES_PATH})"))
    item, cues = ctx.item, ctx.cues
    base = project.rel(item.path)
    if project.rel(item.path) != AUDIO_CUES_PATH or item.meta.id != AUDIO_CUES_ID:
        add(("ERROR", "AUDIO_FILE", base, f"file must be {AUDIO_CUES_PATH} with fm.id '{AUDIO_CUES_ID}'"))
    if not ctx.table:
        add(("WARN", "AUDIO_SHOT", base, "no shots in the project: cues cannot be resolved"))
        return ctx
    fps = 0
    try:
        from .resolve import film_format
        fps = film_format(loaded)["fps"]
    except Exception:  # noqa: BLE001
        fps = FPS
    if int(round(fps)) != FPS:
        add(("ERROR", "AUDIO_FPS", base, f"the mixer grid is {FPS} fps (2000 samples per frame) but the film is {fps} fps"))
    m = cues.mix
    if not (-40.0 <= m.integrated_lufs <= -5.0) or m.true_peak_dbtp > 0.0 or m.bit_depth not in (16, 24) \
            or m.sample_rate != synth.SR or m.channels != 2:
        add(("ERROR", "AUDIO_MIX", f"{base}:mix",
             "mix targets out of range (LUFS -40..-5, true peak <= 0 dBTP, 48 kHz, 2 channels, 16 or 24 bit)"))
    if not (cues.cues or cues.beds):
        add(("INFO", "AUDIO_EMPTY", base, "the cue sheet has no cues and no beds"))

    seen: set[str] = set()
    dup = lambda i, where: (add(("ERROR", "AUDIO_DUP_ID", where, f"duplicate id '{i}'")) if i in seen else None) or seen.add(i)  # noqa: E731

    # ---- cues
    for ci, c in enumerate(cues.cues):
        where = f"{base}:cues[{ci}]({c.id})"
        dup(c.id, where)
        if c.shot not in ctx.table:
            add(("ERROR", "AUDIO_SHOT", where, f"unknown shot '{c.shot}'"))
            continue
        ok, asset = _source(project.repo, c, where, ctx.issues, "cue")
        row = ctx.table[c.shot]
        frames = row["frames"]
        at = c.at
        if c.layer is not None and c.layer not in LAYERS:
            add(("ERROR", "AUDIO_SOURCE", where, f"layer '{c.layer}' is not one of {list(LAYERS)}"))
        frame_v = [v for v in (at.frame, at.f) if v is not None]
        if (at.event is not None) == bool(frame_v) or len(frame_v) > 1:
            add(("ERROR", "AUDIO_AT", where, "`at` needs exactly one of `event` or `frame` (alias `f`)"))
            continue
        if at.event is not None and (at.nth is not None) and at.each:
            add(("ERROR", "AUDIO_AT", where, "`nth` and `each` are mutually exclusive"))
            continue
        locals_: list[tuple[float, str | None]] = []
        if at.event is not None:
            evs = [e for e in ctx.events.get(c.shot, []) if e["id"] == at.event]
            if not evs:
                have = ", ".join(sorted({e["id"] for e in ctx.events.get(c.shot, [])})) or "none (no anim events for this shot)"
                add(("ERROR", "AUDIO_EVENT", where,
                     f"event '{at.event}' does not exist in {c.shot} (available: {have}); ask the animation-director for the event"))
                continue
            if at.each:
                pick = evs
            elif at.nth is not None:
                if at.nth >= len(evs):
                    add(("ERROR", "AUDIO_EVENT_NTH", where, f"event '{at.event}' occurs {len(evs)} time(s) in {c.shot}; nth {at.nth} does not exist"))
                    continue
                pick = [evs[at.nth]]
            elif len(evs) > 1:
                add(("ERROR", "AUDIO_EVENT_AMBIGUOUS", where,
                     f"event '{at.event}' occurs {len(evs)} times in {c.shot} (f{', f'.join(str(e['f']) for e in evs)}): give `nth` or `each: true`"))
                continue
            else:
                pick = evs
            locals_ = [(float(e["f"]) + at.offset_f, at.event) for e in pick]
        else:
            locals_ = [(float(frame_v[0]) + at.offset_f, None)]
        dur = _dur_f(c.recipe, asset, c.duration_f)
        layer = c.layer or default_layer(c.recipe)
        placeholder = bool(c.placeholder or (c.recipe and synth.REGISTRY.get(c.recipe, {}).get("placeholder"))
                           or (asset and asset.get("placeholder")))
        reported: set[str] = set()
        for k, (lf, ev) in enumerate(locals_):
            pid = c.id if len(locals_) == 1 else f"{c.id}#{k}"
            if lf < 0 or lf >= frames:
                if "out" not in reported:
                    add(("ERROR", "AUDIO_OUT_OF_SHOT", where, f"starts at shot-local f{lf:g} but {c.shot} has {frames} frames (0..{frames - 1})"))
                    reported.add("out")
                continue
            end_local = lf + dur if dur is not None else None
            if end_local is not None and end_local > frames + 1e-6 and not c.tail_ok and "past" not in reported:
                add(("ERROR", "AUDIO_PAST_SHOT", where,
                     f"runs to f{end_local:.1f} but {c.shot} ends at f{frames}: shorten `duration_f`, add a fade, or set `tail_ok: true`"))
                reported.add("past")
            if k == 0:
                for h in c.hits:
                    if end_local is not None and not (lf <= h <= end_local + 1e-6):
                        add(("ERROR", "AUDIO_HIT", where, f"hit f{h} lies outside the cue (f{lf:g}..{end_local:.1f})"))
            if not ok:
                continue
            ctx.placements.append(Placement(
                id=pid, kind="cue", owner=c.id, shot=c.shot, scene=shot_scene(loaded, c.shot), recipe=c.recipe, asset=c.asset,
                layer=layer, start_f=row["start"] + lf, end_f=(row["start"] + end_local) if end_local is not None else None,
                gain_db=c.gain_db, pan=c.pan, fade_in_f=c.fade_in_f, fade_out_f=c.fade_out_f, duration_f=dur,
                seed=_seed(c.seed, pid), params=dict(c.params), tail_ok=c.tail_ok, allowed_in_silence=c.allowed_in_silence,
                placeholder=placeholder, event=ev, local_f=lf, hits_f=[row["start"] + h for h in c.hits]))

    # ---- beds and silence spans (scope resolution shared)
    def span(o, where: str, code: str) -> tuple[float, float, str | None, str | None] | None:
        if (o.shot is None) == (o.scene is None):
            add(("ERROR", code, where, "needs exactly one of `shot` or `scene`"))
            return None
        if o.shot is not None:
            if o.shot not in ctx.table:
                add(("ERROR", "AUDIO_SHOT", where, f"unknown shot '{o.shot}'"))
                return None
            lo, hi, sc = ctx.table[o.shot]["start"], ctx.table[o.shot]["start"] + ctx.table[o.shot]["frames"], shot_scene(loaded, o.shot)
        else:
            if o.scene not in ctx.scenes:
                add(("ERROR", "AUDIO_SHOT", where, f"unknown scene '{o.scene}'"))
                return None
            lo, hi = ctx.scenes[o.scene]
            sc = o.scene
        a = lo + (o.from_f or 0)
        b = lo + o.to_f if o.to_f is not None else hi
        if a < lo or b > hi or b <= a:
            add(("ERROR", code, where, f"span local f{o.from_f or 0}..{o.to_f if o.to_f is not None else hi - lo} must be non-empty and inside the {'shot' if o.shot else 'scene'} (0..{hi - lo})"))
            return None
        return float(a), float(b), o.shot, sc

    for bi, b in enumerate(cues.beds):
        where = f"{base}:beds[{bi}]({b.id})"
        dup(b.id, where)
        ok, asset = _source(project.repo, b, where, ctx.issues, "bed")
        sp = span(b, where, "AUDIO_BED")
        if sp is None or not ok:
            continue
        a, e, shot, sc = sp
        placeholder = bool(b.placeholder or (b.recipe and synth.REGISTRY.get(b.recipe, {}).get("placeholder"))
                           or (asset and asset.get("placeholder")))
        ctx.placements.append(Placement(
            id=b.id, kind="bed", owner=b.id, shot=shot, scene=sc, recipe=b.recipe, asset=b.asset, layer=b.layer,
            start_f=a, end_f=e, gain_db=b.gain_db, pan=b.pan, fade_in_f=0, fade_out_f=0, duration_f=e - a,
            seed=_seed(b.seed, b.id), params=dict(b.params), xfade_f=b.xfade_f, allowed_in_silence=b.allowed_in_silence,
            placeholder=placeholder))

    for si, s in enumerate(cues.silence):
        where = f"{base}:silence[{si}]({s.id})"
        dup(s.id, where)
        sp = span(s, where, "AUDIO_SILENCE")
        if sp is None:
            continue
        ctx.silence.append(SilenceSpan(s.id, sp[0], sp[1], s.floor_db if s.floor_db is not None else m.silence_floor_db,
                                       sp[2], sp[3]))

    # ---- silence overlap (extent = nominal cue length; `allowed_in_silence` is the deliberate room-tone floor)
    for p in ctx.placements:
        if p.allowed_in_silence:
            continue
        end = p.end_f if p.end_f is not None else p.start_f + 1e-3
        for s in ctx.silence:
            if p.start_f < s.to_f and end > s.from_f:
                add(("ERROR", "AUDIO_SILENCE_OVERLAP", f"{base}:{p.owner}",
                     f"{p.kind} '{p.id}' (film f{p.start_f:g}..{end:g}) overlaps silence '{s.id}' (f{s.from_f:g}..{s.to_f:g}); "
                     "end it before the span, or set `allowed_in_silence` for a deliberate room-tone floor"))
                break

    # ---- placeholders: reported, never silent
    by_sound: dict[str, list[str]] = {}
    for p in ctx.placements:
        if p.placeholder:
            by_sound.setdefault(p.recipe or p.asset or "?", []).append(p.owner)
    listed = {h.sound for h in cues.human_supply}
    for snd, owners in sorted(by_sound.items()):
        uniq = sorted(set(owners))
        add(("WARN", "AUDIO_PLACEHOLDER", base,
             f"{snd} is a PLACEHOLDER used by {len(uniq)} cue(s) ({', '.join(uniq[:6])}{' ...' if len(uniq) > 6 else ''}): the human supplies the real sound"))
        if snd not in listed:
            add(("WARN", "AUDIO_UNLISTED_PLACEHOLDER", f"{base}:human_supply",
                 f"placeholder {snd} is not on the human_supply list"))
    return ctx


def check_audio(project, loaded) -> list[Issue]:
    """`AUDIO_*` issues for `fm validate` (empty when the project has no cue sheet)."""
    if not loaded.audio_cues:
        return []
    return resolve_cues(project, loaded).issues


def placements_json(ctx: AudioContext) -> list[dict]:
    return [p.to_json() for p in ctx.placements]
