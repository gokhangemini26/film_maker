"""Dependency hashing, staleness, impact analysis, change requests, scopes."""
import pytest
import yaml

from fm import ops, testing
from fm.deps import build_graph
from fm.errors import AuthorityError, FMError, StateError
from fm.io import read_front_matter, write_front_matter
from fm.schemas import Layer
from fm.validate import validate


@pytest.fixture
def storyboarded(sandbox):
    """Toy film approved through G5 (storyboard + shots), now in ASSET_PREP."""
    testing.drive(sandbox, "ASSET_PREP")
    return sandbox


def _stale(project):
    return build_graph(project.load()).stale()


def test_stamp_records_upstream_hashes(storyboarded):
    loaded = storyboarded.load()
    cb = loaded.artifacts["character_bible"]
    deps = {d.ref: d.hash for d in cb.meta.derived_from}
    assert deps["canon:characters.mara.wardrobe.jacket"] == loaded.canon["characters.mara.wardrobe.jacket"].hash
    assert all(h and h.startswith("sha256:") for h in deps.values())
    assert not _stale(storyboarded)


def test_editing_artifact_makes_downstream_stale(storyboarded):
    p = storyboarded
    path = p.dir / "01_story/STORY_STRUCTURE.md"
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body + "\n4. Epilogue.\n")
    stale = _stale(p)
    # direct child and everything below it, down to the shots
    assert "artifact:screenplay" in stale
    assert "artifact:storyboard" in stale and "shot:SC01_SH010" in stale
    assert "artifact:character_bible" not in stale
    codes = {f.code for f in validate(p).findings}
    assert "GATE_DRIFT" in codes and "STALE" in codes


def test_impact_crosses_all_layers(storyboarded):
    p = storyboarded
    for kind, deps in (("resolved", ["shot:SC01_SH010", "canon:look.color.primary"]),
                       ("blend", ["resolved:SC01_SH010"]),
                       ("render", ["blend:SC01_SH010"]),
                       ("qa", ["render:SC01_SH010"])):
        ops.record_derived(p, f"{kind}:SC01_SH010", deps, content=f"{kind} v1")
    imp = build_graph(p.load()).impact(["canon:intent.isolation"])
    assert set(imp) >= {Layer.CANON, Layer.ARTIFACT, Layer.SHOT, Layer.RESOLVED, Layer.BLEND,
                        Layer.RENDER, Layer.QA}
    assert "qa:SC01_SH010" in imp[Layer.QA]


def test_impact_is_selective(storyboarded):
    imp = build_graph(storyboarded.load()).impact(["canon:characters.mara.wardrobe.jacket"])
    flat = {r for refs in imp.values() for r in refs}
    assert {"artifact:character_bible", "shot:SC01_SH010", "shot:SC01_SH020"} <= flat
    assert "shot:SC02_SH010" not in flat           # Mara is not in this shot
    assert "artifact:color_bible" not in flat
    assert "artifact:screenplay" not in flat


def test_stamp_refuses_to_hide_staleness(storyboarded):
    p = storyboarded
    path = p.dir / "01_story/STORY_BIBLE.md"
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body + "\nMore premise.\n")
    with pytest.raises(StateError, match="unchanged"):
        ops.stamp(p, "01_story/STORY_STRUCTURE.md")
    ops.stamp(p, "01_story/STORY_STRUCTURE.md", note="structure unaffected by premise wording")
    assert "artifact:story_structure" not in build_graph(p.load()).direct_staleness()


def _propose_brown(p):
    with testing.as_actor("agent:character-designer"):
        return ops.propose_change(
            p, "characters.mara.wardrobe.jacket",
            {"statement": "Dark brown waxed jacket.",
             "value": {"color": "#3B2A1E", "material": "waxed cotton"}},
            "Brown separates her from the blue night better than black.")


def test_change_request_flow(storyboarded):
    p = storyboarded
    cr = _propose_brown(p)
    assert cr.id == "CHANGE-001" and cr.status.value == "PROPOSED"
    assert "shot:SC01_SH010" in cr.impact["SHOT"] and "shot:SC02_SH010" not in cr.impact["SHOT"]
    # proposal alone changes nothing
    loaded = p.load()
    assert loaded.canon["characters.mara.wardrobe.jacket"].entry.statement == "Black waxed jacket."
    assert not _stale(p)
    with testing.as_actor("agent:character-designer"), pytest.raises(AuthorityError):
        ops.decide_change(p, "CHANGE-001", "approved", sandbox_confirm=True)
    with testing.as_actor("human:director"):
        cr = ops.decide_change(p, "CHANGE-001", "approved", "yes", sandbox_confirm=True)
    entry = p.load().canon["characters.mara.wardrobe.jacket"].entry
    assert entry.version == 2 and entry.status.value == "LOCKED"
    assert entry.history[0].statement == "Black waxed jacket." and entry.history[0].change == "CHANGE-001"
    rep = validate(p)
    assert rep.ok, [str(f) for f in rep.errors]      # approved change is not a lock violation
    stale = _stale(p)
    assert {"artifact:character_bible", "shot:SC01_SH010", "shot:SC01_SH020"} <= set(stale)
    assert "shot:SC02_SH010" not in stale
    assert "CHANGE-001" in (p.dir / "CHANGELOG.md").read_text()
    # G3 and G5 drifted -> cannot advance until regenerated and re-approved
    with testing.as_actor(testing.AGENT), pytest.raises(StateError, match="G3"):
        ops.advance(p)


def test_regenerate_and_reapprove_after_change(storyboarded):
    p = storyboarded
    _propose_brown(p)
    with testing.as_actor("human:director"):
        ops.decide_change(p, "CHANGE-001", "approved", sandbox_confirm=True)
    plan = ops.plan(p, "character:mara")
    assert "artifact:character_bible" in plan["stale"] and "shot:SC02_SH010" not in plan["stale"]
    # regenerate only what is stale: character bible + Mara's two shots
    path = p.dir / "04_characters/CHARACTER_BIBLE.md"
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body.replace("black", "dark brown"))
    ops.stamp(p, "artifact:character_bible")
    for sid in ("SC01_SH010", "SC01_SH020"):
        sp = p.shots_dir / f"{sid}.shot.yaml"
        data = yaml.safe_load(sp.read_text())
        data["environment"]["weather"] = "rain (brown jacket reads warmer)"
        sp.write_text(yaml.safe_dump(data, sort_keys=False))
        ops.stamp(p, f"08_shots/{sid}.shot.yaml")
    stale = _stale(p)
    assert set(stale) == {"artifact:g3_review", "artifact:g5_review"}   # reviews must be redone
    testing.rereview(p, "G3", "jacket now dark brown")
    testing.rereview(p, "G5", "shots rechecked")
    assert not _stale(p)
    with testing.as_actor("human:director"):
        ops.decide_gate(p, "G3", "approved", "re-approve after jacket change", sandbox_confirm=True)
        ops.decide_gate(p, "G5", "approved", "re-approve shots", sandbox_confirm=True)
    with testing.as_actor(testing.AGENT):
        assert ops.advance(p).phase == "BLENDER_BUILD"


def test_change_conflict_detected(storyboarded):
    p = storyboarded
    _propose_brown(p)
    with testing.as_actor("agent:character-designer"):
        ops.propose_change(p, "characters.mara.wardrobe.jacket", {"statement": "Grey jacket."}, "alt idea")
    with testing.as_actor("human:director"):
        ops.decide_change(p, "CHANGE-001", "approved", sandbox_confirm=True)
        with pytest.raises(StateError, match="changed since"):
            ops.decide_change(p, "CHANGE-002", "approved", sandbox_confirm=True)


def test_change_request_only_for_approved_entries(sandbox):
    ops.advance(sandbox)
    testing.write_canon(sandbox, "look", [{"id": "look.color.primary", "statement": "Blue", "rationale": "x"}])
    with pytest.raises(StateError, match="edited directly"):
        ops.propose_change(sandbox, "look.color.primary", {"statement": "Teal"}, "try teal")


# ------------------------------------------------------------------ scopes
@pytest.mark.parametrize("scope,expected", [
    ("shot:SC01_SH010", {"shot:SC01_SH010"}),
    ("shots:SC01_SH010..SC01_SH020", {"shot:SC01_SH010", "shot:SC01_SH020"}),
    ("scene:SC02", {"shot:SC02_SH010"}),
    ("sequence:SQ01", {"shot:SC01_SH010", "shot:SC01_SH020"}),
    ("character:mara", {"shot:SC01_SH010", "shot:SC01_SH020"}),
])
def test_scopes(storyboarded, scope, expected):
    res = ops.plan(storyboarded, scope)
    assert set(res["shots"]) == expected
    assert res["stale"] == []


def test_plan_limits_regeneration_to_scope(storyboarded):
    p = storyboarded
    for sid in ("SC01_SH010", "SC02_SH010"):
        ops.record_derived(p, f"resolved:{sid}", [f"shot:{sid}", "canon:look.color.primary"])
    _propose_brown(p)
    with testing.as_actor("human:director"):
        ops.decide_change(p, "CHANGE-001", "approved", sandbox_confirm=True)
    assert "resolved:SC01_SH010" in ops.plan(p, "shot:SC01_SH010")["stale"]
    # SC02's own shot and products are untouched; only the G5 review (which covers all shots) needs redoing
    assert ops.plan(p, "scene:SC02")["stale"] == ["artifact:g5_review"]


def test_bad_scopes(storyboarded):
    for bad in ("shot:SC09_SH999", "shots:SC02_SH010..SC01_SH010", "planet:mars", "character:nobody"):
        with pytest.raises(FMError):
            ops.plan(storyboarded, bad)
