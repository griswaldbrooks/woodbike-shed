"""Skids section: 2 continuous 16' (192") 4x4 skid lines.

Captain's 2026-08-10 redesign (amended ship order): the sistered
arrangement is dropped - each skid line is ONE full-shed-length 4x4
(x = -3.5..188.5), sitting on the audited composite-skid lines under the
front/back wall bearing lines (y -3.5..0 and 65..68.5, z -9.75..-6.25).
Hingham stocks 16' 4x4; PT ground-contact tagging unchanged. This is a
deliberate divergence from the Onshape model's sistered composite skids -
see OUTSTANDING_ISSUES.md "Skid redesign".
"""
from cad.common import Audit, place_box


def build(audit: Audit):
    parts = []
    for s in audit.group("skid"):
        p = place_box(s)
        p.label = s.label
        parts.append(p)
    return parts
