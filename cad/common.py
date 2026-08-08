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

from build123d import Align, Box, Location

IN = 25.4        # mm per inch (build123d world is mm)
M_PER_IN = 0.0254  # bboxes.json values are meters despite the "_m" key names
REPO = Path(__file__).resolve().parent.parent

# Groups whose parts are tilted in the Y-Z plane (roof pitch) or rolled about
# their long X axis (fascia). Detected by world-AABB != oriented dims.
SLOPE_Y_GROUPS = {"roof rafters", "roof rake board",
                  "left rake wall top plate", "right rake wall top plate"}
ROLL_X_GROUPS = {"roof fascia"}

# Audit names that differ from cut-list labels (see scripts/build_cut_list.py).
CRIPPLE_LONG = ("front wall cripples normal door", 31.0)   # 2x 31"
CRIPPLE_SHORT = ("front wall cripples wide door", 29.0)    # 4x 29"


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


def _cutlist_label(name: str, dims: tuple) -> str:
    """Map audit names to exact CUT_LIST.md labels."""
    if name == "":
        return "skid"  # unnamed composite-skid boards, per OUTSTANDING_ISSUES.md
    if name == "front wall cripples":
        # bboxes.json merges both cripple groups; split by length as the cut
        # list does (31" = normal door, 29" = wide door).
        return CRIPPLE_LONG[0] if abs(max(dims) - CRIPPLE_LONG[1]) < 0.6 else CRIPPLE_SHORT[0]
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
        label = _cutlist_label(p["name"], (p["dx_m"] / M_PER_IN,
                                                    p["dy_m"] / M_PER_IN,
                                                    p["dz_m"] / M_PER_IN))
        bb_by_label.setdefault(label, []).append(p)

    # Match specs to bboxes.
    for label, specs in by_label.items():
        cands = bb_by_label.get(label, [])
        if label == "skid":
            # The four physical skid boards are unnamed in bboxes.json (they
            # live inside the composite skids); placement is inferred in
            # skids.py from the skid sisters + floor extents.
            continue
        if len(cands) != len(specs):
            raise SystemExit(
                f"audit mismatch for '{label}': {len(specs)} in oriented_dims "
                f"vs {len(cands)} in bboxes")
        cands = sorted(cands, key=lambda p: tuple(
            round(v, 3) for v in _center_in(p["bbox_m"])))
        if label in SLOPE_Y_GROUPS | ROLL_X_GROUPS:
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


def solve_pitch(audit: Audit) -> float:
    """Roof pitch from a rafter: dz = L sin(t) + D cos(t). Cross-checks the
    documented 24/65 slope (MANUAL_COMPLETION.md on fm/woodbike-shed-finish-rework).
    """
    r = audit.specs["roof rafters"][0]
    L = max(r.dims)
    D = sorted(r.dims)[1]
    dz = (r.aabb["highZ"] - r.aabb["lowZ"]) / M_PER_IN
    lo, hi = 0.0, math.radians(45)
    for _ in range(60):
        mid = (lo + hi) / 2
        if L * math.sin(mid) + D * math.cos(mid) < dz:
            lo = mid
        else:
            hi = mid
    deg = math.degrees((lo + hi) / 2)
    assert abs(deg - math.degrees(math.atan(24 / 65))) < 0.05, \
        f"solved pitch {deg:.3f} deg disagrees with documented 24/65 slope"
    return deg


CENTER3 = (Align.CENTER, Align.CENTER, Align.CENTER)


def place_box(spec: Spec):
    """Axis-aligned part: world dims from its AABB, centered on AABB center.
    Data is inches; build123d builds mm, so scale at the geometry boundary."""
    b = spec.aabb
    cx, cy, cz = (v * IN for v in _center_in(b))
    sx, sy, sz = (v * IN for v in _bbox_dims_in(b))
    return Location((cx, cy, cz), (0, 0, 0)) * Box(sx, sy, sz, align=CENTER3)


def place_slope_y(spec: Spec, x_dim: float, z_dim: float, pitch_deg: float):
    """Board with length along Y, falling in +Y at the roof pitch (rafters,
    rake boards, rake wall plates). Cross-section: x_dim in X, z_dim thick."""
    cx, cy, cz = (v * IN for v in _center_in(spec.aabb))
    L = spec.length
    return (Location((cx, cy, cz), (-pitch_deg, 0, 0))
            * Box(x_dim * IN, L * IN, z_dim * IN, align=CENTER3))


def place_roll_x(spec: Spec, pitch_deg: float):
    """Board along X, rolled about its long axis so its wide face lies in the
    roof plane (fascia). Local cross-section: 1.5 in Y, 5.5 in Z."""
    cx, cy, cz = (v * IN for v in _center_in(spec.aabb))
    L = spec.length
    t, d = sorted(spec.dims)[:2]
    return (Location((cx, cy, cz), (-pitch_deg, 0, 0))
            * Box(L * IN, t * IN, d * IN, align=CENTER3))
