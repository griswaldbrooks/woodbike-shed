#!/usr/bin/env python3
"""One-shot migration: 93" studs -> 92-5/8" pre-cut studs (captain's
2026-08-10 decision, woodbike-shed-design-calls-decisions.md).

The back, left, and right walls switch to standard 92-5/8" pre-cut studs;
their plate stacks drop 3/8" (wall height 97.5" -> 97.125"). The front wall
is untouched, so the roof plane re-derives about the unchanged front
reference. This script rewrites scripts/oriented_dims.json and
scripts/bboxes.json accordingly. Everything below is re-derived from the
documented constraint chain (MANUAL_COMPLETION.md "Geometry reference" +
scripts/constraint_pilot/), not eyeballed:

  Anchors (inches, Z up):
    Z_F      = 123.0   front wall double top plate top      (unchanged)
    FRONT_BEAR = 121.5 rake plate / rafter bearing at y=0   (unchanged,
                        = Z_F - 1.5" front plate thickness)
    Z_B      = 97.5 -> 97.125   back/left/right wall double top plate top
    RUN      = 65.0    front-to-back wall bearing spacing   (unchanged)

  Derived, as a function of Z_B:
    pitch    tan t = (FRONT_BEAR - Z_B) / RUN        (24/65 -> 24.375/65)
    bearing line  z(y) = FRONT_BEAR - y tan t        (rafter bottom edge /
                             rake plate top edge; seats at the plate heights)
    rafter   bottom edge = bearing line, plumb ends at y=-27.5/80.5 (24"/12"
             overhangs off the wall outer faces, unchanged); front seat flat
             at Z_F with heel at y = -1.5/tan t; back seat flat at Z_B over
             y=65..68.5; depth envelope OFF = 5.5/cos t above the bottom edge
             (the audited AABB top relation, 5.86283" before the change);
             oriented length = 108/cos t (top edge between plumb cuts)
    rake plate  length = RUN/cos t; world AABB z = Z_B .. FRONT_BEAR
             (extent = the rise, per cad/walls_rake.py)
    rake studs  bottom on the side-wall double top plate (Z_B), mitered to
             the plate underside: top edge driven 1.5" below the plate top
             edge measured perpendicular to it (the constraint_pilot
             DISTANCE constraint) -> vertical gap 1.5/cos t; stud k's top
             corner is at its front (low-y) face y0_k:
                 top_k = FRONT_BEAR - y0_k tan t - 1.5/cos t
                 len_k = top_k - Z_B
    right wall cripple studs  bottom fixed at 89" (the 1.5" gap above the
             87.5" headers is a captain's modeling quirk, unchanged), top
             fitted under the right wall top plate bottom = Z_B - 3":
                 len = Z_B - 3 - 89        (5.5" -> 5.125")
    fascia   tops flush with the rafter AABB top at each end:
             highZ = bottom edge(end) + OFF, lowZ = highZ - 5.5

Self-check: before touching anything, the same formulas run with the OLD
constants must reproduce the current audit data (they do, within the
audited parts' ~0.2 mm solver/audit noise); then the NEW constants are
applied. Re-running after migration aborts (idempotency guard).

Usage: .venv/bin/python scripts/restud_92_5_8.py   (from repo root)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent

# --- fixed anchors ---------------------------------------------------------
Z_F = 123.0            # front wall double top plate top (untouched wall)
FRONT_BEAR = Z_F - 1.5  # rake plate / rafter bearing at y=0
RUN = 65.0             # front-to-back wall bearing spacing
Y_STUD_FRONT = (0.0, 15.5, 31.5, 47.5)   # rake stud front faces
Y_END = (-27.5, 80.5)  # rafter plumb ends (24"/12" overhangs, unchanged)
DEPTH = 5.5            # 2x6 depth
GAP = 1.5              # rake stud top edge -> plate top edge, perp distance
M = 0.0254             # inches -> meters

OLD_ZB, NEW_ZB = 97.5, 97.125   # wall height drops 3/8"
OLD_STUD, NEW_STUD = 93.0, 92.625
CRIPPLE_BOT = 89.0              # right wall cripple bottoms (unchanged)
STUD_WALLS = ("back wall studs", "left side wall studs", "right wall studs")
PLATES_DOWN = ("back wall top plate", "back wall double top plate short",
               "left wall top plate", "left wall double top plate",
               "right wall top plate", "right wall double top plate")
DROP_M = (OLD_STUD - NEW_STUD) * M   # 0.009525 m


def roof(z_b):
    """All roof/rake geometry as a function of the low-wall plate height."""
    tan_t = (FRONT_BEAR - z_b) / RUN
    sec = math.hypot(1.0, tan_t)          # 1/cos
    bottom = lambda y: FRONT_BEAR - y * tan_t
    return {
        "tan": tan_t, "sec": sec,
        "rise": FRONT_BEAR - z_b,
        "off": DEPTH * sec,                        # rafter AABB top offset
        "rafter_len": (Y_END[1] - Y_END[0]) * sec,
        "rake_plate_len": RUN * sec,
        "heel": -GAP / tan_t,                      # front seat heel
        "bottom": bottom,
        "stud_top": [FRONT_BEAR - y0 * tan_t - GAP * sec
                     for y0 in Y_STUD_FRONT],
    }


def main():
    od = json.loads((HERE / "oriented_dims.json").read_text())
    bb = json.loads((HERE / "bboxes.json").read_text())

    # idempotency guard
    first_stud = max(next(e for e in od if e["name"] == "back wall studs")
                     ["dx"], 0)
    if abs(first_stud - NEW_STUD) < 0.01:
        sys.exit("already migrated (back wall studs are 92-5/8)")

    old, new = roof(OLD_ZB), roof(NEW_ZB)

    # --- self-check: old formulas reproduce the current audit data ---------
    def near(a, b, tol, what):
        if abs(a - b) > tol:
            sys.exit(f"self-check failed: {what}: formula {a:.6f} vs "
                     f"audit {b:.6f} (tol {tol})")

    for st in ("left rake wall studs", "right rake wall studs"):
        lens = sorted((max(e["dx"], e["dy"], e["dz"])
                       for e in od if e["name"] == st), reverse=True)
        for got, want in zip(lens, sorted(
                (t - OLD_ZB for t in old["stud_top"]), reverse=True)):
            near(got, want, 0.005, f"{st} length")
    for e in od:
        L = max(e["dx"], e["dy"], e["dz"])
        if e["name"] in ("left rake wall top plate", "right rake wall top plate"):
            near(L, old["rake_plate_len"], 0.001, "rake plate length")
        elif e["name"] in ("rafter", "left rake board", "right rake board"):
            near(L, old["rafter_len"], 0.001, f"{e['name']} length")
    rb = next(p for p in bb if p["name"] == "rafter")["bbox_m"]
    near(rb["lowZ"] / M, old["bottom"](Y_END[1]), 0.005, "rafter lowZ")
    near(rb["highZ"] / M, old["bottom"](Y_END[0]) + old["off"], 0.005,
         "rafter highZ")
    for e in od:
        if e["name"] == "right wall cripple studs":
            near(max(e["dx"], e["dy"], e["dz"]),
                 OLD_ZB - 3.0 - CRIPPLE_BOT, 0.001,
                 "right wall cripple studs length")
    for fn, y in (("front fascia", Y_END[0]), ("back fascia", Y_END[1])):
        fb = next(p for p in bb if p["name"] == fn)["bbox_m"]
        near(fb["highZ"] / M, old["bottom"](y) + old["off"], 0.005,
             f"{fn} highZ")
    print("self-check OK: old formulas reproduce current audit data")

    # --- apply: oriented dims ----------------------------------------------
    stud_map = dict(zip(sorted((t - OLD_ZB for t in old["stud_top"]),
                               reverse=True),
                        sorted((t - NEW_ZB for t in new["stud_top"]),
                               reverse=True)))
    for e in od:
        dims = [e["dx"], e["dy"], e["dz"]]
        i = max(range(3), key=lambda k: dims[k])
        L = dims[i]
        n = e["name"]
        if n in STUD_WALLS:
            dims[i] = NEW_STUD
        elif n in ("left rake wall studs", "right rake wall studs"):
            dims[i] = stud_map[min(stud_map, key=lambda k: abs(k - L))]
        elif n in ("left rake wall top plate", "right rake wall top plate"):
            dims[i] = new["rake_plate_len"]
        elif n in ("rafter", "left rake board", "right rake board"):
            dims[i] = new["rafter_len"]
        elif n == "right wall cripple studs":
            dims[i] = NEW_ZB - 3.0 - CRIPPLE_BOT
        else:
            continue
        e["dx"], e["dy"], e["dz"] = dims

    # --- apply: bboxes ------------------------------------------------------
    def fix_world_dims(p):
        b = p["bbox_m"]
        p["dx_m"] = b["highX"] - b["lowX"]
        p["dy_m"] = b["highY"] - b["lowY"]
        p["dz_m"] = b["highZ"] - b["lowZ"]

    hi_front = (new["bottom"](Y_END[0]) + new["off"]) * M
    hi_back = (new["bottom"](Y_END[1]) + new["off"]) * M
    for p in bb:
        n, b = p["name"], p["bbox_m"]
        if n in STUD_WALLS:
            b["highZ"] -= DROP_M
        elif n in PLATES_DOWN:
            b["lowZ"] -= DROP_M
            b["highZ"] -= DROP_M
        elif n == "right wall cripple studs":
            b["highZ"] = (NEW_ZB - 3.0) * M
        elif n in ("left rake wall studs", "right rake wall studs"):
            k = min(range(4), key=lambda k:
                    abs(Y_STUD_FRONT[k] - b["lowY"] / M))
            b["lowZ"] = NEW_ZB * M
            b["highZ"] = new["stud_top"][k] * M
        elif n in ("left rake wall top plate", "right rake wall top plate"):
            b["lowZ"] = NEW_ZB * M
        elif n in ("rafter", "left rake board", "right rake board"):
            b["lowZ"], b["highZ"] = new["bottom"](Y_END[1]) * M, hi_front
        elif n == "front fascia":
            b["highZ"] = hi_front
            b["lowZ"] = hi_front - DEPTH * M
        elif n == "back fascia":
            b["highZ"] = hi_back
            b["lowZ"] = hi_back - DEPTH * M
        else:
            continue
        fix_world_dims(p)

    (HERE / "oriented_dims.json").write_text(
        json.dumps(od, indent=2, sort_keys=True) + "\n")
    (HERE / "bboxes.json").write_text(json.dumps(bb, indent=2) + "\n")

    # --- before/after report ------------------------------------------------
    print(f"\nwall height (back/left/right): {OLD_ZB}\" -> {NEW_ZB}\" "
          f"(stud {OLD_STUD}\" -> {NEW_STUD}\")")
    print(f"roof pitch: atan({old['rise']:g}/65) = "
          f"{math.degrees(math.atan(old['tan'])):.4f} deg -> "
          f"atan({new['rise']:g}/65) = "
          f"{math.degrees(math.atan(new['tan'])):.4f} deg")
    rows = [
        ("back/left/right wall studs", OLD_STUD, NEW_STUD),
        ("rake plate (each)", old["rake_plate_len"], new["rake_plate_len"]),
        ("rafter / rake board", old["rafter_len"], new["rafter_len"]),
        ("right wall cripple studs", OLD_ZB - 3.0 - CRIPPLE_BOT,
         NEW_ZB - 3.0 - CRIPPLE_BOT),
    ] + [(f"rake stud {k+1} (y0={y:g})", ot - OLD_ZB, nt - NEW_ZB)
         for k, (y, ot, nt) in enumerate(
             zip(Y_STUD_FRONT, old["stud_top"], new["stud_top"]))]
    rows += [
        ("front seat heel y", old["heel"], new["heel"]),
        ("rafter AABB lowZ (back end)", old["bottom"](Y_END[1]),
         new["bottom"](Y_END[1])),
        ("rafter AABB highZ (front end)",
         old["bottom"](Y_END[0]) + old["off"],
         new["bottom"](Y_END[0]) + new["off"]),
        ("back fascia z span",
         old["bottom"](Y_END[1]) + old["off"] - DEPTH,
         new["bottom"](Y_END[1]) + new["off"] - DEPTH),
    ]
    print(f"\n{'part / reference':34s} {'before':>12s} {'after':>12s}")
    for label, a, b in rows:
        print(f"{label:34s} {a:12.4f} {b:12.4f}")


if __name__ == "__main__":
    main()
