# Check: pace audibility via OnStart variables, and the phone path (2026-10-09)

## Pace via OnStart + agent variables (PROVEN; audio in outputs/onstart_pace/)
Same voice (Aarti, female) and the same Devanagari opening; only `persona_pace` changed. Two runs each:

| persona_pace | greeting total | active speech | F0 |
|---|---|---|---|
| 0.9 | 9.10 s, 9.10 s | 6.54 s, 6.54 s | 262 Hz |
| 1.3 | 7.06 s, 7.08 s | 5.20 s, 5.10 s | 262 Hz |

Pace 1.3 is about 21–22% faster than 0.9. The difference is repeatable and large enough to hear. The voice stays the same.

## Phone path (Instant Outbound) (DOCUMENTED; not run)
- API: `POST https://apps.sarvam.ai/api/outbounds/v1/orgs/{org_id}/workspaces/{workspace_id}/outbounds`. Body: `app_config {app_id, app_version, connection_config {connection_id, agent_phone_number}, agent_variables, app_overrides {initial_bot_message, initial_state_name, initial_language_name}}`, plus `user_config {user_phone_number}` and an optional `webhook_config`. Response: `attempt_id`.
- `agent_variables` is accepted, so the persona_* variables can reach the OnStart tool on phone calls too. This is ASSUMED until a call is made.
- **Blocker:** our workspace has no telephony connection. Deploy → Phone numbers offers only "Rent from Sarvam" (Vobiz; needs Individual/Corporate KYC, then buying a number billed through Sarvam credits) or "Bring your own telephony" (Exotel, Smartflo, Pulse, InTalk, Vobiz, Twilio, Plivo).
