"""T3b: the hook scripts. pre_gate must block writes outside the allowed run files; log_read must record reads (incl. Bash)."""
import json
import os
import subprocess
import sys

G = os.path.join(os.path.dirname(__file__), "..", "gates")


def hook(name, event, run):
    return subprocess.run([sys.executable, os.path.join(G, name)], input=json.dumps(event), text=True,
                          capture_output=True, env=dict(os.environ, VANI_RUN=str(run)))


def test_pre_gate_allows_persona(tmp_path):
    r = hook("pre_gate.py", {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "04_persona.json")}}, tmp_path)
    assert r.returncode == 0


def test_pre_gate_blocks_facts(tmp_path):
    r = hook("pre_gate.py", {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "facts.json")}}, tmp_path)
    assert r.returncode == 2 and "BLOCKED" in r.stderr


def test_pre_gate_blocks_read_log_bash(tmp_path):
    r = hook("pre_gate.py", {"tool_name": "Bash", "tool_input": {"command": f"echo x > {tmp_path}/read_log.jsonl"}}, tmp_path)
    assert r.returncode == 2


def test_pre_gate_blocks_skill_edit(tmp_path):
    r = hook("pre_gate.py", {"tool_name": "Edit", "tool_input": {"file_path": "/home/daytona/.claude/skills/vani-persona/scripts/validate_persona.py"}}, tmp_path)
    assert r.returncode == 2


def test_log_read_records_read_and_bash(tmp_path):
    hook("log_read.py", {"tool_name": "Read", "tool_input": {"file_path": "/x/seller/buyleads.md"}}, tmp_path)
    hook("log_read.py", {"tool_name": "Bash", "tool_input": {"command": "grep -n E05 /x/seller/core.md"}}, tmp_path)
    rows = [json.loads(x) for x in (tmp_path / "read_log.jsonl").read_text().splitlines()]
    paths = {os.path.basename(r["path"]) for r in rows}
    assert {"buyleads.md", "core.md"} <= paths
