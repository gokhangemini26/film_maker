"""Production phases, approval gates and what each phase must deliver.

Gates are attached to the phase that ends with human review. A gate's
approval records the content hash of every artifact/shot it covers and
locks the canon domains it owns. Nothing downstream may advance past a
gate that is unapproved or has drifted since approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PHASES: tuple[str, ...] = (
    "IDEA",
    "BRIEF",
    "CREATIVE_DIRECTION",
    "STORY",
    "SCREENPLAY",
    "WORLD_CHARACTERS",
    "LOOK",
    "CINEMATOGRAPHY",
    "STORYBOARD",
    "ASSET_PREP",
    "BLENDER_BUILD",
    "PREVIEW",
    "ANIMATION",
    "ANIMATION_PREVIEW",
    "FINAL_RENDER",
    "POST",
    "DELIVERY",
    "COMPLETE",
)


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    closes_phase: str            # the phase whose exit this gate controls
    covers_phases: tuple[str, ...]  # artifacts/shots of these phases are approved by it
    locks_domains: tuple[str, ...]  # canon domains locked on approval
    covers_shots: bool = False


GATES: dict[str, Gate] = {
    g.id: g
    for g in (
        Gate("G1", "Creative direction", "CREATIVE_DIRECTION", ("BRIEF", "CREATIVE_DIRECTION"),
             ("intent", "tone")),
        Gate("G2", "Story and screenplay", "SCREENPLAY", ("STORY", "SCREENPLAY"), ("story",)),
        Gate("G3", "World and characters", "WORLD_CHARACTERS", ("WORLD_CHARACTERS",),
             ("world", "characters")),
        Gate("G4", "Visual direction (style lock)", "LOOK", ("LOOK",), ("look",)),
        Gate("G5", "Storyboard and shots", "STORYBOARD", ("CINEMATOGRAPHY", "STORYBOARD"),
             ("camera", "continuity"), covers_shots=True),
        Gate("G6", "First Blender preview", "PREVIEW", ("ASSET_PREP", "BLENDER_BUILD", "PREVIEW"),
             ()),
        Gate("G7", "Animation preview", "ANIMATION_PREVIEW", ("ANIMATION", "ANIMATION_PREVIEW"),
             ("animation", "audio")),
        Gate("G8", "Final render", "FINAL_RENDER", ("FINAL_RENDER",), ()),
    )
}
GATE_FOR_PHASE = {g.closes_phase: g for g in GATES.values()}


@dataclass(frozen=True)
class PhaseContract:
    """Deliverables required before a phase can be submitted for review."""

    required: tuple[str, ...] = ()   # project-relative paths
    min_shots: int = 0
    notes: str = ""
    extra: dict = field(default_factory=dict)


CONTRACTS: dict[str, PhaseContract] = {
    "BRIEF": PhaseContract(("00_brief/brief.yaml",)),
    "CREATIVE_DIRECTION": PhaseContract(("00_brief/CREATIVE_DIRECTION.md",)),
    "STORY": PhaseContract(("01_story/STORY_BIBLE.md", "01_story/STORY_STRUCTURE.md")),
    "SCREENPLAY": PhaseContract(("02_screenplay/SCREENPLAY.md",)),
    "WORLD_CHARACTERS": PhaseContract(
        ("03_world/WORLD_BIBLE.md", "03_world/ART_DIRECTION_BIBLE.md",
         "04_characters/CHARACTER_BIBLE.md")),
    "LOOK": PhaseContract(
        ("05_look/VISUAL_BIBLE.md", "05_look/COLOR_BIBLE.md", "05_look/LIGHTING_BIBLE.md")),
    "CINEMATOGRAPHY": PhaseContract(("06_cinematography/CINEMATOGRAPHY_BIBLE.md",)),
    "STORYBOARD": PhaseContract(
        ("07_storyboard/STORYBOARD.md", "07_storyboard/SHOT_LIST.md"), min_shots=1),
    # Production phases get their contracts as their tooling lands (M3+).
}

PROJECT_DIRS = (
    "00_brief", "01_story", "02_screenplay", "03_world", "04_characters", "05_look",
    "06_cinematography", "07_storyboard", "08_shots", "09_animation", "10_blender",
    "11_render", "12_post", "13_delivery", "qa", "canon", "changes", "references", ".fm",
    ".fm/derived",
)


def phase_index(phase: str) -> int:
    return PHASES.index(phase)


def next_phase(phase: str) -> str | None:
    i = phase_index(phase)
    return PHASES[i + 1] if i + 1 < len(PHASES) else None


def gates_before(phase: str) -> list[Gate]:
    """Gates whose phase lies strictly before `phase` (must be approved to be in `phase`)."""
    i = phase_index(phase)
    return [g for g in GATES.values() if phase_index(g.closes_phase) < i]
