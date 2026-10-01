"""World anchors of the corner shop, computed once for both the set builder (sets.build_shop) and the animation Stage.

Pure python (mathutils only), no bpy scene: sets.py places the USB socket and the display stand with these numbers and
animate.Stage expresses the kneel presets' shop context (`stand_back_edge`, `socket`) from the same ones, so a poses
context can never drift away from the geometry the set really builds.
"""
from __future__ import annotations

try:
    from mathutils import Vector
except ImportError:  # the standalone python: importing bpy registers the mathutils module
    import bpy  # noqa: F401
    from mathutils import Vector

SOCKET_WALL_INSET = 0.06     # socket plate centre from the back wall (sets: O.y + fd - 0.06)
SOCKET_FROM_RIGHT_WALL = 0.25
STAND_X_FROM_SOCKET = -0.20  # stand centre is 0.2 m to the left of the socket


def shop_anchors(c, origin):
    """`c` = canon world.sets.corner_shop value, `origin` = shop origin (world). Returns world points:
    socket (plate centre), stand_centre (x, y, 0), stand_back_edge (the point of the stand's back edge closest to the
    socket along x, on the floor), stand_back_normal (unit +y: away from the room, toward the wall) and the stand's
    size (w, d, h)."""
    fw, fd = c["footprint_m"]
    dw, dd, dh = c["display_stand"]["size_m"]
    sx = origin.x + fw - SOCKET_FROM_RIGHT_WALL
    sock_y = origin.y + fd - SOCKET_WALL_INSET
    sy = sock_y - c["display_stand"]["gap_to_wall_m"] - dd / 2
    stx = sx + STAND_X_FROM_SOCKET
    edge_x = min(max(sx, stx - dw / 2), stx + dw / 2)
    return {
        "socket": Vector((sx, sock_y, c["socket"]["height_m"])),
        "stand_centre": Vector((stx, sy, 0.0)),
        "stand_back_edge": Vector((edge_x, sy + dd / 2, 0.0)),
        "stand_back_normal": Vector((0.0, 1.0, 0.0)),
        "stand_size": (dw, dd, dh),
    }
