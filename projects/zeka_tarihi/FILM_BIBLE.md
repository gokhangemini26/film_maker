# FILM BIBLE — Biyolojiden Silikona: Zekanın Evrimi

The index of this film's source of truth. Prose bibles explain *why*;
`canon/*.yaml` holds the checkable decisions; `state.yaml` + `.fm/ledger.jsonl`
record what a human has approved. When they disagree, the ledger wins.

| Area | Prose | Canon | Locked at |
|---|---|---|---|
| Creative intent & tone | `00_brief/CREATIVE_DIRECTION.md` | `canon/intent.yaml`, `canon/tone.yaml` | G1 |
| Story | `01_story/STORY_BIBLE.md`, `01_story/STORY_STRUCTURE.md` | `canon/story.yaml` | G2 |
| Screenplay | `02_screenplay/SCREENPLAY.md` | — | G2 |
| World & production design | `03_world/WORLD_BIBLE.md`, `03_world/ART_DIRECTION_BIBLE.md` | `canon/world.yaml` | G3 |
| Characters | `04_characters/CHARACTER_BIBLE.md` | `canon/characters.yaml` | G3 |
| Look: visual, colour, lighting | `05_look/VISUAL_BIBLE.md`, `COLOR_BIBLE.md`, `LIGHTING_BIBLE.md` | `canon/look.yaml` | G4 (style lock) |
| Cinematography | `06_cinematography/CINEMATOGRAPHY_BIBLE.md` | `canon/camera.yaml` | G5 |
| Storyboard & shots | `07_storyboard/`, `08_shots/*.shot.yaml` | `canon/continuity.yaml` | G5 |
| Animation | `09_animation/ANIMATION_BIBLE.md` | `canon/animation.yaml` | G7 |
| Audio | `12_post/AUDIO_BIBLE.md` | `canon/audio.yaml` | G7 |

Changes to anything approved go through `fm change propose` → human decision.
See `CHANGELOG.md` (generated).
