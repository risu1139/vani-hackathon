# Real-time signal & decision block (the `read_seller_signal` tool server)

As of 2026-10-08. Tags: **PROVEN** = measured by us in a spike or computed here from local data; **DOCUMENTED** = stated in vendor or third-party docs; **ASSUMED** = our inference or an untested design value. Local data is cited only as aggregates. No seller text, names or recordings are copied here.

Local sources used: [spike log](../../../raw/research/2026-10-07-spike-log.md), [persona-architecture wiki](../../../wiki/projects/vani-hackathon/persona-architecture.md), [jev_signal_design.md](../VANI%20adaptive%20persona%20architecture/jev_signal_design.md), [peer_platform_patterns.md](../VANI%20adaptive%20persona%20architecture/peer_platform_patterns.md), [sarvam_platform_internals.md](../VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md), and aggregates computed on 2026-10-08 from `data/.../ps07_call_turns.csv` (local, git-ignored; cited below as "ps07 aggregate").

## Q0. Which design, with what role and interfaces? (recommendation)

### Takeaway
Use a **hybrid**. A deterministic lexicon (Devanagari, romanized, and Tamil/Gujarati script cues, NFD-normalised) decides the **current** turn in under 5 ms. Jev runs **in the background, off the critical path**, and corrects or confirms the state used on the **next** tool call. Often that is the second, full-utterance call within the same turn. A code-only policy layer owns every switch.
- Do not make sync Jev the default. It adds ~0.5 s p50 and up to ~1.4 s under concurrency to a ~2.1 s reply.
- Do not rely on async alone. The reply to the turn where the seller first says they are busy is the reply that matters most.
- Small LLMs and Sarvam's own LLM are no faster than Jev and are not calibrated, so use them offline only (teacher labels, directive writing).
- A local CPU classifier is a stretch goal and could replace the lexicon only if time allows.

### Cited Findings
- PROVEN: A keyword stub caught rushed, confused and bot_question on live SDK calls, and the directives changed agent replies. For example, rushed produced an 11–13-word reply with a callback offer. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: Jev agreed with 49/51 labels on 30 hand-written romanized turns:
  - rushed 10/10, frustrated 10/10, confused 9/9, bot_question 5/5, interested 5/6.
  - Cost was ~$0.00004 per decision.

  — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: Jev latency via OpenRouter from the office over VPN:
  - p50 491 ms on keep-alive, 760 ms with a new connection per call.
  - Sequential with new connections: p95 953 ms. 4 concurrent: p50 1,033 ms, p95 1,406 ms.
  - OpenRouter-reported provider latency is 315 ms. Question count barely matters (6 questions p50 482 ms).

  — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: Sarvam reply latency after the seller stops was median ~2.1 s (range 1.2–3.5 s) with the stub. The stub endpoint answered in 0.11 s via cloudflared. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: Jev "does not produce reasoning traces, explanations, or free-form text". It runs on the Decisions API, not chat completions. — [OpenRouter Jev guide](https://openrouter.ai/docs/guides/community/jev) (via [jev_signal_design.md](../VANI%20adaptive%20persona%20architecture/jev_signal_design.md))
- DOCUMENTED: Sarvam's chat API lists `sarvam-105b` and `sarvam-105b-conversations` ("post-trained for real-time dialogue and voice-agent workloads"), plus V2 beta models.
  - Thinking is "on by default (`low`)" and can be turned off with `reasoning_effort: null`.
  - JSON-schema structured output is supported.
  - The page makes no latency claims.

  — [Sarvam Chat Completions overview](https://docs.sarvam.ai/api/chat-completion/overview)
- DOCUMENTED (third party): Artificial Analysis reports a time to first answer token of 13.86 s for Sarvam 30B and 22.31 s for Sarvam 105B in "high" reasoning mode. It also reports that Sarvam-M is deprecated. — [Artificial Analysis: Sarvam](https://artificialanalysis.ai/providers/sarvam); [Sarvam 105B](https://artificialanalysis.ai/models/sarvam-105b/providers). These are reasoning-mode numbers, so non-reasoning latency is unmeasured.

### Inferences
- ASSUMED: The block has a fixed role: **sense → decide → speak-instruction**. It never writes the spoken reply (Sarvam does). It returns only a mode and a pre-written directive.
- ASSUMED: Proposed interfaces:
  - **Sarvam → server:** `POST /read_seller_signal`, header `x-signal-token` (move to Auth secrets).
    - Body: `{call_key, seller_utterance, language}`. `call_key` is the Interaction ID call-context variable; Q3 covers the fallback.
    - Response: `{seller_mode, persona_directive, turn_no, source: "lexicon"|"jev"|"cache", rev}`.
    - Sarvam maps it into `@seller_mode` and `@persona_directive`, as already wired. PROVEN wiring, ASSUMED new fields.
  - **Internal 1:** `lexicon.classify(text_nfd, lang) -> {signal: hit_strength}`. Synchronous, pure, <5 ms (ASSUMED).
  - **Internal 2:** `jev.decide(state) -> {signal: p}`. Async, one in-flight request per call, stale results dropped by `turn_no`.
  - **Internal 3:** `policy.step(call_state, lexicon_hits, jev_latest) -> (mode, directive_id, switch_event)`. Pure function, unit-testable, and replayable offline over transcripts.
  - **Internal 4:** a `directives[mode][language]` table, pre-written and reviewed. No LLM at runtime.
  - **Trace:** JSONL per call (`call_key`, `turn_no`, text hash, lexicon hits, Jev p's, latency, mode, switch flag). This feeds the ON/OFF evaluation and a demo "why did it switch" panel.
- ASSUMED: Ranking of the options for this hackathon:
  1. Hybrid.
  2. Lexicon only (zero risk, but misses implicit frustration and gives no probabilities to show judges).
  3. Jev async only (lags the key turn).
  4. Jev sync (latency).
  5. Local CPU model (best long-term latency, but needs training data and Devanagari alignment).
  6. Small LLM or Sarvam LLM in the loop (slowest and uncalibrated).
- ASSUMED: The hybrid gives a stronger story for judges. A rule-based instant reflex plus a calibrated model that "corrects within the turn" shows core logic that is ours (the policy and lexicon), with Jev as a component.

### Gaps
- No measurement yet of Sarvam reply latency with **no tool at all**, so the tool's own cost on the 2.1 s is unknown. The spike log notes that no no-tool baseline was measured.
- The latency of `sarvam-105b-conversations` with reasoning off, for a short JSON classification, was not found anywhere. Measure it if the Sarvam-only story matters.

## Q1. Latency budget: sync vs async, and is next-turn acceptable for rushed or frustrated sellers?

### Takeaway
Sync Jev makes a ~2.1 s median reply about **2.6 s p50 and ~3+ s at the tail**. Sarvam's tool call is serial (LLM → tool → LLM), so every millisecond counts. Async-only fails the turn that matters most: after the **first** rushed cue, a median of only **2 seller turns remain**, and in **17%** of such calls the cue is on the seller's **last** turn. The current turn must therefore be decided instantly (lexicon), with Jev feeding the next call.

### Cited Findings
- DOCUMENTED: The Sarvam API tool's Max wait is "configurable up to 30s". "If it fails" sets what the agent says on timeout or error. There is no documented async or fire-and-forget mode. The docs suggest the agent say "let me pull that up" to cover latency. — [Sarvam API tool docs](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- PROVEN: We set Max wait to 2 s on the spike agent. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: The tool is often called twice per turn: the ASR finalises on a pause and sends a partial utterance, then the full one. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN (ps07 aggregate; 12,015 calls, 64,625 seller turns):
  - Median **5 seller turns per call** (p10 1, p90 10; mean 5.38).
  - Median seller turn length 4 words (p90 20).
  - Median call length 52 s.
- PROVEN (ps07 aggregate, our crude romanized regex lexicon, ASSUMED to be a rough proxy only):

  | signal | calls with cue | first cue on seller turn 1 | median seller turns left after first cue | cue on last seller turn | ≥2 turns left |
  |---|---|---|---|---|---|
  | rushed | 31.6% | 0.8% | 2 | 17.2% | 62.4% |
  | frustrated | 1.7% | 6.4% | 1 | 29.1% | 46.3% |
  | confused | 4.8% | 38.0% | 3 | 11.4% | 72.0% |
  | bot question | 1.3% | 11.9% | 3 | 19.4% | 63.7% |
- DOCUMENTED (internal heuristic): rush is first seen mid-call 99% of the time and frustration 96%. — local wiki `persona-data-validation.md` via [jev_signal_design.md](../VANI%20adaptive%20persona%20architecture/jev_signal_design.md)
- DOCUMENTED (third party): Veris found that holding the turn for a Jev turn-detection classification raised median reply latency from 2.1 s to 4.6 s, while the task pass rate barely moved (50/300 vs 53/300). — [Veris](https://veris.ai/blog/jev-turn-detection) (via [jev_signal_design.md](../VANI%20adaptive%20persona%20architecture/jev_signal_design.md))
- DOCUMENTED: A typical voice budget is under 800 ms. A 300 ms tool call pushes time to first audio past 1,100 ms. The advice is to run tools in parallel with the LLM, not after it. — [Twig](https://www.twig.so/blog/voice-ai-agents-latency-budget-800ms) (via [peer_platform_patterns.md](../VANI%20adaptive%20persona%20architecture/peer_platform_patterns.md))

### Inferences
- ASSUMED **budget math** (p50 / tail):
  - Stub: ~2.1 s / 3.5 s.
  - Sync Jev on keep-alive: +0.48 s → ~2.6 s.
  - Tail: +0.95 s (sequential p95) to +1.4 s (4 concurrent calls, as during double-calls or several demo calls at once) → 3.5–4.9 s.
  - Sync Jev also consumes most of the 2 s Max wait and risks the spoken "If it fails" message.
  - The hybrid adds ~0 ms on top of the stub.
- ASSUMED **server deadline rule**: the server always answers within ~300 ms (well under the 2 s Max wait) from lexicon plus cache. It never lets Sarvam hit its timeout. Set "If it fails" to a silent or neutral fallback.
- ASSUMED **double calls help async**:
  - The partial-utterance call can launch Jev. If the full-utterance call arrives ≥ ~0.5 s later, Jev's answer is ready and can steer the **same** turn's reply.
  - This makes "async" effectively same-turn for some turns. The gap between the two calls must be measured; it has not been yet.
- ASSUMED: Rushed replies benefit most from immediacy. The seller says "busy, be quick" on turn k, and the reply to turn k must be short. Applying it on turn k+1 wastes one of the ~2 remaining turns. Hence explicit rushed and bot-question cues must be handled by the instant path.
- ASSUMED: Frustration is rarer and more implicit. Lexicon recall will be lower there, so Jev's background correction matters more. Because 29% of first frustration cues fall on the last seller turn, some losses are unavoidable on any design.

### Gaps
- The interval between the partial and full tool calls within one turn was not measured.
- No no-tool Sarvam latency baseline exists.
- The regex lexicon used for the table is ad hoc and unvalidated (no precision measured). The table shows **timing shape**, not true prevalence. The wiki's 21% rushed prior differs from our 31.6%.

## Q2. Accuracy on Devanagari, romanized, Tamil and Gujarati input; Jev caveats; quick evaluation

### Takeaway
The biggest accuracy risk is **script mismatch**, not the model:
- Live ASR delivers **Devanagari** (PROVEN).
- The historical turns are **99.4% Latin script** (PROVEN, ps07 aggregate).
- Jev's smoke test was romanized only.
- Jev is weaker outside English (DOCUMENTED).

Evaluate quickly by sampling ps07 turns, transliterating them to Devanagari, and comparing lexicon and Jev on both forms against a small hand-labelled gold set. Tamil and Gujarati script cannot be evaluated from this file at all.

### Cited Findings
- PROVEN: The tool receives seller words **in Devanagari**, verbatim, with `language: "hindi"`.
  - ASR errors were seen, for example a misheard "bot" phrase and a misheard "busy".
  - The nukta (ज़) requires NFD normalisation.

  — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN (ps07 aggregate) seller-turn script mix:
  - Latin 99.37%, Devanagari 0.18%, empty 0.44%, mixed 0.01%.
  - Tamil script 0%, Gujarati script 0%.
- PROVEN: Jev smoke test (romanized Hinglish/Hindi/Tamil/Gujarati/English):
  - Language Choice 10/11, with Hinglish read as Hindi.
  - "Ok ok" scored 0.69 for interested (the miss).

  — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: "English is the primary training language and where accuracy is currently best. Other languages … are handled but not equally well." — [TypeSafe Models](https://docs.typesafe.ai/models.md)
- DOCUMENTED: Jev reads negation and scope literally. "Accuracy falls as the state grows" with unrelated content. Choice option order can change answers. — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- DOCUMENTED (secondary): Accuracy reached 95.9% zero-shot but "collapsed to 16.7%" with incorrect criteria. With no escape option, 0/30 out-of-scope items were flagged. — [OrcaRouter](https://www.orcarouter.ai/blog/jev-typesafe-system-one-what-we-know)
- DOCUMENTED: Open-source code-mixed models exist. L3Cube HingBERT, HingMBERT and HingRoBERTa were pre-trained on 52.93M romanized Hindi-English sentences. — [l3cube hing-roberta](https://huggingface.co/l3cube-pune/hing-roberta). These are romanized-only, so they do not match Devanagari ASR output.

### Inferences
- ASSUMED **evaluation recipe (about 2–3 hours)**:
  1. Stratify-sample ~600 seller turns from ps07: ~300 random, plus ~300 enriched by lexicon or regex hits for rare signals. Keep the previous agent turn as context.
  2. Make a Devanagari copy of each turn. Use Sarvam's transliteration API (Sarvam infra) or the open-source `indic-transliteration` package, which mimics ASR output.
  3. Hand-label ~200 turns: 2 people, labels only, stored in `data/`.
  4. Run the lexicon and Jev on both scripts, at ~$0.00004 per turn (~$0.05 total).
  5. Report precision and recall per signal per script, and the Jev p distribution, to set thresholds.
  6. Report only aggregates in `raw/` or the wiki.
- ASSUMED: Put **Devanagari and romanized cue words inside Jev criteria**, and optionally pass a transliterated romanized copy in `state` alongside the Devanagari text. Test which wins on the step-5 set.
- ASSUMED **Tamil and Gujarati**: if Sarvam ASR switches language, the tool may receive Tamil or Gujarati script. The lexicon needs script-native cue lists (small, hand-written). Jev accuracy there is unknown; the smoke test used romanized only. Generate ~30 synthetic native-script turns with an OpenRouter LLM as a smoke test, and treat the result as indicative only.
- ASSUMED: ASR noise ("busy" misheard) argues for fuzzy or prefix lexicon matching and for using Jev on context, not single tokens.

### Gaps
- No published Jev accuracy on Devanagari, Tamil or Gujarati script, or on code-mixed text, was found.
- No real Tamil or Gujarati script seller turns exist locally.
- Lexicon precision on real data is unmeasured.

## Q3. Policy layer: state machine, hysteresis, dedup, priority, switch budget, fail-safe, per-call key

### Takeaway
Implement the policy as a pure function per call:
- **Lexicon hits act as high-confidence events** (immediate entry).
- **Jev probabilities drive implicit entry and all exits** through Schmitt thresholds plus 2-turn persistence.
- Fixed priority, at most 2 style switches per call (excluding events), and "keep current" on any failure.
- **Dedup partial and full calls** by treating a new utterance that extends the previous one (same `call_key`, within a few seconds) as the same turn.
- Key state on the **Interaction ID** call-context variable. If that is not available in our picker, use an agent variable we inject per session.

### Cited Findings
- DOCUMENTED: API tools can receive the call-context variables **User Identifier, Call Transcript, Interaction ID** ("The unique ID of the current call" for "idempotency and correlation") and **Call Length**. They are inserted in Body, Params or Headers via the `@` picker. — [Sarvam API tool docs](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- PROVEN, and **in conflict** with that doc: in our agent's body-field picker, the agent variables offered were user_name and current day/date/time, and "No call-transcript variable appeared." — [spike log](../../../raw/research/2026-10-07-spike-log.md). The Interaction ID may be in another picker section, or not enabled for our workspace. Verify.
- DOCUMENTED: User Identifier is populated on inbound calls only. — [sarvam_platform_internals.md](../VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md) citing the [Sarvam changelog 2026-08-20](https://docs.sarvam.ai/changelog/2026/8/20)
- PROVEN: The SDK `InteractionConfig` accepts `agent_variables`. Instant Outbound accepts `app_config.agent_variables`. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: The jev-voice-turn reference policy:
  - Dual thresholds (fire ≥0.85, extend below 0.35).
  - "If Jev fails, times out, or rate-limits, plain silence timeout applies — the app never stalls."
  - At most one request in flight; stale answers are discarded.

  — [jev-voice-turn README](https://raw.githubusercontent.com/dabit3/jev-experiments/main/jev-voice-turn/README.md)
- DOCUMENTED: Gate actions by stakes: "Different actions within the same system should be gated at different levels". — [TypeSafe Confidence](https://docs.typesafe.ai/confidence.md)
- DOCUMENTED (prior design): Priority opt-out > frustrated > bot-question > rushed > confused > interested. Rushed enters at 0.80 and exits at 0.40. 2-turn persistence. Max 2 switches per call. A timeout keeps the persona. *The thresholds are guesses.* — [persona-architecture wiki](../../../wiki/projects/vani-hackathon/persona-architecture.md)

### Inferences
- ASSUMED **call key**:
  - Preferred: `@Interaction ID` in the body as `call_key`.
  - Fallback: generate a UUID per call in our harness or outbound trigger and pass it as an agent variable (`call_key`) via SDK `agent_variables` or Instant Outbound `agent_variables`. Then map it as an "Agent variable" body value.
  - Last resort, for demo only: a single active call per tool URL (one tunnel URL or path token per demo session).
- ASSUMED **turn dedup**, run on each call:
  - `norm = NFD + strip punctuation + collapse spaces`.
  - If `now - last_ts < 6 s` and (`norm` starts with `last_norm`, or `last_norm` starts with `norm`, or token Jaccard ≥ 0.7), it is the **same turn**. Re-run the lexicon on the longer text, keep `turn_no`, and do **not** count it toward persistence or switch budgets.
  - Otherwise `turn_no += 1`.
  - Return the same `rev` if nothing changed.
- ASSUMED **state machine**, one style axis plus orthogonal events:
  - **Events**:
    - opt_out (lexicon hit, or Jev ≥ 0.90) → end/DNC directive.
    - bot_question (lexicon, or Jev ≥ 0.80) → disclosure directive for one reply, then return to the prior style, with a 4-turn cooldown.
    - Events do not consume the switch budget.
  - **Styles** (neutral, rushed, frustrated/calm, confused/simple, interested/closer):
    - Enter on a lexicon hit (instant).
    - Or enter on Jev p ≥ θ_enter (rushed 0.80, frustrated 0.75, confused 0.80, interested 0.85).
    - Or enter on Jev EMA ≥ θ_enter − 0.1 for 2 consecutive turns.
    - Exit only when Jev ≤ θ_exit (0.35–0.50) for 2 turns and the lexicon is silent.
    - Rushed is sticky for the rest of the call (ASSUMED: a busy seller stays busy). Confused auto-decays after one clarification reply.
  - **Jev overrides the lexicon** only to *cancel* a lexicon entry when Jev p ≤ 0.2 on the same turn. This guards against false positives such as the "meeting" or "recording" words, which have other senses.
  - **Budget and dwell**: at most 2 style switches per call, and a minimum 2-reply dwell. Only frustrated and opt-out can override after the budget is exhausted.
  - **Fail-safe**:
    - Any exception, a Jev timeout, 429/529, or a missing `call_key` → return the cached mode and directive (default neutral, "Continue normally."). HTTP 200 always.
    - The Jev client has a hard ~1.5 s timeout in the background.
    - Unknown `call_key`s are evicted after 15 min.
- ASSUMED **combinations**: rushed + interested → a crisp callback or meeting-slot directive. Language is a separate axis, handled by Sarvam's built-in switch.

### Gaps
- Whether Interaction ID appears in our workspace's tool picker is unverified. This is the doc-vs-UI conflict above.
- No sourced optimal thresholds or dwell values exist. All are priors to tune on the Q2 evaluation set.
- Whether partial and full calls are always prefix-related (versus ASR rewriting earlier words) is unmeasured.

## Q4. Deployment: where the server runs, given the OpenRouter IP allowlist and Sarvam's need for public HTTPS

### Takeaway
The hybrid design removes Jev from the critical path, which unlocks a **split deployment**:
- The public signal server (lexicon plus policy) runs on Daytona behind a cloudflared tunnel.
- A Jev worker on a VPN laptop (IPv4 forced) **pulls** jobs over an outbound connection, so no inbound path or allowlist change is needed.

The cleanest alternatives are (a) getting 35.234.211.110 added to the OpenRouter allowlist, or (b) fixing the LiteLLM `/typesafe` pass-through and checking that it is reachable from Daytona. For demo-day simplicity, everything on the VPN laptop plus cloudflared also works, at single-point-of-failure risk.

### Cited Findings
- PROVEN: The OpenRouter key has an IP allowlist.
  - The laptop works only over VPN with IPv4 forced (egress 121.241.109.212), because the VPN is IPv4-only and openrouter.ai resolves IPv6 first.
  - The Daytona egress 35.234.211.110 gets a 403.

  — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: Daytona preview URLs have no wildcard DNS or TLS. A cloudflared quick tunnel in the sandbox works, but its URL changes on restart. Sarvam calls came from 4.213.167.70 and returned 200 in 0.11 s. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: The LiteLLM gateway shows model_group `typesafe/jev-1.13` with 8 requests, all failures, last on 2026-10-05. Its configuration is unreadable to us. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: The LiteLLM TypeSafe pass-through forwards "any path under `/typesafe/`". You "replace `https://api.typesafe.ai` with `LITELLM_PROXY_BASE_URL/typesafe`", authenticate with a LiteLLM virtual key, and the proxy injects `TYPESAFE_API_KEY`. No latency figures are given. — [LiteLLM TypeSafe pass-through](https://docs.litellm.ai/docs/pass_through/typesafe)
- DOCUMENTED: Direct TypeSafe latency is p50 108 ms / p95 159 ms (author's machine, location unknown). OrcaRouter reports p50 151 ms. — [jev-voice-turn README](https://raw.githubusercontent.com/dabit3/jev-experiments/main/jev-voice-turn/README.md); [OrcaRouter](https://www.orcarouter.ai/blog/jev-typesafe-system-one-what-we-know)
- PROVEN: Our OpenRouter path breaks down as ~18 ms network + ~150 ms OpenRouter overhead + ~315 ms TypeSafe upstream. — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences
- ASSUMED options:

  | option | Jev reachable | public URL | risk | notes |
  |---|---|---|---|---|
  | A. All on VPN laptop + cloudflared | yes (IPv4 forced) | quick tunnel | laptop, VPN or venue Wi-Fi drop | fastest to ship; fine for a judged demo |
  | B. Daytona + OpenRouter allowlist adds 35.234.211.110 | yes | quick tunnel | needs the key owner/admin | cleanest; one ask |
  | C. Daytona + LiteLLM `/typesafe` | if the gateway is reachable from Daytona and fixed | quick tunnel | 8/8 failures today; VPN-only reachability | could cut ~150 ms (no OpenRouter hop), which might make sync viable |
  | **D. Split: Daytona server + laptop Jev worker (outbound pull via websocket or long-poll)** | yes | quick tunnel | worker loss → lexicon-only (graceful) | fits the hybrid; no allowlist change |
- ASSUMED: The quick-tunnel URL changes on restart, so keep cloudflared up for the whole event and re-paste the URL into the Sarvam tool if it restarts. A named tunnel needs a Cloudflare account. Check that this does not count as a "new outside vendor" (the quick tunnel is already in use).
- ASSUMED: Ask the Daytona admin for `*.proxy-daytona.intermesh.net` DNS plus a wildcard cert, and ask the OpenRouter key owner to allowlist 35.234.211.110, in parallel. Whichever lands first simplifies to option B.
- ASSUMED: If option C lands with a direct-TypeSafe p95 under ~250 ms from Daytona, revisit **sync-with-deadline** (race Jev against a ~300 ms budget and fall back to the lexicon). The policy interface does not change.

### Gaps
- Whether the LiteLLM gateway is reachable from Daytona at all, and why the 8 requests failed, is unknown.
- Latency from Sarvam (4.213.167.70) through Cloudflare to the laptop or Daytona was not separated from the 0.11 s total.

## Q5. Other fast options on our infra and industry "classifier sidecar" patterns

### Takeaway
Industry platforms that own the turn loop run the classifier in a pre-reply hook, either awaited or in the background:
- LiveKit `on_user_turn_completed`.
- Retell's `update_only` stream.
- Vapi `async: true` tools plus background messages.

Sarvam exposes only LLM-invoked synchronous tools, which makes fast-instant plus async-correct the closest equivalent. Among non-Jev options:
- An OpenRouter small LLM adds the same OpenRouter hop, plus generation time, with no calibrated probabilities.
- Sarvam LLMs have unproven latency for this job.
- A fine-tuned small encoder on Daytona CPU is plausibly ~20–50 ms. However, it needs labelled data (Jev as teacher) and Devanagari-aligned training, so it is a post-MVP upgrade.

### Cited Findings
- DOCUMENTED: LiveKit `on_user_turn_completed` is "called when the user's turn has ended, before the agent's reply". It is async. The docs show a non-awaited `session.say()` "fast pre-response" to "reduce the perceived gap". — [LiveKit nodes & hooks](https://docs.livekit.io/agents/build/nodes/)
- DOCUMENTED: The proposed LiveKit Jev plugin runs in `on_user_turn_completed` to avoid an extra LLM call costing "500–1500 ms". — [livekit/agents #7355](https://github.com/livekit/agents/issues/7355) (via [peer_platform_patterns.md](../VANI%20adaptive%20persona%20architecture/peer_platform_patterns.md))
- DOCUMENTED: In Retell's Custom LLM WebSocket, the server receives `update_only` transcript events and can push `update_agent` and `agent_interrupt`. — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket) (via [peer_platform_patterns.md](../VANI%20adaptive%20persona%20architecture/peer_platform_patterns.md))
- DOCUMENTED (support forum, secondary): A Vapi tool with `async: true` does not wait for the server. The webhook returns immediately and the server later sends a background message. — [Vapi support: async tools](https://support.vapi.ai/t/27099799/should-i-consider-vapi-tool-calls-with-async-true-as-just-fi). Vapi `message.add` hooks inject a system message "for the remainder of the call." — [Vapi hooks](https://docs.vapi.ai/assistants/assistant-hooks)
- DOCUMENTED: Sarvam has no per-turn hook. Its only automatic hooks are on_start and on_end. — [sarvam_platform_internals.md](../VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md)
- DOCUMENTED (third party): An OpenRouter vs OpenAI-direct test (200 GPT-4.1 calls) found OpenRouter TTFT 0.640 s vs 0.712 s direct. — [Opper router benchmark](https://opper.ai/blog/llm-router-latency-benchmark-2026). This contrasts with our measured ~150 ms OpenRouter overhead from India for the Decisions API (PROVEN, spike log). Location and endpoint differ.
- DOCUMENTED (third party): Llama 3.1 8B TTFT of ~0.13 s on Groq and SambaNova for short prompts. In the same test, OpenRouter was reported as "the slowest AI gateway at 25 seconds", which is an implausible outlier and treated as unreliable. — [AIMultiple AI gateways](https://aimultiple.com/ai-gateways). OpenRouter supports `provider.sort: "latency"`, `:nitro` and `preferred_max_latency`, and documents no overhead figure. — [OpenRouter provider routing](https://openrouter.ai/docs/features/provider-routing)
- DOCUMENTED (third party): An INT8 ONNX DistilBERT classifier reports p50 ~29 ms on CPU. — [HF model card](https://huggingface.co/Trakerlack/distilbert-toxic-onnx-int8). Static quantization with Optimum gives "~3x latency improvements". — [philschmid](https://www.philschmid.de/static-quantization-optimum). No published CPU latency was found for MuRIL or IndicBERT specifically.

### Inferences
- ASSUMED: The Sarvam mapping of the sidecar pattern is the hybrid. The lexicon is the "awaited" part, and the Jev worker is the "background" part whose result lands on the next tool call (Retell `update_only` / Vapi async analogue).
- ASSUMED: A small LLM via OpenRouter would be ≥ Jev latency. It pays the same ~150 ms hop, a TTFT of ≥0.13 s at best, and JSON generation, and it returns uncalibrated labels. Use it offline: as a teacher labeller, to write directives, and to generate synthetic Tamil and Gujarati turns.
- ASSUMED: Using a Sarvam LLM as the classifier is attractive for the "core is Sarvam" story. Measure `sarvam-105b-conversations` with `reasoning_effort: null` and a JSON schema, which needs one curl. Do not plan on it: reasoning-mode TTFTs are 14–22 s, and non-reasoning latency is unpublished.
- ASSUMED **local CPU model (stretch goal)**:
  1. Label ~5–10K ps07 seller turns with Jev (≈$0.40).
  2. Transliterate the turns to Devanagari.
  3. Fine-tune a small multilingual encoder (MuRIL or IndicBERT, or multilingual MiniLM) as multi-label.
  4. Export to INT8 ONNX on Daytona CPU. Expect ~20–50 ms per short turn.

  This could replace the lexicon (better recall) while Jev stays as the background corrector. It needs ~half a day plus a check of Daytona sandbox CPU and RAM. It is not needed for the demo.

### Gaps
- No measured CPU latency on the Daytona sandbox (CPU type and cores unknown).
- No published MuRIL or IndicBERT ONNX latency was found.
- No head-to-head evidence on sync vs async classification for user-perceived quality in voice agents, beyond Veris's turn-detection result.
