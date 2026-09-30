"""Shared vocabulary for every FILM_MAKER data file.

Nothing in this package is specific to any model provider: these types
describe film production data, and are exported to JSON Schema so any
tool or model can read and write them.
"""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class Status(str, Enum):
    """Lifecycle of every decision, artifact and shot.

    PROPOSED    an agent (or the user) suggested it; nothing may rely on it as final
    APPROVED    a human accepted it (recorded in the ledger)
    LOCKED      approved and frozen; only an approved change request can alter it
    SUPERSEDED  replaced by a newer version through a change request
    REJECTED    a human declined it
    """

    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


HUMAN_BACKED = {Status.APPROVED, Status.LOCKED, Status.SUPERSEDED, Status.REJECTED}


class Tag(str, Enum):
    """Epistemic tag: what kind of statement this is."""

    FACT = "FACT"
    DECISION = "DECISION"
    ASSUMPTION = "ASSUMPTION"
    RECOMMENDATION = "RECOMMENDATION"
    USER_REQUIREMENT = "USER_REQUIREMENT"
    DEPENDENCY = "DEPENDENCY"
    UNKNOWN = "UNKNOWN"


class Layer(str, Enum):
    """Layers of the production dependency graph, upstream to downstream."""

    INTENT = "INTENT"
    CANON = "CANON"
    ARTIFACT = "ARTIFACT"
    SHOT = "SHOT"
    RESOLVED = "RESOLVED"
    BLEND = "BLEND"
    RENDER = "RENDER"
    AUDIO = "AUDIO"
    EDIT = "EDIT"
    QA = "QA"


LAYER_ORDER = {layer: i for i, layer in enumerate(Layer)}

# ref kinds -> layer. canon refs whose id starts with "intent." are INTENT.
REF_KINDS = {
    "canon": Layer.CANON,
    "artifact": Layer.ARTIFACT,
    "shot": Layer.SHOT,
    "resolved": Layer.RESOLVED,
    "blend": Layer.BLEND,
    "render": Layer.RENDER,
    "audio": Layer.AUDIO,
    "edit": Layer.EDIT,
    "qa": Layer.QA,
}
# Kinds `fm record` / record_derived may write (M6 added audio: stems, mixes; edit: EDL, animatic, master).
DERIVED_KINDS = ("resolved", "blend", "render", "audio", "edit", "qa")

REF_RE = re.compile(
    r"^(canon|artifact|shot|resolved|blend|render|audio|edit|qa):[A-Za-z0-9_.\-]+$")
CANON_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9][a-z0-9_\-]*)+$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
SHOT_ID_RE = re.compile(r"^SC\d{2,3}_SH\d{3,4}$")
SCENE_ID_RE = re.compile(r"^SC\d{2,3}$")
SEQUENCE_ID_RE = re.compile(r"^SQ\d{2,3}$")


def layer_of(ref: str) -> Layer:
    kind, _, ident = ref.partition(":")
    if kind == "canon" and ident.startswith("intent."):
        return Layer.INTENT
    return REF_KINDS[kind]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class DepRef(StrictModel):
    """An upstream dependency. `hash` is the upstream content hash at the
    time this node was produced; None means a structural edge only."""

    ref: str
    hash: str | None = None

    @field_validator("ref")
    @classmethod
    def _ref(cls, v: str) -> str:
        if not REF_RE.match(v):
            raise ValueError(f"invalid ref '{v}' (expected kind:id, kind in {sorted(REF_KINDS)})")
        return v
