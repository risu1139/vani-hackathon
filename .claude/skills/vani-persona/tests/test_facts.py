"""Fixtures for facts.py (T1). Each test builds a synthetic context.json and checks one fact, guard or hook.
Run: python -m pytest .claude/skills/vani-persona/tests -q"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import facts  # noqa: E402

TODAY = date(2026, 10, 10)


def ctx(points=None, calls=None):
    base = {
        "H02": {"vertical_name": "NSD Top Cities - Channel FSF"},
        "C02": {"annual_turnover": "0 - 40 L"},
        "C05": {"paid_free": "Free", "byr_custtype": "FREELIST"},
        "C04": {"member_since": "20200101000000"},
        "C03": {"nature_of_business": "Manufacturer"},
        "B01": {"seller_state": "Gujarat"},
        "D06": {"scorecard": {"cqs": 60, "prd_no_prices": 0, "prod_wo_image": 0}, "filtercount": {"PRODUCT_COUNT": 20}},
        "E05": {}, "E01": {"topbar": {"enq_lm": 30, "enq_lq": 90}}, "I01": {"cmplnts_cnt": 0, "closed_cmplnts": 0},
        "H01": {}, "E10": {"seller": {}, "mcats": {}}, "E11": {}, "E12": [],
        "G00": {"calls": calls or [], "outcome_counts_all_history": {}}, "X00": {"seller_flags": {}}, "X05": {},
    }
    base.update(points or {})
    return {"glid": "T", "points": {k: {"value": v} for k, v in base.items()}}


def run(points=None, calls=None):
    out = facts.build(ctx(points, calls), TODAY)
    val = {x["id"]: x["A_script"]["value"] for x in out["traits"] + out["states"]}
    return out, val


def call(days, outcome="General (talked)", summary="", signals=None, transcript=None):
    return {"date": "2026-10-01", "days_ago": days, "outcome": outcome, "summary": summary,
            "signals": signals or {}, "transcript": transcript or [], "exec_contact": None}


def hooks(out):
    return set(out["eligible_hooks"])


def test_division_nsd_and_reference():
    out, v = run()
    assert v["trait.division"] == "NSD"
    assert out["traits"][0]["A_script"]["detail"]["reference"] == "division_nsd.md"


def test_tmw_uses_csd_hooks():
    out, v = run({"H02": {"vertical_name": "Tele-Monthly Welcome [TMW]"}, "E05": {"bl_credits_alctd": 15, "bl_credit_lapsed": 5, "current_balance": 3}})
    assert v["trait.division"] == "TMW"
    assert "hook.unused_credits" in hooks(out)


def test_bl_usage_lapsed():
    _, v = run({"E05": {"bl_credits_alctd": 15, "bl_credit_lapsed": 13, "current_balance": 2, "last_cons_date": "2026-10-08"}})
    assert v["state.bl_usage"] == "lapsed"


def test_bl_usage_unused():
    _, v = run({"E05": {"bl_credits_alctd": 10, "bl_credit_lapsed": 0, "current_balance": 10, "last_cons_date": "2026-08-01"}})
    assert v["state.bl_usage"] == "unused"


def test_bl_usage_none():
    _, v = run()
    assert v["state.bl_usage"] == "none"


def test_scale_small_and_aov_bump():
    _, v = run({"E10": {"seller": {"stats": {"median_rs": 50000}}, "mcats": {"1": {"stats": {"median_rs": 10000, "p75_rs": 30000}}}}})
    assert v["trait.business_scale"] == "mid"  # small, bumped one step because seller AOV > 2x category


def test_high_value_by_turnover():
    _, v = run({"C02": {"annual_turnover": "5 - 25 Cr"}})
    assert v["trait.high_value"] is True and v["trait.business_scale"] == "large"


def test_profile_weak():
    out, v = run({"D06": {"scorecard": {"cqs": 30, "prd_no_prices": 5, "prod_wo_image": 2}, "filtercount": {"PRODUCT_COUNT": 20}}})
    assert v["trait.im_profile_strength"] == "weak"
    assert "hook.profile_gap" in hooks(out)


def test_enquiry_falling():
    out, v = run({"E01": {"topbar": {"enq_lm": 5, "enq_lq": 90}}})
    assert v["state.enquiry_flow"] == "falling" and "hook.enquiry_drop" in hooks(out)


def test_call_fatigue_guard():
    out, v = run(calls=[call(1), call(3), call(6)])
    assert v["state.call_fatigue"]["vani_calls_7d"] == 3
    assert "guard.call_fatigue" in out["true_guards"]


def test_asked_stop_calling_guard():
    out, _ = run(calls=[call(5, summary="The lead asked to update their system to stop further calls.")])
    assert "guard.asked_stop_calling" in out["true_guards"]


def test_dnc_guard():
    out, _ = run({"X00": {"seller_flags": {"do_not_call_requested": 1.0}}})
    assert "guard.do_not_call" in out["true_guards"]


def test_exec_met_recently_guard():
    out, _ = run({"H01": {"exec_calls": 2, "last": "2026-10-08 10:00:00"}})
    assert "guard.met_exec_recently" in out["true_guards"]


def test_open_grievance_blocks_unused_credits():
    out, v = run({"H02": {"vertical_name": "CSD"}, "E05": {"bl_credits_alctd": 15, "bl_credit_lapsed": 5, "current_balance": 3},
                  "I01": {"cmplnts_cnt": 2, "closed_cmplnts": 1}})
    assert v["state.open_grievance"] == "yes"
    assert "hook.unused_credits" not in hooks(out) and "hook.resolve_grievance" in hooks(out)


def test_money_lead_needs_value():
    out, _ = run({"E12": [{"product": "Bra", "quantity": "200", "unit": "Piece", "order_value_text": "Rs. 10,000 - 11,000", "buyer_city": "Surat"}]})
    assert "hook.money_lead" in hooks(out)
    out2, _ = run({"E12": [{"product": "Bra", "quantity": "200", "unit": "Piece", "order_value_text": None}]})
    assert "hook.money_lead" not in hooks(out2)


def test_peer_ahead():
    e11 = {"status": "ok", "window_days": 30, "seller_leads_bought": {"main_mcat": 10, "window_days": 30},
           "rungs": [{"rung": 3, "allowed": True, "median_leads_per_buyer": 2}]}
    out, v = run({"E11": e11})
    assert v["state.peer_position"]["seller_vs_peers"] == "ahead"
    assert "hook.peer_usage" in hooks(out)


def test_no_peer_rung():
    out, v = run({"E11": {"status": "ok", "rungs": [{"rung": 1, "allowed": False}]}})
    assert "hook.peer_usage" not in hooks(out)


def test_gender_recorded_and_guess_confidence():
    out, v = run({"A07": {"glusr_usr_gender": "Female"}})
    g = next(t for t in out["traits"] if t["id"] == "trait.seller_gender")
    assert v["trait.seller_gender"] == "F" and g["A_script"]["confidence"] == 1.0
    out2, _ = run({"A03": {"glusr_usr_firstname": "Priya"}})
    g2 = next(t for t in out2["traits"] if t["id"] == "trait.seller_gender")
    assert g2["A_script"]["confidence"] <= 0.4


def test_regional_language_from_state():
    _, v = run({"B01": {"seller_state": "Tamil Nadu"}})
    assert v["trait.language"]["regional"] == "ta"


def test_call_mood_decays():
    _, v = run(calls=[call(0, signals={"rushed": 1}), call(60, signals={"rushed": 1})])
    assert 1.2 < v["state.call_mood"]["rushed"] < 1.3  # 1 + 0.25


def test_rural_city_tier():
    _, v = run({"X05": {"status": "ok", "tier": "village_or_unclassified", "rural_proxy": True, "hindi_belt": True, "state": "Bihar"}})
    assert v["trait.city_tier"] == "village_or_unclassified"
