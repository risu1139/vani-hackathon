"""close_loop.py: one finished call -> both learning loops (between runs, never during a call).

  1. app/sarvam/collect_call.py   -> 06_call.json, 07_outcome.json (analytics API: transcript, switch_log, labels)
  2. app/loops/review_call.py     -> 08_review.json (frontier model; names replaced by tokens)
  3. loop2_update.py --run        -> persona and voice scoreboards (Loop 2)
  4. app/loops/loop1_propose.py   -> lexicon proposal over all reviewed runs (Loop 1; a human approves)

Usage: python app/loops/close_loop.py --interaction-id <id> [--names data/agent_export_maps/<pseudo>.json] [--test]
       (--test for smoke / demo calls: never into the real scoreboards)
       python app/loops/close_loop.py --run data/runs/<id> [--names ...]     (06/07 already collected)
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY = sys.executable
SKILL = os.path.join(ROOT, ".claude", "skills", "vani-persona", "scripts")


def step(name, cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    print(f"[{name}] exit={r.returncode} {(r.stdout or r.stderr).strip()[-400:]}")
    if r.returncode:
        raise SystemExit(f"{name} failed")
    return r.stdout


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--interaction-id")
    a.add_argument("--run")
    a.add_argument("--names")
    a.add_argument("--test", action="store_true", help="smoke / demo call: Loop 2 writes to data/scoreboards_test only")
    p = a.parse_args()
    run = p.run
    if p.interaction_id:
        out = step("collect", [PY, os.path.join(ROOT, "app", "sarvam", "collect_call.py"), "--interaction-id", p.interaction_id])
        # collect_call prints "<interaction id> -> data/runs/<decision_id> meeting_fixed=... rows=..."
        line = next((x for x in out.splitlines() if " -> " in x), "")
        run = run or (os.path.join(ROOT, line.split(" -> ")[1].split()[0]) if line else None)
    if not run or not os.path.exists(os.path.join(run, "07_outcome.json")):
        raise SystemExit("no run with 06_call.json / 07_outcome.json")
    review = [PY, os.path.join(ROOT, "app", "loops", "review_call.py"), "--run", run] + (["--names", p.names] if p.names else [])
    step("review", review)
    # test chats (console playground) never touch the real scoreboards
    import json
    test = p.test or json.load(open(os.path.join(run, "06_call.json"), encoding="utf-8")).get("channel") == "playground_text"
    boards = os.path.join(ROOT, "data", "scoreboards_test" if test else "scoreboards")
    step("loop2", [PY, os.path.join(SKILL, "loop2_update.py"), "--run", run, "--scoreboards", boards])
    step("loop1", [PY, os.path.join(ROOT, "app", "loops", "loop1_propose.py")])


if __name__ == "__main__":
    main()
