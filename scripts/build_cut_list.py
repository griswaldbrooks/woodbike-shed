#!/usr/bin/env python3
"""Build a cut list from oriented_dims.json, grouped by shed section, with
treatment (PT vs KD) and a stock-length optimization for ordering.

Organization:
  - Skids (PT 4x4)
  - Floor (PT 2x6 joists + rim, OSB subfloor)
  - Back wall, Front wall, Left wall, Right wall (KD 2x4)
  - Left rake (gable) wall, Right rake (gable) wall (KD 2x4)
  - Roof (KD 2x6 rafters, rake, fascia)

Stock-length optimization:
  First-fit-decreasing bin packing across standard dimensional-lumber stock
  lengths. Uses a 1/8" kerf per cut. For each cross-section+treatment, picks
  the mix of stock lengths that minimizes total linear feet purchased.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

# ----- lumber classification ----------------------------------------------

NOMINAL_LUMBER = {
    (1.5, 3.5): "2x4",
    (1.5, 5.5): "2x6",
    (1.5, 7.25): "2x8",
    (1.5, 9.25): "2x10",
    (3.5, 3.5): "4x4",
    (3.5, 5.5): "4x6",
}
CS_TOL = 0.05  # in


def classify(t, w):
    t, w = sorted([t, w])
    for (nt, nw), name in NOMINAL_LUMBER.items():
        if abs(t - nt) < CS_TOL and abs(w - nw) < CS_TOL:
            return name
    return f"??{t:.2f}x{w:.2f}"


# ----- section + treatment mapping -----------------------------------------

# Parts that should be PT (ground contact / floor system)
PT_SECTIONS = {"Skids", "Floor"}


def section_for(name):
    n = name.lower()
    if n == "" or "skid" in n:
        return "Skids"
    if "floor joist" in n or "rim joist" in n or "sub floor" in n or "subfloor" in n:
        return "Floor"
    if "fascia" in n or "rake board" in n:
        return "Roof"
    if "rake" in n:
        if "left" in n:
            return "Left rake wall"
        return "Right rake wall"
    if "roof" in n or "rafter" in n:
        return "Roof"
    if n.startswith("back wall"):
        return "Back wall"
    if n.startswith("front wall"):
        return "Front wall"
    if n.startswith("left wall") or n.startswith("left side wall"):
        return "Left wall"
    if n.startswith("right wall"):
        return "Right wall"
    if n == "inner volume":
        return None  # excluded
    return "Other"


SECTION_ORDER = [
    "Skids",
    "Floor",
    "Back wall",
    "Front wall",
    "Left wall",
    "Right wall",
    "Left rake wall",
    "Right rake wall",
    "Roof",
    "Other",
]

EXCLUDE_FROM_CUTLIST = {"inner volume"}
RENAME_UNNAMED = "skid"


# ----- stock-length optimization -------------------------------------------

KERF_IN = 0.125  # 1/8" saw kerf per cut

# Standard stock lengths in inches per lumber type
STOCK_LENGTHS = {
    "2x4": [96, 120, 144, 168, 192],                 # 8,10,12,14,16 ft
    "2x6": [96, 120, 144, 168, 192, 240],            # 8,10,12,14,16,20 ft
    "2x8": [96, 120, 144, 168, 192, 240],
    "2x10": [96, 120, 144, 168, 192, 240],
    "4x4": [96, 120, 144, 192],                      # 8,10,12,16 ft
    "4x6": [96, 120, 144, 192],
}


def ffd_bins(cuts, stock_len):
    """First-fit-decreasing bin packing into a single stock length.
    Kerf is charged *between* cuts only: N cuts in a bin consume
    sum(lengths) + (N-1) * kerf. Returns list of [items_used, remaining, items].
    """
    bins = []  # list of [used_in, [items]]
    for length, label in sorted(cuts, key=lambda x: -x[0]):
        placed = False
        for b in bins:
            # If bin already has content, a new cut needs an extra kerf
            need = length + (KERF_IN if b[1] else 0)
            if b[0] + need <= stock_len:
                b[0] += need
                b[1].append((length, label))
                placed = True
                break
        if not placed:
            if length > stock_len:
                bins.append([length, [(length, f"{label} — TOO LONG FOR {stock_len}\"")]])
            else:
                bins.append([length, [(length, label)]])
    return bins


def rightsize_bin(used_in, allowed_stock):
    """Return smallest stock length >= used_in, or largest if nothing fits."""
    for sl in sorted(allowed_stock):
        if sl >= used_in:
            return sl
    return max(allowed_stock)


def pack_and_rightsize(cuts, allowed_stock):
    """For each candidate "target" stock size, FFD-pack into that size, then
    right-size each bin to the smallest stock that fits its content.
    Return the (stock_len, used_in, items) list with the lowest total LF.

    Packing into different target sizes produces different bin structures —
    a smaller target forces single-cut-per-bin for long cuts, which can be
    cheaper once each bin is right-sized to its content.
    """
    best = None
    for target in sorted(set(allowed_stock)):
        raw = ffd_bins(cuts, target)
        # Some bins may hold cuts that exceed `target` (because too long for
        # it); right-size them to the actual needed stock.
        sized = [(rightsize_bin(used, allowed_stock), used, items) for used, items in raw]
        total = sum(sl for sl, _, _ in sized)
        if best is None or total < best[0]:
            best = (total, sized)
    return best[1]


# ----- main ----------------------------------------------------------------


def main():
    data = json.loads(Path("scripts/oriented_dims.json").read_text())

    # (section, lumber, length_in, treatment, name) -> qty
    agg = defaultdict(int)

    for r in data:
        name = r["name"] or RENAME_UNNAMED
        if name in EXCLUDE_FROM_CUTLIST:
            continue
        sec = section_for(name)
        if sec is None:
            continue
        dims = sorted([r["dx"], r["dy"], r["dz"]], reverse=True)
        length, width, thick = dims

        if name == "sub floor osb":
            # sheet good: group as is
            agg[(sec, "OSB 3/4\" 4x8 (half sheets used)", round(length, 2), "—", name)] += 1
            continue

        lumber = classify(thick, width)
        treatment = "PT" if sec in PT_SECTIONS else "KD"
        agg[(sec, lumber, round(length, 2), treatment, name)] += 1

    # Build markdown cut list grouped by section
    out_md = Path("CUT_LIST.md")
    with out_md.open("w") as f:
        f.write("# Bike shed cut list\n\n")
        f.write("Source: Onshape \"wood bike shed\" Part Studio 1. Actual dimensions.\n\n")
        f.write("- **PT** = pressure-treated, ground-contact rated (skids + floor system)\n")
        f.write("- **KD** = kiln-dried dimensional lumber, framing grade (SPF #2 or equivalent)\n")
        f.write("- Saw kerf allowance: 1/8\" per cut (used in stock-length optimization)\n\n")

        for section in SECTION_ORDER:
            rows = [k for k in agg if k[0] == section]
            if not rows:
                continue
            f.write(f"## {section}\n\n")
            f.write("| Qty | Lumber | Treatment | Length | Name |\n")
            f.write("|---:|:---|:---:|---:|:---|\n")
            # Sort within section by (lumber, -length, name)
            rows.sort(key=lambda k: (k[1], -(k[2] or 0), k[4]))
            for key in rows:
                sec, lumber, length, treatment, name = key
                qty = agg[key]
                ft = int(length // 12)
                inch = length - ft * 12
                if "OSB" in lumber:
                    f.write(f"| {qty} | {lumber} | — | {length:.0f}\u2033 × 48\u2033 | {name} |\n")
                else:
                    f.write(f"| {qty} | {lumber} | {treatment} | {ft}\u2032 {inch:.2f}\u2033 ({length:.2f}\u2033) | {name} |\n")
            f.write("\n")

        # ----- stock optimization -----
        f.write("## Stock-length order list\n\n")
        f.write("First-fit-decreasing bin packing, one pass per (lumber, treatment). ")
        f.write("For each group, the stock length shown minimizes total linear feet purchased. ")
        f.write("Kerf: 1/8\" per cut.\n\n")

        # Group all cuts by (lumber, treatment)
        order_groups = defaultdict(list)  # (lumber, treatment) -> [(length, label)]
        for key, qty in agg.items():
            sec, lumber, length, treatment, name = key
            if "OSB" in lumber or "??" in lumber:
                continue
            for i in range(qty):
                label = f"{name} ({sec})"
                order_groups[(lumber, treatment)].append((length, label))

        total_cost_in = 0
        group_order_summary = {}  # (lumber, treatment) -> dict[stock_ft] = qty
        for (lumber, treatment), cuts in sorted(order_groups.items()):
            stock_choices = STOCK_LENGTHS.get(lumber, [96, 120, 144, 192])
            # Ensure we have at least one stock long enough for every cut
            maxcut = max(c[0] for c in cuts)
            if maxcut > max(stock_choices):
                stock_choices = list(stock_choices) + [int(maxcut + 0.9)]

            bins = pack_and_rightsize(cuts, stock_choices)
            total_in = sum(sl for sl, _, _ in bins)
            total_cost_in += total_in
            actual_in = sum(c[0] for c in cuts)

            # Summarize by stock length
            sl_counts = defaultdict(int)
            for sl, _, _ in bins:
                sl_counts[sl] += 1
            order_summary = ", ".join(
                f"{n} × {sl/12:g}\u2032" for sl, n in sorted(sl_counts.items())
            )
            group_order_summary[(lumber, treatment)] = dict(sl_counts)

            waste_in = total_in - actual_in
            waste_pct = 100.0 * waste_in / total_in if total_in else 0
            f.write(f"### {lumber} {treatment} — order **{order_summary}** "
                    f"({total_in/12:.1f} LF purchased, {actual_in/12:.1f} LF cuts, {waste_pct:.1f}% waste)\n\n")
            for i, (sl, used, items) in enumerate(bins, 1):
                items_desc = "; ".join(f"{l:.2f}\u2033 {lbl}" for l, lbl in items)
                remaining = sl - used
                f.write(f"- Board {i} ({sl/12:g}\u2032): {items_desc}  — waste: {remaining:.2f}\u2033\n")
            f.write("\n")

        # OSB summary
        osb_pieces = sum(qty for key, qty in agg.items() if "OSB" in key[1])
        if osb_pieces:
            # Each OSB cut is 72"×48" (half sheet). Standard sheet is 96"×48".
            full_sheets = (osb_pieces + 1) // 2  # pairs of half-sheets => one full sheet
            f.write(f"### OSB 3/4\" 4×8 sheets\n\n")
            f.write(f"{osb_pieces} half-sheets (72\"×48\") needed → **order {full_sheets} full 4×8 sheets**, rip to 72\"+24\" offcut.\n\n")
            f.write(f"(Or cut 2 half-sheets per full sheet with 0\" waste if both offcuts are usable elsewhere.)\n\n")

        f.write(f"---\n\n**Total dimensional lumber LF purchased: {total_cost_in/12:.1f}**\n")

    # CSV: quote-friendly rollup, one row per (lumber, treatment, stock length)
    out_csv = Path("order_list.csv")
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lumber", "treatment", "stock_length_ft", "qty", "notes"])
        for (lumber, treatment), sl_counts in sorted(group_order_summary.items()):
            for sl, n in sorted(sl_counts.items()):
                w.writerow([lumber, treatment, f"{sl/12:g}", n, ""])
        if osb_pieces:
            w.writerow(["OSB 3/4\"", "—", "4x8 sheet", (osb_pieces + 1) // 2, "subfloor; rip to 72\"+24\""])

    print(f"Wrote {out_md} and {out_csv}")


if __name__ == "__main__":
    main()
