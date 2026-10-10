"""X06: GST registered location. The GSTIN must never reach the folder; only the state name does. Synthetic data only."""
import json
import os

import seller_context_builder as B

GLID = "999000222"


def run(monkeypatch, tmp_path, rows):
    monkeypatch.setattr(B, "AOV_CACHE", str(tmp_path))
    seen = {}

    def fake(sql, ds, timeout=120):
        seen["sql"] = sql
        return rows
    monkeypatch.setattr(B, "redash", fake)
    return B.gst_location(GLID, refresh=True), seen


def test_state_from_code(monkeypatch, tmp_path):
    out, seen = run(monkeypatch, tmp_path, [{"code": "36"}])
    assert out == {"status": "ok", "state": "Telangana"}
    assert "left(glusr_gst_no, 2)" in seen["sql"]
    assert "select glusr_gst_no" not in seen["sql"].lower()  # the full GSTIN is never selected


def test_no_gst_and_unknown_code(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path, [])[0]["status"] == "no_gst"
    assert run(monkeypatch, tmp_path, [{"code": None}])[0]["status"] == "no_gst"
    assert run(monkeypatch, tmp_path, [{"code": "55"}])[0]["status"] == "unknown_code"


def test_failure_not_cached(monkeypatch, tmp_path):
    out, _ = run(monkeypatch, tmp_path, None)
    assert out is None
    assert not os.path.exists(os.path.join(str(tmp_path), "gst_state", f"{GLID}.json"))


def test_rendered_in_core_without_gstin():
    o = {"seller_flags": {}, "onboarding_locations": [], "leap_calls": [], "kyc_documents": [], "kyc_sessions": [], "kyc_field_checks": []}
    md = B.render_kyc(o, None, {"status": "ok", "state": "Gujarat"})
    assert "### X06 GST registered location (state only)" in md and "GST registration state: Gujarat" in md
    assert "not available" in B.render_kyc(o, None, None)


def test_code_table_is_json_safe():
    json.dumps(B.GST_STATE_CODES)
    assert B.GST_STATE_CODES["24"] == "Gujarat" and B.GST_STATE_CODES["36"] == "Telangana"
