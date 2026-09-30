"""Resolver: `motion` and `ui_timeline` blocks, schema /2, determinism, partial re-resolve, fallbacks."""
import json
from pathlib import Path

import pytest
import yaml

from fm import animvocab as V
from fm import testing
from fm.deps import build_graph
from fm.errors import FMError
from fm.io import load_yaml, write_yaml
from fm.project import Project
from fm.resolve import film_format, frame_table, resolve, resolve_shot
from fm.uitimeline import UiTimelineError, expand_row, expand_shot
from fm.schemas import CanonEntry

from .test_animation_schema import _baked, _frames, _write, anim, film  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
LAST_SIGNAL = REPO / "projects" / "last_signal"
needs_ls = pytest.mark.skipif(not (LAST_SIGNAL / "canon" / "look.yaml").exists(), reason="Last Signal absent")


def _resolved(project, sid):
    return json.loads((project.dir / "09_resolved" / f"{sid}.json").read_text(encoding="utf-8"))


def _stamp(project):
    with testing.as_actor(testing.AGENT):
        testing.stamp_all(project)


def _shots_only(r):
    return sorted(x for x in r["resolved"] if x != "film")


def _events_only_anim(shot_id, n):
    """A second anim file that uses no pose vocabulary (events only)."""
    return {"fm": {"id": f"anim_{shot_id.lower()}", "kind": "shot_animation", "phase": "ANIMATION",
                   "status": "PROPOSED", "owner_role": "animation-director",
                   "derived_from": [{"ref": f"shot:{shot_id}"}]},
            "shot_id": shot_id, "frames": n, "vocab_version": V.VOCAB_VERSION,
            "rationale": "Only a named sync point in this shot.", "events": [{"f": 1, "id": "tick", "kind": "sound"}]}


# ---------------------------------------------------------------- fallback: no anim file
def test_shots_without_anim_files_keep_the_prose_block_and_get_null_motion(film):
    r = resolve(film)
    for sid in _shots_only(r):
        d = _resolved(film, sid)
        assert d["schema"] == "fm.resolved_shot/2"
        assert d["motion"] is None and d["ui_timeline"] is None          # the sandbox has no phone-screen canon
        assert "animation" in d and d["frames"]["count"] >= 1


def test_stub_anim_files_are_ignored(film):
    write_yaml(film.dir / "09_animation" / "SC01_SH010.anim.yaml",
               {"fm": anim()["fm"], "shot_id": "SC01_SH010"})
    _stamp(film)
    resolve(film)
    assert _resolved(film, "SC01_SH010")["motion"] is None


# ---------------------------------------------------------------- motion block
def test_motion_block_is_built_with_absolute_frames(film):
    n = _frames(film, "SC02_SH010")
    n1 = _frames(film, "SC01_SH010")
    _write(film, "SC01_SH010", anim(frames=n1))
    _stamp(film)
    r = resolve(film)
    d = _resolved(film, "SC01_SH010")
    m = d["motion"]
    start = d["frames"]["start"]
    assert m["schema"] == "fm.motion/1" and m["vocab_version"] == V.VOCAB_VERSION
    assert m["frames"] == n1 and m["frame_start"] == start and m["source"] == "artifact:anim_sc01_sh010"
    pose = m["characters"]["ren"]["pose"]
    assert [(k["f"], k["f_abs"], k["ref"]) for k in pose] == [(0, start, "car_upright"), (10, start + 10, "car_phone_up")]
    assert pose[1]["blend_f"] == 6 and pose[1]["ease"] == "ease_in_out"
    assert m["props"]["glovebox_lid"][0]["state"] == "open_down"
    assert m["events"] == [{"f": 5, "f_abs": start + 5, "id": "lid_drop", "kind": "sound", "source": "anim"}]
    assert m["preview_frames"] == [0, 10, n1 - 1]                        # every pose key + the last frame
    text = json.dumps(m)
    assert "note" not in text and "rationale" not in text                # human text never reaches builders
    assert "SC01_SH010" in r["resolved"]
    assert _resolved(film, "SC02_SH010")["motion"] is None
    assert n > 0


def test_explicit_preview_frames_and_handle_tops(film):
    n = _frames(film, "SC01_SH010")
    d = anim(frames=n, preview_frames=[2, 9])
    d["characters"]["ren"]["move"] = {"gait": "crank_turn", "first_top_f": 4, "note": "1 turn per second"}
    d["characters"]["ren"]["pose"] = [{"f": 0, "ref": "kerb_crank_hold", "ease": "hold"}]
    d["props"] = {}
    d["events"] = []
    _write(film, "SC01_SH010", d)
    _stamp(film)
    resolve(film)
    m = _resolved(film, "SC01_SH010")["motion"]
    assert m["preview_frames"] == [2, 9]
    tops = [e["f"] for e in m["events"] if e["id"] == "handle_top"]
    assert tops == list(range(4, n, 24))
    assert all(e["source"] == "derived:crank_turn" and e["kind"] == "sound" for e in m["events"])
    assert m["characters"]["ren"]["move"]["handle_tops"][0] == {"f": 4, "f_abs": m["frame_start"] + 4}


def test_second_resolve_changes_nothing(film):
    _write(film, "SC01_SH010", anim(frames=_frames(film, "SC01_SH010")))
    _stamp(film)
    first = resolve(film)
    before = {p.name: p.read_bytes() for p in (film.dir / "09_resolved").glob("*.json")}
    second = resolve(film)
    assert second["resolved"] == [] and set(second["unchanged"]) == set(first["resolved"]) - {"film"}
    assert before == {p.name: p.read_bytes() for p in (film.dir / "09_resolved").glob("*.json")}


def test_editing_one_anim_file_re_resolves_only_that_shot(film):
    n1, n2 = _frames(film, "SC01_SH010"), _frames(film, "SC02_SH010")
    _write(film, "SC01_SH010", anim(frames=n1))
    _write(film, "SC02_SH010", _events_only_anim("SC02_SH010", n2))
    _stamp(film)
    resolve(film)
    d = load_yaml(film.dir / "09_animation" / "SC01_SH010.anim.yaml")
    d["characters"]["ren"]["pose"][1]["ref"] = "car_sag"
    write_yaml(film.dir / "09_animation" / "SC01_SH010.anim.yaml", d)
    stale = build_graph(film.load()).stale()
    assert "resolved:SC01_SH010" in stale and "resolved:SC02_SH010" not in stale      # staleness is wired
    r = resolve(film)
    assert _shots_only(r) == ["SC01_SH010"]
    assert _resolved(film, "SC01_SH010")["motion"]["characters"]["ren"]["pose"][1]["ref"] == "car_sag"
    # prose-only edits (notes) leave the resolved bytes alone
    d["characters"]["ren"]["pose"][1]["note"] = "a different sentence"
    write_yaml(film.dir / "09_animation" / "SC01_SH010.anim.yaml", d)
    before = (film.dir / "09_resolved" / "SC01_SH010.json").read_bytes()
    resolve(film)
    assert (film.dir / "09_resolved" / "SC01_SH010.json").read_bytes() == before


def test_a_vocabulary_edit_re_resolves_only_the_shots_that_use_it(film):
    n1, n2 = _frames(film, "SC01_SH010"), _frames(film, "SC02_SH010")
    entries = [e for e in V.canon_entry_dicts() if e["id"] in ("animation.vocab.pose.ren", "animation.vocab.event_kind")]
    for e in entries:
        e["serves"], e["depends_on"] = [], []
    testing.write_canon(film, "animation", entries)
    d1 = anim(frames=n1)
    d1["fm"]["derived_from"] += [{"ref": "canon:animation.vocab.pose.ren"}]
    _write(film, "SC01_SH010", d1)
    _write(film, "SC02_SH010", _events_only_anim("SC02_SH010", n2))
    _stamp(film)
    resolve(film)
    rec = film.load().derived["resolved:SC01_SH010"]
    assert "canon:animation.vocab.pose.ren" in {x.ref for x in rec.derived_from}
    assert "canon:animation.vocab.pose.ren" not in {x.ref for x in film.load().derived["resolved:SC02_SH010"].derived_from}
    assert "canon:animation.vocab.event_kind" in {x.ref for x in film.load().derived["resolved:SC02_SH010"].derived_from}
    path = film.dir / "canon" / "animation.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for e in data["entries"]:
        if e["id"] == "animation.vocab.pose.ren":
            e["statement"] = "Ren's pose presets, reworded."
    write_yaml(path, data)
    stale = build_graph(film.load()).stale()
    assert "resolved:SC01_SH010" in stale and "resolved:SC02_SH010" not in stale
    assert _shots_only(resolve(film)) == ["SC01_SH010"]


# ---------------------------------------------------------------- failing loudly
def test_unknown_refs_and_wrong_frames_are_refused_not_guessed(film):
    n = _frames(film, "SC01_SH010")
    bad = anim(frames=n)
    bad["characters"]["ren"]["pose"][1]["ref"] = "car_sleeping"
    _write(film, "SC01_SH010", bad)
    _stamp(film)
    with pytest.raises(FMError, match=r"SC01_SH010.*ANIM_VOCAB.*car_sleeping"):
        resolve(film)
    _write(film, "SC01_SH010", anim(frames=n + 1))
    _stamp(film)
    with pytest.raises(FMError, match="ANIM_FRAMES"):
        resolve(film)


def test_two_anim_files_for_one_shot_are_refused(film):
    n = _frames(film, "SC01_SH010")
    _write(film, "SC01_SH010", anim(frames=n))
    twin = anim(frames=n)
    twin["fm"]["id"] = "anim_twin"
    write_yaml(film.dir / "09_animation" / "twin.anim.yaml", twin)
    _stamp(film)
    with pytest.raises(FMError, match="2 anim files"):
        resolve(film)


# ---------------------------------------------------------------- ui_timeline: the canon table parser
def _states():
    canon = yaml.safe_load((LAST_SIGNAL / "canon" / "look.yaml").read_text(encoding="utf-8"))["entries"]
    return next(e for e in canon if e["id"] == "look.style.phone_screen.states_by_shot")["value"]


def _frame_counts():
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))["frames"]["count"]
            for p in sorted((LAST_SIGNAL / "09_resolved").glob("SC*.json"))}


@needs_ls
def test_the_parser_reads_all_38_rows_of_states_by_shot():
    states, counts = _states(), _frame_counts()
    rows = [k for k in states if k.startswith("SC")]
    assert len(rows) == 38 == len(counts)
    for sid in rows:
        tl = expand_shot(states, sid, counts[sid])
        assert len(tl["frames"]) == counts[sid] and [f["f"] for f in tl["frames"]] == list(range(counts[sid]))
        assert all(f["ui"] for f in tl["frames"])
        assert tl == expand_shot(states, sid, counts[sid])                                  # deterministic
        if tl["phone"] == "ren":
            assert all(f["pct"] and f["pct"] >= 1 for f in tl["frames"])                    # `never: zero_percent`
            assert all(f["red"] == (f["pct"] <= 4) for f in tl["frames"])                   # continuity.battery


@needs_ls
def test_parser_spot_checks_against_the_canon_table():
    states, counts = _states(), _frame_counts()
    fr = lambda sid: expand_shot(states, sid, counts[sid])["frames"]              # noqa: E731
    a = fr("SC01_SH080")
    assert (a[3]["pct"], a[3]["colour"]) == (5, "charcoal") and (a[4]["pct"], a[4]["colour"]) == (4, "red")
    b = fr("SC01_SH130")
    assert b[31]["bolt"] is True and b[32]["bolt"] is False and b[31]["brightness"] == 1.0 and b[32]["brightness"] == 0.7
    c = fr("SC03_SH050")
    assert [c[i]["pct"] for i in (7, 8)] == [3, 2] and [c[i]["brightness"] for i in (7, 8, 10, 11)] == [1.0, 0.7, 0.7, 1.0]
    d = fr("SC05_SH010")
    assert d[0]["ui"] == "off" and d[2]["ui"] == "wake" and d[0]["brightness"] == 0.0
    assert d[2]["brightness"] == 0.0 and d[3]["brightness"] == 0.75 and d[4]["brightness"] == 1.0   # ramp_to_1.0_by_f4_ease_out
    assert d[1]["phone"] == "hana" and "photo_scale_pct" not in d[1] and d[2]["photo_scale_pct"] == 96 and d[5]["photo_scale_pct"] == 100
    e = fr("SC06_SH010")
    assert e[0]["brightness"] == 1.0 and e[12]["brightness"] == 0.25 and e[24]["brightness"] == 0.0
    assert not e[23].get("screen_off") and e[24]["screen_off"] is True
    g = fr("SC04_SH020")
    assert [g[i]["icon_visible"] for i in (11, 12, 23, 24)] == [True, False, False, True] and all(x["icon_blink"] for x in g)
    assert [g[i]["brightness"] for i in (13, 14, 16, 17, 20, 22)] == [1.0, 0.7, 0.7, 1.0, 0.7, 1.0]
    h = fr("SC04_SH070")
    assert (h[1]["pct"], h[2]["pct"]) == (1, 2) and not any(x["icon_blink"] for x in h)
    i = fr("SC01_SH030")
    assert i[0]["ui"] == "map" and i[3]["slide"]["to"] == "call" and 0 < i[3]["slide"]["progress"] < 1 and i[8]["ui"] == "call"
    j = fr("SC01_SH050")
    assert (j[32]["call_state"], j[33]["call_state"]) == ("ringing", "unanswered")
    k = fr("SC04_SH060")
    assert (k[20]["heart"], k[21]["heart"], k[54]["heart"], k[55]["heart"]) == (False, True, True, False) and k[0]["lines"] == 3
    l = fr("SC01_SH070")
    assert l[15]["typing"] is True and l[16]["typing"] is False and l[0]["lines"] == 1
    m = fr("SC04_SH050")
    assert m[55]["lines"] == 1 and m[56]["lines"] == 2 and m[56]["typing"] is True
    assert fr("SC04_SH090")[0]["sent"] == {"progress": 1.0, "tick": True} and fr("SC04_SH090")[6]["bolt"] and not fr("SC04_SH090")[7]["bolt"]


@needs_ls
def test_flicker_and_compose_to_sent_need_events_the_table_lacks():
    states, counts = _states(), _frame_counts()
    tl = expand_shot(states, "SC04_SH010", counts["SC04_SH010"])
    assert any("flicker" in w for w in tl["warnings"]) and all(f["flicker"] for f in tl["frames"])
    tl = expand_shot(states, "SC04_SH080", counts["SC04_SH080"])
    assert any("compose_to_sent" in w for w in tl["warnings"])


def _ev(**kw):
    from fm.schemas.animation import UiEvent
    return UiEvent(**kw)


@needs_ls
def test_anim_events_are_overlaid_on_the_canon_base():
    states, counts = _states(), _frame_counts()
    n = counts["SC04_SH010"]
    dips = [_ev(f=7, event="dip", dur_f=2), _ev(f=19, event="dip", dur_f=3), _ev(f=38, event="dip", dur_f=2)]
    tl = expand_shot(states, "SC04_SH010", n, dips)
    assert [f["f"] for f in tl["frames"] if f["brightness"] < 1] == [7, 8, 19, 20, 21, 38, 39] and tl["warnings"] == []
    # typing, key presses, the send line and the tick (SC04_SH080)
    n = counts["SC04_SH080"]
    ev = [_ev(f=6, event="key_press", key="send", dur_f=2), _ev(f=8, event="slide", to="sent", dur_f=1),
          _ev(f=8, event="progress", dur_f=25), _ev(f=34, event="tick")]
    tl = expand_shot(states, "SC04_SH080", n, ev)
    f = tl["frames"]
    assert f[7]["ui"] == "compose" and f[7]["key_pressed"] == "send" and f[8]["ui"] == "sent" and tl["warnings"] == []
    assert f[8]["sent"] == {"progress": 0.0, "tick": False} and f[32]["sent"]["progress"] == 1.0
    assert f[33]["sent"]["tick"] is False and f[34]["sent"]["tick"] is True and f[57]["sent"]["tick"] is True
    assert 0 < f[20]["sent"]["progress"] < 1
    tl = expand_shot(states, "SC01_SH070", counts["SC01_SH070"],
                     [_ev(f=0, event="text", line=1, chars=21, dur_f=16)])
    assert tl["frames"][0]["typed"] == {"1": 1} and tl["frames"][15]["typed"] == {"1": 21}
    assert tl["frames"][57]["typed"] == {"1": 21}


def test_bad_tables_and_events_raise():
    with pytest.raises(UiTimelineError, match="unknown ui label"):
        expand_row({"ui": "compose_9_lines_and_a_cat", "pct": 1}, "SC09_SH010", 4)
    with pytest.raises(UiTimelineError, match="unknown states_by_shot keys"):
        expand_row({"ui": "map", "wobble": 1}, "SC09_SH010", 4)
    with pytest.raises(UiTimelineError, match="hana phone"):
        expand_row({"ui": "map", "pct": 5, "colour": "charcoal"}, "SC09_SH010", 4, events=[_ev(f=0, event="pulse", dur_f=2, phone="hana")])
    with pytest.raises(UiTimelineError, match="need a states_by_shot row"):
        expand_shot({}, "SC09_SH010", 4, [_ev(f=0, event="pulse", dur_f=2)])
    assert expand_shot({}, "SC09_SH010", 4) is None


# ---------------------------------------------------------------- the real project
@needs_ls
@pytest.mark.skipif(not (LAST_SIGNAL / "09_animation" / "SC01_SH090.anim.yaml").exists(), reason="example absent")
def test_committed_example_matches_what_the_resolver_produces():
    project = Project(REPO, "last_signal")
    loaded = project.load()
    table = frame_table(loaded, film_format(loaded)["fps"])
    data, refs = resolve_shot(project, loaded, "SC01_SH090", table, film_format(loaded))
    on_disk = json.loads((LAST_SIGNAL / "09_resolved" / "SC01_SH090.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(data)) == on_disk
    assert on_disk["schema"] == "fm.resolved_shot/2" and on_disk["motion"]["characters"]["ren"]["pose"][0]["ref"] == "car_phone_up"
    assert on_disk["ui_timeline"]["frames"][0]["pct"] == 4
    assert "artifact:anim_sc01_sh090" in refs and "canon:look.style.phone_screen.states_by_shot" in refs
    assert "canon:animation.vocab.pose.ren" in refs
    assert loaded.derived["resolved:SC01_SH090"].content_hash
    assert "resolved:SC01_SH090" not in build_graph(loaded).stale()
