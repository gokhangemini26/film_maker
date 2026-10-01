"""Animation vocabulary: the shared enum module (M6-lite, `animation.vocab.*`).

Anim files (`09_animation/<SHOT>.anim.yaml`) never contain free text a builder has
to interpret. Everything a builder, mixer or QA check reads is a NAME from this
module. The names are proposed to canon as `animation.vocab.*` (see
`canon_entry_dicts`) and ratified by the human; the geometry behind each pose name
lives in the Blender package (`poses.py`, blender-td), and a test keeps the two in step.

The lists were derived from the 224 free-text `{f, t, pose}` keys and the prop/ui
prose in the 38 resolved Last Signal shots. They are deliberately short: each preset
is a body configuration, small motion (breath, blink, tuft, hands on a prop) is carried
by the face / look / breath / prop tracks and by blending between presets.

Changing a name here is a vocabulary change: bump `VOCAB_VERSION`; every anim file
written against the old version is then reported (ANIM_VOCAB_VERSION) and its shot goes
stale through the canon entry hash.
"""
from __future__ import annotations

VOCAB_VERSION = 2
# Anim files written against any of these versions are accepted: v2 only ADDS names and tightens five
# presets (no renames), so every v1 key stays legal. Names that exist only in v2 are listed in the
# V2_* tables below; a file that says `vocab_version: 1` may not use them.
ACCEPTED_VOCAB_VERSIONS = (1, 2)

# ------------------------------------------------------------------ eases
EASES: dict[str, str] = {
    "hold": "no interpolation: the value stays until the next key",
    "step": "switch in one frame at the key (cel switch)",
    "linear": "constant rate between keys",
    "ease_in": "starts slow, ends fast (falls with weight)",
    "ease_out": "starts fast, ends slow (quick burst that settles)",
    "ease_in_out": "slow at both ends (the default for deliberate moves)",
    "overshoot_small": "ease-out with one small overshoot before it settles (crown-tuft spring)",
    "gravity": "accelerating fall with a short bounce at the stop (crank drop, lid drop)",
}

# ------------------------------------------------------------------ poses (body configurations)
POSES: dict[str, dict[str, str]] = {
    "ren": {
        # car (driver's seat)
        "car_upright": "Seated upright behind the wheel, hands on the top of the wheel, eyes ahead.",
        "car_reach_up": "Seated, right arm raised to the mirror or the crown tuft, left hand low with the phone.",
        "car_phone_up": "Seated, phone raised to chest or face height in both hands, elbows tucked, neck forward.",
        "car_sag": "Seated, shoulders dropped and head forward, phone fallen to the lap (the letdown).",
        "car_lean_glovebox": "Torso tipped across the cabin, right arm out to the glovebox latch (reach about 0.75 m).",
        "car_recline": "Sunk back into the seat, head on the headrest, arms slack (relief, eyes closed).",
        "car_forehead_wheel": 'Forehead on the top of the wheel rim, spine curled, head pitched 45 deg or more, face hidden from the lens.',
        # street and shop
        "run_phone_out": "Upright running stance, phone arm straight out ahead, right forearm tucked, arms not swinging.",
        "scramble_out": "Ducked in the passenger doorway (crown 1.40 m or lower), phone hand thrust out ahead, right hand pushing off the sill.",
        "kneel_upright": "Kneeling on both knees, torso upright, phone tucked at the chest (shop aisle).",
        "kneel_reach_stand": "kneel_upright turned 25 deg and leaning 12 deg to the display stand, right arm behind its back edge to the socket.",
        "kneel_head_back": "kneel_upright with the head tipped back about 8 deg, chest open 2 deg; hands and phone stay put.",
        # kerb
        "kerb_hunch": "Seated on the kerb, back to the car, knees up, forearms loose over the knees, neck forward.",
        "kerb_crank_hold": "Kerb seat as kerb_hunch, crank across the knee tops, right hand on the knob, left hand follows crank_charger.loc.",
        "kerb_lean_back": "Seated on the kerb, spine reclined against the car's rear quarter, knees open, head tipping up.",
        "lunge_low": "Right knee down, left foot forward, low lunge toward the passenger doorway.",
        "lunge_reach": "Lunge leaning in through the doorway (crown under the roof), left forearm on the seat edge, right hand on the glovebox latch.",
    },
    "hana": {
        "desk_sketch": "Seated at the desk, head tilted down over the sketchbook, right hand drawing, headphones on.",
        "desk_notice": "Seated, head turned 25 deg toward the phone (yaw only), eyes lead; the pencil state comes from the pencil track.",
        "desk_headphones_off": "Both hands at the ear cups, sliding the headphones down to the neck.",
        "desk_phone_low": "Seated, phone low near the chest in both hands, headphones on the neck, eyes on the screen.",
    },
}

# ------------------------------------------------------------------ faces (from canon expressions)
FACES: dict[str, dict[str, tuple[str, ...]]] = {
    "ren": {
        # characters.ren.expressions value.comic_set / tender_set, plus neutral
        "comic": ("rehearsed_breath", "letdown", "freeze", "relief", "stunned_stillness", "wary", "determined"),
        "tender": ("focused_calm", "hesitation_at_heart", "release_after_send", "final_look_up"),
        "neutral": ("neutral",),
    },
    "hana": {
        # characters.hana.expressions value.sequence
        "sequence": ("absorbed", "noticing", "reading", "small_smile"),
    },
}
# From this shot on (film order) Ren's comic set is illegal (tone.the_turn).
COMIC_ENDS_BEFORE = "SC04_SH030"

# ------------------------------------------------------------------ lids (v2)
# Per-character lids track: a multiplier on the face's own eye openness; the gaze is kept.
LIDS: dict[str, float] = {
    "open": 1.0,     # upper lids at the face's own openness
    "low": 0.55,     # heavy lids (tired, tender)
    "closed": 0.0,   # lids shut
}
BLINK_TIMING_F = {"close": (2, 4), "shut": (1, 2), "open": (3, 6), "total_min": 6}

# ------------------------------------------------------------------ eyeline targets
LOOK_TARGETS: dict[str, str] = {
    "mirror": "the rear-view mirror",
    "phone": "the character's own phone",
    "dash": "the dashboard",
    "glovebox": "the glovebox",
    "lap": "the lap",
    "crank": "the crank charger",
    "road_ahead": "ahead through the windscreen or along the street",
    "shop_door": "the shop door",
    "wall_left": "the left wall of the aisle",
    "wall_right": "the right wall of the aisle",
    "socket": "the wall socket / stand corner",
    "ceiling": "the ceiling panels",
    "sky": "up and west toward the afterglow",
    "sketchbook": "the sketchbook page",
    "off_frame": "off frame (implied, nothing to aim at)",
    "camera": "the lens (Ren never looks here in Last Signal)",
    "closed": "eyes closed",
}

# ------------------------------------------------------------------ breath
BREATHS: dict[str, str] = {
    "in_slow": "slow breath in, shoulders rise about 1 cm",
    "out_slow": "slow breath out, shoulders fall about 1 cm",
    "out_long": "one long out-breath, shoulders drop 2-3 cm",
    "hold": "breath held: nothing moves",
    "crank_locked": "in on the up half-turn of the crank, out on the down half-turn",
}

# ------------------------------------------------------------------ gaits
GAITS: dict[str, dict] = {
    "none": {"locomotion": False, "desc": "no travel; the pose track carries the body"},
    "run_phone_out": {"locomotion": True, "desc": "run with the phone arm rigid (arms not swinging), a step every 6 frames"},
    "scramble": {"locomotion": True, "desc": "crouched exit from the car into the first strides"},
    "crank_turn": {"locomotion": False, "desc": "24-frame handle cycle; handle_top events every 24 frames"},
}
CRANK_CYCLE_F = 24

# ------------------------------------------------------------------ props
# fields: field name -> allowed values (tuple) or "unit" (0..1) or "deg" (float degrees) or "frames" (int >= 0)
PROPS: dict[str, dict] = {
    "passenger_door": {
        "desc": "Ren's passenger door (continuity.props.passenger_door).",
        "fields": {"state": ("closed", "open_60"), "swing_deg": "deg"},
        "transitions": {"state": {"closed": ("open_60",), "open_60": ("closed",)}},
        "persistent": True,
    },
    "glovebox_lid": {
        "desc": "Glovebox lid: drops by gravity or is lowered by hand.",
        "fields": {"state": ("closed", "open_down"), "bounce_f": "frames"},
        "transitions": {"state": {"closed": ("open_down",), "open_down": ("closed",)}},
        "persistent": True,
    },
    "crank_charger": {
        "desc": "The crank charger: where it is, whether the arm is out, pip brightness.",
        "fields": {
            "loc": ("glovebox", "falling", "thighs", "lap", "hand_r", "hands_both", "knees"),
            "arm": ("folded", "unfolded"),
            "pip": "unit",
        },
        "transitions": {
            "loc": {
                "glovebox": ("falling", "hand_r"),
                "falling": ("thighs",),
                "thighs": ("glovebox", "hand_r", "hands_both", "lap"),
                "hand_r": ("hands_both", "glovebox", "lap"),
                "hands_both": ("lap", "knees", "hand_r"),
                "lap": ("knees", "hands_both", "hand_r"),
                "knees": ("lap", "hands_both", "hand_r"),
            },
            "arm": {"folded": ("unfolded",), "unfolded": ("folded",)},
        },
        "persistent": True,
    },
    "phone_ren": {
        "desc": "Ren's phone: which hand or surface holds it (the screen comes from ui_timeline).",
        "fields": {"attach": ("hand_l", "hand_r", "hands_both", "lap", "knee", "chest", "car_strip")},
        "transitions": {},
        "persistent": True,
    },
    "phone_hana": {
        "desc": "Hana's phone: on the desk or in her hands.",
        "fields": {"attach": ("desk", "hand_r", "hands_both")},
        "transitions": {},
        "persistent": True,
    },
    "rear_view_mirror": {
        "desc": "Rear-view mirror tilt, keyed to the hand contact.",
        "fields": {"tilt_deg": "deg"},
        "transitions": {},
        "persistent": True,
    },
    "hana_headphones": {
        "desc": "Hana's headphones (world.props.hana_headphones: two positions and an arc between them).",
        "fields": {"state": ("head", "neck")},
        "transitions": {"state": {"head": ("neck",), "neck": ("head",)}},
        "persistent": True,
    },
    "pencil": {
        "desc": "Hana's pencil.",
        "fields": {"state": ("held", "laid")},
        "transitions": {"state": {"held": ("laid",), "laid": ("held",)}},
        "persistent": True,
    },
    "car_body": {
        "desc": "Car body motion presets (amplitude and decay are constants in poses.py).",
        "fields": {"state": ("still", "idle_tremble", "cough", "sigh_sink", "stall_shudder", "sway_1cm")},
        "transitions": {},
        "persistent": False,
    },
    "dash_lights_and_adapter_ring": {
        "desc": "Dash lights and the adapter ring LED.",
        "fields": {"state": ("on", "off")},
        "transitions": {"state": {"on": ("off",), "off": ("on",)}},
        "persistent": True,
    },
    "shop_door": {
        "desc": "Shop door; swing_back is the closer decay (about 70 -> 0 deg over about 36 frames) and carries on past the cut.",
        "fields": {"state": ("closed", "open_70", "swing_back"), "swing_deg": "deg"},
        "transitions": {"state": {"closed": ("open_70",), "open_70": ("swing_back", "closed"),
                                  "swing_back": ("closed", "open_70")}},
        "persistent": False,
    },
    "shop_lights": {
        "desc": "Shop ceiling panels, fridges and fascia sign (the blackout is one frame).",
        "fields": {"state": ("on", "off")},
        "transitions": {"state": {"on": ("off",), "off": ("on",)}},
        "persistent": True,
    },
    "charging_cable": {
        "desc": "Ren's one charging cable (continuity.props.cable): a posed curve, phone end always on phone_ren; `loc` is the source end.",
        "fields": {
            "loc": ("glovebox", "hand_r", "car_usb_adapter", "hand_l_loop", "shop_socket", "loose", "crank_port"),
            "state": ("posed", "hidden"),
        },
        "transitions": {
            "loc": {
                "glovebox": ("hand_r",),
                "hand_r": ("car_usb_adapter", "shop_socket", "crank_port", "hand_l_loop", "glovebox", "loose"),
                "car_usb_adapter": ("hand_l_loop", "hand_r"),
                "hand_l_loop": ("hand_r", "loose"),
                "shop_socket": ("loose", "hand_l_loop", "hand_r"),
                "loose": ("hand_r", "hand_l_loop"),
                "crank_port": ("loose", "hand_r"),
            },
            "state": {"posed": ("hidden",), "hidden": ("posed",)},
        },
        "persistent": True,
        # only the source end chains across cuts; posed/hidden is framing and may change at any cut
        "chained_fields": ("loc",),
        "before_first_key": {"loc": "glovebox", "state": "hidden"},
        "phone_end": "phone_ren",
    },
    "ceiling_panels": {
        "desc": "Ceiling panels: `steady` is a deliberate no-op QA can assert (the gag is the absence).",
        "fields": {"state": ("steady",)},
        "transitions": {},
        "persistent": False,
    },
}
# Fields every prop key may also carry (typed, not per prop).
PROP_COMMON_FIELDS = ("ease", "dur_f")

# ------------------------------------------------------------------ camera, holds, events, ui
CAMERA_MOVES: dict[str, str] = {
    "none": "locked off",
    "dolly_in": "straight push toward the subject (camera.movement.push_in)",
}
HOLD_SCOPES: dict[str, str] = {
    "body": "no pose change inside the span",
    "face": "no face change inside the span",
    "phone": "phone and thumb stay put (insert legibility holds)",
    "all": "nothing moves",
}
EVENT_KINDS: dict[str, str] = {
    "sound": "an audible sync point (the sound-designer cues it by id)",
    "light": "a lighting change (blackout, indicator on/off)",
    "state": "a prop or screen state change worth naming",
    "visual": "a visual beat with no sound (a blink, a contact)",
}
UI_EVENTS: dict[str, str] = {
    "dip": "brightness dip to `value` (default 0.7) for `dur_f` frames (flicker, charge lost)",
    "key_press": "a key darkens for `dur_f` frames; `key` is any, emoji, backspace or send",
    "text": "reveal `chars` characters of `line` over `dur_f` frames (typing)",
    "pulse": "the call button pulses over `dur_f` frames",
    "slide": "the screen changes to `to` over `dur_f` frames (1 = in one frame)",
    "heart": "the heart glyph is visible for `dur_f` frames",
    "progress": "the amber send line fills over `dur_f` frames (linear)",
    "tick": "the amber delivered tick appears whole at `f` and stays",
    "photo_scale": "the caller photo scales `from_pct` -> `to_pct` over `dur_f` frames (ease-out)",
}
UI_SCREENS = ("map", "call", "compose", "sent", "off", "wake", "received")
UI_KEYS = ("any", "emoji", "backspace", "send")
UI_PHONES = ("ren", "hana")

# ------------------------------------------------------------------ v2 additions
# Names that exist only from vocabulary v2 on (an anim file with vocab_version 1 may not use them).
V2_POSES: dict[str, tuple[str, ...]] = {"ren": ("kneel_reach_stand", "kneel_head_back")}
V2_FACES: dict[str, tuple[str, ...]] = {"ren": ("wary", "determined")}
V2_PROPS: tuple[str, ...] = ("charging_cable",)
V2_PROP_VALUES: dict[tuple[str, str], tuple[str, ...]] = {("shop_door", "state"): ("swing_back",)}
V2_PROP_FIELDS: dict[str, tuple[str, ...]] = {"shop_door": ("swing_deg",)}
V2_TRACKS: tuple[str, ...] = ("lids",)
# v1 text of the presets v2 tightened (kept so the v1 canon proposals still match the module)
_V1_POSE_DESCS: dict[str, str] = {
    "car_forehead_wheel": "Head lowered until the forehead rests on the top of the wheel rim, shoulders sagged.",
    "scramble_out": "Ducked and unfolding out of the passenger doorway below the 1.45 m roof line.",
    "kerb_crank_hold": "Seated on the kerb as kerb_hunch with the crank held in both hands in the lap (cranking base).",
    "lunge_reach": "Lunge leaning in through the doorway, left forearm on the seat edge, right arm to the glovebox.",
    "desk_notice": "Seated, head turned about 25 deg toward the lit phone, pencil laid down."
}

_V1_PROP_DESCS: dict[str, str] = {"shop_door": "Shop door (swing continues after the cut)."}


def v2_only_pose(character: str, name: str) -> bool:
    return name in V2_POSES.get(character, ())


def v2_only_face(character: str, name: str) -> bool:
    return name in V2_FACES.get(character, ())


def prop_chained_fields(prop: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Fields of a persistent prop that must agree across cuts (default: every tracked field)."""
    spec = PROPS.get(prop, {})
    cf = spec.get("chained_fields")
    return tuple(f for f in default if f in cf) if cf is not None else tuple(default)


# ------------------------------------------------------------------ helpers
def all_pose_names() -> list[str]:
    return [n for names in POSES.values() for n in names]


def pose_names(character: str) -> tuple[str, ...]:
    return tuple(POSES.get(character, {}))


def face_names(character: str) -> tuple[str, ...]:
    return tuple(n for group in FACES.get(character, {}).values() for n in group)


def comic_faces(character: str) -> tuple[str, ...]:
    return FACES.get(character, {}).get("comic", ())


def prop_fields(prop: str) -> dict:
    return PROPS[prop]["fields"]


def enum_groups() -> dict[str, tuple[str, ...]]:
    """Every named enum, flattened, for uniqueness tests and JSON-schema export."""
    g: dict[str, tuple[str, ...]] = {
        "ease": tuple(EASES), "look_target": tuple(LOOK_TARGETS), "breath": tuple(BREATHS),
        "gait": tuple(GAITS), "prop": tuple(PROPS), "camera_move": tuple(CAMERA_MOVES),
        "hold_scope": tuple(HOLD_SCOPES), "event_kind": tuple(EVENT_KINDS), "ui_event": tuple(UI_EVENTS),
        "ui_screen": UI_SCREENS, "ui_key": UI_KEYS, "lids": tuple(LIDS),
    }
    for ch in POSES:
        g[f"pose.{ch}"] = tuple(POSES[ch])
    for ch in FACES:
        g[f"face.{ch}"] = face_names(ch)
    for prop, spec in PROPS.items():
        for fld, allowed in spec["fields"].items():
            if isinstance(allowed, tuple):
                g[f"prop.{prop}.{fld}"] = allowed
    return g


# ------------------------------------------------------------------ canon proposals
def _v1_view() -> tuple[dict, dict, dict]:
    """(POSES, FACES, PROPS) as vocabulary v1 had them. The `animation.vocab.*` proposals describe v1;
    v2 is specified by the `animation.vocab.v2.*` entries (the PROPOSED v2 canon), so the two never mix."""
    poses = {ch: {n: _V1_POSE_DESCS.get(n, d) for n, d in t.items() if n not in V2_POSES.get(ch, ())}
             for ch, t in POSES.items()}
    faces = {ch: {g: tuple(n for n in names if n not in V2_FACES.get(ch, ())) for g, names in grp.items()}
             for ch, grp in FACES.items()}
    props = {}
    for name, spec in PROPS.items():
        if name in V2_PROPS:
            continue
        flds = {f: (tuple(x for x in a if x not in V2_PROP_VALUES.get((name, f), ())) if isinstance(a, tuple) else a)
                for f, a in spec["fields"].items() if f not in V2_PROP_FIELDS.get(name, ())}
        trans = {f: {k: tuple(x for x in v if x not in V2_PROP_VALUES.get((name, f), ()))
                     for k, v in m.items() if k not in V2_PROP_VALUES.get((name, f), ())}
                 for f, m in spec["transitions"].items()}
        props[name] = {**spec, "desc": _V1_PROP_DESCS.get(name, spec["desc"]), "fields": flds, "transitions": trans}
    return poses, faces, props


def canon_entry_dicts() -> list[dict]:
    """The v1 vocabulary as PROPOSED canon entries (`animation.vocab.*`), each with a rationale.
    The human ratifies them at G7; agents only ever write PROPOSED. v2 lives in `animation.vocab.v2.*`."""
    v1_poses, v1_faces, v1_props = _v1_view()
    common = {"tag": "DECISION", "status": "PROPOSED", "source": "agent:animation-director", "version": 1}
    ver = {"vocab_version": 1}

    def entry(eid, statement, value, rationale, serves, depends_on):
        return {"id": f"animation.vocab.{eid}", "statement": statement, "value": {**ver, **value},
                "rationale": rationale, "serves": serves, "depends_on": depends_on, **common}

    return [
        entry("pose.ren", "Ren's pose presets: the only body configurations an anim file may name for Ren.",
              {"presets": dict(v1_poses["ren"])},
              "Derived from the 224 free-text keys in the shot animation blocks. Each preset is one body "
              "configuration a builder can pose from joints; hands on props, breath, blink and the tuft are "
              "carried by other tracks so the list stays short. Rejected: a preset per prose key (about 90 "
              "near-duplicates) and keeping prose that a regex reads (it cannot tell 'lowered' from 'opened').",
              ["intent.comic_then_tender", "intent.anime_feel"],
              ["characters.ren.movement", "characters.ren.representation"]),
        entry("pose.hana", "Hana's pose presets.",
              {"presets": dict(v1_poses["hana"])},
              "Hana has one desk and four beats (absorbed, noticing, headphones off, reading); four presets "
              "cover them and the blends between. Rejected: a rig for a character who never stands.",
              ["intent.open_hopeful_ending"],
              ["characters.hana.movement", "characters.hana.representation"]),
        entry("face", "Face refs: Ren's comic and tender sets, plus neutral; Hana's four states.",
              {"ren": {k: list(v) for k, v in v1_faces["ren"].items()},
               "hana": {k: list(v) for k, v in v1_faces["hana"].items()},
               "comic_illegal_from_shot": COMIC_ENDS_BEFORE},
              "Taken from characters.*.expressions, not invented. The comic set is illegal from "
              "SC04_SH030 on so the change of key (tone.the_turn) is checkable on his face.",
              ["intent.comic_then_tender", "intent.open_hopeful_ending"],
              ["characters.ren.expressions", "characters.hana.expressions", "tone.the_turn"]),
        entry("look_target", "Eyeline targets the builder resolves to objects in the set.",
              {"targets": dict(LOOK_TARGETS)},
              "Eyelines carry most of the acting in this film. A closed list lets the builder aim the head "
              "and eyes and lets QA check that a target exists in the shot's location.",
              ["intent.comic_then_tender"], []),
        entry("breath", "Breath refs for the breath track.",
              {"breaths": dict(BREATHS)},
              "Breath is the main motion of the held shots, and the ratchet is locked to it after the turn.",
              ["intent.comic_then_tender"], ["tone.the_turn"]),
        entry("gait", "Gaits and their cycle constants.",
              {"gaits": {k: dict(v) for k, v in GAITS.items()}, "crank_cycle_f": CRANK_CYCLE_F},
              "Only five shots travel. crank_turn is one 24-frame handle cycle so the ratchet phase "
              "(handle_top events) has a single source.",
              ["intent.race_against_battery"], ["characters.ren.movement"]),
        entry("ease", "Ease names for pose blends and prop tracks.",
              {"eases": dict(EASES)},
              "The shot prose uses eight timing words; naming them stops each builder guessing its own curve.",
              ["intent.anime_feel"], []),
        entry("prop_states", "Prop state enums and their legal transitions.",
              {"props": {p: {"desc": s["desc"], "fields": {f: (list(a) if isinstance(a, tuple) else a)
                                                            for f, a in s["fields"].items()},
                             "transitions": {f: {k: list(v) for k, v in m.items()}
                                             for f, m in s["transitions"].items()},
                             "persistent": s["persistent"]} for p, s in v1_props.items()}},
              "Props are where prose was ambiguous: SC04_SH040 'lowered by hand ... left down' was read as "
              "open, and the crank is 'in the closed glovebox' in SC04_SH010. An enum (closed | open_down) "
              "settles it and makes cross-shot continuity checkable.",
              ["intent.race_against_battery"],
              ["continuity.props.passenger_door", "continuity.props.glovebox_and_crank",
               "continuity.props.phone_ren", "continuity.hana.headphones"]),
        entry("ui_event", "Phone-screen events an anim file may add on top of the states_by_shot table.",
              {"events": dict(UI_EVENTS), "screens": list(UI_SCREENS), "keys": list(UI_KEYS)},
              "The canon table fixes the base state per shot; flicker dips, key presses, typing and the "
              "send line need frame-exact events the table does not carry.",
              ["intent.race_against_battery"],
              ["look.style.phone_screen.states_by_shot", "look.style.phone_ui"]),
        entry("event_kind", "Kinds of named sync events, plus the camera moves and hold scopes an anim file may use.",
              {"kinds": dict(EVENT_KINDS), "camera_moves": dict(CAMERA_MOVES), "hold_scopes": dict(HOLD_SCOPES)},
              "Named events are the sync points audio, QA and editors read by id; the kind says which are "
              "audible.",
              ["intent.race_against_battery"], ["camera.movement.push_in"]),
    ]
