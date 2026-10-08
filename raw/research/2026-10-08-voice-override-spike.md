# Spike: per-call voice / pace / pitch / language override via the SDK (2026-10-08)

Code: `app/spike/voice_override_spike.py`. Audio + results: `outputs/voice_override/` (7 WAVs, results.json).

## Facts found first
- Agent Voice-Bot-104c356b-536d uses TTS config version 2.0 (voices-DB): its voice is stored as `text_to_speech_config.internal_id` = `01a0cf16-7179-7472-b7df-b7b432d5faa5` ("Shubh", male, voice_id Viraj, Sarvam TTS v3.1), `speech_settings.pace` = 1.15. `on_start_config` = null.
- SDK `TextToSpeechConfig` docstring: "TTS override an on_start tool can set on its context. speaker_id: for voices-DB (v2) apps, the ai_voices.internal_id UUID ... For legacy (v1) apps, a SpeakerName (lowercase, e.g. "maya")." `SarvamOnStartToolContext` exposes `text_to_speech_config`, `set_initial_bot_message`, `set_initial_language_name`, `set_agent_variable`.
- Voice UUIDs come from the console API `GET apps.sarvam.ai/api/app-authoring/orgs/{org}/workspaces/{ws}/voices?offset&limit` (paginated). Examples: Anand - Documentary Voice (male, TTS v4, Hindi) `01a0e8fc-8a76-72d3-ae24-89b4688928eb`; Aarti - Support Agent (female, TTS v4, Hindi) `01a0cf16-90ae-7470-941d-2c1f17b37528`; Ishita - AI Companion (female, v4, en/hi) `01a0e8fc-b042-7326-a139-e97058ab7c50`; Aparna - Support Agent (female, v4, Hindi) `01a0cf16-8d27-75e7-a4f8-f71f57f86443`.

## Test (7 SDK CALL sessions, greeting only, same opening text)
| case | override passed in InteractionConfig | median F0 | speech s | STT |
|---|---|---|---|---|
| default | none | 123 Hz | 3.22 | Hindi opening |
| anand_m_p1.0 | speaker_id Anand, pace 1.0 | 127 Hz | 3.52 | same |
| aarti_f_p0.85 | speaker_id Aarti (female), pace 0.85 | 126 Hz | 3.46 | same |
| aarti_f_p1.25 | Aarti, pace 1.25 | 127 Hz | 3.52 | same |
| aarti_f_pitch+0.2 | Aarti, pitch +0.2 | 127 Hz | 3.52 | same |
| aarti_f_pitch-0.2 | Aarti, pitch −0.2 | 126 Hz | 3.46 | same |
| lang_english_no_opening | initial_language_name English | 140 Hz | 2.80 | "Hi, I am Shubh, calling from Sarvam. How can I help you today?" (en-IN) |

## Result
- **`text_to_speech_config` passed at session start (SDK InteractionConfig) is ignored**: female voice, pace 0.85 vs 1.25 and pitch ±0.2 all produced the same male voice (F0 ~126 Hz, ~3.5 s) as the default. (Male F0 band ~85–155 Hz; a female voice would be ~165–255 Hz.)
- **`initial_language_name` works**: English → agent opened with its English intro. `initial_bot_message` works (spoken verbatim in the Hindi cases; earlier spike too).
- Per the SDK docstring the voice override is meant to be set by an **on_start tool** (Code Tool; Code Tools are "available on request" from Sarvam) — untested. Other routes: one published agent version per voice profile (select via `version` / `app_version`), or Sarvam's "Per-language voices" setting (voice per language only).
- Every call also had the agent re-prompt after silence ("नमस्ते, क्या आप अभी भी कॉल पर हैं?").
