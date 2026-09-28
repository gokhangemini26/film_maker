"""Extension points reserved for future integrations (not implemented in M1).

The core project model never depends on any of these. Each integration
reads resolved, validated files and returns files + a DerivedRecord, so a
new provider (another LLM, a vision model, an image/video generator, a VRM
or MPFB character system, mocap, a render farm) plugs in without changing
canon, shots, the ledger or the dependency graph.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CharacterProvider(Protocol):
    """Turns a character's canon (identity, proportions, wardrobe,
    `representation` block) into a rig-ready asset. MVP provider: stylised
    proxies. Future: MPFB/MakeHuman, VRM, generated meshes, scanned assets."""

    name: str

    def supports(self, representation: dict[str, Any]) -> bool: ...

    def build(self, character_id: str, canon: dict[str, Any], out_dir: Path) -> Path: ...


@runtime_checkable
class MotionSource(Protocol):
    """Keyframed/procedural motion, BVH/FBX mocap, or generated motion."""

    name: str

    def motion_for(self, shot_spec: dict[str, Any], character_id: str, out_dir: Path) -> Path: ...


@runtime_checkable
class RenderBackend(Protocol):
    """Local headless Blender (M3), later a render farm. Must refuse final
    renders without a ledger authorization and must verify the Blender pin."""

    name: str

    def render(self, blend: Path, profile: dict[str, Any], out_dir: Path) -> dict[str, Any]: ...


@runtime_checkable
class VisionReviewer(Protocol):
    """Produces advisory visual QA findings with frame evidence. Its output
    can never pass a gate or mark QA as passed on its own."""

    name: str

    def review(self, frames: list[Path], shot_spec: dict[str, Any], canon: dict[str, Any]
               ) -> list[dict[str, Any]]: ...


@runtime_checkable
class ModelRunner(Protocol):
    """Runs a creative/technical role with a given model. Today: Claude Code
    subagents. Contract: read project files, write PROPOSED files, then call
    `fm validate`."""

    name: str

    def run_role(self, role: str, task: str, project_dir: Path) -> int: ...
