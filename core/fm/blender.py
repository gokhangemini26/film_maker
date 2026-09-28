"""Blender version gate. Every build/render path calls `require_blender()`
first; a mismatched series is refused, never silently used."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import BlenderVersionError
from .io import load_yaml

_VERSION_RE = re.compile(r"Blender\s+(\d+)\.(\d+)(?:\.(\d+))?\s*(LTS)?")


@dataclass(frozen=True)
class BlenderInfo:
    executable: str
    version: str
    series: str
    lts: bool


def load_config(repo: Path) -> dict:
    cfg = (load_yaml(repo / "config" / "blender.yaml") or {}).get("blender", {})
    if os.environ.get("FM_BLENDER"):
        cfg["executable"] = os.environ["FM_BLENDER"]
    return cfg


def parse_version(output: str) -> tuple[str, str, bool]:
    m = _VERSION_RE.search(output)
    if not m:
        raise BlenderVersionError(f"could not read a Blender version from: {output[:200]!r}")
    major, minor, patch, lts = m.groups()
    version = f"{major}.{minor}.{patch or 0}"
    return version, f"{major}.{minor}", bool(lts)


def probe(executable: str, timeout_s: float = 60) -> str:
    if not Path(executable).exists():
        raise BlenderVersionError(f"Blender executable not found: {executable} "
                                  "(set blender.executable in config/blender.yaml or FM_BLENDER)")
    try:
        out = subprocess.run([executable, "--version"], capture_output=True, text=True,
                             timeout=timeout_s)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BlenderVersionError(f"failed to run {executable} --version: {exc}") from exc
    return out.stdout + out.stderr


def require_blender(repo: Path, *, _probe=probe) -> BlenderInfo:
    cfg = load_config(repo)
    exe = cfg.get("executable")
    required = str(cfg.get("required_series", "")).strip()
    if not exe or not required:
        raise BlenderVersionError("config/blender.yaml must set blender.executable and required_series")
    if cfg.get("on_mismatch", "refuse") != "refuse":
        raise BlenderVersionError("only on_mismatch: refuse is supported")
    version, series, lts = parse_version(_probe(exe, cfg.get("version_probe_timeout_s", 60)))
    if series != required:
        raise BlenderVersionError(
            f"Blender {version} found at {exe}, but this pipeline is pinned to {required}.x. "
            "Refusing to continue. Install the pinned series or update config/blender.yaml "
            "deliberately (and re-validate the pipeline).")
    return BlenderInfo(exe, version, series, lts)
