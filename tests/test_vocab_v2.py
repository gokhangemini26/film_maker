"""Animation vocabulary v2: names, lids track, charging_cable, shop_door swing_back, chained_fields."""
import copy

import pytest

from fm import animvocab as V
from fm.schemas import CanonEntry

from .test_animation_schema import anim, codes, parse
from .test_qa_motion import S, T, hits, run


def v2(**over):
    return anim(**over)


def with_ren(d, **tracks):
    d = copy.deepcopy(d)
    d["characters"]["ren"].update(tracks)
    return d


# ---------------------------------------------------------------- module
def test_version_and_v1_names_are_kept():
    assert V.VOCAB_VERSION == 2 and V.ACCEPTED_VOCAB_VERSIONS == (1, 2)
    for n in ("kneel_reach_stand", "kneel_head_back"):
        assert n in V.POSES["ren"]
    for n in ("wary", "determined"):
        assert n in V.face_names("ren") and n in V.comic_faces("ren")
    assert V.LIDS == {"open": 1.0, "low": 0.55, "closed": 0.0}
    assert V.PROPS["shop_door"]["fields"]["state"] == ("closed", "open_70", "swing_back")
    assert V.PROPS["shop_door"]["fields"]["swing_deg"] == "deg"
    cab = V.PROPS["charging_cable"]
    assert cab["fields"]["state"] == ("posed", "hidden") and cab["chained_fields"] == ("loc",)
    assert cab["before_first_key"] == {"loc": "glovebox", "state": "hidden"}
    v1_poses, v1_faces, v1_props = V._v1_view()
    assert "kneel_upright" in v1_poses["ren"] and "kneel_reach_stand" not in v1_poses["ren"]
    assert "charging_cable" not in v1_props and "wary" not in v1_faces["ren"]["comic"]
    assert len(v1_poses["ren"]) == 15 and "swing_back" not in v1_props["shop_door"]["fields"]["state"]
    for e in V.canon_entry_dicts():                       # the v1 canon proposals still describe v1
        assert CanonEntry.model_validate(e).value["vocab_version"] == 1


def test_v1_files_stay_valid_and_cannot_use_v2_names():
    d = anim(vocab_version=1)
    assert not [c for c in codes(d, shot_characters=["ren"]) if c[0] == "ERROR"]
    d = with_ren(anim(vocab_version=1), pose=[{"f": 0, "ref": "kneel_head_back", "ease": "hold"}])
    assert ("ERROR", "ANIM_VOCAB_VERSION") in codes(d, shot_characters=["ren"])
    d = with_ren(anim(vocab_version=1), lids=[{"f": 0, "ref": "open", "ease": "hold"}])
    assert ("ERROR", "ANIM_VOCAB_VERSION") in codes(d, shot_characters=["ren"])
    d = anim(vocab_version=1, props={"charging_cable": [{"f": 0, "loc": "glovebox"}]})
    assert ("ERROR", "ANIM_VOCAB_VERSION") in codes(d, shot_characters=["ren"])


# ---------------------------------------------------------------- poses and faces
def test_new_poses_and_faces_pass_in_v2():
    d = with_ren(v2(), pose=[{"f": 0, "ref": "kneel_upright", "ease": "hold"},
                              {"f": 1, "ref": "kneel_reach_stand", "ease": "ease_out", "blend_f": 5},
                              {"f": 16, "ref": "kneel_head_back", "ease": "ease_in_out", "blend_f": 10}],
                 face=[{"f": 0, "ref": "wary"}, {"f": 18, "ref": "determined"}])
    assert not [c for c in codes(d, shot_characters=["ren"]) if c[0] == "ERROR"]


def test_wary_and_determined_are_illegal_from_the_turn():
    for face in ("wary", "determined"):
        d = with_ren(v2(shot_id="SC04_SH030", fm={**anim()["fm"], "id": "anim_sc04_sh030"}),
                     face=[{"f": 0, "ref": face}])
        assert ("ERROR", "ANIM_FACE_AFTER_TURN") in codes(d, shot_characters=["ren"])


# ---------------------------------------------------------------- lids
BLINK = [{"f": 0, "ref": "open", "ease": "hold"},
         {"f": 28, "ref": "closed", "ease": "ease_in", "dur_f": 4},
         {"f": 34, "ref": "open", "ease": "ease_out", "dur_f": 6}]


def test_lids_track_parses_and_a_blink_passes():
    d = with_ren(v2(), lids=BLINK)
    assert parse(d).characters["ren"].lids[1].ref == "closed"
    assert not [c for c in codes(d, shot_characters=["ren"]) if c[0] == "ERROR"]


@pytest.mark.parametrize("lids,code", [
    ([{"f": 0, "ref": "squint"}], "ANIM_VOCAB"),
    ([{"f": 0, "ref": "open", "ease": "wobble"}], "ANIM_VOCAB"),
    ([{"f": 5, "ref": "open"}, {"f": 5, "ref": "low"}], "ANIM_ORDER"),
    ([{"f": 40, "ref": "open"}], "ANIM_RANGE"),
    ([{"f": 0, "ref": "closed", "dur_f": 8}, {"f": 5, "ref": "open"}], "ANIM_LIDS"),        # runs past next key
    ([{"f": 0, "ref": "closed", "ease": "hold", "dur_f": 2}], "ANIM_LIDS"),
])
def test_lids_rules_fire(lids, code):
    d = with_ren(v2(), lids=lids)
    assert ("ERROR", code) in codes(d, shot_characters=["ren"])


def test_lids_key_inside_a_look_closed_span_is_an_error():
    d = with_ren(v2(), look=[{"f": 0, "target": "phone"}, {"f": 20, "target": "closed"}, {"f": 30, "target": "phone"}],
                 lids=[{"f": 25, "ref": "low"}])
    assert ("ERROR", "ANIM_LIDS") in codes(d, shot_characters=["ren"])
    d = with_ren(v2(), look=[{"f": 0, "target": "phone"}, {"f": 20, "target": "closed"}, {"f": 30, "target": "phone"}],
                 lids=[{"f": 30, "ref": "low"}])                                        # span ends at f29
    assert ("ERROR", "ANIM_LIDS") not in codes(d, shot_characters=["ren"])


def test_hold_all_blocks_lids_but_hold_face_does_not():
    d = with_ren(v2(), lids=BLINK)
    d["holds"] = [{"f0": 20, "f1": 38, "scope": "all"}]
    assert ("ERROR", "ANIM_HOLD") in codes(d, shot_characters=["ren"])
    d["holds"] = [{"f0": 20, "f1": 38, "scope": "face"}]
    assert ("ERROR", "ANIM_HOLD") not in codes(d, shot_characters=["ren"])


# ---------------------------------------------------------------- props
def cable(*keys, **kw):
    return v2(props={"charging_cable": list(keys)}, **kw)


def test_charging_cable_transitions():
    ok = cable({"f": 0, "loc": "glovebox", "state": "hidden"}, {"f": 5, "state": "posed"},
               {"f": 10, "loc": "hand_r"}, {"f": 20, "loc": "car_usb_adapter"})
    assert not [c for c in codes(ok, shot_characters=["ren"]) if c[0] == "ERROR"]
    bad = cable({"f": 0, "loc": "glovebox"}, {"f": 10, "loc": "shop_socket"})            # glovebox -> hand_r only
    assert ("ERROR", "ANIM_PROP_TRANSITION") in codes(bad, shot_characters=["ren"])
    bad = cable({"f": 0, "loc": "elsewhere"})
    assert ("ERROR", "ANIM_VOCAB") in codes(bad, shot_characters=["ren"])
    bad = cable({"f": 0, "attach": "hand_l"})
    assert ("ERROR", "ANIM_PROP") in codes(bad, shot_characters=["ren"])


def test_hidden_is_only_for_the_cable_state():
    bad = v2(props={"pencil": [{"f": 0, "state": "hidden"}]})
    assert ("ERROR", "ANIM_VOCAB") in codes(bad, shot_characters=["ren"])


def test_shop_door_swing_back():
    ok = v2(props={"shop_door": [{"f": 0, "state": "open_70"},
                                 {"f": 14, "state": "swing_back", "ease": "ease_in"}]})
    assert not [c for c in codes(ok, shot_characters=["ren"]) if c[0] == "ERROR"]
    pinned = v2(props={"shop_door": [{"f": 0, "state": "open_70", "swing_deg": 35.0}]})
    assert not [c for c in codes(pinned, shot_characters=["ren"]) if c[0] == "ERROR"]
    bad = v2(props={"shop_door": [{"f": 0, "state": "closed"}, {"f": 5, "state": "swing_back"}]})
    assert ("ERROR", "ANIM_PROP_TRANSITION") in codes(bad, shot_characters=["ren"])


# ---------------------------------------------------------------- qa_motion: chained_fields
def _cab(sid, **key):
    return S(sid, tracks=T(sid, props={"charging_cable": [key]}))


def test_cable_chains_loc_but_not_state():
    a = _cab("SC03_SH050", f=0, loc="shop_socket", state="posed")
    hide = _cab("SC03_SH060", f=0, loc="shop_socket", state="hidden")                  # state may change at any cut
    assert not hits(run(a, hide), "SC03_SH060", "FAIL", "charging_cable")
    jump = _cab("SC03_SH060", f=0, loc="hand_r", state="posed")                        # loc may not
    assert hits(run(a, jump), "SC03_SH060", "FAIL", "charging_cable.loc jumps at the cut")
    illegal = _cab("SC03_SH060", f=3, loc="car_usb_adapter")
    assert hits(run(a, illegal), "SC03_SH060", "FAIL", "not a legal transition")
    stated = _cab("SC03_SH060", f=0, loc="loose", rationale="cut hides the unplugging")
    assert not hits(run(a, stated), "SC03_SH060", "FAIL", "charging_cable")


def test_prop_chained_fields_default_is_every_tracked_field():
    assert V.prop_chained_fields("charging_cable", ("state", "loc")) == ("loc",)
    assert V.prop_chained_fields("glovebox_lid", ("state", "loc")) == ("state", "loc")


# ---------------------------------------------------------------- resolver: v2 tracks reach the resolved motion block
def test_resolved_motion_carries_lids_cable_and_shop_door_v2():
    from fm.motion import build_motion, vocab_canon_refs
    d = with_ren(v2(), lids=[{"f": 0, "ref": "open", "ease": "hold"}, {"f": 8, "ref": "closed", "ease": "ease_in", "dur_f": 4,
                                                                      "note": "blink"}])
    d["props"] = {
        "charging_cable": [{"f": 0, "loc": "hand_r", "state": "posed"}, {"f": 12, "loc": "shop_socket"}],
        "shop_door": [{"f": 0, "state": "open_70"}, {"f": 4, "state": "swing_back", "swing_deg": 40, "dur_f": 20}],
    }
    t = parse(d)
    m = build_motion(t, 1000, "artifact:x")
    assert [(k["f"], k["f_abs"], k["ref"]) for k in m["characters"]["ren"]["lids"]] == [(0, 1000, "open"), (8, 1008, "closed")]
    assert m["characters"]["ren"]["lids"][1]["dur_f"] == 4 and "note" not in m["characters"]["ren"]["lids"][1]
    cab = m["props"]["charging_cable"]
    assert [(k["loc"], k.get("state")) for k in cab] == [("hand_r", "posed"), ("shop_socket", None)]
    assert m["props"]["shop_door"][1]["state"] == "swing_back" and m["props"]["shop_door"][1]["swing_deg"] == 40
    info = m["prop_info"]
    assert info["charging_cable"]["chained_fields"] == ["loc"]            # only the source end chains across cuts
    assert info["charging_cable"]["persistent"] is True
    assert info["charging_cable"]["before_first_key"] == {"loc": "glovebox", "state": "hidden"}
    assert "swing_deg" in info["shop_door"]["fields"] and info["shop_door"]["persistent"] is False and info["shop_door"]["chained_fields"] == []
    refs = vocab_canon_refs(t)
    assert {"canon:animation.vocab.v2.lids", "canon:animation.vocab.v2.prop.charging_cable",
            "canon:animation.vocab.v2.prop.shop_door"} <= refs
    # no lids track: an empty list, not a missing key
    assert build_motion(parse(with_ren(v2())), 0, "x")["characters"]["ren"]["lids"] == []
