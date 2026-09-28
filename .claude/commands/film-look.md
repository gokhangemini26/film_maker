---
description: "Visual, colour and lighting bibles and look canon, then submit gate G4 (the style lock)."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **LOOK**
- agents, in order: `look-director` → `qa-supervisor` (G4 review)
- gate: **G4**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)
- if the look-director reports wardrobe/palette collisions, bring them to the user before submitting

Then stop at the gate and give the user the exact commands to decide it.
