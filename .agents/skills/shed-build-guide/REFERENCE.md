# Shed build guide — full reference

Companion to `SKILL.md`. The guide's own reader-facing statement of the same
rules is `docs/guide/conventions.md`; when the two ever diverge, that page is
what the reader sees, so reconcile it in the same change.

## 1. Figure specification

Figures are hand-authored SVG in `docs/guide/figures/`, named
`fig-<page number>-<slug>.svg`, referenced from their page as
`![Fig 4.1 — caption text](figures/fig-04-a.svg)`. They must stay legible at
phone size and printed on paper.

**P1 — View badge (mandatory, top-left of every figure).** Three fields: the
view type word (ELEVATION / PLAN / SECTION / ISO); the viewing direction in
building terms ("viewed from the street"); and the frame anchor — a gravity
arrow for elevations and sections ("DOWN"), the cut height for plans and
sections ("horizontal cut 40\" above deck"), an axis corner for ISO views.
The badge replaces the reader's assumption with a fact before the first
fixation lands on geometry.

**P2 — Anti-ambiguity rule.** The frame must be decidable from the drawing
alone, without the caption. Test: if the drawing still looks plausible after
swapping vertical with depth, it fails. Every elevation/section needs a
ground-or-deck line plus a gravity arrow; every plan or section needs hatched
cut material and a labelled cut line whose source view is shown in a
neighbouring figure. No naked strip stacks. See §2 for the failure this rule
exists because of, and §6 for the worked fix.

**P3 — Fixed camera.** One default oblique ISO for whole-shed figures (front
elevation drawn true, depth receding up and to the right at half scale,
verticals vertical, viewed from the street with the right corner toward you —
the finished-shed figure on the start page is the reference); one fixed
elevation per wall; one fixed section plane per detail. If a view must change,
say so in words on the figure ("now viewed from the left gable end"), with a
transition locator.

**P4 — Context rule.** No part is ever drawn alone. Every figure of a new
member shows at least two neighbours and one datum edge (deck edge, wall face,
plate top). Colour convention: **new work = full colour, already-built = grey
outline, future work = dashed.** Prior context stays visible; the attachment
point is never occluded.

**P5 — Attachment arrows.** Every new member gets an arrow to its seat or
attachment point, plus the attachment-mode symbol from the start page's symbol
key (nail pattern, screw, hinge, seat cut). A shed's parts fasten in different
ways, so "it's obvious where it goes" is not true here; structural diagrams
alone are invalid for this build.

**P6 — One figure, one message.** A zoom inset counts as a second figure: if
the inset carries the message, promote it to the figure and make the wide
view a small locator. No legend + plan + inset + notes stacks.

**P7 — Labels.** Leader lines carrying cut-list name + nominal size + cut
length (`rafter · 2×6 · 9' 7⅜"`). Never coordinates; the full number-writing
rules are in §4 below.

**P8 — Caption contract.** Number + what it shows + view type + where in the
build + one takeaway sentence. No coordinates in captions.

**P9 — Symbol key, defined once.** `figures/fig-00-symbol-key.svg` (shown on
the start page) is the only place symbols are defined: highlight colours,
grey/dashed states, arrows, the red circle+bar prohibition style for
error-state frames, the warning triangle. Use those marks; if a figure
genuinely needs one the key lacks, that is a note for the maintainers, not a
quietly invented glyph. No invented symbols where ISO 7010 ones exist.

**P10 — Full-size templates.** 1:1 printable profiles where a bevel or seat is
hard to measure: the birdsmouth, rake-plate seat angle, casing mitres. In the
PDF each prints 1:1 on its own zero-margin named page (the `figure.truesize`
mechanism in `assets/guide.css`); keep any new full-size template on that
mechanism.

**P11 — Site legibility.** Figure text at least 3 mm cap height at A4 print
size (4 mm for phone-at-arm's-length); cut edges at least 0.5 mm line weight;
high contrast for sunlight.

**P12 — Redundancy for critical messages.** Anything safety-critical appears
in at least two channels: symbol + text, figure + embedded warning.

**P13 — Error-state frames.** Crossed-out frames in the prohibition style at
the failure points this build actually has: block not under the skid bearing
point, jack stud on the wrong side of the plate, rafter seated on one plate
only, siding course started without the skirt.

## 2. The failure that motivated the spec

An earlier revision of the single-page guide (the lineage now kept read-only
at `docs/build-guide.html`) drew the door-jamb finish layers as one wide wall
band plus four parallel strips stacked outward, each a tall rectangle, under a
title that called it a section. Its projection mapped model depth onto the
horizontal axis and height onto the vertical — but nothing in the drawing said
so: no gravity or ground cue, no cut indicator, no locator, no viewing
direction. The word "section" appeared only in the title; the caption led with
layer names and model coordinates.

The composition is frame-ambiguous by construction: a wall band plus parallel
strips looks identical as an elevation (strips = vertical boards across the
wall), a section (strips = layers through the wall) or a plan (the same strips
from above). The reader's canonical default — boards standing vertical — wins,
exactly as reported from the job site: the frame error was invisible until the
text was found and read.

A later redraw moved in the right direction — the title said "plan view",
OUTSIDE/INSIDE arrows and an inset with legend appeared — but still failed:
the frame declaration lived in small text the reader had to hunt for; the
caption and note lines still rendered model coordinates; one figure carried
plan + inset + legend + notes, four messages at once; and the plan strip still
read as an elevation at first glance because nothing in the drawing plane
itself said "you are looking down" — no cut line, no hatching, no locator.

The lesson, encoded in P1/P2/P6: caption-only framing cannot fix a
frame-ambiguous drawing, because readers glance at figures while holding the
work, not paragraphs. The correction must be drawn — hatching, cut line,
locator, gravity arrow — and it must precede reading.

## 3. Page format

Each page is one Markdown file in `docs/guide/`, starting with exactly this
front matter shape, then the body:

```markdown
---
page: P04
title: Blocks and skids
stage: Stage 1 of 12
prev: 03-order-finish.md
next: 05-floor.md
---

# Stage 1 — Blocks and skids

> **Goal:** what exists when this page is done, in one sentence.
> **Crew:** 1 person · **Time:** about half a day · **Weather:** dry ground

## Before you start

... parts tick-off table, tools, safety for THIS page ...

## Steps

### 1. <One action, imperative>

...text... plus its figure

## Before you move on

- [ ] check with the tool that verifies it
```

Body rules:

- **One action per numbered step.** If a step contains "and then", split it.
- **One figure per step** where a figure is warranted.
- Safety messages go at the **exact step** that carries the hazard, not
  collected at the top. Format:
  `> ⚠️ **WARNING** — <hazard> · <consequence> · <how to avoid>`.
- Every page ends with a "Before you move on" checklist of verifiable
  completion checks, each naming the tool that checks it ("diagonals equal
  within ½\", checked with a tape").
- `stage:` runs "Stage N of 12" across the twelve build-stage pages only; the
  other pages omit the field.
- `prev:`/`next:` follow the canonical order below and are written even when
  the neighbouring page does not exist yet in the working copy.

Canonical reading order (use these exact filenames):

| Order | File | Page |
|---|---|---|
| 1 | `index.md` | Start here |
| 2 | `01-what-youre-building.md` | What you're building |
| 3 | `02-order-framing.md` | Order: framing + foundation |
| 4 | `03-order-finish.md` | Order: finish + hardware |
| 5 | `04-blocks-and-skids.md` | Stage 1 |
| 6 | `05-floor.md` | Stage 2 |
| 7 | `06-front-wall.md` | Stage 3 |
| 8 | `07-back-wall.md` | Stage 4 |
| 9 | `08-side-walls.md` | Stage 5 |
| 10 | `09-raise-and-brace.md` | Stage 6 |
| 11 | `10-rake-plates.md` | Stage 7 |
| 12 | `11-rafters.md` | Stage 8 |
| 13 | `12-fascia-and-roof.md` | Stage 9 |
| 14 | `13-skirt-and-siding.md` | Stage 10 |
| 15 | `14-trim.md` | Stage 11 |
| 16 | `15-doors.md` | Stage 12 |
| 17 | `16-troubleshooting.md` | If it doesn't fit |
| 18 | `r01-cut-list.md` | Reference: cut list |
| 19 | `r02-sources.md` | Reference: sources |

Adding a build stage means a new numbered page in this chain with updated
`prev`/`next` on its neighbours, figures prefixed with the page number, and
the stage count reviewed. Walls are framed flat on the deck (Stages 3–5) and
raised in Stage 6 — keep that sequencing straight in any summary text.

**Tone:** plain, direct, second person. "Set the blocks", not "the blocks
should be set". Short sentences. No coordinate-speak, no CAD vocabulary, no
marketing. The reader is competent with tools but has not built this shed
before.

## 4. Numbers — full rules

- **NEVER render model coordinates in visible text or captions.** No
  `z = -6.75"`, no `(y -3.5...-4.25)`, no `x 15.5...51.5`, no bare decimals
  like `22.773"`.
- Traceability goes in a **non-rendering HTML comment** in the Markdown
  source: `<!-- model trace: siding y -3.5...-4.25; casing -4.25...-5.0 -->`,
  and in the sources appendix page.
- Lengths render as **feet-inches-eighths**: `9' 7⅜"`, not `115.344"`.
- Heights render as **measured up from the deck top**, the guide's zero:
  "40 inches above the deck", never "z 40".
- Horizontal positions render as **tape readings from a named physical mark**:
  "16 inches on centre, measured from the left end mark".
- Parts are named **cut-list name + nominal size + cut length**:
  `rafter · 2×6 · 9' 7⅜"`.

Why, in one line: the reader builds with a tape, and the building has no axis
system on it; split-attention research says the number belongs on the part,
where a coordinate would be noise.

## 5. Sourced principles behind the rules

The method is distilled from instruction-design standards and research; each
rule above traces back to this material. Verification levels from the
original research: FULL = source read in full, SNIPPET = excerpt only.

### 5.1 The governing standard — IEC/IEEE 82079-1:2019

"Preparation of information for use (instructions for use) of products"
explicitly covers products "ranging from a tin of paint to … buildings", so a
shed is squarely in scope ([ISO catalog 71620](https://www.iso.org/standard/71620.html)).
Clauses the guide leans on (clause content via free previews and
committee-adjacent secondary sources; the body text is paywalled):

- **5.3** seven information-quality principles: completeness, minimalism,
  correctness, conciseness, consistency, comprehensibility, accessibility.
- **7.12** instructions for assembly of self-assembly products.
- **8.3.3** leading criteria — tasks ordered "by the order in which tasks are
  performed" (the page chain follows build order); **8.3.4** step-by-step
  structure = preliminary information → instructional steps → completion
  information (the page template's three blocks).
- **9.10** legibility incl. minimum font sizes; **9.11.4** illustration with
  captions (the caption contract).
- The 2012 predecessor gives two rules quoted by number: **6.1.6** "one
  sentence, one command" and **6.3.4** "one illustration, one item of
  information" (one action per step; P6).

Adjacent standards: **ISO 20607:2019** (machinery handbooks; the 4-part
warning formula signal word + hazard + consequence + avoidance — the guide's
warning format); **ANSI Z535.6** (safety messages placed at the exact step);
**ISO 3864 + ISO 7010** (safety colours and signs; red circle+bar =
prohibition, the grammar of the error-state frames); **ISO/IEC Guide 37**
(never rely on one medium for a crucial safety message — P12). A Part 2
dedicated to self-assembly is in development (BSI project 9025-12059); its
scope statement is the closest official definition of this guide's reader: "a
non-skilled target audience assembling a product without help from a trainer
or supervisor".

### 5.2 IKEA — borrow the visual grammar, keep the text

IKEA's instruction designers ("communicators") work to "clarity and
continuity" and **test-assemble the product themselves first** to catch
mistakes that only bite many steps later
([Fast Company](https://www.fastcompany.com/3052604/how-ikea-designs-its-infamous-instruction-manuals), FULL).
Documented conventions: wordless steps with **text reserved for safety**
(verified on a real manual — the only extractable text is a tip-over WARNING);
fixed single viewpoint "mimicking that of the customer"; one action per step;
**crossed-out error frames** ([Frixione & Lombardi](https://link.springer.com/article/10.1007/s13164-014-0216-1));
finished-product "promise" page first (the start page's finished-shed figure).

IKEA's own preconditions for going wordless: fewer than ~100 parts, exactly
one correct assembly path, purely sequential steps. **This shed violates all
three** (293 modeled parts, weather/site judgement, tolerances) — hence text
stays, for safety and one-time operations.

### 5.3 LEGO — delta highlighting, fixed camera, symbols

From LEGO's own history and convention documentation: the **fixed viewpoint**
predates digital tools (step photos shot "exactly on the same spot as the
previous one"); **delta highlighting** — new parts in full colour, prior build
muted (P4); **step-inventory callouts**; an **official symbol set** (P9);
**1:1 templates** for length-ambiguous parts (the precedent for P10); and
error-tolerant step ordering — where error is possible, limit its consequences
to non-critical/aesthetic ([LEGO history](https://www.lego.com/en-us/history/articles/d-lego-building-instructions-through-time),
[BrickNerd](https://bricknerd.com/home/how-lego-instructions-have-changed-over-time-a-forest-of-discovery-10-17-22),
[BricksFanz](https://bricksfanz.com/a-guide-to-lego-instructions-symbols/),
[Brickset](https://brickset.com/article/110723/the-simplification-of-the-lego-building-experience-what-s-up-with-that), all FULL).

### 5.4 Comprehension research — the strongest sources

Two Stanford papers on flat-pack furniture assembly with adults, the closest
published analog to this shed:

- **Agrawala et al., "Designing effective step-by-step assembly instructions",
  ACM TOG (SIGGRAPH)** ([PDF](https://graphics.stanford.edu/papers/assembly_instructions/assembly.pdf), FULL):
  step-by-step beats single all-operations diagrams; one significant part (+
  its fasteners) per diagram; **visibility is "perhaps the strongest design
  principle"** — new part visible, prior context visible, future parts not
  occluded; density balance; reorient only at stable, physically realizable
  poses (build flat, then stand up — the walls workflow).
- **Heiser et al., AVI** ([PDF](https://graphics.stanford.edu/papers/assembly_instructions_study/assemblyuserstudy_hires.pdf), FULL):
  seven validated principles — one diagram per major step; explicit
  numbering/order; parts added in each step visible; **attachment mode
  visible**; action diagrams over structural diagrams; consistent arrow
  semiotics; **avoid changing viewpoints**. Instructions built on these cut
  assembly time ~35% and errors ~50% (n=30). Users **never read text
  explanations while holding the product** — words must be glance-able.
  Crucial caveat: LEGO-style structural diagrams suffice only *because every
  LEGO part attaches the same way*; a shed has nails, screws, hinges,
  birdsmouth seats, mitres — hence P5. In the same study the single
  exploded-view condition failed: participants couldn't see where parts
  connected.

Orientation and projection misreading (the P1/P2 evidence base): **Shepard &
Metzler** — mental-rotation cost scales with angle, so viewpoint changes are
real cognitive work; **Palmer, Rosch & Chase** and **Blanz, Tarr & Bülthoff**
— readers carry canonical preferred views (oblique-from-above beats pure
top/side/front); **Van Den Einde et al., ASEE** ([abstract](https://peer.asee.org/41636))
— novice orthographic-projection errors cluster in top views, alignment and
orientation. Design for the lower half of the spatial-ability distribution: in
the Heiser study, diagrams by low-spatial-ability authors produced 86%
ordering errors vs 12% for high. **Gap, stated plainly:** no published
experiment directly tests "reader treats a plan view as an elevation" — the
§2 mechanism is inferred from this body of work.

Figure–text coupling: **Mayer & Moreno** split-attention effect (the number
belongs on the part); **Moreno & Mayer** contiguity; **Paivio** dual coding;
**Levie & Lentz** — representational illustrations facilitate learning,
decorative ones do not.

One-off builds: **Menn et al., SEFI** ([PDF](https://www.sefi.be/wp-content/uploads/2017/09/54394-JP.-MENN.pdf), FULL)
adapts kit-style instructions to one-of-a-kind production and adds what kits
never need — escalation/troubleshooting pages, per-step tool/time/headcount,
checkpoints, tick-off checklists (the troubleshooting page and page furniture
come from here). **Söderberg et al., Chalmers** ([full text](https://publications.lib.chalmers.se/records/fulltext/202981/local_202981.pdf)):
with the original instructions, 67% of builds missed a part and 49% misplaced
a subassembly; many assemblers **stopped reading and used only the final
finished-product picture**. The IKEA effect (Norton et al.) supplies the
stakes: the emotional payoff requires successful completion — an unrecoverable
instruction error destroys it.

### 5.5 What does NOT transfer from mass-kit design

| Kit convention | Why it exists there | Verdict for this one-off shed |
|---|---|---|
| Fully wordless steps | One booklet, 25+ languages, translation cost | **No** — one reader, one language; text is free and needed for safety |
| Identical part-count callouts ("x2") | Factory-counted identical bags | **Partial** — callouts from the cut list, paired with a cut/spare note for wood waste |
| 1:1 scale of factory hardware | Identical stamped fittings | **Partial** — no hardware to match, but 1:1 *profiles* of birdsmouths/angles transfer (P10) |
| Pre-drilled hole patterns | CNC consistency | **No** — layout is dimensioned from named datums instead |
| No troubleshooting pages | The kit is deterministic | **Inverted** — the shed NEEDS escalation pages (warped stock, out-of-square box) |
| Bag-break pacing | Physical bags | **As analog** — end each page at a structurally stable, weather-safe stopping point |
| Illustration templates reused across products | Thousands of identical products | **No** — one shed; but reuse within the guide (four walls share a layout pattern) |

## 6. Worked example: the door-jamb finish build-up

Content (facts from the model): at a 36" door jamb the finish steps outward in
four ¾" layers — 1×8 lap siding on the wall face → 1×6 jamb casing on the
siding face → door planks on the casing face → 1×4 leaf frame outboard; 3"
proud of the wall face in total. Siding and casing stop at the clear opening;
the leaf laps each jamb casing 1½". Presented per spec, this becomes **two
coupled figures**, not one packed figure.

### Fig. A — elevation locator (declares the frame the section will be cut from)

```
 [ELEVATION · front wall door zone · viewed from the street · DOWN ↓]

   plate top ─────────────────────────────────────────────
                  │ siding │             │casing│
   frieze ════════╪════════╪═════════════╪══════╪═════════
                  │        ┌─ head casing ─┐     │
                  │        │ ┌───────────┐ │     │
                  │        │ │ door leaf │ │     │ ← leaf laps
                  │        │ │ (closed)  │ │     │   casing 1½"
                  │        │ └───────────┘ │     │
   ═══════════════╪═════CUT═══A════════A═══╪═════╪═════  40" above deck
   deck ──────────┴────────────────────────┴─────┘
   ▼ DOWN (gravity)          deck = height datum for the whole guide

   Cut line A–A is horizontal. Fig. B shows this cut, LOOKING DOWN.
```

Why this figure exists: it makes the section's frame self-evident before the
reader ever sees it (P2); it shows the layers in situ with neighbours (P4);
the deck line + gravity arrow make the vertical frame undeniably vertical.

### Fig. B — section A–A (the four ¾" steps, frame declared twice)

```
 [SECTION A–A · horizontal cut 40" above deck · looking DOWN from above]

                      OUTSIDE (yard)
   ┌─────────────────────────────────────────────────────┐
   │▓▓▓ 1×4 leaf frame · ¾" (outermost of the 4 layers)  │
   ├────────────────────────────────────┬────────────────┤
   │▓▓▓ door planks · ¾"                │ stile (edge    │
   ├──────────────────────┬─────────────┤ of the leaf)   │
   │▓▓▓ 1×6 jamb casing·¾"│             │                │
   ├──────────────┬───────┤    CLEAR    │                │
   │▓▓ 1×8 lap    │ 2×4   │    OPENING  │                │
   │   siding · ¾"│ wall  │     36"     │                │
   │              │framing│             │                │
   └──────────────┴───────┴─────────────┴────────────────┘
                      INSIDE (shed)

   ▓ = material cut by the A–A plane (section hatching)
   jack + king studs sit in the wall behind the casing — grey
   "already built" context, not part of this figure's message

   wall face ◄─ +¾" siding ◄─ +¾" casing ◄─ +¾" planks ◄─ +¾" frame
   ⇒ 3" proud of the wall face · siding & casing stop at the clear
     opening · the closed leaf laps each casing 1½"
```

Production notes: cut material hatched per section grammar (hatching is itself
an anti-ambiguity device — elevations don't hatch); leader-line labels with
cut-list names (P7); running dimension chain at the bottom; grey = already-built
framing (P4). Where four thin bands must be shown at page scale, draw them
exaggerated with a stated scale note — as the whole figure, not an inset
within a plan (P6). The model trace goes in a non-rendering comment, e.g.
`<!-- model trace: siding y -3.5...-4.25; casing -4.25...-5.0; planks -5.0...-5.75;
frame -5.75...-6.5; cut at 40" above deck -->`.

Why this beats the failed figure: (1) the frame is declared by the drawing
itself — locator cut line + hatching + "looking DOWN" badge + deck/gravity
anchor — so the default-to-vertical error is corrected before any text is read;
(2) coordinates stay traceable in source comments, invisible in rendering;
(3) two figures, one message each; (4) the neighbour context (jack/king studs,
opening, leaf) is present, so the layers read relative to the building rather
than as abstract blocks; (5) the takeaway dimension (3" proud) is a drawn
chain, not prose.
