"""`fm audio scaffold`: a PROPOSED skeleton of `12_post/AUDIO_CUES.yaml` (M6 task E4).

Generated from two facts the repository already holds, never invented:

* each shot's `animation.sound_sync` line (frame-exact sync points) and its anim `events`, and
* the synth registry's `serves` metadata (which recipe was written for which shot line).

It is the starting point the sound-designer edits: a cue whose frame equals a named `sound` anim event points at
the event (retiming then moves it), otherwise it uses an explicit frame and says so. Board-only lines (a sound in
the STORYBOARD but no frame) get frame 0 and a note. Nothing is stamped or advanced here; it writes only the
requested file. The `serves` strings describe the Last Signal film: for another film the scaffold finds no
registry matches and lists every sync point it could not cover in `scaffold_notes`.
"""
from __future__ import annotations

import re
from pathlib import Path

from .audio import synth
from .audiocues import _FRAME, build_context, sync_points
from .errors import FMError
from .io import write_yaml
from .project import Project
from .schemas.audio import AUDIO_CUES_ID, AUDIO_CUES_PATH

_ENTRY = re.compile(r"^(SC\d{2,3}(?:_SH\d{3,4})?(?:/SC\d{2,3}(?:_SH\d{3,4})?)*)\s*(.*?)\s*\((sync|board)(?:,\s*([^)]*))?\)\s*$")
BED_RECIPES = {"amb.car_interior", "amb.street_dusk", "amb.shop_room", "amb.hana_room"}
ALIAS = {"crank.ratchet": "crank.click"}      # ratchet-run serves lines are click frames
MERGE_HITS = {"car.engine_die"}                # one cue; the later sync frames are the recipe's internal timing
GAIN = {"ui": -14.0, "sfx": -12.0, "body": -18.0, "music": -30.0, "amb": -28.0, "foley": -16.0}
BED_GAIN = {"amb.car_interior": -32.0, "amb.street_dusk": -30.0, "amb.shop_room": -32.0, "amb.hana_room": -38.0}


def _short(recipe: str) -> str:
    return recipe.replace(".", "_")


def _layer(recipe: str) -> str:
    fam = recipe.split(".")[0]
    return fam if fam in GAIN else "sfx"


def _registry_items() -> list[dict]:
    out = []
    for name, e in sorted(synth.REGISTRY.items()):
        for s in e["serves"]:
            m = _ENTRY.match(s)
            if not m:
                continue
            where, mid, kind, flag = m.groups()
            after = re.search(r"\bafter f(\d+)", mid)
            frames = [int(x.group(1)) for x in _FRAME.finditer(re.sub(r"\bafter f\d+", "", mid))]
            out.append({"recipe": name, "where": where, "kind": kind, "frames": frames, "after": int(after.group(1)) if after else None,
                        "text": s, "flag": flag or "", "mid": mid})
    return out


def scaffold(project: Project, out: Path | None = None, force: bool = False) -> dict:  # noqa: C901
    loaded = project.load()
    if not loaded.shots:
        raise FMError("no shots: nothing to scaffold from")
    ctx = build_context(project, loaded)
    target = Path(out) if out else project.dir / AUDIO_CUES_PATH
    if target.exists() and not force:
        raise FMError(f"{target} exists; the sound-designer owns it (pass --out elsewhere, or --force to overwrite)")
    table, events = ctx.table, ctx.events
    notes: list[str] = []
    items = []
    for it in _registry_items():
        if "/" in it["where"]:
            notes.append(f"registry line '{it['text']}' names several shots: not scaffolded (place it by hand)")
            continue
        if it["where"] in table or it["where"] in ctx.scenes:
            items.append(it)
    conflicts = _conflicts(items)
    items = [it for it in items if "CONFLICT" not in it["text"]]      # an open ruling is a conflict entry, never a cue

    cues: list[dict] = []
    beds_in: list[tuple] = []          # (recipe, where, text)
    silence_abs: list[tuple] = []      # (id, from, to, shot, text)
    used_ratchet: set[str] = set()

    def sound_events(sid):
        return [e for e in events.get(sid, []) if e["kind"] == "sound"]

    # ---- silence spans first (beds and cues are cut around them)
    for it in items:
        if it["recipe"] == "amb.silence" and it["where"] in table:
            sid, row = it["where"], table[it["where"]]
            a = it["after"] if it["after"] is not None else (it["frames"][0] if it["frames"] else 0)
            silence_abs.append((f"sil_{sid}" + (f"_f{a}" if a else ""), row["start"] + a, row["start"] + row["frames"], sid, it["text"]))
    for it in items:
        if it["recipe"] in BED_RECIPES:
            beds_in.append((it["recipe"], it["where"], it["text"]))

    # ---- cues
    seen_ids: set[str] = set()

    def new_id(base: str) -> str:
        i, n = base, 2
        while i in seen_ids:
            i, n = f"{base}_{n}", n + 1
        seen_ids.add(i)
        return i

    def at_for(sid, f):
        """(at dict, note) for shot-local frame f: the named sound event at f when one exists."""
        evs = [e for e in sound_events(sid) if e["f"] == f]
        if evs:
            e = evs[0]
            same = [x for x in sound_events(sid) if x["id"] == e["id"]]
            at = {"event": e["id"]}
            if len(same) > 1:
                at["nth"] = same.index(e)
            return at, None
        return {"frame": f}, "no anim event at this frame: ask the animation-director for one so sync survives retiming"

    groups: dict[tuple[str, str], list[dict]] = {}
    for it in items:
        if it["recipe"] == "amb.silence" or it["recipe"] in BED_RECIPES or it["where"] not in table:
            continue
        rec = ALIAS.get(it["recipe"], it["recipe"])
        groups.setdefault((it["where"], rec), []).append(it)

    for (sid, rec), its in sorted(groups.items()):
        row = table[sid]
        frames_n = row["frames"]
        e = synth.REGISTRY[rec]
        layer = _layer(rec)
        base = {"shot": sid, "recipe": rec, "gain_db": GAIN[layer]}
        # ratchet: every handle_top, from the events, never hand-typed
        if rec == "crank.click" and any(x["id"] == "handle_top" for x in sound_events(sid)):
            if sid in used_ratchet:
                continue
            used_ratchet.add(sid)
            cues.append({"id": new_id(f"cue_{sid}_ratchet"), **base, "at": {"event": "handle_top", "each": True},
                         "rationale": "Scaffold: the ratchet pulse, one click per derived handle_top event (audio.ratchet phase lock).",
                         "note": "; ".join(i["text"] for i in its)})
            continue
        frames = sorted({f for i in its for f in i["frames"]})
        boards = [i for i in its if not i["frames"]]
        if rec in MERGE_HITS and frames:
            f0, rest = frames[0], frames[1:]
            at, note = at_for(sid, f0)
            c = {"id": new_id(f"cue_{sid}_{_short(rec)}"), **base, "at": at, "hits": rest,
                 "rationale": "Scaffold: one cue from the first sync frame; the later frames are the recipe's own timing (`hits`).",
                 "note": "; ".join(i["text"] for i in its) + (f"; {note}" if note else "")}
            cues.append(c)
            continue
        for i in its:
            for f in i["frames"]:
                if f >= frames_n:
                    notes.append(f"{sid}: registry line '{i['text']}' names f{f} beyond the shot ({frames_n} frames): skipped")
                    continue
                at, note = at_for(sid, f)
                c = {"id": new_id(f"cue_{sid}_{_short(rec)}_f{f}"), **base, "at": at,
                     "rationale": f"Scaffold: from the shot's sound_sync line ({i['text']}); sound-designer to confirm.",
                     "note": i["text"] + (f"; {note}" if note else "")}
                if rec.startswith("hum.") and "stop" in i["mid"] and f > 0:
                    c["at"], c["duration_f"] = {"frame": 0}, float(f)
                    c["fade_out_f"] = float(min(2, f))
                    c["note"] = i["text"] + "; hum runs from f0 and ends where the sync line says it stops"
                elif i["kind"] == "sync" and f + e["default_duration"] * synth.FPS > frames_n + 1e-6:
                    c["tail_ok"] = True
                cues.append(c)
        for i in boards:
            dur = e["default_duration"] * synth.FPS
            c = {"id": new_id(f"cue_{sid}_{_short(rec)}"), **base, "at": {"frame": 0},
                 "rationale": f"Scaffold: from the STORYBOARD Sound line ({i['text']}); frame unknown (board line).",
                 "note": i["text"] + "; frame 0 is a placeholder position: the sound-designer sets the real frame"}
            if dur > frames_n:
                c["duration_f"] = float(frames_n)
                c["fade_out_f"] = float(min(4, frames_n))
                c["note"] += f"; trimmed to the shot ({frames_n} f)"
            cues.append(c)

    # ---- silence: cut or push so that nothing overlaps (each choice is recorded on the span)
    sil_out = []
    for sid_, a, b, sid, text in silence_abs:
        row = table[sid]
        note = text
        moved = True
        while moved:
            moved = False
            for c in cues:
                if c["shot"] != sid:
                    continue
                cs = (row["start"] + (c["at"].get("frame", 0) if "frame" in c["at"] else _event_f(events, sid, c["at"])))
                d = c.get("duration_f") or synth.REGISTRY[c["recipe"]]["default_duration"] * synth.FPS
                if c["at"].get("each"):
                    continue
                if cs < b and cs + d > a:
                    if cs < a:
                        c["duration_f"] = float(a - cs)
                        c["fade_out_f"] = float(min(2, a - cs))
                        c.pop("tail_ok", None)
                        c["note"] = (c.get("note") or "") + f"; cut at the start of silence {sid_}"
                    else:
                        a = min(b - 1, int(-(-(cs + d) // 1)))
                        note += f"; span starts after cue {c['id']} ends (canon span begins at its onset): confirm"
                        moved = True
        sil_out.append({"id": sid_, "shot": sid, "from_f": int(a - row["start"]),
                        "canon": "audio.silence_map", "note": note,
                        "rationale": "Scaffold: from the registry's silence line for this shot."})

    # ---- beds: shot-level beds win over scene beds; everything is cut around silence
    def subtract(iv, cuts):
        out = [iv]
        for cs, ce in cuts:
            nxt = []
            for a, b in out:
                if ce <= a or cs >= b:
                    nxt.append((a, b))
                    continue
                if cs > a:
                    nxt.append((a, cs))
                if ce < b:
                    nxt.append((ce, b))
            out = nxt
        return [(a, b) for a, b in out if b - a >= 1]

    sil_iv = [(a, b) for _, a, b, _, _ in silence_abs]
    beds: list[dict] = []
    shot_bed_iv: dict[str, list] = {}
    for rec, where, text in beds_in:
        if where in table:
            row = table[where]
            for k, (a, b) in enumerate(subtract((row["start"], row["start"] + row["frames"]), sil_iv)):
                d = {"id": new_id(f"bed_{where}_{_short(rec)}" + (f"_{k + 1}" if k else "")), "shot": where, "recipe": rec,
                     "gain_db": BED_GAIN[rec], "xfade_f": 4.0, "rationale": f"Scaffold: from the STORYBOARD/registry line ({text}).", "note": text}
                if a != row["start"]:
                    d["from_f"] = int(a - row["start"])
                if b != row["start"] + row["frames"]:
                    d["to_f"] = int(b - row["start"])
                beds.append(d)
                shot_bed_iv.setdefault(loaded.shots[where].spec.scene_id, []).append((a, b))
    for rec, where, text in beds_in:
        if where in ctx.scenes and where not in table:
            lo, hi = ctx.scenes[where]
            cuts = sil_iv + shot_bed_iv.get(where, [])
            for k, (a, b) in enumerate(subtract((lo, hi), cuts)):
                d = {"id": new_id(f"bed_{where}_{_short(rec)}" + (f"_{k + 1}" if k else "")), "scene": where, "recipe": rec,
                     "gain_db": BED_GAIN[rec], "xfade_f": 6.0, "rationale": f"Scaffold: from the STORYBOARD/registry line ({text}).", "note": text}
                if a != lo:
                    d["from_f"] = int(a - lo)
                if b != hi:
                    d["to_f"] = int(b - lo)
                beds.append(d)

    # ---- sync points the scaffold could not cover
    def cue_marks(c):
        row = table[c["shot"]]
        a = c["at"]
        if a.get("each"):
            return [e["f"] for e in sound_events(c["shot"]) if e["id"] == a["event"]]
        f = a["frame"] if "frame" in a else _event_f(events, c["shot"], a)
        return [f] + list(c.get("hits", []))
    for sid in sorted(table):
        spec = loaded.shots[sid].spec
        line = (spec.animation or {}).get("sound_sync") if isinstance(spec.animation, dict) else None
        marks = [m for c in cues if c["shot"] == sid for m in cue_marks(c)]
        need = {("sound_sync", f) for f in sync_points(line)} | {(f"event '{e['id']}'", e["f"]) for e in sound_events(sid)}
        for why, f in sorted(need, key=lambda x: x[1]):
            if not any(abs(m - f) <= 1 for m in marks):
                notes.append(f"{sid} f{f} ({why}{': ' + line if why == 'sound_sync' else ''}): no scaffolded cue: needs a recipe, an asset, or a recording")

    # ---- human supply from placeholders
    ph: dict[str, list[str]] = {}
    for c in cues:
        if synth.REGISTRY[c["recipe"]]["placeholder"]:
            ph.setdefault(c["recipe"], []).append(c["shot"])
    supply = [{"sound": r, "need": synth.REGISTRY[r]["desc"], "shots": sorted(set(s)),
               "source": "recorded" if r.startswith("body.") else "licensed", "licence": "UNKNOWN", "status": "NEEDED"}
              for r, s in sorted(ph.items())]

    refs = [f"artifact:{loaded.anims[s].meta.id}" for s in sorted({c["shot"] for c in cues} | {b.get("shot", "") for b in beds}) if s in loaded.anims]
    refs += [f"shot:{s}" for s in sorted({c["shot"] for c in cues} | {b["shot"] for b in beds if "shot" in b})]
    doc = {"fm": {"id": AUDIO_CUES_ID, "kind": "audio_cues", "phase": "ANIMATION_PREVIEW", "status": "PROPOSED",
                  "owner_role": "sound-designer", "derived_from": [{"ref": r} for r in refs],
                  "summary": "SCAFFOLD skeleton from sound_sync lines, anim events and the synth registry; the sound-designer edits it."},
           "mix": {"integrated_lufs": -16.0, "lufs_tolerance": 1.0, "true_peak_dbtp": -1.0, "silence_floor_db": -50.0,
                   "sample_rate": 48000, "bit_depth": 24, "channels": 2, "master_gain_db": 0.0},
           "cues": cues, "beds": beds, "silence": sil_out, "human_supply": supply, "conflicts": conflicts,
           "scaffold_notes": notes}
    write_yaml(target, doc)
    return {"out": str(target), "cues": len(cues), "beds": len(beds), "silence": len(sil_out), "human_supply": len(supply),
            "notes": len(notes)}


def _event_f(events: dict, sid: str, at: dict) -> int:
    evs = [e for e in events.get(sid, []) if e["id"] == at["event"]]
    return evs[at.get("nth", 0)]["f"] if evs else 0


def _conflicts(items: list[dict]) -> list[dict]:
    """Registry lines that flag an open ruling (CONFLICT D4) become conflict entries for the human."""
    out = []
    for it in items:
        if "CONFLICT" in it["text"]:
            out.append({"shots": [it["where"]], "storyboard": it["text"], "shot_file": "see the shot's sound_sync",
                        "assumption": "follow the shot file (no cue scaffolded from the board line is authoritative)"})
    return out
