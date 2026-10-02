"""Opt-in cinematic blocks: `atmosphere` (HDRI environment + volumetric fog) and `grade` (compositor colour grade).

Both are OPTIONAL everywhere they appear (shot spec, canon `look.atmosphere*` / `look.grade*`). A film that never
writes one is validated, resolved and hashed exactly as before: absent means absent, never a default block.

Rule 4 (CLAUDE.md): a decision says why. On a shot the block must carry a `rationale`; in canon the entry's own
`rationale` field plays that part (so the model keeps it optional and `ShotSpec` enforces it).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import StrictModel

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
HDRI_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")
CANON_ATMOSPHERE = "look.atmosphere"
CANON_GRADE = "look.grade"
VIEW_TRANSFORMS = ("Standard", "AgX", "Filmic", "Khronos PBR Neutral", "Raw")
GLARE_TYPES = ("bloom", "fog_glow")

Vec3 = tuple[float, float, float]


class Hdri(StrictModel):
    """Image-based environment light from `library/hdri/<id>/` (Poly Haven CC0 expected)."""

    id: str = Field(description="library/hdri/<id>/ (asset.yaml + the .hdr/.exr it names)")
    rotation_deg: float = Field(default=0.0, ge=-360, le=360, description="rotation about the vertical axis")
    strength: float = Field(default=1.0, ge=0, le=100)
    camera_visible: bool = Field(default=True, description="false: the HDRI only lights; camera rays keep the painted sky")

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not HDRI_ID_RE.match(v):
            raise ValueError(f"invalid hdri id '{v}' (lowercase letters, digits, '_' and '-')")
        return v


class Box(StrictModel):
    center: Vec3 = (0.0, 0.0, 1.0)
    size: Vec3 = (10.0, 10.0, 3.0)

    @field_validator("size")
    @classmethod
    def _size(cls, v: Vec3) -> Vec3:
        if any(x <= 0 for x in v):
            raise ValueError("fog box size must be positive on every axis")
        return v


class Fog(StrictModel):
    """Volumetric scatter. `density` is the scatter coefficient per metre (0.005 haze .. 0.05 thick fog)."""

    density: float = Field(gt=0, le=10)
    anisotropy: float = Field(default=0.0, ge=-0.99, le=0.99, description="0 isotropic, >0 forward scatter (light shafts)")
    height_falloff: float = Field(default=0.0, ge=0, le=10, description="1/m: density * exp(-falloff * z); 0 = uniform")
    colour: str = "#FFFFFF"
    bounds: Literal["world", "box"] = "world"
    box: Box | None = None

    @field_validator("colour")
    @classmethod
    def _colour(cls, v: str) -> str:
        if not HEX_RE.match(v):
            raise ValueError(f"fog colour must be #RRGGBB, got '{v}'")
        return v.upper()

    @model_validator(mode="after")
    def _box(self) -> "Fog":
        if self.bounds == "box" and self.box is None:
            raise ValueError("fog.bounds is 'box' but fog.box (center, size) is missing")
        if self.bounds == "world" and self.box is not None:
            raise ValueError("fog.box is only used with bounds: box")
        return self


class Atmosphere(StrictModel):
    hdri: Hdri | None = None
    fog: Fog | None = None
    rationale: str | None = None

    @model_validator(mode="after")
    def _something(self) -> "Atmosphere":
        if self.hdri is None and self.fog is None:
            raise ValueError("atmosphere needs at least one of hdri, fog")
        return self


class ColorBalance(StrictModel):
    """Blender Color Balance node. lift_gamma_gain: colours where 1.0 is neutral (Blender's convention);
    cdl: ASC CDL slope/power neutral 1.0, offset neutral 0.0."""

    mode: Literal["lift_gamma_gain", "cdl"] = "lift_gamma_gain"
    lift: Vec3 = (1.0, 1.0, 1.0)
    gamma: Vec3 = (1.0, 1.0, 1.0)
    gain: Vec3 = (1.0, 1.0, 1.0)
    offset: Vec3 = (0.0, 0.0, 0.0)
    power: Vec3 = (1.0, 1.0, 1.0)
    slope: Vec3 = (1.0, 1.0, 1.0)

    @model_validator(mode="after")
    def _ranges(self) -> "ColorBalance":
        for name in ("lift", "gamma", "gain", "power", "slope"):
            if any(not 0.0 <= x <= 4.0 for x in getattr(self, name)):
                raise ValueError(f"color_balance.{name} values must be in [0, 4]")
        if any(not -1.0 <= x <= 1.0 for x in self.offset):
            raise ValueError("color_balance.offset values must be in [-1, 1]")
        return self


class GradeGlare(StrictModel):
    type: Literal["bloom", "fog_glow"] = "bloom"
    threshold: float = Field(default=1.0, ge=0, le=100)
    strength: float = Field(default=0.3, ge=0, le=10)
    size: float = Field(default=0.02, gt=0, le=1, description="fraction of the frame width (Blender 5.x)")


class Grade(StrictModel):
    """Compositor grade, applied in this order: exposure -> color balance -> saturation -> curves -> glare."""

    view_transform: Literal["Standard", "AgX", "Filmic", "Khronos PBR Neutral", "Raw"] | None = None
    look: str | None = None
    exposure_ev: float | None = Field(default=None, ge=-10, le=10)
    color_balance: ColorBalance | None = None
    saturation: float | None = Field(default=None, ge=0, le=4, description="1.0 neutral")
    curves: list[tuple[float, float]] | None = Field(default=None, description="master RGB curve control points (x, y) in 0..1")
    glare: GradeGlare | None = None
    rationale: str | None = None

    @field_validator("curves")
    @classmethod
    def _curves(cls, v):
        if v is None:
            return v
        if len(v) < 2 or len(v) > 16:
            raise ValueError("grade.curves needs 2..16 control points")
        xs = [p[0] for p in v]
        if any(not (0.0 <= p[0] <= 1.0 and 0.0 <= p[1] <= 1.0) for p in v):
            raise ValueError("grade.curves points must lie in 0..1")
        if any(b <= a for a, b in zip(xs, xs[1:])):
            raise ValueError("grade.curves x values must be strictly increasing")
        return v

    @model_validator(mode="after")
    def _something(self) -> "Grade":
        if all(getattr(self, k) is None for k in ("view_transform", "look", "exposure_ev", "color_balance", "saturation", "curves", "glare")):
            raise ValueError("grade needs at least one of view_transform, look, exposure_ev, color_balance, saturation, curves, glare")
        return self


def parse_atmosphere(value) -> Atmosphere:
    return Atmosphere.model_validate(value)


def parse_grade(value) -> Grade:
    return Grade.model_validate(value)
