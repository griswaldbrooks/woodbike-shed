#!/usr/bin/env python3
"""One-shot migration: 6 ft shell -> 7 ft shell + the captain's 2-door plan
(captain 2026-08-18 depth decision, shed-depth-decision-2026-08-18.md;
captain 2026-08-23 door verdict, firstmate data/shed-door-plan-model/
captain-decision-2026-08-23.md: the free-doors study WINNER minus the 3 ft
walk-in). Rewrites scripts/oriented_dims.json and scripts/bboxes.json; the
cad/ modules re-derive everything else from those files.

PHASE A - depth 72" -> 84" outer (interior 65" -> 77"), front wall pinned:
  The roof plane pivots about the unchanged front bearing line (restud
  principle). The restud's 24.375/65 pitch is EXACTLY the 7 ft pitch too
  (28.875/77 = 24.375/65 = 0.375) - so the pitch is unchanged and the
  back/left/right wall plate tops land at 92.625" = 92-5/8", the
  pre-restud number (self-checked below).
    z(y)      = 121.5 - 0.375 y      bearing line (rafter bottom edge)
    zu(y)     = z(y) - 1.5*sec       rake plate underside (1.5" plate perp)
    Z_B_NEW   = z(77) = 92.625       back wall double top plate top
    back wall moves y 65..68.5 -> 77..80.5, studs drop to 88-1/8 pre-cut
    floor joists/rim/OSB/skids stretch with the depth
    rafters keep the 24" front overhang (tail -27.5) and gain the back
    tail at 80.5 + 12" overhang = 92.5; back fascia follows the tail.

  Side/gable transition (new at 7 ft): the roof drops below the flat side
  wall's plate stack before the back wall (zu crosses the DTP top 97.125 at
  Y_END_DTP and the top-plate top 95.625 at Y_END_TP). Construction:
    - flat wall (studs + top plate + DTP) runs only to those derived ends;
    - beyond them the wall top follows the roof: studs mitered to the rake
      plate bottom - max(zu(y), Z_B_NEW), the underside out front and the
      flat seat over the back bearing - carry the rake plate straight to
      the back corner (filed with the rake-wall studs, same prism
      construction, bottoms on whatever bears them: sill 1.5 / header top
      89 / DTP top 97.125);
    - the side DTP corner block (y 77..80.5, top 92.625) carries the corner
      rafter's back seat, exactly as today's side DTP does at 6 ft.

PHASE B - the 2-door plan (winner spans/heads, study coordinates):
  FRONT wall, west end: 8 ft (96 in) barn door, clear x 0..96, head 84.
    The west jamb IS the corner: the header spans x -1.5..97.5, its west end
    borne by the corner jack x -1.5..0 standing in the corner block beside
    the corner king (the built-up header-bearing corner post, flagged not
    engineered in the study); east jack 96..97.5 + king 97.5..99. The
    walk-in opening (15.5..51.5) and the old 72" opening are GONE: east of
    the barn the wall is solid studs at 16" oc (97.5..188.5).
  RIGHT wall: 64 in double, clear y 6.5..70.5, head 84. Jacks 5..6.5 and
    70.5..72; the 6.5" end studs each end are the study's flagged minimum
    ((77-64)/2). Cripples under the flat plates stay square; the two over
    the header's east bay miter to the rake plate (filed as rake studs,
    bottom on the 89" header top).
  No left rake-wall door (separate open decision).

Self-check: before touching anything, the current audit data must match the
OLD facts this migration assumes (6 ft shell, old door spans, 0.375 pitch,
the 7 ft pitch identity); then the new geometry is written. Re-running after
migration aborts (idempotency guard).

Usage: ~/.venvs/woodbike-shed/bin/python scripts/depth7ft_2door.py
(from repo root)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

M = 0.0254  # inches -> meters

# --- roof anchors (unchanged by this migration) ----------------------------
Z_F = 123.0                 # front double top plate top
FRONT_BEAR = Z_F - 1.5      # bearing line at y=0 (front wall inner face)
TAN = 24.375 / 65           # pitch, = 0.375 exactly
SEC = math.hypot(1.0, TAN)
GAP_PERP = 1.5 * SEC        # rake plate underside gap (1.5" plate perp)
RAFTER_OFF = 5.5 * SEC      # rafter AABB top offset (2x6 depth vertical)
TAIL_F = -27.5              # front rafter tail (24" overhang, unchanged)
DEPTH_FT = 7.0
STUD_TOP_FLAT = 94.125      # flat side-wall stud top (92-5/8 + 1.5 plate)
TP_TOP = STUD_TOP_FLAT + 1.5      # 95.625 side top plate top
DTP_TOP = TP_TOP + 1.5            # 97.125 side double top plate top

# --- derived 7 ft shell -----------------------------------------------------
OUTER_NEW = DEPTH_FT * 12.0             # 84
Y_BACK_IN = OUTER_NEW - 7.0             # 77 back wall inner face
Y_BACK_OUT = OUTER_NEW - 3.5            # 80.5 back wall outer face
Z_B_NEW = FRONT_BEAR - TAN * Y_BACK_IN  # 92.625 back DTP top
TAIL_B = Y_BACK_OUT + 12.0              # 92.5 back rafter tail (12" o/h)


def zbot(y):
    return FRONT_BEAR - TAN * y


def zu(y):
    return zbot(y) - GAP_PERP


Y_SEAT = (FRONT_BEAR - GAP_PERP - Z_B_NEW) / TAN  # plate seat start
Y_END_TP = (FRONT_BEAR - GAP_PERP - TP_TOP) / TAN    # flat top plate end
Y_END_DTP = (FRONT_BEAR - GAP_PERP - DTP_TOP) / TAN  # flat DTP end


def plate_bottom(y):
    """Rake plate bottom face: the underside out front, the flat seat over
    the back bearing. Mitered studs meet this."""
    return max(zu(y), Z_B_NEW)


# --- new framing layouts ----------------------------------------------------
FRONT_KINGS = [(-3.5, -2.0), (97.5, 99.0), (113.5, 115.0), (129.5, 131.0),
               (145.5, 147.0), (161.5, 163.0), (177.5, 179.0), (187.0, 188.5)]
FRONT_JACKS = [(-1.5, 0.0), (96.0, 97.5)]
BARN_HEADER = (-1.5, 97.5)
FRONT_CRIPPLES = [14.5, 30.5, 46.5, 62.5, 78.5]
RIGHT_JACKS = [(5.0, 6.5), (70.5, 72.0)]
RIGHT_HEADER = (5.0, 72.0)
RIGHT_CRIPPLES = [22.5, 38.5, 54.5]           # square, under the top plate
RIGHT_RAKE_MITRED = [(65.5, 89.0), (68.5, 89.0),   # over the header east bay
                     (73.5, 1.5), (75.5, 1.5)]     # back corner zone
LEFT_FLAT_STUDS = [0.0, 15.5, 31.5, 47.5, 63.5]
LEFT_RAKE_MITRED = [(69.5, 1.5), (73.5, 1.5), (75.5, 1.5)]
RAKE_FLAT = [0.0, 15.5, 31.5, 47.5]           # rake studs on the DTP top
BACK_STUD_X = (-3.5, 11.0, 27.0, 43.0, 59.0, 75.0, 91.0, 107.0, 123.0,
               139.0, 155.0, 171.0, 187.0)


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
    if abs(bb_by["back wall bottom plate"][0]["bbox_m"]["lowY"] / M
           - Y_BACK_IN) < 0.5:
        sys.exit("already migrated (back wall is at the 7 ft position)")

    # --- self-check: the old facts this migration assumes ------------------
    def near(a, b, tol, what):
        if abs(a - b) > tol:
            sys.exit(f"self-check failed: {what}: expected {b:.4f}, "
                     f"audit says {a:.4f}")

    near(bb_by["back wall bottom plate"][0]["bbox_m"]["lowY"] / M, 65.0,
         0.01, "old back wall inner face")
    rb = bb_by["rafter"][0]["bbox_m"]
    near(rb["lowY"] / M, TAIL_F, 0.01, "old front rafter tail")
    near(rb["highY"] / M, 80.5, 0.01, "old back rafter tail")
    fd = bb_by["front wall double top plate"][0]["bbox_m"]
    bd = bb_by["back wall double top plate short"][0]["bbox_m"]
    near((fd["lowZ"] - bd["highZ"]) / (bd["lowY"] - fd["highY"]), TAN,
         1e-3, "old roof pitch")
    # the 7 ft pitch identity: deepening keeps the restud pitch exactly
    near((FRONT_BEAR - Z_B_NEW) / Y_BACK_IN, TAN, 1e-9,
         "7 ft pitch != 24.375/65")
    near(zbot(Y_BACK_IN), Z_B_NEW, 1e-9, "Z_B_NEW off the bearing line")

    from cad.common import load_audit, finish_layout  # noqa: E402
    L = finish_layout(load_audit())
    near(L["b"] - L["f"], 72.0, 0.01, "old outer depth")
    fo = sorted((round(a, 1), round(b, 1)) for a, b, _ in L["front_open"])
    ro = sorted((round(a, 1), round(b, 1)) for a, b, _ in L["right_open"])
    if fo != [(15.5, 51.5), (99.0, 171.0)] or ro != [(8.5, 44.5)]:
        sys.exit(f"self-check failed: old door spans {fo} / {ro}")
    print("self-check OK: old 6 ft shell + old door spans as assumed")

    # --- helpers -------------------------------------------------------------
    _seq = iter(range(1000))

    def add(name, x0, x1, y0, y1, z0, z1, oriented=None):
        """One part: bbox entry + oriented-dims (length, wide, thick).
        oriented = slope length for prisms whose longest edge is not an
        AABB extent; the rake plate's 1.5" member thickness is likewise
        not an AABB extent (its Z extent is the whole roof rise), so it
        is passed as the oriented pair (slope_len, thick)."""
        i = next(_seq)
        b = {"lowX": x0 * M, "lowY": y0 * M, "lowZ": z0 * M,
             "highX": x1 * M, "highY": y1 * M, "highZ": z1 * M}
        bb.append({"partId": f"N{i:02d}", "name": name, "bbox_m": b,
                   "dx_m": b["highX"] - b["lowX"],
                   "dy_m": b["highY"] - b["lowY"],
                   "dz_m": b["highZ"] - b["lowZ"]})
        if isinstance(oriented, tuple):        # (slope_len, thickness)
            dims = sorted([oriented[1], 3.5, oriented[0]])
        else:
            dims = sorted([x1 - x0, y1 - y0, z1 - z0])
            if oriented is not None:
                dims[2] = oriented
        od.append({"name": name, "dx": dims[2], "dy": dims[1],
                   "dz": dims[0]})

    def drop(name):
        bb[:] = [p for p in bb if p["name"] != name]
        od[:] = [e for e in od if e["name"] != name]

    def stretch_y(name, high_y):
        for p in bb_by[name]:
            p["bbox_m"]["highY"] = high_y * M
            p["dy_m"] = p["bbox_m"]["highY"] - p["bbox_m"]["lowY"]

    SIDE_X = {"left": (-3.5, 0.0), "right": (185.0, 188.5)}

    # =====================================================================
    # PHASE A - depth
    # =====================================================================

    # -- back wall: +12 in Y, plate tops drop to the bearing line at y=77
    drop("back wall studs")
    for x0 in BACK_STUD_X:
        add("back wall studs", x0, x0 + 1.5, Y_BACK_IN, Y_BACK_OUT,
            1.5, Z_B_NEW - 3.0)
    drop("back wall bottom plate")
    add("back wall bottom plate", -3.5, 188.5, Y_BACK_IN, Y_BACK_OUT,
        0.0, 1.5)
    drop("back wall top plate")
    add("back wall top plate", -3.5, 188.5, Y_BACK_IN, Y_BACK_OUT,
        Z_B_NEW - 3.0, Z_B_NEW - 1.5)
    drop("back wall double top plate short")
    add("back wall double top plate short", 0.0, 185.0, Y_BACK_IN,
        Y_BACK_OUT, Z_B_NEW - 1.5, Z_B_NEW)

    # -- floor: joists/rim/OSB stretch; back skid line moves under the wall
    stretch_y("floor joist", Y_BACK_OUT - 1.5)
    for e in od:
        if e["name"] == "floor joist":
            e["dx"] = Y_BACK_OUT - 1.5 + 2.0   # joists span y -2..79
    for p in bb_by["rim joist"]:
        if p["bbox_m"]["lowY"] / M > 1.0:      # back rim
            p["bbox_m"]["lowY"] = (Y_BACK_OUT - 1.5) * M
            p["bbox_m"]["highY"] = Y_BACK_OUT * M
    stretch_y("sub floor osb", Y_BACK_OUT)
    for e in od:
        if e["name"] == "sub floor osb":
            dims = sorted((e["dx"], e["dy"], e["dz"]))
            dims[2] = OUTER_NEW                # the 72" sheet dim -> 84"
            e["dx"], e["dy"], e["dz"] = dims[2], dims[1], dims[0]
    for p in bb_by["skid"]:
        if p["bbox_m"]["lowY"] / M > 1.0:      # back skid line
            p["bbox_m"]["lowY"] = Y_BACK_IN * M
            p["bbox_m"]["highY"] = Y_BACK_OUT * M
    for p in bb_by.get("inner volume", []):
        p["bbox_m"]["highY"] += 12.0 * M
        p["dy_m"] = p["bbox_m"]["highY"] - p["bbox_m"]["lowY"]
    for e in od:
        if e["name"] == "inner volume":
            dims = sorted((e["dx"], e["dy"], e["dz"]))
            dims[0] += 12.0                    # the 65" depth dim -> 77"
            e["dx"], e["dy"], e["dz"] = dims[2], dims[1], dims[0]

    # -- side walls: flat plates end where the roof drops past them; corner
    #    post + DTP corner block carry the corner rafters' back seats
    for side, flat_studs in (("left", LEFT_FLAT_STUDS), ("right", [0.0])):
        x0, x1 = SIDE_X[side]
        wall = f"{side} side wall studs" if side == "left" \
            else "right wall studs"
        drop(wall)
        for y0 in flat_studs:
            add(wall, x0, x1, y0, y0 + 1.5, 1.5, STUD_TOP_FLAT)
        cx0 = -1.5 if side == "left" else 185.0
        add(wall, cx0, cx0 + 1.5, Y_BACK_IN, Y_BACK_OUT, 1.5, Z_B_NEW - 3.0)
        drop(f"{side} wall top plate")
        add(f"{side} wall top plate", x0, x1, 0.0, Y_END_TP,
            STUD_TOP_FLAT, TP_TOP)
        drop(f"{side} wall double top plate")
        add(f"{side} wall double top plate", x0, x1, 0.0, Y_END_DTP,
            TP_TOP, DTP_TOP)
        add(f"{side} wall double top plate", x0, x1, Y_BACK_IN, Y_BACK_OUT,
            Z_B_NEW - 1.5, Z_B_NEW)
        if side == "left":
            drop("left side wall bottom plate")
            add("left side wall bottom plate", x0, x1, 0.0, Y_BACK_IN,
                0.0, 1.5)
        else:  # right bottom plates are re-cut around the opening below
            drop("right wall bottom plate long")
            drop("right wall bottom plate short")

    # -- rake walls: plate to the new back wall; standard rake studs kept,
    #    mitered studs take the sloped top over to the corners
    rake_plate_len = Y_BACK_IN * SEC
    for side, mitred in (("left", LEFT_RAKE_MITRED),
                         ("right", RIGHT_RAKE_MITRED)):
        x0, x1 = SIDE_X[side]
        drop(f"{side} rake wall top plate")
        add(f"{side} rake wall top plate", x0, x1, 0.0, Y_BACK_IN,
            Z_B_NEW, FRONT_BEAR, oriented=(rake_plate_len, 1.5))
        drop(f"{side} rake wall studs")
        for y0 in RAKE_FLAT:
            add(f"{side} rake wall studs", x0, x1, y0, y0 + 1.5,
                DTP_TOP, zu(y0))
        for y0, z_bot in mitred:
            add(f"{side} rake wall studs", x0, x1, y0, y0 + 1.5,
                z_bot, plate_bottom(y0))

    # -- roof: rafters/rake boards grow to the new back tail; back fascia
    #    follows. Front bearing line + front tail unchanged.
    rafter_len = (TAIL_B - TAIL_F) * SEC
    tail_top_f = zbot(TAIL_F) + RAFTER_OFF
    tail_top_b = zbot(TAIL_B) + RAFTER_OFF
    for name in ("rafter", "left rake board", "right rake board"):
        for p in bb_by[name]:
            p["bbox_m"]["lowY"] = TAIL_F * M
            p["bbox_m"]["highY"] = TAIL_B * M
            p["bbox_m"]["lowZ"] = zbot(TAIL_B) * M
            p["bbox_m"]["highZ"] = tail_top_f * M
            p["dy_m"] = p["bbox_m"]["highY"] - p["bbox_m"]["lowY"]
            p["dz_m"] = p["bbox_m"]["highZ"] - p["bbox_m"]["lowZ"]
        for e in od:
            if e["name"] == name:
                dims = sorted((e["dx"], e["dy"], e["dz"]))
                e["dx"], e["dy"], e["dz"] = rafter_len, dims[1], dims[0]
    for p in bb_by["back fascia"]:
        p["bbox_m"]["lowY"] = TAIL_B * M
        p["bbox_m"]["highY"] = (TAIL_B + 1.5) * M
        p["bbox_m"]["highZ"] = tail_top_b * M
        p["bbox_m"]["lowZ"] = (tail_top_b - 5.5) * M

    # =====================================================================
    # PHASE B - the 2-door plan
    # =====================================================================

    # -- front wall: one 96" barn opening at the west corner, solid east
    drop("front wall king studs")
    for x0, x1 in FRONT_KINGS:
        add("front wall king studs", x0, x1, -3.5, 0.0, 1.5, 120.0)
    drop("front wall jack studs")
    for x0, x1 in FRONT_JACKS:
        add("front wall jack studs", x0, x1, -3.5, 0.0, 1.5, 84.0)
    drop("front wall headers")
    h0, h1 = BARN_HEADER
    add("front wall headers", h0, h1, -1.5, 0.0, 84.0, 87.5)
    add("front wall headers", h0, h1, -3.5, -2.0, 84.0, 87.5)
    add("front wall headers", h0, h1, -3.5, 0.0, 87.5, 89.0)
    drop("front wall cripple studs")
    for x0 in FRONT_CRIPPLES:
        add("front wall cripple studs", x0, x0 + 1.5, -3.5, 0.0, 89.0, 120.0)

    # -- right wall: the 64" brewery double (end studs 6.5" each end)
    drop("right wall jack studs")
    for y0, y1 in RIGHT_JACKS:
        add("right wall jack studs", 185.0, 188.5, y0, y1, 1.5, 84.0)
    drop("right wall headers")
    r0, r1 = RIGHT_HEADER
    add("right wall headers", 185.0, 186.5, r0, r1, 84.0, 87.5)
    add("right wall headers", 187.0, 188.5, r0, r1, 84.0, 87.5)
    add("right wall headers", 185.0, 188.5, r0, r1, 87.5, 89.0)
    drop("right wall cripple studs")
    for y0 in RIGHT_CRIPPLES:
        add("right wall cripple studs", 185.0, 188.5, y0, y0 + 1.5,
            89.0, STUD_TOP_FLAT)
    add("right wall bottom plate short", 185.0, 188.5, 0.0, 6.5, 0.0, 1.5)
    add("right wall bottom plate long", 185.0, 188.5, 70.5, Y_BACK_IN,
        0.0, 1.5)

    # --- write ---------------------------------------------------------------
    (HERE / "oriented_dims.json").write_text(
        json.dumps(od, indent=2, sort_keys=True) + "\n")
    (HERE / "bboxes.json").write_text(json.dumps(bb, indent=2) + "\n")

    # --- report ---------------------------------------------------------------
    print(f"\ndepth: 72 -> {OUTER_NEW:.0f} in outer "
          f"(interior 65 -> {Y_BACK_IN:.0f}); pitch unchanged "
          f"{math.degrees(math.atan(TAN)):.4f} deg")
    print(f"back/left/right wall height: 97.125 -> {Z_B_NEW:.3f} "
          f"(pre-cut stud 92-5/8 -> {Z_B_NEW - 4.5:.3f} = 88-1/8)")
    print(f"flat side-wall ends: DTP y {Y_END_DTP:.3f}, top plate y "
          f"{Y_END_TP:.3f}; rake plate seat y {Y_SEAT:.3f}..{Y_BACK_IN:.0f}")
    print(f"rafter: tails {TAIL_F}/{TAIL_B}, length {rafter_len:.3f} "
          f"(needs stock > 10 ft now)")
    print("doors: front barn clear 0..96 head 84 (corner jack -1.5..0); "
          "right double clear 6.5..70.5 head 84; walk-in REMOVED")


if __name__ == "__main__":
    main()
