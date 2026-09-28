---
fm:
  id: creative_direction
  kind: creative_direction
  phase: CREATIVE_DIRECTION
  status: PROPOSED
  owner_role: creative-director
  derived_from:
  - ref: artifact:brief
    hash: sha256:f4a7feac5c702dbb3bf357df65a25228fe90e80230f5cefb364ab9b1782b13ae
  - ref: artifact:brief_analysis
    hash: sha256:1f2799750368779bb6e30860818c7bd6260f33e955523374951d21912f7415c7
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
  serves:
  - intent.race_against_battery
  - intent.anime_feel
  - intent.soft_but_cinematic
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.earned_last_signal
  summary: Creative direction for Last Signal (revised after G1 and re-review) — invitation message, unanswered
    call, strictly wordless (invitation is the only readable text).
  stamped_content_hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
title: Creative Direction
---
# Creative Direction — Last Signal

## Logline
Her phone rings out, so he has to text his dinner invitation, the dinner where he
means to tell her he loves her, on a phone with a few percent left. A young man
fights a chain of bad luck (a dead car, a blacked-out shop) until he cranks out
enough power by hand to send the invitation with the last signal.

## The film in a paragraph
He is about 20, and he has finally worked up the nerve: he will invite his friend
to dinner and, at the dinner, tell her how he feels. He calls her. It rings and
rings; she doesn't pick up. He'll text instead, and as he starts typing, the
battery icon turns red. What follows is a small, warm comedy of bad timing: the old
car that would charge the phone gives up with a sigh, and the shop he runs into
goes dark just as he plugs in. He keeps going, earnest and a little ridiculous.
Then he takes up a hand-crank charger, and the film changes key. It turns tender,
and we watch him turn the handle, patiently, one percent at a time. He finishes the
invitation and presses send. It goes. Somewhere else, her phone lights up. She
reads it and smiles. His screen goes dark. She has said yes to dinner, or so her
smile suggests. We know what he is going to tell her there; she doesn't. The film
ends before that dinner.

Nobody speaks, and the invitation is the only readable text in the film. The
phone talks in icons, numbers and colour (`tone.wordless`, strict).

## Intents
Ordered by importance. All are USER_REQUIREMENT except `intent.earned_last_signal`,
a creative-director RECOMMENDATION the user kept at G1.

| id | Tag | Audience effect | How we'll know it worked |
|---|---|---|---|
| intent.race_against_battery | USER_REQUIREMENT | The viewer is with him as he tries to get the invitation to her before the phone dies: unanswered call, then car, shop, crank. | A viewer can retell the chain (call rings out → car → shop → crank → send) after one viewing, without dialogue, and can say what the message was: a dinner invitation. |
| intent.comic_then_tender | USER_REQUIREMENT | Comic, then tender: the car and shop feel comic; the crank and the send feel tender. | Test viewers smile or laugh in the middle and nobody laughs at the crank. |
| intent.open_hopeful_ending | USER_REQUIREMENT | The ending feels open but hopeful: she reads it and smiles, his phone dies, no spoken answer. | Asked "what happens next?", viewers say "they have dinner and he tells her", with hope rather than certainty. |
| intent.earned_last_signal | RECOMMENDATION (kept at G1) | The send lands as a small triumph he earned with his own hands. | Viewers name the crank, not luck, as the reason the invitation got through. |
| intent.anime_feel | USER_REQUIREMENT | It looks and feels like Japanese animation. | Viewers describe it as "anime-style" unprompted. |
| intent.soft_but_cinematic | USER_REQUIREMENT | Soft and pastel to look at, but framed and lit like cinema. | Stills taken at random read as composed frames with a clear light direction, not flat illustration. |

## Tone and anti-goals
Canon: `tone.wordless` (USER_REQUIREMENT), `tone.register`, `tone.comedy_source`,
`tone.the_turn`, `tone.ending_restraint`, `tone.anti_goals` (DECISIONs).

- **Wordless, strict (USER_REQUIREMENT):** no spoken dialogue, no voice on the
  phone. The typed English invitation is the only readable text in the film. The
  phone speaks in icons, numbers and colour: battery %, a call icon that gets no
  answer, a tick for sent. No UI words, no readable names, no readable cards or
  notes; story cues are pictures. Numbers such as "3%" and non-verbal sounds are
  allowed. The user asked for this rule to be locked and chose the strict reading.
- **Register (DECISION):** warm, light romantic comedy-drama. We laugh *with* his
  bad luck, never *at* him.
- **Where the comedy comes from (DECISION, escalation accepted by the user):** the
  world's bad timing and his earnest persistence, played gently. Each failure
  arrives at the worst moment and costs him more than the last, so the second
  failure never plays as a repeat of the first.
- **The turn (DECISION):** one clean turn from comic to tender, when he takes up
  the hand-crank charger. No gags after it. Delivering "tender" as *quiet and slow*
  (only the ratchet and his breath) is this direction's choice, taken from the
  description of the option the user picked; the user's label is "Comic, then
  tender".
- **The ending (DECISION):** restraint. Her small smile at the invitation is the
  only answer ("small" is this direction's choice; the user's label is "She reads
  it, smiles"). No reply, no dinner, no confession on screen; the dark phone is gentle,
  not tragic and not a punchline.
- **The film is not (anti-goals):** manic slapstick · melodrama or tragedy ·
  saccharine sentimentality · cynical or ironic about love · a message about
  technology being bad · sexualised in any way. Both characters are adults of
  about 20; the romance is innocent and unspoken.

## Emotional arc over the 60 s
Timings are guidance for the story-architect, not a lock (RECOMMENDATION).

| Time (approx.) | Beat | Feeling | Energy |
|---|---|---|---|
| 0–10 s | He calls her; the call icon rings and gets no answer; he starts typing; battery goes red | Nerves → small letdown → "oh no" | Rising |
| 10–22 s | The car: plugs in, car dies | Comic frustration, still optimistic | Brisk, comic |
| 22–36 s | The shop: finds a socket, power cuts out | Comic disbelief, more at stake | Brisk, peaks |
| 36–50 s | The crank: slow, patient effort, battery ticks up | Determination, tenderness | Drops, slows |
| 50–55 s | Finishes the invitation, sends; the tick appears | Held breath → release | Still, then lift |
| 55–60 s | Her phone lights; she reads, smiles. His screen goes dark. | Warm, open hope | Soft, settling |

The shape is two quick comic peaks followed by a long exhale. The turn at about
36 s should feel like the film taking a breath.

**One meter, not two (DECISION).** The only stake the viewer tracks is the battery
percentage. "Last signal" in the title means the last of his battery, not weak
network reception. There is no signal-bar crisis at the send, because a second
meter introduced in the last 10 s would blur the stake the film spent 50 s
building. The send is shown simply: the progress completes and a tick appears
(no "Delivered" label, per `tone.wordless`). The story-architect may revisit the
meaning of "last signal" only by proposing it at G2.

### Guidance for STORY: a lighter opening (RECOMMENDATION)
With no words, and no readable text except the invitation, the opening cannot
spend its seconds explaining the crush, the plan and the failed call one by one.
All cues must be pictures (`tone.wordless`, strict). The story-architect will
finalise this; the direction recommends:
- **Let the call carry the setup.** The crush and the plan read from how he
  calls: a rehearsed breath, her photo (no name) on the call screen, and a picture
  in view that says "dinner" (e.g. a small restaurant with a lit window, or a table
  for two seen through glass). Then the call icon rings and gets no answer, and he
  turns to typing. One action, three pieces of information.
- **He knows what the dinner is for; the audience learns it here.** A single
  picture cue tells the audience what he plans to say at the dinner, without the
  message saying it: e.g. a heart emoji he types and then deletes from the draft
  invitation, or a small wrapped gift or flower on the passenger seat. No written
  notes.
- **At most three of his spaces, plus her space.** For example, he calls from the
  car (the car beat starts in place), then the shop, where the crank is found or
  where the crank sequence plays out, then her space.
- **Plant the hand-crank charger early,** inside an existing beat rather than in
  new screen time (e.g. glimpsed on a shelf in the shop before the blackout, or
  rattling in the car's glovebox). Paying it off later makes the crank feel found,
  not given, which serves `intent.earned_last_signal`.

## References → principles
The user named no specific references. The three phrases in the brief are read
here as principles. No studio, director, film or character is used as a spec
(film-conventions/ORIGINALITY.md).

**"Japanese animation style"**
- *Design:* simple, readable character shapes with expressive faces. Emotion is
  carried by the eyes, brows and small posture changes, not by complex bodies.
- *Pacing:* movement alternates with stillness. Held poses and small cycles
  (hair, breath, blinking) are part of the language, so a still frame is a valid
  beat, not a missing animation.
- *Composition:* ordinary objects get their own shots (a battery icon, a plug, a
  crank handle, the sent tick) and are framed as seriously as faces.
- *Comedy:* expressive reaction beats (a frozen stare, a slumped shoulder, a pause
  before he tries again), timed on held frames.

**"Pastel colours"**
- *Colour:* a soft, light-valued palette with low-to-medium saturation. Contrast
  comes from value and warm/cool shifts, not from saturated colour.
- *Colour as story:* the battery's red is one of the few saturated accents, so the
  viewer tracks the stake by eye.
- *Colour over time:* the comic middle can be brighter and airier; the crank and
  send move toward warmer, dimmer pastels (dusk or lamplight), still soft, never
  dark or gritty. Hex values belong to the look-director.

**"Cinematic angles and lighting"**
- *Camera:* the camera has a point of view. Low angles when he makes up his mind,
  high or wide angles when the world beats him, close inserts on the phone, and a
  deliberate change of framing at the turn (the comic middle can be wider and more
  geometric; the crank sequence moves closer and holds).
- *Light:* every scene has a motivated key light with a clear direction
  (sunlight, streetlight, a shop sign, the phone screen). Light failing is itself
  a story event: the shop blackout and the phone going dark are lighting cues.
- *Light as motif (RECOMMENDATION for the look-director):* the phone screen's glow
  on his face is the film's thread. It flickers during the failures, steadies at
  the crank, lights her face at the end, and goes out on him.
- *Composition:* use depth and negative space so frames read as cinema. His
  isolation with the problem gives him space in the frame; her reveal is the first
  frame that feels complete.

## Originality statement
The identity of *Last Signal* is a single, concrete tension: a percentage on a
screen standing between a young man and the evening he has worked up the courage
for. What makes the film its own:
- **The phone as the second character.** Its battery number, its icons and its
  glow carry the plot and the emotion without a single UI word.
- **The hand-crank as the heart.** A modern problem is solved by the oldest kind
  of power, his own effort. The turn from comedy to tenderness happens on that
  physical, repetitive gesture.
- **An ordinary message carrying an unsaid one.** The only text in the film is a
  simple dinner invitation. The audience knows what he means to say at that dinner,
  so a plain line of text carries the weight of a confession without being one.
- **A story that ends one scene early.** The film stops at her smile and his dark
  screen. The confession happens after the credits, in the viewer's head.

## Production constraints as style
- **Stylised proxy characters.** Simple, graphic character shapes are a choice:
  they suit the anime design principle (readable silhouettes, expressive faces)
  and keep the emotion in faces and poses. Invest detail in the faces and in a few
  hero props (phone, car, charger), not in bodies or crowds.
- **Blender 5.2 EEVEE toon/cel shading on a laptop.** Cel shading with two or three
  tone steps and clean shadow shapes is the look, not a compromise. It serves the
  pastel palette and keeps renders cheap. Favour simple, well-motivated lights over
  heavy volumetrics; atmosphere comes from colour and gradient skies, not
  simulation. Keep the car breakdown to sound, a slump and a light change, with no
  smoke or particles.
- **Held poses and limited animation.** Anime-style holds and small cycles cut the
  animation load and are the comic timing tool, so the constraint and the style
  are the same thing.
- **Strictly wordless (`tone.wordless`).** No lip-sync. The unanswered call reads
  through a call icon that rings and gets no answer, and through his face; never a
  voice, never a "Voicemail" label. Story comes from the phone UI in icons, numbers
  and colour (call icon, her photo with no name, battery %, the typed invitation, a
  sent tick), sound (ring tone, engine sputter, power hum dying, crank ratchet, send
  chime) and acting. The invitation is the only readable text, so it must be short
  and legible at a glance. Background props and signage must carry no legible
  words (shop signs as shapes, symbols or colour). The UI font, icon set and any
  phone-UI assets have licence status UNKNOWN until the look-director confirms
  them.
- **60 s.** At most three of his spaces plus her space (see Guidance for STORY).
  Keep sets minimal and reuse lighting rigs.

## Risks
| Risk | Why it matters | How later phases test it |
|---|---|---|
| The opening has too much to say without words (crush, dinner plan, unanswered call) | If the viewer misses the plan, the ending loses its unspoken layer | STORY follows the lighter-opening guidance; G2 checks that a first-time viewer can say (1) he likes her, (2) the message is a dinner invitation, (3) he means to tell her something at dinner |
| The chain feels repetitive (failure, failure) | The comedy flattens and the race slackens | STORY: each failure must escalate (lower battery, more effort, bigger setback), per `tone.comedy_source`; G2 checks that the shop beat raises the stakes over the car beat |
| Where the hand-crank charger comes from | If it just appears, the triumph feels unearned | STORY plants it inside an existing beat (shelf, glovebox) before it is used |
| Too much plot for 60 s | The crank and ending get rushed, and they carry the film | Screenplay timing: the tender last third keeps at least ~20 s |
| The invitation text | It must read as an ordinary invitation, yet carry his nerves; long or over-sweet wording gives the confession away | SCREENPLAY proposes 2–3 short options for the user at G2 |
| Stray readable text (shop signage, car dashboard, packaging, UI labels) | Breaks `tone.wordless` (strict) and dilutes the invitation as the only words | WORLD/LOOK: signage as shapes and symbols; G4 and G6 frames checked for legible text other than the invitation |
| Picture-only cues for "dinner" and "his feelings" are missed | Without text, the unsaid layer of the ending depends on these pictures reading instantly | STORY/STORYBOARD: each cue held long enough and framed as an insert; G2/G5 viewer check that the dinner plan is understood |
| Pastel drifts into saccharine | Anti-goal; weakens the comedy | LOOK: keep value contrast and motivated light; G4 compares stills against the anti-goals |
| Proxy characters too stiff to act | The film depends on faces and posture | First Blender preview (G6): a face and posture test before full animation |
| Her smile must read clearly in a few seconds | It is the only answer the film gives | CINEMATOGRAPHY: a dedicated close-up held long enough; G7 checks readability |
| "Japanese animation style" becomes imitation of a known work | Originality | Every reference stays a principle; QA checks designs against named works |

## Revision G1 — changes
Human G1 decision: **revise**. Notes (verbatim): "The message is the dinner
invitation; the confession stays for the dinner (off screen). The call goes to her
voicemail / she doesn't pick up, so he has to text. Lock the wordless rule in
canon. Keep earned_last_signal, drop rising_stakes. Audience OK." Also addressed:
qa/reviews/G1_REVIEW.md findings 1–7.

| Change | Where | Why |
|---|---|---|
| The sent message is the **dinner invitation**; the confession happens at the dinner, off screen, after the film ends. Her smile answers the invitation. | Logline, paragraph, intents table, arc, originality statement, risks; `intent.race_against_battery`, `intent.open_hopeful_ending` (notes), `intent.earned_last_signal` wording, `tone.ending_restraint` | Human note 1; review finding 1 |
| The call **goes unanswered** (the user's note: "goes to her voicemail / she doesn't pick up"), so he has to text. This is the inciting incident, shown without any voice (after the re-review: a call icon with no answer, no "Voicemail" label). | Logline, paragraph, arc 0–10 s, constraints; `intent.race_against_battery`; `tone.wordless` notes | Human note 2; review finding 2 |
| **Wordless rule in canon** as `tone.wordless` (USER_REQUIREMENT, source: user). | Tone section; `canon/tone.yaml` | Human note 3; review finding 4. Locking it is a human action. |
| **`intent.rising_stakes` removed.** Its `serves` reference in `tone.comedy_source` now points to `intent.race_against_battery`; escalation stays in `tone.comedy_source`. `intent.earned_last_signal` kept. | Intents table; `canon/intent.yaml`; `canon/tone.yaml` | Human note 4; review finding 6 |
| Target audience unchanged. | brief.yaml | Human note 5 ("Audience OK") |
| **USER_REQUIREMENT wording trimmed to the user's language**: "quiet" removed from `intent.comic_then_tender` (it now lives in `tone.the_turn` as a DECISION with rationale); "small" removed from "smile" in `intent.open_hopeful_ending`. | `canon/intent.yaml`; tone section; `tone.the_turn` | Review finding 5 |
| **Second meter dropped**: no "signal bar strains" beat. "Last signal" means the last of the battery; the send ends on a sent tick. | Arc, "One meter, not two", references → principles | Review finding 7 |
| **Lighter opening**: the call carries crush + plan + failure; at most three of his spaces plus hers; the hand-crank is planted early. Stated as guidance for the story-architect. | Guidance for STORY; constraints; risks | Review finding 3 |
| Car breakdown kept to sound, a slump and a light change; UI font and phone-UI assets marked licence UNKNOWN. | Production constraints | Review finding 11 (notes) |

### After the G1 re-review (FAIL on wordless)
Human decisions (explicit choices): wordless = strict; keep the escalation rule;
align wording with the chosen answer labels; audience confirmed.

| Change | Where | Why |
|---|---|---|
| **`tone.wordless` made strict**: the typed invitation is the only readable text; the phone uses icons, numbers and colour (battery %, unanswered call icon, sent tick); no UI words, no readable names; dinner and crush cues are pictures; numbers allowed. Still USER_REQUIREMENT, source user. | `canon/tone.yaml`; brief `special_requirements`; tone section | Human choice "strict"; re-review finding 1 |
| **Every other readable text removed from the direction**: "Delivered" became a sent tick; the voicemail screen became a call icon with no answer; her name became her photo with no name; the restaurant card and reservation became a picture (lit restaurant window, table for two); the note to himself became a deleted heart emoji or a gift on the seat. Stray signage and missed picture cues added as risks. | Paragraph, arc, "One meter, not two", Guidance for STORY, references → principles, originality, constraints, risks | Same |
| **Escalation kept** in `tone.comedy_source` ("each failure costs him more than the last"), now noted as accepted by the user. | `canon/tone.yaml`; tone section | Human choice; re-review finding 2 |
| **Wording aligned to the chosen answer labels**: USER_REQUIREMENTs say "Comic, then tender" and "she reads it and smiles" in `intent.comic_then_tender`, `intent.open_hopeful_ending`, brief `emotional_goal` and BRIEF_ANALYSIS. The options' descriptive extras live in DECISIONs: "gentle" in `tone.comedy_source`, "quiet and slow" in `tone.the_turn`, "small smile" in `tone.ending_restraint`. | `canon/intent.yaml`; `canon/tone.yaml`; brief.yaml; BRIEF_ANALYSIS.md; tone section | Human instruction; re-review finding 3 |
| **Audience note updated**: value unchanged, recorded as confirmed by the user at G1 ("Audience OK"). | brief `target_audience` | Human note |
