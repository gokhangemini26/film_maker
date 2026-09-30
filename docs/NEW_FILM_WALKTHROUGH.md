# New film walkthrough

From `/film-new` to the first Blender preview and gate G6. It assumes you have
done [GETTING_STARTED.md](GETTING_STARTED.md). The reference run is
`projects/last_signal`: open its files next to yours whenever you want to see
what a finished phase looks like.

## How every phase works

```
you: /film-<phase>  ->  agent writes PROPOSED files  ->  fm stamp + fm validate
  ->  fm intent (and fm check continuity at STORYBOARD)  ->  qa-supervisor writes qa/reviews/G#_REVIEW.md
  ->  fm submit  ->  Claude STOPS and prints the exact command
you: read, look, then decide in YOUR OWN terminal:
     fm -p <film> approve G#   |   fm -p <film> revise G# --notes '...'   |   fm -p <film> reject G# --notes '...'
you: /film-next  ->  fm advance and the next phase
```

Rules that never bend:

- Agents write `status: PROPOSED`. Only your typed `fm approve` turns work into
  approved, locked canon. Claude cannot run `approve`, `revise`, `reject`,
  `amend`, `authorize`, `canon approve|lock|reject` or `change approve|reject`
  (blocked in `.claude/settings.json` and refused by `fm`).
- Claude never continues past a gate in the same turn.
- The QA verdict (PASS / WARN / FAIL) is advice. WARN or FAIL needs
  `--ack-review` when you approve; it is recorded and listed as "carried
  forward" in `STATUS.md` so later phases resolve it. Use `--notes '...'` to
  record your answers to the review's open questions (otherwise they live only
  in documents).
- Approving takes a person typing the gate id (`Type 'G3' to confirm:`).
- In PowerShell, put notes in **single quotes** (see
  [TROUBLESHOOTING.md](TROUBLESHOOTING.md)).
- When several projects exist, add `-p <film>` before the command.

Replace `my_film` below with your slug. Commands starting with `/` are typed
in Claude Code; commands starting with `fm` are shell commands (Claude can run
the non-human ones; the human ones you type yourself).

---

## Phase 0 - Brief (no gate of its own)

| | |
|---|---|
| Command | `/film-new my_film <your idea, genre, duration, taste, references, characters, era, style...>` |
| Agent | creative-director (brief analysis) |
| Artifacts | `projects/my_film/00_brief/brief.yaml` (each field `given` / `assumed` / `unknown`), `00_brief/BRIEF_ANALYSIS.md`, `canon/intent.yaml` (your must-haves as `USER_REQUIREMENT` intents) |
| What it does | `fm init my_film --title "..."`, `fm advance` to BRIEF, brief analysis, up to five questions to you (unanswered ones take the default and stay `ASSUMPTION`), then `fm advance` to CREATIVE_DIRECTION |
| Gate | none here; **G1** covers the brief and the direction together |
| Look at | `canon/intent.yaml`: are the intents your words? An intent is an effect on the audience, not a technique. `brief.yaml`: anything marked `assumed` that you disagree with. Say so now: it is cheap |
| Decision | none. Correct things by telling Claude, or edit before the direction is written |

Give the brief as much taste as you can (references, colours, mood, camera and
lighting feel, duration). Vague briefs produce assumptions, and assumptions get
locked at the gates.

## Phase 1 - Creative direction -> G1

| | |
|---|---|
| Command | `/film-direction my_film [notes]` |
| Agent | creative-director, then qa-supervisor |
| Artifacts | `00_brief/CREATIVE_DIRECTION.md` (intents, tone, reference principles, originality statement), `canon/tone.yaml`, `qa/reviews/G1_REVIEW.md` |
| Gate | **G1 Creative direction**. Approves BRIEF and CREATIVE_DIRECTION; locks canon domains `intent`, `tone` |
| Look at | the review verdict and its top findings; whether every intent is served (`fm -p my_film intent`); the originality statement: references must be used as principles, not copied; tone decisions each have a rationale |
| Approve | `fm -p my_film approve G1` (add `--ack-review` for WARN/FAIL, `--notes '...'` for your answers) |
| Send back | `fm -p my_film revise G1 --notes 'the ending must stay open'` then `/film-direction my_film` again |
| Rethink | `fm -p my_film reject G1 --notes '...'` |

Last Signal used two G1 rounds (a revise, then an approve): that is normal.

## Phase 2 - Story (no gate)

| | |
|---|---|
| Command | `/film-story my_film` (or `/film-next`, which runs `fm advance` first) |
| Agent | story-architect |
| Artifacts | `01_story/STORY_BIBLE.md`, `01_story/STORY_STRUCTURE.md` (beats with a time budget), `canon/story.yaml` |
| Gate | none; **G2** covers story and screenplay together |
| Look at | the beat time budget against the brief duration; whether the ending is earned; theme and stakes still match your intents |

## Phase 3 - Screenplay -> G2

| | |
|---|---|
| Command | `/film-script my_film` |
| Agent | screenwriter, then qa-supervisor |
| Artifacts | `02_screenplay/SCREENPLAY.md` (Fountain-compatible), `02_screenplay/SCENES.yaml` (machine-readable scene index: scene ids `SC01...`, headings, characters, location, weather, est. duration), `qa/reviews/G2_REVIEW.md` |
| Gate | **G2 Story and screenplay**. Locks `story` |
| Look at | read the screenplay as a film: does every scene do work? Does `SCENES.yaml` total the running time? Do headings in the index match the screenplay exactly? Unresolved `UNKNOWN`s in the review (for example wording of an on-screen message): decide them now, in `--notes` |
| Approve | `fm -p my_film approve G2` |

## Phase 4 - World and characters -> G3

| | |
|---|---|
| Command | `/film-world my_film` |
| Agents | world-designer, character-designer, then qa-supervisor |
| Artifacts | `03_world/WORLD_BIBLE.md`, `03_world/ART_DIRECTION_BIBLE.md`, `04_characters/CHARACTER_BIBLE.md`, `canon/world.yaml`, `canon/characters.yaml` (set dimensions, proportions, wardrobe, props), `qa/reviews/G3_REVIEW.md` |
| Gate | **G3 World and characters**. Locks `world`, `characters` |
| Look at | wardrobe, colours, ages, heights, prop inventory: these become checkable canon that every shot is tested against. Set dimensions and character `proportions` also drive the Blender proxy figures and sets later, so numbers should be sensible |
| Approve | `fm -p my_film approve G3` |

## Phase 5 - Look -> G4 (the style lock)

| | |
|---|---|
| Command | `/film-look my_film [notes]` |
| Agents | look-director, then qa-supervisor |
| Artifacts | `05_look/VISUAL_BIBLE.md`, `COLOR_BIBLE.md`, `LIGHTING_BIBLE.md`, `canon/look.yaml` (hex palettes, per-scene palettes, lighting rules), `qa/reviews/G4_REVIEW.md` |
| Gate | **G4 Visual direction (style lock)**. Locks `look` |
| Look at | the palette as actual hex swatches; how colour moves across scenes (the emotional progression); the lighting rules; contrast between accent colours and backgrounds if the film has readable UI or props. After G4 a shot that breaks the look needs an explicit `style_break` reason |
| Approve | `fm -p my_film approve G4` |

G4 is the most expensive one to change later: colour and lighting changes
ripple through every shot and every render. Take your time here.

## Phase 6 - Cinematography (no gate)

| | |
|---|---|
| Command | `/film-cinematography my_film` |
| Agent | cinematographer |
| Artifacts | `06_cinematography/CINEMATOGRAPHY_BIBLE.md` (lens set, camera heights, movement, framing, depth, screen direction), `canon/camera.yaml` |
| Gate | none; **G5** covers it |
| Look at | every lens/height/movement choice has a reason and a rejected alternative |

## Phase 7 - Storyboard and shots -> G5

| | |
|---|---|
| Command | `/film-storyboard my_film` |
| Agents | cinematographer (continuity canon, `STORYBOARD.md`, `SHOT_LIST.md`, one `08_shots/<scene>_<shot>.shot.yaml` per shot), animation-director (each shot's `animation` block), then qa-supervisor |
| Artifacts | `canon/continuity.yaml`, `07_storyboard/STORYBOARD.md`, `07_storyboard/SHOT_LIST.md`, `08_shots/*.shot.yaml`, `qa/reviews/G5_REVIEW.md` |
| Checks | `fm -p my_film check continuity` must have no FAIL (a FAIL blocks submit); `fm -p my_film intent` |
| Gate | **G5 Storyboard and shots**. Approves every shot; locks `camera`, `continuity` |
| Look at | the shot list against the running time; every shot has `creative_intent` and `rationale` (required at approval); screen direction and eyelines across cuts; the continuity check output; the review's WARNs |
| Approve | `fm -p my_film approve G5` |

Everything upstream of this point is text. The next phase is the first time
you see pictures.

## Phase 8 - Preview -> G6

| | |
|---|---|
| Advance | after G5: `fm -p my_film advance` three times (ASSET_PREP, BLENDER_BUILD, PREVIEW). It is not a human-only command, and `/film-next` does not cover these phases |
| Command | `/film-blender my_film [shot ids]` |
| Agent | blender-td |
| Commands it runs | `fm -p my_film resolve` (shots + canon -> `09_resolved/*.json`, deterministic), then `fm -p my_film blender preview` (pinned Blender, one process per shot, one still per shot into `10_blender/previews/`, each recorded as `render:preview_<shot>`); then `fm -p my_film qa stills` (deterministic checks; needs Pillow) |
| Artifacts | `09_resolved/`, `10_blender/previews/*.png`, `qa/stills_report.json`, a per-shot report (OK / builder problem / spec problem, with the owner), optionally `qa/reviews/PREVIEW_REVIEW.md` |
| Gate | **G6 First Blender preview**. Locks no canon domain |
| Evidence rule | only stills made with the **pinned Blender 5.2.x** count. `--draft` stills (cloud `bpy`) are for iteration; their records say "draft" |
| Look at | open every still and the contact sheet: is the subject in frame, is the camera inside geometry, do colours match the palette, does lighting match the shot, are the props and screens the spec promises present, does screen direction hold? If a `PREVIEW_REVIEW.md` exists, `fm -p my_film qa review-status` shows its PASS/WARN/FAIL counts and whether it is stale (see the note under "Review findings") |
| Submit | `fm -p my_film submit`, then `fm -p my_film approve G6` |

Long renders: the tool call in Claude Code times out after about two minutes.
Run the full preview in your own terminal window, or in the background (see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md)), then let Claude read the results.

### Know the limits before you promise a look

- The Blender builders in `blender/fm_blender/` currently build **Last Signal's
  sets by name** (`world.sets.street`, `ren_car`, `corner_shop`, `hana_room`).
  A film whose canon does not define those gets the **generic stage** (a ground
  plane and a backdrop) plus proxy figures built from
  `characters.*.proportions`, camera, lighting and palette from your canon.
  That is enough to check framing, colour, lighting and continuity. Sets that
  look like *your* world need new or extended builders: that is builder code
  (blender-td's job in `blender/`), not creative content, and it is the main
  piece of work for a second film beyond running this walkthrough.
- Characters are static proxy figures. Animation, final render, post and delivery
  (M6 and later) are not available; ask for them and Claude will say so.
- After G6 the next phases (ANIMATION, ANIMATION_PREVIEW, FINAL_RENDER, POST,
  DELIVERY) have no commands yet. `fm authorize final-render` exists but has
  nothing to gate yet.

---

## Changing your mind (revisions)

Never edit approved files to "just fix it". Editing an approved document
drifts its gate, editing LOCKED canon in place fails validation
(`LOCKED_CANON_MODIFIED`), and both block advancing. Use the tools that show
the cost first.

### The revision loop

| Step | Command | Who |
|---|---|---|
| 1. See the blast radius | `fm -p my_film impact canon:characters.mara.wardrobe.jacket` (or `artifact:...`, `shot:...`) | anyone |
| 2. See what is stale in a scope | `fm -p my_film plan --scope scene:SC03` (scopes: `film`, `shot:ID`, `shots:A..B`, `scene:SC01`, `sequence:SQ01`, `character:ID`, `asset:ID`, `ref:REF`) | anyone |
| 3a. Work that is not approved yet | tell Claude, or `/film-revise my_film "<feedback>"`; the owning agent revises the PROPOSED file | Claude |
| 3b. Approved or locked canon | the owning agent runs `fm -p my_film change propose <canon id> --set 'statement=Dark brown waxed jacket.' --reason '...'` (add more `--set` for other fields) | Claude |
| 4. Decide the change | `fm -p my_film change list`, `fm -p my_film change show CHANGE-001`, then **you**: `fm -p my_film change approve CHANGE-001` (or `change reject`) | you |
| 5. Regenerate only what is stale | `fm -p my_film plan --scope <narrowest scope>`; each owner regenerates their stale nodes, upstream first; `fm stamp <file>`; `fm validate -q` | Claude |
| 6. Re-decide drifted gates | `fm -p my_film status` lists DRIFTED gates; QA re-reviews; you `fm -p my_film approve G3` again | you |

`/film-revise my_film "Change Mara's jacket to dark brown"` runs steps 1-5 for
you and stops at step 4.

Once you approve the change request the entry becomes v2 (v1 is kept as SUPERSEDED),
`CHANGELOG.md` is regenerated, everything downstream is stale, and the gates
that approved that content show as DRIFTED until you re-approve them.

`fm change propose --set` accepts the fields `statement`, `value`,
`rationale`, `serves`, `depends_on`, `applies_to`, `tag`; values are parsed
as YAML. It cannot change `notes`: use
`fm -p my_film canon annotate <canon id> --notes '...'` for free-text
corrections on a locked entry (logged in the ledger).

### Wording-only edits

If you edited an approved document only to clarify wording (meaning
unchanged), you can accept it without re-approving the gate:
`fm -p my_film amend G3 artifact:world_bible --note 'wording only: ...'`.
It is a typed, ledger-recorded statement by you. Anything that changes meaning
needs a change request and re-approval.

### Sending a gate back

While a gate is pending you can instead run
`fm -p my_film revise G3 --notes '...'`: the agents get your notes verbatim
(`fm log`), revise, and `fm submit` again.

### Review findings -> scoped fixes (`fm feedback`)

For findings from a review, a preview still or your own notes on a specific
target there is a feedback ledger, so a finding turns into the smallest
possible amount of rework:

```
fm -p my_film feedback add shot:SC04_SH020 --note 'phone fills the frame' --severity high
fm -p my_film feedback list --open
fm -p my_film feedback plan FB-001        # owner, handling command, whether a change request is needed, stale set
fm -p my_film feedback resolve FB-001 --by 'revised SC04_SH020 (commit abc123)'
```

(`--severity` is `low|medium|high|blocker`; `--owner` overrides the suggested
owner.) `resolve` is refused while nodes in the plan are still stale unless
`--force-stale` is given, and that is recorded. Items are stored as
`qa/feedback/FB-001.yaml`, `FB-002.yaml`... and `add` prints the id to use.

Note: the `feedback` commands and `fm qa review-status` were present in the
working tree but not yet committed when this page was written (M5 work in
progress). If `fm feedback --help` says the command does not exist, use
`/film-revise` and `fm change propose` as above.

### Rule of thumb for what changes cost

| You change | It re-opens |
|---|---|
| a line in the screenplay | G2 and everything derived from it: usually the shots of that scene |
| a character's wardrobe or proportions | G3, and every shot featuring that character (`plan --scope character:<id>`) |
| the palette or lighting | G4, then every shot and every still |
| one shot's camera | G5 only for that shot, then that shot's still (`fm blender preview --shots SC04_SH020`) |

## When you are done with G6

Record it (`git add -A`, commit, push from the laptop), and keep the QA
findings you acknowledged: they are listed under "carried forward" in
`STATUS.md` and are the to-do list for the next milestone.
