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


# ---- the car interior (v2 layout: the single layout for stills, frames and build.py)
# The v1 set puts the driver's pelvis 0.65 m from the steering wheel (arms 0.59 m: the hands float 0.25 m off the rim) and
# 0.95 m from the glovebox latch (canon reach_from_driver_seat_m 0.75). The v2 layout moves the front seats 0.25 m forward and the
# glovebox 0.10 m toward the dash, which gives wheel 0.40 m ahead of the pelvis (the poses' own default) and a latch 0.75 m
# away horizontally. The v1 layout is retired: stills (preview.py), frames (animate.py) and build.py all use v2 (car_layout() defaults to it).
CAR_V2 = [True]      # kept for compatibility; v2 is the only layout used (nothing switches it off)
CAR_SEAT_SHIFT_V2 = 0.25
CAR_GLOVEBOX_BACK_V2 = 0.10


def car_layout(v2=None):
    """(seat_dy, glovebox_dy): offsets from the v1 seat row (cy + 0.15) and glovebox y (y1 - 0.72)."""
    v2 = CAR_V2[0] if v2 is None else v2
    return (CAR_SEAT_SHIFT_V2, -CAR_GLOVEBOX_BACK_V2) if v2 else (0.0, 0.0)


def insert_shift(ui_assets, cam_to_phone_dist, xv, yv):
    """Lens shift (parallel to the screen, never a tilt) for the 0.30 m text inserts, whose spec centres the screen: moves the frame to
    the named part of it. Single rule for stills (preview.py) and frames (animate.py)."""
    if cam_to_phone_dist >= 0.4:
        return Vector((0, 0, 0))
    ua = set(ui_assets)
    if ua == {"ui.status_bar"}:
        du, dv = 0.012, 0.056
    elif "ui.compose_field" in ua:
        du, dv = 0.0, -0.004
    elif "ui.thread_sent_bubble" in ua:
        du, dv = 0.005, 0.02
    elif "ui.call_screen" in ua:      # SC01_SH030: 0.03 m toward the top edge so the frame runs from just above the status bar to the screen centre
        du, dv = 0.0, 0.03
    else:
        du, dv = 0.0, 0.0
    return xv.normalized() * du + yv.normalized() * dv
