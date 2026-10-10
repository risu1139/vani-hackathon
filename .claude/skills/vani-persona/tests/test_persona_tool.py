"""persona_tool.py: every write-time check refuses the bad case and allows the good one (plan §5a)."""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import fixture as F  # noqa: E402

TOOL = os.path.join(os.path.dirname(__file__), "..", "scripts", "persona_tool.py")


@pytest.fixture
def env(tmp_path, monkeypatch):
    run, hp = F.make(tmp_path)
    e = dict(os.environ, VANI_RUN=str(run), VANI_HIERARCHY=str(hp), VANI_PY=sys.executable, PYTHONIOENCODING="utf-8")
    monkeypatch.setenv("VANI_HIERARCHY", str(hp))
    return run, e


def t(e, *args):
    r = subprocess.run([sys.executable, TOOL] + list(args), env=e, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def top_ids(e, field):
    rc, out = t(e, "probe", "--field", field, "--json")
    return [h["id"] for h in json.loads(out.strip().splitlines()[-1])["hits"][:3]]


def ready(e):
    assert t(e, "select", "--persona", "P2", "--reason", "warm local helper fits")[0] == 0
    for f in ("pace", "formality", "voice_gender", "language_start"):
        t(e, "probe", "--field", f)
    t(e, "probe", "--hook", "hook.profile_gap")


def decide_all(e):
    assert t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "busy last call",
             "--cite", "calls/C01#C01.T2", "--quote", "abhi busy hoon baad me call karo")[0] == 0
    assert t(e, "decide", "--field", "formality", "--value", "medium", "--type", "seller_evidence", "--reason", "proprietor",
             "--cite", "core.md#A04", "--quote", "Proprietor")[0] == 0
    assert t(e, "decide", "--field", "voice_gender", "--value", "F", "--type", "seller_evidence", "--reason", "female seller",
             "--cite", "core.md#A07", "--quote", "Female")[0] == 0
    assert t(e, "decide", "--field", "language_start", "--value", "TELUGU", "--type", "seller_evidence", "--reason", "Telangana",
             "--cite", "core.md#B01", "--quote", "Hyderabad, Telangana")[0] == 0
    assert t(e, "hook", "--id", "hook.profile_gap", "--decision", "rejected", "--reason", "seller sees photos as basic")[0] == 0


def test_decide_before_select_and_probe_refused(env):
    run, e = env
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.0", "--type", "start_persona", "--reason", "x", "--searched", "x")
    assert rc == 1 and "select a persona first" in out and "probe the field first" in out


def test_select_outside_top2_refused(env):
    run, e = env
    rc, out = t(e, "select", "--persona", "P6", "--reason", "x")
    assert rc == 1 and "not one of" in out


def test_seller_evidence_needs_a_hit_and_a_real_quote(env):
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x",
                "--cite", "calls/C01#C01.T2", "--quote", "the seller said nothing")
    assert rc == 1 and "quote not found" in out
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x",
                "--cite", "core.md#A04", "--quote", "Proprietor")
    assert rc == 1 and "must be a hit" in out


def test_quote_from_another_turn_refused(env):
    """Review fix 1: the cite C01.T2 is a hit, but the quote comes from C01.T1."""
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x",
                "--cite", "calls/C01#C01.T2", "--quote", "C01.T1 bot: Namaste ji")
    assert rc == 1 and "not found in that turn" in out


def test_quote_too_short_refused(env):
    """Review fix 2: a 2-word quote that is not a whole line."""
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x",
                "--cite", "calls/C01#C01.T2", "--quote", "busy hoon")
    assert rc == 1 and "too short" in out


def test_start_value_for_fields_without_card(env):
    """voice_gender starts from the card + state rules (the fixture's rule says F), never a free value."""
    run, e = env
    ready(e)
    args = ["decide", "--field", "voice_gender", "--value", "M", "--type", "start_persona", "--reason", "x", "--searched", "s"]
    args += [f"--answer={i}=no" for i in top_ids(e, "voice_gender")]
    rc, out = t(e, *args)
    assert rc == 1 and "keeps the start value" in out
    args[4] = "F"
    assert t(e, *args)[0] == 0


def test_quote_normalised(env):
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x",
                "--cite", "calls/C01#C01.T2", "--quote", "ABHI  busy hoon   baad me")
    assert rc == 0, out


def test_start_persona_keeps_card_value_and_answers_top_hits(env):
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "1.1", "--type", "start_persona", "--reason", "x", "--searched", "s")
    assert rc == 1 and "keeps the start value" in out and "answer the top hit" in out
    args = ["decide", "--field", "pace", "--value", "0.95", "--type", "start_persona", "--reason", "card", "--searched", "busy words"]
    for i in top_ids(e, "pace"):
        args += ["--answer", f"{i}=old call, seller was fine later"]
    rc, out = t(e, *args)
    assert rc == 0, out


def test_hierarchy_needs_brief_data(env):
    run, e = env
    ready(e)
    args = ["decide", "--field", "formality", "--value", "medium", "--type", "hierarchy", "--level", "L4", "--group", "medium",
            "--reason", "x", "--searched", "s"] + [f"--answer={i}=no" for i in top_ids(e, "formality")]
    rc, out = t(e, *args)
    assert rc == 1 and "must match the brief" in out


def test_hierarchy_ok_with_brief(tmp_path, monkeypatch):
    prior = dict(F.PRIOR, brief={"formality": {"level_used": "L4", "value_groups": {"medium": {"n": 40, "rate": 0.18}}}})
    run, hp = F.make(tmp_path, prior=prior)
    e = dict(os.environ, VANI_RUN=str(run), VANI_HIERARCHY=str(hp), PYTHONIOENCODING="utf-8")
    ready(e)
    args = ["decide", "--field", "formality", "--value", "medium", "--type", "hierarchy", "--level", "L4", "--group", "medium",
            "--reason", "x", "--searched", "s"] + [f"--answer={i}=a title, not a style" for i in top_ids(e, "formality")]
    assert t(e, *args)[0] == 0


def test_range_and_group(env):
    run, e = env
    ready(e)
    rc, out = t(e, "decide", "--field", "pace", "--value", "2.0", "--type", "seller_evidence", "--reason", "x",
                "--cite", "calls/C01#C01.T2", "--quote", "abhi busy hoon baad me")
    assert rc == 1 and "outside" in out
    rc, out = t(e, "decide", "--field", "formality", "--value", "posh", "--type", "seller_evidence", "--reason", "x",
                "--cite", "core.md#A04", "--quote", "Proprietor")
    assert rc == 1 and "no value group" in out


def test_text_rejects_fields(env, tmp_path):
    run, e = env
    p = tmp_path / "draft.json"
    p.write_text(json.dumps(dict(F.TEXT, dimensions={"pace": {"value": 1.2}})), encoding="utf-8")
    rc, out = t(e, "text", "--file", str(p))
    assert rc == 1 and "dimensions" in out


def test_finalize_refuses_until_done_then_writes(env):
    run, e = env
    rc, out = t(e, "finalize")
    assert rc == 1 and "not done yet" in out
    ready(e)
    decide_all(e)
    (run / "draft_text.json").write_text(json.dumps(F.TEXT), encoding="utf-8")
    assert t(e, "text", "--file", str(run / "draft_text.json"))[0] == 0
    rc, out = t(e, "finalize")
    assert rc == 0, out
    p = json.loads((run / "04_persona.json").read_text(encoding="utf-8"))
    assert p["dimensions"]["pace"]["reason_type"] == "seller_evidence" and p["prior"]["chosen"] == "P2"
    assert any(json.loads(x)["kind"] == "finalize" for x in (run / "ledger.jsonl").read_text(encoding="utf-8").splitlines())


def test_finalize_runs_validator(env):
    run, e = env
    ready(e)
    decide_all(e)
    bad = dict(F.TEXT, opening="Namaste, main IndiaMART ki AI assistant hoon")
    (run / "draft_text.json").write_text(json.dumps(bad), encoding="utf-8")
    t(e, "text", "--file", str(run / "draft_text.json"))
    rc, out = t(e, "finalize")
    assert rc == 1 and "banned word" in out and not (run / "04_persona.json").exists()


def test_ranking_more_terms_first(tmp_path, monkeypatch):
    import persona_tool as PT
    run, hp = F.make(tmp_path)
    (run / "seller" / "core.md").write_text("### B03 Languages\nbusy hoon\nbusy hoon, baad me call karna\n", encoding="utf-8")
    spec = F.HIERARCHY["fields"]["pace"]
    hits = PT.search(str(run / "seller"), spec, F.TODAY)
    assert hits[0]["score"] == 2  # the line with 2 distinct terms is ranked first


def test_start_value_precedence_rule_beats_card():
    """Review: card says M, a state rule says F -> F, in the one function both the tool and the validator use."""
    import persona_tool as PT
    facts = {"start_rules": {"voice_gender": {"value": "F", "rule": "tense seller"}, "language_start": None, "empathy_add": []}}
    assert PT.start_value("voice_gender", {"voice_gender": "M"}, facts) == "F"
    assert PT.start_value("voice_gender", {"voice_gender": "M"}, {"start_rules": {"voice_gender": None}}) == "M"
    assert PT.start_value("empathy", {"empathy": "warm"}, {"start_rules": {"empathy_add": [{"text": "acknowledge the complaint"}]}}) \
        == "warm; acknowledge the complaint"
