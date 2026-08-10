"""Build the full bike-shed model and export STEP + glTF.

Run from repo root:  .venv/bin/python -m cad.build
Outputs:
  step/NNN <cut-list label>.step   one file per part (names match CUT_LIST.md)
  blender/scene.glb                named scene for Blender (node names = above)
"""
from pathlib import Path

import trimesh
from build123d.exporters3d import export_step

from cad import (common, doors, floor, roof, siding, skids, trim, walls_back,
                 walls_front, walls_rake, walls_side)
from cad.common import REPO

MODULES = (skids, floor, walls_front, walls_back, walls_side, walls_rake, roof)
# captain 2026-08-10: doors/siding/trim are real parts but a SEPARATE order
# list (scripts/build_finish_cut_list.py) - never mixed into the framing one.
FINISH_MODULES = (siding, trim, doors)


def build_all():
    audit = common.load_audit()
    parts = []
    for m in MODULES:
        parts.extend(m.build(audit))
    return audit, parts


def build_finish(audit):
    parts = []
    for m in FINISH_MODULES:
        parts.extend(m.build(audit))
    return parts


def export(parts):
    step_dir = REPO / "step"
    blender_dir = REPO / "blender"
    step_dir.mkdir(exist_ok=True)
    blender_dir.mkdir(exist_ok=True)

    scene = trimesh.Scene()
    for i, p in enumerate(parts, 1):
        fname = f"{i:03d} {p.label}.step"
        # trap rule 2: export_step takes ONE shape, never a list
        export_step(p, step_dir / fname)
        verts, tris = p.tessellate(0.5)
        name = f"{i:03d} {p.label}"
        scene.add_geometry(
            trimesh.Trimesh(vertices=[tuple(v) for v in verts], faces=tris),
            node_name=name, geom_name=name)
    # trimesh .glb export is always binary GLB (the build123d export_gltf
    # binary=False trap does not apply here - kept trimesh for this reason).
    scene.export(blender_dir / "scene.glb")
    return len(parts)


def main():
    audit, parts = build_all()
    n_framing = len(parts)
    parts += build_finish(audit)
    n = export(parts)
    labels = {p.label for p in parts}
    print(f"built {n} parts ({n_framing} framing, {n - n_framing} finish), "
          f"{len(labels)} cut-list names, roof pitch {audit.pitch_deg:.3f} deg")


if __name__ == "__main__":
    main()
