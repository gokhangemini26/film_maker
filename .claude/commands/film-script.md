---
description: "Screenplay and SCENES.yaml scene index, then submit gate G2 (story + screenplay)."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **SCREENPLAY**
- agents, in order: `screenwriter` → `qa-supervisor` (G2 review)
- gate: **G2**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)

Then stop at the gate and give the user the exact commands to decide it.
