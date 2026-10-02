"""Render-engine setup for the OPT-IN cinematic profiles: Cycles, device choice and the AI denoiser.

`fm blender preview|frames|playblast|final --profile <name>` exports the profile as JSON in the environment variable
FM_RENDER_PROFILE, but ONLY when the profile's engine is CYCLES (core/fm/renderprofile.py). `preview.setup_render` then
calls `apply_from_env`. With no variable set (every default profile, every EEVEE film such as last_signal) nothing here
runs and no property of the scene is touched.

Denoiser policy (`denoiser: oidn | optix | auto | none`):
  oidn   Intel Open Image Denoise (CPU, any machine; the realistic default on a Windows ARM64 laptop). Falls back to none
         when this Blender build has no OIDN.
  optix  NVIDIA OptiX denoiser. Needs an OptiX-capable NVIDIA GPU and `device: optix|auto`. Otherwise falls back to oidn,
         then to none.
  auto   optix when an OptiX device is in use, else oidn, else none.
Whatever happens, one log line `FM_DENOISER requested=... used=... reason=...` says what was actually used.

The planners (`plan_device`, `plan_denoiser`) are pure Python and unit-tested without Blender; `configure` is the only part
that needs bpy and was exercised on the bpy 5.0.1 module (CPU), not on the pinned Blender 5.2.1.
"""
from __future__ import annotations

import json
import os

ENV = "FM_RENDER_PROFILE"
GPU_ORDER = ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI")
DENOISER_ENUM = {"oidn": "OPENIMAGEDENOISE", "optix": "OPTIX"}


class RenderEngineError(ValueError):
    """The profile asks for something that cannot be honoured and has no safe fallback."""


def profile_from_env(environ=None) -> dict | None:
    raw = (environ if environ is not None else os.environ).get(ENV)
    if not raw:
        return None
    try:
        prof = json.loads(raw)
    except ValueError as exc:
        raise RenderEngineError(f"{ENV} is not valid JSON: {exc}") from exc
    if not isinstance(prof, dict) or str(prof.get("engine", "")).upper() != "CYCLES":
        return None
    return prof


# ------------------------------------------------------------------------------------------------ pure planners
def plan_device(requested: str, gpu_types: set[str]) -> tuple[str, str]:
    """(compute device type or 'CPU', reason). `gpu_types` are the GPU backends that have at least one device."""
    req = str(requested or "auto").lower()
    if req == "cpu":
        return "CPU", "requested cpu"
    if req == "auto":
        for t in GPU_ORDER:
            if t in gpu_types:
                return t, f"auto picked {t}"
        return "CPU", "auto: no GPU device found"
    want = req.upper()
    if want in gpu_types:
        return want, f"requested {req}"
    return "CPU", f"requested {req} but no such device is available; using CPU"


def plan_denoiser(requested: str, device_used: str, oidn_available: bool) -> tuple[str, str]:
    """(none | oidn | optix, reason). Fallback order optix -> oidn -> none."""
    req = str(requested or "oidn").lower()
    if req == "none":
        return "none", "requested none"
    if req in ("optix", "auto") and device_used == "OPTIX":
        return "optix", f"requested {req}; OptiX device in use"
    if req == "optix":
        why = "optix needs an NVIDIA OptiX device (device: optix|auto)"
        return ("oidn", why + "; fell back to oidn") if oidn_available else ("none", why + "; oidn unavailable too, denoising off")
    if req in ("oidn", "auto"):
        if oidn_available:
            return "oidn", "requested oidn" if req == "oidn" else "auto: no OptiX device, using oidn"
        return "none", f"requested {req} but this Blender build has no OpenImageDenoise; denoising off"
    raise RenderEngineError(f"unknown denoiser '{requested}' (none, oidn, optix, auto)")


# ------------------------------------------------------------------------------------------------ bpy side
def _gpu_types(bpy) -> set[str]:
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except (KeyError, AttributeError):
        return set()
    try:
        prefs.get_devices()
    except Exception:  # noqa: BLE001 - older/newer API: the devices list may already be populated
        pass
    try:
        return {d.type for d in prefs.devices if d.type != "CPU"}
    except Exception:  # noqa: BLE001
        return set()


def _use_device(bpy, scene, dev: str) -> None:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    if dev == "CPU":
        scene.cycles.device = "CPU"
        return
    prefs.compute_device_type = dev
    try:
        prefs.get_devices()
    except Exception:  # noqa: BLE001
        pass
    for d in prefs.devices:
        d.use = d.type in (dev, "CPU")
    scene.cycles.device = "GPU"


def _set_denoiser(scene, choice: str) -> bool:
    """Set the Cycles denoiser; False when this build/device refuses the enum value (the caller falls back)."""
    if choice == "none":
        scene.cycles.use_denoising = False
        return True
    try:
        scene.cycles.denoiser = DENOISER_ENUM[choice]
    except (TypeError, ValueError):
        return False
    scene.cycles.use_denoising = True
    return True


def configure(scene, profile: dict, log=print) -> dict:
    """Apply a normalised Cycles profile (core/fm/renderprofile.cycles_settings) to `scene`. Returns what was set."""
    import bpy

    scene.render.engine = "CYCLES"
    cy = scene.cycles
    try:
        cy.feature_set = "SUPPORTED"
    except (TypeError, AttributeError):
        pass
    gpu = _gpu_types(bpy)
    dev, dev_reason = plan_device(profile.get("device", "auto"), gpu)
    try:
        _use_device(bpy, scene, dev)
    except Exception as exc:  # noqa: BLE001 - a broken GPU stack must not stop a CPU render
        dev, dev_reason = "CPU", f"could not enable {dev} ({type(exc).__name__}: {exc}); using CPU"
        scene.cycles.device = "CPU"
    cy.samples = int(profile.get("samples", 64))
    cy.use_adaptive_sampling = bool(profile.get("adaptive_sampling", True))
    if cy.use_adaptive_sampling:
        cy.adaptive_threshold = float(profile.get("adaptive_threshold", 0.01))
        cy.adaptive_min_samples = int(profile.get("adaptive_min_samples", 0))
    if profile.get("max_bounces") is not None:
        cy.max_bounces = int(profile["max_bounces"])
    if profile.get("clamp_indirect") is not None:
        cy.sample_clamp_indirect = float(profile["clamp_indirect"])
    scene.render.use_motion_blur = bool(profile.get("motion_blur", False))
    depth = profile.get("color_depth")
    if depth:
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_depth = str(int(depth))

    requested = str(profile.get("denoiser", "oidn")).lower()
    oidn_ok = _set_denoiser(scene, "oidn") if requested != "none" else False
    used, why = plan_denoiser(requested, dev, oidn_ok)
    if used != "none" and not _set_denoiser(scene, used):       # e.g. OptiX named but the build refuses it
        used, why = ("oidn", why + "; OptiX enum refused, using oidn") if oidn_ok and used == "optix" else ("none", why + "; enum refused")
        _set_denoiser(scene, used)
    if used == "none":
        scene.cycles.use_denoising = False
    log(f"FM_DENOISER requested={requested} used={used} reason={why}")
    report = {"engine": "CYCLES", "device": dev, "device_reason": dev_reason, "samples": cy.samples,
              "adaptive": cy.use_adaptive_sampling, "denoiser_requested": requested, "denoiser_used": used,
              "denoiser_reason": why, "gpu_backends_seen": sorted(gpu)}
    log("FM_RENDER_ENGINE " + " ".join(f"{k}={v}" for k, v in report.items()))
    return report


def apply_from_env(scene, log=print) -> dict | None:
    """Called by preview.setup_render. No-op (returns None, touches nothing) unless FM_RENDER_PROFILE selects Cycles."""
    prof = profile_from_env()
    if prof is None:
        return None
    return configure(scene, prof, log)


def is_cycles_scene(scene) -> bool:
    return getattr(scene.render, "engine", "") == "CYCLES"
