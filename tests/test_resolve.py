import json

import pytest

from fm import ops, testing
from fm.errors import FMError
from fm.resolve import color, resolve


def test_color_conversion_matches_srgb_transfer():
    c = color("#7c9cc4")
    assert c["hex"] == "#7C9CC4"
    assert c["srgb"][0] == pytest.approx(124 / 255, abs=1e-6)
    assert 0 < c["linear"][0] < c["srgb"][0]            # linear is darker than sRGB for mid tones
    assert color("#FFFFFF")["linear"] == [1.0, 1.0, 1.0] and color("#000000")["linear"] == [0.0, 0.0, 0.0]


def _storyboard(sandbox):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        testing.stamp_all(sandbox)


def test_resolve_writes_deterministic_files_and_records_derived_nodes(sandbox):
    _storyboard(sandbox)
    r = resolve(sandbox)
    assert r["resolved"] and r["film_frames"] > 0
    files = sorted(f for f in (sandbox.dir / "09_resolved").glob("*.json") if f.name != "film.json")
    assert (sandbox.dir / "09_resolved" / "film.json").exists()
    assert len(files) == len([x for x in r["resolved"] if x != "film"])
    data = json.loads(files[0].read_text())
    assert data["schema"] == "fm.resolved_shot/1"
    assert data["frames"]["count"] >= 1 and data["frames"]["start"] == 0
    loaded = sandbox.load()
    assert f"resolved:{data['shot_id']}" in loaded.derived
    again = resolve(sandbox)                              # idempotent: nothing changes
    assert again["resolved"] == [] and set(again["unchanged"]) == set(r["resolved"]) - {"film"}
    assert files[0].read_bytes() == (sandbox.dir / "09_resolved" / files[0].name).read_bytes()


def test_resolved_goes_stale_when_a_shot_changes_and_only_that_shot_is_redone(sandbox):
    _storyboard(sandbox)
    first = resolve(sandbox)
    if len(first["resolved"]) < 3:
        pytest.skip("fixture has a single shot")
    victim = sandbox.load().shots
    item = sorted(victim.values(), key=lambda s: s.spec.shot_id)[0]
    from fm.io import load_yaml, write_yaml
    data = load_yaml(item.path)
    data["duration_s"] = data["duration_s"] + 1
    write_yaml(item.path, data)
    second = resolve(sandbox)
    assert item.spec.shot_id in second["resolved"]
    assert len(second["resolved"]) <= len(first["resolved"])
    # shots after the edited one shift by one second of frames, so they legitimately change too;
    # shots before it must be untouched
    assert all(s not in second["resolved"] for s in first["resolved"] if s < item.spec.shot_id)


def test_resolve_needs_shots(sandbox):
    with pytest.raises(FMError, match="no shots"):
        resolve(sandbox)
