"""Shared group-color legend: Blender renders and the OCP CAD Viewer agree.

One distinct muted wood hue per structural name group. blender/build_scene.py
uses the full tuples (base + roughness/jitter/grain for the PBR woods);
view.py maps the base color onto each part's .color. Keep this file
importable without bpy. Legend hexes in blender/README.md.
"""

# group key -> (base color, roughness, per-board brightness jitter,
#               grain stripe scale, grain mix strength)
MATERIALS = {
    "skid":         ((0.27, 0.26, 0.14), 0.74, 0.22, 8.0, 0.08),   # dark olive (PT)
    "floor_frame":  ((0.36, 0.22, 0.10), 0.80, 0.24, 8.0, 0.10),   # dark amber (PT)
    "deck":         ((0.60, 0.50, 0.22), 0.88, 0.12, 16.0, 0.18),  # golden OSB
    "studs":        ((0.66, 0.50, 0.42), 0.78, 0.30, 9.0, 0.14),   # pale blond SPF
    "plates":       ((0.60, 0.36, 0.12), 0.76, 0.24, 9.0, 0.12),   # honey orange
    "rafter":       ((0.54, 0.28, 0.19), 0.78, 0.30, 7.0, 0.14),   # cedar red
    "fascia":       ((0.36, 0.37, 0.40), 0.70, 0.16, 6.0, 0.10),   # driftwood gray
    "rake":         ((0.40, 0.22, 0.30), 0.72, 0.18, 6.0, 0.12),   # rosewood plum
    # finish parts (cad/siding.py, trim.py, doors.py) - skin palette hues
    "siding":       ((0.150, 0.200, 0.280), 0.55, 0.10, 16.0, 0.10),  # blue-gray lap
    "trim":         ((0.780, 0.770, 0.730), 0.50, 0.05, 8.0, 0.05),   # white trim
    "doors":        ((0.280, 0.045, 0.035), 0.55, 0.12, 9.0, 0.10),   # barn red
}


def group_for(label: str) -> str:
    """Cut-list label -> material group; order matters."""
    if "sub floor osb" in label:
        return "deck"
    if "skid" in label:                       # continuous 16' skid lines
        return "skid"
    if "joist" in label:                      # rim joist, floor joist (PT)
        return "floor_frame"
    if label == "rafter":
        return "rafter"
    if "fascia" in label:
        return "fascia"
    if "rake board" in label:
        return "rake"
    if "plate" in label or "header" in label:  # incl. rake wall top plates
        return "plates"
    if label.startswith("finish siding"):
        return "siding"
    if label.startswith("finish door casing"):
        return "trim"
    if label.startswith("finish door"):
        return "doors"
    if label.startswith("finish"):             # corner/frieze/skirt
        return "trim"
    return "studs"                            # studs, jacks, kings, cripples
