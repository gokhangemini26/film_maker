"""Pure-python (no bpy) hashing and reconcile logic for the persistent .blend.

A "unit" is one collection in the .blend: a set (street/shop/room), a character, a prop or a shot
(camera + timeline marker). Each carries fm_owner/fm_id/fm_hash. `unit_specs` derives the desired
units and the hash of the resolved inputs that produce each; `plan` compares that with what the
file already holds so only changed units are rebuilt.
"""
import hashlib
import json

from . import BUILDER_VERSION
from .assets import prop_names_used

COLOR_PREFIXES = ("look.color.",)   # what the builders read from look canon (materials only)


def h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def canon_subset(canon: dict, prefixes) -> dict:
    prefixes = tuple(prefixes)
    return {k: v for k, v in canon.items() if k.startswith(prefixes)}


def unit_specs(film: dict, shots: dict, version: str = BUILDER_VERSION) -> dict:
    """{unit_id: {kind, name, hash}} for everything the resolved data asks for, in build order."""
    canon = film.get("canon", {})
    colors = canon_subset(canon, COLOR_PREFIXES)
    specs = {}

    def add(uid, kind, name, inputs):
        specs[uid] = {"kind": kind, "name": name, "hash": h({"v": version, "in": inputs})}

    # sets: street is always built (generic stage when the film has no street canon)
    add("set:street", "set", "street", {"c": canon_subset(canon, ("world.sets.street", "world.sets.ren_car")), "col": colors})
    if "world.sets.corner_shop" in canon:
        add("set:shop", "set", "shop", {"c": canon_subset(canon, ("world.sets.corner_shop",)), "col": colors})
    if "world.sets.hana_room" in canon:
        add("set:room", "set", "room", {"c": canon_subset(canon, ("world.sets.hana_room",)), "col": colors})
    for cid in sorted({k.split(".")[1] for k in canon if k.startswith("characters.") and k.count(".") >= 2}):
        add(f"char:{cid}", "char", cid, {"c": canon_subset(canon, (f"characters.{cid}.",)), "col": colors})
    for pname in sorted(prop_names_used(shots)):
        add(f"prop:{pname}", "prop", pname, {"c": canon_subset(canon, (f"world.props.{pname}",)), "col": colors})
    fmt = film.get("format", {})
    for sid in film.get("shots", list(shots)):
        if sid in shots:
            add(f"shot:{sid}", "shot", sid, {"shot": shots[sid], "fps": fmt.get("fps")})
    return specs


def plan(desired: dict, existing: dict) -> dict:
    """desired/existing: {unit_id: hash}. Returns build (new+changed), unchanged, remove (orphans)."""
    new = [u for u in desired if u not in existing]
    changed = [u for u in desired if u in existing and existing[u] != desired[u]]
    unchanged = [u for u in desired if u in existing and existing[u] == desired[u]]
    remove = [u for u in existing if u not in desired]
    return {"new": new, "changed": changed, "unchanged": unchanged, "remove": remove,
            "build": [u for u in desired if u in new or u in changed]}


def report(p: dict, extra: dict | None = None) -> dict:
    r = {"built": p["build"], "created": p["new"], "rebuilt": p["changed"], "unchanged": p["unchanged"],
         "removed": p["remove"], "counts": {"built": len(p["build"]), "unchanged": len(p["unchanged"]), "removed": len(p["remove"])}}
    r.update(extra or {})
    return r
