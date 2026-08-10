#!/usr/bin/env python3
"""One-command OCP CAD Viewer entry point for the build123d shed model.

Usage (VS Code with the "OCP CAD Viewer" extension, viewer listening):

    ~/.venvs/woodbike-shed/bin/python view.py

The viewer's part tree mirrors CUT_LIST.md: one group per cut-list section
(skids, floor, walls, roof), every part under its exact cut-list label.
Parts are tinted per structural group with the same legend the Blender
renders use (blender/group_colors.py) — one distinct hue per group.
Zero Onshape API calls — geometry comes from cad/ + the audit JSON files.
"""
import sys
import warnings

from cad.build import build_all
from blender.group_colors import MATERIALS, group_for
from scripts.build_cut_list import SECTION_ORDER, section_for

try:
    from ocp_vscode import show
    from ocp_vscode.utils import CommsWarning
except ImportError:
    sys.exit(
        "ocp_vscode is not installed in this interpreter.\n"
        "Run view.py inside VS Code with the 'OCP CAD Viewer' extension,\n"
        "using a venv that has ocp_vscode, e.g.:\n"
        "    ~/.venvs/woodbike-shed/bin/python view.py"
    )


def main():
    _, parts = build_all()

    # group tints shared with the Blender renders (blender/group_colors.py)
    for p in parts:
        p.color = (*MATERIALS[group_for(p.label)][0], 1.0)

    # section_for is the cut-list classifier, so the tree mirrors CUT_LIST.md
    groups = {}
    for p in parts:
        groups.setdefault(section_for(p.label), []).append(p)
    tree = {s: groups[s] for s in SECTION_ORDER if s in groups}

    print(f"showing {len(parts)} parts in {len(tree)} sections")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        show(tree, names=["wood bike shed"])

    # ocp_vscode 4.x warns (CommsWarning) instead of raising when nothing is
    # listening (connection refused, or no port set outside VS Code) -
    # detect that and leave a friendly hint.
    if any(issubclass(w.category, CommsWarning) for w in caught):
        sys.exit(
            "Model built, but no viewer is listening.\n"
            "Open this repo in VS Code with the 'OCP CAD Viewer' extension\n"
            "and run view.py again."
        )
    print("sent to OCP CAD Viewer")


if __name__ == "__main__":
    main()
