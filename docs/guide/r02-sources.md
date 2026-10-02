---
page: R02
title: Reference — sources, verification, traceability
prev: r01-cut-list.md
---

# Reference — sources, verification, traceability

> **Goal:** where every number in this guide comes from, what the model's own checks report, and the figure-to-model-coordinate map the build pages deliberately leave out.

This page is traceability, not build reading. The visible pages speak in tape readings and
feet-inches-eighths; the model coordinates live here and in non-rendering source comments,
kept for `cad.verify` lineage.

## Model authority

- Geometry and quantities come from the repo `woodbike-shed`: `cad/*.py` (build123d model —
  framing, siding, trim, doors; shared layout math in `cad/common.py`) plus the generated
  `CUT_LIST.md`, `order_list.csv`, `order_list_finish.csv`.
- The model and lists were last changed at commit
  `c86e75d991126c33e2daa4d0589183db155378b2` ("Finish lumber as real parts: siding/trim/doors
  + separate order list", 2026-08-10). These pages were written 2026-08-13 from a worktree at
  `c961c86` and every overview/order number was re-checked against the model before writing.
- Verification run, 2026-08-23, after the 7 ft depth + 2-door plan rework
  (`~/.venvs/woodbike-shed/bin/python -m cad.verify`):
  `OK: 278 parts (118 framing, 160 finish), 36 framing cut-list names; dims/volumes/placements
  match audit data; seats/kicks/ends flush; finish layers seated; 0 unallowed interference
  (342 pairs swept).` The harness checks every part's dims, volume and placement against the
  audit data, gates the rafter birdsmouth seat/kick faces, the rake-stud mitres, tails flush
  with fascia, and the finish layer planes, and runs the full pairwise interference sweep.
- Viewing the model: `view.py` (OCP CAD Viewer, part tree mirrors the cut list);
  `blender/build_scene.py` renders the scene (`--skin` for the dressed variant).

## Deliberate divergence from the Onshape model

The Onshape document is a retired record copy. It still carries the pre-decision geometry —
93″ studs, sistered skids, no birdsmouths, no finish — and must not be synced from. Since
2026-08-10 the local audit JSON and `cad/` run ahead of it: the 92-5/8″ pre-cut restud and
the two continuous 16′ 4×4 skids were applied locally only, and the roof was re-derived
about the unchanged front wall (pitch 24/65 → 24.375/65). Every number in this guide follows
the local model, not Onshape.

## Foundation — the pier-less gravel pad (captain's decision, 2026-08-24)

The foundation is drawn, not modeled. On 2026-08-24 the captain dropped the piers and
pedestals entirely, superseding the StrataRise adjustable-pedestal design (which itself
superseded the eight-Tuff-Block design retired 2026-08-14): the two continuous 16′ PT 4×4
skids now bear DIRECTLY on a compacted gravel pad — no concrete, no pedestals, no paver
pads, no fasteners. The building above holds the skids; there is no hardware in this
foundation, and no shims — the screeded gravel is the shim.

Pad spec, as built into [P04](04-blocks-and-skids.md): excavate the full 16′ × 7′ footprint
to firm subsoil (probe first; depth varies, typically 8–12″ — dig to firm soil, never a
fixed depth), line with landscape fabric lapped up the sides, fill with ¾″ angular crushed
stone in 3″ tamped lifts (about 3–4 yd³), screed the top flat and level at or slightly
above finished grade, and crown the surrounding grade away from the shed. The practice
derives from the captain's original gravel-pocket drawings (read-only), applied to the
whole footprint instead of eight pockets. Deck top lands 9¾″ above the pad top (skid 3½″ +
2×6 joist 5½″ + ¾″ OSB). Durable decision copy:
`/media/griswald/wd-black-2tb/personal/firstmate/data/shed-guide-depth-pass/captain-decision-2026-08-24.md`.

## Known intentional quirks

- The two 84″ opening-A jack studs and the one 120″ front king stud run from the deck
  through the front bottom plate — a documented modeling quirk, exempt from the
  interference sweep. P01 carries the field handling.
- The inner volume reference envelope pre-dates the roof and is excluded from all lists.
- Not modeled (builder scope): wall sheathing/WRB, roof sheathing/underlayment/roofing,
  fasteners, paint/caulk for the primed finish stock, door stops/weatherstrip.

## Coordinate traceability table

Figure-to-model-coordinate map. The guide's datum: deck top = z 0; front (street) wall at
low Y; X along the 16′ length; Z up. Each figure page also carries its trace as a
non-rendering HTML comment; stage pages owned by other workers carry their own.

| Figure | View | Model anchors |
|---|---|---|
| fig-01-cross-section | SECTION, constant X at 92.5 (through doubled joist pair), viewed from +X | front wall y −3.5…0, z 0…123; back wall y 77…80.5, z 0…92.625; rafter heel y −4 seat z 123, back seat z 92.625 at y 77…80.5, tails y −15.5 / 92.5; fascia faces y −17 / 94; peak z 133.187; skids z −9.75…−6.25; gravel pad schematic (pier-less) |
| fig-16-rafter-seat-gap | SECTION at the back wall seat, viewed from +X | back DTP top z 92.625 at y 77…80.5; plumb kick at y 80.5 to z 91.3125; rafter bottom slope 0.375; error gap 1″ drawn, exaggerated |
| fig-16-floor-diagonals | PLAN, horizontal cut at skid top, looking down | skid lines y −3.5…0 and y 77…80.5, x −3.5…188.5; error: front skid shifted +4″ in X, exaggerated |
| fig-16-rake-courses | ELEVATION, left wall face x −3.5, viewed from −X | siding 7″ exposure from skirt top z 0.5; rake cut line = rafter bottom + 1″ (z 96.8 back → 123.8 front); skirt z −6.75…0.5; error: top course 2″ past rake, exaggerated |

Whole-shed anchors used across pages: footprint x −3.5…188.5 × y −3.5…80.5; front DTP top
z 123; back DTP top z 92.625 (side walls' flat DTP tops z 97.125 run until the roof drops
below them, then the gable follows the roof); roof slope 24.375 rise over 65 run (4.5:12);
rafter layout 15⅞″ o.c. at x −2.75…187.75.

## Before you move on

- [ ] `~/.venvs/woodbike-shed/bin/python -m cad.verify` runs green at the commit this page names, if you are checking numbers against the model.
- [ ] A figure's source comment (`model trace`) agrees with its row in the table above, checked with a grep of the page source.
