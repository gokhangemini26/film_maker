"""Wall rule for the preview builder (blender/fm_blender/sightline.py): pure python, no bpy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))
from fm_blender import sightline as SL  # noqa: E402

# shop back wall (y 8.95-9.05), 4.2 m wide, 2.6 m high; left wall is a slab along x
BACK = ((0.0, 8.95, 0.0), (4.2, 9.05, 2.6))
LEFT = ((-0.05, 0.0, 0.0), (0.05, 9.0, 2.6))
REN = [(3.45, 8.66, 1.2), (3.45, 8.66, 0.8), (3.45, 8.66, 0.5)]  # kneeling, 0.23 m from the wall's inner face


def test_slab_axis_detects_walls_only():
    assert SL.slab_axis(*BACK) == 1
    assert SL.slab_axis(*LEFT) == 0
    assert SL.slab_axis((0, 0, 0), (1.0, 1.0, 0.9)) is None   # a box, not a slab
    assert SL.slab_axis((0, 0, 0), (0.3, 3.0, 2.0)) is None   # too thick (shelf unit)
    assert SL.slab_axis((0, 0, 0), (0.05, 0.6, 2.0)) is None  # thin but narrow (door jamb)


def test_lens_behind_back_wall_hides_it_sh030_sh070():
    for lens in ((3.85, 9.40, 0.85), (3.75, 9.55, 1.05)):
        assert SL.walls_to_hide({"shop_wall_back": BACK, "shop_wall_l": LEFT}, lens, REN) == ["shop_wall_back"]


def test_lens_inside_room_keeps_wall():
    assert SL.walls_to_hide({"shop_wall_back": BACK}, (3.45, 6.0, 1.2), REN) == []   # normal shot, wall behind subject
    assert SL.walls_to_hide({"shop_wall_back": BACK}, (3.45, 8.78, 0.97), REN) == []  # SH060 lens between Ren and wall


def test_subject_on_lens_side_keeps_wall():
    # lens behind the wall, but the subject is also behind it: wall is not between them
    assert SL.walls_to_hide({"shop_wall_back": BACK}, (3.85, 9.4, 0.85), [(3.0, 9.8, 1.0)]) == []


def test_lens_inside_slab_left_to_contain_cull():
    assert SL.walls_to_hide({"shop_wall_back": BACK}, (3.45, 9.0, 1.0), REN) == []


def test_lens_far_beside_wall_does_not_hide_it():
    assert SL.walls_to_hide({"shop_wall_back": BACK}, (9.0, 9.4, 1.0), REN) == []


def test_not_shot_specific_other_wall():
    # outside the west wall looking east at someone inside
    assert SL.walls_to_hide({"shop_wall_l": LEFT}, (-0.6, 4.0, 1.4), [(1.0, 4.0, 1.4)]) == ["shop_wall_l"]


# ---- ray clearance (shared by the static assembly and every animated frame) -------------------------------------
def _slab_cast(slabs):
    """cast(org, u, dist) over axis-aligned boxes {name: (lo, hi)}: first box the ray enters within dist (slab method)."""
    def cast(org, u, dist):
        best = None
        for name, (lo, hi) in slabs.items():
            t0, t1 = 0.0, dist
            for k in range(3):
                if abs(u[k]) < 1e-12:
                    if not lo[k] <= org[k] <= hi[k]:
                        t0, t1 = 1.0, 0.0
                        break
                    continue
                a, b = (lo[k] - org[k]) / u[k], (hi[k] - org[k]) / u[k]
                t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
            if t0 <= t1 and (best is None or t0 < best[0]):
                best = (t0, name)
        return None if best is None else (tuple(org[k] + u[k] * best[0] for k in range(3)), best[1])
    return cast


def test_clear_sight_lines_hides_the_seat_back_in_front_of_the_lens():
    # SC01_SH110: lens 0.34 m from a seat back that filled the whole frame (flat purple-grey in the playblast)
    seat = ((0.80, -0.5, 0.3), (0.84, 0.5, 1.1))
    goals = SL.point_goals((1.28, 0.48, 0.61))
    hidden = []
    got = SL.clear_sight_lines(_slab_cast({"seat_passenger_back": seat}), (0.5, -0.2, 1.0), goals,
                               hideable=lambda h: True, hide=hidden.append)
    assert hidden == got and set(got) == {"seat_passenger_back"}


def test_clear_sight_lines_never_hides_what_is_not_hideable_and_terminates():
    subject = ((1.0, 0.3, 0.5), (1.1, 0.6, 0.8))
    got = SL.clear_sight_lines(_slab_cast({"ren_arm": subject}), (0.5, -0.2, 1.0), [(1.28, 0.48, 0.61)],
                               hideable=lambda h: h != "ren_arm", hide=lambda h: None)
    assert got == []


def test_clear_sight_lines_clear_path_and_min_dist():
    cast = _slab_cast({"wall": ((5, 5, 5), (6, 6, 6))})
    assert SL.clear_sight_lines(cast, (0, 0, 0), SL.point_goals((1, 0, 0)), lambda h: True, lambda h: None) == []
    assert SL.clear_sight_lines(lambda *a: ((0, 0, 0), "x"), (0, 0, 0), [(0.01, 0, 0)], lambda h: True, lambda h: None) == []


def test_goals_and_focus_clamp():
    g = SL.phone_goals((0, 0, 0), (1, 0, 0), (0, 1, 0))
    assert len(g) == 9 and (0.034, 0.072, 0.0) in [tuple(round(c, 3) for c in p) for p in g]
    assert len(SL.point_goals((0, 0, 0))) == 5
    assert SL.focus_clamp(0.083) == 0.083          # a phone 0.083 m away stays in focus (old 0.1 floor put it behind)
    assert SL.focus_clamp(0.0) == SL.CLIP_START + SL.FOCUS_EPS
