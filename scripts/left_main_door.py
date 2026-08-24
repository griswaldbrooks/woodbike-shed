#!/usr/bin/env python3
"""One-shot migration: ADD the LEFT rake-wall 64 in double door — the shed's
MAIN (primary pedestrian) door, closest to the garage/access (captain
2026-08-24, firstmate data/shed-guide-depth-pass/
captain-decision-2026-08-24.md). Mirror of the right brewery double that
scripts/depth7ft_2door.py framed: same span (clear 6.5-70.5 on the 77 in
wall), head 84, 6.5 in end studs, same jack/header/cripple construction.
The free-doors study verified the span (winner2 left-door checks) and the
Blender winner-render scout validated the door against the parked jenga
(firstmate data/shed-blender-winner/report.md): end studs PASS, outswing
leaves stay exterior, flank access flagged.

Rewrites scripts/oriented_dims.json and scripts/bboxes.json; the cad/
modules re-derive everything else from those files.

The left wall before this migration (depth7ft_2door.py PHASE A):
  - flat full-height studs at y 0, 15.5, 31.5, 47.5, 63.5 (z 1.5..94.125)
    + the back corner post (x -1.5..0, y 77..80.5);
  - one bottom plate y 0..77;
  - rake studs: four on the DTP top (y 0, 15.5, 31.5, 47.5) + three mitered
    standing on the sill (y 69.5, 73.5, 75.5).

After (mirror of the right wall's PHASE B framing, x -3.5..0):
  - west end stud y 0..1.5 only; studs 15.5/31.5/47.5/63.5 fall inside the
    opening and are replaced by jacks + cripples;
  - jack studs y 5..6.5 and 70.5..72 (z 1.5..84) carry the header;
  - header: two 1.5" plies (inner x -1.5..0, outer x -3.5..-2) spanning
    y 5..72 at z 84..87.5 + the full-width cap z 87.5..89;
  - cripples y 22.5, 38.5, 54.5 (z 89..94.125, under the flat top plate,
    which runs over the opening unchanged) — 16" oc from the opening edge,
    as on the right wall;
  - bottom plates re-cut around the opening: short y 0..6.5, long y
    70.5..77 (both end up 6.5 long — the flagged minimum end studs);
  - rake studs: the mitered sill stud at 69.5 crossed the opening and is
    retired; over the header's back bay the mitered cripples y 65.5/68.5
    stand on the 89 cap (as on the right wall); the back-corner mitered
    studs 73.5/75.5 and the four DTP-top studs stay.

Every new left part is the exact dimensional mirror of its right-wall
counterpart (both walls run along Y, 3.5 thick in X), self-checked below:
nothing new enters the cut list that the right wall does not already order.

Self-check: before touching anything, the current audit data must match the
pre-left-door facts above; then the new geometry is written. Re-running
after migration aborts (idempotency guard).

Usage: ~/.venvs/woodbike-shed/bin/python scripts/left_main_door.py
(from repo root)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

M = 0.0254  # inches -> meters

# --- anchors shared with depth7ft_2door.py (unchanged by this migration) ---
TAN = 24.375 / 65           # roof pitch, 0.375 exactly
SEC = math.hypot(1.0, TAN)
GAP_PERP = 1.5 * SEC        # rake plate underside gap (1.5" plate perp)
Z_B_NEW = 92.625            # back DTP top (bearing line at y 77)
FRONT_BEAR = 121.5          # bearing line at y 0
STUD_TOP_FLAT = 94.125      # flat side-wall stud top
DTP_TOP = 97.125            # side double top plate top
Y_BACK_IN = 77.0

# --- the door (mirror of the right brewery double) --------------------------
LEFT_X = (-3.5, 0.0)
OPEN = (6.5, 70.5)          # clear opening
JACKS = [(5.0, 6.5), (70.5, 72.0)]
HEADER = (5.0, 72.0)
CRIPPLES = [22.5, 38.5, 54.5]          # square, under the flat top plate
RAKE_FLAT = [0.0, 15.5, 31.5, 47.5]    # rake studs on the DTP top (kept)
RAKE_MITRED = [(65.5, 89.0), (68.5, 89.0),   # over the header's back bay
               (73.5, 1.5), (75.5, 1.5)]     # back corner zone (69.5 gone)
FLAT_STUD_KEEP = [0.0]                     # west end stud only
HEADER_Z = (84.0, 87.5)
CAP_Z = (87.5, 89.0)


def zu(y):
    return FRONT_BEAR - TAN * y - GAP_PERP


def plate_bottom(y):
    return max(zu(y), Z_B_NEW)


def main():
    od = json.loads((HERE / "oriented_dims.json").read_text())
    bb = json.loads((HERE / "bboxes.json").read_text())

    def rebuild_index():
        idx = {}
        for p in bb:
            idx.setdefault(p["name"], []).append(p)
        return idx

    bb_by = rebuild_index()

    # idempotency guard
    if any(e["name"] == "left wall headers" for e in od):
        sys.exit("already migrated (left wall headers exist)")

    # --- self-check: the pre-left-door facts this migration assumes --------
    def near(a, b, tol, what):
        if abs(a - b) > tol:
            sys.exit(f"self-check failed: {what}: expected {b:.4f}, "
                     f"audit says {a:.4f}")

    def yset(name, x_lo=None):
        ys = []
        for p in bb_by[name]:
            b = p["bbox_m"]
            if x_lo is not None and abs(b["lowX"] / M - x_lo) > 0.01:
                continue
            ys.append(round(b["lowY"] / M, 3))
        return sorted(ys)

    # 7 ft shell in place
    near(bb_by["back wall bottom plate"][0]["bbox_m"]["lowY"] / M,
         Y_BACK_IN, 0.01, "back wall inner face (7 ft shell)")
    # left wall flat studs + corner post as depth7ft_2door left them
    if yset("left side wall studs", -3.5) != [0.0, 15.5, 31.5, 47.5, 63.5]:
        sys.exit(f"self-check failed: left flat studs "
                 f"{yset('left side wall studs', -3.5)}")
    near(yset("left side wall studs", -1.5)[0], Y_BACK_IN, 0.01,
         "left back corner post")
    bp = bb_by["left side wall bottom plate"][0]["bbox_m"]
    near(bp["lowY"] / M, 0.0, 0.01, "left bottom plate front end")
    near(bp["highY"] / M, Y_BACK_IN, 0.01, "left bottom plate back end")
    # left rake studs: four DTP-top + mitered 69.5/73.5/75.5
    flat = sorted(round(p["bbox_m"]["lowY"] / M, 3) for p in
                  bb_by["left rake wall studs"]
                  if abs(p["bbox_m"]["lowZ"] / M - DTP_TOP) < 0.01)
    mitred = sorted((round(p["bbox_m"]["lowY"] / M, 3),
                     round(p["bbox_m"]["lowZ"] / M, 3)) for p in
                    bb_by["left rake wall studs"]
                    if abs(p["bbox_m"]["lowZ"] / M - DTP_TOP) >= 0.01)
    if flat != RAKE_FLAT or mitred != [(69.5, 1.5), (73.5, 1.5), (75.5, 1.5)]:
        sys.exit(f"self-check failed: left rake studs {flat} / {mitred}")
    # no left door framing yet
    for n in ("left wall headers", "left wall jack studs",
              "left wall cripple studs"):
        if n in bb_by:
            sys.exit(f"self-check failed: '{n}' already present")
    # the right wall facts being mirrored (span/head/cripples)
    if yset("right wall jack studs") != [5.0, 70.5]:
        sys.exit(f"self-check failed: right jacks (mirror source) "
                 f"{yset('right wall jack studs')}")
    rh = bb_by["right wall headers"][0]["bbox_m"]
    near(rh["lowZ"] / M, HEADER_Z[0], 0.01, "right header bottom")
    if yset("right wall cripple studs") != CRIPPLES:
        sys.exit(f"self-check failed: right cripples "
                 f"{yset('right wall cripple studs')}")
    print("self-check OK: pre-left-door 7 ft shell as assumed; right-wall "
          "mirror source verified")

    # --- helpers (same contract as depth7ft_2door.py) ----------------------
    _seq = iter(range(1000))

    def add(name, x0, x1, y0, y1, z0, z1, oriented=None):
        i = next(_seq)
        b = {"lowX": x0 * M, "lowY": y0 * M, "lowZ": z0 * M,
             "highX": x1 * M, "highY": y1 * M, "highZ": z1 * M}
        bb.append({"partId": f"N{i:02d}", "name": name, "bbox_m": b,
                   "dx_m": b["highX"] - b["lowX"],
                   "dy_m": b["highY"] - b["lowY"],
                   "dz_m": b["highZ"] - b["lowZ"]})
        dims = sorted([x1 - x0, y1 - y0, z1 - z0])
        if oriented is not None:
            dims[2] = oriented
        od.append({"name": name, "dx": dims[2], "dy": dims[1],
                   "dz": dims[0]})

    def drop(name):
        bb[:] = [p for p in bb if p["name"] != name]
        od[:] = [e for e in od if e["name"] != name]

    x0, x1 = LEFT_X

    # --- flat studs: keep the west end stud, drop the opening-zone studs ---
    drop("left side wall studs")
    for y0 in FLAT_STUD_KEEP:
        add("left side wall studs", x0, x1, y0, y0 + 1.5, 1.5, STUD_TOP_FLAT)
    add("left side wall studs", -1.5, 0.0, Y_BACK_IN, 80.5, 1.5,
        Z_B_NEW - 3.0)                       # back corner post, unchanged

    # --- jacks / header / cripples (mirror of the right wall) --------------
    for y0, y1 in JACKS:
        add("left wall jack studs", x0, x1, y0, y1, 1.5, HEADER_Z[0])
    # two plies + the full-width cap, as framed on the right wall
    add("left wall headers", -1.5, 0.0, *HEADER, HEADER_Z[0], HEADER_Z[1])
    add("left wall headers", -3.5, -2.0, *HEADER, HEADER_Z[0], HEADER_Z[1])
    add("left wall headers", x0, x1, *HEADER, CAP_Z[0], CAP_Z[1])
    for y0 in CRIPPLES:
        add("left wall cripple studs", x0, x1, y0, y0 + 1.5,
            CAP_Z[1], STUD_TOP_FLAT)

    # --- bottom plates around the opening ----------------------------------
    drop("left side wall bottom plate")
    add("left wall bottom plate short", x0, x1, 0.0, OPEN[0], 0.0, 1.5)
    add("left wall bottom plate long", x0, x1, OPEN[1], Y_BACK_IN, 0.0, 1.5)

    # --- rake studs: 69.5 retired; mitered cripples over the header --------
    drop("left rake wall studs")
    for y0 in RAKE_FLAT:
        add("left rake wall studs", x0, x1, y0, y0 + 1.5, DTP_TOP, zu(y0))
    for y0, z_bot in RAKE_MITRED:
        add("left rake wall studs", x0, x1, y0, y0 + 1.5,
            z_bot, plate_bottom(y0))

    # --- dims mirror check: every new left part matches its right twin -----
    def od_dims(name):
        return sorted(tuple(sorted((e["dx"], e["dy"], e["dz"])))
                      for e in od if e["name"] == name)

    twins = (("left wall jack studs", "right wall jack studs"),
             ("left wall headers", "right wall headers"),
             ("left wall cripple studs", "right wall cripple studs"),
             ("left wall bottom plate short", "right wall bottom plate short"),
             ("left wall bottom plate long", "right wall bottom plate long"),
             ("left rake wall studs", "right rake wall studs"))
    for left, right in twins:
        if od_dims(left) != od_dims(right):
            sys.exit(f"mirror check failed: {left} {od_dims(left)} != "
                     f"{right} {od_dims(right)}")
    print("mirror check OK: every new left part matches its right twin")

    # --- write ---------------------------------------------------------------
    (HERE / "oriented_dims.json").write_text(
        json.dumps(od, indent=2, sort_keys=True) + "\n")
    (HERE / "bboxes.json").write_text(json.dumps(bb, indent=2) + "\n")

    # --- report ---------------------------------------------------------------
    print(f"\nleft main door: clear {OPEN[0]}-{OPEN[1]} head 84 (mirror of "
          f"the right brewery double); jacks 5-6.5 / 70.5-72; header plies "
          f"+ cap 84-89; cripples 22.5/38.5/54.5; mitered cripples "
          f"65.5/68.5 on the 89 cap; sill stud 69.5 retired")
    print("door roles: LEFT double = MAIN entry; front 8 ft barn = wheeled "
          "roll-out; RIGHT double = brewery service")


if __name__ == "__main__":
    main()
