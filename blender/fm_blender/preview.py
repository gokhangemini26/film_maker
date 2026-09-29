"""Build all sets once, then render a mid-shot still per shot. Run inside Blender:

blender -b --factory-startup --python blender/run_preview.py -- <resolved_dir> <out_dir> [shot,shot..] [width]
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

from . import util as U
from . import sets as S
from .characters import figure

STREET_SCENES = {"SC01", "SC02", "SC04", "SC06"}
DUSK = {"SC04", "SC05", "SC06"}


def load(resolved_dir):
    film = json.load(open(os.path.join(resolved_dir, "film.json"), encoding="utf-8"))
    shots = {}
    for sid in film["shots"]:
        shots[sid] = json.load(open(os.path.join(resolved_dir, sid + ".json"), encoding="utf-8"))
    return film, shots


def setup_render(film, width):
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    fm = film["format"]
    sc.render.resolution_x = width
    sc.render.resolution_y = int(round(width / fm["aspect_ratio"]))
    sc.render.resolution_percentage = 100
    sc.render.fps = fm["fps"]
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.display_settings.display_device = "sRGB"
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:  # noqa: BLE001
        pass


def world_sky(dusk, canon):
    key = "look.color.sky.dusk" if dusk else "look.color.sky.golden_hour"
    stops = canon.get(key) or []
    w = bpy.data.worlds.get("fm.world") or bpy.data.worlds.new("fm.world")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    if stops:
        els = ramp.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, st in zip(els, stops):
            e.position = st["pos"]
            e.color = (*st["linear"], 1)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = w
    return bg


def parse_facing(text, pos, cam, street):
    t = text.lower()
    to_cam = Vector((cam.x - pos.x, cam.y - pos.y, 0))
    if "away" in t:
        v = -to_cam
    elif "camera" in t:
        v = to_cam
    elif street:
        v = Vector((0, 0, 0))
        for w, d in (("west", (0, 1)), ("north", (1, 0)), ("south", (-1, 0)), ("east", (0, -1))):
            if w in t:
                v = Vector((d[0], d[1], 0))
                break
        if v.length == 0:
            v = to_cam
    else:
        v = Vector((0, 1, 0)) if any(w in t for w in ("south", "west", "stand", "phone")) else to_cam
    if v.length < 1e-6:
        v = Vector((0, 1, 0))
    return v.normalized()


def pose_for(scene, shot_id, cid):
    n = int(shot_id.split("SH")[1])
    if cid == "hana":
        return "sit_chair"
    if scene == "SC01":
        return "sit_car"
    if scene == "SC03":
        return "kneel" if n >= 50 else "stand"
    if scene == "SC04":
        return "kneel" if n == 40 else "sit_kerb"
    if scene == "SC06":
        return "sit_kerb"
    return "stand"


def clear_shot_objects():
    for o in [o for o in bpy.data.objects if o.get("fm_shot")]:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if d is not None and d.users == 0:
            for coll in (bpy.data.lights, bpy.data.cameras, bpy.data.meshes):
                if d.name in coll:
                    coll.remove(d)
                    break


def mark(o):
    o["fm_shot"] = True
    return o


def add_light(kind, name, loc, energy, color, col, size=None, rot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "POINT":
        ld.shadow_soft_size = size or 0.1
    if kind == "SUN":
        ld.angle = math.radians(1.0)
    o = bpy.data.objects.new(name, ld)
    col.objects.link(o)
    o.location = loc
    if rot is not None:
        o.rotation_euler = rot
    return mark(o)


def aim(obj, target, up="Y"):
    d = Vector(target) - obj.location
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("-Z", up)


def unit_offset(scene):
    if scene == "SC03":
        return S.SHOP_ORIGIN
    if scene == "SC05":
        return S.ROOM_ORIGIN
    return Vector((0, 0, 0))


def render_shot(film, shot, canon, units, rig, door_name, out_dir, bg):
    scene = shot["scene_id"]
    sid = shot["shot_id"]
    n = int(sid.split("SH")[1])
    off = unit_offset(scene)
    street = scene in STREET_SCENES
    units["street"].hide_render = not street
    units["shop"].hide_render = scene != "SC03"
    units["room"].hide_render = scene != "SC05"
    clear_shot_objects()

    cam_c = shot["camera"]
    sp = Vector(cam_c["start_position"])
    ep = Vector(cam_c.get("end_position", cam_c["start_position"]))
    cpos = (sp + ep) / 2 + off
    cam_data = bpy.data.cameras.new("cam." + sid)
    cam_data.lens = cam_c["lens_mm"]
    cam_data.sensor_width = cam_c["sensor_width_mm"]
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.clip_start = 0.02
    if cam_c.get("dof", {}).get("enabled"):
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = cam_c["dof"].get("f_stop", 5.6)
    cam = mark(bpy.data.objects.new("cam." + sid, cam_data))
    rig.objects.link(cam)
    cam.location = cpos
    bpy.context.scene.camera = cam

    # car door
    door = bpy.data.objects.get(door_name)
    if door is not None:
        hinge = Vector(door["fm_hinge_xy"]) if False else None
        dl = door.dimensions.y
        base = Vector(door.get("fm_closed_loc", door.location))
        door["fm_closed_loc"] = list(base)
        opened = scene in ("SC02", "SC04", "SC06")
        ang = math.radians(door["fm_open_angle_deg"]) if opened else 0.0
        hy = base.y + dl / 2
        door.location = Vector((base.x + (0 if not opened else 0), hy, base.z)) + Vector((0, 0, 0))
        rel = Vector((0, -dl / 2, 0))
        rel.rotate(__import__("mathutils").Euler((0, 0, -ang)))
        door.location = Vector((base.x, hy, base.z)) + rel
        door.rotation_euler = (0, 0, -ang)

    figs = {}
    for ch in shot["characters"]:
        pos = Vector(ch["position"]) + off
        pose = pose_for(scene, sid, ch["id"])
        facing = parse_facing(ch["facing"], pos, cpos, street)
        if pose.startswith("sit") or pose == "kneel":
            pos.z = off.z
        props = ch["canon"]["proportions"]
        tmp = bpy.data.collections.new("fm.tmp." + ch["id"])
        rig.children.link(tmp) if False else bpy.context.scene.collection.children.link(tmp)
        info = figure(tmp, ch["id"], canon, props, pos, facing, pose)
        for o in tmp.objects:
            mark(o)
        figs[ch["id"]] = (info, tmp)

    def target(name):
        if name in figs:
            return figs[name][0]["head"] - Vector((0, 0, 0.1))
        if name in ("phone_ren", "crank_charger") and "ren" in figs:
            i = figs["ren"][0]
            return i["chest"] + i["facing"] * 0.3 - Vector((0, 0, 0.25))
        return {
            "passenger_door": Vector((0.2, 0.0, 0.7)),
            "shop_door": Vector((-1.8, 12.0, 1.0)),
            "ceiling_panels": S.SHOP_ORIGIN + Vector((2.25, 4.5, 2.7)),
            "socket_corner": S.SHOP_ORIGIN + Vector((4.25, 8.9, 0.4)),
            "phone_hana": S.ROOM_ORIGIN + Vector((0.25, -0.3, 0.75)),
            "west_along_pavement": Vector((cpos.x, cpos.y + 10, cpos.z - 0.05)),
        }.get(name, Vector((cpos.x, cpos.y + 3, cpos.z)))

    aim(cam, target(cam_c["look_at"]))
    if cam_c.get("dof", {}).get("enabled"):
        cam_data.dof.focus_distance = max((target(cam_c["look_at"]) - cpos).length, 0.1)

    if "ren" in figs and scene != "SC02":
        i = figs["ren"][0]
        ph = U.box("phone_ren." + sid, (0.071, 0.147, 0.0085), i["hands"] + i["facing"] * 0.12 + Vector((0, 0, 0.12)), figs["ren"][1],
                   U.toon({"hex": "#33333D", "linear": U.lin("#33333D")}))
        ph.rotation_euler = (0, 0, math.atan2(i["facing"].y, i["facing"].x) + math.pi / 2)
        sc = U.box("phone_ren_screen." + sid, (0.06, 0.13, 0.002), ph.location, figs["ren"][1],
                   U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5))
        sc.rotation_euler = ph.rotation_euler
        sc.location = ph.location + Vector((0, 0, 0.005))
        mark(ph), mark(sc)
    # lights
    ls = canon.get("look.color.light_sources") or []
    def ls_col(src, default):
        for e in ls:
            if e.get("source") == src:
                return e["linear"]
        return U.lin(default)
    dusk = scene in DUSK
    col = rig
    if street:
        elev = math.radians(2.0 if dusk else 6.0)
        s = Vector((0, math.cos(elev), math.sin(elev)))
        add_light("SUN", "sun." + sid, (0, 0, 10), 2.5 if dusk else 4.0,
                  ls_col("afterglow_rim_dusk" if dusk else "sun_golden_hour", "#FFD9A0"), col,
                  rot=(-s).to_track_quat("-Z", "Y").to_euler())
        bg.inputs[1].default_value = 0.8
    elif scene == "SC03":
        lit = n < 50
        bg.inputs[1].default_value = 0.0
        for o in bpy.data.objects:
            if o.get("fm_shop_light"):
                o.hide_render = not lit
        if lit:
            for i in range(4):
                add_light("POINT", f"panel{i}.{sid}", S.SHOP_ORIGIN + Vector((2.25, 9.0 * (i + 0.5) / 4, 2.4)), 260, (1.0, 0.95, 0.85), col, size=0.4)
        else:
            i = figs["ren"][0]
            add_light("POINT", "phone." + sid, i["hands"] + i["facing"] * 0.15, 15, ls_col("phone_glow", "#FFF1DE"), col, size=0.1)
    else:
        bg.inputs[1].default_value = 0.0
        add_light("AREA", "window." + sid, S.ROOM_ORIGIN + Vector((0, -0.3, 1.45)), 250, ls_col("sky_fill_dusk", "#9CA2D0"), col, size=1.0,
                  rot=(math.radians(-90), 0, 0))
        add_light("POINT", "lamp." + sid, S.ROOM_ORIGIN + Vector((-0.35, -0.28, 1.1)), 60, ls_col("desk_lamp", "#FFD6A0"), col, size=0.08)
        add_light("POINT", "phone." + sid, S.ROOM_ORIGIN + Vector((0.25, -0.3, 0.85)), 8, ls_col("phone_glow", "#FFF1DE"), col, size=0.05)

    dark_k = 0.04 if (scene == "SC03" and n >= 50) else 1.0
    for m in bpy.data.materials:
        if "fm_shadow" in m and m.node_tree:
            for nd in m.node_tree.nodes:
                if nd.type == "VALTORGB":
                    nd.color_ramp.elements[0].color = (*[c * dark_k for c in m["fm_shadow"]], 1)
    path = os.path.join(out_dir, sid + ".png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for _, tmp in figs.values():
        U.remove_collection(tmp)
    return path


def main(argv):
    resolved_dir, out_dir = argv[0], argv[1]
    only = set(argv[2].split(",")) if len(argv) > 2 and argv[2] not in ("", "all") else None
    width = int(argv[3]) if len(argv) > 3 else 960
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    film, shots = load(resolved_dir)
    canon = film["canon"]
    setup_render(film, width)
    bg = world_sky(False, canon)
    units = {}
    for name in ("street", "shop", "room"):
        c = U.get_collection("fm." + name)
        units[name] = c
    S.build_street(units["street"], canon)
    door = S.build_car(units["street"], canon)["door"]
    S.build_shop(units["shop"], canon)
    S.build_room(units["room"], canon)
    rig = U.get_collection("fm.rig")
    done = []
    for sid, shot in shots.items():
        if only and sid not in only:
            continue
        world_sky(shot["scene_id"] in DUSK, canon)
        bg = bpy.context.scene.world.node_tree.nodes["Background"]
        try:
            done.append(render_shot(film, shot, canon, units, rig, door, out_dir, bg))
            print("FM_OK", sid, flush=True)
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("FM_FAIL", sid, e, flush=True)
    json.dump({"rendered": [os.path.basename(p) for p in done], "builder": __import__("fm_blender").BUILDER_VERSION},
              open(os.path.join(out_dir, "preview_report.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
