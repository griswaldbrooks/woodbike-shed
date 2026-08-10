"""Front wall (tall, 10') - runs along X at the low-Y edge.

King studs (1x 120" + 8x 118.5"), single 192" plates, door
headers/jacks/cripples. All axis-aligned; placements from bboxes.json.

Framing only here (the cut-list scope); the doors/siding/trim that close
these openings live in cad/doors.py / cad/siding.py / cad/trim.py on their
own order list (resolved captain decision 2026-08-10).
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
