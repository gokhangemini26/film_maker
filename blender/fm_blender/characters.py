"""Proxy characters: toon capsule-limb figures driven by resolved proportions + pose presets."""
import math

from mathutils import Matrix, Vector

from . import poses as PS
from . import util as U


def _dig(v, *path):
    for p in path:
        if not isinstance(v, dict) or p not in v:
            return None
        v = v[p]
    return v if isinstance(v, dict) and "hex" in v else None


def _cols(canon, cid):
    face = canon.get(f"characters.{cid}.face") or {}
    out = canon.get(f"characters.{cid}.wardrobe.outfit") or {}
    jac = canon.get(f"characters.{cid}.wardrobe.jacket") or {}
    d = lambda h: {"hex": h, "linear": U.lin(h)}  # noqa: E731
    return {
        "skin": _dig(face, "colors", "skin") or d("#EAC7AB"),
        "hair": _dig(face, "colors", "hair") or d("#3A2F2A"),
        "eyes": _dig(face, "colors", "eyes") or d("#2A2230"),
        "brows": _dig(face, "colors", "brows"),
        "tshirt": _dig(out, "tshirt", "color"),
        "top": _dig(jac, "color") or _dig(out, "top", "color") or _dig(out, "tshirt", "color") or d("#8F809A"),
        "legs": _dig(out, "trousers", "color") or d("#5A4A6A"),
        "shoes": _dig(out, "shoes", "color") or d("#ECE7DE"),
    }


def pick(hs, i, default):
    return hs[i % len(hs)] if hs else {"hex": default, "linear": U.lin(default)}


def aim_head(head, facing, target, max_yaw_deg=75.0, max_pitch_deg=50.0):
    """(yaw, pitch) radians that turn a head at `head` (world) toward `target` (world) for a figure facing `facing`.
    yaw is positive toward the figure's right, pitch positive looking down; both clamped to a human range."""
    f = Vector((facing.x, facing.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))
    d = Vector(target) - Vector(head)
    y, p = PS.look_angles(Vector((0, 0, 0)), Vector((d.dot(f), d.dot(r), d.z)))
    return (max(-math.radians(max_yaw_deg), min(math.radians(max_yaw_deg), y)),
            max(-math.radians(max_pitch_deg), min(math.radians(max_pitch_deg), p)))


def figure(col, cid, canon, props, pos, facing, pose=None, hold=False, joints=None, face=None, look=None, lids=1.0):
    """Build a proxy figure. pos = (x,y,z) of feet/base; facing = unit XY Vector.

    pose   one of the stances stand|kneel|sit_car|sit_kerb|sit_chair (the original behaviour, unchanged), or
    joints a joint dict from poses.py (local frame, see poses.py) which replaces the stance entirely.
    face   a vocabulary face ref (poses.FACE_SHAPES) for brows, eyes and mouth; None keeps joints['face'] or neutral.
    look   a WORLD point the head turns toward (clamped); None keeps the pose's own head yaw and pitch.
    lids   0..1 factor on the face's eye openness (v2 lids track: open 1.0, low 0.55, closed 0.0). It scales the eye
           height only, so the gaze (the head's aim) is untouched; 1.0 builds exactly what it always built."""
    P = props
    H = P["height_m"]
    hh = P.get("head_height_m", H / P.get("head_count", 6.5))
    leg = P.get("leg_length_m", H * 0.49)
    sh = P.get("shoulder_width_m", H * 0.24) / 2
    hip = P.get("hip_width_m", H * 0.19) / 2
    cc = _cols(canon, cid)
    skin, cloth, cloth2, hair = U.toon(cc["skin"]), U.toon(cc["top"]), U.toon(cc["legs"]), U.toon(cc["hair"])
    f = Vector((facing.x, facing.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))  # figure's right
    base = Vector(pos)
    up = Vector((0, 0, 1))

    def W(fw, rt, up_):  # figure-local -> world
        return base + f * fw + r * rt + Vector((0, 0, up_))

    elbows = None
    if joints is not None:
        Wv = lambda v: W(v.x, v.y, v.z)  # noqa: E731
        hipL, hipR, chest, neck, head, shL, shR, handL, handR = (Wv(joints[k]) for k in (
            "hipL", "hipR", "chest", "neck", "head", "shL", "shR", "handL", "handR"))
        knee, foot, elbows = [Wv(v) for v in joints["knee"]], [Wv(v) for v in joints["foot"]], [Wv(v) for v in joints["elbow"]]
        hipc = (hipL + hipR) / 2
        phone = Wv(joints["phone"]) if joints.get("phone") is not None else (handL + handR) / 2
    else:
        torso_len = H - leg - hh * 1.15
        if pose == "kneel":
            hipz = leg * 0.5
            knee = [W(0.25, -hip, 0.05), W(-0.02, hip, 0.05)]
            foot = [W(-0.3, -hip, 0.05), W(-0.32, hip, 0.03)]
            hipL, hipR = W(-0.05, -hip, hipz), W(-0.05, hip, hipz)
            lean = 0.05
        elif pose == "sit_car":
            seat = P.get("seated_on_car_seat", {}).get("seat_height_m", 0.45)
            hipL, hipR = W(0, -hip, seat + 0.05), W(0, hip, seat + 0.05)
            knee = [W(0.42, -hip, seat + 0.15), W(0.42, hip, seat + 0.15)]
            foot = [W(0.5, -hip, 0.15), W(0.5, hip, 0.15)]
            lean = -0.34
        elif pose == "sit_kerb":
            seat = P.get("seated_on_kerb", {}).get("seat_surface_z_m", 0.12)
            hipL, hipR = W(0, -hip, seat + 0.05), W(0, hip, seat + 0.05)
            knee = [W(0.4, -hip, seat + 0.45), W(0.4, hip, seat + 0.45)]
            foot = [W(0.75, -hip, seat), W(0.75, hip, seat)]
            lean = -0.05
        elif pose == "sit_chair":
            seat = 0.46
            hipL, hipR = W(0, -hip, seat + 0.05), W(0, hip, seat + 0.05)
            knee = [W(0.42, -hip, seat + 0.05), W(0.42, hip, seat + 0.05)]
            foot = [W(0.45, -hip, 0.03), W(0.45, hip, 0.03)]
            lean = 0.05
        else:
            hipL, hipR = W(0, -hip, leg), W(0, hip, leg)
            knee = [W(0.02, -hip, leg / 2), W(0.02, hip, leg / 2)]
            foot = [W(0.06, -hip, 0.04), W(0.06, hip, 0.04)]
            lean = 0.0
        hipc = (hipL + hipR) / 2
        chest = hipc + f * lean * torso_len + Vector((0, 0, torso_len * 0.95))
        neck = chest + Vector((0, 0, 0.06)) + f * lean * 0.05
        head = neck + Vector((0, 0, hh * 0.55))
        shL, shR = chest - r * sh, chest + r * sh
        reach = P.get("arm_span_m", H) / 2 - sh
        handL = shL + Vector((0, 0, -reach * 0.85)) + f * 0.05
        handR = shR + Vector((0, 0, -reach * 0.85)) + f * 0.05
        if pose in ("sit_kerb", "kneel"):
            handL, handR = knee[0] + Vector((0, 0, 0.1)), knee[1] + Vector((0, 0, 0.1))
        elif pose == "sit_chair":
            handL, handR = chest + f * 0.35 - r * 0.15 - Vector((0, 0, 0.35)), chest + f * 0.35 + r * 0.15 - Vector((0, 0, 0.35))
        phone = chest + f * 0.24 + Vector((0, 0, -0.16))
        if pose == "sit_car":
            phone = hipc + f * 0.22 + Vector((0, 0, 0.5))
        elif pose == "sit_kerb":
            phone = hipc + f * 0.18 + Vector((0, 0, 0.32))
        if hold and pose in ("sit_car", "sit_kerb", "stand", "sit_chair", "kneel"):
            handL, handR = phone - r * 0.05, phone + r * 0.05
    limb = 0.055 if H > 1.6 else 0.05
    # torso frame (for the jacket cues): the stance code keeps the body frame; a joint pose follows the spine
    if joints is not None:
        nu = (chest - hipc).normalized()
        nf = (f - nu * f.dot(nu)).normalized()
        nr = (shR - shL).normalized()
    else:
        nu, nf, nr = up, f, r
    U.between(f"{cid}_torso", hipc, chest, limb * 2.6, col, cloth)
    U.between(f"{cid}_neck", chest, neck + Vector((0, 0, 0.02)), 0.035, col, skin)
    for i, (hp, kn, ft) in enumerate(zip((hipL, hipR), knee, foot)):
        U.between(f"{cid}_thigh{i}", hp, kn, limb * 1.1, col, cloth2)
        U.between(f"{cid}_shin{i}", kn, ft, limb, col, cloth2)
        if joints is not None:  # a shoe, so the foot direction and the ground contact read
            shoe = U.toon(cc["shoes"])
            U.between(f"{cid}_shoe{i}", ft - f * 0.04 - Vector((0, 0, 0.005)), ft + f * 0.13 - Vector((0, 0, 0.02)), limb * 0.95, col, shoe)
    for i, (s, hnd) in enumerate(((shL, handL), (shR, handR))):
        if elbows is not None:
            el = elbows[i]
        else:
            el = (s + hnd) / 2 + Vector((0, 0, -0.03)) - f * 0.03
        U.between(f"{cid}_uarm{i}", s, el, limb * 0.9, col, cloth)
        U.between(f"{cid}_farm{i}", el, hnd, limb * 0.8, col, skin)
        U.sphere(f"{cid}_hand{i}", P.get("hand_length_m", 0.18) * 0.3, hnd, col, skin)
    # head frame: the body frame unless the pose or `look` turns it (yaw + toward the right, pitch + looking down)
    hyaw = joints.get("head_yaw", 0.0) if joints is not None else 0.0
    hpit = joints.get("head_pitch", 0.0) if joints is not None else 0.0
    if look is not None:
        hyaw, hpit = aim_head(head, f, look)
    yaw = math.atan2(f.y, f.x)
    if hyaw == 0.0 and hpit == 0.0:
        hf, hr, hu = f, r, up
        rot = lambda roll=0.0: (roll, 0.0, yaw)  # noqa: E731
    else:
        cy, sy, cp, sp = math.cos(hyaw), math.sin(hyaw), math.cos(hpit), math.sin(hpit)
        hf = f * (cy * cp) + r * (sy * cp) - up * sp
        hr = -f * sy + r * cy
        hu = f * (sp * cy) + r * (sp * sy) + up * cp
        hm = Matrix(((hf.x, -hr.x, hu.x), (hf.y, -hr.y, hu.y), (hf.z, -hr.z, hu.z)))
        rot = lambda roll=0.0: tuple(  # noqa: E731
            (hm @ Matrix.Rotation(roll, 3, "X")).to_euler())
    hd = U.sphere(f"{cid}_head", hh * 0.5, head, col, skin, scale=(0.85, 0.95, 1.0))
    hd.rotation_euler = (0, 0, yaw) if (hyaw == 0.0 and hpit == 0.0) else rot()
    hair_o = U.sphere(f"{cid}_hair", hh * 0.52, head + hu * hh * 0.14 - hf * hh * 0.1, col, hair, scale=(0.95, 1.0, 0.85))
    pitched = hpit < 0.0  # tipped back (+ pitch = looking down keeps its authored face exactly)
    wt = min(1.0, -hpit / 0.35) if pitched else 0.0  # fades the surface fit in over the first 20 deg, so no pop
    if pitched:  # the hair cap turns with the head, so the hairline stays where the face is
        hair_o.rotation_euler = rot()

    def brow_z(lat, z):
        """Pitched head: the brow height clamped to the forehead skin, below the hairline (where the hair cap pokes out of the
        head ellipsoid), so a raised brow never floats above the head or vanishes into the hair. Unpitched: unchanged."""
        if not pitched:
            return z
        zz = 0.02
        while zz < z:
            nz = zz + 0.005
            qs, qh = 1.0 - (lat / 0.475) ** 2 - (nz / 0.5) ** 2, 1.0 - (lat / 0.52) ** 2 - ((nz - 0.14) / 0.442) ** 2
            if qs <= 0.0 or (qh > 0.0 and -0.1 + 0.494 * math.sqrt(qh) > 0.425 * math.sqrt(qs) - 0.004):
                break
            zz = nz
        return z + wt * (min(z, zz) - z)

    def face_fwd(lat, up_, dflt, lift=0.006):
        """Forward offset (in head frame) of a face decal at (lat, up_) head-height fractions. A pitched head sits the decal ON
        the head ellipsoid (semi-axes .425/.475/.5 head heights) or the hair cap in front of it, so brows, eyes and mouth ride the face surface, never above
        it; an unpitched head keeps the authored offset exactly."""
        if not pitched:
            return dflt
        q = 1.0 - (lat / 0.475) ** 2 - (up_ / 0.5) ** 2
        xs = 0.425 * math.sqrt(max(q, 0.0))
        qh = 1.0 - (lat / 0.52) ** 2 - ((up_ - 0.14) / 0.442) ** 2  # the hair cap's front, so a raised brow rides ON the hairline
        xh = -0.1 + 0.494 * math.sqrt(max(qh, 0.0)) if qh > 0 else xs
        return dflt + wt * (min(dflt, max(xs, xh) + lift) - dflt)
    eye = U.flat(cc["eyes"])
    fdict = canon.get(f"characters.{cid}.face") or {}
    fv = lambda k: str(fdict.get(k) or "")  # noqa: E731
    style = fv("hair_style")
    hexs = lambda h: {"hex": h, "linear": U.lin(h)}  # noqa: E731
    fs_name = face if face is not None else (joints or {}).get("face")
    fs = PS.FACE_SHAPES.get(fs_name) if fs_name else None
    fs = fs or PS.FACE_SHAPES["neutral"]
    # Hair: cap is always present; bob / fringe / tuft come from the canon hair_style string.
    if "bob" in style:  # jaw-length rounded bob: side and back masses down to the jaw line
        for i, sgn in enumerate((-1, 1)):
            U.sphere(f"{cid}_bob{i}", hh * 0.24, head + hr * sgn * hh * 0.4 - hf * hh * 0.05 - hu * hh * 0.12, col, hair, scale=(1.0, 0.8, 1.35))
        U.sphere(f"{cid}_bobback", hh * 0.42, head - hf * hh * 0.2 - hu * hh * 0.1, col, hair, scale=(0.75, 1.0, 1.0))
    if "fringe" in style:  # short straight fringe: a flat lock across the forehead; sits above the brows when the canon says so
        above = "above_brows" in style
        fz = hh * (0.32 if above else 0.28)
        fr = U.sphere(f"{cid}_fringe", hh * 0.36, head + hf * hh * 0.17 + hu * fz, col, hair, scale=(0.55, 1.15, 0.42))
        fr.rotation_euler = rot()
    # Brows (canon colour; straight for 'straight', arched for 'arched'), mouth line (small dark flat shape).
    brow_col = U.flat(cc["brows"] or hexs("#3A2E2A"))
    arched = "arched" in fv("brows")
    for i, sgn in enumerate((-1, 1)):
        bz = brow_z(0.17, (0.125 if arched else 0.115) + fs["brow_dy"])
        bp = head + hf * hh * face_fwd(0.17, bz, 0.42) + hr * sgn * hh * 0.17 + hu * hh * bz
        b = U.box(f"{cid}_brow{i}", (0.008, hh * 0.19, 0.008), bp, col, brow_col, rot=rot())
        b.rotation_euler = rot(sgn * fs["brow_tilt"])
    mouth_w = hh * (0.13 if "small" in fv("mouth") or "line" in fv("mouth") else 0.16) * fs["mouth_w"]
    if not P.get("mouth_hidden"):
        mc = head + hf * hh * face_fwd(0.0, -0.2, 0.385, 0.004) - hu * hh * 0.2
        mm = U.flat(hexs("#6B4444"))
        if fs["smile"] == 0.0:
            U.box(f"{cid}_mouth", (0.01, mouth_w, 0.006 * fs["mouth_h"]), mc, col, mm, rot=rot())
        else:  # a smile or a frown: two half lines, outer ends lifted (smile > 0) or dropped
            a_ = fs["smile"]
            for i, sgn in enumerate((-1, 1)):
                cp_ = mc + hr * sgn * mouth_w * 0.25 + hu * (mouth_w * 0.25 * math.sin(abs(a_)) * (1 if a_ > 0 else -1) * 0.5)
                U.box(f"{cid}_mouth{i}", (0.01, mouth_w * 0.5, 0.006 * fs["mouth_h"]), cp_, col, mm, rot=rot(-sgn * a_))
    ez = fs["eye"] * float(lids)
    for i, sgn in enumerate((-1, 1)):
        U.sphere(f"{cid}_eye{i}", 0.012, head + hf * hh * face_fwd(0.17, 0.02, 0.42, 0.0) + hr * sgn * hh * 0.17 + hu * hh * 0.02, col, eye,
                 **({} if ez == 1.0 else {"scale": (1.0, 1.0, max(ez, 0.12))}))
    tuft = P.get("tuft_extra_m")
    if tuft or "tuft" in style:  # stubborn crown tuft: thin spike leaning slightly back, tapered by a tip ball
        tuft = tuft or 0.04
        crown = head + hu * hh * 0.56
        tip = crown + hu * (tuft + 0.03) - hf * 0.012
        U.between(f"{cid}_tuft", crown, tip, 0.015, col, hair, segs=8)
        U.sphere(f"{cid}_tufttip", 0.011, tip, col, hair)
    # Jacket cues (open, hip length): pale T-shirt centre strip, two chest patch pockets, small collar.
    if canon.get(f"characters.{cid}.wardrobe.jacket"):
        trad = limb * 2.6
        tee = U.toon(cc["tshirt"] or hexs("#EAE2D3"))
        U.between(f"{cid}_centrestrip", hipc + nf * trad * 0.85, chest + nf * trad * 0.85, 0.034, col, tee, segs=8)
        dark = {"hex": cc["top"]["hex"], "linear": [c * 0.8 for c in list(cc["top"]["linear"])[:3]]}
        pk = U.toon(dark)
        for i, sgn in enumerate((-1, 1)):
            U.box(f"{cid}_pocket{i}", (0.012, 0.06, 0.065), chest + nf * trad * 0.95 + nr * sgn * sh * 0.55 - nu * 0.05, col, pk, rot=(0, 0, yaw))
            U.box(f"{cid}_collar{i}", (0.012, 0.05, 0.045), neck + nf * 0.05 + nr * sgn * 0.05 - nu * 0.03, col, cloth, rot=(0, 0, yaw))
    # Over-ear headphones (canon wardrobe.headphones): two cups + band, on the head or resting round the neck.
    hp = canon.get(f"characters.{cid}.wardrobe.headphones")
    if hp:
        shell = U.toon(_dig(hp, "shell_color") or hexs("#EFE8DC"))
        cush = U.toon(_dig(hp, "cushion_color") or hexs("#CFC7BE"))
        down = str(P.get("headphones_state", "on")) == "down"
        if not down:
            lat, cz = hh * 0.5, head
            for i, sgn in enumerate((-1, 1)):
                cp = cz + hr * sgn * (lat + 0.02) - hf * hh * 0.02
                U.cyl(f"{cid}_cup{i}", hh * 0.27, 0.045, cp, col, shell, rot=rot(math.pi / 2))
                U.cyl(f"{cid}_cush{i}", hh * 0.24, 0.02, cp - hr * sgn * 0.03, col, cush, rot=rot(math.pi / 2))
            pts = [head + hr * math.cos(t) * (lat + 0.02) + hu * (math.sin(t) * hh * 0.64) - hf * hh * 0.02 for t in [k * math.pi / 6 for k in range(7)]]
            for k in range(6):
                U.between(f"{cid}_band{k}", pts[k], pts[k + 1], 0.011, col, shell, segs=8)
        else:
            nc = neck - nu * 0.03
            for i, sgn in enumerate((-1, 1)):
                cp = nc + nr * sgn * 0.11 + nf * 0.05
                U.cyl(f"{cid}_cup{i}", hh * 0.27, 0.045, cp, col, shell, rot=(math.pi / 2, 0, yaw + sgn * 0.5))
            back = [nc + nr * math.cos(t) * 0.11 - nf * math.sin(t) * 0.09 + nf * 0.05 * (1 - math.sin(t)) for t in [k * math.pi / 4 for k in range(5)]]
            for k in range(4):
                U.between(f"{cid}_band{k}", back[k], back[k + 1], 0.011, col, shell, segs=8)
    info = {"head": head, "chest": chest, "hands": (handL + handR) / 2, "phone": phone, "facing": f, "hip": hipc}
    info.update({"knee": knee, "foot": foot, "elbow": elbows, "head_forward": hf, "head_yaw": hyaw, "head_pitch": hpit,
                 "handL": handL, "handR": handR})
    return info
