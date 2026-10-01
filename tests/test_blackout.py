"""SC03 blackout look (blender/fm_blender/blackout.py, canon look.lighting.sc03_blackout_render): colours are REPLACED, not
scaled; shop emissives become a dark non-emissive material, not hidden; the pool carries the canon phone glow colour.
Needs the bpy module (no rendering) and the resolved shots of projects/last_signal/09_resolved."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
RES = ROOT / "projects" / "last_signal" / "09_resolved"

try:
    import bpy  # noqa: E402
    from fm_blender import blackout as BO  # noqa: E402
    from fm_blender import preview as P  # noqa: E402
    from fm_blender import util as U  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

if not (RES / "SC03_SH050.json").exists():  # pragma: no cover
    pytest.skip("resolved shots absent", allow_module_level=True)


def shot(sid):
    return json.loads((RES / f"{sid}.json").read_text(encoding="utf-8"))


def canon():
    return json.loads((RES / "film.json").read_text(encoding="utf-8"))["canon"]


# ----------------------------------------------------------------------------- the spec (pure python)
def _bare(sid):
    """The shot as it was before the cinematographer added the resolved render fields."""
    s = copy.deepcopy(shot(sid))
    for blk in (s["lighting"], s["lighting"].get("after") or {}):
        for k in ("render_spec", "ambient", "floor", "exposure_target"):
            blk.pop(k, None)
    return s


@pytest.mark.parametrize("bare", [True, False])
def test_spec_is_the_same_with_or_without_the_shot_fields_present(bare):
    sp = BO.spec(_bare("SC03_SH050") if bare else shot("SC03_SH050"), canon())
    assert (sp["ambient"], sp["floor"], sp["key"], sp["door"]) == ("#1E2030", "#1B1C29", "#FFF1DE", "#C9A77E")
    assert sp["lit_mix"] == pytest.approx(0.30) and sp["reach_m"] == pytest.approx(0.5)
    assert sp["door_shots"] == ("SC03_SH070",)
    assert sp["key_lin"] == pytest.approx(U.lin("#FFF1DE"))   # the canon hex, not a kelvin value


def test_spec_reads_the_shot_fields_when_the_cinematographer_added_them():
    s = copy.deepcopy(shot("SC03_SH060"))
    s["lighting"]["render_spec"] = "look.lighting.sc03_blackout_render"
    s["lighting"]["ambient"] = {"$canon": "look.color.scene.sc03", "value": canon()["look.color.scene.sc03"]}   # resolved ref
    s["lighting"]["floor"] = "#202233"
    s["lighting"]["exposure_target"] = "look.exposure.scene_keys"
    sp = BO.spec(s, canon())
    assert sp["ambient"] == "#1E2030"          # blackout.dominant, not the first colour of the scene entry (accent #F5B940)
    assert sp["floor"] == "#202233"
    assert sp["render_spec"] == "look.lighting.sc03_blackout_render"
    s["lighting"]["ambient"] = "look.color.scene.sc03"       # an unresolved id still falls back
    assert BO.spec(s, canon())["ambient"] == "#1E2030"


def test_blackout_applies_to_sh050_sh060_sh070_only():
    c = canon()
    assert [BO.is_blackout_shot(shot(f"SC03_SH0{n}"), c) for n in (20, 30, 40, 50, 60, 70)] == [False, False, False, True, True, True]
    assert not BO.is_blackout_shot(shot("SC01_SH020"), c)


def test_no_shadow_scaling_or_kelvin_pool_left_in_the_builders():
    for name in ("preview.py", "animate.py"):
        src = (ROOT / "blender" / "fm_blender" / name).read_text(encoding="utf-8")
        assert "dark_k" not in src and "c * dk" not in src, name
    assert "kelvin_lin(4200)" not in (ROOT / "blender" / "fm_blender" / "animate.py").read_text(encoding="utf-8")


# ----------------------------------------------------------------------------- the materials (bpy, no render)
@pytest.fixture(scope="module")
def scene():
    film, shots, cn, units, rig, door = P.init_scene(str(RES), 64)
    return cn, units


def _shadow(mat):
    return [nd for nd in mat.node_tree.nodes if nd.type == "VALTORGB"][0].color_ramp.elements[0].color[:3]


def _lit(mat):
    return [nd for nd in mat.node_tree.nodes if nd.type == "VALTORGB"][0].color_ramp.elements[1].color[:3]


def _obj(name):
    o = bpy.data.objects.get(name)
    return o if o is not None else sorted((x for x in bpy.data.objects if x.name.startswith(name)), key=lambda x: x.name)[0]


def test_shadow_tones_are_replaced_not_scaled(scene):
    cn, _ = scene
    sp = BO.spec(shot("SC03_SH050"), cn)
    originals = {n: _obj(n).active_material for n in ("shop_floor", "stock0_00", "poster0", "shop_counter", "fridge0", "gondola0_end0")}
    before = {n: (list(_shadow(m)), list(_lit(m))) for n, m in originals.items()}
    BO.apply(bpy, True, sp)
    try:
        assert _shadow(_obj("shop_floor").active_material) == pytest.approx(U.lin("#1E2030"), abs=1e-6)     # set surface
        assert _shadow(_obj("shop_wall_back").active_material) == pytest.approx(U.lin("#1E2030"), abs=1e-6)
        for n in ("stock0_00", "poster0", "shop_counter", "fridge0", "gondola0_end0"):                       # merchandise-like
            m = _obj(n).active_material
            assert _shadow(m) == pytest.approx(U.lin("#1B1C29"), abs=1e-6), n
            old = before[n][0]
            assert _shadow(m) != pytest.approx([c * 0.04 for c in old], abs=1e-3), n     # never the old scaled shadow
        # the lit tone is mix(base, base x key, 0.30), only reachable inside the pool
        base = before["stock0_00"][1]
        key = U.lin("#FFF1DE")
        assert _lit(_obj("stock0_00").active_material) == pytest.approx([b * 0.7 + b * k * 0.3 for b, k in zip(base, key)], abs=1e-6)
        # the originals were never mutated
        for n, m in originals.items():
            assert list(_shadow(m)) == pytest.approx(before[n][0], abs=1e-9) and list(_lit(m)) == pytest.approx(before[n][1], abs=1e-9)
    finally:
        BO.apply(bpy, False, sp)
    for n, m in originals.items():
        assert _obj(n).active_material is m                        # lit shots (and every other shot) get the original back


def test_emissives_become_a_dark_non_emissive_material_and_stay_visible(scene):
    cn, _ = scene
    sp = BO.spec(shot("SC03_SH050"), cn)
    lights = [o for o in bpy.data.objects if o.get("fm_shop_light")]
    assert len(lights) >= 4                                         # panels and fridge glass
    orig = {o.name: o.active_material for o in lights}
    assert all(any(nd.type == "EMISSION" for nd in m.node_tree.nodes) for m in orig.values())
    BO.apply(bpy, True, sp)
    try:
        for o in lights:
            m = o.active_material
            assert not o.hide_render                                # dark shapes, not hidden
            assert m is not orig[o.name]
            assert m.get("fm_bo_off") or "fm_bo_of" in m
            assert _shadow(m) == pytest.approx(U.lin("#1B1C29"), abs=1e-6) and _lit(m) == pytest.approx(U.lin("#1B1C29"), abs=1e-6)
        em = [nd for o in lights for nd in o.active_material.node_tree.nodes if nd.type == "EMISSION"]
        assert all(nd.inputs[0].links for nd in em)                 # only the cel shader's output, never a constant glow colour
    finally:
        BO.apply(bpy, False, sp)
    assert all(o.active_material is orig[o.name] for o in lights)


def test_apply_is_idempotent_and_off_is_a_no_op_on_a_clean_scene(scene):
    cn, _ = scene
    sp = BO.spec(shot("SC03_SH050"), cn)
    assert BO.apply(bpy, False, sp) == 0
    BO.apply(bpy, True, sp)
    assert BO.apply(bpy, True, sp) == 0
    assert BO.apply(bpy, False, sp) > 0
    assert BO.apply(bpy, False, sp) == 0


def test_pool_light_is_the_canon_glow_colour_and_a_soft_shadowless_spot(scene):
    from mathutils import Vector
    cn, _ = scene
    sp = BO.spec(shot("SC03_SH050"), cn)
    col = U.get_collection("fm.rig")
    o = BO.make_pool_light(bpy, "phoneglow.test", Vector((0, 0, 1)), sp["pool_w"], sp["key_lin"], col)
    assert list(o.data.color) == pytest.approx(U.lin("#FFF1DE"), abs=1e-6)
    assert o.data.type == "SPOT" and not o.data.use_shadow and o.data.energy == pytest.approx(BO.POOL_W)
    BO.aim_pool(o, Vector((0, -1, 0)))
    assert (o.rotation_quaternion @ Vector((0, 0, -1))).y < -0.99          # shines along the screen normal
    assert BO.pool_position(Vector((1, 5, 1)), Vector((0, 1, 0))).y < 5   # on the screen side of the phone
