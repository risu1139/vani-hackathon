# VANI Persona Design: video story and narration (draft 1)

Source of every number: `outputs/plans/VANI_Persona_Design_Detailed_Doc_v6.md`. Visuals follow the deck (`VANI_Persona_Design_Deck_v2_visual.pptx`): IndiaMART template, one diagram per scene, at most one number. Voice-over: Sarvam text-to-speech. Length about 7 minutes (about 950 spoken words at 140 words per minute).

Wording rules: never say "laptop"; Jev works between calls (it labels real calls between calls, it is not in the live call); the keyword tool decides mood in the call.

## Act 1: the business story (about 2:30)

### Scene 1: The problem (0:30) | deck slides 2 to 3
Visual: one script fans out to five sellers; a clock shows a rushed seller; the numbers 26% and 14% slide in.
Narration: "Every day, VANI calls sellers to get one thing: a meeting with an IndiaMART executive. But today it speaks to every seller in the same voice, with the same script. Some sellers are busy, some are confused, some prefer their own language. When a seller is rushed, the chance of a meeting falls from about twenty-six percent to fourteen percent. The seller changed. VANI did not."

### Scene 2: What we know about each seller (0:30) | slide 4
Visual: a seller circle; data points fly in from around it; names turn into tokens; a shield over phone, GST and PAN.
Narration: "We give VANI what it never had. For each seller we collect sixty-two data points from about sixty IndiaMART sources: their business, their catalogue gaps, live buy leads, their competitors, and how past calls went. Each data point can give VANI a reason for the meeting. Before the model sees any of it, personal data is removed. Names become tokens. Phone, GST and PAN numbers never leave IndiaMART."

### Scene 3: Personas and hooks (0:45) | slides 5 to 7
Visual: seven persona cards; four seller types each light up a different persona and a different hook.
Narration: "From this data, VANI builds a persona for each seller. There are seven starting points: a warm local helper for a small-town seller, a brief persona for someone always busy, a senior advisor for a high-turnover owner, a problem-solver for a seller with a complaint. And every call has a hook, the one reason to meet: a live order, a weak catalogue, unused credits, falling enquiries, similar sellers. The same engine, a different call for each seller."

### Scene 4: One call, start to end (0:45) | slides 10 to 11
Visual: a call timeline; speech bubbles "I'm busy", "samajh nahi aaya", a language switch; VANI's reply changes on the same turn.
Narration: "At the start of the call, the persona sets the voice, the pace, the language and the opening line. Then VANI listens on every turn. Say you are busy, and VANI shortens to one sentence and offers a callback. Say you do not understand, and it slows down to one simple idea. Switch from Marathi to Hindi, and VANI follows, on the same turn. At the end, the meeting is booked with your own sales executive."

## Bridge: the demo (about 1:00) | slide 17
Visual: two or three call clips with the switch log beside them. Decision pending: real recordings (redacted) or re-staged calls with a scripted seller.
Narration: "Here is a real call. Watch the moment the seller says they are busy."

## Act 2: the technical depth (about 2:30)

### Scene 5: The agent decides (0:30) | slide 8
Visual: a rule table on the left (same input, same output) crossed out; on the right the chain data, scripts, scoreboards, agent, validator.
Narration: "Now, how does it decide? Not with a rule table, where the same input always gives the same output. An agent reads this seller's own data. Scripts compute the facts and the safe limits. The scoreboards offer the two personas that have worked best for similar sellers, drawn at random so we keep learning. Then the agent chooses the persona, the hook and twelve fields, and for every choice it must quote the seller's own data."

### Scene 6: The skill (0:30) | slide 9
Visual: the three-step reason ladder, then the seven skill steps, with a validator stamp.
Narration: "The agent follows a skill with seven steps. For every field it picks a reason in order: first, evidence from this seller; second, what worked for similar sellers in earlier calls; last, the persona's default. A single writer tool and a validator enforce this. If a choice has no evidence, or a number is not a verified fact, it is refused and no call is made."

### Scene 7: The architecture (0:30) | slide 15
Visual: a left-to-right pipeline: seller data, builder, safe export, agent in an isolated sandbox, Sarvam voice agent, review.
Narration: "End to end, seller data is built into one folder per seller and exported without personal data. The persona agent works inside an isolated sandbox and sees only tokens. The validated persona becomes the variables of a Sarvam voice agent, and real names are filled in only at call time. During the call, three tools run: start, signal and booking."

### Scene 8: The mood engine (0:30) | slide 12
Visual: a seller turn splits to two lanes: an instant keyword tool into the call, and Jev into a labels box, labelled "between calls".
Narration: "Mood is decided in two layers. In the call, an instant keyword tool reads each turn in Hindi, Hinglish, Marathi and Telugu, in under a millisecond, so VANI can change on the same turn. Between calls, Jev, a decision model, answers six mood questions about real call turns. Its labels score the keyword tool and teach it where it is wrong."

### Scene 9: The self-learning loop (0:45) | slides 13 to 14
Visual: the ring: call, review, outcome, update, brief; six tiles of what the loop learns; a control group at fifteen percent.
Narration: "And VANI keeps learning. After each call, Claude reviews it against our compliance rules, and the outcome, meeting or not, is credited to the persona, the hook, every field and the reason behind it. Next time, the agent reads what worked for similar sellers. Fifteen percent of calls use today's style as a control, so we measure real uplift. No retraining, no hand-tuning. A person approves any change to the library or the keyword tool."

## Close (about 0:30) | slide 16
Visual: future-goal tiles; a small "honest limits" strip.
Narration: "Next, the objective of each call will be chosen per seller: a meeting, catalogue enrichment, or a satisfaction check, along with the best time to call and the best language. The scoreboards start empty today, so they will improve only as real calls arrive. Same seller data, a different conversation for each seller, and a system that learns from every call. That is VANI Persona Design."

## Open decisions
1. Total length: about 7 minutes, or a shorter cut for the hackathon limit.
2. Voice-over language: Indian-English, Hindi, or English with Hindi call snippets.
3. Demo clips: real recordings (redacted) or re-staged calls.
4. Production owner: the storyboard session builds visuals and the MP4; this file is the narration and scene plan.
