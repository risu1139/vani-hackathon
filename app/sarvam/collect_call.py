"""Pull finished VANI calls from the Sarvam Analytics API into data/runs/<decision_id>/ (plan §4).

  python app/sarvam/collect_call.py --interaction-id 20261010/abcd-12:00:00-1234
  python app/sarvam/collect_call.py --since 2026-10-10T10:00:00+05:30 [--until ...] [--app <app_id>]

Writes, per interaction:
  06_call.json     interaction id, app, timestamps, duration, ended_by, language, avg agent response time, audio_url,
                   transcript (from /transcripts), agent_variables, switch_log (parsed), decision_id
  07_outcome.json  meeting_fixed (yes/no), meeting_slot, ended_by, opted_out, final seller_mode
data/ is git-ignored (PII rules). Auth: header X-API-Key = SARVAM_AGENTS_API_KEY from .env (never printed).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://apps.sarvam.ai/api/analytics/v1"
META = ("interaction_id", "start_datetime", "end_datetime", "created_at", "duration_in_seconds", "ended_by",
        "language_name", "average_agent_response_time_in_seconds", "num_messages", "audio_url", "has_log_issues",
        "is_debug_call", "app_version", "user_identifier")


def load_env():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def default_app():
    p = ROOT / "app" / "sarvam" / "agent.json"
    return json.loads(p.read_text(encoding="utf-8"))["app_id"] if p.exists() else os.environ["SARVAM_AGENT_APP_ID"]


def _get(url, **params):
    r = requests.get(url, params=params, timeout=30, headers={"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]})
    r.raise_for_status()
    return r.json()


def list_interactions(app, start, end):
    org, ws = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
    out, offset = [], 0
    while True:
        items = _get(f"{BASE}/{org}/{ws}/{app}/interactions", start_datetime=start.isoformat(),
                     end_datetime=end.isoformat(), limit=100, offset=offset).get("items", [])
        out += items
        if len(items) < 100:
            return out
        offset += 100


def transcript(app, iid):
    org, ws = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
    try:
        return _get(f"{BASE}/{org}/{ws}/{app}/transcripts/{iid}").get("messages", [])
    except Exception as e:  # the transcript can lag a few seconds behind the interaction row
        return [{"error": str(e)[:200]}]


def _json(v, default):
    try:
        return json.loads(v) if isinstance(v, str) and v else (v if v is not None else default)
    except Exception:
        return default


def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:120]


POST_CALL = ("call_summary", "call_outcome", "main_objection", "hook_reaction", "persona_fit", "seller_mood_end", "end_language")


def build(app, item):
    av = item.get("agent_variables") or {}
    iid = item.get("interaction_id", "")
    decision_id = av.get("decision_id") or f"no_decision_{safe(iid)}"
    log = _json(av.get("switch_log"), [])
    call = {"decision_id": decision_id, "app_id": app, **{k: item.get(k) for k in META if k in item},
            "transcript": transcript(app, iid), "agent_variables": av, "switch_log": log,
            "collected_at": datetime.now(timezone.utc).isoformat()}
    outcome = {"decision_id": decision_id, "interaction_id": iid,
               "meeting_fixed": (av.get("meeting_fixed") or "no").lower() == "yes",
               "meeting_slot": av.get("meeting_slot") or "", "ended_by": item.get("ended_by"),
               "opted_out": av.get("seller_mode") == "opt_out" or any(r.get("to") == "opt_out" for r in log if isinstance(r, dict)),
               "final_seller_mode": av.get("seller_mode"), "meeting_held": None,  # future work (not in the hackathon)
               "duration_in_seconds": item.get("duration_in_seconds"),
               # Sarvam post-call labels (contract: set_after_call_by_sarvam); cheap, the frontier review is the judge
               "sarvam_labels": {k: av.get(k) for k in POST_CALL}}
    return decision_id, call, outcome


def write(decision_id, call, outcome, root):
    d = root / safe(decision_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "06_call.json").write_text(json.dumps(call, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "07_outcome.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--interaction-id")
    g.add_argument("--since", help="ISO time, e.g. 2026-10-10T10:00:00+05:30")
    ap.add_argument("--until", help="ISO time (default now + 5 min)")
    ap.add_argument("--app", help="Sarvam app id (default app/sarvam/agent.json)")
    ap.add_argument("--hours", type=float, default=24, help="look-back window for --interaction-id")
    ap.add_argument("--out", default=str(ROOT / "data" / "runs"))
    a = ap.parse_args(argv)
    load_env()
    app = a.app or default_app()
    now = datetime.now(timezone.utc)
    end = datetime.fromisoformat(a.until) if a.until else now + timedelta(minutes=5)
    start = datetime.fromisoformat(a.since) if a.since else now - timedelta(hours=a.hours)
    items = list_interactions(app, start, end)
    if a.interaction_id:
        items = [i for i in items if i.get("interaction_id") == a.interaction_id]
        if not items:
            sys.exit(f"interaction {a.interaction_id} not found in the last {a.hours} h of app {app}")
    for it in items:
        did, call, outcome = build(app, it)
        d = write(did, call, outcome, Path(a.out))
        print(f"{it.get('interaction_id')} -> {d.relative_to(ROOT) if d.is_relative_to(ROOT) else d} "
              f"meeting_fixed={outcome['meeting_fixed']} rows={len(call['switch_log'])}")
    return items


if __name__ == "__main__":
    main()
