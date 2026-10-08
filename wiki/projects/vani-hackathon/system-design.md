# VANI system design: 11 blocks, 4 planes

Sources: [[2026-10-08-deep-research-vani-problem-choice-system-design]] · [[2026-10-08-voice-override-spike]] · [[2026-10-08-plan-following-spike]] · [[2026-10-07-spike-log]] · [[2026-10-07-sarvam-deploy-sdk-docs-check]] · [[2026-10-07-deep-research-vani-adaptive-persona-architecture]] · [[2026-10-08-team-decision-between-run-learning]] · [[2026-10-08-deep-research-self-improving-persona-switch-loops]]

**Answer (as of 2026-10-08):** we build **#4 Persona Design**. Before each call, one persona is generated **per seller** from that seller's data. During the call, a frozen switcher changes tone, brevity and language live. **After each run**, a review updates the switcher and the generator. Requirements: [[persona-requirements]]. Learning design: [[learning-loops]].

## Blocks

| Plane | Block | Role | Status |
|---|---|---|---|
| Pre-call | B1 Seller Context Builder | seller features + history + per-seller memory from past runs; flags missing fields | aggregates PROVEN; build ASSUMED |
| Pre-call | B2 Persona Generator | one spec per seller: rules set levels on 8 settings + conversation plan (opening, personalisation, playbook, escalation, guardrails), Sarvam LLM writes wording only, reason + confidence per field | rule stats PROVEN; agent follows a passed plan 15/16 PROVEN; build ASSUMED |
| Pre-call | B3 Launcher | SDK per-session TTS override, or Instant Outbound `app_version` + variables for phone | SDK CALL PROVEN; TTS override + outbound DOCUMENTED |
| In-call | B4 Sarvam Voice Agent (Agent ID) | speaks every word; calls our tool every seller turn | tool 24/24, directive steers reply PROVEN |
| In-call | B5 Signal & Decision Server | lexicon (Devanagari + romanized, NFD) decides now; policy (hysteresis, priority, max 2 switches); directives; switch log | stub + directives PROVEN |
| In-call | B6 Jev Worker | background Jev corrects the next turn; never blocks a reply | 49/51, ~480 ms PROVEN (romanized only) |
| Eval | B7 Simulated Seller Harness | scripted seller cards voice-to-voice via SDK; ON/OFF paired | PROVEN (`app/spike/call_spike.py`) |
| Eval | B8 Trace Store | one append-only record per run (JSONL + SQLite/DuckDB) | ASSUMED |
| Eval | B9 Metrics & Judges | deterministic metrics (switch timing, reply length) + judge calibrated against human labels | ASSUMED |
| Learning | B10 Post-call Reviewer | after each run (live, simulated or replayed PS07 call): LLM labels true signals and switch mistakes | ASSUMED |
| Learning | B11 Updater + Gate | turns reviews into switcher v(n+1) and generator rules / per-seller memory; ships only if the frozen test set doesn't regress | ASSUMED |

A dashboard is optional and the first thing to cut.

## B2 in one line per setting

Voice (gender + timbre → v4 speaker), language (PNS → state → Hinglish default), pace, pitch (only if audible on v4), formality, warmth, opening/brevity, objection playbook + escalation. Fixed gates the loop can't edit: DNC, AI disclosure, "delivery not facts" guardrail (FAQ Q5). Types such as "re-engage" (4.1% meeting rate) or "meeting follow-up" (21.7%) only explain the rules; they're never the output (FAQ Q1).

## Platform facts that shape the design

- **Per-call voice is not settable from the SDK (PROVEN 2026-10-08, [[2026-10-08-voice-override-spike]]).** `text_to_speech_config` (speaker_id UUID, pace, pitch) passed at session start was ignored: a female voice and pace 0.85/1.25 all came out as the agent's default male voice. `initial_language_name` and `initial_bot_message` do work. Routes: an on-start **Python Code Tool** can set `text_to_speech_config`, but Code Tools are on request and not enabled for us ([[2026-10-08-sarvam-on-start-options-check]]); the self-serve on-start **HTTP** hook only fills variables. Fallback: one published agent version per voice profile.
- **Voice and pace are fixed per call.** UI, verbatim: "Voice is assigned per language at call start and will not change mid-conversation." Live switches change wording, brevity, tone and language only.
- **No per-turn hook.** Our server runs only when the agent's LLM calls the tool. It did so on 24/24 turns at temperature 0, sometimes twice (partial then full utterance).
- **No bring-your-own LLM** in Sarvam agents. OpenRouter models can't write spoken replies.
- **Jev is a decision model**, not a chat model: `POST openrouter.ai/api/alpha/decisions`. No fine-tuning; only `state`, `instructions`, `criteria`.
- **Tool payload is Devanagari**, so cues need Devanagari + NFD normalisation.
- **Multi-state agents are legacy**; we use one state + variables (`seller_mode`, `persona_directive`).
- **Code Tools** (deterministic variable writes) are "available on request": ask Sarvam on Day 1.

## Why lexicon now, Jev next turn

Sync Jev would make replies ~2.6 s typical with 3.5–4.9 s tails. After the first rush cue only ~2 seller turns remain (median), so the current reply must change immediately.

## Deployment

B5 on Daytona behind a cloudflared tunnel. B6 on a VPN laptop (OpenRouter key works only from office IPv4). Ask for an allowlist for Daytona egress 35.234.211.110 and for Daytona wildcard DNS/TLS. Fallback: everything on the laptop.

## P0 tests

1. T1 latency with vs without the tool (p95 added ≤ ~0.8 s).
2. T2 tool skip rate on ≥10-turn calls (<10%).
3. T3 credits, billing, concurrency (40+ calls, ≥3 concurrent).
4. T4 a working Jev route from the in-call server.

P1/P2 (T5–T16) are in the source report.
