# Outstanding issues

Open items for the bike shed BOM / cut list before submitting quotes.
Regenerated 2026-08-07 against the completed model (120 parts; rake walls,
rafters and roof trim finished, all parts named).

## Stock availability

- **16' 2x4 stock**: The optimizer selects 32 × 16' 2x4 KD boards (five 192"
  plates + one 185" plate force 16' stock; the long front-wall studs pair
  best with plates at that length). Not every yard stocks 16' 2x4 — confirm
  with your target yard. If unavailable, re-run `scripts/build_cut_list.py`
  with 192 removed from `STOCK_LENGTHS["2x4"]` to see the 14'/12' fallback.

- **20' 2x6 stock (fascia)**: The two 216" (18') front/back fascia need
  20-foot 2x6 KD boards — a special-order item at most retail yards.
  Alternatives:
  - Two 10' pieces per fascia with a scarf joint at midspan
  - Finger-jointed primed 20' boards (if painting)
  - Ask the yard if they stock 20' #2 SPF or Doug fir

## Waste / overage factor

The cut list reflects the model dimensions exactly (0% overage). Standard
practice is 10% extra for framing jobs to cover mistakes, damaged boards, and
on-site scrap. Decide whether to:
- Bake 10% into the quote quantities before sending
- Or order exact and plan a follow-up run for shortages

## Stud pre-cuts

Back wall, left wall, and right wall studs are all 93". Standard pre-cut
studs (sold as "92-⅝" studs" at big-box stores) are 92.625". The model's
93" studs are 3/8" longer, which matters. Options:
- Use 93" as modeled (cut from stock) — no issue
- Switch to 92-⅝" pre-cut studs — cheaper and saves saw time, but requires
  adjusting the wall height in the Onshape model by 3/8"

## Treatment & species

Currently tagged:
- **PT (pressure-treated, ground-contact)**: all 2x6 floor system (rim
  joists + floor joists) and all 4x4 skids/sisters
- **KD (kiln-dried, framing grade)**: all wall and roof lumber
- **OSB**: 3/4" structural, subfloor-rated

Species/grade is not yet specified. Common choices for the PNW:
- KD framing: SPF #2, Hem-fir #2, or Doug fir #2
- PT ground contact: Hem-fir or SYP with UC4A rating

Confirm species preference with the yard and update `order_list.csv`
accordingly before quoting.

## Rafter bearing vs front-wall double top plate — RESOLVED

The rafters' bearing line (captain's `Rafter Right` sketch) sits at z=121.5"
on the front wall while the double top plate tops out at z=123". Fixed with
**birdsmouths** on every rafter: front seat cut flat at z=123" over the
plate width (heel at y=−4.06"), and a matching back seat at z=97.5" over the
back wall plate (plumb kick at y=68.5") where the tails dipped below the
plate top. Rafters now bear flush on both double top plates; verified by
`scripts/audit_overlaps.py` (zero lumber-on-lumber overlap).

## Known intentional overlaps (left as modeled)

- Opening-A jacks (84") and one king stud (120") run from z=0 through the
  front bottom plate (7.9 in³ each) — the captain's modeling quirk noted in
  the scout report, not corrected.
- The `inner volume` reference envelope pre-dates the roof; the rafters
  pass through its upper zone. Reference body only — excluded from the cut
  list, no action.

## Rake studs

Left and right rake-wall studs are now real parts, one unique length each:
22.40", 16.68", 10.77", 4.86" (re-derived from the live 24/65 slope; the
April 22.40/16.49/10.59/4.68 lengths are superseded). Short enough to cut
from scrap / off-cuts if managed on-site.

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
