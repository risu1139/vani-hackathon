"""Small HTTP helper for the seller-context API probes and fetchers.

Saves every raw response under data/api_cache/ (git-ignored, may hold PII) and prints
only status, latency, top-level keys and error text.
"""
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "api_cache", "probe")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def call(name, url, body=None, timeout=10, form=False, quiet=False):
    data, headers = None, {}
    if body is not None:
        data = urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json"}
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET", headers=headers)
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
            code, text = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code, text = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        if not quiet:
            print(f"{name:46} ERROR {type(e).__name__}: {str(e)[:80]}")
        return None, None
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "".join(c if c.isalnum() else "_" for c in name) + ".txt"), "w", encoding="utf-8") as f:
        f.write(text)
    try:
        obj = json.loads(text)
    except Exception:
        obj = None
    if not quiet:
        if isinstance(obj, dict):
            msg = {k: str(obj[k])[:70] for k in obj
                   if k.lower() in ("message", "err_txt", "status", "status_code", "code", "msg")}
            shape = list(obj)[:10]
        else:
            msg, shape = " ".join(text[:120].split()), type(obj).__name__ if obj is not None else "nonjson"
        print(f"{name:46} HTTP {code} {int((time.time() - t) * 1000):5}ms len={len(text)} {shape} {msg}")
    return code, obj
