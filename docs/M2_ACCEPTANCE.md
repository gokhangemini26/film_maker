# M2 acceptance report

Date: 2026-09-29. Demo film: **Last Signal** (real project, `projects/last_signal`),
60 s, 6 scenes, 38 shots, taken from brief to gate G5 by the agents with every
gate decided by a person at a terminal.

| # | Criterion (from the approved M2 scope) | Result | Evidence |
|---|---|---|---|
| 1 | 9 agents, skills, 13 commands pass the lint test | PASS | `tests/test_agent_layer.py` |
| 2 | M1 tests still pass; new `fm` features tested | PASS | 125 tests green in the cloud clone (2026-09-29) |
| 3 | Demo reaches G5 with `fm validate` 0 errors, everything stamped, all intents served by at least one shot, continuity clean, a review per gate | PASS | validate 0 errors / 0 warnings; `fm intent`: all 6 intents served (6-26 shots each), 0 unserved decisions; `fm check continuity` 0 FAIL / 0 WARN; G1-G5 reviews present (all WARN, advisory) |
| 4 | Every gate decision is `human:*` with typed confirmation; no agent-originated human action | PASS | ledger records 5, 7, 11, 14, 17, 20, 21, 23 are all `human:gokhan_guler`, `confirmation: typed`; chain verified OK |
| 5 | Revision demo regenerates only what `fm plan` lists, logs CHANGE-001, gates re-approved | NOT DEMONSTRATED on this film | You chose to skip it. The behaviour is covered by tests (`test_deps_changes_scopes`, the toy-film drift tests) and was exercised in practice by the door-wording edit: G3 and G4 drifted, downstream documents were re-stamped with notes, and you re-approved both. No change request (CHANGE-nnn) has been run end to end on a real film. |
| 6 | Docs updated | PASS | AGENTS, SKILLS, COMMANDS, WORKFLOW, CLAUDE.md |

## What the run taught us (feed into M3 and later)

1. **Wording edits after approval are expensive.** A one-line door fix in two
   approved bibles drifted G3 and G4 and needed ~10 re-stamps and two
   re-approvals. Consider a "wording-only amendment" path or a smaller
   dependency granularity.
2. **`fm change propose` cannot change `notes`.** A stale note on a LOCKED entry
   (`world.locations.ren_car`) cannot be corrected by any route. Either allow
   `notes` as a changeable field or move such text out of canon.
3. **Advisory WARN findings lock silently.** G5 was approved with QA's open
   findings (phone-lit rule worded backwards, final-image hold, glovebox reach).
   Consider requiring the human to acknowledge open findings, or a "carry
   forward" list that M3/M4 must resolve.
4. **Approving does not record your answers to open questions.** `fm approve`
   has no notes field, so decisions such as the door route live only in
   documents. `story.message` still has wording UNKNOWN in locked canon.
5. **Canon written before later phases goes stale in text.** Locked rationales
   still describe the sky behind Hana's head after the desk decision.

## Known open items on Last Signal (locked but unresolved)

- Invitation wording (A/B/C) not chosen; shots assume A.
- Title/credits exemption from `tone.wordless` undecided.
- Amber sent-tick contrast (1.32:1) unresolved.
- Stale locked text: `world.locations.ren_car.notes`; three Hana rationales.
