"""SC01 - Hook + book intro (00:00-23.6). 2D engine scene, word-synced to the narration.

Shots (times = narration word timings, references/voice/words.json):
  SH010 0.00-6.10  title: open book, luminous brain line-art, MAX BENNETT / ZEKANIN KISA TARİHİ / HIZLI ÖZET
  SH020 6.10-9.40  chess: AI queen crushes the champion's king ("ezip" 8.54)
  SH030 9.40-12.45 kitchen: robot fails to load a dishwasher, plate shatters ("dolduramıyor" 11.46), "?"
  SH040 12.45-16.80 "?" dot -> spark -> brain draws on, lock of "the secret" opens ("çözmek" 15.90)
  SH050 16.80-19.80 600 MİLYON YIL counter; amber timeline grows down from the brain stem
  SH060 19.80-23.60 descent through rock strata; dusty fossil record; settle on the worm trace (bridge to SC02)
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "two_d"))

import skia  # noqa: E402

from fm_2d.assets import (PAL, board_matrix, draw_ammonite, draw_board, draw_book, draw_brain,  # noqa: E402
                          draw_dishwasher, draw_fish_fossil, draw_kitchen, draw_piece, draw_plate, draw_robot,
                          draw_strata, draw_trilobite, draw_worm_trace, square_screen)
from fm_2d.core import (FPS, H, W, Cam, Dust, clamp, draw_glow_path, draw_text, draw_text_reveal,  # noqa: E402
                        ease_in, ease_in_out, ease_out, ease_out_back, fill, font, glow_circle, hexc, lerp, lin,
                        pulse, rad, remap, rrect, shake, smooth, smooth_path, stroke)

DURATION = 23.6

T = dict(sh020=6.10, sh030=9.40, sh040=12.70, sh050=16.80, sh060=19.80)
# word cues used for sync
CUE = dict(max=0.76, zekanin=1.56, kisa=2.06, tarihi=2.42, ozet=4.34, yapay=6.22, dunya=7.46, ezip=8.54,
           neden=9.50, bulasik=10.46, doldur=11.46, iste=12.52, zeka2=14.56, buyuk=15.32, coz=15.90,
           beyin=16.86, s600=17.58, milyon=17.92, evrim=18.64, tabiri=19.84, tozlu=21.36, fosil=21.66,
           kayit=21.98, gotur=22.46)

STARS = Dust(150, 1, size=(0.8, 2.2), speed=(2, 8), drift=(0.2, -0.1))
MOTES = Dust(60, 2, size=(1.5, 4), speed=(10, 30), drift=(0, -1))
DUST = Dust(140, 3, size=(1.2, 3.6), speed=(4, 14), drift=(0.3, 0.2))


def background(cv, t, top="#0b1026", bottom="#1b1f4a"):
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=lin((0, 0), (0, H), [hexc(top), hexc(bottom)])))
    STARS.draw(cv, t, "#cfe3ff", 0.55)


# ===================================================================== SH010
def sh010(cv, t):
    background(cv, t)
    fade_in = ease_out(remap(t, 0.0, 0.7))
    cam_z = 1.0 + 0.05 * ease_in_out(remap(t, 0, 5.6)) + 0.6 * ease_in(remap(t, 5.55, 6.1))
    cv.save()
    Cam(W / 2, 520, cam_z).apply(cv)
    # halo behind everything
    glow_circle(cv, W / 2, 360, 520, "#ffb347", 0.18 * fade_in)
    # book
    rise = ease_out(remap(t, 0.0, 1.2))
    cv.save()
    cv.translate(W / 2, 1010 + (1 - rise) * 120)
    cv.scale(0.82, 0.82)
    flip = remap(t, 0.65, 1.45) if t < 1.5 else remap(t, 1.35, 2.15)
    draw_book(cv, flip=ease_in_out(flip))
    cv.restore()
    MOTES.draw(cv, t, "#ffd59a", 0.7 * fade_in)
    # luminous brain line-art rising from the pages
    draw_on = ease_in_out(remap(t, 0.9, 2.6))
    cv.save()
    cv.translate(W / 2 + 10, 300 + (1 - ease_out(remap(t, 0.9, 2.2))) * 60)
    cv.scale(0.62, 0.62)
    draw_brain(cv, t, draw_on=draw_on, fill_a=0, fire=0.6 * remap(t, 2.4, 3.2), hue="amber", glow=0.5,
               line_mode=True)
    cv.restore()
    cv.restore()

    # typography (screen space, gentle zoom)
    cv.save()
    Cam(W / 2, 540, 1 + 0.02 * remap(t, 0, 6) + 0.5 * ease_in(remap(t, 5.55, 6.1))).apply(cv)
    if t > CUE["max"] - 0.05:
        k = t - (CUE["max"] - 0.05)
        draw_text_reveal(cv, "MAX BENNETT", W / 2, 548, font(34, 600), "#9fb4ff", k, tracking=10, stagger=0.03,
                         dur=0.35)
    title_f = font(104, 900)
    words = [("ZEKANIN", CUE["zekanin"]), ("KISA", CUE["kisa"]), ("TARİHİ", CUE["tarihi"])]
    widths = [title_f.measureText(w) for w, _ in words]
    gap = 34
    total = sum(widths) + gap * 2
    x = W / 2 - total / 2
    for (wd, c), ww in zip(words, widths):
        if t > c - 0.08:
            k = ease_out_back(remap(t, c - 0.08, c + 0.32))
            cv.save()
            cv.translate(x + ww / 2, 660)
            cv.scale(lerp(0.6, 1, k), lerp(0.6, 1, k))
            col = "#ffffff" if wd != "KISA" else "#ffb347"
            draw_text(cv, wd, 0, 0, title_f, fill(hexc(col, 0.45 * clamp(k)), blur=18))
            draw_text(cv, wd, 0, 0, title_f, fill(hexc(col, clamp(k))))
            cv.restore()
        x += ww + gap
    # underline sweep
    ul = ease_in_out(remap(t, 2.7, 3.4))
    if ul > 0:
        cv.drawLine(W / 2 - total / 2 * ul, 700, W / 2 + total / 2 * ul, 700, stroke(hexc("#ffb347", 0.9), 4))
    # badge
    if t > CUE["ozet"] - 0.1:
        k = ease_out_back(remap(t, CUE["ozet"] - 0.1, CUE["ozet"] + 0.35))
        cv.save()
        cv.translate(W / 2, 760)
        cv.scale(k, k)
        bf = font(30, 800)
        label = "HIZLI ÖZET"
        bw = bf.measureText(label) + 26 * 9 * 0 + 80 + 9 * 4
        cv.drawPath(rrect(-bw / 2, -30, bw, 56, 28), fill(hexc("#ff7a6b")))
        cv.drawPath(rrect(-bw / 2, -30, bw, 56, 28), fill(hexc("#ff7a6b", 0.6), blur=16))
        draw_text(cv, label, 0, 9, bf, fill(hexc("#0b1026")), tracking=4)
        cv.restore()
    cv.restore()
    # fade from black
    if fade_in < 1:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#000000", 1 - fade_in)))


# ===================================================================== SH020
BOARD_M = board_matrix(W / 2, 700, 1260, 760, 380)


def sh020(cv, t, tl):
    # tl = local time since shot start
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=lin((0, 0), (0, H), [hexc("#120d2e"), hexc("#271c52")])))
    sx, sy = shake(t, 14, CUE["ezip"] + 0.02)
    cam = Cam(W / 2 + sx, 600 + sy, 1.12 - 0.08 * ease_in_out(remap(tl, 0, 3.3)))
    cv.save()
    cam.apply(cv)
    # spotlight
    cone = skia.Path()
    cone.moveTo(W / 2 - 120, -100)
    cone.lineTo(W / 2 + 120, -100)
    cone.lineTo(W / 2 + 820, 980)
    cone.lineTo(W / 2 - 820, 980)
    cone.close()
    cv.drawPath(cone, fill(0, shader=lin((0, -100), (0, 980), [hexc("#ffe7b8", 0.18), hexc("#ffe7b8", 0.02)])))
    draw_board(cv, BOARD_M)

    q_start, q_end = (1, 6), (5, 2)
    mv = remap(t, CUE["ezip"] - 0.55, CUE["ezip"])
    mvk = ease_in(mv) if mv < 1 else 1
    qc = lerp(q_start[0], q_end[0], mvk)
    qr = lerp(q_start[1], q_end[1], mvk)
    lift = math.sin(math.pi * clamp(mv)) * 70 if 0 < mv < 1 else 0

    # topple of the human king
    top = remap(t, CUE["ezip"] + 0.12, CUE["ezip"] + 0.62)
    king_rot = -84 * ease_in(top) if top < 1 else -84 + 6 * math.sin((t - CUE["ezip"] - 0.62) * 18) * math.exp(
        -(t - CUE["ezip"] - 0.62) * 7)
    wob = 6 * math.sin(t * 40) * pulse(t, CUE["ezip"] + 0.08, 0.12)

    pieces = [  # (col,row,kind,side)
        (7, 0, "rook", "human"), (4, 1, "king", "human"), (3, 2, "pawn", "human"), (6, 2, "pawn", "human"),
        (2, 1, "pawn", "human"), (6, 7, "king", "ai"), (7, 5, "rook", "ai"), (2, 6, "pawn", "ai"),
        (5, 5, "pawn", "ai"), ("Q", None, "queen", "ai"),
    ]
    items = []
    for c, r, k, s in pieces:
        if c == "Q":
            c, r = qc, qr
        items.append((r, c, k, s))
    items.sort(key=lambda it: it[0])
    for r, c, k, s in items:
        x, y, sw = square_screen(BOARD_M, c, r)
        sc = sw / 118
        cv.save()
        cv.translate(x, y)
        if k == "queen" and s == "ai":
            # motion trail
            if 0 < mv < 1:
                for j in range(1, 6):
                    cj = lerp(q_start[0], q_end[0], ease_in(max(0, mv - j * 0.05)))
                    rj = lerp(q_start[1], q_end[1], ease_in(max(0, mv - j * 0.05)))
                    xj, yj, _ = square_screen(BOARD_M, cj, rj)
                    cv.save()
                    cv.translate(xj - x, yj - y - lift)
                    cv.saveLayerAlpha(None, int(60 / j))
                    draw_piece(cv, "queen", "ai", glow=1, scale=sc * 1.15)
                    cv.restore()
                    cv.restore()
            cv.translate(0, -lift)
            g = 0.5 + 0.5 * remap(t, CUE["yapay"], CUE["yapay"] + 0.6)
            draw_piece(cv, "queen", "ai", glow=g + 0.8 * pulse(t, CUE["ezip"], 0.3), scale=sc * 1.15)
        elif k == "king" and s == "human":
            cv.rotate(wob)
            if king_rot != 0:
                cv.translate(-40 * sc, 0)
                cv.rotate(king_rot)
                cv.translate(40 * sc, 0)
            draw_piece(cv, "king", "human", scale=sc * 1.2)
        else:
            draw_piece(cv, k, s, glow=0.35, scale=sc)
        cv.restore()

    # impact ring + sparks
    if t > CUE["ezip"]:
        k = remap(t, CUE["ezip"], CUE["ezip"] + 0.7)
        x, y, sw = square_screen(BOARD_M, *q_end)
        cv.save()
        cv.translate(x, y)
        cv.scale(1, 0.35)
        cv.drawCircle(0, 0, 40 + 380 * ease_out(k), stroke(hexc("#38e1ff", 0.9 * (1 - k)), 10 * (1 - k) + 1,
                                                         blur=4))
        cv.drawCircle(0, 0, 20 + 220 * ease_out(k), stroke(hexc("#ffffff", 0.7 * (1 - k)), 4))
        cv.restore()
        rnd = random.Random(4)
        for i in range(26):
            a = rnd.uniform(math.pi * 1.05, math.pi * 1.95)
            v = rnd.uniform(300, 900)
            dt = t - CUE["ezip"]
            px = x + math.cos(a) * v * dt
            py = y - 60 + math.sin(a) * v * dt + 1400 * dt * dt
            al = clamp(1 - dt / 0.8)
            if al > 0:
                cv.drawCircle(px, py, 4, fill(hexc("#9ff0ff", al), blur=2))
    cv.restore()

    # labels (screen space)
    def chip(text, x, y, col, k, txt="#0b1026"):
        if k <= 0:
            return
        f = font(26, 800)
        w = f.measureText(text) + 44 + 3 * len(text)
        cv.save()
        cv.translate(x, y)
        cv.scale(ease_out_back(k), ease_out_back(k))
        cv.drawPath(rrect(-w / 2, -24, w, 46, 23), fill(hexc(col, 0.5), blur=14))
        cv.drawPath(rrect(-w / 2, -24, w, 46, 23), fill(hexc(col)))
        draw_text(cv, text, 0, 9, f, fill(hexc(txt)), tracking=3)
        cv.restore()

    out = 1 - remap(t, CUE["ezip"] + 0.2, CUE["ezip"] + 0.5)
    chip("YAPAY ZEKA", 470, 860, "#38e1ff", remap(t, CUE["yapay"], CUE["yapay"] + 0.35) * out)
    chip("DÜNYA ŞAMPİYONU", 1080, 300, "#efd9b0", remap(t, CUE["dunya"], CUE["dunya"] + 0.35) * out)
    # checkmate flash text
    if t > CUE["ezip"] + 0.25:
        k = remap(t, CUE["ezip"] + 0.25, CUE["ezip"] + 0.6)
        f = font(92, 900)
        cv.save()
        cv.translate(W / 2, 210)
        cv.scale(lerp(1.3, 1, ease_out(k)), lerp(1.3, 1, ease_out(k)))
        draw_text(cv, "ŞAH MAT", 0, 0, f, fill(hexc("#38e1ff", 0.6 * k), blur=22), tracking=12)
        draw_text(cv, "ŞAH MAT", 0, 0, f, fill(hexc("#e9fbff", k)), tracking=12)
        cv.restore()
    # flash on impact
    fl = pulse(t, CUE["ezip"] + 0.02, 0.12)
    if fl > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#bff6ff", 0.35 * fl)))


# ===================================================================== SH030
_KITCHEN = None


def kitchen_image():
    global _KITCHEN
    if _KITCHEN is None:
        s = skia.Surface(W, H)
        c = s.getCanvas()
        draw_kitchen(c, floor_y=870)
        _KITCHEN = s.makeImageSnapshot()
    return _KITCHEN


DW = dict(x=560, y=500, w=460, h=330)
SLOT_W = (DW["w"] - 80) / 8
SLOT6 = (DW["x"] + 40 + SLOT_W * 6.5, DW["y"] + DW["h"] - 120 + 30)
ROBOT_S = 1.25
FLOOR = 905


def ik(shoulder, target, l1, l2):
    dx, dy = target[0] - shoulder[0], target[1] - shoulder[1]
    d = clamp(math.hypot(dx, dy), 1, l1 + l2 - 0.5)
    base = math.atan2(dy, dx)
    a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    b = math.acos(clamp((l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2), -1, 1))
    sh = base - a  # elbow up (negative = up in y-down)
    el = math.pi - b
    return math.degrees(sh), math.degrees(el)


def robot_state(t):
    """World position of the robot + plate target path (plate centre in world)."""
    rx = lerp(1420, 1205, ease_out(remap(t, T["sh030"] - 0.1, T["sh030"] + 0.8)))
    ry = 870
    # plate centre path (world)
    rest = (rx - 250, 560)
    over = (SLOT6[0] + 6, SLOT6[1] - 120)
    into = (SLOT6[0] + 14, SLOT6[1] - 34)
    a = ease_in_out(remap(t, 10.0, 10.75))
    b = ease_in_out(remap(t, 10.75, 11.28))
    p = (lerp(rest[0], over[0], a), lerp(rest[1], over[1], a))
    p = (lerp(p[0], into[0], b), lerp(p[1], into[1], b))
    # tremble while aligning
    tr = remap(t, 10.4, 11.3) * (1 - remap(t, 11.36, 11.45))
    p = (p[0] + math.sin(t * 47) * 5 * tr, p[1] + math.cos(t * 39) * 4 * tr)
    # bump on tine
    bump = pulse(t, 11.33, 0.08)
    p = (p[0] + 10 * bump, p[1] - 14 * bump)
    return rx, ry, p


def plate_squash(t):
    return lerp(1.0, 0.32, ease_in_out(remap(t, 10.4, 11.0)))


RELEASE = 11.40


def _plate_hit():
    _, _, pc = robot_state(RELEASE)
    g, vy = 2600, -160.0
    return RELEASE + (-vy + math.sqrt(vy * vy + 2 * g * (FLOOR - pc[1]))) / g


PLATE_HIT = None


def sh030(cv, t, tl):
    global PLATE_HIT
    if PLATE_HIT is None:
        PLATE_HIT = _plate_hit()
    cv.drawImage(kitchen_image(), 0, 0)
    sx, sy = shake(t, 9, PLATE_HIT)
    cv.save()
    Cam(W / 2 + sx, H / 2 + sy, 1.0 + 0.04 * ease_in_out(remap(tl, 0, 3))).apply(cv)
    plates_in = (0, 1, 2, 3, 4, 5)
    draw_dishwasher(cv, **DW, plates=plates_in)
    rx, ry, pc = robot_state(t)
    held = t < RELEASE
    # arm IK in robot local frame (robot mirrored to face left)
    bob = -10 + math.sin(t * 2.4) * 6
    lx = (rx - pc[0]) / ROBOT_S
    ly = (pc[1] - ry) / ROBOT_S - bob
    if held:
        shd, eld = ik((70, -200), (lx, ly), 92, 84 + 34)
    else:
        k = ease_out(remap(t, RELEASE, RELEASE + 0.6))
        shd, eld = ik((70, -200), (lx, ly), 92, 118)
        shd, eld = lerp(shd, 40, k), lerp(eld, -60, k)
    sq = plate_squash(t)

    def hold(c):
        if held:
            c.save()
            c.rotate(-(shd + eld))
            c.scale(sq, 1)
            draw_plate(c, 64)
            c.restore()

    surprised = remap(t, 11.35, 11.45)
    confused = t > 11.95
    look = (-1.0, 0.7) if t < 11.45 else (-0.8 + 0.8 * remap(t, 11.45, 11.85), lerp(1.0, -0.2, remap(t, 11.8, 12.2)))
    blink = pulse(t, 9.9, 0.08) + pulse(t, 12.15, 0.07)
    cv.save()
    cv.translate(rx, ry)
    cv.scale(-1, 1)
    draw_robot(cv, t, eye_dx=-look[0], eye_dy=look[1], blink=blink,
               head_tilt=-12 * smooth(remap(t, 11.9, 12.2)) + 4 * surprised * (1 - remap(t, 11.55, 11.75)),
               shoulder=shd, elbow=eld, mood="confused" if confused else "neutral", hold=hold, scale=ROBOT_S,
               arm_shake=0)
    cv.restore()

    # falling plate + shatter
    if not held:
        dt = t - RELEASE
        x0, y0 = pc
        vx, vy = 120.0, -160.0
        hit_t = 0.0
        # solve hit time with floor
        g = 2600
        disc = vy * vy + 2 * g * (FLOOR - y0)
        hit_t = (-vy + math.sqrt(disc)) / g
        if dt < hit_t:
            px = x0 + vx * dt
            py = y0 + vy * dt + 0.5 * g * dt * dt
            cv.save()
            cv.translate(px, py)
            cv.rotate(dt * 380)
            cv.scale(0.32 + 0.68 * abs(math.sin(dt * 7 + 0.3)), 1)
            draw_plate(cv, 64)
            cv.restore()
        else:
            st = dt - hit_t
            hx = x0 + vx * hit_t
            rnd = random.Random(12)
            for i in range(18):
                a = rnd.uniform(math.pi * 1.02, math.pi * 1.98)
                v = rnd.uniform(160, 640)
                tt = min(st, 0.7)
                sxp = hx + math.cos(a) * v * tt * (1 - tt * 0.7)
                syp = FLOOR + min(0, math.sin(a) * v * tt + 1500 * tt * tt) + rnd.uniform(-6, 10)
                cv.save()
                cv.translate(sxp, syp)
                cv.rotate(rnd.uniform(0, 360) + st * 500 * (1 - min(st, 0.7) / 0.7))
                sz = rnd.uniform(10, 26)
                shard = skia.Path()
                shard.moveTo(-sz, 0)
                shard.lineTo(sz * 0.4, -sz * 0.6)
                shard.lineTo(sz * 0.7, sz * 0.4)
                shard.close()
                cv.drawPath(shard, fill(hexc("#eef2f8")))
                cv.drawPath(shard, stroke(hexc("#ff7a6b", 0.8), 2))
                cv.restore()
            k = remap(st, 0, 0.5)
            cv.save()
            cv.translate(hx, FLOOR)
            cv.scale(1, 0.25)
            cv.drawCircle(0, 0, 30 + 260 * ease_out(k), stroke(hexc("#ffffff", 0.6 * (1 - k)), 6))
            cv.restore()
    cv.restore()
    # big question mark
    if t > 11.95:
        draw_qmark(cv, t, (rx - 20, 220), ease_out_back(remap(t, 11.95, 12.3)))


def qmark_path():
    p = skia.Path()
    p.moveTo(-46, -70)
    p.cubicTo(-46, -122, 46, -126, 48, -74)
    p.cubicTo(50, -36, 4, -30, 2, 6)
    p.lineTo(2, 22)
    return p


QDOT = (2, 68)


def draw_qmark(cv, t, pos, k, a=1.0, dot_only=False):
    cv.save()
    cv.translate(*pos)
    cv.scale(1.25 * k, 1.25 * k)
    cv.rotate(6 * math.sin(t * 3))
    if not dot_only:
        draw_glow_path(cv, qmark_path(), "#ffb347", 22, a=a, glow=16)
    cv.drawCircle(*QDOT, 22, fill(hexc("#ffb347", 0.6 * a), blur=16))
    cv.drawCircle(*QDOT, 15, fill(hexc("#ffe2b0", a)))
    cv.restore()


# ===================================================================== WORLD (SH040-SH060)
BRAIN_POS = (960, 470)
BRAIN_S = 0.9
GROUND = 1260
STRATA_TOP = GROUND + 30
TIMELINE_X = BRAIN_POS[0] + 116 * BRAIN_S
TL_TOP = BRAIN_POS[1] + 290 * BRAIN_S
TL_BOTTOM = 3560
TICK_SPACING = (TL_BOTTOM - GROUND) / 6
FOSSILS = [  # (kind, world x, world y) - between the age ticks, alternating sides
    ("ammonite", TIMELINE_X + 460, GROUND + TICK_SPACING * 1.5),
    ("fish", TIMELINE_X - 500, GROUND + TICK_SPACING * 2.6),
    ("trilobite", TIMELINE_X + 450, GROUND + TICK_SPACING * 4.5),
    ("worm", TIMELINE_X + 380, GROUND + TICK_SPACING * 5.55),
]
_STRATA = None
HIDE_BRAIN = False  # set by later scenes that take over the brain


def strata_image():
    global _STRATA
    if _STRATA is None:
        s = skia.Surface(4000, TL_BOTTOM - STRATA_TOP + 600)
        c = s.getCanvas()
        c.translate(240, 0)
        draw_strata(c, width=3760, top=0, band_h=330, n=8)
        _STRATA = s.makeImageSnapshot()
    return _STRATA


def world_cam(t):
    """Camera path for SH040-SH060 (one continuous world)."""
    # SH040: close on the brain
    c0 = (BRAIN_POS[0], BRAIN_POS[1] - 20, 1.25)
    c1 = (BRAIN_POS[0] + 270, BRAIN_POS[1] + 40, 0.92)  # SH050 brain left, counter right
    c2 = (TIMELINE_X + 40, 2000, 1.0)
    c3 = (TIMELINE_X + 200, FOSSILS[3][2] - 70, 1.12)
    a = ease_in_out(remap(t, 16.3, 17.4))
    b = ease_in_out(remap(t, 18.7, 21.2))
    c = ease_in_out(remap(t, 21.0, 23.4))
    x = lerp(lerp(lerp(c0[0], c1[0], a), c2[0], b), c3[0], c)
    y = lerp(lerp(lerp(c0[1], c1[1], a), c2[1], b), c3[1], c)
    z = lerp(lerp(lerp(c0[2], c1[2], a), c2[2], b), c3[2], c)
    z *= 1 + 0.015 * math.sin(t * 0.8)
    return Cam(x, y, z)


def lock(cv, t, k_in, open_k):
    cv.save()
    s = ease_out_back(k_in)
    cv.scale(s, s)
    cv.drawCircle(0, 0, 130, fill(hexc("#ffb347", 0.35 + 0.4 * open_k), blur=40))
    # shackle
    cv.save()
    cv.translate(34, -40 - 34 * ease_out_back(open_k))
    cv.rotate(-28 * ease_out(open_k))
    cv.translate(-34, 0)
    sh = skia.Path()
    sh.moveTo(-34, 0)
    sh.lineTo(-34, -30)
    sh.arcTo(skia.Rect.MakeXYWH(-34, -64, 68, 68), 180, 180, False)
    sh.lineTo(34, 0)
    cv.drawPath(sh, stroke(hexc("#c9d2e4"), 16))
    cv.drawPath(sh, stroke(hexc("#ffffff", 0.6), 5))
    cv.restore()
    body = rrect(-58, -44, 116, 96, 20)
    cv.drawPath(body, fill(0, shader=lin((0, -44), (0, 52), [hexc("#ffd27a"), hexc("#e08a2c")])))
    cv.drawPath(body, stroke(hexc("#8a4a14"), 3))
    cv.drawCircle(0, -4, 12, fill(hexc("#5a2e0c")))
    kh = skia.Path()
    kh.moveTo(-6, 0)
    kh.lineTo(6, 0)
    kh.lineTo(9, 26)
    kh.lineTo(-9, 26)
    kh.close()
    cv.drawPath(kh, fill(hexc("#5a2e0c")))
    cv.restore()


def world(cv, t):
    cam = world_cam(t)
    # sky
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=lin((0, 0), (0, H), [hexc("#0b1026"), hexc("#171c45")])))
    STARS.draw(cv, t, "#cfe3ff", 0.5)
    cv.save()
    cam.apply(cv)

    # ground & strata (only when visible)
    view_bottom = cam.y + H / 2 / cam.zoom
    if view_bottom > GROUND - 200:
        # horizon glow
        glow_circle(cv, TIMELINE_X, GROUND, 900, "#ff7a6b", 0.20)
        cv.drawImage(strata_image(), -1000, STRATA_TOP)
        top = skia.Path()
        top.moveTo(-1000, GROUND)
        rnd = random.Random(9)
        for x in range(-1000, 3000, 60):
            top.lineTo(x, GROUND + rnd.uniform(-6, 6))
        top.lineTo(3000, STRATA_TOP + 20)
        top.lineTo(-1000, STRATA_TOP + 20)
        top.close()
        cv.drawPath(top, fill(hexc("#2b2147")))
        # grass tufts (biology above, history below)
        rnd = random.Random(21)
        for i in range(90):
            gx = rnd.uniform(-600, 2700)
            hh = rnd.uniform(14, 40)
            sw = math.sin(t * 2 + gx * 0.01) * 6
            g = skia.Path()
            g.moveTo(gx - 6, GROUND + 2)
            g.quadTo(gx + sw * 0.5, GROUND - hh * 0.6, gx + sw, GROUND - hh)
            g.quadTo(gx + 2, GROUND - hh * 0.5, gx + 6, GROUND + 2)
            cv.drawPath(g, fill(hexc("#3f8f7a" if i % 3 else "#56b08f")))
        # fossils
        for i, (kind, fx, fy) in enumerate(FOSSILS):
            reach = remap(timeline_tip(t), fy - 80, fy + 40)
            gl = reach * (0.6 + 0.4 * math.sin(t * 3 + i)) * (0.5 + 0.5 * remap(t, CUE["fosil"] - 0.2,
                                                                                CUE["fosil"] + 0.4))
            cv.save()
            cv.translate(fx, fy)
            cv.rotate([-12, 8, -6, 4][i])
            if kind == "ammonite":
                draw_ammonite(cv, 92, glow=gl)
            elif kind == "fish":
                draw_fish_fossil(cv, 1.25, glow=gl)
            elif kind == "trilobite":
                draw_trilobite(cv, 1.35, glow=gl)
            else:
                draw_worm_trace(cv, 1.4)
                if gl > 0:
                    cv.drawOval(skia.Rect.MakeXYWH(-160, -60, 320, 120), fill(hexc("#ffb347", 0.25 * gl), blur=30))
            cv.restore()
            # connector from timeline
            if reach > 0:
                lk = ease_out(reach)
                cv.drawLine(TIMELINE_X, fy, lerp(TIMELINE_X, fx, lk) + (110 if fx < TIMELINE_X else -110) * lk,
                            fy, stroke(hexc("#ffb347", 0.5 * lk), 3))

    # timeline
    tip = timeline_tip(t)
    if tip > TL_TOP:
        p = skia.Path()
        p.moveTo(TIMELINE_X, TL_TOP)
        p.lineTo(TIMELINE_X, tip)
        draw_glow_path(cv, p, "#ffb347", 6, glow=12)
        cv.drawCircle(TIMELINE_X, tip, 14, fill(hexc("#ffe2b0"), blur=4))
        glow_circle(cv, TIMELINE_X, tip, 90, "#ffb347", 0.5)
        tf = font(30, 700)
        for k in range(1, 7):
            yy = GROUND + TICK_SPACING * k
            if tip > yy:
                a = remap(tip, yy, yy + 120)
                cv.drawLine(TIMELINE_X - 22, yy, TIMELINE_X + 22, yy, stroke(hexc("#ffb347", a), 5))
                draw_text(cv, f"{k * 100} milyon yıl önce", TIMELINE_X - 40, yy + 10, tf,
                          fill(hexc("#ffe2b0", a * 0.9)), align="right")

    # brain
    if not HIDE_BRAIN:
        world_brain(cv, t)

    # dust in the strata
    if view_bottom > GROUND:
        cv.save()
        cv.translate(0, cam.y - H / 2)
        DUST.area = (TIMELINE_X - 1200, 0, TIMELINE_X + 1200, H)
        DUST.draw(cv, t, "#ffe2b0", 0.55 * remap(t, CUE["tabiri"], CUE["tozlu"] + 0.3), blur=1.5)
        cv.restore()
    cv.restore()

    # god rays from above while descending
    gr = remap(t, 19.6, 20.6)
    if gr > 0:
        for i in range(5):
            x = 300 + i * 360 + math.sin(t * 0.6 + i) * 40
            ray = skia.Path()
            ray.moveTo(x - 40, -50)
            ray.lineTo(x + 40, -50)
            ray.lineTo(x + 260, H + 50)
            ray.lineTo(x + 60, H + 50)
            ray.close()
            cv.drawPath(ray, fill(0, shader=lin((0, 0), (0, H), [hexc("#ffe2b0", 0.10 * gr), hexc("#ffe2b0", 0)]),
                                  blur=20))
    # counter (screen space)
    counter(cv, t)


def world_brain(cv, t):
    cv.save()
    cv.translate(*BRAIN_POS)
    bob = math.sin(t * 1.3) * 6
    cv.translate(0, bob)
    cv.scale(BRAIN_S, BRAIN_S)
    draw_on = ease_in_out(remap(t, 13.1, 14.4))
    fill_a = ease_in_out(remap(t, 14.2, 14.95))
    fire = 0.35 * remap(t, CUE["zeka2"], CUE["zeka2"] + 0.5) + 0.65 * remap(t, CUE["coz"], CUE["coz"] + 0.4)
    hue = "pink"
    draw_brain(cv, t, draw_on=draw_on, fill_a=fill_a, fire=fire, hue=hue, glow=0.7)
    # amber wash as it becomes history
    wash = remap(t, CUE["evrim"], CUE["evrim"] + 0.8)
    if wash > 0:
        cv.saveLayerAlpha(None, int(140 * wash))
        draw_brain(cv, t, draw_on=1, fill_a=1, fire=0, hue="amber", glow=0)
        cv.restore()
    # the lock of "the great secret"
    lk_in = remap(t, CUE["buyuk"] - 0.15, CUE["buyuk"] + 0.25)
    lk_open = remap(t, CUE["coz"], CUE["coz"] + 0.35)
    lk_out = remap(t, CUE["coz"] + 0.45, CUE["coz"] + 0.85)
    if lk_in > 0 and lk_out < 1:
        cv.save()
        cv.translate(-10, -70)
        cv.saveLayerAlpha(None, int(255 * (1 - lk_out)))
        cv.scale(1 + 0.4 * lk_out, 1 + 0.4 * lk_out)
        lock(cv, t, lk_in, lk_open)
        cv.restore()
        cv.restore()
    burst = remap(t, CUE["coz"] + 0.05, CUE["coz"] + 0.8)
    if 0 < burst < 1:
        cv.drawCircle(-10, -70, 60 + 520 * ease_out(burst), stroke(hexc("#ffe2b0", 0.8 * (1 - burst)), 8 * (1 - burst) + 1))
        rnd = random.Random(31)
        for i in range(30):
            a = rnd.uniform(0, math.tau)
            d = (80 + rnd.uniform(200, 460) * ease_out(burst))
            cv.drawCircle(-10 + math.cos(a) * d, -70 + math.sin(a) * d, 5 * (1 - burst) + 1,
                          fill(hexc("#fff1c9", 1 - burst), blur=2))
    cv.restore()



def timeline_tip(t):
    return lerp(TL_TOP, TL_BOTTOM - 120, ease_in_out(remap(t, CUE["evrim"] - 0.1, 22.9)))


def counter(cv, t):
    k_in = remap(t, CUE["s600"] - 0.25, CUE["s600"] + 0.1)
    k_out = remap(t, 19.4, 19.95)
    if k_in <= 0 or k_out >= 1:
        return
    a = (1 - k_out)
    cx, cy = 1340, 470 - 160 * ease_in(k_out)
    n = int(round(600 * ease_out(remap(t, CUE["s600"] - 0.25, CUE["s600"] + 0.5))))
    f = font(230, 900)
    cv.save()
    cv.translate(cx, cy)
    s = ease_out_back(k_in)
    cv.scale(s, s)
    draw_text(cv, str(n), 0, 0, f, fill(hexc("#ffb347", 0.5 * a), blur=26))
    draw_text(cv, str(n), 0, 0, f, fill(hexc("#fff4e0", a)))
    cv.restore()
    if t > CUE["milyon"] - 0.1:
        draw_text_reveal(cv, "MİLYON YIL", cx, cy + 90, font(64, 800), "#ffb347", t - (CUE["milyon"] - 0.1),
                         tracking=14, stagger=0.035, dur=0.3, a=a)
    if t > CUE["evrim"] - 0.1:
        draw_text_reveal(cv, "evrimsel geçmiş", cx, cy + 156, font(40, 500), "#cfd8ff", t - (CUE["evrim"] - 0.1),
                         tracking=2, stagger=0.025, dur=0.3, a=a * 0.9)


# ===================================================================== DISPATCH
def layer(cv, alpha, fn, *args):
    if alpha <= 0:
        return
    if alpha >= 1:
        fn(*args)
        return
    cv.saveLayerAlpha(None, int(255 * alpha))
    fn(*args)
    cv.restore()


def render(cv, t):
    if t < T["sh020"]:
        sh010(cv, t)
        # flash into chess
        fl = remap(t, 5.85, 6.1)
        if fl > 0:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#e9fbff", fl * 0.9)))
    elif t < T["sh030"]:
        sh020(cv, t, t - T["sh020"])
        fl = 1 - remap(t, T["sh020"], T["sh020"] + 0.25)
        if fl > 0:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#e9fbff", fl * 0.9)))
        # slide transition to kitchen
        s = remap(t, T["sh030"] - 0.22, T["sh030"])
        if s > 0:
            cv.save()
            cv.translate(W * (1 - ease_in_out(s)), 0)
            sh030(cv, T["sh030"], 0)
            cv.restore()
    elif t < T["sh040"] - 0.5:
        sh030(cv, t, t - T["sh030"])
    elif t < T["sh040"] + 0.35:
        # zoom into the question-mark dot, which becomes the spark of SH040
        k = remap(t, T["sh040"] - 0.5, T["sh040"] + 0.35)
        rx, _, _ = robot_state(t)
        qpos = (rx - 20, 220)
        dot = (qpos[0] + QDOT[0] * 1.25, qpos[1] + QDOT[1] * 1.25)
        z = math.exp(ease_in(k) * math.log(9))
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#0b1026")))
        cv.save()
        cv.translate(*dot)
        cv.scale(z, z)
        cv.translate(-dot[0], -dot[1])
        layer(cv, 1 - remap(k, 0.35, 0.8), sh030, cv, t, t - T["sh030"])
        cv.restore()
        # navy takes over, spark stays at centre-ish
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#0b1026", remap(k, 0.5, 0.95))))
        cx = lerp(dot[0], W / 2, ease_in_out(remap(k, 0.45, 1.0)))
        cy = lerp(dot[1], H / 2, ease_in_out(remap(k, 0.45, 1.0)))
        r = 15 * 1.25 * lerp(1, 2.2, k)
        glow_circle(cv, cx, cy, r * 6, "#ffb347", 0.7)
        cv.drawCircle(cx, cy, r, fill(hexc("#ffe2b0")))
        if k > 0.8:
            layer(cv, remap(k, 0.8, 1.0), world, cv, t)
            glow_circle(cv, W / 2, H / 2, r * 6, "#ffb347", 0.7 * (1 - remap(k, 0.8, 1)))
    else:
        world(cv, t)
        # spark travels from screen centre into the brain outline start, fading as the line draws on
        # spark travels from screen centre to where the brain outline starts drawing
        sp = remap(t, T["sh040"] + 0.35, 13.35)
        if sp < 1:
            cam = world_cam(t)
            ox = BRAIN_POS[0] - 264 * BRAIN_S
            oy = BRAIN_POS[1] + 26 * BRAIN_S
            tx, ty = W / 2 + (ox - cam.x) * cam.zoom, H / 2 + (oy - cam.y) * cam.zoom
            m = ease_in_out(remap(sp, 0, 0.75))
            x, y = lerp(W / 2, tx, m), lerp(H / 2, ty, m)
            r = 30 * (1 - remap(sp, 0.7, 1))
            glow_circle(cv, x, y, r * 3.5, "#ffb347", 0.8)
            cv.drawCircle(x, y, r * 0.6, fill(hexc("#ffe2b0")))
    # final fade-out hint at the very end of the scene is left to the edit


if __name__ == "__main__":
    import argparse

    import numpy as np
    from PIL import Image

    from fm_2d.core import Finisher, new_surface, snapshot

    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*", help="render stills at these times")
    ap.add_argument("--out", default=str(ROOT / "projects/zeka_tarihi/11_render/SC01"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fin = Finisher()
    surf = new_surface()
    for ts in args.still or []:
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        render(cv, ts)
        img = fin(snapshot(surf), int(ts * FPS))
        Image.fromarray(img).save(out / f"still_{ts:05.2f}.png")
        print("wrote", out / f"still_{ts:05.2f}.png")
