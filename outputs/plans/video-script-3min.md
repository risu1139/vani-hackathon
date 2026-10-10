# VANI Persona Design: video script, 3 to 3.5 minutes (v1)

Replaces the 7-minute draft (`video-story-and-narration.md`) for the build. Source of every number: `outputs/plans/VANI_Persona_Design_Detailed_Doc_v6.md`. The demo calls are added after this script, at the end.

Rules: about 15 words on screen per beat; detail goes in the voice; at most one number per beat; never say "laptop"; the keyword tool decides mood in the call, Jev works between calls. Voice: Sarvam Bulbul v3, English. Pace about 140 words a minute, about 470 spoken words in total.

| # | Scene | Time | Words |
|---|---|---|---|
| 1 | The gap | 0:25 | 55 |
| 2 | Rich context, no personal data | 0:25 | 60 |
| 3 | A persona and a hook per seller | 0:25 | 55 |
| 4 | The live call | 0:30 | 65 |
| 5 | The agent decides | 0:25 | 55 |
| 6 | The skill | 0:20 | 45 |
| 7 | Mood engine | 0:20 | 45 |
| 8 | The self-learning loop | 0:30 | 65 |
| 9 | Close | 0:15 | 30 |
| | Total | about 3:15 | about 475 |

## Scene 1: The gap (0:25)

| Beat | On screen | Voice |
|---|---|---|
| 1.1 | One script, every seller | VANI calls sellers to get one thing: a meeting with an IndiaMART executive. |
| 1.2 | Same voice. Same words. | But today it speaks to every seller in the same voice, with the same script. |
| 1.3 | Rushed seller: 26% → 14% | When a seller is rushed, the chance of a meeting falls from about twenty-six to fourteen percent. |
| 1.4 | The seller changed. VANI did not. | The seller changed. VANI did not. |

## Scene 2: Rich context, no personal data (0:25)

| Beat | On screen | Voice |
|---|---|---|
| 2.1 | 62 data points per seller | For each seller we collect sixty-two data points from about sixty IndiaMART sources. |
| 2.2 | Business · catalogue gaps · live buy leads · competitors · past calls | Their business, their catalogue gaps, live buy leads, their competitors, and how past calls went. |
| 2.3 | Every data point: a reason to meet | Each one can give VANI a reason for the meeting. |
| 2.4 | Names → tokens. Phone, GST, PAN stay inside IndiaMART | Before the model sees anything, names become tokens. Phone, GST and PAN numbers never leave IndiaMART. |

## Scene 3: A persona and a hook per seller (0:25)

| Beat | On screen | Voice |
|---|---|---|
| 3.1 | 7 personas | From this data, each seller gets a persona: how VANI sounds. |
| 3.2 | Small town → warm, own language. Always busy → brief. | A small-town seller hears a warm voice in their own language. A busy owner hears one short line. |
| 3.3 | 8 hooks: why meet us | And a hook: the one reason to meet. A live order, a weak catalogue, unused credits. |
| 3.4 | Same engine. Different call. | Same engine. A different call for every seller. |

## Scene 4: The live call (0:30)

| Beat | On screen | Voice |
|---|---|---|
| 4.1 | Start: voice, pace, language, opening | At the start, the persona sets the voice, the pace, the language and the opening line. |
| 4.2 | "Abhi busy hoon" → one line + callback | Then VANI listens to every turn. Say you are busy, and it drops to one sentence and offers a callback. |
| 4.3 | "Samajh nahi aaya" → one simple idea | Say you did not understand, and it slows to one simple idea. |
| 4.4 | Marathi → Hindi: VANI follows | Switch language, and VANI follows, on the same turn. |
| 4.5 | Meeting booked with your own executive | At the end, the meeting is booked with the seller's own sales executive. |

## Scene 5: The agent decides (0:25)

| Beat | On screen | Voice |
|---|---|---|
| 5.1 | Rule table: same input, same output | How does it choose? Not with a rule table, where the same input always gives the same answer. |
| 5.2 | Scoreboards → top 2 personas | The scoreboards offer the two personas that worked best for similar sellers. |
| 5.3 | Agent picks persona, hook, 12 fields | Then an agent reads this seller's own data and picks the persona, the hook and every field. |
| 5.4 | Every choice quotes the seller's data | Every choice must quote the seller's data. |

## Scene 6: The skill (0:20)

| Beat | On screen | Voice |
|---|---|---|
| 6.1 | 1 Seller evidence → 2 Earlier calls → 3 Default | The agent follows a skill. For each choice: first the seller's own evidence, then what worked in earlier calls, then the default. |
| 6.2 | No evidence? Refused. No call. | A validator checks every choice. No evidence, or an unverified number, and it is refused. No call is made. |

## Scene 7: Mood engine (0:20)

| Beat | On screen | Voice |
|---|---|---|
| 7.1 | In the call: keyword tool, under 1 ms | In the call, a keyword tool reads each turn in under a millisecond, in Hindi, Marathi and Telugu. |
| 7.2 | Between calls: Jev labels real turns | Between calls, Jev, a decision model, labels real turns and teaches the keyword tool where it was wrong. |

## Scene 8: The self-learning loop (0:30)

| Beat | On screen | Voice |
|---|---|---|
| 8.1 | Call → review → outcome | After each call, Claude reviews it against our compliance rules, and we record the outcome: meeting or not. |
| 8.2 | Credit: persona, hook, each field, its reason | The result is credited to the persona, the hook, every field, and the reason behind it. |
| 8.3 | Next agent reads what worked | The next agent reads what worked for similar sellers, and decides again. |
| 8.4 | 15% control calls measure uplift | Fifteen percent of calls keep today's style, so we measure real uplift. No retraining, no hand-tuning. |

## Scene 9: Close (0:15)

| Beat | On screen | Voice |
|---|---|---|
| 9.1 | Next: objective, call time, language per seller | Next, each seller gets their own objective, best time to call, and best language. |
| 9.2 | VANI Persona Design | A different conversation for every seller, and a system that learns from every call. |

Then: demo calls (added by the team at the end).
