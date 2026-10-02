"""Compositor colour grade for the OPT-IN cinematic pipeline.

Spec: the `grade` block of the RESOLVED shot (a shot-level block, else the canon `look.grade*` entry, merged by `fm resolve`;
schema in core/fm/schemas/cinematic.py). `apply_for_shot` (called from preview.render_shot) builds the node chain only when
the render profile selected Cycles; a shot without a grade, or any EEVEE profile, is untouched.

Node order (fixed, so a grade means the same thing everywhere):
    Render Layers (or whatever already feeds the output, e.g. the locked final glare) -> Exposure -> Color Balance
    -> Hue/Saturation -> RGB Curves -> Glare (optional bloom added on top) -> Group Output
`view_transform` / `look` are scene colour-management settings, not nodes; they are set separately. Standard stays the
default view transform: any other value is the film's explicit, canon-able choice.

Built for the Blender 5.x compositor (`scene.compositing_node_group`): exercised on the bpy 5.0.1 module, NOT yet on the
pinned 5.2.1. The Blender 4.x compositor is not supported here and fails loudly.

DaVinci Resolve is not automated: `fm post grade-handoff` writes the same spec as a hand-off for a colourist.
"""
from __future__ import annotations


class GradeError(ValueError):
    """The grade spec is invalid or this Blender's compositor API is not the expected one."""


VIEW_TRANSFORMS = ("Standard", "AgX", "Filmic", "Khronos PBR Neutral", "Raw")
STEPS = ("view_transform", "exposure", "color_balance", "saturation", "curves", "glare")


def _vec3(name, v, lo, hi):
    if not isinstance(v, (list, tuple)) or len(v) != 3 or any(not isinstance(x, (int, float)) for x in v):
        raise GradeError(f"grade.{name} must be three numbers")
    if any(not lo <= x <= hi for x in v):
        raise GradeError(f"grade.{name} values must be within [{lo}, {hi}]")
    return [float(x) for x in v]


def grade_plan(spec: dict) -> list[dict]:
    """Validate a resolved grade block and return its ordered steps (pure Python; the unit-tested contract)."""
    if not isinstance(spec, dict):
        raise GradeError("grade must be a mapping")
    plan: list[dict] = []
    vt = spec.get("view_transform")
    if vt is not None or spec.get("look") is not None:
        if vt is not None and vt not in VIEW_TRANSFORMS:
            raise GradeError(f"grade.view_transform {vt!r} must be one of {', '.join(VIEW_TRANSFORMS)}")
        plan.append({"step": "view_transform", "view_transform": vt, "look": spec.get("look")})
    if spec.get("exposure_ev") is not None:
        ev = float(spec["exposure_ev"])
        if not -10 <= ev <= 10:
            raise GradeError("grade.exposure_ev must be within [-10, 10]")
        plan.append({"step": "exposure", "ev": ev})
    cb = spec.get("color_balance")
    if cb:
        mode = cb.get("mode", "lift_gamma_gain")
        if mode == "lift_gamma_gain":
            row = {"mode": mode, **{k: _vec3("color_balance." + k, cb.get(k, [1, 1, 1]), 0.0, 4.0) for k in ("lift", "gamma", "gain")}}
        elif mode == "cdl":
            row = {"mode": mode, "offset": _vec3("color_balance.offset", cb.get("offset", [0, 0, 0]), -1.0, 1.0),
                   "power": _vec3("color_balance.power", cb.get("power", [1, 1, 1]), 0.0, 4.0),
                   "slope": _vec3("color_balance.slope", cb.get("slope", [1, 1, 1]), 0.0, 4.0)}
        else:
            raise GradeError(f"grade.color_balance.mode {mode!r} must be lift_gamma_gain or cdl")
        plan.append({"step": "color_balance", **row})
    if spec.get("saturation") is not None:
        s = float(spec["saturation"])
        if not 0 <= s <= 4:
            raise GradeError("grade.saturation must be within [0, 4]")
        plan.append({"step": "saturation", "value": s})
    pts = spec.get("curves")
    if pts:
        pts = [(float(x), float(y)) for x, y in pts]
        if len(pts) < 2 or any(not (0 <= x <= 1 and 0 <= y <= 1) for x, y in pts) or any(b[0] <= a[0] for a, b in zip(pts, pts[1:])):
            raise GradeError("grade.curves needs >= 2 points inside 0..1 with strictly increasing x")
        plan.append({"step": "curves", "points": pts})
    g = spec.get("glare")
    if g:
        typ = g.get("type", "bloom")
        if typ not in ("bloom", "fog_glow"):
            raise GradeError("grade.glare.type must be bloom or fog_glow")
        plan.append({"step": "glare", "type": typ, "threshold": float(g.get("threshold", 1.0)),
                     "strength": float(g.get("strength", 0.3)), "size": float(g.get("size", 0.02))})
    if not plan:
        raise GradeError("grade has no steps (view_transform, exposure_ev, color_balance, saturation, curves, glare)")
    return plan


# ------------------------------------------------------------------------------------------------ bpy side
def _set_view_transform(scene, step):
    vs = scene.view_settings
    if step.get("view_transform"):
        try:
            vs.view_transform = step["view_transform"]
        except TypeError as exc:
            have = [e.identifier for e in vs.bl_rna.properties["view_transform"].enum_items]
            raise GradeError(f"this Blender has no view transform {step['view_transform']!r} (available: {', '.join(have)})") from exc
    if step.get("look"):
        try:
            vs.look = step["look"]
        except TypeError as exc:
            have = [e.identifier for e in vs.bl_rna.properties["look"].enum_items]
            raise GradeError(f"this Blender has no look {step['look']!r} for the view transform (available: {', '.join(have)})") from exc


def _compositor(bpy, scene):
    """(node_group, Group Output node, socket currently feeding its Image input or None). Creates the tree when absent."""
    from . import finish as FN
    if not hasattr(scene, "compositing_node_group"):
        raise GradeError("the compositor grade needs the Blender 5.x compositor (scene.compositing_node_group)")
    ng = scene.compositing_node_group
    if ng is None:
        ng, out, _ = FN._new_tree(bpy, scene)
        return ng, out, None
    out = next((n for n in ng.nodes if n.bl_idname == "NodeGroupOutput"), None)
    if out is None:
        raise GradeError("the scene's compositor tree has no Group Output to splice the grade into")
    socks = [s for s in out.inputs if s.name == "Image"] or list(out.inputs)[:1]
    src = socks[0].links[0].from_socket if socks and socks[0].links else None
    if src is not None and src.node.name.startswith("fm_grade"):          # a grade from an earlier shot: go back to what fed it
        nd, ident = str(ng.get("fm_grade_upstream", "|")).split("|", 1)
        node = ng.nodes.get(nd)
        src = next((s for s in node.outputs if s.identifier == ident), None) if node is not None else None
    return ng, out, src


def apply_grade(scene, grade_spec: dict, log=print) -> dict:
    """Build the grade in `scene`'s compositor, splicing in front of whatever already feeds the output (the locked final glare,
    if any). Returns {'steps': [...], 'nodes': [...]}."""
    import bpy
    from . import finish as FN

    plan = grade_plan(grade_spec)
    if not scene.get("fm_grade_applied"):          # what to put back when a later shot has no grade
        scene["fm_grade_vt_prev"] = [scene.view_settings.view_transform, scene.view_settings.look]
    for step in plan:
        if step["step"] == "view_transform":
            _set_view_transform(scene, step)
    node_steps = [s for s in plan if s["step"] != "view_transform"]
    nodes: list[str] = []
    if node_steps:
        ng, out, src = _compositor(bpy, scene)
        for n in [n for n in ng.nodes if n.name.startswith("fm_grade") and n.name != "fm_grade_layers"]:
            ng.nodes.remove(n)
        if src is None:
            rl = ng.nodes.get("fm_grade_layers") or ng.nodes.new("CompositorNodeRLayers")
            rl.name = "fm_grade_layers"
            rl.scene = scene
            rl.layer = scene.view_layers[0].name
            src = FN._out(rl, "Image")
            if src is None:
                raise GradeError("render layers node has no Image output")
        ng["fm_grade_upstream"] = f"{src.node.name}|{src.identifier}"      # lets a later shot rebuild the grade in place
        cur = src
        for step in node_steps:
            kind = step["step"]
            if kind == "exposure":
                n = ng.nodes.new("CompositorNodeExposure")
                FN._in(n, "Exposure").default_value = step["ev"]
                cur = _chain(ng, n, cur)
            elif kind == "color_balance":
                n = ng.nodes.new("CompositorNodeColorBalance")
                _fill_color_balance(n, step)
                cur = _chain(ng, n, cur)
            elif kind == "saturation":
                n = ng.nodes.new("CompositorNodeHueSat")
                FN._in(n, "Saturation").default_value = step["value"]
                cur = _chain(ng, n, cur)
            elif kind == "curves":
                n = ng.nodes.new("CompositorNodeCurveRGB")
                _fill_curves(n, step["points"])
                cur = _chain(ng, n, cur)
            elif kind == "glare":
                n, cur = _glare(ng, cur, step)
            n.name = n.label = f"fm_grade_{kind}"
            nodes.append(n.name)
        sock = next((s for s in out.inputs if s.name == "Image"), None) or out.inputs[0]
        for lk in list(sock.links):
            ng.links.remove(lk)
        ng.links.new(cur, sock)
    scene["fm_grade_applied"] = True
    rep = {"steps": [s["step"] for s in plan], "nodes": nodes}
    log("FM_GRADE " + " ".join(f"{k}={v}" for k, v in rep.items()))
    return rep


def _chain(ng, node, cur):
    from . import finish as FN
    ng.links.new(cur, FN._in(node, "Image"))
    return FN._out(node, "Image")


def _fill_color_balance(n, step):
    from . import finish as FN
    mode = step["mode"]
    if hasattr(n, "correction_method"):                                    # pre-5.0 properties (kept for completeness)
        raise GradeError("the Blender 4.x compositor is not supported by the grade builder")
    FN._set_menu(FN._in(n, "Type"), ("Lift/Gamma/Gain", "LIFT_GAMMA_GAIN") if mode == "lift_gamma_gain"
                 else ("Offset/Power/Slope (ASC-CDL)", "OFFSET_POWER_SLOPE", "Offset/Power/Slope"))
    keys = ("lift", "gamma", "gain") if mode == "lift_gamma_gain" else ("offset", "power", "slope")
    for k in keys:
        s = FN._in(n, "Color " + k.capitalize())
        if s is None:
            raise GradeError(f"color balance node has no 'Color {k.capitalize()}' socket (found {[x.identifier for x in n.inputs][:10]})")
        s.default_value = (*step[k], 1.0)


def _fill_curves(n, pts):
    curve = n.mapping.curves[3]                      # 0..2 R,G,B; 3 = combined (master)
    while len(curve.points) > 2:
        curve.points.remove(curve.points[1])
    curve.points[0].location = pts[0]
    curve.points[-1].location = pts[-1]
    for x, y in pts[1:-1]:
        curve.points.new(x, y)
    n.mapping.update()


def _glare(ng, cur, step):
    from . import finish as FN
    g = ng.nodes.new("CompositorNodeGlare")
    if FN._in(g, "Type") is None or FN._in(g, "Size") is None:
        raise GradeError("glare node has no Type/Size sockets: the Blender 5.x compositor is required")
    FN._set_menu(FN._in(g, "Type"), ("Bloom", "BLOOM") if step["type"] == "bloom" else ("Fog Glow", "FOG_GLOW"))
    FN._in(g, "Size").default_value = step["size"]
    FN._in(g, "Strength").default_value = step["strength"]
    FN._in(g, "Highlights Threshold").default_value = step["threshold"]
    ng.links.new(cur, FN._in(g, "Image"))
    glare_out = FN._out(g, "Glare")
    if glare_out is None:
        raise GradeError("glare node has no Glare output")
    mix, a_in, b_in, res = FN._add_mix(ng, "ADD")
    mix.name = "fm_grade_glare_mix"
    ng.links.new(cur, a_in)
    ng.links.new(glare_out, b_in)
    return g, res


def clear_grade(scene) -> bool:
    """Undo a grade left by an earlier shot of the same process (the static preview reuses one scene): remove its nodes, feed
    the output from the original upstream again and put the view transform and look back as they were. True when something was undone."""
    if not scene.get("fm_grade_applied"):
        return False
    ng = getattr(scene, "compositing_node_group", None)
    if ng is not None:
        out = next((n for n in ng.nodes if n.bl_idname == "NodeGroupOutput"), None)
        nd, _, ident = str(ng.get("fm_grade_upstream", "|")).partition("|")
        up = ng.nodes.get(nd)
        src = next((s for s in up.outputs if s.identifier == ident), None) if up is not None else None
        for n in [n for n in ng.nodes if n.name.startswith("fm_grade") and n.name != "fm_grade_layers"]:
            ng.nodes.remove(n)
        if out is not None and src is not None:
            sock = next((s for s in out.inputs if s.name == "Image"), None) or out.inputs[0]
            for lk in list(sock.links):
                ng.links.remove(lk)
            ng.links.new(src, sock)
    prev = scene.get("fm_grade_vt_prev")
    if prev:
        scene.view_settings.view_transform, scene.view_settings.look = prev[0], prev[1]
    for k in ("fm_grade_applied", "fm_grade_vt_prev"):
        if k in scene:
            del scene[k]
    return True


def apply_for_shot(scene, shot: dict, log=print) -> dict | None:
    """The hook `preview.render_shot` calls for every shot: None (nothing touched) without a grade block or without a Cycles
    cinematic profile."""
    spec = shot.get("grade")
    if not spec:
        clear_grade(scene)               # no-op unless an earlier shot of this process was graded
        return None
    from . import render_engine as RE
    if RE.profile_from_env() is None:
        log(f"FM_GRADE skipped {shot.get('shot_id')}: the shot has a grade block but the render profile is not a Cycles "
            "(cinematic) profile; select one with --profile")
        return None
    return apply_grade(scene, spec, log)
