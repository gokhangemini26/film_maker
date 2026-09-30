"""fm post / fm qa delivery on tiny synthetic frames (skipped cleanly when ffmpeg or Pillow is missing)."""
import json

import numpy as np
import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from fm import post  # noqa: E402

needs_ffmpeg = pytest.mark.skipif(not post.ffmpeg_available(),
                                  reason="SKIPPED: ffmpeg not found (PATH or imageio_ffmpeg); encode tests did not run")

SHOTS = [("SC01_SH010", 24), ("SC01_SH020", 30), ("SC02_SH010", 42)]
TOTAL = sum(n for _, n in SHOTS)  # 96 frames = 4 s
W, H = 128, 72


def _film(project):
    start, shots = 0, {}
    for sid, n in SHOTS:
        shots[sid] = {"start": start, "frames": n}
        start += n
    (project.dir / "09_resolved").mkdir(exist_ok=True)
    (project.dir / "09_resolved" / "film.json").write_text(
        json.dumps({"format": {"fps": 24}, "total_frames": start, "shots": shots, "scenes": []}), encoding="utf-8")


def _frame(seed, i):
    x = np.linspace(0, 255, W, dtype=np.float32)[None, :].repeat(H, 0)
    y = np.linspace(40, 200, H, dtype=np.float32)[:, None].repeat(W, 1)
    v = np.clip((x * 0.5 + y * 0.5 + seed * 20 + i * 3) % 256, 30, 230).astype(np.uint8)
    return Image.fromarray(np.stack([v, v // 2 + 60, 255 - v], -1), "RGB")


def _finals(project):
    for k, (sid, n) in enumerate(SHOTS):
        d = project.dir / post.FINAL_DIR / sid
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            _frame(k, i).save(d / f"{i + 1:04d}.png")


def _previews(project):
    d = project.dir / post.PREVIEW_DIR
    d.mkdir(parents=True, exist_ok=True)
    for k, (sid, _) in enumerate(SHOTS):
        _frame(k, 0).save(d / f"{sid}.png")


def _mix(path, seconds=TOTAL / 24):
    from fm.audio.mix import write_wav

    t = np.arange(int(48000 * seconds)) / 48000
    x = (0.2 * np.sin(2 * np.pi * 220 * t))[:, None].repeat(2, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_wav(path, x.astype(np.float64))


def test_timecode_roundtrip():
    assert post.timecode(1440) == "00:01:00:00"
    assert post.tc_to_frames("00:00:02:05") == 53


def test_edl_is_exact(sandbox, tmp_path):
    _film(sandbox)
    r = post.build_edl(sandbox, tmp_path)
    ev = post.parse_edl((tmp_path / "EDIT.edl").read_text())
    assert r["events"] == len(SHOTS) == len(ev) and r["total_frames"] == TOTAL
    pos = 0
    for e, (sid, n) in zip(ev, SHOTS):
        assert e["shot"] == sid
        assert post.tc_to_frames(e["rec_in"]) == pos
        assert post.tc_to_frames(e["rec_out"]) == pos + n
        assert post.tc_to_frames(e["src_out"]) - post.tc_to_frames(e["src_in"]) == n
        pos += n
    cc = (tmp_path / "edit.ffconcat").read_text()
    assert cc.startswith("ffconcat version 1.0") and cc.count("duration ") == len(SHOTS)
    # deterministic
    a = (tmp_path / "EDIT.edl").read_bytes()
    post.build_edl(sandbox, tmp_path)
    assert (tmp_path / "EDIT.edl").read_bytes() == a


def test_edl_rejects_gap(sandbox, tmp_path):
    _film(sandbox)
    fp = sandbox.dir / "09_resolved" / "film.json"
    j = json.loads(fp.read_text())
    j["shots"]["SC01_SH020"]["start"] += 1
    fp.write_text(json.dumps(j))
    with pytest.raises(post.FMError):
        post.build_edl(sandbox, tmp_path)


@needs_ffmpeg
def test_animatic_from_stills_has_exact_length(sandbox, tmp_path):
    _film(sandbox)
    _previews(sandbox)
    r = post.build_animatic(sandbox, tmp_path, size=(128, 72), no_audio=True)
    assert r["video"]["frames"] == TOTAL and r["video"]["fps"] == 24.0
    assert r["shots_from_stills"] == 3 and not r["missing_sources"]
    assert abs(r["duration_s"] - TOTAL / 24) < 1 / 24 + 1e-3


@needs_ffmpeg
def test_animatic_with_audio_and_stale_mix(sandbox, tmp_path):
    _film(sandbox)
    _previews(sandbox)
    mix = tmp_path / "mix.wav"
    _mix(mix)
    r = post.build_animatic(sandbox, tmp_path / "o", size=(128, 72), audio=mix)
    assert r["audio"]["sample_rate"] == 48000 and r["audio"]["channels"] == 2
    _mix(mix, seconds=2.0)
    with pytest.raises(post.FMError, match="stale mix"):
        post.build_animatic(sandbox, tmp_path / "o2", size=(128, 72), audio=mix)


@needs_ffmpeg
def test_animatic_is_deterministic(sandbox, tmp_path):
    _film(sandbox)
    _previews(sandbox)
    post.build_animatic(sandbox, tmp_path / "a", size=(128, 72), no_audio=True)
    post.build_animatic(sandbox, tmp_path / "b", size=(128, 72), no_audio=True)
    assert (tmp_path / "a" / "animatic.mp4").read_bytes() == (tmp_path / "b" / "animatic.mp4").read_bytes()


@needs_ffmpeg
def test_assemble_export_and_delivery_qa(sandbox, tmp_path):
    _film(sandbox)
    _finals(sandbox)
    mix = tmp_path / "mix.wav"
    _mix(mix)
    out = tmp_path / "deliv"
    a = post.assemble(sandbox, out, audio=mix)
    assert a["video"]["frames"] == TOTAL and a["audio_info"]["sample_rate"] == 48000
    assert a["loudnorm_pass1"] and "grain" not in a["filters"] and "vignette" not in a["filters"]
    e = post.export(sandbox, out)
    man = json.loads((out / "MANIFEST.json").read_text())
    assert {f["path"] for f in man["files"]} >= {p["path"] for p in e["files"]}
    assert all(len(f["sha256"]) == 64 for f in man["files"])
    rep = post.qa_delivery(sandbox, out, resolution=(W, H), report_dir=tmp_path / "qa", fade_in=12, fade_out=18)
    fails = [(r["file"], f) for r in rep["rows"] for f in r["findings"] if f[0] == "FAIL"]
    assert not fails, fails
    assert (tmp_path / "qa" / "delivery_report.json").exists()
    assert rep["summary"]["fail"] == 0


@needs_ffmpeg
def test_assemble_grain_and_vignette_are_opt_in(sandbox, tmp_path):
    _film(sandbox)
    _finals(sandbox)
    r = post.assemble(sandbox, tmp_path, silent=True, grain=True, vignette=0.05)
    assert "noise=" in r["filters"] and "vignette=" in r["filters"]
    with pytest.raises(post.FMError, match="outside canon"):
        post.assemble(sandbox, tmp_path / "x", silent=True, vignette=0.9)


@needs_ffmpeg
def test_assemble_refuses_missing_frames_and_qa_flags_wrong_length(sandbox, tmp_path):
    _film(sandbox)
    _finals(sandbox)
    (sandbox.dir / post.FINAL_DIR / "SC01_SH020" / "0030.png").unlink()
    with pytest.raises(post.FMError, match="incomplete"):
        post.assemble(sandbox, tmp_path, silent=True)
    _previews(sandbox)
    r = post.build_animatic(sandbox, tmp_path / "an", size=(128, 72), no_audio=True)
    rep = post.qa_delivery(sandbox, files=[r["file"]], expect_frames=TOTAL + 12, resolution=(128, 72),
                           report_dir=tmp_path / "qa")
    msgs = " ".join(f[1] for row in rep["rows"] for f in row["findings"] if f[0] == "FAIL")
    n_fail = sum(1 for row in rep["rows"] for f in row["findings"] if f[0] == "FAIL")
    assert "frames" in msgs and "no audio" in msgs and n_fail >= 2
    # the summary counts findings, not files: one file with several FAIL lines reports all of them
    assert rep["summary"]["fail"] == n_fail and rep["summary"]["files_failing"] == 1 and rep["summary"]["files"] == 1


def test_delivery_summary_counts_findings_not_files():
    rows = [{"file": "a.mov", "findings": [["FAIL", "x"], ["FAIL", "y"], ["WARN", "z"], ["WARN", "w"]]},
            {"file": "b.mp4", "findings": [["WARN", "v"]]},
            {"file": "MANIFEST.json", "findings": []}]
    s = post.delivery_summary(rows, 2)
    assert s == {"files": 2, "rows": 3, "fail": 2, "warn": 3, "files_failing": 1, "files_warning": 2}
    assert post.delivery_summary([], 0)["fail"] == 0
