"""Deterministic procedural audio: recipes and the sample-exact mixer (M6 E2). Outputs go to tmp_path only."""

import hashlib
import subprocess
import sys

import numpy as np
import pytest

from fm.audio import mix, synth

SILENCE = {"amb.silence"}


def _h(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def _dur(name):
    return synth.REGISTRY[name]["default_duration"]


@pytest.mark.parametrize("name", sorted(synth.REGISTRY))
def test_recipe_contract(name):
    d = _dur(name)
    a = synth.render(name, d, seed=7, params={})
    b = synth.render(name, d, seed=7, params={})
    assert _h(a) == _h(b), "same inputs must give identical bytes"
    assert a.dtype == np.float32
    assert a.shape[0] == round(d * 48000)
    ch = synth.REGISTRY[name]["channels"]
    assert a.ndim == (1 if ch == 1 else 2)
    assert np.all(np.isfinite(a))
    assert float(np.max(np.abs(a))) <= 1.0
    if name in SILENCE:
        assert not np.any(a)
    else:
        assert float(np.max(np.abs(a))) > 0.05, "recipe is unexpectedly silent"
    e = synth.REGISTRY[name]
    assert e["desc"] and isinstance(e["serves"], list)
    if name.startswith("body.") or "placeholder" in name:
        assert e["placeholder"] and "PLACEHOLDER" in e["desc"]


def test_seed_changes_noise_recipes():
    assert _h(synth.render("ui.key_tap", 0.06, 1)) != _h(synth.render("ui.key_tap", 0.06, 2))


def test_exact_lengths_for_frame_durations():
    for f in (1, 11, 24, 33):
        assert synth.render_frames("ui.tap", f).shape[0] == f * 2000
    assert synth.render("amb.silence", 1.5).shape[0] == 72000


def test_hum_die_is_exact_zero_after_die():
    x = synth.render("hum.fridge", 1.0, 3, {"die_at": 0.25, "die_dur": 0.1})
    assert np.any(x[:10000]) and not np.any(x[int(0.36 * 48000):])


def test_engine_die_silent_after_stop():
    x = synth.render("car.engine_die", 0.5, 1)
    assert not np.any(x[int(0.56 * 48000):])


def test_ratchet_clicks_land_on_frame_grid():
    times = synth.ratchet_times(2.0, 1.0, first_at=0.0)
    assert times == [0.0, 1.0]
    x = synth.render("crank.ratchet", 2.0, 5, {"click_times": [0.5, 1.5]})
    assert not np.any(x[:24000 - 1]) and np.any(x[24000:24200])
    v = synth.render("crank.ratchet", 4.0, 5, {"rate_start_hz": 1.0, "rate_end_hz": 3.0})
    assert v.shape[0] == 192000 and len(synth.ratchet_times(4.0, 1.0, 3.0)) > 4


def test_ring_pulse_placement_sample_exact():
    tl = mix.Timeline(48)
    ring = synth.render_frames("ui.ring_tone", 11, 1)
    for f in (0, 11, 22):
        s, e = tl.add_cue("ui", ring, at_frame=f, gain_db=-12)
        assert s == f * 2000 and e == s + 22000
    st = tl.stems["ui"]
    # silence from f33 onward, non-silence exactly from the frame start
    assert not np.any(st[33 * 2000:])
    assert np.any(st[0:2000]) and np.any(st[11 * 2000:11 * 2000 + 200])
    assert mix.frame_to_sample(56) == 112000


def test_cue_first_sample_is_at_boundary():
    click = synth.render("crank.click", 0.09, 1)
    assert click[0] != 0 or click[1] != 0
    tl = mix.Timeline(30)
    s, _ = tl.add_cue("sfx", click, at_frame=7, offset_f=2)
    st = tl.stems["sfx"]
    assert s == 9 * 2000
    assert not np.any(st[:s]) and np.any(st[s:s + 50])


def test_gain_pan_fades_and_truncation():
    one = np.ones(4000, dtype=np.float32)
    tl = mix.Timeline(10)
    tl.add_cue("a", one, 1, gain_db=-6.0206, pan=-1.0)
    a = tl.stems["a"]
    assert abs(a[2000 + 5, 0] - 0.5) < 1e-3 and abs(a[2005, 1]) < 1e-6
    tl.add_cue("b", one, 1, pan=0.0)
    assert abs(tl.stems["b"][2500, 0] - np.sqrt(0.5)) < 1e-3
    tl.add_cue("c", one, 0, fade_in_f=1, fade_out_f=1)
    c = tl.stems["c"][:, 0]
    assert c[0] == 0.0 and c[1000] < c[1999] < 1.01 * np.sqrt(0.5) and c[3999] < 0.01
    tl.add_cue("d", np.ones(20000, dtype=np.float32), 9, end_frame=9.5)
    assert np.count_nonzero(tl.stems["d"][:, 0]) == 1000  # end_frame truncates
    tl.add_cue("e", np.ones(50000, dtype=np.float32), 8)  # cut at timeline end
    assert tl.stems["e"].shape[0] == 20000 and np.count_nonzero(tl.stems["e"][:, 0]) == 4000


def test_bed_xfade_and_tiling():
    tl = mix.Timeline(20)
    tl.add_bed("amb", np.ones(3000, dtype=np.float32), 2, 12, xfade_f=2)
    b = tl.stems["amb"][:, 0]
    assert not np.any(b[:4000]) and not np.any(b[24000:])
    assert b[4000] == 0.0 and b[12000] > 0.6


def test_mix_determinism_and_files(tmp_path):
    spec = {"total_frames": 60,
            "beds": [{"stem": "amb", "recipe": "amb.street_dusk", "seed": 1, "from_f": 0, "to_f": 60, "xfade_f": 6, "gain_db": -30}],
            "cues": [{"stem": "ui", "recipe": "ui.ring_tone", "seed": 3, "at_f": 0, "duration_f": 11, "gain_db": -12, "fade": {"out_f": 2}},
                     {"stem": "sfx", "recipe": "fx.plastic_clunk", "seed": 2, "at_f": 31, "gain_db": -9, "pan": 0.2}]}
    p1 = mix.mix_from_spec(spec).write(tmp_path / "a")
    p2 = mix.mix_from_spec(spec).write(tmp_path / "b")
    assert p1["master"].read_bytes() == p2["master"].read_bytes()
    x, sr = mix.read_wav(p1["master"])
    assert sr == 48000 and x.shape == (60 * 2000, 2)
    assert set(p1) == {"stem_amb", "stem_ui", "stem_sfx", "master"}
    m = mix.measure(x)
    assert m["peak_dbfs"] <= -1.0 and not m["clipping"]


def test_wav_roundtrip_24bit(tmp_path):
    x = synth.render("ui.charge_chime", 0.8, 1)
    mix.write_wav(tmp_path / "x.wav", x)
    y, sr = mix.read_wav(tmp_path / "x.wav")
    assert sr == 48000 and y.shape == x.shape and np.max(np.abs(x - y)) < 2e-7


def test_loudness_measure_sane():
    t = np.arange(48000 * 3) / 48000
    s = (0.1 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    st = np.stack([s, s], axis=1)
    assert abs(mix.peak_dbfs(s) + 20.0) < 0.05
    assert abs(mix.rms_dbfs(s) + 23.01) < 0.05
    # K-weighting gain at 1 kHz is +0.69 dB, cancelling the -0.691 offset: two channels of 0.1-peak sine = -20.0 LUFS
    assert abs(mix.lufs_approx(st) - (-20.0)) < 0.15
    assert mix.lufs_approx(np.zeros((48000 * 2, 2), dtype=np.float32)) == -120.0
    assert mix.true_peak_dbfs(s) >= mix.peak_dbfs(s) - 0.01


def test_cli_render_and_list(tmp_path):
    out = tmp_path / "c.wav"
    env = {"PYTHONPATH": "core"}
    import os
    env = {**os.environ, **env}
    r = subprocess.run([sys.executable, "-m", "fm.audio", "render", "ui.tap", "--frames", "4", "--seed", "3", "--out", str(out)],
                       capture_output=True, text=True, env=env, cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    assert r.returncode == 0, r.stderr
    x, _ = mix.read_wav(out)
    assert x.shape[0] == 8000
    r = subprocess.run([sys.executable, "-m", "fm.audio", "list"], capture_output=True, text=True, env=env,
                       cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    assert "crank.ratchet" in r.stdout
