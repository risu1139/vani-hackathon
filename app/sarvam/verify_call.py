"""verify_call.py: did every per-call setting TAKE EFFECT in a finished call? Read from Sarvam's own record (API key).

  python app/sarvam/verify_call.py --run data/runs_daytona/<id> --interaction-id <iid> [--switch-to Hindi]

Checks (PASS / FAIL per line, exit 1 on any FAIL):
  version     the call ran on the template version (agent.json template_version)
  variables   every variable of <run>/05_sarvam_vars.json arrived with the same value (else the API dropped it)
  opening     the first thing the agent said is persona_opening (OnStart set_initial_bot_message)
  language    the agent's first line is in persona_language (OnStart set_initial_language_name)
  tools       read_seller_signal ran on every seller turn
  switch      with --switch-to: read_seller_signal logged the switch and a later agent line is in that language
  booking     the seller named a time: book_meeting ran (meeting_fixed = yes)
Voice and pace are not in the API (the recording needs the console login): listen to the recording.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect_call as CC  # noqa: E402
import vani_tools as VT  # noqa: E402

AGENT = json.load(open(os.path.join(HERE, "agent.json"), encoding="utf-8"))
APP, TEMPLATE = AGENT["app_id"], AGENT.get("template_version")
RANGE = {"TELUGU": (0x0C00, 0x0C7F), "TAMIL": (0x0B80, 0x0BFF), "KANNADA": (0x0C80, 0x0CFF), "MALAYALAM": (0x0D00, 0x0D7F),
         "BENGALI": (0x0980, 0x09FF), "GUJARATI": (0x0A80, 0x0AFF), "PUNJABI": (0x0A00, 0x0A7F), "ODIA": (0x0B00, 0x0B7F),
         "DEVA": (0x0900, 0x097F)}
TIME_SAID = re.compile(r"(बजे|वाजता|గంటలకు|மணிக்கு|ಗಂಟೆಗೆ|વાગ્યે|টায়|മണിക്ക്|ਵਜੇ|ଟାରେ|\bfive\b|\bpm\b|\d)", re.I)


def lang_of(text):
    """Language of a line: by script; Hindi vs Marathi by common words (the same rule as the live tool)."""
    t = text or ""
    for lang, (lo, hi) in RANGE.items():
        if sum(lo <= ord(c) <= hi for c in t) >= 3:
            return (VT.deva_lang(t) or "HINDI/MARATHI").upper() if lang == "DEVA" else lang
    return "ENGLISH" if re.search(r"[A-Za-z]{3,}", t) else ""


def norm(t):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFC", t or "")).lower()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--interaction-id", required=True)
    a.add_argument("--switch-to", default="")
    p = a.parse_args()
    CC.load_env()
    want = json.load(open(os.path.join(p.run, "05_sarvam_vars.json"), encoding="utf-8"))
    now = datetime.now(timezone.utc)
    items = CC.list_interactions(APP, now - timedelta(hours=12), now + timedelta(minutes=5))
    it = next((x for x in items if x.get("interaction_id") == p.interaction_id), None)
    if not it:
        sys.exit(f"interaction {p.interaction_id} is not listed yet; retry in a minute")
    got = it.get("agent_variables") or {}
    turns = [t for t in CC.transcript(APP, p.interaction_id) if "error" not in t]
    text = lambda t: t.get("content") or t.get("text") or ""
    agent = [text(t) for t in turns if str(t.get("role")) in ("assistant", "agent", "bot")]
    seller = [text(t) for t in turns if str(t.get("role")) == "user"]
    res = []

    def check(name, ok, detail):
        res.append(bool(ok))
        print(f"[{'PASS' if ok else 'FAIL'}] {name:9s} {detail}")

    check("version", TEMPLATE is None or str(it.get("app_version")) in (str(TEMPLATE), "None"),
          f"app_version={it.get('app_version')} template={TEMPLATE}")
    diff = [k for k, v in want.items() if str(got.get(k, "")) != str(v)]
    check("variables", not diff, f"{len(want) - len(diff)}/{len(want)} arrived equal" + (f"; DIFFERENT OR MISSING: {diff}" if diff else ""))
    first = agent[0] if agent else ""
    check("opening", bool(first) and norm(want.get("persona_opening"))[:40] in norm(first),
          "first agent line = persona_opening" if first else "no agent line in the transcript")
    check("language", lang_of(first) == str(want.get("persona_language")).upper(),
          f"first agent line in {lang_of(first) or '?'}; wanted {want.get('persona_language')}")
    try:
        log = json.loads(got.get("switch_log") or "[]")
    except ValueError:
        log = []
    sig = [r for r in log if r.get("utt")]
    check("tools", len(seller) > 0 and len(sig) >= len(seller), f"read_seller_signal rows {len(sig)} for {len(seller)} seller turns")
    if p.switch_to:
        to = p.switch_to.upper()
        sw = [r for r in log if to.lower() in str(r.get("change")).lower() or to.lower() in str(r.get("reason")).lower()
              or r.get("to") == "language_switch"]
        later = [lang_of(x) for x in agent[2:]]
        check("switch", bool(sw) and to in later, f"switch rows {len(sw)}; agent languages after turn 1: {later}")
    if any(TIME_SAID.search(x) for x in seller):
        check("booking", str(got.get("meeting_fixed")).lower() == "yes",
              f"meeting_fixed={got.get('meeting_fixed')} slot={str(got.get('meeting_slot'))[:40]}")
    print("voice / pace: not in the API; listen to the recording")
    sys.exit(0 if all(res) else 1)


if __name__ == "__main__":
    main()
