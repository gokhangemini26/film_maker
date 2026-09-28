"""M2 additions to the deterministic core: gate reviews, scene index,
intent coverage, continuity checks, colour validation, ownership warnings."""
import pytest
import yaml

from fm import authority, ops, testing
from fm.continuity import check_continuity
from fm.errors import ValidationFailed
from fm.intent import intent_coverage, unserved_decisions
from fm.io import read_front_matter, write_front_matter, write_yaml
from fm.validate import validate


def _codes(project, level=None):
    return {f.code for f in validate(project).findings if level is None or f.level == level}


def _to_g1_content(p):
    testing.drive(p, "CREATIVE_DIRECTION")
    with testing.as_actor(testing.AGENT):
        testing.produce(p, "CREATIVE_DIRECTION")


# ------------------------------------------------------------------ gate reviews
def test_submit_requires_review(sandbox):
    _to_g1_content(sandbox)
    (sandbox.dir / "qa/reviews/G1_REVIEW.md").unlink()
    with pytest.raises(ValidationFailed, match="G1_REVIEW.md"):
        ops.submit(sandbox)


def test_review_must_cover_everything_the_gate_approves(sandbox):
    _to_g1_content(sandbox)
    path = sandbox.dir / "qa/reviews/G1_REVIEW.md"
    meta, body = read_front_matter(path)
    meta["fm"]["derived_from"] = [d for d in meta["fm"]["derived_from"] if d["ref"] != "artifact:brief"]
    write_front_matter(path, meta, body)
    with pytest.raises(ValidationFailed, match="does not review: artifact:brief"):
        ops.submit(sandbox)


def test_review_verdict_must_be_valid(sandbox):
    _to_g1_content(sandbox)
    path = sandbox.dir / "qa/reviews/G1_REVIEW.md"
    meta, body = read_front_matter(path)
    meta["verdict"] = "LOOKS GREAT"
    write_front_matter(path, meta, body)
    assert "REVIEW_VERDICT" in _codes(sandbox, "ERROR")


def test_stale_review_blocks_approval(sandbox):
    _to_g1_content(sandbox)
    ops.submit(sandbox)
    path = sandbox.dir / "00_brief/CREATIVE_DIRECTION.md"
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body + "\nA late addition the reviewer never saw.\n")
    with testing.as_actor(testing.AGENT):
        ops.stamp(sandbox, "00_brief/CREATIVE_DIRECTION.md")
    with testing.as_actor("human:director"), pytest.raises(ValidationFailed, match="g1_review is stale"):
        ops.decide_gate(sandbox, "G1", "approved", sandbox_confirm=True)


def test_fail_verdict_is_advisory_and_shown_to_the_human(production, monkeypatch):
    monkeypatch.setenv("FM_ACTOR", testing.AGENT)
    ops.advance(production)
    testing.produce(production, "BRIEF")
    ops.advance(production)
    testing.produce(production, "CREATIVE_DIRECTION")
    testing.write_review(production, "G1", verdict="FAIL", note="Tone contradicts intent.hope")
    testing.stamp_all(production)
    ops.submit(production)
    seen = {}

    def fake_prompt(msg):
        seen["msg"] = msg
        return "G1"
    monkeypatch.setenv("FM_ACTOR", "human:director")
    monkeypatch.setattr(authority, "_prompt", fake_prompt)
    st = ops.decide_gate(production, "G1", "approved", "overruling the reviewer")
    assert "qa review verdict (advisory): FAIL" in seen["msg"]
    assert st.gates["G1"].status == "approved"          # the human decides, not the reviewer


# ------------------------------------------------------------------ scene index
def test_screenplay_requires_scene_index(sandbox):
    testing.drive(sandbox, "SCREENPLAY")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "SCREENPLAY")
    (sandbox.dir / "02_screenplay/SCENES.yaml").unlink()
    with pytest.raises(ValidationFailed, match="SCENES.yaml"):
        ops.submit(sandbox)


def test_scene_index_schema(sandbox):
    testing.drive(sandbox, "SCREENPLAY")
    testing.produce(sandbox, "SCREENPLAY")
    path = sandbox.dir / "02_screenplay/SCENES.yaml"
    data = yaml.safe_load(path.read_text())
    data["scenes"].append(dict(data["scenes"][0]))
    write_yaml(path, data)
    assert "SCHEMA" in _codes(sandbox, "ERROR")


# ------------------------------------------------------------------ colours + ownership
def test_look_colors_must_be_hex(sandbox):
    ops.advance(sandbox)
    testing.write_canon(sandbox, "look", [
        {"id": "look.color.primary", "statement": "Blue", "value": "#1B2A3A", "rationale": "x"},
        {"id": "look.color.accent", "statement": "Amber", "value": "amber-ish", "rationale": "x"},
        {"id": "look.color.progression", "statement": "p", "value": [{"hex": "#E0A040"}, {"hex": "E0A040"}],
         "rationale": "x"},
    ])
    msgs = [f.message for f in validate(sandbox).errors if f.code == "BAD_COLOR"]
    assert len(msgs) == 2 and any("amber-ish" in m for m in msgs) and any("'E0A040'" in m for m in msgs)


def test_ownership_warnings(sandbox):
    ops.advance(sandbox)
    testing.write_canon(sandbox, "look", [
        {"id": "look.color.primary", "statement": "Blue", "value": "#1B2A3A", "rationale": "x",
         "source": "agent:screenwriter"}])
    testing.write_md(sandbox, "01_story/STORY_BIBLE.md", "story_bible", "story_bible", "STORY", [], "# x\n")
    path = sandbox.dir / "01_story/STORY_BIBLE.md"
    meta, body = read_front_matter(path)
    meta["fm"]["owner_role"] = "look-director"
    write_front_matter(path, meta, body)
    msgs = [f.message for f in validate(sandbox).findings if f.code == "OWNER_MISMATCH"]
    assert any("screenwriter" in m for m in msgs) and any("story-architect" in m for m in msgs)


# ------------------------------------------------------------------ intent coverage
def test_intent_coverage_and_unserved(sandbox):
    testing.drive(sandbox, "ASSET_PREP")
    loaded = sandbox.load()
    rows = {r.intent: r for r in intent_coverage(loaded)}
    assert set(rows) == {"intent.isolation", "intent.hope"}
    assert "SC01_SH010" in rows["intent.isolation"].shots
    assert "look.color.accent" in rows["intent.hope"].canon
    assert rows["intent.hope"].shots == []
    assert "characters.mara.wardrobe.jacket" in unserved_decisions(loaded)
    codes = _codes(sandbox, "WARN")
    assert {"INTENT_NOT_ON_SCREEN", "UNSERVED_DECISION"} <= codes


# ------------------------------------------------------------------ continuity
def _storyboard_ready(p):
    testing.drive(p, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(p, "STORYBOARD")


def test_continuity_clean_for_fixture(sandbox):
    _storyboard_ready(sandbox)
    assert [f for f in check_continuity(sandbox.load()) if f.level == "FAIL"] == []


def test_continuity_contradiction_blocks_g5(sandbox):
    _storyboard_ready(sandbox)
    testing.write_shot(sandbox, "SC01_SH020", environment={"location": "harbour", "weather": "clear",
                                                           "time_of_day": "night"})
    testing.write_shot(sandbox, "SC01_SH030", characters=[{"id": "ghost"}])
    testing.write_review(sandbox, "G5")
    testing.stamp_all(sandbox)
    fails = [str(f) for f in check_continuity(sandbox.load()) if f.level == "FAIL"]
    assert any("contradicts continuity.sc01.weather" in f for f in fails)
    assert any("'ghost'" in f for f in fails)
    with pytest.raises(ValidationFailed, match="continuity"):
        ops.submit(sandbox)


def test_duration_budget_warning(sandbox):
    _storyboard_ready(sandbox)
    testing.write_shot(sandbox, "SC02_SH020", characters=[], duration_s=30)
    warns = [str(f) for f in check_continuity(sandbox.load()) if f.level == "WARN"]
    assert any("vs brief duration 12s" in w for w in warns)


def test_cli_check_continuity_exit_code(repo, sandbox):
    import os
    import subprocess
    import sys
    _storyboard_ready(sandbox)
    env = {**os.environ, "FM_ROOT": str(repo)}
    ok = subprocess.run([sys.executable, "-m", "fm.cli", "-p", "last_signal", "check", "continuity"],
                        capture_output=True, text=True, env=env)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    testing.write_shot(sandbox, "SC01_SH010", environment={"weather": "snow", "time_of_day": "night"})
    bad = subprocess.run([sys.executable, "-m", "fm.cli", "-p", "last_signal", "check", "continuity"],
                         capture_output=True, text=True, env=env)
    assert bad.returncode == 1 and "FAIL" in bad.stdout
    intent = subprocess.run([sys.executable, "-m", "fm.cli", "-p", "last_signal", "intent"],
                            capture_output=True, text=True, env=env)
    assert intent.returncode == 0 and "intent.isolation" in intent.stdout
