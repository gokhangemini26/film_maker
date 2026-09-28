"""`fm validate`: every rule that keeps the project honest, in one place.

Levels: ERROR blocks submission and approval; WARN is shown; INFO is context.
Technical validity is never treated as creative approval: validation only
checks structure, integrity and traceability. Creative quality is judged by
humans at gates (and, from M2, by review agents whose findings are advisory).
"""
from __future__ import annotations

from dataclasses import dataclass

from .deps import Graph, build_graph
from .io import load_yaml, short
from .ledger import Ledger
from .phases import GATES, PHASES, gates_before, phase_index
from .project import Loaded, Project
from .schemas import (
    HUMAN_BACKED, RATIONALE_REQUIRED_DOMAINS, ProjectState, Status, Tag,
)
from .statemachine import replay


@dataclass
class Finding:
    level: str  # ERROR | WARN | INFO
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.level:5} {self.code:24} {self.where}: {self.message}"


@dataclass
class Report:
    findings: list[Finding]
    state: ProjectState | None
    loaded: Loaded
    graph: Graph | None

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "ERROR"]

    @property
    def ok(self) -> bool:
        return not self.errors


def effective_status(entry_status: Status, ref_id: str, state: ProjectState) -> Status:
    lk = state.canon.get(ref_id)
    return lk.status if lk else entry_status


def gate_health(gate_id: str, state: ProjectState, loaded: Loaded, graph: Graph) -> list[str]:
    """Problems with an APPROVED gate: approved content modified, removed, or stale."""
    g = state.gates[gate_id]
    if g.status != "approved":
        return []
    stale = graph.stale()
    issues = []
    for ref, h in sorted(g.approved_hashes.items()):
        cur = loaded.current_hash(ref)
        if cur is None:
            issues.append(f"{ref} was removed after approval")
        elif cur != h:
            issues.append(f"{ref} was modified after approval ({short(h)} -> {short(cur)})")
        elif ref in stale:
            issues.append(f"{ref} is stale: {stale[ref][0]}")
    return issues


def validate(project: Project) -> Report:  # noqa: C901 - a checklist by design
    F: list[Finding] = []
    add = lambda lvl, code, where, msg: F.append(Finding(lvl, code, where, msg))  # noqa: E731

    # ---- ledger + state integrity
    ledger = Ledger(project.ledger_path)
    for p in ledger.verify():
        add("ERROR", "LEDGER_INTEGRITY", ".fm/ledger.jsonl", p)
    state: ProjectState | None = None
    try:
        state = replay(ledger.records())
    except Exception as exc:  # noqa: BLE001
        add("ERROR", "LEDGER_REPLAY", ".fm/ledger.jsonl", str(exc))
    if state is not None:
        if not project.state_path.exists():
            add("WARN", "STATE_CACHE_MISSING", "state.yaml", "missing; `fm status` regenerates it")
        else:
            cached = load_yaml(project.state_path)
            if cached != state.model_dump(mode="json"):
                add("ERROR", "STATE_TAMPERED", "state.yaml",
                    "does not match the ledger replay; state is only changed through fm commands "
                    "(run `fm status --repair-cache` after investigating)")

    loaded = project.load()
    for where, msg in loaded.errors:
        add("ERROR", "SCHEMA", where, msg)
    graph = build_graph(loaded)
    if state is None:
        return Report(F, None, loaded, graph)

    # ---- canon: lifecycle claims must be backed by the ledger
    for cid, item in loaded.canon.items():
        e, where = item.entry, project.rel(item.path)
        lock = state.canon.get(cid)
        if e.status in HUMAN_BACKED and lock is None:
            add("ERROR", "STATUS_NOT_BACKED", where,
                f"{cid} claims {e.status.value} but no human decision is recorded in the ledger")
        if lock is not None:
            if e.status != lock.status:
                add("ERROR", "STATUS_MISMATCH", where,
                    f"{cid} says {e.status.value}, ledger says {lock.status.value}")
            if item.hash != lock.hash:
                if lock.status == Status.LOCKED:
                    add("ERROR", "LOCKED_CANON_MODIFIED", where,
                        f"{cid} is LOCKED (v{lock.version}) but its content changed "
                        f"({short(lock.hash)} -> {short(item.hash)}). Revert it, or propose the change "
                        f"with `fm change propose {cid} ...` for human approval.")
                elif lock.status == Status.APPROVED:
                    add("ERROR", "APPROVED_CANON_MODIFIED", where,
                        f"{cid} was approved (v{lock.version}) and has since changed; "
                        "use a change request")
            if e.version != lock.version:
                add("ERROR", "VERSION_MISMATCH", where,
                    f"{cid} version {e.version} != ledger version {lock.version}")
        eff = effective_status(e.status, cid, state)
        if (e.domain in RATIONALE_REQUIRED_DOMAINS and e.tag == Tag.DECISION and not e.rationale):
            lvl = "ERROR" if eff in (Status.APPROVED, Status.LOCKED) else "WARN"
            add(lvl, "MISSING_RATIONALE", where, f"{cid}: decisions in '{e.domain}' must say why")
        for d in e.depends_on:
            if d not in loaded.canon:
                add("ERROR", "DANGLING_REF", where, f"{cid} depends_on unknown '{d}'")
        for s in e.serves:
            if s not in loaded.canon:
                add("ERROR", "DANGLING_REF", where, f"{cid} serves unknown intent '{s}'")
        if e.tag == Tag.UNKNOWN and eff == Status.LOCKED:
            add("WARN", "LOCKED_UNKNOWN", where, f"{cid} is locked but tagged UNKNOWN")
    for cid, lock in state.canon.items():
        if cid not in loaded.canon and lock.status in (Status.LOCKED, Status.APPROVED):
            add("ERROR", "LOCKED_CANON_REMOVED", "canon/",
                f"{cid} is {lock.status.value} in the ledger but missing from canon files")

    # ---- artifacts
    for aid, item in loaded.artifacts.items():
        where = project.rel(item.path)
        backed = state.artifacts.get(item.ref)
        if item.meta.status in HUMAN_BACKED and backed is None:
            add("ERROR", "STATUS_NOT_BACKED", where,
                f"artifact {aid} claims {item.meta.status.value} without a recorded gate approval")
        if item.meta.phase not in PHASES:
            add("ERROR", "SCHEMA", where, f"unknown phase '{item.meta.phase}'")
        for d in item.meta.derived_from:
            if not loaded.exists(d.ref):
                add("ERROR", "DANGLING_REF", where, f"derived_from unknown '{d.ref}'")
            elif d.hash is None:
                add("WARN", "UNSTAMPED", where, f"{d.ref} has no recorded hash; run `fm stamp {where}`")

    # ---- shots
    known_chars = {cid.split(".")[1] for cid in loaded.canon if cid.startswith("characters.")}
    for sid, item in loaded.shots.items():
        s, where = item.spec, project.rel(item.path)
        if s.status in HUMAN_BACKED and f"shot:{sid}" not in state.gates["G5"].approved_hashes:
            add("ERROR", "STATUS_NOT_BACKED", where, f"{sid} claims {s.status.value} without G5 approval")
        if s.camera and s.camera.lens_mm and not s.rationale.camera:
            add("WARN", "MISSING_RATIONALE", where, f"{sid}: lens chosen without rationale.camera")
        if not s.creative_intent.narrative_purpose:
            add("WARN", "MISSING_INTENT", where, f"{sid}: creative_intent.narrative_purpose is empty")
        for intent in s.serves:
            if intent not in loaded.canon:
                add("ERROR", "DANGLING_REF", where, f"serves unknown intent '{intent}'")
        for ch in s.characters:
            if ch.id not in known_chars:
                add("WARN", "UNKNOWN_CHARACTER", where, f"character '{ch.id}' has no canon entries")
        for d in s.derived_from:
            if not loaded.exists(d.ref):
                add("ERROR", "DANGLING_REF", where, f"derived_from unknown '{d.ref}'")

    # ---- change requests
    for cid, (cr, path) in loaded.changes.items():
        backed = state.changes.get(cid)
        if cr.status in HUMAN_BACKED and backed != cr.status:
            add("ERROR", "STATUS_NOT_BACKED", project.rel(path),
                f"{cid} claims {cr.status.value}, ledger says {backed.value if backed else 'nothing'}")

    # ---- graph
    for node, ref in graph.missing:
        if not any(f.code == "DANGLING_REF" and ref.split(":", 1)[-1] in f.message for f in F):
            add("ERROR", "DANGLING_REF", node, f"depends on missing '{ref}'")
    stale = graph.stale()
    for ref in sorted(stale):
        add("WARN", "STALE", ref, "; ".join(stale[ref][:2]))

    # ---- gates
    for gid in GATES:
        for issue in gate_health(gid, state, loaded, graph):
            add("WARN", "GATE_DRIFT", gid, issue + " — re-approval required before advancing")
    for g in gates_before(state.phase):
        if state.gates[g.id].status != "approved":
            add("ERROR", "GATE_BYPASSED", g.id,
                f"project is in {state.phase} but {g.id} ({g.name}) is not approved")
    if phase_index(state.phase) > phase_index("BRIEF") and loaded.brief is None:
        add("ERROR", "MISSING_BRIEF", "00_brief/brief.yaml", "brief is missing or unreadable")
    elif loaded.brief is not None:
        unknown = [k for k, v in loaded.brief.fields.items() if v.status == "unknown"]
        if unknown:
            add("INFO", "BRIEF_UNKNOWN", "00_brief/brief.yaml",
                f"{len(unknown)} brief fields still unknown: {', '.join(unknown[:6])}"
                + ("…" if len(unknown) > 6 else ""))
    return Report(F, state, loaded, graph)
