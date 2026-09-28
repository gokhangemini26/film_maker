---
name: animation-design
description: "Plan per-shot character, object and camera animation - timing, spacing, anticipation, follow-through, arcs, weight, eyelines and body language - as shot animation blocks with rationale. Used by the animation-director in STORYBOARD (full animation bible in M6)."
user-invocable: false
---

# Animation design

## Purpose
Make motion carry meaning and avoid robotic interpolation: every action has
timing, weight and intention that fit the character and the shot's intent.

## When to use
- STORYBOARD (M2): fill each shot's `animation` block and `rationale.animation`.
- ANIMATION phase (M6): the full animation bible and animation canon.

## Required inputs
- Shot specs (creative_intent, characters, action, camera movement, duration).
- CHARACTER_BIBLE (movement, posture, arc), CINEMATOGRAPHY_BIBLE (movement grammar).

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

## Validation rules
- Timing fits `duration_s`; distance ÷ speed is plausible.
- No action contradicts character movement canon or the shot's intent.
- You do not change camera, composition or other fields (cinematographer's).

## Failure conditions
- The action cannot fit the duration → report to the orchestrator; do not change duration yourself.

## Examples
See Output format.
