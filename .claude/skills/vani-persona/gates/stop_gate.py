"""Stop hook: runs validate_persona.py; on failure blocks the stop ONCE with all failures in one message (peer lesson).
Always makes sure status.json exists."""
import json
import os
import subprocess
import sys

ev = json.load(sys.stdin)
run = os.environ.get("VANI_RUN")
if not run:
    sys.exit(0)
turn = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))
here = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, os.path.join(here, "..", "scripts", "validate_persona.py"), "--folder", turn["folder"], "--run", run],
                   capture_output=True, text=True)
status_p = os.path.join(run, "status.json")
if r.returncode != 0:
    if ev.get("stop_hook_active"):
        json.dump({"status": "error", "decision_id": turn["decision_id"], "note": "validation failed after one retry",
                   "failures": r.stdout[-3000:]}, open(status_p, "w", encoding="utf-8"), indent=1)
        sys.exit(0)
    print(json.dumps({"decision": "block", "reason": "The persona did not pass validation. Fix ALL of these, then stop again:\n" + r.stdout[-6000:]}))
    sys.exit(0)
if not os.path.exists(status_p):
    json.dump({"status": "done", "decision_id": turn["decision_id"], "note": "status written by gate"}, open(status_p, "w", encoding="utf-8"), indent=1)
sys.exit(0)
