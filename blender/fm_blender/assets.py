"""ASSET_PREP contract (pure python): the assets shots ask for versus what the builders can make.

`CAPABILITIES` mirrors the builders in this package; keep it in step when a builder is added
(tests/test_blender_build.py pins it against the last known set).
"""

# asset id -> (how it is produced, where)
CAPABILITIES = {
    "world.sets.street": ("set", "sets.build_street"),
    "world.sets.ren_car": ("set", "sets.build_car (inside the street unit)"),
    "world.sets.corner_shop": ("set", "sets.build_shop"),
    "world.sets.hana_room": ("set", "sets.build_room"),
    "world.props.shop_socket": ("in_set", "sets.build_shop"),
    "world.props.sketchbook": ("in_set", "sets.build_room"),
    "world.props.desk_lamp": ("in_set", "sets.build_room"),
    "world.props.phone_ren": ("prop", "phone.build_phone"),
    "world.props.phone_hana": ("prop", "phone.build_phone"),
    "world.props.crank_charger": ("per_shot", "preview.render_shot (built per still; not yet in the persistent unit)"),
    "world.props.hana_headphones": ("character_part", "characters.figure (wardrobe.headphones)"),
    "ui.status_bar": ("ui", "phone.Screen.status_bar"),
    "ui.compose_field": ("ui", "phone.build_phone"),
    "ui.thread_sent_bubble": ("ui", "phone.build_phone"),
    "ui.call_screen": ("ui", "phone.build_phone"),
    "ui.map_pin_screen": ("ui", "phone.build_phone"),
    "ui.photo_only": ("ui", "phone.build_phone"),
}
# props that get their own persistent unit (prop:<name>)
PROP_UNITS = ("phone_ren", "phone_hana")


def prop_names_used(shots: dict) -> set:
    used = set()
    for s in shots.values():
        for a in s.get("assets", []):
            n = a.split("world.props.", 1)[1] if a.startswith("world.props.") else None
            if n in PROP_UNITS:
                used.add(n)
    return used


def check(shots: dict, canon: dict | None = None) -> dict:
    """Per-asset usage and gaps. Unknown = no builder produces it (ui.* and world.* only are in scope)."""
    canon = canon or {}
    needs = {}
    for sid, s in shots.items():
        for a in s.get("assets", []):
            if a.startswith(("world.", "ui.")):
                needs.setdefault(a, []).append(sid)
    rows = []
    for a in sorted(needs):
        cap = CAPABILITIES.get(a)
        rows.append({"asset": a, "shots": sorted(needs[a]), "status": "ok" if cap else "UNKNOWN",
                     "how": cap[0] if cap else None, "builder": cap[1] if cap else None,
                     "in_canon": (a in canon) if a.startswith("world.") else None})
    unknown = [r["asset"] for r in rows if r["status"] == "UNKNOWN"]
    return {"assets": rows, "unknown": unknown, "shots": len(shots),
            "summary": {"needed": len(rows), "buildable": len(rows) - len(unknown), "unknown": len(unknown)}}
