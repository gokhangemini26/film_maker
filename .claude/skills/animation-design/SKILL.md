---
name: animation-design
description: "Plan per-shot character, object and camera animation - timing, spacing, anticipation, follow-through, arcs, weight, eyelines and body language - as shot animation blocks with rationale. Used by the animation-director in STORYBOARD (prose blocks) and ANIMATION (M6: structured anim files, vocabulary, events)."
user-invocable: false
---

# Animation design

## Purpose
Make motion carry meaning and avoid robotic interpolation: every action has
timing, weight and intention that fit the character and the shot's intent.

## When to use
- STORYBOARD (M2): fill each shot's `animation` block and `rationale.animation`.
- ANIMATION phase (M6): the animation vocabulary canon, one structured `09_animation/<shot_id>.anim.yaml` per shot,
  and the short ANIMATION_BIBLE. `/film-animate`.

## Required inputs
- Shot specs (creative_intent, characters, action, camera movement, duration).
- CHARACTER_BIBLE (movement, posture, arc), CINEMATOGRAPHY_BIBLE (movement grammar).
- ANIMATION (M6): the resolved shot table (frame counts), `canon/animation.yaml` vocabulary once proposed, and the
  shot's prose `animation` block as the brief.

## Process
1. Read the shot's creative_intent and the character's movement canon.
2. Break each character action into key poses with timing in seconds from
   shot start (anticipation → action → follow-through → settle).
3. Spacing and easing: where the motion accelerates/decelerates; name the
   curve intent (ease-in, hold, overshoot) rather than raw keyframes.
4. Weight and arcs: what shows weight (heel strike, head bob, lean into wind);
   motion follows arcs, not straight lines.
5. Secondary motion: coat/bag/hood lag, rain on shoulders — only what the MVP
   proxy can plausibly show; mark anything that needs simulation as M3+ risk.
6. Eyelines: where the character looks and when the look changes.
7. Camera animation: start/end timing and easing consistent with `camera.movement`.
8. Walk/move speeds in m/s (walk ≈ 1.2–1.5, tired walk ≈ 0.8–1.0) and check
   that distance ÷ speed fits the shot duration.
9. Write `rationale.animation`: how the motion serves the intent.

### ANIMATION phase (M6): structured anim files
10. Vocabulary first. Collect the prose poses, props and eyelines of all shots and propose `animation.vocab.*` canon
    (pose presets grouped by stance family, face refs from character canon, gaits, ease enum, prop state enums with
    allowed transitions, eyeline targets), each with a rationale. Reuse a name rather than minting a near-duplicate.
    The human ratifies the vocabulary at G7.
11. One file per shot, `09_animation/<shot_id>.anim.yaml`, with an `fm:` block (`derived_from`: the shot, the
    characters' canon, the vocabulary). Frames are shot-local integers `0..frames-1`, strictly increasing per track.
    Tracks: per character `pose` / `move` (`gait`, and `path` if and only if a gait) / `face` / `look` / `breath`;
    `props` state tracks; `camera`; `events`.
12. Holds are explicit: `ease: hold`, including the final hold. Hold lengths obey the shot's notes (for example
    `min_hold_f` on insert shots the audience must read).
13. `events`: a named sync point (`id`, `f`, `kind` sound | light | state) for every frame-exact sync the shot's
    `sound_sync` text or the storyboard implies. The sound-designer cues by event id, so keep ids stable.
14. **No prose parsing at build time.** Every `ref`, `state`, `loc`, `target` and `gait` is a vocabulary name. The old
    prose `animation` block stays as the human-readable brief and is never read by builders once a shot has `motion`.
    Free text goes only in `notes`, which nothing parses.
15. Prop-state continuity: the state at the end of shot N is the state at the start of shot N+1 for persistent props
    (doors, lids, carried objects, headphones, lights). Walk the shots in film order before you hand back.
16. `fm stamp` each anim file, then `fm validate -q`; run `fm check anim` and `fm qa motion` when they exist
    (M6 steps A1, D1); if `fm` reports an unknown command, say so in the handoff.

## Output format
In each `08_shots/<id>.shot.yaml`:

```yaml
animation:
  characters:
    mara:
      locomotion: {type: walk, speed_mps: 0.9, path: "x 3 -> -3 along y 0"}
      keys:
        - {t: 0.0, pose: walking head down}
        - {t: 2.4, pose: phone buzz - shoulders tighten, no stop}
        - {t: 4.5, pose: exits frame left}
      secondary: [hood lags head turns, bag swings against hip]
      eyeline: ground ahead; never toward the phone
  camera: {easing: none, notes: locked-off}
rationale:
  animation: She keeps walking through the buzz - the refusal to look is the character beat.
```

Edit only `animation` and `rationale.animation`; then `fm stamp` the shot.

ANIMATION phase (M6), `09_animation/SC04_SH040.anim.yaml` (abridged):

```yaml
fm: {id: anim_SC04_SH040, kind: shot_animation, phase: ANIMATION, status: PROPOSED, owner_role: animation-director}
shot_id: SC04_SH040
frames: 60                      # equals the resolved shot's frame count
vocab_version: 1
characters:
  ren:
    pose:
      - {f: 0,  ref: kerb_sit_phone_left, ease: hold}
      - {f: 24, ref: lunge_glovebox_latch, ease: ease_in_out, blend_f: 6}
      - {f: 54, ref: kerb_sit_crank_lap, ease: hold}
    look: [{f: 0, target: glovebox}, {f: 37, target: crank_charger}]
props:
  glovebox_lid: [{f: 24, state: open_down, ease: hand_lower, dur_f: 6}]
events:
  - {f: 24, id: lid_latch, kind: sound}
notes: []                       # humans only, never parsed
```

The names above are examples; the real ones live in `canon/animation.yaml`.

## Validation rules
- Timing fits `duration_s`; distance ÷ speed is plausible.
- Anim files (M6): every name is in the vocabulary; `frames` matches the resolved count; keys inside `0..frames-1`;
  `blend_f` does not run past the next key; event ids unique per shot; prop states chain across shots.
- No action contradicts character movement canon or the shot's intent.
- You do not change camera, composition or other fields (cinematographer's).

## Failure conditions
- The action cannot fit the duration → report to the orchestrator; do not change duration yourself.
- A needed pose, state or target is not in the vocabulary → propose it as canon with a rationale; never write it as free text.
- Prose in the shot contradicts itself or another shot (for example whether a lid is "lowered" or "open") → list it as a
  conflict for the human; do not pick silently.
- An anim file is stale after its shot changed → revise it and restamp; never stamp to silence staleness.

## Examples
See Output format.
