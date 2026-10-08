# Choose Persona, then prove the switch

**Persona Design (#4) is the right problem to pick.** It scores about **4.05 of 5** on the deck's weighted rubric, against **3.70 for Quality Audit (#1)** and about 3.5 for Best Time to Call (#3) and A/B Testing (#5). It is the only brief whose required deliverable is itself a live, multilingual voice demo, and its core in-call loop already works in our spikes ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)). The lead is narrow and conditional. Persona falls behind Quality Audit if any of three things happens: the added tool step pushes replies routinely past about 3 s or the agent skips the tool on more than 10% of turns, the Sarvam credits cannot fund about 40–150 simulated calls, or the jury visibly rewards data over voice. The recommended architecture has **ten blocks in three planes**: a pre-call plane (seller context, persona generator, launcher), an in-call plane (the Sarvam Voice Agent, a signal-and-decision server, a background Jev worker) and an evaluation plane (simulated sellers, trace store, metrics and judges, aggregator and dashboard). The key design change from earlier drafts follows from measurement. **Jev through OpenRouter takes ~0.49 s p50 from the office, not ~0.1 s**, so it cannot sit synchronously in the turn. A deterministic Devanagari-aware lexicon decides the current reply in milliseconds, and Jev corrects the state for the next tool call, which often arrives within the same seller turn. Live persona on Sarvam means changes to wording, brevity, disclosure and language over a voice fixed per call. The persona's voice and pace are chosen before dialling. Only the reply wording changes during the call. The same trace, judge and simulator blocks become #1 and #5 by swapping the call source and the aggregator.

## Persona leads by 0.35 points, and four day-1 results can flip it

The deck weights Business Impact 25%, Solution Completeness 20%, Technical Robustness 20%, Voice Experience 20% and Demo & skills.md 15%. Every problem must ship a Sarvam Agent ID and a 5–7 minute video, and "plagiarised or pre-built solutions are disqualified" ([hackathon deck](../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)). Only Persona requires a "voice demo on Sarvam… with at least one live mid-call switch" across "2 to 3 contrasting sellers", so it alone turns the 20% Voice Experience criterion into the deliverable rather than a bolt-on ([hackathon deck](../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)). The scores below are team judgements on the 1–5 scale, weighted by the deck. The evidence behind each cell is cited in the paragraphs that follow.

| Problem | Impact 25% | Complete 20% | Robust 20% | Voice 20% | Demo 15% | **Weighted** | Main risk |
|---|---|---|---|---|---|---|---|
| #4 Persona | 3.5 | 4 | 3.5 | 5 | 4.5 | **4.05** | Tool latency/skip; lift only shown in simulation |
| #1 Quality Audit | 4 | 4 | 4 | 2.5 | 4 | **3.70** | Looks like IndiaMART's existing evaluators |
| #3 Best Time to Call | 4 | 4.5 | 4 | 2 | 3 | **3.55** | Observational confounding; no voice |
| #5 A/B Testing | 3.5 | 3.5 | 4 | 3 | 3.5 | **3.50** | Abstract demo; simulated test bed only |
| #2 Global Context | 3 | 3.5 | 3 | 3.5 | 3.5 | **3.28** | Headline metric contradicts 3 failed trials |
| #7 Seller Enrichment | 3 | 2.5 | 2.5 | 2 | 3.5 | **2.68** | No dataset; web sources would be outside vendors |

Persona's business case is real but correlational. Rush cues appear in **21% of transcribed calls**, and those calls fix meetings at **13.6% vs 26.0%** without them. In 99% of cases the cue first appears mid-call, which is exactly the gap a live switch addresses ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)). Language fit is a second lever: **46.6% of Tamil Nadu calls carry Tamil markers while the bot speaks Hinglish** ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)). The weakness is equally concrete. IndiaMART's three personalised-script trials all lost to control: 14.8% vs 17.8%, 11.1% vs 15.8%, and 3.3% vs 18.4% ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)). So Persona must be pitched as accommodation (shorter, calmer, plainer, native-language replies at the right moment), not as personalised content. Its causal claim can only come from paired simulated calls.

The steelman for **Quality Audit** is that it has the strongest verifiable real-data story. The disposition evaluator labels **55.1%** of 150,821 evaluated calls `call_dropped`. In **14.8%** of 18,768 exec-drop-evaluated calls the seller tried to keep talking after the bot closed. **26%** of latency/repetition-evaluated calls were loopy or had the seller repeat themselves ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)). Its weaknesses are a bolt-on voice demo and a headline metric, "agreement with human auditors", that no provided file can measure, since no human-audit labels were shipped. IndiaMART also already runs ten evaluator agents on VANI calls, so a #1 entry must own clustering, fix generation and tested fixes to look new ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)). **A/B Testing** has the single best business number. One unguarded variant ran on 23,046 calls at 11.1% against 15.8% for control, roughly 1,080 meetings lost under a naive counterfactual. The existing disposition evaluator already reaches **94.3% precision and 89.1% recall** against labelled Meeting Fixed calls ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)). But the judged artefact is a statistics report, not a voice. **Best Time to Call** has 530,748 attempts and a 2.4× unadjusted hour spread, but no randomised schedule and essentially no voice. **Global Context** leads with a "lift from the personalised opening" metric that IndiaMART's own trials contradict. **Seller Enrichment** has no dataset in the Drive folder, and the sources it names (website, Google listing, social pages) would require outside vendors ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)).

Combining problems earns credit only where a piece feeds the chosen problem's expected outputs, because Completeness is "share of the expected outputs delivered and working end to end" and each team picks one problem ([hackathon deck](../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)). Hackathon judges also favour "one thing really well rather than five things halfway" ([JetBrains judging notes](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)). The right shape is therefore #4 as the problem, with a mini-#5 paired experiment and #1-style typed judges serving as its robustness evidence.

The choice flips under these conditions. Each is tied to a test in the verification list near the end.

| # | Trigger (measured on day 1) | Effect on scores | New pick |
|---|---|---|---|
| F1 | Tool skip >10% of turns, or the in-loop design makes replies routinely exceed ~3 s (added p95 > ~0.8 s) | Persona Voice 5→3.5, Robustness 3.5→3 → ~3.65 | **#1 Quality Audit**, on the same harness |
| F2 | Paired ON/OFF simulation shows no lift | Persona Impact 3.5→2.5 → ~3.80 | Stay on #4, but pitch "correct, well-timed switches + language fit", not "more meetings" |
| F3 | Sarvam credits too small for ~40+ simulated calls, or SDK CALL mode unavailable at the venue | Persona loses its evidence leg | #1 (offline on real data), else #3 |
| F4 | Jury signals a business/data emphasis, or many teams visibly pick #4 | #1 overtakes on verifiable impact | #1; #5 only if a known-difference test runs convincingly on simulated sellers |

The margin is thin. A ±0.5 move on any 20–25% criterion shifts a total by 0.10–0.13, so two adverse moves erase the 0.35 lead over #1 ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)). The architecture below keeps that pivot cheap: roughly 70% of the blocks serve #1 unchanged.

## Ten blocks in three planes; only two touch the live turn

Four principles shape the design. The first is that **persona is a set of variables, not a state**. Sarvam's multi-state agents are a legacy paradigm due for end-of-life, Workflows are enterprise-only, and Voice Agents allows no bring-your-own model at any layer ([Sarvam multi-state](https://docs.sarvam.ai/conversations/build/states-conversation-flow); [spike log](../../raw/research/2026-10-07-spike-log.md); [Sarvam models](https://docs.sarvam.ai/conversations/build/models)). The second is a **reflex plus background correction**. Sarvam exposes only LLM-invoked synchronous tools, with no per-turn hook and no async tool mode ([Sarvam API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)). The current turn must therefore be decided by fast deterministic code, while the calibrated model works in the background. The third is that **code owns every switch**. Jev, the lexicon and the LLMs produce signals or wording. A pure, replayable policy function decides. The fourth is **one trace contract**: every call, whether simulated, phone, browser or historical, becomes the same `Trace` record. That record is what lets one set of evaluation blocks serve #4, #1 and #5.

```
 PRE-CALL PLANE (seconds to minutes; off the hot path)
 ┌──────────────────┐   ┌──────────────────────┐   ┌───────────────────────────────┐
 │ B1 Seller Context│──►│ B2 Persona Generator │──►│ B3 Launcher & Channel Adapter │
 │ Builder          │   │ rules + archetypes + │   │ arm assignment; SDK session    │
 │ (internal data → │   │ Sarvam LLM wording;  │   │ or Instant Outbound/inbound    │
 │  seller.md)      │   │ DNC gate; evidence[] │   │ (agent_variables, app_version) │
 └──────────────────┘   └──────────────────────┘   └───────────────┬───────────────┘
                                                                   │ call start
 IN-CALL PLANE (per seller turn; latency-critical)                 ▼
 ┌───────────────────────── B4 SARVAM VOICE AGENT (core; Agent ID) ────────────────────┐
 │ VAD → Saaras v4 ASR → routed Sarvam LLM (single state; playbook keyed on            │
 │ @seller_mode/@persona_directive) → Bulbul v4 TTS (voice fixed per call)             │
 │ every seller turn: API tool read_seller_signal (Max wait 2 s)                        │
 └────────────┬─────────────────────────────────────────────────────▲──────────────────┘
   POST {call_key, seller_utterance, language}          {seller_mode, persona_directive}
              ▼                                                      │  ≤300 ms, HTTP 200 always
 ┌──────────────── B5 SIGNAL & DECISION SERVER (FastAPI, ours) ──────┴─────────────────┐
 │ turn dedup → lexicon (Devanagari/Latin/Tamil/Gujarati, NFD) → policy.step           │
 │ (events + Schmitt hysteresis + budget) → directive table → trace row / switch log   │
 └────────────┬──────────────────────────────────────▲─────────────────────────────────┘
   job {call_key, turn_no, state}                    │ {signal: p}  (stale results dropped)
              ▼                                      │
 ┌──────────── B6 JEV WORKER (async; never blocks the turn) ─────────────────────────────┐
 │ OpenRouter Decisions API, typesafe/jev-1.13 (or LiteLLM /typesafe pass-through)       │
 └───────────────────────────────────────────────────────────────────────────────────────┘

 EVALUATION PLANE (after each call / batch)
 ┌──────────────────┐   ┌───────────────┐   ┌────────────────────┐   ┌───────────────────┐
 │ B7 Simulated     │──►│ B8 Trace Store│──►│ B9 Metrics & Judges│──►│ B10 Aggregator &  │
 │ Seller Harness   │   │ JSONL+DuckDB  │   │ deterministic +    │   │ Dashboard         │
 │ (SDK CALL mode,  │   │ ◄ B5 log      │   │ Jev typed + LLM    │   │ #4 lift | #1 audit│
 │  Bulbul seller)  │   │ ◄ webhooks /  │   │ ordinal, arm-blind │   │ | #5 A/B decision │
 └──────────────────┘   │   Analytics   │   └────────────────────┘   └───────────────────┘
                        └───────────────┘
```

## Block contracts: role, interfaces and evidence status

Each block below has one fixed role, defined inputs and outputs, and a status per capability. **PROVEN** means our own spikes or our aggregate computations on the provided data showed it. **DOCUMENTED** means a vendor or published source states it. **ASSUMED** means it needs a test. A block can have proven pieces and still be unbuilt, and the tables keep the two apart.

### B1 Seller Context Builder turns internal history into eight lines

**Role:** deterministically aggregate one seller's internal data into a feature record and a compact `seller.md`. It writes no prose and never includes buyer names or message text. **Input:** a PS07 seller-file row plus Global Context files (local `data/` for the hackathon; an internal data source in production). **Output:** `SellerContext{seller_key, prev_disposition, n_prior_answered_calls, turnover_band, gst_age, business_type, nature, product_count, zone, pns_languages[], prior_signals{rush,frustration,confusion,bot_q}, dnc, exec_contact, whatsapp_active, enq_30d, buyer_calls_30d}` and `seller.md` (≤8 lines, ≤600 chars).

| Capability | Status | Evidence |
|---|---|---|
| Previous disposition is the strongest pre-call predictor (0.74 of meeting-fixed tree importance; MF 17.4% first call vs 4.4% after NI) | PROVEN (correlational) | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| A seller's own past signals recur: rush 30.8% vs 21.1%, bot-question 22.9% vs 3.5% (954 sellers, small n) | PROVEN (correlational) | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| Context coverage: bot calls 88%, WhatsApp 74%, enquiries 55%, PNS languages 28% of 5,000 GC sellers | PROVEN | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| Context should feed answers, not the opening (30-day enquiry volume correlates negatively with meetings: 12.3% at 0 vs 3.7% at >15) | PROVEN (correlational) | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| Live internal data source at call time (vs files) | ASSUMED | — |

### B2 Persona Generator decides with rules and lets an LLM only phrase

**Role:** map `SellerContext` to a `PersonaSpec` with one evidence record per field. Rules own everything with compliance or measurement stakes: the DNC gate, up-front AI disclosure, archetype, language, voice style, pace and playbook order. A Sarvam LLM writes only the opening wording (within ≤3 templates per archetype × language) and the rationale sentence. **Output:** `PersonaSpec{archetype A0–A5, archetype_reason, start_language, allowed_languages, voice_style crisp|warm|formal, app_version, speaker, pace, pitch=0, opening_text, playbook_order[], disclosure_upfront, evidence[{field,value,rule,inputs,stat,source,tag}], persona_version}`.

The archetypes are cut on call history first and business size second. Language is a separate overlay covering 43% of calls. A0 suppresses DNC sellers. A1 re-engage (37.8% of calls, MF 4.1%), A2 callback follow-up (10.8%, MF 8.1%), A3 meeting follow-up (3.1%, MF 21.7%), A4 established first call (19.5%, MF 14.3%) and A5 micro/new first call (28.8%, MF 19.5%) map to three voice styles. That means three committed agent versions for the phone path ([persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md)).

| Capability | Status | Evidence |
|---|---|---|
| Five archetypes are distinct on outcomes (MF 4–22%, NI 35–46%, median call 13–39 s) | PROVEN (correlational) | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| DNC gate needed: 5,719 answered calls in the window reached sellers with `do_not_call_requested=1` (flag is window-aggregated) | PROVEN | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md) |
| Language rule: TN starts English/Tamil (English in 94% of TN PNS calls; no Tamil conversational v4 voice); GJ starts Hinglish with a Gujarati greeting | PROVEN inputs, ASSUMED policy | [persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md); [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Pace defaults (crisp ~1.1, warm 0.9–0.95, floor ~0.85) grounded in "slightly slower raises satisfaction 7.1%" | DOCUMENTED evidence, ASSUMED mapping | [Knowledge at Wharton](https://knowledge.wharton.upenn.edu/article/how-speaking-slower-influences-consumer-behavior/) |
| Sarvam chat API supports JSON-schema output and reasoning off (`reasoning_effort: null`) | DOCUMENTED | [Sarvam chat completions](https://docs.sarvam.ai/api/chat-completion/overview) |
| Sarvam-105B wording quality in Gujarati/Tamil | ASSUMED | — |
| Persona choice causes lift | ASSUMED (only the paired simulation can show it) | — |

### B3 Launcher and Channel Adapter turns one spec into one call

**Role:** turn a `PersonaSpec` plus an `Arm` into a call on exactly one channel, record the `call_key`, and own arm assignment. **Input:** `PersonaSpec`, `Arm{test_id, arm, adapt_enabled, app_version}` and a channel. **Output:** an SDK session (`InteractionConfig` with `agent_variables`, `initial_bot_message`, `initial_language_name`, `text_to_speech_config{speaker, pace, pitch}`, `version`), an Instant Outbound POST (`app_version`, `agent_variables`, `app_overrides`, `webhook_config`), or an inbound deployment. It returns the `interaction_id` or `attempt_id`. Arms use a hashed split, `hash(seller_id, test_id) mod 100 < share`.

| Capability | Status | Evidence |
|---|---|---|
| SDK CALL mode with `version=1`; separate Voice Agents key | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| SDK CHAT mode returns 404 for this voice agent | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Per-session SDK TTS override (speaker, pace, pitch) | DOCUMENTED; not yet exercised | [Sarvam Python SDK](https://docs.sarvam.ai/conversations/deploy/sdks/python) |
| Instant Outbound has no TTS override, so phone voice = choose an `app_version` | DOCUMENTED | [Instant Outbound create](https://docs.sarvam.ai/conversations/api/instant-outbound/create) |
| Number rental needs KYC first; turnaround undocumented | DOCUMENTED | [Rent from Sarvam](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam) |
| Committed-but-not-deployed version dialable via Instant Outbound | ASSUMED | — |
| Traffic split across versions lives in our launcher (no native split documented) | ASSUMED | [eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md) |

### B4 Sarvam Voice Agent speaks every word and calls our tool every turn

**Role:** the core agent with the Agent ID. It owns the whole live loop (VAD, Saaras v4 ASR, routed LLM, Bulbul TTS), runs a single-state, variable-keyed playbook, and calls `read_seller_signal` before every reply. **Inputs:** start-of-call variables, language and opening from B3; per-turn tool responses mapped into `@seller_mode` and `@persona_directive`. **Outputs:** speech; SDK transcript, audio and event callbacks; the on_end hook; post-call webhooks; and the Analytics API (`interaction_id`, `average_agent_response_time_in_seconds`, `audio_url`, `ended_by`, `agent_variables`) ([Sarvam interactions API](https://docs.sarvam.ai/conversations/api/analytics/interactions)). It has five attachment points and no others: call start, the per-turn API tool, call end, post-call analytics, and offline Tests and versions ([runtime block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/runtime_block.md)).

| Capability | Status | Evidence |
|---|---|---|
| Tool fired on every seller turn, 24/24 across SDK calls, at temperature 0 with a mandatory rule | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Tool often fires twice per turn (partial utterance on an ASR pause, then the full one) | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Directives change replies (rushed → 11–13 words + callback; confused → one idea + check; bot-question → disclosure) | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Prompt-only behaviour is inconsistent (one neutral run gave a callback, another a 30-word pitch) | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Tool args arrive verbatim in Devanagari with ASR errors; NFD needed for nukta | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Voice fixed per call; per-language voice assigned at call start | PROVEN (UI) + DOCUMENTED | [spike log](../../raw/research/2026-10-07-spike-log.md); [Sarvam voice & language](https://docs.sarvam.ai/conversations/build/voice-language) |
| No BYO LLM; temperature is the only LLM knob | DOCUMENTED | [Sarvam models](https://docs.sarvam.ai/conversations/build/models) |
| No async/background API tool; docs advise a "let me pull that up" line to cover latency | DOCUMENTED | [Sarvam API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool) |
| Code Tools (deterministic `set_agent_variable`, `change_language`) exist "on request"; absent in our UI | DOCUMENTED + PROVEN absent | [Sarvam code tools](https://docs.sarvam.ai/conversations/build/tools/code-tools); [spike log](../../raw/research/2026-10-07-spike-log.md) |
| `@Interaction ID` / `@Call Transcript` insertable in tool body | DOCUMENTED, but **not seen in our picker** (conflict) | [Sarvam API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool); [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Tool-written variable renders into instructions on the next turn (not only via the response line) | ASSUMED | — |
| Skip rate stays low over long calls and at demo concurrency | ASSUMED | — |
| No Tamil conversational/sales Bulbul v4 voice (only Aravind, Gokul, Vijay) | PROVEN | [voice catalogue](../../raw/research/2026-10-07-sarvam-voice-catalogue.json) |

### B5 Signal and Decision Server senses, decides and instructs in under 300 ms

**Role:** sense, decide and return an instruction. It never writes the spoken reply. It always returns HTTP 200 within a ~300 ms deadline, well under Sarvam's 2 s Max wait, so the platform's "If it fails" path never fires. **External interface:** `POST /read_seller_signal`, header `x-signal-token` (to move into Sarvam Auth secrets), body `{call_key, seller_utterance, language}`, response `{seller_mode, persona_directive, turn_no, source: lexicon|jev|cache, rev}`. **Internal interfaces:**
- `dedup`: same turn if <6 s apart and one normalised utterance prefixes the other, or token Jaccard ≥0.7.
- `lexicon.classify(text_nfd, lang)`: under 5 ms.
- `policy.step(call_state, lexicon_hits, jev_latest) → (mode, directive_id, switch_event)`: a pure function.
- `directives[mode][language]`: a pre-written, reviewed table, with no LLM at runtime.
- Job queue to B6.
- `GET /log` for the dashboard.

**Policy:** opt-out and bot-question are events that fire once and do not consume the switch budget. Style modes (rushed, frustrated, confused, interested) enter instantly on a lexicon hit, or on Jev p ≥ θ_enter. They exit only after two turns below θ_exit. Each call allows at most two style switches with a two-reply dwell, rushed stays sticky, and any failure means "keep current" ([decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md)).

| Capability | Status | Evidence |
|---|---|---|
| Sarvam reaches our endpoint (from 4.213.167.70) through cloudflared; 200 in 0.11 s; 401 without token | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Keyword-stub modes steer replies | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Instant path needed: after the first rush cue, a median of only 2 seller turns remain; 17% of first rush cues fall on the seller's last turn | PROVEN (crude regex proxy, 12,015 calls) | [decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md) |
| Dual-threshold, one-in-flight, never-stall policy pattern | DOCUMENTED | [jev-voice-turn README](https://raw.githubusercontent.com/dabit3/jev-experiments/main/jev-voice-turn/README.md) |
| Lexicon precision/recall per script | ASSUMED (unmeasured) | — |
| Thresholds, dwell, budget values | ASSUMED (engineering priors) | [TypeSafe confidence](https://docs.typesafe.ai/confidence.md) |
| Partial/full calls are prefix-related, so dedup works | ASSUMED | — |

### B6 Jev Worker corrects the next decision and never blocks the turn

**Role:** produce calibrated probabilities that confirm or cancel lexicon hits and drive implicit entries and all exits. Its result applies to the next tool call for that call. **Input:** a job `{call_key, turn_no, state}`, where state holds the last 3–4 turns, the latest seller turn, the current mode and the language, with seller text only in `state`. **Output:** Noul probabilities for rushed, frustrated, confused, bot_question, interested and opt_out, plus a language Choice with an escape option. It keeps one request in flight per call, uses a hard ~1.5 s timeout, and drops stale results by `turn_no`. **Route:** `POST openrouter.ai/api/alpha/decisions` with `typesafe/jev-1.13` pinned, or the LiteLLM `/typesafe` pass-through ([LiteLLM TypeSafe](https://docs.litellm.ai/docs/pass_through/typesafe)).

| Capability | Status | Evidence |
|---|---|---|
| 49/51 agreement on 30 romanized turns (rushed 10/10, frustrated 10/10, confused 9/9, bot_question 5/5, interested 5/6) at ~$0.00004/decision | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Latency from office VPN: p50 491 ms keep-alive, 760 ms new connection; 4 concurrent p50 1,033 / p95 1,406 ms; ~150 ms is OpenRouter overhead | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| OpenRouter key is IP-allowlisted: laptop works only over VPN with IPv4 forced; Daytona 35.234.211.110 gets 403 | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| IndiaMART LiteLLM gateway: `typesafe/jev-1.13` 8 requests, all failures | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| English is Jev's strongest language; accuracy falls with unrelated state; no fine-tuning | DOCUMENTED | [TypeSafe models](https://docs.typesafe.ai/models.md); [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) |
| Accuracy on Devanagari, Tamil and Gujarati script input | ASSUMED (live ASR gives Devanagari; history is 99.4% Latin) | [decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md) |
| Partial-utterance call launches Jev early enough to steer the same turn's full-utterance call | ASSUMED (gap unmeasured) | — |

### B7 Simulated Seller Harness plays a scripted seller voice-to-voice

**Role:** play one `SellerCard` against one `Arm`, voice to voice, with trigger events scripted at fixed turns so that switch timing needs no judge. **Input:** `SellerCard{card_id, lang, code_mix, verbosity, events[{turn, type, line}], hangup_rule, seed, evidence_refs→cluster IDs}` and an `Arm`. **Output:** a raw `Trace`, audio, and the `interaction_id`. Seller lines are rendered with Bulbul in a voice that differs from the agent's, and cached per (card, seed, line) so both arms reuse identical audio.

| Capability | Status | Evidence |
|---|---|---|
| Drives the agent in SDK CALL mode with Bulbul 16 kHz seller audio; RMS > 700 detects agent speech; measures reply latency | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Must keep talking, or the agent's nudge/hang-up ends the session | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| LLM simulators drift to verbosity and "unreasonable patience", so trigger lines are scripted and an LLM fills only the in-between lines | DOCUMENTED | [ConvApparel](https://arxiv.org/html/2602.16938v1) |
| Cost ₹3.50/min for Voice Agents; ₹100 free credit | DOCUMENTED | [Sarvam Epoch](https://www.sarvam.ai/epoch/summary); [Sarvam pricing](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing) |
| SDK simulation billed like phone minutes; SDK session concurrency limit | ASSUMED (undocumented) | — |
| Sarvam's own Tests (simulated user + black-box AI judge, ≤20 runs/case) as a regression complement | DOCUMENTED; whether it calls our real tool is ASSUMED | [Sarvam Tests API](https://docs.sarvam.ai/conversations/api/tests/overview.md) |

### B8 Trace Store holds one append-only record per call

**Role:** the single data contract for every call source. **Inputs:**
- harness traces from B7;
- B5 decision rows, which form the deck's required "switch log: signal detected, change made, reason";
- SDK callbacks;
- post-call webhooks (`interaction_transcript`, `final_agent_variables`) and the Analytics API;
- historical calls with existing evaluator outputs, local and aggregate-only.

**Output:** `Trace{call_id, source sim|phone|web|hist, card_id, seed, arm, app_version, turns[{role,text,lang,t_start,t_end}], tool_calls[{t,args,seller_mode,directive,source}], scripted_events[], audio_path, sarvam_interaction_id}`, stored as JSONL with DuckDB or SQLite views ([eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md)).

| Capability | Status | Evidence |
|---|---|---|
| Interactions API fields (incl. `audio_url`, `average_agent_response_time_in_seconds`, `has_log_issues`, `agent_variables`) | DOCUMENTED | [Sarvam interactions](https://docs.sarvam.ai/conversations/api/analytics/interactions) |
| Transcripts and recordings endpoints exist, schema shown as `{}` | DOCUMENTED (schema unknown) | [Sarvam transcripts](https://docs.sarvam.ai/conversations/api/analytics/transcripts) |
| Inbound webhook carries transcript `{role, en_text, indic_text?}` and final variables | DOCUMENTED | [Deployments webhook](https://docs.sarvam.ai/conversations/api/deployments/webhooks/webhook-payload) |
| Analytics API returns SDK-session calls (`is_debug_call` hints yes) | ASSUMED | — |
| Store itself | ASSUMED (unbuilt) | — |

### B9 Metrics and Judges grade every call arm-blind

**Role:** convert traces into verdicts. Deterministic metrics come first:
- switch latency in turns and seconds after the scripted trigger;
- false-switch rate on cards with no trigger;
- reply words per mode;
- callback offered (Devanagari and Latin regex);
- reply latency;
- tool-skip rate.

Jev handles typed binary judgements: callback offered, truthful disclosure, opt-out honoured, frustrated at end. One OpenRouter LLM, from a different model family than the seller simulator, gives ordinal persona-fit and naturalness scores with the arm label stripped. Jev never grades the ON arm's switch correctness, because it helped make those decisions. **Output:** `Verdict{call_id, criterion, value, severity, rationale, judge_model}`.

| Capability | Status | Evidence |
|---|---|---|
| Reply latency and tool-call counting from traces | PROVEN | [spike log](../../raw/research/2026-10-07-spike-log.md) |
| Jev-style typed judges match LLM judges on binary criteria, are worse on ordinal ones, and are 16–325× cheaper; ~96% of LLM judgments share Jev's confident errors | DOCUMENTED | [arXiv 2609.29769](https://arxiv.org/abs/2609.29769) |
| LLM judges >80% human agreement but biased (position, verbosity, self-preference) | DOCUMENTED | [Zheng et al.](https://arxiv.org/abs/2306.05685) |
| Judge κ ≥ ~0.6 on 20 human-labelled calls per ordinal criterion | ASSUMED | — |

### B10 Aggregator and Dashboard turn verdicts into decisions

**Role:** turn verdicts into one of three decisions and show them to the jury. For #4 it reports paired ON−OFF differences per card, with a bootstrap CI that resamples cards and a sign test. For #1 it builds the Fatal/Non-Fatal queue, root-cause clusters and the fix-test trail. For #5 it gives a Beta-Binomial or mSPRT promote/stop decision with a Fatal-rate guardrail. **Display:** a Streamlit app with a live switch timeline (polling `/log` every 1–2 s), the ON/OFF chart, persona cards with evidence, robustness counters, and Audit and A/B tabs.

| Capability | Status | Evidence |
|---|---|---|
| Quick tunnels do not support SSE and cap at 200 in-flight requests, so the dashboard polls | DOCUMENTED | [Cloudflare quick tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) |
| Sarvam Agent Analytics gives health metrics, not grading, leaving room for our audit layer | DOCUMENTED | [Sarvam Agent Analytics](https://docs.sarvam.ai/conversations/monitor/agent-analytics/overview.md) |
| Always-valid mSPRT p-values allow continuous monitoring and early stopping | DOCUMENTED | [Johari et al.](https://arxiv.org/abs/1512.04922v2) |
| Dashboard and aggregator | ASSUMED (unbuilt) | — |

## A seller turn costs about 2.1 seconds, and the hybrid adds almost nothing

### Per-turn flow

The seller stops speaking. Sarvam's VAD closes the turn, Saaras v4 produces Devanagari text, and the routed LLM's first pass calls `read_seller_signal`. Sarvam POSTs from 4.213.167.70 through the Cloudflare edge and the cloudflared tunnel to B5 on Daytona. B5 de-duplicates against the previous call, runs the lexicon, and calls `policy.step` with the latest Jev result already cached for this call. It returns `{seller_mode, persona_directive}` within its deadline and appends a trace row. In parallel, B5 enqueues a Jev job. The B6 worker picks it up and posts probabilities back keyed by `(call_key, turn_no)`. Sarvam saves the returned fields into variables and renders the response line, and the LLM's second pass writes the reply, which Bulbul speaks. When ASR splits the turn, the full-utterance tool call often arrives after Jev has answered the partial one, so the "next-turn" correction lands within the same seller turn. That gap still needs measuring ([decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md)).

| Segment | Value | Status |
|---|---|---|
| Seller stop → agent audio, end to end, stub tool in loop | median ~2.1 s, range 1.2–3.5 s | PROVEN ([spike log](../../raw/research/2026-10-07-spike-log.md)) |
| Tool round trip Sarvam → tunnel → Daytona → back | ~0.11 s | PROVEN ([spike log](../../raw/research/2026-10-07-spike-log.md)) |
| B5 compute (dedup + lexicon + policy + lookup) | <5 ms target; hard deadline 300 ms | ASSUMED |
| Sarvam-internal VAD + ASR + 2 LLM passes + TTS first byte | ~2.0 s by subtraction | ASSUMED (no no-tool baseline exists) |
| B6 Jev, off the critical path | p50 0.49 s; sequential p95 0.95 s; 4-concurrent p95 1.41 s | PROVEN ([spike log](../../raw/research/2026-10-07-spike-log.md)) |
| **Hybrid total** | **≈ stub: ~2.1 s p50, ≤3.5 s tail** | ASSUMED, to be verified |
| Rejected sync-Jev total | ~2.6 s p50; 3.5–4.9 s tail | Derived from PROVEN parts |
| Red line that triggers flip F1 | replies routinely >3 s, or added p95 >0.8 s | ASSUMED threshold |

Sarvam advertises "sub-second latencies, even at scale" in its docs and "<500ms" on its product page, without defining either measurement ([Sarvam run-time](https://docs.sarvam.ai/conversations/build/run-time); [Sarvam Voice Agents](https://www.sarvam.ai/products/voice-agents)). Our 2.1 s is not comparable, because it includes the VAD wait, a tool round trip and a second LLM pass. The comparison that matters is with and without our tool. A third-party test of a blocking Jev turn gate shows what to avoid: median reply latency rose from **2.1 s to 4.6 s** while task success barely moved ([Veris](https://veris.ai/blog/jev-turn-detection)). The documented knobs are the eagerness setting and keeping tools fast ([Sarvam conversation settings](https://docs.sarvam.ai/conversations/build/conversation-settings)).

### Per-call flow

B1 builds the context and B2 emits the persona. A DNC hit stops here. B3 assigns the arm and opens an SDK session or places a phone call, writing `call_key` into `agent_variables`. B4 speaks the opening in the start language, using the voice fixed by version or session. Per-turn loops then run for about **5 seller turns** (the median in the historical data; median call 52 s) ([decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md)). At the end, B4 fires on_end and the post-call webhook, and B7 closes the trace. B8 joins the B5 rows, the SDK transcript and the Analytics record by `interaction_id`. B9 then grades within seconds (Jev ~0.5 s per decision) to minutes (LLM judges, batched), and B10 updates the paired statistics. The minimal credible experiment is **10 cards × 2 seeds × 2 arms = 40 calls, about 60 call-minutes, about ₹210 at ₹3.5/min**. If all 10 card-level paired differences favour ON, a sign test gives p≈0.002. Run sequentially, the experiment takes about an hour, or 15–20 minutes at 3–4 concurrent sessions ([eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md)). The OFF arm still calls the tool and runs Jev but receives a neutral directive, so latency cannot confound the lift.

## Daytona hosts the server, a VPN laptop reaches Jev, a tunnel lets Sarvam in

Three network facts constrain the layout. Sarvam's tool calls originate from **4.213.167.70** and need public HTTPS. Self-hosted Daytona sandboxes have working egress to Sarvam and OpenRouter, but preview URLs lack wildcard DNS and TLS, so inbound traffic currently goes through a cloudflared quick tunnel whose URL changes on restart. The OpenRouter key is IP-allowlisted: only the office VPN egress (**121.241.109.212**, IPv4 forced, because the VPN tunnels IPv4 only and openrouter.ai resolves IPv6 first) is accepted, and the Daytona IP **35.234.211.110** gets a 403 ([spike log](../../raw/research/2026-10-07-spike-log.md)). The internal LiteLLM gateway is reachable only over VPN and has failed on all eight recorded Jev requests ([spike log](../../raw/research/2026-10-07-spike-log.md)).

```
 Sarvam cloud (Voice Agent B4) ──egress 4.213.167.70── HTTPS ──► Cloudflare edge
                                                                     │ quick tunnel (URL changes on restart)
                                                                     ▼
 ┌──────────── Daytona sandbox (self-hosted, 35.234.211.110) ────────────────────────┐
 │ B5 signal server ◄── /jobs (worker pulls) ──┐   B8 store, B10 dashboard (polling) │
 │ B7 harness (SDK CALL to apps.sarvam.ai ✓)   │   egress to Sarvam ✓, OpenRouter 403│
 └──────────────────────────────────────────────┼────────────────────────────────────┘
                                                │ outbound HTTPS from laptop via tunnel URL
 ┌──────────── Office laptop on VPN (IPv4 forced, egress 121.241.109.212) ────────────┐
 │ B6 Jev worker → openrouter.ai Decisions API ✓                                      │
 │ B9 batch judges (OpenRouter LLM + Jev); seller-line LLM generation for B7 cards    │
 │ optional: LiteLLM gateway /typesafe (VPN-only; currently 8/8 failures)             │
 └────────────────────────────────────────────────────────────────────────────────────┘
```

| Option | Jev reachable from in-call path | Public URL | Failure mode | Verdict |
|---|---|---|---|---|
| **D. Split: Daytona B5 + laptop B6 worker pulling jobs** | Yes, via laptop | Quick tunnel | Worker loss → lexicon-only, degrades gracefully | **Recommended**: fits the hybrid, needs no allowlist change |
| B. Daytona + OpenRouter allowlists 35.234.211.110 | Yes, directly | Quick tunnel | Needs key owner | Ask in parallel; simplest if it lands |
| C. Daytona + LiteLLM `/typesafe` | Only if gateway reachable from Daytona and fixed | Quick tunnel | Gateway down today | Could cut ~150 ms of OpenRouter overhead; revisit sync-with-deadline if p95 <250 ms |
| A. Everything on VPN laptop + cloudflared | Yes | Quick tunnel | Laptop/VPN/venue Wi-Fi is a single point of failure | Day-0 fallback and demo backup |

Two stable-URL fixes cost no new vendor, and both are worth requesting today. The first is a Daytona admin adding `*.proxy-daytona.intermesh.net` DNS plus a wildcard certificate. The second is an internal reverse proxy with a fixed hostname. A named Cloudflare tunnel would give a stable hostname and SSE, but it needs a Cloudflare account and zone, so the team must decide whether that counts as a "new outside vendor". The cloudflared binary itself is Apache-2.0 ([eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md)). Until then, keep the tunnel up for the whole event, and re-paste the URL into the Sarvam tool after any restart.

The demo has three channel tiers. The most reliable is an autonomous harness run recorded with the dashboard, which needs no telephony and is PROVEN. Next is a browser or laptop-mic call through the SDK, where the presenter says "jaldi bolo"; this is DOCUMENTED but untested. Last is a real phone call. An **inbound** rented number that the presenter dials avoids the NDNC failures and the A2P-declaration question that outbound AI calls now raise under TRAI's 18 Sep 2026 amendment ([Rent from Sarvam](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam); [TelecomLead](https://telecomlead.com/telecom-services/trai-tightens-spam-call-rules-with-ai-ml-detection-%E2%82%B90-05-a2p-charge-and-faster-enforcement-127804)). The TRAI summary is secondary, and the primary PDF was not read.

## Twelve alternatives lost on latency, determinism or the rules

| Alternative | Verdict | Reason |
|---|---|---|
| Jev synchronous in the tool call | Rejected as default | +0.48 s p50 and 3.5–4.9 s tails; consumes most of the 2 s Max wait ([spike log](../../raw/research/2026-10-07-spike-log.md)). Revisit only if a direct route shows p95 <250 ms |
| Jev async only (no instant path) | Rejected | Lags the turn that matters most: 17% of first rush cues fall on the seller's last turn ([decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md)) |
| Lexicon only | Kept as fallback | Zero risk, but misses implicit frustration and gives no probabilities to show judges |
| Small OpenRouter LLM or Sarvam LLM as the live classifier | Rejected in-loop; used offline | Same OpenRouter hop plus generation, uncalibrated; Sarvam 30B/105B reasoning-mode first-answer times are 14–22 s ([Artificial Analysis](https://artificialanalysis.ai/providers/sarvam)) |
| Fine-tuned local CPU encoder (MuRIL/IndicBERT INT8) | Deferred stretch goal | Plausibly ~20–50 ms ([INT8 DistilBERT card](https://huggingface.co/Trakerlack/distilbert-toxic-onnx-int8)), but needs labelled Devanagari data and half a day |
| Persona as separate Sarvam states | Rejected | Legacy, end-of-life announced, LLM-judged transitions, one-way conversion ([Sarvam multi-state](https://docs.sarvam.ai/conversations/build/states-conversation-flow)) |
| Workflows | Unavailable | Enterprise plans only ([spike log](../../raw/research/2026-10-07-spike-log.md)) |
| Code Tool instead of API tool | **Preferred if granted** | Deterministic variable/language writes without relying on the LLM to call; "available on request" ([Sarvam code tools](https://docs.sarvam.ai/conversations/build/tools/code-tools)). API tool stays the baseline |
| Own pipeline (Pipecat/LiveKit with Sarvam STT/TTS) for live pace change | Rejected | Core must be a Sarvam Voice Agent with an Agent ID; LiveKit-style pre-reply hooks ([LiveKit hooks](https://docs.livekit.io/agents/build/nodes/)) have no Sarvam equivalent |
| OpenRouter LLM writing each directive live | Rejected | Adds an LLM call of 500–1,500 ms per turn ([livekit/agents #7355](https://github.com/livekit/agents/issues/7355)); use the pre-written directive table |
| Leading the pitch with a personalised opening | Rejected | 0 for 3 in IndiaMART trials ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)) |
| Sarvam Tests as the main experiment | Complement only | Black-box judge, no access to our switch log or scripted-trigger timing ([Sarvam Tests](https://docs.sarvam.ai/conversations/build/tests/run-tests.md)) |

## Open risks: what can still break the design

The largest risk is **tool compliance and latency at demo length**. The 24/24 tool rate comes from short calls at temperature 0. The rate at ten or more turns, under concurrency, or with the playbook prompt at full size is unmeasured, and there is no no-tool baseline. If the routed LLM skips the tool, B5 still holds the last mode, but that turn's reply goes unsteered. The second risk is **signal accuracy on the script the system actually receives**. Live ASR delivers Devanagari with errors, while the historical corpus is 99.4% Latin script. Jev's smoke test used romanized text only, and TypeSafe documents weaker non-English accuracy ([decision block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/decision_block.md); [TypeSafe models](https://docs.typesafe.ai/models.md)). Tamil and Gujarati script cannot be evaluated from local data at all. The third risk is **network fragility**. The in-call path depends on a quick tunnel with "no uptime guarantee", and the Jev path depends on one VPN laptop ([Cloudflare quick tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)).

The remaining risks are smaller but real. **Budget**: 40 calls cost about ₹210 at ₹3.5/min against a ₹100 free credit, so hackathon credits must cover the experiment. Whether SDK simulation is billed like phone minutes is undocumented. **External validity**: Bulbul-rendered seller audio at 16 kHz likely flatters ASR compared with 8 kHz phone lines, and any lift is lift on a simulated population ([eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md)). **Telephony**: KYC turnaround, number price and responsibility for the A2P declaration are all undocumented. **Tamil voice**: no Tamil conversational v4 voice exists, so the TN demo starts in English or uses a narrator voice. **Correlational grounding**: every archetype statistic is observational, and Tamil Nadu figures are confounded because 97% of TN calls ran on one bot version ([persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md)). Finally, **rubric perception**: if many teams pick Persona, the paired ON/OFF evidence and the switch log are what separate this entry from prompt-only adaptations.

## Sixteen verification tests, ordered by what they can overturn

P0 tests decide the problem choice, and they map to flip conditions F1–F3. P1 tests shape block internals. P2 tests are needed for the demo and for reuse.

| Pri | Test | Block | Pass criterion | If it fails |
|---|---|---|---|---|
| P0 | T1 No-tool vs tool latency: same harness, 20 turns each; read Sarvam Tools-tab p50/p95 and `average_agent_response_time_in_seconds`; try Eager vs Normal | B4, B5 | Tool adds p95 ≤ ~0.8 s; replies rarely >3 s | Checkpoint mode (tool only at pitch checkpoints) → if still bad, flip F1 to #1 |
| P0 | T2 Tool skip rate on 10 calls of ≥10 turns, full playbook prompt, 3 concurrent | B4 | Skip <10% | Persisted mode + checkpoint mode; if >10%, flip F1 |
| P0 | T3 Credits and billing: 6-call pilot (3 hero cards × ON/OFF); wallet delta per minute; real call length; max concurrent SDK sessions | B7, B3 | 40+ calls affordable; ≥3 concurrent | Shrink to 3 hero cards; if unfunded, flip F3 |
| P0 | T4 Jev route for the in-call server: allowlist request for 35.234.211.110; LiteLLM `/typesafe` from Daytona; else laptop worker; measure p50/p95 from the chosen host | B6 | Any route works; p95 ≤ ~1 s background | Lexicon-only (demo still works; robustness claim weakens) |
| P1 | T5 Partial→full tool-call interval and prefix relation within one turn (Log Analyser + B5 log) | B5, B6 | Gap ≥ ~0.5 s on most split turns; prefix holds | Jev lands next turn only; dedup by time window alone |
| P1 | T6 `@Interaction ID` / `@Call Transcript` in the tool picker; transcript script/format | B4, B5 | Interaction ID available | Inject `call_key` via SDK/Outbound `agent_variables` |
| P1 | T7 Variable rendering: tool returns mode via Save-to-variable only; check next reply and LLM-input card; check whether duplicate calls both enter context | B4 | Variable steers the next reply | Keep directive in the response line (PROVEN path) |
| P1 | T8 Signal accuracy: ~600 sampled turns, transliterated to Devanagari; 200 hand-labelled; lexicon vs Jev per signal per script; ~30 synthetic Tamil/Gujarati-script turns | B5, B6 | Rushed/bot-question lexicon precision ≥0.85; Jev agreement holds on Devanagari | Put Devanagari cues in Jev criteria; send a romanized copy in state; narrow to rush + language |
| P1 | T9 SDK `text_to_speech_config` with v4 speakers takes effect; ear-test candidate voices on 8 kHz incl. Tamil | B3, B4 | Per-session voice/pace audible | One committed version per voice style for SDK too |
| P1 | T10 Sarvam-105B (reasoning off, JSON schema) opening wording in Hindi/Gujarati/Tamil, plus latency | B2 | Native-sounding within templates | Hand-written templates (SquadStack-style) |
| P2 | T11 Phone path: start KYC; rent inbound number; Instant Outbound with a committed-not-deployed `app_version`; NDNC check; ask who files the TRAI A2P declaration | B3, B4 | One consenting call connects with variables honoured | Browser/SDK demo only |
| P2 | T12 Analytics interactions/transcripts/recordings on a spike `interaction_id`; are SDK calls included? | B8 | Schema known; SDK calls present | Rely on B5 log + SDK callbacks |
| P2 | T13 Judge calibration: 20 human-labelled calls per ordinal criterion | B9 | κ ≥ ~0.6 | Report only deterministic metrics and binary Jev items |
| P2 | T14 Request Code Tools for the hackathon org | B4 | Enabled | Stay on API tool |
| P2 | T15 Stable inbound URL: Daytona wildcard DNS/cert or internal reverse proxy; Daytona proxy passes SSE/WebSocket; decide on Cloudflare named tunnel | Infra, B10 | Stable hostname | Quick tunnel + polling, re-register URL on restart |
| P2 | T16 Sarvam Tests single-case run: does it hit our tool (watch for 4.213.167.70)? Voice or text? | B7 | Real tool called | Keep Tests out of the experiment |

## The same blocks become Quality Audit and A/B testing

For **Quality Audit (#1)**, B4–B6 drop out of the critical path, and the evaluation plane does the work.

- **B8:** gains two adapters, one for historical calls with existing evaluator outputs (local, aggregates only) and one for Sarvam webhooks and the Analytics API ([Deployments webhook](https://docs.sarvam.ai/conversations/api/deployments/webhooks/webhook-payload)).
- **B9:** adds a Fatal/Non-Fatal severity map. Fatal covers wrong commitments, a missed opt-out, a false human claim and abusive tone. Non-Fatal covers a missed objection, a slow switch, an over-long reply and no callback for a rushed seller. B9 also flags the deck's five risk types (wrong requirement, frustration, loops, low confidence, human request), and measures agreement against the existing evaluator labels or a small human set.
- **B10:** clusters judge rationales into root causes ranked by frequency × severity.
- **B2 and B7:** an LLM proposes one prompt diff per cluster. Failing patterns become synthetic seller cards (built from aggregate patterns, not text), and B7 runs fix-ON vs fix-OFF. That yields the deck's "drop in failure rate after a tested fix" and "time from issue to fix tested" ([hackathon deck](../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md); [eval/demo/ops notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/eval_demo_ops.md)).

The real-data pool is already measured: 55.1% `call_dropped`, 14.8% of sellers still talking after the bot closed, and 26% loopy or repeat calls ([problem selection notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/problem_selection.md)).

For **A/B Testing (#5)**, the persona experiment generalises directly.

- **Variants:** published `app_version`s. These are needed anyway for per-call voice on the phone.
- **B3:** its hashed split assigns arms, and split accuracy is a chi-square test of observed against configured share.
- **Auto-disposition:** a B9 judge emitting Meeting Fixed or Callback Fixed. It is validated against labelled calls, where the existing evaluator already shows 94.3% precision and 89.1% recall.
- **B10 decision rule:** Beta(1,1) posteriors with promotion at P(B>A) > 0.95 and expected loss < ε. A Fatal-rate guardrail or one-sided mSPRT triggers early stop ([Johari et al.](https://arxiv.org/abs/1512.04922v2)).
- **"Right winner on a known-difference test":** a deliberately worse variant, for example one that ignores the rush directive, which the engine should stop early. The same run doubles as the Persona ON/OFF evidence.

Across both reuses, B1, B5 and B6 are the only Persona-specific blocks. Everything else carries over with an adapter or an aggregator swap.

## Conclusion

The measurements change where the risk sits. Jev turned out to cost ~0.5 s through OpenRouter from India, not the ~0.1 s quoted elsewhere. As a result the classifier moved off the critical path, and a deterministic lexicon became the part of the system that decides the most important reply: the one right after a seller says "busy, be quick". The open questions are now about Sarvam's turn loop: whether the routed LLM keeps calling the tool over longer calls, and what the tool step itself costs. Those two P0 tests (T1, T2) decide not only latency but the problem choice, because they are exactly flip condition F1.

The design is also built so the pivot stays cheap. The pieces judges can verify are owned code: the pure policy function, the scripted-trigger switch latency and the arm-blind trace contract. Those are the "core logic must be ours" story and the robustness evidence, and they make the Persona build a working prototype of the #5 engine and the #1 audit stack. If day 1 goes badly, the team changes the aggregator, not the architecture.
