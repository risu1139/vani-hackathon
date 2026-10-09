# Sarvam-native options for deterministic mid-call persona switching (2026-10-09)

Read-only research. Nothing was saved, published or uploaded on the agent.

Sources:
- **SDK.** `sarvam-conv-ai-sdk` 1.1.1 is installed. It is also the newest version on PyPI: `pip index versions` shows 1.1.1 as LATEST, and the downloaded wheel is byte-identical to the installed one (`diff -r` showed no differences). Paths below are relative to `site-packages/sarvam_conv_ai_sdk/`. "README" means the wheel's `dist-info/METADATA`.
- **Docs.** docs.sarvam.ai/conversations/*.md, fetched today. Changelog entries from 2026-09-01 to 2026-10-06 were read.
- **Console.** The logged-in Indus tab:
  - the agent config JSON that the console itself fetched (`GET apps.sarvam.ai/api/app-authoring/.../apps/Voice-Bot-104c356b-536d?app_version=1`);
  - the workspace feature flags (`GET indus.sarvam.ai/api/samvaad/flags`);
  - the console's own config-schema bundle (`18s3deri0mvj5.js`; chunk names change on redeploys);
  - accessibility-tree snapshots of the Settings and Instructions pages.
- **Prior notes not repeated here.** These are in raw/research: 2026-10-07 platform/deploy docs checks, 2026-10-08 on-start options, 2026-10-09 open-items, and midcall-pace-lang-switchlog. There is also outputs/research_notes/.../sarvam_platform_internals.md.

## Capability table

| capability | possible? | how exactly | evidence | tag |
|---|---|---|---|---|
| Hook that runs on every user turn without the LLM choosing to call it (pre-LLM, post-ASR, per-turn) | **No** | The SDK has only 3 bases: `SarvamTool` (during the call, LLM-invoked), `SarvamOnStartTool` (class must be named `OnStart`) and `SarvamOnEndTool` (class `OnEnd`). There is no per-turn, pre-LLM, post-ASR or interruption hook. The harness loop is: assemble context → LLM responds or calls a tool. | tool.py:216-236; README "Base Classes"; docs build/concepts/harness ("The LLM reasons, and either responds or calls a tool") | SEEN-IN-SDK + DOCUMENTED |
| Forced or required tool call (tool_choice) | **No** (not exposed) | The string `tool_choice` appears nowhere: not in the docs, not in the console config schema, not in the SDK. Only End call is described as "a required tool call". Per tool, the only control is whether it is sent to the LLM. | docs build/tools ("The model decides when to call a tool"); build/tools/core-tools; grep of the schema bundle for `tool_choice` / `ToolChoice` returned nothing | DOCUMENTED + SEEN-IN-CONSOLE |
| A separate "tool LLM" | Exists, not configurable | The config has `llm_model_variant: "Sarvam Pro"` and `tool_llm_model_variant: "yotta/llama-3.1-70b"`, plus `use_native_function_calling: true`. Feature flag `model_selection: hidden`. Docs: "no model picker", requests are routed automatically, `sarvam-105b-conversations` is in the stack. Whether the tool LLM decides tool calls (and so explains the skips) is unknown. | agent config GET; flags GET; docs build/models, build/conversation-settings | SEEN-IN-CONSOLE / UNCLEAR |
| Context methods available to a during-call code tool | Yes | Available calls:<br>• `get/set_agent_variable` (the variable must already be defined)<br>• `get/set_internal_variable` (hidden from the LLM; any name allowed)<br>• `get_secret`<br>• `get_current_language`, `change_language` (must be in `allowed_languages`)<br>• `get_current_state`, `change_state` (must be in `next_valid_states`)<br>• `set_end_conversation`<br>• `get_user_identifier`, `get_engagement_metadata`<br>Output: `message_to_llm` and/or `message_to_user` (spoken verbatim). `pre_run_message` is spoken before the tool runs. | tool.py:68-151, 216-224 | SEEN-IN-SDK |
| Change TTS speaker, pace or pitch mid-call | **No** (via any SDK API) | `text_to_speech_config` exists only on `SarvamOnStartToolContext` (tool.py:163) and on the client session-start message (`CustomAppOverrides`, messages/config.py:18). `SarvamToolContext` does not have it. No client message changes TTS mid-call. | tool.py:109-138 vs 154-175; messages/types.py:97-114 | SEEN-IN-SDK |
| Different voice when the language changes mid-call | **Unclear** | The UI's "Per-language voices" writes `initial_language_speaker_mapping` and forces `enable_mixed_speaker_settings: false`. Docs: the speaker stays the same "even if the caller switches languages". The runtime schema still has `enable_mixed_speaker_settings` + `mixed_speaker_config` [{language_name, internal_id}] and `language_voice_settings_mapping` (per language: pitch, pace, volume, `emotion`, `style`, `speed`). These are only reachable by a config write (API or MCP), not the UI. | schema `$V2VTextToSpeechConfig`, `$MixedSpeakerConfigV2`, `$VoiceSettings`; console code `eN()` sets `enable_mixed_speaker_settings:!1`; docs build/voice-language | SEEN-IN-CONSOLE / UNCLEAR |
| Per-call TTS / VAD / tool-LLM overrides from the HTTP on-start hook | Unclear | Schema `$OnStartOutput` = {agent_variables, internal_variables, user_information, authoring_config, **custom_app_config**}. `CustomAppConfig` covers text_to_speech_config (incl. language_voice_settings_mapping), vad_config, nudge_config, tool_llm_model_variant, initial_state_name and more. This applies at call start only. | schema `$OnStartOutput`, `$CustomAppConfig`, `$CustomTextToSpeechConfig` | SEEN-IN-CONSOLE / UNCLEAR |
| Multi-state flow; per-state prompt and tools | Yes (prompt, tools, visible variables); **no** per-state voice, language or TTS | `StateConfig` = {name, goal, instructions, context, tool_names, next_states, agent_variables_in_context}. `next_states` can be plain names or `NextState{name, condition}`; conditions are prompt text the LLM judges. Docs call multi-state "an older paradigm … end-of-life once multi-agent launches". Our agent is `is_single_prompt_mode: true` with one state `start`. "Convert to multi-state" sits under Settings→Advanced, and that section is hidden for us (`advanced_settings: hidden`, not visible in the Settings snapshot). | docs build/states-conversation-flow, build/conversation-settings#advanced; schema `$StateConfig`, `$NextState`; agent config; flags | DOCUMENTED + SEEN-IN-CONSOLE |
| State transition decided by code, not the LLM | Yes, but only from a code tool the LLM called | `context.change_state(s)` validates against `next_valid_states`. The SDK tests exercise valid and invalid transitions. A frozen classifier inside the tool decides; the LLM only triggers the call. | tool.py:128-134; tests/test_context_functions.py | SEEN-IN-SDK |
| Global vs state prompt | Yes | `global_prompt` ("Main goal/task prompt used for all states"), `response_style` (personality, guardrails), `global_context`, `global_tool_names`. Docs: global tools vs state-level tools. | schema `$BaseAgentConfig`; docs build/tools | SEEN-IN-CONSOLE + DOCUMENTED |
| LLM-updatable variables (built-in `update_variables` tool) | Exists, currently off | Per-variable `is_agent_updatable`. `allow_mid_call_variable_update`: "If False, the mid-call `update_variables` tool is not surfaced to the LLM". Ours is `false`. This is LLM judgement, so it breaks the team rule. | schema `$BaseAgentConfig`, `$VariableConfig`; agent config | SEEN-IN-CONSOLE |
| **Variable updated mid-call from outside ("Webhook Variable Update")** | **Unclear (promising)** | Per-variable `webhook_config {enabled, template}`, described as: "Configuration for updating this variable via interaction events webhook. If set, the variable can be updated during an active interaction." The template is Jinja over the webhook payload, e.g. `{{ response.data.score }}`. UI: Variables → Advanced → "Webhook Variable Update – Update this variable via webhook response". Our flag is `webhook_variable_update: allow`. The docs link `/conversations/build/advanced/webhook-variables` returns 404 publicly. The endpoint and payload are unknown. | schema `$WebhookVariableUpdateConfig`, `$VariableConfig`; flags GET; console bundle `3_ukabyjl0qa3.js` (UI strings); `2muhxi0edu7ao.js` (doc link) | SEEN-IN-CONSOLE / UNCLEAR |
| Client pushes a variable, language or state change over the session WebSocket | **Unclear** | `ClientMsgType` declares `client.action.variable_update`, `client.action.language_change` and `client.action.state_transition` (types.py:109-111). `__init__.__all__` lists `ClientVariableUpdateMsg`, `ClientLanguageChangeMsg` and `ClientStateTransitionMsg` (\_\_init\_\_.py:82-84), but those classes are missing from the wheel. The server echoes `server.event.variable_update`, `language_change`, `state_transition`, `tool_call` and `kb_query` (types.py:86-94), but the parser union drops them (messages/\_\_init\_\_.py:46-58). This works only for SDK and web sessions, not for Sarvam telephony calls. | listed files | SEEN-IN-SDK / UNCLEAR |
| External program observes the live user transcript | Yes (SDK and web sessions) | `transcript_callback` (ServerTranscriptMsg, role user/bot); events `user_speech_start/end` and `user_interrupt`. | conversation.py:634-660; messages/types.py:86-94; docs deploy/sdks/python | SEEN-IN-SDK + DOCUMENTED |
| Built-in language detection and auto-switch | Yes | Settings: "Switch language during call" (smart language switch), Languages allowed, Starting language, "Auto-detected language switch" with a "Switch after" delay. That last control is in the docs but not visible in our Settings snapshot. Config: `enable_language_identification: true`, `enable_lid: true` (adds the global tool `change_output_language`, so the LLM calls it), `lid_supported_languages`, STT `min_audio_duration_for_language_lid`. `LanguageIdentification{lid_mode: always\|once\|first_turn, language_switch_conversation_connector}` is currently null. | docs build/conversation-settings, build/tools/core-tools; agent config; schema `$LanguageIdentification`; enum in bundle | DOCUMENTED + SEEN-IN-CONSOLE |
| Language switch done by our code | Yes | `context.change_language(SarvamToolLanguageName.GUJARATI)` from the classifier tool. | tool.py:123-126 | SEEN-IN-SDK |
| Interruption / barge-in | Yes | UI: "Let callers interrupt" (switch). Config: `allow_interrupt_during_playback: true`. | Settings snapshot; agent config `interaction_config` | SEEN-IN-CONSOLE + DOCUMENTED |
| Endpointing / silence | Yes (coarse in UI, fine in config) | UI: "Eagerness to respond" (Balanced) and "Volume threshold" (Normal). Docs also mention "Detect when the caller stops talking" under Advanced (hidden for us). Schema:<br>• `vad_config{primary_vad: basic-vad\|hybrid-vad, speech_frame_config{silence_duration_frames (default 6), analysis_frame_size, volume_threshold dBFS, num_initial_ignored_frames}}`;<br>• `probability_modulator_config{short_utterance_sensitivity_duration, bot_resist_interrupt_duration, …multipliers}`;<br>• TTS `silence_duration` (ms between sentences, ours 300).<br>Ours: `basic-vad`, frame config null. | Settings snapshot; schema `$VADConfig`, `$SpeechFrameConfig`, `$ProbabilityModulatorConfig`; docs build/conversation-settings#listening | SEEN-IN-CONSOLE + DOCUMENTED |
| Silence nudges, including a tool-type nudge | Yes; tool type unclear | Nudge after N seconds, each with its own message; option to hang up after unanswered nudges. The console nudge editor has a radio for "Text" vs "Widgets/Tool" (`nudge_type: "tool"`, `tool_name`). That would be a timer-driven tool run with no LLM choice. | docs build/conversation-settings; console bundle `0iq-bnozwj0wv.js` | DOCUMENTED + SEEN-IN-CONSOLE / UNCLEAR |
| Outbound HTTP from code tools | Yes (documented); our egress is unproven | Docs and README examples use `httpx.AsyncClient(timeout=5.0)` inside `SarvamTool.run` and `OnStart`. Secrets come via `context.get_secret`. The API tool timeout is up to 30 s and its egress IP is 4.213.167.70. The code-tool timeout is not documented. | docs build/tools/code-tools; build/tools/https-tool#network-access; README "Secrets" | DOCUMENTED |
| Live call context to an API tool | Yes | `@Call Transcript` (so far), `@Interaction ID`, `@Call Length` and `@User Identifier` are substituted at request time. The docs list "sentiment analysis" on your backend as a use. | docs build/tools/https-tool | DOCUMENTED |
| Native sentiment or emotion detection | **No** | Nothing in the docs, flags or schema. The `emotion` field in `VoiceSettings` is a TTS output knob (alongside ElevenLabs-style `stability`/`similarity_boost`), not detection. "Expressive mode" in the console = `skip_translate_transliterate` (the LLM writes native script directly), not emotion. | docs; schema `$VoiceSettings`; console code | DOCUMENTED (absence) + SEEN-IN-CONSOLE |
| Knowledge base | Yes | KB Query core tool (LLM-called) once a KB is attached. | docs build/knowledge-base, core-tools | DOCUMENTED |
| Post-call analytics | Yes | Output variables extracted by prompt after the call, a call goal, Agent Analytics, Log Analyser (per-turn waveform, ASR confidence, variables with NEW/CHANGED badges, tool calls), Boards SQL, webhooks. Analytics API `agent_variables` gives our switch_log (prior note). Prompt-based `evaluation_config.criteria` also exists in the config (empty). | docs monitor/*, build/variables-personalization; agent config | DOCUMENTED + SEEN-IN-CONSOLE |
| Memory of earlier calls | Exists, hidden | `memory_config.episodic_memory_config.k_recent` (1–50 past conversations); flag `memory_config: hidden`. | console bundle; flags | SEEN-IN-CONSOLE |
| DSL "Workflows" (possibly deterministic flows) | Not for us | MCP `workflows` domain / `configure_workflow`, "enterprise". Flag `workflows: hidden`. "Multi-agent" is announced, with no date. | docs mcp; flags | DOCUMENTED + SEEN-IN-CONSOLE |
| Sept/Oct 2026 releases relevant to switching | None | The entries are:<br>• 10-06: Bulbul V4 in agents, voice catalog<br>• 09-09: per-language voices, locked for the whole call<br>• 09-17: Tests<br>• 09-16: MCP server<br>• 09-02: Saaras V4 (better LID, code-mixing) and call transfer<br>No per-turn hook, tool forcing or mid-call TTS change. | docs changelog/2026/{9,10}/*.md | DOCUMENTED |

## Best Sarvam-native design for deterministic mid-call switching

**Bottom line.** Sarvam has no per-turn hook and no forced tool call. Every in-Sarvam code path during a call starts with the LLM choosing a tool. The one exception is the platform's own language switching, and possibly two unproven external push channels.

So the cleanest design keeps the decision in frozen code (our classifier) and narrows what the LLM must do to "call the tool". Then we measure that call rate. Two things could remove the LLM from the loop entirely:
- Webhook Variable Update, if it is what its schema says;
- `client.action.variable_update`, on SDK/web sessions only.

Both need proof first (tests T1 and T2).

**Recommended stack (in order of reliance):**

1. **Language switch: let the platform do it, and log it in code.** The built-in LID / smart switch already switched 6/6 and 2/2 times without our tool. Keep it on. Take the signal from the transcript or `language_name` after the call (OnEnd or the analytics API), not from our tool.

   Optional belt-and-braces: our classifier tool detects the script or language of the utterance and calls `context.change_language(...)` itself, so the decision is ours, not the LLM's.

   Hypothesis for skip (a): on switch turns the LLM spends its tool call on the built-in `change_output_language` (enabled by `enable_lid: true`) instead of ours. Check this in Log Analyser (T3).
2. **Rushed / frustrated / confused / interested: a frozen classifier in the `ReadSellerSignal` code tool (as today), with the switch applied by code.** Two ways to apply it:
   - **(A) Today's variable route, hardened.**
     - Keep `persona_directive` overwritten by code. Keep `allow_mid_call_variable_update=false` so the LLM cannot write variables itself.
     - Debounce double or partial calls: store the last utterance hash, the time, and the stable mode in `internal_variables`. Only flip the mode when the same mode appears twice, or when the utterance is final (longer than the last one and not a prefix of it). On a duplicate, return "no change".
     - Make the tool the only non-core tool. Its description and the instructions' first line should say: "Call read_seller_signal with the seller's exact words before every reply."
     - Remove `read_seller_signal_http` from the state's `tool_names`, because two similar tools cause confusion.
   - **(B) Multi-state route.** Use one state per mode (`neutral`, `rushed`, `frustrated`, `confused`, `interested`). Each has its own `instructions` (the persona block), the same tool list, and `next_states` = all the others.
     - The classifier tool calls `context.change_state(mode)`. Code decides; the LLM's prompt conditions are not used.
     - Benefit: the persona text is a whole state prompt, not a variable splice, and `agent_variables_in_context` can hide irrelevant variables per state.
     - Costs: the console hides the conversion (Advanced is hidden), so it needs a config write via API or MCP. It is a legacy paradigm. It is unproven whether the new state's prompt applies to the same reply or only the next one (T5).

   Either way the LLM still has to call the tool. That is the residual risk; quantify it (T4).
3. **Voice and pace mid-call.**
   - **Pace / "slow down".** Directive-driven phrasing (short comma phrases and ellipses) is already proven (+17–33% delivery time).
   - **Exact wording.** For key lines the tool can return `message_to_user` (spoken verbatim, so no LLM paraphrase) with comma or ellipsis pacing baked in.
   - **True speaker, pace or pitch change.** Only at call start: OnStart `text_to_speech_config` (proven), or the HTTP on-start `custom_app_config` (unclear).
   - **The only possible mid-call voice change** is tied to language: `enable_mixed_speaker_settings` / `language_voice_settings_mapping`, set by a config write (T6). It cannot express "same language, slower or calmer voice".
4. **Fully deterministic option (no LLM call in the loop), if T1 or T2 passes.**
   - The classifier runs outside Sarvam on our host (Daytona or a local demo box). It receives each user turn: SDK `transcript_callback` for SDK/web sessions, or an interaction-events webhook if that is what feeds T2.
   - It pushes `seller_mode` / `persona_directive` into the live call via Webhook Variable Update (T2) or `client.action.variable_update` (T1).
   - The LLM then just reads `@persona_directive` on its next turn.

   Caveats:
   - This adds a network hop (latency against the turn).
   - T1 does not exist on phone calls.
   - Daytona currently lacks a stable public URL (prior note).

Per signal:

| signal | detector (frozen) | applied by | depends on LLM choosing a tool? |
|---|---|---|---|
| language switch | Sarvam LID / smart switch (plus our script check in the tool) | runtime switches language; optionally our `change_language` | **No** for the switch itself; yes for our optional override |
| rushed | classifier in code tool | variable or state set by code; reply ≤12 words plus callback offer | yes (tool call); **no** only via T1/T2 |
| frustrated | classifier in code tool (lexicon gap: "फिर से पूछ रहा हूं… वरना फोन रख दो") | same | same |
| confused | classifier in code tool | directive: short comma phrases plus a check-in; optional `message_to_user` | same |
| interested | classifier in code tool | directive: move to meeting/time step | same |
| voice / pace | per-call choice in OnStart (from the persona decider) | OnStart `text_to_speech_config` | **No** (lifecycle hook); mid-call only via phrasing, or a language-tied voice (T6) |

## Tests to settle the unclear items (small, one agent clone each; team approval needed for any config write)

- **T1. Client variable push.** Patch `AsyncSamvaadAgent._route_message` to log raw frames.
  - Mid-call, enqueue raw JSON `{"type":"client.action.variable_update","origin":"client","timestamp":…, "agent_variables":{"persona_directive":"RUSHED: reply in ≤8 words"}}`. Also try the key variants `variables` and `data`.
  - Watch for `server.event.variable_update`.
  - Check the next reply's length, and `agent_variables` in the analytics API.
  - Repeat with `client.action.state_transition` and `client.action.language_change`.
  - Pass: the reply follows the pushed directive in 3/3 tries.
- **T2. Webhook Variable Update.**
  - In a clone, turn on the toggle for `persona_directive` with template `persona_directive`, and capture the save request in DevTools to see the stored `webhook_config`.
  - Then ask Sarvam support (or check the in-app docs link `/conversations/build/advanced/webhook-variables`) for the inbound endpoint and payload.
  - Pass: an external POST during a live call changes the next reply.
- **T3. Why the tool was skipped on switch turns.** Open Log Analyser for the 4 earlier switch turns and check whether `change_output_language` was called and ours was not. If so, repeat with our tool doing `change_language` and `enable_lid` off (smart switch kept on), and compare call rate and switch success.
- **T4. Tool-call rate baseline.**
  - Run 20 scripted turns (5 per signal plus 4 language switches) under (A) as is, and (A) with the "call before every reply" first-line instruction, a single tool and debounce.
  - Report the per-turn call rate, the double-call rate and the wrong-mode rate from `switch_log`.
- **T5. State route.**
  - In a clone, use the API to write 5 states with code-only transitions (`next_states` = plain names, no conditions).
  - Check:
    - that `change_state` returns OK;
    - whether the same-turn reply uses the new state's prompt;
    - `server.event.state_transition` frames;
    - the Log Analyser state field.
- **T6. Language-tied voice change.** In a clone, set `enable_mixed_speaker_settings: true`, `mixed_speaker_config: [{Hindi: male UUID}, {Gujarati: female UUID}]`, plus `language_voice_settings_mapping` with a different pace for Gujarati. Switch language mid-call, record, and measure F0 and speech rate before and after.
- **T7. HTTP on-start `custom_app_config`.** Have an on-start API tool (mock) return `{"custom_app_config":{"text_to_speech_config":{"speech_settings":{"pace":1.3}}}}`. Check whether the greeting pace changes (compare with the 0.9 / 1.3 baseline).
- **T8. Tool-type nudge.** Set a nudge with `nudge_type: "tool"` → `read_seller_signal`, then stay silent for 5 s. Check whether the tool runs without an LLM decision (the tool_call event or Log Analyser).
- **T9. Endpointing against double calls.** Set Eagerness to Patient and run the same scripted mid-sentence-pause seller.
  - Measure the restarted-reply rate (17% baseline) and tool double-call rate.
  - If the config route is allowed, try `vad_config.primary_vad: hybrid-vad` and `silence_duration_frames` 8–10.
- **T10. Code-tool egress.** Have a code tool `httpx.get` a public echo with `timeout=3`. Log the status, latency and source IP (expect 4.213.167.70), to decide whether calling Jev in-call is viable.
