"""Procedural sound recipes for FILM_MAKER (deterministic, numpy only).

Contract for every recipe::

    fn(duration: float, seed: int, params: dict) -> float32 ndarray
        shape (n,) mono or (n, 2) stereo, n == round(duration * 48000)

Determinism: the only randomness is ``numpy.random.default_rng`` seeded from
``(seed, crc32(recipe name))``. No clocks, no global state, no scipy. Filters are
FFT-domain (zero phase) so results do not depend on an IIR implementation.

Levels: every recipe peak-normalises to ``params['peak_db']`` (default -6 dBFS)
unless it is exact silence. The mixer applies the cue gain on top.

Recipes marked ``placeholder=True`` are stand-ins. The human records or supplies
the real sound (see ``HUMAN_SOUND_GAPS`` at the bottom).

Shot events in ``serves`` are written ``SHOT:frame what (sync|board)``. ``sync`` means
the line comes from the shot's ``animation.sound_sync`` in 09_resolved; ``board`` means
it comes from the STORYBOARD ``Sound:`` line only.
"""

from __future__ import annotations

import zlib
from typing import Callable

import numpy as np

SR = 48000
FPS = 24
TWO_PI = 2.0 * np.pi


# --------------------------------------------------------------------------- primitives

def n_samples(duration: float) -> int:
    return int(round(float(duration) * SR))


def _rng(seed: int, name: str) -> np.random.Generator:
    return np.random.default_rng([int(seed) & 0xFFFFFFFF, zlib.crc32(name.encode("utf-8"))])


def _t(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SR


def _filt(x: np.ndarray, lp: float | None = None, hp: float | None = None, order: int = 2) -> np.ndarray:
    """Zero-phase Butterworth-magnitude filter applied in the FFT domain."""
    n = len(x)
    if n < 2:
        return x
    if x.ndim == 2:
        return np.stack([_filt(x[:, c], lp, hp, order) for c in range(x.shape[1])], axis=1)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    H = np.ones_like(f)
    if hp:
        r = f / hp
        H *= (r ** order) / np.sqrt(1.0 + r ** (2 * order))
    if lp:
        H *= 1.0 / np.sqrt(1.0 + (f / lp) ** (2 * order))
    return np.fft.irfft(X * H, n)


def _white(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.standard_normal(n)


def _pink(rng: np.random.Generator, n: int) -> np.ndarray:
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1] if n > 1 else 1.0
    return np.fft.irfft(X / np.sqrt(f / f[1]), n)


def _decay(n: int, tau: float, attack: float = 0.0005) -> np.ndarray:
    t = _t(n)
    env = np.exp(-t / max(tau, 1e-6))
    if attack > 0:
        env *= 1.0 - np.exp(-t / attack)
    return env


def _hann(n: int) -> np.ndarray:
    return np.hanning(n) if n > 2 else np.ones(n)


def _sine(freq, n: int, phase: float = 0.0) -> np.ndarray:
    """Sine from a constant or per-sample frequency curve (Hz)."""
    if np.isscalar(freq):
        return np.sin(TWO_PI * freq * _t(n) + phase)
    ph = TWO_PI * np.cumsum(freq) / SR
    return np.sin(ph + phase)


def _place(buf: np.ndarray, sig: np.ndarray, t0: float, gain: float = 1.0) -> None:
    s = int(round(t0 * SR))
    if s >= len(buf) or s + len(sig) <= 0:
        return
    a = max(0, -s)
    b = min(len(sig), len(buf) - s)
    buf[s + a:s + b] += gain * sig[a:b]


def _bell(freq: float, dur: float, tau: float, partials=((1.0, 1.0), (2.0, 0.35), (2.76, 0.2), (5.4, 0.08))) -> np.ndarray:
    n = n_samples(dur)
    out = np.zeros(n)
    for ratio, amp in partials:
        out += amp * _sine(freq * ratio, n) * _decay(n, tau / (1.0 + 0.6 * (ratio - 1.0)), 0.001)
    k = max(2, n // 4)
    out[n - k:] *= np.cos(np.linspace(0.0, np.pi / 2, k)) ** 2  # release so a finite bell never ends on a click
    return out


def _finish(x: np.ndarray, n: int, params: dict, edge_ms: float = 1.0) -> np.ndarray:
    """Pad/trim to exactly n samples, short edge fades, peak-normalise, float32."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[0] < n:
        x = np.concatenate([x, np.zeros((n - x.shape[0], x.shape[1]))], axis=0)
    x = x[:n].copy()
    k = min(int(SR * edge_ms / 1000.0), n // 2)
    if k > 1:
        ramp = np.linspace(0.0, 1.0, k, endpoint=False)[:, None]
        x[:k] *= ramp
        x[n - k:] *= ramp[::-1]
    peak = float(np.max(np.abs(x))) if n else 0.0
    if peak > 0.0:
        target = 10.0 ** (float(params.get("peak_db", -6.0)) / 20.0)
        x *= target / peak
    out = x.astype(np.float32)
    return out[:, 0] if out.shape[1] == 1 else out


def _stereo_from_mono_pair(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.stack([a, b], axis=1)


def _pulse_train(rng, n: int, rate_hz: np.ndarray, jitter: float, pulse: Callable[[np.random.Generator], np.ndarray],
                 amp: np.ndarray | None = None) -> np.ndarray:
    """Pulses at times where the integrated rate crosses integers (with timing jitter)."""
    phase = np.cumsum(rate_hz) / SR
    idx = np.nonzero(np.diff(np.floor(phase), prepend=0.0) > 0)[0]
    out = np.zeros(n)
    for i in idx:
        j = int(i + rng.normal(0.0, jitter) * SR)
        p = pulse(rng)
        a = 1.0 if amp is None else float(amp[min(i, n - 1)])
        if j < 0 or j >= n:
            continue
        m = min(len(p), n - j)
        out[j:j + m] += a * (0.7 + 0.3 * rng.random()) * p[:m]
    return out


def ratchet_times(duration: float, rate_start_hz: float = 1.0, rate_end_hz: float | None = None,
                  first_at: float = 0.0) -> list[float]:
    """Click times (seconds) for a ratchet whose rate glides linearly (public helper for cue generation).

    The canon phase lock (one click per 24 frames = 1.0 Hz) is the default.
    """
    rate_end_hz = rate_start_hz if rate_end_hz is None else rate_end_hz
    times = []
    t = float(first_at)
    while t < duration - 1e-9:
        times.append(round(t, 9))
        r = rate_start_hz + (rate_end_hz - rate_start_hz) * (t / duration if duration > 0 else 0.0)
        t += 1.0 / max(r, 1e-3)
    return times


# --------------------------------------------------------------------------- UI sounds

def _ui_tap(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.tap")
    pitch = float(p.get("pitch", 1.0)) * (1.0 + 0.03 * r.standard_normal())
    body = _sine(880 * pitch, n) * _decay(n, 0.018)
    click = _filt(_white(r, n), hp=2500) * _decay(n, 0.0025)
    return _finish(body + 0.5 * click, n, p)


def _ui_key_tap(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.key_tap")
    pitch = float(p.get("pitch", 1.0)) * (1.0 + 0.06 * r.standard_normal())
    body = _sine(620 * pitch, n) * _decay(n, 0.014)
    click = _filt(_white(r, n), lp=6000, hp=1800) * _decay(n, 0.002)
    return _finish(body * 0.7 + 0.6 * click, n, p)


def _ui_swipe(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.swipe")
    t = _t(n); u = t / max(duration, 1e-6)
    f = 700 + 2600 * u ** 1.5
    wob = 0.6 + 0.4 * _filt(_white(r, n), lp=90)
    wob /= max(np.max(np.abs(wob)), 1e-9)
    air = _filt(_white(r, n), lp=5000, hp=600) * 0.6
    return _finish((_sine(f, n) * 0.4 + air) * wob * _hann(n), n, p)


def _ui_lowbatt_blip(duration, seed, p):
    n = n_samples(duration)
    out = np.zeros(n)
    _place(out, _sine(1175, n_samples(0.04)) * _decay(n_samples(0.04), 0.02), 0.0)
    _place(out, _sine(880, n_samples(0.05)) * _decay(n_samples(0.05), 0.025), 0.055, 0.8)
    return _finish(out, n, p)


def _ui_charge_chime(duration, seed, p):
    n = n_samples(duration); out = np.zeros(n)
    _place(out, _bell(659.26, 0.5, 0.22), 0.0, 0.8)
    _place(out, _bell(987.77, 0.6, 0.28), 0.085, 1.0)
    return _finish(out, n, p)


def _ui_message_chime(duration, seed, p):
    n = n_samples(duration); out = np.zeros(n)
    _place(out, _bell(783.99, 0.45, 0.2), 0.0, 0.8)
    _place(out, _bell(1174.66, 0.55, 0.26), 0.07, 1.0)
    return _finish(out, n, p)


def _ui_ring_tone(duration, seed, p):
    """One ring pulse: the cue sheet places it once per pulse start (SC01_SH050 f0, f11, f22)."""
    n = n_samples(duration); t = _t(n)
    tone = (_sine(440, n) + _sine(480, n)) * (0.85 + 0.15 * np.sin(TWO_PI * 20 * t))
    a = min(int(0.008 * SR), n // 4); r_ = min(int(0.03 * SR), n // 4)
    env = np.ones(n)
    if a > 0:
        env[:a] = np.linspace(0, 1, a, endpoint=False)
    if r_ > 0:
        env[n - r_:] = np.linspace(1, 0, r_)
    return _finish(tone * env, n, p, edge_ms=0.0)


def _ui_send_soft(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.send_soft")
    m = min(n, n_samples(0.07))
    f = np.linspace(650, 980, m)
    sig = _sine(f, m) * np.hanning(m) + 0.15 * _filt(_white(r, m), lp=4000, hp=1000) * np.hanning(m)
    out = np.zeros(n); out[:m] = sig
    return _finish(out, n, p)


def _ui_delivered_tick(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.delivered_tick")
    tone = _sine(2400, n) * _decay(n, 0.012) + 0.5 * _sine(1200, n) * _decay(n, 0.02)
    click = _filt(_white(r, n), hp=3000) * _decay(n, 0.0015)
    return _finish(tone + 0.3 * click, n, p)


def _ui_elec_tick(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "ui.elec_tick")
    t = _white(r, n)
    return _finish(_filt(t, lp=7000, hp=2500) * _decay(n, 0.0012, 0.0001) + 0.2 * _sine(3100, n) * _decay(n, 0.004), n, p)


# --------------------------------------------------------------------------- hums and beds

def _die_curve(n: int, die_at: float | None, die_dur: float):
    """(amp, pitch) per-sample curves: 1/1 until die_at, then pitch sags and amplitude decays to exact 0."""
    amp = np.ones(n); pitch = np.ones(n)
    if die_at is None:
        return amp, pitch
    s = int(round(die_at * SR)); m = max(1, int(round(die_dur * SR)))
    if s >= n:
        return amp, pitch
    k = np.arange(min(m, n - s)) / m
    amp[s:s + len(k)] = (1 - k) ** 2
    pitch[s:s + len(k)] = 1.0 - 0.35 * k
    amp[s + len(k):] = 0.0
    pitch[s + len(k):] = 0.65
    return amp, pitch


def _hum(n, r, base_hz, harmonics, noise_lp, noise_gain, die_at, die_dur, stereo=True):
    amp, pitch = _die_curve(n, die_at, die_dur)
    chans = []
    for c in range(2 if stereo else 1):
        f = base_hz * pitch
        sig = np.zeros(n)
        for k, a in harmonics:
            sig += a * _sine(f * k, n, phase=r.random() * TWO_PI)
        sig *= 1.0 + 0.03 * _filt(_white(r, n), lp=2.0) / 1.0
        noise = _filt(_pink(r, n), lp=noise_lp) * noise_gain
        chans.append((sig + noise) * amp)
    return _stereo_from_mono_pair(chans[0], chans[1]) if stereo else chans[0]


def _hum_fridge(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "hum.fridge")
    x = _hum(n, r, float(p.get("base_hz", 50.0)), [(1, 1.0), (2, 0.6), (3, 0.25), (4, 0.12)], 500, 0.5,
             p.get("die_at"), float(p.get("die_dur", 0.25)))
    return _finish(x, n, p)


def _hum_shop_light(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "hum.shop_light")
    harm = [(k, 1.0 / k ** 0.8) for k in range(1, 9)]
    x = _hum(n, r, float(p.get("base_hz", 100.0)), harm, 3000, 0.15, p.get("die_at"), float(p.get("die_dur", 0.15)))
    return _finish(_filt(x, lp=2500, hp=60), n, p)


def _hum_phone_buzz(duration, seed, p):
    """Desk vibration buzz. CONFLICT (decision D4): STORYBOARD SC05_SH010 wants it, shot says no vibration."""
    n = n_samples(duration); r = _rng(seed, "hum.phone_buzz")
    t = _t(n)
    gate = (np.sin(TWO_PI * 6 * t) > -0.2).astype(float)
    sig = (_sine(175, n) + 0.5 * _sine(350, n) + 0.3 * _filt(_white(r, n), lp=1500)) * gate
    return _finish(_filt(sig, lp=1200), n, p)


_TONE_PRESETS = {
    "car_interior": dict(lp=450, hp=25, hum=(88.0, 0.05), swell=0.0),
    "street_dusk": dict(lp=3500, hp=60, hum=(0.0, 0.0), swell=0.5),
    "shop": dict(lp=1800, hp=40, hum=(50.0, 0.15), swell=0.0),
    "hana_room": dict(lp=1500, hp=40, hum=(0.0, 0.0), swell=0.0),
}


def _room_tone(duration, seed, p, perspective=None):
    perspective = perspective or p.get("perspective", "hana_room")
    cfg = _TONE_PRESETS[perspective]
    n = n_samples(duration); r = _rng(seed, "amb." + perspective)
    chans = []
    for c in range(2):
        x = _filt(_pink(r, n), lp=cfg["lp"], hp=cfg["hp"])
        if cfg["swell"]:
            sw = 1.0 + cfg["swell"] * _filt(_white(r, n), lp=0.4)
            x *= sw / max(np.max(np.abs(sw)), 1e-9) * 1.4
        hz, g = cfg["hum"]
        if hz:
            x = x / max(np.std(x), 1e-9) + g * 8 * _sine(hz, n, phase=r.random() * TWO_PI)
        chans.append(x)
    return _finish(_stereo_from_mono_pair(*chans), n, p, edge_ms=5.0)


def _amb_silence(duration, seed, p):
    return np.zeros(n_samples(duration), dtype=np.float32)


def _amb_distant_car(duration, seed, p):
    """Distant car passing: swelling low-passed noise, pan drifting left to right. Rough synth; a library file may replace it."""
    n = n_samples(duration); r = _rng(seed, "amb.distant_car_pass")
    u = np.linspace(0, 1, n)
    env = np.sin(np.pi * u) ** 2
    base = _filt(_pink(r, n), lp=700, hp=50)
    sweep = _filt(_pink(r, n), lp=1400, hp=100) * u * (1 - u) * 4
    x = (base + 0.4 * sweep) * env
    pan = u
    return _finish(_stereo_from_mono_pair(x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2)), n, p, edge_ms=5.0)


# --------------------------------------------------------------------------- crank, plastic, lids, doors

def _click_core(r, pitch=1.0) -> np.ndarray:
    n = n_samples(0.09)
    pawl = _filt(_white(r, n), hp=1800) * _decay(n, 0.0025, 0.0001)
    tock = (_sine(430 * pitch, n) + 0.5 * _sine(1130 * pitch, n)) * _decay(n, 0.014, 0.0003)
    spring = _sine(2650 * pitch, n) * _decay(n, 0.006, 0.0002) * 0.25
    return 0.9 * pawl + 0.7 * tock + spring


def _crank_click(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "crank.click")
    core = _click_core(r, 1.0 + 0.03 * r.standard_normal())
    out = np.zeros(n); out[:min(n, len(core))] = core[:n]
    return _finish(out, n, p, edge_ms=0.0)


def _crank_ratchet(duration, seed, p):
    """Ratchet run. params: rate_start_hz (default 1.0 = one click per 24 frames), rate_end_hz, first_at (s),
    or click_times (list of seconds, overrides the rate)."""
    n = n_samples(duration); r = _rng(seed, "crank.ratchet")
    times = p.get("click_times")
    if times is None:
        times = ratchet_times(duration, float(p.get("rate_start_hz", 1.0)), p.get("rate_end_hz"), float(p.get("first_at", 0.0)))
    out = np.zeros(n)
    for tt in times:
        vel = 0.85 + 0.15 * r.random()
        _place(out, _click_core(r, 1.0 + 0.025 * r.standard_normal()), tt, vel)
    return _finish(out, n, p, edge_ms=0.0)


def _plastic_clunk(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "fx.plastic_clunk")
    f = 140 * np.exp(-_t(n) / 0.05) + 60
    thump = _sine(f, n) * _decay(n, 0.09, 0.0008)
    body = _filt(_white(r, n), lp=1300, hp=120) * _decay(n, 0.035, 0.0005)
    hollow = (_sine(320, n) + 0.6 * _sine(770, n)) * _decay(n, 0.05, 0.001) * 0.5
    out = thump + 0.8 * body + hollow
    bounce = 0.35 * (_sine(95, n) * _decay(n, 0.05, 0.001) + 0.6 * _filt(_white(r, n), lp=900, hp=100) * _decay(n, 0.02, 0.0005))
    _place(out, bounce[:max(0, n - int(0.058 * SR))], 0.058)
    return _finish(out, n, p, edge_ms=0.5)


def _plastic_scuff(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "fx.plastic_scuff")
    rough = _filt(_white(r, n), lp=6000, hp=1200)
    gate = np.maximum(0.0, _filt(_white(r, n), lp=int(p.get("speed", 14))))
    gate = gate / max(np.max(gate), 1e-9)
    return _finish(rough * gate ** 1.5 * _hann(n) ** 0.5, n, p, edge_ms=4.0)


def _soft_bump(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "fx.soft_bump")
    return _finish(_sine(70, n) * _decay(n, 0.05, 0.002) + 0.4 * _filt(_white(r, n), lp=400) * _decay(n, 0.04, 0.002), n, p)


def _heat_ticks(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.heat_ticks")
    out = np.zeros(n); t = 0.25 + 0.4 * r.random()
    while t < duration - 0.05:
        m = n_samples(0.03)
        f = 2200 + 900 * r.random()
        tick = _sine(f, m) * _decay(m, 0.006, 0.0002) + 0.3 * _filt(_white(r, m), hp=3000) * _decay(m, 0.002, 0.0001)
        _place(out, tick, t, 0.5 + 0.5 * r.random())
        t += 0.5 + 1.1 * r.random()
    return _finish(out, n, p)


def _glovebox_lid(duration, seed, p):
    """mode 'drop' (lid falls open, hinge stop clack) or 'latch' (snaps shut, shorter and drier)."""
    n = n_samples(duration); r = _rng(seed, "car.glovebox_lid")
    mode = p.get("mode", "drop")
    tock = (_sine(260, n) + 0.55 * _sine(540, n) + 0.3 * _sine(910, n)) * _decay(n, 0.03 if mode == "drop" else 0.018, 0.0004)
    click = _filt(_white(r, n), lp=7000, hp=2000) * _decay(n, 0.003, 0.0001)
    out = tock * 0.8 + click
    if mode == "drop":
        rat = _filt(_white(r, n), lp=3500, hp=800) * _decay(n, 0.02, 0.001) * 0.25
        _place(out, rat[:max(0, n - int(0.045 * SR))], 0.045)
    else:
        latch = _sine(1500, n) * _decay(n, 0.004, 0.0001) * 0.5
        _place(out, latch[:max(0, n - int(0.012 * SR))], 0.012)
    return _finish(out, n, p, edge_ms=0.3)


def _door_close(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.door_close")
    thud = _sine(90 * np.exp(-_t(n) / 0.06) + 55, n) * _decay(n, 0.11, 0.001)
    panel = _filt(_white(r, n), lp=900, hp=80) * _decay(n, 0.08, 0.001)
    out = thud + 0.7 * panel
    latch = _filt(_white(r, n), lp=5000, hp=1500) * _decay(n, 0.005, 0.0002) + 0.5 * _sine(1900, n) * _decay(n, 0.006, 0.0002)
    _place(out, latch[:max(0, n - int(0.022 * SR))], 0.022, 0.6)
    return _finish(out, n, p, edge_ms=0.5)


def _door_open(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.door_open")
    click = _filt(_white(r, n), lp=5000, hp=1200) * _decay(n, 0.006, 0.0002) + 0.5 * _sine(1400, n) * _decay(n, 0.008, 0.0002)
    out = click.copy()
    seal = _filt(_white(r, n), lp=1500, hp=200) * _decay(n, 0.1, 0.01) * 0.3
    _place(out, seal[:max(0, n - int(0.03 * SR))], 0.03)
    stop = (_sine(130, n) * _decay(n, 0.04, 0.001) + 0.3 * _filt(_white(r, n), lp=700) * _decay(n, 0.03, 0.001))
    _place(out, stop[:max(0, n - int(0.2 * SR))], 0.2, 0.7)
    return _finish(out, n, p, edge_ms=0.5)


def _shop_door_chime(duration, seed, p):
    """Two-note door bell. params: tail_only (True starts late in the decay, for 'chime tail' under SC03_SH010)."""
    n = n_samples(duration + (0.25 if p.get("tail_only") else 0.0)); out = np.zeros(n)
    _place(out, _bell(1046.5, 0.9, 0.5), 0.0, 0.9)
    _place(out, _bell(783.99, 1.2, 0.7), 0.16, 1.0)
    if p.get("tail_only"):
        cut = n_samples(0.25); out = out[cut:] * np.linspace(1.0, 1.0, max(1, n - cut))
        n = len(out)
    return _finish(out, n_samples(duration), p, edge_ms=1.0)


# --------------------------------------------------------------------------- car start / stall

def _car_starter(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.starter")
    u = _t(n) / max(duration, 1e-6)
    f = 150 + 170 * u ** 0.7
    ph = TWO_PI * np.cumsum(f) / SR
    whine = sum(np.sin(k * ph) / k for k in range(1, 6))
    whine = _filt(whine, lp=2500)
    pulse_rate = 8 + 6 * u
    pulse = 0.55 + 0.45 * np.maximum(0, np.sin(TWO_PI * np.cumsum(pulse_rate) / SR)) ** 2
    rumble = _filt(_white(r, n), lp=260) * pulse * 2.0
    a = min(int(0.015 * SR), n // 3)
    env = np.ones(n)
    if a > 0:
        env[:a] = np.linspace(0, 1, a, endpoint=False)
        env[n - a:] = np.linspace(1, 0.15, a)
    return _finish((0.55 * whine + rumble) * env, n, p)


def _engine_pulse(r) -> np.ndarray:
    m = n_samples(0.07)
    return _filt(_white(r, m), lp=500) * _decay(m, 0.02, 0.001) * 1.5 + _sine(58, m) * _decay(m, 0.03, 0.001)


def _car_cough(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.cough")
    f = 75 * np.exp(-_t(n) / 0.05) + 38
    thump = _sine(f, n) * _decay(n, 0.07, 0.002)
    puff = _filt(_white(r, n), lp=650, hp=40) * _decay(n, 0.09, 0.003)
    out = thump + 1.2 * puff
    m = n_samples(0.05)
    sub = (_filt(_white(r, m), lp=450) * _decay(m, 0.02, 0.001) + _sine(52, m) * _decay(m, 0.03, 0.001)) * 0.5
    _place(out, sub, 0.075)
    return _finish(out, n, p, edge_ms=0.5)


def _car_idle_rough(duration, seed, p):
    n = n_samples(duration); r = _rng(seed, "car.idle_rough")
    rate = np.full(n, float(p.get("rate_hz", 13.0)))
    rate *= 1.0 + 0.08 * _filt(_white(r, n), lp=3.0) / 0.05 * 0.05
    x = _pulse_train(r, n, rate, 0.004, _engine_pulse)
    wob = 1.0 + 0.25 * _filt(_white(r, n), lp=4.0) / max(np.std(_filt(_white(r, n), lp=4.0)), 1e-9) * 0.3
    return _finish(_filt(x * wob, lp=900, hp=30), n, p, edge_ms=8.0)


def _engine_die(duration, seed, p):
    """Engine sigh, shudder, stop. params (seconds): shudder_at (default 4/24), stop_at (default 10/24).
    Exact silence after stop_at. SC01_SH130 from f22: sigh f22, shudder f26, stop f32."""
    n = n_samples(duration); r = _rng(seed, "car.engine_die")
    shudder_at = float(p.get("shudder_at", 4 / 24)); stop_at = float(p.get("stop_at", 10 / 24))
    t = _t(n)
    rate = np.where(t < shudder_at, 13.0 - 4.0 * t / max(shudder_at, 1e-6), 9.0 - 6.5 * (t - shudder_at) / max(stop_at - shudder_at, 1e-6))
    amp = np.where(t < shudder_at, 1.0 - 0.3 * t / max(shudder_at, 1e-6), 0.7 + 0.5 * np.sin(TWO_PI * 11 * t))
    x = _pulse_train(r, n, np.maximum(rate, 1.5), 0.006, _engine_pulse, amp)
    stop = np.zeros(n)
    _place(stop, (_sine(48, n_samples(0.12)) * _decay(n_samples(0.12), 0.05, 0.002) + _filt(_white(r, n_samples(0.12)), lp=300) * _decay(n_samples(0.12), 0.04, 0.002)), stop_at, 1.4)
    x = _filt(x, lp=800, hp=30)
    s = int(round(stop_at * SR))
    fade = np.ones(n); k = min(int(0.03 * SR), s)
    fade[max(0, s - k):s] = np.linspace(1, 0, s - max(0, s - k)); fade[s:] = 0.0
    y = x * fade + stop
    y[int(round((stop_at + 0.14) * SR)):] = 0.0
    return _finish(y, n, p, edge_ms=0.5)


# --------------------------------------------------------------------------- placeholders (human records the real ones)

def _breath(r, n, kind: str, p) -> np.ndarray:
    u = np.linspace(0, 1, n)
    env = (np.sin(np.pi * u ** (0.6 if kind == "in" else 1.6))) ** 1.5
    src = _white(r, n)
    x = _filt(src, lp=3500, hp=350) + 0.9 * _filt(src, lp=1300, hp=700) * 1.5
    return x * env


def _body_breath_placeholder(duration, seed, p):
    """PLACEHOLDER (human records the real breath). params: kind 'in' | 'out'."""
    n = n_samples(duration); r = _rng(seed, "body.breath_placeholder")
    return _finish(_breath(r, n, p.get("kind", "out"), p), n, p, edge_ms=5.0)


def _body_sigh_placeholder(duration, seed, p):
    """PLACEHOLDER (human records the real sigh): breath out with a soft falling voiced hint."""
    n = n_samples(duration); r = _rng(seed, "body.sigh_placeholder")
    x = _breath(r, n, "out", p)
    u = np.linspace(0, 1, n)
    hint = _sine(200 - 60 * u, n) * (np.sin(np.pi * u) ** 3) * 0.08
    return _finish(x + hint, n, p, edge_ms=5.0)


def _body_nose_laugh_placeholder(duration, seed, p):
    """PLACEHOLDER (human records): two soft nasal puffs (SC05_SH030 'might be a laugh')."""
    n = n_samples(duration); r = _rng(seed, "body.nose_laugh_placeholder")
    out = np.zeros(n)
    for t0, g in ((0.0, 1.0), (0.17, 0.7)):
        m = n_samples(0.13)
        out_p = _filt(_white(r, m), lp=2600, hp=500) * np.hanning(m)
        _place(out, out_p, t0, g)
    return _finish(out, n, p, edge_ms=3.0)


def _music_headphone_leak(duration, seed, p):
    """PLACEHOLDER (human supplies the real track): thin arpeggio, high-passed and low-passed like a headphone leak."""
    n = n_samples(duration); out = np.zeros(n)
    notes = [440.0, 554.37, 659.26, 554.37, 493.88, 659.26, 739.99, 659.26]
    step = 0.22
    for i in range(int(duration / step) + 1):
        f = notes[i % len(notes)]
        m = n_samples(0.3)
        tone = (_sine(f, m) + 0.4 * _sine(2 * f, m) + 0.2 * _sine(3 * f, m)) * _decay(m, 0.12, 0.004)
        _place(out, tone, i * step)
    return _finish(_filt(out, lp=4500, hp=700), n, p, edge_ms=5.0)


# --------------------------------------------------------------------------- registry

def _entry(fn, desc, serves, placeholder=False, channels=1, default_duration=0.5):
    return {"fn": fn, "desc": desc, "serves": serves, "placeholder": placeholder, "channels": channels,
            "default_duration": default_duration}


REGISTRY: dict[str, dict] = {
    "ui.tap": _entry(_ui_tap, "Soft UI tap: sine body plus click.",
                     ["SC01_SH020 tap (board)", "SC01_SH040 tap (board)", "SC04_SH060 soft taps (board)"], default_duration=0.08),
    "ui.key_tap": _entry(_ui_key_tap, "Soft on-screen keyboard key tap, no letters, seed varies pitch.",
                         ["SC01_SH070 soft key taps (board)"], default_duration=0.06),
    "ui.swipe": _entry(_ui_swipe, "Soft swipe: rising airy sweep.", ["SC01_SH030 swipe (board)"], default_duration=0.25),
    "ui.lowbatt_blip": _entry(_ui_lowbatt_blip, "Tiny two-pip low-battery blip.", ["SC01_SH080 low-battery blip (board)"], default_duration=0.14),
    "ui.charge_chime": _entry(_ui_charge_chime, "Soft rising two-note charging chime.",
                              ["SC01_SH120 f2 charging chime (sync)", "SC03_SH020 charging chime (board)"], default_duration=0.8),
    "ui.message_chime": _entry(_ui_message_chime, "Soft message chime. Ruling D4 pending: SC04_SH070 shot sync says no UI sound.",
                               ["SC04_SH070 soft chime (board, CONFLICT D4)"], default_duration=0.8),
    "ui.ring_tone": _entry(_ui_ring_tone, "One ring pulse (two-tone with flutter); duration = pulse length, 11 f = 0.4583 s.",
                           ["SC01_SH050 f0 ring 1 (sync)", "SC01_SH050 f11 ring 2 (sync)", "SC01_SH050 f22 ring 3 (sync)"], default_duration=11 / 24),
    "ui.send_soft": _entry(_ui_send_soft, "Soft whoosh-less send sound: short rising blip.", ["SC04_SH080 f6 soft send (sync)"], default_duration=0.12),
    "ui.delivered_tick": _entry(_ui_delivered_tick, "Small bright 'delivered' tick.", ["SC04_SH080 f34 tick (board)"], default_duration=0.1),
    "ui.elec_tick": _entry(_ui_elec_tick, "Tiny electrical tick, very short.", ["SC04_SH020 f14 tick (sync)", "SC04_SH020 f20 tick (sync)"], default_duration=0.05),
    "hum.fridge": _entry(_hum_fridge, "Fridge compressor hum (50 Hz + harmonics, stereo). params die_at (s): hum sags and stops to exact 0.",
                         ["SC03_SH010 fridge hum (board)", "SC03_SH030 fridge hum (board)", "SC03_SH050 f8 hum stops (sync)"], channels=2, default_duration=2.0),
    "hum.shop_light": _entry(_hum_shop_light, "Shop panel light buzz (100 Hz + harmonics). params die_at (s).",
                             ["SC03_SH050 f8 hum stops (sync)"], channels=2, default_duration=2.0),
    "hum.phone_buzz": _entry(_hum_phone_buzz, "Desk vibration buzz. CONFLICT D4: shot says no vibration.",
                             ["SC05_SH010 desk buzz (board, CONFLICT D4)"], default_duration=0.5),
    "amb.car_interior": _entry(lambda d, s, p: _room_tone(d, s, p, "car_interior"), "Closed-cabin room tone bed.",
                               ["SC01 interior bed (board)", "SC01_SH140 silence in the car (sync, bed only)"], channels=2, default_duration=4.0),
    "amb.street_dusk": _entry(lambda d, s, p: _room_tone(d, s, p, "street_dusk"), "Open quiet street at dusk bed (no bird, no traffic).",
                              ["SC04_SH010 street only (board)", "SC06_SH010 street (board)", "SC01_SH150 (board)"], channels=2, default_duration=4.0),
    "amb.shop_room": _entry(lambda d, s, p: _room_tone(d, s, p, "shop"), "Shop room tone with faint 50 Hz.", ["SC03 shop bed (board)"], channels=2, default_duration=4.0),
    "amb.hana_room": _entry(lambda d, s, p: _room_tone(d, s, p, "hana_room"), "Hana's room, near-silent room tone.", ["SC05_SH030 room tone (board)", "SC05_SH020 room quiet (board)"], channels=2, default_duration=4.0),
    "amb.silence": _entry(_amb_silence, "Exact digital silence (float zeros).",
                          ["SC03_SH060 silence (board)", "SC03_SH050 after f8 (sync)", "SC01_SH140 (sync)"], default_duration=1.0),
    "amb.distant_car_pass": _entry(_amb_distant_car, "Rough distant car pass, swelling noise, pan drift. Library file may replace.",
                                   ["SC03_SH070 distant car (board)"], channels=2, default_duration=3.0),
    "crank.click": _entry(_crank_click, "One ratchet click (pawl tick + tock + spring).", ["SC04_SH070 f4 click (sync)", "SC04_SH090 f7 last click (sync)"], default_duration=0.09),
    "crank.ratchet": _entry(_crank_ratchet, "Ratchet run, variable speed: rate_start_hz/rate_end_hz, first_at, or click_times; default 1 Hz = 24 f phase lock.",
                            ["SC04_SH050 f56 + every 24 f (sync)", "SC04_SH060 f0/f24/f48 (sync)", "SC04_SH080 f2/f26/f50 (sync)", "SC04_SH060 slower during hover (board)"], default_duration=3.0),
    "fx.plastic_clunk": _entry(_plastic_clunk, "Heavy plastic CLUNK with a small bounce.", ["SC01_SH100 f31 clunk (sync)", "SC03_SH050 f8 clunk (sync)"], default_duration=0.5),
    "fx.plastic_scuff": _entry(_plastic_scuff, "Plastic scuffs on cloth/plastic; params speed (Hz).", ["SC01_SH110 plastic scuffs (board)", "SC03_SH020 scrape (board)"], default_duration=0.4),
    "fx.soft_bump": _entry(_soft_bump, "Soft low bump.", ["SC01_SH150 soft bump (board)"], default_duration=0.25),
    "car.heat_ticks": _entry(_heat_ticks, "Car metal ticking in the heat, sparse irregular ticks.", ["SC01_SH010 car ticking (board)"], default_duration=2.0),
    "car.glovebox_lid": _entry(_glovebox_lid, "Glovebox lid: params mode 'drop' (falls open) or 'latch' (snaps shut).",
                               ["SC01_SH100 f25 lid (sync)", "SC01_SH110 lid snaps shut (board)", "SC04_SH040 lid (board)"], default_duration=0.3),
    "car.door_close": _entry(_door_close, "Car door close thunk with latch.", ["SC02_SH010 door thunk (board)"], default_duration=0.45),
    "car.door_open": _entry(_door_open, "Car door open: latch release, seal, hinge stop.", ["SC01_SH150/SC02_SH010 door opening (board, implied)"], default_duration=0.45),
    "shop.door_chime": _entry(_shop_door_chime, "Shop door bell; params tail_only=True for the chime tail.",
                              ["SC02_SH030 f15 door chime (sync)", "SC03_SH010 chime tail (board)"], default_duration=1.2),
    "car.starter": _entry(_car_starter, "Starter whine with cranking pulse, rising.", ["SC01_SH100 f3 key turn (sync)"], default_duration=0.25),
    "car.cough": _entry(_car_cough, "Engine cough: thump, puff, trailing sub-pop.", ["SC01_SH100 f5 cough (sync)", "SC01_SH100 f9 cough (sync)"], default_duration=0.3),
    "car.idle_rough": _entry(_car_idle_rough, "Rough idle from the catch; params rate_hz.", ["SC01_SH100 f14 catch, rough idle (sync)"], default_duration=1.0),
    "car.engine_die": _entry(_engine_die, "Engine sigh, shudder, stop, exact silence after stop_at; start at f22 of SC01_SH130 (dur 12 f).",
                             ["SC01_SH130 f22 sigh (sync)", "SC01_SH130 f26 shudder (sync)", "SC01_SH130 f32 stop (sync)"], default_duration=0.5),
    "body.breath_placeholder": _entry(_body_breath_placeholder, "PLACEHOLDER breath, params kind in|out. Human records the real ones.",
                                      ["SC01_SH040 in-breath (board)", "SC01_SH090 exhale (board)", "SC01_SH130 f4 relieved breath (sync)", "SC01_SH150 f26 out-breath (sync)",
                                       "SC03_SH040 long breath out (board)", "SC04_SH030 held breath (board)", "SC04_SH050 breath in time (sync)", "SC04_SH090 f8 breath out (sync)", "SC06_SH010 long easy breath out (board)"],
                                      placeholder=True, default_duration=0.9),
    "body.sigh_placeholder": _entry(_body_sigh_placeholder, "PLACEHOLDER sigh. Human records the real one.", ["SC01_SH060 small sigh (board)"], placeholder=True, default_duration=0.8),
    "body.nose_laugh_placeholder": _entry(_body_nose_laugh_placeholder, "PLACEHOLDER two nasal puffs. Human records the real one.", ["SC05_SH030 breath that might be a laugh (board)"], placeholder=True, default_duration=0.4),
    "music.headphone_leak_placeholder": _entry(_music_headphone_leak, "PLACEHOLDER thin leaked-headphone loop. Human supplies real track.", ["SC05_SH010 leaking music (board)", "SC05_SH020 music drops away (board)"], placeholder=True, default_duration=4.0),
}

# Sounds that no recipe can credibly provide. The human records or downloads these.
HUMAN_SOUND_GAPS = [
    "breaths and sighs (all body.* placeholders): SC01_SH040, SH060, SH090, SH130 f4, SH150 f26, SC03_SH040, SC04_SH030, SH050 in time, SH090 f8, SC05_SH030 nose laugh, SC06_SH010",
    "footsteps (SC02_SH010, SH020, SC03_SH010), cloth and seat creak (SC01_SH060, SC04_SH040), pencil scratch (SC05)",
    "bird (SC01_SH010, SH150), traffic and distant car pass (SC04_SH010, SC03_SH070) library takes preferred over the rough synth",
    "Hana's headphone music track (SC05_SH010/020) and final starter/cough/stall/door/glovebox timbres judged by ear",
    "any real recording that replaces a synth needs library/audio/<id>/asset.yaml with a licence",
]


def list_recipes() -> list[dict]:
    """Sorted, JSON-friendly listing (no functions)."""
    return [{"name": k, **{a: v[a] for a in ("desc", "serves", "placeholder", "channels", "default_duration")}} for k, v in sorted(REGISTRY.items())]


def render(name: str, duration: float, seed: int = 0, params: dict | None = None) -> np.ndarray:
    """Render a recipe to float32 (n,) or (n, 2) with n == round(duration*48000)."""
    if name not in REGISTRY:
        raise KeyError(f"unknown recipe {name!r}; see list_recipes()")
    p = dict(params or {})
    x = REGISTRY[name]["fn"](float(duration), int(seed), p)
    x = np.asarray(x, dtype=np.float32)
    n = n_samples(duration)
    if x.shape[0] != n or not np.all(np.isfinite(x)):
        raise ValueError(f"recipe {name} produced invalid output (shape {x.shape}, expected {n} samples)")
    return x


def render_frames(name: str, frames: float, seed: int = 0, params: dict | None = None) -> np.ndarray:
    """Like render() with the duration given in 24 fps frames (2000 samples each)."""
    return render(name, frames / FPS, seed, params)
