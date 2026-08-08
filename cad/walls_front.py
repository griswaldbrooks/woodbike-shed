"""Front wall (tall, 10') - runs along X at the low-Y edge.

King studs (1x 120" + 8x 118.5"), single 192" plates, door
headers/jacks/cripples. All axis-aligned; placements from bboxes.json.

TODO(captain): door/siding/trim decisions stay pending (ship orders) - the
framing below is what exists in the cut list today; no openings are modeled
beyond the cripple/jack/header members already present.
"""
from cad.common import Audit, place_box

GROUPS = (
    "front wall king studs",
    "front wall bottom plate",
    "front wall top plate",
    "front wall double top plate",
    "front wall jack studs",
    "front wall headers",
    "front wall cripple studs",
)


def build(audit: Audit):
    parts = []
    for spec in audit.group(*GROUPS):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
