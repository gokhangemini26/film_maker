---
fm:
  id: g1_review                 # g1_review .. g5_review
  kind: gate_review
  phase: CREATIVE_DIRECTION     # the phase the gate closes
  status: PROPOSED
  owner_role: qa-supervisor
  derived_from:                 # EVERY artifact (and for G5 every shot) the gate approves
    - ref: artifact:brief
    - ref: artifact:creative_direction
verdict: WARN                   # PASS | WARN | FAIL — advisory
reviewed_gate: G1
title: G1 review — Creative direction
---
# G1 review — Creative direction

**Verdict: WARN** — one-sentence reason.

## What the human should look at first
1. The most important finding, with evidence.
2. ...

## Findings

| # | Dimension | Level | Evidence | Finding | Suggested fix |
|---|---|---|---|---|---|
| 1 | Intent fidelity | WARN | `canon:tone.register`, CREATIVE_DIRECTION §3 | ... | ... |

## Deterministic checks
- `fm validate`: n errors, n warnings
- `fm intent`: intents not served: ...
- `fm check continuity` (G5): ...

## Not reviewed
Anything outside this review's reach (e.g. visual frames before M4).
