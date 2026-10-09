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


# ---------------------------------------------------------------- category value (E09)
DWH = "https://imdwh.intermesh.net/api/go/"
CAT_CACHE = os.path.join(DATA, "api_cache", "category")


def _cat_api(name, body, mcat, refresh):
    """One imdwh category API, cached per MCAT (shared by all sellers in that category). Failures are not cached."""
    path = os.path.join(CAT_CACHE, name, f"{mcat}.json")
    if not refresh and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    code, obj = S.call(f"{name}_{mcat}", DWH + name, body, timeout=25, quiet=True)
    try:
        inner = json.loads(obj["response"]) if isinstance(obj, dict) and isinstance(obj.get("response"), str) else None
    except Exception:
        inner = None
    if code != 200 or inner is None:
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(inner, f, ensure_ascii=False)
    return inner


def category_value(P, refresh=False, top_n=3):
    """Price spread, bulk/retail cut-off and bulk share for the seller's top MCATs.
    Unit prices of listed products, not order values. The boundary value is derived (cut-off x median)."""
    d01 = (P.get("D01") or (None, ""))[0] or {}
    mcats = [m for m in (d01.get("mcats_api") or []) if isinstance(m, dict) and m.get("mid")][:top_n]
    out = []
    for m in mcats:
        mid = str(m["mid"])
        price = _cat_api("mcatpriceapi", {"inmcatid": mid}, mid, refresh) or {}
        retail = _cat_api("mcatetoretail", {"mcat_id": mid}, mid, refresh) or {}
        units = price.get("UNIT_STR") or []
        unit = next((u for u in units if str(u.get("is_recommended")) == "1"), units[0] if units else {})
        rt = next((r for r in retail.get("tov_str") or [] if str(r.get("unit_id")) == str(unit.get("unit_id"))),
                  (retail.get("tov_str") or [{}])[0])
        lt, ge = rt.get("bl_less_than_rt"), rt.get("bl_greater_or_equals_to_rt")
        med, thr = S.num(unit.get("median")), S.num(rt.get("retail_threshold"))
        prd = (price.get("PRD_STR") or [{}])[0]
        out.append({
            "mcat_id": mid, "mcat_name": m.get("mname") or rt.get("mcat_name"), "unit": unit.get("unit_display_name"),
            "listed_products": unit.get("prd_cnt"), "products_all_time": prd.get("prd_all"), "products_last_1y": prd.get("prd_1y"),
            "price_median": med, "price_q1": unit.get("q1"), "price_q3": unit.get("q3"),
            "price_p05": unit.get("percentile_05"), "price_p95": unit.get("percentile_95"),
            "retail_threshold_qty": thr,
            "bl_with_qty_1y": rt.get("bl_count_with_qty"), "bl_bulk_1y": ge, "bl_retail_1y": lt,
            "bulk_share": round(ge / (ge + lt), 3) if isinstance(ge, (int, float)) and isinstance(lt, (int, float)) and ge + lt else None,
            "sellers_buying_bulk_1y": rt.get("unique_sold_greater_or_equals_to_rt"),
            "sellers_buying_retail_1y": rt.get("unique_sold_less_than_rt"),
            "derived_bulk_boundary_value_rs": round(thr * med) if thr and med else None,
            "cities": [c.get("district_name") for c in price.get("CITY_STR") or []][:5],
        })
    return out


# ---------------------------------------------------------------- AOV (E10) via Redash
AOV_CACHE = os.path.join(DATA, "api_cache", "aov")
REDASH_BL_DS = 16       # pg-imblr-prod-live: buy-lead report DB (eto_attribute = last ~3 months)
REDASH_DWH_DS = 8       # im_dwh_rpt (Redshift): dim_glcat_mcat.aov_bucket
NUM_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|thousand|k)?", re.I)
SCALE = {"crore": 1e7, "cr": 1e7, "lakh": 1e5, "lac": 1e5, "thousand": 1e3, "k": 1e3}


def redash(sql, ds, timeout=120):
    """Run one ad-hoc query through Redash (key from ~/.redash_env). Returns rows, or None on failure."""
    import urllib.request
    env = {}
    path = os.path.join(os.path.expanduser("~"), ".redash_env")
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env[k] = v.strip().strip('"\'')
    base, hdr = env["REDASH_URL"].rstrip("/"), {"Authorization": f"Key {env['REDASH_API_KEY']}", "Content-Type": "application/json"}

    def req(url, body=None):
        r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=hdr,
                                   method="POST" if body else "GET")
        return json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    try:
        job = req(f"{base}/api/query_results", {"data_source_id": ds, "max_age": 0, "query": sql}).get("job", {})
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(2)
            j = req(f"{base}/api/jobs/{job['id']}")["job"]
            if j["status"] == 3:
                return req(f"{base}/api/query_results/{j['query_result_id']}")["query_result"]["data"]["rows"]
            if j["status"] == 4:
                print(f"redash ds{ds} failed: {str(j.get('error'))[:120]}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"redash ds{ds} error: {str(e)[:120]}", file=sys.stderr)
    return None


def pov_value(text):
    """'Rs. 14,000 - 16,000' -> 15000; 'Rs. Upto 1,000' -> 500; 'Rs. 5 Lakh - 10 Lakh' -> 750000; 'Rs. 200' -> 200."""
    t = (text or "").lower().replace(",", "")
    nums = [(float(n), (u or "").lower()) for n, u in NUM_UNIT.findall(t)]
    if not nums:
        return None
    units = [u for _, u in nums if u]
    vals = [n * SCALE.get(u or (units[-1] if units and n < 1000 else ""), 1) for n, u in nums[:2]]
    if "upto" in t or "up to" in t or "below" in t or "less than" in t:
        return vals[0] / 2
    return sum(vals) / len(vals)


def value_stats(rows):
    """rows of {value_text, n} -> median / p75 / max of the numeric midpoints, plus the commonest ranges."""
    vals = []
    for r in rows:
        v = pov_value(r.get("v"))
        if v is not None:
            vals += [v] * int(r.get("n") or 1)
    if not vals:
        return None
    vals.sort()
    q = lambda p: vals[min(len(vals) - 1, int(p * len(vals)))]
    top = sorted(rows, key=lambda r: -int(r.get("n") or 0))[:3]
    return {"n_valued": len(vals), "median_rs": round(q(0.5)), "p75_rs": round(q(0.75)), "max_rs": round(vals[-1]),
            "mean_rs": round(sum(vals) / len(vals)), "common_ranges": [r.get("v") for r in top]}


def _cached(path, fn, refresh):
    if not refresh and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    out = fn()
    if out is not None:  # never cache a failure
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    return out


def seller_aov(glid, files, refresh=False):
    """AOV of the buy leads this seller bought: 'Probable Order Value' attribute per lead (buy-lead report DB)."""
    ids = sorted({str(r.get("buylead_id") or "").split(".")[0] for r in files.get("gc_buyleads_bought", [])} - {""})
    if not ids:
        return {"n_bought": 0, "note": "no bought-lead ids in our files (only Global Context sellers have them)"}

    def q():
        rows = redash("select fk_im_spec_options_desc v, count(*) n from eto_attribute where fk_im_spec_master_desc="
                      f"'Probable Order Value' and fk_eto_ofr_display_id in ({','.join(i for i in ids if i.isdigit())}) group by 1",
                      REDASH_BL_DS)
        return None if rows is None else {"n_bought": len(ids), "stats": value_stats(rows)}
    return _cached(os.path.join(AOV_CACHE, "seller", f"{glid}.json"), q, refresh)


def mcat_aov(mcat_ids, refresh=False, days=30):
    """Category AOV per MCAT: buy-lead 'Probable Order Value' over the last `days` days, plus the DWH aov_bucket if reachable."""
    out = {}
    for mid in [m for m in mcat_ids if str(m).isdigit()]:
        def q(mid=mid):
            rows = redash("select fk_im_spec_options_desc v, count(*) n from eto_attribute where date(eto_attribute_mod_date) >= "
                          f"current_date - {days} and eto_attribute_mcat_id={mid} and fk_im_spec_master_desc='Probable Order Value' "
                          "group by 1", REDASH_BL_DS, timeout=150)
            if rows is None:
                return None
            b = redash(f"select aov_bucket, aov_bucket_start, aov_bucket_end from im_dwh_rpt.dim_glcat_mcat where glcat_mcat_id={mid}",
                       REDASH_DWH_DS, timeout=40)
            return {"window_days": days, "stats": value_stats(rows), "dwh_aov_bucket": (b or [None])[0]}
        out[str(mid)] = _cached(os.path.join(AOV_CACHE, "mcat", f"{mid}.json"), q, refresh)
    return out


def render_aov(seller, mcats, cat_rows):
    names = {r["mcat_id"]: r["mcat_name"] for r in cat_rows}
    rs = lambda s: (f"median Rs {s['median_rs']:,}, top quarter from Rs {s['p75_rs']:,}, highest Rs {s['max_rs']:,} "
                    f"({s['n_valued']} leads with a value; common: {', '.join(s['common_ranges'])})") if s else "_no values_"
    lines = ["## E10. Average order value (seller and category)", "",
             "*Source:* buy-lead 'Probable Order Value' (pg-imblr eto_attribute, via Redash). Each range is turned into its "
             "midpoint. Seller = leads this seller bought; category = all buy leads in that MCAT in the window.", ""]
    s = seller or {}
    lines.append(f"- **Seller AOV** ({s.get('n_bought', 0)} leads bought): "
                 + (rs(s.get("stats")) if s.get("n_bought") else s.get("note", "_no data_")))
    for mid, m in (mcats or {}).items():
        if not m:
            lines.append(f"- **{names.get(mid, mid)}** (MCAT {mid}): _query failed_")
            continue
        b = m.get("dwh_aov_bucket")
        lines.append(f"- **Category AOV, {names.get(mid, mid)}** (MCAT {mid}, last {m['window_days']} days): {rs(m.get('stats'))}"
                     + (f"; DWH bucket {b.get('aov_bucket')} (Rs {b.get('aov_bucket_start')}–{b.get('aov_bucket_end')})" if b else ""))
    return "\n".join(lines + [""])


# ---------------------------------------------------------------- peer statistic (E11), all ladder rungs
BANDS = ["0 - 40 L", "40 L - 1.5 Cr", "1.5 - 5 Cr", "5 - 25 Cr", "25 - 100 Cr", "100 - 500 Cr", "> 500 Cr"]
MIN_PEERS = 5


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    return None if not xs else xs[len(xs) // 2]


def peer_stat(glid, cat_rows, refresh=False, days=30):
    """Same-category, same-size peers at every rung of the fallback ladder, precomputed so the agent can pick offline.
    Peers = sellers mapped to the seller's main MCAT (pg-imblr glusr_usr_mcat_prd_count) with a GST turnover band.
    Outcome = buy leads bought in the last `days` days (weberp.eto_lead_pur_hist). Peer AOV = 'Probable Order Value'
    of the leads they bought in this MCAT. The GST number column is never selected."""
    mcats = [r["mcat_id"] for r in cat_rows if str(r.get("mcat_id", "")).isdigit()]
    if not mcats:
        return {"status": "no_mcat"}

    def q():
        mlist = ",".join(mcats)
        own = redash(f"""select coalesce(eto_ofr_prime_mcat_id, user_matched_mcat_id, search_top_mcat_id) m, count(*) n
            from weberp.eto_lead_pur_hist where fk_glusr_usr_id={glid} and eto_pur_date >= current_date - 90 group by 1 order by 2 desc""",
                     REDASH_BL_DS)
        if own is None:
            return None
        bought = [str(int(r["m"])) for r in own if r.get("m") and str(int(r["m"])) in mcats]
        main = bought[0] if bought else mcats[0]
        me = redash(f"""select u.fk_gl_city_id c, u.fk_gl_state_id s, gd.glusr_gst_annual_turnover b
            from glusr_usr u left join glusr_gst_details gd on gd.fk_glusr_usr_id = u.glusr_usr_id where u.glusr_usr_id={glid}""",
                    REDASH_BL_DS) or [{}]
        me = me[0]
        band = me.get("b")
        if band not in BANDS:
            return {"status": "no_band", "main_mcat": main, "band": band}
        bi = BANDS.index(band)
        near = [b for b in BANDS[max(0, bi - 1):bi + 2] if not (bi == 0 and BANDS.index(b) > 1)]
        blist = ",".join(f"'{b}'" for b in near)
        rows = redash(f"""with peers as (select distinct fk_glusr_usr_id g from glusr_usr_mcat_prd_count where fk_glcat_mcat_id={main}
                and fk_glusr_usr_id <> {glid}),
            pinfo as (select p.g, gd.glusr_gst_annual_turnover b, u.fk_gl_city_id c, u.fk_gl_state_id s from peers p
                join glusr_gst_details gd on gd.fk_glusr_usr_id = p.g join glusr_usr u on u.glusr_usr_id = p.g
                where gd.glusr_gst_annual_turnover in ({blist})),
            pur as (select h.fk_glusr_usr_id g, count(*) n_any,
                sum(case when coalesce(h.eto_ofr_prime_mcat_id, h.user_matched_mcat_id, h.search_top_mcat_id) = {main} then 1 else 0 end) n_mcat
                from weberp.eto_lead_pur_hist h where h.fk_glusr_usr_id in (select g from pinfo) and h.eto_pur_date >= current_date - {days} group by 1)
            select pi.b, pi.c, pi.s, coalesce(pu.n_any, 0) n_any, coalesce(pu.n_mcat, 0) n_mcat, pi.g from pinfo pi left join pur pu on pu.g = pi.g""",
                      REDASH_BL_DS, timeout=180)
        if rows is None:
            return None
        povs = redash(f"""select h.fk_glusr_usr_id g, a.fk_im_spec_options_desc v from weberp.eto_lead_pur_hist h
            join eto_attribute a on a.fk_eto_ofr_display_id = h.fk_eto_ofr_id and a.fk_im_spec_master_desc = 'Probable Order Value'
            where h.fk_glusr_usr_id in (select fk_glusr_usr_id from glusr_usr_mcat_prd_count where fk_glcat_mcat_id={main})
            and coalesce(h.eto_ofr_prime_mcat_id, h.user_matched_mcat_id, h.search_top_mcat_id) = {main}
            and h.eto_pur_date >= current_date - {days}""", REDASH_BL_DS, timeout=180) or []
        pov_by = {}
        for r in povs:
            v = pov_value(r.get("v"))
            if v is not None:
                pov_by.setdefault(str(r["g"]), []).append(v)
        own_n = {"any": sum(int(r["n"]) for r in own), "main_mcat": sum(int(r["n"]) for r in own if r.get("m") and str(int(r["m"])) == main)}
        rungs = []
        for i, (geo, same_band) in enumerate([("city", True), ("state", True), ("india", True), ("state", False), ("india", False)], 1):
            sel = [r for r in rows if (r["b"] == band if same_band else True)
                   and (geo == "india" or (geo == "city" and r["c"] == me.get("c")) or (geo == "state" and r["s"] == me.get("s")))]
            buyers = [r for r in sel if int(r["n_mcat"]) > 0]
            aovs = [x for r in buyers for x in pov_by.get(str(r["g"]), [])]
            rungs.append({
                "rung": i, "geo": geo, "band_scope": "same band" if same_band else "band ±1 (" + ", ".join(near) + ")",
                "peers_mapped": len(sel), "peers_bought_in_mcat": len(buyers),
                "share_bought": round(len(buyers) / len(sel), 3) if sel else None,
                "leads_bought_total": sum(int(r["n_mcat"]) for r in buyers),
                "median_leads_per_buyer": _median([int(r["n_mcat"]) for r in buyers]),
                "peer_aov_median_rs": round(_median(aovs)) if aovs else None, "peer_valued_leads": len(aovs),
                "allowed": len(buyers) >= MIN_PEERS})
        first = next((r for r in rungs if r["allowed"]), None)
        return {"status": "ok", "window_days": days, "main_mcat": main, "band": band, "city_id": me.get("c"), "state_id": me.get("s"),
                "seller_leads_bought": {"any_mcat": own_n["any"], "main_mcat": own_n["main_mcat"], "window_days": 90},
                "first_allowed_rung": first["rung"] if first else None, "rungs": rungs,
                "note": "Peer counts undercount: about 24% of purchases have no MCAT. Never claim what peers earned or closed."}
    return _cached(os.path.join(AOV_CACHE, "peer", f"{glid}.json"), q, refresh)


def render_peer(p):
    lines = ["## E11. Peer statistic (same MCAT, same turnover band; fallback ladder)", "",
             "*Source:* pg-imblr glusr_usr_mcat_prd_count + glusr_gst_details + weberp.eto_lead_pur_hist + eto_attribute, via Redash. "
             f"A rung is allowed only with at least {MIN_PEERS} peers who bought leads in the MCAT. Use the first allowed rung and "
             "name its geography honestly. Never compare a small seller with a much bigger band.", ""]
    if not p or p.get("status") != "ok":
        return "\n".join(lines + [f"_not available: {(p or {}).get('status', 'query failed')}_", ""])
    s = p["seller_leads_bought"]
    lines.append(f"- Seller: band {p['band']}, main MCAT {p['main_mcat']}; bought {s['main_mcat']} leads in this MCAT "
                 f"({s['any_mcat']} in all MCATs) in the last {s['window_days']} days. First allowed rung: {p['first_allowed_rung']}.")
    lines.append("")
    lines.append("| Rung | Area | Band | Peers mapped | Bought in MCAT | Share | Leads total | Median per buyer | Peer AOV median | Allowed |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in p["rungs"]:
        lines.append(f"| {r['rung']} | {r['geo']} | {r['band_scope']} | {r['peers_mapped']} | {r['peers_bought_in_mcat']} | {r['share_bought']} | "
                     f"{r['leads_bought_total']} | {r['median_leads_per_buyer']} | {r['peer_aov_median_rs']} | {'yes' if r['allowed'] else 'no'} |")
    return "\n".join(lines + ["", p.get("note", ""), ""])


# ---------------------------------------------------------------- showcase-lead candidates (E12)
def showcase_leads(cat_rows, peer, seller_aov_stats, refresh=False, keep=12):
    """Live and recent expired buy leads in the seller's top MCATs, with order value / quantity, scored for fit.
    Only product, quantity, value, region and status are kept: never the buyer's name, company or contact."""
    mcats = [r["mcat_id"] for r in cat_rows if str(r.get("mcat_id", "")).isdigit()]
    if not mcats:
        return []
    mlist = ",".join(mcats)
    attr = lambda col, cond: (f"(select a.fk_im_spec_options_desc from eto_attribute a where a.fk_eto_ofr_display_id = o.{col} "
                              f"and a.fk_im_spec_master_desc {cond} limit 1)")

    def q(table, status, extra, col="eto_ofr_display_id"):
        return redash(f"""select '{status}' status, o.{col} id, left(o.eto_ofr_title, 90) title, o.fk_glcat_mcat_id mcat,
            ci.gl_city_name city, st.gl_state_name state, ci.fk_gl_state_id state_id, o.eto_ofr_city_id city_id,
            date(o.eto_ofr_approv_date_orig) posted, {attr(col, "= 'Probable Order Value'")} pov,
            {attr(col, "ilike 'quantity'")} qty, {attr(col, "ilike 'quantity unit'")} unit
            from {table} o left join gl_city ci on ci.gl_city_id = o.eto_ofr_city_id left join gl_state st on st.gl_state_id = ci.fk_gl_state_id
            where o.fk_glcat_mcat_id in ({mlist}) {extra} order by o.eto_ofr_approv_date_orig desc limit 120""", REDASH_BL_DS, timeout=150)

    def fetch():
        live = q("eto_ofr", "live", "and o.eto_ofr_approv = 'A'")
        exp = q("eto_ofr_expired", "expired", "and date(o.eto_ofr_approv_date_orig) >= current_date - 30")
        if live is None and exp is None:
            return None
        return (live or []) + (exp or [])
    rows = _cached(os.path.join(AOV_CACHE, "leads", f"{'_'.join(mcats)}.json"), fetch, refresh) or []
    ref = (seller_aov_stats or {}).get("median_rs")
    import math
    out = []
    for r in rows:
        v = pov_value(r.get("pov"))
        if v is None and not r.get("qty"):
            continue
        age = None
        try:
            age = (datetime.now().date() - datetime.strptime(str(r.get("posted"))[:10], "%Y-%m-%d").date()).days
        except Exception:
            pass
        fit = 0.0
        if v and ref:
            fit += max(0.0, 2 - abs(math.log10(v / (ref * 1.2))))      # near (a little above) the seller's AOV
        elif v:
            fit += 1.0
        same_city = peer and r.get("city_id") is not None and r.get("city_id") == peer.get("city_id")
        same_state = peer and r.get("state_id") is not None and r.get("state_id") == peer.get("state_id")
        fit += 2 if same_city else 1 if same_state else 0
        fit += 1 if r["status"] == "live" else 0
        fit += max(0, 1 - (age or 30) / 30)
        out.append({"status": r["status"], "lead_id": r.get("id"), "product": r.get("title"), "mcat": r.get("mcat"),
                    "quantity": r.get("qty"), "unit": r.get("unit"), "order_value_text": r.get("pov"),
                    "order_value_rs": round(v) if v else None, "buyer_city": r.get("city"), "buyer_state": r.get("state"),
                    "posted": str(r.get("posted"))[:10], "days_ago": age, "same_city": bool(same_city), "same_state": bool(same_state),
                    "fit_score": round(fit, 2)})
    out.sort(key=lambda x: -x["fit_score"])
    return out[:keep]


def render_showcase(leads, ref):
    lines = ["## E12. Showcase buy-lead candidates (best first)", "",
             "*Source:* pg-imblr eto_ofr (live) + eto_ofr_expired (last 30 days) + eto_attribute, via Redash. "
             f"fit_score rewards order value near (a little above) the seller's AOV (ref Rs {ref}), the same city/state, live, and new. "
             "Say only product, quantity, value, region and status. Never the buyer's name, company or contact.", ""]
    if not leads:
        return "\n".join(lines + ["_no candidate with an order value or a quantity_", ""])
    lines += ["| # | Status | Product | Qty | Order value | Buyer region | Posted | Fit |", "|---|---|---|---|---|---|---|---|"]
    for i, l in enumerate(leads, 1):
        q = f"{l['quantity'] or ''} {l['unit'] or ''}".strip()
        lines.append(f"| {i} | {l['status']} | {l['product']} | {q} | {l['order_value_text'] or ''} | "
                     f"{l['buyer_city'] or ''}, {l['buyer_state'] or ''} | {l['posted']} ({l['days_ago']} d) | {l['fit_score']} |")
    return "\n".join(lines + [""])


# ---------------------------------------------------------------- old VANI call history (G)
RECENT_DAYS, MAX_DAYS = 30, 90
SIG = {
    "rushed": re.compile(r"busy|call (me )?later|callback|call back|in a meeting|driving|baad me|abhi nahi|बिज़ी|बिजी|बाद में", re.I),
    "frustrated": re.compile(r"irritat|annoy|angry|frustrat|harass|rude|don.?t call|stop call|kitni baar|परेशान|बार बार", re.I),
    "confused": re.compile(r"confus|did not understand|didn.?t understand|samajh nahi|समझ नहीं", re.I),
    "asked_if_bot": re.compile(r"\bbot\b|robot|recorded|\bAI\b|machine|insaan|इंसान|रोबोट", re.I),
    "grievance": re.compile(r"complain|grievance|no (response|enquir|inquir|lead)|not getting|fraud|cheat|refund|bad experience|"
                            r"poor quality|irrelevant|wasted|already paid|शिकायत", re.I),
}


def _j(s):
    try:
        return json.loads(s) if isinstance(s, str) else (s or {})
    except Exception:
        return {}


def call_history(files, now):
    """Old VANI bot calls, ALL of them, newest first (user, 2026-10-10: give the agent the full information).
    Per call: full summary, every evaluator agent's output, and the turn-by-turn transcript when one exists.
    `relevance` (recent <=30 d, older <=90 d, old) is a label for the agent to weigh, not a filter.
    Signals are counts of text matches per call, dated so B2 can decay them."""
    calls = files.get("ps07_bot_calls", [])
    ev = {}
    for r in files.get("ps07_evaluator", []):
        ev.setdefault(r.get("attempt_id"), {})[r.get("eval_agent")] = _j(r.get("agent_output"))
    turns = {}
    for t in files.get("ps07_call_turns", []):
        turns.setdefault(t.get("attempt_id"), []).append(t)
    out = {"n_calls_all_history": len(calls), "outcome_counts_all_history": {}, "objection_categories_all_history": {},
           "meetings_fixed_all_history": 0, "calls": [], "older_calls_ignored": 0}
    for c in calls:
        o = c.get("disposition_label") or "unknown"
        out["outcome_counts_all_history"][o] = out["outcome_counts_all_history"].get(o, 0) + 1
        out["meetings_fixed_all_history"] += str(c.get("meeting_fixed")) == "1"
        for ob in (ev.get(c.get("attempt_id"), {}).get("objections", {}) or {}).get("objection_analysis", []) or []:
            k = ob.get("category") or "?"
            out["objection_categories_all_history"][k] = out["objection_categories_all_history"].get(k, 0) + 1
    for c in sorted(calls, key=lambda c: c.get("call_start_time") or "", reverse=True):
        d = S.dt(c.get("call_start_time"))
        days = (now - d).days if d else None
        e = ev.get(c.get("attempt_id"), {})
        objs = [{"category": ob.get("category"), "reason": "; ".join(ob.get("reasons") or [])[:200],
                 "quote": scrub_text("; ".join(ob.get("evidence_quotes") or [])[:200])}
                for ob in (e.get("objections") or {}).get("objection_analysis", []) or []]
        disp = e.get("disposition") or {}
        se = e.get("se_contact") or {}
        summary = scrub_text(c.get("lead_call_summary") or "")
        text = " ".join([summary] + [o["reason"] + " " + o["quote"] for o in objs] + [str(se.get("seller_exact_quote") or "")])
        tr = sorted(turns.get(c.get("attempt_id"), []), key=lambda t: int(S.num(t.get("turn_no"), 0) or 0))
        out["calls"].append({
            "date": (c.get("call_start_time") or "")[:16], "days_ago": days,
            "relevance": "unknown" if days is None else "recent" if days <= RECENT_DAYS else "older" if days <= MAX_DAYS else "old",
            "outcome": c.get("disposition_label"), "sub_disposition": disp.get("sub_disposition"),
            "disposition_reason": scrub_text(str(disp.get("reason") or "")) or None, "followup_when": disp.get("followup_when"),
            "duration_sec": S.num(c.get("lead_call_duration")), "bot_version": c.get("lead_bot_version"),
            "trigger_bucket": c.get("redis_bucket"), "attempt_count": c.get("call_attempt_count"),
            "summary": summary,
            "objections": objs, "exec_contact": se.get("category"),
            "exec_contact_quote": scrub_text(str(se.get("seller_exact_quote") or "")) or None,
            "who_ended": (e.get("execdrop") or {}).get("who_ended_call"),
            "evaluators": {k: scrub(v) for k, v in e.items()},
            "transcript": [{"speaker": t.get("speaker"), "t": S.num(t.get("start_sec")), "text": scrub_text(t.get("text") or "")} for t in tr],
            "signals": {k: len(p.findall(text + " " + " ".join(t.get("text") or "" for t in tr if t.get("speaker") != "bot")))
                        for k, p in SIG.items()},
        })
    return out


def render_history(h):
    lines = ["## G. Past VANI calls (built by us from PS07 bot calls + evaluator)", "",
             f"*All history:* {h['n_calls_all_history']} calls; outcomes {h['outcome_counts_all_history']}; "
             f"meetings fixed {h['meetings_fixed_all_history']}; objection categories {h['objection_categories_all_history']}. "
             f"Every call is listed, newest first; weigh recent ones more.", ""]
    if not h["calls"]:
        return "\n".join(lines + ["_no past VANI calls (cold seller)_", ""])
    for c in h["calls"]:
        sig = ", ".join(f"{k} {v}" for k, v in c["signals"].items() if v) or "none"
        lines.append(f"### {c['date']} ({c['days_ago']} days ago, {c['relevance']}): {c['outcome']}"
                     + (f" / {c['sub_disposition']}" if c.get("sub_disposition") else "")
                     + f" · {c.get('duration_sec')} s · bot {c.get('bot_version')} · trigger {c.get('trigger_bucket')}")
        lines.append(f"- Summary: {c['summary']}")
        if c.get("disposition_reason"):
            lines.append(f"- Outcome reason: {c['disposition_reason']}" + (f" (follow-up: {c['followup_when']})" if c.get("followup_when") else ""))
        for o in c["objections"]:
            lines.append(f"- Objection: **{o['category']}**: {o['reason']}" + (f" (\"{o['quote']}\")" if o["quote"] else ""))
        if c.get("exec_contact"):
            lines.append(f"- Executive contact: {c['exec_contact']}" + (f" (\"{c['exec_contact_quote']}\")" if c.get("exec_contact_quote") else ""))
        lines.append(f"- Ended by: {c.get('who_ended') or '?'}; signals: {sig}")
        for k, v in (c.get("evaluators") or {}).items():
            if k in ("objections", "se_contact", "disposition"):
                continue
            lines.append(f"- Evaluator `{k}`: {json.dumps(v, ensure_ascii=False)[:600]}")
        if c.get("transcript"):
            lines.append("- Transcript:")
            lines += [f"  - {t['speaker']}: {t['text']}" for t in c["transcript"]]
        lines.append("")
    return "\n".join(lines)


def render_category(rows):
    lines = ["## E09. Category value (unit price spread, bulk share)", "",
             "*Source:* imdwh mcatpriceapi + mcatetoretail, per top MCAT. Unit prices of listed products (not order value); "
             "bulk = buy leads at or above the retail quantity cut-off; boundary value = cut-off x median (derived).", ""]
    if not rows:
        return "\n".join(lines + ["_no data_", ""])
    for r in rows:
        lines += [f"### {r['mcat_name']} (MCAT {r['mcat_id']}, per {r['unit']})",
                  f"- Listed price: median Rs {r['price_median']}, middle half Rs {r['price_q1']}–{r['price_q3']}, "
                  f"5th–95th percentile Rs {r['price_p05']}–{r['price_p95']} ({r['listed_products']} products)",
                  f"- Bulk cut-off: {r['retail_threshold_qty']} {r['unit']}; last year {r['bl_bulk_1y']} of "
                  f"{(r['bl_bulk_1y'] or 0) + (r['bl_retail_1y'] or 0)} buy leads were bulk ({r['bulk_share']}); "
                  f"{r['sellers_buying_bulk_1y']} sellers bought bulk leads, {r['sellers_buying_retail_1y']} bought retail",
                  f"- Derived bulk boundary value: about Rs {r['derived_bulk_boundary_value_rs']}", ""]
    return "\n".join(lines)


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
    cat = category_value(P, refresh) if use_api else []
    P["E09"] = (cat, "imdwh mcatpriceapi + mcatetoretail (top MCATs)")
    s_aov = seller_aov(glid, files, refresh) if use_api else None
    m_aov = mcat_aov([r["mcat_id"] for r in cat], refresh) if use_api else {}
    P["E10"] = ({"seller": s_aov, "mcats": m_aov}, "buy-lead Probable Order Value via Redash (pg-imblr), DWH aov_bucket")
    os.makedirs(OUT, exist_ok=True)
    text = S.render(glid, meta, P, files, api)
    peer = peer_stat(glid, cat, refresh) if use_api else None
    leads = showcase_leads(cat, peer, (s_aov or {}).get("stats"), refresh) if use_api else []
    P["E11"] = (peer, "pg-imblr peer statistic, all ladder rungs (Redash)")
    P["E12"] = (leads, "pg-imblr live + expired buy leads with order value (Redash)")
    ref = ((s_aov or {}).get("stats") or {}).get("median_rs")
    text = text.replace("\n## F. ", "\n" + render_category(cat) + "\n" + render_aov(s_aov, m_aov, cat) + "\n" + render_peer(peer)
                        + "\n" + render_showcase(leads, ref) + "\n## F. ", 1)
    hist = call_history(files, datetime.now())
    P["G00"] = (hist, "ps07_bot_calls + ps07_evaluator (rebuilt by the persona builder)")
    text = text.replace("\n## H. ", "\n" + render_history(hist) + "\n## H. ", 1) if "\n## H. " in text else text + "\n" + render_history(hist)
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
