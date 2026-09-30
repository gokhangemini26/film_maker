"""Entry for `fm blender build`: works under the pinned exe (`blender -b --python run_build.py -- ...`)
and under the bpy module (`python run_build.py ...`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_blender import build  # noqa: E402

build.main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
