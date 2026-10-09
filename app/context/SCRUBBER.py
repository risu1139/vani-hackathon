"""SCRUBBER: build one seller-context Markdown file per GLID for the VANI persona agent.

Reads the 100-GLID test set (data/testset/*.csv, made by make_testset.py) and calls the
internal APIs listed as WORKS in extraction_map.ENDPOINTS (production hosts only).
Writes data/contexts/<glid>.md with:
  every catalogue data point A01-K04 (value + source), in persona order.
This .md is the agent's seller-context source for the Sarvam call. Raw rows and raw API
responses stay in data/testset/ and data/api_cache/ (not in the .md).
No masking: PII handling is owned by the legal team. Output lives in git-ignored data/.

Secrets come from env vars only, never written to disk:
  VANI_AK            employee AK (JWT) for users SOA
  VANI_USERS_TOKEN   users SOA service token
  VANI_USERS_MODID   users SOA modid (default GLADMIN)

Run:
  python app/context/SCRUBBER.py --all                 # all GLIDs in data/testset/glids.csv
  python app/context/SCRUBBER.py --glid 12345678       # one seller
  options: --no-api (files only)  --refresh (ignore API cache)  --workers 8
"""
import argparse
import ast
import csv
import glob
import json
import os
import re
import statistics
import sys
import urllib.parse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from extraction_map import DATA_POINTS, ENDPOINTS  # noqa: E402
from http_util import call  # noqa: E402

csv.field_size_limit(10**9)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
TESTSET = os.path.join(ROOT, "testset")
CACHE = os.path.join(ROOT, "api_cache")
OUT = os.path.join(ROOT, "contexts")
NA = {"", "na", "none", "null", "nan", "n/a", "[]", "{}"}

LABELS = {
    "A01": "Seller GLID", "A02": "Company name", "A03": "Contact person name", "A04": "Contact designation",
    "A05": "Numbers on the account (type, office-hours status, pickup)", "A06": "Past pickup role (DM / family / staff / wrong number)",
    "A07": "Gender / salutation", "B01": "City, district, state", "B02": "Pincode, locality, lat/long",
    "B03": "Languages spoken on real calls", "B04": "Seller's script / Hinglish mix on VANI calls", "B05": "Preferred language id",
    "C01": "Business type", "C02": "Annual turnover", "C03": "Nature of business", "C04": "Business vintage",
    "C05": "Customer type / plan / paid", "C06": "Listing status, KYC flags", "C07": "Employees, year established", "C08": "Business profile content (about us, infrastructure, quality, awards …)",
    "D01": "Top categories", "D02": "Number of categories", "D03": "Categories by rank, negative, D-rank",
    "D04": "Product count and recent changes", "D05": "Product list", "D06": "Catalogue quality and gaps",
    "D07": "Active / approved / deactivated products", "E01": "Enquiries received", "E02": "Latest enquiries",
    "E03": "Responsiveness", "E04": "Buyleads bought", "E05": "BL credits and lapsed credits", "E06": "BL consumption speed",
    "E07": "BL not-interested reasons", "E08": "Local competition", "F01": "Buyer (PNS) calls received / answered",
    "F02": "Buyer-call talk time", "F03": "Pickup ratio and callbacks", "F04": "Best time to call",
    "F05": "Unanswered VANI attempts", "F06": "Promised callback", "F07": "Do-not-call / office-hours setting",
    "F08": "Last seen on IndiaMART", "G01": "VANI call volume", "G02": "VANI outcome history", "G03": "Last VANI call",
    "G04": "Past objections and questions", "G05": "Frustration / bot question / DNC / already-with-executive",
    "G06": "Memory facts (regex baseline)", "G07": "Speech style", "G08": "How past calls ended",
    "G09": "Bot versions and call triggers heard", "G10": "Recordings", "G11": "Per-call signal rows (dated)", "H01": "Executive calls",
    "H02": "Account managers", "H03": "Meetings", "I01": "Complaints", "I02": "Renewal / payment", "I03": "Churn / risk",
    "I04": "Ratings", "J01": "WhatsApp delivery and reads", "J02": "WhatsApp chatbot conversations",
    "J03": "Buyer-call extractions", "K01": "Call trigger", "K02": "Attempt number", "K03": "Local time / season",
    "K04": "Dialled number type",
}
GROUPS = [("A", "Identity and callee"), ("B", "Location and language"), ("C", "Business profile"),
          ("D", "Categories and products"), ("E", "Buyer demand and buyleads"), ("F", "Phone behaviour and timing"),
          ("H", "Human relationship"), ("I", "Account health and risk"),
          ("J", "Other channels"), ("K", "This call's context")]


# ---------------------------------------------------------------- helpers
def blank(v):
    return v is None or (isinstance(v, str) and v.strip().lower() in NA) or (isinstance(v, (list, dict)) and not v)


def num(v, default=None):
    try:
        return float(str(v).strip())
    except Exception:
        return default


def dt(v):
    s = (v or "").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%y %H:%M"):
        try:
            return datetime.strptime(s if fmt != "%Y-%m-%d" else s[:10], fmt)
        except Exception:
            continue
    return None


def decode(o):
    """Recursively parse JSON that APIs return inside strings."""
    if isinstance(o, str) and o.strip()[:1] in "[{":
        try:
            return decode(json.loads(o))
        except Exception:
            return o
    if isinstance(o, dict):
        return {k: decode(v) for k, v in o.items()}
    if isinstance(o, list):
        return [decode(x) for x in o]
    return o


def latest(rows, key="year_month"):
    rows = [r for r in rows or [] if isinstance(r, dict)]
    return max(rows, key=lambda r: str(r.get(key) or f"{r.get('data_year', '')}{str(r.get('attr_month_number', r.get('month_number', ''))).zfill(2)}"),
               default={})


def pick(d, keys):
    return {k: d.get(k) for k in keys if isinstance(d, dict) and not blank(d.get(k))}


def short(v, n=400):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + " …"


# ---------------------------------------------------------------- file data
def key_col(fields):
    for k in ("fk_glusr_usr_id", "seller_glid", "glid"):
        if k in fields:
            return k
    return None


def load_testset():
    data = defaultdict(lambda: defaultdict(list))
    for path in sorted(glob.glob(os.path.join(TESTSET, "*.csv"))):
        name = os.path.basename(path)[:-4]
        if name == "glids":
            continue
        with open(path, encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            k = key_col(r.fieldnames or [])
            for row in r:
                data[(row.get(k) or "").split(".")[0]][name].append(row)
    with open(os.path.join(TESTSET, "glids.csv"), encoding="utf-8", newline="") as f:
        meta = {r["glid"]: r for r in csv.DictReader(f)}
    return data, meta


# ---------------------------------------------------------------- API data
def api_endpoints():
    eps = {}
    for name, (url, body, status, *_rest) in ENDPOINTS.items():
        if status != "WORKS":
            continue
        eps[name] = (url, body)
    return eps


def fetch(glid, refresh=False):
    ak, tok = os.environ.get("VANI_AK"), os.environ.get("VANI_USERS_TOKEN")
    modid = os.environ.get("VANI_USERS_MODID", "GLADMIN")
    out = {}
    for name, (url, body) in api_endpoints().items():
        path = os.path.join(CACHE, name, f"{glid}.json")
        if name == "users_profile":  # company-API method: path-segment GET, one call per profile section type
            if not refresh and os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    out[name] = json.load(f)
                continue
            if not (ak and tok):
                out[name] = {"_error": "VANI_AK / VANI_USERS_TOKEN not set"}
                continue
            sections, codes = {}, []
            for typ in body["types"]:
                u = (url.replace("{g}", glid).replace("{modid}", modid).replace("{type}", typ)
                     .replace("{token}", urllib.parse.quote(tok, safe="")).replace("{ak}", ak))
                code, obj = call(f"users_profile_{glid}_{typ}", u, timeout=20, quiet=True)
                codes.append(code)
                sections[typ] = obj
            rec = {"_endpoint": url.split("/glid/")[0], "_http": 200 if 200 in codes else (codes[0] if codes else None),
                   "_fetched_at": datetime.now().isoformat(timespec="seconds"), "data": sections}
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False)
            out[name] = rec
            continue
        if not refresh and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                out[name] = json.load(f)
            continue
        params = {k: (v.replace("{g}", glid) if isinstance(v, str) else v) for k, v in body.items()}
        if "imutils.com" in url:  # users SOA: GET with credentials in the query
            if not (ak and tok):
                out[name] = {"_error": "VANI_AK / VANI_USERS_TOKEN not set"}
                continue
            q = urllib.parse.urlencode({**params, "modid": modid, "AK": ak, "token": tok})
            code, obj = call(f"{name}_{glid}", f"{url}?{q}", timeout=20, quiet=True)
        else:
            code, obj = call(f"{name}_{glid}", url, params, timeout=25, quiet=True)
        rec = {"_endpoint": url.split("?")[0], "_http": code, "_fetched_at": datetime.now().isoformat(timespec="seconds"),
               "data": decode(obj) if obj is not None else None}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)
        out[name] = rec
    return out


def body(api, name):
    """Unwrap the useful payload of an API record."""
    d = (api.get(name) or {}).get("data")
    if isinstance(d, dict):
        for k in ("response", "Response", "RESPONSE"):
            if k in d:
                d = d[k]
                break
    if isinstance(d, dict) and "Data" in d:
        d = d["Data"]
    if isinstance(d, dict) and "DATA" in d:
        d = d["DATA"]
    return d


# ---------------------------------------------------------------- derivations
DESIG_FAMILY = r"husband|wife|son|beta|ladka|daughter|beti|papa|father|pita|mummy|mother|maa|bhai|brother|bhaiya|bhaiyya|chacha|bhatija|bache|baba|uncle|didi|sister|family"
DESIG_BOSS = r"owner|malik|sir|boss|seth|sahab|saab|saheb|md|director|proprietor|head|senior|manager|madam|mam|babu|incharge|concerned|partner"
MEMORY = {
    "contact_person": r"\b(beta|son|bhai|brother|owner|malik|manager|partner|sir|papa|father|husband|wife|accountant|staff)\b",
    "language_pref": r"\b(hindi|english|gujarati|marathi|tamil|telugu|kannada|bengali|punjabi|malayalam)\b",
    "competitor_or_paid": r"\b(justdial|just dial|tradeindia|trade india|amazon|flipkart|meesho|already paid|package|subscription|paid service)\b",
    "need": r"\b(requirement|leads? chahiye|more leads|enquiry chahiye|buyer chahiye|order chahiye)\b",
}


# Call history is "already known" context, weighted by age; scheduling is owned by another agent.
RECENT_DAYS = 30      # full detail
MAX_AGE_DAYS = 90     # older calls are ignored
SCHED_OUTCOMES = {"Call Later / Busy"}  # kept as outcome + "rushed" signal; only times / slots are dropped
OUTCOME = {"Meeting Fixed": "meeting_fixed", "Not Interested": "not_interested", "General (talked)": "general",
           "Call Later / Busy": "call_later_busy"}
# per-call signal lexicons: romanised + Devanagari (seller turns) and English (summaries)
SIGNALS = {
    "rushed": re.compile(r"busy|बिज़ी|बिजी|jaldi|जल्दी|abhi nahi|अभी नहीं|baad me|बाद में|driving|गाड़ी|meeting me|मीटिंग में|"
                         r"time nahi|टाइम नहीं|call (me )?later|call back|not free|in a hurry|not the right time", re.I),
    "confused": re.compile(r"samajh nahi|समझ नहीं|kya matlab|क्या मतलब|kaun sa|कौन सा|कौन सी|dobara|दोबारा|phir se|फिर से|"
                           r"confus|did not understand|didn't understand|unclear", re.I),
    "frustrated": re.compile(r"pareshan|परेशान|baar baar|बार बार|mat karo|मत करो|dimag|दिमाग|faltu|फालतू|bakwas|बकवास|"
                             r"frustrat|angry|agitat|irritat|annoy|harass|rude|upset|stop call|do not call|don't call|not to call", re.I),
    "asked_if_bot": re.compile(r"\bbot\b|robot|रोबोट|machine|मशीन|computer|कंप्यूटर|recorded|रिकॉर्ड|automated|real person|"
                               r"insaan|इंसान|asked (if|whether) .{0,30}(bot|ai|automated|recorded)", re.I),
}
ID_KEY = re.compile(r"gstin|gst_?no|gst_number|\bgst\b$|pan_?no|pan_number|aadha+r|bank|ifsc|acc_?n|account_no|cin_number|"
                    r"tan_number|iec|fssai|vat|cst_no|service_tax|epf|esi_number|udyam|passport|voter", re.I)
ID_VALUE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b|\b[A-Z]{5}\d{4}[A-Z]\b|\b[A-Z]{4}0[A-Z0-9]{6}\b|"
                      r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")


def scrub_ids(o):
    """Remove government / bank ID numbers from LLM-facing output (team data policy). Flags and years stay."""
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if ID_KEY.search(str(k)) and not isinstance(v, (bool, dict, list)) and not str(k).endswith(("_flag", "_year", "_available")):
                continue
            out[k] = scrub_ids(v)
        return out
    if isinstance(o, list):
        return [scrub_ids(x) for x in o]
    if isinstance(o, str):
        return ID_VALUE.sub("[ID removed]", o)
    return o
SCHED_SUB = re.compile(r"callback|call_back|busy|later|reschedul|voicemail|no_response", re.I)
SCHED_SENT = re.compile(r"(call ?back|call (him|her|them|me)? ?(later|tomorrow|again)|call later|busy|driving|baad me|kal call|"
                        r"\b\d{1,2}(:\d{2})?\s?(am|pm|baje)\b|tomorrow|next week|reschedul|follow[- ]?up (at|time|call))", re.I)
EXCLUDED = {"F04", "F05", "F06", "F07", "K02"}  # scheduling data: handled by the scheduling agent
# previous VANI call history (G01-G11) is not in our scope (user, 2026-10-09): computed but not output
EXCLUDED |= {f"G{i:02d}" for i in range(1, 12)}
# a sentence with any of these carries discussion content: keep it, only blank its time words
SUBSTANCE = re.compile(r"meeting|visit|executive|\bsales\b|interest|denied|bother|stop call|do not call|don't call|complain|"
                       r"frustrat|angry|irritat|price|product|requirement|paid|package|service|order|buyer|enquir|catalog|"
                       r"not need|no need|already|competitor|subscription|not to call|harass|agitat|abus|rude|upset|"
                       r"previous(ly)? (spoke|discuss)|discussion|profile|location", re.I)
TIME_WORDS = re.compile(r"\b(day after tomorrow|tomorrow|today|tonight|next week|this week|"
                        r"(on )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
                        r"(between |at |by |around )?\d{1,2}(:\d{2})?\s?(am|pm|baje)( and \d{1,2}(:\d{2})?\s?(am|pm))?|"
                        r"after (half an hour|an hour|\d+ (minutes|mins|hours|days)))\b", re.I)


def drop_scheduling(text):
    """Strip call timing from a summary: scheduling-only sentences are dropped, sentences with
    discussion content are kept with their time words replaced by [time]. Returns (text, dropped, redacted)."""
    parts = re.split(r"(?<=[.!?।])\s+", text or "")
    out, dropped, redacted = [], 0, 0
    for x in parts:
        if not SCHED_SENT.search(x):
            out.append(x)
        elif SUBSTANCE.search(x):
            y = TIME_WORDS.sub("[time]", x)
            redacted += y != x
            out.append(y)
        else:
            dropped += 1
    return " ".join(out).strip(), dropped, redacted


def evaluator(files, allowed=None):
    by = defaultdict(list)
    for r in files.get("ps07_evaluator", []):
        if allowed is not None and r.get("attempt_id") not in allowed:
            continue
        try:
            by[r["eval_agent"]].append((r.get("attempt_id"), json.loads(r["agent_output"])))
        except Exception:
            continue
    return by


def build_points(glid, files, api, meta, now):
    P = {}

    def put(pid, value, source):
        P[pid] = (value, source)

    sf = (files.get("ps07_seller_file") or [{}])[0]
    gp = (files.get("gc_profile") or [{}])[0]
    bs = (files.get("btc_seller") or [{}])[0]
    so = (files.get("so_seller") or [{}])[0]
    ud = body(api, "users_detail") or {}
    ud = ud if isinstance(ud, dict) else {}
    bots_all = sorted(files.get("ps07_bot_calls", []), key=lambda r: r.get("call_start_time", ""))

    def age(r, col="call_start_time"):
        d = dt(r.get(col))
        return (now - d).days if d else None

    bots = [r for r in bots_all if age(r) is not None and age(r) <= MAX_AGE_DAYS]
    stale = len(bots_all) - len(bots)
    win_ids = {r.get("attempt_id") for r in bots}
    call_date = {r.get("attempt_id"): r.get("call_start_time") for r in bots}
    ev = evaluator(files, win_ids)
    att = sorted(files.get("btc_attempts", []), key=lambda r: r.get("call_start_time") or r.get("lead_sent_time") or "")
    sc = body(api, "scorecard_m") or {}
    sc_last = latest(sc.get("summary") if isinstance(sc, dict) else [])
    v2 = body(api, "scorecard_v2") or {}
    v2_last = latest(v2.get("summary") if isinstance(v2, dict) else [])
    byr = body(api, "byr_supply") or {}
    gl_dtl = (byr.get("GL_DTL") or [{}])[0] if isinstance(byr, dict) else {}
    enq_last = latest(byr.get("ENQALL") if isinstance(byr, dict) else [])
    topbar = ((body(api, "topbar") or {}).get("top_bar_data") or [{}])
    topbar = topbar[0] if isinstance(topbar, list) and topbar else (topbar if isinstance(topbar, dict) else {})
    qsum = body(api, "query_sum") or {}

    # A identity and callee
    put("A01", glid, f"test set stratum = {meta.get('stratum')}, rich sources = {meta.get('rich_sources_of_8')}/8")
    put("A02", pick({"api": ud.get("glusr_usr_companyname"), "gc": gp.get("company_name"), "so": so.get("company_name")},
                    ["api", "gc", "so"]), "users_detail.glusr_usr_companyname · gc_profile · so_sellers")
    put("A03", pick(ud, ["glusr_usr_salute", "glusr_usr_firstname", "glusr_usr_middlename_tbd", "glusr_usr_lastname",
                         "glusr_usr_csalute", "glusr_usr_cfirstname", "glusr_usr_clastname", "glusr_usr_add_contactname"]),
        "users_detail (account holder + contact person)")
    put("A04", pick({"users_detail": ud.get("glusr_usr_designation"), "so_sellers": so.get("contact_designation")},
                    ["users_detail", "so_sellers"]), "users_detail.glusr_usr_designation · so_sellers.contact_designation")
    pns = body(api, "users_pnssetting")
    slots = {k: v for k, v in pns.items() if isinstance(v, dict) and not blank(v.get("number"))} if isinstance(pns, dict) else {}
    contacts = body(api, "users_contacts")
    p12 = body(api, "pns_chart_12w") or {}
    put("A05", {"pns_slots": slots, "all_contact_numbers": contacts if isinstance(contacts, dict) else None,
                "per_number_success": p12.get("pns_no_summ") if isinstance(p12, dict) else None,
                "pns_mapped": p12.get("pns_number_mapped") if isinstance(p12, dict) else None,
                "number_wise_pns_latest": [r for r in (byr.get("number_wise_pns") or [])][-6:] if isinstance(byr, dict) else None},
        "users_pnssetting · users_detail(all_contact_info) · pns_chart_api · byrsupplyapi")
    dispo = [o for _, o in ev.get("disposition", [])]
    alt = [o for o in dispo if not blank(o.get("alternate_person_designation")) or not blank(o.get("alternate_number"))
           or o.get("disposition") in ("alternate_number_or_not_dm", "wrong_number")]
    roles = []
    for o in alt:
        d = str(o.get("alternate_person_designation") or "").lower()
        role = ("wrong_number" if o.get("disposition") == "wrong_number" else
                "family" if re.search(DESIG_FAMILY, d) else "staff (DM is owner/boss)" if re.search(DESIG_BOSS, d) else
                "not_dm (role unknown)")
        roles.append({"role_of_picker": role, **pick(o, ["disposition", "alternate_person_designation",
                                                         "alternate_person_name", "alternate_number", "reason"])})
    put("A06", {"n_calls_with_disposition_json": len(dispo), "events": roles} if dispo else None,
        "ps07 evaluator `disposition`")
    put("A07", pick(ud, ["glusr_usr_gender", "glusr_usr_salute", "glusr_usr_csalute"]) or None,
        "users_detail (often empty; never inferred from names)")

    # B location and language
    put("B01", pick({**sf, **{k: ud.get(k) for k in ("city_name", "state_name")}},
                    ["seller_city", "seller_district", "seller_state", "city_name", "state_name"]), "ps07 seller file · users_detail")
    put("B02", pick({**sf, **bs, **{"address1": ud.get("glusr_usr_add1"), "address2": ud.get("glusr_usr_add2"),
                                     "zip": ud.get("glusr_usr_zip")}},
                    ["seller_pincode", "seller_locality", "seller_latitude", "seller_longitude", "address1", "address2", "zip"]),
        "ps07 seller file · btc sellers · users_detail")
    langs = Counter()
    for r in files.get("gc_buyer_call_extractions", []):
        try:
            for l in ast.literal_eval(r.get("languages") or "[]"):
                langs[l] += 1
        except Exception:
            pass
    put("B03", dict(langs.most_common()) or None, f"gc_buyer_call_extractions.languages ({len(files.get('gc_buyer_call_extractions', []))} calls)")
    seller_turns = [r for r in files.get("ps07_call_turns", [])
                    if r.get("speaker") == "seller" and r.get("attempt_id") in win_ids]
    text = " ".join(r.get("text", "") for r in seller_turns)
    dev, lat = len(re.findall(r"[ऀ-ॿ]", text)), len(re.findall(r"[A-Za-z]", text))
    put("B04", {"seller_turns": len(seller_turns), "devanagari_char_share": round(dev / (dev + lat), 2) if dev + lat else None,
                "latin_char_share": round(lat / (dev + lat), 2) if dev + lat else None} if seller_turns else None,
        "ps07_call_turns (speaker = seller)")
    put("B05", pick({"users_detail": ud.get("gl_pref_language_id"), "so_sellers": so.get("preferred_language_id")},
                    ["users_detail", "so_sellers"]) or None, "users_detail.gl_pref_language_id · so_sellers")

    # C business profile
    put("C01", pick({**sf, "legal_status": ud.get("gl_legal_status_val"), "biz_type": ud.get("glusr_usr_business_type"),
                     "primary_biz_type": ud.get("gl_primary_biz_type")}, ["business_type", "legal_status", "biz_type", "primary_biz_type"]),
        "ps07 seller file · users_detail")
    put("C02", pick({**sf, "users_turnover": ud.get("gl_turnover_val"), "so_gst_turnover": so.get("gst_annual_turnover")},
                    ["annual_turnover", "users_turnover", "so_gst_turnover"]), "ps07 seller file · users_detail · so_sellers")
    put("C03", pick(sf, ["nature_of_business", "nature_of_business_secondary"]), "ps07 seller file")
    put("C04", pick({**sf, "member_since": ud.get("glusr_usr_membersince") or gl_dtl.get("member_since"),
                     "service_start": (qsum.get("summ") or [{}])[0].get("cust_to_serv_startdate") if isinstance(qsum, dict) and qsum.get("summ") else None},
                    ["gst_registration_year", "member_since", "service_start"]), "ps07 seller file · users_detail · byrsupplyapi · queryChartSum")
    put("C05", pick({"users_custtype": ud.get("glusr_usr_custtype_name"), "gc_customer_type": gp.get("customer_type"),
                     "gc_is_paid": gp.get("is_paid"), "scorecard_service": sc_last.get("service"),
                     "byr_custtype": gl_dtl.get("custtype_name"), "paid_free": enq_last.get("supp_paid_free"),
                     "query_sum_service": pick((qsum.get("summ") or [{}])[0], ["service_shortname", "generic_service_name"]) if isinstance(qsum, dict) and qsum.get("summ") else None},
                    ["users_custtype", "gc_customer_type", "gc_is_paid", "scorecard_service", "byr_custtype", "paid_free", "query_sum_service"]),
        "users_detail · gc_profile · cust_scorecard · byrsupplyapi · queryChartSum")
    put("C06", pick({**gp, "users_listing_status": ud.get("glusr_usr_listing_status"), "users_approv": ud.get("glusr_usr_approv"),
                     "disabled_reason": ud.get("glusr_disabled_reason")},
                    ["listing_status", "mobile_verified_flag", "email_verified_flag", "gst_verified_flag", "gst_flag",
                     "is_pan_number_available", "business_type_flag", "visiting_card_flag", "users_listing_status", "users_approv",
                     "disabled_reason"]) or None, "gc_profile · users_detail")
    put("C07", pick({"employees": ud.get("glusr_noof_emp_val"), "year_of_estb": ud.get("glusr_usr_year_of_estb"),
                     "so_employees_id": so.get("employees_id"), "so_year_established": so.get("year_established")},
                    ["employees", "year_of_estb", "so_employees_id", "so_year_established"]) or None, "users_detail · so_sellers")

    # C08 seller-written business profile sections (users/profile, company-API path-segment method)
    prof = (api.get("users_profile") or {}).get("data") or {}
    secs = {}
    for typ, resp in prof.items():
        r = (resp or {}).get("Response") if isinstance(resp, dict) else None
        d = r.get("Data") if isinstance(r, dict) else None
        if isinstance(d, list) and d:
            secs[typ] = [{"title": x.get("GLUSR_PROFILE_TITLE") or x.get("pc_clnt_feature_sv_title"),
                          "description": x.get("GLUSR_PROFILE_DESCRIPTION") or x.get("pc_clnt_feature_sv_description"),
                          "modified": x.get("GLUSR_PROFILE_DATE_MODIFIED"), "added": x.get("GLUSR_PROFILE_DATE_ADDED"),
                          "approval_status": x.get("GLUSR_PROFILE_APPROVAL_STATUS")} for x in d if isinstance(x, dict)]
    put("C08", secs or None, "users_profile (Awards, Custom_Profile, ExtProfile 1/2, Infrastructure, Jobs, Media, News, Quality, "
                             "Testimonial); only sellers who wrote these sections have data")

    # D categories and products
    put("D01", {"top": pick(sf, ["top_category_1", "top_category_2", "top_category_3", "top_parent_category", "top_category_group"]),
                "mcats_api": body(api, "mcat_names")}, "ps07 seller file · blsummarydetails")
    put("D02", {"num_categories": sf.get("num_categories"), "by_rank_api": body(api, "mcat_rank")},
        "ps07 seller file · gl_mcats_prdts_dtls")
    put("D03", {"category_dtls": body(api, "category_dtls"),
                "scorecard_ranks": pick(sc_last, ["a_rank_mcats", "ba_rank_mcats", "bb_rank_mcats", "bc_rank_mcats", "ca_rank_mcats",
                                                  "cb_rank_mcats", "cc_rank_mcats", "d_rank_mcats"]),
                "so_categories": [pick(r, ["mcat_name", "parent_mcat_name", "category_name", "group_name", "is_top5_category",
                                           "is_a_rank", "is_primary_mapping"]) for r in files.get("so_categories", [])] or None},
        "category_dtls · cust_scorecard · so_seller_categories")
    pm = body(api, "prd_mapping") or {}
    put("D04", {"file": pick(sf, ["eng_product_count", "eng_products_modified_90d", "eng_products_modified_1yr"]),
                "prd_mapping_count": (pm.get("Count") if isinstance(pm, dict) else None),
                "added_deactivated": pick(topbar, ["prd_add_lw", "prd_add_lm", "prd_add_lq", "prd_deac_lw", "prd_deac_lm", "prd_deac_lq"])},
        "ps07 seller file · prd_mapping_api · gettopbarsmry")
    put("D05", {"api_top_products": pm.get("prd_dtls") if isinstance(pm, dict) else None,
                "so_products": [pick(r, ["product_name", "mcat_name", "price", "price_unit", "moq_unit", "approval_status"])
                                for r in files.get("so_products", [])] or None}, "prd_mapping_api · so_products")
    put("D06", {"eng_cqs": sf.get("eng_cqs"), "scorecard": pick(sc_last, ["cqs", "prd_no_prices", "name_only_prd", "prod_wo_image", "prod_wo_mcat"]),
                "query_sum_prd_smry": qsum.get("prd_smry") if isinstance(qsum, dict) else None,
                "byr_curr_prd": byr.get("curr_prd") if isinstance(byr, dict) else None,
                "filtercount": body(api, "products_filtercount"),
                "so_catalog_health": files.get("so_catalog_health") or None},
        "ps07 seller file · cust_scorecard · queryChartSum · byrsupplyapi · productfiltercount · so_catalog_health")
    put("D07", {"prd_mapping_count": pm.get("Count") if isinstance(pm, dict) else None,
                "scorecard": pick(sc_last, ["live_prd_cnt", "deactivated_prd", "prd_added"])}, "prd_mapping_api · cust_scorecard")

    # E demand and buyleads
    enqs = sorted(files.get("gc_enquiries", []), key=lambda r: r.get("enquiry_date", ""))
    lag = [(dt(r.get("first_read_date")) - dt(r.get("enquiry_date"))).total_seconds() / 3600 for r in enqs
           if dt(r.get("first_read_date")) and dt(r.get("enquiry_date"))]
    qd = body(api, "query_dtls") or {}
    put("E01", {"file": pick(sf, ["eng_enq_received_90d", "eng_enq_received_1yr"]),
                "gc_enquiries_total": len(enqs) or None,
                "topbar": pick(topbar, ["enq_lw", "enq_lm", "enq_lq", "qry_reply_lw", "qry_reply_lm", "qry_reply_lq"]),
                "byr_latest_month": pick(enq_last, ["data_year", "data_month", "enq_all", "total_enq_recv", "total_whatsapp_enq_recv"]),
                "monthly_18m": qd.get("ENQ") if isinstance(qd, dict) else None},
        "ps07 seller file · gc_enquiries · gettopbarsmry · byrsupplyapi · queryChartDtls")
    put("E02", [pick(r, ["enquiry_date", "subject", "message", "product_name", "search_keyword", "source_module", "buyer_city",
                         "buyer_state", "buyer_country", "buyer_company", "buyer_designation", "read_status", "first_read_date"])
                for r in enqs[-5:][::-1]] or None, "gc_enquiries_received (latest 5)")
    seller_replies = [r for r in files.get("gc_enquiry_messages", []) if r.get("message_from") == "seller"]
    put("E03", {"gc_median_hours_to_first_read": round(statistics.median(lag), 1) if lag else None,
                "gc_enquiries_read": sum(1 for r in enqs if not blank(r.get("first_read_date"))), "gc_enquiries": len(enqs),
                "gc_seller_replies": len(seller_replies),
                "file": pick(sf, ["eng_enq_replies_90d", "eng_enq_replies_1yr"]),
                "scorecard": pick(sc_last, ["replies", "buyer_reply_pct", "buyer_reply_call_pct", "callbacks", "reply_callback_uniq_buyer_cnt"]),
                "callback_speed": pick(v2_last, ["callback_0to1_hrs", "callback_1to4_hrs", "callback_4to24_hrs", "callback_gt_1day", "callbacks"]),
                "byr": pick(enq_last, ["enq_reply_cnt", "callback_count", "thumbs_up_responsiveness_percent", "thumbs_total_responsiveness_cnt"])},
        "gc_enquiries · gc_enquiry_messages · ps07 seller file · cust_scorecard · cust_wh_apiv2 · byrsupplyapi")
    bl = files.get("gc_buyleads_bought", [])
    bls = body(api, "bl_summary") or {}
    put("E04", {"gc_bought": len(bl) or None, "gc_by_mcat_rank": dict(Counter(r.get("mcat_rank") or "?" for r in bl)) or None,
                "gc_top_keywords": dict(Counter(r.get("keyword") for r in bl if r.get("keyword")).most_common(8)) or None,
                "gc_credits_used": sum(num(r.get("credits_used"), 0) for r in bl) or None,
                "api_bl_pur": bls.get("bl_pur") if isinstance(bls, dict) else None,
                "scorecard": pick(sc_last, ["bl_cons", "bl_cons_i", "bl_cons_f", "bl_active_days"]),
                "byr": pick(enq_last, ["bl_pur_total", "bl_pur_india", "bl_pur_foreign", "bl_pur_active_days"])},
        "gc_buyleads_bought · glusr_bl_summaryv2 · cust_scorecard · byrsupplyapi")
    put("E05", pick(sc_last, ["bl_credits_alctd", "bl_credit_lapsed", "bl_credit_lapsed_i", "bl_credit_lapsed_f", "current_balance",
                              "last_cons_date"]) or None, "cust_scorecard (latest month)")
    put("E06", {**pick(sc_last, [k for k in sc_last if k.startswith(("bl_pur_0to", "bl_pur_15to", "bl_pur_4to", "bl_pur_gt", "cons_0_4", "cons_4_24", "cons_grter"))]),
                **pick(enq_last, ["bl_pur_0to4hrs_per", "bl_pur_4to24hrs_per", "bl_pur_gt24hrs_per"])} or None,
        "cust_scorecard · byrsupplyapi")
    put("E07", {"scorecard": pick(sc_last, ["blni", "blni_loc", "blni_spec", "blni_wrng_product", "blni_other"]),
                "reason_wise_month": bls.get("BLNI_REASON_WISE_MONTH") if isinstance(bls, dict) else None},
        "cust_scorecard · glusr_bl_summaryv2")
    put("E08", {"counts": body(api, "prepplus_counts"), "competitors": body(api, "prepplus_competitors")}, "nsdprepplus")

    # F phone behaviour
    gm = body(api, "glmisccount") or {}
    put("F01", {"file": pick(sf, ["eng_pns_received_90d", "eng_pns_answered_90d", "eng_pns_received_1yr", "eng_pns_answered_1yr"]),
                "glmisccount": gm.get("PNS") if isinstance(gm, dict) else None,
                "scorecard": pick(sc_last, ["pns_calls_recd", "pns_calls_ans", "pns_success_prcnt", "in_pns_count", "fr_pns_count"]),
                "topbar": pick(topbar, ["pns_lw", "pns_lm", "pns_lq", "pns_total_7d", "pns_total_30d", "pns_total_90d"])},
        "ps07 seller file · glmisccount · cust_scorecard · gettopbarsmry")
    bc = files.get("gc_buyer_calls", [])
    talk = [num(r.get("talk_sec"), 0) for r in bc if r.get("call_status") == "Connected"]
    put("F02", {"api_avg_talktime": p12.get("pns_avg") if isinstance(p12, dict) else None,
                "gc_buyer_calls": len(bc) or None, "gc_connected": len(talk) or None,
                "gc_median_talk_sec": statistics.median(talk) if talk else None},
        "pns_chart_api · gc_buyer_calls_received")
    put("F03", {"file": pick(sf, ["eng_pickup_ratio_90d", "eng_pickup_ratio_1yr", "eng_long_calls_90d", "eng_short_calls_90d",
                                  "eng_callback_90d", "eng_callback_1yr", "bot_answer_rate", "avg_answered_call_sec"]),
                "callback_speed": pick(v2_last, ["callback_0to1_hrs", "callback_1to4_hrs", "callback_4to24_hrs", "callback_gt_1day"])},
        "ps07 seller file · cust_wh_apiv2")
    put("F08", pick(ud, ["glusr_usr_lastlogin", "glusr_usr_lastmodified", "glusr_usr_ext_modified_date"]) or None, "users_detail")

    # G previous conversations (already known), weighted by age; scheduling removed
    def conv(r):
        a = age(r)
        text, cut, red = drop_scheduling(r.get("lead_call_summary", ""))
        return {"date": r.get("call_start_time"), "days_ago": a, "relevance": "recent" if a <= RECENT_DAYS else "older",
                "outcome": OUTCOME.get(r.get("disposition_label"), r.get("disposition_label")), "duration_sec": r.get("lead_call_duration"),
                "meeting_fixed": r.get("meeting_fixed") == "1" or None,
                "what_was_discussed": text if a <= RECENT_DAYS else (text[:300] + (" …" if len(text) > 300 else "")),
                "scheduling_sentences_dropped": cut or None, "time_words_redacted_in": red or None}
    convs = [conv(r) for r in reversed(bots)]
    durs = [num(r.get("lead_call_duration"), 0) for r in bots]
    put("G01", {"answered_calls_last_90d": len(bots), "of_which_last_30d": sum(1 for c in convs if c["relevance"] == "recent"),
                "older_calls_ignored": stale or None, "last_call_date": bots[-1].get("call_start_time") if bots else None,
                "avg_duration_sec": round(sum(durs) / len(durs), 1) if durs else None,
                "never_reached_by_vani": (not bots_all) or None,
                "n_prior_calls_all_history": len(bots_all),
                "first_call_date_all_history": bots_all[0].get("call_start_time") if bots_all else None},
        f"ps07_bot_calls (window {MAX_AGE_DAYS} d; recent = {RECENT_DAYS} d)")
    put("G02", {"outcome_counts_all_history": dict(Counter(OUTCOME.get(r.get("disposition_label"), r.get("disposition_label"))
                                                           for r in bots_all)) or None,
                "outcome_counts_last_90d": dict(Counter(OUTCOME.get(r.get("disposition_label"), r.get("disposition_label"))
                                                        for r in bots)) or None,
                "meetings_fixed_last_90d": sum(r.get("meeting_fixed") == "1" for r in bots) or None},
        "ps07_bot_calls (all-history = counts only; call_later_busy kept as an outcome, no times)")
    put("G03", {"last_call": convs[0], "earlier_calls_in_window": convs[1:] or None} if convs else
        ({"note": f"{stale} older call(s) beyond {MAX_AGE_DAYS} days ignored"} if stale else None),
        "ps07_bot_calls.lead_call_summary (scheduling sentences removed)")
    put("G04", {"objections": [{"date": call_date.get(aid), "analysis": o.get("objection_analysis")}
                               for aid, o in ev.get("objections", [])] or None,
                "questions": [{"date": call_date.get(aid), **pick(q, ["que_dialogue", "category", "ans_dialogue"])}
                              for aid, o in ev.get("seller_questions", []) for q in (o.get("questions") or [])] or None},
        "evaluator objections / seller_questions (last 90 d)")
    put("G05", {"already_met_or_in_touch": [{"date": call_date.get(aid), **pick(o, ["category", "seller_exact_quote"])}
                                            for aid, o in ev.get("se_contact", []) if o.get("category") != "neither"] or None,
                "incorrect_meeting_fixed": [{"date": call_date.get(aid), **pick(o, ["seller_final_stance", "seller_initial_reaction"])}
                                            for aid, o in ev.get("incorrect_mf", []) if o.get("incorrect_mf")] or None,
                "undated_apr_sep_flags (lower weight)": pick(sf, ["showed_frustration", "asked_if_talking_to_bot",
                                                                  "do_not_call_requested", "already_in_touch_with_executive"])},
        "evaluator se_contact / incorrect_mf (last 90 d) · ps07 seller file (undated)")
    texts = [("summary", r.get("call_start_time"), drop_scheduling(r.get("lead_call_summary", ""))[0]) for r in bots] + \
            [("evaluator", call_date.get(aid), str(o.get("reason", ""))) for aid, o in ev.get("disposition", [])] + \
            [("turn", call_date.get(r.get("attempt_id")), r.get("text", "")) for r in seller_turns]
    facts = []
    for src, date, t in texts:
        for fam, pat in MEMORY.items():
            for m in re.finditer(pat, t or "", re.I):
                facts.append({"family": fam, "match": m.group(0), "source": src, "date": date,
                              "context": (t[max(0, m.start() - 60): m.end() + 60]).replace("\n", " ")})
    put("G06", facts or None, "regex over last-90-day summaries + evaluator + seller turns (scheduling families removed)")
    wpt = [len((r.get("text") or "").split()) for r in seller_turns]
    rate = [len((r.get("text") or "").split()) / (num(r.get("end_sec"), 0) - num(r.get("start_sec"), 0))
            for r in seller_turns if (num(r.get("end_sec"), 0) - num(r.get("start_sec"), 0)) > 0.3]
    lr = [o for _, o in ev.get("latency_repetition", [])]
    put("G07", {"seller_turns": len(seller_turns), "words_per_turn": round(statistics.mean(wpt), 1) if wpt else None,
                "words_per_sec": round(statistics.median(rate), 2) if rate else None,
                "latency_repetition": [{**pick(o.get("latency") or {}, ["p50_sec", "p95_sec", "overlap_count", "seller_had_to_repeat_count"]),
                                        "is_loopy": o.get("is_loopy")} for o in lr] or None} if (seller_turns or lr) else None,
        "ps07_call_turns · evaluator latency_repetition (last 90 d)")
    put("G08", {"how_calls_ended": dict(Counter(o.get("sub_disposition") for o in dispo if o.get("sub_disposition"))) or None,
                "who_ended_call": [pick(o, ["who_ended_call", "seller_tried_after_closure", "explanation"])
                                   for _, o in ev.get("execdrop", [])] or None},
        "evaluator disposition / execdrop (last 90 d)")
    put("G09", {"bot_versions_heard": dict(Counter(r.get("lead_bot_version") for r in bots)) or None}, "ps07_bot_calls (last 90 d)")
    put("G10", [r.get("call_recording_url") for r in bots if not blank(r.get("call_recording_url"))] or None,
        "ps07_bot_calls.call_recording_url (last 90 d)")
    ev_by_call = defaultdict(dict)
    for agent, items in ev.items():
        for aid, o in items:
            ev_by_call[aid][agent] = o
    turns_by_call = defaultdict(list)
    for r in seller_turns:
        turns_by_call[r.get("attempt_id")].append(r.get("text") or "")
    rows = []
    for r in reversed(bots):
        aid, e = r.get("attempt_id"), ev_by_call.get(r.get("attempt_id"), {})
        d, x = e.get("disposition") or {}, e.get("execdrop") or {}
        turn_text, summ = " ".join(turns_by_call.get(aid, [])), r.get("lead_call_summary") or ""
        sig, src = {}, {}
        for name, pat in SIGNALS.items():
            t_hits, s_hits = len(pat.findall(turn_text)), len(pat.findall(summ))
            sig[name], src[name] = t_hits + s_hits, [f"turns:{t_hits}"] * bool(t_hits) + [f"summary:{s_hits}"] * bool(s_hits)
        if r.get("disposition_label") == "Call Later / Busy":
            sig["rushed"] += 1
            src["rushed"].append("outcome:call_later_busy")
        sub = str(d.get("sub_disposition") or "")
        if re.search(r"busy|callback|dropped_mid_pitch", sub):
            sig["rushed"] += 1
            src["rushed"].append(f"evaluator:{sub}")
        ni = r.get("disposition_label") == "Not Interested" or d.get("disposition") == "not_interested"
        sig["not_interested"], src["not_interested"] = int(ni), (["outcome"] if ni else [])
        ndm = d.get("disposition") in ("alternate_number_or_not_dm",) or not blank(d.get("alternate_person_designation"))
        sig["not_decision_maker"], src["not_decision_maker"] = int(ndm), (["evaluator:disposition"] if ndm else [])
        sig["wrong_number"], src["wrong_number"] = int(d.get("disposition") == "wrong_number"), (
            ["evaluator:disposition"] if d.get("disposition") == "wrong_number" else [])
        rows.append({"date": r.get("call_start_time"), "days_ago": age(r),
                     "outcome": OUTCOME.get(r.get("disposition_label"), r.get("disposition_label")),
                     "ended_by": x.get("who_ended_call"), "end_pattern": d.get("sub_disposition"),
                     "duration_sec": num(r.get("lead_call_duration")), "has_transcript": bool(turns_by_call.get(aid)),
                     "has_evaluator": bool(e), "signals": sig,
                     "signal_sources": {k: v for k, v in src.items() if v}})
    put("G11", rows or None, f"ps07_bot_calls + evaluator + seller turns, per answered call in last {MAX_AGE_DAYS} d "
                             "(lexicon hits + labels; counts, not scores)")

    # H human relationship
    ex = [r for r in sorted(files.get("ps07_exec_calls", []), key=lambda r: r.get("call_start_time", ""))
          if age(r) is not None and age(r) <= MAX_AGE_DAYS]
    put("H01", {"exec_calls": len(ex), "answered": sum(r.get("status") == "Answered" for r in ex),
                "last": ex[-1].get("call_start_time") if ex else None, "modules": dict(Counter(r.get("module") for r in ex)) or None,
                "dsr_monthly_api": body(api, "dsr_count")}, "ps07_executive_calls (last 90 d) · getgldsrcount")
    put("H02", gl_dtl or None, "byrsupplyapi.GL_DTL (sales + tele account managers)")
    put("H03", {"se_contact": dict(Counter(o.get("category") for _, o in ev.get("se_contact", []))) or None,
                "scorecard": pick(sc_last, ["video_meet", "physical_meet", "last_video_meet_dt", "success_connect", "succ_connect_bd"])},
        "evaluator se_contact · cust_scorecard · getgldsrcount")

    # I account health
    put("I01", pick(sc_last, ["cmplnts_cnt", "closed_cmplnts", "fdbk_nt_satisfied"]) or None, "cust_scorecard (latest month)")
    put("I02", {"gap": "no working source (getContext / prerenewal_api)",
                "proxy_service_start": (qsum.get("summ") or [{}])[0].get("cust_to_serv_startdate") if isinstance(qsum, dict) and qsum.get("summ") else None},
        "GAP")
    put("I03", {"gap": "no working source (getContext)", "proxies": pick(sc_last, ["defaulter_flag", "pns_defaulter_count"])}, "GAP + cust_scorecard")
    put("I04", {"scorecard": pick(sc_last, ["avg_ratings", "ratings_cnt", "ratings_asked"]),
                "byr": pick(enq_last, [k for k in enq_last if k.startswith(("cumulative_", "thumbs_", "uniq_rating"))])},
        "cust_scorecard · byrsupplyapi")

    # J other channels
    wm = files.get("gc_whatsapp_messages", [])
    put("J01", {"messages": len(wm), "by_sender": dict(Counter(r.get("message_sender") for r in wm)),
                "status": dict(Counter((r.get("message_status") or "").lower() for r in wm)),
                "last": max((r.get("entry_date") or "" for r in wm), default=None)} if wm else None, "gc_whatsapp_messages")
    cb = sorted(files.get("gc_whatsapp_chatbot", []), key=lambda r: r.get("entry_date", ""))
    put("J02", {"turns": len(cb), "intents": dict(Counter(r.get("intent") for r in cb).most_common(10)),
                "latest_seller_messages": [pick(r, ["entry_date", "user_message", "intent", "bot_reply"]) for r in cb[-10:][::-1]],
                "api_conversation": body(api, "wa_conv")} if (cb or body(api, "wa_conv")) else None,
        "gc_whatsapp_chatbot_conversations · getwaconv")
    put("J03", [pick(r, ["call_date", "seller_role_on_call", "is_b2b", "file_intent", "languages", "products_discussed", "categories",
                         "prices_quoted", "specs_discussed", "stock_status"]) for r in files.get("gc_buyer_call_extractions", [])] or None,
        "gc_buyer_call_extractions")

    # K this call
    la = att[-1] if att else {}
    put("K01", {"latest_trigger_bucket": la.get("redis_bucket"), "latest_lead_sent": la.get("lead_sent_time")} if la else None,
        "btc_attempts (latest) = why VANI is calling; live value comes from the dialler")
    put("K03", {"festive_season_window": now.month in (10, 11)}, "calendar month heuristic (call timing is not decided here)")
    put("K04", {"gap": "dialler must pass which number is dialled", "candidate_slots": list(slots)} , "GAP")
    return P


# ---------------------------------------------------------------- markdown
def render_value(v, indent=""):
    if isinstance(v, dict):
        lines = []
        for k, x in v.items():
            if blank(x):
                continue
            if isinstance(x, list) and len(x) <= 12 and all(not isinstance(y, (dict, list)) for y in x):
                lines.append(f"{indent}- **{k}:** " + ", ".join(str(y) for y in x))
            elif isinstance(x, (dict, list)):
                lines.append(f"{indent}- **{k}:**")
                lines.append(render_value(x, indent + "  "))
            else:
                lines.append(f"{indent}- **{k}:** {x}")
        return "\n".join(l for l in lines if l.strip())
    if isinstance(v, list) and len(v) <= 12 and all(not isinstance(x, (dict, list)) for x in v):
        return f"{indent}- " + ", ".join(str(x) for x in v)
    if isinstance(v, list):
        lines = []
        for x in v[:60]:
            if isinstance(x, (dict, list)):
                lines.append(f"{indent}- {short(x, 1200)}")
            else:
                lines.append(f"{indent}- {x}")
        if len(v) > 60:
            lines.append(f"{indent}- … {len(v) - 60} more (full rows in data/testset)")
        return "\n".join(lines)
    return f"{indent}{v}"


def has_value(v):
    if isinstance(v, dict):
        return any(has_value(x) for x in v.values())
    if isinstance(v, list):
        return any(has_value(x) for x in v)
    return not blank(v)


def render(glid, meta, P, files, api):
    filled = [k for k, (v, _) in P.items() if has_value(v) and k not in EXCLUDED]
    shown = [k for k in LABELS if k not in EXCLUDED]
    out = [f"# Seller context: {glid}", "",
           f"Generated {datetime.now():%Y-%m-%d %H:%M} by `app/context/SCRUBBER.py`. Test-set stratum **{meta.get('stratum')}**. "
           f"Data points with a value: **{len(filled)} / {len(shown)}**. Unmasked (PII handling: legal team).", "",
           "**How to use:** seller profile, callee, business, catalogue, demand, account and channel data. Previous VANI call "
           "history and call scheduling (timing, retries, callbacks) are handled elsewhere and are not in this file.", "",
           "**Sources present:** files: " + ", ".join(f"{k} ({len(v)})" for k, v in sorted(files.items()) if v) + "; APIs: " +
           ", ".join(f"{k} (HTTP {r.get('_http')})" for k, r in sorted(api.items())), "",
           "**Missing data points:** " + (", ".join(k for k in shown if k not in filled) or "none"), ""]
    for letter, title in GROUPS:
        out += [f"## {letter}. {title}", ""]
        for pid in [k for k in LABELS if k.startswith(letter) and k not in EXCLUDED]:
            v, src = P.get(pid, (None, ""))
            via, fsrc, apis, status, note = DATA_POINTS[pid]
            out.append(f"### {pid} {LABELS[pid]}")
            out.append(f"*Source:* {src} · *catalogue:* {via}, API {status}")
            out.append("")
            out.append(render_value(v) if not blank(v) else "_no data_")
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------- main
def run_one(glid, data, meta, use_api, refresh):
    files = {k: v for k, v in data.get(glid, {}).items()}
    api = fetch(glid, refresh) if use_api else {}
    P = build_points(glid, files, api, meta.get(glid, {}), datetime.now())
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{glid}.md"), "w", encoding="utf-8") as f:
        f.write(render(glid, meta.get(glid, {}), P, files, api))
    with open(os.path.join(OUT, f"{glid}.points.json"), "w", encoding="utf-8") as f:
        json.dump(scrub_ids({k: {"value": v, "source": s} for k, (v, s) in P.items() if k not in EXCLUDED}), f,
                  ensure_ascii=False, default=str)
    filled = sum(1 for k, (v, _) in P.items() if has_value(v) and k not in EXCLUDED)
    api_ok = sum(1 for r in api.values() if r.get("_http") == 200)
    return glid, filled, api_ok, len(api)


def main():
    a = argparse.ArgumentParser()
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--glid")
    g.add_argument("--all", action="store_true")
    a.add_argument("--no-api", action="store_true")
    a.add_argument("--refresh", action="store_true")
    a.add_argument("--workers", type=int, default=6)
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    data, meta = load_testset()
    glids = list(meta) if p.all else [p.glid.strip()]
    with ThreadPoolExecutor(max_workers=p.workers) as pool:
        results = list(pool.map(lambda x: run_one(x, data, meta, not p.no_api, p.refresh), glids))
    for glid, filled, ok, n in results:
        print(f"{meta.get(glid, {}).get('stratum', '-'):8} points={filled:2}/{len(LABELS) - len(EXCLUDED)} api_ok={ok}/{n}")
    print(f"wrote {len(results)} files to {OUT}")


if __name__ == "__main__":
    main()
