"""Append-only, hash-chained approval ledger.

Every authoritative action (gate decisions, canon approvals/locks, change
decisions, authorizations, phase moves) is one JSON line. Each record
contains the hash of the previous one, so edits, deletions and reordering
are detected by `verify()`. Project state is a pure replay of this file.

This detects tampering; it cannot stop a determined local process from
rewriting the whole file. It exists so that nothing changes *silently*.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .io import canonical_json, now_iso, sha256_text
from .schemas import LedgerRecord

GENESIS = "sha256:" + "0" * 64


def _record_hash(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "hash"}
    return sha256_text(canonical_json(body))


class Ledger:
    def __init__(self, path: Path):
        self.path = path

    def records(self) -> list[LedgerRecord]:
        if not self.path.exists():
            return []
        out = []
        with open(self.path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(LedgerRecord.model_validate(json.loads(line)))
                except Exception as exc:  # noqa: BLE001
                    raise IntegrityError(f"ledger line {n} is unreadable: {exc}") from exc
        return out

    def verify(self) -> list[str]:
        problems: list[str] = []
        prev = GENESIS
        try:
            recs = self.records()
        except IntegrityError as exc:
            return [str(exc)]
        for i, r in enumerate(recs, 1):
            if r.seq != i:
                problems.append(f"ledger record {i}: sequence is {r.seq}, expected {i}")
            if r.prev != prev:
                problems.append(f"ledger record {r.seq}: chain broken (prev hash mismatch)")
            if _record_hash(r.model_dump(mode="json")) != r.hash:
                problems.append(f"ledger record {r.seq}: content altered (hash mismatch)")
            prev = r.hash
        return problems

    def head(self) -> tuple[int, str]:
        recs = self.records()
        return (recs[-1].seq, recs[-1].hash) if recs else (0, GENESIS)

    def append(self, actor: str, action: str, target: str, payload: dict[str, Any] | None = None
               ) -> LedgerRecord:
        problems = self.verify()
        if problems:
            raise IntegrityError("refusing to append to a damaged ledger: " + "; ".join(problems))
        seq, prev = self.head()
        rec = {
            "seq": seq + 1,
            "ts": now_iso(),
            "actor": actor,
            "action": action,
            "target": target,
            "payload": payload or {},
            "prev": prev,
        }
        rec["hash"] = _record_hash(rec)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(canonical_json(rec) + "\n")
        return LedgerRecord.model_validate(rec)
