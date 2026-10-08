# Check: can we set per-call voice ourselves via an on-start tool? (2026-10-08)

Sources: Indus console (agent Voice-Bot-104c356b-536d → Tools → Add tool), docs.sarvam.ai/conversations/build/on-start-on-end-hooks.md, docs.sarvam.ai/conversations/build/tools/code-tools.md, SDK sarvam_conv_ai_sdk/tool.py.

- **On-start API (HTTP) tool: available to us.** Add tool → API Tool → "When should this tool run?" offers "When the call starts" / "During the conversation" / "When the call ends". Docs: on-start is a lifecycle hook with no LLM in the loop; "Map on-start API fields into agent variables and user info" (greeting variables, prefill details, gate tools/states). No documented way for the HTTP hook to set voice/pace/pitch.
- **Code Tools (Python, built on sarvam-conv-ai-sdk): NOT enabled for our account.** Docs: "This feature is available on request. Contact us (support@sarvam.ai)". The docs' Add-tool dialog shows an "Upload Python file" option; our dialog shows only API Tool, Data Validator, Data Verifier, Mock API.
- SDK: `SarvamOnStartToolContext` (code tool) carries `text_to_speech_config` (speaker_id / speaker_name / speech_settings pace, pitch, volume), `initial_bot_message`, `initial_language_name`, `set_agent_variable`. So per-call voice override = an on-start **code** tool → needs Sarvam to enable Code Tools.
- Nothing was added to the agent during this check (dialog cancelled).
