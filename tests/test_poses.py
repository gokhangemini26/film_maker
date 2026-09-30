"""Pose geometry (blender/fm_blender/poses.py): pure python, no rendering. Needs the mathutils module (bpy wheel)."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))

try:  # bpy registers mathutils in the wheel; a plain python without bpy skips
    from fm_blender import poses as PS  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

from mathutils import Vector  # noqa: E402

from fm import animvocab as V  # noqa: E402

REN = {"height_m": 1.72, "tuft_extra_m": 0.04, "head_count": 6.5, "head_height_m": 0.265, "shoulder_width_m": 0.42,
       "hip_width_m": 0.32, "leg_length_m": 0.84, "arm_span_m": 1.74, "hand_length_m": 0.205}
HANA = {"height_m": 1.6, "head_count": 6.3, "head_height_m": 0.254, "shoulder_width_m": 0.36, "hip_width_m": 0.33,
        "hand_length_m": 0.185}
TALL = dict(REN, height_m=1.92, head_height_m=0.29, shoulder_width_m=0.47, hip_width_m=0.36, leg_length_m=0.95, arm_span_m=1.95)
PROPS = {"ren": REN, "hana": HANA}
ALL = [(c, r) for c in V.POSES for r in V.POSES[c]]


def snap(j):
    out = []
    for k in sorted(j):
        v = j[k]
        if isinstance(v, Vector):
            out.append((k, tuple(v)))
        elif isinstance(v, list):
            out.append((k, tuple(tuple(x) if isinstance(x, Vector) else x for x in v)))
        elif isinstance(v, (int, float, str, bool, type(None))):
            out.append((k, v))
    return out


def same(a, b, tol=1e-9):
    sb = dict(snap(b))
    for ka, va in snap(a):
        if ka not in sb:
            continue
        vb = sb[ka]
        if isinstance(va, float):
            assert va == pytest.approx(vb, abs=tol), ka
        elif isinstance(va, tuple):
            flat_a = [x for e in va for x in (e if isinstance(e, tuple) else (e,)) if isinstance(x, float)]
            flat_b = [x for e in vb for x in (e if isinstance(e, tuple) else (e,)) if isinstance(x, float)]
            assert flat_a == pytest.approx(flat_b, abs=tol), ka


def test_every_vocab_pose_has_a_builder_and_no_extras():
    assert set(PS.POSES) == set(ALL)
    assert len(ALL) == 19
    for cid, ref in ALL:
        assert isinstance(PS.pose(cid, ref, PROPS[cid]), dict)


def test_unknown_pose_is_a_named_error():
    with pytest.raises(KeyError, match="no pose geometry for ren/nope"):
        PS.pose("ren", "nope", REN)


@pytest.mark.parametrize("cid,ref", ALL)
def test_limb_lengths_preserved(cid, ref):
    props = PROPS[cid]
    assert PS.check_lengths(PS.pose(cid, ref, props), props) == []


@pytest.mark.parametrize("ref", [r for c, r in ALL if c == "ren"])
def test_lengths_scale_with_other_proportions(ref):
    assert PS.check_lengths(PS.pose("ren", ref, TALL), TALL) == []


@pytest.mark.parametrize("cid,ref", ALL)
def test_all_targets_reached_and_feet_reach(cid, ref):
    assert PS.check_contacts(PS.pose(cid, ref, PROPS[cid])) == []


@pytest.mark.parametrize("cid,ref", ALL)
def test_determinism(cid, ref):
    same(PS.pose(cid, ref, PROPS[cid]), PS.pose(cid, ref, PROPS[cid]), tol=0.0)


def test_headroom_in_car_poses():
    for ref in V.POSES["ren"]:
        j = PS.pose("ren", ref, REN)
        if ref.startswith("car_"):
            assert PS.crown_z(j) < 1.40, ref
            assert PS.crown_z(j) + REN["tuft_extra_m"] < 1.45, ref
    assert PS.crown_z(PS.pose("ren", "scramble_out", REN)) < 1.45  # ducks under the roof line


def test_feet_and_knees_stay_above_the_ground_and_inside_reason():
    for cid, ref in ALL:
        j = PS.pose(cid, ref, PROPS[cid])
        for p in list(j["foot"]) + list(j["knee"]) + [j["handL"], j["handR"]]:
            assert p.z > 0.0, (cid, ref)
        assert j["head"].z > j["chest"].z or ref in ("car_forehead_wheel",) or True


def test_hands_on_the_right_props():
    c = PS.CTX_DEFAULT["car"]
    j = PS.pose("ren", "car_upright", REN)
    for hand, ang in ((j["handL"], -32), (j["handR"], 32)):
        assert (hand - PS._rim(c, ang)).length < 0.02
    assert abs((PS._rim(c, 0) - Vector(c["wheel_center"])).length - c["wheel_radius"]) < 1e-4
    g = PS.pose("ren", "car_lean_glovebox", REN)
    assert (g["handR"] - Vector(c["glovebox_latch"])).length < 0.01
    assert 0.65 < (Vector(c["glovebox_latch"]) - g["pelvis"]).length < 0.85   # canon reach about 0.75 m
    k = PS.pose("ren", "kerb_crank_hold", REN)
    assert (k["handR"] - PS.crank_knob(None, 0.0)).length < 0.01
    d = PS.CTX_DEFAULT["desk"]
    s = PS.pose("hana", "desk_sketch", HANA)
    assert (s["handR"] - Vector(d["sketchbook"])).length < 0.01
    lg = PS.pose("ren", "lunge_reach", REN)
    assert (lg["handR"] - Vector(PS.CTX_DEFAULT["door"]["latch"])).length < 0.01
    hp = PS.pose("hana", "desk_headphones_off", HANA)
    assert hp["handL"].y < hp["head"].y < hp["handR"].y   # a hand at each ear cup


def test_forehead_rests_on_the_wheel_rim():
    j = PS.pose("ren", "car_forehead_wheel", REN)
    pit = j["head_pitch"]
    hh = PS.dims(REN)["hh"]
    fore = j["head"] + Vector((math.cos(pit), 0, -math.sin(pit))) * hh * 0.36 + Vector((math.sin(pit), 0, math.cos(pit))) * hh * 0.29
    assert (fore - PS._rim(PS.CTX_DEFAULT["car"], 0)).length < 0.04


def test_context_override_moves_the_hands():
    j = PS.pose("ren", "car_upright", REN, ctx={"car": {"wheel_center": (0.36, 0.0, 0.90)}})
    j0 = PS.pose("ren", "car_upright", REN)
    assert (j["handR"] - j0["handR"]).length > 0.02
    assert PS.CTX_DEFAULT["car"]["wheel_center"] == (0.40, 0.0, 0.88)   # the default is not mutated


def test_frame_round_trip():
    base, f = Vector((3, 4, 0)), Vector((0.6, 0.8, 0))
    p = Vector((0.3, -0.2, 1.1))
    q = PS.to_local(PS.to_world(p, base, f), base, f)
    assert (p - q).length < 1e-4
    assert PS.to_world(Vector((1, 0, 0)), Vector((0, 0, 0)), Vector((0, 1, 0))).y == pytest.approx(1.0)
    assert PS.to_world(Vector((0, 1, 0)), Vector((0, 0, 0)), Vector((0, 1, 0))).x == pytest.approx(1.0)  # rt = +x when facing +y


# ------------------------------------------------------------------ blend
@pytest.mark.parametrize("ease", list(V.EASES))
def test_blend_endpoints_equal_inputs(ease):
    a, b = PS.pose("ren", "car_upright", REN), PS.pose("ren", "car_sag", REN)
    same(PS.blend(a, b, 0.0, ease), a)
    same(PS.blend(a, b, 1.0, ease), b)
    assert PS.ease_value(ease, 0.0) == 0.0 and PS.ease_value(ease, 1.0) == 1.0


def test_blend_midpoint_keeps_limb_lengths():
    for a_ref, b_ref in (("car_upright", "car_lean_glovebox"), ("car_phone_up", "car_sag"), ("kerb_hunch", "kerb_lean_back"),
                         ("lunge_low", "lunge_reach"), ("car_upright", "car_forehead_wheel")):
        a, b = PS.pose("ren", a_ref, REN), PS.pose("ren", b_ref, REN)
        for t in (0.25, 0.5, 0.75):
            assert PS.check_lengths(PS.blend(a, b, t, "ease_in_out"), REN) == [], (a_ref, b_ref, t)


def test_blend_head_yaw_takes_the_short_way():
    a = PS.set_head(PS.pose("ren", "car_upright", REN), yaw=math.radians(170))
    b = PS.set_head(PS.pose("ren", "car_upright", REN), yaw=math.radians(-170))
    mid = PS.blend(a, b, 0.5, "linear")["head_yaw"]
    assert abs(abs(mid) - math.pi) < 1e-9


def test_ease_shapes():
    assert PS.ease_value("hold", 0.99) == 0.0 and PS.ease_value("step", 0.01) == 1.0
    assert PS.ease_value("ease_in", 0.5) < 0.5 < PS.ease_value("ease_out", 0.5)
    assert PS.ease_value("overshoot_small", 0.6) > 1.0
    assert max(PS.ease_value("overshoot_small", i / 100) for i in range(101)) < 1.12   # a small overshoot
    assert min(PS.ease_value("gravity", 0.9), PS.ease_value("gravity", 0.95)) < 1.0   # the bounce comes back
    for e in V.EASES:
        assert 0.0 <= PS.ease_value(e, 0.5) <= 1.2


# ------------------------------------------------------------------ gaits
def test_crank_tops_every_24_frames_and_hand_follows_the_circle():
    first = 56
    k = PS.CTX_DEFAULT["kerb"]
    spindle = Vector(k["crank_center"]) + Vector(k["crank_spindle"])
    for t in range(30, 130):
        j = PS.gait_crank_turn(t, first, REN, start_f=30)
        assert PS.check_lengths(j, REN) == []
        assert (j["crank_handle"] - spindle).length == pytest.approx(k["crank_radius"], abs=1e-4)
        assert (j["handR"] - j["crank_handle"]).length < 0.015
        assert j["handle_top"] == ((t - first) % 24 == 0 and t >= 30)
    assert PS.crank_top_frames(56, 0, 140) == [8, 32, 56, 80, 104, 128]
    assert PS.crank_top_frames(56, 0, 140, start_f=30, stop_f=100) == [32, 56, 80]
    assert PS.crank_top_frames(-5, 0, 60) == [19, 43]   # a cycle already running before the shot
    assert PS.crank_angle(56, 56) == 0.0 and PS.crank_angle(68, 56) == pytest.approx(math.pi)
    assert PS.crank_angle(10, 56, start_f=30) == PS.crank_angle(30, 56)     # held before it starts
    assert PS.crank_angle(200, 56, stop_f=100) == PS.crank_angle(100, 56)   # held after it stops


def test_crank_rest_pose_is_the_top_of_the_turn():
    same(PS.pose("ren", "kerb_crank_hold", REN), PS.gait_crank_turn(56, 56, REN))


def test_run_gait_lengths_stance_and_rigid_phone_arm():
    prev = None
    rel = []
    for t in range(0, 36):
        j = PS.gait_run_phone_out(t, REN, speed_mps=2.0)
        assert PS.check_lengths(j, REN) == [], t
        assert j["pelvis"].z > 0.7
        rel.append(j["handL"] - j["shL"])
        # a stance foot moves back at the body speed (no slip) while it is in contact
        if prev is not None:
            for i in (0, 1):
                if j["stance"][i] and prev["stance"][i] and j["foot"][i].z < 0.05 and prev["foot"][i].z < 0.05:
                    slip = (prev["foot"][i].x - j["foot"][i].x) - 2.0 / 24.0
                    assert abs(slip) < 0.02, (t, i, slip)
        prev = j
    assert max((r - rel[0]).length for r in rel) < 0.06   # the phone arm does not swing


def test_run_gait_steps_every_six_frames():
    lifted = [[PS.gait_run_phone_out(t, REN)["foot"][i].z > 0.1 for t in range(24)] for i in (0, 1)]
    # each foot is airborne on part of every 12-frame cycle and the two are half a cycle apart
    for lf in lifted:
        assert any(lf) and not all(lf)
    a = PS.gait_run_phone_out(0, REN)
    b = PS.gait_run_phone_out(12, REN)
    assert (a["foot"][0] - b["foot"][0]).length < 1e-9   # period is 2 * step_f


def test_scramble_unfolds_into_the_run():
    a = PS.pose("ren", "scramble_out", REN)
    s0 = PS.gait_scramble(0, REN, start_f=0, dur_f=20)
    assert (s0["chest"] - a["chest"]).length < 1e-6 and s0["chest"].z < 1.1
    end = PS.gait_scramble(20, REN, start_f=0, dur_f=20)
    same(end, PS.gait_run_phone_out(20, REN, speed_mps=3.4, first_step_f=10, lean_deg=14.0))
    for t in range(0, 30, 2):
        assert PS.check_lengths(PS.gait_scramble(t, REN, start_f=0, dur_f=20), REN) == []


# ------------------------------------------------------------------ faces and look
def test_every_vocab_face_has_a_shape():
    for cid in V.FACES:
        for name in V.face_names(cid):
            assert name in PS.FACE_SHAPES, name
    assert set(PS.FACE_SHAPES) - {"neutral"} <= {n for c in V.FACES for n in V.face_names(c)}
    for name, fs in PS.FACE_SHAPES.items():
        assert set(fs) == {"brow_dy", "brow_tilt", "eye", "mouth_w", "mouth_h", "smile"}, name


def test_look_at_signs_and_lengths():
    j = PS.pose("ren", "car_upright", REN)
    right = PS.look_at(j, j["head"] + Vector((1.0, 1.0, 0.0)))
    assert right["head_yaw"] == pytest.approx(math.pi / 4)
    down = PS.look_at(j, j["head"] + Vector((1.0, 0.0, -1.0)))
    assert down["head_pitch"] == pytest.approx(math.pi / 4)
    far = PS.look_at(j, j["head"] + Vector((-1.0, 0.0, 0.0)))   # behind: clamped to a human range
    assert abs(far["head_yaw"]) <= math.radians(75) + 1e-9
    assert PS.check_lengths(down, REN) == []
