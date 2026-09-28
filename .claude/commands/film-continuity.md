---
description: "Continuity check - deterministic fm check continuity plus the qa-supervisor's judgement on wardrobe, props, geography, screen direction, time and weather."
argument-hint: "[project-slug] [scope, e.g. scene:SC02]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill
---

Run `fm check continuity` for `$ARGUMENTS` and show its output. Then dispatch
`qa-supervisor` with the continuity-check skill to review continuity (limited to the scope
if one was given) and **return findings in its handoff only** — no files are written.
Report FAIL/WARN findings with shot ids, evidence and the owner who should fix each.
Do not change anything.
