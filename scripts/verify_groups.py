#!/usr/bin/env python3
"""Verify that parts sharing a name also share dimensions (within tolerance).
Convert all bboxes to inches, sort each part's dims descending (length, width,
thickness), then group by name and report variance within each group.
"""
import json
from collections import defaultdict
from pathlib import Path

M_TO_IN = 39.3700787
EXCLUDE = {"inner volume", "Composite part 3"}
TOL_IN = 0.05  # 1/20 inch — anything tighter is noise

data = json.loads(Path("scripts/bboxes.json").read_text())

def to_sorted_inches(r):
    dims = sorted([r["dx_m"], r["dy_m"], r["dz_m"]], reverse=True)
    return tuple(round(d * M_TO_IN, 3) for d in dims)  # (length, width, thickness)

groups = defaultdict(list)
for r in data:
    if r["name"] in EXCLUDE:
        continue
    if "error" in r:
        print(f"!! error on {r['partId']} {r['name']}: {r['error']}")
        continue
    groups[r["name"]].append((r["partId"], to_sorted_inches(r)))

print(f"{'Group':40s} {'Count':>5s}  {'Dims (L x W x T, in)':40s}  {'Notes'}")
print("-" * 110)
for name, items in sorted(groups.items()):
    n = len(items)
    # Check if all dims match within tol
    dims_set = {d for _, d in items}
    if len(dims_set) == 1:
        d = next(iter(dims_set))
        print(f"{name:40s} {n:5d}  {d[0]:7.3f} x {d[1]:6.3f} x {d[2]:6.3f}            OK")
    else:
        # Group by dim tuple with tolerance
        sub = defaultdict(list)
        for pid, d in items:
            # cluster by rounding to TOL_IN
            key = tuple(round(x / TOL_IN) * TOL_IN for x in d)
            sub[key].append((pid, d))
        if len(sub) == 1:
            # All within tolerance
            d = items[0][1]
            print(f"{name:40s} {n:5d}  {d[0]:7.3f} x {d[1]:6.3f} x {d[2]:6.3f}            OK (within tol)")
        else:
            print(f"{name:40s} {n:5d}  VARIES:")
            for key, subitems in sorted(sub.items(), key=lambda x: -len(x[1])):
                d = subitems[0][1]
                pids = ", ".join(p for p, _ in subitems)
                print(f"{'':40s} {len(subitems):5d}  {d[0]:7.3f} x {d[1]:6.3f} x {d[2]:6.3f}   [{pids}]")
