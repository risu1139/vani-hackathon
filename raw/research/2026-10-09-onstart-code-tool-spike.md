# Spike: per-call VANI voice + opening via an OnStart code tool driven by agent variables (2026-10-09)

Agent Voice-Bot-104c356b-536d (v1 draft). Code: `app/spike/code_tools/vani_onstart_test.py`. Audio: `outputs/onstart_check/`.

## Findings (PROVEN unless noted)
- Code Tools became available in our workspace on 2026-10-09 (Add tool → "Upload Python file"), after the request email that morning. Sarvam has not replied by email yet.
- The uploader registers during-call `SarvamTool` classes (a diagnostic tool showed as "During call · Python"). An on-start tool is picked up only if **the class is named exactly `OnStart`** (subclass of `SarvamOnStartTool`; per the PyPI page for sarvam-conv-ai-sdk 1.1.1). It does not appear in the tools list.
- `OnStart` runs at call start: a fixed test opening set in the tool was spoken ("नमस्ते, यह ऑन स्टार्ट टेस्ट है").
- Setting `context.text_to_speech_config = TextToSpeechConfig(speaker_id=<voice UUID>, speech_settings=SpeechSettings(pace=…, pitch=…))` in `OnStart` **changes the voice**: female Aarti gave a median F0 of 276 Hz, against about 110–130 Hz for the default male Shubh.
- **Per-call values must come through agent variables that are defined in the agent.** Undefined variables passed via SDK `agent_variables` did not reach the tool (default voice and greeting). After creating the input variables `persona_voice_id`, `persona_pace`, `persona_pitch` and `persona_opening` (empty defaults):

| call | agent_variables | result |
|---|---|---|
| vars_female_aarti_p0.9 | Aarti UUID, pace 0.9, opening "…बोल रही हूँ…" | female 269 Hz; opening spoken verbatim |
| vars_male_anand_p1.2 | Anand UUID, pace 1.2, opening "नमस्कार जी… बस एक मिनट लूँगा" | male 94 Hz; opening spoken verbatim |

- With empty variables the agent behaves as before (default male voice, 118 Hz).
- SDK SpeechSettings ranges per PyPI (clamped at runtime): pace 0.85–2.0, pitch −0.5–0.5, volume 0.7–2.0 (DOCUMENTED).
- Not yet measured: the audible pace difference via OnStart (the two calls used different texts), and the phone / Instant Outbound path with these variables.

## Agent state left after the spike
- The OnStart tool is uploaded (variables-driven; no effect when the variables are empty).
- 4 input variables were added.
- The diagnostic during-call tool was removed by re-upload.
