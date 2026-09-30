---
description: "Audio canon, audio bible and per-shot cue sheet tied to animation events, synth and mix, sync checks, and the list of sounds the human must supply. Report only."
argument-hint: "[project-slug] [notes for the agents]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Bash(fm audio:*), Bash(fm qa audio:*), Bash(fm check anim:*), Read, Glob, Grep, Agent, Skill
---

Load the `project-management` skill and run its **A. Phase procedure** with:

- phase: **ANIMATION_PREVIEW** (anim files with events must exist; otherwise send the user to `/film-animate`)
- agents, in order: `sound-designer` (`audio.*` canon proposals, `12_post/AUDIO_BIBLE.md`, `12_post/AUDIO_CUES.yaml`, synthesis recipes, asks list)
- gate: none here (G7 is reached through `/film-post`)
- project and notes: `$ARGUMENTS` (first word = project slug if it names a project; the rest are notes passed verbatim)
- deterministic checks: `fm validate -q`, `fm audio synth` (lands in M6 step E2), `fm audio mix` and `fm qa audio` (land in M6 step E5)

The wordless film has no speech and no generated music: never send this work to a speech or music generator. Breaths, body
foley, library sounds and Hana's headphone track are the human's to record or supply, with licences.
If a subcommand above is unknown to `fm`, say which M6 step provides it; never report a check or a mix as done that did not run.

Then stop and report: files written, the asks list for the human (with licence status), the cue-sheet conflict list (storyboard vs
shot files), decisions D1, D3, D4 and D10 that need a ruling, and `/film-post` as next. The human listens; you do not judge how it sounds.
