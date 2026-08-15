---
page: conventions
title: How this guide is drawn and written
prev: index.md
---

# How this guide is drawn and written

This page is the guide's own account of its rules — what a reader can rely on, and what a
maintainer must keep true when the guide changes. The pages are Markdown files in this
folder, one per page, with figures as SVG files beside them in `figures/`.

## Numbers

- Lengths are written **feet-inches-eighths**: 9' 7⅜", never a long decimal of inches.
- Heights are written **measured up from the deck top**, the guide's zero: "40 inches above
  the deck".
- Horizontal positions are written as **tape readings from a named physical mark**:
  "16 inches on centre, measured from the left end mark".
- Parts are written as **cut-list name, nominal size, cut length**: "rafter · 2×6 · 9' 7⅜\"".

Why no coordinates, ever: this guide is read outdoors with a tape in hand, and the building
has no axis system on it. Model coordinates are traceability between the guide and the model
code, not instruction. They live in non-rendering source comments in the page files (and in
the sources appendix), and never in text, captions, or figures. If you edit a page, keep it
that way.

## Figures

Every figure is a hand-drawn SVG in `figures/`, named `fig-<page number>-<slug>.svg`, and
follows these rules:

- **View badge, top-left, always.** Three facts: the view type word (ELEVATION, PLAN,
  SECTION, ISO); which way you look, in building terms ("viewed from the street"); and a
  frame anchor — a gravity arrow on elevations and sections, the cut height on plans and
  sections, an axis corner on ISO views. The symbol key on the start page shows the badge
  with its three fields labelled.
- **The drawing declares its own frame.** A reader must be able to tell which way a figure
  faces from the drawing alone, before reading a word of caption. Elevations and sections
  carry a ground or deck line and a gravity arrow; plans and sections carry hatched cut
  material and a labelled cut line whose source view is shown in a neighbour figure. A strip
  stack with no frame cues is the one unforgivable figure: an earlier version of this guide
  drew the door-jamb finish layers as bare parallel strips, and every reader's eye read them
  as vertical boards on an elevation, because nothing in the drawing said "you are looking
  down". The fix is structural — hatching, cut line, locator — not a louder caption.
- **Fixed cameras.** Whole-shed ISO views use one oblique camera: the front elevation drawn
  true, depth receding up and to the right at half scale, verticals vertical, viewed from the
  street with the right corner toward you (the finished-shed figure on the start page is the
  reference). One fixed elevation per wall, one fixed section plane per detail. If a view
  must change, the figure says so in words.
- **No part is drawn alone.** Every new member appears with at least two neighbours and one
  datum edge, coloured by state: new work full colour, already-built work grey outline,
  future work dashed.
- **Every new member gets an arrow to its seat**, and the attachment-mode symbol at the
  joint — nail pattern, screw, hinge, or seat cut. This building's parts fasten in different
  ways; "it's obvious where it goes" is not true here.
- **One figure, one message.** A zoom that carries the message is the figure; the wide view
  becomes a small locator.
- **Labels are leader lines** carrying the part name, nominal size and cut length.
- **Captions** carry: number, what the figure shows, view type, where in the build, and one
  takeaway sentence.
- **Site legibility.** Text in figures is at least 3 mm cap height at A4 print size, cut
  edges at least 0.5 mm line weight, high contrast for sunlight.

The **symbol key** (`figures/fig-00-symbol-key.svg`, shown on the start page) is the only
place symbols are defined. Use those marks; if a figure genuinely needs one the key lacks,
that is a note for the maintainers, not a quietly invented glyph.

## Pages

Each page is one Markdown file starting with front matter — `page`, `title`, `stage`
("Stage N of 12" on the twelve build stages only), and `prev` / `next` filenames following
the canonical reading order (start page → what you're building → the two order pages →
Stages 1–12 → troubleshooting → the two references). The `prev`/`next` links are written even
for pages that do not exist yet in your copy; they resolve once everything is together.

Body rules: one action per numbered step (a step containing "and then" is two steps); one
figure per step where a figure is warranted; safety messages at the exact step that carries
the hazard, in the warning format from the symbol key; and every page ends with a "Before you
move on" checklist whose checks name the tool that verifies them.

Tone: plain, direct, second person. "Set the pedestals", not "the pedestals should be set".

## The PDF for the job site

`build-pdf.sh` in this folder assembles the pages in canonical reading order into one PDF.
Prerequisite: **python3 with the standard library, and WeasyPrint** (the `weasyprint`
command, or importable by python3) — both already on this machine; nothing else is installed
by the script. Run it from anywhere:

    docs/guide/build-pdf.sh                 # writes docs/guide/build-guide.pdf
    docs/guide/build-pdf.sh out.pdf         # or a path of your choice
    PAPER=letter docs/guide/build-pdf.sh    # A4 is the default

Pages that do not exist yet are skipped with a warning instead of failing, so the PDF always
reflects what is written so far. On paper each page starts on a new sheet, figures never
split across a break, and text prints dark on white while the figure colour states keep
their colour (they carry meaning).

## What this guide does not cover

Wall sheathing, roofing, fasteners and paint are not modeled and are on neither lumber order.
The guide says so at the steps where it matters, and never invents quantities for them.
