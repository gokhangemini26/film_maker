"""Blender-free tests for the persistent-build logic (hashing, reconcile plan, ASSET_PREP contract)."""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))
from fm_blender import assets, reconcile as R  # noqa: E402

from fm import blenderrun, testing  # noqa: E402
from fm.resolve import resolve  # noqa: E402

FILM = {
    "format": {"fps": 24},
    "shots": {"SC01_SH010": {}, "SC03_SH010": {}},
    "canon": {
        "world.sets.street": {"w": 1}, "world.sets.ren_car": {"x": 1}, "world.sets.corner_shop": {"d": 3},
        "world.props.phone_ren": {"p": 1}, "characters.ren.proportions": {"height_m": 1.7},
        "characters.ren.face": {"f": 1}, "look.color.props": [{"hex": "#111111"}], "look.lighting.sc03": {"k": 1},
    },
}
SHOTS = {
    "SC01_SH010": {"scene_id": "SC01", "assets": ["world.sets.street", "world.props.phone_ren", "ui.status_bar"], "camera": {"lens_mm": 35}},
    "SC03_SH010": {"scene_id": "SC03", "assets": ["world.sets.corner_shop", "world.props.charging_cable"], "camera": {"lens_mm": 35}},
}


def specs(film=FILM, shots=SHOTS):
    return R.unit_specs(film, shots)


def hashes(s):
    return {u: v["hash"] for u, v in s.items()}


def test_units_cover_sets_characters_props_and_one_unit_per_shot():
    s = specs()
    assert set(s) == {"set:street", "set:shop", "char:ren", "prop:phone_ren", "shot:SC01_SH010", "shot:SC03_SH010"}
    assert "set:room" not in s   # no hana_room canon -> no room unit


def test_hash_is_deterministic():
    assert hashes(specs()) == hashes(specs(copy.deepcopy(FILM), copy.deepcopy(SHOTS)))


def test_shot_change_touches_only_that_shot():
    shots = copy.deepcopy(SHOTS)
    shots["SC01_SH010"]["camera"]["lens_mm"] = 85
    a, b = hashes(specs()), hashes(specs(shots=shots))
    assert [u for u in a if a[u] != b[u]] == ["shot:SC01_SH010"]


def test_canon_change_touches_only_the_units_that_read_it():
    film = copy.deepcopy(FILM)
    film["canon"]["world.sets.corner_shop"]["d"] = 4
    a, b = hashes(specs()), hashes(specs(film))
    assert [u for u in a if a[u] != b[u]] == ["set:shop"]
    film = copy.deepcopy(FILM)
    film["canon"]["characters.ren.face"]["f"] = 2
    b = hashes(specs(film))
    assert [u for u in a if a[u] != b[u]] == ["char:ren"]
    film = copy.deepcopy(FILM)
    film["canon"]["look.lighting.sc03"]["k"] = 9    # lighting is not read by unit builders
    assert hashes(specs(film)) == a


def test_colour_change_rebuilds_every_unit_that_uses_colours_but_not_shots():
    film = copy.deepcopy(FILM)
    film["canon"]["look.color.props"][0]["hex"] = "#222222"
    a, b = hashes(specs()), hashes(specs(film))
    assert {u for u in a if a[u] != b[u]} == {"set:street", "set:shop", "char:ren", "prop:phone_ren"}


def test_builder_version_bump_rebuilds_everything():
    a = hashes(R.unit_specs(FILM, SHOTS, version="0.1"))
    b = hashes(R.unit_specs(FILM, SHOTS, version="0.2"))
    assert all(a[u] != b[u] for u in a)


def test_plan_new_changed_unchanged_orphans():
    p = R.plan({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "X", "z": "9"})
    assert p["new"] == ["c"] and p["changed"] == ["b"] and p["unchanged"] == ["a"] and p["remove"] == ["z"]
    assert p["build"] == ["b", "c"]


def test_second_run_rebuilds_nothing_and_deleted_shot_is_orphan():
    d = hashes(specs())
    p = R.plan(d, dict(d))
    assert p["build"] == [] and p["remove"] == [] and len(p["unchanged"]) == len(d)
    shots = {k: v for k, v in SHOTS.items() if k != "SC03_SH010"}
    film = copy.deepcopy(FILM)
    film["shots"].pop("SC03_SH010")
    p = R.plan(hashes(specs(film, shots)), d)
    assert p["remove"] == ["shot:SC03_SH010"] and p["build"] == []


def test_report_counts():
    r = R.report(R.plan({"a": "1", "c": "3"}, {"a": "1", "z": "9"}))
    assert r["counts"] == {"built": 1, "unchanged": 1, "removed": 1} and r["removed"] == ["z"]


def test_asset_contract_flags_unknown():
    r = assets.check(SHOTS, FILM["canon"])
    by = {x["asset"]: x for x in r["assets"]}
    assert by["world.props.phone_ren"]["status"] == "ok"
    assert by["world.props.charging_cable"]["status"] == "UNKNOWN"
    assert r["unknown"] == ["world.props.charging_cable"]
    assert by["world.sets.street"]["in_canon"] is True and by["world.props.charging_cable"]["in_canon"] is False


def test_capabilities_pinned_to_known_builders():
    assert {a for a in assets.CAPABILITIES if a.startswith("world.sets.")} == {
        "world.sets.street", "world.sets.ren_car", "world.sets.corner_shop", "world.sets.hana_room"}
    assert set(assets.PROP_UNITS) <= {a.split("world.props.")[1] for a in assets.CAPABILITIES if a.startswith("world.props.")}


def test_build_refuses_when_pinned_blender_is_missing(sandbox, monkeypatch):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        testing.stamp_all(sandbox)
    resolve(sandbox)
    monkeypatch.setenv("FM_BLENDER", "/nonexistent/blender")
    from fm.errors import BlenderVersionError
    with pytest.raises(BlenderVersionError):
        blenderrun.build(sandbox, sandbox.repo)


@pytest.mark.skipif(importlib.util.find_spec("bpy") is None, reason="bpy module not installed")
def test_draft_build_records_blend_node_and_second_run_is_noop(sandbox):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        testing.stamp_all(sandbox)
    resolve(sandbox)
    r1 = blenderrun.build(sandbox, sandbox.repo, draft=True)
    assert r1["counts"]["built"] > 0 and (sandbox.dir / "10_blender" / f"{sandbox.slug}.blend").exists()
    assert "draft" in (sandbox.load().derived[f"blend:{sandbox.slug}"].notes or "")
    r2 = blenderrun.build(sandbox, sandbox.repo, draft=True)
    assert r2["counts"]["built"] == 0 and r2["counts"]["removed"] == 0
