---
name: sound-design
description: "Design the film's sound as checkable canon plus a per-shot cue sheet - palette, motifs, silence map, perspective, mix targets, sources and licences - with cues tied to animation events by id, and an explicit list of what the human must supply or record. Used by the sound-designer in ANIMATION_PREVIEW (M6)."
user-invocable: false
---

# Sound design

## Purpose
Make sound serve the intents: what is heard, what is withheld and where the
film goes silent. Sync is structural: cues point at named animation events, so
retiming a shot moves its sound with it. Honest about capability: procedural
synthesis is possible, credible breaths, foley and music are not.

## When to use
ANIMATION_PREVIEW (M6), after the shots' anim files and events exist:
`/film-audio`. Again after any revision that changes events, the silence map or the mix targets.

## Required inputs
- Locked canon: intent and tone (`tone.wordless`), animation vocabulary, `continuity`.
- STORYBOARD `Sound:` lines, each shot's `sound_sync` text, and the `events` of every `09_animation/*.anim.yaml`.
- `library/audio/` manifests (what sources exist and their licences).

## Process
1. Read intent and tone first. Decide what sound must do for each intent, and what its absence must do.
2. Propose `audio.*` canon, each with a rationale (choice + mechanism + rejected alternative) and `serves`:
   `principles` (wordless, dynamic range), `score` (recommendation and the rejected alternative; the human decides,
   D1), `palette` (sound families and ids), `motifs`, `silence_map` (frame spans that must be silent or at room-tone
   floor), `ratchet` (phase lock, derived from `handle_top`-style events, never hand-typed), `perspective` (per
   location), `mix` (loudness, peak, sample rate; target is a human decision, D3), `sources`.
3. Write `12_post/AUDIO_BIBLE.md`: the sound world, motifs, perspective and why.
4. Write `12_post/AUDIO_CUES.yaml`, one entry per cue: `id`, `shot`, `at` (exactly one of `{event: <id>}` or
   `{f: n}` shot-local), `sound` (an id in `audio.palette`), `layer` (ui | sfx | foley | amb | body | music),
   `gain_db`, `pan`, `offset_f`, `end`, `fade`, `serves`. Beds are separate `bed` entries with `from_frame`,
   `to_frame`, `xfade_f`. Prefer `event` over `f` whenever an event exists.
5. For every sound id choose `source: synth | library | recorded`. Synth: write the recipe (oscillators, filtered
   noise, envelope, glide) so `fm audio synth` can build it deterministically. Library or recorded: list it on the
   **asks list** with a licence field to fill; never assume a licence.
6. List **conflicts** for the human instead of resolving them (for example storyboard prose that contradicts a
   shot's `sound_sync`). Follow the shot file as the working assumption and tag it ASSUMPTION.
7. Run the deterministic checks that exist: `fm audio synth`, `fm audio mix`, `fm qa audio` (M6 steps E2/E5). If
   `fm` reports an unknown command, record that in the handoff; do not claim a mix or check result.

## Output format
`12_post/AUDIO_BIBLE.md` and `12_post/AUDIO_CUES.yaml` with `fm:` blocks (`derived_from` every anim file whose events
are used, the audio canon ids and the storyboard), plus this section in the handoff:

```
## Asks for the human
| sound id | need | source | licence | status |
| body.breath_in_slow | 3 short takes, phone recording | recorded | own | NEEDED |
| room.headphone_leak | 5 s lowpassed loop | library | UNKNOWN | NEEDED |
## Conflicts for the human
| shots | storyboard says | shot file says | working assumption |
```

## Validation rules
- Every cue has exactly one of `event` / `f`, lies inside its shot (or is a `bed`), and its `sound` exists in the palette.
- Every audible anim event and every `sound_sync` entry has a cue within +-1 frame (`fm qa audio` when it exists).
- No cue in a `speech`-tagged source; no music unless D1 chose it and the human supplied it.
- Silence-map spans have no cue louder than the room-tone floor.
- Unknown licence: WARN before G7, blocks final export.
- Only PROPOSED work; nothing in `canon/audio.yaml` is marked LOCKED by you.

## Failure conditions
- A needed sync point has no animation event: ask the animation-director through the orchestrator; never edit anim files.
- The silence map or ratchet phase cannot be met with the current events: report; do not shift cues by hand.
- Anything that needs a locked canon change: `fm change propose`, never edit the entry.

## Examples
```yaml
- id: cue_SC04_SH040_lid
  shot: SC04_SH040
  at: {event: lid_latch}
  sound: car.glovebox_lid_clack
  layer: sfx
  gain_db: -14
  serves: [intent.effort_is_heard]
```
"SC03_SH050 f8-29 is in `audio.silence_map`; the shop hum cue ends at the blackout event, and there is no bed after it (canon allows silence here)."
