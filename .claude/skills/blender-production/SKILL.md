---
name: blender-production
description: "How FILM_MAKER turns resolved shot specs into Blender scenes and previews - resolver output, builders, pinned Blender vs draft bpy, per-shot processes, what to check in a still. Used by the blender-td (previews in M3; frames, playblast and chunked final render in M6)."
user-invocable: false
---

# Blender production

## Purpose
Turn approved, resolved specs into Blender scenes and preview stills, and report honestly what the stills show.
Blender is the engine, not the database: builders read only `09_resolved/*.json`, never YAML or project state.

## When to use
ASSET_PREP, BLENDER_BUILD and PREVIEW (M3): after G5, to build and review previews for G6.
ANIMATION and ANIMATION_PREVIEW (M6): frames, playblast and motion QA (`/film-animate`, `/film-playblast`).
FINAL_RENDER (M6): chunked final render, only after the human authorized it (`/film-final`).

## Required inputs
`fm status` past G5; `09_resolved/film.json` and shot files (`fm resolve`); the pinned Blender (`fm doctor`).

## Process
1. `fm resolve`, then `fm blender preview` (pinned Blender). `--draft` (bpy module) only for fast iteration, never G6 evidence.
2. One Blender process per shot (a long EEVEE process can corrupt colours on Windows ARM); absolute paths on Windows.
3. Frames: street (+X north, +Y west, Z up); shop offset x=100, room offset x=200.
4. Toon = Diffuse -> ShaderToRGB -> ColorRamp; outline = inverted-hull Solidify; view transform Standard so hex colours are exact.
5. Open every still and the contact sheet (Read tool).

### M6: animated shots (these commands land incrementally: frames and playblast in step C4, final in step F3)
6. Builders read only the resolved `motion` block (tracks, events, `ui_timeline`), never prose. A shot that needs
   animation and has `motion: null` is a hard failure: report the shot and the animation-director; do not patch a builder.
7. **Frames**: `fm blender frames --frames 0,30,59` (or `--every-key`) renders chosen frames to
   `10_blender/frames/<shot>/f####.png` plus a per-shot contact strip with frame numbers stamped. Read the strips,
   not one mid-shot still, to judge the motion beats.
8. **Playblast**: `fm blender playblast [--scope ...]` renders every frame at low resolution, then ffmpeg builds a
   per-shot mp4 and `10_blender/playblast/film.mp4` (silent). It is a review preview, never final evidence.
9. **Chunked render with resume**: one Blender process handles at most about 48 frames and skips frames already on
   disk, so an interrupted run resumes instead of restarting. Re-run the same command to resume; never delete
   partial frames by hand to "restart".
10. **Final render** (`fm blender final [--scope] [--resume]`): pinned Blender only, chunked, one shot per job. It
    refuses without the human's final-render authorization in the ledger. You never run `fm authorize`; if it is
    missing, stop and tell the user. Verify the frame count on disk against the frame table before reporting done.
11. Motion QA: `fm qa motion` tier 0 (spec level, no Blender), then tier 1 (bake report: foot slide, limb drift, attach
    fidelity, reach, keyframe coverage, idempotence). Technical results only, never evidence of creative correctness.

### Opt-in cinematic pipeline (Cycles, HDRI + fog, grade)
12. Only when the film asks (a shot `atmosphere:`/`grade:` block, canon `look.atmosphere*`/`look.grade*`, or a project `config/render.yaml`
    selecting a Cycles profile): `fm blender preview|frames|playblast --profile cinematic_preview`, final with `--profile cinematic_final`.
    Without `--profile` nothing changes; never add these to a film whose canon locks `blender_eevee_toon` (last_signal).
13. After a Cycles run read `10_blender/logs/*.log` for `FM_RENDER_ENGINE`, `FM_DENOISER requested=.. used=..`, `FM_HDRI`, `FM_FOG`,
    `FM_GRADE`: report the denoiser actually used and any `skipped` line. An HDRI error (missing asset.yaml / UNKNOWN licence / file) is a
    spec/library problem for the human (see `library/hdri/README.md`), never something to work around: do not download or fabricate an HDRI.
14. Seconds per frame are UNKNOWN until you measure one frame at target width; say so instead of estimating. See `docs/CINEMATIC_PIPELINE.md`.

## Output format
Per-shot list: shot id, OK / builder problem / spec problem, evidence, owner. Builder problems are fixed in `blender/`;
spec problems go to the owning specialist.

## Validation rules
Subject in frame; camera not inside geometry; colour matches `color.dominant`; lighting matches the shot; screen direction;
props and UI the spec promises are present. A still is never claimed without opening it.
M6: the frame count on disk equals the frame table; every animated object is keyed on every frame of its span; building
the same shot twice gives the same keyframe hash; a playblast or strip you cite was opened, not assumed.

## Failure conditions
Blender series mismatch (refused); a shot that fails to render (report command, log path in `10_blender/logs/`);
a spec problem patched inside a builder (not allowed).
M6: an unknown `fm blender frames|playblast|final` subcommand (not landed yet): report which M6 step provides it; a
final render requested without authorization (refuse and tell the user); a partial chunk on disk (resume, do not overwrite).

## Examples
"SC04_SH020: builder problem - phone fills the frame (camera 0.3 m from phone at 85 mm); fixed by a minimum insert distance."
"SC01_SH150: spec problem - look_at target frames the roof; owner: cinematographer."
