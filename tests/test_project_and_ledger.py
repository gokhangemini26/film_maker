"""Project initialisation, ledger integrity and state replay."""
import json

import pytest
import yaml

from fm.errors import IntegrityError, StateError
from fm.io import load_yaml
from fm.ledger import Ledger
from fm.ops import init_project, load_state
from fm.phases import GATES, PROJECT_DIRS
from fm.statemachine import replay
from fm.validate import validate


def test_init_creates_structure(sandbox):
    d = sandbox.dir
    for sub in PROJECT_DIRS:
        assert (d / sub).is_dir(), sub
    for f in ("state.yaml", "STATUS.md", "CHANGELOG.md", "FILM_BIBLE.md", "00_brief/brief.yaml",
              ".fm/ledger.jsonl", "canon/intent.yaml", "canon/look.yaml"):
        assert (d / f).exists(), f
    assert "Last Signal" in (d / "FILM_BIBLE.md").read_text()
    st = load_state(sandbox)
    assert st.phase == "IDEA" and st.sandbox is True
    assert set(st.gates) == set(GATES)
    assert all(g.status == "pending" for g in st.gates.values())


def test_init_refuses_to_overwrite(repo, sandbox):
    with pytest.raises(StateError):
        init_project(repo, "last_signal", "Again")


def test_fresh_project_validates(sandbox):
    rep = validate(sandbox)
    assert rep.ok, [str(f) for f in rep.errors]


def test_state_is_replay_of_ledger(sandbox):
    cached = load_yaml(sandbox.state_path)
    assert cached == replay(Ledger(sandbox.ledger_path).records()).model_dump(mode="json")


def test_ledger_tamper_detected(sandbox):
    lines = sandbox.ledger_path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["sandbox"] = False
    sandbox.ledger_path.write_text(json.dumps(rec) + "\n")
    problems = Ledger(sandbox.ledger_path).verify()
    assert any("altered" in p for p in problems)
    with pytest.raises(IntegrityError):
        load_state(sandbox)
    with pytest.raises(IntegrityError):
        Ledger(sandbox.ledger_path).append("agent:x", "phase.advance", "BRIEF", {"from": "IDEA", "to": "BRIEF"})


def test_ledger_deletion_detected(sandbox):
    from fm.ops import advance
    advance(sandbox)
    advance(sandbox)
    lines = sandbox.ledger_path.read_text().splitlines()
    sandbox.ledger_path.write_text("\n".join([lines[0], lines[2]]) + "\n")
    assert Ledger(sandbox.ledger_path).verify()


def test_state_cache_tamper_detected(sandbox):
    data = yaml.safe_load(sandbox.state_path.read_text())
    data["phase"] = "FINAL_RENDER"
    data["gates"]["G1"]["status"] = "approved"
    sandbox.state_path.write_text(yaml.safe_dump(data))
    codes = {f.code for f in validate(sandbox).errors}
    assert "STATE_TAMPERED" in codes
    # the real state is still the ledger's
    assert load_state(sandbox).phase == "IDEA"
