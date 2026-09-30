"""Render every FILM_MAKER pose preset (poses.POSES) into a labelled contact sheet with the cloud bpy module.

    python scripts/pose_sheet.py [--project last_signal] [--out DIR] [--sheet FILE] [--size 420] [--only ren/car_sag,...]

One worker process per figure (ren, hana), like blender/run_cloud.py; each renders a side view and a three-quarter
view of every preset against simple proxies of the props the pose touches (seat, wheel, glovebox, kerb, crank,
desk), then this script stitches the tiles with PIL. Run it in the background (nohup) when the 2-minute tool limit
matters: the renders take about a minute.
"""
import argparse
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

FAMILY = {  # pose ref -> the context family whose props are drawn
    "car_": "car", "scramble_out": "door", "lunge": "door", "kerb_": "kerb", "desk_": "desk",
}


def family(ref):
    for k, v in FAMILY.items():
        if ref.startswith(k):
            return v
    return "ground"


# ----------------------------------------------------------------------------------- worker (inside bpy)
def worker(cid, out, size, project, only):
    import bpy
    from mathutils import Vector
    from fm_blender import characters as CH
    from fm_blender import poses as PS
    from fm_blender import util as U

    film = json.load(open(os.path.join(ROOT, "projects", project, "09_resolved", "film.json"), encoding="utf-8"))
    canon = film["canon"]
    props = dict(canon[f"characters.{cid}.proportions"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.view_settings.view_transform = "Standard"
    try:
        sc.eevee.taa_render_samples = 8
    except Exception:  # noqa: BLE001
        pass
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.87, 0.9, 1)
    sc.world = w
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    sc.collection.objects.link(cam)
    sc.camera = cam
    fwd = Vector((0, 1, 0))  # the figure faces +y: local (fw, rt, up) = world (y, x, z)

    def flat(hexs):
        return U.toon({"hex": hexs, "linear": U.lin(hexs)})

    grey, dark, tint, warm = flat("#9A9DA6"), flat("#4C4F58"), flat("#C7B58F"), flat("#E0A050")
    W = lambda p: Vector((p[1], p[0], p[2]))  # noqa: E731  local (fw, rt, up) tuple -> world

    def proxies(col, fam, ref, j, ctx):
        if fam == "car":
            c = ctx["car"]
            z = c["seat_z"]
            U.box("seat_base", (0.46, 0.5, 0.15), (0, 0.0, z - 0.08), col, grey)
            b = U.box("seat_back", (0.46, 0.1, 0.62), (0, -0.30, z + 0.26), col, grey)
            b.rotation_euler = (math.radians(-20), 0, 0)
            cen = Vector(c["wheel_center"])
            U.cyl("wheel", c["wheel_radius"], 0.03, W(cen), col, dark, rot=(math.radians(60), 0, 0))
            U.box("roof_line", (1.4, 1.6, 0.02), (0, 0.5, c["roof_z"] - 0.01), col, tint)
            U.box("latch", (0.05, 0.05, 0.03), W(c["glovebox_latch"]), col, warm)
            U.box("glovebox", (0.32, 0.2, 0.15), W((c["glovebox_latch"][0] + 0.1, c["glovebox_latch"][1], c["glovebox_latch"][2])), col, dark)
            U.box("mirror", (0.22, 0.03, 0.06), W(c["mirror"]), col, tint)
            U.box("floor", (1.4, 2.0, 0.05), (0, 0.5, 0.06), col, flat("#6A5A48"))
            U.box("door_left", (0.03, 1.6, 0.6), (-0.7, 0.5, 0.65), col, tint)
        elif fam == "door":
            c = ctx["door"]
            U.box("seat_edge", (0.5, 0.2, 0.12), W((c["seat_edge"][0] + 0.05, 0.0, c["seat_edge"][2] - 0.06)), col, grey)
            U.box("latch", (0.05, 0.05, 0.03), W(c["latch"]), col, warm)
            U.box("roof_line", (1.6, 1.4, 0.02), (0, 1.0, c["roof_z"] - 0.01), col, tint)
            U.box("sill", (0.05, 0.6, 0.05), W(c["sill"]), col, dark)
        elif fam == "kerb":
            k = ctx["kerb"]
            U.box("pavement", (2.0, 1.6, k["seat_z"]), (0, 0.9, k["seat_z"] / 2), col, grey)
            U.box("car_rear", (1.6, 1.4, 0.9), (0, -1.12, 0.55), col, tint)
            if ref.startswith("kerb_crank") or "crank_handle" in j:
                cc = Vector(k["crank_center"])
                U.box("crank_body", (0.065, 0.13, 0.042), W(cc), col, flat("#D6C592"))
                sp = cc + Vector(k["crank_spindle"])
                ang = j.get("crank_angle", 0.0)
                tip = sp + Vector((math.sin(ang), 0, math.cos(ang))) * 0.085
                U.between("crank_arm", W(sp), W(tip), 0.006, col, flat("#B8A878"))
                U.sphere("crank_knob", 0.012, W(tip), col, flat("#B8A878"))
        elif fam == "desk":
            d = ctx["desk"]
            U.box("desk_top", (1.1, 0.55, 0.04), (0, 0.30 + 0.275, d["desk_z"] - 0.02), col, tint)
            U.box("chair_seat", (0.42, 0.42, 0.04), (0, 0.0, d["seat_z"] - 0.02), col, grey)
            U.box("chair_back", (0.42, 0.04, 0.45), (0, -0.21, d["seat_z"] + 0.22), col, grey)
            U.box("sketchbook", (0.3, 0.22, 0.02), W((d["sketchbook"][0], d["sketchbook"][1] + 0.05, d["desk_z"] + 0.01)), col, flat("#F1EBDD"))
            U.box("phone", (0.071, 0.147, 0.008), W((d["phone"][0], d["phone"][1], d["desk_z"] + 0.004)), col, dark)
        U.box("ground", (3.0, 3.6, 0.02), (0, 0.4, -0.01), col, flat("#B8B3A6"))
        if j.get("phone") is not None:
            U.box("phone_held", (0.075, 0.008, 0.15), W(j["phone"]), col, flat("#101418"))

    refs = [r for c_, r in PS.POSES if c_ == cid and (not only or f"{cid}/{r}" in only)]
    report = {}
    for ref in refs:
        j = PS.pose(cid, ref, props)
        fam = family(ref)
        ctx = PS.merged_ctx()
        report[ref] = {"crown": round(PS.crown_z(j), 3), "lengths": PS.check_lengths(j, props), "contacts": PS.check_contacts(j)}
        for view, loc, tgt, scale in (("side", (6.0, 0.4, 1.0), (0, 0.4, 0.85), 2.3), ("front", (3.6, 4.6, 1.7), (0, 0.4, 0.8), 2.3)):
            col = bpy.data.collections.new("t")
            sc.collection.children.link(col)
            props2 = dict(props)
            if ref == "desk_headphones_off":
                props2["headphones_state"] = "on"
            elif ref == "desk_phone_low":
                props2["headphones_state"] = "down"
            CH.figure(col, cid, canon, props2, Vector((0, 0, 0)), fwd, joints=j)
            proxies(col, fam, ref, j, ctx)
            cam.location = loc
            cam.data.ortho_scale = scale
            d = Vector(tgt) - Vector(loc)
            cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(out, f"{cid}__{ref}__{view}.png")
            bpy.ops.render.render(write_still=True)
            U.remove_collection(col)
        print("FM_POSE", cid, ref, flush=True)
    json.dump(report, open(os.path.join(out, f"{cid}_report.json"), "w"), indent=1)
    print("FM_OK", cid, flush=True)


# ----------------------------------------------------------------------------------- orchestrator
def sheet(out, path, size, only):
    from PIL import Image, ImageDraw
    tiles = []
    for cid in ("ren", "hana"):
        rp = os.path.join(out, f"{cid}_report.json")
        if not os.path.exists(rp):
            continue
        rep = json.load(open(rp))
        for ref, info in rep.items():
            tiles.append((cid, ref, info))
    cols, lab = 4, 34
    rows = (len(tiles) + 1) // 2  # two tiles (side, front) per pose, two poses per row
    cw, ch = size, size + lab
    im = Image.new("RGB", (cols * cw, ((len(tiles) + 1) // 2) * ch), (30, 30, 34))
    dr = ImageDraw.Draw(im)
    for i, (cid, ref, info) in enumerate(tiles):
        x0, y0 = (i % 2) * 2 * cw, (i // 2) * ch
        for k, view in enumerate(("side", "front")):
            p = os.path.join(out, f"{cid}__{ref}__{view}.png")
            if os.path.exists(p):
                im.paste(Image.open(p).convert("RGB"), (x0 + k * cw, y0 + lab))
        flag = "  ".join(info["lengths"] + info["contacts"]) or "ok"
        dr.text((x0 + 6, y0 + 4), f"{cid}/{ref}   crown {info['crown']:.2f} m", fill=(255, 235, 120))
        dr.text((x0 + 6, y0 + 18), flag[:110], fill=(190, 255, 190) if flag == "ok" else (255, 150, 130))
    im.save(path)
    return path, len(tiles)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="last_signal")
    ap.add_argument("--out", default=os.path.join(ROOT, ".fm_local", "pose_sheet"))
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--size", type=int, default=420)
    ap.add_argument("--only", default="")
    ap.add_argument("--worker", default=None)
    a = ap.parse_args()
    only = {x for x in a.only.split(",") if x}
    os.makedirs(a.out, exist_ok=True)
    if a.worker:
        worker(a.worker, a.out, a.size, a.project, only)
        return
    procs = []
    for cid in ("ren", "hana"):
        cmd = [sys.executable, os.path.abspath(__file__), "--worker", cid, "--out", a.out, "--size", str(a.size),
               "--project", a.project, "--only", a.only]
        procs.append((cid, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
    bad = []
    for cid, p in procs:
        txt = p.communicate()[0]
        if "FM_OK" not in txt:
            bad.append(cid)
            print(txt[-1500:])
    path, n = sheet(a.out, a.sheet or os.path.join(a.out, "pose_sheet.png"), a.size, only)
    print("poses", n, "failed", bad, "sheet", path)


if __name__ == "__main__":
    main()
