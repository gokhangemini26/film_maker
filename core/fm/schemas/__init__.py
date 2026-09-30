"""FILM_MAKER data model. All models export to JSON Schema (`fm schema export`)."""
from .artifacts import (  # noqa: F401
    BRIEF_FIELDS, SHOT_NON_CONTENT, ArtifactMeta, Brief, BriefField, Camera, Composition,
    CreativeIntent, SceneEntry, SceneIndex,
    Environment, ShotCharacter, ShotRationale, ShotSpec, StyleBreak,
)
from .animation import AnimationTracks, anim_artifact_id, anim_path  # noqa: F401
from .canon import (  # noqa: F401
    CHANGEABLE_FIELDS, DOMAINS, RATIONALE_REQUIRED_DOMAINS, CanonEntry, CanonFile, HistoryItem,
)
from .common import (  # noqa: F401
    DERIVED_KINDS, HUMAN_BACKED, LAYER_ORDER, REF_RE, DepRef, Layer, Status, Tag, layer_of,
)
from .state import (  # noqa: F401
    Authorization, CanonLock, ChangeRequest, DerivedRecord, GateRecord, LedgerRecord,
    ProjectState,
)

EXPORTED = {
    "canon_file": CanonFile,
    "brief": Brief,
    "scene_index": SceneIndex,
    "artifact_meta": ArtifactMeta,
    "shot": ShotSpec,
    "project_state": ProjectState,
    "ledger_record": LedgerRecord,
    "change_request": ChangeRequest,
    "derived_record": DerivedRecord,
    "anim": AnimationTracks,
}
