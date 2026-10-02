#!/usr/bin/env python3
"""One-shot migration: front roof overhang 24 in -> 12 in, so the roof
overhangs 12 in on all four sides (captain 2026-10-02: "i would rather
shorten the leading edge of the roof rather than move the building. 1 foot
overhang on all sides" - the roof edge then clears the town's 10 ft distance
from the house; firstmate data/shed-site-plan-7ft/report.md, option C).

Rewrites scripts/oriented_dims.json and scripts/bboxes.json; the cad/
modules re-derive everything else from those files.

Only the front rafter tail moves. Walls, pitch (0.375), bearing line,
birdsmouth seats, back tail and side overhangs are untouched:
    z(y)     = 121.5 - 0.375 y        bearing line (rafter bottom edge)
    TAIL_F   = -3.5 - 12 = -15.5      front wall outer face - 12" overhang
               (was -27.5)
    rafter / rake boards: plumb ends y -15.5..92.5, length 108 * sec
               = 115.344" (was 128.160"; 10 ft stock now, was 12 ft)
    tail top = z(-15.5) + 5.5 * sec = 133.187 (was 137.687): the roof's
               high edge drops 12 * 0.375 = 4.5"
    front fascia: y -17.0..-15.5 (1.5" beyond the tail), top flush with
               the tail top
    roof plan: 216 x (94 + 17) = 216 x 111 = 18 ft x 9 ft 3 in
               (was 18 ft x 10 ft 3 in)

Self-check: before touching anything, the current audit data must match the
OLD facts above; then the new geometry is written. Re-running after
migration aborts (idempotency guard).

Usage: .venv/bin/python scripts/front_overhang_12.py   (from repo root)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
M = 0.0254  # inches -> meters

FRONT_BEAR = 121.5          # bearing line at y=0 (front wall inner face)
TAN = 0.375                 # pitch (24.375/65)
SEC = math.hypot(1.0, TAN)
RAFTER_OFF = 5.5 * SEC      # rafter AABB top offset (2x6 depth vertical)
Y_FRONT_OUT = -3.5          # front wall outer face
TAIL_F_OLD = Y_FRONT_OUT - 24.0   # -27.5
TAIL_F = Y_FRONT_OUT - 12.0       # -15.5
TAIL_B = 92.5               # back rafter tail (12" overhang, unchanged)
SLOPED = ("rafter", "left rake board", "right rake board")


def zbot(y):
    return FRONT_BEAR - TAN * y


def main():
    od = json.loads((HERE / "oriented_dims.json").read_text())
    bb = json.loads((HERE / "bboxes.json").read_text())
    by = {}
    for p in bb:
        by.setdefault(p["name"], []).append(p)

    rb = by["rafter"][0]["bbox_m"]
    if abs(rb["lowY"] / M - TAIL_F) < 0.01:
        sys.exit("already migrated (front rafter tail is at the 12 in "
                 "overhang)")

    def near(a, b, tol, what):
        if abs(a - b) > tol:
            sys.exit(f"self-check failed: {what}: expected {b:.4f}, "
                     f"audit says {a:.4f}")

    fd = by["front wall double top plate"][0]["bbox_m"]
    bd = by["back wall double top plate short"][0]["bbox_m"]
    near(fd["lowY"] / M, Y_FRONT_OUT, 0.01, "front wall outer face")
    near(fd["lowZ"] / M, FRONT_BEAR, 0.01, "front bearing height")
    near((fd["lowZ"] - bd["highZ"]) / (bd["lowY"] - fd["highY"]), TAN,
         1e-3, "roof pitch")
    old_top = zbot(TAIL_F_OLD) + RAFTER_OFF
    for name in SLOPED:
        for p in by[name]:
            b = p["bbox_m"]
            near(b["lowY"] / M, TAIL_F_OLD, 0.01, f"old {name} front tail")
            near(b["highY"] / M, TAIL_B, 0.01, f"{name} back tail")
            near(b["highZ"] / M, old_top, 0.01, f"old {name} tail top")
    ff = by["front fascia"][0]["bbox_m"]
    near(ff["highY"] / M, TAIL_F_OLD, 0.01, "old front fascia inner face")
    near(ff["highZ"] / M, old_top, 0.01, "old front fascia top")

    # --- new geometry ------------------------------------------------------
    rafter_len = (TAIL_B - TAIL_F) * SEC
    tail_top = zbot(TAIL_F) + RAFTER_OFF
    for name in SLOPED:
        for p in by[name]:
            b = p["bbox_m"]
            b["lowY"] = TAIL_F * M
            b["highZ"] = tail_top * M
            p["dy_m"] = b["highY"] - b["lowY"]
            p["dz_m"] = b["highZ"] - b["lowZ"]
        for e in od:
            if e["name"] == name:
                dims = sorted((e["dx"], e["dy"], e["dz"]))
                e["dx"], e["dy"], e["dz"] = rafter_len, dims[1], dims[0]
    ff["lowY"] = (TAIL_F - 1.5) * M
    ff["highY"] = TAIL_F * M
    ff["highZ"] = tail_top * M
    ff["lowZ"] = (tail_top - 5.5) * M

    (HERE / "oriented_dims.json").write_text(
        json.dumps(od, indent=2, sort_keys=True) + "\n")
    (HERE / "bboxes.json").write_text(json.dumps(bb, indent=2) + "\n")

    print(f"front tail {TAIL_F_OLD} -> {TAIL_F}; rafter/rake board length "
          f"{(TAIL_B - TAIL_F_OLD) * SEC:.3f} -> {rafter_len:.3f}")
    print(f"front tail/fascia top {old_top:.3f} -> {tail_top:.3f}; fascia "
          f"y {TAIL_F - 1.5}..{TAIL_F}; roof plan 216 x "
          f"{TAIL_B + 1.5 - (TAIL_F - 1.5):.0f}")


if __name__ == "__main__":
    main()
