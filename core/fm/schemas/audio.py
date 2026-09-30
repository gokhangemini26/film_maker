"""Audio cue sheet (M6 task E4): `12_post/AUDIO_CUES.yaml`, artifact kind `audio_cues`.

Structural typing lives here; every semantic rule (recipe exists, event ids exist, frames inside the shot,
silence map, licences, placeholders) is an `AUDIO_*` rule in `fm.audiocues` so an agent gets a precise
message instead of a load error. Every field a rule needs to explain itself is optional here.

Frames are shot-local, 0-based (a bed or silence span scoped to a scene is scene-local: frame 0 is the scene's
first frame). A cue is placed either at a named animation event (`at.event`, retiming the shot moves the cue)
or at an explicit shot-local frame (`at.frame`, alias `f`).
"""
from __future__ import annotations

from pydantic import Field

from .artifacts import ArtifactMeta
from .common import StrictModel

AUDIO_CUES_PATH = "12_post/AUDIO_CUES.yaml"
AUDIO_CUES_ID = "audio_cues"
LAYERS = ("ui", "sfx", "foley", "amb", "body", "music")
SUPPLY_SOURCES = ("recorded", "library", "licensed", "synth")
SUPPLY_STATUS = ("NEEDED", "SUPPLIED", "DECLINED")


class At(StrictModel):
    """Where a cue starts. Exactly one of `event` or `frame`/`f` (rule `AUDIO_AT`)."""

    event: str | None = Field(default=None, description="animation event id in the cue's shot (anim file `events`, or derived e.g. handle_top)")
    nth: int | None = Field(default=None, ge=0, description="which occurrence when the event id repeats in the shot (0-based)")
    each: bool = Field(default=False, description="expand to one placement at every occurrence of the event (ratchet from handle_top)")
    offset_f: float = Field(default=0, description="lead (negative) or lag (positive) in frames, added to the event or frame")
    frame: int | None = Field(default=None, ge=0, description="shot-local frame")
    f: int | None = Field(default=None, ge=0, description="alias of `frame`")


class Cue(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.\-]*$")
    shot: str
    recipe: str | None = Field(default=None, description="synth registry name (`fm audio list`)")
    asset: str | None = Field(default=None, description="library asset id: library/audio/<id>/asset.yaml (file + licence)")
    at: At = Field(default_factory=At)
    layer: str | None = Field(default=None, json_schema_extra={"enum": list(LAYERS)},
                              description="stem; default from the recipe family (ui/amb/body/music, else sfx)")
    gain_db: float = 0.0
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    fade_in_f: float = Field(default=0, ge=0)
    fade_out_f: float = Field(default=0, ge=0)
    duration_f: float | None = Field(default=None, gt=0, description="cue length in frames (default: recipe default / file length)")
    seed: int | None = Field(default=None, description="synth seed (default: stable hash of the placement id)")
    params: dict = Field(default_factory=dict, description="recipe parameters (see `fm audio list`)")
    hits: list[int] = Field(default_factory=list, description=(
        "shot-local frames INSIDE this cue where it lands on a named sync point (the recipe's own internal timing, e.g. "
        "engine_die shudder f26 and stop f32); they count for the +-1 frame coverage check, the mixer ignores them"))
    tail_ok: bool = Field(default=False, description="the sound may ring on past the shot's last frame (e.g. a chime on the cut)")
    allowed_in_silence: bool = Field(default=False, description="deliberate room-tone floor inside a silence span (must still measure below the span floor)")
    placeholder: bool = Field(default=False, description="mark an asset cue as a stand-in (recipes carry this in the registry)")
    serves: list[str] = Field(default_factory=list, description="intent.* ids")
    note: str | None = Field(default=None, description="free text for humans; never parsed")
    rationale: str | None = None


class Bed(StrictModel):
    """Ambience or room tone over a shot, or over a whole scene. Exactly one of `shot` / `scene`."""

    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.\-]*$")
    shot: str | None = None
    scene: str | None = None
    from_f: int | None = Field(default=None, ge=0, description="local frame (shot- or scene-relative); default 0")
    to_f: int | None = Field(default=None, ge=1, description="exclusive local frame; default the end of the shot/scene")
    recipe: str | None = None
    asset: str | None = None
    layer: str = "amb"
    xfade_f: float = Field(default=0, ge=0)
    gain_db: float = -30.0
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    seed: int | None = None
    params: dict = Field(default_factory=dict)
    allowed_in_silence: bool = False
    placeholder: bool = False
    note: str | None = None
    rationale: str | None = None


class Silence(StrictModel):
    """A span that must be silent (or at the room-tone floor). `fm qa audio` measures the rendered mix."""

    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.\-]*$")
    shot: str | None = None
    scene: str | None = None
    from_f: int | None = Field(default=None, ge=0)
    to_f: int | None = Field(default=None, ge=1)
    floor_db: float | None = Field(default=None, description="RMS ceiling in dBFS (default `mix.silence_floor_db`)")
    canon: str | None = Field(default=None, description="e.g. audio.silence_map")
    note: str | None = None
    rationale: str | None = None


class MixTargets(StrictModel):
    integrated_lufs: float = -16.0
    lufs_tolerance: float = Field(default=1.0, ge=0)
    true_peak_dbtp: float = -1.0
    silence_floor_db: float = -50.0
    sample_rate: int = 48000
    bit_depth: int = Field(default=24, description="16 or 24")
    channels: int = 2
    master_gain_db: float = Field(default=0.0, description="applied to every stem and the master; set from the QA suggestion")


class HumanSupply(StrictModel):
    """A sound the pipeline cannot make credibly: the human records or supplies it."""

    sound: str = Field(description="recipe name being replaced, or a new asset id")
    need: str
    source: str = Field(default="recorded", json_schema_extra={"enum": list(SUPPLY_SOURCES)})
    licence: str = "UNKNOWN"
    status: str = Field(default="NEEDED", json_schema_extra={"enum": list(SUPPLY_STATUS)})
    shots: list[str] = Field(default_factory=list)
    note: str | None = None


class Conflict(StrictModel):
    shots: list[str] = Field(default_factory=list)
    storyboard: str | None = None
    shot_file: str | None = None
    assumption: str | None = None


class AudioCues(StrictModel):
    """`12_post/AUDIO_CUES.yaml`."""

    fm: ArtifactMeta
    mix: MixTargets = Field(default_factory=MixTargets)
    cues: list[Cue] = Field(default_factory=list)
    beds: list[Bed] = Field(default_factory=list)
    silence: list[Silence] = Field(default_factory=list)
    human_supply: list[HumanSupply] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    scaffold_notes: list[str] = Field(default_factory=list, description="free text for humans (e.g. sync points the scaffold could not cover)")
