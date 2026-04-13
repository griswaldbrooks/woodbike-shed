#!/usr/bin/env python3
"""Fetch bounding boxes for every part in the Part Studio, concurrently.
Writes results to scripts/bboxes.json as a list of {partId, name, bbox} records.
"""
import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from onshape import signed_request  # type: ignore

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"

# 1. List parts
status, body = signed_request("GET", f"/api/v6/parts/d/{DID}/w/{WID}/e/{EID}")
assert status == 200, (status, body)
parts = json.loads(body)

# 2. For each part, fetch bbox
def fetch_bbox(part):
    pid = part["partId"]
    pid_enc = urllib.parse.quote(pid, safe="")
    path = f"/api/v6/parts/d/{DID}/w/{WID}/e/{EID}/partid/{pid_enc}/boundingboxes"
    status, body = signed_request("GET", path)
    if status != 200:
        return {"partId": pid, "name": part["name"], "error": f"HTTP {status}: {body[:200]}"}
    bb = json.loads(body)
    return {
        "partId": pid,
        "name": part["name"],
        "bbox_m": bb,
        "dx_m": bb["highX"] - bb["lowX"],
        "dy_m": bb["highY"] - bb["lowY"],
        "dz_m": bb["highZ"] - bb["lowZ"],
    }

results = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch_bbox, p): p for p in parts}
    for i, fut in enumerate(as_completed(futures), 1):
        r = fut.result()
        results.append(r)
        if i % 20 == 0:
            print(f"  fetched {i}/{len(parts)}", file=sys.stderr)

results.sort(key=lambda r: r["partId"])
out = Path(__file__).parent / "bboxes.json"
out.write_text(json.dumps(results, indent=2))
print(f"Wrote {len(results)} records to {out}")
errors = [r for r in results if "error" in r]
if errors:
    print(f"ERRORS: {len(errors)}")
    for e in errors[:5]:
        print(f"  {e['partId']} {e['name']}: {e['error']}")
