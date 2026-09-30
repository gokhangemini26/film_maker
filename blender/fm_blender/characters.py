"""Proxy characters: toon capsule-limb figures driven by resolved proportions + pose presets."""
import math

from mathutils import Vector

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


def figure(col, cid, canon, props, pos, facing, pose, hold=False):
    """Build a proxy figure. pos = (x,y,z) of feet/base; facing = unit XY Vector; pose in stand|kneel|sit_car|sit_kerb|sit_chair."""
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
    phone = chest + f * 0.24 + Vector((0, 0, -0.16))
    if pose == "sit_car":
        phone = hipc + f * 0.22 + Vector((0, 0, 0.5))
    elif pose == "sit_kerb":
        phone = hipc + f * 0.18 + Vector((0, 0, 0.32))
    if hold and pose in ("sit_car", "sit_kerb", "stand", "sit_chair", "kneel"):
        handL, handR = phone - r * 0.05, phone + r * 0.05
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
    eye = U.flat(cc["eyes"])
    yaw = math.atan2(f.y, f.x)
    fdict = canon.get(f"characters.{cid}.face") or {}
    fv = lambda k: str(fdict.get(k) or "")  # noqa: E731
    style = fv("hair_style")
    hexs = lambda h: {"hex": h, "linear": U.lin(h)}  # noqa: E731
    up = Vector((0, 0, 1))
    # Hair: cap is always present; bob / fringe / tuft come from the canon hair_style string.
    if "bob" in style:  # jaw-length rounded bob: side and back masses down to the jaw line
        for i, sgn in enumerate((-1, 1)):
            U.sphere(f"{cid}_bob{i}", hh * 0.24, head + r * sgn * hh * 0.4 - f * hh * 0.05 - up * hh * 0.12, col, hair, scale=(1.0, 0.8, 1.35))
        U.sphere(f"{cid}_bobback", hh * 0.42, head - f * hh * 0.2 - up * hh * 0.1, col, hair, scale=(0.75, 1.0, 1.0))
    if "fringe" in style:  # short straight fringe: a flat lock across the forehead; sits above the brows when the canon says so
        above = "above_brows" in style
        fz = hh * (0.32 if above else 0.28)
        fr = U.sphere(f"{cid}_fringe", hh * 0.36, head + f * hh * 0.17 + up * fz, col, hair, scale=(0.55, 1.15, 0.42))
        fr.rotation_euler = (0, 0, yaw)
    # Brows (canon colour; straight for 'straight', arched for 'arched'), mouth line (small dark flat shape).
    brow_col = U.flat(cc["brows"] or hexs("#3A2E2A"))
    arched = "arched" in fv("brows")
    for i, sgn in enumerate((-1, 1)):
        bp = head + f * hh * 0.42 + r * sgn * hh * 0.17 + up * hh * (0.125 if arched else 0.115)
        b = U.box(f"{cid}_brow{i}", (0.008, hh * 0.19, 0.008), bp, col, brow_col, rot=(0, 0, yaw))
        b.rotation_euler = (arched * sgn * 0.0, 0, yaw)
    mouth_w = hh * (0.13 if "small" in fv("mouth") or "line" in fv("mouth") else 0.16)
    if not P.get("mouth_hidden"):
      U.box(f"{cid}_mouth", (0.01, mouth_w, 0.006), head + f * hh * 0.385 - up * hh * 0.2, col, U.flat(hexs("#6B4444")), rot=(0, 0, yaw))
    for i, sgn in enumerate((-1, 1)):
        U.sphere(f"{cid}_eye{i}", 0.012, head + f * hh * 0.42 + r * sgn * hh * 0.17 + Vector((0, 0, hh * 0.02)), col, eye)
    tuft = P.get("tuft_extra_m")
    if tuft or "tuft" in style:  # stubborn crown tuft: thin spike leaning slightly back, tapered by a tip ball
        tuft = tuft or 0.04
        crown = head + up * hh * 0.56
        tip = crown + up * (tuft + 0.03) - f * 0.012
        U.between(f"{cid}_tuft", crown, tip, 0.015, col, hair, segs=8)
        U.sphere(f"{cid}_tufttip", 0.011, tip, col, hair)
    # Jacket cues (open, hip length): pale T-shirt centre strip, two chest patch pockets, small collar.
    if canon.get(f"characters.{cid}.wardrobe.jacket"):
        trad = limb * 2.6
        tee = U.toon(cc["tshirt"] or hexs("#EAE2D3"))
        U.between(f"{cid}_centrestrip", hipc + f * trad * 0.85, chest + f * trad * 0.85, 0.034, col, tee, segs=8)
        dark = {"hex": cc["top"]["hex"], "linear": [c * 0.8 for c in list(cc["top"]["linear"])[:3]]}
        pk = U.toon(dark)
        for i, sgn in enumerate((-1, 1)):
            U.box(f"{cid}_pocket{i}", (0.012, 0.06, 0.065), chest + f * trad * 0.95 + r * sgn * sh * 0.55 - up * 0.05, col, pk, rot=(0, 0, yaw))
            U.box(f"{cid}_collar{i}", (0.012, 0.05, 0.045), neck + f * 0.05 + r * sgn * 0.05 - up * 0.03, col, cloth, rot=(0, 0, yaw))
    # Over-ear headphones (canon wardrobe.headphones): two cups + band, on the head or resting round the neck.
    hp = canon.get(f"characters.{cid}.wardrobe.headphones")
    if hp:
        shell = U.toon(_dig(hp, "shell_color") or hexs("#EFE8DC"))
        cush = U.toon(_dig(hp, "cushion_color") or hexs("#CFC7BE"))
        down = str(P.get("headphones_state", "on")) == "down"
        if not down:
            lat, cz = hh * 0.5, head
            for i, sgn in enumerate((-1, 1)):
                cp = cz + r * sgn * (lat + 0.02) - f * hh * 0.02
                U.cyl(f"{cid}_cup{i}", hh * 0.27, 0.045, cp, col, shell, rot=(math.pi / 2, 0, yaw))
                U.cyl(f"{cid}_cush{i}", hh * 0.24, 0.02, cp - r * sgn * 0.03, col, cush, rot=(math.pi / 2, 0, yaw))
            pts = [head + r * math.cos(t) * (lat + 0.02) + up * (math.sin(t) * hh * 0.64) - f * hh * 0.02 for t in [k * math.pi / 6 for k in range(7)]]
            for k in range(6):
                U.between(f"{cid}_band{k}", pts[k], pts[k + 1], 0.011, col, shell, segs=8)
        else:
            nc = neck - up * 0.03
            for i, sgn in enumerate((-1, 1)):
                cp = nc + r * sgn * 0.11 + f * 0.05
                U.cyl(f"{cid}_cup{i}", hh * 0.27, 0.045, cp, col, shell, rot=(math.pi / 2, 0, yaw + sgn * 0.5))
            back = [nc + r * math.cos(t) * 0.11 - f * math.sin(t) * 0.09 + f * 0.05 * (1 - math.sin(t)) for t in [k * math.pi / 4 for k in range(5)]]
            for k in range(4):
                U.between(f"{cid}_band{k}", back[k], back[k + 1], 0.011, col, shell, segs=8)
    return {"head": head, "chest": chest, "hands": (handL + handR) / 2, "phone": phone, "facing": f, "hip": hipc}
