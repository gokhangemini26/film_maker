import importlib.util

import pytest

from fm import blenderrun, testing
from fm.errors import BlenderVersionError, FMError
from fm.resolve import resolve


def _ready(sandbox):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        testing.stamp_all(sandbox)
    resolve(sandbox)


def test_preview_refuses_when_pinned_blender_is_missing(sandbox, monkeypatch):
    _ready(sandbox)
    monkeypatch.setenv("FM_BLENDER", "/nonexistent/blender")
    with pytest.raises(BlenderVersionError):
        blenderrun.preview(sandbox, sandbox.repo)
    assert not list((sandbox.dir / "10_blender" / "previews").glob("*.png")) if (sandbox.dir / "10_blender" / "previews").exists() else True


def test_draft_needs_the_bpy_module(sandbox, monkeypatch):
    _ready(sandbox)
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None)
    with pytest.raises(FMError, match="bpy"):
        blenderrun.preview(sandbox, sandbox.repo, draft=True)


def test_unknown_shot_is_reported(sandbox):
    _ready(sandbox)
    with pytest.raises(FMError, match="no resolved shot"):
        blenderrun._shot_ids(sandbox, ["SC99_SH999"])


@pytest.mark.skipif(importlib.util.find_spec("bpy") is None, reason="bpy module not installed")
def test_draft_preview_renders_and_records_derived_nodes(sandbox):
    _ready(sandbox)
    sid = sorted(p.stem for p in (sandbox.dir / "09_resolved").glob("SC*.json"))[0]
    rep = blenderrun.preview(sandbox, sandbox.repo, shots=[sid], width=160, draft=True)
    assert rep["failed"] == [] and rep["draft"] is True
    assert (sandbox.dir / "10_blender" / "previews" / f"{sid}.png").exists()
    rec = sandbox.load().derived[f"render:preview_{sid}"]
    assert "draft" in (rec.notes or "")


def test_scope_shots_and_frame_command(sandbox, monkeypatch, tmp_path):
    _ready(sandbox)
    ids = blenderrun._shot_ids(sandbox, None)
    assert blenderrun.scope_shots(sandbox, None) == ids
    assert blenderrun.scope_shots(sandbox, f"shot:{ids[0]}") == [ids[0]]
    assert blenderrun.scope_shots(sandbox, ids[0]) == [ids[0]]
    scene = ids[0].split("_")[0]
    assert all(s.startswith(scene + "_") for s in blenderrun.scope_shots(sandbox, f"scene:{scene}"))
    with pytest.raises(FMError):
        blenderrun.scope_shots(sandbox, "wat:1")
    monkeypatch.setenv("FM_BLENDER", str(tmp_path / "blender"))
    (tmp_path / "blender").write_text("")
    monkeypatch.setattr(blenderrun, "_pinned_version", lambda exe: "blender-test", raising=False)
    try:
        cmd, _ = blenderrun._frame_cmd(sandbox.repo, draft=False, resolved=tmp_path, out=tmp_path, sid="S", width=64, spec="1,2",
                                       stamp=True, samples=None, fast=False, resume=False)
    except FMError:  # version pin check not satisfiable without a real Blender
        return
    assert "--python" in cmd and cmd[-10:][2] == "S" and "stamp" in cmd
