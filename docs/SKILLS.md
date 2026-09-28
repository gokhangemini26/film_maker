# Skills

Skills live in `.claude/skills/<name>/SKILL.md`. All are `user-invocable:
false`: they are knowledge for agents, not entries in the `/` menu (only the
`/film-*` commands appear there). Every skill has the same sections: Purpose,
When to use, Required inputs, Process, Output format, Validation rules,
Failure conditions, Examples.

## Shared

**film-conventions** — preloaded into every agent. Holds the rules once:

| File | Covers |
|---|---|
| `SKILL.md` | the per-task process, what agents may never do, the Handoff format |
| `ARTIFACT_CONVENTIONS.md` | file locations and owners, the `fm:` block, stamping, staleness |
| `CANON_PROTOCOL.md` | reading canon, writing entries, change requests, conflicts |
| `INTENT_AND_RATIONALE.md` | intent vs implementation; what a rationale must contain |
| `ORIGINALITY.md` | learning from references without copying; asset licences |
| `REVIEW_RUBRIC.md` | the coherence dimensions every review uses |
| `templates/` | `BRIEF_ANALYSIS.md`, `SCENES.yaml`, `shot.shot.yaml`, `GATE_REVIEW.md` (tested against the schemas) |

**project-management** — the Executive Producer's procedures: A. phase
procedure, B. after a human decision, C. revision procedure.

## Domain skills (M2)

| Skill | Used by | Produces |
|---|---|---|
| film-development | creative-director | brief analysis, intents, tone, creative direction, originality statement |
| story-development | story-architect | premise, theme, beat table with time budget, arcs, ending |
| screenwriting | screenwriter | Fountain screenplay, SCENES.yaml |
| world-building | world-designer | world bible, world canon |
| production-design | world-designer | art direction bible: sets, props, materials, hierarchy |
| character-design | character-designer | character bible, silhouette/proportions/wardrobe/representation canon |
| visual-development | look-director | visual bible, style-lock rules, motifs |
| color-design | look-director | colour bible, palette and per-scene hex canon |
| lighting-design | look-director | lighting bible, motivated lighting canon |
| cinematography | cinematographer | camera language, lens set, continuity canon |
| storyboarding | cinematographer | storyboard, shot list, shot specs |
| animation-design | animation-director | shot animation blocks |
| continuity-check | qa-supervisor | continuity findings |
| creative-review | qa-supervisor | gate reviews |

Deferred: blender-scene-building, blender-python, blender-materials,
blender-lighting, blender-camera, blender-animation, render-management (M3);
visual-qa (M4); post-production (M6).
