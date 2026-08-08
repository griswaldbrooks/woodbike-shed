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
- Roof pitch is *solved from the rafter audit data* (`cad.common.solve_pitch`),
  cross-checked against the documented 24/65 slope (~20.26°) recorded in
  MANUAL_COMPLETION.md on branch `fm/woodbike-shed-finish-rework`.

## Layout

One module per shed section; `cad/common.py` loads the audit data and places
parts (center = AABB center; tilted parts rotate about X by the solved pitch):

`skids.py` `floor.py` `walls_front.py` `walls_back.py` `walls_side.py`
`walls_rake.py` `roof.py` → orchestrated by `build.py`, checked by `verify.py`.

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

## Pending captain decisions (TODO seams, do not decide unilaterally)

- **Birdsmouth/trim cuts in code** — `roof.py`: the upstream model's rafter
  seat cuts and end trims are RESOLVED in OUTSTANDING_ISSUES.md, but the cut
  list describes full 2x6 stock, so rafters are rectangular here (AABB
  deltas carried as documented verify tolerances). Implementing the cuts in
  code is a follow-up only if render fidelity needs it.
- **Doors/siding/trim** — `walls_front.py` (and right wall opening): framing
  only, as cut-listed.
- **Skid composites** — `skids.py`: physical boards modeled; Onshape
  composite bodies / "Composite part 3" remain as documented in
  OUTSTANDING_ISSUES.md.
- **Rake-plate end/nose cuts** — `walls_rake.py`: rectangular stock; the
  audit AABB shows the real part's extents are the bare 65"/24" run/rise
  (verify.py tolerates the difference).
