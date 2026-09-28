# Agents

Specialist subagents live in `.claude/agents/`. The **main Claude Code session
is the Executive Producer**: it runs the `/film-*` commands, dispatches
specialists, runs `fm`, and stops at every gate. Specialists do not have the
`Agent` tool, so they cannot spawn other agents; all coordination goes
through the main session.

Every specialist preloads the `film-conventions` skill (shared rules) plus its
domain skills, writes only `PROPOSED` work in the paths it owns, stamps and
validates it with `fm`, and ends with a fixed **Handoff** (files written, canon
proposed with the intents it serves, assumptions, open questions, conflicts,
validation result, limits).

## Roster (M2)

| Agent | Phase | Writes | Canon domains | Skills |
|---|---|---|---|---|
| creative-director | BRIEF, CREATIVE_DIRECTION | BRIEF_ANALYSIS.md, brief statuses, CREATIVE_DIRECTION.md | intent, tone | film-development |
| story-architect | STORY | STORY_BIBLE.md, STORY_STRUCTURE.md | story | story-development |
| screenwriter | SCREENPLAY | SCREENPLAY.md, SCENES.yaml | — | screenwriting |
| world-designer | WORLD_CHARACTERS | WORLD_BIBLE.md, ART_DIRECTION_BIBLE.md | world | world-building, production-design |
| character-designer | WORLD_CHARACTERS | CHARACTER_BIBLE.md | characters | character-design |
| look-director | LOOK | VISUAL/COLOR/LIGHTING_BIBLE.md | look (style lock at G4) | visual-development, color-design, lighting-design |
| cinematographer | CINEMATOGRAPHY, STORYBOARD | CINEMATOGRAPHY_BIBLE.md, STORYBOARD.md, SHOT_LIST.md, shot specs | camera, continuity | cinematography, storyboarding |
| animation-director | STORYBOARD | each shot's `animation` block + `rationale.animation` | (animation, from M6) | animation-design |
| qa-supervisor | every gate | `qa/reviews/G#_REVIEW.md` only | — | creative-review, continuity-check |

Later: **blender-td** (M3: resolver, scene builders, renders) and
**post-supervisor** (M6: edit plan, audio bible, animatic).

## What no agent can do

Enforced by `fm` (human-only actions refuse non-human or non-interactive
callers) and, as a second layer, by deny rules in `.claude/settings.json`:

- approve, revise or reject a gate; approve, lock or reject canon; decide a
  change request; authorize a final render; use `--sandbox-confirm`
- edit `state.yaml`, `STATUS.md`, `CHANGELOG.md`, `.fm/`, `changes/`
- set `FM_ACTOR`

The deny rules are defence in depth. The authoritative guard is `fm` itself:
in a production project a human decision needs a person typing the
confirmation in an interactive terminal.

## The review is separate

The qa-supervisor reviews work it did not produce. Its verdict (PASS / WARN /
FAIL) is shown to you at approval but is **advisory**: it can neither block
nor pass a gate. Its review must list every item the gate approves; if any of
them changes afterwards, the review goes stale and approval is refused until
it is redone.

## Models

`config/models.yaml` maps each role to a model class (creative / technical /
vision). Agent files carry the matching `model:`; a test keeps them in sync.
The artifacts agents produce follow the schemas in `schemas/json/`, so any
other model, tool or person could produce them instead.
