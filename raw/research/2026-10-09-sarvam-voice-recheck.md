# Re-check on hackathon day 1: Sarvam voice controls (2026-10-09)

Docs re-read today (docs.sarvam.ai; latest changelog entry 2026-10-06), TTS API measured, agent override spike re-run, console checked.

## Docs (DOCUMENTED, as of 2026-10-09)
- Bulbul model page: `pace` 0.5–2.0 for bulbul:v3 and bulbul:v4-flash; `pitch` and `loudness` listed as **bulbul:v2 only**; no SSML. "Romanised Indic input degrades quality ... Always use native script for Indic words."
- Bulbul v4 Flash: 222 persona voice IDs `<name>_<language>_<style>` (e.g., aditya_hi_sales, ritu_hi_customer_warm, ishita_enhi_customer).
- Changelog 2026-10-06: Bulbul V4 available for Voice Agents (choose V3 or V4 per agent; filterable catalog; V3→V4 name mapping). 2026-10-01: voice-cloning streaming (cloning is enterprise-only for agents). 2026-10-04: Doc Agents only.
- Agents "Speakers & voice": **Per-language voices** — "assign a dedicated voice persona to each starting language ... At the start of a call, the agent selects the voice mapped to the starting language"; speaker stays for the whole call. Agent UI also has Speaking speed and Pitch sliders.

## TTS API measurements (PROVEN, outputs/tts_check/)
Same Devanagari sentence, 16 kHz:
- **Pace works on v3 and v4:** active speech v3 aditya 3.66 s (1.0) / 4.82 s (0.7) / 3.26 s (1.4); v4 aditya_hi_sales 2.28 s / 3.98 s / 1.76 s.
- **Pitch is accepted and works on v3 and v4 despite the docs** (3 runs each, median F0): v4 aditya_hi_sales 104 / 150 / 162 Hz at pitch −0.5 / 0 / +0.5; v3 aditya 89 / 106 / 132 Hz. Run-to-run variation is large (generative), but the direction is consistent.
- v4 female voices: ritu_hi_customer_warm F0 254 Hz, ishita_enhi_customer 267 Hz; male aditya_hi_sales ~132–150 Hz.

## Agent per-call override re-run (PROVEN)
- SDK `text_to_speech_config` (female speaker_id, pace 0.85 / 1.25) still ignored: identical greeting audio (F0 122 Hz, 3.18 s) for default and both overrides.
- Console Add tool still shows only API Tool / Data Validator / Data Verifier / Mock API — Code Tools (Upload Python file) not enabled.

## Implications
- Per-call voice WITHOUT Code Tools: Per-language voices + per-call `initial_language_name` (proven to work) selects the voice per call — but only one voice per language per agent version.
- Pitch is usable on v3/v4 (API-level proven; agent-level pitch slider untested).
- Write Indic text (openings, plan lines) in native script, not romanised.
