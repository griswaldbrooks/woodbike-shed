"""Roof section: 13 rafters, 2 fascia, 2 rake boards.

Rafters: 2x6 x 115.13", 15.875" o.c. at x = -2.75..187.75, falling in +Y at
the roof pitch, with a long front overhang (y -27.5") and short back
overhang. Rake boards: same section/length, tilted along the roof overhang
edges at x = -14.75 and 199.75. Fascia: 2x6 x 216" (12" past each side
wall), rolled about their long axis so the wide face lies in the roof plane.

TODO(captain): birdsmouth acceptance is a PENDING design decision (ship
orders). The Onshape model the audit came from has front/back seat cuts on
the rafters (documented in MANUAL_COMPLETION.md on branch
fm/woodbike-shed-finish-rework: seats at z=123 front / z=97.5 back). If
accepted, add the cuts here; until then rafters are full rectangular stock,
which is exactly what the cut list dimensions describe.
"""
from cad.common import (Audit, ROLL_X_GROUPS, place_roll_x, place_slope_y)

RAFTER = "roof rafters"
RAKE_BOARD = "roof rake board"


def build(audit: Audit):
    parts = []
    for spec in audit.group(RAFTER, RAKE_BOARD):
        # 2x6: 1.5" wide in X, 5.5" deep, length along the slope (Y)
        p = place_slope_y(spec, x_dim=1.5, z_dim=5.5, pitch_deg=audit.pitch_deg)
        p.label = spec.label
        parts.append(p)
    for spec in audit.group(*ROLL_X_GROUPS):
        p = place_roll_x(spec, audit.pitch_deg)
        p.label = spec.label
        parts.append(p)
    return parts
