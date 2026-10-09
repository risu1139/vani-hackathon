# Spike: Jev on native-script (Devanagari/Tamil/Gujarati) seller turns (2026-10-09)

Code: `app/spike/jev_devanagari.py`. Results: `outputs/spike-jev-native-20261009-143835.json`. Jev model typesafe/jev-1.13 via the OpenRouter Decisions API from the VPN laptop (IPv4). The 30 sentences from the 2026-10-07 smoke set were rewritten as live ASR writes them (Hindi in Devanagari with English loanwords in Devanagari, Tamil in Tamil script, Gujarati in Gujarati script). 6 extra tricky native-script cases were added. All sentences are hand-written; no customer data.

| condition | correct | p50 latency |
|---|---|---|
| A romanised text + current (romanised-cue) questions | 50/51 | 508 ms |
| B native script + current questions | **49/51** | 509 ms |
| C native script + criteria with native-script cue examples | 49/51 | 505 ms |
| D 6 tricky native cases + current questions | **10/10** | 498 ms |
| E 6 tricky native cases + native cues | 10/10 | 493 ms |

## Findings (PROVEN, on this set)
- Jev handles native-script input as well as romanised input. Its signal decisions on the 5 required signals plus bot question were all correct in native script: rushed 10/10, frustrated 10/10, confused 9/9, bot_question 5/5.
- Remaining misses in both scripts:
  - "ओके ओके" / "Ok ok" scored as interested (0.55–0.69).
  - One label dispute: "मैं ड्राइविंग कर रहा हूँ, बाद में कॉल करो" labelled hinglish, Jev said hindi.
- The known lexicon false positive is handled: "फिर से पूछ रहा हूँ, प्राइस बताओ वरना फोन रख दो" → confused 0, frustrated 1, interested 1. "फिर से बोलिए, आवाज़ नहीं आई" → confused 1.
- Adding native-script cue examples to the criteria changed nothing (49/51 either way). The current questions can stay.
- Latency is unchanged at ~500 ms p50 from the office VPN.

## Limits
- Small set (36 sentences), one run, written by us rather than real ASR output. Real ASR spelling variants and noise are untested.
- The "interested" threshold needs tuning for bare acknowledgements ("ok ok").
