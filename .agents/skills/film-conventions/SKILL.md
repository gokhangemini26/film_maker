---
name: film-conventions
description: "Shared FILM_MAKER rules every film agent follows - fm artifact blocks, canon protocol, intent and rationale, fact tags, originality, handoff format. Preloaded into every film subagent."
user-invocable: false
---

# FILM_MAKER conventions

## Purpose
One set of rules for every agent so that work from different agents (or
different models, or a person) fits together, stays traceable, and never
overrides a human decision.

## When to use
Always, before and while producing any FILM_MAKER artifact. Detailed
references live next to this file:
- `ARTIFACT_CONVENTIONS.md` — the `fm:` block, `derived_from`, stamping, file locations
- `CANON_PROTOCOL.md` — reading canon, proposing entries, change requests
- `INTENT_AND_RATIONALE.md` — separating intent from implementation; writing rationale
- `ORIGINALITY.md` — learning from references without copying them
- `templates/` — skeletons for every document type

## Required inputs
- The project directory (`projects/<slug>/`) and its current phase: run `fm status`.
- `canon/*.yaml` for every domain your work touches, and `fm canon list`.
- The upstream artifacts named in your task.

## Process (every task)
1. `fm status` — confirm the phase your work belongs to.
2. Read `canon/intent.yaml` first, then the canon and documents your work depends on.
   LOCKED entries are constraints. Approved documents are the agreed version.
3. Produce your work as **PROPOSED** files in the paths you own (see your agent file).
4. Every document gets an `fm:` block with `derived_from` (what you built it from)
   and `serves` (which intents it serves).
5. Run `fm stamp <file>` for each file you wrote, upstream files first.
6. Run `fm validate -q`. Fix every ERROR you caused. Read the WARNs and fix the
   ones in your area.
7. Return the handoff (below). Never run `fm submit`, `fm advance` or any human
   command yourself unless your task says so; the orchestrator does that.

## Output format — the handoff
End every task with exactly this section:

```
## Handoff
- Files written: <paths>
- Canon proposed: <ids, each with the intent it serves>
- Assumptions (tagged ASSUMPTION): <list or "none">
- Open questions for the human: <max 3, each with why it matters, or "none">
- Conflicts with locked canon: <none | change request proposed: CHANGE-NNN>
- fm validate: <n errors, n warnings>
- Not done / limits: <anything you could not do>
```

## Validation rules
- You write `status: PROPOSED` only. Never APPROVED, LOCKED, SUPERSEDED or REJECTED.
- Never edit a LOCKED canon entry. If your work needs it changed, run
  `fm change propose <id> --set field=value --reason "..."` and say so in the handoff.
- Never edit `state.yaml`, `STATUS.md`, `CHANGELOG.md`, `.fm/`, `changes/`.
- Never run `fm approve|revise|reject`, `fm canon approve|lock|reject`,
  `fm change approve|reject`, `fm authorize`, or anything with `--sandbox-confirm`.
- Every DECISION in story/world/characters/look/camera/animation/audio has a
  `rationale` and should `serve` at least one intent.
- Tag statements honestly: FACT, DECISION, ASSUMPTION, RECOMMENDATION,
  USER_REQUIREMENT, DEPENDENCY, UNKNOWN. Only the user's own words are
  USER_REQUIREMENT. Never upgrade an assumption to a fact.
- Stay in your lane: propose canon only in your role's domains.

## Failure conditions
Stop and report instead of guessing when:
- the phase is wrong for your task;
- a LOCKED decision blocks the work (propose a change, don't work around it);
- required upstream artifacts are missing or stale (`fm plan --scope film`);
- the brief lacks something that materially changes the result — ask, max 3 questions;
- `fm validate` shows errors you cannot resolve in your own files.
Never claim a file exists, a check passed or a command succeeded without having seen it.

## Examples
A look-director proposing a colour:

```yaml
  - id: look.color.accent
    statement: Warm amber from practical sources only.
    value: "#E0A040"
    rationale: >
      Warmth is withheld from the ambient light so it can mean hope; keeping it
      practical-only lets the audience track it as an object in the world.
      Rejected: teal/orange grading, which spreads warmth everywhere.
    serves: [intent.hope]
    tag: DECISION
    status: PROPOSED
    source: agent:look-director
```
