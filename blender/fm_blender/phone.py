"""Phone proxy with a drawn screen (icons, numbers and colour only, per look.style.phone_ui).

The phone is built in its own local frame (x across, y up the screen, z out of the screen)
under an Empty, so a caller can orient it by giving three world axes. The screen is drawn with
flat emissive planes: no text, no image files, so it works in any Blender and stays deterministic.
"""
import math

import bpy
from mathutils import Matrix, Vector

from . import util as U

W, H, T = 0.071, 0.147, 0.0085  # body
SW, SH = 0.062, 0.134  # screen
ZS = T / 2 + 0.0004  # screen plane height above body centre

DEFAULTS = {
    "screen_background": "#F6F2EC", "ink_text_and_glyphs": "#2B303B", "icon_neutral": "#6B7280",
    "icon_unanswered_grey": "#A3A8B0", "sent_bubble": "#D3E0F2", "compose_field": "#FDFCFA",
    "keyboard_base": "#DCD8D1", "keyboard_key": "#F7F5F1", "battery_red": "#C8321E", "amber": "#F5B940",
    "map_road": "#FFFFFF", "map_block": "#E7E1D5", "pin_blue": "#4A7FD0", "call_green": "#5DBB7E",
    "photo_skin": "#E9B99A", "photo_hair": "#4A3A34", "photo_bg": "#C9BFDA",
}


def screen_state(scene, n, ui_assets):
    """Battery/bolt state from continuity.battery, by beat. Returns dict."""
    st = {"pct": 5, "red": False, "bolt": False, "digits": True, "blink": False}
    if scene == "SC01":
        if n >= 120:
            st.update(pct=3, red=True, bolt=(n < 140))
        elif n >= 70:
            st.update(pct=4, red=True, bolt=True)
    elif scene == "SC02":
        st.update(pct=3, red=True, bolt=True)
    elif scene == "SC03":
        st.update(pct=2, red=True, bolt=False)
    elif scene == "SC04":
        if n >= 70:
            st.update(pct=2, red=True, bolt=True)
        else:
            st.update(pct=1, red=True, digits=False, blink=True)
    elif scene == "SC06":
        st.update(pct=2, red=True, bolt=False)
    return st


class Screen:
    def __init__(self, parent, col, sid, colors):
        self.p, self.col, self.sid, self.c = parent, col, sid, colors
        self.k = 0

    def _mat(self, hexv, s=1.0):
        return U.flat({"hex": hexv, "linear": U.lin(hexv)}, strength=s)

    def _fin(self, o, z):
        o.parent = self.p
        o.location.z = z
        o["fm_shot"] = True
        return o

    def rect(self, u, v, w, h, hexv, z=0.0, rot=0.0, s=1.0):
        self.k += 1
        o = U.box(f"ui{self.k}.{self.sid}", (w, h, 0.0004), (u, v, 0), self.col, self._mat(hexv, s), rot=(0, 0, rot))
        return self._fin(o, ZS + 0.0002 + z)

    def disc(self, u, v, r, hexv, z=0.0, s=1.0):
        self.k += 1
        o = U.cyl(f"ui{self.k}.{self.sid}", r, 0.0004, (u, v, 0), self.col, self._mat(hexv, s), segs=24)
        return self._fin(o, ZS + 0.0002 + z)

    # ---- glyphs ----
    def digit(self, ch, u, v, hh, hexv):
        segs = {"0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg",
                "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg"}[ch]
        t = hh * 0.16
        w = hh * 0.55
        pos = {"a": (0, hh / 2 - t / 2, w, t), "d": (0, -hh / 2 + t / 2, w, t), "g": (0, 0, w, t),
               "f": (-w / 2 + t / 2, hh / 4, t, hh / 2), "b": (w / 2 - t / 2, hh / 4, t, hh / 2),
               "e": (-w / 2 + t / 2, -hh / 4, t, hh / 2), "c": (w / 2 - t / 2, -hh / 4, t, hh / 2)}
        for sg in segs:
            du, dv, sw, sh = pos[sg]
            self.rect(u + du, v + dv, sw, sh, hexv, z=0.0003)

    def percent(self, u, v, hh, hexv):
        self.rect(u, v, hh * 0.09, hh * 0.9, hexv, z=0.0003, rot=math.radians(-30))
        self.disc(u - hh * 0.2, v + hh * 0.28, hh * 0.11, hexv, z=0.0003)
        self.disc(u + hh * 0.2, v - hh * 0.28, hh * 0.11, hexv, z=0.0003)

    def bolt(self, u, v, hh, hexv):
        self.rect(u + hh * 0.06, v + hh * 0.2, hh * 0.22, hh * 0.65, hexv, z=0.0003, rot=math.radians(18))
        self.rect(u - hh * 0.06, v - hh * 0.2, hh * 0.22, hh * 0.65, hexv, z=0.0003, rot=math.radians(18))

    def status_bar(self, st):
        ink, red = self.c["ink_text_and_glyphs"], self.c["battery_red"]
        col = red if st["red"] else ink
        top = SH / 2 - 0.013
        right = SW / 2 - 0.006
        bw, bh = 0.022, 0.0105
        bu = right - bw / 2 - 0.002
        self.rect(bu, top, bw, bh, col, z=0.0003)  # outline
        self.rect(bu, top, bw - 0.0032, bh - 0.0032, self.c["screen_background"], z=0.0005)
        fill = max(0.12, min(1.0, st["pct"] / 100.0 * 6)) if not st["blink"] else 0.12
        fw = (bw - 0.005) * fill
        self.rect(bu - (bw - 0.005) / 2 + fw / 2, top, fw, bh - 0.005, col, z=0.0007)
        self.rect(right + 0.0006, top, 0.0016, bh * 0.4, col, z=0.0003)  # cap
        u = bu - bw / 2 - 0.004
        if st["digits"]:
            hh = 0.0125
            self.percent(u - hh * 0.3, top, hh, col)
            u -= hh * 0.85
            for ch in reversed(str(st["pct"])):
                self.digit(ch, u, top, hh, col)
                u -= hh * 0.85
        if st["bolt"]:
            self.bolt(u - 0.002, top, 0.0125, self.c["amber"])

    def photo(self, u, v, r):
        self.disc(u, v, r, self.c["photo_bg"], z=0.0002)
        self.disc(u, v - r * 0.15, r * 0.5, self.c["photo_hair"], z=0.0004)
        self.disc(u, v - r * 0.2, r * 0.42, self.c["photo_skin"], z=0.0006)
        self.disc(u, v - r * 0.95, r * 0.7, self.c["photo_skin"], z=0.0005)

    def call_screen(self, st):
        self.photo(0, 0.022, 0.019)
        self.disc(0, -0.040, 0.0125, self.c["call_green"], z=0.0002)
        self.rect(0, -0.040, 0.0075, 0.0028, "#FFFFFF", z=0.0005, rot=math.radians(-40))

    def map_screen(self):
        bg = self.c["map_block"]
        self.rect(0, 0, SW, SH * 0.88, bg, z=0.0001)
        for v in (0.035, -0.02, -0.048):
            self.rect(0, v, SW, 0.0055, self.c["map_road"], z=0.0002)
        for u in (-0.016, 0.014):
            self.rect(u, 0, 0.0055, SH * 0.88, self.c["map_road"], z=0.0002)
        self.rect(0.004, 0.015, SW, 0.0035, self.c["map_road"], z=0.0002, rot=math.radians(-25))
        self.disc(0.0, 0.006, 0.0065, self.c["pin_blue"], z=0.0004)
        self.rect(0.0, -0.004, 0.005, 0.009, self.c["pin_blue"], z=0.0004, rot=math.radians(45))
        self.rect(0.0, 0.006, 0.0013, 0.007, "#FFFFFF", z=0.0006)

    def keyboard(self, top_v=-0.005):
        base_h = SH / 2 + top_v
        self.rect(0, top_v - base_h / 2, SW, base_h, self.c["keyboard_base"], z=0.0001)
        rows = 4
        kh = (base_h - 0.006) / rows
        for r in range(rows):
            cols = 6 if r < 3 else 3
            kw = (SW - 0.004) / 6
            for k in range(cols):
                cu = (k - (cols - 1) / 2) * kw
                self.rect(cu, top_v - 0.004 - kh * (r + 0.5), kw - 0.002, kh - 0.002, self.c["keyboard_key"], z=0.0003)
        self.disc(-0.024, top_v - 0.004 - kh * 3.5, 0.0035, self.c["icon_neutral"], z=0.0006)  # emoji key

    def compose(self):
        self.rect(0, 0.052, SW - 0.006, 0.022, self.c["compose_field"], z=0.0002)
        self.rect(0.0, 0.052, SW - 0.02, 0.0025, self.c["ink_text_and_glyphs"], z=0.0004)
        self.rect(-0.006, 0.045, SW - 0.032, 0.0025, self.c["ink_text_and_glyphs"], z=0.0004)
        self.disc(0.024, 0.0625, 0.004, self.c["icon_neutral"], z=0.0005)
        self.keyboard()

    def sent(self):
        self.rect(0.008, 0.035, SW - 0.026, 0.026, self.c["sent_bubble"], z=0.0002)
        self.rect(0.004, 0.038, SW - 0.036, 0.0025, self.c["ink_text_and_glyphs"], z=0.0004)
        self.rect(-0.003, 0.031, SW - 0.05, 0.0025, self.c["ink_text_and_glyphs"], z=0.0004)
        self.rect(0.0, 0.016, SW - 0.02, 0.0016, self.c["amber"], z=0.0003)  # progress line
        # tick, lower right of bubble
        self.rect(0.0195, 0.019, 0.0028, 0.0085, self.c["amber"], z=0.0005, rot=math.radians(-40))
        self.rect(0.0235, 0.021, 0.0028, 0.0125, self.c["amber"], z=0.0005, rot=math.radians(35))


def build_phone(col, sid, center, x_axis, y_axis, z_axis, ui_assets, st, colors, body_hex="#33333D", screen_on=True):
    """Return the parent Empty. Axes are world vectors: x across, y up the screen, z out of the screen."""
    e = bpy.data.objects.new("phone." + sid, None)
    col.objects.link(e)
    m = Matrix((x_axis.normalized(), y_axis.normalized(), z_axis.normalized())).transposed().to_4x4()
    e.matrix_world = m
    e.location = center
    e["fm_shot"] = True
    body = U.box("phone_body." + sid, (W, H, T), (0, 0, 0), col, U.toon({"hex": body_hex, "linear": U.lin(body_hex)}))
    body.parent = e
    body["fm_shot"] = True
    if not screen_on:
        return e
    sc = Screen(e, col, sid, colors)
    sc.rect(0, 0, SW, SH, colors["screen_background"], z=0.0, s=1.0)
    ui = set(ui_assets)
    if "ui.photo_only" in ui:
        sc.photo(0, 0.012, 0.02)
        return e
    if "ui.map_pin_screen" in ui:
        sc.map_screen()
    if "ui.call_screen" in ui:
        sc.call_screen(st)
    if "ui.compose_field" in ui:
        sc.compose()
    if "ui.thread_sent_bubble" in ui:
        sc.sent()
    if ui & {"ui.status_bar", "ui.map_pin_screen", "ui.call_screen"} and not (ui & {"ui.compose_field"}):
        sc.status_bar(st)
    elif not ui:
        sc.status_bar(st)
    return e


def colors_for(shot, canon):
    c = dict(DEFAULTS)
    dom = (shot.get("color") or {}).get("dominant") or []
    if isinstance(dom, dict):
        dom = dom.get("value") or []
    for d in dom:
        if isinstance(d, dict) and d.get("role") in c and d.get("hex"):
            c[d["role"]] = d["hex"]
    for key, name in (("look.color.accent_battery_red", "battery_red"), ("look.color.accent_power_amber", "amber")):
        v = canon.get(key) or {}
        if isinstance(v, dict) and v.get("hex"):
            c[name] = v["hex"]
    return c
