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
- Verification run, 2026-08-13 (`~/.venvs/woodbike-shed/bin/python -m cad.verify`):
  `OK: 293 parts (117 framing, 176 finish), 36 framing cut-list names; dims/volumes/placements
  match audit data; seats/kicks/ends flush; finish layers seated; 0 unallowed interference
  (333 pairs swept).` The harness checks every part's dims, volume and placement against the
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

## Foundation drawings

The foundation is drawn, not modeled. The originals are the captain's gravel-pocket set
(read-only); the plan view used by the Stage 1 page is adapted from them for the 16′
footprint and the continuous skids (the old drawing's 8-ft sistered splice no longer
applies), and the pocket section detail is inlined unchanged. Block, paver, and stone
quantities come from those drawings, not from the model.

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
| fig-01-cross-section | SECTION, constant X at 92.5 (through doubled joist pair), viewed from +X | front wall y −3.5…0, z 0…123; back wall y 65…68.5, z 0…97.125; rafter heel y −4 seat z 123, back seat z 97.125 at y 65…68.5, tails y −27.5 / 80.5; fascia faces y −29 / 82; peak z 137.687; skids z −9.75…−6.25; foundation schematic |
| fig-16-rafter-seat-gap | SECTION at the back wall seat, viewed from +X | back DTP top z 97.125 at y 65…68.5; plumb kick at y 68.5 to z 95.8125; rafter bottom slope 0.375; error gap 1″ drawn, exaggerated |
| fig-16-floor-diagonals | PLAN, horizontal cut at skid top, looking down | skid lines y −3.5…0 and y 65…68.5, x −3.5…188.5; block centres x 2.5 / 62.5 / 122.5 / 182.5; error: front skid shifted +4″ in X, exaggerated |
| fig-16-rake-courses | ELEVATION, left wall face x −3.5, viewed from −X | siding 7″ exposure from skirt top z 0.5; rake cut line = rafter bottom + 1″ (z 96.8 back → 123.8 front); skirt z −6.75…0.5; error: top course 2″ past rake, exaggerated |

Whole-shed anchors used across pages: footprint x −3.5…188.5 × y −3.5…68.5; front DTP top
z 123; back/left/right DTP tops z 97.125; roof slope 24.375 rise over 65 run (4.5:12);
rafter layout 15⅞″ o.c. at x −2.75…187.75.

## Before you move on

- [ ] `~/.venvs/woodbike-shed/bin/python -m cad.verify` runs green at the commit this page names, if you are checking numbers against the model.
- [ ] A figure's source comment (`model trace`) agrees with its row in the table above, checked with a grep of the page source.
