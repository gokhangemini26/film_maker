"""Canon lifecycle: proposals vs. locked decisions, and no silent changes."""
import pytest
import yaml

from fm import ops, testing
from fm.errors import AuthorityError, StateError, ValidationFailed
from fm.validate import validate


def _codes(project):
    return {f.code for f in validate(project).findings}


def _edit_entry(project, domain, cid, **changes):
    path = project.canon_dir / f"{domain}.yaml"
    data = yaml.safe_load(path.read_text())
    for e in data["entries"]:
        if e["id"] == cid:
            e.update(changes)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


@pytest.fixture
def after_g3(sandbox):
    testing.drive(sandbox, "LOOK")
    return sandbox


def test_agent_cannot_claim_locked_status(sandbox):
    ops.advance(sandbox)
    testing.write_canon(sandbox, "intent", [
        {"id": "intent.isolation", "statement": "Isolated.", "status": "LOCKED", "tag": "USER_REQUIREMENT"}])
    rep = validate(sandbox)
    assert "STATUS_NOT_BACKED" in {f.code for f in rep.errors}


def test_locked_canon_cannot_be_silently_changed(after_g3):
    p = after_g3
    assert ops.load_state(p).canon["characters.mara.wardrobe.jacket"].status.value == "LOCKED"
    _edit_entry(p, "characters", "characters.mara.wardrobe.jacket",
                statement="Dark brown jacket.", value={"color": "#3B2A1E", "material": "waxed cotton"})
    rep = validate(p)
    errs = [f for f in rep.errors if f.code == "LOCKED_CANON_MODIFIED"]
    assert errs and "characters.mara.wardrobe.jacket" in errs[0].message
    # cannot submit or move forward on a violated lock
    with testing.as_actor(testing.AGENT):
        testing.produce(p, "LOOK")
        with pytest.raises(ValidationFailed, match="LOCKED_CANON_MODIFIED"):
            ops.submit(p)
        with pytest.raises(StateError):
            ops.advance(p)


def test_status_reset_to_proposed_is_detected(after_g3):
    _edit_entry(after_g3, "characters", "characters.mara.identity", status="PROPOSED")
    assert "STATUS_MISMATCH" in _codes(after_g3)


def test_locked_entry_removal_is_detected(after_g3):
    path = after_g3.canon_dir / "world.yaml"
    path.write_text(yaml.safe_dump({"domain": "world", "entries": []}))
    assert "LOCKED_CANON_REMOVED" in _codes(after_g3)


def test_gate_refuses_decisions_without_rationale(sandbox):
    testing.drive(sandbox, "CREATIVE_DIRECTION")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "CREATIVE_DIRECTION")
        _edit_entry(sandbox, "tone", "tone.register", rationale=None)
        ops.submit(sandbox)  # PROPOSED without rationale is only a warning
    assert "MISSING_RATIONALE" in _codes(sandbox)
    with testing.as_actor("human:director"), pytest.raises(ValidationFailed, match="rationale"):
        ops.decide_gate(sandbox, "G1", "approved", sandbox_confirm=True)


def test_individual_canon_decisions(sandbox):
    ops.advance(sandbox)
    testing.write_canon(sandbox, "look", [
        {"id": "look.color.primary", "statement": "Blue", "value": "#1B2A3A", "rationale": "cold"},
        {"id": "look.color.secondary", "statement": "Teal", "value": "#1B4A4A", "rationale": "calm"},
        {"id": "look.grain", "statement": "Heavy grain"},  # no rationale
    ])
    with testing.as_actor(testing.AGENT), pytest.raises(AuthorityError):
        ops.canon_decide(sandbox, "look.color.primary", "approve", sandbox_confirm=True)
    with testing.as_actor("human:director"):
        assert ops.canon_decide(sandbox, "look.color.primary", "approve",
                                sandbox_confirm=True).canon["look.color.primary"].status.value == "APPROVED"
        assert ops.canon_decide(sandbox, "look.color.primary", "lock",
                                sandbox_confirm=True).canon["look.color.primary"].status.value == "LOCKED"
        assert ops.canon_decide(sandbox, "look.color.secondary", "reject",
                                sandbox_confirm=True).canon["look.color.secondary"].status.value == "REJECTED"
        with pytest.raises(ValidationFailed, match="rationale"):
            ops.canon_decide(sandbox, "look.grain", "approve", sandbox_confirm=True)
        with pytest.raises(StateError, match="change propose"):
            ops.canon_decide(sandbox, "look.color.primary", "reject", sandbox_confirm=True)
    assert validate(sandbox).ok
