"""Pose geometry for the proxy figures: pure python (mathutils.Vector only, no bpy calls).

A pose is a JOINT DICT in the figure-local frame. Local coordinates are (fw, rt, up):
fw = along the figure's facing, rt = the figure's right (the same right as characters.figure()), up = world
z from the ground (figure() places seated and kneeling figures with the base at z = 0, so `up` is an
absolute height and a kerb seat is at 0.12). `characters.figure(joints=...)` converts local -> world.

Joint dict keys (all Vectors are local):
    pelvis, hipL, hipR, chest, neck, head, shL, shR, handL, handR   Vector
    knee, foot, elbow                                               [left, right] lists of Vector
    phone                Vector | None  the phone centre when it is held or lying in the lap
    phone_hand           'L' | 'R' | 'both' | None
    head_yaw, head_pitch radians. yaw is positive toward the figure's RIGHT; pitch is positive when the face
                         looks DOWN. Both are absolute (relative to the figure's facing / the horizon).
    face                 face ref name or None (neutral); the face track normally drives it
    _dims                the bone lengths the solver used (blend() and check_lengths() read them)
    knee_pole, elbow_pole  bend directions kept so blend() can re-solve knees and elbows
    reach_err            [left, right] metres by which a hand target was out of reach (0 when reached)
    (crank gaits also add crank_handle, crank_angle, handle_top)

Registry: POSES[(cid, pose_ref)](props, ctx=None) -> joint dict, one entry per animvocab preset.
Contexts (car, door, kerb, desk) give the props each pose touches in the same local frame; pass
`ctx={'car': {...}}` to override single values, or build one from set geometry with `to_local`.
"""
from __future__ import annotations

import math

try:
    from mathutils import Vector
except ImportError:  # the standalone (non-Blender) python: bpy registers the mathutils module
    import bpy  # noqa: F401
    from mathutils import Vector

# ----------------------------------------------------------------------------------- context
CTX_DEFAULT = {
    # Driver seat, figure facing the windscreen. Numbers follow the Ren canon (seat 0.45, roof 1.45, glovebox
    # reach 0.75 m from the driver) and a normal driving position; sets.py places the wheel about 0.6 m further
    # forward, so pass a ctx built from the set (see to_local) if the set is meant to drive the pose.
    "car": {
        "seat_z": 0.45, "roof_z": 1.45,
        "wheel_center": (0.40, 0.0, 0.88), "wheel_radius": 0.19,
        "wheel_up": (0.5, 0.0, 0.866),       # in-plane top direction (fw, rt, up) of the wheel (rake 60 deg, sets.py)
        "mirror": (0.45, -0.10, 1.18),
        "glovebox_latch": (0.45, -0.55, 0.72),   # 0.75 m from the pelvis (canon reach_from_driver_seat_m)
        "console_top": (0.15, -0.30, 0.56),
        "pedal_r": (0.55, 0.10, 0.14), "pedal_l": (0.45, -0.15, 0.12),
    },
    # Standing on the pavement beside the passenger door, facing into the car.
    "door": {
        "seat_edge": (0.62, -0.22, 0.47), "latch": (1.02, 0.10, 0.72), "sill": (0.60, 0.20, 0.72),
        "roof_z": 1.45,
    },
    "kerb": {
        "seat_z": 0.12,                       # pavement surface Ren sits on (and rests his feet on)
        "crank_center": (0.40, 0.0, 0.64),    # crank body centre, between the knee tops (top face about 0.68)
        "crank_spindle": (0.045, 0.0, 0.021), # spindle relative to the body centre (preview.crank_lap)
        "crank_radius": 0.091,                # arm 0.085 + knob offset
    },
    "desk": {
        "seat_z": 0.46,                       # chair seat top
        "desk_z": 0.74,                       # desk top surface
        "sketchbook": (0.52, -0.16, 0.775),   # page centre for the drawing hand
        "sketchbook_hold": (0.47, -0.36, 0.775),
        "phone": (0.55, 0.25, 0.775),         # phone lying on the desk
    },
    # Kneeling in the shop (v2): the display stand is on the figure's right, the USB socket behind it on the wall.
    # Local (fw, rt, up) of the kneeling figure (base on the floor under the pelvis). stand_back_edge is a point on the
    # stand's back edge and stand_back_normal points away from the figure; "behind the stand" is the +normal side.
    "shop": {
        "stand_back_edge": (0.03, 0.62, 0.0), "stand_back_normal": (1.0, 0.0, 0.0),
        "socket": (0.26, 0.40, 0.30),
    },
}

FACE_SHAPES = {
    # brow_dy: raise as a fraction of head height; brow_tilt: radians, + = inner ends UP (worry), - = inner ends down
    # eye: openness 0..1.3 (1 = as built); mouth_w: width factor; mouth_h: thickness factor; smile: radians, + = corners up
    "neutral": dict(brow_dy=0.0, brow_tilt=0.0, eye=1.0, mouth_w=1.0, mouth_h=1.0, smile=0.0),
    # ren, comic set
    "rehearsed_breath": dict(brow_dy=0.05, brow_tilt=0.10, eye=1.0, mouth_w=0.6, mouth_h=3.0, smile=0.0),
    "letdown": dict(brow_dy=-0.02, brow_tilt=0.42, eye=0.7, mouth_w=0.9, mouth_h=1.0, smile=-0.30),
    "freeze": dict(brow_dy=0.12, brow_tilt=0.05, eye=1.35, mouth_w=0.55, mouth_h=3.5, smile=0.0),
    "relief": dict(brow_dy=0.05, brow_tilt=0.18, eye=0.12, mouth_w=1.0, mouth_h=1.5, smile=0.35),
    "stunned_stillness": dict(brow_dy=0.08, brow_tilt=0.0, eye=1.25, mouth_w=0.7, mouth_h=2.4, smile=0.0),
    # v2 (animation.vocab.v2.face.ren): comic set additions, shape hints from the canon
    "wary": dict(brow_dy=-0.01, brow_tilt=0.0, eye=0.85, mouth_w=0.85, mouth_h=0.7, smile=-0.05),
    "determined": dict(brow_dy=0.0, brow_tilt=-0.15, eye=1.0, mouth_w=0.8, mouth_h=0.7, smile=0.0),
    # ren, tender set
    "focused_calm": dict(brow_dy=-0.03, brow_tilt=-0.10, eye=0.85, mouth_w=0.85, mouth_h=1.0, smile=0.0),
    "hesitation_at_heart": dict(brow_dy=0.02, brow_tilt=0.35, eye=0.95, mouth_w=0.7, mouth_h=1.0, smile=-0.10),
    "release_after_send": dict(brow_dy=0.04, brow_tilt=0.18, eye=0.55, mouth_w=0.9, mouth_h=1.0, smile=0.15),
    "final_look_up": dict(brow_dy=0.06, brow_tilt=0.20, eye=1.1, mouth_w=0.9, mouth_h=1.0, smile=0.22),
    # hana
    "absorbed": dict(brow_dy=-0.03, brow_tilt=-0.05, eye=0.55, mouth_w=0.7, mouth_h=1.0, smile=0.0),
    "noticing": dict(brow_dy=0.08, brow_tilt=0.10, eye=1.2, mouth_w=0.75, mouth_h=2.2, smile=0.0),
    "reading": dict(brow_dy=0.0, brow_tilt=0.05, eye=0.8, mouth_w=0.8, mouth_h=1.0, smile=0.0),
    "small_smile": dict(brow_dy=0.04, brow_tilt=0.10, eye=0.8, mouth_w=1.05, mouth_h=1.0, smile=0.30),
}

_R = math.radians
V = Vector


def merged_ctx(ctx=None):
    """CTX_DEFAULT with the caller's per-family overrides applied (a new dict; inputs untouched)."""
    out = {k: dict(v) for k, v in CTX_DEFAULT.items()}
    for k, v in (ctx or {}).items():
        out.setdefault(k, {}).update(v)
    return out


def _v(t):
    return t if isinstance(t, Vector) else Vector(t)


# ----------------------------------------------------------------------------------- frames
def to_local(p, base, facing):
    """World point -> figure-local (fw, rt, up) given the figure base and its facing (unit XY)."""
    f = Vector((facing.x, facing.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))
    d = Vector(p) - Vector(base)
    return Vector((d.dot(f), d.dot(r), d.z))


def to_world(p, base, facing):
    f = Vector((facing.x, facing.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))
    return Vector(base) + f * p.x + r * p.y + Vector((0, 0, p.z))


# ----------------------------------------------------------------------------------- proportions
def dims(props):
    """Bone lengths from resolved proportions. Same formulas figure() uses for its defaults."""
    H = props["height_m"]
    hh = props.get("head_height_m", H / props.get("head_count", 6.5))
    leg = props.get("leg_length_m", H * 0.49)
    sh = props.get("shoulder_width_m", H * 0.24) / 2
    hip = props.get("hip_width_m", H * 0.19) / 2
    torso = H - leg - hh * 1.15
    reach = 0.9 * (props.get("arm_span_m", H) / 2 - sh)   # shoulder joint to hand centre
    return {
        "H": H, "hh": hh, "leg": leg, "sh": sh, "hip": hip, "ankle": 0.04,
        "thigh": (leg - 0.04) / 2, "shin": (leg - 0.04) / 2,
        "spine": torso * 0.95, "neck": 0.06, "headoff": hh * 0.55,
        "up": 0.51 * reach, "fore": 0.49 * reach, "tuft": float(props.get("tuft_extra_m") or 0.0),
    }


def _dir(pitch_deg, roll_deg=0.0):
    p, q = _R(pitch_deg), _R(roll_deg)
    return Vector((math.sin(p) * math.cos(q), math.sin(q), math.cos(p) * math.cos(q))).normalized()


def _ik2(root, target, l1, l2, pole, slack=0.985):
    """Two-bone chain from root toward target. Returns (mid joint, end joint, shortfall).
    Both bones keep their length exactly; the end is pulled back when the target is out of reach."""
    d = Vector(target) - root
    L = d.length
    dv = d / L if L > 1e-9 else Vector((0, 0, -1))
    lc = min(max(L, abs(l1 - l2) + 1e-3), (l1 + l2) * slack)
    end = root + dv * lc
    a = (l1 * l1 - l2 * l2 + lc * lc) / (2 * lc)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = Vector(pole) - dv * Vector(pole).dot(dv)
    if p.length < 1e-6:
        p = Vector((0, 0, 1)) - dv * dv.z
        if p.length < 1e-6:
            p = Vector((1, 0, 0))
    p.normalize()
    return root + dv * a + p * h, end, max(L - lc, 0.0)


# ----------------------------------------------------------------------------------- the rig
def rig(D, *, pelvis, spine=(0.0, 0.0), twist=0.0, neck_pitch=0.0, head_pitch=0.0, head_yaw=0.0,
        foot, hand=None, knee_pole=((0.5, 0, 1), (0.5, 0, 1)), elbow_pole=((0, -0.6, -1), (0, 0.6, -1)),
        shoulder_drop=0.0, phone=None, phone_hand=None, face=None, hips_z_extra=0.0):
    """Solve a full joint dict.

    pelvis      Vector, the hip-line centre. spine = (pitch deg, roll deg): pitch + leans the chest forward, roll +
                leans it to the figure's right. twist deg: + turns the shoulders toward the right.
    neck_pitch  extra forward pitch of the neck; head_pitch extra pitch of the head (deg, + = down).
    foot        (left, right) ankle targets. hand: (left, right) targets; an entry may be a callable(j) -> Vector
                that sees the partial joints (knees, shoulders, chest, head) so hands can sit on knees or ear cups.
    """
    P = _v(pelvis)
    up = Vector((0, 0, 1))
    hipL, hipR = P + Vector((0, -D["hip"], 0)), P + Vector((0, D["hip"], 0))
    pitch, roll = spine
    d = _dir(pitch, roll)
    chest = P + d * D["spine"]
    a0 = Vector((0, 1, 0))
    a = (a0 - d * a0.dot(d)).normalized()
    fp = Vector((1, 0, 0))
    fp = (fp - d * fp.dot(d) - a * fp.dot(a)).normalized()
    t = _R(twist)
    at = (a * math.cos(t) - fp * math.sin(t)).normalized()
    drop = up * shoulder_drop
    shL, shR = chest - at * D["sh"] - drop, chest + at * D["sh"] - drop
    tot = pitch + neck_pitch
    neck = chest + _dir(tot, roll) * D["neck"]
    total_head = tot + head_pitch
    head = neck + Vector((math.sin(_R(total_head)), 0, math.cos(_R(total_head)))) * D["headoff"]
    knees, feet, kerr = [], [], []
    for hp, ft, pole in zip((hipL, hipR), foot, knee_pole):
        k, f_, e = _ik2(hp, _v(ft), D["thigh"], D["shin"], _v(pole))
        knees.append(k)
        feet.append(f_)
        kerr.append(e)
    j = {"pelvis": P, "hipL": hipL, "hipR": hipR, "chest": chest, "neck": neck, "head": head,
         "shL": shL, "shR": shR, "knee": knees, "foot": feet}
    if hand is None:
        hand = (None, None)
    hands = []
    for s, h in zip((shL, shR), hand):
        if callable(h):
            h = h(j)
        hands.append(_v(h) if h is not None else s + Vector((0, 0, -D["up"] - D["fore"] * 0.85)))
    elbows, herr = [], []
    for s, h, pole in zip((shL, shR), hands, elbow_pole):
        e, h2, err = _ik2(s, h, D["up"], D["fore"], _v(pole))
        elbows.append(e)
        herr.append(err)
        hands[len(elbows) - 1] = h2
    j.update({
        "elbow": elbows, "handL": hands[0], "handR": hands[1],
        "phone": _v(phone) if phone is not None else None, "phone_hand": phone_hand,
        "head_yaw": _R(head_yaw), "head_pitch": _R(total_head), "face": face,
        "_dims": {k: D[k] for k in ("thigh", "shin", "up", "fore", "spine", "neck", "headoff", "hip", "sh", "hh", "tuft")},
        "knee_pole": [_v(p).copy() for p in knee_pole], "elbow_pole": [_v(p).copy() for p in elbow_pole],
        "reach_err": herr, "foot_err": kerr,
    })
    return j


def set_head(j, yaw=None, pitch=None):
    """New joints with the head yaw/pitch replaced (radians) and the head centre re-placed on the neck."""
    o = _copy(j)
    if yaw is not None:
        o["head_yaw"] = yaw
    if pitch is not None:
        o["head_pitch"] = pitch
        o["head"] = o["neck"] + Vector((math.sin(pitch), 0, math.cos(pitch))) * o["_dims"]["headoff"]
    return o


def look_angles(head, target):
    """(yaw, pitch) in radians to face `target` from `head`, both local points. yaw + = right, pitch + = down."""
    v = Vector(target) - Vector(head)
    return math.atan2(v.y, v.x), math.atan2(-v.z, math.hypot(v.x, v.y))


def look_at(j, target, max_yaw_deg=75.0, max_pitch_deg=50.0, yaw=None):
    """Aim the head at a LOCAL target point (use to_local for a world point). Clamped to a human range."""
    y, p = look_angles(j["head"], target)
    y = max(-_R(max_yaw_deg), min(_R(max_yaw_deg), y))
    p = max(-_R(max_pitch_deg), min(_R(max_pitch_deg), p))
    return set_head(j, yaw=y if yaw is None else yaw, pitch=p)


def _copy(j):
    o = {}
    for k, v in j.items():
        if isinstance(v, Vector):
            o[k] = v.copy()
        elif isinstance(v, list):
            o[k] = [x.copy() if isinstance(x, Vector) else x for x in v]
        elif isinstance(v, dict):
            o[k] = dict(v)
        else:
            o[k] = v
    return o


# ----------------------------------------------------------------------------------- checks
def crown_z(j):
    """Highest point of the head (hair, no tuft) in local up."""
    hh = j["_dims"]["hh"]
    p = j["head_pitch"]
    return j["head"].z + hh * (0.58 * math.cos(p) + 0.05 * abs(math.sin(p)))


def check_lengths(j, props, tol=0.03):
    """Bone-length violations beyond `tol` (default 3 %). [] when the rig is anatomically consistent."""
    D = dims(props)
    out = []

    def chk(name, a, b, want):
        got = (a - b).length
        if abs(got - want) > tol * want:
            out.append(f"{name}: {got:.3f} m vs {want:.3f} m ({(got / want - 1) * 100:+.1f} %)")

    for i, (hp, s) in enumerate(((j["hipL"], "L"), (j["hipR"], "R"))):
        chk("thigh" + s, hp, j["knee"][i], D["thigh"])
        chk("shin" + s, j["knee"][i], j["foot"][i], D["shin"])
    for i, (sh, hnd, s) in enumerate(((j["shL"], j["handL"], "L"), (j["shR"], j["handR"], "R"))):
        chk("upperarm" + s, sh, j["elbow"][i], D["up"])
        chk("forearm" + s, j["elbow"][i], hnd, D["fore"])
    chk("spine", (j["hipL"] + j["hipR"]) / 2, j["chest"], D["spine"])
    chk("neck", j["chest"], j["neck"], D["neck"])
    chk("headoff", j["neck"], j["head"], D["headoff"])
    chk("hipwidth", j["hipL"], j["hipR"], 2 * D["hip"])
    chk("shoulderwidth", j["shL"], j["shR"], 2 * D["sh"])
    return out


def check_contacts(j, tol=0.02):
    """Reach shortfalls (hands and feet out of reach of their targets), as strings."""
    out = []
    for name, errs in (("hand", j.get("reach_err") or []), ("foot", j.get("foot_err") or [])):
        for i, e in enumerate(errs):
            if e > tol:
                out.append(f"{name}{'LR'[i]} short by {e:.3f} m")
    return out


# ----------------------------------------------------------------------------------- easing and blending
def _smooth(t):
    return t * t * (3 - 2 * t)


def ease_value(name, t):
    """Map t in [0,1] to the eased blend weight. Endpoints are exactly 0 and 1 for every ease."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if name == "hold":
        return 0.0
    if name == "step":
        return 1.0
    if name == "linear":
        return t
    if name == "ease_in":
        return t * t
    if name == "ease_out":
        return 1 - (1 - t) * (1 - t)
    if name == "overshoot_small":
        c = 0.9
        u = t - 1
        return 1 + (c + 1) * u * u * u + c * u * u
    if name == "gravity":
        if t < 0.8:
            u = t / 0.8
            return u * u
        return 1 - 0.08 * math.sin(math.pi * (t - 0.8) / 0.2)
    return _smooth(t)  # ease_in_out and unknown names


def _lerp(a, b, u):
    return a + (b - a) * u


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def blend(a, b, t, ease="ease_in_out"):
    """Per-joint interpolation from pose a to pose b at t in [0,1] with a vocabulary ease.
    t <= 0 returns a copy of a and t >= 1 a copy of b. In between, hips, shoulders, chest, neck, head, feet
    and hands are interpolated (head yaw the short way round) and the bone lengths are restored: the spine,
    neck and head offsets keep their length and the knees and elbows are re-solved from the blended targets
    and poles, so no limb shrinks mid-blend."""
    u = ease_value(ease, t)
    if u <= 0.0:
        return _copy(a)
    if u >= 1.0 and t >= 1.0:
        return _copy(b)
    o = _copy(a)
    for k in ("pelvis", "hipL", "hipR", "chest", "neck", "head", "shL", "shR", "handL", "handR"):
        o[k] = _lerp(a[k], b[k], u)
    o["foot"] = [_lerp(x, y, u) for x, y in zip(a["foot"], b["foot"])]
    o["knee_pole"] = [_lerp(x, y, u) for x, y in zip(a["knee_pole"], b["knee_pole"])]
    o["elbow_pole"] = [_lerp(x, y, u) for x, y in zip(a["elbow_pole"], b["elbow_pole"])]
    o["head_pitch"] = _lerp(a["head_pitch"], b["head_pitch"], u)
    o["head_yaw"] = a["head_yaw"] + _wrap(b["head_yaw"] - a["head_yaw"]) * u
    for k in ("phone",):
        if a.get(k) is not None and b.get(k) is not None:
            o[k] = _lerp(a[k], b[k], u)
        else:
            o[k] = (b if u >= 0.5 else a).get(k)
    for k in ("phone_hand", "face", "crank_handle", "crank_angle", "handle_top"):
        src = b if u >= 0.5 else a
        if k in src:
            o[k] = src[k]
        else:
            o.pop(k, None)
    D = a["_dims"]
    hipc = (o["hipL"] + o["hipR"]) / 2
    o["pelvis"] = hipc
    hw = (o["hipR"] - o["hipL"])
    if hw.length > 1e-9:
        o["hipL"], o["hipR"] = hipc - hw.normalized() * D["hip"], hipc + hw.normalized() * D["hip"]
    o["chest"] = hipc + _unit(o["chest"] - hipc) * D["spine"]
    sw = o["shR"] - o["shL"]
    sc = (o["shL"] + o["shR"]) / 2
    if sw.length > 1e-9:
        o["shL"], o["shR"] = sc - sw.normalized() * D["sh"], sc + sw.normalized() * D["sh"]
    o["neck"] = o["chest"] + _unit(o["neck"] - o["chest"]) * D["neck"]
    o["head"] = o["neck"] + _unit(o["head"] - o["neck"]) * D["headoff"]
    kn, ft, kerr = [], [], []
    for hp, f_, pole in zip((o["hipL"], o["hipR"]), o["foot"], o["knee_pole"]):
        k, f2, e = _ik2(hp, f_, D["thigh"], D["shin"], pole)
        kn.append(k)
        ft.append(f2)
        kerr.append(e)
    o["knee"], o["foot"], o["foot_err"] = kn, ft, kerr
    el, herr, hands = [], [], []
    for s, h, pole in zip((o["shL"], o["shR"]), (o["handL"], o["handR"]), o["elbow_pole"]):
        e, h2, err = _ik2(s, h, D["up"], D["fore"], pole)
        el.append(e)
        hands.append(h2)
        herr.append(err)
    o["elbow"], o["handL"], o["handR"], o["reach_err"] = el, hands[0], hands[1], herr
    return o


def _unit(v):
    return v.normalized() if v.length > 1e-9 else Vector((0, 0, 1))


# ----------------------------------------------------------------------------------- preset builders
def _rim(c, ang_deg):
    """Point on the steering-wheel rim; 0 deg is the top, + toward the driver's right."""
    cen, r, upv = _v(c["wheel_center"]), c["wheel_radius"], _v(c["wheel_up"])
    side = Vector((0, 1, 0))
    a = _R(ang_deg)
    return cen + (upv * math.cos(a) + side * math.sin(a)) * r


def _car_legs(c, slack=False):
    z = c["seat_z"]
    if slack:
        return (Vector((0.52, -0.16, z - 0.31)), Vector((0.52, 0.16, z - 0.31)))
    return (_v(c["pedal_l"]), _v(c["pedal_r"]))


def _car_pelvis(c, dx=0.0, dz=0.0):
    return Vector((dx, 0, c["seat_z"] + 0.02 + dz))


_KP_SIT = ((0.5, -0.05, 1.0), (0.5, 0.05, 1.0))
_EP_DOWN = ((0, -0.6, -1), (0, 0.6, -1))
_EP_TUCK = ((-0.5, -0.5, -1), (-0.5, 0.5, -1))


def car_upright(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    return rig(D, pelvis=_car_pelvis(c), spine=(-10, 0), neck_pitch=10, foot=_car_legs(c), knee_pole=_KP_SIT,
               hand=(_rim(c, -32), _rim(c, 32)), elbow_pole=_EP_DOWN)


def car_reach_up(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    j = rig(D, pelvis=_car_pelvis(c), spine=(4, 4), twist=-6, neck_pitch=-4, foot=_car_legs(c), knee_pole=_KP_SIT,
            hand=(Vector((0.26, -0.14, 0.68)), _v(c["mirror"])), elbow_pole=((0, -0.6, -1), (0, 0.5, -0.4)),
            phone=Vector((0.28, -0.14, 0.70)), phone_hand="L")
    return look_at(j, _v(c["mirror"]), max_yaw_deg=25)


def car_phone_up(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    ph = Vector((0.32, 0.0, 1.0))
    return rig(D, pelvis=_car_pelvis(c), spine=(-6, 0), neck_pitch=18, head_pitch=12, foot=_car_legs(c), knee_pole=_KP_SIT,
               hand=(ph + Vector((0, -0.05, 0)), ph + Vector((0, 0.05, 0))), elbow_pole=_EP_TUCK, phone=ph, phone_hand="both")


def car_sag(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    lap = c["seat_z"] + 0.11
    return rig(D, pelvis=_car_pelvis(c, dx=0.02, dz=-0.02), spine=(20, 0), neck_pitch=24, head_pitch=8, shoulder_drop=0.04,
               foot=_car_legs(c), knee_pole=_KP_SIT,
               hand=(Vector((0.24, -0.15, lap)), Vector((0.24, 0.15, lap))), elbow_pole=((-0.4, -0.5, -1), (-0.4, 0.5, -1)),
               phone=Vector((0.26, 0.02, lap + 0.01)), phone_hand=None)


def car_lean_glovebox(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    latch = _v(c["glovebox_latch"])
    best = None
    for k in range(0, 121):
        s = k / 100.0
        j = rig(D, pelvis=_car_pelvis(c), spine=(24 * s, -50 * s), twist=-34 * s, neck_pitch=-10 * s, foot=_car_legs(c),
                knee_pole=_KP_SIT, hand=(_v(c["console_top"]), latch), elbow_pole=((0, -0.6, -1), (0.3, 0.3, -0.6)),
                shoulder_drop=0.0)
        best = j
        if j["reach_err"][1] < 1e-4 and (j["shR"] - latch).length < 0.93 * (D["up"] + D["fore"]):
            break
    return look_at(best, latch, max_yaw_deg=60)


def car_recline(props, ctx=None):
    D, c = dims(props), merged_ctx(ctx)["car"]
    return rig(D, pelvis=_car_pelvis(c, dx=0.08, dz=-0.03), spine=(-32, 0), neck_pitch=22, foot=_car_legs(c, slack=True),
               knee_pole=_KP_SIT, hand=(Vector((0.05, -0.30, 0.50)), Vector((0.05, 0.30, 0.50))), elbow_pole=_EP_DOWN)


_FW_CACHE = {}


def _forehead_point(j_neck, D, t):
    """Forehead contact point for a head whose total pitch is t (radians): neck + head offset + forehead offset."""
    hf = Vector((math.cos(t), 0, -math.sin(t)))
    hu = Vector((math.sin(t), 0, math.cos(t)))
    return j_neck + hu * D["headoff"] + hf * D["hh"] * 0.36 + hu * D["hh"] * 0.29


def _fw_solve(D, c, top, neck_pitch):
    """(pelvis dx, spine pitch deg, total head pitch deg) that put the forehead on `top` (the rim top). The neck depends
    only on the pelvis and the spine pitch, so each (dx, pitch) has one best head pitch: a coarse scan then a fine one. dx
    stays 0 (the pelvis does not move) whenever that already reaches; a wheel set further away lets him slide forward."""
    key = (round(D["hh"], 4), round(D["spine"], 4), round(D["neck"], 4), round(D["headoff"], 4), round(D["thigh"], 4),
           round(c["seat_z"], 4), tuple(round(x, 4) for x in c["wheel_center"]), round(c["wheel_radius"], 4),
           tuple(round(x, 4) for x in c["wheel_up"]), neck_pitch)
    if key in _FW_CACHE:
        return _FW_CACHE[key]

    def best_t(neck, lo, hi, step):
        best = None
        n = int(round((hi - lo) / step))
        for k in range(n + 1):
            t = lo + k * step
            e = (_forehead_point(neck, D, _R(t)) - top).length
            if best is None or e < best[0]:
                best = (e, t)
        return best

    def solve(dx):
        pel = _car_pelvis(c, dx=dx, dz=-0.02)

        def neck_of(p):
            return pel + _dir(p) * D["spine"] + _dir(p + neck_pitch) * D["neck"]

        best = None
        for p in range(8, 56):
            e, t = best_t(neck_of(float(p)), 45.0, 85.0, 1.0)
            if best is None or e < best[0]:
                best = (e, float(p), t)
        _, p0, t0 = best
        for k in range(-20, 21):
            p = p0 + k * 0.05
            e, t = best_t(neck_of(p), max(45.0, t0 - 1.0), t0 + 1.0, 0.05)
            if e < best[0]:
                best = (e, p, t)
        return best

    out = None
    for dx in (0.0, 0.04, 0.08, 0.12):
        e, p, t = solve(dx)
        if out is None or e < out[0]:
            out = (e, dx, p, t)
        if e <= 0.003:
            break
    _FW_CACHE[key] = (out[1], out[2], out[3])
    return _FW_CACHE[key]


def car_forehead_wheel(props, ctx=None):
    """The forehead (not the nose, not the horn pad) on the top of the rim: the spine curls forward and the head pitches
    down to meet the rim top. Hands on the rim at +/-78 deg, the left one holding the phone against it, shoulders 4 cm
    down. The spine and head pitch are solved so the forehead point lies on the rim top (acceptance: 1 cm); when the wheel
    is too far for that the pelvis slides forward on the seat, up to 12 cm."""
    D, c = dims(props), merged_ctx(ctx)["car"]
    top = _rim(c, 0)
    neck_pitch = 12
    dx, p, t = _fw_solve(D, c, top, neck_pitch)
    hl = _rim(c, -78)
    return rig(D, pelvis=_car_pelvis(c, dx=dx, dz=-0.02), spine=(p, 0), neck_pitch=neck_pitch, head_pitch=t - p - neck_pitch,
               shoulder_drop=0.04, foot=_car_legs(c), knee_pole=_KP_SIT, hand=(hl, _rim(c, 78)), elbow_pole=_EP_DOWN,
               phone=hl, phone_hand="L")


def forehead_point(j):
    """The forehead contact point of a joint dict (local): where the head touches a rim."""
    pit = j["head_pitch"]
    hh = j["_dims"]["hh"]
    return j["head"] + Vector((math.cos(pit), 0, -math.sin(pit))) * hh * 0.36 + Vector((math.sin(pit), 0, math.cos(pit))) * hh * 0.29


def _stand_legs(D, spread=0.0):
    return (Vector((0.06, -D["hip"], D["ankle"])), Vector((0.06, D["hip"], D["ankle"])))


_KNEEL_PH = Vector((0.22, 0, 0.93))


def _kneel_rig(props, spine=(4, 0), twist=0.0, neck_pitch=6, head_pitch=10, shoulder_drop=0.0, hand_r=None, elbow_pole_r=None):
    """kneel_upright and its variants share knees, pelvis, feet and the left hand with the phone at the chest."""
    D = dims(props)
    h = D["hip"]
    ph = _KNEEL_PH
    ep = _EP_TUCK if elbow_pole_r is None else (_EP_TUCK[0], elbow_pole_r)
    return rig(D, pelvis=Vector((0, 0, D["thigh"] + 0.07)), spine=spine, twist=twist, neck_pitch=neck_pitch,
               head_pitch=head_pitch, shoulder_drop=shoulder_drop,
               foot=(Vector((-0.42, -h, 0.05)), Vector((-0.42, h, 0.05))), knee_pole=((1, 0, -0.8), (1, 0, -0.8)),
               hand=(ph + Vector((0, -0.05, 0)), ph + Vector((0, 0.05, 0)) if hand_r is None else hand_r),
               elbow_pole=ep, phone=ph, phone_hand="both" if hand_r is None else "L")


def kneel_upright(props, ctx=None):
    return _kneel_rig(props)


def kneel_head_back(props, ctx=None):
    """kneel_upright with the head tipped back 8 deg (the neck extends 2 deg, the head 6 deg). Spine, shoulders, hands
    and phone are exactly kneel_upright's: the shoulder drop belongs to the breath track."""
    return _kneel_rig(props, neck_pitch=4, head_pitch=4)


def kneel_reach_stand(props, ctx=None):
    """kneel_upright's knees, pelvis and left hand with the phone at the chest; the torso turns 25 deg to the right
    and bends toward the display stand just far enough for the right hand to reach the socket behind the stand
    (shop ctx: stand_back_edge, socket). The right shoulder dips 4 cm and the head turns toward the socket."""
    D = dims(props)
    sh = merged_ctx(ctx)["shop"]
    sock = _v(sh["socket"])
    best = None
    for roll in range(8, 61):   # least side-bend that gets the hand to the socket (arm 0.59 m, a 0.30 m socket)
        j = _kneel_rig(props, spine=(12, float(roll)), twist=25.0, neck_pitch=6, head_pitch=10, shoulder_drop=0.04,
                       hand_r=sock, elbow_pole_r=(-0.3, 0.5, -1))
        best = j
        if j["reach_err"][1] < 1e-4 and j["reach_err"][0] < 1e-4:
            break
    return look_at(best, sock, max_yaw_deg=45, max_pitch_deg=35)


def scramble_out(props, ctx=None):
    """Ducked in the passenger doorway: crown <= 1.40 m, spine about 52 deg forward, head leading with the eyes ahead.
    The LEFT hand carries the phone, thrust out ahead of the chest; the RIGHT hand pushes off the sill. Right foot on
    the pavement, left foot still on the car floor. Frame 0 of gait scramble."""
    D, c = dims(props), merged_ctx(ctx)["door"]
    h = D["hip"]

    def phone_hand(j):   # ahead of the chest at chest height, a little left of the spine
        return j["chest"] + Vector((0.42, -0.10, -0.03))

    j = rig(D, pelvis=Vector((0.05, 0, 0.60)), spine=(52, -4), neck_pitch=-28, head_pitch=-8, twist=8,
            foot=(Vector((0.34, -h, 0.22)), Vector((-0.22, h, 0.04))), knee_pole=((1, 0, 0.6), (1, 0, 0.6)),
            hand=(phone_hand, _v(c["sill"])),
            elbow_pole=((0, -0.6, -0.5), (-0.6, 0.6, -0.6)))
    j["phone"] = j["handL"] + Vector((0.04, 0, 0.03))
    j["phone_hand"] = "L"
    return j


# kerb (seated on the pavement edge)
def _kerb_base(props, ctx, spine, neck_pitch, head_pitch, hand, elbow_pole, feet=None, knee_pole=None, pelvis_dx=0.0, **kw):
    D, k = dims(props), merged_ctx(ctx)["kerb"]
    z = k["seat_z"]
    h = D["hip"]
    ft = feet or (Vector((0.36, -h, z + 0.04)), Vector((0.36, h, z + 0.04)))
    return rig(D, pelvis=Vector((pelvis_dx, 0, z + 0.09)), spine=spine, neck_pitch=neck_pitch, head_pitch=head_pitch,
               foot=ft, knee_pole=knee_pole or ((0.2, -0.1, 1), (0.2, 0.1, 1)), hand=hand, elbow_pole=elbow_pole, **kw)


def kerb_hunch(props, ctx=None):
    off = Vector((0.12, 0, 0.06))
    return _kerb_base(props, ctx, (32, 0), 16, 0, (lambda j: j["knee"][0] + off + Vector((0, -0.03, 0)),
                                                  lambda j: j["knee"][1] + off + Vector((0, 0.03, 0))),
                      ((0.3, -0.7, -0.6), (0.3, 0.7, -0.6)))


def _crank_geom(k):
    cc, sp = _v(k["crank_center"]), _v(k["crank_spindle"])
    return cc, cc + sp, k["crank_radius"]


def crank_knob(ctx, angle):
    """Local position of the crank knob at `angle` radians (0 = 12 o'clock, + = forward over the top)."""
    k = merged_ctx(ctx)["kerb"]
    _, spindle, r = _crank_geom(k)
    return spindle + Vector((math.sin(angle) * r, 0.0, math.cos(angle) * r))


def _kerb_crank(props, ctx, angle):
    """Clamped cranking base (pelvis and feet as kerb_hunch): the crank body lies across the knees at the kerb crank
    point, the spine leans 22 deg, the right hand is on the knob at `angle` (0 = 12 o'clock) and the head is pitched
    toward the crank. The left hand follows ctx kerb crank_loc: 'lap' (default, clamped: phone held about 0.76 m high
    over the near knee beside the port) or 'hands_both' (under the crank body with the phone flat in the palm)."""
    k = merged_ctx(ctx)["kerb"]
    cc, _, _ = _crank_geom(k)
    knob = crank_knob(ctx, angle)
    loc = k.get("crank_loc") or "lap"
    D = dims(props)
    both = loc == "hands_both"
    if both:
        left = Vector((cc.x - 0.02, cc.y - 0.07, cc.z - 0.06))
    else:
        left = lambda j: Vector((j["knee"][0].x + 0.04, j["knee"][0].y + 0.02, k.get("phone_lap_z", 0.76) - 0.03))  # noqa: E731
    j = _kerb_base(props, ctx, (22, 0), 10, 0, (left, knob),
                   ((0.3, -0.7, -0.6), (0.3, 0.7, -0.6)), feet=None)
    j["phone"] = j["handL"] + (Vector((0.0, 0.0, 0.02)) if both else Vector((0.0, 0.0, 0.03)))
    j["phone_hand"] = "L"
    j["crank_handle"] = knob
    j["crank_angle"] = angle
    j["crank_loc"] = loc
    return look_at(j, cc, max_yaw_deg=20)


def kerb_crank_hold(props, ctx=None):
    return _kerb_crank(props, ctx, 0.0)


def kerb_lean_back(props, ctx=None):
    D, k = dims(props), merged_ctx(ctx)["kerb"]
    z = k["seat_z"]
    return _kerb_base(props, ctx, (-22, 0), 8, 0,
                      (Vector((-0.10, -0.30, z + 0.05)), Vector((-0.10, 0.30, z + 0.05))),
                      ((0, -0.8, -0.6), (0, 0.8, -0.6)),
                      feet=(Vector((0.60, -0.34, z + 0.04)), Vector((0.60, 0.34, z + 0.04))),
                      knee_pole=((0.3, -0.7, 1), (0.3, 0.7, 1)), pelvis_dx=-0.02)


def _lunge(props, ctx, pelvis, spine, neck_pitch, head_pitch, hand, elbow_pole, rfoot_x, lfoot_x):
    D = dims(props)
    h = D["hip"]
    return rig(D, pelvis=pelvis, spine=spine, neck_pitch=neck_pitch, head_pitch=head_pitch,
               foot=(Vector((lfoot_x, -h, 0.04)), Vector((rfoot_x, h, 0.05))),
               knee_pole=((1, 0, 0.8), (1, 0, -1.0)), hand=hand, elbow_pole=elbow_pole)


def lunge_low(props, ctx=None):
    return _lunge(props, ctx, Vector((0.10, 0, 0.42)), (24, 0), -10, -6,
                  (Vector((0.62, -0.20, 0.78)), Vector((0.50, 0.20, 0.72))), ((0, -0.6, -0.6), (0, 0.6, -0.6)),
                  rfoot_x=-0.52, lfoot_x=0.52)


def lunge_reach(props, ctx=None):
    """lunge_low's legs (right knee down, left foot forward). The torso leans about 52 deg in through the passenger
    doorway (crown well under the 1.45 m roof), the left forearm rests on the seat edge with the phone screen up, the
    right hand is on the glovebox latch (well inside the arm's length, elbow not locked) and the eyes are on it."""
    c = merged_ctx(ctx)["door"]
    seat = _v(c["seat_edge"])
    latch = _v(c["latch"])
    hl = seat + Vector((0.16, -0.03, 0.06))

    def solve(h_left):
        return _lunge(props, ctx, Vector((0.24, 0, 0.42)), (52, 0), -18, -8, (h_left, latch),
                      ((0, -0.6, -0.8), (0, 0.5, -0.5)), rfoot_x=-0.38, lfoot_x=0.62)

    for _ in range(14):   # put the middle of the left forearm on the seat edge
        j = solve(hl)
        mid = (j["elbow"][0] + j["handL"]) / 2
        err = seat - mid
        if err.length < 0.002:
            break
        hl = hl + err
    j["phone"] = j["handL"] + Vector((0.0, 0.0, 0.03))
    j["phone_hand"] = "L"
    return look_at(j, latch, max_yaw_deg=40)


# hana at her desk
def _desk(props, ctx, spine, neck_pitch, head_pitch, hand, elbow_pole, twist=0.0, head_yaw=0.0, pelvis_x=-0.04, **kw):
    D, d = dims(props), merged_ctx(ctx)["desk"]
    h = D["hip"]
    return rig(D, pelvis=Vector((pelvis_x, 0, d["seat_z"] + 0.03)), spine=spine, twist=twist, neck_pitch=neck_pitch,
               head_pitch=head_pitch, head_yaw=head_yaw,
               foot=(Vector((0.30, -h, D["ankle"])), Vector((0.30, h, D["ankle"]))), knee_pole=((0.6, 0, 1), (0.6, 0, 1)),
               hand=hand, elbow_pole=elbow_pole, **kw)


def desk_sketch(props, ctx=None):
    d = merged_ctx(ctx)["desk"]
    return _desk(props, ctx, (26, 0), 14, 8, (_v(d["sketchbook_hold"]), _v(d["sketchbook"])),
                 ((0, -0.7, -0.6), (0.2, 0.5, -0.6)), twist=-8)


def desk_notice(props, ctx=None):
    """Seated as desk_sketch with the head turned 25 deg toward the phone (yaw only). The spine lifts from 26 to 14 deg,
    the torso twists 5.5 deg toward the book (6 deg is the limit), the right (pencil) hand stays on the page where the stroke ended (the pelvis slides 2.5 cm forward
    on the chair so the arm still reaches with the spine up) and the left hand stays at the sketchbook edge. Whether the pencil is held or laid is the pencil track's job, not this pose's."""
    d = merged_ctx(ctx)["desk"]
    j = _desk(props, ctx, (14, 0), 8, 6, (_v(d["sketchbook_hold"]), _v(d["sketchbook"])),
              ((0, -0.7, -0.6), (0.2, 0.5, -0.6)), twist=-5.5, head_yaw=25, pelvis_x=-0.015)
    return look_at(j, _v(d["phone"]), yaw=_R(25))


def desk_headphones_off(props, ctx=None):
    D = dims(props)
    off = 0.5 * D["hh"] + 0.035
    cup = lambda s: (lambda j: j["head"] + Vector((0, s * off, 0)))  # noqa: E731
    return _desk(props, ctx, (5, 0), 4, 2, (cup(-1), cup(1)), ((-0.3, -1, -0.2), (-0.3, 1, -0.2)))


def desk_phone_low(props, ctx=None):
    D = dims(props)
    ph = Vector((0.27, 0, 0.82))
    return _desk(props, ctx, (8, 0), 18, 14, (ph + Vector((0, -0.05, 0)), ph + Vector((0, 0.05, 0))), _EP_TUCK,
                 phone=ph, phone_hand="both")


# ----------------------------------------------------------------------------------- gaits
def gait_run_phone_out(t, props, ctx=None, *, speed_mps=4.2, step_f=6, first_step_f=0, fps=24, stance=0.38,
                       stride_cap_m=0.30, lean_deg=14.0, lift_m=0.22):
    """One frame of the run cycle. A foot lands every `step_f` frames (left first at first_step_f); a stance foot
    moves back at the body speed until the stride cap. The phone arm (left) stays rigid out in front and the
    right forearm is tucked; the arms never swing (characters.ren.movement)."""
    D = dims(props)
    cyc = 2.0 * step_f
    c = ((t - first_step_f) / cyc) % 1.0
    T_st = stance * cyc / fps
    E = min(speed_mps * T_st / 2.0, stride_cap_m)
    z0 = D["thigh"] * 2 * 0.955 + D["ankle"] * 0.0
    zp = z0 - 0.03 * math.cos(4 * math.pi * (c - stance / 2))
    feet = []
    for lag in (0.0, 0.5):
        u = (c + lag) % 1.0
        if u < stance:
            x = E - 2 * E * (u / stance)
            z = D["ankle"]
        else:
            s = (u - stance) / (1 - stance)
            x = -E + 2 * E * _smooth(s)
            z = D["ankle"] + lift_m * math.sin(math.pi * s)
        feet.append((x, z))
    h = D["hip"]
    foot = (Vector((feet[0][0], -h, feet[0][1])), Vector((feet[1][0], h, feet[1][1])))
    tw = 4.0 * math.sin(2 * math.pi * c)

    def phone_hand(j):
        return j["shL"] + Vector((0.50, 0.0, -0.05))

    def tuck(j):
        return j["shR"] + Vector((0.12, -0.07, -0.30))

    j = rig(D, pelvis=Vector((0, 0, zp)), spine=(lean_deg, 0), twist=tw, neck_pitch=-lean_deg, foot=foot,
            knee_pole=((1, 0, 0.6), (1, 0, 0.6)), hand=(phone_hand, tuck), elbow_pole=((0, -0.5, -1), (-1, 0.3, -0.4)),
            phone=None, phone_hand="L")
    j["phone"] = j["handL"] + Vector((0.04, 0, 0.03))
    j["stance"] = [((c + lag) % 1.0) < stance for lag in (0.0, 0.5)]
    return j


def gait_scramble(t, props, ctx=None, *, start_f=0, dur_f=20, speed_mps=3.4, step_f=6, fps=24):
    """Crouched exit from the car into the first strides: the scramble_out crouch unfolds over `dur_f` frames
    while the run cycle takes over (speed ramps up). At t >= start_f + dur_f it equals gait_run_phone_out."""
    a = scramble_out(props, ctx)
    u = min(max((t - start_f) / float(dur_f), 0.0), 1.0)
    sp = speed_mps * (0.3 + 0.7 * u)
    r = gait_run_phone_out(t, props, ctx, speed_mps=sp, step_f=step_f, first_step_f=start_f + dur_f * 0.5, fps=fps,
                           lean_deg=14.0 + 36.0 * (1 - u))
    if u >= 1.0:
        return r
    return blend(a, r, u, "ease_in_out")


def crank_angle(t, first_top_f, start_f=None, stop_f=None, cycle_f=24):
    """Handle angle in radians (0 = 12 o'clock) at frame t. Tops fall at first_top_f + k * cycle_f; before
    start_f and after stop_f the handle is held where it is."""
    te = t
    if start_f is not None:
        te = max(te, start_f)
    if stop_f is not None:
        te = min(te, stop_f)
    return (2 * math.pi * ((te - first_top_f) / float(cycle_f))) % (2 * math.pi)


def crank_top_frames(first_top_f, f0, f1, start_f=None, stop_f=None, cycle_f=24):
    """Frames in [f0, f1] on which the handle is at 12 o'clock while it is turning."""
    out = []
    k0 = math.floor((f0 - first_top_f) / cycle_f) - 1
    k1 = math.ceil((f1 - first_top_f) / cycle_f) + 1
    for k in range(k0, k1 + 1):
        f = first_top_f + k * cycle_f
        if f0 <= f <= f1 and (start_f is None or f >= start_f) and (stop_f is None or f <= stop_f):
            out.append(f)
    return out


def gait_crank_turn(t, first_top_f, props, ctx=None, *, start_f=None, stop_f=None, cycle_f=24):
    """Cranking on the kerb: the left hand steadies the crank body, the right hand follows the handle circle
    (12 o'clock at first_top_f, then every `cycle_f` frames). Returns the joints with crank_handle, crank_angle
    and handle_top (True on the frames the handle is at the top)."""
    ang = crank_angle(t, first_top_f, start_f, stop_f, cycle_f)
    j = _kerb_crank(props, ctx, ang)
    tops = crank_top_frames(first_top_f, int(t), int(t), start_f, stop_f, cycle_f)
    j["handle_top"] = bool(tops) and float(t) == int(t)
    return j


GAITS = {"run_phone_out": gait_run_phone_out, "scramble": gait_scramble, "crank_turn": gait_crank_turn}


# ----------------------------------------------------------------------------------- the charging cable (posed, never simulated)
def cable_points(src, dst, n=16, ground_z=None, sag=None):
    """Points of a hanging cable from `src` (source end) to `dst` (the phone end), both world points: a cubic Bezier whose
    inner control points sag below the chord (about 18 % of its length), pushed up so no point is below `ground_z`. The two
    end points are exactly src and dst. Pure and deterministic; the cable is posed per frame, there is no simulation."""
    a, b = Vector(src), Vector(dst)
    L = (b - a).length
    drop = Vector((0.0, 0.0, -(0.18 * L + 0.03 if sag is None else sag)))
    c1, c2 = a + (b - a) * 0.28 + drop, a + (b - a) * 0.72 + drop
    out = []
    for i in range(n + 1):
        t = i / float(n)
        u = 1.0 - t
        p = a * (u ** 3) + c1 * (3 * u * u * t) + c2 * (3 * u * t * t) + b * (t ** 3)
        if ground_z is not None and 0 < i < n:
            p = Vector((p.x, p.y, max(p.z, ground_z + 0.004)))
        out.append(p)
    return out


# ----------------------------------------------------------------------------------- registry
POSES = {
    ("ren", "car_upright"): car_upright,
    ("ren", "car_reach_up"): car_reach_up,
    ("ren", "car_phone_up"): car_phone_up,
    ("ren", "car_sag"): car_sag,
    ("ren", "car_lean_glovebox"): car_lean_glovebox,
    ("ren", "car_recline"): car_recline,
    ("ren", "car_forehead_wheel"): car_forehead_wheel,
    ("ren", "run_phone_out"): lambda props, ctx=None: gait_run_phone_out(0, props, ctx),
    ("ren", "scramble_out"): scramble_out,
    ("ren", "kneel_upright"): kneel_upright,
    ("ren", "kneel_reach_stand"): kneel_reach_stand,
    ("ren", "kneel_head_back"): kneel_head_back,
    ("ren", "kerb_hunch"): kerb_hunch,
    ("ren", "kerb_crank_hold"): kerb_crank_hold,
    ("ren", "kerb_lean_back"): kerb_lean_back,
    ("ren", "lunge_low"): lunge_low,
    ("ren", "lunge_reach"): lunge_reach,
    ("hana", "desk_sketch"): desk_sketch,
    ("hana", "desk_notice"): desk_notice,
    ("hana", "desk_headphones_off"): desk_headphones_off,
    ("hana", "desk_phone_low"): desk_phone_low,
}


def pose(cid, ref, props, ctx=None):
    """The joint dict for a vocabulary pose. Unknown (cid, ref) is a builder bug: KeyError with the known names."""
    try:
        fn = POSES[(cid, ref)]
    except KeyError:
        known = sorted(r for c, r in POSES if c == cid)
        raise KeyError(f"no pose geometry for {cid}/{ref}; known: {known}") from None
    return fn(props, ctx)
