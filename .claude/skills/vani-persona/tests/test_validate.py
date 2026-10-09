"""T3: validate_persona.py must refuse each bad case and stay quiet on the good one (both directions)."""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_persona as V  # noqa: E402

FILES = {
    "INDEX.md": "# Seller X: INDEX\n- **K1** Division: NSD\n",
    "core.md": "### A07 Gender / salutation\nFemale\n### H02 Account managers\nNSD Top Cities\n",
    "buyleads.md": "### E05 BL credits and lapsed credits\n13 credits lapsed, balance 2\n### E10 AOV\nmedian Rs 15,500\n",
    "candidate_leads.md": "| CL | live | 36 inch Ladies Bra | 200 Piece | Rs. 10,000 - 11,000 | Surat, Gujarat |\nCL-1\n",
    "catalogue.md": "### D06 Catalogue quality\ncqs 30, 5 products without photo\n",
    "calls/C01_2026-10-01.md": "# call C01\n- Summary: seller said he is busy, call later\n  - C01.T3 seller: abhi busy hoon baad mein call karo\n",
}
FACTS = {"division": "NSD", "true_guards": ["guard.call_fatigue"], "eligible_hooks": ["hook.money_lead", "hook.profile_gap"],
         "hooks": [{"id": "hook.money_lead", "A_script": {"probe_files": ["candidate_leads.md", "buyleads.md"]}},
                   {"id": "hook.profile_gap", "A_script": {"probe_files": ["catalogue.md"]}}]}
CTX = {"points": {"G00": {"value": {"calls": [{"days_ago": 9}]}}}}


def c(i, q):
    return {"id": i, "quote": q}


GOOD_REVIEW = {"hooks": [
    {"id": "hook.money_lead", "B_agent": {"decision": "primary", "reason": "a live 200-piece lead in her city matches her AOV",
        "probe": {"cites": [c("candidate_leads.md#CL-1", "200 Piece"), c("buyleads.md#E10", "median Rs 15,500"),
                            c("calls/C01#C01.T3", "abhi busy hoon")]},
        "counter_evidence": {"text": "she was busy last time", "cites": [c("calls/C01#C01.T3", "baad mein call karo")]}}},
    {"id": "hook.profile_gap", "B_agent": {"decision": "backup", "reason": "photos missing",
        "probe": {"cites": [c("catalogue.md#D06", "5 products without photo")]}}}]}
DIM = lambda v, ev="WEAK": {"value": v, "reason": "fits her facts", "cites": [], "confidence": 0.5, "evidence": ev}
GOOD_PERSONA = {
    "decision_id": "d1", "division": "NSD", "prior": {"top2": ["P2", "P4"], "chosen": "P4", "override": False},
    "dimensions": {"voice_gender": {**DIM("F"), "cites": [c("core.md#A07", "Female")]}, "voice_id": DIM("uuid"), "pace": DIM(1.1, "MODERATE"),
                   "pitch": DIM(0.0, "GUESS"), "language_start": DIM("GUJARATI"), "code_mix": DIM("light_hinglish"), "accent": DIM("gu-IN", "GUESS"),
                   "formality": DIM("medium", "GUESS"), "warmth": DIM("high"), "empathy": DIM("acknowledge earlier calls"),
                   "sophistication": DIM("practical", "GUESS"), "words_per_turn": DIM(10, "MODERATE")},
    "personalisation": [{"what": "her product and city", "cites": [c("candidate_leads.md#CL-1", "Surat, Gujarat")]}],
    "hook": {"id": "hook.money_lead", "claim": "Kal Surat se 200 piece ka order aaya, lagbhag 10,000 ka", "fact_ids": ["candidate_leads.md#CL-1"], "backup": "hook.profile_gap"},
    "opening": "Namaste ji, main IndiaMART se baat kar rahi hoon. Do minute milenge?",
    "identity_line": "Main IndiaMART se baat kar rahi hoon, aapke profile ko correct karne ke liye call kiya hai.",
    "call_plan": [{"step": 1, "goal": "hook", "say": "Surat se 200 piece ka order aaya hai ji."}],
    "objection_playbook": [{"objection": "phone par bata do", "response": "Ji, 30 minute ki meeting mein executive dikha denge.", "fact_ids": []}],
    "escalation_rules": ["opt-out: end"], "guardrails": ["never volunteer AI"],
    "verified_facts": [{"id": "candidate_leads.md#CL-1", "say": "200 piece, Rs 10,000 - 11,000, Surat"}],
    "switch_sensitivity": {"rushed": "high"}, "guards_ack": [{"guard": "guard.call_fatigue", "action": "short call, acknowledge earlier calls", "cites": []}],
    "amendments": [{"dimension": "pace", "from": 1.0, "to": 1.1, "menu_item": "pace_up", "reason": "busy last time",
                    "cites": [c("calls/C01#C01.T3", "abhi busy hoon")]}],
    "new_persona_suggestion": None, "overall_confidence": 0.5, "completeness": 0.8}
READS = ["candidate_leads.md", "buyleads.md", "catalogue.md", "calls/C01_2026-10-01.md", "INDEX.md", "core.md"]


def make(tmp, persona=None, review=None, reads=None, facts=None):
    folder, run = tmp / "seller", tmp / "run"
    for name, text in FILES.items():
        p = folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (folder / "facts.json").write_text(json.dumps(facts or FACTS), encoding="utf-8")
    (folder / "context.json").write_text(json.dumps(CTX), encoding="utf-8")
    run.mkdir(exist_ok=True)
    if persona is not False:
        (run / "04_persona.json").write_text(json.dumps(persona or GOOD_PERSONA), encoding="utf-8")
    (run / "02_review.json").write_text(json.dumps(review or GOOD_REVIEW), encoding="utf-8")
    (run / "read_log.jsonl").write_text("\n".join(json.dumps({"path": str(folder / r)}) for r in (reads if reads is not None else READS)), encoding="utf-8")
    return V.validate(str(folder), str(run))


def bad(tmp, mutate, expect, **kw):
    p, r = copy.deepcopy(GOOD_PERSONA), copy.deepcopy(GOOD_REVIEW)
    mutate(p, r)
    fails = make(tmp, p, r, **kw)
    assert any(expect in f for f in fails), fails


def test_good_passes(tmp_path):
    assert make(tmp_path) == []


def test_missing_field(tmp_path):
    bad(tmp_path, lambda p, r: p.pop("escalation_rules"), "missing field 'escalation_rules'")


def test_fake_cite(tmp_path):
    bad(tmp_path, lambda p, r: r["hooks"][0]["B_agent"]["probe"]["cites"].append(c("enquiries.md#E01", "x")), "does not exist")


def test_wrong_quote(tmp_path):
    bad(tmp_path, lambda p, r: r["hooks"][0]["B_agent"]["probe"]["cites"].__setitem__(0, c("candidate_leads.md#CL-1", "500 tonnes")), "quote not found")


def test_unread_probe(tmp_path):
    bad(tmp_path, lambda p, r: None, "was not read", reads=["INDEX.md", "core.md", "catalogue.md"])


def test_primary_needs_calls_cite(tmp_path):
    def m(p, r):
        r["hooks"][0]["B_agent"]["probe"]["cites"] = [c("candidate_leads.md#CL-1", "200 Piece"), c("buyleads.md#E10", "median Rs 15,500"),
                                                      c("buyleads.md#E05", "13 credits lapsed")]
    bad(tmp_path, m, "cite from calls/")


def test_no_counter_evidence(tmp_path):
    bad(tmp_path, lambda p, r: r["hooks"][0]["B_agent"].pop("counter_evidence"), "counter_evidence")


def test_guard_not_acked(tmp_path):
    bad(tmp_path, lambda p, r: p.__setitem__("guards_ack", []), "guard.call_fatigue is not acknowledged")


def test_banned_word(tmp_path):
    bad(tmp_path, lambda p, r: p.__setitem__("opening", "Namaste, main IndiaMART ki AI assistant hoon"), "banned word")


def test_branch_manager(tmp_path):
    bad(tmp_path, lambda p, r: p.__setitem__("opening", "Main branch manager bol rahi hoon"), "banned word")


def test_gender_agreement(tmp_path):
    bad(tmp_path, lambda p, r: p.__setitem__("opening", "Namaste ji, main IndiaMART se baat kar raha hoon"), "masculine")


def test_unverified_number(tmp_path):
    bad(tmp_path, lambda p, r: p["call_plan"].append({"step": 2, "goal": "x", "say": "Aapke competitor ne 5000 leads liye"}), "not in verified_facts")


def test_money_first(tmp_path):
    def m(p, r):
        p["hook"] = {"id": "hook.profile_gap", "claim": "photos missing", "fact_ids": [], "backup": None}
        p["verified_facts"] = []
        p["call_plan"] = [{"step": 1, "goal": "hook", "say": "Photos missing hain ji"}]
        p["objection_playbook"] = [{"objection": "x", "response": "Ji samjha"}]
    bad(tmp_path, m, "money_lead is eligible")


def test_amendment_menu(tmp_path):
    bad(tmp_path, lambda p, r: p["amendments"][0].__setitem__("menu_item", "vibes"), "not in the fixed menu")


def test_confidence_above_completeness(tmp_path):
    bad(tmp_path, lambda p, r: p["dimensions"]["pace"].__setitem__("confidence", 0.95), "> completeness")


def test_pace_range(tmp_path):
    bad(tmp_path, lambda p, r: p["dimensions"]["pace"].__setitem__("value", 1.6), "outside 0.85-1.25")


def test_dnc_blocks_persona(tmp_path):
    f = dict(FACTS, true_guards=["guard.do_not_call"])
    fails = make(tmp_path, facts=f)
    assert any("do_not_call" in x for x in fails)
    t2 = tmp_path / "second"
    t2.mkdir()
    assert make(t2, persona=False, facts=f) == []


def test_identity_line_names_indiamart(tmp_path):
    bad(tmp_path, lambda p, r: p.__setitem__("identity_line", "Main aapke profile ke liye call kar rahi hoon"), "must name IndiaMART")


def test_compile_refuses_unvalidated_and_fills(tmp_path):
    import compile_vars as C
    make(tmp_path)
    run = tmp_path / "run"
    (run / "validation.json").write_text(json.dumps({"pass": False}), encoding="utf-8")
    try:
        C.compile_vars(str(run))
        assert False, "should refuse"
    except SystemExit as e:
        assert "REFUSED" in str(e)
    (run / "validation.json").write_text(json.dumps({"pass": True}), encoding="utf-8")
    p = json.loads((run / "04_persona.json").read_text(encoding="utf-8"))
    p["opening"] = "Namaste {SELLER_NAME} ji, main IndiaMART se baat kar rahi hoon."
    (run / "04_persona.json").write_text(json.dumps(p), encoding="utf-8")
    out = C.compile_vars(str(run), {"{SELLER_NAME}": "Ravi", "{COMPANY}": "X"}, "Surat")
    assert out["persona_opening"].startswith("Namaste Ravi ji") and out["persona_language"] == "GUJARATI"
    assert out["persona_voice_gender"] == "F" and "feminine" in out["prompt_style"] and "Gujarati" in out["prompt_style"]
    assert "Surat se 200 piece" in out["prompt_phases"] and "200 piece, Rs 10,000 - 11,000, Surat" in out["prompt_facts"]
    assert "Kal Surat se 200 piece" in out["prompt_objective"]  # the hook drives the objective
    assert "@" not in out["prompt_persona"] + out["prompt_phases"]  # nested refs resolved before sending
    text = (run / "06_sarvam_prompt.md").read_text(encoding="utf-8")
    for head in ("# Persona", "# Environment & Situation", "# Objective", "# Speaking Style", "# Facts",
                 "# Conversation Guidelines", "# Guardrails", "# Date resolution"):
        assert head in text
    assert "@prompt_" not in text and "@identity_line" not in text
