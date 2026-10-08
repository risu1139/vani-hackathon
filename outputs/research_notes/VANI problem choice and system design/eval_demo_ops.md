# Evaluation, demo and operations blocks: harness, trace/judges/dashboard, live demo, hosting, and reuse for #1 and #5

Research date: 2026-10-08. No customer data. Tags: **PROVEN** = observed in our own spikes ([[2026-10-07-spike-log]], `raw/research/2026-10-07-spike-log.md`); **DOCUMENTED** = stated in vendor/paper docs (cited); **ASSUMED** = our design inference, untested. Earlier notes this builds on: `outputs/research_notes/VANI adaptive persona architecture/simulation_eval_reuse.md` and `raw/research/2026-10-07-deep-research-vani-adaptive-persona-architecture.md`.

## 1. Block definitions with fixed roles and interfaces

### Takeaway
Five blocks, one data contract: every call (simulated, phone, browser, or historical) becomes a `Trace` JSONL record; judges add `Verdict` rows; an aggregator turns verdicts into paired-lift (#4), Fatal/root-cause queues (#1) or variant decisions (#5); one dashboard reads all of it. Only the call source and the aggregator change across problems. The harness and signal-server pieces exist as spike code (PROVEN); the judges, store and dashboard are not built yet (ASSUMED).

### Cited Findings
- PROVEN: `app/spike/call_spike.py` drives the agent in SDK CALL mode (version=1) with Sarvam TTS seller audio (bulbul:v3, speaker "rahul", 16 kHz PCM, 20 ms frames). It detects agent speech by RMS > 700 because background ambience streams constantly (p50 RMS ~300, speech p90 ~3,800), joins the signal-server `/log`, and measured tool calls on 12/12 + 6/6 + 6/6 seller turns, with median reply latency ~2.1 s (range 1.2–3.5 s) using the stub classifier — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: CHAT mode returns 404 "App not found for the interaction type"; only CALL mode works, so every simulated call is a voice call — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: the agent's "nudge quiet callers / hang up after unanswered nudges" setting ends a silent session, so the harness must keep talking — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: the tool receives seller words verbatim in Devanagari with ASR errors ("अब बोट हो क्या"), so cue matching needs Devanagari + NFD normalisation — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: the Python SDK exposes `transcript_callback` (user + agent speech), `audio_callback`, `event_callback` (interaction_connected, user_interrupt, interaction_end), `send_audio`, `get_interaction_id` — [Sarvam deploy/SDK docs check](../../../raw/research/2026-10-07-sarvam-deploy-sdk-docs-check.md)
- DOCUMENTED: SDK session config can override `text_to_speech_config{speaker, pitch, pace}`, `agent_variables`, `initial_language_name`, `version` per session — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: Sarvam Analytics API `GET https://apps.sarvam.ai/api/analytics/v1/{org_id}/{workspace_id}/{app_id}/interactions` (required `start_datetime`/`end_datetime`, `limit` default 20, `offset`, `filter_conditions`) returns per call `interaction_id, duration_in_seconds, language_name, num_messages, average_agent_response_time_in_seconds, average_user_response_time_in_seconds, is_debug_call, audio_url, failure_reason, ended_by, has_log_issues, agent_variables, channel_type…` — [Sarvam Interactions API](https://docs.sarvam.ai/conversations/api/analytics/interactions.md)
- DOCUMENTED: `GET …/transcripts/{interaction_id}` exists, but the docs page shows an empty example body; the turn schema is not documented — [Sarvam Transcripts API](https://docs.sarvam.ai/conversations/api/analytics/transcripts.md)

### Inferences (block contracts; all ASSUMED unless marked)
| Block | Fixed role | Inputs → outputs | Status |
|---|---|---|---|
| B1 `SellerSim` + `AgentClient` (harness) | Play one seller card against one agent arm, voice-to-voice | `PersonaCard{card_id, lang, code_mix, verbosity, events[{turn, type: rush/confused/lang_switch/bot_question, line}], hangup_rule, seed}` + `Arm{app_version, adapt: on/off, voice}` → raw `Trace` | Harness PROVEN for scripted lines; LLM-driven seller turns ASSUMED |
| B2 `TraceStore` | Append-only record of every call | `Trace{call_id, source: sim/phone/web/hist, card_id, seed, arm, app_version, turns[{role, text, lang, t_start, t_end}], tool_calls[{t, args, seller_mode, directive}], scripted_events[{turn, type, t}], audio_path, sarvam_interaction_id}` → JSONL files + SQLite/DuckDB view | ASSUMED |
| B3 `Metrics` (deterministic) | Judge-free numbers | Trace → `switch_latency_turns/s` (first directive change after scripted event), `false_switch_rate`, `reply_words` per mode, `callback_offered` (regex in Devanagari + Latin), `reply_latency_s`, `tool_skip_rate` | Latency + tool counting PROVEN in spike; rest ASSUMED |
| B4 `Judges` | Typed verdicts per call | Trace (arm label stripped) → `Verdict{call_id, criterion, value, severity, rationale, judge_model}`; Jev for binary/typed criteria, OpenRouter LLM (different family from simulator) for ordinal persona-fit/naturalness | ASSUMED |
| B5 `Aggregator` + `Dashboard` | Turn verdicts into decisions; show judges | Verdicts → paired lift with bootstrap CI (#4), Fatal/root-cause/risk queue (#1), Beta-Binomial / mSPRT decision (#5); dashboard reads B2/B5 and live SSE from signal server | ASSUMED |
| Signal server (in-call) | Already the switch-log producer | Sarvam API tool POST → `{seller_mode, persona_directive}` + log row | PROVEN with stub; Jev not yet reachable from Daytona |

- The signal-server log is the deck's required "Switch log: signal detected, change made, reason", so B2 should ingest it per call (ASSUMED).
- Joining sim traces to Sarvam's own record: store `get_interaction_id()` in each trace, then pull `audio_url`, `average_agent_response_time_in_seconds` and `has_log_issues` from the Interactions API as an independent check on our RMS-based latency (ASSUMED; endpoint DOCUMENTED).

### Gaps
- Exact per-turn transcript schema (role/text/timestamps/tool calls) of the Transcripts API is undocumented; test with keys.
- Whether `transcript_callback` gives agent-turn timestamps precise enough for latency, or RMS must stay the timing source, is unverified (the spike used RMS).

## 2. Minimal credible experiment for a 2-day hackathon (calls, metrics, cost, time)

### Takeaway
Run 10 seller cards × 2 seeds × 2 arms (ON/OFF, both calling the tool) = **40 voice calls ≈ 60 call-minutes ≈ ₹210 at the ₹3.5/min published rate (₹360 at ₹6/min)**, plus the 3 hero sellers the deck asks for. This exceeds the ₹100 free credit (≈28 minutes ≈ 19 calls at ₹3.5), so hackathon credits are needed. Lead with judge-free metrics (switch latency vs scripted trigger, reply words after trigger, callback offered), and add one LLM-judge persona-fit score. A sign test on 10 card-level paired differences reaches p≈0.002 if all 10 favour ON.

### Cited Findings
- DOCUMENTED: Sarvam Epoch: "Voice Agents are now generally available, with no waitlist, at ₹3.50 per minute with authoring, simulation, phone numbers, evaluation, and analytics included." — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)
- DOCUMENTED: Sarvam pricing page: "₹100 worth of free credits" that "never expire"; plans Starter (PAYG), Pro ₹10,000/month, Business ₹50,000/month; no per-minute Voice Agents rate shown on that page — [Sarvam pricing](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing)
- The "₹6/min PAYG, ₹1.5/min BYO" figures that appear in search results are **Edesy's** platform pricing, not Sarvam's — [Edesy](https://edesy.in/ai-voice-agent/technology/sarvam-ai). Treat ₹6/min only as a conservative upper bound.
- DOCUMENTED: hackathon teams get "API keys / credits on dashboard.sarvam.ai" — [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- PROVEN: in the spike, rushed-mode replies were 11–13 words with a callback offer; in a neutral-mode run the agent once gave a callback by itself and once a 30-word pitch, so prompt-only behaviour is inconsistent and an ON/OFF comparison is needed for attribution — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: the control arm should still call the tool (neutral directive) so latency doesn't confound lift; a "prompt-only" third arm is the steelman — [prior deep research](../../../raw/research/2026-10-07-deep-research-vani-adaptive-persona-architecture.md)
- DOCUMENTED: median pass@k − pass^k gap of 0.44 across 12 systems in EVA-Bench, so repeats matter — [arXiv 2605.13841](https://arxiv.org/abs/2605.13841)
- DOCUMENTED: LLM judges reach >80% agreement with humans but have position, verbosity and self-enhancement bias (2023, older) — [Zheng et al.](https://arxiv.org/abs/2306.05685)
- DOCUMENTED: Sarvam's own Tests feature plays "a simulated user against a committed version of your agent"; "an AI judge reads each finished transcript and grades it"; runs repeat 1/2/3/5×; voice simulations "take minutes"; limits 60 req/min per key, 10 suite runs per 5 min, 20 single-case runs per min (org-wide) — [Tests API overview](https://docs.sarvam.ai/conversations/api/tests/overview.md); [Run tests](https://docs.sarvam.ai/conversations/build/tests/run-tests.md)

### Inferences
- Cost table (ASSUMED ~1.5 min/call, the task's estimate; at ₹3.5 / ₹6 per min, agent side only):
  | Run | Calls | Minutes | ₹3.5/min | ₹6/min |
  |---|---|---|---|---|
  | Pilot (3 hero cards × ON/OFF) | 6 | 9 | 32 | 54 |
  | Minimal credible (10 cards × 2 seeds × 2 arms) | 40 | 60 | 210 | 360 |
  | Stronger (20 × 2 × 2) | 80 | 120 | 420 | 720 |
  | Prior plan (30 × 3 × 2) | 180 | 270 | 945 | 1,620 |
  Seller-side Bulbul TTS is extra; cache audio per (card, seed, line) so repeats and both arms reuse it.
- Time: 40 calls × 1.5 min = 60 min sequential; ~15–20 min at 3–4 concurrent sessions. Run arms interleaved in random order.
- Statistics (my arithmetic): average the two seeds per card, then test 10 paired card differences. Two-sided sign test: 10/10 → p≈0.002, 9/10 → p≈0.021, 8/10 → p≈0.11. With 20 cards, 15/20 → p≈0.041. Report the mean paired difference with a bootstrap CI resampling cards. Objective metrics like switch latency should show near-deterministic ON/OFF gaps (OFF never switches), so 10 cards suffice for them. Judge scores need the 20-card version to be convincing.
- Metric set, mapped to the five Persona success metrics:
  1. Correct, well-timed switches: switch latency in turns/seconds vs scripted trigger; false-switch rate on cards with no trigger (deterministic).
  2. Fit: LLM-judge persona-fit 1–5 conditioned on the hidden card, arm-blind; reply words after a rush trigger; callback offered after rush (regex).
  3. Distinctness: judge or embedding classifier recovering the card archetype from agent turns alone.
  4. Natural voice in 2+ languages: the language-switch card (Hindi→Tamil/Gujarati) plus Sarvam's `average_agent_response_time_in_seconds`; human MOS from 2–3 teammates on 6 clips.
  5. Past-call evidence: card parameters cite aggregate clusters from the data (no raw text).
- Judge calibration at hackathon scale: 20 human-labelled calls per ordinal criterion, Cohen's κ reported; claim lift only on criteria with acceptable κ (ASSUMED threshold ~0.6).
- Sarvam Tests could be a cheap regression smoke-test (and the deck for #5 itself says "test on simulated sellers built with Sarvam voice agents"), but its judge is a black box and it doesn't expose our switch log or scripted-trigger timing. Keep our harness as the measured experiment and mention Tests as complementary (ASSUMED).

### Gaps
- No published per-minute price for SDK simulated calls vs telephony in Sarvam docs; whether simulation minutes are billed the same as phone minutes is unknown. Ask Sarvam on day 1 and check wallet deltas after the pilot.
- Sarvam concurrency limit for SDK CALL sessions is undocumented.
- Real average call length of our simulated calls not yet measured (1.5 min is an estimate).

## 3. Realism of simulated sellers

### Takeaway
Seed cards from aggregate patterns in the past-call data (turn-length distribution, objection types and their turn of first appearance, language mix, hang-up turn, rush/frustration rates), script the trigger events, and let an OpenRouter LLM fill only the in-between lines in the card's style. Use Bulbul v4 voices that differ from the agent's voice. Validate with a distribution overlay and a real-vs-sim discriminator. ASR quirks are a feature to keep, because the real agent sees them too.

### Cited Findings
- DOCUMENTED: LLM simulators show "excessive verbosity, lack of a consistent persona… and unreasonable patience" — [ConvApparel, arXiv 2602.16938](https://arxiv.org/html/2602.16938v1)
- DOCUMENTED: EVA-Bench detects user-simulator errors and regenerates before scoring — [arXiv 2605.13841](https://arxiv.org/abs/2605.13841)
- PROVEN: voice catalogue of 200 voices (176 Bulbul v4) tagged by gender/tone/pace/use-case/language; Hindi sales voices include Aditya, Tarun, Ritu, Simran; Gujarati Bhavik, Pooja; Tamil v4 has only Aravind (ad), Gokul and Vijay (narrators), with no Tamil conversational voice — [spike log](../../../raw/research/2026-10-07-spike-log.md); `raw/research/2026-10-07-sarvam-voice-catalogue.json`
- PROVEN: the PS07 data shows live signals (rush 21% of calls) halve meetings, and script personalisation failed 3 trials — [[persona-data-validation]] (`wiki/projects/vani-hackathon/persona-data-validation.md`)
- PROVEN: ASR splits a seller turn on a pause (tool called twice per turn: partial then full utterance) and mis-hears words ("अभी जी हूं यार" for "अभी बिजी हूँ यार") — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences (ASSUMED)
- Card generation: cluster historical calls on outcome × objection set × language × length and sample card parameters from each cluster's empirical distribution; store only `evidence_refs` to cluster IDs and aggregate stats (meets the no-customer-data rule and the "support from past-call evidence" metric).
- Scripted triggers are written as card-specific lines in the card language ("abhi busy hoon yaar, jaldi bolo"), injected at a fixed turn, so switch latency is measurable without a judge.
- Seller voices: rotate Bulbul v4 speakers by card gender/language with pace variation (e.g. a fast speaker for rushed cards); never reuse the agent's voice. Tamil seller lines can use any v4 speaker that renders Tamil, since seller naturalness matters less than agent naturalness.
- Inject realism cheaply: short replies ("haan", "boliye"), filler, occasional overlap/barge-in (send audio while the agent speaks), and 1–2 s mid-turn pauses that trigger the ASR split seen in the spike.
- Validation for the deck: histogram overlay of sim vs aggregate real turn length and call length, plus an LLM discriminator on (anonymised, aggregate-styled) real vs sim excerpts. Only aggregates go into notes.

### Gaps
- No published realism benchmark for code-mixed Indian B2B seller simulation.
- Whether Bulbul-rendered seller speech is recognised by Sarvam ASR more cleanly than real phone audio (8 kHz, noise) is unknown; it likely flatters ASR. Mitigation: add noise or downsample to 8 kHz and back (ASSUMED).

## 4. Trace store, judges and the dashboard: tech and what to show

### Takeaway
Use JSONL + DuckDB/SQLite and a **Streamlit** (or Gradio) app for the analytical dashboard, plus a tiny live "switch log" page fed by SSE/polling from the signal server. Show judges four panels: live switch timeline, ON vs OFF paired results, persona specs with evidence, and the reuse panels (#1 audit queue, #5 run report). Sarvam's built-in analytics gives health metrics only, not auto-grading, which leaves room for our audit layer.

### Cited Findings
- DOCUMENTED: Sarvam Agent Analytics provides volume, connectivity, latency, billable minutes, short-call rate, top failure reasons and outcome classes; it does not describe automatic call grading or issue flagging, and suggests users "sample a few rows" when metrics look suspicious — [Sarvam Agent Analytics overview](https://docs.sarvam.ai/conversations/monitor/agent-analytics/overview.md)
- DOCUMENTED: deck criteria weights: Business Impact 25%, Solution Completeness 20%, Technical Robustness 20%, Voice Experience 20%, Demo & skills.md 15%; Persona outputs include "Live demo with at least one mid-call switch" and "Switch log: signal detected, change made, reason"; the demo is "the same scenario for 2 to 3 contrasting sellers" — [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- DOCUMENTED: Jev-style typed judges vs LLM judges: similar accuracy on binary criteria, worse on ordinal, 16–325× cheaper, 28–350× faster; when Jev is confidently wrong, ~96% of LLM judgments share the error — [arXiv 2609.29769](https://arxiv.org/abs/2609.29769)
- PROVEN: Jev via OpenRouter Decisions API costs ~$0.00004 per 6-question decision; keep-alive p50 ~491 ms from the office — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences (ASSUMED)
- Tech choice: Streamlit is the fastest to build for tables, charts and audio players (`st.audio`) and runs as one Python process in a Daytona sandbox. A Next.js app is slower to build and adds nothing judges score. Gradio is equivalent; pick whichever the team knows.
- Judges: Jev for typed binary items (callback offered? bot disclosed truthfully? opt-out honoured? seller frustrated at end?) on every call; one OpenRouter LLM (different family from the seller simulator, arm-blind) for persona-fit 1–5 and naturalness. Do not let Jev grade the ON arm's switch correctness (it made those decisions); use deterministic switch latency instead.
- Dashboard panels for the jury (one per scoring criterion):
  1. Voice Experience: live call view with an audio player, per-turn transcript, and `seller_mode` flips with timestamps and reply latency.
  2. Business Impact: ON vs OFF paired chart (switch latency, reply words after rush, callback rate, persona-fit), with CI and p-value, plus the data evidence that rush halves meetings.
  3. Completeness: persona spec per seller with a reason and evidence per field; switch log table.
  4. Robustness: tool-skip rate, Jev timeout fallbacks, false-switch rate, judge κ.
  5. Reuse tabs: "Audit" (#1) and "A/B" (#5) on the same traces.

### Gaps
- No source checked on Streamlit/Gradio SSE support behind proxies; the quick-tunnel SSE limitation (section 6) applies whichever framework is used.

## 5. Live demo paths and the 5–7 minute video

### Takeaway
Three tiers, from most to least reliable: (A) **autonomous harness run**, recorded with the dashboard (PROVEN path, no telephony); (B) **browser call** via the Web SDK through our backend proxy, presenter speaks Hinglish and says "jaldi bolo" (DOCUMENTED, untested); (C) **real phone call** via Instant Outbound to a consenting teammate, which needs a rented number (KYC first) or a BYO connection, `app_version` per voice archetype, and a TRAI/NDNC check (DOCUMENTED, blocked on KYC). Record A and B for the video; attempt C only if KYC clears on day 1.

### Cited Findings
- DOCUMENTED: Instant Outbound `POST https://apps.sarvam.ai/api/outbounds/v1/orgs/{org_id}/workspaces/{workspace_id}/outbounds`, required `app_config{app_id, app_version (int), connection_config{connection_id, agent_phone_number}}`, `user_config{user_phone_number}`; optional `agent_variables`, `app_overrides`, `webhook_config{url, metadata}`; returns `attempt_id` — [Sarvam Instant Outbound create](https://docs.sarvam.ai/conversations/api/instant-outbound/create.md)
- PROVEN (from UI/docs check): Instant Outbound has no TTS override, so per-call voice on the phone means one published `app_version` per voice archetype — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: Rent from Sarvam: Individual or Corporate account, "Complete KYC verification (required before renting)", numbers are rented for 30 calendar days and auto-renew, price varies per number, cost deducted from the Sarvam wallet; KYC documents and approval time are not stated — [Sarvam rent a number](https://docs.sarvam.ai/conversations/deploy/telephony/rent-from-sarvam.md)
- DOCUMENTED: outbound webhook statuses `connected / no_answer / busy / failed`; failure reasons are provider-prefixed, e.g. `"exotel: Phone number is registered under TRAI NDNC"`; transcript items are `{role, en_text}` (English) — [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload.md)
- DOCUMENTED (secondary news source): a TRAI amendment dated 18 Sep 2026 treats AI-voice calls as A2P calls that must be pre-declared to the telecom provider — [TelecomLead](https://telecomlead.com/telecom-services/trai-tightens-spam-call-rules-with-ai-ml-detection-%E2%82%B90-05-a2p-charge-and-faster-enforcement-127804) (via prior research note)
- PROVEN: call forwarding in the agent UI is "Vobiz only" — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: Web SDK = `sarvam-conv-ai-sdk` `/browser` entry; `BrowserAudioInterface` captures the mic and plays agent audio (16-bit PCM mono); callbacks `transcriptCallback`, `stateCallback`, `audioLevelCallback`, `eventCallback`; "Never embed your API key in client-side code. Point `baseUrl` at a backend you control… so the proxy adds the Sarvam key server-side"; `start()` must come from a user gesture. No no-code widget or share link is described on that page — [Sarvam Web SDK](https://docs.sarvam.ai/conversations/deploy/sdks/web.md)
- DOCUMENTED: the deploy overview lists a "Web widget: embedded call-or-chat button, no phone needed" channel — [Sarvam deploy docs check](../../../raw/research/2026-10-07-sarvam-deploy-sdk-docs-check.md)
- DOCUMENTED: submission requires a 5–7 min demo video, approach note, Agent ID / live link, code + README, skills.md; the jury screens the video, then a live demo + Q&A follows on a later date — [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)

### Inferences (ASSUMED)
- Simplest browser fallback: a Python SDK client using `AsyncDefaultAudioInterface` (laptop mic/speaker) avoids building the web proxy at all. Use the Web SDK only if a shareable judge-facing link is wanted. The Sarvam web widget, if available on the plan, is the zero-code option, but it can't carry per-seller `agent_variables` unless configured.
- Phone-path checklist: KYC submitted on day 1 morning; one `app_version` per voice archetype (2–3); presenter's number is non-NDNC and they consent; webhook URL on a stable host; ask the Sarvam floor team who handles the TRAI A2P declaration for rented numbers.
- Video plan (6.5 min), scored against the five criteria:
  - 0:00–0:40: problem + data evidence (rush 21% halves meetings).
  - 0:40–1:40: persona generator: 3 contrasting seller cards → 3 specs with reasons and evidence.
  - 1:40–4:00: three voice calls, same scenario. One is a live/browser call with a mid-call "jaldi bolo" switch and the switch log updating on the dashboard. One is a Hindi→Tamil/Gujarati language switch. One is a bot-question disclosure. Show the latency number on screen.
  - 4:00–5:20: ON vs OFF experiment: N calls, paired chart, p-value, judge κ, cost per call.
  - 5:20–6:10: reuse: the same traces in the Audit tab (#1: Fatal flags, root-cause clusters) and the A/B tab (#5: variant decision).
  - 6:10–6:30: architecture slide, Agent ID, skills.md pointer.

### Gaps
- KYC document list and approval time for Sarvam number rental are undocumented.
- Whether Vobiz/Sarvam files the TRAI A2P pre-declaration for rented numbers is unknown.
- Whether the hackathon org has the web widget enabled is not checked.

## 6. Hosting and networking: where each service runs; stable public URL options

### Takeaway
Run the **signal server, trace store, judges and dashboard in a self-hosted Daytona sandbox** (egress to Sarvam and OpenRouter PROVEN). The blockers are inbound DNS/TLS (no wildcard on `*.proxy-daytona.intermesh.net`) and OpenRouter's IP allowlist (sandbox IP 35.234.211.110 not allowlisted). Today's inbound is a cloudflared quick tunnel, whose URL changes on restart and which **does not support SSE**. The best fix is for the Daytona admin to add wildcard DNS + a wildcard certificate (DNS-01). Next best is a fixed internal reverse-proxy hostname. A named Cloudflare tunnel is a stable fallback, but it needs a Cloudflare account and zone, so check the vendor rule. Route Jev via the IndiaMART LiteLLM gateway or get 35.234.211.110 allowlisted on OpenRouter.

### Cited Findings
- PROVEN: Daytona sandbox egress to api.sarvam.ai, apps.sarvam.ai and openrouter.ai works; Python 3.11.14 inside; the Python SDK 0.222 is incompatible (use REST) — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: preview URL `https://{port}-{id}.proxy-daytona.intermesh.net` has no wildcard DNS and no wildcard TLS cert; it works only with a Host header + `-k` against 35.234.211.110; the sandbox is public (no preview token needed) — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: cloudflared quick tunnel inside the sandbox works: health 200, `/read_seller_signal` 200 in 0.11 s with token, 401 without; Sarvam's API tool reached it from 4.213.167.70 — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED: Quick Tunnels: "up to 200 in-flight requests. Additional requests return a 429"; "no uptime guarantee"; Server-Sent Events are not supported; "The hostname changes each time you create a Quick Tunnel"; Cloudflare recommends a standard tunnel for stable hostnames — [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- DOCUMENTED: Daytona open-source deployment behind a public domain with HTTPS uses Caddy as reverse proxy and Let's Encrypt; the compose stack includes a separate Proxy service — [Daytona OSS deployment (search summary)](https://www.daytona.io/docs/oss-deployment/) (the page itself returned 404 on fetch, so the details are unverified)
- DOCUMENTED: hosted Daytona preview URLs follow `https://{port}-{sandboxId}.{proxyDomain}`; non-Tier-3 orgs see a warning page unless the request sends `X-Daytona-Skip-Preview-Warning: true` — [Daytona preview docs](https://www.daytona.io/docs/en/preview-and-authentication/)
- PROVEN: OpenRouter allowlist: the office VPN tunnels IPv4 only; forcing IPv4 (egress 121.241.109.212) gives 200, IPv6 exits via Wi-Fi and gets 403; the sandbox (35.234.211.110) is still not allowlisted — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN: LiteLLM has a TypeSafe pass-through (`<LITELLM_PROXY>/typesafe`), but IndiaMART's gateway shows 8 Jev requests, all failures (22 Sep–5 Oct) — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences (ASSUMED)
| Service | Where | Inbound | Outbound needs |
|---|---|---|---|
| Signal server (in-call, latency-critical) | Daytona sandbox | Sarvam API tool from 4.213.167.70 → stable HTTPS URL | Jev: OpenRouter (needs sandbox IP allowlisted) or LiteLLM gateway |
| Harness (SDK CALL sessions) | Daytona sandbox (egress PROVEN) or laptop | none | Sarvam WS + TTS; OpenRouter for LLM seller lines |
| Judges / aggregator (batch) | Office laptop on VPN with IPv4 forced, or sandbox once allowlisted | none | OpenRouter/Jev |
| Dashboard | Daytona sandbox | Judges/presenters' browsers | reads local store |
| Webhook receiver (phone path, #1) | same server as signal | Sarvam webhooks | none |

- Stable URL options, ranked:
  1. Ask the Daytona admin for `*.proxy-daytona.intermesh.net` DNS → 35.234.211.110 plus a wildcard cert (DNS-01). This fixes every port with no new vendor.
  2. An internal reverse proxy (nginx/Caddy on an existing IndiaMART host with a fixed `vani-hack.<internal-domain>` record) pointing at the sandbox IP + Host header. Same effect, one hostname.
  3. A named Cloudflare tunnel (stable hostname, SSE supported per standard tunnels). Needs a Cloudflare account and a DNS zone on Cloudflare, so confirm Cloudflare is acceptable under "no new outside vendors" (cloudflared itself is Apache-2.0).
  4. Quick tunnel: demo-only. Re-register the tool URL in the Sarvam agent after every restart, and use polling instead of SSE for the live dashboard.
- Live dashboard over a quick tunnel: use 1–2 s polling of `/log`, not SSE.
- Keep the harness and dashboard independent of OpenRouter: if the allowlist isn't fixed, run the judges batch-wise from the VPN laptop and push results to the sandbox.

### Gaps
- Exact self-hosted Daytona env var names for the proxy domain (e.g. `PROXY_DOMAIN`, template URL) were not verified (docs page 404).
- Whether Daytona's proxy passes SSE/WebSocket upgrades is untested.
- Whether Cloudflare (named tunnel) counts as an "outside vendor" under the team rule needs a user decision.

## 7. Reuse for Quality Audit (#1) and A/B Testing (#5)

### Takeaway
#1 = the same judges pointed at real calls pulled from Sarvam's Interactions/Transcripts APIs (or webhooks), with a Fatal/Non-Fatal severity map, clustering of failure rationales, LLM fix suggestions, and fix validation through the paired simulator. #5 = the ON/OFF experiment generalised: variants are published `app_version`s, the split is a hashed random assignment in our launcher, auto-disposition is a Jev/LLM judge, and decisions use a Beta-Binomial expected-loss rule or mSPRT with a Fatal-rate guardrail for early stop.

### Cited Findings
- DOCUMENTED (#1 deck): "Auto-grade every call as Fatal or Non-Fatal; group failures into root causes; rank by frequency and severity; suggest the prompt fix; one dashboard showing audit, issue, fix, test; flag risky calls: wrong requirement, frustration, loops, low confidence, human request". Metrics: agreement with human auditors, share of calls audited, root-cause quality, drop in failure rate after a tested fix, time from issue to fix tested — [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- DOCUMENTED (#5 deck): variants A/B; audience share (e.g. 10%), random assignment, fixed window, goal disposition (Meeting Fixed, Buyer Enriched, Callback Fixed); LLM auto-disposition; winner checked for significance and promoted; stop a clearly worse variant early; "test on simulated sellers built with Sarvam voice agents". Metrics: right winner on a known-difference test, split accuracy, auto-disposition accuracy vs labels, correct promotion/early stop, easy setup — [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- DOCUMENTED: post-call data for #1: Interactions API (incl. `audio_url`, `ended_by`, `has_log_issues`, `agent_variables`, response times) and per-interaction Transcripts — [Interactions](https://docs.sarvam.ai/conversations/api/analytics/interactions.md); [Transcripts](https://docs.sarvam.ai/conversations/api/analytics/transcripts.md)
- DOCUMENTED: inbound deployment webhook POSTs `app_id, app_version, deployment_id, interaction_id, duration, final_agent_variables, output_agent_variables, start/end_datetime, interaction_transcript (role, text), metadata` after each call; configured via the deployment's `webhook_config` — [Deployments webhook](https://docs.sarvam.ai/conversations/api/deployments/webhooks/webhook-payload.md)
- DOCUMENTED: outbound webhook carries `status`, `failure_reason`, `final_agent_variables`, transcript `{role, en_text}`; no recording URL — [Instant Outbound webhook](https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload.md)
- DOCUMENTED: campaigns webhook POSTs each call's outcome, connectivity, retry metadata, timestamps and output variables — [Sarvam platform docs check](../../../raw/research/2026-10-07-sarvam-platform-docs-check.md)
- DOCUMENTED: always-valid p-values via mSPRT allow continuous monitoring and stopping at any time while controlling Type I error (older; deployed at Optimizely) — [Johari et al., arXiv 1512.04922](https://arxiv.org/abs/1512.04922v2)
- DOCUMENTED: Bayesian expected-loss stopping rule: stop when the expected loss of choosing the better arm falls below a "threshold of caring" (VWO whitepaper default ε = 0.02) — [Stucchio blog](https://chrisstucchio.com/blog/2014/bayesian_ab_decision_rule.html) (older, via search summary). Bayesian tests are not immune to optional-stopping issues for error rates — [Analytics-Toolkit](https://blog.analytics-toolkit.com/2017/bayesian-ab-testing-not-immune-to-optional-stopping-issues/) (older)
- DOCUMENTED: Sarvam Tests supports repeat runs per case and runs against a chosen agent version — [Run tests](https://docs.sarvam.ai/conversations/build/tests/run-tests.md)
- PROVEN: the local past-call data includes evaluator outputs (aggregates only usable in notes) — task context; [[persona-data-validation]]

### Inferences (ASSUMED)
- **#1 Quality Audit on the same blocks**:
  - Ingest: B2 adapter for (a) historical calls with existing evaluator outputs (offline, local `data/` only), (b) Sarvam Interactions + Transcripts pull, (c) webhooks.
  - Grade: B4 judges with a severity map. Fatal = wrong commitment/misinformation, missed opt-out, false claim of being human, abusive tone. Non-Fatal = missed objection, slow switch, over-long reply, no callback for a rushed seller. The risk queue covers the deck's five flags: wrong requirement, frustration, loops (repeated agent turns), low confidence (judge disagreement or Jev p near 0.5), human request.
  - Agreement metric: compare judge verdicts with the existing evaluator labels / a small human-labelled set (κ).
  - Root causes: embed judge rationales, cluster, rank by frequency × severity.
  - Fix: an LLM proposes a prompt diff per cluster. Validate by turning failing calls into synthetic cards (aggregate pattern, not text) and running fix-ON vs fix-OFF in B1. This is the "drop in failure rate after a suggested fix is tested" metric, with "time from issue to fix tested" timed by the pipeline.
- **#5 A/B on the same blocks**:
  - Variants = published `app_version`s (needed anyway for per-call voice). The launcher assigns each call by `hash(seller_id, test_id) mod 100 < share`, and the B2 trace records arm + version. Split accuracy = observed vs configured share (chi-square).
  - Auto-disposition = a B4 judge emitting the goal disposition (Meeting Fixed / Callback Fixed), checked against labelled calls.
  - Decision: Beta(1,1) prior per arm on goal-disposition rate. Promote when P(B>A) > 0.95 and expected loss < ε. Early stop on a guardrail (Fatal-rate posterior or one-sided mSPRT on Fatal) or when P(B>A) < 0.05. On the simulator, run on paired card blocks.
  - "Right winner on a known-difference test": build a deliberately worse variant (e.g. a version that ignores the rush directive or pitches 60 words) and show the engine stops it early. This also doubles as the persona ON/OFF experiment, so one run feeds both stories.
- Same dashboard, three tabs: Persona (live + lift), Audit, A/B.

### Gaps
- Sarvam APIs do not document a way to set traffic share across `app_version`s natively for campaigns; the split must live in our launcher (assumed, not verified).
- The analytics APIs' rate limits and data retention are not documented.
- Whether the Interactions API returns calls made via SDK CALL sessions (`is_debug_call` hints yes) is untested.
