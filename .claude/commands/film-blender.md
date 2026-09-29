---
description: "Resolve shots, build Blender previews for every shot, read them, and report per-shot problems. Does not decide G6."
argument-hint: "[project-slug] [shot ids or scope]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm resolve:*), Bash(fm blender:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm log:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill. Run `fm status`; the project must be past G5. Dispatch the `blender-td`
agent with `$ARGUMENTS` (first word = project slug if it names a project; the rest = shot ids to limit the run).
It resolves, renders previews with the pinned Blender, reads every still and reports OK / builder problem /
spec problem per shot. Fix builder problems (code in `blender/`) once, re-render only affected shots. Spec problems
go back to their owner via `/film-revise`. Then stop: G6 is decided by the human.
