"""facts.py: deterministic facts for the VANI persona agent (Part A of every trait, state, hook and guard).

Reads <folder>/context.json (built by app/persona/seller_context_builder.py) and writes <folder>/facts.json.
Formats: references/formats/{trait,state,hook}.json. The agent fills Part B later; this script never ranks hooks.
Thresholds are starting values (persona-skill-design.md section 3-5); they are tuned with data later.

Usage: python3 facts.py --folder /abs/path/data/contexts/<glid> [--today YYYY-MM-DD]
"""
import argparse
import json
import math
import os
import re
from datetime import date, datetime

FILE_OF = {}
for f, ids in {"core.md": "A B H I K X04 X05", "business.md": "C", "catalogue.md": "D",
               "buyleads.md": "E04 E05 E06 E07 E09 E10", "enquiries.md": "E01 E02 E03", "channels.md": "F J X01",
               "peers.md": "E08 E11", "candidate_leads.md": "E12"}.items():
    for i in ids.split():
        FILE_OF[i] = f
BANDS = ["0 - 40 L", "40 L - 1.5 Cr", "1.5 - 5 Cr", "5 - 25 Cr", "25 - 100 Cr", "100 - 500 Cr", "> 500 Cr"]
STATE_LANG = {"gujarat": "gu", "maharashtra": "mr", "tamil nadu": "ta", "karnataka": "kn", "kerala": "ml", "telangana": "te",
              "andhra pradesh": "te", "west bengal": "bn", "odisha": "or", "punjab": "pa", "assam": "as"}
FEMALE_NAMES = re.compile(r"^(.*(a|i|ee|ita|ika|ini|ani|devi|bai|ben|kumari)|priya|pooja|neha|anjali|sunita|anita|kavita|rekha|"
                          r"meena|seema|geeta|sita|lata|usha|asha|shobha|nisha|ritu|sonia|rani)$", re.I)
MALE_EXCEPTIONS = re.compile(r"^(krishna|aditya|chaitanya|shiva|surya|vidya sagar|ravi|hari|mani|bhai|bharti|ali)$", re.I)


def num(v, d=None):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "", "NA", "nan") else d
    except (TypeError, ValueError):
        return d


def cite(pid):
    return f"{FILE_OF.get(pid, FILE_OF.get(pid[:1], 'core.md'))}#{pid}"


def ev(pid, field, value, src="context.json"):
    return {"cite": cite(pid), "field": field, "value": value, "source": src}


def item(kind, iid, value, evidence, confidence, rule, detail=None, missing=None, **extra):
    a = {"value": value, "detail": detail or {}, "evidence": evidence, "confidence": round(confidence, 2), "rule": rule,
         "missing_inputs": missing or []}
    a.update(extra)
    return {"id": iid, "kind": kind, "A_script": a, "B_agent": None}


def days_between(a, b):
    try:
        return (b - datetime.strptime(str(a)[:10], "%Y-%m-%d").date()).days
    except Exception:
        return None


def build(ctx, today):
    P = {k: v.get("value") for k, v in ctx["points"].items()}
    g = lambda k: P.get(k) or {}
    calls = (g("G00") or {}).get("calls", []) if isinstance(g("G00"), dict) else []
    T, S, H, G = [], [], [], []

    # ---------------- traits
    vert = (g("H02").get("vertical_name") or "") if isinstance(g("H02"), dict) else ""
    div = "NSD" if "NSD" in vert.upper() else "CSD" if "CSD" in vert.upper() else "TMW" if "TMW" in vert.upper() or "WELCOME" in vert.upper() \
        else "KCD" if "KCD" in vert.upper() else "unknown"
    T.append(item("trait", "trait.division", div, [ev("H02", "H02.vertical_name", vert)], 1.0 if div != "unknown" else 0.3,
                  "text match on vertical_name; TMW and KCD use the CSD reference until decided",
                  detail={"vertical_name": vert, "reference": "division_nsd.md" if div == "NSD" else "division_csd.md",
                          "objective": "get a meeting (profile help framing; never 'sales')" if div == "NSD"
                          else "get a meeting (buy-lead usage / profile review framing; upsell happens in the meeting)"}))
    c5 = g("C05") if isinstance(g("C05"), dict) else {}
    T.append(item("trait", "trait.plan", c5.get("paid_free") or "unknown", [ev("C05", "C05.paid_free", c5.get("paid_free"))], 0.9,
                  "copy", detail={"plan_name": c5.get("byr_custtype") or c5.get("users_custtype")}))
    c4 = g("C04") if isinstance(g("C04"), dict) else {}
    ms = str(c4.get("member_since") or "")[:8]
    yrs = None
    if len(ms) == 8 and ms.isdigit():
        yrs = round(days_between(f"{ms[:4]}-{ms[4:6]}-{ms[6:]}", today) / 365.25, 1)
    T.append(item("trait", "trait.years_on_im", yrs, [ev("C04", "C04.member_since", c4.get("member_since"))], 0.9 if yrs is not None else 0.2,
                  "today minus member_since"))
    band = (g("C02") or {}).get("annual_turnover") if isinstance(g("C02"), dict) else None
    e10 = g("E10") if isinstance(g("E10"), dict) else {}
    s_stats = ((e10.get("seller") or {}).get("stats") or {})
    mc = next(iter((e10.get("mcats") or {}).values()), None) or {}
    c_stats = (mc.get("stats") or {}) if isinstance(mc, dict) else {}
    tier = None
    if band in BANDS:
        bi = BANDS.index(band)
        tier = "small" if bi == 0 else "mid" if bi <= 2 else "large"
    if tier and s_stats.get("median_rs") and c_stats.get("median_rs") and s_stats["median_rs"] > 2 * c_stats["median_rs"]:
        tier = {"small": "mid", "mid": "large", "large": "large"}[tier]
    aov_ref = s_stats.get("median_rs") or c_stats.get("median_rs")
    aov_tier = None
    if aov_ref and c_stats.get("median_rs"):
        aov_tier = "high" if aov_ref >= c_stats.get("p75_rs", 1e18) else "low" if aov_ref < 0.5 * c_stats["median_rs"] else "mid"
    elif aov_ref:
        aov_tier = "high" if aov_ref >= 50000 else "low" if aov_ref < 5000 else "mid"
    T.append(item("trait", "trait.business_scale", tier or "unknown",
                  [ev("C02", "C02.annual_turnover", band), ev("E10", "E10.seller.median_rs", s_stats.get("median_rs")),
                   ev("E10", "E10.category.median_rs", c_stats.get("median_rs"))],
                  0.8 if band in BANDS else 0.3,
                  "small < 40 L; mid 40 L-5 Cr; large > 5 Cr; one step up if seller AOV > 2x category AOV",
                  detail={"turnover_band": band, "aov_tier": aov_tier, "seller_aov_rs": s_stats.get("median_rs"),
                          "category_aov_rs": c_stats.get("median_rs"), "category_p75_rs": c_stats.get("p75_rs")},
                  missing=[] if band in BANDS else ["C02.annual_turnover"]))
    hv = (band in BANDS and BANDS.index(band) >= 3) or aov_tier == "high"
    T.append(item("trait", "trait.high_value", hv, [ev("C02", "C02.annual_turnover", band), ev("E10", "E10 AOV tier", aov_tier)],
                  0.8 if band in BANDS else 0.4, "high value = turnover 5 Cr+ or AOV tier high (seller AOV >= category top quarter)",
                  detail={"why": "high-value sellers may get Hinglish/English instead of the regional language (team decision)"}))
    c3 = g("C03") if isinstance(g("C03"), dict) else {}
    nob = " ".join(str(v) for v in c3.values() if v).lower()
    st = "manufacturer" if "manufactur" in nob else "trader" if re.search(r"trad|wholesal|retail|distribut|supplier", nob) \
        else "service" if "service" in nob else "unknown"
    T.append(item("trait", "trait.seller_type", st, [ev("C03", "C03.nature_of_business", c3)], 0.8 if st != "unknown" else 0.3, "text match"))
    a7 = g("A07")
    a3 = g("A03") if isinstance(g("A03"), dict) else {}
    gen, src, conf = "unknown", "none", 0.0
    if isinstance(a7, dict):
        val = " ".join(str(v) for v in a7.values() if v).lower()
        if re.search(r"\bfemale\b|\bmrs\b|\bms\b|\bmiss\b|\bsmt\b", val):
            gen, src, conf = "F", "recorded", 1.0
        elif re.search(r"\bmale\b|\bmr\b|\bshri\b", val):
            gen, src, conf = "M", "recorded", 1.0
    if gen == "unknown":
        first = (a3.get("glusr_usr_cfirstname") or a3.get("glusr_usr_firstname") or "").strip().split(" ")[0]
        if first:
            if MALE_EXCEPTIONS.match(first):
                gen, src, conf = "M", "name", 0.4
            elif FEMALE_NAMES.match(first):
                gen, src, conf = "F", "name", 0.4
            else:
                gen, src, conf = "M", "name", 0.4
    T.append(item("trait", "trait.seller_gender", gen, [ev("A07", "A07", a7), ev("A03", "A03.first_name", "(name, not repeated here)")], conf,
                  "recorded A07 first (1.0); else a first-name guess (0.4). Used ONLY to choose VANI's voice; never said aloud",
                  detail={"source": src}))
    b3 = g("B03") if isinstance(g("B03"), dict) else {}
    ct = g("X05") if isinstance(g("X05"), dict) else {}
    state = (ct.get("state") or (g("B01") or {}).get("seller_state") or "") if isinstance(g("B01"), dict) or ct else ""
    regional = STATE_LANG.get(state.strip().lower(), "hi")
    main_lang = max(b3, key=b3.get) if b3 else None
    T.append(item("trait", "trait.language", {"observed_main": main_lang, "regional": regional,
                                              "observed": b3, "default_start": regional if regional != "hi" else "hi (Hinglish light)"},
                  [ev("B03", "B03", b3), ev("B01", "B01.state", state)], 0.7 if b3 else 0.4,
                  "regional language of the state unless the seller is high value (team decision); observed languages from calls"))
    T.append(item("trait", "trait.city_tier", ct.get("tier") or "unknown", [ev("X05", "X05", ct)], 0.8 if ct.get("tier") else 0.2,
                  "gl_city_classification 1 metro / 2 tier2 / 3 small town / empty village; rural proxy = small town or village",
                  detail={"rural_proxy": ct.get("rural_proxy"), "hindi_belt": ct.get("hindi_belt"), "state": ct.get("state") or state or None}))
    d6 = g("D06") if isinstance(g("D06"), dict) else {}
    sc = d6.get("scorecard") if isinstance(d6.get("scorecard"), dict) else {}
    cqs = num(sc.get("cqs"), num(d6.get("eng_cqs")))
    fc = d6.get("filtercount") if isinstance(d6.get("filtercount"), dict) else {}
    prods = num(fc.get("PRODUCT_COUNT"), 0) or 0
    no_photo = num(fc.get("PRODUCT_COUNT_IMP_WITHOUT_PHOTO"), num(sc.get("prod_wo_image"), 0)) or 0
    no_price = num(sc.get("prd_no_prices"), 0) or 0
    gap_share = (no_photo + no_price) / prods if prods else None
    strength = "unknown"
    if cqs is not None:
        strength = "weak" if cqs < 40 or (gap_share or 0) > 0.2 else "strong" if cqs >= 70 and not (no_photo or no_price) else "ok"
    T.append(item("trait", "trait.im_profile_strength", strength, [ev("D06", "D06.cqs", cqs), ev("D06", "D06.no_photo/no_price", [no_photo, no_price])],
                  0.8 if cqs is not None else 0.2, "weak: CQS < 40 or > 20% products without photo/price; strong: CQS >= 70 and no gaps",
                  detail={"cqs": cqs, "products": prods, "without_photo": no_photo, "without_price": no_price, "c08_present": bool(P.get("C08"))}))
    txt = " ".join((c.get("summary") or "") + " " + " ".join(t.get("text", "") for t in c.get("transcript") or []) for c in calls).lower()
    plats = sorted({p for p in ["justdial", "tradeindia", "amazon", "flipkart", "meesho", "exportersindia", "udaan", "google"] if p in txt})
    T.append(item("trait", "trait.online_presence", {"other_platforms_mentioned": plats}, [ev("G00", "calls/*", plats)], 0.5,
                  "platform names in past calls"))
    oc = (g("G00") or {}).get("outcome_counts_all_history", {}) if isinstance(g("G00"), dict) else {}
    answered = sum(oc.values()) or 0
    busy = oc.get("Call Later / Busy", 0)
    T.append(item("trait", "trait.call_behaviour", {"answered_calls": answered, "busy_rate": round(busy / answered, 2) if answered else None,
                                                    "meetings_fixed": oc.get("Meeting Fixed", 0)},
                  [ev("G00", "G00.outcome_counts_all_history", oc)], 0.8 if answered else 0.2, "busy_rate = Call Later / Busy ÷ answered calls"))
    i1 = g("I01") if isinstance(g("I01"), dict) else {}
    h1 = g("H01") if isinstance(g("H01"), dict) else {}
    themes = sorted(((g("G00") or {}).get("objection_categories_all_history") or {}).keys()) if isinstance(g("G00"), dict) else []
    T.append(item("trait", "trait.service_history", {"complaints": num(i1.get("cmplnts_cnt"), 0), "closed": num(i1.get("closed_cmplnts"), 0),
                                                     "not_satisfied": num(i1.get("fdbk_nt_satisfied"), 0), "exec_calls": num(h1.get("exec_calls"), 0),
                                                     "past_objection_themes": themes},
                  [ev("I01", "I01", i1), ev("H01", "H01.exec_calls", h1.get("exec_calls"))], 0.8, "counts"))

    # ---------------- states
    e5 = g("E05") if isinstance(g("E05"), dict) else {}
    allot, lapsed, bal = num(e5.get("bl_credits_alctd"), 0), num(e5.get("bl_credit_lapsed"), 0), num(e5.get("current_balance"), 0)
    last_use = days_between(e5.get("last_cons_date"), today) if e5.get("last_cons_date") else None
    used = max(0.0, (allot or 0) - (bal or 0) - (lapsed or 0))
    if lapsed and lapsed > 0:
        bu = "lapsed"
    elif allot and (last_use is None or last_use > 30):
        bu = "unused"
    elif allot and used / allot < 0.3:
        bu = "low_use"
    elif allot:
        bu = "active"
    else:
        bu = "none"
    S.append(item("state", "state.bl_usage", bu, [ev("E05", "E05", e5)], 0.9 if e5 else 0.2,
                  "lapsed if lapsed > 0; unused if no use in 30 d; low_use if used < 30% of allotted; none if no credits",
                  detail={"allotted": allot, "lapsed": lapsed, "balance": bal, "days_since_last_use": last_use},
                  as_of=str(today), half_life_days=30, weight=1.0))
    pos = None
    if s_stats.get("median_rs") and c_stats.get("median_rs"):
        r = s_stats["median_rs"] / c_stats["median_rs"]
        pos = "below" if r < 0.7 else "above" if r > 1.3 else "same"
    S.append(item("state", "state.bl_value", pos or "unknown", [ev("E10", "E10", {"seller": s_stats.get("median_rs"), "category": c_stats.get("median_rs")})],
                  0.7 if pos else 0.2, "below if seller AOV < 0.7x category; above if > 1.3x",
                  as_of=str(today), half_life_days=30, weight=1.0))
    e7 = g("E07") if isinstance(g("E07"), dict) else {}
    ni = e7.get("scorecard") if isinstance(e7.get("scorecard"), dict) else {}
    ni_total = sum(num(v, 0) or 0 for v in ni.values())
    bad_talk = len(re.findall(r"irrelevant|not relevant|poor quality|fake|wrong (product|lead)|bekar|faltu lead", txt))
    S.append(item("state", "state.bl_quality_issue", "yes" if ni_total >= 3 or bad_talk else "no",
                  [ev("E07", "E07.scorecard", ni), ev("G00", "calls/*", f"{bad_talk} 'bad lead' mentions")], 0.7,
                  "yes if rejected leads >= 3 or a call says leads are bad", detail={"ni_reasons": ni, "bad_lead_mentions": bad_talk},
                  as_of=str(today), half_life_days=30, weight=1.0))
    e1 = g("E01") if isinstance(g("E01"), dict) else {}
    tb = e1.get("topbar") if isinstance(e1.get("topbar"), dict) else {}
    lm, lq = num(tb.get("enq_lm")), num(tb.get("enq_lq"))
    trend = "unknown"
    if lm is not None and lq:
        trend = "falling" if lm < 0.7 * (lq / 3) else "rising" if lm > 1.3 * (lq / 3) else "flat"
    S.append(item("state", "state.enquiry_flow", trend, [ev("E01", "E01.topbar", tb)], 0.8 if trend != "unknown" else 0.2,
                  "falling if last month < 0.7 x (last quarter / 3); rising if > 1.3x", detail={"last_week": tb.get("enq_lw"), "last_month": lm, "last_quarter": lq},
                  as_of=str(today), half_life_days=30, weight=1.0))
    f1 = g("F01") if isinstance(g("F01"), dict) else {}
    fsc = f1.get("scorecard") if isinstance(f1.get("scorecard"), dict) else {}
    S.append(item("state", "state.pns_flow", {"received": num(fsc.get("pns_calls_recd")), "answered": num(fsc.get("pns_calls_ans")),
                                              "success_pct": num(fsc.get("pns_success_prcnt"))},
                  [ev("F01", "F01.scorecard", fsc)], 0.8 if fsc else 0.2, "copy", as_of=str(today), half_life_days=30, weight=1.0))
    mood = {k: 0.0 for k in ("rushed", "frustrated", "confused", "asked_if_bot", "grievance")}
    last_mood_date = None
    for c in calls:
        if c.get("days_ago") is None:
            continue
        w = 0.5 ** (c["days_ago"] / 30)
        for k in mood:
            if (c.get("signals") or {}).get(k):
                mood[k] += w
                last_mood_date = last_mood_date or c.get("date")
    S.append(item("state", "state.call_mood", {k: round(v, 2) for k, v in mood.items()},
                  [ev("G00", "calls/*", "signals per call, weighted 0.5^(days/30)")], 0.6 if calls else 0.1,
                  "sum of per-call signals weighted by age (half-life 30 d)", detail={"last_signal_call": last_mood_date},
                  as_of=str(today), half_life_days=30, weight=1.0))
    recent = [c for c in calls if c.get("days_ago") is not None and c["days_ago"] <= 90]
    intent = "unknown"
    if recent:
        last = recent[0]
        lt = (last.get("summary") or "").lower()
        if last.get("outcome") == "Not Interested":
            intent = "not_interested"
        elif re.search(r"upgrade|plan|package|paid service|premium", lt):
            intent = "wants_upgrade"
        elif re.search(r"complain|problem|issue|not getting|no response|fraud", lt):
            intent = "problem"
    S.append(item("state", "state.intent", intent, [ev("G00", "calls/C01", recent[0]["outcome"] if recent else None)], 0.5 if recent else 0.1,
                  "last call in 90 d: Not Interested → not_interested; plan/upgrade words → wants_upgrade; complaint words → problem",
                  as_of=str(today), half_life_days=45, weight=1.0))
    last_exec = days_between(h1.get("last"), today) if h1.get("last") else None
    exec_in_calls = [c for c in recent if c.get("exec_contact") and c["exec_contact"] not in ("neither", None)]
    S.append(item("state", "state.recent_exec_contact", {"days_since_exec_call": last_exec, "exec_mentions_in_calls_90d": len(exec_in_calls)},
                  [ev("H01", "H01.last", h1.get("last"))], 0.8 if h1 else 0.2, "copy", as_of=str(today), half_life_days=14, weight=1.0))
    c7 = sum(1 for c in calls if c.get("days_ago") is not None and c["days_ago"] <= 7)
    c30 = sum(1 for c in calls if c.get("days_ago") is not None and c["days_ago"] <= 30)
    stop = any(re.search(r"stop (further |the )?call|don.?t call|do not call|update (their|your) system|no more calls|band karo",
                         (c.get("summary") or "") + " " + " ".join(t.get("text", "") for t in c.get("transcript") or []), re.I) for c in recent)
    S.append(item("state", "state.call_fatigue", {"vani_calls_7d": c7, "vani_calls_30d": c30, "asked_stop_calling": stop},
                  [ev("G00", "calls/*", {"7d": c7, "30d": c30})], 0.9, "count calls; stop-calling words in summaries/turns",
                  as_of=str(today), half_life_days=7, weight=1.0))
    open_c = (num(i1.get("cmplnts_cnt"), 0) or 0) - (num(i1.get("closed_cmplnts"), 0) or 0)
    griev = [c for c in calls if c.get("days_ago") is not None and c["days_ago"] <= 60 and (c.get("signals") or {}).get("grievance")]
    S.append(item("state", "state.open_grievance", "yes" if open_c > 0 or griev else "no",
                  [ev("I01", "I01", i1), ev("G00", "calls/*", f"{len(griev)} grievance calls in 60 d")], 0.7,
                  "yes if an open complaint, or a grievance signal in a call in the last 60 d",
                  detail={"open_complaints": open_c, "grievance_calls_60d": len(griev)}, as_of=str(today), half_life_days=60, weight=1.0))
    e8 = g("E08") if isinstance(g("E08"), dict) else {}
    md = ((e8.get("counts") or {}).get("mcat_data") or [{}]) if isinstance(e8.get("counts"), dict) else [{}]
    md0 = md[0] if md and isinstance(md[0], dict) else {}
    e9 = P.get("E09") or []
    S.append(item("state", "state.category_demand", {"local_bl": num(md0.get("local_bl")), "hyperlocal_bl": num(md0.get("hyperlocal_bl")),
                                                     "total_bl": num(md0.get("total_bl")),
                                                     "bulk_share": (e9[0] or {}).get("bulk_share") if e9 else None},
                  [ev("E08", "E08.counts", md0), ev("E09", "E09", "bulk share")], 0.7 if md0 else 0.2, "copy",
                  as_of=str(today), half_life_days=30, weight=1.0))
    e11 = g("E11") if isinstance(g("E11"), dict) else {}
    rung = next((r for r in e11.get("rungs", []) if r.get("allowed")), None) if e11.get("status") == "ok" else None
    peer_pos = None
    if rung:
        sb = e11.get("seller_leads_bought") or {}
        own = (sb.get("main_mcat") or 0) * (e11.get("window_days", 30) / (sb.get("window_days") or e11.get("window_days", 30)))
        med = rung.get("median_leads_per_buyer") or 0
        peer_pos = "ahead" if own > med * 1.2 else "behind" if own < med * 0.8 else "level"
    S.append(item("state", "state.peer_position", {"rung": rung, "seller_vs_peers": peer_pos},
                  [ev("E11", "E11", e11.get("first_allowed_rung"))], 0.7 if rung else 0.2,
                  "first rung with >= 5 same-size peers who bought; ahead / level / behind vs the peer median",
                  as_of=str(today), half_life_days=30, weight=1.0))
    leads = P.get("E12") or []
    S.append(item("state", "state.showcase_lead", {"best": leads[0] if leads else None, "backup": leads[1] if len(leads) > 1 else None},
                  [ev("E12", "candidate_leads.md#CL-1", bool(leads))], 0.8 if leads else 0.1, "first two rows by fit_score (E12)",
                  as_of=str(today), half_life_days=7, weight=1.0))

    # ---------------- guards
    fl = ((P.get("X00") or {}).get("seller_flags") or {})
    dnc = str(fl.get("do_not_call_requested")) in ("1", "1.0", "True", "true")
    G.append({"id": "guard.do_not_call", "value": dnc, "evidence": [ev("X04", "X04.do_not_call_requested", fl.get("do_not_call_requested"))],
              "action": "STOP: write status do_not_call; no persona, no Sarvam variables"})
    G.append({"id": "guard.asked_stop_calling", "value": stop, "evidence": [ev("G00", "calls/*", "stop-calling words")],
              "action": "default no pitch: apologise, confirm, close; override only with a newer call where the seller agreed"})
    met = (last_exec is not None and last_exec <= 3)
    G.append({"id": "guard.met_exec_recently", "value": met, "evidence": [ev("H01", "H01.last", h1.get("last"))],
              "action": "do not ask for a new meeting; follow up on the meeting, or recommend not calling"})
    G.append({"id": "guard.call_fatigue", "value": c7 >= 3, "evidence": [ev("G00", "calls/*", {"7d": c7})],
              "action": "short call; acknowledge earlier calls; never repeat the last pitch; may recommend skipping"})

    # ---------------- hooks (eligibility only)
    st = {s["id"]: s["A_script"]["value"] for s in S}
    tr = {t["id"]: t["A_script"]["value"] for t in T}
    div_ok = lambda ds: div in ds or (div in ("TMW", "KCD") and "CSD" in ds)

    def hook(hid, divisions, eligible, because, blockers, probe, facts):
        H.append({"id": hid, "kind": "hook", "A_script": {"eligible": bool(eligible and div_ok(divisions) and not blockers), "because": because,
                                                          "blockers": blockers, "division_fit": divisions, "probe_files": probe,
                                                          "facts_for_claim": facts}, "B_agent": None})
    hook("hook.profile_gap", ["NSD", "CSD"], tr["trait.im_profile_strength"] == "weak",
         [{"cite": cite("D06"), "fact": f"CQS {cqs}, {no_photo:.0f} without photo, {no_price:.0f} without price"}], [], ["catalogue.md", "business.md"],
         {"cqs": cqs, "without_photo": no_photo, "without_price": no_price})
    best = (st["state.showcase_lead"] or {}).get("best") or {}
    hook("hook.money_lead", ["NSD", "CSD"], bool(best.get("order_value_text")),
         [{"cite": "candidate_leads.md#CL-1", "fact": f"{best.get('product')} {best.get('quantity')} {best.get('unit')} {best.get('order_value_text')} {best.get('buyer_city')}"}],
         [], ["candidate_leads.md", "buyleads.md"], {"lead": best})
    cd = st["state.category_demand"] or {}
    hook("hook.category_demand", ["NSD", "CSD"], (cd.get("local_bl") or 0) > 0 or (cd.get("total_bl") or 0) > 0,
         [{"cite": cite("E08"), "fact": f"local BL {cd.get('local_bl')}, total {cd.get('total_bl')}"}], [], ["peers.md", "buyleads.md"], cd)
    blk = []
    if st["state.open_grievance"] == "yes":
        blk.append("open grievance: address it first")
    if stop:
        blk.append("asked to stop calling")
    hook("hook.unused_credits", ["CSD"], st["state.bl_usage"] in ("lapsed", "unused", "low_use"),
         [{"cite": cite("E05"), "fact": f"{lapsed:.0f} lapsed, balance {bal:.0f}"}], blk, ["buyleads.md", "calls/"],
         {"lapsed": lapsed, "balance": bal, "allotted": allot})
    hook("hook.lead_quality_fix", ["CSD"], st["state.bl_quality_issue"] == "yes",
         [{"cite": cite("E07"), "fact": f"rejection reasons {ni}"}], [], ["buyleads.md", "calls/"], {"ni": ni})
    hook("hook.enquiry_drop", ["CSD", "NSD"], st["state.enquiry_flow"] == "falling",
         [{"cite": cite("E01"), "fact": f"last month {lm}, last quarter {lq}"}], [], ["enquiries.md"], {"last_month": lm, "last_quarter": lq})
    pp = st["state.peer_position"] or {}
    hook("hook.peer_usage", ["NSD", "CSD"], bool(pp.get("rung")),
         [{"cite": cite("E11"), "fact": f"rung {(pp.get('rung') or {}).get('rung')}, seller {pp.get('seller_vs_peers')}"}],
         [], ["peers.md"], {"rung": pp.get("rung"), "seller_vs_peers": pp.get("seller_vs_peers"),
                            "permitted_line": "you are ahead of sellers your size" if pp.get("seller_vs_peers") == "ahead"
                            else "same-size sellers are using buy leads (numbers from the rung)"})
    hook("hook.resolve_grievance", ["CSD", "NSD"], st["state.open_grievance"] == "yes",
         [{"cite": cite("I01"), "fact": f"open complaints {open_c}, grievance calls {len(griev)}"}], [], ["core.md", "calls/"], {})
    return {"glid": ctx.get("glid"), "today": str(today), "division": div, "traits": T, "states": S, "guards": G, "hooks": H,
            "true_guards": [x["id"] for x in G if x["value"]], "eligible_hooks": [h["id"] for h in H if h["A_script"]["eligible"]],
            "start_rules": start_rules(T, S, G)}


def pick(rules):
    """First matching rule wins (the list order IS the priority).
    Returns {id, value, rule, grade, evidence, priority, matched} (priority and matched are rule ids)."""
    matched = [r for r in rules if r[0]]
    if not matched:
        return None
    _, value, rule, evidence, rid, grade = matched[0]
    return {"id": rid, "value": value, "rule": rule, "grade": grade, "evidence": evidence, "priority": [r[4] for r in rules],
            "matched": [r[4] for r in matched]}


LANG_NAME = {"hi": "HINDI", "gu": "GUJARATI", "mr": "MARATHI", "ta": "TAMIL", "kn": "KANNADA", "ml": "MALAYALAM", "te": "TELUGU",
             "bn": "BENGALI", "or": "ODIA", "pa": "PUNJABI", "as": "HINDI"}


def start_rules(T, S, G):
    """The state rules that set a field's start value at delivery (deterministic, never drawn). The selected card gives
    voice_gender and empathy; these rules change them when a state says so. language_start comes from the rules only.
    Sources: team decisions 2026-10-09 (seller gender -> VANI voice) and 2026-10-10 (female lean for tense calls and the
    rural Hindi belt; regional language unless high value; acknowledge grievances first)."""
    v = {x["id"]: x["A_script"] for x in T + S}
    val = lambda i: (v.get(i) or {}).get("value")
    det = lambda i: (v.get(i) or {}).get("detail") or {}
    mood = val("state.call_mood") or {}
    grievance = val("state.open_grievance") == "yes"
    tense = grievance or (mood.get("frustrated") or 0) >= 0.5
    rural_hb = bool(det("trait.city_tier").get("rural_proxy") and det("trait.city_tier").get("hindi_belt"))
    # Fixed priority (first match wins; never dict order). Every match is recorded so the persona's reason can cite it.
    # (match, value, rule text, evidence ids, rule id, evidence grade) - the grade says how strong the rule's own basis is
    voice_rules = [
        (val("trait.seller_gender") == "F", "F", "seller is female (recorded or name guess): female voice", ["trait.seller_gender"],
         "voice.female_seller", "WEAK"),
        (tense, "F", "tense seller (frustrated on calls or open grievance): female voice", ["state.call_mood", "state.open_grievance"],
         "voice.tense", "WEAK"),
        (rural_hb, "F", "rural Hindi-belt seller: female voice", ["trait.city_tier"], "voice.rural_hindi_belt", "GUESS"),
    ]
    voice = pick(voice_rules)
    lang = val("trait.language") or {}
    code = (lang.get("regional") if isinstance(lang, dict) else None) or "hi"
    language = pick([
        (bool(val("trait.high_value")), "ENGLISH", "high-value seller (5 Cr+ or high AOV): English with light Hindi", ["trait.high_value"],
         "lang.high_value", "GUESS"),
        (True, LANG_NAME.get(code, "HINDI"), f"regional language of the seller's state ({code})", ["trait.language"],
         "lang.regional", "WEAK"),
    ])
    adds = []
    if grievance:
        adds.append({"id": "emp.grievance", "grade": "WEAK", "text": "acknowledge the open complaint first, in one sentence",
                     "rule": "state.open_grievance = yes"})
    if (mood.get("frustrated") or 0) >= 0.5:
        adds.append({"id": "emp.frustrated", "grade": "GUESS", "text": "apologise briefly for the earlier calls",
                     "rule": "state.call_mood.frustrated >= 0.5"})
    if (mood.get("rushed") or 0) >= 0.5 or any(g["id"] == "guard.call_fatigue" and g["value"] for g in G):
        adds.append({"id": "emp.rushed", "grade": "GUESS", "text": "respect their time: keep it short, offer a callback",
                     "rule": "rushed mood or call fatigue"})
    return {"voice_gender": voice, "language_start": language, "empathy_add": adds}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--today")
    p = a.parse_args()
    today = datetime.strptime(p.today, "%Y-%m-%d").date() if p.today else date.today()
    ctx = json.load(open(os.path.join(p.folder, "context.json"), encoding="utf-8"))
    out = build(ctx, today)
    with open(os.path.join(p.folder, "facts.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"division": out["division"], "true_guards": out["true_guards"], "eligible_hooks": out["eligible_hooks"]}))


if __name__ == "__main__":
    main()
