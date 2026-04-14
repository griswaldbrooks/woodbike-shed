#!/usr/bin/env python3
"""Fetch true oriented dimensions for every solid part via FeatureScript eval.

World-axis-aligned bboxes over-state the dimensions of any part that isn't
aligned to world axes (e.g. roof rafters tilted to the pitch). This script
runs a FeatureScript on the server that, for each solid body:

  1. Finds the largest planar face (the "broad" face of a board).
  2. Builds a coordinate system from that face's normal + in-plane axis.
  3. Computes a tight bounding box in that coordinate system.
  4. Returns name, partId, and three dimensions in inches.

Composite bodies are skipped (they're roll-ups, not physical lumber).

Output: scripts/oriented_dims.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from onshape import signed_request  # type: ignore

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"

# Note: `box` is a reserved word in FeatureScript — use `bb` instead.
FEATURESCRIPT = r"""
function(context is Context, queries is map)
{
    var results = [];
    // Solid bodies only — excludes composite roll-ups and sheet bodies.
    var bodies = evaluateQuery(context, qBodyType(qEverything(EntityType.BODY), BodyType.SOLID));
    for (var body in bodies)
    {
        var nameStr = "";
        try { nameStr = getProperty(context, { entity: body, propertyType: PropertyType.NAME }); } catch (e) {}

        // Find the broad face: largest planar face (thickness normal)
        var faces = evaluateQuery(context, qOwnedByBody(body, EntityType.FACE));
        var maxArea = 0 * meter * meter;
        var bestPlane;
        var foundFace = false;
        for (var f in faces)
        {
            try
            {
                var pl = evPlane(context, { face: f });
                var a = evArea(context, { entities: f });
                if (a > maxArea)
                {
                    maxArea = a;
                    bestPlane = pl;
                    foundFace = true;
                }
            }
            catch (e) {}
        }

        // Find longest linear edge for length direction
        var edges = evaluateQuery(context, qOwnedByBody(body, EntityType.EDGE));
        var maxLen = 0 * meter;
        var bestDir;
        var foundEdge = false;
        for (var e in edges)
        {
            try
            {
                var L = evLength(context, { entities: e });
                var ln = evLine(context, { edge: e });  // fails on non-linear edges
                if (L > maxLen)
                {
                    maxLen = L;
                    bestDir = ln.direction;
                    foundEdge = true;
                }
            }
            catch (er) {}
        }

        var dx = 0; var dy = 0; var dz = 0;
        if (foundFace && foundEdge)
        {
            // Project length direction onto face plane (in case edge isn't exactly in plane)
            var nrm = bestPlane.normal;
            var xAxis = normalize(bestDir - dot(bestDir, nrm) * nrm);
            var cs = coordSystem(bestPlane.origin, xAxis, nrm);
            var bb = evBox3d(context, { topology: body, tight: true, cSys: cs });
            dx = (bb.maxCorner[0] - bb.minCorner[0]) / inch;
            dy = (bb.maxCorner[1] - bb.minCorner[1]) / inch;
            dz = (bb.maxCorner[2] - bb.minCorner[2]) / inch;
        }
        else
        {
            var bb = evBox3d(context, { topology: body, tight: true });
            dx = (bb.maxCorner[0] - bb.minCorner[0]) / inch;
            dy = (bb.maxCorner[1] - bb.minCorner[1]) / inch;
            dz = (bb.maxCorner[2] - bb.minCorner[2]) / inch;
        }

        results = append(results, {
            "name": nameStr,
            "dx": dx,
            "dy": dy,
            "dz": dz
        });
    }
    return results;
}
"""


def unwrap_fs_value(v):
    """Recursively unwrap Onshape FS value envelopes into plain Python."""
    if not isinstance(v, dict):
        return v
    t = v.get("btType", "")
    if "ValueNumber" in t or "ValueInteger" in t:
        return v.get("value")
    if "ValueString" in t or "ValueBoolean" in t:
        return v.get("value")
    if "ValueArray" in t:
        return [unwrap_fs_value(x) for x in v.get("value", [])]
    if "ValueMap" in t:
        return {unwrap_fs_value(entry["key"]): unwrap_fs_value(entry["value"])
                for entry in v.get("value", [])}
    return v


def main():
    path = f"/api/v6/partstudios/d/{DID}/w/{WID}/e/{EID}/featurescript"
    body = json.dumps({"script": FEATURESCRIPT, "queries": {}}).encode("utf-8")
    status, resp = signed_request("POST", path, body=body, content_type="application/json")
    print(f"HTTP {status}")
    if status != 200:
        print(resp[:4000])
        sys.exit(1)
    data = json.loads(resp)
    notices = data.get("notices") or []
    errs = [n for n in notices if n.get("level") == "ERROR"]
    if errs:
        print(f"{len(errs)} errors:")
        for n in errs[:10]:
            loc = (n.get("stackTrace") or [{}])[0]
            print(f"  line {loc.get('line')} col {loc.get('column')}: {n.get('message')}")
        sys.exit(1)
    unwrapped = unwrap_fs_value(data["result"])
    out_path = Path(__file__).parent / "oriented_dims.json"
    out_path.write_text(json.dumps(unwrapped, indent=2))
    print(f"Wrote {len(unwrapped)} records to {out_path}")


if __name__ == "__main__":
    main()
