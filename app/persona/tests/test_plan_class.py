"""X07: plan class. custtype.paid = -1 is PAID, everything else is FREE. Synthetic data only."""
import os

import seller_context_builder as B

GLID = "999000444"


def run(monkeypatch, tmp_path, rows):
    monkeypatch.setattr(B, "AOV_CACHE", str(tmp_path))
    seen = {}

    def fake(sql, ds, timeout=120):
        seen.update(sql=sql, ds=ds)
        return rows
    monkeypatch.setattr(B, "redash", fake)
    return B.plan_class(GLID, refresh=True), seen


def test_minus_one_is_paid_rest_free(monkeypatch, tmp_path):
    out, seen = run(monkeypatch, tmp_path, [{"paid": -1.0, "custtype": "CATALOG"}])
    assert out == {"status": "ok", "plan": "paid", "custtype": "CATALOG"} and seen["ds"] == 21 and "c.paid" in seen["sql"]
    assert run(monkeypatch, tmp_path, [{"paid": 0.0, "custtype": "FCP"}])[0]["plan"] == "free"
    assert run(monkeypatch, tmp_path, [{"paid": None, "custtype": None}])[0]["plan"] == "free"      # only two classes
    assert run(monkeypatch, tmp_path, [{"paid": "-1", "custtype": "BL Paid VgFCP"}])[0]["plan"] == "paid"


def test_missing_and_failure(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path, [])[0] == {"status": "no_plan"}
    os.remove(os.path.join(str(tmp_path), "plan_class", f"{GLID}.json"))       # the no_plan answer above was cached
    out, _ = run(monkeypatch, tmp_path, None)
    assert out is None and not os.path.exists(os.path.join(str(tmp_path), "plan_class", f"{GLID}.json"))


def test_cross_check_with_division():
    paid, free = {"status": "ok", "plan": "paid"}, {"status": "ok", "plan": "free"}
    assert "consistent" in B.plan_check(free, "NSD") and "consistent" in B.plan_check(paid, "CSD")
    assert "consistent" in B.plan_check(paid, "KCD") and "consistent" in B.plan_check(paid, "TMW")
    assert "MISMATCH" in B.plan_check(paid, "NSD") and "MISMATCH" in B.plan_check(free, "CSD")
    assert "division not available" in B.plan_check(paid, None) and B.plan_check(None, "NSD") == "plan class not available"


def test_rendered_in_core():
    o = {"seller_flags": {}, "onboarding_locations": [], "leap_calls": [], "kyc_documents": [], "kyc_sessions": [], "kyc_field_checks": []}
    md = B.render_kyc(o, None, None, {"status": "ok", "plan": "free", "custtype": "FCP"}, "NSD")
    assert "### X07 Seller plan class (free or paid)" in md and "plan class: free (customer type FCP)" in md and "consistent" in md
    assert "_not available_" in B.render_kyc(o, None, None, None, None)
