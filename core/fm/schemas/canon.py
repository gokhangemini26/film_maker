"""Canon: the structured, checkable source of truth.

Prose bibles carry reasoning; canon carries the decisions downstream work
depends on. Creative intent ("the protagonist should feel isolated") lives
in the `intent` domain and is kept separate from the decisions that
implement it (lens, negative space, palette), which point back to it via
`serves`. Implementations can then be revised without losing the intent.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from .common import CANON_ID_RE, Status, StrictModel, Tag

DOMAINS = (
    "intent",      # creative intent, independent of implementation
    "tone",        # tone, emotional objective, originality rules
    "story",       # premise, theme, structure, ending
    "world",       # geography, architecture, era, rules, production design
    "characters",  # identity, appearance, wardrobe, representation
    "look",        # visual language, colour, lighting (style lock at G4)
    "camera",      # lens set, camera language, screen-direction rules
    "animation",   # motion style, timing philosophy
    "audio",       # sound and music direction
    "continuity",  # per-scene time/weather/wardrobe state
)

# Domains where an approved DECISION must say *why*.
RATIONALE_REQUIRED_DOMAINS = {
    "tone", "story", "world", "characters", "look", "camera", "animation", "audio",
}


class HistoryItem(StrictModel):
    version: int
    hash: str
    status: Status
    change: str | None = None       # CHANGE-NNN that superseded this version
    at: str | None = None
    statement: str | None = None
    value: Any = None
    rationale: str | None = None


class CanonEntry(StrictModel):
    id: str = Field(description="domain.path.name, e.g. characters.mara.wardrobe.jacket")
    statement: str = Field(description="Human-readable decision or intent.")
    value: Any = Field(default=None, description="Machine-readable implementation value, if any.")
    rationale: str | None = Field(default=None, description="WHY this was decided.")
    serves: list[str] = Field(default_factory=list, description="intent.* ids this decision implements")
    depends_on: list[str] = Field(default_factory=list, description="other canon ids this relies on")
    applies_to: list[str] = Field(
        default_factory=list,
        description="Scope: scene ids (SC01), shot ids, sequence ids, character ids. Empty = whole film.",
    )
    tag: Tag = Tag.DECISION
    status: Status = Status.PROPOSED
    source: str = Field(default="unknown", description="user | agent:<role> | human:<name>")
    version: int = 1
    notes: str | None = None
    history: list[HistoryItem] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not CANON_ID_RE.match(v):
            raise ValueError(f"invalid canon id '{v}' (lowercase dotted path, e.g. look.color.primary)")
        return v

    @field_validator("serves")
    @classmethod
    def _serves(cls, v: list[str]) -> list[str]:
        for s in v:
            if not s.startswith("intent."):
                raise ValueError(f"serves must reference intent.* ids, got '{s}'")
        return v

    @property
    def domain(self) -> str:
        return self.id.split(".", 1)[0]

    def content(self) -> dict:
        """The part of the entry that constitutes the decision (hashed)."""
        return {
            "id": self.id,
            "statement": self.statement,
            "value": self.value,
            "rationale": self.rationale,
            "serves": sorted(self.serves),
            "depends_on": sorted(self.depends_on),
            "applies_to": sorted(self.applies_to),
            "tag": self.tag.value,
        }


class CanonFile(StrictModel):
    domain: str
    entries: list[CanonEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _domain(self) -> "CanonFile":
        if self.domain not in DOMAINS:
            raise ValueError(f"unknown canon domain '{self.domain}' (allowed: {', '.join(DOMAINS)})")
        for e in self.entries:
            if e.domain != self.domain:
                raise ValueError(f"entry '{e.id}' is not in domain '{self.domain}'")
        return self


# Editable fields a change request may set on a canon entry.
CHANGEABLE_FIELDS = ("statement", "value", "rationale", "serves", "depends_on", "applies_to", "tag")
