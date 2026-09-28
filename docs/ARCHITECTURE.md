# Architecture

## 1. Principles

These are design constraints, not aspirations. Each names where it is enforced.

| # | Principle | Enforced by |
|---|---|---|
| A | **Creative quality is first-class.** Technical validity is never proof of creative correctness. | Validation only certifies structure and traceability; creative approval exists only as a human gate decision. Review agents (M2+) produce advisory findings that cannot pass a gate. |
| B | **Intent is separate from implementation.** "The protagonist should feel isolated" is stored on its own (`canon/intent.yaml`); lens, palette, negative space point to it via `serves:`. | Schema: `serves` must reference `intent.*`; shots carry `creative_intent` separately from camera/lighting blocks. Revising an implementation never touches the intent. |
| C | **Decisions carry their rationale.** | `rationale` required on approved DECISIONs in story/world/characters/look/camera/animation/audio; `rationale.camera` required for shots with a lens at G5. Gates refuse without them. |
| D | **The project is a dependency graph.** Intent → canon → artifacts → shots → resolved specs → Blender → render → QA. | `fm.deps`: content hashes on every node, upstream hashes recorded at production time, staleness and impact computed, never guessed. |
| E | **Shots reserve creative intent + rationale.** | `ShotSpec.creative_intent` (narrative / emotional / visual purpose, audience effect) and `ShotSpec.rationale` (camera, lighting, composition, movement, colour, blocking, animation). |
| F | **Human approval is authoritative.** | Human-only commands refuse non-human actors and non-interactive callers; status claims in files must be backed by the ledger; Claude Code deny-rules block the commands outright. Final renders need a recorded authorization. |
| G | **Model-independent.** | All data is Markdown/YAML/JSON with exported JSON Schemas. Models only appear in `config/models.yaml` and the runner layer. `fm.interfaces` reserves protocols for other LLMs, vision models, generators, character systems, mocap and render farms. |
| H | **Blender is the engine, not the database.** | Authoritative data lives in text; Blender receives resolved specs (M3) and `.blend` files are gitignored build products recorded as `blend:` nodes. |
| I | **Partial production.** One asset, character, scene, shot, range, sequence or the whole film. | `fm.scopes` + `fm plan --scope`: scope → roots → downstream closure ∩ stale. |
| J | **Reliability first.** | Deterministic core, 63 tests, stable exit codes, append-only ledger. |
| + | **Proposal ≠ locked decision.** | Lifecycle `PROPOSED → APPROVED → LOCKED (→ SUPERSEDED)` on every canon entry, artifact and shot, from the first file. |

## 2. Two layers

```
 ┌──────────────── Agents (M2) ─────────────────┐   judgement, creativity
 │ creative-director, story-architect, ...      │   write PROPOSED files
 └───────────────┬──────────────────────────────┘
                 │ files + `fm validate / stamp / submit / change propose`
 ┌───────────────▼──────────────────────────────┐   deterministic, tested
 │ fm core: schemas · canon · ledger · state    │   same input → same output
 │          deps/impact · scopes · validation   │
 └───────────────┬──────────────────────────────┘
                 │ resolved specs (M3)
 ┌───────────────▼──────────────────────────────┐
 │ Blender 5.2.x headless (pinned, verified)    │   production engine
 └──────────────────────────────────────────────┘
        ▲
        │ approve / revise / reject / lock / change approve / authorize
      Human (interactive terminal only)
```

Agents never change project state themselves. They write files and call
`fm`; `fm` validates and records. Only a person decides.

## 3. Source of truth

| Kind | Where | Role |
|---|---|---|
| Canon | `canon/<domain>.yaml` | Checkable decisions, each with lifecycle, tag, rationale, `serves`, version history |
| Prose bibles | `*_BIBLE.md` etc. with an `fm:` block | Reasoning and nuance; traced via `derived_from` |
| Shots | `08_shots/*.shot.yaml` | Machine-readable shot specs |
| Ledger | `.fm/ledger.jsonl` | Every human decision and state change; hash-chained |
| State | `state.yaml` | A cache, rebuilt by replaying the ledger; tampering is detected |
| Derived records | `.fm/derived/<kind>/*.json` | Resolved specs, `.blend`, renders, QA reports with their inputs' hashes |

When files disagree with the ledger, the ledger wins and `fm validate` says so.

**Honest limit:** the ledger makes silent changes *detectable*, not impossible.
A process with full disk access could rewrite everything. The protections
are aimed at accidents and at agents drifting, which is the real risk.

## 4. Agents (M2) — 11 subagents + orchestrator

| Subagent | Owns | Covers roles |
|---|---|---|
| main session (Executive Producer) | routing, state, gates | 7.1 |
| creative-director | CREATIVE_DIRECTION, intent/tone canon | 7.2 |
| story-architect | STORY_BIBLE, STORY_STRUCTURE | 7.3 |
| screenwriter | SCREENPLAY | 7.4 |
| world-designer | WORLD_BIBLE, ART_DIRECTION_BIBLE | 7.5, 7.7 |
| character-designer | CHARACTER_BIBLE, character canon incl. `representation` | 7.6 |
| look-director | VISUAL/COLOR/LIGHTING bibles, look canon | 7.8, 7.9, 7.12 |
| cinematographer | CINEMATOGRAPHY_BIBLE, STORYBOARD, SHOT_LIST, shot specs | 7.10, 7.11 |
| animation-director | ANIMATION_BIBLE, shot animation blocks | 7.13 |
| blender-td | resolver, builders, render config | 7.14–7.17 |
| qa-supervisor | technical/visual/continuity QA | 7.18, 7.19 |
| post-supervisor | EDIT_PLAN, AUDIO_BIBLE, animatic | 7.20 |

## 5. Blender strategy (M3)

- **Primary:** headless `blender -b --factory-startup --python ... -- args`
  subprocess. Deterministic, loggable, verified on the target laptop.
- **Secondary:** the Higgsfield live bridge for interactive look-dev only;
  never on the build path.
- **Version pin:** `config/blender.yaml` → `required_series: "5.2"`.
  `fm.blender.require_blender()` runs before every build/render and refuses
  any other series. `fm doctor` shows the result.
- **Idempotency:** every generated datablock tagged `fm_id` / `fm_owner`;
  builders reconcile (create / update / remove-owned-orphans).
- **Characters:** behind `CharacterProvider`. MVP provider = stylised proxy;
  character canon carries a `representation` entry so MPFB, VRM, generated
  or mocap-driven characters plug in without changing shots or canon.

## 6. Extension points (`core/fm/interfaces.py`)

`CharacterProvider`, `MotionSource`, `RenderBackend`, `VisionReviewer`,
`ModelRunner`. Each consumes validated files and returns files plus a
`DerivedRecord`, so the dependency graph tracks their output like anything
else. None are implemented in M1.

## 7. Known limits (M1)

- Canon→canon links (`depends_on`, `serves`) are structural: they appear in
  impact reports but do not make canon entries "stale" (canon entries don't
  record upstream hashes). Change requests list those dependents for review.
- Artifacts are discovered by their `fm:` block; unmanaged files are ignored.
- Production-phase contracts (ASSET_PREP → DELIVERY) are empty until their
  tooling lands; those gates currently approve with no covered artifacts.
