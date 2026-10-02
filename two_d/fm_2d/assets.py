"""Reusable 2D illustration assets (original designs) for FILM_MAKER 2D films.

Each draw_* function draws in local coordinates; callers position with
canvas.translate/scale. Expensive geometry is cached at module level.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

import skia

from .core import (clamp, ease_out, fill, hexc, lerp, lin, mix, partial_path, poly, rad, rrect, smooth,
                   smooth_path, stroke)

# Shared palette (proposed look; becomes canon at G4).
PAL = {
    "night": "#0b1026", "night2": "#141a3a", "indigo": "#232a5c",
    "amber": "#ffb347", "coral": "#ff7a6b", "rose": "#f2a5a0", "bone": "#efe2c6",
    "cyan": "#38e1ff", "teal": "#1fb5c9", "violet": "#8b7bff",
    "white": "#f4f6fb", "steel": "#b9c3d6", "steel_d": "#6b7690", "ink": "#121733",
}


# ============================================================== ROBOT
def draw_robot(cv, t, eye_dx=0.0, eye_dy=0.0, blink=0.0, head_tilt=0.0, shoulder=60.0, elbow=-30.0,
               mood="neutral", hold=None, bob=True, scale=1.0, rim="#38e1ff", arm_shake=0.0):
    """Hovering domestic robot. Origin = point under hover pad. Height ~430.
    shoulder/elbow in degrees (0 = arm pointing right/forward, positive = down).
    hold(cv) is called in the hand's frame (x forward along hand) to draw a held object.
    Returns hand position in local coords."""
    cv.save()
    cv.scale(scale, scale)
    by = -10 + (math.sin(t * 2.4) * 6 if bob else 0)

    # hover glow + shadow
    cv.drawOval(skia.Rect.MakeXYWH(-95, -12, 190, 24), fill(hexc("#000000", 0.35), blur=10))
    cv.drawOval(skia.Rect.MakeXYWH(-70, by - 30, 140, 50), fill(hexc(rim, 0.35), blur=22))

    cv.translate(0, by)
    # back arm (behind the body, relaxed)
    _arm(cv, -66, -200, 104 + 4 * math.sin(t * 1.7), -48, hexc("#7e89a6"), hexc("#5d6788"), None, 0)
    # hover pad
    pad = rrect(-70, -58, 140, 34, 17)
    cv.drawPath(pad, fill(0, shader=lin((0, -58), (0, -24), [hexc("#3a4364"), hexc("#1d2340")])))
    cv.drawOval(skia.Rect.MakeXYWH(-46, -32, 92, 12), fill(hexc(rim, 0.95), blur=3))

    # body
    body = skia.Path()
    body.moveTo(-78, -70)
    body.cubicTo(-92, -150, -88, -215, -60, -238)
    body.lineTo(60, -238)
    body.cubicTo(88, -215, 92, -150, 78, -70)
    body.cubicTo(50, -54, -50, -54, -78, -70)
    body.close()
    cv.drawPath(body, fill(0, shader=lin((-90, -200), (90, -80), [hexc("#ffffff"), hexc("#dfe6f2"),
                                                                    hexc("#9aa6c0")], [0, 0.55, 1])))
    cv.drawPath(body, stroke(hexc("#7d89a8", 0.6), 2))
    # belly panel + chest light
    cv.drawPath(rrect(-44, -190, 88, 80, 22), fill(hexc("#c8d1e3")))
    cv.drawPath(rrect(-44, -190, 88, 80, 22), stroke(hexc("#8d98b4", 0.7), 2))
    beat = 0.6 + 0.4 * math.sin(t * 3.0)
    cv.drawCircle(0, -150, 22, fill(hexc(rim, 0.55 * beat), blur=14))
    cv.drawCircle(0, -150, 14, fill(0, shader=rad((-4, -154), 16, [hexc("#ffffff"), hexc(rim)])))
    for i in range(3):
        cv.drawPath(rrect(-30 + i * 22, -100, 16, 6, 3), fill(hexc("#8d98b4")))

    # neck
    cv.drawPath(rrect(-16, -262, 32, 30, 8), fill(hexc("#4a5374")))

    # head
    cv.save()
    cv.translate(0, -262)
    cv.rotate(head_tilt)
    head = rrect(-108, -150, 216, 150, 52)
    cv.drawPath(head, fill(0, shader=lin((-100, -150), (100, 0), [hexc("#ffffff"), hexc("#e3e9f4"),
                                                                    hexc("#a3aec6")], [0, 0.5, 1])))
    cv.drawPath(head, stroke(hexc("#7d89a8", 0.6), 2))
    # ear pods
    for sx in (-1, 1):
        cv.drawPath(rrect(sx * 108 - 12, -100, 24, 50, 10), fill(hexc("#9aa6c0")))
        cv.drawCircle(sx * 112, -75, 5, fill(hexc(rim, 0.9)))
    # antenna
    cv.drawLine(0, -150, 6, -196, stroke(hexc("#6b7690"), 5))
    ab = 0.7 + 0.3 * math.sin(t * 5)
    cv.drawCircle(6, -200, 16, fill(hexc(rim, 0.5 * ab), blur=10))
    cv.drawCircle(6, -200, 9, fill(hexc(rim)))
    # visor
    visor = rrect(-84, -128, 168, 100, 36)
    cv.drawPath(visor, fill(0, shader=lin((0, -128), (0, -28), [hexc("#1b2348"), hexc("#0a0f26")])))
    cv.drawPath(visor, stroke(hexc(rim, 0.35), 3))
    # visor reflection
    refl = skia.Path()
    refl.moveTo(-70, -112)
    refl.cubicTo(-40, -124, 10, -124, 40, -118)
    refl.lineTo(30, -108)
    refl.cubicTo(0, -112, -40, -112, -64, -100)
    refl.close()
    cv.drawPath(refl, fill(hexc("#ffffff", 0.12)))
    # eyes
    cv.save()
    cv.clipPath(visor, doAntiAlias=True)
    eh = 40 * (1 - clamp(blink))
    for sx in (-1, 1):
        ex, ey = sx * 36 + eye_dx * 14, -78 + eye_dy * 10
        if mood == "confused" and sx == 1:
            ehh = eh * 0.55
            ey -= 6
        elif mood == "happy":
            ehh = eh * 0.5
        else:
            ehh = eh
        ehh = max(ehh, 4)
        cv.drawPath(rrect(ex - 16, ey - ehh / 2, 32, ehh, 15), fill(hexc(rim, 0.6), blur=12))
        cv.drawPath(rrect(ex - 13, ey - ehh / 2, 26, ehh, 13), fill(hexc("#bff6ff")))
        if mood == "confused":
            # one raised "brow" line
            cv.drawLine(ex - 16, ey - ehh / 2 - 14 - (8 if sx == 1 else 0), ex + 16,
                        ey - ehh / 2 - 14 + (4 if sx == 1 else 0), stroke(hexc(rim, 0.9), 5))
    cv.restore()
    cv.restore()  # head

    # front arm
    hand = _arm(cv, 70, -200, shoulder, elbow, hexc("#eef2f8"), hexc("#a9b4cb"), hold, arm_shake, t)
    cv.restore()
    return (hand[0] * scale, (hand[1] + by) * scale)


def _arm(cv, sx, sy, shoulder, elbow, c1, c2, hold, arm_shake, t=0.0):
    l1, l2 = 92, 84
    a1 = math.radians(shoulder)
    ex, ey = sx + l1 * math.cos(a1), sy + l1 * math.sin(a1)
    a2 = a1 + math.radians(elbow + arm_shake * math.sin(t * 40))
    hx, hy = ex + l2 * math.cos(a2), ey + l2 * math.sin(a2)
    p = skia.Path()
    p.moveTo(sx, sy)
    p.lineTo(ex, ey)
    p.lineTo(hx, hy)
    cv.drawPath(p, stroke(c2, 30))
    cv.drawPath(p, stroke(c1, 22))
    cv.drawCircle(sx, sy, 20, fill(c2))
    cv.drawCircle(sx, sy, 14, fill(c1))
    cv.drawCircle(ex, ey, 15, fill(c2))
    cv.drawCircle(ex, ey, 9, fill(hexc("#38e1ff", 0.9)))
    # clamp hand
    cv.save()
    cv.translate(hx, hy)
    cv.rotate(math.degrees(a2))
    cv.drawCircle(0, 0, 16, fill(c2))
    for s in (-1, 1):
        f = skia.Path()
        f.moveTo(4, s * 6)
        f.cubicTo(22, s * 18, 36, s * 16, 40, s * 6)
        cv.drawPath(f, stroke(c2, 9))
    if hold is not None:
        cv.save()
        cv.translate(34, 0)
        hold(cv)
        cv.restore()
    cv.restore()
    return hx, hy


# ============================================================== PLATE
def draw_plate(cv, r=70, tint="#f4f6fb", crack=0.0):
    cv.drawCircle(0, 0, r, fill(0, shader=rad((-r * 0.3, -r * 0.35), r * 1.4,
                                               [hexc("#ffffff"), hexc(tint), hexc("#aeb9cf")], [0, 0.5, 1])))
    cv.drawCircle(0, 0, r * 0.66, stroke(hexc("#9aa6c0", 0.7), 3))
    cv.drawCircle(0, 0, r * 0.82, stroke(hexc("#ff7a6b", 0.8), 4))
    cv.drawCircle(0, 0, r, stroke(hexc("#7e89a6"), 2.5))
    if crack > 0:
        c = skia.Path()
        c.moveTo(-r * 0.1, -r)
        c.lineTo(r * 0.05, -r * 0.5)
        c.lineTo(-r * 0.12, -r * 0.1)
        c.lineTo(r * 0.15, r * 0.35)
        cv.drawPath(partial_path(c, crack), stroke(hexc("#3a4364"), 3))


# ============================================================== DISHWASHER / KITCHEN
def draw_kitchen(cv, w=1920, h=1080, floor_y=860):
    # wall
    cv.drawRect(skia.Rect.MakeXYWH(0, 0, w, floor_y), fill(0, shader=lin((0, 0), (0, floor_y),
                                                                      [hexc("#1c2550"), hexc("#2b3570")])))
    # wall tiles
    for yy in range(140, 470, 52):
        cv.drawLine(0, yy, w, yy, stroke(hexc("#ffffff", 0.05), 2))
    for i, yy in enumerate(range(140, 470, 52)):
        off = 0 if i % 2 == 0 else 52
        for xx in range(-52 + off, w, 104):
            cv.drawLine(xx, yy, xx, yy + 52, stroke(hexc("#ffffff", 0.05), 2))
    # window light
    cv.drawRect(skia.Rect.MakeXYWH(1180, 120, 420, 300), fill(hexc("#38e1ff", 0.05)))
    cv.drawRect(skia.Rect.MakeXYWH(1180, 120, 420, 300), stroke(hexc("#ffffff", 0.08), 6))
    # upper cabinets
    for i in range(3):
        x = 160 + i * 250
        cv.drawPath(rrect(x, 40, 230, 260, 12), fill(hexc("#30396f")))
        cv.drawPath(rrect(x + 12, 52, 206, 236, 8), stroke(hexc("#ffffff", 0.06), 3))
        cv.drawPath(rrect(x + 100, 250, 30, 8, 4), fill(hexc("#8d98b4")))
    # counter
    cv.drawRect(skia.Rect.MakeXYWH(0, 470, w, 26), fill(hexc("#e8dcc3")))
    cv.drawRect(skia.Rect.MakeXYWH(0, 494, w, 8), fill(hexc("#000000", 0.25)))
    # lower cabinets
    cv.drawRect(skia.Rect.MakeXYWH(0, 502, w, floor_y - 502), fill(hexc("#2a3366")))
    for x in range(0, w, 240):
        cv.drawPath(rrect(x + 10, 516, 220, floor_y - 530, 8), stroke(hexc("#ffffff", 0.06), 3))
    # counter props: kettle, plant, fruit bowl, pendant lamp
    kx, ky = 250, 470
    cv.drawPath(rrect(kx - 50, ky - 90, 100, 90, 30), fill(0, shader=lin((kx - 50, 0), (kx + 50, 0), [
        hexc("#ff9a8a"), hexc("#ff7a6b"), hexc("#c24f48")])))
    cv.drawPath(rrect(kx - 20, ky - 104, 40, 16, 8), fill(hexc("#2b3570")))
    sp = skia.Path()
    sp.moveTo(kx + 46, ky - 60)
    sp.quadTo(kx + 86, ky - 70, kx + 94, ky - 98)
    cv.drawPath(sp, stroke(hexc("#c24f48"), 12))
    px, py = 1560, 470
    cv.drawPath(poly([(px - 46, py - 70), (px + 46, py - 70), (px + 34, py), (px - 34, py)]),
                fill(hexc("#e8dcc3")))
    for i, (ang, ln) in enumerate([(-100, 120), (-70, 100), (-125, 95), (-50, 80), (-145, 70), (-88, 140)]):
        a = math.radians(ang)
        lf = skia.Path()
        lf.moveTo(px, py - 70)
        lf.quadTo(px + math.cos(a + 0.4) * ln * 0.6, py - 70 + math.sin(a + 0.4) * ln * 0.6,
                  px + math.cos(a) * ln, py - 70 + math.sin(a) * ln)
        lf.quadTo(px + math.cos(a - 0.4) * ln * 0.6, py - 70 + math.sin(a - 0.4) * ln * 0.6, px, py - 70)
        cv.drawPath(lf, fill(hexc("#3f8f7a" if i % 2 else "#56b08f")))
    bx, by = 1780, 470
    for j, c in enumerate(["#ffb347", "#ff7a6b", "#f6d365"]):
        cv.drawCircle(bx - 26 + j * 26, by - 34 - (8 if j == 1 else 0), 22, fill(hexc(c)))
    cv.drawPath(poly([(bx - 70, by - 30), (bx + 70, by - 30), (bx + 46, by), (bx - 46, by)]), fill(hexc("#8b7bff")))
    for lx in (700, 1320):
        cv.drawLine(lx, 0, lx, 40, stroke(hexc("#0b1026"), 3))
        cv.drawPath(poly([(lx - 50, 90), (lx + 50, 90), (lx + 22, 40), (lx - 22, 40)]), fill(hexc("#151b44")))
        cv.drawOval(skia.Rect.MakeXYWH(lx - 50, 82, 100, 16), fill(hexc("#ffe2b0", 0.9)))
        cone = poly([(lx - 50, 90), (lx + 50, 90), (lx + 260, floor_y), (lx - 260, floor_y)])
        cv.drawPath(cone, fill(0, shader=lin((0, 90), (0, floor_y), [hexc("#ffe2b0", 0.14), hexc("#ffe2b0", 0)])))
    # floor
    cv.drawRect(skia.Rect.MakeXYWH(0, floor_y, w, h - floor_y), fill(0, shader=lin(
        (0, floor_y), (0, h), [hexc("#161c3e"), hexc("#0d1230")])))
    for x in range(-400, w + 400, 160):
        cv.drawLine(x, floor_y, x + (x - w / 2) * 0.6, h, stroke(hexc("#ffffff", 0.04), 2))


def draw_dishwasher(cv, x, y, w=440, h=360, door=1.0, plates=(0, 1, 2, 4, 5)):
    """Front view of an opened dishwasher; x,y top-left of the opening (counter line)."""
    # cavity
    cv.drawPath(rrect(x, y, w, h, 10), fill(hexc("#0e1330")))
    cv.drawRect(skia.Rect.MakeXYWH(x + 16, y + 16, w - 32, h - 32),
                fill(0, shader=lin((x, y), (x, y + h), [hexc("#3b4570"), hexc("#1d2348")])))
    # interior glow
    cv.drawCircle(x + w / 2, y + 60, 160, fill(0, shader=rad((x + w / 2, y + 60), 200,
                                                              [hexc("#9fe8ff", 0.25), hexc("#9fe8ff", 0)])))
    # rack
    ry = y + h - 120
    rack = skia.Path()
    for i in range(9):
        xx = x + 40 + i * (w - 80) / 8
        rack.moveTo(xx, ry + 100)
        rack.lineTo(xx, ry)
    cv.drawRect(skia.Rect.MakeXYWH(x + 30, ry + 96, w - 60, 10), fill(hexc("#c9d2e4")))
    # plates in slots (behind front tines)
    slot_w = (w - 80) / 8
    for i in plates:
        cx = x + 40 + slot_w * (i + 0.5)
        cv.save()
        cv.translate(cx, ry + 30)
        cv.scale(0.32, 1.0)
        draw_plate(cv, 70)
        cv.restore()
    cv.drawPath(rack, stroke(hexc("#dfe6f2"), 5))
    # door (opened down, seen as a slab toward us)
    if door > 0:
        dh = 40 * door
        d = poly([(x - 10, y + h), (x + w + 10, y + h), (x + w + 40, y + h + dh), (x - 40, y + h + dh)])
        cv.drawPath(d, fill(0, shader=lin((0, y + h), (0, y + h + dh), [hexc("#d4dbe8"), hexc("#8b97b2")])))
    # control strip
    cv.drawRect(skia.Rect.MakeXYWH(x, y - 18, w, 18), fill(hexc("#c9d2e4")))
    for i in range(4):
        cv.drawCircle(x + w - 40 - i * 26, y - 9, 4, fill(hexc("#38e1ff" if i == 0 else "#7e89a6")))


# ============================================================== CHESS
_PIECE_PROFILES = {
    # half-profiles (x, y) from base (y=0) upward, y negative = up. Mirrored around x=0.
    "pawn": [(40, 0), (40, -10), (30, -16), (30, -22), (20, -26), (14, -52), (24, -58), (24, -64),
             (12, -66), (20, -78), (22, -92), (14, -104), (0, -108)],
    "king": [(46, 0), (46, -12), (36, -18), (36, -26), (24, -30), (18, -88), (32, -96), (32, -104),
             (20, -108), (28, -128), (30, -140), (16, -146), (8, -146), (8, -156), (0, -156)],
    "queen": [(46, 0), (46, -12), (36, -18), (36, -26), (24, -30), (16, -86), (30, -94), (30, -102),
              (18, -106), (32, -136), (22, -132), (16, -142), (8, -136), (0, -146)],
    "rook": [(44, 0), (44, -12), (34, -18), (34, -24), (26, -30), (24, -78), (34, -84), (34, -110),
             (24, -110), (24, -100), (12, -100), (12, -110), (0, -110)],
}


@lru_cache(maxsize=None)
def piece_path(kind: str) -> skia.Path:
    half = _PIECE_PROFILES[kind]
    pts = [(x, y) for x, y in half] + [(-x, y) for x, y in reversed(half)]
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    if kind == "king":
        cr = skia.Path()
        cr.addRect(skia.Rect.MakeXYWH(-4, -184, 8, 32))
        cr.addRect(skia.Rect.MakeXYWH(-14, -174, 28, 8))
        p.addPath(cr)
    if kind == "queen":
        p.addCircle(0, -152, 9)
    if kind == "pawn":
        p.addCircle(0, -110, 0.1)
    return p


def draw_piece(cv, kind, side="human", glow=0.0, scale=1.0):
    """side human = warm ivory; ai = dark glass with cyan edges."""
    p = piece_path(kind)
    cv.save()
    cv.scale(scale, scale)
    cv.drawOval(skia.Rect.MakeXYWH(-52, -10, 104, 20), fill(hexc("#000000", 0.45), blur=8))
    if side == "human":
        cv.drawPath(p, fill(0, shader=lin((-46, 0), (46, 0), [hexc("#fff3dc"), hexc("#efd9b0"),
                                                                hexc("#b48d5c")], [0, 0.45, 1])))
        cv.drawPath(p, stroke(hexc("#6b4a2a", 0.6), 2.5))
    else:
        if glow > 0:
            cv.drawPath(p, stroke(hexc("#38e1ff", 0.7 * glow), 14, blur=16))
        cv.drawPath(p, fill(0, shader=lin((-46, 0), (46, 0), [hexc("#2d376e"), hexc("#141a3a"),
                                                                hexc("#0a0e24")], [0, 0.5, 1])))
        cv.drawPath(p, stroke(hexc("#38e1ff", 0.85), 3))
        # circuit lines
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        for i in range(3):
            yy = -40 - i * 28
            cv.drawLine(-30, yy, -6, yy, stroke(hexc("#38e1ff", 0.5), 2))
            cv.drawLine(-6, yy, 4, yy - 10, stroke(hexc("#38e1ff", 0.5), 2))
            cv.drawCircle(4, yy - 10, 3, fill(hexc("#38e1ff", 0.8)))
        cv.restore()
    cv.restore()


def board_matrix(cx, cy, w_front, w_back, depth):
    """Perspective matrix mapping board units [0,8]x[0,8] (row 0 = far) to screen."""
    m = skia.Matrix()
    src = [skia.Point(0, 0), skia.Point(8, 0), skia.Point(8, 8), skia.Point(0, 8)]
    dst = [skia.Point(cx - w_back / 2, cy - depth / 2), skia.Point(cx + w_back / 2, cy - depth / 2),
           skia.Point(cx + w_front / 2, cy + depth / 2), skia.Point(cx - w_front / 2, cy + depth / 2)]
    m.setPolyToPoly(src, dst)
    return m


def draw_board(cv, m, light="#e9d8b8", dark="#3a2f5c"):
    # board edge (thickness)
    corners = [m.mapXY(0, 0), m.mapXY(8, 0), m.mapXY(8, 8), m.mapXY(0, 8)]
    pts = [(c.x(), c.y()) for c in corners]
    edge = poly([pts[3], pts[2], (pts[2][0], pts[2][1] + 34), (pts[3][0], pts[3][1] + 34)])
    cv.drawPath(edge, fill(hexc("#1a1438")))
    frame = poly(pts)
    cv.drawPath(frame, stroke(hexc("#4b3d78"), 18))
    cv.save()
    cv.concat(m)
    for r in range(8):
        for c in range(8):
            col = light if (r + c) % 2 == 0 else dark
            cv.drawRect(skia.Rect.MakeXYWH(c, r, 1, 1), fill(hexc(col)))
    cv.restore()
    # sheen
    cv.drawPath(frame, fill(0, shader=lin(pts[0], pts[2], [hexc("#ffffff", 0.10), hexc("#ffffff", 0),
                                                            hexc("#000000", 0.25)], [0, 0.5, 1])))


def square_screen(m, col, row):
    p = m.mapXY(col + 0.5, row + 0.62)
    # scale by apparent square width
    a, b = m.mapXY(col, row + 0.5), m.mapXY(col + 1, row + 0.5)
    return p.x(), p.y(), (b.x() - a.x())


# ============================================================== BOOK
def draw_book(cv, t_open=1.0, flip=0.0, cover="#ff7a6b"):
    """Open book seen slightly from above. Origin = spine bottom centre. ~700 wide."""
    W2 = 330
    # cover
    cv.drawPath(rrect(-W2 - 22, -232, 2 * W2 + 44, 252, 14), fill(hexc(cover)))
    cv.drawPath(rrect(-W2 - 22, -232, 2 * W2 + 44, 252, 14), fill(0, shader=lin((0, -232), (0, 20),
                                                                                [hexc("#000000", 0), hexc("#000000", 0.3)])))
    # page stacks
    for s in (-1, 1):
        for k in range(5, 0, -1):
            pg = _page_path(s, W2, -k * 2.5, 1.0)
            cv.drawPath(pg, fill(mix("#e8dcc3", "#c9b896", k / 5)))
        pg = _page_path(s, W2, 0, 1.0)
        cv.drawPath(pg, fill(0, shader=lin((0, 0), (s * W2, 0), [hexc("#d8cbb0"), hexc("#fbf3e1"),
                                                                 hexc("#f3e8cf")], [0, 0.18, 1])))
        # text lines
        cv.save()
        cv.clipPath(pg, doAntiAlias=True)
        rnd = random.Random(3 if s < 0 else 9)
        for i in range(11):
            yy = -190 + i * 16
            x0, x1 = (s * 40, s * (W2 - 40))
            L = rnd.uniform(0.6, 1.0)
            cv.drawLine(min(x0, x1), yy + abs(x0) * 0.0, min(x0, x1) + abs(x1 - x0) * L, yy,
                        stroke(hexc("#6b5a40", 0.35), 4))
        cv.restore()
    # spine shadow
    cv.drawRect(skia.Rect.MakeXYWH(-14, -222, 28, 230), fill(0, shader=lin((-14, 0), (14, 0), [
        hexc("#000000", 0), hexc("#000000", 0.28), hexc("#000000", 0)])))
    # flipping page (right -> left)
    if 0 < flip < 1:
        k = math.cos(flip * math.pi)  # 1..-1
        pg = _page_path(1, W2 * abs(k), -6 - 40 * math.sin(flip * math.pi), 1.0)
        cv.save()
        if k < 0:
            cv.scale(-1, 1)
        cv.drawPath(pg, fill(hexc("#fffaf0" if k > 0 else "#efe4cc")))
        cv.drawPath(pg, stroke(hexc("#b9a77f", 0.5), 1.5))
        cv.restore()


def _page_path(s, w, lift, _):
    p = skia.Path()
    p.moveTo(0, -214)
    p.cubicTo(s * w * 0.3, -232 + lift, s * w * 0.7, -228 + lift, s * w, -222 + lift)
    p.lineTo(s * w, 2 + lift * 0.3)
    p.cubicTo(s * w * 0.7, -4 + lift * 0.3, s * w * 0.3, -8, 0, 4)
    p.close()
    return p


# ============================================================== BRAIN
_BRAIN_OUTLINE = [(-264, 26), (-276, -46), (-256, -122), (-204, -186), (-118, -228), (-10, -240), (100, -226),
                  (192, -186), (256, -122), (288, -44), (284, 24), (262, 70), (214, 92), (150, 100), (96, 122),
                  (30, 150), (-48, 154), (-122, 136), (-172, 102), (-188, 66), (-226, 56)]
_CEREBELLUM = [(140, 102), (214, 92), (262, 82), (288, 118), (262, 166), (196, 184), (140, 164), (118, 132)]
# Hand-authored folds (sulci), facing left.
_FOLDS = [
    [(-182, 64), (-110, 42), (-30, 30), (50, 12), (120, -28), (150, -70)],          # lateral sulcus
    [(22, -238), (2, -176), (26, -112), (2, -50), (18, 12)],                       # central sulcus
    [(-46, -230), (-70, -178), (-48, -132), (-76, -82), (-58, -34)],
    [(-120, -214), (-132, -168), (-110, -124), (-136, -86)],
    [(-196, -170), (-196, -126), (-170, -96), (-200, -56), (-176, -22)],
    [(-252, -96), (-222, -78), (-238, -36), (-214, -2)],
    [(-120, -40), (-90, -10), (-140, 6), (-108, 26)],
    [(-30, -30), (-60, 0), (-24, 4)],
    [(80, -224), (64, -170), (92, -126), (70, -84), (90, -42)],
    [(150, -196), (126, -150), (158, -112), (140, -70)],
    [(214, -150), (196, -108), (226, -72), (204, -30)],
    [(262, -96), (240, -60), (268, -20), (250, 22)],
    [(160, -26), (190, 4), (166, 36), (210, 60)],
    [(100, 30), (70, 56), (110, 80)],
    [(-150, 92), (-110, 82), (-90, 110), (-40, 100)],
    [(-30, 64), (10, 80), (40, 60), (80, 90)],
    [(-90, 60), (-60, 76), (-70, 112)],
    [(-176, -150), (-150, -132), (-164, -110)],
    [(-30, -200), (-12, -162), (-36, -146)],
    [(40, -60), (64, -30), (44, -6)],
    [(200, -120), (176, -134)],
    [(-232, -10), (-250, 14)],
]


@lru_cache(maxsize=None)
def brain_geometry(seed=11):
    outline = smooth_path(_BRAIN_OUTLINE, closed=True, tension=1.0)
    rnd = random.Random(seed)
    gyri = [smooth_path(f, closed=False, tension=1.0) for f in _FOLDS[2:]]
    lateral = smooth_path(_FOLDS[0], closed=False)
    central = smooth_path(_FOLDS[1], closed=False)
    cereb = smooth_path(_CEREBELLUM, closed=True)
    cereb_lines = []
    for k in range(5):
        cereb_lines.append(smooth_path([(130 + k * 6, 130 + k * 9), (200, 112 + k * 13), (282, 104 + k * 13)],
                                       closed=False))
    stem = smooth_path([(96, 132), (132, 128), (140, 210), (126, 290), (100, 290), (104, 210)], closed=True)
    sites = []
    while len(sites) < 60:
        x, y = rnd.uniform(-250, 260), rnd.uniform(-220, 130)
        if outline.contains(x, y):
            sites.append((x, y))
    return outline, gyri, lateral, central, cereb, cereb_lines, stem, sites


def draw_brain(cv, t, draw_on=1.0, fill_a=1.0, fire=0.0, hue="pink", glow=0.6, line_mode=False):
    """Side-view brain (facing left). draw_on 0..1 traces the outline; fill_a fades the illustrated fill.
    fire 0..1 = neuron activity sparks. line_mode draws a luminous line-art version only."""
    outline, gyri, lateral, central, cereb, cereb_lines, stem, sites = brain_geometry()
    base = {"pink": ("#ffb8b0", "#f27f86", "#b84d6a"), "amber": ("#ffd59a", "#ffb347", "#c96a2c"),
            "cyan": ("#bff6ff", "#38e1ff", "#1f6fa8")}[hue]
    line_col = {"pink": "#ffd0c8", "amber": "#ffd59a", "cyan": "#9ff0ff"}[hue]

    if glow > 0:
        cv.drawPath(outline, fill(hexc(base[1], 0.35 * glow * max(fill_a, draw_on)), blur=40))

    if fill_a > 0:
        cv.saveLayerAlpha(None, int(255 * clamp(fill_a)))
        cv.drawPath(stem, fill(0, shader=lin((100, 140), (130, 280), [hexc(base[1]), hexc(base[2])])))
        cv.drawPath(cereb, fill(0, shader=lin((120, 100), (250, 180), [hexc(base[1]), hexc(base[2])])))
        cv.save()
        cv.clipPath(cereb, doAntiAlias=True)
        for cl in cereb_lines:
            cv.drawPath(cl, stroke(hexc(base[2], 0.9), 4))
        cv.restore()
        cv.drawPath(cereb, stroke(hexc(base[2]), 4))
        cv.drawPath(outline, fill(0, shader=rad((-80, -120), 420, [hexc(base[0]), hexc(base[1]),
                                                                    hexc(base[2])], [0, 0.55, 1])))
        cv.save()
        cv.clipPath(outline, doAntiAlias=True)
        for g in gyri + [lateral, central]:
            cv.save()
            cv.translate(-3, -5)
            cv.drawPath(g, stroke(hexc("#ffffff", 0.30), 7))
            cv.restore()
        for g in gyri:
            cv.drawPath(g, stroke(hexc(base[2], 0.95), 7))
        # inner shading toward the bottom edge
        cv.drawPath(outline, fill(0, shader=lin((0, -60), (0, 150), [hexc(base[2], 0), hexc(base[2], 0.45)])))
        cv.drawPath(lateral, stroke(hexc(base[2]), 10))
        cv.drawPath(central, stroke(hexc(base[2]), 9))
        cv.restore()
        cv.drawPath(outline, stroke(hexc(base[2]), 5))
        cv.restore()

    if draw_on > 0 and (line_mode or fill_a < 1):
        a = 1.0 if line_mode else (1 - fill_a)
        po = partial_path(outline, draw_on)
        cv.drawPath(po, stroke(hexc(line_col, 0.6 * a), 12, blur=10))
        cv.drawPath(po, stroke(hexc(line_col, a), 4))
        inner = remap_local(draw_on, 0.35, 1.0)
        if inner > 0:
            for path in (lateral, central, stem, cereb):
                pp = partial_path(path, inner)
                cv.drawPath(pp, stroke(hexc(line_col, 0.5 * a), 8, blur=8))
                cv.drawPath(pp, stroke(hexc(line_col, a), 3))
            for i, g in enumerate(gyri[::2]):
                gk = remap_local(draw_on, 0.45 + (i % 9) * 0.05, 1.0)
                if gk > 0:
                    cv.drawPath(partial_path(g, gk), stroke(hexc(line_col, 0.55 * a), 2.5))

    if fire > 0:
        for i, (x, y) in enumerate(sites):
            ph = (t * 1.7 + i * 0.137) % 1.0
            k = max(0.0, 1 - abs(ph - 0.5) * 4) * fire
            if k > 0.02:
                cv.drawCircle(x, y, 22 * k + 4, fill(hexc("#ffffff", 0.35 * k), blur=12))
                cv.drawCircle(x, y, 4 + 3 * k, fill(hexc("#fff6e0", k)))
                j = sites[(i * 7 + 3) % len(sites)]
                if math.dist((x, y), j) < 160:
                    cv.drawLine(x, y, j[0], j[1], stroke(hexc("#fff1c9", 0.45 * k), 2.2, blur=1.5))


def remap_local(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else 1.0


# ============================================================== FOSSILS & STRATA
@lru_cache(maxsize=None)
def ammonite_path(r=80, turns=3.2, ribs=34):
    spiral = skia.Path()
    ribs_p = skia.Path()
    b = math.log(1 / 0.08) / (turns * math.tau)
    n = 240
    pts = []
    for i in range(n + 1):
        th = i / n * turns * math.tau
        rr = r * math.exp(-b * th)
        pts.append((rr * math.cos(th), rr * math.sin(th)))
    spiral.moveTo(*pts[0])
    for q in pts[1:]:
        spiral.lineTo(*q)
    for j in range(ribs * 3):
        th = j / (ribs * 3) * turns * math.tau
        r_out = r * math.exp(-b * th)
        r_in = r * math.exp(-b * (th + math.tau))
        ribs_p.moveTo(r_out * math.cos(th), r_out * math.sin(th))
        mid = th + 0.18
        ribs_p.quadTo((r_out + r_in) / 2 * math.cos(mid), (r_out + r_in) / 2 * math.sin(mid),
                      r_in * math.cos(th), r_in * math.sin(th))
    return spiral, ribs_p


def draw_ammonite(cv, r=80, glow=0.0, col="#efe2c6"):
    spiral, ribs = ammonite_path(r)
    if glow > 0:
        cv.drawCircle(0, 0, r * 1.2, fill(hexc("#ffb347", 0.4 * glow), blur=30))
    cv.drawCircle(0, 0, r, fill(0, shader=rad((-r * 0.3, -r * 0.3), r * 1.3, [hexc(col), hexc("#b89a6c")])))
    cv.drawPath(ribs, stroke(hexc("#7c6440", 0.75), 2.2))
    cv.drawPath(spiral, stroke(hexc("#5c4628"), 4))
    cv.drawCircle(0, 0, r, stroke(hexc("#5c4628"), 3))


def draw_trilobite(cv, s=1.0, glow=0.0, col="#efe2c6"):
    cv.save()
    cv.scale(s, s)
    body = smooth_path([(0, -70), (40, -60), (52, -30), (44, 20), (30, 60), (0, 76), (-30, 60), (-44, 20),
                        (-52, -30), (-40, -60)])
    if glow > 0:
        cv.drawPath(body, fill(hexc("#ffb347", 0.45 * glow), blur=26))
    cv.drawPath(body, fill(0, shader=rad((-14, -30), 110, [hexc(col), hexc("#a98a5c")])))
    head = skia.Path()
    head.moveTo(-50, -26)
    head.cubicTo(-46, -70, 46, -70, 50, -26)
    cv.drawPath(head, stroke(hexc("#5c4628"), 3))
    for i in range(9):
        yy = -18 + i * 9
        ww = 46 - i * 3.6
        cv.drawLine(-ww, yy, ww, yy, stroke(hexc("#6b5434", 0.85), 2.5))
    cv.drawLine(-14, -26, -12, 70, stroke(hexc("#5c4628", 0.8), 2.5))
    cv.drawLine(14, -26, 12, 70, stroke(hexc("#5c4628", 0.8), 2.5))
    for sx in (-1, 1):
        cv.drawOval(skia.Rect.MakeXYWH(sx * 22 - 6, -50, 12, 9), fill(hexc("#4a3820")))
    cv.drawPath(body, stroke(hexc("#5c4628"), 3))
    cv.restore()


def draw_fish_fossil(cv, s=1.0, glow=0.0, col="#efe2c6"):
    cv.save()
    cv.scale(s, s)
    if glow > 0:
        cv.drawOval(skia.Rect.MakeXYWH(-130, -50, 260, 100), fill(hexc("#ffb347", 0.4 * glow), blur=26))
    sp = smooth_path([(-100, 0), (-40, -6), (20, -2), (80, 4), (110, 2)], closed=False)
    cv.drawPath(sp, stroke(hexc(col), 6))
    for i in range(16):
        x = -60 + i * 10
        h = 34 * math.sin(math.pi * (i + 1) / 18)
        cv.drawLine(x, -3, x + 6, -3 - h, stroke(hexc(col, 0.9), 3))
        cv.drawLine(x, -3, x + 6, -3 + h, stroke(hexc(col, 0.9), 3))
    skull = smooth_path([(-136, 2), (-118, -26), (-88, -32), (-72, -6), (-84, 22), (-116, 22)])
    cv.drawPath(skull, fill(hexc(col, 0.95)))
    cv.drawCircle(-104, -8, 6, fill(hexc("#4a3820")))
    tail = poly([(108, 2), (150, -34), (138, 2), (150, 36)])
    cv.drawPath(tail, stroke(hexc(col), 4))
    cv.restore()


def draw_worm_trace(cv, s=1.0, col="#efe2c6"):
    cv.save()
    cv.scale(s, s)
    p = smooth_path([(-90, 0), (-50, -24), (-10, 10), (30, -18), (70, 8), (100, -6)], closed=False)
    cv.drawPath(p, stroke(hexc(col, 0.85), 16))
    cv.drawPath(p, stroke(hexc("#7c6440", 0.6), 16, ))
    cv.drawPath(p, stroke(hexc(col), 10))
    meas = skia.PathMeasure(p, False)
    L = meas.getLength()
    for i in range(1, 22):
        pos, tan = meas.getPosTan(L * i / 22)
        nx, ny = -tan.y(), tan.x()
        cv.drawLine(pos.x() - nx * 6, pos.y() - ny * 6, pos.x() + nx * 6, pos.y() + ny * 6,
                    stroke(hexc("#7c6440", 0.7), 2))
    cv.restore()


STRATA_COLS = ["#4a3550", "#6a4250", "#8a5446", "#a8693f", "#7d5a3c", "#5f4a3e", "#3f3445", "#2c2640"]


@lru_cache(maxsize=None)
def strata_bands(width=2400, top=0, band_h=260, n=9, seed=5):
    rnd = random.Random(seed)
    edges = []
    for k in range(n + 1):
        y0 = top + k * band_h
        pts = []
        ph = rnd.random() * 6
        for i in range(0, width + 121, 120):
            pts.append((i - 240, y0 + math.sin(i * 0.004 + ph) * 26 + rnd.uniform(-10, 10)))
        edges.append(pts)
    pebbles = [(rnd.uniform(-240, width), rnd.uniform(top, top + n * band_h), rnd.uniform(3, 9))
               for _ in range(420)]
    return edges, pebbles


def draw_strata(cv, width=2400, top=0, band_h=260, n=9):
    edges, pebbles = strata_bands(width, top, band_h, n)
    for k in range(n):
        a, b = edges[k], edges[k + 1]
        pth = skia.Path()
        pth.moveTo(*a[0])
        for q in a[1:]:
            pth.lineTo(*q)
        for q in reversed(b):
            pth.lineTo(*q)
        pth.close()
        col = STRATA_COLS[k % len(STRATA_COLS)]
        y0 = a[0][1]
        cv.drawPath(pth, fill(0, shader=lin((0, y0), (0, y0 + band_h), [hexc(col), mix(col, "#1a1428", 0.35)])))
        # band texture lines
        for j in range(4):
            yy = y0 + band_h * (0.2 + j * 0.2)
            cv.drawLine(-240, yy, width, yy + 8, stroke(hexc("#000000", 0.08), 3))
        top_edge = skia.Path()
        top_edge.moveTo(*a[0])
        for q in a[1:]:
            top_edge.lineTo(*q)
        cv.drawPath(top_edge, stroke(hexc("#ffffff", 0.10), 4))
        cv.drawPath(top_edge, stroke(hexc("#000000", 0.25), 2))
    for (x, y, r) in pebbles:
        cv.drawCircle(x, y, r, fill(hexc("#000000", 0.18)))
        cv.drawCircle(x - r * 0.3, y - r * 0.3, r * 0.5, fill(hexc("#ffffff", 0.06)))
