"""PreToolUse hook (Write|Edit|MultiEdit|NotebookEdit): the agent may write only draft_text.json and status.json in
$VANI_RUN. 04_persona.json and 02_review.json are written by persona_tool.py (enforcement plan §5a, item 2); a Bash
bypass is not parsed here: the launcher's sha check and validator catch it after the turn.

Exit 2 = block (reason on stderr). Input the gate cannot read = allow (the launcher is the backstop).
When it blocks, it touches <run>/.pre_gate_fired (the launch self-test looks for it).
"""
import json
import os
import sys

TOOL_ONLY = {"04_persona.json", "02_review.json", "ledger.jsonl"}
ALLOWED = {"draft_text.json", "status.json"}


def canon(p):
    return os.path.normcase(os.path.realpath(os.path.abspath(p)))


def main():
    try:
        ev = json.load(sys.stdin)
        run = os.environ.get("VANI_RUN") or ""
        ti = ev.get("tool_input") or {}
        path = ti.get("file_path") or ti.get("notebook_path") or ""
    except Exception:
        return 0
    if not run or ev.get("tool_name") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return 0
    p, r = canon(path), canon(run)
    name = os.path.basename(p)
    tool = f"\"$VANI_PY\" {canon(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts', 'persona_tool.py'))}"
    if os.path.dirname(p) == r and name in ALLOWED:
        return 0
    if name in TOOL_ONLY:
        msg = (f"{name} is written by the tool, not by hand. Use: {tool} status (then select / probe / decide / hook / "
               f"text --file {os.path.join(run, 'draft_text.json')} / finalize)")
    else:
        msg = f"you may only write {sorted(ALLOWED)} in {run}; not {path}"
    try:
        open(os.path.join(run, ".pre_gate_fired"), "a").close()
    except OSError:
        pass
    print("BLOCKED: " + msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
