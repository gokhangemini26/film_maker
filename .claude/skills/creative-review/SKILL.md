---
name: creative-review
description: "Review a phase's work against intent, canon and craft using the review rubric, and write the gate review report (qa/reviews/G#_REVIEW.md) with evidence-backed PASS/WARN/FAIL findings. Used by the qa-supervisor before every gate (G1-G5 in M2, G7-G8 in M6)."
user-invocable: false
---

# Creative review

## Purpose
Give the human an honest, evidence-based second opinion before each gate.
The reviewer did not make the work, so it can judge it. Its verdict is advice:
it cannot approve, block or pass anything.

## When to use
Before `fm submit` at G1–G5 and G7–G8 (every phase command runs it), and `/film-review` on demand.

## Required inputs
- The gate being reviewed and everything it approves: artifacts of the gate's
  phases (see `fm status` / `docs/WORKFLOW.md`) and, for G5, every shot.
- All locked canon (intent first), `film-conventions/REVIEW_RUBRIC.md`,
  `ORIGINALITY.md`, the template `templates/GATE_REVIEW.md`.
- Deterministic results: `fm validate -q`, `fm intent`, and for G5 `fm check continuity`; for G7 `fm qa motion` and
  `fm qa audio`; for G8 `fm qa motion` on final frames and `fm qa delivery` (each only if it exists yet).
- G7: the anim files, contact strips, AUDIO_BIBLE, AUDIO_CUES, EDIT_PLAN, POST_PLAN. G8: the final frame manifest and licence table.

## Process
1. Run the deterministic checks and record their results first.
2. Read the reviewed work fully. Read intent and tone canon again before judging.
3. Go through every rubric dimension relevant to the gate. For each finding,
   cite evidence (file + section, canon id, shot id) and suggest a fix and an owner.
4. Check rationale quality: pick the 3 most important decisions and test each
   rationale for choice + mechanism + rejected alternative.
5. Check originality against CREATIVE_DIRECTION's originality statement.
6. For G5 also apply the continuity-check skill (for G7, its prop-state continuity step).
   For G7 and G8 also apply the **G7/G8 rubric** below.
7. Decide the verdict: FAIL if anything contradicts intent/canon or cannot be
   produced; WARN if the human should look at something; otherwise PASS.
   Do not soften a FAIL to WARN to be agreeable, and do not invent problems to look thorough.
8. Write `qa/reviews/G#_REVIEW.md` from the template. `derived_from` must list
   **every** artifact the gate covers (and every shot for G5) — `fm submit`
   rejects incomplete reviews. Then `fm stamp` it.
9. You do not fix the work. Findings go to the orchestrator, which routes them to owners.

### G7/G8 rubric (M6)
Add these dimensions to the review; each finding still needs evidence, a fix and an owner.
- **Motion coherence** (G7): do the pose keys, holds, gaits and eyelines in the contact strips carry the shot's
  `creative_intent` and the character's movement canon? Weight, anticipation and the holds the shot needs are present;
  no comic-register motion after the turn; the vocabulary reads as one language. Cite shot id and frame numbers.
- **Sync** (G7): every audible event has a cue on the right frame, and cues reference events by id, not hand-typed
  frames. Quote `fm qa audio` coverage results; do not re-derive them.
- **Silence** (G7): the silence map is honoured in the cue sheet (and in the rendered-mix result if `fm qa audio` ran);
  silence is used where canon says, and the world is not digitally silent elsewhere.
- **Sound vs canon** (G7): no speech or music the tone canon forbids (`tone.wordless`); palette, motifs, perspective
  and mix target match `audio.*`; unknown licences are listed.
- **Post vs canon** (G7/G8): only locked finish steps, transitions only from `camera.rhythm.transitions`, titles handled
  per the human's ruling; open D-decisions are listed for the human.
- **Final frames** (G8): frame set complete against the frame table, no drift from the approved animatic,
  `fm qa delivery` result quoted.
- **Not reviewable by you**: how the audio sounds. You review the cue sheet, the frames and the reports; whether the
  hum death lands or the mix is right is the human's call and goes under "Not reviewed".

## Output format
Template `templates/GATE_REVIEW.md`: front-matter with `verdict` and
`reviewed_gate`; sections: Verdict line · What the human should look at first
(max 3) · Findings table · Deterministic checks · Not reviewed.

## Validation rules
- Every finding has evidence and a suggested owner.
- `verdict` ∈ PASS/WARN/FAIL and matches the findings.
- `derived_from` covers everything the gate approves.
- Only `qa/reviews/` is written.

## Failure conditions
- The work to review is missing or stale → report instead of reviewing.
- You find yourself agreeing with everything → re-read the intents and look
  for the weakest rationale; say explicitly if it is genuinely all sound.

## Examples
Finding: `| 2 | Intent fidelity | FAIL | canon:look.color.accent_hope, SC01_SH010 lighting | Amber practical sits right beside Mara in the first shot, spending the hope motif before the story earns it | move the practical out of reach (frame left, 10 m) | cinematographer |`
