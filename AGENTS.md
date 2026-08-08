# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.

## The Onshape document

One document, never touch any other: did `24d3743de768051f7ae10bb3`,
workspace (Main) `4c0f1b0cf9df2e322f841b94`, Part Studio
`5730975eb353b57bac8d52c4`. IDs also live at the top of every `scripts/*.py`.
Model state history and geometry rationale: `MANUAL_COMPLETION.md` and the
scout report referenced there. Restore version taken before the 2026-08-07
rework: `aa73830b88f34f965190a7c6` ("pre-fleet-completion 2026-08-05").

## Script pipeline

`fetch_bboxes.py` + `fetch_oriented_dims.py` (FeatureScript eval) →
`bboxes.json` / `oriented_dims.json` → `build_cut_list.py` → `CUT_LIST.md` +
`order_list.csv`. `verify_groups.py` checks dim consistency per part name.
Run from the repo root (scripts read `scripts/*.json` relatively).
`scripts/fs_probe.py '<FS code>'` is the eval REPL for model queries.

## Onshape API sharp edges (learned the hard way)

- `onshape.py` does signed GET/POST/PATCH/DELETE; pass a JSON body as 3rd
  arg (or `@file`). Credentials: `~/.config/onshape/credentials`.
- Renaming a part = POST `/api/v6/metadata/d/{did}/w/{wid}/e/{eid}/p/{partId}`
  updating property `57f3fb8efa3416c06701d60d` (Name). Body needs `href`
  fields; URL-quote partIds (they can contain `+`). Pattern:
  `scripts/rename_parts.py`.
- Feature names do NOT propagate to part names for standard features
  (bodies come out as `Part NN`); custom `frame` parts are the exception.
  Plan a metadata rename pass after adding features.
- Add features: POST `/api/v6/partstudios/.../features` with
  `{"serializationVersion","sourceMicroversion","feature"}` — the server
  assigns its own featureId (re-fetch the feature list to learn it before a
  dependent feature references it). Update: POST to
  `.../features/featureid/{fid}`; delete: DELETE on the same path.
- Sketch coordinates are in meters; plain-FS `queryString`s (e.g.
  `qSketchRegion(id + "…")`) work fine in place of qCompressed blobs.
  Clone an existing same-plane sketch's `sketchPlane` query verbatim to reuse
  its plane.
- Extrudes from a default-plane sketch: `oppositeDirection` flips the
  extrusion; `startOffset` moves the start along the plane normal (+),
  independent of extrusion direction — use `startOffsetOppositeDirection`
  to move it the other way.
- Tail of the feature tree (~indices 98–119) is the captain's mid-refactor
  work, in ERROR on deleted references — see `MANUAL_COMPLETION.md` before
  touching anything there.
- `fetch_oriented_dims.py` reports length as the longest linear edge; for
  plumb-cut (parallelogram) members a cSys box extent along the grain
  over-states the board length, so don't switch back to box-extent length.

## Naming conventions

Parts are named by section-role, one shared name per role group ("back wall
studs", "right wall headers"); `build_cut_list.section_for()` classifies by
those prefixes ("rake" wins over wall side). Keep new part names in that
scheme so the pipeline files them correctly.
