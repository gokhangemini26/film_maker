"""Compositor glare, the locked `look.style.glow` finish step (blender/fm_blender/finish.py).

Pure part: parameters read from canon, the frame command's final flag. bpy part: the compositor really builds (guarded for both
Blender APIs), only the final profile feeds the glare, a lit emitter keeps its contents, the halo stays inside the canon cap,
and draft materials are untouched."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT / "core"))

from fm import blenderrun  # noqa: E402
from fm_blender import finish as FN  # noqa: E402

GLOW = {"glow_sources": "emissives_only", "max_radius_pct_frame_width": 1.5, "streaks": False, "star_glare": False,
        "ghosts": False, "bokeh_discs": False, "implementation": "compositor_glare_bloom_on_emission_pass"}
HAVE_BPY = importlib.util.find_spec("bpy") is not None


# ------------------------------------------------------------------------------------------------ pure
def test_params_are_read_from_the_canon_value_and_scale_with_width():
    p = FN.glare_params({"look.style.glow": GLOW}, 1920)
    assert p["type"] == "BLOOM" and p["source"] == "look.style.glow" and p["aov"] == "fm_glow"
    assert p["max_radius_pct_frame_width"] == 1.5 and p["max_radius_px"] == 28.8 and p["size"] == 0.015
    assert FN.glare_params({"look.style.glow": {**GLOW, "max_radius_pct_frame_width": 1.0}}, 960)["max_radius_px"] == 9.6
    assert FN.glare_params(GLOW, 1920)["size"] == 0.015            # the bare value is accepted too


def test_no_glow_canon_means_no_glare():
    assert FN.glare_params({"look.style.sky": {}}, 1920) is None


@pytest.mark.parametrize("over,word", [({"streaks": True}, "streaks"), ({"star_glare": True}, "star_glare"),
                                       ({"ghosts": True}, "ghosts"), ({"implementation": "ffmpeg_bloom"}, "implementation"),
                                       ({"glow_sources": "everything"}, "glow_sources"),
                                       ({"max_radius_pct_frame_width": 0}, "outside")])
def test_canon_this_builder_cannot_honour_is_refused_not_ignored(over, word):
    with pytest.raises(FN.FinishError, match=word):
        FN.glare_params({"look.style.glow": {**GLOW, **over}}, 1920)


def test_missing_radius_is_refused():
    bad = {k: v for k, v in GLOW.items() if k != "max_radius_pct_frame_width"}
    with pytest.raises(FN.FinishError, match="max_radius"):
        FN.glare_params({"look.style.glow": bad}, 1920)


def test_pre5_bloom_step_never_exceeds_the_cap():
    for frac in (0.001, 0.0078, 0.015, 0.03, 0.5, 1.0):
        n = FN.bloom_step_pre5(frac)
        assert 1 <= n <= 9
        assert n == 1 or 2.0 ** (n - 9) <= frac            # each step doubles the radius; the chosen one fits under the cap
    assert FN.bloom_step_pre5(0.015) == 2 and FN.bloom_step_pre5(1.0) == 9


def test_frame_command_marks_only_the_final_profile(tmp_path, monkeypatch):
    class Info:
        executable = "/x/blender"
        version = "5.2.0"

    monkeypatch.setattr(blenderrun, "require_blender", lambda repo: Info())
    kw = dict(draft=False, resolved=tmp_path, out=tmp_path, sid="S", width=64, spec="1", stamp=False, samples=None, fast=False,
              resume=False)
    assert blenderrun._frame_cmd(tmp_path, **kw)[0][-1] == "-"                   # frames / playblast / preview: no glare
    assert blenderrun._frame_cmd(tmp_path, **kw, final=True)[0][-1] == "final"


# ------------------------------------------------------------------------------------------------ bpy
bpy_only = pytest.mark.skipif(not HAVE_BPY, reason="bpy module not installed")


def _scene(width, glow_aov, final, strength=None):
    """A lit emitter (a glow material) on a mid-grey world, 5 m from a 50 mm camera; returns the rendered RGB as numpy."""
    import bpy
    import numpy as np
    from fm_blender import util as U

    bpy.ops.wm.read_factory_settings(use_empty=True)
    U.GLOW_AOV[0] = glow_aov
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = width, width * 9 // 16, 100
    sc.view_settings.view_transform = "Standard"
    sc.eevee.taa_render_samples = 1
    sc.world = bpy.data.worlds.new("w")
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location, cam.rotation_euler = (0, -5, 0), (1.5708, 0, 0)
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 0), rotation=(1.5708, 0, 0))
    bpy.context.object.data.materials.append(U.flat({"hex": "#FFFFFF", "linear": [1, 1, 1]}, strength=3.0, glow=True))
    if final:
        gp = FN.glare_params({"look.style.glow": GLOW}, width)
        if strength is not None:
            gp["strength"] = strength
        FN.apply_glare(bpy, sc, gp)
    sc.render.filepath = str(Path(bpy.app.tempdir or "/tmp") / f"fm_glare_test_{width}_{int(final)}.png")
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(sc.render.filepath)
    px = np.array(im.pixels[:]).reshape(im.size[1], im.size[0], 4)[:, :, :3]
    bpy.data.images.remove(im)
    return px


@bpy_only
def test_flat_material_writes_the_glow_aovs_only_when_enabled():
    import bpy
    from fm_blender import util as U

    bpy.ops.wm.read_factory_settings(use_empty=True)
    U.GLOW_AOV[0] = False
    off = U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5, glow=True)
    assert not [n for n in off.node_tree.nodes if n.bl_idname == "ShaderNodeOutputAOV"]      # draft: the material is unchanged
    assert off.name == "fm.flat.%.3f_%.3f_%.3f.2.5" % tuple(U.lin("#FFF1DE"))
    U.GLOW_AOV[0] = True
    try:
        on = U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5, glow=True)
        assert on is not off and on.name.endswith(".glow")
        aovs = {n.aov_name: n for n in on.node_tree.nodes if n.bl_idname == "ShaderNodeOutputAOV"}
        assert set(aovs) == {"fm_glow", "fm_glow_mask"}
        assert [round(c, 4) for c in aovs["fm_glow"].inputs[0].default_value[:3]] == [round(c * 2.5, 4) for c in U.lin("#FFF1DE")]
        plain = U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5)          # not a light: never feeds the glare
        assert not [n for n in plain.node_tree.nodes if n.bl_idname == "ShaderNodeOutputAOV"]
    finally:
        U.GLOW_AOV[0] = False


@bpy_only
def test_compositor_is_built_for_the_running_blender_api():
    import bpy

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    rep = FN.apply_glare(bpy, sc, FN.glare_params({"look.style.glow": GLOW}, 1920))
    assert rep["flavour"] == ("5.x" if hasattr(sc, "compositing_node_group") else "4.x")
    assert rep["type"] == "BLOOM" and {"fm_glow", "fm_glow_mask"} <= {a.name for a in sc.view_layers[0].aovs}
    ng = sc.compositing_node_group if rep["flavour"] == "5.x" else sc.node_tree
    kinds = sorted(n.bl_idname for n in ng.nodes)
    assert kinds.count("CompositorNodeGlare") == 1 and kinds.count("CompositorNodeRLayers") == 1
    assert "CompositorNodeComposite" in kinds or "NodeGroupOutput" in kinds
    assert all(link.is_valid for link in ng.links)


@bpy_only
def test_halo_stays_inside_the_cap_and_the_lit_source_keeps_its_pixels():
    import numpy as np

    w = 960
    draft = _scene(w, glow_aov=False, final=False)
    fin = _scene(w, glow_aov=True, final=True)
    d = np.abs(fin - draft).max(2)
    assert d.max() > 0.05                                           # a halo exists
    ys, xs = np.nonzero(d > 0.004)                                  # about 1 level of 8-bit
    edge = round(0.25 / 5 * 50 / 36 * w)                            # half width of the emitter in px
    cx, cy = w // 2, draft.shape[0] // 2
    reach = max(abs(xs - cx).max(), abs(ys - cy).max()) - edge
    assert reach <= 0.015 * w, f"halo reaches {reach}px, cap {0.015 * w}px"
    inner = np.abs(fin - draft)[cy - edge + 3:cy + edge - 3, cx - edge + 3:cx + edge - 3]
    assert inner.max() < 0.004                                      # nothing added on top of the emitter itself

