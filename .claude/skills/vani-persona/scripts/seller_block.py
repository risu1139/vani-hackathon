"""seller_block.py: the short seller block VANI reads during the call (plan 5d; variable prompt_seller).

Built by code from the frozen 01_facts.json and the validated 04_persona.json; no LLM writes it.
- Values and fixed labels only: never free seller text (complaint wording, catalogue text, call notes), which could
  carry instructions into the voice agent. Free strings that do appear (a city, a call outcome) are cut to safe characters.
- Every number comes from a state or trait value in 01_facts.json; lines() returns each line with its source cite.
- Cap 2,500 characters, counted after names are filled. Trim order: other-hook pointers (last first), then the named
  peers line, then trait lines. Fails only when the core (main hook, states, handler) alone is over the cap.
- Named peers (user rule 2026-10-10, switch references/policy.json peer_naming): name token, "paid IndiaMART seller",
  city, time on IndiaMART in words. No number ever sits in the peers line; group figures are said about the group.
"""
import json
import os
import re

CAP = 2500
HERE = os.path.dirname(os.path.abspath(__file__))
POLICY = os.path.join(HERE, "..", "references", "policy.json")
SAFE = re.compile(r"[^A-Za-z0-9 ,./()&+-]")
# allow-lists: a value not in its list is dropped (values only; never free text into the voice agent)
ALLOW = {"state.bl_usage": {"lapsed", "unused", "low_use", "active", "none"}, "state.enquiry_flow": {"rising", "falling", "flat"},
         "state.intent": {"not_interested", "wants_upgrade", "problem"}, "state.peer_position": {"ahead", "level", "behind"},
         "call_mood": {"rushed", "frustrated", "confused", "asked_if_bot", "grievance"},
         "trait.business_scale": {"small", "mid", "large"}, "trait.seller_type": {"manufacturer", "trader", "service"},
         "trait.city_tier": {"metro", "tier2", "small_town", "village"}, "trait.im_profile_strength": {"weak", "ok", "strong"}}
PHONE_EMAIL = re.compile(r"(\+?\d[\d\s-]{8,}\d)|([\w.+-]+@[\w-]+\.[\w.]+)")
UNIT = re.compile(r"[A-Za-z]{1,12}")
HOOK_LABEL = {"hook.profile_gap": "catalogue gaps", "hook.money_lead": "a live buy-lead", "hook.category_demand": "category demand",
              "hook.unused_credits": "unused buy-lead credits", "hook.lead_quality_fix": "lead quality",
              "hook.enquiry_drop": "falling enquiries", "hook.peer_usage": "same-size sellers", "hook.resolve_grievance": "open complaint"}


def policy():
    try:
        return json.load(open(POLICY, encoding="utf-8"))
    except (OSError, ValueError):
        return {"peer_naming": "off"}


def ok(kind, v):
    return isinstance(v, str) and v in ALLOW[kind]


def safe(x, n=40):
    return SAFE.sub("", str(x or "")).strip()[:n]


def num(x):
    try:
        f = float(x)
        return f"{f:.0f}" if f == int(f) else f"{f:.1f}"
    except (TypeError, ValueError):
        return None


def _v(items):
    """{id: value}, the agent's correction (B_agent) when there is one."""
    out = {}
    for it in items:
        b = it.get("B_agent") or {}
        out[it["id"]] = b.get("value") if isinstance(b, dict) and "value" in b else (it.get("A_script") or {}).get("value")
        out[it["id"] + "#detail"] = (it.get("A_script") or {}).get("detail") or {}
    return out


def state_lines(st):
    L = []
    u, d = st.get("state.bl_usage"), st.get("state.bl_usage#detail")
    if ok("state.bl_usage", u):
        parts = [f"{num(d.get(k))} {k}" for k in ("allotted", "lapsed", "balance") if num(d.get(k))]
        L.append((f"Buy-lead credits: {safe(u)}" + (f" ({', '.join(parts)})" if parts else "")
                  + (f"; last used {num(d['days_since_last_use'])} days ago" if num(d.get("days_since_last_use")) else ""), "state.bl_usage"))
    if st.get("state.bl_quality_issue") == "yes":
        L.append(("Has complained about lead quality: yes", "state.bl_quality_issue"))
    ef, d = st.get("state.enquiry_flow"), st.get("state.enquiry_flow#detail")
    if ok("state.enquiry_flow", ef):
        L.append((f"Enquiries: {safe(ef)}" + (f" ({num(d.get('last_week'))} last week, {num(d.get('last_month'))} last month)"
                                             if num(d.get("last_week")) and num(d.get("last_month")) else ""), "state.enquiry_flow"))
    pn = st.get("state.pns_flow") or {}
    if isinstance(pn, dict) and num(pn.get("received")):
        L.append((f"PNS calls: {num(pn.get('received'))} received, {num(pn.get('answered')) or 0} answered", "state.pns_flow"))
    moods = [k for k, v in (st.get("state.call_mood") or {}).items() if ok("call_mood", k) and isinstance(v, (int, float)) and v > 0]
    if moods:
        L.append((f"Earlier calls: seller was {', '.join(m.replace('_', ' ') for m in moods)}", "state.call_mood"))
    it = st.get("state.intent")
    if ok("state.intent", it):
        L.append((f"Last call result: {it.replace('_', ' ')}", "state.intent"))
    rc = st.get("state.recent_exec_contact") or {}
    if isinstance(rc, dict) and num(rc.get("days_since_exec_call")):
        L.append((f"Last IndiaMART executive call: {num(rc['days_since_exec_call'])} days ago", "state.recent_exec_contact"))
    cf = st.get("state.call_fatigue") or {}
    if isinstance(cf, dict) and (num(cf.get("vani_calls_30d")) not in (None, "0") or cf.get("asked_stop_calling")):
        L.append((f"Calls from us in 30 days: {num(cf.get('vani_calls_30d')) or 0}"
                  + ("; asked us to stop calling" if cf.get("asked_stop_calling") else ""), "state.call_fatigue"))
    L.append((f"Open complaint: {'yes' if st.get('state.open_grievance') == 'yes' else 'no'}", "state.open_grievance"))
    pp = st.get("state.peer_position") or {}
    if isinstance(pp, dict) and ok("state.peer_position", pp.get("seller_vs_peers")):
        L.append((f"Buy-lead use compared with same-size sellers: {pp['seller_vs_peers']}", "state.peer_position"))
    return L


def handler_line(st):
    if st.get("state.handler") == "person":
        return ("Handler: IndiaMART executive {SALES_EXEC} handles this account. If asked, say the name. "
                "Book the meeting with {SALES_EXEC}; when confirming, say the day and time with '{SALES_EXEC} aapse milenge'.", "state.handler")
    return ("Handler: the IndiaMART team handles this account (no person to name). If asked, say hamare IndiaMART executive "
            "will contact them.", "state.handler")


def trait_lines(tr):
    L = []
    pl = tr.get("trait.plan")
    if pl:
        L.append((f"Plan: {'paid' if str(pl).lower() == 'paid' else 'free'}", "trait.plan"))
    y = num(tr.get("trait.years_on_im"))
    if y:
        L.append((f"On IndiaMART: about {y} years", "trait.years_on_im"))
    for k, lab in (("trait.business_scale", "Business size"), ("trait.seller_type", "Seller type"), ("trait.city_tier", "City type")):
        if ok(k, tr.get(k)):
            L.append((f"{lab}: {tr[k].replace('_', ' ')}", k))
    d = tr.get("trait.im_profile_strength#detail") or {}
    if ok("trait.im_profile_strength", tr.get("trait.im_profile_strength")):
        extra = [f"{num(d.get(k))} {lab}" for k, lab in (("without_photo", "products without photo"), ("without_price", "without price"))
                 if num(d.get(k))]
        L.append((f"Catalogue: {tr['trait.im_profile_strength']}" + (f" ({', '.join(extra)})" if extra else ""), "trait.im_profile_strength"))
    return L


def peers_line(st):
    if policy().get("peer_naming") != "on":
        return None
    ps = [p for p in (st.get("state.peer_names") or []) if isinstance(p, dict) and re.fullmatch(r"\{COMPETITOR_\d+\}", str(p.get("token")))]
    if not ps:
        return None
    parts = [p["token"] + (", paid IndiaMART seller" if p.get("paid") else "") + (f", {p['city']}" if re.fullmatch(r"[A-Za-z .]{2,30}", str(p.get("city") or "")) else "")
             + (f", on IndiaMART {p['on_im']}" if p.get("on_im") else "") for p in ps]
    return ("Similar sellers nearby (say the name, paid, city; never a number about them): " + "; ".join(parts), "state.peer_names")


def pointer_lines(facts, main):
    by = {h["id"]: (h.get("A_script") or {}) for h in facts.get("hooks") or []}
    L = []
    for hid in facts.get("eligible_hooks") or []:
        if hid == main or hid not in by:
            continue
        fc = by[hid].get("facts_for_claim") or {}
        bits = []
        if hid == "hook.money_lead":
            lead = fc.get("lead") or {}
            # buyer text (product, city) is never copied: only numbers, a one-word unit and the order-value numbers
            q, unit = num(lead.get("quantity")), str(lead.get("unit") or "")
            vals = re.findall(r"\d[\d,]*", str(lead.get("order_value_text") or ""))[:2]
            bits = ["live lead in the seller's category (product: see facts)"]
            if q:
                bits.append(f"quantity {q}" + (f" {unit}" if UNIT.fullmatch(unit) else ""))
            if vals:
                bits.append("order value Rs " + " to ".join(vals))
        else:
            bits = [f"{k.replace('_', ' ')} {num(v)}" for k, v in fc.items() if num(v) is not None][:4]
            if hid == "hook.peer_usage":
                bits = [f"seller is {fc['seller_vs_peers']} of same-size sellers"] if ok("state.peer_position", fc.get("seller_vs_peers")) else []
        L.append((f"- {HOOK_LABEL.get(hid, hid)}: {'; '.join(bits) or 'see facts'}", hid))
    return L


def build(facts, persona, names=None):
    """(text, lines with cites). Names fill on the laptop; the cap counts the filled text."""
    st, tr = _v(facts.get("states") or []), _v(facts.get("traits") or [])
    main = (persona.get("hook") or {}).get("id")
    core = [(f"Main topic of this call: {HOOK_LABEL.get(main, main or 'see objective')}", "hook")] + state_lines(st) + [handler_line(st)]
    traits = trait_lines(tr)
    peer = peers_line(st)
    pointers = pointer_lines(facts, main)

    def render(tl, pe, po):
        out = ["About this seller (use when it helps; never read it out as a list):"] + [x for x, _ in core + tl]
        if pe:
            out.append(pe[0])
        if po:
            out += ["Other topics (only if the seller asks, or the main topic fails twice):"] + [x for x, _ in po]
        text = "\n".join(out)
        for k, v in (names or {}).items():
            text = text.replace(k, v)
        return text

    # trim order: pointers (last first), then the peers line, then trait lines
    po = list(pointers)
    while po and len(render(traits, peer, po)) > CAP:
        po.pop()
    pe = peer if len(render(traits, peer, po)) <= CAP else None
    tl = list(traits)
    while tl and len(render(tl, pe, po)) > CAP:
        tl.pop()
    text = render(tl, pe, po)
    if PHONE_EMAIL.search(text):
        raise SystemExit("REFUSED: seller block holds a phone number or an email")
    if len(text) > CAP:
        raise SystemExit(f"REFUSED: seller block core is {len(text)} characters, over the {CAP} cap")
    return text, core + tl + ([pe] if pe else []) + po
