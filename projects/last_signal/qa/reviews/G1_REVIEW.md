---
fm:
  id: g1_review
  kind: gate_review
  phase: CREATIVE_DIRECTION
  status: PROPOSED
  owner_role: qa-supervisor
  derived_from:
  - ref: artifact:brief
    hash: sha256:df35810dd51f64d6713210e3ddc72d55126a0551d908546cde31dabe79520116
  - ref: artifact:brief_analysis
    hash: sha256:3b841e76a7d59e474cbb0314f167d1c50586a4463157fff582e604b083f343e8
  - ref: artifact:creative_direction
    hash: sha256:b7c238c28c52e5272c03e982fcff8887704e380f8f86932b9a17e04794d18e50
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
  summary: Advisory QA review of G1 (creative direction) for Last Signal.
  stamped_content_hash: sha256:a1372a888f9d444b79fbeb11122fd4a65653a191df11e8f84bcc3c62238709a8
verdict: WARN
reviewed_gate: G1
title: G1 review — Creative direction
---
# G1 review — Creative direction

**Verdict: WARN** — the direction is sound, well-reasoned and original, but it
quietly moves the love confession from the dinner into the message and drops
the phone call. Those two story facts should be settled by the human now,
before the intent locks.

## What the human should look at first
1. **Is the message the dinner invitation or the love confession?** In your
   brief, he invites her to dinner, *where* he plans to tell her he loves her
   (`canon:intent.race_against_battery`; brief.yaml `story_idea`, `concept`).
   CREATIVE_DIRECTION turns the message itself into the confession: the Logline
   has "a love confession waiting to be sent", and the Originality statement
   says "The confession is the only language". Under Risks, the message text is
   "the confession". Two readings follow. (a) The message is the invitation: her
   smile means "yes to dinner", and the confession is still to come. (b) The
   message is the confession: the dinner plan is dropped. Both are valid films,
   but they are different films, and her smile means something different in
   each. The "The film in a paragraph" section doesn't commit either way. Please
   decide at G1 and have it written into the intent.
2. **Does the phone call happen?** Your brief opens with "calls a girl", and
   `intent.race_against_battery` keeps "he calls to invite her". You also asked
   for an almost wordless film with no spoken answer, and CREATIVE_DIRECTION's
   0–8 s beat is only "he goes to call her; battery warning". Nothing says
   whether the call rings, fails to connect or is abandoned, or why he switches
   to a typed message. Since the film has no dialogue, the call has to fail
   before anyone speaks. That is a small story decision, but it is the film's
   inciting incident. At minimum, record it as an open item for the
   story-architect. A clean option: the call dies on the first ring, which is
   what pushes him to text.
3. **60 s is tight for the setup, not for the ending.** The tender last third
   gets 24 s (36–60 s), which is healthy. The weak point is 0–8 s. With no words,
   those 8 s must show the friendship, his crush, the dinner plan and the call
   attempt. On top of that, the hand-crank charger has to be set up somewhere
   (see Risks, "Where the hand-crank charger comes from"). The film also plans
   up to five spaces: his call location, car, shop, crank location and her
   space (Production constraints, "60 s"). Recommend telling STORY to merge
   spaces (e.g. he calls from the car; the crank is found at the shop) and to
   set up the crank inside an existing beat rather than adding time.

## Findings

| # | Dimension | Level | Evidence | Finding | Suggested fix | Owner |
|---|---|---|---|---|---|---|
| 1 | Intent fidelity | WARN | `canon:intent.race_against_battery` ("where he plans to tell her he loves her") vs CREATIVE_DIRECTION §Logline, §Originality statement ("The confession is the only language"), §Risks row 4 | The direction reinterprets the user's story: the confession moves from the planned dinner into the sent message. This is not tagged as a DECISION or RECOMMENDATION, so it looks like the user's story when it isn't. | Human decides at G1: message = invitation, or message = confession. Then make CREATIVE_DIRECTION consistent with that choice. If "confession" is chosen, say it explicitly as a RECOMMENDATION with a rationale. If "invitation" is chosen, reword the Logline, Originality statement and Risks row. | creative-director (human decision first) |
| 2 | Narrative coherence | WARN | `canon:intent.race_against_battery` ("he calls to invite her"); brief.yaml `special_requirements` (no spoken dialogue); CREATIVE_DIRECTION §Emotional arc 0–8 s | The call is in the locked-to-be intent, but the direction never says what happens to it. A connected call would break the wordless requirement. Leaving this to the storyteller risks either dialogue creeping in or the call silently disappearing. | Add a line to CREATIVE_DIRECTION (or a STORY brief note): the call never connects (battery dies or warning cuts it off), which motivates the typed message. Decision can sit with story-architect at G2 if the human prefers, but record it as an open item. | creative-director / story-architect |
| 3 | Pacing / budget | WARN | CREATIVE_DIRECTION §Emotional arc (0–8 s setup), §Production constraints ("Four locations at most … plus her space"), §Risks row 2 (charger setup) | 8 s is very little to convey, without words, his crush, the dinner plan and a failed call. The crank's setup also needs screen time. Five spaces in 60 s spend seconds on establishing shots. | Tell STORY: at most 3 of his spaces + her space. Plant the crank charger inside the car or shop beat (e.g. glimpsed on a shelf before the blackout). Let a single prop (e.g. a draft message or a restaurant card) carry "dinner" in the setup. | story-architect |
| 4 | Intent fidelity | WARN | brief.yaml `special_requirements`; `canon/tone.yaml` (all entries) | "Almost wordless, only the typed English message, no spoken answer" is one of the user's firmest requirements. At G1 it lives only in brief.yaml, and none of the canon being locked (intent or tone) records it. Downstream agents read canon first. | Either add it to `tone.anti_goals` / a tone entry ("no spoken dialogue; the only words are the typed English message"), or have the human confirm the approved brief is enough. | creative-director |
| 5 | Intent fidelity | WARN (minor) | brief.yaml `emotional_goal`; `canon:intent.comic_then_tender` ("turn quiet and tender"); BRIEF_ANALYSIS §What the user asked for ("her small smile") | The user's answers as relayed to QA say "turning tender" and "she reads it and smiles". The recorded USER_REQUIREMENTs add "quiet" and "small". The notes admit to "lightly edited" wording. "Quiet" changes the sound design (`tone.the_turn`: "quiet and slow"). | Human confirms the wording at G1. If "quiet" was not the user's word, move it into `tone.the_turn` as a DECISION with rationale and keep the intent to the user's words. | creative-director |
| 6 | Intent fidelity | PASS (advice) | `canon:intent.earned_last_signal`, `canon:intent.rising_stakes`; `fm intent` | **earned_last_signal is useful.** It is the only intent that makes the crank's *cause* matter, it backs `tone.the_turn`, and its test (viewers credit the crank, not luck) is measurable. **rising_stakes is partly redundant.** `race_against_battery` already implies the race, and `tone.comedy_source` already builds escalation into the comedy. Its added value is the escalation test ("attention rises rather than dips at the shop beat"). | Keep earned_last_signal. rising_stakes is optional: keep it if you want escalation enforced as a gate test at G2, or drop it and nothing is lost except that test. | human |
| 7 | Narrative coherence | WARN (minor) | CREATIVE_DIRECTION §Emotional arc 50–55 s ("signal bar strains") | A second mechanic (weak reception) is added to the battery in a 5 s beat. Two meters to read at once can blur the stakes the film spent 50 s building. It is defensible as the title's "last signal", but it is an addition, not the user's story. | Tag as RECOMMENDATION. STORY decides whether "last signal" means the last of the battery (simpler) or also network signal. | creative-director / story-architect |
| 8 | Rationale quality | PASS | `canon:tone.register`, `canon:tone.comedy_source`, `canon:tone.the_turn` | All three name a choice, a mechanism and a rejected alternative. register: affection keeps us rooting for him through 3 failures; farce rejected. comedy_source: timing escalates toward zero battery, so comedy and stakes share one engine; pratfall rejected. the_turn: a single turn signals stakes becoming emotional; sprinkled jokes rejected. `tone.ending_restraint` names two rejected alternatives. `tone.anti_goals` is the weakest ("no stated anti-goals" is a straw-man alternative), but it is acceptable for a list of exclusions. | none | — |
| 9 | Emotional coherence | PASS | CREATIVE_DIRECTION §Emotional arc; `canon:tone.the_turn`, `canon:tone.ending_restraint` | Two comic peaks followed by one clean turn at the crank fits the user's "gently comic, turning tender at the crank and the send". The dark phone is explicitly "gentle, not a punchline", so the ending does not re-open the comedy after the turn. | none | — |
| 10 | Originality | PASS | CREATIVE_DIRECTION §References → principles, §Originality statement; grep of 00_brief/ for studio/director/film names: none | No studio, director, film or character is used as a spec. "Japanese animation style" is translated into principles (held poses, object inserts, reaction beats, expressive faces). The statement names the film's own identity: phone as second character, crank as heart, one line of text, the answer we never hear. | Keep QA's check of later designs against named works (Risks row 8). | — |
| 11 | Feasibility | PASS (with notes) | CREATIVE_DIRECTION §Production constraints as style, §Risks rows 6–7 | Suitable for proxy characters with EEVEE toon shading. The film has no crowds, no lip-sync and no simulation. Light failing is a lighting cue, the crank is a simple cycle, and the phone glow is emissive material plus a small light. The real risks are named: facial acting on proxies (her smile carries the ending) and legible English UI text. One gap: the on-screen font is an external asset whose licence is UNKNOWN (ORIGINALITY.md §Assets). Also keep the car breakdown to sound, a slump and light change, not smoke or particles. | Record the message font and phone-UI assets as licence UNKNOWN for the look-director. G6 face/posture test stays as planned. | look-director (later) |
| 12 | Scope (decide now vs later) | PASS | brief.yaml `target_audience` (assumed), `location`, `references`, `aspect_ratio`, `fps` | Correctly deferred: location/Japan, references, palette hex, names, message wording (G2). Needs a human yes/no at G1: `target_audience` (assumed by creative-director, "Confirm or change at G1"). Also needed now: findings 1 and 2. 16:9 / 24 fps are low-impact assumptions, and changing them later is cheap. | Human confirms target_audience at G1. | human |

## Deterministic checks
- `fm validate -q` (before writing this review): 0 errors, 0 warnings, 1 info
  (`BRIEF_UNKNOWN`: references, environment, location still unknown, which is expected
  at this stage).
- `fm intent`: all 7 intents are served by at least one document. By canon:
  `intent.anime_feel` 0 entries (expected until LOOK canon). `intent.soft_but_cinematic`,
  `intent.race_against_battery` and `intent.rising_stakes` 1 entry each.
  `intent.comic_then_tender` 4 entries. No intent is unserved.
- `fm check continuity`: not applicable at G1 (no shots).

## Not reviewed
- Visual inspection of any rendered frames: not available until M4, and nothing is
  rendered yet.
- Palette, lighting, camera, character and world canon: not yet written (later
  phases). Only their principles in CREATIVE_DIRECTION were checked.
- I could not verify the user's exact wording of the five answers beyond the version
  the orchestrator relayed (finding 5 depends on this).
- No reference material was supplied (`references/` is empty), so there was nothing
  to check originality against beyond named works.
