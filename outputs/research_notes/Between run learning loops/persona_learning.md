# Persona generator learning between runs: per-seller memory + global rule updates (PS04)

As of 2026-10-08. Aggregates only; no seller names, messages or transcripts were copied. Tags: **PROVEN** = computed this session on local PS07 data (or our spikes); **DOCUMENTED** = published source; **ASSUMED** = our inference/design.

Binding context: [team decision](../../../raw/hackathon/2026-10-08-team-decision-between-run-learning.md) (nothing learns mid-call; LLM reviews after a run; corrections update switcher + generator; PS07 calls bootstrap both loops) · [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md) (persona per seller, FAQ Q1; reason + evidence strength per setting; Q5 delivery not facts; Q6 missing → default + lower confidence; scoring fit 25 / switches 25 / distinctness 20 / voice 15 / evidence 15) · [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md) · [system-design](../../../wiki/projects/vani-hackathon/system-design.md). Extends (does not redo) [generator_loop.md](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md) and [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md). Platform constraint: Sarvam voice/pace fixed per call → voice, pace, language start are **pre-call** choices; live switches change wording/brevity/tone/language only.

**Data runs this session** (scripts in session scratchpad: `memory_stats.py`, `memory_stats2.py`, `memory_stats3.py`; inputs `ps07_bot_calls_*.csv` (269,455 answered calls), `ps07_call_turns.csv` (seller turns only, 11,834 transcribed calls), `ps07_evaluator_outputs_*.csv` (objections, seller_questions, execdrop, disposition), `ps07_seller_files_part1/2.csv` (profile columns only)). Signals on transcripts use the same romanized keyword lexicon as [`app/validate/profile_persona.py`](../../../app/validate/profile_persona.py) (stand-in for Jev labels), plus two new proxies: `terse` (seller averages ≤3 words/turn) and `english_heavy` (≥50% of matched function words English). Cited below as **[MEM]**. Local data path: `data/Persona Files/Persona Files/` (git-ignored).

---

## Q1. Per-seller memory: how much can it help, what to store, decay, and mapping to the next persona

### Takeaway
Memory has a large, PROVEN base: 40.5% of sellers (52,757) have ≥2 answered calls and they hold 71% of all calls; the median gap between a seller's consecutive calls is ~1 day. The previous call predicts the next one far better than the profile does (next-call meeting AUC 0.71 memory vs 0.58 profile; next-call NI AUC 0.78 vs 0.54, time split). Outcome "state" decays back to baseline within ~45 days, while delivery "traits" (terse, rush, English-heavy) persist across gaps, so memory should store both, with recency decay on state and shrinkage (not decay) on traits. Signal-level evidence is thin (954 transcribed pairs), so signal memory starts MODERATE/WEAK.

### Cited Findings

**Volume and timing (PROVEN [MEM], 269,455 answered bot calls, Apr–Sep 2026)**
- 130,129 sellers. Calls per seller: 1 → 77,372; 2 → 24,232; 3 → 10,980; 4–5 → 9,451; 6–10 → 6,618; >10 → 1,476.
- **52,757 sellers (40.5%) have ≥2 answered calls; they account for 192,083 calls (71.3%)**. Median calls among repeat sellers 3, p90 7.
- 139,326 consecutive same-seller pairs. Gap between consecutive answered calls: p10 0.04 d, p25 0.52 d, **median 1.02 d**, p75 13.1 d, p90 38.3 d. Buckets: ≤1 d 44.8%, 1–3 d 17.7%, 3–7 d 5.2%, 7–14 d 8.7%, 14–30 d 9.1%, 30–60 d 10.0%, >60 d 4.5%.
- 87.4% of consecutive pairs used the same `lead_bot_version` (so "persona" barely varied between a seller's calls historically).
- Transcript history is thin: of 11,834 transcribed calls (10,880 sellers), only **842 sellers have ≥2 transcribed calls (954 pairs)**; median gap among those pairs 3.1 d.

**Outcome N → outcome N+1 (PROVEN [MEM]; row %)**

| previous call | n | next Not Interested | next General | next Call Later/Busy | next Meeting Fixed |
|---|---|---|---|---|---|
| first call (no history) | 130,129 | 41.1 | 24.2 | 17.2 | 17.5 |
| Not Interested | 57,440 | **67.1** | 16.6 | 11.9 | 4.4 |
| General (talked) | 44,415 | 19.6 | **65.9** | 10.8 | 3.7 |
| Call Later / Busy | 29,213 | 43.8 | 20.3 | 27.7 | 8.1 |
| Meeting Fixed | 8,258 | 34.5 | 25.8 | 17.9 | **21.7** |

- **Memory depth (two calls back adds information):** when the previous call was NI, the next-call meeting rate is 2.3% if the call before was also NI (n=26,950), 3.7% if General (n=4,483), 5.8% if Call Later (n=6,070), **9.5% if Meeting Fixed (n=1,686)**.
- Short-call persistence: P(next call ≤30 s | previous ≤30 s) = 78.0% (n=87,911) vs 55.6% otherwise; Spearman ρ of consecutive durations 0.31.
- Detailed-disposition recurrence (disposition evaluator, 74,308 pairs): `already_in_touch_with_im` 20.4% vs 1.7% base (n=2,514); `wrong_number` 24.0% vs 4.2% (n=2,575); `callback_requested` 22.9% vs 7.9% (n=11,862); `not_interested` 23.6% vs 8.5% (n=7,232); `call_dropped` 73.0% vs 47.7% (n=44,224).
- Who ended the call (execdrop, 1,584 pairs): seller hung up last time → seller hangs up again 15.0% vs 10.2% (n=167; small).

**Decay: recurrence by gap since the previous call (PROVEN [MEM])**
- NI → NI: ≤3 d **78.3%** (n=30,490); 4–14 d 65.5% (n=7,588); 15–45 d 54.7% (n=12,746); >45 d **41.3%** (n=6,616) ≈ first-call NI base 41.1%. The outcome "state" decays to baseline by ~45+ days.
- Meeting rate after NI rises with gap: ≤3 d 2.3%, 4–14 d 5.7%, 15–45 d 6.7%, >45 d 8.1%.
- Meeting Fixed → meeting again: 27.5% (≤3 d, n=171), ~21–22% at every longer gap (n=1,925–3,646): no decay visible.
- Rough fit (ASSUMED arithmetic on the NI excess over base: 37.2 pts at ~1.5 d → 13.6 pts at ~30 d): exponential τ ≈ 28 d, **half-life ≈ 20 days** for outcome state.

**Signal N → signal N+1 on transcribed pairs (PROVEN [MEM], 954 pairs; lexicon labels)**

| signal on call N | P(on N+1 \| on N) | P(on N+1 \| not on N) | lift | n with prior | 95% CI of difference (pts) |
|---|---|---|---|---|---|
| rush | 30.8% | 20.8% | 1.48× | 276 | [3.8, 16.2] |
| confusion | 25.0% | 7.0% | 3.57× | 68 | [7.6, 28.4] |
| frustration | 17.9% | 8.2% | 2.19× | 39 | [−2.4, 21.9] (n.s.) |
| bot-question | 22.9% | 3.5% | 6.56× | 35 | [5.4, 33.3] |
| interest | 29.2% | 17.3% | 1.69× | 185 | [4.8, 19.0] |
| terse (≤3 words/turn) | 41.0% | 17.8% | 2.31× | 183 | [15.6, 30.8] |
| English-heavy | 13.8% | 4.3% | 3.24× | 65 | [1.1, 18.1] |
| regional-language markers | 5.3% | 2.2% | 2.34× | 19 | [−7.1, 13.1] (n.s.) |

- Base rates per transcribed call: rush 21.0%, terse 26.4%, interest 16.8%, English-heavy 6.7%, confusion 6.5%, bot-question 4.0%, frustration 3.6%, regional markers 2.3%, Devanagari 0.2%.
- 35.6% of transcribed pairs carry a prior rush/confusion/frustration flag.
- **Traits vs states by gap:** rush recurs at every gap (≤3 d 28.2 vs 19.4; 4–30 d 35.9 vs 23.3; >30 d 25.0 vs 17.1); terse too (43.0 vs 15.1; 39.4 vs 19.4; 38.5 vs 24.3); English-heavy (15.6 vs 4.2; 14.3 vs 3.9). Confusion is strongest short-term (≤3 d 34.3 vs 7.7, n=35; 4–30 d 14.3 vs 5.5, n=28). All small n.
- Prior signal → next outcome: prior frustration → next meeting 5.1% vs 15.2% (n=39); prior bot-question 5.7% vs 15.1% (n=35); prior interest 16.8% vs 14.3% (n=185); prior rush 14.1% vs 15.0% (n=276; no outcome penalty).

**Objection / question type recurrence (PROVEN [MEM]; objections evaluator only 151 pairs, small)**
- Callback / Deferred Engagement: 45.2% next if present before (n=62) vs 11.2%.
- Explicit Disinterest / Refusal: 48.1% (n=27) vs 16.1%.
- Existing Engagement / Past Experience: 40.0% (n=20) vs 8.4%.
- Seller Unavailability & Scheduling: 37.3% (n=67) vs 22.6%.
- Identity-confirmation question: 35.0% (n=20) vs 19.0% (seller_questions, 78 pairs).

**Predictive value of memory vs profile (PROVEN [MEM]; logistic regression; train = pairs whose call N+1 is before 1 Aug, test = Aug–Sep; profile = business type, turnover, nature of business, state, GST year, #categories, CQS, hour; memory = previous disposition, gap bucket, disposition two calls back, previous short call / previous signals)**

| target (test n, prevalence) | profile only AUC | memory only AUC | profile + memory AUC | Brier base → best |
|---|---|---|---|---|
| next meeting (93,417; 5.8%) | 0.579 | 0.710 | 0.716 | 0.0547 → 0.0523 |
| next NI (93,417; 39.1%) | 0.540 | **0.776** | 0.733 | 0.2714 → 0.2255 |
| next rush, transcribed (684; 24.1%) | 0.510 | 0.566 | 0.551 | 0.1833 → 0.1832 |
| next terse, transcribed (684; 24.7%) | 0.525 | 0.619 | 0.616 | 0.1937 → 0.1822 |
| next any rush/confusion/frustration (684; 34.6%) | 0.500 | 0.570 | 0.517 | 0.2265 → 0.2248 |

- Caveats: unscaled features caused solver convergence warnings; profile+memory below memory-only on NI suggests overfit/drift, not that profile hurts. Signal targets have tiny train sets (270).
- Seller-file history columns (`past_objections`, `showed_frustration`, `past_dispositions_detailed`, `asked_if_talking_to_bot`) summarise **all of Apr–Sep**, so using them to "predict" a call inside that window leaks the future. Backtests must rebuild history from call-level files up to time t (PROVEN by the [data dictionary](../../../data/Persona%20Files/Persona%20Files/Seller-Fit%20Adaptive%20Voice%20Persona%20-%20Dataset%201%20of%203/PS07_DATA_DICTIONARY.md) definition "Bot call history (Apr–Sep)").

**Industry practice on what to store (DOCUMENTED)**
- SquadStack "Persistent Memory" (9 Jul 2026): lead-level context across calls; up to **20 extraction points per agent** (callback preferences/time slots, stated objections, last completed step, product interest, budget, sentiment and engagement); two modes: **Refresh** (replace with latest call) and **Rolling History** ("last few calls"); no outcome metrics published; identification via "masked fingerprint". — [SquadStack blog](https://www.squadstack.ai/blog/introducing-persistent-memory)
- Zep/Graphiti: when a new fact contradicts an old one, the edge gets an `invalid_at` timestamp instead of deletion (bi-temporal history). — [Zep, arXiv 2501.13956](https://arxiv.org/html/2501.13956v1)

### Inferences

**What to store after each call (ASSUMED schema; one JSON record per call, append-only, plus a derived per-seller summary)**
```json
{
  "seller_id": "glid",              // join key only; no name/number stored
  "call_id": "...", "ts": "2026-10-09T11:20:00+05:30", "source": "live|sim|ps07_replay",
  "persona_version": "gen-v3", "persona_settings": {"voice":"crisp_f","pace":1.1,"lang_start":"hinglish",
        "formality":"mid","warmth":"mid","opening":"time_boxed","playbook_order":["scheduling","callback"]},
  "signals": {"rush":{"seen":true,"first_turn":2,"src":"lexicon|jev|reviewer"},
              "confusion":{...}, "frustration":{...}, "interest":{...}, "bot_question":{...}},
  "language": {"seller_lang":"hi-Latn|en-heavy|gu|ta…","switched_to":"en","switch_turn":4},
  "brevity": {"seller_words_per_turn":2.6, "terse":true},
  "objections": ["callback_deferred"],          // category ids only, no quotes
  "outcome": {"disposition":"call_later","detailed":"callback_requested","who_ended":"seller","duration_s":41},
  "switches": [{"turn":3,"signal":"rush","change":"brevity→short","review":"correct|late|false|missed"}],
  "review": {"setting_fit": {"pace":"too_slow","formality":"ok"}, "what_worked":["time_boxed opening"],
             "reviewer":"llm|human", "agreed_with_human":true},
  "dnc": false
}
```
Derived per-seller summary (recomputed, never hand-edited): `last_outcome`, `last_gap_days`, `outcome_state_weight`, `trait_estimates` (rush/terse/english-heavy/confusion as Beta posteriors), `objection_queue`, `lang_pref`, `dnc`, `n_calls`, `confidence`.

**State vs trait, with decay (ASSUMED, sized from PROVEN decay)**
- **State** (last outcome, last objection, callback request, confusion): weight `w = exp(−gap_days / 28)` (half-life ≈ 20 d from the NI decay). After ~45–60 days fall back to profile defaults. Use the last 2 calls, not just 1 (prev2 changes next meeting 2.3% → 9.5% when prev = NI).
- **Trait** (rush, terse, English-heavy, bot-question): no time decay seen up to >30 d; use a per-seller Beta posterior shrunk to the segment rate: `p̂ = (k + α_seg) / (n + α_seg + β_seg)`, with `α_seg+β_seg ≈ 4–10` (ASSUMED) so one observed call moves the estimate partway, two consistent calls move it most of the way. This is the Beta-Binomial pattern in Q2 applied per seller.
- Newer evidence overrides: like Zep's `invalid_at`, a language switch on call N+1 supersedes the older `lang_pref` rather than averaging (the STALE result in Q4 shows models fail at implicit invalidation, so do this in code, not in the LLM).

**Mapping memory → next-call persona (ASSUMED directions; evidence tier of the *propensity* is PROVEN, the *helpfulness* of the delivery change is GUESS unless shown otherwise)**

| memory item | next-call setting (pre-call, because voice/pace are fixed per call) | reason template | evidence tier |
|---|---|---|---|
| prior rush or terse | pace 1.1, crisp voice, time-boxed opening ("2 minute"), playbook trimmed to top-1 | "rushed/terse on last call (N d ago); rush recurs 30.8% vs 20.8%, terse 41% vs 18%" | MODERATE (n=276/183) for recurrence; GUESS that pace helps |
| prior confusion (≤3 d) | pace 0.9, formality low/plain Hindi, one idea per sentence, confirm-understanding step | "confused last call; recurs 25% vs 7% (34% if ≤3 d)" | WEAK–MODERATE (n=68) |
| prior English-heavy speech | start English-leaning Hinglish voice/lang | "spoke mostly English last time; recurs 13.8% vs 4.3%" | WEAK (n=65) |
| prior regional-language switch | start in that language (voice chosen for it) | "switched to X last call" | WEAK (n=19); seller-file PNS language preferred |
| prior bot-question / `asked_if_talking_to_bot` | AI disclosure up front, warm-formal | "asked if bot; recurs 22.9% vs 3.5%; next meeting 5.7% vs 15.1%" | MODERATE (lift CI excludes 0, n=35) |
| last outcome NI (≤14 d) | re-engage plan: acknowledge last call, short, one value point, easy exit | "said not interested N d ago; NI repeats 78% within 3 d" | STRONG (n=30,490) |
| last outcome NI (>45 d) | treat ~like first call, keep acknowledgement | "NI recurrence back to base after 45 d (41.3%)" | STRONG (n=6,616) |
| last outcome Meeting Fixed | follow-up plan, warm, reference meeting | "21.7% meeting again vs 4.4% after NI" | STRONG (n=8,258) |
| last objection category | that category first in the playbook | "objected on X last time; recurs 37–48% vs 8–23%" | WEAK (n=20–67) |
| `already_in_touch_with_im` | acknowledge executive, don't repitch | "recurs 20.4% vs 1.7%" | STRONG (n=2,514) |
| DNC | hard gate, no call | compliance | fixed gate, never learned |
| no history | profile defaults, confidence LOW (FAQ Q6) | "first contact; live adaptation will correct" | — |

- Confidence per field = min(tier, recency weight, data completeness) (extends the generator_loop.md rule).
- **Strong argument for memory under the Sarvam constraint:** a mid-call switch can't change voice or pace, so a wrong pre-call voice/pace stays wrong for the whole call. Memory is the only lever that fixes it, on the *next* call. That ties the loop directly to PS04 §3.2 fit.

### Gaps
- Signal labels are a keyword lexicon (not Jev, not human); recurrence rates may shift with Jev labels. Frustration and regional-language recurrence are not significant at current n.
- The objections evaluator covers too few repeat pairs (151) for STRONG objection memory.
- Whether acting on memory improves outcomes is **unknown**: historic calls used one style (87.4% same bot version between a seller's calls), so the data shows *who will rush again*, not *that a faster pace helps them*.
- Decay half-life is fit on NI outcome only; signals have too few long-gap pairs to estimate their decay.

---

## Q2. Global rule updates from pooled reviewer findings

### Takeaway
Treat every generator rule as a (segment × setting) Beta-Binomial with an empirical-Bayes prior from PS07, update it with reviewer findings from each run, discount old evidence when the time split shows drift, and promote/demote tiers by posterior + n + time-split stability. Our data shows two traps this must handle: (1) **drift** — P(NI again | prev NI) was 75.8% Apr–Jul vs 63.4% Aug–Sep; (2) **no treatment variation** — PS07 never varied formality/pace, so historical data can't tell which *setting* works; that part can only come from reviewer findings on new runs and will stay WEAK/GUESS in 2 days.

### Cited Findings
- **Visible learning (PROVEN [MEM]; cumulative Beta(1+x, 1+n−x) 95% interval, by month):**
  - P(meeting | prev NI): Apr 2.7% [1.9, 3.7] n=1,315 → May 2.1% [1.7, 2.5] n=6,174 → Jun 3.5% [3.1, 3.9] n=8,460 → Jul 4.5% [4.2, 4.8] n=17,183 → Aug 4.1% [3.9, 4.3] n=44,342 → Sep 4.4% [4.2, 4.6] n=57,440. Time split 4.5% vs 4.4% → **stable; STRONG**. Note the April interval excludes the final value: early data was biased, not just noisy.
  - P(meeting | prev Meeting Fixed): Apr 31.6% [21.0, 44.5] n=57 → Sep 21.7% [20.8, 22.6] n=8,258; time split 17.5% vs 24.2% → direction stable, magnitude drifts.
  - P(NI again | prev NI): Apr 78.9% → Aug 75.2% → Sep cumulative 67.1%; time split **75.8% vs 63.4%** → direction holds (≫ 41.1% base) but the level drifts by 12 pts.
- Empirical-Bayes Beta-Binomial: learn the prior from all groups (method of moments) and shrink each group's rate toward the pooled mean, more for small n; example: 95 impressions at 14.74% raw shrinks to 10.86%; typically 20–50% lower MSE than raw rates. — [MetricGate empirical Bayes](https://metricgate.com/docs/empirical-bayes/); [Skeptric, pooling proportions](https://skeptric.com/pooling-proportions-empirical-bayes/)
- Shrinkage estimators are used in online experiments to reduce error across many simultaneous treatment-effect estimates. — [Dimmery et al., arXiv 1904.12918](https://arxiv.org/pdf/1904.12918)
- Earlier in-repo design: keep a rule only if n ≥ 200, bootstrap CI excludes 0, holds on time split; tiers STRONG (n ≥ 2,000 + time split + survives reweighting by bucket/version) / MODERATE (n ≥ 200 + holds) / WEAK (n < 200 or literature only) / GUESS (no data). — [generator_loop.md Q2](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md); [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)
- Cekura's automated loop "diagnoses failing scenarios by class, applies targeted prompt or config edits, redeploys, scans for prompt overfitting, and iterates" (vendor description). — [Cekura](https://cekura.ai/blogs/self-improving-voice-agents-closing-eval-loop) via search snippet

### Inferences

**From reviewer finding to rule change (ASSUMED pipeline)**
1. **Finding record** (from the post-call reviewer B10): `{segment features, setting, level, finding ∈ {fit, misfit:<kind>}, signal_outcome}` e.g. `{turnover:<40L, gst_age:0–2, formality:high, misfit:"confused"}`.
2. **Pool** by (rule key = segment bucket × setting × level). Count `k` = misfit findings, `n` = calls reviewed at that key. Segment buckets come from the explainable "types" (allowed by FAQ Q1 for explanation), kept coarse (≤ ~30 keys per setting) so counts accumulate.
3. **Prior**: Beta(α0, β0) fitted by method of moments across all keys for that setting (empirical Bayes). For settings never varied historically (formality, pace, voice), the prior is weak (α0+β0 ≈ 2–5) → **these are the rules runs can visibly move**. For outcome/propensity rules mined from 269K calls, the prior is huge and a few dozen hackathon runs will not move them (honest).
4. **Posterior**: Beta(α0+k, β0+n−k). Compare level A vs level B in the same segment: P(misfit_A > misfit_B) by Monte Carlo (10K draws, milliseconds).
5. **Reviewer-noise correction**: calibrate the LLM reviewer on 30–50 human-labelled calls; if sensitivity Se and specificity Sp are known, correct the observed rate with the standard misclassification (Rogan–Gladen) adjustment `p = (p_obs + Sp − 1)/(Se + Sp − 1)` (ASSUMED method choice; not sourced here). If κ < 0.6 (Q3), findings may *only* lower confidence, never change a rule.
6. **Drift handling**: discount old counts with a forgetting factor per month (power-prior style), e.g. λ = 0.8/month (ASSUMED), justified by the PROVEN 12-pt drift on NI recurrence.
7. **Change rule** only if: posterior P(effect in claimed direction) ≥ 0.95, effective n ≥ 200 (MODERATE) / ≥ 2,000 (STRONG), and it holds on the time split (mine on earlier runs/months, check on later ones). Ship via the gate in [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md): frozen test set must not regress.

**Tier ladder (ASSUMED; the "visible learning" artefact)**

| tier | condition | example today |
|---|---|---|
| GUESS | no data; design prior only | "confused sellers prefer lower formality"; voice gender |
| WEAK | n < 200 or CI includes 0 or literature only | prior frustration recurs (n=39, CI incl. 0); objection-type memory |
| MODERATE | n ≥ 200, P ≥ 0.95, holds on time split | prior rush recurs (n=276, CI [3.8, 16.2]) |
| STRONG | n ≥ 2,000, holds on time split, stable level, survives reweighting | P(meeting \| prev NI) 4.5% vs 4.4% |
| DEMOTED | direction holds but level drifts > X pts across split | P(NI again \| prev NI) 75.8 → 63.4 (flag "drifting", widen interval) |

- **Upgrade story to show judges:** a rule card with its Beta interval at run 0 (PS07 prior), after PS07 replay batch, after Day-1 runs, after Day-2 runs; tier badge changes (e.g., "pace 0.9 for prior-confused" GUESS → WEAK as reviewed runs accumulate). Plot the interval narrowing, like the monthly series above.
- **Support thresholds sized to hackathon volume:** with ~30–60 reviewed live/sim runs in 2 days, only rules with weak priors and large effects (≥20 pts) can reach WEAK→MODERATE; most new-setting rules will end as WEAK. Say so on the slide.
- **Guard:** rules can never touch the DNC gate, AI disclosure, facts/prices (FAQ Q5).

### Gaps
- No public source found that applies Beta-Binomial rule tiering specifically to voice-agent persona rules; the pipeline is our design.
- Reviewer sensitivity/specificity per finding type is unmeasured.
- Forgetting factor and prior strength values are unsized guesses.

---

## Q3. Evaluating persona improvement between versions without counterfactual outcomes

### Takeaway
We can't measure "persona v2 gets more meetings than v1" from logged data: PS07 has one delivery style (no overlap), so off-policy estimators are undefined. What we *can* show: (1) **predictive validity** — the persona's declared expected signals vs the seller's actual next call (memory already lifts AUC from ~0.51–0.58 to ~0.57–0.78); (2) **spec fit** by an LLM judge calibrated against a small human set (κ ≥ 0.6); (3) deterministic checks; (4) small paired simulated A/B on switches only.

### Cited Findings
- OPE needs overlap/positivity: the logging policy must have positive probability for every action the target policy takes; inverse-propensity weights explode as overlap shrinks, and violations preclude IPS and doubly-robust methods. — [DOLCE, arXiv 2505.00961](https://arxiv.org/html/2505.00961v3); [Off-Policy Evaluation from Logged Human Feedback, arXiv 2406.10030](https://arxiv.org/pdf/2406.10030); [UW CSE599m notes](https://courses.cs.washington.edu/courses/cse599m/19sp/notes/off_policy.pdf)
- PS07 historically: "VANI talks to every seller in one voice and one style" — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md); 87.4% of a seller's consecutive calls used the same bot version and bot-version assignment is non-random (97% of Tamil Nadu on `arrowhead`) (PROVEN [MEM]; [generator_loop.md](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md)).
- Predictive-validity numbers in Q1 table (PROVEN [MEM]).
- LLM-judge calibration: use Cohen's κ, not % agreement; build a calibration set labelled by humans with the judge's rubric; reported practice: κ > 0.6 acceptable, > 0.8 strong, < ~0.6 too noisy to gate decisions (secondary/practitioner sources). — [Koji docs](https://www.koji.so/docs/llm-as-a-judge-vs-human-evaluation); [Tian Pan blog](https://tianpan.co/blog/2026-04-28-llm-judge-ceiling-auto-eval-human-correlation)
- Judges with high % agreement can still assign very different scores; verified references improve agreement and mitigate self-preference. — [Judging the Judges, arXiv 2406.12624](https://arxiv.org/abs/2406.12624v1); "No Free Labels" review via [themoonlight.io](https://www.themoonlight.io/en/review/no-free-labels-limitations-of-llm-as-a-judge-without-human-grounding)
- Small-sample limit: κ ±0.26 at n=30; only ~20-pt gains distinguishable with ~25–30 positives per signal. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences (ASSUMED)
- **Predictive validity as the headline metric for "the generator learned".** Each spec declares `expected: {rush: 0.31, confusion: 0.07, english_heavy: 0.04, NI: 0.67, …}` from memory + rules. Score AUC/Brier on held-out sellers' *next real call* (time split). v0 (profile only) vs v1 (profile + memory) vs v2 (+ rule updates). Today's PROVEN baseline: meeting AUC 0.58 → 0.71, NI 0.54 → 0.78, terse 0.53 → 0.62. It is unhackable by verbosity and grounded in real outcomes, but it measures *understanding the seller*, not *better delivery*. Say exactly that.
- **Fit judge**: different model family from generator; rubric per setting ("is it justified by this seller's data/memory?"); 30–50 specs double-labelled by a teammate; report κ; if κ < 0.6 fix the judge.
- **Reviewer-defined misfit rate on replayed calls**: for PS07 replay, generate the persona the generator *would* have produced from history before the call, then ask the reviewer whether the seller's real behaviour on that call contradicts it (e.g., spec said "patient, long pitch" but seller was terse in turn 2). This is "expectation mismatch rate", a fit proxy — still not causal.
- **Where real A/B is possible**: simulated sellers with paired ON/OFF (B7 harness), for switch timing only; simulators under-express resistance (disengagement deficit, see generator_loop.md), so don't use them for generator outcome claims.
- **Never claim**: "persona v2 increases meetings by X%".

### Gaps
- No calibration set exists yet; κ unknown.
- Predictive validity for signals uses only 954 transcribed pairs (test 684), so CIs on AUC are wide (unquantified here).

---

## Q4. Precedent for cross-session customer memory in voice/sales agents, and pitfalls

### Takeaway
Memory layers (Mem0, Zep, Letta) are mature for *recall* and production sales-voice vendors (SquadStack) now ship per-lead cross-call memory, but none publish outcome lift from it. The documented failure modes — stale memories (best model 55.2% on STALE), over-personalisation/sycophancy to remembered preferences, and cross-context leakage — all argue for **structured, typed, decaying memory written by code**, with LLMs used only to extract.

### Cited Findings
- **Mem0** (arXiv 2504.19413, Apr 2025): extracts, consolidates and retrieves salient facts; on LOCOMO, 26% relative improvement on LLM-as-judge vs OpenAI memory; graph variant ~2% higher; 91% lower p95 latency and >90% token savings vs full context. LOCOMO = 10 conversations of ~600 dialogues/26K tokens. Vendor-authored. — [arXiv 2504.19413](https://arxiv.org/abs/2504.19413)
- **Zep** (arXiv 2501.13956, Jan 2025): temporal knowledge graph (Graphiti) with episodic/semantic/community subgraphs; contradicting facts get `invalid_at`; DMR 94.8% vs MemGPT 93.4%; LongMemEval up to +18.5% accuracy, −90% latency. Vendor-authored. — [arXiv 2501.13956](https://arxiv.org/html/2501.13956v1)
- **Letta (MemGPT)**: editable memory blocks; a separate "sleep-time" agent consolidates memory asynchronously while the primary agent is idle. — [Letta blog](https://letta.com/blog/sleep-time-compute). This matches our "review after the run, not during" decision.
- **SquadStack Persistent Memory** (Jul 2026): lead-level cross-call memory for voice sales agents, up to 20 extraction points (objections, callback slots, sentiment), Refresh vs Rolling History modes; no metrics; little detail on retention/deletion. — [SquadStack](https://www.squadstack.ai/blog/introducing-persistent-memory); also "CRM-aware from the first second" per [SquadStack sales page](https://www.squadstack.ai/voicebot/ai-voice-agent-for-sales-automation) (search snippet).
- **Coval / Cekura** (eval, not memory): Coval runs thousands of simulations, regression tests on prompt/model changes, and production evals ([TechCrunch](https://techcrunch.com/2025/01/23/coval-evaluates-ai-voice-and-chat-agents-like-self-driving-cars); [Coval](https://www.coval.ai/)); Cekura generates test cases (impatience, one-word answers, broken English), LLM-judge + Python metrics, reviewer annotation with "Auto Improve" and a scenario-suite gate ([Cekura](https://www.cekura.ai/blogs/voice-ai-evals)). Both are outside vendors → reference only, not usable (AGENTS.md).
- **Stale memory**: STALE benchmark (May 2026): "Implicit Conflict" (later observation invalidates an earlier memory without explicit negation); best model **55.2%** across 1,200 queries; models accept outdated premises and fail to propagate a change to related memories. — [arXiv 2605.06527](https://arxiv.org/abs/2605.06527)
- **Over-personalisation**: persistent memories can leak sensitive details across unrelated contexts or make models "defer sycophantically to remembered preferences"; structured memory partitions cut cross-domain leakage ~8% on PersistBench across 7 models. — [ICML 2026](https://icml.cc/virtual/2026/67886)
- Irrational personalisation: semantic similarity activates irrelevant preferences that conflict with current needs (RPEval). — [arXiv 2601.16621](https://arxiv.org/abs/2601.16621v1)
- PerMemBench: static memory policies waste budget on transient sessions; propose session-level storage gating. — [benchmarklist](https://benchmarklist.com/benchmarks/permembench/) (search snippet only)
- **Privacy (India)**: DPDP Rules 2025 notified 14 Nov 2025; erase personal data when purpose is no longer served or consent withdrawn; processing logs kept ≥1 year; retention/erasure provisions in force 13 May 2027. — [SCC Online](https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/); [Mondaq](https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified)

### Inferences (ASSUMED)
- **Use the pattern, not the product.** Building on Mem0/Zep/Letta would be a new outside dependency and arguably "pre-built" for the core; a typed JSON/DuckDB record (Q1 schema) written by our code covers what we need and is explainable. Cite them as precedent on the slide.
- **Stale-memory guard in code**: recency weight + supersede-on-conflict (language, DNC, already-in-touch) + hard expiry of state after ~60 d. Don't ask the LLM to decide whether a memory is stale (STALE 55.2%).
- **Over-personalisation guard**: memory changes delivery only (FAQ Q5); cap memory's effect so one call can't flip every setting (trait shrinkage); never quote the seller's past words back (privacy + creepiness); "I remember you said X" only for explicit callback/scheduling facts.
- **Self-fulfilling loop risk**: if memory says "NI → short, easy exit", the next call is designed to end quickly, NI recurs, memory "confirms" it. Mitigate with a small exploration share in sims, and by reporting it as a limitation.
- **Privacy**: store category ids and numeric features only, keyed by GLID, in git-ignored `data/`; reviewer runs on Sarvam LLM / internal gateway; DNC is a permanent gate.

### Gaps
- No public outcome lift numbers for cross-call memory in voice sales agents (SquadStack published none).
- Mem0/Zep numbers are vendor-authored benchmarks on chat QA, not voice sales.

---

## Q5. Devil's advocate: scope, 2-day feasibility, and the single highest-value piece

### Takeaway
PS04 scores fit, switches, distinctness, voice and evidence; it never scores "learning across runs". Per-seller memory earns points only because it makes each persona fit its seller better with data-backed reasons, and its evidence is the strongest we have. The global Bayesian rule loop is worth one slide (tier badges + interval narrowing), not hours. The single highest-value piece is **memory-driven pre-call settings with reasons + evidence tiers, shown as a "same seller, call 1 → review → call 2" persona diff**.

### Cited Findings
- Scoring weights and deliverables: fit 25, switches 25, distinctness 20, natural voice 15, evidence 15; deliverables are generator code, spec per seller with reasons, live demo with ≥1 switch, switch log, one slide. No criterion mentions cross-run improvement. — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Data shows prior call outcome is the strongest predictor (AUC 0.71–0.78 vs profile 0.54–0.58) (PROVEN [MEM]); prior previous-disposition carries 0.74–0.85 of tree importance (PROVEN, [generator_loop.md](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md)).
- Budget: core deliverables ≈ 20–30 dev-hours vs ~18–24 usable; cap loop work at ~6 h. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences (ASSUMED)

**Out of PS04 scope (flag, don't build)**
- Proving outcome lift (meetings) from new personas: impossible without live traffic or overlap.
- Online bandits / Thompson sampling on persona options; fine-tuning.
- A general memory layer (graph DB, Mem0/Zep/Letta clone).
- Memory for anything beyond delivery (pricing, offers): forbidden by FAQ Q5.

**Can't be shown in 2 days**
- Rules for never-varied settings (pace, formality, voice) reaching MODERATE/STRONG: at most a few dozen reviewed runs; they stay WEAK/GUESS. Show them honestly as GUESS → WEAK.
- Decay of signal memory (too few long-gap transcribed pairs).
- Reviewer accuracy beyond κ at n≈30 (±0.26).

**What is cheap and shows well**
- Memory store + derived summary from PS07 call-level files (rebuild history as of time t to avoid leakage) — ~1–2 h.
- 6–8 memory→setting rules with PROVEN propensity stats and tiers (Q1 table) — reuses the rule layer.
- Predictive-validity number (v0 profile-only vs v1 + memory, time split): one chart.
- Rule cards with Beta intervals by month (already computed above for 3 rules).

**Single piece that earns the most points:** per-seller memory → pre-call persona settings with a reason and evidence tier on every field. It feeds fit (25: persona follows what this seller actually did), evidence (15: PROVEN recurrence and transition stats with n and tier), distinctness (20: two sellers with identical profiles but different histories get audibly different voice/pace/opening, a per-seller difference no fixed library can produce, FAQ Q1), and it is the only fix for voice/pace mistakes, since those can't change mid-call. Demo: call seller A (simulated, rushes + switches to English) → reviewer writes memory → regenerate → call 2 starts crisp, English-leaning, time-boxed opening, with the diff and reasons on screen.

### Gaps
- Organisers' sample-seller set and whether they will accept a "second call" demo framing are unknown; ask on Day 1.
- Whether judges value the cross-run loop at all is unknown; weights are "indicative".
