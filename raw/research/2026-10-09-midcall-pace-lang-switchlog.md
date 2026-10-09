# Checks: mid-call slow-down via the prompt, language switch with a persona voice, and reading the switch log back (2026-10-09)

Agent Voice-Bot-104c356b-536d with the OnStart and ReadSellerSignal code tools and the call_plan variable. Audio from the punctuation test: `outputs/pace_by_punctuation/`.

## 1. Pace can be lowered mid-call through the text the LLM writes (PROVEN)
- **TTS effect.** Same words, same voice (Aarti), pace 1.0, 2 runs each:

  | text style | total delivery | active speech |
  |---|---|---|
  | plain | 8.8 s | 6.5 s |
  | commas between short phrases | 10.3–11.7 s (+17–33%) | 7.3–7.7 s |
  | "…" pauses | 11.0 s (+25%) | 6.9 s |

  Bulbul's prosody slows and pauses on commas and ellipses.
- **The LLM follows the directive.** The confused directive was changed to "Slow down: … very short phrases separated by commas (3–4 words per phrase), then check understanding." In the scripted call (2 runs), the confused reply was:
  - **3.0–3.3 words per phrase with 4 commas**, against 7–10 words per phrase on neutral turns;
  - e.g. "मतलब, बस एक छोटी बात, हमारे expert आपसे मिलेंगे, ज़्यादा orders दिलाएंगे, समझ आया आपको?".

  Rushed stayed at 10 words with a callback offer.
- **Conclusion.** PS04 §3.5 "slows down and simplifies when confused" can be met mid-call by directive-driven phrasing, even though the TTS pace setting is fixed per call.

## 2. Language switch keeps the persona voice (PROVEN + DOCUMENTED)
- **Voice support (DOCUMENTED).** All checked Bulbul v4 voices support 12 languages: Bengali, English, Gujarati, Hindi, Kannada, Konkani, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu. This is from the console voice catalogue API.
- **Gujarati call (PROVEN, 1 run).** The OnStart voice was female Aarti; the seller switches to Gujarati mid-call. Result: 5/5 checks. The agent continued in Gujarati script and used feminine forms ("હું કહેતી હતી"), consistent with the female voice. Sarvam docs say the speaker stays the same for the whole call.
- Downloading the recording via the analytics audio_url returned HTML, not audio (it needs a console session), so the switch-segment F0 was not measured. A listening check is still due.

## 3. The switch log can be read back after the call (PROVEN)
- `GET https://apps.sarvam.ai/api/analytics/v1/{org}/{workspace}/{app}/interactions` with header **`X-API-Key: <agents API key>`** (Bearer / api-subscription-key give 401) returns `agent_variables` per interaction, including our `switch_log`, plus duration, language, ended_by, audio_url and timestamps.
- Example log of one hostile-scenario call: 4 neutral turns, then `neutral → rushed` on "अभी बिजी हूँ यार, बाद में बात करते हैं" (0.04 ms per decision).
- It confirms the in-Sarvam tool ran on every seller turn with Devanagari input.
- **Lexicon gap seen:** "फिर से पूछ रहा हूं, प्राइस बताओ वरना फोन रख दो" was not flagged as frustrated by the keyword list (Jev flags it, per 2026-10-09-jev-devanagari-spike.md).
