# Outstanding issues

Open items for the bike shed BOM / cut list before submitting quotes.
Regenerated 2026-08-07 against the completed model (120 parts; rake walls,
rafters and roof trim finished, all parts named). 2026-08-10: captain's
ordering decisions applied locally (this branch); the Onshape model still
carries the pre-decision geometry (zero API calls).

## Stock availability — RESOLVED (2026-08-10, Hingham Lumber)

- **16' 2x4 stock**: Hingham Lumber stocks it — KEEP. The optimizer selects
  32 × 16' 2x4 KD boards (five 192" plates + one 185" plate force 16'
  stock). If a future yard lacks it, re-run `scripts/build_cut_list.py`
  with 192 removed from `STOCK_LENGTHS["2x4"]` to see the 14'/12' fallback.

- **20' 2x6 stock (fascia)**: Hingham Lumber stocks true 20' 2x6 — ORDER
  TRUE 20'. The two 216" (18') front/back fascia take one 20' board each.

## Waste / overage factor — RESOLVED (2026-08-10)

ORDER EXACT quantities (0% overage); the captain plans a follow-up order
for shortages. order_list.csv carries no waste factor by design.

## Stud pre-cuts — RESOLVED (2026-08-10)

SWITCHED to standard 92-5/8" pre-cut studs for the back, left, and right
walls; wall height dropped 3/8" (97.5" -> 97-1/8"). Applied locally by
`scripts/restud_92_5_8.py`, which re-derives every dependent value from the
constraint chain (roof plane pivots about the unchanged front wall; rake
studs, rafters, fascia and cripples follow — see the script docstring and
the 2026-08-10 commit for before/after dims). The Onshape model still has
the 93" studs; sync it (or not) is a future captain call.

## Skid redesign — continuous 16' lines (2026-08-10 captain's decision)

The sistered skid arrangement is DROPPED: each skid line is now ONE
continuous 16' (192") 4x4 (two total, full shed length x = -3.5..188.5), on
the audited composite-skid lines under the front/back wall bearing lines
(y -3.5..0 and 77..80.5, z -9.75..-6.25, since the 7 ft depth). Hingham
stocks 16' 4x4; PT ground-contact tagging unchanged. **Deliberate divergence
from Onshape**, whose model keeps the sistered composite skids (4x 96"
boards + 2x 48" sisters); the local model, cut list and order list carry the
redesign.

**Foundation, 2026-08-24 — piers/pedestals DROPPED.** This supersedes the
StrataRise pedestal revision. The two continuous skids bear DIRECTLY on one
compacted ¾" crushed-stone gravel pad screeded level across the whole
16′ × 7′ footprint — no pedestals, no paver base pads, no shims. Model, cut
list, and the guide's Stage 1 (gravel pad and skids) all carry it; the
pedestal order lines are removed. The pad footprint/spec is stated on the
P04 foundation page because the landscaper excavates it before any lumber
arrives.

## Treatment & species

Currently tagged:
- **PT (pressure-treated, ground-contact)**: all 2x6 floor system (rim
  joists + floor joists) and all 4x4 skids
- **KD (kiln-dried, framing grade)**: all wall and roof lumber
- **OSB**: 3/4" structural, subfloor-rated

Species decisions:
- KD framing: **SPF #2** — decided; recorded in order_list.csv notes.
- PT ground contact: **CLOSED — captain 2026-08-24, permanently.** There is no
  choice: order whatever the yard stocks (ground-contact rated). This question
  is never to be re-opened.

## Doors / siding / trim — separate order list — RESOLVED (2026-08-10)

Captain's call: model doors/siding/trim for real, but order them on a
COMPLETELY SEPARATE order list — never mixed into this framing lumber list.
Implemented on branch fm/woodbike-shed-siding-model: `cad/siding.py`,
`cad/trim.py`, `cad/doors.py` (real dimensioned parts in scene.glb + per-part
STEP + view.py sections), ordered via `order_list_finish.csv` and the FINISH
sections of CUT_LIST.md (`scripts/build_finish_cut_list.py`). Hardware
(strap hinges, latches) stays line items only.

## Rafter bearing vs front-wall double top plate — RESOLVED

The rafters' bearing line (captain's `Rafter Right` sketch) sits at z=121.5"
on the front wall while the double top plate tops out at z=123". Fixed with
**birdsmouths** on every rafter: front seat cut flat at z=123" over the
plate width (heel at y=−4.06"), and a matching back seat at z=97.5" over the
back wall plate (plumb kick at y=68.5") where the tails dipped below the
plate top. Rafters now bear flush on both double top plates; verified by
`scripts/audit_overlaps.py` (zero lumber-on-lumber overlap). The local
build123d model carries the same birdsmouths as exact profile prisms
(2026-08-10; seats/kicks derived from the plate solids, re-derived for the
92-5/8 restud: front seat z=123" heel y=-4.0", back seat z=97.125" plumb
kick y=68.5"), guarded by the `cad.verify` seating + zero-interference
checks.

## Known intentional overlaps (left as modeled)

- The `inner volume` reference envelope pre-dates the roof; the rafters
  pass through its upper zone. Reference body only — excluded from the cut
  list, no action.
- (2026-08-23: the as-designed opening-A jacks and tall king that ran
  from z=0 through the front bottom plate were retired by the door-plan
  reframe — every new jack/king sits on the plate, and `cad.verify`'s
  ALLOWED_OVERLAPS exemption no longer matches anything.)

## Door plan — adopted 3-door plan (captain 2026-08-23, left MAIN door added 2026-08-24)

Verdict (durable copies in firstmate data/shed-door-plan-model/
captain-decision-2026-08-23.md and data/shed-guide-depth-pass/
captain-decision-2026-08-24.md): adopt the free-doors study's WINNER
(firstmate data/shed-jenga-arrange/report.md) MODIFIED — the 3 ft walk-in
is REMOVED — and then ADD the LEFT rake-wall 64 in double as the MAIN
(primary pedestrian) door. Model + audit JSON updated 2026-08-23 by
`scripts/depth7ft_2door.py` (7 ft depth + barn + right brewery) and
2026-08-24 by `scripts/left_main_door.py` (the left MAIN door, an exact
mirror of the right brewery double).

- **Barn door 8 ft (96 in)**, front wall west end, clear 0-96, head 84 —
  wheeled roll-out (bikes + blower) and slab carry-in on edge. The west
  jamb IS the corner: the header bears on the corner king + a corner jack
  in the corner block (the built-up header-bearing corner post; flagged not
  engineered in the study). East of the opening the front wall is solid
  studs at 16" oc.
- **MAIN entry double 64 in**, LEFT rake wall, clear 6.5-70.5, head 84,
  6.5 in end studs. The shed's everyday pedestrian door — closest to the
  garage/access. Exact mirror of the right brewery double's framing
  (jacks, header plies + cap, cripples, mitered header cripples).
- **Brewery double 64 in**, RIGHT rake wall, clear 6.5-70.5, head 84,
  6.5 in end studs (the study's flagged minimum).
- **Walk-in / slab-feed door REMOVED.**
- **7 ft shell**: back wall out to y 77..80.5, plate tops at 92-5/8 (the
  restud slope 24.375/65 is exactly the 7 ft slope 28.875/77). Where the
  roof drops below the flat plate stack, the gable ends follow it: the
  flat DTP runs to y 60.73 and the top plate to 64.73, mitered studs carry
  the rake plate to the back corner, and side DTP corner blocks carry the
  corner rafters' back seats (all derived in the script's docstring).

**Door roles** (recorded everywhere in the guide): LEFT double = MAIN
entry; front 8 ft barn = wheeled roll-out + slab carry; RIGHT double =
brewery service. Recorded in the fit check:

- `scripts/fit_study_free_doors.py --arrange winner2` (the free-doors
  study adapted for the adopted plan; the original arrangements still run
  unchanged) — full record in `scripts/fit_summary_winner2.txt`: every
  named check PASS, "everything fits with access kept":
  - pedestrian entry through the LEFT MAIN door (64 in vs the 36 in
    minimum), entry landing + maneuver floor clear to 48 in;
  - slabs carried on edge through the barn door (96 in ≥ 28 in slab +
    18 in carrier), aisle 49 in ≥ 46, rack feed face 23.75 in at the east
    end of the run (≥ 21 in as-designed precedent);
  - unchanged from the winner: bikes + blower straight-roll under the run,
    brewery service from outside the 64 in door (6.5 in end studs), hood +
    duct + panel checks;
  - left-door sanity suite (end studs, outswing leaves stay exterior, entry
    landing clear) matches the checks the winner-render scout validated
    (firstmate data/shed-blender-winner/report.md).

## Plywood lean-to relocation — FOLLOW-UP (2026-08-24)

The plywood lean-to run planned against the LEFT wall must RELOCATE: the
left wall now carries the MAIN entry double, so the lean-to cannot stay
where it was. The family has accepted the relocation. Choosing the new
spot is NOT part of the door/depth task — open it as its own decision when
the interior arrangement is next revisited.

## Rake studs

Left and right rake-wall studs are now real parts, one unique length each:
22.77", 16.96", 10.96", 4.96" (re-derived 2026-08-10 from the 24.375/65
restud slope; the 93-stud 22.40/16.68/10.77/4.86 lengths and the April
22.40/16.49/10.59/4.68 lengths are superseded). Short enough to cut from
scrap / off-cuts if managed on-site.

## Onshape model cleanup

- All 40 formerly default-named parts are renamed (front wall, back-wall
  studs, rake studs, rafters). Zero `Part NN` remain.
- The 4 unnamed solid **bodies** inside the two multi-body `skid` parts
  remain unnamed (they are sub-bodies, not parts — nothing to rename).
- `"inner volume"` remains excluded from the cut list; confirmed reference
  only (interior clearance envelope).
- The captain's 20 broken tail features (rake-wall/rafter chains) were
  **deleted 2026-08-08** with his go-ahead; the feature tree is fully green
  (119 features, zero errors). Diagnosis record: `MANUAL_COMPLETION.md`.
