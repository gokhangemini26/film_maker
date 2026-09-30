"""State machine transitions, gates, and human authority."""
import pytest

from fm import authority, ops, testing
from fm.errors import AuthorityError, StateError, ValidationFailed
from fm.ledger import Ledger
from tests.conftest import set_actor


def test_advance_through_ungated_phases(sandbox):
    assert ops.advance(sandbox).phase == "BRIEF"
    assert ops.advance(sandbox).phase == "CREATIVE_DIRECTION"


def test_cannot_leave_gated_phase_without_approval(sandbox):
    ops.advance(sandbox)
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "BRIEF")
    ops.advance(sandbox)  # -> CREATIVE_DIRECTION (gate G1)
    with pytest.raises(StateError, match="G1"):
        ops.advance(sandbox)


def test_submit_requires_deliverables(sandbox):
    ops.advance(sandbox)
    ops.advance(sandbox)
    with pytest.raises(ValidationFailed, match="CREATIVE_DIRECTION.md"):
        ops.submit(sandbox)


def _to_g1_review(project):
    testing.drive(project, "CREATIVE_DIRECTION")
    with testing.as_actor(testing.AGENT):
        testing.produce(project, "CREATIVE_DIRECTION")
        ops.submit(project)


def test_awaiting_approval_blocks_advance(sandbox):
    _to_g1_review(sandbox)
    st = ops.load_state(sandbox)
    assert st.phase_status == "awaiting_approval" and st.gates["G1"].status == "awaiting_approval"
    with pytest.raises(StateError, match="awaiting"):
        ops.advance(sandbox)


def test_agent_cannot_approve(sandbox):
    _to_g1_review(sandbox)
    set_actor_env = testing.as_actor("agent:creative-director")
    with set_actor_env, pytest.raises(AuthorityError, match="human-only"):
        ops.decide_gate(sandbox, "G1", "approved", sandbox_confirm=True)
    assert ops.load_state(sandbox).gates["G1"].status == "awaiting_approval"


def test_human_approves_then_advance(sandbox):
    _to_g1_review(sandbox)
    with testing.as_actor("human:director"):
        st = ops.decide_gate(sandbox, "G1", "approved", "looks right", sandbox_confirm=True)
    g = st.gates["G1"]
    assert g.status == "approved" and g.decided_by == "human:director"
    assert "artifact:creative_direction" in g.approved_hashes
    assert "artifact:brief" in g.approved_hashes
    assert st.canon["intent.isolation"].status.value == "LOCKED"
    assert st.canon["tone.register"].status.value == "LOCKED"
    # file mirrors updated, hash unaffected
    assert "status: LOCKED" in (sandbox.canon_dir / "tone.yaml").read_text()
    assert ops.advance(sandbox).phase == "STORY"


def test_revise_sends_back_with_notes(sandbox):
    _to_g1_review(sandbox)
    with testing.as_actor("human:director"):
        with pytest.raises(Exception, match="notes"):
            ops.decide_gate(sandbox, "G1", "revise", sandbox_confirm=True)
        st = ops.decide_gate(sandbox, "G1", "revise", "warmer ending", sandbox_confirm=True)
    assert st.gates["G1"].status == "revise" and st.phase_status == "in_progress"
    with pytest.raises(StateError):
        ops.advance(sandbox)
    with testing.as_actor(testing.AGENT):
        ops.submit(sandbox)  # resubmit after revision
    assert ops.load_state(sandbox).gates["G1"].status == "awaiting_approval"


def test_production_project_rejects_simulated_confirmation(production, monkeypatch):
    set_actor(monkeypatch, "human:director")
    with pytest.raises(AuthorityError, match="sandbox"):
        ops.authorize(production, "final-render", sandbox_confirm=True)


def test_production_project_needs_interactive_terminal(production, monkeypatch):
    set_actor(monkeypatch, "human:director")
    with pytest.raises(AuthorityError, match="interactive terminal"):
        ops.authorize(production, "final-render")


def test_typed_confirmation_on_production(production, monkeypatch):
    set_actor(monkeypatch, "human:director")
    monkeypatch.setattr(authority, "_prompt", lambda _msg: "wrong")
    with pytest.raises(AuthorityError, match="did not match"):
        ops.authorize(production, "final-render")
    monkeypatch.setattr(authority, "_prompt", lambda _msg: "final-render")
    st = ops.authorize(production, "final-render")
    assert st.authorizations[0].by == "human:director"
    last = Ledger(production.ledger_path).records()[-1]
    assert last.payload["confirmation"] == "typed" and last.payload["simulated"] is False


def test_final_render_requires_authorization(sandbox):
    testing.drive(sandbox, "ANIMATION_PREVIEW")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "ANIMATION_PREVIEW")     # M6 contract: bibles, mix, animatic, review
        ops.submit(sandbox)
    with testing.as_actor("human:director"):
        ops.decide_gate(sandbox, "G7", "approved", sandbox_confirm=True)
    with testing.as_actor(testing.AGENT), pytest.raises(StateError, match="authorization"):
        ops.advance(sandbox)
    with testing.as_actor("human:director"):
        ops.authorize(sandbox, "final-render", sandbox_confirm=True)
    with testing.as_actor(testing.AGENT):
        assert ops.advance(sandbox).phase == "FINAL_RENDER"


def test_gate_bypass_by_editing_state_is_detected(sandbox):
    """Even if someone rewrote the cache, the ledger replay is the truth."""
    import yaml
    from fm.validate import validate
    data = yaml.safe_load(sandbox.state_path.read_text())
    data["phase"] = "LOOK"
    sandbox.state_path.write_text(yaml.safe_dump(data))
    rep = validate(sandbox)
    assert "STATE_TAMPERED" in {f.code for f in rep.errors}
