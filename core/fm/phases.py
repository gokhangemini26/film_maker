"""Production phases, approval gates and what each phase must deliver.

Gates are attached to the phase that ends with human review. A gate's
approval records the content hash of every artifact/shot it covers and
locks the canon domains it owns. Nothing downstream may advance past a
gate that is unapproved or has drifted since approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .roles import REVIEW_FOR_GATE

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
        # M6: G7 approves the animation AND the audio and post plan (animatic with sound).
        # Approving it does not authorize the final render (`fm authorize final-render`).
        Gate("G7", "Animation, audio and post plan", "ANIMATION_PREVIEW",
             ("ANIMATION", "ANIMATION_PREVIEW"), ("animation", "audio")),
        Gate("G8", "Final render", "FINAL_RENDER", ("FINAL_RENDER",), ()),
    )
}
GATE_FOR_PHASE = {g.closes_phase: g for g in GATES.values()}


@dataclass(frozen=True)
class PhaseContract:
    """Deliverables required before a phase can be submitted for review."""

    required: tuple[str, ...] = ()   # project-relative paths of managed artifacts (need an `fm:` block)
    min_shots: int = 0
    notes: str = ""
    extra: dict = field(default_factory=dict)
    # M6 additions (all default empty, so earlier phases behave exactly as before):
    files: tuple[str, ...] = ()        # unmanaged deliverables (media, EDL, manifests): must exist
    per_shot: tuple[str, ...] = ()     # path templates with {shot}: one per shot spec must exist
    qa_reports: tuple[str, ...] = ()   # JSON reports that must exist with summary.fail == 0
    authorizations: tuple[str, ...] = ()  # human authorizations that must be in the ledger


# Files the M6 tools write (names are part of the contract; see docs/WORKFLOW.md).
ANIM_FILE = "09_animation/{shot}.anim.yaml"
MOTION_REPORT = "qa/motion_report.json"
AUDIO_REPORT = "qa/audio_report.json"
FINAL_FRAMES_REPORT = "qa/final_frames_report.json"
DELIVERY_REPORT = "qa/delivery_report.json"

CONTRACTS: dict[str, PhaseContract] = {
    "BRIEF": PhaseContract(("00_brief/brief.yaml",)),
    "CREATIVE_DIRECTION": PhaseContract(("00_brief/CREATIVE_DIRECTION.md", REVIEW_FOR_GATE["G1"])),
    "STORY": PhaseContract(("01_story/STORY_BIBLE.md", "01_story/STORY_STRUCTURE.md")),
    "SCREENPLAY": PhaseContract(("02_screenplay/SCREENPLAY.md", "02_screenplay/SCENES.yaml",
                                 REVIEW_FOR_GATE["G2"])),
    "WORLD_CHARACTERS": PhaseContract(
        ("03_world/WORLD_BIBLE.md", "03_world/ART_DIRECTION_BIBLE.md",
         "04_characters/CHARACTER_BIBLE.md", REVIEW_FOR_GATE["G3"])),
    "LOOK": PhaseContract(
        ("05_look/VISUAL_BIBLE.md", "05_look/COLOR_BIBLE.md", "05_look/LIGHTING_BIBLE.md",
         REVIEW_FOR_GATE["G4"])),
    "CINEMATOGRAPHY": PhaseContract(("06_cinematography/CINEMATOGRAPHY_BIBLE.md",)),
    "STORYBOARD": PhaseContract(
        ("07_storyboard/STORYBOARD.md", "07_storyboard/SHOT_LIST.md", REVIEW_FOR_GATE["G5"]),
        min_shots=1),
    # Production phases get their contracts as their tooling lands (M3+).
    # ---- M6 (docs/M6_SCOPE.md 5.5). The anim/audio/motion tools land in later tasks; the
    # contracts name the files they will write so `fm submit` / `fm advance` can already enforce them.
    "ANIMATION": PhaseContract(
        ("09_animation/ANIMATION_BIBLE.md",),
        per_shot=(ANIM_FILE,),
        qa_reports=(MOTION_REPORT,),
        notes="an anim file for every shot and `fm qa motion` with no FAIL, before ANIMATION_PREVIEW"),
    "ANIMATION_PREVIEW": PhaseContract(
        ("12_post/AUDIO_BIBLE.md", "12_post/AUDIO_CUES.yaml", "12_post/EDIT_PLAN.md",
         "12_post/POST_PLAN.md", REVIEW_FOR_GATE["G7"]),
        files=("10_blender/playblast/film.mp4", "12_post/audio/mix_48k_stereo.wav",
               "12_post/animatic.mp4", "12_post/EDIT.edl"),
        per_shot=(ANIM_FILE,),
        qa_reports=(MOTION_REPORT, AUDIO_REPORT),
        notes="G7: silent playblast, 48 kHz stereo mix, animatic with sound and EDL; motion and audio QA without FAIL"),
    "FINAL_RENDER": PhaseContract(
        (REVIEW_FOR_GATE["G8"],),
        files=("11_render/final/MANIFEST.json",),
        qa_reports=(FINAL_FRAMES_REPORT,),
        authorizations=("final-render",),
        notes="G8: human-authorized render of every frame with the pinned Blender, frame QA without FAIL"),
    "POST": PhaseContract(
        files=("13_delivery/MANIFEST.json",),
        qa_reports=(DELIVERY_REPORT,),
        notes="no gate (G9 Delivery is deferred): master assembled, `fm qa delivery` without FAIL"),
}

PROJECT_DIRS = (
    "00_brief", "01_story", "02_screenplay", "03_world", "04_characters", "05_look",
    "06_cinematography", "07_storyboard", "08_shots", "09_animation", "10_blender",
    "11_render", "12_post", "13_delivery", "qa", "qa/reviews", "canon", "changes", "references", ".fm",
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
