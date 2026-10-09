"""PreToolUse hook: the agent may write only 02_review.json, 04_persona.json and status.json in $VANI_RUN.
Blocks edits to the skill, facts.json, prior.json, read_log.jsonl and the seller folder (exit 2 = block, reason on stderr)."""
import json
import os
import re
import sys

ev = json.load(sys.stdin)
run = os.path.abspath(os.environ.get("VANI_RUN", "/nonexistent"))
ti = ev.get("tool_input") or {}
ALLOWED = {"02_review.json", "04_persona.json", "status.json"}
if ev.get("tool_name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    p = os.path.abspath(ti.get("file_path") or ti.get("notebook_path") or "")
    if not (os.path.dirname(p) == run and os.path.basename(p) in ALLOWED):
        print(f"BLOCKED: you may only write {sorted(ALLOWED)} in {run}; not {p}", file=sys.stderr)
        sys.exit(2)
if ev.get("tool_name") == "Bash":
    cmd = ti.get("command") or ""
    if re.search(r"(read_log\.jsonl|facts\.json|prior\.json|/skills/vani-persona/)", cmd) and re.search(r"(>|\btee\b|\bsed -i\b|\brm\b|\bmv\b|\bcp\b|python3? .*(open\(.*['\"]w))", cmd):
        print("BLOCKED: do not modify facts, prior, the read log or the skill", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
