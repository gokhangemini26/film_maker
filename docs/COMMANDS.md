# `/film-*` commands

Run inside Claude Code opened at the repository root. Each phase command
follows the same procedure (skill `project-management`, section A):

1. `fm status` — the project must be in the right phase
2. dispatch the owning agent(s)
3. `fm stamp` everything written, `fm validate`
4. `fm intent` (and `fm check continuity` at STORYBOARD)
5. qa-supervisor writes the gate review
6. `fm submit` — then **stop** and tell you the exact command to decide

Gate decisions are always yours, typed in your own terminal:
`fm approve G#`, `fm revise G# --notes "..."`, `fm reject G# --notes "..."`.

| Command | Phase | Agents | Ends at |
|---|---|---|---|
| `/film-new <slug> <idea...>` | IDEA → BRIEF | creative-director (brief analysis) + up to 5 questions for you | CREATIVE_DIRECTION |
| `/film-direction` | CREATIVE_DIRECTION | creative-director → qa-supervisor | **G1** |
| `/film-story` | STORY | story-architect | advance to SCREENPLAY |
| `/film-script` | SCREENPLAY | screenwriter → qa-supervisor | **G2** |
| `/film-world` | WORLD_CHARACTERS | world-designer → character-designer → qa-supervisor | **G3** |
| `/film-look` | LOOK | look-director → qa-supervisor | **G4** (style lock) |
| `/film-cinematography` | CINEMATOGRAPHY | cinematographer | advance to STORYBOARD |
| `/film-storyboard` | STORYBOARD | cinematographer → animation-director → qa-supervisor | **G5** |
| `/film-blender [shots]` | ASSET_PREP → PREVIEW | blender-td | previews + per-shot report (G6 is yours) |
| `/film-animate [scope]` | ANIMATION (M6) | animation-director → blender-td | frames + checks; advance to ANIMATION_PREVIEW |
| `/film-playblast [scope]` | ANIMATION_PREVIEW (M6) | blender-td | frames, playblast, motion QA, contact strips (report) |
| `/film-audio` | ANIMATION_PREVIEW (M6) | sound-designer | audio canon, bible, cue sheet, asks list (report) |
| `/film-post` | ANIMATION_PREVIEW (M6) | post-supervisor → qa-supervisor | **G7** |
| `/film-final [scope]` | FINAL_RENDER (M6) | blender-td → qa-supervisor | **G8** (needs your final-render authorization first) |
| `/film-export` | POST (M6) | post-supervisor | delivery report |
| `/film-next` | whatever is next | — | runs the right command above |
| `/film-status` | any | — | plain-language status + next step |
| `/film-review` | any | qa-supervisor | review written, nothing submitted |
| `/film-continuity [scope]` | any | qa-supervisor | findings only, nothing written |
| `/film-revise "<feedback>"` | any | owners of affected work | change requests / regenerated work |

All commands accept an optional project slug as the first argument and pass
any further text to the agents as your notes, e.g.
`/film-look last_signal keep the palette almost monochrome`.

## Revising

`/film-revise "Change Mara's jacket to dark brown"`:

1. finds the affected canon and runs `fm impact` — you see the blast radius first
2. unapproved work → the owner revises it
3. approved/locked canon → the owner writes `fm change propose ...` with a new
   rationale; **you** run `fm change approve CHANGE-NNN`
4. `fm plan --scope ...` → only stale items are regenerated, by their owners
5. affected reviews are redone; you re-approve the drifted gates

## Feedback loop (M5)

Files only, under `qa/feedback/FB-###.yaml` (no ledger line: the ledger has no
non-approval record action, and `fm record` writes derived-product JSON only).

```
fm feedback add shot:SC04_SH050 --note "head out of frame" [--severity low|medium|high|blocker] [--owner ROLE]
fm feedback list [--open]
fm feedback plan FB-001        # owner + command, change request needed?, minimal stale set (fm plan/impact)
fm feedback resolve FB-001 --by "reframed, restamped" [--force-stale]   # agents allowed; actor recorded
fm qa review-status [--file qa/reviews/PREVIEW_REVIEW.md] [--json]      # PASS/WARN/FAIL counts + stale vs project
```

Owner routing (first keyword in the note wins, then the canon domain, then
`cinematographer` for shots): camera/framing -> cinematographer; motion ->
animation-director; colour/ui/lighting -> look-director; figure/character ->
character-designer; world/set/car/prop -> world-designer; builder/blender/proxy
-> blender-td. `/film-revise` remains the way to act on a plan.

## M6 commands (in progress)

`/film-animate`, `/film-playblast`, `/film-audio`, `/film-post`, `/film-final` and
`/film-export` are defined, but the tools they call land incrementally, so each
command states which `fm` subcommands may not exist yet and reports the
missing ones instead of pretending they ran:

| Tool | Lands in M6 step |
|---|---|
| `ANIM_*` validation (in `fm validate`) | A1 |
| resolver `motion` block | A3 |
| `fm blender frames`, `fm blender playblast` | C4 |
| `fm qa motion` tier 0, alias `fm check anim` (below) | D1 |
| `fm qa motion` tier 1 (bake report) | D2 |
| `fm audio list`, `fm audio synth` | E2 |
| `fm audio scaffold`, `AUDIO_*` validation | E4 |
| `fm audio mix`, `fm qa audio` | E5 |
| `fm post edl`, `fm post animatic` | F2 (landed) |
| `fm blender final` | F3 |
| `fm post assemble|export`, `fm qa delivery` | F4 (landed) |

```
fm qa motion [--strict] [--no-record]     # alias: fm check anim; tier 0, no Blender; exit 1 on FAIL
```

Tier 0 reads the anim files, shot specs, canon and (if present) `09_resolved/`, writes
`qa/motion_report.json` (`{summary:{fail,warn,shots}, rows:[{shot, findings:[[sev,msg]]}]}`, the file the
ANIMATION contract requires with `summary.fail == 0`) and records the derived node `qa:motion`
(`--no-record` writes the report only). Film and scene findings sit in rows named `FILM` / `SCnn`.
FAIL: `ANIM_*` rules (frames vs the shot table, key range and order, vocabulary and transition
legality, comic faces after the turn, hold minimums); persistent-prop jumps between consecutive shots
in film order (a change needs a key after f0, or a `rationale` on the f0 key) and against
`continuity.props.*` per scene; camera peak speed over the `camera.movement.push_in` cap (0.15 m/s), dolly
length vs the shot's start/end positions, camera moves outside SC04 or beyond the allowed count; phone
screen rules from `look.style.phone_screen.states_by_shot` (0 %, digit hidden, colour vs number, battery
not in `continuity.battery` for the scene or changing at a cut, bolt while the crank arm is folded, overlay
events changing the table's number/colour/bolt, resolved `ui_timeline` out of date); resolved frame
counts or `film.json` total differing from the shot table. WARN: a missing or stub anim file (FAIL with
`--strict`), long pose-key gaps, locomotion speed above the gait limit, `sound_sync` frames with no named
event, scene running time more than 3 % off `SCENES.yaml`, film length more than 5 % off the brief,
resolved motion out of date. Technical only; never creative evidence.

```
fm audio list [--json]                          # synth registry: recipe, placeholder flag, default length, `serves` lines
fm audio synth [--id NAME]... [--out DIR] [--seed N]   # library WAVs (default 12_post/audio/lib/); writes only DIR
fm audio scaffold [--out FILE] [--force]        # PROPOSED cue-sheet skeleton (default 12_post/AUDIO_CUES.yaml; never overwrites)
fm audio mix                                    # AUDIO_CUES.yaml -> 12_post/audio/mix_48k_stereo.wav + stem_<layer>.wav + mix_report.json
fm qa audio [--final] [--ffmpeg|--no-ffmpeg]    # qa/audio_report.json; exit 1 on FAIL
```

`12_post/AUDIO_CUES.yaml` (artifact kind `audio_cues`, exactly one; schema `fm.schemas.audio`) holds `mix` targets
(-16 LUFS +-1, -1 dBTP, silence floor -50 dBFS, 48 kHz stereo 24-bit, `master_gain_db`), `cues`, `beds`, `silence`,
`human_supply` and `conflicts`. A cue names one `recipe` (synth registry) or one library `asset`
(`library/audio/<id>/asset.yaml`: `file`, `licence`, optional `tags`, `placeholder`) and is placed at
`at.event` (a named anim event, optionally `nth` or `each`, plus `offset_f`) or at an explicit shot-local
`at.frame`; retiming a shot moves event cues. Other fields: `gain_db`, `pan`, `fade_in_f`, `fade_out_f`,
`duration_f`, `params`, `hits` (sync landmarks inside one cue), `tail_ok`, `allowed_in_silence`, `note`,
`rationale`. `fm validate` runs the `AUDIO_*` rules: FILE, FPS, SHOT, DUP_ID, SOURCE, RECIPE, ASSET, SPEECH
(the film is wordless), AT, EVENT, EVENT_AMBIGUOUS, EVENT_NTH, OUT_OF_SHOT, PAST_SHOT, BED, SILENCE,
SILENCE_OVERLAP, HIT, MIX (errors) and LICENCE, PLACEHOLDER, UNLISTED_PLACEHOLDER (warnings).

`scaffold` builds the skeleton only from facts the repo holds (each shot's `sound_sync` line, anim events, the
registry's `serves` lines), points a cue at a named `sound` event when one sits on the frame, and lists every sync
point it could not cover in `scaffold_notes`; the sound-designer edits it, then `fm stamp` and `fm validate`.
`mix` is deterministic and sample exact (`total_frames x 2000` samples; 2 880 000 for 60 s), applies no limiter or
normalisation (the suggested `mix.master_gain_db` is printed) and records the derived node `audio:mix`.
`qa audio` FAILs on: a `sound` anim event or `sound_sync` frame with no cue start or `hits` within +-1 frame, a
silence span measuring above its floor, clipping, true peak above target, integrated loudness outside target
(ffmpeg ebur128 when available, else a built-in BS.1770 approximation), wrong length or sample rate, a stale mix,
no mix; WARNs on placeholders in the mix, digitally silent frames outside the silence map and UNKNOWN licences
(FAIL with `--final`). It lists `human_supply` and records `qa:audio`. Technical only.

```
fm post edl [--out DIR]                         # 12_post/EDIT.edl (CMX3600, 24 fps NDF) + edit.ffconcat
fm post animatic [--out DIR] [--size WxH] [--audio WAV] [--no-audio] [--no-stamp]
fm post assemble [--out DIR] [--frames DIR] [--audio WAV] [--silent] [--grain] [--vignette N]
                 [--fade-in N] [--fade-out N]   # master mezzanine in 13_delivery/
fm post export [--out DIR] [--master FILE] [--no-proxy]   # web MP4 + proxy + MANIFEST.json
fm qa delivery [--out DIR] [--report-dir DIR] [FILE...]   # qa/delivery_report.json; exit 1 on FAIL
```

Post tooling reads the resolved frame table (`09_resolved/film.json`, must be contiguous and sum to
`total_frames`) and never authors the edit: hard cuts in scene-then-shot order, a fade in (canon
`post.fade_in`, else 12 frames) and the fade out from `camera.rhythm.transitions`. `edl` writes exact
frame-accurate events and an ffconcat list. `animatic` uses per-shot rendered frames
(`10_blender/frames/<SHOT>`, then `playblast`) when present, else the preview still held for the shot
duration with the shot id stamped, and muxes `12_post/audio/mix_48k_stereo.wav` if present (a mix whose
length is not the film's is refused as stale; `--no-audio` skips it). `assemble` needs a complete
`11_render/final/<SHOT>/%04d.png` per shot (frame counts checked), applies grain and vignette only when
asked (strength from look canon; vignette above canon max is refused), fades, two-pass loudnorm to
-16 LUFS / -1 dBTP, and writes ProRes 422 HQ (x264 crf 8 mkv fallback if `prores_ks` is missing).
`export` writes the 1080p H.264/AAC web MP4, a 640 px proxy and `MANIFEST.json` (sha256, bytes, probe
facts, ffmpeg version and source). `qa delivery` checks frame count and duration (60.0 s, 1 frame),
24 fps, resolution against `camera.format`, 48 kHz stereo audio, loudness and true peak, black or frozen
head and tail, and manifest checksums. Every command takes `--out` (or `--report-dir`) so dry runs never
touch the project. ffmpeg is found via `$FM_FFMPEG`, PATH, then `imageio_ffmpeg`; without ffprobe on PATH
the probe parses `ffmpeg -i` and counts frames by a stream-copy decode.

The steps are the task ids in [M6_SCOPE.md](M6_SCOPE.md) section 6.
The core enforces what each command must leave behind (files, per-shot anim files, QA reports
with no FAIL): see the M6 table in [WORKFLOW.md](WORKFLOW.md). G7 is "Animation, audio and post
plan"; POST has no gate in this cut, so `fm advance` out of POST checks the delivery report.
Approving G7 does not authorize the final render: `/film-final` needs your own
`fm authorize final-render` first, typed in your terminal. Agents cannot run it.

Not yet available: `/film-render` (M3–M4), `/film-qa` (M4).
