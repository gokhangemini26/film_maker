"""Persistent scene build: one .blend per project holding the film's units, reconciled by hash.

Run inside Blender (pinned exe or the bpy module) via blender/run_build.py:
    run_build.py <resolved_dir> <out.blend> [report.json]

Units (one collection each, tagged fm_owner/fm_id/fm_hash): set:street|shop|room, char:<id> (rest-pose proxy
figure), prop:<name> (phones), shot:<id> (camera + timeline marker "fm:<id>" at the shot's first frame).
Re-running rebuilds only units whose hash changed, removes orphans (fm_owner objects whose unit is no longer
wanted) and never touches objects without fm_owner. Blender is the engine, not the database: the .blend
can always be rebuilt from 09_resolved/.
"""
import json
import os
import sys

import bpy
from mathutils import Vector

from . import BUILDER_VERSION
from . import util as U
from . import sets as S
from . import phone as PH
from . import reconcile as R
from .characters import figure
from .preview import load, setup_render, unit_offset, aim

STAGE = {"char": Vector((300.0, 0, 0)), "prop": Vector((400.0, 0, 0))}   # off-set staging areas
TARGETS = {  # named look_at targets that are not characters (same points the preview uses)
    "passenger_door": (0.2, 0.0, 0.7), "shop_door": (-1.8, 12.0, 1.0),
    "ceiling_panels": (S.SHOP_ORIGIN.x + 2.25, 4.5, 2.7), "socket_corner": (S.SHOP_ORIGIN.x + 4.25, 8.9, 0.4),
    "phone_hana": (S.ROOM_ORIGIN.x + 0.25, -0.3, 0.75),
}


def coll_name(uid):
    kind, _, name = uid.partition(":")
    return f"fm.{name}" if kind == "set" else f"fm.{kind}.{name}"


def existing_units():
    return {c["fm_id"]: c.get("fm_hash", "") for c in bpy.data.collections
            if c.get("fm_owner") == U.OWNER and str(c.get("fm_id", "")).partition(":")[0] in ("set", "char", "prop", "shot")}


def _drop_data(data):
    if data is not None and getattr(data, "users", 1) == 0:
        for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
            if data.name in coll and coll[data.name] == data:
                coll.remove(data)
                break


def remove_owned(objs):
    n = 0
    for o in list(objs):
        if o.get("fm_owner") == U.OWNER:
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            _drop_data(d)
            n += 1
    return n


def purge_unit(coll):
    """Delete fm_owner objects of a unit collection; keep the collection (untagged) when foreign objects live in it."""
    remove_owned(coll.all_objects)
    if len(coll.all_objects) == 0:
        for ch in list(coll.children):
            bpy.data.collections.remove(ch)
        bpy.data.collections.remove(coll)
        return True
    for k in ("fm_owner", "fm_id", "fm_hash"):
        if k in coll:
            del coll[k]
    return False


def drop_marker(sid):
    sc = bpy.context.scene
    for m in [m for m in sc.timeline_markers if m.name == "fm:" + sid]:
        sc.timeline_markers.remove(m)


def stamp(coll, uid, spec):
    U.tag(coll, uid, fm_hash=spec["hash"], fm_kind=spec["kind"])
    for o in coll.all_objects:
        if o.get("fm_owner") != U.OWNER:
            U.tag(o, f"{uid}/{o.name}")
        o["fm_unit"] = uid
        o["fm_hash"] = spec["hash"]


# ------------------------------------------------------------------ unit builders
def build_set(name, film, col):
    canon = film["canon"]
    if name == "street":
        if "world.sets.street" in canon:
            S.build_street(col, canon)
            if "world.sets.ren_car" in canon:
                S.build_car(col, canon)
        else:
            S.build_generic(col, canon)
    elif name == "shop":
        S.build_shop(col, canon)
    elif name == "room":
        S.build_room(col, canon)


def build_char(cid, film, col, index):
    canon = film["canon"]
    props = dict(canon.get(f"characters.{cid}.proportions") or {"height_m": 1.7})
    pos = STAGE["char"] + Vector((3.0 * index, 0, 0))
    figure(col, cid, canon, props, pos, Vector((0, -1, 0)), "stand")


def build_prop(name, film, col, index):
    canon = film["canon"]
    who = "hana" if name == "phone_hana" else "ren"
    st = PH.screen_state("SC05" if who == "hana" else "SC01", 10, ["ui.photo_only"] if who == "hana" else [])
    ui = ["ui.photo_only"] if who == "hana" else []
    PH.build_phone(col, name, STAGE["prop"] + Vector((0.5 * index, 0, 1.0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                   Vector((0, -1, 0)), ui, st, PH.colors_for({}, canon), phone=who)


def build_shot(sid, film, shot, col):
    scene = shot["scene_id"]
    off = unit_offset(scene)
    c = shot["camera"]
    sp = Vector(c.get("start_position") or (0, -5, 1.5))
    ep = Vector(c.get("end_position") or c.get("start_position") or (0, -5, 1.5))
    cpos = (sp + ep) / 2 + off
    cd = bpy.data.cameras.new("cam." + sid)
    cd.lens = c.get("lens_mm", 35)
    cd.sensor_width = c.get("sensor_width_mm", 36)
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.02
    dof = c.get("dof") or {}
    if dof.get("enabled"):
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = dof.get("f_stop", 5.6)
    cam = bpy.data.objects.new("cam." + sid, cd)
    col.objects.link(cam)
    cam.location = cpos
    look = c.get("look_at", "")
    tgt = None
    for ch in shot.get("characters", []):
        if ch["id"] == look:
            hgt = (ch.get("canon", {}).get("proportions") or {}).get("height_m", 1.7)
            tgt = Vector(ch.get("position") or (0, 0, 0)) + off + Vector((0, 0, hgt * 0.85))
    if tgt is None and look in TARGETS:
        tgt = Vector(TARGETS[look])
    if tgt is None:
        tgt = Vector((cpos.x, cpos.y + 3, cpos.z))
    aim(cam, tgt)
    if dof.get("enabled"):
        cd.dof.focus_distance = max((tgt - cpos).length, 0.025)   # clip_start 0.02 + eps (sightline.focus_clamp)
    cam["fm_look_at"] = look
    cam["fm_scene"] = scene
    cam["fm_start_position"] = list(sp)
    cam["fm_end_position"] = list(ep)
    fr = shot["frames"]
    drop_marker(sid)
    m = bpy.context.scene.timeline_markers.new("fm:" + sid, frame=int(fr["start"]))
    m.camera = cam


def build_unit(uid, spec, film, shots, index):
    kind, _, name = uid.partition(":")
    col = U.get_collection(coll_name(uid))
    if kind == "set":
        build_set(name, film, col)
    elif kind == "char":
        build_char(name, film, col, index)
    elif kind == "prop":
        build_prop(name, film, col, index)
    elif kind == "shot":
        build_shot(name, film, shots[name], col)
    stamp(col, uid, spec)


# ------------------------------------------------------------------ reconcile
def reconcile(film, shots):
    specs = R.unit_specs(film, shots)
    desired = {u: s["hash"] for u, s in specs.items()}
    have = existing_units()
    p = R.plan(desired, have)
    for uid in p["remove"] + p["changed"]:            # rebuild = remove then build fresh
        c = bpy.data.collections.get(coll_name(uid))
        if c is not None:
            purge_unit(c)
        if uid.startswith("shot:"):
            drop_marker(uid[5:])
    for m in [m for m in bpy.context.scene.timeline_markers if m.name.startswith("fm:") and m.name[3:] not in shots]:
        bpy.context.scene.timeline_markers.remove(m)
    counters = {}
    for uid in desired:
        kind = uid.partition(":")[0]
        idx = counters.get(kind, 0)
        counters[kind] = idx + 1
        if uid in p["build"]:
            build_unit(uid, specs[uid], film, shots, idx)
    # stray fm_owner objects that belong to no live unit (left by removed collections); foreign objects are never touched
    live = {o for c in bpy.data.collections if c.get("fm_owner") == U.OWNER and c.get("fm_id") in desired for o in c.all_objects}
    stray = [o for o in bpy.data.objects if o.get("fm_owner") == U.OWNER and o not in live]
    n_stray = remove_owned(stray)
    for m in [m for m in bpy.data.materials if m.get("fm_owner") == U.OWNER and m.users == 0]:
        bpy.data.materials.remove(m)
    first = next((s for s in film["shots"] if s in shots), None)
    if first and bpy.data.objects.get("cam." + first):
        bpy.context.scene.camera = bpy.data.objects["cam." + first]
    return R.report(p, {"stray_objects_removed": n_stray})


def main(argv):
    resolved_dir, blend = argv[0], argv[1]
    report_path = argv[2] if len(argv) > 2 else None
    film, shots = load(resolved_dir)
    existed = os.path.exists(blend)
    if existed:
        bpy.ops.wm.open_mainfile(filepath=blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render(film, 1280)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 0, max(int(film.get("total_frames", 1)) - 1, 0)
    rep = reconcile(film, shots)
    rep.update({"blend": blend, "opened_existing": existed, "builder": BUILDER_VERSION, "bpy": bpy.app.version_string,
                "objects": sum(1 for o in bpy.data.objects if o.get("fm_owner") == U.OWNER),
                "markers": len([m for m in sc.timeline_markers if m.name.startswith("fm:")])})
    os.makedirs(os.path.dirname(os.path.abspath(blend)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=1)
    print("FM_REPORT " + json.dumps(rep), flush=True)
    print("FM_OK build", flush=True)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
