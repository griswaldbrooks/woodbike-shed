"""Roof section: 13 rafters, front/back fascia, left/right rake boards.

Rafters: 2x6 x 115.13", 15.875" o.c. at x = -2.75..187.75, falling in +Y at
the roof pitch. Rake boards: same section/length along the roof overhang
edges. Fascia: 2x6 x 216" (12" past each side wall), axis-aligned vertical
boards since the 2026-08 roof-trim rework on main.

Birdsmouth note: the upstream model has front/back seat cuts on every rafter
(OUTSTANDING_ISSUES.md "Rafter bearing ... RESOLVED": front seat z=123, heel
y=-4.06; back seat z=97.5, plumb kick y=68.5) plus end trims. This rebuild
follows the CUT LIST, which describes rafters as full 2x6 x 115.13" stock,
so rafters here are rectangular; verify.py carries the resulting AABB deltas
as documented per-group tolerances. Implementing the cuts in code is a
follow-up if render fidelity needs it.
"""
from cad.common import Audit, place_box, place_slope_y

RAFTER = "rafter"
RAKE_BOARDS = ("left rake board", "right rake board")
FASCIA = ("front fascia", "back fascia")


def build(audit: Audit):
    parts = []
    for spec in audit.group(RAFTER, *RAKE_BOARDS):
        # 2x6: 1.5" wide in X, 5.5" deep, length along the slope (Y)
        p = place_slope_y(spec, x_dim=1.5, z_dim=5.5, pitch_deg=audit.pitch_deg)
        p.label = spec.label
        parts.append(p)
    for spec in audit.group(*FASCIA):
        p = place_box(spec)
        p.label = spec.label
        parts.append(p)
    return parts
