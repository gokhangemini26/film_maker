# Data model

Machine contracts are in `schemas/json/*.schema.json` (regenerate with
`fm schema export`). All files are UTF-8, LF line endings.

## Vocabulary

**Lifecycle** (`Status`): `PROPOSED`, `APPROVED`, `LOCKED`, `SUPERSEDED`, `REJECTED`.

**Tag** (what kind of statement): `FACT`, `DECISION`, `ASSUMPTION`,
`RECOMMENDATION`, `USER_REQUIREMENT`, `DEPENDENCY`, `UNKNOWN`. Never turn an
assumption into a fact; change the tag only with evidence.

**Refs** (graph nodes): `canon:<id>`, `artifact:<id>`, `shot:<id>`,
`resolved:<id>`, `blend:<id>`, `render:<id>`, `audio:<id>` (stems, mixes), `edit:<id>` (EDL, animatic, master), `qa:<id>`.
`canon:intent.*` nodes form the INTENT layer.

## Canon entry — `canon/<domain>.yaml`

Domains: `intent, tone, story, world, characters, look, camera, animation, audio, continuity`.

```yaml
domain: look
entries:
  - id: look.color.accent            # domain.path.name, lowercase
    statement: Warm amber practicals. # what was decided (human-readable)
    value: "#E0A040"                  # machine-readable implementation
    rationale: Warmth is reserved for hope.   # WHY (required on approved decisions)
    serves: [intent.hope]             # the intent this implements
    depends_on: []                    # other canon ids
    applies_to: [SC03]                # scope: scenes/shots/sequences/characters; empty = whole film
    tag: DECISION
    status: PROPOSED                  # agents only ever write PROPOSED
    source: agent:look-director
    version: 1
    history: []                       # superseded versions (managed by fm)
```

Intent example (`canon/intent.yaml`):

```yaml
  - id: intent.isolation
    statement: The protagonist should feel isolated.
    tag: USER_REQUIREMENT
    source: user
```

The **content hash** covers `id, statement, value, rationale, serves,
depends_on, applies_to, tag` — not status, version, history, source or notes.

## Artifact — any `.md` (or `.yaml`) with an `fm:` block

```markdown
---
fm:
  id: character_bible
  kind: character_bible
  phase: WORLD_CHARACTERS
  status: PROPOSED
  owner_role: character-designer
  derived_from:
    - ref: canon:characters.mara.wardrobe.jacket
      hash: sha256:…          # filled by `fm stamp`
  serves: [intent.isolation]
title: Character Bible
---
# Characters
...
```

Hash = everything except the `fm:` block (front-matter + normalised body).

## Brief — `00_brief/brief.yaml`

Each field is `{value, status: given | assumed | unknown, note}`. Fields:
title, concept, genre, duration_s, target_audience, emotional_goal,
story_idea, visual_style, color_palette, references, realism,
animation_style, camera_style, lighting_style, environment, characters, era,
location, aspect_ratio, fps, special_requirements.

## Shot — `08_shots/SC01_SH010.shot.yaml`

```yaml
shot_id: SC01_SH010
scene_id: SC01
sequence_id: SQ01
status: PROPOSED
duration_s: 4.0
serves: [intent.isolation]
creative_intent:                 # WHAT the shot is for
  narrative_purpose: Establish Mara alone in the city.
  emotional_purpose: Loneliness.
  visual_purpose: Small figure, large negative space.
  audience_effect: The viewer feels her distance from everyone.
camera: {lens_mm: 50, height_m: 1.6, movement: static, look_at: mara}
composition: {framing: wide, aspect_ratio: 2.39, subject_position: lower_right}
characters: [{id: mara, position: [3, 0, 0], action: walking}]
environment: {location: harbour street, weather: rain, time_of_day: night}
lighting: {}        # open in M1; typed as builders land
color: {}
animation: {}
render: {}
rationale:                       # WHY each implementation choice
  camera: Moderate compression separates her from the background ...
  lighting: ...
  composition: ...
  movement: ...
style_break: null                # {reason: ...} when a shot breaks the style lock on purpose
continuity_refs: [continuity.sc01.weather]
derived_from: [{ref: artifact:shot_list}]
```

## Shot animation — `09_animation/SC01_SH090.anim.yaml` (kind `shot_animation`, M6)

Typed tracks a builder reads; the prose `animation` block in the shot file stays the human brief.
Artifact id is `anim_<shot id lowercase>`; owner `animation-director`; JSON Schema `schemas/json/anim.schema.json`.

```yaml
fm: {id: anim_sc01_sh090, kind: shot_animation, phase: ANIMATION, status: PROPOSED, ...}
shot_id: SC01_SH090
frames: 24                 # must equal the resolver's frame count
vocab_version: 1           # core/fm/animvocab.py = canon animation.vocab.*
rationale: ...
characters:
  ren:
    pose:   [{f: 0, ref: car_phone_up, ease: hold, blend_f: 0, note: ..., rationale: ...}]
    move:   {gait: none}   # run_phone_out | scramble need `path`; crank_turn needs first_top_f
    face:   [{f: 0, ref: freeze}]
    look:   [{f: 0, target: phone}]
    breath: [{f: 0, ref: hold, dur_f: 16}]
props:      {phone_ren: [{f: 0, attach: hand_l}]}      # per-prop typed fields (animvocab.PROPS)
ui_timeline: []            # typed overlay events on canon look.style.phone_screen.states_by_shot
camera: {move: none}       # or dolly_in with start_f/end_f/dist_m/ease ranges
holds:  [{f0: 0, f1: 15, scope: all, min_f: 16}]
events: [{f: 16, id: stuck_exhale, kind: visual}]
preview_frames: [0, 16, 23]
```

Frames are shot-local. `note` and `rationale` are free text for humans and are never parsed or
copied into resolved files. `fm validate` runs the `ANIM_*` rules (vocabulary, ranges, ordering,
blends, prop transitions, holds, camera, events); the resolver refuses a file with any ANIM error.
Resolved shots (`fm.resolved_shot/2`) carry `motion` (tracks plus absolute frames, derived
`handle_top` events) and `ui_timeline` (per-frame phone screen state); both are `null` when the shot
has no anim file / no canon row. Bare files with only `fm` and `shot_id` are stubs and are ignored.

## Ledger — `.fm/ledger.jsonl`

One JSON object per line: `seq, ts, actor, action, target, payload, prev, hash`.
`hash = sha256(canonical JSON of the record without hash)`; `prev` is the
previous record's hash. Actions: `project.init, phase.advance, phase.submit,
gate.decide, canon.approve, canon.lock, canon.reject, change.propose,
change.approve, change.reject, authorize, shot.stage`. Human decisions record
`confirmation: typed | sandbox-simulated`.

`state.yaml` is `replay(ledger)`; `fm validate` reports `STATE_TAMPERED` if
the cache differs.

## Change request — `changes/CHANGE-NNN.yaml`

`target, reason, set (fields to replace), base_version, base_hash,
proposed_by, impact, status, decided_by, new_hash`. Approval fails if the
target changed since the proposal (conflict).

## Derived record — `.fm/derived/<kind>/<id>.json`

`ref, derived_from [{ref, hash}], content_hash, path, producer, created_at`.
Written by builders (M3+) or `fm record`.

## Actors

`FM_ACTOR=<human|agent|system>:<name>`. Unset: an interactive terminal is a
human (named from `git config user.name`); anything else is
`agent:unattended`. The repo's `.claude/settings.json` sets
`FM_ACTOR=agent:claude-code` for Claude Code sessions.
