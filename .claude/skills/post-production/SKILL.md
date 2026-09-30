---
name: post-production
description: "Plan and verify the edit and delivery - EDL from the shot table, locked finish steps read from canon (glare, grain, optional vignette), titles ruling, final render settings, animatic with sound, master and delivery encodes, delivery checks. Used by the post-supervisor in ANIMATION_PREVIEW and POST (M6)."
user-invocable: false
---

# Post-production

## Purpose
Turn approved frames and the cue sheet into an edit, an animatic for review and a
delivery master, adding only the finish the look canon locks. The edit is
generated from the shot table; nothing here is a creative grade.

## When to use
- ANIMATION_PREVIEW: `/film-post` (edit plan, post plan, EDL, animatic with sound, for G7).
- POST: `/film-export` (assemble, export, delivery checks), after G8.

## Required inputs
- `09_resolved/film.json` (frame table), SHOT_LIST, `canon/camera.yaml` (`camera.rhythm.transitions`), `look.style.*`
  (grain, glow), `tone.wordless`, `audio.mix`, `config/render_profiles.yaml`.
- `10_blender/playblast/` (animatic picture) and `12_post/audio/mix_48k_stereo.wav` (from the sound-designer's cues).
- For POST: the complete final frame set and the human's `fm authorize final-render` already in the ledger.

## Process
1. Cut list: `fm post edl` (M6 step F2) writes `12_post/EDIT.edl` (CMX3600, 24 fps non-drop), `edit.ffconcat` and the
   readable cut list. Transitions come only from `camera.rhythm.transitions`. Write `12_post/EDIT_PLAN.md`: shot
   order, record in/out from the frame table, head and tail fades, carried-forward hold checks.
2. `12_post/POST_PLAN.md`: one step per locked finish (glare, grain, optional vignette), each with parameters read
   from canon so a canon change restales it; the titles/credits ruling; the final render settings proposal; the
   delivery spec (master, delivery encodes, loudness and peak, checksum manifest).
3. Human decisions are written as recommendations with rejected alternatives and left `UNKNOWN` until ruled:
   titles vs `tone.wordless` (D2), loudness (D3), vignette (D5), final render profile (D6), FADE IN length (D7).
4. `fm post animatic` (M6 step F2): playblast picture plus the mix muxed into `12_post/animatic.mp4`, the G7 review artifact.
5. POST only: `fm post assemble` then `fm post export` (M6 step F4): frames -> grain -> optional vignette -> fades ->
   audio mux -> master and delivery encodes, then `fm qa delivery` (ffprobe: resolution, exactly 24/1 fps, frame
   count, duration, audio spec, loudness and true peak, black frames beyond the fades, checksums).
6. Licences: list every `UNKNOWN` asset or audio licence as blocking final export.

## Output format
`EDIT_PLAN.md` and `POST_PLAN.md` with `fm:` blocks (`derived_from`: the frame table, the canon ids read, AUDIO_CUES),
plus the report: files produced, command results (quoted, not paraphrased), decisions still open, licence table.

## Validation rules
- Runtime of the assembled cut equals the shot table's total frames exactly.
- No transition other than those in `camera.rhythm.transitions`.
- No finish step whose parameters are not read from canon.
- Never claim an animatic, master or delivery report exists or passed unopened and unrun.
- Never run `fm authorize`, `fm blender final` or any human-only command.

## Failure conditions
- The playblast or the mix is missing or stale: report; do not build an animatic from partial inputs.
- `fm post` / `fm qa delivery` unknown (not landed yet): say which M6 step provides it; do not fabricate output.
- A required finish would contradict locked canon (for example on-screen text vs `tone.wordless`): `fm change propose`, stop.

## Examples
"POST_PLAN step `grain`: monochrome, amplitude from `look.style.texture_and_grain`, fixed seed, applied at assembly. Rejected: baking grain in Blender (not re-appliable without a re-render)."
"Open decision D2 (titles): recommendation A, no on-screen text in the master; status UNKNOWN until the human rules."
