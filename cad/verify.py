"""Assertion harness - run after EVERY change:

    .venv/bin/python -m cad.verify

Checks the built model against the repo's audit data (no Onshape calls):
1. coverage: every oriented_dims.json part (cut list) exists with its label
2. per part: world bbox dims + volume match the oriented dims exactly
3. per part: world placement matches bboxes.json (tolerances below; the rake
   plates get a wider z tolerance because their real end cuts are not in the
   audit data - see cad/walls_rake.py)

The smoke test that chose this stack proved silent boolean no-ops are the
real failure mode on the OCCT kernel; check 2 catches that class of bug
(volume shortfall) for every part on every run.
"""
import sys

from cad.build import build_all
from cad.common import (IN, ROLL_X_GROUPS, SLOPE_Y_GROUPS, _bbox_dims_in,
                        _center_in)

TIGHT = 0.02                      # inches, axis-aligned parts + centers
TILTED_EXT = 0.05                 # inches, rafters/rake boards/fascia extents
RAKE_PLATE_Z = 1.5                # inches, rake plates' z extent (end cuts)

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def main():
    audit, parts = build_all()

    # --- 1. coverage ---------------------------------------------------------
    expected = {l: len(v) for l, v in audit.specs.items()}
    got: dict[str, int] = {}
    for p in parts:
        got[p.label] = got.get(p.label, 0) + 1
    check(expected == got,
          f"coverage mismatch:\n  missing/extra: "
          f"{ {l: (expected.get(l, 0), got.get(l, 0)) for l in set(expected) | set(got) if expected.get(l) != got.get(l)} }")

    # --- 2+3. dims, volume, placement ----------------------------------------
    for label, specs in audit.specs.items():
        group = [p for p in parts if p.label == label]
        if len(group) != len(specs):
            continue  # already reported by coverage
        # round keys: full-precision float noise in one axis must not
        # reorder parts that are distinct only in another axis
        specs_sorted = sorted(
            specs, key=lambda s: (tuple(round(v, 3) for v in _center_in(s.aabb))
                                  if s.aabb else (0, 0, 0)))
        group_sorted = sorted(group, key=lambda p: tuple(round(v, 3) for v in (
            (p.bounding_box().min.X + p.bounding_box().max.X) / 2 / IN,
            (p.bounding_box().min.Y + p.bounding_box().max.Y) / 2 / IN,
            (p.bounding_box().min.Z + p.bounding_box().max.Z) / 2 / IN)))
        tilted = label in SLOPE_Y_GROUPS | ROLL_X_GROUPS
        for s, p in zip(specs_sorted, group_sorted):
            b = p.bounding_box()
            mdims = sorted(((b.max.X - b.min.X) / IN,
                            (b.max.Y - b.min.Y) / IN,
                            (b.max.Z - b.min.Z) / IN))
            edims = sorted(s.dims)
            if not tilted:
                # axis-aligned: world dims ARE the board dims
                check(all(abs(a - e) < max(TIGHT, 1e-3 * e)
                          for a, e in zip(mdims, edims)),
                      f"'{label}': dims {[round(d,2) for d in mdims]} != "
                      f"audit {[round(d,2) for d in edims]}")
            evol = p.volume / IN ** 3
            avol = edims[0] * edims[1] * edims[2]
            check(abs(evol - avol) < 1e-3 * avol,
                  f"'{label}': volume {evol:.1f} != audit {avol:.1f} in^3 "
                  f"(silent boolean no-op?)")
            if s.aabb is None:
                continue  # skids: placement inferred, see cad/skids.py
            mc = ((b.min.X + b.max.X) / 2 / IN,
                  (b.min.Y + b.max.Y) / 2 / IN,
                  (b.min.Z + b.max.Z) / 2 / IN)
            ec = _center_in(s.aabb)
            check(all(abs(a - e) < TIGHT for a, e in zip(mc, ec)),
                  f"'{label}': center {tuple(round(v,2) for v in mc)} != "
                  f"audit {tuple(round(v,2) for v in ec)}")
            if tilted:
                # tilted/rolled: world AABB is pitch-inflated; compare it to
                # bboxes.json (the real placement check for these parts)
                ext_tol = (RAKE_PLATE_Z if "rake wall top plate" in label
                           else TILTED_EXT)
                eext = sorted(_bbox_dims_in(s.aabb))
                check(all(abs(a - e) < ext_tol
                          for a, e in zip(mdims, eext)),
                      f"'{label}': extents {tuple(round(v,2) for v in mdims)} "
                      f"!= audit {tuple(round(v,2) for v in eext)} "
                      f"(tol {ext_tol}\")")

    n = len(parts)
    if failures:
        print(f"FAIL: {len(failures)} problem(s) in {n} parts")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {n} parts, {len(audit.specs)} cut-list names, all dims/"
          f"volumes/placements match audit data")


if __name__ == "__main__":
    main()
