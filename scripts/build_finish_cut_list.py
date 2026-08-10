#!/usr/bin/env python3
"""Finish cut list + SEPARATE order list (captain 2026-08-10: doors/siding/
trim are modeled for real but ordered on a completely different list - never
mixed into order_list.csv).

Reads the built finish parts (cad/siding.py, cad/trim.py, cad/doors.py) and
writes order_list_finish.csv plus appends the FINISH section to CUT_LIST.md
(build_cut_list.py calls this after the framing sections, so a regen keeps
both lists in step). Hardware (strap hinges, latches) has no geometry - it
is listed as line items only.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from scripts.build_cut_list import (KERF_IN, YARD, ffd_bins, fmt_in,
                                        pack_and_rightsize, section_for)
except ImportError:  # run directly from scripts/
    from build_cut_list import (KERF_IN, YARD, ffd_bins, fmt_in,
                                pack_and_rightsize, section_for)

from cad.build import build_finish
from cad.common import IN, load_audit

# label -> (stock lumber, treatment); product dims live in the cad modules
LABEL_META = {
    "finish siding":        ("1x8", "PRIMED"),
    "finish skirt":         ("1x8", "PRIMED"),
    "finish corner boards": ("1x6", "PRIMED"),
    "finish frieze":        ("1x10", "PRIMED"),
    "finish door casings":  ("1x6", "PRIMED"),
    "finish door planks":   ("1x6", "KD"),
    "finish door rails":    ("1x4", "KD"),
}
STOCK_FINISH = {"1x4": [96, 120, 144, 168, 192],
                "1x6": [96, 120, 144, 168, 192],
                "1x8": [96, 120, 144, 168, 192],
                "1x10": [96, 120, 144, 168, 192]}

# no geometry - line items only
HARDWARE = [
    (8, 'strap hinge 12" black', "2 per leaf, 4 leaves"),
    (3, "gate latch + hasp black", "1 per opening (double: center latch)"),
]


def meta_for(label):
    return next(v for k, v in LABEL_META.items() if label.startswith(k))


def finish_rows():
    """(section, lumber, length_in, treatment, label) -> qty, from the built
    finish parts (length = longest bbox dim)."""
    audit = load_audit()
    agg = defaultdict(int)
    for p in build_finish(audit):
        lumber, treatment = meta_for(p.label)
        b = p.bounding_box()
        length = max(b.max.X - b.min.X, b.max.Y - b.min.Y,
                     b.max.Z - b.min.Z) / IN
        agg[(section_for(p.label), lumber, round(length, 3), treatment,
             p.label)] += 1
    return agg


def write_finish_outputs():
    agg = finish_rows()

    out_csv = Path("order_list_finish.csv")
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lumber", "treatment", "stock_length_ft", "qty", "notes"])
        order_groups = defaultdict(list)
        for (sec, lumber, length, treatment, label), qty in agg.items():
            for _ in range(qty):
                order_groups[(lumber, treatment)].append((length, label))
        for (lumber, treatment), cuts in sorted(order_groups.items()):
            bins = pack_and_rightsize(cuts, STOCK_FINISH[lumber])
            counts = defaultdict(int)
            for sl, _, _ in bins:
                counts[sl] += 1
            for sl, n in sorted(counts.items()):
                w.writerow([lumber, treatment, f"{sl/12:g}", n,
                            f"finish; {YARD}"])
        for qty, name, note in HARDWARE:
            w.writerow([name, "—", "ea", qty, f"finish hardware; {note}"])

    out_md = Path("CUT_LIST.md")
    with out_md.open("a") as f:
        f.write("---\n\n")
        f.write("# FINISH — SEPARATE ORDER LIST (order_list_finish.csv)\n\n")
        f.write("Captain 2026-08-10: doors/siding/trim modeled for real in\n")
        f.write("`cad/siding.py`, `cad/trim.py`, `cad/doors.py` but ordered on a\n")
        f.write("completely separate list - never mixed with the framing lumber\n")
        f.write("above. Rows derive from the built finish parts. Hardware has no\n")
        f.write("geometry; line items only.\n\n")
        for section in ("Finish siding", "Finish trim", "Finish doors"):
            rows = [k for k in agg if k[0] == section]
            if not rows:
                continue
            f.write(f"## {section}\n\n")
            f.write("| Qty | Lumber | Treatment | Length | Name |\n")
            f.write("|---:|:---|:---:|---:|:---|\n")
            rows.sort(key=lambda k: (k[1], -k[2], k[4]))
            for sec, lumber, length, treatment, label in rows:
                ft = int(length // 12)
                inch = length - ft * 12
                f.write(f"| {agg[(sec, lumber, length, treatment, label)]} | "
                        f"{lumber} | {treatment} | "
                        f"{ft}′ {fmt_in(inch)}″ ({fmt_in(length)}″) | {label} |\n")
            f.write("\n")
        f.write("## Finish hardware (no geometry)\n\n")
        f.write("| Qty | Item | Note |\n|---:|:---|:---|\n")
        for qty, name, note in HARDWARE:
            f.write(f"| {qty} | {name} | {note} |\n")
        f.write("\n")

        f.write("## Finish stock-length order list\n\n")
        f.write(f"Same first-fit-decreasing packing as the framing list "
                f"(kerf {KERF_IN}\"): \n\n")
        order_groups = defaultdict(list)
        for (sec, lumber, length, treatment, label), qty in agg.items():
            for _ in range(qty):
                order_groups[(lumber, treatment)].append((length, label))
        for (lumber, treatment), cuts in sorted(order_groups.items()):
            bins = pack_and_rightsize(cuts, STOCK_FINISH[lumber])
            total = sum(sl for sl, _, _ in bins)
            actual = sum(c[0] for c in cuts)
            counts = defaultdict(int)
            for sl, _, _ in bins:
                counts[sl] += 1
            summary = ", ".join(f"{n} × {sl/12:g}′"
                                for sl, n in sorted(counts.items()))
            f.write(f"### {lumber} {treatment} — order **{summary}** "
                    f"({total/12:.1f} LF purchased, {actual/12:.1f} LF cuts, "
                    f"{100 * (total - actual) / total:.1f}% waste)\n\n")
            for i, (sl, used, items) in enumerate(bins, 1):
                desc = "; ".join(f"{fmt_in(l)}″ {lbl}" for l, lbl in items)
                f.write(f"- Board {i} ({sl/12:g}′): {desc}  "
                        f"— waste: {sl - used:.2f}″\n")
            f.write("\n")

    print(f"Wrote {out_csv} and appended finish sections to {out_md}")


if __name__ == "__main__":
    write_finish_outputs()
