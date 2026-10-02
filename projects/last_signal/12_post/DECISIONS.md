---
fm:
  id: post_decisions
  kind: post_decisions
  phase: ANIMATION_PREVIEW
  status: PROPOSED
  owner_role: post-supervisor
  derived_from:
  - ref: artifact:edit_plan
    hash: sha256:603fceb0350f0917493700d2933af04ee80a6f1fb7d3df24631ae22509efab4a
  - ref: artifact:post_plan
    hash: sha256:792d0f041d41cab704ad327a10b46bbcad0aeb848e7f6861d86ffd260f3aeb7f
  - ref: artifact:audio_bible
    hash: sha256:496cfd2ebec66ea0b0ca6909a80422696583b6e6f27a0bc247532550c5f48293
  - ref: artifact:animation_bible
    hash: sha256:95b1aa19a882987694b707feff5e6dc66faa17dd50c9b0507f231ce0fd7eddd4
  - ref: artifact:g7_review
    hash: sha256:667d747da0b93242a8d4b6d42a3623d279caab4252ed239338cb768cd55bcd23
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:tone.the_turn
    hash: sha256:653b9a834c3b4f01813d471792c37227f6b7476e3a4d314cc4792b6e51f5b361
  - ref: canon:world.rules.no_readable_text
    hash: sha256:a21cccd660b3af6cffb29094f0fab852e3e2fe1bd316dd2e7dcb094615bad1ae
  - ref: canon:camera.rhythm.transitions
    hash: sha256:0ff059c432a2227bfbe4eebceef37bc953cd834328d87d7ae75970a866ddcb15
  - ref: canon:camera.format
    hash: sha256:2501c716273516ebe3e4dba470a0e8896aff0761fda6926bbb09cfc7bad1eeea
  - ref: canon:look.style.texture_and_grain
    hash: sha256:544d2906507dbfac6969ea7ce0b48e5a8978571267e475fc5f86fcfc2ab71698
  - ref: canon:look.style.glow
    hash: sha256:894609d6570cb3d925e8a7697aa0cc2bcb14b26910712173ab394d4c9bc4d087
  - ref: canon:look.style.render_constraints
    hash: sha256:5ff198e989a3e2bfe6217768a89180fee793f10f9c349cccdf50a71f00958c0e
  - ref: canon:audio.score
    hash: sha256:ce4ecd489ab13d322a77d749e27db91f1ba564de8273e004da6eb19510253dd2
  - ref: canon:audio.mix
    hash: sha256:dd10c4767db381b6a23ee351aaa51e12de78423dbb6b8a527d92e9be707484b6
  - ref: canon:audio.conflicts
    hash: sha256:6ed601c6debe4079741c5088600614a0437e50428fc5b79880ed65368bcec11b
  - ref: canon:audio.sources
    hash: sha256:646f49fa76f35f969f1b383ce098be7ea6f28b2af12890e8a43a53929d53d2ef
  - ref: canon:animation.vocab.v2
    hash: sha256:8b44ad00375ed7ae85539a9a9a04da4c190036ce937433a27570ff25ad8a3942
  - ref: canon:animation.vocab.v2.face.ren
    hash: sha256:6131d42bb63b44ebbeb5ccfcab9d117e271f486759f2f5560c047d714c091660
  - ref: canon:animation.vocab.v2.prop.charging_cable
    hash: sha256:06b0072b9573eef18df3d2f731f6e3084dcdb24b98ec49369b9f6a3834def2bc
  - ref: canon:characters.ren.expressions
    hash: sha256:e59d1a65dbde02bb2660940e2e4c2a1a973d1088acce3d766cec064b3cd676d3
  - ref: canon:continuity.props.cable
    hash: sha256:4db888d6dba86f7106b088e7c7eac2a8a32c3a74f2bc925a7269d8fa39d1fc0b
  serves:
  - intent.soft_but_cinematic
  - intent.earned_last_signal
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  summary: Recommended rulings on open decisions D1-D10 (plus the G7 side questions), each with rationale
    and the rejected alternative, prepared under the human's delegation; every ruling is UNKNOWN until
    the human confirms it at G7.
  stamped_content_hash: sha256:835096d3b75e20cefe986a34966b7982f439fc087f61f2041acd640017ea4e2f
title: Open decisions D1-D10 — recommended rulings
---
# Open decisions D1-D10 — recommended rulings

FACT: the human delegated all open decisions to the production team (2026-10-01 "hepsini sen belirle", and
again on 2026-10-02 as relayed by the main session). Each item below is a **RECOMMENDED RULING**, not a
decision. Agents cannot approve anything: every ruling has status **UNKNOWN until the human rules**, at G7 or
with the command named. The definitions of D1-D10 are those of `docs/M6_SCOPE.md` (decision table) and
G7 review "Open human decisions".

Selection test for every item: the option that best serves the locked intents — wordless
(`tone.wordless`), no score unless the documents argue otherwise, `intent.soft_but_cinematic`, and
`intent.earned_last_signal` — at the least downstream churn.

## Summary

| # | Question | Recommended ruling | Changes a value? | Status |
|---|---|---|---|---|
| D1 | Score | No underscore; ratchet + breath + diegetic sound only | No (`audio.score` already says so) | UNKNOWN |
| D2 | Titles and credits vs `tone.wordless` | A: no on-screen text in or around the master; title and credits as delivery metadata | No | UNKNOWN |
| D3 | Loudness | -16 LUFS integrated (+-1 LU), true peak <= -1 dBTP; plus a 3 dB post-turn bed duck | Duck applied in the 2026-10-02 mix (sound-designer) | UNKNOWN |
| D4 | Doc conflicts (`audio.conflicts`, ASSUMPTION) | Shot files win, all 3 D4 items and the 4 extras as written | No | UNKNOWN |
| D5 | Vignette | Off | No | UNKNOWN |
| D6 | Final render profile | `final` as it stands: EEVEE 1920x1080, 64 samples, no motion blur, 8-bit PNG, 48-frame resumable chunks, authorization required | No | UNKNOWN |
| D7 | FADE IN length | 12 frames (0.5 s) | No | UNKNOWN |
| D8 | Ratify the vocabulary | Ratify v1 + v2 entire, with `face.ren` ratified only together with CHANGE-005 | No | UNKNOWN |
| D9 | Delivery gate | Add G9 Delivery | No (tool change) | UNKNOWN |
| D10 | Foley, breaths, headphone track | Human records body sounds; human picks CC0/own library foley with written licences; SC05 headphone leak dropped (room tone only) | Yes: leak already removed from the 2026-10-02 mix and the export blockers | UNKNOWN |

## D1 — Score

- **RECOMMENDED RULING: no underscore.** The film has no non-diegetic music; the crank ratchet and Ren's
  breath are the score (`audio.score`, PROPOSED, value `underscore: none`).
- Rationale: the 1 Hz ratchet phase-locked to the crank gait (`audio.ratchet`) is already a pulse the
  audience feels; music would tell them what to feel at the very point `intent.earned_last_signal` needs
  them to hear his effort. No document argues for a score.
- Rejected: a light comic cue before the turn (pushes toward the manic register `tone.anti_goals`
  excludes); a tender cue at the send (saccharine, and it would bury the last click at SC04_SH090 f7).

## D2 — Titles and credits

- **RECOMMENDED RULING: option A.** No on-screen title or credits in the 60 s master and no bumper file. The
  title ("Last Signal") and credits travel in `13_delivery/MANIFEST.json` and the delivery description.
- Rationale: `tone.wordless` (LOCKED, USER_REQUIREMENT) makes the typed invitation "the ONLY readable text in
  the film"; `world.rules.no_readable_text` (LOCKED) agrees. Keeping it the only words the viewer reads is
  what lets it land at the send. A delegated call cannot reinterpret the scope of the human's own locked
  requirement, and A needs no change request.
- Rejected: B, a 3-4 s title/credit bumper outside the runtime (still readable text; needs the human's own
  ruling on scope or a creative-director change request against `tone.wordless`); C, a card inside the
  runtime (breaks the FADE IN onto the car or the held final image, and spends frames the LOCKED
  `camera.rhythm.scene_budget` does not have).
- If a festival later demands a card, that is a change request then, not now.

## D3 — Loudness

- **RECOMMENDED RULING: -16 LUFS integrated (+-1 LU), true peak <= -1 dBTP**, 2-pass loudnorm, 48 kHz 24-bit
  stereo — the values `audio.mix` (PROPOSED) already carries. **Plus** a dependency for the sound-designer:
  lower the street beds from SC04_SH040 (the turn) to the end by 3 dB relative to the pre-turn beds, so the
  tender half sits audibly quieter inside the same integrated target.
- Rationale: the film is a 60 s web/mobile short; -16 LUFS is the web norm, and most web video platforms (YouTube among
  them) turn loud files down but do not turn quiet ones up, so a quieter master plays quieter than everything around it on a
  phone speaker, where the breaths would vanish. G7 review #11 and AUDIO_BIBLE section 8 show the real
  problem is relative, not absolute: at -16 the post-turn street bed sits at the same RMS as the comic car
  (SC01 about -21 to -22 dBFS, SC04 about -21.8 to -22.7 dBFS), so `tone.the_turn` ("quiet") is not yet
  audible as level. A relative duck fixes the turn without moving the delivery target
  (`intent.soft_but_cinematic`, `intent.comic_then_tender`).
- Rejected: -20 LUFS (about 19 dB peak-to-loudness headroom, but about 4 dB under neighbouring content on
  every web platform, and it still would not make the tender half quieter than the comic half); -14 LUFS
  (louder, crushes the clunk and coughs against the -1 dBTP ceiling, and platforms turn it down anyway);
  -23 LUFS / EBU R128 (broadcast spec, far too quiet on phones).
- Fallback, for the human's ears at G7: if after the duck the turn still does not feel quieter, take
  -20 LUFS instead; post changes only the loudnorm target.
- FACT (2026-10-02, sound-designer): the duck is applied. `audio.mix` (PROPOSED) carries
  `post_turn_street_bed_offset_db: -3.0` from `SC04_SH040`; the mix places the pre-turn SC04 bed at -21 dB and
  the turn and SC06 beds at -24 dB; `fm qa audio`: -16.5 LUFS integrated, true peak -1.1 dBTP. Whether the turn
  reads as level is for the human's ears at G7.
- FACT (tool fix, commit 5e7d6e1): `core/fm/post.py` `finish_params` now reads `integrated_lufs`,
  `true_peak_dbtp` and `lufs_tolerance` from `audio.mix`, so a non-default D3 (e.g. the -20 LUFS fallback)
  reaches the master and `fm qa delivery`.

## D4 — Documented conflicts (`audio.conflicts`, ASSUMPTION)

- **RECOMMENDED RULING: the shot files win over STORYBOARD prose**, exactly as `audio.conflicts` lists:
  SC05_SH010 no desk buzz; SC04_SH070 no chime, ratchet only; glovebox lid closed at SC04_SH040 f0 with a
  soft latch at `lid_latch` f24. The four extras likewise: SC04_SH060 ratchet stays 24 f through the hover;
  SC04_SH080 ratchet keeps clicking under the tick and stops at SC04_SH090 f7; SC01_SH150 very soft bump at
  `forehead_contact`; SC01_SH020 soft tap kept on the cut at f0.
- Rationale: the shot files were approved at G5 and carry the frame-exact sync; each ruling keeps a canon
  rule intact: no buzz keeps "the light is what reaches her" (`intent.open_hopeful_ending`); no chime at
  1 % -> 2 % keeps the gain his, not the phone's (`intent.earned_last_signal`); the closed lid keeps LOCKED
  `continuity.props.glovebox_and_crank`; the steady ratchet keeps the phase lock.
- Rejected: resolving toward the storyboard prose (contradicts approved shots and locked continuity; a
  slower ratchet in SH060 or a stop under the tick breaks the pulse the turn rides on).
- Optional follow-up (G7 review #15): promote the SC01_SH020 tap to an anim `ui_event` so it is
  event-anchored, not frame-anchored (animation-director).
- Effect of approval: approving `audio.conflicts` turns the ASSUMPTION into canon; the human may add
  `--notes "D4 ruled: shot files win"` when deciding.

## D5 — Vignette

- **RECOMMENDED RULING: off** (`fm post assemble` without `--vignette`).
- Rationale: composition and lighting canon already place light and value; the phone inserts carry the
  battery pip and status icons near the frame corners, which a vignette would darken
  (`intent.race_against_battery`); and it can be added at assembly (`--vignette 0..0.1`) with no re-render,
  so "off" closes no door.
- Rejected: 10 % on (dims the insert corners for a framing the shots already do); per-shot vignette (canon
  forbids it: "the same on every shot").

## D6 — Final render profile

- **RECOMMENDED RULING: `config/render_profiles.yaml` `final` as it stands**: EEVEE, `resolution_scale 1.0`
  (1920x1080, 24/1 from `camera.format`), 64 samples, `motion_blur: false`, `output: png` (8-bit RGB,
  Standard view transform from `look.style.render_constraints`), `chunk_frames: 48` with `--resume`,
  `requires_authorization: true`; glare from the emission pass per `look.style.glow` (LOCKED).
- FACT: no config change is needed; every look-bearing field is fixed by LOCKED canon, and the profile
  already matches.
- Rationale: PNG feeds `fm post assemble` directly (it reads `%04d.png`); 48-frame chunks avoid the Windows
  ARM long-process colour corruption; 64 samples is the safe side for the soft shadow radii and the 1.5 %
  glow halo on a first pass.
- Rejected: EXR (about 10 GB, no grade needs the headroom, assembly does not read it); motion blur on
  (canon forbids it; it smears the cel outline and the battery number); 32 samples without a 3-shot test
  (adopt later only after a recorded comparison).
- FACT (commit 5e7d6e1): compositor glare on the emission pass is now implemented
  (`blender/fm_blender/finish.py`, final renders only, parameters read from `look.style.glow`; `fm blender
  final` refuses if canon asks for more than it implements). Unit tests pass in this environment.
- DEPENDENCY (blocks the render, not the ruling): verify it headless in the pinned Blender on the laptop
  (blender-td, M6 task A0). D6 authorizes nothing: the human still runs `fm authorize final-render` before
  `fm blender final` will start.

## D7 — FADE IN length

- **RECOMMENDED RULING: 12 frames (0.5 s)**, record 0-11, sound fading in over the same frames.
- Rationale: half a second lets the hand already moving at f0 arrive out of black (soft,
  `intent.soft_but_cinematic`) and clears before the mirror gag reads (`intent.comic_then_tender`).
  FACT: `fm post edl` (re-run 2026-10-02) prints "fade in 12 / out 18 frames"; the EDL is unchanged.
- Rejected: 24 frames (eats more than half of the 40-frame opening shot and buries the gag set-up);
  0 or 6 frames (a snap open, harsher than the soft register).
- DEPENDENCY: the value lives in a code default. A canon home (`post.fade_in`, which the tool already reads)
  needs the human to adopt a `post` canon domain; post does not create it.

## D8 — Ratify the animation vocabulary (v1 + v2)

- **RECOMMENDED RULING: ratify all 18 PROPOSED `animation.vocab.*` entries (v1 + v2) at G7**, with one
  condition: `animation.vocab.v2.face.ren` (`wary`, `determined`) is ratified **only together with
  CHANGE-005** (PROPOSED, target `characters.ren.expressions`, filed by the character-designer), so the
  locked character canon and the vocabulary agree.
- Rationale: the vocabulary is the contract 38 anim files, `fm qa motion` and the builder already obey
  (38 shots: 0 FAIL); v2 renames nothing (`no_renames: true`). `wary` and `determined` carry the
  expectation half of the SC03 wary gag and the reset of freeze-sag-reset (`intent.comic_then_tender`),
  and both stay illegal from SC04_SH030, so the tender half is untouched. CHANGE-005 also writes into
  locked canon that `focused_calm` keeps level brows, which is what G7 review #4 needs the builder to fix.
- Rejected: reverting the four keys (SC01_SH060 f18, SC02_SH010 f0, SC03_SH020 f0, SC03_SH030 f0) to
  `neutral` (legal, but loses the gag's set-up and the reset); ratifying `face.ren` without CHANGE-005
  (vocabulary would contradict LOCKED `characters.ren.expressions`).
- Note on `animation.vocab.v2.prop.charging_cable`: its `chain_by_shot` text still says `loose hidden` for
  SC04_SH010-SH040, while the anim files now key `posed` (ANIMATION_BIBLE 7.2, after G7 review #10).
  RECOMMENDED side ruling: the cable is **posed** in SC04_SH010-SH040 (LOCKED `continuity.props.cable`
  allows only "most of its length" off screen). Ratify the entry with a note; the animation-director
  corrects the value text at the next revision (v3).
- Known gap, not ratified by D8: no thumb/hand track for SC04_SH020/SH060 (G7 review #8;
  ANIMATION_BIBLE 7.3 option B is a v3 proposal after G7).
- FACT (ANIMATION_BIBLE, G5-fix revision 2026-10-02): the bible now records a DECISION that a `phone` or `all`
  hold freezes the phone's world position **and facing** (used by SC03_SH020), plus the delegated SC01_SH090
  thumb and SC03_SH020 head-cover rulings. None of these adds or renames a vocabulary name: the hold scopes
  are already in `animation.vocab.event_kind`, and SC03_SH020's new `phone_still` event uses the existing
  `visual` kind. So the D8 recommendation is unchanged; the hold semantics are a bible/builder rule, which the
  human may want written into the vocabulary at v3 (animation-director).

## D9 — Delivery gate

- **RECOMMENDED RULING: add a G9 Delivery gate** after G8: frames approved at G8; the finished master, the
  encodes, an all-PASS `fm qa delivery` report and a cleared licence table approved at G9.
- Rationale: G8 judges pictures before grain, fades, loudness and encoding exist; a separate gate makes "the
  file is right" a human approval and gives the licence blockers a gate to clear at.
- Rejected: folding the master into G8 (two approvals in one; a file could ship on a frame approval).
- DEPENDENCY: `fm` state-machine change (A4, main session / tool owner). Until then post treats an all-PASS
  `fm qa delivery` and zero UNKNOWN licences as the release condition.

## D10 — Foley, breaths and the headphone track

- **RECOMMENDED RULING:**
  1. **The human records** Ren's breaths (about 16 takes), the sigh and Hana's nose-laugh (phone recording,
     48 kHz), licence `own`. These cannot be substituted: the placeholders are audibly noise, and they carry
     the whole crank sequence.
  2. **The human picks library foley** (footsteps pavement/shop, knees and body, cloth, seat creak, pencil,
     headphones slide, phone handling, street bird, distant traffic), **CC0 or own recordings only**, each
     with `library/audio/<id>/asset.yaml` stating the licence and source URL. Agents may shortlist
     candidates; the human downloads and confirms the licence.
  3. **Hana's headphone leak is dropped: SC05 is room tone only** (the fallback in AUDIO_BIBLE section 7, item 5).
- Rationale: (1) the tender half lives on the breath (`intent.earned_last_signal`); (2) CC0/own keeps the
  licence table clearable without legal review; (3) no music anywhere keeps D1 absolute, removes the one
  licence that needs negotiation, and leaves SC05 to "the light is what reaches her"
  (`intent.open_hopeful_ending`), with the nose-laugh as the scene's only voice-like sound.
- Rejected: synthesising body sounds (read as fake, break the tenderness); attribution-licensed library
  files (CC-BY needs a credits line, which D2 keeps off screen; usable only if the metadata credit is
  accepted); a licensed lyric-free track for the leak (licence cost and risk for 3-5 s that sits under the
  film's softest beat).
- FACT (2026-10-02, sound-designer, ahead of the ruling): the leak is out of the mix (SC05 is
  `bed_SC05_hana_room` only), `audio.sources` (PROPOSED) says `music_assets: none (D10)`, and `fm qa audio`
  lists the leak as "not needed". POST_PLAN section 6 no longer counts it as a blocker. If the human overrules
  D10 it returns to the mix and the blocker list. The `headphones_slide` foley stays (a prop sound, not music).
- Time (M6 scope estimate): about 1.5 human days.

## Other G7 rulings the human was asked for (recommended)

- **Scene budget vs SCENES.yaml (G7 #12):** LOCKED `camera.rhythm.scene_budget` is the authority; SCENES.yaml
  `est_duration_s` stays an estimate (all drifts inside 15 %). Rejected: editing SCENES.yaml (drifts G2 for
  no on-screen change). Status UNKNOWN.
- **Cable in SC04_SH010-SH040 (G7 #10):** posed (see D8 note). Status UNKNOWN.

## Human commands (none run by agents)

- Change request: `fm change approve CHANGE-005` (before or with G7) — required for the D8 ruling as written.
- Canon still PROPOSED (39 per `fm canon list`, 2026-10-02 evening), for `fm canon approve <id>` — note that approving G7 locks every PROPOSED
  `animation.*` and `audio.*` entry in one step (G7 review, `decide_gate to_lock`), so individual approvals
  are only needed to rule ahead of the gate:
  - animation (18): `animation.vocab.breath`, `animation.vocab.ease`, `animation.vocab.event_kind`,
    `animation.vocab.face`, `animation.vocab.gait`, `animation.vocab.look_target`,
    `animation.vocab.pose.hana`, `animation.vocab.pose.ren`, `animation.vocab.prop_states`,
    `animation.vocab.ui_event`, `animation.vocab.v2`, `animation.vocab.v2.face.ren`,
    `animation.vocab.v2.lids`, `animation.vocab.v2.pose.hana`, `animation.vocab.v2.pose.ren`,
    `animation.vocab.v2.prop.charging_cable`, `animation.vocab.v2.prop.shop_door`,
    `animation.vocab.v2.prop_state.hidden`
  - audio (10): `audio.conflicts`, `audio.mix`, `audio.motifs`, `audio.palette`, `audio.perspective`,
    `audio.principles`, `audio.ratchet`, `audio.score`, `audio.silence_map`, `audio.sources`
  - look (11): `look.color.ui_portraits`, `look.lighting.sc03_blackout_render`,
    `look.lighting.sc03_sh070_style_break` (new with the G5 fixes: the SC03_SH070 light-link style break),
    `look.style.phone_screen.call`, `look.style.phone_screen.compose`, `look.style.phone_screen.geometry`,
    `look.style.phone_screen.hana`, `look.style.phone_screen.map`, `look.style.phone_screen.sent`,
    `look.style.phone_screen.states_by_shot`, `look.style.phone_screen.status_bar`
