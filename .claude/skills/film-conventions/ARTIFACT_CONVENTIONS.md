# Artifact conventions

## Where things go

| Phase | Files | Owner |
|---|---|---|
| BRIEF | `00_brief/brief.yaml`, `00_brief/BRIEF_ANALYSIS.md` | creative-director |
| CREATIVE_DIRECTION | `00_brief/CREATIVE_DIRECTION.md` | creative-director |
| STORY | `01_story/STORY_BIBLE.md`, `01_story/STORY_STRUCTURE.md` | story-architect |
| SCREENPLAY | `02_screenplay/SCREENPLAY.md`, `02_screenplay/SCENES.yaml` | screenwriter |
| WORLD_CHARACTERS | `03_world/WORLD_BIBLE.md`, `03_world/ART_DIRECTION_BIBLE.md` | world-designer |
| WORLD_CHARACTERS | `04_characters/CHARACTER_BIBLE.md` | character-designer |
| LOOK | `05_look/VISUAL_BIBLE.md`, `COLOR_BIBLE.md`, `LIGHTING_BIBLE.md` | look-director |
| CINEMATOGRAPHY | `06_cinematography/CINEMATOGRAPHY_BIBLE.md` | cinematographer |
| STORYBOARD | `07_storyboard/STORYBOARD.md`, `SHOT_LIST.md`, `08_shots/*.shot.yaml` | cinematographer (+ animation-director for shot `animation` blocks) |
| every gate | `qa/reviews/G#_REVIEW.md` | qa-supervisor |

## The `fm:` block (Markdown)

```markdown
---
fm:
  id: story_bible              # lowercase slug, unique in the project
  kind: story_bible            # see the table of kinds in roles
  phase: STORY                 # the phase this belongs to
  status: PROPOSED             # always PROPOSED when you write it
  owner_role: story-architect
  derived_from:                # everything you actually used
    - ref: artifact:creative_direction
    - ref: canon:story.premise
  serves: [intent.isolation]   # intents this document serves
  summary: One line on what this document decides.
title: Story Bible
---
# Story Bible
...
```

YAML artifacts (`brief.yaml`, `SCENES.yaml`) put the same block under a
top-level `fm:` key.

Refs: `canon:<id>`, `artifact:<id>`, `shot:<SC01_SH010>`.

## Hashes and stamping

- Content = everything outside the `fm:` block. Editing it changes the hash.
- `fm stamp <file>` writes the current hash of each `derived_from` ref into your
  file. Always stamp after writing; stamp upstream files before downstream ones.
- If an upstream changes later, your file becomes **stale**. Fix it by
  revising the content and stamping again. `fm stamp` refuses to refresh hashes
  on unchanged content unless you pass `--note "why no revision is needed"` —
  use that only when it is genuinely true, and say so in your handoff.
- Shots also get their implicit dependencies stamped (intents served,
  characters' canon, continuity, scoped canon).

## Approved documents

After a gate is approved, its documents are the agreed version. Editing one
makes the gate DRIFTED: the human must re-approve it. Do this only when the
orchestrator asks you to revise, never incidentally.

## Useful read-only commands

```
fm status                       fm canon list [--domain look]
fm canon show <id>              fm deps <ref>
fm impact <ref>                 fm plan --scope <scope>
fm intent                       fm check continuity
fm validate -q
```
