---
name: color-design
description: "Define primary, secondary and accent palettes, per-scene palettes and the emotional colour progression as hex canon plus a colour bible. Used by the look-director in LOOK."
user-invocable: false
---

# Colour design

## Purpose
Give colour a job: a palette that serves the intents, a progression that
moves with the story, and values precise enough for Blender.

## When to use
LOOK phase, with visual-development and lighting-design; colour revisions.

## Required inputs
- Intent/tone canon, STORY_STRUCTURE (emotional beats), SCENES.yaml,
  CHARACTER_BIBLE (wardrobe colours), ART_DIRECTION_BIBLE (materials).

## Process
1. Colour script: for each scene, dominant hue, saturation and value, and the
   emotion it supports — plot the progression across the film.
2. Palette: primary (ambient/world), secondary, accent(s). Limit accents; an
   accent that appears everywhere stops meaning anything.
3. Relationships: warm/cool split, complementary accents, saturation
   strategy (what is allowed to be saturated), value structure (key darks and lights).
4. Character separation: check wardrobe hex against each scene's palette
   (value contrast ≥ noticeable at night). If wardrobe must change, request it
   via the orchestrator (character canon belongs to the character-designer).
5. Exposure philosophy: where blacks sit, whether highlights clip, how dark
   "night" really is.
6. Canon: `look.color.primary`, `.secondary`, `.accent_*` (value `#RRGGBB`),
   per-scene keys as `look.color.scene.<scid>` with `value: {dominant: "#..",
   accent: "#.."}` and `applies_to: [SCxx]`, `look.exposure.*`.
   Hex only in M2; RGB/HSV/linear values are computed by the M3 resolver.

## Output format
`05_look/COLOR_BIBLE.md`: Colour intent · Palette table
`| id | hex | role | serves | never use for |` · Colour script by scene ·
Relationships and saturation rules · Character separation check · Exposure.

## Validation rules
- Every colour value in `look.color.*` is `#RRGGBB` (fm validates).
- Every scene in SCENES.yaml has a scene palette.
- Every accent is tied to an intent or motif.

## Failure conditions
- Wardrobe colour collides with the scene palette → flag with a proposed fix; do not edit character canon.

## Examples
`look.color.accent_hope` `#E0A040` — "Only on practical lights and the phone
screen. Rationale: warmth = contact with another person (intent.hope).
Rejected: warm grade on skin — it would make her feel warm from the start."
