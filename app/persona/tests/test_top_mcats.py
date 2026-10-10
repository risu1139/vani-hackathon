"""D08: top MCATs by active products. Synthetic data only."""
import os

import seller_context_builder as B


def run(monkeypatch, tmp_path, rows):
    monkeypatch.setattr(B, "AOV_CACHE", str(tmp_path))
    seen = {}

    def fake(sql, ds, timeout=120):
        seen.update(sql=sql, ds=ds)
        return rows
    monkeypatch.setattr(B, "redash", fake)
    return B.top_mcats("999000333", refresh=True), seen


def test_rows_become_ints_in_order(monkeypatch, tmp_path):
    out, seen = run(monkeypatch, tmp_path, [{"mcat_id": 1707.0, "mcat_name": "Canopies", "active_products": 4},
                                            {"mcat_id": 1705.0, "mcat_name": "Awnings", "active_products": 3}])
    assert out["status"] == "ok" and out["mcats"][0] == {"mcat_id": 1707, "mcat_name": "Canopies", "active_products": 4}
    assert seen["ds"] == 21 and "pc_item_status_approval >= 10" in seen["sql"] and "LIMIT 5" in seen["sql"]
    assert "ORDER BY active_products DESC" in seen["sql"]


def test_failure_not_cached(monkeypatch, tmp_path):
    out, _ = run(monkeypatch, tmp_path, None)
    assert out is None and not os.path.exists(os.path.join(str(tmp_path), "top_mcats", "999000333.json"))


def test_render():
    md = B.render_top_mcats({"status": "ok", "mcats": [{"mcat_id": 1, "mcat_name": "Canopies", "active_products": 4}]})
    assert "### D08 Top MCATs by active products" in md and "1. Canopies (MCAT 1): 4 active products" in md
    assert "_not available_" in B.render_top_mcats(None)
