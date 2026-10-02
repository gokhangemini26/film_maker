"""Render profiles (config/render_profiles.yaml + projects/<film>/config/render.yaml) and the opt-in Cycles settings.

`load_profile` is what `fm blender final` always used; the project file overrides the repository file per key, and (new) a
project may also define a whole profile of its own. `validate_profile` only checks the keys it knows; a profile that has
none of the Cycles keys is returned exactly as written, so the default EEVEE profiles behave as before.

Only a profile whose engine is CYCLES produces `subprocess_env`: the Blender-side render_engine module reads the
FM_RENDER_PROFILE variable, and with no variable nothing about the scene changes (docs/CINEMATIC_PIPELINE.md).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import FMError
from .io import load_yaml
from .project import Project

ENV = "FM_RENDER_PROFILE"
LIBRARY_ENV = "FM_LIBRARY_DIR"
ENGINES = ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH")
DENOISERS = ("none", "oidn", "optix", "auto")
DEVICES = ("auto", "cpu", "optix", "cuda", "hip", "metal", "oneapi")
CYCLES_DEFAULTS = {"samples": 64, "adaptive_sampling": True, "adaptive_threshold": 0.01, "adaptive_min_samples": 0,
                   "denoiser": "oidn", "device": "auto", "max_bounces": None, "clamp_indirect": None, "color_depth": None,
                   "motion_blur": False}
CYCLES_KEYS = tuple(CYCLES_DEFAULTS)


def load_profile(project: Project, repo: Path, name: str = "final") -> dict:
    """Render profile `name` from config/render_profiles.yaml, overridden key by key by projects/<film>/config/render.yaml."""
    base = (load_yaml(repo / "config" / "render_profiles.yaml") or {}).get("profiles", {})
    override_file = project.dir / "config" / "render.yaml"
    over = ((load_yaml(override_file) or {}).get("profiles") or {}) if override_file.exists() else {}
    if name not in base and name not in over:
        known = ", ".join(sorted(set(base) | set(over)))
        raise FMError(f"no render profile '{name}' in config/render_profiles.yaml or the project's config/render.yaml (known: {known})")
    prof = dict(base.get(name) or {})
    prof.update(over.get(name) or {})
    validate_profile(prof, name)
    return prof


def validate_profile(prof: dict, name: str = "?") -> None:
    eng = prof.get("engine")
    if eng is not None and str(eng).upper() not in ENGINES:
        raise FMError(f"render profile '{name}': engine {eng!r} must be one of {', '.join(ENGINES)}")
    if "denoiser" in prof and str(prof["denoiser"]).lower() not in DENOISERS:
        raise FMError(f"render profile '{name}': denoiser {prof['denoiser']!r} must be one of {', '.join(DENOISERS)}")
    if "device" in prof and str(prof["device"]).lower() not in DEVICES:
        raise FMError(f"render profile '{name}': device {prof['device']!r} must be one of {', '.join(DEVICES)}")
    if prof.get("color_depth") not in (None, 8, 16):
        raise FMError(f"render profile '{name}': color_depth must be 8 or 16")
    for k in ("samples", "adaptive_min_samples", "max_bounces"):
        if k in prof and prof[k] is not None and (not isinstance(prof[k], int) or isinstance(prof[k], bool) or prof[k] < 0):
            raise FMError(f"render profile '{name}': {k} must be a non-negative integer")
    if "samples" in prof and prof["samples"] is not None and prof["samples"] < 1:
        raise FMError(f"render profile '{name}': samples must be >= 1")
    if "adaptive_threshold" in prof and not (isinstance(prof["adaptive_threshold"], (int, float)) and 0 < prof["adaptive_threshold"] <= 1):
        raise FMError(f"render profile '{name}': adaptive_threshold must be in (0, 1]")
    if str(eng or "").upper() != "CYCLES":
        used = [k for k in ("denoiser", "device", "adaptive_sampling", "adaptive_threshold", "adaptive_min_samples", "max_bounces",
                            "clamp_indirect", "color_depth") if k in prof]
        if used:
            raise FMError(f"render profile '{name}': {', '.join(used)} only apply to engine: CYCLES (this profile's engine is {eng})")


def is_cycles(prof: dict) -> bool:
    return str(prof.get("engine", "")).upper() == "CYCLES"


def cycles_settings(prof: dict, samples: int | None = None) -> dict | None:
    """The normalised Cycles settings sent to Blender (None for a non-Cycles profile). `samples` is a CLI override."""
    if not is_cycles(prof):
        return None
    out = {"engine": "CYCLES"}
    for k, d in CYCLES_DEFAULTS.items():
        out[k] = prof.get(k, d)
    out["denoiser"] = str(out["denoiser"]).lower()
    out["device"] = str(out["device"]).lower()
    out["adaptive_sampling"] = bool(out["adaptive_sampling"])
    out["motion_blur"] = bool(out["motion_blur"])
    if samples:
        out["samples"] = int(samples)
    return out


def subprocess_env(prof: dict | None, repo: Path, samples: int | None = None) -> dict | None:
    """Environment for the Blender subprocess. None (inherit as before) for a missing or non-Cycles profile, unless the parent
    environment itself carries FM_RENDER_PROFILE, which is then removed so an EEVEE run can never pick it up."""
    cy = cycles_settings(prof, samples) if prof else None
    if cy is None:
        if ENV in os.environ:
            return {k: v for k, v in os.environ.items() if k != ENV}
        return None
    env = dict(os.environ)
    env[ENV] = json.dumps(cy, sort_keys=True)
    env.setdefault(LIBRARY_ENV, str(repo / "library"))
    return env
