"""Stop hook: refuses the stop ONCE with every failure in one numbered message (max 6 shown, each with its fix).
On the second stop (stop_hook_active) it allows at once; the launcher validates again after the turn and never
trusts the agent's status. Any error inside the gate = allow (the launcher is the backstop).

Checks: do_not_call → no persona; otherwise persona_tool finalize ran, 04/02 equal the finalize sha (no hand edit
after finalize), and validate_persona passes. Touches <run>/.stop_gate_fired when it refuses (launch self-test).
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.abspath(os.path.join(HERE, ".."))
TOOL = os.path.join(SKILL, "scripts", "persona_tool.py")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def failures(run):
    turn = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))
    if turn.get("selftest"):
        return ["self-test: the stop gate is active"]
    facts = json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))
    p04, p02 = os.path.join(run, "04_persona.json"), os.path.join(run, "02_review.json")
    if "guard.do_not_call" in facts.get("true_guards", []):
        return ["guard.do_not_call is true: leave the files as they are and write $VANI_RUN/status.json = {\"status\": \"do_not_call\"}; the launcher discards the persona and makes no call"] if os.path.exists(p04) else []
    fin = None
    lp = os.path.join(run, "ledger.jsonl")
    if os.path.exists(lp):
        for line in open(lp, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") == "finalize":
                fin = r
    fix = f"\"$VANI_PY\" {os.path.abspath(TOOL)}"
    if not fin:
        return [f"the persona is not finalized. Run: {fix} status, finish the missing steps, then {fix} finalize"]
    out = []
    if sha(p04) != fin.get("sha04") or sha(p02) != fin.get("sha02"):
        out.append(f"04_persona.json / 02_review.json changed after finalize. Run {fix} finalize again (never edit them by hand)")
    pyf = [] if os.name == "nt" else ["-E", "-s"]  # ignore PYTHON* env and the user site dir (planted .pth files)
    r = subprocess.run([sys.executable] + pyf + [os.path.join(SKILL, "scripts", "validate_persona.py"), "--folder", turn["folder"],
                        "--run", run], capture_output=True, text=True, encoding="utf-8", timeout=150)
    if r.returncode != 0:
        out += [ln[2:] for ln in r.stdout.splitlines() if ln.startswith("- ")] or [r.stdout[-500:] or r.stderr[-500:]]
    return out


def main():
    try:
        ev = json.load(sys.stdin)
        run = os.environ.get("VANI_RUN")
        if not run or ev.get("stop_hook_active"):
            return 0
        fails = failures(run)
    except Exception:
        return 0
    if not fails:
        return 0
    try:
        open(os.path.join(run, ".stop_gate_fired"), "a").close()
    except OSError:
        pass
    shown = [f"{i}. {f}" for i, f in enumerate(fails[:6], 1)]
    if len(fails) > 6:
        shown.append(f"... and {len(fails) - 6} more (all are printed by persona_tool.py finalize)")
    print(json.dumps({"decision": "block", "reason": "Not done. Fix ALL of these now; this gate asks only once:\n" + "\n".join(shown)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
