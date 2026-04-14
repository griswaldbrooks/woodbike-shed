# Outstanding issues

Open items for the bike shed BOM / cut list before submitting quotes.

## Stock availability

- **14' 2x4 stock**: The optimizer selected 25 × 14' 2x4 boards. Not every
  yard carries 14' — some only stock 8/10/12/16. Confirm with your target
  yard. If unavailable, re-run `scripts/build_cut_list.py` with 14' removed
  from `STOCK_LENGTHS["2x4"]` to fall back to 12' or 16'.

- **20' 2x6 stock (fascia)**: Two 20-foot 2x6 KD boards are needed for the
  roof fascia (each 216" = 18'). This is a special-order item at most retail
  yards. Alternatives:
  - Two 10' pieces per fascia with a scarf joint at midspan
  - Finger-jointed primed 20' boards (if painting)
  - Ask the yard if they stock 20' #2 SPF or Doug fir

## 2x4 8' boards — consider longer stock

The optimizer currently assigns 20 × 8' 2x4 boards, mostly for cuts in the
93"–96" range (studs, plates). These cuts leave almost zero scrap — fine for
material, but a practical concern:

- A 93" stud cut from an 8' (96") board leaves only 3" of waste, meaning
  zero tolerance for a warped/damaged end or a re-cut.
- Depending on the yard's per-foot price curve, 10' or 12' stock might not
  cost much more per board but would give you flexibility and scrap for
  shimming / blocking.

**Action:** Check the yard's price per linear foot for 2x4 at 8' vs 10' vs
12'. If the per-foot price is comparable, switch some or all 8' boards to 10'
or 12' for margin. Update `STOCK_LENGTHS["2x4"]` to exclude 8' and re-run to
see the result.

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
- Use 93" as modeled (cut from 8' stock) — no issue
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

## Onshape model cleanup

- **4 unnamed parts** inside composite skids: the physical 96" 4x4 boards
  that make up the composite skid assemblies have no part name in Onshape.
  The cut list labels them "skid" based on context, but they should be
  renamed in the Part Studio for traceability.
- **Composite part 3** is still default-named and excluded from the cut list.
  Confirm it's not needed.
- **"inner volume"** is excluded from the cut list. Confirm it's a reference
  body only.

## Rake studs annotation

Left and right rake wall studs are annotated "(different heights)" in the
model. Each is a unique length (22.40", 16.49", 10.59", 4.68"). The cut list
treats each as a distinct line item. These are short enough to cut from
scrap / off-cuts if managed on-site.
