# Sarvam Voice Agents platform + Pipecat Sarvam services: docs check (2026-10-07)

Docs read, not yet tested with keys. Sources: docs.sarvam.ai pages below.

## Sarvam Voice Agents ("Conversations") platform
- Agent = instruction (persona, objective, guardrails) + variables + speakers & voice + tools + on-start/on-end hooks + knowledge base. (conversations/build/agent/overview)
- Voice settings: default voice, per-language voice overrides, model **Bulbul V3 or V4**, speaking speed slider, pitch slider, pronunciation dictionary. (conversations/build/voice-language)
- "The assigned speaker then remains consistent for the duration of the call, even if the caller switches languages mid-conversation." Speaker, speed, pitch are agent-level; docs show no per-state / per-tool / per-variable change. Language can follow the caller.
- Multi-state agents: each state has its own name, instructions, tools, next states. Transitions "when conditions are met" (e.g. collected a field, caller wants to escalate). Docs don't say whether a state can have its own voice or whether a tool can force a transition. (conversations/build/states-conversation-flow)
- Tools: "The model decides when to call a tool via function calling; the harness validates and executes it." (conversations/build/tools)
- Variables: input variables come from telephony metadata, on-start hook responses, and campaign CSV columns. "Tools can read and write any agent variable mid-call." Output variables are extracted after the call ends. (conversations/build/variables-personalization)
- API tools can receive live call context: User Identifier, Call Transcript, Interaction ID, Call Length. (changelog 2026-08-20)
- Campaigns: outbound calling to a contact list on a schedule. A webhook POSTs each call's outcome, connectivity, retry metadata, timestamps, output variables. (changelog 2026-08-20)
- No bring-your-own-LLM / custom endpoint found in the pages read.

## Pipecat + Sarvam
- `pipecat-ai[sarvam]`: SarvamTTSService supports `bulbul:v3` with multiple speakers (default "Shubh") and Indic language codes. (docs.sarvam.ai/api/integration/build-voice-agent-with-pipecat)
- SarvamSTTService: streaming WebSocket, saarika/saaras. `saaras:v3-realtime` needs SarvamRealtimeSTTService, which is "not yet in the released pipecat-ai[sarvam] package"; the release ships the legacy SarvamSTTService. (docs.sarvam.ai/api/integration/pipecat-production-guide)
- Sarvam's own telephony guides use Twilio / Exotel (not allowed under the project's hard rule).
