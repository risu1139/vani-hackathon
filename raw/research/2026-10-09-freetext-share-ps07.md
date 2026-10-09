# Free-text facts in PS07 call history: share that would change a VANI persona or call-plan decision (2026-10-09)

Measured locally on the PS07 files in `data/` with Python regex and keyword rules. No LLM or API call touched the data. Aggregates only. Full notes: `outputs/research_notes/Agent decides VANI persona/freetext_share_ps07.md`.

**Setup.** There are 8 fact families: callback time, different contact, language, competitor/already-paid, specific need, complaint, personal constraint, and price detail. A fact counts only when the specific detail (time, person, language, competitor, need, amount) is in the text. A category label alone does not count. Sources are the call summary, the evaluator JSON (disposition reason/followup_when/alternate_*, objections, execdrop, seller_questions, incorrect_mf, se_contact) and seller transcript turns. "Due" seller = latest call in Aug–Sep with ≥1 earlier call (n = 35,794). Precision was estimated by manually reading about 40–60 random matches per family (text not saved).

## Results (PROVEN)
| Family | % calls (269,455) | % sellers (130,129) | % due sellers | est. precision |
|---|---|---|---|---|
| callback time | 6.45 | 11.44 | 18.76 | ~90% |
| different contact | 1.23 | 2.20 | 3.38 | ~85% |
| language | 0.11 | 0.21 | 0.26 | ~90% |
| competitor / already paid | 0.23 | 0.46 | 0.56 | ~75% |
| specific need | 0.20 | 0.37 | 0.51 | ~70% |
| complaint | 1.60 | 2.94 | 3.84 | ~88% |
| personal constraint | 5.40 | 9.63 | 13.99 | ~95% |
| price detail | 0.79 | 1.51 | 2.26 | ~93% |
| **any** | 13.24 | 21.43 | **30.76** (~28.8 adj.) | |
| durable (contact, language, competitor, need, complaint, price) | | 6.97 | **9.68** (~8.5 adj.) | |

- **Source.** Due sellers with a fact found via the summary: 20.9%; via evaluator JSON: 23.3%; via transcript: 3.3%. 9.9% have facts only outside the summary. Hit rate per call with the source present: summary 9.0%, evaluator 13.6%, transcript 21.3%.
- **Month.** % of calls with any fact: Apr 8.6, May 10.1, Jun 12.9, Jul 14.2, Aug 15.4, Sep 12.0. This tracks evaluator coverage (Aug 99%, Sep 64%) and transcript coverage (Jul–Aug only). The summary-only rate is flat at 8–10%. Sep relabelling: NI share fell from 51% to 19% and General rose from 24% to 55%.
- **Recency.** 49.5% of fact-holding due sellers have a fact in their last prior call. The rest have it only in older calls. Median age of the newest fact is 6.5 days (price 24 days, competitor 16.5 days).
- **Overlap.** 85% of callback-time calls and 77% of constraint calls are already labelled Call Later or `callback_requested`. The free text adds the *when* and *why*.
- **Conflict with structured data.** NI label on calls with a specific need: 38%; with another contact: 16%; with a constraint: 8%; with a callback time: 6%. 24% of language-fact sellers are in Hindi-belt states. Any conflict: 3.0% of due sellers (9.9% of those with a fact).

## Limits
Regex recall is unmeasured, so the shares are lower bounds. Evaluator coverage was only 12–22% in Apr–Jun. Transcripts cover about 9% of Jul–Aug calls. The due proxy includes many same-day callbacks (median gap 0 days).
