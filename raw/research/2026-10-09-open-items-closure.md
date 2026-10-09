# Closing the v6 architecture open items (2026-10-09)

Agent Voice-Bot-104c356b-536d (v1 draft). Code: `app/spike/code_tools/vani_onstart_test.py` (OnStart + ReadSellerSignal). Results: `outputs/onstart_pitch/`, `outputs/spike-callplan-insarvam-20261009-150535.json`.

## 1. Can a during-call tool change voice or pace? NO (DOCUMENTED, SDK 1.1.1)
`SarvamToolContext` (during-call) has no `text_to_speech_config`. It can:
- change_language, change_state;
- set/get agent variables (only variables defined in the agent: set_agent_variable raises "Variable … not defined" otherwise);
- end the conversation;
- return `message_to_llm` or `message_to_user` (speak an exact line).

Only the OnStart tool can set the TTS config. So "slow down when confused" mid-call must be a wording change (simpler, shorter, check understanding), not a pace change.

## 2. Pitch via OnStart variables: WORKS (PROVEN)
Same voice (Aarti), same Devanagari opening, pace 1.0, one run each:
- persona_pitch −0.3 → F0 239 Hz;
- 0 → 267 Hz;
- +0.3 → 286 Hz.

That is about ±2 semitones, which is audible.

## 3. Signal-server host: resolved by running the switcher INSIDE Sarvam (PROVEN)
- **Daytona:** the preview URL still has no DNS (`8000-<id>.proxy-daytona.intermesh.net` does not resolve). The sandbox was found **stopped** despite autoStop 0. The cloudflared quick tunnel was down, and its URL changes on every restart. So Daytona is not a stable host for the in-call endpoint without admin help.
- **New route:** a during-call Python code tool `ReadSellerSignal` (tool name read_seller_signal) runs inside Sarvam. It does the following, with no external host or network hop:
  - classifies the seller's utterance with the romanised + Devanagari keyword list;
  - sets the `seller_mode` and `persona_directive` variables;
  - appends to a `switch_log` variable (defined in the agent);
  - returns the directive to the LLM.

  Local unit test: 0.07 ms per call.
- **Not covered by the code tool:** Jev, which needs network. From inside Sarvam it would go out via Sarvam's egress IP (4.213.167.70), which is not on our OpenRouter allowlist. Options: allowlist that IP, or run Jev offline in the review loop only.
- The old HTTP tool was renamed `read_seller_signal_http`. It still points at the dead tunnel and is not called by the prompt.

## 4. Separate `call_plan` variable: WORKS (PROVEN)
- Setup:
  - Defined `call_plan` and added "CALL PLAN for this seller (follow its steps and objection order; it stays valid for the whole call): @call_plan" to the instructions.
  - The plan was passed only in `call_plan`, with `persona_directive` starting as "Continue normally."
  - The in-Sarvam tool overwrites only seller_mode / persona_directive / switch_log.
- Result: same hostile + Gujarati scenarios as the 2026-10-08 stress test, 2 runs each: **19/20 checks**.
  - The one fail is a false alarm: "१५ minute" tripped the no-digit price check; it is a time, not a price. So effectively 20/20.
  - Compare 2026-10-08: plan re-sent every turn 20/20; plan only at call start in persona_directive 23/28.
  - Rush → "कोई बात नहीं, मैं आपको कब call करूँ?" (10–12 words), so the in-Sarvam switch fired.
  - The Gujarati switch held; price objections were deflected to the meeting with no amount.
- Re-sending the plan every turn is no longer needed.

## 5. Phone number
Parked by the team lead: rent from Sarvam later. The Instant Outbound API accepts agent_variables (see 2026-10-09-onstart-pace-and-phone-check.md).

## 6. Data agent schema
Drafted as `app/contracts/seller_context.schema.json`: v0, then v0.1 with the data agent's optional additions; owner is the data agent. Sent to the peer; their adapter from points.json → seller_context will be the source. Peer facts are filed in raw/hackathon/2026-10-09-peer-briefs.md.

## Agent state after this work
- Tools: OnStart and ReadSellerSignal (Python), plus read_seller_signal_http (inactive in practice).
- Variables: call_plan, switch_log, persona_voice_id/pace/pitch/opening, seller_mode, persona_directive, user_name.
- Instructions: add the @call_plan line.
