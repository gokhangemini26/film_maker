"""Phone proxy with a drawn screen (icons, numbers and colour only, per look.style.phone_ui).

The phone is built in its own local frame (x across, y up the screen, z out of the screen)
under an Empty, so a caller can orient it by giving three world axes. The screen is drawn with
flat emissive polygons: no text, no image files, so it works in any Blender and stays deterministic.

Spec: canon look.style.phone_screen.* (geometry, status_bar, map, call, compose, sent, hana,
states_by_shot), look.color.ui, look.color.ui_portraits, continuity.battery.
Layouts are screen fractions (x from the left edge, y from the TOP edge), see look.style.phone_screen.geometry.
"""
import glob
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import util as U

# Ren's phone (world.props.phone_ren); Hana's is PHONES["hana"]
W, H, T = 0.071, 0.147, 0.0085  # body
SW, SH = 0.062, 0.134  # screen
PHONES = {
    "ren": dict(W=0.071, H=0.147, T=0.0085, SW=0.062, SH=0.134, GW=0.068, GH=0.141, case="#5E6B7A"),
    "hana": dict(W=0.072, H=0.150, T=0.009, SW=0.063, SH=0.137, GW=0.069, GH=0.144, case="#E9DFCF"),
}
LAYER = 0.00008  # z step between painter's-order layers

# names follow the canon roles (look.color.ui and friends); aliases at the end are the old keys
DEFAULTS = {
    "screen_background": "#F6F2EC", "ink_text_and_glyphs": "#2B303B", "icon_neutral": "#6B7280",
    "icon_unanswered_grey": "#A3A8B0", "battery_outline_and_normal_fill": "#2B303B",
    "sent_bubble": "#D3E0F2", "compose_field": "#FDFCFA", "keyboard_base": "#DCD8D1",
    "keyboard_key": "#F7F5F1", "keyboard_key_pressed": "#C9C4BC", "map_land": "#E8EAE3",
    "map_road": "#FBFAF7", "map_park": "#CFE3CF", "map_water": "#C9DCEB", "map_pin": "#4A6FA5",
    "map_pin_glyph": "#FDFCFA", "photo_frame_ring": "#E3DED6", "screen_off": "#1F2029",
    "battery_red": "#E5483B", "amber": "#F5B940", "ui_heart": "#E5483B", "call_green": "#5DB37E",
    "glyph_white": "#FDFCFA",
    "portrait_ground": "#A79FC6", "hana_skin": "#F1D3BE", "hana_hair": "#2F2629", "hana_eyes": "#4A3A33",
    "hana_brows": "#2A2224", "hana_top": "#AFC8B6", "ren_skin": "#EAC7AB", "ren_hair": "#4A3A31",
    "ren_eyes": "#5B4637", "ren_brows": "#3E3029", "ren_jacket": "#7C9CC4", "ren_tshirt": "#EAE2D3",
}
# older role names some shots/callers may still carry -> canon role
ALIASES = {"map_block": "map_land", "pin_blue": "map_pin", "call_green": "call_green"}


# ------------------------------------------------------------------ state table
_SHOT_COUNT = {}


def _shot_count(scene, n):
    """Frame count of a resolved shot (09_resolved), cached; 24 if it cannot be found."""
    key = (scene, n)
    if key not in _SHOT_COUNT:
        cnt = 24
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for p in sorted(glob.glob(os.path.join(root, "projects", "*", "09_resolved", "%s_SH%03d.json" % (scene, n)))):
            try:
                cnt = int((json.load(open(p)).get("frames") or {}).get("count") or 24)
                break
            except Exception:
                pass
        _SHOT_COUNT[key] = cnt
    return _SHOT_COUNT[key]


def mid_frame(shot):
    """0-based mid-shot frame from a resolved shot's frames.count."""
    fr = shot.get("frames") or {}
    return max(0, int(fr.get("count") or 24) // 2)


def _flicker_dip(f):
    # irregular 70 % dips, 2-3 frames (look.style.phone_ui.screen_behaviour.flicker_at_1pct), as in SC04_SH020
    return f in (14, 15, 16, 20, 21)


def screen_state(scene, n, ui_assets=None, frame=None, count=None):
    """Screen state for shot scene_SHnnn at a 0-based frame (look.style.phone_screen.states_by_shot,
    continuity.battery). frame=None means 'a still': the mid-shot frame, and a blinking icon is drawn
    visible. Keys: pct, red, bolt, digits, blink, icon_visible, brightness, ui, hana_ui, frame, sent."""
    still = frame is None
    if frame is None:
        frame = (count if count else _shot_count(scene, n)) // 2
    f = int(frame)
    pct, bolt, blink, bright, ui = 5, False, False, 1.0, None
    hana_ui, sent = None, None
    if scene == "SC01":
        if n == 80:
            pct = 5 if f < 4 else 4
        elif n in (90, 100, 110):
            pct = 4
        elif n == 120:
            pct, bolt = 4, f >= 2
        elif n == 130:
            pct, bolt = 4, f < 32
            bright = 0.7 if f in (32, 33) else 1.0
        elif n == 140:
            pct = 4 if f < 2 else 3
            bright = 0.7 if f == 0 else 1.0
        elif n >= 150:
            pct = 3
        # SH010-SH070: 5 %, no bolt
    elif scene == "SC02":
        pct = 3
    elif scene == "SC03":
        pct = 3
        if n == 20:
            bolt = f >= 14
        elif n in (30, 40):
            bolt = True
        elif n == 50:
            pct, bolt = (3, True) if f < 8 else (2, False)
            bright = 0.7 if 8 <= f <= 10 else 1.0
        elif n >= 60:
            pct = 2
    elif scene == "SC04":
        if n <= 40:
            pct, blink = 1, True
            bright = 0.7 if _flicker_dip(f) else 1.0
        elif n == 50:
            pct, blink, bolt = 1, True, f >= 30
            bright = 1.0 if f >= 30 else (0.7 if _flicker_dip(f) else 1.0)
        elif n == 60:
            pct, blink, bolt = 1, True, True
        elif n == 70:
            pct = 1 if f < 2 else 2
            blink, bolt = f < 2, True
        elif n == 80:
            pct, bolt = 2, True
            ui = "compose3" if f < 8 else "sent"
            if f >= 8:
                sent = {"progress": min(1.0, (f - 8) / 24.0), "tick": f >= 34}
        elif n >= 90:
            pct, bolt = 2, f < 7
            ui, sent = "sent", {"progress": 1.0, "tick": True}
        # SC04 compose text state (lines / heart) for SH010-SH070
        if n == 50:
            ui = "compose2" if f >= 56 else "compose1"
        elif n == 60:
            ui = "compose3"
        elif n == 70:
            ui = "compose3"
    elif scene == "SC05":
        hana_ui = {10: "off" if f < 2 else "wake", 20: "wake", 30: "received"}.get(n, "wake")
        if n == 10:
            bright = 0.0 if f < 2 else min(1.0, 1 - (1 - min(1.0, (f - 2) / 2.0)) ** 2)
    elif scene == "SC06":
        pct = 2
        t = min(1.0, f / 24.0)
        bright = (1.0 - t) ** 2  # ease-out fade to off over f0-24
        ui, sent = "sent", {"progress": 1.0, "tick": True}
    if scene == "SC01" and n == 70:
        ui = "compose1"
    period_vis = (f % 24) < 12  # 1 Hz, 50 % duty, each shot starts visible
    return {"pct": pct, "red": pct <= 4, "bolt": bolt, "digits": True, "blink": blink,
            "icon_visible": True if still else (period_vis if blink else True),
            "brightness": bright, "ui": ui, "hana_ui": hana_ui, "frame": f, "sent": sent}


# ------------------------------------------------------------------ geometry helpers
def _circle_pts(cx, cy, rx, ry, n=36):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _rrect_pts(x0, y0, x1, y1, r, seg=5):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r <= 1e-9:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _clip_rect(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a polygon to an axis-aligned rectangle."""
    def clip(poly, inside, inter):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(inter(a, b))
                out.append(b)
            elif ia:
                out.append(inter(a, b))
        return out
    def ix(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def iy(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    for ins, it in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                    (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            break
        pts = clip(pts, ins, it)
    return pts


def _clip_circle(pts, cx, cy, r):
    """Project points outside the circle radially onto it (polygon stays inside the ring)."""
    out = []
    for x, y in pts:
        d = math.hypot(x - cx, y - cy)
        if d > r:
            x, y = cx + (x - cx) * r / d, cy + (y - cy) * r / d
        out.append((x, y))
    return out


def _lerp_hex(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(3))


class Screen:
    def __init__(self, parent, col, sid, colors, sw=SW, sh=SH, zs=None, bright=1.0):
        self.p, self.col, self.sid, self.c = parent, col, sid, colors
        self.sw, self.sh = sw, sh
        self.zs = zs if zs is not None else T / 2 + 0.0004
        self.k = 0
        self.bright = bright
        self.mm = sw / 0.062 * 0.001  # metres per 'Ren millimetre' of the layout entries

    # ---- coordinates: screen fractions -> local metres
    def X(self, fx):
        return (fx - 0.5) * self.sw

    def Y(self, fy):
        return (0.5 - fy) * self.sh

    def _mat(self, hexv):
        return U.flat({"hex": hexv, "linear": U.lin(hexv)}, strength=self.bright)

    def poly(self, pts, hexv, layer=1):
        """Flat emissive n-gon (points in local metres) at painter's-order layer."""
        self.k += 1
        name = f"ui{self.k}.{self.sid}"
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, 0.0)) for x, y in pts]
        if len(vs) >= 3:
            bm.faces.new(vs)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = U._obj(name, me, self.col, self._mat(hexv), (0, 0, 0))
        o.parent = self.p
        o.location.z = self.zs + layer * LAYER
        o["fm_shot"] = True
        return o

    def strip(self, outer, inner, hexv, layer=1):
        """Closed band between two equal-length point loops (rings, outlines)."""
        self.k += 1
        name = f"ui{self.k}.{self.sid}"
        bm = bmesh.new()
        vo = [bm.verts.new((x, y, 0.0)) for x, y in outer]
        vi = [bm.verts.new((x, y, 0.0)) for x, y in inner]
        n = len(vo)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = U._obj(name, me, self.col, self._mat(hexv), (0, 0, 0))
        o.parent = self.p
        o.location.z = self.zs + layer * LAYER
        o["fm_shot"] = True
        return o

    def rect(self, u0, v0, u1, v1, hexv, layer=1, r=0.0):
        """Axis-aligned (rounded) rect, local metres, corners (u0,v0)-(u1,v1)."""
        return self.poly(_rrect_pts(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1), r), hexv, layer)

    def frect(self, fx0, fy0, fx1, fy1, hexv, layer=1, r=0.0):
        return self.rect(self.X(fx0), self.Y(fy1), self.X(fx1), self.Y(fy0), hexv, layer, r)

    def line(self, p, q, w, hexv, layer=1):
        dx, dy = q[0] - p[0], q[1] - p[1]
        d = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / d * w / 2, dx / d * w / 2
        return self.poly([(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)], hexv, layer)

    def disc(self, u, v, r, hexv, layer=1):
        return self.poly(_circle_pts(u, v, r, r), hexv, layer)

    def ellipse(self, u, v, rx, ry, hexv, layer=1):
        return self.poly(_circle_pts(u, v, rx, ry, 40), hexv, layer)

    def ring(self, u, v, r_out, r_in, hexv, layer=1, n=36):
        return self.strip(_circle_pts(u, v, r_out, r_out, n), _circle_pts(u, v, r_in, r_in, n), hexv, layer)

    def glyph_poly(self, pts_box, u0, v0, w, h, hexv, layer):
        """Polygon given in a glyph box (x right, y down, 0..1); (u0,v0)=box top-left in local metres."""
        return self.poly([(u0 + gx * w, v0 - gy * h) for gx, gy in pts_box], hexv, layer)

    # ---- glyphs
    def digit(self, ch, uc, vc, hh, hexv, layer=3):
        segs = {"0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg",
                "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg"}[ch]
        t, w = hh * 0.16, hh * 0.55
        pos = {"a": (0, hh / 2 - t / 2, w, t), "d": (0, -hh / 2 + t / 2, w, t), "g": (0, 0, w, t),
               "f": (-w / 2 + t / 2, hh / 4, t, hh / 2), "b": (w / 2 - t / 2, hh / 4, t, hh / 2),
               "e": (-w / 2 + t / 2, -hh / 4, t, hh / 2), "c": (w / 2 - t / 2, -hh / 4, t, hh / 2)}
        for sg in segs:
            du, dv, sw_, sh_ = pos[sg]
            self.rect(uc + du - sw_ / 2, vc + dv - sh_ / 2, uc + du + sw_ / 2, vc + dv + sh_ / 2, hexv, layer)

    def percent(self, uc, vc, hh, hexv, layer=3):
        st = hh * 0.16
        self.line((uc - hh * 0.22, vc - hh * 0.5), (uc + hh * 0.22, vc + hh * 0.5), st, hexv, layer)
        for du, dv in ((-0.2, 0.28), (0.2, -0.28)):
            self.ring(uc + du * hh, vc + dv * hh, hh * 0.2, hh * 0.2 - st * 0.9, hexv, layer)

    BOLT = [(0.62, 0.0), (0.10, 0.58), (0.46, 0.58), (0.36, 1.0), (0.90, 0.40), (0.54, 0.40)]

    def bolt(self, uc, vc, hh, hexv, layer=4, box_w=None):
        w = box_w or hh * 0.6
        self.glyph_poly(self.BOLT, uc - w / 2, vc + hh / 2, w, hh, hexv, layer)

    def status_bar(self, st):
        """look.style.phone_screen.status_bar: right-aligned, centred on y 0.040; bolt slot always reserved."""
        c = self.c
        col = c["battery_red"] if st["red"] else c["battery_outline_and_normal_fill"]
        vc = self.Y(0.040)
        bh = 0.030 * self.sh
        bx0, bx1 = self.X(0.785), self.X(0.935)
        if st.get("icon_visible", True):
            rad = bh * 0.2
            self.rect(bx0, vc - bh / 2, bx1, vc + bh / 2, col, 2, rad)
            s = 0.6 * self.mm
            self.rect(bx0 + s, vc - bh / 2 + s, bx1 - s, vc + bh / 2 - s, c["screen_background"], 3, max(0.0, rad - s))
            ins = 1.2 * self.mm
            inner_w = (bx1 - bx0) - 2 * ins
            fw = inner_w * 0.06 * st["pct"]
            self.rect(bx0 + ins, vc - bh / 2 + ins, bx0 + ins + fw, vc + bh / 2 - ins, col, 4, max(0.0, rad - ins))
            self.rect(bx1, vc - bh * 0.2, self.X(0.950), vc + bh * 0.2, col, 2)
        hh = 0.036 * self.sh
        if st["digits"]:
            self.percent((self.X(0.710) + self.X(0.765)) / 2, vc, hh * 0.9, col)
            self.digit(str(st["pct"])[-1], (self.X(0.657) + self.X(0.700)) / 2, vc, hh, col)
        if st["bolt"]:
            self.bolt((self.X(0.593) + self.X(0.638)) / 2, vc, hh, c["amber"], 4, box_w=self.X(0.638) - self.X(0.593))

    # ---- portraits (colours from look.color.ui_portraits), clipped to the ring
    def portrait(self, fu, fv, diam_frac, subject, scale=1.0):
        c = self.c
        u, v = self.X(fu), self.Y(fv)
        R = diam_frac * self.sw / 2 * scale
        rw = 1.2 * self.mm * scale
        Ri = R - rw
        self.disc(u, v, R, c["photo_frame_ring"], 2)
        self.disc(u, v, Ri, c["portrait_ground"], 3)

        def clip(pts):
            return _clip_circle(pts, u, v, Ri)

        def ell(cx, cy, rx, ry, hexv, layer):
            self.poly(clip(_circle_pts(u + cx * Ri, v + cy * Ri, rx * Ri, ry * Ri, 44)), hexv, layer)

        def box(x0, y0, x1, y1, hexv, layer):
            self.poly(clip([(u + x0 * Ri, v + y0 * Ri), (u + x1 * Ri, v + y0 * Ri), (u + x1 * Ri, v + y1 * Ri), (u + x0 * Ri, v + y1 * Ri)]), hexv, layer)

        if subject == "hana":
            ell(0.0, -0.05, 0.50, 0.66, c["hana_hair"], 4)  # long hair behind head and shoulders
            ell(0.0, -0.98, 0.92, 0.58, c["hana_top"], 5)  # sage knit shoulders
            box(-0.12, -0.60, 0.12, -0.28, c["hana_skin"], 6)  # neck
            ell(0.0, 0.10, 0.33, 0.41, c["hana_skin"], 7)  # face
            self.poly(clip([(u - 0.36 * Ri, v + 0.16 * Ri), (u - 0.20 * Ri, v + 0.52 * Ri), (u + 0.10 * Ri, v + 0.56 * Ri), (u + 0.36 * Ri, v + 0.16 * Ri),
                            (u + 0.30 * Ri, v + 0.46 * Ri), (u + 0.0, v + 0.60 * Ri), (u - 0.30 * Ri, v + 0.46 * Ri)]), c["hana_hair"], 8)  # fringe
            eye, brow, hair_sk = c["hana_eyes"], c["hana_brows"], None
        else:
            ell(0.0, -1.0, 0.95, 0.60, c["ren_jacket"], 5)  # blue jacket
            self.poly(clip([(u - 0.26 * Ri, v - 0.50 * Ri), (u + 0.26 * Ri, v - 0.50 * Ri), (u, v - 0.86 * Ri)]), c["ren_tshirt"], 6)  # oat T-shirt at the neck
            box(-0.11, -0.56, 0.11, -0.26, c["ren_skin"], 6)  # neck
            self.poly(clip([(u - 0.11 * Ri, v - 0.52 * Ri), (u + 0.11 * Ri, v - 0.52 * Ri), (u, v - 0.66 * Ri)]), c["ren_skin"], 7)
            ell(0.0, 0.12, 0.35, 0.44, c["ren_hair"], 6)  # short hair cap
            ell(0.0, 0.03, 0.31, 0.38, c["ren_skin"], 7)  # face
            eye, brow = c["ren_eyes"], c["ren_brows"]
        for sx in (-1, 1):
            e_u, e_v = u + sx * 0.125 * Ri, v + 0.08 * Ri
            self.disc(e_u, e_v, 0.038 * Ri, eye, 9)
            self.line((e_u - 0.075 * Ri, e_v + 0.115 * Ri), (e_u + 0.075 * Ri, e_v + 0.125 * Ri), 0.03 * Ri, brow, 9)
        return R

    # ---- screens
    def call_screen(self, st, subject="hana", unanswered=False, ring_f=None):
        c = self.c
        self.portrait(0.50, 0.30, 0.60, subject)
        bu, bv = self.X(0.5), self.Y(0.80)
        br = 0.15 * self.sw
        s, hexv = 1.0, (c["icon_unanswered_grey"] if unanswered else c["call_green"])
        if ring_f is not None and not unanswered:
            ph = (ring_f % 11) / 11.0
            s = 1.0 + 0.12 * math.sin(math.pi * ph)
            hp = ph  # halo grows 100 -> 150 % and fades out
            halo = _lerp_hex(c["call_green"], c["screen_background"], min(1.0, 0.25 + 0.75 * hp))
            self.ring(bu, bv, br * (1 + 0.5 * hp), br * (1 + 0.5 * hp) - 0.0012 * self.sw / 0.062, halo, 1)
        self.disc(bu, bv, br * s, hexv, 3)
        d = 2 * br * s
        th = 0.15 * d
        R = 0.27 * d  # handset = a curved bar (arc bulging to the lower right) with a heavier earpiece and mouthpiece
        pts = []
        for i in range(11):
            a = math.radians(-55 - 100 * i / 10 + 90)  # sweep 35 deg .. 135 deg
            pts.append((bu - R * 0.45 + R * math.cos(a) * 1.0, bv - R * 0.45 + R * math.sin(a) * 1.0))
        mx = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2
        my = (min(q[1] for q in pts) + max(q[1] for q in pts)) / 2
        pts = [(x - mx + bu, y - my + bv) for x, y in pts]
        for a_, b_ in zip(pts, pts[1:]):
            self.line(a_, b_, th, c["glyph_white"], 5)
        for q in pts[1:-1]:
            self.disc(q[0], q[1], th / 2, c["glyph_white"], 5)
        for q in (pts[0], pts[-1]):
            self.disc(q[0], q[1], th * 0.85, c["glyph_white"], 5)

    def map_screen(self):
        c = self.c
        y0, y1 = 0.075, 1.0
        self.frect(0, y0, 1, y1, c["map_land"], 1)
        self.frect(0.00, 0.70, 0.19, 0.83, c["map_park"], 2)
        self.frect(0.78, 0.075, 1.0, 0.20, c["map_water"], 2)
        clipb = (self.X(0), self.Y(y1), self.X(1), self.Y(y0))
        hw = 0.085 * self.sw / 2
        for fx in (0.24, 0.73):
            self.frect(fx - 0.0425, y0, fx + 0.0425, y1, c["map_road"], 3)
        for fy in (0.24, 0.66, 0.87):
            self.frect(0, fy - 0.085 * self.sw / self.sh / 2, 1, fy + 0.085 * self.sw / self.sh / 2, c["map_road"], 3)
        p, q = (self.X(0.0), self.Y(0.40)), (self.X(1.0), self.Y(0.70))
        dx, dy = q[0] - p[0], q[1] - p[1]
        d = math.hypot(dx, dy)
        nx, ny = -dy / d * hw, dx / d * hw
        band = [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]
        self.poly(_clip_rect(band, *clipb), c["map_road"], 3)
        # pin: head circle (0.50, 0.475) d 0.16 sw, tip (0.50, 0.555)
        hu, hv = self.X(0.5), self.Y(0.475)
        R = 0.08 * self.sw
        tip = (self.X(0.5), self.Y(0.555))
        dd = hv - tip[1]
        b = math.acos(min(1.0, R / dd)) if dd > R else 0.0
        t1 = (hu + R * math.sin(b), hv - R * math.cos(b))
        t2 = (hu - R * math.sin(b), hv - R * math.cos(b))
        self.poly([t1, tip, t2], c["map_pin"], 5)
        self.disc(hu, hv, R, c["map_pin"], 5)
        G = 0.6 * 2 * R
        g = c["map_pin_glyph"]
        fu, ku = hu - 0.24 * G, hu + 0.24 * G
        self.rect(fu - 0.045 * G, hv - G / 2, fu + 0.045 * G, hv + 0.02 * G, g, 6)  # fork handle
        self.rect(fu - 0.17 * G, hv + 0.0 * G, fu + 0.17 * G, hv + 0.09 * G, g, 6)  # fork base
        for tx in (-0.135, 0.0, 0.135):
            self.rect(fu + tx * G - 0.03 * G, hv + 0.05 * G, fu + tx * G + 0.03 * G, hv + G / 2, g, 6)  # tines
        self.rect(ku - 0.045 * G, hv - G / 2, ku + 0.045 * G, hv - 0.05 * G, g, 6)  # knife handle
        self.poly([(ku - 0.07 * G, hv - 0.05 * G), (ku + 0.09 * G, hv - 0.05 * G), (ku + 0.09 * G, hv + 0.36 * G), (ku + 0.05 * G, hv + G / 2), (ku - 0.07 * G, hv + 0.30 * G)], g, 6)

    def keyboard(self, pressed=None):
        c = self.c
        self.frect(0, 0.56, 1, 1.0, c["keyboard_base"], 1)
        kw, kh = 5.4 * self.mm, 10.7 * self.mm
        rows = [0.610, 0.708, 0.806, 0.904]

        def key(fx, fy, w=None, hexv=None):
            u, v = self.X(fx), self.Y(fy)
            w = w if w is not None else kw
            self.rect(u - w / 2, v - kh / 2, u + w / 2, v + kh / 2, hexv or c["keyboard_key"], 2, 0.0013)
            return u, v

        for i in range(10):
            key(0.05 + 0.10 * i, rows[0])
        for i in range(9):
            key(0.10 + 0.10 * i, rows[1])
        for i in range(7):
            key(0.16 + 0.10 * i, rows[2])
        # backspace x 0.855-0.99 with an ink backspace arrow
        bw = (0.99 - 0.855) * self.sw
        bu, bv = key((0.855 + 0.99) / 2, rows[2], bw)
        ink, kk = c["ink_text_and_glyphs"], c["keyboard_key"]
        gw, gh = 0.62 * bw, 0.30 * kh
        self.poly([(bu - gw / 2, bv), (bu - gw / 2 + gh * 0.6, bv + gh / 2), (bu + gw / 2, bv + gh / 2), (bu + gw / 2, bv - gh / 2), (bu - gw / 2 + gh * 0.6, bv - gh / 2)], ink, 4)
        xc, xr = bu + gw * 0.12, gh * 0.18
        self.line((xc - xr, bv - xr), (xc + xr, bv + xr), gh * 0.13, kk, 5)
        self.line((xc - xr, bv + xr), (xc + xr, bv - xr), gh * 0.13, kk, 5)
        # row 4: emoji key, space bar, blank key
        eu, ev = key((0.01 + 0.145) / 2, rows[3], (0.145 - 0.01) * self.sw)
        er = 0.20 * kh
        self.ring(eu, ev, er, er * 0.80, c["icon_neutral"], 4)
        for sx in (-1, 1):
            self.disc(eu + sx * er * 0.36, ev + er * 0.20, er * 0.10, c["icon_neutral"], 4)
        smile = [(eu + er * 0.5 * math.cos(math.radians(a)), ev - er * 0.08 + er * 0.5 * math.sin(math.radians(a))) for a in range(200, 341, 20)]
        for a, b in zip(smile, smile[1:]):
            self.line(a, b, er * 0.13, c["icon_neutral"], 4)
        key((0.26 + 0.74) / 2, rows[3], (0.74 - 0.26) * self.sw)
        key((0.855 + 0.99) / 2, rows[3], (0.99 - 0.855) * self.sw)

    LINES = [("Are you free tonight?", 42.0), ("Dinner at 8?", 24.0), ("My treat.", 19.0)]

    def heart(self, u, v, h, hexv, layer=5):
        pts = []
        for i in range(40):
            t = 2 * math.pi * i / 40
            pts.append((16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
        s = h / 29.0
        self.poly([(u + x * s, v + (y + 2.5) * s) for x, y in pts], hexv, layer)

    def text_bars(self, u_left, v_first, lines, prog=1.0, heart_f=False, layer=4):
        """The invitation as ink bars (preview proxy): one bar per line, height = cap height."""
        ink = self.c["ink_text_and_glyphs"]
        cap = 0.021 * self.sh
        pitch = 0.040 * self.sh
        last_u = None
        for i in range(lines):
            L = self.LINES[i][1] * self.mm * (prog if i == lines - 1 else 1.0)
            v = v_first - pitch * i
            if L > 1e-5:
                self.rect(u_left, v - cap / 2, u_left + L, v + cap / 2, ink, layer)
            last_u = (u_left + L, v)
        if heart_f and last_u:
            self.heart(last_u[0] + 1.6 * self.mm + 1.7 * self.mm, last_u[1], 1.1 * cap, self.c["ui_heart"])

    def compose(self, lines=1, prog=1.0, heart=False, send_pressed=False):
        c = self.c
        if lines > 0:
            top = 0.545 - (0.020 + 0.040 * lines)
            self.frect(0.03, top, 0.86, 0.545, c["compose_field"], 2, 4.0 * self.mm)
            self.text_bars(self.X(0.03) + 2.2 * self.mm, self.Y(top + 0.010 + 0.020), lines, prog, heart)
            if heart is False or True:
                cur_u = self.X(0.03) + 2.2 * self.mm
        else:
            self.frect(0.03, 0.485, 0.86, 0.545, c["compose_field"], 2, 4.0 * self.mm)
        # send button (0.925, 0.515), d 0.105 sw, up-arrow in #FDFCFA
        su, sv = self.X(0.925), self.Y(0.515)
        sr = 0.105 * self.sw / 2
        self.disc(su, sv, sr, c["ink_text_and_glyphs"] if send_pressed else c["icon_neutral"], 2)
        w = c["glyph_white"]
        self.poly([(su, sv + sr * 0.55), (su - sr * 0.5, sv + sr * 0.02), (su + sr * 0.5, sv + sr * 0.02)], w, 4)
        self.rect(su - sr * 0.13, sv - sr * 0.5, su + sr * 0.13, sv + sr * 0.05, w, 4)
        self.keyboard()

    def sent(self, sent=None):
        c = self.c
        sent = sent or {"progress": 1.0, "tick": True}
        self.compose(lines=0)
        self.frect(0.19, 0.265, 0.95, 0.405, c["sent_bubble"], 2, 3.7 * self.mm)
        self.text_bars(self.X(0.19) + 2.2 * self.mm, self.Y(0.265 + 0.020 + 0.0), 3, 1.0, False, 4)
        # progress line: centre y 0.435, x 0.19-0.80, round ends, fills left to right
        p = max(0.0, min(1.0, sent["progress"]))
        th = 0.008 * self.sh
        x0, x1 = 0.19, 0.19 + (0.80 - 0.19) * p
        if p > 0.0:
            self.rect(self.X(x0), self.Y(0.435) - th / 2, max(self.X(x1), self.X(x0) + th), self.Y(0.435) + th / 2, c["amber"], 3, th / 2)
        if sent["tick"]:
            self.tick(self.X(0.885), self.Y(0.435), 6.6 * self.mm, 6.0 * self.mm, 1.3 * self.mm)

    def tick(self, uc, vc, w, h, stroke):
        pts = [(0.0, 0.55), (0.38, 1.0), (1.0, 0.0)]  # x right, y down, short arm lower left, long arm rising right
        P = [(uc - w / 2 + gx * w, vc + h / 2 - gy * h) for gx, gy in pts]
        for a, b in zip(P, P[1:]):
            self.line(a, b, stroke, self.c["amber"], 4)
        for q in P:
            self.disc(q[0], q[1], stroke / 2, self.c["amber"], 4)

    def hana_received(self):
        c = self.c
        self.frect(0.05, 0.265, 0.81, 0.405, c["sent_bubble"], 2, 3.7 * self.mm)
        self.text_bars(self.X(0.05) + 2.2 * self.mm, self.Y(0.265 + 0.020), 3, 1.0, False, 4)


def build_phone(col, sid, center, x_axis, y_axis, z_axis, ui_assets, st, colors, body_hex=None, screen_on=True,
                phone=None, W=None, H=None, T=None, SW=None, SH=None, subject=None):
    """Return the parent Empty. Axes are world vectors: x across, y up the screen, z out of the screen.
    phone: 'ren' or 'hana' picks size and case colour (default: 'hana' when the UI is ui.photo_only, else 'ren');
    W,H,T,SW,SH override the size (defaults = that phone's canon size). body_hex overrides the case colour;
    the legacy dark greys are ignored so the canon case colours show."""
    ui = set(ui_assets)
    phone = phone or ("hana" if "ui.photo_only" in ui else "ren")
    d = PHONES[phone]
    w_, h_, t_ = W or d["W"], H or d["H"], T or d["T"]
    sw_, sh_ = SW or d["SW"], SH or d["SH"]
    if body_hex in (None, "#33333D", "#3D3A4A"):
        body_hex = d["case"]
    e = bpy.data.objects.new("phone." + sid, None)
    col.objects.link(e)
    m = Matrix((x_axis.normalized(), y_axis.normalized(), z_axis.normalized())).transposed().to_4x4()
    e.matrix_world = m
    e.location = center
    e["fm_shot"] = True
    body = U.box("phone_body." + sid, (w_, h_, t_), (0, 0, 0), col, U.toon({"hex": body_hex, "linear": U.lin(body_hex)}))
    body.parent = e
    body["fm_shot"] = True
    zs = t_ / 2 + 0.0004
    bright = st.get("brightness", 1.0)
    # front glass (screen_off colour), always present; the case shows as a lip around it
    gw, gh = d["GW"] * (sw_ / d["SW"]), d["GH"] * (sh_ / d["SH"])
    glass = Screen(e, col, sid, colors, sw_, sh_, zs, 1.0)
    glass.poly(_rrect_pts(-gw / 2, -gh / 2, gw / 2, gh / 2, 0.006), colors["screen_off"], -1)
    if not screen_on or bright <= 0.001:
        return e
    sc = Screen(e, col, sid, colors, sw_, sh_, zs, bright)
    sc.poly(_rrect_pts(-sw_ / 2, -sh_ / 2, sw_ / 2, sh_ / 2, 0.005), colors["screen_background"], 0)
    if phone == "hana":  # Hana's phone never shows a status bar
        h_ui = st.get("hana_ui") or "wake"
        if h_ui == "received":
            sc.hana_received()
        else:
            scale = 0.96 if (st.get("scene_n") == 10 and st.get("frame", 9) < 5) else 1.0
            sc.portrait(0.50, 0.30, 0.60, subject or "ren", scale)
        return e
    ui_state = st.get("ui")
    subj = subject or "hana"
    if "ui.map_pin_screen" in ui:
        sc.map_screen()
    elif "ui.call_screen" in ui:
        f = st.get("frame", 0)
        ring = f if (st.get("call") == "ringing") else None
        sc.call_screen(st, subj, unanswered=(st.get("call") == "unanswered"), ring_f=ring)
    elif ("ui.thread_sent_bubble" in ui and ui_state in (None, "sent")) or ui_state == "sent":
        sc.sent(st.get("sent"))
    elif ui & {"ui.compose_field"} or (ui_state or "").startswith("compose"):
        lines = {"compose1": 1, "compose2": 2, "compose3": 3}.get(ui_state, 1)
        prog = 1.0
        if st.get("typing1"):
            prog = st["typing1"]
        heart = bool(st.get("heart"))
        sc.compose(lines, prog, heart, send_pressed=bool(st.get("send_pressed")))
    sc.status_bar(st)  # every screen-on state of Ren's phone shows the status bar
    return e


def colors_for(shot, canon):
    c = dict(DEFAULTS)

    def take(role, hexv):
        role = ALIASES.get(role, role)
        if hexv and role in c:
            c[role] = hexv

    for key in ("look.color.ui", "look.color.ui_portraits"):
        v = canon.get(key)
        if isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    take(d.get("role"), d.get("hex"))
    dom = (shot.get("color") or {}).get("dominant") or []
    if isinstance(dom, dict):
        dom = dom.get("value") or []
    for d in dom:
        if isinstance(d, dict):
            take(d.get("role"), d.get("hex"))
    for key, name in (("look.color.accent_battery_red", "battery_red"), ("look.color.accent_power_amber", "amber"),
                      ("look.color.ui_heart", "ui_heart"), ("look.color.accent_call_green", "call_green")):
        v = canon.get(key) or {}
        if isinstance(v, dict) and v.get("hex"):
            c[name] = v["hex"]
    return c
