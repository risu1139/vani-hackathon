"""rule_checks.py: post-call checks of the call rules (plan 5f, .claude/skills/vani-persona/references/call_rules.json)
on one finished call, without an LLM -> <run>/08_rules.json. Each rule: pass | fail | unknown, the turns, the language.

  python app/loops/rule_checks.py --run data/runs_daytona/<id>        (needs 06_call.json from collect_call.py)

Checks that need no judgement (R1 and R4 are scored by review_call.py, the Opus review):
  R2 meeting-pace  a VANI turn that asks for the meeting (meeting / day / time words + a question) must not follow
                   another asking turn, nor answer a seller question (unless the seller showed interest or named a time)
  R3 no-repeat     the same number in 2+ VANI turns, unless the seller asked for it again in between
  R5 close-with-care  the agent ended the call: after a meeting was booked (or at the end), VANI must have asked
                   'anything else' and the seller must have answered; exceptions: opt-out, the seller ended the call
'unknown' when the words for a check do not cover the call's language (never a silent 'pass').
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "app", "sarvam"))
import vani_tools as VT  # noqa: E402  (time_mention, classify: the same words the live tool uses)

MEET = re.compile(r"(?<![a-z])(meeting|milein|milna|milte|mil sakte|executive|tomorrow|kal|subah|shaam)(?![a-z])|"
                  r"मीटिंग|मिलें|मिलना|मिल सकते|मिलेंगे|कल|सुबह|शाम|भेट|उद्या|सकाळी|संध्याकाळी|"
                  r"మీటింగ్|రేపు|ఉదయం|సాయంత్రం|மீட்டிங்|நாளை|காலை|மாலை|ಮೀಟಿಂಗ್|ನಾಳೆ|ಬೆಳಿಗ್ಗೆ|ಸಂಜೆ|"
                  r"મીટિંગ|કાલે|সকাল|মিটিং|ਮੀਟਿੰਗ|ਕੱਲ੍ਹ", re.I)
ASKISH = re.compile(r"[?？]|(?<![a-z])(kya|ya|or|which)(?![a-z])|या|किंवा|లేదా|அல்லது|ಅಥವಾ|અથવા|নাকি|ਜਾਂ", re.I)
ELSE = re.compile(r"anything else|aur kuch|aur koi|और कुछ|और कोई|अजून काही|आणखी काही|ఇంకేమైనా|ఇంకా ఏమైనా|வேறு ஏதாவது|"
                  r"ಬೇರೆ ಏನಾದರೂ|മറ്റെന്തെങ്കിലും|બીજું કંઈ|আর কিছু|ਹੋਰ ਕੁਝ", re.I)
COVERED = {"hindi", "english", "marathi", "telugu", "tamil", "kannada", "gujarati", "bengali", "punjabi"}
NUM = re.compile(r"\d[\d,]*")


def nums(t):
    return {n.replace(",", "") for n in NUM.findall(t or "") if len(n.replace(",", "")) >= 2}  # skip 1-digit counts


def check(call):
    tr = [m for m in call.get("transcript") or [] if m.get("role") in ("assistant", "user")]
    lang = str(call.get("language_name") or "").lower()
    covered = lang in COVERED or not lang
    log = call.get("switch_log") or []
    opted = any(r.get("to") == "opt_out" for r in log)
    booked = str((call.get("agent_variables") or {}).get("meeting_fixed")).lower() == "yes"
    out = {}

    # R2: asks in a row, or an ask right after a seller question
    asks, bad = [], []
    prev_ask = False
    for i, m in enumerate(tr):
        t = m.get("content") or ""
        if m["role"] == "user":
            continue
        ask = bool(MEET.search(t) and ASKISH.search(t)) and not ELSE.search(t)  # a closing 'anything else' turn is not an ask
        seller = tr[i - 1].get("content") if i and tr[i - 1]["role"] == "user" else ""
        smode = VT.classify(seller)[0] if seller else "neutral"
        granted = smode == "interested" or bool(VT.time_mention(seller or ""))
        if ask:
            asks.append(i)
            if not granted and (prev_ask or smode == "question"):
                bad.append(i)
        prev_ask = ask
    out["R2"] = {"result": "fail" if bad else ("pass" if covered else "unknown"), "asks": len(asks),
                 "vani_turns": sum(m["role"] == "assistant" for m in tr), "bad_turns": bad}

    # R3: the same number in 2+ VANI turns, unless the seller said it (asked again) in between
    first, rep = {}, []
    for i, m in enumerate(tr):
        if m["role"] != "assistant":
            continue
        for n in nums(m.get("content")):
            if n in first:
                between = " ".join(x.get("content") or "" for x in tr[first[n] + 1:i] if x["role"] == "user")
                if n not in nums(between):
                    rep.append({"number": n, "turns": [first[n], i]})
            first.setdefault(n, i)
    out["R3"] = {"result": "fail" if rep else ("pass" if first or covered else "unknown"), "repeats": rep}

    # R5: the agent ended the call -> an 'anything else' question answered by the seller, unless an exception
    ended = call.get("ended_by")
    if opted or ended != "AGENT_ENDS":
        out["R5"] = {"result": "pass", "why": "exception: " + ("opt-out" if opted else f"ended_by={ended}")}
    else:
        idx = [i for i, m in enumerate(tr) if m["role"] == "assistant" and ELSE.search(m.get("content") or "")]
        answered = any(any(x["role"] == "user" for x in tr[i + 1:]) for i in idx)
        out["R5"] = {"result": "pass" if answered else ("fail" if covered else "unknown"), "booked": booked,
                     "asked_anything_else_at": idx}
    for k in out:
        out[k]["language"] = lang or "?"
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    p = a.parse_args()
    call = json.load(open(os.path.join(p.run, "06_call.json"), encoding="utf-8"))
    res = {"rules_version": json.load(open(os.path.join(ROOT, ".claude", "skills", "vani-persona", "references", "call_rules.json"),
                                           encoding="utf-8"))["version"], "interaction_id": call.get("interaction_id"),
           "rules": check(call)}
    json.dump(res, open(os.path.join(p.run, "08_rules.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v["result"] for k, v in res["rules"].items()}))


if __name__ == "__main__":
    main()
