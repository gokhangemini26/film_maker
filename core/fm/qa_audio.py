"""`fm qa audio` (M6 task E5): deterministic sync, silence and level checks on the rendered mix.

Report shape follows `qa_stills` (`{"summary": {shots, fail, warn}, "rows": [{shot, findings: [[level, msg]]}]}`)
and is written to `qa/audio_report.json`. Creative judgement (does the hum death land) is the human's at G7:
nothing here says the mix "sounds good", only whether it is structurally what the cue sheet, the animation
events and the canon require.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import numpy as np

from .audio import mix as M
from .audio import synth
from .audiocues import licence_of, read_asset, resolve_cues, sync_points
from .audiorun import MIX_DIR, MIX_REPORT, MIX_WAV
from .ops import record_derived
from .project import Project

REPORT_REL = "qa/audio_report.json"
GAP_DB = -90.0


def ffmpeg_loudness(wav) -> dict | None:
    """Integrated loudness and true peak by ffmpeg `ebur128` (the delivery reference), or None."""
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "-hide_banner", "-nostats", "-i", str(wav), "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    tail = r.stderr.split("Summary:")[-1]
    i = re.search(r"\bI:\s+(-?[\d.]+)\s+LUFS", tail)
    pk = re.search(r"\bPeak:\s+(-?[\d.]+)\s+dBFS", tail)
    if not i:
        return None
    return {"lufs": float(i.group(1)), "true_peak_dbtp": float(pk.group(1)) if pk else None}


def _shot_of(where: str) -> str | None:
    m = re.search(r"SC\d{2,3}_SH\d{3,4}", where)
    return m.group(0) if m else None


def check(project: Project, use_ffmpeg: bool | None = None, final: bool = False) -> dict:  # noqa: C901
    loaded = project.load()
    rows: dict[str, list] = {}

    def add(shot: str, level: str, msg: str) -> None:
        rows.setdefault(shot, []).append([level, msg])

    report_extra: dict = {}
    if not loaded.audio_cues:
        add("FILM", "FAIL", "no audio_cues artifact (12_post/AUDIO_CUES.yaml)")
        return _write(project, loaded, rows, report_extra, [], final)
    ctx = resolve_cues(project, loaded)
    cues = ctx.cues
    for lvl, code, where, msg in ctx.issues:
        sev = {"ERROR": "FAIL", "WARN": "WARN", "INFO": "INFO"}[lvl]
        if code == "AUDIO_LICENCE" and final:
            sev = "FAIL"
        add(_shot_of(where) or "FILM", sev, f"{code} {where}: {msg}")

    mix_dir = project.dir / MIX_DIR
    wav_p, rep_p = mix_dir / MIX_WAV, mix_dir / MIX_REPORT
    if not wav_p.exists() or not rep_p.exists():
        add("FILM", "FAIL", f"no rendered mix ({MIX_DIR}/{MIX_WAV} and {MIX_REPORT}): run `fm audio mix`")
        return _write(project, loaded, rows, report_extra, _human(cues), final)
    rep = json.loads(rep_p.read_text(encoding="utf-8"))
    if rep.get("cues_hash") != ctx.item.hash:
        add("FILM", "FAIL", "the mix is stale: the cue sheet changed since `fm audio mix` (re-run it)")
    x, sr = M.read_wav(wav_p)
    x = x if x.ndim == 2 else np.stack([x, x], axis=1)
    want = ctx.total_frames * M.SPF

    # ---- duration / format
    if sr != synth.SR:
        add("FILM", "FAIL", f"sample rate {sr} Hz, expected {synth.SR}")
    if x.shape[0] != want:
        add("FILM", "FAIL", f"mix length {x.shape[0]} samples, expected exactly {want} ({ctx.total_frames} frames x {M.SPF})")

    # ---- sync: every audible event and every sound_sync frame has a placed cue within +-1 frame
    starts = [(t["start_sample"] / M.SPF, t) for t in rep.get("placements", [])
              if t.get("kind") == "cue" and t.get("start_sample") is not None]
    marks = list(starts)
    for t in rep.get("placements", []):
        if t.get("kind") == "cue" and t.get("start_sample") is not None:
            marks += [(h, t) for h in t.get("hits_f", [])]

    def covered(abs_f: float):
        return [t for s, t in marks if abs(s - abs_f) <= 1.0 + 1e-9]
    n_points = 0
    for sid, row in sorted(ctx.table.items()):
        pts: dict[int, list[str]] = {}
        for e in ctx.events.get(sid, []):
            if e["kind"] == "sound":
                pts.setdefault(e["f"], []).append(f"event '{e['id']}'")
        spec = loaded.shots[sid].spec
        line = (spec.animation or {}).get("sound_sync") if isinstance(spec.animation, dict) else None
        for f in sync_points(line):
            pts.setdefault(f, []).append("sound_sync")
        for f, why in sorted(pts.items()):
            n_points += 1
            if f >= row["frames"]:
                add(sid, "WARN", f"{' + '.join(why)} names f{f} but the shot has {row['frames']} frames")
                continue
            if not covered(row["start"] + f):
                add(sid, "FAIL", f"{' + '.join(why)} at f{f} has no cue within +-1 frame"
                    + (f" (sound_sync: {line})" if "sound_sync" in why else ""))
    report_extra["sync_points"] = n_points

    # ---- silence map: rendered RMS
    sil = []
    for s in ctx.silence:
        a, b = int(round(s.from_f * M.SPF)), int(round(s.to_f * M.SPF))
        db = M.rms_dbfs(x, a, b)
        sil.append({"id": s.id, "from_f": s.from_f, "to_f": s.to_f, "floor_db": s.floor_db, "rms_dbfs": round(db, 2)})
        if db > s.floor_db:
            add(s.shot or "FILM", "FAIL", f"silence '{s.id}' (film f{s.from_f:g}..{s.to_f:g}) measures {db:.1f} dBFS RMS, above its {s.floor_db:.0f} dBFS floor")
    report_extra["silence"] = sil

    # ---- gaps: digitally silent frames outside declared silence (usually a bug: the world is never silent)
    if x.shape[0] == want and want:
        per = np.mean(x.astype(np.float64).reshape(ctx.total_frames, M.SPF, 2) ** 2, axis=(1, 2))
        quiet = per < 10.0 ** (GAP_DB / 10.0)
        for s in ctx.silence:
            quiet[int(s.from_f):int(np.ceil(s.to_f))] = False
        for sid, row in ctx.table.items():
            idx = np.nonzero(quiet[row["start"]:row["start"] + row["frames"]])[0]
            if idx.size:
                add(sid, "WARN", f"{idx.size} frame(s) with no sound and no silence-map entry (first f{int(idx[0])}): the world is never digitally silent")

    # ---- levels
    mt = cues.mix
    m = M.measure(x)
    m["peak_float"] = rep.get("measure", {}).get("peak_float", m["peak_dbfs"])
    ff = ffmpeg_loudness(wav_p) if (use_ffmpeg is None or use_ffmpeg) else None
    if use_ffmpeg and ff is None:
        add("FILM", "WARN", "ffmpeg loudness measurement unavailable: using the built-in BS.1770 approximation")
    lufs = ff["lufs"] if ff else m["lufs_approx"]
    tp = (ff["true_peak_dbtp"] if ff and ff.get("true_peak_dbtp") is not None else m["true_peak_dbfs"])
    levels = {"integrated_lufs": lufs, "lufs_source": "ffmpeg-ebur128" if ff else "approx-bs1770", "lufs_approx": m["lufs_approx"],
              "true_peak_dbtp": tp, "sample_peak_dbfs": m["peak_dbfs"], "rms_dbfs": m["rms_dbfs"],
              "targets": {"integrated_lufs": mt.integrated_lufs, "lufs_tolerance": mt.lufs_tolerance, "true_peak_dbtp": mt.true_peak_dbtp}}
    if m["peak_float"] > 1.0 or float(np.max(np.abs(x))) >= 0.99999:
        add("FILM", "FAIL", f"clipping: master reaches {20 * np.log10(max(m['peak_float'], 1e-9)):.2f} dBFS (lower `mix.master_gain_db` or the loudest cue)")
    if tp > mt.true_peak_dbtp:
        add("FILM", "FAIL", f"true peak {tp:.2f} dBTP is above the {mt.true_peak_dbtp:.1f} dBTP target")
    if lufs < -100:
        add("FILM", "FAIL", "the mix is silent (no measurable loudness)")
    elif abs(lufs - mt.integrated_lufs) > mt.lufs_tolerance:
        delta = round(mt.integrated_lufs - lufs, 1)
        add("FILM", "FAIL", f"integrated loudness {lufs:.1f} LUFS is outside {mt.integrated_lufs:.0f} +-{mt.lufs_tolerance:g} LU "
            f"(suggested `mix.master_gain_db`: {round(mt.master_gain_db + delta, 1)}; check true peak after the change)")
        levels["suggested_master_gain_db"] = round(mt.master_gain_db + delta, 1)
    report_extra["levels"] = levels

    # ---- licences and placeholders (reported, never silent)
    lic, seen = [], set()
    for p in ctx.placements:
        if p.asset and p.asset not in seen:
            seen.add(p.asset)
            l = licence_of(read_asset(project.repo, p.asset))
            lic.append({"asset": p.asset, "licence": l})
            if l.upper() in ("", "UNKNOWN", "UNSPECIFIED", "TBD"):
                add("FILM", "FAIL" if final else "WARN", f"asset '{p.asset}' has licence UNKNOWN" + ("" if final else " (blocks final export)"))
    for h in cues.human_supply:
        if h.status == "SUPPLIED" and h.licence.upper() in ("", "UNKNOWN", "UNSPECIFIED", "TBD"):
            add("FILM", "FAIL" if final else "WARN", f"human-supplied '{h.sound}' has licence UNKNOWN" + ("" if final else " (blocks final export)"))
    report_extra["licences"] = lic
    ph = {}
    for p in ctx.placements:
        if p.placeholder:
            ph.setdefault(p.recipe or p.asset, []).append(p.owner)
    report_extra["placeholders"] = [{"sound": k, "cues": sorted(set(v))} for k, v in sorted(ph.items())]
    for k, v in sorted(ph.items()):
        add("FILM", "WARN", f"PLACEHOLDER {k} is in the mix ({len(set(v))} cue(s)): stands in until the human supplies the real sound")
    return _write(project, loaded, rows, report_extra, _human(cues), final)


def _human(cues) -> list[dict]:
    return [h.model_dump(mode="json") for h in cues.human_supply] if cues else []


def _write(project: Project, loaded, rows: dict, extra: dict, human: list[dict], final: bool) -> dict:
    order = ["FILM"] + sorted(k for k in rows if k != "FILM")
    out_rows = [{"shot": k, "findings": rows[k]} for k in order if k in rows]
    def count(sev): return sum(any(f[0] == sev for f in r["findings"]) for r in out_rows)
    summary = {"shots": sum(1 for r in out_rows if r["shot"] != "FILM"), "fail": count("FAIL"), "warn": count("WARN"),
               "info": count("INFO")}
    human_open = [h for h in human if h.get("status") == "NEEDED"]
    report = {"schema": "fm.qa_audio/1", "mode": "final" if final else "preview", "summary": summary, "rows": out_rows,
              **extra, "human_supply": human, "human_supply_open": len(human_open)}
    rp = project.dir / REPORT_REL
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    deps = [i.ref for i in loaded.audio_cues]
    if "audio:mix" in loaded.derived:
        deps.append("audio:mix")
    if deps:
        record_derived(project, "qa:audio", deps, file=rp, producer="fm.qa.audio")
    return report
