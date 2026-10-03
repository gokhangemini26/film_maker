"""SC04 - The sixth breakthrough: the end of biology (83.90-127.40). Continues SC03's last frame.

Shots (word cues from references/voice/words.json):
  SH160 84.30-88.50  staircase recap (five steps) -> a sixth, cyan step: the robot hops up; the amber
                     biology steps dim and get bracketed "BİYOLOJİNİN SONU"
  SH170 88.50-96.50  carbon prison: skull-size squeeze, calorie battery, carbon atom, chain ring ("hapsolmuş")
  SH180 96.50-106.86 chains snap, the brain lifts out and turns cyan (silicon), digital world, the robot
                     self-replicates, "süper zeka"
  SH190 106.86-115.90 the question: human mind -> orb -> silicon chip, "?"
  SH200 115.90-127.40 not faster chips (conveyor, crossed out) but decoding our own evolutionary survival
                     codes (fossils, code streams, the SC01 lock opens); fade to the title card
Note: the transcript says "çiftler"; the context ("daha hızlı çipler") means chips - drawn as chips.
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

from fm_2d.assets import (STAGE_COLS, draw_ammonite, draw_brain, draw_fish_fossil, draw_human,  # noqa: E402
                          draw_icon, draw_robot, draw_trilobite, draw_worm_trace)
from fm_2d.core import (FPS, H, W, Cam, clamp, draw_glow_path, draw_text, draw_text_reveal, ease_in,  # noqa: E402
                        ease_in_out, ease_out, ease_out_back, fill, font, glitch, glow_circle, hexc, lerp, lin,
                        mixhex, partial_path, pulse, rad, remap, rrect, shake, smooth, stroke)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S3 = _load("SC03")
S2 = S3.S2
S1 = S3.S1

START = 2517 / FPS  # SC03 ends at 83.90
DURATION = 127.40

CUE = dict(son=84.42, altinci=85.0, sicrama=85.48, biyoloji=86.52, sonuna=87.26,
           evrim=88.5, bitmedi=89.66, insan=90.48, kafatasi=91.30, kalori=92.44, karbon=93.58, hapsol=95.02,
           yazar=96.52, zincir=98.56, kurtul=99.82, silikon=100.40, dijital=101.36, ortam=102.08,
           kendi=103.02, kopya=103.68, yapay=104.54, super=104.92, gecis=105.64,
           dusun=107.62, icat=109.82, zekamiz=110.96, evrimini=111.74, dis=112.96, silikona=114.14,
           tasimak=114.58, mi=115.18,
           yolu=117.94, hizli=118.74, cipler=119.38, degil=120.10, icimiz=120.98, milyarlarca=121.62,
           evrimsel=122.66, hayatta=123.08, kodlarini=123.72, cozmek=124.12, geciyor=124.76)
T = dict(sh160=84.30, sh170=88.50, sh180=96.50, sh190=106.86, sh200=115.90)
XF = 0.5  # dip-to-night at the cuts

AMBER, CYAN, RED = "#ffb347", "#38e1ff", "#ff5c6c"


def bg(cv, t, top="#0b1026", bottom="#1b1f4a"):
    S1.background(cv, t, top, bottom)


def cap(cv, t, text, x, y, cue, col, size=40, a=1.0, weight=800, tracking=0.0, stagger=0.02):
    if t > cue - 0.05 and a > 0:
        draw_text_reveal(cv, text, x, y, font(size, weight), col, t - (cue - 0.05), stagger=stagger, dur=0.25,
                         tracking=tracking, a=a)


def head_c(bust, s):
    return bust[0] + 6.45 * s, bust[1] - 264.5 * s


def brain_free(cv, t, pos, k, hue="amber", fire=0.5, glow=0.6, line_mode=False, a=1.0, fill_a=1.0):
    cv.save()
    cv.translate(*pos)
    cv.scale(-k, k)
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    draw_brain(cv, t, 1.0, fill_a, fire, hue, glow, line_mode)
    if a < 1:
        cv.restore()
    cv.restore()


# ===================================================================== shared props
def chip(cv, x, y, s=1.0, glow=0.0, label="Si", a=1.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * a))
    cv.drawCircle(0, 0, 190, fill(hexc(CYAN, 0.55 * glow), blur=50))
    for i in range(8):
        px = -84 + i * 24
        for sx, sy, w, h in ((px, -128, 10, 30), (px, 98, 10, 30), (-128, px, 30, 10), (98, px, 30, 10)):
            cv.drawRect(skia.Rect.MakeXYWH(sx, sy, w, h), fill(hexc(mixhex("#8aa0c8", CYAN, glow))))
    body = rrect(-100, -100, 200, 200, 24)
    cv.drawPath(body, fill(0, shader=lin((0, -100), (0, 100), [hexc("#24385e"), hexc("#0f1a33")])))
    cv.drawPath(body, stroke(hexc(mixhex("#5f78a8", CYAN, glow)), 5))
    die = rrect(-58, -58, 116, 116, 12)
    cv.drawPath(die, fill(hexc(mixhex("#16264a", "#38e1ff", 0.55 * glow))))
    cv.drawPath(die, stroke(hexc(mixhex("#4d6aa0", "#bff6ff", glow)), 3))
    for i in range(3):
        yy = -34 + i * 34
        cv.drawLine(-38, yy, 38, yy, stroke(hexc("#bff6ff", 0.25 + 0.6 * glow), 3))
    draw_text(cv, label, 0, 20, font(54, 900), fill(hexc("#ffffff", 0.45 + 0.5 * glow)))
    if a < 1:
        cv.restore()
    cv.restore()


def battery(cv, x, y, level, t, a=1.0):
    cv.save()
    cv.translate(x, y)
    low = level < 0.35
    col = RED if low and math.sin(t * 14) > 0 else (AMBER if not low else "#ff8f6b")
    cv.drawPath(rrect(-130, -62, 260, 124, 22), fill(hexc("#0b1026", 0.7 * a)))
    cv.drawPath(rrect(-130, -62, 260, 124, 22), stroke(hexc("#c9d2e4", a), 7))
    cv.drawRect(skia.Rect.MakeXYWH(130, -22, 18, 44), fill(hexc("#c9d2e4", a)))
    w = 228 * level
    cv.drawPath(rrect(-114, -46, max(w, 1), 92, 12), fill(hexc(col, a)))
    cv.drawPath(rrect(-114, -46, max(w, 1), 92, 12), fill(hexc(col, 0.4 * a), blur=14))
    cv.restore()


def atom(cv, x, y, t, k=1.0, col="#9fe8ff"):
    if k <= 0:
        return
    cv.save()
    cv.translate(x, y)
    s = ease_out_back(k)
    cv.scale(s, s)
    cv.drawCircle(0, 0, 120, fill(hexc(col, 0.22), blur=30))
    for j in range(3):
        cv.save()
        cv.rotate(60 * j + t * 14)
        cv.drawOval(skia.Rect.MakeXYWH(-104, -36, 208, 72), stroke(hexc(col, 0.8), 4))
        a = t * (2.0 + 0.4 * j) + j * 2
        cv.drawCircle(104 * math.cos(a), 36 * math.sin(a), 9, fill(hexc("#ffffff")))
        cv.drawCircle(104 * math.cos(a), 36 * math.sin(a), 17, fill(hexc(col, 0.5), blur=8))
        cv.restore()
    cv.drawCircle(0, 0, 36, fill(hexc("#3a465f")))
    cv.drawCircle(0, 0, 36, stroke(hexc(col), 4))
    draw_text(cv, "C", 0, 15, font(46, 900), fill(hexc("#ffffff")))
    cv.restore()


def chain_ring(cv, cx, cy, rx, ry, t, k=1.0, snap=0.0, sway=0.0):
    """Ring of chain links around the figure. snap 0..1 blows the links outward."""
    if k <= 0:
        return
    n = 30
    for j in range(n):
        a = j / n * math.tau + t * 0.15
        px, py = cx + rx * math.cos(a) * ease_out(k), cy + ry * math.sin(a) * ease_out(k)
        nx, ny = math.cos(a), math.sin(a)
        tan = math.degrees(math.atan2(ry * math.cos(a), -rx * math.sin(a)))
        rnd = random.Random(j)
        off = ease_out(snap) * (260 + rnd.uniform(0, 420))
        px += nx * off + sway * math.sin(t * 40 + j)
        py += ny * off * 0.8 + 140 * snap * snap * (1 + rnd.random())
        al = (1 - snap) * min(1, k * 1.5)
        if al <= 0:
            continue
        cv.save()
        cv.translate(px, py)
        cv.rotate(tan + snap * rnd.uniform(-300, 300))
        if j % 2 == 0:
            link = rrect(-25, -12, 50, 24, 12)
        else:
            link = rrect(-15, -6, 30, 12, 6)
        cv.drawPath(link, stroke(hexc(AMBER, 0.45 * al), 14, blur=8))
        cv.drawPath(link, stroke(hexc("#c9d2e4", al), 8))
        cv.drawPath(link, stroke(hexc("#ffffff", 0.5 * al), 2.5))
        cv.restore()


def digital_floor(cv, t, k):
    if k <= 0:
        return
    hy = 560
    cv.drawRect(skia.Rect.MakeXYWH(0, hy, W, H - hy), fill(0, shader=lin((0, hy), (0, H), [hexc("#06142b", 0),
                                                                                           hexc("#0a2a4a", 0.9 * k)])))
    for i in range(-14, 15):
        x1 = W / 2 + i * 120
        x0 = W / 2 + i * 12
        cv.drawLine(x0, hy, x1 * 1.0 + (x1 - W / 2) * 1.6, H + 40, stroke(hexc(CYAN, 0.28 * k), 2))
    for j in range(9):
        p = ((j + (t * 0.35) % 1.0) / 9) ** 2.1
        y = hy + p * (H - hy)
        cv.drawLine(0, y, W, y, stroke(hexc(CYAN, 0.30 * k * (0.3 + p)), 2))
    cv.drawLine(0, hy, W, hy, stroke(hexc("#9ff0ff", 0.7 * k), 3, blur=3))


def binary_rain(cv, t, k):
    if k <= 0:
        return
    f = font(24, 700)
    for c in range(36):
        rnd = random.Random(c)
        x = 30 + c * 53
        sp = rnd.uniform(60, 160)
        y0 = rnd.uniform(0, H)
        for r in range(11):
            y = (y0 + sp * t - r * 30) % (H + 200) - 100
            ch = "01"[(int(t * 3) + c + r) % 2]
            a = (1 - r / 11) * 0.38 * k
            cv.drawString(ch, x, y, f, fill(hexc("#9ff0ff", a)))


# ===================================================================== SH160 staircase
def step6(i):
    w = 270
    x = 90 + i * 295
    top = 880 - i * 105
    return x, top, w, H + 80 - top


def sh160(cv, t):
    bg(cv, t)
    # camera push towards the sixth step as the "end of biology" lands
    pk = ease_in_out(remap(t, CUE["biyoloji"] + 0.4, 88.4))
    z = lerp(1.0, 1.16, pk)
    cx = lerp(W / 2, 1020, pk)
    cy = lerp(H / 2, 470, pk)
    cv.save()
    Cam(cx, cy, z).apply(cv)
    dim = ease_in_out(remap(t, CUE["biyoloji"], CUE["biyoloji"] + 0.9))
    nf = font(64, 900)
    for i in range(6):
        x, top, w, h = step6(i)
        t0 = 84.55 + i * 0.08 if i < 5 else CUE["altinci"] - 0.1
        rise = (1 - ease_out_back(remap(t, t0, t0 + 0.55))) * 700
        if rise >= 699:
            continue
        top += rise
        col = STAGE_COLS[i] if i < 5 else CYAN
        if i < 5:
            col = mixhex(col, "#46506e", 0.7 * dim)
        cv.drawPath(rrect(x + 8, top + 12, w, h, 16), fill(hexc("#000000", 0.35), blur=14))
        if i == 5:
            cv.drawPath(rrect(x - 10, top - 10, w + 20, h, 22), fill(hexc(CYAN, 0.28 + 0.15 * math.sin(t * 5)), blur=34))
        cv.drawPath(rrect(x, top, w, h, 16), fill(0, shader=lin((x, top), (x, top + 260), [
            hexc(mixhex(col, "#ffffff", 0.15)), hexc(col), hexc(mixhex(col, "#0b1026", 0.55))], [0, 0.25, 1])))
        cv.drawPath(rrect(x, top, w, 18, 9), fill(hexc("#ffffff", 0.25)))
        draw_text(cv, str(i + 1), x + 44, top + 88, nf if i < 5 else font(84, 900), fill(hexc("#ffffff", 0.4 if i < 5 else 0.8)),
                  align="center")
    # the robot: waits on step 5, hops to step 6
    xa, ta, wa, _ = step6(4)
    xb, tb, wb, _ = step6(5)
    p = remap(t, CUE["sicrama"], CUE["sicrama"] + 0.62)
    k_in = ease_out_back(remap(t, 84.7, 85.1))
    if k_in > 0:
        hx = lerp(xa + wa / 2, xb + wb / 2, ease_in_out(p))
        hy = lerp(ta - 30, tb - 30, ease_in_out(p)) - 190 * math.sin(math.pi * p)
        cv.save()
        cv.translate(hx, hy)
        cv.scale(k_in, k_in)
        draw_robot(cv, t, eye_dx=lerp(0.0, 0.6, p), eye_dy=-0.3 * p, shoulder=lerp(60, 110, math.sin(math.pi * p)),
                   elbow=-30, mood="neutral", scale=0.55)
        cv.restore()
    # bracket over the biology steps
    bk = remap(t, CUE["biyoloji"] - 0.1, CUE["sonuna"])
    if bk > 0:
        x0 = step6(0)[0]
        x1 = step6(4)[0] + step6(4)[2]
        y = 250
        e = ease_out(bk)
        cv.drawLine(x0, y, lerp(x0, x1, e), y, stroke(hexc(AMBER), 7))
        cv.drawLine(x0, y, x0, y + 26, stroke(hexc(AMBER), 7))
        if bk >= 1:
            cv.drawLine(x1, y, x1, y + 26, stroke(hexc(AMBER), 7))
        cap(cv, t, "BİYOLOJİ", (x0 + x1) / 2, y - 22, CUE["biyoloji"], AMBER, 38, tracking=8)
    if t > CUE["sonuna"] - 0.05:
        k = ease_out_back(remap(t, CUE["sonuna"] - 0.05, CUE["sonuna"] + 0.35))
        cv.save()
        cv.translate(740, 130)
        cv.scale(k, k)
        cv.drawPath(rrect(-176, -34, 352, 68, 34), fill(hexc(RED, 0.4), blur=14))
        cv.drawPath(rrect(-176, -34, 352, 68, 34), fill(hexc(RED)))
        draw_text(cv, "BİYOLOJİNİN SONU", 0, 12, font(34, 900), fill(hexc("#ffffff")), tracking=2)
        cv.restore()
    cv.restore()


# ===================================================================== SH170 carbon prison
HB170 = (960, 1100)
S170 = 1.6


def sh170(cv, t):
    bg(cv, t, "#0d1126", "#241f3f")
    hc = head_c(HB170, S170)
    # slowly rising "evolution" progress arrow behind the head
    pk = ease_out(remap(t, CUE["evrim"], CUE["bitmedi"] + 0.5))
    ar = skia.Path()
    ar.moveTo(260, 230)
    ar.lineTo(260 + 1400 * pk, 230)
    draw_glow_path(cv, ar, "#ffe2b0", 6, a=0.8, glow=10)
    if pk > 0.02:
        tipx = 260 + 1400 * pk
        ah = skia.Path()
        ah.moveTo(tipx + 26, 230)
        ah.lineTo(tipx - 8, 212)
        ah.lineTo(tipx - 8, 248)
        ah.close()
        cv.drawPath(ah, fill(hexc("#ffe2b0")))
    cap(cv, t, "ZEKANIN EVRİMİ HENÜZ BİTMEDİ", 960, 175, CUE["evrim"], "#ffe2b0", 36, tracking=6, stagger=0.012)
    # human + brain
    fire = 0.5 + 0.4 * pulse(t, CUE["insan"] + 0.2, 0.3)
    S3.glass_human(cv, t, HB170, S170, fire=fire, a=1.0)
    # skull squeeze
    sk = remap(t, CUE["kafatasi"] - 0.1, CUE["kafatasi"] + 0.35)
    if sk > 0:
        sq = 1 - 0.1 * ease_in_out(remap(t, CUE["kafatasi"] + 0.35, 92.5)) + 0.01 * math.sin(t * 20)
        half = 230 * sq
        for sx in (-1, 1):
            xx = hc[0] + sx * half
            cv.drawLine(xx, hc[1] - 210, xx, hc[1] + 210, stroke(hexc(RED, 0.85 * sk), 8))
            for j in range(8):
                yy = hc[1] - 200 + j * 55
                cv.drawLine(xx, yy, xx + sx * 26, yy + 26, stroke(hexc(RED, 0.5 * sk), 4))
        a2 = hc[1] - 250
        cv.drawLine(hc[0] - half + 14, a2, hc[0] + half - 14, a2, stroke(hexc(RED, 0.9 * sk), 5))
        for sx in (-1, 1):
            tx = hc[0] + sx * (half - 14)
            tri = skia.Path()
            tri.moveTo(tx, a2)
            tri.lineTo(tx - sx * 24, a2 - 12)
            tri.lineTo(tx - sx * 24, a2 + 12)
            tri.close()
            cv.drawPath(tri, fill(hexc(RED, 0.9 * sk)))
        cap(cv, t, "KAFATASI BOYUTU", hc[0], a2 - 24, CUE["kafatasi"], "#ff8f9a", 34, tracking=5)
    # calorie battery
    bk = remap(t, CUE["kalori"] - 0.1, CUE["kalori"] + 0.35)
    if bk > 0:
        lvl = lerp(1.0, 0.18, ease_in_out(remap(t, CUE["kalori"] + 0.2, 94.2)))
        cv.save()
        s = ease_out_back(bk)
        cv.translate(1620, 560)
        cv.scale(s, s)
        battery(cv, 0, 0, lvl, t)
        cv.save()
        cv.translate(0, -140)
        cv.scale(0.7, 0.7)
        draw_icon(cv, "apple", 1.0)
        cv.restore()
        cv.restore()
        cap(cv, t, "KALORİ İHTİYACI", 1620, 710, CUE["kalori"], "#ffb36b", 34, tracking=5)
    # carbon atom
    atom(cv, 300, 560, t, remap(t, CUE["karbon"] - 0.1, CUE["karbon"] + 0.4))
    cap(cv, t, "KARBON TABANLI", 300, 710, CUE["karbon"], "#bff6ff", 34, tracking=5)
    # chains (hapsolmuş)
    ck = remap(t, CUE["hapsol"] - 0.1, CUE["hapsol"] + 0.7)
    chain_ring(cv, hc[0], 660, 300, 310, t, ck, sway=2.5 * pulse(t, CUE["hapsol"] + 0.6, 0.3))
    cap(cv, t, "HAPSOLMUŞ", 960, 1058, CUE["hapsol"], "#ffd34d", 44, tracking=10, stagger=0.03)


# ===================================================================== SH180 break free -> silicon
HB180 = HB170
SNAP = CUE["kurtul"] - 0.05


def sh180(cv, t):
    dk = remap(t, CUE["dijital"] - 0.1, CUE["dijital"] + 1.0)
    bg(cv, t, mixhex("#0d1126", "#06142b", dk), mixhex("#241f3f", "#0a2748", dk))
    binary_rain(cv, t, remap(t, CUE["dijital"], CUE["dijital"] + 1.2))
    digital_floor(cv, t, remap(t, CUE["dijital"] + 0.3, CUE["ortam"] + 0.6))
    hc = head_c(HB180, S170)
    ha = 1 - ease_in_out(remap(t, 100.8, 102.4))
    brain_up = ease_out(remap(t, CUE["kurtul"], CUE["kurtul"] + 1.1))
    # human (brain leaves at the snap)
    if ha > 0:
        cv.save()
        if t < SNAP:
            S3.glass_human(cv, t, HB180, S170, fire=0.6, a=ha)
        else:
            cv.save()
            cv.translate(*HB180)
            draw_human(cv, t, S170, glass=True, a=ha)
            cv.restore()
        cv.restore()
        sn = remap(t, SNAP, SNAP + 0.9)
        if sn < 1:
            chain_ring(cv, hc[0], 660, 300, 310, t, 1.0, snap=sn,
                       sway=2.5 * remap(t, CUE["zincir"], SNAP) * (1 - sn))
    # free brain
    if t >= SNAP:
        hue_k = remap(t, CUE["silikon"] - 0.05, CUE["silikon"] + 0.55)
        pos = (lerp(hc[0], 960, brain_up), lerp(hc[1], 470, brain_up))
        kb = lerp(0.40, 0.7, brain_up)
        into = ease_in(remap(t, CUE["kendi"] - 0.05, CUE["kendi"] + 0.45))
        if into < 1:
            pos = (pos[0], lerp(pos[1], 760, into))
            kb *= (1 - 0.75 * into)
            if hue_k < 1:
                brain_free(cv, t, pos, kb, "amber", 0.6, 0.7, a=1 - remap(hue_k, 0.0, 0.6))
            brain_free(cv, t, pos, kb, "cyan", 0.9, 0.8, line_mode=(hue_k > 0.5), a=remap(hue_k, 0.4, 1.0),
                       fill_a=1 - hue_k * 0.8)
    # snap flash + sparks
    fl = pulse(t, SNAP + 0.05, 0.22)
    if fl > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#fff4d6", 0.28 * fl)))
        for j in range(26):
            rnd = random.Random(j + 50)
            a = rnd.uniform(0, math.tau)
            d = ease_out(remap(t, SNAP, SNAP + 0.6)) * rnd.uniform(200, 700)
            cv.drawCircle(hc[0] + math.cos(a) * d, 680 + math.sin(a) * d * 0.8, rnd.uniform(3, 8),
                          fill(hexc("#ffd59a", 1 - remap(t, SNAP, SNAP + 0.7)), blur=3))
    # Si tile
    sk = remap(t, CUE["silikon"] - 0.1, CUE["silikon"] + 0.35) * (1 - remap(t, CUE["kendi"] - 0.3, CUE["kendi"] + 0.3))
    if sk > 0:
        cv.save()
        cv.translate(1560, 330)
        s = ease_out_back(sk)
        cv.scale(s, s)
        cv.drawPath(rrect(-90, -90, 180, 180, 20), fill(hexc(CYAN, 0.4), blur=26))
        cv.drawPath(rrect(-90, -90, 180, 180, 20), fill(0, shader=lin((0, -90), (0, 90), [hexc("#0f3a5e"), hexc("#0a2038")])))
        cv.drawPath(rrect(-90, -90, 180, 180, 20), stroke(hexc(CYAN), 5))
        draw_text(cv, "14", -52, -52, font(30, 800), fill(hexc("#9ff0ff")), align="center")
        draw_text(cv, "Si", 0, 34, font(100, 900), fill(hexc("#ffffff")))
        draw_text(cv, "SİLİKON", 0, 70, font(22, 800), fill(hexc("#9ff0ff")), tracking=4)
        cv.restore()
    # robots multiply
    spawns = [(0, 0, 0.82, CUE["kendi"] + 0.35), (-370, 0, 0.82, CUE["kopya"]), (370, 0, 0.82, CUE["kopya"]),
              (-740, 0, 0.82, CUE["kopya"] + 0.36), (740, 0, 0.82, CUE["kopya"] + 0.36)]
    back = [(-555, -200, 0.5, CUE["yapay"] - 0.2), (-185, -200, 0.5, CUE["yapay"] - 0.1),
            (185, -200, 0.5, CUE["yapay"] - 0.1), (555, -200, 0.5, CUE["yapay"] - 0.2)]
    sup = pulse(t, CUE["super"] + 0.3, 0.5)
    for dx, dy, s, t0 in back + spawns:
        k = ease_out_back(remap(t, t0, t0 + 0.45))
        if k <= 0:
            continue
        cv.save()
        cv.translate(960 + dx, 800 + dy)
        cv.scale(k, k)
        draw_robot(cv, t + dx * 0.01, eye_dx=0.0, eye_dy=0.0, shoulder=60, elbow=-30, mood="neutral", scale=s,
                   rim="#9ff0ff" if sup > 0.3 else CYAN)
        cv.restore()
        ring = remap(t, t0, t0 + 0.5)
        if 0 < ring < 1:
            cv.drawCircle(960 + dx, 800 + dy - 100 * s, 40 + 200 * ring, stroke(hexc(CYAN, 0.7 * (1 - ring)), 5))
    # super intelligence halo
    sk2 = remap(t, CUE["super"], CUE["super"] + 1.2)
    if sk2 > 0:
        for j in range(3):
            r = 150 + 1100 * ease_out(remap(t, CUE["super"] + j * 0.25, CUE["super"] + 1.3 + j * 0.25))
            al = 0.7 * (1 - remap(t, CUE["super"] + j * 0.25, CUE["super"] + 1.3 + j * 0.25))
            cv.drawCircle(960, 700, r, stroke(hexc("#9ff0ff", al), 6, blur=4))
    # captions
    cap(cv, t, "SONRAKİ AŞAMA", 960, 150, CUE["yazar"] + 0.5, "#ffe2b0", 38, a=1 - remap(t, CUE["kurtul"] - 0.2, CUE["kurtul"] + 0.2),
        tracking=8)
    cap(cv, t, "SİLİKON TABANLI · DİJİTAL", 960, 170, CUE["dijital"], "#bff6ff", 36,
        a=1 - remap(t, CUE["kopya"] - 0.1, CUE["kopya"] + 0.2), tracking=6)
    cap(cv, t, "KENDİNİ KOPYALAYAN", 960, 170, CUE["kopya"] + 0.3, "#bff6ff", 40,
        a=1 - remap(t, CUE["super"] - 0.2, CUE["super"] + 0.1), tracking=6)
    if t > CUE["super"] - 0.05:
        draw_text_reveal(cv, "SÜPER ZEKA", 960, 190, font(76, 900), "#ffffff", t - (CUE["super"] - 0.05), stagger=0.04,
                         dur=0.3, tracking=10, glow=1.0)
    gk = remap(t, CUE["gecis"] - 0.1, CUE["gecis"] + 0.5)
    if gk > 0:
        cv.save()
        cv.translate(960, 985)
        cv.scale(ease_out_back(gk), ease_out_back(gk))
        draw_text(cv, "BİYOLOJİ", -270, 18, font(48, 900), fill(hexc(AMBER)), tracking=6)
        ar = skia.Path()
        ar.moveTo(-100, 0)
        ar.lineTo(100, 0)
        draw_glow_path(cv, ar, "#ffffff", 6, a=0.9, glow=8)
        tri = skia.Path()
        tri.moveTo(120, 0)
        tri.lineTo(88, -18)
        tri.lineTo(88, 18)
        tri.close()
        cv.drawPath(tri, fill(hexc("#ffffff")))
        draw_text(cv, "SİLİKON", 290, 18, font(48, 900), fill(hexc(CYAN)), tracking=6)
        cv.restore()


# ===================================================================== SH190 the question
HB190 = (480, 1100)
S190 = 1.5
CHIP190 = (1430, 700)


def orb_pos(p):
    """Cubic bezier head -> chip."""
    P0, P1, P2, P3 = (500, 600), (700, 130), (1250, 130), (CHIP190[0], CHIP190[1] - 90)
    u = 1 - p
    x = u ** 3 * P0[0] + 3 * u * u * p * P1[0] + 3 * u * p * p * P2[0] + p ** 3 * P3[0]
    y = u ** 3 * P0[1] + 3 * u * u * p * P1[1] + 3 * u * p * p * P2[1] + p ** 3 * P3[1]
    return x, y


def sh190(cv, t):
    bg(cv, t, "#0d1126", "#1b1f4a")
    z = lerp(1.0, 1.07, remap(t, T["sh190"], 115.9))
    cv.save()
    Cam(W / 2, H / 2 + 20, z).apply(cv)
    hc = head_c(HB190, S190)
    # warm / cool halves
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((hc[0], 700), 700, [hexc("#ffb347", 0.18), hexc("#ffb347", 0)])))
    pa = remap(t, CUE["dis"], CUE["silikona"] + 0.4)
    gl = ease_in_out(remap(t, CUE["silikona"] + 0.4, CUE["mi"]))
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((CHIP190[0], 700), 700, [hexc(CYAN, 0.18 * (0.2 + gl)), hexc(CYAN, 0)])))
    S3.glass_human(cv, t, HB190, S190, fire=lerp(0.6, 0.15, remap(t, CUE["dis"], 114.0)), a=1.0)
    chip(cv, CHIP190[0], CHIP190[1], 1.15, glow=gl)
    # title
    if t > CUE["dusun"]:
        draw_text_reveal(cv, "İNSANLIĞIN EN BÜYÜK İCADI", 960, 160, font(60, 900), "#ffe2b0", t - (CUE["icat"] - 1.1),
                         stagger=0.035, dur=0.3, tracking=6, a=1 - remap(t, CUE["zekamiz"], CUE["zekamiz"] + 0.5))
    cap(cv, t, "BİYOLOJİ", hc[0], 1040, CUE["dis"] - 0.4, AMBER, 36, tracking=8)
    cap(cv, t, "SİLİKON", CHIP190[0], 1040, CUE["silikona"] - 0.1, CYAN, 36, tracking=8)
    # orb of intelligence
    ok = remap(t, CUE["zekamiz"] - 0.2, CUE["evrimini"] + 0.2)
    if ok > 0 and t < CUE["tasimak"] + 0.6:
        p = ease_in_out(remap(t, CUE["dis"] - 0.1, CUE["tasimak"]))
        x, y = orb_pos(p)
        if p <= 0:
            x, y = hc[0] + 10, hc[1] - 40
            y -= 70 * ease_out(ok)
        col = mixhex(AMBER, CYAN, remap(p, 0.6, 1.0))
        for j in range(14):
            pj = max(0.0, p - j * 0.012)
            tx, ty = orb_pos(pj) if p > 0 else (x, y)
            cv.drawCircle(tx, ty, 26 - j, fill(hexc(col, 0.35 * (1 - j / 14)), blur=10))
        cv.drawCircle(x, y, 58 * ease_out_back(ok) * (1 - 0.7 * remap(t, CUE["tasimak"], CUE["tasimak"] + 0.5)), fill(hexc(col, 0.55), blur=22))
        cv.drawCircle(x, y, 26 * ease_out_back(ok) * (1 - 0.7 * remap(t, CUE["tasimak"], CUE["tasimak"] + 0.5)), fill(hexc("#ffffff")))
    # the big question
    qk = remap(t, CUE["mi"] - 0.05, CUE["mi"] + 0.5)
    if qk > 0:
        cv.save()
        cv.translate(960, 560 - 20 * math.sin(t * 3))
        s = ease_out_back(qk)
        cv.scale(s, s)
        cv.drawCircle(0, -40, 160, fill(hexc("#ffffff", 0.18), blur=40))
        draw_text(cv, "?", 0, 80, font(360, 900), fill(hexc("#ffffff", 0.95)))
        cv.restore()
    cv.restore()


# ===================================================================== SH200 decode the survival codes
HB200 = (960, 1100)


def belt_pos(t):
    """Integrated conveyor offset: accelerates after "daha hızlı", halts at "değil"."""
    x, tt = 0.0, 116.0
    while tt < t:
        v = 90 + 1050 * ease_in(remap(tt, 117.9, 119.6))
        v *= 1 - remap(tt, CUE["degil"], CUE["degil"] + 0.45)
        x += v * 0.02
        tt += 0.02
    return x


def code_stream(cv, t, src, dst, k, seed, col="#ffd59a"):
    rnd = random.Random(seed)
    f = font(26, 800)
    for j in range(7):
        p = ((t * 0.55 + j / 7 + rnd.random() * 0.1) % 1.0)
        x = lerp(src[0], dst[0], p)
        y = lerp(src[1], dst[1], p) - 60 * math.sin(math.pi * p)
        ch = "ACGT01"[(int(t * 6) + j + seed) % 6]
        cv.drawString(ch, x - 8, y + 9, f, fill(hexc(col, k * math.sin(math.pi * p))))


def sh200(cv, t):
    # ---- phase A: faster chips (blueprint) ----
    outA = ease_in_out(remap(t, CUE["degil"] + 0.55, CUE["icimiz"] + 0.2))
    if outA < 1:
        cv.save()
        bg(cv, t, "#071328", "#0e2446")
        for gx in range(0, W, 80):
            cv.drawLine(gx, 0, gx, H, stroke(hexc("#38e1ff", 0.07), 1.5))
        for gy in range(0, H, 80):
            cv.drawLine(0, gy, W, gy, stroke(hexc("#38e1ff", 0.07), 1.5))
        # headline
        words = [("ZEKANIN", 116.18), ("GELECEĞİNİ", 116.54), ("İNŞA", 117.10), ("ETMENİN", 117.42), ("YOLU", 117.94)]
        f = font(58, 900)
        total = sum(f.measureText(w) for w, _ in words) + 24 * (len(words) - 1)
        x = 960 - total / 2
        for w, c in words:
            wd = f.measureText(w)
            if t > c:
                k = remap(t, c, c + 0.3)
                cv.save()
                cv.translate(0, (1 - ease_out(k)) * 22)
                cv.drawString(w, x, 170, f, fill(hexc("#ffffff", k)))
                cv.restore()
            x += wd + 24
        # conveyor
        by = 800
        cv.drawPath(rrect(-40, by, W + 80, 70, 14), fill(hexc("#16264a")))
        cv.drawPath(rrect(-40, by, W + 80, 70, 14), stroke(hexc("#5f78a8"), 4))
        off = belt_pos(t)
        for j in range(30):
            sx = ((j * 64 + off * 0.6) % (W + 128)) - 64
            cv.drawLine(sx, by + 6, sx - 20, by + 64, stroke(hexc("#2d4575"), 4))
        # road line (yolu) draws on above the belt
        rk = remap(t, CUE["yolu"] - 0.6, CUE["hizli"] - 0.1)
        if rk > 0:
            road = skia.Path()
            road.moveTo(120, 420)
            road.cubicTo(500, 300, 900, 560, 1300, 420)
            road.cubicTo(1500, 360, 1650, 400, 1800, 380)
            draw_glow_path(cv, partial_path(road, rk), CYAN, 7, a=0.8, glow=10)
        # chips on the belt
        stop = 1 - remap(t, CUE["degil"], CUE["degil"] + 0.5)
        for j in range(7):
            px = ((j * 330 + off) % (W + 500)) - 250
            if t < CUE["hizli"] - 0.7:
                px = -400
            chip(cv, px, by - 60, 0.42, glow=0.4 + 0.5 * stop, label="Si")
            if t > CUE["hizli"] - 0.7 and stop > 0.1:
                for q in range(4):
                    cv.drawLine(px - 120 - q * 36, by - 80 + q * 12, px - 70 - q * 36 - 40 * remap(t, 118, 119.6), by - 80 + q * 12,
                                stroke(hexc(CYAN, 0.35 * stop * (1 - q / 4)), 3))
        # label + cross
        lab_a = 1 - 0.55 * remap(t, CUE["degil"], CUE["degil"] + 0.3)
        cap(cv, t, "DAHA HIZLI ÇİPLER", 960, 330, CUE["hizli"], "#bff6ff", 76, a=lab_a, tracking=8, weight=900, stagger=0.03)
        xk = remap(t, CUE["degil"] - 0.05, CUE["degil"] + 0.3)
        if xk > 0:
            cv.save()
            cv.translate(960, 560)
            s = ease_out_back(xk)
            cv.scale(s, s)
            cv.drawCircle(0, 0, 150, fill(hexc(RED, 0.3), blur=28))
            cv.drawLine(-110, -110, 110, 110, stroke(hexc(RED), 28))
            cv.drawLine(-110, 110, 110, -110, stroke(hexc(RED), 28))
            cv.restore()
        cv.restore()
    # ---- phase B: decode the codes inside us ----
    inA = ease_in_out(remap(t, CUE["degil"] + 0.55, CUE["icimiz"] + 0.2))
    if inA > 0:
        cv.save()
        cv.saveLayerAlpha(None, int(255 * inA))
        bg(cv, t, "#0d1126", "#241f3f")
        hc = head_c(HB200, S170)
        cv.drawCircle(hc[0], hc[1], 520, fill(0, shader=rad((hc[0], hc[1]), 520, [hexc(AMBER, 0.20), hexc(AMBER, 0)])))
        S3.glass_human(cv, t, HB200, S170, fire=0.55 + 0.35 * pulse(t, CUE["kodlarini"], 1.0), a=1.0)
        # fossils appear in turn ("milyarlarca yıllık")
        spots = [("ammonite", (330, 420), CUE["milyarlarca"] + 0.15), ("trilobite", (1590, 470), CUE["milyarlarca"] + 0.6),
                 ("fish", (300, 820), CUE["evrimsel"]), ("worm", (1610, 840), CUE["evrimsel"] + 0.4)]
        for j, (kind, pos, c) in enumerate(spots):
            k = ease_out_back(remap(t, c, c + 0.4))
            if k <= 0:
                continue
            cv.save()
            cv.translate(*pos)
            cv.scale(k, k)
            cv.drawCircle(0, 0, 110, fill(hexc(AMBER, 0.20), blur=26))
            glow_v = pulse(t, c + 0.2, 0.5)
            if kind == "ammonite":
                draw_ammonite(cv, 70, glow=glow_v)
            elif kind == "trilobite":
                draw_trilobite(cv, 1.2, glow=glow_v)
            elif kind == "fish":
                draw_fish_fossil(cv, 1.2, glow=glow_v)
            else:
                draw_worm_trace(cv, 1.3)
            cv.restore()
            # tether + code stream to the brain
            tk = remap(t, CUE["hayatta"] + 0.2 + j * 0.1, CUE["hayatta"] + 0.8 + j * 0.1)
            if tk > 0:
                tet = skia.Path()
                tet.moveTo(pos[0], pos[1])
                tet.quadTo((pos[0] + hc[0]) / 2, min(pos[1], hc[1]) - 160, hc[0], hc[1] - 20)
                draw_glow_path(cv, partial_path(tet, tk), AMBER, 3, a=0.45, glow=8)
            ck = remap(t, CUE["kodlarini"] - 0.1 + j * 0.05, CUE["kodlarini"] + 0.4)
            if ck > 0:
                code_stream(cv, t, pos, (hc[0], hc[1] - 20), ck * (1 - 0.6 * remap(t, CUE["cozmek"], 125.0)), j + 3)
        cap(cv, t, "MİLYARLARCA YILLIK EVRİM", 960, 150, CUE["milyarlarca"], "#ffe2b0", 46, tracking=6)
        cap(cv, t, "HAYATTA KALMA KODLARI", 960, 1030, CUE["hayatta"], AMBER, 46, tracking=8, weight=900)
        # the lock from the very first scene opens
        lk = remap(t, CUE["cozmek"] - 0.35, CUE["cozmek"] + 0.05)
        if lk > 0:
            cv.save()
            cv.translate(hc[0] + 20, hc[1] - 20)
            S1.lock(cv, t, lk, remap(t, CUE["cozmek"] + 0.15, CUE["geciyor"] - 0.1))
            cv.restore()
        bk = remap(t, CUE["geciyor"] - 0.1, CUE["geciyor"] + 0.2)
        fl = pulse(t, CUE["geciyor"] + 0.15, 0.5)
        if fl > 0:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((hc[0], hc[1]), 1100, [hexc("#fff4d6", 0.7 * fl),
                                                                                           hexc("#ffd59a", 0)])))
            for j in range(40):
                rnd = random.Random(j + 9)
                a = rnd.uniform(0, math.tau)
                d = ease_out(remap(t, CUE["geciyor"], CUE["geciyor"] + 0.9)) * rnd.uniform(150, 800)
                cv.drawCircle(hc[0] + math.cos(a) * d, hc[1] + math.sin(a) * d, rnd.uniform(2, 6),
                              fill(hexc("#ffe2b0", 1 - remap(t, CUE["geciyor"], CUE["geciyor"] + 1.0)), blur=3))
        cv.restore()
    # ---- outro: fade to the title card ----
    ok = ease_in_out(remap(t, 125.15, 126.0))
    if ok > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#070a1c", ok)))
        tk = t - 126.1
        if tk > 0:
            fo = 1 - remap(t, 127.0, 127.4)
            draw_text_reveal(cv, "ZEKANIN KISA TARİHİ", 960, 520, font(110, 900), "#ffffff", tk, stagger=0.05, dur=0.35,
                             tracking=10, a=fo, glow=1.0)
            sub = remap(t, 126.6, 127.0) * fo
            if sub > 0:
                draw_text(cv, "Max Bennett", 960, 610, font(42, 600), fill(hexc("#ffb347", sub)), tracking=8)


# ===================================================================== DISPATCH
def shot_of(t):
    if t < T["sh160"]:
        return -1
    if t < T["sh170"]:
        return 0
    if t < T["sh180"]:
        return 1
    if t < T["sh190"]:
        return 2
    if t < T["sh200"]:
        return 3
    return 4


SHOTS = [sh160, sh170, sh180, sh190, sh200]


def render(cv, t):
    i = shot_of(t)
    if i < 0:  # hold SC03's last frame while the narrator takes a breath
        S3.sh150(cv, t)
        return
    if i > 0:
        tt = (T["sh170"], T["sh180"], T["sh190"], T["sh200"])[i - 1]
        k = remap(t, tt, tt + XF)
        if k < 1:  # dip through the night colour: two busy shots never overlap
            if k < 0.5:
                SHOTS[i - 1](cv, t)
                cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#070a1c", ease_in_out(2 * k))))
            else:
                SHOTS[i](cv, t)
                cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#070a1c", ease_in_out(2 * (1 - k)))))
            return
    SHOTS[i](cv, t)
    if i == 0:
        glitch(cv, t, 0.9 * (1 - remap(t, T["sh160"], T["sh160"] + 0.3)), seed=10)


if __name__ == "__main__":
    import argparse

    from PIL import Image

    from fm_2d.core import Finisher, new_surface, snapshot

    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--out", default=str(ROOT / "projects/zeka_tarihi/11_render/SC04"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fin = Finisher()
    surf = new_surface()
    for ts in a.still or []:
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        render(cv, ts)
        Image.fromarray(fin(snapshot(surf), int(ts * FPS))).save(out / f"still_{ts:06.2f}.png")
        print("wrote", ts)
