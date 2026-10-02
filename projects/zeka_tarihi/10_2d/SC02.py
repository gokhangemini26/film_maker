"""SC02 - The five breakthroughs (23.43-51.40). Continues SC01's last frame (worm trace in the strata).

Shots (word cues from references/voice/words.json):
  SH070 23.43-30.20 camera rises from the worm fossil to the brain; brain splits into 5 evolutionary layers
                    ("sıfırdan var olmadığını"), numbers 1-5 ("beş aşamada"), rebuilt bottom-up ("inşa"),
                    layers fly out and become the steps of SH080
  SH080 30.20-42.60 staircase of 5 breakthroughs: worm steering, fish trial-and-error, mammal imagining,
                    primate understanding others, human speech; "uzanan harika bir süreç" sweep up the stairs
  SH090 42.60-51.40 zoom into the human's head -> glass head with the layered brain ("kafatasımızın içindeki"),
                    layers light up with their creatures ("600 milyon yıllık katmanlarından"), pull back into a
                    museum ("canlı bir fosil müzesi"); the robot from SC01 visits, "?" -> "Kesinlikle evet."
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "two_d"))

import skia  # noqa: E402

from fm_2d.assets import (STAGE_COLS, bubble, draw_ammonite, draw_brain, draw_fish, draw_human, draw_monkey,  # noqa: E402
                          draw_mouse, draw_robot, draw_trilobite, draw_worm)
from fm_2d.core import (FPS, H, W, Cam, clamp, draw_glow_path, draw_text, draw_text_reveal, ease_in,  # noqa: E402
                        ease_in_out, ease_out, ease_out_back, fill, font, glow_circle, hexc, lerp, lin, mix,
                        partial_path, pulse, rad, remap, rrect, smooth, stroke)

_spec = importlib.util.spec_from_file_location("SC01", HERE / "SC01.py")
S1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S1)
S1.HIDE_BRAIN = True  # this scene draws the brain itself (layered)

START = 703 / FPS  # SC01 is cut after frame 702 (voice of SC02 starts at 23.48)
DURATION = 51.80  # "İkinci olarak" (SC03) starts at ~51.85

CUE = dict(ilk=23.48, beyin=24.28, karmasik=25.02, sifir=26.04, tam=27.42, bes=27.84, insa=28.52,
           gor=29.28, solucan=30.14, yon=31.20, balik=32.78, deneme=33.40, yanilma=33.80, memeli=34.74,
           hayal=35.82, primat=37.32, baskasi=37.90, bizler=39.98, konus=40.50, uzanan=40.96, harika=41.38,
           surec=42.08, kafa=42.88, yapi=43.92, zeka=44.76, s600=45.34, katman=46.52, canli=47.90,
           fosil=48.48, muze=48.72, dusun=49.34, miyiz=49.88, kesin=50.58, evet=51.14)
T = dict(sh080=30.20, sh090=42.60)
EVET_ALPHA = lambda t: 1.0  # noqa: E731  (SC03 fades the stamp out)

NAMES = ["SOLUCAN", "BALIK", "MEMELİ", "PRİMAT", "İNSAN"]
ABILITY = ["Yönlendirme", "Deneme-Yanılma", "Geleceği Hayal Etme", "Başkalarını Anlama", "Konuşma"]
STAGE_CUE = ["solucan", "balik", "memeli", "primat", "bizler"]
ABIL_CUE = ["yon", "deneme", "hayal", "baskasi", "konus"]

# brain layers (local brain coords, bottom = oldest). edges from bottom to top.
EDGES = [300, 150, 62, -40, -138, -250]
BAND_YC = [(EDGES[i] + EDGES[i + 1]) / 2 for i in range(5)]


# ===================================================================== brain layers
def brain_comp(cv, t, fire, glow=0.0):
    draw_brain(cv, t, draw_on=1, fill_a=1, fire=fire, hue="pink", glow=glow)
    cv.saveLayerAlpha(None, 140)
    draw_brain(cv, t, draw_on=1, fill_a=1, fire=0, hue="amber", glow=0)
    cv.restore()


def band_clip(i):
    return skia.Rect.MakeLTRB(-340, EDGES[i + 1], 340, EDGES[i])


def draw_layered_brain(cv, t, offs, tints, fire, glow=0.7, edge_a=0.0):
    """offs[i] = vertical offset (local units, up = negative) per band; tints[i] = 0..1 stage colour."""
    if glow > 0 and max(abs(o) for o in offs) < 1:
        draw_brain(cv, t, draw_on=0, fill_a=0, fire=0, glow=glow)
    for i in range(5):
        cv.save()
        cv.translate(0, offs[i])
        cv.clipRect(band_clip(i), doAntiAlias=True)
        cv.saveLayer(None, None)
        brain_comp(cv, t, fire)
        if tints[i] > 0:
            p = fill(hexc(STAGE_COLS[i], 0.72 * tints[i]))
            p.setBlendMode(skia.BlendMode.kSrcATop)
            cv.drawRect(band_clip(i), p)
        cv.restore()
        cv.restore()
        if edge_a > 0:
            cv.save()
            cv.translate(0, offs[i])
            for y in (EDGES[i], EDGES[i + 1]):
                cv.drawLine(-300, y, 300, y, stroke(hexc(STAGE_COLS[i], 0.0), 1))
            cv.restore()


# ===================================================================== SH070 (world of SC01)
_orig_cam = S1.world_cam
BRAIN_FRAME = (S1.BRAIN_POS[0], S1.BRAIN_POS[1] + 10, 1.05)


def cam_a(t):
    c = _orig_cam(min(t, 23.4))
    a = ease_in_out(remap(t, 23.75, 25.7))
    x, y, z = lerp(c.x, BRAIN_FRAME[0], a), lerp(c.y, BRAIN_FRAME[1], a), lerp(c.zoom, BRAIN_FRAME[2], a)
    e = ease_in_out(remap(t, 26.0, 26.8))  # make room for the exploded layers
    z = lerp(z, 0.82, e)
    return Cam(x, y, z)


S1.world_cam = cam_a


def band_offsets(t):
    k = ease_out_back(remap(t, CUE["sifir"] + 0.05, CUE["sifir"] + 0.75))
    offs = []
    for i in range(5):
        o = -(i - 2) * 92 * k
        # rebuild bottom-up
        r = remap(t, CUE["insa"] + i * 0.16, CUE["insa"] + i * 0.16 + 0.28)
        o *= 1 - ease_in(r)
        if r >= 1:
            o = -6 * math.sin((t - CUE["insa"] - i * 0.16 - 0.28) * 30) * math.exp(
                -(t - CUE["insa"] - i * 0.16 - 0.28) * 12)
        offs.append(o)
    return offs


def sh070(cv, t):
    S1.world(cv, t)
    cam = cam_a(t)
    bob = math.sin(t * 1.3) * 6
    offs = band_offsets(t)
    tint = [ease_out(remap(t, CUE["sifir"] + 0.1 + 0.06 * i, CUE["sifir"] + 0.6 + 0.06 * i)) for i in range(5)]
    fire = 1.0 + 0.6 * pulse(t, CUE["karmasik"] + 0.4, 0.6)
    fly = remap(t, 29.55, 30.25)
    cv.save()
    cam.apply(cv)
    cv.translate(S1.BRAIN_POS[0], S1.BRAIN_POS[1] + bob)
    cv.scale(S1.BRAIN_S, S1.BRAIN_S)
    if fly <= 0:
        draw_layered_brain(cv, t, offs, tint, min(fire, 1.0), glow=0.7)
        # numbers
        nf = font(46, 900)
        for i in range(5):
            k = ease_out_back(remap(t, CUE["bes"] - 0.05 + i * 0.09, CUE["bes"] + 0.3 + i * 0.09))
            if k > 0:
                y = BAND_YC[i] + offs[i]
                cv.save()
                cv.translate(372, y)
                cv.scale(k, k)
                cv.drawCircle(0, 0, 40, fill(hexc(STAGE_COLS[i], 0.5), blur=14))
                cv.drawCircle(0, 0, 34, fill(hexc(STAGE_COLS[i])))
                draw_text(cv, str(i + 1), 0, 16, nf, fill(hexc("#0b1026")))
                cv.restore()
                cv.drawLine(296, y, 372 - 40 * k, y, stroke(hexc(STAGE_COLS[i], 0.7 * k), 3))
    cv.restore()
    # title
    if t > CUE["bes"] - 0.1 and fly < 0.6:
        a = 1 - remap(fly, 0, 0.6)
        draw_text_reveal(cv, "5 AŞAMA", 330, 500, font(110, 900), "#ffffff", t - (CUE["bes"] - 0.1),
                         stagger=0.05, dur=0.35, a=a, glow=14)
        if t > CUE["insa"]:
            draw_text_reveal(cv, "katman katman inşa", 330, 570, font(40, 500), "#ffb347", t - CUE["insa"],
                             stagger=0.02, dur=0.3, a=a)
    if fly > 0:
        fly_to_steps(cv, t, cam, bob, offs, tint)


def band_screen(cam, bob, offs, i):
    lx, ly = 0, BAND_YC[i] + offs[i]
    wx = S1.BRAIN_POS[0] + lx * S1.BRAIN_S
    wy = S1.BRAIN_POS[1] + bob + ly * S1.BRAIN_S
    return W / 2 + (wx - cam.x) * cam.zoom, H / 2 + (wy - cam.y) * cam.zoom, S1.BRAIN_S * cam.zoom


def fly_to_steps(cv, t, cam, bob, offs, tint):
    for i in range(5):
        p = ease_in_out(remap(t, 29.55 + i * 0.05, 30.2 + i * 0.07))
        sx, sy, ss = band_screen(cam, bob, offs, i)
        bx, by, bw, bh = step_rect(i)
        tx, ty = bx + bw / 2, by + 40
        x, y = lerp(sx, tx, p), lerp(sy, ty, p)
        if p < 1:
            cv.save()
            cv.translate(x, y)
            cv.scale(ss * (1 - 0.75 * p), ss * (1 - 0.75 * p))
            cv.translate(0, -BAND_YC[i])
            cv.saveLayerAlpha(None, int(255 * (1 - p)))
            cv.clipRect(band_clip(i), doAntiAlias=True)
            cv.saveLayer(None, None)
            brain_comp(cv, t, 1.0)
            pp = fill(hexc(STAGE_COLS[i], 0.72 * tint[i]))
            pp.setBlendMode(skia.BlendMode.kSrcATop)
            cv.drawRect(band_clip(i), pp)
            cv.restore()
            cv.restore()
            cv.restore()


# ===================================================================== SH080 staircase
def step_rect(i):
    w = 300
    x = 160 + i * 330
    top = 850 - i * 118
    return x, top, w, H + 80 - top


def cam_s(t):
    """Focus each stage as it is introduced, then pull back for the sweep."""
    focus = [(step_rect(i)[0] + 150, step_rect(i)[1] - 150) for i in range(5)]
    x, y, z = W / 2, H / 2, 1.0
    a0 = ease_in_out(remap(t, 30.45, 31.2))
    x, y, z = lerp(x, focus[0][0] + 60, a0), lerp(y, focus[0][1], a0), lerp(z, 1.55, a0)
    for i in range(1, 5):
        c = CUE[STAGE_CUE[i]]
        a = ease_in_out(remap(t, c - 0.45, c + 0.35))
        x, y = lerp(x, focus[i][0] + 40, a), lerp(y, focus[i][1], a)
    b = ease_in_out(remap(t, CUE["uzanan"] - 0.2, CUE["uzanan"] + 0.9))
    x, y, z = lerp(x, W / 2, b), lerp(y, H / 2 - 20, b), lerp(z, 1.0, b)
    return Cam(x, y, z)


def step_blocks(cv, t, appear=1.0):
    nf = font(64, 900)
    af = font(25, 700)
    for i in range(5):
        x, top, w, h = step_rect(i)
        rise = (1 - ease_out_back(remap(t, 29.8 + i * 0.07, 30.3 + i * 0.07))) * 560
        top += rise
        col = STAGE_COLS[i]
        cv.drawPath(rrect(x + 8, top + 12, w, h, 16), fill(hexc("#000000", 0.35), blur=14))
        cv.drawPath(rrect(x, top, w, h, 16), fill(0, shader=lin((x, top), (x, top + 260), [
            hexc(mix_hex(col, "#ffffff", 0.15)), hexc(col), hexc(mix_hex(col, "#0b1026", 0.55))], [0, 0.25, 1])))
        cv.drawPath(rrect(x, top, w, 18, 9), fill(hexc("#ffffff", 0.25)))
        draw_text(cv, str(i + 1), x + 40, top + 86, nf, fill(hexc("#ffffff", 0.35)), align="center")
        c = CUE[ABIL_CUE[i]]
        if t > c - 0.05:
            draw_text_reveal(cv, ABILITY[i], x + w / 2 + 18, top + 140, af, "#ffffff", t - (c - 0.05),
                             stagger=0.02, dur=0.25)


def mix_hex(a, b, k):
    from fm_2d.core import mixhex
    return mixhex(a, b, k)


def chip(cv, text, x, y, col, k, size=24):
    if k <= 0:
        return
    f = font(size, 800)
    w = f.measureText(text) + 40 + 2 * len(text)
    cv.save()
    cv.translate(x, y)
    s = ease_out_back(k)
    cv.scale(s, s)
    cv.drawPath(rrect(-w / 2, -22, w, 42, 21), fill(hexc(col, 0.45), blur=12))
    cv.drawPath(rrect(-w / 2, -22, w, 42, 21), fill(hexc(col)))
    draw_text(cv, text, 0, 8, f, fill(hexc("#0b1026")), tracking=2)
    cv.restore()


def creature(cv, t, i, k):
    """Creature i standing on its step; k = appear progress."""
    if k <= 0:
        return
    x, top, w, _ = step_rect(i)
    cx = x + w / 2
    cv.save()
    s = ease_out_back(k)
    cv.translate(cx, top + 2)
    cv.scale(s, s)
    if i == 0:
        # steering toward food
        prog = ease_in_out(remap(t, CUE["yon"], CUE["yon"] + 1.4))
        cv.save()
        cv.translate(-40 + 40 * prog, -26)
        cv.scale(0.85, 0.85)
        draw_worm(cv, t)
        cv.restore()
        fk = remap(t, CUE["yon"] - 0.1, CUE["yon"] + 0.2)
        if fk > 0:
            lf = skia.Path()
            lf.moveTo(120, -30)
            lf.cubicTo(130, -60, 160, -60, 168, -40)
            lf.cubicTo(160, -20, 130, -18, 120, -30)
            cv.drawPath(lf, fill(hexc("#7ed957", fk)))
            arr = skia.Path()
            arr.moveTo(-10, -86)
            arr.quadTo(60, -126, 120, -80)
            pa = partial_path(arr, ease_out(remap(t, CUE["yon"], CUE["yon"] + 0.6)))
            cv.drawPath(pa, stroke(hexc("#ffffff", 0.85), 5))
            if remap(t, CUE["yon"], CUE["yon"] + 0.6) >= 1:
                head = skia.Path()
                head.moveTo(120, -80)
                head.lineTo(98, -82)
                head.lineTo(112, -100)
                head.close()
                cv.drawPath(head, fill(hexc("#ffffff", 0.85)))
    elif i == 1:
        # fish in a water globe
        cv.drawCircle(0, -100, 96, fill(0, shader=rad((-30, -140), 140, [hexc("#9fe8ff", 0.45),
                                                                         hexc("#38a3d6", 0.35)])))
        cv.drawCircle(0, -100, 96, stroke(hexc("#dff6ff", 0.7), 4))
        cv.drawRect(skia.Rect.MakeXYWH(-50, -14, 100, 14), fill(hexc("#1f5f9a")))
        cv.save()
        cv.translate(math.sin(t * 1.2) * 20, -100 + math.sin(t * 2.1) * 6)
        cv.scale(0.75, 0.75)
        draw_fish(cv, t)
        cv.restore()
        cv.drawPath(rrect(-60, -170, 30, 50, 15), fill(hexc("#ffffff", 0.25)))
        for j in range(4):
            ph = (t * 0.6 + j * 0.25) % 1
            cv.drawCircle(30 + j * 6, -110 - ph * 80, 4 + j, stroke(hexc("#ffffff", 0.6 * (1 - ph)), 2))
        # trial and error
        x1 = remap(t, CUE["deneme"], CUE["deneme"] + 0.3)
        x2 = remap(t, CUE["yanilma"], CUE["yanilma"] + 0.3)
        mark(cv, -60, -240, "x", x1)
        mark(cv, 60, -240, "v", x2)
    elif i == 2:
        draw_mouse(cv, t, 0.9)
        k2 = remap(t, CUE["hayal"] - 0.3, CUE["hayal"] + 0.1)
        bubble(cv, 40, -250, 230, 130, k2, tail=(-0.4, 1))
        if k2 >= 1:
            # imagined path to cheese
            pth = skia.Path()
            pth.moveTo(-60, -230)
            pth.cubicTo(-30, -300, 10, -190, 40, -250)
            pth.cubicTo(60, -290, 80, -260, 90, -240)
            pp = partial_path(pth, ease_in_out(remap(t, CUE["hayal"] + 0.1, CUE["hayal"] + 1.2)))
            pe = stroke(hexc("#ff7a6b"), 5)
            pe.setPathEffect(skia.DashPathEffect.Make([12, 9], -t * 40))
            cv.drawPath(pp, pe)
            ch = skia.Path()
            ch.moveTo(88, -224)
            ch.lineTo(126, -224)
            ch.lineTo(126, -252)
            ch.close()
            cv.drawPath(ch, fill(hexc("#ffd34d")))
            cv.drawCircle(114, -232, 4, fill(hexc("#e0a800")))
            cv.drawCircle(-62, -230, 7, fill(hexc("#8f7d6e")))
    elif i == 3:
        draw_monkey(cv, t, 0.95)
        k2 = remap(t, CUE["baskasi"] - 0.3, CUE["baskasi"] + 0.1)
        bubble(cv, 70, -300, 200, 150, k2, tail=(-0.5, 1))
        if k2 >= 1:
            cv.save()
            cv.translate(50, -258)
            cv.scale(0.42, 0.42)
            draw_monkey(cv, t + 1.3, 1.0, col="#a0643f")
            cv.restore()
            f = font(44, 900)
            qa = remap(t, CUE["baskasi"] + 0.2, CUE["baskasi"] + 0.5)
            draw_text(cv, "?", 128, -306, f, fill(hexc("#ff7a6b", qa)))
            hk = remap(t, CUE["baskasi"] + 0.5, CUE["baskasi"] + 0.8)
            heart = skia.Path()
            heart.moveTo(128, -350)
            heart.cubicTo(110, -368, 96, -344, 128, -326)
            heart.cubicTo(160, -344, 146, -368, 128, -350)
            cv.save()
            cv.translate(0, -10 * hk)
            cv.drawPath(heart, fill(hexc("#ff7a6b", hk)))
            cv.restore()
    else:
        draw_human(cv, t, 0.55)
        k2 = remap(t, CUE["konus"] - 0.2, CUE["konus"] + 0.15)
        bubble(cv, 150, -300, 230, 100, k2, col="#ffffff", tail=(-0.45, 0.9))
        if k2 >= 1:
            txt = "Merhaba!"
            n = int(len(txt) * clamp(remap(t, CUE["konus"] + 0.15, CUE["konus"] + 0.8)))
            draw_text(cv, txt[:n], 150, -288, font(36, 800), fill(hexc("#2b2147")))
    cv.restore()


def mark(cv, x, y, kind, k):
    if k <= 0:
        return
    cv.save()
    cv.translate(x, y)
    s = ease_out_back(k)
    cv.scale(s, s)
    col = "#ff5c6c" if kind == "x" else "#5be38a"
    cv.drawCircle(0, 0, 34, fill(hexc(col, 0.4), blur=10))
    cv.drawCircle(0, 0, 30, fill(hexc(col)))
    if kind == "x":
        cv.drawLine(-12, -12, 12, 12, stroke(hexc("#ffffff"), 7))
        cv.drawLine(12, -12, -12, 12, stroke(hexc("#ffffff"), 7))
    else:
        p = skia.Path()
        p.moveTo(-13, 0)
        p.lineTo(-4, 10)
        p.lineTo(14, -10)
        cv.drawPath(p, stroke(hexc("#ffffff"), 7))
    cv.restore()


def staircase(cv, t, cam=None):
    S1.background(cv, t)
    cam = cam or cam_s(t)
    cv.save()
    cam.apply(cv)
    glow_circle(cv, W / 2, 700, 900, "#b48bff", 0.10)
    step_blocks(cv, t)
    for i in range(5):
        c = CUE[STAGE_CUE[i]]
        k = remap(t, c - 0.1, c + 0.35)
        creature(cv, t, i, k)
        x, top, w, _ = step_rect(i)
        chip(cv, NAMES[i], x + w / 2 + 18, top + 72, "#ffffff", remap(t, c, c + 0.3))
    # the sweep: "uzanan harika bir süreç"
    sw = remap(t, CUE["uzanan"] + 0.2, CUE["surec"] + 0.2)
    if sw > 0:
        p = skia.Path()
        pts = [(step_rect(i)[0] + 150, step_rect(i)[1] + 14) for i in range(5)]
        p.moveTo(pts[0][0] - 170, pts[0][1] + 20)
        for (x, y) in pts:
            p.lineTo(x, y)
        p.lineTo(pts[-1][0] + 180, pts[-1][1] - 70)
        pp = partial_path(p, ease_in_out(sw))
        draw_glow_path(cv, pp, "#ffe2b0", 6, a=0.9, glow=14)
        meas = skia.PathMeasure(pp, False)
        L = meas.getLength()
        if L > 1:
            pos, _ = meas.getPosTan(L)
            glow_circle(cv, pos.x(), pos.y(), 70, "#ffb347", 0.8)
    cv.restore()
    sp = remap(t, CUE["harika"], CUE["harika"] + 1.2)
    if 0 < sp < 1:
        rnd = random.Random(8)
        for j in range(40):
            x, y = rnd.uniform(100, W - 100), rnd.uniform(80, 600)
            ph = clamp(sp * 1.6 - rnd.random() * 0.6)
            a = math.sin(math.pi * ph)
            if a > 0:
                sparkle(cv, x, y, 6 + 10 * a, "#fff1c9", a)


def sparkle(cv, x, y, r, col, a):
    p = skia.Path()
    p.moveTo(x, y - r)
    p.quadTo(x, y, x + r, y)
    p.quadTo(x, y, x, y + r)
    p.quadTo(x, y, x - r, y)
    p.quadTo(x, y, x, y - r)
    cv.drawPath(p, fill(hexc(col, a)))
    cv.drawCircle(x, y, r * 0.8, fill(hexc(col, 0.4 * a), blur=6))


# ===================================================================== SH090 head + museum
BUST = (760, 1100)
BUST_S = 1.9
HEAD_C = (BUST[0] + 6 * BUST_S, BUST[1] - (96 + 168) * BUST_S)  # cranium centre
BRAIN_IN_S = 0.48


def brain_in_head_tf(cv):
    cv.translate(HEAD_C[0] - 8, HEAD_C[1] + 30)
    cv.scale(-BRAIN_IN_S, BRAIN_IN_S)  # mirrored -> faces right like the head


def cam_m(t):
    x, y, z = W / 2, H / 2, 1.0
    a = ease_in_out(remap(t, CUE["canli"] - 0.35, CUE["muze"] + 0.4))
    x, y, z = lerp(x, 900, a), lerp(y, 860, a), lerp(z, 0.6, a)
    z *= 1 + 0.012 * math.sin(t * 0.8)
    return Cam(x, y, z)


def museum_room(cv, t, a):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    cv.drawRect(skia.Rect.MakeLTRB(-1400, -800, 3400, 1500), fill(0, shader=lin((0, -800), (0, 1500), [
        hexc("#1a1438"), hexc("#2a1f4f")])))
    # wainscot + floor
    cv.drawRect(skia.Rect.MakeLTRB(-1400, 1180, 3400, 1500), fill(hexc("#231a45")))
    cv.drawLine(-1400, 1180, 3400, 1180, stroke(hexc("#ffe2b0", 0.15), 4))
    cv.drawRect(skia.Rect.MakeLTRB(-1400, 1500, 3400, 2400), fill(0, shader=lin((0, 1500), (0, 2000), [
        hexc("#3a2d5e"), hexc("#140f2c")])))
    for x in range(-1400, 3400, 220):
        cv.drawLine(x, 1500, x + (x - 900) * 0.5, 2400, stroke(hexc("#ffffff", 0.04), 3))
    # side exhibits (callbacks to SC01 fossils)
    for (fx, kind) in ((-420, "ammonite"), (2330, "trilobite")):
        cv.drawPath(rrect(fx - 190, 300, 380, 440, 10), fill(hexc("#120e28")))
        cv.drawPath(rrect(fx - 190, 300, 380, 440, 10), stroke(hexc("#c9a35c"), 14))
        glow_circle(cv, fx, 520, 260, "#ffe2b0", 0.18)
        cv.save()
        cv.translate(fx, 520)
        if kind == "ammonite":
            draw_ammonite(cv, 110)
        else:
            draw_trilobite(cv, 1.6)
        cv.restore()
        cv.drawPath(rrect(fx - 110, 780, 220, 50, 6), fill(hexc("#c9a35c", 0.9)))
    # pedestal
    cv.drawPath(rrect(BUST[0] - 330, BUST[1] - 10, 660, 70, 8), fill(hexc("#e8dcc3")))
    cv.drawRect(skia.Rect.MakeLTRB(BUST[0] - 290, BUST[1] + 60, BUST[0] + 290, 1500),
                fill(0, shader=lin((BUST[0] - 290, 0), (BUST[0] + 290, 0), [hexc("#d8cbb0"), hexc("#f3e8cf"),
                                                                           hexc("#b9a77f")], [0, 0.4, 1])))
    # plaque
    cv.drawPath(rrect(BUST[0] - 250, 1230, 500, 170, 10), fill(hexc("#2b2147")))
    cv.drawPath(rrect(BUST[0] - 250, 1230, 500, 170, 10), stroke(hexc("#c9a35c"), 5))
    draw_text(cv, "CANLI FOSİL MÜZESİ", BUST[0], 1300, font(42, 900), fill(hexc("#ffe2b0")), tracking=3)
    draw_text(cv, "İnsan beyni · 600 milyon yıllık koleksiyon", BUST[0], 1352, font(26, 500),
              fill(hexc("#cfd8ff", 0.85)))
    cv.restore()


def museum_front(cv, t, a):
    """Glass case + spotlights, drawn over the head."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    x0, x1, y0, y1 = BUST[0] - 420, BUST[0] + 420, 230, BUST[1] - 10
    cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(hexc("#bfe0ff", 0.06)))
    cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), stroke(hexc("#dfeeff", 0.45), 5))
    g = skia.Path()
    g.moveTo(x0 + 40, y0 + 40)
    g.lineTo(x0 + 140, y0 + 40)
    g.lineTo(x0 + 40, y0 + 260)
    g.close()
    cv.drawPath(g, fill(hexc("#ffffff", 0.08)))
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 10, y0 - 30, x1 + 10, y0), fill(hexc("#c9a35c")))
    for lx in (BUST[0] - 220, BUST[0] + 220):
        on = remap(t, CUE["canli"] + (0 if lx < BUST[0] else 0.18), CUE["canli"] + 0.1 + (0 if lx < BUST[0] else 0.18))
        cone = skia.Path()
        cone.moveTo(lx - 30, -300)
        cone.lineTo(lx + 30, -300)
        cone.lineTo(lx + 300 * (1 if lx < BUST[0] else -1) * 0.2 + 260, 1100)
        cone.lineTo(lx + 300 * (1 if lx < BUST[0] else -1) * 0.2 - 260, 1100)
        cone.close()
        cv.drawPath(cone, fill(0, shader=lin((0, -300), (0, 1100), [hexc("#ffe2b0", 0.22 * on),
                                                                     hexc("#ffe2b0", 0)]), blur=10))
        cv.drawPath(rrect(lx - 36, -330, 72, 50, 10), fill(hexc("#120e28")))
    # velvet rope
    for px in (BUST[0] - 560, BUST[0] + 560):
        cv.drawRect(skia.Rect.MakeXYWH(px - 8, 1560, 16, 200), fill(hexc("#c9a35c")))
        cv.drawCircle(px, 1556, 16, fill(hexc("#e8c46c")))
    rope = skia.Path()
    rope.moveTo(BUST[0] - 560, 1580)
    rope.quadTo(BUST[0], 1700, BUST[0] + 560, 1580)
    cv.drawPath(rope, stroke(hexc("#b8324a"), 16))
    cv.restore()


def badges(cv, t, a):
    if a <= 0:
        return
    hf = font(26, 800)
    k0 = remap(t, CUE["zeka"] - 0.1, CUE["zeka"] + 0.3)
    draw_text(cv, "600 MİLYON YILLIK KATMANLAR", 1440, 175, hf, fill(hexc("#ffb347", a * k0)), tracking=3)
    for i in range(5):
        k = remap(t, 45.0 + i * 0.32, 45.3 + i * 0.32)
        if k <= 0:
            continue
        bx, by = 1440, 880 - i * 150
        # line from brain band to badge
        lx = HEAD_C[0] - 8 + 240 * BRAIN_IN_S
        ly = HEAD_C[1] + 30 + BAND_YC[i] * BRAIN_IN_S
        p = skia.Path()
        p.moveTo(lx, ly)
        p.cubicTo(lx + 180, ly, bx - 240, by, bx - 66, by)
        cv.drawPath(partial_path(p, ease_out(k)), stroke(hexc(STAGE_COLS[i], 0.8 * a), 3))
        cv.drawCircle(lx, ly, 7 * k, fill(hexc(STAGE_COLS[i], a)))
        cv.save()
        cv.translate(bx, by)
        s = ease_out_back(k)
        cv.scale(s, s)
        cv.drawCircle(0, 0, 66, fill(hexc(STAGE_COLS[i], 0.45 * a), blur=14))
        cv.drawCircle(0, 0, 60, fill(hexc("#141a3a", a)))
        cv.drawCircle(0, 0, 60, stroke(hexc(STAGE_COLS[i], a), 6))
        clip = skia.Path()
        clip.addCircle(0, 0, 56)
        cv.save()
        cv.clipPath(clip, doAntiAlias=True)
        cv.saveLayerAlpha(None, int(255 * a))
        [lambda: (cv.translate(0, 8), cv.scale(0.42, 0.42), draw_worm(cv, t)),
         lambda: (cv.translate(4, 4), cv.scale(0.5, 0.5), draw_fish(cv, t)),
         lambda: (cv.translate(-6, 44), cv.scale(0.42, 0.42), draw_mouse(cv, t)),
         lambda: (cv.translate(-4, 66), cv.scale(0.4, 0.4), draw_monkey(cv, t)),
         lambda: (cv.translate(-10, 72), cv.scale(0.27, 0.27), draw_human(cv, t))][i]()
        cv.restore()
        cv.restore()
        cv.restore()
        draw_text(cv, NAMES[i], bx + 86, by + 10, font(28, 800), fill(hexc("#ffffff", a)), align="left")


def head_scene(cv, t, glass_k):
    cam = cam_m(t)
    S1.background(cv, t)
    cv.save()
    cam.apply(cv)
    room = remap(t, CUE["canli"] - 0.4, CUE["canli"] + 0.4)
    museum_room(cv, t, room)
    glow_circle(cv, HEAD_C[0], HEAD_C[1], 520, "#b48bff", 0.16 * (1 - room) + 0.10)
    # opaque human fading to glass
    if glass_k < 1:
        cv.save()
        cv.translate(*BUST)
        cv.saveLayerAlpha(None, int(255 * (1 - glass_k)))
        draw_human(cv, t, BUST_S)
        cv.restore()
        cv.restore()
    if glass_k > 0:
        cv.save()
        cv.translate(*BUST)
        draw_human(cv, t, BUST_S, glass=True, a=glass_k)
        cv.restore()
        # brain inside
        tints = [ease_out(remap(t, 45.0 + i * 0.32, 45.3 + i * 0.32)) for i in range(5)]
        cv.save()
        brain_in_head_tf(cv)
        cv.saveLayerAlpha(None, int(255 * glass_k))
        fire = 0.5 + 0.5 * remap(t, CUE["yapi"], CUE["yapi"] + 0.5)
        draw_layered_brain(cv, t, [0] * 5, tints, fire, glow=0.6)
        cv.restore()
        cv.restore()
    museum_front(cv, t, room)
    robot_visit(cv, t)
    cv.restore()
    badges(cv, t, glass_k * (1 - remap(t, CUE["canli"] - 0.5, CUE["canli"])))
    # "EVET"
    ek = remap(t, CUE["evet"] - 0.12, CUE["evet"] + 0.18)
    if ek > 0:
        cv.save()
        cv.translate(1460, 250)
        cv.rotate(-8)
        s = lerp(1.8, 1.0, ease_out(ek))
        cv.scale(s, s)
        a = clamp(ek * 2) * EVET_ALPHA(t)
        cv.drawPath(rrect(-220, -80, 440, 150, 26), fill(hexc("#5be38a", 0.35 * a), blur=20))
        cv.drawPath(rrect(-220, -80, 440, 150, 26), stroke(hexc("#5be38a", a), 10))
        draw_text(cv, "EVET!", 30, 32, font(104, 900), fill(hexc("#e9ffef", a)), tracking=6)
        ck = skia.Path()
        ck.moveTo(-180, -6)
        ck.lineTo(-150, 26)
        ck.lineTo(-100, -36)
        cv.drawPath(ck, stroke(hexc("#5be38a", a), 16))
        cv.restore()
        if ek < 1:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#e9ffef", 0.18 * (1 - ek))))


def robot_visit(cv, t):
    if t < 48.7:
        return
    rx = lerp(2650, 1880, ease_out(remap(t, 48.7, 49.7)))
    ry = 1660
    happy = t > CUE["kesin"]
    nod = 7 * math.sin((t - CUE["kesin"]) * 16) * math.exp(-(t - CUE["kesin"]) * 3) if happy else 0
    cv.save()
    cv.translate(rx, ry)
    cv.scale(-1, 1)
    draw_robot(cv, t, eye_dx=1.0, eye_dy=-0.4, blink=pulse(t, 49.1, 0.07),
               head_tilt=(-10 * smooth(remap(t, CUE["dusun"], CUE["dusun"] + 0.3)) if not happy else 0) + nod,
               shoulder=80, elbow=-20, mood="happy" if happy else ("confused" if t > CUE["dusun"] else "neutral"),
               scale=1.7)
    cv.restore()
    qk = remap(t, CUE["miyiz"] - 0.25, CUE["miyiz"] + 0.1) * (1 - remap(t, CUE["kesin"], CUE["kesin"] + 0.2))
    if qk > 0:
        S1.draw_qmark(cv, t, (rx - 30, ry - 880), ease_out_back(qk) * 1.1, a=qk)


# ===================================================================== DISPATCH
def render(cv, t):
    if t < 29.55:
        sh070(cv, t)
    elif t < 30.45:
        # layers fly down onto the rising steps; the strata world fades away underneath
        staircase(cv, t, Cam())
        k = remap(t, 29.55, 30.0)
        cv.saveLayerAlpha(None, int(255 * (1 - k)))
        S1.world(cv, t)
        cv.restore()
        cam = cam_a(t)
        fly_to_steps(cv, t, cam, math.sin(t * 1.3) * 6, band_offsets(t), [1] * 5)
    elif t < 42.2:
        staircase(cv, t)
    elif t < 42.95:
        # zoom into the human head of step 5, match into the big head
        k = remap(t, 42.2, 42.95)
        x, top, w, _ = step_rect(4)
        head = (x + w / 2 + 6 * 0.55, top - (96 + 168) * 0.55)
        cam = cam_s(t)
        hs = (W / 2 + (head[0] - cam.x) * cam.zoom, H / 2 + (head[1] - cam.y) * cam.zoom)
        z = math.exp(ease_in_out(k) * math.log(BUST_S / 0.55))
        tgt = (lerp(hs[0], HEAD_C[0], ease_in_out(k)), lerp(hs[1], HEAD_C[1], ease_in_out(k)))
        S1.background(cv, t)
        cv.save()
        cv.translate(*tgt)
        cv.scale(z, z)
        cv.translate(-hs[0], -hs[1])
        cv.saveLayerAlpha(None, int(255 * (1 - remap(k, 0.6, 1.0))))
        staircase(cv, t)
        cv.restore()
        cv.restore()
        if k > 0.6:
            cv.saveLayerAlpha(None, int(255 * remap(k, 0.6, 1.0)))
            head_scene(cv, t, 0.0)
            cv.restore()
    else:
        head_scene(cv, t, ease_in_out(remap(t, CUE["kafa"], CUE["yapi"])))


if __name__ == "__main__":
    import argparse

    from PIL import Image

    from fm_2d.core import Finisher, new_surface, snapshot

    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--out", default=str(ROOT / "projects/zeka_tarihi/11_render/SC02"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fin = Finisher()
    surf = new_surface()
    for ts in a.still or []:
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        render(cv, ts)
        Image.fromarray(fin(snapshot(surf), int(ts * FPS))).save(out / f"still_{ts:05.2f}.png")
        print("wrote", ts)
