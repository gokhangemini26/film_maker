"""Per-frame animation for the resolved shots (M6-lite): frame_state() and render_frames().

Part 1 (pure python, mathutils only, no scene): `frame_state(shot, motion, ui_timeline, f)` returns everything a
frame needs, deterministically: every character's joint dict (blended between the keyed presets with the key's
ease, run / scramble / crank gaits, head aimed at the look target, breath, face), the prop states (passenger
door angle, glovebox lid amount, crank charger place / arm / pip, phone attach, headphones, pencil, car body
offsets, shop lights, mirror), the phone screen state from the resolved `ui_timeline`, and the camera position.

Part 2 (needs bpy): `render_frames()` builds the shot ONCE with the existing static assembly
(preview.render_shot), then re-poses the figures, props, phone, lights and camera per frame and renders PNGs.
No keyframes: each frame is a pure function of (shot, f).

Frame selection and contact strips live in framesel.py (no bpy, so `fm` can use them).

Conventions (see poses.py): a joint dict is in a figure-local frame (fw, rt, up); fw = the figure's facing,
rt = its right, up = absolute z for the car / kerb / desk families (base z = 0). Every character has a ROOT frame
(base, facing) per frame (its home place, or the path for the gaits); the poses of other families (car, kerb,
door) live in their own constant frames and are converted through world space before they are blended.
"""
from __future__ import annotations

import math
import os
import re

try:
    from mathutils import Vector
except ImportError:  # the standalone python: importing bpy registers the mathutils module
    import bpy  # noqa: F401
    from mathutils import Vector

from . import poses as PS
from .framesel import contact_strip, parse_frames, select_frames  # noqa: F401  (pure helpers, re-exported)

LOOK_BLEND_F = 4          # frames the head takes to turn to a new look target
SHOP_ORIGIN = Vector((100.0, 0.0, 0.0))   # same values as sets.py (kept here so this part imports without the set builders)
ROOM_ORIGIN = Vector((200.0, 0.0, 0.0))
STREET_SCENES = {"SC01", "SC02", "SC04", "SC06"}

# car body offsets: amplitude in metres, per preset (the vocabulary leaves them to the builder)
CAR_BODY = {
    "still": None,
    "idle_tremble": dict(amp=0.0008, period_f=3.0),
    "cough": dict(amp=0.006, dur_f=6),
    "sigh_sink": dict(amp=0.018, dur_f=14),
    "stall_shudder": dict(amp=0.010, dur_f=10),
    "sway_1cm": dict(amp=0.010, dur_f=16),
}
DOOR_DEG = {"closed": 0.0, "open_60": 60.0}
SHOP_DOOR_DEG = {"closed": 0.0, "open_70": 70.0}
BREATH_M = {"in_slow": 0.010, "out_slow": 0.0, "out_long": -0.025}
FALLBACK_FACE = "neutral"
TWO_PI = 2 * math.pi


# ----------------------------------------------------------------------------------- small helpers
def _ease(name, t):
    return PS.ease_value(name or "ease_in_out", t)


def _lerp(a, b, u):
    return a + (b - a) * u


def _clip01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def _last(keys, f):
    """(index, key) of the last key with key['f'] <= f; (-1, None) before the first."""
    idx = -1
    for i, k in enumerate(keys):
        if k["f"] <= f:
            idx = i
        else:
            break
    return idx, (keys[idx] if idx >= 0 else None)


def _norm(v, fallback=(0.0, 1.0, 0.0)):
    v = Vector(v)
    return v.normalized() if v.length > 1e-9 else Vector(fallback)


def _yaw(facing):
    return math.atan2(facing.y, facing.x)


def _dir(yaw):
    return Vector((math.cos(yaw), math.sin(yaw), 0.0))


def _angle_lerp(a, b, u):
    d = (b - a + math.pi) % TWO_PI - math.pi
    return a + d * u


# ----------------------------------------------------------------------------------- generic track values
def _segments(keys, field):
    """[(f0, dur, ease, target)] for the keys of a prop track that set `field`."""
    return [(k["f"], k.get("dur_f"), k.get("ease"), k[field]) for k in keys if k.get(field) is not None]


def _seg_value(segs, f, default, mix):
    """Value of a segment list at frame f. `mix(a, b, u)` blends two targets; the change of a key that carries
    dur_f occupies frames f0..f0+dur-1 (the last one is complete), no dur_f switches at f0."""
    if not segs:
        return default
    if f < segs[0][0]:
        return segs[0][3]
    i = max(j for j, s in enumerate(segs) if s[0] <= f)
    f0, dur, ease, cur = segs[i]
    if i == 0 or not dur:
        return cur
    t = _clip01((f - f0 + 1) / float(dur))
    return mix(segs[i - 1][3], cur, _ease(ease or "ease_in_out", t))


def _num(keys, field, f, default=0.0):
    return _seg_value(_segments(keys, field), f, default, _lerp)


def _enum(keys, field, f, default=None):
    """(from, to, t) of an enumerated field at frame f; t is the eased change weight (1 once complete)."""
    segs = _segments(keys, field)
    if not segs:
        return default, default, 1.0
    if f < segs[0][0]:
        return segs[0][3], segs[0][3], 1.0
    i = max(j for j, s in enumerate(segs) if s[0] <= f)
    f0, dur, ease, cur = segs[i]
    prev = segs[i - 1][3] if i > 0 else cur
    if i == 0 or not dur or prev == cur:
        return cur, cur, 1.0
    t = _clip01((f - f0 + 1) / float(dur))
    return prev, cur, _ease(ease or "ease_in_out", t)


# ----------------------------------------------------------------------------------- stage (geometry of the shot)
def unit_offset(scene):
    return SHOP_ORIGIN if scene == "SC03" else (ROOM_ORIGIN if scene == "SC05" else Vector((0, 0, 0)))


def _parse_facing(text, pos, cam, street, scene):
    from .preview import parse_facing   # the static assembly's own rule (kept in one place)
    return parse_facing(text, pos, cam, street, scene)


def _car_anchors(canon):
    """World points of the car interior, computed the way sets.build_car places them."""
    s, c = canon.get("world.sets.street"), canon.get("world.sets.ren_car")
    if not s or not c:
        return None
    x0, x1 = s["car_body_x"]
    y0, y1 = s["car_body_y"]
    W = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sill, H = c["sill_height_m"], c["height_m"]
    seat_z = c["seat_height_m"]
    fy = cy + 0.15
    drv_x, pas_x = x1 - W * 0.27, x0 + W * 0.27
    gb_w, gb_h = c["glovebox"]["opening_m"]
    gb_y, gb_z = y1 - 0.72, sill + 0.4
    return {
        "drv_x": drv_x, "pas_x": pas_x, "seat_z": seat_z, "roof_z": H, "sill": sill,
        "wheel": Vector((drv_x, y1 - 0.85, sill + 0.62)),
        "latch": Vector((pas_x, gb_y - 0.121, gb_z + gb_h / 2 - 0.03)),
        "glovebox_front": Vector((pas_x, gb_y - 0.105, gb_z)),
        "console_top": Vector((cx, fy + 0.25, seat_z + 0.16)),
        "mirror": Vector((cx + 0.15, y1 - 0.95, H - 0.28)),
        "dash": Vector((cx, y1 - 0.55, sill + 0.6)),
        "adapter": Vector((cx, fy + 0.25, seat_z + 0.17)),
        "x0": x0, "x1": x1, "y0": y0, "y1": y1,
    }


class Stage:
    """Where things are for one shot: per-character home frames, the constant pose-family frames (car, kerb, door),
    the merged poses context, world anchors for the look targets. Pure; `canon` is optional (defaults otherwise)."""

    CAR_BASE_Y = 0.05        # driver pelvis y (the set's wheel is 0.65 m ahead of it; sets.py puts the seat further back)

    def __init__(self, shot, canon=None, motion=None):
        self.shot = shot
        self.motion = motion if motion is not None else (shot.get("motion") or {})
        self.canon = canon or {}
        self.sid = shot["shot_id"]
        self.scene = shot["scene_id"]
        self.n = int(self.sid.split("SH")[1])
        self.off = unit_offset(self.scene)
        self.street = self.scene in STREET_SCENES
        cam = shot.get("camera") or {}
        sp = Vector(cam.get("start_position") or (0, -5, 1.5))
        ep = Vector(cam.get("end_position") or cam.get("start_position") or (0, -5, 1.5))
        self.cam_start, self.cam_end = sp + self.off, ep + self.off
        self.cpos = (sp + ep) / 2 + self.off
        street = self.canon.get("world.sets.street") or {}
        self.pavement_z = street.get("pavement_z", 0.12)
        self.south_x = street.get("south_pavement_x", [-1.8, 0.0])
        self.north_x = street.get("north_pavement_x", [5.5, 7.3])
        self.car = _car_anchors(self.canon)
        self.props = {}
        self.home = {}
        for ch in shot.get("characters", []):
            cid = ch["id"]
            self.props[cid] = dict((ch.get("canon") or {}).get("proportions") or {"height_m": 1.7})
            pos = Vector(ch.get("position") or (0, 0, 0)) + self.off
            fac = _parse_facing(ch.get("facing", "camera"), pos, self.cpos, self.street, self.scene)
            self.home[cid] = (Vector((pos.x, pos.y, 0.0)), fac)
        self.frames = {}
        self.ctx = {}
        self._build_frames()

    # ---- ground
    def ground_z(self, p):
        if not self.street:
            return self.off.z
        x = p.x
        if self.south_x[0] <= x <= self.south_x[1] or self.north_x[0] <= x <= self.north_x[1]:
            return self.pavement_z
        return 0.0

    def _build_frames(self):
        ren = self.home.get("ren")
        a = self.car
        # car: the driver's frame (pelvis on the seat, facing west = +y)
        car_base = Vector((a["drv_x"] if a else 1.28, self.CAR_BASE_Y, 0.0))
        self.frames["car"] = (car_base, Vector((0, 1, 0)))
        # kerb: sitting on the south pavement edge with the car behind him (facing south = -x)
        kb = ren[0] if ren else Vector((-0.1, -1.0, 0.0))
        self.frames["kerb"] = (Vector((kb.x, kb.y, 0.0)), Vector((-1, 0, 0)))
        # door: beside the passenger door facing into the car. Shots with a path start at its first point;
        # the lunge (no path) kneels where the glovebox latch is 1.02 m ahead and 0.10 m to the right
        path = self._path("ren")
        if path:
            base = Vector((path[0][1], path[0][2], 0.0))
            fac = Vector((1, 0, 0))
        else:
            latch = a["latch"] if a else Vector((0.6, 0.71, 0.77))
            fac = _norm((0.84, 0.55, 0.0))
            r = Vector((fac.y, -fac.x, 0))
            base = latch - fac * 1.02 - r * 0.10
            base = Vector((base.x, base.y, 0.0))
        base.z = self.ground_z(base)
        self.frames["door"] = (base, fac)
        # ctx: the poses context, expressed in the frame each family uses
        ctx = {}
        cb, cf = self.frames["car"]
        if a:
            L = lambda p: PS.to_local(p, cb, cf)   # noqa: E731
            wl = L(a["wheel"])
            ctx["car"] = {"seat_z": a["seat_z"], "roof_z": a["roof_z"], "wheel_center": tuple(wl),
                          "mirror": tuple(L(a["mirror"])), "glovebox_latch": tuple(L(a["latch"])),
                          "console_top": tuple(L(a["console_top"]))}
            db, df = self.frames["door"]
            ctx["door"] = {"latch": tuple(PS.to_local(a["latch"], db, df)), "roof_z": a["roof_z"]}
        self.ctx = PS.merged_ctx(ctx)

    # ---- paths
    def _path(self, cid):
        mv = ((self.motion or {}).get("characters", {}).get(cid) or {}).get("move") or {}
        return [(p["f"], p["x"], p["y"]) for p in mv.get("path") or []]

    def root_at(self, cid, path, f, n):
        """(base, facing) of the character's root frame at frame f."""
        base, fac = self.home[cid]
        if len(path) < 2:
            return base, fac
        b = self._path_pos(path, f)
        b = Vector((b[0], b[1], 0.0)) + Vector((self.off.x, self.off.y, 0.0))
        b.z = self.ground_z(b)
        f0, f1 = max(0, f - 3), min(n - 1, f + 3)
        a, c = self._path_pos(path, f0), self._path_pos(path, f1)
        d = Vector((c[0] - a[0], c[1] - a[1], 0.0))
        if d.length < 0.02:                       # not moving: use the nearest moving direction of the path
            best = None
            for g in range(0, n):
                a2, c2 = self._path_pos(path, max(0, g - 3)), self._path_pos(path, min(n - 1, g + 3))
                dd = Vector((c2[0] - a2[0], c2[1] - a2[1], 0.0))
                if dd.length >= 0.02 and (best is None or abs(g - f) < best[0]):
                    best = (abs(g - f), dd)
            d = best[1] if best else fac
        return b, _norm(d)

    @staticmethod
    def _path_pos(path, f):
        if f <= path[0][0]:
            return path[0][1], path[0][2]
        for a, b in zip(path, path[1:]):
            if f <= b[0]:
                u = (f - a[0]) / float(b[0] - a[0])
                return _lerp(a[1], b[1], u), _lerp(a[2], b[2], u)
        return path[-1][1], path[-1][2]

    # ---- anchors for look targets (world)
    def anchor(self, name):
        a, off = self.car, self.off
        table = {
            "mirror": a and a["mirror"], "dash": a and a["dash"], "glovebox": a and a["latch"],
            "shop_door": Vector((-1.8, 12.0, 1.1)),
            "socket": SHOP_ORIGIN + Vector((4.25, 8.9, 0.4)),
            "camera": self.cpos,
        }
        v = table.get(name)
        if v is None and name == "sketchbook":
            d = self.ctx["desk"]["sketchbook"]
            return PS.to_world(Vector(d), *self.home.get("hana", (Vector(off), Vector((0, 1, 0)))))
        return v


# ----------------------------------------------------------------------------------- frames of reference
def _to_frame(j, src, dst):
    """Joint dict `j` (local to frame `src` = (base, facing)) re-expressed in frame `dst`. Positions go through world
    space; pole directions and head yaw only rotate."""
    sb, sf = src
    db, df = dst
    if (sb - db).length < 1e-9 and (sf - df).length < 1e-9:
        return PS._copy(j)
    W = lambda v: PS.to_local(PS.to_world(Vector(v), sb, sf), db, df)              # noqa: E731
    Dv = lambda v: PS.to_local(PS.to_world(Vector(v), Vector((0, 0, 0)), sf), Vector((0, 0, 0)), df)  # noqa: E731
    o = PS._copy(j)
    for k in ("pelvis", "hipL", "hipR", "chest", "neck", "head", "shL", "shR", "handL", "handR", "phone", "crank_handle"):
        if isinstance(o.get(k), Vector):
            o[k] = W(o[k])
    for k in ("knee", "foot", "elbow"):
        o[k] = [W(v) for v in o[k]]
    for k in ("knee_pole", "elbow_pole"):
        if k in o:
            o[k] = [Dv(v) for v in o[k]]
    o["head_yaw"] = j["head_yaw"] + _yaw(df) - _yaw(sf)
    return o


# ----------------------------------------------------------------------------------- characters
def _family(ref):
    if ref.startswith("car_"):
        return "car"
    if ref.startswith("kerb_"):
        return "kerb"
    if ref.startswith("lunge_") or ref == "scramble_out":
        return "door"
    if ref.startswith("desk_"):
        return "home"
    return "root"


def _home_frame_name(pose_keys):
    """Which constant frame is a character's root when it has no path: the family of its first pose."""
    fam = _family(pose_keys[0]["ref"]) if pose_keys else "home"
    return fam if fam in ("car", "kerb") else "home"


def _pose_joints(cid, ref, f, stage, move, first_step_f):
    """Joints of preset `ref` at frame f in ITS family frame. The gait poses (run_phone_out, crank hold) are gait
    frames, not still poses."""
    props, ctx = stage.props[cid], stage.ctx
    gait = move.get("gait", "none")
    if ref == "run_phone_out" and gait in ("run_phone_out", "scramble"):
        return PS.gait_run_phone_out(f, props, ctx, speed_mps=move.get("speed_mps") or 4.2, first_step_f=first_step_f)
    if ref == "kerb_crank_hold" and gait == "crank_turn" and move.get("first_top_f") is not None:
        return PS.gait_crank_turn(f, move["first_top_f"], props, ctx, start_f=move.get("start_f"), stop_f=move.get("stop_f"))
    return PS.pose(cid, ref, props, ctx)


def _char_frame(stage, cid, fam, root, f):
    if fam == "root":
        return root
    if fam == "home":
        return stage.home[cid]
    return stage.frames[fam]


def _pose_track(cid, mc, stage, f, n):
    """(joints in the output frame, output frame, info) for character cid at frame f."""
    keys = mc.get("pose") or []
    move = mc.get("move") or {}
    path = stage._path(cid)
    props = stage.props[cid]
    first_step = next((k["f"] for k in keys if k["ref"] == "run_phone_out"), 0)
    if path and len(path) >= 2:
        root = stage.root_at(cid, path, f, n)
    else:
        fam = _home_frame_name(keys)
        root = stage.frames[fam] if fam in stage.frames and fam != "home" else stage.home[cid]
    if not keys:
        j = PS.POSES[(cid, sorted(r for c, r in PS.POSES if c == cid)[0])](props, stage.ctx)
        return j, root, {"from": None, "to": None, "t": 1.0}
    i, k = _last(keys, f)
    i = max(i, 0)
    k = keys[i]
    prev = keys[i - 1] if i > 0 else None
    bf = k.get("blend_f") or 0
    if prev is not None and bf and f < k["f"] + bf:
        t = _clip01((f - k["f"]) / float(bf))
        ease = k.get("ease", "ease_in_out")
        A, B = prev["ref"], k["ref"]
    else:
        A = B = k["ref"]
        t, ease = 1.0, "hold"
    ja = _pose_joints(cid, A, f, stage, move, first_step)
    fa = _char_frame(stage, cid, _family(A), root, f)
    if A == B:
        return ja, fa, {"from": A, "to": B, "t": 1.0}
    jb = _pose_joints(cid, B, f, stage, move, first_step)
    fb = _char_frame(stage, cid, _family(B), root, f)
    u = PS.ease_value(ease, t)
    out_base = fa[0] * (1 - u) + fb[0] * u
    out_fac = _dir(_angle_lerp(_yaw(fa[1]), _yaw(fb[1]), u))
    out = (out_base, out_fac)
    ja2, jb2 = _to_frame(ja, fa, out), _to_frame(jb, fb, out)
    return PS.blend(ja2, jb2, t, ease), out, {"from": A, "to": B, "t": u}


# ---- look, face, breath
def _look_world(stage, cid, name, j, frame, props_state):
    """World point for a look target, or None for 'nothing to aim at'."""
    base, fac = frame
    w = lambda v: PS.to_world(Vector(v), base, fac)   # noqa: E731
    head_w = w(j["head"])
    if name == "phone":
        ph = j.get("phone")
        return w(ph) if ph is not None else w((j["handL"] + j["handR"]) / 2)
    if name == "crank":
        return props_state["crank_charger"]["world"] if props_state.get("crank_charger") else None
    if name == "lap":
        return w(j["pelvis"] + Vector((0.28, 0, -0.05)))
    if name == "road_ahead":
        return head_w + fac * 10.0 - Vector((0, 0, 0.3))
    if name == "wall_left":
        return head_w + Vector((fac.y, -fac.x, 0)) * -1.6 + fac * 0.3
    if name == "wall_right":
        return head_w + Vector((fac.y, -fac.x, 0)) * 1.6 + fac * 0.3
    if name == "ceiling":
        return head_w + Vector((0, 0, 2.0)) + fac * 0.4
    if name == "sky":
        return head_w + Vector((0, 10.0, 4.0))
    if name in ("off_frame", "closed"):
        return None
    return stage.anchor(name)


def _aim(j, target_local):
    y, p = PS.look_angles(j["head"], target_local)
    return (max(-math.radians(75), min(math.radians(75), y)), max(-math.radians(50), min(math.radians(50), p)))


def _apply_look(stage, cid, mc, j, frame, f, props_state):
    keys = mc.get("look") or []
    i, k = _last(keys, f)
    if k is None:
        return j, None, False
    tgt = k["target"]
    closed = tgt == "closed"

    def angles(name):
        w = _look_world(stage, cid, name, j, frame, props_state)
        if w is None:
            return None
        return _aim(j, PS.to_local(w, *frame))

    cur = angles(tgt)
    if cur is None:
        return j, tgt, closed
    if i > 0 and f < k["f"] + LOOK_BLEND_F:
        prev = angles(keys[i - 1]["target"])
        if prev is not None:
            u = _ease("ease_in_out", (f - k["f"] + 1) / float(LOOK_BLEND_F))
            cur = (_angle_lerp(prev[0], cur[0], u), _lerp(prev[1], cur[1], u))
    return PS.set_head(j, yaw=cur[0], pitch=cur[1]), tgt, closed


def _face_at(mc, f):
    keys = mc.get("face") or []
    i, k = _last(keys, f)
    ref = k["ref"] if k else FALLBACK_FACE
    return ref if ref in PS.FACE_SHAPES else FALLBACK_FACE


def _breath_at(mc, f, crank_angle):
    """Shoulder / chest lift in metres from the breath track."""
    keys = mc.get("breath") or []
    level, cur_f, cur_k = 0.0, None, None
    lvl_before = 0.0
    for k in keys:
        if k["f"] > f:
            break
        lvl_before = level
        cur_f, cur_k = k["f"], k
        if k["ref"] != "crank_locked":
            level = BREATH_M.get(k["ref"], level)
    if cur_k is None:
        return 0.0
    ref, dur = cur_k["ref"], cur_k.get("dur_f") or 12
    if ref == "crank_locked":
        end = cur_f + (cur_k.get("dur_f") or 10 ** 6)
        if f >= end or crank_angle is None:
            return 0.0
        return 0.005 * math.cos(crank_angle)
    if ref == "hold":
        return lvl_before
    t = _clip01((f - cur_f + 1) / float(dur))
    return _lerp(lvl_before, level, _ease("ease_in_out", t))


def _lift(j, dz):
    """Raise shoulders, chest, neck and head by dz (breath); hands stay, the arms are re-solved."""
    if abs(dz) < 1e-9:
        return j
    o = PS._copy(j)
    up = Vector((0, 0, dz))
    for k in ("chest", "neck", "head", "shL", "shR"):
        o[k] = o[k] + up
    d = o["_dims"]
    el = []
    for s, h, pole in zip((o["shL"], o["shR"]), (o["handL"], o["handR"]), o["elbow_pole"]):
        e, h2, _ = PS._ik2(s, h, d["up"], d["fore"], pole)
        el.append(e)
    o["elbow"] = el
    return o


# ----------------------------------------------------------------------------------- props
def _car_body_offset(keys, f):
    """(dx, dy, dz) metres of the car body at frame f from the car_body preset track."""
    i, k = _last(keys, f)
    if k is None or k.get("state") in (None, "still"):
        return (0.0, 0.0, 0.0)
    spec = CAR_BODY[k["state"]]
    t0 = f - k["f"]
    if k["state"] == "idle_tremble":
        return (0.0, 0.0, spec["amp"] * math.sin(TWO_PI * t0 / spec["period_f"]))
    dur = k.get("dur_f") or spec["dur_f"]
    if t0 >= dur:
        return (0.0, 0.0, 0.0)
    t = t0 / float(dur)
    env = 1.0 - t
    if k["state"] == "cough":
        return (0.0, 0.0, -spec["amp"] * math.sin(math.pi * t) * (1 if t0 % 2 == 0 else 0.5))
    if k["state"] == "sigh_sink":
        return (0.0, 0.0, -spec["amp"] * math.sin(math.pi * t))
    if k["state"] == "stall_shudder":
        return (0.0, 0.0, spec["amp"] * env * math.sin(TWO_PI * t0 / 2.0))
    return (0.0, spec["amp"] * env * math.sin(TWO_PI * t), 0.0)     # sway_1cm


def _crank_place(state, j, frame, stage):
    """World position of the crank body for the current loc (blended from -> to)."""
    base, fac = frame
    w = lambda v: PS.to_world(Vector(v), base, fac)   # noqa: E731
    car = stage.car
    kerb_c = lambda: PS.to_world(Vector(stage.ctx["kerb"]["crank_center"]), *stage.frames["kerb"])   # noqa: E731

    def loc_pos(loc):
        if loc == "glovebox":
            return car["glovebox_front"] if car else Vector((0.6, 0.72, 0.72))
        if loc == "hand_r":
            return w(j["handR"] + Vector((0.0, 0.0, 0.02)))
        if loc == "hands_both":
            return kerb_c() if "crank_handle" in j else w((j["handL"] + j["handR"]) / 2 + Vector((0.0, 0.0, 0.02)))
        if loc == "knees":
            return w((j["knee"][0] + j["knee"][1]) / 2 + Vector((0.0, 0.0, 0.07)))
        if loc == "thighs":
            return w(j["pelvis"] + Vector((0.26, 0.0, 0.10)))
        if loc == "falling":
            return (loc_pos("glovebox") + loc_pos("thighs")) / 2
        return kerb_c() if "crank_handle" in j else w(j["pelvis"] + Vector((0.16, 0.0, 0.16)))   # lap

    t = state["loc_t"]
    a, b = loc_pos(state["loc_from"]), loc_pos(state["loc_to"])
    return a * (1 - t) + b * t


def _prop_states(shot_motion, f, stage, chars):
    """State of every prop at frame f. Position-dependent parts of the crank are filled in later."""
    props = shot_motion.get("props") or {}
    out = {}
    if "passenger_door" in props:
        ks = props["passenger_door"]
        segs = []
        cur = None
        for k in ks:
            tgt = k.get("swing_deg")
            if tgt is None and k.get("state") is not None:
                tgt = DOOR_DEG[k["state"]]
            if tgt is None:
                continue
            segs.append((k["f"], k.get("dur_f"), k.get("ease"), tgt))
        out["passenger_door"] = {"angle_deg": _seg_value(segs, f, 0.0, _lerp)}
    if "shop_door" in props:
        segs = [(k["f"], k.get("dur_f"), k.get("ease"), SHOP_DOOR_DEG[k["state"]]) for k in props["shop_door"] if k.get("state")]
        out["shop_door"] = {"angle_deg": _seg_value(segs, f, 0.0, _lerp)}
    if "glovebox_lid" in props:
        segs = [(k["f"], k.get("dur_f"), k.get("ease"), 1.0 if k["state"] == "open_down" else 0.0)
                for k in props["glovebox_lid"] if k.get("state")]
        out["glovebox_lid"] = {"open": _seg_value(segs, f, 0.0, _lerp)}
    if "crank_charger" in props:
        ks = props["crank_charger"]
        a, b, t = _enum(ks, "loc", f, "lap")
        arm_segs = [(k["f"], k.get("dur_f"), k.get("ease"), 1.0 if k["arm"] == "unfolded" else 0.0) for k in ks if k.get("arm")]
        out["crank_charger"] = {"loc_from": a, "loc_to": b, "loc_t": t, "loc": b if t >= 0.5 else a,
                                "unfold": _seg_value(arm_segs, f, 0.0, _lerp), "pip": _num(ks, "pip", f, 0.0)}
    for pn in ("phone_ren", "phone_hana"):
        if pn in props:
            a, b, t = _enum(props[pn], "attach", f, None)
            out[pn] = {"attach": b if t >= 0.5 else a}
    if "hana_headphones" in props:
        a, b, t = _enum(props["hana_headphones"], "state", f, "head")
        out["hana_headphones"] = {"from": a, "to": b, "t": t, "state": b if t >= 0.5 else a}
    if "pencil" in props:
        a, b, t = _enum(props["pencil"], "state", f, "held")
        out["pencil"] = {"state": b if t >= 0.5 else a}
    if "car_body" in props:
        out["car_body"] = {"offset": _car_body_offset(props["car_body"], f)}
    if "shop_lights" in props:
        a, b, t = _enum(props["shop_lights"], "state", f, "on")
        out["shop_lights"] = {"on": (b if t >= 0.5 else a) == "on"}
    if "dash_lights_and_adapter_ring" in props:
        a, b, t = _enum(props["dash_lights_and_adapter_ring"], "state", f, "on")
        out["dash_lights_and_adapter_ring"] = {"on": (b if t >= 0.5 else a) == "on"}
    if "rear_view_mirror" in props:
        out["rear_view_mirror"] = {"tilt_deg": _num(props["rear_view_mirror"], "tilt_deg", f, 0.0)}
    return out


# ----------------------------------------------------------------------------------- phone screen
_LINE_CHARS = {1: 21, 2: 12, 3: 9}   # "Are you free tonight?", "Dinner at 8?", "My treat."


def ui_to_st(fr):
    """phone.py's state dict from one frame of the resolved ui_timeline (None when the shot has no screen)."""
    if not fr:
        return None
    screen = fr.get("ui") or "off"
    sl = fr.get("slide")
    if sl and sl.get("progress", 0) >= 0.5:
        screen = sl["to"]
    off = bool(fr.get("screen_off")) or screen == "off"
    st = {
        "phone": fr.get("phone", "ren"), "screen": screen, "screen_off": off,
        "pct": fr.get("pct") if fr.get("pct") is not None else 0, "red": bool(fr.get("red")),
        "bolt": bool(fr.get("bolt")), "digits": True,
        "icon_visible": bool(fr.get("icon_visible", True)),
        "brightness": 0.0 if off else float(fr.get("brightness", 1.0)),
        "frame": fr["f"], "sent": fr.get("sent"),
    }
    if screen == "compose":
        lines = int(fr.get("lines") or 1)
        st["ui"] = f"compose{min(3, max(1, lines))}"
        typed = (fr.get("typed") or {}).get(str(lines))
        if typed is not None:
            st["typing1"] = _clip01(typed / float(_LINE_CHARS[min(3, max(1, lines))]))
        st["heart"] = bool(fr.get("heart"))
        st["send_pressed"] = fr.get("key_pressed") == "send"
    elif screen == "sent":
        st["ui"] = "sent"
        st["sent"] = fr.get("sent") or {"progress": 1.0, "tick": True}
    elif screen == "call":
        st["ui"] = "call"
        st["call"] = fr.get("call_state", "idle")
    elif screen == "map":
        st["ui"] = "map"
    else:
        st["ui"] = None
        st["hana_ui"] = screen
    return st


# ----------------------------------------------------------------------------------- camera
def camera_progress(cam, f):
    """0..1 along the dolly at frame f: speed ramps up over ease_in_f, cruises, ramps down over ease_out_f."""
    if not cam or cam.get("move", "none") == "none":
        return 0.0
    a, b = cam.get("ease_in_f") or (cam["start_f"], cam["start_f"])
    c, d = cam.get("ease_out_f") or (cam["end_f"], cam["end_f"])
    up, down = float(b - a), float(d - c)
    total = 0.5 * up + (c - b) + 0.5 * down
    if total <= 0:
        return 1.0 if f >= cam.get("end_f", 0) else 0.0
    if f <= a:
        s = 0.0
    elif f < b:
        s = (f - a) ** 2 / (2 * up)
    elif f <= c:
        s = 0.5 * up + (f - b)
    elif f < d:
        s = 0.5 * up + (c - b) + (f - c) - (f - c) ** 2 / (2 * down)
    else:
        s = total
    return _clip01(s / total)


def _camera_state(stage, cam_motion, f):
    p = camera_progress(cam_motion, f)
    if cam_motion and cam_motion.get("move", "none") != "none":
        pos = stage.cam_start + (stage.cam_end - stage.cam_start) * p
    else:
        pos = stage.cpos.copy()
    return {"pos": pos, "progress": p, "move": (cam_motion or {}).get("move", "none")}


# ----------------------------------------------------------------------------------- the public function
def frame_state(shot, motion, ui_timeline, f, *, stage=None):
    """Everything one frame of `shot` needs, as a pure function of the resolved shot, its motion block, its ui_timeline
    and the shot-local frame f. `stage` (optional) carries canon-derived geometry; the default has the poses' defaults.

    Returns {"f", "shot_id", "characters": {cid: {...}}, "props": {...}, "ui": phone st | None, "camera": {...}}.
    Per character: frame (base, facing), joints (local to that frame), face, look, eyes_closed, breath_m, pose
    (from, to, eased weight), phone (attach, local position), gait info."""
    stage = stage or Stage(shot, motion=motion)
    if not stage.motion:
        stage.motion = motion
    n = int((shot.get("frames") or {}).get("count") or motion.get("frames") or 1)
    f = int(f)
    if not 0 <= f < n:
        raise ValueError(f"frame {f} is outside the shot ({stage.sid} has {n} frames: 0..{n - 1})")
    props = _prop_states(motion, f, stage, None)
    chars = {}
    for cid, mc in (motion.get("characters") or {}).items():
        if cid not in stage.home:
            continue
        j, frame, pinfo = _pose_track(cid, mc, stage, f, n)
        ang = j.get("crank_angle")
        if cid == "ren" and "crank_charger" in props:
            props["crank_charger"]["world"] = _crank_place(props["crank_charger"], j, frame, stage)
        j, look, closed = _apply_look(stage, cid, mc, j, frame, f, props)
        j = _lift(j, _breath_at(mc, f, ang))
        face = _face_at(mc, f)
        j["face"] = face
        att = (props.get("phone_ren") if cid == "ren" else props.get("phone_hana")) or {}
        chars[cid] = {
            "frame": frame, "joints": j, "face": face, "look": look, "eyes_closed": closed,
            "pose": pinfo, "phone_attach": att.get("attach"), "gait": (mc.get("move") or {}).get("gait", "none"),
            "crank_angle": ang, "handle_top": bool(j.get("handle_top")),
        }
    if "crank_charger" in props and "world" not in props["crank_charger"]:
        props["crank_charger"]["world"] = None
    ui_frames = (ui_timeline or {}).get("frames") if isinstance(ui_timeline, dict) else ui_timeline
    st = ui_to_st(ui_frames[f]) if ui_frames else None
    return {"f": f, "shot_id": stage.sid, "characters": chars, "props": props, "ui": st,
            "camera": _camera_state(stage, motion.get("camera"), f)}


# ----------------------------------------------------------------------------------- prop continuity across shots
PERSISTENT_PROPS = ("passenger_door", "glovebox_lid", "crank_charger", "phone_ren", "phone_hana", "hana_headphones",
                    "pencil", "shop_lights", "dash_lights_and_adapter_ring")


def _end_key(prop, st):
    """One prop-track key (without f) that reproduces state `st` (from _prop_states) - the carry-over between shots."""
    if prop == "passenger_door":
        a = st["angle_deg"]
        return {"state": "closed"} if a < 0.5 else ({"state": "open_60"} if abs(a - 60.0) < 0.5 else {"state": "open_60", "swing_deg": a})
    if prop == "glovebox_lid":
        return {"state": "open_down" if st["open"] >= 0.5 else "closed"}
    if prop == "crank_charger":
        return {"loc": st["loc_to"], "arm": "unfolded" if st["unfold"] >= 0.5 else "folded", "pip": st["pip"]}
    if prop in ("phone_ren", "phone_hana"):
        return {"attach": st["attach"]} if st.get("attach") else None
    if prop in ("hana_headphones", "pencil"):
        return {"state": st["state"]}
    if prop in ("shop_lights", "dash_lights_and_adapter_ring"):
        return {"state": "on" if st["on"] else "off"}
    return None


def end_state(shot, motion=None):
    """State of every persistent prop at the LAST frame of a shot (only the props its motion block animates)."""
    motion = motion or shot.get("motion") or {}
    n = int((shot.get("frames") or {}).get("count") or motion.get("frames") or 1)
    return {p: s for p, s in _prop_states(motion, n - 1, Stage(shot, motion=motion), None).items() if p in PERSISTENT_PROPS}


def start_state(shot, motion=None):
    motion = motion or shot.get("motion") or {}
    return {p: s for p, s in _prop_states(motion, 0, Stage(shot, motion=motion), None).items() if p in PERSISTENT_PROPS}


def with_carried_props(shot, prior_shots):
    """The shot's motion block with a frame-0 key for every persistent prop it does not animate, taken from the end
    state of the latest earlier shot (film order) that does. `prior_shots` = the shots before it, in film order."""
    motion = shot.get("motion") or {}
    props = {p: list(v) for p, v in (motion.get("props") or {}).items()}
    carried = {}
    for prev in prior_shots:
        pm = prev.get("motion") or {}
        if not pm:
            continue
        for p, st in end_state(prev, pm).items():
            carried[p] = st
    for p, st in carried.items():
        if p not in props:
            key = _end_key(p, st)
            if key:
                props[p] = [dict(key, f=0)]
    return dict(motion, props=props)


# ===================================================================================== part 2: rendering (needs bpy)
def _bpy():
    import bpy
    return bpy


def _cam_up_aim(cam, target, up_vec):
    from .preview import aim_up
    aim_up(cam, target, up_vec)


# insert shots: where the lens sits relative to the phone screen (from the static assembly, per ui asset set)
def _insert_shift(ui_assets, cam_to_phone_dist, xv, yv):
    if cam_to_phone_dist >= 0.4:
        return Vector((0, 0, 0))
    ua = set(ui_assets)
    if ua == {"ui.status_bar"}:
        du, dv = 0.012, 0.056
    elif "ui.compose_field" in ua:
        du, dv = 0.0, -0.004
    elif "ui.thread_sent_bubble" in ua:
        du, dv = 0.005, 0.02
    else:
        du, dv = 0.0, 0.0
    return xv.normalized() * du + yv.normalized() * dv


def _phone_local(j, attach, ctx):
    """Local centre of a held or resting phone."""
    if j.get("phone") is not None and attach in (None, "hand_l", "hand_r", "hands_both"):
        return j["phone"]
    if attach == "hand_r":
        return j["handR"] + Vector((0.03, 0, 0.03))
    if attach == "hand_l":
        return j["handL"] + Vector((0.03, 0, 0.03))
    if attach == "lap":
        return j["pelvis"] + Vector((0.24, 0, 0.12))
    if attach == "chest":
        return j["chest"] + Vector((0.24, 0, -0.16))
    if attach == "knee":
        return j["knee"][0] + Vector((0, 0, 0.10))
    if attach == "car_strip":
        return Vector(ctx["car"]["console_top"]) + Vector((0, 0, 0.01))
    if attach == "desk":
        return Vector(ctx["desk"]["phone"])
    return (j["handL"] + j["handR"]) / 2 + Vector((0.03, 0, 0.02))


class _FrameRig:
    """The animated parts of one assembled shot: everything that changes from frame to frame is (re)built here."""

    def __init__(self, ctx, stage, motion, ui_tl):
        from . import phone as PH
        from . import preview as P
        from . import util as U
        self.bpy, self.PH, self.P, self.U = _bpy(), PH, P, U
        self.c = ctx
        self.stage, self.motion, self.ui_tl = stage, motion, ui_tl
        self.shot, self.canon, self.sid = ctx["shot"], ctx["canon"], ctx["shot"]["shot_id"]
        self.scene, self.n = stage.scene, stage.n
        self.off = stage.off
        self.cam, self.cam_data = ctx["cam"], ctx["cam_data"]
        self.rig = ctx["rig"]
        self.units = ctx["units"]
        self.colors = PH.colors_for(self.shot, self.canon)
        self.is_insert = (self.shot.get("composition") or {}).get("framing") == "insert"
        self.look_at = (self.shot.get("camera") or {}).get("look_at", "")
        self.ui_assets = [a for a in self.shot.get("assets", []) if a.startswith("ui.")]
        self.cam0 = Vector(ctx["cpos"])            # the lens position the static assembly settled on
        self.cam_static_pos = stage.cpos.copy()
        self.frame_col = None
        bpy = self.bpy
        # remove the static figure / phone / crank collections: they are rebuilt per frame
        for cid, (_info, tmp) in list(ctx["figs"].items()):
            U.remove_collection(tmp)
        ctx["figs"].clear()
        # car pieces: remember base locations so the car body offsets do not accumulate
        self.car_objs = []
        if self.scene in STREET_SCENES:
            for o in ctx["units"]["street"].objects:
                if o.name.startswith(P_CAR_PIECES):
                    o["fm_base_loc"] = list(o.location)
                    self.car_objs.append(o)
        car = ctx["car"] if isinstance(ctx["car"], dict) else {"door": ctx["car"]}
        self.door = bpy.data.objects.get(car.get("door")) if car.get("door") else None
        self.lid = bpy.data.objects.get(car.get("glovebox_lid")) if car.get("glovebox_lid") else None
        if self.door is not None:
            self.door["fm_closed_loc"] = list(self.door.get("fm_closed_loc", self.door.location))
        self.lights = [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("phone.")]
        for o in self.lights:
            o["fm_base_energy"] = o.data.energy
        self._extra_props_built = False
        self._setup_shop()
        self._setup_extras()

    # ---- one-off objects
    def _setup_shop(self):
        bpy, P, U = self.bpy, self.P, self.U
        self.panel_lights, self.fridge_lights, self.shop_glow = [], [], None
        if self.scene != "SC03":
            return
        for o in bpy.data.objects:
            if o.type == "LIGHT" and o.name.endswith("." + self.sid):
                if o.name.startswith("panel"):
                    self.panel_lights.append(o)
                elif o.name.startswith("fridges"):
                    self.fridge_lights.append(o)
        lt = self.shot.get("lighting") or {}
        key = lt.get("key")
        key_k = key.get("temperature_k") if isinstance(key, dict) else None
        if not self.panel_lights:      # shots that start dark in the static assembly (SC03_SH050): make the panel lights
            pc = P.kelvin_lin(key_k or 5000)
            from . import sets as S
            for i in range(4):
                self.panel_lights.append(P.add_light("POINT", f"panel{i}.{self.sid}", S.SHOP_ORIGIN + Vector((2.25, 9.0 * (i + 0.5) / 4, 2.4)),
                                                     260, pc, self.rig, size=0.4))
        for o in self.panel_lights:
            o["fm_base_energy"] = 260 if o.data.energy < 1 else o.data.energy
        for o in self.fridge_lights:
            o["fm_base_energy"] = o.data.energy
        glow = P.add_light("POINT", "phoneglow." + self.sid, Vector((0, 0, 0)), 15, P.kelvin_lin(4200), self.rig, size=0.1)
        glow["fm_base_energy"] = 15.0
        self.shop_glow = glow

    def _setup_extras(self):
        """Props the set does not build but the vocabulary animates: the rear-view mirror and the adapter ring LED."""
        U, bpy = self.U, self.bpy
        self.mirror = self.adapter_on = self.adapter_off = None
        a = self.stage.car
        pr = self.motion.get("props") or {}
        if a and "rear_view_mirror" in pr:
            m = U.box("rear_view_mirror", (0.22, 0.03, 0.06), a["mirror"], self.rig, U.toon({"hex": "#2B2E36", "linear": U.lin("#2B2E36")}))
            m["fm_shot"] = True
            self.mirror = m
        if a and "dash_lights_and_adapter_ring" in pr:
            on = U.cyl("adapter_ring_on", 0.014, 0.004, a["adapter"], self.rig, U.flat({"hex": "#F5B940", "linear": U.lin("#F5B940")}, strength=4.0))
            off = U.cyl("adapter_ring_off", 0.014, 0.004, a["adapter"], self.rig, U.flat({"hex": "#3A3630", "linear": U.lin("#3A3630")}))
            for o in (on, off):
                o["fm_shot"] = True
            self.adapter_on, self.adapter_off = on, off

    # ---- per frame
    def apply(self, S):
        bpy, U = self.bpy, self.U
        f = S["f"]
        self._camera_setup(S)
        self._car(S)
        if self.frame_col is not None:
            U.remove_collection(self.frame_col)
        self.frame_col = bpy.data.collections.new("fm.frame")
        bpy.context.scene.collection.children.link(self.frame_col)
        infos = {}
        for cid, cs in S["characters"].items():
            infos[cid] = self._character(cid, cs, S)
        self._phones(S, infos)
        self._crank(S, infos)
        self._pencil(S, infos)
        self._lights(S, infos)
        self._camera_aim(S, infos)
        for o in self.frame_col.all_objects:
            o["fm_shot"] = True
        bpy.context.view_layer.update()

    def _camera_setup(self, S):
        if S["camera"]["move"] != "none":
            self.cam.location = self.cam0 + (S["camera"]["pos"] - self.cam_static_pos)
            self.cam_now = S["camera"]["pos"]

    def _car(self, S):
        from mathutils import Euler
        props = S["props"]
        door, lid = self.door, self.lid
        off = props.get("car_body", {}).get("offset", (0.0, 0.0, 0.0))
        d = Vector(off)
        if door is not None:
            deg = props.get("passenger_door", {}).get("angle_deg", 0.0)
            dl = door.dimensions.y
            base = Vector(door["fm_closed_loc"])
            ang = math.radians(deg)
            hy = float((door.get("fm_hinge_xy") or [base.x, base.y + dl / 2])[1])
            rel = Vector((0, base.y - hy, 0))
            rel.rotate(Euler((0, 0, -ang)))
            door.location = Vector((base.x, hy, base.z)) + rel + d
            door.rotation_euler = (0, 0, -ang)
        if lid is not None:
            amt = props.get("glovebox_lid", {}).get("open", 0.0)
            lc, lo = Vector(lid["fm_closed_loc"]), Vector(lid["fm_open_loc"])
            lid.location = lc + (lo - lc) * amt + d
            lid.rotation_euler = (math.radians(-90) * amt, 0, 0)
        for o in self.car_objs:
            if o is door or o is lid:
                continue
            o.location = Vector(o["fm_base_loc"]) + d
        self.car_offset = d
        if self.mirror is not None:
            self.mirror.rotation_euler = (math.radians(props["rear_view_mirror"]["tilt_deg"]), 0, 0)
            self.mirror.location = self.stage.car["mirror"] + d
        if self.adapter_on is not None:
            on = props["dash_lights_and_adapter_ring"]["on"]
            self.adapter_on.hide_render = not on
            self.adapter_off.hide_render = on
            for o in (self.adapter_on, self.adapter_off):
                o.location = self.stage.car["adapter"] + d
        if self.scene == "SC03":
            for o in self.bpy.data.objects:
                if o.get("fm_shop_light"):
                    o.hide_render = not props.get("shop_lights", {}).get("on", True)
        sd = props.get("shop_door")
        if sd is not None and "shop_door" in self.bpy.data.objects:
            pass

    def _character(self, cid, cs, S):
        bpy, U = self.bpy, self.U
        from .characters import figure
        base, fac = cs["frame"]
        base = base.copy()
        if cid == "ren" and self.scene == "SC01":
            base = base + Vector(self.car_offset)
        pr = dict(self.stage.props[cid])
        hs = S["props"].get("hana_headphones", {}).get("state") if cid == "hana" else None
        if hs == "neck":
            pr["headphones_state"] = "down"
        face = cs["face"]
        if cs["eyes_closed"]:
            face = face + "+closed"
            if face not in PS.FACE_SHAPES:
                PS.FACE_SHAPES[face] = dict(PS.FACE_SHAPES[cs["face"]], eye=0.12)
        col = bpy.data.collections.new("fm.frame." + cid)
        self.frame_col.children.link(col)
        info = figure(col, cid, self.canon, pr, base, fac, joints=cs["joints"], face=face)
        if self.is_insert:
            for o in col.objects:
                n_ = o.name.split("_", 1)[1] if "_" in o.name else o.name
                if n_.startswith(("head", "hair", "eye", "tuft", "neck", "thigh", "shin", "torso", "uarm", "farm", "hand")):
                    o.hide_render = True
        info["col"] = col
        info["base"], info["fac"] = base, fac
        info["w"] = lambda v, b=base, f_=fac: PS.to_world(Vector(v), b, f_)
        return info

    def _phones(self, S, infos):
        bpy, U, PH = self.bpy, self.U, self.PH
        st = S["ui"]
        zup = Vector((0, 0, 1))
        # Ren's phone: the ui_timeline drives the screen, phone_ren the hand
        if "ren" in infos and st is not None and st.get("phone") == "ren":
            i = infos["ren"]
            att = S["characters"]["ren"]["phone_attach"]
            pos = i["w"](_phone_local(S["characters"]["ren"]["joints"], att, self.stage.ctx))
            head = i["w"](S["characters"]["ren"]["joints"]["head"])
            toward = (self.cam0 - pos) if (self.is_insert and self.look_at == "phone_ren") else (head - pos)
            nz = toward.normalized() if toward.length > 1e-6 else zup
            yv = zup - nz * zup.dot(nz)
            yv = yv.normalized() if yv.length > 1e-4 else Vector((1, 0, 0))
            xv = yv.cross(nz)
            assets = {"map": ["ui.map_pin_screen"], "call": ["ui.call_screen"], "sent": ["ui.thread_sent_bubble"]}.get(st["screen"], ["ui.compose_field"])
            e = PH.build_phone(i["col"], self.sid, pos, xv, yv, nz, assets, st, self.colors, screen_on=not st["screen_off"], phone="ren")
            i["phone_w"], i["phone_axes"] = pos, (xv, yv, nz)
            for o in i["col"].objects:
                o["fm_shot"] = True
        # Hana's phone (SC05): held, or lying on the desk
        if "world.props.phone_hana" in self.shot.get("assets", []):
            pr = S["props"].get("phone_hana", {})
            att = pr.get("attach") or "desk"
            hst = st if (st and st.get("phone") == "hana") else {"pct": 0, "red": False, "bolt": False, "digits": False, "hana_ui": "wake",
                                                                  "brightness": 1.0, "frame": S["f"], "ui": None}
            cs = S["characters"].get("hana")
            if cs is not None and att != "desk":
                i = infos["hana"]
                pos = i["w"](_phone_local(cs["joints"], att, self.stage.ctx))
                toward = i["w"](cs["joints"]["head"]) - pos
                col = i["col"]
            else:
                pos = ROOM_ORIGIN + Vector((0.25, -0.3, 0.75))
                toward = self.cam0 - pos
                pos = pos + toward.normalized() * 0.06
                col = self.frame_col
            nz = toward.normalized()
            yv = zup - nz * zup.dot(nz)
            yv = yv.normalized() if yv.length > 1e-4 else Vector((1, 0, 0))
            hp = PH.build_phone(col, self.sid + "h", pos, yv.cross(nz), yv, nz, ["ui.photo_only"], hst, self.colors, body_hex="#3D3A4A",
                                screen_on=not hst.get("screen_off", False), phone="hana")
            if cs is not None and "hana" in infos:
                infos["hana"]["phone_w"] = pos
            for o in col.all_objects:
                o["fm_shot"] = True
            hp["fm_shot"] = True

    def _crank(self, S, infos):
        U, bpy = self.U, self.bpy
        cr = S["props"].get("crank_charger")
        if cr is None or "ren" not in infos or cr.get("world") is None:
            return
        i, cs = infos["ren"], S["characters"]["ren"]
        lap = cr["world"]
        yaw = math.atan2(i["fac"].y, i["fac"].x)
        if "crank_handle" in cs["joints"]:
            yaw = math.atan2(self.stage.frames["kerb"][1].y, self.stage.frames["kerb"][1].x)

        def at(x_, y_, z_):
            v_ = Vector((x_, y_, z_))
            v_.rotate(__import__("mathutils").Euler((0, 0, yaw)))
            return lap + v_
        col = i["col"]
        cm = U.toon({"hex": "#D6C592", "linear": U.lin("#D6C592")})
        am = U.toon({"hex": "#B8A878", "linear": U.lin("#B8A878")})
        top, sx = 0.021, 0.045
        U.box("crank_body", (0.13, 0.065, 0.042), lap, col, cm, rot=(0, 0, yaw))
        # arm: flush along the top groove (pointing back) when folded, else at the handle angle (0 = 12 o'clock, + forward)
        ang = cs["crank_angle"] if cs["crank_angle"] is not None else 0.0
        ang = ang if ang <= math.pi else ang - TWO_PI
        a = _lerp(-math.pi / 2, ang, _ease("ease_in_out", cr["unfold"])) if cr["unfold"] < 1.0 else ang
        arm_l = 0.085
        p0 = at(sx, 0, top)
        p1 = at(sx + math.sin(a) * arm_l, 0, top + 0.004 + math.cos(a) * arm_l)
        U.between("crank_arm", p0, p1, 0.006, col, am)
        U.cyl("crank_knob", 0.01, 0.022, at(sx + math.sin(a) * (arm_l + 0.006), 0, top + 0.004 + math.cos(a) * (arm_l + 0.006)), col, am,
              rot=(math.pi / 2, 0, yaw))
        amb = self.canon.get("look.color.accent_power_amber") or {}
        a_hex = amb.get("hex", "#F5B940")
        off_hex = "#6B6B5F"
        k = cr["pip"]
        hx = a_hex if k >= 1.0 else ("#" + "".join("%02X" % int(round(int(a_hex[q:q + 2], 16) * k + int(off_hex[q:q + 2], 16) * (1 - k))) for q in (1, 3, 5)) if k > 0 else off_hex)
        U.cyl("crank_pip", 0.003, 0.004, at(-0.05, 0.0, top + 0.002), col, U.flat({"hex": hx, "linear": U.lin(hx)}))

    def _pencil(self, S, infos):
        pen = S["props"].get("pencil")
        if pen is None or "hana" not in infos:
            return
        U = self.U
        col = infos["hana"]["col"]
        wood = U.toon({"hex": "#C9A46A", "linear": U.lin("#C9A46A")})
        if pen["state"] == "held":
            a = infos["hana"]["w"](S["characters"]["hana"]["joints"]["handR"])
            U.between("hana_pencil", a + Vector((0, 0, 0.02)), a + Vector((0, 0.1, -0.06)), 0.004, col, wood)
        else:
            o = ROOM_ORIGIN
            U.between("hana_pencil", o + Vector((0.02, -0.36, 0.749)), o + Vector((0.17, -0.34, 0.749)), 0.004, col, wood)

    def _lights(self, S, infos):
        bright = (S["ui"] or {}).get("brightness", 1.0) if S["ui"] else 1.0
        ph = infos.get("ren", {}).get("phone_w")
        for o in self.lights:
            if ph is not None:
                o.location = ph + infos["ren"]["fac"] * 0.06 + Vector((0, 0, 0.04))
            o.data.energy = o["fm_base_energy"] * bright
        if self.scene == "SC03":
            on = S["props"].get("shop_lights", {}).get("on", True)
            for o in self.panel_lights:
                o.data.energy = o["fm_base_energy"] if on else 0.0
            for o in self.fridge_lights:
                o.data.energy = o["fm_base_energy"] if on else 0.0
            if self.shop_glow is not None:
                self.shop_glow.data.energy = 0.0 if on else 15.0 * bright
                if "ren" in infos:
                    self.shop_glow.location = infos["ren"]["w"](S["characters"]["ren"]["joints"]["handL"]) + infos["ren"]["fac"] * 0.15
            dk = 1.0 if on else 0.04
            for m in self.bpy.data.materials:
                if "fm_shadow" in m and m.node_tree:
                    for nd in m.node_tree.nodes:
                        if nd.type == "VALTORGB":
                            nd.color_ramp.elements[0].color = (*[c * dk for c in m["fm_shadow"]], 1)

    def _camera_aim(self, S, infos):
        """Static cameras keep the rotation from the static assembly (but aim once at the animated subject); inserts stay
        squared to the phone, and the dolly moves the lens without turning it."""
        cam, P = self.cam, self.P
        if self.is_insert and self.look_at == "phone_ren" and "ren" in infos and "phone_axes" in infos["ren"]:
            xv, yv, nz = infos["ren"]["phone_axes"]
            pos = infos["ren"]["phone_w"]
            base = self.cam0
            sh = _insert_shift(self.ui_assets, (self.cam0 - pos).length, xv, yv)
            cam.location = base + sh
            P.aim_up(cam, pos + sh, yv)
            if self.cam_data.dof.use_dof:
                self.cam_data.dof.focus_distance = max(((pos + sh) - cam.location).length, 0.1)
            return
        if not getattr(self, "_aimed", False):
            tgt = self._subject_target(S, infos)
            if tgt is not None:
                P.aim(cam, tgt)
                if self.cam_data.dof.use_dof:
                    self.cam_data.dof.focus_distance = max((tgt - self.cam0).length, 0.1)
            self._aimed = True

    def _subject_target(self, S, infos):
        la = self.look_at
        if la in infos:
            i = infos[la]
            head = i["w"](S["characters"][la]["joints"]["head"])
            cr = S["props"].get("crank_charger")
            if la == "ren" and self.scene == "SC04" and self.stage.n in (40, 50, 90) and cr and cr.get("world") is not None:
                return (head + Vector((0, 0, 0.1))) * 0.62 + cr["world"] * 0.38
            return head - Vector((0, 0, 0.1))
        if la == "phone_ren" and "ren" in infos and "phone_w" in infos["ren"]:
            return infos["ren"]["phone_w"]
        if la == "crank_charger" and (S["props"].get("crank_charger") or {}).get("world") is not None:
            return S["props"]["crank_charger"]["world"]
        return None

    def close(self):
        if self.frame_col is not None:
            self.U.remove_collection(self.frame_col)
            self.frame_col = None


P_CAR_PIECES = ("car_", "seat_passenger", "seat_driver", "dashboard", "console", "steering_wheel", "glovebox")


def _stamp(sid, on):
    sc = _bpy().context.scene
    r = sc.render
    r.use_stamp = bool(on)
    if not on:
        return
    for k in ("use_stamp_date", "use_stamp_time", "use_stamp_render_time", "use_stamp_camera", "use_stamp_lens",
              "use_stamp_scene", "use_stamp_marker", "use_stamp_filename", "use_stamp_sequencer_strip",
              "use_stamp_hostname", "use_stamp_memory", "use_stamp_frame_range"):
        if hasattr(r, k):
            setattr(r, k, False)
    r.use_stamp_frame = True
    r.use_stamp_note = True
    r.stamp_note_text = sid
    r.stamp_font_size = max(10, int(r.resolution_x / 40))
    r.use_stamp_labels = False
    r.stamp_foreground = (1, 1, 1, 1)
    r.stamp_background = (0, 0, 0, 0.6)


def render_frames(resolved_dir, shot_id, frames, out_dir, width, *, stamp=False, samples=None, fast=False, skip_existing=False, log=print):
    """Render the given shot-local frames of one shot to <out_dir>/<shot_id>/%04d.png. Builds the shot once with the
    static assembly (preview.render_shot), then re-poses everything per frame. Returns the list of PNG paths."""
    bpy = _bpy()
    from . import preview as P
    film, shots, canon, units, rig, door = P.init_scene(resolved_dir, width)
    ev = bpy.context.scene.eevee
    try:
        if samples:
            ev.taa_render_samples = int(samples)
        if fast:  # draft playblast: cheaper shadows (the costly part of an EEVEE frame here), same look otherwise
            ev.shadow_ray_count, ev.shadow_step_count, ev.shadow_resolution_scale = 1, 1, 0.25
    except Exception:  # noqa: BLE001
        pass
    shot = shots[shot_id]
    ordered = list(shots)
    prior = [shots[s] for s in ordered[:ordered.index(shot_id)]]
    if not shot.get("motion"):
        raise ValueError(f"{shot_id} has no motion block (no anim file): nothing to animate")
    motion = with_carried_props(shot, prior)
    P.world_sky(shot["scene_id"] in P.DUSK, canon)
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    shot_dir = os.path.join(out_dir, shot_id)
    os.makedirs(shot_dir, exist_ok=True)
    stage = Stage(shot, canon, motion=motion)
    written = []

    def go(ctx):
        rig_ = _FrameRig(ctx, stage, motion, shot.get("ui_timeline"))
        _stamp(shot_id, stamp)
        scn = bpy.context.scene
        for f in frames:
            path = os.path.join(shot_dir, "%04d.png" % f)
            if skip_existing and os.path.exists(path) and os.path.getsize(path) > 0:
                written.append(path)
                continue
            S = frame_state(shot, motion, shot.get("ui_timeline"), f, stage=stage)
            rig_.apply(S)
            scn.frame_current = f
            scn.render.filepath = path
            bpy.ops.render.render(write_still=True)
            written.append(path)
            log(f"FM_FRAME {shot_id} {f}")
        rig_.close()
        return written

    P.render_shot(film, shot, canon, units, rig, door, out_dir, bg, shots, animate=go)
    return written


# ===================================================================================== entry point for run_frames.py
def main(argv):
    """run_frames.py <resolved_dir> <out_dir> <shot_id> <width> <frames: 12,24,30-40|all> [stamp|no] [samples|-] [fast|-] [resume|-]"""
    resolved_dir, out_dir, shot_id, width, spec = argv[:5]
    stamp = len(argv) > 5 and argv[5] in ("stamp", "1", "true")
    samples = int(argv[6]) if len(argv) > 6 and argv[6].isdigit() else None
    fast = len(argv) > 7 and argv[7] == "fast"
    resume = len(argv) > 8 and argv[8] == "resume"
    shot = __import__("json").load(open(os.path.join(resolved_dir, shot_id + ".json"), encoding="utf-8"))
    n = int(shot["frames"]["count"])
    frames = parse_frames(spec, n)
    try:
        render_frames(resolved_dir, shot_id, frames, out_dir, int(width), stamp=stamp, samples=samples, fast=fast, skip_existing=resume)
        print("FM_OK", shot_id, len(frames), flush=True)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("FM_FAIL", shot_id, e, flush=True)
