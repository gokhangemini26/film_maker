---
fm:
  id: g1_review
  kind: gate_review
  phase: CREATIVE_DIRECTION
  status: PROPOSED
  owner_role: qa-supervisor
  derived_from:
  - ref: artifact:brief
    hash: sha256:f4a7feac5c702dbb3bf357df65a25228fe90e80230f5cefb364ab9b1782b13ae
  - ref: artifact:brief_analysis
    hash: sha256:1f2799750368779bb6e30860818c7bd6260f33e955523374951d21912f7415c7
  - ref: artifact:creative_direction
    hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
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
  summary: Advisory QA review (third pass) of G1 for Last Signal after the human chose strict wordless
    and kept escalation.
  stamped_content_hash: sha256:b1adbcecb1d6d91fdb8ca00eef11c7937ff176a77c33c4b7a097e2690f5894dd
verdict: WARN
reviewed_gate: G1
title: G1 review — Creative direction (third pass)
---
# G1 review — Creative direction (third pass)

**Verdict: WARN.** The wordless contradiction is gone. CREATIVE_DIRECTION no
longer plans any readable on-screen text other than the typed invitation, and
the wording now matches your labels. One edge case is worth deciding before
`tone.wordless` locks: whether the film's **title card and credits** are
exempt from "the ONLY readable text in the film".

## What the human should look at first
1. **Title card and credits under strict wordless.**
   - `canon:tone.wordless` says "The typed English dinner invitation is the ONLY
     readable text in the film" (`readable_text: typed_english_invitation_only`).
   - The film is titled "Last Signal" (brief.yaml `title`, status given).
   - CREATIVE_DIRECTION §Originality statement assumes credits exist ("The
     confession happens after the credits").
   - As written, locking the entry forbids an on-screen title and credits, and
     post-production would need a change request to add them. A title card also
     works against the originality claim that the invitation is the only text.

   Pick one:
   - **(a)** Title and credits are outside "the film". This is the usual reading;
     add it to the entry's notes before locking.
   - **(b)** No on-screen title or credits at all. The title lives only in file
     names and metadata.

   QA leans to (a). It is a one-line clarification by the creative-director and
   not a rework. If you are happy for this to be settled later by a change
   request, it is not a blocker.
2. **Phone keyboard letters (note for later departments; no decision needed
   now).** He types the invitation on screen (CREATIVE_DIRECTION §Emotional arc
   0–10 s and 50–55 s; the heart-emoji cue in §Guidance for STORY). A standard
   phone keyboard shows readable letter keys. Under strict wordless, the keyboard
   must be kept out of frame, blurred, or drawn as unlettered keys. §Risks row
   "Stray readable text" covers signage, dashboard, packaging and UI labels, but
   not the keyboard.

   This is for the look-director and cinematographer at G4/G5. It does not change
   the direction.
3. **Everything you asked for in the last round is in place.**
   - Strict wordless is in `canon:tone.wordless` and brief.yaml
     `special_requirements`.
   - Escalation is kept in `canon:tone.comedy_source`, noted as accepted by you.
   - USER_REQUIREMENT wording now uses your labels ("Comic, then tender", "She
     reads it, smiles"). "Gentle", "quiet and slow" and "small smile" are each a
     tagged DECISION with a rationale.

## Verification: readable on-screen text in CREATIVE_DIRECTION.md
I searched for quoted words, "label", "readable/legible", "sign", "title",
"credits", "name", "card", "note", "Delivered" and "Voicemail".

| Earlier text | Now | Evidence | Status |
|---|---|---|---|
| "Delivered" | a sent tick | §Emotional arc 50–55 s; §"One meter, not two" ("no 'Delivered' label") | Resolved |
| voicemail screen | call icon that rings and gets no answer | §Film in a paragraph; §Production constraints ("never a 'Voicemail' label") | Resolved |
| her name on screen | her photo, no name | §Guidance for STORY; §Production constraints | Resolved |
| restaurant card / reservation | a lit restaurant window, a table for two | §Guidance for STORY | Resolved |
| note to himself | a heart emoji typed and deleted, or a gift/flower on the seat | §Guidance for STORY ("No written notes") | Resolved (an emoji is a pictogram, not text) |
| shop signage, dashboard, packaging | shapes, symbols, colour; checked at G4/G6 | §Production constraints; §Risks (new row) | Resolved as a rule |
| battery % | numbers allowed | `canon:tone.wordless` `numbers_allowed: true` | Consistent |
| title card / credits | not addressed | §Originality statement ("after the credits"); brief `title` | **Open** (see item 1 above) |
| phone keyboard while typing | not addressed | §Emotional arc; §Guidance for STORY | **Open, for later** (see item 2 above) |

The remaining quoted words in the document are story or user-label quotations
("tender", "Comic, then tender", "last signal" as the title's meaning). They
are not planned on-screen text.

## Verification: wording alignment

| Item | Evidence | Status |
|---|---|---|
| "Comic, then tender" as USER_REQUIREMENT | `canon:intent.comic_then_tender` statement and notes; brief.yaml `emotional_goal`; BRIEF_ANALYSIS §From the user's answers, Q5 | Aligned. No "gently" or "quiet" remains in USER_REQUIREMENT text. |
| "She reads it, smiles" as USER_REQUIREMENT | `canon:intent.open_hopeful_ending` notes; brief.yaml `emotional_goal`; BRIEF_ANALYSIS Q3 | Aligned. "small" is gone from USER_REQUIREMENT text. |
| "gentle" | `canon:tone.comedy_source` statement ("The comedy is gentle") and rationale | DECISION, labelled as the direction's reading |
| "quiet and slow" | `canon:tone.the_turn` value and rationale | DECISION with a mechanism and a rejected alternative |
| "small smile" | `canon:tone.ending_restraint` statement and rationale ("reads as private pleasure rather than a declaration") | DECISION with a mechanism |
| Strict wordless | `canon:tone.wordless` (USER_REQUIREMENT, source user); brief.yaml `special_requirements` (given); BRIEF_ANALYSIS §G1 notes | Aligned across all three |
| Escalation kept | `canon:tone.comedy_source` (DECISION, rationale opens "Accepted by the user at G1"); BRIEF_ANALYSIS lists it under the user's G1 decisions | Aligned. Correctly remains a DECISION that you accepted, not an intent. |
| Audience | brief.yaml `target_audience.note` ("Confirmed by the user at G1") | Resolved |

I found no change you did not ask for. The new additions (the signage rule, the
keyboard-free risks, picture cues) are direct consequences of choosing strict.

## Previous findings: status

| Prev # (2nd pass) | Topic | Status |
|---|---|---|
| 1 | On-screen words vs `tone.wordless` | Resolved (see the first verification table); the title and credits edge case remains |
| 2 | Escalation carried into tone canon | Resolved: accepted by the human |
| 3 | Brief vs canon wording ("quiet", "small") | Resolved (see the wording table) |
| 4 | "Last signal" = battery, not reception | Still stands as a DECISION, revisable at G2. The human saw it at the 2nd pass and raised no objection. |
| 6 | Stale audience note | Resolved |

## Findings

| # | Dimension | Level | Evidence | Finding | Suggested fix | Owner |
|---|---|---|---|---|---|---|
| 1 | Intent fidelity | WARN | `canon:tone.wordless` ("ONLY readable text in the film"); brief.yaml `title`; CREATIVE_DIRECTION §Originality statement ("after the credits") | The entry as written forbids an on-screen title card and credits, and it is about to be locked. | Human picks (a) exempt title and credits or (b) none at all. The creative-director adds one line to `tone.wordless` notes/value (e.g. `title_and_credits: outside_film`) before locking. | human, then creative-director |
| 2 | Feasibility / intent fidelity | WARN (minor, later) | CREATIVE_DIRECTION §Emotional arc (typing beats), §Risks "Stray readable text" | A phone keyboard with lettered keys would be readable text on screen during the typing beats. It is not listed among the stray-text risks. | Add "phone keyboard" to the stray-text risk, or leave it for the look-director and cinematographer: frame the keyboard out, blur it, or use unlettered keys. | creative-director (optional) / look-director, cinematographer |
| 3 | Narrative coherence | PASS | CREATIVE_DIRECTION §Film in a paragraph, §Guidance for STORY, §Risks | The chain holds: the unanswered call, then texting, then car, shop and crank, then send, her smile, and his screen going dark. With strict wordless, the dinner plan and the crush depend on picture cues alone. §Risks names this, with a G2/G5 viewer check. This is the film's main storytelling risk, and it is correctly handed to STORY. | none | — |
| 4 | Emotional coherence | PASS | CREATIVE_DIRECTION §Emotional arc; `canon:tone.the_turn` | Two comic peaks, one clean turn at about 36 s, and a gentle ending. Unchanged and sound. | none | — |
| 5 | Rationale quality | PASS | `canon:tone.comedy_source`, `canon:tone.the_turn`, `canon:tone.ending_restraint` | Each names a choice, a mechanism and a rejected alternative. The new "small smile" rationale adds a mechanism ("private pleasure rather than a declaration"). | none | — |
| 6 | Originality | PASS | CREATIVE_DIRECTION §References → principles, §Originality statement | No named studio, director, film or character is used as a spec. The strict rule sharpens the film's identity ("without a single UI word"). | none | — |
| 7 | Feasibility | PASS | CREATIVE_DIRECTION §Production constraints as style | Strict wordless reduces production load: no lip-sync, one text element, icon-based UI. The icon set and UI font are marked licence UNKNOWN, as required. Proxy characters with EEVEE toon shading remain adequate. | none | — |
| 8 | Pacing / budget | PASS | CREATIVE_DIRECTION §Emotional arc, §Guidance for STORY | The 60 s split is 10 s setup, two comic beats of about 12–14 s, and a 24 s tender third. There are at most 3 of his spaces plus hers, and the crank is planted within an existing beat. This is realistic. | none | — |

## Deterministic checks
- `fm validate -q` (before this rewrite): 0 errors, 1 warning, 1 info. The
  warning was `STALE artifact:g1_review` (brief and brief_analysis had changed),
  which this rewrite resolves. The info is `BRIEF_UNKNOWN` (references,
  environment, location), which is expected at this stage.
- `fm intent`: 6 intents, all served by at least one document. By canon entries,
  `intent.anime_feel` has 0 (expected until LOOK canon) and
  `intent.soft_but_cinematic` has 1.
- `fm check continuity`: not applicable at G1 (no shots).

## Not reviewed
- Visual inspection of rendered frames: not available until M4. Nothing is
  rendered, so stray on-screen text can only be checked from G4/G6 frames onward.
- Palette, lighting, camera, character and world canon are not yet written.
- The human's decisions after the second pass were relayed by the orchestrator.
  I verified their implementation, not their wording at source.
- `references/` is empty, so originality was checked only against named works.
