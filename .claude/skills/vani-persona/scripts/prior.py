"""prior.py: starting persona and voice for one seller, from two learning scoreboards (S2).

Scoreboard A (persona arms P0..P6): hierarchy  all → division → turnover band  (Beta partial pooling, κ pseudo-calls),
plus additive log-odds offsets for zone and AOV tier (review M12: few levels, separate effects).
Scoreboard B (voice F / M): base with an asymmetric female prior (team decision), plus offsets for seller gender,
city tier (rural proxy), Hindi belt and call tension (review M13).
Thompson sampling picks the arm; P(best) by Monte Carlo is logged as the propensity (review M10).
A 15% holdout uses P0 (current production style) as the measurement baseline (review M11) - a normal arm, not a fallback.

Scoreboards live in data/scoreboards/{persona,voice}.json and are updated only by loop2_update.py.
Usage: python3 prior.py --folder <seller folder> --decision-id <id> [--scoreboards <dir>]
"""
import argparse
import hashlib
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "references", "persona_library.json")
KAPPA = 20
HOLDOUT = 0.15
DRAWS = 4000
BASE = 0.12
VOICE_BASE = {"F": 0.13, "M": 0.11}      # asymmetric: female default (team decision 2026-10-10)
VOICE_LEAN_F = 0.02                        # extra female lean for tense calls and rural / Hindi-belt sellers
BANDS = ["0 - 40 L", "40 L - 1.5 Cr", "1.5 - 5 Cr", "5 - 25 Cr", "25 - 100 Cr", "100 - 500 Cr", "> 500 Cr"]
ZONE = {"North": "delhi haryana punjab chandigarh himachal pradesh jammu and kashmir uttarakhand uttar pradesh rajasthan",
        "West": "maharashtra gujarat goa", "South": "tamil nadu karnataka kerala andhra pradesh telangana puducherry",
        "East": "west bengal odisha bihar jharkhand assam meghalaya tripura manipur mizoram nagaland arunachal pradesh sikkim",
        "Central": "madhya pradesh chhattisgarh"}


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigm(x):
    return 1 / (1 + math.exp(-x))


def zone_of(state):
    s = (state or "").strip().lower()
    for z, ss in ZONE.items():
        if s and s in ss:
            return z
    return "Other"


def band_group(band):
    if band not in BANDS:
        return "unknown"
    return band if BANDS.index(band) < 3 else "5 Cr+"


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {"cells": {}}


def cell(sb, key, arm):
    c = sb["cells"].get(key, {}).get(arm, {})
    return c.get("n", 0), c.get("s", 0)


def pooled(prior_mean, n, s, k=KAPPA):
    return (k * prior_mean + s) / (k + n), k + n


def seed_mean(lib, keyname, value, arm):
    lean = lib["seed_leans"]
    return lean["base_mean"] + (lean["lean"] if arm in lean["by_key"].get(f"{keyname}={value}", []) else 0)


def persona_scores(lib, sb, path):
    """Mean and effective n per arm: L0 → division → band (pooling), then zone and AOV offsets."""
    out = {}
    for p in lib["personas"]:
        arm = p["id"]
        m, eff = pooled(BASE, *cell(sb, "all", arm))
        m, eff = pooled((m + seed_mean(lib, "division", path["division"], arm)) / 2, *cell(sb, f"div={path['division']}", arm))
        m, eff = pooled((m + seed_mean(lib, "turnover", path["band"], arm)) / 2,
                        *cell(sb, f"div={path['division']}|band={path['band']}", arm))
        x = logit(m)
        for keyname, val in (("zone", path["zone"]), ("aov", path["aov"])):
            n, s = cell(sb, f"{keyname}={val}", arm)
            prior = seed_mean(lib, keyname, val, arm)
            post, _ = pooled(prior, n, s)
            x += logit(post) - logit(BASE)          # additive offset, shrunk by κ
        out[arm] = (sigm(x), eff)
    return out


def voice_scores(sb, v):
    out = {}
    for arm in ("F", "M"):
        m, eff = pooled(VOICE_BASE[arm], *cell(sb, "all", arm))
        x = logit(m)
        lean_f = (v["tense"] or v["rural"] or v["hindi_belt_rural"])
        if arm == "F" and lean_f:
            x += logit(VOICE_BASE["F"] + VOICE_LEAN_F) - logit(VOICE_BASE["F"])
        for key in (f"seller_gender={v['seller_gender']}", f"city_tier={v['city_tier']}", f"tense={v['tense']}"):
            n, s = cell(sb, key, arm)
            post, _ = pooled(m, n, s)
            x += logit(post) - logit(m)
        out[arm] = (sigm(x), eff)
    return out


def thompson(scores, rng):
    arms = list(scores)
    wins = {a: 0 for a in arms}
    first_draw = None
    for i in range(DRAWS):
        d = {a: rng.betavariate(max(1e-3, m * n), max(1e-3, (1 - m) * n)) for a, (m, n) in scores.items()}
        best = max(d, key=d.get)
        wins[best] += 1
        if i == 0:
            first_draw = sorted(d, key=d.get, reverse=True)
    pbest = {a: round(wins[a] / DRAWS, 4) for a in arms}
    return first_draw, pbest


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--decision-id", required=True)
    a.add_argument("--scoreboards", default=None)
    p = a.parse_args()
    sbdir = p.scoreboards or os.path.join(p.folder, "..", "..", "scoreboards")
    facts = json.load(open(os.path.join(p.folder, "facts.json"), encoding="utf-8"))
    lib = json.load(open(LIB, encoding="utf-8"))
    val = {x["id"]: x["A_script"] for x in facts["traits"] + facts["states"]}
    div = facts["division"] if facts["division"] in ("NSD", "CSD") else ("CSD" if facts["division"] in ("TMW", "KCD") else "NSD")
    scale = val["trait.business_scale"]["detail"]
    ct = val["trait.city_tier"]
    path = {"division": div, "band": band_group(scale.get("turnover_band")), "aov": scale.get("aov_tier") or "unknown",
            "zone": zone_of(ct["detail"].get("state"))}
    rng = random.Random(int(hashlib.sha256(p.decision_id.encode()).hexdigest()[:12], 16))
    holdout = rng.random() < HOLDOUT
    pscores = persona_scores(lib, load(os.path.join(sbdir, "persona.json")), path)
    order, pbest = thompson(pscores, rng)
    if holdout:
        top2 = ["P0"]
        chosen_rule = "holdout: P0 baseline (measurement arm, 15%)"
    else:
        top2 = [x for x in order if x != "P0"][:2]
        chosen_rule = "Thompson draw; agent must start from top2[0] or top2[1]"
    mood = val["state.call_mood"]["value"] or {}
    tense = bool((mood.get("frustrated") or 0) >= 0.5 or val["state.open_grievance"]["value"] == "yes")
    v = {"seller_gender": val["trait.seller_gender"]["value"], "city_tier": ct["value"], "tense": tense,
         "rural": bool(ct["detail"].get("rural_proxy")), "hindi_belt_rural": bool(ct["detail"].get("rural_proxy") and ct["detail"].get("hindi_belt"))}
    vscores = voice_scores(load(os.path.join(sbdir, "voice.json")), v)
    vorder, vpbest = thompson(vscores, rng)
    out = {"decision_id": p.decision_id, "library_version": lib["version"], "kappa": KAPPA,
           "persona": {"path": path, "holdout": holdout, "top2": top2, "rule": chosen_rule, "p_best": pbest,
                       "scores": {k: round(m, 4) for k, (m, n) in pscores.items()},
                       "top2_cards": [next(x for x in lib["personas"] if x["id"] == t) for t in top2]},
           "voice": {"inputs": v, "chosen": vorder[0], "p_best": vpbest, "scores": {k: round(m, 4) for k, (m, n) in vscores.items()}}}
    with open(os.path.join(p.folder, "prior.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"path": path, "top2": top2, "holdout": holdout, "voice": vorder[0], "p_voice_F": vpbest["F"]}))


if __name__ == "__main__":
    main()
