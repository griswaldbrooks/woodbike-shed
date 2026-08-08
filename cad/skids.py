"""Skids section: 4x 4x4x96" skids + 2x 4x4x48" sisters.

The four physical skid boards are UNNAMED in the audit data (see
OUTSTANDING_ISSUES.md: "4 unnamed parts inside composite skids"), so
bboxes.json has no AABBs for them. Placement is inferred from the audited
skid sisters + floor extents: two skid lines under the floor joists, two 96"
boards per line meeting at the mid-span joint the sisters reinforce
(96" + 96" = 192" = floor length, checks out exactly).

TODO(captain): OUTSTANDING_ISSUES.md items "4 unnamed parts inside composite
skids" and "Composite part 3" stay pending - this module models the physical
boards per CUT_LIST.md, not the Onshape composite bodies.
"""
from build123d import Box, Location

from cad.common import IN, M_PER_IN, Audit, CENTER3, place_box

SKID_THICK = 3.5  # inches, 4x4 actual


def build(audit: Audit):
    parts = []
    sisters = audit.group("skid sister")
    rims = audit.group("rim joist")
    x_min = min(r.aabb["lowX"] for r in rims) / M_PER_IN
    x_max = max(r.aabb["highX"] for r in rims) / M_PER_IN

    for s in sisters:
        b = s.aabb
        y_lo, y_hi = b["lowY"] / M_PER_IN, b["highY"] / M_PER_IN
        z_lo = b["lowZ"] / M_PER_IN
        joint_x = (b["lowX"] + b["highX"]) / 2 / M_PER_IN
        for (a, c) in ((x_min, joint_x), (joint_x, x_max)):
            p = (Location(((a + c) / 2 * IN, (y_lo + y_hi) / 2 * IN,
                            (z_lo + SKID_THICK / 2) * IN), (0, 0, 0))
                 * Box((c - a) * IN, (y_hi - y_lo) * IN, SKID_THICK * IN,
                       align=CENTER3))
            p.label = "skid"
            parts.append(p)
    # sisters themselves are audited, plain axis-aligned boxes
    for s in sisters:
        p = place_box(s)
        p.label = s.label
        parts.append(p)
    return parts
