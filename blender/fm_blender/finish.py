"""Locked finish steps that happen inside Blender, for the FINAL profile only: the compositor glare.

Source of truth is the LOCKED canon entry `look.style.glow` (never hard-coded here):
  glow_sources: emissives_only, max_radius_pct_frame_width: 1.5, streaks/star_glare/ghosts/bokeh_discs: false,
  implementation: compositor_glare_bloom_on_emission_pass.

How it is built (and why it is not the stock Emission pass):
  * Nearly every material in this film is an Emission shader (the cel shader is Diffuse -> Shader to RGB -> Emission), so the
    EEVEE Emission pass is the whole picture, not "the emissives". Real light sources (phone screens, lamps, panels, fridge
    glass, adapter ring, door glass) are therefore flat materials built with `util.flat(glow=True)`; while `util.GLOW_AOV`
    is on they also write their emitted colour to the colour AOV `fm_glow`. That AOV is the emission pass the glare reads.
  * The compositor: Render Layers (Image, fm_glow) -> Glare (BLOOM) on fm_glow -> halo = bloom * (1 - fm_glow_mask) (nothing is added
    on top of the emitter itself, so a lit screen keeps its contents; the value AOV fm_glow_mask marks the sources) -> Image + halo.
    BLOOM has no streaks, stars or ghosts; bokeh discs are never produced (no lens-blur node, no bokeh). Canon that asks
    for any of them is refused loudly instead of silently ignored.
  * The Bloom Size is a fraction of the frame width in Blender 5.x (a socket); size * width is the nominal radius in
    pixels, so `size = max_radius_pct / 100` keeps the halo inside the cap at every resolution. Before 5.0 (a 1-9 integer
    property that doubles per step) the nearest step at or under the cap is used.
  * API differences guarded here: Blender 5.0+ keeps the compositor in `scene.compositing_node_group` (a node tree with a
    Group Output) and Glare is configured through input sockets; 4.x uses `scene.use_nodes` + `scene.node_tree` + a
    Composite node and Glare properties. The mix node is `ShaderNodeMix` (5.x) or `CompositorNodeMixRGB` (4.x).

Nothing in this module runs for draft, preview, frames or playblast renders: those never call `enable_glow_aov` or
`apply_glare`, so their materials and pixels are untouched.
"""
from __future__ import annotations

import math

GLARE_AOV = "fm_glow"
MASK_AOV = "fm_glow_mask"
IMPLEMENTATION = "compositor_glare_bloom_on_emission_pass"
CANON_ID = "look.style.glow"
# Builder choices that canon does not fix (recorded in the final manifest with the canon values, so a change restales it).
BLOOM_STRENGTH = 2.0       # halo gain over the bloom of the source; tuned on a lit phone insert (1.0 was barely visible)
BLOOM_THRESHOLD = 0.0      # the AOV already holds only emissives, so no highlight cut is needed


class FinishError(ValueError):
    """The canon asks for something this builder does not implement, or the compositor API is not what was expected."""


def glare_params(canon: dict, width: int) -> dict | None:
    """Glare parameters from the canon value of `look.style.glow` (the resolved film canon mapping, or the value itself).
    None when the film's canon has no such entry (a film that locks no glow gets none); an entry this builder cannot honour
    raises FinishError."""
    if isinstance(canon, dict) and CANON_ID not in canon and "max_radius_pct_frame_width" not in canon:
        return None
    g = canon.get(CANON_ID, canon) if isinstance(canon, dict) else None
    if isinstance(g, dict) and "value" in g and isinstance(g["value"], dict):
        g = g["value"]
    if not isinstance(g, dict) or "max_radius_pct_frame_width" not in g:
        raise FinishError(f"canon {CANON_ID} is missing or has no max_radius_pct_frame_width: the final render needs it")
    if g.get("implementation", IMPLEMENTATION) != IMPLEMENTATION:
        raise FinishError(f"canon {CANON_ID}.implementation is {g.get('implementation')!r}; this builder implements {IMPLEMENTATION}")
    if g.get("glow_sources", "emissives_only") != "emissives_only":
        raise FinishError(f"canon {CANON_ID}.glow_sources is {g.get('glow_sources')!r}; only emissives_only is implemented")
    asked = [k for k in ("streaks", "star_glare", "ghosts") if g.get(k)]
    if asked:
        raise FinishError(f"canon {CANON_ID} asks for {', '.join(asked)}, but the bloom glare implements none of them")
    pct = float(g["max_radius_pct_frame_width"])
    if not 0.0 < pct <= 100.0:
        raise FinishError(f"canon {CANON_ID}.max_radius_pct_frame_width {pct} is outside (0, 100]")
    frac = pct / 100.0
    w = int(width)
    return {"source": CANON_ID, "type": "BLOOM", "aov": GLARE_AOV, "max_radius_pct_frame_width": pct,
            "max_radius_px": round(frac * w, 2), "width_px": w,
            "size": frac,                                           # Blender 5.x: fraction of the frame width
            "size_step_pre5": bloom_step_pre5(frac),                # Blender 4.x: 1..9, each step doubles the radius
            "strength": BLOOM_STRENGTH, "threshold": BLOOM_THRESHOLD}


def bloom_step_pre5(frac: float) -> int:
    """Largest 1..9 glare step whose radius (2**(n-9) of the frame width) does not exceed `frac` of it; 1 at the minimum."""
    return int(min(9, max(1, math.floor(9 + math.log2(max(frac, 1e-9))))))


def enable_glow_aov() -> None:
    """Turn on the AOV output of the glow materials. Must run before the scene's materials are built (final profile only)."""
    from . import util as U
    U.GLOW_AOV[0] = True


# ------------------------------------------------------------------------------------------------------- compositor
def _in(node, ident):
    for s in node.inputs:
        if s.identifier == ident or s.name == ident:
            return s
    return None


def _out(node, ident):
    for s in node.outputs:
        if s.identifier == ident or s.name == ident:
            return s
    return None


def _set_menu(sock_or_prop_owner, value_names):
    """Set a Blender 5.x menu socket to the first value it accepts (menu item names differ in case between builds)."""
    for v in value_names:
        try:
            sock_or_prop_owner.default_value = v
            return v
        except (TypeError, ValueError):
            continue
    raise FinishError(f"menu socket {sock_or_prop_owner.name!r} accepts none of {value_names}")


def _new_tree(bpy, scene):
    """The scene's compositor tree plus a callable that links a colour socket into the output. API guarded for 4.x / 5.x."""
    if hasattr(scene, "compositing_node_group"):                       # Blender 5.0+
        ng = bpy.data.node_groups.new("fm_final_compositor", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        out = ng.nodes.new("NodeGroupOutput")
        scene.compositing_node_group = ng
        return ng, out, "5.x"
    scene.use_nodes = True                                              # Blender 4.x
    ng = scene.node_tree
    for n in list(ng.nodes):
        ng.nodes.remove(n)
    out = ng.nodes.new("CompositorNodeComposite")
    return ng, out, "4.x"


def _add_mix(ng, blend="ADD", clamp=False):
    """A colour mix node (blend 'ADD' / 'SUBTRACT') and its (A, B, result) sockets: ShaderNodeMix in 5.x, CompositorNodeMixRGB
    in 4.x."""
    try:
        n = ng.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        n.clamp_result = clamp
        _in(n, "Factor_Float").default_value = 1.0
        return n, _in(n, "A_Color"), _in(n, "B_Color"), _out(n, "Result_Color")
    except (RuntimeError, TypeError, AttributeError):
        n = ng.nodes.new("CompositorNodeMixRGB")
        n.blend_type = blend
        n.inputs[0].default_value = 1.0
        n.use_clamp = clamp
        return n, n.inputs[1], n.inputs[2], n.outputs[0]


def apply_glare(bpy, scene, params: dict) -> dict:
    """Build the glare compositor on `scene` (the active view layer gains the fm_glow AOV). Returns a report of what was built."""
    vl = scene.view_layers[0]
    for name, typ in ((GLARE_AOV, "COLOR"), (MASK_AOV, "VALUE")):
        if name not in [a.name for a in vl.aovs]:
            a = vl.aovs.add()
            a.name, a.type = name, typ
    ng, out, flavour = _new_tree(bpy, scene)
    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    rl.layer = vl.name
    aov_sock, mask_sock, img_sock = _out(rl, GLARE_AOV), _out(rl, MASK_AOV), _out(rl, "Image")
    if aov_sock is None or mask_sock is None or img_sock is None:
        raise FinishError(f"render layers node has no {GLARE_AOV!r} / 'Image' output (found {[s.name for s in rl.outputs][:8]})")
    g = ng.nodes.new("CompositorNodeGlare")
    g.name = g.label = "fm_glare"
    if _in(g, "Type") is not None and _in(g, "Size") is not None:       # 5.x: sockets
        _set_menu(_in(g, "Type"), ("Bloom", "BLOOM"))
        _in(g, "Size").default_value = params["size"]
        _in(g, "Strength").default_value = params["strength"]
        _in(g, "Highlights Threshold").default_value = params["threshold"]
        q = _in(g, "Quality")
        if q is not None:
            try:
                _set_menu(q, ("High", "HIGH"))
            except FinishError:
                pass
        glare_out = _out(g, "Glare")
        api = "sockets"
    else:                                                               # 4.x: node properties
        g.glare_type = "BLOOM"
        g.size = params["size_step_pre5"]
        g.threshold = params["threshold"]
        if hasattr(g, "mix"):
            g.mix = 1.0                                                 # glare only (the add below keeps the untouched Image)
        if hasattr(g, "strength"):
            g.strength = params["strength"]
        g.quality = "HIGH"
        glare_out = _out(g, "Glare") or _out(g, "Image")
        api = "properties"
    if glare_out is None:
        raise FinishError("glare node has no glare output")
    # The bloom also adds light on top of the emitter itself, which would blow a lit phone screen out to white and cost the
    # legibility of what is on it (canon camera.inserts.legibility). So the halo is the bloom outside the source only:
    # halo = bloom * (1 - fm_glow_mask) (a Mix of bloom -> black by the mask), then Image + halo.
    halo, h_a, h_b, h_res = _add_mix(ng, "MIX")
    h_b.default_value = (0.0, 0.0, 0.0, 1.0)             # the mix's B default is mid grey, not black
    if _in(halo, "Factor_Float") is not None:
        ng.links.new(mask_sock, _in(halo, "Factor_Float"))
    else:
        ng.links.new(mask_sock, halo.inputs[0])
    mix, a_in, b_in, res = _add_mix(ng, "ADD")
    ng.links.new(aov_sock, _in(g, "Image"))
    ng.links.new(glare_out, h_a)
    ng.links.new(img_sock, a_in)
    ng.links.new(h_res, b_in)
    ng.links.new(res, out.inputs[0] if flavour == "5.x" else _in(out, "Image"))
    return {"flavour": flavour, "glare_api": api, "mix_node": mix.bl_idname, "type": params["type"], "size": params["size"],
            "aov": GLARE_AOV, "nodes": sorted(n.name for n in ng.nodes)}
