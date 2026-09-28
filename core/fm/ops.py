"""High-level operations. The CLI is a thin wrapper around these.

Rule of thumb enforced here:
  * agents/system may: init, write PROPOSED content, stamp, submit, advance
    (when gates allow), propose changes, record derived products
  * only a human may: decide gates, approve/lock/reject canon, decide change
    requests, authorize final renders
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .authority import Actor, assert_human, current_actor, require_human
from .deps import build_graph, group_by_layer
from .errors import FMError, IntegrityError, StateError, ValidationFailed
from .io import (
    dump_yaml, hash_file_bytes, hash_obj, load_yaml, now_iso, read_front_matter, short,
    write_front_matter, write_json, write_yaml,
)
from .ledger import Ledger
from .phases import (
    CONTRACTS, GATE_FOR_PHASE, GATES, PROJECT_DIRS, gates_before, next_phase,
)
from .project import Loaded, Project, canon_hash
from .report import render_changelog, render_status
from .schemas import (
    BRIEF_FIELDS, CHANGEABLE_FIELDS, DERIVED_KINDS, DOMAINS, RATIONALE_REQUIRED_DOMAINS,
    CanonEntry, CanonFile, ChangeRequest, DepRef, DerivedRecord, HistoryItem, ProjectState,
    Status, Tag,
)
from .statemachine import replay
from .validate import gate_health, validate


# ================================================================ plumbing
def _append(project: Project, actor: Actor, action: str, target: str, payload: dict) -> ProjectState:
    Ledger(project.ledger_path).append(str(actor), action, target, payload)
    return refresh(project)


def refresh(project: Project) -> ProjectState:
    """Replay the ledger and rewrite the state cache + STATUS.md + CHANGELOG.md."""
    state = replay(Ledger(project.ledger_path).records())
    write_yaml(project.state_path, state.model_dump(mode="json"))
    loaded = project.load()
    graph = build_graph(loaded)
    project.status_path.write_text(render_status(project, state, loaded, graph), encoding="utf-8",
                                   newline="\n")
    (project.dir / "CHANGELOG.md").write_text(render_changelog(loaded), encoding="utf-8", newline="\n")
    return state


def load_state(project: Project) -> ProjectState:
    ledger = Ledger(project.ledger_path)
    problems = ledger.verify()
    if problems:
        raise IntegrityError("ledger integrity check failed: " + "; ".join(problems))
    return replay(ledger.records())


def _entry_dump(e: CanonEntry) -> dict:
    """Readable YAML: omit None and empty lists (defaults restore them on load)."""
    return {k: v for k, v in e.model_dump(mode="json", exclude_none=True).items() if v != []}


def _write_canon_entry(project: Project, loaded: Loaded, entry: CanonEntry) -> None:
    item = loaded.canon[entry.id]
    cf = CanonFile.model_validate(load_yaml(item.path) or {})
    cf.entries = [entry if e.id == entry.id else e for e in cf.entries]
    write_yaml(item.path, {"domain": cf.domain, "entries": [_entry_dump(e) for e in cf.entries]})


def _set_artifact_status(item, status: Status) -> None:
    if item.fmt == "md":
        meta, body = read_front_matter(item.path)
        meta["fm"]["status"] = status.value
        write_front_matter(item.path, meta, body)
    else:
        data = load_yaml(item.path)
        data["fm"]["status"] = status.value
        write_yaml(item.path, data)


def _set_shot_status(item, status: Status) -> None:
    data = load_yaml(item.path)
    data["status"] = status.value
    write_yaml(item.path, data)


def _rationale_problems(entries: list[CanonEntry]) -> list[str]:
    return [f"{e.id}: DECISION in '{e.domain}' has no rationale"
            for e in entries
            if e.domain in RATIONALE_REQUIRED_DOMAINS and e.tag == Tag.DECISION and not e.rationale]


# ================================================================ init
def init_project(repo: Path, slug: str, title: str, *, sandbox: bool = False) -> Project:
    project = Project(repo, slug)
    if project.dir.exists() and any(project.dir.iterdir()):
        raise StateError(f"projects/{slug} already exists; refusing to overwrite")
    for d in PROJECT_DIRS:
        (project.dir / d).mkdir(parents=True, exist_ok=True)
    tpl = repo / "templates" / "project"
    if tpl.exists():
        for src in tpl.rglob("*"):
            if src.is_file():
                dst = project.dir / src.relative_to(tpl)
                dst.parent.mkdir(parents=True, exist_ok=True)
                text = src.read_text(encoding="utf-8").replace("{{title}}", title).replace("{{slug}}", slug)
                dst.write_text(text, encoding="utf-8", newline="\n")
    for domain in DOMAINS:
        write_yaml(project.canon_dir / f"{domain}.yaml", {"domain": domain, "entries": []})
    brief = {
        "fm": {"id": "brief", "kind": "brief", "phase": "BRIEF", "status": "PROPOSED",
               "owner_role": "executive-producer",
               "summary": "The user's creative brief. status: given | assumed | unknown."},
        "fields": {f: {"value": None, "status": "unknown"} for f in BRIEF_FIELDS},
    }
    brief["fields"]["title"] = {"value": title, "status": "given"}
    write_yaml(project.dir / "00_brief" / "brief.yaml", brief)
    for d in PROJECT_DIRS:  # keep empty dirs in git
        p = project.dir / d
        if p.is_dir() and not any(p.iterdir()) and not d.startswith(".fm"):
            (p / ".gitkeep").write_text("", encoding="utf-8")
    actor = current_actor()
    Ledger(project.ledger_path).append(str(actor), "project.init", slug,
                                       {"project": slug, "title": title, "sandbox": sandbox})
    refresh(project)
    return project


# ================================================================ phases
def _contract_problems(project: Project, phase: str, loaded: Loaded) -> list[str]:
    c = CONTRACTS.get(phase)
    if not c:
        return []
    out = []
    by_path = {project.rel(a.path): a for a in loaded.artifacts.values()}
    for rel in c.required:
        if not (project.dir / rel).exists():
            out.append(f"missing {rel}")
        elif rel not in by_path:
            out.append(f"{rel} has no valid `fm:` metadata block")
    if c.min_shots and len(loaded.shots) < c.min_shots:
        out.append(f"needs at least {c.min_shots} shot spec(s) in 08_shots/")
    return out


def submit(project: Project) -> ProjectState:
    state = load_state(project)
    gate = GATE_FOR_PHASE.get(state.phase)
    if gate is None:
        raise StateError(f"{state.phase} has no approval gate; use `fm advance`")
    if state.phase_status == "awaiting_approval":
        raise StateError(f"{state.phase} is already awaiting approval ({gate.id})")
    report = validate(project)
    problems = _contract_problems(project, state.phase, report.loaded)
    for g in gates_before(state.phase):
        problems += [f"{g.id}: {i}" for i in gate_health(g.id, state, report.loaded, report.graph)]
    problems += [str(f) for f in report.errors]
    if problems:
        raise ValidationFailed("cannot submit for review:\n  " + "\n  ".join(problems))
    return _append(project, current_actor(), "phase.submit", state.phase,
                   {"phase": state.phase, "gate": gate.id})


def advance(project: Project) -> ProjectState:
    state = load_state(project)
    nxt = next_phase(state.phase)
    if nxt is None:
        raise StateError("project is COMPLETE")
    if state.phase_status == "awaiting_approval":
        raise StateError(f"{state.phase} is awaiting human approval; it cannot advance yet")
    gate = GATE_FOR_PHASE.get(state.phase)
    if gate and state.gates[gate.id].status != "approved":
        raise StateError(f"{gate.id} ({gate.name}) must be approved by a human before leaving "
                         f"{state.phase}. Submit with `fm submit`.")
    report = validate(project)
    problems = _contract_problems(project, state.phase, report.loaded)
    for g in [*gates_before(state.phase), *([gate] if gate else [])]:
        problems += [f"{g.id}: {i}" for i in gate_health(g.id, state, report.loaded, report.graph)]
    problems += [str(f) for f in report.errors]
    if nxt == "FINAL_RENDER" and not any(a.what == "final-render" for a in state.authorizations):
        problems.append("final render needs a human authorization: `fm authorize final-render`")
    if problems:
        raise StateError(f"cannot advance {state.phase} -> {nxt}:\n  " + "\n  ".join(problems))
    return _append(project, current_actor(), "phase.advance", nxt, {"from": state.phase, "to": nxt})


# ================================================================ gates (human)
def decide_gate(project: Project, gate_id: str, decision: str, notes: str | None = None, *,
                sandbox_confirm: bool = False) -> ProjectState:
    if gate_id not in GATES:
        raise FMError(f"unknown gate '{gate_id}' ({', '.join(GATES)})")
    if decision not in ("approved", "revise", "rejected"):
        raise FMError("decision must be approved | revise | rejected")
    assert_human(f"{decision} {gate_id}")
    gate = GATES[gate_id]
    state = load_state(project)
    rec = state.gates[gate_id]
    report = validate(project)
    loaded, graph = report.loaded, report.graph
    drifted = gate_health(gate_id, state, loaded, graph)
    reapproval = rec.status == "approved" and bool(drifted)
    in_review = state.phase == gate.closes_phase and state.phase_status == "awaiting_approval"
    if not (in_review or (reapproval and decision == "approved")):
        raise StateError(f"{gate_id} is not awaiting a decision (phase {state.phase}, "
                         f"{state.phase_status}; gate {rec.status})")
    if decision != "approved":
        if not notes:
            raise FMError(f"a '{decision}' decision needs --notes explaining what to change")
        confirm = require_human(f"{decision.upper()} {gate_id} ({gate.name})", gate_id,
                                sandbox=state.sandbox, sandbox_confirm=sandbox_confirm)
        return _append(project, current_actor(), "gate.decide", gate_id,
                       {"gate": gate_id, "decision": decision, "notes": notes,
                        "phase": gate.closes_phase, **confirm})

    # ---- approval preconditions
    problems = [str(f) for f in report.errors]
    for g in gates_before(gate.closes_phase):
        problems += [f"{g.id}: {i}" for i in gate_health(g.id, state, loaded, graph)]
        if state.gates[g.id].status != "approved":
            problems.append(f"{g.id} must be approved first")
    covered_art = {a.ref: a for a in loaded.artifacts.values() if a.meta.phase in gate.covers_phases}
    for ph in gate.covers_phases:
        problems += _contract_problems(project, ph, loaded)
    covered_shots = {s.ref: s for s in loaded.shots.values()} if gate.covers_shots else {}
    for s in covered_shots.values():
        sp = s.spec
        if not sp.creative_intent.narrative_purpose:
            problems.append(f"{sp.shot_id}: creative_intent.narrative_purpose required for approval")
        if sp.camera and sp.camera.lens_mm and not sp.rationale.camera:
            problems.append(f"{sp.shot_id}: rationale.camera required for approval")
    to_lock = [it.entry for it in loaded.canon.values()
               if it.entry.domain in gate.locks_domains
               and (state.canon.get(it.entry.id) is None
                    or state.canon[it.entry.id].status in (Status.APPROVED, Status.LOCKED))]
    problems += _rationale_problems(to_lock)
    stale = graph.stale()
    problems += [f"{r} is stale ({stale[r][0]})" for r in [*covered_art, *covered_shots] if r in stale]
    if problems:
        raise ValidationFailed(f"cannot approve {gate_id}:\n  " + "\n  ".join(problems))

    summary = (f"APPROVE {gate_id} - {gate.name}\n"
               f"  artifacts approved: {len(covered_art)}   shots approved: {len(covered_shots)}\n"
               f"  canon entries locked: {len(to_lock)} (domains: {', '.join(gate.locks_domains) or '-'})"
               + ("\n  (re-approval after drift)" if reapproval else ""))
    confirm = require_human(summary, gate_id, sandbox=state.sandbox, sandbox_confirm=sandbox_confirm)
    approved_hashes = {r: a.hash for r, a in covered_art.items()}
    approved_hashes |= {r: s.hash for r, s in covered_shots.items()}
    locked = {e.id: {"hash": canon_hash(e), "version": e.version} for e in to_lock}
    state = _append(project, current_actor(), "gate.decide", gate_id,
                    {"gate": gate_id, "decision": "approved", "notes": notes,
                     "phase": gate.closes_phase if in_review else None,
                     "approved_hashes": approved_hashes, "locked": locked, **confirm})
    # mirror statuses into files (content hashes are unaffected)
    for a in covered_art.values():
        _set_artifact_status(a, Status.APPROVED)
    for s in covered_shots.values():
        _set_shot_status(s, Status.APPROVED)
    for e in to_lock:
        _write_canon_entry(project, loaded, e.model_copy(update={"status": Status.LOCKED}))
    return refresh(project)


# ================================================================ canon (human)
def canon_decide(project: Project, cid: str, action: str, *, sandbox_confirm: bool = False
                 ) -> ProjectState:
    assert_human(f"canon {action} {cid}")
    state = load_state(project)
    loaded = project.load()
    if cid not in loaded.canon:
        raise FMError(f"unknown canon id '{cid}'")
    e = loaded.canon[cid].entry
    cur = state.canon.get(cid)
    cur_status = cur.status if cur else Status.PROPOSED
    if loaded.canon[cid].hash != (cur.hash if cur else loaded.canon[cid].hash):
        raise IntegrityError(f"{cid} differs from its recorded version; resolve with a change request")
    allowed = {
        "approve": {Status.PROPOSED},
        "lock": {Status.PROPOSED, Status.APPROVED},
        "reject": {Status.PROPOSED},
    }[action]
    if cur_status not in allowed:
        raise StateError(f"cannot {action} {cid}: it is {cur_status.value}"
                         + (" (use `fm change propose` to alter it)" if cur_status == Status.LOCKED else ""))
    if action in ("approve", "lock"):
        probs = _rationale_problems([e])
        if probs:
            raise ValidationFailed("; ".join(probs))
    confirm = require_human(f"{action.upper()} canon {cid}\n  {e.statement}", cid,
                            sandbox=state.sandbox, sandbox_confirm=sandbox_confirm)
    new_status = {"approve": Status.APPROVED, "lock": Status.LOCKED, "reject": Status.REJECTED}[action]
    state = _append(project, current_actor(), f"canon.{action}", cid,
                    {"id": cid, "hash": loaded.canon[cid].hash, "version": e.version, **confirm})
    _write_canon_entry(project, loaded, e.model_copy(update={"status": new_status}))
    return refresh(project)


# ================================================================ change requests
def _next_change_id(loaded: Loaded) -> str:
    nums = [int(c.split("-")[1]) for c in loaded.changes] or [0]
    return f"CHANGE-{max(nums) + 1:03d}"


def impact_of(loaded: Loaded, refs: list[str]) -> dict[str, list[str]]:
    graph = build_graph(loaded)
    return {layer.value: items for layer, items in graph.impact(refs).items()}


def propose_change(project: Project, cid: str, updates: dict[str, Any], reason: str) -> ChangeRequest:
    state = load_state(project)
    loaded = project.load()
    if cid not in loaded.canon:
        raise FMError(f"unknown canon id '{cid}'")
    lock = state.canon.get(cid)
    if lock is None or lock.status not in (Status.APPROVED, Status.LOCKED):
        raise StateError(f"{cid} is not approved/locked; PROPOSED entries are edited directly")
    bad = set(updates) - set(CHANGEABLE_FIELDS)
    if bad:
        raise FMError(f"cannot change fields {sorted(bad)} (allowed: {', '.join(CHANGEABLE_FIELDS)})")
    current = loaded.canon[cid].entry
    if loaded.canon[cid].hash != lock.hash:
        raise IntegrityError(f"{cid} was edited in place; revert the file before proposing a change")
    candidate = CanonEntry.model_validate({**current.model_dump(mode="json"), **updates})
    if canon_hash(candidate) == lock.hash:
        raise FMError("the proposed change is identical to the current decision")
    probs = _rationale_problems([candidate])
    if probs:
        raise ValidationFailed("; ".join(probs))
    cr = ChangeRequest(
        id=_next_change_id(loaded), target=cid, reason=reason, set=updates,
        base_version=lock.version, base_hash=lock.hash, proposed_by=str(current_actor()),
        proposed_at=now_iso(), impact=impact_of(loaded, [f"canon:{cid}"]),
    )
    write_yaml(project.changes_dir / f"{cr.id}.yaml", cr.model_dump(mode="json", exclude_none=True))
    _append(project, current_actor(), "change.propose", cr.id, {"change": cr.id, "target": cid})
    return cr


def decide_change(project: Project, change_id: str, decision: str, notes: str | None = None, *,
                  sandbox_confirm: bool = False) -> ChangeRequest:
    assert_human(f"change {decision} {change_id}")
    state = load_state(project)
    loaded = project.load()
    if change_id not in loaded.changes:
        raise FMError(f"unknown change '{change_id}'")
    cr, path = loaded.changes[change_id]
    if state.changes.get(change_id) != Status.PROPOSED:
        raise StateError(f"{change_id} is not awaiting a decision")
    lock = state.canon.get(cr.target)
    if lock is None or lock.hash != cr.base_hash:
        raise StateError(f"{cr.target} changed since {change_id} was proposed; propose again")
    item = loaded.canon[cr.target]
    before = item.entry
    impact = impact_of(loaded, [f"canon:{cr.target}"])
    lines = [f"{decision.upper()} {change_id}: {cr.target} v{before.version}",
             f"  reason: {cr.reason}"]
    for k, v in cr.set.items():
        lines.append(f"  {k}: {getattr(before, k)!r}  ->  {v!r}")
    lines.append("  impact: " + ", ".join(f"{k} {len(v)}" for k, v in impact.items()) if impact
                 else "  impact: none")
    confirm = require_human("\n".join(lines), change_id, sandbox=state.sandbox,
                            sandbox_confirm=sandbox_confirm)
    actor = current_actor()
    if decision == "rejected":
        _append(project, actor, "change.reject", change_id, {"change": change_id, **confirm})
        cr = cr.model_copy(update={"status": Status.REJECTED, "decided_by": str(actor),
                                   "decided_at": now_iso(), "decision_notes": notes})
    elif decision == "approved":
        hist = HistoryItem(version=before.version, hash=item.hash, status=Status.SUPERSEDED,
                           change=change_id, at=now_iso(), statement=before.statement,
                           value=before.value, rationale=before.rationale)
        after = CanonEntry.model_validate({**before.model_dump(mode="json"), **cr.set})
        after = after.model_copy(update={"version": before.version + 1,
                                         "history": [*before.history, hist],
                                         "status": lock.status})
        new_hash = canon_hash(after)
        _append(project, actor, "change.approve", change_id,
                {"change": change_id, "target": cr.target, "old_hash": item.hash,
                 "new_hash": new_hash, "version": after.version, **confirm})
        _write_canon_entry(project, loaded, after)
        cr = cr.model_copy(update={"status": Status.APPROVED, "decided_by": str(actor),
                                   "decided_at": now_iso(), "decision_notes": notes,
                                   "new_hash": new_hash, "impact": impact})
    else:
        raise FMError("decision must be approved | rejected")
    write_yaml(path, cr.model_dump(mode="json", exclude_none=True))
    refresh(project)
    return cr


# ================================================================ authorization (human)
AUTHORIZABLE = ("final-render",)


def authorize(project: Project, what: str, scope: str = "film", *, sandbox_confirm: bool = False
              ) -> ProjectState:
    assert_human(f"authorize {what}")
    if what not in AUTHORIZABLE:
        raise FMError(f"can only authorize: {', '.join(AUTHORIZABLE)}")
    state = load_state(project)
    confirm = require_human(f"AUTHORIZE {what} for scope '{scope}'", what,
                            sandbox=state.sandbox, sandbox_confirm=sandbox_confirm)
    return _append(project, current_actor(), "authorize", what, {"what": what, "scope": scope, **confirm})


# ================================================================ stamping
def stamp(project: Project, target: str, note: str | None = None, *, _refresh: bool = True
          ) -> dict[str, str]:
    """Record current upstream hashes into an artifact or shot's derived_from.

    Refuses to refresh changed upstream hashes on a node whose own content has
    not changed since its last stamp (that would hide staleness) unless a note
    explains why the content legitimately needs no revision.
    """
    loaded = project.load()
    item = None
    for coll in (loaded.artifacts.values(), loaded.shots.values()):
        for it in coll:
            if target in (it.ref, project.rel(it.path), str(it.path)) or it.path == Path(target).resolve():
                item = it
    if item is None:
        raise FMError(f"'{target}' is not a managed artifact or shot")
    is_shot = item.ref.startswith("shot:")
    deps = list(item.spec.derived_from if is_shot else item.meta.derived_from)
    if is_shot:  # record implicit dependencies (characters, intents, scoped canon) with hashes
        from .deps import implicit_shot_deps
        known = {d.ref for d in deps}
        deps += [DepRef(ref=r) for r in implicit_shot_deps(loaded, item.spec) if r not in known]
    prev_stamp = item.spec.stamped_content_hash if is_shot else item.meta.stamped_content_hash
    new_deps, refreshed = [], {}
    for d in deps:
        cur = loaded.current_hash(d.ref)
        if cur is None:
            raise FMError(f"{d.ref} does not exist")
        if d.hash is not None and d.hash != cur:
            refreshed[d.ref] = f"{short(d.hash)} -> {short(cur)}"
        new_deps.append(DepRef(ref=d.ref, hash=cur).model_dump(mode="json"))
    if refreshed and prev_stamp == item.hash and not note:
        raise StateError(
            f"{item.ref} content is unchanged since its last stamp but upstream changed "
            f"({', '.join(refreshed)}). Revise it first, or pass --note explaining why no revision is needed.")
    if is_shot:
        data = load_yaml(item.path)
        data["derived_from"] = new_deps
        data["stamped_content_hash"] = item.hash
        if note:
            data["stamp_note"] = note
        write_yaml(item.path, data)
    elif item.fmt == "md":
        meta, body = read_front_matter(item.path)
        meta["fm"]["derived_from"] = new_deps
        meta["fm"]["stamped_content_hash"] = item.hash
        if note:
            meta["fm"]["stamp_note"] = note
        write_front_matter(item.path, meta, body)
    else:
        data = load_yaml(item.path)
        data["fm"]["derived_from"] = new_deps
        data["fm"]["stamped_content_hash"] = item.hash
        if note:
            data["fm"]["stamp_note"] = note
        write_yaml(item.path, data)
    if _refresh:
        refresh(project)
    return refreshed


# ================================================================ derived products
def record_derived(project: Project, ref: str, from_refs: list[str], *, file: Path | None = None,
                   content: str | None = None, producer: str | None = None,
                   note: str | None = None) -> DerivedRecord:
    kind, _, ident = ref.partition(":")
    if kind not in DERIVED_KINDS:
        raise FMError(f"derived refs must be one of {DERIVED_KINDS}: got '{ref}'")
    loaded = project.load()
    deps = []
    for r in from_refs:
        h = loaded.current_hash(r)
        if h is None:
            raise FMError(f"upstream '{r}' does not exist")
        deps.append(DepRef(ref=r, hash=h))
    if file is not None:
        ch = hash_file_bytes(file)
    elif content is not None:
        ch = hash_obj(content)
    else:
        ch = hash_obj([d.model_dump(mode="json") for d in deps])
    rec = DerivedRecord(ref=ref, derived_from=deps, content_hash=ch,
                        path=project.rel(file) if file else None, created_at=now_iso(),
                        producer=producer or str(current_actor()), notes=note)
    write_json(project.derived_dir / kind / f"{ident}.json", rec.model_dump(mode="json"))
    refresh(project)
    return rec


def plan(project: Project, scope: str) -> dict[str, Any]:
    from .scopes import resolve_scope
    loaded = project.load()
    graph = build_graph(loaded)
    ss = resolve_scope(scope, loaded, graph)
    stale = graph.stale()
    todo = sorted(r for r in ss.closure if r in stale)
    return {"scope": scope, "roots": sorted(ss.roots), "in_scope": len(ss.closure),
            "shots": ss.shots, "stale": todo,
            "by_layer": {k.value: v for k, v in group_by_layer(todo).items()}}
