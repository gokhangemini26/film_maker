---
name: story-development
description: "Build premise, theme, structure, character arc, stakes and ending for a short film with a beat-by-beat time budget. Used by the story-architect in the STORY phase."
user-invocable: false
---

# Story development

## Purpose
Give the film a story that serves the locked intents: a premise with a
personal stake, a structure that fits the running time, and an ending the
story earns.

## When to use
STORY phase (`/film-story`), and when a revision touches premise, arc or ending.

## Required inputs
- Locked `canon/intent.yaml`, `canon/tone.yaml`, `00_brief/CREATIVE_DIRECTION.md`.
- Brief duration (`duration_s`), characters and story idea.

## Process
1. **Premise**: who wants what, what stands in the way, what it costs. One sentence.
2. **Theme**: the question the film asks (not the answer).
3. **Size the story to the time.** Rough guide: 30–60 s ≈ one situation and one
   turn; 1–3 min ≈ setup, complication, turn, resolution; 3–10 min ≈ up to three
   sequences with a midpoint. Fewer ideas, fully felt, beats more ideas rushed.
4. **Beats**: list every beat with its purpose, the intent it serves, and a
   time budget in seconds. The total must match the brief duration ±10%.
5. **Character arc**: the protagonist's state at start and end, and the beat
   where it changes. In very short films a small shift (noticing, choosing) is enough.
6. **Ending**: must follow from the premise and pay the intent (check against
   `CREATIVE_DIRECTION`'s emotional arc). Name the image the film ends on.
7. **Production sanity**: count locations and characters; with proxy
   characters, favour silhouettes, posture and staging over facial acting.
8. Propose canon: `story.premise`, `story.theme`, `story.arc.<character>`,
   `story.ending` (DECISION, rationale, serves).

## Output format
- `01_story/STORY_BIBLE.md`: Premise · Theme · Characters in the story (role,
  want, need) · Stakes · Ending and final image · What the story deliberately leaves out.
- `01_story/STORY_STRUCTURE.md`: beat table
  `| # | Beat | Purpose | Serves | Seconds | Cumulative |` then total vs brief duration.
- `fm:` blocks: derived_from creative_direction + the story canon; serves the intents.

## Validation rules
- Beat seconds sum to the brief duration ±10%.
- Every beat serves at least one intent; every intent is served by at least one beat.
- Premise, arc and ending are in canon with rationale.
- No beat requires something the world or MVP cannot provide without flagging it.

## Failure conditions
- Duration unknown → ask (it decides the story's size).
- The intents pull in incompatible directions → report to the orchestrator for the creative-director.

## Examples
Beat row: `| 3 | The signal | Mara's phone lights with a message from her dead brother's number | intent.hope | 6 | 22 |`
Rationale for `story.ending`: "Ends on her answering, not on what he says:
the hope is the act of reaching back. Rejected: revealing the sender — it
turns an emotional ending into a plot twist."
