"""Deploy app/signal_server to a self-hosted Daytona sandbox via REST (SDK 0.222 is incompatible).

Prints the public preview URL. Re-running reuses the sandbox id stored in .daytona_signal_sandbox.
"""
import os
import secrets
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / ".env"
STATE = ROOT / "app" / "spike" / ".daytona_signal_sandbox"


def load_env():
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env()
if not os.environ.get("SIGNAL_TOKEN"):
    tok = secrets.token_urlsafe(24)
    with ENV.open("a") as f:
        f.write(f"\n# Shared secret the Sarvam tool sends as x-signal-token\nSIGNAL_TOKEN={tok}\n")
    os.environ["SIGNAL_TOKEN"] = tok

A = os.environ["DAYTONA_API_URL"].rstrip("/")
H = {"Authorization": f"Bearer {os.environ['DAYTONA_API_KEY']}"}


def call(method, path, **kw):
    r = requests.request(method, A + path, headers=H, timeout=120, **kw)
    if r.status_code >= 300:
        sys.exit(f"{method} {path} -> {r.status_code} {r.text[:300]}")
    return r.json() if r.content and "json" in r.headers.get("content-type", "") else r.text


def sh(sb, cmd, timeout=120):
    out = call("POST", f"/toolbox/{sb}/toolbox/process/execute", json={"command": cmd, "timeout": timeout})
    return out.get("exitCode"), out.get("result", "").replace(
        "/usr/bin/bash: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8): No such file or directory\n", "")


sb = STATE.read_text().strip() if STATE.exists() else None
if sb:
    st = call("GET", f"/sandbox/{sb}")
    if st.get("state") != "started":
        call("POST", f"/sandbox/{sb}/start")
else:
    sb = call("POST", "/sandbox", json={"public": True, "labels": {"purpose": "vani-signal-server"},
                                         "autoStopInterval": 0})["id"]
    STATE.write_text(sb)
for _ in range(60):
    if call("GET", f"/sandbox/{sb}").get("state") == "started":
        break
    time.sleep(2)

src = (ROOT / "app" / "signal_server" / "main.py").read_bytes()
call("POST", f"/toolbox/{sb}/toolbox/files/upload", params={"path": "/home/daytona/signal/main.py"},
     files={"file": ("main.py", src)})
call("POST", f"/toolbox/{sb}/toolbox/files/upload", params={"path": "/home/daytona/signal/restart.sh"},
     files={"file": ("restart.sh", (ROOT / "app" / "signal_server" / "restart.sh").read_bytes())})
print(sh(sb, "pip install -q fastapi uvicorn 2>&1 | tail -1", timeout=240))
print(sh(sb, f"env SIGNAL_TOKEN={os.environ['SIGNAL_TOKEN']} bash /home/daytona/signal/restart.sh"))
prev = call("GET", f"/sandbox/{sb}/ports/8000/preview-url")
print("SANDBOX", sb)
print("URL", prev["url"])
print("(preview DNS has no wildcard record yet; public URL comes from the cloudflared tunnel, SIGNAL_SERVER_URL)")
