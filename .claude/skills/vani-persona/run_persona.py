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
Daytona (root-owned install, see app/daytona/install_vani.sh): VANI_INSTALLED_SKILL=<root-owned skill dir> uses the skill
in place (no writable copy); VANI_SETTINGS_FILE / VANI_MCP_FILE = root-owned settings and empty MCP config;
VANI_PTY=1 runs claude -p inside /usr/bin/script (Linux needs a TTY); VANI_REPO = the dir with app/contracts + app/sarvam;
VANI_AGENT_USER=<user> runs claude as that unprivileged user (no sudo, cannot write the install; peer review blocker 1);
VANI_CLAUDE_BIN = the root-owned pinned CLI (absolute path). On Linux every Python child runs with -E -s (blocker 3).
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
def _repo_root():
    """VANI_REPO if set; else the nearest parent of the skill that holds app/contracts (the repo, or a Daytona stage)."""
    if os.environ.get("VANI_REPO"):
        return os.path.abspath(os.environ["VANI_REPO"])
    d = SKILL
    for _ in range(6):
        d = os.path.dirname(d)
        if os.path.isfile(os.path.join(d, "app", "contracts", "sarvam_vars.contract.json")):
            return d
    return os.path.abspath(os.path.join(SKILL, "..", "..", ".."))


ROOT = _repo_root()
MODEL = "claude-opus-5-5"
SELFTEST_MODEL = "claude-haiku-4-5-20251001"
CLI_TESTED = {"2.1.292", "2.1.296"}
PY = sys.executable
PYF = [] if os.name == "nt" else ["-E", "-s"]  # Linux: ignore PYTHON* env and the user site dir (planted .pth files)
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
    if os.environ.get("VANI_CLAUDE_BIN"):
        return [os.environ["VANI_CLAUDE_BIN"]]
    p = shutil.which("claude")
    if not p:
        raise RuntimeError("claude CLI not found")
    return [p]


AGENT = os.environ.get("VANI_AGENT_USER")


def sudo(*args):
    return subprocess.run(["/usr/bin/sudo", "-n"] + list(args), capture_output=True, text=True)


def as_agent(cmd):
    return sudo("-u", AGENT, "-H", "/bin/bash", "-c", cmd)


def agent_reap():
    """Peer review MUST 1: no agent process may outlive a run (nohup, setsid, &). Kill every process of the agent user
    and check that none is left. Returns '' or the problem. No-op without an agent user (laptop)."""
    if not AGENT:
        return ""
    import pwd
    uid = pwd.getpwnam(AGENT).pw_uid

    def pids():  # /proc scan: no procps needed (the sandbox image has no pgrep/pkill)
        out = []
        for d in os.listdir("/proc"):
            if d.isdigit():
                try:
                    if os.stat(f"/proc/{d}").st_uid == uid:
                        out.append(d)
                except OSError:
                    pass
        return out
    for _ in range(20):
        if not pids():
            return ""
        as_agent("kill -KILL -1")  # as the agent: signals every process that user owns (bash builtin)
        time.sleep(0.25)
    left = pids()
    return f"agent user {AGENT} still has processes after the kill: {left[:5]}" if left else ""


def agent_wipe_home():
    """SHOULD 4: the agent's home keeps only the Claude login (~/.claude/.credentials.json, ~/.claude.json);
    earlier sellers' session transcripts (~/.claude/projects), caches and ~/.local are removed between runs."""
    if AGENT:
        as_agent("cd ~ && find . -mindepth 1 -maxdepth 1 ! -name .claude ! -name .claude.json -exec rm -rf {} + ; "
                 "[ -d .claude ] && find .claude -mindepth 1 -maxdepth 1 ! -name .credentials.json -exec rm -rf {} + ; true")
        base = os.environ.get("VANI_CLAUDE_JSON_BASELINE")  # root-owned copy taken right after the human login
        if base:
            sudo("/usr/bin/install", "-o", AGENT, "-g", AGENT, "-m", "600", base, f"/home/{AGENT}/.claude.json")


def share_with_agent(path, frozen=()):
    """MUST 2 / SHOULD 3: the run dir is group vaniagent, mode 3770 (setgid + sticky): the agent may add files but can
    neither list other runs nor rename/delete the launcher's frozen inputs; frozen paths are group-readable only."""
    if not AGENT:
        return
    sudo("/usr/bin/chgrp", "-R", AGENT, path)
    os.chmod(path, 0o3770)
    for f in frozen:
        sudo("/usr/bin/chmod", "-R", "g+rX,g-w,o-rwx", f)


def unshare(path):
    """After the run: the run dir is locked to the launcher again (no agent access to earlier runs)."""
    if AGENT and os.path.isdir(path):
        sudo("/usr/bin/chown", "-R", f"{os.getuid()}:{os.getgid()}", path)
        sudo("/usr/bin/chmod", "-R", "go-rwx", path)


def agent_cannot_see(paths):
    """Self-test: the agent user cannot list the runs root or the seller staging dir."""
    bad = [p for p in paths if p and as_agent(f"ls {p}").returncode == 0]
    return f"agent user can list {bad}" if bad else ""


def kill_tree(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()
        agent_reap()  # sudo was the child; script/claude/agent processes run as the agent user


def pty_wrap(cmd, cwd, env):
    """Linux: claude -p needs a TTY (peer lesson). Write an inner script that EXPORTS every env var it needs, run it
    under `script -qec`, and keep stdout/stderr in files so escape codes can be stripped."""
    import shlex
    inner = os.path.join(cwd, ".inner.sh")
    keep = [k for k in env if k.startswith(("VANI_", "ANTHROPIC_", "STUB_", "LANG")) or k in ("PATH", "PYTHONIOENCODING")]
    with open(inner, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n" + "".join(f"export {k}={shlex.quote(env[k])}\n" for k in keep)
                + f"cd {shlex.quote(cwd)}\n" + " ".join(shlex.quote(c) for c in cmd) + "\n")
    os.chmod(inner, 0o755)
    user = os.environ.get("VANI_AGENT_USER")
    pre = ["/usr/bin/sudo", "-n", "-u", user, "-H", "--"] if user else []
    return pre + ["/usr/bin/script", "-qec", inner, "/dev/null"]


def last_json(text):
    """The last JSON object line in a PTY log (escape codes and CRs removed)."""
    import re
    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text).replace("\r", "")
    for line in reversed(clean.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return line
    return clean


def run_claude(args, cwd, env, timeout):
    cmd = claude_cmd() + args
    if os.environ.get("VANI_PTY") == "1":
        cmd = pty_wrap(cmd, cwd, env)
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        out, err = proc.communicate()
        return 124, out or "", (err or "") + "\nTIMEOUT"
    if os.environ.get("VANI_PTY") == "1":
        with open(os.path.join(cwd, "run.log"), "a", encoding="utf-8", errors="replace") as f:  # raw bytes for post-mortem
            f.write(out or "")
        out = last_json(out or "")
    return proc.returncode, out or "", err or ""


def settings(skill, ldir):
    if os.environ.get("VANI_SETTINGS_FILE"):  # Daytona: root-owned settings written by install_vani.sh
        return os.environ["VANI_SETTINGS_FILE"], os.environ["VANI_MCP_FILE"]
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


def hostile(st, on):
    """Peer check: with --setting-sources '' a hostile disableAllHooks in the project and in the agent user's settings
    must NOT silence the gates. Writes them (on=True) or removes them (on=False)."""
    proj = os.path.join(st, ".claude", "settings.json")
    user = os.environ.get("VANI_AGENT_USER")
    if on:
        os.makedirs(os.path.dirname(proj), exist_ok=True)
        json.dump({"disableAllHooks": True}, open(proj, "w"))
        if user:
            subprocess.run(["/usr/bin/sudo", "-n", "-u", user, "-H", "/bin/bash", "-c",
                            "mkdir -p ~/.claude && cp -n ~/.claude/settings.json ~/.claude/settings.json.vani_bak 2>/dev/null; "
                            "echo '{\"disableAllHooks\": true}' > ~/.claude/settings.json"], capture_output=True)
    else:
        if os.path.exists(proj):
            os.remove(proj)
        if user:
            subprocess.run(["/usr/bin/sudo", "-n", "-u", user, "-H", "/bin/bash", "-c",
                            "if [ -f ~/.claude/settings.json.vani_bak ]; then mv ~/.claude/settings.json.vani_bak ~/.claude/settings.json; "
                            "else rm -f ~/.claude/settings.json; fi"], capture_output=True)


def agent_has_no_sudo():
    """Blocker 1: the agent user must not have passwordless sudo. True when there is no agent user (laptop)."""
    user = os.environ.get("VANI_AGENT_USER")
    if not user:
        return True
    r = subprocess.run(["/usr/bin/sudo", "-n", "-u", user, "-H", "/usr/bin/sudo", "-n", "true"], capture_output=True)
    return r.returncode != 0


def selftest(skill, sfile, mcp, ldir):
    """Both gates must fire on a cheap launch, also under hostile settings; the agent user has no sudo.
    Returns '' if ok, else the reason."""
    if not agent_has_no_sudo():
        return "self-test: the agent user has passwordless sudo (remove it)"
    why = agent_reap() or agent_cannot_see([os.environ.get("VANI_RUNS_ROOT"), os.environ.get("VANI_SELLERS_ROOT")])
    if why:
        return "self-test: " + why
    st = os.path.join(ldir, "selftest")
    os.makedirs(st, exist_ok=True)
    if AGENT:
        os.chmod(ldir, 0o711)
    for f in (".pre_gate_fired", ".stop_gate_fired"):
        if os.path.exists(os.path.join(st, f)):
            os.remove(os.path.join(st, f))
    json.dump({"decision_id": "selftest", "folder": st, "run": st, "selftest": True}, open(os.path.join(st, "turn.json"), "w", encoding="utf-8"))
    share_with_agent(st, [os.path.join(st, "turn.json")])
    env = dict(os.environ, VANI_RUN=st, VANI_PY=PY, VANI_SKILL=skill, VANI_REPO=ROOT, PYTHONIOENCODING="utf-8")
    prompt = f"Self-test. Use the Write tool to create {os.path.join(st, '04_persona.json')} with the text {{}}. Then reply DONE and stop."
    args = base_args(skill, sfile, mcp, SELFTEST_MODEL, st, 4)
    args.insert(1, prompt)
    hostile(st, True)
    try:
        rc, out, err = run_claude(args, st, env, 300)
    finally:
        hostile(st, False)
        left = agent_reap()
        unshare(st)
    if left:
        return "self-test: " + left
    missing = [f for f in (".pre_gate_fired", ".stop_gate_fired") if not os.path.exists(os.path.join(st, f))]
    return f"self-test: hooks did not fire under hostile settings ({', '.join(missing)}); rc={rc}; {err[-300:]}" if missing else ""


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
        os.makedirs(ldir)
        if os.environ.get("VANI_INSTALLED_SKILL"):  # Daytona: root-owned install, used in place (tamper-proof)
            skill = os.path.abspath(os.environ["VANI_INSTALLED_SKILL"])
            status["skill_mode"] = "root-owned install"
        else:  # laptop: a launcher copy outside the run dir (tamper-evident via the tree sha)
            skill = os.path.join(ldir, "skill")
            shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns("__pycache__", "tests", "*.pyc"))
            status["skill_mode"] = "launcher copy"
        status["skill_sha"] = skill_sha = tree_sha(skill)
        # 3. frozen seller copy, facts and prior on it
        seller = os.path.join(run, "seller")
        if os.path.exists(seller):
            shutil.rmtree(seller)
        shutil.copytree(os.path.abspath(p.folder), seller)
        boards = os.environ.get("VANI_SCOREBOARDS") or os.path.join(ROOT, "data", "scoreboards")
        for script, extra in (("facts.py", []), ("prior.py", ["--decision-id", did, "--scoreboards", boards])):
            r = subprocess.run([PY] + PYF + [os.path.join(skill, "scripts", script), "--folder", seller] + extra, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            if r.returncode:
                raise RuntimeError(f"{script} failed: {r.stderr[-400:]}")
        shutil.copy(os.path.join(seller, "facts.json"), os.path.join(run, "01_facts.json"))
        shutil.copy(os.path.join(seller, "prior.json"), os.path.join(run, "03_prior.json"))
        shas = {"01": fsha(os.path.join(run, "01_facts.json")), "03": fsha(os.path.join(run, "03_prior.json")), "seller": tree_sha(seller)}
        json.dump({"decision_id": did, "source": os.path.abspath(p.folder), "folder": os.path.abspath(seller), "run": run, "as_of": datetime.date.today().isoformat(), "py": PY,
                   "skill": skill}, open(os.path.join(run, "turn.json"), "w", encoding="utf-8"), indent=1)
        facts = json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))
        # 4. settings + CLI version
        sfile, mcp = settings(skill, ldir)
        cfg_sha = (fsha(sfile), fsha(mcp))
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
        env = dict(os.environ, VANI_RUN=run, VANI_PY=PY, VANI_SKILL=skill, VANI_REPO=ROOT, PYTHONIOENCODING="utf-8",
                   ANTHROPIC_SMALL_FAST_MODEL=MODEL, ANTHROPIC_DEFAULT_HAIKU_MODEL=MODEL)  # background tasks on the same model
        tool = os.path.join(skill, "scripts", "persona_tool.py")
        prompt = (f"Use the vani-persona skill: read {os.path.join(skill, 'SKILL.md')} first and follow its steps exactly. "
                  f"Run directory ($VANI_RUN): {run}. Seller folder: {seller}. "
                  f"The only way to write the persona is \"$VANI_PY\" {tool} (start with: status).")
        assert env["VANI_RUN"] and os.path.isfile(os.path.join(env["VANI_RUN"], "turn.json")), "VANI_RUN is not set up"
        agent_wipe_home()
        share_with_agent(run, [os.path.join(run, f) for f in ("seller", "01_facts.json", "03_prior.json", "turn.json")])
        args = base_args(skill, sfile, mcp, MODEL, run, p.max_turns)
        args.insert(1, prompt)
        t0 = time.time()
        for attempt in (1, 2):
            rc, out, err = run_claude(args, run, env, p.timeout)
            left = agent_reap()
            j, why = output_ok(out)
            if rc == 124:
                why = "killed: timeout"
            if left:
                why = (why + "; " if why else "") + left
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
        if used != [MODEL]:
            status["reason"] = f"model check: modelUsage must name {MODEL} alone, got {used}"
            rc_launcher = 0
            return
        # 7. after the turn: trust nothing the agent wrote
        status["stop_gate_fired"] = os.path.exists(os.path.join(run, ".stop_gate_fired"))  # evals: must be true on some runs
        status["pre_gate_fired"] = os.path.exists(os.path.join(run, ".pre_gate_fired"))
        problems = []
        if tree_sha(skill) != skill_sha:
            problems.append("the skill copy changed during the turn")
        if (fsha(sfile), fsha(mcp)) != cfg_sha:
            problems.append("the settings or MCP config changed during the turn")
        if fsha(os.path.join(run, "01_facts.json")) != shas["01"] or fsha(os.path.join(run, "03_prior.json")) != shas["03"]:
            problems.append("01_facts.json or 03_prior.json changed during the turn")
        if tree_sha(seller) != shas["seller"]:
            problems.append("the frozen seller copy changed during the turn")
        p04 = os.path.join(run, "04_persona.json")
        if "guard.do_not_call" in facts.get("true_guards", []):
            note = "guard.do_not_call (01_facts.json): no call, no variables"
            if os.path.exists(p04):
                os.replace(p04, os.path.join(run, "04_persona.discarded.json"))
                note += "; a persona was written anyway and was discarded"
            if not problems:
                status.update(status="do_not_call", reason=note)
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
            for own in ("validation.json", "05_sarvam_vars.json", "06_sarvam_prompt.md"):  # agent-owned copies: the launcher writes its own
                if os.path.exists(os.path.join(run, own)):
                    os.remove(os.path.join(run, own))
            v = subprocess.run([PY] + PYF + [os.path.join(skill, "scripts", "validate_persona.py"), "--folder", seller, "--run", run],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            status["validation"] = "pass" if v.returncode == 0 else "fail"
            if v.returncode:
                problems.append("validator: " + (v.stdout or v.stderr)[-2500:])
        if problems:
            status["reason"] = "; ".join(problems)
            rc_launcher = 0
            return
        cmd = [PY] + PYF + [os.path.join(skill, "scripts", "compile_vars.py"), "--run", run] + (["--names", p.names] if p.names else [])
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
        reap = agent_reap()
        if reap:
            status.update(status="error", reason=(status.get("reason") or "") + "; " + reap)
        try:
            unshare(run)
            agent_wipe_home()
        except Exception as e:  # the status below is still written
            status["cleanup_error"] = str(e)[:200]
        if status.get("status") != "done":
            for f in ("05_sarvam_vars.json", "06_sarvam_prompt.md"):
                if os.path.exists(os.path.join(run, f)):
                    os.remove(os.path.join(run, f))
        sp = os.path.join(run, "status.json")
        if os.path.exists(sp):  # an agent-written status.json is never trusted and may be owned by the agent user
            os.remove(sp)
        json.dump(status, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: status.get(k) for k in ("decision_id", "status", "reason", "validation", "agent_seconds", "cost_usd")},
                         ensure_ascii=False)[:1200])
    sys.exit(rc_launcher)


if __name__ == "__main__":
    main()
