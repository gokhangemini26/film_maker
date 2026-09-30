"""Run the Blender-side builders (blender/fm_blender) for a project.

Two backends:
  exe  - the pinned Blender executable (config/blender.yaml). The only backend whose output counts as
         evidence for G6. Every run goes through `require_blender()` first.
  bpy  - the `bpy` Python module, for fast DRAFT previews in environments without the pinned Blender
         (e.g. the cloud workspace). Never version-pinned, so it must be requested explicitly (--draft)
         and its records say "draft".
One Blender process per shot: a single long EEVEE process produced corrupted colours on Windows ARM.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .blender import require_blender
from .errors import FMError
from .ops import record_derived
from .project import Project
from .resolve import resolve

PREVIEW_DIR = "10_blender/previews"
BUILDERS = Path(__file__).resolve().parents[2] / "blender"   # builder code ships with fm itself


def _shot_ids(project: Project, only: list[str] | None) -> list[str]:
    files = sorted((project.dir / "09_resolved").glob("SC*.json"))
    ids = [f.stem for f in files]
    if only:
        missing = [s for s in only if s not in ids]
        if missing:
            raise FMError(f"no resolved shot(s): {', '.join(missing)}")
        ids = only
    return ids


def preview(project: Project, repo: Path, *, shots: list[str] | None = None, width: int = 768,
            draft: bool = False, jobs: int = 1, timeout_s: int = 600) -> dict:
    resolve(project, "film")  # make sure 09_resolved is current (no-op when unchanged)
    ids = _shot_ids(project, shots)
    resolved = project.dir / "09_resolved"
    out = project.dir / PREVIEW_DIR
    logs = project.dir / "10_blender" / "logs"
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    if draft:
        if importlib.util.find_spec("bpy") is None:
            raise FMError("--draft needs the 'bpy' Python module (pip install bpy)")
        import bpy  # noqa: F401
        version = f"bpy {bpy.app.version_string} (DRAFT, not the pinned series)"
        cmd = lambda sid: [sys.executable, str(BUILDERS / "run_cloud.py"), str(resolved), str(out), sid, str(width)]  # noqa: E731
    else:
        info = require_blender(repo)
        version = f"blender {info.version}"
        cmd = lambda sid: [info.executable, "-b", "--factory-startup", "--python",  # noqa: E731
                           str(BUILDERS / "run_preview.py"), "--", str(resolved), str(out), sid, str(width)]

    def one(sid: str):
        r = subprocess.run(cmd(sid), capture_output=True, text=True, timeout=timeout_s)
        (logs / f"preview_{sid}.log").write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
        png = out / f"{sid}.png"
        return sid, ("FM_OK" in r.stdout and png.exists()), png

    with ThreadPoolExecutor(max(1, jobs)) as ex:
        results = list(ex.map(one, ids))
    failed = [s for s, ok, _ in results if not ok]
    for sid, ok, png in results:
        if ok:
            record_derived(project, f"render:preview_{sid}", [f"resolved:{sid}"], file=png,
                           producer="fm.blender.preview",
                           note=f"{version}; {'draft' if draft else 'pinned'}; width {width}")
    report = {"rendered": [s for s, ok, _ in results if ok], "failed": failed, "backend": version, "draft": draft}
    (project.dir / "10_blender" / "preview_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


def _fm_blender():
    """Import the pure-python parts of fm_blender (assets/reconcile) without bpy."""
    if str(BUILDERS) not in sys.path:
        sys.path.insert(0, str(BUILDERS))
    from fm_blender import assets, reconcile
    return assets, reconcile


def assets_report(project: Project) -> dict:
    """ASSET_PREP contract check: assets each shot needs (world.*, ui.*) vs what the builders can produce."""
    assets, _ = _fm_blender()
    resolved = project.dir / "09_resolved"
    film = json.loads((resolved / "film.json").read_text(encoding="utf-8"))
    shots = {s: json.loads((resolved / f"{s}.json").read_text(encoding="utf-8")) for s in _shot_ids(project, None)}
    return assets.check(shots, film.get("canon", {}))


def build(project: Project, repo: Path, *, draft: bool = False, timeout_s: int = 600, blend: Path | None = None) -> dict:
    """Build/update the ONE persistent .blend (10_blender/<slug>.blend), reconciled by per-unit hash, and record a
    derived `blend:<slug>` node. The .blend is regenerable from 09_resolved (Blender is the engine, not the database)."""
    resolve(project, "film")
    resolved = project.dir / "09_resolved"
    blend = blend or project.dir / "10_blender" / f"{project.slug}.blend"
    logs = project.dir / "10_blender" / "logs"
    blend.parent.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    report_path = project.dir / "10_blender" / "build_report.json"
    script = str(BUILDERS / "run_build.py")
    if draft:
        if importlib.util.find_spec("bpy") is None:
            raise FMError("--draft needs the 'bpy' Python module (pip install bpy)")
        import bpy  # noqa: F401
        version = f"bpy {bpy.app.version_string} (DRAFT, not the pinned series)"
        cmd = [sys.executable, script, str(resolved), str(blend), str(report_path)]
    else:
        info = require_blender(repo)
        version = f"blender {info.version}"
        cmd = [info.executable, "-b", "--factory-startup", "--python", script, "--", str(resolved), str(blend), str(report_path)]
    report_path.unlink(missing_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    (logs / "build.log").write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    if "FM_OK build" not in r.stdout or not blend.exists() or not report_path.exists():
        raise FMError(f"blender build failed (see {project.rel(logs / 'build.log')}): {(r.stderr or r.stdout)[-400:]}")
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    refs = ["resolved:film"] + [f"resolved:{s}" for s in _shot_ids(project, None)]
    c = rep["counts"]
    record_derived(project, f"blend:{project.slug}", refs, file=blend, producer="fm.blender.build",
                   note=f"{version}; {'draft' if draft else 'pinned'}; built {c['built']}, unchanged {c['unchanged']}, removed {c['removed']}")
    rep.update({"backend": version, "draft": draft, "derived": f"blend:{project.slug}"})
    report_path.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return rep


# ---------------------------------------------------------------------------------------------------------- M6-lite
FRAMES_DIR = "10_blender/frames"
PLAYBLAST_DIR = "10_blender/playblast"


def _fm_framesel():
    """The pure frame helpers (frame selection, contact strips) from the builders package; no bpy needed."""
    if str(BUILDERS) not in sys.path:
        sys.path.insert(0, str(BUILDERS))
    from fm_blender import framesel
    return framesel


def scope_shots(project: Project, scope: str | None) -> list[str]:
    """Shot ids for a scope: None/film (all), shot:ID[,ID], shots:A..B, scene:SC01, or a bare shot id."""
    ids = _shot_ids(project, None)
    if not scope or scope == "film":
        return ids
    kind, _, val = scope.partition(":")
    if not val:
        kind, val = "shot", scope
    if kind == "shot":
        return _shot_ids(project, [v.strip() for v in val.split(",") if v.strip()])
    if kind == "scene":
        out = [s for s in ids if s.startswith(val + "_")]
    elif kind == "shots" and ".." in val:
        a, b = val.split("..", 1)
        out = [s for s in ids if a <= s <= b]
    else:
        raise FMError(f"unsupported scope '{scope}' for frames/playblast (use shot:ID, scene:SC01, shots:A..B or film)")
    if not out:
        raise FMError(f"scope '{scope}' matches no resolved shot")
    return out


def _frame_cmd(repo: Path, *, draft: bool, resolved: Path, out: Path, sid: str, width: int, spec: str, stamp: bool,
               samples: int | None, fast: bool, resume: bool) -> tuple[list[str], str]:
    tail = [str(resolved), str(out), sid, str(width), spec, "stamp" if stamp else "no", str(samples or "-"), "fast" if fast else "-",
            "resume" if resume else "-"]
    script = str(BUILDERS / "run_frames.py")
    if draft:
        if importlib.util.find_spec("bpy") is None:
            raise FMError("--draft needs the 'bpy' Python module (pip install bpy)")
        import bpy  # noqa: F401
        return [sys.executable, script, *tail], f"bpy {bpy.app.version_string} (DRAFT, not the pinned series)"
    info = require_blender(repo)
    return [info.executable, "-b", "--factory-startup", "--python", script, "--", *tail], f"blender {info.version}"


def _render_shots(project: Project, repo: Path, ids: list[str], out: Path, *, specs: dict[str, str], width: int, draft: bool,
                  jobs: int, timeout_s: int, stamp: bool, samples: int | None, fast: bool, resume: bool, tag: str) -> tuple[list[str], list[str], str]:
    resolved = project.dir / "09_resolved"
    logs = project.dir / "10_blender" / "logs"
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    cmds = {sid: _frame_cmd(repo, draft=draft, resolved=resolved, out=out, sid=sid, width=width, spec=specs[sid], stamp=stamp,
                            samples=samples, fast=fast, resume=resume) for sid in ids}
    version = next(iter(cmds.values()))[1] if cmds else ""

    def one(sid: str):
        r = subprocess.run(cmds[sid][0], capture_output=True, text=True, timeout=timeout_s)
        (logs / f"{tag}_{sid}.log").write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
        return sid, "FM_OK" in r.stdout

    with ThreadPoolExecutor(max(1, jobs)) as ex:
        results = list(ex.map(one, ids))
    return [s for s, ok in results if ok], [s for s, ok in results if not ok], version


def frames(project: Project, repo: Path, *, scope: str | None = None, frames: str | None = None, every_key: bool = False,
           preview_frame: bool = False, draft: bool = False, width: int = 480, jobs: int = 1, timeout_s: int = 1800,
           samples: int | None = None) -> dict:
    """Render chosen frames of the animated shots into 10_blender/frames/<SHOT>/%04d.png plus a contact strip per shot
    (strip.png). Frames: --frames 12,f24,30-40 | --every-key (the anim file's preview_frames) | --preview-frame (the shot's
    designated still); several may be combined, and with none of them the mid-shot frame is rendered.
    Nothing is recorded in the project state: frames are working images for review, never evidence."""
    ids = scope_shots(project, scope)
    sel = _fm_framesel()
    resolved = project.dir / "09_resolved"
    specs, missing = {}, []
    for sid in ids:
        shot = json.loads((resolved / f"{sid}.json").read_text(encoding="utf-8"))
        if not shot.get("motion"):
            missing.append(sid)
            continue
        specs[sid] = ",".join(str(f) for f in sel.select_frames(shot, frames=frames, every_key=every_key, preview_frame=preview_frame))
    ids = [s for s in ids if s in specs]
    if not ids:
        raise FMError("no shot in scope has a motion block (no anim file): nothing to render" + (f" ({', '.join(missing)})" if missing else ""))
    out = project.dir / FRAMES_DIR
    ok, failed, version = _render_shots(project, repo, ids, out, specs=specs, width=width, draft=draft, jobs=jobs, timeout_s=timeout_s,
                                        stamp=False, samples=samples, fast=False, resume=False, tag="frames")
    strips = {}
    for sid in ok:
        nums = [int(x) for x in specs[sid].split(",")]
        paths = [out / sid / ("%04d.png" % f) for f in nums]
        paths = [p for p in paths if p.exists()]
        if paths:
            strips[sid] = str(sel.contact_strip([str(p) for p in paths], str(out / sid / "strip.png"),
                                                labels=[f"{sid} f{int(p.stem)}" for p in paths], title=f"{sid}  ({version})"))
    rep = {"rendered": {s: specs[s] for s in ok}, "failed": failed, "skipped_no_motion": missing, "strips": strips,
           "backend": version, "draft": draft, "dir": str(out)}
    return rep


def _ffmpeg() -> str:
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise FMError("ffmpeg not found (put it on PATH or pip install imageio-ffmpeg)") from exc


def encode_mp4(frames_dir: Path, out_mp4: Path, fps: int, *, first: int = 0) -> Path:
    """<frames_dir>/%04d.png -> h264 mp4 (yuv420p, even dimensions)."""
    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(first), "-i", str(frames_dir / "%04d.png"),
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out_mp4)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out_mp4.exists():
        raise FMError(f"ffmpeg failed for {out_mp4.name}: {r.stderr[-300:]}")
    return out_mp4


def playblast(project: Project, repo: Path, *, scope: str | None = None, draft: bool = False, width: int = 640, jobs: int = 1,
              timeout_s: int = 3600, resume: bool = False, samples: int | None = None) -> dict:
    """Every frame of each shot in scope -> 10_blender/playblast/<SHOT>/%04d.png (shot id and frame number stamped in a corner)
    -> <SHOT>.mp4, and film.mp4 (concat, silent) when the whole film was rendered. --resume keeps frames already on disk.
    Draft (cloud bpy) uses cheaper shadows and 4 samples; the pinned route uses 8 samples (M6_SCOPE 2.6)."""
    ids = scope_shots(project, scope)
    resolved = project.dir / "09_resolved"
    shots = {sid: json.loads((resolved / f"{sid}.json").read_text(encoding="utf-8")) for sid in ids}
    film = json.loads((resolved / "film.json").read_text(encoding="utf-8"))
    fps = int(film["format"]["fps"])
    todo = [s for s in ids if shots[s].get("motion")]
    if not todo:
        raise FMError("no shot in scope has a motion block (no anim file): nothing to render")
    out = project.dir / PLAYBLAST_DIR
    ok, failed, version = _render_shots(project, repo, todo, out, specs={s: "all" for s in todo}, width=width, draft=draft, jobs=jobs,
                                        timeout_s=timeout_s, stamp=True, samples=samples or (4 if draft else 8), fast=draft,
                                        resume=resume, tag="playblast")
    mp4s = {}
    for sid in ok:
        n = int(shots[sid]["frames"]["count"])
        d = out / sid
        have = len(list(d.glob("[0-9][0-9][0-9][0-9].png")))
        if have < n:
            failed.append(sid)
            continue
        mp4s[sid] = str(encode_mp4(d, out / f"{sid}.mp4", fps))
    film_mp4 = None
    every = _shot_ids(project, None)
    if not failed and set(mp4s) == set(every):
        lst = out / "film.ffconcat"
        lst.write_text("".join(f"file '{sid}.mp4'\n" for sid in every), encoding="utf-8")
        cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "film.mp4")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            film_mp4 = str(out / "film.mp4")
    return {"rendered": sorted(mp4s), "failed": sorted(set(failed)), "mp4": mp4s, "film": film_mp4, "backend": version, "draft": draft,
            "skipped_no_motion": [s for s in ids if s not in todo], "dir": str(out)}
