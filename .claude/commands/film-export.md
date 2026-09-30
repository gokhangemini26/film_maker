---
description: "Assemble the master (grain, fades, audio), make delivery encodes and run the delivery checks. Ends with a delivery report; nothing is approved."
argument-hint: "[project-slug]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm post:*), Bash(fm qa delivery:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill. Run `fm status`; the project must be in **POST** (G8 approved; otherwise say what is missing and stop).
Dispatch `post-supervisor` with `$ARGUMENTS` (first word = project slug if it names a project) to:

1. `fm post assemble`: frames, grain, optional vignette, fades and audio mux into the master (lands in M6 step F4)
2. `fm post export`: delivery encodes, review proxy and checksum manifest (lands in M6 step F4)
3. `fm qa delivery`: resolution, exactly 24/1 fps, frame count, duration, audio spec, loudness and true peak, black frames, checksums (lands in M6 step F4)

Only the finish steps recorded in `12_post/POST_PLAN.md` from canon are applied. If a subcommand is unknown to `fm`, say which M6 step provides it;
never state that a master or delivery file exists or passed unless the command ran and its report was read.

Then stop and report the delivery report with paths, checks passed and failed, and any blocking licence. Any delivery approval is the human's.
