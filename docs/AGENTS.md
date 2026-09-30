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

## Roster (12 agents, one file each in `.claude/agents/`)

| Agent | Phase | Writes | Canon domains | Skills |
|---|---|---|---|---|
| creative-director | BRIEF, CREATIVE_DIRECTION | BRIEF_ANALYSIS.md, brief statuses, CREATIVE_DIRECTION.md | intent, tone | film-development |
| story-architect | STORY | STORY_BIBLE.md, STORY_STRUCTURE.md | story | story-development |
| screenwriter | SCREENPLAY | SCREENPLAY.md, SCENES.yaml | — | screenwriting |
| world-designer | WORLD_CHARACTERS | WORLD_BIBLE.md, ART_DIRECTION_BIBLE.md | world | world-building, production-design |
| character-designer | WORLD_CHARACTERS | CHARACTER_BIBLE.md | characters | character-design |
| look-director | LOOK | VISUAL/COLOR/LIGHTING_BIBLE.md | look (style lock at G4) | visual-development, color-design, lighting-design |
| cinematographer | CINEMATOGRAPHY, STORYBOARD | CINEMATOGRAPHY_BIBLE.md, STORYBOARD.md, SHOT_LIST.md, shot specs | camera, continuity | cinematography, storyboarding |
| blender-td | ASSET_PREP, BLENDER_BUILD, PREVIEW; M6: ANIMATION_PREVIEW, FINAL_RENDER | runs `fm resolve` / `fm blender preview`, reads stills, reports builder vs spec problems; M6: `fm blender frames|playblast|final`, `fm qa motion`; builder code in `blender/` | (none) | blender-production |
| animation-director | STORYBOARD; M6: ANIMATION | STORYBOARD: each shot's `animation` block + `rationale.animation`. M6: `09_animation/<shot>.anim.yaml`, ANIMATION_BIBLE.md; never edits shot files once a shot has an anim file | animation (vocabulary, locked at G7) | animation-design |
| sound-designer | ANIMATION_PREVIEW (M6) | `audio.*` canon proposals, `12_post/AUDIO_BIBLE.md`, `AUDIO_CUES.yaml`, synthesis recipes, the asks list for the human | audio (locked at G7) | sound-design |
| post-supervisor | ANIMATION_PREVIEW, POST (M6) | `12_post/EDIT_PLAN.md`, `POST_PLAN.md`; runs `fm post *` and `fm qa delivery` | (none by default) | post-production |
| qa-supervisor | every gate (G1-G8) | `qa/reviews/G#_REVIEW.md` only | — | creative-review, continuity-check |

Every file in `.claude/agents/` has a row above (creative-director,
story-architect, screenwriter, world-designer, character-designer,
look-director, cinematographer, animation-director, blender-td,
qa-supervisor, sound-designer, post-supervisor).

**M6 in progress.** The sound-designer and post-supervisor are defined, and
the animation-director, blender-td and qa-supervisor are extended, but the
`fm` subcommands and builders they call (`fm audio`, `fm post`, `fm qa
motion|audio|delivery`, `fm check anim`, `fm blender frames|playblast|final`)
land incrementally (see [M6_SCOPE.md](M6_SCOPE.md)). Agents report an unknown
subcommand instead of pretending it ran. Model classes: sound-designer and
post-supervisor are `creative`, like the animation-director.
No M6 agent can authorize a final render or approve a gate; that stays yours.

Which command dispatches whom is in [COMMANDS.md](COMMANDS.md); the step-by-step
use of all of them for a new film is in
[NEW_FILM_WALKTHROUGH.md](NEW_FILM_WALKTHROUGH.md).

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

## Feedback is not a decision

`fm feedback add|list|plan|resolve` (M5) turns a review finding into a scoped
fix. Agents may run all four: `add` routes a suggested owner, `plan` reuses
`fm plan`/`fm impact` and says whether a change request is needed (locked
canon still needs `fm change propose`, decided by you), and `resolve` records
the acting agent and refuses while the plan's nodes are stale (`--force-stale`
overrides and is recorded). Resolving never approves anything.

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
