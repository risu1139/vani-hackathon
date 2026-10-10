"""run_persona.py: one trigger, one seller, end to end up to the Sarvam variables (the launcher).

Enforcement plan §5a (reviewed and approved by the Redash peer, 2026-10-10). The launcher trusts nothing the agent
writes: it re-validates after the turn, with its own hash-checked copy of the skill, and writes status.json on every
exit path.

  1. A unique run dir; every gate input cleared. status.json = error until proven otherwise (try/finally).
  2. Launcher copy of the skill OUTSIDE the run dir (data/launcher/<id>/skill) + its sha. The agent and the hooks use
     this copy; the post-turn validator runs only if the copy is unchanged.
  3. Frozen seller copy <run>/seller (facts.py and prior.py run on it) -> 01_facts.json, 03_prior.json; shas.
  4. Settings OUTSIDE the run dir, read-only: PreToolUse + Stop hooks with timeouts; --setting-sources "" (no
     project/user settings), --strict-mcp-config with an empty config, no web tools, sandbox CLAUDE.md appended.
  5. Self-test on EVERY launch (cheap model): the pre gate and the stop gate must both fire. Else: error, no run.
  6. The turn: claude -p (pinned model, no shell, the process tree is killed on timeout); one retry only if no
     assistant output came. The model is checked in the output's modelUsage.
  7. After the turn: the skill copy, 01/03 and the seller copy are unchanged; do_not_call from 01_facts (never from
     the agent); 04/02 equal the finalize sha; the validator passes -> compile_vars -> status done. Any failure:
     status error with the reason, and NO Sarvam variables.
Exit code 0 = the launcher finished its own work (read status.json for the result); 1 = the launcher itself failed.

Usage: python run_persona.py --folder data/agent_export/<pseudo> --names data/agent_export_maps/<pseudo>.json
Tests: VANI_CLAUDE=<stub.py> replaces the claude binary.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
import uuid

SKILL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SKILL, "..", "..", ".."))
MODEL = "claude-opus-5-5"
SELFTEST_MODEL = "claude-haiku-4-5-20251001"
CLI_TESTED = {"2.1.292", "2.1.296"}
PY = sys.executable
GATE_INPUTS = ["status.json", "ledger.jsonl", "02_review.json", "04_persona.json", "draft_text.json", "validation.json",
               "05_sarvam_vars.json", "06_sarvam_prompt.md", ".pre_gate_fired", ".stop_gate_fired", "agent_output.json"]


def tree_sha(path, skip=("__pycache__",)):
    h = hashlib.sha256()
    for base, dirs, files in sorted(os.walk(path)):
        dirs[:] = sorted(d for d in dirs if d not in skip)
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            h.update(os.path.relpath(p, path).replace("\\", "/").encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()


def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def claude_cmd():
    c = os.environ.get("VANI_CLAUDE")
    if c:
        return [PY, c] if c.endswith(".py") else [c]
    p = shutil.which("claude")
    if not p:
        raise RuntimeError("claude CLI not found")
    return [p]


def kill_tree(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_claude(args, cwd, env, timeout):
    proc = subprocess.Popen(claude_cmd() + args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        out, err = proc.communicate()
        return 124, out or "", (err or "") + "\nTIMEOUT"
    return proc.returncode, out or "", err or ""


def settings(skill, ldir):
    g = lambda f: f'"{PY}" "{os.path.join(skill, "gates", f)}"'
    s = {"hooks": {
        "PreToolUse": [{"matcher": "Write|Edit|MultiEdit|NotebookEdit", "hooks": [{"type": "command", "command": g("pre_gate.py"), "timeout": 10}]}],
        "Stop": [{"hooks": [{"type": "command", "command": g("stop_gate.py"), "timeout": 180}]}]}}
    p = os.path.join(ldir, "settings.json")
    json.dump(s, open(p, "w", encoding="utf-8"), indent=1)
    mcp = os.path.join(ldir, "empty_mcp.json")
    json.dump({"mcpServers": {}}, open(mcp, "w", encoding="utf-8"))
    for f in (p, mcp):
        os.chmod(f, stat.S_IREAD)
    return p, mcp


def base_args(skill, sfile, mcp, model, run, max_turns):
    return ["-p", "--model", model, "--settings", sfile, "--setting-sources", "", "--strict-mcp-config", "--mcp-config", mcp,
            "--disallowedTools", "WebFetch", "WebSearch", "TodoWrite",
            "--append-system-prompt-file", os.path.join(skill, "sandbox", "CLAUDE.md"),
            "--add-dir", run, "--add-dir", skill, "--permission-mode", "bypassPermissions",
            "--max-turns", str(max_turns), "--output-format", "json"]


def selftest(skill, sfile, mcp, ldir):
    """Both gates must fire on a cheap launch. Returns '' if ok, else the reason."""
    st = os.path.join(ldir, "selftest")
    os.makedirs(st, exist_ok=True)
    for f in (".pre_gate_fired", ".stop_gate_fired"):
        if os.path.exists(os.path.join(st, f)):
            os.remove(os.path.join(st, f))
    json.dump({"decision_id": "selftest", "folder": st, "run": st, "selftest": True}, open(os.path.join(st, "turn.json"), "w", encoding="utf-8"))
    env = dict(os.environ, VANI_RUN=st, VANI_PY=PY, PYTHONIOENCODING="utf-8")
    prompt = f"Self-test. Use the Write tool to create {os.path.join(st, '04_persona.json')} with the text {{}}. Then reply DONE and stop."
    args = base_args(skill, sfile, mcp, SELFTEST_MODEL, st, 4)
    args.insert(1, prompt)
    rc, out, err = run_claude(args, st, env, 300)
    missing = [f for f in (".pre_gate_fired", ".stop_gate_fired") if not os.path.exists(os.path.join(st, f))]
    return f"self-test: hooks did not fire ({', '.join(missing)}); rc={rc}; {err[-300:]}" if missing else ""


def output_ok(out):
    try:
        j = json.loads(out)
    except ValueError:
        return None, "no JSON output"
    if not j.get("num_turns") and not j.get("result"):
        return j, "no assistant output"
    return j, ""


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--names")
    a.add_argument("--runs", default=os.path.join(ROOT, "data", "runs"))
    a.add_argument("--decision-id")
    a.add_argument("--max-turns", default="120")
    a.add_argument("--timeout", type=int, default=2400)
    p = a.parse_args()
    did = p.decision_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    run = os.path.abspath(os.path.join(p.runs, did))
    ldir = os.path.abspath(os.path.join(os.environ.get("VANI_LAUNCHER_DIR") or os.path.join(ROOT, "data", "launcher"), did))
    os.makedirs(run, exist_ok=True)
    status = {"decision_id": did, "status": "error", "model": MODEL, "reason": "launcher did not finish"}
    rc_launcher = 1
    try:
        for f in GATE_INPUTS:
            if os.path.exists(os.path.join(run, f)):
                os.remove(os.path.join(run, f))
        # 2. launcher copy of the skill (outside the run dir)
        if os.path.exists(ldir):
            shutil.rmtree(ldir, onerror=lambda fn, pth, e: (os.chmod(pth, stat.S_IWRITE), fn(pth)))
        skill = os.path.join(ldir, "skill")
        shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns("__pycache__", "tests", "*.pyc"))
        status["skill_sha"] = skill_sha = tree_sha(skill)
        # 3. frozen seller copy, facts and prior on it
        seller = os.path.join(run, "seller")
        if os.path.exists(seller):
            shutil.rmtree(seller)
        shutil.copytree(os.path.abspath(p.folder), seller)
        boards = os.environ.get("VANI_SCOREBOARDS") or os.path.join(ROOT, "data", "scoreboards")
        for script, extra in (("facts.py", []), ("prior.py", ["--decision-id", did, "--scoreboards", boards])):
            r = subprocess.run([PY, os.path.join(skill, "scripts", script), "--folder", seller] + extra, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            if r.returncode:
                raise RuntimeError(f"{script} failed: {r.stderr[-400:]}")
        shutil.copy(os.path.join(seller, "facts.json"), os.path.join(run, "01_facts.json"))
        shutil.copy(os.path.join(seller, "prior.json"), os.path.join(run, "03_prior.json"))
        shas = {"01": fsha(os.path.join(run, "01_facts.json")), "03": fsha(os.path.join(run, "03_prior.json")), "seller": tree_sha(seller)}
        json.dump({"decision_id": did, "folder": seller, "run": run, "as_of": datetime.date.today().isoformat(), "py": PY,
                   "skill": skill}, open(os.path.join(run, "turn.json"), "w", encoding="utf-8"), indent=1)
        facts = json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))
        # 4. settings + CLI version
        sfile, mcp = settings(skill, ldir)
        ver = subprocess.run(claude_cmd() + ["--version"], capture_output=True, text=True).stdout.strip()
        status["claude_version"] = ver
        if ver.split(" ")[0] not in CLI_TESTED:
            status["cli_warning"] = f"CLI {ver} not in the tested set {sorted(CLI_TESTED)}; the self-test decides"
        # 5. self-test, every launch
        why = selftest(skill, sfile, mcp, ldir)
        if why:
            status["reason"] = why
            rc_launcher = 0
            return
        status["selftest"] = "pass"
        # 6. the turn
        env = dict(os.environ, VANI_RUN=run, VANI_PY=PY, PYTHONIOENCODING="utf-8")
        tool = os.path.join(skill, "scripts", "persona_tool.py")
        prompt = (f"Use the vani-persona skill: read {os.path.join(skill, 'SKILL.md')} first and follow its steps exactly. "
                  f"Run directory ($VANI_RUN): {run}. Seller folder: {seller}. "
                  f"The only way to write the persona is \"$VANI_PY\" {tool} (start with: status).")
        args = base_args(skill, sfile, mcp, MODEL, run, p.max_turns)
        args.insert(1, prompt)
        t0 = time.time()
        for attempt in (1, 2):
            rc, out, err = run_claude(args, run, env, p.timeout)
            j, why = output_ok(out)
            if why != "no assistant output" or attempt == 2:
                break
            status["retry"] = "no assistant output on attempt 1"
        status["agent_seconds"] = round(time.time() - t0)
        open(os.path.join(run, "agent_output.json"), "w", encoding="utf-8").write(out)
        open(os.path.join(run, "agent_stderr.txt"), "w", encoding="utf-8").write(err)
        if why:
            status["reason"] = f"agent turn: {why} (rc={rc})"
            rc_launcher = 0
            return
        used = list((j.get("modelUsage") or {}).keys())
        status["models_used"], status["cost_usd"] = used, j.get("total_cost_usd")
        if MODEL not in used:
            status["reason"] = f"model check: {MODEL} not in modelUsage {used}"
            rc_launcher = 0
            return
        # 7. after the turn: trust nothing the agent wrote
        problems = []
        if tree_sha(skill) != skill_sha:
            problems.append("the skill copy changed during the turn")
        if fsha(os.path.join(run, "01_facts.json")) != shas["01"] or fsha(os.path.join(run, "03_prior.json")) != shas["03"]:
            problems.append("01_facts.json or 03_prior.json changed during the turn")
        if tree_sha(seller) != shas["seller"]:
            problems.append("the frozen seller copy changed during the turn")
        p04 = os.path.join(run, "04_persona.json")
        if "guard.do_not_call" in facts.get("true_guards", []):
            if os.path.exists(p04):
                problems.append("do_not_call is true but a persona was written")
            if not problems:
                status.update(status="do_not_call", reason="guard.do_not_call (01_facts.json): no persona, no variables")
            else:
                status["reason"] = "; ".join(problems)
            rc_launcher = 0
            return
        fin = None
        lp = os.path.join(run, "ledger.jsonl")
        if os.path.exists(lp):
            for line in open(lp, encoding="utf-8"):
                try:
                    r = json.loads(line)
                    fin = r if r.get("kind") == "finalize" else fin
                except ValueError:
                    pass
        if not fin:
            problems.append("no finalize in ledger.jsonl (the persona was not written by persona_tool.py)")
        elif fsha(p04) != fin.get("sha04") or fsha(os.path.join(run, "02_review.json")) != fin.get("sha02"):
            problems.append("04_persona.json / 02_review.json differ from the finalize sha (written around the tool)")
        if tree_sha(skill) == skill_sha:
            v = subprocess.run([PY, os.path.join(skill, "scripts", "validate_persona.py"), "--folder", seller, "--run", run],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            status["validation"] = "pass" if v.returncode == 0 else "fail"
            if v.returncode:
                problems.append("validator: " + (v.stdout or v.stderr)[-2500:])
        if problems:
            status["reason"] = "; ".join(problems)
            rc_launcher = 0
            return
        cmd = [PY, os.path.join(skill, "scripts", "compile_vars.py"), "--run", run] + (["--names", p.names] if p.names else [])
        c = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, VANI_REPO=ROOT))
        if c.returncode:
            for f in ("05_sarvam_vars.json", "06_sarvam_prompt.md"):
                if os.path.exists(os.path.join(run, f)):
                    os.remove(os.path.join(run, f))
            status["reason"] = "compile_vars: " + (c.stdout or c.stderr)[-500:]
        else:
            status.update(status="done", reason="validated and compiled")
        rc_launcher = 0
    except Exception as e:
        status["reason"] = f"launcher: {type(e).__name__}: {str(e)[:400]}"
    finally:
        if status.get("status") != "done":
            for f in ("05_sarvam_vars.json", "06_sarvam_prompt.md"):
                if os.path.exists(os.path.join(run, f)):
                    os.remove(os.path.join(run, f))
        json.dump(status, open(os.path.join(run, "status.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: status.get(k) for k in ("decision_id", "status", "reason", "validation", "agent_seconds", "cost_usd")},
                         ensure_ascii=False)[:1200])
    sys.exit(rc_launcher)


if __name__ == "__main__":
    main()
