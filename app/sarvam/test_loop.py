"""test_loop.py: short scripted SDK calls (about 1 minute each), one per call-rule fix, each checked in this order:
  1. verify_call.py   the per-call variables arrived (21/22 equal), opening, language: if this fails, nothing else counts
  2. collect_call.py  the call record into data/test_loop/<scenario>/
  3. rule_checks.py   R2 / R3 / R5 on the transcript, plus the scenario's own expectation

  python app/sarvam/test_loop.py --run data/runs_daytona/<id> [--scenarios questions,handler,...]
Writes data/test_loop/summary.json. Uses Sarvam credits (one SDK call per scenario).
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
sys.path.insert(0, os.path.join(ROOT, "app", "sarvam"))
from voice_smoke import SCENARIOS  # noqa: E402

# what each scenario must show besides the rule checks (read from the switch log and the variables)
EXPECT = {
    "questions": "no meeting ask right after a seller question (R2 pass)",
    "handler": "the handler line is said; no repeated dodge",
    "decline_then_book": "the call stays open after 'nahi chahiye'; meeting booked; 'anything else' before the end (R5 pass)",
    "explicit_end": "the call ends politely after the explicit request (opt_out)",
    "telugu_questions": "Telugu questions answered, no ask after them (R2 pass)",
    "switch_rushed": "mode rushed on turn 2; short reply, callback offered; no pitch",
    "switch_frustrated": "mode frustrated on turn 2; apology first, pitch stopped; stays frustrated through the question",
    "switch_confused": "mode confused; simpler words, one idea",
    "switch_bot": "bot_question then bot_question_pressed: sidestep, then 'virtual assistant', never human",
    "switch_language": "replies follow Marathi -> Hindi -> English on the same turn",
}


def run(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=ENV, cwd=ROOT, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--scenarios", default=",".join(SCENARIOS))
    a.add_argument("--check-only", default="", help="scenario=interaction_id: check an earlier call, place no new call")
    p = a.parse_args()
    summary = []
    todo = [p.check_only.split("=", 1)[0]] if p.check_only else p.scenarios.split(",")
    for sc in todo:
        if p.check_only:
            out = "INTERACTION " + p.check_only.split("=", 1)[1]
        else:
            rc, out = run([PY, "app/sarvam/voice_smoke.py", "--run", p.run, "--scenario", sc])
        iid = next((ln.split()[-1] for ln in out.splitlines() if ln.startswith("INTERACTION")), None)
        row = {"scenario": sc, "expect": EXPECT.get(sc), "interaction": iid}
        if not iid or iid == "None":
            row["error"] = out[-300:]
            summary.append(row)
            print(json.dumps(row, ensure_ascii=False))
            continue
        for attempt in range(10):  # analytics lists the call some time after it ends
            time.sleep(20)
            rc, vout = run([PY, "app/sarvam/verify_call.py", "--run", p.run, "--interaction-id", iid])
            if "not listed yet" not in vout:
                break
        row["verify"] = [ln for ln in vout.splitlines() if ln.startswith("[")]
        row["variables_ok"] = any(ln.startswith("[PASS] variables") for ln in row["verify"])
        out_dir = os.path.join(ROOT, "data", "test_loop", sc)
        rc, cout = run([PY, "app/sarvam/collect_call.py", "--interaction-id", iid, "--hours", "2", "--out", out_dir])
        line = next((x for x in cout.splitlines() if " -> " in x), "")
        rdir = os.path.join(ROOT, line.split(" -> ")[1].split()[0]) if line else ""
        if rdir and os.path.exists(os.path.join(rdir, "06_call.json")):
            rc, rout = run([PY, "app/loops/rule_checks.py", "--run", rdir])
            rp = os.path.join(rdir, "08_rules.json")  # read the file: stdout carries library warnings too
            row["rules"] = {k: v["result"] for k, v in json.load(open(rp, encoding="utf-8"))["rules"].items()}                 if rc == 0 and os.path.exists(rp) else rout[-200:]
            call = json.load(open(os.path.join(rdir, "06_call.json"), encoding="utf-8"))
            row["ended_by"] = call.get("ended_by")
            row["meeting_fixed"] = (call.get("agent_variables") or {}).get("meeting_fixed")
            row["modes"] = [(r.get("overlay") or r.get("to"), r.get("ask_ok")) for r in call.get("switch_log") or []]
            row["transcript"] = [(m.get("role"), (m.get("content") or "")[:140]) for m in call.get("transcript") or []]
        summary.append(row)
        print(json.dumps({k: row.get(k) for k in ("scenario", "interaction", "variables_ok", "rules", "ended_by", "meeting_fixed", "modes")},
                         ensure_ascii=False), flush=True)
    os.makedirs(os.path.join(ROOT, "data", "test_loop"), exist_ok=True)
    path = os.path.join(ROOT, "data", "test_loop", "summary.json")
    old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    keep = [r for r in old if r.get("scenario") not in {x["scenario"] for x in summary}]
    json.dump(keep + summary, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
