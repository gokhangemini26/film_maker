"""Structured shot animation: schema, vocabulary module, ANIM_* rules, canon proposals, JSON Schema."""
import copy
import json
import shutil
from pathlib import Path

import pytest
import yaml

from fm import animvocab as V
from fm import testing
from fm.animcheck import check_animation, crank_tops, lint_tracks
from fm.io import load_yaml, write_yaml
from fm.project import Project
from fm.schemas import EXPORTED, AnimationTracks, CanonEntry, anim_artifact_id
from fm.validate import validate

REPO = Path(__file__).resolve().parents[1]
LAST_SIGNAL = REPO / "projects" / "last_signal"


def anim(**over):
    """A small valid anim dict for SC01_SH010 (96 frames in the toy film, 40 in Last Signal)."""
    d = {
        "fm": {"id": "anim_sc01_sh010", "kind": "shot_animation", "phase": "ANIMATION", "status": "PROPOSED",
               "owner_role": "animation-director", "derived_from": [{"ref": "shot:SC01_SH010"}]},
        "shot_id": "SC01_SH010", "frames": 40, "vocab_version": V.VOCAB_VERSION,
        "rationale": "A held freeze then one small exhale keeps the gag on the stillness.",
        "characters": {"ren": {
            "pose": [{"f": 0, "ref": "car_upright", "ease": "hold", "note": "start"},
                     {"f": 10, "ref": "car_phone_up", "ease": "ease_in_out", "blend_f": 6, "note": "raise"}],
            "move": {"gait": "none"},
            "face": [{"f": 0, "ref": "freeze", "note": "held"}],
            "look": [{"f": 0, "target": "phone"}],
            "breath": [{"f": 0, "ref": "hold", "dur_f": 8}]}},
        "props": {"glovebox_lid": [{"f": 5, "state": "open_down", "ease": "gravity", "dur_f": 3, "note": "drops"}],
                  "phone_ren": [{"f": 0, "attach": "hand_l"}]},
        "events": [{"f": 5, "id": "lid_drop", "kind": "sound"}],
    }
    d.update(over)
    return d


def parse(d):
    return AnimationTracks.model_validate(d)


def codes(d, **kw):
    kw.setdefault("frame_count", 40)
    return [(lvl, c) for lvl, c, _, _ in lint_tracks(parse(d), **kw)]


# ---------------------------------------------------------------- vocabulary module
def test_vocabulary_names_are_unique_and_described():
    for name, values in V.enum_groups().items():
        assert len(values) == len(set(values)), f"duplicate names in {name}"
    poses = V.all_pose_names()
    assert len(poses) == len(set(poses)), "a pose name must mean one thing for every character"
    for ch, table in V.POSES.items():
        for pose, line in table.items():
            assert 20 < len(line) < 130 and line.endswith("."), f"{ch}.{pose} needs a one-line meaning"
    for table in (V.EASES, V.LOOK_TARGETS, V.BREATHS, V.EVENT_KINDS, V.UI_EVENTS, V.CAMERA_MOVES, V.HOLD_SCOPES):
        assert all(table.values())
    assert 12 <= len(V.POSES["ren"]) <= 16 and len(V.POSES["hana"]) == 4      # M6-lite size


def test_prop_transitions_only_use_declared_states():
    for prop, spec in V.PROPS.items():
        for fld, table in spec["transitions"].items():
            allowed = spec["fields"][fld]
            assert isinstance(allowed, tuple)
            for a, tos in table.items():
                assert a in allowed and set(tos) <= set(allowed), f"{prop}.{fld}"


def test_canon_proposals_are_proposed_only_and_well_formed():
    ents = V.canon_entry_dicts()
    ids = [e["id"] for e in ents]
    assert len(ids) == len(set(ids)) and all(i.startswith("animation.vocab.") for i in ids)
    for e in ents:
        ce = CanonEntry.model_validate(e)
        assert ce.status.value == "PROPOSED" and ce.rationale and ce.value["vocab_version"] == V.VOCAB_VERSION
    # the proposals carry exactly the module's names
    by_id = {e["id"]: e["value"] for e in ents}
    assert set(by_id["animation.vocab.pose.ren"]["presets"]) == set(V.POSES["ren"])
    assert set(by_id["animation.vocab.pose.hana"]["presets"]) == set(V.POSES["hana"])
    assert set(by_id["animation.vocab.prop_states"]["props"]) == set(V.PROPS)


@pytest.mark.skipif(not LAST_SIGNAL.exists(), reason="Last Signal project not present")
def test_faces_come_from_canon_and_canon_ids_exist():
    canon = {}
    for p in (LAST_SIGNAL / "canon").glob("*.yaml"):
        for e in yaml.safe_load(p.read_text(encoding="utf-8"))["entries"]:
            canon[e["id"]] = e
    ren = canon["characters.ren.expressions"]["value"]
    assert tuple(ren["comic_set"]) == V.FACES["ren"]["comic"] and tuple(ren["tender_set"]) == V.FACES["ren"]["tender"]
    assert tuple(canon["characters.hana.expressions"]["value"]["sequence"]) == V.FACES["hana"]["sequence"]
    for e in V.canon_entry_dicts():
        for ref in [*e["serves"], *e["depends_on"]]:
            assert ref in canon, f"{e['id']} points at unknown canon '{ref}'"
    # the ratifiable proposals written to the project match the module
    written = {i: e for i, e in canon.items() if i.startswith("animation.vocab.")}
    if written:
        for e in V.canon_entry_dicts():
            assert json.loads(json.dumps(written[e["id"]]["value"])) == json.loads(json.dumps(e["value"]))
            assert written[e["id"]]["status"] == "PROPOSED"


# ---------------------------------------------------------------- every committed anim file resolves
def _all_anim_files():
    return sorted((REPO / "projects").glob("*/09_animation/*.anim.yaml"))


def test_every_committed_anim_ref_resolves():
    files = _all_anim_files()
    for path in files:
        t = AnimationTracks.model_validate(load_yaml(path))
        assert path.name == f"{t.shot_id}.anim.yaml" and t.fm.id == anim_artifact_id(t.shot_id)
        errs = [(c, w, m) for lvl, c, w, m in lint_tracks(t) if lvl == "ERROR"]
        assert not errs, f"{path.name}: {errs}"


@pytest.mark.skipif(not (LAST_SIGNAL / "09_animation" / "SC01_SH090.anim.yaml").exists(), reason="example absent")
def test_example_anim_file_is_clean_in_project_context():
    project = Project(REPO, "last_signal")
    loaded = project.load()
    assert "SC01_SH090" in loaded.anims
    rows = [r for r in check_animation(project, loaded) if r[0] in ("ERROR", "WARN")]
    assert rows == []
    assert not [f for f in validate(project).errors]


# ---------------------------------------------------------------- schema
def test_stub_files_are_valid_and_carry_no_motion():
    t = parse({"fm": anim()["fm"], "shot_id": "SC01_SH010"})
    assert t.is_stub
    assert lint_tracks(t) == [("INFO", "ANIM_STUB", "", lint_tracks(t)[0][3])]


def test_unknown_fields_are_refused_and_free_text_is_optional():
    with pytest.raises(Exception):
        parse(anim(mystery=1))
    d = anim()
    for k in d["characters"]["ren"]["pose"]:
        k.pop("note", None)
    assert not [c for lvl, c in codes(d) if lvl == "ERROR"]


def test_json_schema_export_matches_committed_file():
    committed = json.loads((REPO / "schemas" / "json" / "anim.schema.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(EXPORTED["anim"].model_json_schema()))
    props = committed["$defs"]
    assert set(props["PoseKey"]["required"]) == {"f", "ref"}
    assert "ease_in_out" in props["PoseKey"]["properties"]["ease"]["enum"]
    assert "glovebox" in props["LookKey"]["properties"]["target"]["enum"]


# ---------------------------------------------------------------- ANIM_* rules
def test_a_valid_file_has_no_findings():
    assert [x for x in codes(anim(), shot_characters=["ren"], shot_movement="static") if x[0] != "INFO"] == []


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d["characters"]["ren"]["pose"][1].update(ref="car_sleeping"), "ANIM_VOCAB"),
    (lambda d: d["characters"]["ren"]["pose"][1].update(ref="desk_sketch"), "ANIM_VOCAB"),        # Hana's pose
    (lambda d: d["characters"]["ren"]["pose"][1].update(ease="wobble"), "ANIM_VOCAB"),
    (lambda d: d["characters"]["ren"]["look"][0].update(target="moon"), "ANIM_VOCAB"),
    (lambda d: d["characters"]["ren"]["breath"][0].update(ref="gasp"), "ANIM_VOCAB"),
    (lambda d: d["characters"]["ren"]["face"][0].update(ref="grin"), "ANIM_VOCAB"),
    (lambda d: d["characters"].update(bob={"pose": []}), "ANIM_VOCAB"),                           # no vocabulary
    (lambda d: d["props"].update(teapot=[{"f": 0, "state": "on"}]), "ANIM_VOCAB"),
    (lambda d: d["props"]["glovebox_lid"][0].update(state="ajar"), "ANIM_VOCAB"),
    (lambda d: d["props"]["glovebox_lid"][0].update(loc="thighs"), "ANIM_PROP"),                  # wrong field
    (lambda d: d["props"]["phone_ren"][0].pop("attach"), "ANIM_PROP"),                            # empty key
    (lambda d: d["characters"]["ren"]["pose"][1].update(f=60), "ANIM_RANGE"),
    (lambda d: d["characters"]["ren"]["pose"][1].update(f=0), "ANIM_ORDER"),
    (lambda d: d["characters"]["ren"]["pose"][1].update(blend_f=40), "ANIM_BLEND"),
    (lambda d: d["characters"]["ren"]["pose"][0].update(blend_f=3), "ANIM_BLEND"),
    (lambda d: d["characters"]["ren"]["pose"][1].update(ease="step"), "ANIM_BLEND"),
    (lambda d: d["characters"]["ren"]["move"].update(gait="run_phone_out"), "ANIM_PATH"),          # needs a path
    (lambda d: d["characters"]["ren"]["move"].update(path=[{"f": 0, "x": 0, "y": 0}, {"f": 5, "x": 1, "y": 0}]), "ANIM_PATH"),
    (lambda d: d["characters"]["ren"]["move"].update(gait="crank_turn"), "ANIM_PATH"),
    (lambda d: d["events"].append({"f": 6, "id": "lid_drop"}), "ANIM_EVENTS"),
    (lambda d: d["events"].append({"f": 41, "id": "late"}), "ANIM_RANGE"),
    (lambda d: d.update(frames=39), "ANIM_FRAMES"),
    (lambda d: d.update(vocab_version=99), "ANIM_VOCAB_VERSION"),
    (lambda d: d.update(preview_frames=[3, 3]), "ANIM_RANGE"),
    (lambda d: d.update(ui_timeline=[{"f": 3, "event": "slide", "dur_f": 2}]), "ANIM_UI"),              # no `to`
    (lambda d: d.update(ui_timeline=[{"f": 3, "event": "sparkle", "dur_f": 2}]), "ANIM_VOCAB"),
    (lambda d: d.update(holds=[{"f0": 0, "f1": 20, "scope": "body"}]), "ANIM_HOLD"),               # key at f10 inside
    (lambda d: d.update(holds=[{"f0": 2, "f1": 5, "scope": "body", "min_f": 10}]), "ANIM_HOLD"),
    (lambda d: d.update(camera={"move": "dolly_in"}), "ANIM_CAMERA"),
])
def test_anim_rules_fire(mutate, code):
    d = copy.deepcopy(anim())
    mutate(d)
    found = codes(d, shot_characters=["ren"], shot_movement="static")
    assert ("ERROR", code) in found, found


def test_character_must_be_in_the_shot():
    assert ("ERROR", "ANIM_CHARACTER") in codes(anim(), shot_characters=["hana"])


def test_camera_must_agree_with_the_shot():
    d = anim(camera={"move": "dolly_in", "start_f": 4, "end_f": 30, "dist_m": 0.18,
                     "ease_in_f": [4, 8], "ease_out_f": [28, 30]})
    assert not [x for x in codes(d, shot_movement="dolly_in") if x[0] == "ERROR"]
    assert ("ERROR", "ANIM_CAMERA") in codes(d, shot_movement="static")
    assert ("ERROR", "ANIM_CAMERA") in codes(anim(), shot_movement="dolly_in")


def test_prop_transitions_are_checked():
    d = anim(props={"crank_charger": [{"f": 0, "loc": "glovebox"}, {"f": 4, "loc": "lap"}]})   # skips falling/hand
    assert ("ERROR", "ANIM_PROP_TRANSITION") in codes(d)
    ok = anim(props={"crank_charger": [{"f": 0, "loc": "glovebox"}, {"f": 4, "loc": "falling"},
                                       {"f": 10, "loc": "thighs"}, {"f": 12, "arm": "folded", "pip": 0.0}]})
    assert not [x for x in codes(ok) if x[0] == "ERROR"]


def test_comic_faces_are_illegal_from_the_turn():
    d = anim(shot_id="SC04_SH030")
    assert ("ERROR", "ANIM_FACE_AFTER_TURN") in codes(d)                        # freeze is a comic-set face
    d["characters"]["ren"]["face"][0]["ref"] = "focused_calm"
    assert ("ERROR", "ANIM_FACE_AFTER_TURN") not in codes(d)
    assert ("ERROR", "ANIM_FACE_AFTER_TURN") not in codes(anim(shot_id="SC03_SH070"))


def test_crank_turn_phase_gives_handle_tops():
    from fm.schemas.animation import MoveTrack
    mv = MoveTrack(gait="crank_turn", start_f=30, first_top_f=56)
    assert crank_tops(mv, 80) == [56]
    assert crank_tops(MoveTrack(gait="crank_turn", first_top_f=0), 68) == [0, 24, 48]         # SC04_SH060
    assert crank_tops(MoveTrack(gait="crank_turn", first_top_f=4), 26) == [4]                 # SC04_SH070
    assert crank_tops(MoveTrack(gait="crank_turn", first_top_f=2), 58) == [2, 26, 50]         # SC04_SH080
    assert crank_tops(MoveTrack(gait="crank_turn", first_top_f=-8, stop_f=7), 28) == []       # SC04_SH090
    assert crank_tops(MoveTrack(gait="none"), 30) == []
    d = anim(characters={"ren": {"pose": [{"f": 0, "ref": "kerb_crank_hold", "ease": "hold"}],
                                 "move": {"gait": "crank_turn", "first_top_f": 4}}},
             props={}, events=[{"f": 4, "id": "handle_top"}])
    assert ("ERROR", "ANIM_EVENTS") in codes(d)                                             # derived, not hand-written


# ---------------------------------------------------------------- inside a project (validate)
def _film(sandbox):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        item = sandbox.load().shots["SC01_SH010"]
        data = load_yaml(item.path)
        data["characters"] = [{"id": "ren", "position": [0, 0, 0]}]
        write_yaml(item.path, data)
        testing.stamp_all(sandbox)
    return sandbox


@pytest.fixture(scope="module")
def _baked(tmp_path_factory):
    """The toy film driven to STORYBOARD once per module (about 14 s), with Ren in SC01_SH010."""
    from fm.ops import init_project
    mp = pytest.MonkeyPatch()
    root = tmp_path_factory.mktemp("baked") / "film_maker"
    shutil.copytree(REPO / "config", root / "config")
    shutil.copytree(REPO / "templates", root / "templates")
    (root / "projects").mkdir()
    mp.setenv("FM_ROOT", str(root))
    mp.setenv("FM_ACTOR", "agent:test")
    mp.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
    mp.delenv("FM_PROJECT", raising=False)
    try:
        _film(init_project(root, "last_signal", "Last Signal", sandbox=True))
    finally:
        mp.undo()
    return root


@pytest.fixture
def film(_baked, tmp_path, monkeypatch):
    root = tmp_path / "film_maker"
    shutil.copytree(_baked, root)
    monkeypatch.setenv("FM_ROOT", str(root))
    monkeypatch.setenv("FM_ACTOR", "agent:test")
    monkeypatch.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
    monkeypatch.delenv("FM_PROJECT", raising=False)
    monkeypatch.chdir(root)
    return Project(root, "last_signal")


def _write(project, shot_id, d):
    path = project.dir / "09_animation" / f"{shot_id}.anim.yaml"
    write_yaml(path, d)
    return path


def _frames(project, shot_id):
    from fm.resolve import film_format, frame_table
    loaded = project.load()
    return frame_table(loaded, film_format(loaded)["fps"])[shot_id]["frames"]


def test_validate_reports_anim_rules_with_where(film):
    n = _frames(film, "SC01_SH010")
    d = anim(frames=n)
    d["characters"]["ren"]["pose"][1]["ref"] = "car_sleeping"
    _write(film, "SC01_SH010", d)
    rep = validate(film)
    hits = [f for f in rep.errors if f.code == "ANIM_VOCAB"]
    assert hits and "SC01_SH010.anim.yaml" in hits[0].where and "characters.ren.pose[1]" in hits[0].where


def test_validate_checks_frames_filename_and_shot(film):
    _write(film, "SC01_SH010", anim(frames=7))
    assert "ANIM_FRAMES" in [f.code for f in validate(film).errors]
    (film.dir / "09_animation" / "SC01_SH010.anim.yaml").unlink()
    bad = anim(frames=_frames(film, "SC01_SH010"))
    bad["fm"]["id"] = "anim_wrong"
    _write(film, "SC01_SH010", bad)
    assert "ANIM_FILENAME" in [f.code for f in validate(film).errors]
    (film.dir / "09_animation" / "SC01_SH010.anim.yaml").unlink()
    ghost = anim(shot_id="SC09_SH010", frames=10)
    ghost["fm"]["id"] = "anim_sc09_sh010"
    write_yaml(film.dir / "09_animation" / "SC09_SH010.anim.yaml", ghost)
    assert "ANIM_SHOT_MISSING" in [f.code for f in validate(film).errors]


def test_a_clean_anim_file_validates_and_is_owned_by_the_animation_director(film):
    _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    with testing.as_actor(testing.AGENT):
        testing.stamp_all(film)
    rep = validate(film)
    assert not [f for f in rep.errors], [str(f) for f in rep.errors]
    assert not [f for f in rep.findings if f.code == "OWNER_MISMATCH" and "anim_" in f.message]
    assert anim_artifact_id("SC01_SH010") in film.load().artifacts
