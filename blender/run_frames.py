"""Render frames of one shot. Two routes, one script:
  cloud bpy   python blender/run_frames.py <resolved_dir> <out_dir> <SHOT> <width> <frames|all> [stamp]
  pinned exe  blender -b --factory-startup --python blender/run_frames.py -- <same arguments>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_blender import animate  # noqa: E402

animate.main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
