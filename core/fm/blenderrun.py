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
