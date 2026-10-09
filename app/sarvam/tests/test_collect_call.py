"""Offline test of collect_call.build/write (no network: transcript() is stubbed)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collect_call as cc  # noqa: E402


def test_build_and_write(tmp_path, monkeypatch):
    monkeypatch.setattr(cc, "transcript", lambda app, iid: [{"role": "user", "content": "x"}])
    item = {"interaction_id": "20261010/ab:12-x", "duration_in_seconds": 61, "ended_by": "agent", "audio_url": "u",
            "agent_variables": {"decision_id": "d1", "meeting_fixed": "yes", "meeting_slot": "kal 5 baje",
                                "seller_mode": "interested",
                                "switch_log": json.dumps([{"to": "rushed", "cue": "busy"}])}}
    did, call, outcome = cc.build("APP", item)
    assert did == "d1" and call["switch_log"][0]["cue"] == "busy" and call["audio_url"] == "u"
    assert outcome["meeting_fixed"] is True and outcome["meeting_slot"] == "kal 5 baje" and not outcome["opted_out"]
    d = cc.write(did, call, outcome, tmp_path)
    assert (d / "06_call.json").exists() and json.loads((d / "07_outcome.json").read_text(encoding="utf-8"))["decision_id"] == "d1"


def test_no_decision_id_and_opt_out(monkeypatch):
    monkeypatch.setattr(cc, "transcript", lambda app, iid: [])
    did, _, outcome = cc.build("APP", {"interaction_id": "a/b:c", "agent_variables": {"switch_log": "[{\"to\": \"opt_out\"}]"}})
    assert did.startswith("no_decision_") and "/" not in did and outcome["opted_out"] and outcome["meeting_fixed"] is False
