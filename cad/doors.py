"""Finish doors: board-and-batten barn doors over every framed opening.

Front wall: single leaf over the 36" opening + center double over the 72";
right wall: single over its 36" opening (matches the captain's reference
photo and the skin renders). Each leaf = vertical 1x6 planks edge-to-edge
with a 1x4 perimeter frame (stiles + rails) on the outer face; leaves hang
on the casing face (one layer proud of the trim) where strap hinges would
bear. Hardware is NOT modeled - strap hinges/latches are line items in
order_list_finish.csv only.

Leaf extents derive from the clear openings (finish_layout); planks are
ripped to fit (n = ceil(width/5.5)), as on site.
"""
import math

from cad.common import Audit, box_at, finish_layout
from cad.trim import TRIM_T

PLANK_W = 5.5     # 1x6 actual
FRAME_W = 3.5     # 1x4 actual
OVERLAP = 1.5     # leaf bearing onto each jamb casing
GAP = 0.25        # double-leaf meeting gap; head clearance
Z0 = 1.0          # leaf bottom, just above the skirt top


def _leaf(parts, L, wall, a0, a1):
    """One leaf on `wall` spanning a0..a1 on the wall axis."""
    head = (L["front_open"] if wall == "front" else L["right_open"])
    zt = min(h for _, _, h in head) - GAP
    o = TRIM_T + 0.75  # trim outer face offset from the wall plane
    if wall == "front":
        p_lo, p_hi = L["f"] - o - 0.75, L["f"] - o          # plank layer
        f_lo, f_hi = p_lo - 0.75, p_lo                      # frame layer
        box_p = lambda l, a, b, z0, z1: box_at(l, a, b, p_lo, p_hi, z0, z1)
        box_f = lambda l, a, b, z0, z1: box_at(l, a, b, f_lo, f_hi, z0, z1)
    else:
        p_lo, p_hi = L["r"] + o, L["r"] + o + 0.75
        f_lo, f_hi = p_hi, p_hi + 0.75
        box_p = lambda l, a, b, z0, z1: box_at(l, p_lo, p_hi, a, b, z0, z1)
        box_f = lambda l, a, b, z0, z1: box_at(l, f_lo, f_hi, a, b, z0, z1)

    w = a1 - a0
    n = math.ceil(w / PLANK_W)
    for k in range(n):
        parts.append(box_p("finish door planks", a0 + k * w / n,
                           a0 + (k + 1) * w / n, Z0, zt))
    parts.append(box_f("finish door rails", a0, a0 + FRAME_W, Z0, zt))
    parts.append(box_f("finish door rails", a1 - FRAME_W, a1, Z0, zt))
    parts.append(box_f("finish door rails", a0 + FRAME_W, a1 - FRAME_W,
                       Z0, Z0 + FRAME_W))
    parts.append(box_f("finish door rails", a0 + FRAME_W, a1 - FRAME_W,
                       zt - FRAME_W, zt))


def build(audit: Audit):
    L = finish_layout(audit)
    parts = []
    for o0, o1, _hz in L["front_open"]:
        if o1 - o0 > 48:                     # center double
            mid = (o0 + o1) / 2
            _leaf(parts, L, "front", o0 - OVERLAP, mid - GAP / 2)
            _leaf(parts, L, "front", mid + GAP / 2, o1 + OVERLAP)
        else:
            _leaf(parts, L, "front", o0 - OVERLAP, o1 + OVERLAP)
    for o0, o1, _hz in L["right_open"]:
        _leaf(parts, L, "right", o0 - OVERLAP, o1 + OVERLAP)
    return parts
