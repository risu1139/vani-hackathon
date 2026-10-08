# Self-improving per-seller persona generator: architecture and improvement loop (PS04)

As of 2026-10-08. Aggregates only; no seller names, messages or transcripts. Tags: **PROVEN** = our data or spikes; **DOCUMENTED** = published source; **ASSUMED** = our inference.

Binding requirements are taken from [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md) and [persona-requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md):
- a persona **per seller**; FAQ Q1 allows no fixed library;
- a reason for every setting, tied to seller data;
- evidence strength stated;
- missing fields fall back to defaults with lower confidence (Q6);
- delivery changes, never facts, prices or compliance (Q5);
- scoring is fit 25 / switches 25 / distinctness 20 / voice in 2+ languages 15 / evidence 15;
- all build work happens in the 2 days, and pre-built solutions are disqualified.

Internal data pointers:
- **[PB]**: [persona_block.md](../VANI%20problem%20choice%20and%20system%20design/persona_block.md), the prior aggregate analysis.
- **[L30]**: [last30days self-improving loops](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md).
- **[ARMS]**: a new aggregate run this session (`arms.py` in the session scratchpad) over `ps07_bot_calls_*.csv`.

---

## Q1. GEPA and DSPy optimizers: how they work, inputs, cost, gains, failure modes, OpenRouter, licence

### Takeaway
GEPA is the right tool for the **LLM-written part** of the generator. That part is the instructions that turn seller features plus mined rules into opening, playbook and reason text. GEPA:
- learns from natural-language feedback;
- needs only about 20–100 examples and roughly 100–500 metric calls;
- is MIT-licensed;
- reaches any LiteLLM model, which includes OpenRouter.

Its documented failure modes are overfitting small train sets and prompt bloat, so a held-out set and a length cap are mandatory.

### Cited Findings
**Mechanism (DOCUMENTED)**
- GEPA samples trajectories and **reflects on them in natural language** to diagnose problems, then proposes and tests prompt updates. It combines complementary lessons from the **Pareto frontier** of its own attempts. — [GEPA paper, arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
- Pareto selection keeps candidates that are "achieving the highest score on at least one evaluation instance", rather than only the global best. — [DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)

**Reported gains (DOCUMENTED, author-reported)**
- About 6% average over GRPO, up to 20% on some tasks, with up to 35× fewer rollouts.
- More than 10% over MIPROv2, including +12% on AIME-2025. — [arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
- Benchmarks: HotpotQA, IFBench, HoVer, PUPA, AIME-2025, LiveBench-Math. Models: Qwen3-8B and GPT-4.1-mini.
- Qwen3-8B budgets were 1,839–7,051 rollouts per task, vs GRPO's 24,000. IFBench reached its best prompt after 678 rollouts.
- "The majority of GEPA's rollout budget is spent on validation."
- GEPA prompts are up to 9.2× shorter than MIPROv2's.
- Merge (crossover) gave +2% on GPT-4.1-mini but **degraded Qwen3-8B**. — [arXiv 2507.19457 HTML](https://arxiv.org/html/2507.19457)

**Inputs and API (DOCUMENTED)**
- Inputs: a seed candidate (text), a trainset and valset, a metric, a `reflection_lm`, and a `max_metric_calls` budget ("typically 100–500 evaluations"). — [gepa-ai/gepa README](https://github.com/gepa-ai/gepa)
- `optimize_anything` extends GEPA to code and configs. — [gepa-ai/gepa README](https://github.com/gepa-ai/gepa)
- **MIT licence**; `pip install gepa`. — [gepa-ai/gepa README](https://github.com/gepa-ai/gepa)
- **Models via LiteLLM**, which covers OpenRouter, OpenAI, Anthropic and others. — [gepa-ai/gepa README](https://github.com/gepa-ai/gepa)
- DSPy's metric signature is `(gold, pred, trace, pred_name, pred_trace)`. It returns a float or `dspy.Prediction(score, feedback)`. Feedback should explain *why* a case succeeded or failed, and decomposing scores into sub-objectives helps. — [DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)
- DSPy GEPA settings:
  - budget: `auto` light/medium/heavy, or `max_metric_calls` / `max_full_evals`;
  - `reflection_minibatch_size` default 3;
  - `candidate_selection_strategy` "pareto" or "current_best";
  - `use_merge` default True;
  - `track_stats` exposes lineage and per-instance scores.
  — [DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)
- "If only trainset supplied, GEPA overfits to it." — [DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)

**Failure modes from production (DOCUMENTED)**
- Unconstrained prompts grew past 5,000 characters. Going from 50 to 500 samples made the prompt length "balloon by 75% while performance decreased". **20–100 examples beat 500.**
- A 1,500-character cap during reflection gave 4× compression at a 0.8% performance cost.
- Small reflection models "fail completely", so a frontier reflection LM is required. Reflection is only 5–10% of total cost.
— [Decagon, Optimizing GEPA for production](https://decagon.ai/blog/optimizing-gepa-for-production)

Search-snippet findings, not opened in full:
- One case saw train accuracy rise 90→95% while held-out accuracy fell 95→85% (gpt-4.1-nano, 30 questions).
- Another saw an optimised prompt score 34.0% against the seed's 62.4% on a small train set.
— [GEPA overfitting search results: Datasette/DSPy news](https://letsdatascience.com/news/dspy-evaluates-and-refines-datasette-agent-prompts-6ced2073), [MAGE arXiv 2607.11944](https://arxiv.org/pdf/2607.11944)

**Other evidence**
- Practitioners say GEPA works "in narrow ways, against specific metrics" (DOCUMENTED, via [L30]).
- Shrewd: "prompt-optimisation gains on dev vanish on test". — [L30] citing [sshah03/shrewd](https://github.com/sshah03/shrewd)

### Inferences
- (ASSUMED) The sweet spot for us is **30 train / 30 val / 40 test sellers**, stratified by history state × size × language zone. That is far inside the 20–100 range Decagon found best.
- (ASSUMED) Budget: `max_metric_calls` ≈ 150–250, with one strong reflection LM via OpenRouter and the task LM set to the model that will run the generator.
- (ASSUMED) Cost and time estimate:
  - each metric call = 1 generator call (~3k tokens in / 1.5k out) + 1 judge call (~4k in);
  - with about 8 parallel workers, one run takes about **20–40 minutes** of wall-clock time and a few dollars of OpenRouter spend.
  - This is not measured; time a 20-call smoke run on Day 1.
- (ASSUMED) Set `use_merge=False` at first, because merge was mixed in the paper. Also cap the evolved instruction at about 1,500 characters through a custom proposer or by rejecting longer candidates.
- (ASSUMED) **Prefer the bare `gepa` package with a custom adapter over a full DSPy rewrite.** The generator is one LLM step plus deterministic code, so DSPy module plumbing adds little. Either is a framework, not a pre-built solution.
- MIPROv2 and SIMBA: these optimize instructions plus few-shot demos (MIPROv2) or do stochastic mini-batch self-reflection (SIMBA). GEPA outperforms MIPROv2 per its paper, and few-shot demos would mean pasting past-call examples into prompts, which risks leaking real seller text. **Skip both.** (ASSUMED; MIPROv2 comparison from [arXiv 2507.19457](https://arxiv.org/abs/2507.19457))

### Gaps
- The DSPy optimizer overview page failed to render, so MIPROv2/SIMBA costs and data needs are not independently sourced here.
- Whether Sarvam's chat API (sarvam-m / 105B) is reachable as a LiteLLM model string, so it can be GEPA's task LM, is unverified. If not, write a thin custom adapter, which GEPA supports.
- There are no published GEPA results on persona or style-generation tasks; all gains are on QA, math and instruction following.

---

## Q2. Alternatives: rule mining and uplift, bandits, and self-refine

### Takeaway
The **highest-value "learning" for PS04 is evidence-mined rules**: shallow trees and segment contrasts on past-call outcomes and signals, each turned into a rule with n, effect and confidence. This directly produces the 15% evidence criterion and the per-setting reasons. True uplift is only possible on the few concurrent bot-version arms, which are confounded and whose content we don't know. Bandits need live traffic we don't have. Self-refine is a cheap per-seller polish step, not a learning loop.

### Cited Findings
**Rule-mining material already exists (PROVEN [PB])**
- Depth-4 trees: previous disposition carries 0.74 of importance for meeting-fixed and 0.85 for not-interested. For rush on transcribed calls, it is 0.52, with zone and GST age 0.13 each.
- Previous-disposition table (n=269,455), meeting-fixed by previous call:
  - first call 17.4%;
  - previous Meeting-Fixed 21.7%;
  - previous Call-Later 8.1%;
  - previous Not Interested 4.4%.
  Reweighting by lead bucket or bot version changes these by ±0.7 pt.
- A seller's own prior signal persists into the next call:
  - rush 30.8% vs 21.1% (n=276);
  - confusion 25.0% vs 7.0% (n=68);
  - bot-question 22.9% vs 3.5% (n=35).
- Objection mix is nearly flat across segments (±5 pts). Identity questions rise with size (38.0% → 47.2%) and history (49.4% for previously-NI sellers).
- 11:00–14:00 calls convert 8.2% vs 12.7–13.5% at other times.

**Natural "treatment" arms in the data (PROVEN [ARMS])**
- 8 `lead_bot_version` values across 269,455 calls and 130,129 sellers:

| version | calls | meeting-fixed | months |
|---|---|---|---|
| main_vani | 208,605 | 11.6% | Apr–Sep |
| arrowhead | 30,676 | 10.7% | — |
| last_met_d | 23,046 | 11.1% | Jun–Jul |
| main | 5,573 | 14.0% | — |
| last_met_a | 723 | 11.9% | — |
| personalis | 452 | 14.2% | — |
| base_vani | 289 | 18.3% | — |
| summary_va | 91 | 3.3% | — |

- 3–4 versions ran concurrently with ≥1,000 calls each in Jun–Aug.
- 13,906 sellers were reached by ≥2 versions.
- [PB] notes 97% of Tamil Nadu calls went to `arrowhead`, so assignment is **not random**.

**Uplift caveats (DOCUMENTED)**
- Uplift modelling estimates heterogeneous treatment effects (S/T/X/R meta-learners, causal forests). On observational data, "where the treatment is not assigned randomly", it "should take extra caution", because omitted confounders bias the effect. — [CausalML, arXiv 2002.11631](https://arxiv.org/pdf/2002.11631)
- Causal forest and BART are interpretable and do well in low dimensions, but struggle with high-dimensional sparse features. — [TSCAN, arXiv 2504.18881](https://arxiv.org/pdf/2504.18881)

**Self-refine and judges (DOCUMENTED)**
- Self-preference bias: GPT-4o and Claude 3.5 Sonnet rate their own and same-family outputs higher. The mechanism is low perplexity: judges favour text that "reads most like themselves".
- Mitigation: use separate judges across model families, randomise order, test length sensitivity, and calibrate against human labels. — [PromptLayer self-preference glossary](https://www.promptlayer.com/glossary/self-preference-bias); [Self-Preference Bias in Rubric-Based Evaluation, alphaXiv 2604.06996](https://www.alphaxiv.org/abs/2604.06996)

**Simulated sellers (DOCUMENTED)**
- On 2,790 production sales conversations, LLM user simulators showed a **"disengagement deficit"**. Simulated non-buyers halved expressed resistance (25.1% → 13.5%) and nearly doubled deliberation (21.9% → 40.1%): "real non-buyers say 'not now' and stop; simulated non-buyers ask about price".
- In another benchmark, simulators were "persuaded by sales agent suggestions" and the best model reached <79% alignment with persona specs. — [alphaXiv 2605.08334](https://www.alphaxiv.org/abs/2605.08334) (via search snippets)

### Inferences
**Rule mining → deterministic rule layer (ASSUMED; recommended core).** Pipeline, all written in-event:
1. Compute candidate rules: segment → (signal rate, outcome rate) contrasts and depth-3/4 trees on features we have:
   - previous disposition and attempt count;
   - turnover, GST age, business type, nature of business;
   - product count, state/zone;
   - `asked_if_talking_to_bot`, `showed_frustration`, `past_objections` and `past_questions_asked` categories;
   - `do_not_call_requested`, `already_in_touch_with_executive`;
   - hour bucket.
2. Keep a rule only if all three hold:
   - n ≥ 200;
   - the bootstrap 95% CI of the contrast excludes 0;
   - the contrast **holds on a time split** (Apr–Jul mine, Aug–Sep check).
3. Assign a strength tier:
   - STRONG: n ≥ 2,000, holds on time split, survives reweighting by bucket/version;
   - MODERATE: n ≥ 200 and holds;
   - WEAK: n < 200, or external literature only;
   - GUESS: design assumption with no data.
4. Map each surviving rule to a persona-setting *direction* (e.g. "prior rush → pace +0.1, brevity high, opening time-boxed"). The mapping itself is a **design assumption**. The data shows *who will rush*, not that a crisp pace *helps* them. Label it "signal-propensity evidence, not causal lift".
5. Re-mine once on Day 2 after the generator is fixed. Report rules added or dropped and CI changes. That is the "self-improving evidence base" story.

**Uplift on bot-version arms (ASSUMED).** At most one honest slide:
- Within concurrent months and within lead bucket, compare segment × version meeting rates (e.g. T-learner style per-segment differences).
- We don't know what each version changed in delivery, so it can't be mapped to persona dimensions.
- The confounding is shown (TN→arrowhead).
- Use only as "where we'd A/B next", not to drive rules.

**Bandits / Bayesian updating (ASSUMED).** Thompson sampling over persona options needs outcome feedback from new calls made with our personas. No such traffic exists in 2 days, and the demo has 2–3 calls.
- A Beta-posterior *display* is fine: rule confidence as Beta(successes + 1, failures + 1) from historical counts, posterior mean ± interval. It is honest and fits FAQ Q6 confidence.
- **Online bandit learning is out of scope.**

**Self-refine (ASSUMED).** One critique-and-revise pass per seller is cheap: check reasons cite real fields, no numbers or prices, confidence lowered for missing fields. It is better done **deterministically** with validators plus a retry. It improves the *output*, not the *generator*, so don't call it the learning loop.

**Simulated sellers (ASSUMED).** Too agreeable and too slow (multi-turn × sellers × candidates) to drive the generator loop. Keep them for switch-detection testing (a separate block), and even there seed them with real aggregate resistance rates.

### Gaps
- What each bot version actually changed (script, voice, prompt) is unknown; ask the organisers on Day 1.
- No randomized persona experiment exists in the data, so every rule is correlational.
- The simulator-realism paper was seen through search snippets only.

---

## Q3. What the base persona is and how per-seller variation is computed

### Takeaway
The base persona is a **fully specified default spec** in which every field has a value, a reason ("default: no seller data"), confidence = LOW and evidence = GUESS or external. Per-seller personas apply **feature → setting functions** (mined rules) as additive deltas on that base, then LLM wording. Every applied rule writes its id, the seller fields used, its stat and its tier into the spec. Missing inputs leave the base value in place with lowered confidence, which satisfies FAQ Q6 by construction.

### Cited Findings
- Spec fields required: voice (gender, accent, pitch, pace), language (Hinglish mix, formality), tone (warmth, empathy), plan (opening, personalisation, objection playbook, escalation, guardrails), each with a reason tied to seller data. — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Seller file columns available include:
  - business_type, annual_turnover, nature_of_business, gst_registration_year;
  - top categories and state;
  - `eng_*` engagement counts (pickup ratio, callbacks, meetings, NI counts, enquiries, PNS);
  - bot_attempts / answered / dispositions;
  - avg_answered_call_sec;
  - past_objections, past_questions_asked, asked_if_talking_to_bot, showed_frustration;
  - past_dispositions_detailed, already_in_touch_with_executive, do_not_call_requested.
  (PROVEN, header read of `ps07_seller_files_part1.csv`)
- [PB] prior design (ASSUMED there):
  - 5 history/size archetypes + a DNC gate + a language overlay;
  - 3 voice styles (crisp / warm / formal) mapped to v4 voices;
  - pace 0.9–1.1;
  - pitch held at 0 with the voice carrying timbre;
  - language rule: PNS language > state table > Hinglish.
- Platform: voice is fixed per call. Per-session `text_to_speech_config{speaker, pace, pitch}` exists in the SDK but was not exercised live. Phone calls select one of the published `app_version`s. (DOCUMENTED/PROVEN per [PB] Q6)
- Selection with 75% host-fit / 15% diversity / 10% wildcard in a deterministic persona PoC. It was used for selecting among candidate personas, not for generating per-user specs. — [L30] citing [TYanoLine PR](https://github.com/TYanoLine/zutto-pccom-prototype/pull/129)

### Inferences
**Recommended generator architecture (ASSUMED):**
```
seller row ─► feature extractor (deterministic; flags missing fields)
           ─► rule layer: base spec + Σ applicable mined rules (deltas, ids, stats, tiers)
                          + hard gates (DNC, AI-disclosure if asked_if_talking_to_bot, guardrail block)
           ─► continuous settings: pace = clip(1.0 + Σ w_i·f_i, 0.9, 1.1); warmth, formality,
              Hinglish-mix, brevity as 0–1 scores = clip(base + Σ w_i·f_i)
           ─► voice resolver: (gender pref, style, language) → nearest v4 voice in catalogue
              (or → app_version on phone)
           ─► LLM step (Sarvam LLM; THE LEARNABLE PROMPT): writes opening, personalisation line,
              playbook ordering + first moves, escalation wording, and the reason sentences,
              given features + applied rules; JSON schema
           ─► validators: schema; every reason cites ≥1 present seller field + rule id;
              no digits/prices/claims outside a whitelist; confidence = min(rule tier,
              data completeness); spec diff vs base non-empty
           ─► persona.json (+ evidence table rows)
```

**Learnable parts and how each learns:**

| part | learned how | when |
|---|---|---|
| which rules exist, plus their n/effect/tier | mined from data (Q2) | Day 1, re-mined on Day 2 |
| weights `w_i` (continuous deltas) | set from the standardised effect size of the rule, scaled to the allowed range | with the rules |
| LLM instructions (wording policy, how to order the playbook, how to write reasons) | GEPA | Day 1 evening / Day 2 morning |
| voice resolver, gates, guardrails | **fixed, hand-written** | — |

- The gates and guardrails stay fixed for compliance: a loop must never be able to edit them.
- Weight tuning (the `w_i`) by search is possible but **not recommended**. No metric exists that rewards a pace of 1.07 over 1.05 except a judge's taste.
- Per-seller (not per-type) variation comes from three things:
  - continuous scores, not archetype lookups;
  - seller-specific inputs: the seller's own top-3 past objections reorder the playbook, prior signals, PNS language, category name, history state;
  - LLM wording conditioned on those inputs.
- Types (archetypes) appear only in the explanation, per FAQ Q1.
- Confidence:
  - each field is `min(tier(rule), completeness(inputs))`;
  - if no rule fired, the base value stays with confidence LOW, reason "default; live adaptation will correct" (FAQ Q6).

### Gaps
- Whether per-session pace/pitch override works with v4 speakers is unverified ([PB] Q6). If not, pace is per `app_version` and continuous pace collapses to 3 levels on phone.
- There is no evidence that bot gender or voice affects outcomes ([PB] Q4), so gender reasons will be GUESS tier.

---

## Q4. The improvement loop: signal, what gets optimized, iterations in 2 days, anti-overfitting

### Takeaway
Use a **two-speed loop**:
- **Slow loop (data → rules):** evidence mining with a time-split check. It drives the evidence and fit criteria, and is the most defensible "improvement".
- **Fast loop (GEPA on the LLM instructions):** a composite metric of
  1. deterministic spec checks;
  2. a cross-family LLM-judge fit rubric that returns textual feedback;
  3. a batch distinctness term;
  4. an **evidence-consistency / predictive-validity** term computed against held-out sellers' real next-call signals.

Past-call outcomes **cannot** directly score a new persona, because there is no counterfactual. They can only score whether the persona's *expectations* match what those sellers actually did next. Expect **2–3 GEPA runs and 1 rule re-mine** in the 2 days.

### Cited Findings
- GEPA wants feedback text and decomposed sub-scores ([DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)), 20–100 examples, a length cap and a frontier reflection LM ([Decagon](https://decagon.ai/blog/optimizing-gepa-for-production)).
- A judge from a different model family, plus human label checks, mitigates self-preference. — [PromptLayer](https://www.promptlayer.com/glossary/self-preference-bias)
- "Self improving agents improve every loop right up until the live demo, then regress to the mean" (practitioner quip). The SkillPoison paper shows self-improving pipelines can be poisoned even when every step passes verification. — [L30]
- Prior signals recur on the next call (rush 30.8 vs 21.1%, confusion 25.0 vs 7.0%), and previous disposition predicts the next outcome strongly. This gives a real held-out target for "expectation" fields. (PROVEN [PB])

### Inferences
**Signal options compared (ASSUMED)**

| signal | scores which criterion | verdict |
|---|---|---|
| Deterministic checks: schema, reason cites real present field, rule ids exist, no prices/digits, confidence lowered on missing fields, guardrail block present | fit (reasons), evidence, Q5/Q6 compliance | **must have**; cheap; can't be hacked by verbosity |
| LLM-judge fit rubric (sees seller aggregates + spec): per dimension 1–5, "is the setting justified by this seller's data?", plus a one-line critique | fit 25% | **use**; judge from a different family to the generator *and* the reflection LM; pin the judge prompt (never optimised) |
| Batch distinctness: mean pairwise field distance across a stratified batch, but only counting differences explained by feature differences (penalise variation between near-identical sellers) | distinctness 20% | **use**, as a per-instance proxy: distance to nearest other seller's persona minus expected distance from feature distance |
| Predictive validity on held-out sellers: the persona declares `expected_signals` (rush/confusion/frustration/bot-question) and `expected_engagement`; score AUC/Brier against the seller's **next** real call (time split) | evidence 15%, robustness | **use**; the only outcome-grounded, unhackable term |
| Simulated-seller conversation outcomes | switches (another block) | **don't use** for the generator: slow, sims too agreeable |
| Real outcome lift of new personas | everything | impossible in 2 days (no traffic) |

**Composite metric (ASSUMED)**
- score = 0.35·judge_fit + 0.25·deterministic_pass + 0.20·distinctness_proxy + 0.20·predictive_validity.
- Any guardrail violation scores 0, a hard fail.
- Feedback text concatenates failed checks + the judge critique + "differs from seller X only in …".

**What is optimized (ASSUMED)**
- **Learnable:** the LLM instruction block. It covers how to order the playbook from past objections, how to phrase the opening for each history state, how to write reasons and the confidence language, and when to pick Hinglish vs regional greeting wording within the rule layer's language choice.
- **Not learnable by GEPA:**
  - the rule table (changes only through data re-mining);
  - gates and guardrails;
  - the judge prompt;
  - the metric weights.

**Iteration budget for 2 days (ASSUMED; time the smoke run)**

| when | step | wall-clock |
|---|---|---|
| Day 1 AM | write the generator v0 (rules from Q2 + seed prompt) and validators | — |
| Day 1 PM | mine rules + tiers; time-split check | ~1–2 h, mostly compute on 269K calls |
| Day 1 PM | 20-call GEPA smoke run | — |
| Day 1 evening | GEPA run 1 (~200 metric calls) | ~30–40 min |
| Day 1 evening | human spot check of 10 specs | ~30 min |
| Day 2 AM | fix the judge/metric if the spot check disagrees; GEPA run 2 | ~30–40 min |
| Day 2 AM | rule re-mine with the fixed generator | — |
| Day 2 midday | freeze; generate specs for all sample sellers | 149K × 1 LLM call is too many for a full run; generate for the organiser's "sample seller files" set and a stratified 1–2K, rules-only for the rest |

Total loop effort is about 4–6 person-hours. The rest of the team time goes to switches (25%) and voice (15%).

**Overfitting and reward-hacking controls (ASSUMED)**
1. **Three-way split by seller** (train / val / test), stratified. Report only test. Freeze test before any run.
2. **Time split for rules and predictive validity:** mine Apr–Jul, validate Aug–Sep.
3. **Judge from a different model family** than both the generator and the reflection LM. A second judge from a third family runs on test only, and both must improve.
4. **Length cap** of about 1,500 characters on the evolved instruction. Reject candidates that add numbers or price words.
5. **Anti-verbosity:** cap reason length. The judge rubric explicitly penalises reasons that don't cite a concrete field value.
6. **Distinctness anti-hack:** count only differences explained by feature differences; random variation scores 0.
7. **Human spot check:** 10–20 test specs rated blind (v0 vs vN shuffled) by the non-tech teammate. Report agreement with the judge. If the judge disagrees with humans more than about 30% of the time, fix the judge, not the generator.
8. **Guardrail regression test:** a fixed set of adversarial seller rows (missing everything, DNC=1, contradictory fields, price-objection-heavy) must pass every iteration.
9. **No self-written evidence:** the LLM may cite only rule ids from the mined table; validators reject unknown ids.

### Gaps
- No measured cost or latency for GEPA on our task yet; the estimates above are ASSUMED.
- Predictive-validity AUC on persona `expected_signals` is unmeasured. With keyword-lexicon signals ([PB]) and small n for seller-level persistence (35–276), the term may be noisy for frustration and bot-question.
- The organisers' "sample seller files" count is unknown, which matters for the "spec for every sample seller" deliverable.

---

## Q5. How to show the loop's improvement to judges

### Takeaway
Show a **before/after table on held-out sellers** (v0 seed vs final), a short **lineage strip** (GEPA candidates and their val score), the **prompt diff** (the rules GEPA added, in plain language), the **rule table with tiers and the time-split check**, and **2 example specs side by side**. Keep the claim modest: "the generator improved on held-out fit, distinctness and evidence-grounding". Not "meetings went up".

### Cited Findings
- GEPA `track_stats=True` returns `detailed_results` with candidate lineage, per-instance scores and Pareto frontier metadata, which is ready-made material for a lineage chart. — [DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)
- The deck rewards "validation on real data" under Technical Robustness (20%), and the PS04 one-slide deliverable needs "sample persona spec + past-call evidence + workflow". — [persona-requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)

### Inferences
Demo artefacts (ASSUMED):

1. **Scoreboard** (test sellers, n≈40, v0 → vN), each with a bootstrap CI:
   - deterministic pass %;
   - judge fit (judge A and the unseen judge B);
   - distinctness proxy;
   - # distinct voice configs / Hinglish-mix spread;
   - % fields with STRONG/MODERATE evidence;
   - predictive-validity AUC;
   - human blind-preference % (v0 vs vN).
2. **Evidence table:** rule id, segment, stat, n, CI, tier, time-split holds ✓/✗. Show 1–2 rules *dropped* by the time split, to demonstrate honesty.
3. **Prompt diff:** 3–5 bullet "lessons" GEPA wrote, e.g. "for previously-NI sellers, open with permission + identity; never re-pitch".
4. **Same scenario, 3 sellers:** audio plus spec cards, linking the loop to the voice demo.
5. In skills.md, record the loop runs as the build journey: timestamps, budgets, scores.

### Gaps
- No evidence was found on how hackathon juries weigh a "self-improving" loop. It is not a named criterion.

---

## Q6. Devil's advocate: does each loop component earn its place?

### Takeaway
Only two loop components map cleanly onto scored criteria and fit the 2 days:
- **evidence mining with tiers** → evidence 15%, fit 25% reasons, robustness;
- **a small held-out GEPA run on the wording/reason prompt** → fit 25%, distinctness 20%.

Bandits, uplift-driven rules, simulated-seller optimisation, weight search and multi-run evolution are unscorable, out of scope, or too slow. The "self-improving" framing is itself **not a PS04 criterion**: it must not eat time from switches (25%) and voice (15%).

### Cited Findings
- PS04 criteria and deliverables. — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Pre-built rule, the 2-day build rule, and the spike-code caution. — [persona-requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- GEPA overfitting and bloat. — [Decagon](https://decagon.ai/blog/optimizing-gepa-for-production)
- Simulator disengagement deficit. — [alphaXiv 2605.08334](https://www.alphaxiv.org/abs/2605.08334)
- Observational uplift caveat. — [CausalML](https://arxiv.org/pdf/2002.11631)

### Inferences (ASSUMED)

| component | serves (deliverable / criterion) | risk flags | verdict |
|---|---|---|---|
| Base spec + deterministic feature→setting rules with reasons and confidence | D1 generator, D2 spec per seller; fit 25%; Q6 defaults | none; it is the core requirement | **build first** |
| Rule mining with n/CI/tier + time split | evidence 15%; reasons for fit; one-slide "evidence"; robustness | correlational only; must say "propensity, not causal lift"; Tamil/Gujarati signals limited by the keyword lexicon | **build** (highest ROI) |
| Rule re-mine on Day 2 ("evidence base updates") | evidence 15% | little change expected; cosmetic if nothing changes | optional, ~30 min |
| GEPA on the LLM instruction block | fit 25% (judge), distinctness 20% | overfitting/bloat (documented); judge-hacking; ~1 h per run including setup; library is a framework (OK), but the adapter, metric, rules and prompts must be written in-event | **build 1–2 runs** after v0 works end-to-end; drop if behind by Day 1 evening |
| LLM-judge fit rubric | proxy for fit 25%; also a dashboard | judge ≠ jury; self-preference; unscorable by itself | **use as a metric only**; validate with a human spot check |
| Distinctness proxy | distinctness 20% | can be gamed by arbitrary variation | use, with the feature-explained constraint |
| Predictive-validity term (expected signals vs next real call) | evidence 15%; robustness (real-data validation) | noisy for rare signals; lexicon labels | **use**; it is the most honest "it works on real data" number |
| Uplift on bot-version arms | evidence 15% at most | confounded (TN→arrowhead), unknown treatment content, can't map to persona dimensions; time sink | **one slide max**, or skip |
| Thompson-sampling bandit on persona choices | none in 2 days (no live traffic) | **unscorable / out of scope** | skip; show Beta-posterior confidence intervals only |
| Simulated-seller loop for the generator | none directly | too slow (multi-turn × candidates), too agreeable (documented); judges care about the **live** switch | skip for the generator; use sims only to test the switch block |
| Search over continuous weights `w_i` | fit (marginal) | no ground truth rewards a specific pace; overfits the judge's taste | skip; derive from effect sizes |
| Self-refine per seller | spec quality (fit) | not "learning"; adds latency | do it as deterministic validators + one retry |
| Personas changing facts/prices | — | **violates Q5** | hard validator; loop can never edit the guardrail block |
| Pre-event spike code / analysis scripts | — | **pre-built risk** | treat as research; rewrite the miner, generator and adapter during the event; say so in skills.md |
| Generating 149K specs | D2 says "every sample seller" | cost and time; unclear which sellers are "sample" | full rules-only pass (cheap, deterministic) + LLM wording for the demo/sample set; confirm with organisers |

**Biggest strategic risks (ASSUMED)**
1. **The loop optimises a judge, not the jury.** Mitigate with the human blind check and by keeping the claim to "held-out judge + real-data validity".
2. **Time.** If the voice demo with a live switch isn't working by Day 1 evening, GEPA is the first thing to cut. The rule miner stays, because it *is* the evidence deliverable.
3. **Distinctness vs fit tension.** The data says objection mix is nearly flat across profiles ([PB] Q2). True distinctness comes from history state, prior signals, language and size. Forcing more variation than the data supports would score on distinctness but lose on evidence and fit, so expose this trade-off explicitly in the spec ("varied because …").

### Gaps
- PS04 weights are "indicative, to be confirmed"; if they change on Day 1, re-weight the composite metric.
- Whether juries see a library such as `gepa` as acceptable "framework" use is assumed from the AGENTS.md rule ("frameworks are fine; core logic must be ours"), not confirmed with organisers.
