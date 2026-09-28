---
name: lighting-design
description: "Define motivated lighting - key/fill/rim strategy, practicals, colour temperature, contrast, shadows, volumetrics and exposure - as a lighting bible and canon. Used by the look-director in LOOK."
user-invocable: false
---

# Lighting design

## Purpose
Light that is motivated by the world and serves the emotion: every light has
a source in the world and a reason in the story.

## When to use
LOOK phase with visual-development and color-design; lighting revisions.

## Required inputs
- WORLD_BIBLE (light sources that exist), ART_DIRECTION_BIBLE (sets),
  COLOR_BIBLE, SCENES.yaml (time/weather), intent/tone canon.

## Process
1. Motivation map per location: every possible source (sky, streetlamps,
   windows, signs, screens) with type, colour temperature and height.
2. Key strategy: where the key usually comes from relative to the subject
   (side/back/top), and how that changes with the arc.
3. Fill and contrast: target contrast ratio per scene (e.g. night exteriors
   8:1 or harder), whether fill exists at all.
4. Rim/separation: how characters separate from backgrounds when the key is weak.
5. Practicals: which are visible in frame, which are hero practicals.
6. Colour temperature split: ambient vs practical Kelvin, tied to colour canon.
7. Shadows: hard/soft, their direction, what they hide.
8. Volumetrics and weather: fog density, rain catching light — cost aware for EEVEE.
9. Exposure: where mid-grey sits; what may clip.
10. Canon: `look.lighting.*` (strategy rules, per-scene `applies_to`), with
    Kelvin/ratios in `value`, DECISION + rationale + serves.

## Output format
`05_look/LIGHTING_BIBLE.md`: Principles · Motivation maps per location ·
Per-scene lighting plan `| scene | key source | K | contrast | rim | practicals | volumetrics | mood |`
· Arc of light across the film · Feasibility notes for EEVEE.

## Validation rules
- No unmotivated light (every light names its world source or is an explicit style rule).
- Consistent with colour canon (Kelvin ↔ palette).
- Every scene covered.

## Failure conditions
- The world has no plausible source for a needed light → propose adding a
  practical to the set (world-designer's decision) rather than faking one.

## Examples
`look.lighting.night_exterior` value `{ambient_k: 7500, practical_k: 2200,
contrast: "10:1", fill: none}` — "Cold ambient with no fill keeps her half
unreadable; rim from wet ground bounce only. Rejected: soft fill — makes the
street feel safe."
