# woodbike-shed

Tooling to pull a BOM / cut list from the Onshape model of the bike shed and
prep lumber-yard RFQs.

## Model as code

[`cad/`](cad/README.md) re-derives the whole shed model as build123d code
from this repo's audit data (no Onshape API calls) and exports per-part STEP
plus one named `blender/scene.glb` for renders. Build: `.venv/bin/python -m
cad.build` — verify (run after every change): `.venv/bin/python -m cad.verify`.

## Onshape document

- Name: *wood bike shed*
- URL: <https://cad.onshape.com/documents/24d3743de768051f7ae10bb3/w/4c0f1b0cf9df2e322f841b94/e/5730975eb353b57bac8d52c4>

## Credentials

API keys are stored in `~/.config/onshape/credentials` (mode `0600`, outside
this repo) as:

```
ONSHAPE_ACCESS_KEY=...
ONSHAPE_SECRET_KEY=...
```

Never commit these. The `.gitignore` blocks common credential filenames anyway.

## Key files

- [`CUT_LIST.md`](CUT_LIST.md) — full cut list grouped by section (skids,
  floor, walls, roof), with stock-length optimization.
- [`order_list.csv`](order_list.csv) — quote-ready CSV: lumber, treatment,
  stock length, qty.
- [`OUTSTANDING_ISSUES.md`](OUTSTANDING_ISSUES.md) — open items before
  sending quotes (stock availability, species, pre-cuts, waste factor, etc.).
- [`cad/`](cad/README.md) — model-as-code rebuild (build123d), per-part STEP
  exports in `step/`, Blender scene in `blender/scene.glb`.

## Scripts

- `scripts/onshape.py` — signed-request helper against `cad.onshape.com/api/v6`.
  Usage: `python3 scripts/onshape.py GET /api/v6/documents/{did}`.
- `scripts/fetch_bboxes.py` — pulls world-axis-aligned bounding boxes for every
  part in the Part Studio. Writes `scripts/bboxes.json`.
- `scripts/fetch_oriented_dims.py` — uses FeatureScript eval to get true
  oriented bounding boxes (correct for tilted parts like rafters). Writes
  `scripts/oriented_dims.json`.
- `scripts/build_cut_list.py` — builds `CUT_LIST.md` and `order_list.csv`
  from oriented dims. Classifies lumber, groups by section, assigns treatment
  (PT/KD), runs stock-length optimization with FFD bin packing.
- `scripts/verify_groups.py` — groups parts by name and flags any
  within-group dimension variance. Useful for sanity-checking the
  model after bulk-renaming.
- `scripts/fs_probe.py` — lightweight FeatureScript REPL for debugging.
