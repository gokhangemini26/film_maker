"""Deterministic procedural sound library and sample-exact mixer (M6 task E2).

- ``fm.audio.synth``  : recipe registry (name -> function, description, shot events served)
- ``fm.audio.mix``    : 48 kHz stereo timeline on the 24 fps frame grid, stems, loudness measure
- ``python -m fm.audio`` : list / render / mix / measure (fm audio subcommands are wired later)

Everything is numpy-only (no scipy needed) and bit-identical for identical inputs.
"""

from .synth import FPS, REGISTRY, SR, list_recipes, render, render_frames
from .mix import Timeline, frame_to_sample, measure, read_wav, write_wav

__all__ = [
    "SR", "FPS", "REGISTRY", "list_recipes", "render", "render_frames",
    "Timeline", "frame_to_sample", "measure", "read_wav", "write_wav",
]
