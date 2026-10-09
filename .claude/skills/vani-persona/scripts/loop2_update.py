"""loop2_update.py: Loop 2 (between runs). Adds one call outcome to every scoreboard cell on its path.

Inputs: data/runs/<decision_id>/03_prior.json (path, arms) and 04_persona.json (final persona, amendments) and
07_outcome.json ({"meeting_fixed": true/false, "meeting_held": null|true|false}).
Credit (review M10): the arm is the persona the script's draw chose (top2 entry the agent started from). If the agent
fully overrode it (COMPOSED), the outcome is logged to the separate arm "COMPOSED". Amendments are logged as factors
in amendments.json for later analysis; they never change persona cells directly.

Usage: python3 loop2_update.py --run data/runs/<decision_id> [--scoreboards data/scoreboards] [--dry-run]
       python3 loop2_update.py --replay replay.jsonl   (rows: {path, arm, voice, voice_inputs, meeting})
"""
import argparse
import json
import os

ARM_KEYS = lambda path: ["all", f"div={path['division']}", f"div={path['division']}|band={path['band']}",
                         f"zone={path['zone']}", f"aov={path['aov']}"]


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {"cells": {}}


def add(sb, key, arm, win):
    c = sb["cells"].setdefault(key, {}).setdefault(arm, {"n": 0, "s": 0})
    c["n"] += 1
    c["s"] += 1 if win else 0


def apply(sbdir, path, arm, voice, vin, win, dry=False):
    ps, vs = load(os.path.join(sbdir, "persona.json")), load(os.path.join(sbdir, "voice.json"))
    for k in ARM_KEYS(path):
        add(ps, k, arm, win)
    for k in ["all", f"seller_gender={vin.get('seller_gender')}", f"city_tier={vin.get('city_tier')}", f"tense={vin.get('tense')}"]:
        add(vs, k, voice, win)
    if not dry:
        os.makedirs(sbdir, exist_ok=True)
        json.dump(ps, open(os.path.join(sbdir, "persona.json"), "w", encoding="utf-8"), indent=1)
        json.dump(vs, open(os.path.join(sbdir, "voice.json"), "w", encoding="utf-8"), indent=1)
    return ps, vs


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run")
    a.add_argument("--replay")
    a.add_argument("--scoreboards", default=os.path.join("data", "scoreboards"))
    a.add_argument("--dry-run", action="store_true")
    p = a.parse_args()
    if p.replay:
        n = 0
        for line in open(p.replay, encoding="utf-8"):
            r = json.loads(line)
            apply(p.scoreboards, r["path"], r["arm"], r["voice"], r["voice_inputs"], r["meeting"], p.dry_run)
            n += 1
        print(f"replayed {n} outcomes into {p.scoreboards}")
        return
    prior = json.load(open(os.path.join(p.run, "03_prior.json"), encoding="utf-8"))
    persona = json.load(open(os.path.join(p.run, "04_persona.json"), encoding="utf-8"))
    outcome = json.load(open(os.path.join(p.run, "07_outcome.json"), encoding="utf-8"))
    win = bool(outcome.get("meeting_held") if outcome.get("meeting_held") is not None else outcome.get("meeting_fixed"))
    start = persona.get("prior", {}).get("chosen")
    arm = start if start in prior["persona"]["top2"] else "COMPOSED"
    apply(p.scoreboards, prior["persona"]["path"], arm, persona["voice"]["gender"], prior["voice"]["inputs"], win, p.dry_run)
    with open(os.path.join(p.scoreboards, "amendments.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"decision_id": prior["decision_id"], "arm": arm, "path": prior["persona"]["path"],
                            "amendments": persona.get("amendments", []), "meeting": win}) + "\n")
    print(json.dumps({"arm": arm, "voice": persona["voice"]["gender"], "meeting": win}))


if __name__ == "__main__":
    main()
