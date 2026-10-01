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
