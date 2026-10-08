# /last30days synthesis - open-source voice AI agents for VANI (as delivered 2026-10-07)

Context: produced by Claude after running /last30days v3.16.0 (window 2026-09-07 to 2026-10-07) plus web supplements. Engine raw dump: [[2026-10-07-last30days-open-source-voice-ai-agents]]. Problem statements: [[2026-10-07-hackathon-deck-problem-statements]].

User constraints captured before research (Q&A, 2026-10-07):
- Q1 problem: open, recommend best fit.
- Q2 reuse: fork a near-complete repo (flagged: deck rule "Plagiarised or pre-built solutions are disqualified").
- Q3 stack: Sarvam for the voice agent; other LLM calls via OpenRouter; TypeSafe Jev for fast real-time decisions, with a training loop.
- Q4 team: mixed, 1 strong dev.
- Q5 Jev = TypeSafe "System One" model, https://typesafe.ai/blog/introducing-system-one-models-and-jev
- Q6 output: ranked picks + 1 recommendation.

Jev facts (typesafe.ai launch post): System One model for classification, routing, scoring, extraction; 70-500 ms end-to-end; 40-200x faster than frontier LLMs; $0.042/MTok input, output free; typed outputs defined by schema (no hallucinated labels); trained with "Reinforcement Learning for Calibrated Decisions (RLCD)"; early access from 2026-09-28 via typesafe.ai console; no open weights; no voice use cases in launch post.

---

What I learned:

**Jev's first voice-agent benchmark came out this week, and it used Jev to detect turn ends during the call** - Veris AI (veris.ai/blog/jev-turn-detection, 6 Oct, on HN) wired Jev into a Pipecat agent as a semantic turn detector. Jev reads the caller's words so far plus the agent's last line and returns a label in about 150 ms. The agent cut callers off on 11% of turns instead of 52%. But median reply time rose from 2.1s to 4.6s, and task completion didn't change (50 vs 53 of 300). So Jev is good at fast "what is happening right now" labels: is this seller frustrated, confused, rushed, or switching to Hindi? It should not write replies, and it should not block turn-taking. A community list, awesome-jev-projects (github.com/logicrw/awesome-jev-projects, 664 stars), already tracks Jev integrations.

**Most new voice agents are still built on Pipecat** - Pipecat 1.10 shipped on 12 Sep with MCP 2.x and turn-detection controls, and the Veris test ran on v1.12. Dograh (github.com/dograh-hq/dograh) is an open-source alternative to Vapi/Retell (BSD-2 licence) built on a forked Pipecat, with Langfuse tracing and a drag-and-drop call-flow builder. It supports 30+ languages including Hindi, and v1.20 added speech-to-speech. It's catching on with Indian creators: Yohita's ₹0/min self-hosted Hindi voice agent (youtube a8zQbgs7Ul8) has 10.5K views, and Shreyas Raj's free 4-hour course (youtube pucxyDS2lG4, 22K views) builds an outbound calling agent on it.

**Live calls are getting a separate voice per persona and emotion-aware context** - ferni-ai/voiceai PR #104 gives live calls "tools, memory models and voice-emotion context", after an audit of how human the calls sounded. PR #102 gives each persona its own voice and never drops a call when the cloned voice is refused. That is close to the Persona Design problem, except it runs on Gemini Live rather than Sarvam.

**Voice testing now runs on open-source simulated callers** - Egma and chanl-eval (both MIT licence) run simulated callers with personas against your agent and score each criterion pass/fail. That covers the "simulated sellers" test bed in the A/B problem and the grading loop in the Quality Audit problem.

**Sarvam had no new release this month** - the current stack is still Bulbul v3 (Feb 2026; 30+ persona voices, 11 languages, Hinglish, telephony-grade audio) and Saaras v3 for speech-to-text (23 languages). Top Fireship comment on the AI pace: "Im tired boss" (@YoavDoesntBass, 3,400 likes); "AI fatigue is real" (@A.T.D1).

Ranked by least change for the highest score:

1. Persona Design (#4), the recommendation. Every piece has a fresh reference: Pipecat or Dograh as the call pipeline (Pipecat should include Sarvam speech-to-text and text-to-speech services; confirm in the first hour), Bulbul v3's persona voices, Jev for the live switch signals, ferni-ai PR #102 and #104 as a pattern for swapping the voice mid-call, and the Persona dataset is already provided. It also scores best on Voice Experience (20%).
2. Quality Audit (#1). Jev grades every call Fatal or Non-Fatal; at $0.042 per million input tokens, auditing 100% of calls instead of a sample costs very little. An OpenRouter LLM groups failures into root causes and suggests prompt fixes; chanl-eval's per-criterion scorecards are the template. Strong, but the demo is a dashboard rather than a voice demo.
3. A/B Testing (#5). Egma's simulated callers plus Jev for tagging each call's outcome cover most of it. The statistics and auto-promotion take more custom code.

Memory (#2), Best Time to Call (#3) and Seller Enrichment (#7) gain little from this month's voice news; they are mostly data and ML work.

Plan for Persona Design (one strong dev):
- Pipeline: fork Pipecat's phone-bot example with Sarvam speech-to-text, OpenRouter for replies, and Bulbul for the voice.
- Persona generator: an OpenRouter LLM turns each seller row into a JSON spec covering speaker, pace, pitch, how much Hinglish to use, the opening line, and the objection playbook.
- Live switch: Jev classifies each seller turn as {frustrated, confused, interested, rushed, lang_switch, neutral}. It runs alongside the reply, not in front of it, which avoids Veris's 4.6s slowdown. When a label crosses a set threshold, swap the Bulbul speaker or pace and the system prompt, and write a line to the switch log.
- Training loop: an OpenRouter LLM labels past call turns from the dataset, and those labels tune Jev's thresholds against meetings fixed. Check on the TypeSafe console whether custom training is open; if not, the loop is threshold tuning only.
- Disqualification risk: Pipecat and Dograh count as frameworks, while the persona engine and switch logic are the team's own work. Don't copy ferni-ai's code; use it only as a pattern.

KEY PATTERNS:
1. Use Jev for fast labels during the call and an LLM for the actual replies; Jev is weakest as the turn-taking gatekeeper (Veris AI).
2. Pipecat, or Dograh on top of it, is the default base for forking a phone agent, including Hindi setups (Yohita, YouTube).
3. A separate voice per persona, with a fallback so the call never drops, is becoming standard (ferni-ai/voiceai).
4. Testing on simulated callers with personas has moved to MIT-licensed open source (Egma, chanl-eval).
5. The open-source agent space is busy, but little of it is about voice; most of the 30-day volume is coding and agent runtimes (r/AI_Agents).

Coverage: Reddit 25 threads, YouTube 3 videos, HN 12 stories, GitHub 22 items, Polymarket 1 market. X/Twitter not searched (no auth). arXiv, Digg, Techmeme returned 0.
