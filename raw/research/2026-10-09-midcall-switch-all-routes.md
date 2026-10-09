# Mid-call persona switching on a real phone call: all routes, plus Jev key safety (2026-10-09)

Desk research only. Nothing on the Sarvam agent or console was changed. No keys were printed. No PII.

Builds on (not repeated here):
- `raw/research/2026-10-09-sarvam-native-midcall-switching.md` (Sarvam capability table, tests T1 to T10)
- `raw/research/2026-10-09-jev-midcall-options.md` (Jev shape, latency, allowlist cause, bridge options A to J)
- `raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md` (signals: frustration, confusion, interest, language switch, rush; 25% of the score is "correct, well-timed mid-call switches")

Tags:
- **PROVEN** = we ran it.
- **DOCUMENTED** = vendor docs, or seen in the Sarvam SDK source or console config schema.
- **ASSUMED** = inference, not tested.

New sources read today:
- Sarvam docs (`.md` pages): code-tools, settings/secrets, https-tool, call-transfer, conversation-settings, mcp, tests, telephony (index, bring-your-own, exotel, vobiz), deployments webhook payload, api/getting-started (pricing, ratelimits), platform/organisations-and-workspaces, text-processing/language-detection.
- Sarvam SDK 1.1.1 README "Secrets" section, and `tool.py` (`SarvamToolBaseContext.secrets` / `get_secret`).
- IndiaMART internal API-docs assistant (two questions about telephony).
- TypeSafe docs (`docs.typesafe.ai/llms-full.txt`: Models, API errors, Quick start).
- OpenRouter docs: authentication, security-settings, guardrails, management-api-keys, api-key-rotation.
- LiteLLM docs: TypeSafe pass-through, virtual keys.
- Third-party notes on Jev access: flaviocopes.com/jev-api-key, opentweet.io/jev/limits.
- LiveKit Sarvam plugin pages; Asterisk WebSocket channel driver; FreeSWITCH media-streaming modules.

## Headline

1. **No route lets our own code see every seller turn on a Sarvam-hosted phone call without the Sarvam LLM first choosing to call a tool.** Sarvam has no per-turn hook and no forced tool call (earlier note). The exceptions:
   - Sarvam's built-in language switch.
   - Two push channels that are still unproven: Webhook Variable Update (O3), and the client push (O4), which works only on SDK sessions.
2. **To get our code into every turn, we must own the audio path (O16 / O17).** On today's evidence that is blocked by telephony, not by Sarvam:
   - IndiaMART's click-to-call stack uses Knowlarity and Airtel. It has no SIP or audio-bridge API, and neither vendor is on Sarvam's bring-your-own list.
   - Sarvam does not document a generic SIP trunk.
3. **The cleanest new in-rules classifier is a Sarvam model called from the code tool (O6, O7).**
   - Same vendor, a public endpoint, and no IP allowlist.
   - It needs a Sarvam Model-API key as a workspace secret.
   - Latency is unmeasured.
4. **The only true mid-call voice change found on a phone call is a call transfer to a second Sarvam agent (O15).** It is a hack: there is ringing, and context must be handed over.
5. **Key safety.** A Sarvam secret is not shown to the seller, the LLM or the logs, unless our code puts it there. But any workspace Editor can read it with a tool of their own. So:
   - give Sarvam only a key that is worth little (capped, model-locked, expiring); or
   - keep the key on our side (relay or LiteLLM gateway).
   - Do not buy a direct TypeSafe subscription for this: it would be a new outside vendor, and its keys have no documented limits.

## Table: all routes

"Who decides" means who makes the switch decision. "LLM triggers" means the Sarvam LLM must still choose to call the tool, and that is the residual risk on every in-Sarvam route.

"When" values:
- **Same turn** = the reply that answers the triggering utterance already uses the new persona.
- **Next turn** = the reply after that.

| # | Route | How it works, end to end | Who decides | When | Added latency per turn | Phone call? | What is needed | Risks | Evidence | Tag |
|---|---|---|---|---|---|---|---|---|---|---|
| O1 | Prompt-only adaptation + built-in language switch (listed) | The persona prompt tells the LLM how to change delivery for each signal. Sarvam LID / smart switch changes the language. | Sarvam LLM; Sarvam LID for language | Same turn | 0 | Yes | Nothing new | Not deterministic; no code-written switch log (only post-call extraction); LLM may over- or under-switch | 2026-10-09-sarvam-native-midcall-switching.md (LID 6/6, 2/2); midcall-pace-lang-switchlog.md | PROVEN (language); ASSUMED (others) |
| O1b | Pre-compiled per-seller switch playbook (refines O1) | OnStart writes five ready-made directive variables (rushed / frustrated / confused / interested / language) for this seller. The prompt says "when you notice X, follow `@directive_X`". The LLM only picks among blocks we wrote. | Sarvam LLM picks; our code wrote the blocks | Same turn | 0 | Yes (OnStart and variables work on phone, ASSUMED until a phone call is made) | OnStart code tool (have it) | Still LLM judgement; prompt grows by about 5 short blocks | onstart-code-tool-spike.md; onstart-pace-and-phone-check.md | PROVEN (OnStart variables); ASSUMED (switch quality) |
| O1c | Built-in `update_variables` tool | Turn on `allow_mid_call_variable_update` and mark `seller_mode` as agent-updatable. The LLM writes the mode itself, which gives a logged variable change. | Sarvam LLM | Same turn (ASSUMED) | One LLM tool step | Yes | Config change (off today) | LLM judgement, so it breaks the "frozen classifier decides" rule | Schema `$BaseAgentConfig` (earlier note) | DOCUMENTED |
| O2 | Code tool with keyword list (listed, current) | The LLM calls `read_seller_signal(utterance)`. Python matches the lexicon and sets `persona_directive` / `change_language`. | Our code; LLM triggers | Same turn | ~0.07 ms + the tool-call LLM step | Yes | Nothing | Misses phrases (e.g. "phir se ... warna phone rakh do"); false positives; tool skipped on some turns | jev-midcall-options.md (F) | PROVEN |
| O2b | Code tool calls Jev on OpenRouter directly (listed) | Same as O2, but the tool sends an `httpx` POST to OpenRouter Decisions with the key from `context.get_secret`. | Jev; LLM triggers | Same turn | ~0.5 s p50, ~1 s p95 | Yes, if allowlisted | Add 4.213.167.70 to the OpenRouter IP allowlist (org-wide, Enterprise feature); key as Sarvam secret | Allowlisting a shared Sarvam IP covers **every** IndiaMART OpenRouter key; latency over budget; see key safety | jev-midcall-options.md (A); OpenRouter security-settings | PROVEN (cause); ASSUMED (latency from Sarvam) |
| O2c | Code tool calls Jev through a laptop relay tunnel (listed) | The tool posts the utterance to a tunnel URL. The relay on the VPN laptop calls Jev with the key it holds. | Jev; LLM triggers | Same turn | O2b + 20 to 100 ms | Yes | Laptop + VPN up; tunnel (URL changes on restart) | Demo depends on the laptop; tunnel died once | jev-midcall-options.md (C, D) | PROVEN (tunnel works once, died once) |
| O3 | Jev on laptop pushes variables via Webhook Variable Update (listed) | Our host gets each turn from somewhere, classifies it, and pushes `persona_directive` into the live call. | Our classifier; no LLM tool call | Next turn | Off the reply path | Unknown | Inbound endpoint and payload unknown (docs page 404); also needs a per-turn feed, and none exists for phone calls | Unknown whether it works mid-call at all; no per-turn event feed on phone, so "turn N" must come from O5's transcript POSTs | sarvam-native-midcall-switching.md (T2) | ASSUMED |
| O4 | Laptop pushes state or language by client action (listed) | `client.action.variable_update` / `state_transition` / `language_change` frames over the SDK WebSocket. | Our classifier | Next turn | Off the reply path | **No** on Sarvam-hosted telephony. Only on an SDK session, i.e. only with O16 | SDK session; frame format unproven (another agent is testing T1 now) | Undocumented; message classes missing from the wheel | sarvam-native-midcall-switching.md (T1) | ASSUMED |
| O5 | API (HTTP) tool with `@Call Transcript`, no LLM-filled arguments | Instead of a code tool, an API tool whose body is `@Call Transcript` + `@Interaction ID`. It is called with no arguments, so the LLM need not copy the utterance. Our relay classifies the last user turn and returns the directive, which is mapped into variables ("Save reply into variables"). | Our relay's classifier (lexicon, distilled model or Jev); LLM triggers | Same turn | Tool LLM step + hop + classifier (relay 20 to 100 ms; Jev +0.5 s) | Yes | Public HTTPS relay reachable from 4.213.167.70. The tool URL may not resolve to a private IP: Sarvam refuses those | Same hosting risk as O2c; earlier spike moved away from API tools because of the extra LLM step | https-tool docs (call-context variables, egress IP); mcp docs (network safety); jev-midcall-options.md (E) | DOCUMENTED; PROVEN (API tool to relay, spike 2/3) |
| O6 | Code tool calls a **Sarvam LLM** as the classifier | The tool sends the utterance + a fixed classification prompt to Sarvam Chat Completions (`sarvam-105b`, or an open-weight model Sarvam serves, e.g. Gemma 4 31B / DeepSeek V4.1 Flash), using structured output, low reasoning effort and `max_tokens` small. Code maps the label to the directive. | Sarvam model with a frozen prompt; LLM triggers | Same turn | Unmeasured. ASSUMED 0.4 to 1.5 s (`sarvam-105b` is a reasoning model) | Yes (api.sarvam.ai is public; no allowlist) | Sarvam Model-API key as workspace secret; credits (`sarvam-105b` ₹29.28 input / ₹73.2 output per M tokens); LLM rate limit 60 req/min on Starter, per account | Latency may exceed budget; all keys in an org share one credit balance and Sarvam has **no per-key budget**; a "frozen" LLM prompt is less stable than Jev | Sarvam pricing, ratelimits, openweight, organisations-and-workspaces | DOCUMENTED; latency ASSUMED |
| O7 | Code tool calls **Sarvam Language Identification** API | The tool sends the utterance text to `text/identify-language` and gets back language + script. If it differs from `get_current_language()`, it calls `change_language`. Covers the language signal only. | Sarvam LID model + our code; LLM triggers | Same turn | ASSUMED 0.1 to 0.3 s | Yes | Sarvam Model-API key as secret | Duplicates the built-in LID that already works; romanised Hindi may read as English | Sarvam language-detection docs; pricing page lists "Language Identification" | DOCUMENTED |
| O8 | Code tool calls the **internal LiteLLM gateway** (a chat model, or the TypeSafe pass-through) | Like O2b / O6, but the target is `imllm.intermesh.net` with a LiteLLM virtual key. | Gateway-served model or Jev; LLM triggers | Same turn | As O2b (Jev) or O6 (chat), plus the gateway hop | Yes, once opened | Gateway admin: enable `/typesafe` pass-through (404 today); unblock the path for 4.213.167.70 (403 today from outside IPs); a key with model access (today's key lacks Jev) | Depends on an admin; gateway reliability unknown | jev-midcall-options.md (B); LiteLLM pass-through docs | PROVEN (blocked today); DOCUMENTED (pass-through) |
| O9 | Distilled small classifier inside the code tool | Char n-gram logistic regression trained offline on Jev-labelled turns; weights inlined as a Python dict; no network. | Our frozen model; LLM triggers | Same turn | ASSUMED < 5 ms | Yes | Jev-labelled training set (VPN laptop route works) | Code-tool size and import limits are undocumented; quality is capped by the labels | jev-midcall-options.md (G, section 4) | ASSUMED |
| O10 | Hybrid gate (O2/O9 first, remote model on ambiguous turns only) | Local classifier decides at once. Only turns that are long or contain risky tokens call Jev / Sarvam LLM, with a hard ~400 ms timeout; on timeout the local result stands. | Local first, remote can veto or add | Same turn | 0 on most turns; ≤ 400 ms on gated turns | Yes | One remote route unblocked (O2b, O6 or O8) | Gate tuning; still needs the LLM to call the tool | jev-midcall-options.md (section 3) | ASSUMED |
| O11 | Multi-state flow, transitions set by code | One state per mode, each with its own instruction block. The classifier tool calls `context.change_state(mode)`. | Our code; LLM triggers | Unknown whether same turn or next (T5) | Same as the tool | Yes | Config write via API or MCP (the convert option sits under Advanced; Sarvam calls multi-state an older paradigm, end-of-life once multi-agent ships) | One-way conversion; legacy feature; prompt swap timing unknown | conversation-settings docs (Advanced, "one-way"); SDK `change_state`; earlier note | DOCUMENTED |
| O11b | Multi-state flow, transitions judged by the LLM | `next_states` with prose conditions ("if the seller sounds rushed"). The LLM chooses the transition. | Sarvam LLM | Unknown | 0 | Yes | Same config write | LLM judgement (breaks the frozen-classifier rule) | Schema `$NextState{name, condition}` | DOCUMENTED |
| O12 | Language-tied voice change (mixed speaker / per-language voice settings) | Config sets a different speaker, pace or pitch per language. When the call switches language, the voice changes with it. | Whoever switches the language (LID or our tool) | Same turn (ASSUMED) | 0 | Yes (ASSUMED) | Config write (`enable_mixed_speaker_settings`, `mixed_speaker_config`, `language_voice_settings_mapping`); the UI forces it off | Only expresses "voice per language", not "calmer voice in the same language"; untested (T6) | Console schema (earlier note); docs say per-language voices stay fixed for the call | ASSUMED |
| O13 | Silence nudges, including a tool-type nudge | After N seconds of silence, speak a nudge, or run a tool (`nudge_type: "tool"`) with no LLM choice. Useful for "confused / gone quiet", not for words. | Timer; our tool if tool-type | On silence only | 0 | Yes | Nudge config (text nudges documented; tool type seen in console code only) | Covers silence only; tool-type unproven (T8) | conversation-settings docs ("Nudge quiet callers"); earlier note | DOCUMENTED (text) / ASSUMED (tool) |
| O14 | Verbatim delivery from the tool (`message_to_user`, `pre_run_message`) | When the classifier fires, the tool returns the exact short line to speak (e.g. a 10-word rushed pitch with comma pacing), so the LLM cannot paraphrase it. This is an applier that pairs with any detector above. | Our code; LLM triggers | Same turn | 0 | Yes | Nothing | Lines must be pre-written per language; sounds scripted if overused | SDK `SarvamToolOutput` (earlier note) | DOCUMENTED |
| O15 | Call transfer to a second Sarvam agent with a different voice | The classifier sets a `transfer_target` variable. The LLM calls the core `call_transfer` tool. The call is bridged to another Sarvam agent's inbound number (or SIP URI) whose voice and pace are the new persona. That agent's on-start hook fetches the context (by caller number or a relay key). | Our code picks the target; LLM triggers the transfer | Several seconds later (ringing + new greeting) | ASSUMED 3 to 8 s gap | Yes, phone only | A telephony connection with self-serve transfer: Vobiz or Plivo (Rent from Sarvam = Vobiz, needs KYC); a second agent + inbound deployment; context handoff | Audible gap and re-greeting; doubles call minutes; context loss; the seller may hear ringing. A one-shot hack, not a live adaptation loop | call-transfer docs; onstart-pace-and-phone-check.md (no telephony connection today) | DOCUMENTED (transfer); ASSUMED (as a persona switch) |
| O16 | **Own the phone leg**: open-source PBX bridged to a Sarvam SDK session | PSTN ↔ SIP trunk ↔ Asterisk (WebSocket channel driver / AudioSocket) or FreeSWITCH (WebSocket media module) or LiveKit SIP ↔ our bridge ↔ Sarvam Python SDK session in call mode (16 kHz PCM). The bridge sees every user and bot transcript and the `user_interrupt` events. It can also measure audio features (speech rate, loudness, barge-in count) for rushed / frustrated. It applies switches by O4 (client push), O3 or O16b. | Our classifier on every turn, with no LLM choice | Next turn (push), or same turn if our tool still runs inside | Classifier off the reply path; the bridge adds ~10 to 50 ms audio hop (ASSUMED) | Yes, if we get a trunk | A SIP trunk or PSTN gateway from IndiaMART telephony. IndiaMART's click-to-call uses **Knowlarity and Airtel** (single-leg); no SIP or audio-bridge API is documented. A new trunk vendor is not allowed. Plus a public host (Daytona has no inbound DNS yet) | Biggest build; telephony team dependency; push channel (O4) unproven; loses Sarvam's phone analytics | Internal API docs (Dialer Service, C2C Inhouse; repo `click-to-call` adapters for Knowlarity and Airtel); Sarvam BYO page (Exotel, Twilio, Smartflo, Pulse, Intalk, Vobiz, Plivo; no generic SIP); Asterisk chan_websocket docs; SDK `transcript_callback` | DOCUMENTED (parts); ASSUMED (as a whole) |
| O16b | Session hot-swap on our own leg | On a switch, the bridge closes Sarvam session A and opens session B with a new `text_to_speech_config` (speaker, pace, pitch) and a short summary in agent variables, then keeps piping audio. The only route to a **real mid-call voice change in the same language**. | Our classifier | Next turn, after a gap | ASSUMED 1 to 2 s (new signed URL + connect + no greeting) | Yes, with O16 | O16 + `initial_bot_message` empty or a bridging line | Audible pause; context only as rich as the summary; each WebSocket URL is single-use | SDK session-start overrides; web SDK docs ("each WebSocket URL is single-use") | ASSUMED |
| O17 | Own pipeline on Sarvam models (LiveKit Agents or Pipecat + Saaras STT + Sarvam-105B + Bulbul TTS) | We run the turn loop ourselves: every turn passes through our code; TTS speaker or pace can change per sentence; any classifier runs before the LLM. Phone leg as in O16. | Our code, every turn | Same turn | Classifier only; but we own all pipeline latency | Yes, with O16's trunk | Sarvam Model-API key; open-source framework (LiveKit `livekit-plugins-sarvam` has STT, TTS and LLM); trunk as O16 | **Rule risk**: the deck wants "the demo on Sarvam". This uses Sarvam models but not the Sarvam Voice Agent platform, so judges may not count it; we rebuild turn-taking, barge-in and analytics | LiveKit Sarvam plugin docs; Sarvam pipecat guide (earlier note) | DOCUMENTED (parts); ASSUMED (eligibility) |
| O18 | Sarvam Tests (simulated user + AI judge) | Not live. Write test cases per signal ("seller says he is busy at turn 3"); expected behaviours such as "next reply ≤ 12 words"; run against a committed version; read pass/fail. | n/a (evaluation) | Between runs | n/a | n/a (simulated) | Tests tab or MCP `run_eval` | AI judge noise; simulated speech is not real ASR | tests docs; mcp docs (Evals) | DOCUMENTED |
| O19 | Sarvam MCP server | Not live. Authoring and operations plane: `configure_agent` (states, mixed speaker, nudges), commit versions, `run_eval`, analytics traces. Calls always run a committed version, so a live call cannot be steered. A tool URL resolving to a private IP is refused. | n/a | Between runs | n/a | n/a | OAuth via Sarvam SSO (24 h token) | Equivalent to a programmatic operator: reads transcripts and prompts | mcp docs | DOCUMENTED |
| O20 | Jev between runs (gold labels, relabel switch_log, tune lexicon and thresholds) | Already covered: H, I, J in the Jev note. | Jev offline | Between runs | n/a | n/a | VPN laptop | Overfitting a small set | jev-midcall-options.md | PROVEN (route) |

Considered and dropped:
- **Two parallel Sarvam sessions (one per persona) with our bridge muting one.** Each session's history diverges from what the seller actually heard. ASSUMED.
- **Audio or prosody features inside a Sarvam code tool.** The tool context has no audio, only variables. DOCUMENTED (absence in SDK context).
- **An LLM helper inside the code tool.** The context exposes no LLM call, only variables, secrets, language, state, end-call and metadata. Any model call has to be an outbound HTTP call (O6, O8). DOCUMENTED (absence).
- **A Sarvam text-classification or sentiment API.** None exists. The Text Processing APIs are translate, transliterate and language identification. Classification must use Chat Completions (O6). DOCUMENTED (absence).
- **Agent versions per persona chosen per call.** This is a pre-call choice, not a mid-call one. It is already covered by OnStart.

### Shortlist (for the later decision, not a decision)

- **Today, no admin needed:**
  - O1b + O2 (later O9) + O14, with language left to Sarvam LID.
  - Every switch is written to the switch log by our code.
- **One step up, still all-Sarvam:**
  - O10 with O6 as the remote model.
  - Measure p95 from inside a code tool before relying on it.
- **If an admin helps:**
  - O8 (LiteLLM gateway for Jev) is the cleanest Jev route.
  - O2b needs the org-wide OpenRouter allowlist change; see the warning below.
- **Real voice change mid-call:**
  - Only O15 (phone hack) or O16b (needs our own phone leg).
  - Both are high risk for the hackathon window.

## Key safety

### What happens to a secret in a Sarvam code tool (DOCUMENTED unless marked)

- **Where it lives.** Secrets are created under Settings → Secrets. Each is "scoped to the workspace", so every tool in that workspace can reference it by name (SDK README).
  - On upload, the platform scans the tool for secret names and rejects names that do not exist.
  - At runtime the value is "resolved fresh for each session and passed to your tool only in memory". In the SDK it is a plain `secrets: Dict[str, str]` on the context (`tool.py`).
- **Not in the LLM context, the transcript or the logs by default.** The README says secret values "never appear in your tool file or logs". The LLM sees only what we return in `message_to_llm` / `message_to_user`, agent variables and tool arguments.
  - So the key leaks to the LLM, the seller or the Log Analyser only if our code puts it there. That means returning it, storing it in a variable, `print()`-ing it (print output appears in the debug chat), or raising an exception that carries it.
- **API tools** take credentials through a masked input. The value is stored as a workspace secret and never in the tool config (https-tool docs).
- **Who can read it:**
  1. Sarvam's runtime (vendor trust, the same as for call audio).
  2. **Any workspace member who can upload a tool** (Editor or Admin role). They can write a tool that sends the secret anywhere. This is the real exposure.
  - Whether the Secrets page re-displays a saved value is not documented (ASSUMED masked).
  - Viewers are read-only.
- **The egress IP 4.213.167.70 is shared by all Sarvam customers.** OpenRouter's IP allowlist is account- or org-wide (Enterprise feature, all keys). Adding this IP lets *any* IndiaMART OpenRouter key be used from *any* Sarvam tenant's tool. The allowlist then stops being a second factor for all our keys, not just the Jev key.

**Answer to "will our key be exposed or compromised?"** Not to the seller, the LLM or the call logs, provided the tool never prints, returns or stores it. It is exposed to everyone with Editor rights in that Sarvam workspace, and to Sarvam itself. A leak is unlikely but possible. So the key we put there must be cheap to lose: capped, locked to one model, expiring and revocable. Or the real key should stay on our side.

### What each provider lets us restrict

| Control | TypeSafe direct | OpenRouter | Internal LiteLLM gateway | Sarvam Model-API key (for O6/O7) |
|---|---|---|---|---|
| Key creation | console.typesafe.ai keys page (DOCUMENTED). Third-party notes: direct access waitlisted since 2026-09-15 and signups paused ~2026-09-22 (ASSUMED current) | Per key, with name, credit limit and expiry (DOCUMENTED) | Virtual keys via `/key/generate` by an admin (DOCUMENTED) | Per workspace (DOCUMENTED) |
| Spend cap | None documented | Per-key credit limit with daily/weekly/monthly reset; guardrail budgets per key and per member, lower one wins (DOCUMENTED) | `max_budget` + `budget_duration` per key; spend tracked for TypeSafe pass-through (DOCUMENTED) | **None per key**: one credit balance per organisation (DOCUMENTED) |
| Model lock | n/a (only Jev) | Guardrail model allowlist and provider allowlist (DOCUMENTED); whether it binds the alpha Decisions endpoint is ASSUMED, so test it | `models` list per key (DOCUMENTED) | No |
| Rate limit | 80 req/s, 100K tokens/s, "adjusting dynamically" (DOCUMENTED) | No Decisions-specific limit published | `rpm_limit` / `tpm_limit` per key (DOCUMENTED) | Per account, e.g. LLM 60 req/min Starter (DOCUMENTED) |
| Expiry / rotation | None documented | Expiry fixed at creation; disable (reversible) or archive; management keys automate rotation; org can enforce a maximum key lifetime (DOCUMENTED) | `duration` expiry, `/key/block`, `/key/regenerate`, auto-rotate (DOCUMENTED) | Revoke and recreate (DOCUMENTED); up to 50 active keys per org |
| IP allowlist | None documented | Org-wide, Enterprise only, applies to all keys (DOCUMENTED; ours is on, PROVEN by the 403) | Load balancer blocks outside IPs on the pass-through path today (PROVEN); per-key IP rules not checked | None documented |
| Leak detection | None documented | GitHub secret-scanning partner; emails on exposure (DOCUMENTED) | n/a | Not checked |

Price context for a leaked unlimited TypeSafe key: at the documented 100K tokens/s × $0.042 per million tokens, the worst case is about $15 per hour (arithmetic, ASSUMED sustained).

**Rule check.** A direct TypeSafe subscription would be a **new outside vendor**, which AGENTS.md forbids. Jev is allowed today only because it comes through OpenRouter (and possibly the internal gateway). So "the TypeSafe subscription" is not a route for us. Use Jev through OpenRouter or LiteLLM.

### Recommended setup for each of the three options

**1. Dedicated limited key stored as a Sarvam secret** (fastest; blocked until the allowlist question is settled)
- Key type:
  - Create a **new OpenRouter key used only by this tool**, not a TypeSafe key and not a shared team key.
  - Credit limit about $2 to $5 with **daily reset**.
  - Expiry = hackathon end + 1 day.
  - Attach a guardrail whose model allowlist is `typesafe/jev-1.13` only. Test that a chat model call with this key is refused.
- Storage: put it in Settings → Secrets as e.g. `JEV_TOOL_KEY`.
- In the tool:
  - Never `print`, return or store it.
  - Send it only in the `Authorization` header, never in a URL.
  - Wrap the call in `try/except` and return a generic "classifier unavailable" so exceptions cannot echo request details.
  - Use a 400 ms timeout.
- Access: keep Editor rights in that Sarvam workspace to the core team. Disable the key after the event.
- Residual risk:
  - Readable by workspace Editors.
  - Needs 4.213.167.70 on the **org-wide** OpenRouter allowlist, which weakens the allowlist for every IndiaMART key. Ask the owner explicitly about that trade-off.
  - A leak costs at most the daily cap.

**2. Relay, so the real key never leaves our side** (safest for the key; weakest for uptime)
- The relay (laptop on VPN, or Daytona once it has inbound DNS) holds the OpenRouter key. The VPN egress is already allowlisted.
- What the tool sends: only the latest utterance (plus language), the interaction ID, a timestamp, and an **HMAC signature**.
  - Signature = HMAC-SHA256 over body + timestamp, keyed by a relay signing secret stored in Sarvam Secrets.
  - Prefer the HMAC over a bearer "short-lived token": the tool cannot fetch fresh tokens without another secret, while the HMAC secret itself never travels.
- What the relay enforces:
  - rejects requests older than ~30 s or replayed;
  - accepts only from 4.213.167.70;
  - runs only our fixed 6-question set (it is not a general Jev proxy);
  - caps requests per minute;
  - logs aggregates only.
- If the Sarvam secret leaks, the attacker can only ask "classify this sentence" through our capped relay. We rotate the signing secret in seconds without touching OpenRouter.
- Cost: one extra hop (20 to 100 ms) and all the hosting risk already measured (tunnel URL churn, laptop and VPN uptime).

**3. LiteLLM gateway virtual key with a budget** (best governance and best fit with "use IndiaMART infra"; needs an admin)
- Ask the gateway admin for four things:
  - (a) enable the `/typesafe` pass-through (LiteLLM adds the upstream TypeSafe or OpenRouter key from its own environment, so clients never see it);
  - (b) allow that path from 4.213.167.70;
  - (c) issue a virtual key with `models` = Jev only, `max_budget` a few dollars, `budget_duration` 1 day, `duration` = through the event, and `rpm_limit` ≈ 120;
  - (d) block the key after the event.
- Store the virtual key as a Sarvam secret, with the same tool hygiene as option 1.
- If it leaks, it buys only capped Jev calls and can be blocked centrally. The upstream key and the org-wide OpenRouter allowlist stay untouched.
- Note: if the gateway's own upstream is TypeSafe direct, that subscription must already be an IndiaMART-held account. Otherwise the gateway should forward to OpenRouter.

**Order of preference for safety:** 3 > 2 > 1.

**For speed:** 1 (if the allowlist owner agrees) > 3 (if the admin responds today) > 2.

**For an all-Sarvam classifier (O6/O7):** the same rules apply to the Sarvam Model-API key, with one difference. Sarvam has **no per-key budget**, so keep a separate workspace and key for the tool, keep org credits low, and revoke after the event.
