"""Left/right side walls - run along Y between front and back walls.

Axis-aligned studs + plates. The right wall carries jack studs/headers/
cripples for its opening; bottom-plate shorts frame around it.
"""
from cad.common import Audit, place_box

GROUPS = (
    "left side wall studs",
    "left side wall bottom plate",
    "left wall top plate",
    "left wall double top plate",
    "right wall studs",
    "right wall bottom plate long",
    "right wall bottom plate short",
    "right wall top plate",
    "right wall double top plate",
    "right wall jack studs",
    "right wall headers",
    "right wall cripple studs",
)


def build(audit: Audit):
    parts = []
    for spec in audit.group(*GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
