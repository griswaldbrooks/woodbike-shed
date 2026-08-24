#!/usr/bin/env python3
"""Full pairwise overlap audit of the woodbike-shed model.

Every part is represented as an X-interval plus a YZ profile polygon:
axis-aligned parts use their world bbox rectangle; sloped members (rafters,
rake boards, rake plates, rake studs, fascia) use their exact construction
profiles. Intersection volume = X-overlap * clipped-polygon area, so touching
(0-volume) contacts are not flagged.

Usage: python3 audit_overlaps.py   (reads scripts/bboxes.json)
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
M = 39.3700787
EPS_A = 1e-4   # in^2 profile-area noise floor
EPS_V = 0.01   # in^3 report threshold

# Roof re-derived 2026-08-23 for the 7 ft depth + 2-door plan
# (scripts/depth7ft_2door.py): the back wall moved y 65..68.5 -> 77..80.5
# and its plate tops dropped to 92.625 (the restud pitch 24.375/65 is
# exactly the 7 ft pitch 28.875/77, so the slope is unchanged); every front
# reference stayed. Same construction as the audit data: bearing line =
# rafter bottom edge = rake plate top edge, seats flat at the plate heights.
Z_B = 92.625                        # back wall double top plate top
FRONT_BEAR = 121.5                  # bearing at y=0 (front plate 123 - 1.5)
SLOPE = (FRONT_BEAR - Z_B) / 77.0   # 28.875/77 = 24.375/65
SEC = math.hypot(1.0, SLOPE)        # 1/cos
OFF = 5.5 * SEC                     # rafter AABB top offset
HEEL = -1.5 / SLOPE                 # front seat heel
TAIL_F, TAIL_B = -27.5, 92.5        # rafter tails (24"/12" overhangs)


def zbot(y):
    return FRONT_BEAR - SLOPE * y


RAFTER = [(TAIL_F, zbot(TAIL_F)), (HEEL, 123.0), (0.0, 123.0),
          (0.0, FRONT_BEAR), (77.0, Z_B), (80.5, Z_B),
          (80.5, zbot(80.5)), (TAIL_B, zbot(TAIL_B)),
          (TAIL_B, zbot(TAIL_B) + OFF), (TAIL_F, zbot(TAIL_F) + OFF)]
RAKE_BOARD = [(TAIL_F, zbot(TAIL_F)), (TAIL_B, zbot(TAIL_B)),
              (TAIL_B, zbot(TAIL_B) + OFF), (TAIL_F, zbot(TAIL_F) + OFF)]
# Rake plate underside = the rake stud top line: stud top edges are driven
# 1.5" below the plate top edge, measured perpendicular to it -> vertical
# gap 1.5*SEC; the underside crosses the back plate top at the seat line,
# and the plate bottom runs flat at Z_B from there to the back wall.
Z_US0 = FRONT_BEAR - 1.5 * SEC
Y_SEAT = (Z_US0 - Z_B) / SLOPE
RIGHT_RAKE_PLATE = [(77.0, Z_B), (0.0, FRONT_BEAR), (0.0, Z_US0),
                    (Y_SEAT, Z_B)]
LEFT_RAKE_PLATE = RIGHT_RAKE_PLATE


def zu(y):
    return Z_US0 - SLOPE * y


def rake_stud_poly(y0, y1, z_bot):
    """Rake/gable stud: flat bottom on its bearing (audited bbox lowZ),
    top mitered to the plate bottom (underside or the flat seat)."""
    top = lambda y: max(zu(y), Z_B)
    return [(y0, z_bot), (y1, z_bot), (y1, top(y1)), (y0, top(y0))]


FASCIA_FRONT = [(-29.0, zbot(TAIL_F) + OFF - 5.5),
                (-27.5, zbot(TAIL_F) + OFF - 5.5),
                (-27.5, zbot(TAIL_F) + OFF), (-29.0, zbot(TAIL_F) + OFF)]
FASCIA_BACK = [(TAIL_B, zbot(TAIL_B) + OFF - 5.5),
               (TAIL_B + 1.5, zbot(TAIL_B) + OFF - 5.5),
               (TAIL_B + 1.5, zbot(TAIL_B) + OFF), (TAIL_B, zbot(TAIL_B) + OFF)]


def zspan(poly, y):
    """(zlo, zhi) of a vertically-convex polygon at ordinate y."""
    zs = []
    n = len(poly)
    for i in range(n):
        y1, z1 = poly[i]
        y2, z2 = poly[(i + 1) % n]
        if (y1 <= y <= y2) or (y2 <= y <= y1):
            if y2 == y1:
                continue
            t = (y - y1) / (y2 - y1)
            zs.append(z1 + t * (z2 - z1))
    if not zs:
        return None
    return (min(zs), max(zs))


def overlap_area(a, b):
    """Area of intersection of two vertically-convex polygons.
    Midpoint sampling on the vertex-ordinate breakpoints; exact for
    piecewise-linear integrands up to crossing kinks (dense K keeps any
    error far below the report threshold)."""
    ys = sorted({p[0] for p in a} | {p[0] for p in b})
    if len(ys) < 2:
        return 0.0
    total = 0.0
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        dy = y1 - y0
        if dy < 1e-9:
            continue
        K = 16
        for k in range(K):
            y = y0 + dy * (k + 0.5) / K
            sa, sb = zspan(a, y), zspan(b, y)
            if sa is None or sb is None:
                continue
            f = max(0.0, min(sa[1], sb[1]) - max(sa[0], sb[0]))
            total += f * dy / K
    return total


def main():
    bboxes = json.loads((HERE / "bboxes.json").read_text())
    parts = []
    for r in bboxes:
        name = r["name"]
        bb = r["bbox_m"]
        x0, x1 = bb["lowX"] * M, bb["highX"] * M
        y0, y1 = bb["lowY"] * M, bb["highY"] * M
        z0, z1 = bb["lowZ"] * M, bb["highZ"] * M
        parts.append({"name": name, "x": (x0, x1),
                      "poly": ([(y0, z0), (y1, z0), (y1, z1), (y0, z1)])})

    # exact profiles override the bbox rectangle (keyed by name; rake studs
    # are built from their own bbox: bottom on the audited bearing, top
    # mitered to the plate bottom)
    prof = {
        "rafter": RAFTER,
        "left rake board": RAKE_BOARD,
        "right rake board": RAKE_BOARD,
        "left rake wall top plate": LEFT_RAKE_PLATE,
        "right rake wall top plate": RIGHT_RAKE_PLATE,
        "front fascia": FASCIA_FRONT,
        "back fascia": FASCIA_BACK,
    }
    for p in parts:
        if p["name"] in prof:
            p["poly"] = prof[p["name"]]
        elif p["name"] in ("left rake wall studs", "right rake wall studs"):
            (y0, z0), (y1, _) = p["poly"][0], p["poly"][1]
            p["poly"] = rake_stud_poly(y0, y1, z0)

    hits = []
    n = len(parts)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = parts[i], parts[j]
            xo = min(a["x"][1], b["x"][1]) - max(a["x"][0], b["x"][0])
            if xo <= 1e-6:
                continue
            # quick bbox y/z reject
            ay = [q[0] for q in a["poly"]]
            by = [q[0] for q in b["poly"]]
            az = [q[1] for q in a["poly"]]
            bz = [q[1] for q in b["poly"]]
            if max(ay) < min(by) or max(by) < min(ay):
                continue
            if max(az) < min(bz) or max(bz) < min(az):
                continue
            ar = overlap_area(a["poly"], b["poly"])
            if ar > EPS_A:
                vol = ar * xo
                if vol > EPS_V:
                    hits.append((vol, a["name"], b["name"]))

    hits.sort(reverse=True)
    print(f"{len(hits)} overlapping pairs (vol > {EPS_V} in^3):")
    for vol, an, bn in hits:
        print(f"  {vol:9.3f} in^3  {an}  x  {bn}")
    if not hits:
        print("  none")


if __name__ == "__main__":
    main()
