"""Back wall (low, 8') - runs along X at the high-Y edge.

13 studs at 93", single 192" plates + the 185" double-top short.
Axis-aligned.
"""
from cad.common import Audit, place_box

GROUPS = (
    "back wall studs",
    "back wall bottom plate",
    "back wall top plate",
    "back wall double top plate short",
)


def build(audit: Audit):
    parts = []
    for spec in audit.group(*GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
