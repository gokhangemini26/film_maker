# 2D engine (`two_d/fm_2d`)

A second render backend next to Blender, for films the user wants as **2D animation**
(first use: `projects/zeka_tarihi`, a narrated book-summary episode for YouTube).

Same principles as the Blender side: every frame is reproducible from text (Python scene
files), assets are original code-drawn illustrations, nothing lives only in a binary file.

| File | Role |
|---|---|
| `two_d/fm_2d/core.py` | canvas 1920x1080 @ 30 fps, easing/timing, paints, gradients, glow, spline paths, draw-on, kinetic type, 2D camera, particles, finishing (vignette + grain) |
| `two_d/fm_2d/assets.py` | reusable original illustrations: robot character, brain (line-art and illustrated, neuron firing), chess board/pieces, kitchen + dishwasher + plate, open book, fossils (ammonite, trilobite, fish, worm trace), rock strata |
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
