"""M18 leakage test with a synthetic seller: nothing dated after as_of may reach any output file. Also m7 cache_hash."""
import glob
import json
import os

import pytest

import seller_context_builder as B

GLID = "900000001"
AS_OF = "2026-08-31"


def call(aid, when, summary):
    return {"attempt_id": aid, "fk_glusr_usr_id": GLID, "call_start_time": when, "disposition_label": "Call Later",
            "lead_call_summary": summary, "lead_call_duration": "60", "meeting_fixed": "0", "lead_bot_version": "v1",
            "redis_bucket": "b1", "call_attempt_count": "1"}


def turn(aid, n, text):
    return {"attempt_id": aid, "fk_glusr_usr_id": GLID, "speaker": "seller", "turn_no": str(n), "start_sec": str(n),
            "end_sec": str(n + 1), "text": text}


def evaluator(aid, quote):
    out = {"objection_analysis": [{"category": "price", "reasons": ["too costly"], "evidence_quotes": [quote]}]}
    return {"attempt_id": aid, "fk_glusr_usr_id": GLID, "eval_agent": "objections", "agent_output": json.dumps(out)}


def synthetic_files():
    return {
        "ps07_bot_calls": [call("A1", "2026-08-10 11:00:00", "BEFOREMARK seller asked to call later"),
                           call("A2", "2026-09-15 11:00:00", "LEAKCALL seller agreed to a meeting"),
                           call("A3", "", "LEAKNODATE call with no date")],
        "ps07_call_turns": [turn("A1", 1, "BEFORETURN abhi busy hoon"), turn("A2", 1, "LEAKTURN haan aa jaiye"),
                            turn("A9", 1, "LEAKORPHAN turn with no call")],
        "ps07_evaluator": [evaluator("A1", "BEFOREEVAL mehenga hai"), evaluator("A2", "LEAKEVAL quote")],
        "gc_enquiries": [{"seller_glid": GLID, "query_id": "Q1", "enquiry_date": "2026-08-01 10:00:00", "subject": "BEFOREENQ pipes",
                          "message": "need pipes"},
                         {"seller_glid": GLID, "query_id": "Q2", "enquiry_date": "2026-09-20 10:00:00", "subject": "LEAKENQ valves",
                          "message": "LEAKENQ need valves"}],
        "gc_enquiry_messages": [{"seller_glid": GLID, "query_id": "Q2", "reply_date": "2026-08-30 10:00:00", "reply_text": "LEAKMSG"}],
        "gc_whatsapp_messages": [{"glid": GLID, "entry_date": "2026-09-02 09:00:00", "campaign_name": "LEAKWA", "message_sender": "bot"}],
        "gc_whatsapp_chatbot": [{"glid": GLID, "entry_date": "2026-09-03 09:00:00", "user_message": "LEAKCHAT", "intent": "LEAKCHAT"}],
        "ps07_exec_calls": [{"fk_glusr_usr_id": GLID, "call_start_time": "2026-09-05 10:00:00", "status": "Answered", "module": "LEAKEXEC"}],
        "gc_exec_calls": [{"fk_glusr_usr_id": GLID, "call_start_time": "2026-09-05 10:00:00", "status": "Answered", "module": "LEAKEXEC"}],
        "btc_attempts": [{"fk_glusr_usr_id": GLID, "call_start_time": "2026-08-20 10:00:00", "redis_bucket": "BEFOREBTC"},
                         {"fk_glusr_usr_id": GLID, "call_start_time": "", "lead_sent_time": "2026-09-25 10:00:00", "redis_bucket": "LEAKBTC"}],
        "gc_buyleads_bought": [{"seller_glid": GLID, "purchase_date": "2026-09-01 00:00:01", "keyword": "LEAKBL", "buylead_id": "1"},
                               {"seller_glid": GLID, "purchase_date": "2026-08-31 23:00:00", "keyword": "BEFOREBL", "buylead_id": "2"}],
        "leap_call_logs": [{"fk_glusr_usr_id": GLID, "entered_on": "2026-09-09 10:00:00", "disposition_remarks": "LEAKLEAP"}],
        "ps07_seller_file": [{"fk_glusr_usr_id": GLID, "seller_city": "Testpur", "seller_state": "Teststate"}],
    }


def test_filter_drops_everything_after_as_of():
    files, dropped = B.filter_as_of(synthetic_files(), AS_OF)
    blob = json.dumps(files)
    assert "LEAK" not in blob
    for m in ("BEFOREMARK", "BEFORETURN", "BEFOREEVAL", "BEFOREENQ", "BEFOREBTC", "BEFOREBL"):
        assert m in blob
    assert dropped["ps07_bot_calls"] == 2 and dropped["ps07_call_turns"] == 2 and dropped["ps07_evaluator"] == 1
    assert files["ps07_seller_file"]  # undated snapshot kept


@pytest.fixture
def built(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "seller_rows", lambda g: synthetic_files())
    monkeypatch.setattr(B, "OUT_ASOF", str(tmp_path / "asof"))
    monkeypatch.setattr(B, "OUT", str(tmp_path / "ctx"))
    folder, _, how = B.build(GLID, use_api=False, as_of=AS_OF)
    assert how == "built"
    return folder


def test_build_as_of_has_no_leak(built):
    assert built.replace("\\", "/").endswith(f"asof/{AS_OF}/{GLID}")
    text = ""
    for f in glob.glob(os.path.join(built, "**", "*"), recursive=True):
        if os.path.isfile(f):
            text += open(f, encoding="utf-8").read()
    assert "LEAK" not in text
    assert "BEFOREMARK" in text and "BEFORETURN" in text
    ctx = json.load(open(os.path.join(built, "context.json"), encoding="utf-8"))
    assert ctx["as_of"] == AS_OF and ctx["as_of_dropped_rows"]["ps07_bot_calls"] == 2
    days = [c["days_ago"] for c in ctx["points"]["G00"]["value"]["calls"]]
    assert days and all(d is not None and d >= 0 for d in days)  # dates measured from as_of, never negative


def test_as_of_flags_api_points():
    P = {"A02": ("x", "users_detail.glusr_usr_companyname · gc_profile"), "E11": ({}, "pg-imblr peer statistic"),
         "C03": ("x", "ps07 seller file"), "G00": ({}, "ps07_bot_calls + ps07_evaluator"), "J01": ({}, "gc_whatsapp_messages")}
    f = B.as_of_flags(P)
    assert f["A02"] == {"as_of_unsafe": True} and f["E11"] == {"as_of_unsafe": True}
    assert f["C03"] == {"as_of_snapshot": True}
    assert "G00" not in f and "J01" not in f


def test_as_of_unsafe_written_to_context(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "seller_rows", lambda g: synthetic_files())
    monkeypatch.setattr(B, "OUT_ASOF", str(tmp_path / "asof"))
    folder, _, _ = B.build(GLID, use_api=False, as_of=AS_OF)
    ctx = json.load(open(os.path.join(folder, "context.json"), encoding="utf-8"))
    pts = ctx["points"]
    assert pts["E11"].get("as_of_unsafe") is True and pts["X05"].get("as_of_unsafe") is True
    assert "as_of_unsafe" not in pts["G00"]


def test_cache_hash_stable_and_sensitive(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "OUT", str(tmp_path / "ctx"))
    files = synthetic_files()
    monkeypatch.setattr(B, "seller_rows", lambda g: files)
    f1, _, _ = B.build(GLID, use_api=False, rebuild=True)
    h1 = json.load(open(os.path.join(f1, "context.json"), encoding="utf-8"))["cache_hash"]
    f2, _, _ = B.build(GLID, use_api=False, rebuild=True)
    h2 = json.load(open(os.path.join(f2, "context.json"), encoding="utf-8"))["cache_hash"]
    assert h1 == h2 and h1.startswith("sha256:")
    files["ps07_bot_calls"][0]["lead_call_summary"] += " changed"
    f3, _, _ = B.build(GLID, use_api=False, rebuild=True)
    assert json.load(open(os.path.join(f3, "context.json"), encoding="utf-8"))["cache_hash"] != h1
