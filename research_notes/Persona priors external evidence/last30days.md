# last30days: voice agent persona tuning for outbound sales (external evidence)

Run: 2026-10-10, last30days v3.16.0, window 2026-09-09 to 2026-10-09.
Sources searched: Reddit (partial, timed out after 19 items), X (17), YouTube (11), HN (37), GitHub (10), Techmeme (1), arXiv (0), Digg (error). Plus 4 host WebSearch supplements.
Full engine dump: `~/Documents/Last30Days/voice-ai-agent-persona-tuning-for-outbound-sales-calls-raw-v3.md`.

Verdict up front: the last 30 days of social discussion has almost nothing on persona tuning with numbers. Most hard numbers come from web pages (vendor blogs, a July 2026 report), not practitioner threads. Treat everything below as weak priors.

## Synthesis

Legend: **[NUM]** = claim carries a number; **[ANEC]** = anecdote/opinion; **[VENDOR]** = number from a vendor marketing page (self-reported, unaudited); **[OUT-OF-WINDOW]** = older than 30 days.

### 1. Voice gender, pace, pitch
- **[NUM][OUT-OF-WINDOW]** Upfirst report (published 2026-07-31; 450,000 *inbound* calls, 503 AI receptionists): male vs female voice, greeting length and opening-question style showed **no measurable difference** in hang-up rate once other factors were controlled. AI settings (greeting, voice, training) explained only **~13%** of the variance in hang-up rates between businesses. Many hang-ups happen in the first seconds, before the AI has said much. Caveat: inbound, US SMB receptionists, not outbound B2B.
- **[ANEC]** Blog claim (via search summary): "female voices do better for appointment booking, male voices for technical support." No source data. Low trust.
- No practitioner post in the window reported a pace or pitch A/B test with numbers.

### 2. Opening hook / disclosure
- **[NUM][OUT-OF-WINDOW]** Upfirst: saying it is an AI up front was linked to **~20% fewer hang-ups**. "This call is recorded" was linked to **~30% fewer**. Opening with "the owner is unavailable" raised hang-up odds **~50%**. (Correlational, inbound.)
- **[ANEC]** r/AI_Agents, 2026-10-09, "Our voice agent says it's an AI in the first few seconds" (6 pts, 5 comments). Commenters back disclosure up front: "watching someone realize they were duped into a conversation is way worse than them just hanging up" (u/Informal_Eye_4849). Another cites a UK sales trainer's opener: "You might get mad, but this is a cold call. Do you want to hang up now or give..." (u/majesticjg).
- **[NUM][VENDOR]** Hamming AI guide: **40-60%** of outbound dials end in the first 10 seconds because the opener is wrong. Their advice: A/B test 3-5 opening variants in simulation first, then live.
- **[NUM][VENDOR]** SquadStack tracks the Abruptly Disconnected Rate (the share of calls cut in the first 10 s once the caller realises it is an AI). They claim **~10%**, against a human range of **8-12%**.

### 3. A/B testing method
- **[ANEC/VENDOR]** Harmony AI: split live calls 50/50 and change one variable per test (opener, objection handling or transfer trigger), never the whole script. Compare containment, transfer and booking rates.
- **[ANEC]** @nikkithashanker on X, 2026-09-24 (15 likes): "your conversion rate is lying to you". Outbound conversion depends on lead quality, offer, pricing and timing, so judging the agent on raw close rate is a mistake. This matters for us: compare persona arms only inside the same lead segment.
- **[ANEC]** r/aiagents, 2026-10-05, "Our voice agent resolved calls that weren't resolved" (18 pts). Teams dropped "call ended with agreement" as the success metric. They now use no repeat contact on the same issue within ~7 days plus explicit confirmation. The lesson: measure the outcome after the call, not how the call ended.
- **[ANEC]** r/aiagents, ElevenLabs vs Retell thread: test with messy calls (short answers, angry date corrections, interruptions) before you pick a stack.

### 4. Cold start and bandits
- No practitioner in the window reported running bandits on a voice agent persona or opener.
- **[ANEC/academic]** arXiv 2604.14961: LLM-predicted rewards for arms not yet played are injected into LinUCB as weighted pseudo-observations, which cuts cold-start regret. This maps directly onto "seed priors from a model, then learn from outcomes". There is also arXiv 2502.06358 (contextual-bandit prompt tuning for agents) and a 2025 survey of MAB plus LLMs (2505.13355).
- Indirect cold-start practice from vendors: simulate the variants first (Hamming), then go live with one variable at a time.

### 5. India / Hindi / Hinglish (Sarvam, Gnani, SquadStack, Bolna)
- **[NUM][VENDOR]** SquadStack: **50 lakh+ calls/day** for 60+ brands (another page says 40 lakh/day with **90%** lead connectivity). It claims a **93%** PoC success rate against **~25%** for the category, **2-3x** lower CAC than human teams, and says it is trained on ~600M minutes of Indian sales calls with native Hinglish code-switching.
- **[NUM][blog]** Indian landscape blogs (edesy, caller.digital): the cost floor for a competent Hindi agent in 2026 is **~35-55%** of what earlier contracts cost (Bulbul/Sarvam TTS, AI4Bharat open weights).
- **[ANEC]** @bolna_dev, 2026-10-09: promoting "Symphony", a Voice AI India event. No results data.
- No Sarvam, Gnani or Bolna practitioner post in the window shared persona or voice A/B numbers.

### 6. Other in-window items with numbers (low relevance)
- **[NUM][ANEC]** @JulianGoldieSEO on X: "followed up with 86 leads and closed 4 deals" overnight. This is a marketing post and unverified.
- **[NUM][blog]** "AI outbound conversation rates 45-60% with personalized scripts; 3x the conversion of email-only reactivation" (Brilo/JustCall-type stat pages). Unverified.

## What this means for VANI (my read, not from sources)
1. The only large-n evidence (Upfirst) says voice gender and greeting style barely move hang-ups, while disclosure and framing do. That fits our memory rule that voice gender should be outcome-driven with no quotas, and it suggests the opener/framing deserves more test budget than the voice timbre.
2. Measure persona arms against a downstream outcome (for example a callback, a lead purchase or a renewal within N days), not "call ended positively". Stratify by lead or seller segment so lead quality does not drive the result.
3. For cold start, the "LLM pseudo-observation" bandit pattern is the closest published analogue to seeding the decider's priors from data and then learning.
4. Indian numbers come only from vendors (SquadStack). There is no independent Hinglish persona A/B data in the window.

## Raw engine output (verbatim, relevant parts only)

```
🌐 last30days v3.16.0 · synced 2026-10-10
- Date range: 2026-09-09 to 2026-10-09
- Sources: 6 active (GitHub, Hacker News, Reddit, Techmeme, X, YouTube)
Warnings: digg failed; reddit partial (timeout after 19 items)

[reddit] Our voice agent says it's an AI in the first few seconds. Here's how people reacted
  2026-10-09 | r/AI_Agents | 6pts, 5cmt
  https://www.reddit.com/r/AI_Agents/comments/1x1sfa6/our_voice_agent_says_its_an_ai_in_the_first_few/
  u/Informal_Eye_4849: "the honesty-up-front thing is huge especially in real estate where reputation's everything. watching someone realize they were duped into a conversation is way worse than them just hanging up at the s..."
  u/majesticjg: "A sales trainer in the UK ... says straight up, 'You might get mad, but this is a cold call. Do you want to hang up now or give ..."

[x] @nikkithashanker 2026-09-24 [15 likes, 4 rt, 9 re]
  https://x.com/nikkithashanker/status/2103136454469914672
  "Outbound voice agents are going to be the next big revenue unlock for voice AI. And if you're building one, there is a chance your conversion rate is lying to you ... sales depends on more than the rep: lead quality, offer, pricing, brand, timing."

[reddit] Our voice agent resolved calls that weren't resolved
  2026-10-05 | r/aiagents | 18pts, 4cmt
  https://www.reddit.com/r/aiagents/comments/1wy3gd8/our_voice_agent_resolved_calls_that_werent/
  u/Worried_Garage8422: "we stopped tracking 'call ended with agreement' as a success metric ... no repeat contact on same issue for X days + explicit confirmation"
  u/QuanTradin: "seven day recontact on the same subject is the honest version of resolved."

[reddit] ElevenLabs vs Retell for Voice AI Agents
  2026-10-08 | r/aiagents | 6pts, 11cmt
  https://www.reddit.com/r/aiagents/comments/1x0mc98/elevenlabs_vs_retell_for_voice_ai_agents_since/
  u/curly_lighting: "throw as many messed up calls as you can at both before deciding. Short answers, people correcting dates while being angry, interrupting halfway through the confirmation"

[reddit] Anyone actually using an AI voice agent to pick up calls 24/7?
  2026-09-16 | r/smallbusiness | 66cmt
  u/littlelorax (7 upvotes): "if I hit an AI receptionist I also bounce. If I am calling, it is urgent and I need to talk to a human."

[x] @JulianGoldieSEO 2026-10-02 [11 likes] "followed up with 86 leads and closed 4 deals" (promo)
[x] @bolna_dev 2026-10-09 [14 likes] Symphony Voice AI India event promo
[youtube] PolyAI CTO Shawn Wen - "How a Voice Agent Learns the Rhythm of Conversation" (turn-taking model Dialog-RSN-1; adapting to the person on the line)
[youtube] Vaani AI platform walkthrough - voice selection, system prompts for B2B outbound
[hackernews] Show HN: VoiceGremlin - automated tests against AI phone agents (https://voicegremlin.com/)
[hackernews] "Jev for Voice Agents" - turn detection (https://veris.ai/blog/jev-turn-detection), 6 pts
[techmeme] Modulate raises $25M for voice models + emotion analysis (techcrunch, 2026-09-28)

---
✅ All agents reported back!
├─ 🟠 Reddit: 19 threads │ 481 upvotes │ 696 comments │ ⚠ partial after 19 items: Connection error: TimeoutError: The read operation timed out (run doctor for fixes)
├─ 🔵 X: 17 posts │ 171 likes │ 26 reposts
├─ 🔴 YouTube: 11 videos │ 1,829,934 views │ 5/11 with transcripts
├─ 🟡 HN: 37 storys │ 2,678 points │ 1,792 comments
├─ 🐙 GitHub: 10 items │ 1 reactions │ 6,111 comments
├─ 📰 Techmeme: 1 headline
├─ 🗣️ Top voices: @anthonycerullo, @JulianGoldieSEO, @agentcommunity_ │ r/AI_Agents, r/aiagents, r/LovingOpenSourceAI
└─ 📎 Raw results saved to ~/Documents/Last30Days/voice-ai-agent-persona-tuning-for-outbound-sales-calls-raw-v3.md
---
```

Dropped as off-topic: OpenClaw/Hermes threads, Suno song agent, SQL-agent accuracy post, Anthropic voice-data news, generic "AI teammates" posts, n8n/Bland/Retell tutorials without results.

## WebSearch supplements

- **Upfirst report via NewsBytes / LatestLY** (newsbytesapp.com, latestly.com): 2026-07-31, 450k inbound calls. Voice gender, greeting length and question style had no measurable effect. Disclosure was linked to ~20% fewer hang-ups, the recording notice to ~30% fewer. Settings explain ~13% of variance.
- **Hamming AI** (hamming.ai/resources/voice-agent-ab-testing-guide): prompt experiments, canary gates, split tests. 40-60% of dials end in the first 10 s; A/B 3-5 openers.
- **Harmony AI** (harmony.ai/blog/how-to-a-b-test-voice-ai-agent-scripts): 50/50 split, one variable at a time.
- **SquadStack** (squadstack.ai): 50 lakh+ calls/day, 93% PoC success, 2-3x lower CAC, ADR ~10% vs human 8-12% (vendor).
- **arXiv 2604.14961** (arxiv.org): calibration-gated LLM pseudo-observations for contextual bandits, aimed at cold start.
- **edesy.in / caller.digital / zartek.in**: India landscape; Hindi agent cost floor ~35-55% of earlier contracts.
