"""validate_persona.py: the gate between the agent and Sarvam (S4). Pass/fail checks only; never judges the choice.

Checks (review B4, B5, M9, M14):
  1. persona.json has every required field (references/formats/persona.json).
  2. review.json has Part B for every eligible hook; the primary hook has >= 3 cites from >= 2 files, a cited
     counter_evidence, and a calls/ cite when there was a VANI call in the last 90 days; every true guard is acknowledged.
  3. Every cite exists in the seller folder and its quote (<= 20 words) appears in that file.
  4. Probe files of each decided hook appear in the read log (written by the PostToolUse hook, not by the agent).
  5. Spoken text: no banned words (AI, bot, branch/account manager, personally ...); first-person verb forms agree with
     the voice gender; numbers above 60 only if they appear in verified_facts; identity line names IndiaMART.
  6. money_lead: if eligible, it must be the hook or the backup or in verified_facts, unless a guard acknowledgement cites why.
  7. do_not_call guard → no persona may exist. Ranges for pace / pitch. Confidence <= completeness.

Usage: python3 validate_persona.py --folder <seller folder> --run <run dir>
Writes <run>/validation.json and exits 1 on any failure (all failures in one message).
"""
import argparse
import glob
import json
import os
import re

REQ_DIMS = ["voice_gender", "voice_id", "pace", "pitch", "language_start", "code_mix", "accent", "formality", "warmth",
            "empathy", "sophistication", "words_per_turn"]
REQ_TOP = ["decision_id", "division", "prior", "dimensions", "personalisation", "hook", "opening", "identity_line", "call_plan",
           "objection_playbook", "escalation_rules", "guardrails", "verified_facts", "switch_sensitivity", "guards_ack",
           "amendments", "overall_confidence", "completeness"]
BANNED = re.compile(r"\b(AI|A\.I\.|artificial intelligence|bot|robot|chatbot|branch manager|account manager|personally|"
                    r"main khud|khud aa(unga|ungi)|एआई|बॉट|रोबोट|ब्रांच मैनेजर|अकाउंट मैनेजर)\b", re.I)
MASC = re.compile(r"(raha hoon|rahaa hoon|karta hoon|bol raha|aaya hoon|gaya hoon|sakta hoon|रहा हूँ|रहा हूं|करता हूँ|करता हूं|सकता हूँ|सकता हूं|बोल रहा)", re.I)
FEM = re.compile(r"(rahi hoon|karti hoon|bol rahi|aayi hoon|gayi hoon|sakti hoon|रही हूँ|रही हूं|करती हूँ|करती हूं|सकती हूँ|सकती हूं|बोल रही)", re.I)
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
AMEND_MENU = {"pace_up", "pace_down", "pitch_up", "pitch_down", "more_formal", "less_formal", "warmer", "briefer", "longer",
              "language_switch", "code_mix_more", "code_mix_less", "simpler", "more_numbers", "voice_gender_flip", "hook_swap"}


def norm(t):
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


def file_for(folder, cid):
    path = cid.split("#")[0]
    if path.startswith("calls/") and not path.endswith(".md"):
        m = glob.glob(os.path.join(folder, "calls", os.path.basename(path) + "_*.md"))
        return m[0] if m else None
    p = os.path.join(folder, path)
    return p if os.path.exists(p) else None


def check_cite(folder, c, fails, where):
    cid, quote = (c.get("id") if isinstance(c, dict) else c), (c.get("quote") if isinstance(c, dict) else None)
    f = file_for(folder, cid or "")
    if not f:
        fails.append(f"{where}: cite '{cid}' does not exist in the seller folder")
        return None
    text = open(f, encoding="utf-8").read()
    anchor = cid.split("#", 1)[1] if "#" in cid else None
    if anchor and anchor not in text:
        fails.append(f"{where}: cite '{cid}': id '{anchor}' not found in {os.path.basename(f)}")
    if not quote:
        fails.append(f"{where}: cite '{cid}' has no quote")
    elif len(quote.split()) > 20:
        fails.append(f"{where}: cite '{cid}' quote is longer than 20 words")
    elif norm(quote) not in norm(text):
        fails.append(f"{where}: cite '{cid}' quote not found in {os.path.basename(f)}")
    return os.path.relpath(f, folder).replace("\\", "/")


def spoken(persona):
    out = [("opening", persona.get("opening")), ("identity_line", persona.get("identity_line")),
           ("hook.claim", (persona.get("hook") or {}).get("claim"))]
    out += [(f"call_plan[{i}]", s.get("say")) for i, s in enumerate(persona.get("call_plan") or [])]
    out += [(f"objection[{i}]", o.get("response")) for i, o in enumerate(persona.get("objection_playbook") or [])]
    return [(k, v) for k, v in out if v]


def validate(folder, run):
    fails = []
    facts = json.load(open(os.path.join(folder, "facts.json"), encoding="utf-8"))
    dnc = "guard.do_not_call" in facts.get("true_guards", [])
    ppath = os.path.join(run, "04_persona.json")
    if dnc:
        if os.path.exists(ppath):
            fails.append("guard.do_not_call is true but a persona was written: write status do_not_call only")
        return fails
    if not os.path.exists(ppath):
        return ["04_persona.json missing"]
    persona = json.load(open(ppath, encoding="utf-8"))
    review = json.load(open(os.path.join(run, "02_review.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, "02_review.json")) else {}
    reads = set()
    rl = os.path.join(run, "read_log.jsonl")
    if os.path.exists(rl):
        for line in open(rl, encoding="utf-8"):
            try:
                reads.add(os.path.relpath(json.loads(line)["path"], folder).replace("\\", "/"))
            except Exception:
                pass

    # 1. fields
    for k in REQ_TOP:
        if k not in persona:
            fails.append(f"persona: missing field '{k}'")
    dims = persona.get("dimensions") or {}
    for d in REQ_DIMS:
        x = dims.get(d)
        if not isinstance(x, dict) or "value" not in x or not x.get("reason") or "confidence" not in x or not x.get("evidence"):
            fails.append(f"persona.dimensions.{d}: needs value, reason, confidence, evidence grade")
        elif x["confidence"] > (persona.get("completeness") or 1) + 1e-9:
            fails.append(f"persona.dimensions.{d}: confidence {x['confidence']} > completeness {persona.get('completeness')}")
    for d, x in dims.items():
        for c in (x.get("cites") or []) if isinstance(x, dict) else []:
            check_cite(folder, c, fails, f"dimensions.{d}")
    pace = (dims.get("pace") or {}).get("value")
    pitch = (dims.get("pitch") or {}).get("value")
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
    pr = persona.get("prior") or {}
    if pr.get("chosen") not in (pr.get("top2") or []) and not pr.get("override"):
        fails.append("prior.chosen is not one of top2 and override is false")
    if pr.get("override") and not pr.get("override_reason"):
        fails.append("prior.override is true but override_reason is empty")

    # 2. hook decisions and guards
    rh = {h["id"]: h for h in review.get("hooks", [])}
    ctx = json.load(open(os.path.join(folder, "context.json"), encoding="utf-8"))
    calls = (((ctx.get("points") or {}).get("G00") or {}).get("value") or {}).get("calls", [])
    recent_call = any(c.get("days_ago") is not None and c["days_ago"] <= 90 for c in calls)
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
        probe = next((h["A_script"]["probe_files"] for h in facts["hooks"] if h["id"] == hid), [])
        for pf in probe:
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
    if (persona.get("hook") or {}).get("id") and persona["hook"]["id"] not in facts.get("eligible_hooks", []):
        fails.append(f"hook {persona['hook']['id']} is not eligible for this seller")

    # 6. money first
    if "hook.money_lead" in facts.get("eligible_hooks", []):
        h = persona.get("hook") or {}
        in_facts = any("CL-" in (v.get("id") or "") for v in persona.get("verified_facts") or [])
        guard_reason = any("money" in (g.get("action") or "").lower() for g in persona.get("guards_ack") or [])
        if h.get("id") != "hook.money_lead" and h.get("backup") != "hook.money_lead" and not in_facts and not guard_reason:
            fails.append("money_lead is eligible: put it as hook/backup or in verified_facts (money first), or cite a guard reason")

    # 5. spoken text
    allowed_nums = set()
    for v in persona.get("verified_facts") or []:
        for n in NUM.findall(v.get("say") or ""):
            allowed_nums.add(n.replace(",", ""))
    g = (dims.get("voice_gender") or {}).get("value")
    for where, t in spoken(persona):
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
