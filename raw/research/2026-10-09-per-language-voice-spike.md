# Spike: per-call voice via Per-language voices + initial_language_name (2026-10-09)

Agent Voice-Bot-104c356b-536d (v1 draft). Settings → Speaking → Per-language voices ON; mapping Hindi → "Aarti - Support Agent" (female, Bulbul v4); no English mapping (falls back to default "Shubh", male). Calls via SDK CALL mode, greeting recorded and measured (code: app/spike/voice_override_spike.py; audio: outputs/voice_perlang_check/).

| case | per-call input | median F0 | STT |
|---|---|---|---|
| perlang_hindi | initial_language_name=Hindi + Devanagari opening | 286 Hz (female) | "नमस्ते, मैं इंडिया मार्ट से बोल रही हूँ…" |
| perlang_english | initial_language_name=English, no opening | 140 Hz (male Shubh) | "Hi, I am Shubh calling from Sarvam…" |
| perlang_hindi_no_lang_given | opening only (starting language default = Hindi) | 281 Hz (female) | Hindi |
| after_revert_hindi (setting turned OFF again) | Hindi + opening | 116 Hz (male default) | Hindi |

## Result (PROVEN)
- The voice IS selectable per call without Code Tools: map voices per starting language, then set `initial_language_name` per call.
- Limit: one voice per language per agent version (e.g., Hindi→female, English→male). Two voices for the same language still need two published versions or Code Tools.
- Setting was reverted after the test (verified: Hindi back to male default).
