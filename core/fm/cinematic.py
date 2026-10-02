"""Opt-in cinematic blocks in the resolver and in `fm validate`: `atmosphere` (HDRI + fog) and `grade`.

Per shot, the effective block is the first of:
  1. the shot spec's own `atmosphere:` / `grade:` block (rationale required),
  2. a canon entry `look.atmosphere.*` / `look.grade.*` whose `applies_to` names the shot, then one that names its scene,
  3. the film-wide canon entry `look.atmosphere` / `look.grade` (empty `applies_to`).
Two entries at the same specificity are ambiguous and refused. Nothing is added to a resolved shot (or to its dependency list)
when no block applies, so a film that never uses them resolves to the same bytes as before.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .errors import FMError
from .schemas.cinematic import CANON_ATMOSPHERE, CANON_GRADE, Atmosphere, Grade

KINDS = {"atmosphere": (CANON_ATMOSPHERE, Atmosphere), "grade": (CANON_GRADE, Grade)}
_BUILDERS = Path(__file__).resolve().parents[2] / "blender"


def fm_atmosphere():
    """fm_blender.atmosphere (pure Python at import time) for the asset checks, without bpy."""
    if str(_BUILDERS) not in sys.path:
        sys.path.insert(0, str(_BUILDERS))
    from fm_blender import atmosphere
    return atmosphere


def canon_entries(loaded, base: str) -> list:
    return [(cid, it) for cid, it in sorted(loaded.canon.items()) if cid == base or cid.startswith(base + ".")]


def pick_canon(loaded, base: str, shot_id: str, scene_id: str):
    """The canon item that applies to this shot (most specific wins), or None. Ambiguity raises FMError."""
    best: dict[int, list] = {}
    for cid, it in canon_entries(loaded, base):
        scope = set(it.entry.applies_to)
        tier = 2 if shot_id in scope else 1 if scene_id in scope else 0 if not scope else -1
        if tier >= 0:
            best.setdefault(tier, []).append((cid, it))
    if not best:
        return None
    top = best[max(best)]
    if len(top) > 1:
        raise FMError(f"{shot_id}: canon entries {', '.join(c for c, _ in top)} all apply to it at the same specificity; "
                      "scope one of them with applies_to (shot or scene ids)")
    return top[0]


def resolve_blocks(loaded, spec) -> tuple[dict, set[str]]:
    """({'atmosphere': {...}, 'grade': {...}} for the blocks that apply, canon refs to add to the shot's derived_from)."""
    out: dict = {}
    refs: set[str] = set()
    for key, (base, model) in KINDS.items():
        own = getattr(spec, key)
        if own is not None:
            out[key] = {**own.model_dump(mode="json", exclude_none=True), "source": "shot"}
            continue
        hit = pick_canon(loaded, base, spec.shot_id, spec.scene_id)
        if hit is None:
            continue
        cid, it = hit
        try:
            block = model.model_validate(it.entry.value).model_dump(mode="json", exclude_none=True)
        except Exception as exc:  # noqa: BLE001
            raise FMError(f"canon {cid} is not a valid {key} block: {str(exc).splitlines()[0] if str(exc) else exc}") from exc
        out[key] = {**block, "source": f"canon:{cid}"}
        refs.add(f"canon:{cid}")
    return out, refs


def check_cinematic(project, loaded) -> list[tuple[str, str, str, str]]:
    """Findings (level, code, where, message) for `fm validate`. Empty for a film without these blocks."""
    F: list[tuple[str, str, str, str]] = []
    at = fm_atmosphere()
    lib = project.repo / "library"
    seen_hdri: dict[str, str | None] = {}

    def hdri_finding(hid: str, where: str) -> None:
        if hid not in seen_hdri:
            try:
                at.load_hdri_asset(hid, lib, require_file=False)
                seen_hdri[hid] = None
                try:
                    at.load_hdri_asset(hid, lib, require_file=True)
                except at.AtmosphereError as exc:
                    seen_hdri[hid] = "WARN:" + str(exc)       # record fine, file absent here (not committed): fatal only at render
            except at.AtmosphereError as exc:
                seen_hdri[hid] = "ERROR:" + str(exc)
        res = seen_hdri[hid]
        if res:
            lvl, _, msg = res.partition(":")
            F.append((lvl, "HDRI_ASSET", where, msg))

    for key, (base, model) in KINDS.items():
        for cid, it in canon_entries(loaded, base):
            where = project.rel(it.path)
            try:
                block = model.model_validate(it.entry.value)
            except Exception as exc:  # noqa: BLE001 - pydantic ValidationError and a non-mapping value alike
                F.append(("ERROR", "CINEMATIC_SCHEMA", where, f"{cid}: {str(exc).splitlines()[0] if str(exc) else exc}"))
                continue
            if not (it.entry.rationale or "").strip():
                F.append(("WARN", "MISSING_RATIONALE", where, f"{cid}: a {key} decision needs a rationale"))
            if key == "atmosphere" and block.hdri:
                hdri_finding(block.hdri.id, where)
    for sid, item in loaded.shots.items():
        where = project.rel(item.path)
        if item.spec.atmosphere is not None and item.spec.atmosphere.hdri:
            hdri_finding(item.spec.atmosphere.hdri.id, where)
        try:
            for base in (CANON_ATMOSPHERE, CANON_GRADE):
                pick_canon(loaded, base, item.spec.shot_id, item.spec.scene_id)
        except FMError as exc:
            F.append(("ERROR", "CINEMATIC_AMBIGUOUS", where, str(exc)))
    return F
