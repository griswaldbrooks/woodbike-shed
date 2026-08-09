# blender/ — headless render pipeline for the shed

`scene.glb` (121 named parts, from `cad/build.py`, names = CUT_LIST.md labels
with an `NNN ` instance prefix) + `build_scene.py`, which turns it into a lit,
materialled scene and renders it. Nothing hand-placed: cameras, ground and
sun derive from the imported bounding box, so re-running survives model
changes.

## Regenerate (headless)

Blender is not part of the repo. Any Blender 4.x works; on this box it lives
in the task worktree scratch:

```
./.scratch/blender-4.5.12-linux-x64/blender --background --python blender/build_scene.py            # -> shed_scene.blend
./.scratch/blender-4.5.12-linux-x64/blender --background --python blender/build_scene.py -- --render  # + renders/ (Cycles 1920x1080)
```

`--render` renders all four saved cameras into `blender/renders/`.
GPU (OptiX/CUDA) is used when present, CPU otherwise.

## Material-by-name-group

`group_for()` maps the cut-list label (after stripping the `NNN ` prefix) to
one material, checked in order: `sub floor osb` → OSB deck; `skid` (incl.
skid sister) → PT skids; `joist` (rim/floor) → PT floor framing; `rafter`;
`fascia`/`rake board` → trim; `plate` (incl. rake wall top plates); anything
else (studs, headers, king/jack/cripple) → framing lumber.

Each material is a Principled BSDF with a per-group base color/roughness, a
subtle Wave-texture grain in object space, and per-object brightness jitter
(Object Info → Random) so boards read individually. Tones are in the
`MATERIALS` dict at the top of `build_scene.py`.

## Scene

- Ground plane at the lowest board; Nishita sky (sun disc off) as ambient.
- One SUN lamp from front-left (~53° elevation); the sky's sun azimuth is
  matched to it.
- Cameras: `cam_front_left` / `cam_back_right` (3/4 product shots),
  `cam_interior` (axial view down the bay from the right-end door opening),
  `cam_elevation` (straight-on front, orthographic).
- Cycles 256 samples + denoise, AgX (medium-high contrast look).

## Known limits

- Framing-only model: no siding, sheathing or roof boards beyond the OSB
  floor deck (matches CUT_LIST.md scope).
- Rafters/trim are rectangular stock; no birdsmouth or end cuts (see
  `cad/README.md` pending items).
