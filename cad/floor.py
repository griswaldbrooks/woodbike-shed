"""Floor section: rim joists, floor joists, OSB subfloor.

All axis-aligned; placements straight from bboxes.json. Deck top is z=0
(OSB top), joist tops at z=-0.75", rims outside the joist ends.
"""
from cad.common import Audit, place_box

GROUPS = ("rim joist", "floor joist", "sub floor osb")


def build(audit: Audit):
    parts = []
    for spec in audit.group(*GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
