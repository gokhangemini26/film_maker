# M6 SCOPE: Animation, audio and post-production planning

Status: **proposal, awaiting approval.** No M6 code written. Date: 2026-09-30.
Baseline: `cd74567` (M4 wave 2). Last Signal has G1–G6 approved, G5 shows DRIFTED, and 38 shots come to 1440 frames (60 s at 24 fps).
Suggested save path: `docs/M6_SCOPE.md`, plus the Projects doc `claude/M6_SCOPE.md`.

Two untracked files, `core/fm/feedback.py` and `core/fm/qa_review.py`, exist in the working tree and are not mine. M6 core work should not collide with them.

---

## 0. What the repo told me (drives every decision below)

1. **The animation blocks are mostly free text.**
   - Across the 38 resolved shots there are 224 keys of the form `{f, t, pose: "<prose>"}`.
   - Props are prose too, for example `glovebox_lid: "lowered by hand f24-30 (ease-in-out), left down"`.
   - Prop and UI blocks are keyed `props` (23 shots), `ui` (14) and `sound_sync` (14).
   - Nothing in the shot schema constrains `animation`: `ShotSpec.animation` is `dict[str, Any]`.
2. **The M3/M4 builder already regex-parses those strings.** This is exactly what M6 must delete:
   - `preview.pose_from_text` maps prose to 5 stances (`stand|kneel|sit_car|sit_kerb|sit_chair`).
   - `car_state` reads the door angle and glovebox state from prose.
   - `headphones_down` reads a frame number out of prose.
   - The face `mouth_hidden` flag comes from a regex.
   - Each of these picks a single pose per still, at the mid-shot frame.
3. **A real ambiguity is already hiding in the prose.** `SC04_SH040` says the glovebox lid is "lowered by hand f24-30 … left down". `car_state` treats "lowered" as OPEN. `SC04_SH010` says the crank is "in the closed glovebox". Only an enum (`closed | open_down`) settles this, and the animation-director must then say which one it means.
4. **Characters are not rigged.**
   - `characters.figure()` computes joint points for one of 5 stances and places capsule limbs with `util.between()`.
   - There is no armature and no keyframing anywhere in `blender/`.
   - Canon `characters.*.representation` promises "humanoid_standard_bone_names", but the M3 provider does not implement it.
5. **Very little of the film needs body motion.**

   | Kind of motion | Shots |
   |---|---|
   | `locomotion.type != none` | 5 |
   | Camera moves (dolly-in) | 2: `SC04_SH030`, `SC04_SH050` |
   | Seated or held shots | ~32 |

   - The 5 locomotion shots are `SC02_SH010/020/030`, `SC03_SH010` (run then kneel) and `SC04_SH040` (kneel lunge).
   - Most of the work is therefore prop, UI, face, eyeline and car-body animation, not walking. The plan is sized that way.
6. **Structured tables already have a precedent in canon.**
   - `look.style.phone_screen.states_by_shot` holds a per-shot, per-frame table, LOCKED.
   - Its rationale records that builder thresholds drifted from it in 24 of 35 rows. The lesson: do not let builders infer state from anything but a table.
7. **Audio has canon and prose to build on, but no design.**
   - `canon/audio.yaml` and `canon/animation.yaml` are empty (`entries: []`).
   - `tone.wordless` (LOCKED) forbids dialogue and voice on the phone.
   - It allows non-verbal sounds: breaths, sighs, small vocal reactions.
   - `tone.the_turn` says that from SC04 on the soundtrack is "only the ratchet and his breath".
   - `WORLD_BIBLE` bans sirens, window music and dogs, and leaves sound design "to the audio department".
   - STORYBOARD has a one-line `Sound:` cue for all 38 shots, and 14 shot files carry frame-exact `sound_sync` prose. Those are the seed for the cue sheet.
   - No score is anywhere in the documents. The only music is Hana's headphone leak in `SC05_SH010/020`.
8. **Post is nearly pre-decided by locked canon.**
   - `look.style.texture_and_grain` allows only monochrome grain at 1.5 % luma, an optional vignette of at most 10 %, and no LUT.
   - `look.style.glow` allows compositor glare on emission only.
   - `camera.rhythm.transitions` fixes hard cuts, a FADE IN at the head (length "set by post") and an 18-frame FADE OUT at the tail. `SC06_SH010` already reserves f64–82 for it.
   - So there is no creative grade to plan. Post is mostly assembly, grain, fade, mix and export.
9. **The title card and credits question is open**, and it collides with locked canon.
   - `tone.wordless` says the invitation is the ONLY readable text in the film.
   - STORY_BIBLE lists title and credits as "not decided in canon".
10. **Tooling facts.**
    - Higgsfield `generate_audio` is speech-only. Its description says it cannot do general music or SFX, so it has no role in a wordless film.
    - ffmpeg is on both machines.
    - 48 kHz ÷ 24 fps = exactly 2000 samples per frame, so audio sync can be sample-exact.
    - The Windows ARM EEVEE process corrupts colours in long single processes. That is why previews run one process per shot, and it constrains sequence rendering.
    - `DERIVED_KINDS = (resolved, blend, render, qa)` has no `audio` or `edit`.
    - `PHASES` has no gate between POST and COMPLETE.

---

## 1. Principles for M6 (carried over, plus three new)

- Unchanged from M1–M3: `fm` is authoritative, agents write PROPOSED only, and humans decide gates. Blender is an engine, not a database. Builds are idempotent and pinned to 5.2.x. Only the pinned Blender counts as G7/G8 evidence, and `--draft` never does.
- **New 1. No free-text parsing at build time.**
  - Anything a builder, mixer or QA check needs is a typed field validated against a canon vocabulary.
  - Free-text `pose:` notes stay for humans and reviewers.
  - The build fails loudly on an unknown ref and never guesses.
- **New 2. Frames are the only clock.** Animation, audio cues, the edit list and QA all address global film frames, or shot-local frames converted by the resolver's frame table. Nothing is timed in seconds after resolve.
- **New 3. Creative vs technical split.**
  - Which pose, when, and why is the animation-director's job (canon vocabulary names + tracks).
  - How a pose is realised in joints and meshes (`poses.py`) is the blender-td's job.
  - Changing pose geometry is a builder change, never a creative change.

---

## 2. Animation build design

### 2.1 Where the structured data lives (schema decision)

**Do not change `ShotSpec` and do not touch the G5-approved shot files.**

- G5 is already DRIFTED. Editing 38 approved shot files to add tracks would cascade re-approvals and stale reviews for no creative gain.
- `09_animation/` exists, is empty, and is already listed in `PROJECT_DIRS`.

New artifact kind **`shot_animation`**, one file per shot: `09_animation/<shot_id>.anim.yaml`.

- It has an `fm:` block like `scenes` does, so the loader already discovers it.
- Its `derived_from` is `shot:<id>` + the characters' canon + the vocabulary.
- The old prose `animation` block in the shot stays untouched. It is the human-readable brief and the source the animation-director reads.
- `ARTIFACT_OWNERS["shot_animation"] = "animation-director"`.

Schema `AnimationTracks` (Pydantic, `extra="forbid"`; exported to `schemas/json/anim.schema.json`):

```yaml
fm: {id: anim_SC04_SH040, kind: shot_animation, phase: ANIMATION, status: PROPOSED,
     owner_role: animation-director, derived_from: [...], serves: [...]}
shot_id: SC04_SH040
frames: 60                      # must equal the resolved shot's frame count
vocab_version: 1                # canon animation.vocab version this was written against
characters:
  ren:
    pose:                       # discrete presets; builder blends between consecutive keys
      - {f: 0,  ref: kerb_sit_phone_left,   ease: hold}
      - {f: 6,  ref: kneel_lunge_start,     ease: ease_in_out, blend_f: 10}
      - {f: 16, ref: lunge_lean_door_reach, ease: ease_out,    blend_f: 8}
      - {f: 24, ref: lunge_glovebox_latch,  ease: ease_in_out, blend_f: 6}
      - {f: 30, ref: lunge_glovebox_grasp,  ease: hold}
      - {f: 36, ref: lunge_back_out_crank,  ease: ease_in_out, blend_f: 8}
      - {f: 42, ref: lunge_two_hand_crank,  ease: hold}
      - {f: 44, ref: kerb_sit_crank_lap,    ease: ease_in,     blend_f: 8}
      - {f: 54, ref: kerb_sit_crank_lap,    ease: hold}       # explicit final hold
    move:
      gait: none            # none | run_phone_out | scramble | crank_turn
      path: []              # waypoints [{f, x, y}] in set coords; only when gait != none
    face:   [{f: 0, ref: focused_calm}]
    look:   [{f: 0, target: glovebox}, {f: 37, target: crank_charger}]   # eyeline
    breath: [{f: 54, ref: in_slow}]
props:
  glovebox_lid:   [{f: 24, state: open_down, ease: hand_lower, dur_f: 6}]
  crank_charger:  [{f: 0,  loc: glovebox},
                   {f: 30, loc: hand_r}, {f: 42, loc: hands_both},
                   {f: 54, loc: lap, arm: folded, pip: 0.0}]
  phone_ren:      [{f: 0,  attach: hand_l}]                 # screen comes from ui_timeline (2.3)
camera: {move: none}            # or {type: dolly, dist_m: .., ease_in_f: [4,8], ease_out_f: [34,35]}
events:                         # named sync points, consumed by audio, QA and editors
  - {f: 24, id: lid_latch}
  - {f: 33, id: crank_lift}
  - {f: 52, id: seat_land}
preview_frames: [0, 16, 30, 44, 59]   # optional; default = every pose key + last frame
notes: []                       # free text for humans only; never parsed
```

Rules enforced by `fm validate` (new check `ANIM_*`) at ANIMATION and after:

- Every `ref`, `state`, `loc`, `target` and `gait` must be in the vocabulary (2.2).
- Frames are integers with `0 <= f <= frames-1`, strictly increasing per track.
- `blend_f` must not run past the next key.
- `path` is required if and only if `gait != none`.
- `events` ids are unique per shot.
- `frames` matches the resolver's frame table.

### 2.2 The `pose_ref` vocabulary

**Names live in canon** (domain `animation`, LOCKED at G7), as entries `animation.vocab.*` with a rationale each.
**Geometry lives in code**: `blender/fm_blender/poses.py` maps each name to joint targets in the character's local frame, reusing the joint solver logic now in `figure()`.

A test asserts that the canon names equal the keys of `poses.py`. A missing geometry entry is a builder bug, and an unknown name in a track is a spec error.

Proposed enums, drafted from the 224 existing keys. The animation-director finalises them in its first task and the human ratifies at G7.

**Ren stances and poses** (~22 presets, grouped by stance family):

| Family | Presets |
|---|---|
| car (seated, driver) | `car_upright_wheel`, `car_phone_chest`, `car_phone_lap`, `car_mirror_reach`, `car_tuft_press`, `car_freeze_thumb_up`, `car_sag`, `car_sit_up`, `car_reach_glovebox`, `car_crank_lap`, `car_forehead_wheel` |
| street / shop | `stand_upright`, `run_phone_out`, `scramble_out`, `swerve_left`, `kneel_socket`, `kneel_still` |
| kerb | `kerb_sit_knees_up`, `kerb_sit_phone_left`, `kerb_sit_crank_lap`, `kerb_lean_back_car`, `kneel_lunge_start`, `lunge_lean_door_reach`, `lunge_glovebox_latch`, `lunge_glovebox_grasp`, `lunge_back_out_crank`, `lunge_two_hand_crank` |

**Hana** (~6): `desk_sketch_head_down`, `desk_notice_eyes`, `desk_headphones_hands_up`, `desk_headphones_neck`, `desk_phone_low`, `desk_smile_settle`.

**Face refs:** derived from canon, not invented.
- Ren's `comic_set` (`rehearsed_breath`, `letdown`, `freeze`, `relief`, `stunned_stillness`) and `tender_set` (`focused_calm`, `hesitation_at_heart`, `release_after_send`, `final_look_up`), plus `neutral`.
- Hana's set comes from `characters.hana.expressions`.
- The face controls to implement are those in `representation.face.controls` (brows, eyes, mouth line and so on).
- A validator rule: comic-set faces are illegal from `SC04_SH030` on, per `tone.the_turn`.

**Gaits:**
- `none`, `run_phone_out` (arms not swinging, per `characters.ren.movement`), `scramble` and `crank_turn`.
- `crank_turn` is a 24-frame handle cycle. It exposes `handle_top` events every 24 frames. This is the single source of truth for the ratchet click (see 3.4).

**Ease enum:** `hold`, `step`, `linear`, `ease_in`, `ease_out`, `ease_in_out`, `overshoot_small` (crown-tuft spring), `gravity` (crank drop, lid drop).

**Prop state enums** (each with allowed transitions, from the prose seen):

| Prop | States or params |
|---|---|
| `passenger_door` | `closed`, `open_60`; `swing` overshoot param (`SC02_SH010`) |
| `glovebox_lid` | `closed`, `open_down`; ease `gravity_drop` or `hand_lower`; `bounce_f` |
| `crank_charger` | `loc`: `glovebox`, `falling`, `thighs`, `lap`, `hand_r`, `hands_both`, `glovebox_stowed`; `arm`: `folded`, `unfolded`; `pip` 0..1 |
| `phone_ren`, `phone_hana` | `attach`: `hand_l`, `hand_r`, `lap`, `chest`, `desk_face_up`, `hands_low` |
| `rear_view_mirror` | `tilt_deg` track |
| `hana_headphones` | `head`, `neck`, and an arc transition |
| `pencil` | `held`, `laid` |
| `car_body` | presets `cough`, `idle_tremble`, `sigh_sink`, `stall_shudder`, `sway_1cm` (amplitude in mm and decay are preset constants in `poses.py`) |
| `dash_lights_and_adapter_ring` | `on`, `off` |
| `shop_door` | `swing` param |
| `shop_lights` | `on`, `off` (blackout event) |
| `ceiling_panels` | `steady` (a deliberate no-op the QA can assert) |

**Eyeline targets:** a fixed enum resolved to world objects by the builder (`mirror`, `phone_ren`, `glovebox`, `crank_charger`, `road`, `sky`, `camera`, `ground`, `phone_hana`, `sketchbook`, `window`, and so on). The resolver checks the target exists in the shot's location assets.

Rejected alternative: keeping `pose:` prose and running a smarter parser. That is the failure mode M6 exists to remove. The parser cannot tell "lowered" from "opened" and would fail silently.

### 2.3 Resolver pass-through

`fm.resolve.resolve_shot` gains:

- Load `09_animation/<id>.anim.yaml` if present. Validate it against the schema and the canon vocabulary.
- Emit a new `motion` block in `09_resolved/<id>.json`:
  - tracks with absolute film frames added (`f_abs = frames.start + f`) and shot-local frames kept;
  - `events` expanded with `f_abs`;
  - a per-frame `ui_timeline` (below);
  - the vocabulary version.
- The prose `animation` block continues to pass through untouched as `animation` (for reviewers). The builder never reads it once `motion` exists.
- Bump the schema tag to `fm.resolved_shot/2`. Shots without an anim file keep `motion: null`, and the M3 still-preview path keeps working until migrated.
- Add `artifact:anim_<id>` and the `canon:animation.vocab.*` entries to `from_refs`. Editing one anim file re-resolves only that shot. Editing a vocabulary entry re-resolves every shot that uses it, via the existing graph.

**`ui_timeline`, from the existing canon table.** The resolver expands `look.style.phone_screen.states_by_shot` into explicit per-frame states for each shot:

```json
{"f": 8, "pct": 2, "red": true, "bolt": true, "icon_blink": false, "brightness": 1.0, "ui": "sent", "sent": {"progress": 0.0, "tick": false}}
```

- The parser for that table lives once, in `core/fm`, and is tested against all 38 rows (the compact `{f0:…, f32:…}` forms, `flicker`, `ramp_to_1.0_by_f4_ease_out`).
- `phone.screen_state()` (currently number thresholds) is deleted.
- Screen states then have one source of truth, in canon, that both the builder and `fm qa motion` read.

### 2.4 Builder consumption (Blender side)

Refactor the 350-line `render_shot` into three deterministic steps in new modules:

1. **`assemble.py`**: set visibility, camera object, lights, car and props at frame 0 state. This is the current static build without any regex.
2. **`rig.py` + `poses.py` + `motion.py`**: apply tracks.
   - `rig.build_figure(char, canon)` builds the same capsule figure as today, but each limb is bound to named joint empties (`hip`, `chest`, `neck`, `head`, `sh_L/R`, `el_L/R`, `hand_L/R`, `hip_L/R`, `knee_L/R`, `foot_L/R`). Limb objects are aimed between joints.
   - **Rig decision:** joint positions are blended in Python and baked as keyframes on every frame, with LINEAR interpolation in Blender.
     - Blender's own F-curve defaults therefore never influence the result.
     - Same input gives the same keyframes.
     - It needs no armature, no IK solver, no constraint stack.
     - It matches "a stylised proxy" and the spike's finding that outlines, materials and one-process-per-shot are already fragile.
   - `motion.bake(shot)`, for each frame of the shot:
     - resolve the active pose pair and eased fraction per character;
     - blend joints;
     - apply `move` (path and gait);
     - apply `look` (head yaw/pitch toward the target, eye offset);
     - swap face shapes;
     - set prop transforms from state tracks and attach frames;
     - insert keyframes.
   - `gait` generators (`run_phone_out`, `scramble`, `crank_turn`) are pure functions of (frame, speed, path), returning joint offsets and foot-contact flags. Contact flags go into the bake report for the slide check.
3. **`render.py`**: render a frame list or range (2.6).

**Phone screens.** The screen is a mesh painted by `phone.py`, not a texture. It cannot change mid-shot with keyframes alone.
- Build one phone screen object per distinct `ui_timeline` state in the shot.
- Key `hide_render` and `hide_viewport` per frame to switch between them.
- Brightness scales the emission factor, keyed per frame.
- `SC04_SH080` (progress line f8–32) has ~25 distinct states, and `SC01_SH070` (typing) ~16. That is acceptable.
- `SC04_SH020`'s flicker is 2 brightness levels only.

**Camera animation.**
- Only 2 shots move. Interpolate `start_position` to `end_position` along the `move` type (`dolly`) with the ease-in and ease-out frame ranges from the anim file.
- The peak-speed cap of 0.15 m/s from those shots' notes becomes a check (2.7).

**Lights events.** `shop_lights` on/off (`SC03_SH050` f8) and phone glow brightness are keyed from `props` and `ui_timeline`.

**Removed from the builder in M6:** `pose_from_text`, `_scene_rule_pose`, `car_state`, `headphones_down`, the `face_txt` regex, and every "search prose for a word" branch. A build with `motion == null` on a shot that has an anim requirement is a hard failure.

### 2.5 One-frame stills for QA (`preview_frame`)

Extend `fm blender preview`, or add `fm blender frames`, with `--frames 0,30,59`, `--every-key` and `--scope`.

Frames come from the anim file's `preview_frames`. If absent, the default is every pose-key frame plus the last frame.

Outputs go to `10_blender/frames/<shot>/f####.png`, each recorded as `render:frame_<shot>_f####` and derived from `resolved:<shot>`.

- Also produce a per-shot **contact strip**: the chosen frames side by side with frame numbers stamped. PIL is already an optional dep, and the M4 `scripts/m3_preview_cloud.py` contact sheet shows the pattern.
- The qa-supervisor's vision pass then reads strips instead of one mid-shot still. This is what lets it judge the motion beats (the lunge, the headphone slide).
- Existing mid-frame preview stays as the fast path, but it now renders the pose actually active at the mid-frame.

### 2.6 Playblast video

`fm blender playblast [--scope ...] [--width 640] [--jobs N]` renders each shot's full frame range, then assembles with ffmpeg.

- **Render settings.** PNG sequence at 640 px wide, EEVEE 8 samples, no motion blur, `use_stamp` on for frame, shot id and timecode. Output goes to `10_blender/playblast/<shot>/####.png`.
- **Chunking with resume.** Render in chunks of ~48 frames per Blender process (see risks), skipping frames already on disk.
- **Assembly.** `ffmpeg` builds `<shot>.mp4` per shot and `10_blender/playblast/film.mp4`, the whole film silent. This becomes the video track of the M6 animatic.
- **Record.** Each shot is a `render:playblast_<shot>` node derived from `resolved:<shot>`.
- **Budget.**
  - The spike measured 5.9–6.9 s per 1080p EEVEE frame at 16 samples.
  - At 640 px and 8 samples, a working estimate is 1–3 s per frame, so the full 1440 frames take roughly 30–70 minutes on the laptop (to be measured in task A0, section 6).
  - It is unattended and resumable.

### 2.7 Deterministic checks: `fm qa motion`

Two tiers, both writing `qa/motion_report.json`, recorded as `qa:motion`, exit 1 on FAIL. Technical only; never creative evidence.

**Tier 0: spec level, runs anywhere (no Blender), in `core/fm/qa_motion.py`:**

| Check | Level |
|---|---|
| Every shot has an anim file; `frames` equals the resolved count | FAIL |
| Timing: all keys and events inside `0..frames-1`; last pose key not past the end; no key gaps larger than the shot's hold policy | FAIL / WARN |
| Vocabulary and transition legality: e.g. `glovebox_lid` cannot go `open_down → open_down`; `crank_charger.loc` follows the allowed graph; comic faces after the turn | FAIL |
| **Prop continuity across shots** (film order): the state at the end of shot N equals the state at the start of shot N+1 for persistent props (`passenger_door`, `glovebox_lid`, `crank_charger.loc/arm`, `phone_*.attach`, `hana_headphones`, `shop_lights`, `dash_lights…`). Battery and screen state are checked against canon `continuity.battery`. | FAIL |
| Distance / speed: from `path` plus frames, mean and peak speed within a gait-specific max from canon (`characters.ren.movement`, run ≈ 3–5 m/s, kneel step ≈ 1.1 m/s per the existing notes) | WARN |
| Camera: peak speed under the 0.15 m/s cap (`camera.movement.push_in`); dolly length matches `start/end_position` | FAIL |
| **Running time vs SCENES:** per scene, the sum of shot frames vs `est_duration_s × 24` (SC04 is 434 f vs 19 s = 456 f, a known 22-frame gap); total = 1440 f vs the brief's 60 s | WARN beyond tolerance, FAIL if total differs from the shot table |
| `ui_timeline` self-consistency: no `0 %`, bolt only while a source is live (canon `never:` list), digit never hidden | FAIL |
| Hold rules carried from shot notes: minimum-hold counts on the insert legibility shots (e.g. "held f16-57, minimum 41"), read from a small `min_hold_f` field in the anim file | FAIL |

**Tier 1: bake report from Blender (per shot, written by `motion.bake`):**

| Check | How |
|---|---|
| **Foot sliding** | For each character and each frame flagged in contact (from the gait generator or a pose preset's `planted` list), world foot displacement between consecutive contact frames must be ≤ 5 mm. Applies to the 5 locomotion shots plus kerb/car pose blends. |
| Limb-length drift | Each limb's length across the shot vs its rest length: ≤ 8 % (joint-blending artifacts) |
| Attach fidelity | `crank_charger` in `hand_r` or `hands_both`: hand-to-crank-grip distance ≤ 2 cm; phone in hand ≤ 2 cm; headphones on head or neck |
| Reach | Hand-to-target distance at contact key frames (the known `SC04_SH040` glovebox reach of ~0.7 m against the proxy arm limit) reported as a margin. WARN below 5 cm margin. |
| Canon geometry rules | e.g. `camera.framing.jacket_off_sky`: max jacket z in `SC04_SH040` must stay below the car roof line (1.45 m), evaluated on the baked joints |
| Keyframe coverage | Every animated object has a key on every frame of its track span; no orphan `fm_id` |
| Idempotence | Building the same shot twice gives an identical per-object keyframe hash |

**Tier 2, advisory:** the qa-supervisor reads the contact strips and writes findings into `qa/reviews/G7_REVIEW.md`, labelled judgment.

---

## 3. Audio design

### 3.1 Roles

Add **`sound-designer`** (agent, model class creative, tools `Read, Edit, Glob, Grep, Bash`).

- It owns:
  - `canon/audio.yaml` proposals (domain `audio`, LOCKED at G7);
  - `12_post/AUDIO_BIBLE.md`;
  - `12_post/AUDIO_CUES.yaml`;
  - the sound library manifest and synthesis recipes.
- The `post-supervisor` (already in `config/models.yaml`) owns the edit and delivery side (section 4).
- Both are added to `roles.py`.
- **Correction to `CANON_DOMAINS`:** move `audio` from `post-supervisor` to `sound-designer`.
- New skills: `sound-design`, `post-production`. New artifact kinds: `audio_bible`, `audio_cues`, `edit_plan`, `post_plan`.

### 3.2 Canon structure (`canon/audio.yaml`)

Entries follow the M1 schema (rationale, `serves`, `depends_on`). Proposed ids:

| Id | Content |
|---|---|
| `audio.principles` | Strictly wordless (cites `tone.wordless`). Soft-but-cinematic dynamic range. Quiet street world. Comic sound density before the turn, "only ratchet and breath" after (`tone.the_turn`). |
| `audio.score` | **Human decision D1.** Recommendation: no underscore. Rationale: the ratchet plus breath is the score; music would compete with the intent that the effort is heard. Rejected: a light comic cue before the turn, which pushes the film toward the manic register the tone anti-goals exclude. |
| `audio.palette` | Sound families and each sound id. Families: `ui` (tap, swipe, key, low-battery blip, charging chime, send whoosh, tick, ring tone), `car` (starter, cough, idle, sigh, shudder, stop, door thunk, lid clack), `shop` (door chime, fridge hum, panel buzz, clunk, scrape), `body` (breaths, sighs, footsteps, cloth, seat creak), `room` (pencil, headphone leak, room tone), `street` (bird, distant traffic, dusk ambience). |
| `audio.motifs` | Three rhymes: (1) the ring tone ×3 then silence (`SC01_SH050`); (2) the hum dying (car in `SC01_SH130`, shop in `SC03_SH050`); (3) the ratchet as the film's pulse (60 clicks per minute, one per 24 frames). |
| `audio.silence_map` | Frame spans that must be silent or at room-tone floor: `SC03_SH050` f8–29, `SC03_SH060`, `SC01_SH140` (no UI sound on the number change), `SC04_SH010` (nothing but the street). |
| `audio.ratchet` | Phase lock: first click `SC04_SH050` f56, then every 24 frames, carried across `SC04_SH060–SH090` (clicks at f0/24/48 of SH060, f4 of SH070, f2/26/50 of SH080, last at f7 of SH090). The cue generator derives these from the `handle_top` events instead of hand-typing them. |
| `audio.perspective` | Per scene: interior car (closed cabin, ambience outside filtered), street (open), shop (fridges and panels), Hana's room (near silence, headphone leak). |
| `audio.mix` | Delivery loudness and headroom: -16 LUFS integrated (web/festival default; decision D3), true peak ≤ -1 dBTP, 48 kHz, 24-bit master, stereo. No dialogue anywhere, so no dialogue-based levelling. |
| `audio.sources` | For each sound id: `source: synth | library | recorded`, licence (`CC0`, `own`, `UNKNOWN`), and the recipe or file path. Unknown licence blocks final export, as for assets (ARCHITECTURE section 10). |

### 3.3 Cue sheet per shot

`12_post/AUDIO_CUES.yaml` (artifact `audio_cues`) has one entry per cue:

```yaml
- id: cue_SC01_SH050_ring1
  shot: SC01_SH050
  at: {event: ring_pulse_1}           # or {f: 0}, shot-local; exactly one of the two
  sound: ui.ring_tone                 # id in audio.palette
  layer: ui                           # ui | sfx | foley | amb | body | music
  gain_db: -12
  pan: 0.0
  offset_f: 0                         # small lead or lag, in frames
  end: {f: 11}                        # or {until: next_cue} or natural length
  fade: {in_f: 0, out_f: 2}
  serves: [intent.race_against_battery]
```

- Beds (ambience and room tone) are separate entries: `bed: amb.street_dusk, from_frame, to_frame, xfade_f`.
- Sound-designer starting points:
  - the STORYBOARD `Sound:` lines, one per shot;
  - the 14 `sound_sync` texts;
  - the **anim `events`**.
- Where an anim event exists (`lid_latch`, `crank_lift`, `handle_top`, `seat_land`), the cue references it by id, not by frame number. Retiming a shot moves the cue with it. Sync is then structural, not clerical.
- The animation-director adds events for every frame-exact sync the storyboard implies (`key_turn`, `cough_1`, `catch`, `clunk`, `stall`, `door_chime`, `blackout`, and so on). For `SC01_SH100` that is `key_turn` f3, cough f5 and f9, catch f14, lid f25, clunk f31. Each event carries a `kind` (`sound`, `light`, `state`) so QA knows which are audible.
- **Mismatch already in the docs.** STORYBOARD says `SC05_SH010` has "a soft buzz on the desk", but the shot says no vibration or shift. The sound-designer flags this as a conflict for the human rather than resolving it. Similarly STORYBOARD's `SC04_SH070` has a "soft chime" where the shot's sound_sync says "no UI sound". These need rulings (decision D4).

### 3.4 How audio is produced with the tools available

Honest capability table. No tool available to the agents generates SFX or music, and the film has no speech to generate.

| Sound group | Approach | Who |
|---|---|---|
| UI (taps, swipe, keys, blip, chime, ring ×3, whoosh, tick), hums (fridge, panel buzz, car idle, engine sigh), ratchet, clunk, room tone | **Procedural synthesis** in Python (`core/fm/audio/synth.py`: numpy/scipy oscillators, filtered noise, envelopes, pitch glides), deterministic, recipe stored in the manifest, zero licence risk. The starter, cough and stall are the hardest to make convincing (2 days budgeted). | sound-designer writes recipes, Claude implements, **human listens and rules** |
| Footsteps, cloth, seat creak, pencil scratch, door thunk, glovebox lid, shop door chime, dusk street bird and traffic | CC0 or royalty-free library files (Freesound CC0 filter, Sonniss GDC bundle, Kenney). The **human** downloads and drops them in `library/audio/`. Sandbox internet cannot verify licences. A `library/audio/<id>/asset.yaml` with licence is required per file. | human (½ day) |
| Breaths, sighs, the held breath, "a breath through the nose that might be a laugh", relieved exhale | Non-verbal vocal sounds: no tool of ours makes credible ones. **Human records** with a phone (about 20 short takes, the list is generated from the cue sheet). | human (about 1 h recording plus editing) |
| Hana's leaking headphone music (`SC05_SH010/020`, 4–6 s, lowpassed, faint) | Not generated by any tool available. Human supplies a CC0/licensed track or short composed loop; the pipeline applies the filter and level. If none is supplied, fall back to a synthesised generic pad marked `PLACEHOLDER`. | human |
| Score | Recommended none (D1). If chosen, it is a human or licensed asset; nothing here composes music. | human |
| Speech / TTS | **Not needed. The film is wordless.** Higgsfield `generate_audio` is speech-only and is deliberately unused. | n/a |

**Mixer:** `fm audio mix` renders `AUDIO_CUES.yaml` to `12_post/audio/mix_48k_stereo.wav`.
- Deterministic Python with cues placed at sample offsets `round(frame × 2000)`.
- Uses numpy where available, with a pure-stdlib `wave` fallback (60 s stereo is small). numpy on Windows ARM64 must be checked in task A0.
- ffmpeg is used only for loudness measurement (`ebur128`/`loudnorm` analysis) and the final mux.
- Stems per layer are written for the human's listening review.

### 3.5 Sync check: `fm qa audio` (deterministic)

| Check | Rule |
|---|---|
| Coverage | Every `sound_sync` entry and every audible anim event has a cue within ±1 frame (1 frame = 41.7 ms; audio placed exactly, tolerance covers `offset_f` intent) |
| Bounds | Every cue lies inside its shot's frames, or is an explicit `bed` |
| Resolution | Every `sound` id exists in `audio.palette` and has an existing source file or recipe; licence known (else WARN before G7, FAIL before final) |
| Silence map | RMS over each `audio.silence_map` span is below the room-tone floor (e.g. -50 dBFS); the rendered track proves it |
| Ratchet phase | Rendered ratchet cue frames match `handle_top` events exactly |
| No forbidden content | Speech-band heuristics are unreliable, so instead: no cue in a library tagged `speech`; a manifest tag check |
| Duration | Mix length equals 1440 frames × 2000 samples = 2 880 000 samples exactly |
| Levels | Peak ≤ -1 dBFS, integrated loudness within ±1 LU of target, no clipping |
| Coverage of silence | Frames with no bed and no cue are flagged (usually a bug; the world is never digitally silent, except `SC03` post-blackout per canon) |

Creative judgment (does the hum death land, is it too funny, does the ratchet move you) is the human's, at G7. The qa-supervisor gets the cue sheet, not the audio, and reviews structure and canon compliance, not the sound.

---

## 4. Post-production planning

### 4.1 Colour and grade

- **No creative grade.** `look.style.texture_and_grain` allows no LUT beyond the palette and `look.style.glow` fixes the halo. The colour is already baked at render by the Standard view transform, and the spike verified hex fidelity.
- Post applies only the locked finish:
  1. **Glare/bloom.** In the Blender compositor at render time (needs the emission pass). Verify it in task A0, since the compositor was untested in the spike.
  2. **Grain.** Monochrome, 1.5 % luma amplitude, uniform. Applied in ffmpeg (`noise` filter, fixed seed, temporal) at assembly, for determinism and cheap re-application.
  3. **Vignette.** Optional at most 10 % (D5).
- `post_plan` records each as a step with parameters read from canon values, so changing `look.style.texture_and_grain` restales the assembly.

### 4.2 Titles and credits

- **This needs a human ruling (D2).** `tone.wordless` (LOCKED) says the invitation is the only readable text.
- Options:
  - **A. No on-screen text.** Title and credit go into file metadata and the description only. This is consistent with canon and needs no change request.
  - **B. A 3–4 s title/credit card outside the 60 s runtime.** It is not part of the story, but it is readable text. The creative-director must clarify whether `tone.wordless` covers a card, or the human approves a change request.
  - **C. Title card at the head, inside the runtime.** Rejected: it breaks the FADE IN into an opening on the car and the 60 s budget.
- **Recommendation: A for the picture-locked master, plus an optional B bumper delivered as a separate file** if festivals require a card.
- The brief says the confession happens "after the credits, in the viewer's head", so the credits are creatively expected. That is the argument for B, and why D2 is the human's call.

### 4.3 Final render settings

Changes proposed to `config/render_profiles.yaml` `final`. Human approves as D6.

| Setting | Current | Proposed | Why |
|---|---|---|---|
| Resolution | scale 1.0 | 1920×1080 | matches `camera.format` |
| Engine | EEVEE | EEVEE, pinned 5.2.x | look canon |
| Samples | 64 | 64 (measure; 32 may suffice for flat toon) | render time |
| Motion blur | true | **false** | cel/held-pose style; blur on a toon character smears the outline. Human decision. |
| Output | exr | 8-bit PNG sequence, Standard view transform | no grade headroom needed, EXR for 1440 frames is ~10 GB |
| Compositor | none | glare on emission | `look.style.glow` |
| Chunking | none | ≤ 48 frames per process, resume, one shot per job | Windows ARM colour corruption on long processes |
| Authorization | required | required (`fm authorize final-render`) | unchanged |

**Estimate:** 1440 frames at 5–12 s each (real sets are slower than the spike's simple scene) is about 2–5 hours of unattended render, chunked and resumable. Wall-clock cost is machine time, not human time.

### 4.4 Editing: EDL from the shot list

The shot table already defines the cut: hard cuts everywhere, shots butted in scene-then-shot order. So the "edit" is generated, not authored.

- `fm post edl` writes:
  - `12_post/EDIT.edl` (CMX3600, 24 fps non-drop);
  - `12_post/edit.ffconcat`;
  - `12_post/EDIT_PLAN.md`, a readable cut list.
- Contents: shot id, record in and out (from `frames.start`, `count`), source frames, transition, plus the head fade-in and 18-frame tail fade-out.
- The transitions come from the canon `camera.rhythm.transitions` value (`fade_in: head`, `fade_out.frames: 18`); nothing else may be a dissolve or wipe.
- **The FADE IN length is undefined.** "Length set by post" with no number, so a human decision (D7). Recommendation: 12 frames.
- **The carry-forward finding** ("~8-frame hold before the SC06 fade") is verified here. `SC06_SH010` reserves f64–82 for the fade after the hold, which makes the hold f24–63 minus the breath.
- The EDL is also the input for the human, if they want to finish in Premiere/Resolve. The `pr_*` Higgsfield tools are an option but out of scope for M6.

### 4.5 Assembly and export

- `fm post animatic`: playblast video + mixed audio muxed to `12_post/animatic.mp4` (silent M3 animatic `scripts/m3_animatic.py` becomes the base). This is the G7 review artifact.
- `fm post assemble` (after the final render): frames → ffmpeg with, in order, grain, optional vignette, fade in/out, audio mux → **master** `13_delivery/last_signal_master.mov` (ProRes 422 HQ or lossless H.264 in MKV, 1080p24, stereo 48 kHz 24-bit PCM).
- Delivery encodes: `last_signal_1080p.mp4` (H.264 High, ~12 Mbps, AAC 320 kbps, -16 LUFS, `+faststart`) and a small review proxy.
- `fm qa delivery` (ffprobe): resolution, fps exactly 24/1, frame count 1440 (±0), duration 60.000 s, audio 48 kHz stereo, loudness and true-peak, no black frames beyond the fades, checksum manifest.
- Files are gitignored. `13_delivery/MANIFEST.json` (hashes, settings, `fm` version, Blender version) is tracked and is a `render:delivery` derived node.

---

## 5. New agents, skills, commands, gates

### 5.1 Agents

| Agent | Phase | Tools | Writes |
|---|---|---|---|
| **animation-director** (extend) | ANIMATION | Read, Edit, Glob, Grep, Bash | `animation.vocab.*` canon proposals, `09_animation/*.anim.yaml`, `09_animation/ANIMATION_BIBLE.md` (short: movement philosophy, holds, timing rules). **Its old rule "edit only shot animation blocks" is replaced**: it never edits shot files again. |
| **sound-designer** (new) | ANIMATION_PREVIEW | Read, Edit, Glob, Grep, Bash | `canon/audio.yaml` proposals, `12_post/AUDIO_BIBLE.md`, `AUDIO_CUES.yaml`, recipes, recording and library asks (a list for the human) |
| **post-supervisor** (new, already in `models.yaml`) | ANIMATION_PREVIEW, POST | Read, Edit, Glob, Grep, Bash | `12_post/EDIT_PLAN.md`, `POST_PLAN.md`, delivery spec; runs `fm post *` |
| blender-td (extend) | ANIMATION_PREVIEW, FINAL_RENDER | Read, Glob, Grep, Bash | runs `fm blender frames|playblast|final`, `fm qa motion`, builder code under `blender/` |
| qa-supervisor (extend) | G7, G8 | Read + write `qa/reviews/` | `G7_REVIEW.md`, `G8_REVIEW.md`; reads contact strips and the cue sheet |

Every agent stays without the `Agent` tool and with the existing deny list. None can run `fm authorize`, `approve` or `reject`.

### 5.2 Skills

- `animation-design`: extend it (structured tracks, vocabulary, events, holds, the "no prose parsing" rule).
- `sound-design` (new).
- `post-production` (new).
- `blender-production`: extend it (frames, playblast, motion bake, chunking).
- `creative-review`: add G7/G8 rubric sections (motion coherence, sync, silence, sound vs canon).
- `continuity-check`: add prop-state continuity.

### 5.3 `fm` CLI additions

| Command | Purpose |
|---|---|
| `fm resolve` | now includes `motion` and `ui_timeline` (2.3) |
| `fm blender frames --frames/--every-key` | QA stills and contact strips |
| `fm blender playblast [--scope]` | video previews |
| `fm blender final [--scope] [--resume]` | chunked final render; refuses without authorization and the pin |
| `fm qa motion` | tiers 0 and 1 (2.7) |
| `fm audio synth [--id]` / `fm audio mix` | procedural sound library and cue mixer |
| `fm qa audio` | sync and level checks (3.5) |
| `fm post edl` / `animatic` / `assemble` / `export` | edit list, previews, master |
| `fm qa delivery` | ffprobe checks |
| `fm check anim` | alias for the animation validation rules |

Core changes: add `audio` and `edit` to `DERIVED_KINDS`; new artifact kinds; new `CONTRACTS` for ANIMATION, ANIMATION_PREVIEW, FINAL_RENDER, POST; `REVIEW_FOR_GATE` gains G7 and G8; `CANON_DOMAINS` and `ARTIFACT_OWNERS` updated. All tested.

### 5.4 `/film-*` commands

| Command | Phase | Does | Ends at |
|---|---|---|---|
| `/film-animate [scope]` | ANIMATION | animation-director writes the vocabulary then anim files; `fm validate`; `fm qa motion` tier 0; blender-td bakes and renders frames; fix loop | advance to ANIMATION_PREVIEW |
| `/film-playblast [scope]` | ANIMATION_PREVIEW | blender-td: frames, playblast, tier 1 motion QA, contact strips | report |
| `/film-audio` | ANIMATION_PREVIEW | sound-designer: audio canon, bible, cue sheet, synth; `fm audio mix`; `fm qa audio`; lists what the human must supply | report |
| `/film-post` | ANIMATION_PREVIEW | post-supervisor: EDIT_PLAN, POST_PLAN, EDL, animatic with audio; qa-supervisor G7 review; `fm submit` | **G7** |
| `/film-final [scope]` | FINAL_RENDER | after `fm authorize final-render` (human): blender-td runs chunked render, `fm qa` on frames; qa-supervisor G8 review; `fm submit` | **G8** |
| `/film-export` | POST | `fm post assemble/export`, `fm qa delivery` | delivery report |

CLAUDE.md is updated: the "animation, final render and post are not available yet" line is removed once each command lands.

### 5.5 Gates

**G7 Animation, audio and post plan** (redefined from "Animation preview"):
- **Covers:** ANIMATION and ANIMATION_PREVIEW artifacts. That is all `shot_animation` files, the ANIMATION_BIBLE, AUDIO_BIBLE, AUDIO_CUES, EDIT_PLAN, POST_PLAN, and the G7 review.
- **Locks:** domains `animation`, `audio`, plus a new `post` domain, if adopted (see below).
- **Phase contract before `fm submit`:**
  - an anim file for every shot, with `fm qa motion` having no FAIL;
  - `10_blender/playblast/film.mp4`;
  - `12_post/audio/mix_48k_stereo.wav` with `fm qa audio` having no FAIL;
  - `12_post/animatic.mp4`;
  - `EDIT.edl`.
- **The human reviews:** the animatic (picture and sound together), contact strips for flagged shots, the cue-sheet conflict list, and the unresolved licence list.
- **The human decides:** the D-decisions in 5.6.
- Approving it does not authorize the final render. That stays a separate `fm authorize final-render`.

**G8 Final render:**
- **Covers:** FINAL_RENDER (complete frame set, per-shot and film manifests). Locks nothing.
- **Contract:**
  - `fm authorize final-render` recorded;
  - all 1440 frames rendered with the pinned Blender;
  - `fm qa stills`-class checks and `fm qa motion` re-run on final frames;
  - the assembled master passes `fm qa delivery`;
  - no `UNKNOWN` licence (assets or audio), as ARCHITECTURE requires.
- **The human reviews:** a scrub of the master with sound, the G8 review, the licence table.

**Recommendation on POST and DELIVERY (small state-machine change, needs OK):** they currently have no gate. Either add a **G9 Delivery** gate closing POST, or fold the master into G8 by moving G8's close to POST. G9 is cleaner (frames approved, then the finished file approved) and costs about half a day plus tests. I recommend G9 but list it as decision D9.

### 5.6 Human decision points (all needed by G7)

| # | Decision | Recommendation |
|---|---|---|
| D1 | Score or no score | No underscore; only the ratchet, breath and diegetic sounds |
| D2 | Title and credits vs `tone.wordless` | A: no on-screen text in the 60 s master; optional B bumper as a separate file (needs a ruling or change request) |
| D3 | Loudness target | -16 LUFS, -1 dBTP |
| D4 | Rulings on the doc conflicts: `SC05_SH010` desk buzz vs "no vibration"; `SC04_SH070` chime vs "no UI sound"; glovebox lid `SC04_SH040` start state (closed) vs `SC04_SH010` crank "in the closed glovebox" | Follow the shot files; storyboard prose is superseded |
| D5 | Vignette on or off (at most 10 %) | Off, since it costs nothing to add later |
| D6 | Final render profile: motion blur off, PNG output, 64 samples | As proposed in 4.3 |
| D7 | FADE IN length | 12 frames |
| D8 | Ratify the pose and prop vocabulary (the enums), at G7 | Review the list once; it is short |
| D9 | Add gate G9 Delivery | Yes |
| D10 | Foley source: who records the breaths and picks the library files, and Hana's headphone track | Human, about 1.5 days spread over the audio work |

Also handled by the existing process: any **locked-canon change** that animation or audio work exposes goes through `fm change propose`, as before.

---

## 6. Task breakdown

**Owners:** **C** = Claude in the cloud workspace (`fm` core, schemas, agents, tests, no Blender). **CL** = Claude with the laptop's pinned Blender (builders, renders). **H** = Gökhan. Days are working days of focused effort *including* iteration and review loops, not raw generation time.

### Group A: Foundations (do first; blocks B–F)

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| A0 | Spike (like M3 step 0) on the laptop: sequence render timing (640 px and 1080p), compositor glare works headless, chunked process stability on Windows ARM, numpy availability, ffmpeg codecs | CL | none | 1 |
| A1 | `AnimationTracks` schema, `shot_animation` kind, ownership, validate rules (`ANIM_*`), JSON Schema export | C | none | 1.5 |
| A2 | Vocabulary canon file + shared enum module; test that canon names equal `poses.py` keys | C | A1 | 1 |
| A3 | Resolver: read anim files, `motion` block, `ui_timeline` expansion of `states_by_shot`, schema /2, deps and staleness, tests on all 38 rows | C | A1, A2 | 2 |
| A4 | Core plumbing: `DERIVED_KINDS`, phase contracts, `REVIEW_FOR_GATE`, gates G7/G8 redefinition (+ G9 if D9), roles/domains/owners, tests | C | none | 1.5 |

### Group B: Animation authoring (needs A1–A3)

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| B1 | animation-director skill and agent rewrite; propose the vocabulary from the 224 existing keys | C | A2 | 1 |
| B2 | Write 38 anim files (10 body-motion shots need care; ~28 are holds, props, UI, face and events); `fm stamp`, validate | C (agent) | B1, A3 | 2.5 |
| B3 | Human review of vocabulary and the 10 body-motion shots' timing (in playblast form) | H | B2, C-group | 0.5 |

### Group C: Builders (parallel with B once A2 is stable; laptop-bound)

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| C1 | Refactor `render_shot` into `assemble` / `rig` / `motion` / `render`; delete the prose regexes; joint rig and bake | CL | A3 | 4 |
| C2 | `poses.py`: geometry for ~22 Ren and ~6 Hana presets, face shape swaps, `look` aiming; gait generators (run, scramble, crank_turn) | CL | C1 | 4 |
| C3 | Prop animators: door, lid, crank, headphones, pencil, mirror, car_body presets, dash and shop lights, phone-screen state switching from `ui_timeline` | CL | C1 | 3 |
| C4 | Camera animation (2 shots) and frame rendering: `frames`, `playblast`, chunking, resume, stamp overlay, contact strips, compositor glare | CL | C1, A0 | 3 |

### Group D: Motion QA (partly parallel)

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| D1 | `fm qa motion` tier 0 (timing, vocab legality, prop continuity across shots, speed, camera cap, running time, UI rules) and tests | C | A3 | 2 |
| D2 | Tier 1: bake report and checks (foot slip, drift, attach, reach, canon geometry, idempotence) | CL | C2, C3 | 1.5 |
| D3 | Vision review pass on contact strips + iteration fixes (builder vs spec problems) | CL / C | C4, D1 | 2 |

### Group E: Audio (parallel with C/D once A4 and the events convention are set)

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| E1 | sound-designer agent, `sound-design` skill, `audio` canon, AUDIO_BIBLE | C | A4 | 2 |
| E2 | Synth library: UI sounds, ring, chime, hums, ratchet, clunk (about 1.5 days); car starter, cough, sigh, stall (about 2 days) | C | E1 | 3.5 |
| E3 | Human supplies and records: library files (CC0 with licences), breaths and body foley, Hana's headphone track | H | E1 (asks list) | 1.5 |
| E4 | AUDIO_CUES.yaml for 38 shots; event-referenced cues; conflict list | C (agent) | E1, B2 (events) | 1.5 |
| E5 | `fm audio mix` (sample-exact placement, beds, stems), `fm qa audio` | C | E4 | 3 |
| E6 | Listening review loops with the human: mix and synth tweaks | H + C | E5 | 1.5 |

### Group F: Post

| # | Task | Owner | Depends | Days |
|---|---|---|---|---|
| F1 | post-supervisor agent and skill, EDIT_PLAN, POST_PLAN | C | A4 | 1 |
| F2 | `fm post edl` (CMX3600 + ffconcat) and `fm post animatic` (playblast + mix), tests | C | C4, E5 | 2 |
| F3 | `fm blender final` (chunked, resume, authorization, pin) | CL | C4 | 2 |
| F4 | `fm post assemble/export` (grain, vignette, fades, mux, loudnorm, encodes) and `fm qa delivery` | C | F2 | 3 |
| F5 | G7/G8/G9 reviews and rubric, docs (`ANIMATION.md`, `AUDIO.md`, `POST.md`, COMMANDS/AGENTS/SKILLS/CLAUDE.md) | C | all | 2 |
| F6 | The **final render run** (unattended) and G8 review | CL + H | F3, G7 approved | machine time 2–5 h; 0.5 day human |

### Dependencies and parallel lanes

```
A0 ─────────────────────────────────────────────┐
A1 → A2 → A3 ──┬─ B1 → B2 ─────────────┐         │
A4 ────────────┼─ E1 → E2 ─┐           │         │
               │   E3(H) ──┤            ▼         ▼
               ├─ C1 → C2,C3 → C4 → D2 → D3 ──→ [/film-post → G7]
               ├─ D1 (needs A3, B2 for full run)
               └─ F1                    E4 → E5 → E6 ─┘   F2 → F4
                                                    G7 → authorize → F3/F6 → G8 → F4 export
```

**Parallelisable groups:**
- **Lane 1, cloud (C):** A1–A4 first, then B1–B2, D1, E1, E2, E4, E5, F1, F2, F4 (no Blender needed).
- **Lane 2, laptop (CL):** A0, then C1–C4, D2, D3, F3.
- **Lane 3, human (H):** E3 and the D-decisions can start as soon as E1 produces the asks list and the decision list. B3 and E6 are review points.
- The two Claude lanes meet at D3 (fixes) and F2 (animatic).

### Effort, honestly

- **Core development effort:** about **36–40 working days** as listed. Of that, roughly 20 days are cloud-side (`fm`, agents, tests, synth, mixer, post tooling) and about 16–18 days are laptop-bound Blender work.
- **Calendar with two lanes running:** about **5–6 weeks** to G7. A2 to C1 and C1 to C2 are the critical path, so the joint-rig refactor is where slippage will show.
- **Human time:** about 5–6 days spread across decisions, foley, listening and review. D10 (recording and sourcing sound) is the piece nobody else can do.
- **Realism check for 60 seconds.** The work is dominated by four things, not by animating 1440 frames: (1) the rig and pose-preset refactor (C1, C2), (2) prop and UI timelines, (3) the procedural sound library, and (4) Blender iteration on Windows ARM. A 60 s wordless film with 32 held shots is a favourable case. A film with sustained walking or acting would multiply C2 and B2 several times over.
- **Cheaper cut (M6-lite, about 22 days):**
  - keep the pose vocabulary to ~12 Ren and 4 Hana presets;
  - animate body motion only in the ~10 shots that need it, holding the poses elsewhere;
  - synthesise UI and hum sounds only and use the human's phone recordings for everything else;
  - do not build G9, grain and vignette in the compositor, or the delivery encodes beyond one master and one MP4.
- The final render itself is machine time (2–5 h unattended) and belongs to F6, after G7 and `fm authorize final-render`. M6 can be declared done at G7 with F3/F4 tested by a dry run on 2–3 shots. Running the full final render and G8/G9 is then a one-off follow-up (call it M6b).

---

## 7. Acceptance criteria

1. `09_animation/*.anim.yaml` exists for all 38 shots; `fm validate` has 0 errors; every ref is in the ratified vocabulary; no builder code path reads prose from `animation` (a test greps `blender/` for the removed functions and fails if present).
2. `fm resolve` produces `motion` and `ui_timeline` for every shot, deterministically (second run changes nothing). Editing one anim file re-resolves only that shot.
3. `fm blender playblast` on the pinned Blender produces the silent film (1440 frames, 24 fps) with frame stamps. Rebuilding one shot changes only that shot's keyframe hash.
4. `fm qa motion` has no FAIL across tiers 0 and 1. Known WARNs are listed in the G7 review.
5. `fm audio mix` produces a 2 880 000-sample stereo file; `fm qa audio` has no FAIL; every `sound_sync` line and audible event has a cue within ±1 frame; the silence map is provably silent.
6. `12_post/animatic.mp4` plays picture and sound together, and `EDIT.edl` matches the resolved frame table exactly.
7. G7 is decided by the human at a terminal, with the D-decisions recorded via `--notes`.
8. A dry-run final render of 3 shots on the pinned Blender, assembled with grain, fades and audio, passes `fm qa delivery`.
9. All new `fm` logic has tests (resolver, vocab, QA, mixer, EDL, phase contracts); all M1–M5 tests still pass; Blender-side tests run on the laptop.
10. Docs updated: `docs/ANIMATION.md`, `docs/AUDIO.md`, `docs/POST.md`, and the COMMANDS, AGENTS, SKILLS, WORKFLOW, ARCHITECTURE and CLAUDE.md edits.

---

## 8. Risks

- **Windows ARM EEVEE colour corruption in long processes.** Mitigation: chunks of ≤ 48 frames per process, resumable, and a checksum sample of each chunk compared with the first frame's histogram. A0 measures the real safe chunk size.
- **Render time.** Real sets are slower than the spike's test scene. If the estimate is off by 3x, the playblast is still under 4 h and the final about 15 h. Fallbacks: lower samples, per-shot Cycles never, playblast at 480 px.
- **Joint-blend look.** Blending joint positions instead of solving IK can pop elbows and knees on long blends. The 8 % limb-drift check catches it. The known weak spot is `SC04_SH040`'s 0.7 m glovebox reach at the proxy arm limit (already flagged in `risks_m3`). Fallback is a two-bone analytic solve for arms only, planned as a contingency task of 1.5 days.
- **Proxy face.** Held-pose expressions are the plan, but the face may not carry Hana's smile (the M3 risk). The character bible has three fallback stagings. M6 does not change the face system beyond swapping the existing control shapes.
- **Procedural sound quality.** UI and hum synthesis works well. Engine cough, sigh and stall may sound artificial, and no listener test can be automated. The human's ear is the gate. Fallback: a recorded or CC0 engine sample for those three cues.
- **Human dependency.** Foley recording, library licensing and the score decision all block audio at G7, and only the human can do them. The asks list is produced early (E1) to allow parallel work.
- **numpy on Windows ARM64** may not be available. The stdlib fallback mixer exists but is slower.
- **Compositor glare headless** is untested (the spike did not cover it). A0 verifies it. Fallback: bake the glow as an emissive-only blur pass in ffmpeg (gblur on a mask), which is looser than the canon's 1.5 % rule and would need a change request.
- **Vocabulary churn.** If the human changes the vocabulary after B2, every affected anim file restales (as designed). The vocabulary is therefore ratified at the start of B (B3 review of the list and 10 shots), not at G7, to avoid late rewrites. G7 locks it formally.
- **G5 already DRIFTED.** Not caused by M6, but G7 approval requires every earlier gate healthy. Clear the G5 drift first (`fm amend` or re-approve), or G7 cannot be approved.

---

## 9. Deliberately out of scope

- Real character rigs: armatures, IK, weight painting, MPFB/VRM providers, mocap import. The rig here is joint-baked proxies.
- Lip sync and any dialogue, TTS or voice work (the film is wordless; `lip_sync: false`).
- Cloth, hair, crown-tuft physics and any simulation (the tuft is one bone with a keyed overshoot).
- Music composition or generation (no tool available; a score is a human or licensed asset).
- Surround or immersive audio, Dolby, HDR, DCP, festival packaging beyond one master and one web encode.
- A creative colour grade or LUT (locked out by `look.style.texture_and_grain`).
- Motion blur, depth-of-field animation, camera shake (`static` and dolly-in only).
- Captions or subtitles (nothing is spoken; the only text is the invitation, which is on screen).
- A render farm or cloud rendering; final rendering runs on the laptop.
- Editing alternatives, multiple cuts, versioned edits, or a timeline UI. The EDL is derived from the shot table.
- Re-doing G1–G5 creative decisions. Anything animation or audio exposes about them goes through `fm change propose`.

---

### Critical Files for Implementation

- `/home/claude/film_maker/core/fm/resolve.py`
- `/home/claude/film_maker/blender/fm_blender/preview.py`
- `/home/claude/film_maker/blender/fm_blender/characters.py`
- `/home/claude/film_maker/core/fm/phases.py`
- `/home/claude/film_maker/core/fm/schemas/artifacts.py`

### Notes for the main session (nothing saved to memory from here)

- Stated by the user's own project docs and worth remembering for later sessions on FILM_MAKER:
  - M6 is planned around sidecar `09_animation/<shot>.anim.yaml` artifacts, so the G5-approved shot files are not edited.
  - The film is wordless, and Higgsfield `generate_audio` is speech-only, so it does not apply to this film.
  - The 10 open human decisions D1–D10 above.
