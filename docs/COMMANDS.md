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

Not yet available: `/film-blender`, `/film-render` (M3–M4), `/film-qa` (M4), `/film-export` (M6).
