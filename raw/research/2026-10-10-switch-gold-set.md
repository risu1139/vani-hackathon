# Switch gold set: aggregate counts (2026-10-10)

**Why.** Adversarial review finding M17 asks for a held-out gold set for the mid-call switcher, made from real PS07 seller turns plus the hand-made sentences, so the lexicon and Jev can be scored on real data, not simulated data.

**Method.** Script: `app/persona/build_gold.py`. The text stays only in git-ignored `data/gold/switch_gold.jsonl`. This note holds counts only. No seller text, names or ids.
1. **Sample.** One pass over `data/index/sellers.sqlite` (source `ps07_call_turns`, speaker = seller, 2–40 words). Each turn goes into a bucket by keyword pre-filter (romanised + Devanagari cues). A reservoir sample is drawn per bucket (seed 7). Quotas: 20 each for opt_out, bot_question, frustrated, confused, rushed, interested; 30 for neutral. Total 150. The bot line just before each turn is kept as context. Phones and emails are masked.
2. **Label.** One Jev call per turn (OpenRouter Decisions API, `typesafe/jev-1.13-20260917`). It asks the 6 questions of `app/spike/jev_spike.py` plus a new `opt_out` question ("asks to stop calling / remove number"). Threshold is 0.5. The primary label is the first positive signal in this order: opt_out > bot_question > frustrated > confused > rushed > interested. If none is positive, the label is neutral. 150 calls, 0 failures.
3. **Hand-made.** 63 sentences labelled by hand: the 29 romanised `CASES` of `jev_spike.py` with a switch label (the language-only case is skipped), the same 29 in native script (`jev_devanagari.NATIVE`), and 5 tricky `EXTRA` cases. These labels are partial: each sentence was written for one or two signals.

## Counts

| Label | PS07 turns (Jev) | Hand-made | Total |
|---|---|---|---|
| opt_out | 18 | 0 | 18 |
| bot_question | 16 | 6 | 22 |
| frustrated | 23 | 9 | 32 |
| confused | 9 | 9 | 18 |
| rushed | 26 | 15 | 41 |
| interested | 24 | 9 | 33 |
| neutral | 34 | 15 | 49 |
| **Total** | **150** | **63** | **213** |

- 36 rows have more than one positive signal (for example, rushed + opt_out).
- Language of the PS07 turns (Jev): hinglish 103, hindi 43, english 2, tamil 1, unclear 1. These are ASR text, mostly romanised Hindi.
- Seller turns seen per pre-filter bucket in the full scan: neutral 41,302; interested 4,230; rushed 2,959; confused 760; bot_question 404; opt_out 222; frustrated 106. The rare signals are well under 1% of turns, which is why the sample oversamples them.

## Pre-filter vs Jev label (PS07 turns, 20–30 per bucket)

| Pre-filter bucket | Jev agrees | Jev says otherwise |
|---|---|---|
| opt_out (20) | 14 | rushed 4, frustrated 1, neutral 1 |
| bot_question (20) | 16 | interested 2, rushed 1, neutral 1 |
| frustrated (20) | 16 | opt_out 3, interested 1 |
| confused (20) | 7 | neutral 5, interested 5, opt_out 1, frustrated 1, rushed 1 |
| rushed (20) | 14 | neutral 5, interested 1 |
| interested (20) | 8 | neutral 7, rushed 3, frustrated 2 |
| neutral (30) | 15 | interested 7, rushed 3, frustrated 3, confused 2 |

Keyword cues are weakest for **confused** (7/20) and **interested** (8/20). Half of the "neutral" bucket shows a signal by Jev's reading. This matches the 2026-10-09 finding that the lexicon misses romanised interest cues.

## Caveats
- The PS07 labels are **Jev's, not yet human-checked**. `label_by` says "(unreviewed)". Before the gold set is used to score Jev itself, a human spot check of at least the rare labels is needed. Otherwise Jev would be scored against its own labels.
- Keep the set held out from lexicon tuning (M17).
- Only 9 PS07 turns came out confused, so confusion stays thin. The next draw should take more from the confused bucket.
