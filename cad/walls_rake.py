"""Left/right rake walls - the gable-end infill under the roof edge.

Stepped studs (4 unique heights per side) + the sloped top plate that
carries the rake board. Plate is tilted at the roof pitch (solved from the
rafters' audit AABBs; equals the documented 24.375/65 slope).

Note: the plate's audited world AABB has z-extent = exactly the 24-3/8"
rise, which a plain rectangular box at pitch over-states by ~1.4" (the real
part's end cuts are not captured in the audit data). verify.py allows a
wider tolerance for these two plates; modeled as rectangular stock per
CUT_LIST.md.
"""
from cad.common import Audit, place_box, place_slope_y

STUD_GROUPS = ("left rake wall studs", "right rake wall studs")
PLATE_GROUPS = ("left rake wall top plate", "right rake wall top plate")


def build(audit: Audit):
    parts = []
    for spec in audit.group(*STUD_GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    for spec in audit.group(*PLATE_GROUPS):
        # 2x4 on edge: 3.5" across the wall (X), 1.5" thick, length along slope
        p = place_slope_y(spec, x_dim=3.5, z_dim=1.5, pitch_deg=audit.pitch_deg)
        p.label = spec.label
        parts.append(p)
    return parts
