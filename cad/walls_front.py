"""Front wall (tall, 10') - runs along X at the low-Y edge.

Studs 118.5", plates, door headers/jacks/cripples. All axis-aligned;
placements from bboxes.json.

TODO(captain): door/siding/trim decisions stay pending (ship orders) - the
framing below is what exists in the cut list today; no openings are modeled
beyond the cripple/jack/header members already present.
"""
from cad.common import Audit, place_box

GROUPS = (
    "front wall studs",
    "front wall bottom plate long",
    "front wall bottom plate short",
    "front wall top plate",
    "front wall double top plate long",
    "front wall double top plate short",
    "front wall header long",
    "front wall header long cap",
    "front wall header short",
    "front wall jack studs",
    "front wall cripples normal door",
    "front wall cripples wide door",
)


def build(audit: Audit):
    parts = []
    for spec in audit.group(*GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
