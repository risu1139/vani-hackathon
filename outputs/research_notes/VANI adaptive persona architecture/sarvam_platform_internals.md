# Sarvam Voice Agents (Conversations / Samvaad) internals for live per-turn persona switching

Research date: 2026-10-07. Method: downloaded every docs.sarvam.ai/conversations/*.md page listed in https://docs.sarvam.ai/conversations/llms.txt (about 110 pages, including all 2026 changelog pages), plus `pip download sarvam-conv-ai-sdk` (wheel v1.1.1, uploaded 2026-09-22) and read its source, plus the sarvamai GitHub org. Labels used: **[DOC]** stated in the official docs; **[CODE]** seen in the SDK wheel source (v1.1.1) but not documented; **[INF]** my inference; **[UNK]** unknown or unverified. Note: https://docs.sarvam.ai/llms-full.txt is now only a 13.7 KB index (the same as llms.txt), not the full docs. The full content lives in the per-page `.md` files.

## Q1. State transitions, prompt structure, templating: can a tool or webhook force a transition or inject instructions?

### Takeaway
Transitions, instructions and tool use are all driven by the LLM through function calling. The docs describe no rule engine that moves states from variable values. Two things can force a state or inject text deterministically: a **Code Tool** (Python, available on request or on enterprise plans; `context.change_state()`, `message_to_llm`, `message_to_user`) and an API tool's **response template**, which feeds text to the LLM. Multi-state agents are officially a legacy approach and will reach end-of-life once "multi-agent" launches.

### Cited Findings
- [DOC] A state has a Name, Instructions, Tools and Next states (allowed transitions). "Transitions move the agent from one state to the next when conditions are met, for example, after collecting a required field, verifying identity, or detecting that the caller wants to escalate." The page does not describe any mechanism other than the agent judging those conditions. — [Multi-state agents](https://docs.sarvam.ai/conversations/build/states-conversation-flow)
- [DOC] "Multi-state is an **older paradigm** that we are moving away from in favour of a **multi-agent** architecture. It remains available for specific use-cases and will reach end-of-life once multi-agent launches." Converting an agent to multi-state is "a **one-way** operation". — [Multi-state agents](https://docs.sarvam.ai/conversations/build/states-conversation-flow); [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- [DOC] Each state has its own instructions. Tools are either "global" (available in all states) or "state-level". Global vs state-level is documented for **tools**. The docs describe no separate "global prompt" field for multi-state agents. — [Tools](https://docs.sarvam.ai/conversations/build/tools)
- [DOC] The harness loop runs every turn: "1. Assemble context: conversation history, variables, and available tools. 2. The LLM reasons, and either responds or calls a tool. 3. If it calls a tool, the harness runs it and feeds the result back. 4. Repeat until the LLM produces a response." Also: "Values can also be injected into context (for example from an on-start hook or your backend), so the model always reasons over the right state." — [Harness](https://docs.sarvam.ai/conversations/build/concepts/harness)
- [DOC] Variables are inserted into instructions inline, by typing `@` in the editor. The `{{var}}` syntax appears in voicemail messages (`{{user_name}}`) and in API tool response templates (`The account balance is {{balance}}`). — [Instruction](https://docs.sarvam.ai/conversations/build/system-prompt); [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings); [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [DOC] "Tools can read and write any agent variable mid-call." An API tool can "Save reply into variables". Input variables have a toggle that controls whether they are sent to the LLM (on by default). Log Analyser shows **NEW** / **CHANGED** badges on variables per turn. — [Variables & Personalization](https://docs.sarvam.ai/conversations/build/variables-personalization)
- [DOC] Code Tools: "A code tool runs your Python inside the call, with access to a context object that holds the live interaction. It can … change how the rest of the conversation goes." Status: "available on request. Contact us". On the MCP surface, uploading `tools.py` (`upload_agent_code`) is listed as **Enterprise**. Non-enterprise workspaces get only HTTP, validator and verifier tools. — [Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools); [MCP Server](https://docs.sarvam.ai/conversations/mcp); [Changelog 2026-08-15](https://docs.sarvam.ai/changelog/2026/8/15)
- [CODE] `SarvamToolContext` (passed to code tools) has these fields: `state`, `next_valid_states`, `language`, `allowed_languages`, `agent_variables`, `internal_variables`, `end_conversation`. Methods: `change_state(state)` (raises an error unless the state is in `next_valid_states`), `change_language(lang)` (raises an error unless the language is in `allowed_languages`), `set_agent_variable` (the variable must already be defined), `set_end_conversation()`, `get_secret`. — [PyPI sarvam-conv-ai-sdk 1.1.1, file tool.py](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [CODE] `SarvamToolOutput` has `message_to_llm` (text fed back to the LLM), `message_to_user` (text spoken to the user) and `context`. At least one of the two messages is required. `SarvamTool.pre_run_message` is a "Message to user before tool execution". — [PyPI sarvam-conv-ai-sdk](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [CODE] The on-start hook context (`SarvamOnStartToolContext`) can set `initial_bot_message`, `initial_state_name`, `initial_language_name`, `speech_hotwords` and `text_to_speech_config` (speaker_id or speaker_name, plus `speech_settings` pitch, pace and volume). The source comment reads: "TTS override an on_start tool can set on its context". — [PyPI sarvam-conv-ai-sdk](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [DOC] Per-tool toggle: "Each tool has a toggle that controls whether it's sent to the LLM." — [Tools](https://docs.sarvam.ai/conversations/build/tools)

### Inferences
- [INF] The docs never say whether an `@variable` inside the instruction text is re-rendered when a tool changes it mid-call. The harness description ("Assemble context: … variables" on each turn) and the per-turn CHANGED badges suggest the **current** variable values are in the LLM context every turn. That could be as a variables block rather than by re-templating the prompt. Either way, the directive the LLM sees on the next turn should reflect a mid-call write. Verify this live on day 1 with a toy variable.
- [INF] A state cannot override speaker, voice or speed. A state has no voice fields in the docs, the code-tool context has no TTS fields (only on_start does), and the voice docs say the speaker stays fixed for the whole call.
- [INF] "Language" is per call and can change mid-call, through the core tool, auto-detect, or a code tool's `change_language`.

### Gaps
- [UNK] Whether the instruction text is literally re-templated each turn, or whether variables are sent as a separate block.
- [UNK] Whether an HTTP API tool (as opposed to a code tool) can force a state transition. The docs show no such field. Response fields can only be mapped into variables and the response template.
- [UNK] The launch date and API of "multi-agent".

## Q2. Tool mechanics: schema, timeouts, filler, latency, and any every-turn hook

### Takeaway
API tools are HTTPS webhooks that the LLM calls by name. They are synchronous, with a configurable **Max wait of up to 30 s** and a configurable "If it fails" message. They can receive the live **Call Transcript**, User Identifier, Interaction ID and Call Length. There is **no documented webhook that fires on every user turn without the LLM choosing it.** The only automatic hooks are on_start and on_end. Running a per-turn classifier therefore depends on instructing the LLM to call a tool on every turn, which is probabilistic.

### Cited Findings
- [DOC] Lifecycle options: `run` (during the conversation, called by the LLM), `on_start`, `on_end`. "`on_start` and `on_end` are **lifecycle hooks**: there is no LLM in the loop". The agent invokes a tool "by name (`call tool:your_tool_name` in the instructions)". — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [DOC] Request settings: method (GET/POST/PUT/PATCH/DELETE), URL, path, params, headers, body, auth (none, bearer, api_key, basic; secrets are stored in the workspace). Response: a template that uses `@` fields. Advanced settings: **Max wait** (timeout), **If it fails**, **Save reply into variables**. "Keep timeouts tight (configurable up to 30s)". — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [DOC] Call-context variables are resolved at request time: "the transcript includes everything said up to that point". User Identifier is populated on inbound calls only: "On outbound calls, use the number from the campaign contact instead." Added on 2026-08-20. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool); [Changelog 2026-08-20](https://docs.sarvam.ai/changelog/2026/8/20)
- [DOC] Filler: "a mid-call API hit means a pause on the line, so have the agent say something like 'let me pull that up' first." No automatic filler is documented for API tools. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [CODE] Code tools have a `pre_run_message`, for example "Let me check that for you." — [Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools); [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [DOC] Egress IP to allowlist: `4.213.167.70`. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [DOC] Tool analytics report p50 and p95 tool latency and flag tools with an error rate above about 5%. — [Changelog 2026-08-13](https://docs.sarvam.ai/changelog/2026/8/13)
- [DOC] Mock tools return a canned response, which is useful for testing flows. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)
- [DOC] The run-time claims "sub-second latencies" per turn and "20,000+ concurrent calls". — [Run-time](https://docs.sarvam.ai/conversations/build/run-time)
- [DOC] Webhooks that fire after the call: campaign webhook, inbound deployment webhook, instant outbound webhook. All are post-call. — [Changelog 2026-08-20](https://docs.sarvam.ai/changelog/2026/8/20); [Changelog 2026-09-02](https://docs.sarvam.ai/changelog/2026/9/2); [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload)

### Inferences
- [INF] Added latency per tool call is one extra LLM step (the decision to call), plus your HTTP round trip, plus a second LLM pass over the tool result. The second pass may be the larger cost. Expect several hundred ms on top of the normal turn, even if the classifier itself is fast. Sarvam publishes no per-tool latency number.
- [INF] Reliability of an every-turn tool call: an instruction such as "Before every reply, call tool:read_seller_signal" depends on the LLM. Temperature 0.1 (Compliant) should help. Expect occasional skipped calls. To limit the damage, persist the last persona in a variable so a skipped turn keeps the previous persona.
- [INF] Because the tool receives the full Call Transcript, your server (TypeSafe Jev via OpenRouter) can classify the latest user utterance without the LLM having to pass it as an argument.

### Gaps
- [UNK] Request and response JSON envelope of the API tool, beyond what the UI configures. The docs show none. Assume your endpoint returns arbitrary JSON and you map fields into the template and variables.
- [UNK] Whether the agent speaks anything while an API tool is pending. This is undocumented, so treat it as silence unless the LLM was told to speak first.
- [UNK] Any transcript-streaming or per-turn webhook. None was found in the docs, the changelogs or the OpenAPI listing.

## Q3. Which LLM powers the agent; can it be changed or brought from outside?

### Takeaway
There is no model picker and no bring-your-own-LLM option at any layer. A routed mix of Sarvam models and fine-tuned open-weight models serves the agent, including `sarvam-105b-conversations`. The only exposed control is temperature.

### Cited Findings
- [DOC] "Reasoning (LLM): a constellation of open-weight models along with `sarvam-105b-conversations`, the Sarvam-105B variant tuned for real-time dialogue. Workloads are routed automatically … so you don't pick a model per agent." — [Models](https://docs.sarvam.ai/conversations/build/models)
- [DOC] "Voice Agents does **not** support bringing your own models at any part of the stack (ASR, LLM, or TTS)." — [Models](https://docs.sarvam.ai/conversations/build/models)
- [DOC] "The underlying model is managed internally, there is no model picker." Model temperature ranges from 0.1 to 0.9, default 0.3. — [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- [DOC] Model API history: `sarvam-m` was deprecated on 2026-06-05 and `sarvam-30b` on 2026-08-18. `sarvam-105b` is the only Sarvam chat model on the API. Price: ₹29.28 input, ₹10.98 cached input and ₹73.2 output per 1M tokens, the same for `sarvam-105b-conversations`. — [Changelog 2026-06-05](https://docs.sarvam.ai/changelog/2026/6/5); [Changelog 2026-08-18](https://docs.sarvam.ai/changelog/2026/8/18)
- Sarvam's own skill file says `sarvam-105b-conversations` is "a 32K-context variant post-trained specifically for real-time dialogue". This is a GitHub skill file, not the docs. — [sarvamai/skills voice-agents SKILL.md](https://github.com/sarvamai/skills/blob/main/voice-agents/SKILL.md)

### Inferences
- [INF] Your external classifier (Jev via OpenRouter) is allowed because it runs behind a tool endpoint on your server, not in the real-time loop. That fits the rule against BYO models.

### Gaps
- [UNK] The context window and tool-call latency of the routed in-agent LLM.

## Q4. Language Switch: trigger, languages, voice effect, latency

### Takeaway
Language switching is a core tool, enabled by the setting "Switch language during call". An optional **auto-detected** switch has a "Switch after" delay. The **speaker does not change** when the language changes. A per-language voice is selected only from the starting language.

### Cited Findings
- [DOC] Core tool "Language switch: lets the agent change the spoken language mid-call. Enabled when 'Switch language during call' is enabled." — [Core tools](https://docs.sarvam.ai/conversations/build/tools/core-tools)
- [DOC] Settings: Starting language (can be overridden per campaign contact), Switch language during call, Languages allowed, "Auto-detected language switch: when enabled, the agent can switch based on detected speech (with a **Switch after** delay)", Output numbers in Indic. — [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- [DOC] "At the start of a call, the agent selects the voice mapped to the starting language. The assigned speaker then remains consistent for the duration of the call, even if the caller switches languages mid-conversation." — [Speakers & voice](https://docs.sarvam.ai/conversations/build/voice-language); [Changelog 2026-09-09](https://docs.sarvam.ai/changelog/2026/9/9)
- [CODE] Language enum in the SDK: Assamese, Bengali, Gujarati, Kannada, Malayalam, Tamil, Telugu, Punjabi, Odia, Marathi, Hindi, English, Konkani. The instant-outbound `initial_language_name` enum adds Sanskrit and omits Konkani. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/); [Create outbound call](https://docs.sarvam.ai/conversations/api/instant-outbound/create)
- [DOC] Sarvam variable `language_name`: "The language configured for the current call". — [Variables](https://docs.sarvam.ai/conversations/build/variables-personalization)

### Inferences
- [INF] For a Hinglish→Tamil demo, the same Bulbul voice will speak Tamil. Pick a voice that is good in both languages, or start the call in the language you expect. The skill file notes that Bulbul v4 voice personas are language-specific, for example `gokul_ta_narration` for Tamil.
- [INF] Hinglish is not a separate language. It is Hindi or English with code-mixing, which the LLM produces natively ("code-mixed, colloquial Indic").

### Gaps
- [UNK] Latency of a language switch, and whether `language_name` updates mid-call.

## Q5. Bulbul V4 vs V3; style or emotion control mid-utterance

### Takeaway
Bulbul V4 was added to Voice Agents on **2026-10-06**. It offers "improved quality and expressiveness" and a larger catalog of persona-named voices. Voice, speed and pitch are **agent-level settings fixed per call**. **SSML is not supported** (documented for v3). The docs show no style or emotion tags. The only per-session TTS override is at session start or on_start.

### Cited Findings
- [DOC] "Bulbul V4 is now available for Voice Agents, alongside Bulbul V3 … choose between Bulbul V3 and Bulbul V4 per agent." V4 display names describe a style, for example "Shubh - Hinglish Ad Voice", "Ritu - Hindi Support Agent", "Priya - Recovery Agent", "Simran - Hinglish Support Agent", "Ashutosh - Friendly, High, Expressive". — [Changelog 2026-10-06](https://docs.sarvam.ai/changelog/2026/10/6); [Speakers & voice](https://docs.sarvam.ai/conversations/build/voice-language)
- [DOC] Voice settings: Voice, Model (V3 or V4), speaking speed slider, pitch slider, pronunciation dictionary (JSON up to 5 MB, per language; "Phonemes are not supported yet"). Voice cloning is enterprise-only. — [Speakers & voice](https://docs.sarvam.ai/conversations/build/voice-language)
- [DOC] Models page: "176 natural voices", "Pace control: adjustable speed from 0.5x to 2.0x", 11 languages. — [Models](https://docs.sarvam.ai/conversations/build/models)
- [DOC] "**No SSML support**: Bulbul does not support SSML tags for fine-grained prosody control. Use `pace` for coarse control; split text at natural pause points." (Bulbul v3 page.) — [Bulbul model page](https://docs.sarvam.ai/api/getting-started/models/bulbul)
- [CODE] The session-start `text_to_speech_config` takes `speaker_id` (a voices-DB UUID) or `speaker_name`, plus `speech_settings` {pitch, pace, volume}. It can be set in the SDK's `InteractionConfig` or by an on_start code tool. Nothing in the WebSocket client protocol changes it mid-call. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- Sarvam skill file (model API, not agents): `bulbul:v4-flash` uses persona IDs of the form `voice_language_style`, for example `simran_en_customer`, `aparna_hi_customer`, `gokul_ta_narration`. "No v4 personas for ml-IN / od-IN". Pitch ranges from -0.5 to 0.5 and loudness from 0.1 to 2.5 on v4-flash. — [sarvamai/skills SKILL.md](https://github.com/sarvamai/skills/blob/main/voice-agents/SKILL.md)

### Inferences
- [INF] Within one call, the persona switch has to be expressed through **words**: shorter sentences for a rushed seller, slower step-by-step phrasing for a confused one, apology and empathy for a frustrated one. Pace, pitch and speaker cannot change mid-call on the platform. You can change the voice between calls (instant-outbound has no TTS override, but the SDK and on_start do), or pick a voice per demo leg.
- [INF] Fewer words per turn and fewer clauses sound faster even at a fixed speed. That is the best available proxy for changing pace.

### Gaps
- [UNK] No public Bulbul V4 API model page was found. docs.sarvam.ai/llms.txt lists only v3 model pages. V4's emotion and style controls are not documented for Agents.

## Q6. Saaras V4 inside agents: keyterms and code-mixed output

### Takeaway
Saaras V4 is routed automatically inside agents and has no agent-level setting. Keyterms are a Model-API feature. The agent equivalents are the **"Important words"** setting (ASR hotwords) and `speech_hotwords` at session start or on_start. The docs do not say an agent can choose an ASR output mode (codemix or translit).

### Cited Findings
- [DOC] "`saaras:v4` is now live on Voice Agents and generally available, routing happens automatically, with no configuration change needed." (2026-09-02) — [Changelog 2026-09-02](https://docs.sarvam.ai/changelog/2026/9/2)
- [DOC] Saaras v4 output modes: transcribe, translate, verbatim, transliterate, code-mix. It is "tuned for 8 kHz phone audio", covers "22 Indian languages and English", and adds Global English. — [Models](https://docs.sarvam.ai/conversations/build/models)
- [DOC] Keyterm prompting for saaras:v4 (up to 50 terms) is available on REST and Batch from 2026-09-09 and on the streaming WebSockets from 2026-09-22. These are Model API endpoints. — [Changelog 2026-09-09](https://docs.sarvam.ai/changelog/2026/9/9); [Changelog 2026-09-22](https://docs.sarvam.ai/changelog/2026/9/22)
- [DOC] Agent Advanced settings: "**Important words**: names or terms the agent should hear more accurately (ASR hotwords)." — [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- [CODE] `speech_hotwords: list[str]` exists in `InteractionConfig` and in the on_start context. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [DOC] Post-call transcripts in webhooks carry `en_text`: "English text of the turn (translated if the conversation was in another language)". — [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload)

### Inferences
- [INF] The Call Transcript that reaches your tool is probably also English or translated text, as in the webhook. That would hide language-switch cues from your classifier. Use the `language_name` variable, or pass it explicitly, to detect a switch. Verify on day 1.

### Gaps
- [UNK] The format and language of the Call Transcript passed to API tools (native script or English).

## Q7. Outbound and telephony: on-demand calls, numbers, Indian regulation

### Takeaway
**There is an on-demand single-call API ("Instant Outbound")**, so a campaign is not required. It needs a telephony connection (`connection_id`) and an agent number. The simplest way to get one is **Rent from Sarvam** (Vobiz-backed, needs KYC, 30-day rental paid from the Sarvam wallet). Per-call `agent_variables` and the starting language and state can be set. TRAI's 2026-09-18 amendment requires A2P/AI calls to be **pre-declared** to the telecom provider.

### Cited Findings
- [DOC] `POST https://apps.sarvam.ai/api/outbounds/v1/orgs/{org_id}/workspaces/{workspace_id}/outbounds` with body fields `app_config` {app_id, app_version, connection_config {connection_id, agent_phone_number}, agent_variables, app_overrides {initial_bot_message, initial_state_name, initial_language_name}}, `user_config` {user_phone_number} and `webhook_config` {url, metadata}. Returns `attempt_id`. — [Create outbound call](https://docs.sarvam.ai/conversations/api/instant-outbound/create)
- [DOC] The instant outbound webhook fires after each attempt with status `connected`, `no_answer`, `busy` or `failed`, plus duration, interaction_id, failure_reason (example: "exotel: Phone number is registered under TRAI NDNC"), final_agent_variables and interaction_transcript. — [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload)
- [DOC] The Voice Agents API uses the `X-API-Key` header. — [Changelog 2026-09-16](https://docs.sarvam.ai/changelog/2026/9/16)
- [DOC] Rent from Sarvam: Deploy → Phone Numbers → Add Connection → Rent from Sarvam. Choose Individual or Corporate, then complete KYC ("required before you can rent numbers"), then buy a number, which is "provisioned instantly". Rentals last 30 days and auto-renew. "No [credit card]. The cost of the number is deducted from your Sarvam wallet." Numbers starting with 080 or 079 are landlines and need a 0 or +91 prefix. — [Rent from Sarvam](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam)
- [DOC] Bring-your-own options: Exotel, Twilio, Smartflo, Pulse, Intalk, Vobiz, Plivo, generic SIP. Call transfer is "Supported end to end on Vobiz". — [Phone Numbers index](https://docs.sarvam.ai/conversations/llms.txt); [Changelog 2026-09-02](https://docs.sarvam.ai/changelog/2026/9/2)
- [DOC] Campaigns support a DND suppression list and API, cohorts streamed as JSON (up to 1,000 users per request, can be added while the campaign is running), and phone-number rotation. "Calling compliance is your responsibility." — [DND](https://docs.sarvam.ai/conversations/deploy/campaigns/dnd); [Changelog 2026-08-15](https://docs.sarvam.ai/changelog/2026/8/15); [Changelog 2026-09-01](https://docs.sarvam.ai/changelog/2026/9/1)
- [DOC] Max call length is configurable up to 60 minutes. Voicemail detection applies on outbound calls. — [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings)
- The TRAI TCCCPR (Third Amendment) Regulations, 2026, dated **18 Sep 2026**, define A2P calls to include "artificial-voice technologies". An entity must "pre-declare its use of the technology to its telecom service provider and provide details of the CLIs". Undeclared A2P calls are treated as unsolicited commercial communication. Numbers in the 140xx (promotional) and 1600xx/1601xx (service/transactional) series are not auto-flagged as spam. Terminating operators may charge up to ₹0.05/min for A2P calls. — [TelecomLead summary](https://telecomlead.com/telecom-services/trai-tightens-spam-call-rules-with-ai-ml-detection-%E2%82%B90-05-a2p-charge-and-faster-enforcement-127804); [TRAI PR 111/2026](https://www.trai.gov.in/sites/default/files/2026-08/PR_No111of2026.pdf) (not opened; it is listed in search results)

### Inferences
- [INF] For the live demo (calling the presenter's phone), use Instant Outbound with a rented Sarvam/Vobiz number and the presenter's explicit consent. KYC is the gating item, so start it immediately. The KYC turnaround time is not documented. Whether the A2P declaration has to be made by the hackathon team or is handled by Sarvam/Vobiz is unclear. If the presenter's number is on NDNC, the call may fail; the documented `failure_reason` shows exactly that.
- [INF] Instant Outbound takes no TTS override. To vary the voice per call, use separate agent versions or apps, or an on_start code tool.
- [INF] User Identifier is empty on outbound calls, so pass the seller context through `agent_variables`.

### Gaps
- [UNK] KYC turnaround, number prices (shown only in the catalog UI), whether an individual KYC is accepted for outbound use, and the effective date of the TRAI amendment.

## Q8. SDK surface (`sarvam-conv-ai-sdk` 1.1.1) and Web SDK

### Takeaway
The Python SDK can stream audio in and receive transcript, audio, text and events. It also has an **undocumented `send_text()`** for chat-mode sessions. Session-start overrides include `text_to_speech_config` and `speech_hotwords`. The protocol enum **declares** client actions `variable_update`, `language_change` and `state_transition`, but the SDK has **no message classes or methods** for them. Mid-call steering from outside is therefore unsupported in the SDK. Transcripts carry no interim flag and no timing beyond a timestamp.

### Cited Findings
- [DOC] Required `InteractionConfig` fields: `user_identifier_type`, `user_identifier`, `org_id`, `workspace_id`, `app_id`, `interaction_type`, `sample_rate` (16000). Optional: `version`, `agent_variables`, `initial_language_name`, `initial_state_name`. Methods: start, send_audio, is_connected, get_interaction_id, wait_for_disconnect, stop. — [Python SDK](https://docs.sarvam.ai/conversations/deploy/sdks/python)
- [CODE] Other public methods: `send_text(text)` (sends `client.media.text`), `send_voice_note(bytes, transcribe=True)`, `wait_for_connect(timeout)`, and a `create_conversation()` helper. Constructor arguments: `api_key` (SecretStr), `config`, `audio_interface`, `audio_callback`, `text_callback`, `event_callback`, `transcript_callback`, `base_url="https://apps.sarvam.ai/api/app-runtime/"`. The signed WebSocket URL comes from `GET {base}/orgs/{org}/workspaces/{ws}/apps/{app}/url` with the header `X-API-Key`. `InteractionType` is `call` or `chat`. Sample rates are 16000 or 48000 in; output is 16000. — [PyPI SDK 1.1.1](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [CODE] `CustomAppOverrides` (the session start message): agent_variables, initial_language_name, initial_bot_message, initial_state_name, speech_hotwords, text_to_speech_config. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [CODE] `ServerTranscriptMsg` fields: `type="server.event.transcription"`, `role` (user or bot), `content`, `timestamp`, `origin`. It has no interim/final flag, no language field and no latency. `ServerTextChunkMsg` carries agent text chunks with status pending, completed or failed. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [CODE] The `ServerMsgType` enum includes `user_speech_start`, `user_speech_end`, `variable_update`, `language_change`, `state_transition`, `kb_query` and `tool_call`. The parser union handles only text, text_chunk, transcription, audio_chunk, user_interrupt, interaction_connected, interaction_end and ping. The other types fail parsing and are logged as errors. `ClientMsgType` declares `client.action.variable_update`, `client.action.language_change` and `client.action.state_transition`, but no client message class or method uses them. A test fixture shows `server.media.text` carrying `"events":[{"type":"server.event.variable_update","variable_name":…,"variable_value":…}]`, which the SDK model ignores. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)
- [DOC] Web SDK (`sarvam-conv-ai-sdk/browser`, `ConversationAgent`): adds `getState()`, `mute()`/`unmute()` (sends silence so voice activity detection stays stable) and `audioLevelCallback`. "Reconnection is not supported: each WebSocket URL is single-use." Also: "Never expose production API keys in browser code." — [Web SDK](https://docs.sarvam.ai/conversations/deploy/sdks/web); [Deploy with Code](https://docs.sarvam.ai/conversations/deploy/deploy-with-code)
- [DOC] Platform **Tests**: "the platform plays a simulated user against a committed version of your agent while an AI judge grades each expected behavior". Up to 20 runs per case, with a REST API. — [Changelog 2026-09-17](https://docs.sarvam.ai/changelog/2026/9/17)
- [DOC] The MCP server at `https://mcp.sarvam.ai/voice-agents` can `configure_agent`, commit versions and test calls. Its tool list depends on the plan. — [MCP Server](https://docs.sarvam.ai/conversations/mcp)

### Inferences
- [INF] For demo 1 (bot against a simulated seller), drive the Sarvam agent through the SDK in `CALL` mode. Produce the simulated seller's speech with Bulbul TTS (16 kHz PCM) and send it with `send_audio`. The `transcript_callback` (role=user/bot) gives the turn boundaries your dashboard needs. A faster, more deterministic variant is `InteractionType.CHAT` with `send_text`, but that loses the voice element. You could also send a raw `client.action.variable_update` frame over the WebSocket. This is untested and undocumented, and the server may reject it, so do not depend on it.
- [INF] Because SDK sessions can set `text_to_speech_config`, demo 1 can show "persona-specific voice per session" even though the voice cannot change mid-call.
- [INF] Turn timing has to be measured on the client, from message timestamps and audio chunk arrival.

### Gaps
- [UNK] Whether the server accepts the declared `client.action.*` messages. React Native and Flutter SDK details were not reviewed.

## Q9. Pricing, limits, hackathon quotas

### Takeaway
The docs publish **no per-minute price for Voice Agents**. A third-party integrator quotes "₹6/min + telephony" (unverified). New Model-API accounts get ₹100 in free credits. Hackathon quotas were not found publicly.

### Cited Findings
- [DOC] Free credits for new accounts are ₹100 (previously ₹1,000). — [Changelog 2026-05-01](https://docs.sarvam.ai/changelog/2026/5/1)
- [DOC] Number rentals are billed from the Sarvam wallet. "Check your plan for pricing and included allocations." — [Rent from Sarvam](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam)
- [DOC] Overview analytics show "total billable minutes". — [Changelog 2026-08-13](https://docs.sarvam.ai/changelog/2026/8/13)
- Third-party claim: Sarvam-powered voice agents "starting at ₹6 per minute plus telephony costs". This is an integrator's price, not Sarvam's. — [edesy.in](https://edesy.in/ai-voice-agent/technology/sarvam-ai)
- [DOC] Limits: tool timeout up to 30 s, max call length 60 min, pronunciation dictionary up to 5 MB, streamed cohorts up to 1,000 users per request, webhook retries up to 200 per request. — [API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool); [Conversation Settings](https://docs.sarvam.ai/conversations/build/conversation-settings); [Campaigns](https://docs.sarvam.ai/conversations/deploy/campaigns)

### Gaps
- [UNK] The Voice Agents per-minute rate, hackathon account limits (concurrency, whether code tools are enabled, rental allowance), and rate limits on the instant-outbound API.

## Q10. Public examples and community posts of multi-state agents with tools

### Takeaway
Sarvam's GitHub has **no example of a multi-state Voice Agent**. The cookbook covers DIY pipelines (Exotel, LiveKit, Pipecat, Twilio notebooks). The only first-party code-tool example is the order-status sample in the docs. No X posts from Aug–Oct 2026 were reviewed (no access).

### Cited Findings
- The sarvamai org repos (pushed up to 2026-10-06) include sarvam-mcp, skills, sarvam-ai-cookbook, n8n-sarvam-node and sarvam-ai-sdk. In the cookbook, the voice-agent files are `integrations/build_voice_agent_with_{exotel,livekit,pipecat,twilio}.ipynb`. The skills repo has `voice-agents/SKILL.md`, which covers LiveKit and Pipecat only. — [github.com/sarvamai](https://github.com/sarvamai); [sarvam-ai-cookbook](https://github.com/sarvamai/sarvam-ai-cookbook); [skills](https://github.com/sarvamai/skills)
- [DOC] Code tool example `GetOrderStatus`: two HTTP calls, `set_agent_variable`, `message_to_llm`. — [Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools)
- [CODE] The SDK test suite (`tests/test_tools.py`, `test_context_functions.py`) exercises `change_state` and `change_language`. Its examples include a "language change tool" and valid and invalid state transitions. — [PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)

### Gaps
- [UNK] Community or X posts about mid-call persona switching. None were found in this pass. X was not searched directly.

## Q11. Synthesis: the most reliable way to switch persona per turn

### Takeaway
In order of reliability: (1) **Code tool, if Sarvam enables it for the hackathon org.** It is deterministic: `change_state` to a persona state, `set_agent_variable("persona", …)`, a `message_to_llm` directive, and optionally `message_to_user` for verbatim acknowledgements. (2) **API tool fallback** (always available): a single-state agent whose instructions contain a persona playbook keyed on an `@seller_mode` variable, and which is told to "call tool:read_seller_signal before every reply". The tool sends the Call Transcript and `language_name` to your server, which runs Jev and returns `{mode, directive}`. The reply is mapped into `seller_mode`, and the template injects the directive. (3) Voice, pace and speaker cannot change per turn. Change them per call, through the SDK `text_to_speech_config` or on_start.

### Cited Findings
- The building blocks are cited above: per-turn context assembly ([Harness](https://docs.sarvam.ai/conversations/build/concepts/harness)), tool variable writes and response templates ([API tool](https://docs.sarvam.ai/conversations/build/tools/https-tool)), code-tool context methods ([PyPI SDK](https://pypi.org/project/sarvam-conv-ai-sdk/)), code tools available on request ([Code Tools](https://docs.sarvam.ai/conversations/build/tools/code-tools)), speaker fixed per call ([Speakers & voice](https://docs.sarvam.ai/conversations/build/voice-language)).

### Inferences
- [INF] Ask Sarvam (support@sarvam.ai, or the hackathon contacts) **now** for Code Tools access. It is the only documented path to deterministic per-turn state changes.
- [INF] In the fallback, keep personas as **instruction sections inside one state**, not separate states, so that no transition is needed. Multi-state is legacy and its transitions are judged by the LLM anyway.
- [INF] Show the "seller asks if bot" case with a verbatim disclosure (`message_to_user` with a code tool, or a strict response template with an API tool). Show the language switch with the native Language Switch core tool and auto-detect, and have the classifier only confirm it.
- [INF] Budget for the tool round trip in each turn. Keep the classifier response under about 300 ms and set Max wait to about 2 s, with an "If it fails" fallback of "keep the current persona". The LLM may skip the call on some turns, so log `seller_mode` CHANGED events in Log Analyser to show the switches to judges.

### Gaps
- [UNK] Whether a per-turn tool call is fast enough on Sarvam's routed LLM. This needs a live measurement, with Tool analytics p50/p95 as the source.
