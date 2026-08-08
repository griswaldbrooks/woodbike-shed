#!/usr/bin/env python3
"""Rename all default-named ('Part NN') parts via the metadata API.

Naming follows the project's section-role convention ('back wall studs',
'right wall headers', ...) using the scout report's §4 classification for the
front/back wall parts, plus the additive members built by build_members.py.
The metadata Name property id is the Onshape standard 57f3fb8efa3416c06701d60d.
"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from onshape import signed_request

DID = "24d3743de768051f7ae10bb3"
WID = "4c0f1b0cf9df2e322f841b94"
EID = "5730975eb353b57bac8d52c4"
NAME_PROP = "57f3fb8efa3416c06701d60d"

# Part-name -> new name (one entry per part; groups listed explicitly)
RENAMES = {}
for n in range(28, 39):
    RENAMES[f"Part {n}"] = "back wall studs"               # 28-38 (27 already done)
RENAMES["Part 46"] = "front wall top plate"
RENAMES["Part 47"] = "front wall bottom plate"
RENAMES["Part 91"] = "front wall double top plate"
for n in (48, 49, 50, 53, 54, 55, 60, 63, 69):
    RENAMES[f"Part {n}"] = "front wall king studs"
for n in (61, 62, 67, 68):
    RENAMES[f"Part {n}"] = "front wall jack studs"
for n in (64, 65, 66, 70, 71, 72):
    RENAMES[f"Part {n}"] = "front wall headers"
for n in (51, 52, 56, 57, 58, 59):
    RENAMES[f"Part {n}"] = "front wall cripple studs"
for n in range(93, 97):
    RENAMES[f"Part {n}"] = "right rake wall studs"
for n in range(97, 101):
    RENAMES[f"Part {n}"] = "left rake wall studs"
RENAMES["Part 101"] = "left rake wall top plate"
for n in range(102, 115):
    RENAMES[f"Part {n}"] = "rafter"


def main():
    s, b = signed_request("GET", f"/api/v6/parts/d/{DID}/w/{WID}/e/{EID}")
    parts = json.loads(b)
    by_name = {p["name"]: p["partId"] for p in parts}

    missing = [k for k in RENAMES if k not in by_name]
    if missing:
        print("!! these parts were not found:", missing)
        sys.exit(1)

    failures = 0
    for old, new in sorted(RENAMES.items(), key=lambda kv: int(kv[0].split()[1])):
        pid = by_name[old]
        qpid = urllib.parse.quote(pid, safe="")  # partIds may contain '+' etc.
        href = f"https://cad.onshape.com/api/v6/metadata/d/{DID}/w/{WID}/e/{EID}/p/{qpid}"
        body = {"items": [{"href": href, "properties": [
            {"href": href + "?cid=5877a03ebe4c21163b49dce0&pid=" + NAME_PROP,
             "propertyId": NAME_PROP, "value": new}]}]}
        s, b = signed_request("POST",
                              f"/api/v6/metadata/d/{DID}/w/{WID}/e/{EID}/p/{qpid}",
                              body=json.dumps(body).encode())
        ok = s == 200 and '"status":"SUCCEEDED"' in b.replace(" ", "")
        print(f"{'ok' if ok else 'FAIL'}  {old:9s} -> {new}")
        if not ok:
            failures += 1
            print(f"   HTTP {s}: {b[:300]}")
    print(f"\n{len(RENAMES) - failures}/{len(RENAMES)} renamed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
