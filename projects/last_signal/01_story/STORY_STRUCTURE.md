---
fm:
  id: story_structure
  kind: story_structure
  phase: STORY
  status: PROPOSED
  owner_role: story-architect
  derived_from:
  - ref: artifact:story_bible
    hash: sha256:1604e946f2eeda770e916acb21b0dcf1777fb847dc583f6ba72fb9659452742e
  serves:
  - intent.race_against_battery
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.earned_last_signal
  - intent.anime_feel
  - intent.soft_but_cinematic
  summary: Nine-beat, 60 s structure for Last Signal — two comic failures (car, shop), one clean turn
    at 34 s, a 26 s tender third.
  stamped_content_hash: sha256:d8a12c83b7c349e115615b4a1d07b7f27082e08ec5109da940295a188ee99f3c
title: Story Structure
---
# Story Structure — Last Signal

Brief duration: **60 s** (USER_REQUIREMENT). Shape: one situation, one turn.
Two comic peaks (car, shop), a clean turn to tender at 34 s, then a long exhale.
All beats are DECISIONs, PROPOSED for G2. Battery values follow
`story.escalation`.

## Beat table

| # | Beat | Purpose | Serves | Seconds | Cumulative |
|---|---|---|---|---|---|
| 1 | The call | Parked car, golden hour. Ren checks his hair in the rear-view mirror, opens a map pin with a fork-and-knife icon, then taps call; her photo (no name) fills the screen. A rehearsed breath. The call icon rings and rings; no answer. Battery 5%. Sets up crush, plan and the inciting failure in one action. | intent.race_against_battery, intent.soft_but_cinematic | 8 | 8 |
| 2 | Text instead | He lowers the phone, a small deflation, then decides to type. As the first words appear the battery icon turns red: 4%. A held "oh no" stare. The race starts. | intent.race_against_battery, intent.anime_feel | 4 | 12 |
| 3 | The car | He turns the key; the old engine coughs to life. Glovebox for the cable: the chunky hand-crank charger clunks onto his lap; he shoves it back (plant). Cable in, charging bolt appears. The engine sighs, shudders and dies; the dash lights go out; the bolt vanishes. 3%. His forehead sinks to the steering wheel. First comic failure. | intent.comic_then_tender, intent.race_against_battery, intent.earned_last_signal, intent.anime_feel | 10 | 22 |
| 4 | The shop | Wide: he bolts out of the car and up the street into the small corner shop. He spots a socket low behind a display, drops to his knees, plugs in; the bolt appears, he exhales, and the whole shop blinks dark around him. 2%. Held frame: his lit face the only light in the room. Bigger, public failure that costs more than the car. | intent.comic_then_tender, intent.race_against_battery, intent.anime_feel | 12 | 34 |
| 5 | The turn | Out on the kerb by the dead car at dusk. 1%, blinking. He sits, spent. His eyes go to the glovebox. He opens it and takes out the crank charger, this time holding it carefully. The film takes a breath: the comedy stops here. | intent.comic_then_tender, intent.earned_last_signal, intent.soft_but_cinematic | 5 | 39 |
| 6 | The crank | Sitting on the kerb, he unfolds the handle and turns it, slow and steady; only the ratchet and his breath. The screen glow steadies on his face. With his thumb he finishes the invitation, types a heart at the end, hesitates, deletes it. 1% becomes 2%. | intent.earned_last_signal, intent.comic_then_tender, intent.open_hopeful_ending, intent.race_against_battery | 11 | 50 |
| 7 | Send | Thumb over send. Pressed. The progress completes and a tick appears (no label). He lets go of the handle. Held breath, then release. | intent.earned_last_signal, intent.race_against_battery | 3 | 53 |
| 8 | Her smile | Hana's room, evening, desk by the window. Headphones on, sketching. Her phone lights. She slides the headphones down, reads, and gives a small smile. The first frame that feels complete. | intent.open_hopeful_ending, intent.soft_but_cinematic | 4 | 57 |
| 9 | Dark | Back on the kerb, his screen fades to black. He leans back against the car, dark phone on his chest, and looks up at the dusk sky. Final image. | intent.open_hopeful_ending, intent.soft_but_cinematic, intent.anime_feel | 3 | 60 |

**Total: 60 s vs brief 60 s** (0% difference; tolerance ±10% = 54–66 s).

## Checks

**Every intent is served by at least one beat.**

| Intent | Beats |
|---|---|
| intent.race_against_battery | 1, 2, 3, 4, 6, 7 |
| intent.comic_then_tender | 3, 4 (comic), 5 (turn), 6 (tender) |
| intent.open_hopeful_ending | 6 (the deleted heart), 8, 9 |
| intent.earned_last_signal | 3 (plant), 5 (choice), 6 (effort), 7 (send) |
| intent.anime_feel | 2, 3, 4 (held reaction frames), 9 (held sky image) |
| intent.soft_but_cinematic | 1 (golden hour), 5 (dusk shift), 8 (first complete frame), 9 (final image) |

Beats 1–9 each list at least one intent. `intent.anime_feel` and
`intent.soft_but_cinematic` are served by beats only in the sense that those
beats give the look and camera departments held frames and light changes to
use; the story does not deliver them on its own (ASSUMPTION about how QA will
count them).

**Shape against CREATIVE_DIRECTION's arc (RECOMMENDATION there, guidance only).**

| Section | Direction | This structure | Note |
|---|---|---|---|
| Setup (call, battery red) | 0–10 s | 0–12 s | +2 s: the call carries three cues and needs the hold |
| Car | 10–22 s | 12–22 s | 10 s; the plant is inside it |
| Shop | 22–36 s | 22–34 s | 12 s; turn arrives 2 s earlier |
| Turn + crank | 36–50 s | 34–50 s | 16 s, including the 5 s turn beat |
| Send | 50–55 s | 50–53 s | 3 s |
| Her + dark | 55–60 s | 53–60 s | 7 s; she gets 4 s for the smile to read |

The tender stretch (beats 5–9) runs 26 s, above the direction's ~20 s
minimum. The two failures escalate: the car costs him a private hope in his
own space; the shop costs him a public sprint and plunges a whole room into
darkness, one percent closer to zero (`tone.comedy_source`).

**Production sanity.** Two characters. Three spaces (street with car, shop
interior, her room), with the car and shop sharing one exterior. Hero props:
phone, car, crank charger, Hana's headphones. No crowds, no vehicle motion, no
particles. Every beat is playable through posture, staging and silhouette plus
phone inserts; the only close facial beat that must read is her small smile
(beat 8), already flagged as a risk for CINEMATOGRAPHY and G7.

**Tight spots.** Beat 1 (8 s for mirror, pin, call, breath, ringing) and beat 3
(10 s including the plant) are the most crowded. If the screenplay finds them
rushed, the first place to borrow from is beat 6 (11 s), which can drop to 9 s
without losing the heart cue.
