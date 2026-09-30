---
description: "Edit plan, post plan, EDL and animatic with sound, then the G7 review and submit. Ends at gate G7 (animation, audio and post plan)."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm post:*), Bash(fm qa motion:*), Bash(fm qa audio:*), Bash(fm qa review-status:*), Bash(fm check anim:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **ANIMATION_PREVIEW**
- agents, in order: `post-supervisor` (`12_post/EDIT_PLAN.md`, `POST_PLAN.md`, EDL, animatic) → `qa-supervisor` (G7 review: motion coherence, sync, silence, sound vs canon)
- gate: **G7**
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes passed verbatim)
- preconditions, checked before dispatching: an anim file for every shot; `10_blender/playblast/film.mp4`; `12_post/audio/mix_48k_stereo.wav`;
  otherwise stop and name the command to run (`/film-animate`, `/film-playblast`, `/film-audio`)
- deterministic checks: `fm validate -q`, `fm intent`, `fm qa motion` (M6 step D1), `fm qa audio` (M6 step E5), `fm post edl` and `fm post animatic` (M6 step F2)

If a subcommand is unknown to `fm`, say which M6 step provides it; `fm submit` refuses if the phase contract is unmet, so report that and do not work around it.
Approving G7 does not authorize the final render: that is a separate human step.

Then stop at the gate. Report the animatic path, contact strips for flagged shots, the review verdict, the open human decisions
(score, titles vs wordless, loudness, doc conflicts, vignette, render profile, fade length, vocabulary ratification, delivery gate, foley source),
the unresolved licence list, and the exact commands to decide it: `fm approve G7` or `fm revise G7 --notes "..."`.
