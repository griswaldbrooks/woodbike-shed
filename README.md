# woodbike-shed

Tooling to pull a BOM / cut list from the Onshape model of the bike shed and
prep lumber-yard RFQs.

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

## Scripts

- `scripts/onshape.py` — signed-request helper against `cad.onshape.com/api/v6`.
  Usage: `python3 scripts/onshape.py GET /api/v6/documents/{did}`.
- `scripts/fetch_bboxes.py` — pulls world-axis-aligned bounding boxes for every
  part in the Part Studio. Writes `scripts/bboxes.json`.
- `scripts/verify_groups.py` — groups parts by name and flags any
  within-group dimension variance. Useful for sanity-checking the
  model after bulk-renaming.
