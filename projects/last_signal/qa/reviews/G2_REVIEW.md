---
fm:
  id: g2_review
  kind: gate_review
  phase: SCREENPLAY
  status: PROPOSED
  owner_role: qa-supervisor
  derived_from:
  - ref: artifact:story_bible
    hash: sha256:1604e946f2eeda770e916acb21b0dcf1777fb847dc583f6ba72fb9659452742e
  - ref: artifact:story_structure
    hash: sha256:d8a12c83b7c349e115615b4a1d07b7f27082e08ec5109da940295a188ee99f3c
  - ref: artifact:screenplay
    hash: sha256:56d22d2e73f971b8a0d3c17ed54478249bc67c8f37212bc6730918daaae17022
  - ref: artifact:scenes
    hash: sha256:137da02c736eaa6e9e9e5d0e0288b49020e337d14fbb636cb1797ee1d002461b
  - ref: artifact:creative_direction
    hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
  - ref: artifact:g1_review
    hash: sha256:b1adbcecb1d6d91fdb8ca00eef11c7937ff176a77c33c4b7a097e2690f5894dd
  - ref: canon:intent.race_against_battery
    hash: sha256:0f143f4624a8c8cebe71b8b7c11549ffdc6b37263c85d07695afa1cba4a5a0a0
  - ref: canon:intent.anime_feel
    hash: sha256:3206d035843005dca7956fdf1cd27273af35423e8f5eee72077d947ab905171c
  - ref: canon:intent.soft_but_cinematic
    hash: sha256:35eb1dec38d475cfd9f63f627450051df79b9102dd7ce598913762dc050e8e7a
  - ref: canon:intent.comic_then_tender
    hash: sha256:470a5a95955efc7d581f5cf9fbf010cf479f60ad92ace91013d7e6523e8de8b7
  - ref: canon:intent.open_hopeful_ending
    hash: sha256:d00fb87fa639a0f256795fd7d6646100e1b6515fb07a70d641db163777d047fc
  - ref: canon:intent.earned_last_signal
    hash: sha256:9bfa4a6653ffe02fa47dc7e8c03e506b5cc69fdbf0d60fc7c8833b279f12d802
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:tone.register
    hash: sha256:5541e8cb19b725bdc161a31b0d8a4be9ba4cd6c424ed1a759748e4c933281903
  - ref: canon:tone.comedy_source
    hash: sha256:ad4f3b655e3e9c899631f06c90646a9fdabf0c60f79bbce11df5d4f8d16b9478
  - ref: canon:tone.the_turn
    hash: sha256:653b9a834c3b4f01813d471792c37227f6b7476e3a4d314cc4792b6e51f5b361
  - ref: canon:tone.ending_restraint
    hash: sha256:96e2bcf71a89d916ed0ce17fe4ccdc55c000fef096ccaf31653c15b648f4f0ad
  - ref: canon:tone.anti_goals
    hash: sha256:d6476842356e596dd37c3b164729c301f406236331567508fa016e50b5d7722b
  - ref: canon:story.premise
    hash: sha256:936c5ad6969fe46f3883da6547f7f556587665f1bc5a10b551796f538bf7782b
  - ref: canon:story.theme
    hash: sha256:0a4183b2104659865ae6fa28cde750f49c70a5eff8851d427f4c7ea0a1732d96
  - ref: canon:story.cast
    hash: sha256:372c8cc8f14c4123ee8c44adcb3cec942207bce7fde9ebf737809f7567be0989
  - ref: canon:story.arc.ren
    hash: sha256:df0ad68cc2484fa1482960f99791ad9769c312347df703ae51042da2d471b9d8
  - ref: canon:story.arc.hana
    hash: sha256:b4a1dc03fb920de195729535214fdeba08ddd285547f90709e4cba5445956240
  - ref: canon:story.inciting_incident
    hash: sha256:e35e0f9fe8cc4cd64253b6280ebfa8349ca12eff8886754f3c6e08c10292c957
  - ref: canon:story.setup_cues
    hash: sha256:3c1e09bf27191aa14554f013c0f14778e5d9cb35ce687c17a94e500bacfd9e21
  - ref: canon:story.crank_plant
    hash: sha256:89f02ddf8ea05d7ac2249eea269396b53f51f1dc26d4bd2bc19680689a381c6a
  - ref: canon:story.escalation
    hash: sha256:8f6ad8618119799ff3b76b9f8adb710ed3e379445ac9b0aad0c1634793f79067
  - ref: canon:story.message
    hash: sha256:5225cd2112b4a2e40f5bc368d6c925345067c99b528df66e9af18f1cef4305e6
  - ref: canon:story.locations
    hash: sha256:77eef6b526928eb349658b62bac2e39606b5de9fba946abeabed7db61efd4cba
  - ref: canon:story.ending
    hash: sha256:9bdbce43d119929004b6775fbeaaaa1df422f184f59c8b71109300df1ea2cfde
  summary: Advisory QA review of G2 (story and screenplay) for Last Signal. Verdict WARN. Nothing breaks
    locked canon. Open points are pacing of the last 10 s, the repeated gag rhythm, one door-continuity
    gap, why he can't just send, and three human choices.
  stamped_content_hash: sha256:0913c3ea1c368eb0b69d78afbe541f6d909745e730239cb9d598c420b20b5565
verdict: WARN
reviewed_gate: G2
title: G2 review — Story and screenplay
---
# G2 review — Story and screenplay

**Verdict: WARN.** The story and screenplay follow every locked intent and
tone entry. Nothing here contradicts canon. The film is strictly wordless as
written, with a clean single turn, a planted crank, and an ending that holds
back. You should still look at five things. Three are choices only you can make
(invitation wording, setup length, title and credits). Two are craft fixes the
screenwriter can make before G3: the climax and ending are squeezed into 10 s,
and the shop gag repeats the car gag's rhythm.

## What the human should look at first
1. **The last 10 s are crowded, and the setup-length choice decides it.**
   - Send (3 s), her smile (4 s) and the final image (3 s) together carry the
     film's triumph and its answer (STORY_STRUCTURE beats 7–9; SCREENPLAY
     notes §2 and §4).
   - In SC04, the send has to show thumb over send, the press, the progress
     line, the tick, letting go of the handle, the click and an exhale, all in
     3 s. In SC06, the screen fade, the lean back and the look up leave about
     1 s to hold the final image.
   - Meanwhile the setup runs 12 s and the crank 11 s.
   - Deciding **setup 12 s vs 10 s** is really deciding where those 2 s go.
   - QA recommends 10 s, with the 2 s going to the send and final image
     rather than to the car beat as the screenwriter proposes (details under
     Open human questions).
2. **Invitation wording A / B / C.** QA agrees with the screenwriter's
   recommendation of **A**, for one more reason:
   - B's first fragment, "Dinner tonight?", is already a complete invitation.
     If he types it at 4% and doesn't press send, the viewer can ask why he
     didn't just send it. That undercuts `intent.earned_last_signal`.
   - A's fragment ("Are you free tonight?") and C's ("Hey, are you free
     tonight?") are both visibly unfinished without "dinner".
   - C's "just us" leans toward the confession the deleted heart is meant to
     hold back (`story.message` `confession_in_text: false`).
3. **Title card and credits are still undecided, and `tone.wordless` is now
   LOCKED without the clarification.**
   - G1 review item 1 asked for this to be settled before locking. It wasn't.
   - As locked, "The typed English dinner invitation is the ONLY readable text
     in the film" forbids an on-screen title and credits.
   - The screenplay correctly adds none (SCREENPLAY opening note).
   - If you want a title or credits, the creative-director has to run
     `fm change propose` on `tone.wordless`. The entry can no longer just be
     edited.

## Open human questions
| # | Question | Options | Why it matters | QA view |
|---|---|---|---|---|
| Q1 | Invitation wording | **A** "Are you free tonight? Dinner at 8? My treat." (9 words) · **B** "Dinner tonight? There's a place I want to show you." (10) · **C** "Hey, are you free tonight? Dinner, just us? 8pm?" (9) | It is the only readable text in the film, and it has to read at the send in about 3 s | **A.** It reads fastest, and its SC01 fragment is visibly unfinished. B's fragment is sendable on its own (item 2 above). C's "just us" hints at the confession. All three are 12 words or fewer, contain no name and confess nothing (verified). |
| Q2 | Setup 12 s (as written) or 10 s | 12 s: the draft · 10 s: the screenwriter's cut (beat 1 to 7 s by dropping the mirror tilt-back and one "Rings"; beat 2 to 3 s) | The setup carries three picture cues (crush, dinner, failed call). The ending carries the triumph and the answer. | **10 s**, but spend the 2 s on send +1 s and final image +1 s, **not** on the car beat. The mirror press-down, the breath and the photo keep the crush cue. The cut does not touch the map pin. |
| Q3 | Title card and credits under locked `tone.wordless` | **(a)** Outside "the film": the creative-director proposes a change request adding e.g. `title_and_credits: outside_film` · **(b)** None on screen; the title lives in metadata only | Post and delivery need to know. Under (a), the title and credits must also stay outside the 60 s. | Same as at G1: (a) is the usual reading. It is not a story blocker. It can be settled by change request any time before post. |

## Findings

| # | Dimension | Level | Evidence | Finding | Suggested fix | Owner |
|---|---|---|---|---|---|---|
| 1 | Pacing / budget | WARN | STORY_STRUCTURE beats 7–9 (3 + 4 + 3 s); SCREENPLAY SC04 send paragraph, SC05, SC06; notes §4 | The total is exactly 60 s and the tender third is 26 s (at least 20 s required). But the climax and resolution get 10 s together, while setup and crank get 23 s. The send (the moment `intent.earned_last_signal` is about) and the held final image (`story.ending` final_image; STORY_STRUCTURE counts it for `intent.anime_feel`) are each about 3 s with several actions inside. SC05's 4 s for four actions is flagged by the screenwriter as a risk. | Take the 2 s from setup (Q2) and up to 2 s from the crank (STORY_STRUCTURE already allows beat 6 to drop from 11 s to 9 s). Aim for about send 4 s, smile 5 s, final image 4–5 s. The screenwriter updates SCREENPLAY notes §2 and SCENES `est_duration_s`. | screenwriter (with story-architect for STORY_STRUCTURE) |
| 2 | Emotional coherence / comedy craft | WARN | SCREENPLAY SC01 ("A charging bolt appears… Relief." → "The engine sighs… dies") and SC03 ("The charging bolt appears… long breath." → "Clunk… goes out"); `canon:tone.comedy_source` rationale ("the second failure never plays as a repeat of the first"); CREATIVE_DIRECTION §Risks "chain feels repetitive" | The shop raises the scale (public, the whole room dark), and the G2 check "shop raises the stakes over the car" is met. But the gag runs beat for beat like the car: plug in, bolt, relief breath, power dies, bolt gone, minus 1%. The second time, the audience expects the pattern, so the same timing lands weaker. | Vary the shop gag's timing so it plays on that expectation. For example: this time he is wary, glances up at the lights, and plugs in; nothing happens; he exhales as the bolt appears; and only then the room goes dark. Or: the dark hits a beat *before* the relief. Keep it to about 10 s and stay inside `tone.comedy_source` (no injury, no humiliation). | screenwriter |
| 3 | Narrative coherence | WARN | SCREENPLAY SC02 ("The car door swings open", driver side, road side) vs SC04 ("The passenger door stands open. The glovebox."); STORY_STRUCTURE beat 5 ("His eyes go to the glovebox") | He leaves by the driver's door, but at the kerb the passenger door is already open, with no action causing it. The kerb side is the passenger side under either traffic handedness. Opening that door himself would also make the choice more active. | In SC04, have him get up and open the passenger door himself (about 1 s, taken from the 5 s turn), then the glovebox. Or show the door left open by an earlier action. | screenwriter |
| 4 | Narrative coherence / intent fidelity | WARN | `canon:intent.earned_last_signal` ("his own effort… got the invitation through"); SCREENPLAY SC01 (fragment typed at 4%, not sent), SC04 ("The glow… stops flickering and holds"); `canon:story.escalation` | The film only feels earned if the viewer believes the invitation could not have gone out without the crank. At 4–2% he visibly has power and a draft. The only sign that the phone can't work at 1% is the stopped flicker, which is shown *after* he starts cranking. So the viewer may ask "why not just finish and send?" | Show the constraint before the crank. At 1% blinking, he tries to type and the screen dips toward black or stutters, and he stops, one beat inside the 5 s turn. The crank then visibly keeps the screen alive. Pick Option A or C so the SC01 fragment reads as unfinished (Q1). | screenwriter; story-architect to confirm `story.escalation` |
| 5 | Intent fidelity (wordless) | WARN | `canon:tone.wordless` (LOCKED; "ONLY readable text in the film"); G1_REVIEW item 1; SCREENPLAY opening note; STORY_BIBLE §Notes | The G1 open note was not settled before the lock. The work itself complies. | Human answers Q3. Under (a), the creative-director runs `fm change propose tone.wordless …` with a reason. | human, then creative-director |
| 6 | Intent fidelity (wordless) | PASS | SCREENPLAY notes §3; STORY_BIBLE §What the story leaves out and §Notes; `canon:story.setup_cues` notes | No spoken line. The phone uses icons, numbers and colour only. There are no names (both notification screens show a photo, no name) and no "Voicemail" or "Delivered". The map pin has no labels. The heart is a pictogram. G1 item 2 (keyboard letters) is carried forward as a DEPENDENCY to look-director and cinematographer in both documents. "8" and "8pm" sit inside the invitation, so they are allowed. Residual for G4: the phone's status bar (carrier name, clock) must also carry no words. | Add "status bar" to the phone UI no-words list when look canon is written. | look-director (G4) |
| 7 | Intent fidelity (the turn, comic then tender) | PASS | `canon:tone.the_turn`; SCREENPLAY SC04 opening note; STORY_STRUCTURE beat 5 | There is one turn, at the crank. SC04 onward has no gags; the sound drops to the ratchet and his breath. The plant is introduced as a gag (clunk onto his lap) and paid off with care. That contrast is the turn and serves `intent.comic_then_tender` exactly. The heart typed and deleted is tender, not comic. | none | — |
| 8 | Intent fidelity (open, hopeful ending) | PASS | `canon:story.ending`, `canon:tone.ending_restraint`; SCREENPLAY SC04–SC06 | The order follows the user's words: sends, she reads and smiles, his phone dies. There is no reply, dinner or confession. The phone going dark is gentle ("He doesn't reach for it"). The headphones answer "was she ignoring him?" with no words (`story.arc.hana`). | none | — |
| 9 | Intent fidelity (race against battery) | PASS | `canon:story.escalation`; SCREENPLAY battery values | The battery runs 5 → 4 (red) → 3 → 2 → 1 (blinking) → 2 → black, the same in STORY_BIBLE, STORY_STRUCTURE, SCREENPLAY and SCENES. There is one meter, and "last signal" still means the last of the battery. Minor: the drop from 2% to 1% happens off screen between SC03 and SC04 with no setback, so "one step per setback" is loose. The elapsed golden hour → dusk covers it. | Optional: reword `story.escalation` to "one step per setback, and one more as time runs out". | story-architect (optional) |
| 10 | Narrative coherence (picture cues) | PASS | CREATIVE_DIRECTION §Risks (G2 viewer check); `canon:story.setup_cues`; SCREENPLAY SC01, SC04 | Checked against the three things a first-time viewer must get. (1) He likes her: the mirror, the practised breath, her photo. (2) The message is a dinner invitation: the fork-and-knife pin plus "Dinner" in all three options. (3) He means to tell her something at dinner: the heart typed then deleted. All three read from pictures. The pin is on screen for about 1 s, so the insert needs holding at G5. | Cinematographer holds the pin insert long enough to read (G5). | cinematographer (G5) |
| 11 | Character consistency | PASS | `canon:story.cast`, `story.arc.ren`, `story.arc.hana`; SCENES `characters` | Two characters. Ids `ren` and `hana` are used consistently. The arc (nervous → calm and spent) is played through posture as canon says. Both are adults. Nothing is sexualised (`tone.anti_goals`). Nobody helps him. | none | — |
| 12 | World consistency | PASS (note) | `canon:story.locations`; SCENES SC01–SC06 `weather: clear`, SC05 `time_of_day: evening` | Three spaces, with the car and shop on one street and a blackout in the shop only. This matches canon. Two notes. (a) `weather: clear` is not decided anywhere in canon and is untagged. It is harmless, but the world-designer owns it. (b) SC05 happens at the same moment as the dusk kerb, so her window should show the same dusk. The charging cable also goes car → shop → crank. Continuity should track it at G5. | World-designer confirms weather. Look and continuity: her window dusk matches SC04/SC06. Continuity tracks the cable. | world-designer; cinematographer (G5) |
| 13 | Rationale quality | PASS | `canon:story.crank_plant`, `story.ending`, `story.escalation` | I tested the three most important decisions. Each names the choice, the mechanism (rejection makes the payoff a choice; ending on him keeps the ending on his effort; one number, one step, keeps the race legible) and a rejected alternative (crank found on a shop shelf; ending on her smile or on black; a signal-bar crisis). Every other story entry also has a rejected alternative. The weakest is `story.escalation` "one step per setback" (finding 9). | none | — |
| 14 | Originality | PASS | CREATIVE_DIRECTION §Originality statement; `references/` empty | All four claims are delivered in the script: the phone as a second character, the crank as the heart, an ordinary message carrying an unsaid one, and ending one scene early. No named work, studio or recognisable scene is used as a model. | none | — |
| 15 | Feasibility | PASS (notes) | STORY_STRUCTURE §Production sanity; SCREENPLAY notes §4 | Two proxy characters, no vehicle motion, no crowds, no particles. Two moments are already flagged with fallbacks: one hand cranking while the other thumb types, and the close smile (G7 risk). The headphones sliding down onto the neck is the only cloth-like contact and is buildable as a rigid prop. | none now; animation-director confirms at G5/G7 | animation-director (later) |
| 16 | Traceability (SCENES vs SCREENPLAY) | PASS | SCENES.yaml SC01–SC06; SCREENPLAY headings | Headings match exactly. Durations 22 + 2 + 10 + 19 + 4 + 3 = 60 s. The beat mapping matches STORY_STRUCTURE. `fm check continuity` reports 0 FAIL and 0 WARN. | Update `est_duration_s` if Q2 or finding 1 changes the timing. | screenwriter |
| 17 | Visual / cinematographic coherence | n/a | — | Look and camera canon do not exist yet (G4/G5). | — | — |

## Previous (G1) open notes: status
| G1 item | Status |
|---|---|
| 1 Title card and credits vs `tone.wordless` | **Still open.** `tone.wordless` was locked without the clarification, so it now needs a change request (Q3, finding 5). |
| 2 Phone keyboard letters | **Carried forward correctly** as a DEPENDENCY for look-director and cinematographer (STORY_BIBLE §Notes; SCREENPLAY notes §3). Nothing to do at G2. |
| Prev #4 "Last signal" = battery, not reception | Kept, with no second meter (`story.escalation` `network_signal_meter: false`). |

## Deterministic checks
- `fm validate -q` (before writing this review): 0 errors, 0 warnings, 1
  info (`BRIEF_UNKNOWN`: references, environment, location; expected).
- `fm intent`: all 6 intents are served by documents (5–6 docs each).
  Counted by canon entries, `intent.anime_feel` has 0 and
  `intent.soft_but_cinematic` has 2 (`story.locations`, `tone.anti_goals`).
  That is expected before look and camera canon. STORY_STRUCTURE says so
  itself (ASSUMPTION, correctly tagged).
- `fm check continuity`: 0 FAIL, 0 WARN (no shots yet; scene level only).
- Word counts of invitation options: counted by hand, A 9, B 10, C 9, all
  within `story.message` `max_words: 12`.

## Not reviewed
- **Visual inspection of rendered frames is not available until M4.** Nothing
  is storyboarded or rendered, so whether the picture cues read, whether any
  stray text is legible, and whether the smile lands can't be checked yet.
- Look, camera, world and character canon do not exist yet. Visual and
  cinematographic coherence are not assessed.
- There is no audience or viewer test. The "first-time viewer" check (finding
  10) is QA's reading of the script, not a test with real viewers.
- `references/` is empty, so originality was checked only against named works.
- Timings are the documents' own estimates. There is no animatic yet to test
  them against.
