---
fm:
  id: creative_direction
  kind: creative_direction
  phase: CREATIVE_DIRECTION
  status: PROPOSED
  owner_role: creative-director
  derived_from:
  - ref: artifact:brief
    hash: sha256:df35810dd51f64d6713210e3ddc72d55126a0551d908546cde31dabe79520116
  - ref: artifact:brief_analysis
    hash: sha256:3b841e76a7d59e474cbb0314f167d1c50586a4463157fff582e604b083f343e8
  - ref: canon:intent.race_against_battery
    hash: sha256:38b8018fd8b5ba6159639d321941e99cca8ee39d43279df3145dc184e718f563
  - ref: canon:intent.anime_feel
    hash: sha256:3206d035843005dca7956fdf1cd27273af35423e8f5eee72077d947ab905171c
  - ref: canon:intent.soft_but_cinematic
    hash: sha256:35eb1dec38d475cfd9f63f627450051df79b9102dd7ce598913762dc050e8e7a
  - ref: canon:intent.comic_then_tender
    hash: sha256:24c45012d6a900ee7d505ad16569c12c54a4913f787c22719ada438fbec848bf
  - ref: canon:intent.open_hopeful_ending
    hash: sha256:10a4454c81bd3ab0b1b81fbb3c2c6f4b752ab46d9cecd298d05483716cb71c67
  - ref: canon:intent.rising_stakes
    hash: sha256:25336a4526e5e52c74307b29f31ab6be2344b1e3a450551a4db776aa7ff6c856
  - ref: canon:intent.earned_last_signal
    hash: sha256:9b61ec9186cf2822eba26d224e501b00c4d04290e2230a27bcbc19794edb4bcf
  - ref: canon:tone.register
    hash: sha256:7dc5832e397d5d5a7f0be12671694da4e8e3ab1834cb7f98f0b8b63a76f98816
  - ref: canon:tone.comedy_source
    hash: sha256:f39121e4a12eea8167393a4c148d714bc39951d3a095b2c81b40482df3dd3e83
  - ref: canon:tone.the_turn
    hash: sha256:bb9e8df572abae3eb2d985af85ae4d56f8e960c6ce2404ce817a7a0699fd9a16
  - ref: canon:tone.ending_restraint
    hash: sha256:3eddb7d69c10acf6d6ab1e4b674e30b6c3f15d1040015c84c2d0a0c7d0dceb44
  - ref: canon:tone.anti_goals
    hash: sha256:becca987fcf46239c392c8c1f6745187df8bae73b0409d3ce140e46215f65f5a
  serves:
  - intent.race_against_battery
  - intent.anime_feel
  - intent.soft_but_cinematic
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.rising_stakes
  - intent.earned_last_signal
  summary: Creative direction for Last Signal — what the film is for, its tone and turn, and the principles
    later departments follow.
  stamped_content_hash: sha256:b7c238c28c52e5272c03e982fcff8887704e380f8f86932b9a17e04794d18e50
title: Creative Direction
---
# Creative Direction — Last Signal

## Logline
With his phone at a few percent and a love confession waiting to be sent, a
young man fights a chain of bad luck (a dead car, a blacked-out shop) until he
cranks out enough power by hand to send one message with the last signal.

## The film in a paragraph
He is about 20, and he has finally worked up the nerve to invite his friend to
dinner and tell her how he feels. The moment he reaches for his phone, the
battery icon turns red. What follows is a small, warm comedy of bad timing: the
old car that would charge the phone gives up with a sigh, the shop he runs into
goes dark just as he plugs in. He keeps going, earnest and a little ridiculous.
Then he finds a hand-crank charger, and the film changes key: it goes quiet, and
we watch him turn the handle, patiently, one percent at a time. He types the
message and presses send; the bar climbs, and it goes. Somewhere else, her phone
lights up. She reads it and smiles. His screen goes dark. We never hear her
answer, and we don't need to.

The words of the message are the only words in the film.

## Intents
Ordered by importance. USER_REQUIREMENT intents come from the user; the two
RECOMMENDATIONs are open for acceptance at G1.

| id | Tag | Audience effect | How we'll know it worked |
|---|---|---|---|
| intent.race_against_battery | USER_REQUIREMENT | The viewer is with him as he tries to reach her before the phone dies, through car, shop and crank. | A viewer can retell the chain (car → shop → crank → send) after one viewing, without dialogue. |
| intent.comic_then_tender | USER_REQUIREMENT | The car and shop feel gently funny; the crank and send feel quiet and tender. | Test viewers smile or laugh in the middle and fall silent in the last third; nobody laughs at the crank. |
| intent.open_hopeful_ending | USER_REQUIREMENT | The ending feels open but hopeful: she reads it and smiles, his phone dies, no answer heard. | Asked "did it work out?", viewers answer "probably" or "I hope so", not "yes" or "no". |
| intent.earned_last_signal *(RECOMMENDATION)* | RECOMMENDATION | The send lands as a small triumph he earned with his own hands. | Viewers name the crank, not luck, as the reason the message got through. |
| intent.rising_stakes *(RECOMMENDATION)* | RECOMMENDATION | Each setback makes the unsent message matter more. | Viewers can say how low the battery was at each failure; attention rises rather than dips at the shop beat. |
| intent.anime_feel | USER_REQUIREMENT | It looks and feels like Japanese animation. | Viewers describe it as "anime-style" unprompted. |
| intent.soft_but_cinematic | USER_REQUIREMENT | Soft and pastel to look at, but framed and lit like cinema. | Stills taken at random read as composed frames with a clear light direction, not flat illustration. |

## Tone and anti-goals
Canon: `tone.register`, `tone.comedy_source`, `tone.the_turn`,
`tone.ending_restraint`, `tone.anti_goals`.

- **Register (DECISION):** warm, light romantic comedy-drama. We laugh *with* his
  bad luck, never *at* him.
- **Where the comedy comes from (DECISION):** the world's bad timing and his
  earnest persistence. Each failure arrives at the worst possible moment; he tries
  again anyway. The comic engine and the rising stakes are the same engine.
- **The turn (DECISION):** one clean turn from comic to tender, when he takes up
  the hand-crank charger. No gags after it.
- **The ending (DECISION):** restraint. Her smile is the only answer. No reply,
  no dinner, no reunion; the dark phone is gentle, not tragic and not a punchline.
- **The film is not (anti-goals):** manic slapstick · melodrama or tragedy ·
  saccharine sentimentality · cynical or ironic about love · a message about
  technology being bad · sexualised in any way. Both characters are adults of
  about 20; the romance is innocent and unspoken.

## Emotional arc over the 60 s
Timings are guidance for the story-architect, not a lock (RECOMMENDATION).

| Time (approx.) | Beat | Feeling | Energy |
|---|---|---|---|
| 0–8 s | Nerve gathered; he goes to call her; battery warning | Hopeful nerves → "oh no" | Rising |
| 8–22 s | The car: plugs in, car dies | Comic frustration, still optimistic | Brisk, comic |
| 22–36 s | The shop: finds a socket, power cuts out | Comic disbelief, stakes now real | Brisk, peaks |
| 36–50 s | The crank: slow, patient effort, battery ticks up | Quiet determination, tenderness | Drops, slows |
| 50–55 s | Types and sends; signal bar strains; it goes | Held breath → release | Still, then lift |
| 55–60 s | Her phone lights; she reads, smiles. His screen goes dark. | Warm, open hope | Soft, settling |

The shape is two quick comic peaks followed by a long exhale. The turn at about
36 s should feel like the film taking a breath.

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
  crank handle, a signal bar) and are framed as seriously as faces.
- *Comedy:* expressive reaction beats (a frozen stare, a slumped shoulder, a pause
  before he gives up and tries again), timed on held frames.

**"Pastel colours"**
- *Colour:* a soft, light-valued palette with low-to-medium saturation. Contrast
  comes from value and warm/cool shifts, not from saturated colour.
- *Colour as story:* the phone's UI colour (battery red, signal) is one of the few
  saturated accents, so the viewer tracks the stakes by eye.
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
screen standing in for the courage to say something. What makes the film its own:
- **The phone as the second character.** Its battery, its glow and its signal bar
  carry the plot and the emotion without words.
- **The hand-crank as the heart.** A modern problem is solved by the oldest kind
  of power, his own effort. The turn from comedy to tenderness happens on that
  physical, repetitive gesture.
- **One line of text as the only dialogue.** The confession is the only language
  in the film, so it lands with the weight of every silent second before it.
- **An answer we never hear.** The film ends on her smile and his dark screen.

## Production constraints as style
- **Stylised proxy characters.** Simple, graphic character shapes are a choice:
  they suit the anime design principle (readable silhouettes, expressive faces)
  and keep the emotion in faces and poses. Invest detail in the faces and in a few
  hero props (phone, car, charger), not in bodies or crowds.
- **Blender 5.2 EEVEE toon/cel shading on a laptop.** Cel shading with two or three
  tone steps and clean shadow shapes is the look, not a compromise. It serves the
  pastel palette and keeps renders cheap. Favour simple, well-motivated lights over
  heavy volumetrics; atmosphere comes from colour and gradient skies, not
  simulation.
- **Held poses and limited animation.** Anime-style holds and small cycles cut the
  animation load and are the comic timing tool, so the constraint and the style
  are the same thing.
- **Almost wordless.** No lip-sync. Story comes from the phone UI (battery,
  signal, typed message), sound (engine sputter, power hum dying, crank ratchet,
  send chime) and acting. The on-screen English message must be short and legible
  at a glance.
- **60 s.** Four locations at most (where he calls from, the car, the shop, the
  crank location), plus her space. Keep sets minimal and reuse lighting rigs.

## Risks
| Risk | Why it matters | How later phases test it |
|---|---|---|
| The chain feels repetitive (failure, failure) | Breaks `intent.rising_stakes`; the comedy flattens | STORY: each failure must escalate (lower battery, more effort, bigger setback); G2 checks that the shop beat raises the stakes over the car beat |
| Where the hand-crank charger comes from | If it just appears, the triumph feels unearned | STORY must set it up or motivate it (seen earlier, found in the shop, a stranger's, etc.) |
| Too much plot for 60 s | The crank and ending get rushed, and they carry the film | Screenplay timing: the tender last third keeps at least ~20 s |
| The message text (the confession) | It carries the whole emotional payoff; clichéd or long wording deflates it | SCREENPLAY proposes 2–3 short options for the user at G2 |
| Pastel drifts into saccharine | Anti-goal; weakens the comedy | LOOK: keep value contrast and motivated light; G4 compares stills against the anti-goals |
| Proxy characters too stiff to act | The film depends on faces and posture | First Blender preview (G6): a face and posture test before full animation |
| Her smile must read clearly in a few seconds | It is the only answer the film gives | CINEMATOGRAPHY: a dedicated close-up held long enough; G7 checks readability |
| "Japanese animation style" becomes imitation of a known work | Originality | Every reference stays a principle; QA checks designs against named works |
