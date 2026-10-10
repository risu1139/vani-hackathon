"""loop2_update.py: Loop 2 (between runs). Adds one call outcome to the scoreboard cells on the seller's path.

Levels and keys come from references/hierarchy.json through scripts/hierarchy.py: the SAME functions prior.py uses to read, so the keys
written here equal the keys read there.

Inputs: data/runs/<decision_id>/03_prior.json (path, arms), 04_persona.json (final persona: dimensions with value, reason_type; hook)
and 07_outcome.json ({"meeting_fixed": true/false, "meeting_held": null|true|false}).
Credit (review M10): the arm is the persona the script's draw chose (the top-2 entry the agent selected as its base). If the agent fully
overrode it (COMPOSED), the outcome is logged to the separate arm "COMPOSED".

Scoreboards written (data/scoreboards/ or data/scoreboards_test/):
  persona.json  cells[key][arm] = {n, s}            (nested chain + L6 branch)
  voice.json    cells[key][voice] = {n, s}          (flat voice keys, Hindi belt included)
  fields.json   cells[key][field][value_group] = {n, s}   (the brief reads this)
  reasons.json  cells[reason_type][field] = {n, s}  plus cells[reason_type]['_all']   (seller_evidence / hierarchy / start_persona / ...)
  hooks.json    cells[key][hook_id] = {n, s}        (per-segment hook tally, same persona keys)
  rules.json    cells[rule_id][field] = {n, s} plus cells[rule_id]['_all']   (start rules that fixed a value: dimensions[field].start_rule_ids)
  decisions.jsonl / amendments.jsonl: one row per call (path, arm, hook, per-field group + reason_type, amendments, outcome)

Usage: python3 loop2_update.py --run data/runs/<decision_id> [--scoreboards data/scoreboards] [--dry-run]
       python3 loop2_update.py --replay replay.jsonl   (rows: {path, arm, voice, voice_inputs, meeting, [fields], [hook]})
       python3 loop2_update.py --report [--scoreboards data/scoreboards] [--json]   (meeting rate by reason_type; uplift vs the holdout arm)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hierarchy as H  # noqa: E402

HIER = H.load()


def ARM_KEYS(path, h=None):
    """Persona cell keys for a path (kept as the public name used by the tests and close_loop)."""
    return H.persona_keys(h or HIER, path)


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {"cells": {}}


def add(sb, key, arm, win):
    c = sb["cells"].setdefault(key, {}).setdefault(arm, {"n": 0, "s": 0})
    c["n"] += 1
    c["s"] += 1 if win else 0


def add3(sb, key, field, group, win):
    c = sb["cells"].setdefault(key, {}).setdefault(field, {}).setdefault(group, {"n": 0, "s": 0})
    c["n"] += 1
    c["s"] += 1 if win else 0


def field_records(persona, h=None):
    """{field: {group, reason_type, value}} for every learned field of a finished persona (04_persona.json)."""
    h = h or HIER
    out = {}
    dims = persona.get("dimensions") or {}
    for f in H.learned_fields(h):
        d = dims.get(f)
        if not isinstance(d, dict) or d.get("value") in (None, ""):
            continue
        g = H.group_of(h, f, d.get("value"))
        if g is not None:
            out[f] = {"group": g, "reason_type": d.get("reason_type") or "unspecified", "value": d.get("value")}
    return out


def rule_records(persona):
    """[(field, rule_id)] for every dimension decided by start rules (reason_type start_persona with start_rule_ids)."""
    out = []
    for f, d in (persona.get("dimensions") or {}).items():
        if isinstance(d, dict) and d.get("reason_type") == "start_persona":
            out += [(f, r) for r in (d.get("start_rule_ids") or [])]
    return out


def apply(sbdir, path, arm, voice, vin, win, dry=False, fields=None, hook=None, h=None, rules=None):
    """Add one outcome. fields = {field: {group, reason_type}}; hook = hook id; rules = [(field, rule_id)]. Returns (persona_sb, voice_sb)."""
    h = h or HIER
    ps, vs = load(os.path.join(sbdir, "persona.json")), load(os.path.join(sbdir, "voice.json"))
    fs, rs, hs, ru = (load(os.path.join(sbdir, n)) for n in ("fields.json", "reasons.json", "hooks.json", "rules.json"))
    pkeys = H.persona_keys(h, path)
    for k in pkeys:
        add(ps, k, arm, win)
    for k in H.voice_keys(h, vin):
        add(vs, k, voice, win)
    for f, r in (fields or {}).items():
        for k in pkeys:
            add3(fs, k, f, r["group"], win)
        rt = r.get("reason_type") or "unspecified"
        add(rs, rt, f, win)
        add(rs, rt, "_all", win)
    if hook:
        for k in pkeys:
            add(hs, k, hook, win)
    for f, rid in (rules or []):
        add(ru, rid, f, win)
        add(ru, rid, "_all", win)
    if not dry:
        os.makedirs(sbdir, exist_ok=True)
        for name, sb in (("persona.json", ps), ("voice.json", vs), ("fields.json", fs), ("reasons.json", rs), ("hooks.json", hs), ("rules.json", ru)):
            json.dump(sb, open(os.path.join(sbdir, name), "w", encoding="utf-8"), indent=1)
    return ps, vs


def rate(c):
    return round(c["s"] / c["n"], 4) if c and c.get("n") else None


def report(sbdir, h=None):
    """Meeting rate by reason_type, and uplift of every arm versus the holdout arm (P0) in the same cell."""
    h = h or HIER
    rs, ps = load(os.path.join(sbdir, "reasons.json")), load(os.path.join(sbdir, "persona.json"))
    by_reason = {}
    for rt, cols in sorted(rs["cells"].items()):
        by_reason[rt] = {"n": cols.get("_all", {}).get("n", 0), "rate": rate(cols.get("_all")),
                         "by_field": {f: {"n": c["n"], "rate": rate(c)} for f, c in sorted(cols.items()) if f != "_all"}}
    base = h["holdout"]["arm"]
    uplift = []
    for key, arms in sorted(ps["cells"].items()):
        b = arms.get(base)
        if not b or not b.get("n"):
            continue
        for arm, c in sorted(arms.items()):
            if arm == base or not c.get("n"):
                continue
            uplift.append({"cell": key, "arm": arm, "n": c["n"], "rate": rate(c), "baseline": base, "baseline_n": b["n"],
                           "baseline_rate": rate(b), "uplift_pts": round((rate(c) - rate(b)) * 100, 2)})
    ru = load(os.path.join(sbdir, "rules.json"))
    by_rule = {rid: {"n": cols.get("_all", {}).get("n", 0), "rate": rate(cols.get("_all")),
                     "by_field": {f: {"n": c["n"], "rate": rate(c)} for f, c in sorted(cols.items()) if f != "_all"}}
               for rid, cols in sorted(ru["cells"].items())}
    return {"by_reason_type": by_reason, "by_start_rule": by_rule, "uplift_vs_holdout": uplift,
            "note": "rates are meetings per call in that cell; small n means no conclusion; uplift needs both arms in the same cell"}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run")
    a.add_argument("--replay")
    a.add_argument("--report", action="store_true")
    a.add_argument("--json", action="store_true")
    a.add_argument("--scoreboards", default=os.path.join("data", "scoreboards"))
    a.add_argument("--dry-run", action="store_true")
    p = a.parse_args()
    if p.report:
        r = report(p.scoreboards)
        if p.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
            return
        print("Meeting rate by reason_type")
        for rt, v in r["by_reason_type"].items():
            print(f"  {rt}: n={v['n']} rate={v['rate']}")
        print("Meeting rate by start rule (rule fixed a value)")
        for rid, v in r["by_start_rule"].items():
            print(f"  {rid}: n={v['n']} rate={v['rate']}")
        print(f"Uplift vs {HIER['holdout']['arm']} (same cell): {len(r['uplift_vs_holdout'])} comparisons")
        for u in r["uplift_vs_holdout"][:30]:
            print(f"  {u['cell']} {u['arm']}: {u['rate']} (n={u['n']}) vs {u['baseline_rate']} (n={u['baseline_n']}): {u['uplift_pts']} pts")
        return
    if p.replay:
        n = 0
        for line in open(p.replay, encoding="utf-8"):
            r = json.loads(line)
            apply(p.scoreboards, r["path"], r["arm"], r["voice"], r["voice_inputs"], r["meeting"], p.dry_run,
                  fields=r.get("fields"), hook=r.get("hook"), rules=[tuple(x) for x in r.get("rules") or []])
            n += 1
        print(f"replayed {n} outcomes into {p.scoreboards}")
        return
    prior = json.load(open(os.path.join(p.run, "03_prior.json"), encoding="utf-8"))
    persona = json.load(open(os.path.join(p.run, "04_persona.json"), encoding="utf-8"))
    outcome = json.load(open(os.path.join(p.run, "07_outcome.json"), encoding="utf-8"))
    win = bool(outcome.get("meeting_held") if outcome.get("meeting_held") is not None else outcome.get("meeting_fixed"))
    start = persona.get("prior", {}).get("chosen")
    arm = start if start in prior["persona"]["top2"] else "COMPOSED"
    voice = ((persona.get("dimensions") or {}).get("voice_gender") or {}).get("value") or (persona.get("voice") or {}).get("gender")
    fields = field_records(persona)
    hook = (persona.get("hook") or {}).get("id")
    rules = rule_records(persona)
    apply(p.scoreboards, prior["persona"]["path"], arm, voice, prior["voice"]["inputs"], win, p.dry_run, fields=fields, hook=hook, rules=rules)
    if not p.dry_run:
        os.makedirs(p.scoreboards, exist_ok=True)
        row = {"decision_id": prior["decision_id"], "arm": arm, "path": prior["persona"]["path"], "hook": hook,
               "amendments": persona.get("amendments", []), "meeting": win}
        with open(os.path.join(p.scoreboards, "amendments.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        with open(os.path.join(p.scoreboards, "decisions.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({**row, "fields": {k: {"group": v["group"], "reason_type": v["reason_type"]} for k, v in fields.items()},
                                "voice": voice, "hierarchy_version": prior.get("hierarchy_version"),
                                "start_rule_ids": {f: [r for ff, r in rules if ff == f] for f in sorted({ff for ff, _ in rules})}}, ensure_ascii=False) + "\n")
    print(json.dumps({"arm": arm, "voice": voice, "hook": hook, "meeting": win, "fields_counted": len(fields), "start_rules": len(rules), "scoreboards": p.scoreboards}))


if __name__ == "__main__":
    main()
