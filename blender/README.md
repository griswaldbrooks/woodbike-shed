# blender/ — headless render pipeline for the shed

`scene.glb` (117 named parts, from `cad/build.py`, names = CUT_LIST.md labels
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
./.scratch/blender-4.5.12-linux-x64/blender --background --python blender/build_scene.py -- --skin --render  # dressed variant -> shed_skin.blend + renders/skin/
```

`--render` renders all four saved cameras into `blender/renders/`.
GPU (OptiX/CUDA) is used when present, CPU otherwise.

## Skin mode (`--skin`) — render dressing, NOT modeled lumber

`--skin` layers a "finished shed" look over the framing for presentation
renders, matching the captain's reference photo: blue-gray horizontal lap
siding, white corner boards / door casings / frieze / skirt, barn-red plank
doors with black strap hinges and latches, and a natural-wood roof deck with
exposed rafter tails. Doors follow the model's actual framed openings (front
single + front double + right single), not the photo's door count.

Everything is procedural boxes/prisms aligned to wall planes and openings
read off the imported parts' world bboxes (`skin_layout()`), so like the
cameras it re-derives from `scene.glb`. `scene.glb` and the framing-only /
colorized modes are untouched; the framing model stays the source of truth.
Saves `shed_skin.blend` and renders four views (front-left 3/4 at the
reference angle, back-right, straight-on front, double-door close-up) into
`blender/renders/skin/`.

## Material-by-name-group

`group_for()` maps the cut-list label (after stripping the `NNN ` prefix) to
one material, checked in order: `sub floor osb` → deck; `skid` (incl. skid
sister); `joist` (rim/floor) → floor_frame; `rafter`; `fascia`;
`rake board` → rake; `plate`/`header` (incl. rake wall top plates) → plates;
anything else (studs, king/jack/cripple) → studs. Each group gets a distinct
wood-tinted hue (annotated-product-shot style, legend under Scene).

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

### Group color legend

Approximate on-screen tints (base colors from `MATERIALS` in
`build_scene.py`; renders here are the ground truth):

| Group | Tint | Parts |
|---|---|---|
| skid | dark olive `#8E8B69` | skid (two continuous 16' 4x4) |
| floor_frame | dark amber `#A28159` | rim joist, floor joist |
| deck | golden `#CBBC81` | sub floor osb |
| studs | pale blond `#D4BCAD` | studs, king/jack/cripple studs |
| plates | honey orange `#CBA261` | plates, headers |
| rafter | cedar red `#C29079` | rafter |
| fascia | driftwood gray `#A2A4AA` | back/front fascia |
| rake | rosewood plum `#AA8195` | rake boards |

## Known limits

- Framing-only model: no siding, sheathing or roof boards beyond the OSB
  floor deck (matches CUT_LIST.md scope).
