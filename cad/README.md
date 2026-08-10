# cad/ — bike shed model-as-code

The Onshape model re-derived as code (build123d), per the scout report
`data/woodbike-shed-cadlib-scout/report.md`. Geometry flows one way out:
per-part STEP (exact record, occasional manual Onshape import) and one named
GLB for Blender renders. **No Onshape API calls anywhere in this package** —
the repo's audit files are the only model source.

## Stack (pinned in ../requirements.txt)

- Python 3.12, `build123d==0.11.1` (OCCT via cadquery-ocp-novtk 7.9.3), `trimesh`
- Setup: `uv venv --python 3.12 .venv && uv pip install -r requirements.txt`

## Commands (from repo root)

| Command | Effect |
|---|---|
| `.venv/bin/python -m cad.build` | Rebuild all parts, write `step/*.step` + `blender/scene.glb` |
| `.venv/bin/python -m cad.verify` | Assertion harness — **run after every change** |

## Sources of truth

- `scripts/oriented_dims.json` — part names (== CUT_LIST.md labels) + edge dims
- `scripts/bboxes.json` — world bounding boxes (placement)
- `CUT_LIST.md` / `OUTSTANDING_ISSUES.md` — cross-checks and open items
- Roof pitch is *derived from the plate solids* (`cad.common.roof_ref`:
  front double top plate bottom at the front wall inner face -> back double
  top plate top at the back wall inner face), sanity-checked against the
  documented 24.375/65 slope (~20.56°). The audit data reflects the
  2026-08-10 restud to 92-5/8" pre-cut studs (`scripts/restud_92_5_8.py` —
  full derivation record); the pre-restud slope was 24/65 (~20.26°, see
  MANUAL_COMPLETION.md). Wall-height edits propagate: seats, kicks, mitres
  and the pitch all re-derive from the plates.

## Layout

One module per shed section; `cad/common.py` loads the audit data and places
parts. Axis-aligned parts are AABB boxes (`place_box`); the roof/rake
members (rafters, rake boards, rake plates, rake studs) are exact YZ-profile
prisms (`prism_yz`, `roof_ref`) carrying the audited birdsmouth/seat/kick/
mitre/end cuts, anchored on their own world coordinates (never re-centered
on an AABB):

`skids.py` `floor.py` `walls_front.py` `walls_back.py` `walls_side.py`
`walls_rake.py` `roof.py` → orchestrated by `build.py`, checked by `verify.py`.

Finish lumber (captain 2026-08-10: modeled for real, SEPARATE order list) is
`siding.py` (1x8 lap courses, rabbet-nested, rake-cut tops), `trim.py`
(skirt/corners/frieze/casings), `doors.py` (board-and-batten leaves over the
framed openings) → `build.py build_finish()`, checked by the same
`verify.py` run (volumes, layer planes, envelope, zero interference against
the framing too). Their heights derive from `common.finish_layout` (audit
bboxes + roof_ref); only product dims are constants. Labels use a `finish `
prefix so `scripts/build_cut_list.section_for` files them under the Finish
sections and `scripts/build_finish_cut_list.py` orders them separately.

Naming scheme: every part's `.label` matches CUT_LIST.md exactly. STEP
filenames and glTF node names are `NNN <label>` (instance number prefix for
uniqueness — group names repeat, e.g. 14 × "back wall studs").

## build123d trap rules (learned empirically — do not break)

1. **Location tuple form only**: `Location((x,y,z), (rx,ry,rz))`.
   `Location(Pos(...), Rot(...))` constructs without error but **silently
   drops the rotation** — parts build in the wrong pose. All placement in
   `common.py` uses the tuple form; keep it that way.
2. **`export_step` takes ONE shape** — pass parts one at a time, never a
   list (`'list' object has no attribute 'wrapped'`). Also: build123d
   `Compound` drops child labels, so a single-file named STEP assembly is
   not available; per-part files are the workable path.
3. build123d `export_gltf` writes JSON glTF even for `.glb` unless
   `binary=True` — this repo exports meshes via trimesh instead (always
   binary GLB, names verified in Blender 4.5 LTS: one selectable object per
   part).
4. **build123d builds in mm**: `prism_yz` takes inch profiles and scales
   them at the boundary. Feeding raw inch points to `Polygon` builds a part
   25.4x too small without any error.

## Pending captain decisions (TODO seams, do not decide unilaterally)

(none open)

Resolved seams (kept for the record):
- **Doors/siding/trim** — implemented 2026-08-10 as real parts
  (`siding.py`/`trim.py`/`doors.py`) on a separate order list
  (`order_list_finish.csv`), per the captain's decision; hardware stays line
  items only.
- **Birdsmouth/trim cuts in code** — implemented 2026-08-10
  (`roof.py`/`walls_rake.py` prisms, `verify.py` seating gate). The old
  rectangular-stock approximation silently interpenetrated both double top
  plates by up to 1.5"; diagnosis record: firstmate report
  `woodbike-shed-birdsmouth-scout/report.md`.
- **Rake-plate end/nose cuts** — implemented with the plate prisms.
- **Skid composites** — superseded by the captain's 2026-08-10 skid
  redesign (two continuous 16' 4x4 lines; OUTSTANDING_ISSUES.md "Skid
  redesign").
