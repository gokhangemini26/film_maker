"""A tiny deterministic film ("Last Signal") used by the test-suite and the
M1 demo. It exercises every layer of the data model with placeholder
creative content — it is a fixture, not an example of good writing."""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from . import ops
from .io import write_front_matter, write_yaml
from .project import Project


@contextmanager
def as_actor(actor: str):
    old = os.environ.get("FM_ACTOR")
    os.environ["FM_ACTOR"] = actor
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("FM_ACTOR", None)
        else:
            os.environ["FM_ACTOR"] = old


AGENT = "agent:toy-writer"
HUMAN = "human:director"


def write_canon(project: Project, domain: str, entries: list[dict]) -> None:
    write_yaml(project.canon_dir / f"{domain}.yaml", {"domain": domain, "entries": entries})


def write_md(project: Project, rel: str, aid: str, kind: str, phase: str, deps: list[str],
             body: str, serves: list[str] | None = None) -> Path:
    path = project.dir / rel
    meta = {"fm": {"id": aid, "kind": kind, "phase": phase, "status": "PROPOSED",
                   "derived_from": [{"ref": d} for d in deps], "serves": serves or []},
            "title": kind.replace("_", " ").title()}
    write_front_matter(path, meta, body)
    return path


def write_shot(project: Project, shot_id: str, **fields) -> Path:
    scene = shot_id.split("_")[0]
    spec = {
        "shot_id": shot_id, "scene_id": scene, "sequence_id": "SQ01", "status": "PROPOSED",
        "duration_s": 4.0,
        "serves": ["intent.isolation"],
        "creative_intent": {
            "narrative_purpose": "Establish Mara alone in the city.",
            "emotional_purpose": "Loneliness.",
            "visual_purpose": "Small figure, large negative space.",
            "audience_effect": "The viewer feels her distance from everyone.",
        },
        "camera": {"lens_mm": 50, "height_m": 1.6, "movement": "static"},
        "rationale": {"camera": "Moderate compression separates her from the background "
                                "while keeping the street readable."},
        "characters": [{"id": "mara", "position": [0, 0, 0], "action": "walking"}],
        "environment": {"location": "old harbour street", "weather": "rain", "time_of_day": "night"},
        "derived_from": [{"ref": "artifact:shot_list"}],
    }
    spec.update(fields)
    path = project.shots_dir / f"{shot_id}.shot.yaml"
    write_yaml(path, spec)
    return path


# ---------------------------------------------------------------- per-phase content
def produce(project: Project, phase: str) -> None:
    P = project
    if phase == "BRIEF":
        import yaml
        brief_path = P.dir / "00_brief" / "brief.yaml"
        data = yaml.safe_load(brief_path.read_text(encoding="utf-8"))
        data["fields"].update({
            "concept": {"value": "A lone courier receives a message from someone presumed dead.", "status": "given"},
            "duration_s": {"value": 30, "status": "given"},
            "emotional_goal": {"value": "isolation turning into hope", "status": "given"},
            "color_palette": {"value": "muted blue with warm amber accents", "status": "given"},
            "fps": {"value": 24, "status": "assumed", "note": "cinema default"},
        })
        write_yaml(brief_path, data)
        write_canon(P, "intent", [
            {"id": "intent.isolation", "statement": "The protagonist should feel isolated.",
             "tag": "USER_REQUIREMENT", "source": "user"},
            {"id": "intent.hope", "statement": "The ending should open a small door of hope.",
             "tag": "USER_REQUIREMENT", "source": "user"},
        ])
    elif phase == "CREATIVE_DIRECTION":
        write_canon(P, "tone", [
            {"id": "tone.register", "statement": "Quiet, melancholic, restrained.",
             "rationale": "Restraint makes the final moment of hope land harder.",
             "serves": ["intent.isolation", "intent.hope"], "source": "agent:creative-director"},
        ])
        write_md(P, "00_brief/CREATIVE_DIRECTION.md", "creative_direction", "creative_direction",
                 "CREATIVE_DIRECTION", ["artifact:brief", "canon:intent.isolation", "canon:tone.register"],
                 "# Creative direction\n\nQuiet, rain-soaked, lonely; a single warm light at the end.\n",
                 serves=["intent.isolation", "intent.hope"])
    elif phase == "STORY":
        write_canon(P, "story", [
            {"id": "story.premise", "statement": "A courier finds a message from her dead brother.",
             "rationale": "A personal stake turns a delivery into a reckoning.",
             "serves": ["intent.hope"], "source": "agent:story-architect"},
        ])
        write_md(P, "01_story/STORY_BIBLE.md", "story_bible", "story_bible", "STORY",
                 ["artifact:creative_direction", "canon:story.premise"], "# Story bible\n\nPremise...\n")
        write_md(P, "01_story/STORY_STRUCTURE.md", "story_structure", "story_structure", "STORY",
                 ["artifact:story_bible"], "# Structure\n\n1. Walk. 2. Message. 3. Light.\n")
    elif phase == "SCREENPLAY":
        write_md(P, "02_screenplay/SCREENPLAY.md", "screenplay", "screenplay", "SCREENPLAY",
                 ["artifact:story_structure"], "EXT. HARBOUR STREET - NIGHT\n\nRain. MARA walks alone.\n")
    elif phase == "WORLD_CHARACTERS":
        write_canon(P, "world", [
            {"id": "world.city.district", "statement": "An old harbour district, half-abandoned.",
             "rationale": "Empty streets make her isolation visible.", "serves": ["intent.isolation"],
             "source": "agent:world-designer"},
        ])
        write_canon(P, "characters", [
            {"id": "characters.mara.identity", "statement": "Mara, 34, night courier.",
             "rationale": "A job done alone at night embodies isolation.", "serves": ["intent.isolation"],
             "source": "agent:character-designer"},
            {"id": "characters.mara.wardrobe.jacket", "statement": "Black waxed jacket.",
             "value": {"color": "#111111", "material": "waxed cotton"},
             "rationale": "Dark silhouette reads against wet, reflective streets.",
             "source": "agent:character-designer"},
            {"id": "characters.mara.representation", "statement": "Stylised proxy for the MVP.",
             "value": {"provider": "proxy", "height_m": 1.68},
             "rationale": "Proxies keep the pipeline reliable until a human character system is chosen.",
             "tag": "DECISION", "source": "agent:character-designer"},
        ])
        write_md(P, "03_world/WORLD_BIBLE.md", "world_bible", "world_bible", "WORLD_CHARACTERS",
                 ["canon:world.city.district"], "# World\n")
        write_md(P, "03_world/ART_DIRECTION_BIBLE.md", "art_direction_bible", "art_direction_bible",
                 "WORLD_CHARACTERS", ["artifact:world_bible"], "# Art direction\n")
        write_md(P, "04_characters/CHARACTER_BIBLE.md", "character_bible", "character_bible",
                 "WORLD_CHARACTERS", ["canon:characters.mara.identity", "canon:characters.mara.wardrobe.jacket"],
                 "# Characters\n\nMara wears a black waxed jacket.\n")
    elif phase == "LOOK":
        write_canon(P, "look", [
            {"id": "look.color.primary", "statement": "Muted night blue.", "value": "#1B2A3A",
             "rationale": "Cold ambient colour isolates her.", "serves": ["intent.isolation"],
             "source": "agent:look-director"},
            {"id": "look.color.accent", "statement": "Warm amber practicals.", "value": "#E0A040",
             "rationale": "Warmth is reserved for hope.", "serves": ["intent.hope"],
             "source": "agent:look-director"},
        ])
        for name, aid in (("VISUAL_BIBLE", "visual_bible"), ("COLOR_BIBLE", "color_bible"),
                          ("LIGHTING_BIBLE", "lighting_bible")):
            write_md(P, f"05_look/{name}.md", aid, aid, "LOOK",
                     ["canon:look.color.primary", "canon:look.color.accent"], f"# {name}\n")
    elif phase == "CINEMATOGRAPHY":
        write_canon(P, "camera", [
            {"id": "camera.lens_set", "statement": "Primes: 24, 35, 50, 85mm.", "value": [24, 35, 50, 85],
             "rationale": "A small prime set keeps the camera language consistent.",
             "source": "agent:cinematographer"},
        ])
        write_md(P, "06_cinematography/CINEMATOGRAPHY_BIBLE.md", "cinematography_bible",
                 "cinematography_bible", "CINEMATOGRAPHY",
                 ["canon:camera.lens_set", "artifact:visual_bible"], "# Cinematography\n")
    elif phase == "STORYBOARD":
        write_canon(P, "continuity", [
            {"id": "continuity.sc01.weather", "statement": "SC01: rain, night.",
             "value": {"weather": "rain", "time": "night"}, "applies_to": ["SC01"],
             "tag": "FACT", "source": "agent:cinematographer"},
        ])
        write_md(P, "07_storyboard/STORYBOARD.md", "storyboard", "storyboard", "STORYBOARD",
                 ["artifact:screenplay", "artifact:cinematography_bible"], "# Storyboard\n")
        write_md(P, "07_storyboard/SHOT_LIST.md", "shot_list", "shot_list", "STORYBOARD",
                 ["artifact:storyboard"], "# Shot list\n")
        write_shot(P, "SC01_SH010")
        write_shot(P, "SC01_SH020", camera={"lens_mm": 85, "movement": "slow push"},
                   rationale={"camera": "Long lens compresses rain between us and her."})
        write_shot(P, "SC02_SH010", characters=[], sequence_id="SQ02",
                   creative_intent={"narrative_purpose": "Empty street after she leaves."},
                   rationale={"camera": "Same lens as SH010 for a clean match."})
    stamp_all(P)


def stamp_all(project: Project) -> None:
    """Stamp every artifact and shot, upstream first (repeat until settled)."""
    for _ in range(4):
        loaded = project.load()
        for item in [*loaded.artifacts.values(), *loaded.shots.values()]:
            try:
                ops.stamp(project, item.ref if item.ref.startswith("artifact:") else project.rel(item.path),
                          note="fixture restamp", _refresh=False)
            except Exception:  # noqa: BLE001 - dependency not produced yet
                pass
    ops.refresh(project)


def drive(project: Project, until_phase: str) -> None:
    """Produce content and walk the state machine, approving every gate as
    the (simulated, sandbox) human, until `until_phase` is the current phase."""
    from .phases import GATE_FOR_PHASE, PHASES
    state = ops.load_state(project)
    while PHASES.index(state.phase) < PHASES.index(until_phase):
        with as_actor(AGENT):
            produce(project, state.phase)
        gate = GATE_FOR_PHASE.get(state.phase)
        if gate:
            with as_actor(AGENT):
                ops.submit(project)
            with as_actor(HUMAN):
                ops.decide_gate(project, gate.id, "approved", "fixture approval", sandbox_confirm=True)
        if state.phase == "ANIMATION_PREVIEW":
            with as_actor(HUMAN):
                ops.authorize(project, "final-render", sandbox_confirm=True)
        with as_actor(AGENT):
            state = ops.advance(project)
