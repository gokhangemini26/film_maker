---
description: "Run whichever /film-* step comes next for the project."
argument-hint: "[project-slug] [notes]"
allowed-tools: Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill, Bash(fm init:*), AskUserQuestion
---

Run `fm status` for `$ARGUMENTS`.
- If a gate is awaiting approval, a change request awaits a decision, or a gate has
  drifted: do nothing; tell the user exactly what they need to decide and the command.
- If the current phase's gate is approved: `fm advance` first.
- Then run the command for the phase: BRIEF → `/film-new` step 2 onward;
  CREATIVE_DIRECTION → `/film-direction`; STORY → `/film-story`; SCREENPLAY → `/film-script`;
  WORLD_CHARACTERS → `/film-world`; LOOK → `/film-look`; CINEMATOGRAPHY → `/film-cinematography`;
  STORYBOARD → `/film-storyboard`; anything later → say it arrives in M3+.
Follow that command's instructions exactly, passing any notes through.
