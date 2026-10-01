# Review rubric

Used by the qa-supervisor for gate reviews, and by every agent as a self-check
before handing work back. Technical validity (`fm validate` clean) is necessary
and says nothing about whether the work is good.

For each dimension give a verdict (PASS / WARN / FAIL) and **evidence**: a
file and section, a canon id, a shot id, or a quoted phrase of at most a few words.

| Dimension | Question | Typical FAIL |
|---|---|---|
| Intent fidelity | Does every major choice serve a locked intent? Is every intent served? | A decision that works against an intent; an intent nothing serves (`fm intent`) |
| Narrative coherence | Do cause and effect, stakes and the ending follow from the premise? | An ending the story didn't earn; a beat that contradicts an earlier one |
| Emotional coherence | Does the emotional arc move in the intended direction at the intended pace? | Tone swings the creative direction didn't ask for |
| Character consistency | Do appearance, behaviour and wardrobe match the character canon everywhere? | Jacket colour, height or manner differs between documents |
| World consistency | Do locations, era, weather and rules match world canon? | Technology or architecture from outside the world's rules |
| Visual coherence | Do palette, lighting and composition follow the style lock (after G4)? | A shot lit against the lighting bible with no `style_break` reason |
| Cinematographic coherence | Are lens, height, movement and framing motivated and consistent with the camera language? | Random lens changes; a 180° line crossed without reason |
| Rationale quality | Does each rationale name a mechanism and a rejected alternative? | "Because it looks cinematic" |
| Originality | Are references used as principles, not copied? | A recognisable shot or design lifted from a reference |
| Feasibility | Can this be produced with proxy characters in Blender 5.2 on a laptop (for M3+)? | Crowds, water simulation or hair close-ups the MVP cannot build |
| Pacing / budget | Do durations fit the brief's running time? | Shot total far from the brief duration |

## Verdict
- **FAIL** if any dimension FAILs: something contradicts canon/intent or cannot be made.
- **WARN** if nothing fails but something needs the human's attention.
- **PASS** otherwise.

The verdict is advice. The human decides at the gate.
