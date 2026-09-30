"""Sample-exact mixer on a 48 kHz stereo timeline at the 24 fps frame grid, plus loudness measures.

- 1 frame = 2000 samples exactly (48000 / 24). Cue positions are ``round(frame * 2000)``.
- Cues are added to named stems (ui, sfx, foley, amb, body, music ...); the master is the
  stem sum. Nothing is normalised or limited here: the mixer reports, it never hides clipping.
- Pan law: constant power, pan in [-1 (left), +1 (right)]. A mono source at centre gets -3 dB
  per side; a stereo source is balanced with unity at centre.
- numpy only. Loudness is an approximation of BS.1770 (K-weighting applied in the frequency
  domain, 400 ms blocks with 75 % overlap, absolute and relative gates). ffmpeg ebur128
  stays the reference for delivery; use this for quick checks and tests.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

from . import synth

SR = synth.SR
FPS = synth.FPS
SPF = SR // FPS  # 2000
assert SR % FPS == 0


def frame_to_sample(frame: float) -> int:
    return int(round(float(frame) * SPF))


def db_to_gain(db: float) -> float:
    return float(10.0 ** (float(db) / 20.0))


def _to_stereo(x: np.ndarray, pan: float) -> np.ndarray:
    theta = (float(np.clip(pan, -1.0, 1.0)) + 1.0) * np.pi / 4.0
    gl, gr = np.cos(theta), np.sin(theta)
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        return np.stack([x * gl, x * gr], axis=1)
    k = np.sqrt(2.0)
    return np.stack([x[:, 0] * gl * k, x[:, 1] * gr * k], axis=1)


class Timeline:
    """Stereo float32 stems on a frame-grid timeline."""

    def __init__(self, total_frames: int):
        self.total_frames = int(total_frames)
        self.n = self.total_frames * SPF
        self.stems: dict[str, np.ndarray] = {}
        self.placements: list[dict] = []

    def _stem(self, name: str) -> np.ndarray:
        if name not in self.stems:
            self.stems[name] = np.zeros((self.n, 2), dtype=np.float32)
        return self.stems[name]

    def add_cue(self, stem: str, audio: np.ndarray, at_frame: float = 0, gain_db: float = 0.0, pan: float = 0.0,
                fade_in_f: float = 0, fade_out_f: float = 0, offset_f: float = 0, end_frame: float | None = None,
                label: str = "") -> tuple[int, int]:
        """Place audio starting at sample round((at_frame + offset_f) * 2000). Returns (start, stop) samples.

        end_frame (exclusive, timeline frame) truncates the cue; fades are linear, in frames.
        Anything outside the timeline is cut.
        """
        start = frame_to_sample(float(at_frame) + float(offset_f))
        y = _to_stereo(audio, pan) * db_to_gain(gain_db)
        if end_frame is not None:
            y = y[:max(0, frame_to_sample(end_frame) - start)]
        m = len(y)
        fi = min(frame_to_sample(fade_in_f), m)
        fo = min(frame_to_sample(fade_out_f), m)
        if fi > 0:
            y[:fi] *= np.linspace(0.0, 1.0, fi, endpoint=False)[:, None]
        if fo > 0:
            y[m - fo:] *= np.linspace(1.0, 0.0, fo)[:, None]
        a = max(0, -start)
        b = min(m, self.n - start)
        if b > a:
            buf = self._stem(stem)
            buf[start + a:start + b] += y[a:b].astype(np.float32)
        stop = start + b if b > a else start
        self.placements.append({"stem": stem, "label": label, "start": start, "stop": max(stop, start)})
        return start, max(stop, start)

    def add_bed(self, stem: str, audio: np.ndarray, from_frame: float, to_frame: float, xfade_f: float = 0,
                gain_db: float = 0.0, pan: float = 0.0, label: str = "") -> tuple[int, int]:
        """Bed over [from_frame, to_frame); audio is tiled if shorter (generate beds full length), cross-faded at both ends."""
        s, e = frame_to_sample(from_frame), frame_to_sample(to_frame)
        length = max(0, e - s)
        a = np.asarray(audio)
        if len(a) < length and len(a) > 0:
            reps = -(-length // len(a))
            a = np.concatenate([a] * reps, axis=0)
        a = a[:length]
        return self.add_cue(stem, a, at_frame=from_frame, gain_db=gain_db, pan=pan, fade_in_f=xfade_f,
                            fade_out_f=xfade_f, label=label or "bed")

    def master(self, stem_gain_db: dict[str, float] | None = None, muted: tuple[str, ...] = ()) -> np.ndarray:
        out = np.zeros((self.n, 2), dtype=np.float32)
        for name in sorted(self.stems):  # fixed order => bit-identical sums
            if name in muted:
                continue
            g = db_to_gain((stem_gain_db or {}).get(name, 0.0))
            out += (self.stems[name] * np.float32(g)).astype(np.float32)
        return out

    def write(self, out_dir: str | Path, master_name: str = "mix_48k_stereo.wav", bits: int = 24) -> dict[str, Path]:
        out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for name in sorted(self.stems):
            p = out_dir / f"stem_{name}.wav"; write_wav(p, self.stems[name], SR, bits); paths[f"stem_{name}"] = p
        p = out_dir / master_name; write_wav(p, self.master(), SR, bits); paths["master"] = p
        return paths


def mix_from_spec(spec: dict) -> Timeline:
    """Build a timeline from a plain dict (JSON-able), rendering recipes with fm.audio.synth.

    spec = {"total_frames": 96,
            "beds": [{"stem": "amb", "recipe": "amb.street_dusk", "seed": 1, "from_f": 0, "to_f": 96, "xfade_f": 6, "gain_db": -30}],
            "cues": [{"stem": "ui", "recipe": "ui.ring_tone", "seed": 3, "at_f": 0, "duration_f": 11, "params": {},
                      "gain_db": -12, "pan": 0.0, "offset_f": 0, "end_f": null, "fade": {"in_f": 0, "out_f": 2}}]}
    A cue may give "file" (a wav path) instead of "recipe".
    """
    tl = Timeline(spec["total_frames"])
    for b in spec.get("beds", []):
        dur_f = b["to_f"] - b["from_f"]
        audio = synth.render_frames(b["recipe"], dur_f, b.get("seed", 0), b.get("params"))
        tl.add_bed(b.get("stem", "amb"), audio, b["from_f"], b["to_f"], b.get("xfade_f", 0), b.get("gain_db", 0.0), b.get("pan", 0.0), b["recipe"])
    for c in spec.get("cues", []):
        if "file" in c:
            audio, _ = read_wav(c["file"])
        else:
            dur_f = c.get("duration_f")
            if dur_f is None:
                dur_f = synth.REGISTRY[c["recipe"]]["default_duration"] * FPS
            audio = synth.render_frames(c["recipe"], dur_f, c.get("seed", 0), c.get("params"))
        fade = c.get("fade", {})
        tl.add_cue(c.get("stem", "sfx"), audio, c.get("at_f", 0), c.get("gain_db", 0.0), c.get("pan", 0.0),
                   fade.get("in_f", 0), fade.get("out_f", 0), c.get("offset_f", 0), c.get("end_f"), c.get("recipe", c.get("file", "")))
    return tl


# --------------------------------------------------------------------------- WAV I/O (wave module, deterministic)

def write_wav(path, x: np.ndarray, sr: int = SR, bits: int = 24) -> None:
    """Write float32 (n,) or (n, ch) to PCM WAV, 16 or 24 bit. Same input => same bytes."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    ch = x.shape[1]
    scale = float(2 ** (bits - 1) - 1)
    q = np.clip(np.round(x * scale), -scale - 1, scale).astype("<i4")
    if bits == 16:
        raw = q.astype("<i2").tobytes()
    elif bits == 24:
        raw = q.reshape(-1).view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    else:
        raise ValueError("bits must be 16 or 24")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch); w.setsampwidth(bits // 8); w.setframerate(sr)
        w.writeframes(raw)


def read_wav(path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        q = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v & 0x800000, v - 0x1000000, v)
        q = v.astype(np.float64) / 8388608.0
    else:
        raise ValueError(f"unsupported sample width {sw}")
    q = q.reshape(-1, ch)
    return (q[:, 0] if ch == 1 else q).astype(np.float32), sr


# --------------------------------------------------------------------------- measures

_FLOOR = -120.0


def _db(v: float) -> float:
    return float(20.0 * np.log10(v)) if v > 1e-6 else _FLOOR


def peak_dbfs(x: np.ndarray) -> float:
    return _db(float(np.max(np.abs(x)))) if x.size else _FLOOR


def true_peak_dbfs(x: np.ndarray, oversample: int = 4) -> float:
    """Approximate true peak: FFT zero-pad upsampling per channel."""
    a = np.asarray(x, dtype=np.float64)
    a = a[:, None] if a.ndim == 1 else a
    best = 0.0
    for c in range(a.shape[1]):
        X = np.fft.rfft(a[:, c]); n = len(a)
        Y = np.zeros(n * oversample // 2 + 1, dtype=complex); Y[:len(X)] = X
        y = np.fft.irfft(Y, n * oversample) * oversample
        best = max(best, float(np.max(np.abs(y))))
    return _db(best)


def rms_dbfs(x: np.ndarray, start: int = 0, stop: int | None = None) -> float:
    seg = np.asarray(x[start:stop], dtype=np.float64)
    return _db(float(np.sqrt(np.mean(seg ** 2)))) if seg.size else _FLOOR


def _biquad_response(b, a, w):
    z = np.exp(-1j * w)
    return (b[0] + b[1] * z + b[2] * z ** 2) / (a[0] + a[1] * z + a[2] * z ** 2)


def _k_weight(x: np.ndarray) -> np.ndarray:
    """BS.1770 K-weighting (48 kHz coefficients) applied via frequency response."""
    n = len(x)
    w = np.linspace(0, np.pi, n // 2 + 1)
    h1 = _biquad_response([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], w)
    h2 = _biquad_response([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], w)
    return np.fft.irfft(np.fft.rfft(x) * h1 * h2, n)


def lufs_approx(x: np.ndarray) -> float:
    """Integrated loudness (approximate BS.1770-4, stereo channel weights 1.0)."""
    a = np.asarray(x, dtype=np.float64)
    a = a[:, None] if a.ndim == 1 else a
    block, hop = int(0.4 * SR), int(0.1 * SR)
    if a.shape[0] < block:
        return _FLOOR
    kw = [_k_weight(a[:, c]) for c in range(a.shape[1])]
    z = []
    for s in range(0, a.shape[0] - block + 1, hop):
        z.append(sum(np.mean(k[s:s + block] ** 2) for k in kw))
    z = np.asarray(z)
    with np.errstate(divide="ignore"):
        lk = -0.691 + 10.0 * np.log10(np.maximum(z, 1e-20))
    g1 = z[lk > -70.0]
    if g1.size == 0:
        return _FLOOR
    rel = -0.691 + 10.0 * np.log10(np.mean(g1)) - 10.0
    g2 = z[lk > rel]
    if g2.size == 0:
        return _FLOOR
    return float(-0.691 + 10.0 * np.log10(np.mean(g2)))


def measure(x: np.ndarray) -> dict:
    return {"samples": int(np.asarray(x).shape[0]), "peak_dbfs": round(peak_dbfs(x), 2),
            "true_peak_dbfs": round(true_peak_dbfs(x), 2), "rms_dbfs": round(rms_dbfs(x), 2),
            "lufs_approx": round(lufs_approx(x), 2), "clipping": bool(np.max(np.abs(x)) > 1.0) if np.size(x) else False}


def _main_measure(path: str) -> str:
    x, _ = read_wav(path)
    return json.dumps(measure(x), indent=2, sort_keys=True)
