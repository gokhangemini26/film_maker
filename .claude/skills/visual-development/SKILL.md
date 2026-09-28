---
name: visual-development
description: "Define the film's visual language - style, realism vs stylisation, texture, atmosphere, composition principles and visual motifs - as the visual bible that becomes the style lock. Used by the look-director in LOOK."
user-invocable: false
---

# Visual development

## Purpose
Decide how the film looks as a whole, so that colour, light, sets, characters
and camera all express one identity. Approved at G4 as the **style lock**.

## When to use
LOOK phase (`/film-look`), always together with color-design and lighting-design.

## Required inputs
- Locked intent/tone/story/world/characters canon; CREATIVE_DIRECTION
  (reference principles + originality statement); ART_DIRECTION_BIBLE; CHARACTER_BIBLE.
- MVP constraints: stylised proxies, Blender 5.2 EEVEE, laptop render budget.

## Process
1. Realism level: where on the scale from graphic to photoreal, and why. With
   proxies, choose a stylisation where simplified characters look intentional
   (e.g. sculptural matte figures, strong silhouettes, painterly atmosphere).
2. Texture and surface: how detailed surfaces are, grain/noise, softness.
3. Atmosphere: fog, haze, rain, particles — how much depth separation they give.
4. Composition principles: symmetry vs asymmetry, negative space, depth
   staging, horizon placement — as rules the cinematographer will follow.
5. Visual motifs: 1–3 recurring images/shapes/colours that carry meaning
   across the film (tie each to an intent and name where it recurs).
6. Style lock list: the explicit rules that later work must obey, and how a
   shot may deliberately break them (`style_break` with reason).
7. Canon: `look.style.*` entries (realism, texture, atmosphere, composition
   rules, motifs), DECISION + rationale + serves.

## Output format
`05_look/VISUAL_BIBLE.md`: Visual identity in one paragraph · Realism and
stylisation · Texture · Atmosphere · Composition rules · Motifs (table:
motif, meaning, serves, where it appears) · Style lock (numbered rules) ·
How to break the style deliberately. `fm:` derived_from CREATIVE_DIRECTION,
ART_DIRECTION_BIBLE, CHARACTER_BIBLE, look canon.

## Validation rules
- The style is achievable with the MVP pipeline, or the gap is flagged.
- Every style-lock rule is checkable in a frame (the qa-supervisor must be
  able to say PASS/FAIL against it).
- Consistent with the originality statement.

## Failure conditions
- Taste references demand photoreal humans → explain the MVP limit and propose
  a stylisation that serves the same intent.

## Examples
Style-lock rule: "Only practical sources may be warm (≥ 3500K is forbidden for
ambient/sky). Break allowed once, in the final shot, when warmth reaches Mara."
