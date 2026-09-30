"""M6 core plumbing (task A4): derived kinds, artifact/canon ownership, phase contracts,
gates G7/G8, the human-only `authorize final-render`, and migration safety."""
import json
import shutil
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from fm import ops, testing
from fm.cli import cli
from fm.errors import AuthorityError, FMError, StateError, ValidationFailed
from fm.phases import (
    ANIM_FILE, AUDIO_REPORT, CONTRACTS, DELIVERY_REPORT, FINAL_FRAMES_REPORT, GATES, MOTION_REPORT,
    PHASES,
)
from fm.project import Project
from fm.roles import ARTIFACT_OWNERS, CANON_DOMAINS, REVIEW_FOR_GATE
from fm.schemas import DERIVED_KINDS, DOMAINS, REF_RE, DepRef, Layer, layer_of
from fm.validate import gate_health, validate

REPO = Path(__file__).resolve().parents[1]
AGENT = testing.AGENT
HUMAN = "human:director"


# ------------------------------------------------------------------ helpers
_SEEDS: dict[str, Path] = {}
_SEED_PHASES = ("ASSET_PREP", "ANIMATION", "ANIMATION_PREVIEW", "POST")


def _build_seeds():
    """Drive one sandbox project through the state machine once and snapshot it at the phases the
    tests start from (driving from IDEA costs ~10 s each time)."""
    import tempfile
    root = Path(tempfile.mkdtemp(prefix="fm_m6_seeds_"))
    work = root / "repo"
    shutil.copytree(REPO / "config", work / "config")
    shutil.copytree(REPO / "templates", work / "templates")
    (work / "projects").mkdir()
    mp = pytest.MonkeyPatch()
    try:
        mp.setenv("FM_ROOT", str(work))
        mp.setenv("FM_ACTOR", "agent:test")
        mp.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
        mp.chdir(work)
        project = ops.init_project(work, "last_signal", "Last Signal", sandbox=True)
        for phase in _SEED_PHASES:
            testing.drive(project, phase)
            assert ops.load_state(project).phase == phase
            _SEEDS[phase] = root / f"seed_{phase}"
            shutil.copytree(project.dir, _SEEDS[phase])
    finally:
        mp.undo()


def _to(project, phase):
    """Put `project` (a fresh sandbox) at the start of `phase` by restoring a snapshot."""
    if not _SEEDS:
        _build_seeds()
    shutil.rmtree(project.dir)
    shutil.copytree(_SEEDS[phase], project.dir)
    assert ops.load_state(project).phase == phase


def _agent_produce(project, phase):
    with testing.as_actor(AGENT):
        testing.produce(project, phase)


def _submit(project):
    with testing.as_actor(AGENT):
        return ops.submit(project)


def _advance(project):
    with testing.as_actor(AGENT):
        return ops.advance(project)


def _approve(project, gate):
    with testing.as_actor(HUMAN):
        return ops.decide_gate(project, gate, "approved", "fixture", sandbox_confirm=True)


# ------------------------------------------------------------------ 1. derived kinds
def test_derived_kinds_include_audio_and_edit():
    assert set(DERIVED_KINDS) == {"resolved", "blend", "render", "audio", "edit", "qa"}


@pytest.mark.parametrize("kind,layer", [("audio", Layer.AUDIO), ("edit", Layer.EDIT)])
def test_new_ref_kinds_have_layers_and_parse(kind, layer):
    assert REF_RE.match(f"{kind}:mix_48k")
    assert layer_of(f"{kind}:mix_48k") == layer
    assert DepRef(ref=f"{kind}:x").ref == f"{kind}:x"


def test_layer_order_places_audio_and_edit_between_render_and_qa():
    order = list(Layer)
    assert order.index(Layer.RENDER) < order.index(Layer.AUDIO) < order.index(Layer.EDIT) < order.index(Layer.QA)


def test_record_derived_audio_and_edit_and_staleness(sandbox):
    _to(sandbox, "ASSET_PREP")
    a = ops.record_derived(sandbox, "audio:mix", ["shot:SC01_SH010"], content="mix v1")
    e = ops.record_derived(sandbox, "edit:animatic", ["audio:mix", "shot:SC01_SH010"], content="cut v1")
    assert a.ref == "audio:mix" and e.ref == "edit:animatic"
    assert (sandbox.derived_dir / "audio" / "mix.json").exists()
    assert (sandbox.derived_dir / "edit" / "animatic.json").exists()
    loaded = sandbox.load()
    assert loaded.exists("audio:mix") and loaded.exists("edit:animatic")
    assert not loaded.errors
    assert ops.plan(sandbox, "ref:audio:mix")["stale"] == []
    # editing an upstream shot makes the audio and the edit stale, layer by layer
    p = sandbox.shots_dir / "SC01_SH010.shot.yaml"
    data = yaml.safe_load(p.read_text())
    data["duration_s"] = 5.0
    p.write_text(yaml.safe_dump(data))
    stale = sandbox.load()
    from fm.deps import build_graph
    graph = build_graph(stale)
    assert {"audio:mix", "edit:animatic"} <= set(graph.stale())
    impact = graph.impact(["shot:SC01_SH010"])
    assert "audio:mix" in impact[Layer.AUDIO] and "edit:animatic" in impact[Layer.EDIT]


def test_record_derived_still_rejects_unknown_kind(sandbox):
    with pytest.raises(FMError, match="derived refs must be one of"):
        ops.record_derived(sandbox, "master:film", [], content="x")


# ------------------------------------------------------------------ 2. artifact owners
M6_OWNERS = {
    "animation_bible": "animation-director",
    "audio_bible": "sound-designer",
    "audio_cues": "sound-designer",
    "edit_plan": "post-supervisor",
    "post_plan": "post-supervisor",
}


@pytest.mark.parametrize("kind,role", sorted(M6_OWNERS.items()))
def test_m6_artifact_owner(kind, role):
    assert ARTIFACT_OWNERS[kind] == role


def test_m6_owner_roles_have_model_config():
    cfg = yaml.safe_load((REPO / "config/models.yaml").read_text())
    for role in set(M6_OWNERS.values()):
        assert role in cfg["roles"], role


def test_owner_mismatch_warning_for_m6_kind(sandbox):
    _to(sandbox, "ANIMATION")
    with testing.as_actor(AGENT):
        testing.write_md(sandbox, "12_post/POST_PLAN.md", "post_plan", "post_plan", "ANIMATION_PREVIEW",
                         [], "# Post plan\n")
    path = sandbox.dir / "12_post/POST_PLAN.md"
    text = path.read_text().replace("derived_from: []", "derived_from: []\n  owner_role: sound-designer")
    path.write_text(text)
    codes = [f.code for f in validate(sandbox).findings]
    assert "OWNER_MISMATCH" in codes


# ------------------------------------------------------------------ 3. canon domains
def test_canon_domain_owners():
    assert CANON_DOMAINS["animation-director"] == ("animation",)
    assert CANON_DOMAINS["sound-designer"] == ("audio",)
    assert "post-supervisor" not in CANON_DOMAINS           # audio moved to the sound-designer


def test_every_canon_domain_owned_is_a_real_domain_and_animation_audio_covered():
    owned = {d for doms in CANON_DOMAINS.values() for d in doms}
    assert owned <= set(DOMAINS)
    assert {"animation", "audio"} <= owned


def test_audio_canon_from_sound_designer_is_not_a_mismatch(sandbox):
    testing.write_canon(sandbox, "audio", [
        {"id": "audio.principles", "statement": "Wordless.", "rationale": "Follows tone.wordless.",
         "source": "agent:sound-designer"},
        {"id": "audio.stray", "statement": "x", "rationale": "y", "source": "agent:animation-director"},
    ])
    finds = [f for f in validate(sandbox).findings if f.code == "OWNER_MISMATCH"]
    assert [f.message.split(":")[0] for f in finds] == ["audio.stray"]


# ------------------------------------------------------------------ 4. gates
def test_g7_redefined_animation_audio_and_post_plan():
    g = GATES["G7"]
    assert g.name == "Animation, audio and post plan"
    assert g.closes_phase == "ANIMATION_PREVIEW"
    assert g.covers_phases == ("ANIMATION", "ANIMATION_PREVIEW")
    assert set(g.locks_domains) == {"animation", "audio"}
    assert not g.covers_shots


def test_g8_final_render_locks_nothing():
    g = GATES["G8"]
    assert g.name == "Final render"
    assert g.closes_phase == "FINAL_RENDER" and g.covers_phases == ("FINAL_RENDER",)
    assert g.locks_domains == ()


def test_no_g9_in_the_m6_lite_cut():
    assert "G9" not in GATES and list(GATES) == [f"G{i}" for i in range(1, 9)]


def test_review_for_gate_gains_g7_and_g8():
    assert REVIEW_FOR_GATE["G7"] == "qa/reviews/G7_REVIEW.md"
    assert REVIEW_FOR_GATE["G8"] == "qa/reviews/G8_REVIEW.md"
    assert "G6" not in REVIEW_FOR_GATE                       # G6 keeps its M3 behaviour


# ------------------------------------------------------------------ 5. contracts
def test_contract_tables():
    a = CONTRACTS["ANIMATION"]
    assert a.required == ("09_animation/ANIMATION_BIBLE.md",)
    assert a.per_shot == (ANIM_FILE,) and a.qa_reports == (MOTION_REPORT,)
    p = CONTRACTS["ANIMATION_PREVIEW"]
    assert set(p.required) == {"12_post/AUDIO_BIBLE.md", "12_post/AUDIO_CUES.yaml", "12_post/EDIT_PLAN.md",
                               "12_post/POST_PLAN.md", "qa/reviews/G7_REVIEW.md"}
    assert set(p.files) == {"10_blender/playblast/film.mp4", "12_post/audio/mix_48k_stereo.wav",
                            "12_post/animatic.mp4", "12_post/EDIT.edl"}
    assert p.per_shot == (ANIM_FILE,) and set(p.qa_reports) == {MOTION_REPORT, AUDIO_REPORT}
    f = CONTRACTS["FINAL_RENDER"]
    assert f.required == ("qa/reviews/G8_REVIEW.md",)
    assert f.authorizations == ("final-render",)
    assert f.files == ("11_render/final/MANIFEST.json",) and f.qa_reports == (FINAL_FRAMES_REPORT,)
    post = CONTRACTS["POST"]
    assert post.files == ("13_delivery/MANIFEST.json",) and post.qa_reports == (DELIVERY_REPORT,)


def test_earlier_contracts_are_unchanged():
    for phase in PHASES[:PHASES.index("STORYBOARD") + 1]:
        c = CONTRACTS.get(phase)
        if c:
            assert not (c.files or c.per_shot or c.qa_reports or c.authorizations), phase


def test_animation_contract_blocks_advance_until_complete(sandbox):
    _to(sandbox, "ANIMATION")
    with pytest.raises(StateError) as e:
        _advance(sandbox)
    msg = str(e.value)
    assert "ANIMATION_BIBLE.md" in msg and "anim.yaml for 3 shot(s)" in msg and MOTION_REPORT in msg
    _agent_produce(sandbox, "ANIMATION")
    assert _advance(sandbox).phase == "ANIMATION_PREVIEW"


def test_animation_contract_names_the_missing_shot(sandbox):
    _to(sandbox, "ANIMATION")
    _agent_produce(sandbox, "ANIMATION")
    (sandbox.dir / ANIM_FILE.format(shot="SC02_SH010")).unlink()
    with pytest.raises(StateError, match=r"for 1 shot\(s\): SC02_SH010"):
        _advance(sandbox)


@pytest.mark.parametrize("payload,needle", [
    ({"summary": {"fail": 2, "warn": 0}}, "reports 2 FAIL"),
    ("not json", "unreadable"),
    ({"rows": []}, "unreadable"),
    ({"summary": {"fail": "x"}}, "unreadable"),
])
def test_qa_report_with_fail_or_garbage_blocks(sandbox, payload, needle):
    _to(sandbox, "ANIMATION")
    _agent_produce(sandbox, "ANIMATION")
    rp = sandbox.dir / MOTION_REPORT
    rp.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    with pytest.raises(StateError, match=needle):
        _advance(sandbox)


def test_missing_qa_report_blocks(sandbox):
    _to(sandbox, "ANIMATION")
    _agent_produce(sandbox, "ANIMATION")
    (sandbox.dir / MOTION_REPORT).unlink()
    with pytest.raises(StateError, match="missing qa/motion_report.json"):
        _advance(sandbox)


def test_g7_submit_needs_every_deliverable(sandbox):
    _to(sandbox, "ANIMATION_PREVIEW")
    with pytest.raises(ValidationFailed) as e:
        _submit(sandbox)
    msg = str(e.value)
    for needle in ("AUDIO_BIBLE.md", "AUDIO_CUES.yaml", "EDIT_PLAN.md", "POST_PLAN.md", "G7_REVIEW.md",
                   "10_blender/playblast/film.mp4", "12_post/audio/mix_48k_stereo.wav",
                   "12_post/animatic.mp4", "12_post/EDIT.edl", AUDIO_REPORT):
        assert needle in msg, needle


@pytest.mark.parametrize("victim", [
    "10_blender/playblast/film.mp4", "12_post/audio/mix_48k_stereo.wav", "12_post/animatic.mp4",
    "12_post/EDIT.edl", "12_post/AUDIO_CUES.yaml", "qa/audio_report.json",
])
def test_g7_submit_blocked_by_each_missing_item(sandbox, victim):
    _to(sandbox, "ANIMATION_PREVIEW")
    _agent_produce(sandbox, "ANIMATION_PREVIEW")
    (sandbox.dir / victim).unlink()
    with pytest.raises(ValidationFailed, match=victim.replace(".", r"\.")):
        _submit(sandbox)


def test_g7_audio_fail_blocks_submit(sandbox):
    _to(sandbox, "ANIMATION_PREVIEW")
    _agent_produce(sandbox, "ANIMATION_PREVIEW")
    (sandbox.dir / AUDIO_REPORT).write_text(json.dumps({"summary": {"fail": 1}}))
    with pytest.raises(ValidationFailed, match="audio_report.json reports 1 FAIL"):
        _submit(sandbox)


def test_g7_review_must_cover_anim_and_post_artifacts(sandbox):
    """The G7 review is stale-checked like G1-G5: it must list every ANIMATION/ANIMATION_PREVIEW artifact."""
    _to(sandbox, "ANIMATION_PREVIEW")
    _agent_produce(sandbox, "ANIMATION_PREVIEW")
    review = sandbox.dir / "qa/reviews/G7_REVIEW.md"
    text = review.read_text()
    assert "artifact:post_plan" in text and "artifact:anim_sc01_sh010" in text
    review.write_text(text.replace("  - ref: artifact:post_plan\n", "").replace(
        "- ref: artifact:post_plan\n", ""))
    with pytest.raises(ValidationFailed, match="does not review: .*artifact:post_plan"):
        _submit(sandbox)


def test_full_m6_flow_to_complete_and_gate_effects(sandbox):
    _to(sandbox, "ANIMATION_PREVIEW")
    _agent_produce(sandbox, "ANIMATION_PREVIEW")
    st = _submit(sandbox)
    assert st.gates["G7"].status == "awaiting_approval"
    st = _approve(sandbox, "G7")
    assert st.gates["G7"].status == "approved"
    # G7 locks the animation and audio domains, nothing else new
    assert st.canon["audio.principles"].status.value == "LOCKED"
    assert {"artifact:audio_bible", "artifact:edit_plan", "artifact:post_plan", "artifact:audio_cues",
            "artifact:animation_bible", "artifact:g7_review"} <= set(st.gates["G7"].approved_hashes)
    # approving G7 does NOT authorize the final render
    assert not st.authorizations
    with pytest.raises(StateError, match="authorization"):
        _advance(sandbox)
    with testing.as_actor(HUMAN):
        ops.authorize(sandbox, "final-render", sandbox_confirm=True)
    assert _advance(sandbox).phase == "FINAL_RENDER"
    # G8
    with pytest.raises(ValidationFailed) as e:
        _submit(sandbox)
    assert "G8_REVIEW.md" in str(e.value) and "11_render/final/MANIFEST.json" in str(e.value)
    _agent_produce(sandbox, "FINAL_RENDER")
    _submit(sandbox)
    before = {cid: c.status for cid, c in ops.load_state(sandbox).canon.items()}
    st = _approve(sandbox, "G8")
    assert {cid: c.status for cid, c in st.canon.items()} == before      # G8 locks nothing
    assert _advance(sandbox).phase == "POST"
    # POST has no gate: contract enforced on advance
    with pytest.raises(StateError, match="13_delivery/MANIFEST.json"):
        _advance(sandbox)
    _agent_produce(sandbox, "POST")
    assert _advance(sandbox).phase == "DELIVERY"
    assert _advance(sandbox).phase == "COMPLETE"
    rep = validate(sandbox)
    assert not rep.errors, [str(f) for f in rep.errors]


def test_post_qa_fail_blocks_leaving_post(sandbox):
    _to(sandbox, "POST")
    _agent_produce(sandbox, "POST")
    (sandbox.dir / DELIVERY_REPORT).write_text(json.dumps({"summary": {"fail": 3}}))
    with pytest.raises(StateError, match="delivery_report.json reports 3 FAIL"):
        _advance(sandbox)


def test_authorization_contract_is_checked_directly(sandbox):
    """`_contract_extras` re-checks the authorization even if the ledger path into FINAL_RENDER changes."""
    loaded = sandbox.load()
    out = ops._contract_extras(sandbox, CONTRACTS["FINAL_RENDER"], loaded)
    assert any("fm authorize final-render" in m for m in out)
    with testing.as_actor(HUMAN):
        ops.authorize(sandbox, "final-render", sandbox_confirm=True)
    out = ops._contract_extras(sandbox, CONTRACTS["FINAL_RENDER"], sandbox.load())
    assert not any("authorize" in m for m in out)


# ------------------------------------------------------------------ 6. authorize final-render (human only)
def test_authorize_final_render_is_the_only_authorizable_action():
    assert ops.AUTHORIZABLE == ("final-render",)


def test_agent_cannot_authorize_final_render(sandbox):
    with testing.as_actor("agent:blender-td"), pytest.raises(AuthorityError, match="human-only"):
        ops.authorize(sandbox, "final-render", sandbox_confirm=True)
    assert not ops.load_state(sandbox).authorizations


def test_authorize_refuses_unknown_actions(sandbox):
    with testing.as_actor(HUMAN), pytest.raises(FMError, match="can only authorize"):
        ops.authorize(sandbox, "G7", sandbox_confirm=True)


def test_cli_authorize_refused_for_non_interactive_agent(sandbox):
    """The CLI path agents would use: refused, and nothing is written to the ledger."""
    n = len(ops.Ledger(sandbox.ledger_path).records())
    r = CliRunner().invoke(cli, ["-p", "last_signal", "authorize", "final-render", "--sandbox-confirm"])
    assert isinstance(r.exception, AuthorityError) and "human-only" in str(r.exception)
    r = CliRunner().invoke(cli, ["-p", "last_signal", "authorize", "final-render"])
    assert isinstance(r.exception, AuthorityError)
    assert len(ops.Ledger(sandbox.ledger_path).records()) == n


def test_cli_authorize_choice_is_final_render_only():
    r = CliRunner().invoke(cli, ["authorize", "--help"])
    assert "final-render" in r.output and "G7" not in r.output


def test_settings_deny_list_still_covers_authorize_and_human_actions():
    cfg = json.loads((REPO / ".claude/settings.json").read_text())
    deny, allow = set(cfg["permissions"]["deny"]), set(cfg["permissions"]["allow"])
    for rule in ("Bash(fm authorize:*)", "Bash(*fm authorize*)", "Bash(fm approve:*)", "Bash(fm reject:*)",
                 "Bash(fm revise:*)", "Bash(fm amend:*)", "Bash(fm canon lock:*)", "Bash(fm canon approve:*)",
                 "Bash(fm canon reject:*)", "Bash(fm change approve:*)", "Bash(fm change reject:*)",
                 "Bash(*--sandbox-confirm*)", "Bash(*FM_ACTOR=*)", "Edit(projects/*/state.yaml)",
                 "Write(projects/*/state.yaml)", "Edit(projects/*/.fm/**)", "Write(projects/*/.fm/**)"):
        assert rule in deny, rule
    assert not any("authorize" in a for a in allow)
    assert cfg["env"]["FM_ACTOR"].startswith("agent:")


# ------------------------------------------------------------------ 7. migration safety
def test_project_at_g6_is_unaffected_by_m6_tables(sandbox):
    """A project that predates M6 (G1-G6 approved, PREVIEW) still validates and its approvals hold."""
    _to(sandbox, "ANIMATION")
    st = ops.load_state(sandbox)
    assert all(st.gates[f"G{i}"].status == "approved" for i in range(1, 7))
    rep = validate(sandbox)
    assert not rep.errors, [str(f) for f in rep.errors]
    for i in range(1, 7):
        assert gate_health(f"G{i}", st, rep.loaded, rep.graph) == []
    # entering ANIMATION needs no M6 deliverable
    assert st.phase == "ANIMATION"


def test_last_signal_ledger_still_validates_and_keeps_g1_to_g6(repo):
    """Copy of the real project (read-only source): ledger replays, 0 errors, G1-G6 stay approved."""
    src = REPO / "projects" / "last_signal"
    if not (src / "state.yaml").exists():
        pytest.skip("real project not present")
    dst = repo / "projects" / "last_signal"
    shutil.copytree(src, dst)
    p = Project(repo, "last_signal")
    rep = validate(p)
    assert not rep.errors, [str(f) for f in rep.errors]
    st = ops.load_state(p)
    assert st.phase == "PREVIEW"
    assert all(st.gates[f"G{i}"].status == "approved" for i in range(1, 7))
    assert st.gates["G7"].status == "pending" and st.gates["G8"].status == "pending"
    for i in (1, 2, 3, 4, 6):
        assert gate_health(f"G{i}", st, rep.loaded, rep.graph) == [], i
    # no M6 rule reaches back into PREVIEW
    assert ops._contract_problems(p, "PREVIEW", rep.loaded) == []
