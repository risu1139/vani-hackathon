# Sarvam Voice Agents: deploy channels, core tools, Python SDK (docs check 2026-10-07)

Docs read, not yet tested with keys. Follows [[2026-10-07-sarvam-platform-docs-check]].

Deck requirement (submission checklist): "Agent ID / live link on Sarvam platform", so the Sarvam Voice Agent is compulsory.

## Deploy channels (conversations/deploy/overview)
- Telephony inbound: phone number linked to the agent (provider number or Sarvam rental).
- Telephony outbound: Campaigns, a contact list on a schedule.
- Web widget: embedded call-or-chat button, no phone needed.
- API & WebSocket: "Start sessions and stream voice over WebSocket". SDKs: Python, Web, React Native, Flutter.

## Core tools (conversations/build/tools/core-tools)
End Call (always on), Call Transfer (phone / SIP URI), KB Query, Voicemail Detection, **Language Switch** ("allows mid-call language changes when the feature is enabled in settings").

## Python SDK (conversations/deploy/sdks/python)
- `pip install "sarvam-conv-ai-sdk[all]"`, class `AsyncSamvaadAgent`.
- Constructor: `app_id` (agent), `agent_variables` (seed at session start), `initial_language_name`, `sample_rate` 16000 (16-bit PCM mono), `audio_interface` (AsyncDefaultAudioInterface for mic/speaker).
- Callbacks: `transcript_callback` (ServerTranscriptMsg, user + agent speech), `audio_callback` (raw agent audio chunks), `event_callback` (interaction_connected, user_interrupt / barge-in, interaction_end).
- Mid-session methods: `send_audio(raw_pcm_bytes)`, `is_connected()`, `get_interaction_id()`, `wait_for_disconnect()`.
- No documented `send_text`, `update_variables`, or interrupt. An outside program can talk to and observe the agent, but can't steer it mid-call.
- Fuller recipes: indus.sarvam.ai/samvaad/deploy/with-code; API reference at /api-reference/introduction.
