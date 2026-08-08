#!/usr/bin/env python3
"""Decode qCompressed query strings from the feature list dump.

The feature list (featurelist_dump.json, written by the diagnosis step) stores
each query as query=qCompressed(1.0,"...",id); — either a readable $-tagged
format ("%B5$QueryM5Sa$...") or zlib+base64 ("&694$eJy..."). This script
decodes all queries for a feature-index range and prints what each feature
references (operationIds, sketchEntityIds, deterministicIds).
"""
import base64
import json
import re
import sys
import zlib
from pathlib import Path

DUMP = Path(__file__).parent / "featurelist_dump.json"


def decode_qcomp(s):
    """Decode the payload of qCompressed(1.0,"PAYLOAD",id)."""
    m = re.match(r'qCompressed\(1\.0,"(.*)",id\)', s, re.S)
    if not m:
        return s
    payload = m.group(1)
    # readable tagged format: %B5$QueryM5Sa$entityTypeBa$EntityType...
    if payload.startswith("%"):
        payload = payload.split("$", 2)[-1]
        return payload
    # zlib format: &694$eJy...
    if payload.startswith("&"):
        b64 = payload.split("$", 1)[1]
        try:
            return zlib.decompress(base64.b64decode(b64)).decode("utf-8", "replace")
        except Exception as e:
            return f"<decode error: {e}>"
    return payload


def walk_queries(obj, out):
    if isinstance(obj, dict):
        if "queryString" in obj and obj["queryString"]:
            out.append((obj.get("parameterId", "?"), obj["queryString"],
                        obj.get("deterministicIds", [])))
        for v in obj.values():
            walk_queries(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_queries(v, out)


def main():
    data = json.load(open(DUMP))
    feats = data["features"]
    lo, hi = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else int(sys.argv[1])
    for i in range(lo, hi + 1):
        f = feats[i]
        qs = []
        walk_queries(f.get("parameters", []), qs)
        print(f"=== [{i}] {f.get('featureType')} {f.get('featureId')} {f.get('name')!r}")
        for pid, qs_str, det in qs:
            qm = re.search(r"query\s*=\s*(.*);?\s*$", qs_str, re.S)
            body = qm.group(1) if qm else qs_str
            dec = decode_qcomp(body)
            print(f"  param={pid} det={det}")
            print(f"    {dec[:600]}")
        print()


if __name__ == "__main__":
    main()
