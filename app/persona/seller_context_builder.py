"""Build one seller's context on demand, by GLID, for the VANI persona agent.

The peer's SCRUBBER.py only builds the 100 pre-picked test sellers (data/testset/, made by make_testset.py),
so any other seller means re-scanning ~840 MB of CSVs. This builder:
  1. `index` (one time): loads every offline seller file into one SQLite file, data/index/sellers.sqlite,
     keyed and indexed by GLID.
  2. `build --glid G`: reads that seller's rows from SQLite in milliseconds, fetches the internal APIs
     (cached in data/api_cache/), and reuses SCRUBBER's build_points + render unchanged.
     It then removes PII and writes data/contexts/<glid>.md and <glid>.json.
     If they already exist, it reuses them unless --refresh is given.

PII rule (persona use):
- kept: names (seller, contact, company, competitors), city/district/state/locality, messages and summaries;
- removed: phone numbers, email addresses, pincode, latitude/longitude, street address, and
  GST/PAN/Aadhaar/bank/other ID numbers (flags and years stay).
Output stays in git-ignored data/.

Run (from the repo root; tokens VANI_AK / VANI_USERS_TOKEN are read from .env):
  python app/persona/seller_context_builder.py index
  python app/persona/seller_context_builder.py build --glid 12345678 [--no-api] [--refresh]
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "app", "context"))
import SCRUBBER as S  # noqa: E402  (peer's builder; reused, not edited)
from make_testset import FILES, KEYS  # noqa: E402
from seller_inventory import glid_of, rows  # noqa: E402

DATA = os.path.join(REPO, "data")
DB = os.path.join(DATA, "index", "sellers.sqlite")
OUT = os.path.join(DATA, "contexts")

KEYMAP = {name: "fk_glusr_usr_id" for name in FILES}
KEYMAP.update({k: v for k, v in KEYS.items() if k.startswith(("gc_", "so_"))})

DROP_KEY = re.compile(r"(^|_)(pincode|zip|latitude|longitude|lat|long|add1|add2|address\d?|email|e_mail|mobile|phone|"
                      r"ph_number|ph2_number|ph_mobile|ph_mobile_alt|fax|fax_number|number|patch_number)($|_)", re.I)
KEEP_KEY = re.compile(r"(_flag|_verified|_available|_year|_cnt|_count|_pct|_rate|_status|_type|_id|_hashed)$", re.I)
PHONE = re.compile(r"(?<![\d])(?:\+?91[-\s]?)?[6-9]\d{9}(?![\d])|(?<![\d])0\d{2,4}[-\s]?\d{6,8}(?![\d])|(?<![\d])80\d{8}(?:,\d+)?(?![\d])")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PIN = re.compile(r"(?<![\d])[1-9]\d{5}(?![\d])")


def load_env():
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.rstrip("\n").split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ---------------------------------------------------------------- one-time index
def index():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    tmp = DB + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    con.execute("CREATE TABLE r (source TEXT, glid TEXT, row TEXT)")
    t0 = time.time()
    for name, pattern in FILES.items():
        key, n, batch = KEYMAP[name], 0, []
        for r in rows(pattern):
            g = glid_of(r.get(key))
            if not g:
                continue
            batch.append((name, g, json.dumps(r, ensure_ascii=False)))
            if len(batch) >= 20000:
                con.executemany("INSERT INTO r VALUES (?,?,?)", batch)
                n += len(batch)
                batch = []
        con.executemany("INSERT INTO r VALUES (?,?,?)", batch)
        n += len(batch)
        con.commit()
        print(f"{name:28} {n:9} rows  ({time.time() - t0:.0f} s)", file=sys.stderr)
    con.execute("CREATE INDEX ix_glid ON r (glid)")
    con.commit()
    con.close()
    os.replace(tmp, DB)
    print(f"index ready: {DB}", file=sys.stderr)


def seller_rows(glid):
    if not os.path.exists(DB):
        sys.exit(f"No index at {DB}. Run: python {os.path.relpath(__file__, REPO)} index")
    con = sqlite3.connect(DB)
    files = {}
    for source, row in con.execute("SELECT source, row FROM r WHERE glid = ?", (glid,)):
        files.setdefault(source, []).append(json.loads(row))
    con.close()
    return files


# ---------------------------------------------------------------- PII removal
def scrub_text(s):
    s = S.ID_VALUE.sub("[ID removed]", s)
    s = EMAIL.sub("[email]", s)
    s = PHONE.sub("[phone]", s)
    return s


def scrub(o, key=""):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            ks = str(k)
            if S.ID_KEY.search(ks) and not isinstance(v, (bool, dict, list)) and not KEEP_KEY.search(ks):
                continue
            if DROP_KEY.search(ks) and not KEEP_KEY.search(ks):
                continue
            out[k] = scrub(v, ks)
        return out
    if isinstance(o, list):
        return [scrub(x, key) for x in o]
    if isinstance(o, str):
        return scrub_text(o)
    return o


def scrub_points(P):
    clean = {}
    for pid, (v, src) in P.items():
        if pid == "A05":  # phone numbers and per-number pickup: not used for persona
            continue
        if pid == "B02" and isinstance(v, dict):
            v = {k: x for k, x in v.items() if "locality" in k}
        elif pid == "B02" and isinstance(v, str):
            v = PIN.sub("[pin]", v)
        clean[pid] = (scrub(v), src)
    return clean


# ---------------------------------------------------------------- build
def build(glid, use_api=True, refresh=False):
    glid = glid.strip()
    md, js = os.path.join(OUT, f"{glid}.md"), os.path.join(OUT, f"{glid}.json")
    if not refresh and os.path.exists(md) and os.path.exists(js):
        return md, js, "cached"
    files = seller_rows(glid)
    if not files:
        print(f"warning: GLID {glid} not found in any offline file; building from APIs only", file=sys.stderr)
    meta = {"glid": glid, "stratum": "on-demand", "rich_sources_of_8": "-"}
    api = S.fetch(glid, refresh) if use_api else {}
    P = scrub_points(S.build_points(glid, files, api, meta, datetime.now()))
    os.makedirs(OUT, exist_ok=True)
    text = S.render(glid, meta, P, files, api)
    text = text.replace("Unmasked (PII handling: legal team).",
                        "PII removed for persona use: phones, emails, pincode, lat/long, street address, ID numbers.")
    with open(md, "w", encoding="utf-8") as f:
        f.write(scrub_text(text))
    doc = {"glid": glid, "built_at": datetime.now().isoformat(timespec="seconds"),
           "sources": {k: len(v) for k, v in sorted(files.items())},
           "api_status": {k: r.get("_http") for k, r in sorted(api.items())},
           "points": {k: {"value": v, "source": s} for k, (v, s) in P.items() if k not in S.EXCLUDED}}
    with open(js, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, default=str)
    return md, js, "built"


def main():
    load_env()
    a = argparse.ArgumentParser()
    sub = a.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    b = sub.add_parser("build")
    b.add_argument("--glid", required=True)
    b.add_argument("--no-api", action="store_true")
    b.add_argument("--refresh", action="store_true")
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if p.cmd == "index":
        index()
    else:
        t0 = time.time()
        md, js, how = build(p.glid, not p.no_api, p.refresh)
        print(f"{how}: {md} and {os.path.basename(js)} ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
