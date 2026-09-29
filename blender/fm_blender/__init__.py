"""fm_blender: idempotent scene builders that run INSIDE Blender 5.2.x (bpy).

Input is only JSON produced by `fm resolve` (film.json + per-shot files); nothing here reads YAML or
project state. Every generated datablock is tagged fm_owner="fm_blender" plus fm_id, and each build
unit is a collection carrying the hash of its inputs, so a rebuild creates, updates or removes only
what changed.
"""
BUILDER_VERSION = "0.1"
