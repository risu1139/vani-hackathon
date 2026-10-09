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
