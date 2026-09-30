---
fm:
  id: post_plan
  kind: post_plan
  phase: ANIMATION_PREVIEW
  status: PROPOSED
  owner_role: post-supervisor
  derived_from:
  - ref: artifact:edit_plan
    hash: sha256:963f35db15fd5bf2709367598a8b68b32e47151919a3f13a71ca1663e79b91ee
  - ref: artifact:audio_cues
    hash: sha256:7429405e767d311ddc2be98036e0d1da623777dee787584b4e10771d0e523e68
  - ref: artifact:creative_direction
    hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
  - ref: canon:look.style.texture_and_grain
    hash: sha256:544d2906507dbfac6969ea7ce0b48e5a8978571267e475fc5f86fcfc2ab71698
  - ref: canon:look.style.glow
    hash: sha256:894609d6570cb3d925e8a7697aa0cc2bcb14b26910712173ab394d4c9bc4d087
  - ref: canon:look.style.render_constraints
    hash: sha256:5ff198e989a3e2bfe6217768a89180fee793f10f9c349cccdf50a71f00958c0e
  - ref: canon:look.style.phone_ui
    hash: sha256:5b1bcd7579ec10d43bbfefbd045d981b00248cbbc4ca45550862e8c0df97c0e6
  - ref: canon:camera.format
    hash: sha256:2501c716273516ebe3e4dba470a0e8896aff0761fda6926bbb09cfc7bad1eeea
  - ref: canon:camera.rhythm.transitions
    hash: sha256:0ff059c432a2227bfbe4eebceef37bc953cd834328d87d7ae75970a866ddcb15
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:world.rules.no_readable_text
    hash: sha256:a21cccd660b3af6cffb29094f0fab852e3e2fe1bd316dd2e7dcb094615bad1ae
  - ref: canon:audio.mix
    hash: sha256:6928de0e3e54edc5d62ed70cec1108d335e08443b7d45148af2206cd5b5c0c60
  serves:
  - intent.soft_but_cinematic
  - intent.anime_feel
  - intent.open_hopeful_ending
  summary: Locked finish steps with parameters read from canon (glare, grain, optional vignette, fades),
    titles ruling, final render settings proposal, delivery spec, licence status; human decisions D2/D3/D5/D6/D7/D9
    left UNKNOWN.
  stamped_content_hash: sha256:a758974886f6d08533803e75e2bb646073ae38b1d6ae1c85795a79caa56591e8
title: Post Plan
---
# Post Plan: Last Signal

Post adds only the finish the look canon locks. There is no creative grade. Every parameter below is
read from a canon value and names its source, so a canon change restales this plan. Human decisions
are recommendations and stay **UNKNOWN** until ruled.

## 1. Order of operations (POST phase, after G8)

`11_render/final/<SHOT>/%04d.png` (glare already applied in the Blender compositor at render)
-> grain -> [vignette, only if D5 = on] -> FADE IN / FADE OUT -> audio mux (loudness D3) -> master
-> delivery encodes -> `fm qa delivery` -> `13_delivery/MANIFEST.json`.

FACT: `fm post assemble` implements this order (`core/fm/post.py`: "[grain] -> [vignette] -> fades ->
audio (loudnorm 2-pass) -> mezzanine"). Grain and vignette are **off by default** in the tool. The POST
command line must pass `--grain` explicitly (section 2.2).

## 2. Finish steps (parameters read from canon)

### 2.1 Glare (render time, not assembly)
- Source: `look.style.glow` (LOCKED). `glow_sources: emissives_only`, `max_radius_pct_frame_width: 1.5`
  (= 28.8 px at 1920 wide), `streaks: false`, `star_glare: false`, `ghosts: false`, `bokeh_discs: false`,
  `implementation: compositor_glare_bloom_on_emission_pass`.
- DECISION: applied in the Blender compositor at final render (owner: blender-td), not in post.
  Rejected: a post bloom in ffmpeg (it cannot isolate emissives without the emission pass).
- UNKNOWN: whether the compositor glare path has been verified on this machine (M6 task A0). Until it is,
  the final profile cannot be called ready (section 4).

### 2.2 Grain (assembly)
- Source: `look.style.texture_and_grain` (LOCKED). `grain.type: monochrome`, `amplitude_luma: 0.015`,
  `uniform_across_film: true`.
- DECISION: applied at assembly by `fm post assemble --grain`. The tool reads `amplitude_luma` from canon
  (`finish_params`) and builds ffmpeg `noise` on luma only, temporal, with a fixed seed (1337) so the
  result can be reproduced. Rejected: baking grain in Blender (it cannot be re-applied without a
  re-render, and it doubles the risk of wrong colour on the Windows ARM machine).
- ASSUMPTION: the mapping from 0.015 to ffmpeg's `c0s` strength gives about 1.5 % luma amplitude. Nobody
  has measured this yet. Verify on one final shot at POST (difference of graded and ungraded frame, std
  of luma) before the full assembly.

### 2.3 Vignette (optional, D5)
- Source: `look.style.texture_and_grain` `vignette_max: 0.1` ("the same on every shot").
- **D5: UNKNOWN.** RECOMMENDATION: **off**. The composition canon already places light and value. A
  vignette can be added at assembly at no cost later (`--vignette 0..0.1`) with no re-render, so deciding
  "off" now closes no doors. Rejected: 10 % on (darkens the phone inserts' corners, where the pip and the
  status bar sit); a per-shot vignette (canon forbids it).

### 2.4 Fades
- FADE OUT: 18 frames at the tail, after the final-image hold. Source: `camera.rhythm.transitions`
  `fade_out.frames: 18` (LOCKED). Record 1422-1439 (see EDIT_PLAN section 3).
- FADE IN: **D7 UNKNOWN.** Canon says `fade_in: head` with no length. RECOMMENDATION: **12 frames**.
  Rejected: 24 and 0/6 frames (reasons in EDIT_PLAN section 1). FACT: `fm post edl` and
  `fm post assemble` currently use a code default of 12, labelled "default (M6_SCOPE D7 recommendation)",
  because no canon `post.fade_in` exists. Once the human rules, the value should become canon (a `post`
  domain entry `post.fade_in`, if the human adopts that domain), so that the EDL and the master read it
  instead of a default.
- Audio follows picture: the sound fades in and out over the same frames (EDIT_PLAN section 5).

### 2.5 Not applied (canon forbids)
- FACT, `look.style.texture_and_grain`: `chromatic_aberration: false`, `extra_lut: false`, no sharpening.
  FACT, `look.style.render_constraints`: Standard view transform, look None, exposure 0, gamma 1. The
  colour is final at render. Post applies no grade, LUT, sharpening or CA. Any request for one is a
  change request against look canon.

## 3. Titles and credits (D2)

- FACT: `tone.wordless` (LOCKED, USER_REQUIREMENT): "The typed English dinner invitation is the ONLY
  readable text in the film." `world.rules.no_readable_text` (LOCKED) says the same.
- FACT: CREATIVE_DIRECTION says "The confession happens after the credits, in the viewer's head", so
  credits are expected creatively. This question has been open since G1 (G1 review item 1; G4 review
  finding 11).
- **D2: UNKNOWN.** Options:
  - **A. No on-screen text in the 60 s master.** The title and credits go in the file metadata
    (title, artist, comment) and in the delivery description. Consistent with canon; no change request.
  - **B. A 3-4 s title/credit card as a separate bumper file**, outside the 60 s runtime and never cut
    into the master. It is readable text, so the human must rule whether `tone.wordless` covers a card
    outside the story, or approve a change request scoping it to story frames.
  - **C. Title card inside the runtime (head or tail).** Rejected: it breaks the FADE IN onto the car
    (or the held final image and the fade to black), and it spends frames the LOCKED budget does not have.
- RECOMMENDATION: **A for the master**, plus **an optional B bumper delivered as its own file** only if a
  festival or platform requires a card. If B is chosen, post does not build it until the human rules on
  `tone.wordless` scope (ruling or `fm change propose` by the creative-director). Post will not propose
  that change itself.

## 4. Final render settings proposal (D6)

FACT: `config/render_profiles.yaml` `final` today reads: `engine: BLENDER_EEVEE`, `resolution_scale: 1.0`,
`samples: 64`, `motion_blur: true`, `output: exr`, `requires_authorization: true`.

| Setting | Current `final` | Proposed | Source / reason |
|---|---|---|---|
| Resolution | scale 1.0 | 1920x1080, scale 1.0 | FACT `camera.format` `resolution_px: [1920, 1080]` |
| Frame rate | (from scene) | 24/1 | FACT `camera.format` `fps: 24` |
| Engine | EEVEE | EEVEE, Blender pinned 5.2.x | FACT `look.style.render_constraints` `engine: eevee` |
| View transform | (builder) | Standard, look None, exposure 0, gamma 1 | FACT `look.style.render_constraints` |
| Samples | 64 | 64 | RECOMMENDATION; measure. 32 may be enough for flat toon shading, to be tested on 3 shots before the full run |
| Motion blur | **true** | **false** | FACT: `look.style.render_constraints` (LOCKED) says `motion_blur: false`. The current profile **contradicts locked canon**, so this row is a correction, not a creative choice. |
| Output | exr | 8-bit PNG sequence, RGB | RECOMMENDATION: no grade means no headroom is needed. EXR for 1440 frames is about 10 GB. `fm post assemble` reads `%04d.png`. |
| Compositor | none | glare on the emission pass | FACT `look.style.glow` `implementation` |
| Chunking | none | at most 48 frames per process, one shot per job, resumable | RECOMMENDATION (Windows ARM colour corruption on long processes, M6 scope 4.3) |
| Authorization | required | required: `fm authorize final-render` by the human | unchanged |

- **D6: UNKNOWN.** RECOMMENDATION: approve as proposed. Rejected: EXR output (size, and nothing downstream
  uses the range); motion blur on (canon forbids it, and blur smears the cel outline and the phone number).
- DEPENDENCY: post does not edit `config/render_profiles.yaml`. After D6, the owner (blender-td or the
  main session, via the normal process) writes the profile or a project override
  `projects/last_signal/config/render.yaml`.
- FACT (wave 6 re-check): `config/render_profiles.yaml` `final` still reads `motion_blur: true`. It is
  repository-wide config (shared by every film), outside post's lane. It is also not read by any `fm` code
  today (no consumer in `core/`), so nothing has been rendered with it yet. The motion-blur row needs no
  creative ruling, because locked canon already decides it. The other D6 rows (output, samples, chunking)
  do.
- ASSUMPTION: 1440 frames at 5-12 s each is about 2-5 hours of unattended rendering (M6 scope estimate,
  not measured on the real sets).
- Post never runs `fm authorize` or `fm blender final`.

## 5. Delivery spec

| File | Spec | Built by |
|---|---|---|
| `13_delivery/last_signal_master.mov` (mezzanine) | ProRes 422 HQ (`prores_ks` profile 3), 1920x1080, 24/1, 10-bit 4:2:2, BT.709 tv range; stereo 48 kHz 24-bit PCM; exactly 1440 frames, 60.000 s | `fm post assemble` |
| `13_delivery/last_signal_1080p.mp4` (web) | H.264 High, about 12 Mbps, yuv420p, AAC 320 kbps 48 kHz stereo, `+faststart` | `fm post export` |
| review proxy | small H.264 for review | `fm post export` (unless `--no-proxy`) |
| `13_delivery/MANIFEST.json` | files, sha256, probe facts, settings, `fm` and Blender versions (tracked in git) | `fm post export` |
| optional bumper (only if D2 = A+B) | separate file, never inside the master | not built until ruled |

- FACT: ffmpeg 6.1.1 in this environment has `prores_ks`, so the tool would write `.mov`. Without ProRes
  it falls back to lossless-ish H.264 in `.mkv`. ASSUMPTION: the assembly machine has the same encoder.
- **Loudness, D3: UNKNOWN.** RECOMMENDATION: **-16 LUFS integrated, -1 dBTP true peak**, 2-pass loudnorm.
  This is the web/mobile norm, and the quiet ending keeps its dynamics. Rejected: -14 LUFS (louder, and
  platforms turn it down anyway, at the cost of the tender half's range); -23 LUFS / EBU R128 (right for
  broadcast, far too quiet on phones and laptops). FACT: `audio.mix` now exists as **PROPOSED** canon
  (sound-designer: `integrated_lufs: -16.0`, `lufs_tolerance: 1.0`, `true_peak_dbtp: -1.0`, 48 kHz, 24-bit,
  stereo, `decision: D3`). It is not LOCKED, so D3 is still open. FACT: the wave-6 mix measures
  -16.39 LUFS (ffmpeg ebur128), true peak -1.7 dBTP (`fm qa audio`), inside the proposed target.
- `fm qa delivery` checks (all must PASS at POST): 1920x1080; exactly 24/1 fps; 1440 frames (+-0); duration
  60.000 s; audio 48 kHz stereo; integrated loudness within +-1 LU of target; true peak <= -1 dBTP; black
  only inside the fades; checksums match the manifest.
- DEPENDENCY: the master and the encodes are gitignored. Only `MANIFEST.json` is tracked.
- **D9 (gate G9 Delivery): UNKNOWN.** POST and DELIVERY have no gate today. RECOMMENDATION: add G9 (frames
  approved at G8, then the finished file approved at G9). Rejected: folding the master into G8 (it mixes
  "frames are right" with "the file is right" in one approval). This is a state-machine change the human
  must OK. Post only recommends it.

## 6. Licence status (blocks final export while UNKNOWN)

| Item | Where used | Source | Licence | Blocks export |
|---|---|---|---|---|
| breath (placeholder) | SC01_SH040/090/130/150, SC02_SH020, SC03_SH040, SC04_SH030/050-090, SC06_SH010 | to be recorded by the human | UNKNOWN | **yes** |
| sigh (placeholder) | SC01_SH060 | to be recorded | UNKNOWN | **yes** |
| nose laugh (placeholder) | SC05_SH030 | to be recorded | UNKNOWN | **yes** |
| foley: footsteps, door push, knees, cloth (`fx.soft_bump` placeholder, 6 asks) | SC02_SH010-030, SC03_SH010, SC04_SH040, SC05_SH020, SC06_SH010 | library files, human picks | UNKNOWN | **yes** |
| foley: seat creak, headphones, pencil, phone grip (`fx.plastic_scuff` placeholder, 3 asks) | SC01_SH060, SC04_SH040, SC05_SH020 | library files, human picks | UNKNOWN | **yes** |
| street bird | SC01_SH010, SC01_SH150 | library file | UNKNOWN | **yes** |
| distant traffic | SC03_SH070, SC04_SH010, SC06_SH010 | library file | UNKNOWN | **yes** |
| headphone leak music | SC05_SH010, SC05_SH020 | licensed track to be supplied (agents never generate music) | UNKNOWN | **yes** |
| phone UI font | typed invitation, numbers (`look.style.phone_ui` `font: open_licence_humanist_sans`) | not yet chosen (Noto Sans / Inter suggested) | UNKNOWN (canon notes: "Font licence UNKNOWN until verified") | **yes** |
| procedural sound recipes (`fm audio synth`) | all other cues | generated in-house | ASSUMPTION: own work, no third-party licence. To be confirmed by the sound-designer's registry | no, if confirmed |
| 3D assets, sky | all shots | built procedurally, no `library/assets` in use (the directory is empty) | FACT: nothing third-party found | no |

- FACT: `fm qa audio` (wave 6) lists 15 human-supply items with status NEEDED and licence UNKNOWN; the table
  above groups them.
- RECOMMENDATION: `fm post export` is not run for release until every UNKNOWN above is resolved. An
  animatic with placeholders is fine for G7 review.

## 7. Animatic (wave 6 run)

FACT, `fm post animatic` output: "`12_post/animatic.mp4`: 60.000 s, 1440 frames @ 24.0 fps, 1280x720, audio:
yes, 20 shots from frames, 18 from stills". ffprobe: video h264 1280x720, 24/1, 1440 frames, 60.000000 s;
audio aac 48000 Hz, 2 channels, 60.000000 s.

What it is and is not:
- **Picture is mixed.** 20 shots come from rendered frames: the 15 SC01 playblasts in
  `10_blender/playblast/` and 5 shots in `10_blender/frames/` (SC02_SH010, SC03_SH010, SC04_SH050,
  SC04_SH080, SC05_SH020). The other 18 shots are single preview stills held for their duration, so they
  show timing and order but not motion.
- **Sound is the wave-6 mix** (`12_post/audio/mix_48k_stereo.wav`), with the placeholders listed in
  section 6 and one door chime across SC02/SC03 (EDIT_PLAN section 5).
- **No fades.** The animatic does not apply the head and tail fades.
- So it is a **partial** G7 review artifact. A full G7 animatic needs motion for the remaining 18 shots
  (animation-director / blender-td). Rebuild with `fm post animatic` once they exist.

FACT, `fm qa delivery 12_post/animatic.mp4` (report `qa/delivery_report.json`), quoted summary line:
"1 delivery file(s): 1 FAIL, 2 WARN finding(s) (1 row(s) failing)". The command exits non-zero on FAIL.
- FAIL: resolution 1280x720, render canon says 1920x1080. **Expected**: the animatic is a preview-size
  review file (`--size` default 1280x720), not a delivery file.
- WARN: first frame is not black although a fade-in is specified; WARN: last frame is not black although
  a fade-out is specified. Expected for an animatic without fades.
- Passing: 24/1 fps, 1440 frames, 60.0 s, 48 kHz stereo audio of the right length, integrated loudness
  -16.5 LUFS (within +-1 LU of -16), true peak -1.8 dBTP.
- Tool fix (wave 6): the summary used to count files with a FAIL or WARN, not findings. It now counts
  findings, and keeps the per-file counts as `files_failing` / `files_warning` (`core/fm/post.py`
  `delivery_summary`). `fm qa audio` had the same bug and got the same fix.

## 8. Risks

1. 18 of 38 shots still have no motion in the animatic (section 7). Owners: animation-director,
   blender-td. The mix exists (wave 6).
2. The final profile still contradicts locked canon (`motion_blur: true`, re-checked in wave 6). If nobody
   corrects it before `fm authorize final-render`, the whole render is wrong. The fix is one line in
   `config/render_profiles.yaml`, made by its owner; D6 closes the rest.
3. The grain amplitude mapping has not been measured (2.2). If it is wrong, the grain is too strong or
   too weak on every frame. Verify on one shot first.
4. Compositor glare is untested (2.1). It must pass A0 before the final render.
5. D7 comes from a code default, and D3 from PROPOSED (not LOCKED) canon `audio.mix`. A later change to the default would silently
   change the film. Put the rulings in canon.
6. UNKNOWN licences (section 6) block release, and the font one also blocks the final render of the
   insert shots.
7. G5 is DRIFTED. A different re-approved shot timing moves every record frame here. Regenerate by
   `fm resolve` -> `fm post edl` -> re-stamp.
