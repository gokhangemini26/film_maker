---
description: "World, production design and characters, then submit gate G3."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **WORLD_CHARACTERS**
- agents, in order: `world-designer` → `character-designer` → `qa-supervisor` (G3 review)
- gate: **G3**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)
- tell the character-designer about any wardrobe/prop constraints the world-designer reported

Then stop at the gate and give the user the exact commands to decide it.
