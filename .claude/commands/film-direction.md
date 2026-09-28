---
description: "Creative direction: intents, tone, reference principles and originality statement, then submit gate G1."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **CREATIVE_DIRECTION**
- agents, in order: `creative-director` → `qa-supervisor` (G1 review)
- gate: **G1**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes from the user to pass verbatim to the agents)

Then stop at the gate and give the user the exact commands to decide it.
