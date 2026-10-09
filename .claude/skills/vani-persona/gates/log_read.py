"""PostToolUse hook: records every file the agent reads or searches into $VANI_RUN/read_log.jsonl.
The agent cannot write this log (pre_gate.py blocks it). Bash reads of the seller folder (cat/head/grep/sed) are logged too (review M9)."""
import json
import os
import re
import sys

ev = json.load(sys.stdin)
run = os.environ.get("VANI_RUN")
if not run:
    sys.exit(0)
ti = ev.get("tool_input") or {}
paths = []
if ev.get("tool_name") == "Read":
    paths.append(ti.get("file_path"))
elif ev.get("tool_name") in ("Grep", "Glob"):
    paths.append(ti.get("path"))
elif ev.get("tool_name") == "Bash":
    cmd = ti.get("command") or ""
    if re.search(r"\b(cat|head|tail|sed|grep|rg|less|awk|jq)\b", cmd):
        paths += re.findall(r"(/[^\s'\"|;&>]+\.(?:md|json))", cmd) + re.findall(r"([A-Za-z]:[\/][^\s'\"|;&>]+\.(?:md|json))", cmd)
with open(os.path.join(run, "read_log.jsonl"), "a", encoding="utf-8") as f:
    for p in paths:
        if p:
            f.write(json.dumps({"tool": ev.get("tool_name"), "path": os.path.abspath(p)}) + "\n")
