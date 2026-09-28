---
description: "Run the qa-supervisor's review of the current phase against intent, canon and craft (writes the gate review; does not submit)."
argument-hint: "[project-slug]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill. Run `fm status` for `$ARGUMENTS`. Find the gate the
current phase leads to (G1 for BRIEF/CREATIVE_DIRECTION, G2 for STORY/SCREENPLAY, G3,
G4, G5 for CINEMATOGRAPHY/STORYBOARD). Dispatch `qa-supervisor` to write that gate's
review. Report the verdict and the top findings with their owners. Do not submit,
advance or fix anything.
