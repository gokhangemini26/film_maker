---
description: "Continuity canon, storyboard, shot list and shot specs, shot animation blocks, continuity check, then submit gate G5."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **STORYBOARD**
- agents, in order: `cinematographer` (continuity canon, SHOT_LIST, shots, STORYBOARD) → `animation-director` (every shot's animation block) → `qa-supervisor` (G5 review incl. continuity)
- gate: **G5**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)
- run `fm check continuity` and `fm intent` before the review; send FAILs back to the cinematographer once

Then stop at the gate and give the user the exact commands to decide it.
