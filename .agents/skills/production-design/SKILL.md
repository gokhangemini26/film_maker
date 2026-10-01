---
name: production-design
description: "Design sets, props, materials, set dressing and visual hierarchy for each location as an art direction bible. Used by the world-designer in WORLD_CHARACTERS."
user-invocable: false
---

# Production design

## Purpose
Translate the world into buildable sets and props with a clear visual
hierarchy, so each frame shows the audience what matters first.

## When to use
WORLD_CHARACTERS phase, after the world bible draft; revisions to sets or props.

## Required inputs
- WORLD_BIBLE.md and world canon; SCREENPLAY.md/SCENES.yaml; CREATIVE_DIRECTION.
- Production constraints (proxy characters, Blender 5.2, laptop rendering).

## Process
1. Per location, define the set: footprint (rough metres), key architecture,
   what is in foreground / midground / background, entrances and eyelines.
2. Hero props: anything a character touches or the story needs (e.g. the
   phone). Give each an id, size, material and story function.
3. Materials palette: a few material families per location (wet asphalt,
   painted steel, glass), with roughness/wear notes — the look-director sets
   colour; you set material character.
4. Visual hierarchy: what the eye should find first in this location, and
   which design choices guarantee it (contrast, isolation, scale).
5. Set dressing density: sparse vs dense and why (tie to intent).
6. Build list for M3: primitives/procedural vs asset needed; mark any asset
   whose licence is unknown.
7. Propose canon: `world.sets.<location>.*`, `world.props.<id>` with
   rationale; the phone/key props become shot `assets` later.

## Output format
`03_world/ART_DIRECTION_BIBLE.md`: Principles · Per-location sets (footprint,
layers, hierarchy, materials, dressing) · Hero props table
`| id | object | size | material | story function | scenes |` · Build list.
`fm:` derived_from WORLD_BIBLE and world canon.

## Validation rules
- Every hero prop the screenplay mentions is listed with an id.
- Sizes are given in metres (Blender units).
- No trademarked logos or identifiable brands.

## Failure conditions
- A set needs more geometry than the MVP can build → propose staging that
  hides it (fog, depth of field, tight framing) and flag for the cinematographer.

## Examples
Hierarchy note: "Harbour street: the only saturated object is the phone
screen; everything else stays below 30% saturation so the signal is found instantly."
