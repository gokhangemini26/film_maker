---
name: world-building
description: "Define the film's world - geography, era, architecture, culture, weather, rules and environmental storytelling - as a world bible plus checkable world canon. Used by the world-designer in WORLD_CHARACTERS."
user-invocable: false
---

# World building

## Purpose
Make the world specific and consistent enough that every scene, set and shot
agrees on what exists, when, and why — and so that the world itself serves the intents.

## When to use
WORLD_CHARACTERS phase (`/film-world`), and when a revision changes a location, era or rule.

## Required inputs
- Locked intent/tone/story canon; SCREENPLAY.md and SCENES.yaml (every location used).
- CREATIVE_DIRECTION (reference principles, originality statement).

## Process
1. Inventory: every location, time of day and weather the screenplay uses.
2. For each location: geography and scale, architecture and materials, age and
   wear, who uses it and when, sound of the place, what it says about the world.
3. World rules: era/technology level, economy of the place, what is normal
   here that would be strange to us (keep to what the film shows).
4. Environmental storytelling: 2–4 details per location that tell the story
   without dialogue, each tied to an intent.
5. Weather and light as world facts (e.g. "the harbour is always wet; sodium
   lights, no neon") — hand lighting *style* to the look-director.
6. Feasibility: what must be modelled for M3 vs what can stay in darkness,
   fog or out of focus. Prefer depth and silhouette over detail.
7. Propose canon: `world.era`, `world.rules.*`, `world.locations.<id>.*`
   (with `applies_to` scene ids), each DECISION with rationale + serves.

## Output format
`03_world/WORLD_BIBLE.md`: Overview · Rules · Locations (one section each:
description, scale, materials, wear, sound, storytelling details, scenes) ·
What the world never shows · Feasibility notes. `fm:` block derived_from
screenplay, scenes and the world canon.

## Validation rules
- Every location in SCENES.yaml is described and has canon.
- No rule contradicts story canon or the screenplay.
- Every DECISION has rationale and serves an intent.

## Failure conditions
- A location in the script is impossible to build at MVP fidelity → propose a
  staging alternative and flag it.
- Real-world places: describe the *kind* of place; do not reproduce identifiable
  private property or trademarks.

## Examples
`world.locations.harbour.state` — "Half-abandoned fishing harbour: one working
light in five, boats covered for the season." Rationale: "Scarcity of light
makes every lit window meaningful (serves intent.isolation); covered boats say
the town is waiting, not dead (serves intent.hope)."
