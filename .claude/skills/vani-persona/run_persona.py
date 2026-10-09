"""run_persona.py: one trigger, one seller, end to end up to the Sarvam variables (orchestrator).

Steps: [facts.py] → [prior.py] → claude -p (Opus 5.5, the vani-persona skill, gates as hooks) → validate → compile_vars.
The agent sees only the pseudonymised export folder. Names are filled on premises by compile_vars from the export map.
Always writes <run>/status.json.

Usage (laptop):  python run_persona.py --folder data/agent_export/<pseudo> --names data/agent_export_maps/<pseudo>.json
Usage (Daytona): python3 run_persona.py --folder /home/daytona/contexts/<pseudo>   (names filled back on the laptop)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

SKILL = os.path.dirname(os.path.abspath(__file__))
MODEL = "claude-opus-5-5"
PY = sys.executable


def hooks_settings(run):
    g = lambda f: f'"{PY}" "{os.path.join(SKILL, "gates", f)}"'
    return {"hooks": {
        "PreToolUse": [{"matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash", "hooks": [{"type": "command", "command": g("pre_gate.py")}]}],
        "PostToolUse": [{"matcher": "Read|Grep|Glob|Bash", "hooks": [{"type": "command", "command": g("log_read.py")}]}],
        "Stop": [{"hooks": [{"type": "command", "command": g("stop_gate.py")}]}]}}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--names")
    a.add_argument("--runs", default=os.path.join("data", "runs"))
    a.add_argument("--decision-id")
    a.add_argument("--max-turns", default="60")
    p = a.parse_args()
    folder = os.path.abspath(p.folder)
    did = p.decision_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    run = os.path.abspath(os.path.join(p.runs, did))
    os.makedirs(run, exist_ok=True)
    status = {"decision_id": did, "status": "error", "model": MODEL}
    try:
        subprocess.run([PY, os.path.join(SKILL, "scripts", "facts.py"), "--folder", folder], check=True)
        subprocess.run([PY, os.path.join(SKILL, "scripts", "prior.py"), "--folder", folder, "--decision-id", did], check=True)
        shutil.copy(os.path.join(folder, "facts.json"), os.path.join(run, "01_facts.json"))
        shutil.copy(os.path.join(folder, "prior.json"), os.path.join(run, "03_prior.json"))
        json.dump({"decision_id": did, "folder": folder, "run": run}, open(os.path.join(run, "turn.json"), "w"), indent=1)
        json.dump(hooks_settings(run), open(os.path.join(run, "settings.json"), "w"), indent=1)
        env = dict(os.environ, VANI_RUN=run)
        prompt = (f"Use the vani-persona skill (read {os.path.join(SKILL, 'SKILL.md')} first and follow its steps exactly). "
                  f"Seller folder: {folder}. Run directory ($VANI_RUN): {run}. turn.json is in the run directory. "
                  f"Write 02_review.json, 04_persona.json and status.json in the run directory.")
        ver = subprocess.run(["claude", "--version"], capture_output=True, text=True, shell=os.name == "nt").stdout.strip()
        status["claude_version"] = ver
        t0 = time.time()
        r = subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--settings", os.path.join(run, "settings.json"),
                            "--permission-mode", "bypassPermissions", "--max-turns", p.max_turns,
                            "--add-dir", folder, "--add-dir", SKILL, "--output-format", "json"],
                           cwd=run, env=env, capture_output=True, text=True, shell=os.name == "nt", timeout=1800)
        status["agent_seconds"] = round(time.time() - t0)
        open(os.path.join(run, "agent_output.json"), "w", encoding="utf-8").write(r.stdout or "")
        open(os.path.join(run, "agent_stderr.txt"), "w", encoding="utf-8").write(r.stderr or "")
        agent_status = json.load(open(os.path.join(run, "status.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, "status.json")) else {}
        if agent_status.get("status") == "do_not_call":
            status.update(status="do_not_call", note="guard.do_not_call: no persona")
        else:
            v = subprocess.run([PY, os.path.join(SKILL, "scripts", "validate_persona.py"), "--folder", folder, "--run", run],
                               capture_output=True, text=True)
            status["validation"] = "pass" if v.returncode == 0 else "fail"
            if v.returncode == 0:
                cmd = [PY, os.path.join(SKILL, "scripts", "compile_vars.py"), "--run", run]
                if p.names:
                    cmd += ["--names", p.names]
                c = subprocess.run(cmd, capture_output=True, text=True)
                status.update(status="done" if c.returncode == 0 else "error", compile=(c.stdout or c.stderr)[-500:])
            else:
                status["failures"] = v.stdout[-3000:]
    except Exception as e:
        status["note"] = f"{type(e).__name__}: {str(e)[:300]}"
    json.dump(status, open(os.path.join(run, "status.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: status.get(k) for k in ("decision_id", "status", "validation", "agent_seconds", "claude_version")}))


if __name__ == "__main__":
    main()
