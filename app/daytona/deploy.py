"""deploy.py: run the vani-persona skill on the Daytona sandbox, end to end, from the laptop (the orchestrator owns all
I/O; the agent on the sandbox never fetches or sends anything itself). Peer-reviewed order (Redash skill, 2026-10-10):

  stage        tar the skill + the 3 app files it needs -> upload /tmp/vani_stage.tgz (+ its sha256, kept on the laptop)
  install      sudo install_vani.sh: verifies the sha, root-owned skill/gates/validator/settings, pinned root-owned
               Claude Code, agent user `vaniagent` with no sudo, work dirs /srv/vani
  checks       on the sandbox: pytest of the skill tests (stub CLI, bypass + fail-closed), then a stub launch in the
               ROOT-OWNED mode (good + bypass) to prove the installed gates and the backstop work there
  seller P     upload the pseudonymised export data/agent_export/<P> to /dev/shm/vani/sellers/<P> (tmpfs)
  run P [ID]   the real run: run_persona.py on Opus 5.5 (PTY, root-owned skill + settings), async, polled
  fetch ID     download the run dir (without the seller copy) to data/runs_daytona/<ID>, then DELETE the run's seller
               copy and the tmpfs input on the sandbox (PII)
  login        print the steps for the human Claude login as the agent user
  baseline     after the login: root-owned copy of ~vaniagent/.claude.json, restored before every run
  sh "cmd"     run one command (debugging)

Names never go to the sandbox: compile the Sarvam variables with names on the laptop after fetch:
  python .claude/skills/vani-persona/scripts/compile_vars.py --run data/runs_daytona/<ID> --names data/agent_export_maps/<P>.json
Usage: python app/daytona/deploy.py <command> [args]
"""
import io
import json
import re
import shlex
import os
import sys
import tarfile
import time

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API, KEY = os.environ["DAYTONA_API_URL"].rstrip("/"), os.environ["DAYTONA_API_KEY"]
SB = os.environ.get("VANI_SANDBOX", "58ca1228-9971-4fd8-850a-bfb7b129978a")
H = {"Authorization": f"Bearer {KEY}"}
TB = f"{API}/toolbox/{SB}/toolbox"
WORK = "/srv/vani"
INST = "/usr/local/share/vani-persona"
PYS = "/usr/bin/python3.13"  # root-owned system python; trusted path always runs it with -E -s
ENV = (f"VANI_INSTALLED_SKILL={INST}/skill VANI_SETTINGS_FILE={INST}/settings.json VANI_MCP_FILE={INST}/empty_mcp.json "
       f"VANI_REPO={INST}/repo VANI_PTY=1 VANI_AGENT_USER=vaniagent VANI_CLAUDE_BIN=/usr/local/bin/claude "
       f"VANI_SCOREBOARDS={WORK}/scoreboards VANI_LAUNCHER_DIR={WORK}/launcher "
       f"VANI_RUNS_ROOT={WORK}/runs VANI_SELLERS_ROOT=/dev/shm/vani/sellers "
       f"VANI_CLAUDE_JSON_BASELINE={INST}/claude_json.baseline "
       f"PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 PYTHONIOENCODING=utf-8")
STAGE_SHA = os.path.join(ROOT, "data", "launcher", "daytona_stage.sha256")


def sh(cmd, timeout=600):
    r = requests.post(f"{TB}/process/execute", headers=H, json={"command": f"bash -c {shlex.quote(cmd)}", "timeout": timeout},
                      timeout=timeout + 30)
    r.raise_for_status()
    d = r.json()
    return d.get("exitCode"), d.get("result") or ""


def run_async(cmd, sid, poll=15, limit=3600):
    requests.post(f"{TB}/process/session", headers=H, json={"sessionId": sid}, timeout=30)
    c = requests.post(f"{TB}/process/session/{sid}/exec", headers=H, json={"command": f"bash -c {shlex.quote(cmd)}", "runAsync": True},
                      timeout=60).json()["cmdId"]
    t0 = time.time()
    while time.time() - t0 < limit:
        st = requests.get(f"{TB}/process/session/{sid}/command/{c}", headers=H, timeout=30).json()
        if st.get("exitCode") is not None:
            logs = requests.get(f"{TB}/process/session/{sid}/command/{c}/logs", headers=H, timeout=60).text
            requests.delete(f"{TB}/process/session/{sid}", headers=H, timeout=30)
            return st["exitCode"], logs
        print(f"  ... running {int(time.time() - t0)} s", flush=True)
        time.sleep(poll)
    return None, "TIMEOUT waiting for the command"


def upload_bytes(data, path):
    r = requests.post(f"{TB}/files/upload", headers=H, params={"path": path}, files={"file": ("f", data)}, timeout=300)
    r.raise_for_status()


def tar_of(entries):
    """entries: [(local path, arcname)] -> tar.gz bytes (no __pycache__). Deterministic (sorted names, mtime 0, owner 0,
    gzip mtime 0), so the same files always give the same sha256 (vani_e2e.py reinstalls only when it changes)."""
    import gzip
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        for p, arc in entries:
            files = [(p, arc)] if os.path.isfile(p) else [
                (os.path.join(b, fn), arc + "/" + os.path.relpath(os.path.join(b, fn), p).replace("\\", "/"))
                for b, ds, fs in os.walk(p) if "__pycache__" not in b for fn in fs if not fn.endswith(".pyc")]
            for src, name in sorted(files, key=lambda x: x[1]):  # forward-slash names (no "\\" from Windows joins)
                name = name.replace("\\", "/")
                data = open(src, "rb").read()
                if src.endswith(".sh"):  # bash rejects CRLF (git on Windows checks out CRLF)
                    data = data.replace(b"\r\n", b"\n")
                ti = tarfile.TarInfo(name)
                ti.size, ti.mtime, ti.uid, ti.gid = len(data), 0, 0, 0
                ti.mode = 0o755 if src.endswith(".sh") else 0o644
                t.addfile(ti, io.BytesIO(data))
    return gzip.compress(buf.getvalue(), mtime=0)


def cmd_stage():
    skill = os.path.join(ROOT, ".claude", "skills", "vani-persona")
    entries = [(skill, "skill"), (os.path.join(ROOT, "app", "daytona"), "app/daytona"),
               (os.path.join(ROOT, "app", "contracts", "sarvam_vars.contract.json"), "app/contracts/sarvam_vars.contract.json"),
               (os.path.join(ROOT, "app", "sarvam", "vani_prompt.md"), "app/sarvam/vani_prompt.md")]
    oj = os.path.join(ROOT, "outputs", "objections.json")
    if os.path.exists(oj):
        entries.append((oj, "outputs/objections.json"))
    import hashlib
    data = tar_of(entries)
    os.makedirs(os.path.dirname(STAGE_SHA), exist_ok=True)
    open(STAGE_SHA, "w").write(hashlib.sha256(data).hexdigest())
    upload_bytes(data, "/tmp/vani_stage.tgz")
    # a readable copy for the stub checks only (the install extracts its own copy as root after the sha check)
    print(sh("rm -rf /tmp/vani_stage && mkdir -p /tmp/vani_stage && tar xzf /tmp/vani_stage.tgz -C /tmp/vani_stage && ls /tmp/vani_stage"))


def cmd_install():
    sha = open(STAGE_SHA).read().strip()
    # the installer itself is taken from the verified tarball, never from the writable /tmp copy
    print(sh(f"set -e; T=$(mktemp -d); tar xzf /tmp/vani_stage.tgz -C $T app/daytona/install_vani.sh; "
             f"echo '{sha}  /tmp/vani_stage.tgz' | sha256sum -c - && sudo bash $T/app/daytona/install_vani.sh /tmp/vani_stage.tgz {sha} 2>&1 | tail -8; rm -rf $T",
             timeout=900))


def cmd_checks():
    """1. the skill tests on the sandbox (stub CLI); 2. stub launches in the ROOT-OWNED mode (agent user, installed
    gates and settings, reaping, isolation); 3. no agent process is left."""
    code, out = run_async("cd /tmp/vani_stage/skill && (python3.11 -m pytest --version >/dev/null 2>&1 || "
                          "python3.11 -m pip install -q --user pytest) && python3.11 -m pytest -q tests 2>&1 | tail -2",
                          "checks-pytest", poll=20, limit=2200)
    print("1. pytest on the sandbox:", out.strip().splitlines()[-1] if out.strip() else out)
    seller = "/tmp/vani_stage/stub_seller"
    sh(f"rm -rf {seller} && mkdir -p {seller}/calls && printf '%s' "
       + shlex.quote(json.dumps({"points": {"H02": {"value": {"vertical_name": "NSD"}}, "B01": {"value": {"seller_state": "Telangana"}}}}))
       + f" > {seller}/context.json && printf '# INDEX\n' > {seller}/INDEX.md && "
       f"printf '# core\n### B01 City\nHyderabad, Telangana\n' > {seller}/core.md && chmod -R a+rX /tmp/vani_stage")
    expect = {"good": "done", "bypass": "error", "forged": "error", "hang": "error"}
    for mode, extra in (("good", ""), ("bypass", ""), ("forged", ""), ("hang", "--timeout 20")):
        did = f"stub-{mode}-" + os.urandom(3).hex()
        code, out = run_async(f"cd {WORK} && {ENV} VANI_CLAUDE=/tmp/vani_stage/skill/tests/stub_claude.py STUB_MODE={mode} "
                              f"{PYS} -E -s {INST}/skill/run_persona.py --folder {seller} --runs {WORK}/stubruns --decision-id {did} "
                              f"{extra} 2>&1 | tail -1", f"checks-{mode}", poll=5, limit=600)
        try:  # the launcher's own status.json (the printed summary line is cut at 1200 chars)
            raw = sh(f"cat {WORK}/stubruns/{did}/status.json")[1]
            st = json.loads(raw[raw.index("{"):])
        except (ValueError, IndexError):
            st = {"status": "?", "reason": out[-300:]}
        ok = st.get("status") == expect[mode]
        print(f"2. {mode:7s} {'PASS' if ok else 'FAIL'}: status={st.get('status')} reason={str(st.get('reason'))[:160]}")
    code, out = sh("for p in /proc/[0-9]*; do [ \"$(stat -c %U $p 2>/dev/null)\" = vaniagent ] && echo LEFT; done; echo end")
    print("3. leftover vaniagent processes:", out.count("LEFT"))


LEAK_PHONE = re.compile(r"(?<![\w{])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?![\w}])")
PERSON_TOKENS = {"{SELLER_NAME}", "{SALES_EXEC}", "{TELE_EXEC}", "{EXEC_NAME}"}
LEAK_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")


def leak_scan(src, pseudo):
    """Plan 5d: before any upload, the pseudonymised folder must hold no person name from the laptop's token map, no
    phone number and no email. Fails closed: a missing or unreadable map refuses the upload. Returns the hits."""
    mp = os.path.join(ROOT, "data", "agent_export_maps", f"{pseudo}.json")
    try:
        m = json.load(open(mp, encoding="utf-8"))
        # person names only (seller, handler, staff); company names may be in the export (user decision 2026-10-10)
        names = {v.strip().lower() for t, vs in (m.get("tokens") or m).items() if t in PERSON_TOKENS
                 for v in (vs if isinstance(vs, list) else [vs]) if isinstance(v, str) and len(v.strip()) >= 4}
    except (OSError, ValueError, AttributeError) as e:
        sys.exit(f"REFUSED upload: token map {mp} missing or unreadable ({e})")
    hits = []
    for dp, _, fs in os.walk(src):
        for fn in fs:
            p = os.path.join(dp, fn)
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            low = text.lower()
            rel = os.path.relpath(p, src)
            hits += [f"{rel}: person name ({len(n)} chars)" for n in names
                     if re.search(r"(?<![a-z])" + re.escape(n) + r"(?![a-z])", low)]
            hits += [f"{rel}: phone number" for _ in LEAK_PHONE.finditer(text)][:1]
            hits += [f"{rel}: email" for _ in LEAK_EMAIL.finditer(text)][:1]
    return hits


def cmd_seller(pseudo):
    src = os.path.join(ROOT, "data", "agent_export", pseudo)
    if not os.path.isdir(src):
        sys.exit(f"no export folder {src}")
    hits = leak_scan(src, pseudo)
    if hits:  # the names themselves are never printed
        sys.exit("REFUSED upload: leak scan found\n" + "\n".join(sorted(set(hits))[:20]))
    upload_bytes(tar_of([(src, pseudo)]), f"/dev/shm/{pseudo}.tgz")
    # ONE seller at a time (peer review MUST 2): the staging dir is emptied first, mode 700, owned by daytona
    print(sh(f"umask 077 && mkdir -p /dev/shm/vani/sellers && chmod 700 /dev/shm/vani /dev/shm/vani/sellers && "
             f"rm -rf /dev/shm/vani/sellers/* && tar xzf /dev/shm/{pseudo}.tgz -C /dev/shm/vani/sellers && rm /dev/shm/{pseudo}.tgz && "
             f"du -sh /dev/shm/vani/sellers/{pseudo}"))


def cmd_run(pseudo, did=None):
    did = did or time.strftime("dt-%Y%m%d-%H%M%S-") + os.urandom(4).hex()  # not guessable (peer note)
    cmd = (f"cd {WORK} && {ENV} {PYS} -E -s {INST}/skill/run_persona.py --folder /dev/shm/vani/sellers/{pseudo} "
           f"--runs {WORK}/runs --decision-id {did} > {WORK}/runs/{did}.launcher.log 2>&1; "
           f"rm -rf /dev/shm/vani/sellers/{pseudo}; tail -5 {WORK}/runs/{did}.launcher.log")  # staged seller wiped at the end of the run
    print(f"run {did} (Opus 5.5 on Daytona) ...")
    code, logs = run_async(cmd, f"vani-{did}")
    print(code, logs[-2000:])
    print(f"next: python app/daytona/deploy.py fetch {did}")


def cmd_fetch(did):
    code, out = sh(f"cd {WORK}/runs && tar czf /tmp/{did}.tgz --exclude='{did}/seller' {did} {did}.launcher.log && echo ok")
    if "ok" not in out:
        sys.exit(out)
    r = requests.get(f"{TB}/files/download", headers=H, params={"path": f"/tmp/{did}.tgz"}, timeout=300)
    r.raise_for_status()
    dest = os.path.join(ROOT, "data", "runs_daytona")
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as t:
        t.extractall(dest, filter="data")
    seller = json.load(open(os.path.join(dest, did, "turn.json"), encoding="utf-8")).get("folder", "")
    pseudo = os.path.basename(json.load(open(os.path.join(dest, did, "turn.json"), encoding="utf-8")).get("source", "") or "")
    sh(f"rm -f /tmp/{did}.tgz; sudo rm -rf {WORK}/runs/{did}/seller /dev/shm/vani/sellers/*; echo cleaned")  # PII off the box
    print(f"sandbox cleaned: run seller copy {seller} and the tmpfs inputs removed")
    st = json.load(open(os.path.join(dest, did, "status.json"), encoding="utf-8"))
    print(json.dumps({k: st.get(k) for k in ("status", "reason", "validation", "selftest", "models_used", "cost_usd",
                                             "agent_seconds", "stop_gate_fired", "pre_gate_fired", "skill_mode", "claude_version")},
                     ensure_ascii=False, indent=1)[:2500])


def cmd_login():
    print("1. SSH in (ask Claude for a fresh key: deploy.py has none).\n"
          "2. sudo -iu vaniagent\n"
          "3. /usr/local/bin/claude      -> log in with your own browser (OAuth), then /exit\n"
          "4. /usr/local/bin/claude -p 'say ok' --model claude-opus-5-5\n"
          "5. exit (back to daytona), tell Claude it is done.")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c, args = sys.argv[1], sys.argv[2:]
    if c == "stage":
        cmd_stage()
    elif c == "install":
        cmd_install()
    elif c == "checks":
        cmd_checks()
    elif c == "seller":
        cmd_seller(args[0])
    elif c == "run":
        cmd_run(*args)
    elif c == "fetch":
        cmd_fetch(args[0])
    elif c == "login":
        cmd_login()
    elif c == "baseline":
        print(sh(f"sudo test -f /home/vaniagent/.claude/.credentials.json && "
                 f"sudo install -o root -g root -m 644 /home/vaniagent/.claude.json {INST}/claude_json.baseline && "
                 f"sudo ls -la {INST}/claude_json.baseline || echo 'NOT LOGGED IN as vaniagent yet'"))
    elif c == "sh":
        print(sh(args[0], timeout=int(args[1]) if len(args) > 1 else 600))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
