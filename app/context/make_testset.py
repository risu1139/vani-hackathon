"""Pick the 100-GLID test set and copy their rows from every offline file.

Strata (seeded, reproducible), drawn from the coverage index (seller_inventory.py build):
  rich    45  GC sellers with >= 4 of 8 rich sources
  medium  25  GC sellers with 2-3 rich sources
  sparse  15  GC sellers with 0-1 rich sources (but at least one answered VANI call)
  cold    10  GC sellers with no answered VANI call
  onboard  5  PS07 sellers that also appear in Seller Onboarding (designation, products)
Output (git-ignored): data/testset/glids.csv and one CSV per source with only these sellers.

Run: python app/context/make_testset.py [--n-seed 42]
"""
import argparse
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from seller_inventory import INDEX, ROOT, SOURCES, glid_of, rows  # noqa: E402

OUT = os.path.join(ROOT, "testset")
RICH = ["gc_enquiries", "gc_buyer_calls", "gc_whatsapp_chatbot", "gc_buyer_call_extractions", "ps07_call_turns",
        "ps07_evaluator", "gc_buyleads_bought", "gc_enquiry_messages"]
# one output file per physical source (filters like "unanswered" are derived later, not copied twice)
FILES = {
    "ps07_seller_file": "ps07/ps07_seller_files_part*.csv",
    "ps07_bot_calls": "ps07/ps07_bot_calls_*.csv",
    "ps07_call_turns": "ps07/ps07_call_turns.csv",
    "ps07_evaluator": "ps07/ps07_evaluator_outputs_*.csv",
    "ps07_recording_sample": "ps07/ps07_recording_sample_5000.csv",
    "ps07_exec_calls": "ps07/ps07_executive_calls.csv",
    "btc_seller": "best_time_to_call/Best-Time-to-Call - Sellers.csv",
    "btc_attempts": "best_time_to_call/Best-Time-to-Call - Call Attempts Apr-Sep 2026.csv",
    "leap_call_logs": "aids/Call_Logs_Hackathon.csv",
}
KEYS = {name: key for name, _, key, _, _ in SOURCES}
for name, pattern, key, _, _ in SOURCES:
    if name.startswith(("gc_", "so_")):
        FILES[name] = pattern


def pick(seed):
    with open(INDEX, encoding="utf-8", newline="") as f:
        idx = list(csv.DictReader(f))
    rnd = random.Random(seed)
    gc = [r for r in idx if int(r["gc_profile"])]
    rich = lambda r: sum(int(r[k]) > 0 for k in RICH)
    called = lambda r: int(r["ps07_bot_calls"]) > 0
    strata = {
        "rich": [r for r in gc if called(r) and rich(r) >= 4],
        "medium": [r for r in gc if called(r) and 2 <= rich(r) <= 3],
        "sparse": [r for r in gc if called(r) and rich(r) <= 1],
        "cold": [r for r in gc if not called(r)],
        "onboard": [r for r in idx if int(r["so_seller"]) and int(r["ps07_seller_file"])],
    }
    want = {"rich": 45, "medium": 25, "sparse": 15, "cold": 10, "onboard": 5}
    chosen = []
    for s, n in want.items():
        pool = sorted(strata[s], key=lambda r: r["glid"])
        for r in rnd.sample(pool, min(n, len(pool))):
            chosen.append((r["glid"], s, rich(r)))
    return chosen


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--seed", type=int, default=42)
    p = a.parse_args()
    os.makedirs(OUT, exist_ok=True)
    chosen = pick(p.seed)
    ids = {g for g, _, _ in chosen}
    with open(os.path.join(OUT, "glids.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["glid", "stratum", "rich_sources_of_8"])
        w.writerows(chosen)
    keymap = {"ps07_seller_file": "fk_glusr_usr_id", "ps07_bot_calls": "fk_glusr_usr_id",
              "ps07_call_turns": "fk_glusr_usr_id", "ps07_evaluator": "fk_glusr_usr_id",
              "ps07_recording_sample": "fk_glusr_usr_id", "ps07_exec_calls": "fk_glusr_usr_id",
              "btc_seller": "fk_glusr_usr_id", "btc_attempts": "fk_glusr_usr_id", "leap_call_logs": "fk_glusr_usr_id"}
    keymap.update({k: v for k, v in KEYS.items() if k.startswith(("gc_", "so_"))})
    for name, pattern in FILES.items():
        key, n, writer, fh = keymap[name], 0, None, None
        for r in rows(pattern):
            if glid_of(r.get(key)) not in ids:
                continue
            if writer is None:
                fh = open(os.path.join(OUT, f"{name}.csv"), "w", newline="", encoding="utf-8")
                writer = csv.DictWriter(fh, fieldnames=list(r.keys()))
                writer.writeheader()
            writer.writerow(r)
            n += 1
        if fh:
            fh.close()
        print(f"{name:28} {n:7} rows", file=sys.stderr)
    from collections import Counter
    print(f"test set: {len(chosen)} sellers {dict(Counter(s for _, s, _ in chosen))} → {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
