import json

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from fm import qa_stills, testing  # noqa: E402
from fm.resolve import resolve  # noqa: E402


def _ready(sandbox):
    testing.drive(sandbox, "STORYBOARD")
    with testing.as_actor(testing.AGENT):
        testing.produce(sandbox, "STORYBOARD")
        testing.stamp_all(sandbox)
    resolve(sandbox)
    return sorted(p.stem for p in (sandbox.dir / "09_resolved").glob("SC*.json"))


def test_missing_flat_black_and_white_frames_are_flagged(sandbox):
    ids = _ready(sandbox)
    out = sandbox.dir / qa_stills.PREVIEW_DIR
    out.mkdir(parents=True, exist_ok=True)
    kinds = {"flat": (128, 128, 128), "black": (0, 0, 0), "white": (255, 255, 255)}
    used = list(zip(ids, kinds))
    for sid, k in used:
        Image.new("RGB", (320, 180), kinds[k]).save(out / f"{sid}.png")
    rep = qa_stills.check(sandbox)
    by = {r["shot"]: [f[1] for f in r["findings"]] for r in rep["rows"]}
    for sid, k in used:
        assert by[sid], f"{k} frame not flagged"
    for sid in ids[len(used):]:
        assert by[sid] == ["no preview still"]
    assert (sandbox.dir / "qa" / "stills_report.json").exists()
    assert "qa:stills" in sandbox.load().derived


def test_a_varied_frame_passes(sandbox):
    ids = _ready(sandbox)
    out = sandbox.dir / qa_stills.PREVIEW_DIR
    out.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (320, 180), (90, 110, 140))
    for x in range(160):
        for y in range(90):
            im.putpixel((x, y), (200, 160, 120))
    im.save(out / f"{ids[0]}.png")
    rep = qa_stills.check(sandbox)
    assert rep["rows"][0]["findings"] == []
