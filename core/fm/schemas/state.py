"""Project state, ledger events, change requests, derived-product records."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .common import DepRef, Status, StrictModel

GateStatus = Literal["pending", "awaiting_approval", "approved", "revise", "rejected"]
PhaseStatus = Literal["in_progress", "awaiting_approval"]
ShotStage = Literal["spec", "resolved", "built", "previewed", "qa_pass", "approved", "final"]


class GateRecord(StrictModel):
    status: GateStatus = "pending"
    decided_by: str | None = None
    decided_at: str | None = None
    notes: str | None = None
    # ref -> content hash of everything the human approved at this gate
    approved_hashes: dict[str, str] = Field(default_factory=dict)
    ledger_seq: int | None = None
    # advisory QA verdict shown at approval and whether the human acknowledged it (carried forward)
    review_verdict: str | None = None
    review_acknowledged: bool = False
    amendments: int = 0


class CanonLock(StrictModel):
    status: Status
    hash: str
    version: int
    ledger_seq: int


class Authorization(StrictModel):
    what: str
    scope: str
    by: str
    at: str
    ledger_seq: int


class ProjectState(StrictModel):
    """Projection of the ledger. `state.yaml` is a cache of this; the
    append-only ledger is authoritative and `fm validate` re-derives it."""

    schema_version: int = 1
    project: str
    title: str
    sandbox: bool = False
    created_at: str
    phase: str
    phase_status: PhaseStatus = "in_progress"
    gates: dict[str, GateRecord] = Field(default_factory=dict)
    canon: dict[str, CanonLock] = Field(default_factory=dict)
    artifacts: dict[str, Status] = Field(default_factory=dict)  # ref -> human-backed status
    shots: dict[str, ShotStage] = Field(default_factory=dict)
    authorizations: list[Authorization] = Field(default_factory=list)
    changes: dict[str, Status] = Field(default_factory=dict)
    ledger_seq: int = 0
    ledger_head: str = ""


class LedgerRecord(StrictModel):
    seq: int
    ts: str
    actor: str
    action: str
    target: str
    payload: dict[str, Any] = Field(default_factory=dict)
    prev: str
    hash: str


class ChangeRequest(StrictModel):
    """A proposal to alter an APPROVED/LOCKED canon entry."""

    id: str
    status: Status = Status.PROPOSED
    target: str = Field(description="canon id")
    reason: str = Field(min_length=5)
    set: dict[str, Any] = Field(description="fields of the canon entry to replace")
    base_version: int
    base_hash: str
    proposed_by: str
    proposed_at: str
    impact: dict[str, list[str]] = Field(default_factory=dict)
    decided_by: str | None = None
    decided_at: str | None = None
    decision_notes: str | None = None
    new_hash: str | None = None


class DerivedRecord(StrictModel):
    """A downstream production product (resolved spec, .blend, render, QA
    report). Written by builders; not authoritative for creative decisions."""

    ref: str
    derived_from: list[DepRef]
    content_hash: str
    path: str | None = None
    created_at: str
    producer: str
    notes: str | None = None
