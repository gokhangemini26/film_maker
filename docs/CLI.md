# `fm` command reference

`fm [-p PROJECT] <command>`. Project resolution: `-p` > `FM_PROJECT` > the
project containing the current directory > the only project.

**Who:** A = agents/anyone, H = human at an interactive terminal only.

| Command | Who | What |
|---|---|---|
| `fm init SLUG --title T [--sandbox]` | A | Create a project. `--sandbox` (permanent) allows simulated approvals for demos/tests. |
| `fm status [--repair-cache]` | A | Show status, regenerate STATUS.md. `--repair-cache` rebuilds state.yaml from the ledger (blocked for Claude Code so a person investigates first). |
| `fm list` | A | List projects. |
| `fm validate [-q] [--json]` | A | All checks. Exit 1 on errors. |
| `fm submit` | A | Submit the current gated phase for review. |
| `fm advance` | A | Next phase, if gates allow. |
| `fm approve G# [--notes T] [--ack-review]` | **H** | Approve a gate: record hashes, lock its canon domains. Re-approves a drifted gate. `--notes` records your answers to the review's open questions. A WARN/FAIL QA review needs `--ack-review`; the acknowledgement is carried forward in STATUS.md. |
| `fm amend G# REF.. --note T` | **H** | Accept a wording-only edit to approved documents without re-approving the gate: records their new hashes as approved and restamps downstream stale nodes with the note. Documents only; canon changes still need a change request. |
| `fm revise G# --notes ..` | **H** | Send back with feedback. |
| `fm reject G# --notes ..` | **H** | Reject the submission. |
| `fm authorize final-render [--scope]` | **H** | Required before entering FINAL_RENDER. |
| `fm canon list [--domain D]` / `show ID` | A | Inspect canon (status comes from the ledger). |
| `fm canon approve|lock|reject ID` | **H** | Decide a single entry. |
| `fm canon annotate ID --notes T` | A | Correct the free-text notes of an entry, even a LOCKED one. Notes are not part of the decision hash; every annotation is logged in the ledger with old and new text. |
| `fm change propose ID --set f=v .. --reason ..` | A | Propose changing an approved/locked entry. Values parsed as YAML. |
| `fm change list` / `show CHANGE-NNN` | A | Inspect change requests. |
| `fm change approve|reject CHANGE-NNN` | **H** | Decide a change request. |
| `fm resolve [--scope S]` | A | Resolve shots + canon into engine-ready JSON (`09_resolved/`), recorded as derived nodes. |
| `fm blender preview [--shots ..] [--width N] [--draft] [--jobs N]` | A | One still per shot into `10_blender/previews/`, one Blender process per shot, each recorded as `render:preview_<shot>`. Uses the pinned Blender (refused on mismatch); `--draft` uses the bpy module and is never G6 evidence. |
| `fm qa stills` | A | Deterministic checks on `10_blender/previews/` (missing, flat, near-black, clipped-white frames, colour drift); writes `qa/stills_report.json`, records `qa:stills`. Exit 1 on FAIL. Technical only: never evidence of creative correctness. Needs Pillow (`pip install -e ".[vision]"`). |
| `fm impact REF..` | A | Downstream of REFs, grouped by layer (nothing is modified). |
| `fm plan --scope S` | A | What in scope is stale and must be regenerated. |
| `fm deps REF` | A | Hash, upstream (ok/CHANGED/structural), downstream. |
| `fm hash REF` | A | Current content hash. |
| `fm stamp FILE|REF [--note]` | A | Record upstream hashes into `derived_from`. |
| `fm record REF --from R.. [--file F]` | A | Record a derived product (resolved/blend/render/qa). |
| `fm intent [--json]` | A | Intent coverage: canon, documents and shots serving each intent; decisions serving none. |
| `fm check continuity` | A | Shots vs continuity canon, SCENES.yaml, characters, running time. Exit 1 on FAIL. |
| `fm log [--tail N]` | A | Ledger + chain verification. |
| `fm doctor` | A | Environment + Blender pin check. Exit 4 if Blender is refused. |
| `fm schema export [--out DIR]` | A | Write JSON Schemas. |

Human commands prompt `Type 'G3' to confirm:`. In a sandbox project,
`--sandbox-confirm` replaces the prompt and the ledger marks it `simulated`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | Validation failed |
| 2 | State/usage error (e.g. gate not approved) |
| 3 | Authority refused (agent attempted a human action, no terminal, bad confirmation) |
| 4 | Blender version refused / not found |
| 5 | Integrity error (ledger damaged, locked entry edited, conflict) |

## Environment variables

| Var | Purpose |
|---|---|
| `FM_ROOT` | Repository root (otherwise found from cwd) |
| `FM_PROJECT` | Default project |
| `FM_ACTOR` | `human:<name>` / `agent:<role>` / `system:<name>` |
| `FM_BLENDER` | Override the Blender executable |
| `FM_FIXED_TIME` | Pin timestamps (tests) |
