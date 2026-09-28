---
description: "Camera language: lens set, heights, movement, framing, depth, screen direction, rhythm (no gate; G5 covers it)."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **CINEMATOGRAPHY**
- agents, in order: `cinematographer` (CINEMATOGRAPHY_BIBLE.md + camera canon only)
- gate: none — finish with `fm advance`
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)

Then suggest `/film-storyboard`.
