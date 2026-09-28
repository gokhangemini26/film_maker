# Workflow

## Phases and gates

```
IDEA → BRIEF → CREATIVE_DIRECTION ─G1→ STORY → SCREENPLAY ─G2→
WORLD_CHARACTERS ─G3→ LOOK ─G4 (style lock)→ CINEMATOGRAPHY → STORYBOARD ─G5→
ASSET_PREP → BLENDER_BUILD → PREVIEW ─G6→ ANIMATION → ANIMATION_PREVIEW ─G7→
[authorize final-render] → FINAL_RENDER ─G8→ POST → DELIVERY → COMPLETE
```

| Gate | Approves artifacts of | Locks canon domains |
|---|---|---|
| G1 Creative direction | BRIEF, CREATIVE_DIRECTION | intent, tone |
| G2 Story & screenplay | STORY, SCREENPLAY | story |
| G3 World & characters | WORLD_CHARACTERS | world, characters |
| G4 Visual direction | LOOK | look (the **style lock**) |
| G5 Storyboard & shots | CINEMATOGRAPHY, STORYBOARD + all shots | camera, continuity |
| G6 First preview | ASSET_PREP, BLENDER_BUILD, PREVIEW | — |
| G7 Animation preview | ANIMATION, ANIMATION_PREVIEW | animation, audio |
| G8 Final render | FINAL_RENDER | — |

Deliverables each phase must have before `fm submit` are in
`core/fm/phases.py` (`CONTRACTS`).

## The loop inside a gated phase

```
agent writes PROPOSED files ─→ fm stamp ─→ fm validate ─→ fm submit
                                                           │
                    human: fm approve G# ◄─────────────────┤
                    human: fm revise G# --notes "..." ─→ agent revises ─→ fm submit
                    human: fm reject G# --notes "..." ─→ rethink
fm advance  (only after approval, and only while every earlier gate is healthy)
```

Approving a gate:
1. requires the phase to be submitted and `fm validate` to have no errors,
2. requires every earlier gate to be approved and not drifted,
3. requires rationale on decisions it locks and creative intent + camera
   rationale on shots (G5),
4. records the content hash of every artifact/shot it covers,
5. locks the canon in its domains,
6. needs a person at a terminal typing the gate id.

## Proposal vs locked decision

```
Agent proposes (PROPOSED) → Human reviews → APPROVED → LOCKED → downstream may depend on it
                                         ↘ REJECTED
LOCKED → change request → human approves → new version LOCKED, old version SUPERSEDED
```

- Agents may only write `PROPOSED`. A file claiming `APPROVED`/`LOCKED`
  without a ledger record fails validation (`STATUS_NOT_BACKED`).
- Editing a LOCKED entry in place fails validation
  (`LOCKED_CANON_MODIFIED`) and blocks submit/advance.
- PROPOSED entries can be edited freely.

## Changing an approved decision

```
fm impact canon:characters.mara.wardrobe.jacket            # preview the blast radius
fm change propose characters.mara.wardrobe.jacket \
   --set "statement=Dark brown waxed jacket." \
   --set "value={color: '#3B2A1E'}" --reason "..."          # agent or human
fm change approve CHANGE-001                                # human, terminal
fm plan --scope character:mara                              # what to regenerate
```

After approval the entry is v2 (v1 kept in `history` as SUPERSEDED),
`CHANGELOG.md` is regenerated, and every downstream node is **stale**.
Gates whose approved content is now stale show as **DRIFTED** and block
`fm advance` until the stale items are regenerated, stamped, and the gate
re-approved (`fm approve G3` works again on a drifted gate).

## Partial production

`fm plan --scope <scope>` lists only what is stale inside the scope:

| Scope | Selects |
|---|---|
| `film` | everything |
| `shot:SC01_SH010` | one shot and its downstream products |
| `shots:SC01_SH010..SC02_SH030` | a range (ordered by scene, shot) |
| `scene:SC01`, `sequence:SQ01` | by scene or sequence |
| `character:mara` | the character's canon + every shot featuring them |
| `asset:<id>` | shots listing the asset + matching canon |
| `ref:<node>` | any single node |

## Staleness and stamping

Every artifact/shot lists `derived_from`. `fm stamp <file>` records the
current hash of each upstream (and, for shots, of implicit dependencies:
served intents, characters' canon, continuity, scoped canon). If an
upstream later changes, the node and everything below it is stale.

`fm stamp` refuses to refresh changed upstream hashes on a node whose own
content hasn't changed, unless `--note` explains why no revision is needed —
so staleness cannot be silenced by re-stamping.

## Final render

`fm advance` into FINAL_RENDER requires `fm authorize final-render`
(human). From M3 every render backend also checks the authorization and
the Blender pin.
