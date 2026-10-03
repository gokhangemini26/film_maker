# 2D engine (`two_d/fm_2d`)

A second render backend next to Blender, for films the user wants as **2D animation**
(first use: `projects/zeka_tarihi`, a narrated book-summary episode for YouTube).

Same principles as the Blender side: every frame is reproducible from text (Python scene
files), assets are original code-drawn illustrations, nothing lives only in a binary file.

| File | Role |
|---|---|
| `two_d/fm_2d/core.py` | canvas 1920x1080 @ 30 fps, easing/timing, paints, gradients, glow, spline paths, draw-on, kinetic type, 2D camera, particles, finishing (vignette + grain) |
| `two_d/fm_2d/assets.py` | reusable original illustrations: robot character, brain (line-art and illustrated, neuron firing), chess board/pieces, kitchen + dishwasher + plate, open book, fossils (ammonite, trilobite, fish, worm trace), rock strata, staircase/creatures, layered brain, human glass-head, ice block, clock, chat window, memory cards, glitch effect |
| `two_d/fm_2d/audio.py` | synthesized SFX and ambient pad (no third-party samples), stereo mixer, wav I/O |
| `two_d/fm_2d/render.py` | parallel chunked render to H.264 + audio mux |
| `projects/<film>/10_2d/SCxx.py` | one scene: shot timings, word cues, `render(canvas, t)`; `--still t ...` for review frames |
| `projects/<film>/12_post/SCxx_audio.py` | scene mix: narration (master timeline) + bed + SFX tied to the scene's cue times |

## Narration-driven timing

The user's recorded voice is the master clock. `references/voice/words.json` holds word
timestamps (faster-whisper, medium, Turkish); scene files put those times in a `CUE` table
and every animation beat is keyed to a word, so a re-recorded line only needs new cues.

## Commands

```
pip install skia-python numpy pillow faster-whisper
python projects/zeka_tarihi/10_2d/SC01.py --still 3.0 8.9 15.6          # review stills
python projects/zeka_tarihi/12_post/SC01_audio.py                        # mix
ffmpeg -i 12_post/audio/SC01_mix_pre.wav -af loudnorm=I=-14:TP=-1.5 12_post/audio/SC01_mix.wav
python two_d/fm_2d/render.py projects/zeka_tarihi/10_2d/SC01.py --audio .../SC01_mix.wav --out .../SC01.mp4
```

Delivery target: YouTube 1080p30, H.264 CRF 15, AAC 256k, -14 LUFS integrated.

## Multi-scene programme (zeka_tarihi SC01-SC04)

Scenes share helpers by importing the previous scene module (`SC02` loads `SC01`, `SC03` loads `SC02`,
`SC04` loads `SC03`), keep one robot character and palette (amber/coral = biology, cyan/violet =
silicon), and cut frame-exactly: each scene declares `START` (previous scene's end) and `DURATION`.
One continuous music bed (`12_post/music.py`) is sliced per scene so the score never restarts.

```
python projects/zeka_tarihi/12_post/SC04_audio.py                       # per-scene pre-mix
python two_d/fm_2d/render.py projects/zeka_tarihi/10_2d/SC04.py --out .../SC04_video.mp4 --start 83.9
python projects/zeka_tarihi/12_post/assemble.py SC01 SC02 SC03 SC04     # trim, join, loudnorm once
```

Renders take ~6-8 min per 30-45 s scene and the assembly ~15 min, so run them in the background.
Final programme: `13_delivery/zeka_tarihi_SC01-SC04.mp4` (127.4 s, 1080p30, CRF 17, AAC 256k, ~-14 LUFS).
