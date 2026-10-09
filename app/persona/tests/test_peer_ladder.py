"""M15: peer ladder rules. Synthetic data only."""
import seller_context_builder as B

GLID = "999000111"


def raw(rows, own=None, pov_by=None, band="40 L - 1.5 Cr"):
    return {"status": "ok", "window_days": 30, "main_mcat": "555", "band": band,
            "me": {"c": 1, "s": 10, "b": band}, "near": ["0 - 40 L", "40 L - 1.5 Cr", "1.5 - 5 Cr"],
            "own": own if own is not None else [{"m": 555, "n_win": 3, "n90": 12}, {"m": 777, "n_win": 1, "n90": 4}],
            "rows": rows, "pov_by": pov_by or {}}


def peer(g, b="40 L - 1.5 Cr", c=1, s=10, n=2):
    return {"g": g, "b": b, "c": c, "s": s, "n_any": n, "n_mcat": n}


def test_band_pm1_rungs_never_allowed():
    # only 2 same-band buyers, but 20 bigger-band buyers: rungs 4-5 have plenty and must still be refused
    rows = [peer(i) for i in range(2)] + [peer(100 + i, b="1.5 - 5 Cr", n=9) for i in range(20)]
    p = B.peer_ladder(raw(rows), GLID)
    by = {r["rung"]: r for r in p["rungs"]}
    assert by["4"]["peers_bought_in_mcat"] >= 5 and by["5"]["peers_bought_in_mcat"] >= 5
    assert not by["4"]["allowed"] and not by["5"]["allowed"]
    assert "band ±1" in by["4"]["why_not_allowed"]
    assert p["first_allowed_rung"] is None
    assert all(not r["allowed"] for r in p["rungs"] if r["band_scope"] != "same band")


def test_same_band_rung_allowed_and_first():
    rows = [peer(i, c=2) for i in range(6)]  # same band, other city, same state
    p = B.peer_ladder(raw(rows), GLID)
    by = {r["rung"]: r for r in p["rungs"]}
    assert not by["1"]["allowed"] and by["2"]["allowed"]
    assert p["first_allowed_rung"] == "2"


def test_seller_count_uses_peer_window():
    p = B.peer_ladder(raw([peer(i) for i in range(6)]), GLID)
    s = p["seller_leads_bought"]
    assert s["window_days"] == p["window_days"] == 30
    assert s["main_mcat"] == 3 and s["any_mcat"] == 4  # the 30-day counts, not the 90-day ones (12 / 16)


def test_aov_variant_filters_peers():
    rows = [peer(i) for i in range(10)]
    pov = {str(i): [1000.0] for i in range(6)}            # 6 peers near the seller's AOV
    pov.update({str(i): [100000.0] for i in range(6, 10)})  # 4 peers far above it
    stats = {"median_rs": 1200, "n_valued": 15}
    p = B.peer_ladder(raw(rows, pov_by=pov), GLID, stats)
    by = {r["rung"]: r for r in p["rungs"]}
    assert by["1a"]["peers_bought_in_mcat"] == 6 and by["1a"]["allowed"]
    assert by["1"]["peers_bought_in_mcat"] == 10
    assert by["1a"]["aov_filter"] and "0.5–2x" in by["1a"]["aov_filter"]
    assert p["first_allowed_rung"] == "1a"
    assert p["aov_filter"]["seller_aov_rs"] == 1200


def test_no_aov_variant_without_enough_seller_values():
    p = B.peer_ladder(raw([peer(i) for i in range(6)]), GLID, {"median_rs": 1200, "n_valued": 3})
    assert not any(r["rung"].endswith("a") for r in p["rungs"])
    assert "not applied" in p["aov_filter"]["status"]


def test_aov_from_own_valued_leads_when_e10_missing():
    pov = {GLID: [2000.0] * 12}
    p = B.peer_ladder(raw([peer(i) for i in range(6)], pov_by=pov), GLID, None)
    assert p["aov_filter"]["seller_aov_rs"] == 2000
    assert any(r["rung"] == "1a" for r in p["rungs"])


def test_key_fact_and_render_text():
    p = B.peer_ladder(raw([peer(i) for i in range(6)]), GLID)
    K = B.key_facts({}, {"calls": []}, p, [], None, {}, [])
    line = next(t for _, t, c in K if c == "peers.md#E11")
    assert "same turnover band" in line and "same 30 d" in line and "context only" in line
    assert "90" not in line
    md = B.render_peer(p)
    assert "never allowed for a claim" in md and "no: band ±1" in md


def test_key_fact_without_allowed_rung():
    rows = [peer(100 + i, b="1.5 - 5 Cr") for i in range(20)]
    p = B.peer_ladder(raw(rows), GLID)
    K = B.key_facts({}, {"calls": []}, p, [], None, {}, [])
    line = next(t for _, t, c in K if c == "peers.md#E11")
    assert line.startswith("Peers: no same-band rung")
