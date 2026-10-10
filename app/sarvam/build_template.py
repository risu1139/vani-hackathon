"""build_template.py: the ONE-TIME agent template change, built only from repo files (no hand edits in the console).

The agent holds one fixed template; every seller's text arrives per call as variables (place_call.py / SDK session),
and OnStart applies the voice, pace, pitch, language and opening. After this template is committed, no per-seller
step touches the console.

Writes data/sarvam_backups/template_change.json:
  instructions  app/sarvam/vani_prompt.md with every @x turned into {{x}} (Sarvam's placeholder form)
  variables     every set_before_call key of app/contracts/sarvam_vars.contract.json (each must be defined, or Sarvam
                drops the per-call value); empty default values, so a call without variables is visibly wrong, never
                another seller
  tool_names    the during-call tools the model may call (uploading vani_tools.py registers them; listing enables them)
  sha256        of the instructions, to check what a committed version holds

The authoring API accepts only the console login (the SDK has no authoring calls), so the apply step runs where that
login is; it must use exactly this file.

Usage: python app/sarvam/build_template.py
"""
import hashlib
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS = ["read_seller_signal", "book_meeting"]


def build():
    sk = open(os.path.join(ROOT, "app", "sarvam", "vani_prompt.md"), encoding="utf-8").read().replace("\r\n", "\n")
    instructions = re.sub(r"@([a-z_]+)", r"{{\1}}", sk)
    contract = json.load(open(os.path.join(ROOT, "app", "contracts", "sarvam_vars.contract.json"), encoding="utf-8"))
    slots = sorted(set(re.findall(r"\{\{(\w+)\}\}", instructions)))
    variables = list(contract["set_before_call"])
    missing = [s for s in slots if s not in variables]
    if missing:
        raise SystemExit(f"skeleton slots not in the contract: {missing}")
    out = {"instructions": instructions, "variables": variables, "tool_names": TOOLS, "slots": slots,
           "sha256": hashlib.sha256(instructions.encode("utf-8")).hexdigest()}
    path = os.path.join(ROOT, "data", "sarvam_backups", "template_change.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return path, out


if __name__ == "__main__":
    p, o = build()
    print(json.dumps({"file": os.path.relpath(p, ROOT), "slots": o["slots"], "variables": len(o["variables"]),
                      "tools": o["tool_names"], "sha256": o["sha256"][:16]}))
