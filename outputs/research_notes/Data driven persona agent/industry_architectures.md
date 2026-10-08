# Industry architectures: data prep → per-customer decision → data flywheel (as of 2026-10-08)

Tags: **DOCUMENTED** = vendor docs, engineering blog or paper describes the mechanism. **VENDOR CLAIM** = self-reported results or marketing. **ASSUMED** = my inference, or from memory without a source fetched this session.
Scope: decisioning / bandits / contact-centre pairing / agent flywheels. Voice platforms and sales-prep agents are already in `outputs/research_notes/Persona generator architecture/industry_practice.md`, so they are not repeated here.

## Q1. Next-best-action / real-time decisioning (Pega, Salesforce, Adobe): what code prepares, what decides, what is logged, how it learns

### Takeaway
Classic NBA engines are a fixed funnel: code builds the customer profile, **hard eligibility rules filter** the candidate actions, a **per-action adaptive model** scores propensity, and an **explicit arbitration formula** combines propensity with business value and levers. Learning is continuous and per action. Every served decision plus its response is the training row. New actions get exploration through **Thompson sampling with a starting prior**. Salesforce's newer Agentforce/Atlas puts an **LLM ReAct planner** on top. Its "learning" is configuration (topics, instructions, actions) plus grounding data, not an outcome-trained model.

### Cited Findings
- **Pega CDH arbitration (DOCUMENTED):** priority = **P × C × V × L**. P = propensity (AI-predicted likelihood of a positive response), C = context weighting (situational), V = business value of the action, L = business levers (line-of-business priority). The top-priority actions are selected after eligibility/applicability/suitability filtering. — [Pega Academy: action arbitration](https://academy.pega.com/node/47811); [Pega Academy](https://academy.pega.com/node/51771)
- **Pega cold start for new actions (DOCUMENTED):**
  - Propensity for new actions is "not reliable as they would have too few or no customer responses".
  - Pega uses **Thompson sampling** to "add some noise to the propensity values, with a lot of noise added if the models have received very few responses".
  - Less mature actions are partly filtered by maturity, and the remaining ones have their propensity adjusted by Thompson sampling.
  - Adjusted propensity is a weighted average with **StartingPropensity (weight 1) and StartingEvidence (weight 25)**, so new actions get "a fighting chance".
  - This applies to both inbound and outbound.
  - — [Pega docs: model learning for new actions](https://docs-previous.pega.com/node/2307541) (search snippet; the page redirected and was not fully read); [Pega: Predict Action Propensity strategy](https://docs-previous.pega.com/node/2411056)
- **Pega adaptive model internals (ASSUMED, from memory, not re-fetched):**
  - One online model per action × channel × direction ("model context").
  - Naive-Bayes-style scorecard over automatically binned predictors.
  - Predictors become active only above a performance (AUC) threshold.
  - Every response updates bin counts incrementally (no batch retrain).
  - Monitoring via positives/responses/AUC per model; Pega publishes the open-source `pega-datascientist-tools` for this ([GitHub](https://github.com/pegasystems/pega-datascientist-tools)).
- **Salesforce Atlas / Agentforce (DOCUMENTED, engineering blog):**
  - Agents are defined by Role, Data, Actions, Guardrails and Channel.
  - "State acts as both short-term and long-term memory".
  - System-2 inference-time reasoning with advanced retrieval.
  - Asynchronous, event-driven, graph-based orchestration.
  - Declarative **YAML** configuration.
  - A "concierge orchestrator" coordinates agents.
  - **VENDOR CLAIM:** "2x increase in response relevance and 33% increase in end-to-end accuracy" vs competitors.
  - — [Salesforce Engineering: Inside Atlas](https://engineering.salesforce.com/inside-the-brain-of-agentforce-revealing-the-atlas-reasoning-engine/)
- **Atlas loop and grounding (secondary sources, not Salesforce docs):**
  - Reason–act–observe (ReAct) loop.
  - Input is classified to a **topic**, which carries instructions, rules and the allowed actions (Flows, Apex, prompt templates, APIs).
  - Grounding comes from Salesforce/Data Cloud/MCP.
  - — [ITConvergence](https://www.itconvergence.com/blog/how-does-agentforce-reason-inside-salesforces-atlas-reasoning-engine/); [eesel.ai](https://www.eesel.ai/blog/salesforce-agentforce)
- **Einstein Next Best Action, legacy (ASSUMED, not fetched):** recommendations are records; a Strategy Builder pipeline filters, sorts and optionally scores them with an Einstein prediction; accept/reject reactions are logged.
- **Adobe Journey Optimizer decisioning (DOCUMENTED):**
  - Ranking options: priority, a ranking formula, or an AI model.
  - **Auto-optimization** is non-personalised and optimises on "global" offer performance (clicks → conversion).
  - **Personalized optimization** trains on customer data against a business goal.
  - Conversion rate = conversions / impressions.
  - "Ranking method testing" A/B-tests formulas against models.
  - — [AJO AI models](https://experienceleague.adobe.com/en/docs/journey-optimizer/using/decisioning/experience-decisioning/experience-decisioning-rankings/experience-decisioning-ai-models/ai-models); [AJO legacy AI models](https://experienceleague.adobe.com/en/docs/journey-optimizer/using/decisioning/offer-decisioning/rankings/ai-models/ai-models)

### Inferences
- **ASSUMED:** NBA engines keep three separate things apart: **eligibility (hard rules)**, **propensity (learned)** and **value/levers (business-set)**. In the VANI shape, the LLM agent shouldn't merge them. Rules filter the voice catalogue (language coverage, DNC, guardrails). A learned table supplies "propensity" per persona dimension. The LLM explains, composes and fills in what the data doesn't cover.
- **ASSUMED:** Pega's StartingPropensity/StartingEvidence is exactly the mechanism for the team lead's hypotheses. "₹1 Cr+ → authoritative senior voice" goes in as a **prior with small evidence weight**, not a hard rule. Data then overrides it.
- **ASSUMED:** Atlas shows the LLM-agent pattern in production is **topic-scoped tools + declarative config + guardrails**. Its improvement loop is humans editing topics and instructions from logs. That matches VANI's "rules/evidence/memory" stage.

### Gaps
- Pega's adaptive-model docs page didn't render, so the naive-Bayes and binning details are ASSUMED.
- No public documentation on whether Agentforce learns from outcomes automatically. It appears not to (config plus evaluation tooling), but that isn't confirmed.
- No independent lift numbers for Pega, Adobe or Salesforce were found this session.

## Q2. Content/treatment optimisation and bandits (Optimizely, Statsig, Persado, Aampe; Braze/Movable Ink/Phrasee)

### Takeaway
Production per-user treatment selection is mostly **contextual bandits over a human-curated catalogue of variants**: LinUCB or Thompson sampling, retrained hourly to nightly, always compared against random or holdout traffic. The closest published match to VANI is Aampe's peer-reviewed "agentic personalisation" (arXiv 2506.16429). It runs one agent per user, **decomposes the action space into dimensions such as tone-of-voice**, keeps a Beta posterior per user × action, seeds cold start with empirical-Bayes priors from similar users, and **deliberately does not let an LLM generate content**.

### Cited Findings
- **Optimizely CMAB (DOCUMENTED):** selects a variation per user from user attributes and past responses, balancing exploration and exploitation, with unlimited attributes from client, API or third-party sources. — [Optimizely docs](https://docs.developers.optimizely.com/feature-experimentation/docs/run-contextual-multi-armed-bandits); [Optimizely support](https://support.optimizely.com/hc/en-us/articles/29328842964109)
- **Statsig Autotune AI (DOCUMENTED):**
  - Algorithm: a LinUCB variant ("disjoint model", Li, Chu, Langford & Schapire): one model per variant, L2 logistic regression (or ridge for continuous outcomes), choosing the upper end of a 95% CI.
  - Low-traffic variants get higher CIs, which is the "bounce-back mechanism".
  - **Models update hourly.** Changing the model definition resets the data.
  - Training sample: a flat number of samples per variant, preferring recent ones (per day over the last two weeks), and strictly preferring the **explore dataset**.
  - Monitoring: random vs targeted traffic performance, with coefficients visible.
  - Categorical features are one-hot encoded.
  - — [Statsig methodology](https://docs.statsig.com/autotune/contextual/methodology); [Statsig contextual bandit](https://docs.statsig.com/contextual-bandit)
- **Aampe, agentic per-user personalisation (DOCUMENTED, arXiv paper by the vendor):**
  - One independent agent per user chooses message content, timing and channel (email, push, in-app, WhatsApp, SMS).
  - The action space is split into modular sets: **tone-of-voice, emoji usage, value proposition, incentive**.
  - Thompson sampling uses a Beta-Bernoulli posterior per user-action, sampling an ITE (individual treatment effect) estimate per action.
  - **Cold start:** an "empirical Bayes prior… based on behaviour from similar users", inspired by user-based collaborative filtering.
  - The reward is a weighted sum of goal and proxy events with exponential temporal decay.
  - Content comes from marketer-curated catalogues, explicitly to "avoid problems of confabulation… with Large Language Models".
  - **Evaluation:** a 3-week RCT on **6.4M users**, using DiD (difference-in-differences) plus interrupted time series.
  - **Results:**
    - intent +0.7% to +2.45%;
    - conversion +0.07% to +0.48%;
    - GMV +14% to +43% relative;
    - 99% CIs exclude zero.
    - Self-reported by the vendor, but an RCT, so stronger than a VENDOR CLAIM.
  - — [arXiv 2506.16429](https://arxiv.org/html/2506.16429v1)
- **Persado (VENDOR CLAIM):**
  - A knowledge base of ">100 billion language permutations tagged with emotional and motivational metadata", scored against ">40 billion impressions", from data on 1.2B consumers.
  - LLMs are "constantly trained on marketing messages and their subsequent performance".
  - It uses a patented experimentation approach.
  - — [BusinessWire 2023](https://www.businesswire.com/news/home/20230816302368/en/New-Persado-Essential-Motivation-AI-Solution-Empowers-Marketers-to-Instantly-Generate-Better-Performing-Messages-Across-Channels); [Unite.ai](https://www.unite.ai/?p=206553)
- **LLM priors for bandits (DOCUMENTED, research):** prompting an LLM to simulate preferences gives a pre-training dataset that "jump-starts" a contextual bandit and reduces early regret. — [arXiv 2406.19317](https://arxiv.org/html/2406.19317v2)
- **Braze Intelligent Selection/Canvas, Movable Ink Da Vinci, Phrasee/Jacquard (ASSUMED, not fetched):** the same pattern. A bandit allocates traffic across marketer- or LLM-generated variants inside brand-language guardrails. Results are vendor claims only.

### Inferences
- **ASSUMED:** Aampe's decomposition is the key design idea for VANI. Treat **voice (gender/timbre), language, pace, tone/formality and opening** as separate dimensions, each with its own posterior per segment. Joint persona combinations explode, so 3 voices × 3 paces × 3 tones = 27 arms, each starved of data. Per-dimension learning assumes the dimensions interact little, which is a known simplification.
- **ASSUMED:** For credibility, copy two things: Statsig's "prefer explore data" and Aampe's RCT. **Learning needs logged randomisation.** If the agent always picks a female voice for rural sellers, you can never learn whether that was right.
- **ASSUMED (power arithmetic):** with a baseline meeting rate around 10%, detecting +3 pp at 80% power and α=0.05 needs roughly 1,700–1,800 calls per arm. Aampe needed 6.4M users to see sub-1% conversion lifts. Hackathon-scale calls can't validate segment → voice rules. Only PS07 replay and post-event live traffic can.

### Gaps
- Braze, Movable Ink and Phrasee mechanism docs were not fetched.
- Persado's experimental design is not public beyond the patent reference.
- Optimizely's CMAB algorithm and retrain cadence were not found on the page snippets.

## Q3. Contact-centre AI: pairing/routing and behaviour-outcome mining (Afiniti, Genesys, Cresta, Observe.AI, NICE)

### Takeaway
Afiniti and Genesys predictive routing answer "which agent for which customer". That is the human analogue of "which voice for which seller". They are **supervised outcome models over pair features, retrained nightly or weekly, with protected attributes explicitly excluded, and proven by built-in ON/OFF benchmarking**. Cresta and Observe.AI-style conversation intelligence mines **which behaviours correlate with outcomes** and turns them into coaching and playbooks. That's the analogue of VANI's post-call review → rules.

### Cited Findings
- **Afiniti (DOCUMENTED, vendor's responsible-AI page):**
  - Models "predict the outcome of all possible caller/agent pairings based on previous similar interactions" and are **refreshed nightly**.
  - **Inputs:**
    - telephony;
    - CRM/journey;
    - outcomes;
    - third-party consumer data;
    - agent experience, shift, compensation and training.
  - Predictors include caller tenure/history/profile/intent, agent experience/shift, offers, product mix and competitor information.
  - **Excludes** agent surveys, **protected-class data** and scraped data. Data stays behind the client firewall.
  - — [Afiniti: how it works](https://www.afiniti.com/responsible-ai/how-it-works/)
- **Afiniti benchmarking:**
  - **DOCUMENTED:** AI cycled ON/OFF in short alternating periods throughout the day.
  - **VENDOR CLAIM (secondary):** typically **80% ON / 20% OFF**. It is said to control for agent mix, campaigns and even weather. The patent covers benchmarking pairing strategies.
  - — [Afiniti](https://www.afiniti.com/?p=20685); [Justia patent 20210241201](https://patents.justia.com/patent/20210241201); [Telco Magazine](https://telcomagazine.com/technology-and-ai/power-afiniti-behavioural-pairing-technology)
- **Genesys Cloud Predictive Routing (DOCUMENTED):**
  - Uses **white-box** models with feature importance.
  - Agent features: skills, tenure, department, certificates, AHT (average handle time). Customer features: e.g. interaction frequency over 30 days.
  - **No PII; no gender or nationality.**
  - Features are refreshed daily and **models retrain weekly**. Data is kept for under 90 days.
  - It acknowledges "temporal bias".
  - It has built-in A/B testing to show KPI uplift, and supports custom KPIs (sales or service: NPS, CSAT, FCR, AHT, etc.).
  - — [Genesys: use of AI in predictive routing](https://help.genesys.cloud/articles/use-of-ai-in-predictive-routing/); [Genesys use case SL06](https://all.docs.genesys.com/UseCases/Public/PureEngage/SL06); [Genesys custom KPIs](https://help.genesys.cloud/announcements/genesys-cloud/predictive-routing-supports-customer-defined-business-outcomes-with-custom-kpis/)
- **Cresta (VENDOR CLAIM / product pages):**
  - Models "detect and correlate conversation outcomes… with agent behaviors" and find the tactics "proven to drive" sales and retention.
  - Coaching actions are prioritised per agent by expected impact.
  - AI Analyst answers natural-language questions over conversations.
  - — [Cresta conversation intelligence](https://cresta.com/conversation-intelligence); [CustomerThink on AI Analyst](https://customerthink.com/cresta-unveils-ai-analyst-empowering-organizations-to-uncover-insights-from-customer-conversations-at-unparalleled-speeds/)
- **Observe.AI, NICE Enlighten (ASSUMED, not fetched):** the same "auto-score every call against behaviour rubrics → correlate with outcomes → coach" loop. NICE Enlighten markets behaviour models such as empathy and ownership, trained on large interaction corpora.

### Inferences
- **ASSUMED:** Afiniti's exclusion list matches our existing guard. VANI picks the **bot's** voice; it never infers seller gender or protected traits. Rural/turnover segments are fine as features, but "₹1 Cr+ → senior male voice" needs an audit for gender skew, which is already in learning-loops ("audit >80% skew").
- **ASSUMED:** The ON/OFF benchmark is the cheapest credible proof for VANI after the event. Keep a fixed fraction of calls (for example 20%) on the default persona or a random persona, logged as such. Lift = agent persona vs holdout.
- **ASSUMED:** Afiniti and Genesys learn **pair-level outcome models offline** (nightly/weekly), not in-call. That validates the team's "nothing learns during a call" decision.
- **ASSUMED:** Cresta's behaviour → outcome mining is the template for B10/B11: the reviewer labels behaviours, an aggregate job correlates them with outcomes, and the result becomes a candidate rule with an evidence tier.

### Gaps
- Afiniti's exact model class isn't public, and its lift numbers (often cited as ~4–5% revenue) weren't verified this session. No independent evaluation was found.
- Genesys docs don't state a minimum data threshold or cold-start behaviour.
- Observe.AI and NICE were not fetched.

## Q4. "LLM agent + data flywheel" reference architectures (NVIDIA blueprint, LLM + bandit hybrids)

### Takeaway
NVIDIA's Data Flywheel blueprint is the canonical "agent flywheel". It **logs every LLM request/response with a `workload_id`**, curates eval and fine-tune sets from those logs, compares base vs in-context-learning vs LoRA variants with an LLM judge, and leaves **promotion as a human decision**. Its goal is cheaper or smaller models for the same decision, not better outcomes. Outcome-driven improvement comes from bandit/NBA layers. Hybrid designs use the LLM for candidates, priors and explanations, and the statistical layer for choosing and learning.

### Cited Findings
- **NVIDIA Data Flywheel Blueprint (DOCUMENTED):**
  - **Log schema in Elasticsearch:** `timestamp`, `workload_id` ("primary key for slicing, deduplication, and dataset creation"), `client_id`, and the full OpenAI-format request and response.
  - **Pipeline:**
    1. Dedupe the logs.
    2. Do a class-aware stratified split by tool type.
    3. Store in NeMo Datastore.
    4. Run experiments: **base** (replay prompts), **ICL** (few-shot drawn from traffic, random or semantic-similarity), **customized** (LoRA SFT).
    5. Score with an LLM-as-judge similarity metric in [0,1].
  - "Think of the Flywheel as a flashlight, not an autopilot. Promotion to production… remains a human decision."
  - **VENDOR CLAIM:** "reduce inference costs by up to 98.6%" in tool-calling cases.
  - — [NVIDIA-AI-Blueprints/data-flywheel](https://github.com/NVIDIA-AI-Blueprints/data-flywheel)
- **LLM + bandit hybrids (DOCUMENTED, research):**
  - LLM-simulated preferences as bandit pre-training reduce early regret — [arXiv 2406.19317](https://arxiv.org/html/2406.19317v2)
  - An RL + LLM framework for automated A/B tests: an LLM generates variants and RL allocates them — [summary](https://sotaverified.org/papers/a-reinforcement-learning-enhanced-llm)
- **Counter-pattern (DOCUMENTED):** Aampe's production agent keeps LLMs out of content generation and runs the decision on Thompson sampling — [arXiv 2506.16429](https://arxiv.org/html/2506.16429v1).

### Inferences
- **ASSUMED:** The NVIDIA flywheel's useful part for VANI is the **logging discipline**: one record per agent call keyed by workload (`persona_decision`, `post_call_review`, `switch_judge`), with full tool calls and outputs. That later enables (a) replay of decisions against new rules or prompts and (b) eventually distilling the decision agent into a small model or a plain lookup table. Training stays "later/optional", matching the team lead's plan.
- **ASSUMED:** The LLM-judge-similarity metric measures imitation, not outcome. VANI's flywheel must join decisions to **call outcomes** (meeting fixed, engagement, signals). Otherwise it learns to copy itself.

### Gaps
- No public production case was found where an **LLM agent with tools** is the per-customer decider *and* is improved from outcomes automatically. Every outcome-learning system found uses a statistical layer (Bayes, bandit, supervised model) for the learning part.
- The cost-reduction figure is the only NVIDIA result. There are no outcome results.

## Q5. Synthesis: common reference architecture and what VANI should copy

### Takeaway
Every system found has the same five layers:

1. Deterministic feature/profile prep.
2. Hard eligibility rules.
3. A learned scorer per action (or per action dimension) with priors and exploration.
4. Arbitration that combines score with business value/levers.
5. A decision log joined to delayed outcomes that feeds periodic, gated updates, with a holdout to prove lift.

LLM agents (Atlas) sit **on top** as planner/composer with scoped tools. In the systems found, they are not the thing that learns from outcomes. VANI's proposed shape fits this well if the LLM agent **reads** learned statistics through tools and **writes** a structured, logged decision. The rules/evidence/posterior tables do the learning.

### Cited Findings
- Eligibility → propensity → P×C×V×L arbitration; Thompson sampling with starting evidence — [Pega Academy](https://academy.pega.com/node/47811); [Pega docs](https://docs-previous.pega.com/node/2307541)
- Decomposed tone-of-voice dimension, per-user Beta posteriors, similar-user priors, curated catalogue, RCT proof — [arXiv 2506.16429](https://arxiv.org/html/2506.16429v1)
- Hourly retrain, explore-data preference, random vs targeted monitoring — [Statsig](https://docs.statsig.com/autotune/contextual/methodology)
- Pairing outcome models, protected-attribute exclusion, nightly/weekly retrain, ON/OFF or A/B proof — [Afiniti](https://www.afiniti.com/responsible-ai/how-it-works/); [Genesys](https://help.genesys.cloud/articles/use-of-ai-in-predictive-routing/)
- `workload_id` logging, replay/ICL/LoRA experiments, human promotion — [NVIDIA](https://github.com/NVIDIA-AI-Blueprints/data-flywheel)
- LLM planner with topics, actions, guardrails and declarative config — [Salesforce Engineering](https://engineering.salesforce.com/inside-the-brain-of-agentforce-revealing-the-atlas-reasoning-engine/)

### Inferences: what VANI should copy (all ASSUMED)

**Reference shape mapped to VANI:**

| Layer | Industry | VANI block |
|---|---|---|
| Profile prep | Data Cloud / AEP profile, Pega data flows | B1 script: seller features, history, memory, missing-field flags |
| Eligibility | Pega engagement policies, Sierra rules | Code: language → voice-catalogue coverage, DNC, AI disclosure, guardrails; drop ineligible personas *before* the agent sees them |
| Scorer with prior | Pega adaptive + StartingEvidence; Aampe Beta posteriors | **Evidence table**: per segment × dimension (voice, language, pace, tone, opening, playbook) → α/β counts + tier; team-lead hypotheses enter as priors (e.g., worth 10–25 pseudo-calls), PS07 aggregates as stronger priors |
| Decider | Pega arbitration; Atlas LLM planner | **LLM agent (Sarvam) with tools**: `get_seller`, `segment_stats` (returns posteriors + n + tier), `similar_sellers` (empirical-Bayes neighbours), `rules`, `voice_catalogue`. Outputs a schema-validated spec, a cited reason per field (rule/evidence ID) and a confidence |
| Exploration | Thompson sampling / UCB / ON-OFF | Code, not the LLM: with probability ε (or a Thompson draw on low-n dimensions), override one dimension; plus a fixed **holdout** (e.g., 10–20% default persona) |
| Decision log | Pega interaction history; NVIDIA workload logs | One row per call: `policy_version`, features snapshot, eligible set, agent tool calls, chosen levels, **whether each dimension was agent-chosen / explored / holdout and its selection probability**, LLM I/O |
| Outcome join | Delayed responses (Pega), reward with decay (Aampe) | Post-call: Sarvam output variables + B10 review labels (signals, fit, persona-mismatch) + later outcomes (meeting, next-call result); reward = weighted sum, as in Aampe |
| Update | Online Bayes (Pega), hourly (Statsig), nightly (Afiniti), weekly (Genesys) | Batch after each run/day: update α/β counts → recompute tiers → candidate rule edits from reviewer → **gate** on frozen set + time split → new version; per-seller memory updated directly |
| Proof | Afiniti ON/OFF, Genesys A/B, Aampe RCT | Agent persona vs holdout on meeting rate / signal metrics; report n and CI; say "not yet significant" honestly |
| Training (later) | NVIDIA LoRA distillation | Optional: distil agent decisions into a small classifier or lookup once logs exist; human promotes |

**Specific recommendations:**
1. **Separate decide from learn.** The agent decides; the evidence table learns. The agent must quote posteriors from `segment_stats`, never "remember" outcomes in free text. This keeps learning auditable and stops a drifting prompt from being the model.
2. **Log selection probabilities.** Without propensity or explore flags, the accumulated data can't fairly evaluate a new policy offline (inverse-propensity scoring). That's the most common thing teams forget and the hardest to backfill.
3. **Learn per dimension, not per persona.** Copy Aampe's modular action space so each dimension gets enough data. Add interaction terms only when a dimension pair has a large n.
4. **Treat segment hypotheses as priors plus experiments.** Examples: "₹1 Cr+ → authoritative senior", "rural → young warm female". Give each a StartingEvidence-style weight, explore around them, and let data overturn them. Run the gender-skew audit and keep the "never infer the seller's gender" guard (Afiniti and Genesys both exclude protected attributes).
5. **Cold start ladder.** Seller memory → similar sellers (empirical Bayes) → segment prior from PS07 → team-lead hypothesis prior → default persona. Optionally add LLM-simulated priors (arXiv 2406.19317), labelled as such and weighted lowest.
6. **Keep learning out of the call** (Afiniti nightly, Genesys weekly). That's already decided.
7. **Be honest about scale.** Segment → voice effects need roughly 1,000+ calls per arm. Pitch the hackathon as "architecture plus PS07-replay evidence", with the live flywheel as what happens after.

### Gaps
- No public example of exactly "LLM agent + tools picks a voice persona per customer and learns from outcomes" was found. The design is a composition of the patterns above, and that composition is ASSUMED.
- Independent (non-vendor) lift evidence exists only for Aampe (self-run RCT, peer-review status unknown). Everything else is a vendor claim.
- The interaction between voice dimensions (e.g., gender × tone) is untested anywhere public, so the per-dimension independence assumption is unverified.
