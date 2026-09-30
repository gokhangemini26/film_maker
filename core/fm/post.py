"""Post-production tooling (M6 tasks F2 and F4): EDL, animatic, assembly, delivery encodes, delivery QA.

The edit is generated, never authored: hard cuts in scene-then-shot order from the resolved frame table
(``09_resolved/film.json``), plus the two fades the locked ``camera.rhythm.transitions`` allows. Everything
here is deterministic (no timestamps in media, fixed grain seed, single-threaded filters) and only writes
where told to: every command takes an ``out`` override so dry runs never touch the project.

ffmpeg discovery order: ``$FM_FFMPEG`` / PATH, then ``imageio_ffmpeg``. ffprobe: PATH, else a parse of
``ffmpeg -i`` output (imageio's static binary ships no ffprobe).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .errors import FMError
from .io import now_iso
from .project import Project

FPS = 24
DEFAULT_FADE_IN_FRAMES = 12           # M6_SCOPE D7 recommendation; overridable by canon post.fade_in
DEFAULT_FADE_OUT_FRAMES = 18          # fallback only; canon camera.rhythm.transitions is read first
TARGET_LUFS = -16.0
TARGET_TP = -1.0
GRAIN_SEED = 1337
POST_DIR = "12_post"
DELIVERY_DIR = "13_delivery"
AUDIO_MIX = "12_post/audio/mix_48k_stereo.wav"
FINAL_DIR = "11_render/final"
FRAME_DIRS = ("10_blender/frames", "10_blender/playblast")
PREVIEW_DIR = "10_blender/previews"
QA_REPORT = "qa/delivery_report.json"


# ------------------------------------------------------------------------------- tools
_TOOLS: dict[str, Any] = {}


def find_ffmpeg() -> tuple[str, str]:
    """Return (path, source). Order: $FM_FFMPEG, PATH, imageio_ffmpeg."""
    import os

    env = os.environ.get("FM_FFMPEG")
    if env and Path(env).exists():
        return env, "FM_FFMPEG"
    p = shutil.which("ffmpeg")
    if p:
        return p, "PATH"
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe(), "imageio_ffmpeg"
    except Exception:
        pass
    raise FMError("ffmpeg not found: install it, or `pip install imageio-ffmpeg`, or set FM_FFMPEG")


def ffmpeg_available() -> bool:
    try:
        find_ffmpeg()
        return True
    except FMError:
        return False


def _ffmpeg() -> str:
    return find_ffmpeg()[0]


def _run(cmd: list[str], *, input_bytes: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, input=input_bytes, capture_output=True)
    if check and r.returncode != 0:
        tail = r.stderr.decode("utf-8", "replace").strip().splitlines()[-12:]
        raise FMError(f"command failed ({r.returncode}): {' '.join(cmd[:6])} ...\n" + "\n".join(tail))
    return r


def ffmpeg_version() -> str:
    out = _run([_ffmpeg(), "-version"]).stdout.decode()
    return out.splitlines()[0].strip() if out else "unknown"


def _encoders() -> str:
    if "enc" not in _TOOLS:
        _TOOLS["enc"] = _run([_ffmpeg(), "-hide_banner", "-encoders"]).stdout.decode()
    return _TOOLS["enc"]


def has_encoder(name: str) -> bool:
    return re.search(rf"^\s*[VAS][\w.]+\s+{re.escape(name)}\s", _encoders(), re.M) is not None


# ------------------------------------------------------------------------------- probe
def probe(path: str | Path) -> dict:
    """Facts about a media file: duration, fps, frames, resolution, codecs, audio rate/channels.

    Uses ffprobe when on PATH, else parses ``ffmpeg -i`` and counts frames with a null decode."""
    path = str(path)
    fp = shutil.which("ffprobe")
    if fp:
        r = _run([fp, "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
        j = json.loads(r.stdout)
        out: dict[str, Any] = {"duration_s": float(j["format"].get("duration", 0) or 0),
                               "container": j["format"].get("format_name"), "tool": "ffprobe"}
        for s in j["streams"]:
            if s["codec_type"] == "video" and "video" not in out:
                num, _, den = (s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1").partition("/")
                fps = float(num) / float(den or 1) if float(den or 1) else 0.0
                nb = s.get("nb_frames")
                out["video"] = {"codec": s["codec_name"], "width": s["width"], "height": s["height"],
                                "fps": round(fps, 4), "fps_rational": s.get("avg_frame_rate"),
                                "pix_fmt": s.get("pix_fmt"),
                                "frames": int(nb) if nb and str(nb).isdigit() else None,
                                "duration_s": float(s["duration"]) if s.get("duration") else None}
            elif s["codec_type"] == "audio" and "audio" not in out:
                out["audio"] = {"codec": s["codec_name"], "sample_rate": int(s["sample_rate"]),
                                "channels": int(s["channels"]),
                                "duration_s": float(s["duration"]) if s.get("duration") else None}
        if "video" in out and out["video"]["frames"] is None:
            out["video"]["frames"] = _count_frames(path)
        return out
    return _probe_via_ffmpeg(path)


def _count_frames(path: str) -> int:
    r = _run([_ffmpeg(), "-hide_banner", "-nostats", "-i", path, "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
             check=False)
    m = re.findall(r"frame=\s*(\d+)", r.stderr.decode("utf-8", "replace"))
    return int(m[-1]) if m else 0


def _probe_via_ffmpeg(path: str) -> dict:
    err = _run([_ffmpeg(), "-hide_banner", "-i", path], check=False).stderr.decode("utf-8", "replace")
    out: dict[str, Any] = {"tool": "ffmpeg-parse"}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    out["duration_s"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    out["container"] = None
    v = re.search(r"Stream #\S+.*?Video:\s*(\w+)[^\n]*?,\s*(\w+)[^\n]*?,\s*(\d+)x(\d+)[^\n]*?,\s*([\d.]+) fps", err)
    if v:
        out["video"] = {"codec": v[1], "pix_fmt": v[2], "width": int(v[3]), "height": int(v[4]),
                        "fps": float(v[5]), "fps_rational": None, "frames": _count_frames(path)}
        out["video"]["duration_s"] = out["video"]["frames"] / out["video"]["fps"] if out["video"]["fps"] else None
    a = re.search(r"Stream #\S+.*?Audio:\s*(\w+)[^\n]*?,\s*(\d+) Hz,\s*([^,\n]+)", err)
    if a:
        lay = a[3].strip()
        ch = {"mono": 1, "stereo": 2, "5.1": 6}.get(lay.split("(")[0], 2 if "stereo" in lay else 0)
        out["audio"] = {"codec": a[1], "sample_rate": int(a[2]), "channels": ch, "duration_s": out["duration_s"]}
    return out


# ------------------------------------------------------------------------------- frame table + canon
def timecode(frame: int, fps: int = FPS) -> str:
    """Non-drop timecode HH:MM:SS:FF."""
    if frame < 0:
        raise ValueError("negative frame")
    f = frame % fps
    s = frame // fps
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{f:02d}"


def load_table(project: Project) -> dict:
    """The resolved frame table, checked to be contiguous, ordered, and to sum to total_frames."""
    fp = project.dir / "09_resolved" / "film.json"
    if not fp.exists():
        raise FMError("09_resolved/film.json missing: run `fm resolve` first")
    film = json.loads(fp.read_text(encoding="utf-8"))
    fps = int((film.get("format") or {}).get("fps", FPS))
    if fps != FPS:
        raise FMError(f"post tooling is built for {FPS} fps; the film is {fps}")
    rows = sorted(({"shot": k, "start": int(v["start"]), "frames": int(v["frames"])}
                   for k, v in film["shots"].items()), key=lambda r: r["start"])
    cur = 0
    for r in rows:
        if r["start"] != cur:
            raise FMError(f"frame table is not contiguous at {r['shot']}: starts {r['start']}, expected {cur}")
        if r["frames"] < 1:
            raise FMError(f"{r['shot']} has no frames")
        cur += r["frames"]
    total = int(film.get("total_frames", cur))
    if total != cur:
        raise FMError(f"frame table sums to {cur} but film.total_frames is {total}")
    scenes = {s["scene_id"]: s for s in film.get("scenes", [])}
    for r in rows:
        r["scene"] = r["shot"].split("_")[0]
    return {"rows": rows, "total": total, "fps": fps, "format": film.get("format") or {}, "scenes": scenes}


def finish_params(project: Project) -> dict:
    """Locked finish parameters, read from canon (never hard-coded where canon has them)."""
    loaded = project.load()

    def val(cid: str) -> dict:
        c = loaded.canon.get(cid)
        return dict(c.entry.value) if c is not None and isinstance(c.entry.value, dict) else {}

    tr = val("camera.rhythm.transitions")
    fo = tr.get("fade_out") if isinstance(tr.get("fade_out"), dict) else {}
    tex = val("look.style.texture_and_grain")
    grain = tex.get("grain") if isinstance(tex.get("grain"), dict) else {}
    post = val("post.fade_in")
    fmt = val("camera.format")
    aud = val("audio.mix")
    return {
        "fade_in_frames": int(post.get("frames", DEFAULT_FADE_IN_FRAMES)),
        "fade_in_source": "canon post.fade_in" if "frames" in post else "default (M6_SCOPE D7 recommendation)",
        "fade_out_frames": int(fo.get("frames", DEFAULT_FADE_OUT_FRAMES)),
        "fade_out_source": "canon camera.rhythm.transitions" if "frames" in fo else "default",
        "grain_amplitude_luma": float(grain.get("amplitude_luma", 0.015)),
        "vignette_max": float(tex.get("vignette_max", 0.1)),
        "resolution": tuple(fmt.get("resolution_px", (1920, 1080))),
        "loudness_lufs": float(aud.get("loudness_lufs", TARGET_LUFS)) if isinstance(aud.get("loudness_lufs", TARGET_LUFS), (int, float)) else TARGET_LUFS,
    }


def _rel_out(project: Project, out: str | Path | None, default: str) -> Path:
    p = Path(out) if out else project.dir / default
    p.mkdir(parents=True, exist_ok=True)
    return p


def _record(project: Project, ref: str, file: Path, producer: str) -> None:
    """Record a derived node, only for files inside the project; failure never blocks the tool."""
    try:
        from .ops import record_derived

        file.resolve().relative_to(project.dir.resolve())
        table = load_table(project)
        record_derived(project, ref, [f"resolved:{r['shot']}" for r in table["rows"]], file=file, producer=producer)
    except Exception:
        pass


# ------------------------------------------------------------------------------- EDL + ffconcat
def preview_still(project: Project, shot: str, base: Path | None = None) -> Path | None:
    p = (base or project.dir / PREVIEW_DIR) / f"{shot}.png"
    return p if p.exists() else None


def build_edl(project: Project, out: str | Path | None = None, title: str | None = None) -> dict:
    """CMX3600 EDL (24 fps non-drop) and ffconcat list from the frame table. Exact and deterministic."""
    t = load_table(project)
    fin = finish_params(project)
    od = _rel_out(project, out, POST_DIR)
    fi, fo = fin["fade_in_frames"], fin["fade_out_frames"]
    total = t["total"]
    if fi + fo >= total:
        raise FMError("fades longer than the film")
    lines = [f"TITLE: {title or project.slug.upper()}", "FCM: NON-DROP FRAME", ""]
    lines += [f"* FILM {total} FRAMES @ {FPS} FPS = {timecode(total)}",
              f"* FADE IN {fi} FRAMES FROM BLACK AT {timecode(0)} (source: {fin['fade_in_source']})",
              f"* FADE OUT {fo} FRAMES TO BLACK AT {timecode(total - fo)} (source: {fin['fade_out_source']})",
              "* ALL OTHER TRANSITIONS ARE HARD CUTS (camera.rhythm.transitions)", ""]
    for i, r in enumerate(t["rows"], 1):
        s, n = r["start"], r["frames"]
        lines.append(f"{i:03d}  AX       V     C        {timecode(0)} {timecode(n)} {timecode(s)} {timecode(s + n)}")
        lines.append(f"* FROM CLIP NAME: {r['shot']}")
        if i == 1:
            lines.append(f"* FADE IN {fi} FRAMES")
        if i == len(t["rows"]):
            lines.append(f"* FADE OUT {fo} FRAMES")
    edl = "\n".join(lines) + "\n"
    (od / "EDIT.edl").write_text(edl, encoding="utf-8", newline="\n")

    cl = ["ffconcat version 1.0", f"# {project.slug}: {total} frames @ {FPS} fps; one still per shot for the animatic"]
    prev = project.dir / PREVIEW_DIR
    for r in t["rows"]:
        still = preview_still(project, r["shot"])
        rel = Path("..") / PREVIEW_DIR / f"{r['shot']}.png" if od.resolve() == (project.dir / POST_DIR).resolve() \
            else prev / f"{r['shot']}.png"
        cl.append(f"# {r['shot']} frames {r['start']}-{r['start'] + r['frames'] - 1}"
                  + ("" if still else " (NO PREVIEW STILL)"))
        cl.append(f"file '{str(rel).replace(chr(92), '/')}'")
        cl.append(f"duration {r['frames'] / FPS:.9f}")
    last = t["rows"][-1]["shot"]
    rel_last = Path("..") / PREVIEW_DIR / f"{last}.png" if od.resolve() == (project.dir / POST_DIR).resolve() \
        else prev / f"{last}.png"
    cl.append(f"file '{str(rel_last).replace(chr(92), '/')}'")   # concat demuxer quirk: last file repeated
    (od / "edit.ffconcat").write_text("\n".join(cl) + "\n", encoding="utf-8", newline="\n")
    _record(project, "edit:edl", od / "EDIT.edl", "fm.post.edl")
    return {"edl": str(od / "EDIT.edl"), "ffconcat": str(od / "edit.ffconcat"), "events": len(t["rows"]),
            "total_frames": total, "end_timecode": timecode(total), "fade_in": fi, "fade_out": fo}


def parse_edl(text: str) -> list[dict]:
    """Read back the events of an EDL written by build_edl (used by tests and QA)."""
    ev = []
    for ln in text.splitlines():
        m = re.match(r"^(\d{3})\s+(\S+)\s+V\s+C\s+(\S+) (\S+) (\S+) (\S+)$", ln)
        if m:
            ev.append({"n": int(m[1]), "reel": m[2], "src_in": m[3], "src_out": m[4], "rec_in": m[5], "rec_out": m[6]})
        m = re.match(r"^\* FROM CLIP NAME: (\S+)$", ln)
        if m and ev:
            ev[-1]["shot"] = m[1]
    return ev


def tc_to_frames(tc: str) -> int:
    h, m, s, f = (int(x) for x in tc.split(":"))
    return ((h * 60 + m) * 60 + s) * FPS + f


# ------------------------------------------------------------------------------- animatic
def _font(size: int):
    from PIL import ImageFont

    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def _shot_frame_files(project: Project, shot: str, count: int) -> tuple[list[Path], str]:
    for d in FRAME_DIRS:
        fd = project.dir / d / shot
        if fd.is_dir():
            files = sorted(fd.glob("*.png"))
            if files:
                return files, d
    return [], ""


def _canvas(im, size: tuple[int, int]):
    from PIL import Image

    w, h = size
    im = im.convert("RGB")
    s = min(w / im.width, h / im.height)
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    bg = Image.new("RGB", (w, h), (0, 0, 0))
    bg.paste(im, ((w - nw) // 2, (h - nh) // 2))
    return bg


def _stamp(im, text: str, size: tuple[int, int]):
    from PIL import ImageDraw

    d = ImageDraw.Draw(im)
    f = _font(max(12, size[1] // 30))
    x, y = 12, 10
    bb = d.textbbox((x, y), text, font=f)
    d.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill=(0, 0, 0))
    d.text((x, y), text, fill=(255, 255, 255), font=f)
    return im


def _x264_args(crf: int = 18) -> list[str]:
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-x264-params", "threads=1:bframes=2:keyint=48:min-keyint=48:scenecut=0", "-bf", "2",
            "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def build_animatic(project: Project, out: str | Path | None = None, size: tuple[int, int] = (1280, 720),
                   audio: str | Path | None = None, stamp: bool = True, no_audio: bool = False) -> dict:
    """12_post/animatic.mp4: rendered frames per shot when present, else the preview still held for the shot's
    duration with the shot id stamped; muxed with the mix if present, else silent. H.264 yuv420p 24 fps."""
    from PIL import Image

    t = load_table(project)
    od = _rel_out(project, out, POST_DIR)
    dest = od / "animatic.mp4"
    mix = Path(audio) if audio else project.dir / AUDIO_MIX
    has_audio = mix.exists() and not no_audio
    total = t["total"]
    w, h = size
    w -= w % 2
    h -= h % 2
    size = (w, h)
    if has_audio:
        # the mix must be the film's length: a mismatch is a stale mix, not something to pad silently
        from .audio.mix import read_wav

        x, sr = read_wav(mix)
        exp = total * (sr // FPS)
        if sr != 48000 or x.shape[0] != exp:
            raise FMError(f"{mix.name}: {x.shape[0]} samples at {sr} Hz, expected {exp} at 48000 "
                          f"({total} frames): stale mix, rebuild it or pass --no-audio")
    sources: dict[str, str] = {}
    cmd = [_ffmpeg(), "-hide_banner", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-framerate", str(FPS), "-i", "-"]
    if has_audio:
        cmd += ["-i", str(mix)]
    cmd += ["-map", "0:v"] + (["-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"] if has_audio else [])
    cmd += _x264_args(18) + ["-r", str(FPS), "-fflags", "+bitexact", "-flags:v", "+bitexact",
                             "-map_metadata", "-1", "-movflags", "+faststart", "-frames:v", str(total), str(dest)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    missing = []
    try:
        for r in t["rows"]:
            files, srcdir = _shot_frame_files(project, r["shot"], r["frames"])
            n = r["frames"]
            if files:
                sources[r["shot"]] = f"frames:{srcdir}"
                for i in range(n):
                    f = files[min(i, len(files) - 1)]
                    im = _canvas(Image.open(f), size)
                    if stamp:
                        im = _stamp(im, f"{r['shot']}  f{i:03d}/{n}", size)
                    proc.stdin.write(im.tobytes())
                continue
            still = preview_still(project, r["shot"])
            if still is None:
                missing.append(r["shot"])
                im = Image.new("RGB", size, (24, 24, 24))
                sources[r["shot"]] = "placeholder"
            else:
                im = _canvas(Image.open(still), size)
                sources[r["shot"]] = "preview_still"
            if stamp:
                im = _stamp(im, r["shot"], size)
            raw = im.tobytes()
            for _ in range(n):
                proc.stdin.write(raw)
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "replace")
        rc = proc.wait()
    except BrokenPipeError:
        err = proc.stderr.read().decode("utf-8", "replace")
        rc = proc.wait()
    if rc != 0:
        raise FMError("animatic encode failed:\n" + "\n".join(err.strip().splitlines()[-10:]))
    info = probe(dest)
    _record(project, "edit:animatic", dest, "fm.post.animatic")
    kinds = sorted(set(v.split(":")[0] for v in sources.values()))
    return {"file": str(dest), "duration_s": info["duration_s"], "video": info.get("video"), "audio": info.get("audio"),
            "with_audio": has_audio, "size": list(size), "total_frames": total, "sources": kinds,
            "shots_from_stills": sum(v == "preview_still" for v in sources.values()),
            "shots_from_frames": sum(v.startswith("frames") for v in sources.values()),
            "missing_sources": missing, "bytes": dest.stat().st_size}


# ------------------------------------------------------------------------------- assemble
def _final_frames(project: Project, final_dir: Path, t: dict) -> dict[str, list[Path]]:
    got, problems = {}, []
    for r in t["rows"]:
        d = final_dir / r["shot"]
        files = sorted(d.glob("*.png")) if d.is_dir() else []
        if len(files) != r["frames"]:
            problems.append(f"{r['shot']}: {len(files)} frames, expected {r['frames']}")
        got[r["shot"]] = files
    if problems:
        raise FMError("final frames incomplete (" + str(len(problems)) + " shot(s)): " + "; ".join(problems[:8]))
    return got


def _loudnorm(src: Path, dst: Path, dur_s: float, target: float, tp: float) -> dict:
    """Two-pass loudnorm to a 24-bit 48 kHz stereo wav padded/trimmed to dur_s. Returns pass-1 measurements."""
    ff = _ffmpeg()
    ln = f"loudnorm=I={target}:TP={tp}:LRA=11"
    r = _run([ff, "-hide_banner", "-nostats", "-i", str(src), "-af", ln + ":print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr.decode("utf-8", "replace"), re.S)
    if not m:
        raise FMError("loudnorm pass 1 produced no measurement")
    ms = json.loads(m.group(0))
    if ms["input_i"] in ("-inf", "inf"):
        raise FMError("the mix is digital silence: nothing to normalise")
    p2 = (f"{ln}:measured_I={ms['input_i']}:measured_TP={ms['input_tp']}:measured_LRA={ms['input_lra']}:"
          f"measured_thresh={ms['input_thresh']}:offset={ms['target_offset']}:linear=true,"
          f"aresample=48000,apad=whole_dur={dur_s:.6f},atrim=end={dur_s:.6f}")
    _run([ff, "-hide_banner", "-y", "-loglevel", "error", "-i", str(src), "-af", p2, "-ar", "48000", "-ac", "2",
          "-c:a", "pcm_s24le", "-map_metadata", "-1", str(dst)])
    return {k: ms[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def _vignette_angle(amount: float) -> float:
    """Corner darkening of ffmpeg's vignette is cos^4(angle) at the corner: solve for the given amount."""
    return math.acos((1.0 - amount) ** 0.25)


def build_grain_filter(amplitude_luma: float) -> str:
    """Monochrome temporal grain: luma only, fixed seed. Amplitude is a fraction of full range."""
    s = max(1, round(amplitude_luma * 255))
    return f"noise=c0_seed={GRAIN_SEED}:c0s={s}:c0f=t+u:c1s=0:c2s=0"


def assemble(project: Project, out: str | Path | None = None, *, frames_dir: str | Path | None = None,
             audio: str | Path | None = None, grain: bool = False, vignette: float = 0.0,
             fade_in: int | None = None, fade_out: int | None = None, silent: bool = False,
             name: str | None = None) -> dict:
    """Master from final frames: [grain] -> [vignette] -> fades -> audio (loudnorm 2-pass) -> mezzanine.

    Grain and vignette are OFF unless asked (flags); their strength comes from look canon."""
    t = load_table(project)
    fin = finish_params(project)
    od = _rel_out(project, out, DELIVERY_DIR)
    fdir = Path(frames_dir) if frames_dir else project.dir / FINAL_DIR
    frames = _final_frames(project, fdir, t)
    fi = fin["fade_in_frames"] if fade_in is None else int(fade_in)
    fo = fin["fade_out_frames"] if fade_out is None else int(fade_out)
    total = t["total"]
    if vignette and not (0 < vignette <= fin["vignette_max"]):
        raise FMError(f"vignette {vignette} is outside canon look.style.texture_and_grain (max {fin['vignette_max']})")
    mix = Path(audio) if audio else project.dir / AUDIO_MIX
    if not mix.exists() and not silent:
        raise FMError(f"{mix} missing: build the mix, or pass --silent to assemble without sound")
    dur = total / FPS
    prores = has_encoder("prores_ks")
    master = od / f"{name or project.slug}_master.{'mov' if prores else 'mkv'}"

    chain = ["format=rgb24"]
    if grain:
        chain.append(build_grain_filter(fin["grain_amplitude_luma"]))
    if vignette:
        chain.append(f"vignette=angle={_vignette_angle(vignette):.6f}:mode=forward:eval=init")
    if fi:
        chain.append(f"fade=t=in:s=0:n={fi}")
    if fo:
        chain.append(f"fade=t=out:s={total - fo}:n={fo}")
    chain.append("scale=in_range=full:out_range=tv:flags=accurate_rnd+full_chroma_int,format=" + ("yuv422p10le" if prores else "yuv420p"))
    vf = ",".join(chain)

    with tempfile.TemporaryDirectory(prefix="fm_assemble_") as td:
        tdp = Path(td)
        seq = tdp / "seq"
        seq.mkdir()
        i = 0
        for r in t["rows"]:
            for f in frames[r["shot"]]:
                i += 1
                link = seq / f"{i:06d}.png"
                try:
                    link.symlink_to(f.resolve())
                except OSError:
                    shutil.copyfile(f, link)
        loud = None
        cmd = [_ffmpeg(), "-hide_banner", "-y", "-loglevel", "error", "-framerate", str(FPS),
               "-i", str(seq / "%06d.png")]
        if not silent:
            wav = tdp / "audio_norm.wav"
            loud = _loudnorm(mix, wav, dur, fin["loudness_lufs"], TARGET_TP)
            cmd += ["-i", str(wav)]
        cmd += ["-filter_threads", "1", "-vf", vf, "-map", "0:v"] + (["-map", "1:a", "-c:a", "pcm_s24le"] if not silent else [])
        if prores:
            cmd += ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", "-bits_per_mb", "8000"]
        else:
            cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "8", "-x264-params", "threads=1"]
        cmd += ["-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-r", str(FPS), "-frames:v", str(total), "-fflags", "+bitexact", "-flags:v", "+bitexact",
                "-flags:a", "+bitexact", "-map_metadata", "-1", str(master)]
        _run(cmd)
    info = probe(master)
    return {"master": str(master), "codec": "prores_ks 422 HQ" if prores else "libx264 crf8 (ProRes unavailable)",
            "filters": vf, "fade_in": fi, "fade_out": fo, "grain": grain, "vignette": vignette,
            "audio": (not silent), "loudnorm_pass1": loud, "duration_s": info["duration_s"],
            "video": info.get("video"), "audio_info": info.get("audio")}


# ------------------------------------------------------------------------------- export + manifest
def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_master(od: Path) -> Path | None:
    for pat in ("*_master.mov", "*_master.mkv"):
        c = sorted(od.glob(pat))
        if c:
            return c[0]
    return None


def export(project: Project, out: str | Path | None = None, *, master: str | Path | None = None,
           proxy: bool = True, name: str | None = None) -> dict:
    """Delivery encodes from the master: web MP4 (H.264 High ~12 Mbps, AAC 320k, +faststart) and an optional
    640 px review proxy; writes MANIFEST.json (files, sha256, probe facts) covering the master and encodes."""
    od = _rel_out(project, out, DELIVERY_DIR)
    src = Path(master) if master else _find_master(od)
    if src is None or not src.exists():
        raise FMError(f"no master in {od}: run `fm post assemble` first (or pass --master)")
    slug = name or project.slug
    ff = _ffmpeg()
    common = ["-hide_banner", "-y", "-loglevel", "error", "-i", str(src), "-fflags", "+bitexact",
              "-flags:v", "+bitexact", "-flags:a", "+bitexact", "-map_metadata", "-1"]
    web = od / f"{slug}_1080p.mp4"
    _run([ff, *common, "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
          "-b:v", "12M", "-maxrate", "14M", "-bufsize", "24M", "-x264-params", "threads=1:keyint=48:min-keyint=48",
          "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
          "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(web)])
    made = [src, web]
    if proxy:
        px = od / f"{slug}_proxy_640.mp4"
        _run([ff, *common, "-vf", "scale=640:-2:flags=bicubic", "-c:v", "libx264", "-preset", "medium", "-crf", "26",
              "-pix_fmt", "yuv420p", "-x264-params", "threads=1", "-c:a", "aac", "-b:a", "96k", "-ar", "48000", "-ac", "2",
              "-movflags", "+faststart", str(px)])
        made.append(px)
    fin = finish_params(project)
    files = []
    for f in made:
        pr = probe(f)
        files.append({"path": f.name, "bytes": f.stat().st_size, "sha256": _sha256(f), "probe": pr})
    from . import __version__

    manifest = {"schema": "fm.delivery_manifest/1", "project": project.slug, "created": now_iso(),
                "fm_version": __version__, "ffmpeg": ffmpeg_version(), "ffmpeg_source": find_ffmpeg()[1],
                "fps": FPS, "loudness_target": {"lufs": fin["loudness_lufs"], "true_peak_dbtp": TARGET_TP},
                "files": files}
    rm = project.dir / FINAL_DIR / "MANIFEST.json"
    if rm.exists():
        manifest["render_manifest_sha256"] = _sha256(rm)
    mp = od / "MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    _record(project, "render:delivery", mp, "fm.post.export")
    return {"manifest": str(mp), "files": [{k: f[k] for k in ("path", "bytes", "sha256")} for f in files]}


# ------------------------------------------------------------------------------- delivery QA
def _measure_loudness(path: Path) -> dict | None:
    r = _run([_ffmpeg(), "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af",
              "ebur128=peak=true", "-f", "null", "-"], check=False)
    err = r.stderr.decode("utf-8", "replace")
    i = err.rfind("Summary:")
    if i < 0:
        return None
    s = err[i:]
    lu = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", s)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", s)
    return {"integrated_lufs": float(lu[1]) if lu else None, "true_peak_dbtp": float(tp[1]) if tp else None}


def _edge_luma(path: Path, start: float, dur: float, w: int = 160) -> list[float]:
    """Per-frame mean luma (0-255) of a window, read as raw gray at a small size."""
    r = _run([_ffmpeg(), "-hide_banner", "-loglevel", "error", "-ss", f"{start:.6f}", "-t", f"{dur:.6f}", "-i",
              str(path), "-map", "0:v:0", "-vf", f"scale={w}:-2,format=gray", "-f", "rawvideo", "-"])
    import numpy as np

    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    if buf.size == 0:
        return []
    h = int(round(w * 9 / 16 / 2) * 2)
    n = buf.size // (w * h)
    if n == 0:
        return []
    fr = buf[: n * w * h].reshape(n, w * h).astype(np.float64)
    return [float(x) for x in fr.mean(axis=1)]


def delivery_summary(rows: list[dict], n_files: int) -> dict:
    """Summary of a delivery report. `fail`/`warn` count FINDINGS (every FAIL/WARN line), not files; the
    per-file counts are kept separately as `files_failing`/`files_warning`. `files` is the number of delivery
    files probed; `rows` also includes the MANIFEST row (or the "no delivery files" row)."""
    def findings(sev: str) -> int:
        return sum(1 for r in rows for x in r["findings"] if x[0] == sev)

    def failing(sev: str) -> int:
        return sum(any(x[0] == sev for x in r["findings"]) for r in rows)

    return {"files": n_files, "rows": len(rows), "fail": findings("FAIL"), "warn": findings("WARN"),
            "files_failing": failing("FAIL"), "files_warning": failing("WARN")}


def qa_delivery(project: Project, out: str | Path | None = None, *, files: list[str | Path] | None = None,
                expect_frames: int | None = None, resolution: tuple[int, int] | None = None,
                report_dir: str | Path | None = None, target_lufs: float | None = None,
                fade_in: int | None = None, fade_out: int | None = None) -> dict:
    """ffprobe-based delivery checks, report shaped like qa_stills: {"summary": {...}, "rows": [...]}."""
    od = Path(out) if out else project.dir / DELIVERY_DIR
    fin = finish_params(project)
    total = expect_frames if expect_frames is not None else load_table(project)["total"]
    res = tuple(resolution) if resolution else tuple(fin["resolution"])
    fi = fin["fade_in_frames"] if fade_in is None else fade_in
    fo = fin["fade_out_frames"] if fade_out is None else fade_out
    target = fin["loudness_lufs"] if target_lufs is None else target_lufs
    cands = [Path(f) for f in files] if files else sorted(p for p in od.glob("*") if p.suffix in (".mov", ".mkv", ".mp4"))
    rows: list[dict] = []
    if not cands:
        rows.append({"file": str(od), "findings": [["FAIL", "no delivery files found"]]})
    for f in cands:
        row: dict[str, Any] = {"file": f.name, "findings": []}
        rows.append(row)
        fnd = row["findings"]
        try:
            pr = probe(f)
        except FMError as exc:
            fnd.append(["FAIL", f"unreadable: {exc}"])
            continue
        row["probe"] = pr
        proxy = "proxy" in f.name
        v = pr.get("video")
        if not v:
            fnd.append(["FAIL", "no video stream"])
            continue
        dur = pr["duration_s"]
        want = total / FPS
        vdur = v.get("duration_s") or dur
        if abs(v["fps"] - FPS) > 0.001:
            fnd.append(["FAIL", f"frame rate {v['fps']} (expected exactly {FPS})"])
        if v.get("frames") is not None and abs(v["frames"] - total) > 1:
            fnd.append(["FAIL", f"{v['frames']} frames, expected {total} (+-1)"])
        elif v.get("frames") is not None and v["frames"] != total:
            fnd.append(["WARN", f"{v['frames']} frames, expected {total} (within 1 frame)"])
        if abs(vdur - want) > 1.0 / FPS + 1e-3:
            fnd.append(["FAIL", f"video duration {vdur:.3f} s, expected {want:.3f} s +-1 frame"])
        if not proxy and (v["width"], v["height"]) != res:
            fnd.append(["FAIL", f"resolution {v['width']}x{v['height']}, render canon says {res[0]}x{res[1]}"])
        a = pr.get("audio")
        if not a:
            fnd.append(["FAIL", "no audio stream"])
        else:
            if a["sample_rate"] != 48000:
                fnd.append(["FAIL", f"audio {a['sample_rate']} Hz, expected 48000"])
            if a["channels"] != 2:
                fnd.append(["FAIL", f"audio has {a['channels']} channel(s), expected stereo"])
            adur = a.get("duration_s") or dur
            if abs(adur - want) > 1.0 / FPS + 1e-3:
                fnd.append(["FAIL", f"audio duration {adur:.3f} s, expected {want:.3f} s +-1 frame"])
            ld = _measure_loudness(f)
            row["loudness"] = ld
            if ld and ld["integrated_lufs"] is not None:
                if abs(ld["integrated_lufs"] - target) > 1.0:
                    fnd.append(["FAIL" if abs(ld["integrated_lufs"] - target) > 2.0 else "WARN",
                                f"integrated loudness {ld['integrated_lufs']} LUFS, target {target} +-1"])
                if ld["true_peak_dbtp"] is not None and ld["true_peak_dbtp"] > TARGET_TP + 0.1:
                    fnd.append(["FAIL", f"true peak {ld['true_peak_dbtp']} dBTP above {TARGET_TP}"])
            elif ld is None:
                fnd.append(["WARN", "loudness could not be measured"])
        # head and tail: the fades are black by design at their extreme frame only, and the picture must move
        # out of black inside the fade-in and not be frozen through the last frames before the fade-out
        head = _edge_luma(f, 0, max(fi + 12, 24) / FPS)
        tail = _edge_luma(f, max(0.0, vdur - (fo + 24) / FPS), (fo + 24) / FPS)
        if head:
            row["head_luma"] = [round(x, 1) for x in head[:3]] + ["..."] + [round(head[-1], 1)]
            if head[-1] < 4.0 and max(head) < 4.0:
                fnd.append(["FAIL", "head stays black through and after the fade-in"])
            elif fi and head[0] > 40.0:
                fnd.append(["WARN", "first frame is not black although a fade-in is specified"])
            elif not fi and head[0] < 2.0:
                fnd.append(["FAIL", "black first frame with no fade-in specified"])
        if tail:
            row["tail_luma"] = [round(tail[0], 1), "...", *[round(x, 1) for x in tail[-3:]]]
            pre = tail[: max(1, len(tail) - fo)]
            if len(pre) > 6 and max(pre) - min(pre) < 1e-6 and all(x < 4.0 for x in pre):
                fnd.append(["FAIL", "black frames before the fade-out"])
            if fo and tail[-1] > 8.0:
                fnd.append(["WARN", "last frame is not black although a fade-out is specified"])
    mp = od / "MANIFEST.json"
    if not files:
        if not mp.exists():
            rows.append({"file": "MANIFEST.json", "findings": [["FAIL", "MANIFEST.json missing"]]})
        else:
            man = json.loads(mp.read_text(encoding="utf-8"))
            bad = []
            for e in man.get("files", []):
                fp = od / e["path"]
                if not fp.exists() or _sha256(fp) != e["sha256"]:
                    bad.append(e["path"])
            rows.append({"file": "MANIFEST.json", "findings": (
                [["FAIL", "checksum mismatch or missing file: " + ", ".join(bad)]] if bad else [])})
    summary = delivery_summary(rows, len(cands))
    report = {"summary": summary, "rows": rows}
    rd = Path(report_dir) if report_dir else project.dir / "qa"
    rd.mkdir(parents=True, exist_ok=True)
    rp = rd / "delivery_report.json"
    rp.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    _record(project, "qa:delivery", rp, "fm.qa.delivery")
    report["report_file"] = str(rp)
    return report
