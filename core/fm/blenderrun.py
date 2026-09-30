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
