"""prior.py: starting persona, voice and per-field brief for one seller, from learning scoreboards (S2).

The levels, keys, kappa, holdout and base means come from references/hierarchy.json through scripts/hierarchy.py (no level list in this file).
Scoreboard A (persona arms P0..P6): nested chain L0 all -> L1 division -> L2 band -> L3 AOV tier -> L4 zone -> L5 state, with L6 category
group as a branch under L1. Partial pooling at each level: a cell with few calls falls back to its parent (kappa pseudo-calls).
Scoreboard B (voice F / M): asymmetric female base plus flat offsets for each voice level (seller gender, city tier, tension, Hindi belt).
Thompson sampling picks the top-2 personas only (never a field value); P(best) by Monte Carlo is logged as the propensity.
A 15% holdout uses P0 (current production style) as the comparison arm.
Brief: for each learned field, the value groups that got meetings at the deepest level with enough calls (see hierarchy.json 'brief').

Scoreboards live in data/scoreboards/{persona,voice,fields}.json and are updated only by loop2_update.py.
Usage: python3 prior.py --folder <seller folder> --decision-id <id> [--scoreboards <dir>]
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hierarchy as H  # noqa: E402

LIB = os.path.join(HERE, "..", "references", "persona_library.json")
HIER = H.load()
KAPPA = HIER["kappa"]
HOLDOUT = HIER["holdout"]["share"]
BASE = HIER["base_means"]["persona"]
VOICE_BASE = HIER["base_means"]["voice"]
VOICE_LEAN_F = HIER["voice_lean_f"]["value"]
MIN_CALLS = HIER["brief"]["min_calls"]
DRAWS = 4000


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigm(x):
    return 1 / (1 + math.exp(-x))


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
    """Weak lean toward an arm, only for the keys in persona_library.json seed_leans.by_key (evidence-backed leans only)."""
    lean = lib["seed_leans"]
    return lean["base_mean"] + (lean["lean"] if arm in lean["by_key"].get(f"{keyname}={value}", []) else 0)


def _level_seed(lib, lv, path, arm):
    sk = lv.get("seed_key")
    return seed_mean(lib, sk, path.get(lv["path_key"]), arm) if sk else None


def persona_scores(lib, sb, path, h=None):
    """Mean and effective n per arm. Walks the nested chain (each level pools toward its parent), then adds the L6 branch as an offset."""
    h = h or HIER
    levels = {lv["id"]: lv for lv in h["persona_levels"]}
    ch, br = H.chain(h, path), H.branch_keys(h, path)
    out = {}
    for p in lib["personas"]:
        arm = p["id"]
        m, eff = BASE, KAPPA
        m_by_level = {}
        for lid, key in ch:
            seed = _level_seed(lib, levels[lid], path, arm) if lid != "L0" else None
            prior_mean = (m + seed) / 2 if seed is not None else m
            m, eff = pooled(prior_mean, *cell(sb, key, arm))
            m_by_level[lid] = m
        x = logit(m)
        for lid, key in br:                                   # branch level: additive offset from its parent level, shrunk by kappa
            parent = m_by_level.get(levels[lid]["parent"], m)
            post, _ = pooled(parent, *cell(sb, key, arm))
            x += logit(post) - logit(parent)
        out[arm] = (sigm(x), eff)
    return out


def voice_scores(sb, v, h=None):
    h = h or HIER
    keys = H.voice_keys(h, v)[1:]
    out = {}
    for arm in ("F", "M"):
        m, eff = pooled(VOICE_BASE[arm], *cell(sb, "all", arm))
        x = logit(m)
        lean_f = (v["tense"] or v["rural"] or v["hindi_belt_rural"])
        if arm == "F" and lean_f:
            x += logit(VOICE_BASE["F"] + VOICE_LEAN_F) - logit(VOICE_BASE["F"])
        for key in keys:
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


def brief(fields_sb, path, h=None, min_calls=None):
    """{field: {level_used, key, n_total, value_groups: {group: {n, rate}}}} for every learned field.
    Levels are tried deepest first (L6 branch, then L5 down to L0); the first with >= min_calls calls for the field is used."""
    h = h or HIER
    min_calls = MIN_CALLS if min_calls is None else min_calls
    ch, br = H.chain(h, path), H.branch_keys(h, path)
    order = list(reversed(br)) + list(reversed(ch))
    out = {}
    for f in H.learned_fields(h):
        groups = h["fields"][f]["value_groups"]
        entry = {"level_used": None, "key": None, "n_total": 0, "value_groups": {}}
        for lid, key in order:
            cells = (fields_sb.get("cells", {}).get(key, {}) or {}).get(f, {})
            total = sum(c.get("n", 0) for c in cells.values())
            if total >= min_calls:
                entry = {"level_used": lid, "key": key, "n_total": total,
                         "value_groups": {g: {"n": cells.get(g, {}).get("n", 0),
                                              "rate": (round(cells[g]["s"] / cells[g]["n"], 4) if cells.get(g, {}).get("n") else None)}
                                          for g in groups}}
                break
        out[f] = entry
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--folder", required=True)
    a.add_argument("--decision-id", required=True)
    a.add_argument("--scoreboards", default=None)
    p = a.parse_args()
    sbdir = p.scoreboards or os.path.join(p.folder, "..", "..", "scoreboards")
    facts = json.load(open(os.path.join(p.folder, "facts.json"), encoding="utf-8"))
    ctx_path = os.path.join(p.folder, "context.json")
    points = json.load(open(ctx_path, encoding="utf-8")).get("points", {}) if os.path.exists(ctx_path) else {}
    lib = json.load(open(LIB, encoding="utf-8"))
    val = {x["id"]: x["A_script"] for x in facts["traits"] + facts["states"]}
    by_id = {k: {"value": v["value"], "detail": v.get("detail") or {}} for k, v in val.items()}
    path = H.resolve_path(HIER, by_id, points)
    ct = val["trait.city_tier"]
    rng = random.Random(int(hashlib.sha256(p.decision_id.encode()).hexdigest()[:12], 16))
    holdout = rng.random() < HOLDOUT
    pscores = persona_scores(lib, load(os.path.join(sbdir, "persona.json")), path)
    order, pbest = thompson(pscores, rng)
    if holdout:
        top2 = [HIER["holdout"]["arm"]]
        chosen_rule = f"holdout: {top2[0]} baseline (measurement arm, {int(HOLDOUT * 100)}%)"
    else:
        top2 = [x for x in order if x != HIER["holdout"]["arm"]][:HIER["select_rule"]["top_n"]]
        chosen_rule = "Thompson draw picks the top-2 only; agent selects one as its base"
    mood = val["state.call_mood"]["value"] or {}
    tense = bool((mood.get("frustrated") or 0) >= 0.5 or val["state.open_grievance"]["value"] == "yes")
    v = {"seller_gender": val["trait.seller_gender"]["value"], "city_tier": ct["value"], "tense": tense,
         "rural": bool(ct["detail"].get("rural_proxy")), "hindi_belt_rural": bool(ct["detail"].get("rural_proxy") and ct["detail"].get("hindi_belt"))}
    vscores = voice_scores(load(os.path.join(sbdir, "voice.json")), v)
    vorder, vpbest = thompson(vscores, rng)
    out = {"decision_id": p.decision_id, "library_version": lib["version"], "hierarchy_version": HIER["version"], "kappa": KAPPA,
           "persona": {"path": path, "holdout": holdout, "top2": top2, "rule": chosen_rule, "p_best": pbest,
                       "scores": {k: round(m, 4) for k, (m, n) in pscores.items()},
                       "top2_cards": [next(x for x in lib["personas"] if x["id"] == t) for t in top2]},
           "voice": {"inputs": v, "chosen": vorder[0], "p_best": vpbest, "scores": {k: round(m, 4) for k, (m, n) in vscores.items()}},
           "brief": brief(load(os.path.join(sbdir, "fields.json")), path)}
    with open(os.path.join(p.folder, "prior.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"path": path, "top2": top2, "holdout": holdout, "voice": vorder[0], "p_voice_F": vpbest["F"]}))


if __name__ == "__main__":
    main()
