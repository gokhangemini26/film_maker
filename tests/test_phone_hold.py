"""SC03_SH020 phone hold (anim holds[0], f10-35): the phone keeps its position and its screen squares to the lens, world up on top.
Pure python (mathutils), resolved shots of projects/last_signal/09_resolved."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
RES = ROOT / "projects" / "last_signal" / "09_resolved"

try:
    from fm_blender import animate as A  # noqa: E402
    from fm_blender import poses as PS  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

if not (RES / "SC03_SH020.json").exists():  # pragma: no cover
    pytest.skip("resolved shots absent", allow_module_level=True)

ZUP = A.Vector((0, 0, 1))


def _setup():
    shot = json.loads((RES / "SC03_SH020.json").read_text(encoding="utf-8"))
    canon = json.loads((RES / "film.json").read_text(encoding="utf-8"))["canon"]
    return shot, A.Stage(shot, canon, motion=shot["motion"])


def _phone(shot, stage, f):
    S = A.frame_state(shot, shot["motion"], shot["ui_timeline"], f, stage=stage)
    c = S["characters"]["ren"]
    base, fac = c["frame"]
    w = lambda v: PS.to_world(A.Vector(v), base, fac)  # noqa: E731
    pos = w(A._phone_local(c["joints"], c["phone_attach"], stage.ctx))
    return S, c, pos, w


def _axes(shot, stage, f):
    S, c, pos, w = _phone(shot, stage, f)
    toward = A.ren_phone_toward(c["phone_hold"], pos, w, stage.cpos, False, shot["camera"]["look_at"], w(c["joints"]["head"]))
    nz = toward.normalized()
    yv = (ZUP - nz * ZUP.dot(nz)).normalized()
    return pos, nz, yv


def test_sc03_sh020_phone_frozen_and_squared_to_the_lens_f10_35():
    shot, stage = _setup()
    p10, _, _ = _axes(shot, stage, 10)
    for f in range(10, 36):
        pos, nz, yv = _axes(shot, stage, f)
        assert (pos - p10).length < 1e-3, f                                   # under 1 mm
        assert math.degrees(nz.angle((stage.cpos - pos).normalized())) < 10.0, f
        assert math.degrees(yv.angle((ZUP - nz * ZUP.dot(nz)).normalized())) < 15.0, f


def test_sc03_sh020_screen_turns_gradually_into_the_hold_f5_10():
    shot, stage = _setup()
    angs = []
    for f in range(5, 11):
        pos, nz, _ = _axes(shot, stage, f)
        angs.append(math.degrees(nz.angle((stage.cpos - pos).normalized())))
    assert angs[-1] < 1.0
    assert all(a > b for a, b in zip(angs, angs[1:]))      # no pop: every frame is closer to the lens aim


def test_left_hand_stays_on_the_frozen_phone():
    shot, stage = _setup()
    for f in (10, 20, 35):
        _, c, pos, w = _phone(shot, stage, f)
        assert (w(c["joints"]["handL"]) - pos).length < 0.08, f


def test_only_sc03_sh020_takes_the_lens_aim_in_the_film():
    hits = []
    for p in sorted(RES.glob("SC*_SH*.json")):
        shot = json.loads(p.read_text(encoding="utf-8"))
        holds = (shot.get("motion") or {}).get("holds") or []
        if ((shot.get("camera") or {}).get("look_at") == "phone_ren" and (shot.get("composition") or {}).get("framing") != "insert"
                and any(h.get("scope") in ("phone", "all") and h.get("character") in (None, "ren") for h in holds)):
            hits.append(shot["shot_id"])
    assert hits == ["SC03_SH020"]
