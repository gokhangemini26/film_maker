# Cinematic pipeline (opt-in): Cycles, AI denoiser, HDRI + fog, colour grade

An optional render path for films that want a realistic, physically lit image. It is **opt-in per film**: nothing in a film
changes unless that film asks. The demo `projects/last_signal` (locked canon `engine: blender_eevee_toon`, Standard view
transform, painted/toon look, no realism; G4 style lock, G5 approved) does not ask, and is guarded by tests so it cannot start
to (`tests/test_cinematic.py::test_last_signal_validates_and_resolves_exactly_as_before`).

| Piece | Where | Default |
|---|---|---|
| Cycles + denoiser + device + adaptive sampling | `cinematic_preview` / `cinematic_final` in `config/render_profiles.yaml` | off: `preview` and `final` stay EEVEE |
| HDRI environment + volumetric fog | `atmosphere:` block (shot, or canon `look.atmosphere*`) | no block, nothing built |
| Compositor colour grade | `grade:` block (shot, or canon `look.grade*`) | no block, nothing built |
| DaVinci Resolve hand-off | `fm post grade-handoff` | not run |
| Physically shaded materials (instead of Shader-to-RGB cel) | automatic with a Cycles profile | cel (toon) |

## What is opt-in, exactly

- A profile selects the engine. `fm blender preview|frames|playblast` use no profile unless you pass `--profile`; `fm blender final`
  uses `final` unless you pass `--profile`. `preview` and `final` are EEVEE, so every existing command behaves bit for bit as before
  (no environment variable is passed to Blender, no manifest key is added).
- Only a profile with `engine: CYCLES` exports `FM_RENDER_PROFILE` to the Blender process. Blender-side, `preview.setup_render`,
  the atmosphere hook and the grade hook do nothing without it. A shot that carries `atmosphere:`/`grade:` but is rendered with an
  EEVEE profile logs `FM_ATMOSPHERE skipped ...` / `FM_GRADE skipped ...` and renders as before.
- The new shot fields are optional and excluded from the content hash while unset, `fm resolve` adds keys to a resolved shot only
  when a block applies, so a film without them resolves to identical bytes and no node goes stale.

## Enable it for a new film

1. **Pick an HDRI** (human step; the sandbox cannot reach polyhaven.com and FILM_MAKER never downloads): follow
   `library/hdri/README.md`: download a CC0 `.hdr`/`.exr` from <https://polyhaven.com/hdris> into `library/hdri/<id>/` and write `asset.yaml`
   (file, licence, source_url, resolution, tags, sha256).
2. **Say it in the look** (look-director, LOOK phase; the G4 style lock then covers it). Film-wide values go in canon, scoped with
   `applies_to` (scene or shot ids) when they differ. A canon entry needs its own `rationale` (CLAUDE.md rule 4):

   ```yaml
   # projects/<film>/canon/look.yaml
   - id: look.atmosphere
     statement: "Low overcast daylight with a thin ground haze."
     value:
       hdri: {id: kloofendal_48d_partly_cloudy_puresky, rotation_deg: 120, strength: 1.0}
       fog: {density: 0.008, anisotropy: 0.2, height_falloff: 0.35, colour: "#C9D6E8"}
     rationale: "Haze separates the planes and keeps the street desaturated, as the brief's 'quiet, cold morning' asks."
     serves: [intent.isolation]
   - id: look.grade
     statement: "Cool shadows, slightly warm highlights, restrained saturation."
     value:
       exposure_ev: 0.2
       color_balance: {mode: lift_gamma_gain, lift: [0.98, 1.0, 1.04], gamma: [1, 1, 1], gain: [1.04, 1.0, 0.95]}
       saturation: 0.9
       curves: [[0, 0], [0.25, 0.22], [0.75, 0.8], [1, 1]]
     rationale: "The cool/warm split carries the isolation intent without leaving the palette."
   - id: look.grade.sc03_night            # scene-specific: wins over look.grade for SC03 shots
     applies_to: [SC03]
     ...
   ```

   Or per shot (the cinematographer / animation-director), where the block **must** carry a `rationale`:

   ```yaml
   # 08_shots/SC01_SH010.shot.yaml
   atmosphere:
     fog: {density: 0.02, anisotropy: 0.3, bounds: box, box: {center: [0, 4, 1.2], size: [10, 8, 2.4]}}
     rationale: "A local fog bank behind the subject separates her from the shopfronts."
   grade: {saturation: 0.8, rationale: "This shot is the cold low point of the arc."}
   ```

   Precedence per shot: its own block, then the canon entry that names the shot, then the one that names its scene, then the film-wide
   entry. Two entries at the same level are refused (`CINEMATIC_AMBIGUOUS`).
3. **Run** (`fm resolve` expands the blocks into `09_resolved/<SHOT>.json`; `preview` and `final` run it for you, run it before `frames`/`playblast`):

   ```
   fm validate                                            # HDRI_ASSET / CINEMATIC_SCHEMA findings, if any
   fm blender preview  --profile cinematic_preview        # one still per shot (pinned Blender; --draft = cloud bpy, never evidence)
   fm blender frames   --profile cinematic_preview --scope shot:SC01_SH010 --every-key
   fm blender playblast --profile cinematic_preview --scope scene:SC01
   fm blender final    --profile cinematic_final          # needs YOUR `fm authorize final-render`; chunked, resumable
   fm post grade-handoff                                  # optional: hand-off package for DaVinci Resolve
   ```

   To make a film use the cinematic profiles by default, override per project in `projects/<film>/config/render.yaml` (the existing
   mechanism; keys merge over the repository profile, and a project may define a whole profile of its own):

   ```yaml
   profiles:
     cinematic_final: {samples: 128, denoiser: oidn}   # tune this film's cost
   ```

## Render profile keys (engine: CYCLES)

| Key | Values | Meaning |
|---|---|---|
| `samples` | int | Cycles samples (`--samples` overrides). With adaptive sampling it is a ceiling |
| `adaptive_sampling`, `adaptive_threshold`, `adaptive_min_samples` | bool, (0..1], int | stop sampling converged pixels |
| `denoiser` | `oidn` \| `optix` \| `auto` \| `none` | see below |
| `device` | `auto` \| `cpu` \| `optix` \| `cuda` \| `hip` \| `metal` \| `oneapi` | `auto` takes the best GPU backend with a device, else CPU |
| `max_bounces`, `clamp_indirect` | int, float | optional light-path limits (noise vs energy) |
| `color_depth` | 8 \| 16 | PNG bit depth; `cinematic_final` writes 16-bit for grading headroom |
| `chunk_frames`, `requires_authorization`, `resolution_scale`, `output` | as for `final` | `output` must stay `png` (`fm post assemble` reads PNG); EXR output is **not** implemented |

The Cycles settings are part of the final manifest fingerprint (`MANIFEST.json` -> shot -> `profile.cycles`), so changing any of them
re-renders a shot instead of mixing settings. The effective atmosphere/grade are part of the resolved shot, so changing a canon
`look.atmosphere*`/`look.grade*` entry makes the affected `resolved:` nodes (and the frames made from them) stale through the normal
impact analysis (`fm plan`).

### Denoiser, honestly

- `oidn`: Intel Open Image Denoise, runs on the CPU, works anywhere. **The realistic default on a Windows ARM64 laptop.** Whether the
  Windows-ARM64 Blender 5.2.1 build ships OIDN is **not verified**: if it does not, the fallback below turns denoising off and the log says so.
- `optix`: NVIDIA OptiX, needs an NVIDIA GPU with OptiX and `device: optix` (or `auto`). The user's laptop has none, so this path is
  only exercised through its fallback.
- `auto`: `optix` when an OptiX device is in use, else `oidn`, else `none`.
- Fallback chain `optix -> oidn -> none` always logs one line: `FM_DENOISER requested=... used=... reason=...` (and `FM_RENDER_ENGINE ...`
  with the device actually used) in `10_blender/logs/*.log`. Read it before trusting a render.
- Denoising removes noise at low samples; it can also smear fine detail. Judge a denoised still, not the noise.

## Atmosphere

- `hdri`: world environment texture from `library/hdri/<id>/` through a Mapping node (`rotation_deg` about the vertical axis) into the
  world's `Background` (`strength`). `camera_visible: false` mixes the previous sky back in for camera rays (Light Path).
  The record is verified at render time: missing/UNKNOWN licence, missing file or checksum mismatch stops the shot with the reason.
- `fog`: Volume Scatter. `bounds: world` (default) is a world volume, uniform or `density * exp(-height_falloff * z)`;
  `bounds: box` is a bounded volume cube (`box.center`, `box.size`) for a local fog bank. `anisotropy > 0` gives forward-scatter light
  shafts. `density` is per metre: roughly 0.003 to 0.01 light haze, 0.02 to 0.05 thick fog. Volumes raise render time sharply.

## Grade

`grade` builds Compositor nodes in a fixed order: **Exposure -> Color Balance -> Hue/Saturation -> RGB Curves -> Glare (bloom added
on top)**, spliced in front of whatever already feeds the output (so the locked final glare of `look.style.glow` keeps working).
`view_transform` / `look` set the scene's colour management instead (Standard stays the default; any other value is an explicit
look decision). Color Balance values follow Blender: lift/gamma/gain neutral at 1.0 (or `mode: cdl`: slope/power 1.0, offset 0.0).

### DaVinci Resolve

**Resolve is not automated.** `fm post grade-handoff` writes `13_delivery/resolve_handoff/`: `GRADE_SPEC.yaml` + `grade_spec.json` (per shot:
frame range, effective grade, atmosphere, where the frames are and their PNG bit depth) and `README_RESOLVE.md` (the manual steps: render
with `cinematic_final`, import the sequences and the EDL, set the input colour space, grade by eye). It records nothing in project state,
produces no `.drx`/`.cube`, and the numbers are a brief for a colourist: Resolve's maths differs from Blender's compositor.

## Materials and what a Cycles film gets today

Shader to RGB (the heart of the toon cel material) exists only in EEVEE, so with a Cycles profile `util.toon` builds a Principled BSDF
from the same colour (key `...pbr`) and the painted outlines are skipped. The set, character and prop builders in `blender/fm_blender/`
(`sets.py`, `characters.py`, `phone.py`, `blackout.py`) and the lighting in `preview.render_shot` were written for last_signal; a new film
gets the generic stage (`build_generic`) and the same proxy figures until its own builders are added. Atmosphere and grade apply to any
shot, but they do not make a proxy scene look realistic by themselves.

## Runtime and cost

- **Cycles on a CPU is slow.** Seconds per frame for this system are **UNKNOWN until measured** on the target machine (nothing here
  has been timed beyond 16-48 px test frames). Plan: measure one hero frame with `fm blender frames --profile cinematic_preview` at the
  target width, scale by samples and frame count, then choose `samples`/`adaptive_threshold`/`resolution_scale`.
- `cinematic_final` uses `chunk_frames: 12` and the per-process `--timeout` is 3600 s by default: if a chunk of 12 frames takes longer,
  raise `--timeout` or lower `chunk_frames` in the profile.
- Cost drivers, in order: resolution, samples, volumetric fog (and `max_bounces`), denoiser off (needs more samples), HDRI resolution (memory only).
- A final render still needs the human's `fm authorize final-render` (the profile keeps `requires_authorization: true`, and `final()`
  refuses without it for any profile). The cloud draft route (`--route cloud`, bpy 5.0.1) renders Cycles on CPU for tests at tiny
  samples; `fm qa final` rejects its output as non-pinned.

## Verification status

| Item | Status |
|---|---|
| Profile loading/validation, env export, denoiser/device planners, HDRI record checks, schema, canon merge, resolver, validate codes, final-manifest fingerprint, handoff files | unit-tested (pure Python, always run) |
| last_signal validates with 0 errors, shot hashes and resolved JSON identical, no node stale | tested against the real project |
| Cycles configure + OIDN on CPU, HDRI/fog/grade node building and a graded vs ungraded render, grade splice before the final glare, `fm blender frames --draft --profile cinematic_preview` end to end on a copy of last_signal with an HDRI + fog + grade shot | run on **bpy 5.0.1 (cloud, CPU)** |
| Everything Blender-side on the **pinned Blender 5.2.1** (Windows ARM64): node socket names, Color Balance/Glare/Curves API, OIDN availability, 16-bit PNG, volume scatter | **untested** |
| OptiX denoiser and any GPU device | **untested** (no NVIDIA hardware); only the fallback is tested |
| Real Poly Haven HDRI file | **untested** (test HDRIs were generated 64x32 images) |
| A full Cycles final render of a film; seconds per frame | **not done** |
| DaVinci Resolve | not automated, not tested |
