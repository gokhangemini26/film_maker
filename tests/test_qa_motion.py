"""`fm qa motion` / `fm check anim`: tier 0 spec-level motion checks. Pure `analyze` tests build the inputs by hand
(one negative case per check); the project tests cover the report file, the derived node, the CLI and the contract."""
import json

import pytest
from click.testing import CliRunner

from fm import animvocab as V
from fm import qa_motion as Q
from fm.cli import cli
from fm.io import write_yaml
from fm.phases import CONTRACTS, MOTION_REPORT
from fm.schemas import AnimationTracks

from .test_animation_schema import _baked, _frames, _write, anim, film  # noqa: F401


# ---------------------------------------------------------------- builders
def T(sid="SC01_SH010", frames=40, **over):
    d = anim(**{"shot_id": sid, "frames": frames, "props": {}, "events": [], **over})
    d["fm"] = {**d["fm"], "id": "anim_" + sid.lower()}
    return AnimationTracks.model_validate(d)


def S(sid="SC01_SH010", frames=40, tracks="default", start=0, **kw):
    scene = kw.pop("scene", sid.split("_")[0])
    if tracks == "default":
        tracks = T(sid, frames)
    kw.setdefault("characters", ["ren"])
    return Q.ShotInfo(sid, scene, frames, start, tracks=tracks, anim_ref="artifact:anim_" + sid.lower(), **kw)


def run(*shots, strict=False, **kw):
    return Q.analyze(Q.Inputs(shots=list(shots), strict=strict, **kw))


def hits(rep, shot, sev, needle):
    return [m for s, m in rep.rows.get(shot, []) if s == sev and needle in m]


def props(**p):
    return T(props=p)


# ---------------------------------------------------------------- presence
def test_missing_anim_file_is_warn_and_fail_only_when_strict():
    assert hits(run(S(tracks=None)), "SC01_SH010", "WARN", "no anim file")
    assert hits(run(S(tracks=None), strict=True), "SC01_SH010", "FAIL", "no anim file")
    stub = AnimationTracks.model_validate({"fm": T().fm.model_dump(), "shot_id": "SC01_SH010"})
    assert hits(run(S(tracks=stub)), "SC01_SH010", "WARN", "stub")
    assert hits(run(S(tracks=stub), strict=True), "SC01_SH010", "FAIL", "stub")


def test_a_clean_shot_has_no_findings():
    assert run(S()).rows["SC01_SH010"] == []


# ---------------------------------------------------------------- timing and vocabulary (anim lint surfaced as FAIL)
def test_frame_count_key_range_order_and_vocabulary_fail():
    assert hits(run(S(frames=41, tracks=T(frames=40))), "SC01_SH010", "FAIL", "ANIM_FRAMES")
    d = anim(shot_id="SC01_SH010", frames=40, props={}, events=[])
    d["characters"]["ren"]["pose"][1]["f"] = 45                      # past the last frame
    assert hits(run(S(tracks=AnimationTracks.model_validate(d))), "SC01_SH010", "FAIL", "ANIM_RANGE")
    d = anim(shot_id="SC01_SH010", frames=40, props={}, events=[])
    d["characters"]["ren"]["pose"][1]["f"] = 0                       # not increasing
    assert hits(run(S(tracks=AnimationTracks.model_validate(d))), "SC01_SH010", "FAIL", "ANIM_ORDER")
    d = anim(shot_id="SC01_SH010", frames=40, props={}, events=[])
    d["characters"]["ren"]["pose"][1]["ref"] = "car_sleeping"
    assert hits(run(S(tracks=AnimationTracks.model_validate(d))), "SC01_SH010", "FAIL", "ANIM_VOCAB")


def test_illegal_prop_transition_and_comic_face_after_the_turn_fail():
    t = props(crank_charger=[{"f": 0, "loc": "glovebox"}, {"f": 4, "loc": "lap"}])
    assert hits(run(S(tracks=t)), "SC01_SH010", "FAIL", "ANIM_PROP_TRANSITION")
    t = T("SC04_SH030")                                              # default face is the comic `freeze`
    assert hits(run(S("SC04_SH030", tracks=t)), "SC04_SH030", "FAIL", "ANIM_FACE_AFTER_TURN")


def test_hold_shorter_than_its_minimum_fails():
    t = T(holds=[{"f0": 0, "f1": 9, "scope": "phone", "min_f": 41}])
    assert hits(run(S(tracks=t)), "SC01_SH010", "FAIL", "ANIM_HOLD")


def test_long_gap_between_pose_keys_warns_unless_a_body_hold_covers_it():
    d = anim(shot_id="SC01_SH010", frames=100, props={}, events=[])
    d["characters"]["ren"]["pose"] = [{"f": 0, "ref": "car_upright", "ease": "hold"}]
    t = AnimationTracks.model_validate(d)
    assert hits(run(S(frames=100, tracks=t)), "SC01_SH010", "WARN", "no pose key between")
    d["holds"] = [{"f0": 0, "f1": 98, "scope": "body"}]
    t = AnimationTracks.model_validate(d)
    assert not hits(run(S(frames=100, tracks=t)), "SC01_SH010", "WARN", "no pose key between")


# ---------------------------------------------------------------- prop continuity across shots
def _lid(f, state, **k):
    return props(glovebox_lid=[{"f": f, "state": state, **k}])


def test_prop_jump_at_a_cut_fails_and_a_stated_change_passes():
    a = S("SC01_SH010", tracks=_lid(5, "open_down"))
    jump = S("SC01_SH020", tracks=_lid(0, "closed"))
    assert hits(run(a, jump), "SC01_SH020", "FAIL", "glovebox_lid.state jumps at the cut")
    stated = S("SC01_SH020", tracks=_lid(0, "closed", rationale="lid shut in the cut-away"))
    assert not hits(run(a, stated), "SC01_SH020", "FAIL", "jumps")
    in_shot = S("SC01_SH020", tracks=_lid(4, "closed"))
    assert not hits(run(a, in_shot), "SC01_SH020", "FAIL", "glovebox_lid")
    same = S("SC01_SH020", tracks=_lid(0, "open_down"))
    assert not hits(run(a, same), "SC01_SH020", "FAIL", "glovebox_lid")


def test_hand_held_attach_across_a_scene_change_is_only_a_warn():
    a = S("SC03_SH070", tracks=props(phone_ren=[{"f": 0, "attach": "hand_l"}]))
    b = S("SC04_SH010", tracks=props(phone_ren=[{"f": 0, "attach": "hands_both"}]))
    rep = run(a, b)
    assert hits(rep, "SC04_SH010", "WARN", "changes between scenes") and not hits(rep, "SC04_SH010", "FAIL", "phone_ren")


def test_illegal_transition_across_shots_fails():
    a = S("SC01_SH010", tracks=props(crank_charger=[{"f": 0, "loc": "falling"}]))
    b = S("SC01_SH020", tracks=props(crank_charger=[{"f": 5, "loc": "lap"}]))      # falling -> thighs only
    assert hits(run(a, b), "SC01_SH020", "FAIL", "not a legal transition")


def test_other_persistent_props_and_a_shot_without_motion_data():
    a = S("SC01_SH010", tracks=props(phone_ren=[{"f": 0, "attach": "hand_l"}], hana_headphones=[{"f": 3, "state": "neck"}]))
    b = S("SC01_SH020", tracks=props(phone_ren=[{"f": 0, "attach": "hands_both"}]))
    c = S("SC01_SH030", tracks=props(hana_headphones=[{"f": 0, "state": "head"}]))
    rep = run(a, b, c)
    assert hits(rep, "SC01_SH020", "FAIL", "phone_ren.attach jumps")
    assert hits(rep, "SC01_SH030", "FAIL", "hana_headphones.state jumps")
    # a shot with no anim file in between: state is unknown, so nothing is compared
    gap = run(a, S("SC01_SH020", tracks=None), b)
    assert not hits(gap, "SC01_SH030", "FAIL", "jumps") and not hits(gap, "SC01_SH020", "FAIL", "jumps")
    # car_body is not persistent
    x = S("SC01_SH010", tracks=props(car_body=[{"f": 0, "state": "cough"}]))
    y = S("SC01_SH020", tracks=props(car_body=[{"f": 0, "state": "still"}]))
    assert not [1 for r in run(x, y).rows.values() for s, _ in r if s == "FAIL"]


def test_rear_view_mirror_tilt_jump_fails():
    a = S("SC01_SH010", tracks=props(rear_view_mirror=[{"f": 2, "tilt_deg": 4.0}]))
    b = S("SC01_SH020", tracks=props(rear_view_mirror=[{"f": 0, "tilt_deg": 0.0}]))
    assert hits(run(a, b), "SC01_SH020", "FAIL", "rear_view_mirror.tilt_deg jumps")


CANON = {
    "continuity.props.passenger_door": {"SC01": "closed", "SC02": "flung_open_by_ren_exiting_left_open",
                                        "SC04": "open_60deg", "SC06": "open_60deg"},
    "continuity.props.glovebox_and_crank": {
        "SC01": {"glovebox": "closed_open_closed", "crank": "lap_then_back_in_glovebox_folded"},
        "SC04": {"glovebox": "opened_left_down", "crank": "both_hands_then_right_hand_cranking"},
        "SC04_end": {"crank": "in_lap"},
        "SC06": {"glovebox": "lid_down", "crank": "in_lap_arm_out_pip_off"}},
    "continuity.hana.headphones": {"SC05_start": "on_head", "SC05_after_wake": "around_neck"},
}


def test_canon_props_are_enforced_per_scene():
    door = S("SC01_SH010", tracks=props(passenger_door=[{"f": 3, "state": "open_60"}]))
    assert hits(run(door, canon=CANON), "SC01_SH010", "FAIL", "canon continuity.props.passenger_door says closed")
    sc02 = S("SC02_SH010", tracks=props(passenger_door=[{"f": 3, "state": "open_60"}, {"f": 30, "state": "closed"}]))
    assert hits(run(sc02, canon=CANON), "SC02_SH010", "FAIL", "ends SC02 as closed")
    ok = S("SC04_SH010", tracks=props(passenger_door=[{"f": 0, "state": "open_60"}]))
    assert not hits(run(ok, canon=CANON), "SC04_SH010", "FAIL", "passenger_door")
    box = S("SC01_SH150", tracks=props(glovebox_lid=[{"f": 2, "state": "open_down"}],
                                       crank_charger=[{"f": 0, "loc": "glovebox", "arm": "folded"}]))
    assert hits(run(box, canon=CANON), "SC01_SH150", "FAIL", "glovebox_lid.state ends SC01 as open_down")
    sc06 = S("SC06_SH010", tracks=props(glovebox_lid=[{"f": 0, "state": "closed"}],
                                        crank_charger=[{"f": 0, "loc": "lap", "arm": "folded"}]))
    rep = run(sc06, canon=CANON)
    assert hits(rep, "SC06_SH010", "FAIL", "glovebox_lid.state is closed") and hits(rep, "SC06_SH010", "FAIL", "crank_charger.arm")
    hp = S("SC05_SH010", tracks=props(hana_headphones=[{"f": 0, "state": "neck"}]))
    assert hits(run(hp, canon=CANON), "SC05_SH010", "FAIL", "starts SC05 as neck")
    # scene-edge expectations wait until the scene's last shot has an anim file
    early = run(S("SC02_SH010", tracks=props(passenger_door=[{"f": 3, "state": "closed"}])), S("SC02_SH020", tracks=None),
                canon=CANON)
    assert not hits(early, "SC02_SH010", "FAIL", "ends SC02")
    assert hits(run(S("SC01_SH010", tracks=props(phone_ren=[{"f": 0, "attach": "hand_r"}])), canon=CANON),
                "SC01_SH010", "WARN", "left hand")


# ---------------------------------------------------------------- camera
CAM_SPEC = {"movement": "dolly_in", "start_position": [0, 0, 1], "end_position": [0, 0.18, 1]}


def _dolly(start_f=0, end_f=39, dist=0.18, **k):
    return T(camera={"move": "dolly_in", "start_f": start_f, "end_f": end_f, "dist_m": dist, **k})


def test_camera_speed_cap_length_scene_and_count():
    cap = {"camera.movement.push_in": {"max_speed_m_s": 0.15, "max_count_film": 1, "scene": "SC01"}}
    ok = S(tracks=_dolly(), camera=CAM_SPEC)
    assert not hits(run(ok, canon=cap), "SC01_SH010", "FAIL", "camera")
    fast = S(tracks=_dolly(end_f=20), camera=CAM_SPEC)                        # 0.18 m in 20 frames = 0.216 m/s
    assert hits(run(fast, canon=cap), "SC01_SH010", "FAIL", "exceeds the 0.15 m/s cap")
    eased = S(tracks=_dolly(end_f=30, ease_in_f=[0, 6], ease_out_f=[24, 30]), camera=CAM_SPEC)   # peak > mean
    assert hits(run(eased, canon=cap), "SC01_SH010", "FAIL", "exceeds")
    long = S(tracks=_dolly(dist=0.3), camera=CAM_SPEC)
    assert hits(run(long, canon=cap), "SC01_SH010", "FAIL", "dolly length")
    declared = S(tracks=_dolly(peak_speed_mps=0.2), camera=CAM_SPEC)
    assert hits(run(declared, canon=cap), "SC01_SH010", "FAIL", "declared camera peak_speed_mps")
    off = {"camera.movement.push_in": {"max_speed_m_s": 0.15, "scene": "SC04"}}
    assert hits(run(ok, canon=off), "SC01_SH010", "FAIL", "outside SC04")
    late = S("SC05_SH010", tracks=_dolly(), camera=CAM_SPEC)
    assert hits(run(late, canon=off), "SC05_SH010", "FAIL", "after SC04")
    two = run(ok, S("SC01_SH020", tracks=_dolly(), camera=CAM_SPEC), canon=cap)
    assert hits(two, "FILM", "FAIL", "camera moves")


def test_default_cap_applies_without_canon():
    fast = S(tracks=_dolly(end_f=20), camera=CAM_SPEC)
    assert hits(run(fast), "SC01_SH010", "FAIL", "0.15 m/s cap")


# ---------------------------------------------------------------- locomotion
def test_locomotion_speed_warns():
    d = anim(shot_id="SC02_SH010", frames=40, props={}, events=[])
    d["characters"]["ren"]["move"] = {"gait": "run_phone_out", "speed_mps": 4.0,
                                      "path": [{"f": 0, "x": 0, "y": 0}, {"f": 39, "x": 30, "y": 0}]}
    rep = run(S("SC02_SH010", tracks=AnimationTracks.model_validate(d)))
    assert hits(rep, "SC02_SH010", "WARN", "path speed peaks")
    assert hits(rep, "SC02_SH010", "WARN", "declared speed_mps")
    d["characters"]["ren"]["move"]["path"] = [{"f": 0, "x": 0, "y": 0}, {"f": 39, "x": 4.9, "y": 0}]   # 3 m/s
    assert not hits(run(S("SC02_SH010", tracks=AnimationTracks.model_validate(d))), "SC02_SH010", "WARN", "path speed")


# ---------------------------------------------------------------- sound_sync text vs events
def test_sound_sync_frames_need_named_events():
    text = {"sound_sync": "clunk on f5; silence from f30; ratchet f10, then every 24 frames"}
    t = T(events=[{"f": 5, "id": "clunk", "kind": "sound"}])
    rep = run(S(tracks=t, animation=text))
    msg = hits(rep, "SC01_SH010", "WARN", "sound_sync")
    assert msg and "f10" in msg[0] and "f34" in msg[0] and "f5" not in msg[0].split("(sound_sync")[0].replace("f5x", "")
    assert "f30" not in msg[0].split("(sound_sync")[0]
    t = T(events=[{"f": 5, "id": "clunk"}, {"f": 10, "id": "a"}, {"f": 34, "id": "b"}])
    assert not hits(run(S(tracks=t, animation=text)), "SC01_SH010", "WARN", "sound_sync")


def test_sound_sync_counts_derived_crank_tops():
    d = anim(shot_id="SC04_SH060", frames=40, props={}, events=[])
    d["characters"]["ren"] = {"pose": [{"f": 0, "ref": "kerb_crank_hold", "ease": "hold"}],
                              "move": {"gait": "crank_turn", "first_top_f": 4}}
    t = AnimationTracks.model_validate(d)
    ok = run(S("SC04_SH060", tracks=t, animation={"sound_sync": "ratchet click at f4, then every 24 frames"}))
    assert not hits(ok, "SC04_SH060", "WARN", "sound_sync")
    bad = run(S("SC04_SH060", tracks=t, animation={"sound_sync": "ratchet click at f6"}))
    assert hits(bad, "SC04_SH060", "WARN", "f6")


# ---------------------------------------------------------------- phone screen
def row(pct=4, colour="red", bolt=False, **k):
    return {"ui": "compose_1_line", "pct": pct, "colour": colour, "bolt": bolt, **k}


def ui(rows, *shots, canon=None, **kw):
    c = {"look.style.phone_screen.states_by_shot": {**rows, "colour_hex": {"charcoal": "#2B303B", "red": "#E5483B"}}}
    c.update(canon or {})
    return run(*shots, canon=c, **kw)


def test_a_consistent_screen_is_clean():
    assert ui({"SC01_SH010": row()}, S()).rows["SC01_SH010"] == []


def test_zero_percent_missing_digit_and_wrong_colour_fail():
    assert hits(ui({"SC01_SH010": row(pct=0)}, S()), "SC01_SH010", "FAIL", "0 %")
    r = row()
    r.pop("pct")
    assert hits(ui({"SC01_SH010": r}, S()), "SC01_SH010", "FAIL", "digit missing")
    assert hits(ui({"SC01_SH010": row(pct=4, colour="charcoal")}, S()), "SC01_SH010", "FAIL", "colour disagrees")


def test_battery_must_match_the_scene_in_canon_and_not_jump_at_cuts():
    canon = {"continuity.battery": {"SC01": [5, 4, 3], "off_screen_change": "SC03_to_SC04_2_to_1"}}
    assert hits(ui({"SC01_SH010": row(pct=2)}, S(), canon=canon), "SC01_SH010", "FAIL", "not in canon continuity.battery")
    rows = {"SC01_SH010": row(pct=4), "SC01_SH020": row(pct=3)}
    rep = ui(rows, S(), S("SC01_SH020"))
    assert hits(rep, "SC01_SH020", "FAIL", "at f0")
    rows = {"SC03_SH070": row(pct=2), "SC04_SH010": row(pct=1)}
    ok = ui(rows, S("SC03_SH070"), S("SC04_SH010"), canon=canon)
    assert not hits(ok, "SC04_SH010", "FAIL", "at f0")
    assert hits(ui(rows, S("SC03_SH070"), S("SC04_SH010")), "SC04_SH010", "FAIL", "at f0")          # no canon exception


def test_bolt_while_the_crank_arm_is_folded_fails():
    canon = {"continuity.battery": {"SC04_bolt_on": "while_cranking"}}
    rows = {"SC04_SH050": row(pct=1, bolt=True)}
    folded = S("SC04_SH050", tracks=props(crank_charger=[{"f": 0, "arm": "folded"}]))
    assert hits(ui(rows, folded, canon=canon), "SC04_SH050", "FAIL", "bolt shown")
    out = S("SC04_SH050", tracks=props(crank_charger=[{"f": 0, "arm": "folded"}, {"f": 10, "arm": "unfolded"}]))
    assert hits(ui(rows, out, canon=canon), "SC04_SH050", "FAIL", "f0-9")
    live = S("SC04_SH050", tracks=props(crank_charger=[{"f": 0, "arm": "unfolded"}]))
    assert not hits(ui(rows, live, canon=canon), "SC04_SH050", "FAIL", "bolt shown")


def test_ui_events_need_a_table_row_the_right_phone_and_dips_for_flicker():
    ev = T(ui_timeline=[{"f": 2, "event": "dip", "dur_f": 2}])
    assert hits(ui({}, S(tracks=ev)), "SC01_SH010", "FAIL", "no states_by_shot row")
    wrong = T(ui_timeline=[{"f": 2, "event": "dip", "dur_f": 2, "phone": "hana"}])
    assert hits(ui({"SC01_SH010": row()}, S(tracks=wrong)), "SC01_SH010", "FAIL", "ui:")
    flick = row(brightness="flicker")
    assert hits(ui({"SC01_SH010": flick}, S()), "SC01_SH010", "WARN", "flicker")
    assert not hits(ui({"SC01_SH010": flick}, S(tracks=ev)), "SC01_SH010", "WARN", "flicker")


def test_a_stale_resolved_ui_timeline_fails():
    from fm.uitimeline import expand_shot
    table = {"SC01_SH010": row(pct=4), "colour_hex": {}}
    fresh = expand_shot(table, "SC01_SH010", 40)
    stale = expand_shot({"SC01_SH010": row(pct=3)}, "SC01_SH010", 40)
    good = S(resolved={"frames": {"count": 40}, "ui_timeline": json.loads(json.dumps(fresh))})
    bad = S(resolved={"frames": {"count": 40}, "ui_timeline": json.loads(json.dumps(stale))})
    assert not hits(ui({"SC01_SH010": row(pct=4)}, good), "SC01_SH010", "FAIL", "resolved ui_timeline")
    assert hits(ui({"SC01_SH010": row(pct=4)}, bad), "SC01_SH010", "FAIL", "resolved ui_timeline differs")


# ---------------------------------------------------------------- running time and resolved files
def test_running_time_scene_film_and_resolved_totals():
    rep = run(S(), scenes=[("SC01", 4.0)])
    assert hits(rep, "SC01", "WARN", "scene running time 40 f")
    assert not hits(run(S(), scenes=[("SC01", 40 / 24)]), "SC01", "WARN", "running time")
    assert hits(run(S(), brief_duration_s=60), "FILM", "WARN", "brief says 60 s")
    assert hits(run(S(), film_total_resolved=99), "FILM", "FAIL", "shot table adds up to 40")


def test_stale_resolved_shot_files():
    assert hits(run(S(resolved={"frames": {"count": 41}, "motion": None})), "SC01_SH010", "FAIL", "41 frames")
    assert hits(run(S(resolved={"frames": {"count": 40}, "motion": None})), "SC01_SH010", "WARN", "no motion block")
    assert hits(run(S(resolved={"frames": {"count": 40}, "motion": {"schema": "fm.motion/1"}})),
                "SC01_SH010", "WARN", "out of date")


def test_vocab_module_names_used_here_exist():
    assert "passenger_door" in V.PROPS and V.PROPS["glovebox_lid"]["persistent"]


# ---------------------------------------------------------------- project level: report, record, CLI, contract
def _prime(film):
    n = _frames(film, "SC01_SH010")
    _write(film, "SC01_SH010", anim(frames=n))


def test_check_writes_the_report_in_the_stills_shape_and_records_the_node(film):
    _prime(film)
    rep = Q.check(film)
    saved = json.loads((film.dir / MOTION_REPORT).read_text(encoding="utf-8"))
    assert saved == rep and set(saved["summary"]) == {"fail", "warn", "shots"}
    assert saved["summary"]["shots"] == len(film.load().shots) and saved["summary"]["fail"] == 0
    assert all(set(r) == {"shot", "findings"} and all(len(f) == 2 for f in r["findings"]) for r in saved["rows"])
    assert "qa:motion" in film.load().derived
    assert saved["summary"]["warn"] >= 1                                   # the other shots have no anim file yet
    before = film.load().derived["qa:motion"]
    Q.check(film, record=False)
    assert film.load().derived["qa:motion"].content_hash == before.content_hash


def test_strict_turns_missing_anim_files_into_fail(film):
    _prime(film)
    assert Q.check(film, strict=True)["summary"]["fail"] == len(film.load().shots) - 1


def test_cli_qa_motion_and_check_anim_alias_exit_codes(film):
    _prime(film)
    for cmd in (("qa", "motion"), ("check", "anim")):
        r = CliRunner().invoke(cli, ["-p", "last_signal", *cmd], standalone_mode=False, catch_exceptions=True)
        assert r.exception is None or getattr(r.exception, "code", 0) == 0, r.output
        assert "0 FAIL" in r.output and "qa/motion_report.json" in r.output
    r = CliRunner().invoke(cli, ["-p", "last_signal", "qa", "motion", "--strict", "--no-record"],
                           standalone_mode=False, catch_exceptions=True)
    assert getattr(r.exception, "code", None) == 1 and "FAIL" in r.output


def test_a_fail_makes_the_animation_contract_report_check_fail(film):
    n = _frames(film, "SC01_SH010")
    d = anim(frames=n)
    d["characters"]["ren"]["pose"][1]["ref"] = "car_sleeping"
    _write(film, "SC01_SH010", d)
    rep = Q.check(film)
    assert rep["summary"]["fail"] == 1
    assert MOTION_REPORT in CONTRACTS["ANIMATION"].qa_reports
