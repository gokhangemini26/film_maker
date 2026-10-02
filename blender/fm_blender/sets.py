"""Blockout sets built from world canon dimensions. All procedural, no external assets."""
import math

import bpy
from mathutils import Vector

from . import util as U
from .anchors import car_layout, shop_anchors

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
    pave = _t(col, pal(1))
    kerb = _t(col, pal(2))
    b1, b2, b3 = _t(col, pal(4)), _t(col, pal(5)), _t(col, pal(6))
    y0, y1 = s["detail_zone_y"]
    L = y1 - y0
    cy = (y0 + y1) / 2
    x0, x1 = s["carriageway_x"]
    U.box("road", (x1 - x0, L, 0.05), ((x0 + x1) / 2, cy, -0.025), col, ground)
    sx0, sx1 = s["south_pavement_x"]
    U.box("pavement_south", (sx1 - sx0, L, s["pavement_z"]), ((sx0 + sx1) / 2, cy, s["pavement_z"] / 2), col, pave)
    U.box("kerb_south", (0.15, L, s["pavement_z"] + 0.003), (-0.075, cy, (s["pavement_z"] + 0.003) / 2), col, kerb)
    nx0, nx1 = s["north_pavement_x"]
    U.box("kerb_north", (0.15, L, s["pavement_z"] + 0.003), (nx0 + 0.075, cy, (s["pavement_z"] + 0.003) / 2), col, kerb)
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
    shp = Pal(canon, "look.color.shop", "#BFE0D2")
    n_st = 9
    for k in range(n_st):  # striped awning: alternating stripes across the frontage
        U.box(f"shop_awning_s{k}", (aw["depth_m"], fw / n_st, 0.06), (bs + aw["depth_m"] / 2, fy0 + fw * (k + 0.5) / n_st, aw["height_m"]),
              col, _t(col, shp(k % 2)))
    # fascia with a plain pictogram basket (shapes only, no text) above the awning
    navy = _t(col, shp(3))
    U.box("shop_fascia", (0.08, 3.0, 0.5), (bs + 0.04, dcy, 2.85), col, _t(col, shp(2)))
    U.box("fascia_basket", (0.02, 0.28, 0.16), (bs + 0.09, dcy, 2.78), col, navy)
    for k, sy in enumerate((-1, 1)):
        U.box(f"fascia_basket_handle{k}", (0.02, 0.02, 0.1), (bs + 0.09, dcy + sy * 0.08, 2.91), col, navy)
    U.box("fascia_basket_handle_top", (0.02, 0.18, 0.02), (bs + 0.09, dcy, 2.96), col, navy)
    for k, sy in enumerate((-1, 1)):  # door jambs
        U.box(f"shop_door_jamb{k}", (0.08, 0.06, 2.1), (bs + 0.02, dcy + sy * 0.53, 1.05), col, _t(col, shp(10)))
    # lamp poles and utility poles
    steel = _t(col, pal(10))
    for i, (px, py) in enumerate(s.get("lamp_poles", [])):
        U.cyl(f"lamp_pole{i}", 0.07, 5.0, (px, py, 2.5), col, steel)
        U.sphere(f"lamp_head{i}", 0.22, (px + 0.5, py, 5.0), col, U.flat({"hex": "#F6DCA6", "linear": U.lin("#F6DCA6")}, glow=True))
    for i, (px, py) in enumerate(s.get("utility_poles_extra", [])):
        U.cyl(f"utility_pole{i}", 0.09, 7.0, (px, py, 3.5), col, steel)
    # distant western railing and open sky beyond
    U.box("west_railing", (8.0, 0.1, 1.0), (3.0, s.get("west_railing_y", 30), 0.5), col, steel)
    U.box("distant_roofs", (10, 2.0, 5.0), (3.0, 80.0, 2.5), col, _t(col, Pal(canon, "look.color.street", "#8F95A3")(12)))


def build_car(col, canon):
    s = canon["world.sets.street"]
    c = canon["world.sets.ren_car"]
    pal = Pal(canon, "look.color.props", "#9FB0C4")
    named = {c.get("item"): c for c in pal.c if isinstance(c, dict) and c.get("item")}
    pick = lambda item, i: named.get(item) or pal(i)  # noqa: E731
    body = _t(col, pick("car_paint", 6))
    roofm = _t(col, pick("car_paint_sun_faded_roof_bonnet", 6))
    dark = _t(col, pick("car_rubber_trim_tyres", 2))
    seat = _t(col, pick("car_seats", 3))
    x0, x1 = s["car_body_x"]
    y0, y1 = s["car_body_y"]
    W, L = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sill, H = c["sill_height_m"], c["height_m"]
    # lower body, roof, pillars (open windows so the interior reads), wheels
    U.box("car_lower", (W, L, sill + 0.35), (cx, cy, (sill + 0.35) / 2 + 0.1), col, body)
    U.box("car_roof", (W, L * 0.62, 0.06), (cx, cy - 0.1, H), col, roofm)
    for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.box(f"car_pillar{i}", (0.06, 0.06, H - sill - 0.4), (cx + dx * (W / 2 - 0.03), cy - 0.1 + dy * L * 0.31, (H + sill + 0.4) / 2), col, body)
    for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.cyl(f"car_wheel{i}", 0.3, 0.2, (cx + dx * (W / 2 + 0.02), cy + dy * (c["wheelbase_m"] / 2), 0.3), col, dark, rot=(0, math.pi / 2, 0))
    # interior, front half: driver seat (kerb side is passenger: x small), passenger seat, dash, wheel, console, glovebox
    seat_z = c["seat_height_m"]
    seat_dy, gb_dy = car_layout()
    fy = cy + 0.15 + seat_dy  # front seats forward of centre (+y is west; the car faces west)
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
    gb_y, gb_z = y1 - 0.72 + gb_dy, sill + 0.4
    U.box("glovebox", (gb_w, 0.2, gb_h), (pas_x, gb_y, gb_z), col, U.toon({"hex": "#3A3630", "linear": U.lin("#3A3630")}))
    # glovebox lid: face toward the seat (-y). Closed = vertical panel; open = dropped flat, hinged on its bottom edge
    lid = U.box("glovebox_lid", (gb_w, 0.02, gb_h), (pas_x, gb_y - 0.111, gb_z), col, _t(col, pal(4)))
    lid["fm_closed_loc"] = [pas_x, gb_y - 0.111, gb_z]
    lid["fm_open_loc"] = [pas_x, gb_y - 0.111 - gb_h / 2, gb_z - gb_h / 2]
    # passenger door on the kerb side (x = x0): hinged rectangle, angle applied per shot via property
    door = U.box("car_door_passenger", (0.05, c["door_length_m"], 0.85), (0, c["door_length_m"] / 2, 0), col, body)
    door.location = (x0, 0.525 - c["door_length_m"] / 2, sill + 0.62)  # closed: hinge at the front end, y 0.525 (canon door centre y 0)
    door["fm_open_angle_deg"] = c["door_open_angle_deg"]
    door["fm_hinge_xy"] = [x0, 0.525]
    return {"door": door.name, "glovebox_lid": lid.name}


def _mix(a, b, t):
    """Deterministic blend of two resolved colours (hex + linear), for shade variants of canon colours."""
    ha, hb = a["hex"].lstrip("#"), b["hex"].lstrip("#")
    v = "#" + "".join("%02X" % round(int(ha[i:i + 2], 16) * (1 - t) + int(hb[i:i + 2], 16) * t) for i in (0, 2, 4))
    return {"hex": v, "linear": U.lin(v)}


def _stock(col, tag, x, y0, y1, z, kind, mat, step=0.36, dx=0.0):
    """One row of merchandise along +Y: kind 0 round tins, 1 tall boxes, 2 pillow bags, 3 bottles (shape families, no labels)."""
    y = y0 + step / 2
    n = 0
    while y < y1:
        if kind == 0:
            U.cyl(f"{tag}_{n}", 0.06, 0.14, (x, y, z + 0.07), col, mat)
        elif kind == 1:
            U.box(f"{tag}_{n}", (0.13, 0.11, 0.24), (x, y, z + 0.12), col, mat)
        elif kind == 2:
            U.box(f"{tag}_{n}", (0.15, 0.13, 0.15), (x, y, z + 0.075), col, mat)
        else:
            U.cyl(f"{tag}_{n}", 0.035, 0.22, (x, y, z + 0.11), col, mat)
        y += step
        n += 1


def build_shop(col, canon):
    c = canon["world.sets.corner_shop"]
    pal = Pal(canon, "look.color.shop", "#F4EEDF")
    fw, fd = c["footprint_m"]
    H = c["ceiling_m"]
    O = SHOP_ORIGIN
    floor = _t(col, pal(5))
    wear = _t(col, _mix(pal(5), pal(20), 0.07))
    wall = _t(col, pal(4))
    ceil = _t(col, _mix(pal(4), pal(2), 0.5))
    shelving = _t(col, pal(6))
    frame = _t(col, pal(10))
    counter_m = _t(col, pal(7))
    till_m = _t(col, pal(8))
    curtain_m = _t(col, pal(9))
    stand_m = _t(col, pal(11))
    dark = _t(col, pal(20))
    fam = [_t(col, pal(i)) for i in (12, 13, 14, 15, 16)]
    xm, ym = fw / 2, fd / 2
    U.box("shop_floor", (fw, fd, 0.05), (O.x + xm, O.y + ym, -0.025), col, floor)
    for i, ax in enumerate((0.475, 1.9)):  # scuffed aisle centre lines
        U.box(f"shop_floor_wear{i}", (0.7, fd - 2.0, 0.004), (O.x + ax, O.y + 1.9 + (fd - 2.0) / 2, 0.002), col, wear)
    U.box("shop_wall_back", (fw, 0.1, H), (O.x + xm, O.y + fd, H / 2), col, wall)
    U.box("shop_wall_l", (0.1, fd, H), (O.x, O.y + ym, H / 2), col, wall)
    U.box("shop_wall_r", (0.1, fd, H), (O.x + fw, O.y + ym, H / 2), col, wall)
    U.box("shop_wall_front_l", (fw / 2 - 0.5, 0.1, H), (O.x + (fw / 2 - 0.5) / 2, O.y, H / 2), col, wall)
    U.box("shop_wall_front_r", (fw / 2 - 0.5, 0.1, H), (O.x + fw - (fw / 2 - 0.5) / 2, O.y, H / 2), col, wall)
    U.box("shop_wall_front_top", (1.0, 0.1, H - 2.1), (O.x + xm, O.y, 2.1 + (H - 2.1) / 2), col, wall)
    U.box("shop_ceiling", (fw, fd, 0.05), (O.x + xm, O.y + ym, H), col, ceil)
    # door frame (front opening stays open: characters walk through it)
    for i, sx in enumerate((-1, 1)):
        U.box(f"shop_door_jamb{i}", (0.05, 0.14, 2.1), (O.x + xm + sx * 0.5, O.y, 1.05), col, frame)
    U.box("shop_door_header", (1.05, 0.14, 0.05), (O.x + xm, O.y, 2.1), col, frame)
    # ceiling panels (emissive; switched by the preview via property fm_shop_light)
    for i in range(c["ceiling_panels"]):
        p = U.box(f"shop_panel{i}", (0.9, 0.9, 0.03), (O.x + xm, O.y + fd * (i + 0.5) / c["ceiling_panels"], H - 0.03), col,
                  U.flat({"hex": "#FFF6E4", "linear": U.lin("#FFF6E4")}, strength=3.0, glow=True))
        p["fm_shop_light"] = True
    # counter front-left with a plain till box (no screen)
    cw, cd, ch = c["counter"]["size_m"]
    cx, cy = O.x + 0.2 + cw / 2, O.y + 1.6
    U.box("shop_counter", (cw, cd, ch - 0.04), (cx, cy, (ch - 0.04) / 2), col, counter_m)
    U.box("shop_counter_top", (cw + 0.06, cd + 0.06, 0.04), (cx, cy, ch - 0.02), col, _t(col, _mix(pal(7), pal(20), 0.12)))
    U.box("shop_till", (0.3, 0.24, 0.16), (cx - 0.6, cy, ch + 0.08), col, till_m)
    # back-room doorway behind the counter, on the left wall, with a hanging strip curtain
    bw, bh = c["back_room_doorway"]["size_m"]
    dy = O.y + 2.7
    U.box("back_room_doorway", (0.04, bw, bh), (O.x + 0.07, dy, bh / 2), col, dark)
    for i, sy in enumerate((-1, 1)):
        U.box(f"back_room_jamb{i}", (0.06, 0.05, bh + 0.05), (O.x + 0.08, dy + sy * (bw / 2 + 0.025), (bh + 0.05) / 2), col, frame)
    U.box("back_room_header", (0.06, bw + 0.1, 0.05), (O.x + 0.08, dy, bh + 0.025), col, frame)
    for i in range(8):
        U.box(f"strip_curtain{i}", (0.012, 0.085, bh - 0.08), (O.x + 0.12, dy - bw / 2 + 0.05 + i * (bw - 0.1) / 7, (bh - 0.08) / 2 + 0.06), col, curtain_m)
    # two low gondolas: spine + boards, one merchandise family per row, colour-blocked end caps
    ag = c["aisles"]
    gl, gh = ag["gondola_length_m"], ag["gondola_height_m"]
    for g in range(ag["count"]):
        gx = O.x + 1.2 + g * (0.5 + ag["aisle_width_m"])
        gy0, gy1 = O.y + 4.5 - gl / 2, O.y + 4.5 + gl / 2
        U.box(f"gondola{g}", (0.06, gl, gh), (gx, O.y + 4.5, gh / 2), col, shelving)
        U.box(f"gondola{g}_plinth", (0.5, gl, 0.1), (gx, O.y + 4.5, 0.05), col, frame)
        U.box(f"gondola{g}_cap", (0.52, gl + 0.04, 0.04), (gx, O.y + 4.5, gh + 0.02), col, shelving)
        for e, ey in enumerate((gy0 - 0.02, gy1 + 0.02)):
            U.box(f"gondola{g}_end{e}", (0.52, 0.04, gh), (gx, ey, gh / 2), col, fam[(g * 2 + e) % 5])
        for r, zb in enumerate((0.28, 0.68, 1.08)):
            for s_, sx in enumerate((-1, 1)):
                U.box(f"gondola{g}_board{r}{s_}", (0.22, gl, 0.03), (gx + sx * 0.14, O.y + 4.5, zb), col, shelving)
                k = (g * 3 + r + s_) % 4
                _stock(col, f"stock{g}_{r}{s_}", gx + sx * 0.14, gy0, gy1, zb + 0.015, k, fam[k])
    # right-wall shelving run (does not touch the aisle centres)
    U.box("wall_shelf_spine", (0.04, 5.0, 1.9), (O.x + fw - 0.07, O.y + 5.0, 0.95), col, shelving)
    for r, zb in enumerate((0.35, 0.8, 1.25, 1.7)):
        U.box(f"wall_shelf_board{r}", (0.28, 5.0, 0.03), (O.x + fw - 0.21, O.y + 5.0, zb), col, shelving)
        _stock(col, f"wall_stock{r}", O.x + fw - 0.2, O.y + 2.5, O.y + 7.5, zb + 0.015, (r + 1) % 4, fam[(r + 1) % 4], step=0.4)
    # pictogram posters (shapes only, no text) above the wall shelving
    post = [_t(col, pal(i)) for i in (17, 18, 19)]
    panel = _t(col, pal(2))
    for i, py in enumerate((3.4, 4.9, 6.4)):
        px = O.x + fw - 0.055
        U.box(f"poster{i}", (0.01, 0.6, 0.45), (px, O.y + py, 2.32), col, panel)
        if i == 0:  # ice lolly
            U.box("poster0_lolly", (0.012, 0.16, 0.22), (px, O.y + py, 2.36), col, post[0])
            U.box("poster0_stick", (0.012, 0.04, 0.1), (px, O.y + py, 2.2), col, stand_m)
        elif i == 1:  # starburst
            U.box("poster1_a", (0.012, 0.22, 0.22), (px, O.y + py, 2.32), col, post[1])
            U.box("poster1_b", (0.012, 0.22, 0.22), (px, O.y + py, 2.32), col, post[1], rot=(math.pi / 4, 0, 0))
        else:  # steaming cup
            U.box("poster2_cup", (0.012, 0.18, 0.15), (px, O.y + py, 2.24), col, post[2])
            for k in range(3):
                U.box(f"poster2_steam{k}", (0.012, 0.025, 0.1), (px, O.y + py - 0.05 + k * 0.05, 2.42), col, post[2])
    # three upright fridges across the back wall, left of the socket corner
    fz = c["fridges"]["size_m"]
    for i in range(c["fridges"]["count"]):
        fx_ = O.x + 0.95 + i * 0.95
        U.box(f"fridge{i}", tuple(fz), (fx_, O.y + fd - fz[1] / 2 - 0.05, fz[2] / 2), col, frame)
        g = U.box(f"fridge_glow{i}", (fz[0] * 0.85, 0.02, fz[2] * 0.8), (fx_, O.y + fd - fz[1] - 0.06, fz[2] / 2), col,
                  U.flat({"hex": "#DDF3F4", "linear": U.lin("#DDF3F4")}, strength=2.0, glow=True))
        g["fm_shop_light"] = True
        for r, zb in enumerate((0.55, 0.95, 1.35)):  # bottle silhouettes standing on the lit shelves
            U.box(f"fridge{i}_shelf{r}", (fz[0] * 0.85, 0.03, 0.02), (fx_, O.y + fd - fz[1] - 0.075, zb), col, frame)
            for k in range(5):
                U.cyl(f"fridge{i}_b{r}{k}", 0.03, 0.2, (fx_ - 0.24 + k * 0.12, O.y + fd - fz[1] - 0.09, zb + 0.11), col, fam[(i + r + k) % 4])
    # USB wall socket, right-hand corner, low on the back wall
    sock = c["socket"]
    anc = shop_anchors(c, O)
    sx_ = anc["socket"].x
    U.box("shop_socket", (0.146, 0.02, 0.086), (sx_, O.y + fd - 0.06, sock["height_m"]), col, _t(col, pal(2)))
    for k, ox in enumerate((-0.035, 0.035)):
        U.box(f"shop_socket_port{k}", (0.03, 0.01, 0.014), (sx_ + ox, O.y + fd - 0.07, sock["height_m"] + 0.022), col, dark)
        U.cyl(f"shop_socket_pin{k}", 0.013, 0.01, (sx_ + ox, O.y + fd - 0.07, sock["height_m"] - 0.012), col, dark, rot=(math.pi / 2, 0, 0))
    # tiered display stand standing 0.25 m in front of the socket, hiding it from the door
    dw, dd, dh = c["display_stand"]["size_m"]
    sy_, stx = anc["stand_centre"].y, anc["stand_centre"].x
    for t_, (tw, tz, th) in enumerate(((dw, 0.0, 0.45), (dw - 0.1, 0.45, 0.4), (dw - 0.2, 0.85, 0.45))):
        U.box(f"display_stand_tier{t_}", (tw, dd - 0.04 * t_, th), (stx, sy_, tz + th / 2), col, stand_m)
        U.cyl(f"display_stand_tin{t_}", 0.05, 0.1, (stx - 0.05, sy_ - 0.08, tz + th + 0.05), col, fam[t_])
    U.box("display_stand_top", (dw - 0.2, dd - 0.08, 0.03), (stx, sy_, dh - 0.015), col, fam[3])


def build_room(col, canon):
    c = canon["world.sets.hana_room"]
    pal = Pal(canon, "look.color.hana_room", "#EDE2CF")
    fx, fy = c["footprint_m"]
    H = c["ceiling_m"]
    O = ROOM_ORIGIN
    wall = _t(col, pal(0))
    wood = _t(col, pal(2))
    dwood = _t(col, _mix(pal(2), pal(7), 0.4))
    floor = _t(col, _mix(pal(2), pal(0), 0.4))
    rug = _t(col, _mix(pal(3), pal(0), 0.35))
    bedm, curt, chairm, paper, framem = _t(col, pal(1)), _t(col, pal(3)), _t(col, pal(4)), _t(col, pal(5)), _t(col, pal(6))
    dark = _t(col, pal(7))
    sil = U.flat(pal(7))  # dusk silhouettes outside the window: shape only
    U.box("room_floor", (fx, fy, 0.05), (O.x, O.y - fy / 2, -0.025), col, floor)
    U.box("room_rug", (1.7, 1.3, 0.01), (O.x, O.y - 1.25, 0.005), col, rug)
    U.box("room_wall_east", (fx + 0.1, 0.1, H), (O.x, O.y - fy, H / 2), col, wall)
    U.box("room_wall_north", (0.1, fy, H), (O.x + fx / 2, O.y - fy / 2, H / 2), col, wall)
    U.box("room_wall_south", (0.1, fy, H), (O.x - fx / 2, O.y - fy / 2, H / 2), col, wall)
    U.box("room_ceiling", (fx, fy, 0.05), (O.x, O.y - fy / 2, H), col, wall)
    # window wall (y = 0, west) with an opening; frame, sill, open curtains
    w = c["window"]
    sill, wh, ww = w["sill_height_m"], w["height_m"], w["width_m"]
    U.box("wall_w_left", (fx / 2 - ww / 2, 0.1, H), (O.x - fx / 4 - ww / 4, O.y, H / 2), col, wall)
    U.box("wall_w_right", (fx / 2 - ww / 2, 0.1, H), (O.x + fx / 4 + ww / 4, O.y, H / 2), col, wall)
    U.box("wall_w_below", (ww, 0.1, sill), (O.x, O.y, sill / 2), col, wall)
    U.box("wall_w_above", (ww, 0.1, H - sill - wh), (O.x, O.y, sill + wh + (H - sill - wh) / 2), col, wall)
    for i, sx in enumerate((-1, 1)):
        U.box(f"window_jamb{i}", (0.04, 0.14, wh), (O.x + sx * (ww / 2 - 0.02), O.y - 0.02, sill + wh / 2), col, framem)
    U.box("window_head", (ww, 0.14, 0.04), (O.x, O.y - 0.02, sill + wh - 0.02), col, framem)
    U.box("window_sill", (ww + 0.16, 0.22, 0.03), (O.x, O.y - 0.06, sill + 0.015), col, framem)
    for i, sx in enumerate((-1, 1)):
        U.box(f"curtain{i}", (0.26, 0.08, H - 0.45), (O.x + sx * (ww / 2 + 0.08), O.y - 0.1, 0.35 + (H - 0.45) / 2), col, curt)
    U.cyl("curtain_rod", 0.012, ww + 0.7, (O.x, O.y - 0.1, H - 0.15), col, dark, rot=(0, math.pi / 2, 0))
    # sill plant (sketch subject: a plant)
    plant = _t(col, Pal(canon, "look.color.street", "#8FB08A")(17))
    U.cyl("plant_pot", 0.05, 0.09, (O.x + 0.42, O.y - 0.08, sill + 0.075), col, chairm)
    for k, (lx, lz, ls) in enumerate(((0, 0.11, 0.06), (-0.04, 0.09, 0.045), (0.04, 0.1, 0.045))):
        U.sphere(f"plant_leaf{k}", ls, (O.x + 0.42 + lx, O.y - 0.08, sill + 0.12 + lz), col, plant, scale=(1, 1, 1.4))
    # view through the window: rooftop silhouettes, a utility pole and wires (flat dusk colour)
    for i in range(7):
        rw = 1.6 + (i % 3) * 0.7
        rx = O.x - 6.0 + i * 2.0 + (i % 2) * 0.4
        ry = O.y + 9.0 + (i % 3) * 1.6
        top = 0.1 + (i % 4) * 0.22
        U.box(f"view_house{i}", (rw, 3.0, top + 3.0), (rx, ry, top / 2 - 1.5), col, sil)
        U.box(f"view_roof{i}", (rw + 0.3, 1.0, 1.0), (rx, ry, top), col, sil, rot=(math.pi / 4, 0, 0))
    px, py = O.x + 0.9, O.y + 6.0
    U.cyl("view_pole", 0.07, 6.5, (px, py, 2.2), col, sil)
    U.box("view_pole_arm", (1.3, 0.06, 0.06), (px, py, 4.7), col, sil)
    for k, zo in enumerate((0.0, -0.18, -0.36)):
        ox = px - 0.55 + k * 0.55
        U.between(f"view_wire{k}a", (ox, py, 4.7 + zo), (px - 9.0, py + 0.5, 4.3 + zo), 0.012, col, sil)
        U.between(f"view_wire{k}b", (ox, py, 4.7 + zo), (px + 9.0, py + 0.5, 4.2 + zo), 0.012, col, sil)
    # desk under the window
    dw, dd = c["desk"]["size_m"]
    dh = c["desk"]["height_m"]
    U.box("desk_top", (dw, dd, 0.04), (O.x, O.y - dd / 2, dh), col, wood)
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.box(f"desk_leg{i}", (0.05, 0.05, dh), (O.x + sx * (dw / 2 - 0.04), O.y - dd / 2 + sy * (dd / 2 - 0.04), dh / 2), col, dwood)
    U.box("desk_apron", (dw - 0.1, 0.02, 0.08), (O.x, O.y - dd + 0.03, dh - 0.06), col, dwood)
    # simple desk chair
    U.box("chair_seat", (0.42, 0.42, 0.04), (O.x, O.y - 0.85, 0.44), col, chairm)
    U.box("chair_back", (0.42, 0.04, 0.45), (O.x, O.y - 1.06, 0.68), col, chairm)
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        U.box(f"chair_leg{i}", (0.03, 0.03, 0.42), (O.x + sx * 0.18, O.y - 0.85 + sy * 0.18, 0.21), col, dark)
    # desk, left to right: lamp, open sketchbook (no writing), pencil cup, phone
    U.box("sketchbook", (0.3, 0.22, 0.02), (O.x - 0.2, O.y - 0.28, dh + 0.03), col, paper)
    U.box("sketchbook_drawing", (0.12, 0.08, 0.003), (O.x - 0.28, O.y - 0.3, dh + 0.0415), col, dark)
    U.cyl("pencil_cup", 0.035, 0.09, (O.x + 0.06, O.y - 0.16, dh + 0.065), col, chairm)
    for k, (dx_, dy_) in enumerate(((0.02, 0.01), (-0.015, -0.01), (0.0, 0.02))):
        U.between(f"pencil{k}", (O.x + 0.06, O.y - 0.16, dh + 0.09), (O.x + 0.06 + dx_, O.y - 0.16 + dy_, dh + 0.19), 0.004, col, (wood, curt, bedm)[k])
    U.cyl("desk_lamp_base", 0.07, 0.02, (O.x - 0.45, O.y - 0.2, dh + 0.03), col, dark)
    U.between("desk_lamp_arm", (O.x - 0.45, O.y - 0.2, dh + 0.03), (O.x - 0.35, O.y - 0.28, dh + 0.42), 0.012, col, dark)
    U.cyl("desk_lamp_shade", 0.075, 0.08, (O.x - 0.35, O.y - 0.28, dh + 0.43), col, dark)
    U.sphere("desk_lamp_head", 0.035, (O.x - 0.35, O.y - 0.28, dh + 0.38), col, U.flat({"hex": "#FFD6A0", "linear": U.lin("#FFD6A0")}, strength=4.0, glow=True))
    U.box("phone_hana", (0.071, 0.147, 0.0085), (O.x + 0.25, O.y - 0.3, dh + 0.03), col, dark)
    U.box("phone_hana_screen", (0.06, 0.13, 0.002), (O.x + 0.25, O.y - 0.3, dh + 0.036), col,
          U.flat({"hex": "#FFF1DE", "linear": U.lin("#FFF1DE")}, strength=2.5, glow=True))
    # five pinned sketches either side of the window (pictures only: window view, rooftops, plant, cat, cup shapes)
    for i, sxp in enumerate((-1.24, -1.02, 0.98, 1.16, 1.34)):
        sz = 1.55 - (i % 3) * 0.14
        U.box(f"wall_sketch{i}", (0.16, 0.008, 0.21), (O.x + sxp, O.y - 0.054, sz), col, paper)
        U.box(f"wall_sketch{i}_mark", (0.11, 0.004, 0.05 + (i % 2) * 0.03), (O.x + sxp, O.y - 0.06, sz - 0.05), col, (dark, chairm, curt, dark, bedm)[i])
    # rest of the room, low detail: bed edge against the north wall, freestanding shelf, back door
    U.box("bed_base", (0.95, 1.85, 0.3), (O.x + fx / 2 - 0.05 - 0.475, O.y - fy + 0.05 + 0.925, 0.15), col, dwood)
    U.box("bed_mattress", (0.93, 1.83, 0.16), (O.x + fx / 2 - 0.05 - 0.475, O.y - fy + 0.05 + 0.925, 0.38), col, bedm)
    U.box("bed_blanket", (0.95, 1.0, 0.05), (O.x + fx / 2 - 0.05 - 0.475, O.y - fy + 0.05 + 1.35, 0.485), col, curt)
    U.box("bed_pillow", (0.5, 0.35, 0.1), (O.x + fx / 2 - 0.05 - 0.475, O.y - fy + 0.05 + 0.25, 0.51), col, paper)
    shx, shy = O.x + fx / 2 - 0.05 - 0.15, O.y - 1.35
    U.box("shelf_unit", (0.3, 0.6, 0.9), (shx, shy, 0.45), col, wood)
    for r, zb in enumerate((0.3, 0.62)):
        for k in range(4):
            U.box(f"shelf_item{r}{k}", (0.03, 0.05, 0.14 + ((r + k) % 3) * 0.03),
                  (shx - 0.155, shy - 0.21 + k * 0.14, zb + 0.08), col, (bedm, paper, curt, bedm)[(r + k) % 4])
    U.box("room_door", (0.9, 0.04, 2.0), (O.x - 0.6, O.y - fy + 0.07, 1.0), col, _t(col, _mix(pal(6), pal(2), 0.35)))
    U.sphere("room_door_knob", 0.022, (O.x - 0.25, O.y - fy + 0.1, 1.0), col, dark)


def build_generic(col, canon):
    """Fallback stage for films whose canon has no set dimensions: ground plane + far backdrop."""
    ground = U.toon({"hex": "#B9B4AA", "linear": U.lin("#B9B4AA")})
    U.box("stage_ground", (60, 60, 0.05), (0, 0, -0.025), col, ground)
    U.box("stage_backdrop", (60, 0.2, 12), (0, 30, 6), col, U.toon({"hex": "#C9D6E3", "linear": U.lin("#C9D6E3")}))
