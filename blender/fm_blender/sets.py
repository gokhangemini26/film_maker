"""Blockout sets built from world canon dimensions. All procedural, no external assets."""
import math

import bpy
from mathutils import Vector

from . import util as U

SHOP_ORIGIN = Vector((100.0, 0.0, 0.0))
ROOM_ORIGIN = Vector((200.0, 0.0, 0.0))


def hexes(v, out=None):
    out = [] if out is None else out
    if isinstance(v, dict):
        if "hex" in v and "linear" in v:
            out.append(v)
        else:
            for x in v.values():
                hexes(x, out)
    elif isinstance(v, list):
        for x in v:
            hexes(x, out)
    return out


class Pal:
    def __init__(self, canon, key, fallback):
        self.c = hexes(canon.get(key, [])) or [{"hex": fallback, "linear": U.lin(fallback)}]

    def __call__(self, i):
        return self.c[i % len(self.c)]


def _t(col, c, threshold=0.5):
    return U.toon(c, threshold=threshold)


def build_street(col, canon):
    s = canon["world.sets.street"]
    pal = Pal(canon, "look.color.street", "#CCC6BB")
    ground = _t(col, pal(0))
    pave = _t(col, pal(2))
    b1, b2, b3 = _t(col, pal(4)), _t(col, pal(5)), _t(col, pal(6))
    y0, y1 = s["detail_zone_y"]
    L = y1 - y0
    cy = (y0 + y1) / 2
    x0, x1 = s["carriageway_x"]
    U.box("road", (x1 - x0, L, 0.05), ((x0 + x1) / 2, cy, -0.025), col, ground)
    sx0, sx1 = s["south_pavement_x"]
    U.box("pavement_south", (sx1 - sx0, L, s["pavement_z"]), ((sx0 + sx1) / 2, cy, s["pavement_z"] / 2), col, pave)
    nx0, nx1 = s["north_pavement_x"]
    U.box("pavement_north", (nx1 - nx0, L, s["pavement_z"]), ((nx0 + nx1) / 2, cy, s["pavement_z"] / 2), col, pave)
    # north building line: a row of low houses
    bx = s["building_line_north_x"]
    y = y0
    i = 0
    while y < y1:
        w = 4.5 + (i % 3) * 1.5
        hgt = 6.0 + (i % 2) * 2.0
        U.box(f"house_n{i}", (5.0, w, hgt), (bx + 2.5, y + w / 2, hgt / 2), col, (b1, b2, b3)[i % 3])
        y += w + 0.4
        i += 1
    # south building line: houses, with the shop frontage gap
    bs = s["building_line_south_x"]
    fy0, fy1 = s["shop_frontage_y"]
    y = y0
    i = 0
    while y < y1:
        w = 4.5 + (i % 3) * 1.2
        if y + w > fy0 and y < fy1:
            y = fy1
            continue
        hgt = 5.5 + (i % 2) * 1.5
        U.box(f"house_s{i}", (5.0, w, hgt), (bs - 2.5, y + w / 2, hgt / 2), col, (b2, b3, b1)[i % 3])
        y += w + 0.4
        i += 1
    # shop facade slab (door gap in the middle) + awning
    dcy = s["shop_door_centre"][1]
    fw = fy1 - fy0
    facade = _t(col, Pal(canon, "look.color.shop", "#F4EEDF")(1))
    U.box("shop_facade_l", (0.3, dcy - 0.5 - fy0, 3.2), (bs - 0.15, (fy0 + dcy - 0.5) / 2, 1.6), col, facade)
    U.box("shop_facade_r", (0.3, fy1 - dcy - 0.5, 3.2), (bs - 0.15, (fy1 + dcy + 0.5) / 2, 1.6), col, facade)
    U.box("shop_facade_top", (0.3, 1.0, 1.2), (bs - 0.15, dcy, 2.6), col, facade)
    aw = canon.get("world.sets.corner_shop", {}).get("awning", {"depth_m": 1.0, "height_m": 2.3})
    U.box("shop_awning", (aw["depth_m"], fw, 0.06), (bs + aw["depth_m"] / 2, (fy0 + fy1) / 2, aw["height_m"]),
          col, _t(col, Pal(canon, "look.color.shop", "#BFE0D2")(0)))
    # lamp poles and utility poles
    steel = _t(col, pal(11))
    for i, (px, py) in enumerate(s.get("lamp_poles", [])):
        U.cyl(f"lamp_pole{i}", 0.07, 5.0, (px, py, 2.5), col, steel)
        U.sphere(f"lamp_head{i}", 0.22, (px + 0.5, py, 5.0), col, U.flat({"hex": "#F6DCA6", "linear": U.lin("#F6DCA6")}))
    for i, (px, py) in enumerate(s.get("utility_poles_extra", [])):
        U.cyl(f"utility_pole{i}", 0.09, 7.0, (px, py, 3.5), col, steel)
    # distant western railing and open sky beyond
    U.box("west_railing", (8.0, 0.1, 1.0), (3.0, s.get("west_railing_y", 30), 0.5), col, steel)
    U.box("distant_roofs", (10, 2.0, 5.0), (3.0, 80.0, 2.5), col, _t(col, Pal(canon, "look.color.street", "#8F95A3")(12)))


def build_car(col, canon):
    s = canon["world.sets.street"]
    c = canon["world.sets.ren_car"]
    pal = Pal(canon, "look.color.props", "#9FB0C4")
    body = _t(col, pal(6))
    dark = _t(col, pal(2))
    seat = _t(col, pal(3))
    x0, x1 = s["car_body_x"]
    y0, y1 = s["car_body_y"]
    W, L = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sill, H = c["sill_height_m"], c["height_m"]
    # lower body, roof, pillars (open windows so the interior reads), wheels
    U.box("car_lower", (W, L, sill + 0.35), (cx, cy, (sill + 0.35) / 2 + 0.1), col, body)
    U.box("car_roof", (W, L * 0.62, 0.06), (cx, cy - 0.1, H), col, body)
    for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.box(f"car_pillar{i}", (0.06, 0.06, H - sill - 0.4), (cx + dx * (W / 2 - 0.03), cy - 0.1 + dy * L * 0.31, (H + sill + 0.4) / 2), col, body)
    for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.cyl(f"car_wheel{i}", 0.3, 0.2, (cx + dx * (W / 2 + 0.02), cy + dy * (c["wheelbase_m"] / 2), 0.3), col, dark, rot=(0, math.pi / 2, 0))
    # interior, front half: driver seat (kerb side is passenger: x small), passenger seat, dash, wheel, console, glovebox
    seat_z = c["seat_height_m"]
    fy = cy + 0.15  # front seats forward of centre (+y is west; the car faces west)
    drv_x = x1 - W * 0.27
    pas_x = x0 + W * 0.27
    for nm, sx in (("driver", drv_x), ("passenger", pas_x)):
        U.box(f"seat_{nm}_base", (0.45, 0.5, 0.15), (sx, fy, seat_z - 0.08), col, seat)
        b = U.box(f"seat_{nm}_back", (0.45, 0.1, 0.6), (sx, fy - 0.27, seat_z + 0.28), col, seat)
        b.rotation_euler = (math.radians(-20), 0, 0)
    U.box("dashboard", (W - 0.1, 0.35, 0.28), (cx, y1 - 0.55, sill + 0.45), col, dark)
    U.box("console", (0.22, 0.5, 0.22), (cx, fy + 0.25, seat_z + 0.05), col, dark)
    U.cyl("steering_wheel", 0.19, 0.03, (drv_x, y1 - 0.85, sill + 0.62), col, dark, rot=(math.radians(60), 0, 0))
    gb_w, gb_h = c["glovebox"]["opening_m"]
    U.box("glovebox", (gb_w, 0.2, gb_h), (pas_x, y1 - 0.72, sill + 0.4), col, _t(col, pal(4)))
    # passenger door on the kerb side (x = x0): hinged rectangle, angle applied per shot via property
    door = U.box("car_door_passenger", (0.05, c["door_length_m"], 0.85), (0, c["door_length_m"] / 2, 0), col, body)
    door.location = (x0, cy - c["door_length_m"] / 2 + 0.0, sill + 0.62)
    door["fm_open_angle_deg"] = c["door_open_angle_deg"]
    door["fm_hinge_xy"] = [x0, y1 - 0.35]
    return {"door": door.name}


def build_shop(col, canon):
    c = canon["world.sets.corner_shop"]
    pal = Pal(canon, "look.color.shop", "#F4EEDF")
    fw, fd = c["footprint_m"]
    H = c["ceiling_m"]
    O = SHOP_ORIGIN
    floor = _t(col, pal(4))
    wall = _t(col, pal(1))
    dark = _t(col, pal(3))
    goods = [_t(col, pal(i)) for i in (0, 12, 14, 15, 16)]
    xm, ym = fw / 2, fd / 2
    U.box("shop_floor", (fw, fd, 0.05), (O.x + xm, O.y + ym, -0.025), col, floor)
    U.box("shop_wall_back", (fw, 0.1, H), (O.x + xm, O.y + fd, H / 2), col, wall)
    U.box("shop_wall_l", (0.1, fd, H), (O.x, O.y + ym, H / 2), col, wall)
    U.box("shop_wall_r", (0.1, fd, H), (O.x + fw, O.y + ym, H / 2), col, wall)
    U.box("shop_wall_front_l", (fw / 2 - 0.5, 0.1, H), (O.x + (fw / 2 - 0.5) / 2, O.y, H / 2), col, wall)
    U.box("shop_wall_front_r", (fw / 2 - 0.5, 0.1, H), (O.x + fw - (fw / 2 - 0.5) / 2, O.y, H / 2), col, wall)
    U.box("shop_wall_front_top", (1.0, 0.1, H - 2.1), (O.x + xm, O.y, 2.1 + (H - 2.1) / 2), col, wall)
    U.box("shop_ceiling", (fw, fd, 0.05), (O.x + xm, O.y + ym, H), col, wall)
    # ceiling panels (emissive; switched by the preview via property fm_shop_light)
    for i in range(c["ceiling_panels"]):
        p = U.box(f"shop_panel{i}", (0.9, 0.9, 0.03), (O.x + xm, O.y + fd * (i + 0.5) / c["ceiling_panels"], H - 0.03), col,
                  U.flat({"hex": "#FFF6E4", "linear": U.lin("#FFF6E4")}, strength=3.0))
        p["fm_shop_light"] = True
    cw, cd, ch = c["counter"]["size_m"]
    U.box("shop_counter", (cw, cd, ch), (O.x + 0.2 + cw / 2, O.y + 1.6, ch / 2), col, dark)
    for i in range(c["aisles"]["count"]):
        U.box(f"gondola{i}", (0.5, c["aisles"]["gondola_length_m"], c["aisles"]["gondola_height_m"]),
              (O.x + 1.2 + i * (0.5 + c["aisles"]["aisle_width_m"]), O.y + 4.5, c["aisles"]["gondola_height_m"] / 2), col, goods[i % 5])
    fz = c["fridges"]["size_m"]
    for i in range(c["fridges"]["count"]):
        f = U.box(f"fridge{i}", tuple(fz), (O.x + 0.9 + i * 1.5, O.y + fd - fz[1] / 2 - 0.05, fz[2] / 2), col, _t(col, pal(9)))
        g = U.box(f"fridge_glow{i}", (fz[0] * 0.85, 0.02, fz[2] * 0.8), (O.x + 0.9 + i * 1.5, O.y + fd - fz[1] - 0.06, fz[2] / 2), col,
                  U.flat({"hex": "#DDF3F4", "linear": U.lin("#DDF3F4")}, strength=2.0))
        g["fm_shop_light"] = True
    sock = c["socket"]
    U.box("shop_socket", (0.08, 0.02, 0.08), (O.x + fw - 0.25, O.y + fd - 0.06, sock["height_m"]), col, dark)
    dw, dd, dh = c["display_stand"]["size_m"]
    U.box("display_stand", (dw, dd, dh), (O.x + fw - 0.9, O.y + fd - 0.06 - c["display_stand"]["gap_to_wall_m"] - dd / 2, dh / 2), col, goods[3])
    bw, bh = c["back_room_doorway"]["size_m"]
    U.box("back_room_doorway", (bw, 0.05, bh), (O.x + 1.0, O.y + 2.4, bh / 2), col, dark)


def build_room(col, canon):
    c = canon["world.sets.hana_room"]
    pal = Pal(canon, "look.color.hana_room", "#EDE2CF")
    fx, fy = c["footprint_m"]
    H = c["ceiling_m"]
    O = ROOM_ORIGIN
    wall, floor, dark = _t(col, pal(0)), _t(col, pal(2)), _t(col, pal(7))
    U.box("room_floor", (fx, fy, 0.05), (O.x, O.y - fy / 2, -0.025), col, floor)
    U.box("room_wall_east", (0.1, fy, H), (O.x, O.y - fy, H / 2), col, wall)
    U.box("room_wall_north", (0.1, fy, H), (O.x + fx / 2, O.y - fy / 2, H / 2), col, wall).rotation_euler = (0, 0, math.pi / 2)
    U.box("room_wall_south", (0.1, fy, H), (O.x - fx / 2, O.y - fy / 2, H / 2), col, wall)
    U.box("room_ceiling", (fx, fy, 0.05), (O.x, O.y - fy / 2, H), col, wall)
    # window wall (y = 0) with an opening
    w = c["window"]
    sill, wh, ww = w["sill_height_m"], w["height_m"], w["width_m"]
    U.box("wall_w_left", (fx / 2 - ww / 2, 0.1, H), (O.x - fx / 4 - ww / 4, O.y, H / 2), col, wall)
    U.box("wall_w_right", (fx / 2 - ww / 2, 0.1, H), (O.x + fx / 4 + ww / 4, O.y, H / 2), col, wall)
    U.box("wall_w_below", (ww, 0.1, sill), (O.x, O.y, sill / 2), col, wall)
    U.box("wall_w_above", (ww, 0.1, H - sill - wh), (O.x, O.y, sill + wh + (H - sill - wh) / 2), col, wall)
    dw, dd = c["desk"]["size_m"]
    dh = c["desk"]["height_m"]
    U.box("desk_top", (dw, dd, 0.04), (O.x, O.y - dd / 2, dh), col, _t(col, pal(2)))
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.box(f"desk_leg{i}", (0.05, 0.05, dh), (O.x + sx * (dw / 2 - 0.04), O.y - dd / 2 + sy * (dd / 2 - 0.04), dh / 2), col, dark)
    U.box("chair_seat", (0.42, 0.42, 0.04), (O.x, O.y - 0.85, 0.44), col, dark)
    U.box("chair_back", (0.42, 0.04, 0.45), (O.x, O.y - 1.06, 0.68), col, dark)
    U.box("sketchbook", (0.3, 0.22, 0.02), (O.x - 0.2, O.y - 0.28, dh + 0.03), col, _t(col, pal(5)))
    U.cyl("desk_lamp_base", 0.07, 0.02, (O.x - 0.45, O.y - 0.2, dh + 0.03), col, dark)
    U.between("desk_lamp_arm", (O.x - 0.45, O.y - 0.2, dh + 0.03), (O.x - 0.35, O.y - 0.28, dh + 0.42), 0.012, col, dark)
    U.sphere("desk_lamp_head", 0.07, (O.x - 0.35, O.y - 0.28, dh + 0.42), col, U.flat({"hex": "#FFD6A0", "linear": U.lin("#FFD6A0")}, strength=4.0))
    U.box("phone_hana", (0.071, 0.147, 0.0085), (O.x + 0.25, O.y - 0.3, dh + 0.03), col, _t(col, pal(7)))
    U.box("phone_hana_screen", (0.06, 0.13, 0.002), (O.x + 0.25, O.y - 0.3, dh + 0.036), col,
          U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5))
    for i in range(5):
        U.box(f"wall_sketch{i}", (0.25, 0.01, 0.3), (O.x - 0.5 + i * 0.28, O.y - 0.06, 1.75), col, _t(col, pal(3 + i)))


def build_generic(col, canon):
    """Fallback stage for films whose canon has no set dimensions: ground plane + far backdrop."""
    ground = U.toon({"hex": "#B9B4AA", "linear": U.lin("#B9B4AA")})
    U.box("stage_ground", (60, 60, 0.05), (0, 0, -0.025), col, ground)
    U.box("stage_backdrop", (60, 0.2, 12), (0, 30, 6), col, U.toon({"hex": "#C9D6E3", "linear": U.lin("#C9D6E3")}))
