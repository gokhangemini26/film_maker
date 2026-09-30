---
description: "Animation vocabulary and one structured anim file per shot with named events, spec-level motion checks, then frames from Blender. Ends at ANIMATION_PREVIEW; no gate."
argument-hint: "[project-slug] [shot ids or scope] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm resolve:*), Bash(fm qa motion:*), Bash(fm check anim:*), Bash(fm blender frames:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **ANIMATION** (the project must be past G6; `fm status` says so, never skip a gate)
- agents, in order: `animation-director` (vocabulary canon proposals, then `09_animation/<shot>.anim.yaml` for every shot in scope, with events) → `blender-td` (bake and render frames)
- gate: none here (G7 closes ANIMATION_PREVIEW; see `/film-post`)
- project, scope and notes: `$ARGUMENTS` (first word = project slug if it names a project, then shot ids or a scope, then notes passed verbatim)
- deterministic checks: `fm validate -q`, `fm check anim` (lands in M6 step A1), `fm qa motion` tier 0 (lands in M6 step D1)
- frames: `fm resolve` then `fm blender frames --every-key` (lands in M6 step C4); the qa-supervisor reads the contact strips inside `/film-post`

Builders never parse prose: a shot with an anim file must resolve a `motion` block (lands in M6 step A3). If a subcommand above
is unknown to `fm`, say which M6 step provides it and continue with what exists; never report a check as passed that did not run.
Send FAIL findings back to the `animation-director` once, builder problems to `blender-td`. The human ratifies the vocabulary at G7.

Then stop and report: files written, vocabulary proposed, checks run and not run, conflicts for the human, and `/film-playblast` as next.
