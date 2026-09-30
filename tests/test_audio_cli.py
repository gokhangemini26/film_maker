"""`fm audio list|synth|scaffold|mix` and `fm qa audio` on the toy film (M6 E5). Mixes are deterministic."""
import hashlib
import json
import wave

import pytest
from click.testing import CliRunner

from fm.cli import cli
from fm.io import write_yaml
from fm.phases import AUDIO_REPORT

from .test_animation_schema import _baked, _frames, _write, anim, film  # noqa: F401
from .test_audio_cues import cues_doc

TOTAL = 288                    # 3 shots x 96 frames at 24 fps
MIX = "12_post/audio/mix_48k_stereo.wav"


def run(*args, ok=True):
    r = CliRunner().invoke(cli, ["-p", "last_signal", *args], standalone_mode=False, catch_exceptions=True)
    code = getattr(r.exception, "code", 0) if r.exception else 0
    if ok:
        assert r.exception is None or code == 0, (r.output, repr(r.exception))
    return r, code


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheet(film, **over):
    """Cues at the lid event and the last frames of the film, a room bed, a loose mix window."""
    _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    d = cues_doc(**over)
    d["mix"] = {"integrated_lufs": -16.0, "lufs_tolerance": 60.0, "true_peak_dbtp": -1.0, "master_gain_db": 6.0}
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    return d


def report(film):
    return json.loads((film.dir / AUDIO_REPORT).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- list / synth
def test_audio_list_json_and_text():
    r, _ = run("audio", "list", "--json")
    rows = json.loads(r.output)
    names = {x["name"] for x in rows}
    assert {"fx.plastic_clunk", "amb.silence", "body.sigh_placeholder"} <= names
    assert [x for x in rows if x["name"].startswith("body.")] and all(x["placeholder"] for x in rows if x["name"].startswith("body."))
    r, _ = run("audio", "list")
    assert "PLACEHOLDER" in r.output and f"{len(rows)} recipe(s)" in r.output


def test_audio_synth_writes_only_the_output_directory(film, tmp_path):
    out = tmp_path / "lib"
    run("audio", "synth", "--id", "ui.tap", "--id", "amb.silence", "--out", str(out))
    assert sorted(p.name for p in out.iterdir()) == ["amb.silence.wav", "manifest.json", "ui.tap.wav"]
    first = sha(out / "ui.tap.wav")
    run("audio", "synth", "--id", "ui.tap", "--out", str(out))
    assert sha(out / "ui.tap.wav") == first                   # deterministic
    r, code = run("audio", "synth", "--id", "no.such", "--out", str(out), ok=False)
    assert r.exception is not None
    assert not (film.dir / "12_post" / "audio").exists()      # nothing leaked into the project


# ---------------------------------------------------------------- scaffold
def test_audio_scaffold_default_path_and_refusal(film, tmp_path):
    _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    out = tmp_path / "x.yaml"
    r, _ = run("audio", "scaffold", "--out", str(out))
    assert "PROPOSED" in r.output and "cue(s)" in r.output and out.exists()
    r, _ = run("audio", "scaffold", "--out", str(out), ok=False)
    assert r.exception is not None and "exists" in str(r.exception)
    assert not (film.dir / "12_post/AUDIO_CUES.yaml").exists()


# ---------------------------------------------------------------- mix
def test_mix_is_sample_exact_deterministic_and_recorded(film):
    sheet(film)
    r, _ = run("audio", "mix")
    wav = film.dir / MIX
    with wave.open(str(wav)) as w:
        assert (w.getframerate(), w.getnchannels(), w.getnframes()) == (48000, 2, TOTAL * 2000)
    assert (film.dir / "12_post/audio/mix_report.json").exists()
    assert (film.dir / "12_post/audio/stem_sfx.wav").exists() and (film.dir / "12_post/audio/stem_amb.wav").exists()
    assert "recorded audio:mix" in r.output and "samples" in r.output
    assert "audio:mix" in film.load().derived
    first = sha(wav)
    run("audio", "mix")
    assert sha(wav) == first


def test_mix_refuses_a_sheet_with_errors_and_a_missing_sheet(film):
    r, _ = run("audio", "mix", ok=False)
    assert r.exception is not None and "AUDIO_CUES" in str(r.exception)
    d = cues_doc()
    d["cues"][0]["recipe"] = "no.such"
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    r, _ = run("audio", "mix", ok=False)
    assert r.exception is not None and "AUDIO_RECIPE" in str(r.exception)


# ---------------------------------------------------------------- qa audio
def test_qa_audio_passes_a_coherent_sheet_and_writes_the_report(film):
    d = sheet(film)
    d["silence"] = [{"id": "hush", "shot": "SC02_SH010", "from_f": 40, "to_f": 96}]
    d["beds"] = [{"id": "room", "scene": "SC01", "recipe": "amb.car_interior", "gain_db": -30.0},
                 {"id": "tail", "shot": "SC02_SH010", "recipe": "amb.shop_room", "to_f": 40, "gain_db": -30.0}]
    d["mix"] = {"integrated_lufs": -16.0, "lufs_tolerance": 60.0, "true_peak_dbtp": -1.0, "master_gain_db": 6.0}
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    run("audio", "mix")
    r, code = run("qa", "audio", "--no-ffmpeg")
    assert code == 0 and "0 FAIL" in r.output and "qa/audio_report.json" in r.output
    rep = report(film)
    assert rep["summary"]["fail"] == 0 and rep["sync_points"] >= 1 and rep["mode"] == "preview"
    assert rep["silence"][0]["id"] == "hush" and rep["silence"][0]["rms_dbfs"] <= -50
    lv = rep["levels"]
    assert lv["targets"]["true_peak_dbtp"] == -1.0 and lv["targets"]["integrated_lufs"] == -16.0
    assert lv["true_peak_dbtp"] <= -1.0
    assert "qa:audio" in film.load().derived


def test_qa_audio_fails_on_missing_mix_stale_mix_and_uncovered_events(film):
    sheet(film)
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert code == 1 and "no rendered mix" in r.output
    run("audio", "mix")
    # a sound event with no cue near it is a sync FAIL
    d = anim(frames=_frames(film, "SC01_SH010"))
    d["events"].append({"f": 60, "id": "extra_thump", "kind": "sound"})
    _write(film, "SC01_SH010", d)
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert code == 1 and "extra_thump" in r.output and "no cue within +-1 frame" in r.output
    # the sheet changed after the mix: stale
    d2 = cues_doc()
    d2["cues"][0]["gain_db"] = -20.0
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d2)
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert "stale" in r.output


def test_qa_audio_flags_clipping_true_peak_and_loudness_with_a_suggested_gain(film):
    d = sheet(film)
    d["mix"] = {"integrated_lufs": -16.0, "lufs_tolerance": 1.0, "true_peak_dbtp": -1.0, "master_gain_db": 40.0}
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    run("audio", "mix")
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert code == 1 and ("clipping" in r.output or "true peak" in r.output)
    d["mix"]["master_gain_db"] = 0.0
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    run("audio", "mix")
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert code == 1 and "integrated loudness" in r.output and "suggested" in r.output
    assert "suggested_master_gain_db" in report(film)["levels"]


def test_qa_audio_placeholders_and_final_licence_mode(film):
    d = sheet(film)
    d["silence"] = [{"id": "hush", "shot": "SC01_SH010", "from_f": 0, "to_f": 20, "floor_db": -80.0}]
    d["silence"][0]["canon"] = "audio.silence_map"
    d["beds"] = []
    d["cues"] = [{"id": "sigh", "shot": "SC01_SH010", "recipe": "body.sigh_placeholder", "at": {"frame": 30}, "gain_db": -20.0,
                  "rationale": "stand-in"}]
    d["human_supply"] = [{"sound": "body.sigh_placeholder", "need": "a real sigh", "shots": ["SC01_SH010"],
                          "status": "SUPPLIED", "licence": "UNKNOWN"}]
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    run("audio", "mix")
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    rep = report(film)
    assert any("PLACEHOLDER body.sigh_placeholder" in m for row in rep["rows"] for _, m in row["findings"])
    assert rep["placeholders"] == [{"sound": "body.sigh_placeholder", "cues": ["sigh"]}]
    assert any("licence UNKNOWN" in m and s == "WARN" for row in rep["rows"] for s, m in row["findings"])
    r, code = run("qa", "audio", "--no-ffmpeg", "--final", ok=False)
    assert code == 1 and rep["human_supply"][0]["sound"] == "body.sigh_placeholder"
    assert any("licence UNKNOWN" in m and s == "FAIL" for row in report(film)["rows"] for s, m in row["findings"])


def test_qa_audio_measures_a_silence_breach_in_the_rendered_mix(film):
    d = sheet(film)
    d["silence"] = [{"id": "hush", "shot": "SC01_SH010", "from_f": 0, "to_f": 40, "canon": "audio.silence_map"}]
    d["beds"] = [{"id": "hiss", "shot": "SC01_SH010", "recipe": "amb.car_interior", "gain_db": -12.0, "allowed_in_silence": True}]
    d["cues"] = []
    write_yaml(film.dir / "12_post/AUDIO_CUES.yaml", d)
    run("audio", "mix")
    r, code = run("qa", "audio", "--no-ffmpeg", ok=False)
    assert code == 1 and "silence 'hush'" in r.output and "above its" in r.output
