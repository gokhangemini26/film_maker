"""Per-frame animation state (blender/fm_blender/animate.py, framesel.py): pure python, no rendering.
Needs mathutils (bpy wheel) and the resolved shots of projects/last_signal/09_resolved."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
RES = ROOT / "projects" / "last_signal" / "09_resolved"

try:
    from fm_blender import animate as A  # noqa: E402
    from fm_blender import framesel as FS  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

if not (RES / "SC04_SH050.json").exists():  # pragma: no cover
    pytest.skip("resolved shots absent", allow_module_level=True)


def shot(sid):
    return json.loads((RES / f"{sid}.json").read_text(encoding="utf-8"))


def fs(sid, f):
    s = shot(sid)
    return A.frame_state(s, s["motion"], s["ui_timeline"], f)


def test_out_of_range_frame_raises():
    s = shot("SC02_SH010")
    with pytest.raises(ValueError):
        A.frame_state(s, s["motion"], s["ui_timeline"], s["frames"]["count"])
    with pytest.raises(ValueError):
        A.frame_state(s, s["motion"], s["ui_timeline"], -1)


def test_deterministic():
    a, b = fs("SC02_SH010", 9), fs("SC02_SH010", 9)
    assert a["characters"]["ren"]["joints"].keys() == b["characters"]["ren"]["joints"].keys()
    assert repr(a) == repr(b)


def test_pose_blend_endpoints_and_ease():
    # SC02_SH010: hold scramble_out at f0, blend into run_phone_out over 6 frames from f6 (ease_out)
    assert fs("SC02_SH010", 0)["characters"]["ren"]["pose"] == {"from": "scramble_out", "to": "scramble_out", "t": 1.0}
    p6 = fs("SC02_SH010", 6)["characters"]["ren"]["pose"]
    p9 = fs("SC02_SH010", 9)["characters"]["ren"]["pose"]
    p12 = fs("SC02_SH010", 12)["characters"]["ren"]["pose"]
    assert (p6["from"], p6["to"], p6["t"]) == ("scramble_out", "run_phone_out", 0.0)
    assert p6["t"] < p9["t"] < 1.0
    assert p9["t"] > 0.5  # ease_out is ahead of linear at the midpoint
    assert p12["t"] == 1.0 and p12["from"] == "run_phone_out"


def test_gait_moves_root_and_limbs():
    r0 = fs("SC02_SH010", 12)["characters"]["ren"]
    r1 = fs("SC02_SH010", 15)["characters"]["ren"]
    assert r0["gait"] == "scramble"
    assert (r0["frame"][0] - r1["frame"][0]).length > 0.05  # the path advances
    j0, j1 = r0["joints"], r1["joints"]
    assert any((j0[k] - j1[k]).length > 1e-4 for k in j0 if k in j1 and hasattr(j0[k], "length"))


def test_door_angle_at_key_frames():
    ang = [fs("SC02_SH010", f)["props"]["passenger_door"]["angle_deg"] for f in range(8)]
    assert ang[0] == 20.0
    assert ang[4] == 63.0  # swing overshoot peak
    assert ang[5] == pytest.approx(61.5) and ang[6] == 60.0 and ang[7] == 60.0
    assert 20.0 < ang[1] < ang[2] < ang[3] < 63.0  # monotone swing toward the peak


def test_crank_pip_lit_windows():
    pip = {f: fs("SC04_SH050", f)["props"]["crank_charger"]["pip"] for f in (0, 29, 30, 34, 37, 38, 39)}
    assert pip[0] == 0.0 and pip[29] == 0.0
    assert pip[30] == pytest.approx(1 / 81)  # ease_in over 9 frames: first frame t=1/9, squared
    assert 0.0 < pip[30] < pip[34] < pip[37] < 1.0
    assert pip[38] == 1.0 and pip[39] == 1.0
    assert fs("SC04_SH050", 12)["props"]["crank_charger"]["loc_t"] == pytest.approx(0.2593, abs=1e-3)  # default ease (smoothstep) of 1/3, 3-frame change from f12
    assert fs("SC04_SH050", 14)["props"]["crank_charger"]["loc"] == "lap"


def test_ui_state_at_frame_boundaries():
    s = shot("SC04_SH020")
    for f in (13, 14, 15):
        ui = fs("SC04_SH020", f)["ui"]
        row = s["ui_timeline"]["frames"][f]
        assert ui["frame"] == f and ui["brightness"] == row["brightness"] and ui["pct"] == row["pct"]
    assert fs("SC04_SH020", 13)["ui"]["brightness"] == 1.0
    assert fs("SC04_SH020", 14)["ui"]["brightness"] == 0.7  # the key press dips the brightness at f14
    assert fs("SC04_SH020", 14)["ui"]["screen"] == "compose"


def test_prop_continuity_across_consecutive_shots():
    prev, nxt = shot("SC04_SH040"), shot("SC04_SH050")
    end, start = A.end_state(prev), A.start_state(nxt)
    for prop in ("glovebox_lid", "crank_charger", "phone_ren"):
        assert end[prop] == start[prop], prop
    # door: SC04_SH050 does not animate it; the carried motion reproduces the previous end state at frame 0
    m = A.with_carried_props(nxt, [prev])
    assert m["props"]["passenger_door"][0]["state"] == "open_60"
    st = A.frame_state(nxt, m, nxt["ui_timeline"], 0)
    assert st["props"]["passenger_door"]["angle_deg"] == 60.0
    a, b = shot("SC02_SH010"), shot("SC02_SH020")
    assert A.end_state(a)["phone_ren"] == A.start_state(b)["phone_ren"]


def test_camera_static_and_dolly():
    for sid in ("SC04_SH050", "SC02_SH010"):
        s = shot(sid)
        for f in (0, s["frames"]["count"] - 1):
            c = fs(sid, f)["camera"]
            assert 0.0 <= c["progress"] <= 1.0
    dolly = [sid for sid in ("SC01_SH010", "SC01_SH020", "SC01_SH030", "SC04_SH060", "SC05_SH020")
             if (shot(sid).get("motion") or {}).get("camera", {}).get("move") == "dolly_in"]
    for sid in dolly:
        n = shot(sid)["frames"]["count"]
        assert fs(sid, 0)["camera"]["progress"] == 0.0 and fs(sid, n - 1)["camera"]["progress"] == 1.0


def test_parse_frames_and_select():
    assert FS.parse_frames("12,f24,30-32,last", 60) == [12, 24, 30, 31, 32, 59]
    assert FS.parse_frames("all", 4) == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        FS.parse_frames("99", 10)
    s = shot("SC04_SH050")
    assert FS.select_frames(s, frames=None, every_key=False, preview_frame=False) == [s["frames"]["count"] // 2]
    pf = FS.select_frames(s, frames=None, every_key=False, preview_frame=True)
    assert pf == [s["animation"]["preview_frame"]]


def test_still_frame_is_a_representative_key_frame_not_frame_zero():
    # designated preview_frame wins (SH060: a still insert, f12)
    assert FS.still_frame(shot("SC03_SH060")) == (12, "animation.preview_frame")
    # no preview_frame: the first state event after f0 is the hero beat (SH020: bolt_on f14, not the rest pose at f0)
    s = shot("SC03_SH020")
    assert not (s.get("animation") or {}).get("preview_frame")
    assert FS.still_frame(s) == (14, "hero_event:bolt_on")
    # nothing usable: mid-shot; deterministic; out-of-range preview_frame ignored
    bare = {"frames": {"count": 30}, "animation": {"preview_frame": 99}, "motion": {"events": [{"f": 0, "id": "x", "kind": "state"}]}}
    assert FS.still_frame(bare) == (15, "mid_shot") == FS.still_frame(bare)
    # every shot of the film gets a frame inside the shot and never the default of 0 unless it is the only frame
    for f in sorted(RES.glob("SC*.json")):
        sh = json.loads(f.read_text(encoding="utf-8"))
        fr, src = FS.still_frame(sh)
        assert 0 <= fr < sh["frames"]["count"] and src
        assert FS.select_frames(sh, preview_frame=True) == [fr]


def test_preview_main_renders_animated_shots_through_the_playblast_path():
    src = (ROOT / "blender" / "fm_blender" / "preview.py").read_text(encoding="utf-8")
    assert "ANIM.render_frames(" in src and "FS.still_frame(" in src and "FM_PICK" in src


# ------------------------------------------------------------------ vocabulary v2 builder pieces
def _motion_with(sid, chars=None, props=None):
    s = shot(sid)
    m = json.loads(json.dumps(s["motion"]))
    for cid, tr in (chars or {}).items():
        m["characters"].setdefault(cid, {}).update(tr)
    m.setdefault("props", {}).update(props or {})
    return s, m


def test_lids_track_blink_keeps_the_gaze():
    blink = [{"f": 0, "ref": "open", "ease": "hold"}, {"f": 4, "ref": "closed", "ease": "ease_in", "dur_f": 4},
             {"f": 10, "ref": "open", "ease": "ease_out", "dur_f": 6}]
    vals = [A.lids_at(blink, f) for f in range(18)]
    assert vals[0] == 1.0 and vals[3] == 1.0
    assert vals[7] == 0.0 and vals[8] == 0.0 and vals[9] == 0.0           # shut for the frames between the keys
    assert vals[4] > vals[5] > vals[6] > vals[7]                          # closes over dur_f frames
    assert vals[10] < vals[11] < vals[14] and vals[15] == 1.0             # opens over its dur_f
    assert A.lids_at([{"f": 2, "ref": "low"}], 0) == 1.0                  # open before the first key
    assert A.lids_at([{"f": 2, "ref": "low"}], 3) == 0.55
    assert A.lids_at([{"f": 2, "ref": "bogus"}], 3) == 1.0 and A.lids_at(None, 3) == 1.0
    # the head aim does not change while the lids move: only `lids` differs between the frames
    s, m = _motion_with("SC04_SH050", {"ren": {"lids": blink}})
    a = A.frame_state(s, m, s["ui_timeline"], 2)["characters"]["ren"]
    b = A.frame_state(s, m, s["ui_timeline"], 8)["characters"]["ren"]
    assert a["lids"] == 1.0 and b["lids"] == 0.0 and a["eyes_closed"] is False and b["eyes_closed"] is False
    assert b["joints"]["head_yaw"] == a["joints"]["head_yaw"] and b["look"] == a["look"]


def test_shop_door_swing_back_decays_past_the_cut():
    keys = [{"f": 0, "state": "open_70", "ease": "hold"}, {"f": 14, "state": "swing_back", "ease": "ease_in"}]
    ang = [A.shop_door_angle(keys, f) for f in range(0, 90)]
    assert ang[13] == 70.0 and ang[14] == 70.0                            # starts from where it was
    assert 69.0 < ang[15] <= 70.0                                         # the shot's last frame: barely started, no slam
    assert all(ang[i] >= ang[i + 1] for i in range(14, 89))               # monotone decay
    assert ang[14 + 36] == pytest.approx(0.0, abs=1e-9) and ang[89] == 0.0   # about 36 frames to shut
    assert max(ang[i] - ang[i + 1] for i in range(14, 89)) < 4.0          # never a slam
    # a pinned partial angle: the decay starts from it
    k2 = [{"f": 0, "state": "open_70"}, {"f": 4, "state": "swing_back", "swing_deg": 30}]
    a2 = [A.shop_door_angle(k2, f) for f in range(0, 30)]
    assert a2[3] == 70.0 and a2[4] == 30.0 and a2[5] < 30.0 and a2[29] == 0.0
    # plain states keep their meaning (and swing_deg alone pins an angle)
    assert A.shop_door_angle([{"f": 0, "state": "closed"}, {"f": 2, "state": "open_70", "dur_f": 4}], 5) == 70.0
    assert A.shop_door_angle([{"f": 0, "swing_deg": 25}], 3) == 25.0
    s, m = _motion_with("SC02_SH030", props={"shop_door": keys})
    st = A.frame_state(s, m, s["ui_timeline"], 15)["props"]["shop_door"]
    assert st["state"] == "swing_back" and 69.0 < st["angle_deg"] <= 70.0


def test_cable_loc_chains_and_hidden_state():
    ks = [{"f": 0, "loc": "glovebox", "state": "hidden"}, {"f": 23, "state": "posed"}, {"f": 30, "loc": "hand_r"}]
    assert A.cable_at(ks, 5) == ("glovebox", "hidden")
    assert A.cable_at(ks, 23) == ("glovebox", "posed")
    assert A.cable_at(ks, 31) == ("hand_r", "posed")
    assert A.cable_at([{"f": 4, "loc": "loose"}], 1) == ("glovebox", "hidden")          # before the first key
    assert A.cable_at([{"f": 0, "loc": "loose", "state": "hidden"}], 9) == ("loose", "hidden")
    assert A.cable_at([{"f": 0, "loc": "elsewhere"}], 3) == ("glovebox", "posed")       # unknown values are ignored
    s, m = _motion_with("SC04_SH050", props={"charging_cable": [{"f": 0, "loc": "hand_r", "state": "posed"},
                                                                 {"f": 10, "loc": "crank_port"}]})
    a = A.frame_state(s, m, s["ui_timeline"], 5)["props"]["charging_cable"]
    b = A.frame_state(s, m, s["ui_timeline"], 12)["props"]["charging_cable"]
    assert (a["loc"], a["hide_render"]) == ("hand_r", False) and b["loc"] == "crank_port"
    assert a["src"] is not None and a["phone_end"] is not None and b["src"] is not None
    hid = A.frame_state(*(lambda s_, m_: (s_, m_, s_["ui_timeline"], 5))(*_motion_with(
        "SC04_SH050", props={"charging_cable": [{"f": 0, "loc": "loose", "state": "hidden"}]})))["props"]["charging_cable"]
    assert hid["hide_render"] is True and hid["src"] is None and hid["loc"] == "loose"   # hidden: nothing to render, loc kept


def test_cable_carries_between_shots():
    s1, m1 = _motion_with("SC04_SH050", props={"charging_cable": [{"f": 0, "loc": "shop_socket", "state": "posed"}]})
    s1 = dict(s1, motion=m1)
    s2 = shot("SC04_SH060")
    carried = A.with_carried_props(s2, [s1])["props"]["charging_cable"]
    assert carried == [{"loc": "shop_socket", "state": "posed", "f": 0}]
    s1h = dict(s1, motion=_motion_with("SC04_SH050", props={"charging_cable": [{"f": 0, "loc": "loose", "state": "hidden"}]})[1])
    assert A.with_carried_props(s2, [s1h])["props"]["charging_cable"] == [{"loc": "loose", "state": "hidden", "f": 0}]


def test_cable_curve_ends_on_the_two_plugs_and_stays_above_ground():
    from fm_blender import poses as PS
    from mathutils import Vector
    a, b = Vector((0.0, 0.0, 0.4)), Vector((0.5, 0.2, 0.9))
    pts = PS.cable_points(a, b, ground_z=0.0)
    assert (pts[0] - a).length < 1e-9 and (pts[-1] - b).length < 1e-9 and len(pts) == 17
    assert min(p.z for p in pts) < min(a.z, b.z)                       # it hangs below the chord
    low = PS.cable_points(Vector((0, 0, 0.02)), Vector((0.6, 0, 0.05)), ground_z=0.0)
    assert min(p.z for p in low[1:-1]) >= 0.004                         # a loose cable lies on the ground, not in it
    assert [tuple(p) for p in pts] == [tuple(p) for p in PS.cable_points(a, b, ground_z=0.0)]


def test_clamped_crank_left_hand_follows_the_charger_loc():
    s = shot("SC04_SH050")
    st = A.frame_state(s, s["motion"], s["ui_timeline"], 30)
    j = st["characters"]["ren"]["joints"]
    assert st["props"]["crank_charger"]["loc"] == "lap"
    assert j["phone_hand"] == "L" and j["phone"].z > 0.7               # the phone is held over the knee, above the crank
    s, m = _motion_with("SC04_SH050", props={"crank_charger": [{"f": 0, "loc": "hands_both", "arm": "unfolded"}]})
    jb = A.frame_state(s, m, s["ui_timeline"], 30)["characters"]["ren"]["joints"]
    assert jb["handL"].z < j["handL"].z - 0.05                          # under the crank body


def _film_canon():
    return json.loads((RES / "film.json").read_text(encoding="utf-8"))["canon"]


def test_shop_kneel_ctx_uses_the_sets_real_stand_and_socket():
    from fm_blender.anchors import shop_anchors
    canon = _film_canon()
    if "world.sets.corner_shop" not in canon:  # pragma: no cover
        pytest.skip("shop canon absent")
    s = shot("SC03_SH020")
    st = A.Stage(s, canon, motion=s["motion"])
    base, fac = st.home["ren"]
    anc = shop_anchors(canon["world.sets.corner_shop"], A.SHOP_ORIGIN)
    sh = st.ctx["shop"]
    assert (A.PS.to_world(A.Vector(sh["socket"]), base, fac) - anc["socket"]).length < 1e-4
    assert (A.PS.to_world(A.Vector(sh["stand_back_edge"]), base, fac) - anc["stand_back_edge"]).length < 1e-4
    # the stand really is where the set builds it (0.8 m to Ren's right at the shot's spot), not the 0.62 m default
    assert sh["stand_back_edge"] != A.PS.CTX_DEFAULT["shop"]["stand_back_edge"]
    assert abs(sh["stand_back_edge"][1] - 0.8) < 0.02
    # the default stage (no canon) and other scenes keep the poses' own defaults
    assert A.Stage(s, None, motion=s["motion"]).ctx["shop"] == A.PS.CTX_DEFAULT["shop"]
    s4 = shot("SC04_SH050")
    assert A.Stage(s4, canon, motion=s4["motion"]).ctx["shop"] == A.PS.CTX_DEFAULT["shop"]


def test_kneel_reach_follows_the_real_socket_when_ren_kneels_beside_the_stand():
    import copy
    canon = _film_canon()
    s = copy.deepcopy(shot("SC03_SH020"))
    s["characters"][0]["position"] = [3.45, 8.66, 0.0]          # kneeling left of the stand, as the preset assumes (the shot's own spot)
    st = A.Stage(s, canon, motion=s["motion"])
    j = A.PS.pose("ren", "kneel_reach_stand", st.props["ren"], st.ctx)
    base, fac = st.home["ren"]
    hand = A.PS.to_world(j["handR"], base, fac)
    from fm_blender.anchors import shop_anchors
    assert (hand - shop_anchors(canon["world.sets.corner_shop"], A.SHOP_ORIGIN)["socket"]).length <= 0.02
    # at the shot's own position the real socket is out of reach: reported, not hidden by a default
    s0 = copy.deepcopy(shot("SC03_SH020"))
    s0["characters"][0]["position"] = [1.2, 5.0, 0.0]            # across the shop: the socket is out of reach
    st0 = A.Stage(s0, canon, motion=s0["motion"])
    far = A.PS.pose("ren", "kneel_reach_stand", st0.props["ren"], st0.ctx)
    assert far["reach_err"][1] > 0.5
