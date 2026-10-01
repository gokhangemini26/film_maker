# Canon protocol

Canon (`canon/<domain>.yaml`) holds the decisions downstream work depends on.
Prose explains; canon commits.

## Reading canon
1. `fm canon list` shows every entry with its **ledger** status (the file's
   `status` field may lag; the list is authoritative).
2. Read `intent` and `tone` before anything else: they say what the film is for.
3. LOCKED = agreed and frozen. APPROVED = agreed. PROPOSED = still open.
   REJECTED/SUPERSEDED = do not use (history only).

## What belongs in canon
Anything a later agent or the Blender build must obey and that can be stated
checkably: a premise, a world rule, a character's height or jacket, a palette
hex, a lens set, the time and weather of a scene. Not: mood prose, reasoning,
alternatives (those go in the bible, and the reasoning also in `rationale`).

## Writing an entry

```yaml
- id: characters.mara.wardrobe.jacket   # <domain>.<subject>.<aspect>..., lowercase
  statement: Dark waxed jacket, worn at the cuffs.
  value: {color: "#1A1A1C", material: waxed cotton, fit: slightly large}
  rationale: >
    The dark silhouette reads against wet, reflective streets; the worn cuffs
    say she has done this job for years. Rejected: a courier uniform (too
    institutional for someone this alone).
  serves: [intent.isolation]
  applies_to: []            # empty = whole film; or [SC01, SC01_SH020, mara, SQ02]
  depends_on: []            # other canon ids this assumes
  tag: DECISION
  status: PROPOSED
  source: agent:character-designer
```

- `id` domain prefix must match the file (`characters.yaml` → `characters.*`).
- Machine values go in `value`. Colours are `#RRGGBB` (validated).
- Scene-specific canon uses `applies_to` rather than a new id per scene when
  the same aspect varies by scene (e.g. `look.color.scene_key` per scene id)
  — or a scoped id like `continuity.sc03.weather` with `applies_to: [SC03]`.

## Changing canon
- PROPOSED entries (yours or others' in your domain): edit directly.
- APPROVED / LOCKED entries: never edit. Propose:

```
fm impact canon:characters.mara.wardrobe.jacket
fm change propose characters.mara.wardrobe.jacket \
  --set "statement=Dark brown waxed jacket." \
  --set "value={color: '#3B2A1E', material: waxed cotton}" \
  --set "rationale=Brown separates her from the blue night while staying muted." \
  --reason "Director note: black loses her against the night palette."
```

When the value changes, update the rationale too so it explains the new
choice against the same intent. Keep `serves` unless the intent itself changed.
The human decides the change; after approval `fm plan` shows what to regenerate.

## Conflicts
If two locked decisions contradict each other, or your task cannot be done
without breaking one, stop. Report the conflict with both ids and a proposed
resolution. The creative-director may propose the resolution; the human decides.
