"""Vocabulary v2, Blender builder side: car interior vs pose reach, phone ui events (photo_scale, pulse, key_press).
Pure python (bpy/mathutils only as a library); needs the resolved shots of projects/last_signal/09_resolved."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
RES = ROOT / "projects" / "last_signal" / "09_resolved"

try:
    from fm_blender import animate as A  # noqa: E402
    from fm_blender import phone as PH  # noqa: E402
    from fm_blender import poses as PS  # noqa: E402
    from fm_blender import anchors as AN  # noqa: E402
    from mathutils import Vector  # noqa: E402
    import bpy  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

if not (RES / "SC04_SH030.json").exists():  # pragma: no cover
    pytest.skip("resolved shots absent", allow_module_level=True)


def shot(sid):
    return json.loads((RES / f"{sid}.json").read_text(encoding="utf-8"))


def canon():
    return json.loads((RES / "film.json").read_text(encoding="utf-8"))["canon"]


def test_car_layout_defaults_to_v2():
    assert AN.CAR_V2[0] is True and AN.car_layout() == (AN.CAR_SEAT_SHIFT_V2, -AN.CAR_GLOVEBOX_BACK_V2)
    assert AN.car_layout(False) == (0.0, 0.0)
    assert AN.car_layout(True) == (AN.CAR_SEAT_SHIFT_V2, -AN.CAR_GLOVEBOX_BACK_V2)


@pytest.mark.parametrize("sid", ["SC04_SH030", "SC01_SH120", "SC04_SH040"])
def test_car_interior_matches_the_poses_reach(sid):
    s = shot(sid)
    st = A.Stage(s, canon(), motion=s["motion"])
    cc = st.ctx["car"]
    assert cc["wheel_center"][0] == pytest.approx(0.40, abs=0.01)                      # wheel 0.40 m ahead of the pelvis
    la = Vector(cc["glovebox_latch"])
    assert Vector((la.x, la.y, 0)).length == pytest.approx(0.75, abs=0.02)              # canon reach_from_driver_seat_m
    props = st.props["ren"]
    for ref in ("car_upright", "car_reach_up", "car_phone_up", "car_lean_glovebox", "car_sag", "car_recline", "car_forehead_wheel"):
        j = PS.pose("ren", ref, props, st.ctx)
        assert PS.check_lengths(j, props) == [], ref
        assert max(j["reach_err"]) <= 0.01, (ref, j["reach_err"])                      # hands really reach their targets
        assert PS.crown_z(j) < 1.40, ref


def test_ui_to_st_carries_photo_scale_pulse_and_key_press():
    base = {"f": 3, "ui": "call", "phone": "ren", "pct": 3}
    st = A.ui_to_st(dict(base, photo_scale_pct=97.5, pulse=0.25, call_state="idle"))
    assert st["photo_scale_pct"] == 97.5 and st["pulse"] == 0.25
    assert "photo_scale_pct" not in A.ui_to_st(base) and "pulse" not in A.ui_to_st(base)
    c = A.ui_to_st({"f": 0, "ui": "compose", "lines": 1, "pct": 3, "phone": "ren", "key_pressed": "emoji"})
    assert c["key_pressed"] == "emoji" and c["send_pressed"] is False
    s = A.ui_to_st({"f": 0, "ui": "compose", "lines": 1, "pct": 3, "phone": "ren", "key_pressed": "send"})
    assert s["send_pressed"] is True and "key_pressed" not in s


@pytest.fixture
def recorded(monkeypatch):
    """Run Screen drawing methods with the geometry calls recorded instead of building meshes."""
    calls = []
    colors = {k: v for k, v in vars(PH).items() if k.isupper() and isinstance(v, dict) and "keyboard_key_pressed" in v}
    c = next(iter(colors.values()))
    sc = PH.Screen.__new__(PH.Screen)
    sc.c, sc.sw, sc.sh, sc.mm = c, 0.062, 0.135, 0.001
    for name in ("rect", "poly", "disc", "ring", "line", "ellipse", "strip", "frect"):
        monkeypatch.setattr(sc, name, lambda *a, _n=name, **k: calls.append((_n, a, k)), raising=False)
    return sc, calls, c


def test_keyboard_pressed_key_uses_the_pressed_colour(recorded):
    sc, calls, c = recorded
    sc.keyboard(None)
    n_plain = sum(1 for n, a, k in calls if n == "rect" and c["keyboard_key_pressed"] in a)
    assert n_plain == 0
    for key in ("any", "emoji", "backspace"):
        calls.clear()
        sc.keyboard(key)
        assert sum(1 for n, a, k in calls if n == "rect" and c["keyboard_key_pressed"] in a) == 1, key


def test_call_pulse_scales_the_button(recorded):
    sc, calls, c = recorded
    discs = lambda: [a for n, a, k in calls if n == "disc" and a[3] == c["call_green"]]  # noqa: E731
    sc.call_screen({}, "hana")
    r_idle = discs()[-1][2]
    calls.clear()
    sc.call_screen({"pulse": 0.5}, "hana")
    assert discs()[-1][2] > r_idle * 1.1                      # the beat peaks at phase 0.5 (+12 %)
    calls.clear()
    sc.call_screen({"pulse": 0.0}, "hana")
    assert discs()[-1][2] == pytest.approx(r_idle)


def test_photo_scale_scales_the_portrait(recorded):
    sc, calls, c = recorded
    sc.call_screen({}, "hana")
    big = max(a[2] for n, a, k in calls if n == "disc" and a[3] == c["photo_frame_ring"])
    calls.clear()
    sc.call_screen({"photo_scale_pct": 90.0}, "hana")
    small = max(a[2] for n, a, k in calls if n == "disc" and a[3] == c["photo_frame_ring"])
    assert small == pytest.approx(big * 0.9, rel=1e-6)


def test_insert_hides_every_head_piece():
    """Inserts hide the figure pieces the lens sits in; the prefix list must cover every head piece characters.figure builds
    (a missed fringe/brow/mouth rendered flat brown in SC01_SH070/080/120/140)."""
    import re
    src = (ROOT / "blender" / "fm_blender" / "characters.py").read_text(encoding="utf-8")
    names = set(re.findall(r'\{cid\}_([a-z]+)', src))
    keep = {"shoe", "centrestrip", "pocket", "collar"}       # body wardrobe pieces an insert leaves visible
    for n in sorted(names - keep):
        assert n.startswith(A.INSERT_HIDE_PREFIXES), f"insert would leave {n!r} visible"
    for n in ("fringe", "brow", "mouth", "hair", "bob", "bobback", "tuft", "tufttip", "ear"):
        assert n.startswith(A.INSERT_HIDE_PREFIXES)


def test_insert_shift_has_a_call_screen_case_and_one_rule_everywhere():
    xv, yv = Vector((1, 0, 0)), Vector((0, 0, 1))
    assert AN.insert_shift(["ui.call_screen"], 0.30, xv, yv).length == pytest.approx(0.03)     # SC01_SH030: toward the top edge
    assert AN.insert_shift(["ui.call_screen"], 0.67, xv, yv).length == 0.0                     # SH020/050 (0.67 m): no shift
    assert AN.insert_shift(["ui.status_bar"], 0.30, xv, yv).length > 0.05
    assert A._insert_shift is AN.insert_shift


def _wheel():
    import bpy
    from fm_blender import sets as SE
    col = bpy.data.collections.new("wheel_test")
    w = SE.steering_wheel("steering_wheel_test", (0, 0, 0), col, None)
    return w, SE


def test_steering_wheel_is_a_ring_with_spokes_not_a_disk():
    w, SE = _wheel()
    w.rotation_euler = (0, 0, 0)                      # test in the wheel plane: axis Z, +Y top
    me = w.data
    R = SE.WHEEL_RADIUS_M

    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])

    def hit(x, y):
        return tree.ray_cast(Vector((x, y, 1.0)), Vector((0, 0, -1)))[0] is not None
    assert hit(R, 0.0) and hit(0.0, R) and hit(-R, 0.0) and hit(0.0, -R)                 # the rim is there all round
    assert hit(0.0, 0.0)                                                                  # the hub
    r45 = R * 0.6
    assert not hit(r45 * math.cos(math.radians(45)), r45 * math.sin(math.radians(45)))   # open between the spokes (upper right)
    assert not hit(-r45 * math.cos(math.radians(45)), r45 * math.sin(math.radians(45)))  # upper left
    assert not hit(0.0, R * 0.6)                                                          # no spoke at the top: rim top and thumbs clear
    assert hit(R * 0.6, 0.0) and hit(-R * 0.6, 0.0) and hit(0.0, -R * 0.6)                # side and bottom spokes
    rmax = max(math.hypot(v.co.x, v.co.y) for v in me.vertices)
    assert rmax == pytest.approx(R + SE.WHEEL_TUBE_M, abs=1e-3)                          # rim centre line = the poses' wheel_radius


def test_steering_wheel_rake_matches_the_poses_wheel_plane():
    w, SE = _wheel()
    up = w.rotation_euler.to_matrix() @ Vector((0, 1, 0))
    assert (up - Vector((0, *PS.CTX_DEFAULT["car"]["wheel_up"][:1], PS.CTX_DEFAULT["car"]["wheel_up"][2]))).length < 1e-3
    assert SE.WHEEL_RADIUS_M == PS.CTX_DEFAULT["car"]["wheel_radius"]
