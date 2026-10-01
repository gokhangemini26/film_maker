# Production runbook: from G7 to the delivered master (laptop, PowerShell)

Ordered, copy-paste sequence for the real film (`last_signal`) on the laptop with the pinned Blender. Every flag below was checked against
`fm <command> --help` of this repository state. Steps marked **HUMAN** are human-only: `fm` refuses them for any non-interactive caller, and
Claude never runs them. Run those in a normal PowerShell window you are typing in, with `FM_ACTOR` **unset** (`Remove-Item Env:FM_ACTOR`).

Conventions used throughout:

```powershell
cd C:\Users\ggule\film_maker
$env:FM_PROJECT = "last_signal"          # or add  -p last_signal  right after `fm`
$scenes = "SC01","SC02","SC03","SC04","SC05","SC06"
```

Stop at the first non-zero exit code. Every `fm` command here exits non-zero on failure, so after any step you can check `$LASTEXITCODE`.
Render commands are long (minutes to hours): keep the laptop on mains power and awake, and run **one render command at a time**.

---

## Part 1. Prepare (agent-safe commands, no gate decisions)

### 1. Sync and check the environment

```powershell
git pull --ff-only
python -m pip install -e ".[dev,vision]"     # only after dependency changes; ffmpeg must be on PATH too
fm --version
fm doctor                                    # must print: blender: 5.2.x OK (pinned 5.2.x); exit 4 means the pin is wrong
fm validate -q                               # 0 errors required (warnings such as GATE_DRIFT are listed, not blocking)
fm status
```

### 2. Resolve and the pinned stills

```powershell
fm resolve                                   # 09_resolved/ is current; a no-op when nothing changed
fm blender preview --width 768               # one pinned still per shot -> 10_blender/previews/ (add --jobs 2 if memory allows)
fm qa stills                                 # exit 1 on FAIL
```

### 3. Motion QA

```powershell
fm qa motion --strict                        # tier 0 on the anim files; writes qa/motion_report.json; exit 1 on FAIL
```

### 4. Review frames and the silent playblast, scene by scene

`--resume` keeps frames already on disk, so a crashed or interrupted scene is just re-run. Frames go to `10_blender/frames/`, the playblast to
`10_blender/playblast/`.

```powershell
foreach ($s in $scenes) { fm blender frames --scope "scene:$s" --every-key }      # QA frames + contact strips (strip.png per shot)
foreach ($s in $scenes) { fm blender playblast --scope "scene:$s" --resume }      # every frame, stamped, <SHOT>.mp4
fm blender playblast --resume                # whole film: every frame is already on disk, so this only encodes 10_blender/playblast/film.mp4
```

`film.mp4` is written only by a run whose scope is the whole film and that finds every shot complete. `fm blender frames` has no `--resume` (it
re-renders the few chosen frames each time).

### 5. Audio

```powershell
fm audio synth                               # library WAVs -> 12_post/audio/lib/ (deterministic, default seed 0)
fm audio mix                                 # AUDIO_CUES.yaml -> 12_post/audio/mix_48k_stereo.wav + stems
fm qa audio                                  # qa/audio_report.json; exit 1 on FAIL (an UNKNOWN licence is a WARN until the final: --final)
```

### 6. Edit list and animatic

`fm post animatic` takes its pictures from the **first** of `10_blender/frames`, `10_blender/playblast` that holds numbered frames. The
`frames` folder holds only the sparse `--every-key` stills, which would be step-held, so move it aside first (a rename, nothing is deleted):

```powershell
if (Test-Path projects\last_signal\10_blender\frames) {
  Rename-Item projects\last_signal\10_blender\frames frames_review
}
fm post edl                                  # 12_post/EDIT.edl, edit.ffconcat
fm post animatic                             # 12_post/animatic.mp4 with the mix; add --no-audio for a silent one
```

If `frames_review` already exists from an earlier run, delete or rename it first (Rename-Item will not overwrite). To get contact strips back
later, re-run `fm blender frames ...` (it recreates `10_blender/frames`).

### 7. Package for G7: the plans and the review, then submit

`12_post/EDIT_PLAN.md`, `POST_PLAN.md` and `qa/reviews/G7_REVIEW.md` are written by the agents (`/film-post` in Claude Code, which runs the
qa-supervisor review). Once they exist and are stamped:

```powershell
fm stamp 12_post/EDIT_PLAN.md                # only if /film-post did not already; one fm stamp per document it listed
fm validate -q
fm submit                                    # G7 contract: anim files, motion + audio reports, film.mp4, mix, animatic, EDL, plans, review
```

### 8. Commit and push

Final PNG frames are git-ignored, but the manifests and reports are not.

```powershell
git add -A
git status                                   # read it; no media should be staged except small files
git commit -m "M6: G7 package (playblast, mix, animatic, EDL)"
git push
```

---

## Part 2. Human decisions and the final render

### 9. HUMAN: approve G7, authorize the final render, advance

Watch `12_post/animatic.mp4` with sound and read `qa/reviews/G7_REVIEW.md` first. Approving G7 does **not** authorize the render; that is a
separate decision.

```powershell
fm approve G7                                # add --notes "..." (answers to the review's open questions); --ack-review if the review is WARN/FAIL
fm authorize final-render                    # scope defaults to the whole film; a narrower --scope only covers those shots
fm advance                                   # ANIMATION_PREVIEW -> FINAL_RENDER (refuses without both the approval and the authorization)
```

`fm blender final` checks the ledger itself and refuses without the authorization (it never creates one).

### 10. The final render (pinned Blender, chunked, resumable)

Profile `final` (`config/render_profiles.yaml`): EEVEE, scale 1.0 (1920x1080), 64 samples, **PNG output** (`fm post assemble` reads a PNG
sequence), at most 48 frames per Blender process. Frames go to `11_render/final/<SHOT>/NNNN.png` (0-based, shot-local);
`11_render/final/MANIFEST.json` records per shot the frame count, a sha256 per frame, the Blender version, route, profile settings and the hash
of the resolved shot. Logs: `10_blender/logs/final_<SHOT>_<frames>.log`.

Render scene by scene. Re-running the same line after any interruption continues where it stopped (valid, same-settings frames are kept; a
truncated PNG from a killed process is detected and re-rendered):

```powershell
foreach ($s in $scenes) {
  fm blender final --scope "scene:$s" --resume
  if ($LASTEXITCODE -ne 0) { Write-Host "scene $s incomplete: fix, then re-run this loop"; break }
}
```

Useful variants:

```powershell
fm blender final --scope "shot:SC03_SH050" --resume          # one shot
fm blender final --scope "scene:SC01" --resume --jobs 2      # two chunks (Blender processes) in parallel
fm blender final --scope "shot:SC03_SH050" --frames 96-143   # re-render only these shot-local frames (one-shot scope only)
fm blender final --scope "shot:SC03_SH050" --chunk-frames 24 # smaller chunks for a shot that crashes Blender
fm blender final --scope "scene:SC01" --width 960 --samples 16   # a quick dry run: NOT G8 material (see step 11)
```

Notes:

- Do not run two `fm blender final` commands at once: both rewrite `MANIFEST.json`. Use `--jobs` for parallelism instead.
- Changing `--width`, `--samples` or the profile after a shot was rendered makes `--resume` re-render the whole shot (a shot never mixes settings);
  `--frames` refuses in that case.
- `--route cloud` is the bpy draft and is rejected by `fm qa final`. The real render is the default `--route exe`.
- Chunk failures print `failed chunks (re-run with --resume)`; read the log named after the chunk.

### 11. Frame QA (the G8 contract file)

```powershell
fm qa final                                  # writes qa/final_frames_report.json; exit 1 on FAIL
```

It checks, for every shot of the resolved film: frame count (and no extra files), PNG integrity (a full decode), size against the manifest and
the film's aspect ratio and width, black frames (isolated ones are a FAIL; a run touching the shot's first/last frame, or 12+ frames long, is a
WARN to judge against the shot's intent), every frame's sha256 against `MANIFEST.json`, pinned-Blender route, and that the frames were rendered
from the current resolved shot. For a dry run at reduced size use `fm qa final --allow-reduced` (the contract still needs a clean report for G8).

### 12. G8: review and submit

```powershell
fm validate -q
fm status
# In Claude Code: /film-final  (qa-supervisor writes qa/reviews/G8_REVIEW.md), then:
fm submit                                    # contract: authorization, MANIFEST.json, final_frames_report.json with 0 FAIL, G8 review
```

### 13. HUMAN: decide G8 and advance to POST

Scrub representative frames and the licence table first.

```powershell
fm approve G8                                # or: fm revise G8 --notes "..."
fm advance                                   # FINAL_RENDER -> POST
```

### 14. Assemble, export and check the delivery

`fm post assemble` needs exactly the manifest's frames per shot (it counts `*.png` in each shot folder) and applies, in order: grain, vignette,
fades, the audio mix (loudnorm). Grain and vignette are off unless asked for.

```powershell
fm post assemble --grain                     # master from 11_render/final + 12_post/audio/mix_48k_stereo.wav -> 13_delivery/
                                             # add --vignette 0.1, --fade-in N, --fade-out N, or --silent as the post plan says
fm post export                               # web MP4 (+ review proxy; --no-proxy to skip) and 13_delivery/MANIFEST.json
fm qa delivery                               # ffprobe checks -> qa/delivery_report.json; exit 1 on FAIL
fm qa audio --final                          # UNKNOWN licences are a FAIL in final-export mode
git add -A; git commit -m "M6: final render manifest, master, delivery report"; git push
```

---

## Quick reference: who may run what

| Command | Who |
|---|---|
| `fm doctor`, `fm resolve`, `fm validate`, `fm qa *`, `fm blender preview|frames|playblast|final`, `fm audio *`, `fm post *`, `fm submit`, `fm stamp` | agent or human (`fm blender final` additionally needs the human's authorization in the ledger) |
| `fm approve`, `fm revise`, `fm reject`, `fm authorize`, `fm amend`, `fm canon approve|lock|reject`, `fm change approve|reject` | **human only**, interactive terminal |
| `fm advance` | allowed for agents by the rules, but in this runbook the human runs it at the two gates above so the decision and the move happen together |

## Recovery

| Symptom | Action |
|---|---|
| `final render refused: no human authorization` | The human runs `fm authorize final-render` (step 9). |
| `authorization does not cover ...` | Authorize `--scope film`, or render only the covered shots. |
| `blender: REFUSED` from `fm doctor` or the render | Wrong Blender series: fix `config/blender.yaml` / `FM_BLENDER` deliberately; never bypass. |
| A chunk failed or the laptop slept | Re-run the same `fm blender final ... --resume` line. |
| `fm qa final`: `corrupt or truncated frame(s)` or `do not match their MANIFEST hash` | Delete those PNGs and re-run with `--resume` (or `--frames a-b`). |
| `fm qa final`: `stale` | The resolved shot changed after the render (`fm resolve` ran). Re-render that shot (no `--frames`). |
| `fm post assemble`: `final frames incomplete` | A shot folder has the wrong number of `*.png`; `fm qa final` names it. |
