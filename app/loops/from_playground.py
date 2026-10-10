"""from_playground.py: console playground (text) chat -> 06_call.json + 07_outcome.json, so close_loop can run on it.

Playground chats are not in the analytics feed that app/sarvam/collect_call.py reads, and their post-call labels stay
empty (the chat is never ended). This adapter takes:
  --chat    the saved playground replies ({session: {interaction_id, turns: [{seller, data: {text}}]}})
  --record  the interaction record from app-authoring .../interactions/<id> (agent_variables incl. switch_log)
Usage: python app/loops/from_playground.py --run data/runs/<id> --chat <smoke raw json> --record <record json> --session S1
"""
import argparse
import json
import os
from datetime import datetime, timezone


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    return json.loads(d) if isinstance(d, str) else d


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--chat", required=True)
    a.add_argument("--record", required=True)
    a.add_argument("--session", required=True, help="session key in the chat file, e.g. S1_hook_objection")
    p = a.parse_args()
    chat, rec = load(p.chat)[p.session], load(p.record)
    av = rec.get("agent_variables") or {}
    transcript = []
    for t in chat["turns"]:
        if t.get("seller"):
            transcript.append({"role": "user", "content": t["seller"]})
        transcript.append({"role": "assistant", "content": (t.get("data") or {}).get("text", "")})
    log = av.get("switch_log")
    log = json.loads(log) if isinstance(log, str) and log else (log or [])
    did = av.get("decision_id") or os.path.basename(p.run)
    call = {"decision_id": did, "interaction_id": rec.get("interaction_id"), "channel": "playground_text",
            "transcript": transcript, "agent_variables": av, "switch_log": log,
            "collected_at": datetime.now(timezone.utc).isoformat()}
    outcome = {"decision_id": did, "interaction_id": rec.get("interaction_id"),
               "meeting_fixed": str(av.get("meeting_fixed") or "no").lower() == "yes", "meeting_slot": av.get("meeting_slot") or "",
               "final_seller_mode": av.get("seller_mode"), "meeting_held": None,
               "sarvam_labels": {k: av.get(k) or None for k in ("call_summary", "call_outcome", "main_objection", "hook_reaction",
                                                                "persona_fit", "seller_mood_end", "end_language")},
               "note": "playground text chat: never ended, so Sarvam post-call labels are empty; test data, not a real outcome"}
    json.dump(call, open(os.path.join(p.run, "06_call.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(outcome, open(os.path.join(p.run, "07_outcome.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"turns": len(transcript), "switch_rows": len(log), "meeting_fixed": outcome["meeting_fixed"]}))


if __name__ == "__main__":
    main()
