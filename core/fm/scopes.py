"""Scopes for partial production: regenerate only what a request touches.

    film                         everything
    shot:SC01_SH010              one shot
    shots:SC01_SH010..SC02_SH030 an inclusive range (ordered by scene, shot)
    scene:SC01                   one scene
    sequence:SQ01                one sequence
    character:mara               a character's canon + every shot featuring them
    asset:neon_sign              shots/canon that use an asset
    ref:canon:look.color.primary any single node

A scope resolves to root nodes; the production set is the roots plus
everything downstream of them. `plan` intersects that set with what is
stale, so nothing unrelated is rebuilt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .deps import Graph
from .errors import FMError
from .project import Loaded

_SHOT_KEY = re.compile(r"^SC(\d+)_SH(\d+)$")


def shot_key(shot_id: str) -> tuple[int, int]:
    m = _SHOT_KEY.match(shot_id)
    if not m:
        raise FMError(f"invalid shot id '{shot_id}'")
    return int(m.group(1)), int(m.group(2))


@dataclass
class ScopeSet:
    scope: str
    roots: set[str]
    closure: set[str]  # roots + downstream

    @property
    def shots(self) -> list[str]:
        return sorted((r for r in self.closure if r.startswith("shot:")),
                      key=lambda r: shot_key(r.split(":", 1)[1]))


def resolve_scope(scope: str, loaded: Loaded, graph: Graph) -> ScopeSet:
    kind, _, arg = scope.partition(":")
    shots = loaded.shots
    roots: set[str]
    if scope in ("film", "all"):
        roots = set(graph.nodes)
    elif kind == "shot":
        if arg not in shots:
            raise FMError(f"unknown shot '{arg}'")
        roots = {f"shot:{arg}"}
    elif kind == "shots":
        lo, sep, hi = arg.partition("..")
        if not sep:
            raise FMError("range must be shots:FIRST..LAST, e.g. shots:SC01_SH010..SC01_SH040")
        klo, khi = shot_key(lo), shot_key(hi)
        if klo > khi:
            raise FMError(f"empty range: {lo} comes after {hi}")
        roots = {f"shot:{s}" for s in shots if klo <= shot_key(s) <= khi}
    elif kind == "scene":
        roots = {f"shot:{s}" for s, it in shots.items() if it.spec.scene_id == arg}
    elif kind == "sequence":
        roots = {f"shot:{s}" for s, it in shots.items() if it.spec.sequence_id == arg}
    elif kind == "character":
        roots = {f"canon:{c}" for c in loaded.canon if c.startswith(f"characters.{arg}.")}
        roots |= {f"shot:{s}" for s, it in shots.items() if any(c.id == arg for c in it.spec.characters)}
    elif kind == "asset":
        roots = {f"shot:{s}" for s, it in shots.items() if arg in it.spec.assets}
        roots |= {f"canon:{c}" for c in loaded.canon if f".assets.{arg}" in c or c.endswith(f".{arg}")}
    elif kind == "ref":
        if arg not in graph.nodes:
            raise FMError(f"unknown node '{arg}'")
        roots = {arg}
    else:
        raise FMError(f"unknown scope '{scope}' (film, shot:, shots:A..B, scene:, sequence:, "
                      "character:, asset:, ref:)")
    if not roots:
        raise FMError(f"scope '{scope}' matched nothing")
    return ScopeSet(scope, roots, roots | graph.downstream(roots))
