"""Left/right rake walls - the gable-end infill under the roof edge.

Stepped studs (4 unique heights per side) + the sloped top plate that
carries the rake board. Both are exact YZ-profile prisms derived
parametrically from the plate solids (cad.common.roof_ref):

- Plate: top edge = the bearing line; plumb nose trimmed at the front wall
  inner face; underside 1 plate-thickness (perpendicular) below the top
  edge; flat seat on the back/side double top plate top where the underside
  meets it (the audited RIGHT_RAKE_PLATE construction, incl. the nose trims
  recorded in MANUAL_COMPLETION.md "Rake-plate noses").
- Studs: bottom on their side-wall double top plate top, top edge mitered
  to the plate underside (the constraint_pilot DISTANCE constraint), width
  from the audited AABB.
"""
from cad.common import M_PER_IN, Audit, prism_yz, roof_ref

STUD_GROUPS = ("left rake wall studs", "right rake wall studs")
SIDE_PLATE_FOR = {"left rake wall studs": "left wall double top plate",
                  "right rake wall studs": "right wall double top plate"}


def plate_profile(ref) -> list:
    """Trimmed rake plate YZ profile (inches), back seat -> front top edge
    -> plumb nose -> underside -> flat seat on the back plate top."""
    y_seat = ref.front_bear_y + (ref.front_bear_z - ref.plate_thick * ref.sec
                                 - ref.back_seat_z) / ref.slope
    return [
        (ref.back_seat_start_y, ref.back_seat_z),
        (ref.front_bear_y, ref.zbot(ref.front_bear_y)),   # top edge to nose
        (ref.front_bear_y, ref.zu(ref.front_bear_y)),     # plumb nose
        (y_seat, ref.back_seat_z),                        # underside
    ]


def stud_profile(ref, z_bot: float, y0: float, y1: float) -> list:
    """Rake stud YZ profile (inches): flat bottom on the side double top
    plate top, top edge mitered to the rake plate underside."""
    return [
        (y0, z_bot), (y1, z_bot),
        (y1, ref.zu(y1)), (y0, ref.zu(y0)),
    ]


def build(audit: Audit):
    ref = roof_ref(audit)
    parts = []
    for group in STUD_GROUPS:
        z_bot = audit.specs[SIDE_PLATE_FOR[group]][0].aabb["highZ"] / M_PER_IN
        for spec in audit.group(group):
            b = spec.aabb
            p = prism_yz(stud_profile(ref, z_bot,
                                      b["lowY"] / M_PER_IN,
                                      b["highY"] / M_PER_IN),
                         b["lowX"] / M_PER_IN, b["highX"] / M_PER_IN)
            p.label = spec.label
            parts.append(p)
    for spec in audit.group("left rake wall top plate",
                            "right rake wall top plate"):
        b = spec.aabb
        p = prism_yz(plate_profile(ref), b["lowX"] / M_PER_IN,
                     b["highX"] / M_PER_IN)
        p.label = spec.label
        parts.append(p)
    return parts
