"""place_call.py: a real PHONE call to a whitelisted test number with one run's persona, by API (no console clicks).

Endpoint (found 2026-10-10 from the console's "Test agent -> Phone -> Call"): POST
  https://apps.sarvam.ai/api/scheduling/v1/orgs/{org}/workspaces/{ws}/playground-test   (X-API-Key = SARVAM_AGENTS_API_KEY)
  body {"app_config": {"app_id", "app_version", "user_config": {"app_overrides": {"initial_language_name", "agent_variables"}}},
        "phone_numbers": ["+91..."]}
Only numbers whitelisted in the workspace can be called (Deploy -> phone numbers). The per-call agent_variables are
sent in app_overrides; after the call the script checks the interaction's variables to confirm they arrived (else the
version's default variable values were used, and it says so).
Production calls to sellers need a telephony connection and the Instant Outbound API (outbounds), not this endpoint.

Usage: python app/sarvam/place_call.py --run data/runs_daytona/<id> --to +91XXXXXXXXXX [--version 3]
"""
import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
ORG, WS, KEY = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"], os.environ["SARVAM_AGENTS_API_KEY"]
APP = "VANI-person-b8c173ff-b272"
LANG_NAME = {"TELUGU": "Telugu", "HINDI": "Hindi", "GUJARATI": "Gujarati", "MARATHI": "Marathi", "TAMIL": "Tamil",
             "KANNADA": "Kannada", "MALAYALAM": "Malayalam", "BENGALI": "Bengali", "PUNJABI": "Punjabi", "ODIA": "Odia",
             "ENGLISH": "English"}


def find_interaction(since, decision_id, wait=600):
    """The interaction started after `since` on this app; (iid, agent_variables) once analytics lists it."""
    t0 = time.time()
    while time.time() - t0 < wait:
        r = requests.get(f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{APP}/interactions", headers={"X-API-Key": KEY},
                         params={"start_datetime": since.isoformat(), "end_datetime": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                                 "limit": 20}, timeout=30)
        items = r.json().get("items", []) if r.ok else []
        if items:
            it = sorted(items, key=lambda x: x.get("start_datetime") or x.get("interaction_id"))[-1]
            return it.get("interaction_id"), it.get("agent_variables") or {}
        time.sleep(30)
    return None, {}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--to", required=True, help="whitelisted test number, e.g. +91XXXXXXXXXX")
    a.add_argument("--version", type=int, default=3)
    a.add_argument("--no-wait", action="store_true", help="do not wait for the interaction record")
    p = a.parse_args()
    v = json.load(open(os.path.join(p.run, "05_sarvam_vars.json"), encoding="utf-8"))
    lang = LANG_NAME.get(str(v.get("persona_language")).upper(), "Hindi")
    since = datetime.now(timezone.utc) - timedelta(seconds=30)
    # 2026-10-10: agent_variables under user_config.app_overrides did NOT reach the call (the version defaults were used);
    # also send them at app_config.agent_variables, where the Instant Outbound API takes them, and check again.
    body = {"app_config": {"app_id": APP, "app_version": p.version, "agent_variables": v,
                           "user_config": {"app_overrides": {"initial_language_name": lang, "agent_variables": v}}},
            "phone_numbers": [p.to]}
    r = requests.post(f"https://apps.sarvam.ai/api/scheduling/v1/orgs/{ORG}/workspaces/{WS}/playground-test",
                      headers={"X-API-Key": KEY, "Content-Type": "application/json"}, json=body, timeout=60)
    res = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
    ok = r.ok and all(x.get("success") for x in res.get("responses", [{}]))
    print(json.dumps({"http": r.status_code, "placed": ok, "language": lang, "version": p.version,
                      "attempt": [(x.get("attempt_data") or {}).get("attempt_id") for x in res.get("responses", [])],
                      "error": [x.get("error") for x in res.get("responses", []) if x.get("error")] or res.get("error")}))
    if not ok or p.no_wait:
        return
    print("call placed: answer the phone. Waiting for the interaction record ...", flush=True)
    iid, av = find_interaction(since, v.get("decision_id"))
    arrived = av.get("decision_id") == v.get("decision_id") and av.get("persona_language") == v.get("persona_language")
    print(json.dumps({"interaction": iid, "per_call_variables_arrived": arrived,
                      "note": "per-call variables used" if arrived else "the version's default variable values were used"}))
    print(f"INTERACTION {iid}")


if __name__ == "__main__":
    main()
