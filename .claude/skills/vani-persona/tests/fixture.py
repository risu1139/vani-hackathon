"""A small synthetic seller + run dir + hierarchy for the enforcement tests (no real seller data)."""
import datetime
import json
import os

TODAY = datetime.date.today()
CALL_DAY = (TODAY - datetime.timedelta(days=9)).isoformat()

HIERARCHY = {
    "version": "test", "reason_types": {"order": ["seller_evidence", "hierarchy", "start_persona"]},
    "fields": {
        "pace": {"probe_files": ["calls/", "core.md#B03"], "search_terms": ["busy hoon", "re:baad me (call|baat)"],
                 "value_groups": ["0.85-0.95", "0.95-1.05", "1.05-1.25"], "hard_range": [0.85, 1.25], "reason_required": True,
                 "evidence_rule": "a call turn where the seller was rushed"},
        "formality": {"probe_files": ["core.md#A04"], "search_terms": ["proprietor", "director"],
                      "value_groups": ["low", "medium", "high"], "reason_required": True},
        "voice_gender": {"probe_files": ["core.md#A07"], "search_terms": ["female", "male"], "value_groups": ["F", "M"],
                         "reason_required": True},
        "language_start": {"probe_files": ["core.md#B01"], "search_terms": ["telangana"], "value_groups": "any Sarvam language",
                           "hard_range": "compile_vars list", "reason_required": True},
        "voice_id": {"probe_files": [], "reason_required": False},
        "hook": {"probe_files": "see hooks", "reason_required": True},
        "opening": {"probe_files": ["calls/"], "search_terms": [], "reason_required": True},
    },
    "hooks": {"hook.profile_gap": {"probe_files": ["catalogue.md#D06"], "search_terms": ["without photo"]}},
}

FILES = {
    "INDEX.md": "# Seller: INDEX\n- **K1** Division: NSD\n",
    "core.md": ("# core\n### A04 Contact designation\nProprietor\n### A07 Gender / salutation\nFemale\n"
                "### B01 City, district, state\nHyderabad, Telangana\n### B03 Languages spoken on real calls\nTelugu, Hindi\n"
                "### I01 Complaints\nnone\n"),
    "catalogue.md": "# catalogue\n### D06 Catalogue quality\ncqs 30, 5 products without photo\n",
    f"calls/C01_{CALL_DAY}.md": ("# call C01\n### a call\n- Summary: seller was busy\n"
                                 "  - C01.T1 bot: Namaste ji\n  - C01.T2 seller: abhi busy hoon baad me call karo\n"),
}
FACTS = {"division": "NSD", "true_guards": [], "eligible_hooks": ["hook.profile_gap"], "hooks": [], "traits": [], "states": [],
         "start_rules": {"voice_gender": {"value": "F", "rule": "seller is female"},
                         "language_start": {"value": "TELUGU", "rule": "regional language (te)"}, "empathy_add": []}}
PRIOR = {"decision_id": "t1", "persona": {"top2": ["P2", "P4"], "holdout": False, "path": {}}, "brief": {},
         "voice": {"chosen": "F"}}
TEXT = {"personalisation": [], "hook": {"id": None, "claim": "", "fact_ids": [], "backup": None},
        "opening": "Namaste {SELLER_NAME}, main {AGENT_NAME}, IndiaMART se baat kar rahi hoon. Do minute milenge?",
        "identity_line": "Main {AGENT_NAME}, IndiaMART se baat kar rahi hoon, aapke profile ke liye call kiya hai.",
        "call_plan": [{"step": 1, "goal": "ask", "say": "Kya kal milna theek rahega?", "basis": {"type": "persona", "ref": "pace"}, "kind": "ask", "fact_ids": []}],
        "objection_playbook": [{"objection": "busy", "response": "Theek hai, kab call karun?", "basis": {"type": "division", "ref": "O1"}}],
        "escalation_rules": ["opt-out: end"], "guardrails": ["never volunteer AI"], "verified_facts": [],
        "switch_sensitivity": {"rushed": "high"}, "guards_ack": [], "new_persona_suggestion": None,
        "overall_confidence": 0.5, "completeness": 0.8}


def make(tmp, facts=None, prior=None):
    """tmp/run with seller/, 01_facts.json, 03_prior.json, turn.json; tmp/hierarchy.json. Returns (run, hierarchy path)."""
    run = tmp / "run"
    seller = run / "seller"
    for name, text in FILES.items():
        p = seller / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (run / "01_facts.json").write_text(json.dumps(facts or FACTS), encoding="utf-8")
    (run / "03_prior.json").write_text(json.dumps(prior or PRIOR), encoding="utf-8")
    (run / "turn.json").write_text(json.dumps({"decision_id": "t1", "folder": str(seller), "run": str(run),
                                               "as_of": TODAY.isoformat()}), encoding="utf-8")
    hp = tmp / "hierarchy.json"
    hp.write_text(json.dumps(HIERARCHY), encoding="utf-8")
    (seller / "context.json").write_text(json.dumps({"points": {}}), encoding="utf-8")
    return run, hp
