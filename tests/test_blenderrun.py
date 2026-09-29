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
