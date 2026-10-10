"""E08 competitors: plan flag (custtype.paid = -1 is paid) and no catalog_url. Synthetic data only."""
import json
import os

import export_for_agent as E
import seller_context_builder as B


def P_with(comps):
    return {"E08": ({"counts": {}, "competitors": {"competitors": comps}}, "x")}


def test_plan_flag_and_catalog_url_dropped(monkeypatch, tmp_path):
    monkeypatch.setattr(B, "AOV_CACHE", str(tmp_path))
    seen = {}

    def fake(sql, ds, timeout=120):
        seen.update(sql=sql, ds=ds)
        return [{"n": "CATALOG", "p": -1.0}, {"n": "STAR", "p": -1.0}, {"n": "FREELIST", "p": 0.0}, {"n": "FCP", "p": None}]
    monkeypatch.setattr(B, "redash", fake)
    P = P_with([{"competitor_company": "A", "custtype_name": "CATALOG", "catalog_url": "https://x/a-slug/"},
                {"competitor_company": "B", "custtype_name": "FREELIST", "catalog_url": "https://x/b-slug/"},
                {"competitor_company": "C", "custtype_name": "FCP"}, {"competitor_company": "D", "custtype_name": "UNKNOWN_TYPE"}])
    B.tidy_competitors(P, refresh=True)
    c = P["E08"][0]["competitors"]["competitors"]
    assert [x.get("plan") for x in c] == ["paid", "free", "free", None]
    assert all("catalog_url" not in x for x in c) and seen["ds"] == 21 and "custtype" in seen["sql"]


def test_no_competitors_is_fine(monkeypatch, tmp_path):
    monkeypatch.setattr(B, "AOV_CACHE", str(tmp_path))
    B.tidy_competitors({"E08": ({"counts": {}}, "x")})
    B.tidy_competitors({})


def test_export_strips_catalog_url_everywhere():
    ctx = {"points": {"E08": {"value": {"competitors": {"competitors": [{"competitor_company": "A", "catalog_url": "https://x/a-slug/", "plan": "paid"}]}}}}}
    out = E.strip_sources(ctx)
    assert "catalog_url" not in json.dumps(out) and out["points"]["E08"]["value"]["competitors"]["competitors"][0]["plan"] == "paid"
    md = '    - {"competitor_company": "A", "custtype_name": "STAR", "catalog_url": "https://x/a-slug/", "plan": "paid"}'
    assert "catalog_url" not in E.CATALOG_URL_TEXT.sub("", md) and "a-slug" not in E.CATALOG_URL_TEXT.sub("", md)
    last = '    - {"competitor_company": "A", "catalog_url": "https://x/a-slug/"}'
    assert E.CATALOG_URL_TEXT.sub("", last) == '    - {"competitor_company": "A"}'
