"""Assertion harness - run after EVERY change:

    .venv/bin/python -m cad.verify

Checks the built model against the repo's audit data (no Onshape calls):
1. coverage: every oriented_dims.json part (cut list) exists with its label
2. per part: dims/volume/placement match the audit data - PROFILE_GROUPS
   (prisms built with exact birdsmouth/mitre/end-cut profiles) check the
   world AABB against bboxes.json at TIGHT and the volume against the
   profile's own expected volume; every other part checks world dims and
   volume against the oriented dims
3. seating/flushness: rafter seats coplanar with the plate top faces, kick
   and plumb-end faces present, tails flush with the fascia, rake studs
   mitered onto the rake plate underside
4. zero interference: pairwise exact solid sweep; only the documented
   intentional front-bottom-plate overlaps are exempt

The smoke test that chose this stack proved silent boolean no-ops are the
real failure mode on the OCCT kernel; the volume checks catch that class of
bug for every part on every run. Checks 3-4 are the regression gate for the
birdsmouth seating that the rectangular-stock rebuild silently lost
(diagnosis: firstmate report woodbike-shed-birdsmouth-scout, 2026-08-10).
"""
import sys

from build123d import Plane

from cad.build import build_all
from cad.common import (IN, PROFILE_GROUPS, _bbox_dims_in, _center_in)

TIGHT = 0.02                      # inches, placement + flushness tolerances
SEAT_AREA_MIN = (6.0, 5.0)        # in^2, front/back rafter seat faces
KICK_AREA_MIN = (2.0, 1.5)        # in^2, front/back plumb kicks
END_AREA_MIN = 8.0                # in^2, plumb tail cuts (5.87 x 1.5)
OVERLAP_EPS = 0.01                # in^3, report threshold

# Captain's documented modeling quirks, present in the Onshape model too
# (OUTSTANDING_ISSUES.md "Known intentional overlaps").
ALLOWED_OVERLAPS = {
    frozenset(("front wall jack studs", "front wall bottom plate")),
    frozenset(("front wall king studs", "front wall bottom plate")),
}

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def bbox_in(p):
    b = p.bounding_box()
    return (b.min.X / IN, b.max.X / IN, b.min.Y / IN, b.max.Y / IN,
            b.min.Z / IN, b.max.Z / IN)


def face_planes(p):
    """[(origin_in, normal, area_in2)] for the planar faces of a part."""
    out = []
    for f in p.faces():
        try:
            pl = Plane(f)
        except Exception:
            continue  # non-planar
        n = pl.z_dir
        out.append(((pl.origin.X / IN, pl.origin.Y / IN, pl.origin.Z / IN),
                    (n.X, n.Y, n.Z), f.area / IN ** 2))
    return out


def z_on_plane(pt, n, y):
    """z of a plane (pt, n) at ordinate y (n.z != 0)."""
    return pt[2] - (n[1] / n[2]) * (y - pt[1])


def main():
    audit, parts = build_all()
    by_label: dict[str, list] = {}
    for p in parts:
        by_label.setdefault(p.label, []).append(p)

    # --- 1. coverage ---------------------------------------------------------
    expected = {l: len(v) for l, v in audit.specs.items()}
    got: dict[str, int] = {}
    for p in parts:
        got[p.label] = got.get(p.label, 0) + 1
    check(expected == got,
          f"coverage mismatch:\n  missing/extra: "
          f"{ {l: (expected.get(l, 0), got.get(l, 0)) for l in set(expected) | set(got) if expected.get(l) != got.get(l)} }")

    # --- 2. dims, volume, placement -------------------------------------------
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
        profile = label in PROFILE_GROUPS
        for s, p in zip(specs_sorted, group_sorted):
            b = p.bounding_box()
            if not profile:
                mdims = sorted(((b.max.X - b.min.X) / IN,
                                (b.max.Y - b.min.Y) / IN,
                                (b.max.Z - b.min.Z) / IN))
                edims = sorted(s.dims)
                check(all(abs(a - e) < max(TIGHT, 1e-3 * e)
                          for a, e in zip(mdims, edims)),
                      f"'{label}': dims {[round(d,2) for d in mdims]} != "
                      f"audit {[round(d,2) for d in edims]}")
            evol = p.volume / IN ** 3
            if profile:
                # exact profile prism: volume from the construction polygon
                avol = p.expected_volume_in3
                check(abs(evol - avol) < 1e-3 * avol,
                      f"'{label}': volume {evol:.1f} != profile {avol:.1f} "
                      f"in^3 (silent boolean no-op?)")
                eext = _bbox_dims_in(s.aabb)
                mext = ((b.max.X - b.min.X) / IN, (b.max.Y - b.min.Y) / IN,
                        (b.max.Z - b.min.Z) / IN)
                check(all(abs(m - e) < TIGHT for m, e in zip(mext, eext)),
                      f"'{label}': extents {tuple(round(v,2) for v in mext)} "
                      f"!= audit {tuple(round(v,2) for v in eext)}")
            else:
                avol = edims[0] * edims[1] * edims[2]
                check(abs(evol - avol) < 1e-3 * avol,
                      f"'{label}': volume {evol:.1f} != audit {avol:.1f} in^3 "
                      f"(silent boolean no-op?)")
            if s.aabb is None:
                continue
            mc = ((b.min.X + b.max.X) / 2 / IN,
                  (b.min.Y + b.max.Y) / 2 / IN,
                  (b.min.Z + b.max.Z) / 2 / IN)
            ec = _center_in(s.aabb)
            check(all(abs(a - e) < TIGHT for a, e in zip(mc, ec)),
                  f"'{label}': center {tuple(round(v,2) for v in mc)} != "
                  f"audit {tuple(round(v,2) for v in ec)}")

    # --- 3. seating / flushness ------------------------------------------------
    front_dtp = by_label["front wall double top plate"][0]
    back_dtps = by_label["back wall double top plate short"][0]
    fasc_f = by_label["front fascia"][0]
    fasc_b = by_label["back fascia"][0]
    fb = bbox_in(front_dtp)
    bb_ = bbox_in(back_dtps)
    fasc_fb, fasc_bb = bbox_in(fasc_f), bbox_in(fasc_b)
    seat_f_z, seat_b_z = fb[5], bb_[5]          # plate top faces
    kick_f_y, kick_b_y = fb[3], bb_[3]          # plate inner/outer faces

    def faces_at(planes, axis, coord, tol):
        """(normal, total area) of faces whose plane crosses `coord` on
        `axis` (0=x,1=y,2=z) with a near-axis-aligned normal."""
        tot = 0.0
        nrm = None
        for pt, n, a in planes:
            if abs(pt[axis] - coord) < tol and \
                    sum(n[i] * n[i] for i in range(3) if i != axis) < 1e-4:
                tot += a
                nrm = n
        return nrm, tot

    for r in by_label["rafter"]:
        rb = bbox_in(r)
        planes = face_planes(r)
        _, a_seat_f = faces_at(planes, 2, seat_f_z, 0.005)
        check(a_seat_f >= SEAT_AREA_MIN[0],
              f"'rafter' x{rb[0]:.2f}: front seat face at z={seat_f_z:.3f} "
              f"area {a_seat_f:.2f} < {SEAT_AREA_MIN[0]} (birdsmouth lost?)")
        _, a_seat_b = faces_at(planes, 2, seat_b_z, 0.005)
        check(a_seat_b >= SEAT_AREA_MIN[1],
              f"'rafter' x{rb[0]:.2f}: back seat face at z={seat_b_z:.3f} "
              f"area {a_seat_b:.2f} < {SEAT_AREA_MIN[1]} (birdsmouth lost?)")
        n_kf, a_kf = faces_at(planes, 1, kick_f_y, 0.005)
        check(a_kf >= KICK_AREA_MIN[0] and n_kf and n_kf[1] < -0.99,
              f"'rafter' x{rb[0]:.2f}: front kick at y={kick_f_y:.3f} "
              f"area {a_kf:.2f} (want >= {KICK_AREA_MIN[0]}, -Y normal)")
        # both kick faces look into their notch -> -Y outward normal
        n_kb, a_kb = faces_at(planes, 1, kick_b_y, 0.005)
        check(a_kb >= KICK_AREA_MIN[1] and n_kb and n_kb[1] < -0.99,
              f"'rafter' x{rb[0]:.2f}: back kick at y={kick_b_y:.3f} "
              f"area {a_kb:.2f} (want >= {KICK_AREA_MIN[1]}, -Y normal)")
        _, a_end_f = faces_at(planes, 1, rb[2], 0.005)
        check(a_end_f >= END_AREA_MIN,
              f"'rafter' x{rb[0]:.2f}: front plumb end at y={rb[2]:.3f} "
              f"area {a_end_f:.2f} < {END_AREA_MIN}")
        _, a_end_b = faces_at(planes, 1, rb[3], 0.005)
        check(a_end_b >= END_AREA_MIN,
              f"'rafter' x{rb[0]:.2f}: back plumb end at y={rb[3]:.3f} "
              f"area {a_end_b:.2f} < {END_AREA_MIN}")
        # tail tops flush with the fascia tops
        top = next(((pt, n) for pt, n, _ in planes
                    if n[2] > 0.5 and abs(n[0]) < 1e-6), None)
        check(top is not None, f"'rafter' x{rb[0]:.2f}: no sloped top face")
        if top:
            zf = z_on_plane(top[0], top[1], rb[2])
            check(abs(zf - fasc_fb[5]) < 0.01,
                  f"'rafter' x{rb[0]:.2f}: front tail top {zf:.4f} != "
                  f"front fascia top {fasc_fb[5]:.4f}")
            zb = z_on_plane(top[0], top[1], rb[3])
            check(abs(zb - fasc_bb[5]) < 0.01,
                  f"'rafter' x{rb[0]:.2f}: back tail top {zb:.4f} != "
                  f"back fascia top {fasc_bb[5]:.4f}")

    # rake boards butt the fascia inner faces
    for lbl in ("left rake board", "right rake board"):
        for p in by_label[lbl]:
            pb = bbox_in(p)
            check(abs(pb[2] - fasc_fb[3]) < 0.01,
                  f"'{lbl}': front end {pb[2]:.4f} != fascia inner face "
                  f"{fasc_fb[3]:.4f}")
            check(abs(pb[3] - fasc_bb[2]) < 0.01,
                  f"'{lbl}': back end {pb[3]:.4f} != fascia inner face "
                  f"{fasc_bb[2]:.4f}")

    # rake studs mitered onto the rake plate underside
    for side in ("left", "right"):
        plate = by_label[f"{side} rake wall top plate"][0]
        under = next(((pt, n) for pt, n, _ in face_planes(plate)
                      if n[2] < -0.5 and abs(n[0]) < 1e-6), None)
        check(under is not None, f"'{side} rake wall top plate': no underside")
        if not under:
            continue
        upt, un = under
        for s in by_label[f"{side} rake wall studs"]:
            stop = next(((pt, n) for pt, n, _ in face_planes(s)
                         if n[2] > 0.5 and abs(n[0]) < 1e-6), None)
            check(stop is not None, f"'{side} rake wall studs': no mitre face")
            if stop:
                spt, sn = stop
                coplanar = abs((spt[0] - upt[0]) * un[0] +
                               (spt[1] - upt[1]) * un[1] +
                               (spt[2] - upt[2]) * un[2]) < 0.01
                check(coplanar and abs(sn[1] / sn[2] - un[1] / un[2]) < 1e-3,
                      f"'{side} rake wall studs' y{spt[1]:.2f}: top face not "
                      f"on plate underside (gap/offset)")

    # --- 4. zero-interference sweep ---------------------------------------------
    n_exact = 0
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            ab, bb2 = bbox_in(a), bbox_in(b)
            if not (min(ab[1], bb2[1]) - max(ab[0], bb2[0]) > 1e-9 and
                    min(ab[3], bb2[3]) - max(ab[2], bb2[2]) > 1e-9 and
                    min(ab[5], bb2[5]) - max(ab[4], bb2[4]) > 1e-9):
                continue
            n_exact += 1
            v = (a & b).volume / IN ** 3
            if v <= OVERLAP_EPS:
                continue
            pair = frozenset((a.label, b.label))
            if pair in ALLOWED_OVERLAPS:
                continue
            check(False, f"interference {v:.3f} in^3: {a.label} x {b.label}")

    n = len(parts)
    if failures:
        print(f"FAIL: {len(failures)} problem(s) in {n} parts "
              f"({n_exact} exact pair intersections evaluated)")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {n} parts, {len(audit.specs)} cut-list names; dims/volumes/"
          f"placements match audit data; seats/kicks/ends flush; "
          f"0 unallowed interference ({n_exact} pairs swept)")


if __name__ == "__main__":
    main()
