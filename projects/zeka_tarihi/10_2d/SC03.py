"""SC03 - Catastrophic forgetting (51.80-83.90). Continues SC02's museum frame (robot + "EVET!").

Shots (word cues from references/voice/words.json):
  SH100 51.80-58.30 push in on the robot; weak point (warning) -> "FELAKETSEL UNUTMA" glitch title
  SH110 58.30-65.35 split: human memory stacks new cards on old ones; the AI's single memory slot is
                    overwritten ("eskisinin üzerine yazıyor") and the old card disintegrates
  SH120 65.35-68.60 launch stage ("piyasaya sürüldükleri an"): confetti, v1.0 tag -> ice grows over the robot
                    ("öğrenmeleri donduruluyor")
  SH130 68.60-73.45 back in SC01's kitchen: the robot tries to imagine a plate falling; its physics
                    simulation breaks ("dünyayı fiziksel olarak simüle edemiyorlar"). The narration's TV
                    reference is not depicted (third-party character); our own robot carries the beat.
  SH140 73.45-77.80 frozen genius: robot in ice, a clock that stops ("zamanda donup kalmış dahiler")
  SH150 77.80-83.90 human glass head with an inner world simulation, loop + ✗/✓ learning; the frozen robot
                    lacks it ("yoksunlar") - ends on the pair, ready for SC04 (the sixth breakthrough)
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

from fm_2d.assets import (STAGE_COLS, bubble, draw_card, draw_chat_window, draw_clock, draw_dishwasher,  # noqa: E402
                          draw_human, draw_ice_block, draw_plate, draw_robot, snowflake)
from fm_2d.core import (FPS, H, W, Cam, Dust, clamp, draw_glow_path, draw_text, draw_text_reveal,  # noqa: E402
                        ease_in, ease_in_out, ease_out, ease_out_back, fill, font, glitch, glow_circle, hexc, lerp,
                        lin, partial_path, pulse, rad, remap, rrect, shake, smooth, stroke)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S2 = _load("SC02")
S1 = S2.S1

START = 1554 / FPS  # SC02 ends at 51.80
DURATION = 83.90    # "Son olarak" (SC04) starts at ~84.3

CUE = dict(ikinci=51.85, yapay=52.70, meshur=53.78, zayif=54.12, nokta=54.42, felaket=55.68, unutma=56.42,
           yuz=57.20, bizler=58.42, miras=59.36, durmadan=59.90, ogrenir=60.30, chat=61.08, sistem=62.08,
           yeni=62.78, ogrendi=63.26, eski=63.80, uzerine=64.30, yaziyor=64.66, iste=65.42, piyasa=66.02,
           surul=66.46, ogrenme=67.22, dondur=67.82, tipki=68.96, robot=69.90, dunya=71.00, fizik=71.44,
           simul=72.12, demek=73.52, bugun=73.96, yapay2=74.26, aslinda=75.82, zaman=76.32, donup=76.62,
           kalmis=76.98, dahi=77.30, cunku=77.86, bizim=78.26, icsel=78.70, dunya2=79.28, simulasyon=79.50,
           kurarak=80.14, surekli=80.64, hata=81.54, yaparak=81.84, ogrenme2=82.18, yetenek=82.58,
           yoksun=83.12)
T = dict(sh110=58.30, sh120=65.35, sh130=68.60, sh140=73.45, sh150=77.80)

STARS = S1.STARS


def bg(cv, t, top="#0b1026", bottom="#1b1f4a"):
    S1.background(cv, t, top, bottom)


# ===================================================================== SH100 museum -> robot close-up
_orig_cam_m = S2.cam_m
ROBOT_W = (1880, 1660)


def cam_100(t):
    c = _orig_cam_m(min(t, 51.8))
    a = ease_in_out(remap(t, 52.1, 54.0))
    x, y, z = lerp(c.x, ROBOT_W[0] - 120, a), lerp(c.y, ROBOT_W[1] - 560, a), lerp(c.zoom, 1.25, a)
    # glitch push
    z *= 1 + 0.08 * ease_in(remap(t, CUE["felaket"] - 0.2, 57.6))
    return Cam(x, y, z)


S2.cam_m = cam_100
S2.EVET_ALPHA = lambda t: 1 - remap(t, 51.95, 52.45)


def robot_100(cv, t):
    """Replaces SC02.robot_visit for SC03 (same robot, same place, new acting)."""
    rx, ry = ROBOT_W
    turn = smooth(remap(t, 52.4, 52.9))
    gl = remap(t, CUE["felaket"], CUE["felaket"] + 0.2) * (1 - remap(t, 57.4, 58.0))
    blink = pulse(t, 52.6, 0.07) + (0.8 * (math.sin(t * 37) > 0.4) * gl)
    cv.save()
    cv.translate(rx, ry)
    cv.scale(-1, 1)
    draw_robot(cv, t, eye_dx=lerp(1.0, -0.3, turn) + (math.sin(t * 29) * 0.8 * gl), eye_dy=lerp(-0.4, 0.2, turn),
               blink=blink, head_tilt=lerp(0, 6, turn) + 3 * math.sin(t * 31) * gl,
               shoulder=80, elbow=-20, mood="confused" if t > CUE["zayif"] else "neutral", scale=1.7,
               rim="#ff5c6c" if (gl > 0 and math.sin(t * 13) > 0) else "#38e1ff")
    cv.restore()
    # weak point: warning badge
    wk = remap(t, CUE["zayif"] - 0.1, CUE["zayif"] + 0.25) * (1 - remap(t, CUE["felaket"] - 0.1, CUE["felaket"] + 0.2))
    if wk > 0:
        cv.save()
        cv.translate(rx - 420, ry - 820)
        s = ease_out_back(wk)
        cv.scale(s, s)
        tri = skia.Path()
        tri.moveTo(0, -80)
        tri.lineTo(80, 60)
        tri.lineTo(-80, 60)
        tri.close()
        cv.drawPath(tri, fill(hexc("#ffd34d", 0.5), blur=16))
        cv.drawPath(tri, fill(hexc("#ffd34d")))
        cv.drawPath(tri, stroke(hexc("#2b2147"), 6))
        draw_text(cv, "!", 0, 44, font(96, 900), fill(hexc("#2b2147")))
        cv.restore()
        draw_text_reveal(cv, "ZAYIF NOKTA", rx - 420, ry - 680, font(44, 900), "#ffd34d", t - CUE["zayif"],
                         tracking=6, stagger=0.03, dur=0.25, a=1 - remap(t, CUE["felaket"] - 0.1, CUE["felaket"] + 0.2))


S2.robot_visit = robot_100


def sh100(cv, t):
    S2.head_scene(cv, t, 1.0)
    # chest-light/visor "error" scanlines handled by glitch; title
    gk = remap(t, CUE["felaket"] - 0.05, CUE["felaket"] + 0.2)
    if gk > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(hexc("#0b1026", 0.45 * gk)))
        f = font(120, 900)
        a = 1 - remap(t, 57.9, 58.3)
        for line, y, cue in (("FELAKETSEL", 470, CUE["felaket"]), ("UNUTMA", 610, CUE["unutma"])):
            if t > cue - 0.05:
                k = remap(t, cue - 0.05, cue + 0.15)
                jx = (random.Random(int(t * 30) + y).uniform(-14, 14)) * (1 - k * 0.7)
                for col, dx in (("#ff2e63", -6), ("#38e1ff", 6)):
                    draw_text(cv, line, W / 2 + dx + jx, y, f, fill(hexc(col, 0.55 * a * k)), tracking=10)
                draw_text(cv, line, W / 2 + jx, y, f, fill(hexc("#ffffff", a * k)), tracking=10)
    g = 0.25 * pulse(t, CUE["felaket"], 0.25) + 0.35 * pulse(t, CUE["unutma"], 0.25) + 0.15 * remap(
        t, CUE["unutma"], 57.6) * (0.5 + 0.5 * math.sin(t * 23)) + 0.9 * remap(t, 57.85, 58.3)
    glitch(cv, t, g, seed=1)


# ===================================================================== SH110 memory: stack vs overwrite
HUM = (420, 1080, 1.15)       # bust origin + scale (faces right)
ROB = (1290, 1000, 1.0)       # robot (faces right)
HBOX = (640, 360, 300, 640)   # x, top, w, h of the human memory box
RBOX = (1560, 360, 300, 640)
HUM_CARDS = [("Elma", "apple", 59.95), ("Bisiklet", "bike", 60.35), ("Kedi", "cat", 60.75), ("Müzik", "music", 61.15),
             ("Güneş", "sun", 61.55)]
ROB_CARDS = [("Elma", "apple", 61.9), ("Bisiklet", "bike", 63.35)]


def brain_in_bust(cv, bust, s):
    hx = bust[0] + 6 * s - 8 * s / 1.9
    hy = bust[1] - (96 + 168) * s + 30 * s / 1.9
    cv.translate(hx, hy)
    k = 0.48 * s / 1.9
    cv.scale(-k, k)


def glass_human(cv, t, bust, s, tints=(1, 1, 1, 1, 1), fire=0.6, a=1.0, inner=None):
    cv.save()
    cv.translate(*bust)
    draw_human(cv, t, s, glass=True, a=a)
    cv.restore()
    cv.save()
    brain_in_bust(cv, bust, s)
    cv.saveLayerAlpha(None, int(255 * a))
    S2.draw_layered_brain(cv, t, [0] * 5, list(tints), fire, glow=0.6)
    cv.restore()
    cv.restore()


def memory_box(cv, box, label, col, a=1.0):
    x, top, w, h = box
    cv.drawPath(rrect(x, top, w, h, 24), fill(hexc(col, 0.06 * a)))
    p = stroke(hexc(col, 0.7 * a), 4)
    p.setPathEffect(skia.DashPathEffect.Make([18, 12], 0))
    cv.drawPath(rrect(x, top, w, h, 24), p)
    draw_text(cv, label, x + w / 2, top + h + 46, font(30, 800), fill(hexc(col, a)), tracking=4)


def fly_card(cv, t, label, icon, t0, start, end, rot0=-20, rot1=0, s=1.0, dur=0.45):
    k = remap(t, t0, t0 + dur)
    if k <= 0:
        return False
    e = ease_out(k)
    x = lerp(start[0], end[0], e)
    y = lerp(start[1], end[1], e) - math.sin(math.pi * k) * 120
    cv.save()
    cv.translate(x, y)
    cv.rotate(lerp(rot0, rot1, e))
    draw_card(cv, label, icon, s)
    cv.restore()
    return k >= 1


def disintegrate(cv, t, label, icon, t0, pos, s=1.0):
    """Old card shatters into pixels after t0."""
    if t < t0:
        cv.save()
        cv.translate(*pos)
        draw_card(cv, label, icon, s)
        cv.restore()
        return
    dt = t - t0
    if dt > 1.4:
        return
    surf = skia.Surface(220, 150)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.translate(110, 76)
    draw_card(c, label, icon, 1.0)
    img = surf.makeImageSnapshot()
    rnd = random.Random(hash(label) & 0xFFFF)
    cell = 14
    for gy in range(0, 150, cell):
        for gx in range(0, 220, cell):
            d = rnd.uniform(0, 0.35) + gx / 220 * 0.3
            k = clamp((dt - d) / 0.9)
            vx, vy = rnd.uniform(40, 220), rnd.uniform(-160, -20)
            px = pos[0] + (gx - 110) * s + vx * k
            py = pos[1] + (gy - 76) * s + vy * k + 380 * k * k
            a = 1 - k
            if a <= 0:
                continue
            p = skia.Paint(AntiAlias=False)
            p.setAlphaf(a)
            dst = skia.Rect.MakeXYWH(px, py, cell * s * (1 - 0.4 * k), cell * s * (1 - 0.4 * k))
            cv.drawImageRect(img, skia.Rect.MakeXYWH(gx, gy, cell, cell), dst, skia.SamplingOptions(), p)
            if k > 0.05 and rnd.random() < 0.15:
                cv.drawRect(dst, fill(hexc("#38e1ff", 0.5 * a)))


def sh110(cv, t):
    bg(cv, t)
    intro = ease_out(remap(t, T["sh110"], T["sh110"] + 0.6))
    cv.save()
    Cam(W / 2, H / 2 + 20, 1.0 + 0.02 * remap(t, T["sh110"], T["sh120"])).apply(cv)
    # divider
    cv.drawLine(W / 2, 80, W / 2, 80 + 920 * intro, stroke(hexc("#ffffff", 0.15), 3))
    # headers
    hf = font(46, 900)
    la = remap(t, CUE["bizler"] - 0.1, CUE["bizler"] + 0.3)
    ra = remap(t, CUE["chat"] - 0.1, CUE["chat"] + 0.3)
    draw_text(cv, "İNSAN", W / 4, 150, hf, fill(hexc("#ffb347", la)), tracking=8)
    draw_text(cv, "YAPAY ZEKA", 3 * W / 4, 150, hf, fill(hexc("#38e1ff", ra)), tracking=8)
    draw_text(cv, "durmadan öğrenir, üstüne ekler", W / 4, 200, font(28, 500), fill(hexc("#ffe2b0", la * 0.9)))
    draw_text(cv, "yeni bilgi eskisinin üzerine yazılır", 3 * W / 4, 200, font(28, 500),
              fill(hexc("#bff6ff", remap(t, CUE["eski"], CUE["eski"] + 0.4) * 0.9)))
    # LEFT: human
    if la > 0:
        cv.saveLayerAlpha(None, int(255 * la))
        cv.save()
        cv.translate(-200 * (1 - ease_out(la)), 0)
        tints = [ease_out(remap(t, CUE["miras"] + i * 0.1, CUE["miras"] + 0.3 + i * 0.1)) for i in range(5)]
        glass_human(cv, t, HUM[:2], HUM[2], tints, fire=0.4 + 0.6 * remap(t, CUE["durmadan"], CUE["durmadan"] + 0.4))
        memory_box(cv, HBOX, "HAFIZA", "#ffb347")
        for i, (lab, ic, c) in enumerate(HUM_CARDS):
            end = (HBOX[0] + HBOX[2] / 2 + (8 if i % 2 else -8), HBOX[1] + HBOX[3] - 90 - i * 105)
            if fly_card(cv, t, lab, ic, c, (HBOX[0] - 400, -100), end, rot0=-25, rot1=(3 if i % 2 else -3), s=1.1):
                pk = pulse(t, c + 0.48, 0.12)
                if pk > 0:
                    glow_circle(cv, end[0], end[1], 160, "#5be38a", 0.5 * pk)
                    draw_text(cv, "+", end[0] + 140, end[1] + 16, font(64, 900), fill(hexc("#5be38a", pk)))
        cv.restore()
        cv.restore()
    # RIGHT: AI
    if ra > 0:
        cv.saveLayerAlpha(None, int(255 * ra))
        cv.save()
        cv.translate(200 * (1 - ease_out(ra)), 0)
        cv.save()
        cv.translate(1250, 390)
        draw_chat_window(cv, 380, 230, t, lines=3)
        cv.restore()
        draw_text(cv, "ChatGPT gibi sistemler", 1250, 548, font(26, 700), fill(hexc("#bff6ff", 0.85)))
        cv.save()
        cv.translate(ROB[0], ROB[1])
        over = remap(t, CUE["eski"] - 0.05, CUE["eski"] + 0.2)
        draw_robot(cv, t, eye_dx=0.8, eye_dy=0.2, blink=pulse(t, 61.6, 0.07), shoulder=-10, elbow=-40,
                   mood="confused" if over > 0 else "neutral", scale=ROB[2] * 0.9)
        cv.restore()
        memory_box(cv, RBOX, "HAFIZA", "#38e1ff")
        slot = (RBOX[0] + RBOX[2] / 2, RBOX[1] + RBOX[3] - 110)
        # card 1 arrives; card 2 overwrites it at "eskisinin üzerine"; card 3 again at the end
        c1, c2 = ROB_CARDS
        t_hit2 = c2[2] + 0.45  # lands on "üzerine"
        if t < t_hit2:
            fly_card(cv, t, c1[0], c1[1], c1[2], (RBOX[0] + 500, -100), slot, rot0=25, rot1=0, s=1.1)
        else:
            disintegrate(cv, t, c1[0], c1[1], t_hit2, (slot[0] + 30, slot[1] + 10), 1.1)
        fly_card(cv, t, c2[0], c2[1], c2[2], (RBOX[0] + 500, -100), slot, rot0=25, rot1=0, s=1.1)
        pk = pulse(t, t_hit2, 0.15)
        if pk > 0:
            glow_circle(cv, slot[0], slot[1], 200, "#ff5c6c", 0.6 * pk)
        sk = remap(t, CUE["yaziyor"] - 0.1, CUE["yaziyor"] + 0.2)
        if sk > 0:
            cv.save()
            cv.translate(slot[0], slot[1] - 200)
            cv.rotate(-8)
            s = lerp(1.6, 1, ease_out(sk))
            cv.scale(s, s)
            cv.drawPath(rrect(-170, -40, 340, 72, 14), stroke(hexc("#ff5c6c", sk), 6))
            draw_text(cv, "ÜZERİNE YAZILDI", 0, 12, font(32, 900), fill(hexc("#ff5c6c", sk)), tracking=2)
            cv.restore()
        cv.restore()
        cv.restore()
    cv.restore()
    # transition out: zoom into the robot
    g = 0.7 * remap(t, T["sh120"] - 0.3, T["sh120"])
    glitch(cv, t, g, seed=3)


# ===================================================================== SH120 launch -> freeze
CONF = [(random.Random(i).uniform(-900, 900), random.Random(i + 99).uniform(-700, -200),
         random.Random(i + 7).choice(["#ff7a6b", "#ffb347", "#38e1ff", "#b48bff", "#5be38a"]),
         random.Random(i + 3).uniform(0, 6.28)) for i in range(90)]


def frozen_robot(cv, t, x, y, s, ice_k, eyes_frozen, t_freeze, extra_mood="neutral"):
    blink = 0 if eyes_frozen else pulse(t, t_freeze - 1.2, 0.07)
    tt = min(t, t_freeze) if eyes_frozen else t  # motion stops when frozen
    cv.save()
    cv.translate(x, y)
    draw_robot(cv, tt, eye_dx=0.0, eye_dy=0.0, blink=blink, shoulder=60, elbow=-50, mood=extra_mood, scale=s,
               rim="#9fe8ff" if eyes_frozen else "#38e1ff", bob=not eyes_frozen)
    cv.restore()
    draw_ice_block(cv, x - 175 * s, y + 20, 350 * s, 560 * s, ice_k, seed=4)


def sh120(cv, t):
    bg(cv, t, "#0d1230", "#23285a")
    z = 1.0 + 0.05 * ease_in_out(remap(t, T["sh120"], T["sh130"]))
    cv.save()
    Cam(W / 2, H / 2, z).apply(cv)
    # stage + spotlight
    cone = skia.Path()
    cone.moveTo(W / 2 - 90, -50)
    cone.lineTo(W / 2 + 90, -50)
    cone.lineTo(W / 2 + 520, 900)
    cone.lineTo(W / 2 - 520, 900)
    cone.close()
    cv.drawPath(cone, fill(0, shader=lin((0, -50), (0, 900), [hexc("#e9fbff", 0.22), hexc("#e9fbff", 0.03)])))
    cv.drawOval(skia.Rect.MakeXYWH(W / 2 - 420, 860, 840, 90), fill(hexc("#3a4570")))
    cv.drawOval(skia.Rect.MakeXYWH(W / 2 - 420, 850, 840, 80), fill(0, shader=lin((0, 850), (0, 930), [
        hexc("#5a6699"), hexc("#2b3570")])))
    ice = ease_out(remap(t, CUE["ogrenme"] + 0.1, CUE["dondur"] + 0.6))
    frozen = t > CUE["dondur"] + 0.3
    frozen_robot(cv, t, W / 2, 880, 1.05, ice, frozen, CUE["dondur"] + 0.3)
    # v1.0 tag
    tk = remap(t, CUE["piyasa"] - 0.1, CUE["piyasa"] + 0.3)
    if tk > 0:
        cv.save()
        cv.translate(W / 2 + 330, 470)
        cv.rotate(8 + 3 * math.sin(t * 2))
        s = ease_out_back(tk)
        cv.scale(s, s)
        cv.drawLine(-110, -40, -190, -60, stroke(hexc("#ffe2b0"), 3))
        cv.drawPath(rrect(-110, -60, 230, 120, 16), fill(hexc("#ffb347")))
        cv.drawCircle(-90, -40, 8, fill(hexc("#0b1026")))
        draw_text(cv, "v1.0", 10, -2, font(48, 900), fill(hexc("#2b2147")))
        draw_text(cv, "YAYINDA", 10, 38, font(24, 800), fill(hexc("#2b2147")), tracking=3)
        cv.restore()
    # confetti on release
    ck = t - CUE["surul"]
    if 0 < ck < 2.2:
        for (dx, vy, col, ph) in CONF:
            x = W / 2 + dx * ease_out(min(1, ck * 1.4)) + math.sin(ck * 4 + ph) * 20
            y = 300 + vy * ease_out(min(1, ck * 1.6)) + 260 * ck * ck
            a = clamp(1.6 - ck * 0.8)
            cv.save()
            cv.translate(x, y)
            cv.rotate(ph * 60 + ck * 400)
            cv.drawRect(skia.Rect.MakeXYWH(-6, -10, 12, 20), fill(hexc(col, a)))
            cv.restore()
    cv.restore()
    # frost overlay + snowflake + label
    fk = remap(t, CUE["dondur"] - 0.1, CUE["dondur"] + 0.6)
    if fk > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((W / 2, H / 2), 1200, [hexc("#e9fbff", 0),
                                                                                    hexc("#bff6ff", 0.35 * fk)],
                                                                  [0.45, 1])))
        snowflake(cv, 330, 300, 90 * ease_out_back(fk), fk)
        draw_text_reveal(cv, "ÖĞRENME", 330, 470, font(56, 900), "#e9fbff", t - CUE["dondur"], tracking=6,
                         stagger=0.03, dur=0.25)
        draw_text_reveal(cv, "DONDURULDU", 330, 535, font(56, 900), "#9fe8ff", t - CUE["dondur"] - 0.2,
                         tracking=6, stagger=0.03, dur=0.25)
        # learning meter dropping
    mk = 1 - ease_in_out(remap(t, CUE["ogrenme"], CUE["dondur"] + 0.4))
    cv.drawPath(rrect(1560, 300, 60, 420, 30), stroke(hexc("#cfd8ff", 0.6), 4))
    cv.drawPath(rrect(1568, 308 + 404 * (1 - mk), 44, max(4, 404 * mk), 22), fill(hexc(
        "#5be38a" if mk > 0.4 else "#ff5c6c")))
    draw_text(cv, "öğrenme", 1590, 770, font(26, 700), fill(hexc("#cfd8ff", 0.8)))
    gl = 0.6 * remap(t, T["sh130"] - 0.3, T["sh130"])
    glitch(cv, t, gl, seed=5)


# ===================================================================== SH130 kitchen: broken simulation
def sh130(cv, t):
    cv.drawImage(S1.kitchen_image(), 0, 0)
    cv.save()
    Cam(W / 2 + 120, H / 2 - 20, 1.08 + 0.05 * ease_in_out(remap(t, T["sh130"], T["sh140"]))).apply(cv)
    draw_dishwasher(cv, **S1.DW, plates=(0, 1, 2, 3, 4, 5))
    rx, ry = 1205, 870
    thinking = remap(t, CUE["robot"] - 0.4, CUE["robot"])
    err = t > CUE["simul"] + 0.1
    cv.save()
    cv.translate(rx, ry)
    cv.scale(-1, 1)
    draw_robot(cv, t, eye_dx=-0.6, eye_dy=-0.8 * thinking, blink=pulse(t, 69.2, 0.07), head_tilt=-6 * thinking,
               shoulder=60, elbow=-30, mood="confused" if err else "neutral", scale=S1.ROBOT_S,
               hold=lambda c: (c.save(), c.rotate(-30), draw_plate(c, 64), c.restore()))
    cv.restore()
    # thought bubble with a tiny physics sim
    bk = remap(t, CUE["tipki"] - 0.2, CUE["tipki"] + 0.3)
    bx, by, bw, bh = 820, 230, 560, 330
    if bk > 0:
        bubble(cv, bx, by, bw, bh, bk, col="#e9eef8", tail=(0.55, 0.85))
        if bk >= 1:
            cv.save()
            clip = rrect(bx - bw / 2 + 20, by - bh / 2 + 20, bw - 40, bh - 40, 40)
            cv.clipPath(clip, doAntiAlias=True)
            # grid "simulation" floor
            for i in range(-6, 7):
                cv.drawLine(bx + i * 40, by + 90, bx + i * 70, by + 160, stroke(hexc("#9aa6c0", 0.4), 2))
            cv.drawLine(bx - 260, by + 90, bx + 260, by + 90, stroke(hexc("#6b7690"), 3))
            # table
            cv.drawRect(skia.Rect.MakeXYWH(bx - 180, by + 10, 200, 14), fill(hexc("#8b7bff")))
            cv.drawRect(skia.Rect.MakeXYWH(bx - 170, by + 24, 12, 66), fill(hexc("#6a5ce0")))
            cv.drawRect(skia.Rect.MakeXYWH(bx + 2, by + 24, 12, 66), fill(hexc("#6a5ce0")))
            # imagined plate: first falls normally, then glitches through the floor / floats up
            st = t - (CUE["dunya"] - 0.2)
            if st > 0:
                if st < 0.6:
                    px, py = bx + 60 + st * 120, by - 80 + 0.5 * 900 * st * st
                elif not err:
                    px, py = bx + 132, by + 82 + 30 * math.sin(st * 9)  # jitters on the floor line
                else:
                    et = t - CUE["simul"] - 0.1
                    px, py = bx + 132 + math.sin(et * 50) * 14, by + 82 - 140 * ease_out(min(1, et * 0.8))
                cv.save()
                cv.translate(px, py)
                cv.rotate(st * 220)
                cv.scale(0.55, 0.55)
                draw_plate(cv, 64)
                cv.restore()
                if err and int(t * 12) % 2 == 0:
                    cv.save()
                    cv.translate(px + 14, py)
                    cv.scale(0.55, 0.55)
                    cv.saveLayerAlpha(None, 110)
                    draw_plate(cv, 64, tint="#ff5c6c")
                    cv.restore()
                    cv.restore()
            if err:
                ek = remap(t, CUE["simul"] + 0.1, CUE["simul"] + 0.35)
                cv.drawRect(skia.Rect.MakeXYWH(bx - bw / 2, by - bh / 2, bw, bh), fill(hexc("#ff5c6c", 0.12 * ek)))
                cv.save()
                cv.translate(bx, by - 100)
                cv.scale(ease_out_back(ek), ease_out_back(ek))
                cv.drawPath(rrect(-230, -36, 460, 64, 12), fill(hexc("#ff5c6c")))
                draw_text(cv, "SİMÜLASYON HATASI", 0, 10, font(32, 900), fill(hexc("#ffffff")), tracking=2)
                cv.restore()
            cv.restore()
    cv.restore()
    lab = remap(t, CUE["fizik"] - 0.1, CUE["fizik"] + 0.3) * (1 - remap(t, T["sh140"] - 0.4, T["sh140"]))
    if lab > 0:
        draw_text_reveal(cv, "fiziksel dünyayı simüle edemez", W / 2, 1010, font(40, 700), "#ffe2b0",
                         t - CUE["fizik"] + 0.1, stagger=0.015, dur=0.25, a=lab)
    g = 0.3 * pulse(t, CUE["simul"] + 0.12, 0.2) + 0.8 * remap(t, T["sh140"] - 0.3, T["sh140"])
    glitch(cv, t, g, seed=7)


# ===================================================================== SH140 frozen genius + clock
def clock_angles(t):
    stop = CUE["donup"] + 0.15
    tt = min(t, stop)
    slow = 1 - remap(t, CUE["zaman"], stop)  # it slows down before it stops
    m = (tt - T["sh140"]) * 260 * (0.3 + 0.7 * slow) + 50
    return m, m / 12 + 300


def sh140(cv, t, cam_x=None, robot=True, bg_on=True):
    if bg_on:
        bg(cv, t, "#0b1430", "#16244a")
    cx = cam_x if cam_x is not None else W / 2
    cv.save()
    Cam(cx, H / 2, 1.0 + 0.04 * ease_in_out(remap(t, T["sh140"], T["sh150"]))).apply(cv)
    fr = remap(t, CUE["donup"], CUE["donup"] + 0.6)
    # big clock behind
    cv.save()
    cv.translate(W / 2 + 330, 430)
    m, h = clock_angles(t)
    draw_clock(cv, 230, m, h, frost=fr)
    cv.restore()
    # frozen robot (already frozen since SH120)
    if robot:
        frozen_robot(cv, t, W / 2 - 300, 930, 1.0, 1.0, True, CUE["dondur"] + 0.3)
    # genius halo over the ice
    dk = remap(t, CUE["dahi"] - 0.1, CUE["dahi"] + 0.4)
    if dk > 0:
        gx, gy = W / 2 - 300, 360
        glow_circle(cv, gx, gy, 160, "#ffd34d", 0.5 * dk)
        for k in range(10):
            a = k * math.tau / 10 + t * 0.4
            r0, r1 = 70, 70 + 40 * ease_out(dk)
            cv.drawLine(gx + math.cos(a) * r0, gy + math.sin(a) * r0, gx + math.cos(a) * r1, gy + math.sin(a) * r1,
                        stroke(hexc("#ffd34d", dk), 6))
        cv.save()
        cv.translate(gx, gy)
        cv.scale(0.22 * ease_out_back(dk), 0.22 * ease_out_back(dk))
        S2.brain_comp(cv, t, 0.3)
        cv.restore()
        for k in range(5):
            snowflake(cv, gx - 120 + k * 60, gy + 110 + (k % 2) * 20, 14, dk * 0.9)
    cv.restore()
    # kinetic text
    if t > CUE["zaman"] - 0.1:
        draw_text_reveal(cv, "ZAMANDA DONUP KALMIŞ", 1340, 820, font(54, 900), "#e9fbff",
                         t - (CUE["zaman"] - 0.1), tracking=4, stagger=0.025, dur=0.25)
    if t > CUE["dahi"] - 0.1:
        draw_text_reveal(cv, "DAHİLER", 1340, 920, font(96, 900), "#ffd34d", t - (CUE["dahi"] - 0.1), tracking=10,
                         stagger=0.05, dur=0.3, glow=16)
    fk = remap(t, CUE["donup"], CUE["donup"] + 0.5)
    if fk > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((W / 2, H / 2), 1200, [hexc("#e9fbff", 0),
                                                                                    hexc("#bff6ff", 0.3 * fk)],
                                                                  [0.5, 1])))


# ===================================================================== SH150 inner simulation vs frozen AI
def inner_world(cv, t, k):
    """Tiny simulated world inside the head: hill, tree, sun, a ball rolling and replayed."""
    if k <= 0:
        return
    cv.save()
    s = ease_out_back(k)
    cv.scale(s, s)
    r = 120
    cv.drawCircle(0, 0, r + 14, fill(hexc("#ffe2b0", 0.35), blur=20))
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    cv.save()
    cv.clipPath(clip, doAntiAlias=True)
    cv.drawRect(skia.Rect.MakeXYWH(-r, -r, 2 * r, 2 * r), fill(0, shader=lin((0, -r), (0, r), [hexc("#9fe8ff"),
                                                                                                 hexc("#e9fbff")])))
    cv.drawCircle(60, -60, 22, fill(hexc("#ffd34d")))
    hill = skia.Path()
    hill.moveTo(-r, 40)
    hill.cubicTo(-60, -10, 0, -20, 30, 20)
    hill.cubicTo(60, 50, 90, 40, r, 30)
    hill.lineTo(r, r)
    hill.lineTo(-r, r)
    hill.close()
    cv.drawPath(hill, fill(hexc("#56b08f")))
    cv.drawRect(skia.Rect.MakeXYWH(-64, -24, 8, 30), fill(hexc("#6b4a2a")))
    cv.drawCircle(-60, -34, 22, fill(hexc("#3f8f7a")))
    # ball rolls down the hill, again and again (rehearsal)
    ph = (t * 0.7) % 1
    bx = lerp(-20, 100, ph)
    by = -6 + 40 * ph * ph
    cv.drawCircle(bx, by, 12, fill(hexc("#ff7a6b")))
    cv.drawCircle(bx - 4, by - 4, 4, fill(hexc("#ffffff", 0.6)))
    cv.restore()
    cv.drawCircle(0, 0, r, stroke(hexc("#ffe2b0"), 5))
    cv.restore()


def sh150(cv, t):
    # pan left from the frozen robot to reveal the human
    pan = ease_in_out(remap(t, T["sh150"] - 0.1, T["sh150"] + 1.0))
    bg(cv, t, "#0b1430", "#1b1f4a")
    cv.save()
    Cam(lerp(W / 2, W / 2 - 40, pan), H / 2, 1.0).apply(cv)
    # human (left) - glass head with inner world
    ha = pan
    cv.saveLayerAlpha(None, int(255 * ha))
    cv.save()
    cv.translate(-260 * (1 - ha), 0)
    hb = (520, 1080)
    glass_human(cv, t, hb, 1.55, fire=0.6, a=1.0)
    wk = remap(t, CUE["icsel"] - 0.1, CUE["simulasyon"] + 0.3)
    cv.save()
    cv.translate(hb[0] + 10, hb[1] - (96 + 170) * 1.55)
    inner_world(cv, t, wk)
    cv.restore()
    # continuous loop arrow around the head
    lk = remap(t, CUE["surekli"] - 0.1, CUE["surekli"] + 0.6)
    if lk > 0:
        cx, cy, rr = hb[0] + 10, hb[1] - 410, 300
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(cx - rr, cy - rr, 2 * rr, 2 * rr), -90 + t * 60, 300 * ease_out(lk))
        draw_glow_path(cv, arc, "#ffb347", 7, glow=12)
        meas = skia.PathMeasure(arc, False)
        L = meas.getLength()
        if L > 10:
            pos, tan = meas.getPosTan(L)
            ah = skia.Path()
            ah.moveTo(pos.x() + tan.x() * 22, pos.y() + tan.y() * 22)
            ah.lineTo(pos.x() - tan.y() * 16, pos.y() + tan.x() * 16)
            ah.lineTo(pos.x() + tan.y() * 16, pos.y() - tan.x() * 16)
            ah.close()
            cv.drawPath(ah, fill(hexc("#ffb347")))
    # trial and error marks orbiting
    for j, (kind, cue) in enumerate((("x", CUE["hata"]), ("v", CUE["yaparak"] + 0.1))):
        mk = remap(t, cue - 0.05, cue + 0.25)
        if mk > 0:
            a = math.radians(-150 + j * 70) + t * 0.6
            S2.mark(cv, hb[0] + 10 + math.cos(a) * 300, hb[1] - 410 + math.sin(a) * 300, kind, mk)
    cv.restore()
    cv.restore()
    # robot slides from its SH140 spot to the right, frozen
    frozen_robot(cv, t, lerp(W / 2 - 300 + 40 * 0, 1460, pan), 930, 1.0, 1.0, True, CUE["dondur"] + 0.3)
    yk = remap(t, CUE["yoksun"] - 0.15, CUE["yoksun"] + 0.25)
    if yk > 0:
        cv.save()
        cv.translate(1460, 300)
        s = ease_out_back(yk)
        cv.scale(s, s)
        cv.drawCircle(0, 0, 90, fill(hexc("#ff5c6c", 0.35), blur=16))
        cv.drawCircle(0, 0, 80, stroke(hexc("#ff5c6c"), 12))
        cv.drawLine(-56, 56, 56, -56, stroke(hexc("#ff5c6c"), 12))
        cv.save()
        cv.scale(0.45, 0.45)
        cv.saveLayerAlpha(None, 140)
        inner_world(cv, t, 1.0)
        cv.restore()
        cv.restore()
        cv.restore()
    cv.restore()
    # captions
    if t > CUE["icsel"] - 0.1:
        draw_text_reveal(cv, "içsel dünya simülasyonu", 520, 150, font(40, 800), "#ffe2b0", t - CUE["icsel"] + 0.1,
                         stagger=0.015, dur=0.25)
    if t > CUE["surekli"] - 0.1:
        draw_text_reveal(cv, "sürekli · hata yaparak öğrenme", 520, 205, font(30, 600), "#ffb347",
                         t - CUE["surekli"] + 0.1, stagger=0.012, dur=0.25)
    if t > CUE["yoksun"] - 0.1:
        draw_text_reveal(cv, "yapay zekada yok", 1460, 150, font(40, 800), "#ff8f9a", t - CUE["yoksun"] + 0.1,
                         stagger=0.02, dur=0.25)
    fr = 1 - remap(t, T["sh150"], T["sh150"] + 0.6)
    if fr > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(0, shader=rad((W / 2, H / 2), 1200, [hexc("#e9fbff", 0),
                                                                                    hexc("#bff6ff", 0.3 * fr)],
                                                                  [0.5, 1])))


# ===================================================================== DISPATCH
def render(cv, t):
    if t < T["sh110"]:
        sh100(cv, t)
    elif t < T["sh120"]:
        sh110(cv, t)
        g = 0.9 * (1 - remap(t, T["sh110"], T["sh110"] + 0.3))
        glitch(cv, t, g, seed=2)
    elif t < T["sh130"]:
        sh120(cv, t)
        glitch(cv, t, 0.7 * (1 - remap(t, T["sh120"], T["sh120"] + 0.3)), seed=4)
    elif t < T["sh140"]:
        sh130(cv, t)
        glitch(cv, t, 0.6 * (1 - remap(t, T["sh130"], T["sh130"] + 0.3)), seed=6)
    elif t < T["sh150"]:
        sh140(cv, t)
        glitch(cv, t, 0.8 * (1 - remap(t, T["sh140"], T["sh140"] + 0.3)), seed=8)
    else:
        sh150(cv, t)
        k = remap(t, T["sh150"], T["sh150"] + 0.5)
        if k < 1:
            cv.saveLayerAlpha(None, int(255 * (1 - k)))
            sh140(cv, t, robot=False, bg_on=False)
            cv.restore()


if __name__ == "__main__":
    import argparse

    from PIL import Image

    from fm_2d.core import Finisher, new_surface, snapshot

    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--out", default=str(ROOT / "projects/zeka_tarihi/11_render/SC03"))
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
