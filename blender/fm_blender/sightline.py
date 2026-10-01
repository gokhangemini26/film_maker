"""Pure-python (no bpy) sight-line rules for the preview builder, so they can be unit tested.

Wall rule: an interior set piece that is a thin slab (a wall, ceiling or floor) is hidden for a shot when the lens sits
outside it - on the far side of the slab plane from every subject point - and in front of its face, laterally. This is
the "wild back wall for reverse shots" the SC03 camera canon allows (camera.geography.sc03 reverse wild_piece); it is
general and never keyed on a shot id. Pieces whose box contains the lens are handled separately by the cull pass."""

THIN_MAX = 0.25      # slab thickness limit, metres
BROAD_MIN = 1.0      # both other extents at least this
LATERAL = 0.3        # lens may sit this far past the slab's edge and still count as "behind" it


def slab_axis(lo, hi):
    """Index of the thin axis if the box is a wall-like slab, else None."""
    ext = [hi[k] - lo[k] for k in range(3)]
    a = min(range(3), key=lambda k: ext[k])
    others = [ext[k] for k in range(3) if k != a]
    return a if ext[a] <= THIN_MAX and all(e >= BROAD_MIN for e in others) else None


def lens_outside_slab(lo, hi, lens, subject_pts, margin=0.03):
    """True when the lens is outside slab (lo, hi) on one side and every subject point is on the other side."""
    a = slab_axis(lo, hi)
    if a is None or not subject_pts:
        return False
    c = (lo[a] + hi[a]) / 2.0
    half = (hi[a] - lo[a]) / 2.0
    d = lens[a] - c
    if abs(d) <= half + margin:          # lens inside the slab: the contain-cull pass owns that case
        return False
    side = 1 if d > 0 else -1
    if any((p[a] - c) * side >= 0 for p in subject_pts):
        return False                     # some subject point is on the lens side: the wall is behind the subject
    for k in range(3):
        if k != a and not (lo[k] - LATERAL <= lens[k] <= hi[k] + LATERAL):
            return False
    return True


def walls_to_hide(boxes, lens, subject_pts):
    """boxes: {name: (lo, hi)}. Names of slabs the lens is outside of, relative to the subject."""
    return [n for n, (lo, hi) in boxes.items() if lens_outside_slab(lo, hi, lens, subject_pts)]
