---
fm:
  id: audio_bible
  kind: audio_bible
  phase: ANIMATION_PREVIEW
  status: PROPOSED
  owner_role: sound-designer
  derived_from:
  - ref: canon:intent.race_against_battery
    hash: sha256:0f143f4624a8c8cebe71b8b7c11549ffdc6b37263c85d07695afa1cba4a5a0a0
  - ref: canon:intent.comic_then_tender
    hash: sha256:470a5a95955efc7d581f5cf9fbf010cf479f60ad92ace91013d7e6523e8de8b7
  - ref: canon:intent.earned_last_signal
    hash: sha256:9bfa4a6653ffe02fa47dc7e8c03e506b5cc69fdbf0d60fc7c8833b279f12d802
  - ref: canon:intent.open_hopeful_ending
    hash: sha256:d00fb87fa639a0f256795fd7d6646100e1b6515fb07a70d641db163777d047fc
  - ref: canon:intent.soft_but_cinematic
    hash: sha256:35eb1dec38d475cfd9f63f627450051df79b9102dd7ce598913762dc050e8e7a
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:tone.the_turn
    hash: sha256:653b9a834c3b4f01813d471792c37227f6b7476e3a4d314cc4792b6e51f5b361
  - ref: canon:tone.comedy_source
    hash: sha256:ad4f3b655e3e9c899631f06c90646a9fdabf0c60f79bbce11df5d4f8d16b9478
  - ref: canon:tone.ending_restraint
    hash: sha256:96e2bcf71a89d916ed0ce17fe4ccdc55c000fef096ccaf31653c15b648f4f0ad
  - ref: canon:tone.anti_goals
    hash: sha256:d6476842356e596dd37c3b164729c301f406236331567508fa016e50b5d7722b
  - ref: canon:continuity.props.glovebox_and_crank
    hash: sha256:1a07722fc5b25ac9e48d8fa4597991629967aa68fc89db15ce4175247e556e7a
  - ref: canon:continuity.battery
    hash: sha256:3ae887fb83c87d7b62fa330892adc433d0a7258b0ebcb3ee0adf07fd003bf12e
  - ref: canon:animation.vocab.gait
    hash: sha256:ea3330e9a3aeaf73beeec3474dede9d8ce7e0ec50da6801efddbc2ab582f509b
  - ref: canon:animation.vocab.event_kind
    hash: sha256:14744df8191ecde7d93d67b53053d743d520722a07c59b7f4322e14696d5f603
  - ref: canon:audio.principles
    hash: sha256:575a17a531edd2b16da2ce24401a12126e78fc9a42e054d3927179f8bdd4d4b4
  - ref: canon:audio.score
    hash: sha256:ce4ecd489ab13d322a77d749e27db91f1ba564de8273e004da6eb19510253dd2
  - ref: canon:audio.palette
    hash: sha256:54b18dedd40516567bafb44ac9d7d7511bec38092d95b73262c54f7dd6c45c86
  - ref: canon:audio.motifs
    hash: sha256:b57836b997a1df4f976c3ed5cb9c18534b3f7799db3f5bf129a2c9c690946dd0
  - ref: canon:audio.silence_map
    hash: sha256:e8d96274f7adfd3cfb6ea1b7901ef0bac2f67763b695528fa98a3f01395ee042
  - ref: canon:audio.ratchet
    hash: sha256:9cb25aef670f215e3375d4cc6ee5487fde85d40728d408d97739ac5eeaf50bdb
  - ref: canon:audio.perspective
    hash: sha256:099b8c847ed8cf44a0da6cd28156665d6751ca671f87546b1787773d68817564
  - ref: canon:audio.mix
    hash: sha256:dd10c4767db381b6a23ee351aaa51e12de78423dbb6b8a527d92e9be707484b6
  - ref: canon:audio.sources
    hash: sha256:646f49fa76f35f969f1b383ce098be7ea6f28b2af12890e8a43a53929d53d2ef
  - ref: canon:audio.conflicts
    hash: sha256:6ed601c6debe4079741c5088600614a0437e50428fc5b79880ed65368bcec11b
  - ref: artifact:storyboard
    hash: sha256:61654c415ba79404f9dcbaa7a2bb7fc0dbc02f7bd511e1c656da9820229e428d
  serves:
  - intent.race_against_battery
  - intent.comic_then_tender
  - intent.earned_last_signal
  - intent.open_hopeful_ending
  - intent.soft_but_cinematic
  summary: The sound world of Last Signal. It is wordless and has no music at all. The mishaps are busy
    with sound until the crank, after which only the ratchet, breath and a 3 dB quieter street are heard.
    There is one true silence, and the human supplies the breaths (recorded) and the foley (CC0 or own).
  stamped_content_hash: sha256:496cfd2ebec66ea0b0ca6909a80422696583b6e6f27a0bc247532550c5f48293
  stamp_note: 'Reviewed 2026-10-02 (post-supervisor, at the main session''s request) against STORYBOARD
    61654c41 (G5-fix revision): changes are framing only (SC01_SH090 thumb in frame inside the ring; SC03_SH020
    CU OTS over his right shoulder at 1.28 m; SC03_SH030 MS, tilt 6.9 deg; SC03_SH060 lens 1.18 m). No
    sound beat, sync point, perspective or conflict item (audio.conflicts / D4) changed; the shot files
    still win. No content revision needed.'
title: Audio Bible
---
# Audio Bible: Last Signal

Status: PROPOSED. The human judges every creative question at G7 (does the hum death land, is the
ratchet moving). Nothing here claims the mix sounds right. `fm qa audio` only proves sync, silence and
levels.

## 1. Intent (what sound must do)

| Intent | What sound does | What its absence does |
|---|---|---|
| `intent.race_against_battery` | Gentle UI sounds count the battery down: blip at 4 %, chime, loss. | The unanswered call is three rings and **nothing**. There is no voice and no fourth ring. |
| `intent.comic_then_tender` | Up to the crank, the world talks back. The starter, coughs, clunks, hums and chimes land on the frame. | After the turn (SC04_SH040) nothing is funny, all the density goes, and the street itself drops 3 dB. |
| `intent.earned_last_signal` | The ratchet, one click per handle top, is the film's pulse. His breath locks to it. | No chime answers the crank's 1 % to 2 %, and no music swells at the send. |
| `intent.open_hopeful_ending` | A breath through Hana's nose that might be a laugh. His long, easy breath out. | The phone dies in silence (no power-down sound). The street fades with the picture. |
| `intent.soft_but_cinematic` | Soft, rounded UI; real transients; one room per scene. | One true silence (SC03 blackout) gives the film real dynamic range. |

DECISION (`audio.principles`, `audio.score`): strictly wordless, with no music of any kind: no underscore
(D1) and no headphone leak (D10). Both are recommended rulings in `12_post/DECISIONS.md`; the human rules
at G7.

## 2. Palette (`audio.palette`)

- **ui**: tap, key tap, swipe, ring pulse, low-battery blip, charging chime, electrical tick, soft send,
  delivered tick. Sine bodies, nothing shrill, no brand-like alert tones.
- **car**: heat ticks, starter, cough, rough idle, engine die (sigh, shudder, stop), glovebox lid
  (drop / latch), door open. The cable's three plug-ins (car adapter SC01_SH120 `bolt_on`, shop socket
  SC03_SH020 `plug_in`, crank port SC04_SH050 `plug_in`) share one small latch tick at -30 to -32 dB,
  so plugging in always sounds the same and the chime, or its absence, is what changes.
- **shop**: door chime, fridge hum (50 Hz), panel buzz (100 Hz), the breaker CLUNK.
- **crank**: one click (pawl, tock, spring), 90 ms.
- **body**: breaths, sigh, nose-laugh. These are PLACEHOLDERS until the human records them.
- **room**: car cabin, dusk street, shop, quiet room. SC03_SH070 uses the quiet-room preset as a dead
  room. There is also a distant car pass and exact silence.
- Excluded: desk buzz and message chime (D4), Hana's headphone leak (D10: SC05 is room tone only; agents
  never generate music either),
  car door close (the door stays open on screen), blink sounds (the vocab v2 `lids` blinks in SC03_SH070,
  SC04_SH010, SC04_SH030 and SC05_SH030 stay silent).

## 3. Motifs (`audio.motifs`, `audio.ratchet`)

1. **The unanswered call.** Three ring pulses in SC01_SH050 (`ring_1`, `ring_2`, `ring_3`), then
   nothing from `ring_silence`.
2. **The hum dies.** The car's idle sighs, shudders and stops (SC01_SH130 `engine_sigh` f22,
   `shudder` f26, `stall` f32). The shop's fridges and panels die on the clunk (SC03_SH050 `clunk` f8).
   Both times the power goes and a quieter room is left.
3. **The ratchet pulse.** A `crank.click` sits on every derived `handle_top` of the crank gait:
   SC04_SH050 f56; SH060 f0, f24, f48; SH070 f4; SH080 f2, f26, f50. The last click is the
   `ratchet_stop` event at SC04_SH090 f7. The cue sheet uses `at: {event: handle_top, each: true}`,
   so no frame is typed by hand. His breath is locked to the same cycle: in on the way up, out from
   each top.
4. **The chime and the tick.** The charging chime sounds twice (SC01_SH120, SC03_SH020), and twice the
   world takes the charge back. At the crank no chime sounds. The small delivered tick (SC04_SH080
   `tick_on`) is the one phone sound never taken back.

## 4. Perspective per scene (`audio.perspective`)

| Scene | Room | Foreground |
|---|---|---|
| SC01 car | Closed cabin tone, outside muffled | UI close; the engine as the comic antagonist |
| SC02 street | Open dusk street | Footsteps, the door, the shop chime on the cut; the closer's soft swing-back decays under the cut, never a slam |
| SC03 shop | Shop tone, fridge hum and panel buzz in every shot | The CLUNK; then true silence; then a dead room and a distant car |
| SC04 kerb | Quiet street at dusk (SC04_SH010: nothing else); from the SH040 cut the street is 3 dB lower | The ratchet and his breath only |
| SC05 Hana's room | Near silence, room tone only (no music, D10) | Pencil, headphones (the prop), the nose-laugh |
| SC06 kerb | The same street, still 3 dB under the pre-turn level | A long breath out; the street fades with the picture from `fade_out_start` |

## 5. Silence (`audio.silence_map`)

- **SC01_SH140**, the whole shot. The cabin drops to room-tone floor on the cut after the stall. There
  is no UI sound on 4 % to 3 %. Measured at -60.5 dBFS RMS against a -50 floor.
- **SC03_SH050 f8 onward.** The clunk's own 8-frame decay ends at f16. From f16 to the end of SC03_SH060
  is the film's one true digital silence. It measures as exact zeros.
- **SC04_SH010** is street-only: the dusk bed and nothing else.

## 6. Sources and licences (`audio.sources`)

- **Synth.** These are deterministic recipes in `fm audio` (project code). They cover the UI, car,
  shop, crank and room sounds, including the rough distant car pass. The human may swap any synth
  sound for a library take after listening.
- **Recorded by the human.** Breaths, the sigh and Hana's nose-laugh. Licence: `own` once recorded.
  Until then the licence is UNKNOWN.
- **Library, chosen and downloaded by the human.** Footsteps (pavement and shop), knees and body
  contacts, cloth, seat creak, pencil, headphones slide, phone handling, bird, distant traffic.
  **CC0 or the human's own recording only** (D10); CC-BY and other attribution licences are not
  accepted, because D2 keeps credits off screen. Each file gets `library/audio/<asset id>/asset.yaml`
  with `file`, `licence`, and `source_url` (library) or `recorded_by` (own). No licence is assumed, and
  UNKNOWN blocks final export.
- **No music asset.** Hana's headphone track is dropped (D10); SC05 is room tone only.
- Stand-ins in the current mix are marked PLACEHOLDER. They are `body.*_placeholder` (24 cues),
  `fx.soft_bump` (23 cues) and `fx.plastic_scuff` (6 cues), all listed in AUDIO_CUES `human_supply`.
## 7. What the human must supply

The full list, with the cues each file replaces, is in `12_post/AUDIO_CUES.yaml` under `human_supply`.
Every file goes to `library/audio/<asset id>/<file>.wav` (48 kHz WAV) with an `asset.yaml` beside it.
Once a file exists, the sound-designer swaps the cue from the placeholder recipe to `asset: <asset id>`.

1. **Recorded by the human (licence `own`, phone, 48 kHz, no voice).** Ren: `body.ren_breath_in_short`,
   `body.ren_exhale_stuck`, `body.ren_exhale_relief`, `body.ren_out_breath_small`, `body.ren_run_breath`,
   `body.ren_exhale_long`, `body.ren_crank_breath_out`, `body.ren_crank_breath_in`,
   `body.ren_exhale_release`, `body.ren_easy_breath_in`, `body.ren_easy_breath_out`, `body.ren_sigh`.
   Hana: `body.hana_nose_laugh`. About 16 takes in total. These stay declared PLACEHOLDERS in the mix
   until the files exist.
2. **Library foley (CC0 or own).** `foley.footstep_pavement_r`, `foley.footstep_pavement_l`,
   `foley.footstep_shop_run`, `foley.footstep_shop_brake`, `foley.knees_shop_floor`,
   `foley.knee_pavement`, `foley.kerb_sit`, `foley.shop_door_push`, `foley.shop_door_swing_back`,
   `foley.car_seat_creak`, `foley.cloth_jacket`, `foley.pencil_stroke`, `foley.pencil_down`,
   `foley.headphones_slide`, `foley.phone_lift_desk`, `foley.phone_on_chest`, `street.bird_dusk`.
3. **Optional (CC0 or own).** `street.distant_traffic`, `street.distant_car_pass`.
4. **Not needed.** `music.headphone_leak` is DECLINED (D10).

## 8. Mix (`audio.mix`, D3)

The master is -16 LUFS integrated (+-1 LU) with true peak at or below -1 dBTP, 48 kHz / 24-bit stereo,
and exactly 2,880,000 samples. There is no limiter.

DECISION (D3 recommended ruling, G7 review #11): the street beds from the SC04_SH040 cut to the end
(`bed_SC04_street_turn`, `bed_SC06_street`, `c_SC06_SH010_street_tail`) sit 3 dB under the pre-turn
beds. The cut gets a 4-frame crossfade between two segments of the same street bed (same seed). The
turn is then quieter as level as well as density, without moving the delivery target. Rejected: -20
LUFS for the whole film, which quietens both halves equally.

FACT (measured by `fm audio mix` on this revision, `mix.master_gain_db` 21.9): about -16.5 LUFS,
true peak -1.13 dBTP. The ambience stem RMS is -18.7 dBFS in SC04 before the cut and -21.7 dBFS after
it, and -21.8 dBFS in SC06.

The mix tool suggests a master gain of 22.4 dB, which would hit -16.0 LUFS but push the true peak to
about -0.6 dBTP, over the ceiling. 21.9 dB is the highest gain that holds both limits with margin. The
human judges at G7 whether the turn now reads as quieter. If it does not, the documented fallback is
-20 LUFS.

## 9. Conflicts for the human (`audio.conflicts`, ASSUMPTION)

The working rule is that the shot files win over the storyboard prose.

- **SC05_SH010** (D4): no desk buzz.
- **SC04_SH070** (D4): no chime, ratchet only.
- **Glovebox** (D4): closed at SC04_SH040 f0, with a soft latch at `lid_latch`.
- **SC04_SH060**: the ratchet stays at 24 frames through the hover.
- **SC04_SH080**: the ratchet does not stop under the tick.
- **SC01_SH150**: the bump is very soft.
- **SC01_SH020**: the tap sits on the cut.
