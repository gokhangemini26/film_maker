"""Project state as a pure replay of the ledger.

`state.yaml` is only a readable cache. `replay()` is the single definition
of what the project's state *is*; `fm validate` compares the cache against
it and reports tampering.
"""
from __future__ import annotations

from .errors import IntegrityError
from .phases import GATES, PHASES
from .schemas import (
    Authorization, CanonLock, GateRecord, LedgerRecord, ProjectState, Status,
)


def replay(records: list[LedgerRecord]) -> ProjectState:
    if not records:
        raise IntegrityError("ledger is empty (project was never initialised)")
    first = records[0]
    if first.action != "project.init":
        raise IntegrityError("ledger does not start with project.init")
    p = first.payload
    st = ProjectState(
        project=p["project"], title=p["title"], sandbox=bool(p.get("sandbox")),
        created_at=first.ts, phase=PHASES[0],
        gates={gid: GateRecord() for gid in GATES},
    )
    for r in records:
        _apply(st, r)
        st.ledger_seq, st.ledger_head = r.seq, r.hash
    return st


def _apply(st: ProjectState, r: LedgerRecord) -> None:  # noqa: C901 - flat dispatch
    p, a = r.payload, r.action
    if a == "project.init":
        return
    if a == "phase.advance":
        st.phase, st.phase_status = p["to"], "in_progress"
    elif a == "phase.submit":
        st.phase_status = "awaiting_approval"
        if p.get("gate"):
            st.gates[p["gate"]].status = "awaiting_approval"
    elif a == "gate.decide":
        g = st.gates[p["gate"]]
        g.status = p["decision"]
        g.decided_by, g.decided_at, g.notes, g.ledger_seq = r.actor, r.ts, p.get("notes"), r.seq
        if p["decision"] == "approved":
            g.approved_hashes = dict(p.get("approved_hashes", {}))
            g.review_verdict = p.get("review_verdict")
            g.review_acknowledged = bool(p.get("review_acknowledged", False))
            g.amendments = 0
            for cid, lk in p.get("locked", {}).items():
                st.canon[cid] = CanonLock(status=Status.LOCKED, hash=lk["hash"],
                                          version=lk["version"], ledger_seq=r.seq)
            for cid, rj in p.get("rejected", {}).items():
                st.canon[cid] = CanonLock(status=Status.REJECTED, hash=rj["hash"],
                                          version=rj["version"], ledger_seq=r.seq)
            for ref in g.approved_hashes:
                if ref.startswith("artifact:"):
                    st.artifacts[ref] = Status.APPROVED
                elif ref.startswith("shot:"):
                    st.shots.setdefault(ref.split(":", 1)[1], "spec")
        if p.get("phase") == st.phase:
            st.phase_status = "in_progress"
    elif a in ("canon.approve", "canon.lock", "canon.reject"):
        status = {"canon.approve": Status.APPROVED, "canon.lock": Status.LOCKED,
                  "canon.reject": Status.REJECTED}[a]
        st.canon[p["id"]] = CanonLock(status=status, hash=p["hash"], version=p["version"],
                                      ledger_seq=r.seq)
    elif a == "change.propose":
        st.changes[p["change"]] = Status.PROPOSED
    elif a == "change.approve":
        st.changes[p["change"]] = Status.APPROVED
        prev = st.canon.get(p["target"])
        keep = prev.status if prev and prev.status in (Status.APPROVED, Status.LOCKED) else Status.LOCKED
        st.canon[p["target"]] = CanonLock(status=keep, hash=p["new_hash"], version=p["version"],
                                          ledger_seq=r.seq)
    elif a == "change.reject":
        st.changes[p["change"]] = Status.REJECTED
    elif a == "authorize":
        st.authorizations.append(Authorization(what=p["what"], scope=p.get("scope", "film"),
                                               by=r.actor, at=r.ts, ledger_seq=r.seq))
    elif a == "gate.amend":
        g = st.gates[p["gate"]]
        for ref, ch in p["changed"].items():
            g.approved_hashes[ref] = ch["new"]
        g.amendments += 1
    elif a == "canon.annotate":
        return  # notes are not part of the decision hash; the record is the audit trail
    elif a == "shot.stage":
        st.shots[p["shot"]] = p["stage"]
    else:
        raise IntegrityError(f"unknown ledger action '{a}' at record {r.seq}")
