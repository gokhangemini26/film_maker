---
name: storyboarding
description: "Break the screenplay into shots - storyboard, shot list and one machine-readable shot spec per shot with creative_intent and rationale. Used by the cinematographer in STORYBOARD."
user-invocable: false
---

# Storyboarding

## Purpose
Turn scenes into shots a Blender builder can construct and a human can judge:
what each shot is *for* (creative_intent) and why it is built that way (rationale).

## When to use
STORYBOARD phase (`/film-storyboard`); regenerating shots in a scope after revisions.

## Required inputs
- SCREENPLAY, SCENES.yaml, CINEMATOGRAPHY_BIBLE, camera + continuity canon,
  look canon (style lock), character canon (heights, wardrobe), ART_DIRECTION_BIBLE (sets, props).
- Template: `film-conventions/templates/shot.shot.yaml`.

## Process
1. For each scene, list shots in order. Ids `SC01_SH010, SC01_SH020...`
   (steps of 10 leave room for inserts).
2. For each shot decide, in this order: story purpose → emotional purpose →
   what the image must show → shot scale and lens → camera height and position
   → movement → subject position and blocking → lighting cues from the
   lighting bible → colour references (canon ids) → duration → transition.
3. Write `creative_intent` (all four fields) *before* camera values. If you
   cannot say what a shot is for, cut it.
4. Write `rationale` for camera, composition, lighting, movement, colour and
   blocking: choice + mechanism + rejected alternative.
5. Keep `environment` consistent with `continuity.<scene>` canon.
6. Positions in metres, Z up. Rough positions are fine in M2 (the M3 resolver refines them).
7. Timing: shot durations per scene should match SCENES.yaml estimates; the
   film total should match the brief (±15%, checked by `fm check continuity`).
8. Storyboard (text in M2): per shot, a precise description of the frame —
   layers front to back, where the subject sits, where the eye goes first,
   what moves. Image frames come later.
9. Leave `animation: {}` and `rationale.animation` for the animation-director.
10. Write every shot file, then SHOT_LIST.md and STORYBOARD.md, then stamp:
    shot list → shots → storyboard.

## Output format
- `08_shots/<id>.shot.yaml` — one per shot (template).
- `07_storyboard/SHOT_LIST.md` — table
  `| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |` + totals per scene and film.
- `07_storyboard/STORYBOARD.md` — per shot: frame description, eye path,
  movement, sound cue, transition; `derived_from` the shot list and SCREENPLAY.

## Validation rules
- Every scene has ≥ 1 shot; every shot's scene exists in SCENES.yaml.
- `creative_intent` fully filled; `rationale.camera` present (G5 requires it).
- Lenses from the lens set; style breaks carry a reason.
- `fm check continuity` has no FAIL; `fm intent` shows every intent on screen.

## Failure conditions
- A scene cannot be covered within its time budget → propose cuts, report.
- A shot needs something the MVP cannot build (crowd, close facial acting) →
  choose another staging and say why in the rationale.

## Examples
SC01_SH010 creative_intent.narrative_purpose: "Establish that the harbour is
empty and that she is alone in it." rationale.movement: "Locked-off: the
street does not care that she passes. Rejected: a tracking shot, which would
make the camera her companion."
