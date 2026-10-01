---
name: character-design
description: "Define characters' identity, appearance, proportions, wardrobe, movement and representation as a character bible and continuity-grade canon. Used by the character-designer in WORLD_CHARACTERS."
user-invocable: false
---

# Character design

## Purpose
Make each character specific, consistent and producible. Character continuity
is a hard constraint: whatever is locked here must look the same in every shot.

## When to use
WORLD_CHARACTERS phase (`/film-world`), wardrobe/appearance revisions.

## Required inputs
- Story canon (arcs), SCREENPLAY.md, SCENES.yaml (who appears where).
- CREATIVE_DIRECTION, world canon (era, climate, economy).

## Process
1. Identity: name, age, role in the story, want/need, one defining behaviour.
2. Silhouette first: with proxy characters the silhouette carries identity —
   height, build, posture, one distinctive shape (hood, bag, coat length).
3. Proportions: height in metres and build; these drive the proxy in M3.
4. Wardrobe per scene: items, colour (`#RRGGBB`, coordinate with the look
   palette — propose, the look-director may request changes), material, wear,
   and any change between scenes (and why).
5. Movement: pace, posture, gesture vocabulary; how it changes with the arc.
6. Face and hands: only what the film will actually show at MVP fidelity.
7. Representation (for M3+): `characters.<id>.representation` with
   `value: {provider: proxy, height_m, build, silhouette_features}` and a
   rationale. Future providers (MPFB, VRM, generated, mocap) plug in by
   changing this entry through a change request — design the description so it
   stays valid for them.
8. Continuity table: what must never change unless the story says so.

## Output format
`04_characters/CHARACTER_BIBLE.md`: per character — Identity · Silhouette ·
Proportions · Wardrobe by scene · Movement · Arc in body language ·
Continuity rules. Canon: `characters.<id>.identity`, `.proportions`,
`.silhouette`, `.wardrobe.<item>`, `.movement`, `.representation`
(DECISION + rationale + serves; wardrobe entries may use `applies_to` scene ids).

## Validation rules
- Every character in SCENES.yaml has identity, proportions, wardrobe and representation canon.
- Wardrobe colours are hex; items are consistent across scenes unless `applies_to` says otherwise.
- Nothing resembles a real person or a copyrighted character.

## Failure conditions
- The script requires facial performance the MVP proxy cannot carry → propose
  staging (back view, silhouette, hands, sound) and flag it for the cinematographer.

## Examples
`characters.mara.silhouette` — "Tall, narrow, hood always up; long coat to the
knee, one shoulder bag." Rationale: "Readable at 20 m in rain and low light,
where faces are not; the bag gives her a job before we know it."
