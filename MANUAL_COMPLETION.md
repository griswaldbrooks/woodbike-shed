# Manual completion guide — the captain's broken tail features

Status as of 2026-08-07 (restore version `aa73830b88f34f965190a7c6`
"pre-fleet-completion 2026-08-05" taken before any change).

The rake-wall and rafter geometry the mid-refactor was building **now exists
in the model**, rebuilt additively from current geometry (features added by
`scripts/build_members.py`, all named, all verified):

| New part group | Qty | Dims (oriented) |
|---|---:|---|
| right rake wall studs | 4 | 2x4, heights 22.40 / 16.68 / 10.77 / 4.86" |
| left rake wall studs | 4 | same heights (mirrored wall) |
| left rake wall top plate | 1 | 2x4 × 69.29", sloped 24/65, mirror of right |
| rafter | 13 | 2x6 × 115.13", 15.875" o.c., x = -2.75…187.75, birdsmouthed front (seat z=123) and back (seat z=97.5) |
| front / back fascia | 2 | 2x6 × 216" (12" past each side wall), tops flush with rafter tails |
| left / right rake board | 2 | 2x6 × 115.13", along the slope at the roof overhang edges (flush with the fascia ends), butting the fascia inner faces |

The captain's own tail features (indices ~98–119) were left untouched. They
remain in **ERROR**, generate no geometry, and conflict with the new parts
only if re-activated. This guide explains why they broke and how to
reconcile them.

## Why the tail features fail

Decoded query analysis (`scripts/decode_queries.py`): the chains dangle on
entities that were **deleted in the May 13 rework** and have no equivalent
current entity recoverable via API:

- Deleted sketch/feature `FrZYFpgdFKjya90_36` (a fit-spline sketch, probably
  the pre-rework rafter/rake source sketch) is referenced by Frame 64,
  Split 3, the `Rafter Right` sketch plane, Frame 67, Delete face 1 and
  Linear pattern 12.
- The `left rake wall` sketch (FiKQ888uBey2hqI_78) plane references an
  imprint of the front-wall sketch (`6EjE1s8sV2Tc "bottom"`) through a
  derived-edge chain that died when the front wall was re-framed — the
  sketch cannot regenerate, so Frame 65/66 paths into it dangle.
- The `Rafter Right` sketch plane dangles the same way (back-wall imprint
  chain through Frame 11).
- Transform 5 and Frames 68/69 reference four **deleted mate connectors**
  (`FnIecGR1qx20dBs`, `FRVwmcycLIvehP7`, `FpFOhvn0h3OXIgO`,
  `FG26LejFgzsuatY`) — the fascia/rake-board alignment rig is unrecoverable.
- The right/left chains' Split/Delete features reference imprints on parts
  that were rebuilt with new ids; repointing ~45 compressed derived
  references blind was judged unsafe, so nothing was edited.

## What each broken chain was building (best reconstruction)

**Right rake wall** (sketch OK + Frame 63 OK → the existing 69.29" rake top
plate; Frame 64 + Linear pattern 10 (4 × 16") + Split 3 + Delete part 2 →
the rake studs): superseded by the new `right rake wall studs` (4 parts).

**Left rake wall** (sketch ERROR → whole chain dead): superseded by the new
`left rake wall top plate` + `left rake wall studs`.

**Rafter Right** (sketch plane ERROR → Frame 67 rafter + Linear pattern 12
(12 instances × 16") + Delete face 1 + Transform 5 + Frames 68–71 + Move
face 13): Frame 67 + pattern 12 → the rafters, superseded by the new 13
`rafter` parts. Frames 68–71 (four frames on mate-connector angle
references) + Transform 5 + the 12" Move face 13 were the **roof trim
package** — the April fascia/rake-board construction with the roof extended
12" past each side wall. That intent is now superseded by the new
`front/back fascia` (2x6 × 216" = 192" shed + 2 × 12") and
`left/right rake board` (2x6 × 118.32", running end-to-end flush with the
fascia outer faces) parts.

## Recommended cleanup in the Onshape UI

1. Suppress or delete the 20 tail features in ERROR (Frame 64 … Frame 71 and
   their sketches/patterns/splits/deletes/transforms — everything from
   `right rake wall` sketch's Frame 64 onward, plus the `left rake wall`
   and `Rafter Right` sketches). The new parts already deliver their
   rake/rafter output; keeping them only leaves red features.
2. If you want the captain's original construction instead of the rebuild:
   restore version `aa73830b88f34f965190a7c6`, then in the UI re-point
   - the `left rake wall` sketch plane onto the left wall plane (same plane
     as `left wall sketch`),
   - Frame 64's second selection and Split 3's targets onto current
     front-wall geometry,
   - the `Rafter Right` sketch plane onto a plane normal to X (e.g. the
     shed mid plane), and rebuild the four fascia mate connectors.
3. The fascia and rake boards are modeled now (see table above); nothing
   else is missing from the roof framing.

## Geometry reference used for the rebuild (all in inches, Z up)

- Roof slope: **24/65** (rise 24" over the 65" front-to-back wall bearing
  spacing; matches the right rake plate's top edge exactly).
- Right rake plate top edge: (y=65, z=97.5) → (y=0, z=121.5); underside
  line: z = 97.5 + (24/65)·(60.669 − y).
- Rake stud centers (both walls, on the wall's 16" grid): y = 0.75, 16.25,
  32.25, 48.25; each bears on the double top plate (z=97.5) and is mitered
  to the rake-plate underside.
- Rafter bottom edge (the captain's `Rafter Right` line, decoded): from
  (y=−27.5, z=131.654) to (y=80.5, z=91.777) = 24" front / 12" back overhang
  from the wall outer faces, bearing on the front plate at (y=0, z=121.5)
  and back plate at (y=65, z=97.5); 2x6 (5.5" depth ⊥ slope), plumb end
  cuts, length 115.13". Birdsmouths: front seat flat at z=123 (heel at
  y=−4.0625, plumb kick at the front wall inner face y=0); back seat flat
  at z=97.5 over y=65…68.5 with plumb kick at the back outer face.
- Rafter X positions: 13 uniformly spaced centers −2.75 … 187.75 (the live
  stud-grid endpoints), spacing 15.875".
- Fascia: 2x6, x = −15.5 … 200.5 (216", 12" past each side wall), front at
  y = −29 … −27.5 with top flush at the front rafter-tail top (z = 137.52),
  back at y = 80.5 … 82 flush at z = 97.64. Rake boards: full rafter
  profile (115.13"), 1.5" thick, flush with the fascia ends at the roof
  overhang edges (x = −15.5 … −14 and 199 … 200.5), butting the fascia
  inner faces (y = −27.5 … 80.5) so the fascia stays unbroken.
- Rake-plate noses (0.27" slivers that poked into the front wall plates):
  left plate trimmed in its sketch (front end now a vertical face at y=0);
  right (captain's) plate trimmed by the scoped REMOVE feature
  "right rake plate nose trim" (wedge under the plate-top line, boolean
  scope limited to the plate body).
