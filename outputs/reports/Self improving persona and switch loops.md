> **Correction 2026-10-08 (team decision):** nothing learns during a call, and no LLM decides switches live. The "LLM teacher on uncertain turns" tier below is replaced by a post-call review that improves the switcher and generator between runs. Current design: `wiki/projects/vani-hackathon/learning-loops.md`.

# Make the loops produce evidence, not buzzwords

**Build both loops, but as gated offline improvement passes that produce held-out evidence. Nothing in PS04 should learn live during the demo.** PS04 never asks for "self-improvement". It scores fit 25%, correct and well-timed switches 25%, distinctness 20%, natural voice in 2+ languages 15% and past-call evidence 15%. Its five deliverables are generator code, a spec per seller with reasons, a Sarvam voice demo with at least one live switch, a switch log, and one slide ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)). A loop earns points only when it raises those numbers, or when it produces the "validation on real data" that the deck's Robustness criterion asks for ([persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)).

The design is as follows.

- **Generator (MVV):** guarantee distinctness structurally. Deterministic rules mined from past calls place each seller on discrete, audible attribute levels. A Sarvam LLM only phrases the result. The loop is one or two gated "worst failures → rule or wording fix" rounds, scored on a frozen held-out seller split.
- **Switching (MVV):** a lexicon decides the current reply and Jev corrects the next one. An LLM teacher is consulted only when Jev lands in a calibrated uncertain band. Teacher labels improve the lexicon and thresholds offline, behind a human-adjudicated frozen test set.
- **Budget:** the in-scope core alone is roughly **20–30 developer-hours** against **~18–24 productive hours**, so loop work is capped at about 6 hours. GEPA, kNN memory in Jev's state, trainable students, bandits and mid-demo learning are stretch goals or out of scope.
- **Open rulings:** two organiser answers can reshape the plan. One is whether sending seller text to OpenRouter or Sarvam LLMs counts as leaving premises. The other is what the "sample seller files" set actually is.

## PS04 rewards correct, evidenced personas; "self-improving" must hide inside those criteria

The binding text is narrow, and the devil's-advocate test follows from it. Three points shape everything else:

- **FAQ Q1** forbids a fixed persona library. The output must be "a persona per seller", and grouping into types is allowed only to explain the logic.
- **FAQ Q6** wants missing fields to fall back to defaults marked lower confidence, with live adaptation correcting them.
- **FAQ Q5** forbids any persona change to facts, pricing or compliance.

([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md))

The one-slide deliverable must hold a sample spec, its past-call evidence, and a workflow. **Self-improvement is not among its required elements** ([PS04 doc §5](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)).

The deck adds three rules that act as hard filters on any loop design. **All build work happens during the 2 days**, **pre-built solutions are disqualified**, and **no customer data leaves the premises** ([persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)). A loop is therefore worth building only if it does three things:

1. It feeds fit, distinctness, evidence or switch correctness.
2. It can be written from scratch in hours.
3. It does not ship real seller text to an unapproved endpoint.

The empirical backdrop argues for modest claims (PROVEN):

- **IndiaMART's three static-personalisation trials all failed to beat control.** For example, `personalis` scored 14.8% vs 17.8% and `summary_va` 3.3% vs 18.4% ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)). A "the loop made personas better" claim backed only by an LLM judge has no outcome support.
- **Public precedent is thin.** The production self-improving voice systems found, SquadStack Lift and Cekura, are vendor-reported. Both work offline or through gated A/B with a human approval step, never mid-call. No hackathon-winning voice agent with a measured self-improving persona or routing loop turned up ([proof and scope notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/proof_and_scope.md); [SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent); [Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)) (DOCUMENTED).

A frozen-test v0→v1 table already sits above the public norm. A "learns live" claim would be unusual and hard to defend in Q&A.

## The generator: rules fix the levels, Sarvam writes the words, the loop edits both behind a frozen test set

### Why a free-text LLM generator fails distinctness

**Persona collapse is a measured failure mode.** Agents given distinct profiles "converge into narrow behavioral modes". The models with the highest per-persona fidelity "consistently produce the most stereotyped populations" ([arXiv 2604.24698](https://arxiv.org/abs/2604.24698)) (DOCUMENTED). Different models also produce strikingly similar outputs, the "Artificial Hivemind" effect ([arXiv 2510.22954](https://arxiv.org/abs/2510.22954)) (DOCUMENTED).

The fixes that worked all make diversity an explicit objective over a defined attribute space ([distinctness notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/distinctness.md)):

- diversity axes plus a two-stage generator: population decisions first, per-persona prose second ([Persona Generators, arXiv 2602.03545](https://arxiv.org/html/2602.03545v1));
- quality-diversity grids ([QDAIF, arXiv 2310.13032](https://arxiv.org/pdf/2310.13032));
- dedup thresholds ([Persona Hub](https://arxiv.org/html/2406.20094v1)).

Our own spike agrees. Prompt-only behaviour was inconsistent: one neutral run gave a callback, another a 30-word pitch ([spike log](../../raw/research/2026-10-07-spike-log.md)) (PROVEN). If one LLM writes the whole spec, PS04 personas will drift to "polite, warm, medium pace, Hinglish" with reworded reasons, which is exactly the "minor variations of one" the rubric penalises (ASSUMED).

### Minimum viable generator

The recommended shape is the Persona Generators pattern scaled down to a function of the seller (ASSUMED design):

```
seller row → feature extractor (deterministic; flags missing fields)
          → base spec (every field filled, reason "default: no seller data", confidence LOW)
          → rule layer: + Σ mined rules as level/delta changes (rule id, inputs, n, effect, tier)
                        + fixed gates: DNC, AI disclosure if bot-question history, guardrail block
          → voice resolver: (gender, timbre, language) → v4 speaker (or app_version on phone)
          → Sarvam LLM (JSON schema, reasoning off): opening, personalisation line,
                        playbook wording, reason sentences, written only inside the chosen levels
          → validators: every reason cites a present field + an existing rule id; no digits or price words;
                        confidence = min(rule tier, data completeness); retry once on failure
          → persona.json + evidence rows
```

The FAQ Q6 default behaviour falls out by construction: a missing input leaves the base value in place at LOW confidence ([generator notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/generator_loop.md)). Archetypes appear only in the explanation, never as a lookup, which keeps FAQ Q1 intact.

### Grounding the rules in real data

The rules come from data we already hold (PROVEN, aggregate, correlational):

- **Previous disposition dominates.** It carries 0.74 of tree importance for meeting-fixed. Meeting-fixed runs 17.4% on a first call, 21.7% after a prior Meeting-Fixed, 8.1% after Call-Later and 4.4% after Not Interested (n=269,455).
- **A seller's own prior signals recur.** Rush 30.8% vs 21.1% (n=276), confusion 25.0% vs 7.0% (n=68), bot-question 22.9% vs 3.5% (n=35).
- **Objection mix is nearly flat across segments (±5 pts).** Distinctness must therefore come from history state, prior signals, language and size, not from objection type.

([generator notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/generator_loop.md))

A rule survives only if all three conditions hold: n ≥ 200, a bootstrap CI that excludes zero, and **the contrast still holds on a time split** (mine Apr–Jul, check Aug–Sep). It is then tagged STRONG, MODERATE, WEAK or GUESS. Voice gender and timbre will mostly be GUESS, because no data links them to outcomes. PS04 §3.4 rewards saying exactly that ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)).

Every rule must carry the label "signal propensity, not causal lift". The data shows *who* rushes. It does not show that a crisper pace *helps* them.

### Distinctness as a property of the mapping

Distinctness is guaranteed by the mapping, not by asking the LLM to be diverse. The proposed grid has eight dimensions (ASSUMED design):

| Dimension | Levels | Knob |
|---|---|---|
| Voice gender + timbre | 4 | `speaker` from v4 catalogue tags |
| Language | 3 | `initial_language_name` |
| Pace | 0.9 / 1.0 / 1.15 | `pace` |
| Pitch | ±0.15 | `pitch`, **only if audible on v4** |
| Formality | 3 | prompt variable |
| Warmth | 3 | prompt variable |
| Opening / brevity | 3 | `initial_bot_message` variant |
| Objection playbook + escalation | 3 | playbook variable |

The data can fill this grid without inventing noise (PROVEN, aggregate):

- PS07 holds 149,363 sellers.
- A coarse 5-feature grid has **285 populated cells, 181 of them with ≥50 sellers**. The largest cell holds 7.6%.
- The catalogue has 176 v4 voices.
- Regional voice spread is the bottleneck: only 3 Gujarati-tagged and 9 Marathi-tagged voices ([distinctness notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/distinctness.md)).

The guarantee has two halves:

- **Different sellers sound different.** Two sellers who differ on a driving feature must differ on at least one *audible* dimension (voice, language, pace or opening).
- **Identical sellers get identical levels.** Two sellers with identical feature vectors differ only in personalisation slots.

The second half stops "manufactured distinctness": randomly spreading voices would buy distinctness points at the cost of fit and evidence. Two caveats apply. The public Bulbul docs say v3 has no pitch control, and per-session pace and pitch on v4 is untested ([Sarvam Bulbul docs](https://docs.sarvam.ai/api/models/bulbul)) (DOCUMENTED). So **pitch is not a distinctness lever until audio measurement confirms it**. And because the voice is fixed per call, distinctness is a pre-call property: live switches change only tone, brevity and language ([persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)).

### The improvement loop, MVV and stretch

The loop edits only two learnable parts:

- **the rule table**, which changes only by re-mining data;
- **the LLM instruction block** that governs playbook ordering, opening phrasing and reason writing.

Four parts stay **fixed and hand-written**: gates, guardrails, the judge prompt and the metric weights. That way no loop can erode compliance, mirroring SquadStack's locked compliance and pricing sections ([SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)).

**MVV (about 2 hours of loop work).** Run v0 on train and val. List the worst failures from three sources: deterministic checks, distinctness collisions, and a judge or human critique. Apply one or two manual rule or wording fixes, and accept a fix only if val does not regress. Then score v0 against v1 once on test.

The most persuasive output is a concrete story, not a score delta. An illustrative example: "the loop found re-engage sellers getting the warm-slow voice despite a rush history and a 4.1% meeting rate, and moved them to crisp" ([proof and scope notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/proof_and_scope.md)).

**Stretch (3–5 hours, only if the voice demo and live switch work end to end by Day 1 evening).** Run GEPA on the instruction block alone.

- **Why it fits:** GEPA reflects on trajectories in natural language and keeps a per-instance Pareto frontier. It is MIT-licensed, installs with `pip install gepa`, and reaches models through LiteLLM ([gepa-ai/gepa](https://github.com/gepa-ai/gepa)). It typically takes 100–500 metric calls ([arXiv 2507.19457](https://arxiv.org/abs/2507.19457)) (DOCUMENTED).
- **Documented failure modes:**
  - Without a valset, "GEPA overfits" ([DSPy GEPA docs](https://dspy.ai/current/api/optimizers/GEPA/overview/)).
  - Unconstrained prompts grew past 5,000 characters, and 500 examples did worse than 20–100.
  - A 1,500-character cap cost only 0.8% performance.
  - Small reflection models "fail completely".
  ([Decagon](https://decagon.ai/blog/optimizing-gepa-for-production))
- **Settings if run:** a 1,500-character cap, merge off, a frontier reflection LM, and a fixed judge from a different model family.
- **Composite metric (ASSUMED):** 0.35 judge fit + 0.25 deterministic pass + 0.20 feature-explained distinctness + 0.20 predictive validity, with any guardrail violation scored as zero.

The **predictive-validity term** is the one unhackable, outcome-grounded piece. Each spec declares `expected_signals` (rush, confusion, frustration, bot-question). Those are scored by AUC or Brier against the seller's *next* real call on a time split.

### Generator components that do not earn their place

| Component | Verdict | Reason |
|---|---|---|
| Thompson-sampling bandits | Skip | Need live traffic we will not have; show Beta-posterior confidence on historical counts instead |
| Uplift on the 8 historical bot versions | One slide at most | Assignment is confounded (97% of Tamil Nadu calls went to one version), and what each version changed is unknown ([generator notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/generator_loop.md); [CausalML](https://arxiv.org/pdf/2002.11631)) |
| Simulated-seller optimisation of the generator | Skip | Simulators halve expressed resistance (25.1%→13.5%) and are "persuaded by sales agent suggestions" ([alphaXiv 2605.08334](https://www.alphaxiv.org/abs/2605.08334)) |
| Weight search over continuous settings | Skip | Nothing rewards a pace of 1.07 over 1.05 except a judge's taste |
| MIPROv2 / few-shot demos | Skip | Would paste past-call text into prompts |

## Switching: lexicon now, Jev next turn, an LLM teacher only in Jev's uncertain band

### Why the user's framing needs one adjustment

Jev cannot sit in the live turn, and it cannot "learn".

- **Latency (PROVEN):** through OpenRouter from the office, Jev runs at p50 491 ms, rising to p95 1,406 ms under four concurrent calls. A Sarvam reply already takes ~2.1 s median with a stub tool ([spike log](../../raw/research/2026-10-07-spike-log.md)).
- **Inputs (DOCUMENTED):** Jev's only inputs are `state` plus per-question `type`, `instructions` and `criteria`. There is no few-shot field and no fine-tuning ([TypeSafe API](https://docs.typesafe.ai/api.md)).
- **Known weaknesses (DOCUMENTED):** accuracy "falls as the state grows with content unrelated to the decision". Choice questions lean to the first option, and score levels are "weak in numerical calibration" ([Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)).
- **Third-party benchmark (DOCUMENTED):** a tuned policy *cut* Jev accuracy from 86.20% to 82.53%. Decision models "do not reliably outperform" LLM judges or small classifiers ([Red Hat Developer](https://developers.redhat.com/articles/2026/10/02/benchmarking-ai-decision-models-against-traditional-guardrails)).

"Jev decides confident cases, an LLM decides uncertain ones" therefore becomes a four-tier cascade in which the improvements land on the parts that *can* change: thresholds, the lexicon, and optionally the retrieved examples.

### The cascade, minimum viable version

The design comes from the [switch loop notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/switch_loop.md) (ASSUMED values, PROVEN parts as marked).

1. **Lexicon decides now (<5 ms).** A Devanagari-aware lexicon picks the current turn's directive. An instant path matters because after the first rush cue a median of only 2 seller turns remain, and **17.2% of first rush cues fall on the seller's last turn** (PROVEN, crude regex over 12,015 calls).
2. **Jev runs asynchronously, one Noul per signal.** Noul is used because Choice has a first-option bias. The result applies to the next tool call.
3. **Per-signal band.** Jev p ≥ θ_high enters the mode, p ≤ θ_low rejects it, and anything in between is "uncertain".
4. **LLM teacher on uncertain turns.** On uncertain turns only (an estimated 10–30%), an LLM teacher runs asynchronously with a 3 s hard timeout and one request in flight per call.
   - **Model:** Sarvam `sarvam-105b-conversations` or 30B with reasoning off and JSON-schema output. This keeps the core-is-Sarvam story and reads Devanagari natively ([Sarvam chat completions](https://docs.sarvam.ai/api/chat-completion/overview)).
   - **On time:** a verdict that lands before the next tool call overrides the call state for that turn.
   - **Late:** a late verdict is only logged.
   - **Scope:** the teacher emits labels, never directives or spoken text.
5. **Code still owns every switch.** The pure policy function with hysteresis, dwell and a two-switch budget makes the decision ([system design report](VANI%20problem%20choice%20and%20system%20design.md)).

Two cautions on timing and latency:

- The teacher helps mainly with **implicit** signals such as frustration and interest. Explicit rush cues are already caught by the lexicon.
- Sarvam LLM latency in non-reasoning mode is **unpublished**. Third-party figures conflict (13.86 s, 2.06 s, "no data"), so measure it with one curl on Day 1 ([Artificial Analysis](https://artificialanalysis.ai/providers/sarvam)).

### How the teacher's decisions improve the component (offline, gated)

The highest-value learning is offline, because live event data is tiny. About 40 simulated calls give ~200 seller turns and only tens of teacher labels. Bounded thresholds need far more: **shrewd's bounded routing needs "about a thousand judged documents"** and naive curve-read thresholds "failed in 4 to 7 of 10 draws" ([sshah03/shrewd](https://github.com/sshah03/shrewd)). Conformal cascades need roughly n ≥ 200 exchangeable calibration points ([Conformal Cascade](https://www.alphaxiv.org/abs/2607.25018.md)) (DOCUMENTED).

**MVV loop, done in-event:**

1. Sample about 400 enriched PS07 seller turns. Transliterate a share to Devanagari, because live ASR delivers Devanagari while 99.37% of historical turns are Latin script (PROVEN).
2. Label the pool with Jev plus the teacher, blind to each other.
3. Hand-label about 200 *separate* turns as the frozen gold test, double-labelled and adjudicated, with ≥25 positives per required signal. Language switch is labelled deterministically from script or language-ID.
4. Fit θ_high and θ_low per signal with a Clopper-Pearson bound on false-positive and miss rates.
5. Promote lexicon additions that fire on ≥k train examples and do not raise false switches on val negatives.
6. Score lexicon v0 vs v1 on the frozen test.

Promotion follows **two-key rules**:

- A label is promoted only when Jev and the teacher agree, or a human confirms it.
- Promotions are rate-limited per call.
- Each promotion carries provenance and a one-click rollback.
- The locked test set is never touched.

These guards matter because self-improving pipelines can be poisoned: PoisonedEvolution embedded target behaviour in **91.0% of trials at 10% attacker support** ([arXiv 2608.05563](https://arxiv.org/pdf/2608.05563)). Corrupted labels have also led an optimiser to delete correct rules ([Wahi, arXiv 2609.02246](https://arxiv.org/abs/2609.02246)) (DOCUMENTED).

**Stretch options, in priority order:**

| Option | Cost | Value and risk |
|---|---|---|
| Char 2–5-gram TF-IDF + logistic-regression student, retrained between demo rounds | Trains in seconds; ~0.35 ms per document on CPU ([shrewd](https://github.com/sshah03/shrewd)) | The cheapest *real* parameter update; also serves as the kNN retriever |
| kNN memory in Jev `state`: the 3–5 nearest teacher-verified examples | 4–6 h | Inter-Cascade reports up to +33% weak-model accuracy from retrieved strong-model resolutions ([arXiv 2509.22984](https://arxiv.org/abs/2509.22984)), but nothing shows Jev uses examples rather than being distracted. A/B it against no memory and a random-neighbour placebo, and drop it on no gain |
| simple-jev + RFDT or an encoder fine-tune | Out of reach | RFDT training is effectively GPU-only ([RFDT README](https://raw.githubusercontent.com/featherless-ai/simple-jev/main/RFDT/README.md)), and the allowed infra has no GPU |

## About 25 core hours leave only six for loops

Hours are ASSUMED estimates for one strong developer unless noted. "Never" means the item maps to a required deliverable. Cut order 1 goes first.

| # | Component | Deliverable / criterion | Status | Est. h | Cut order |
|---|---|---|---|---|---|
| 1 | Seller context builder (row → features, missing-field flags) | D1; Fit 25% | IN-SCOPE | 2–3 | never |
| 2 | Base spec + rule layer + gates + validators + Sarvam wording step | D1, D2; Fit 25%, Distinct 20%, Q5/Q6 | IN-SCOPE | 4–6 | never |
| 3 | Rule miner with n / CI / tier and a time-split check → evidence table | D2 reasons, D5 slide; Evidence 15% | IN-SCOPE | 2–3 (non-tech writes the narrative) | never |
| 4 | Sarvam agent + launcher (2–3 sellers, 2 languages) | D3; Voice 15%, deck Voice 20% | IN-SCOPE | 4–6 | never |
| 5 | Signal server: lexicon + policy + directives + switch log | D3 live switch, D4; Switches 25% | IN-SCOPE | 4–6 | never |
| 6 | Slide, video, skills.md, README | D5; deck Demo 15% | IN-SCOPE | 4–6 (shared) | never |
| 7 | Deterministic distinctness metrics (entropy bars, distinct ratio, Hamming, Mantel r) | Distinct 20%; Robustness | SUPPORTING (high value per hour) | 1–2 | keep |
| 8 | Switch eval set: ~400 train + ~200 adjudicated test turns | Switches 25%; Robustness | SUPPORTING | 2 dev + 2–3 labelling | keep |
| 9 | Offline switch loop: θ bands + lexicon v0→v1 behind the frozen gate | Switches 25%; Robustness | SUPPORTING (worth it) | 3–4 | keep (1 iteration) |
| 10 | Generator loop MVV: 1–2 manual fix rounds on a frozen split | Fit, Distinct (indirect); Robustness | SUPPORTING | ~2 | 6 |
| 11 | Jev async worker | Switches 25% (accuracy, exits) | SUPPORTING | 2–3 | 8 |
| 12 | Live LLM teacher on Jev's uncertain band (labels only) | Switches 25% (implicit signals) | SUPPORTING | ~2 | 5 |
| 13 | Sim harness, paired timing (10 cards) | Switch timing; Robustness | SUPPORTING | 1–2 (rewrite) | 7 (shrink) |
| 14 | LLM judge for fit + human calibration (30 specs) | Fit claim; Robustness | SUPPORTING | 2 dev + 3–4 non-tech | 4 (fall back to deterministic + human) |
| 15 | Predictive-validity term (expected signals vs next real call) | Evidence 15%; Robustness | SUPPORTING | 1–2 | 4 |
| 16 | Audio distinctness check + farthest-point demo-seller picker | Distinct 20%; Voice 15% | SUPPORTING | 1–2 | 5 |
| 17 | Day-2 rule re-mine | Evidence 15% (cosmetic) | SUPPORTING | 0.5 | 3 |
| 18 | GEPA on the wording/reason prompt | Fit (indirect) | STRETCH → OUT-OF-SCOPE if behind | 3–5 | 2 |
| 19 | Char-n-gram student; kNN memory in Jev state | Switches (marginal) | STRETCH | 3–6 | 2 |
| 20 | Dashboard | none directly | OUT-OF-SCOPE (use a static chart) | 2–4 | **1** |
| 21 | Bandits, uplift-driven rules, sim-driven generator optimisation, weight search, RFDT/encoder fine-tune, mid-demo learning, teacher writing directives live, post-call quality scoring | none / risky | OUT-OF-SCOPE | — | do not build |

Generating 149K LLM specs is also out. Run the deterministic rules-only pass on every seller and LLM wording on the organisers' sample set, after confirming what "every sample seller" means.

**Three conflicts remain between the notes, resolved here.**

- **GEPA.** The generator notes recommend one or two GEPA runs. The scope notes rate GEPA out of scope. This report sides with scope: GEPA is a stretch that is cut first. The manual fix round produces the same before/after evidence at a fraction of the risk.
- **Distinctness metric.** One note proposes raw pairwise distance; another proposes feature-explained distance (Mantel r). Only the feature-explained version is used, because raw diversity rewards noise.
- **Teacher model.** Sarvam is the primary live teacher. A stronger OpenRouter model is used only offline, and only if data handling is cleared.

Two rule-risk flags need explicit handling:

- **Pre-built.** Pre-event spike code and aggregate scripts are research. Rewrite the miner, generator, signal server and loop code in the event repo with timestamped commits, and disclose the spikes in skills.md. Using the `gepa` library is assumed to count as "framework" use, which is not confirmed ([persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)).
- **Data on premises.** Judge and teacher calls carrying real PS07 turn text go off-box to OpenRouter or Sarvam. Prefer the internal LiteLLM gateway where it works (it failed 8 of 8 Jev requests in our spike) ([spike log](../../raw/research/2026-10-07-spike-log.md)), or get an organiser ruling first.

## Proof protocol: frozen splits, one primary metric per loop, intervals that admit their width

### Generator protocol

**Split (ASSUMED design).** Before the first loop iteration, freeze a seeded split stratified by history archetype × language: **20 train / 20 val / 30 test sellers plus ~6 canaries** (all fields missing, DNC=1, contradictory fields, price-heavy objections). Print the split's hash in skills.md.

**Primary metric:** judge fit on the 30 test sellers, from a judge in a different model family than the generator and the reflection LM. The judge is arm-blind, scores both A/B orders, and has a length cap in its rubric.

**Judge gate:**

1. Two humans, including the non-tech member, blind-label the same 30 specs.
2. Report human–human and judge–human weighted kappa with bootstrap CIs.
3. If judge–human κ is below ~0.4, or more than ~0.15 below human–human, **pre-declare the fallback**: human blind preference v0 vs v1 becomes primary, and the judge is dropped.

The gate exists because percent agreement misleads. Judges with high agreement can still sit 10–20 points off human scores ([Judging the Judges, arXiv 2406.12624](https://arxiv.org/html/2406.12624)). Judges also carry position, verbosity and self-preference bias ([MT-Bench, arXiv 2306.05685](https://arxiv.org/html/2306.05685v4)) (DOCUMENTED). Fix the human rubric after a short look at outputs and before final scoring, to avoid criteria drift ([arXiv 2404.12272](https://arxiv.org/pdf/2404.12272)).

**Secondary metrics, all deterministic:**

- per-dimension entropy and coverage, failing any dimension with more than 80% of sellers on one level unless the data is that skewed;
- distinct-persona ratio and largest-cluster share;
- zero Hamming-0 pairs across different feature cells;
- **Mantel r** between seller-feature distance and persona distance, with 999 permutations ([Mantel test](https://uw.pressbooks.pub/appliedmultivariatestatistics/chapter/mantel-test/));
- evidence-link coverage (every reason cites an existing rule id);
- guardrail and schema validity;
- stability (same seller twice gives the same levels);
- predictive-validity AUC.

### Switching protocol

**Primary metric:** macro-F1 over the five required signals on the frozen adjudicated test, v0 → v1.

**Secondary metrics:**

- per-signal precision and recall with Wilson CIs;
- false-switch rate on negatives;
- a confusion matrix (rush vs frustration is the likely confusion);
- teacher-consulted and teacher-overturned rates.

**Timing.** Use the same 10 scripted cards and seeds for v0 vs v1. Measure turns-to-switch and seconds-to-switch after the trigger, plus spurious switches per call.

**Live calls.** The 3–6 live human calls are qualitative evidence for FAQ Q3, not a statistic.

**Independence rule.** Jev and the teacher never grade the test set they helped label ([proof and scope notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/proof_and_scope.md)).

### Honest sample-size limits

These are computed, and should be said aloud:

- **Wilson CIs widen fast.** 24/30 gives [0.63, 0.90] and 16/20 gives [0.58, 0.92]. At ~25–30 positives per signal, only differences of **~20+ points** separate cleanly.
- **Kappa is imprecise at small n.** At κ≈0.7 the 95% half-width is **±0.31 at n=20, ±0.26 at n=30 and ±0.20 at n=50**, so 30–50 labelled items is the honest minimum.
- **Paired binary tests need many discordant pairs.** With 10 discordant pairs, ≥9 must favour one side for p<0.05; with 15, ≥12 must. Forty paired simulated calls can show only a large effect.
- **Rare-signal bounds stay loose.** Frustration appears in about 1.7–3.6% of calls, so its threshold bounds stay wide even with enriched sampling. The "zero errors in n" rule gives at best ~4.6% at n≈50.
- **Run-to-run variance matters.** Run each test seller twice and report the spread, because LLM variance can exceed small loop gains.

Use paired bootstrap, McNemar or Wilcoxon for before/after comparisons, as Dror et al. recommend ([ACL 2018](https://arxiv.org/pdf/1809.01448)) (DOCUMENTED). The whole labelling load is about 3–4 person-hours, which suits the non-tech member with a rubric.

## Sixty seconds of video and one feedback arrow on the slide

### On the slide

Present the loops as an **evaluation-driven engineering method** that produced a measured, held-out improvement *before* the demo. The live call then runs on frozen v1 rules.

- Say "refined in N gated rounds against real PS07 data; held-out results below".
- Avoid "self-learning", "learns from every call" and "autonomous".
- Use "self-improving" at most once, and define it in the same breath.

Industry framing that sells uses the words gated, held-out and human-approved ([SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)). A higher evaluation score "does not always mean a better language model system" ([arXiv 2609.25848](https://arxiv.org/abs/2609.25848)) (DOCUMENTED).

The slide's required elements come first: a sample spec, the evidence behind it, and the workflow (LLM, Sarvam, data flow, live detection, integration). The loop is a small feedback arrow inside that workflow ("PS07 turns → Jev/teacher labels → lexicon/θ update → frozen-test gate"), with one number and its n.

### In the video

| Time | Content |
|---|---|
| 0:00–0:30 | Problem: rush cues sit in 21% of calls, which fix meetings at 13.6% vs 26.0% (PROVEN, correlational; [persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)) |
| 0:30–1:30 | Seller file → spec with reasons and evidence tiers |
| 1:30–4:00 | Same scenario for 2–3 contrasting sellers in 2 languages, a live switch, the switch log scrolling |
| 4:00–5:00 | Evidence table plus **one** before/after held-out chart: switch macro-F1 v0→v1 with CIs, and generator fit + Mantel r v0→v1 |
| 5:00–6:00 | Workflow, guardrails, limits |

Two more points belong in the video:

- **Show one failure the gate rejected**, such as a dropped rule or a signal that did not improve. It proves the gate is real and pre-empts "you tuned on the test set".
- **Pick demo sellers by a documented farthest-point rule** on audible dimensions, restricted to complete files in populated cells. Plot them on the Mantel scatter so they do not look cherry-picked. Verify the audible contrast with measured speaking rate, F0 and speaker-embedding distance.

Do not market a mid-call voice or pace change. Sarvam fixes the voice per call ([persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)).

## Risks and the Day-1 questions that decide scope

### Main risks

| Risk | Mitigation |
|---|---|
| **The loop optimises the judge, not the jury.** "Master key" inputs elicit false-positive judge rewards up to 80% ([NeurIPS 2025](https://neurips.cc/virtual/2025/131135)) | Deterministic vetoes, a cross-family judge, canaries, human-scored finals |
| **Teacher errors get baked into the lexicon.** Jev's 49/51 agreement was on romanized text only and may not transfer to Devanagari | Two-key promotion; human-adjudicated test; ~20 hand spot-checks before each update |
| **Fit and distinctness pull against each other.** Objection mix is nearly flat, so forcing variation beyond the data loses evidence and fit points | Distinctness counted only over rule-driven levels |
| **Time.** If the voice demo and live switch are not working by Day 1 evening, every loop beyond the frozen eval sets is cut | The rule miner stays, because it *is* the evidence deliverable |
| **Rules.** Spike-code reuse, ambiguous "pre-built" aggregates, and real seller text leaving premises through LLM calls | Rewrite in-event, re-run aggregation in-event, keep only aggregates in `raw/` and `wiki/`, avoid speaking real business names in recorded audio |

A self-improving system that "improves every loop right up until the live demo, then regress[es] to the mean" is exactly what the frozen-v1 demo avoids ([last30days scan](../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md)).

### Day-1 questions to resolve

1. **Which seller set is "every sample seller"?** It sets LLM spec volume and the test pool.
2. **Do OpenRouter and Sarvam LLM calls carrying PS07 turn text count as leaving premises?** If yes, use the internal gateway or Jev only, and drop the cross-family judge on real text.
3. **Are open-source optimiser libraries such as `gepa` acceptable as "frameworks"?** Do pre-event aggregates count as pre-built?
4. **Are the PS04 weights final?** Re-weight the composite metric if they change.
5. **Does per-session `text_to_speech_config` pace or pitch take effect on v4 speakers (T9)?** Is pitch audible? This decides whether pace stays continuous or collapses to three app versions.
6. **How fast is Sarvam LLM with reasoning off on a short JSON label?** Measure the gap between consecutive tool calls (T5). Together these decide whether the live teacher can steer turn k+1.
7. **How accurate is Jev on transliterated Devanagari (T8), and how many positives does enriched sampling yield per signal?**
8. **Can the Sarvam floor team enable Code Tools or a mid-call speaker or pace change?**
9. **What did each historical bot version change?** This decides whether the uplift slide is worth anything.

## Conclusion

The research shifts the question from "how do we make it self-improving" to "which improvements can be *proven* inside PS04's criteria in two days". The answer is asymmetric:

- **The switch loop has near-objective labels.** It can show an honest v0→v1 gain on a frozen, human-adjudicated test, so it is the one loop worth keeping.
- **The generator's real "learning" is evidence mining with a time-split check.** That directly is the 15% evidence criterion. Its prompt optimisation is the first thing to cut.
- **Distinctness was never a learning problem.** It is a design property of mapping seller features to discrete audible levels, and any loop that pushes personas apart for its own sake costs more fit and evidence points than it gains.

The non-obvious implication is that the most credible "self-improving" artefact is not a live behaviour at all. It is the gate: frozen splits, a pre-declared primary metric, a rejected edit shown on screen, and intervals reported at their true width. Teams that claim live learning will be asked "measured how?". A team that shows the gate has already answered.
