import hashlib
import json
import math

import bpy
import bmesh
from mathutils import Vector

OWNER = "fm_blender"


def h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def tag(idb, fm_id, **extra):
    idb["fm_owner"] = OWNER
    idb["fm_id"] = fm_id
    for k, v in extra.items():
        idb[k] = v
    return idb


def lin(hex_or_dict):
    """Linear RGB from a resolved colour dict or a '#RRGGBB' string."""
    if isinstance(hex_or_dict, dict):
        return list(hex_or_dict["linear"])
    s = hex_or_dict.lstrip("#")
    c = [int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def first_hex(value, default="#888888"):
    """First colour found in a resolved canon value (dict/list/colour)."""
    if isinstance(value, dict):
        if "hex" in value and "linear" in value:
            return value
        for v in value.values():
            r = first_hex(v, None)
            if r:
                return r
    elif isinstance(value, list):
        for v in value:
            r = first_hex(v, None)
            if r:
                return r
    return None if default is None else {"hex": default, "linear": lin(default)}


# ------------------------------------------------------------------ materials
def _mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        for n in list(m.node_tree.nodes):
            m.node_tree.nodes.remove(n)
        tag(m, name)
    return m


def toon(color, shadow=None, threshold=0.5, outline=False, name=None):
    """Two-tone cel material. `color` is lit tone; shadow defaults to a cooler, darker mix."""
    lit = lin(color)
    sh = lin(shadow) if shadow else [c * 0.72 for c in lit]
    key = name or f"fm.toon.{'%.3f_%.3f_%.3f' % tuple(lit)}.{threshold}"
    m = bpy.data.materials.get(key)
    if m is not None:
        return m
    m = _mat(key)
    m["fm_shadow"] = list(sh)
    nt = m.node_tree
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*sh, 1)
    ramp.color_ramp.elements[1].position = threshold
    ramp.color_ramp.elements[1].color = (*lit, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(d.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs[0], bw.inputs[0])
    nt.links.new(bw.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def flat(color, name=None, strength=1.0):
    lit = lin(color)
    key = name or f"fm.flat.{'%.3f_%.3f_%.3f' % tuple(lit)}.{strength}"
    m = bpy.data.materials.get(key)
    if m is not None:
        return m
    m = _mat(key)
    nt = m.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*lit, 1)
    em.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def outline_mat(color):
    key = "fm.outline." + "%.3f_%.3f_%.3f" % tuple(lin(color))
    m = bpy.data.materials.get(key)
    if m is not None:
        return m
    m = flat(color, name=key)
    m.use_backface_culling = True
    return m


# ------------------------------------------------------------------ geometry
def _obj(name, mesh, col, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), fm_id=None):
    o = bpy.data.objects.new(name, mesh)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    if mat is not None:
        o.data.materials.append(mat)
    tag(o, fm_id or name)
    return o


def box(name, size, loc, col, mat, rot=(0, 0, 0)):
    """Axis-aligned box centred at loc; size = (sx, sy, sz)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _obj(name, me, col, mat, loc, rot)


def cyl(name, radius, depth, loc, col, mat, rot=(0, 0, 0), segs=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=radius, radius2=radius, depth=depth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _obj(name, me, col, mat, loc, rot)


def sphere(name, radius, loc, col, mat, scale=(1, 1, 1), segs=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=radius)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = _obj(name, me, col, mat, loc)
    o.scale = scale
    return o


def between(name, a, b, radius, col, mat, segs=12):
    """Cylinder from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    length = max(d.length, 1e-4)
    o = cyl(name, radius, length, (a + b) / 2, col, mat, segs=segs)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o


def add_outline(obj, color, thickness=0.012):
    """Coloured inverted-hull outline as a Solidify modifier using a second material slot."""
    if len(obj.data.materials) < 2:
        obj.data.materials.append(outline_mat(color))
    mod = obj.modifiers.new("fm_outline", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1
    mod.use_flip_normals = True
    mod.material_offset = 1
    return obj


def get_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def remove_collection(c):
    for o in list(c.all_objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and hasattr(data, "users") and data.users == 0:
            try:
                (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else
                 bpy.data.cameras if isinstance(data, bpy.types.Camera) else
                 bpy.data.lights).remove(data)
            except Exception:  # noqa: BLE001
                pass
    bpy.data.collections.remove(c)
