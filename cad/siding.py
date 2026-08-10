"""Finish siding: horizontal lap boards, one course stack per wall.

Product: 1x8 drop siding (3/4" x 7-1/2" actual), 7" exposure - successive
courses nest via a 1/2" x 3/8" rabbet/tongue so the wall stays in ONE plane
(no bevel drift) and courses touch without interfering. Front/back courses
are Dolly-Varden profiles in the thickness plane extruded along the wall
(prism_yz); side-wall full courses are the same profile turned 90 deg
(prism_xz). Where the roof rake crosses a side-wall course, that course is a
full-thickness (y,z) outline prism with a sloped top edge butting the tongue
top of the course below - the frieze and casings (trim.py) cover every joint.

Heights all derive from cad.common.finish_layout (audit bboxes + roof_ref);
only the product dims below are constants. Wall-height edits propagate.
"""
from cad.common import TRIM_T, Audit, finish_layout, prism_xz, prism_yz

SIDING_T = 0.75     # 1x8 actual thickness
BOARD_W = 7.5       # 1x8 actual width
EXPOSURE = 7.0      # lap = BOARD_W - EXPOSURE
RAB = 0.375         # rabbet/tongue depth
Z_START = 0.0       # bottom course tucks behind the skirt board (trim.py)

LABELS = {"front": "finish siding front", "back": "finish siding back",
          "left": "finish siding left", "right": "finish siding right"}


def _course_profile(z: float, first: bool, top: float | None):
    """Dolly-Varden lap profile in (u, z), u=0 at the wall plane, -SIDING_T
    outer. first: square bottom (no rabbet); top: square top at z=top
    (no tongue), else tongue nested under the next course."""
    zt = z + BOARD_W if top is None else top
    # simple-polygon walk: back bottom -> up the back -> across the top ->
    # down the outer face -> across the bottom
    pts = [(0.0, z if first else z + 0.5), (0.0, zt)]
    if top is None:
        pts += [(-RAB, zt), (-RAB, zt - 0.5), (-SIDING_T, zt - 0.5)]
    else:
        pts.append((-SIDING_T, zt))
    pts.append((-SIDING_T, z))
    if not first:
        pts += [(-RAB, z), (-RAB, z + 0.5)]
    return pts


def _segments(x0, x1, opens, z):
    """Wall-length segments of a course: full width above the heads, piers
    between/around door openings below."""
    if not opens or z >= min(h for _, _, h in opens):
        return [(x0, x1)]
    xs = [x0] + [c for o0, o1, _ in opens for c in (o0, o1)] + [x1]
    return [(a, b_) for a, b_ in zip(xs[::2], xs[1::2]) if b_ - a > 0.5]


def _front_back(L, wall):
    """Courses along X; door openings cut the courses below the head line."""
    parts = []
    u2y = (lambda u: L["f"] + u) if wall == "front" else (lambda u: L["b"] - u)
    # back: one tuck line shared with the frieze, clear of the rafter tails
    ztop = L["front_top"] if wall == "front" \
        else L["back_top_at"](SIDING_T + TRIM_T)
    opens = L["front_open"] if wall == "front" else []
    i = 0
    while True:
        z = Z_START + EXPOSURE * i
        tongue_top = z + BOARD_W
        is_top = tongue_top >= ztop
        for a, b_ in _segments(L["l"], L["r"], opens, z):
            p = prism_yz([(u2y(u), zz) for u, zz in
                          _course_profile(z, i == 0, ztop if is_top else None)],
                         a, b_)
            p.label = LABELS[wall]
            parts.append(p)
        if is_top:
            return parts
        i += 1


def _rake_y(L, z):
    """y where the side-top rake line equals z (None if past the front)."""
    ref = L["ref"]
    y = ref.front_bear_y + (ref.front_bear_z - (z - 1.0)) / ref.slope
    return y if L["f"] <= y <= L["b"] else None


def _side(L, wall):
    """Courses along Y; the rake clips the top courses' length and edge."""
    parts = []
    x0 = L["l"] - SIDING_T if wall == "left" else L["r"]
    ztop = L["side_top"]
    yf, yb = L["f"], L["b"]
    opens = L["right_open"] if wall == "right" else []
    i = 0
    z = Z_START
    while z + BOARD_W < ztop(yb):          # full courses under the rake
        for a, b_ in _segments(yf, yb, opens, z):
            u2x = (lambda u: L["l"] + u) if wall == "left" \
                else (lambda u: L["r"] - u)
            p = prism_xz([(u2x(u), zz) for u, zz in
                          _course_profile(z, i == 0, None)], a, b_)
            p.label = LABELS[wall]
            parts.append(p)
        z += EXPOSURE
        i += 1
    if i:
        z += BOARD_W - EXPOSURE   # rake courses butt the last tongue top
    # rake-crossing courses: full-thickness outlines, top edge =
    # min(own width, rake line)
    while z < ztop(yf):
        tt = z + BOARD_W
        ytip = _rake_y(L, z)               # rake crosses the bottom edge
        yk = _rake_y(L, tt)                # ... and the top edge
        top_f = min(tt, ztop(yf))
        pts = [(yf, z)]
        if ytip is not None:               # tip triangle at the back
            pts.append((ytip, z))
        else:
            pts.append((yb, min(tt, ztop(yb))))
        if yk is not None:
            pts += [(yk, tt), (yf, tt)]
        else:
            pts.append((yf, top_f))
        p = prism_yz(pts, x0, x0 + SIDING_T)
        p.label = LABELS[wall]
        parts.append(p)
        z = tt
    return parts


def build(audit: Audit):
    L = finish_layout(audit)
    return (_front_back(L, "front") + _front_back(L, "back")
            + _side(L, "left") + _side(L, "right"))
