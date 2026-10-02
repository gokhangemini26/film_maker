"""FILM_MAKER 2D engine - core drawing, timing and finishing helpers (skia).

Everything is code-defined so a scene is reproducible from text, like the
Blender side. Coordinates: 1920x1080 canvas, origin top-left, y down.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np
import skia

W, H = 1920, 1080
FPS = 30


# ---------------------------------------------------------------- timing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def remap(t, a, b):
    """0..1 progress of t inside [a, b], clamped."""
    if b == a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_in_out(x):
    x = clamp(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x * x * x


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0.0, 1.0):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def pulse(t, center, width):
    """Smooth bump 0..1..0 around center."""
    d = abs(t - center) / max(width, 1e-6)
    return 0.0 if d >= 1 else 0.5 * (1 + math.cos(math.pi * d))


def wobble(t, freq=1.0, seed=0.0):
    return (math.sin(t * freq * 2.1 + seed) * 0.6 + math.sin(t * freq * 3.7 + seed * 1.7) * 0.4)


# ---------------------------------------------------------------- colour
def hexc(h: str, a: float = 1.0) -> int:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)


def mix(h1: str, h2: str, t: float, a: float = 1.0) -> int:
    h1, h2 = h1.lstrip("#"), h2.lstrip("#")
    c1 = [int(h1[i:i + 2], 16) for i in (0, 2, 4)]
    c2 = [int(h2[i:i + 2], 16) for i in (0, 2, 4)]
    c = [int(lerp(c1[i], c2[i], clamp(t))) for i in range(3)]
    return skia.ColorSetARGB(int(clamp(a) * 255), *c)


def mixhex(h1: str, h2: str, t: float) -> str:
    h1, h2 = h1.lstrip("#"), h2.lstrip("#")
    c1 = [int(h1[i:i + 2], 16) for i in (0, 2, 4)]
    c2 = [int(h2[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{int(lerp(c1[i], c2[i], clamp(t))):02x}" for i in range(3))


# ---------------------------------------------------------------- paints
def fill(color, blur: float = 0.0, shader=None, blend=None) -> skia.Paint:
    p = skia.Paint(AntiAlias=True, Color=color)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        if color == 0:
            p.setColor(skia.ColorBLACK)
        p.setShader(shader)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def stroke(color, width: float, blur: float = 0.0, cap=skia.Paint.kRound_Cap,
           join=skia.Paint.kRound_Join, shader=None, blend=None) -> skia.Paint:
    p = fill(color, blur, shader, blend)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    p.setStrokeCap(cap)
    p.setStrokeJoin(join)
    return p


def lin(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], colors, pos)


def rad(c, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*c), max(r, 0.01), colors, pos)


def glow_circle(cv, x, y, r, color_hex, a=1.0):
    """Soft radial light blob."""
    cv.drawCircle(x, y, r, fill(0, shader=rad((x, y), r, [hexc(color_hex, a), hexc(color_hex, a * 0.35),
                                                          hexc(color_hex, 0)], [0, 0.35, 1])))


def draw_glow_path(cv, path, color_hex, width, a=1.0, glow=14):
    cv.drawPath(path, stroke(hexc(color_hex, a * 0.55), width * 2.2, blur=glow))
    cv.drawPath(path, stroke(hexc(color_hex, a), width))


# ---------------------------------------------------------------- paths
def smooth_path(pts, closed=True, tension=1.0) -> skia.Path:
    """Catmull-Rom spline through points as cubic beziers."""
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else p2
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def partial_path(path: skia.Path, t: float) -> skia.Path:
    """Trim path to first t fraction of its length (draw-on effect)."""
    t = clamp(t)
    out = skia.Path()
    if t <= 0:
        return out
    meas = skia.PathMeasure(path, False)
    while True:
        L = meas.getLength()
        seg = skia.Path()
        meas.getSegment(0, L * t, seg, True)
        out.addPath(seg)
        if not meas.nextContour():
            break
    return out


def poly(pts, closed=True) -> skia.Path:
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def rrect(x, y, w, h, r) -> skia.Path:
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


# ---------------------------------------------------------------- text
_tf_cache: dict = {}


def typeface(family="Inter Display", weight=700):
    key = (family, weight)
    if key not in _tf_cache:
        _tf_cache[key] = skia.Typeface(family, skia.FontStyle(weight, skia.FontStyle.kNormal_Width,
                                                              skia.FontStyle.kUpright_Slant))
    return _tf_cache[key]


def font(size, weight=700, family="Inter Display"):
    f = skia.Font(typeface(family, weight), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    return f


def text_width(s, f):
    return f.measureText(s)


def draw_text(cv, s, x, y, f, paint, align="center", tracking=0.0):
    """Draw text with optional letter tracking; align left/center/right on x."""
    if tracking == 0:
        w = f.measureText(s)
        ox = {"left": 0, "center": -w / 2, "right": -w}[align]
        cv.drawString(s, x + ox, y, f, paint)
        return w
    widths = [f.measureText(ch) for ch in s]
    w = sum(widths) + tracking * (len(s) - 1)
    ox = {"left": 0, "center": -w / 2, "right": -w}[align]
    cx = x + ox
    for ch, cw in zip(s, widths):
        cv.drawString(ch, cx, y, f, paint)
        cx += cw + tracking
    return w


def draw_text_reveal(cv, s, x, y, f, color_hex, t, align="center", tracking=0.0, rise=24, stagger=0.06,
                     dur=0.5, a=1.0, glow=0.0):
    """Per-letter rise + fade reveal; t in seconds since reveal start."""
    widths = [f.measureText(ch) for ch in s]
    w = sum(widths) + tracking * (len(s) - 1)
    ox = {"left": 0, "center": -w / 2, "right": -w}[align]
    cx = x + ox
    for i, (ch, cw) in enumerate(zip(s, widths)):
        k = ease_out(remap(t, i * stagger, i * stagger + dur))
        if k > 0 and ch.strip():
            yy = y + (1 - k) * rise
            if glow > 0:
                cv.drawString(ch, cx, yy, f, fill(hexc(color_hex, a * k * 0.6), blur=glow))
            cv.drawString(ch, cx, yy, f, fill(hexc(color_hex, a * k)))
        cx += cw + tracking
    return w


# ---------------------------------------------------------------- camera
@dataclass
class Cam:
    x: float = W / 2
    y: float = H / 2
    zoom: float = 1.0
    rot: float = 0.0  # degrees

    def apply(self, cv, parallax: float = 1.0):
        """parallax 1 = moves with world; 0 = fixed to screen."""
        z = 1 + (self.zoom - 1) * parallax
        cv.translate(W / 2, H / 2)
        cv.rotate(self.rot * parallax)
        cv.scale(z, z)
        cv.translate(-(W / 2 + (self.x - W / 2) * parallax), -(H / 2 + (self.y - H / 2) * parallax))


def shake(t, amount, t0, dur=0.35, freq=38.0):
    k = 1 - remap(t, t0, t0 + dur)
    if t < t0 or k <= 0:
        return 0.0, 0.0
    a = amount * k * k
    return math.sin(t * freq) * a, math.cos(t * freq * 1.3) * a


# ---------------------------------------------------------------- particles
class Dust:
    """Deterministic drifting particles (stars, dust, spores)."""

    def __init__(self, n, seed, area=(0, 0, W, H), size=(1, 3), speed=(5, 20), drift=(0, -1)):
        rnd = random.Random(seed)
        self.p = [(rnd.uniform(area[0], area[2]), rnd.uniform(area[1], area[3]), rnd.uniform(*size),
                   rnd.uniform(*speed), rnd.random() * 6.28, rnd.uniform(0.3, 1.0)) for _ in range(n)]
        self.area = area
        self.drift = drift

    def draw(self, cv, t, color_hex, alpha=1.0, twinkle=True, blur=0.0):
        x0, y0, x1, y1 = self.area
        wdt, hgt = x1 - x0, y1 - y0
        for (x, y, s, sp, ph, br) in self.p:
            px = x0 + (x - x0 + self.drift[0] * sp * t + math.sin(t * 0.5 + ph) * 8) % wdt
            py = y0 + (y - y0 + self.drift[1] * sp * t) % hgt
            a = br * alpha * ((0.55 + 0.45 * math.sin(t * 2.3 + ph * 3)) if twinkle else 1)
            cv.drawCircle(px, py, s, fill(hexc(color_hex, a), blur=blur or s * 0.6))


# ---------------------------------------------------------------- finishing
class Finisher:
    """Vignette + film grain + subtle chroma, applied on the numpy frame."""

    def __init__(self, vignette=0.35, grain=2.6, seed=7):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        self.vig = (1 - vignette * np.clip(d, 0, 1) ** 2.2)[..., None].astype(np.float32)
        rng = np.random.default_rng(seed)
        self.noise = [rng.normal(0, grain, (H, W, 1)).astype(np.float32) for _ in range(6)]

    def __call__(self, rgba: np.ndarray, frame: int) -> np.ndarray:
        rgb = rgba[..., :3].astype(np.float32)
        rgb = rgb * self.vig + self.noise[frame % len(self.noise)]
        return np.clip(rgb, 0, 255).astype(np.uint8)


def new_surface():
    return skia.Surface(W, H)


def snapshot(surface) -> np.ndarray:
    img = surface.makeImageSnapshot()
    return img.toarray(colorType=skia.kRGBA_8888_ColorType)


def glitch(cv, t, amount, seed=0):
    """Digital glitch on what is already drawn: displaced horizontal slices + RGB fringe."""
    if amount <= 0:
        return
    surf = cv.getSurface()
    if surf is None:
        return
    img = surf.makeImageSnapshot()
    rnd = random.Random(int(t * 24) + seed)
    n = int(4 + 10 * amount)
    for _ in range(n):
        y = rnd.uniform(0, H)
        h = rnd.uniform(6, 70) * (0.5 + amount)
        dx = rnd.uniform(-1, 1) * 90 * amount
        src = skia.Rect.MakeXYWH(0, y, W, h)
        dst = skia.Rect.MakeXYWH(dx, y, W, h)
        cv.save()
        cv.resetMatrix()
        cv.drawImageRect(img, src, dst)
        cv.restore()
    # chroma fringe
    cv.save()
    cv.resetMatrix()
    for col, off in ((skia.ColorSetARGB(int(70 * amount), 255, 40, 80), 8), (skia.ColorSetARGB(int(70 * amount), 40, 230, 255), -8)):
        p = skia.Paint(ColorFilter=skia.ColorFilters.Blend(col, skia.BlendMode.kSrcIn))
        p.setBlendMode(skia.BlendMode.kScreen)
        p.setAlphaf(0.35 * amount)
        cv.drawImage(img, off * amount, 0, skia.SamplingOptions(), p)
    cv.restore()
