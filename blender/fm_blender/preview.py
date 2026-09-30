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
from . import phone as PH

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


def parse_facing(text, pos, cam, street, scene=""):
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
            v = {"SC01": Vector((0, 1, 0)), "SC04": Vector((-1, 0, 0)), "SC06": Vector((-1, 0, 0))}.get(scene, to_cam)
    else:
        v = Vector((0, 1, 0)) if any(w in t for w in ("south", "west", "stand", "phone")) else to_cam
    if v.length < 1e-6:
        v = Vector((0, 1, 0))
    return v.normalized()


import re as _re


def _scene_rule_pose(scene, n, cid):
    if cid == "hana":
        return "sit_chair"
    if scene == "SC01":
        return "sit_car"
    if scene == "SC03":
        return "kneel" if n >= 20 else "stand"
    if scene == "SC04":
        return "kneel" if n == 40 else "sit_kerb"
    if scene == "SC06":
        return "sit_kerb"
    return "stand"


def pose_from_text(text, scene):
    """Keyword mapper over one free-text key pose. Returns a figure pose name or None when the text says nothing."""
    t = (text or "").lower()
    if _re.search(r"kneel|onto (the |his )?(right |left |one )?knee|lunge|crouch", t):
        return "kneel"  # no separate crouch pose in characters.py: kneel is the closest
    if "kerb" in t and _re.search(r"sit|seat|lower|onto|back to", t):
        return "sit_kerb"
    if _re.search(r"chair|desk", t):
        return "sit_chair"
    if _re.search(r"\bsit|seated|behind the wheel|on the (top of the )?wheel|hands on the .*wheel|hunched|forearms loose|\blap\b|thighs", t):
        return {"SC01": "sit_car", "SC05": "sit_chair"}.get(scene, "sit_kerb" if scene in ("SC04", "SC06") else "sit_car")
    if _re.search(r"running|upright, pivoting|standing|\bstands\b|foot contact|foot lands|foot on the pavement|unfolding out", t):
        return "stand"
    return None


def pose_for(scene, shot_id, cid, shot=None):
    n = int(shot_id.split("SH")[1])
    fallback = _scene_rule_pose(scene, n, cid)
    if not shot:
        return fallback
    ch = ((shot.get("animation") or {}).get("characters") or {}).get(cid) or {}
    keys = ch.get("keys") or []
    if not keys:
        return fallback
    mid = ((shot.get("frames") or {}).get("count") or 0) // 2
    active = max([i for i, k in enumerate(keys) if k.get("f", 0) <= mid] or [0])
    # the mid-shot still shows the pose active at the middle frame: search from it back to the first key
    for k in reversed(keys[:active + 1]):
        p = pose_from_text(k.get("pose"), scene)
        if p:
            return p
    return fallback


_CANON_LS = []


def kelvin_lin(k):
    """Colour for a spec'd temperature: the look canon's light source at that kelvin when one exists (art-directed),
    else a blackbody fit (Tanner Helland, sRGB decoded) softened halfway to white."""
    best = min((e for e in _CANON_LS if e.get("kelvin")), key=lambda e: abs(e["kelvin"] - k), default=None)
    if best is not None and abs(best["kelvin"] - k) <= 0.04 * k:
        return tuple(best["linear"])
    t = max(1000.0, min(40000.0, float(k))) / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, v)) / 255.0 for v in (r, g, b)]
    lin = [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c]
    return tuple(0.5 * v + 0.5 for v in lin)


def _prop_texts(shot, key):
    pr = (shot.get("animation") or {}).get("props") or {}
    return [str(v) for k, v in pr.items() if key in k]


def car_state(shots, sid, default_door_deg):
    """Walk the shots in film order up to `sid` and carry the car panel states from their animation.props text
    (passenger_door, glovebox_lid). Returns (door_open_deg, glovebox_open)."""
    door_deg, glove = 0.0, False
    for k, shot in shots.items():
        for t in _prop_texts(shot, "passenger_door"):
            tl = t.lower()
            m = _re.search(r"(\d+)\s*deg", tl.split("settles back to")[-1]) if "open" in tl else None
            if "open" in tl and "not open" not in tl:
                door_deg = float(m.group(1)) if m else default_door_deg
            if _re.search(r"\b(shut|closes|closed|slams)\b", tl) and "open" not in tl:
                door_deg = 0.0
        for t in _prop_texts(shot, "car"):
            if _re.search(r"closed glovebox|glovebox (is )?closed|glovebox shut", t.lower()):
                glove = False
        for t in _prop_texts(shot, "glovebox_lid"):
            tl = t.lower()
            if _re.search(r"drops|lowered|open|down", tl):
                glove = True
            elif _re.search(r"closed|shut|closes", tl):
                glove = False
        if k == sid:
            break
    return door_deg, glove


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


def aim_up(obj, target, up_vec):
    """Point -Z at target with the camera's +Y as close to up_vec as possible (roll-exact)."""
    d = Vector(target) - obj.location
    obj.rotation_mode = "QUATERNION"
    z = (-d).normalized()
    x = Vector(up_vec).cross(z)
    x = x.normalized() if x.length > 1e-6 else Vector((1, 0, 0))
    y = z.cross(x)
    m = __import__("mathutils").Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z)))
    obj.rotation_quaternion = m.to_quaternion()


def headphones_down(all_shots, sid, cid, scene):
    """Hana's headphones slide to the neck (animation.props hana_headphones text 'switched to the neck ... at fNN')."""
    if cid != "hana":
        return False
    down = False
    for k, sh in all_shots.items():
        if sh.get("scene_id") != scene:
            continue
        for t in _prop_texts(sh, "headphones"):
            m = _re.search(r"neck[^.;]*?\bf(\d+)", t.lower())
            if "neck" in t.lower():
                f_ = int(m.group(1)) if m else 0
                if k == sid:
                    mid = ((sh.get("frames") or {}).get("count") or 0) // 2
                    down = down or mid >= f_
                else:
                    down = True
        if k == sid:
            break
    return down


CAR_PIECES = ("car_", "seat_passenger", "dashboard", "console", "seat_driver")


def crank_lap(i, scene, n):
    """Where the crank sits: in the lap, or in both hands in SC04 SH040/SH050 (lifted out / turning)."""
    if scene == "SC04" and n in (40, 50):
        return i["hands"] + i["facing"] * 0.08 + Vector((0, 0, 0.03))
    if scene == "SC04" and n == 90:
        return i["hip"] + i["facing"] * 0.16 + Vector((0, 0, 0.2))  # rests on the near knee, top and pip above it
    return i["hip"] + i["facing"] * 0.16 + Vector((0, 0, 0.14))


def unit_offset(scene):
    if scene == "SC03":
        return S.SHOP_ORIGIN
    if scene == "SC05":
        return S.ROOM_ORIGIN
    return Vector((0, 0, 0))


def render_shot(film, shot, canon, units, rig, door_name, out_dir, bg, all_shots=None, animate=None):
    all_shots = all_shots or {shot["shot_id"]: shot}
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
    sp = Vector(cam_c.get("start_position") or (0, -5, 1.5))
    ep = Vector(cam_c.get("end_position") or cam_c.get("start_position") or (0, -5, 1.5))
    cpos = (sp + ep) / 2 + off
    cam_data = bpy.data.cameras.new("cam." + sid)
    cam_data.lens = cam_c.get("lens_mm", 35)
    cam_data.sensor_width = cam_c.get("sensor_width_mm", 36)
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.clip_start = 0.02
    if cam_c.get("dof", {}).get("enabled"):
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = cam_c["dof"].get("f_stop", 5.6)
    cam = mark(bpy.data.objects.new("cam." + sid, cam_data))
    rig.objects.link(cam)
    cam.location = cpos
    bpy.context.scene.camera = cam

    # car panels: passenger door and glovebox lid carried shot to shot from animation.props text
    car = door_name if isinstance(door_name, dict) else {"door": door_name}
    door = bpy.data.objects.get(car.get("door")) if car.get("door") else None
    door_deg, glove_open = car_state(all_shots, sid, door["fm_open_angle_deg"] if door is not None else 60.0)
    if door is not None:
        dl = door.dimensions.y
        base = Vector(door.get("fm_closed_loc", door.location))
        door["fm_closed_loc"] = list(base)
        ang = math.radians(door_deg)
        hy = float((door.get("fm_hinge_xy") or [base.x, base.y + dl / 2])[1])  # canon: hinge at the door's front end (y 0.525)
        rel = Vector((0, base.y - hy, 0))
        rel.rotate(__import__("mathutils").Euler((0, 0, -ang)))
        door.location = Vector((base.x, hy, base.z)) + rel
        door.rotation_euler = (0, 0, -ang)
    lid = bpy.data.objects.get(car.get("glovebox_lid")) if car.get("glovebox_lid") else None
    if lid is not None:
        lid.location = Vector(lid["fm_open_loc"] if glove_open else lid["fm_closed_loc"])
        lid.rotation_euler = (math.radians(-90) if glove_open else 0.0, 0, 0)

    figs = {}
    for ch in shot["characters"]:
        pos = Vector(ch.get("position") or (0, 0, 0)) + off
        pose = pose_for(scene, sid, ch["id"], shot)
        facing = parse_facing(ch.get("facing", "camera"), pos, cpos, street, scene)
        if pose.startswith("sit") or pose == "kneel":
            pos.z = off.z
        props = dict((ch.get("canon") or {}).get("proportions") or {"height_m": 1.7})
        if headphones_down(all_shots, sid, ch["id"], scene):
            props["headphones_state"] = "down"
        face_txt = str((((shot.get("animation") or {}).get("characters") or {}).get(ch["id"]) or {}).get("face", "")).lower()
        if _re.search(r"face (is )?(hidden|not seen|turned away)|mouth (is )?(hidden|covered)|hand to (the|her|his) mouth", face_txt):
            props["mouth_hidden"] = True
        tmp = bpy.data.collections.new("fm.tmp." + ch["id"])
        rig.children.link(tmp) if False else bpy.context.scene.collection.children.link(tmp)
        info = figure(tmp, ch["id"], canon, props, pos, facing, pose, hold=True)
        for o in tmp.objects:
            mark(o)
        figs[ch["id"]] = (info, tmp)

    def target(name):
        if name in figs:
            i_ = figs[name][0]
            if name == "ren" and scene == "SC04" and n in (40, 50, 90):  # shot notes: aim between the crown and the pip
                return (i_["head"] + Vector((0, 0, 0.1))) * 0.62 + crank_lap(i_, scene, n) * 0.38
            return i_["head"] - Vector((0, 0, 0.1))
        if name == "crank_charger" and "ren" in figs:
            return figs["ren"][0]["hip"] + figs["ren"][0]["facing"] * 0.16 + Vector((0, 0, 0.14))
        if name == "phone_ren" and "ren" in figs:
            return figs["ren"][0]["phone"]
        return {
            "passenger_door": Vector((0.2, 0.0, 0.7)),
            "shop_door": Vector((-1.8, 12.0, 1.0)),
            "ceiling_panels": S.SHOP_ORIGIN + Vector((2.25, 4.5, 2.7)),
            "socket_corner": S.SHOP_ORIGIN + Vector((4.25, 8.9, 0.4)),
            "phone_hana": S.ROOM_ORIGIN + Vector((0.25, -0.3, 0.75)),
            "west_along_pavement": Vector((cpos.x, cpos.y + 10, cpos.z - 0.05)),
        }.get(name, Vector((cpos.x, cpos.y + 3, cpos.z)))

    tgt = target(cam_c.get("look_at", ""))
    aim(cam, tgt)
    if cam_c.get("dof", {}).get("enabled"):
        cam_data.dof.focus_distance = max((target(cam_c.get("look_at", "")) - cpos).length, 0.1)

    if "ren" in figs:
        i = figs["ren"][0]
        is_insert = (shot.get("composition") or {}).get("framing") == "insert" and cam_c.get("look_at", "") == "phone_ren"
        zup = Vector((0, 0, 1))
        toward = (cpos - i["phone"]) if is_insert else (i["head"] - i["phone"])
        nz = toward.normalized() if toward.length > 1e-6 else zup
        yv = zup - nz * zup.dot(nz)
        yv = yv.normalized() if yv.length > 1e-4 else Vector((1, 0, 0))
        xv = yv.cross(nz)
        ui_assets = [a for a in shot.get("assets", []) if a.startswith("ui.")]
        ph = PH.build_phone(figs["ren"][1], sid, i["phone"], xv, yv, nz, ui_assets,
                            PH.screen_state(scene, n, ui_assets), PH.colors_for(shot, canon), screen_on=(scene != "SC06" or n < 90))
        for o in figs["ren"][1].objects:
            mark(o)
        if is_insert:  # resolved camera honoured as-is: screen squared to the lens, camera up = phone top edge
            sh_ = Vector((0, 0, 0))
            if (cpos - i["phone"]).length < 0.4:  # 0.30 m text inserts: the spec centres the screen; shift the lens parallel to it (never tilt) to the named part
                ua = set(ui_assets)
                if ua == {"ui.status_bar"}:
                    du, dv = 0.012, 0.056
                elif "ui.compose_field" in ua:
                    du, dv = 0.0, -0.004
                elif "ui.thread_sent_bubble" in ua:
                    du, dv = 0.005, 0.02
                else:
                    du, dv = 0.0, 0.0
                sh_ = xv.normalized() * du + yv.normalized() * dv
                cam.location = cam.location + sh_
                cpos = cam.location.copy()
            aim_up(cam, i["phone"] + sh_, yv)
            if cam_c.get("dof", {}).get("enabled"):
                cam_data.dof.focus_distance = max(((i["phone"] + sh_) - cpos).length, 0.1)
    # crank charger: built for every shot that lists it (world.props.crank_charger); the pip is the only amber
    if "ren" in figs and "world.props.crank_charger" in shot.get("assets", []):
        i = figs["ren"][0]
        f_ = i["facing"]
        lap = crank_lap(i, scene, n)
        # canon world.props.crank_charger: body 0.13x0.065x0.042, arm 0.085, knob dia 0.02 x 0.022, pip dia 0.006
        # pip state from the shot text / look.lighting.power_indicators: lit while cranking (SC04 SH050 from f30, SH060-SH080),
        # 40 % and falling at the SH090 stop, off in SH040 (arm folded), SC01 and SC06
        arm_out = (scene == "SC04" and n >= 50) or scene == "SC06"
        pip_k = 1.0 if (scene == "SC04" and 50 <= n < 90) else (0.25 if (scene == "SC04" and n == 90) else 0.0)
        yaw = math.atan2(f_.y, f_.x)
        rz = Vector((0, 0, 1))

        def at(x_, y_, z_):
            v_ = Vector((x_, y_, z_))
            v_.rotate(__import__("mathutils").Euler((0, 0, yaw)))
            return lap + v_
        cm = U.toon({"hex": "#D6C592", "linear": U.lin("#D6C592")})
        am = U.toon({"hex": "#B8A878", "linear": U.lin("#B8A878")})
        parts = [U.box("crank_body." + sid, (0.13, 0.065, 0.042), lap, figs["ren"][1], cm, rot=(0, 0, yaw))]
        top = 0.021
        sx = 0.045  # spindle at the near end of the top face
        if arm_out:
            parts.append(U.box("crank_arm." + sid, (0.012, 0.012, 0.085), at(sx, 0, top + 0.0425), figs["ren"][1], am, rot=(0, 0, yaw)))
            parts.append(U.cyl("crank_knob." + sid, 0.01, 0.022, at(sx, 0.0, top + 0.085 + 0.006), figs["ren"][1], am, rot=(math.pi / 2, 0, yaw)))
        else:
            parts.append(U.box("crank_arm." + sid, (0.085, 0.012, 0.01), at(sx - 0.0425, 0, top + 0.005), figs["ren"][1], am, rot=(0, 0, yaw)))
            parts.append(U.cyl("crank_knob." + sid, 0.01, 0.022, at(sx - 0.085, 0.0, top + 0.011), figs["ren"][1], am, rot=(math.pi / 2, 0, yaw)))
        amb = canon.get("look.color.accent_power_amber") or {}
        a_hex = amb.get("hex", "#F5B940")
        off_hex = "#6B6B5F"
        if pip_k >= 1.0:
            ph_hex = a_hex
        elif pip_k > 0:
            ph_hex = "#" + "".join("%02X" % int(round(int(a_hex[k:k + 2], 16) * pip_k + int(off_hex[k:k + 2], 16) * (1 - pip_k))) for k in (1, 3, 5))
        else:
            ph_hex = off_hex
        parts.append(U.cyl("crank_pip." + sid, 0.003, 0.004, at(-0.05, 0.0, top + 0.002), figs["ren"][1], U.flat({"hex": ph_hex, "linear": U.lin(ph_hex)})))
        for o in parts:
            mark(o)
    # Hana's phone (SC05): held when she is in the shot, else lying on the desk, square to the lens for inserts
    if "world.props.phone_hana" in shot.get("assets", []):
        st_ = PH.screen_state(scene, n, [])
        cols_ = PH.colors_for(shot, canon)
        zup = Vector((0, 0, 1))
        if "hana" in figs:
            hi = figs["hana"][0]
            pos_, toward = hi["phone"], hi["head"] - hi["phone"]
        else:
            pos_ = S.ROOM_ORIGIN + Vector((0.25, -0.3, 0.75))
            toward = cpos - pos_
            pos_ = pos_ + toward.normalized() * 0.06
        nz = toward.normalized()
        yv = zup - nz * zup.dot(nz)
        yv = yv.normalized() if yv.length > 1e-4 else Vector((1, 0, 0))
        hp = PH.build_phone(figs["hana"][1] if "hana" in figs else rig, sid + "h", pos_, yv.cross(nz), yv, nz, ["ui.photo_only"], st_, cols_, body_hex="#3D3A4A")
        mark(hp)
        for o in hp.children:
            mark(o)
    # cull static objects the camera sits inside (car body, seat backs, walls)
    culled = []
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.get("fm_shot") or o.type != "MESH" or o.name.startswith(("fm.",)):
            continue
        if o.get("fm_culled_by_preview") is not None:
            o.hide_render = False
            o["fm_culled_by_preview"] = None
    for coll in (units["street"], units["shop"], units["room"]):
        if coll.hide_render:
            continue
        for o in coll.objects:
            if o.type != "MESH":
                continue
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
            hi = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
            if all(lo[k] - 0.03 <= cpos[k] <= hi[k] + 0.03 for k in range(3)):
                o.hide_render = True
                o["fm_culled_by_preview"] = 1
                culled.append(o.name)
    # sight-line clearance: hide static set pieces standing between the lens and what the shot is about.
    # Inserts: every static piece may go, ray-cast to the screen/prop corners (not only the centre).
    # Other shots: car body pieces only (CAR_PIECES), cast to the subject's head/chest/hip; the subject is never touched.
    is_ins = (shot.get("composition") or {}).get("framing") == "insert"
    pts = []
    if is_ins and cam_c.get("look_at", "") == "phone_ren" and "ren" in figs:
        i_ = figs["ren"][0]
        zup_ = Vector((0, 0, 1))
        nz_ = (cpos - i_["phone"]).normalized()
        yv_ = zup_ - nz_ * zup_.dot(nz_)
        yv_ = yv_.normalized() if yv_.length > 1e-4 else Vector((0, 1, 0))
        xv_ = yv_.cross(nz_)
        pts = [i_["phone"] + xv_ * a_ * 0.034 + yv_ * b_ * 0.072 for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)]
    elif is_ins:
        pts = [tgt + Vector((a_, b_, c_)) * 0.05 for a_ in (-1, 1) for b_ in (-1, 1) for c_ in (0,)] + [tgt]
    else:
        for cid_, (info_, _t) in figs.items():
            pts += [info_["head"], info_["chest"], info_["hip"], (info_["chest"] + info_["hip"]) / 2]
        if cam_c.get("look_at", "") in figs:
            pass
    if pts:
        dg = bpy.context.evaluated_depsgraph_get()
        for goal in pts:
            org = cam.location.copy()
            for _ in range(10):
                d_ = goal - org
                dist = d_.length
                if dist < 0.05:
                    break
                hit, loc, _nrm, _idx, ho, _m = bpy.context.scene.ray_cast(dg, org, d_.normalized(), distance=dist - 0.03)
                if not hit:
                    break
                if not ho.get("fm_shot") and not ho.hide_render and (is_ins or ho.name.startswith(CAR_PIECES)):
                    ho.hide_render = True
                    ho["fm_culled_by_preview"] = 1
                    culled.append(ho.name)
                org = loc + d_.normalized() * 0.01
    if (shot.get("composition") or {}).get("framing") == "insert":
        for cid, (info, tmp) in figs.items():
            for o in tmp.objects:
                n_ = o.name.split("_", 1)[1] if "_" in o.name else o.name
                if n_.startswith(("head", "hair", "eye", "tuft", "neck", "thigh", "shin", "torso", "uarm", "farm", "hand")):
                    o.hide_render = True
    if culled:
        print("FM_CULLED", sid, culled, flush=True)
    if scene == "SC05":
        for w, cond in (("room_wall_south", cpos.x < S.ROOM_ORIGIN.x - 1.4), ("room_wall_north", cpos.x > S.ROOM_ORIGIN.x + 1.4)):
            if w in bpy.data.objects:
                bpy.data.objects[w].hide_render = cond
    # lights
    ls = canon.get("look.color.light_sources") or []
    _CANON_LS[:] = [e for e in ls if isinstance(e, dict) and "linear" in e]
    def ls_col(src, default):
        for e in ls:
            if e.get("source") == src:
                return e["linear"]
        return U.lin(default)
    dusk = scene in DUSK
    col = rig
    lt = shot.get("lighting") or {}
    key, fill, rim, amb = lt.get("key"), lt.get("fill"), lt.get("rim"), lt.get("ambient")
    key_src = (key.get("source", "") if isinstance(key, dict) else str(key or "")).lower()
    key_k = key.get("temperature_k") if isinstance(key, dict) else None
    rim_k = rim.get("temperature_k") if isinstance(rim, dict) else None
    fill_t = (fill if isinstance(fill, str) else str((fill or {}).get("source", ""))).lower()
    phone_key = "phone" in key_src
    flick = 0.8 if "flicker" in str(lt.get("key_state", "")).lower() else 1.0
    m_el = _re.search(r"(\d+(?:\.\d+)?)\s*deg up", key_src)

    def sun(tag, kelvin, elev_deg, energy, default_src):
        color = kelvin_lin(kelvin) if kelvin else ls_col(default_src, "#FFD9A0")
        e = math.radians(elev_deg)
        v = Vector((0, math.cos(e), math.sin(e)))  # sun sits west (+y), shining toward -y
        add_light("SUN", tag + "." + sid, (0, 0, 10), energy, color, col, rot=(-v).to_track_quat("-Z", "Y").to_euler())

    def cam_side_fill(color, energy, size=2.0):
        # soft bounce/sky fill from the lens side, aimed at the subject
        ref = figs["ren"][0]["head"] if "ren" in figs else tgt
        o = add_light("AREA", "fill." + sid, cpos + Vector((0, 0, 0.3)), energy, color, col, size=size)
        aim(o, ref)

    def phone_light(energy, kelvin=None):
        if "ren" in figs:
            i_ = figs["ren"][0]
            add_light("POINT", "phone." + sid, i_["phone"] + i_["facing"] * 0.06 + Vector((0, 0, 0.04)), energy * flick,
                      kelvin_lin(kelvin) if kelvin else ls_col("phone_glow", "#FFF1DE"), col, size=0.08)

    if street:
        if phone_key or dusk:
            # dusk: afterglow rim from the west (rim block, 3000 K); the phone is the key when the spec says so
            sun("rim", rim_k, 2.0, 2.5 if dusk else 4.0, "afterglow_rim_dusk")
            bg.inputs[1].default_value = 0.8
            if phone_key and scene != "SC06":
                phone_light(15)
        elif isinstance(key, dict) and "sun" in key_src:
            sun("sun", key_k, float(m_el.group(1)) if m_el else 6.0, 4.0, "sun_golden_hour")
            bg.inputs[1].default_value = 0.8
            if "bounce" in fill_t or "sky" in fill_t:
                cam_side_fill(kelvin_lin(3800) if "warm" in fill_t else ls_col("sky_fill_golden_hour", "#C8D3EA"), 60 if "warm" in fill_t else 90)
        else:
            # inserts (key = phone screen emission): keep the scene's ambient sun as low fill, phone is its own light
            sun("sun", None if dusk else 3200, 6.0, 2.5 if dusk else 4.0, "afterglow_rim_dusk" if dusk else "sun_golden_hour")
            bg.inputs[1].default_value = 0.8
    elif scene == "SC03":
        lit = n < 50
        bg.inputs[1].default_value = 0.0
        for o in bpy.data.objects:
            if o.get("fm_shop_light"):
                o.hide_render = not lit
        if lit:
            pc = kelvin_lin(key_k or 5000)
            for i in range(4):
                add_light("POINT", f"panel{i}.{sid}", S.SHOP_ORIGIN + Vector((2.25, 9.0 * (i + 0.5) / 4, 2.4)), 260, pc, col, size=0.4)
            if "fridge" in fill_t or "fridge" in str(rim).lower():
                add_light("AREA", "fridges." + sid, S.SHOP_ORIGIN + Vector((2.25, 8.6, 1.0)), 60, kelvin_lin(6500), col, size=2.0,
                          rot=(math.radians(90), 0, math.pi))
        else:
            i = figs["ren"][0]
            add_light("POINT", "phone." + sid, i["hands"] + i["facing"] * 0.15, 15 * flick, ls_col("phone_glow", "#FFF1DE"), col, size=0.1)
    else:
        bg.inputs[1].default_value = 0.25
        lamp_on = "lamp" in key_src or "lamp" in str(fill).lower() or "lamp" in str(lt.get("background_practicals", ""))
        add_light("AREA", "window." + sid, S.ROOM_ORIGIN + Vector((0, -0.3, 1.45)), 250, kelvin_lin(10000), col, size=1.0,
                  rot=(math.radians(-90), 0, 0))
        if lamp_on or "hana" in figs:
            add_light("POINT", "lamp." + sid, S.ROOM_ORIGIN + Vector((-0.35, -0.28, 1.1)), 60, kelvin_lin(key_k if lamp_on and key_k else 2700), col, size=0.08)
        add_light("POINT", "phone." + sid, S.ROOM_ORIGIN + Vector((0.25, -0.3, 0.85)), 8, ls_col("phone_glow", "#FFF1DE"), col, size=0.05)

    dark_k = 0.04 if (scene == "SC03" and n >= 50) else 1.0
    for m in bpy.data.materials:
        if "fm_shadow" in m and m.node_tree:
            for nd in m.node_tree.nodes:
                if nd.type == "VALTORGB":
                    nd.color_ramp.elements[0].color = (*[c * dark_k for c in m["fm_shadow"]], 1)
    if os.environ.get("FM_DEBUG"):
        near = sorted(((o.matrix_world.translation - cpos).length, o.name) for o in bpy.data.objects
                      if o.type in ("MESH", "LIGHT") and not o.hide_render)[:6]
        print("FM_NEAR", sid, [(round(d, 2), nme) for d, nme in near], flush=True)
    if animate is not None:  # animate.render_frames re-poses this assembled shot and renders its frames itself
        return animate(dict(film=film, shot=shot, canon=canon, units=units, rig=rig, car=car, bg=bg, cam=cam, cam_data=cam_data,
                            cpos=cpos, tgt=tgt, off=off, figs=figs, out_dir=out_dir, culled=culled))
    path = os.path.join(out_dir, sid + ".png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for _, tmp in figs.values():
        U.remove_collection(tmp)
    return path


def init_scene(resolved_dir, width):
    """Empty scene with the render settings, the sky and every set built once: (film, shots, canon, units, rig, door)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    film, shots = load(resolved_dir)
    canon = film["canon"]
    setup_render(film, width)
    world_sky(False, canon)
    units = {}
    for name in ("street", "shop", "room"):
        c = U.get_collection("fm." + name)
        units[name] = c
    door = None
    if "world.sets.street" in canon:
        S.build_street(units["street"], canon)
        if "world.sets.ren_car" in canon:
            door = S.build_car(units["street"], canon)
    else:
        S.build_generic(units["street"], canon)   # any film without street canon still gets a stage
    if "world.sets.corner_shop" in canon:
        S.build_shop(units["shop"], canon)
    if "world.sets.hana_room" in canon:
        S.build_room(units["room"], canon)
    rig = U.get_collection("fm.rig")
    return film, shots, canon, units, rig, door


def main(argv):
    resolved_dir, out_dir = argv[0], argv[1]
    only = set(argv[2].split(",")) if len(argv) > 2 and argv[2] not in ("", "all") else None
    width = int(argv[3]) if len(argv) > 3 else 960
    os.makedirs(out_dir, exist_ok=True)
    film, shots, canon, units, rig, door = init_scene(resolved_dir, width)
    done = []
    for sid, shot in shots.items():
        if only and sid not in only:
            continue
        world_sky(shot["scene_id"] in DUSK, canon)
        bg = bpy.context.scene.world.node_tree.nodes["Background"]
        try:
            done.append(render_shot(film, shot, canon, units, rig, door, out_dir, bg, shots))
            print("FM_OK", sid, flush=True)
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("FM_FAIL", sid, e, flush=True)
    json.dump({"rendered": [os.path.basename(p) for p in done], "builder": __import__("fm_blender").BUILDER_VERSION},
              open(os.path.join(out_dir, "preview_report.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
