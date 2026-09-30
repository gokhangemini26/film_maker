"""Review feedback -> scoped regeneration (M5).

A finding from a human or agent review becomes a structured item under
`qa/feedback/FB-###.yaml`. `plan` reuses the existing impact/plan code
(`ops.impact_of`, `ops.plan`) to show the minimal stale set, the agent that
handles it and whether a change request is needed. `resolve` is NOT
human-only: it records the actor and refuses while the plan's nodes are stale.

Storage: plain files only. The ledger has no non-approval record action
(`fm record` writes derived-product JSON, not ledger lines), so feedback is
not hash-chained; each item carries its own append-only `history`. The files
have no `fm:` block, so the artifact loader ignores them and they never
enter the dependency graph.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .authority import current_actor
from .errors import FMError, StateError
from .io import hash_obj, load_yaml, now_iso, write_yaml
from .project import Project
from .roles import CANON_DOMAINS
from .schemas import Status

FEEDBACK_DIR = "qa/feedback"
SEVERITIES = ("low", "medium", "high", "blocker")
_ID_RE = re.compile(r"^FB-\d{3,}$")

# Ordered: first table row whose keyword appears (as a word stem) in the note wins.
ROUTING: list[tuple[str, tuple[str, ...]]] = [
    ("cinematographer", ("camera", "framing", "frame", "lens", "composition", "headroom", "angle", "crop")),
    ("animation-director", ("motion", "animation", "timing", "movement", "gesture")),
    ("look-director", ("colour", "color", "ui", "lighting", "light", "palette", "glow", "exposure", "contrast")),
    ("character-designer", ("figure", "character", "silhouette", "wardrobe", "face")),
    ("world-designer", ("world", "set", "car", "prop", "street", "location", "architecture")),
    ("blender-td", ("builder", "blender", "render", "proxy", "resolver")),
]
DOMAIN_OWNER = {d: role for role, doms in CANON_DOMAINS.items() for d in doms}
OWNER_COMMAND = {
    "cinematographer": "/film-storyboard", "animation-director": "/film-storyboard",
    "look-director": "/film-look", "character-designer": "/film-world", "world-designer": "/film-world",
    "blender-td": "/film-blender", "story-architect": "/film-story", "screenwriter": "/film-script",
    "creative-director": "/film-direction", "executive-producer": "/film-revise",
}
_SCOPE_KINDS = ("shot", "shots", "scene", "sequence", "character", "asset", "ref")


def route_owner(target: str, note: str) -> tuple[str, str]:
    """(owner, why). Note keywords first, then the target's canon domain, then shot -> cinematographer."""
    words = set(re.findall(r"[a-z]+", note.lower()))
    for role, kws in ROUTING:
        hit = next((k for k in kws if k in words), None)
        if hit:
            return role, f"note keyword '{hit}'"
    kind, _, ident = target.partition(":")
    if kind == "canon" and ident.split(".")[0] in DOMAIN_OWNER:
        return DOMAIN_OWNER[ident.split(".")[0]], f"canon domain '{ident.split('.')[0]}'"
    if kind in ("shot", "shots", "scene", "sequence"):
        return "cinematographer", "shot-level default"
    return "executive-producer", "no routing match: triage"


def scope_for(target: str) -> str:
    """Map a feedback target to an `fm plan` scope."""
    kind, _, _ = target.partition(":")
    if kind in _SCOPE_KINDS:
        return target
    if kind in ("canon", "artifact", "resolved", "blend", "render", "qa"):
        return f"ref:{target}"
    raise FMError(f"unsupported feedback target '{target}' (shot:ID, canon:ID, artifact:ID, scene:, ...)")


# ------------------------------------------------------------------ storage
def _dir(project: Project) -> Path:
    return project.dir / FEEDBACK_DIR


def _path(project: Project, fid: str) -> Path:
    if not _ID_RE.match(fid):
        raise FMError(f"invalid feedback id '{fid}' (expected FB-001)")
    return _dir(project) / f"{fid}.yaml"


def load_item(project: Project, fid: str) -> dict[str, Any]:
    p = _path(project, fid)
    if not p.exists():
        raise FMError(f"unknown feedback '{fid}'")
    data = load_yaml(p)
    if not isinstance(data, dict) or "feedback" not in data:
        raise FMError(f"{p}: not a feedback file")
    return data["feedback"]


def _save(project: Project, item: dict[str, Any]) -> None:
    write_yaml(_path(project, item["id"]), {"feedback": item})


def list_items(project: Project, *, open_only: bool = False) -> list[dict[str, Any]]:
    d = _dir(project)
    out = []
    for p in sorted(d.glob("FB-*.yaml")) if d.exists() else []:
        data = load_yaml(p)
        if isinstance(data, dict) and "feedback" in data:
            it = data["feedback"]
            if not open_only or it.get("status") == "OPEN":
                out.append(it)
    return out


def _next_id(project: Project) -> str:
    nums = [int(i["id"][3:]) for i in list_items(project)]
    return f"FB-{(max(nums) + 1 if nums else 1):03d}"


# ------------------------------------------------------------------ operations
def add(project: Project, target: str, note: str, *, severity: str = "medium",
        owner: str | None = None) -> dict[str, Any]:
    from .ops import plan as run_plan
    if severity not in SEVERITIES:
        raise FMError(f"severity must be one of {', '.join(SEVERITIES)}")
    if not note.strip():
        raise FMError("--note must not be empty")
    scope = scope_for(target)
    run_plan(project, scope)  # validates the target/scope (raises on unknown)
    loaded = project.load()
    if owner:
        why = "given with --owner"
    else:
        owner, why = route_owner(target, note)
    actor = str(current_actor())
    item = {
        "id": _next_id(project), "status": "OPEN", "target": target, "note": note.strip(),
        "severity": severity, "suggested_owner": owner, "owner_reason": why,
        "created_at": now_iso(), "created_by": actor,
        "target_hash": loaded.current_hash(target) if ":" in target and target.split(":")[0]
        in ("canon", "artifact", "shot", "resolved", "blend", "render", "qa") else None,
        "history": [{"at": now_iso(), "actor": actor, "event": "opened"}],
    }
    _save(project, item)
    return item


def plan_for(project: Project, fid: str) -> dict[str, Any]:
    """Reuse ops.plan / ops.impact_of; add owner, command and change-request verdict."""
    from .ops import impact_of, load_state, plan as run_plan
    item = load_item(project, fid)
    target = item["target"]
    res = run_plan(project, scope_for(target))
    loaded = project.load()
    state = load_state(project)
    kind, _, ident = target.partition(":")
    cr, cr_why = False, "target is unapproved work: its owner revises it directly"
    if kind == "canon":
        lock = state.canon.get(ident)
        if lock is not None and lock.status in (Status.APPROVED, Status.LOCKED):
            cr, cr_why = True, f"{target} is {lock.status.value}: `fm change propose {ident} --set ... --reason ...`"
    elif kind == "shot" and ident in loaded.shots and loaded.shots[ident].spec.status in (
            Status.APPROVED, Status.LOCKED):
        cr_why = ("shot is APPROVED: revise it, then the human re-approves the covering gate "
                  "(no canon change request unless the cause is a locked canon entry)")
    owner = item["suggested_owner"]
    return {"id": fid, "target": target, "scope": res["scope"], "owner": owner,
            "command": OWNER_COMMAND.get(owner, "/film-revise"), "change_request_needed": cr,
            "change_request_note": cr_why, "stale": res["stale"], "by_layer": res["by_layer"],
            "shots": res["shots"],
            "impact": impact_of(loaded, [target]) if loaded.exists(target) else {}}


def resolve(project: Project, fid: str, by: str, *, force_stale: bool = False) -> dict[str, Any]:
    item = load_item(project, fid)
    if item["status"] != "OPEN":
        raise StateError(f"{fid} is already {item['status']}")
    if not by.strip():
        raise FMError("--by must not be empty")
    pl = plan_for(project, fid)
    if pl["stale"] and not force_stale:
        raise StateError(f"{fid}: {len(pl['stale'])} node(s) in scope are still stale "
                         f"({', '.join(pl['stale'][:6])}{' ...' if len(pl['stale']) > 6 else ''}). "
                         "Regenerate them (`fm feedback plan`), or pass --force-stale to accept the risk.")
    loaded = project.load()
    now_hash = loaded.current_hash(item["target"])
    actor = str(current_actor())
    changed = None if item.get("target_hash") is None else (now_hash != item["target_hash"])
    item["status"] = "RESOLVED"
    item["resolution"] = {"by": by.strip(), "actor": actor, "at": now_iso(),
                          "forced_stale": bool(pl["stale"] and force_stale),
                          "stale_at_resolve": pl["stale"], "target_hash": now_hash,
                          "target_changed": changed}
    item["history"].append({"at": now_iso(), "actor": actor, "event": "resolved",
                            "forced_stale": bool(pl["stale"] and force_stale)})
    item["content_hash"] = hash_obj({k: v for k, v in item.items() if k != "content_hash"})
    _save(project, item)
    return item
