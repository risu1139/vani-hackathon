"""A stand-in for the claude CLI in the launcher tests (VANI_CLAUDE=<this file>). It calls the REAL hooks from the
settings file the launcher wrote, the way Claude Code would. STUB_MODE picks the behaviour of the main turn:
  good      runs the persona_tool flow (select, probe, decide, hook, text, finalize)
  bypass    hand-writes 04_persona.json and 02_review.json with Python (no Write tool, no persona_tool)
  edit      runs the good flow, then edits 04_persona.json after finalize
  tamper    runs the good flow, then changes 01_facts.json
  noop      prints nothing (no JSON)
  crash     exits 3 with no output
  wrongmodel  good flow, but reports only a cheap model in modelUsage
  dead_hooks  self-test does not run the hooks (as if a CLI update dropped them)
"""
import json
import os
import subprocess
import sys

MODEL = "claude-opus-5-5"


def argval(name):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else None


def hook_cmd(settings, event):
    s = json.load(open(settings, encoding="utf-8"))
    return s["hooks"][event][0]["hooks"][0]["command"]


def fire(settings, event, payload):
    return subprocess.run(hook_cmd(settings, event), shell=True, input=json.dumps(payload), capture_output=True, text=True,
                          env=os.environ)


def tool(*args):
    run = os.environ["VANI_RUN"]
    t = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))
    r = subprocess.run([sys.executable, os.path.join(t["skill"], "scripts", "persona_tool.py")] + list(args),
                       capture_output=True, text=True, encoding="utf-8", env=os.environ)
    if r.returncode:
        sys.stderr.write(f"tool {args[:2]} failed: {r.stdout}{r.stderr}\n")
    return r


def good_flow(run):
    prior = json.load(open(os.path.join(run, "03_prior.json"), encoding="utf-8"))
    facts = json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))
    sys.path.insert(0, os.path.join(json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))["skill"], "scripts"))
    import persona_tool as PT
    h = PT.load_hierarchy()
    chosen = (["P0"] if prior["persona"].get("holdout") else prior["persona"]["top2"])[0]
    tool("select", "--persona", chosen, "--reason", "stub")
    card = PT.card_of(chosen) or {}
    defaults = {"voice_gender": "F", "language_start": "HINDI", "empathy": "acknowledge earlier calls"}
    for f in PT.decide_fields(h):
        out = tool("probe", "--field", f, "--json").stdout.strip().splitlines()
        hits = json.loads(out[-1])["hits"][:3] if out else []
        spec = h["fields"][f]
        v = PT.start_value(f, card, prior)
        if v is None and isinstance(spec.get("value_groups"), list):
            v = spec["value_groups"][0]
        args = ["decide", "--field", f, "--value", str(v), "--type", "start_persona", "--reason", "stub card value",
                "--searched", "stub: hits read, none applies"]
        for x in hits:
            args.append(f"--answer={x['id']}=stub: not evidence for this field")
        tool(*args)
    for hid in facts.get("eligible_hooks", []):
        if hid in (h.get("hooks") or {}):
            tool("probe", "--hook", hid)
        tool("hook", "--id", hid, "--decision", "rejected", "--reason", "stub")
    text = {"personalisation": [], "hook": {"id": None, "claim": "", "fact_ids": [], "backup": None},
            "opening": "Namaste ji, main IndiaMART se baat kar rahi hoon. Do minute milenge?",
            "identity_line": "Main IndiaMART se baat kar rahi hoon, aapke profile ke liye call kiya hai.",
            "call_plan": [{"step": 1, "goal": "ask", "say": "Kya kal milna theek rahega ji?", "basis": {"type": "persona", "ref": "words_per_turn"}}],
            "objection_playbook": [{"objection": "busy", "response": "Ji, kab call karun?", "basis": {"type": "division", "ref": "O1"}}],
            "escalation_rules": ["opt-out: end"], "guardrails": ["never volunteer AI"], "verified_facts": [],
            "switch_sensitivity": {"rushed": "high"},
            "guards_ack": [{"guard": g, "action": "stub", "cites": []} for g in facts.get("true_guards", [])],
            "new_persona_suggestion": None, "overall_confidence": 0.3, "completeness": 0.8}
    p = os.path.join(run, "draft_text.json")
    json.dump(text, open(p, "w", encoding="utf-8"))
    tool("text", "--file", p)
    return tool("finalize")


def main():
    if "--version" in sys.argv:
        print("2.1.292 (Claude Code)")
        return 0
    run, settings, model = os.environ["VANI_RUN"], argval("--settings"), argval("--model")
    mode = os.environ.get("STUB_MODE", "good")
    turn = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))
    if turn.get("selftest"):
        if mode != "dead_hooks":
            fire(settings, "PreToolUse", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(run, "04_persona.json"), "content": "{}"}})
            fire(settings, "Stop", {"stop_hook_active": False})
        print(json.dumps({"num_turns": 2, "result": "DONE", "modelUsage": {model: {}}}))
        return 0
    if mode == "noop":
        return 0
    if mode == "hang":
        import time
        time.sleep(120)
        return 0
    if mode == "editskill":
        with open(os.path.join(turn["skill"], "scripts", "validate_persona.py"), "a", encoding="utf-8") as f:
            f.write("\n# weakened\n")
    if mode == "sellerchange":
        with open(os.path.join(turn["folder"], "core.md"), "a", encoding="utf-8") as f:
            f.write("\nextra\n")
    if mode in ("dnc", "dnc_persona"):
        json.dump({"status": "do_not_call"}, open(os.path.join(run, "status.json"), "w"))
        if mode == "dnc_persona":
            json.dump({"dimensions": {}}, open(os.path.join(run, "04_persona.json"), "w"))
        print(json.dumps({"num_turns": 2, "result": "do_not_call", "modelUsage": {model: {}}}))
        return 0
    if mode == "crash":
        return 3
    if mode == "forged":
        import hashlib
        p04, p02 = os.path.join(run, "04_persona.json"), os.path.join(run, "02_review.json")
        json.dump({"dimensions": {}, "opening": "x"}, open(p04, "w"))
        json.dump({"hooks": []}, open(p02, "w"))
        h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        with open(os.path.join(run, "ledger.jsonl"), "a") as f:
            f.write(json.dumps({"kind": "finalize", "sha04": h(p04), "sha02": h(p02)}) + "\n")
    elif mode == "bypass":
        subprocess.run([sys.executable, "-c", "import json,sys; json.dump({'dimensions': {}}, open(sys.argv[1], 'w')); "
                        "json.dump({'hooks': []}, open(sys.argv[2], 'w'))", os.path.join(run, "04_persona.json"),
                        os.path.join(run, "02_review.json")])
    else:
        r = good_flow(run)
        if r.returncode:
            sys.stderr.write("good flow failed: " + r.stdout + r.stderr)
        if mode == "edit":
            p = os.path.join(run, "04_persona.json")
            d = json.load(open(p, encoding="utf-8"))
            d["opening"] = "Namaste ji, edited after finalize."
            json.dump(d, open(p, "w", encoding="utf-8"))
        if mode == "tamper":
            p = os.path.join(run, "01_facts.json")
            d = json.load(open(p, encoding="utf-8"))
            d["true_guards"] = []
            d["tampered"] = True
            json.dump(d, open(p, "w", encoding="utf-8"))
    fire(settings, "Stop", {"stop_hook_active": False})
    used = {"claude-haiku-4-5-20251001": {}} if mode == "wrongmodel" else {model: {}}
    print(json.dumps({"num_turns": 12, "result": "done", "modelUsage": used, "total_cost_usd": 0}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
