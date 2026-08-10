"""Shared data loading + placement helpers for the model-as-code rebuild.

Source of truth (HARD RULE: zero Onshape API calls):
- scripts/oriented_dims.json  -> part names (== CUT_LIST.md labels), edge dims
- scripts/bboxes.json          -> world axis-aligned bounding boxes (meters)
- CUT_LIST.md                  -> the human-readable cross-check

build123d TRAP RULES (learned empirically; see cad/README.md):
1. Location tuple form ONLY: Location((x,y,z), (rx,ry,rz)).
   Location(Pos(...), Rot(...)) constructs fine but SILENTLY DROPS the
   rotation. Every helper in this file uses the tuple form.
2. export_step takes ONE shape. Pass parts one at a time — a list fails
   with "'list' object has no attribute 'wrapped'".
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from build123d import Align, Box, Location, Plane, Polygon, Pos, extrude

IN = 25.4        # mm per inch (build123d world is mm)
M_PER_IN = 0.0254  # bboxes.json values are meters despite the "_m" key names
REPO = Path(__file__).resolve().parent.parent

TRIM_T = 0.75    # finish trim stock thickness (trim.py, doors.py, siding.py)

# Groups whose parts are tilted in the Y-Z plane at the roof pitch
# (world-AABB != oriented dims). Fascia are axis-aligned since the 2026-08
# roof-trim rework ("Fix fascia to symmetric 12 inch overhangs" on main).
SLOPE_Y_GROUPS = {"rafter", "left rake board", "right rake board",
                  "left rake wall top plate", "right rake wall top plate"}

# Groups built as exact YZ-profile prisms (birdsmouth/mitre/end cuts), so
# their volume is profile-area x width, not the oriented-dims product.
PROFILE_GROUPS = SLOPE_Y_GROUPS | {"left rake wall studs",
                                   "right rake wall studs"}


@dataclass
class Spec:
    label: str                     # exact CUT_LIST.md name
    dims: tuple                    # (dx, dy, dz) inches, longest = board length
    aabb: dict | None = None       # world bbox meters, None if not in bboxes.json

    @property
    def length(self) -> float:
        return max(self.dims)


@dataclass
class Audit:
    specs: dict = field(default_factory=dict)   # label -> list[Spec]
    pitch_deg: float = 0.0                      # roof pitch, solved from rafters

    def group(self, *labels) -> list[Spec]:
        out = []
        for l in labels:
            out.extend(self.specs.get(l, []))
        return out


def _bbox_dims_in(b: dict) -> tuple:
    """b is a bbox_m dict; returns world dims in inches."""
    return ((b["highX"] - b["lowX"]) / M_PER_IN,
            (b["highY"] - b["lowY"]) / M_PER_IN,
            (b["highZ"] - b["lowZ"]) / M_PER_IN)


def _center_in(b: dict) -> tuple:
    """b is a bbox_m dict; returns center in inches."""
    return ((b["lowX"] + b["highX"]) / 2 / M_PER_IN,
            (b["lowY"] + b["highY"]) / 2 / M_PER_IN,
            (b["lowZ"] + b["highZ"]) / 2 / M_PER_IN)


def _cutlist_label(name: str, dims: tuple = ()) -> str:
    """Map audit names to exact CUT_LIST.md labels."""
    if name == "":
        return "skid"  # unnamed composite-skid boards, per OUTSTANDING_ISSUES.md
    return name


def load_audit() -> Audit:
    od = json.loads((REPO / "scripts/oriented_dims.json").read_text())
    bb = json.loads((REPO / "scripts/bboxes.json").read_text())

    # oriented_dims.json -> specs keyed by cut-list label
    entries = [e for e in od if e["name"] != "inner volume"]
    by_label: dict[str, list] = {}
    for e in entries:
        dims = (e["dx"], e["dy"], e["dz"])
        label = _cutlist_label(e["name"], dims)
        by_label.setdefault(label, []).append(Spec(label=label, dims=dims))

    # bboxes.json -> candidates keyed the same way
    bb_by_label: dict[str, list] = {}
    for p in bb:
        label = _cutlist_label(p["name"], ())
        bb_by_label.setdefault(label, []).append(p)

    # Match specs to bboxes. The two "skid" specs pair with the two audited
    # composite-skid lines (their full 192" AABBs) since the 2026-08-10 skid
    # redesign: one continuous 16' 4x4 per line, no sisters.
    for label, specs in by_label.items():
        cands = bb_by_label.get(label, [])
        if len(cands) != len(specs):
            raise SystemExit(
                f"audit mismatch for '{label}': {len(specs)} in oriented_dims "
                f"vs {len(cands)} in bboxes")
        cands = sorted(cands, key=lambda p: tuple(
            round(v, 3) for v in _center_in(p["bbox_m"])))
        if label in SLOPE_Y_GROUPS:
            for s, p in zip(specs, cands):
                s.aabb = p["bbox_m"]
        else:
            # axis-aligned: pair by matching world dims
            used = [False] * len(cands)
            for s in specs:
                want = sorted(s.dims)
                hit = next((i for i, p in enumerate(cands)
                            if not used[i] and
                            all(abs(a - b) < 1e-3
                                for a, b in zip(sorted(_bbox_dims_in(p["bbox_m"])), want))),
                           None)
                if hit is None:
                    raise SystemExit(f"no bbox matches dims {s.dims} for '{label}'")
                used[hit] = True
                s.aabb = cands[hit]["bbox_m"]

    audit = Audit(specs=by_label)
    audit.pitch_deg = solve_pitch(audit)
    return audit


# Roof pitch history, for the sanity check only: 24/65 until the 2026-08-10
# restud to 92-5/8" pre-cut studs dropped the back/left/right plate tops
# 3/8" -> 24.375/65 (record: scripts/restud_92_5_8.py). The pitch used by
# the build is always DERIVED from the plate solids (roof_ref), so future
# wall-height edits propagate; this constant just fences gross errors.
DOCUMENTED_PITCH = math.degrees(math.atan(24.375 / 65))  # ~20.56 deg


@dataclass
class RoofRef:
    """Roof bearing geometry derived parametrically from the plate solids.

    The plates are placed exactly on their audited AABBs (place_box), so a
    plate spec's AABB faces ARE the plate solid's faces: seat planes come
    from plate tops, the bearing line from the front double top plate bottom
    at the front wall inner face to the back double top plate top at the
    back wall inner face, kicks from the plate inner/outer faces. No
    hardcoded roof numbers anywhere downstream - wall-height edits propagate.
    """
    slope: float            # tan(pitch), drop per +y
    sec: float              # 1/cos(pitch)
    front_bear_y: float     # front wall inner face (front DTP highY)
    front_bear_z: float     # bearing at front_bear_y (front DTP lowZ)
    front_seat_z: float     # front DTP top
    heel_y: float           # bottom edge x front seat plane
    back_seat_z: float      # back DTP short top
    back_seat_start_y: float  # back wall inner face (back DTP lowY)
    back_kick_y: float      # back wall outer face (back DTP highY)
    tail_f_y: float         # rafter front plumb end (rafter AABB lowY)
    tail_b_y: float         # rafter back plumb end (rafter AABB highY)
    rafter_depth: float     # 2x6 depth, perpendicular to the slope
    plate_thick: float      # rake plate 2x4 thickness

    def zbot(self, y: float) -> float:
        """Rafter bottom edge = rake plate top edge (the bearing line)."""
        return self.front_bear_z - self.slope * (y - self.front_bear_y)

    @property
    def rafter_off(self) -> float:
        """Vertical offset bottom edge -> top edge (vertical-sided profile,
        the audited construction: AABB highZ = bottom edge + off)."""
        return self.rafter_depth * self.sec

    def zu(self, y: float) -> float:
        """Rake plate underside: plate_thick perpendicular below the top
        edge -> vertical gap plate_thick * sec (the constraint_pilot
        DISTANCE constraint)."""
        return self.zbot(y) - self.plate_thick * self.sec


def roof_ref(audit: Audit) -> RoofRef:
    fd = audit.specs["front wall double top plate"][0].aabb
    bd = audit.specs["back wall double top plate short"][0].aabb
    front_seat_z = fd["highZ"] / M_PER_IN
    front_bear_z = fd["lowZ"] / M_PER_IN
    front_bear_y = fd["highY"] / M_PER_IN
    back_seat_z = bd["highZ"] / M_PER_IN
    back_seat_start_y = bd["lowY"] / M_PER_IN
    back_kick_y = bd["highY"] / M_PER_IN
    slope = (front_bear_z - back_seat_z) / (back_seat_start_y - front_bear_y)
    sec = math.hypot(1.0, slope)
    rafts = audit.group("rafter")
    tail_f_y = min(r.aabb["lowY"] for r in rafts) / M_PER_IN
    tail_b_y = max(r.aabb["highY"] for r in rafts) / M_PER_IN
    return RoofRef(
        slope=slope, sec=sec,
        front_bear_y=front_bear_y, front_bear_z=front_bear_z,
        front_seat_z=front_seat_z,
        heel_y=front_bear_y + (front_bear_z - front_seat_z) / slope,
        back_seat_z=back_seat_z,
        back_seat_start_y=back_seat_start_y, back_kick_y=back_kick_y,
        tail_f_y=tail_f_y, tail_b_y=tail_b_y,
        rafter_depth=sorted(rafts[0].dims)[1],
        plate_thick=min(audit.specs["left rake wall top plate"][0].dims))


def solve_pitch(audit: Audit) -> float:
    """Roof pitch derived from the plate solids (roof_ref), sanity-checked
    against the documented slope above."""
    deg = math.degrees(math.atan(roof_ref(audit).slope))
    assert abs(deg - DOCUMENTED_PITCH) < 0.5, \
        f"plate-derived pitch {deg:.3f} deg vs documented {DOCUMENTED_PITCH:.3f}"
    return deg


def prism_xz(profile_in: list, y0_in: float, y1_in: float):
    """Same as prism_yz but the profile polygon lives in the world X-Z plane
    (points (x, z) in inches) and extrudes in +Y from y0 to y1. Used for
    finish boards that run along Y with their lap profile in the thickness
    (X) direction. Carries .expected_volume_in3 like prism_yz."""
    area = _polygon_area_xz(profile_in)
    if area < 0:
        profile_in = list(reversed(profile_in))
        area = -area
    # plane normal is -Y: extruding +amount from y1 runs back to y0
    plane = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    sk = plane * Polygon(*[(x * IN, z * IN) for x, z in profile_in])
    width = y1_in - y0_in
    part = Pos(0, y1_in * IN, 0) * extrude(sk, amount=width * IN)
    part.expected_volume_in3 = area * width
    return part


def _polygon_area_xz(pts: list) -> float:
    a = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        a += x1 * z2 - x2 * z1
    return a / 2.0


def box_at(label: str, x0: float, x1: float, y0: float, y1: float,
           z0: float, z1: float):
    """Axis-aligned finish part from explicit inch bounds (world axes), with
    .label and .expected_volume_in3 for the verify harness."""
    p = Location(((x0 + x1) / 2 * IN, (y0 + y1) / 2 * IN, (z0 + z1) / 2 * IN),
                 (0, 0, 0)) * Box((x1 - x0) * IN, (y1 - y0) * IN,
                                  (z1 - z0) * IN, align=CENTER3)
    p.label = label
    p.expected_volume_in3 = (x1 - x0) * (y1 - y0) * (z1 - z0)
    return p


def finish_layout(audit: Audit) -> dict:
    """Wall planes, finish heights and clear door openings, all derived from
    the audited framing solids (inches) - the finish modules hardcode only
    product dims (board widths/exposures), never wall geometry. Mirrors what
    blender/build_scene.py skin_layout reads off the GLB, but from audit
    bboxes so cad/ stays the source of truth."""
    g = lambda n: audit.specs[n][0].aabb  # noqa: E731
    f = g("front wall bottom plate")["lowY"] / M_PER_IN    # front outer face
    b = g("back wall bottom plate")["highY"] / M_PER_IN    # back outer face
    l = g("left wall top plate")["lowX"] / M_PER_IN        # left outer face
    r = g("right wall top plate")["highX"] / M_PER_IN      # right outer face
    front_top = g("front wall double top plate")["highZ"] / M_PER_IN
    back_top = g("back wall double top plate short")["highZ"] / M_PER_IN
    rim_low = min(s.aabb["lowZ"] for s in audit.group("rim joist")) / M_PER_IN
    ref = roof_ref(audit)

    def openings(key, axis):
        """header bboxes -> clear openings [(lo, hi, head_z)]; the two plies
        share a span. Clear = header span minus one jack width per side."""
        jack = min(s.dims[2] for s in audit.specs[key.replace("headers",
                                                             "jack studs")])
        spans = {}
        for s in audit.specs[key]:
            a = s.aabb
            k = round(a["lowX" if axis == 0 else "lowY"], 3)
            lo = a["lowX" if axis == 0 else "lowY"] / M_PER_IN
            hi = a["highX" if axis == 0 else "highY"] / M_PER_IN
            hz = a["lowZ"] / M_PER_IN
            t = spans.setdefault(k, [lo, hi, hz])
            t[1] = max(t[1], hi)
            t[2] = min(t[2], hz)
        return [(t[0] + jack, t[1] - jack, t[2])
                for t in sorted(spans.values())]

    return {
        "f": f, "b": b, "l": l, "r": r,
        "front_top": front_top, "back_top": back_top,
        "rim_low": rim_low, "ref": ref,
        # side-wall siding/frieze top line: rafter bottom edge + 1" tuck
        "side_top": lambda y: ref.zbot(y) + 1.0,
        # back wall: rafter tails overhang the siding, so tops there tuck
        # under the rafter bottom edge at the part's own outer face
        "back_top_at": lambda off: ref.zbot(b + off),
        "front_open": openings("front wall headers", 0),
        "right_open": openings("right wall headers", 1),
    }


CENTER3 = (Align.CENTER, Align.CENTER, Align.CENTER)


def place_box(spec: Spec):
    """Axis-aligned part: world dims from its AABB, centered on AABB center.
    Data is inches; build123d builds mm, so scale at the geometry boundary."""
    b = spec.aabb
    cx, cy, cz = (v * IN for v in _center_in(b))
    sx, sy, sz = (v * IN for v in _bbox_dims_in(b))
    return Location((cx, cy, cz), (0, 0, 0)) * Box(sx, sy, sz, align=CENTER3)


def _polygon_area(pts: list) -> float:
    """Shoelace area of a 2D polygon (signed)."""
    a = 0.0
    for i in range(len(pts)):
        y1, z1 = pts[i]
        y2, z2 = pts[(i + 1) % len(pts)]
        a += y1 * z2 - y2 * z1
    return a / 2.0


def prism_yz(profile_in: list, x0_in: float, x1_in: float):
    """Exact YZ-profile prism: polygon (inches, in the world Y-Z plane)
    extruded in +X from x0 to x1. The profile polygon IS the part's
    construction record (birdsmouths, mitres, plumb ends), so placement is
    anchored on the profile's own world coordinates - never re-centered on
    an AABB. Carries .expected_volume_in3 for the verify harness."""
    area = _polygon_area(profile_in)
    if area < 0:  # CCW in (y,z) -> +X extrusion normal
        profile_in = list(reversed(profile_in))
        area = -area
    plane = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    # trap: build123d works in mm - scale the inch profile at the boundary
    sk = plane * Polygon(*[(y * IN, z * IN) for y, z in profile_in])
    width = x1_in - x0_in
    part = Pos(x0_in * IN, 0, 0) * extrude(sk, amount=width * IN)
    part.expected_volume_in3 = area * width
    return part



