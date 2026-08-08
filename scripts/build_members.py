#!/usr/bin/env python3
"""Additively build the missing woodbike-shed members in the captain's Onshape doc.

Adds NEW features only (never touches the captain's features):
  stage 1: right rake wall studs (4, mitered to the live rake-plate underside)
  stage 2: left rake wall studs (4, same profile)
  stage 3: left rake wall top plate (mirror of the captain's right plate profile)
  stage 4: rafters (13, 2x6, per the captain's 'Rafter Right' sketch line)

Geometry derived from the live model (2026-08-07):
  - rake plate underside line: z = 97.5 + (24/65)*(60.669 - y)   [inches]
    (pulled from 'right rake wall top plate' edges: bottom edge through
     (y=60.669, z=97.5), slope 24/65, front bottom corner (-0.268, 120.0))
  - rake stud centers y = 0.75/16.25/32.25/48.25 (the wall 16" o.c. grid,
    same centers as the existing flat side-wall studs)
  - rafter bottom edge: (-27.5, 131.6538) -> (80.5, 91.7769) = the captain's
    'Rafter Right' line (24" front / 12" back overhang from wall outer faces,
    slope 24/65, bearing on front plate (y=0, z=121.5) and back plate
    (y=65, z=97.5)); depth 5.5 perpendicular, plumb end cuts -> board 115.13"
  - rafter X grid: 13 positions, centers -2.75 .. 187.75 (the live stud grid
    endpoints), uniform 15.875" spacing

Sketch space: the captain's 'right rake wall' sketch plane is reused
(verified mapping from his sketch point: sketch x = world Y, sketch y = world
Z, meters). Extrude direction/offsets are verified empirically per stage.
"""
import copy
import json
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from onshape import signed_request

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"
IN = 0.0254  # inch -> meter

DUMP = json.loads((Path(__file__).parent / "featurelist_dump.json").read_text())
FEATS = DUMP["features"]
SKETCH_TEMPLATE = FEATS[98]      # 'right rake wall' sketch (same plane, resolved)
EXTRUDE_TEMPLATE = FEATS[16]     # 'Subfloor' extrude
PATTERN_TEMPLATE = FEATS[21]     # 'Linear pattern 7'

SLOPE = 24.0 / 65.0


def uid(n=17):
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))


def zu(y_in):
    """Rake plate underside height at world y (inches)."""
    return 97.5 + SLOPE * (60.669 - y_in)


def seg(x0, y0, x1, y1, eid):
    """BTMSketchCurveSegment for a line (sketch units = meters)."""
    dx, dy = x1 - x0, y1 - y0
    L = (dx * dx + dy * dy) ** 0.5
    return {
        "btType": "BTMSketchCurveSegment-155",
        "geometry": {
            "btType": "BTCurveGeometryLine-117",
            "pntX": x0, "pntY": y0,
            "dirX": dx / L, "dirY": dy / L,
        },
        "isConstruction": False,
        "offsetCurveExtensions": [],
        "startPointId": f"{eid}.start",
        "endPointId": f"{eid}.end",
        "startParam": 0.0,
        "endParam": L,
        "centerId": "",
        "isFromSplineHandle": False,
        "internalIds": [],
        "curvedTextIds": [],
        "isFromEndpointSplineHandle": False,
        "isFromSplineControlPolygon": False,
        "namespace": "",
        "name": "",
        "parameters": [],
        "nodeId": uid(),
        "entityId": eid,
    }


def quad_entity(points_yz_in, prefix):
    """4 segments for a quad given as [(y,z), ...] in world inches."""
    entities = []
    n = len(points_yz_in)
    for i in range(n):
        (y0, z0) = points_yz_in[i]
        (y1, z1) = points_yz_in[(i + 1) % n]
        entities.append(seg(y0 * IN, z0 * IN, y1 * IN, z1 * IN, f"{prefix}seg{i}"))
    return entities


def make_sketch(feature_id, name, entities):
    sk = copy.deepcopy(SKETCH_TEMPLATE)
    sk["featureId"] = feature_id
    sk["nodeId"] = uid()
    sk["name"] = name
    sk["entities"] = entities
    sk["constraints"] = []
    # neutralize nodeIds inside parameters
    for p in sk["parameters"]:
        p["nodeId"] = uid()
        for q in p.get("queries", []) or []:
            q["nodeId"] = uid()
            q["deterministicIds"] = []
    return sk


def make_extrude(feature_id, name, sketch_id, depth_expr,
                 opposite_direction=False, start_offset_expr=None,
                 start_offset_opposite=False):
    ex = copy.deepcopy(EXTRUDE_TEMPLATE)
    ex["featureId"] = feature_id
    ex["nodeId"] = uid()
    ex["name"] = name
    for p in ex["parameters"]:
        p["nodeId"] = uid()
        pid = p["parameterId"]
        if pid == "entities":
            q = p["queries"][0]
            q["queryString"] = f'query = qSketchRegion(id + "{sketch_id}", true);'
            q["featureId"] = sketch_id
            q["nodeId"] = uid()
            q["deterministicIds"] = []
        elif pid == "depth":
            p["expression"] = depth_expr
        elif pid == "oppositeDirection":
            p["value"] = opposite_direction
        elif pid == "startOffset":
            p["value"] = start_offset_expr is not None
        elif pid == "startOffsetDistance" and start_offset_expr is not None:
            p["expression"] = start_offset_expr
        elif pid == "startOffsetOppositeDirection":
            p["value"] = start_offset_opposite
        elif pid in ("hasOffset", "hasExtrudeDirection", "midplane", "symmetric",
                     "hasDraft", "hasSecondDirection", "hasSecondDirectionOffset",
                     "hasSecondDirectionDraft"):
            p["value"] = False
        elif isinstance(p.get("queries"), list) and pid != "entities":
            p["queries"] = []
    return ex


def add_feature(feature):
    body = {
        "serializationVersion": DUMP.get("serializationVersion", "1.2.21"),
        "sourceMicroversion": DUMP.get("sourceMicroversion"),
        "feature": feature,
    }
    path = f"/api/v6/partstudios/d/{DID}/w/{WID}/e/{EID}/features"
    s, b = signed_request("POST", path, body=json.dumps(body).encode())
    return s, b


def feature_list():
    s, b = signed_request("GET", f"/api/v6/partstudios/d/{DID}/w/{WID}/e/{EID}/features")
    data = json.loads(b)
    return data["features"], data.get("featureStates", {})


def add_and_resolve(feature):
    """Add a feature; return its server-assigned featureId (the new tail entry)."""
    before, _ = feature_list()
    s, b = add_feature(feature)
    if s != 200:
        print(f"    HTTP {s}\n{b[:2000]}")
        sys.exit(1)
    after, states = feature_list()
    if len(after) <= len(before):
        print("    !! feature list did not grow")
        sys.exit(1)
    new = after[-1]
    fid = new["featureId"]
    st = states.get(fid, {})
    print(f"    -> server id {fid} status={st.get('featureStatus')}")
    return fid


def make_pattern(feature_id, name, seed_body_feature_id, distance_expr, count_expr,
                 opposite_direction=False):
    pat = copy.deepcopy(PATTERN_TEMPLATE)
    pat["featureId"] = feature_id
    pat["nodeId"] = uid()
    pat["name"] = name
    for p in pat["parameters"]:
        p["nodeId"] = uid()
        pid = p["parameterId"]
        if pid == "entities":
            p["queries"] = [{
                "btType": "BTMIndividualQuery-138",
                "queryStatement": None,
                "queryString": f'query = qCreatedBy(id + "{seed_body_feature_id}", EntityType.BODY);',
                "nodeId": uid(),
                "deterministicIds": [],
            }]
        elif pid == "directionOne":
            # reuse the captain's rake sketch-plane query verbatim (normal = world X)
            q = SKETCH_TEMPLATE["parameters"][0]["queries"][0]
            p["queries"] = [dict(q, nodeId=uid(), deterministicIds=[])]
        elif pid == "distance":
            p["expression"] = distance_expr
        elif pid == "instanceCount":
            p["expression"] = count_expr
        elif pid == "oppositeDirection":
            p["value"] = opposite_direction
        elif pid == "hasSecondDir":
            p["value"] = False
        elif pid in ("faces", "booleanScope", "directionTwo"):
            p["queries"] = []
    return pat


def part_summary():
    s, b = signed_request("GET", f"/api/v6/parts/d/{DID}/w/{WID}/e/{EID}")
    parts = json.loads(b)
    names = {}
    for p in parts:
        names.setdefault(p["name"], []).append(p["partId"])
    return len(parts), names


# ---- geometry ----------------------------------------------------------------

def rake_stud_quads():
    quads = []
    for i, yc in enumerate([0.75, 16.25, 32.25, 48.25]):
        y0, y1 = yc - 0.75, yc + 0.75
        quads.append((f"rs{i}", [(y0, 97.5), (y1, 97.5), (y1, zu(y1)), (y0, zu(y0))]))
    return quads


LEFT_RAKE_PLATE = [(65.0, 97.5), (0.0, 121.5), (-0.268, 120.0), (60.669, 97.5)]

RAFTER = [(-27.5, 131.65385), (80.5, 91.77692), (80.5, 97.63975), (-27.5, 137.51668)]

# Roof trim (per the April roof: 2 fascia 2x6 x 216" = shed + 12" past each
# side wall, 2 rake boards along the slope outside the end rafters, running
# end-to-end flush with the fascia outer faces). Fascia tops flush with the
# rafter tail tops.
FRONT_FASCIA = [(-29.0, 132.01668), (-27.5, 132.01668), (-27.5, 137.51668), (-29.0, 137.51668)]
BACK_FASCIA = [(80.5, 92.13975), (82.0, 92.13975), (82.0, 97.63975), (80.5, 97.63975)]
RAKE_BOARD = [(-29.0, 132.20769), (82.0, 91.22308), (82.0, 97.08591), (-29.0, 138.07052)]


def run_stage(stage_name):
    if stage_name in ("right-studs", "left-studs"):
        side = "right" if stage_name == "right-studs" else "left"
        entities = []
        for prefix, quad in rake_stud_quads():
            entities += quad_entity(quad, prefix)
        sk = make_sketch("Ftmp1", f"{side} rake wall studs profile", entities)
        print(f"--- adding sketch {sk['name']!r}")
        sid = add_and_resolve(sk)
        if side == "right":
            ex = make_extrude("Ftmp2", f"{side} rake wall studs", sid, "3.5 in",
                              opposite_direction=True)
        else:
            ex = make_extrude("Ftmp2", f"{side} rake wall studs", sid, "3.5 in",
                              opposite_direction=True, start_offset_expr="188.5 in",
                              start_offset_opposite=True)
        print(f"--- adding extrude {ex['name']!r}")
        add_and_resolve(ex)
    elif stage_name == "left-plate":
        sk = make_sketch("Ftmp1", "left rake wall top plate profile",
                         quad_entity(LEFT_RAKE_PLATE, "lp"))
        print(f"--- adding sketch {sk['name']!r}")
        sid = add_and_resolve(sk)
        ex = make_extrude("Ftmp2", "left rake wall top plate", sid, "3.5 in",
                          opposite_direction=True, start_offset_expr="188.5 in",
                          start_offset_opposite=True)
        print(f"--- adding extrude {ex['name']!r}")
        add_and_resolve(ex)
    elif stage_name == "rafters":
        sk = make_sketch("Ftmp1", "rafter profile", quad_entity(RAFTER, "rf"))
        print(f"--- adding sketch {sk['name']!r}")
        sid = add_and_resolve(sk)
        ex = make_extrude("Ftmp2", "rafter", sid, "1.5 in",
                          opposite_direction=True, start_offset_expr="190.5 in",
                          start_offset_opposite=True)
        print(f"--- adding extrude {ex['name']!r}")
        exid = add_and_resolve(ex)
        pat = make_pattern("Ftmp3", "rafter pattern", exid, "15.875 in", "13")
        print(f"--- adding pattern {pat['name']!r}")
        add_and_resolve(pat)
    elif stage_name == "trim":
        jobs = [
            ("front fascia profile", FRONT_FASCIA, "front fascia", "216 in",
             True, "12 in", False),
            ("back fascia profile", BACK_FASCIA, "back fascia", "216 in",
             True, "12 in", False),
            ("left rake board profile", RAKE_BOARD, "left rake board", "1.5 in",
             True, "202.5 in", True),
            ("right rake board profile", RAKE_BOARD, "right rake board", "1.5 in",
             False, "10.5 in", False),
        ]
        for skname, quad, exname, depth, opp, off, offopp in jobs:
            sk = make_sketch("Ftmp1", skname,
                             quad_entity(quad, exname.replace(" ", "")[:4]))
            print(f"--- adding sketch {sk['name']!r}")
            sid = add_and_resolve(sk)
            ex = make_extrude("Ftmp2", exname, sid, depth,
                              opposite_direction=opp, start_offset_expr=off,
                              start_offset_opposite=offopp)
            print(f"--- adding extrude {ex['name']!r}")
            add_and_resolve(ex)
    else:
        raise SystemExit(f"unknown stage {stage_name}")


def main():
    stage_name = sys.argv[1]
    run_stage(stage_name)
    n, names = part_summary()
    print(f"\nparts now: {n}")
    for k in sorted(names):
        if "rake" in k or "rafter" in k or k.startswith("Part"):
            print(f"  {k}: {len(names[k])}")


if __name__ == "__main__":
    main()
