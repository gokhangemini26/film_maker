---
description: "Where the film stands - phase, gates, stale work, pending decisions - in plain language, with the next step."
argument-hint: "[project-slug]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Run `fm status`, `fm validate -q` and `fm plan --scope film` for `$ARGUMENTS`. Summarise
for the user in plain language: current phase and whether it waits for them; each gate
(approved / drifted / pending); anything stale and why; change requests awaiting a
decision; revise notes not yet addressed; and the single next step (a `/film-*` command
or the exact `fm` command they must type themselves). Change nothing.
