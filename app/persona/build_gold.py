"""Gold set for the mid-call switcher (review M17): real PS07 seller turns labelled by Jev, plus the hand-made sentences.

Steps (all output stays in git-ignored data/gold/):
  sample  scan data/index/sellers.sqlite (source ps07_call_turns, speaker = seller), bucket each turn with keyword
          pre-filters, and draw a stratified sample (~150) that oversamples the rare signals.
          -> data/gold/ps07_candidates.jsonl
  label   ask Jev the 6 spike questions (app/spike/jev_spike.py) plus opt_out, one call per turn, cached by text hash.
          -> data/gold/jev_labels.jsonl
  write   merge Jev-labelled PS07 turns with the hand-made sentences of jev_spike.py / jev_devanagari.py.
          -> data/gold/switch_gold.jsonl  rows {text, label, labels, source, label_by, ...}
          -> data/gold/counts.json         aggregate counts only (safe to copy into raw/)
  all     sample + label + write

Label = the first positive signal in PRIORITY (opt_out > bot_question > frustrated > confused > rushed > interested),
else neutral. Jev labels are unreviewed until a human spot check (label_by says so).
Run: python app/persona/build_gold.py all [--n 150] [--seed 7]
"""
import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "data", "index", "sellers.sqlite")
GOLD = os.path.join(REPO, "data", "gold")
CAND = os.path.join(GOLD, "ps07_candidates.jsonl")
JEV = os.path.join(GOLD, "jev_labels.jsonl")
OUT = os.path.join(GOLD, "switch_gold.jsonl")
COUNTS = os.path.join(GOLD, "counts.json")

SIGNALS = ["rushed", "frustrated", "confused", "interested", "bot_question", "opt_out"]
PRIORITY = ["opt_out", "bot_question", "frustrated", "confused", "rushed", "interested"]
LABELS = PRIORITY + ["neutral"]

# keyword pre-filters (romanised + Devanagari), only to oversample rare signals; the label comes from Jev
PREFILTER = {
    "opt_out": r"call mat|phone mat|mat karna|mat kariye|don.?t call|do not call|stop call|number hata|remove (my )?number|"
               r"band karo|dobara|कॉल मत|फोन मत|मत करना|नंबर हटा|दोबारा",
    "bot_question": r"\bbot\b|robot|recorded|recording|\bai\b|machine|insaan|real person|human|बॉट|रोबोट|रिकॉर्ड|मशीन|इंसान",
    "frustrated": r"kitni baar|pareshan|faltu|irritat|dimag|harass|bakwas|बार बार|कितनी बार|परेशान|फालतू|दिमाग|बकवास",
    "confused": r"samajh nahi|samjha nahi|kya bola|kya matlab|kaun bol|kis cheez|phir se bol|didn.?t understand|samjh|"
                r"समझ नहीं|क्या बोला|क्या मतलब|कौन बोल|किस चीज़|फिर से बोल",
    "rushed": r"busy|baad me|later|meeting me|driving|time nahi|abhi nahi|jaldi|बिज़ी|बिजी|बाद में|टाइम नहीं|अभी नहीं|जल्दी|ड्राइव",
    "interested": r"kitna|price|charge|rate|details|bhej|kab aa|aa jaiye|theek hai|कितना|प्राइस|चार्ज|रेट|डिटेल|भेज|कब आ|आ जाइए|ठीक है",
}
PRE = {k: re.compile(v, re.I) for k, v in PREFILTER.items()}
QUOTA = {"opt_out": 20, "bot_question": 20, "frustrated": 20, "confused": 20, "rushed": 20, "interested": 20, "neutral": 30}

OPT_OUT_Q = {"type": "noul",
             "instructions": "In the latest seller turn, does the seller ask IndiaMART to stop calling them, remove their number, "
                             "or never call again?",
             "criteria": {"true": "e.g. 'dobara call mat karna', 'number hata do', 'mujhe call mat karo', 'don't call me again', "
                                  "'कॉल मत करना', 'मेरा नंबर हटा दो'.",
                          "false": "Refusing the offer only ('nahi chahiye', 'interest nahi hai') without asking to stop calls, "
                                   "or asking to call later."}}


def scrub(t):
    t = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", t)
    return re.sub(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)", "[phone]", t)


def bucket(text):
    return next((k for k in PRE if PRE[k].search(text)), "neutral")


# ---------------------------------------------------------------- sample
def sample(n=150, seed=7, per_bucket_pool=400):
    """One pass over the PS07 turns; reservoir per bucket, so memory stays small. Keeps the bot line before each turn."""
    rnd = random.Random(seed)
    pools, seen = {k: [] for k in QUOTA}, Counter()
    con = sqlite3.connect(DB)
    prev = {}
    t0 = time.time()
    for (row,) in con.execute("SELECT row FROM r WHERE source = 'ps07_call_turns'"):
        r = json.loads(row)
        sp, text, aid = (r.get("speaker") or "").lower(), (r.get("text") or "").strip(), r.get("attempt_id")
        if sp != "seller":
            prev[aid] = text  # the last non-seller (bot) line of this call
            if len(prev) > 5000:
                prev.clear()
            continue
        if not (2 <= len(text.split()) <= 40):
            continue
        b = bucket(text)
        seen[b] += 1
        item = {"text": scrub(text), "prefilter": b, "agent_last_line": scrub(prev.get(aid) or "")[:300]}
        pool = pools[b]
        if len(pool) < per_bucket_pool:
            pool.append(item)
        else:
            j = rnd.randrange(seen[b])
            if j < per_bucket_pool:
                pool[j] = item
    con.close()
    total = sum(QUOTA.values())
    out, texts = [], set()
    for b, q in QUOTA.items():
        q = round(q * n / total)
        for it in rnd.sample(pools[b], len(pools[b])):
            if q <= 0:
                break
            if it["text"] not in texts:
                texts.add(it["text"])
                out.append(it)
                q -= 1
    os.makedirs(GOLD, exist_ok=True)
    with open(CAND, "w", encoding="utf-8") as f:
        for it in out:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"sample: {len(out)} turns; seller turns per pre-filter bucket {dict(seen)} ({time.time() - t0:.0f} s)", file=sys.stderr)
    return out


# ---------------------------------------------------------------- label with Jev
def _jev():
    sys.path.insert(0, os.path.join(REPO, "app", "spike"))
    import jev_spike
    return jev_spike


def label(workers=4):
    J = _jev()
    questions = dict(J.QUESTIONS, opt_out=OPT_OUT_Q)
    cands = [json.loads(l) for l in open(CAND, encoding="utf-8")]
    done = {}
    if os.path.exists(JEV):
        for l in open(JEV, encoding="utf-8"):
            d = json.loads(l)
            done[d["key"]] = d
    key = lambda t: hashlib.sha1(t.encode("utf-8")).hexdigest()
    todo = [c for c in cands if key(c["text"]) not in done]

    def one(c):
        body = {"model": J.MODEL, "state": {"agent_last_line": c.get("agent_last_line") or "", "seller_latest_turn": c["text"]},
                "questions": questions}
        for attempt in range(3):
            try:
                r = J.SESSION.post(J.URL, headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}, json=body, timeout=40)
                r.raise_for_status()
                a = r.json()["answers"]
                return {"key": key(c["text"]), "model": r.json().get("model"),
                        "scores": {k: round(a[k]["noul"], 3) for k in SIGNALS if k in a},
                        "language": a.get("language", {}).get("choice")}
            except Exception as e:  # noqa: BLE001
                err = type(e).__name__
                time.sleep(2 * (attempt + 1))
        return {"key": key(c["text"]), "error": err}
    with ThreadPoolExecutor(max_workers=workers) as ex, open(JEV, "a", encoding="utf-8") as f:
        for res in ex.map(one, todo):
            if "error" not in res:
                f.write(json.dumps(res) + "\n")
                done[res["key"]] = res
    errors = len([c for c in cands if key(c["text"]) not in done])
    print(f"label: {len(todo)} asked, {errors} failed", file=sys.stderr)
    return done


def primary(pos):
    return next((k for k in PRIORITY if k in pos), "neutral")


# ---------------------------------------------------------------- hand-made sentences
def hand_rows():
    sys.path.insert(0, os.path.join(REPO, "app", "spike"))
    import jev_spike
    import jev_devanagari
    rows = []
    sets = [("hand:jev_spike.CASES", jev_spike.CASES),
            ("hand:jev_devanagari.NATIVE", list(zip(jev_devanagari.NATIVE, [e for _, e in jev_spike.CASES]))),
            ("hand:jev_devanagari.EXTRA", jev_devanagari.EXTRA)]
    for src, cases in sets:
        for text, exp in cases:
            pos = [k for k in SIGNALS if exp.get(k) == 1]
            zeros = [k for k in SIGNALS if exp.get(k) == 0]
            if not pos and not zeros:
                continue  # language-only case: no switch label
            rows.append({"text": text, "label": primary(pos), "labels": pos, "source": src, "label_by": "hand",
                         "language": exp.get("language"), "partial": True})
    return rows


# ---------------------------------------------------------------- write
def write():
    J = {}
    if os.path.exists(JEV):
        for l in open(JEV, encoding="utf-8"):
            d = json.loads(l)
            J[d["key"]] = d
    rows = []
    for c in (json.loads(l) for l in open(CAND, encoding="utf-8")):
        d = J.get(hashlib.sha1(c["text"].encode("utf-8")).hexdigest())
        if not d:
            continue
        pos = [k for k in SIGNALS if (d["scores"].get(k) or 0) >= 0.5]
        rows.append({"text": c["text"], "label": primary(pos), "labels": pos, "source": "ps07_call_turns",
                     "label_by": f"jev:{d.get('model')} (unreviewed)", "scores": d["scores"], "language": d.get("language"),
                     "prefilter": c["prefilter"], "agent_last_line": c.get("agent_last_line")})
    rows += hand_rows()
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    counts = {"total": len(rows), "by_source": dict(Counter(r["source"] for r in rows)),
              "by_label": {s: dict(Counter(r["label"] for r in rows if r["source"] == s)) for s in sorted({r["source"] for r in rows})},
              "by_label_all": {k: sum(r["label"] == k for r in rows) for k in LABELS},
              "multi_label_rows": sum(len(r["labels"]) > 1 for r in rows),
              "ps07_prefilter_vs_jev": {b: dict(Counter(r["label"] for r in rows if r.get("prefilter") == b)) for b in QUOTA},
              "ps07_language": dict(Counter(r.get("language") for r in rows if r["source"] == "ps07_call_turns"))}
    with open(COUNTS, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=1)
    print(json.dumps(counts, indent=1))
    return rows, counts


def main():
    a = argparse.ArgumentParser()
    a.add_argument("step", choices=["sample", "label", "write", "all"])
    a.add_argument("--n", type=int, default=150)
    a.add_argument("--seed", type=int, default=7)
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if p.step in ("sample", "all"):
        sample(p.n, p.seed)
    if p.step in ("label", "all"):
        label()
    if p.step in ("write", "all"):
        write()


if __name__ == "__main__":
    main()
