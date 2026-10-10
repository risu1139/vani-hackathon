"""T2: prior.py hierarchy, Thompson sampling, holdout and voice prior; loop2_update learning."""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import loop2_update as L  # noqa: E402
import prior as P  # noqa: E402

LIB = json.load(open(P.LIB, encoding="utf-8"))
PATH = {"division": "NSD", "band": "0 - 40 L", "zone": "North", "aov": "low"}
V = {"seller_gender": "M", "city_tier": "metro", "tense": False, "rural": False, "hindi_belt_rural": False}


def test_empty_scoreboard_uses_seeds():
    s = P.persona_scores(LIB, {"cells": {}}, PATH)
    assert s["P2"][0] > s["P6"][0]          # NSD + small + low AOV seeds favour P2 over P6


def test_strong_cell_wins(tmp_path):
    sb = {"cells": {"div=NSD|band=0 - 40 L": {"P6": {"n": 400, "s": 120}}}}
    s = P.persona_scores(LIB, sb, PATH)
    assert max(s, key=lambda k: s[k][0]) == "P6"


def test_close_arms_both_get_draws():
    sb = {"cells": {"div=NSD|band=0 - 40 L": {"P2": {"n": 30, "s": 4}, "P3": {"n": 30, "s": 4}}}}
    _, pbest = P.thompson(P.persona_scores(LIB, sb, PATH), random.Random(1))
    assert pbest["P2"] > 0.05 and pbest["P3"] > 0.05


def test_voice_prior_female_default():
    _, pb = P.thompson(P.voice_scores({"cells": {}}, V), random.Random(2))
    assert pb["F"] > 0.5


def test_voice_lean_female_rural_tense():
    v = dict(V, tense=True, rural=True, hindi_belt_rural=True)
    _, base = P.thompson(P.voice_scores({"cells": {}}, V), random.Random(3))
    _, lean = P.thompson(P.voice_scores({"cells": {}}, v), random.Random(3))
    assert lean["F"] >= base["F"]


def test_loop2_moves_scores(tmp_path):
    before = P.persona_scores(LIB, {"cells": {}}, PATH)["P4"][0]
    for _ in range(60):
        L.apply(str(tmp_path), PATH, "P4", "F", V, True)
    sb = json.load(open(tmp_path / "persona.json", encoding="utf-8"))
    after = P.persona_scores(LIB, sb, PATH)["P4"][0]
    assert after > before + 0.2


def test_holdout_rate():
    hits = sum(random.Random(i).random() < P.HOLDOUT for i in range(2000))
    assert 0.12 < hits / 2000 < 0.18


# ---------------------------------------------------------------- hierarchy v2.0 (levels and keys from references/hierarchy.json)
import hierarchy as H  # noqa: E402

HIER = H.load()
FULL = {"division": "CSD", "band": "1.5 - 5 Cr", "aov": "high", "zone": "South", "state": "telangana", "catgroup": "Apparel, Clothing & Garments"}
VFULL = {"seller_gender": "F", "city_tier": "small_town", "tense": True, "rural": True, "hindi_belt_rural": False}


def reads(fn):
    """Cell keys that prior.py asks for while computing fn()."""
    seen = set()
    orig = P.cell

    def spy(sb, key, arm):
        seen.add(key)
        return orig(sb, key, arm)
    P.cell = spy
    try:
        fn()
    finally:
        P.cell = orig
    return seen


def test_chain_is_nested_and_skips_unknown():
    ch = [k for _, k in H.chain(HIER, FULL)]
    assert ch == ["all", "div=CSD", "div=CSD|band=1.5 - 5 Cr", "div=CSD|band=1.5 - 5 Cr|aov=high",
                  "div=CSD|band=1.5 - 5 Cr|aov=high|zone=South", "div=CSD|band=1.5 - 5 Cr|aov=high|zone=South|state=telangana"]
    assert [k for _, k in H.branch_keys(HIER, FULL)] == ["div=CSD|catgroup=Apparel, Clothing & Garments"]
    cut = dict(FULL, aov="unknown")
    ck = [k for _, k in H.chain(HIER, cut)]
    assert "div=CSD|band=1.5 - 5 Cr|zone=South" in ck and not any("aov" in k for k in ck)   # unknown AOV is skipped, zone and state still count


def test_sparse_state_falls_back_to_zone():
    zone = "div=CSD|band=1.5 - 5 Cr|aov=high|zone=South"
    state = zone + "|state=telangana"
    base = {"cells": {zone: {"P5": {"n": 300, "s": 90}}}}
    sparse = {"cells": {zone: {"P5": {"n": 300, "s": 90}}, state: {"P5": {"n": 2, "s": 0}}}}
    a = P.persona_scores(LIB, base, FULL)["P5"][0]
    b = P.persona_scores(LIB, sparse, FULL)["P5"][0]
    assert abs(a - b) < 0.03 and b > 0.25         # 2 calls barely move a state: it stays near its zone (0.29), far from the base (0.12)


def test_strong_state_cell_wins():
    state = "div=CSD|band=1.5 - 5 Cr|aov=high|zone=South|state=telangana"
    sb = {"cells": {state: {"P3": {"n": 500, "s": 200}}}}
    s = P.persona_scores(LIB, sb, FULL)
    assert max(s, key=lambda k: s[k][0]) == "P3"


def test_category_group_branch_offsets_score():
    cat = "div=CSD|catgroup=Apparel, Clothing & Garments"
    none = P.persona_scores(LIB, {"cells": {}}, FULL)["P1"][0]
    some = P.persona_scores(LIB, {"cells": {cat: {"P1": {"n": 300, "s": 120}}}}, FULL)["P1"][0]
    assert some > none + 0.1


def test_loop2_keys_equal_prior_keys(tmp_path):
    """tests_required: the keys loop2 writes = the keys prior reads, both from hierarchy.json."""
    got = reads(lambda: P.persona_scores(LIB, {"cells": {}}, FULL))
    L.apply(str(tmp_path), FULL, "P1", "F", VFULL, True)
    written = set(json.load(open(tmp_path / "persona.json", encoding="utf-8"))["cells"])
    assert got == written == set(L.ARM_KEYS(FULL))
    vgot = reads(lambda: P.voice_scores({"cells": {}}, VFULL))
    vwritten = set(json.load(open(tmp_path / "voice.json", encoding="utf-8"))["cells"])
    assert vwritten == set(H.voice_keys(HIER, VFULL)) and vgot == vwritten - {"all"} | {"all"}


def test_hindi_belt_is_a_learned_voice_key(tmp_path):
    v = dict(VFULL, hindi_belt_rural=True)
    assert "hindi_belt_rural=True" in H.voice_keys(HIER, v)
    for _ in range(80):
        L.apply(str(tmp_path), FULL, "P1", "M", v, True)       # males win in Hindi-belt rural
    vs = json.load(open(tmp_path / "voice.json", encoding="utf-8"))
    before = P.voice_scores({"cells": {}}, v)["M"][0]
    assert P.voice_scores(vs, v)["M"][0] > before + 0.2


def test_group_of_numeric_and_text():
    assert H.group_of(HIER, "pace", 1.0) == "0.95-1.05" and H.group_of(HIER, "pace", 1.25) == "1.05-1.25"
    assert H.group_of(HIER, "pitch", -0.2) == "-0.3..-0.1" and H.group_of(HIER, "words_per_turn", 10) == "8-12"
    assert H.group_of(HIER, "formality", "Medium") == "medium" and H.group_of(HIER, "voice_gender", "F") == "F"
    assert H.group_of(HIER, "empathy", "acknowledge") is None and H.group_of(HIER, "pace", None) is None


def test_brief_levels_and_rates():
    empty = P.brief({"cells": {}}, FULL)
    assert empty["pace"] == {"level_used": None, "key": None, "n_total": 0, "value_groups": {}}
    div, band = "div=CSD", "div=CSD|band=1.5 - 5 Cr"
    fs = {"cells": {div: {"pace": {"0.95-1.05": {"n": 30, "s": 6}}},
                    band: {"pace": {"0.85-0.95": {"n": 25, "s": 10}, "1.05-1.25": {"n": 5, "s": 0}}},
                    band + "|aov=high": {"pace": {"0.95-1.05": {"n": 4, "s": 4}}}}}       # too few calls: not used
    b = P.brief(fs, FULL)["pace"]
    assert b["level_used"] == "L2" and b["n_total"] == 30
    assert b["value_groups"]["0.85-0.95"] == {"n": 25, "rate": 0.4} and b["value_groups"]["0.95-1.05"] == {"n": 0, "rate": None}
    fs["cells"]["div=CSD|catgroup=Apparel, Clothing & Garments"] = {"pace": {"1.05-1.25": {"n": 20, "s": 8}}}
    assert P.brief(fs, FULL)["pace"]["level_used"] == "L6"                                 # L6 is checked first
    assert set(P.brief(fs, FULL)) == set(H.learned_fields(HIER))


def test_loop2_counts_fields_reason_types_hooks_and_report(tmp_path):
    persona = {"dimensions": {"pace": {"value": 1.1, "reason_type": "seller_evidence"}, "warmth": {"value": "high", "reason_type": "start_persona"},
                              "empathy": {"value": "x", "reason_type": "hierarchy"}}, "hook": {"id": "hook.money_lead"}}
    fr = L.field_records(persona)
    assert fr == {"pace": {"group": "1.05-1.25", "reason_type": "seller_evidence", "value": 1.1},
                  "warmth": {"group": "high", "reason_type": "start_persona", "value": "high"}}   # empathy is free text: not counted
    for i in range(10):
        L.apply(str(tmp_path), FULL, "P0", "F", VFULL, i < 2, fields=fr, hook="hook.money_lead")
        L.apply(str(tmp_path), FULL, "P1", "F", VFULL, i < 6, fields=fr, hook="hook.profile_gap")
    fs = json.load(open(tmp_path / "fields.json", encoding="utf-8"))["cells"]["all"]["pace"]["1.05-1.25"]
    hs = json.load(open(tmp_path / "hooks.json", encoding="utf-8"))["cells"]["div=CSD"]
    assert fs == {"n": 20, "s": 8} and hs["hook.money_lead"] == {"n": 10, "s": 2} and hs["hook.profile_gap"] == {"n": 10, "s": 6}
    r = L.report(str(tmp_path))
    assert r["by_reason_type"]["seller_evidence"]["n"] == 20 and r["by_reason_type"]["seller_evidence"]["rate"] == 0.4
    up = next(u for u in r["uplift_vs_holdout"] if u["cell"] == "all" and u["arm"] == "P1")
    assert up["uplift_pts"] == 40.0 and up["baseline"] == "P0"


def test_dry_run_writes_nothing(tmp_path):
    L.apply(str(tmp_path), FULL, "P1", "F", VFULL, True, dry=True)
    assert not os.listdir(tmp_path)


def test_seed_leans_only_where_evidence_exists():
    sl = LIB["seed_leans"]
    assert set(sl["by_key"]) <= set(sl["evidence"]) and all(k.startswith("division=") for k in sl["by_key"])
    assert sl["dropped_guess_leans"]["by_key"]                                          # kept for the record, never applied
    p5 = {"division": "NSD", "band": "5 Cr+", "aov": "high", "zone": "North"}
    sc = P.persona_scores(LIB, {"cells": {}}, p5)
    assert sc["P6"][0] == sc["P4"][0]                                                    # no turnover / AOV / zone lean any more


def test_hierarchy_file_is_consistent():
    ids = [lv["id"] for lv in HIER["persona_levels"]]
    assert ids == ["L0", "L1", "L2", "L3", "L4", "L5", "L6"] and HIER["approved_by"] != "pending"
    for lv in HIER["persona_levels"][1:]:
        assert lv["path_key"] and lv["parent"] in ids
    for f in H.learned_fields(HIER):
        assert HIER["fields"][f]["value_groups"] and HIER["fields"][f]["probe_files"]


def test_prior_main_writes_brief_and_path(tmp_path, monkeypatch):
    folder = tmp_path / "seller"
    folder.mkdir()
    tr = lambda i, v, d=None: {"id": i, "A_script": {"value": v, "detail": d or {}}}
    facts = {"division": "CSD",
             "traits": [tr("trait.division", "CSD"), tr("trait.business_scale", "mid", {"turnover_band": "40 L - 1.5 Cr", "aov_tier": "mid"}),
                        tr("trait.city_tier", "tier2", {"state": "Gujarat", "rural_proxy": False, "hindi_belt": False}),
                        tr("trait.seller_gender", "F")],
             "states": [tr("state.call_mood", {"frustrated": 0}), tr("state.open_grievance", "no")]}
    (folder / "facts.json").write_text(json.dumps(facts), encoding="utf-8")
    (folder / "context.json").write_text(json.dumps({"points": {"D01": {"value": {"top": {"top_category_group": "Textiles"}}}}}), encoding="utf-8")
    sb = tmp_path / "sb"
    sb.mkdir()
    (sb / "fields.json").write_text(json.dumps({"cells": {"div=CSD": {"pace": {"1.05-1.25": {"n": 25, "s": 5}}}}}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["prior.py", "--folder", str(folder), "--decision-id", "d-test", "--scoreboards", str(sb)])
    P.main()
    out = json.load(open(folder / "prior.json", encoding="utf-8"))
    assert out["persona"]["path"] == {"division": "CSD", "band": "40 L - 1.5 Cr", "aov": "mid", "zone": "West", "state": "gujarat", "catgroup": "Textiles"}
    assert out["brief"]["pace"]["level_used"] == "L1" and out["brief"]["pace"]["value_groups"]["1.05-1.25"] == {"n": 25, "rate": 0.2}
    assert len(out["persona"]["top2"]) in (1, 2) and out["hierarchy_version"] == HIER["version"]
