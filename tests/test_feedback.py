"""M5 feedback loop: fm feedback add/list/plan/resolve and fm qa review-status. Tmp sandbox only."""
import pytest

from fm import feedback, ops, testing
from fm.deps import build_graph
from fm.errors import FMError, StateError
from fm.io import read_front_matter, write_front_matter
from fm.qa_review import review_status


@pytest.fixture
def film(sandbox):
    testing.drive(sandbox, "ASSET_PREP")
    return sandbox


def _touch_shot_upstream(p):
    """Edit an artifact so its dependants (incl. shots) go stale."""
    path = p.dir / "01_story/STORY_STRUCTURE.md"
    meta, body = read_front_matter(path)
    write_front_matter(path, meta, body + "\nEpilogue.\n")


def test_routing_table():
    assert feedback.route_owner("shot:SC01_SH010", "framing is too tight")[0] == "cinematographer"
    assert feedback.route_owner("shot:SC01_SH010", "the car is cream")[0] == "world-designer"
    assert feedback.route_owner("shot:SC01_SH010", "ui colour wrong")[0] == "look-director"
    assert feedback.route_owner("shot:SC01_SH010", "figure has no head")[0] == "character-designer"
    assert feedback.route_owner("shot:SC01_SH010", "motion too slow")[0] == "animation-director"
    assert feedback.route_owner("shot:SC01_SH010", "builder crash on proxy")[0] == "blender-td"
    assert feedback.route_owner("canon:look.color.primary", "hmm")[0] == "look-director"
    assert feedback.route_owner("artifact:x", "hmm")[0] == "executive-producer"


def test_add_list_and_ids(film):
    a = feedback.add(film, "shot:SC01_SH010", "framing cuts the head", severity="high")
    b = feedback.add(film, "canon:characters.mara.wardrobe.jacket", "jacket colour", owner="look-director")
    assert (a["id"], b["id"]) == ("FB-001", "FB-002")
    assert a["status"] == "OPEN" and a["suggested_owner"] == "cinematographer"
    assert b["owner_reason"] == "given with --owner"
    assert (film.dir / "qa/feedback/FB-001.yaml").exists()
    assert [i["id"] for i in feedback.list_items(film, open_only=True)] == ["FB-001", "FB-002"]
    # feedback files must not leak into the artifact graph or break validation
    assert not any("FB-" in k for k in film.load().artifacts)
    assert not film.load().errors


def test_add_rejects_bad_input(film):
    with pytest.raises(FMError):
        feedback.add(film, "shot:NOPE", "x")
    with pytest.raises(FMError):
        feedback.add(film, "bogus:thing", "x")
    with pytest.raises(FMError):
        feedback.add(film, "shot:SC01_SH010", "x", severity="cosmic")
    with pytest.raises(FMError):
        feedback.add(film, "shot:SC01_SH010", "  ")


def test_plan_reports_owner_locked_canon_and_impact(film):
    fb = feedback.add(film, "canon:characters.mara.wardrobe.jacket", "jacket should be darker")
    pl = feedback.plan_for(film, fb["id"])
    assert pl["change_request_needed"] is True          # G3 locked it in the fixture
    assert "fm change propose" in pl["change_request_note"]
    flat = {r for refs in pl["impact"].values() for r in refs}
    assert "shot:SC01_SH010" in flat and "shot:SC02_SH010" not in flat
    assert pl["owner"] == "look-director" or pl["owner"]  # routed by note/domain
    assert pl["stale"] == []


def test_plan_matches_ops_plan_and_lists_only_scoped_stale(film):
    fb = feedback.add(film, "shot:SC01_SH010", "framing")
    _touch_shot_upstream(film)
    pl = feedback.plan_for(film, fb["id"])
    assert pl["stale"] == ops.plan(film, "shot:SC01_SH010")["stale"]
    assert "shot:SC01_SH010" in pl["stale"]
    assert pl["change_request_needed"] is False
    assert pl["command"] == "/film-storyboard"
    # nothing outside the scope is in the minimal set even though other shots are stale too
    assert "shot:SC02_SH010" in build_graph(film.load()).stale()
    assert "shot:SC02_SH010" not in pl["stale"]


def test_resolve_refuses_while_stale_then_allows(film):
    fb = feedback.add(film, "shot:SC01_SH010", "framing")
    _touch_shot_upstream(film)
    with pytest.raises(StateError, match="stale"):
        feedback.resolve(film, fb["id"], "revised")
    assert feedback.load_item(film, fb["id"])["status"] == "OPEN"
    testing.stamp_all(film)
    it = feedback.resolve(film, fb["id"], "shot re-stamped")
    assert it["status"] == "RESOLVED"
    assert it["resolution"]["actor"] == "agent:test"    # actor recorded; agents may resolve
    assert it["resolution"]["by"] == "shot re-stamped"
    with pytest.raises(StateError, match="already"):
        feedback.resolve(film, fb["id"], "again")
    assert feedback.list_items(film, open_only=True) == []


def test_force_stale_is_recorded(film):
    fb = feedback.add(film, "shot:SC01_SH010", "framing")
    _touch_shot_upstream(film)
    it = feedback.resolve(film, fb["id"], "accepting risk", force_stale=True)
    assert it["resolution"]["forced_stale"] is True
    assert "shot:SC01_SH010" in it["resolution"]["stale_at_resolve"]


def test_feedback_does_not_touch_ledger_or_state(film):
    from fm.ledger import Ledger
    before = Ledger(film.ledger_path).head()
    feedback.add(film, "shot:SC01_SH010", "framing")
    assert Ledger(film.ledger_path).head() == before   # files only: no ledger action exists for this


def test_review_status_counts_and_staleness(film):
    rel = "qa/reviews/PREVIEW_REVIEW.md"
    path = film.dir / rel
    shots = sorted(film.load().shots)[:3]
    refs = [{"ref": f"shot:{s}"} for s in shots]
    body = ("# Preview review\n\n| Shot | Verdict | Evidence |\n|---|---|---|\n"
            f"| {shots[0]} | PASS | ok |\n| {shots[1]} | WARN | meh |\n| {shots[2]} | FAIL | bad |\n")
    write_front_matter(path, {"fm": {"id": "preview_review", "kind": "gate_review", "phase": "PREVIEW",
                                     "status": "PROPOSED", "derived_from": refs},
                              "verdict": "FAIL", "reviewed_gate": "G6"}, body)
    ops.stamp(film, rel)
    r = review_status(film)
    assert r["counts"] == {"PASS": 1, "WARN": 1, "FAIL": 1} and r["verdict"] == "FAIL"
    assert r["stale"] is False
    _touch_shot_upstream(film)                     # shots' upstream moves; shot files themselves do not
    assert review_status(film)["stale"] is False   # reviewed hashes (shot content) still match
    spec = film.dir / "08_shots" / f"{shots[0]}.shot.yaml"
    from fm.io import load_yaml, write_yaml
    d = load_yaml(spec)
    d["rationale"] = str(d.get("rationale", "")) + " (revised)"
    write_yaml(spec, d)
    r = review_status(film)
    assert r["stale"] is True and any(shots[0] in x for x in r["stale_reasons"])


def test_review_status_missing_file(film):
    with pytest.raises(FMError):
        review_status(film)


def test_cli_roundtrip(film):
    from click.testing import CliRunner
    from fm.cli import cli
    r = CliRunner()
    run = lambda *a: r.invoke(cli, ["-p", film.slug, *a], catch_exceptions=False)  # noqa: E731
    out = run("feedback", "add", "shot:SC01_SH010", "--note", "framing too tight", "--severity", "high")
    assert out.exit_code == 0 and "FB-001 OPEN" in out.output and "cinematographer" in out.output
    assert "FB-001" in run("feedback", "list", "--open").output
    pl = run("feedback", "plan", "FB-001")
    assert pl.exit_code == 0 and "/film-storyboard" in pl.output and "change request: no" in pl.output
    res = run("feedback", "resolve", "FB-001", "--by", "reviewed")
    assert res.exit_code == 0 and "RESOLVED by agent:test" in res.output
    assert "no feedback open" in run("feedback", "list", "--open").output


def test_settings_allow_feedback_but_keep_blocks():
    import json
    from pathlib import Path
    s = json.loads((Path(__file__).resolve().parents[1] / ".claude" / "settings.json").read_text())
    allow = " ".join(s["permissions"]["allow"])
    assert "fm feedback" in allow and "fm qa review-status" in allow
    assert "fm feedback" not in " ".join(s["permissions"]["deny"])
