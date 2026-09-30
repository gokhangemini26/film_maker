"""`fm audio synth` and `fm audio mix` (M6 task E5): render the cue sheet to a sample-exact 48 kHz stereo mix.

Everything is deterministic: identical cue sheet + identical library files => identical bytes. The mixer never
hides problems (no limiter, no normalisation): the master gain is an explicit number in `mix.master_gain_db`,
and `fm qa audio` reports the suggestion that would reach the loudness target.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .audio import mix as M
from .audio import synth
from .audiocues import AudioContext, Placement, placements_json, read_asset, resolve_cues
from .errors import FMError
from .io import write_json
from .ops import record_derived
from .project import Project

MIX_DIR = "12_post/audio"
MIX_WAV = "mix_48k_stereo.wav"
MIX_REPORT = "mix_report.json"
LIB_DIR = "12_post/audio/lib"


# ------------------------------------------------------------------ synth library
def synth_library(project: Project, out: Path | None = None, only: list[str] | None = None,
                  seed: int = 0, bits: int = 24) -> dict:
    """Render registry recipes (default duration, seed 0) to WAV files. Writes only into `out`
    (default `12_post/audio/lib/`): one WAV per recipe plus `manifest.json`."""
    names = sorted(synth.REGISTRY) if not only else list(only)
    bad = [n for n in names if n not in synth.REGISTRY]
    if bad:
        raise FMError(f"unknown recipe(s): {', '.join(bad)} (see `fm audio list`)")
    out = Path(out) if out else project.dir / LIB_DIR
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in names:
        e = synth.REGISTRY[n]
        x = synth.render(n, e["default_duration"], seed, {})
        M.write_wav(out / f"{n}.wav", x, synth.SR, bits)
        rows.append({"recipe": n, "file": f"{n}.wav", "seed": seed, "duration_s": e["default_duration"],
                     "placeholder": e["placeholder"], "channels": e["channels"], **M.measure(x)})
    write_json(out / "manifest.json", {"schema": "fm.audio_lib/1", "sample_rate": synth.SR, "bit_depth": bits, "items": rows})
    return {"out": str(out), "rendered": names}


# ------------------------------------------------------------------ mix
def _audio_for(p: Placement, repo: Path) -> np.ndarray:
    if p.recipe:
        return synth.render_frames(p.recipe, p.duration_f, p.seed, p.params)
    asset = read_asset(repo, p.asset)
    x, sr = M.read_wav(asset["_file"])
    if sr != synth.SR:
        raise FMError(f"asset '{p.asset}': sample rate {sr} Hz, the mix needs {synth.SR} Hz (resample the file first)")
    return x


def build_timeline(ctx: AudioContext, repo: Path) -> M.Timeline:
    """Render every placement onto a `Timeline` (stems by layer). Cues first, then beds, each in id order."""
    tl = M.Timeline(ctx.total_frames)
    order = sorted(ctx.placements, key=lambda p: (p.kind != "bed", p.start_f, p.id))
    for p in order:
        audio = _audio_for(p, repo)
        if p.kind == "bed":
            tl.add_bed(p.layer, audio, p.start_f, p.end_f, p.xfade_f, p.gain_db, p.pan, label=p.id)
        else:
            tl.add_cue(p.layer, audio, p.start_f, p.gain_db, p.pan, p.fade_in_f, p.fade_out_f, 0.0,
                       end_frame=p.end_f if p.duration_f is not None else None, label=p.id)
    return tl


def mix_project(project: Project) -> dict:
    """Render `12_post/AUDIO_CUES.yaml` to `12_post/audio/`: master, one stem per layer, `mix_report.json`;
    record the `audio:mix` derived node (deps: the cue sheet and every shot's resolved/shot node)."""
    loaded = project.load()
    if not loaded.audio_cues:
        raise FMError("no audio_cues artifact (12_post/AUDIO_CUES.yaml): nothing to mix (`fm audio scaffold` builds a skeleton)")
    ctx = resolve_cues(project, loaded)
    errs = [f"{c} {w}: {m}" for lvl, c, w, m in ctx.issues if lvl == "ERROR"]
    if errs:
        raise FMError(f"the cue sheet has {len(errs)} AUDIO error(s); fix them first (`fm validate`): " + "; ".join(errs[:4])
                      + (" ..." if len(errs) > 4 else ""))
    if not ctx.placements:
        raise FMError("the cue sheet has no cues or beds: nothing to mix")
    cues = ctx.cues
    tl = build_timeline(ctx, project.repo)
    g = np.float32(M.db_to_gain(cues.mix.master_gain_db))
    for name in tl.stems:
        tl.stems[name] = (tl.stems[name] * g).astype(np.float32)
    master = tl.master()
    n = ctx.total_frames * M.SPF
    assert master.shape == (n, 2)

    out = project.dir / MIX_DIR
    out.mkdir(parents=True, exist_ok=True)
    bits = int(cues.mix.bit_depth)
    stems = {}
    for name in sorted(tl.stems):
        M.write_wav(out / f"stem_{name}.wav", tl.stems[name], synth.SR, bits)
        stems[name] = f"stem_{name}.wav"
    wav = out / MIX_WAV
    M.write_wav(wav, master, synth.SR, bits)

    meas = M.measure(master)
    meas["peak_float"] = float(np.max(np.abs(master))) if master.size else 0.0
    delta = round(cues.mix.integrated_lufs - meas["lufs_approx"], 1) if meas["lufs_approx"] > -100 else None
    by_id = {t["label"]: t for t in tl.placements}
    plc = []
    for p in ctx.placements:
        row = p.to_json()
        t = by_id.get(p.id, {})
        row["start_sample"], row["stop_sample"] = t.get("start"), t.get("stop")
        plc.append(row)
    placeholders = sorted({p.recipe or p.asset for p in ctx.placements if p.placeholder})
    report = {
        "schema": "fm.audio_mix/1", "cues_hash": ctx.item.hash, "cues_file": project.rel(ctx.item.path),
        "total_frames": ctx.total_frames, "samples": int(n), "sample_rate": synth.SR, "channels": 2, "bit_depth": bits,
        "master_gain_db": cues.mix.master_gain_db, "measure": meas, "stems": stems,
        "lufs_delta_to_target_db": delta,
        "suggested_master_gain_db": round(cues.mix.master_gain_db + delta, 1) if delta is not None else None,
        "placeholders": placeholders, "placements": plc,
        "silence": [{"id": s.id, "from_f": s.from_f, "to_f": s.to_f, "floor_db": s.floor_db} for s in ctx.silence],
    }
    rp = out / MIX_REPORT
    write_json(rp, report)

    deps = [ctx.item.ref]
    for sid in sorted({p.shot for p in ctx.placements if p.shot}):
        deps.append(f"resolved:{sid}" if f"resolved:{sid}" in loaded.derived else f"shot:{sid}")
    rec = record_derived(project, "audio:mix", deps, file=wav, producer="fm.audio.mix")
    return {"wav": project.rel(wav), "report": project.rel(rp), "stems": sorted(stems), "samples": int(n),
            "placements": len(plc), "measure": meas, "suggested_master_gain_db": report["suggested_master_gain_db"],
            "derived": rec.ref, "placeholders": placeholders}
