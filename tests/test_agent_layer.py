"""Structural checks for the agent layer (.claude/agents, skills, commands).

These cannot judge creative quality; they keep the layer consistent with the
deterministic core so that agents, skills, commands, schemas and permissions
never drift apart.
"""
import json
import re
from pathlib import Path

import pytest
import yaml

from fm.io import read_front_matter
from fm.roles import ARTIFACT_OWNERS, CANON_DOMAINS
from fm.schemas import ArtifactMeta, SceneIndex, ShotSpec

REPO = Path(__file__).resolve().parents[1]
CLAUDE = REPO / ".claude"

M2_AGENTS = {"creative-director", "story-architect", "screenwriter", "world-designer",
             "character-designer", "look-director", "cinematographer", "animation-director",
             "qa-supervisor"}
M3_AGENTS = {"blender-td"}
M6_AGENTS = {"sound-designer", "post-supervisor"}
DOMAIN_SKILLS = {"film-development", "story-development", "screenwriting", "world-building",
                 "production-design", "character-design", "visual-development", "color-design",
                 "lighting-design", "cinematography", "storyboarding", "animation-design",
                 "continuity-check", "creative-review", "blender-production", "sound-design",
                 "post-production"}
SUPPORT_SKILLS = {"film-conventions", "project-management"}
COMMANDS = {"film-new", "film-direction", "film-story", "film-script", "film-world", "film-look",
            "film-cinematography", "film-storyboard", "film-review", "film-continuity",
            "film-revise", "film-status", "film-next", "film-blender",
            "film-animate", "film-playblast", "film-audio", "film-post", "film-final", "film-export"}
SECTIONS = ("## Purpose", "## When to use", "## Required inputs", "## Process", "## Output format",
            "## Validation rules", "## Failure conditions", "## Examples")
HUMAN_ONLY = ("fm approve", "fm revise G", "fm reject", "fm authorize", "fm canon approve",
              "fm canon lock", "fm canon reject", "fm change approve", "fm change reject", "fm amend",
              "--sandbox-confirm")


ALL_AGENTS = M2_AGENTS | M3_AGENTS | M6_AGENTS


def fm_of(path):
    meta, body = read_front_matter(path)
    return meta, body


def agents():
    return {p.stem: fm_of(p) for p in sorted((CLAUDE / "agents").glob("*.md"))}


def skills():
    return {p.parent.name: fm_of(p) for p in sorted((CLAUDE / "skills").glob("*/SKILL.md"))}


def commands():
    return {p.stem: fm_of(p) for p in sorted((CLAUDE / "commands").glob("*.md"))}


def _tools(meta):
    t = meta.get("tools", "")
    return [x.strip() for x in (t if isinstance(t, list) else str(t).split(","))]


# ------------------------------------------------------------------ agents
def test_exactly_the_m2_agents():
    assert set(agents()) == ALL_AGENTS


@pytest.mark.parametrize("name", sorted(ALL_AGENTS))
def test_agent_definition(name):
    meta, body = agents()[name]
    assert meta["name"] == name
    assert len(meta["description"]) > 40
    tools = _tools(meta)
    assert "Agent" not in tools, "specialists must not spawn agents; the main session orchestrates"
    assert "Bash" in tools, "agents need fm stamp/validate"
    assert "film-conventions" in meta["skills"]
    for s in meta["skills"]:
        assert s in skills(), f"{name} preloads unknown skill {s}"
    assert "--sandbox-confirm" in body and "cannot approve" in body.lower()


def test_agent_models_match_config():
    cfg = yaml.safe_load((REPO / "config/models.yaml").read_text())
    for name, (meta, _) in agents().items():
        role_class = cfg["roles"][name]
        assert meta["model"] == cfg["models"][role_class]["model"], name
    assert set(cfg["roles"]) == ALL_AGENTS


def test_roles_known_to_core_have_agents():
    owners = set(ARTIFACT_OWNERS.values()) - {"executive-producer"}
    assert owners <= ALL_AGENTS
    assert set(CANON_DOMAINS) <= ALL_AGENTS


def test_writers_and_reviewer_tools():
    a = agents()
    assert "Write" not in _tools(a["animation-director"][0])       # edits shot files only
    assert "Edit" not in _tools(a["qa-supervisor"][0])             # writes its review, edits nothing


# ------------------------------------------------------------------ skills
def test_skill_set():
    assert set(skills()) == DOMAIN_SKILLS | SUPPORT_SKILLS


@pytest.mark.parametrize("name", sorted(DOMAIN_SKILLS | SUPPORT_SKILLS))
def test_skill_structure(name):
    meta, body = skills()[name]
    assert meta["name"] == name
    assert len(meta["description"]) > 40
    assert meta.get("user-invocable") is False, "domain skills stay out of the / menu"
    for section in SECTIONS:
        assert section in body, f"{name} missing '{section}'"


def test_conventions_references_exist():
    base = CLAUDE / "skills/film-conventions"
    for ref in ("ARTIFACT_CONVENTIONS.md", "CANON_PROTOCOL.md", "INTENT_AND_RATIONALE.md",
                "ORIGINALITY.md", "REVIEW_RUBRIC.md", "templates/SCENES.yaml",
                "templates/shot.shot.yaml", "templates/GATE_REVIEW.md", "templates/BRIEF_ANALYSIS.md"):
        assert (base / ref).exists(), ref


def test_templates_match_schemas():
    base = CLAUDE / "skills/film-conventions/templates"
    SceneIndex.model_validate(yaml.safe_load((base / "SCENES.yaml").read_text()))
    ShotSpec.model_validate(yaml.safe_load((base / "shot.shot.yaml").read_text()))
    for f in ("GATE_REVIEW.md", "BRIEF_ANALYSIS.md"):
        meta, _ = read_front_matter(base / f)
        ArtifactMeta.model_validate(meta["fm"])
    meta, _ = read_front_matter(base / "GATE_REVIEW.md")
    assert meta["verdict"] in ("PASS", "WARN", "FAIL")


# ------------------------------------------------------------------ commands
def test_command_set():
    assert set(commands()) == COMMANDS


@pytest.mark.parametrize("name", sorted(COMMANDS))
def test_command_is_thin_and_consistent(name):
    meta, body = commands()[name]
    assert len(meta["description"]) > 30
    assert len(body.strip().splitlines()) <= 35, "commands stay thin; logic lives in skills"
    allowed = meta.get("allowed-tools", "")
    for h in HUMAN_ONLY:
        assert h not in allowed, f"{name} pre-approves a human-only command: {h}"
    for ref in re.findall(r"`([a-z]+(?:-[a-z]+)+)`", body):
        if ref.startswith("film-") or ref in {"fm-status"}:
            continue
        assert ref in agents() or ref in skills(), f"{name} references unknown agent/skill '{ref}'"


def test_project_management_references_real_agents():
    _, body = skills()["project-management"]
    for ref in ("qa-supervisor",):
        assert ref in body and ref in agents()


# ------------------------------------------------------------------ permissions
def test_settings_block_human_actions():
    s = json.loads((CLAUDE / "settings.json").read_text())
    deny = " ".join(s["permissions"]["deny"])
    for h in ("fm approve", "fm authorize", "fm canon lock", "fm change approve", "--sandbox-confirm",
              "FM_ACTOR=", "state.yaml", ".fm/**", "changes/**"):
        assert h in deny, h
    allow = " ".join(s["permissions"]["allow"])
    for h in HUMAN_ONLY:
        assert h not in allow
    assert s["env"]["FM_ACTOR"].startswith("agent:")
