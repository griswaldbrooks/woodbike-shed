#!/usr/bin/env python3
"""Probe FeatureScript eval with a minimal script to understand the syntax."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from onshape import signed_request

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"

SCRIPT = sys.argv[1] if len(sys.argv) > 1 else r"""
function(context is Context, queries is map)
{
    var bodies = evaluateQuery(context, qEverything(EntityType.BODY));
    return size(bodies);
}
"""

path = f"/api/v6/partstudios/d/{DID}/w/{WID}/e/{EID}/featurescript"
body = json.dumps({"script": SCRIPT, "queries": {}}).encode("utf-8")
status, resp = signed_request("POST", path, body=body, content_type="application/json")
print(f"HTTP {status}")
data = json.loads(resp)
print("result:", json.dumps(data.get("result"), indent=2)[:1000])
notices = data.get("notices") or []
if notices:
    print(f"\n{len(notices)} notices:")
    for n in notices[:10]:
        loc = n.get("stackTrace", [{}])[0]
        print(f"  [{n['level']}] line {loc.get('line')} col {loc.get('column')}: {n.get('message')}")
console = data.get("console")
if console:
    print(f"\nconsole: {console}")
