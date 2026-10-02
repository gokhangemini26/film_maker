---
fm:
  id: shot_list
  kind: shot_list
  phase: STORYBOARD
  status: PROPOSED
  owner_role: cinematographer
  derived_from:
  - ref: artifact:cinematography_bible
    hash: sha256:0ece10f8b6c21ceaf49bb36622c7860dbe7ce588190de888782fa6b1fa08262d
  - ref: artifact:screenplay
    hash: sha256:56d22d2e73f971b8a0d3c17ed54478249bc67c8f37212bc6730918daaae17022
  - ref: artifact:scenes
    hash: sha256:137da02c736eaa6e9e9e5d0e0288b49020e337d14fbb636cb1797ee1d002461b
  - ref: artifact:character_bible
    hash: sha256:71e9d285acb36dc68c5f5a59a3678b05dccd38d1f34595550de52325379cfbec
  - ref: artifact:art_direction_bible
    hash: sha256:b55a2438747bcd566ab5452b1c55534e8808728c2840c4ced1c1339201f6c001
  - ref: artifact:lighting_bible
    hash: sha256:95224320170d0ddbd153032d19139e397472ec4d9c95e12212ea9a97a78ca2f3
  - ref: canon:camera.format
    hash: sha256:2501c716273516ebe3e4dba470a0e8896aff0761fda6926bbb09cfc7bad1eeea
  - ref: canon:camera.lens_set
    hash: sha256:9fb9751fd7e1a1c7e78db64c2c1d002963715a175d0b36784b12ca0fd51697ac
  - ref: canon:camera.lens.roles
    hash: sha256:96b9e326f047dfb3174ff35e6a3e04c514792ef137650b1b2e5a1b62eb9a049b
  - ref: canon:camera.height.eye_level
    hash: sha256:e2d432bb886ba9b6e07bed858c4df59379bc335b0c157e74840e19f714c3938b
  - ref: canon:camera.height.high
    hash: sha256:53f5fce143be9fd863b0247a153073c5f18a50cdf76a83646d46466f48873170
  - ref: canon:camera.height.low
    hash: sha256:ef557119cd2774d9ad4f84d6c46caee413b496ad38b9c331d426be6db7c1373d
  - ref: canon:camera.movement.push_in
    hash: sha256:b2116094133cd8c9d9331d429d13d6259b58acde02cf25587f7163b9cdc4f092
  - ref: canon:camera.framing.shot_size_arc
    hash: sha256:060c1aaa7a1a79dc84891334d4b63aa91f0170ce0dc77f9b735032fa369a68c6
  - ref: canon:camera.framing.jacket_off_sky
    hash: sha256:a1b44051ca76f0e7d7a0eb179647edf7e77901f22cefde1c098253a122b0963d
  - ref: canon:camera.inserts.legibility
    hash: sha256:4b85f4c49c8376dc8b5c5af4e27046ea1d57741f53addd5a5c3a24f766ad6859
  - ref: canon:camera.inserts.heart
    hash: sha256:d2f73b83562c499ca0081215788d62b3927bc8db8264111957313dd5e0200ba5
  - ref: canon:camera.phone_lit.framing
    hash: sha256:877709f4bd871a9acf176d8154784483642306f0dac3bf181f07c8690a44b31a
  - ref: canon:camera.geography.sc02
    hash: sha256:23366df4656fdb81deffd2d208407fccf11181183a4003a349b2ab8ec4aca1ec
  - ref: canon:camera.geography.sc03
    hash: sha256:e426b8886e816baa16c233f2dc982b793c5ac89e41553bc6e07299c3eb332a41
  - ref: canon:camera.geography.sc04_sc06
    hash: sha256:f3523dd5f594b8501d1b6232af934e15492d4a4751b1327aac4a2dae17dbf115
  - ref: canon:camera.geography.sc05
    hash: sha256:4a2b9a9f368b1deafcd37875023198c61e71d29bffe70c0d79d670061e3c886d
  - ref: canon:camera.gags.no_repeat
    hash: sha256:e268a6d91364cc5e7dd5818f91e0bddcdd747334c64e72808b3021f423b03971
  - ref: canon:camera.rhythm.scene_budget
    hash: sha256:3a0f9e8b633e6af955192a0d459cd316fdbb721ce25b920263219195e0cd943f
  - ref: canon:camera.rhythm.pace
    hash: sha256:159ba88fec689f71013a9b320634dd92231e1355c17de392979a90a0479b8b30
  - ref: canon:camera.rhythm.transitions
    hash: sha256:0ff059c432a2227bfbe4eebceef37bc953cd834328d87d7ae75970a866ddcb15
  - ref: canon:continuity.battery
    hash: sha256:3ae887fb83c87d7b62fa330892adc433d0a7258b0ebcb3ee0adf07fd003bf12e
  - ref: canon:story.message
    hash: sha256:1af4da69fe957aae4808a1834171aeef9813455dde4e69d8fd7103ff068e368e
  serves:
  - intent.race_against_battery
  - intent.anime_feel
  - intent.soft_but_cinematic
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.earned_last_signal
  summary: 38 shots, 1440 frames (60.00 s at 24 fps); per-scene totals equal the human-accepted camera
    budget (SC01 528, SC02 48, SC03 240, SC04 434, SC05 108, SC06 82).
  stamped_content_hash: sha256:0df8869673943062b5d6299f81beb7a8c81a6812572cda84343c6d26c64550cb
  stamp_note: 'Content revised since the G5 approval (8e9b8b7): preview pass 1, v2 car interior, v2 frontal
    and G5-fix revision sections; height cells of the 13 insert rows; SC04_SH090 height 0.95 to 0.92;
    SC03_SH020/030/060 rows (scale, height) and the bolt legibility note (2026-10-02). Restamped after
    those revisions, not to silence staleness.'
title: Shot List
---
# Shot List: Last Signal

PROPOSED for G5. One row per `08_shots/<id>.shot.yaml`; the shot files are the
source of truth for camera values, and this table was generated from them.
Frame counts are at 24 fps (`camera.format`). Scales: INS insert, MCU medium
close-up, MS medium, MWS medium-wide, WS wide. Heights are lens heights in
metres (Z up) with their meaning from `camera.height.*`. "push-in" is a
`dolly_in` in the shot file.

**Coordinates.** Street, car and kerb shots use the `world.sets.street` frame
(+Y west, +X north). SC03 uses shop-local coordinates (x west, y depth into
the shop, z up, origin at the door threshold). SC05 uses room-local coordinates
(x north, y west, z up, origin at the foot of the window wall). All positions
are rough (M2); the M3 resolver refines them.

**Invitation wording.** The shots use Option A, the text in the approved
SCREENPLAY: SC01 "Are you free tonight?", SC04 "Are you free tonight? Dinner at
8? My treat." ASSUMPTION: Option A stands; `story.message` still records the
wording as UNKNOWN (open since G2/G3). A different option changes the holds in
SC01_SH070 and SC04_SH060 only.

**Preview pass 1 revision (PROPOSED, re-approval needed at G5).** The first
Blender preview showed camera positions that could not give the promised frames.
Changed shots and why: SC04_SH030 lens moved 40 deg east around him on the
pavement so the glovebox is inside the 50 mm frame; SC04_SH050 and SC04_SH090
lens moved 30 deg east so he reads three-quarter facing screen left instead of
frontal (SH090 height now equals the SH050 end, 0.92 m); every text insert
(SC01_SH030/070/080/120/140, SC03_SH060, SC04_SH020/060/070/080) now sits
0.30 m from the screen on his eyeline (frame 71 mm), and the two screen inserts
(SC01_SH020/050) sit 0.67 m from the screen above his left shoulder (frame
0.16 m, head out of the sight line). Each insert states its assumed screen
centre as a DEPENDENCY for the animation hold. Durations, lenses, scales and
serves are unchanged.

**v2 car interior revision (PROPOSED).** The animated frames (and, from now on,
the stills) use the v2 car interior: front seats 0.25 m forward, so his phone
rests at about (1.28, 0.62, 1.00) instead of (1.29, -0.09, 0.97). Every SC01
phone insert lens moved with the phone, keeping its old offset from the screen
(no tilt, no new lens): the text inserts SC01_SH030/070/080/120/140 sit at
(1.28, 0.37, 1.17), 0.30 m from the screen on his eyeline (frame 72 mm; the
lens is inside his head, which inserts do not render), and the screen inserts
SC01_SH020/050 sit at (1.01, 0.12, 1.35), 0.67 m from the screen above his left
shoulder (frame 159 mm; the sight line clears his head and hair). Measured with
the pure-Python frame state (animate.frame_state). Before the move the old
lenses were 0.97 m (text inserts) and 1.28 m (screen inserts) from the phone,
and no legibility minimum was met. SC01_SH030 needs about 0.03 m toward the
phone's top edge to frame the status bar with her photo: handled by the builder
(`anchors.insert_shift` has a `ui.call_screen` case). Other SC01 and SC02
shots keep their framing.

**v2 frontal revision (PROPOSED, re-approval needed at G5).** With the ring
steering wheel in the builder, the two 50 mm frontals SC01_SH010/SH090 move
their lens 0.50 m back along the same axis, from (1.29, 1.00, 1.20) to
(1.29, 1.50, 1.20), inside the car body (car_body_y max 1.55). Lens, height
(eye level 1.20 m), aim (look_at ren), scale, duration and serves are
unchanged, so no table cell changes. At y 1.00 the v2 seats had made the MCU a
close-up with the crown and tuft cut; y 1.25 and 1.45 still clip the tuft; at
y 1.50 the preview shows the headliner edge at the top, crown and tuft whole,
the ring behind his hands and the phone uncovered (SH010). SH090: superseded
by the G5-fix revision below (the thumb ruling). DEPENDENCY for the animation-director: SH090's key text still says
"thumb up ... (lower frame)" and SH010's eyeline says "frame top-left" for the
mirror, which the v2 preview shows in the upper frame on the right. No other
shot shares this lens position (SC01_SH150 is the exterior frontal at
(1.29, 1.75, 1.72) and is not changed).

**G5-fix revision (PROPOSED, 2026-10-02; re-review needed at G5).** This
revision answers the FAIL findings 1-3 of the G5 re-review. It also records the
human's rulings on SC01_SH090 and the blackout exposure. Durations, lenses and
serves are unchanged.
- SC03_SH030 (finding 1): `look_at` moves from `ceiling_panels` to `ren`. The
  lens moves to (3.85, 10.15, 0.90), beyond the wild back wall. The computed
  tilt up is 6.9°, inside the locked 8° of `camera.height.low`. The panels
  still hang in the upper frame. The scale is now MS.
- SC03_SH020 (finding 3): the lens moves to (3.62, 8.90, 1.28), over his right
  shoulder at his own eyeline. The phone's face shows f4-f22 and the bolt is
  visible from f14 to f35. Its size is about 1.5 %, under the 3 % minimum (see
  the legibility section).
- SC03_SH060 (finding 2): the lens moves to (3.45, 8.72, 1.18), 0.30 m from the
  kneel-rig phone on his eyeline. The frame is 71 mm and the "2 %" is sharp, at
  about 6 % of frame height.
- SC01_SH090 (finding 4, ruling delegated by the human): the camera change
  stays. The raised-thumb hand is in frame, inside the ring at the bottom. It
  does not read as a thumb because the figure's hands are mitts. The deviation
  from SCREENPLAY line 93 is recorded as a DECISION in the shot file.
- SC03_SH050/SH060/SH070: the human's 0.12 exposure ruling (2026-10-02) is
  recorded in each shot's `rationale.lighting`.
- Stale dependency notes now say what the builder handles: the
  `ui.call_screen` shift and the thin-wall rule.

### SC01 INT. REN'S CAR - GOLDEN HOUR (budget 22.00 s / 528 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC01_SH010 | SC01 | 1.67 s (40 f) | MCU | 50 | eye level 1.2 m | static | Mirror check, tuft | race_against_battery, soft_but_cinematic, anime_feel | FADE IN / cut |
| SC01_SH020 | SC01 | 1.58 s (38 f) | INS | 85 | insert 1.35 m | static | Map, fork-and-knife pin | race_against_battery, open_hopeful_ending | cut |
| SC01_SH030 | SC01 | 1.17 s (28 f) | INS | 85 | insert 1.17 m | static | Swipe to her photo, 5 % | race_against_battery | cut |
| SC01_SH040 | SC01 | 1.25 s (30 f) | MCU | 24 | eye level 1.12 m | static | Practised breath, taps call | race_against_battery, comic_then_tender | cut |
| SC01_SH050 | SC01 | 1.83 s (44 f) | INS | 85 | insert 1.35 m | static | Call button pulses x3, greys | race_against_battery, comic_then_tender | cut |
| SC01_SH060 | SC01 | 1.42 s (34 f) | MS | 24 | mild low 1.0 m | static | Letdown, sits up to text | comic_then_tender, race_against_battery | cut |
| SC01_SH070 | SC01 | 2.42 s (58 f) | INS | 85 | insert 1.17 m | static | Types 'Are you free tonight?' | race_against_battery, open_hopeful_ending | cut |
| SC01_SH080 | SC01 | 1.25 s (30 f) | INS | 85 | insert 1.17 m | static | 5 % -> red 4 % | race_against_battery, comic_then_tender | cut |
| SC01_SH090 | SC01 | 1.00 s (24 f) | MCU | 50 | eye level 1.2 m | static | Freeze, stuck exhale | comic_then_tender, race_against_battery | cut |
| SC01_SH100 | SC01 | 2.00 s (48 f) | MS | 24 | eye level 1.2 m | static | Key, glovebox, crank clunks onto lap | earned_last_signal, comic_then_tender, race_against_battery | cut |
| SC01_SH110 | SC01 | 1.33 s (32 f) | INS | 85 | insert 1.0 m | static | Crank in lap, shoved back, cable out | earned_last_signal, comic_then_tender | cut |
| SC01_SH120 | SC01 | 0.83 s (20 f) | INS | 85 | insert 1.17 m | static | Bolt appears beside 4 % | race_against_battery, comic_then_tender | cut |
| SC01_SH130 | SC01 | 1.42 s (34 f) | MS | 24 | eye level 1.2 m | static | Relief; engine dies, dash dark | comic_then_tender, race_against_battery | cut on the stall frame |
| SC01_SH140 | SC01 | 1.33 s (32 f) | INS | 85 | insert 1.17 m | static | Bolt gone, 4 -> 3 % | race_against_battery, comic_then_tender | cut |
| SC01_SH150 | SC01 | 1.50 s (36 f) | MS | 50 | mild high 1.72 m | static | Forehead to the wheel | comic_then_tender, race_against_battery | cut |

**SC01 total: 15 shots, 528 frames = 22.00 s** (average 1.47 s per shot).

### SC02 EXT. STREET - GOLDEN HOUR (budget 2.00 s / 48 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC02_SH010 | SC02 | 0.75 s (18 f) | MWS | 24 | mild low 1.45 m | static | Door flies open, he scrambles out (left open) | race_against_battery, comic_then_tender | cut (elliptical) |
| SC02_SH020 | SC02 | 0.58 s (14 f) | MWS | 35 | eye, tilt down 11° 1.72 m | static | Mid-run from behind, into the gold | race_against_battery, comic_then_tender, anime_feel | cut (elliptical) |
| SC02_SH030 | SC02 | 0.67 s (16 f) | MWS | 35 | eye level 1.7 m | static | Ducks into the shop, chime; car far behind | race_against_battery, comic_then_tender | cut |

**SC02 total: 3 shots, 48 frames = 2.00 s** (average 0.67 s per shot).

### SC03 INT. CORNER SHOP - GOLDEN HOUR (budget 10.00 s / 240 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC03_SH010 | SC03 | 2.17 s (52 f) | WS | 35 | strong high 2.3 m | static | Master: enters, crosses, kneels | comic_then_tender, race_against_battery, anime_feel | cut |
| SC03_SH020 | SC03 | 1.50 s (36 f) | CU (OTS) | 35 | his eyeline 1.28 m | static | OTS plug-in, bolt beside 3 % | race_against_battery, comic_then_tender | cut |
| SC03_SH030 | SC03 | 1.08 s (26 f) | MS | 24 | mild low 0.9 m | static | Wary look up at the panels: nothing | comic_then_tender | cut |
| SC03_SH040 | SC03 | 0.92 s (22 f) | MCU | 35 | eye level 1.05 m | static | Long exhale | comic_then_tender | cut |
| SC03_SH050 | SC03 | 1.25 s (30 f) | WS | 35 | strong high 2.3 m | static | Master: blackout | comic_then_tender, race_against_battery, anime_feel | cut |
| SC03_SH060 | SC03 | 1.08 s (26 f) | INS | 85 | insert 1.18 m | static | 2 %, bolt gone | race_against_battery | cut |
| SC03_SH070 | SC03 | 2.00 s (48 f) | MCU | 35 | eye level 1.05 m | static | Reverse: phone-lit face, door far behind (held) | comic_then_tender, race_against_battery, soft_but_cinematic | hard cut, black to dusk |

**SC03 total: 7 shots, 240 frames = 10.00 s** (average 1.43 s per shot).

### SC04 EXT. STREET, KERB BY REN'S CAR - DUSK (budget 18.08 s / 434 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC04_SH010 | SC04 | 1.92 s (46 f) | MWS | 35 | eye level 0.95 m | static | Bookend: hunched at 1 % | comic_then_tender, soft_but_cinematic, open_hopeful_ending, anime_feel | cut |
| SC04_SH020 | SC04 | 1.33 s (32 f) | INS | 85 | insert 0.79 m | static | 1 % blinking; tries to type, stutter | race_against_battery, earned_last_signal | cut |
| SC04_SH030 | SC04 | 1.50 s (36 f) | MCU | 50 | eye level 0.95 m | push-in | Looks to the open door, glovebox (push 1) | earned_last_signal, comic_then_tender | cut |
| SC04_SH040 | SC04 | 2.50 s (60 f) | MS | 50 | strong low 0.5 m | static | Takes the crank, sits back holding it (strong low) | earned_last_signal, comic_then_tender | cut |
| SC04_SH050 | SC04 | 3.33 s (80 f) | MS | 50 | eye level 0.92 m | push-in | Plugs in, cranks, glow steadies (push 2) | earned_last_signal, comic_then_tender, soft_but_cinematic | cut |
| SC04_SH060 | SC04 | 2.83 s (68 f) | INS | 85 | insert 0.79 m | static | Finishes invitation; heart typed, deleted | race_against_battery, open_hopeful_ending, earned_last_signal | cut |
| SC04_SH070 | SC04 | 1.08 s (26 f) | INS | 85 | insert 0.79 m | static | 1 % -> 2 %, bolt on | earned_last_signal, race_against_battery | cut |
| SC04_SH080 | SC04 | 2.42 s (58 f) | INS | 85 | insert 0.79 m | static | Send, progress, tick | earned_last_signal, race_against_battery, open_hopeful_ending | cut |
| SC04_SH090 | SC04 | 1.17 s (28 f) | MCU | 50 | eye level 0.92 m | static | Lets go, click, breath out | earned_last_signal, comic_then_tender, open_hopeful_ending | cut on light |

**SC04 total: 9 shots, 434 frames = 18.08 s** (average 2.01 s per shot).

### SC05 INT. HANA'S ROOM - EVENING (dusk) (budget 4.50 s / 108 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC05_SH010 | SC05 | 1.00 s (24 f) | INS | 85 | insert 1.39 m | static | Her phone wakes: his photo | open_hopeful_ending, earned_last_signal | cut |
| SC05_SH020 | SC05 | 1.33 s (32 f) | MS | 50 | eye level 1.14 m | static | Headphones down, picks up phone | open_hopeful_ending, soft_but_cinematic | cut |
| SC05_SH030 | SC05 | 2.17 s (52 f) | MCU | 50 | eye level 1.14 m | static | Reads; small smile (held) | open_hopeful_ending, soft_but_cinematic | cut on direction |

**SC05 total: 3 shots, 108 frames = 4.50 s** (average 1.50 s per shot).

### SC06 EXT. STREET, KERB BY REN'S CAR - DUSK - MOMENTS LATER (budget 3.42 s / 82 f)

| shot | scene | dur | scale | lens | height | movement | subject | serves | transition |
|---|---|---|---|---|---|---|---|---|---|
| SC06_SH010 | SC06 | 3.42 s (82 f) | MWS | 35 | eye level 0.95 m | static | Bookend: screen fades, leans back, looks up; fade out | open_hopeful_ending, earned_last_signal, soft_but_cinematic, anime_feel | FADE OUT (18 f) |

**SC06 total: 1 shots, 82 frames = 3.42 s** (average 3.42 s per shot).

## Film total

| Scene | Shots | Frames | Seconds | SCENES.yaml estimate | Difference |
|---|---|---|---|---|---|
| SC01 | 15 | 528 | 22.00 | 22 | 0 |
| SC02 | 3 | 48 | 2.00 | 2 | 0 |
| SC03 | 7 | 240 | 10.00 | 10 | 0 |
| SC04 | 9 | 434 | 18.08 | 19 | -4.8 % |
| SC05 | 3 | 108 | 4.50 | 4 | +12.5 % |
| SC06 | 1 | 82 | 3.42 | 3 | +13.9 % |
| **Film** | **38** | **1440** | **60.00** | **60** | **0** |

USER_REQUIREMENT (human decision, 2026-09-29): the SC04/SC05/SC06 durations
above are accepted; SCENES.yaml is not edited, and every scene is within ±15 %
of its estimate.

## Lens and height use

| Lens | Shots | Where |
|---|---|---|
| 24 mm | 6 | SC01 cabin mediums (SH040, SH060, SH100, SH130), SC02 exit, SC03 wary low angle |
| 35 mm | 9 | SC02 street axis shots, SC03 master x2, OTS, exhale, reverse; SC04/SC06 bookend x2 |
| 50 mm | 9 | SC01 frontal x3 (the lens-roles exception), SC04 faces and the turn, SC05 medium and MCU |
| 85 mm | 14 | Every phone and crank insert (SC01 x8, SC03 x1, SC04 x4, SC05 x1) |

No focal length outside `camera.lens_set`; no `style_break` anywhere. High
angles: SC01_SH150 (mild), SC03_SH010/SH050 (strong); none after the turn.
Low angles: SC01_SH060, SC02_SH010, SC03_SH030 (mild, tilt up 6.9°), SC04_SH040 (strong,
once). Moves: exactly two push-ins, both in SC04 (SH030, SH050), each at or
under 0.135 m/s; every other shot is static; nothing moves after the send.

## Legibility check (`camera.inserts.legibility`, `camera.inserts.heart`)

| Rule | Minimum | Shot | As planned |
|---|---|---|---|
| Map pin | 6 % height, near centre, 36 f | SC01_SH020 | centre, 38 f on screen |
| Her photo on the call screen | 15 % height | SC01_SH030, SH050 | about 25-55 % |
| Battery digits when they change or are the beat | 3 %, 24 f after change | SC01_SH030 (5 %), SH080 (4 % red, 26 f), SH140 (3 %, 30 f); SC03_SH060 (2 %, 26 f); SC04_SH020 (1 %, 32 f), SH070 (2 %, 24 f) | text-size framing (about 71 mm of frame at the screen) |
| Charging bolt | 3 %, 18 f | SC01_SH120 (18 f after appearing), SH140 (absence 32 f); SC03_SH020 (22 f; about 1.5 %, under the minimum, see below); SC04_SH070 | as planned, except SC03_SH020 |
| Invitation, SC01 fragment (4 words) | cap 3.5 %, 0.5 + 4 x 0.3 = 1.7 s (41 f) after the last word | SC01_SH070 | 42 f |
| Invitation, SC04 completion (5 new words) | cap 3.5 %, 0.5 + 5 x 0.3 = 2.0 s (48 f) | SC04_SH060 | 54 f (the heart beat plays inside the hold) |
| Heart | visible 12 f, hover 20 f, plain text 12 f after delete; compose field only; emoji panel never framed | SC04_SH060 | 12 / 20 / 12 |
| Progress line and tick | line 1 s; tick 5 %, thumb clear, in the eye path, 24 f | SC04_SH080 | line f 8-32, tick f 34, held 24 f |
| His photo on her phone | 5 % height | SC05_SH010 | about 25 % |
| Crank pip | 1 % height | SC04_SH050 (end) | about 1.3 % |

DEPENDENCY (look-director / M3 UI build): the sizes need the UI texture on the
0.147 m phone model to give the invitation a cap height of at least 2.5 mm,
battery digits at least 2.2 mm, the map pin at least 9.6 mm, the sent tick at
least 3.6 mm. The tick's contrast is still open in look canon (G4 finding 4).
SC03_SH020 (an over-the-shoulder, not an insert): the earlier figure of a
4.4 mm bolt was wrong. The rendered bolt glyph is 4.8 mm, and 3 % of frame
height needs a frame of 0.16 m or less at the phone, a 0.28 m lens distance at
35 mm, which in this kneel rig is inside his head. Measured on draft frames
(2026-10-02), the bolt is about 1.5 % of frame height. That is a conflict
between `camera.inserts.legibility` and `camera.gags.no_repeat` (no insert for
the shop's hope), left for the human.

## Changes from the bible's coverage sketch (section 12.3)

- **SC01:** 15 shots, not 14. The plant medium was split: SC01_SH100 (key,
  glovebox, clunk) and a new 85 mm crank insert SC01_SH110, because in the
  24 mm medium the crank is about 7 % of frame width, under the 10 % minimum for
  a prop whose state carries the beat (`camera.framing.space_and_size`). The
  call screen is two inserts: a text-size upper half (her photo and a readable
  5 %) and the full screen for the ring. The typing insert grew to 58 f to meet
  the reading hold; other SC01 shots gave back the frames. Scene total unchanged.
- **SC03:** the 2 % insert is 26 f (not 19 f) to meet the 24-frame digit hold;
  the reverse is 48 f (exactly the 2 s minimum hold).
- **SC04:** the finish-typing, heart and delete beats share one insert
  (SC04_SH060); the text's reading hold and the heart's holds overlap, which is
  what makes 434 f possible. No face cut during the hover.
- **SC05:** three shots, not two: an 85 mm insert of her phone waking is the only
  way to meet the 5 % photo minimum with the locked desk layout (camera canon
  and bible updated at this phase). Cost: the smile holds 2.17 s, not 2.5 s.
- **SC03 blocking:** he faces the back wall (world canon: the fridges are in front
  of him and the door behind him), so the blackout master shows a pool of phone
  light around his figure rather than his lit face; the lit face is the reverse.
