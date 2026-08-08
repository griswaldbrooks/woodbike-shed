#!/usr/bin/env python3
"""Pilot: replace the absolute-coord 'right rake wall studs profile' sketch
(FqDfLcBqgGzsYjO_103) with a relationship-driven one, in place.

Subcommands:
  build      write sketch_new.json next to this script (dry)
  update     POST the in-place feature update
  restore    POST the original sketch back (rollback)
  inspect    print stored constraint det ids + states for sketch & extrude
"""
import copy
import json
import os
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from onshape import signed_request

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"
BASE = f"/api/v6/partstudios/d/{DID}/w/{WID}/e/{EID}"
SKETCH_FID = "FqDfLcBqgGzsYjO_103"
EXTRUDE_FID = "Fy5dCT6DCAu9y9X_103"
LOG = Path("/tmp/mutation_log.txt")

HERE = Path(__file__).resolve().parent
IN = 0.0254
SLOPE = 24.0 / 65.0
CENTERS_IN = [0.75, 16.25, 32.25, 48.25]
SAMPLE_X = 4.7117          # 185.5 in: inside plate x-range, clear of rightmost rafter
PLATE_TOP_Z = 2.4765       # 97.5 in
SEED_DX = 0.005            # deliberate seed perturbation so the solver must move geometry
SEED_DZ = -0.0365


def zu_m(y_in):
    return (97.5 + SLOPE * (60.669 - y_in)) * IN


def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    print(msg)


def uid(n=17):
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))


def seg(x0, y0, x1, y1, eid, index):
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
        "index": index,
    }


def c_base(ctype, params, index):
    return {
        "btType": "BTMSketchConstraint-2",
        "hasOffsetData1": False,
        "offsetOrientation1": False,
        "offsetDistance1": 0.0,
        "hasOffsetData2": False,
        "offsetOrientation2": False,
        "offsetDistance2": 0.0,
        "hasPierceParameter": False,
        "pierceParameter": 0.0,
        "helpParameters": [],
        "namespace": "",
        "constraintType": ctype,
        "name": "",
        "parameters": params,
        "index": index,
        "nodeId": uid(),
        "entityId": uid(15),
    }


def p_str(pid, value):
    return {"btType": "BTMParameterString-149", "libraryRelationType": "DEFAULT",
            "value": value, "nodeId": uid(), "parameterId": pid, "parameterName": ""}


def p_ext(pid, query_string):
    return {"btType": "BTMParameterQueryList-148", "libraryRelationType": "DEFAULT",
            "queries": [{"btType": "BTMIndividualQuery-138", "queryStatement": None,
                         "queryString": query_string, "nodeId": uid(), "deterministicIds": []}],
            "filter": None, "nodeId": uid(), "parameterId": pid, "parameterName": ""}


def p_enum(pid, enum_name, value):
    return {"btType": "BTMParameterEnum-145", "namespace": "", "nodeId": uid(),
            "libraryRelationType": "DEFAULT", "enumName": enum_name, "value": value,
            "parameterId": pid, "parameterName": ""}


def p_qty(pid, expr):
    return {"btType": "BTMParameterQuantity-147", "libraryRelationType": "DEFAULT",
            "isInteger": False, "value": 0.0, "units": "", "expression": expr,
            "nodeId": uid(), "parameterId": pid, "parameterName": ""}


def face_q(x, y, z):
    return ("query = qContainsPoint(qEverything(EntityType.FACE), "
            f"vector({x}, {y}, {z}) * meter);")


def distance_c(line_a, line_b, expr, index):
    return c_base("DISTANCE", [
        p_str("localFirst", line_a),
        p_str("localSecond", line_b),
        p_enum("direction", "DimensionDirection", "HORIZONTAL"),
        p_qty("length", expr),
        p_enum("alignment", "DimensionAlignment", "ALIGNED"),
        p_qty("labelRatio", "0.5"),
        p_qty("labelDistance", "0.05*m"),
    ], index)


def build():
    old = json.loads((HERE / "sketch_old_absolute.json").read_text())
    entities = []
    constraints = []
    quads = []  # per stud: dict of the 4 entity ids
    idx = 0
    for c_in in CENTERS_IN:
        y0 = (c_in - 0.75) * IN + SEED_DX
        y1 = (c_in + 0.75) * IN + SEED_DX
        zb = PLATE_TOP_Z + SEED_DZ
        zt0 = zu_m(c_in - 0.75) + SEED_DZ
        zt1 = zu_m(c_in + 0.75) + SEED_DZ
        b, r, t, l = uid(12), uid(12), uid(12), uid(12)
        entities += [
            seg(y0, zb, y1, zb, b, idx + 1),
            seg(y1, zb, y1, zt1, r, idx + 2),
            seg(y1, zt1, y0, zt0, t, idx + 3),
            seg(y0, zt0, y0, zb, l, idx + 4),
        ]
        idx += 4
        quads.append({"B": b, "R": r, "T": t, "L": l, "c_in": c_in})

    # The rake plate's underside face is NOT probeable via qContainsPoint (the
    # frame-feature sweep surface rejects point containment). The plate's TOP
    # face IS probeable, and the underside plane is exactly 1.5 in perpendicular
    # below it: (121.5-119.901)/sqrt(1+(24/65)^2) = 1.5000 in. So the top edge is
    # dimensioned 1.5 in (MINIMUM) from the top face instead.
    top_z_at_30 = (121.5 - SLOPE * 30.0) * IN
    halfspace = os.environ.get("HALFSPACE", "LEFT")
    ci = 0
    for i, q in enumerate(quads):
        c_in = q["c_in"]
        # between-stud sample y's keep the point clear of any coplanar stud faces
        y_sample_in = {0: 8.5, 1: 24.5, 2: 40.5, 3: 56.25}[i]
        constraints.append(c_base("HORIZONTAL", [p_str("localFirst", q["B"])], 1)); ci += 1
        constraints.append(c_base("COINCIDENT", [
            p_str("localFirst", q["B"]),
            p_ext("externalSecond", face_q(SAMPLE_X, y_sample_in * IN, PLATE_TOP_Z)),
        ], 2)); ci += 1
        constraints.append(c_base("DISTANCE", [
            p_ext("externalFirst", face_q(SAMPLE_X, 30.0 * IN, top_z_at_30)),
            p_str("localSecond", q["T"]),
            p_enum("direction", "DimensionDirection", "MINIMUM"),
            p_qty("length", "1.5 in"),
            p_enum("halfSpace1", "DimensionHalfSpace", halfspace),
            p_qty("labelRatio", "0.5"),
            p_qty("labelDistance", "0.05*m"),
        ], 1)); ci += 1
        constraints.append(c_base("VERTICAL", [p_str("localFirst", q["L"])], 1)); ci += 1
        constraints.append(c_base("VERTICAL", [p_str("localFirst", q["R"])], 2)); ci += 1
        constraints.append(distance_c(q["L"], q["R"], "1.5 in", 1)); ci += 1
        constraints.append(c_base("COINCIDENT", [p_str("localFirst", f"{q['B']}.end"), p_str("localSecond", f"{q['R']}.start")], 10)); ci += 1
        constraints.append(c_base("COINCIDENT", [p_str("localFirst", f"{q['R']}.end"), p_str("localSecond", f"{q['T']}.start")], 11)); ci += 1
        constraints.append(c_base("COINCIDENT", [p_str("localFirst", f"{q['T']}.end"), p_str("localSecond", f"{q['L']}.start")], 12)); ci += 1
        constraints.append(c_base("COINCIDENT", [p_str("localFirst", f"{q['L']}.end"), p_str("localSecond", f"{q['B']}.start")], 13)); ci += 1

    # stud-1 anchor: left edge on the y=0 plane via the front wall top plate's
    # outer face (the rake-plate trim face at y=0 is created DOWNSTREAM of this
    # sketch and is invisible to it at regen time).
    constraints.append(c_base("COINCIDENT", [
        p_str("localFirst", quads[0]["L"]),
        p_ext("externalSecond", face_q(SAMPLE_X, 0.0, 3.06)),
    ], 4)); ci += 1
    # stud-to-stud spacing (left edge -> next left edge). Ground-truth left
    # edges are 0, 15.5, 31.5, 47.5 in -> spacings 15.5, 16, 16 (stud 1 hard
    # against the front corner, studs 2-4 on the 16in grid).
    for i, sp in enumerate(("15.5 in", "16 in", "16 in")):
        constraints.append(distance_c(quads[i]["L"], quads[i + 1]["L"], sp, 2 + i)); ci += 1

    sk = copy.deepcopy(old)
    sk["entities"] = entities
    sk["constraints"] = constraints
    sk["nodeId"] = uid()  # fresh feature node id; parameters (sketchPlane) kept verbatim
    return sk


def post_update(feature, label):
    s, b = signed_request("GET", f"{BASE}/features")
    d = json.loads(b)
    body = {"serializationVersion": d["serializationVersion"],
            "sourceMicroversion": d["sourceMicroversion"],
            "feature": feature}
    s, b = signed_request("POST", f"{BASE}/features/featureid/{feature['featureId']}",
                          body=json.dumps(body).encode())
    log(f"POST {BASE}/features/featureid/{feature['featureId']}  [{label}]  HTTP {s}  sourceMicroversion={body['sourceMicroversion']}")
    if s != 200:
        print(b[:3000])
        sys.exit(1)


def inspect():
    s, b = signed_request("GET", f"{BASE}/features")
    d = json.loads(b)
    states = d["featureStates"]
    feats = {f["featureId"]: f for f in d["features"]}
    print("features:", len(d["features"]), "nonOK:",
          {k: v["featureStatus"] for k, v in states.items() if v.get("featureStatus") != "OK"})
    for fid, label in ((SKETCH_FID, "sketch"), (EXTRUDE_FID, "extrude")):
        f = feats.get(fid)
        if not f:
            print(f"{label} MISSING"); continue
        print(f"{label} {fid}: state={states.get(fid, {}).get('featureStatus')} name={f['name']!r}")
    sk = feats[SKETCH_FID]
    for c in sk.get("constraints", []):
        ext = [p for p in c["parameters"] if p["parameterId"].startswith("external")]
        if not ext:
            continue
        loc = [p["value"] for p in c["parameters"] if p["parameterId"].startswith("local")]
        q = ext[0]["queries"][0] if ext[0].get("queries") else {}
        det = q.get("deterministicIds")
        flag = "DANGLING!" if det == [""] else ""
        print(f"  {c['constraintType']} local={loc} ext det={det} {flag}")


def main():
    cmd = sys.argv[1]
    if cmd == "build":
        sk = build()
        json.dump(sk, open(HERE / "sketch_new.json", "w"), indent=1)
        print(f"built: {len(sk['entities'])} entities, {len(sk['constraints'])} constraints")
    elif cmd == "update":
        sk = json.loads((HERE / "sketch_new.json").read_text())
        post_update(sk, "pilot relationship-driven sketch")
    elif cmd == "restore":
        old = json.loads((HERE / "sketch_old_absolute.json").read_text())
        post_update(old, "ROLLBACK original absolute sketch")
    elif cmd == "inspect":
        inspect()
    else:
        raise SystemExit(f"unknown {cmd}")


if __name__ == "__main__":
    main()
