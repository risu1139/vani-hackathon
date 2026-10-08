# Voice AI landscape, Oct 2026: what's out there for VANI

Sources: [[2026-10-07-voice-ai-research-synthesis]] · [[2026-10-07-last30days-open-source-voice-ai-agents]] · [[2026-10-07-hackathon-deck-problem-statements]] · [[2026-10-07-sarvam-platform-docs-check]]

**Answer:** this is the market scan behind picking **#4 Persona Design** on a **[[sarvam-voice-agents]]** agent. The Sarvam agent is compulsory, since the deck requires an Agent ID. The current design lives in [[system-design]]; this page keeps only the outside facts. As of 2026-10-07.

## Why #4

- Voice Experience is 20% of the deck score, and Persona Design is the only problem whose demo is the voice itself.
- The dataset is provided (PS07 persona files).
- Ranking by "least change for highest score": Persona (#4) > Quality Audit (#1) > A/B Testing (#5) ≫ Memory (#2), Best Time to Call (#3), Seller Enrichment (#7).

## Outside facts still in use

- **[[jev]] is a classifier, not a talker.** TypeSafe "System One" model (early access 2026-09-28): typed labels from a schema, $0.042/MTok input, free output.
  - First voice benchmark (Veris AI, 2026-10-06): Jev as a turn detector cut interruptions from 52% to 11% of turns, but median reply rose from 2.1 s to 4.6 s and task completion didn't change.
  - Lesson: run Jev beside the conversation, never as a gate on the reply. That's why B6 is background-only.
- **Persona-per-voice is a live pattern** (`ferni-ai/voiceai`, Gemini Live). Copy the pattern, not the code.
- **[[sarvam-bulbul]]** is the voice palette: 176 tagged v4 voices ([[2026-10-07-sarvam-voice-catalogue]]), Hinglish, telephony audio. No Tamil conversational voice.
- **[[voice-agent-eval]] went open source** (Egma, chanl-eval: simulated callers, per-criterion pass/fail). They can't drive Sarvam agents directly, so we build a thin harness on `sarvam-conv-ai-sdk` (B7).
- **[[pipecat]] / [[dograh]]** are capable open-source stacks, but they can't be VANI: the bot must be the Sarvam agent. Not in our path.

## Risk carried forward

- **Disqualification:** "plagiarised or pre-built solutions are disqualified". Frameworks are fine; the persona logic, switch logic and loops must be ours, written during the event.
