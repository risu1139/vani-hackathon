# Self-improving live switching: Jev, an LLM teacher, and a learning loop

As of 2026-10-08. Tags: **PROVEN** = measured by us (spike log) or computed from local data; **DOCUMENTED** = stated in vendor, paper or third-party docs; **ASSUMED** = our inference or an untested design value. Local data is cited only as aggregates (taken from [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md), which computed them from `data/.../ps07_call_turns.csv`). No transcript text appears here.

Local sources: [spike log](../../../raw/research/2026-10-07-spike-log.md), [system design](../../../wiki/projects/vani-hackathon/system-design.md), [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md), [last30days self-improving loops](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md).

## Q0. Recommendation: what self-improving design should we build?

### Takeaway
Build a **four-tier cascade with an off-path teacher** and make the "learning" mostly **offline and gated**, with a small, visible **online memory** for the demo:
1. Lexicon decides now (<5 ms).
2. Background Jev corrects the next tool call (~0.5 s).
3. When Jev is inconclusive (its noul falls in a calibrated "uncertain band"), an **LLM teacher runs asynchronously** (Sarvam LLM preferred, an OpenRouter model as fallback). Its verdict (a) overrides the call's state for the next turn and (b) is logged as a candidate label.
4. Candidate labels are promoted, after a held-out check, into the **kNN example memory** (live) and into **per-signal threshold recalibration and lexicon additions** (batch, between demo rounds).

A trainable local student (simple-jev+RFDT, ModernBERT/MuRIL, TF-IDF) is a stretch goal. Only TF-IDF/char-n-gram is realistic in 2 days on CPU. The highest-value "learning" for the 25% switch score is **offline calibration on transliterated ps07 turns**. The online loop is mainly a demo story, and it must be measured on a frozen held-out set to avoid fooling ourselves.

### Cited Findings
- PROVEN: Jev via OpenRouter from the office: p50 491 ms on keep-alive. Under 4 concurrent calls: p50 1,033 ms, p95 1,406 ms. Agreement 49/51 on 30 romanized turns. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: Sarvam reply ~2.1 s median (1.2–3.5 s) with a stub tool. The tool is called on every seller turn, often twice (partial, then full). The tool receives Devanagari. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN (ps07 aggregate): median 5 seller turns per call. After the first rushed cue a median of 2 seller turns remain, and 17.2% of first rushed cues fall on the last seller turn. — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md)
- DOCUMENTED: Inter-Cascade has the weak model learn from the strong model **without parameter updates**. Strong-model resolutions of deferred queries are stored as reusable strategies, then retrieved by similarity into the weak model's context. Reported: weak-model accuracy up to +33.06%, system accuracy up to +6.35%, strong-model calls down up to 48.05%. — [arXiv 2509.22984](https://arxiv.org/abs/2509.22984)
- DOCUMENTED: shrewd distils LLM labels into local students, then routes with **statistically bounded thresholds**. Thresholds read off evaluation curves "failed in 4 to 7 of 10 draws" on new data. The bounded routing needs "about a thousand judged documents". — [sshah03/shrewd](https://github.com/sshah03/shrewd)

### Inferences
- ASSUMED: Jev itself cannot "learn". Its only inputs are `state`, per-question `instructions` and `criteria` (DOCUMENTED, Q1). "Correcting the state of Jev" can mean three different things, and they should be kept separate:
  - (a) **Per-call correction:** the teacher verdict becomes part of *our* call state, so the policy treats it as a Jev-equivalent reading for the next turn. Optionally a short `prior_assessment` field goes into Jev's state (risk: anchoring; test it).
  - (b) **Cross-call memory:** corrected examples are retrieved into Jev's `state`.
  - (c) **Configuration updates:** criteria text, thresholds and lexicon change between rounds.
- ASSUMED **timing**: the teacher has roughly one agent reply plus one seller utterance to finish before the next tool call (≥ ~3–5 s at a 2.1 s reply plus speaking time; not measured). A ≤2–3 s teacher can therefore usually steer turn k+1. That is the same slot Jev targets, so the teacher mainly helps on **inconclusive, implicit** signals (frustration, interest), not on explicit rushed cues, which the lexicon already handles.

### Gaps
- The gap between consecutive tool calls (seller turn k → k+1) has not been measured, so the teacher's deadline is an estimate.
- No source measures whether a teacher-in-the-loop improves *switch timing* in voice agents specifically.

## Q1. Exact Jev knobs on the Decisions API, and do examples in `state` help or hurt?

### Takeaway
The knobs are: `state` (string, object or array), plus per question `type` (noul, choice or score), `instructions`, and `criteria`.
- Noul criteria: true/false meanings.
- Choice criteria: a map from option to rubric, up to 255 options.
- Score criteria: 2–10 ordered levels.

There is no few-shot field and no documented state-size cap beyond the 32K-token context. TypeSafe says nothing about examples in state. It does warn that **"accuracy falls as the state grows with content unrelated to the decision"**. So kNN examples are an untested bet: they might help if they are close neighbours, and they will hurt if they are noisy. A/B them on the eval set before turning them on.

### Cited Findings
- DOCUMENTED: Endpoint `POST https://openrouter.ai/api/alpha/decisions`. Three primitives (Choice, Noul, Score). 32,000-token context (state plus questions). You pay per input token; "Output tokens are free". — [OpenRouter Jev guide](https://openrouter.ai/docs/guides/community/jev)
- DOCUMENTED: Request fields:
  - `state` ("string | object | array").
  - `model`.
  - `questions` (a map of typed Question objects with `type`, `instructions` and `criteria`).
  - Noul `criteria`: an optional object with `true`/`false` meanings.
  - Choice: "a map of option to rubric description … maximum of 255 options".
  - Score: "ordered array of level descriptions", 2–10 levels.
  - No state size limit or question-count limit is documented, and there is no few-shot guidance.

  — [TypeSafe API reference](https://docs.typesafe.ai/api.md)
- DOCUMENTED: "Use an object for most requests so each part of the state has a descriptive name". Policies can sit in state next to the content. There is no guidance on examples, memory or history depth. — [TypeSafe State](https://docs.typesafe.ai/concepts/state.md)
- DOCUMENTED (jaggedness, jev-1.13):
  - "Accuracy falls as the state grows with content unrelated to the decision. Unrelated detail acts as a distractor." The advice is to "retrieve and filter in code first".
  - When `instructions` and `criteria` "ask for different things, jev-1.13 might get confused".
  - It reads negation and scope literally.
  - It "leans toward the option that comes first" in a Choice.
  - "score levels are weak in numerical calibration".

  — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- DOCUMENTED: Confidence is distribution concentration ("1 when all the probability is on one outcome and 0 when … spread evenly"). There are no calibration numbers. "The correct threshold values depend on your domain"; "Start with conservative thresholds, test with your own data, and adjust". — [TypeSafe Confidence](https://docs.typesafe.ai/confidence.md)
- DOCUMENTED: The confidence-routing example uses a 0.6 floor (below it, route to a human) and 0.85 for high-stakes auto-action. It gives no method for choosing thresholds or for feedback loops. — [TypeSafe confidence routing](https://docs.typesafe.ai/patterns/confidence-routing.md)
- DOCUMENTED (third party): A tuned prompt policy that helped Laya **cut Jev accuracy from 86.20% to 82.53%** (−3.67 pts) on content safety. Jev scored 86.35% on prompt injection (4th; Qwen3.6-35B 89.31%, deberta-v3-base 89.01%). Median latency was Jev 348 ms vs deberta 54 ms. The conclusion: "decision models like Jev do not reliably outperform LLM-as-a-judge, pre-trained predictive models, or open source decision models in speed or accuracy." English-only benchmark. — [Red Hat Developer, 2026-10-02](https://developers.redhat.com/articles/2026/10/02/benchmarking-ai-decision-models-against-traditional-guardrails)
- DOCUMENTED: "English is the primary training language … Other languages … are handled but not equally well." — [TypeSafe Models](https://docs.typesafe.ai/models.md) (via [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md))
- PROVEN: 6 questions vs 1 question barely changes latency (p50 482 vs 491 ms). A 979-token request had a provider latency of 315 ms. — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences
- ASSUMED **criteria optimisation (mechanism 1)**: this is the only "training-like" knob TypeSafe sanctions. The Red Hat result and shrewd's "prompt optimisation gains on dev vanish on test" both warn that optimised wording can overfit or regress.
  - Do a small, manual-plus-LLM-assisted search: 3–5 candidate wordings per signal, scored on a locked Devanagari test set. Accept a change only if it beats the current wording on the **locked** set by more than noise.
  - A full GEPA run needs hundreds of rollouts (GEPA found its IFBench prompt after 678 rollouts; [arXiv 2507.19457](https://arxiv.org/abs/2507.19457)). At ~$0.00004 per Jev call that is cheap in money, but it costs hours of build and eval time. Do it at most once, offline, before the event.
- ASSUMED **kNN-in-state (mechanism 2)**: put the 3–5 nearest *teacher-verified* examples, each as `{text, label}`, in a named state field (`similar_cases`). Keep them short to limit distractor risk. This adds about 100–250 input tokens, and latency barely moves because token count rather than question count dominates, and 979 tokens took 315 ms upstream. Untested whether Jev uses the labels or gets distracted. A/B on the eval set: no memory vs memory vs memory with random neighbours (the placebo check).
- ASSUMED: Use **Noul per signal** (not one Choice), because Choice has a first-option bias and multi-signal turns exist. Keep the true/false criteria aligned with the instructions, as the jaggedness doc says.

### Gaps
- No TypeSafe or third-party evidence on few-shot or retrieved examples in Jev `state`. This is the central uncertainty of mechanism 2.
- No published Jev accuracy on Devanagari or code-mixed text.
- No documented max state length other than the 32K context.

## Q2. Is a trainable local student feasible (simple-jev+RFDT on small Qwen, ModernBERT/IndicBERT/MuRIL, TF-IDF) on Daytona CPU?

### Takeaway
- **simple-jev serving** on CPU is possible but unbenchmarked.
- **RFDT training is effectively GPU-only.** CPU training is "useful for checking the workflow" only, and we have no GPU in the allowed infra. So simple-jev+RFDT is **not realistic in 2 days**.
- An **encoder** fine-tune (MuRIL/IndicBERT/ModernBERT) also wants a GPU (shrewd: ~25 min on a GPU, ~11 GB RAM).
- A **TF-IDF / char-n-gram logistic regression** student trains in seconds on CPU, runs in ~0.35 ms, and works for Devanagari through character n-grams. Its realistic role is a **better lexicon** that also serves as the kNN retriever, not a Jev replacement.

### Cited Findings
- DOCUMENTED: simple-jev turns open models (Qwen 0.8B, 4B, 27B, 35B MoE; Gemma 12B/26B) into a Jev-style `POST /v1/classifier` taking `state` plus questions. It runs one prefill, caches the shared prefix's KV, reads answer-token logits, and has "no autoregressive decode loop". CPU is supported (`--model Qwen/Qwen3.5-0.8B --device cpu --dtype float32`). "Actual latency depends on the model, hardware, context length…"; **no latency numbers** are given. Its values "are not calibrated probabilities of correctness". Apache-2.0. — [featherless-ai/simple-jev](https://github.com/featherless-ai/simple-jev)
- DOCUMENTED: RFDT data is JSONL `{request, targets, group_id}`. Teacher labelling calls any OpenAI-compatible `/chat/completions` at `temperature=0`, with retries and caching. It supports LoRA (`--lora --lora-rank 16`) or full-weight training. CPU training is "useful for checking the workflow". The example runs 3 epochs on 4 GPUs. **No training time is given.** "Mode agreement against soft teacher targets is not ground-truth accuracy", and Score/Noul calibration metrics "are not yet included". — [RFDT README](https://raw.githubusercontent.com/featherless-ai/simple-jev/main/RFDT/README.md)
- DOCUMENTED: shrewd students:
  - TF-IDF ~0.35 ms per document (<10 MB). ModernBERT 3–30 ms per document.
  - Encoder fine-tune "~11 GB RAM" and "~25 min on a GPU". TF-IDF and embeddings train in seconds.
  - Uncertainty sampling cut teacher calls 2.0–2.3×.

  — [sshah03/shrewd](https://github.com/sshah03/shrewd)
- DOCUMENTED (third party): Small pre-trained classifiers were the fastest in the Red Hat benchmark (deberta-v3-base median 54.1 ms on an M1 MacBook Pro) at near-top accuracy. — [Red Hat Developer](https://developers.redhat.com/articles/2026/10/02/benchmarking-ai-decision-models-against-traditional-guardrails)
- DOCUMENTED: MuRIL gives Indic scripts a larger vocabulary share, which suits Devanagari Hindi. L3Cube HindBERT/DevBERT are Devanagari BERTs. **No published CPU/ONNX latency was found for MuRIL or IndicBERT.** — [L3Cube HindBERT/DevBERT](https://arxiv.org/pdf/2211.11418); search summary
- DOCUMENTED: Qwen3.5-0.8B claims support for 200+ languages. **No Hindi or Devanagari classification accuracy or CPU latency numbers were found.** — [Qwen3.5-0.8B (Qualcomm card)](https://huggingface.co/qualcomm/Qwen3.5-0.8B)
- PROVEN: Daytona sandbox runs Python 3.11, with outbound access to Sarvam and OpenRouter. CPU type and cores are unknown. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN (ps07 aggregate): 64,625 seller turns; 99.37% Latin script, 0.18% Devanagari. — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md)

### Inferences
- ASSUMED: A 0.8B decoder prefill of ~300–600 tokens on a few CPU cores is likely to take hundreds of ms, which is not faster than Jev, and untrained 0.8B judgement on Devanagari Hinglish is unknown. Its value would come from RFDT fine-tuning, which needs a GPU. **Verdict: skip for the hackathon.** Mention it as the roadmap ("distil Jev+teacher into an on-prem 0.8B Jev-compatible model; same API, so drop-in").
- ASSUMED **2-day student**: char 2–5-gram TF-IDF + logistic regression per signal.
  - Train it on ~3–5K ps07 turns **transliterated to Devanagari**, plus their romanized originals, with labels from Jev and the teacher. Hand-labelled gold is kept separate.
  - Train time: seconds. Inference: <1 ms.
  - It replaces or augments the hand lexicon on the instant path and gives a probability, so it can join the cascade.
  - Retraining between demo rounds is the cheapest *real* parameter update we can show.
- ASSUMED: Teacher-label cost is small. Jev ~$0.00004 per turn means 5K turns ≈ $0.20. LLM-teacher cost depends on the model.

### Gaps
- No CPU latency for simple-jev with Qwen 0.8B/2B, and none for MuRIL/IndicBERT ONNX.
- No RFDT training-time data.
- No evidence on small-Qwen Devanagari or Hinglish classification quality.
- Daytona sandbox CPU and RAM are unmeasured.

## Q3. How do we set "Jev conclusive" thresholds with guarantees from small labelled sets (conformal or bounded routing)?

### Takeaway
Define "inconclusive" per signal as Jev noul in **(θ_low, θ_high)**.
- Choose θ_high so the **precision of auto-entering a style** is ≥ 1 − α.
- Choose θ_low so the **miss rate of auto-rejecting** is ≤ α.
- Use a conformal or upper-confidence-bound procedure on a held-out labelled set.
- Everything in between goes to the teacher.

Guarantees need exchangeable calibration data (Devanagari-like, not romanized-only) and roughly 200–1,000 labelled turns. Rare signals (frustration ≈1.7% of calls) need **enriched sampling**, or their bounds will be vacuous. Isotonic regression is a poor fit at these sample sizes; prefer a fixed band plus a binomial upper bound, or set-size conformal.

### Cited Findings
- DOCUMENTED: Conformal Cascade defers unless the conformal prediction set is a singleton. Per tier the set contains the true answer with probability ≥ 1 − α, so the cascade error is ≤ Kα (≤ α under selection preservation). The threshold is the ⌈(1−α)(n+1)⌉-th quantile of the calibration scores; deployment needs roughly n ≥ 200. Assumes exchangeability; "covariate-shift deployment needs online recalibration". The guarantee is marginal, not per subgroup. — [Conformal Cascade, arXiv 2607.25018](https://www.alphaxiv.org/abs/2607.25018.md)
- DOCUMENTED: shrewd's bounded routing needs "about a thousand judged documents". Locally answered requests were "1.5% wrong on guardrail against 7.0% overall". Naive curve-read thresholds failed in 4–7 of 10 draws. "Calibration alone can mask poor ranking ability." — [sshah03/shrewd](https://github.com/sshah03/shrewd)
- DOCUMENTED: C3PO bounds per-query cascade *cost* with conformal methods and claims effectiveness "even with small calibration sets". — [search summary of C3PO, SlidesLive](https://slideslive.com/39049778/c3po-optimized-large-language-model-cascades-with-probabilistic-cost-constraints-for-reasoning)
- DOCUMENTED: Jev score levels are "weak in numerical calibration", and simple-jev outputs are "not calibrated probabilities". — [Jev jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md); [simple-jev](https://github.com/featherless-ai/simple-jev)
- PROVEN (ps07 aggregate, crude regex): calls with a cue were rushed 31.6%, frustrated 1.7%, confused 4.8%, bot question 1.3%. — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md)

### Inferences
- ASSUMED **procedure** (2–3 hours, after the ~200–600 turn eval set exists):
  1. For each signal, sort the labelled turns by Jev p.
  2. Pick the lowest θ_high such that the Clopper-Pearson **upper bound on false-positive rate** among turns with p ≥ θ_high is ≤ α (for example α = 0.1, at 90% confidence).
  3. Do the same from the bottom for θ_low on missed positives.
  4. Report coverage, meaning the share of turns decided without the teacher.

  This is a Learn-then-Test style bounded threshold. It is simpler than full set-valued conformal prediction and is the same idea as shrewd's bounded routing.
- ASSUMED **sample math**: with ~50 positives per rare signal, a 90% upper bound on error is wide (the "zero errors in n" rule gives roughly 2.3/n ≈ 4.6% at best). Enrich rare-signal samples through lexicon hits and the teacher, and accept that frustration bounds stay loose. State this honestly to the judges.
- ASSUMED **per script or script variant**: calibrate on the Devanagari set (live distribution). If a separate romanized set exists, keep separate thresholds, because conformal guarantees break under the romanized→Devanagari shift.
- ASSUMED **online updates**: with ~40 demo calls (~200 seller turns, maybe 20–60 teacher labels), re-running the bound live will not move thresholds meaningfully. Recalibrate in batch only between rounds, and show the numbers.

### Gaps
- No published conformal results for voice or dialogue signal detection, or for Jev specifically.
- Actual positive counts per signal in an enriched ps07 sample are unknown until the eval set is built.

## Q4. The five improvement mechanisms compared (latency, evidence, cost, 2-day build, live demonstration, risks)

### Takeaway
Ranked for this hackathon:
1. **Threshold calibration plus cascade timing** (mechanisms 3 and 5): high value, low risk.
2. **Teacher-labelled offline eval plus lexicon/TF-IDF student retrain between rounds** (mechanism 4, light): moderate.
3. **kNN memory in Jev state** (mechanism 2): the best *live* demo of "learning" but untested, and it carries leakage and poisoning risk.
4. **Criteria optimisation** (mechanism 1): one offline pass at most.
5. **simple-jev/RFDT or encoder students**: out of reach without a GPU.

### Cited Findings
- See Q1–Q3 sources. Additional evidence:
  - DOCUMENTED: GEPA beats GRPO by 6% on average with up to 35× fewer rollouts (an ICLR 2026 oral). It still uses hundreds of rollouts per task. — [GEPA, arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
  - DOCUMENTED: Trajectory poisoning of self-evolving skill systems ("PoisonedEvolution") embedded target behaviour in 546/600 trials (91.0%) at 10% attacker support in SkillClaw, and 369/600 (61.5%) on Trace2Skill. — [arXiv 2608.05563](https://arxiv.org/pdf/2608.05563). The tweet-cited "SkillPoison (95.7%)" paper could not be located directly; it is cited only via [the X post in our raw dump](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md).
  - DOCUMENTED: shrewd pitfalls: "Better teacher labels didn't always improve students"; teacher errors propagate. — [sshah03/shrewd](https://github.com/sshah03/shrewd)

### Inferences
ASSUMED comparison (latency is the added critical-path latency):

| # | Mechanism | Added critical-path latency | Accuracy evidence | Cost | 2-day build | How "learning" shows live | Main risks |
|---|---|---|---|---|---|---|---|
| 1 | Criteria/instruction optimisation with teacher labels | 0 (offline) | Mixed: GEPA strong on benchmarks; Jev regressed −3.67 pts with another model's tuned policy; shrewd says gains vanish on test | ~$1 Jev + LLM time | 3–6 h for a small search; full GEPA ≥1 day | "v1 criteria → v2 criteria" accuracy on a locked set | Overfitting to dev; criteria/instruction mismatch confuses Jev |
| 2 | kNN corrected examples in Jev `state` | ~+5 ms retrieval; Jev latency ~unchanged (+100–250 tokens) | Inter-Cascade: +33% weak-model accuracy via retrieved strong-model strategies (no Jev evidence); Jev distractor warning | negligible | 4–6 h (TF-IDF char-gram retriever + memory store + A/B) | A teacher correction on call N changes Jev's p on a similar turn in call N+1; show the "neighbours used" panel | Leakage (scripted cards repeat → memorisation looks like learning); poisoning or teacher error persisting; distractor hurt |
| 3 | Threshold calibration per signal/script (bounded/conformal) | 0 | Conformal Cascade gains on 49/72 pairs; shrewd's naive thresholds fail 4–7/10 | ~0 | 2–3 h after the eval set | Before/after precision and coverage table per signal | Small n → loose bounds; shift romanized→Devanagari breaks exchangeability |
| 4 | Distil into local student (simple-jev+RFDT / encoder / TF-IDF) | TF-IDF <1 ms; encoder 3–30 ms (GPU-trained); 0.8B decoder unknown, likely hundreds of ms on CPU | Red Hat: small classifiers 33–54 ms with top-tier accuracy; shrewd TF-IDF matches teacher on 70–80% coverage | TF-IDF ~0; RFDT needs a GPU | TF-IDF 3–4 h; encoder/RFDT not feasible without a GPU | "Student v1 → v2 after N new teacher labels" on the locked set; student coverage climbing | Teacher errors baked into weights; Devanagari train/test mismatch |
| 5 | Cascade order and timing (lexicon/student → Jev → async teacher) | 0 (teacher async; lexicon in the instant path) | Industry sidecar pattern (decision_block Q5); Veris: sync classification doubled latency for no gain | Teacher ~$0.0001–0.001 per call (ASSUMED) | 3–4 h on top of the existing B5/B6 | Trace shows source per decision: lexicon → jev → teacher | Teacher arrives late (after the call ends); double tool calls racing |

- ASSUMED **guardrails against feedback loops and poisoning**:
  - **Two-key promotion:** a teacher label enters memory only if Jev and the teacher agree, or if it is human-confirmed. Uncertain-band disagreements are queued, not promoted.
  - **Locked test set** never touched by updates. Each promotion batch must not lower locked-set accuracy (regression gate).
  - **Memory cap** per signal, with provenance (`source`, `teacher_model`, `call_id`, `ts`) and a one-click rollback.
  - **Exclude simulated-seller cards** that appear in evaluation from memory, to prevent leakage.
  - **Rate-limit** promotions per call, so one adversarial or odd call cannot flood memory (PoisonedEvolution worked at 10% attacker support).
  - **The teacher never writes directives or criteria live.** It only emits labels.

### Gaps
- No head-to-head evidence that any of these loops improves *voice switch timing*. All the accuracy evidence is from text classification or QA.
- No evidence on kNN examples inside Jev state (mechanism 2).

## Q5. Which LLM teacher, and at what latency? (It must run off the critical path.)

### Takeaway
Use **Sarvam `sarvam-105b-conversations` (or 30B) with reasoning off and JSON-schema output** as the primary teacher. It keeps the "core is Sarvam" story and it reads Devanagari natively. Fall back to a fast OpenRouter model for labelling throughput offline. Non-reasoning Sarvam latency is **unpublished**, so measure it (one curl). Live teaching only needs ≤ ~3 s, and offline labelling has no deadline.

### Cited Findings
- DOCUMENTED: The Sarvam chat API lists `sarvam-105b` and `sarvam-105b-conversations` ("post-trained for real-time dialogue and voice-agent workloads"). Thinking is "on by default (`low`)" and can be disabled with `reasoning_effort: null`. JSON-schema output is supported. — [Sarvam Chat Completions](https://docs.sarvam.ai/api/chat-completion/overview) (via [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md))
- DOCUMENTED (third party, conflicting):
  - decision_block cites Artificial Analysis TTFT of 13.86 s (30B) and 22.31 s (105B) in "high" reasoning mode.
  - A search snippet today reported "2.06 seconds" TTFT for Sarvam 30B (high).
  - The fetched Artificial Analysis page itself now shows "No data available" for TTFT and output speed, and $0.03 per 1M tokens.

  **Treat all three as unreliable**; measure ourselves. — [Artificial Analysis Sarvam 30B](https://artificialanalysis.ai/models/sarvam-30b/providers); [Artificial Analysis Sarvam provider](https://artificialanalysis.ai/providers/sarvam)
- DOCUMENTED (third party): Llama 3.1 8B TTFT ~0.13 s on fast providers for short prompts (via decision_block). OpenRouter adds a hop (PROVEN ~150 ms overhead for the Decisions API from India). — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md); [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: RFDT teacher labelling uses any OpenAI-compatible endpoint at temperature 0 with caching. That means the Sarvam or OpenRouter teacher can feed RFDT later without code changes. — [RFDT README](https://raw.githubusercontent.com/featherless-ai/simple-jev/main/RFDT/README.md)

### Inferences
- ASSUMED **teacher prompt**: give it the last 2–3 seller turns plus the last agent turn (Devanagari), the signal definitions (the same text as the Jev criteria, to keep one source of truth), and the Jev p's. Output a JSON label per signal plus a short reason (for the demo panel).
  - Show it Jev's p's? That raises agreement bias. Prefer **blind** labelling, then compare.
- ASSUMED **live budget**: fire the teacher only on inconclusive turns (estimated 10–30% of turns), with one in flight per call and a 3 s hard timeout. If the teacher answers after the next tool call arrives, it still logs a label for learning but does not change the switch.
- ASSUMED: Use a **stronger OpenRouter model offline** to label the ps07 calibration set. Spot-check ~100 against human labels to estimate teacher error, because teacher errors propagate.

### Gaps
- No measured latency for Sarvam LLMs in non-reasoning mode on a short JSON classification.
- Teacher accuracy on Devanagari seller turns is unknown.

## Q6. How do we log and display the learning?

### Takeaway
Extend the existing per-call JSONL trace (B8) with the decision **source** and the **teacher-correction events**. Display three things in B10:
1. A live **switch log** showing what drove each decision and when.
2. A **"corrected by teacher" feed** showing promotions and their effect.
3. A **locked-set accuracy and coverage chart per learning version** (v0 → v1 → v2).

The chart must be computed on a frozen held-out set, not on the live calls being demoed.

### Cited Findings
- PROVEN or DOCUMENTED design: the B8 trace store (JSONL plus DuckDB/SQLite) and the B10 dashboard (poll, no SSE through a quick tunnel) are planned. — [system design](../../../wiki/projects/vani-hackathon/system-design.md)
- DOCUMENTED: The proposed trace fields are `call_key`, `turn_no`, text hash, lexicon hits, Jev p's, latency, mode and switch flag. — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md)
- DOCUMENTED: RFDT and shrewd report agreement with the teacher separately from ground-truth accuracy ("Mode agreement … is not ground-truth accuracy"). — [RFDT README](https://raw.githubusercontent.com/featherless-ai/simple-jev/main/RFDT/README.md)

### Inferences
- ASSUMED **trace additions per turn**:
  - `decision_source` (lexicon | student | jev | teacher | cache).
  - `jev_band` (conclusive_pos | conclusive_neg | uncertain).
  - `teacher_label`, `teacher_latency_ms`, `teacher_arrived_before_next_turn` (bool).
  - `memory_neighbours` (ids only).
  - `learning_version`.
  - `switch_event`, plus `switch_latency_turns` relative to the first cue.
- ASSUMED **events table**: `{event: teacher_correction | promotion | rejection | rollback, signal, from, to, gate_result, version}`.
- ASSUMED **judge-facing panel**:
  - Per call: a timeline of seller turns with chips (lexicon/Jev/teacher) and the switch moment.
  - A counter: "teacher consulted on X% of turns, of which Y% overturned Jev".
  - A version chart: locked-set F1 per signal and teacher-call rate going down, which is the shrewd/Inter-Cascade cost story.
- ASSUMED: Keep the **ON/OFF paired design** (B7) for the headline claim. "Learning v2 vs v0" is a secondary chart.

### Gaps
- None external. The design fields are untested.

## Q7. Devil's advocate: does an online-learning loop help the 25% "correct, well-timed switches" in a 2-day hackathon? And what is in or out of PS04 scope?

### Takeaway
Mostly **no**. Live data during the event is tiny: ~40 simulated calls ≈ 200 seller turns ≈ tens of teacher labels. That is far below the ~200–1,000 labels that bounded thresholds need, and scripted cards make memory gains look like memorisation. The switch score is driven by **instant-path recall on Devanagari** and **policy timing** (hysteresis, persistence, dedup), and those are improved most by **offline calibration and lexicon/student training on transliterated ps07 turns** labelled by Jev and the teacher.

Keep the online loop small (teacher on inconclusive turns plus gated kNN memory) as a credible "self-improving" story. Present the offline pipeline as the same loop run in batch.

### Cited Findings
- PROVEN: The minimal experiment is 10 cards × 2 seeds × 2 arms = 40 calls (~60 min). — [system design](../../../wiki/projects/vani-hackathon/system-design.md)
- PROVEN (ps07 aggregate): 12,015 calls and 64,625 seller turns; median 5 seller turns per call; 99.37% Latin script vs live Devanagari ASR. — [decision_block.md](../VANI%20problem%20choice%20and%20system%20design/decision_block.md)
- DOCUMENTED: Bounded routing needs ~1,000 judged documents ([shrewd](https://github.com/sshah03/shrewd)). Conformal needs roughly n ≥ 200 and exchangeability ([Conformal Cascade](https://www.alphaxiv.org/abs/2607.25018.md)).
- DOCUMENTED (anecdote, low weight): "self improving agents improve every loop right up until the live demo, then regress to the mean". — [X post in raw dump](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md)
- PROVEN: Live tool input is Devanagari with ASR errors. — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences
- ASSUMED **where the 25% is won**:
  - (i) The rushed reply on the *same* turn (lexicon/student).
  - (ii) No false switches (Jev cancel rule, calibrated θ_high).
  - (iii) Exits and dwell.
  - (iv) Implicit frustration on the next turn (Jev, with the teacher on uncertain turns).

  Only (iv) benefits from the live teacher, and frustration is rare (1.7% of calls), so a live loop moves the score little.
- ASSUMED **higher-value version (do this first)**:
  1. Sample ~3–5K ps07 turns (enriched), transliterate them to Devanagari, and label them with Jev plus the teacher.
  2. Hand-label ~200–300 as the locked gold set.
  3. Fit θ bands per signal.
  4. Train the char-n-gram student.
  5. Tune the lexicon from student errors.
  6. Seed the kNN memory from verified labels.

  This *is* the self-improving loop, run offline. The live loop reuses the same code.
- ASSUMED **scope flags for PS04 (Persona Design)**:
  - In scope: the signal → switch → directive path and its evaluation.
  - Out of scope or risky:
    - Teacher LLM writing **directives or spoken replies** live (Sarvam must speak, and directives are pre-written).
    - **Fine-tuning a model** (no GPU; adds time but no PS04 value).
    - Building a **generic self-improving agent platform**.
    - **Post-call quality scoring** of calls, which drifts toward the Quality Audit problem.
    - Using the OpenRouter teacher as the "core decision-maker": keep Sarvam as the core agent and Jev/teacher as components.
  - Hosting the teacher on an outside vendor is not allowed. Use Sarvam, OpenRouter or the LiteLLM gateway only.
- ASSUMED **flip condition**: if the A/B of kNN memory on the locked set shows no gain, or a loss (the Jev distractor risk), drop mechanism 2 and present calibration plus student versions as the learning story.

### Gaps
- Judges' weighting of "self-improving" within the 25% is unknown. The rubric names correctness and timing, not learning.
- Teacher error rate and Jev Devanagari accuracy are both unmeasured. They must be measured before claiming any learning gain.
