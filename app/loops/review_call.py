"""review_call.py: after-call review by a frontier model (Opus 5.5 via `claude -p`) -> <run>/08_review.json.

Feeds both loops (plan §4-5):
- Loop 1 (switch): per seller turn, the true mode vs what read_seller_signal decided (correct / missed / wrong).
- Loop 2 (persona): persona fit per dimension, did the hook land, QA Fatal / Non-Fatal, outcome check.

Inputs in the run dir: 04_persona.json (tokens only), 06_call.json + 07_outcome.json (from app/sarvam/collect_call.py).
PII: real names in the transcript are replaced by the export-map tokens before anything is sent (data-sharing policy).

Usage: python app/loops/review_call.py --run data/runs/<id> [--names data/agent_export_maps/<pseudo>.json] [--dry-run]
"""
import argparse
import json
import os
import re
import subprocess

MODEL = "claude-opus-5-5"
MODES = ["neutral", "rushed", "frustrated", "confused", "interested", "bot_question", "opt_out", "language_switch"]
DIMS = ["voice_gender", "pace", "language_start", "code_mix", "formality", "warmth", "empathy", "sophistication", "words_per_turn"]
SCHEMA = {
    "turns": [{"turn": "int", "seller": "seller words (tokens kept)", "true_mode": "|".join(MODES),
               "tool_mode": "what read_seller_signal returned", "switch_verdict": "correct|missed|wrong|na",
               "reply_followed_directive": "true|false|null", "note": "short"}],
    "persona_fit": {"verdict": "good|too_long|too_formal|too_casual|wrong_language|too_pushy|too_fast|other",
                    "dimension_issues": [{"dimension": "|".join(DIMS), "now": "value used", "should_be": "better value",
                                          "evidence": "turn numbers + short quote"}]},
    "hook": {"landed": "true|false|not_reached", "evidence": "turn + quote"},
    "qa": {"fatal": ["said a banned word / an unverified number / claimed to be human / pushed after opt-out ..."],
           "non_fatal": ["..."]},
    "outcome_check": {"meeting_booked": "true|false", "agrees_with_sarvam_labels": "true|false", "note": "short"},
}


def tokens_from_map(path):
    """{original string: token}, longest first, from an export map (on premises)."""
    if not path:
        return []
    m = json.load(open(path, encoding="utf-8"))
    pairs = [(o, tok) for tok, origs in (m.get("tokens") or {}).items() for o in (origs if isinstance(origs, list) else [origs])
             if isinstance(o, str) and len(o) >= 3]
    return sorted(pairs, key=lambda p: -len(p[0]))


def scrub(text, pairs):
    for o, tok in pairs:
        text = re.sub(re.escape(o), tok, text, flags=re.I)
    return text


def build_prompt(run, pairs):
    persona = json.load(open(os.path.join(run, "04_persona.json"), encoding="utf-8"))
    call = json.load(open(os.path.join(run, "06_call.json"), encoding="utf-8"))
    outcome = json.load(open(os.path.join(run, "07_outcome.json"), encoding="utf-8"))
    dims = {d: ((persona.get("dimensions") or {}).get(d) or {}).get("value") for d in DIMS}
    brief = {"division": persona.get("division"), "style": (persona.get("prior") or {}).get("chosen"), "dimensions": dims,
             "hook": (persona.get("hook") or {}).get("claim"), "call_plan_goals": [s.get("goal") for s in persona.get("call_plan") or []],
             "verified_facts": [x.get("say") for x in persona.get("verified_facts") or []]}
    switch_rows = [{k: r.get(k) for k in ("turn", "utt", "to", "cue", "directive_id", "reason")} for r in call.get("switch_log") or []]
    body = json.dumps({"persona": brief, "transcript": call.get("transcript"), "switch_log": switch_rows,
                       "sarvam_labels": outcome.get("sarvam_labels"), "meeting_fixed": outcome.get("meeting_fixed")},
                      ensure_ascii=False, indent=1)
    return (
        "You review one finished call by VANI, IndiaMART's outbound voice agent. Its goal is a meeting with an IndiaMART "
        "executive. read_seller_signal is VANI's keyword switch: before each reply it labels the seller turn with a mode "
        f"({', '.join(MODES)}) and VANI must follow the directive for that mode.\n"
        "Judge strictly from the data below. For EVERY seller turn give the true mode and compare it with the tool's "
        "mode: correct, missed (true mode is not neutral, the tool said neutral or another mode), wrong (the tool switched "
        "but the true mode is different), na (no tool row). Then judge persona fit per dimension with evidence, whether "
        "the hook landed, and QA (fatal = banned word, unverified number, claim to be human, pushing after an opt-out, "
        "naming a buyer).\n"
        "Tokens such as {SELLER_NAME}, {COMPANY} and {EXEC_NAME} are names we removed for privacy before this review; "
        "on the call the real name was spoken. Never report a token as an unfilled placeholder.\n"
        f"Answer with ONE JSON object only, in this shape: {json.dumps(SCHEMA)}\n\nDATA:\n" + scrub(body, pairs))


def parse(out):
    try:
        res = json.loads(out).get("result", out)
    except (ValueError, AttributeError):
        res = out
    m = re.search(r"\{.*\}", res or "", re.S)
    if not m:
        raise ValueError("no JSON object in the model output")
    rev = json.loads(m.group(0))
    for k in ("turns", "persona_fit", "hook", "qa", "outcome_check"):
        if k not in rev:
            raise ValueError(f"review misses '{k}'")
    for t in rev["turns"]:
        if t.get("true_mode") not in MODES or t.get("switch_verdict") not in ("correct", "missed", "wrong", "na"):
            raise ValueError(f"bad turn row {t}")
    return rev


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--names")
    a.add_argument("--dry-run", action="store_true", help="write the prompt only; no model call")
    p = a.parse_args()
    prompt = build_prompt(p.run, tokens_from_map(p.names))
    if p.dry_run:
        open(os.path.join(p.run, "08_review_prompt.txt"), "w", encoding="utf-8").write(prompt)
        print(f"prompt written ({len(prompt)} chars)")
        return
    r = subprocess.run(["claude", "-p", "--model", MODEL, "--output-format", "json"], input=prompt, capture_output=True,
                       text=True, encoding="utf-8", shell=os.name == "nt", timeout=900)
    rev = parse(r.stdout)
    rev["model"] = MODEL
    json.dump(rev, open(os.path.join(p.run, "08_review.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    v = [t["switch_verdict"] for t in rev["turns"]]
    print(json.dumps({"turns": len(v), "missed": v.count("missed"), "wrong": v.count("wrong"),
                      "fit": rev["persona_fit"].get("verdict"), "fatal": len(rev["qa"].get("fatal") or [])}))


if __name__ == "__main__":
    main()
