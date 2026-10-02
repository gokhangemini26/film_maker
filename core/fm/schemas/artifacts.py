"""Artifacts (prose/YAML documents), the creative brief, and shot specs."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .cinematic import Atmosphere, Grade
from .common import (
    SCENE_ID_RE, SEQUENCE_ID_RE, SHOT_ID_RE, SLUG_RE, DepRef, Status, StrictModel,
)


# ---------------------------------------------------------------- artifacts
class ArtifactMeta(StrictModel):
    """The `fm:` block at the top of every managed document.

    Everything outside this block is the artifact's content and is hashed.
    """

    id: str
    kind: str = Field(description="e.g. story_bible, screenplay, color_bible")
    phase: str
    status: Status = Status.PROPOSED
    owner_role: str | None = None
    derived_from: list[DepRef] = Field(default_factory=list)
    serves: list[str] = Field(default_factory=list, description="intent.* ids")
    summary: str | None = None
    # Managed by `fm stamp`; used to catch dependency refreshes without real revision.
    stamped_content_hash: str | None = None
    stamp_note: str | None = None

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError(f"invalid artifact id '{v}' (lowercase slug)")
        return v


# --------------------------------------------------------------------- brief
BriefStatus = Literal["given", "assumed", "unknown"]


class BriefField(StrictModel):
    value: Any = None
    status: BriefStatus = "unknown"
    note: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> "BriefField":
        if self.status != "unknown" and self.value in (None, ""):
            raise ValueError(f"brief field marked '{self.status}' but has no value")
        return self


BRIEF_FIELDS = (
    "title", "concept", "genre", "duration_s", "target_audience", "emotional_goal",
    "story_idea", "visual_style", "color_palette", "references", "realism",
    "animation_style", "camera_style", "lighting_style", "environment", "characters",
    "era", "location", "aspect_ratio", "fps", "special_requirements",
)


class Brief(StrictModel):
    fm: ArtifactMeta
    fields: dict[str, BriefField]

    @field_validator("fields")
    @classmethod
    def _known(cls, v: dict[str, BriefField]) -> dict[str, BriefField]:
        unknown = set(v) - set(BRIEF_FIELDS)
        if unknown:
            raise ValueError(f"unknown brief fields: {sorted(unknown)}")
        return v


# --------------------------------------------------------------------- shots
class SceneEntry(StrictModel):
    """One row of the screenplay's machine-readable scene index."""

    scene_id: str
    heading: str
    summary: str | None = None
    est_duration_s: float | None = Field(default=None, gt=0)
    characters: list[str] = Field(default_factory=list)
    location: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    sequence_id: str | None = None

    @field_validator("scene_id")
    @classmethod
    def _scene(cls, v: str) -> str:
        if not SCENE_ID_RE.match(v):
            raise ValueError(f"invalid scene_id '{v}' (expected SC01)")
        return v


class SceneIndex(StrictModel):
    """02_screenplay/SCENES.yaml"""

    fm: ArtifactMeta
    scenes: list[SceneEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> "SceneIndex":
        ids = [s.scene_id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate scene_id in scene index")
        return self


class CreativeIntent(StrictModel):
    """What the shot is FOR, independent of how it is implemented."""

    narrative_purpose: str | None = None
    emotional_purpose: str | None = None
    visual_purpose: str | None = None
    audience_effect: str | None = None


class ShotRationale(StrictModel):
    """WHY each implementation choice serves the intent."""

    camera: str | None = None
    lighting: str | None = None
    composition: str | None = None
    movement: str | None = None
    color: str | None = None
    blocking: str | None = None
    animation: str | None = None


Vec3 = tuple[float, float, float]


class DepthOfField(StrictModel):
    enabled: bool = False
    f_stop: float | None = Field(default=None, gt=0)
    focus_target: str | None = None


class Camera(StrictModel):
    lens_mm: float | None = Field(default=None, ge=6, le=1200)
    height_m: float | None = None
    movement: str | None = None
    start_position: Vec3 | None = None
    end_position: Vec3 | None = None
    look_at: str | None = None
    dof: DepthOfField | None = None


class Composition(StrictModel):
    framing: str | None = None
    aspect_ratio: float | None = Field(default=None, gt=0)
    subject_position: str | None = None
    notes: str | None = None


class ShotCharacter(StrictModel):
    id: str = Field(description="character id as used in canon: characters.<id>.*")
    position: Vec3 | None = None
    facing: str | None = None
    action: str | None = None


class Environment(StrictModel):
    location: str | None = None
    weather: str | None = None
    time_of_day: str | None = None


class StyleBreak(StrictModel):
    reason: str = Field(min_length=10)
    approved_by_intent: list[str] = Field(default_factory=list)


class ShotSpec(StrictModel):
    """Machine-readable specification of one shot.

    Implementation blocks (lighting/color/animation/render) stay open
    dictionaries in M1; they are tightened as their builders land (M3+).
    """

    shot_id: str
    scene_id: str
    sequence_id: str | None = None
    status: Status = Status.PROPOSED
    duration_s: float = Field(gt=0, le=600)
    serves: list[str] = Field(default_factory=list, description="intent.* ids")
    creative_intent: CreativeIntent = Field(default_factory=CreativeIntent)
    camera: Camera | None = None
    composition: Composition | None = None
    characters: list[ShotCharacter] = Field(default_factory=list)
    environment: Environment | None = None
    lighting: dict[str, Any] | None = None
    color: dict[str, Any] | None = None
    animation: dict[str, Any] | None = None
    render: dict[str, Any] | None = None
    atmosphere: Atmosphere | None = Field(default=None, description="opt-in: HDRI environment + volumetric fog (docs/CINEMATIC_PIPELINE.md)")
    grade: Grade | None = Field(default=None, description="opt-in: compositor colour grade for this shot (overrides canon look.grade)")
    assets: list[str] = Field(default_factory=list)
    rationale: ShotRationale = Field(default_factory=ShotRationale)
    style_break: StyleBreak | None = None
    continuity_refs: list[str] = Field(default_factory=list)
    derived_from: list[DepRef] = Field(default_factory=list)
    stamped_content_hash: str | None = None
    stamp_note: str | None = None

    @field_validator("shot_id")
    @classmethod
    def _shot(cls, v: str) -> str:
        if not SHOT_ID_RE.match(v):
            raise ValueError(f"invalid shot_id '{v}' (expected SC01_SH010)")
        return v

    @field_validator("scene_id")
    @classmethod
    def _scene(cls, v: str) -> str:
        if not SCENE_ID_RE.match(v):
            raise ValueError(f"invalid scene_id '{v}' (expected SC01)")
        return v

    @field_validator("sequence_id")
    @classmethod
    def _seq(cls, v: str | None) -> str | None:
        if v is not None and not SEQUENCE_ID_RE.match(v):
            raise ValueError(f"invalid sequence_id '{v}' (expected SQ01)")
        return v

    @field_validator("serves")
    @classmethod
    def _serves(cls, v: list[str]) -> list[str]:
        for s in v:
            if not s.startswith("intent."):
                raise ValueError(f"serves must reference intent.* ids, got '{s}'")
        return v

    @model_validator(mode="after")
    def _cinematic_rationale(self) -> "ShotSpec":
        for name in ("atmosphere", "grade"):
            block = getattr(self, name)
            if block is not None and not (block.rationale or "").strip():
                raise ValueError(f"{name} needs a rationale (say why this atmosphere/grade serves the shot's intent)")
        return self

    @model_validator(mode="after")
    def _scene_prefix(self) -> "ShotSpec":
        if not self.shot_id.startswith(self.scene_id + "_"):
            raise ValueError(f"shot_id '{self.shot_id}' does not belong to scene '{self.scene_id}'")
        return self


# Shot fields excluded from the content hash: lifecycle + bookkeeping.
SHOT_NON_CONTENT = ("status", "derived_from", "stamped_content_hash", "stamp_note")
# Optional fields added after films existed: they join the content hash only when set, so a shot that never uses them
# hashes exactly as it did before they were introduced (no existing node goes stale).
SHOT_OPTIONAL_CONTENT = ("atmosphere", "grade")
