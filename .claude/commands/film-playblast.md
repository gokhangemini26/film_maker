---
description: "Render frames and a low-resolution playblast of the animated shots, run motion QA and build contact strips. Report only; nothing is submitted."
argument-hint: "[project-slug] [shot ids or scope]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm resolve:*), Bash(fm qa motion:*), Bash(fm check anim:*), Bash(fm blender frames:*), Bash(fm blender playblast:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill. Run `fm status`; the project must be in **ANIMATION_PREVIEW** (run `/film-animate` first if
anim files are missing). Dispatch the `blender-td` agent with `$ARGUMENTS` (first word = project slug if it names a project;
the rest = shot ids or scope) to:

1. `fm resolve`, then `fm blender frames --every-key` for contact strips (lands in M6 step C4)
2. `fm blender playblast`: chunked, resumable, silent `10_blender/playblast/film.mp4` (lands in M6 step C4)
3. `fm qa motion` tier 0 (lands in M6 step D1) and tier 1, the bake report: foot slide, limb drift, attach fidelity (lands in M6 step D2)
4. open every strip the report cites (Read tool) and report per shot: OK / builder problem (blender-td) / spec problem (animation-director)

Rerun only affected shots. If a subcommand is unknown to `fm`, say which M6 step provides it; do not fabricate output.
Then stop: no gate here. Tell the user the outputs, with `/film-audio` and `/film-post` as next steps.
