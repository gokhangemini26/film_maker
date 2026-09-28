"""Which agent role owns which artifacts and canon domains.

Used only for advisory warnings (`OWNER_MISMATCH`): ownership keeps
responsibilities clear, but authority stays with the human gates.
"""
from __future__ import annotations

# artifact kind -> owning role
ARTIFACT_OWNERS: dict[str, str] = {
    "brief": "executive-producer",
    "brief_analysis": "creative-director",
    "creative_direction": "creative-director",
    "story_bible": "story-architect",
    "story_structure": "story-architect",
    "screenplay": "screenwriter",
    "scene_index": "screenwriter",
    "world_bible": "world-designer",
    "art_direction_bible": "world-designer",
    "character_bible": "character-designer",
    "visual_bible": "look-director",
    "color_bible": "look-director",
    "lighting_bible": "look-director",
    "cinematography_bible": "cinematographer",
    "storyboard": "cinematographer",
    "shot_list": "cinematographer",
    "gate_review": "qa-supervisor",
}

# role -> canon domains it may propose entries in
CANON_DOMAINS: dict[str, tuple[str, ...]] = {
    "creative-director": ("intent", "tone"),
    "story-architect": ("story",),
    "screenwriter": ("story",),
    "world-designer": ("world",),
    "character-designer": ("characters",),
    "look-director": ("look",),
    "cinematographer": ("camera", "continuity"),
    "animation-director": ("animation",),
    "post-supervisor": ("audio",),
}

# gate -> the review artifact that must accompany its submission
REVIEW_FOR_GATE: dict[str, str] = {
    "G1": "qa/reviews/G1_REVIEW.md",
    "G2": "qa/reviews/G2_REVIEW.md",
    "G3": "qa/reviews/G3_REVIEW.md",
    "G4": "qa/reviews/G4_REVIEW.md",
    "G5": "qa/reviews/G5_REVIEW.md",
}
VERDICTS = ("PASS", "WARN", "FAIL")
