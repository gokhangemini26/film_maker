---
name: film-development
description: "Turn a user's brief, taste and references into brief analysis, locked creative intent, tone and a creative direction with an originality statement. Used by the creative-director in BRIEF and CREATIVE_DIRECTION."
user-invocable: false
---

# Film development

## Purpose
Establish what the film is *for* before anyone decides how it looks or what
happens: the intents (audience effects), the tone, and a creative direction
that interprets the user's taste into principles every later agent can follow.

## When to use
- BRIEF phase: analysing a new brief (`/film-new`).
- CREATIVE_DIRECTION phase: writing `00_brief/CREATIVE_DIRECTION.md` (`/film-direction`).
- Any time two locked decisions conflict and a resolution must be proposed.

## Required inputs
- `00_brief/brief.yaml` and the user's original words (from the orchestrator).
- References the user gave (names, links, descriptions, images in `references/`).
- `film-conventions` (preloaded) — especially `ORIGINALITY.md` and `INTENT_AND_RATIONALE.md`.

## Process

### Brief analysis (BRIEF)
1. Copy the user's explicit statements into brief fields as `status: given`.
2. For each empty field decide: (a) decidable later by another role → leave
   `unknown` and list it under "Not needed yet"; (b) inferable with low risk →
   `status: assumed` with a `note` giving the reason; (c) materially changes
   the film → a question.
3. Ask at most 5 questions, ranked by impact, each with a default. Duration,
   emotional goal, audience and ending direction usually matter most; lens
   choice and palette hex values never belong here.
4. Write the user's must-haves into `canon/intent.yaml` as `USER_REQUIREMENT`
   (their words, lightly edited). Propose further intents only as
   `RECOMMENDATION`, clearly marked, for the human to accept at G1.
5. Write `00_brief/BRIEF_ANALYSIS.md` from the template.

### Creative direction (CREATIVE_DIRECTION)
1. Restate the film in one sentence (logline-level) and one paragraph.
2. Intents: 2–5 audience effects, each testable ("the viewer should
   notice..."). Merge duplicates. Order by importance.
3. Tone: register, what the film is *not* (anti-goals), emotional range and its
   movement over time. Put the core in `canon/tone.yaml` with rationale + serves.
4. Reference interpretation: for each reference, 2–4 principles (light, camera,
   design, colour, pacing, composition) — principles, not features.
5. Originality statement: what makes this film's identity its own.
6. Constraints the production will live with (MVP: stylised proxy characters,
   Blender 5.2, laptop rendering) and how the direction turns them into style
   rather than hiding them.
7. Open creative risks and how later phases should test them.

## Output format
`00_brief/CREATIVE_DIRECTION.md` sections: Logline · The film in a paragraph ·
Intents (table: id, audience effect, how we'll know it worked) · Tone and
anti-goals · Emotional arc over time · References → principles · Originality
statement · Production constraints as style · Risks. `fm:` block with
`derived_from: [artifact:brief, canon:intent.*, canon:tone.*]` and `serves` all intents.

Canon: `intent.*` (USER_REQUIREMENT / RECOMMENDATION), `tone.*` (DECISION with rationale).

## Validation rules
- Every intent is an audience effect, not a technique.
- Nothing tagged USER_REQUIREMENT that the user did not say.
- Every tone DECISION has rationale and `serves`.
- References produce principles; no copied shots, designs, characters or names used as specs.
- `fm validate -q` has no errors from your files.

## Failure conditions
- The brief is too thin to state even one intent → ask, don't invent one.
- The user's requirements contradict each other → surface both, propose options, let the human choose.
- A reference is a copyrighted character/franchise the user wants reproduced → say it can inspire principles only.

## Examples
Weak intent: "Blade Runner-like atmosphere." Strong: `intent.city_indifference`
— "The city should feel beautiful and indifferent: the viewer admires it and
feels it would not notice if Mara disappeared." Principle from the reference:
"Light sources belong to the city, not to the people; humans are lit by
advertising and infrastructure."
