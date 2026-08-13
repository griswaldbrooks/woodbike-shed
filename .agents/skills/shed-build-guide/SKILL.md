---
name: shed-build-guide
description: Authoring method for the woodbike-shed build guide — page format, number-writing rules, figure conventions, and the checks every change must pass. Use when writing or editing a page of the shed build guide, drawing or revising a figure for it, adding a build stage, or reviewing guide changes.
---

# Shed build guide — authoring method

The guide lives in `docs/guide/`: one Markdown file per page, SVG figures in
`docs/guide/figures/`, assembled into a job-site PDF by `docs/guide/build-pdf.sh`.
Its reader-facing statement of the rules is `docs/guide/conventions.md`; this
skill is the maintainer's copy of the method, and `REFERENCE.md` beside this
file carries the full figure specification, the page template, the sourced
principles behind each rule, and the door-jamb worked example. Read it before
any non-trivial change.

The reader builds outdoors, tape in hand, possibly from a paper printout.
Everything below serves that reader.

## Sources of truth

Guide numbers come from the model, never invented: `cad/*.py` + `cad/verify.py`,
`CUT_LIST.md`, `order_list.csv`, `order_list_finish.csv`. If a page disagrees
with the model, fix the page. Wall sheathing, roofing, fasteners and paint are
NOT modeled and are on neither lumber order — say so where it matters and never
invent quantities for them.

## Workflow

1. Read `docs/guide/conventions.md`, the page or figure you are changing, and
   its neighbours — the prev/next chain must stay intact.
2. Take every number from the sources of truth above.
3. Write to the page template in `REFERENCE.md`, or draw to the figure spec
   there, applying the two rules below as you go.
4. Run the anti-ambiguity test on every new or revised figure.
5. Grep your change for coordinate leakage: `z `, `x `, `y `, `…` ranges, bare
   decimals like `22.773"`. Rendered text, captions and figure labels must be
   clean; model traces only inside non-rendering HTML comments.
6. Regenerate the PDF (`docs/guide/build-pdf.sh`) and check your pages,
   including figure sizing and any 1:1 template page.

## Rule 1 — the anti-ambiguity test (every figure)

A figure's frame of reference must be decidable from the drawing alone, before
a word of caption is read. Test: **if the drawing still looks plausible after
swapping vertical with depth, it fails and must be redrawn.**

Concrete failure it catches: a wall band beside four parallel finish strips
reads identically as an elevation (vertical boards on the wall), a section
(layers through the wall) or a plan (the same strips from above) — and every
reader's eye picks the canonical default, vertical boards. The fix is
structural, not a louder caption:

- every elevation and section carries a ground or deck line **and** a gravity
  arrow;
- every plan and section carries hatched cut material plus a labelled cut line
  whose source view appears in a neighbouring figure;
- every figure carries a top-left view badge naming the view type, the viewing
  direction in building terms, and the frame anchor. No naked strip stacks.

The worked redraw (elevation locator coupled to a hatched section by cut line
A–A) is in `REFERENCE.md`, "Worked example".

## Rule 2 — no model coordinates, ever (every number)

The building has no axis system on it. Never render model coordinates in text,
captions, labels or figures — no `z = -6.75"`, no `(y −3.5…−4.25)`, no bare
decimals. Instead:

- lengths as feet-inches-eighths: `9' 7⅜"`, never `115.344"`;
- heights measured up from the deck top, the guide's zero: "40 inches above the
  deck", never "z 40";
- horizontal positions as tape readings from a named mark: "16 inches on
  centre from the left end mark";
- parts as cut-list name + nominal size + cut length: `rafter · 2×6 · 9' 7⅜"`.

Coordinates are traceability, not instruction. They live only in
non-rendering source comments, e.g.
`<!-- model trace: siding y -3.5...-4.25; casing -4.25...-5.0 -->`, and in the
sources appendix page.

## Everything else lives in REFERENCE.md

Full figure specification (view badge, fixed cameras, context and attachment
rules, one-figure-one-message, captions, symbol key, 1:1 templates, site
legibility, error-state frames), the page file template and canonical page
order, the figure failure's forensics, the sourced instruction-design
principles behind each rule, and what does NOT transfer from IKEA/LEGO kit
design.
