# Persona Design: does the data support it?

Sources: [[2026-10-07-persona-data-validation-run]] · [[2026-10-07-ps07-persona-data-dictionary]]

**Answer:** the data gives evidence for both halves of the brief. **Live adaptation has a real target**: 31% of transcribed calls show a mid-call signal, those calls have roughly half the meeting rate, and almost all signals appear *mid-call*. **Static script personalisation has failed internally** (three trials, none beat control). That's a risk note for the opening, not a reason to drop it: opening and personalisation are required deck items ([[persona-requirements]]). As of 2026-10-07.

## Script personalisation: 0 for 3

| test | result |
|---|---|
| `personalis` vs `base_vani`, concurrent, 30 Sep (452 vs 289 calls) | 14.8% vs 17.8% meeting-fixed (lead-type matched), p=0.13. But Not Interested 5.5% vs 13.1%: it keeps sellers talking without closing. |
| `last_met_d` vs `main_vani`, 16 Jun–14 Jul (23K vs 16K) | 11.1% vs 15.8%, lower on 22 of 23 paired days |
| `summary_va` vs `base_vani`, 30 Sep (91 calls) | 3.3% vs 18.4%, p<0.001 |

Implication: deliver the opening and personalisation fully (required), but don't claim they lift meetings. The `personalis` drop in Not Interested is the one positive: personalisation earns attention, and the close is what fails.

## Live signals: the target exists

Keyword heuristic on 11,834 transcribed calls (romanized Hinglish; a stand-in for [[jev]]):

| signal | % of calls | meeting-fixed present / absent | first seen mid-call |
|---|---|---|---|
| rush | 21.0 | 13.6 / 26.0 | 99% |
| interest | 16.8 | 22.5 / 23.6 | 80% |
| confusion | 6.5 | 20.0 / 23.7 | 68% |
| bot question | 4.0 | 22.6 / 23.5 | 70% |
| frustration | 3.6 | 12.8 / 23.8 | 96% |
| regional language | 2.3 | 31.4 / 23.2 | 90% |

- **Rush is the big one:** 1 in 5 calls, and the meeting rate halves. Natural switch: crisp-fast persona → offer a callback slot.
- Frustration is rare (3.6%) but also halves the rate.
- These are correlations, not proof that adapting helps. Causal evidence has to come from the demo or a simulation.

## Language fit

- **Tamil Nadu: 46.6% of calls carry Tamil markers**, yet the bot speaks Hinglish. A Gujarati-marker rate of only 2% understates Gujarat (51K calls, the second-largest state) because the lexicon is thin.
- Seller turns are romanized (0.2% Devanagari), so Jev input is romanized text.
- Persona must include **language choice from seller_state + live language-switch** (Sarvam's built-in Language Switch tool).

## Seller traits (pre-call persona inputs)

Meeting-fixed spread across groups: turnover 9.7 pts (0–40 L sellers convert best among known slabs), business type 7.1, nature of business 6.3, category group 3.8, state 3.3. Missing-profile sellers convert highest (~14–18%), likely newer sellers: a confound to control for.

## Caveats

- The transcript subset is biased: 23.4% meeting-fixed vs 11.5% overall.
- The keyword lexicon is crude. Replace with Jev labels (spike test 0) and re-run.
- Trial arms differ in lead-type mix; lead-type matching helps but can't rule out time-of-day effects.

## Next

- Re-run section 3 with Jev labels instead of keywords.
- Check `ps07_evaluator_outputs` (objections, latency_repetition) for what the bot *did* after each signal.
- Feeds the rule mining and per-seller memory in [[learning-loops]].
