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


# ------------------------------------------------------------------------------------------ ray clearance
# One shared implementation of "hide what stands between the lens and what the shot is about", used by the static
# assembly (preview.render_shot) and by every animated frame (animate._FrameRig.apply). Pure python on tuples: the callers
# supply the ray cast and the hide action, so the rule is unit tested without bpy.
CLIP_START = 0.02      # camera clip_start set by preview/build (metres)
FOCUS_EPS = 0.005      # focus never closer than clip_start + this: inside it the lens could not see the plane anyway
RAY_MARGIN = 0.03      # the ray stops this far short of its goal so the goal's own surface is not a blocker
RAY_STEP = 0.01        # after a hit the ray restarts this far beyond it
MAX_HOPS = 10          # blockers hidden per goal, at most


def focus_clamp(dist, clip_start=CLIP_START):
    """Focus distance for a DOF camera: the real lens-to-target distance, but never inside the clip plane. The old 0.1 m
    floor put the focus plane behind a phone screen only 0.083 m from the lens (SC03_SH060), blurring the very thing in focus."""
    return max(float(dist), clip_start + FOCUS_EPS)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _len(v):
    return (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) ** 0.5


def phone_goals(phone, xv, yv, half_w=0.034, half_h=0.072):
    """3x3 grid of points over a phone screen (corners, edge midpoints, centre): `phone` centre, xv/yv unit axes (tuples)."""
    return [tuple(phone[k] + xv[k] * a * half_w + yv[k] * b * half_h for k in range(3))
            for a in (-1, 0, 1) for b in (-1, 0, 1)]


def point_goals(target, spread=0.05):
    """Four points around a small prop (the crank, a desk phone) plus its centre."""
    return [(target[0] + a * spread, target[1] + b * spread, target[2]) for a in (-1, 1) for b in (-1, 1)] + [tuple(target)]


def clear_sight_lines(cast, origin, goals, hideable, hide, min_dist=0.05):
    """Ray-cast from `origin` to every goal; each blocker for which hideable(handle) is true is hidden via hide(handle) and the
    ray resumes beyond it (up to MAX_HOPS per goal). Blockers that cannot be hidden are passed through, never hit twice.
    cast(org, unit_dir, dist) -> None | (hit_point, handle). Returns the handles hidden, in order."""
    hidden = []
    for goal in goals:
        org = tuple(origin)
        for _ in range(MAX_HOPS):
            d = _sub(goal, org)
            dist = _len(d)
            if dist < min_dist:
                break
            u = tuple(c / dist for c in d)
            hit = cast(org, u, dist - RAY_MARGIN)
            if hit is None:
                break
            loc, handle = hit
            if hideable(handle):
                hide(handle)
                hidden.append(handle)
            org = tuple(loc[k] + u[k] * RAY_STEP for k in range(3))
    return hidden
