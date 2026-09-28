"""Creative-intent coverage (`fm intent`).

For every intent: which canon decisions, documents and shots serve it.
An intent nothing serves is a creative gap; a decision that serves no
intent is an implementation without a stated purpose.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .project import Loaded
from .schemas import Tag

# Domains whose DECISIONs are expected to name the intent they serve.
SERVING_DOMAINS = ("story", "world", "characters", "look", "camera", "animation", "audio", "tone")


@dataclass
class IntentCoverage:
    intent: str
    statement: str
    canon: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    shots: list[str] = field(default_factory=list)


def intent_coverage(loaded: Loaded) -> list[IntentCoverage]:
    rows = {cid: IntentCoverage(cid, it.entry.statement)
            for cid, it in sorted(loaded.canon.items()) if cid.startswith("intent.")}
    for cid, it in sorted(loaded.canon.items()):
        for s in it.entry.serves:
            if s in rows:
                rows[s].canon.append(cid)
    for aid, a in sorted(loaded.artifacts.items()):
        for s in a.meta.serves:
            if s in rows:
                rows[s].artifacts.append(aid)
    for sid, sh in sorted(loaded.shots.items()):
        for s in sh.spec.serves:
            if s in rows:
                rows[s].shots.append(sid)
    return list(rows.values())


def unserved_decisions(loaded: Loaded) -> list[str]:
    return sorted(cid for cid, it in loaded.canon.items()
                  if it.entry.domain in SERVING_DOMAINS and it.entry.tag == Tag.DECISION
                  and not it.entry.serves)
