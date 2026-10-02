---
fm:
  id: post_plan
  kind: post_plan
  phase: ANIMATION_PREVIEW
  status: PROPOSED
  owner_role: post-supervisor
  derived_from:
  - ref: artifact:edit_plan
    hash: sha256:603fceb0350f0917493700d2933af04ee80a6f1fb7d3df24631ae22509efab4a
  - ref: artifact:audio_cues
    hash: sha256:3938a7a3ff047e56c4d85dde64f08d16b8f308bdb1e5bb0064e56cd56af0ac76
  - ref: artifact:creative_direction
    hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
  - ref: canon:look.style.texture_and_grain
    hash: sha256:544d2906507dbfac6969ea7ce0b48e5a8978571267e475fc5f86fcfc2ab71698
  - ref: canon:look.style.glow
    hash: sha256:894609d6570cb3d925e8a7697aa0cc2bcb14b26910712173ab394d4c9bc4d087
  - ref: canon:look.style.render_constraints
    hash: sha256:5ff198e989a3e2bfe6217768a89180fee793f10f9c349cccdf50a71f00958c0e
  - ref: canon:look.style.phone_ui
    hash: sha256:5b1bcd7579ec10d43bbfefbd045d981b00248cbbc4ca45550862e8c0df97c0e6
  - ref: canon:camera.format
    hash: sha256:2501c716273516ebe3e4dba470a0e8896aff0761fda6926bbb09cfc7bad1eeea
  - ref: canon:camera.rhythm.transitions
    hash: sha256:0ff059c432a2227bfbe4eebceef37bc953cd834328d87d7ae75970a866ddcb15
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:world.rules.no_readable_text
    hash: sha256:a21cccd660b3af6cffb29094f0fab852e3e2fe1bd316dd2e7dcb094615bad1ae
  - ref: canon:audio.mix
    hash: sha256:dd10c4767db381b6a23ee351aaa51e12de78423dbb6b8a527d92e9be707484b6
  serves:
  - intent.soft_but_cinematic
  - intent.anime_feel
  - intent.open_hopeful_ending
  summary: Locked finish steps with parameters read from canon (glare, grain, optional vignette, fades),
    titles ruling, final render settings, delivery spec, licence status; D1-D10 carried as recommended
    rulings (register in 12_post/DECISIONS.md), UNKNOWN until the human rules at G7.
  stamped_content_hash: sha256:792d0f041d41cab704ad327a10b46bbcad0aeb848e7f6861d86ffd260f3aeb7f
  stamp_note: 2026-10-02 evening refresh after the G5 fixes and the laptop rebuild (6c0b9b2) - section
    7.5 (mix and EDL byte-identical; new animatic not in this checkout, unprobed), licence counts per
    the current audio report, risk 1
title: Post Plan
---
# Post Plan: Last Signal

Post adds only the finish the look canon locks. There is no creative grade. Every parameter below is
read from a canon value and names its source, so a canon change restales this plan.

## 0. Delegated decisions (recommended rulings, 2026-10-02)

FACT (as relayed to post by the main session): the human delegated all open decisions D1-D10 to the
production team (2026-10-01 "hepsini sen belirle"; repeated 2026-10-02). The full register, with rationale
and rejected alternatives, is `12_post/DECISIONS.md`. Every item is a **RECOMMENDED RULING** with status
**UNKNOWN until the human rules** at G7; where this plan says "DECISION Dn" below, read "recommended ruling
Dn, not human-approved".

| # | Recommended ruling | Where | Canon already decides? |
|---|---|---|---|
| D1 | No underscore (sound-designer domain; no post step) | DECISIONS | Proposed: `audio.score` (PROPOSED) |
| D2 | No on-screen titles or credits, in or around the master; title and credits travel as delivery metadata (MANIFEST.json, delivery description). No bumper. | 3 | Yes, in effect: `tone.wordless` and `world.rules.no_readable_text` (LOCKED) |
| D3 | -16 LUFS integrated (+-1 LU), true peak <= -1 dBTP, 2-pass loudnorm; plus a 3 dB post-turn bed duck in the mix (sound-designer; applied in the 2026-10-02 mix) | 5 | Proposed only: `audio.mix` (PROPOSED) carries these values, and `fm post` now reads them; approving it is the human's step |
| D4 | Shot files win over storyboard prose (all `audio.conflicts` items) | DECISIONS | Proposed (ASSUMPTION): `audio.conflicts` |
| D5 | Vignette off | 2.3 | No (canon allows 0-10 %) |
| D6 | `final` profile as it stands: EEVEE, 1920x1080, 64 samples, no motion blur, 8-bit PNG, 48-frame chunks, authorization required; glare from the emission pass per `look.style.glow` | 4 | Partly: format, engine, view transform, motion blur and glare are LOCKED canon |
| D7 | FADE IN 12 frames | 2.4 | No (`fade_in: head`, no length) |
| D8 | Ratify vocab v1 + v2; `face.ren` only together with CHANGE-005 | DECISIONS | Proposed: `animation.vocab.*` |
| D9 | Add a G9 Delivery gate after G8 | 5 | No (state machine) |
| D10 | Human records body sounds; CC0/own library foley with written licences; headphone leak dropped (SC05 room tone only; applied in the 2026-10-02 mix) | 6 | Proposed: `audio.sources` `music_assets: none (D10)`, `audio.score` (PROPOSED) |

## 1. Order of operations (POST phase, after G8)

`11_render/final/<SHOT>/%04d.png` (glare already applied in the Blender compositor at render)
-> grain -> [vignette, only if D5 = on] -> FADE IN / FADE OUT -> audio mux (loudness D3) -> master
-> delivery encodes -> `fm qa delivery` -> `13_delivery/MANIFEST.json`.

FACT: `fm post assemble` implements this order (`core/fm/post.py`: "[grain] -> [vignette] -> fades ->
audio (loudnorm 2-pass) -> mezzanine"). Grain and vignette are **off by default** in the tool. The POST
command line must pass `--grain` explicitly (section 2.2).

## 2. Finish steps (parameters read from canon)

### 2.1 Glare (render time, not assembly)
- Source: `look.style.glow` (LOCKED). `glow_sources: emissives_only`, `max_radius_pct_frame_width: 1.5`
  (= 28.8 px at 1920 wide), `streaks: false`, `star_glare: false`, `ghosts: false`, `bokeh_discs: false`,
  `implementation: compositor_glare_bloom_on_emission_pass`.
- DECISION: applied in the Blender compositor at final render (owner: blender-td), not in post.
  Rejected: a post bloom in ffmpeg (it cannot isolate emissives without the emission pass).
- FACT (commit 5e7d6e1): the glare is implemented in `blender/fm_blender/finish.py`, final renders only
  (draft, preview, frames and playblast never call it). `glare_params` reads `look.style.glow` from the
  resolved film canon: BLOOM on the `fm_glow` emission AOV, `size` = 1.5 % of frame width (28.8 px at 1920),
  the halo masked off the emitter itself. It refuses (and `fm blender final` refuses "final render refused")
  if canon asks for anything it does not implement (streaks, star glare, ghosts, another implementation or
  source). `core/fm/finalrender.py` records the canon-derived glare in the render settings. FACT:
  `pytest tests/test_finish.py tests/test_post.py` 31 passed (2026-10-02, this environment, no Blender).
- UNKNOWN: not yet verified headless in the pinned Blender on the laptop (M6 task A0: "compositor glare works
  headless"). No final frame exists (`11_render/` absent). Risk 4 is reduced, not closed.

### 2.2 Grain (assembly)
- Source: `look.style.texture_and_grain` (LOCKED). `grain.type: monochrome`, `amplitude_luma: 0.015`,
  `uniform_across_film: true`.
- DECISION: applied at assembly by `fm post assemble --grain`. The tool reads `amplitude_luma` from canon
  (`finish_params`) and builds ffmpeg `noise` on luma only, temporal, with a fixed seed (1337) so the
  result can be reproduced. Rejected: baking grain in Blender (it cannot be re-applied without a
  re-render, and it doubles the risk of wrong colour on the Windows ARM machine).
- ASSUMPTION: the mapping from 0.015 to ffmpeg's `c0s` strength gives about 1.5 % luma amplitude. Nobody
  has measured this yet. Verify on one final shot at POST (difference of graded and ungraded frame, std
  of luma) before the full assembly.

### 2.3 Vignette (optional, D5)
- Source: `look.style.texture_and_grain` `vignette_max: 0.1` ("the same on every shot").
- **DECISION D5: vignette off** (`fm post assemble` without `--vignette`). Delegated by the human 2026-10-01;
  to be ratified at G7. Rationale: the composition and lighting canon already place light and value; the
  phone inserts carry the battery pip and status icons near the corners, which a vignette would darken
  (`intent.race_against_battery`); and it can be added later at assembly (`--vignette 0..0.1`) with no
  re-render, so "off" closes no doors. Rejected: 10 % on (dims the insert corners for a framing the shots
  already do); a per-shot vignette (canon forbids it: "the same on every shot").

### 2.4 Fades
- FADE OUT: 18 frames at the tail, after the final-image hold. Source: `camera.rhythm.transitions`
  `fade_out.frames: 18` (LOCKED). Record 1422-1439 (see EDIT_PLAN section 3).
- **DECISION D7: FADE IN 12 frames** (record 0-11). Delegated by the human 2026-10-01; to be ratified at G7.
  Canon says `fade_in: head` with no length. Rationale and rejected alternatives (24 and 0/6 frames) are in
  EDIT_PLAN section 1. FACT: `fm post edl` and `fm post assemble` already use a code default of 12 ("default
  (M6_SCOPE D7 recommendation)"), so the EDL, ffconcat and animatic are unchanged and were not regenerated.
  DEPENDENCY: to move the value from code into canon, the human would adopt a `post` domain with
  `post.fade_in` (the tool already reads it). Post does not create that domain.
- Audio follows picture: the sound fades in and out over the same frames (EDIT_PLAN section 5).

### 2.5 Not applied (canon forbids)
- FACT, `look.style.texture_and_grain`: `chromatic_aberration: false`, `extra_lut: false`, no sharpening.
  FACT, `look.style.render_constraints`: Standard view transform, look None, exposure 0, gamma 1. The
  colour is final at render. Post applies no grade, LUT, sharpening or CA. Any request for one is a
  change request against look canon.

## 3. Titles and credits (D2)

- FACT: `tone.wordless` (LOCKED, USER_REQUIREMENT): "The typed English dinner invitation is the ONLY
  readable text in the film." `world.rules.no_readable_text` (LOCKED) says the same.
- FACT: CREATIVE_DIRECTION says "The confession happens after the credits, in the viewer's head", so
  credits are expected creatively. This question has been open since G1 (G1 review item 1; G4 review
  finding 11).
- Options considered:
  - **A. No on-screen text in the 60 s master.** The title and credits go in the file metadata
    (title, artist, comment) and in the delivery description. Consistent with canon; no change request.
  - **B. A 3-4 s title/credit card as a separate bumper file**, outside the 60 s runtime and never cut
    into the master. It is readable text, so the human must rule whether `tone.wordless` covers a card
    outside the story, or approve a change request scoping it to story frames.
  - **C. Title card inside the runtime (head or tail).** Rejected: it breaks the FADE IN onto the car
    (or the held final image and the fade to black), and it spends frames the LOCKED budget does not have.
- **DECISION D2: A.** No on-screen title or credits in the master and no bumper. The title ("Last Signal")
  and the credits go in `13_delivery/MANIFEST.json` and the delivery description. Delegated by the human
  2026-10-01; to be ratified at G7. Rationale: canon already decides this: `tone.wordless` is a LOCKED
  USER_REQUIREMENT ("the typed English dinner invitation is the ONLY readable text in the film"). Keeping the
  invitation the only words the viewer ever reads is what lets it land at the send
  (`intent.race_against_battery`, `intent.open_hopeful_ending`). CREATIVE_DIRECTION's "after the credits, in
  the viewer's head" describes where the confession happens, not an on-screen credit card. Rejected: B (a
  bumper is still readable text; a delegated post call cannot reinterpret the scope of the human's own locked
  requirement, so a card needs the human's ruling or a creative-director change request if a festival ever
  demands one); C (breaks the FADE IN onto the car or the held final image, and spends frames the LOCKED
  budget does not have).
- DEPENDENCY: `fm post assemble`/`export` strip container metadata (`-map_metadata -1`); a container title
  tag would need a tool option. MANIFEST.json and the delivery description are enough for D2.

## 4. Final render settings proposal (D6)

FACT: `config/render_profiles.yaml` `final` reads (re-read 2026-10-02; committed, `git status` clean):
`engine: BLENDER_EEVEE`, `resolution_scale: 1.0`, `samples: 64`, `motion_blur: false`,
**`output: png`**, **`chunk_frames: 48`**, `requires_authorization: true`.

| Setting | Current `final` | Proposed | Source / reason |
|---|---|---|---|
| Resolution | scale 1.0 | 1920x1080, scale 1.0 | FACT `camera.format` `resolution_px: [1920, 1080]` |
| Frame rate | (from scene) | 24/1 | FACT `camera.format` `fps: 24` |
| Engine | EEVEE | EEVEE, Blender pinned 5.2.x | FACT `look.style.render_constraints` `engine: eevee` |
| View transform | (builder) | Standard, look None, exposure 0, gamma 1 | FACT `look.style.render_constraints` |
| Samples | 64 | 64 | DECISION (D6). Unmeasured; 64 is the safe side for the soft light-radius shadows and the 1.5 % glow halo, at an estimated 2-5 h for the film. Rejected: 32 now (cheaper but untested on the real sets; adopt later only after a 3-shot comparison, recorded as a change) |
| Motion blur | false | false | FACT: `look.style.render_constraints` (LOCKED) says `motion_blur: false`; the profile matches. Not a D6 question. |
| Output | png | 8-bit PNG sequence, RGB | FACT: the profile now says `png`, matching this proposal; `fm blender final` refuses any other output ("set output: png"), because `fm post assemble` reads `%04d.png`. Rejected: EXR (about 10 GB for 1440 frames, no grade needs the headroom). |
| Compositor | (builder, final only) | glare on the emission pass | FACT `look.style.glow` `implementation` (LOCKED). FACT (2026-10-02): implemented in `blender/fm_blender/finish.py`, parameters read from canon, final-only (section 2.1). UNKNOWN: headless verification on the laptop's pinned Blender (A0) not yet recorded (risk 4) |
| Chunking | 48 frames per process | at most 48 frames per process, resumable | FACT: profile `chunk_frames: 48`; `fm blender final` reads it (override `--chunk-frames`) and has `--resume`. Reason: colour corruption in long Blender processes on Windows ARM (M6 scope 4.3). |
| Authorization | required | required: `fm authorize final-render` by the human | FACT: `fm blender final` "REFUSES without the human's `fm authorize final-render`", and refuses shots the recorded authorization's scope does not cover |

- FACT: the final render tool exists: `fm blender final` renders every frame to `11_render/final/<SHOT>/NNNN.png`
  in chunks, then `MANIFEST.json`; route `exe` (pinned Blender) is the only one G8 accepts. It needs the
  human's `fm authorize final-render` in the ledger first. Post never runs `fm authorize` or `fm blender final`.
- **DECISION D6: the `final` profile as it stands** (table above): EEVEE, scale 1.0 = 1920x1080, 64 samples,
  no motion blur, 8-bit PNG, 48-frame resumable chunks, authorization required; glare from the emission pass
  as `look.style.glow` locks it. Delegated by the human 2026-10-01; to be ratified at G7. Rationale: every
  look-bearing setting is already fixed by LOCKED canon (`camera.format`, `look.style.render_constraints`,
  `look.style.glow`); the open fields are chosen for reproducibility on this machine (PNG feeds
  `fm post assemble` directly; 48-frame chunks avoid the Windows ARM colour corruption) and a clean first
  pass (64 samples). Rejected: EXR output (about 10 GB, no grade needs the headroom); motion blur on (canon
  forbids it; it smears the cel outline and the phone number); 32 samples without a test.
- FACT: no config change was needed. `config/render_profiles.yaml` already carries these values, and
  `git status` (2026-10-01) shows the file unmodified, so they are committed. Glare is not a profile field:
  it comes from canon through the builder.
- DEPENDENCY (blocks the final render, not the decision): verify the now-implemented compositor glare headless
  on the laptop's pinned Blender (blender-td, M6 task A0), e.g. on one insert shot with a lit screen. D6
  authorizes nothing: the human still runs `fm authorize final-render` before `fm blender final` will start.
- ASSUMPTION: 1440 frames at 5-12 s each is about 2-5 hours of unattended rendering (M6 scope estimate,
  not measured on the real sets).
- Post never runs `fm authorize` or `fm blender final`.

## 5. Delivery spec

| File | Spec | Built by |
|---|---|---|
| `13_delivery/last_signal_master.mov` (mezzanine) | ProRes 422 HQ (`prores_ks` profile 3), 1920x1080, 24/1, 10-bit 4:2:2, BT.709 tv range; stereo 48 kHz 24-bit PCM; exactly 1440 frames, 60.000 s | `fm post assemble` |
| `13_delivery/last_signal_1080p.mp4` (web) | H.264 High, about 12 Mbps, yuv420p, AAC 320 kbps 48 kHz stereo, `+faststart` | `fm post export` |
| review proxy | small H.264 for review | `fm post export` (unless `--no-proxy`) |
| `13_delivery/MANIFEST.json` | files, sha256, probe facts, settings, `fm` and Blender versions (tracked in git) | `fm post export` |
| title and credits (D2 = A) | text fields in `MANIFEST.json` and the delivery description; no on-screen card, no bumper | `fm post export` / delivery description |

- FACT: ffmpeg 6.1.1 in this environment has `prores_ks`, so the tool would write `.mov`. Without ProRes
  it falls back to lossless-ish H.264 in `.mkv`. ASSUMPTION: the assembly machine has the same encoder.
- **DECISION D3: -16 LUFS integrated (+-1 LU), true peak <= -1 dBTP**, 2-pass loudnorm, 48 kHz 24-bit stereo.
  Delegated by the human 2026-10-01; to be ratified at G7. Rationale: the web/mobile norm, and the quiet
  ending and the clunk/ratchet transients keep their dynamics (`intent.soft_but_cinematic`,
  `intent.comic_then_tender`). Rejected: -14 LUFS (louder, and
  platforms turn it down anyway, at the cost of the tender half's range); -23 LUFS / EBU R128 (right for
  broadcast, far too quiet on phones and laptops). FACT: `audio.mix` now exists as **PROPOSED** canon
  (sound-designer: `integrated_lufs: -16.0`, `lufs_tolerance: 1.0`, `true_peak_dbtp: -1.0`, 48 kHz, 24-bit,
  stereo, `decision: D3`): the same values. Approving it is the human's step at G7; post proposes no further
  canon. FACT (`qa/audio_report.json`, 2026-10-02 mix): integrated -16.5 LUFS (ffmpeg ebur128), true peak
  -1.1 dBTP, inside the proposed target; the report reads its targets from `audio.mix`.
- FACT (D3 duck applied, sound-designer, 2026-10-02): `audio.mix` now carries
  `post_turn_street_bed_offset_db: -3.0`, `post_turn_from: SC04_SH040`; the mix has `bed_SC04_street_pre_turn`
  at -21 dB (816-934) and `bed_SC04_street_turn` / `bed_SC06_street` at -24 dB from 930. Whether the turn now
  reads as level is a G7 listening judgement. Fallback if it still sounds flat: -20 LUFS, which changes only
  the `audio.mix` `integrated_lufs` value. Rationale and rejected alternatives in `12_post/DECISIONS.md`.
- FACT (tool fix, commit 5e7d6e1): `core/fm/post.py` `finish_params` now reads `integrated_lufs`,
  `true_peak_dbtp` and `lufs_tolerance` from `audio.mix` (constants only as fallback for a film without the
  entry); `fm post assemble` loudnorm, the export manifest (`loudness_target.source`) and `fm qa delivery` use
  them. A canon change to D3 now reaches the master.
- `fm qa delivery` checks (all must PASS at POST): 1920x1080; exactly 24/1 fps; 1440 frames (+-0); duration
  60.000 s; audio 48 kHz stereo; integrated loudness within +-1 LU of target; true peak <= -1 dBTP; black
  only inside the fades; checksums match the manifest.
- DEPENDENCY: the master and the encodes are gitignored. Only `MANIFEST.json` is tracked.
- **DECISION D9: add a G9 Delivery gate** (frames approved at G8; the finished master, the encodes, an
  all-PASS `fm qa delivery` report and a cleared licence table approved at G9). Delegated by the human
  2026-10-01; to be ratified at G7. Rationale: G8 judges pictures before grain, fades, loudness and encoding
  exist; a separate gate makes "the file is right" a human approval and gives the licence blockers
  (section 6) a gate to clear at. Rejected: folding the master into G8 (mixes two approvals and lets a file
  ship on a frame approval).
- DEPENDENCY: G9 is an `fm` state-machine change (main session / tool owner), not a post edit. Until it
  lands, post treats an all-PASS `fm qa delivery` and zero UNKNOWN licences as the release condition.

## 6. Licence status (blocks final export while UNKNOWN)

| Item | Where used | Source | Licence | Blocks export |
|---|---|---|---|---|
| breath (placeholder) | SC01_SH040/090/130/150, SC02_SH020, SC03_SH040, SC04_SH030/050-090, SC06_SH010 | to be recorded by the human | UNKNOWN | **yes** |
| sigh (placeholder) | SC01_SH060 | to be recorded | UNKNOWN | **yes** |
| nose laugh (placeholder) | SC05_SH030 | to be recorded | UNKNOWN | **yes** |
| foley: footsteps, knees/kerb, shop door, pencil down, phone on chest (`fx.soft_bump` placeholder, 4 asks, 11 files) | SC02_SH010-030, SC03_SH010, SC04_SH040, SC05_SH020, SC06_SH010 | library files, human picks | UNKNOWN | **yes** |
| foley: seat creak, jacket cloth, pencil stroke, headphones slide, phone lift (`fx.plastic_scuff` placeholder, 1 ask, 5 files) | SC01_SH060, SC04_SH040, SC05_SH020 | library files, human picks | UNKNOWN | **yes** |
| street bird | SC01_SH010, SC01_SH150 | library file | UNKNOWN | **yes** |
| distant traffic, distant car pass (optional ask, 2 files) | SC03_SH070, SC04_SH010, SC06_SH010 | library files | UNKNOWN | **yes** if used; the synth `amb.distant_car_pass` stands in meanwhile |
| headphone leak music | (none) | FACT: removed from the 2026-10-02 mix per the D10 recommended ruling (SC05 is `bed_SC05_hana_room` only; `audio.sources` `music_assets: none (D10)`); `fm qa audio` lists it as "not needed" | not used | no, while the human upholds D10 at G7; if D10 is overruled it returns as a blocker |
| phone UI font | typed invitation, numbers (`look.style.phone_ui` `font: open_licence_humanist_sans`) | not yet chosen (Noto Sans / Inter suggested) | UNKNOWN (canon notes: "Font licence UNKNOWN until verified") | **yes** |
| procedural sound recipes (`fm audio synth`) | all other cues | generated in-house | ASSUMPTION: own work, no third-party licence. To be confirmed by the sound-designer's registry | no, if confirmed |
| 3D assets, sky | all shots | built procedurally, no `library/assets` in use (the directory is empty) | FACT: nothing third-party found | no |

- FACT: `qa/audio_report.json` (2026-10-02) lists 11 human-supply rows, `human_supply_open: 10` (the 11th is
  the dropped headphone leak, status DECLINED), all licence UNKNOWN; the table above groups them. Counted by
  target file name in those rows (post count, 2026-10-02 evening): **32 files** still to supply, 13 body
  recordings by the human (11 breaths, 1 sigh, 1 nose laugh) and 19 library foley/ambience files (2 of them,
  the distant traffic pair, optional). The figure "15 human-supply item(s)" in 7.3 is the 2026-10-01 count of
  rows, before the cue sheet grouped them; it is superseded. 5 placeholder recipes remain in the mix (22 breath
  cues on `body.breath_placeholder`). The mix was not changed by the G5 fixes (7.5), so neither was this table.
- RECOMMENDATION: `fm post export` is not run for release until every UNKNOWN above is resolved. An
  animatic with placeholders is fine for G7 review.

## 7. Animatic (rebuilt 2026-10-01)

### 7.1 Why the G7 review found a 47-frame animatic
- FACT: the 2026-10-01 14:43:21 `fm post animatic` run (`.fm/logs/fm.log`) was interrupted about 3 s in.
  The tool wrote straight to `12_post/animatic.mp4`; on interruption ffmpeg's input closed and it finalised
  a valid but short file (47 frames, 1.958 s: SC01_SH010 and the first 7 frames of SC01_SH020), replacing
  the full wave-6 animatic. No error was recorded because the process never reached its own check.
- FACT, tool fix (`core/fm/post.py` `build_animatic`): the encode now goes to `12_post/.animatic.partial.mp4`
  and replaces `animatic.mp4` only after ffprobe confirms exactly `total_frames`; an interrupt kills ffmpeg
  and deletes the partial file. Regression test `test_interrupted_animatic_never_replaces_the_existing_one`.
- FACT, second fix found on the way (`_shot_frame_files`): `10_blender/frames/<SHOT>/` holds sparse
  `--every-key` frames plus a `strip.png` contact sheet. The tool used to play the keys back to back as
  consecutive frames and then hold `strip.png` (the contact sheet) for the rest of the shot. It now reads
  only `NNNN.png`, places each at its frame index and holds it until the next key. Test
  `test_sparse_key_frames_are_step_held_and_strip_ignored`.

### 7.2 This run
FACT, `fm post animatic` output: "`12_post/animatic.mp4`: 60.000 s, 1440 frames @ 24.0 fps, 1280x720, audio:
yes, 29 shots from frames, 9 from stills". ffprobe (`-count_frames`): video h264 1280x720, 24/1,
nb_read_frames 1440, 60.000000 s; audio aac 48000 Hz, 2 channels, 60.000000 s.

What it is and is not:
- **Picture is mixed (38 shots).**
  - 14 shots play every frame from the `10_blender/playblast/` sequences: SC01_SH010-SH050 and
    SC01_SH070-SH150. ASSUMPTION (by file date): these playblasts (2026-09-30) predate the 2026-10-01 vocab-v2
    anim migration, so their motion may not match the current anim files.
  - 15 shots step-hold v2 draft key frames from `10_blender/frames/` (1 to 9 keys each): SC01_SH060,
    SC02_SH010, SC03_SH010-SH070, SC04_SH050-SH090, SC05_SH020. They show key poses at the right frames,
    not continuous motion. SC01_SH060 uses its draft keys, not its older full playblast (frames dir first).
  - 9 shots are single preview stills held for their duration (timing and order only, no motion):
    SC02_SH020, SC02_SH030, SC04_SH010-SH040, SC05_SH010, SC05_SH030, SC06_SH010.
- **Sound is the 2026-10-01 mix** (`12_post/audio/mix_48k_stereo.wav`, 1440 x 2000 samples), with the
  placeholders listed in section 6, re-rendered late 2026-10-01 after the upstream restamp (see 7.3).
- **No fades.** The animatic does not apply the head and tail fades.
- So it is a full-length but **partial-motion** G7 review artifact: 24 of 38 shots lack full motion
  (15 key-held, 9 stills). Rebuild with `fm post animatic` once playblasts exist (blender-td).

FACT, `fm qa delivery projects/last_signal/12_post/animatic.mp4` (report `qa/delivery_report.json`), quoted
summary line: "1 delivery file(s): 1 FAIL, 2 WARN finding(s) (1 row(s) failing)". The command exits non-zero on FAIL.
- FAIL: resolution 1280x720, render canon says 1920x1080. **Expected**: the animatic is a preview-size
  review file (`--size` default 1280x720), not a delivery file.
- WARN: first frame is not black although a fade-in is specified; WARN: last frame is not black although
  a fade-out is specified. Expected for an animatic without fades.
- Passing: 24/1 fps, 1440 frames, 60.0 s, 48 kHz stereo audio of the right length, integrated loudness
  -16.5 LUFS (within +-1 LU of -16), true peak -1.8 dBTP.
- Tool fix (wave 6): the summary used to count files with a FAIL or WARN, not findings. It now counts
  findings, and keeps the per-file counts as `files_failing` / `files_warning` (`core/fm/post.py`
  `delivery_summary`). `fm qa audio` had the same bug and got the same fix.

### 7.3 Re-run after the SC04 cable posing and the SC03_SH010 restamp (2026-10-01, late)
- FACT: AUDIO_CUES restamped without content change (all anim event ids/frames identical; see EDIT_PLAN 2.2).
  `fm audio synth` not run: `fm audio mix` renders the recipes itself and no recipe changed.
- FACT, `fm audio mix`: "mixed 138 placement(s) -> 12_post/audio/mix_48k_stereo.wav (2880000 samples ...)",
  "peak -1.74 dBFS, true peak -1.73 dBTP, ~-16.39 LUFS (suggested mix.master_gain_db: 21.7)"; `mix_report.json`
  identical to the previous one. FACT, `fm qa audio`: "audio: 0 FAIL, 10 WARN (66 sync point(s); 15
  human-supply item(s) still needed)"; the 10 WARN are the 5 placeholder recipes, each reported twice.
- FACT, `fm post animatic`: "60.000 s, 1440 frames @ 24.0 fps, 1280x720, audio: yes, 29 shots from frames,
  9 from stills". ffprobe: h264 1280x720 24/1 nb_frames 1440; aac 48000 Hz 2 ch; duration 60.000000. Picture
  sources as in 7.2 (same 14 playblast, 15 key-held, 9 still shots). The SC04_SH010 still predates the
  cable posing (`render:preview_SC04_SH010` STALE), so the posed cable is not visible in the animatic.
- FACT: `fm qa delivery` with no argument: "0 delivery file(s): 2 FAIL" (`13_delivery` has no files and no
  MANIFEST.json). Expected: nothing is delivered before G8. FACT, `fm qa delivery
  projects/last_signal/12_post/animatic.mp4`: "1 delivery file(s): 1 FAIL, 2 WARN finding(s) (1 row(s)
  failing)": the same expected 1280x720 FAIL and no-fade WARNs as 7.2; loudness -16.5 LUFS, true peak
  -1.8 dBTP. Note the report file `qa/delivery_report.json` holds the animatic run (the last one).

### 7.4 Status 2026-10-02: animatic STALE, not rebuilt here
- FACT: `fm validate` lists `edit:animatic` STALE (resolved SC01 shots changed). `12_post/animatic.mp4` is dated
  2026-10-01 21:37; the 2026-10-02 mix (`mix_48k_stereo.wav`, 13:14) with the D3 duck and D10 is newer, so the
  animatic's sound predates both. Its SC01 picture predates the lens/layout commits (fba52bf, 0ac12ba), and
  its SC03 keys predate the blackout luma spec (0.12).
- DECISION (procedural): `fm post animatic` was **not run** in this environment. The pinned frames and
  playblasts live on the human's laptop; here the tool would fall back to stills and overwrite the
  animatic with a worse one.
- Required: re-render the SC01 (and stale SC03/SC04_SH010) frames/playblasts on the laptop (blender-td), then
  `fm post animatic` there, then `fm qa delivery projects/last_signal/12_post/animatic.mp4` and ffprobe, and
  update section 7. Until then, the G7 animatic has the old mix and old SC01 framing; no claim about the new
  animatic is made here. (Superseded in part by 7.5: the laptop has now rebuilt it.)

### 7.5 Laptop rebuild after the G5 fixes (commit 6c0b9b2, 2026-10-02 evening)
- FACT (ledger records pushed in 6c0b9b2): on the human's laptop `fm audio mix` (2026-10-02T19:44:10Z,
  `audio:mix` hash `dec4205c...`), `fm post edl` (19:44:11Z, `edit:edl` `e8b5c6cb...`) and `fm post animatic`
  (19:44:46Z, `edit:animatic` `9ce5d06b...`) were re-run after the pinned previews were re-rendered (38 preview
  PNGs and `qa/playblast_sheet.jpg` updated in the same commit).
- FACT: in this checkout `sha256(12_post/audio/mix_48k_stereo.wav)` = `dec4205c...` and `sha256(12_post/EDIT.edl)`
  = `e8b5c6cb...`: the mix and the EDL are byte-identical to the laptop's. The G5 fixes changed no timing
  (EDIT_PLAN 2.5) and no cue anchor (AUDIO_CUES review note), which is consistent.
- FACT: `12_post/animatic.mp4` is gitignored (`.gitignore:18`), so the laptop's new animatic did **not** arrive
  with the push. The file here is the 2026-10-01 21:37 build, sha256 `dda75883...`, which matches no current
  record. ffprobe of that local file (`-count_frames`): video h264 1280x720, `r_frame_rate` 24/1, nb_read_frames
  1440, 60.000000 s, yuv420p; audio aac 48000 Hz, 2 channels, 60.000000 s. These describe the **old** build only.
- FACT: `qa/delivery_report.json` was not re-run on the laptop (record `qa:delivery` 2026-10-01T18:37:55Z): it
  still describes the old animatic (1 FAIL, 1280x720, expected for a review file; 2 WARN, no fades; -16.5 LUFS,
  true peak -1.8 dBTP after AAC). FACT, `qa/audio_report.json` (2026-10-02T10:15Z, on the same mix bytes as
  now): integrated -16.5 LUFS (ffmpeg ebur128), true peak -1.1 dBTP, sample peak -1.14 dBFS, targets -16.0
  +-1.0 LU / -1.0 dBTP read from `audio.mix`; 0 FAIL, 10 WARN; 66 sync points; 3 silence windows at the floor.
- UNKNOWN: the frame count, duration, picture sources (frames / playblast / stills per shot) and AAC loudness
  of the laptop's `9ce5d06b` animatic. Not verified here; no claim is made. Required before G7 review: on the
  laptop, `ffprobe -count_frames 12_post/animatic.mp4` and `fm qa delivery projects/last_signal/12_post/animatic.mp4`,
  then commit `qa/delivery_report.json`; or copy the `.mp4` into this checkout and run both here. Expected
  (not yet observed): 1440 frames, 60.000 s, 24/1, 1280x720 (`--size` default), the same expected FAIL/WARNs.

## 8. Risks

1. The animatic was rebuilt on the laptop after the G5 fixes (7.5), but that file is not in this checkout and
   has not been probed or `fm qa delivery`-checked by post; its picture sources (how many shots play motion
   vs held keys/stills) are unknown here. The 2026-10-01 build had 24 of 38 shots without full motion.
   Owners: the human (copy or probe on the laptop), blender-td.
2. D6 is decided (delegated, to be ratified at G7), but the final render still needs the glare verified on
   the laptop (risk 4) and the human's `fm authorize final-render`, which `fm blender final` requires.
3. The grain amplitude mapping has not been measured (2.2). If it is wrong, the grain is too strong or
   too weak on every frame. Verify on one shot first.
4. Compositor glare is implemented (final-only, read from `look.style.glow`) but not yet verified headless in
   the pinned Blender on the laptop (A0). If it silently no-ops there, LOCKED `look.style.glow` is missing from
   every final frame. Verify on one shot before the full render. Owner: blender-td.
5. D7 still comes from a code default, and D3 from PROPOSED (not LOCKED) canon `audio.mix`. The loudness
   key defect is fixed (2026-10-02, section 5): `fm post` now reads `integrated_lufs`, `true_peak_dbtp` and
   `lufs_tolerance` from `audio.mix`.
6. UNKNOWN licences (section 6) block release, and the font one also blocks the final render of the
   insert shots.
7. G5 is DRIFTED. A different re-approved shot timing moves every record frame here. Regenerate by
   `fm resolve` -> `fm post edl` -> re-stamp.
