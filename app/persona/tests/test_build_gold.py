"""M17 gold-set script: pure parts only (no Jev call, no real seller text)."""
import hashlib
import json

import build_gold as G


def test_prefilter_buckets():
    assert G.bucket("bhai dobara call mat karna") == "opt_out"
    assert G.bucket("aap robot ho kya") == "bot_question"
    assert G.bucket("kitni baar call karoge") == "frustrated"
    assert G.bucket("samajh nahi aaya") == "confused"
    assert G.bucket("abhi busy hoon") == "rushed"
    assert G.bucket("kitna charge hai") == "interested"
    assert G.bucket("haan ji boliye") == "neutral"


def test_primary_priority():
    assert G.primary(["interested", "frustrated"]) == "frustrated"
    assert G.primary(["rushed", "opt_out"]) == "opt_out"
    assert G.primary([]) == "neutral"


def test_scrub_removes_phone_and_email():
    assert "[phone]" in G.scrub("mera number 9876543210 hai") and "[email]" in G.scrub("mail a.b@c.com")


def test_hand_rows_cover_all_signals():
    rows = G.hand_rows()
    labels = {r["label"] for r in rows}
    assert {"rushed", "frustrated", "confused", "interested", "bot_question", "neutral"} <= labels
    assert all(r["label_by"] == "hand" and r["source"].startswith("hand:") for r in rows)


def test_write_merges(tmp_path, monkeypatch):
    cand, jev = tmp_path / "c.jsonl", tmp_path / "j.jsonl"
    texts = ["synthetic one", "synthetic two"]
    cand.write_text("".join(json.dumps({"text": t, "prefilter": "neutral"}) + "\n" for t in texts), encoding="utf-8")
    scores = [{"opt_out": 0.9, "rushed": 0.7}, {"rushed": 0.1}]
    jev.write_text("".join(json.dumps({"key": hashlib.sha1(t.encode()).hexdigest(), "model": "m", "scores": s}) + "\n"
                           for t, s in zip(texts, scores)), encoding="utf-8")
    for k, v in {"CAND": cand, "JEV": jev, "OUT": tmp_path / "o.jsonl", "COUNTS": tmp_path / "n.json"}.items():
        monkeypatch.setattr(G, k, str(v))
    rows, counts = G.write()
    ps = [r for r in rows if r["source"] == "ps07_call_turns"]
    assert [r["label"] for r in ps] == ["opt_out", "neutral"] and ps[0]["labels"] == ["rushed", "opt_out"]
    assert counts["by_source"]["ps07_call_turns"] == 2
