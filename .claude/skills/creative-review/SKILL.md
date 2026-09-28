---
name: creative-review
description: "Review a phase's work against intent, canon and craft using the review rubric, and write the gate review report (qa/reviews/G#_REVIEW.md) with evidence-backed PASS/WARN/FAIL findings. Used by the qa-supervisor before every gate."
user-invocable: false
---

# Creative review

## Purpose
Give the human an honest, evidence-based second opinion before each gate.
The reviewer did not make the work, so it can judge it. Its verdict is advice:
it cannot approve, block or pass anything.

## When to use
Before `fm submit` at G1–G5 (every phase command runs it), and `/film-review` on demand.

## Required inputs
- The gate being reviewed and everything it approves: artifacts of the gate's
  phases (see `fm status` / `docs/WORKFLOW.md`) and, for G5, every shot.
- All locked canon (intent first), `film-conventions/REVIEW_RUBRIC.md`,
  `ORIGINALITY.md`, the template `templates/GATE_REVIEW.md`.
- Deterministic results: `fm validate -q`, `fm intent`, and for G5 `fm check continuity`.

## Process
1. Run the deterministic checks and record their results first.
2. Read the reviewed work fully. Read intent and tone canon again before judging.
3. Go through every rubric dimension relevant to the gate. For each finding,
   cite evidence (file + section, canon id, shot id) and suggest a fix and an owner.
4. Check rationale quality: pick the 3 most important decisions and test each
   rationale for choice + mechanism + rejected alternative.
5. Check originality against CREATIVE_DIRECTION's originality statement.
6. For G5 also apply the continuity-check skill.
7. Decide the verdict: FAIL if anything contradicts intent/canon or cannot be
   produced; WARN if the human should look at something; otherwise PASS.
   Do not soften a FAIL to WARN to be agreeable, and do not invent problems to look thorough.
8. Write `qa/reviews/G#_REVIEW.md` from the template. `derived_from` must list
   **every** artifact the gate covers (and every shot for G5) — `fm submit`
   rejects incomplete reviews. Then `fm stamp` it.
9. You do not fix the work. Findings go to the orchestrator, which routes them to owners.

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
