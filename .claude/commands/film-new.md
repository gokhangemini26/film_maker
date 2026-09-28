---
description: "Start a new film - create the project, analyse the brief, ask only the questions that matter, record intents, and move to creative direction."
argument-hint: "<project-slug> <your idea, taste, references...>"
allowed-tools: Bash(fm init:*), Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill, AskUserQuestion
---

Load the `project-management` skill, then:

1. Take the first word of `$ARGUMENTS` as the project slug (lowercase, underscores) and the
   rest as the user's brief. If there is no brief text, ask the user for their idea first.
   Ask for a working title if none is obvious. Run `fm init <slug> --title "<title>"`
   (never `--sandbox`), then `fm advance` (to BRIEF).
2. Dispatch `creative-director` for **brief analysis**: pass the user's words verbatim and
   ask for BRIEF_ANALYSIS.md, brief.yaml statuses, and `canon/intent.yaml`.
3. Ask the user the creative-director's questions (max 5, with their defaults) using
   AskUserQuestion. Unanswered questions take the default and stay ASSUMPTION.
4. Dispatch `creative-director` again with the answers verbatim to update the brief,
   analysis and intents.
5. `fm stamp` / `fm validate -q` (section A step 4), then `fm advance` (to CREATIVE_DIRECTION).
6. Report: the intents as recorded (the user should check they are their words),
   assumptions, and next step `/film-direction`.
