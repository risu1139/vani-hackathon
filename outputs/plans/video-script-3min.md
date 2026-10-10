# VANI Persona Design: video script, 3 to 3.5 minutes (v2)

v2 merges the storyboard session's approved work (`outputs/video-storyboard.md`, `app/video/voice.py`): scenes 1 and 2 use its approved voice lines word for word; scene 3 (traits and states) and scene 4 (a persona for each seller) follow its scene 3 prototype and scene 4 draft. Source of every number: `outputs/plans/VANI_Persona_Design_Detailed_Doc_v6.md`. The demo calls are added after scene 9.

Rules: about 15 words on screen per beat; detail in the voice; at most one number per beat; never say "laptop"; the keyword tool decides mood in the call, Jev works between calls; do not show the voice changing mid-call (tone only); no "AI" or "bot" wording; no "best time to call" as a working feature; example sellers are invented. Voice: Sarvam Bulbul v3, speaker aditya, en-IN. The voice file spells for speech ("Vaani", "sixty-two", "G S T"); the screen keeps normal spelling. Pace of the approved voice: about 1.9 words a second with pauses, so about 380 spoken words for 3:20.

| # | Scene | Beats | Status |
|---|---|---|---|
| 1 | The gap | 6 | voice approved (storyboard session) |
| 2 | Rich context, no personal data | 5 | voice approved (storyboard session) |
| 3 | Traits and states | 4 | first two lines approved, rest draft |
| 4 | A persona for each seller | 5 | draft (storyboard scene 4) |
| 5 | The live call | 4 | draft |
| 6 | The agent decides, and the skill | 4 | draft |
| 7 | Mood engine | 2 | draft |
| 8 | The self-learning loop | 3 | draft |
| 9 | Close | 2 | draft |

## Scene 1: The gap

| Beat | On screen | Voice |
|---|---|---|
| 1.1 | IndiaMART knows each seller | IndiaMART knows a lot about each seller. Business, categories, past calls. |
| 1.2 | Objective: a meeting with an IndiaMART executive | Every call has one objective: a meeting with an IndiaMART executive. |
| 1.3 | Same voice. Every seller. Whole call. | But today, VANI speaks to every seller the same way, for the whole call. |
| 1.4 | Rushed seller: VANI does not change | When a seller is in a rush, VANI does not change. |
| 1.5 | Meetings: 26% → 14% | In these calls, meetings fall by half. |
| 1.6 | Persona: the bridge | We close this gap with a persona for each seller. |

## Scene 2: Rich context, no personal data

| Beat | On screen | Voice |
|---|---|---|
| 2.1 | 62 data points per seller | For each seller, we read 62 data points. |
| 2.2 | Business · catalogue · buy leads · competitors · past calls | Business. Catalogue. Buy leads. Competitors. Past calls. |
| 2.3 | Each one: a reason to meet | Each one gives VANI a reason to meet. |
| 2.4 | Personal data removed first | Before the model sees anything, personal data is removed. |
| 2.5 | Names → tokens. Phone, GST, PAN stay inside IndiaMART | Names become tokens. Phone, GST and PAN stay inside IndiaMART. |

## Scene 3: Traits and states

| Beat | On screen | Voice |
|---|---|---|
| 3.1 | Raw data → facts, by code | Raw data is not a persona. First, code converts the data into facts. |
| 3.2 | Traits: who the seller is | Stable facts are traits: business size, division, language. |
| 3.3 | States: what is happening now | Changing facts are states: buy-lead use, enquiry flow, mood on recent calls. Old signals fade. |
| 3.4 | Same data in → same facts out | The same data always gives the same facts. |

## Scene 4: A persona for each seller

| Beat | On screen | Voice |
|---|---|---|
| 4.1 | 7 persona styles | Our persona agent reads the data and picks one of seven persona styles. |
| 4.2 | Every choice cites seller data | It tunes pace, warmth and language, and every choice cites the seller's data. |
| 4.3 | Small town → warm · Busy → brief · Large → senior | A small-town trader hears warmth. A busy distributor, one line. A large manufacturer, a senior advisor. |
| 4.4 | 8 hooks: why meet us | The hook comes from the data too: a catalogue gap, or a live buyer. |
| 4.5 | Changes delivery. Never facts or prices. | It changes how VANI speaks. Never the facts or the prices. |

## Scene 5: The live call

| Beat | On screen | Voice |
|---|---|---|
| 5.1 | Start: voice, pace, language, opening | At the start, the persona sets the voice, pace, language and opening line. |
| 5.2 | "Abhi busy hoon" → one line + a callback | Then VANI listens. A busy seller gets one short line and a callback. |
| 5.3 | Confused → one idea · Marathi → VANI follows | A confused seller gets one simple idea. Switch language, and VANI follows. |
| 5.4 | Meeting booked with the seller's own executive | The meeting is booked with the seller's own executive. |

## Scene 6: The agent decides, and the skill

| Beat | On screen | Voice |
|---|---|---|
| 6.1 | Not a rule table | Not a rule table, where every seller type gets the same answer. |
| 6.2 | Scoreboards → top 2 → the agent picks | Scoreboards offer the two personas that worked for similar sellers. The agent reads this seller and picks. |
| 6.3 | 1 Seller evidence → 2 Earlier calls → 3 Default | Its skill puts the seller's own evidence first, then earlier calls, then the default. |
| 6.4 | No evidence? Refused. No call. | A validator checks every choice. No evidence, no call. |

## Scene 7: Mood engine

| Beat | On screen | Voice |
|---|---|---|
| 7.1 | In the call: keyword tool, under 1 ms | In the call, a keyword tool reads every turn in under a millisecond. |
| 7.2 | Between calls: Jev labels real turns | Between calls, Jev, a decision model, labels real turns and teaches the keyword tool. |

## Scene 8: The self-learning loop

| Beat | On screen | Voice |
|---|---|---|
| 8.1 | Call → review → outcome | After each call, Claude reviews it against our rules, and we record: meeting or not. |
| 8.2 | Credit persona, hook, each field → next agent reads it | The result is credited to the persona, hook and every field, and the next agent reads it. |
| 8.3 | 15% control calls measure real uplift | Fifteen percent of calls keep today's style, so we measure real uplift. |

## Scene 9: Close

| Beat | On screen | Voice |
|---|---|---|
| 9.1 | Next: objective and language per seller | Next, each seller gets their own objective and their own language. |
| 9.2 | Persona Design | A different conversation for every seller, and a system that learns from every call. |

Then: demo calls (added by the team at the end).
