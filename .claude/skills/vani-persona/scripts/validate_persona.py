"""validate_persona.py: the gate between the agent and Sarvam (S4). Pass/fail checks only; never judges the choice.

Run by persona_tool.py finalize, by the Stop hook, and again by the launcher after the turn (from its own
hash-checked copy). It checks CONTENT only, so a persona written around the tool gets the same checks; the launcher
adds the sha check against the finalize row.

Checks:
  1. Required fields. The prior: chosen is one of 03_prior.json top-2 (or P0 for the holdout).
  2. Hooks: every eligible hook has a decision with a reason; the primary has >= 3 cites from >= 2 files and cited
     counter-evidence; true guards are acknowledged; the hook is eligible; money first.
  3. Every cite resolves and its quote (<= 20 words) is in the file (normalised: case, quotes, spaces).
  4. Spoken text: banned words; first-person forms agree with the voice gender; numbers above 60 only from
     verified_facts; the identity line names IndiaMART.
  5. do_not_call (from 01_facts.json) means no persona may exist.
  7. Hierarchy mode, the text: verified_facts {id, quote, say} quote-checked, numbers in 'say' only from the quote;
     hook.fact_ids are verified_facts ids; personalisation has cites; every call_plan step and objection answer has a
     basis (evidence: cite+quote; persona: a decided field; division: an O<n> / hook / obj.* id); words per item
     within caps from words_per_turn; scripts fit language_start (+ Latin, + Devanagari); no promises; no other
     seller's tokens.
  6. Hierarchy mode (references/hierarchy.json; user decision 2026-10-10, plan §5a): every field is a decision:
     - reason_type is seller_evidence, hierarchy or start_persona (in that order of preference);
     - seller_evidence: quoted cites, at least one of them a hit of the field's probe search (re-run here);
     - hierarchy / start_persona: a 'searched' note and an answer for each of the top-3 hits (re-run here);
     - hierarchy: level and value group match the brief in 03_prior.json (n > 0);
     - start_persona: the value equals the selected card's value;
     - hard ranges and value groups from hierarchy.json.
     Without hierarchy.json (VANI_HIERARCHY=none, old tests) the earlier read-log + amendment-menu rules apply.

Usage: python validate_persona.py --folder <seller folder> --run <run dir>
Writes <run>/validation.json and exits 1 on any failure (all failures in one message).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import persona_tool as PT  # noqa: E402

REQ_DIMS_OLD = ["voice_gender", "voice_id", "pace", "pitch", "language_start", "code_mix", "accent", "formality", "warmth",
                "empathy", "sophistication", "words_per_turn"]
REQ_TOP = ["decision_id", "division", "prior", "dimensions", "personalisation", "hook", "opening", "identity_line", "call_plan",
           "objection_playbook", "escalation_rules", "guardrails", "verified_facts", "switch_sensitivity", "guards_ack",
           "overall_confidence", "completeness"]
BANNED = re.compile(r"\b(AI|A\.I\.|artificial intelligence|bot|robot|chatbot|branch manager|account manager|personally|"
                    r"main khud|khud aa(unga|ungi)|एआई|बॉट|रोबोट|ब्रांच मैनेजर|अकाउंट मैनेजर)\b", re.I)
MASC = re.compile(r"(raha hoon|rahaa hoon|karta hoon|bol raha|aaya hoon|gaya hoon|sakta hoon|रहा हूँ|रहा हूं|करता हूँ|करता हूं|सकता हूँ|सकता हूं|बोल रहा)", re.I)
FEM = re.compile(r"(rahi hoon|karti hoon|bol rahi|aayi hoon|gayi hoon|sakti hoon|रही हूँ|रही हूं|करती हूँ|करती हूं|सकती हूँ|सकती हूं|बोल रही)", re.I)
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
# user decision 2026-10-10: an honorific must belong to the language of the sentence (no 'ji' inside Telugu text)
HONORIFIC = {"hi": re.compile(r"(?<![A-Za-z])(ji|jee|saheb|sahab)(?![A-Za-z])|जी|साहब|ਜੀ", re.I),
             "te": re.compile(r"(?<![A-Za-z])(garu|gaaru)(?![A-Za-z])|గారు|गारु", re.I),
             "kn": re.compile(r"(?<![A-Za-z])avare(?![A-Za-z])|ಅವರೇ|ಅವರೆ", re.I)}
SCRIPT_LANG = [("te", re.compile(r"[ఀ-౿]")), ("kn", re.compile(r"[ಀ-೿]")), ("ta", re.compile(r"[஀-௿]")),
               ("ml", re.compile(r"[ഀ-ൿ]")), ("bn", re.compile(r"[ঀ-৿]")), ("gu", re.compile(r"[઀-૿]")),
               ("or", re.compile(r"[଀-୿]"))]


def wrong_honorific(t):
    """An honorific of another language inside a sentence in a regional script (e.g. 'ji' in Telugu); else None."""
    lang = next((l for l, rx in SCRIPT_LANG if rx.search(t)), None)
    if not lang:
        return None
    for hl, rx in HONORIFIC.items():
        m = rx.search(t)
        if m and hl != lang:
            return m.group(0)
    return None
AMEND_MENU = {"pace_up", "pace_down", "pitch_up", "pitch_down", "more_formal", "less_formal", "warmer", "briefer", "longer",
              "language_switch", "code_mix_more", "code_mix_less", "simpler", "more_numbers", "voice_gender_flip", "hook_swap"}


def norm(t):
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


STRICT = {"on": True}  # hierarchy mode = strict quotes bound to the cited span; old mode = whole-file match


def check_cite(folder, c, fails, where):
    cid, quote = (c.get("id") if isinstance(c, dict) else c), (c.get("quote") if isinstance(c, dict) else None)
    e = PT.quote_ok(folder, cid or "", quote, strict=STRICT["on"])
    if e:
        fails.append(f"{where}: {e}")
        return None if "does not exist" in e else cid.split("#")[0]
    return cid.split("#")[0]


def spoken(persona):
    out = [("opening", persona.get("opening")), ("identity_line", persona.get("identity_line")),
           ("hook.claim", (persona.get("hook") or {}).get("claim"))]
    out += [(f"call_plan[{i}]", s.get("say")) for i, s in enumerate(persona.get("call_plan") or [])]
    out += [(f"objection[{i}]", o.get("response")) for i, o in enumerate(persona.get("objection_playbook") or [])]
    return [(k, v) for k, v in out if v]


def _load(run, name, folder, fallback):
    p = os.path.join(run, name)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    q = os.path.join(folder, fallback)
    return json.load(open(q, encoding="utf-8")) if os.path.exists(q) else {}


def check_fields(folder, run, persona, h, prior, fails, facts=None):
    """Rule 6: every field is a decision with a checkable reason (content only; the search is re-run here)."""
    dims = persona.get("dimensions") or {}
    types = (h.get("reason_types") or {}).get("order") or ["seller_evidence", "hierarchy", "start_persona"]
    chosen = (persona.get("prior") or {}).get("chosen")
    card = PT.card_of(chosen) or {}
    as_of = PT.as_of(run) if os.path.exists(os.path.join(run, "turn.json")) else __import__("datetime").date.today()
    brief = prior.get("brief") or {}
    for f in PT.decide_fields(h):
        spec = h["fields"][f]
        x = dims.get(f)
        w = f"dimensions.{f}"
        if not isinstance(x, dict) or "value" not in x:
            fails.append(f"{w}: missing; decide it: persona_tool.py decide --field {f} ...")
            continue
        rt, v = x.get("reason_type"), x.get("value")
        if rt not in types:
            fails.append(f"{w}: reason_type must be one of {types}, not {rt!r}")
            continue
        if not x.get("reason"):
            fails.append(f"{w}: no reason")
        rng = spec.get("hard_range")
        if isinstance(rng, list) and len(rng) == 2 and (not isinstance(v, (int, float)) or not rng[0] <= v <= rng[1]):
            fails.append(f"{w}: value {v!r} outside {rng}")
        if isinstance(spec.get("value_groups"), list) and spec["value_groups"] and PT.group_of(spec, v) is None:
            fails.append(f"{w}: value {v!r} is in no value group {spec['value_groups']}")
        hits = PT.search(folder, spec, as_of)
        if rt == "seller_evidence":
            cites = x.get("cites") or []
            if not cites:
                fails.append(f"{w}: seller_evidence needs quoted cites")
            for c in cites:
                check_cite(folder, c, fails, w)
            hc = {k["cite"] for k in hits} | {k["id"] for k in hits}
            if cites and not any(isinstance(c, dict) and c.get("id") in hc and PT.quote_in_hit(c.get("quote"), hits, {c.get("id")})
                                 for c in cites):
                fails.append(f"{w}: no cite quotes a hit line of the field's probe search (probe --field {f})")
        else:
            if not x.get("searched"):
                fails.append(f"{w}: {rt} needs a 'searched' note")
            ans = x.get("answers") or {}
            for k in hits[:3]:
                if not (ans.get(k["id"]) or "").strip():
                    fails.append(f"{w}: top hit {k['id']} is not answered (it may be seller evidence)")
            if rt == "hierarchy":
                b, hi = brief.get(f) or {}, x.get("hierarchy") or {}
                g = (b.get("value_groups") or {}).get(hi.get("value_group")) or {}
                if not b.get("level_used") or hi.get("level") != b.get("level_used") or not g.get("n"):
                    fails.append(f"{w}: hierarchy data does not match the brief in 03_prior.json")
                elif PT.group_of(spec, v) != hi.get("value_group"):
                    fails.append(f"{w}: value {v!r} is not in the cited group {hi.get('value_group')!r}")
            sv = PT.start_value(f, card, facts) if rt == "start_persona" else None
            if rt == "start_persona" and sv is None:
                fails.append(f"{w}: start_persona but there is no start value for {f}")
            elif rt == "start_persona" and v != sv:
                fails.append(f"{w}: start_persona must keep the start value {sv!r}")
        cf = x.get("confidence")
        if cf is not None and (not isinstance(cf, (int, float)) or not 0 <= cf <= 1):
            fails.append(f"{w}: confidence {cf!r} must be within 0-1")
        elif cf is not None and cf > (persona.get("completeness") or 1) + 1e-9:
            fails.append(f"{w}: confidence {cf} > completeness {persona.get('completeness')}")


# ---------------------------------------------------------------- rule 7: the spoken text is evidenced (plan 5a, Q1)
SCRIPTS = {"deva": (0x0900, 0x097F), "beng": (0x0980, 0x09FF), "guru": (0x0A00, 0x0A7F), "gujr": (0x0A80, 0x0AFF),
           "orya": (0x0B00, 0x0B7F), "taml": (0x0B80, 0x0BFF), "telu": (0x0C00, 0x0C7F), "knda": (0x0C80, 0x0CFF),
           "mlym": (0x0D00, 0x0D7F)}
LANG_SCRIPT = {"HINDI": "deva", "MARATHI": "deva", "GUJARATI": "gujr", "TELUGU": "telu", "TAMIL": "taml", "KANNADA": "knda",
               "MALAYALAM": "mlym", "BENGALI": "beng", "PUNJABI": "guru", "ODIA": "orya", "ENGLISH": None}
ALWAYS_SCRIPTS = {"deva"}  # Latin is always allowed (transliterated speech); Devanagari = the Hindi fallback
PROMISE = re.compile(r"(guarantee[ds]?|guaranteed|pakka (order|lead|business)|100 ?%|sure ?shot|गारंटी|पक्का ऑर्डर|"
                     r"zaroor (milenge|milega|aayenge)|ज़रूर मिलेंगे)", re.I)
NEGATION = re.compile(r"(nahi|nahin|nhi|नहीं|नही|not|no |cannot|can't|won't|never|ఇవ్వను|కాదు|லை|ಇಲ್ಲ|ഇല്ല|না|ના|નહીં)", re.I)
OTHER_SELLER = re.compile(r"\{(COMPETITOR_\d+(_ID)?|BUYER_COMPANY|EXEC_NAME)\}")


def scripts_in(text):
    out = set()
    for ch in text or "":
        o = ord(ch)
        for s, (lo, hi) in SCRIPTS.items():
            if lo <= o <= hi:
                out.add(s)
                break
    return out


def _nums(t):
    out = set()
    for n in NUM.findall(t or ""):
        v = n.replace(",", "")
        out.add(v[:-2] if v.endswith(".0") else v)
    return out


def division_refs(division):
    """Ids the text may name as basis=division: O<n> objections and hook headings in the division file, plus
    objections.json ids (obj.*) when the repo copy is reachable."""
    refs = set()
    ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references",
                       f"division_{'nsd' if division == 'NSD' else 'csd'}.md")
    if os.path.exists(ref):
        t = open(ref, encoding="utf-8").read()
        refs |= {f"O{m}" for m in re.findall(r"\*\*O(\d+)\.", t)}
        refs |= set(re.findall(r"^###\s+(hook\.[a-z_]+)", t, re.M))
    oj = os.path.join(os.environ.get("VANI_REPO") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."),
                      "outputs", "objections.json")
    if os.path.exists(oj):
        try:
            refs |= {o.get("id") for o in json.load(open(oj, encoding="utf-8")).get("objections", []) if o.get("id")}
        except (ValueError, AttributeError):
            pass
    return refs


def check_text(folder, persona, fails):
    """Facts and claims carry cites + quotes; plan steps and objection answers carry a basis; text fits the persona."""
    dims = persona.get("dimensions") or {}
    lang = str((dims.get("language_start") or {}).get("value") or "").upper()
    wpt = (dims.get("words_per_turn") or {}).get("value")
    wpt = wpt if isinstance(wpt, (int, float)) else None
    allowed = {LANG_SCRIPT[lang]} if LANG_SCRIPT.get(lang) else set()
    allowed |= ALWAYS_SCRIPTS
    vf_ids = set()
    for i, v in enumerate(persona.get("verified_facts") or []):
        w = f"verified_facts[{i}]"
        if not (v.get("id") and v.get("quote") and v.get("say")):
            fails.append(f"{w}: needs id (cite), quote and say")
            continue
        vf_ids.add(v["id"])
        e = PT.quote_ok(folder, v["id"], v["quote"])
        if e:
            fails.append(f"{w}: {e}")
        extra = _nums(v["say"]) - _nums(v["quote"])
        if extra:
            fails.append(f"{w}: numbers {sorted(extra)} in 'say' are not in the quote")
    hk = persona.get("hook") or {}
    if hk.get("id") and hk.get("claim"):
        fids = hk.get("fact_ids") or []
        if not fids or not set(fids) <= vf_ids:
            fails.append(f"hook.fact_ids {fids} must be ids of verified_facts {sorted(vf_ids)}")
    for i, x in enumerate(persona.get("personalisation") or []):
        if not x.get("cites"):
            fails.append(f"personalisation[{i}]: needs cites")
        for c in x.get("cites") or []:
            check_cite(folder, c, fails, f"personalisation[{i}]")
    refs = division_refs(persona.get("division"))
    items = [(f"call_plan[{i}]", s, s.get("say")) for i, s in enumerate(persona.get("call_plan") or [])]
    items += [(f"objection[{i}]", o, o.get("response")) for i, o in enumerate(persona.get("objection_playbook") or [])]
    for w, item, _ in items:
        b = item.get("basis") or {}
        bt = b.get("type")
        if bt == "evidence":
            e = PT.quote_ok(folder, b.get("cite") or "", b.get("quote"))
            if e:
                fails.append(f"{w}.basis: {e}")
        elif bt == "persona":
            if b.get("ref") not in dims:
                fails.append(f"{w}.basis: persona ref {b.get('ref')!r} is not a decided field {sorted(dims)}")
        elif bt == "division":
            if b.get("ref") not in refs:
                fails.append(f"{w}.basis: division ref {b.get('ref')!r} not found (e.g. {sorted(refs)[:6]})")
        else:
            fails.append(f"{w}: needs basis {{type: evidence|persona|division, ...}}")
    steps = persona.get("call_plan") or []
    total = sum(len(str(s.get("say") or "").split()) for s in steps)
    if len(steps) > 12 or total > 300:
        fails.append(f"call_plan too long: {len(steps)} steps, {total} words (max 12 steps, 300 words)")
    spoken_items = [("opening", persona.get("opening"), max(30, 2 * (wpt or 15))), ("identity_line", persona.get("identity_line"), 40),
                    ("hook.claim", hk.get("claim"), max(40, 3 * (wpt or 15)))]
    spoken_items += [(w, t, max(20, 2 * (wpt or 15)) if w.startswith("call_plan") else max(40, 3 * (wpt or 15))) for w, _, t in items]
    for w, t, cap in spoken_items:
        if not t:
            continue
        n = len(str(t).split())
        if wpt and n > cap:
            fails.append(f"{w}: {n} words, more than {cap} for words_per_turn {wpt}")
        foreign = scripts_in(t) - allowed
        if lang and foreign:
            fails.append(f"{w}: script {sorted(foreign)} does not fit language_start {lang}")
        for sent in re.split(r"[.!?।\n]", str(t)):
            if PROMISE.search(sent) and not NEGATION.search(sent):
                fails.append(f"{w}: promise '{PROMISE.search(sent).group(0)}' (never promise leads, orders or results)")
        if OTHER_SELLER.search(str(t)):
            fails.append(f"{w}: names another seller / buyer / executive ({OTHER_SELLER.search(str(t)).group(0)}); peers only as aggregates")


def validate(folder, run):
    fails = []
    facts = _load(run, "01_facts.json", folder, "facts.json")
    prior = _load(run, "03_prior.json", folder, "prior.json")
    h = PT.load_hierarchy()
    STRICT["on"] = bool(h)
    dnc = "guard.do_not_call" in facts.get("true_guards", [])
    ppath = os.path.join(run, "04_persona.json")
    if dnc:
        if os.path.exists(ppath):
            fails.append("guard.do_not_call is true but a persona was written: write status do_not_call only")
        return fails
    if not os.path.exists(ppath):
        return ["04_persona.json missing" + (" (persona_tool.py finalize writes it)" if h else "")]
    persona = json.load(open(ppath, encoding="utf-8"))
    review = json.load(open(os.path.join(run, "02_review.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, "02_review.json")) else {}

    # 1. fields and the prior
    for k in REQ_TOP + ([] if h else ["amendments"]):
        if k not in persona:
            fails.append(f"persona: missing field '{k}'")
    dims = persona.get("dimensions") or {}
    pr = persona.get("prior") or {}
    p = prior.get("persona") or {}
    allowed = (["P0"] if p.get("holdout") else p.get("top2")) or pr.get("top2") or []
    if pr.get("chosen") not in allowed and not (pr.get("override") and not h):
        fails.append(f"prior.chosen {pr.get('chosen')!r} is not one of {allowed} (03_prior.json)")
    if h:
        check_fields(folder, run, persona, h, prior, fails, facts)
        check_text(folder, persona, fails)
    else:
        for d in REQ_DIMS_OLD:
            x = dims.get(d)
            if not isinstance(x, dict) or "value" not in x or not x.get("reason") or "confidence" not in x or not x.get("evidence"):
                fails.append(f"persona.dimensions.{d}: needs value, reason, confidence, evidence grade")
            elif x["confidence"] > (persona.get("completeness") or 1) + 1e-9:
                fails.append(f"persona.dimensions.{d}: confidence {x['confidence']} > completeness {persona.get('completeness')}")
        for d, x in dims.items():
            for c in (x.get("cites") or []) if isinstance(x, dict) else []:
                check_cite(folder, c, fails, f"dimensions.{d}")
        pace, pitch = (dims.get("pace") or {}).get("value"), (dims.get("pitch") or {}).get("value")
        if isinstance(pace, (int, float)) and not 0.85 <= pace <= 1.25:
            fails.append(f"pace {pace} outside 0.85-1.25")
        if isinstance(pitch, (int, float)) and not -0.3 <= pitch <= 0.3:
            fails.append(f"pitch {pitch} outside -0.3-0.3")
        for i, a in enumerate(persona.get("amendments") or []):
            if a.get("menu_item") not in AMEND_MENU:
                fails.append(f"amendments[{i}]: menu_item '{a.get('menu_item')}' not in the fixed menu {sorted(AMEND_MENU)}")
            if not a.get("cites"):
                fails.append(f"amendments[{i}]: no cites")
            for c in a.get("cites") or []:
                check_cite(folder, c, fails, f"amendments[{i}]")
        if pr.get("override") and not pr.get("override_reason"):
            fails.append("prior.override is true but override_reason is empty")

    # 2. hook decisions and guards
    rh = {x["id"]: x for x in review.get("hooks", [])}
    ctx_p = os.path.join(folder, "context.json")
    ctx = json.load(open(ctx_p, encoding="utf-8")) if os.path.exists(ctx_p) else {}
    calls = (((ctx.get("points") or {}).get("G00") or {}).get("value") or {}).get("calls", [])
    recent_call = any(c.get("days_ago") is not None and c["days_ago"] <= 90 for c in calls)
    reads = set()
    rl = os.path.join(run, "read_log.jsonl")
    if not h and os.path.exists(rl):
        for line in open(rl, encoding="utf-8"):
            try:
                reads.add(os.path.relpath(json.loads(line)["path"], folder).replace("\\", "/"))
            except Exception:
                pass
    for hid in facts.get("eligible_hooks", []):
        b = (rh.get(hid) or {}).get("B_agent")
        if not b or b.get("decision") not in ("primary", "backup", "rejected") or not b.get("reason"):
            fails.append(f"review: eligible {hid} needs a decision (primary/backup/rejected) with a reason")
            continue
        files = set()
        for c in (b.get("probe") or {}).get("cites", []):
            f = check_cite(folder, c, fails, f"review.{hid}")
            if f:
                files.add(f)
        if not h:
            pfiles = next((x["A_script"]["probe_files"] for x in facts.get("hooks", []) if x["id"] == hid), [])
            for pf in pfiles:
                ok = any(r.startswith(pf.rstrip("/")) for r in reads) if pf.endswith("/") else pf in reads
                if not ok and not (pf == "calls/" and not recent_call):
                    fails.append(f"review.{hid}: probe file '{pf}' was not read (read log)")
        if b["decision"] == "primary":
            if len((b.get("probe") or {}).get("cites", [])) < 3 or len(files) < 2:
                fails.append(f"review.{hid}: primary needs >= 3 cites from >= 2 files")
            if recent_call and not any(f.startswith("calls/") for f in files):
                fails.append(f"review.{hid}: primary needs a cite from calls/ (a VANI call in the last 90 days exists)")
            ce = b.get("counter_evidence") or {}
            if not (isinstance(ce, dict) and ce.get("text") and ce.get("cites")):
                fails.append(f"review.{hid}: primary needs counter_evidence with text and cites")
            else:
                for c in ce["cites"]:
                    check_cite(folder, c, fails, f"review.{hid}.counter_evidence")
    acked = {g.get("guard") for g in persona.get("guards_ack") or []}
    for gid in facts.get("true_guards", []):
        if gid not in acked:
            fails.append(f"guards_ack: true guard {gid} is not acknowledged")
    hk = persona.get("hook") or {}
    if hk.get("id") and hk["id"] not in facts.get("eligible_hooks", []):
        fails.append(f"hook {hk['id']} is not eligible for this seller")
    if h and hk.get("id"):
        prim = [x for x, r in rh.items() if (r.get("B_agent") or {}).get("decision") == "primary"]
        if prim and hk["id"] not in prim:
            fails.append(f"hook.id {hk['id']} is not the primary hook decided ({prim})")

    # money first
    if "hook.money_lead" in facts.get("eligible_hooks", []):
        in_facts = any("CL-" in (v.get("id") or "") for v in persona.get("verified_facts") or [])
        guard_reason = any("money" in (g.get("action") or "").lower() for g in persona.get("guards_ack") or [])
        if hk.get("id") != "hook.money_lead" and hk.get("backup") != "hook.money_lead" and not in_facts and not guard_reason:
            fails.append("money_lead is eligible: put it as hook/backup or in verified_facts (money first), or cite a guard reason")

    # 4. spoken text
    allowed_nums = set()
    for v in persona.get("verified_facts") or []:
        for n in NUM.findall(v.get("say") or ""):
            allowed_nums.add(n.replace(",", ""))
    g = (dims.get("voice_gender") or {}).get("value")
    g = {"female": "F", "male": "M"}.get(str(g).lower(), g)
    for where, t in spoken(persona):
        if h and wrong_honorific(t):
            fails.append(f"{where}: honorific '{wrong_honorific(t)}' does not belong to the language of this sentence")
        if BANNED.search(t):
            fails.append(f"{where}: banned word '{BANNED.search(t).group(0)}' (identity rule)")
        if g == "F" and MASC.search(t):
            fails.append(f"{where}: masculine first-person form '{MASC.search(t).group(0)}' with a female voice")
        if g == "M" and FEM.search(t):
            fails.append(f"{where}: feminine first-person form '{FEM.search(t).group(0)}' with a male voice")
        for n in NUM.findall(t):
            v = n.replace(",", "")
            try:
                big = float(v) > 60
            except ValueError:
                big = False
            if big and v not in allowed_nums:
                fails.append(f"{where}: number {n} is not in verified_facts")
    if persona.get("identity_line") and "indiamart" not in norm(persona["identity_line"]).replace(" ", "") \
            and "इंडियामार्ट" not in persona["identity_line"] and "इंडिया मार्ट" not in persona["identity_line"]:
        fails.append("identity_line must name IndiaMART")
    return fails


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--run", required=True)
    p = a.parse_args()
    fails = validate(p.folder, p.run)
    with open(os.path.join(p.run, "validation.json"), "w", encoding="utf-8") as f:
        json.dump({"pass": not fails, "failures": fails}, f, ensure_ascii=False, indent=1)
    if fails:
        print("VALIDATION FAILED (" + str(len(fails)) + "):\n- " + "\n- ".join(fails))
        raise SystemExit(1)
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
