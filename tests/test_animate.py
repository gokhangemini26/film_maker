"""Per-frame animation state (blender/fm_blender/animate.py, framesel.py): pure python, no rendering.
Needs mathutils (bpy wheel) and the resolved shots of projects/last_signal/09_resolved."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
RES = ROOT / "projects" / "last_signal" / "09_resolved"

try:
    from fm_blender import animate as A  # noqa: E402
    from fm_blender import framesel as FS  # noqa: E402
except ImportError:  # pragma: no cover
    pytest.skip("mathutils/bpy not importable", allow_module_level=True)

if not (RES / "SC04_SH050.json").exists():  # pragma: no cover
    pytest.skip("resolved shots absent", allow_module_level=True)


def shot(sid):
    return json.loads((RES / f"{sid}.json").read_text(encoding="utf-8"))


def fs(sid, f):
    s = shot(sid)
    return A.frame_state(s, s["motion"], s["ui_timeline"], f)


def test_out_of_range_frame_raises():
    s = shot("SC02_SH010")
    with pytest.raises(ValueError):
        A.frame_state(s, s["motion"], s["ui_timeline"], s["frames"]["count"])
    with pytest.raises(ValueError):
        A.frame_state(s, s["motion"], s["ui_timeline"], -1)


def test_deterministic():
    a, b = fs("SC02_SH010", 9), fs("SC02_SH010", 9)
    assert a["characters"]["ren"]["joints"].keys() == b["characters"]["ren"]["joints"].keys()
    assert repr(a) == repr(b)


def test_pose_blend_endpoints_and_ease():
    # SC02_SH010: hold scramble_out at f0, blend into run_phone_out over 6 frames from f6 (ease_out)
    assert fs("SC02_SH010", 0)["characters"]["ren"]["pose"] == {"from": "scramble_out", "to": "scramble_out", "t": 1.0}
    p6 = fs("SC02_SH010", 6)["characters"]["ren"]["pose"]
    p9 = fs("SC02_SH010", 9)["characters"]["ren"]["pose"]
    p12 = fs("SC02_SH010", 12)["characters"]["ren"]["pose"]
    assert (p6["from"], p6["to"], p6["t"]) == ("scramble_out", "run_phone_out", 0.0)
    assert p6["t"] < p9["t"] < 1.0
    assert p9["t"] > 0.5  # ease_out is ahead of linear at the midpoint
    assert p12["t"] == 1.0 and p12["from"] == "run_phone_out"


def test_gait_moves_root_and_limbs():
    r0 = fs("SC02_SH010", 12)["characters"]["ren"]
    r1 = fs("SC02_SH010", 15)["characters"]["ren"]
    assert r0["gait"] == "scramble"
    assert (r0["frame"][0] - r1["frame"][0]).length > 0.05  # the path advances
    j0, j1 = r0["joints"], r1["joints"]
    assert any((j0[k] - j1[k]).length > 1e-4 for k in j0 if k in j1 and hasattr(j0[k], "length"))


def test_door_angle_at_key_frames():
    ang = [fs("SC02_SH010", f)["props"]["passenger_door"]["angle_deg"] for f in range(8)]
    assert ang[0] == 20.0
    assert ang[4] == 63.0  # swing overshoot peak
    assert ang[5] == pytest.approx(61.5) and ang[6] == 60.0 and ang[7] == 60.0
    assert 20.0 < ang[1] < ang[2] < ang[3] < 63.0  # monotone swing toward the peak


def test_crank_pip_lit_windows():
    pip = {f: fs("SC04_SH050", f)["props"]["crank_charger"]["pip"] for f in (0, 29, 30, 34, 37, 38, 39)}
    assert pip[0] == 0.0 and pip[29] == 0.0
    assert pip[30] == pytest.approx(1 / 81)  # ease_in over 9 frames: first frame t=1/9, squared
    assert 0.0 < pip[30] < pip[34] < pip[37] < 1.0
    assert pip[38] == 1.0 and pip[39] == 1.0
    assert fs("SC04_SH050", 12)["props"]["crank_charger"]["loc_t"] == pytest.approx(0.2593, abs=1e-3)  # default ease (smoothstep) of 1/3, 3-frame change from f12
    assert fs("SC04_SH050", 14)["props"]["crank_charger"]["loc"] == "lap"


def test_ui_state_at_frame_boundaries():
    s = shot("SC04_SH020")
    for f in (13, 14, 15):
        ui = fs("SC04_SH020", f)["ui"]
        row = s["ui_timeline"]["frames"][f]
        assert ui["frame"] == f and ui["brightness"] == row["brightness"] and ui["pct"] == row["pct"]
    assert fs("SC04_SH020", 13)["ui"]["brightness"] == 1.0
    assert fs("SC04_SH020", 14)["ui"]["brightness"] == 0.7  # the key press dips the brightness at f14
    assert fs("SC04_SH020", 14)["ui"]["screen"] == "compose"


def test_prop_continuity_across_consecutive_shots():
    prev, nxt = shot("SC04_SH040"), shot("SC04_SH050")
    end, start = A.end_state(prev), A.start_state(nxt)
    for prop in ("glovebox_lid", "crank_charger", "phone_ren"):
        assert end[prop] == start[prop], prop
    # door: SC04_SH050 does not animate it; the carried motion reproduces the previous end state at frame 0
    m = A.with_carried_props(nxt, [prev])
    assert m["props"]["passenger_door"][0]["state"] == "open_60"
    st = A.frame_state(nxt, m, nxt["ui_timeline"], 0)
    assert st["props"]["passenger_door"]["angle_deg"] == 60.0
    a, b = shot("SC02_SH010"), shot("SC02_SH020")
    assert A.end_state(a)["phone_ren"] == A.start_state(b)["phone_ren"]


def test_camera_static_and_dolly():
    for sid in ("SC04_SH050", "SC02_SH010"):
        s = shot(sid)
        for f in (0, s["frames"]["count"] - 1):
            c = fs(sid, f)["camera"]
            assert 0.0 <= c["progress"] <= 1.0
    dolly = [sid for sid in ("SC01_SH010", "SC01_SH020", "SC01_SH030", "SC04_SH060", "SC05_SH020")
             if (shot(sid).get("motion") or {}).get("camera", {}).get("move") == "dolly_in"]
    for sid in dolly:
        n = shot(sid)["frames"]["count"]
        assert fs(sid, 0)["camera"]["progress"] == 0.0 and fs(sid, n - 1)["camera"]["progress"] == 1.0


def test_parse_frames_and_select():
    assert FS.parse_frames("12,f24,30-32,last", 60) == [12, 24, 30, 31, 32, 59]
    assert FS.parse_frames("all", 4) == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        FS.parse_frames("99", 10)
    s = shot("SC04_SH050")
    assert FS.select_frames(s, frames=None, every_key=False, preview_frame=False) == [s["frames"]["count"] // 2]
    pf = FS.select_frames(s, frames=None, every_key=False, preview_frame=True)
    assert pf == [s["animation"]["preview_frame"]]
