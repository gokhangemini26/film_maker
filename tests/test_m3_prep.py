"""Small fm changes made before M3, from lessons of the Last Signal run."""
import pytest

from fm import authority, ops, testing
from fm.errors import AuthorityError, FMError, StateError
from fm.io import read_front_matter, write_front_matter


def _to_g1_submitted(project, monkeypatch, verdict):
    monkeypatch.setenv("FM_ACTOR", testing.AGENT)
    ops.advance(project)
    testing.produce(project, "BRIEF")
    ops.advance(project)
    testing.produce(project, "CREATIVE_DIRECTION")
    testing.write_review(project, "G1", verdict=verdict)
    testing.stamp_all(project)
    ops.submit(project)
    monkeypatch.setenv("FM_ACTOR", "human:director")
    monkeypatch.setattr(authority, "_prompt", lambda msg: "G1")


# ---- review acknowledgement ---------------------------------------------
def test_warn_review_needs_explicit_acknowledgement(production, monkeypatch):
    _to_g1_submitted(production, monkeypatch, "WARN")
    with pytest.raises(FMError, match="--ack-review"):
        ops.decide_gate(production, "G1", "approved")
    assert ops.load_state(production).gates["G1"].status == "awaiting_approval"
    st = ops.decide_gate(production, "G1", "approved", "wording A; keep desk", ack_review=True)
    g = st.gates["G1"]
    assert g.status == "approved" and g.review_verdict == "WARN" and g.review_acknowledged
    assert g.notes == "wording A; keep desk"
    assert "carried forward: G1 approved past a WARN QA review" in (production.dir / "STATUS.md").read_text()


def test_pass_review_needs_no_acknowledgement(production, monkeypatch):
    _to_g1_submitted(production, monkeypatch, "PASS")
    st = ops.decide_gate(production, "G1", "approved")
    assert st.gates["G1"].review_verdict == "PASS" and not st.gates["G1"].review_acknowledged


# ---- canon annotate ------------------------------------------------------
def _locked_entry(project):
    state = ops.load_state(project)
    loaded = project.load()
    from fm.schemas import Status
    for cid, lk in state.canon.items():
        if lk.status == Status.LOCKED and cid in loaded.canon:
            return cid
    raise AssertionError("no locked canon in fixture")


def test_annotate_locked_canon_notes_is_logged_and_does_not_break_the_lock(sandbox):
    testing.drive(sandbox, "STORY")
    cid = _locked_entry(sandbox)
    before = sandbox.load().canon[cid].hash
    with testing.as_actor(testing.AGENT):
        ops.annotate_canon(sandbox, cid, "Corrected: door decided by the human.")
    loaded = sandbox.load()
    assert loaded.canon[cid].entry.notes == "Corrected: door decided by the human."
    assert loaded.canon[cid].hash == before                      # the decision itself is untouched
    from fm.validate import validate
    assert not [f for f in validate(sandbox).errors]
    from fm.ledger import Ledger
    last = Ledger(sandbox.ledger_path).records()[-1]
    assert last.action == "canon.annotate" and last.payload["new_notes"].startswith("Corrected")
    with pytest.raises(FMError, match="identical"):
        ops.annotate_canon(sandbox, cid, "Corrected: door decided by the human.")


# ---- amend ---------------------------------------------------------------
def _reword(project, rel):
    path = project.dir / rel
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body + "\nA wording-only clarification.\n")


def test_amend_accepts_wording_edit_without_reapproval_and_restamps_downstream(sandbox):
    testing.drive(sandbox, "STORY")                                 # G1 approved
    _reword(sandbox, "00_brief/CREATIVE_DIRECTION.md")
    from fm.validate import validate
    assert any(f.code == "GATE_DRIFT" for f in validate(sandbox).findings)
    with testing.as_actor(testing.AGENT), pytest.raises(AuthorityError):
        ops.amend_gate(sandbox, "G1", ["artifact:creative_direction"], "wording", sandbox_confirm=True)
    with testing.as_actor("human:director"):
        st = ops.amend_gate(sandbox, "G1", ["artifact:creative_direction"],
                            "clarified one sentence; meaning unchanged", sandbox_confirm=True)
    assert st.gates["G1"].amendments == 1
    rep = validate(sandbox)
    assert not [f for f in rep.findings if f.code in ("GATE_DRIFT", "STALE")], rep.findings
    assert not rep.errors
    from fm.ledger import Ledger
    rec = [r for r in Ledger(sandbox.ledger_path).records() if r.action == "gate.amend"][0]
    assert rec.payload["note"].startswith("clarified") and rec.payload["restamped"]


def test_amend_refuses_unmodified_unapproved_or_noteless(sandbox):
    testing.drive(sandbox, "STORY")
    with testing.as_actor("human:director"):
        with pytest.raises(FMError, match="not been modified"):
            ops.amend_gate(sandbox, "G1", ["artifact:creative_direction"], "x", sandbox_confirm=True)
        with pytest.raises(FMError, match="--note"):
            ops.amend_gate(sandbox, "G1", ["artifact:creative_direction"], "", sandbox_confirm=True)
        with pytest.raises(StateError, match="not approved"):
            ops.amend_gate(sandbox, "G3", ["artifact:world_bible"], "x", sandbox_confirm=True)
        with pytest.raises(FMError, match="only documents"):
            ops.amend_gate(sandbox, "G1", ["canon:intent.hope"], "x", sandbox_confirm=True)


# ---- older projects keep validating -----------------------------------------
def test_state_cache_written_before_new_fields_is_not_tampered(sandbox):
    from fm.io import load_yaml, write_yaml
    from fm.validate import validate
    testing.drive(sandbox, "STORY")
    data = load_yaml(sandbox.state_path)
    for g in data["gates"].values():
        for k in ("review_acknowledged", "amendments"):  # defaults in replay
            g.pop(k, None)
    write_yaml(sandbox.state_path, data)
    assert not [f for f in validate(sandbox).findings if f.code == "STATE_TAMPERED"]
    data["gates"]["G1"]["decided_by"] = "human:someone_else"      # a real edit is still caught
    write_yaml(sandbox.state_path, data)
    assert [f for f in validate(sandbox).findings if f.code == "STATE_TAMPERED"]
