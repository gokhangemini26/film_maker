---
fm:
  id: edit_plan
  kind: edit_plan
  phase: ANIMATION_PREVIEW
  status: PROPOSED
  owner_role: post-supervisor
  derived_from:
  - ref: artifact:shot_list
    hash: sha256:92b3bcc6a1e21d96ab99793feca0f3a485f4dd5eb8713306e20fa1161705c27a
  - ref: artifact:scenes
    hash: sha256:137da02c736eaa6e9e9e5d0e0288b49020e337d14fbb636cb1797ee1d002461b
  - ref: artifact:audio_cues
    hash: sha256:ad57b77535192c291ed921e797e542e8ca319119171c92379f36852d9ccc433a
  - ref: canon:camera.rhythm.transitions
    hash: sha256:0ff059c432a2227bfbe4eebceef37bc953cd834328d87d7ae75970a866ddcb15
  - ref: canon:camera.rhythm.scene_budget
    hash: sha256:3a0f9e8b633e6af955192a0d459cd316fdbb721ce25b920263219195e0cd943f
  - ref: canon:camera.rhythm.pace
    hash: sha256:159ba88fec689f71013a9b320634dd92231e1355c17de392979a90a0479b8b30
  - ref: canon:camera.format
    hash: sha256:2501c716273516ebe3e4dba470a0e8896aff0761fda6926bbb09cfc7bad1eeea
  - ref: shot:SC01_SH010
    hash: sha256:451ee18abe337cfe8beac674b76d40a4822a78cfec4b4f5bf9ba095201b23135
  - ref: shot:SC03_SH010
    hash: sha256:1f76a5f9b1d9f67b45b4d32494cd8fa297d0e56eeec18ea1eaacf0bb5c82e63f
  - ref: shot:SC03_SH070
    hash: sha256:c943fa8776bee45915f96d41d7cbb2c060a78f6a93e0cee3910c79ca39dff1fd
  - ref: shot:SC04_SH090
    hash: sha256:ba37458305d5c99080be0a44998f4f3680a91d45b3f9a2c2106e97e19ae494d8
  - ref: shot:SC05_SH010
    hash: sha256:ca697fb6681d099dddf3be0b8126b615fb84abfee75495b95672debdc91a0413
  - ref: shot:SC05_SH030
    hash: sha256:fe59950a5823efe8c8ad34c1a74192a78ea62fa7a90efb08872e242264b7d7b3
  - ref: shot:SC06_SH010
    hash: sha256:eec626a9a5695ed8fc717c735aba806479066922e0e1cb99ad5a2215622680bd
  serves:
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.soft_but_cinematic
  summary: Readable cut list generated from the resolved frame table; hard cuts, FADE IN (length D7, UNKNOWN)
    and 18-frame FADE OUT from canon; scene-time and sound-cut notes.
  stamped_content_hash: sha256:5cf11cfaeb28b7f2a843e37958d8e195506e08d343755daad330c96dd87aff08
title: Edit Plan
---
# Edit Plan: Last Signal

The edit is generated from the shot table, not authored. This document is the readable
companion to `12_post/EDIT.edl` (CMX3600, 24 fps non-drop) and `12_post/edit.ffconcat`,
both written by `fm post edl` from `09_resolved/film.json`.

## 1. Rules applied

- FACT: `camera.rhythm.transitions` (LOCKED) value: `default: cut`, `fade_in: head`,
  `fade_out: {at: tail, frames: 18, after: final_image_hold}`, `sc03_to_sc04: hard_cut_black_to_dusk`,
  `sc04_to_sc05: cut_on_light`, `sc05_to_sc06: cut_on_direction`, forbidden: dissolve, wipe,
  sky_cutaway, wire_cutaway.
- DECISION: shots are butted in scene-then-shot order with hard cuts. There are no transitions other
  than the head fade-in and the tail fade-out. Any dissolve, wipe or extra fade would need a change
  request against `camera.rhythm.transitions`, not an edit step.
- FACT: `camera.format` (LOCKED) gives 24 fps and 1920x1080. The film is 1440 frames = 00:01:00:00 by
  the frame table (`total_frames: 1440`). The EDL also has 1440 frames, ending at 00:01:00:00.
- UNKNOWN (D7): FADE IN length. Canon says only "head" and gives no number (`SC01_SH010` notes:
  "length set by post"). `fm post edl` used its default of 12 frames and labelled it in the EDL header as
  "source: default (M6_SCOPE D7 recommendation)". RECOMMENDATION: 12 frames (0.5 s). Rejected: 24 frames
  (eats more than half of the 40-frame opening shot, and the hand that is already moving at f0 would be
  lost in the fade); 0/6 frames (a snap open, which is harsher than the "soft" register asks for). The EDL
  must be regenerated if the human rules a different value.

## 2. Cut list (record frames from `09_resolved/film.json`)

Source in is 00:00:00:00 for every event (each shot is its own clip, starting at its frame 0).
Record out is exclusive, as in the EDL.

| # | Shot | Record frames | Frames | Rec in | Rec out | Transition in |
|---|---|---|---|---|---|---|
| 001 | SC01_SH010 | 0-39 | 40 | 00:00:00:00 | 00:00:01:16 | FADE IN (12 f, D7) |
| 002 | SC01_SH020 | 40-77 | 38 | 00:00:01:16 | 00:00:03:06 | cut |
| 003 | SC01_SH030 | 78-105 | 28 | 00:00:03:06 | 00:00:04:10 | cut |
| 004 | SC01_SH040 | 106-135 | 30 | 00:00:04:10 | 00:00:05:16 | cut |
| 005 | SC01_SH050 | 136-179 | 44 | 00:00:05:16 | 00:00:07:12 | cut |
| 006 | SC01_SH060 | 180-213 | 34 | 00:00:07:12 | 00:00:08:22 | cut |
| 007 | SC01_SH070 | 214-271 | 58 | 00:00:08:22 | 00:00:11:08 | cut |
| 008 | SC01_SH080 | 272-301 | 30 | 00:00:11:08 | 00:00:12:14 | cut |
| 009 | SC01_SH090 | 302-325 | 24 | 00:00:12:14 | 00:00:13:14 | cut |
| 010 | SC01_SH100 | 326-373 | 48 | 00:00:13:14 | 00:00:15:14 | cut |
| 011 | SC01_SH110 | 374-405 | 32 | 00:00:15:14 | 00:00:16:22 | cut |
| 012 | SC01_SH120 | 406-425 | 20 | 00:00:16:22 | 00:00:17:18 | cut |
| 013 | SC01_SH130 | 426-459 | 34 | 00:00:17:18 | 00:00:19:04 | cut |
| 014 | SC01_SH140 | 460-491 | 32 | 00:00:19:04 | 00:00:20:12 | cut |
| 015 | SC01_SH150 | 492-527 | 36 | 00:00:20:12 | 00:00:22:00 | cut |
| 016 | SC02_SH010 | 528-545 | 18 | 00:00:22:00 | 00:00:22:18 | cut |
| 017 | SC02_SH020 | 546-559 | 14 | 00:00:22:18 | 00:00:23:08 | cut |
| 018 | SC02_SH030 | 560-575 | 16 | 00:00:23:08 | 00:00:24:00 | cut |
| 019 | SC03_SH010 | 576-627 | 52 | 00:00:24:00 | 00:00:26:04 | cut |
| 020 | SC03_SH020 | 628-663 | 36 | 00:00:26:04 | 00:00:27:16 | cut |
| 021 | SC03_SH030 | 664-689 | 26 | 00:00:27:16 | 00:00:28:18 | cut |
| 022 | SC03_SH040 | 690-711 | 22 | 00:00:28:18 | 00:00:29:16 | cut |
| 023 | SC03_SH050 | 712-741 | 30 | 00:00:29:16 | 00:00:30:22 | cut |
| 024 | SC03_SH060 | 742-767 | 26 | 00:00:30:22 | 00:00:32:00 | cut |
| 025 | SC03_SH070 | 768-815 | 48 | 00:00:32:00 | 00:00:34:00 | cut |
| 026 | SC04_SH010 | 816-861 | 46 | 00:00:34:00 | 00:00:35:22 | hard cut, black to dusk (`sc03_to_sc04`) |
| 027 | SC04_SH020 | 862-893 | 32 | 00:00:35:22 | 00:00:37:06 | cut |
| 028 | SC04_SH030 | 894-929 | 36 | 00:00:37:06 | 00:00:38:18 | cut |
| 029 | SC04_SH040 | 930-989 | 60 | 00:00:38:18 | 00:00:41:06 | cut |
| 030 | SC04_SH050 | 990-1069 | 80 | 00:00:41:06 | 00:00:44:14 | cut |
| 031 | SC04_SH060 | 1070-1137 | 68 | 00:00:44:14 | 00:00:47:10 | cut |
| 032 | SC04_SH070 | 1138-1163 | 26 | 00:00:47:10 | 00:00:48:12 | cut |
| 033 | SC04_SH080 | 1164-1221 | 58 | 00:00:48:12 | 00:00:50:22 | cut |
| 034 | SC04_SH090 | 1222-1249 | 28 | 00:00:50:22 | 00:00:52:02 | cut |
| 035 | SC05_SH010 | 1250-1273 | 24 | 00:00:52:02 | 00:00:53:02 | cut on light (`sc04_to_sc05`) |
| 036 | SC05_SH020 | 1274-1305 | 32 | 00:00:53:02 | 00:00:54:10 | cut |
| 037 | SC05_SH030 | 1306-1357 | 52 | 00:00:54:10 | 00:00:56:14 | cut |
| 038 | SC06_SH010 | 1358-1439 | 82 | 00:00:56:14 | 00:01:00:00 | cut on direction (`sc05_to_sc06`); FADE OUT 18 f at 1422-1439 |

- FACT: 38 events, 1440 frames. The EDL written by `fm post edl` has the same record timecodes
  (e.g. event 034 00:00:50:22-00:00:52:02, event 038 00:00:56:14-00:01:00:00).
- FACT: shortest shot SC02_SH020 at 14 frames. This is inside the `camera.format` exception "SC02 elliptical
  cuts, 14-19 frames". Every other shot is at least 20 frames, above `shortest_shot_frames: 12`.
- FACT: from SC04_SH010 on, no shot is shorter than 24 frames (SC05_SH010 = 24, SC04_SH070 = 26), which
  meets `camera.rhythm.pace` `tender_min_shot_s: 1.0`.
- DEPENDENCY: 21 of the 38 shots are PROPOSED (modified after G5 approval; G5 is DRIFTED): SC01_SH020/030/050/
  070/080/120/140, all seven SC03 shots, SC04_SH020/030/050-090. The cut follows the frame table as it
  stands. If the human re-approves G5 with different durations, `fm resolve` then `fm post edl` regenerate
  everything here.
- FACT (2026-10-01 re-run): `fm post edl` after the SC03 blocking/camera change and the cue update printed
  "38 events, 1440 frames, end 00:01:00:00, fade in 12 / out 18 frames". The new `EDIT.edl` is byte-identical
  to the previous one. No shot duration changed, so no record frame in this table moved.
- FACT (2026-10-01 animatic rebuild): `fm post edl` again printed "38 events, 1440 frames, end 00:01:00:00,
  fade in 12 / out 18 frames"; `git diff` shows `EDIT.edl` and `edit.ffconcat` unchanged.

### 2.1 SC03 blocking and camera change (recorded 2026-10-01)

- FACT: Ren's SC03 kneel mark moved from shop (2.2, 8.0) to (3.45, 8.66), the end of the west aisle. His
  SC03_SH010 entry is re-pathed (through the door under the camera, round the near gondola end cap, straight
  down the west aisle): about 7.9 m in 48 f, a hard run (mean about 4.1 m/s, peak 5.0 m/s), still inside
  the 52-frame shot. The SC03_SH070 reverse moved from (2.25, 8.9) to (3.75, 9.55), behind a wild back wall,
  with the door rectangle now above his right shoulder. SC03_SH060's phone reference moved to about
  (3.45, 8.88, 0.93). The SC03_SH020-SH070 anim files were reviewed against the new blocking; their timing is
  unchanged.
- FACT: SC03 still runs 576-815 (240 f); every SC03 shot keeps its frame count. The SC02 -> SC03 cut (575/576)
  and the SC03 -> SC04 hard cut, black to dusk (815/816), are unchanged.
- FACT (animatic rebuild 2026-10-01, evening): all seven SC03 shots now take their picture from the v2 draft
  key frames in `10_blender/frames/SC03_SH0x0/` (rendered 2026-10-01 20:23-20:56, after the blocking change),
  step-held by frame index: 1 to 8 keys per shot, so SC03 shows the new staging as key poses, not full
  motion. SC03_SH060 has a single key (f12) held for all 26 frames. FACT: `fm validate` still lists
  `artifact:anim_sc03_sh010` and `resolved:SC03_SH010` as stale (`shot:SC03_SH010 changed`), so the SC03_SH010
  keys may not match the current shot file. Post judges only timing in SC03.

### 2.2 Re-run after the SC04 cable posing and the SC03_SH010 restamp (2026-10-01, late)

- FACT: upstream changed in commit 1598a4f: `anim_sc04_sh010` (cable `prop_state` hidden -> posed, loose
  end on the pavement by his left foot), `anim_sc04_sh050` (rationale text only), `anim_sc03_sh010`
  restamped, and `fm resolve` re-run. Compared against 1598a4f^: frame counts unchanged (SC03_SH010 52,
  SC04_SH010 46, SC04_SH050 80) and every anim event id, frame and kind identical. AUDIO_CUES was restamped
  with that note and no cue edit (content hash `ad57b775...` unchanged).
- FACT: `fm post edl` printed "38 events, 1440 frames, end 00:01:00:00, fade in 12 / out 18 frames";
  `EDIT.edl` is byte-identical to the previous one. No record frame in section 2 moved.
- FACT: the SC04_SH010 picture in the animatic is still the preview still `10_blender/previews/SC04_SH010.png`
  dated 2026-09-30, which predates the cable posing; `render:preview_SC04_SH010` is STALE in `fm validate`.
  So the animatic does not yet show the posed cable in that wide. Post judges only its timing (816-861).
  Owner of the re-render: blender-td.

## 3. Head and tail

- **Head.** FADE IN from black over record frames 0-11 (if D7 = 12). FACT: the `SC01_SH010` camera notes
  start the acting at f0 "so the hand is already in motion as the FADE IN clears". With 12 frames the
  mirror move (f6-9) happens under the fade. RECOMMENDATION: acceptable, because the gag lands after the
  fade clears.
- **Tail, carried-forward hold check.** FACT (from the `SC06_SH010` animation): the look-up ends at f56.
  From there the pose is held, with one breath (in f56-68, out f68-81). The fade out runs over f64-81 =
  record 1422-1439 = EDL 00:00:59:06, 18 frames. That leaves **8 frames of clear held pose (f56-63, record
  1414-1421) before the fade starts**, and 26 held frames in all under the breath. This confirms the
  carry-forward finding "~8-frame hold before the SC06 fade" and matches `fade_out.after:
  final_image_hold`. RECOMMENDATION: keep this. If the hold feels short at G7, the fix is animation timing
  inside SC06_SH010 (animation-director), not a longer fade.

## 4. Scene running time vs SCENES.yaml

| Scene | Frames (frame table) | Budget (`camera.rhythm.scene_budget`, LOCKED) | SCENES.yaml `est_duration_s` x 24 | Delta vs SCENES.yaml |
|---|---|---|---|---|
| SC01 | 528 (0-527) | 528 | 22 s = 528 | 0 |
| SC02 | 48 (528-575) | 48 | 2 s = 48 | 0 |
| SC03 | 240 (576-815) | 240 | 10 s = 240 | 0 |
| SC04 | 434 (816-1249) | 434 | 19 s = 456 | **-22 f (-4.8 %)** |
| SC05 | 108 (1250-1357) | 108 | 4 s = 96 | **+12 f (+12.5 %)** |
| SC06 | 82 (1358-1439) | 82 | 3 s = 72 | **+10 f (+13.9 %)** |
| Film | 1440 | 1440 | 60 s = 1440 | 0 |

- FACT: the cut matches the LOCKED scene budget exactly, and the film total matches SCENES.yaml exactly.
- FACT: SC04, SC05 and SC06 differ from the approved `02_screenplay/SCENES.yaml` estimates. Each is inside
  the 15 % tolerance the budget's rationale cites, and the budget entry notes it as an open human question
  ("keep SCENES.yaml timings exactly, or accept this redistribution").
- RECOMMENDATION, **flagged to the cinematographer and the screenwriter**: nothing to change in the cut.
  Either the screenwriter updates `SCENES.yaml` `est_duration_s` (SC04 18.08, SC05 4.5, SC06 3.42), which
  drifts G2 and needs re-approval, or the human confirms the budget as the authority and SCENES.yaml stays
  an estimate. Post does not edit either file.

## 5. Sound-cut relationships

Frames below are record frames. FACT: placements are read from `12_post/audio/mix_report.json`, written by
the 2026-10-01 `fm audio mix` (138 placements, 1440 frames, 3 silence windows, 5 placeholder recipes; cues hash
`ad57b775...`, which matches the stamped `12_post/AUDIO_CUES.yaml`, PROPOSED). FACT (late 2026-10-01 re-run):
`fm audio mix` again "mixed 138 placement(s)", ~-16.39 LUFS, true peak -1.73 dBTP, and `mix_report.json` is
identical to the previous one key for key, so every placement below still holds. Against the wave-6 mix
(136 placements) two cues were added and none removed or moved: `c_SC01_SH120_plug_click` (408-412, inside
SC01_SH120, no cut involved) and `c_SC02_SH030_door_swing_back` (574-582, across the SC02 -> SC03 cut, below).
These are edit-side requirements for the sound-designer, not mix decisions.

| Cut | Picture | Sound relationship (RECOMMENDATION unless tagged) |
|---|---|---|
| Head, f0 | FADE IN | FACT: `bed_SC01_car_interior` starts at f0 with no fade in the mix report; `c_SC01_SH010_heat_ticks` starts at f0 with a 4-frame fade in. RECOMMENDATION: fade the sound in over the same length as the picture (D7) at assembly, so no sound arrives before the image. |
| SC01 -> SC02, 527/528 | cut | FACT: `car.door_open` (`c_SC02_SH010_door_open`) at 528, with the door already swinging on the cut. The car bed hands over to `bed_SC02_street` at 528. The SC01_SH140 silence (460-491) sits before this cut. A door sound that straddles the cut is fine. |
| SC02 -> SC03, 575/576 | cut | FACT, **resolved (wave 6)**: the mix has exactly one `shop.door_chime` (`c_SC02_SH030_door_chime`, 575-603.8). It strikes on SC02_SH030 f15, the cut point, and its second note and decay ring on under SC03_SH010 as the board's "chime tail". There is no chime at SC03_SH010 f0. The cue's `rationale` records the keep-one ruling. The fridge and panel hums and the shop bed start on the cut at 576. FACT (2026-10-01 mix): the door's swing-back (`c_SC02_SH030_door_swing_back`, `fx.plastic_scuff` placeholder, -38 dB) runs 574-582, so it straddles the cut by 6 frames under the chime and Ren's first SC03 steps (576 on). RECOMMENDATION: acceptable, it is the same door continuing behind him; check by ear at G7 that it does not mask the chime's first note. |
| SC03 end -> SC04, 815/816 | hard cut, black to dusk | FACT: after the clunk at SC03_SH050 f8 (720-728) the shop is silent (`sil_SC03_SH050_after_clunk` 728-742, `sil_SC03_SH060` 742-768). SC03_SH070 (768-815) carries `amb.distant_car_pass` over `bed_SC03_SH070_dead_room`. `bed_SC04_street` starts on the cut at 816, a hard sound cut to match the hard picture cut. RECOMMENDATION: its `xfade_f: 4` should run inside SC04 and not pre-lap into the black. Post checks this by ear at G7. |
| Ratchet across SC04_SH050-SH090 | four hard cuts | FACT (mix report): `crank.click` placements at 1046, 1070, 1094, 1118, 1142, 1166, 1190, 1214, then the stop at 1229 (SH090 f7). That is every 24 frames across the cuts, so the cuts do not reset the ratchet rhythm. |
| SC04 -> SC05, 1249/1250 | cut on light | Send at SC04_SH080 (`send_press`), the delivered tick at f34 (1198), his release breath at SC04_SH090 f8 (1230). FACT: SC05_SH010 holds 2 dark frames before her screen wakes. RECOMMENDATION: the street bed hard-cuts out at 1250 and her room tone or headphone leak starts at 1250, with no sound on the waking screen (D4 desk buzz conflict: follow the shot file). |
| SC05 -> SC06, 1357/1358 | cut on direction | The room tone ends with her held smile. The street dusk bed returns at 1358, a hard cut. The same bed as SC04 gives the bookend by ear too. |
| Tail, 1422-1439 | FADE OUT 18 f | FACT (mix report): `bed_SC06_street` ends at 1422. `c_SC06_SH010_street_tail` runs 1418-1440 with an 18-frame fade out. The out-breath `c_SC06_SH010_breath_out` (1426-1440, a placeholder) is the last sound. RECOMMENDATION: fade the audio out over the same 18 frames so picture and sound reach black and silence together at 1439. |

## 6. Outputs

- `12_post/EDIT.edl`, `12_post/edit.ffconcat` (`fm post edl`, recorded as `edit:edl`).
- `12_post/animatic.mp4` (`fm post animatic`, recorded as `edit:animatic`): 1440 frames, 60.000 s, with the
  mix. See POST_PLAN section 7 for the per-shot picture source and what it is and is not.
