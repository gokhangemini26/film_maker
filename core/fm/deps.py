"""The production dependency graph.

    Creative intent -> Canon -> Creative artifacts -> Shot specs
      -> Resolved specs -> Blender scene -> Render -> QA

Edges come from:
  * `derived_from` on artifacts, shots and derived products (with the
    upstream hash recorded at production time -> staleness detection)
  * canon `depends_on` / `serves` (structural)
  * shots: `serves` -> intents; characters -> canon `characters.<id>.*`;
    continuity_refs; canon entries whose `applies_to` names the shot/scene/
    sequence/character (structural)

A node is STALE when a recorded upstream hash no longer matches, or when
any of its upstream nodes is stale. Impact of a change = everything
downstream of the changed nodes.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from .project import Loaded
from .schemas import LAYER_ORDER, DepRef, Layer, layer_of


@dataclass
class Node:
    ref: str
    layer: Layer
    hash: str | None
    deps: list[DepRef] = field(default_factory=list)


@dataclass
class Graph:
    nodes: dict[str, Node]
    down: dict[str, set[str]]  # upstream ref -> downstream refs
    missing: list[tuple[str, str]]  # (node, missing upstream ref)
    _stale: dict[str, list[str]] | None = field(default=None, repr=False)

    # ------------------------------------------------------------ queries
    def upstream(self, ref: str) -> set[str]:
        seen: set[str] = set()
        q = deque(d.ref for d in self.nodes[ref].deps) if ref in self.nodes else deque()
        while q:
            r = q.popleft()
            if r in seen:
                continue
            seen.add(r)
            if r in self.nodes:
                q.extend(d.ref for d in self.nodes[r].deps)
        return seen

    def downstream(self, refs) -> set[str]:
        seen: set[str] = set()
        q = deque(refs)
        while q:
            r = q.popleft()
            for d in self.down.get(r, ()):
                if d not in seen:
                    seen.add(d)
                    q.append(d)
        return seen

    def direct_staleness(self) -> dict[str, list[str]]:
        """node -> reasons, for nodes whose own recorded upstream hashes are outdated."""
        out: dict[str, list[str]] = {}
        for n in self.nodes.values():
            for d in n.deps:
                if d.hash is None:
                    continue
                cur = self.nodes[d.ref].hash if d.ref in self.nodes else None
                if cur is None:
                    out.setdefault(n.ref, []).append(f"{d.ref} no longer exists")
                elif cur != d.hash:
                    out.setdefault(n.ref, []).append(f"{d.ref} changed")
        return out

    def stale(self) -> dict[str, list[str]]:
        """All stale nodes: directly stale plus everything downstream of them.
        Cached: a Graph is an immutable snapshot of the project."""
        if self._stale is not None:
            return self._stale
        direct = self.direct_staleness()
        out = {k: list(v) for k, v in direct.items()}
        for ref in self.downstream(direct.keys()):
            if ref not in out:
                ups = sorted(u for u in self.upstream(ref) if u in direct)
                out[ref] = [f"upstream {u} is stale" for u in ups[:3]] or ["upstream is stale"]
        self._stale = out
        return out

    def impact(self, changed: list[str]) -> dict[Layer, list[str]]:
        return group_by_layer(self.downstream(changed))


def group_by_layer(refs) -> dict[Layer, list[str]]:
    grouped: dict[Layer, list[str]] = defaultdict(list)
    for r in refs:
        grouped[layer_of(r)].append(r)
    return {k: sorted(grouped[k]) for k in sorted(grouped, key=lambda l: LAYER_ORDER[l])}


def _canon_matching(loaded: Loaded, prefix: str) -> list[str]:
    return [cid for cid in loaded.canon if cid.startswith(prefix)]


def applies_index(loaded: Loaded) -> dict[str, list[str]]:
    applies: dict[str, list[str]] = defaultdict(list)
    for cid, item in loaded.canon.items():
        for target in item.entry.applies_to:
            applies[target].append(cid)
    return applies


def implicit_shot_deps(loaded: Loaded, spec, applies: dict[str, list[str]] | None = None) -> list[str]:
    """Dependencies a shot has by virtue of its content (intents it serves,
    characters in it, continuity refs, canon scoped to it). `fm stamp` records
    their hashes so a canon change makes exactly the right shots stale."""
    applies = applies if applies is not None else applies_index(loaded)
    out: list[str] = []

    def add(ref: str) -> None:
        if ref not in out:
            out.append(ref)

    for intent in spec.serves:
        add(f"canon:{intent}")
    for ch in spec.characters:
        for cid in _canon_matching(loaded, f"characters.{ch.id}."):
            add(f"canon:{cid}")
    for ref in spec.continuity_refs:
        add(ref if ":" in ref else f"canon:{ref}")
    for target in (spec.shot_id, spec.scene_id, spec.sequence_id, *[c.id for c in spec.characters]):
        for cid in applies.get(target or "", []):
            add(f"canon:{cid}")
    return out


def build_graph(loaded: Loaded) -> Graph:
    nodes: dict[str, Node] = {}
    # canon + intent
    for cid, item in loaded.canon.items():
        deps = [DepRef(ref=f"canon:{d}") for d in item.entry.depends_on]
        deps += [DepRef(ref=f"canon:{s}") for s in item.entry.serves]
        nodes[item.ref] = Node(item.ref, layer_of(item.ref), item.hash, deps)
    applies = applies_index(loaded)
    # artifacts
    for aid, item in loaded.artifacts.items():
        deps = list(item.meta.derived_from)
        known = {d.ref for d in deps}
        deps += [DepRef(ref=f"canon:{s}") for s in item.meta.serves if f"canon:{s}" not in known]
        nodes[item.ref] = Node(item.ref, Layer.ARTIFACT, item.hash, deps)
    # shots
    for sid, item in loaded.shots.items():
        deps = list(item.spec.derived_from)
        known = {d.ref for d in deps}
        deps += [DepRef(ref=r) for r in implicit_shot_deps(loaded, item.spec, applies) if r not in known]
        nodes[item.ref] = Node(item.ref, Layer.SHOT, item.hash, deps)
    # derived products
    for ref, rec in loaded.derived.items():
        nodes[ref] = Node(ref, layer_of(ref), rec.content_hash, list(rec.derived_from))

    down: dict[str, set[str]] = defaultdict(set)
    missing: list[tuple[str, str]] = []
    for n in nodes.values():
        for d in n.deps:
            down[d.ref].add(n.ref)
            if d.ref not in nodes:
                missing.append((n.ref, d.ref))
    return Graph(nodes, down, missing)
