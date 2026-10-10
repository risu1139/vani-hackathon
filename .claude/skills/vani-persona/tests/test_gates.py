"""The two hooks, both directions. pre_gate: only draft_text.json / status.json may be written by hand; the persona is
the tool's. stop_gate: refuses once with all failures; allows on stop_hook_active; allows a finalized, valid run."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fixture as F  # noqa: E402

G = os.path.join(os.path.dirname(__file__), "..", "gates")
TOOL = os.path.join(os.path.dirname(__file__), "..", "scripts", "persona_tool.py")


def hook(name, event, run, extra=None):
    raw = event if isinstance(event, str) else json.dumps(event)
    return subprocess.run([sys.executable, os.path.join(G, name)], input=raw, text=True, capture_output=True,
                          env=dict(os.environ, VANI_RUN=str(run), PYTHONIOENCODING="utf-8", **(extra or {})))


def write(run, name):
    return {"tool_name": "Write", "tool_input": {"file_path": str(run / name), "content": "{}"}}


def test_pre_gate_blocks_persona_and_review(tmp_path):
    run, _ = F.make(tmp_path)
    for name in ("04_persona.json", "02_review.json", "ledger.jsonl"):
        r = hook("pre_gate.py", write(run, name), run)
        assert r.returncode == 2 and "persona_tool.py" in r.stderr
    assert (run / ".pre_gate_fired").exists()


def test_pre_gate_allows_draft_and_status(tmp_path):
    run, _ = F.make(tmp_path)
    for name in ("draft_text.json", "status.json"):
        assert hook("pre_gate.py", write(run, name), run).returncode == 0


def test_pre_gate_blocks_elsewhere_and_edit(tmp_path):
    run, _ = F.make(tmp_path)
    assert hook("pre_gate.py", write(run / "seller", "core.md"), run).returncode == 2
    ev = {"tool_name": "Edit", "tool_input": {"file_path": str(run / "04_persona.json"), "old_string": "a", "new_string": "b"}}
    assert hook("pre_gate.py", ev, run).returncode == 2


def test_pre_gate_case_and_slash_insensitive_on_windows(tmp_path):
    run, _ = F.make(tmp_path)
    p = str(run / "draft_text.json")
    p = (p[0].swapcase() + p[1:]).replace("\\", "/") if os.name == "nt" else p
    ev = {"tool_name": "Write", "tool_input": {"file_path": p, "content": "{}"}}
    assert hook("pre_gate.py", ev, run).returncode == 0


def test_pre_gate_allows_on_garbage_and_other_tools(tmp_path):
    run, _ = F.make(tmp_path)
    assert hook("pre_gate.py", "not json", run).returncode == 0
    assert hook("pre_gate.py", {"tool_name": "Bash", "tool_input": {"command": "cat x"}}, run).returncode == 0


def test_stop_gate_refuses_once_with_fix(tmp_path):
    run, hp = F.make(tmp_path)
    r = hook("stop_gate.py", {"stop_hook_active": False}, run, {"VANI_HIERARCHY": str(hp)})
    out = json.loads(r.stdout)
    assert out["decision"] == "block" and "not finalized" in out["reason"] and "persona_tool.py" in out["reason"]
    r2 = hook("stop_gate.py", {"stop_hook_active": True}, run, {"VANI_HIERARCHY": str(hp)})
    assert r2.stdout.strip() == ""


def test_stop_gate_allows_finalized_and_catches_hand_edit(tmp_path):
    run, hp = F.make(tmp_path)
    e = dict(os.environ, VANI_RUN=str(run), VANI_HIERARCHY=str(hp), PYTHONIOENCODING="utf-8")
    t = lambda *a: subprocess.run([sys.executable, TOOL] + list(a), env=e, capture_output=True, text=True, encoding="utf-8")
    t("select", "--persona", "P2", "--reason", "x")
    for f in ("pace", "formality", "voice_gender", "language_start"):
        t("probe", "--field", f)
    t("decide", "--field", "pace", "--value", "1.1", "--type", "seller_evidence", "--reason", "x", "--cite", "calls/C01#C01.T2", "--quote", "busy hoon")
    t("decide", "--field", "formality", "--value", "medium", "--type", "seller_evidence", "--reason", "x", "--cite", "core.md#A04", "--quote", "Proprietor")
    t("decide", "--field", "voice_gender", "--value", "F", "--type", "seller_evidence", "--reason", "x", "--cite", "core.md#A07", "--quote", "Female")
    t("decide", "--field", "language_start", "--value", "TELUGU", "--type", "seller_evidence", "--reason", "x", "--cite", "core.md#B01", "--quote", "Telangana")
    t("probe", "--hook", "hook.profile_gap")
    t("hook", "--id", "hook.profile_gap", "--decision", "rejected", "--reason", "x")
    (run / "draft_text.json").write_text(json.dumps(F.TEXT), encoding="utf-8")
    t("text", "--file", str(run / "draft_text.json"))
    assert t("finalize").returncode == 0
    assert hook("stop_gate.py", {"stop_hook_active": False}, run, {"VANI_HIERARCHY": str(hp)}).stdout.strip() == ""
    p = run / "04_persona.json"
    p.write_text(p.read_text(encoding="utf-8").replace("Do minute", "Teen minute"), encoding="utf-8")
    out = json.loads(hook("stop_gate.py", {"stop_hook_active": False}, run, {"VANI_HIERARCHY": str(hp)}).stdout)
    assert "changed after finalize" in out["reason"]


def test_stop_gate_dnc(tmp_path):
    run, hp = F.make(tmp_path, facts=dict(F.FACTS, true_guards=["guard.do_not_call"]))
    assert hook("stop_gate.py", {"stop_hook_active": False}, run).stdout.strip() == ""
    (run / "04_persona.json").write_text("{}", encoding="utf-8")
    assert "do_not_call" in json.loads(hook("stop_gate.py", {"stop_hook_active": False}, run).stdout)["reason"]
