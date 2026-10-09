"""Per-seller data inventory over the offline hackathon files.

`build` makes one pass over every seller-keyed file in data/ and writes
data/index/seller_coverage.csv: one row per GLID, with row count, first date
and last date for each source. `show` prints what we hold for one GLID:
sources with counts and date ranges, plus which profile fields are filled.
Values are hidden unless --values is passed (they can be PII).

Run:
  python app/context/seller_inventory.py build
  python app/context/seller_inventory.py show --glid 12345678 [--values]
  python app/context/seller_inventory.py summary
"""
import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

csv.field_size_limit(10**9)
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data")
INDEX = os.path.join(ROOT, "index", "seller_coverage.csv")

# name, file glob (under data/), key column, date column, row filter
SOURCES = [
    ("ps07_seller_file", "ps07/ps07_seller_files_part*.csv", "fk_glusr_usr_id", None, None),
    ("ps07_bot_calls", "ps07/ps07_bot_calls_*.csv", "fk_glusr_usr_id", "call_start_time", None),
    ("ps07_bot_calls_with_summary", "ps07/ps07_bot_calls_*.csv", "fk_glusr_usr_id", "call_start_time",
     lambda r: bool(r.get("lead_call_summary", "").strip())),
    ("ps07_bot_calls_with_recording", "ps07/ps07_bot_calls_*.csv", "fk_glusr_usr_id", "call_start_time",
     lambda r: bool(r.get("call_recording_url", "").strip())),
    ("ps07_call_turns", "ps07/ps07_call_turns.csv", "fk_glusr_usr_id", None, None),
    ("ps07_evaluator", "ps07/ps07_evaluator_outputs_*.csv", "fk_glusr_usr_id", None, None),
    ("ps07_recording_sample", "ps07/ps07_recording_sample_5000.csv", "fk_glusr_usr_id", "call_start_time", None),
    ("ps07_exec_calls", "ps07/ps07_executive_calls.csv", "fk_glusr_usr_id", "call_start_time", None),
    ("gc_profile", "global_context/gc_seller_profile.csv", "fk_glusr_usr_id", None, None),
    ("gc_enquiries", "global_context/gc_enquiries_received.csv", "seller_glid", "enquiry_date", None),
    ("gc_enquiry_messages", "global_context/gc_enquiry_messages.csv", "seller_glid", "reply_date", None),
    ("gc_buyer_calls", "global_context/gc_buyer_calls_received.csv", "seller_glid", "call_datetime", None),
    ("gc_buyleads_bought", "global_context/gc_buyleads_bought.csv", "seller_glid", "purchase_date", None),
    ("gc_whatsapp_messages", "global_context/gc_whatsapp_messages.csv", "glid", "entry_date", None),
    ("gc_whatsapp_chatbot", "global_context/gc_whatsapp_chatbot_conversations.csv", "glid", "entry_date", None),
    ("gc_buyer_call_extractions", "global_context/gc_buyer_call_extractions.csv", "glid", "call_date", None),
    ("gc_bot_calls", "global_context/gc_bot_calls.csv", "fk_glusr_usr_id", "call_start_time", None),
    ("gc_bot_call_turns", "global_context/gc_bot_call_turns.csv", "fk_glusr_usr_id", None, None),
    ("gc_exec_calls", "global_context/gc_executive_calls.csv", "fk_glusr_usr_id", "call_start_time", None),
    ("btc_seller", "best_time_to_call/Best-Time-to-Call - Sellers.csv", "fk_glusr_usr_id", None, None),
    ("btc_attempts", "best_time_to_call/Best-Time-to-Call - Call Attempts Apr-Sep 2026.csv", "fk_glusr_usr_id",
     "call_start_time", None),
    ("btc_unanswered", "best_time_to_call/Best-Time-to-Call - Call Attempts Apr-Sep 2026.csv", "fk_glusr_usr_id",
     "call_start_time", lambda r: r.get("lead_call_status") != "Answered"),
    ("so_seller", "seller_onboarding/so_sellers.csv", "fk_glusr_usr_id", None, None),
    ("so_locations", "seller_onboarding/so_seller_locations.csv", "fk_glusr_usr_id", None, None),
    ("so_categories", "seller_onboarding/so_seller_categories.csv", "fk_glusr_usr_id", None, None),
    ("so_products", "seller_onboarding/so_products_part*.csv", "fk_glusr_usr_id", None, None),
    ("so_catalog_health", "seller_onboarding/so_catalog_health.csv", "fk_glusr_usr_id", None, None),
    ("so_kyc_documents", "seller_onboarding/so_kyc_documents.csv", "fk_glusr_usr_id", "uploaded_on", None),
    ("so_kyc_field_checks", "seller_onboarding/so_kyc_field_checks.csv", "fk_glusr_usr_id", None, None),
    ("so_kyc_sessions", "seller_onboarding/so_kyc_sessions.csv", "fk_glusr_usr_id", "created_on", None),
    ("leap_call_logs", "aids/Call_Logs_Hackathon.csv", "fk_glusr_usr_id", "entered_on", None),
]
EVAL_AGENTS = ["disposition", "seller_questions", "objections", "topics", "incorrect_mf", "execdrop",
               "se_contact", "location_confirmation", "latency_repetition", "ivr"]
PROFILE_FILES = [
    ("ps07_seller_file", "ps07/ps07_seller_files_part*.csv", "fk_glusr_usr_id"),
    ("gc_profile", "global_context/gc_seller_profile.csv", "fk_glusr_usr_id"),
    ("btc_seller", "best_time_to_call/Best-Time-to-Call - Sellers.csv", "fk_glusr_usr_id"),
    ("so_seller", "seller_onboarding/so_sellers.csv", "fk_glusr_usr_id"),
    ("so_catalog_health", "seller_onboarding/so_catalog_health.csv", "fk_glusr_usr_id"),
]


def glid_of(value):
    return (value or "").strip().split(".")[0]


def rows(pattern):
    for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            yield from csv.DictReader(f)


def build():
    cols = [s[0] for s in SOURCES] + [f"ps07_eval_{a}" for a in EVAL_AGENTS]
    count = defaultdict(lambda: defaultdict(int))
    first, last = defaultdict(dict), defaultdict(dict)
    for name, pattern, key, date_col, keep in SOURCES:
        n = 0
        for r in rows(pattern):
            if keep and not keep(r):
                continue
            g = glid_of(r.get(key))
            if not g:
                continue
            n += 1
            count[g][name] += 1
            if name == "ps07_evaluator":
                count[g]["ps07_eval_" + r.get("eval_agent", "")] += 1
            d = (r.get(date_col) or "")[:10] if date_col else ""
            if d:
                if d < first[g].get(name, "9999"):
                    first[g][name] = d
                if d > last[g].get(name, ""):
                    last[g][name] = d
        print(f"{name}: {n} rows", file=sys.stderr)
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["glid"] + cols + [f"{c}__first" for c in cols[:len(SOURCES)]]
                   + [f"{c}__last" for c in cols[:len(SOURCES)]])
        for g in sorted(count):
            w.writerow([g] + [count[g].get(c, 0) for c in cols]
                       + [first[g].get(c, "") for c in cols[:len(SOURCES)]]
                       + [last[g].get(c, "") for c in cols[:len(SOURCES)]])
    print(f"wrote {INDEX}: {len(count)} sellers", file=sys.stderr)


def load_index():
    with open(INDEX, encoding="utf-8", newline="") as f:
        return {r["glid"]: r for r in csv.DictReader(f)}


def show(glid, values):
    idx = load_index().get(glid)
    if not idx:
        print(json.dumps({"glid": glid, "found": False}))
        return
    sources = {}
    for name, *_ in SOURCES:
        n = int(idx[name])
        if n:
            sources[name] = {"rows": n, "first": idx.get(f"{name}__first") or None,
                             "last": idx.get(f"{name}__last") or None}
    evals = {a: int(idx[f"ps07_eval_{a}"]) for a in EVAL_AGENTS if int(idx[f"ps07_eval_{a}"])}
    profile = {}
    for name, pattern, key in PROFILE_FILES:
        if name not in sources:
            continue
        for r in rows(pattern):
            if glid_of(r.get(key)) == glid:
                filled = {k: v for k, v in r.items() if k != key and (v or "").strip() not in ("", "NA", "nan")}
                profile[name] = filled if values else sorted(filled)
                break
    out = {"glid": glid, "found": True, "sources": sources, "evaluator_agents": evals,
           "profile_fields_filled": profile,
           "missing_sources": [s[0] for s in SOURCES if s[0] not in sources]}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def summary():
    idx = load_index()
    ps07 = {g for g, r in idx.items() if int(r["ps07_seller_file"])}
    gc = {g for g, r in idx.items() if int(r["gc_profile"])}
    names = [s[0] for s in SOURCES] + [f"ps07_eval_{a}" for a in EVAL_AGENTS]
    print(f"{'source':34} {'sellers':>8} {'%PS07':>6} {'%GC5k':>6}")
    for c in names:
        have = {g for g, r in idx.items() if int(r[c])}
        print(f"{c:34} {len(have):8} {100*len(have & ps07)/len(ps07):6.1f} {100*len(have & gc)/len(gc):6.1f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("summary")
    s = sub.add_parser("show")
    s.add_argument("--glid", required=True)
    s.add_argument("--values", action="store_true", help="print field values (may include PII)")
    a = p.parse_args()
    {"build": build, "summary": summary}.get(a.cmd, lambda: show(a.glid, a.values))()
