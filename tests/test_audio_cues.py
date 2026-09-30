"""AUDIO_CUES.yaml: schema, `AUDIO_*` rules, event resolution, sync-point parsing, scaffold (M6 E4).
Toy fixtures like tests/test_resolve_motion.py; the real-project scaffold test writes to tmp_path only."""
import copy
from pathlib import Path

import pytest

from fm.audiocues import resolve_cues, sync_points
from fm.audiorun import mix_project  # noqa: F401 - import smoke
from fm.errors import FMError
from fm.io import load_yaml, write_yaml
from fm.project import Project
from fm.schemas import AUDIO_CUES_PATH, EXPORTED, AudioCues
from fm.validate import validate

from .test_animation_schema import _baked, _frames, _write, anim, film  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
LAST_SIGNAL = REPO / "projects" / "last_signal"


def cues_doc(**over):
    """A small valid cue sheet for the toy film (3 shots x 96 frames; SC01_SH010 has a `lid_drop` event at f5)."""
    d = {
        "fm": {"id": "audio_cues", "kind": "audio_cues", "phase": "ANIMATION_PREVIEW", "status": "PROPOSED",
               "owner_role": "sound-designer", "derived_from": [{"ref": "shot:SC01_SH010"}]},
        "mix": {"integrated_lufs": -16.0, "true_peak_dbtp": -1.0},
        "cues": [{"id": "lid", "shot": "SC01_SH010", "recipe": "fx.plastic_clunk", "at": {"event": "lid_drop"},
                  "gain_db": -12.0, "rationale": "the lid lands on the drop"}],
        "beds": [{"id": "room", "scene": "SC01", "recipe": "amb.car_interior", "gain_db": -32.0}],
        "silence": [], "human_supply": [],
    }
    d.update(over)
    return d


def setup(film, doc=None, events=True):
    if events:
        _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    write_yaml(film.dir / AUDIO_CUES_PATH, doc or cues_doc())
    return film.load()


def issues(film, doc=None, events=True):
    loaded = setup(film, doc, events)
    return resolve_cues(film, loaded)


def codes(ctx, level=None):
    return [c for lvl, c, _, _ in ctx.issues if level is None or lvl == level]


def with_cue(**over):
    d = cues_doc()
    d["cues"] = [{**d["cues"][0], **over}]
    return d


# ---------------------------------------------------------------- schema
def test_schema_is_exported_and_rejects_unknown_fields():
    assert EXPORTED["audio_cues"] is AudioCues
    doc = cues_doc()
    AudioCues.model_validate(doc)
    bad = copy.deepcopy(doc)
    bad["cues"][0]["surprise"] = 1
    with pytest.raises(Exception):
        AudioCues.model_validate(bad)
    m = AudioCues.model_validate(doc)
    assert m.mix.integrated_lufs == -16.0 and m.mix.true_peak_dbtp == -1.0 and m.mix.sample_rate == 48000
    assert m.cues[0].pan == 0.0 and m.cues[0].fade_in_f == 0


def test_cue_sheet_is_loaded_as_a_typed_artifact_and_validates_clean(film):
    loaded = setup(film)
    assert [i.meta.id for i in loaded.audio_cues] == ["audio_cues"]
    rep = validate(film)
    assert not [f for f in rep.errors if f.code.startswith("AUDIO_")], [f.code for f in rep.errors]


# ---------------------------------------------------------------- resolution
def test_event_cue_resolves_to_absolute_frame_and_offset_moves_it(film):
    ctx = issues(film)
    assert not codes(ctx, "ERROR")
    cue = [p for p in ctx.placements if p.kind == "cue"][0]
    assert cue.event == "lid_drop" and cue.start_f == 5 and cue.local_f == 5 and cue.layer == "sfx"
    ctx = issues(film, with_cue(at={"event": "lid_drop", "offset_f": -2}))
    assert [p for p in ctx.placements if p.kind == "cue"][0].start_f == 3


def test_explicit_frame_in_a_later_shot_is_film_absolute(film):
    ctx = issues(film, with_cue(shot="SC01_SH020", at={"frame": 10}))
    assert [p for p in ctx.placements if p.kind == "cue"][0].start_f == 96 + 10


def test_each_and_nth_pick_repeated_events(film):
    n = _frames(film, "SC01_SH010")
    d = anim(frames=n)
    d["events"] = [{"f": 5, "id": "lid_drop", "kind": "sound"}, {"f": 30, "id": "lid_drop", "kind": "sound"}]
    _write(film, "SC01_SH010", d)
    for at, want in (({"event": "lid_drop", "each": True}, [5, 30]), ({"event": "lid_drop", "nth": 1}, [30])):
        write_yaml(film.dir / AUDIO_CUES_PATH, with_cue(at=at))
        ctx = resolve_cues(film, film.load())
        assert not codes(ctx, "ERROR")
        assert [p.start_f for p in ctx.placements if p.kind == "cue"] == want
    write_yaml(film.dir / AUDIO_CUES_PATH, with_cue(at={"event": "lid_drop"}))
    assert "AUDIO_EVENT_AMBIGUOUS" in codes(resolve_cues(film, film.load()))
    write_yaml(film.dir / AUDIO_CUES_PATH, with_cue(at={"event": "lid_drop", "nth": 4}))
    assert "AUDIO_EVENT_NTH" in codes(resolve_cues(film, film.load()))


def test_scene_bed_spans_the_whole_scene(film):
    ctx = issues(film)
    bed = [p for p in ctx.placements if p.kind == "bed"][0]
    assert (bed.start_f, bed.end_f) == (0, 192) and bed.layer == "amb"


# ---------------------------------------------------------------- rules, one negative case each
@pytest.mark.parametrize("over,code", [
    ({"recipe": "no.such_recipe"}, "AUDIO_RECIPE"),
    ({"asset": "nothing_here"}, "AUDIO_SOURCE"),                        # recipe AND asset
    ({"recipe": None, "asset": None}, "AUDIO_SOURCE"),
    ({"recipe": None, "asset": "nothing_here"}, "AUDIO_ASSET"),
    ({"shot": "SC09_SH999"}, "AUDIO_SHOT"),
    ({"at": {}}, "AUDIO_AT"),
    ({"at": {"event": "lid_drop", "frame": 3}}, "AUDIO_AT"),
    ({"at": {"event": "not_an_event"}}, "AUDIO_EVENT"),
    ({"at": {"frame": 96}}, "AUDIO_OUT_OF_SHOT"),
    ({"at": {"frame": 95}, "duration_f": 30}, "AUDIO_PAST_SHOT"),
    ({"at": {"frame": 10}, "hits": [200]}, "AUDIO_HIT"),
    ({"layer": "nonsense"}, "AUDIO_SOURCE"),
])
def test_cue_rules(film, over, code):
    ctx = issues(film, with_cue(**over))
    assert code in codes(ctx, "ERROR"), ctx.issues


def test_past_shot_is_allowed_with_tail_ok(film):
    ctx = issues(film, with_cue(at={"frame": 95}, duration_f=30, tail_ok=True))
    assert "AUDIO_PAST_SHOT" not in codes(ctx)


def test_duplicate_ids_and_bad_mix_and_stray_event_without_anim(film):
    d = cues_doc()
    d["cues"].append({**d["cues"][0]})
    assert "AUDIO_DUP_ID" in codes(issues(film, d))
    d = cues_doc()
    d["mix"] = {"integrated_lufs": 3.0}
    assert "AUDIO_MIX" in codes(issues(film, d))
    (film.dir / "09_animation" / "SC01_SH010.anim.yaml").unlink()
    assert "AUDIO_EVENT" in codes(issues(film, cues_doc(), events=False))     # no anim file: the event cannot exist


def test_silence_span_forbids_overlapping_cues_unless_allowed(film):
    d = cues_doc(silence=[{"id": "quiet", "shot": "SC01_SH010", "from_f": 0, "to_f": 40, "canon": "audio.silence_map"}])
    d["beds"] = []
    assert "AUDIO_SILENCE_OVERLAP" in codes(issues(film, d))
    d["cues"][0]["allowed_in_silence"] = True
    assert "AUDIO_SILENCE_OVERLAP" not in codes(issues(film, d))
    d = cues_doc(silence=[{"id": "bad", "shot": "SC01_SH010", "from_f": 50, "to_f": 40}])
    assert "AUDIO_SILENCE" in codes(issues(film, d))
    d = cues_doc(silence=[{"id": "bad2", "from_f": 0, "to_f": 4}])        # neither shot nor scene
    assert "AUDIO_SILENCE" in codes(issues(film, d))


def test_placeholders_are_reported_never_silent(film):
    d = with_cue(recipe="body.sigh_placeholder", at={"frame": 3})
    ctx = issues(film, d)
    assert "AUDIO_PLACEHOLDER" in codes(ctx, "WARN") and "AUDIO_UNLISTED_PLACEHOLDER" in codes(ctx, "WARN")
    assert [p for p in ctx.placements if p.kind == "cue"][0].placeholder
    d["human_supply"] = [{"sound": "body.sigh_placeholder", "need": "a real sigh", "shots": ["SC01_SH010"]}]
    ctx = issues(film, d)
    assert "AUDIO_PLACEHOLDER" in codes(ctx) and "AUDIO_UNLISTED_PLACEHOLDER" not in codes(ctx)


def _asset(film, name, **manifest):
    import numpy as np
    from fm.audio import mix as M
    d = film.repo / "library" / "audio" / name
    d.mkdir(parents=True, exist_ok=True)
    M.write_wav(d / "a.wav", np.zeros((4800, 2), dtype=np.float32) + 0.1, 48000, 24)
    write_yaml(d / "asset.yaml", {"file": "a.wav", **manifest})


def test_library_assets_need_a_licence_and_may_not_speak(film):
    _asset(film, "creak", licence="CC0")
    _asset(film, "mystery")
    _asset(film, "voice", licence="CC0", tags=["speech"])
    ok = issues(film, with_cue(recipe=None, asset="creak", at={"frame": 3}))
    assert not codes(ok, "ERROR") and "AUDIO_LICENCE" not in codes(ok)
    assert [p for p in ok.placements if p.kind == "cue"][0].duration_f == pytest.approx(2.4)     # 0.1 s at 24 fps
    assert "AUDIO_LICENCE" in codes(issues(film, with_cue(recipe=None, asset="mystery", at={"frame": 3})), "WARN")
    assert "AUDIO_SPEECH" in codes(issues(film, with_cue(recipe=None, asset="voice", at={"frame": 3})), "ERROR")


def test_two_cue_sheets_are_refused(film):
    setup(film)
    write_yaml(film.dir / "12_post" / "other.yaml", {**cues_doc(), "fm": {**cues_doc()["fm"], "id": "audio_cues_2"}})
    assert "AUDIO_FILE" in codes(resolve_cues(film, film.load()), "ERROR")


# ---------------------------------------------------------------- sync-point parsing
@pytest.mark.parametrize("line,want", [
    ("key turn f3, coughs f5 and f9", [3, 5, 9]),
    ("silence from f33; cut after f33", []),
    ("engine dies f26, stops f32", [26, 32]),
    ("crank f8-29", [8]),                     # a range end is not a sync point
    ("no sound at all", []),
    (None, []),
])
def test_sync_points(line, want):
    got = sync_points(line)
    assert set(want) <= set(got) and all(isinstance(x, int) for x in got)
    if want == []:
        assert got == []


# ---------------------------------------------------------------- scaffold
def test_scaffold_refuses_to_overwrite_and_reports_uncovered_points(film, tmp_path):
    from fm.audioscaffold import scaffold
    _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    out = tmp_path / "cues.yaml"
    r = scaffold(film, out)                     # toy shots reuse Last Signal ids: a few registry lines match
    assert out.exists() and r["cues"] >= 1 and r["notes"] >= 1      # lid_drop is a sound event the registry knows nothing about
    with pytest.raises(FMError, match="exists"):
        scaffold(film, out)
    scaffold(film, out, force=True)
    AudioCues.model_validate(load_yaml(out))
    assert not (film.dir / AUDIO_CUES_PATH).exists()               # only the requested file is written


@pytest.mark.skipif(not (LAST_SIGNAL / "09_animation" / "SC01_SH090.anim.yaml").exists(), reason="Last Signal anim files absent")
def test_scaffold_on_last_signal_covers_every_sound_sync_frame(tmp_path):
    from fm.audioscaffold import scaffold
    from fm.audiocues import build_context
    project = Project(REPO, "last_signal")
    out = tmp_path / "AUDIO_CUES.yaml"
    r = scaffold(project, out)
    doc = load_yaml(out)
    model = AudioCues.model_validate(doc)
    assert model.fm.status.value == "PROPOSED" and r["cues"] == len(model.cues) >= 40
    assert r["beds"] == len(model.beds) >= 4 and r["silence"] >= 1 and model.human_supply
    assert all(c.rationale for c in model.cues)
    # every shot's sound_sync frame lies within +-1 frame of a scaffolded cue start or hit
    loaded = project.load()
    ctx = build_context(project, loaded)
    ev = ctx.events

    def starts(c):
        sid = c.shot
        if c.at.event:
            fs = [e["f"] for e in ev[sid] if e["id"] == c.at.event]
            fs = fs if c.at.each else [fs[c.at.nth or 0]]
        else:
            fs = [c.at.frame if c.at.frame is not None else c.at.f]
        return [f + c.at.offset_f for f in fs] + list(c.hits)
    missed, total = [], 0
    for sid in ctx.table:
        line = (loaded.shots[sid].spec.animation or {}).get("sound_sync")
        marks = [m for c in model.cues if c.shot == sid for m in starts(c)]
        for f in sync_points(line):
            total += 1
            if not any(abs(m - f) <= 1 for m in marks):
                missed.append((sid, f))
    assert total >= 25 and not missed, missed
