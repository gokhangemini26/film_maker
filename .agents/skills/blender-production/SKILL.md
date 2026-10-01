---
name: blender-production
description: "How FILM_MAKER turns resolved shot specs into Blender scenes and previews - resolver output, builders, pinned Blender vs draft bpy, per-shot processes, what to check in a still. Used by the blender-td."
user-invocable: false
---

# Blender production

## Purpose
Turn approved, resolved specs into Blender scenes and preview stills, and report honestly what the stills show.
Blender is the engine, not the database: builders read only `09_resolved/*.json`, never YAML or project state.

## When to use
ASSET_PREP, BLENDER_BUILD and PREVIEW (M3): after G5, to build and review previews for G6.

## Required inputs
`fm status` past G5; `09_resolved/film.json` and shot files (`fm resolve`); the pinned Blender (`fm doctor`).

## Process
1. `fm resolve`, then `fm blender preview` (pinned Blender). `--draft` (bpy module) only for fast iteration, never G6 evidence.
2. One Blender process per shot (a long EEVEE process can corrupt colours on Windows ARM); absolute paths on Windows.
3. Frames: street (+X north, +Y west, Z up); shop offset x=100, room offset x=200.
4. Toon = Diffuse -> ShaderToRGB -> ColorRamp; outline = inverted-hull Solidify; view transform Standard so hex colours are exact.
5. Open every still and the contact sheet (Read tool).

## Output format
Per-shot list: shot id, OK / builder problem / spec problem, evidence, owner. Builder problems are fixed in `blender/`;
spec problems go to the owning specialist.

## Validation rules
Subject in frame; camera not inside geometry; colour matches `color.dominant`; lighting matches the shot; screen direction;
props and UI the spec promises are present. A still is never claimed without opening it.

## Failure conditions
Blender series mismatch (refused); a shot that fails to render (report command, log path in `10_blender/logs/`);
a spec problem patched inside a builder (not allowed).

## Examples
"SC04_SH020: builder problem - phone fills the frame (camera 0.3 m from phone at 85 mm); fixed by a minimum insert distance."
"SC01_SH150: spec problem - look_at target frames the roof; owner: cinematographer."
