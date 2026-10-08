# Peer-Platform Patterns for Mid-Call Persona Adaptation (mapped to Sarvam Voice Agents primitives)

Research date: 2026-10-07. All URLs fetched/searched on this date unless labelled. "Documented" = stated on the cited page. "Inferred" = my reasoning. "Training-knowledge (unverified this session)" = I believe it to be true from prior knowledge but did not re-fetch a page confirming it; the report writer should treat it as lower confidence.

Sarvam primitives we can control (from the brief): (a) per-state instructions, (b) LLM-invoked tools, (c) variables, (d) on-start hooks. Voice is fixed per call.

---

## Q1. Retell AI: how does it do mid-call adaptation?

### Takeaway
Retell's two mechanisms are (1) graph-based **Conversation Flow** with transitions that are either LLM-judged (prompt) or deterministic **equation conditions over dynamic variables**, and (2) a **Custom LLM WebSocket** that lets your server write every response and push an `update_agent` event, though that event covers only responsiveness, interruption sensitivity and reminder timing, not voice or speed. The equation-over-variables transition is the pattern that transfers best to Sarvam.

### Cited Findings
- Conversation Flow has five node types: Conversation (dialogue without tools), Subagent (dialogue with tool calling), Function (deterministic API execution), Logic (branching) and End. Global settings include prompt, personality, voice and language. "The choice of model can be overridden within individual nodes." The overview page does not mention per-node voice or speed overrides. — [Retell Conversation Flow overview](https://docs.retellai.com/build/conversation-flow/overview)
- Transitions come in two types. **Prompt-based** transitions are natural-language conditions the LLM evaluates. **Equation-based** transitions are deterministic comparisons over dynamic variables (`==`, `!=`, `>`, `<`, `CONTAINS`, exists) with "no LLM involvement." — [Retell transition conditions](https://docs.retellai.com/build/conversation-flow/transition-condition)
- When transitions are evaluated: for conversation nodes, "after each user turn — or, with Skip Response on, as soon as the agent finishes speaking". For function, code and MCP nodes, after tool results arrive. Logic split nodes evaluate immediately on entry. — [Retell transition conditions](https://docs.retellai.com/build/conversation-flow/transition-condition)
- Evaluation order: Always edges, then equation conditions (top to bottom), then prompt conditions (the LLM picks the best match), then else edges, otherwise stay in the current node. Global-node entry conditions are evaluated alongside the prompt conditions. — [Retell transition conditions](https://docs.retellai.com/build/conversation-flow/transition-condition)
- Equation conditions can reference only dynamic variables. For information learned during the call, you must use prompt conditions or "first capture values using extract DV nodes, then branch." — [Retell transition conditions](https://docs.retellai.com/build/conversation-flow/transition-condition)
- In the Custom LLM WebSocket, Retell sends `update_only`, `response_required` and `reminder_required`. The server sends `response` (streamed, with `content_complete`), `agent_interrupt` (stop current speech and speak now), `metadata`, tool-call events and `update_agent`. `update_agent` adjusts only responsiveness (0–1), interruption sensitivity (0–1) and reminder timing. The page gives no voice or speed change mid-call. — [Retell LLM WebSocket API](https://docs.retellai.com/api-references/llm-websocket)

### Inferences
- The **"extract variable → equation edge"** pattern maps directly onto Sarvam. A tool such as `report_signals` writes a variable such as `persona_mode`, and the state transition or instruction text branches on that variable rather than on a free-form LLM judgement. This is deterministic and testable.
- Retell's `update_only` stream suggests a design where an external classifier sees every transcript update without being on the critical path. Sarvam probably has no equivalent push channel, so the classifier has to be reached through a tool call.
- Even Retell offers no documented mid-call voice or speed change through the WebSocket. "Voice fixed per call" is normal across the industry, not a Sarvam-specific handicap.

### Gaps
- I did not find a Retell built-in, real-time sentiment signal usable for branching mid-call. Retell's post-call analysis (sentiment and so on) is known from training knowledge, but I did not verify it this session, and it is post-call only.
- I could not confirm whether conversation or subagent nodes can override voice or speed per node.

---

## Q2. Vapi: squads, hooks, live control

### Takeaway
Vapi adapts through **Squads**: handoffs between specialised assistants, each of which can have its own voice through `assistantOverrides`. It also has **assistant hooks**, event-triggered actions including `message.add`, which injects a *system message* that changes LLM behaviour for the rest of the call. Hooks cannot change voice or config. The `message.add` system-message injection is the closest analogue to what VANI needs.

### Cited Findings
- Squads split a workflow into specialised assistants that transfer control during the call, keeping "full conversation context across handoffs". You can "limit message history to reduce tokens, improve performance, and prevent context poisoning". Variable extraction and summaries can happen at handoff. Vapi claims squads reduce "hallucination, cost, and latency versus one assistant." — [Vapi Squads](https://docs.vapi.ai/squads)
- `assistantOverrides` changes individual squad members (for example, the voice) without editing the saved assistant. The docs' example uses it to make *all* members share one voice. — [Vapi Squads](https://docs.vapi.ai/squads)
- Assistant hook events: `call.ending`, `call.timeElapsed`, `assistant.speech.interrupted`, `customer.speech.interrupted`, `customer.speech.timeout`, `assistant.transcriber.endpointedSpeechLowConfidence`. Actions: `say` (exact or prompt), `tool` (transferCall, function, endCall), `message.add`. — [Vapi assistant hooks](https://docs.vapi.ai/assistants/assistant-hooks)
- `message.add` with role `system`: "Instead of speaking a fixed message, you can inject a system message into the conversation to change the LLM's behavior for the remainder of the call." Hooks cannot directly change voice or other assistant config. — [Vapi assistant hooks](https://docs.vapi.ai/assistants/assistant-hooks)
- Community reports say that for hooks you should prefer `exact` over `prompt` for reliability, and that there is a `timeoutSeconds` bug report. — [Vapi support thread](https://support.vapi.ai/t/33046267/prompt-on-customer-speech-time-out-hook); [Vapi community](https://vapi.ai/community/m/1420777051228606515)
- Live Call Control: the server receives `call.monitor.controlUrl` and can POST to it, for example `{"type":"transfer", ...}`. The dynamic-transfer page documents only transfer and gives no latency or timeout numbers. — [Vapi dynamic transfers](https://docs.vapi.ai/calls/call-dynamic-transfers)

### Inferences
- Vapi's pattern is "event → inject system message." On Sarvam the equivalent is "tool result → returned text that the LLM treats as a directive" or "tool sets variable → state instructions reference the variable."
- Voice changes on Vapi happen only *by switching assistant* (a squad handoff). On a platform where the voice is fixed per call, persona has to be carried by wording, pacing words, length and register, not by timbre.

### Gaps
- I did not fetch Vapi's Live Call Control `add-message` and `say` control types or the `assistant-request` server-message timeout. I believe from training knowledge that `assistant-request` must answer within a few seconds at call start, but this is unverified. Vapi has no documented built-in per-turn sentiment signal that I verified.

---

## Q3. ElevenLabs Agents: workflows, multi-voice, language

### Takeaway
ElevenLabs has the richest *documented* mid-call voice adaptation of the platforms checked. **Workflow subagent nodes** can override the system prompt, LLM, voice (speed, tone, or a different voice), knowledge base and tools. Edges can be LLM conditions or deterministic expressions. **Multi-voice** lets the LLM switch voice per segment with XML tags, and only the first use of each voice adds latency.

### Cited Findings
- Workflow node types: Subagent, Say, Dispatch tool, Update state (assigns dynamic variables), Agent transfer, Transfer to number, End. — [ElevenLabs Agent Workflows](https://elevenlabs.io/docs/agents-platform/customization/agent-workflows)
- Subagent nodes can "append or override system instructions", switch LLM, change voice configuration ("adjust speed, tone, or switch voices entirely"), add node-specific knowledge base entries and tools. — [ElevenLabs Agent Workflows](https://elevenlabs.io/docs/agents-platform/customization/agent-workflows)
- Edge types: LLM conditions, expression-based deterministic conditions, unconditional. Dynamic variables are updated through the Update state tool and nodes. Language detection is listed as a system tool. Per-node analytics cover entries, duration and edge flow. — [ElevenLabs Agent Workflows](https://elevenlabs.io/docs/agents-platform/customization/agent-workflows)
- Multi-voice: `<VOICE_LABEL>text</VOICE_LABEL>` tags chosen by the LLM. Up to 10 voices per agent. Nested tags are not supported. Unknown labels fall back to the default voice. "Voice switching adds minimal overhead. The first use of each voice in a conversation may have slightly higher latency." — [ElevenLabs multi-voice support](https://elevenlabs.io/docs/agents-platform/customization/voice/multi-voice-support)

### Inferences
- The **"Update state node/tool → expression edge → subagent with overridden prompt"** chain is structurally the same as Sarvam's "tool sets variable → state transition → per-state instructions." It is the cleanest template to copy.
- Multi-voice tagging is evidence that **the LLM, not external code, can be the switch**, as long as the options are enumerated in the prompt. The same idea works for persona registers on Sarvam: "respond in register FAST / WARM / FORMAL as indicated by `{{persona_mode}}`."

### Gaps
- I did not fetch the language-detection system tool page, so its trigger semantics and latency are unverified. I found no ElevenLabs page quantifying subagent-transition latency.

---

## Q4. LiveKit Agents: handoffs, runtime updates, per-turn hooks, Jev plugin

### Takeaway
LiveKit gives full code-level control. `on_user_turn_completed` runs after each user turn and before the reply, and can inject temporary or persistent context or abort with `StopResponse`. Handoffs happen when a function tool returns a new `Agent`, and each agent can have its own TTS voice. `update_options()` swaps LLM or TTS without a handoff. The proposed TypeSafe Jev plugin (issue #7355) targets exactly the per-turn classification VANI wants. Its motivation is to avoid the "500–1500 ms" cost of an extra LLM call in `on_user_turn_completed`.

### Cited Findings
- In `on_user_turn_completed`, `turn_ctx.add_message()` adds messages for the current turn only. `await self.update_chat_ctx(turn_ctx)` persists them. Editing `new_message` persists. `raise StopResponse()` suppresses the reply. "Fast pre-response" pattern: call `self.session.say()` without awaiting, so a filler plays while the main reply generates. — [LiveKit pipeline nodes & hooks](https://docs.livekit.io/agents/build/nodes/)
- Handoff: return a different Agent from a tool, e.g. `return BillingAgent(chat_ctx=self.chat_ctx), "Transferring to billing"`. Each Agent can set its own `tts=`, `llm=`, `stt=` and `vad=`. `on_enter()` runs on activation. `chat_ctx.copy(exclude_instructions=True)` carries the turns without the old system prompt. `session.userdata` holds typed shared state. — [LiveKit agents & handoffs](https://docs.livekit.io/agents/logic/agents-handoffs/)
- "Python-only feature using `update_options()` on active agents to swap LLM/TTS without handoff". Realtime models cannot be replaced on an active agent and need a handoff. — [LiveKit agents & handoffs](https://docs.livekit.io/agents/logic/agents-handoffs/)
- Handoff costs "Handoff overhead per transition", so the docs consider it worse than supervisor or delegation patterns when switches are frequent. — [LiveKit workflows](https://docs.livekit.io/agents/build/workflows/)
- Issue #7355, "[Plugin] livekit-plugins-typesafe: per-turn decisions (routing, opt-out, escalation) with TypeSafe's Jev", opened 2026-09-19 by sidxh (not affiliated with TypeSafe):
  - Jev is a decision model released 2026-09-15 that evaluates several questions in parallel and returns typed answers: Choice (with a probability distribution), Score, or a binary yes/no. It does not generate text.
  - Proposed API: `typesafe.SystemOne().evaluate(state=typesafe.build_turn_state(turn_ctx, last_n=3), questions={...})`, called in `on_user_turn_completed` to avoid an extra LLM call costing "500–1500 ms".
  - It would not implement `llm.LLM`. The issue is shown as closed, with no maintainer response or linked PR, and Jev was early-access/waitlist at the time.
  — [livekit/agents#7355](https://github.com/livekit/agents/issues/7355)
- Training knowledge, unverified this session: LiveKit `Agent.update_instructions()` and `Agent.update_tools()` exist in Agents 1.x, and many TTS plugins expose `tts.update_options(voice=..., speed=...)`. The fetched pages did not show them.

### Inferences
- The LiveKit idiom for VANI-style adaptation: run the classifier inside `on_user_turn_completed`, either awaited (adds ~100 ms with Jev) or fire-and-forget. Write the result to `userdata`, then add an ephemeral system message such as "caller is rushed: answer in ≤12 words" for *this* turn. Change persistent instructions only when the hysteresis threshold is crossed.
- Sarvam lacks an `on_user_turn_completed` hook, so the classifier can only enter the turn through an LLM tool call. That makes it serial (LLM → tool → LLM) unless the signal is consumed on the *next* turn. See Q7.

### Gaps
- No public benchmark of LiveKit handoff overhead in milliseconds was found. The Jev ~108 ms p50 figure comes from the brief; issue #7355 did not restate it.

---

## Q5. Pipecat + Pipecat Flows

### Takeaway
Pipecat is the most explicit about **out-of-band setting changes**. Pushing a `TTSUpdateSettingsFrame` (or the LLM/STT equivalents) changes voice or speed mid-conversation. These frames are *uninterruptible*. Pipecat Flows is a node graph in which each node focuses the LLM on a single task with only the tools it needs, and node transitions are triggered by function calls.

### Cited Findings
- To change settings at runtime, push an `*UpdateSettingsFrame`. `TTSUpdateSettingsFrame(delta=Service.Settings(speed=1.2))` changes voice or speed. Only the specified fields change. "Update settings frames are uninterruptible and will always be processed even if a user interruption occurs." — [Pipecat service settings](https://docs.pipecat.ai/guides/fundamentals/service-settings)
- Flows: "a graph of nodes, where each node focuses the LLM on a single task with only the tools it needs". Flows are declarative (YAML/JSON) or programmatic (`NodeConfig`), and handlers are the Python that runs when a tool is called. — [Pipecat Flows guide](https://docs.pipecat.ai/guides/features/pipecat-flows)
- Hume publishes a Pipecat integration. — [Hume Pipecat integration](https://dev.hume.ai/docs/integrations/pipecat)
- Training knowledge, unverified this session: Flows nodes have `role_messages` (persona) and `task_messages` (task). Context strategies are APPEND, RESET and RESET_WITH_SUMMARY. Nodes have `pre_actions` and `post_actions` (e.g. `tts_say`, `end_conversation`, custom). A transition happens when a tool handler returns the next node. Pipecat's `ParallelPipeline` can run a side branch (for example a sentiment classifier) next to the main LLM branch.

### Inferences
- The **role/task split** in Flows corresponds to Sarvam's per-state instructions: keep a stable "role" (the IndiaMART seller-success persona) and vary the "task/register" block per state.
- Changing speed through a frame has no Sarvam equivalent because voice is fixed per call. Speed has to be approximated through text: shorter sentences, fewer clauses, no preamble.

### Gaps
- I did not fetch the Flows API reference, so the context-strategy and action names above are training knowledge. I found no Pipecat-published latency numbers for transitions.

---

## Q6. Others: Hume EVI, OpenAI Realtime, Gemini Live, Bland, Synthflow, Ultravox

### Takeaway
Hume EVI is the only platform found that is natively emotion-aware: prosody features are fed into response generation. OpenAI Realtime allows **instruction updates at any time via `session.update`**, but the voice is locked after the first audio output. Lock-after-start voice, with freely mutable instructions, is the same constraint Sarvam has.

### Cited Findings
- Hume's speech prosody model measures "48 dimensions of emotional expression" from how something is said (pitch, pace, intensity). EVI runs over a WebSocket. — [Hume prosody model](https://dev.hume.ai/docs/expression-measurement/models/prosody); [Hume EVI docs](https://dev.hume.ai/docs/speech-to-speech-evi)
- Contrary Research reports that EVI 3 responds in under 300 ms, with a "practical latency … of 1.2 seconds" from end of user speech to reply. This is a secondary source. — [Contrary Research: Hume AI](https://research.contrary.com/company/hume-ai)
- OpenAI Realtime: "Most session properties can be updated at any time, except for the voice … after the model has responded with audio once during the session." Instructions can be changed with `session.update`. — [OpenAI Realtime conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)
- Training knowledge, unverified this session: per-response `instructions` can be passed in `response.create` in OpenAI Realtime. Gemini Live system instructions are set at session setup.

### Inferences
- The Realtime guide's statement "instructions mutable, voice locked after first audio" shows that the industry consensus for adapting persona mid-call is **instruction/register change, not voice change**. That is exactly what Sarvam can do.

### Gaps
- No primary-source documentation was gathered for Bland (pathways), Synthflow or Ultravox mid-call adaptation in this session. Budget limits were reached. These remain open.

---

## Q7. Latency patterns: parallel vs blocking, next-turn application, hysteresis, fillers, budgets

### Takeaway
Industry budgets target **≤800 ms voice-to-voice**, and the LLM is the largest and most variable slice. One serial tool call of about 300 ms pushes time-to-first-audio to around 1.1 s. A ~108 ms classifier is small enough to block on in code-level frameworks. On a platform where the LLM must call a tool, the dominant cost is the **second LLM round-trip**, not the classifier. So the proven pattern is to apply the signal on the *next* turn, plus hysteresis.

### Cited Findings
- Typical budget: STT 50–150 ms, LLM 200–400 ms, TTS time-to-first-byte (TTFB) 100–200 ms, network 20–80 ms, for under 800 ms total. A 300 ms tool call pushes time-to-first-audio (TTFA) to over 1,100 ms. Tools and retrieval should run in parallel with the LLM, not after it. — [Twig: 800 ms rule](https://www.twig.so/blog/voice-ai-agents-latency-budget-800ms); [Smallest.ai latency budget](https://smallest.ai/blog/designing-voice-assistants-stt-llm-tts-tools-and-latency-budget)
- Morph claims the LLM takes 350–1,000 ms of an ~800 ms budget. — [Morph: Voice Agent API and latency (2026)](https://www.morphllm.com/voice-agent-api)
- An extra LLM call for per-turn decisions costs "500–1500 ms" (the motivation for Jev). — [livekit/agents#7355](https://github.com/livekit/agents/issues/7355)
- Filler or pre-response: speak a short phrase without awaiting it while the main reply generates. — [LiveKit nodes](https://docs.livekit.io/agents/build/nodes/)
- Pipecat settings frames are uninterruptible, so a voice or speed change applies reliably even if the user barges in. — [Pipecat service settings](https://docs.pipecat.ai/guides/fundamentals/service-settings)
- LiveKit says handoffs carry per-transition overhead and are a poor fit for frequent switching. — [LiveKit workflows](https://docs.livekit.io/agents/build/workflows/)

### Inferences
These are design recommendations derived from the findings above. They are not documented by any one source.
1. **Next-turn application is the only cheap option on Sarvam.** If the LLM calls `get_signals` at the *start* of its turn, the sequence is LLM decides → tool (~108 ms + network) → LLM continues. That costs a full extra LLM time-to-first-token (TTFT), likely 300–700 ms. The alternative is to fold the classifier *into a tool the LLM already calls*, or to have the tool run asynchronously: the tool returns immediately and stores the signal in a variable that the next turn's state instructions read. That way the current turn pays almost nothing.
2. **Hysteresis or debounce.** Switch persona only when the signal persists, for example K = 2 consecutive turns, or score > 0.7 to enter and < 0.4 to exit. Every platform here treats a persona switch as a heavyweight event: a handoff or node change with overhead and context effects, per LiveKit and Vapi. Flapping between states also resets the per-state prompt the LLM conditions on.
3. **Prefer a register variable over a state change for minor shifts.** Use a `{{persona_mode}}` variable read inside one state's instructions for tone and length. Reserve state transitions for real phase changes (for example escalation or opt-out). This mirrors ElevenLabs "Update state" plus expression edges, and Retell's equation edges.
4. **Fillers.** Where the platform permits, let the LLM emit a short acknowledgement ("ji, samjha") before the tool call, so the tool latency is masked.

### Gaps
- No published measurement was found of how much latency a Sarvam tool call adds. It must be measured in the hackathon environment.

---

## Q8. Evidence that mid-call adaptation improves outcomes

### Takeaway
I found **no rigorous, primary-source A/B evidence** that real-time sentiment-driven persona switching improves conversion, CSAT or call length. The numbers in circulation come from vendor or aggregator marketing without methodology.

### Cited Findings
- Claim: companies using sentiment analysis in voice agents see "25% higher conversion", "25–35% CSAT improvement" and "30–40% cost reduction." No study is cited, so treat this as marketing. — [Sobot article](https://www.sobot.io/article/ai-voice-agents-mimic-human-interaction-customer-support/)
- Claim: "36% higher meeting conversion" for personalized AI calls. This is a vendor playbook, not about mid-call adaptation specifically. — [Darwin AI blog](https://blog.getdarwin.ai/en/ai-voice-agents-b2b-sales-2026)
- A Forrester 2026 prediction (90%+ CSAT on routine interactions) is cited second-hand. — [JustCall blog](https://justcall.io/blog/ai-voice-agent-personalization.html)
- SquadStack (Indian voice-AI vendor) has a "Lift" self-improvement layer. This is relevant context for Indian outbound calling, but I did not verify any outcome figures. — [SquadStack Lift](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)

### Inferences
- VANI should treat the uplift as a hypothesis and instrument it: log the per-turn signal, the persona_mode, hang-up turn and outcome. A hackathon demo can show *behavioural* change, such as shorter replies when the caller is rushed, more credibly than an outcome lift.

### Gaps
- No peer-reviewed or independently audited study was found on dynamic persona switching in voice agents.

---

## Q9. Which patterns work when only the LLM decides when to call tools (Sarvam)

### Takeaway
Of the patterns surveyed, those that transfer are: (1) a **variable-gated register** inside state instructions (ElevenLabs Update-state, Retell equation edges); (2) **tool results as directives**, the equivalent of Vapi `message.add`; (3) **classification piggy-backed on tools the LLM must call anyway**, applied next-turn; and (4) **state-entry or on-start setup** of a baseline persona. Patterns that need out-of-band control will not transfer: Pipecat frames, LiveKit `on_user_turn_completed`, Retell `update_agent` and `agent_interrupt`, and voice or speed changes.

### Cited Findings (mechanism precedents)
- Retell: deterministic equation transitions over dynamic variables, plus extract-variable nodes. — [Retell transitions](https://docs.retellai.com/build/conversation-flow/transition-condition)
- ElevenLabs: Update-state tool/node sets dynamic variables, expression edges route, and subagents override the prompt. — [ElevenLabs workflows](https://elevenlabs.io/docs/agents-platform/customization/agent-workflows)
- Vapi: injected system messages change LLM behaviour "for the remainder of the call." — [Vapi hooks](https://docs.vapi.ai/assistants/assistant-hooks)
- ElevenLabs multi-voice: the LLM reliably picks among enumerated options when they are listed in the system prompt. — [ElevenLabs multi-voice](https://elevenlabs.io/docs/agents-platform/customization/voice/multi-voice-support)
- LiveKit handoff via a tool returning an Agent: the LLM decides the switch by calling a tool. — [LiveKit handoffs](https://docs.livekit.io/agents/logic/agents-handoffs/)

### Inferences (mapping to Sarvam; all are design proposals)
| Peer pattern | Sarvam mapping | Latency on the current turn |
|---|---|---|
| Retell equation edge / ElevenLabs expression edge | Tool `report_turn(signal...)` sets `persona_mode`. The state's instructions contain conditional blocks that reference `{{persona_mode}}`, or a transition fires when the variable changes. | Pays one tool round-trip if called before speaking. ~0 if the signal applies next turn. |
| Vapi `message.add` | The tool returns natural-language guidance (for example "Caller rushed (p=0.82). Next reply ≤15 words, skip pleasantries."). The LLM reads it as a directive. | Same as above. |
| LiveKit `on_user_turn_completed` + Jev | Not directly possible. Approximate it by putting "ALWAYS call `assess_turn` first, every turn" in every state's instructions. Expect imperfect compliance and an extra LLM round-trip (~300–700 ms estimated). | High, so make the tool fast and the output short. |
| Next-turn application | Have the classifier run inside tools the LLM already calls (for example `lookup_lead`, `log_answer`), or make `assess_turn` fire-and-forget so it returns "ok" instantly while the result lands in a variable. | Lowest. |
| Hysteresis | Compute it server-side inside the tool. Keep counters in variables and change `persona_mode` only after K turns or when a threshold is crossed. Never let the LLM decide the flip. | None. |
| Handoff to a specialised agent | A Sarvam state transition only for real phase changes (escalation, opt-out, language switch). Not for tone. | State change overhead, unmeasured. |
| On-start persona seeding (Vapi `assistant-request` style) | On-start hook fetches seller profile (tenure, prior calls, language) → initial `persona_mode` and language. | Before the first turn, so the user does not feel it. |
| Voice or speed change (Pipecat frame, ElevenLabs subagent voice) | Not available because voice is fixed. Emulate it with text: sentence length, Hinglish vs. formal Hindi register, no filler, number formatting. | None. |

### Gaps
- It is unknown whether Sarvam tools can be asynchronous or fire-and-forget, or whether tool results can update variables that the *current* state's instructions re-render on the next turn. This needs verification against Sarvam docs. It is the key feasibility question.
- How reliably the LLM complies with "call X every turn" instructions on Sarvam has not been measured. Peer platforms avoid relying on this by using deterministic hooks.
