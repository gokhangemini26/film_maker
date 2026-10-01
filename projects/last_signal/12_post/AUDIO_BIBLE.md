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
    hash: sha256:2ed0685e13a4ee7ef1d37d1ab31f5403fb357a506b856c86dbef5bf932da5661
  - ref: canon:audio.score
    hash: sha256:ba175fbaf4350e9bb3d9a208454900db2cf9789779cf443cb2bc74e54541bb4c
  - ref: canon:audio.palette
    hash: sha256:d295ae4564d6179c10237ad9582b5267c1f22f8674b6d28e592cb8e0cb717e1e
  - ref: canon:audio.motifs
    hash: sha256:b57836b997a1df4f976c3ed5cb9c18534b3f7799db3f5bf129a2c9c690946dd0
  - ref: canon:audio.silence_map
    hash: sha256:e8d96274f7adfd3cfb6ea1b7901ef0bac2f67763b695528fa98a3f01395ee042
  - ref: canon:audio.ratchet
    hash: sha256:9cb25aef670f215e3375d4cc6ee5487fde85d40728d408d97739ac5eeaf50bdb
  - ref: canon:audio.perspective
    hash: sha256:25a13b6b5e3db8e0af9ac55be3c9a107dffa81af124274e3d44abadd16260826
  - ref: canon:audio.mix
    hash: sha256:6928de0e3e54edc5d62ed70cec1108d335e08443b7d45148af2206cd5b5c0c60
  - ref: canon:audio.sources
    hash: sha256:f6591a7d497aff372318d2b159c24a3cbd26dfe4a97369e1926919a47d80043d
  - ref: canon:audio.conflicts
    hash: sha256:6ed601c6debe4079741c5088600614a0437e50428fc5b79880ed65368bcec11b
  - ref: artifact:storyboard
    hash: sha256:891aec9e44443e0c00e161d46f5cdf7a23346d513b4fbd2cb228e807f7f18523
  serves:
  - intent.race_against_battery
  - intent.comic_then_tender
  - intent.earned_last_signal
  - intent.open_hopeful_ending
  - intent.soft_but_cinematic
  summary: The sound world of Last Signal. It is wordless and has no score. The mishaps are busy with
    sound until the crank, after which only the ratchet and breath are heard. There is one true silence,
    and the human supplies the bodies, feet and music.
  stamped_content_hash: sha256:3126772f9cb95dfdc7d6dac505a55c55923fed0a8c1180e1a5ee5a7cd75ec1ff
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
| `intent.comic_then_tender` | Up to the crank, the world talks back. The starter, coughs, clunks, hums and chimes land on the frame. | After the turn (SC04_SH040) nothing is funny, and all the density goes. |
| `intent.earned_last_signal` | The ratchet, one click per handle top, is the film's pulse. His breath locks to it. | No chime answers the crank's 1 % to 2 %, and no music swells at the send. |
| `intent.open_hopeful_ending` | A breath through Hana's nose that might be a laugh. His long, easy breath out. | The phone dies in silence (no power-down sound). The street fades with the picture. |
| `intent.soft_but_cinematic` | Soft, rounded UI; real transients; one room per scene. | One true silence (SC03 blackout) gives the film real dynamic range. |

DECISION (`audio.principles`, `audio.score`): strictly wordless, with no underscore (D1 recommendation,
the human decides).

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
- Excluded: desk buzz and message chime (D4), generated headphone music (agents never generate music),
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
| SC04 kerb | Quiet street at dusk (SC04_SH010: nothing else) | The ratchet and his breath only |
| SC05 Hana's room | Near silence | Pencil, headphones, the nose-laugh; the headphone leak only if supplied |
| SC06 kerb | The same street | A long breath out; the street fades with the picture from `fade_out_start` |

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
- **Library, downloaded by the human.** Footsteps (pavement and shop), knees and body contacts, cloth,
  seat creak, pencil, headphones slide, phone handling, bird, distant traffic. Each file gets
  `library/audio/<id>/asset.yaml` with its licence written down. No licence is assumed, and UNKNOWN
  blocks final export.
- **Licensed or own.** Hana's headphone track. It must have no lyrics (`tone.wordless`). It is not in
  the mix yet.
- Stand-ins in the current mix are marked PLACEHOLDER. They are `body.*_placeholder` (24 cues),
  `fx.soft_bump` (23 cues) and `fx.plastic_scuff` (6 cues), all listed in AUDIO_CUES `human_supply`.
## 7. What the human must supply

This is the full asks list, with shot and event ids, in `12_post/AUDIO_CUES.yaml` under `human_supply`.
In short:

1. About 16 breath takes for Ren, a sigh, and Hana's nose-laugh (phone recording, 48 kHz).
2. Footsteps on pavement (9) and on a shop floor (8), plus knees, kerb sit and the shop door push and swing-back.
3. Cloth, seat creak, pencil (stroke and set-down), headphones slide, phone lift, phone on chest.
4. Birdsong for SC01_SH010 and SC01_SH150. Optionally, distant traffic for the streets and a better
   car pass for SC03_SH070.
5. Hana's headphone track, 3 to 5 s, with a written licence (or the human's own). If none is supplied,
   SC05 is room tone only.

## 8. Mix (`audio.mix`, D3)

The master is -16 LUFS integrated with true peak at or below -1 dBTP, 48 kHz / 24-bit stereo, and
exactly 2,880,000 samples. There is no limiter. `mix.master_gain_db` is 21.3 dB.

FACT (measured): -16.4 LUFS (ffmpeg ebur128), true peak -1.7 dBTP.

For D3: -16 LUFS with a -1 dBTP ceiling allows a peak-to-loudness ratio of only about 15 dB. In this
sparse, wordless film the room-tone beds therefore carry most of the loudness (the ambience stem
measures about -17.7 LUFS on its own). They sit several dB higher, relative to the clunk, the coughs
and the ratchet, than a quieter target would need. If the beds sound too present at G7, the options
are a lower target (about -20 LUFS allows about 19 dB) or limiting the transient peaks in post.

## 9. Conflicts for the human (`audio.conflicts`, ASSUMPTION)

The working rule is that the shot files win over the storyboard prose.

- **SC05_SH010** (D4): no desk buzz.
- **SC04_SH070** (D4): no chime, ratchet only.
- **Glovebox** (D4): closed at SC04_SH040 f0, with a soft latch at `lid_latch`.
- **SC04_SH060**: the ratchet stays at 24 frames through the hover.
- **SC04_SH080**: the ratchet does not stop under the tick.
- **SC01_SH150**: the bump is very soft.
- **SC01_SH020**: the tap sits on the cut.
