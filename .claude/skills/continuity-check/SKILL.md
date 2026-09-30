---
name: continuity-check
description: "Check continuity across documents and shots - wardrobe, props, positions, time, weather, location, screen direction and narrative continuity - combining fm check continuity with judgement. Used by the qa-supervisor."
user-invocable: false
---

# Continuity check

## Purpose
Catch contradictions between shots and canon before anything is built:
what `fm` can check mechanically, plus what needs a trained eye.

## When to use
Every G5 review; `/film-continuity` at any time; after any revision that touches
characters, world, continuity canon or shots.

## Required inputs
- `fm check continuity` output, `fm intent`, `fm validate -q`.
- Canon: characters (wardrobe, proportions), continuity, world, camera; SCENES.yaml;
  all shot specs; STORYBOARD.md.

## Process
1. Run `fm check continuity`. Every FAIL goes into the report verbatim with its shot.
2. Wardrobe and props: for each character per scene, the items worn/carried in
   each shot vs character canon (`applies_to` scene variants included). Props that
   appear, disappear or move between consecutive shots without an action causing it.
3. Positions and geography: characters' positions and travel direction across
   consecutive shots; the 180° line per scene (camera canon); eyelines matching
   between shot/reverse-shot.
4. Time and weather: consistent within a scene; changes between scenes
   explained by the screenplay.
5. Lighting continuity: the key source and direction do not jump between shots
   of the same scene unless motivated.
6. Narrative continuity: what the audience knows at each shot matches the
   screenplay order (no information shown before it is set up).
7. **Prop-state continuity across shots (M6, ANIMATION and after).** Walk `09_animation/*.anim.yaml` in film order
   (scene, then shot). For each persistent prop (doors, lids, carried objects and their `loc` / `attach`, headphones,
   lights) the state at the end of shot N must equal the state at the start of shot N+1, and each change must follow
   an allowed transition in the vocabulary (a lid cannot go `open_down` to `open_down`). Screen and battery state
   must match the continuity canon. `fm qa motion` and `fm check anim` do this mechanically once they exist (M6
   steps D1 and A1); you add judgement on props the vocabulary does not track and on cuts where a change happens off-screen.
8. Classify: FAIL (contradiction with canon or impossible), WARN (likely
   jarring, needs a decision), PASS.

## Output format
A "Continuity" section in the gate review (or a standalone review body for
`/film-continuity`):
`| shot(s) | aspect | level | evidence | issue | suggested fix | owner |`
where owner is the agent whose file should change (prop-state problems: the animation-director).

## Validation rules
- Every FAIL cites a shot id and a canon id or document section.
- Suggested fixes respect locked canon (fix the shot, or propose a change request — never both silently).

## Failure conditions
- Shots are missing environment or character data needed to check → WARN "uncheckable", list the fields.

## Examples
`| SC04_SH030→SH040 | prop state | FAIL | anim_SC04_SH030 end: glovebox_lid closed; anim_SC04_SH040 f0: glovebox_lid open_down | lid changes state across the cut with no action | start SH040 with the lid closed and lower it on the latch event | animation-director |`
`| SC01_SH020→SH030 | screen direction | FAIL | camera.screen_direction.sc01 = left_to_right | Mara exits frame left in SH020 and enters from left in SH030 | flip SH030 entry to screen right | cinematographer |`
