#!/usr/bin/env python3
"""Onshape API helper: signed requests using personal API keys.

Loads credentials from ~/.config/onshape/credentials (KEY=VALUE lines).
Usage:
    ./onshape.py GET /api/v6/documents/{did}
    ./onshape.py GET '/api/v6/documents/d/{did}/w/{wid}/elements'
    ./onshape.py POST /api/v6/... '{"json": "body"}'      # inline JSON body
    ./onshape.py POST /api/v6/... @body.json              # JSON body from file
"""
import base64
import datetime
import hashlib
import hmac
import os
import secrets
import sys
import urllib.parse
import urllib.request

HOST = "https://cad.onshape.com"
CREDS_PATH = os.path.expanduser("~/.config/onshape/credentials")


def load_creds():
    creds = {}
    with open(CREDS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            creds[k.strip()] = v.strip()
    return creds["ONSHAPE_ACCESS_KEY"], creds["ONSHAPE_SECRET_KEY"]


def signed_request(method, path_with_query, body=b"", content_type="application/json"):
    access_key, secret_key = load_creds()
    parsed = urllib.parse.urlparse(path_with_query)
    path = parsed.path
    query = parsed.query  # may be empty

    nonce = secrets.token_hex(12)  # 24-char hex, > 16 chars required
    date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    # Onshape signing string: method + nonce + date + content-type + path + query
    # all lowercased, joined by newlines, with trailing newline
    str_to_sign = "\n".join([
        method.lower(),
        nonce.lower(),
        date.lower(),
        content_type.lower(),
        path.lower(),
        query.lower(),
    ]) + "\n"

    sig = base64.b64encode(
        hmac.new(
            secret_key.encode("utf-8"),
            str_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    headers = {
        "Date": date,
        "On-Nonce": nonce,
        "Content-Type": content_type,
        "Accept": "application/json;charset=UTF-8;qs=0.09",
        "Authorization": f"On {access_key}:HmacSHA256:{sig}",
    }

    url = HOST + path_with_query
    req = urllib.request.Request(url, data=body if body else None, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    method, path = sys.argv[1], sys.argv[2]
    body = b""
    if len(sys.argv) > 3:
        arg = sys.argv[3]
        if arg.startswith("@"):
            with open(arg[1:], "rb") as f:
                body = f.read()
        else:
            body = arg.encode("utf-8")
    status, body_text = signed_request(method, path, body=body)
    print(f"HTTP {status}")
    print(body_text)
