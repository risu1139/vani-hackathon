"""vani_e2e.py: ONE command, seller GLID -> persona -> final Sarvam prompt -> live test call -> learning loop.

  python app/e2e/vani_e2e.py --glid <GLID> [--no-call] [--refresh]

Steps (each prints one line; any failure stops with the reason):
  1. context   laptop: seller_context_builder.py build (cached; --refresh re-fetches the APIs)
  2. export    laptop: export_for_agent.py (pseudonymised folder + name map; names never leave the laptop)
  3. sandbox   Daytona: start the sandbox if it is stopped
  4. install   Daytona: reinstall the root-owned skill only when the laptop's stage sha differs from the installed one
  5. login     Daytona: the agent user (vaniagent) must be logged in to Claude (a human does this once; see deploy.py login)
  6. agent     Daytona: upload the seller, run the Opus 5.5 agent (gates, self-test), fetch, clean the sandbox
  7. prompt    laptop: re-validate, compile the Sarvam variables + the final prompt WITH names
  8. call      Sarvam: one live voice call with those variables (SDK, the persona's language), collect it, review it,
               and run both learning loops in test mode (never into the real scoreboards)
Outputs: data/runs_daytona/<decision id>/ (04_persona.json, 05_sarvam_vars.json, 06_sarvam_prompt.md, 06_call.json,
07_outcome.json, 08_review.json, status.json).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "app", "daytona"))
import deploy as D  # noqa: E402

PY = sys.executable
SKILL = os.path.join(ROOT, ".claude", "skills", "vani-persona")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def step(name, ok, detail=""):
    print(f"[{name:8s}] {'OK  ' if ok else 'FAIL'} {detail}", flush=True)
    if not ok:
        sys.exit(1)


def run(cmd, timeout=1800):
    r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def pseudo_for(glid):
    for f in glob.glob(os.path.join(ROOT, "data", "agent_export_maps", "*.json")):
        if str(json.load(open(f, encoding="utf-8")).get("glid")) == str(glid):
            return os.path.splitext(os.path.basename(f))[0]
    return None


def sandbox_up():
    import requests
    s = requests.get(f"{D.API}/sandbox/{D.SB}", headers=D.H, timeout=30).json()
    if s.get("state") != "started":
        requests.post(f"{D.API}/sandbox/{D.SB}/start", headers=D.H, timeout=60)
        for _ in range(60):
            time.sleep(5)
            s = requests.get(f"{D.API}/sandbox/{D.SB}", headers=D.H, timeout=30).json()
            if s.get("state") == "started":
                break
    return s.get("state")


def stage_sha():
    import hashlib
    skill = os.path.join(ROOT, ".claude", "skills", "vani-persona")
    entries = [(skill, "skill"), (os.path.join(ROOT, "app", "daytona"), "app/daytona"),
               (os.path.join(ROOT, "app", "contracts", "sarvam_vars.contract.json"), "app/contracts/sarvam_vars.contract.json"),
               (os.path.join(ROOT, "app", "sarvam", "vani_prompt.md"), "app/sarvam/vani_prompt.md")]
    if os.path.exists(os.path.join(ROOT, "outputs", "objections.json")):
        entries.append((os.path.join(ROOT, "outputs", "objections.json"), "outputs/objections.json"))
    return hashlib.sha256(D.tar_of(entries)).hexdigest()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--glid", required=True)
    a.add_argument("--refresh", action="store_true", help="re-fetch the APIs and queries for the context")
    a.add_argument("--no-call", action="store_true", help="stop after the final prompt (no Sarvam call)")
    a.add_argument("--decision-id")
    p = a.parse_args()

    # 1-2. context + export (laptop)
    rc, out = run([PY, "app/persona/seller_context_builder.py", "build", "--glid", p.glid] + (["--refresh"] if p.refresh else ["--rebuild"]
                  if os.path.isdir(os.path.join(ROOT, "data", "contexts", p.glid)) else []))
    step("context", rc == 0, out.strip().splitlines()[-1][:160] if out.strip() else "")
    rc, out = run([PY, "app/persona/export_for_agent.py", "--glid", p.glid])
    pseudo = pseudo_for(p.glid)
    step("export", rc == 0 and pseudo is not None, f"pseudonym {pseudo} (PII gate passed)" if rc == 0 else out[-300:])

    # 3-5. sandbox, install, login
    state = sandbox_up()
    step("sandbox", state == "started", f"{D.SB[:8]} {state}")
    local = stage_sha()
    installed = D.sh(f"cat {D.INST}/stage.sha256 2>/dev/null")[1].strip().splitlines()[-1:] or [""]
    if installed[0].strip() != local:
        D.cmd_stage()
        D.cmd_install()
        installed = D.sh(f"cat {D.INST}/stage.sha256 2>/dev/null")[1].strip().splitlines()[-1:] or [""]
        step("install", installed[0].strip() == local, "reinstalled (the skill changed)")
    else:
        step("install", True, "up to date (sha matches)")
    rc, out = D.sh("sudo test -f /home/vaniagent/.claude/.credentials.json && echo LOGGED_IN || echo NO_LOGIN")
    step("login", "LOGGED_IN" in out, "vaniagent is logged in" if "LOGGED_IN" in out else
         "vaniagent is NOT logged in: run `python app/daytona/deploy.py login` and follow the steps, then rerun")
    D.sh(f"sudo test -f {D.INST}/claude_json.baseline || sudo install -o root -g root -m 644 /home/vaniagent/.claude.json {D.INST}/claude_json.baseline")

    # 6. the agent on Daytona
    did = p.decision_id or time.strftime("e2e-%Y%m%d-%H%M%S-") + os.urandom(3).hex()
    D.cmd_seller(pseudo)
    cmd = (f"cd {D.WORK} && {D.ENV} {D.PYS} -E -s {D.INST}/skill/run_persona.py --folder /dev/shm/vani/sellers/{pseudo} "
           f"--runs {D.WORK}/runs --decision-id {did} > {D.WORK}/runs/{did}.launcher.log 2>&1; "
           f"rm -rf /dev/shm/vani/sellers/{pseudo}; tail -1 {D.WORK}/runs/{did}.launcher.log")
    print(f"[agent   ] running {did} on Daytona (Opus 5.5) ...", flush=True)
    code, logs = D.run_async(cmd, f"e2e-{did}", poll=20, limit=3600)
    D.cmd_fetch(did)
    rdir = os.path.join(ROOT, "data", "runs_daytona", did)
    st = json.load(open(os.path.join(rdir, "status.json"), encoding="utf-8"))
    if st.get("status") == "do_not_call":
        step("agent", True, "do_not_call (01_facts): no persona, no call. Done.")
        return
    step("agent", st.get("status") == "done",
         f"status={st.get('status')} validation={st.get('validation')} models={st.get('models_used')} "
         f"{st.get('agent_seconds')} s ${st.get('cost_usd')} gates fired: stop={st.get('stop_gate_fired')} "
         f"pre={st.get('pre_gate_fired')} | {str(st.get('reason'))[:200]}")

    # 7. the final prompt, with names, on the laptop
    folder = os.path.join(ROOT, "data", "agent_export", pseudo)
    rc, out = run([PY, os.path.join(SKILL, "scripts", "validate_persona.py"), "--folder", folder, "--run", rdir])
    step("validate", rc == 0, "laptop re-validation against the local seller copy" if rc == 0 else out[-600:])
    rc, out = run([PY, os.path.join(SKILL, "scripts", "compile_vars.py"), "--run", rdir, "--names",
                   os.path.join(ROOT, "data", "agent_export_maps", f"{pseudo}.json")])
    step("prompt", rc == 0 and os.path.exists(os.path.join(rdir, "06_sarvam_prompt.md")),
         f"{os.path.relpath(os.path.join(rdir, '06_sarvam_prompt.md'), ROOT)}" if rc == 0 else out[-400:])
    if p.no_call:
        return

    # 8. live voice call on the Sarvam agent, then the learning loops (test mode)
    rc, out = run([PY, "app/sarvam/voice_smoke.py", "--run", rdir], timeout=600)
    iid = next((ln.split()[-1] for ln in out.splitlines() if ln.startswith("INTERACTION")), None)
    step("call", rc == 0 and iid not in (None, "None"), f"interaction {iid}" if iid else out[-400:])
    for attempt in range(8):  # analytics lists the call (and its post-call labels) some time after it ends
        time.sleep(30)
        rc, out = run([PY, "app/sarvam/collect_call.py", "--interaction-id", iid, "--hours", "2", "--out", os.path.join(ROOT, "data", "runs_daytona")])
        if rc == 0:
            break
    step("collect", rc == 0, out.strip().splitlines()[-1][:160] if out.strip() else "")
    rc, out = run([PY, "app/loops/close_loop.py", "--run", rdir, "--test", "--names",
                   os.path.join(ROOT, "data", "agent_export_maps", f"{pseudo}.json")], timeout=1200)
    step("loops", rc == 0, " | ".join(ln[:120] for ln in out.strip().splitlines() if ln.startswith("[")))
    print(f"done: {os.path.relpath(rdir, ROOT)}")


if __name__ == "__main__":
    main()
