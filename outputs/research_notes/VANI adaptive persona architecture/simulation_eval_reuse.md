# Simulated-caller harnesses, causal-lift evaluation, and reuse for Quality Audit (#1) and A/B testing (#5)

Research date: 2026-10-07. Material dated before 2025 is labelled "(older)". No IndiaMART customer data is used in these notes.

## 1. Open-source simulation/eval tools: Egma, chanl-eval and others. Licences, architecture, custom WebSocket support, persona formats, scorecards

### Takeaway
No open-source tool found here has a ready adapter for a Sarvam Samvaad WebSocket agent. chanl-eval (MIT, TypeScript/NestJS, text-only) and Egma (MIT, LiveKit/Retell adapters) are useful as references for design and scorecards, but both are young. The Pipecat release-eval harness (BSD-2) is the closest model for "LLM persona + optional TTS audio + judge". The practical route is a thin custom Python harness built on `sarvam-conv-ai-sdk` that borrows persona and scorecard ideas from these tools.

### Cited Findings
**chanl-eval**
- An "open-source engine for stress-testing AI agents with simulated conversations, adaptive personas, and per-criteria scorecards"; MIT licence; repo github.com/chanl-ai/chanl-eval; announced April 1, 2026 — [channel.tel blog](https://www.channel.tel/blog/chanl-eval-open-source)
- Three concepts: Scenarios (situations), Personas (adaptive customer traits such as emotion, patience and formality, set with UI "trait sliders"), and Scorecards (per-criterion verdicts). It has a CLI for CI with YAML test files, a Docker Compose deployment, and tool fixtures that mock APIs. A Python SDK is "planned". The roadmap lists pytest integration, batch parallel execution and MCP — [channel.tel blog](https://www.channel.tel/blog/chanl-eval-open-source)
- Repo state at fetch time: 18 stars, 9 forks, 95 commits. It is a monorepo of `scenarios-core` (persona engine + LLM adapters), `scorecards-core` (9 criterion handlers), a NestJS server (port 18005), a TS SDK, a CLI, and a Next.js dashboard (port 3010) — [GitHub chanl-ai/chanl-eval](https://github.com/chanl-ai/chanl-eval)
- Agent adapters: OpenAI, Anthropic, and OpenAI-compatible endpoints (Ollama, Together, vLLM, Azure). No WebSocket or custom-HTTP adapter is mentioned, and voice testing is roadmap-only — [GitHub chanl-ai/chanl-eval](https://github.com/chanl-ai/chanl-eval)
- The 9 scorecard criteria are keyword match, LLM judge, response time, tool-call verification, hallucination, RAG faithfulness, knowledge retention, conversation completeness and role adherence — [GitHub](https://github.com/chanl-ai/chanl-eval)
- CLI includes `chanl-eval compare --scenario X --prompt-a Y --prompt-b Z` for A/B prompt comparison and `chanl-eval generate --from-prompt` to auto-generate scenarios — [GitHub](https://github.com/chanl-ai/chanl-eval); [channel.tel blog](https://www.channel.tel/blog/chanl-eval-open-source)

**Egma**
- An open-source platform for simulation testing, production monitoring and self-improvement of voice agents. You define custom caller personas ("angry, confused, overly verbose"), graders, tool mocking and pass/fail thresholds. It runs synthetic voice **and** text multi-turn conversations from the codebase via the Egma CLI or coding agents. Adapters exist for LiveKit (JS/TS) and Retell AI. MIT licence; self-host (default port 3101) or Egma Cloud — [voiceaispace Egma listing](https://www.voiceaispace.com/tool/egma-ai); [voiceaispace repo page](https://www.voiceaispace.com/knowledge/repo/0d3a7395-bb40-451c-97ae-c38211c846fa)
- Bring-your-own STT, LLM and TTS keys; tests are written alongside the code in the repo — [voiceaispace Egma listing](https://www.voiceaispace.com/tool/egma-ai)
- There is an `egma` package on PyPI described as "Egma SDK for livekit Python agents" (the page did not render when fetched) — [PyPI egma](https://pypi.org/project/egma/)

**Other open-source options (Cekura survey dated Sept 23, 2026)**
- Pipecat release-eval harness, BSD-2-Clause: "scripted and simulated conversations, in text or synthesized audio", run locally. Framework-specific — [Cekura blog](https://www.cekura.ai/blogs/open-source-voice-agent-testing-tools)
- How the Pipecat harness works: it is an RTVI client connecting to bots started with `-t eval`. "Simulated scenarios" use "an LLM playing a caller with a goal... hangs up when the goal is reached or clearly out of reach". Text mode is fast and silent; audio mode synthesises user turns with Kokoro TTS and caches them; `./run.sh --repeat 50` measures pass rates; results are written to `results.jsonl` with audio recordings. Verdicts come from **Jev** (hosted TypeSafe classifier, API key needed), with local Ollama `gemma4:12b` as a fallback explainer — [Pipecat evals/release README](https://github.com/pipecat-ai/pipecat/tree/main/evals/release)
- LiveKit Agents test framework (Apache-2.0): turn-by-turn assertions on messages, tool calls and handoffs **in text** via pytest/Vitest — [Cekura blog](https://www.cekura.ai/blogs/open-source-voice-agent-testing-tools)
- EVA-Bench (ServiceNow, MIT per Cekura): bot-to-bot **audio** conversations, 213 scenarios in 3 enterprise domains, accent/noise perturbations. It includes "automatic simulation validation that detects user simulator error and regenerates conversations before scoring". It reports two composites: EVA-A (task accuracy, faithfulness, speech fidelity) and EVA-X (conversation progression, spoken conciseness, turn-taking timing). It reports pass@1, pass@k and pass^k. Across 12 systems, the median pass@k − pass^k gap was 0.44 — [arXiv 2605.13841](https://arxiv.org/abs/2605.13841); [Cekura blog](https://www.cekura.ai/blogs/open-source-voice-agent-testing-tools)
- voicetest (Apache-2.0): LLM-simulated users against imported Retell, Vapi, LiveKit, Bland or Telnyx agents. Voice Lab (Apache-2.0) tests the LLM and prompt only. cekura-ai/metrics (Apache-2.0) is 7 Python modules for transcript-based LLM judging, usable outside Cekura — [Cekura blog](https://www.cekura.ai/blogs/open-source-voice-agent-testing-tools)
- τ2-bench, promptfoo and DeepEval are described as evaluating models rather than simulating agents — [Cekura blog](https://www.cekura.ai/blogs/open-source-voice-agent-testing-tools)
- FutureAGI has an "Agent Simulate SDK" with LiveKit and Retell integrations — [FutureAGI docs](https://docs.futureagi.com/docs/sdk/simulate) (licence not verified)

### Inferences
- None of these tools can drive a Sarvam Samvaad agent out of the box. The lowest-risk path is a small custom Python harness. It would contain: a persona-LLM loop via OpenRouter, Bulbul TTS producing 16 kHz PCM, `AsyncSamvaadAgent` streaming that audio, agent transcript and audio callbacks (plus Saaras STT if agent text is not exposed), a JSONL trace, and a judge. It would copy chanl-eval's persona-trait and scorecard taxonomy and the Pipecat/EVA-Bench conventions (goal-based hang-up, `--repeat N`, simulator-error validation, pass^k).
- chanl-eval's `compare --prompt-a --prompt-b` is the same shape as both problem #5 (variant comparison) and the ON/OFF persona test. This is good framing for the jury: "same harness, different arm".
- Cekura, Coval, Hamming and FutureAGI are commercial. Use them only as methodology references, not as recommended components.

### Gaps
- I could not reach Egma's GitHub repo URL, star count or release cadence directly; the licence and features come from a directory listing site (voiceaispace), so verify on egma.ai before citing in the deck.
- No source was found on chanl-eval's exact persona YAML schema.
- Jev's licence and availability (hosted vs open weights) were not confirmed; Pipecat calls it a "hosted classifier". It is probably **not** an allowed component under the open-source/Sarvam/OpenRouter rule. If the team's "Jev labels" mean labels already produced by Jev on the 12K calls, they can be used as data, but a live judge should be an OpenRouter or open model.

## 2. Building realistic simulated sellers from historical transcripts, and validating realism

### Takeaway
Off-the-shelf LLM simulators drift from their persona and are unrealistically patient and verbose. Ground the persona cards in empirical distributions from the 12K calls (turn length, objection types and their timing, language mix, hang-up points). Make behaviour scripts event-driven with seeded stochasticity. Before trusting any lift number, validate realism with persona-consistency metrics and a discriminator test against real transcripts.

### Cited Findings
- LLM simulators show a "realism gap": "excessive verbosity, lack of a consistent persona, inability to express coherent preferences, unrealistic 'knowledge,' and unreasonable patience" — [ConvApparel, arXiv 2602.16938](https://arxiv.org/html/2602.16938v1)
- Off-the-shelf LLMs "often drift from their assigned personas, contradict earlier statements, or abandon role-appropriate behavior". Proposed metrics are prompt-to-line consistency, line-to-line consistency and Q&A consistency, validated against human annotations. Multi-turn RL reduced inconsistency by >55% (NeurIPS 2025) — [arXiv 2511.00222](https://arxiv.org/abs/2511.00222v1); [NeurIPS 2025](https://proceedings.nips.cc/paper_files/paper/2025/hash/4c91443877f8388d8190c938ac5a4d4d-Abstract-Conference.html)
- Simulations often lack verification that enough personas are covered; one paper studies identifying missing personas for a simulation context — [arXiv 2602.15832](https://arxiv.org/html/2602.15832v1)
- EVA-Bench detects user-simulator errors automatically and regenerates the conversation before scoring, so simulator failures are not counted as agent failures — [arXiv 2605.13841](https://arxiv.org/abs/2605.13841)
- The Pipecat simulated caller is goal-conditioned: it ends the call when the goal is reached "or clearly out of reach" — [Pipecat evals README](https://github.com/pipecat-ai/pipecat/tree/main/evals/release)
- Commercial persona design (Egma, chanl-eval) uses traits such as emotion, patience and formality, with archetypes like angry, confused and verbose — [channel.tel](https://www.channel.tel/blog/chanl-eval-open-source); [voiceaispace Egma](https://www.voiceaispace.com/tool/egma-ai)

### Inferences
- **Persona card schema** (derived from the 12K calls, fully synthetic and de-identified):
  - Identity: `seller_segment` (e.g. manufacturer, trader or service; tenure; category), `primary_language`, `code_mix_ratio`, `switch_trigger` (e.g. switches to Hindi after agent confusion or after turn k).
  - Behaviour: `patience_budget_turns`, `rush_level`, `frustration_curve` (starting level plus increments per unanswered question), `verbosity` (target words per turn, sampled from the empirical distribution), `objections[]` (type, earliest turn, probability; drawn from the objection evaluator's frequency table), `questions[]`, `hidden_goal` (e.g. willing to fix a meeting only if objection X is resolved), `hangup_rule`.
  - Reference: `evidence_refs` pointing to cluster IDs, not raw calls. This supports the "support from past-call evidence" metric.
- Build cards by clustering real calls on outcome, objection set, language and length. Sample card parameters from each cluster's empirical distribution so the simulated population matches real mix proportions. Hold out a test split of clusters so personas are not tuned to the same calls used to design the adaptive policy.
- **Stochasticity**: fix `seed` per (card, run_index), covering the persona-LLM sampling seed (where OpenRouter providers honour it), the objection-order draw and the frustration noise. Use the identical seed in both ON and OFF arms. LLM sampling is not fully deterministic across providers, so record the realised event script and replay the same script in both arms.
- **Realism validation** (cheap, credible to a jury):
  1. Distributional match: simulated vs real turn length, call length, objection frequency, language-switch rate (KS test or histogram overlay).
  2. A judge discriminator: an LLM shown a real transcript and a simulated one guesses which is real. Near-50% accuracy means realistic.
  3. Persona-consistency checks from arXiv 2511.00222: prompt-to-line and line-to-line consistency.
  4. A simulator-error filter in the style of EVA-Bench: discard and regenerate runs where the simulator broke character or leaked its instructions.

### Gaps
- No published realism benchmark specific to Indian-language or code-mixed B2B seller simulation was found.

## 3. Experiment design for causal lift with small N: paired seeds, number of runs, metrics, LLM-judge reliability

### Takeaway
Use a within-persona paired (crossover) design: the same persona card, seed and scripted event schedule runs once with adaptive persona ON and once OFF. Analyse paired differences (McNemar or exact sign test for binary outcomes; paired t-test, Wilcoxon or bootstrap for scores), with ≥3 repeats per pair to average out simulator noise. Roughly 30–40 persona pairs detect a medium effect; ~15 suffice only for a large one. Report pass^k (reliability), not only pass@1. Control LLM-judge bias by blinding the arm, randomising order and calibrating on a small human-labelled set.

### Cited Findings
- Strong LLM judges (GPT-4) reach >80% agreement with human preferences, the same level as human–human agreement. Known biases are position, verbosity and self-enhancement, plus limited reasoning, and the paper proposes mitigations (2023, older) — [Zheng et al., arXiv 2306.05685](https://arxiv.org/abs/2306.05685)
- Jev (typed classifier) vs LLM judges on 9 benchmark panels: accuracy differed significantly in at most 8 of 27 paired comparisons. Jev was better on binary criteria and worse on ordinal scales. When Jev was confidently wrong, ~96% of LLM judgments made the same error. LLM judges cost 16–325× more and took 28–350× longer. Cascading the two gained at most 2.7 points over the best single judge — [arXiv 2609.29769](https://arxiv.org/abs/2609.29769)
- Practitioner guidance: use a typed or classifier judge when the verdict is "narrow and typed (a label, a level on a rubric, or a yes/no)" and needed at volume — [Langfuse Jev-as-a-judge docs](https://langfuse.com/docs/evaluation/evaluation-methods/jev-as-a-judge.md); [Arize blog](https://arize.com/blog/typesafe-jev-llm-judge/)
- Peak and reliable performance diverge a lot (median pass@k − pass^k gap 0.44), so repeated runs are needed — [EVA-Bench](https://arxiv.org/abs/2605.13841)
- The Pipecat harness supports `--repeat 50` specifically "to measure pass rates" — [Pipecat evals README](https://github.com/pipecat-ai/pipecat/tree/main/evals/release)

### Inferences
- **Why paired seeds give causal lift**: the persona card, seed and event script are held fixed and only the arm flag changes. Any difference is therefore attributable to the adaptive persona, up to residual LLM nondeterminism, which the repeats handle. This is a randomised crossover design with the simulated seller as its own control. Randomise arm order and run the arms interleaved in time, so provider latency drift or rate limits do not confound the result.
- **Sample-size rules of thumb** (standard paired-test power at α=0.05 two-sided and 80% power; my calculation, not from a source): a paired standardised effect d=0.8 needs ~15 pairs, d=0.5 ~34 pairs, d=0.3 ~90 pairs. For a binary "meeting fixed" proxy, power depends on the number of **discordant** pairs. Detecting e.g. 30% vs 50% success needs roughly 80–100 pairs, so a binary outcome alone is weak at hackathon N. Lead with continuous or ordinal judge scores and use the binary result as supporting evidence.
- **Suggested hackathon budget**: 20–30 persona cards × 3 seeds × 2 arms gives 120–180 calls. At ~2–4 minutes per voice call with 10–20 parallel sessions, that is roughly 30–60 minutes of wall-clock time. Report the mean paired difference with a 95% bootstrap CI (resampling persona cards, not calls, because calls within a card are correlated) and a sign or Wilcoxon p-value.
- **Metrics**:
  - Outcome: meeting-fixed proxy (the agent extracts a confirmed slot), objection resolved (per objection, from the existing objection evaluator), seller-initiated hang-up before goal, and call length (report it but do not optimise it; shorter is not always better).
  - Persona-specific: persona fit (an ordinal 1–5 rubric conditioned on the hidden persona card), switch correctness (did a switch happen within N turns of the scripted trigger, and was the target style appropriate?), false-switch rate (switches with no trigger), distinctness (an embedding or LLM-classifier check that styles are distinguishable) and language naturalness in 2+ languages.
  - Timing can be scored **deterministically**: because the event script is known (e.g. frustration injected at turn 5), switch latency in turns and seconds needs no judge. This is the most jury-convincing metric because it is objective.
- **Judge design**: use typed, binary or anchored-ordinal questions in a single call per criterion. Hide the arm label, strip system-prompt artefacts, and use a judge model from a different family than the agent and simulator (e.g. a different OpenRouter open model) to reduce self-enhancement bias. For pairwise comparisons, swap positions to cancel position bias. Use ensemble or majority voting across 2–3 open judges. Calibrate on ~30–50 human-labelled calls per criterion, report Cohen's κ, and only claim lift on criteria with acceptable agreement (κ ≳ 0.6 is a common threshold; not from the sources above).
- **Voice vs text simulation**: run the **headline experiment voice-to-voice**. The persona claim includes "natural voice in 2+ languages" and switch timing, which text cannot show, and EVA-Bench and Pipecat audio mode set precedent that juries recognise. Use text-mode or cached-TTS runs only for fast iteration. As with Pipecat's TTS caching, cache Bulbul audio per (seed, turn text) to cut cost and latency on repeats.

### Gaps
- Sarvam Samvaad does not appear to offer a text-only channel into the deployed agent (the brief says audio only); I did not verify this in Sarvam docs. If true, every simulated call incurs Bulbul TTS for the seller side plus agent-side STT/LLM/TTS, so per-call cost and latency should be measured in a pilot.
- No published human-agreement numbers specific to "persona fit" or "switch correctness" rubrics were found. These need in-house calibration.

## 4. Daytona sandboxes for parallel sessions: licence, SDK, limits, public preview URLs

### Takeaway
Daytona's public repo (AGPL-3.0, last open release v0.190.0) has been **archived**: core development went private in June 2026 and the repo was marked read-only on Oct 3, 2026. The community fork "Nightona" continues the AGPL code. The hosted Daytona SDK still offers preview URLs on any port, which suits exposing a webhook server. **Tier 1/2 accounts have restricted egress**: `openrouter.ai` is on the allowed essential-services list but **sarvam.ai is not**, so Sarvam calls from a Tier 1/2 sandbox will likely be blocked. Use Tier 3+ (full internet) or run the Sarvam-facing harness outside the sandbox.

### Cited Findings
- GitHub daytonaio/daytona: "This repository was archived by the owner on Oct 3, 2026. It is now read-only." and "As of June 2026, Daytona's core development has moved to a private codebase. This repository will receive no further updates, fixes, or releases." The code "remains public and free to use, fork, and build on under the LICENSE, as is" — [GitHub daytonaio/daytona](https://github.com/daytonaio/daytona)
- Last open release v0.190.0 under AGPL-3.0. Nightona is a community fork with full history (2,700+ commits) continuing from v0.190.0 under AGPL-3.0, "self-hosted first". Features: dedicated kernel/filesystem/network/vCPU/RAM/disk per sandbox, "spin up in under 90ms", SDKs in Python, TypeScript, Ruby, Go and Java plus REST and CLI, and process exec, filesystem, git, LSP, PTY, log streaming and preview URLs — [Nightona README](https://cdn.jsdelivr.net/gh/nightona-co/nightona@main/README.md)
- Preview URLs work on ports 1–65535 with format `https://{port}-{sandboxId}.{proxyDomain}`. `get_preview_link()` returns a URL plus a sandbox-wide token sent in the `x-daytona-preview-token` header (not revocable). `create_signed_preview_url()` embeds a port-specific token that expires after 1–86,400 s and can be revoked with `expire_signed_preview_url()`. Public sandboxes allow unauthenticated access. Stopping and restarting a sandbox issues a new token. A browser warning page appears unless the request sends `X-Daytona-Skip-Preview-Warning: true` or the org is Tier 3 — [Daytona docs: Preview](https://www.daytona.io/docs/en/preview-and-authentication/)
- Org resource limits by tier: T1 10 vCPU / 20 GiB / 30 GiB disk; T2 100 vCPU / 200 GiB / 300 GiB; T3 250 / 500 / 2,000; T4 500 / 1,000 / 5,000. Unlocks: T1 email verification, T2 card + $25 top-up, T3 $500, T4 $2,000. Concurrency is bounded by aggregate resources, not a fixed sandbox count — [Daytona docs: Limits](https://www.daytona.io/docs/en/limits/)
- Network: on Tier 1 & 2, "Network access is restricted and cannot be overridden at the sandbox level", with only essential services reachable. Tier 3 & 4 get full internet by default and an optional `domain_allow_list` (max 100 entries) — [Daytona docs: Network limits](https://www.daytona.io/docs/en/network-limits/)
- The essential services list includes package registries, GitHub/GitLab, Docker registries, and AI APIs (Anthropic, OpenAI, Google, Groq, Hugging Face, DeepSeek… and `openrouter.ai`). **sarvam.ai is not listed**, and no whitelist-request process is documented — [Daytona docs: Network limits](https://www.daytona.io/docs/en/network-limits/)

### Inferences
- Pattern: one orchestrator sandbox runs a FastAPI webhook/dashboard server, exposed via a public preview URL, or a signed URL for a time-boxed demo link. N worker sandboxes (or N asyncio tasks in one sandbox) each run one simulated-seller session. At ~1 vCPU per session for TTS I/O and PCM streaming (this is I/O-bound, so it is likely less), Tier 1's 10 vCPU fits roughly 10–20 concurrent sessions, but Tier 1 cannot reach Sarvam.
- To satisfy "runs in Daytona", there are three options:
  - (a) Top up to Tier 3 ($500) for full egress.
  - (b) Self-host Nightona or the last AGPL Daytona release, so the team controls egress.
  - (c) Keep the Sarvam WebSocket client outside Daytona and run only the OpenRouter persona-LLM, judge and dashboard inside.
  Ask the hackathon organisers whether they have a sponsored Daytona tier or allow-list first.
- Licence note: AGPL-3.0 copyleft applies if Daytona or Nightona source is modified and served over a network. Merely using the hosted service or its SDKs does not create an AGPL obligation for the harness code (general AGPL reading; check the SDK licences separately).
- Daytona's open-source status changed in June–October 2026. Calling Daytona "open source" in the deck is now only partly accurate. Say "Daytona (last AGPL-3.0 release v0.190.0; community fork Nightona)".

### Gaps
- SDK licence (Apache vs AGPL) for the current `daytona` Python package not verified.
- Free credits and auto-stop defaults were not found in the limits doc.
- Whether WebSocket upgrade works through preview URLs was not explicitly documented in the fetched page (HTTP services are documented). Test early.

## 5. Reuse: mapping the harness, Jev labels and evaluator pipeline to Quality Audit (#1) and A/B testing (#5); sequential testing and early stopping

### Takeaway
The architecture is one pipeline: simulated or real call → trace (JSONL) → typed judges and evaluators → aggregation. The adaptive-persona ON/OFF experiment is literally a 2-arm A/B test. Problem #5 generalises it (N variants, traffic split, sequential stopping, auto-promote). Problem #1 points the same judges at real calls, adds Fatal/Non-Fatal severity, clusters failures, and feeds fixes back into new simulated regression scenarios. For #5, mSPRT / always-valid p-values or a Bayesian posterior with a stopping rule allow continuous monitoring and early stopping without inflating false positives.

### Cited Findings
- Classic p-values are "wholly unreliable if users make decisions while continuously monitoring their tests". Always-valid p-values (via the mixture SPRT, mSPRT) allow stopping at any data-dependent time while controlling Type I error. This has been deployed at Optimizely since 2015 (older; Operations Research 2022) — [Johari, Pekelis, Walsh, arXiv 1512.04922](https://arxiv.org/abs/1512.04922v2); [IDEAS/RePEc OR 70(3)](https://ideas.repec.org/a/inm/oropre/v70y2022i3p1806-1821.html)
- Power comparisons of sequential tests (SPRT, AGILE group-sequential, always-valid inference) show trade-offs in expected sample size vs power (older, practitioner blog) — [Analytics-Toolkit blog](https://blog.analytics-toolkit.com/?p=1524)
- chanl-eval ships `compare --prompt-a --prompt-b` (A/B of agent prompts on the same scenario) and `dataset generate`. Batch parallel execution is on its roadmap — [GitHub chanl-ai/chanl-eval](https://github.com/chanl-ai/chanl-eval)
- Egma pairs pre-deployment simulation with "production monitoring" that "proactively analyzes production conversations to surface unexpected behaviors, patterns, and failures" such as hallucinations. This is the same simulation-plus-audit loop proposed for #1 — [voiceaispace Egma](https://www.voiceaispace.com/tool/egma-ai)
- Jev-style typed judges are 16–325× cheaper and 28–350× faster than LLM judges at similar accuracy on binary criteria, which makes grading every call feasible. On ordinal criteria they are worse — [arXiv 2609.29769](https://arxiv.org/abs/2609.29769)
- The Pipecat harness writes per-scenario `results.jsonl` with audio and logs, a usable trace format to emulate — [Pipecat evals README](https://github.com/pipecat-ai/pipecat/tree/main/evals/release)

### Inferences
- **Shared components**:
  1. `SellerSim`: persona card, seed, event script, OpenRouter LLM and Bulbul TTS.
  2. `AgentClient`: `AsyncSamvaadAgent`, parameterised by agent/variant ID.
  3. `Trace`: turns, timestamps, language tags, persona-switch events, audio paths.
  4. `Judges`: typed rubric questions on open models via OpenRouter, reusing the existing objection and question evaluators and Jev labels as features or ground truth.
  5. `Aggregator`: paired stats, sequential tests, clustering.
  6. `Dashboard`: served on a Daytona preview URL.
- **#1 Quality Audit mapping**:
  - Run the same judges on real calls.
  - Assign Fatal or Non-Fatal severity per criterion, e.g. Fatal = wrong commitment, misinformation, abusive tone or compliance breach; Non-Fatal = missed objection or slow switch.
  - Cluster failure rationales (embed the judge outputs, then HDBSCAN or k-means) to find root causes.
  - An LLM proposes a prompt diff per cluster. Validate the fix by regenerating persona cards from the failing calls and rerunning them in the simulator with the fix ON vs OFF: the same paired design as section 3. This closes the "fix loop" with evidence.
  - Rank the risk queue by P(Fatal) × seller value.
- **#5 A/B mapping**:
  - Variants = agent configurations or prompt versions. The simulated-traffic phase uses paired seeds, which is high-power and low-N, before live traffic.
  - Live phase: traffic split with mSPRT always-valid p-values, or Bayesian Beta-Binomial on the meeting-fixed proxy with P(B>A) > 0.95 to promote and expected-loss thresholds to stop early. Add guardrail metrics, e.g. a Fatal-rate increase stops immediately (a one-sided SPRT on the Fatal rate).
  - Auto-disposition = the same judges labelling outcomes.
- The adaptive-persona demo is therefore also the demo of #5's engine. "Persona ON vs OFF" is variant A vs B in paired simulation. Showing the identical dashboard for both is a strong reuse story for the jury.
- Caveat: sequential methods assume independent observations, so paired simulated calls should be tested on paired differences per persona-card block, not on individual calls. Simulated results estimate lift on the simulated population only, so live A/B (#5) is the external-validity step.

### Gaps
- No open-source, voice-specific A/B auto-rollout tool was found. The sequential stats would need to be implemented directly (mSPRT is a few lines; Bayesian Beta-Binomial is trivial).
- No sources found on Coval or Hamming methodology pages within the call budget. Hamming, Coval and Cekura are commercial and not recommendable as components anyway.
