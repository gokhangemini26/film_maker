import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_blender import preview  # noqa: E402

preview.main(sys.argv[sys.argv.index("--") + 1:])
