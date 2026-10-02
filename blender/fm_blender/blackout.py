"""SC03 blackout look (canon look.lighting.sc03_blackout_render): a power cut, not a dimmer.

Why this module exists: scaling every material's shadow colour by a scalar keeps the pastel hues and lifts them to a
neutral grey veil. The spec REPLACES the colours instead:
  * every shop source is off (lights 0 W, panel / fridge-glass / fascia emissives swapped to a dark NON-emissive
    "off" material, never hidden, so the fridges stay as dark shapes), world strength 0, no exposure or grade lift;
  * the shadow tone of every set surface becomes the blackout ambient (#1E2030), merchandise, fridges, posters, the
    counter, Ren and the cable become the film floor (#1B1C29);
  * the only lit tones are inside the phone's pool: lit = mix(base, base x key colour, 0.30) where a surface still
    crosses the cel threshold (it only does within about 0.5 m of the screen);
  * the door glass is a small warm rectangle (#C9A77E or darker) in the shots that face the shop front.

Everything is read from the shot's `lighting` block when the cinematographer has added `render_spec` / `ambient` /
`floor` / `exposure_target` there, and otherwise from the canon (look.lighting.sc03_blackout_render, look.color.scene.sc03,
look.exposure.value_structure, look.color.phone_glow), so the builder works either way.

Materials are never mutated: a blackout variant of each toon material is made once and assigned per object, and
`apply(..., on=False)` puts the originals back, so every other shot renders exactly as before.
"""
from __future__ import annotations

import re

AMBIENT_HEX = "#1E2030"      # look.color.scene.sc03 blackout.dominant
FLOOR_HEX = "#1B1C29"        # look.exposure.value_structure film_floor_hex
KEY_HEX = "#FFF1DE"          # look.color.phone_glow
DOOR_HEX = "#C9A77E"         # look.color.scene.sc03 blackout.door_rectangle
LIT_MIX = 0.30               # lit tone = mix(base, base x key, 0.30)
POOL_W = 50.0                # phone-glow point light power: calibrated so the cel threshold is crossed within ~0.5 m
LIT_PHONE_W = 15.0           # the phone light while the shop is still lit (before the cut): unchanged from the old builder
DOOR_STRENGTH = 0.85         # emission strength of the door rectangle: darker than its hex, never brighter
DEFAULT_SHOTS = ("SC03_SH050", "SC03_SH060", "SC03_SH070")
DEFAULT_DOOR_SHOTS = ("SC03_SH070",)

# objects of the shop set that are merchandise-like (film floor), by name; every other shop object is a set surface
_MERCH = re.compile(r"^(stock|wall_stock|fridge\d|poster|shop_counter|shop_till|display_stand_tin|gondola\d+_end)")
_HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def _hex(v):
    """First '#RRGGBB' found in a resolved canon value (str / {'hex':..} / nested), else None."""
    if isinstance(v, str):
        m = _HEX.search(v)
        return m.group(0).upper() if m else None
    if isinstance(v, dict):
        if isinstance(v.get("hex"), str) and _HEX.fullmatch(v["hex"]):
            return v["hex"].upper()
        for x in v.values():
            r = _hex(x)
            if r:
                return r
    if isinstance(v, list):
        for x in v:
            r = _hex(x)
            if r:
                return r
    return None


def _lin(h):
    s = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(s[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def _canon_value(canon, key):
    e = (canon or {}).get(key)
    return e.get("value", e) if isinstance(e, dict) and "value" in e else e


def spec(shot, canon):
    """The blackout look for this shot: hex colours (+ linear), shot lists, pool power. Pure python."""
    canon = canon or {}
    lt = (shot or {}).get("lighting") or {}
    after = lt.get("after") if isinstance(lt.get("after"), dict) else {}

    def field(k):
        return lt.get(k) if lt.get(k) is not None else after.get(k)

    cv = _canon_value(canon, "look.lighting.sc03_blackout_render") or {}
    sc03 = _canon_value(canon, "look.color.scene.sc03") or {}
    bo = sc03.get("blackout", {}) if isinstance(sc03, dict) else {}
    floors = _canon_value(canon, "look.exposure.value_structure") or {}
    pool = cv.get("pool", {}) if isinstance(cv, dict) else {}
    door = cv.get("door_rectangle", {}) if isinstance(cv, dict) else {}

    amb = field("ambient")
    if isinstance(amb, dict) and isinstance(amb.get("value"), dict):      # a resolved canon ref: take its blackout dominant
        amb = (amb["value"].get("blackout") or {}).get("dominant")
    elif isinstance(amb, str) and not _HEX.search(amb):                    # an unresolved id such as look.color.scene.sc03
        amb = None
    ambient = _hex(amb) or _hex(bo.get("dominant")) or AMBIENT_HEX
    fl = field("floor")
    floor = (_hex(fl) if not isinstance(fl, dict) or "hex" in fl else None) or _hex(floors.get("film_floor_hex")) or FLOOR_HEX
    key = _hex(pool.get("colour")) or _hex(_canon_value(canon, "look.color.phone_glow")) or _hex(bo.get("key_light")) or KEY_HEX
    door_hex = _hex(door.get("hex_max")) or _hex(bo.get("door_rectangle")) or DOOR_HEX
    shots = tuple(cv.get("shots") or DEFAULT_SHOTS) if isinstance(cv, dict) else DEFAULT_SHOTS
    door_shots = tuple(door.get("in_frame") or DEFAULT_DOOR_SHOTS)
    reach = float(pool.get("reach_m") or 0.5)
    return {
        "ambient": ambient, "floor": floor, "key": key, "door": door_hex,
        "ambient_lin": _lin(ambient), "floor_lin": _lin(floor), "key_lin": _lin(key), "door_lin": _lin(door_hex),
        "lit_mix": float(pool.get("lit_mix", LIT_MIX)), "reach_m": reach,
        "shots": shots, "door_shots": door_shots,
        "pool_w": POOL_W, "lit_phone_w": LIT_PHONE_W,
        "render_spec": field("render_spec"),
    }


POOL_CONE_DEG = 175.0        # the screen emits forward only: a wide cone toward the holder, nothing onto the wall behind the phone


def pool_position(phone, facing):
    """Where the phone-glow light sits: just on the screen side of the phone (the screen faces the holder)."""
    return phone - facing * 0.08


def make_pool_light(bpy, name, loc, energy, colour_lin, collection):
    """The phone's glow: a wide soft spot, no shadows (Ren's own hands do not carve it), colour = canon phone_glow."""
    from . import preview as P
    o = P.add_light("SPOT", name, loc, energy, colour_lin, collection)
    o.data.shadow_soft_size = 0.1
    o.data.spot_size = __import__("math").radians(POOL_CONE_DEG)
    o.data.spot_blend = 0.6
    o.data.use_shadow = False
    return o


def aim_pool(obj, axis):
    """Point the pool light along the screen normal (toward the holder's face)."""
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = axis.normalized().to_track_quat("-Z", "Y")


def is_blackout_shot(shot, canon=None):
    """True for the SC03 shots that render the blackout (SC03_SH050 from f8, SH060, SH070)."""
    if (shot or {}).get("scene_id") != "SC03":
        return False
    sid = shot["shot_id"]
    cv = _canon_value(canon, "look.lighting.sc03_blackout_render")
    listed = cv.get("shots") if isinstance(cv, dict) else None
    if listed:
        return sid in listed
    return int(sid.split("SH")[1]) >= 50


def classify(obj):
    """'off' | 'merch' | 'surface' | 'char' for an object, by what the blackout does to its toon colours."""
    if obj.get("fm_shop_light"):
        return "off"
    cols = [c.name for c in getattr(obj, "users_collection", [])]
    if "fm.shop" not in cols:          # Ren, the cable, the phone body, the crank: not the set
        return "char"
    return "merch" if _MERCH.match(obj.name) else "surface"


def _ramp(mat):
    for nd in mat.node_tree.nodes:
        if nd.type == "VALTORGB":
            return nd.color_ramp
    return None


def _variant(bpy, orig, kind, sp):
    """Blackout copy of a toon material: shadow tone REPLACED by the class colour, lit tone = mix(base, base x key, 0.30)."""
    hx = sp["floor"] if kind in ("merch", "char") else sp["ambient"]
    key = f"fm.bo.{kind}.{hx}.{sp['key']}.{orig.name}"
    m = bpy.data.materials.get(key)
    if m is not None:
        return m
    m = orig.copy()
    m.name = key
    m["fm_bo_of"] = orig.name
    ramp = _ramp(m)
    if ramp is not None:
        lit = list(ramp.elements[1].color)
        k, a = sp["key_lin"], sp["lit_mix"]
        ramp.elements[0].color = (*(_lin(hx)), 1.0)
        ramp.elements[1].color = (*(lit[i] * (1 - a) + lit[i] * k[i] * a for i in range(3)), lit[3])
    return m


def _off_material(bpy, sp):
    """The switched-off panels, fridge glass and fascia sign: a dark NON-emissive "off" material (no emission strength, no
    light of its own) in the film floor colour, drawn through the same two-tone cel shader as the rest of the set so it
    reads #1B1C29 in the dark and takes the pool like any surface. Never hidden: the fridges stay as dark shapes."""
    from . import util as U
    hx = {"hex": sp["floor"], "linear": sp["floor_lin"]}
    m = U.toon(hx, shadow=hx, name=f"fm.bo.off.{sp['floor']}")
    m["fm_bo_off"] = True
    return m


def apply(bpy, on, sp):
    """Switch the scene's materials into (on=True) or out of (on=False) the blackout. Idempotent; safe to call every
    frame, because per-frame figures are new objects with the original materials."""
    n_changed = 0
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.material_slots:
            continue
        kind = classify(o) if on else None
        for slot in o.material_slots:
            cur = slot.material
            if cur is None:
                continue
            orig = bpy.data.materials.get(cur["fm_bo_of"]) if "fm_bo_of" in cur else cur
            if "fm_bo_off" in cur:                       # the off material has no original recorded: use the object's stash
                orig = bpy.data.materials.get(o.get("fm_bo_orig", ""))
                if orig is None:
                    continue
            target = orig
            if on:
                if kind == "off":
                    target = _off_material(bpy, sp)
                    o["fm_bo_orig"] = orig.name
                elif "fm_shadow" in orig and orig.node_tree is not None:
                    target = _variant(bpy, orig, kind, sp)
            if target is not cur:
                slot.material = target
                n_changed += 1
    return n_changed


def add_door_rectangle(bpy, col, origin, shop_width, sp):
    """The door glass: a small warm emissive rectangle in the shop's front opening, only for the shots that face the front."""
    from . import util as U
    from mathutils import Vector
    o = U.box("shop_door_glass", (0.9, 0.01, 2.05), (origin.x + shop_width / 2, origin.y + 0.03, 1.025), col,
              U.flat({"hex": sp["door"], "linear": sp["door_lin"]}, strength=DOOR_STRENGTH, glow=True))
    o["fm_shot"] = True
    return o
