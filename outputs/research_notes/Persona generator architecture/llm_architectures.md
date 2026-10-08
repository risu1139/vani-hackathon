# LLM architectures for generating a grounded, structured, per-seller persona spec (as of 2026-10-08)

Tags: **DOCUMENTED** = a paper or official doc fetched or searched this session says this. **ASSUMED** = our inference for PS04. No customer data is used here.

Read alongside:
- [industry_practice.md](industry_practice.md): industry uses P1 (template + variables) plus P3 (a library-grounded LLM) plus a P5 checker. Free agents are rare.
- [generator_loop.md](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md): rule mining, then GEPA on the wording prompt.
- [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md): persona collapse; a discrete grid chosen by rules; Mantel, entropy and Hamming metrics.

This note does not repeat those. It adds the research case on rules vs one call vs RAG vs an agent loop, on attribution, and on the evaluation of the generator itself.

Binding PS04 requirements:
- a persona per seller;
- a reason per setting, tied to seller data;
- an evidence-strength label;
- missing fields fall back to defaults with lower confidence;
- facts, prices and compliance never change;
- scoring is fit 25 / switches 25 / distinctness 20 / voice 15 / evidence 15.

Source: [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md).

---

## Q1. What does 2023–2026 research say about rules vs a single call vs agentic generation for structured, grounded output? Measured gains and failure modes

### Takeaway
Iterative loops (self-refine, reflexion, critique) give real, measured gains **only when the feedback comes from outside the model**: tests, tools, validators, retrieval. Intrinsic self-critique, where the same model reviews its own output with no new signal, gives little or no gain and sometimes makes things worse. LLM judges inside the loop add their own biases: self-preference, position, verbosity, and sycophantic over-correction. Anthropic's own guidance is to start with one optimised call plus retrieval and add a workflow or agent only when it measurably helps.

For PS04, the loop is worth having only where a **code validator or retrieved evidence** supplies the feedback.

### Cited Findings

**Self-correction (DOCUMENTED)**
- **Self-Refine** (NeurIPS 2023): one LLM is generator, critic and refiner. Across 7 tasks, from dialogue response to math, on GPT-3.5, ChatGPT and GPT-4, it improved task performance by about 20% absolute on average over one-step generation. No training is needed. — [Madaan et al.](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract.html)
- **Counter-evidence, "LLMs Cannot Self-Correct Reasoning Yet"** (ICLR 2024, Google DeepMind / UIUC):
  - Without external feedback, LLMs struggle to self-correct, and performance sometimes *degrades* after self-correction.
  - Earlier gains often came from oracle labels, or from a weak first prompt.
  - Multi-agent debate does no better than self-consistency at an equal number of responses.
  - — [Huang et al., arXiv 2310.01798](https://arxiv.org/abs/2310.01798)
- **Critical survey** (TACL 2024):
  1. No prior work shows successful self-correction with feedback from prompted LLMs, except on tasks unusually suited to it.
  2. Self-correction works well when **reliable external feedback** is available.
  3. Large-scale fine-tuning makes self-correction possible.
  - — [Kamoi et al., arXiv 2406.01297](https://arxiv.org/abs/2406.01297)
- **CRITIC** (ICLR 2024): a Verify → Correct → Verify loop. The *tools* do the verifying: a search API for facts, a Python interpreter for code and arithmetic, a toxicity classifier. It consistently improves QA, program synthesis and detoxification. — [Gou et al., arXiv 2305.11738](https://arxiv.org/abs/2305.11738)
- **Reflexion** (NeurIPS 2023): verbal reflections on task feedback are stored in episodic memory. 91% pass@1 on HumanEval vs 80% for GPT-4. The feedback there is unit-test execution, an external signal. — [Shinn et al., arXiv 2303.11366](https://arxiv.org/abs/2303.11366)
- **DSPy Assertions**: code-level constraints with retry semantics, which generalise self-refinement to any pipeline step. In 4 text-generation case studies, constraints were passed up to **164% more often**, with up to **37% more higher-quality responses**. — [Singhvi et al., arXiv 2312.13382](https://arxiv.org/abs/2312.13382)
- Weak secondary source: one aggregator says iterative self-refinement can degrade "due to prompt bias, uncontrolled scope creep, and a lack of restraint where models feel compelled to change even perfect outputs". The primary paper was not identified. — [hyper.ai "autoreason" summary](https://hyper.ai/ar/papers/autoreason)

**LLM judge in the loop: biases (DOCUMENTED)**
- **MT-Bench / Chatbot Arena** (NeurIPS 2023): GPT-4 as judge agreed with humans over 80% of the time, about the same as human–human agreement. The paper also documents **position, verbosity and self-enhancement biases** and limited reasoning. — [Zheng et al., arXiv 2306.05685](https://arxiv.org/abs/2306.05685)
- **Self-preference** (NeurIPS 2024 oral): an LLM evaluator scores its own outputs higher than others' when humans rate them as equal. The bias correlates linearly with the model's ability to recognise its own text. — [Panickssery et al., arXiv 2404.13076](https://arxiv.org/abs/2404.13076)
- **Sycophancy** (ICLR 2024):
  - Assistants wrongly admit mistakes when challenged. Admission rates ranged from 42% (GPT-4) to 98% (Claude 1.3).
  - Asking "Are you sure?" cut accuracy by up to 27% on average across six datasets.
  - Their feedback shifts with the sentiment the user expresses.
  - — [Sharma et al., arXiv 2310.13548](https://arxiv.org/abs/2310.13548)

**Structured outputs and constrained decoding (DOCUMENTED)**
- **"Let Me Speak Freely?"** (EMNLP 2024 Industry):
  - Strict format restrictions (JSON mode, constrained decoding) significantly hurt *reasoning*.
  - On *classification* they are competitive or even better.
  - **Key order in the schema can interfere with reasoning.**
  - A two-step approach (reason in natural language, then convert to the format) is one mitigation.
  - — [Tam et al., arXiv 2408.02442](https://arxiv.org/abs/2408.02442)
- **JSONSchemaBench** (2025): 10K real schemas.
  - All frameworks cover over 86% of simple schemas.
  - On hard, deeply nested schemas coverage collapses: Guidance 41%, llama.cpp 39%, XGrammar 28%, Outlines 3%.
  - — [Geng et al., arXiv 2501.10868](https://arxiv.org/abs/2501.10868); the figures are from a [secondary summary](https://beancount.io/bean-labs/research-logs/2026/07/08/jsonschemabench-structured-outputs-language-models), not checked against the PDF.

**Agent design guidance (DOCUMENTED)**
- **Anthropic, "Building effective agents"** (19 Dec 2024):
  - *Workflows* run along predefined code paths. *Agents* direct their own process and tool use.
  - The guide names five workflows: prompt chaining, routing, parallelisation, orchestrator-workers, evaluator-optimizer. Evaluator-optimizer fits "when clear evaluation criteria exist and iterative refinement adds measurable value".
  - "Start with simple prompts, optimize them with comprehensive evaluation, and add multi-step agentic systems only when simpler solutions fall short."
  - For many applications, "optimizing single LLM calls with retrieval and in-context examples" is enough.
  - Agents trade latency and cost for performance.
  - — [Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- **"AI Agents That Matter"** (TMLR 2025): simple baselines, such as retrying or calling the model several times, **beat many state-of-the-art complex agent architectures on HumanEval at much lower cost**. Accuracy-only reporting has produced "needlessly complex and costly" agents and wrong conclusions about where gains come from. — [Kapoor et al., arXiv 2407.01502](https://arxiv.org/abs/2407.01502)
- **MAST** (NeurIPS 2025): multi-agent systems often show minimal gains over single-agent frameworks. 14 failure modes fall into 3 groups: specification, inter-agent misalignment, task verification. Inter-annotator κ = 0.88. ChatDev reached only 33.33% correctness on ProgramDev. — [Cemri et al., arXiv 2503.13657](https://arxiv.org/abs/2503.13657)
- **Agent Skills** (Anthropic docs):
  - A skill is a folder: `SKILL.md` with name and description, plus instructions and optional scripts and resources, loaded by **progressive disclosure**.
  - Load cost: about 100 tokens of metadata always; under 5k tokens of instructions when triggered; resources only when read.
  - Bundled scripts run through bash, and only their output enters context, "providing deterministic operations" (e.g. `validate.py`).
  - Claude Code skills live in `.claude/skills/` and have full network access. On the API they run in a sandbox with no network.
  - Security: "treat like installing software".
  - — [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

**Persona generation at scale (DOCUMENTED; detail in distinctness.md)**
- PersonaHub uses a near-duplicate threshold (cosine or MinHash 0.9) to dedup synthetic personas. — [arXiv 2406.20094](https://arxiv.org/html/2406.20094v1)
- Persona Generators evolves the generator *code* against population-diversity metrics. — [arXiv 2602.03545](https://arxiv.org/html/2602.03545v1)
- "Persona collapse": the models with the highest fidelity to each individual persona produce the most stereotyped populations. — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)

### Inferences (ASSUMED)
How the four architectures compare for PS04:

| Architecture | Fit 25 | Distinct 20 | Evidence 15 | Hallucination risk | Cost / latency per seller | Verdict |
|---|---|---|---|---|---|---|
| A. Rules only (feature → level table + templates) | Medium: reasons are rigid but true | High *if* the grid is designed well (structural) | High: every rule carries a rule id and stats | ~0 | ~0, ms | **Backbone.** Weak on prose personalisation (opening, playbook wording). |
| B. One grounded structured LLM call (rules fix the levels; the LLM writes prose fields citing rule and library ids; schema-validated) | High | High: levels stay fixed by rules, so the LLM can't collapse them | High if ids are enforced | Low; caught by validator | 1 call, ~2–10 s | **Recommended core.** |
| C. RAG over similar sellers' past calls and the library | Higher on objection-specific wording | Neutral, or lower if the same top-k examples are retrieved for everyone | Highest: concrete exemplars | Low–medium (retrieved text may leak seller-specific facts) | +embedding/BM25 lookup | Add as *retrieval of library entries and aggregate rule rows*, not raw transcripts (data rule). |
| D. Agent loop (Claude Code + skill: read files → draft → run validator → revise; or plan → draft → judge → revise) | Same as B on most sellers; better on messy or missing-data sellers | Risk: revision and judging pull toward a "safe" mean | Same as B if the validator is the critic | Low with a validator; higher with an LLM judge as sole critic (self-preference, sycophancy) | 5–30+ tool turns, tens of seconds to minutes per seller (ASSUMED; not measured) | **Offline authoring tool and demo showpiece, not the runtime.** |

- The research favours B plus a **code-validator retry**. That is effectively CRITIC or DSPy Assertions with the validator as the tool. The PS04 "critique" step should be deterministic checks:
  - every reason cites a seller field that exists;
  - every rule id exists and its tier matches the rule table;
  - no numbers, prices or claims appear outside the library;
  - the voice id is in the catalogue;
  - the language matches the seller's zone.

  An LLM judge should be used only as a *scored evaluator* on a held-out set (Q4), not as the in-loop critic.
- **Schema design (from Tam et al.):** put `reason` and `evidence` text **before** the chosen value in each field object, or reason first and then format. Keep the schema shallow, under about 3 levels, to stay inside the "simple schema" regime where constrained decoding is reliable.
- The **Claude Code + skill** variant is a legitimate way to *build* and *debug* the generator: it reads `data/`, runs `validate.py`, and fixes the prompt or rules. But per AGENTS.md **the core agent must be Sarvam**, so the per-seller runtime generator should be a Sarvam (or OpenRouter) call orchestrated by our code. Pitch the Claude Code skill as the developer or ops loop, if at all.

### Gaps
- No paper found that compares rules vs single-call vs agentic generation **for persona or sales-script specs** specifically. All evidence comes from QA, code, math and dialogue.
- The dottxt rebuttal to "Let Me Speak Freely" (that well-designed constrained decoding does not hurt) is ASSUMED from memory and was not fetched. Treat the format penalty as contested.
- No measured cost or latency for a Claude Code headless skill run per seller. Estimate it in a spike.
- Whether Sarvam's LLM (sarvam-m / 105B) supports JSON-schema constrained decoding is unverified. If not, use prompt plus parse plus validator retry.

---

## Q2. How to make each field cite evidence and verify attribution

### Takeaway
Do not trust the LLM to cite. **Make citation a selection from ids that code provides, then verify in code.** Each field object carries:
- `value`;
- `reason`;
- `seller_fields_used[]`, keys that must exist in the seller context;
- `rule_id`, which must exist in the rule table;
- `library_ids[]`, which must exist in the library;
- `tier` (strong / moderate / guess), **copied by code from the rule table, never from the LLM**;
- `confidence`, lowered by code when a used field is missing.

Free-text attribution checks (NLI or an LLM checking that a reason is supported) are only about 80% accurate, so use them as a secondary audit, not a gate.

### Cited Findings
- **ALCE** (EMNLP 2023): the first benchmark for LLM generation with citations, scored on fluency, correctness, and citation recall and precision. Automatic citation metrics agree with humans at 85.1% (recall) and 77.6% (precision). Even the best model left 49 ELI5 generations without complete citation support. — [Gao et al., arXiv 2305.14627](https://arxiv.org/abs/2305.14627)
- **AttributionBench** (ACL Findings 2024): automatic attribution evaluation is hard. Even fine-tuned GPT-3.5 gets about 80% macro-F1 on binary "is this claim supported by the cited evidence". Most errors come from nuanced information. NLI-tuned models (T5-XXL-TRUE, AttrScore) do best. — [Li et al., arXiv 2402.15089](https://arxiv.org/abs/2402.15089)
- **Anthropic Citations API:**
  - The API extracts `cited_text` itself, so citations "are guaranteed to contain valid pointers to the provided documents".
  - Custom-content documents let *you* define the citable chunks (block index ranges), e.g. one block per rule row.
  - **Citations cannot be combined with structured outputs (400 error).**
  - — [Claude docs: Citations](https://platform.claude.com/docs/en/build-with-claude/citations)
- CRITIC-style verification with tools beats self-verification (Q1). — [arXiv 2305.11738](https://arxiv.org/abs/2305.11738)

### Inferences (ASSUMED)
- **Id-based attribution beats span-based attribution here.** PS04 evidence consists of *aggregate rules* (e.g. "price-objection sellers: opening X, n = …, lift …"), not passages. Give each rule a stable id, so verification becomes a set-membership check: 100% precise and cheap. Span citation (ALCE, the Citations API) only matters for showing transcript-*summary* exemplars.
- **Two-level check:**
  1. **Hard (code):** the ids exist; `seller_fields_used` ⊆ the non-null keys in the context; the rule's precondition evaluates to true on this seller (re-run the rule predicate in code); the tier equals the rule-table tier.
  2. **Soft (audit):** an LLM or NLI check on a sample that the `reason` text is consistent with the rule and the field values. Report the agreement rate; don't gate on it.
- **Evidence-link coverage metric:** the share of spec fields with a valid rule id whose predicate is true, split by tier. Show "x% strong / y% moderate / z% informed guess". This answers the PS04 criterion "be clear about how strong the evidence is".
- Missing fields (FAQ Q6): code sets `confidence = low`, `tier = default` and `reason = "default: <field> missing"` *before* the LLM sees the spec. The LLM may reword it but not upgrade it.
- If Claude were used with citations, the structured-output conflict means you would either use citations with free text and parse it, or use structured outputs with id fields. The id-field route is simpler and portable to Sarvam.

### Gaps
- No published method found for verifying *rule-based* (statistical) attribution, as opposed to passage attribution. The id-plus-predicate re-check is our design.

---

## Q3. Which fields are deterministic, which are LLM-reasoned, and which need an agent loop? Where does an agent loop measurably beat one grounded call?

### Takeaway
Use **deterministic** logic for anything that is a level, a number, an id, a safety rule or a confidence. Use the **LLM** for prose that must sound personal: the opening line, personalisation hooks, playbook wording, reason sentences. Keep the **agent loop** for:
- building the evidence and rule table and the library offline;
- sellers whose single call fails validation twice.

The research gives no basis to expect an agent loop to beat one grounded call when the critic is the same LLM without new information. Gains appear only when the loop brings new signal: validator errors, retrieved similar-seller evidence, or tool checks.

### Cited Findings
- Self-correction helps with reliable external feedback and not with intrinsic critique. — [Kamoi et al.](https://arxiv.org/abs/2406.01297); [Huang et al.](https://arxiv.org/abs/2310.01798)
- Constraint-plus-retry raises compliance (up to +164% passes). — [DSPy Assertions](https://arxiv.org/abs/2312.13382)
- Strict formats are fine or better for classification-like choices and worse for reasoning-heavy text. — [Tam et al.](https://arxiv.org/abs/2408.02442)
- Workflows (predefined paths) should come before agents; evaluator-optimizer only "when clear evaluation criteria exist". — [Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- Industry practitioners dropped free ReAct agents (wrong tools, loops) for fixed structure (11x), and pin playbooks for determinism (Octave). — [industry_practice.md](industry_practice.md)

### Inferences (ASSUMED): field allocation

| Field | Owner | Why |
|---|---|---|
| voice gender, speaker id, pitch, pace level | **Rules** (feature → level → catalogue id) | Distinctness is structural; must be a valid catalogue id; audible and auditable |
| language, Hinglish mix, formality | **Rules** (zone, past-call language, business type) | Classification-like; strong data signals |
| warmth and empathy levels | **Rules** (objection history, past outcomes) | Levels on a grid; prevents collapse to "warm/medium" |
| tier, confidence, rule_id, missing-field defaults | **Code only** | The LLM must not upgrade evidence |
| guardrails (no price, fact or compliance change) | **Code constant + post-check** | FAQ Q5; never generated |
| escalation triggers | **Rules** (thresholds), LLM rewords the phrasing | Must be testable |
| objection playbook | **Retrieval** of library entries matched to the seller's past objection types; **LLM** selects, orders and adapts the wording, citing `library_ids` | Octave pattern; grounded |
| opening, personalisation hooks | **LLM** (one call), must cite `seller_fields_used` | This is where per-seller prose earns the fit score |
| reason sentences | **LLM** rewords a code-built skeleton ("rule R12: price objection in 3 of the last 4 calls → slower pace") | Keeps facts in code and readability in prose |

Where an **agent / retrieve → draft → validate → revise loop adds measurable value** over one grounded call:
1. **Validator failure recovery:** one retry with the validator's error text, which is CRITIC-style external feedback. Cheap and proven in principle. Then fall back to the template.
2. **Sparse or contradictory seller data:** retrieving the k most similar sellers' *aggregate* rule outcomes gives evidence for an informed guess. Measure it as a fit-judge delta on low-data sellers only.
3. **Offline library and rule authoring:** Claude Code with a skill reads `data/` aggregates, proposes rules, runs the stats scripts, and revises. Here the "external feedback" is real (the stats). This is where the coding-agent pattern fits best, and it stays out of the per-seller runtime.
4. **No expected gain:** an LLM-judge-only critique loop on already-valid specs. Expect drift toward a generic, safe persona (sycophancy, self-preference, homogenisation), which costs distinctness (20%).

Measuring "adds value": run an ablation on held-out sellers comparing B (one call + validator) with D (loop), scoring fit-judge, Mantel r / entropy, evidence-link coverage, validator pass rate, and cost/latency. Keep D only if fit rises without a distinctness drop.

### Gaps
- No direct evidence on how the retrieval-of-similar-sellers gain varies with data sparsity in this domain. It has to be measured.

---

## Q4. Evaluating generator quality: a fit judge calibrated to humans, distinctness, evidence-link coverage

### Takeaway
Use three metric families:
1. A **rubric LLM judge** for fit. Calibrate it on about 30–50 human-labelled specs. Use a different model family from the generator, randomise position, and cap length.
2. **Structural distinctness** on the discrete grid (see distinctness.md).
3. **Code-computed evidence metrics**: link coverage, tier mix, validator pass rate, and the fabricated-number rate.

Report judge–human agreement next to every judge score. Expect criteria to shift while labelling, so freeze the rubric after one labelling round.

### Cited Findings
- GPT-4-class judges reach over 80% agreement with humans, about the human–human level, but carry position, verbosity and self-enhancement biases. — [Zheng et al.](https://arxiv.org/abs/2306.05685)
- A judge favours its own model's text, and the bias scales with self-recognition. — [Panickssery et al.](https://arxiv.org/abs/2404.13076)
- **Criteria drift** (EvalGen, UIST 2024): people need criteria to grade outputs, but grading outputs changes the criteria. LLM-generated evaluators "inherit all the problems of the LLMs they evaluate" and need human validation. EvalGen picks the assertion or judge implementations that best match a small set of human grades. — [Shankar et al., arXiv 2404.12272](https://arxiv.org/abs/2404.12272)
- Automatic citation metrics agree with humans at 77–85% ([ALCE](https://arxiv.org/abs/2305.14627)). Attribution judges reach about 80% F1 ([AttributionBench](https://arxiv.org/abs/2402.15089)).
- Population metrics: coverage, uniformity, pairwise distance, near-duplicate thresholds. — [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md), citing [Persona Hub](https://arxiv.org/html/2406.20094v1) and [Persona Generators](https://arxiv.org/html/2602.03545v1)

### Inferences (ASSUMED): eval harness
- **Fit judge:**
  - Rubric per field: does the setting follow from the cited seller data, and is it plausible given the evidence? Score each field 1–5, plus an overall score.
  - Run it with an OpenRouter or Jev model from a *different family* than the generator.
  - Swap the order on pairwise comparisons and penalise length.
  - Calibrate on 30–50 specs labelled by 2 team members. Report Cohen's κ or Spearman ρ against humans.
  - Include deliberate **negative controls**: a spec swapped to another seller, and a generic spec. The judge must score them lower. This is the cheapest test of whether the judge actually reads the seller data.
- **Distinctness:** per-dimension entropy, distinct-persona ratio, Hamming, and Mantel r between seller distance and persona distance. Add text-embedding similarity of the prose fields with a 0.9 near-duplicate flag.
- **Evidence:** link coverage by tier; validator pass rate on the first try and after the retry; fabricated-number rate (any digit or price in the prose that is not in the library or the context, which should be 0); missing-field default correctness.
- **Consistency:** generate each seller 3 times at the production temperature and measure level-vector agreement. It should be about 100% because rules own the levels. Measure prose embedding variance as well. Hallucination and inconsistency should be confined to prose.
- **Cost:** tokens and seconds per seller, and the share of sellers that fall back to the template.

### Gaps
- No published human-calibrated judge exists for "persona fit to a seller". The κ we get is the only evidence, and a small n means wide CIs.

---

## Q5. Devil's advocate: over-engineering for a 2-day build; an agent per seller at scale

### Takeaway
An agent per seller is the wrong runtime:
- it is the expensive, slow and least reproducible option;
- the literature shows complex agents often fail to beat simple baselines at equal cost;
- intrinsic critique loops don't self-correct;
- an LLM critic pulls toward homogenised personas, which costs the 20% distinctness score.

The 2-day build should be rules + one grounded Sarvam call + a code validator (retry once, then template) + an offline eval harness. The "agentic" story belongs to offline evidence and library building and to the post-call update loop, both of which use real external signal.

### Cited Findings
- Simple, cheap baselines beat complex agents on cost-controlled evaluation. — [Kapoor et al.](https://arxiv.org/abs/2407.01502)
- Multi-agent systems often show minimal gains, with 14 failure modes. — [MAST](https://arxiv.org/abs/2503.13657)
- "Add multi-step agentic systems only when simpler solutions fall short"; agents trade cost and latency for performance. — [Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- Intrinsic self-correction can degrade outputs. — [Huang et al.](https://arxiv.org/abs/2310.01798)
- Sycophancy: up to a 27% accuracy drop when challenged. — [Sharma et al.](https://arxiv.org/abs/2310.13548)
- Self-preference. — [Panickssery et al.](https://arxiv.org/abs/2404.13076)
- Fidelity-optimised models produce the most stereotyped persona populations. — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)
- Skills in Claude Code have full network access and can run arbitrary scripts, so they need a security audit. — [Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Inferences (ASSUMED)
- **Scale:** at hundreds of thousands of sellers, even about 20 s and a few thousand tokens per agent run is days of compute and meaningful spend. Agent outputs also vary run to run, which breaks "same seller → same persona" auditability. A single call with rule-fixed levels is reproducible on everything except the prose.
- **Rule compliance:** AGENTS.md says "the core agent must be Sarvam". Running Claude Code as the per-seller generator risks looking like a non-Sarvam core, and some may read a third-party agent runtime as "pre-built". Frame Claude Code as a dev tool. The generator logic (rules, schema, validator, compiler) must be our code.
- **Over-engineering checklist.** Cut, in this order, if time is short:
  1. the LLM-judge critique loop;
  2. retrieval of similar sellers;
  3. GEPA;
  4. the soft attribution audit.

  Never cut the rules grid, the id-cited schema, the code validator plus fallback, or the distinctness and coverage metrics. Those map directly onto fit, distinctness and evidence (60% of the score).
- **Counter-argument (steelman for the agent):** judges may reward a visible "the agent read the data, drafted, ran checks, revised" trace as sophistication. Get that cheaply by *logging* the B pipeline's steps (context built → draft → validator result → retry → final) as a trace on the one-slide workflow. No real agent is needed.
- **Where an agent would be justified later:** sellers with long, messy call histories where the relevant evidence must be *searched* (many transcripts, unknown objection types). That is a post-hackathon scale problem, not a demo problem.

### Gaps
- No measured comparison on our data yet. The ablation in Q3 is the evidence to collect if time allows.
- The organisers' view on Claude Code or third-party agent runtimes within "pre-built" is unconfirmed. Ask on Day 1.
