"""Finish trim: skirt (water table), corner boards, frieze, door casings.

All trim is 3/4" stock mounted ON the siding outer face (one proud layer,
backs touching the siding), so trim and siding never interpenetrate:
- skirt   1x8 over the rim joist band, siding starts behind its top edge
- corners two 1x6s per corner, one flat on each wall face (butting the
          skirt top and the frieze ends)
- frieze  1x10 band under the eave: square top at the plate tops on the
          front/back walls, raked (prism outline) on the side walls
- casings 1x6 door casings; head casing spans over the jamb casings

Every height/extent derives from finish_layout; only product widths here.
"""
from cad.common import TRIM_T, Audit, box_at, finish_layout, prism_yz
from cad.siding import SIDING_T
CAS_W = 5.5       # 1x6 casings + corner boards
FRIEZE_H = 9.25   # 1x10
SKIRT_H = 7.25    # 1x8


def _layer(L, wall):
    """(lo, hi) of the trim layer, proud of the siding outer face."""
    o = SIDING_T
    if wall == "front":
        return L["f"] - o - TRIM_T, L["f"] - o
    if wall == "back":
        return L["b"] + o, L["b"] + o + TRIM_T
    if wall == "left":
        return L["l"] - o - TRIM_T, L["l"] - o
    return L["r"] + o, L["r"] + o + TRIM_T


def build(audit: Audit):
    L = finish_layout(audit)
    f, b, l, r = L["f"], L["b"], L["l"], L["r"]
    zsk = L["rim_low"] - 0.5
    zc0 = zsk + SKIRT_H                      # trim starts on the skirt top
    parts = []

    # --- skirt ---------------------------------------------------------
    parts.append(box_at("finish skirt", l, r, *_layer(L, "front"),
                        zsk, zsk + SKIRT_H))
    parts.append(box_at("finish skirt", l, r, *_layer(L, "back"),
                        zsk, zsk + SKIRT_H))
    parts.append(box_at("finish skirt", *_layer(L, "left"), f, b,
                        zsk, zsk + SKIRT_H))
    parts.append(box_at("finish skirt", *_layer(L, "right"), f, b,
                        zsk, zsk + SKIRT_H))

    # --- corner boards: one flat 1x6 per wall face at each corner --------
    for cx, wall_x, sx in ((l, "left", 1), (r, "right", -1)):
        for cy, wall_y, sy in ((f, "front", 1), (b, "back", -1)):
            top_x = L["side_top"](cy)
            top_y = L["front_top"] if wall_y == "front" \
                else L["back_top_at"](SIDING_T + TRIM_T)
            x0 = cx if sx == 1 else cx - CAS_W
            y0 = cy if sy == 1 else cy - CAS_W
            # board flat on the wall_y face (runs in X)
            parts.append(box_at("finish corner boards", x0, x0 + CAS_W,
                                *_layer(L, wall_y), zc0, top_y))
            # board flat on the wall_x face (runs in Y)
            parts.append(box_at("finish corner boards", *_layer(L, wall_x),
                                y0, y0 + CAS_W, zc0, top_x))

    # --- frieze ----------------------------------------------------------
    parts.append(box_at("finish frieze", l + CAS_W, r - CAS_W,
                        *_layer(L, "front"),
                        L["front_top"] - FRIEZE_H, L["front_top"]))
    bz = L["back_top_at"](SIDING_T + TRIM_T)
    parts.append(box_at("finish frieze", l + CAS_W, r - CAS_W,
                        *_layer(L, "back"), bz - FRIEZE_H, bz))
    for wall in ("left", "right"):
        lo, hi = _layer(L, wall)
        t = L["side_top"]
        p = prism_yz([(f + CAS_W, t(f + CAS_W) - FRIEZE_H),
                      (b - CAS_W, t(b - CAS_W) - FRIEZE_H),
                      (b - CAS_W, t(b - CAS_W)),
                      (f + CAS_W, t(f + CAS_W))], lo, hi)
        p.label = "finish frieze"
        parts.append(p)

    # --- door casings: jamb + jamb + head-over-jambs per opening ---------
    # Corner-adjacent openings (the barn door at the west corner, the 64"
    # double on its 6.5" end studs) have no room for a full jamb casing
    # beside the corner board: the casing clamps to the corner board's
    # inner edge and degenerates to nothing when the corner board already
    # covers the jamb.
    def casing_pair(wall, o0, o1, hz, start, end):
        lo, hi = _layer(L, wall)
        a0 = max(o0 - CAS_W, start + CAS_W)
        a1 = min(o1 + CAS_W, end - CAS_W)
        def box(c0, c1, z0, z1):
            if wall in ("front", "back"):
                parts.append(box_at("finish door casings", c0, c1, lo, hi,
                                    z0, z1))
            else:
                parts.append(box_at("finish door casings", lo, hi, c0, c1,
                                    z0, z1))
        if a0 < o0:
            box(a0, o0, zc0, hz)
        if a1 > o1:
            box(o1, a1, zc0, hz)
        if wall in ("left", "right") and L["side_top"](a1) - FRIEZE_H \
                < hz + CAS_W:
            # the rake drops below the head casing's top: scribe the casing
            # to the frieze bottom (its top edge follows the rake line)
            from cad.common import prism_yz
            yb = (L["ref"].front_bear_z - (hz + CAS_W + FRIEZE_H - 1.0)) \
                / L["ref"].slope
            p = prism_yz([(a0, hz), (a1, hz),
                          (a1, L["side_top"](a1) - FRIEZE_H),
                          (yb, hz + CAS_W), (a0, hz + CAS_W)], lo, hi)
            p.label = "finish door casings"
            parts.append(p)
        else:
            box(a0, a1, hz, hz + CAS_W)

    for o0, o1, hz in L["front_open"]:
        casing_pair("front", o0, o1, hz, l, r)
    for o0, o1, hz in L["right_open"]:
        casing_pair("right", o0, o1, hz, f, b)
    return parts
