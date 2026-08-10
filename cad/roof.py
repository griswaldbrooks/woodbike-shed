"""Roof section: 13 rafters, front/back fascia, left/right rake boards.

Rafters: 2x6, 15.875" o.c. at x = -2.75..187.75, falling in +Y at the roof
pitch. Built as exact YZ-profile prisms with the audited birdsmouths: front
seat flat on the front double top plate top (heel where the bottom edge
crosses the seat plane, plumb kick at the front wall inner face) and back
seat flat on the back double top plate top out to the back wall outer face
(plumb kick there), plumb end cuts at the audited tail extents. Every roof
number is derived parametrically from the plate solids via
cad.common.roof_ref (seat plane = plate top face; heel/kick = bottom edge x
plate faces), so wall-height edits propagate. Same construction as
scripts/audit_overlaps.py RAFTER and the Onshape build
(scripts/build_members.py).

Rake boards: the same parallelogram profile minus the seats (they run along
the roof overhang edges, bearing on nothing), butting the fascia inner
faces. Fascia: 2x6 x 216" (12" past each side wall), axis-aligned vertical
boards.
"""
from cad.common import M_PER_IN, Audit, place_box, prism_yz, roof_ref

RAFTER = "rafter"
RAKE_BOARDS = ("left rake board", "right rake board")
FASCIA = ("front fascia", "back fascia")


def rafter_profile(ref) -> list:
    """Birdsmouthed rafter YZ profile (inches): plumb front tail -> heel ->
    front seat -> kick -> bottom edge -> back seat -> kick -> plumb back
    tail -> top edge (bottom edge + rafter_off, the audited vertical
    offset)."""
    zb, zf = ref.zbot(ref.tail_f_y), ref.zbot(ref.tail_b_y)
    return [
        (ref.tail_f_y, zb),                        # front tail bottom (plumb)
        (ref.heel_y, ref.front_seat_z),            # heel
        (ref.front_bear_y, ref.front_seat_z),      # front seat
        (ref.front_bear_y, ref.zbot(ref.front_bear_y)),  # front plumb kick
        (ref.back_seat_start_y, ref.back_seat_z),  # bottom edge to back seat
        (ref.back_kick_y, ref.back_seat_z),        # back seat
        (ref.back_kick_y, ref.zbot(ref.back_kick_y)),  # back plumb kick
        (ref.tail_b_y, zf),                        # bottom edge to back tail
        (ref.tail_b_y, zf + ref.rafter_off),       # back tail top (plumb)
        (ref.tail_f_y, zb + ref.rafter_off),       # top edge
    ]


def rake_board_profile(ref) -> list:
    """Full parallelogram between the plumb ends (no seats)."""
    zb, zf = ref.zbot(ref.tail_f_y), ref.zbot(ref.tail_b_y)
    return [
        (ref.tail_f_y, zb),
        (ref.tail_b_y, zf),
        (ref.tail_b_y, zf + ref.rafter_off),
        (ref.tail_f_y, zb + ref.rafter_off),
    ]


def build(audit: Audit):
    ref = roof_ref(audit)
    parts = []
    for spec in audit.group(RAFTER):
        x0 = spec.aabb["lowX"] / M_PER_IN
        x1 = spec.aabb["highX"] / M_PER_IN
        p = prism_yz(rafter_profile(ref), x0, x1)
        p.label = spec.label
        parts.append(p)
    for spec in audit.group(*RAKE_BOARDS):
        x0 = spec.aabb["lowX"] / M_PER_IN
        x1 = spec.aabb["highX"] / M_PER_IN
        p = prism_yz(rake_board_profile(ref), x0, x1)
        p.label = spec.label
        parts.append(p)
    for spec in audit.group(*FASCIA):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
