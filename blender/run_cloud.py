import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_blender import preview
preview.main(sys.argv[1:])
