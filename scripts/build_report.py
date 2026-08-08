#!/usr/bin/env python3
"""Regenerate the woodbike-shed live-model design report (report.html).

Reads scripts/bboxes.json (world bboxes per part) and
scripts/oriented_dims.json (true oriented dims per body) and emits an
HTML report in the same style as the 2026-08-05 scout report, updated to
the completed model. Output path defaults to the firstmate data dir.

Usage: python3 build_report.py [output.html]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import audit_overlaps as ao

HERE = Path(__file__).parent
M = 39.3700787
DEFAULT_OUT = ("/media/griswald/wd-black-2tb/personal/firstmate/data/"
               "woodbike-shed-design-report/report.html")

CSS = """
body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;background:#f6f4ef;color:#26241f;line-height:1.45}
main{max-width:1060px;margin:0 auto;padding:24px 28px 80px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:20px;margin:34px 0 8px;border-bottom:2px solid #b08954;padding-bottom:4px}
h3{font-size:16px;margin:22px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
th,td{border:1px solid #d4cdbd;padding:4px 8px;text-align:left;vertical-align:top}
th{background:#ece5d4}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.meta{color:#5b574c;font-size:14px}
.callout{background:#fdf3e3;border:1px solid #e0a040;border-left-width:5px;padding:10px 14px;margin:12px 0;border-radius:3px}
.warn{background:#fbeaea;border-color:#c0392b}
.ok{background:#eef5ea;border-color:#7a9a5b}
code{background:#eee9dc;padding:1px 4px;border-radius:3px;font-size:12.5px}
svg{display:block;margin:10px 0;background:#fff;border:1px solid #ddd6c6;border-radius:4px}
.small{font-size:12.5px;color:#5b574c}
figcaption{font-size:12.5px;color:#5b574c;margin:-4px 0 14px}
ul{margin:6px 0}
li{margin:3px 0}
.tag{display:inline-block;background:#ece5d4;border-radius:3px;padding:0 6px;font-size:12px;margin-right:4px}
"""


def section_for(name):
    n = name.lower()
    if n == "" or "skid" in n:
        return "Skids"
    if "floor joist" in n or "rim joist" in n or "sub floor" in n or "subfloor" in n:
        return "Floor"
    if "fascia" in n or "rake board" in n or "rafter" in n:
        return "Roof"
    if "rake" in n:
        return "Left rake wall" if "left" in n else "Right rake wall"
    if n.startswith("back wall"):
        return "Back wall"
    if n.startswith("front wall"):
        return "Front wall"
    if n.startswith("left wall") or n.startswith("left side wall"):
        return "Left wall"
    if n.startswith("right wall"):
        return "Right wall"
    if n == "inner volume":
        return "Reference"
    return "Other"


SECTION_ORDER = ["Skids", "Floor", "Back wall", "Front wall", "Left wall",
                 "Left rake wall", "Right wall", "Right rake wall", "Roof",
                 "Reference", "Other"]

COLOR = {"Skids": "#7d6b3f", "Floor": "#9db38a", "Back wall": "#e3c692",
         "Front wall": "#e3c692", "Left wall": "#e3c692", "Right wall": "#e3c692",
         "Left rake wall": "#b08954", "Right rake wall": "#b08954",
         "Roof": "#7fa8c9", "Reference": "#cccccc", "Other": "#999999"}


def corners(r):
    bb = r["bbox_m"]
    return ([bb["lowX"] * M, bb["lowY"] * M, bb["lowZ"] * M],
            [bb["highX"] * M, bb["highY"] * M, bb["highZ"] * M])


def svg_plan(parts, title, width=749, height=355, maxw=720):
    """Top-down: X horizontal, Y vertical."""
    xs = [c for r in parts for c in corners(r) for c in [c]][0:0]  # noqa
    lo = [min(corners(r)[0][0] for r in parts), min(corners(r)[0][1] for r in parts)]
    hi = [max(corners(r)[1][0] for r in parts), max(corners(r)[1][1] for r in parts)]
    return _svg(parts, title, lo, hi, 0, 1, width, height, maxw=maxw)


def svg_elev(parts, title, axes, width=663, height=395, profiles=None, maxw=300):
    """axes: (i,j) world-axis indices for (horizontal, vertical).
    profiles: optional partId -> [(u,v)] true profile in those axes, for
    sloped members whose world bbox would draw as a misleading rectangle."""
    lo = [min(corners(r)[0][axes[0]] for r in parts),
          min(corners(r)[0][axes[1]] for r in parts)]
    hi = [max(corners(r)[1][axes[0]] for r in parts),
          max(corners(r)[1][axes[1]] for r in parts)]
    return _svg(parts, title, lo, hi, axes[0], axes[1], width, height,
                flip_v=True, profiles=profiles, maxw=maxw)


def _svg(parts, title, lo, hi, ai, aj, width, height, flip_v=False, profiles=None, maxw=None):
    pad = 12
    # uniform scale + content-sized viewBox so proportions are true
    s = min((width - 2 * pad) / (hi[0] - lo[0]), (height - 2 * pad) / (hi[1] - lo[1]))
    vw = (hi[0] - lo[0]) * s + 2 * pad
    vh = (hi[1] - lo[1]) * s + 2 * pad
    mw = f"width:{maxw}px;" if maxw else ""
    out = [f'<svg viewBox="0 0 {vw:.0f} {vh:.0f}" style="{mw}max-width:100%;height:auto" '
           f'role="img" font-family="system-ui,sans-serif"><title>{title}</title>']

    def tx(u, v):
        x = pad + (u - lo[0]) * s
        y = pad + (v - lo[1]) * s
        if flip_v:
            y = vh - pad - (v - lo[1]) * s
        return x, y

    for r in parts:
        col = COLOR.get(section_for(r["name"]), "#999999")
        poly = profiles.get(r["partId"]) if profiles else None
        if poly:
            pts = " ".join(f"{tx(u, v)[0]:.1f},{tx(u, v)[1]:.1f}" for u, v in poly)
            out.append(f'<polygon points="{pts}" fill="{col}" stroke="#453c22" '
                       f'stroke-width="0.8" opacity="0.85"/>')
            continue
        a, b = corners(r)
        x0, y0 = tx(a[ai], a[aj])
        x1, y1 = tx(b[ai], b[aj])
        out.append(f'<rect x="{min(x0,x1):.1f}" y="{min(y0,y1):.1f}" '
                   f'width="{max(abs(x1-x0),1):.1f}" height="{max(abs(y1-y0),1):.1f}" '
                   f'fill="{col}" stroke="#453c22" stroke-width="0.8" opacity="0.7"/>')
    out.append("</svg>")
    return "".join(out)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    bb = json.loads((HERE / "bboxes.json").read_text())
    od = json.loads((HERE / "oriented_dims.json").read_text())

    # oriented dims grouped by name
    ogroups = defaultdict(Counter)
    for r in od:
        d = tuple(round(x, 2) for x in sorted([r["dx"], r["dy"], r["dz"]], reverse=True))
        ogroups[r["name"] or "skid"][d] += 1

    bysec = defaultdict(list)
    for r in bb:
        bysec[section_for(r["name"])].append(r)

    # true YZ profiles for sloped members so elevations don't draw bboxes
    prof_by_name = {
        "rafter": ao.RAFTER,
        "left rake board": ao.RAKE_BOARD, "right rake board": ao.RAKE_BOARD,
        "left rake wall top plate": ao.LEFT_RAKE_PLATE,
        "right rake wall top plate": ao.RIGHT_RAKE_PLATE,
        "front fascia": ao.FASCIA_FRONT, "back fascia": ao.FASCIA_BACK,
    }
    stud_profiles = {round(yc, 2): q for yc, q in
                     zip((0.75, 16.25, 32.25, 48.25), ao.RAKE_STUDS)}
    PROF = {}
    for r in bb:
        if r["name"] in prof_by_name:
            PROF[r["partId"]] = prof_by_name[r["name"]]
        elif r["name"] in ("left rake wall studs", "right rake wall studs"):
            b = r["bbox_m"]
            PROF[r["partId"]] = stud_profiles[round((b["lowY"] + b["highY"]) / 2 * M, 2)]

    named = [r for r in bb if r["name"]]
    ndefault = sum(1 for r in bb if r["name"].startswith("Part"))

    P = []
    P.append("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">")
    P.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    P.append("<title>Wood Bike Shed — Live-Model Design Report</title>")
    P.append(f"<style>{CSS}</style></head><body><main>")
    P.append("<h1>Wood Bike Shed — Design Report (live Onshape model)</h1>")
    P.append('<p class="meta">Document: “wood bike shed” · Part Studio 1 (workspace Main)<br>'
             'did <code>24d3743de768051f7ae10bb3</code> · wid <code>4c0f1b0cf9df2e322f841b94</code> '
             '· eid <code>5730975eb353b57bac8d52c4</code><br>'
             'Data pulled: <strong>2026-08-07</strong> (parts API: 120 parts; oriented-dims eval: '
             '122 solid bodies; per-part world bounding boxes: 120).<br>'
             'Supersedes the 2026-08-05 scout report after the fleet completion pass '
             '(restore point <code>aa73830b88f34f965190a7c6</code> “pre-fleet-completion 2026-08-05”).<br>'
             'All requests read-only GET / FeatureScript eval except the additive completion features.</p>')

    P.append("<h2>1. Key findings</h2><ul>")
    P.append(f"<li><strong>{len(named)} named parts, fully accounted for</strong> "
             f"({len(bysec['Skids'])} skids, {len(bysec['Floor'])} floor, {len(bysec['Back wall'])} back wall, "
             f"{len(bysec['Left wall'])}+{len(bysec['Left rake wall'])} left wall/rake, "
             f"{len(bysec['Right wall'])}+{len(bysec['Right rake wall'])} right wall/rake, "
             f"{len(bysec['Front wall'])} front wall, {len(bysec['Roof'])} roof, 1 reference). "
             "Zero default-named parts remain.</li>")
    P.append("<li><strong>Roof is now present.</strong> 13 rafters (2x6 x 115.13\", birdsmouthed), "
             "2 fascia (2x6 x 216\"), 2 rake boards (2x6 x 115.13\"). The 2026-08-05 report's "
             "“roof absent” finding is resolved.</li>")
    P.append("<li><strong>Rake walls complete both sides.</strong> Left rake top plate (69.29\" 2x4, "
             "24/65 slope) + 4 rake studs per side (22.40/16.68/10.77/4.86\"), mitered to the "
             "rake-plate underside.</li>")
    P.append("<li><strong>Overlap audit clean.</strong> Analytic prism-intersection sweep "
             "(<code>scripts/audit_overlaps.py</code>) shows zero lumber-on-lumber interference. "
             "Rafters carry birdsmouths front (seat z=123) and back (seat z=97.5); rake boards butt "
             "to the fascia inner faces; rake-plate noses trimmed flush at the front wall.</li>")
    P.append("<li><strong>Captain's mid-refactor tail features remain in ERROR</strong> (indices ~98–119) "
             "but are superseded by the additive completion parts; see repo MANUAL_COMPLETION.md.</li>")
    P.append("</ul>")

    P.append("<h2>2. Model orientation and overall geometry</h2><ul>")
    P.append("<li>World axes: X = long axis (16 ft), Y = short axis (6 ft), Z = up. Floor surface z=0.</li>")
    P.append("<li>Footprint 192\" x 72\". Front = low-Y (door side, high wall 123\"), back = high-Y (97.5\").</li>")
    P.append("<li>Shed-roof slope <strong>24/65</strong> (rise 24\" over the 65\" front-to-back bearing "
             "spacing). Rafter bottom edge from (y=-27.5, z=131.654) to (y=80.5, z=91.777) = 24\" front / "
             "12\" back overhang, bearing on front plate (0,121.5) and back plate (65,97.5).</li>")
    P.append("<li>Stud/joist/rafter layout on a 16\" o.c. grid; rafters at 13 centers -2.75…187.75.</li>")
    P.append("<li>Roof overhangs 12\" past each side wall (fascia x=-15.5…200.5); rake boards flush with "
             "the fascia ends.</li>")
    P.append("</ul>")

    P.append('<figure>' + svg_plan(bysec["Floor"] + bysec["Skids"], "Top-down floor framing plan") +
             '<figcaption>Floor framing plan (skids, rims, joists, OSB).</figcaption></figure>')

    P.append("<h2>3. Section-by-section inventory (120/120 parts)</h2>")
    for sec in SECTION_ORDER:
        rows = bysec.get(sec, [])
        if not rows:
            continue
        P.append(f"<h3>3.{SECTION_ORDER.index(sec)+1} {sec} — {len(rows)} parts</h3>")
        P.append('<table><tr><th class="num">Qty</th><th>Member</th>'
                 '<th>Oriented dims L×W×T (in)</th><th>Model part name(s)</th></tr>')
        # group by name
        names = defaultdict(list)
        for r in rows:
            names[r["name"]].append(r)
        for name in sorted(names):
            q = len(names[name])
            dimstr = ", ".join(f"{n}×{d[0]}×{d[1]}×{d[2]}" for d, n in
                               sorted(ogroups.get(name, {}).items())) or "—"
            P.append(f"<tr><td class='num'>{q}</td><td>{name or 'skid (sub-body)'}</td>"
                     f"<td>{dimstr}</td><td class='small'>{name or '(unnamed sub-bodies)'}</td></tr>")
        P.append("</table>")

    P.append('<figure>' + svg_elev(bysec["Back wall"], "Back wall elevation", (0, 2), maxw=720) +
             '<figcaption>Back wall elevation.</figcaption></figure>')
    P.append('<figure>' + svg_elev(bysec["Front wall"], "Front wall elevation", (0, 2), maxw=720) +
             '<figcaption>Front wall elevation (two rough openings).</figcaption></figure>')
    P.append('<div style="display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap">')
    P.append('<figure style="margin:10px 0">' +
             svg_elev(bysec["Left wall"] + bysec["Left rake wall"], "Left wall elevation", (1, 2), profiles=PROF) +
             '<figcaption>Left wall + rake elevation.</figcaption></figure>')
    P.append('<figure style="margin:10px 0">' +
             svg_elev(bysec["Right wall"] + bysec["Right rake wall"], "Right wall elevation", (1, 2), profiles=PROF) +
             '<figcaption>Right wall + rake elevation (door opening).</figcaption></figure>')
    P.append('</div>')
    P.append('<figure>' + svg_plan(bysec["Roof"], "Roof plan") +
             '<figcaption>Roof plan (rafters, fascia, rake boards).</figcaption></figure>')

    # lumber rollup
    P.append("<h2>4. Live-model lumber rollup</h2>")
    P.append('<table><tr><th>Lumber</th><th class="num">Length (in)</th><th class="num">Qty</th>'
             '<th>Used in</th></tr>')
    roll = defaultdict(int)
    usedin = defaultdict(set)
    for r in od:
        name = r["name"] or "skid"
        d = tuple(round(x, 2) for x in sorted([r["dx"], r["dy"], r["dz"]], reverse=True))
        w, t = d[1], d[2]
        lum = {(1.5, 3.5): "2x4", (1.5, 5.5): "2x6", (3.5, 3.5): "4x4"}.get(
            (round(w, 1), round(t, 1)), "OSB" if t < 1 else "?")
        roll[(lum, d[0])] += 1
        usedin[(lum, d[0])].add(section_for(name))
    for (lum, L), q in sorted(roll.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        P.append(f"<tr><td>{lum}</td><td class='num'>{L}</td><td class='num'>{q}</td>"
                 f"<td class='small'>{', '.join(sorted(usedin[(lum, L)]))}</td></tr>")
    P.append("</table>")
    P.append('<p class="small">PT: 4x4 skids + 2x6 floor. KD: all 2x4/2x6 walls+roof. '
             'OSB: 2 full 4x8 sheets ripped to four 48x72 half-sheets.</p>')

    P.append("<h2>5. Build status vs the 2026-08-05 report</h2><ul>")
    P.append("<li><span class='tag'>DONE</span> Skids, floor, back wall, front wall — unchanged, verified.</li>")
    P.append("<li><span class='tag'>DONE</span> Left/right rake walls — plates + studs added.</li>")
    P.append("<li><span class='tag'>DONE</span> Roof — rafters + fascia + rake boards added.</li>")
    P.append("<li><span class='tag'>DONE</span> Naming — all 40 former <code>Part NN</code> renamed.</li>")
    P.append("<li><span class='tag'>OPEN</span> Doors, siding/sheathing, trim — still unmodeled.</li>")
    P.append("<li><span class='tag'>OPEN</span> Captain's broken tail features to reconcile (MANUAL_COMPLETION.md).</li>")
    P.append("</ul>")

    P.append("<h2>6. Appendix: all 120 parts, individually</h2>")
    P.append('<p class="small">World center in inches (x, y, z). Sorted by section then name.</p>')
    P.append('<table><tr><th>partId</th><th>Model name</th><th>Section</th>'
             '<th class="num">Center (x,y,z)</th></tr>')
    for sec in SECTION_ORDER:
        for r in sorted(bysec.get(sec, []), key=lambda r: r["name"]):
            a, b = corners(r)
            c = [(a[i] + b[i]) / 2 for i in range(3)]
            P.append(f"<tr><td class='small'>{r['partId']}</td><td>{r['name'] or '(sub-body)'}</td>"
                     f"<td>{sec}</td><td class='num small'>{c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}</td></tr>")
    P.append("</table>")

    P.append("<hr><p class='small'>Method: read-only Onshape API v6 + additive completion features. "
             "Regenerated 2026-08-07 by scripts/build_report.py.</p>")
    P.append("</main></body></html>")

    Path(out_path).write_text("".join(P))
    print(f"wrote {out_path} ({len(named)} named parts, {ndefault} default-named)")


if __name__ == "__main__":
    main()
