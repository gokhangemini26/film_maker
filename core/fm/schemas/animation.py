"""Structured shot animation (M6): `09_animation/<SHOT>.anim.yaml`, artifact kind `shot_animation`.

The prose `animation` block in the G5-approved shot file stays untouched (the human-readable
brief). This sidecar holds the typed tracks a builder reads. Structural typing lives here;
vocabulary membership, frame ranges and shot context are `ANIM_*` rules (`fm.animcheck`) so an
agent gets a precise message instead of a load error.

Every key keeps a free-text `note` (for humans, never parsed) and may keep a `rationale`.
Frames are shot-local, 0-based integers; the resolver adds absolute film frames.

The fixture files written by the phase tests carry only `fm` and `shot_id`: every other
field is optional so those stay valid ("stub" files; see `AnimationTracks.is_stub`).
"""
from __future__ import annotations

from pydantic import Field, field_validator

from .. import animvocab as V
from .artifacts import ArtifactMeta
from .common import SHOT_ID_RE, StrictModel


class _Key(StrictModel):
    f: int = Field(ge=0, description="shot-local frame, 0-based")
    note: str | None = Field(default=None, description="free text for humans; never parsed")
    rationale: str | None = Field(default=None, description="why this key serves the shot")


class PoseKey(_Key):
    ref: str = Field(description="pose preset name", json_schema_extra={"x-vocab": "pose.<character>"})
    ease: str = Field(default="ease_in_out", json_schema_extra={"enum": list(V.EASES)})
    blend_f: int | None = Field(default=None, ge=0, description=(
        "frames the blend INTO this pose takes, starting at f (0/None = switch at f); must end by the next key"))


class PathPoint(StrictModel):
    f: int = Field(ge=0)
    x: float
    y: float


class MoveTrack(StrictModel):
    gait: str = Field(default="none", json_schema_extra={"enum": list(V.GAITS)})
    path: list[PathPoint] = Field(default_factory=list, description="waypoints in set coords; required for locomotion gaits")
    speed_mps: float | None = Field(default=None, ge=0, description="peak speed, for QA")
    start_f: int | None = Field(default=None, ge=0, description="crank_turn: frame the first turn begins (default: already turning)")
    first_top_f: int | None = Field(default=None, description=(
        "crank_turn: a frame at which the handle is at 12 o'clock; tops repeat every 24 frames (may be negative "
        "when the cycle was already running before the shot)"))
    stop_f: int | None = Field(default=None, ge=0, description="crank_turn: frame the handle stops (optional)")
    note: str | None = None
    rationale: str | None = None


class FaceKey(_Key):
    ref: str = Field(json_schema_extra={"x-vocab": "face.<character>"})


class LookKey(_Key):
    target: str = Field(json_schema_extra={"enum": list(V.LOOK_TARGETS)})


class BreathKey(_Key):
    ref: str = Field(json_schema_extra={"enum": list(V.BREATHS)})
    dur_f: int | None = Field(default=None, ge=1)


class LidKey(_Key):
    """v2: eyelid openness multiplier on the face's own eye openness; the gaze (look track) is kept."""

    ref: str = Field(json_schema_extra={"enum": list(V.LIDS)})
    ease: str = Field(default="ease_in_out", json_schema_extra={"enum": list(V.EASES)})
    dur_f: int | None = Field(default=None, ge=1, description=(
        "frames the change INTO this lids value takes, starting at f; must end by the next lids key"))


class CharacterTracks(StrictModel):
    pose: list[PoseKey] = Field(default_factory=list)
    move: MoveTrack = Field(default_factory=MoveTrack)
    face: list[FaceKey] = Field(default_factory=list)
    look: list[LookKey] = Field(default_factory=list)
    breath: list[BreathKey] = Field(default_factory=list)
    lids: list[LidKey] = Field(default_factory=list, description="vocabulary v2: blinks and heavy lids that keep the gaze")


class PropKey(_Key):
    """One key of a prop track. Which value fields are legal depends on the prop (animvocab.PROPS)."""

    state: str | None = None
    loc: str | None = None
    arm: str | None = None
    attach: str | None = None
    pip: float | None = Field(default=None, ge=0, le=1)
    tilt_deg: float | None = None
    swing_deg: float | None = None
    bounce_f: int | None = Field(default=None, ge=0)
    ease: str | None = Field(default=None, json_schema_extra={"enum": list(V.EASES)})
    dur_f: int | None = Field(default=None, ge=1, description="frames the change takes, starting at f")


class UiEvent(_Key):
    event: str = Field(json_schema_extra={"enum": list(V.UI_EVENTS)})
    phone: str = Field(default="ren", json_schema_extra={"enum": list(V.UI_PHONES)})
    dur_f: int | None = Field(default=None, ge=1)
    value: float | None = Field(default=None, description="dip: brightness (default 0.7)")
    key: str | None = Field(default=None, json_schema_extra={"enum": list(V.UI_KEYS)})
    line: int | None = Field(default=None, ge=1, le=3)
    chars: int | None = Field(default=None, ge=0)
    to: str | None = Field(default=None, json_schema_extra={"enum": list(V.UI_SCREENS)})
    from_pct: float | None = None
    to_pct: float | None = None


class CameraTrack(StrictModel):
    move: str = Field(default="none", json_schema_extra={"enum": list(V.CAMERA_MOVES)})
    start_f: int | None = Field(default=None, ge=0)
    end_f: int | None = Field(default=None, ge=0)
    dist_m: float | None = Field(default=None, gt=0)
    ease_in_f: tuple[int, int] | None = None
    ease_out_f: tuple[int, int] | None = None
    peak_speed_mps: float | None = Field(default=None, ge=0)
    note: str | None = None
    rationale: str | None = None


class Hold(StrictModel):
    f0: int = Field(ge=0)
    f1: int = Field(ge=0)
    scope: str = Field(json_schema_extra={"enum": list(V.HOLD_SCOPES)})
    character: str | None = None
    min_f: int | None = Field(default=None, ge=1, description="minimum frames the hold must last (legibility rule)")
    note: str | None = None
    rationale: str | None = None


class EventKey(_Key):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", description="unique per shot; audio and QA refer to it")
    kind: str = Field(default="sound", json_schema_extra={"enum": list(V.EVENT_KINDS)})


class AnimationTracks(StrictModel):
    """`09_animation/<SHOT>.anim.yaml`."""

    fm: ArtifactMeta
    shot_id: str
    frames: int | None = Field(default=None, ge=1, description="must equal the resolver's frame count for the shot")
    vocab_version: int | None = Field(default=None, ge=1, description="animation.vocab version this was written against")
    rationale: str | None = Field(default=None, description="why this motion serves the shot (CLAUDE.md rule 4)")
    characters: dict[str, CharacterTracks] = Field(default_factory=dict)
    props: dict[str, list[PropKey]] = Field(default_factory=dict)
    ui_timeline: list[UiEvent] = Field(default_factory=list)
    camera: CameraTrack = Field(default_factory=CameraTrack)
    holds: list[Hold] = Field(default_factory=list)
    events: list[EventKey] = Field(default_factory=list)
    preview_frames: list[int] = Field(default_factory=list, description="default: every pose key plus the last frame")
    notes: list[str] = Field(default_factory=list, description="free text for humans; never parsed")

    @field_validator("shot_id")
    @classmethod
    def _shot(cls, v: str) -> str:
        if not SHOT_ID_RE.match(v):
            raise ValueError(f"invalid shot_id '{v}' (expected SC01_SH010)")
        return v

    @property
    def is_stub(self) -> bool:
        """A bare file (only `fm` and `shot_id`): valid, but carries no motion."""
        return self.vocab_version is None and self.frames is None and not (
            self.characters or self.props or self.ui_timeline or self.events or self.holds
            or self.camera.move != "none")


def anim_artifact_id(shot_id: str) -> str:
    """Artifact ids are lowercase slugs: SC04_SH040 -> anim_sc04_sh040."""
    return "anim_" + shot_id.lower()


def anim_path(shot_id: str) -> str:
    return f"09_animation/{shot_id}.anim.yaml"
