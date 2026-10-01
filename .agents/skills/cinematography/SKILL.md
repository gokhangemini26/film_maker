---
name: cinematography
description: "Define the film's camera language - lens set, camera height, movement, framing, depth of field, blocking, screen direction and visual rhythm - with a reason for every choice. Used by the cinematographer in CINEMATOGRAPHY and STORYBOARD."
user-invocable: false
---

# Cinematography

## Purpose
A camera language that serves the intents and stays consistent: lenses,
heights, movement and framing are chosen, not defaulted.

## When to use
CINEMATOGRAPHY phase (`/film-cinematography`); every shot design in STORYBOARD.

## Required inputs
- Locked look canon (style lock), VISUAL/LIGHTING bibles, SCREENPLAY, SCENES.yaml,
  ART_DIRECTION_BIBLE (sets, footprints), CHARACTER_BIBLE (heights).

## Process
1. **Lens set**: a small prime set (3–5 focal lengths). For each: what it does
   (compression, distortion, intimacy) and when the film uses it.
2. **Camera height** conventions: eye level, below, above — and what each means here.
3. **Movement grammar**: when the camera moves, why it moves (motivated by a
   character, a reveal, or an emotional shift), and when it must not.
4. **Framing**: shot-scale vocabulary; headroom/lead-room rules; how negative
   space is used (tie to composition rules in the style lock).
5. **Depth**: foreground/midground/background staging; depth of field
   strategy (f-stop range) and focus pulls as story events.
6. **Screen direction and geography**: per scene, the 180° line, which way
   characters travel, how geography is established before it is broken.
7. **Rhythm**: typical shot durations per sequence; where cutting speeds up
   or holds; relation to the story's beat budget.
8. **Continuity canon**: per scene `continuity.<scid>.*` (time, weather,
   location, screen_direction) with `applies_to: [SCxx]`, values as a dict
   with keys `time_of_day`, `weather`, `location` so `fm check continuity` can verify shots.
9. Canon: `camera.lens_set`, `camera.height.*`, `camera.movement.*`,
   `camera.dof.*`, `camera.rhythm.*` — DECISION + rationale + serves.

## Output format
`06_cinematography/CINEMATOGRAPHY_BIBLE.md`: Camera philosophy · Lens set
table `| mm | effect | used for | never for |` · Heights · Movement grammar ·
Framing and negative space · Depth and focus · Per-scene geography and 180°
line · Rhythm. `fm:` derived_from the look bibles, SCREENPLAY, SCENES, camera canon.

## Validation rules
- No lens outside the lens set without a `style_break`.
- Every movement rule names its motivation.
- Every scene has continuity canon (time, weather, location) and a screen direction.

## Failure conditions
- A set footprint makes the required framing impossible → report with alternatives.

## Examples
"85mm is reserved for moments when Mara is watched by the city: compression
stacks rain and lights between us and her (serves intent.isolation). Never
used for her point of view."
