# `/film-*` commands

Run inside Claude Code opened at the repository root. Each phase command
follows the same procedure (skill `project-management`, section A):

1. `fm status` — the project must be in the right phase
2. dispatch the owning agent(s)
3. `fm stamp` everything written, `fm validate`
4. `fm intent` (and `fm check continuity` at STORYBOARD)
5. qa-supervisor writes the gate review
6. `fm submit` — then **stop** and tell you the exact command to decide

Gate decisions are always yours, typed in your own terminal:
`fm approve G#`, `fm revise G# --notes "..."`, `fm reject G# --notes "..."`.

| Command | Phase | Agents | Ends at |
|---|---|---|---|
| `/film-new <slug> <idea...>` | IDEA → BRIEF | creative-director (brief analysis) + up to 5 questions for you | CREATIVE_DIRECTION |
| `/film-direction` | CREATIVE_DIRECTION | creative-director → qa-supervisor | **G1** |
| `/film-story` | STORY | story-architect | advance to SCREENPLAY |
| `/film-script` | SCREENPLAY | screenwriter → qa-supervisor | **G2** |
| `/film-world` | WORLD_CHARACTERS | world-designer → character-designer → qa-supervisor | **G3** |
| `/film-look` | LOOK | look-director → qa-supervisor | **G4** (style lock) |
| `/film-cinematography` | CINEMATOGRAPHY | cinematographer | advance to STORYBOARD |
| `/film-storyboard` | STORYBOARD | cinematographer → animation-director → qa-supervisor | **G5** |
| `/film-blender [shots]` | ASSET_PREP → PREVIEW | blender-td | previews + per-shot report (G6 is yours) |
| `/film-animate [scope]` | ANIMATION (M6) | animation-director → blender-td | frames + checks; advance to ANIMATION_PREVIEW |
| `/film-playblast [scope]` | ANIMATION_PREVIEW (M6) | blender-td | frames, playblast, motion QA, contact strips (report) |
| `/film-audio` | ANIMATION_PREVIEW (M6) | sound-designer | audio canon, bible, cue sheet, asks list (report) |
| `/film-post` | ANIMATION_PREVIEW (M6) | post-supervisor → qa-supervisor | **G7** |
| `/film-final [scope]` | FINAL_RENDER (M6) | blender-td → qa-supervisor | **G8** (needs your final-render authorization first) |
| `/film-export` | POST (M6) | post-supervisor | delivery report |
| `/film-next` | whatever is next | — | runs the right command above |
| `/film-status` | any | — | plain-language status + next step |
| `/film-review` | any | qa-supervisor | review written, nothing submitted |
| `/film-continuity [scope]` | any | qa-supervisor | findings only, nothing written |
| `/film-revise "<feedback>"` | any | owners of affected work | change requests / regenerated work |

All commands accept an optional project slug as the first argument and pass
any further text to the agents as your notes, e.g.
`/film-look last_signal keep the palette almost monochrome`.

## Revising

`/film-revise "Change Mara's jacket to dark brown"`:

1. finds the affected canon and runs `fm impact` — you see the blast radius first
2. unapproved work → the owner revises it
3. approved/locked canon → the owner writes `fm change propose ...` with a new
   rationale; **you** run `fm change approve CHANGE-NNN`
4. `fm plan --scope ...` → only stale items are regenerated, by their owners
5. affected reviews are redone; you re-approve the drifted gates

## Feedback loop (M5)

Files only, under `qa/feedback/FB-###.yaml` (no ledger line: the ledger has no
non-approval record action, and `fm record` writes derived-product JSON only).

```
fm feedback add shot:SC04_SH050 --note "head out of frame" [--severity low|medium|high|blocker] [--owner ROLE]
fm feedback list [--open]
fm feedback plan FB-001        # owner + command, change request needed?, minimal stale set (fm plan/impact)
fm feedback resolve FB-001 --by "reframed, restamped" [--force-stale]   # agents allowed; actor recorded
fm qa review-status [--file qa/reviews/PREVIEW_REVIEW.md] [--json]      # PASS/WARN/FAIL counts + stale vs project
```

Owner routing (first keyword in the note wins, then the canon domain, then
`cinematographer` for shots): camera/framing -> cinematographer; motion ->
animation-director; colour/ui/lighting -> look-director; figure/character ->
character-designer; world/set/car/prop -> world-designer; builder/blender/proxy
-> blender-td. `/film-revise` remains the way to act on a plan.

## M6 commands (in progress)

`/film-animate`, `/film-playblast`, `/film-audio`, `/film-post`, `/film-final` and
`/film-export` are defined, but the tools they call land incrementally, so each
command states which `fm` subcommands may not exist yet and reports the
missing ones instead of pretending they ran:

| Tool | Lands in M6 step |
|---|---|
| `fm check anim`, `ANIM_*` validation | A1 |
| resolver `motion` block | A3 |
| `fm blender frames`, `fm blender playblast` | C4 |
| `fm qa motion` tier 0 | D1 |
| `fm qa motion` tier 1 (bake report) | D2 |
| `fm audio synth` | E2 |
| `fm audio mix`, `fm qa audio` | E5 |
| `fm post edl`, `fm post animatic` | F2 |
| `fm blender final` | F3 |
| `fm post assemble|export`, `fm qa delivery` | F4 |

The steps are the task ids in [M6_SCOPE.md](M6_SCOPE.md) section 6.
The core enforces what each command must leave behind (files, per-shot anim files, QA reports
with no FAIL): see the M6 table in [WORKFLOW.md](WORKFLOW.md). G7 is "Animation, audio and post
plan"; POST has no gate in this cut, so `fm advance` out of POST checks the delivery report.
Approving G7 does not authorize the final render: `/film-final` needs your own
`fm authorize final-render` first, typed in your terminal. Agents cannot run it.

Not yet available: `/film-render` (M3–M4), `/film-qa` (M4).
