# Voice runtime block: Sarvam Voice Agents (Samvaad / Indus) role, interfaces, proof status

Research date: 2026-10-08. Method: re-downloaded all ~135 `docs.sarvam.ai/conversations/*.md` pages listed in `conversations/llms.txt`, plus every changelog entry from 2026-08-13 to 2026-10-06. Inspected the installed `sarvam_conv_ai_sdk` 1.1.1, which is still the latest version on PyPI. Read our spike log and the earlier docs notes. Web searches covered latency claims and integration patterns on other platforms.

Tags:
- **PROVEN**: seen in our own spike. Source: `raw/research/2026-10-07-spike-log.md`, cited below as [Spike log](raw/research/2026-10-07-spike-log.md).
- **DOCUMENTED**: stated on a docs.sarvam.ai page, cited inline.
- **CODE**: seen in the SDK 1.1.1 source but not documented.
- **ASSUMED**: not verified.

No customer data was used.

Earlier notes are still valid and not repeated here in full: [sarvam_platform_internals.md](outputs/research_notes/VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md), [2026-10-07-sarvam-platform-docs-check](raw/research/2026-10-07-sarvam-platform-docs-check.md) and [2026-10-07-sarvam-deploy-sdk-docs-check](raw/research/2026-10-07-sarvam-deploy-sdk-docs-check.md).

## Q1. What the runtime block is, its fixed interfaces, and what is proven, documented or assumed

### Takeaway
Sarvam's hosted runtime owns the whole live loop: telephony or SDK audio, VAD and turn-taking, ASR (Saaras v4), the LLM (routed, no model picker, no BYO model) and TTS (Bulbul v3/v4, voice fixed per call). Our system can attach at five points only:
1. **Call start:** agent_variables, initial message, language and state through the SDK, Instant Outbound or an on_start hook. The SDK can also set TTS.
2. **Per turn:** the LLM-invoked API tool, whose response is mapped into variables plus a response line.
3. **Call end:** the on_end hook, plus post-call webhooks.
4. **After the call:** the Analytics REST API (interactions, transcripts, recordings, agent_variables).
5. **Offline:** Tests (simulated users plus an AI judge) and versioning.

There is no documented per-turn push, no mid-call voice change, no deterministic forced variable write without the LLM choosing to call the tool (except with Code Tools, which are on request), and no async/background tool mode for API tools.

### Cited Findings

**Inputs at call start**
- PROVEN: the SDK CALL mode with `version=1` works. CHAT mode returns 404 "App not found for the interaction type" for this voice agent. The SDK needs a separate Voice Agents key sent as `X-API-Key`, distinct from the speech API key. — [Spike log](raw/research/2026-10-07-spike-log.md)
- CODE / DOCUMENTED: per-session SDK overrides (`CustomAppOverrides`) are `agent_variables`, `initial_bot_message`, `initial_language_name`, `initial_state_name`, `speech_hotwords` and `text_to_speech_config{speaker_id|speaker_name, speech_settings{pitch,pace,volume}}`. — [Python SDK](https://docs.sarvam.ai/conversations/deploy/sdks/python); SDK 1.1.1 source
- DOCUMENTED: Instant Outbound takes `app_config{app_id, app_version (integer, required), connection_config{connection_id, agent_phone_number}, agent_variables, app_overrides{initial_bot_message, initial_state_name, initial_language_name}}`, `user_config{user_phone_number}` and `webhook_config`. It has **no TTS override**. — [Create outbound call](https://docs.sarvam.ai/conversations/api/instant-outbound/create)
- DOCUMENTED: the on_start hook fetches context before the agent speaks and maps fields into agent variables. It can "gate tools or states based on returned flags". There is no LLM in the loop. — [On-start & on-end hooks](https://docs.sarvam.ai/conversations/build/on-start-on-end-hooks); [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- PROVEN (UI): "Voice is assigned per language at call start and will not change mid-conversation." DOCUMENTED: "The assigned speaker then remains consistent for the duration of the call." — [Spike log](raw/research/2026-10-07-spike-log.md); [Speakers & voice](https://docs.sarvam.ai/conversations/build/voice-language)

**Per-turn interface (API tool)**
- PROVEN: the API tool fired on every seller turn in 24 of 24 SDK CALL-mode turns (12/12 + 6/6 + 6/6), often twice per turn: once on the partial utterance when ASR finalises on a pause, then on the full one. The agent prompt had a MANDATORY "call tool every turn" rule at temperature 0 ("Compliant"). — [Spike log](raw/research/2026-10-07-spike-log.md)
- PROVEN: the request comes from 4.213.167.70 with UA `python-httpx/0.28.1`. The body is the JSON of the LLM-filled args, e.g. `{"seller_utterance": "...", "language": "hindi"}`. The utterance arrives verbatim in **Devanagari**, ASR errors included. The documented egress IP matches. — [Spike log](raw/research/2026-10-07-spike-log.md); [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- PROVEN: response fields are mapped into agent variables (`seller_mode`, `persona_directive`) and a response line ("Seller mode: @seller_mode | Directive…"). The directive changed the next reply: rushed → 11–13 words plus a callback offer; confused → one idea plus a check question; bot_question → disclosure. Caveat: prompt-only behaviour without the tool was inconsistent, so attribution still needs an ON/OFF A/B. — [Spike log](raw/research/2026-10-07-spike-log.md)
- PROVEN: the body-field value picker offers "Let the agent decide / Agent variable / Fixed value". Agent variables offered were user_name and Current day/date/time. **No Call Transcript appeared in the picker** in our UI. — [Spike log](raw/research/2026-10-07-spike-log.md)
- DOCUMENTED (conflicts with the point above): call-context variables User Identifier, **Call Transcript** ("the full conversation transcript so far"), Interaction ID and Call Length can be inserted with `@` in Body/Params/Headers. They are resolved at request time. User Identifier is filled on inbound calls only. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- DOCUMENTED: tool options are lifecycle (`run`, `on_start`, `on_end`), Max wait (≤30 s), "If it fails" message, and "Save reply into variables". Auth is none / bearer / api_key / basic, with secrets stored in the workspace. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- DOCUMENTED: there is no API-tool async or filler mode. The docs say: "a mid-call API hit means a pause on the line, so have the agent say something like 'let me pull that up' first." A grep of all conversations pages found no "filler", "asynchronous" or "background" tool option. Only Code Tools have `pre_run_message` (CODE: `tool.py:217`). — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- DOCUMENTED: harness loop per turn: "Assemble context: conversation history, variables, and available tools → LLM responds or calls a tool → harness runs it and feeds the result back → repeat." "Tools can read and write any agent variable mid-call." — [Harness](https://docs.sarvam.ai/conversations/build/concepts/harness); [Variables](https://docs.sarvam.ai/conversations/build/variables-personalization)
- DOCUMENTED: a deterministic mid-call state, variable or language change, or a verbatim user message, needs a **Code Tool**: `change_state`, `set_agent_variable`, `change_language`, `message_to_llm`, `message_to_user`. It is "available on request". PROVEN: there is no Code Tool option in our UI (API Tool, Data Validator, Data Verifier, Mock API only). — [Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools); [Spike log](raw/research/2026-10-07-spike-log.md)
- PROVEN: Workflows (multi-step journeys) are "only available for enterprise plans". DOCUMENTED: multi-state is "an older paradigm … will reach end-of-life once multi-agent launches". Multi-agent is **announced but not launched**: no page, changelog entry or API exists as of 2026-10-06. — [Spike log](raw/research/2026-10-07-spike-log.md); [Multi-state agents](https://docs.sarvam.ai/conversations/build/states-conversation-flow); [Changelog index](https://docs.sarvam.ai/changelog/llms.txt)

**Outputs during and after the call**
- CODE: SDK callbacks give `ServerTranscriptMsg` (role user/bot, content, timestamp; no interim flag), audio chunks and events (interaction_connected, user_interrupt, interaction_end). The `variable_update` / `tool_call` server events are declared but not parsed. — SDK 1.1.1 source; [Python SDK](https://docs.sarvam.ai/conversations/deploy/sdks/python)
- DOCUMENTED: the on_end hook pushes disposition and outcome variables, collected fields, and "transcript or recording references (when available)". — [On-start & on-end hooks](https://docs.sarvam.ai/conversations/build/on-start-on-end-hooks)
- DOCUMENTED: three post-call webhooks exist: Inbound deployment, Instant Outbound and Campaign. All fire **after** the call. The inbound payload has `app_id`, `app_version`, `interaction_id`, `duration`, `final_agent_variables`, `output_agent_variables` and `interaction_transcript[{role, en_text, indic_text?}]`. Delivery records can be listed, and up to 200 retries can be requested. — [Deployments webhook payload](https://docs.sarvam.ai/conversations/api/deployments/webhooks/webhook-payload); [Inbound deployments](https://docs.sarvam.ai/conversations/deploy/inbounds); [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload)
- DOCUMENTED (new vs. earlier notes): the **Analytics data-fetch API** with `X-API-Key`:
  - `GET apps.sarvam.ai/api/analytics/v1/{org}/{ws}/{app_id}/interactions` takes a required start/end datetime, limit/offset and filter_conditions JSON. Each item carries `interaction_id`, duration, `language_name`, `num_messages`, `average_agent_response_time_in_seconds`, `average_user_response_time_in_seconds`, `is_debug_call`, `audio_url`, `ended_by`, `failure_reason`, `has_log_issues` and `agent_variables`.
  - `GET …/transcripts/{interaction_id}` and `GET …/recordings/{interaction_id}` exist, but their response schema is undocumented (`{}` example).

  Sources: [Get interactions](https://docs.sarvam.ai/conversations/api/analytics/interactions); [Get transcripts](https://docs.sarvam.ai/conversations/api/analytics/transcripts); [Get recordings](https://docs.sarvam.ai/conversations/api/analytics/recordings)
- DOCUMENTED: output variables are "extracted by the LLM after the call ends" using an extraction prompt. A "Successful when" rule scores every call. — [Variables](https://docs.sarvam.ai/conversations/build/variables-personalization)
- DOCUMENTED: Log Analyser shows, per turn: ASR text, confidence and audio; the "exact inputs and outputs of each tool call"; LLM input/output cards; TTS speaker and settings; and variables with NEW/CHANGED badges. It also shows end-of-call flags (callback requested, language changed). — [Log Analyser](https://docs.sarvam.ai/conversations/monitor/agent-analytics/log-analyser)
- DOCUMENTED: the Agent Analytics → Tools tab reports tool calls, errors, error rate, and median and p95 latency "from tool dispatch to response", plus a per-tool table and error types. The Overview and Engagement tabs show average agent response latency and "end-to-end latency" in ms. The Boards API (SQL widgets over workspace tables, REST) was added 2026-09-16. — [Tools analytics](https://docs.sarvam.ai/conversations/monitor/agent-analytics/tools); [Overview](https://docs.sarvam.ai/conversations/monitor/agent-analytics/overview); [Engagement](https://docs.sarvam.ai/conversations/monitor/agent-analytics/engagement); [Changelog 2026-09-16](https://docs.sarvam.ai/changelog/2026/9/16)
- DOCUMENTED: Data retention is configurable per workspace, with a Voice Agents override (2026-09-15). — [Changelog 2026-09-15](https://docs.sarvam.ai/changelog/2026/9/15)

**Offline: versions and Tests**
- DOCUMENTED: versions go Draft → Committed → Deployed, with rollback. Inbound deployments lock to an agent plus a committed version. Instant Outbound and Tests take an integer `app_version`. — [Agent versioning](https://docs.sarvam.ai/conversations/build/agent/versioning); [Inbound deployments](https://docs.sarvam.ai/conversations/deploy/inbounds)
- DOCUMENTED: Tests (2026-09-17) play a simulated user against a **committed** version while an AI judge grades expected behaviours Pass/Fail.
  - Each case can run up to 20 times. A suite can hold up to 200 cases, with global guardrails, variables and variable mappings per app_version, and max turns. Results return the full transcript.
  - REST base: `apps.sarvam.ai/api/evals/v1/{org}/{ws}/test-suites`.
  - Rate limits: 60 req/min per key, 10 suite runs per 5 min per org, 20 single-case runs per min per org.
  - Errors: 402 when credits run out; 400 when the app fails the pre-run ping.

  Sources: [Tests](https://docs.sarvam.ai/conversations/build/tests); [Tests API overview](https://docs.sarvam.ai/conversations/api/tests/overview); [Changelog 2026-09-17](https://docs.sarvam.ai/changelog/2026/9/17)
- DOCUMENTED: the MCP server `https://mcp.sarvam.ai/voice-agents` (OAuth via Sarvam SSO) can build, deploy, test and analyse agents from an assistant. — [Changelog 2026-09-16](https://docs.sarvam.ai/changelog/2026/9/16)

**Platform behaviour**
- PROVEN: background ambience streams constantly. The agent nudges silent callers and then hangs up. — [Spike log](raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: run-time layers handle pronunciation, language switching, voicemail, hold, long silence, barge-in and background noise. Human handover is enterprise-only, and DTMF is "planned". — [Run-time](https://docs.sarvam.ai/conversations/build/run-time)
- DOCUMENTED: "Voice Agents does not support bringing your own models at any part of the stack." The only LLM knob is temperature. — [Models](https://docs.sarvam.ai/conversations/build/models)
- Changelog Aug–Oct 2026 for Voice Agents: Tool analytics (08-13); call-context variables for tools and campaign webhooks (08-20); saaras:v4 GA in agents (09-02); Data retention (09-15); MCP server and Boards API (09-16); Tests (09-17); Bulbul V4 and renamed voices (10-06). The 09-21 to 10-01 entries cover Cowork and Model APIs only. **Nothing new about tool execution modes, per-turn hooks or multi-agent.** — [Changelog](https://docs.sarvam.ai/changelog/llms.txt)

### Inferences
- ASSUMED: the fixed contract our "decision service" must satisfy.
  - It is an HTTPS POST endpoint reachable from 4.213.167.70.
  - It accepts `{seller_utterance, language, …}` (LLM-filled) and ideally `@Call Transcript` and `@Interaction ID`, if the picker exposes them.
  - It returns flat JSON fields within the Max wait (we set 2 s), e.g. `{seller_mode, persona_directive, …}`. The platform saves these into variables and renders them into one response line.
  - It must be **idempotent per (interaction_id, turn)**, because PROVEN duplicate calls occur (partial and full utterance).
  - It must hold its own per-call state (last mode), because a skipped or failed tool call should keep the previous persona.
- ASSUMED: everything downstream (dashboards, audits, judge scoring) should key on `interaction_id`. During the call, use our own tool-server log plus SDK transcript callbacks. After the call, use the webhook payload or the Analytics API for the authoritative transcript, variables and recording.
- ASSUMED: persona archetypes on the phone can be modelled as **separate committed versions** (one per voice or speed), selected through `app_version` in Instant Outbound, because Instant Outbound cannot override TTS. In SDK sessions, use `text_to_speech_config` instead. Untested whether a non-deployed committed version can be dialled through Instant Outbound.
- ASSUMED: Tests could serve as a cheap A/B harness (tool ON vs OFF versions, 20 runs per case) to show that the directive causes the behaviour change. It is unknown whether test runs execute real API tools or a text-only simulation.

### Gaps
- Is Call Transcript actually in our workspace's variable picker (doc vs UI conflict)? If it is, what script and format does it carry (Devanagari vs `en_text` translation) and how is it delimited? **Test (10 min):** type `@` in Body → look for "Call Transcript"; if present, add it as a field and use Send/Test or one SDK call, then log the body.
- Does a variable written by the tool render into `@seller_mode` inside the **instructions** on the next turn, or only through the response line? PROVEN for the response line only. **Test:** have the tool return mode only through Save-to-variable with an empty response template, then check the next reply and the Log Analyser LLM-input card.
- Is there a duplicate-call cost? Does the second (full-utterance) call replace the first result in context, or do both appear? **Test:** check Log Analyser Tool Call cards for one turn.
- Code Tools are available on request: not yet requested or confirmed for the hackathon org. Multi-agent: no date.
- The transcripts and recordings API response schemas are undocumented. **Test:** one GET per endpoint against a spike interaction_id.
- Do Tests runs call our real API tool, and do they run in voice or text? CHAT mode 404s for our voice agent, so a text simulator may fail or skip tools. **Test:** one single-case run (counts against the 20/min limit), then check our server log for 4.213.167.70 hits.

## Q2. Telephony: what a live demo call to a phone needs

### Takeaway
A phone demo needs: a Rent-from-Sarvam (Vobiz) number, which needs **KYC approved first** (turnaround undocumented); a committed agent version; and then either Instant Outbound to the presenter's phone (`connection_id` + `agent_phone_number` + `app_version`) or an Inbound deployment so the presenter dials in. Inbound is simpler for compliance: the person calls us, so no A2P outbound declaration or DND issue arises. The Web widget or SDK in a browser is a no-telephony fallback.

### Cited Findings
- DOCUMENTED: Rent from Sarvam has these steps: Deploy → Phone Numbers → Add Connection → Rent from Sarvam → Individual or Corporate + email → "Complete KYC … required before you can rent numbers" → buy (provisioned instantly, shown as "Sarvam Vobiz"). Each number has its own price, shown in the catalog. The rental is 30 days and auto-renews. It is paid from the Sarvam wallet, with no credit card. 080/079 numbers are landlines and need a 0 or +91 prefix. Route the number through an Inbound deployment, or through groups for campaigns. — [Rent from Sarvam](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam)
- DOCUMENTED: an Inbound deployment selects the agent plus a committed version, which is locked unless the deployment is paused. Its post-call webhook includes the transcript and variables. Sarvam advises: "place a real call … a phone call surfaces carrier audio, latency, and interruption behavior you can't see otherwise." — [Inbound deployments](https://docs.sarvam.ai/conversations/deploy/inbounds)
- DOCUMENTED: the Instant Outbound webhook statuses are connected, no_answer, busy and failed. The example failure_reason is "exotel: Phone number is registered under TRAI NDNC". — [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload)
- DOCUMENTED: Campaigns have a DND suppression list, and "Calling compliance is your responsibility." Call transfer is supported end to end on Vobiz. — [DND](https://docs.sarvam.ai/conversations/deploy/campaigns/dnd); [Changelog 2026-09-02](https://docs.sarvam.ai/changelog/2026/9/2)
- PROVEN (UI): call forwarding is offered for Vobiz only. Max call length is ≤60 min. — [Spike log](raw/research/2026-10-07-spike-log.md)
- Secondary: the TRAI TCCCPR Third Amendment (18 Sep 2026) treats AI/"artificial-voice" calls as A2P. Senders must pre-declare the technology and the CLIs to their telecom provider, or the calls count as UCC. — [TelecomLead summary](https://telecomlead.com/telecom-services/trai-tightens-spam-call-rules-with-ai-ml-detection-%E2%82%B90-05-a2p-charge-and-faster-enforcement-127804) (carried over from earlier notes; primary TRAI PDF not opened)
- DOCUMENTED: the Web widget and Web SDK are a no-phone channel. WebSocket URLs are single-use, and the API key must not be exposed in the browser (proxy it instead). — [Web SDK](https://docs.sarvam.ai/conversations/deploy/sdks/web); [Deploy with code](https://docs.sarvam.ai/conversations/deploy/deploy-with-code)

### Inferences
- ASSUMED: for the demo, use an **inbound** number that the presenter dials. This avoids NDNC failure on outbound calls and the A2P-declaration question. Keep Instant Outbound as the "agent calls the seller" story if KYC and the number arrive in time. Keep the SDK or browser path as the guaranteed fallback.
- ASSUMED: wallet balance gates number rental, calls and Tests (402 on Tests). Check the hackathon org's wallet.

### Gaps
- KYC turnaround, whether IndiaMART (Corporate) KYC is needed or an individual KYC suffices, number price, and whether the hackathon org gets a provisioned number from the organisers. **Action:** start KYC today, and ask the hackathon contacts.
- Whether Sarvam/Vobiz handles the TRAI A2P declaration for rented numbers. Undocumented.
- Whether Instant Outbound accepts a committed but not deployed `app_version`. **Test:** one call per version once a number exists.

## Q3. Latency: claims vs our 2.1 s, drivers, guidance

### Takeaway
Sarvam's claims are run-time "sub-second latencies, even at scale" in the docs and "<500ms" on the product page. Neither defines the measurement point. **We could not find a "sub-2 s on production traffic" claim** on sarvam.ai. Our measured seller-stop → agent-audio time was a median of ~2.1 s (range 1.2–3.5 s). That figure includes the VAD endpoint wait, a tool round trip and a second LLM pass, and it was measured without Jev. Expect Jev via OpenRouter to add ~0.5 s p50 on keep-alive. The documented knobs are eagerness, keeping tools fast, and tight timeouts. There is no documented guidance on prompt length.

### Cited Findings
- PROVEN: reply latency after the seller stops was median ~2.1 s, range 1.2–3.5 s, with a stub classifier. No no-tool baseline has been measured. — [Spike log](raw/research/2026-10-07-spike-log.md)
- PROVEN: Jev through OpenRouter (office, VPN, IPv4, keep-alive) has a p50 of 491 ms, or 760 ms with a new connection per call. The Daytona sandbox IP is not yet allowlisted. — [Spike log](raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: "each turn has to complete in well under a second to feel natural … **sub-second latencies**, even at scale", achieved by self-hosted, co-located models with "no external network hops between stages". — [Run-time](https://docs.sarvam.ai/conversations/build/run-time)
- Vendor marketing: "<500ms" real-time latency. — [sarvam.ai Voice Agents](https://www.sarvam.ai/products/voice-agents). This conflicts with or differs from the docs' "sub-second"; neither states whether it is TTFB, per stage or end-to-end.
- DOCUMENTED: "Eagerness to respond (Patient / Normal / Eager): how quickly the agent jumps in after a pause." "Sound sensitivity" controls false interruptions. — [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- DOCUMENTED: "Keep timeouts tight", "Design around latency: a mid-call API hit means a pause on the line". Tools analytics measures tool p50/p95 from dispatch to response, and Engagement shows end-to-end latency. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool); [Tools analytics](https://docs.sarvam.ai/conversations/monitor/agent-analytics/tools); [Engagement](https://docs.sarvam.ai/conversations/monitor/agent-analytics/engagement)
- DOCUMENTED: the Analytics interactions API returns `average_agent_response_time_in_seconds` per call, so the platform's own latency figure can be pulled per call. — [Get interactions](https://docs.sarvam.ai/conversations/api/analytics/interactions)
- DOCUMENTED: "a smaller, faster model backed by a tight harness often beats a bigger, slower one for real-time voice; latency is a feature." KB retrieval returns ~500 tokens of top chunks "to keep latency low". — [Models](https://docs.sarvam.ai/conversations/build/models); [Knowledge base](https://docs.sarvam.ai/conversations/build/knowledge-base)

### Inferences
- ASSUMED latency budget per seller turn: VAD endpoint wait (set by eagerness) + ASR final + LLM pass 1 (deciding to call the tool) + our HTTP round trip + LLM pass 2 + TTS first byte. The tool adds roughly one LLM pass plus our round trip. The PROVEN duplicate calls may add a second round trip when the partial-utterance call is still pending.
- ASSUMED: to cut latency, keep the decision service under ~300 ms. Options: a keyword or cheap fast path first, then Jev, possibly async with the result used next turn; keep-alive connections; set eagerness to Eager; keep the response line short; and keep the instructions compact. Prompt length is not documented as a factor.
- ASSUMED: "sub-second" probably refers to the Sarvam-internal pipeline without external tools and possibly excludes the VAD wait. Our 2.1 s is not directly comparable.

### Gaps
- No no-tool baseline. **Test (15 min):** same harness, tool disabled vs enabled, 20 turns each. Compare our timing with the platform's `average_agent_response_time_in_seconds` from the interactions API and the Tools-tab p50/p95.
- Effect of eagerness setting (Patient/Normal/Eager) on our median. Test with 3 × 10 turns.
- The source of the "sub-2 s on production traffic" figure in the brief could not be located. Treat it as unverified.

## Q4. How other platforms attach external decision services per turn; Sarvam community examples

### Takeaway
Hosted voice platforms offer three patterns:
- **Tool/function webhooks chosen by the LLM.** Vapi custom tools, with an optional async flag and request-start filler messages. This is what Sarvam API tools are.
- **Custom-LLM sockets that receive every turn.** Retell's LLM WebSocket sends `update_only` / `response_required` events with the live transcript. This gives the external service deterministic per-turn control.
- **Inject at call start only.** Avoids per-turn latency.

Sarvam offers only the first and third patterns: no BYO LLM, no per-turn push. We found no public Sarvam community example of a per-turn decision service on hosted Voice Agents.

### Cited Findings
- Retell: its LLM WebSocket gives the custom server the "live transcript and other inputs". The interaction types are `update_only`, `response_required` and `reminder_required`, and the server must answer `response_required` when Retell detects a turn end. — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket); [Retell integrate LLM](https://docs.retellai.com/integrate-llm/overview)
- Vapi: custom tools have an "Enable if the tool should run asynchronously" option, Request Start messages (e.g. "Checking the weather forecast. Please wait..."), and a configurable timeout. The result must be "a flat string". — [Vapi custom tools](https://docs.vapi.ai/tools/custom-tools)
- Hindsight's Vapi memory integration injects context once at call start, "no per-turn integration and no latency added mid-call". — [Hindsight blog](https://hindsight.vectorize.io/blog/2026/06/03/vapi-persistent-memory)
- Sarvam's own GitHub (cookbook, skills) covers DIY pipelines (LiveKit, Pipecat, Exotel, Twilio) and has no hosted-agent per-turn tool example. The only first-party code-tool sample is `GetOrderStatus` in the docs. — [sarvamai GitHub](https://github.com/sarvamai); [Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools) (from the earlier notes, re-checked via the changelog; no new examples)
- DOCUMENTED: Sarvam says wiring an outside model into the loop puts "reliability, latency, and accuracy at risk", which is the rationale for no BYO model. — [Models](https://docs.sarvam.ai/conversations/build/models)

### Inferences
- ASSUMED: our pattern ("prompt mandates tool every turn + variable mapping + response line") is the closest Sarvam equivalent to Retell's per-turn hook. It is PROVEN 24/24 in short calls, but its reliability over long calls or at higher temperature is unmeasured.
- ASSUMED: an optional hybrid is to run a heavier analysis (Jev, multi-question) out of band. The tool returns the previous turn's cached decision immediately and kicks off async scoring of the current utterance. The lag is one turn, but the tool latency stays at about 50 ms. This mirrors Vapi's async idea, implemented on our side.
- ASSUMED: the SDK's `transcript_callback` stream can feed a parallel observer (dashboard or judge) in SDK demos only. Phone calls have no live stream, only the tool calls and the post-call webhook.

### Gaps
- X/Twitter (@SarvamAI, @SarvamForDevs) was not searchable in this session. We found no community posts on per-turn tools with Sarvam Voice Agents.
- Whether Sarvam plans async/background API tools or per-turn webhooks: nothing on the roadmap besides "multi-agent", DTMF and human handover.
