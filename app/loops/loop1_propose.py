"""loop1_propose.py: Loop 1 (switch), between runs. Reviews -> lexicon change proposals -> gold-set check -> human.

Plan §5, Loop 1:
  1. 08_review.json labels each seller turn (true mode vs the tool's mode).
  2. Missed switch -> candidate new cue (an n-gram of that turn); wrong switch -> candidate removal of the cue that fired.
  3. Each candidate runs on the gold set (data/gold/switch_gold.jsonl); kept only if accuracy does not drop and no
     neutral gold turn starts to switch.
  4. A human approves the proposal file; then the cue goes into LEXICON in app/sarvam/vani_tools.py with a new
     LEXICON_VERSION, the tests run, and the tools file is uploaded (RUNBOOK §3).

Writes data/loops/loop1_proposal_<ts>.json (holds seller words: data/ only).
Usage: python app/loops/loop1_propose.py [--runs data/runs] [--gold data/gold/switch_gold.jsonl]
"""
import argparse
import glob
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "app", "sarvam"))
import vani_tools as T  # noqa: E402

CLASSIFY_MODES = {"neutral", "rushed", "frustrated", "confused", "interested", "bot_question", "opt_out"}


def gold_rows(path):
    return [r for r in (json.loads(x) for x in open(path, encoding="utf-8") if x.strip()) if r.get("label") in CLASSIFY_MODES]


def score(rows, compiled):
    """(accuracy, neutral false switches) of T.classify on the gold rows with the given compiled lexicon."""
    saved = T._COMPILED
    T._COMPILED = compiled
    try:
        pred = [T.classify(r["text"])[0] for r in rows]
    finally:
        T._COMPILED = saved
    acc = sum(p == r["label"] for p, r in zip(pred, rows)) / max(len(rows), 1)
    fp = sum(p != "neutral" and r["label"] == "neutral" for p, r in zip(pred, rows))
    return round(acc, 4), fp


def ngrams(text, n_max=3):
    """Candidate cues, most specific first: 3-word, then 2-word phrases, then single words of >= 6 letters."""
    w = T.norm(text).split()
    out = []
    for n in range(n_max, 0, -1):
        for i in range(len(w) - n + 1):
            g = " ".join(w[i:i + n])
            if g not in out and (n > 1 or len(g) >= 6):
                out.append(g)
    return out


def script_has_gold(cue, rows):
    s = T.script_of(cue)
    return s in ("none", "latn") or any(T.script_of(r["text"]) == s for r in rows)


def add_cue(compiled, mode, cue):
    return compiled + [(mode, "strong", cue, T._cue_re(cue))]


def drop_cue(compiled, cue):
    return [c for c in compiled if c[2] != cue]


def reviews(runs):
    for f in sorted(glob.glob(os.path.join(runs, "*", "08_review.json"))):
        rev = json.load(open(f, encoding="utf-8"))
        call = os.path.join(os.path.dirname(f), "06_call.json")
        log = json.load(open(call, encoding="utf-8")).get("switch_log") or [] if os.path.exists(call) else []
        cues = {r.get("turn"): r.get("cue") for r in log if isinstance(r, dict)}
        for t in rev.get("turns") or []:
            yield os.path.basename(os.path.dirname(f)), {**t, "cue": t.get("cue") or cues.get(t.get("turn"))}


def propose(runs, gold):
    rows = gold_rows(gold)
    base = score(rows, T._COMPILED)
    props, seen = [], set()
    all_turns = list(reviews(runs))
    neutral_turns = [T.norm(t.get("seller", "")) for _, t in all_turns if t.get("true_mode") == "neutral"]
    for run, t in all_turns:
        v, true, said = t.get("switch_verdict"), t.get("true_mode"), t.get("tool_mode")
        if v == "missed" and true in CLASSIFY_MODES - {"neutral"}:
            best = None
            for g in ngrams(t.get("seller", "")):
                if (true, g) in seen or any(T._cue_re(g).search(n) for n in neutral_turns):
                    continue  # already proposed, or the phrase also occurs in a turn the reviews judged neutral
                cand = add_cue(T._COMPILED, true, g)
                acc, fp = score(rows, cand)
                saved = T._COMPILED
                T._COMPILED = cand
                fixes = T.classify(t.get("seller", ""))[0] == true
                T._COMPILED = saved
                if fixes and acc >= base[0] and fp <= base[1]:
                    best = {"action": "add_cue", "mode": true, "cue": g, "gold_acc": acc, "gold_neutral_fp": fp,
                            "gold_covers_script": script_has_gold(g, rows)}
                    if not best["gold_covers_script"]:
                        best["warning"] = "the gold set has no turns in this script: the gold check cannot catch false switches"
                    break  # most specific phrase that fixes the turn and is safe on the gold set
            seen.add((true, best["cue"]) if best else (true, t.get("seller")))
            props.append({"run": run, "turn": t.get("turn"), "seller": t.get("seller"), "verdict": v, "true_mode": true,
                          "tool_mode": said, "proposal": best or {"action": "none", "why": "no safe n-gram on the gold set"}})
        elif v == "wrong" and t.get("cue"):
            cue = str(t["cue"]).split(" [")[0]
            acc, fp = score(rows, drop_cue(T._COMPILED, cue))
            ok = acc >= base[0]
            props.append({"run": run, "turn": t.get("turn"), "seller": t.get("seller"), "verdict": v, "true_mode": true,
                          "tool_mode": said, "proposal": {"action": "drop_cue" if ok else "none", "cue": cue,
                                                          "gold_acc": acc, "gold_neutral_fp": fp}})
    return {"lexicon": T.LEXICON_VERSION, "gold": os.path.relpath(gold, ROOT), "gold_rows": len(rows),
            "baseline": {"acc": base[0], "neutral_fp": base[1]}, "proposals": props,
            "status": "awaiting human approval"}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--runs", default=os.path.join(ROOT, "data", "runs"))
    a.add_argument("--gold", default=os.path.join(ROOT, "data", "gold", "switch_gold.jsonl"))
    p = a.parse_args()
    out = propose(p.runs, p.gold)
    os.makedirs(os.path.join(ROOT, "data", "loops"), exist_ok=True)
    path = os.path.join(ROOT, "data", "loops", f"loop1_proposal_{time.strftime('%Y%m%d-%H%M%S')}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    acts = [x["proposal"]["action"] for x in out["proposals"]]
    print(json.dumps({"baseline": out["baseline"], "proposals": len(acts), "add_cue": acts.count("add_cue"),
                      "drop_cue": acts.count("drop_cue"), "file": os.path.relpath(path, ROOT)}))


if __name__ == "__main__":
    main()
