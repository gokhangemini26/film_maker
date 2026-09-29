"""Proxy characters: toon capsule-limb figures driven by resolved proportions + pose presets."""
import math

from mathutils import Vector

from . import util as U


def _cols(canon, cid):
    ent = canon.get(f"characters.{cid}.face") or {}
    hs = []

    def walk(v):
        if isinstance(v, dict):
            if "hex" in v and "linear" in v:
                hs.append(v)
            else:
                for x in v.values():
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    for k in (f"characters.{cid}.face", f"characters.{cid}.wardrobe.outfit", f"characters.{cid}.wardrobe.jacket",
              f"characters.{cid}.silhouette"):
        walk(canon.get(k))
    return hs


def pick(hs, i, default):
    return hs[i % len(hs)] if hs else {"hex": default, "linear": U.lin(default)}


def figure(col, cid, canon, props, pos, facing, pose):
    """Build a proxy figure. pos = (x,y,z) of feet/base; facing = unit XY Vector; pose in stand|kneel|sit_car|sit_kerb|sit_chair."""
    P = props
    H = P["height_m"]
    hh = P.get("head_height_m", H / P.get("head_count", 6.5))
    leg = P.get("leg_length_m", H * 0.49)
    sh = P.get("shoulder_width_m", H * 0.24) / 2
    hip = P.get("hip_width_m", H * 0.19) / 2
    hs = _cols(canon, cid)
    skin = U.toon(pick(hs, 0, "#E8B994"))
    cloth = U.toon(pick(hs, 1, "#8F809A"))
    cloth2 = U.toon(pick(hs, 2, "#5A4A6A"))
    hair = U.toon(pick(hs, 3, "#2B2430"))
    f = Vector((facing.x, facing.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))  # figure's right
    base = Vector(pos)

    def W(fw, rt, up):  # figure-local -> world
        return base + f * fw + r * rt + Vector((0, 0, up))

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
    limb = 0.055 if H > 1.6 else 0.05
    U.between(f"{cid}_torso", hipc, chest, limb * 2.6, col, cloth)
    U.between(f"{cid}_neck", chest, neck + Vector((0, 0, 0.02)), 0.035, col, skin)
    for i, (hp, kn, ft) in enumerate(zip((hipL, hipR), knee, foot)):
        U.between(f"{cid}_thigh{i}", hp, kn, limb * 1.1, col, cloth2)
        U.between(f"{cid}_shin{i}", kn, ft, limb, col, cloth2)
    for i, (s, hnd) in enumerate(((shL, handL), (shR, handR))):
        el = (s + hnd) / 2 + Vector((0, 0, -0.03)) - f * 0.03
        U.between(f"{cid}_uarm{i}", s, el, limb * 0.9, col, cloth)
        U.between(f"{cid}_farm{i}", el, hnd, limb * 0.8, col, skin)
        U.sphere(f"{cid}_hand{i}", P.get("hand_length_m", 0.18) * 0.3, hnd, col, skin)
    hd = U.sphere(f"{cid}_head", hh * 0.5, head, col, skin, scale=(0.85, 0.95, 1.0))
    hd.rotation_euler = (0, 0, math.atan2(f.y, f.x))
    U.sphere(f"{cid}_hair", hh * 0.52, head + Vector((0, 0, hh * 0.14)) - f * hh * 0.1, col, hair, scale=(0.95, 1.0, 0.85))
    eye = U.flat({"hex": "#2A2230", "linear": U.lin("#2A2230")})
    for i, sgn in enumerate((-1, 1)):
        U.sphere(f"{cid}_eye{i}", 0.012, head + f * hh * 0.42 + r * sgn * hh * 0.17 + Vector((0, 0, hh * 0.02)), col, eye)
    tuft = P.get("tuft_extra_m")
    if tuft:
        U.sphere(f"{cid}_tuft", 0.03, head + Vector((0, 0, hh * 0.62 + tuft)), col, hair)
    return {"head": head, "chest": chest, "hands": (handL + handR) / 2, "facing": f}
