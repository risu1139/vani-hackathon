# Should an LLM agent DECIDE each seller's VANI persona and call plan (Design L), or should code decide a baseline and the agent propose gated refinements (Design V2)? (as of 2026-10-09)

Tags: **DOCUMENTED** = a paper, vendor doc or earlier project note says it. **VENDOR CLAIM** = self-reported or marketing material. **PROVEN** = measured by this team (cited via earlier notes). **ASSUMED** = inference or design. No customer data was used.

Designs compared:
- **Design L** (team lead): the agent gets the seller's traits and states plus the candidate personas. It calls tools (history including free-text summaries and objections, seller memory, a seller-type × persona scoreboard, the persona library, voice options) and **decides** the persona and plan. It also emits a "no good fit" signal that drives the creation of new personas.
- **Design V2** (our draft): code picks a baseline from data. The agent proposes bounded changes with reasons. Code validators accept or reject them.

Earlier project evidence that this builds on:
- **Test results.** The LLM deciding settings got 16/23 key decisions right, versus 23/23 for rules. A draft-plus-revise loop reached 17/23. The test is weak: the labels came from the same toy rule table (circular) and the sellers had no free text ([Persona generator architecture report](../../reports/Persona%20generator%20architecture.md)).
- **Self-correction needs external signal** (Huang et al. 2310.01798; Kamoi et al. 2406.01297).
- **Wrong logging probabilities caused up to 3.0× estimation error, and a decision leaking into features up to 8.7×**, in Microsoft's Decision Service ([Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)).

---

## 1. LLM as decider or policy for personalisation and next-best-action: who makes the final call in production, and how reliable is it?

### Takeaway
Production systems almost never let the LLM have unconstrained final authority over a business decision. The 2025–26 trend runs the other way: vendors are adding deterministic layers (Salesforce Agent Script, Sierra deterministic guards and supervisors, Decagon AOPs that compile to "controllable logic"). Where LLMs do rank or decide (recommenders, NBA), they sit inside a stack whose quantitative layer is propensity or uplift scoring plus bandits. Gains from LLM rankers are real but often small, and they are validated by A/B tests, not by the LLM's own reasoning.

### Cited Findings

**Salesforce Agentforce / Atlas** (DOCUMENTED, vendor)
- In Oct 2025 Salesforce introduced Agent Script, a DSL compiled into an "Agent Graph" consumed by the Atlas Reasoning Engine. It adds "hybrid reasoning" that separates deterministic execution from LLM reasoning, "ensuring the agent follows a precisely defined structure for every workflow execution while still using LLM reasoning where judgment and contextual interpretation are needed" — [Salesforce dev blog](https://developer.salesforce.com/blogs/2025/10/introducing-hybrid-reasoning-with-agent-script); [Architect guide](https://architect.salesforce.com/docs/architect/fundamentals/guide/hybrid-reasoning-agentforce-builder-agent-script)
- Salesforce's own argument against pure prompt control ("doomprompting"): "a 5% failure rate for something like order returns is a dealbreaker for most companies." Their list of what should be deterministic: topic classification, action sequencing, conditional variables, and pre-reasoning context gathering. The LLM keeps phrasing and nuance of intent. — [Salesforce blog](https://salesforce.com/blog/doomprompting/)

**Sierra and Decagon** (DOCUMENTED, vendor)
- Sierra: "LLMs ... are non-deterministic." It uses deterministic guards, which are "non-model checks that can't be talked out of doing their job" (for example, tools hidden until the customer is authenticated). Supervisor agents audit every action and response and switch from observe to intercept on high-risk topics. — [Sierra: enterprise-grade agents](https://sierra.ai/blog/enterprise-grade-agents); [Sierra: defense in depth](https://sierra.ai/jp/blog/defense-in-depth-in-the-age-of-agents)
- Decagon: natural-language Agent Operating Procedures compile "into controllable logic", so engineers keep code-level control — [Decagon blog](https://workos-pilot.decagon.ai/blog/the-future-of-ai-agents-is-test-driven)

**Next-best-action (BCG 2026)** (DOCUMENTED, consultancy; no numbers)
- Action selection has three layers: propensity and uplift, contextual bandits, and agent reasoning. These "are additive, not alternative."
- On authority: "The agent doesn't replace the bandit; it decides when to defer to the bandit's quantitative recommendation and when to override it because unstructured context has changed the calculus."
- "Policies and budgets computed in the batch layer serve as guardrails ... prevents the agent from making locally optimal decisions that are globally suboptimal."
- The LLM supplies a reasoned prior for new actions, and the bandit "updates it through controlled exploration."
- BCG gives **no quantified results**.
- Source: [BCG: The science behind NBA programs](https://www.bcg.com/publications/2026/the-science-behind-next-best-action-programs)

**LLM rankers in production** (DOCUMENTED)
- **Netflix GenRec (2026).** This is an LLM-backed ranker over "verbalized user histories and context." A large A/B test showed "statistically significant gains in offline and online metrics" using far fewer labelled examples. It needed a cost-constrained, prefill-only serving design — [arXiv 2608.10257](https://arxiv.org/abs/2608.10257)
  - A secondary outlet reports about +1.6% offline MRR and a **0.006% relative** online lift on 10% of traffic — [runtimewire (aggregator, unverified)](https://runtimewire.com/article/netflix-genrec-llm-ranker-traffic-test)
- **Real-estate search (2026).** An LLM re-ranker in a randomised A/B test (Apr 7 – May 8, 2026) gave **+5.3% relative CTR** and **+4.8% scheduled visits**. It added **+4.2 s latency** and about **+7% cost**. (Figures from the search snippet; not opened in full.) — [arXiv 2607.14835](https://arxiv.org/pdf/2607.14835)

**LLM as a bandit policy** (DOCUMENTED, research)
- Krishnamurthy et al. (NeurIPS 2024): LLMs "do not robustly engage in exploration without substantial interventions." Only GPT-4 with chain-of-thought **and an externally summarised interaction history** behaved satisfactorily — [Microsoft Research](https://www.microsoft.com/en-us/research/publication/can-large-language-models-explore-in-context/)
- EVOLvE (ICML 2025): current LLMs largely fail bandit tasks in context. Algorithm-guided support at inference time, or distillation from bandit algorithms, is needed — [PMLR 267](https://proceedings.mlr.press/v267/nie25b.html)
- In LLM-based contextual bandits, greedy policies are sub-optimal on regret and epistemic uncertainty helps — [arXiv 2404.02649](https://arxiv.org/abs/2404.02649)

**Structured prediction** (DOCUMENTED)
- Gradient-boosted trees beat LLMs on tabular prediction once there are more than a few examples. TabLLM wins only at 8 shots or fewer — [arXiv 2411.04324](https://arxiv.org/html/2411.04324v1)

### Inferences
- **The industry pattern is closest to V2**, and BCG's "agent decides when to override" is a middle ground (ASSUMED):
  - the quantitative layer (scoreboard, rules, bandit) produces the default;
  - the agent may override with a stated reason;
  - batch-computed guardrails bound the override.
- Pure Design L, where the agent reads a scoreboard and decides, asks the LLM to do in-context statistics. The bandit literature says this is unreliable **unless the history is pre-summarised externally** (ASSUMED application). That is an argument for scoreboard tools that return computed posteriors and CIs, not raw rows.
- **The real case for the LLM is unstructured context** (free-text objections and call summaries) that rules cannot encode. BCG and GenRec both locate the LLM's value there (ASSUMED synthesis).

### Gaps
- No public A/B test was found in which an LLM agent *alone* chose a per-customer treatment versus a rules or ML baseline in outbound sales or voice. No Etsy LLM-profile outcome numbers were retrieved, and no Intercom Fin decision-authority data (not searched in depth within the budget).
- Sierra and Decagon outcome claims are vendor claims, with no independent numbers.

---

## 2. Do tools over real data reduce wrong-but-confident decisions?

### Takeaway
Only partly, and it depends on the tool type:
- **Verification-type tools** (deterministic computation) improve calibration.
- **Evidence-type tools** (noisy retrieval) can *increase* overconfidence.

Verbalised confidence is inflated. Self-consistency is a positive but weak signal, and errors are often confidently shared across runs and models. Agreement-based abstention buys accuracy at a large cost in coverage.

### Cited Findings
- **"The Confidence Dichotomy" (Jan 2026).** Tool-use agents show higher calibration error than standalone LLMs. "Evidence tools (e.g., web search) systematically induce severe overconfidence due to inherent noise in retrieved information, while verification tools (e.g., code interpreters) can ground reasoning through deterministic feedback." The fix was RL training, which is not available to us. — [arXiv 2601.07264](https://arxiv.org/abs/2601.07264)
- **Verbalised confidence.** Models are systematically "moderately overconfident" and often confidently wrong — [Xiong et al.](https://arxiv.org/pdf/2306.13063); [search summary of 2604.01457](https://www.alphaxiv.org/abs/2604.01457.md)
- **Behavioural consistency (ICML 2026, Mehta), 4 models and 8,000 runs:**
  - The same agent on identical input gives **2.3–4.2 distinct action sequences per 10 runs**.
  - Consistent tasks score 82–87% accuracy; inconsistent tasks score 41–65%.
  - Answering only when 3 runs agree gives **87–88% accuracy at 54–62% coverage**, +6–14 pp over a single run.
  - Consistency detects failures at AUROC 0.62–0.78.
  - Single-run evaluation **misranked models 29.3% of the time**.
  - Source: [ICML 2026 poster](https://icml.cc/virtual/2026/74530)
- **"When LLMs Agree, Are They Right?" (2026), 265K samples across 53 runners:**
  - Agreement and correctness correlate only weakly (Spearman 0.20–0.59).
  - gpt-4.1 had the highest self-consistency (0.89) but the weakest link to correctness. High-confidence answers (C ≥ 0.8) were **wrong 48%** of the time on GPQA Diamond (ECE 0.41).
  - **28% of cases were confidently wrong across all runners**, and different providers shared the same wrong answers.
  - Source: [alphaXiv 2607.08065](https://www.alphaxiv.org/abs/2607.08065.md)
- **Self-consistency in general.** It is "a regime-dependent empirical proxy for accuracy ... unreliable as a standalone confidence score," and a consensus can be confidently wrong — [search summary of 2604.19444 / 2605.x](https://www.alphaxiv.org/abs/2604.19444v1)
- **Earlier project findings** (DOCUMENTED in [llm_architectures.md](../Persona%20generator%20architecture/llm_architectures.md)):
  - CRITIC-style correction works because tools do the checking.
  - Intrinsic self-correction does not.

### Inferences
- Classifying Design L's tools (ASSUMED):
  - The **scoreboard and stats tools are verification-like** (deterministic numbers). They should help, provided they return computed effect sizes, n, CIs and tiers rather than raw rows.
  - **Free-text history and summaries are evidence-like** (noisy and anecdotal). By the Confidence Dichotomy finding they are the input most likely to produce confident over-reading, such as one remark turning into a persona switch.
  - Free text is also the only input where an LLM beats rules.
- **Agent confidence and "no good fit" should not be self-reported.** Derive them externally (ASSUMED design):
  - (a) k=3–5 sampled decisions and their agreement rate;
  - (b) agreement with the code baseline;
  - (c) scoreboard n and CI for the chosen cell.
- The "no good fit" signal in Design L is an abstention signal. On the evidence above, verbalised abstention is miscalibrated. Make it a computed trigger instead (ASSUMED), for example:
  - low agreement across samples;
  - the best persona's scoreboard CI overlaps the population mean;
  - a free-text objection class that no library persona covers.

### Gaps
- No study was found on LLM calibration when the tool returns *aggregate outcome statistics*, which is our scoreboard case. The dichotomy paper covers search and code only.
- No results on Sarvam-105b calibration or self-consistency specifically.

---

## 3. Control and safety: validators, structured outputs, and decision-authority patterns

### Takeaway
Every production pattern found combines **deterministic pre-gates, a bounded action space, and post-hoc deterministic checks**, with LLM judgement only inside those bounds. "Decide within an enumerated action set, then gate" (Design L made safe) and "propose a delta, then gate" (V2) are both legitimate. The difference is what happens on rejection, and whether a rejected decision falls back to a data-backed default.

### Cited Findings
- **Sierra.** Deterministic guards restrict which tools the agent can even see. Supervisors audit every action and can intercept — [Sierra](https://sierra.ai/blog/enterprise-grade-agents)
- **Salesforce.** Pre-reasoning context gathering and conditional variables are deterministic, and the LLM reasons only inside defined topics — [Salesforce](https://salesforce.com/blog/doomprompting/)
- **BCG.** Batch-layer policies and budgets act as guardrails on agent decisions — [BCG](https://www.bcg.com/publications/2026/the-science-behind-next-best-action-programs)
- **Earlier project spikes:**
  - Sarvam strict json_schema mode looped on nested schemas in 4/6 calls, while a flat schema never failed (PROVEN).
  - DSPy Assertions report up to 164% more constraint passes from constraint-plus-retry (DOCUMENTED).
  - Source: [Persona generator architecture](../../reports/Persona%20generator%20architecture.md)

### Inferences: how authority could be split (ASSUMED)

| Authority pattern | Agent output | Code role | On rejection | Fits |
|---|---|---|---|---|
| L-free | Free-form persona + plan | Validate form | Repair, then template | Not recommended (no data-backed fallback) |
| **L-bounded** | Pick `persona_id` from code-filtered eligible set + plan move ids + reason citing tool results | Eligibility pre-filter, cited-evidence check, STRONG-rule binding check | Fall back to code baseline | Design L made safe |
| **V2** | Delta vs baseline (≤ k fields changed), each with reason + cited evidence | Baseline, validator, accept/reject per delta | Keep baseline field | Our draft |
| BCG override | Defer or override the quantitative pick, with reason | Bandit/scoreboard default | Default stands | Hybrid |

- If the eligible set is computed by code, the fallback is the code baseline, and every override must cite a tool result that the validator can re-run, then **L-bounded and V2 converge**. The remaining difference is framing ("choose" versus "edit").
- **Anchoring is the one real behavioural difference.** V2 anchors the LLM on the baseline, which reduces overrides and raises precision but may suppress valid free-text-driven changes. L-bounded does not anchor, which gives more overrides with lower precision. This is testable (see §6).
- **Human-in-the-loop does not fit a nightly batch of thousands of sellers** except as sampled audit, plus approval of *new personas* created from "no good fit". New personas are a library change, so they should go through the B5 gate (n, time split, human approval).

### Gaps
- No published comparison of "choose from set" versus "edit a baseline" framings on decision quality. The anchoring effect is ASSUMED from general LLM anchoring behaviour, not measured in this setting.

---

## 4. Learning compatibility: if the agent decides, how to log probabilities, feed back outcomes and handle drift

### Takeaway
An LLM's choice has no usable propensity by default. Temperature sampling gives probabilities only if you sample many times or read token log-probs, and LLMs are poor at in-context exploration. **For off-policy evaluation, the logged probability must come from a code-side randomiser** applied *after* the agent's ranking (ε-greedy or softmax over the agent's scores, plus a holdout). This works under both designs. **Learning must live in tables the tools read, not in the agent.**

### Cited Findings
- **Large action spaces.** IPS-based off-policy estimators "degrade severely" there, with extreme bias and variance — [Saito & Joachims ICML 2022](https://icml.cc/virtual/2022/spotlight/16730)
- **Off-policy evaluation of LLM coaching (2025).** Logging propensities had to be *approximated* by fitting behaviour models, or by re-running the behaviour LLM to extract token log-probs at the action span. Estimators used were SNIPS and AIPW — [arXiv 2510.17173](https://arxiv.org/pdf/2510.17173)
- **LLMs need external summarisation to explore**, so an LLM is not a reliable exploration policy on its own — [Krishnamurthy et al.](https://www.microsoft.com/en-us/research/publication/can-large-language-models-explore-in-context/); [EVOLvE](https://proceedings.mlr.press/v267/nie25b.html)
- **Microsoft Decision Service.** Wrong probabilities caused up to 3.0× estimation error, and a decision leaking into features up to 8.7× — [arXiv 1606.03966](https://arxiv.org/abs/1606.03966) via [Data driven persona agent](../../reports/Data%20driven%20persona%20agent.md)
- **Same input, different actions.** An agent produced 2.3–4.2 distinct action sequences per 10 runs ([ICML 2026](https://icml.cc/virtual/2026/74530)). The LLM's decision is therefore already stochastic but with **unknown** probability. That is the worst case for off-policy evaluation, because there is randomness with no logged propensity (ASSUMED implication).

### Inferences (ASSUMED)
- Three ways to get a propensity when the agent decides:
  1. **Agent ranks or scores every eligible persona, then code samples** (softmax with temperature τ, or ε-greedy with ε of about 0.1) and logs p. **Recommended.** It is the same mechanism in L and V2.
  2. **Sample the agent N times** (e.g. 5) and use empirical frequencies as p. The estimate is noisy (p in steps of 0.2) and costs N×. It gives the agreement signal for §2 at the same time.
  3. **Token log-probs** of the persona_id. Needs a logprob API; Sarvam support is unverified.
- **Determinism for reproducibility.** Pin the model version, prompt version and tool-result snapshot in the decision row. Use temperature 0 for the ranking call, and keep all randomness in the code sampler, so that p is known exactly.
- **Feedback.** Outcomes update scoreboard posteriors, seller memory and rules (versioned tables). The agent sees learning only through tools, so prompt drift cannot carry hidden state.
- **"No good fit" counts are themselves a logged event** (rate per segment). A rising rate signals library drift.
- **Drift monitors:**
  - agent override rate versus baseline per segment;
  - share of decisions per persona (collapse detection: free generation collapses toward stereotypes, arXiv 2604.24698, via earlier notes);
  - calibration of agent-chosen arms on realised outcomes.

### Gaps
- Not confirmed whether Sarvam's chat API exposes token log-probs.
- No reported OPE of an LLM-ranking-plus-code-sampler policy in outbound calling.

---

## 5. Cost and latency at nightly-batch scale

### Takeaway
A nightly batch removes the latency objection; Vapi's 7.5 s limit applies only at dial time. Cost scales with tool turns and the number of samples. A tool-using agent costs roughly 10–20× one wording call, and k-sample consistency multiplies that again. At the likely daily volume (tens of thousands of sellers due), both designs are affordable. Throughput and rate limits, not money, are the binding constraint.

### Cited Findings
- **Earlier measured costs on Sarvam-105b** (PROVEN, [Persona generator architecture](../../reports/Persona%20generator%20architecture.md)):

| Option | Cost per seller | Latency per seller |
|---|---|---|
| A: rules + one wording call | ~₹0.017 | ~1.0 s |
| B: single structured call | ~₹0.16 | ~4.2 s |
| C: draft + 2 revisions | ~₹0.30 | ~7.6 s |
| Claude Code agent (off-premises) | ~$0.18 | ~24 s |

- A covers 149K sellers for about ₹2.5K and about 2 h at 20-way concurrency.
- **The real-estate LLM re-ranker** added 4.2 s latency and about 7% operating cost — [arXiv 2607.14835](https://arxiv.org/pdf/2607.14835)
- **Netflix needed a prefill-only serving design** to make an LLM ranker cost-feasible — [arXiv 2608.10257](https://arxiv.org/abs/2608.10257)

### Inferences (ASSUMED)
- **Design L per seller:** about 4–6 tool round-trips plus a final decision, so roughly ₹0.3–0.6 and 8–15 s. With k=3 samples for consistency and propensity: about ₹1–2.
- **Design V2 per seller:** code baseline plus one refinement call with pre-fetched tool results (no agent loop), about ₹0.05–0.2. **Run it only for sellers with free text or low baseline confidence.**
- **Volume:** if about 40K of 12 lakh sellers are due per day (an assumption; the real call cadence is unknown), the daily cost is:

| Design | Daily cost | Batch time at 20-way concurrency |
|---|---|---|
| L (k=3) | ₹40K–80K | ~5–8 h |
| V2 | ₹2K–8K | under 1 h |

- **Cost-saving moves for L** (cost depends on inputs, not on who decides):
  - pre-fetch tool results deterministically (Salesforce's "pre-reasoning context gathering");
  - cache persona-library and scoreboard prompts;
  - skip the agent for sellers with no free text and a STRONG baseline.

### Gaps
- Daily due-seller volume, Sarvam batch and rate limits, and current Sarvam-105b pricing were not re-verified in this pass.

---

## 6. Verdict criteria: when does Design L beat V2, and what is a fair 2-day experiment?

### Takeaway
**Design L can win only where free-text history carries decision-relevant information that rules and the scoreboard cannot encode, and only if its decisions are grounded (cited, verifiable tool results) and bounded (eligible set, code fallback).** Where the signal is structured, code plus statistics wins on accuracy, reproducibility, auditability and cost. The earlier 16/23 result is weak evidence because of circular labels and no free text. A fair test needs **pre-registered expected answers written before either system runs, free-text-bearing sellers, and a judge independent of both designs.**

### Cited Findings
- GBDTs beat LLMs on structured prediction beyond a few shots — [arXiv 2411.04324](https://arxiv.org/html/2411.04324v1)
- LLMs read unstructured context that structured models cannot — [BCG](https://www.bcg.com/publications/2026/the-science-behind-next-best-action-programs)
- **Single-run evaluation misranks systems 29.3%** of the time, so run multiple seeds — [ICML 2026](https://icml.cc/virtual/2026/74530)
- **LLM judges are biased**; same-family judges share errors — earlier notes ([llm_architectures.md](../Persona%20generator%20architecture/llm_architectures.md)). Cross-provider shared wrong answers appear above chance — [alphaXiv 2607.08065](https://www.alphaxiv.org/abs/2607.08065.md)
- **Simple baselines beat complex agents at equal cost** (Kapoor et al. 2407.01502, via earlier report).

### Inferences: conditions (ASSUMED)

**Design L beats V2 when all of these hold:**
1. A large share of sellers due have **free-text objections or summaries** that change the right persona. Example: "spoke to my son last time, he handles it" calls for a different opening.
2. The **persona library is large or compositional** (many persona × plan combinations), so a code baseline cannot enumerate rules for each.
3. The scoreboard is **sparse** (new personas, small cells), so the code baseline is close to a guess anyway.
4. **Grounding is enforced:** the agent's reasons must cite tool outputs that a validator re-checks.
5. **Consistency is high:** k samples agree. Where they disagree, fall back.

**V2 beats L when any of these hold:**
1. The decision-relevant signal is mostly structured (traits, states, past outcomes). PS07 analysis shows memory and outcome fields drive the predictions (AUC 0.71–0.78), per earlier reports.
2. Reproducibility and audit matter. Judges ask "why slow pace?" and want a rule id with n and tier.
3. Off-policy evaluation and learning must be clean from day one (§4).
4. Cost or throughput is tight.

**On the "no good fit" signal:** this is the strongest original part of Design L. It is equally possible in V2, where the agent flags "baseline wrong and nothing in the library fits". It should be a computed abstention, not self-report (§2), and must route to a gated library change, not an instant new persona.

**A practical merge ("V2 with L's strengths"):**
- Code baseline plus eligible set.
- The agent ranks the eligible personas, with the baseline shown as one candidate (de-anchoring), using pre-fetched tools including free text. Each override needs cited evidence.
- Code accepts the override only if: the evidence validates, no STRONG rule is violated, and k=3 samples agree.
- Code samples with logged p.
- "No good fit" fires when the computed triggers fire.

### Inferences: a fair 2-day experiment (ASSUMED design)

**Test set**
- 30–40 **synthetic** sellers (no customer data), with about 60% carrying free-text history.
- Stratify across 4 kinds of case:

| Case type | What it tests |
|---|---|
| (a) Structured signal only | Does L do no harm? |
| (b) Free text that *changes* the right answer | L's claimed edge |
| (c) Free text that is a *distractor* (noisy, one-off remark) | Over-reading |
| (d) Genuinely no-fit cases | "No good fit" recall |

**Pre-registered labels**
- **Before** either system is run, two teammates who did not build the systems write the expected persona_id, or "no fit", plus the 2–3 critical plan elements per seller.
- Each label carries a short rationale. Labels are frozen in a hashed file.
- Disagreements are adjudicated by a third person. Report inter-rater agreement.
- The labels must not be derived from the rule table, to avoid the circularity of the earlier test.

**Arms**
- L-bounded.
- V2.
- Code baseline alone (control).
- Optionally the merged design.
- Same Sarvam model, same tools, same tool snapshots, **k=5 runs per seller per arm**.

**Metrics**

| Metric | Measure |
|---|---|
| Decision accuracy | Match to pre-registered label, primary metric |
| Free-text sensitivity | Accuracy on (b) |
| Distractor robustness | Accuracy on (c) |
| No-fit precision and recall | On (d) |
| Confident-wrong rate | Wrong with self-confidence ≥ 0.8, or wrong with k-agreement ≥ 0.8 |
| Run-to-run consistency | Agreement across the 5 runs |
| Validator rejection rate | Share of decisions rejected |
| Cited-evidence validity | Share of citations that check out |
| Cost and latency | Per seller |

**Independent judge**
- Use only for plan or wording quality, not persona choice, which uses the pre-registered labels.
- The judge is a different model family from the decider (e.g. a model on the internal gateway), blind to arm, with order randomised.
- Calibrate it against about 20 human-labelled items first.

**Decision rule (pre-registered)**
- **Adopt L or the merged design** only if it beats V2 on (b) by ≥ 15 pp **and** is not worse on (a) and (c) by more than 5 pp **and** its confident-wrong rate is ≤ V2's.
- **Otherwise keep V2.** Use L's agent as V2's refinement step.
- With n ≈ 35, only large differences are detectable. State this upfront.

**Schedule**
- Day 1 morning: author sellers and labels.
- Day 1 afternoon: build both arms on shared tools.
- Day 1 evening: run the batch.
- Day 2 morning: analyse.

### Gaps
- Real proportion of VANI sellers with useful free-text history is unknown, and it decides condition L1. It is measurable from PS07 aggregates (share of calls with non-empty objection or summary text) without exposing content.
- No external benchmark of "choose" versus "edit-baseline" framing exists. The experiment above is the only way to settle it for this case.
- Sarvam-105b self-consistency and tool-use reliability at k=5 is untested.
