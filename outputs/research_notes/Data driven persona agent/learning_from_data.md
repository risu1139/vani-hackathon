# Learning from data: a staged path for the VANI persona + call-plan agent (as of 2026-10-08)

Tags: **DOCUMENTED** = a paper or official page found in this session (search snippet or fetch) says it. **ASSUMED** = our inference for VANI. No seller data used.

Context read first:
- [learning-loops.md](../../../wiki/projects/vani-hackathon/learning-loops.md): the decided design. No model is trained. Learning edits rules, per-seller memory, tiers, lexicon and prompt wording. Bandits and fine-tuning are out for the hackathon.
- [llm_architectures.md](../Persona%20generator%20architecture/llm_architectures.md): self-critique only helps with an external signal (Huang et al., Kamoi et al., CRITIC).
- [vani_options_test.md](../Persona%20generator%20architecture/vani_options_test.md): on 6 synthetic sellers, rules + 1 wording call got 23/23 rule decisions right; an LLM deciding the settings got 16/23, with confident false reasons.

**The key structural fact.** PS07 (269K calls) used one voice and one style. Every call has the same voice, tone and pace, so the data has **zero variation in the treatment**. It can say which *sellers* convert, and which in-call *signals* (rush, confusion, language) predict outcomes. It cannot say which *voice/tone* works for which segment. No model, LLM or statistics, can recover a voice effect from data where the voice never changed (ASSUMED; this is the positivity/overlap requirement in causal inference, see Stage 2). Only new runs where persona choices vary produce that evidence.

---

## Q1. Stage 0 (cold start): rules/hypotheses as priors, LLM agent grounded in tables

### Takeaway
At cold start, the only trustworthy learning signal is PS07's *seller-side* evidence (memory, signals, outcomes). Persona *delivery* choices (voice gender, timbre, tone) have no outcome evidence and must be labelled hypotheses (GUESS). Our own test, plus the literature, says code should apply the rules and the LLM should not decide them. An "agent with tools" adds value only where the tool returns new, external information.

### Cited Findings
- On 6 synthetic sellers, rules applied in code + 1 Sarvam wording call: 23/23 key decisions correct, ~1.0 s, ~₹0.017/seller. One structured LLM call deciding the settings: 16/23, and validator-driven revisions only reached 17/23. Its wrong decisions came with plausible false reasons that no validator caught. (PROVEN in-repo) — [vani_options_test.md](../Persona%20generator%20architecture/vani_options_test.md)
- Without external feedback, LLMs struggle to self-correct, and performance sometimes degrades after self-correction (DOCUMENTED). — [Huang et al., arXiv 2310.01798](https://arxiv.org/abs/2310.01798)
- Self-correction works well when reliable external feedback is available (DOCUMENTED). — [Kamoi et al., arXiv 2406.01297](https://arxiv.org/abs/2406.01297)
- LLM-generated priors used to warm-start a contextual bandit reduced early regret by 14–20% in the original CBLI work (DOCUMENTED). — [Jump Starting Bandits with LLM-Generated Prior Knowledge, arXiv 2406.19317](https://arxiv.org/html/2406.19317v2)
- A 2026 follow-up: warm-starting stays effective up to ~30% label corruption, loses its advantage around 40%, and hurts beyond 50%. Under **systematic misalignment**, LLM priors can give **higher regret than a cold start** even with no added noise (DOCUMENTED, search summary). — [Jump start or false start, arXiv 2604.02527](https://arxiv.org/abs/2604.02527)
- Per-seller memory is our strongest PS07 lever: next-call meeting AUC 0.71 for memory vs 0.58 for profile; 4.4% meeting after Not Interested vs 21.7% after Meeting Fixed (PROVEN, aggregate, in-repo). — [learning-loops.md](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences (ASSUMED)
- **Data needed:** seller file + PS07 aggregates (segment outcome rates, signal rates, per-seller last-call memory), the voice catalogue, a rule/evidence table with tiers. No outcome data on persona choices exists, and none is needed to start.
- **Minimum volume:** none for decisions. For *rules mined from PS07*, the existing gate holds: n ≥ 200, CI excluding zero, holds on a time split.
- **What it can learn:** seller → plan-content rules (what to open with, objection order, language, brevity after rush). These are supported by PS07 because they are about *the seller*, not the voice.
- **What it cannot learn:** any voice/tone/gender effect. Rules like "₹1 Cr+ → authoritative voice" stay GUESS until Stage 2 data exists.
- **Role of the "agent with tools":** the tools (seller history, segment stats, similar sellers, catalogue) are fine as *retrieval*. The *decision* should be the rule engine. If the LLM is the policy, treat its output as a **prior** (like CBLI), and expect the false-start risk: if its priors are systematically wrong (stereotypes), it does worse than a neutral default.
- **Failure modes:** stereotype-as-prior (a confident LLM rationale for "rural → young warm female" is not evidence); rule decisions applied wrongly by an LLM (seen in our test); evidence-tier inflation (code must copy tiers).
- **Evaluate:** rule-decision correctness on a hand-labelled set (decided by code, so this checks the code); fit judge; distinctness (Mantel/Spearman ρ, 0.82 in A); evidence-link coverage by tier. None of these measure *outcomes*. Stage 0 cannot claim "this persona converts better".

### Gaps
- No public study found on LLM-generated priors for *voice persona* choices specifically.

---

## Q2. Stage 1: in-context learning from experience (retrieval, memory, evidence-table updates, prompt optimisation)

### Takeaway
Memory and retrieval of past experiences reliably improve LLM agents on *task-success* benchmarks with *verifiable* outcomes. Gains range from +24.6% to +51% relative (AWM) and up to +16 points (Agent KB). Prompt optimisation from traces (GEPA) beats RL at a fraction of the rollouts. All of this assumes the reward signal is reliable and the stored cases are representative. For VANI, Stage 1 can learn *plan content* and *per-seller adaptation* well, but it still cannot separate voice effects from seller effects unless Stage 2 varies the choices.

### Cited Findings
- **ExpeL** (AAAI 2024): the agent gathers experiences on training tasks, then either recalls successful trajectories by task similarity or extracts natural-language **insights**. Both boost performance, and performance improves as experience accumulates, with no parameter updates (DOCUMENTED). — [Zhao et al., arXiv 2308.10144](https://arxiv.org/abs/2308.10144)
- **Agent Workflow Memory** (ICML 2025): induces reusable workflows from past trajectories. +24.6% relative step success on Mind2Web and +51.1% relative success on WebArena; beats methods given human-written workflows by 7.9%. Online AWM beats baselines by 8.9–14.0 absolute points as the train-test gap widens (DOCUMENTED). — [Wang et al., arXiv 2409.07429](https://arxiv.org/abs/2409.07429); [PMLR](https://proceedings.mlr.press/v267/wang25bx.html)
- **Agent KB** (2025): a "Reason-Retrieve-Refine" pipeline over a shared, hierarchical experience base built from execution logs. On GAIA, up to +16.36 points overall. GPT-4.1 Level 2: 53.49% → 73.26%. Claude-3.7 Level 3: 38.46% → 57.69% (DOCUMENTED, search summary). — [Tang et al., arXiv 2507.06229](https://arxiv.org/abs/2507.06229)
- **LaMP** (ACL 2024): retrieving items from a user's own profile into the prompt improves every personalisation task. Fine-tuning with retrieval augmentation gave a 23.5% relative average gain (DOCUMENTED). — [Salemi et al., arXiv 2304.11406](https://arxiv.org/abs/2304.11406)
- **GEPA** (ICLR 2026 oral): reflective prompt evolution reads trajectories in natural language, proposes prompt updates and keeps a Pareto frontier. It beats GRPO by 6% on average (up to 20%) with up to 35× fewer rollouts; on IFBench, 678 rollouts gave 38.61% vs GRPO's 35.88% with 24,000. It beats MIPROv2 by over 10% (DOCUMENTED). — [Agrawal et al., arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
- **LLMs as in-context explorers:** only one configuration explored a simple bandit satisfactorily: GPT-4 with chain-of-thought **and an externally summarised history given as sufficient statistics**. Otherwise models showed "suffix" failures (stick with the recent option) or uniform behaviour. Raw history in the prompt was not enough (DOCUMENTED). — [Krishnamurthy et al., arXiv 2403.15371](https://arxiv.org/abs/2403.15371)
- Reflexion's gains came from an external signal (unit tests) (DOCUMENTED). — [Shinn et al., arXiv 2303.11366](https://arxiv.org/abs/2303.11366)

### Inferences (ASSUMED)
- **Data needed:**
  - a trace store per call: seller features, persona spec + rule ids, the voice/tone actually used, plan followed, switch log, post-call review labels, outcome (meeting, callback, NI), and a **version id** for the generator;
  - per-segment counters: successes/trials per (segment × persona option).
- **Bayesian evidence table (the safe core of Stage 1):** keep a Beta(α, β) per (segment × option) for binary outcomes. Prior from PS07 base rate with a small pseudo-count (e.g. 10–20 calls' worth) so early rows don't swing. Shrink sparse segments toward the parent segment (hierarchical / empirical Bayes). Show the posterior mean and 90% interval in the evidence table; tier = function of interval width. This is just arithmetic; the LLM reads it, never writes it.
- **Retrieval of similar cases:** retrieve *aggregate* rows and a few anonymised past-case summaries for similar sellers. Per Krishnamurthy et al., give the agent **summarised statistics** (n, rate, interval), not raw transcripts, or it will over-weight recent or vivid cases.
- **Insights (ExpeL/AWM style):** the post-call reviewer proposes rules ("sellers confused at high formality → ..."). Each candidate becomes a rule row only after code computes n, effect and CI and it passes the time split. This is the existing gate in learning-loops.md, and it is ExpeL insight extraction with a statistical filter.
- **Prompt optimisation (GEPA/DSPy):** good fit for *wording* prompts (opening, reasons) where an external metric exists (validator pass, fit judge calibrated to humans, later: outcome). Not for *decisions*. Low rollout counts (hundreds) make it feasible even offline.
- **Minimum volume (rough, ASSUMED arithmetic, two-sided α 0.05, 80% power):** to tell a 10% from a 15% meeting rate needs ~680 calls *per arm*; 10% vs 12% needs ~3,800 per arm. Multiply by the number of segments you want separate answers for. A few dozen hackathon calls distinguish nothing at the segment level; that matches learning-loops.md ("~20-point gains only").
- **What Stage 1 can learn:** per-seller adaptation (strongest), plan-content rules, wording that passes checks and reads better, signal → action mappings in the switcher.
- **What it cannot learn:** causal voice/tone effects, if the agent keeps choosing deterministically by segment. If "₹1 Cr+" always gets voice X, the voice effect is perfectly confounded with the segment.
- **Failure modes:**
  - *Self-reinforcing memory:* the agent retrieves its own past choices as "evidence" and repeats them (the [Chaney et al.](https://arxiv.org/abs/1710.11214) feedback loop, Q5).
  - *Reviewer bias:* an LLM post-call reviewer labelling "did the persona fit" has self-preference and sycophancy issues ([llm_architectures.md](../Persona%20generator%20architecture/llm_architectures.md) Q1). Gate on hard outcomes and human-checked samples.
  - *Insight drift:* insights accumulate and contradict each other. Version them, expire unconfirmed ones.
  - *Recency/suffix bias* when raw history is in context (Krishnamurthy et al.).
- **Evaluate:** time-split replay on PS07 for the seller-side rules (mine Apr–Jul, test Aug–Sep); held-out sellers for memory (next-call AUC); validator pass and calibrated fit judge for prompt changes. Report each version vs the previous on a **frozen** test set.

### Gaps
- No benchmark found where experience memory is applied to **persuasion/sales call personas** with noisy, delayed, binary business outcomes. All cited gains are on tasks with verifiable success (web navigation, QA, code).

---

## Q3. Stage 2: exploration + causal learning (bandits, Thompson sampling, LLM-as-policy, propensities, OPE, uplift)

### Takeaway
To learn which voice/tone works for which segment, the system must **randomise among plausible options and log the probability of each choice**. Thompson sampling over a small menu of persona options per segment is the standard, sample-efficient way to do this, and it beats greedy policies in LLM-based bandits. LLMs on their own explore poorly. Use a classic bandit (or LLM + explicit uncertainty) as the policy and keep the LLM for wording. Logged propensities make off-policy evaluation (IPS/DR) possible later. Report per-segment effects, because average gains can hide harm to subgroups.

### Cited Findings
- In contextual bandits with natural-language input, LLM bandits using **Thompson sampling** with uncertainty estimates (Laplace, dropout, epinets) beat **greedy** policies on real-world data (DOCUMENTED). — [Felicioni et al., arXiv 2404.02649](https://arxiv.org/abs/2404.02649)
- LLMs given bandit history in the prompt mostly fail to explore. Success needed external summarisation into sufficient statistics; the authors say fine-tuning or dataset curation "may be required" for LLM decision agents in complex settings (DOCUMENTED). — [Krishnamurthy et al., arXiv 2403.15371](https://arxiv.org/abs/2403.15371)
- Thompson-sampling-style active exploration also improves sample efficiency for online LLM alignment as a contextual dueling bandit (DOCUMENTED). — [Liu et al., Sample-Efficient Alignment, arXiv 2411.01493](https://arxiv.org/abs/2411.01493)
- LLM-generated priors cut early bandit regret 14–20% when aligned and hurt when systematically misaligned (DOCUMENTED). — [arXiv 2406.19317](https://arxiv.org/html/2406.19317v2); [arXiv 2604.02527](https://arxiv.org/abs/2604.02527)
- **Off-policy evaluation:** IPS reweights logged rewards by the propensity ratio and makes no reward-model assumption; doubly robust (DR) combines a reward model with IPS and is unbiased if either the model or the propensities are right; SNIPS reduces variance (DOCUMENTED, search summary). — [Off-Policy Evaluation from Logged Human Feedback, arXiv 2406.10030](https://arxiv.org/abs/2406.10030)
- **OPE for a real LLM agent** (7 users, 280 rated turns, health coaching): factorised decision heads (Tool / Style). A uniform heavy-tool policy raised the average value on logs but **harmed specific subgroups** (low health literacy / high self-efficacy). Authors recommend: freeze the generator and learn subgroup-aware *decision* components; use typed rewards (objective outcome + satisfaction); always report per-archetype metrics (DOCUMENTED). — [arXiv 2510.17173](https://arxiv.org/abs/2510.17173)
- Feedback loops in recommenders homogenise behaviour without increasing utility, and bias held-out evaluation; open-loop (random) exposure is the comparison (DOCUMENTED). — [Chaney, Stewart, Engelhardt, RecSys 2018, arXiv 1710.11214](https://arxiv.org/abs/1710.11214)

### Inferences (ASSUMED)
- **Design for VANI:**
  - **Arms:** a small menu per decision dimension, not the full grid. E.g. voice ∈ {2–3 catalogue voices covering the seller's language}, tone ∈ {neutral-warm, crisp-formal}, pace ∈ {normal, slower}. The full 8-setting grid is far too many arms for the data.
  - **Context / segments:** a few coarse segments (language zone × business type × turnover band), with hierarchical pooling.
  - **Policy:** Beta-Bernoulli Thompson sampling per (segment × arm), with priors from Stage 0/1 (and LLM priors only with a small pseudo-count, given the false-start result). Add a floor, e.g. every allowed arm ≥ 10% probability, to keep overlap for OPE and avoid lock-in.
  - **Guardrails before sampling:** arms that break rules (DNC, language mismatch, catalogue gaps, compliance) are removed by code. Per-seller memory overrides (e.g. a seller who complained about the voice) win over exploration.
  - **Log per call:** the arm chosen, **the probability it had**, the full arm distribution, policy version, segment, and outcome. Without logged propensities, later OPE is guesswork.
- **LLM-as-policy:** if the agent must "decide", have it output a *distribution* or a ranked shortlist, then let code sample (Thompson / ε-floor) and log the probability. Never let an LLM pick deterministically and call it exploration.
- **Uplift / heterogeneous effects:** once arms were randomised within segments, fit T-learner or causal-forest style uplift models on (seller features × arm) → outcome to find *which sellers* respond to which voice. Needs randomised data, and many thousands of calls (see volumes).
- **Minimum volume:** same power arithmetic as Stage 1, per segment × arm. Voice effects in persuasion studies are *small* (Q6), so realistic differences are a few points. Expect thousands of calls per segment before a voice rule moves from GUESS to MODERATE. Bandits cut the *cost* of learning (less traffic on bad arms) but not the requirement for enough data to be sure.
- **What it can learn:** causal effects of persona options on outcomes, per segment, under real conditions.
- **What it cannot learn:** effects for arms never tried in a segment (no overlap); long-term effects (seller fatigue across calls) unless the reward includes later calls; reasons *why* (the reviewer gives hypotheses only).
- **Failure modes:**
  - *Confounding through the seller:* if voice depends on anything other than logged context + randomness, OPE breaks. Log everything the policy saw.
  - *Feedback loops / premature convergence:* a bandit locks onto one voice per segment and stops learning; the floor and periodic resets prevent this.
  - *Non-stationarity / drift:* seasonality, list changes and novelty effects. Use discounting or sliding windows; re-check on a time split.
  - *Reward proxy:* "meeting fixed" can be gamed by an over-pushy plan that also raises DNC or complaints. Use a typed reward: meeting + no complaint/DNC + seller-reported satisfaction where available.
  - *Stereotype amplification:* a bandit that learns "segment X → female young voice" can encode and harden a stereotype, even if it is real in the data. Audit allocations, keep both genders in rotation where the catalogue allows (the existing ~80% skew alarm).
  - *Multiple comparisons:* many segments × arms → false winners. Pre-register a few hypotheses, correct for multiplicity.
- **Evaluate:** the A/B or bandit itself (online), plus OPE (SNIPS/DR) to score a candidate new policy on logged data before deployment, plus per-segment and per-subgroup results (the health-coaching finding). Keep a small always-random holdout (e.g. 5%) as an unbiased reference.

### Gaps
- No public study found of contextual bandits over **TTS voice / persona** choices in outbound sales or collections calls.
- No source checked for typical voice-effect sizes on B2B call conversion; the volumes above are arithmetic on assumed effect sizes.

---

## Q4. Stage 3: training (distillation, SFT on good trajectories, DPO/KTO, RL from outcomes, RLAIF, offline RL)

### Takeaway
Training is the last step, and only worth it once Stages 1–2 have produced logged, randomised, outcome-labelled decisions at volume. Two separate things can be trained: (1) a **small decision policy** (persona options from seller features) learned from randomised logs, which is cheap and auditable; (2) the **LLM's wording/plan behaviour**, tuned on high-reward trajectories (SFT, KTO with binary outcomes, DPO with pairs). Post-training can raise persuasiveness much more than personalisation does, but in a large study it also cut factual accuracy, so it needs strong guardrails. For VANI's rules (core agent must be Sarvam, no GPU, no time), training is out of scope for the hackathon; Stage 3 is a long-term path.

### Cited Findings
- **KTO** aligns a model from **binary desirable/undesirable labels** (no paired preferences), using a prospect-theory value function; reported to match or exceed preference-based methods (DPO) from 1B to 30B parameters (DOCUMENTED, search summaries). — [Ethayarajh et al., arXiv 2402.01306](https://arxiv.org/abs/2402.01306)
- **Post-training for persuasion** (Science 2025; 19 LLMs, 707 issues, 76,977 participants, 466,769 claims fact-checked): targeted post-training (SFT + reward modelling) increased persuasiveness by up to 51%; prompting strategies by up to 27%; **personalisation to age or politics gave only a negligible boost**; the most persuasive models were the **least accurate** (DOCUMENTED, search summary of paper and Oxford release). — [Hackenburg et al., arXiv 2507.13919](https://arxiv.org/abs/2507.13919); [Oxford news](https://www.ox.ac.uk/news/2025-12-11-study-reveals-how-conversational-ai-can-exert-influence-over-political-beliefs)
- GEPA beat GRPO RL by 6% on average with up to 35× fewer rollouts, i.e. prompt optimisation can be a cheaper substitute for RL when rollouts are expensive (DOCUMENTED). — [arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
- LaMP: fine-tuning with personalised retrieval augmentation gave a 23.5% relative average gain (DOCUMENTED). — [arXiv 2304.11406](https://arxiv.org/abs/2304.11406)
- The health-coaching OPE paper recommends **freezing the language generator** and learning only subgroup-aware decision heads (DOCUMENTED). — [arXiv 2510.17173](https://arxiv.org/abs/2510.17173)
- Krishnamurthy et al. suggest fine-tuning or dataset curation may be needed for LLMs to act as decision agents (DOCUMENTED). — [arXiv 2403.15371](https://arxiv.org/abs/2403.15371)

### Inferences (ASSUMED)
- **Order of training, cheapest first:**
  1. *Distil the decision policy* into a small model (logistic regression / gradient boosting / small contextual-bandit model) on randomised logs with IPS weights. Auditable, cheap, retrains in minutes. This replaces hand rules as data grows; the LLM keeps writing words.
  2. *SFT on high-reward trajectories* (openings, plans, wording) from calls with good outcomes **and** no guardrail violations. Risk: filtering on outcome copies seller-side luck (selection bias), so weight or balance by segment.
  3. *KTO* is the natural fit for call outcomes (meeting yes/no is a binary desirable label per call). *DPO* needs pairs, e.g. two openings tried on similar sellers.
  4. *RL from outcomes / offline RL* over multi-turn calls: highest potential, highest risk (reward hacking, credit assignment over turns, needs a simulator).
  5. *RLAIF* (an AI judge as reward): only for style/fit qualities, calibrated against humans, never as the sole reward for persuasion.
- **Requirements:** logged propensities (from Stage 2), randomised coverage of each option, a held-out time period and held-out sellers, a frozen evaluation set, and a guardrail suite (no invented prices/facts, compliance, DNC). Data volume: tens of thousands of outcome-labelled calls for the decision model to beat rules per segment; more for LLM tuning (ASSUMED, no source found for a threshold).
- **Platform constraint:** the core agent is Sarvam and Sarvam agents don't take our own LLM ([learning-loops.md](../../../wiki/projects/vani-hackathon/learning-loops.md)). So fine-tuning the *in-call* LLM depends on Sarvam offering fine-tuning; the decision model and offline wording generator can be ours.
- **Failure modes:**
  - *Reward hacking / accuracy trade-off:* optimising for meetings can learn pushy or inaccurate claims, as in the Science study's persuasion-accuracy trade-off.
  - *Distribution shift:* the trained policy moves off the logged data; OPE variance explodes where propensities were small.
  - *Stereotype hardening:* a trained model turns a weak correlation (e.g. region ↔ voice) into a fixed rule with no visible reason.
  - *Loss of auditability:* PS04 requires a reason and evidence tier per setting; a trained black-box loses that unless reasons are generated from features + effect sizes.
- **Evaluate:** OPE (DR/SNIPS) on held-out logs → small online A/B against the current policy → per-segment and per-subgroup harm metrics → guardrail violation rate (must be 0) → factual accuracy audit of wording.

### Gaps
- No source found giving data-volume thresholds for distilling an LLM decision agent into a small policy, or for outcome-based fine-tuning of sales-call agents.
- Did not verify KTO's numbers against the PDF (search summaries only).
- Whether Sarvam offers customer fine-tuning of `sarvam-105b` was not checked.

---

## Q5. Cross-stage failure modes and how to evaluate each stage

### Takeaway
The same few failures recur at every stage: the system learning from data it caused (feedback loop), mistaking seller effects for persona effects (confounding), optimising a proxy (reward hacking), turning stereotypes into rules, and drift. The defence is the same everywhere: randomisation with logged propensities, a frozen held-out set and time split, per-segment reporting, and code-owned guardrails.

### Cited Findings
- Feedback loops homogenise users without utility gains and bias held-out evaluation (DOCUMENTED). — [Chaney et al., arXiv 1710.11214](https://arxiv.org/abs/1710.11214)
- Average gains can hide subgroup harm; report per-archetype metrics (DOCUMENTED). — [arXiv 2510.17173](https://arxiv.org/abs/2510.17173)
- Persuasion-optimised models were less accurate (DOCUMENTED). — [arXiv 2507.13919](https://arxiv.org/abs/2507.13919)
- Systematically misaligned LLM priors can do worse than no prior (DOCUMENTED). — [arXiv 2604.02527](https://arxiv.org/abs/2604.02527)
- LLM judges have self-preference, position and verbosity biases; LLMs are sycophantic when challenged (DOCUMENTED, via in-repo note). — [llm_architectures.md](../Persona%20generator%20architecture/llm_architectures.md)

### Inferences (ASSUMED): summary table

| Stage | Data needed | Rough minimum | Can learn | Cannot learn | Main failure | Evaluate with |
|---|---|---|---|---|---|---|
| 0 Rules + grounded agent | Seller file, PS07 aggregates, catalogue | n ≥ 200 per mined rule | Seller-side rules, per-seller memory | Any voice/tone effect | Stereotype priors; LLM misapplies rules | Rule correctness, fit judge, distinctness, tier coverage |
| 1 Memory / retrieval / Bayesian tables / GEPA | Traces + outcomes + versions | Hundreds per segment for rough rates; ~700+/arm for 5-pt effects | Plan content, wording, per-seller adaptation | Causal voice effects if choices are deterministic | Self-reinforcing memory, reviewer bias, recency bias | Time-split replay, frozen test set, next-call AUC |
| 2 Bandit + propensities + uplift | Randomised arms + logged probabilities | Thousands per segment × arm for small effects | Causal persona effects per segment | Untried arms, long-term fatigue | Lock-in, drift, proxy reward, stereotype amplification | Online A/B, OPE (SNIPS/DR), random holdout, per-subgroup |
| 3 Training | Large randomised, outcome-labelled logs | Tens of thousands (ASSUMED) | Smooth policy over many features; better wording | Anything outside logged support | Reward hacking, accuracy loss, lost auditability | OPE → online A/B, guardrail rate 0, accuracy audit |

- **Honest hackathon claim:** VANI on 9–10 Oct is Stage 0 + a thin Stage 1 (per-seller memory, Bayesian table, gated rule updates). Stage 2 needs live traffic with randomised voices, which the event doesn't have. Say "the system logs propensities so Stage 2 can start on day one of production", not "it learned which voice works".

### Gaps
- No end-to-end case study found of a voice sales agent going through these stages with published numbers.

---

## Q6. Personalisation and voice/tone matching evidence: are segment hypotheses like "₹1 Cr+ → authoritative voice; rural → young warm female voice" supported?

### Takeaway
Weakly at best, and risky. Evidence on *personalising content* by demographics shows small or negligible gains in the largest, most recent studies (one debate study is the exception). Evidence on *voice* effects comes mostly from small online lab studies with US participants, synthetic voices and self-reported "purchase likelihood"; effects of gender/age are small and interact in non-obvious ways. Tone (positive/neutral vs negative) and delivery (moderate pace, natural pauses, lower pitch) have better support than gender. None of it was done in India, in Hindi/regional languages, or with B2B sellers. Mapping region or wealth to voice gender/age is a stereotype hypothesis with no direct evidence, and it carries reputational and fairness risk. Treat all such rules as GUESS and test them only via randomised Stage 2 runs.

### Cited Findings
- **Content personalisation:**
  - GPT-4 microtargeted political messages were persuasive, but **not statistically more persuasive than non-targeted messages** (PNAS 2024) (DOCUMENTED). — [Hackenburg & Margetts, PMC11181035](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11181035/)
  - In the 76,977-participant study, personalisation to age or politics gave a **negligible** boost; information density and post-training mattered much more (DOCUMENTED). — [Hackenburg et al., arXiv 2507.13919](https://arxiv.org/abs/2507.13919)
  - Counterpoint: in live multi-round debates, GPT-4 *with* sociodemographic personalisation had 81.7% higher odds of increasing agreement vs human opponents; without personalisation, +21.3% and non-significant (Nature Human Behaviour 2025) (DOCUMENTED, search summary). — [Salvi et al.](https://www.rivista.ai/wp-content/uploads/2025/05/s41562-025-02194-6.pdf)
  - LaMP: retrieving the user's **own past items** improves personalisation on all tasks (DOCUMENTED). This supports *per-user memory* personalisation, not demographic stereotypes. — [arXiv 2304.11406](https://arxiv.org/abs/2304.11406)
- **Voice gender/age/tone:**
  - 335 US Prolific participants, synthesised Microsoft voices, product-review clips, 7-point purchase-likelihood ratings: **positive (large effect) and neutral (medium) tones** beat negative tones; **middle-aged male and younger female** voices were rated more persuasive than younger male or middle-aged female (**small effect**). Effects worked through perceived persuasiveness. Limitations: US only, synthetic, online, binary gender, older voices dropped because ages were hard to tell apart (DOCUMENTED). — [arXiv 2405.04791](https://ar5iv.labs.arxiv.org/html/2405.04791)
  - Male synthetic speech was rated preferable to female synthetic speech, but **persuasion did not differ** between human and synthetic speech (DOCUMENTED, search snippet). — [Social perception of male and female computer synthesized speech, Penn State](https://pure.psu.edu/en/publications/social-perception-of-male-and-female-computer-synthesized-speech/)
  - Telephone survey introductions (1,380 recordings, U. Michigan ISR): agreement was highest at a **moderate speaking rate (~3.5 words/s)** with moderate pausing; perfectly fluent, no-pause delivery had the lowest success ("too scripted"); median pitch was lower in successful contacts for both male and female interviewers; pitch variability helped female but hurt male interviewers (DOCUMENTED, search summary). — [ScienceDaily summary](https://www.sciencedaily.com/releases/2011/05/110515122507.htm)
  - In customer-service voice studies, low pitch and moderate speaking rates were preferred for trust (student thesis; DOCUMENTED, weak source). — [U. Twente thesis](https://essay.utwente.nl/essays/100878)
  - Male CEOs with deeper voices ran larger firms: −22.1 Hz pitch ↔ +$440M firm size, +$187K pay (792 S&P 1500 CEOs; correlational, about the *speaker's* career, not listener persuasion) (DOCUMENTED). — [Mayew, Parsons & Venkatachalam 2013](https://people.duke.edu/~wmayew/Bio/MillionDollarVoice.pdf)
  - An analysis of AI voice-phishing calls reported that persuasiveness of the **script**, not the voice, drove compliance (each step up in persuasiveness → 2.58× odds) (DOCUMENTED, news summary; primary not fetched). — [Help Net Security](https://www.helpnetsecurity.com/?p=377915)
- **Stereotype risk:** UNESCO's "I'd Blush If I Could" (2019) found female-by-default voice assistants signal women as "obliging, docile and eager-to-please helpers" and recommended ending female-by-default voices (DOCUMENTED). — [Dezeen summary](https://www.dezeen.com/2019/05/24/united-nations-voice-assistants-gender-biases-siri-alexa/)
- "Persona collapse": the models with the highest fidelity to individual personas produce the most stereotyped populations (DOCUMENTED, via in-repo note). — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)

### Inferences (ASSUMED)
- **"₹1 Cr+ → authoritative voice":** partial, indirect support for *delivery* (lower pitch, moderate pace, crisp formal tone) being trusted and perceived as competent. No support for tying it to a *gender*. Reasonable as a GUESS-tier rule on **tone/pace/formality**, voice-gender-neutral. Test by randomising.
- **"Rural → young warm female voice":** no direct evidence. The one study with a gender × age effect (younger female and middle-aged male more persuasive) is US-only, small-effect, synthetic, and about consumer products. Mapping *rural* to a young female voice is a stereotype (and UNESCO flags female-as-helper defaults). High risk for judges' Q&A and fairness review; low expected gain. Recommend: **don't ship it as a rule**. Keep "warm tone, slower pace, simpler words, regional language" for low-familiarity sellers, which is supported by the language/confusion signals in PS07, and leave voice gender to catalogue coverage + rotation.
- **What the evidence does support for VANI:** per-seller memory (LaMP, PS07 AUC 0.71); language match; positive/neutral tone over negative; moderate pace with natural pauses rather than over-fluent scripted delivery; content quality over demographic tailoring (Hackenburg 2024/2025, phishing analysis).
- **Rule of thumb for the evidence table:** voice gender and age rules = GUESS until randomised Stage 2 data exists; tone/pace rules = WEAK (indirect lab/survey evidence, not India); language and per-seller memory rules = MODERATE/STRONG from PS07.

### Gaps
- No India-specific, Hindi/regional-language, or B2B study found on voice gender/age effects in sales or service calls.
- Primary sources for the Michigan interviewer-voice study and the voice-phishing analysis were not fetched; figures come from summaries.
- No study found that tests matching voice demographics *to listener demographics* (homophily) in call outcomes.
