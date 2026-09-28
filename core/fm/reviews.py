"""Gate review reports (qa/reviews/G#_REVIEW.md).

A review is an ordinary artifact written by the qa-supervisor. Its
`derived_from` must list everything the gate covers, so any later edit to a
reviewed item makes the review stale and blocks approval until it is redone.
Its verdict is advisory: a FAIL is shown prominently to the human but can
neither block nor pass a gate on its own.
"""
from __future__ import annotations

from .phases import Gate
from .project import ArtifactItem, Loaded, Project
from .roles import REVIEW_FOR_GATE, VERDICTS


def find_review(project: Project, gate_id: str, loaded: Loaded) -> ArtifactItem | None:
    rel = REVIEW_FOR_GATE.get(gate_id)
    if not rel:
        return None
    for a in loaded.artifacts.values():
        if project.rel(a.path) == rel:
            return a
    return None


def review_verdict(project: Project, gate_id: str, loaded: Loaded) -> str | None:
    r = find_review(project, gate_id, loaded)
    return str(r.extra.get("verdict")) if r else None


def review_problems(project: Project, gate: Gate, loaded: Loaded) -> list[str]:
    if gate.id not in REVIEW_FOR_GATE:
        return []
    r = find_review(project, gate.id, loaded)
    if r is None:
        return []  # absence is reported by the phase contract
    out = []
    if r.meta.kind != "gate_review":
        out.append(f"{REVIEW_FOR_GATE[gate.id]}: kind must be gate_review")
    if r.extra.get("verdict") not in VERDICTS:
        out.append(f"{REVIEW_FOR_GATE[gate.id]}: verdict must be one of {', '.join(VERDICTS)}")
    if r.extra.get("reviewed_gate") != gate.id:
        out.append(f"{REVIEW_FOR_GATE[gate.id]}: reviewed_gate must be {gate.id}")
    reviewed = {d.ref for d in r.meta.derived_from}
    required = {a.ref for a in loaded.artifacts.values()
                if a.meta.phase in gate.covers_phases and a.ref != r.ref}
    if gate.covers_shots:
        required |= {s.ref for s in loaded.shots.values()}
    missing = sorted(required - reviewed)
    if missing:
        out.append(f"{REVIEW_FOR_GATE[gate.id]} does not review: {', '.join(missing)}")
    return out
