---
description: "Apply feedback or a change - impact analysis first, then revise unapproved work or propose change requests for locked canon, then regenerate only what is stale."
argument-hint: "[project-slug] \"<your feedback>\""
allowed-tools: Bash(fm change propose:*), Bash(fm change list:*), Bash(fm change show:*), Bash(fm status:*), Bash(fm validate:*), Bash(fm stamp:*), Bash(fm submit:*), Bash(fm advance:*), Bash(fm intent:*), Bash(fm check:*), Bash(fm canon list:*), Bash(fm canon show:*), Bash(fm log:*), Bash(fm plan:*), Bash(fm impact:*), Bash(fm deps:*), Read, Glob, Grep, Agent, Skill, AskUserQuestion
---

Load the `project-management` skill and run its **C. Revision procedure** with the
feedback in `$ARGUMENTS` (verbatim).

Always show the user `fm impact` before changing anything. For locked canon, stop after
the change request and give the user `fm change approve CHANGE-NNN` to run in their own
terminal. After approval, regenerate only what `fm plan --scope ...` lists, re-review the
affected gates, and tell the user which gates need `fm approve` again.
