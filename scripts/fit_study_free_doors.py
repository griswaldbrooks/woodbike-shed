#!/usr/bin/env python3
"""Storage jenga, FREE-DOORS study (REPO COPY, adapted 2026-08-23): arrange
the 7 ft shed interior first, then propose the doors.

Adapted from the firstmate free-doors study
(data/shed-jenga-arrange/storage_jenga_free_doors.py, scout report beside
it). The adaptation adds the captain's adopted arrangement (--arrange
winner2): the winner MINUS the 3 ft walk-in (captain 2026-08-23), PLUS the
LEFT rake-wall 64 in double promoted to MAIN pedestrian door (captain
2026-08-24, closest to the garage/access - mirror of the right brewery
double). Slab loading routes through the 8 ft barn door; the left main door
is the everyday entry. The original four arrangements run unchanged. The
study's narrative references (../shed-jenga-brewery/ etc.) live in the
firstmate data tree, not here.

Extends the permanent-brewery study (../shed-jenga-brewery/, its
storage_jenga_brewery.py is the scaffold here). Equipment facts unchanged,
all sourced in ../shed-jenga-brewery/research/EQUIPMENT_FACTS.md (TEB
3-kettle 20-gal: stand 64 x 26 x 34.5, kettles 17.7 sq x ~23 H w/ lid,
pumps below, 30A panel 18.5 x 16 x 9.125 wall-mount, hood 67 x 24 x 12,
>= 312 CFM extraction for the 5500 W elements, ~2 gal/hr boil-off).

Arrangements (--arrange):
  winner      SIDE brewery on the RIGHT rake wall (64 in opening), west
              cluster: blower + both bikes nose-in UNDER the lifted slab
              run, all straight-rolling out one 8-ft barn door; 36 in
              walk-in + slab feed door east of it. 3 doors total.
  runner-up   FRONT brewery (stand east, 72 in corner door), same west
              cluster + barn door; walk-in + slab feed move to the right
              wall. 3 doors total.
  old-front   Reproduction of the prior brewery study: brewery on the front
              wall, doors AS DESIGNED (walk-in 15.5-51.5, double 99-171,
              right 8.5-44.5) - the forced baseline this study beats.
  old-baseline  The pure lifted-rack baseline with as-designed doors.
  winner2     The ADOPTED plan (winner minus the walk-in, + the captain's
              2026-08-24 LEFT main door): barn 8 ft + LEFT rake-wall 64 in
              MAIN entry (closest to the garage/access) + RIGHT brewery 64
              in; slab feed via the barn door. NOTE: the filled-storage study
              leans 4 plywood sheets on this (west/left) wall strip y 1-49;
              the MAIN door now occupies that strip, so the plywood lean-to
              RELOCATES (new spot a separate decision — see
              OUTSTANDING_ISSUES.md "Plywood lean-to relocation"). Run:
              scripts/fit_summary_winner2.txt carries the record.
  --mirror    Geometric mirror of winner/runner-up (brewery LEFT, rack east)
              - proves the left/right symmetry of Q1.

Named-check suite (every arrangement): nose-in bike fit + lift clearance
under the slab stack, blower exit path, slab feed path (10 ft slabs carried
on edge), brewer reach from outside (kettle centers <= 24 in past the door
plane), pedestrian entry, pairwise 3-D overlap; plus the new free-doors
checks: straight-roll bike+blower exit, side-wall brewery reach, kettles
inside the side-door span, rake-wall duct exit over the door head, pier and
end-stud widths, panel reach/read from the brewer station.

Door structural reality is a consequence note, never a blocker: any new
opening re-frames its wall; the 64 in rake-wall opening is flagged loudly.

Usage (any venv with build123d + Pillow, e.g. ~/.venvs/woodbike-shed):
    python storage_jenga_free_doors.py --repo /path/to/woodbike-shed \
        --out DIR [--arrange winner|runner-up|old-front|old-baseline]
        [--mirror] [--side-door-w-in 64] [--rack-clear-in 48]
        [--slabs N] [--bikes N] [--view]
Prints the fit summary (fit_summary_<arrange>[_mirror].txt) and writes
plan/iso/section PNGs with the same suffix.

Axis note (model coordinates, kept out of rendered text): X = shed length
(left->right), Y = shed depth (front->back), Z = up, inches.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path


def find_repo(start: Path, override: str | None) -> Path:
    cands = ([Path(override)] if override else []) + [start, *start.parents]
    for p in cands:
        if (p / "cad" / "common.py").exists():
            return p
    sys.exit("could not locate the woodbike-shed repo (cad/common.py); "
             "pass --repo PATH")


# ---------------------------------------------------------------- parameters

@dataclass
class P:
    slab_count: int = 6        # the jenga knob
    slab_len: float = 120.0    # in, 10 ft slabs
    slab_w: float = 28.0       # in
    slab_t: float = 2.0        # in, 8/4
    sticker: float = 0.75      # in air gap between slabs
    rack_clear: float = 48.0   # in, UNDERSIDE of the bottom slab (the lift)
    arm_t: float = 1.5         # in, support arm thickness under the stack
    bike_count: int = 2
    bike_l: float = 70.0       # in, captain-measured
    bike_w: float = 27.0       # in, handlebar width, captain-measured
    bike_h: float = 43.0       # in, rolling height (floor-parked)
    blower_l: float = 56.0     # in, Storm 2410, captain-measured
    blower_w: float = 27.0     # in, 24 body + side crank handle
    blower_h: float = 43.0     # in, captain-measured
    # --- permanent brewery, sourced in EQUIPMENT_FACTS.md (see docstring):
    kettle_d: float = 17.7
    kettle_h: float = 20.7
    lid_h: float = 2.25
    stand_w: float = 64.0      # the reach face (kettle row direction)
    stand_d: float = 26.0
    stand_h: float = 34.5
    hood_w: float = 67.0
    hood_d: float = 24.0
    hood_h: float = 12.0
    hood_gap: float = 15.0
    panel_w: float = 16.0
    panel_h: float = 18.5
    panel_d: float = 9.125
    pump_l: float = 10.0
    pump_w: float = 8.0
    pump_h: float = 6.0
    brewery: bool = True
    # --- free-doors concept rules of thumb (flagged, not engineered):
    min_pier: float = 10.0     # in of stud wall between two openings
    min_end_stud: float = 6.0  # in of wall between an opening and a corner
    door_head: float = 84.0    # in, as-designed head height, kept


HEAD = 84.0


# ---------------------------------------------------------------- envelope

@dataclass
class Env:
    x0: float; x1: float; y0: float; y1: float      # inside faces of framing
    wall_t: float
    outer_depth: float
    front_top: float; back_top: float                # plate tops
    doors: list = field(default_factory=list)        # (wall, lo, hi, head)
    roof_z: object = None                            # roof underside z(y)


def envelope(depth_ft: float, verbose: bool = True) -> Env:
    """Concept envelope: same wall build as the audited 6 ft shed, deeper.
    Wall totals DERIVED from the model (cad/common.py), 7.0 in total.
    Door positions are NOT read from the model in this study - they are free
    variables proposed by each arrangement (old-* modes re-set the
    as-designed spans themselves)."""
    sys.path.insert(0, str(REPO))
    from cad.common import load_audit, finish_layout
    audit = load_audit()
    L = finish_layout(audit)
    ref = L["ref"]
    outer_d_model = L["b"] - L["f"]
    inner_d_model = ref.back_seat_start_y - ref.front_bear_y
    wall_t = (outer_d_model - inner_d_model) / 2
    assert abs(wall_t - 3.5) < 0.01, \
        f"wall build changed under the jenga: {2 * wall_t:.2f} in total"
    x1 = (L["r"] - L["l"]) - 2 * wall_t
    assert abs(x1 - 185.0) < 0.01, "shell length is no longer 16 ft"
    outer_depth = depth_ft * 12.0
    y1 = outer_depth - 2 * wall_t
    roof_z = lambda y: ref.front_bear_z - ref.slope * (y - ref.front_bear_y)
    if verbose:
        print("Concept envelope (wall build verified from the audited "
              "model, not assumed):")
        print(f"  model: {outer_d_model:.1f} in outer - "
              f"{inner_d_model:.1f} in interior = "
              f"{2 * wall_t:.1f} in wall total (two {wall_t:.1f} in walls)")
        print(f"  concept: {outer_depth:.0f} in outer - "
              f"{2 * wall_t:.0f} in walls = {y1:.0f} in interior depth; "
              f"length stays {x1:.0f} in")
        print(f"  roof pinned at the front bearing line; back wall top "
              f"{roof_z(y1):.2f} in, front wall top {L['front_top']:.1f} in")
        print(f"  as-designed doors (reference only, now FREE variables): "
              f"front {[(round(a,1), round(b,1)) for a,b,_ in L['front_open']]}, "
              f"left {[(round(a,1), round(b,1)) for a,b,_ in L['left_open']]}, "
              f"right {[(round(a,1), round(b,1)) for a,b,_ in L['right_open']]}")
    return Env(
        x0=0.0, x1=x1, y0=0.0, y1=y1, wall_t=wall_t, outer_depth=outer_depth,
        front_top=L["front_top"], back_top=roof_z(y1), roof_z=roof_z,
    )


# ------------------------------------------------------------------ layout

def layout(p: P, e: Env, arrange: str, mirror: bool = False,
           side_door_w: float = 64.0):
    """Returns (boxes, checks, info). Doors are part of the arrangement -
    derived from what rolls or feeds through them, not read from the model.
    mirror=True flips the whole arrangement about the shed centerline
    (x -> x1 - x), proving the left/right symmetry."""
    boxes, checks = [], []
    X1, Y1 = e.x1, e.y1

    def mx(v):
        return X1 - v if mirror else v

    def box(kind, label, x0, x1, y0, y1, z0, z1, color, **kw):
        if mirror:
            x0, x1 = X1 - x1, X1 - x0
        b = dict(kind=kind, label=label, x0=x0, x1=x1, y0=y0, y1=y1,
                 z0=z0, z1=z1, color=color)
        b.update(kw)
        boxes.append(b)

    def add_door(wall, lo, hi, role):
        if mirror and wall in ("left", "right"):
            wall = "left" if wall == "right" else "right"
        if mirror and wall == "front":
            lo, hi = X1 - hi, X1 - lo
        e.doors.append((wall, lo, hi, p.door_head, role))

    old_front = arrange in ("old-front", "old-baseline")
    if old_front:
        # the as-designed spans, for the reproduction runs
        e.doors += [("front", 15.5, 51.5, HEAD, "walk-in (as designed)"),
                    ("front", 99.0, 171.0, HEAD, "double (as designed)"),
                    ("right", 8.5, 44.5, HEAD, "right door (as designed)")]

    aisle_y = Y1 - p.slab_w                     # clear depth in front of rack
    underside = p.rack_clear - p.arm_t          # true structural underside
    bay_w = p.bike_count * p.bike_w + (p.bike_count - 1) * 2.0

    # ------------------------------------------------------------- slab rack
    # Back wall. Winner/runner-up keep the rack on the LEFT (all prior
    # studies); mirror puts it right. Rack posts: west post inset 4 in (a
    # free-doors change, flagged: the west cluster needs the bay from ~6 in
    # on); east post inset 8 in as before.
    rack_x0 = 0.0
    rack_x1 = p.slab_len
    rxlo, rxhi = min(rack_x0, rack_x1), max(rack_x0, rack_x1)
    rack_y1 = Y1
    rack_y0 = rack_y1 - p.slab_w
    checks.append(("slab length fits the interior",
                   p.slab_len <= X1,
                   f"slab {p.slab_len:.0f} in vs interior {X1:.0f} in"))
    up = sorted([4.0, p.slab_len - 8.0])
    for ux in up:
        box("rack", "rack upright", ux - 1.75, ux + 1.75, rack_y0 + 1.0,
            rack_y1 - 1.0, 0, p.rack_clear, (130, 130, 135))
    for ay in (rack_y0 + 3.0, rack_y1 - 3.0):
        box("rack", "rack arm", up[0] - 1.75, up[1] + 1.75, ay - 1.75,
            ay + 1.75, underside, p.rack_clear, (130, 130, 135))
    top_of_stack = p.rack_clear
    for i in range(p.slab_count):
        z0 = p.rack_clear + i * (p.slab_t + p.sticker)
        box("slab", f"cherry slab {i + 1}", rxlo, rxhi, rack_y0, rack_y1,
            z0, z0 + p.slab_t, (166, 98, 66))
        top_of_stack = z0 + p.slab_t
    checks.append(("stack top clears the back wall comfortably",
                   top_of_stack <= e.back_top - 12,
                   f"stack top {top_of_stack:.2f} in vs back wall "
                   f"{e.back_top:.2f} in ({e.back_top - top_of_stack:.1f} in "
                   f"headroom)"))

    # ------------------------------------------------- the west cluster
    # Free-doors Q2: bikes + blower ALL nose-in under the lifted slab run,
    # hard against the west end (clear of the west post by 2 in), so every
    # wheeled item straight-rolls out one wide front door. The blower's
    # 43 in height clears the 46.5 in structure exactly like the bikes.
    cluster = arrange in ("winner", "winner2", "runner-up")
    if cluster:
        cs = (up[0] + 1.75) + 2.0               # cluster west edge
        bl_x0 = cs
        bikes_x0 = cs + p.blower_w + 2.0
    else:
        bikes_x0 = 51.5                         # as-designed pin (old modes)
        bl_x0 = None

    bike_y0 = Y1 - p.bike_l
    bike_y1 = Y1
    apron = bike_y0
    bikes = []
    for i in range(p.bike_count):
        bx0 = bikes_x0 + i * (p.bike_w + 2.0)
        bikes.append((bx0, bx0 + p.bike_w))
        box("bike", f"bike {i + 1} (nose-in)", bx0, bx0 + p.bike_w,
            bike_y0, bike_y1, 0, p.bike_h, (70, 130, 180))
    checks.append(("bikes fit nose-in (floor-parked)",
                   bike_y0 >= 0,
                   f"bike {p.bike_l:.0f} in vs interior depth {Y1:.0f} in"
                   f" -> {apron:.0f} in apron"))
    checks.append(("bikes clear the stack underside (the lift check)",
                   underside - p.bike_h >= 3,
                   f"structure {underside:.1f} in over {p.bike_h:.0f} in "
                   f"bikes -> {underside - p.bike_h:.1f} in clear (min 3)"))
    checks.append(("bike bay tucked under the slab run",
                   bikes[0][0] >= rxlo and bikes[-1][1] <= rxhi,
                   f"bay {bikes[0][0]:.2f}-{bikes[-1][1]:.2f} in within "
                   f"rack {rxlo:.0f}-{rxhi:.0f} in"))
    checks.append(("bike bay clears the rack uprights",
                   min(bikes[0][0] - (up[0] + 1.75),
                       (up[1] - 1.75) - bikes[-1][1]) >= 2,
                   f"tightest gap {min(bikes[0][0] - (up[0] + 1.75), (up[1] - 1.75) - bikes[-1][1]):.2f} in"))

    if cluster:
        # the blower joins the cluster, nose-in under the run (43 in vs the
        # 46.5 in structure - same mechanism as the bikes)
        bl_x1 = bl_x0 + p.blower_w
        bl_y0 = Y1 - p.blower_l
        box("blower", "snow blower (nose-in)", bl_x0, bl_x1, bl_y0, Y1,
            0, p.blower_h, (200, 90, 60))
        checks.append(("blower clears the stack underside (the lift check)",
                       underside - p.blower_h >= 3,
                       f"structure {underside:.1f} in over "
                       f"{p.blower_h:.0f} in blower -> "
                       f"{underside - p.blower_h:.1f} in clear (min 3)"))
        checks.append(("blower clears the west upright (rack post inset "
                       "moved 8 -> 4 in for the cluster, flagged)",
                       bl_x0 - (up[0] + 1.75) >= 2,
                       f"{bl_x0 - (up[0] + 1.75):.2f} in gap"))
        checks.append(("Q2: bikes AND blower hard on one side (west "
                       "cluster under the run)",
                       min(bikes[0][0], bl_x0) < 12
                       and max(bikes[-1][1], bl_x1) < 100,
                       f"cluster {min(bikes[0][0], bl_x0):.2f}-"
                       f"{max(bikes[-1][1], bl_x1):.2f} in of the "
                       f"{X1:.0f} in shell"))
    blower = (bl_x0, bl_x0 + p.blower_w, Y1 - p.blower_l, Y1) if cluster \
        else None

    # ------------------------------------------------------------- brewery
    brew = {}
    brew_wall = {"winner": "right", "winner2": "right",
                 "runner-up": "front",
                 "old-front": "front", "old-baseline": None}[arrange]
    if p.brewery and brew_wall:
        kettle_top = p.stand_h + p.kettle_h + p.lid_h
        kettle_rim = p.stand_h + p.kettle_h
        if brew_wall == "front":
            # stand against the front wall, reach face along X
            if old_front:
                dbl = (99.0, 171.0)
                st_x0 = bikes[-1][1] + 0.5      # scaffold placement
            else:                       # runner-up: east corner, door 72
                st_x0 = X1 - p.stand_w - 0.0
                dbl = (X1 - 72.0, X1)
            st_x1 = st_x0 + p.stand_w
            st_y0, st_y1 = 0.0, p.stand_d
            kettles = [st_x0 + p.stand_w * (i + 0.5) / 3 for i in range(3)]
            box("stand", "brew stand", st_x0, st_x1, st_y0, st_y1,
                0, p.stand_h, (120, 85, 60))
            for i, cx in enumerate(kettles):
                box("kettle", f"kettle {i + 1} (20 gal)",
                    cx - p.kettle_d / 2, cx + p.kettle_d / 2,
                    st_y0 + (p.stand_d - p.kettle_d) / 2,
                    st_y0 + (p.stand_d + p.kettle_d) / 2,
                    p.stand_h, kettle_top, (185, 190, 195))
            pumps = [(st_x0 + p.stand_w * f - p.pump_l / 2,
                      st_x0 + p.stand_w * f + p.pump_l / 2)
                     for f in (0.28, 0.72)]
            for j, (qx0, qx1) in enumerate(pumps):
                box("pump", f"pump {j + 1}", qx0, qx1, st_y0 + 5,
                    st_y0 + 13, 0, p.pump_h, (60, 60, 65))
            hx0 = min((st_x0 + st_x1) / 2 - p.hood_w / 2, X1 - p.hood_w)
            hz0 = kettle_top + p.hood_gap
            box("hood", "condensate hood", hx0, hx0 + p.hood_w, st_y0,
                st_y0 + p.hood_d, hz0, hz0 + p.hood_h, (150, 150, 155),
                alpha=0.5)
            door_span = dbl
        else:
            # stand against the RIGHT rake wall (mirror: left), reach face
            # along Y; the stand's 64 in runs down the 77 in wall centered,
            # leaving the end-stud strips the door framing needs
            st_y0 = (Y1 - p.stand_w) / 2
            st_y1 = st_y0 + p.stand_w
            st_x0, st_x1 = X1 - p.stand_d, X1
            kettles = [st_y0 + p.stand_w * (i + 0.5) / 3 for i in range(3)]
            box("stand", "brew stand", st_x0, st_x1, st_y0, st_y1,
                0, p.stand_h, (120, 85, 60))
            kcx = (st_x0 + st_x1) / 2
            for i, cy in enumerate(kettles):
                box("kettle", f"kettle {i + 1} (20 gal)",
                    kcx - p.kettle_d / 2, kcx + p.kettle_d / 2,
                    cy - p.kettle_d / 2, cy + p.kettle_d / 2,
                    p.stand_h, kettle_top, (185, 190, 195))
            pumps = [(st_y0 + p.stand_w * f - p.pump_l / 2,
                      st_y0 + p.stand_w * f + p.pump_l / 2)
                     for f in (0.28, 0.72)]
            for j, (qy0, qy1) in enumerate(pumps):
                px0 = st_x0 + 2
                box("pump", f"pump {j + 1}", px0, px0 + p.pump_l, qy0,
                    qy1, 0, p.pump_h, (60, 60, 65))
            hy0 = (st_y0 + st_y1) / 2 - p.hood_w / 2
            hz0 = kettle_top + p.hood_gap
            hx0 = kcx - p.hood_d / 2
            box("hood", "condensate hood", hx0, hx0 + p.hood_d, hy0,
                hy0 + p.hood_w, hz0, hz0 + p.hood_h, (150, 150, 155),
                alpha=0.5)
            door_span = (st_y0, st_y1)

        brew = dict(wall=brew_wall, st_x0=st_x0, st_x1=st_x1,
                    st_y0=st_y0 if brew_wall == "right" else None,
                    kettles=kettles, kettle_rim=kettle_rim,
                    kettle_top=kettle_top, hood_z0=hz0,
                    hood=(hx0, hx0 + (p.hood_w if brew_wall == "front"
                                      else p.hood_d)),
                    pumps=pumps, door_span=door_span)

        # brewery door (free-doors: sized and placed for the kettle row)
        if not old_front:
            if brew_wall == "front":
                add_door("front", st_x0 - 8.0, X1,
                         "brewery 72 in (corner door)")
            else:
                lo = (st_y0 + st_y1) / 2 - side_door_w / 2
                add_door("right", lo, lo + side_door_w,
                         f"brewery {side_door_w:.0f} in rake-wall door")
                brew["door"] = (lo, lo + side_door_w)
                checks.append((f"side-door width carries the kettle row",
                               side_door_w >= p.stand_w,
                               f"kettle bodies span "
                               f"{p.stand_w - 2 * (p.stand_w / 6 - p.kettle_d / 2):.1f} in "
                               f"of the {p.stand_w:.0f} in stand; door "
                               f"{side_door_w:.0f} in"))
                checks.append(("rake-wall end studs survive the opening "
                               "(flagged, not engineered)",
                               lo >= p.min_end_stud
                               and Y1 - (lo + side_door_w) >= p.min_end_stud,
                               f"{lo:.1f} in at the front end, "
                               f"{Y1 - lo - side_door_w:.1f} in at the back "
                               f"end of the {Y1:.0f} in wall (min "
                               f"{p.min_end_stud:.0f})"))
        else:
            brew["door"] = (99.0, 171.0)

        # reach from outside (door plane = wall inner face)
        checks.append((f"brewer reach from outside ({brew_wall} wall)",
                       p.stand_d / 2 + p.kettle_d / 2 <= 24,
                       f"kettle centers {p.stand_d / 2:.0f} in past the "
                       f"door plane, rims {kettle_rim:.2f} in over the deck "
                       f"(<= 24 in comfortable reach)"))
        checks.append(("brewery: hood covers every kettle",
                       (hx0 <= (kettles[0] - p.kettle_d / 2)
                        and hx0 + (p.hood_w if brew_wall == "front"
                                   else p.hood_d)
                        >= kettles[-1] + p.kettle_d / 2)
                       if brew_wall == "front" else
                       (hy0 <= kettles[0] - p.kettle_d / 2
                        and hy0 + p.hood_w >= kettles[-1] + p.kettle_d / 2),
                       f"hood {p.hood_w:.0f} x {p.hood_d:.0f} in over the "
                       f"kettle row"))
        checks.append(("brewery: hood underside clears the lids (TEB 15 in)",
                       hz0 - kettle_top >= 12,
                       f"{hz0 - kettle_top:.0f} in gap, hood underside "
                       f"{hz0:.2f} in"))
        if brew_wall == "front":
            checks.append(("brewery: hood top stays under the front wall "
                           "(6 in duct exits through the header band)",
                           hz0 + p.hood_h <= e.front_top,
                           f"hood top {hz0 + p.hood_h:.2f} in vs wall "
                           f"{e.front_top:.1f} in"))
        else:
            checks.append(("brewery: hood top stays under the rake plate "
                           "at the hood's own y",
                           hz0 + p.hood_h <= e.roof_z(hy0 + p.hood_w),
                           f"hood top {hz0 + p.hood_h:.2f} in vs plate "
                           f"{e.roof_z(hy0 + p.hood_w):.1f} in at the back "
                           f"end of the hood"))
            dz0, dz1 = hz0 + p.hood_h, hz0 + p.hood_h + 6
            checks.append(("rake-wall duct exit clears the door head and "
                           "stays under the plate",
                           dz0 >= p.door_head + 0.4
                           and dz1 <= e.roof_z(hy0 + p.hood_w),
                           f"6 in duct at {dz0:.2f}-{dz1:.2f} in vs head "
                           f"{p.door_head:.0f} in and plate "
                           f"{e.roof_z(hy0 + p.hood_w):.1f} in"))
        checks.append(("kettle spacing on the stand (TEB 'comfortably')",
                       p.stand_w / 3 - p.kettle_d >= 3,
                       f"{p.stand_w / 3 - p.kettle_d:.1f} in between "
                       f"kettle bodies"))
        checks.append(("brewery: pumps gravity-fed under the stand",
                       p.pump_h < p.stand_h - 20,
                       "pumps on the floor under the kettle row"))

        # panel: on the wall the brewer can read/sidestep to
        if arrange in ("winner", "winner2"):
            pz0 = 50.0
            # front wall, WEST of the stand: clears the #1 kettle envelope
            # (its south edge sits 8.3 in off the wall, the panel protrudes
            # 9.125 - east of the stand the two would clip)
            px0, px1 = X1 - 40.0, X1 - 24.0
            box("panel", "control panel 30A", px0, px1, 0.0, p.panel_d,
                pz0, pz0 + p.panel_h, (90, 90, 140))
            checks.append(("panel on the front wall beside the stand, "
                           "clear of the kettle row, readable from the "
                           "brewery door",
                           px1 <= X1 - p.stand_d / 2 - p.kettle_d / 2 - 1.0
                           and pz0 >= 44 and px1 <= X1,
                           f"panel {px0:.0f}-{px1:.0f} in, bottom "
                           f"{pz0:.0f} in, clears the kettle row by "
                           f"{X1 - p.stand_d / 2 - p.kettle_d / 2 - px1:.1f} in; "
                           f"brewer reads it from the door, sidesteps the "
                           f"corner to operate (or mount it exterior - the "
                           f"enclosure is watertight)"))
        elif arrange == "runner-up":
            pz0 = 50.0
            px0, px1 = 96.5, 112.5              # pier between D1 and D2
            box("panel", "control panel 30A", px0, px1, 0.0, p.panel_d,
                pz0, pz0 + p.panel_h, (90, 90, 140))
            checks.append(("panel on the pier beside the brewery door, "
                           "readable from the brewer's station",
                           px1 <= st_x0 - 8 and pz0 >= 44,
                           f"panel {px0:.1f}-{px1:.1f} in on the "
                           f"{112.5 - px1 + 16:.0f} in pier, bottom "
                           f"{pz0:.0f} in (raised over the walk corridor)"))
        elif arrange == "old-front":
            pz0 = p.bike_h + 3.0
            px1 = 99.0 - 1.0
            box("panel", "control panel 30A", px1 - p.panel_w, px1, 0.0,
                p.panel_d, pz0, pz0 + p.panel_h, (90, 90, 140))
            brew["panel"] = (px1 - p.panel_w, px1, pz0, pz0 + p.panel_h)

    # ------------------------------------------------------------- blower,
    # as-designed modes only (cluster mode handled above)
    if arrange == "old-front":
        bl_x0, bl_x1 = X1 - p.blower_l, X1
        bl_y0, bl_y1 = rack_y0 + 0.5, rack_y0 + 0.5 + p.blower_w
        box("blower", "snow blower", bl_x0, bl_x1, bl_y0, bl_y1,
            0, p.blower_h, (200, 90, 60))
        blower = (bl_x0, bl_x1, bl_y0, bl_y1)
        checks.append(("blower re-parked beside the rack (pocket evicted)",
                       bl_x0 >= rxhi and bl_y1 <= Y1,
                       f"blower {bl_x0:.0f}-{bl_x1:.0f} x "
                       f"{bl_y0:.1f}-{bl_y1:.1f} in"))
        man_diag = math.hypot(X1 - rxhi, bl_y1 - p.stand_d)
        checks.append(("blower drag-out: corner zone diagonal carries its "
                       "length",
                       man_diag >= p.blower_l,
                       f"diagonal {man_diag:.0f} in vs blower "
                       f"{p.blower_l:.0f} in"))
        checks.append(("blower exits via the walk-in (bikes first)",
                       p.blower_w <= 36,
                       "drag + pivot + walk-in"))
    elif arrange == "old-baseline":
        cy = (8.5 + 44.5) / 2
        bl_y0, bl_y1 = cy - p.blower_w / 2, cy + p.blower_w / 2
        bl_x0, bl_x1 = X1 - p.blower_l, X1
        box("blower", "snow blower", bl_x0, bl_x1, bl_y0, bl_y1,
            0, p.blower_h, (200, 90, 60))
        blower = (bl_x0, bl_x1, bl_y0, bl_y1)
        checks.append(("blower centered on the right door",
                       bl_y0 >= 8.5 and bl_y1 <= 44.5,
                       f"blower {bl_y0:.0f}-{bl_y1:.0f} in vs door "
                       f"8.5-44.5 in"))
        checks.append(("blower rolls straight out the right door",
                       p.blower_w <= 36 and bl_x1 >= X1 - 1,
                       f"blower {p.blower_w:.0f} in vs door 36 in, nose at "
                       f"the wall"))

    # ------------------------------------------------------- free doors and
    # the roles that earn them (cluster modes)
    if arrange in ("winner", "winner2"):
        barn_lo = mx(0.0)
        barn_hi = mx(96.0)
        add_door("front", 0.0, 96.0,
                 "barn door 8 ft - bikes + blower straight roll")
        if arrange == "winner":
            add_door("front", 112.0, 148.0, "walk-in + slab feed 3 ft")
        else:
            # captain 2026-08-24: the LEFT rake-wall double is the MAIN
            # (primary pedestrian) door - closest to the garage/access.
            # Exact mirror of the right brewery double: same 6.5-70.5 span
            # on the 77 in wall, head 84, flagged 6.5 in end studs.
            add_door("left", 6.5, 70.5,
                     "main entry 64 in double - closest to garage/access")
    elif arrange == "runner-up":
        add_door("front", 0.0, 96.0,
                 "barn door 8 ft - bikes + blower straight roll")
        # y 28-64: clear of the brewery stand's east face (stand runs
        # y 0-26 against the front wall); the as-designed 8.5-44.5 span
        # would be half-blocked by the stand
        add_door("right", 28.0, 64.0, "walk-in + slab feed 3 ft")

    # ---------------------------------------------------------- door checks
    def span_overlap(a0, a1, b0, b1):
        return max(0.0, min(a1, b1) - max(a0, b0))

    if cluster:
        fdd = [(lo, hi) for w, lo, hi, hz, r in e.doors if w == "front"]
        d1 = max(fdd, key=lambda s: s[1] - s[0])
        ab = sorted((b["x0"], b["x1"]) for b in boxes if b["kind"] == "bike")
        ablb = next(b for b in boxes if b["kind"] == "blower")
        checks.append(("straight roll-out: bikes AND blower fit the barn "
                       "door with margin",
                       all(lo >= d1[0] + 2 and hi <= d1[1] - 2
                           for lo, hi in ab)
                       and ablb["x0"] >= d1[0] + 2
                       and ablb["x1"] <= d1[1] - 2,
                       f"bay {min(ab[0][0], ablb['x0']):.2f}-"
                       f"{max(ab[-1][1], ablb['x1']):.2f} in "
                       f"inside door {d1[0]:.0f}-{d1[1]:.0f} in (>= 2 in "
                       f"margin each side); back out {apron:.0f} in, roll "
                       f"straight"))
        checks.append(("bike exit: back out, roll straight (no turn)",
                       all(lo >= d1[0] and hi <= d1[1] for lo, hi in ab),
                       f"{p.bike_w:.0f} in bikes in a "
                       f"{d1[1] - d1[0]:.0f} in door"))
        checks.append(("blower exit: straight reverse-roll out the barn "
                       "door (Storm 2410 has reverse)",
                       ablb["x0"] >= d1[0] and ablb["x1"] <= d1[1],
                       f"blower {p.blower_w:.0f} in parked "
                       f"{Y1 - p.blower_l:.0f} in off the back wall"))

    if p.brewery and brew_wall and brew:
        dspan = brew.get("door") or brew["door_span"]
        if brew_wall == "right":
            k0 = kettles[0] - p.kettle_d / 2
            k1 = kettles[-1] + p.kettle_d / 2
            checks.append(("all three kettles inside the side-door span",
                           k0 >= dspan[0] and k1 <= dspan[1],
                           f"kettle bodies {k0:.1f}-{k1:.1f} in vs door "
                           f"{dspan[0]:.1f}-{dspan[1]:.1f} in "
                           f"({min(k0 - dspan[0], dspan[1] - k1):.1f} in "
                           f"tightest margin - the door is sized to the "
                           f"stand, not bigger)"))
        else:
            k0 = kettles[0] - p.kettle_d / 2
            k1 = kettles[-1] + p.kettle_d / 2
            checks.append(("all three kettles inside the brewery door span",
                           k0 >= dspan[0] and k1 <= dspan[1],
                           f"kettle bodies {k0:.1f}-{k1:.1f} in vs door "
                           f"{dspan[0]:.0f}-{dspan[1]:.0f} in"))

    # -------------------------------------------------------- access checks
    def clear(name, x0, x1, y0, y1, z0=0.0, z1=200.0, ignore=()):
        hits = [b["label"] for b in boxes
                if b["label"] not in ignore
                and b["x0"] < x1 - .5 and b["x1"] > x0 + .5
                and b["y0"] < y1 - .5 and b["y1"] > y0 + .5
                and b["z0"] < z1 - .5 and b["z1"] > z0 + .5]
        checks.append((name, not hits,
                       "clear" if not hits else "blocked by " + ", ".join(hits)))

    if arrange in ("winner", "winner2"):
        # all geometry here taken from the ACTUAL (post-mirror) boxes and
        # doors, so the mirror arrangement passes the identical checks
        fd = [(lo, hi) for w, lo, hi, hz, r in e.doors if w == "front"]
        barn = max(fd, key=lambda s: s[1] - s[0])
        ab = sorted((b["x0"], b["x1"]) for b in boxes if b["kind"] == "bike")
        abl = next(b for b in boxes if b["kind"] == "blower")
        ast = next(b for b in boxes if b["kind"] == "stand")
        cl_a0 = min(ab[0][0], abl["x0"])
        cl_a1 = max(ab[-1][1], abl["x1"])
        asl = [b for b in boxes if b["kind"] == "slab"]
        ar0 = min(b["x0"] for b in asl)
        ar1 = max(b["x1"] for b in asl)
        if arrange == "winner":
            walk = next((lo, hi) for w, lo, hi, hz, r in e.doors
                        if w == "front" and hi - lo <= 48)
            clear("pedestrian entry kept: walk-in landing clear",
                  walk[0], walk[1], 0, 30, 0, 48.0)
            clear("slab feed corridor to the walk-in clear",
                  walk[0], walk[1], 0, rack_y0, 0, 48.0)
            face = max(cl_a0 - ar0, ar1 - cl_a1)   # gap beside the walk-in
            face_note = (f"slabs carried on edge through the 3 ft door")
        else:
            # winner2 + captain 2026-08-24: walk-in REMOVED; the LEFT
            # rake-wall double is the MAIN pedestrian door (closest to the
            # garage/access); slab loading stays with the 8 ft barn door.
            # The checks below are the left-door sanity suite the
            # winner-render scout validated (firstmate data/
            # shed-blender-winner/report.md).
            mw, mlo, mhi = next((w, lo, hi) for w, lo, hi, hz, r in e.doors
                                if r.startswith("main entry"))
            checks.append(("pedestrian entry through the left MAIN door "
                           "(captain 2026-08-24, closest to garage/access)",
                           mhi - mlo >= 36,
                           f"{mhi - mlo:.0f} in double vs a 36 in "
                           f"pedestrian minimum; {mw} wall "
                           f"{mlo:.1f}-{mhi:.1f} in"))
            checks.append(("main-door rake-wall end studs survive the "
                           "opening (flagged, not engineered)",
                           mlo >= p.min_end_stud
                           and Y1 - mhi >= p.min_end_stud,
                           f"{mlo:.1f} in at the front end, "
                           f"{Y1 - mhi:.1f} in at the back end of the "
                           f"{Y1:.0f} in wall (min {p.min_end_stud:.0f}) - "
                           f"the same flagged 6.5 in rule as the brewery "
                           f"double"))
            flank = cl_a0 if mw == "left" else X1 - cl_a1
            checks.append(("main door outswing: leaves stay exterior, no "
                           "swing clash with the cluster flank",
                           flank >= p.min_end_stud,
                           f"cluster flank stands {flank:.2f} in off the "
                           f"{mw} wall; every door in the study outswings, "
                           f"so the leaf envelopes never cross the wall "
                           f"plane"))
            if mw == "left":
                clear("main-door entry landing clear (headroom to 48 in)",
                      0.0, cl_a0, mlo, min(mhi, rack_y0), 0, 48.0)
            else:
                clear("main-door entry landing clear (headroom to 48 in)",
                      cl_a1, X1, mlo, min(mhi, rack_y0), 0, 48.0)
            clear("pedestrian path: maneuver floor off the entry clear "
                  "(headroom to 48 in)",
                  cl_a1, ast["x0"], 0, rack_y0, 0, 48.0)
            checks.append(("slab carry through the barn door: opening "
                           "carries slab on edge + carrier",
                           barn[1] - barn[0] >= p.slab_w + 18,
                           f"{barn[1] - barn[0]:.0f} in barn door vs slab "
                           f"{p.slab_w:.0f} in + 18 in carrier"))
            face = ar1 - cl_a1     # rack face east of the cluster
            face_note = (f"slabs carried on edge through the barn door, "
                         f"fed at the east face of the run")
        checks.append(("slab corridor depth carries slab width + carrier",
                       rack_y0 >= p.slab_w + 18,
                       f"aisle {rack_y0:.0f} in vs slab {p.slab_w:.0f} in "
                       f"+ 18 in carrier"))
        checks.append(("slab feed: rack face reachable from the entry "
                       "(as-designed precedent >= 21 in)",
                       face - 3.5 >= 21,
                       f"{face:.2f} in of the {p.slab_len:.0f} in run not "
                       f"parked over, minus the 3.5 in end upright -> "
                       f"{face - 3.5:.2f} in; {face_note}"))
        clear("circulation kept: apron in front of the cluster",
              cl_a0, cl_a1, 0, bike_y0)
        gap = max(ast["x0"] - cl_a1, cl_a0 - ast["x1"])
        checks.append(("turn/maneuver floor between the cluster and the "
                       "stand carries a bike length",
                       math.hypot(gap, rack_y0) >= p.bike_l,
                       f"open floor {gap:.2f} in x {rack_y0:.0f} in aisle, "
                       f"diagonal {math.hypot(gap, rack_y0):.0f} in vs "
                       f"bike {p.bike_l:.0f} in"))
    elif arrange == "runner-up":
        wx0 = max(bikes[-1][1], bl_x0 + p.blower_w)
        st_w = X1 - p.stand_w
        # L-shaped landing: along the door (clear of the stand) and into
        # the aisle (clear of the rack, whose uprights start at y 50)
        clear("pedestrian entry kept: walk-in landing clear (door side)",
              st_w, X1, 28.0, 64.0, 0, 48.0)
        clear("pedestrian entry kept: walk-in landing clear (aisle side)",
              wx0, st_w, 28.0, rack_y0, 0, 48.0)
        clear("slab feed corridor from the right-wall walk-in clear",
              wx0, st_w, 28.0, rack_y0, 0, 48.0)
        checks.append(("slab corridor depth carries slab width + carrier",
                       rack_y0 >= p.slab_w + 18,
                       f"aisle {rack_y0:.0f} in vs slab {p.slab_w:.0f} in "
                       f"+ 18 in carrier"))
        face = rxhi - wx0
        checks.append(("slab feed: rack face reachable from the walk-in "
                       "(as-designed precedent >= 21 in)",
                       face - 3.5 >= 21,
                       f"{face - 3.5:.2f} in of face, slabs carried on "
                       f"edge through the right-wall door"))
        clear("circulation kept: apron in front of the cluster",
              0, 96.0, 0, bike_y0)
        clear("circulation kept: passage between cluster and brewery "
              "pier", 96.0, 113.0, 0, rack_y0, 0, 48.0)
    elif old_front:
        walk = (15.5, 51.5)
        pnl_z = brew["panel"][2] if brew and "panel" in brew else 200.0
        clear("pedestrian entry kept: walk-in landing clear",
              walk[0], walk[1], 0, 30)
        feed_face = min(walk[1], rxhi) - max(walk[0], rxlo)
        checks.append(("slab feed at the walk-in span",
                       feed_face >= 24,
                       f"{feed_face:.0f} in of rack face"))
        clear("slab feed corridor to the walk-in clear",
              walk[0], walk[1], 0, rack_y0)
        clear("circulation kept: west aisle", 0, bikes[0][0], 0, rack_y0)
        clear("circulation kept: apron in front of the bikes (under the "
              "panel overhang)",
              0, brew["st_x0"] if brew else X1, 0, bike_y0, 0, pnl_z)
        if brew:
            clear("circulation kept: passage east of the stand",
                  brew["st_x1"], X1, 0, rack_y0, 0, brew["hood_z0"])
            checks.append(("turn space west of the stand carries bike AND "
                           "blower",
                           math.hypot(brew["st_x0"], rack_y0)
                           >= max(p.bike_l, p.blower_l),
                           f"diagonal {math.hypot(brew['st_x0'], rack_y0):.0f} in"))
            checks.append(("bike exit via the walk-in",
                           p.bike_w <= 36, "back out, turn, roll"))
            clear("bike backing lanes clear under the panel overhang",
                  bikes[0][0], bikes[-1][1], 0, bike_y0, 0, pnl_z)
    elif arrange == "old-baseline":
        clear("pedestrian entry kept: walk-in landing clear",
              15.5, 51.5, 0, 30)
        feed_diag = math.hypot(bl_x0, rack_y0)
        checks.append(("slab feed kept: open aisle rotates a slab on edge",
                       feed_diag >= p.slab_len,
                       f"diagonal {feed_diag:.0f} in vs slab "
                       f"{p.slab_len:.0f} in"))
        infeed = span_overlap(99.0, 171.0, rxlo, rxhi)
        checks.append(("rack face directly behind the double door",
                       infeed >= 12, f"{infeed:.0f} in"))
        clear("circulation kept: corridor between bike bay and blower",
              bikes[-1][1], bl_x0, 0, rack_y0)
        clear("bike backing lanes clear", bikes[0][0], bikes[-1][1], 0,
              bike_y0)
        checks.append(("turn space diagonal carries a bike length",
                       math.hypot(bl_x0, rack_y0) >= p.bike_l,
                       f"{math.hypot(bl_x0, rack_y0):.0f} in"))

    # ------------------------------------------- piers / framing consequences
    if arrange in ("winner", "runner-up"):
        front_doors = sorted([(lo, hi) for w, lo, hi, hz, r in e.doors
                              if w == "front"])
        piers = []
        prev = 0.0
        for lo, hi in front_doors:
            piers.append(lo - prev)
            prev = hi
        piers.append(X1 - prev)
        ok = all(w >= p.min_pier or w <= 0.01 for w in piers[1:-1])
        checks.append(("front-wall piers between/beside openings "
                       "(concept min 10 in, flagged not engineered)",
                       ok,
                       " / ".join(f"{w:.0f} in" for w in piers)))
        if arrange == "runner-up":
            checks.append(("east corner door: header bears on the corner "
                           "post (CONSEQUENCE NOTE, not a blocker)",
                           front_doors[-1][1] >= X1 - 0.01,
                           "the 72 in brewery door runs to the east corner; "
                           "re-frame with a built-up corner post"))
        checks.append(("barn door runs from a corner (CONSEQUENCE NOTE, "
                       "not a blocker)",
                       front_doors[0][0] <= 0.01
                       or front_doors[-1][1] >= X1 - 0.01,
                       "the 96 in opening starts at a corner post; "
                       "re-frame that corner as a header-bearing post"))

    # ------------------------------------------------------- envelope check
    checks.append(("every item inside the interior",
                   all(0 <= b["x0"] and b["x1"] <= X1 + .01
                       and 0 <= b["y0"] and b["y1"] <= Y1 + .01
                       and b["z1"] <= e.roof_z((b["y0"] + b["y1"]) / 2)
                       for b in boxes),
                   "footprints and heights vs walls and roof underside"))

    # ------------------------------------------------- pairwise 3-D overlap
    for b in boxes:
        for c in boxes:
            if (c is b or b["label"] >= c["label"]
                    or b["kind"] == c["kind"] == "rack"
                    or {b["kind"], c["kind"]} <= {"stand", "pump"}):
                continue
            ov = (b["x0"] < c["x1"] - .5 and b["x1"] > c["x0"] + .5
                  and b["y0"] < c["y1"] - .5 and b["y1"] > c["y0"] + .5
                  and b["z0"] < c["z1"] - .5 and b["z1"] > c["z0"] + .5)
            checks.append((f"no overlap: {b['label']} / {c['label']}",
                           not ov, ""))

    info = dict(aisle=aisle_y, apron=apron, rack_x0=rxlo, rack_x1=rxhi,
                rack_y0=rack_y0, top_of_stack=top_of_stack,
                underside=underside, blower=blower, bikes=bikes,
                bike_y0=bike_y0, brewery=p.brewery and brew_wall,
                brew=brew, arrange=arrange, mirror=mirror,
                cluster=cluster, posts=up)
    return boxes, checks, info


def door_roles(e, boxes, info):
    lines = ["Door roles (as parked, every door earns its place):"]
    for w, lo, hi, hz, role in e.doors:
        hits = []
        for b in boxes:
            if b["kind"] in ("rack", "hood", "panel"):
                # rack = wall furniture, hood = overhead air, panel =
                # wall-mounted 4 ft up (a door can pass under it)
                continue
            if w == "front":
                ov = span = (min(b["x1"], hi) - max(b["x0"], lo)) \
                    if b["y0"] < 36 else 0.0
            elif w == "right":
                ov = (min(b["y1"], hi) - max(b["y0"], lo)) \
                    if b["x1"] > e.x1 - 36 else 0.0
            else:
                ov = (min(b["y1"], hi) - max(b["y0"], lo)) \
                    if b["x0"] < 36 else 0.0
            if ov > 1.0:
                hits.append((b["label"], ov))
        occ = ", ".join(f"{n.split(' (')[0]} ({ov:.0f} in)"
                        for n, ov in hits) if hits else "clear"
        lines.append(f"  {w} wall {lo:.1f}-{hi:.1f} in ({hi - lo:.0f} in, "
                     f"head {hz:.0f}): {role} | parked: {occ}")
    return lines


# --------------------------------------------------------------- build123d

def build_scene(p, e, boxes):
    from build123d import Align, Box, Location, Plane, Polygon, Pos, extrude
    CENTER3 = (Align.CENTER, Align.CENTER, Align.CENTER)
    IN = 25.4
    parts = []

    def mkb(x0, x1, y0, y1, z0, z1, label, color, alpha=1.0):
        part = Location(((x0 + x1) / 2 * IN, (y0 + y1) / 2 * IN,
                         (z0 + z1) / 2 * IN), (0, 0, 0)) * Box(
            (x1 - x0) * IN, (y1 - y0) * IN, (z1 - z0) * IN, align=CENTER3)
        part.label = label
        part.color = tuple(c / 255 for c in color) + (alpha,)
        parts.append(part)

    t, X1, Y1 = e.wall_t, e.x1, e.y1
    mkb(e.x0 - t, X1 + t, e.y0 - t, Y1 + t, -0.75, 0, "deck", (196, 180, 148))
    segs = [e.x0 - t]
    for w, lo, hi, hz, r in sorted(e.doors, key=lambda d: d[1]):
        if w == "front":
            segs += [lo, hi]
    segs += [X1 + t]
    for a, b in zip(segs[::2], segs[1::2]):
        mkb(a, b, e.y0 - t, e.y0, 0, e.front_top, "front wall",
            (222, 214, 198))
    for w, lo, hi, hz, r in e.doors:
        if w == "front":
            mkb(lo, hi, e.y0 - t, e.y0, hz, e.front_top, "front header",
                (222, 214, 198))
    mkb(e.x0 - t, X1 + t, Y1, Y1 + t, 0, e.back_top, "back wall",
        (222, 214, 198))
    for side_x0, side_x1 in ((e.x0 - t, e.x0), (X1, X1 + t)):
        prof = [(e.y0 - t, 0), (Y1 + t, 0)]
        prof += [(y, max(0.0, e.roof_z(y))) for y in (Y1 + t, e.y0 - t)]
        plane = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        sk = plane * Polygon(*[(y * IN, z * IN) for y, z in prof])
        part = Pos(side_x0 * IN, 0, 0) * extrude(sk,
                                                 amount=(side_x1 - side_x0) * IN)
        part.label = "side wall"
        part.color = (222 / 255, 214 / 255, 198 / 255, 1.0)
        parts.append(part)
    y0r, y1r = e.y0 - 6.0, Y1 + 6.0
    prof = [(y0r, e.roof_z(y0r)), (y1r, e.roof_z(y1r)),
            (y1r, e.roof_z(y1r) + 7.0), (y0r, e.roof_z(y0r) + 7.0)]
    plane = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    sk = plane * Polygon(*[(y * IN, z * IN) for y, z in prof])
    part = Pos((e.x0 - 6.0) * IN, 0, 0) * extrude(sk,
                                                  amount=(X1 - e.x0 + 12) * IN)
    part.label = "roof"
    part.color = (127 / 255, 168 / 255, 201 / 255, 0.35)
    parts.append(part)

    for b in boxes:
        mkb(b["x0"], b["x1"], b["y0"], b["y1"], b["z0"], b["z1"],
            b["label"], b["color"], b.get("alpha", 1.0))
    return parts


# ------------------------------------------------------------------ render

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def fmt_ftin(v):
    ft, inch = divmod(int(round(v)), 12)
    if ft == 0:
        return f"{inch} in"
    return f"{ft}'{inch:02d}\"" if inch else f"{ft} ft"


class Fig:
    def __init__(self, w, h, title, note):
        from PIL import Image, ImageDraw, ImageFont
        self.img = Image.new("RGB", (w, h), (246, 244, 239))
        self.d = ImageDraw.Draw(self.img)
        self.fT = ImageFont.truetype(FONT_B, 30)
        self.fL = ImageFont.truetype(FONT_R, 22)
        self.fS = ImageFont.truetype(FONT_R, 18)
        self.d.rectangle([8, 8, w - 8, h - 8], outline=(60, 55, 45), width=3)
        self.d.text((24, 20), title, font=self.fT, fill=(40, 36, 28))
        self.d.text((24, 58), note, font=self.fS, fill=(90, 84, 72))

    def legend(self, x, y, entries):
        for i, (name, col) in enumerate(entries):
            yy = y + i * 30
            self.d.rectangle([x, yy, x + 24, yy + 22], fill=col,
                             outline=(60, 55, 45))
            self.d.text((x + 32, yy - 2), name, font=self.fL,
                        fill=(40, 36, 28))

    def dim_h(self, x0, x1, y, label, up=True):
        d, s = self.d, 6 if up else -6
        d.line([x0, y, x1, y], fill=(40, 36, 28), width=2)
        for x, dx in ((x0, 1), (x1, -1)):
            d.line([x, y, x + 8 * dx, y - 5], fill=(40, 36, 28), width=2)
            d.line([x, y, x + 8 * dx, y + 5], fill=(40, 36, 28), width=2)
        w = self.fS.getlength(label)
        d.rectangle([(x0 + x1) / 2 - w / 2 - 4, y - 24, (x0 + x1) / 2 +
                     w / 2 + 4, y - 2], fill=(246, 244, 239))
        d.text(((x0 + x1) / 2 - w / 2, y - 25), label, font=self.fS,
               fill=(40, 36, 28))

    def dim_v(self, x, y0, y1, label, right=True, bg=False):
        d = self.d
        d.line([x, y0, x, y1], fill=(40, 36, 28), width=2)
        for y, dy in ((y0, 1), (y1, -1)):
            d.line([x, y, x - 5, y + 8 * dy], fill=(40, 36, 28), width=2)
            d.line([x, y, x + 5, y + 8 * dy], fill=(40, 36, 28), width=2)
        t = self.fS.getlength(label)
        tx = x + 8 if right else x - 8 - self.fS.getlength(label)
        if bg:
            d.rectangle([tx - 3, (y0 + y1) / 2 - 11, tx + t + 3,
                         (y0 + y1) / 2 + 11], fill=(246, 244, 239))
        d.text((tx, (y0 + y1) / 2 - 9), label, font=self.fS,
               fill=(40, 36, 28))


def legend_entries(p, brew_wall):
    ent = [("e-bikes (floor-parked)", (70, 130, 180)),
           ("snow blower", (200, 90, 60)),
           ("cherry slabs", (166, 98, 66)), ("slab rack", (130, 130, 135))]
    if brew_wall:
        ent += [("brew stand (permanent)", (120, 85, 60)),
                ("20-gal kettles x3", (185, 190, 195)),
                ("control panel 30A", (90, 90, 140)),
                ("condensate hood (overhead)", (150, 150, 155))]
    ent.append(("shed shell", (222, 214, 198)))
    return ent


def render_plan(p, e, boxes, info, out):
    W, H = 1700, 1150
    arrange, brew = info["arrange"], info["brewery"]
    tag = {"winner": "PROPOSED (free doors) — ",
           "winner2": "ADOPTED PLAN (barn + left MAIN + right brewery) — ",
           "runner-up": "RUNNER-UP (free doors) — ",
           "old-front": "AS-DESIGNED DOORS — ",
           "old-baseline": "BASELINE (as-designed doors, no brewery) — "}
    fig = Fig(W, H,
              f"{tag[arrange]}PLAN — storage + permanent brewery, "
              f"{fmt_ftin(e.outer_depth)} deep, viewed from above",
              "front wall at the bottom · left wall at the left · rack "
              f"underside {fmt_ftin(p.rack_clear)}: bikes AND blower nose "
              "in under the slab run · brewer works from OUTSIDE"
              + (f" the {brew} wall door" if brew else ""))
    d = fig.d
    t, X1, Y1 = e.wall_t, e.x1, e.y1
    s = min(7.0, (H - 370) / (Y1 + 2 * t + 14))
    ox, oy = 120, H - 200

    def X(x):
        return ox + x * s

    def Y(y):
        return oy - y * s

    d.rectangle([X(-t), Y(Y1 + t), X(X1 + t), Y(-t)], fill=(210, 200, 180),
                outline=(60, 55, 45), width=2)
    order = {"slab": 0, "rack": 1, "stand": 2, "pump": 3, "kettle": 4,
             "blower": 5, "bike": 6, "panel": 7}
    for b in sorted(boxes, key=lambda b: order.get(b["kind"], 9)):
        if b["kind"] == "rack":
            d.rectangle([X(b["x0"]), Y(b["y1"]), X(b["x1"]), Y(b["y0"])],
                        fill=None, outline=b["color"], width=3)
        elif b["kind"] == "hood":
            continue
        elif b["kind"] == "kettle":
            d.ellipse([X(b["x0"]), Y(b["y1"]), X(b["x1"]), Y(b["y0"])],
                      fill=b["color"], outline=(40, 36, 28), width=2)
        else:
            d.rectangle([X(b["x0"]), Y(b["y1"]), X(b["x1"]), Y(b["y0"])],
                        fill=b["color"], outline=(40, 36, 28), width=2)
    # walls
    d.rectangle([X(-t), Y(0), X(X1 + t), Y(-t)], fill=(222, 214, 198),
                outline=(60, 55, 45), width=2)
    d.rectangle([X(-t), Y(Y1 + t), X(X1 + t), Y(Y1)], fill=(222, 214, 198),
                outline=(60, 55, 45), width=2)
    d.rectangle([X(-t), Y(Y1), X(0), Y(0)], fill=(222, 214, 198),
                outline=(60, 55, 45), width=2)
    d.rectangle([X(X1), Y(Y1), X(X1 + t), Y(0)], fill=(222, 214, 198),
                outline=(60, 55, 45), width=2)
    # door gaps + red swing lines + role labels
    for w, lo, hi, hz, role in e.doors:
        short = role.split(" - ")[0]
        if w == "front":
            d.rectangle([X(lo), Y(0), X(hi), Y(-t)], fill=(246, 244, 239),
                        outline=(60, 55, 45), width=2)
            d.line([X(lo), Y(-t / 2), X(hi), Y(-t / 2)], fill=(200, 60, 60),
                   width=3)
            tw = fig.fS.getlength(short)
            d.text(((X(lo) + X(hi)) / 2 - tw / 2, Y(-t) + 26), short,
                   font=fig.fS, fill=(200, 60, 60))
        else:
            xx = X1 if w == "right" else 0
            d.rectangle([X(xx), Y(hi), X(xx + t), Y(lo)],
                        fill=(246, 244, 239), outline=(60, 55, 45), width=2)
            d.line([X(xx + t / 2), Y(lo), X(xx + t / 2), Y(hi)],
                   fill=(200, 60, 60), width=3)
            if w == "right":
                words = short.split(" ")
                l1, l2 = " ".join(words[:2]), " ".join(words[2:])
                d.text((X(X1 + t) + 10, (Y(lo) + Y(hi)) / 2 + 50), l1,
                       font=fig.fS, fill=(200, 60, 60))
                d.text((X(X1 + t) + 10, (Y(lo) + Y(hi)) / 2 + 72), l2,
                       font=fig.fS, fill=(200, 60, 60))
            else:
                d.text((X(-t) - 10 - fig.fS.getlength(short),
                        (Y(lo) + Y(hi)) / 2 - 27), short, font=fig.fS,
                       fill=(200, 60, 60))
    # item labels
    if info["cluster"]:
        bl = info["blower"]
        cx = X((bl[0] + bl[1]) / 2)
        cy = Y(Y1 - p.blower_l / 2)
        for i, ln in enumerate(["blower", "(nose-in)"]):
            tw = fig.fL.getlength(ln)
            d.text((cx - tw / 2, cy - 13 + 24 * i), ln, font=fig.fL,
                   fill=(255, 255, 255))
        bcx = X((info["bikes"][0][0] + info["bikes"][-1][1]) / 2)
        for i, ln in enumerate(["e-bikes (nose-in)", "under the slabs"]):
            tw = fig.fL.getlength(ln)
            d.text((bcx - tw / 2, Y(Y1 - p.bike_l / 2) - 13 + 24 * i), ln,
                   font=fig.fL, fill=(255, 255, 255))
        d.text((X(100.0) + 6, Y(e.y1 - 4)), "slab rack",
               font=fig.fS, fill=(255, 255, 255))
        d.text((X(100.0) + 6, Y(e.y1 - 4) + 22),
               f"stack top {fmt_ftin(info['top_of_stack'])}",
               font=fig.fS, fill=(255, 255, 255))
    else:
        lbl = {
            "snow blower": (["snow blower"] +
                            (["exit: drag + pivot,", "out the walk-in"]
                             if arrange == "old-front"
                             else ["out the right door"]), None),
            "cherry slab 1": ([f"{p.slab_count} cherry slabs",
                               f"stack top {fmt_ftin(info['top_of_stack'])}"],
                              (26.0, e.y1 - 14)),
            "bike 1 (nose-in)": (["e-bikes (nose-in)",
                                  "tucked under the slabs"], None),
        }
        for b in boxes:
            if b["label"] in lbl:
                lines, anchor = lbl[b["label"]]
                cx = X(anchor[0]) if anchor else (X(b["x0"]) + X(b["x1"])) / 2
                cy = Y(anchor[1]) if anchor else (Y(b["y0"]) + Y(b["y1"])) / 2
                for i, text in enumerate(lines):
                    tw = fig.fL.getlength(text)
                    d.text((cx - tw / 2, cy - 26 + 26 * i), text,
                           font=fig.fL, fill=(255, 255, 255)
                           if b["kind"] != "rack" else (70, 65, 55))
        d.text((X(info["rack_x0"] + 20), Y(e.y1 - 4)), "slab rack",
               font=fig.fS, fill=(255, 255, 255))
    if brew:
        b = info["brew"]
        hb = next(x for x in boxes if x["kind"] == "hood")
        pts = [(X(hb["x0"]), Y(hb["y0"])), (X(hb["x1"]), Y(hb["y0"])),
               (X(hb["x1"]), Y(hb["y1"])), (X(hb["x0"]), Y(hb["y1"]))]
        for i in range(4):
            d.line([pts[i], pts[(i + 1) % 4]], fill=(90, 85, 75), width=3,
                   joint="curve")
        scx = (X(b["st_x0"]) + X(b["st_x1"])) / 2
        scy = (Y(info.get("rack_y0", p.stand_d) and p.stand_d) + Y(0)) / 2 \
            if b["wall"] == "front" else Y((Y1) / 2)
        lab1 = "brew stand + 3 kettles — PERMANENT"
        if b["wall"] == "front":
            d.text((scx - fig.fL.getlength(lab1) / 2, Y(p.stand_d) + 10),
                   lab1, font=fig.fL, fill=(70, 65, 55))
            d.text((scx - fig.fS.getlength("pumps under · panel on the "
                                           "pier") / 2, Y(p.stand_d) + 36),
                   "pumps under · panel on the pier", font=fig.fS,
                   fill=(70, 65, 55))
        else:
            d.text((X(e.x1 - p.stand_d) - 330, scy - 40), lab1,
                   font=fig.fL, fill=(70, 65, 55))
            d.text((X(e.x1 - p.stand_d) - 330, scy - 14),
                   "pumps under · panel on the front wall beside the stand",
                   font=fig.fS, fill=(70, 65, 55))
        # brewer marker outside the brewery door
        bd = b.get("door") or b["door_span"]
        if b["wall"] == "front":
            bx = (X(bd[0]) + X(bd[1])) / 2
            by = Y(-13)
            for dx in (-34, 34):
                d.ellipse([bx + dx - 11, by - 11, bx + dx + 11, by + 11],
                          fill=(120, 60, 120), outline=(40, 36, 28), width=2)
            lab = "BREWER STANDS OUTSIDE — kettles 13 in past the threshold"
            d.text((bx - fig.fL.getlength(lab) / 2, by + 18), lab,
                   font=fig.fL, fill=(120, 60, 120))
        else:
            by = (Y(bd[0]) + Y(bd[1])) / 2
            bx = X(X1 + 13)
            for dy in (-34, 34):
                d.ellipse([bx - 11, by + dy - 11, bx + 11, by + dy + 11],
                          fill=(120, 60, 120), outline=(40, 36, 28), width=2)
            lab = "BREWER STANDS OUTSIDE the rake-wall door"
            cx = (X(0) + X(X1)) / 2
            d.text((cx - fig.fL.getlength(lab) / 2, Y(-t) + 90), lab,
                   font=fig.fL, fill=(120, 60, 120))
            d.text((cx - fig.fS.getlength("kettle centers 13 in past the "
                   "plane") / 2, Y(-t) + 118), "kettle centers 13 in "
                   "past the plane", font=fig.fS, fill=(120, 60, 120))
    # dims
    fig.dim_h(X(info["rack_x0"]), X(info["rack_x1"]), Y(Y1 + t) - 14,
              f"slabs {fmt_ftin(p.slab_len)}")
    fig.dim_h(X(0), X(X1), Y(Y1 + t) - 40,
              f"interior length {fmt_ftin(X1)}")
    fig.dim_v(X(-t) - 60, Y(0), Y(Y1),
              f"interior depth {fmt_ftin(Y1)}", right=True)
    fig.dim_v(X(100.0), Y(0), Y(info["rack_y0"]),
              f"aisle {fmt_ftin(info['aisle'])}", right=True)
    fig.dim_v(X(96.0), Y(info["bike_y0"]), Y(e.y1),
              f"bikes {fmt_ftin(p.bike_l)}", right=True)
    lab = f"tails {fmt_ftin(info['apron'])} off the front wall"
    tw = fig.fS.getlength(lab)
    tx = (X(info["bikes"][0][0]) + X(info["bikes"][-1][1])) / 2 - tw / 2
    d.rectangle([tx - 4, Y(0) - 26, tx + tw + 4, Y(0) - 4],
                fill=(246, 244, 239))
    d.text((tx, Y(0) - 24), lab, font=fig.fS, fill=(70, 65, 55))
    fig.legend(W - 400, 110, legend_entries(p, brew))
    fig.img.save(out)


def render_iso(p, e, boxes, info, out):
    W, H = 1700, 1150
    tag = {"winner": "PROPOSED (free doors) — ",
           "winner2": "ADOPTED PLAN (barn + left MAIN + right brewery) — ",
           "runner-up": "RUNNER-UP (free doors) — ",
           "old-front": "AS-DESIGNED DOORS — ",
           "old-baseline": "BASELINE — "}[info["arrange"]]
    fig = Fig(W, H, f"{tag}ISO — storage jenga + brewery inside the "
              "concept shed",
              "LIFTED slab rack over the wheeled cluster · the permanent "
              f"brewery on the {info['brew'] and info['brew']['wall'] or '—'} "
              "wall · front and right faces opened")
    d = fig.d
    yaw, pitch = math.radians(35), math.radians(20)
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), \
        math.sin(pitch)

    def proj(x, y, z):
        x1 = x * cy - y * sy
        y1 = x * sy + y * cy
        return (x1, y1 * cp - z * sp, y1 * sp + z * cp)

    t, X1, Y1 = e.wall_t, e.x1, e.y1
    faces = []
    walls = {
        "back": (-t, X1 + t, Y1, Y1 + t, 0, e.back_top),
        "left": (-t, 0, -t, Y1 + t, 0, e.roof_z(Y1 + t)),
    }
    for (x0, x1, y0, y1, z0, z1) in walls.values():
        faces += box_faces(x0, x1, y0, y1, z0, z1, (222, 214, 198), keep=
                           {"back": ("top", "front"), "left": ("top", "right")})
    faces += box_faces(-t, X1 + t, -t, Y1 + t, -0.75, 0, (196, 180, 148),
                       keep=("top",))
    for b in boxes:
        a = b.get("alpha", 1.0)
        col = tuple(int(c * a + 246 * (1 - a)) for c in b["color"])
        faces += box_faces(b["x0"], b["x1"], b["y0"], b["y1"], b["z0"],
                           b["z1"], col)
    pts = [proj(*pt) for f in faces for pt in f[0]]
    xs = [q[0] for q in pts]
    zs = [q[1] for q in pts]
    s = min((W - 260) / (max(xs) - min(xs)), (H - 220) / (max(zs) - min(zs)))
    mx, mz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2

    def P2(q):
        return (W / 2 + (q[0] - mx) * s, H / 2 - (q[1] - mz) * s + 30)

    LIGHT = (0.45, -0.5, 0.74)
    drawn = []
    for fpts, col in faces:
        pp = [proj(*q) for q in fpts]
        depth = sum(q[2] for q in pp) / len(pp)
        n = face_normal(fpts)
        lam = max(0.0, sum(a * b for a, b in zip(n, LIGHT)))
        b_ = 0.6 + 0.4 * lam
        drawn.append((depth, [P2(q) for q in pp],
                      tuple(int(c * b_) for c in col)))
    for _, scr, col in sorted(drawn, key=lambda t_: t_[0]):
        d.polygon(scr, fill=col, outline=(40, 36, 28))
    fig.legend(W - 400, H - 330, legend_entries(p, info["brewery"]))
    fig.img.save(out)


def box_faces(x0, x1, y0, y1, z0, z1, col, keep=None):
    F = {
        "bottom": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        "top": [(x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)],
        "front": [(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)],
        "back": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "left": [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        "right": [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
    }
    if keep:
        F = {k: v for k, v in F.items() if k in keep}
    return [(v, col) for v in F.values()]


def face_normal(pts):
    ax, ay, az = pts[0]
    bx, by, bz = pts[1]
    cx, cy_, cz = pts[2]
    u = (bx - ax, by - ay, bz - az)
    v = (cx - ax, cy_ - ay, cz - az)
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    l = math.sqrt(sum(c * c for c in n)) or 1
    return tuple(c / l for c in n)


def render_section(p, e, boxes, info, out):
    brew = info["brewery"]
    b = info["brew"]
    W, H = 1700, 1150
    if brew and b["wall"] == "right":
        # cut across the middle kettle: y = const, looking toward the back
        cut = b["kettles"][1]
        fig = Fig(W, H,
                  "SECTION A-A — the permanent brewery on the RIGHT wall",
                  f"cut across the middle kettle · looking toward the back "
                  "wall · west cluster under the lifted rack at left · the "
                  "6 in duct leaves the rake wall OVER the door head")
        d = fig.d
        t, X1, Y1 = e.wall_t, e.x1, e.y1
        s = min((H - 330) / (e.front_top + 15), (W - 900) / (X1 + 2 * t))
        ox, oy = 330, H - 170

        def Xh(x):
            return ox + x * s

        def Z(z):
            return oy - z * s

        plate = e.roof_z(cut)
        d.rectangle([Xh(-t), Z(0), Xh(X1 + t), Z(-0.75)],
                    fill=(196, 180, 148), outline=(60, 55, 45), width=2)
        # left wall stub (with the main-door head when the cut crosses it),
        # right wall with the brewery-door head
        main = next(((lo, hi) for w, lo, hi, hz, r in e.doors
                     if r.startswith("main entry")), None)
        if main and main[0] < cut < main[1]:
            d.rectangle([Xh(-t), Z(plate), Xh(0), Z(p.door_head)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
            d.line([Xh(-t), Z(p.door_head), Xh(0), Z(p.door_head)],
                   fill=(200, 60, 60), width=3)
            d.text((Xh(0) + 14, Z(p.door_head) + 10),
                   f"main door head {fmt_ftin(p.door_head)}", font=fig.fS,
                   fill=(200, 60, 60))
        else:
            d.rectangle([Xh(-t), Z(plate), Xh(0), Z(0)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
        in_door = b["door_span"][0] < cut < b["door_span"][1] \
            or b.get("door") and b["door"][0] < cut < b["door"][1]
        if in_door:
            d.rectangle([Xh(X1), Z(plate), Xh(X1 + t), Z(p.door_head)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
            d.line([Xh(X1), Z(p.door_head), Xh(X1 + t), Z(p.door_head)],
                   fill=(200, 60, 60), width=3)
            d.text((Xh(X1) - 260, Z(p.door_head) + 10),
                   f"door head {fmt_ftin(p.door_head)}", font=fig.fS,
                   fill=(200, 60, 60))
        else:
            d.rectangle([Xh(X1), Z(plate), Xh(X1 + t), Z(0)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
        # roof at the cut
        d.rectangle([Xh(-t - 6), Z(plate + 7), Xh(X1 + t + 6), Z(plate)],
                    fill=(127, 168, 201), outline=(60, 55, 45))
        # cut items
        for bx in boxes:
            if bx["y0"] < cut < bx["y1"]:
                d.rectangle([Xh(bx["x0"]), Z(bx["z1"]), Xh(bx["x1"]),
                             Z(bx["z0"])], fill=bx["color"],
                            outline=(40, 36, 28), width=2)
        # grade + brewer outside the right wall
        d.line([Xh(X1 + t), Z(-12), Xh(X1 + t + 34), Z(-12)],
               fill=(60, 55, 45), width=3)
        d.text((Xh(X1 + t) - 190, Z(-12) + 8), "grade ~1 ft below deck",
               font=fig.fS, fill=(70, 65, 55))
        bx = Xh(X1 + t + 16)
        d.rectangle([bx - 8, Z(60), bx + 8, Z(-12)], fill=(120, 60, 120),
                    outline=(40, 36, 28), width=2)
        d.ellipse([bx - 9, Z(67), bx + 9, Z(60)], fill=(120, 60, 120),
                  outline=(40, 36, 28), width=2)
        d.text((bx - 24, Z(72)), "brewer", font=fig.fS, fill=(120, 60, 120))
        # height ladder in the open floor between cluster and stand
        fig.dim_v(Xh(104.0), Z(0), Z(p.stand_h), f"stand {p.stand_h} in",
                  right=False, bg=True)
        fig.dim_v(Xh(118.0), Z(0), Z(p.rack_clear),
                  f"rack underside {fmt_ftin(p.rack_clear)}",
                  right=False, bg=True)
        fig.dim_v(Xh(132.0), Z(0), Z(b["kettle_rim"]),
                  f"kettle rim {fmt_ftin(b['kettle_rim'])}",
                  right=False, bg=True)
        fig.dim_v(Xh(146.0), Z(0), Z(b["hood_z0"]),
                  f"hood underside {fmt_ftin(b['hood_z0'])}",
                  right=False, bg=True)
        # duct over the head
        dz = b["hood_z0"] + p.hood_h
        d.rectangle([Xh(X1), Z(dz + 6), Xh(X1 + t), Z(dz)],
                    fill=(150, 150, 155), outline=(40, 36, 28), width=2)
        fig.dim_v(Xh(X1 + t / 2) + 60, Z(p.door_head), Z(dz + 6),
                  f"duct {dz:.1f}-{dz + 6:.1f} in over head", right=True)
        fig.dim_v(Xh(155.0), Z(b["kettle_top"]),
                  Z(b["hood_z0"]), f"{p.hood_gap:.0f} in gap", right=False)
        d.text((Xh(96.0), Z(b["hood_z0"] + p.hood_h) - 8),
               "condensate hood — 6 in duct out the rake wall",
               font=fig.fS, fill=(90, 85, 75))
        d.text((Xh(X1 - p.stand_d) + 8, Z(10)), "pumps under",
               font=fig.fS, fill=(40, 36, 28))
        fig.dim_h(Xh(X1 - p.stand_d), Xh(X1), Z(0) + 40,
                  f"stand {fmt_ftin(p.stand_d)} deep")
        fig.dim_h(Xh(X1 - p.stand_d / 2), Xh(X1), Z(b["kettle_rim"]) - 46,
                  "reach 13 in", up=False)
        # the west cluster story at left
        d.text((Xh(8), Z(p.bike_h) - 26), "bikes + blower nose-in, 43 in "
               f"tall, {info['underside'] - p.bike_h:.1f} in clear under "
               "the structure", font=fig.fS, fill=(40, 36, 28))
        fig.dim_v(Xh(126.0), Z(info["underside"]),
                  Z(info["top_of_stack"]),
                  f"stack {info['top_of_stack'] - info['underside']:.0f} in",
                  right=False, bg=True)
    else:
        # cut through the middle kettle (front brewery) or bike bay
        cut = b["kettles"][1] if brew else \
            (info["bikes"][0][0] + info["bikes"][0][1]) / 2
        if brew:
            fig = Fig(W, H,
                      "SECTION A-A — the permanent brewery at the front "
                      "doors",
                      "cut through the middle kettle · looking toward the "
                      "right wall · header-only front wall at left")
        else:
            fig = Fig(W, H, "SECTION A-A — bike bay and the LIFTED slab "
                      "rack",
                      "looking toward the right wall · front wall at the "
                      "left")
        d = fig.d
        t, X1, Y1 = e.wall_t, e.x1, e.y1
        s = min((H - 330) / (e.front_top + 15), (W - 900) / (Y1 + 2 * t))
        ox, oy = 400, H - 170

        def Y(y):
            return ox + y * s

        def Z(z):
            return oy - z * s

        d.rectangle([Y(-t), Z(0), Y(Y1 + t), Z(-0.75)],
                    fill=(196, 180, 148), outline=(60, 55, 45), width=2)
        in_door = False
        hz = p.door_head
        for w, lo, hi, hd, r in e.doors:
            if w == "front" and lo < cut < hi:
                in_door, hz = True, hd
        if in_door:
            d.rectangle([Y(-t), Z(e.front_top), Y(0), Z(hz)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
            d.line([Y(-t), Z(hz), Y(0), Z(hz)], fill=(200, 60, 60), width=3)
            d.text((Y(-t) + 4, Z(e.front_top) + 16),
                   f"door head {fmt_ftin(hz)}", font=fig.fS,
                   fill=(200, 60, 60))
        else:
            d.rectangle([Y(-t), Z(e.front_top), Y(0), Z(0)],
                        fill=(222, 214, 198), outline=(60, 55, 45), width=2)
        d.rectangle([Y(Y1), Z(e.back_top), Y(Y1 + t), Z(0)],
                    fill=(222, 214, 198), outline=(60, 55, 45), width=2)
        rf = [(Y(e.y0 - 6), Z(e.roof_z(e.y0 - 6))),
              (Y(Y1 + 6), Z(e.roof_z(Y1 + 6))),
              (Y(Y1 + 6), Z(e.roof_z(Y1 + 6) + 7)),
              (Y(e.y0 - 6), Z(e.roof_z(e.y0 - 6) + 7))]
        d.polygon(rf, fill=(127, 168, 201), outline=(60, 55, 45))
        for bx in boxes:
            if bx["x0"] < cut < bx["x1"]:
                d.rectangle([Y(bx["y0"]), Z(bx["z1"]), Y(bx["y1"]),
                             Z(bx["z0"])], fill=bx["color"],
                            outline=(40, 36, 28), width=2)
        if brew:
            d.line([Y(-34), Z(-12), Y(-t), Z(-12)], fill=(60, 55, 45),
                   width=3)
            d.text((Y(-34), Z(-12) + 8), "grade ~1 ft below deck",
                   font=fig.fS, fill=(70, 65, 55))
            bx = Y(-16)
            d.rectangle([bx - 8, Z(60), bx + 8, Z(-12)],
                        fill=(120, 60, 120), outline=(40, 36, 28), width=2)
            d.ellipse([bx - 9, Z(67), bx + 9, Z(60)], fill=(120, 60, 120),
                      outline=(40, 36, 28), width=2)
            d.text((bx - 60, Z(72)), "brewer", font=fig.fS,
                   fill=(120, 60, 120))
            xr = Y(Y1 + t) + 40
            fig.dim_v(xr, Z(0), Z(p.stand_h), f"stand {p.stand_h} in",
                      right=True)
            fig.dim_v(xr + 110, Z(0), Z(b["kettle_rim"]),
                      f"kettle rim {fmt_ftin(b['kettle_rim'])}", right=True)
            fig.dim_v(xr + 230, Z(0), Z(b["hood_z0"]),
                      f"hood underside {fmt_ftin(b['hood_z0'])}", right=True)
            fig.dim_h(Y(0), Y(p.stand_d / 2), Z(b["kettle_rim"]) - 46,
                      "reach 13 in", up=False)
            fig.dim_v(Y(p.stand_d + 6), Z(b["kettle_top"]), Z(b["hood_z0"]),
                      f"{p.hood_gap:.0f} in gap", right=True)
            d.text((Y(p.hood_d) + 12, Z(b["hood_z0"] + p.hood_h) - 8),
                   "condensate hood — 6 in duct out the front header band,",
                   font=fig.fS, fill=(90, 85, 75))
            d.text((Y(p.hood_d) + 12, Z(b["hood_z0"] + p.hood_h) + 14),
                   "452 CFM inline fan", font=fig.fS, fill=(90, 85, 75))
            d.text((Y(p.stand_d) + 8, Z(10)), "pumps under", font=fig.fS,
                   fill=(40, 36, 28))
            fig.dim_h(Y(0), Y(p.stand_d), Z(0) + 40,
                      f"stand {fmt_ftin(p.stand_d)} deep")
        else:
            d.text((Y(info["bike_y0"] + 8), Z(p.bike_h) - 30),
                   "e-bike, 43 in tall", font=fig.fS, fill=(40, 36, 28))
            fig.dim_v(Y(Y1 - 8), Z(0), Z(p.rack_clear),
                      f"rack underside {fmt_ftin(p.rack_clear)}")
            fig.dim_v(Y(Y1 - 8), Z(p.bike_h), Z(info["underside"]),
                      f"{info['underside'] - p.bike_h:.1f} in clear")
        d.text((Y(Y1) + 12, Z(e.back_top) - 12),
               f"back wall {fmt_ftin(e.back_top)}", font=fig.fS,
               fill=(40, 36, 28))
    fig.legend(W - 400, H - 320, legend_entries(p, brew))
    fig.img.save(out)


# -------------------------------------------------------------------- vents

def vent_lines():
    """Q3 machine-printed ventilation arithmetic (report §: vent holes vs
    hood). Sources: TEB ventilation facts (EQUIPMENT_FACTS.md) + standard
    psychrometric/stack-effect arithmetic labeled as derived."""
    watts = 5500.0
    req_cfm = watts / 17.6                       # TEB's own rule
    boiloff_gal_hr = 2.0
    lb_hr = boiloff_gal_hr * 8.34
    def cfm_for(dw):
        return lb_hr / (60 * 0.075 * dw)
    # passive stack: two equal louvers in series, effective area A/sqrt(2)
    import math as _m
    A_louver = (12 * 18) / 144.0                 # 12x18 in louver, sq ft
    A_eff = A_louver / _m.sqrt(2)
    def stack_cfm(h_ft, dT, cd=0.65):
        v = _m.sqrt(2 * 32.2 * h_ft * dT / 530.0)
        return A_eff * cd * v * 60
    lines = [
        "Ventilation arithmetic (Q3; TEB facts + derived psychrometrics):",
        f"  required extraction (TEB rule watts/17.6): {req_cfm:.0f} CFM "
        f"for the {watts:.0f} W elements",
        f"  boil-off {boiloff_gal_hr:.0f} gal/hr = {lb_hr:.1f} lb/hr of "
        f"water vapor",
        f"  air needed to carry it: {cfm_for(0.010):.0f} CFM at "
        "0.010 lb/lb humidity rise, "
        f"{cfm_for(0.0075):.0f} CFM at 0.0075 -> 312-450 CFM band",
        f"  passive stack, two 12x18 louvers (effective {A_eff:.2f} sq "
        f"ft), 4 ft apart, 20 F inside-out: {stack_cfm(4, 20):.0f} CFM; "
        f"5 ft apart, 30 F: {stack_cfm(5, 30):.0f} CFM",
        f"  -> passive louvers deliver ~{stack_cfm(5, 30) / req_cfm * 100:.0f}% "
        f"of the required flow on a GOOD day; FAILS the requirement",
        "  open doors: the brew already happens with doors open and the "
        "operator outside (confirmed in the brewery study); that is "
        "dilution, not capture - steam still reaches the ceiling and the "
        "cherry before it finds a door",
        "  options: (A) TEB hood + 452 CFM inline fan = capture at source, "
        "duct fits every arrangement tested; (B) wall fan >= 452 CFM + "
        "louvered intake, no hood = room-level capture, cheaper, winter "
        "condensation on cold surfaces incl. the slab stack; (C) passive "
        "vents only = undersized on calm/cold days, NOT recommended",
        "  RECOMMENDATION: A (hood + fan). B only if the captain accepts "
        "wiping down cold surfaces after winter boils. Never C alone.",
    ]
    return lines


# -------------------------------------------------------------------- main

def fit_lines(p, e, boxes, checks, info):
    lines = [f"Concept envelope, {fmt_ftin(e.outer_depth)} outer depth "
             f"(wall total {2 * e.wall_t:.1f} in verified from the audited "
             f"model):",
             f"  floor area {fmt_ftin(e.x1 - e.x0)} x {fmt_ftin(e.y1 - e.y0)}"
             f"  (inside faces of the 2x4 framing)",
             f"  clear height front {fmt_ftin(e.roof_z(e.y0))} -> back "
             f"{fmt_ftin(e.roof_z(e.y1))} (roof underside), deck at 0",
             f"  arrangement: {info['arrange']}"
             + (" (MIRROR: brewery LEFT, rack east)" if info["mirror"]
                else "")]
    lines.append("Doors PROPOSED by this arrangement (clear openings, all "
                 "outswing, heads 84 in unless noted):")
    for w, lo, hi, hz, role in e.doors:
        lines.append(f"  {w} wall: {hi - lo:.0f} in opening at "
                     f"{lo:.1f}-{hi:.1f} - {role}")
    lines += door_roles(e, boxes, info)
    lines.append("Fit checks:")
    for name, ok, det in checks:
        if "no overlap" in name and ok:
            continue
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name}"
                     + (f" - {det}" if det else ""))
    if info["arrange"] == "winner":
        lines += vent_lines()
    if not all(ok for _, ok, _ in checks):
        lines.append("RESULT: DOES NOT FIT as parameterized")
    else:
        lines.append("RESULT: everything fits with access kept")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=None)
    ap.add_argument("--out", default=str(Path(__file__).parent))
    ap.add_argument("--arrange", default="winner",
                    choices=["winner", "winner2", "runner-up", "old-front",
                             "old-baseline"])
    ap.add_argument("--mirror", action="store_true",
                    help="mirror the arrangement about the centerline "
                         "(brewery LEFT wall, rack east)")
    ap.add_argument("--side-door-w-in", type=float, default=64.0,
                    help="rake-wall brewery door width (64 default; the "
                         "77 in wall cannot frame a 72 with end studs)")
    ap.add_argument("--depth-ft", type=float, default=7.0)
    ap.add_argument("--rack-clear-in", type=float, default=48.0)
    ap.add_argument("--no-brewery", action="store_true")
    ap.add_argument("--slabs", type=int, default=6)
    ap.add_argument("--slab-len-ft", type=float, default=10.0)
    ap.add_argument("--slab-w-in", type=float, default=28.0)
    ap.add_argument("--bikes", type=int, default=2)
    ap.add_argument("--view", action="store_true")
    a = ap.parse_args()

    global REPO
    REPO = find_repo(Path(__file__).resolve(), a.repo)
    p = P(slab_count=a.slabs, slab_len=a.slab_len_ft * 12,
          slab_w=a.slab_w_in, bike_count=a.bikes, rack_clear=a.rack_clear_in,
          brewery=not a.no_brewery)
    e = envelope(a.depth_ft)
    boxes, checks, info = layout(p, e, a.arrange, a.mirror,
                                 a.side_door_w_in)

    lines = fit_lines(p, e, boxes, checks, info)
    print("\n".join(lines))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    suf = f"_{a.arrange}" + ("_mirror" if a.mirror else "")
    (out / f"fit_summary{suf}.txt").write_text("\n".join(lines) + "\n")

    fsuf = f"-{a.arrange}" + ("-mirror" if a.mirror else "")
    if a.mirror:
        print("mirror run: fit summary only (figures would duplicate the "
              "non-mirror arrangement)")
    else:
        render_plan(p, e, boxes, info, out / f"plan{fsuf}.png")
        render_iso(p, e, boxes, info, out / f"iso{fsuf}.png")
        render_section(p, e, boxes, info, out / f"section{fsuf}.png")
        print(f"wrote 3 figures to {out}")

    if a.view:
        from ocp_vscode import show
        parts = build_scene(p, e, boxes)
        show(parts, names=["storage jenga, free doors"])


if __name__ == "__main__":
    main()
