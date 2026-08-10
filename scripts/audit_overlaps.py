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

# Roof re-derived 2026-08-10 for the 92-5/8" pre-cut stud decision
# (scripts/restud_92_5_8.py): the back/left/right wall plate tops dropped
# 97.5 -> 97.125 while every front reference stayed. Same construction as
# the audit data: bearing line = rafter bottom edge = rake plate top edge,
# seats flat at the plate heights.
Z_B = 97.125                        # back wall double top plate top
FRONT_BEAR = 121.5                  # bearing at y=0 (front plate 123 - 1.5)
SLOPE = (FRONT_BEAR - Z_B) / 65.0   # 24.375/65 (was 24/65)
SEC = math.hypot(1.0, SLOPE)        # 1/cos
OFF = 5.5 * SEC                     # rafter AABB top offset (was 5.86283)
HEEL = -1.5 / SLOPE                 # front seat heel (was -4.0625)


def zbot(y):
    return FRONT_BEAR - SLOPE * y


RAFTER = [(-27.5, zbot(-27.5)), (HEEL, 123.0), (0.0, 123.0), (0.0, FRONT_BEAR),
          (65.0, Z_B), (68.5, Z_B), (68.5, zbot(68.5)), (80.5, zbot(80.5)),
          (80.5, zbot(80.5) + OFF), (-27.5, zbot(-27.5) + OFF)]
RAKE_BOARD = [(-27.5, zbot(-27.5)), (80.5, zbot(80.5)),
              (80.5, zbot(80.5) + OFF), (-27.5, zbot(-27.5) + OFF)]
# Rake plate underside = the rake stud top line: stud top edges are driven
# 1.5" below the plate top edge, measured perpendicular to it -> vertical
# gap 1.5*SEC; the line crosses the back plate top at y = (z_us(0)-Z_B)/SLOPE.
Z_US0 = FRONT_BEAR - 1.5 * SEC
RIGHT_RAKE_PLATE = [(65.0, Z_B), (0.0, FRONT_BEAR), (0.0, Z_US0),
                    ((Z_US0 - Z_B) / SLOPE, Z_B)]
LEFT_RAKE_PLATE = RIGHT_RAKE_PLATE


def zu(y):
    return Z_US0 - SLOPE * y


RAKE_STUDS = []
for yc in (0.75, 16.25, 32.25, 48.25):
    y0, y1 = yc - 0.75, yc + 0.75
    RAKE_STUDS.append([(y0, Z_B), (y1, Z_B), (y1, zu(y1)), (y0, zu(y0))])

FASCIA_FRONT = [(-29.0, zbot(-27.5) + OFF - 5.5), (-27.5, zbot(-27.5) + OFF - 5.5),
                (-27.5, zbot(-27.5) + OFF), (-29.0, zbot(-27.5) + OFF)]
FASCIA_BACK = [(80.5, zbot(80.5) + OFF - 5.5), (82.0, zbot(80.5) + OFF - 5.5),
               (82.0, zbot(80.5) + OFF), (80.5, zbot(80.5) + OFF)]


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
    # are four distinct parts sharing four profiles matched by y-position)
    prof = {
        "rafter": RAFTER,
        "left rake board": RAKE_BOARD,
        "right rake board": RAKE_BOARD,
        "left rake wall top plate": LEFT_RAKE_PLATE,
        "right rake wall top plate": RIGHT_RAKE_PLATE,
        "front fascia": FASCIA_FRONT,
        "back fascia": FASCIA_BACK,
    }
    stud_profiles = {round(yc, 2): q for yc, q in
                     zip((0.75, 16.25, 32.25, 48.25), RAKE_STUDS)}
    for p in parts:
        if p["name"] in prof:
            p["poly"] = prof[p["name"]]
        elif p["name"] in ("left rake wall studs", "right rake wall studs"):
            yc = round(sum(q[0] for q in p["poly"]) / 4, 2)
            p["poly"] = stud_profiles[yc]

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
