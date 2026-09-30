---
description: "Chunked final render of every shot after the human has authorized it, frame checks, then the G8 review and submit. Ends at gate G8."
argument-hint: "[project-slug] [shot ids or scope]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm resolve:*), Bash(fm qa motion:*), Bash(fm qa review-status:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill. Run `fm status`; the project must be in **FINAL_RENDER**. That needs G7 approved **and** the human's own
final-render authorization in the ledger (see `docs/WORKFLOW.md`); you never run that command. If it is missing, stop and tell the user to run it in their terminal.

- agents, in order: `blender-td` (`fm blender final`, chunked and resumable, pinned Blender only; frames counted against the frame table) → `qa-supervisor` (G8 review)
- gate: **G8**
- project and scope: `$ARGUMENTS` (first word = project slug if it names a project; the rest = shot ids or scope)
- deterministic checks: `fm validate -q`, `fm qa motion` on the final frames (M6 step D1); `fm blender final` itself lands in M6 step F3
- expect a permission prompt before the render starts: `fm blender final` is deliberately not pre-approved

If `fm blender final` is unknown to `fm`, say it lands in M6 step F3 and stop; never claim frames exist that were not counted on disk. Report unknown
licences (assets or audio) as blocking. The human scrubs the master with sound, so do not continue past the gate in the same turn.

Then stop at the gate with the frame counts, the review verdict, the licence table, and `fm approve G8` or `fm revise G8 --notes "..."`.
