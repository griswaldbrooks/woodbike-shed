"""Left/right side walls - run along Y between front and back walls.

Axis-aligned studs + plates. Both rake walls carry jack studs/headers/
cripples for their 64 in doubles (left = main entry, captain 2026-08-24;
right = brewery service); bottom-plate shorts/longs frame around them.
"""
from cad.common import Audit, place_box

GROUPS = (
    "left side wall studs",
    "left wall bottom plate long",
    "left wall bottom plate short",
    "left wall top plate",
    "left wall double top plate",
    "left wall jack studs",
    "left wall headers",
    "left wall cripple studs",
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
