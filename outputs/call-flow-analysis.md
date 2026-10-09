# VANI call flow: what 20 real seller calls show

As of 2026-10-09. Method: 20 transcribed VANI calls on **20 different sellers** from the PS07 data (`ps07_call_turns.csv` + bot-call outcomes). 10 long (150–500 s, 20–35 turns) and 10 short (0–44 s, 4–8 turns), spread over all four outcomes. Full transcripts: `data/call_flows/call01..20_*.md` (local, git-ignored, contain company names). Patterns were then checked on all 12,354 transcribed calls with outcomes.

The calls are **outbound sales calls to sellers**; the bot introduces itself as "Payal" from IndiaMART, speaks Hinglish, and always has one goal: **book a 15–20 minute meeting with a sales executive for tomorrow.**

---

## 1. The standard flow (every call follows it)

| Step | What the bot does | Typical timing |
|---|---|---|
| 1. Identity check | "Kya aap {company name} se bol rahe hain?" (uses the business name from the data) | 0–4 s |
| 2. Introduction + hook | "Main IndiaMART se Payal bol rahi hoon." Then a hook from data: **N+ buyer enquiries in {city} in your category**, or "you were exploring paid services / checking buy-leads", or "you asked for a callback about {product}" | 5–20 s |
| 3. The ask (in the same breath as the hook) | "Kal aap kis time 15 se 20 minute nikal sakte hain?" Median first ask at **6.8 s**; within 30 s in **88%** of calls that contain it | by ~20 s |
| 4. Seller reaction | one of five types (below) | 1–2 turns |
| 5. Handling | restate the hook, answer a question, or repeat the ask | rest of the call |
| 6. Close | confirm the slot, ask the meeting location / WhatsApp location, thank | last 15 s |

**The hook changes with the bot version and trigger, not with the seller.** `main_vani`: city + enquiry count ("145 से ज़्यादा buyer enquiry"). `arrowhead`: "buyers have already shown interest in your profile; experts can triple it; free 20-minute meeting". `last_met_d`: a variant for sellers an executive has already met. Within a version the script is the same for every seller (same voice, same name, same pace).

---

## 2. Seller reactions and what happened

| Seller reaction | Examples in the 20 | What worked | What didn't |
|---|---|---|---|
| **Passive yes** ("theek hai", "okay", "haan boliye") | 3 short calls | Meeting fixed in **36–44 s**: short hook, one ask, one time slot | — |
| **Clarification** ("kis baare mein?", "kya matlab meeting?", "aap kaun?") | 3 long calls | Restating in one simple sentence; explaining what the meeting is; confirming the profile name | Asking the same question again with the same words |
| **Price / trial question** ("charges kya hain?", "one month free trial?") | 3 long calls | Quoting a price range, then returning to "the meeting is free" → seller agreed; offering a lighter format (phone / virtual meeting) converted a seller who was busy | A price quoted differently in two calls (2–3 thousand a month vs ₹32,000 a year + GST) |
| **Objection from past experience** ("executives only ask for money", "bogus enquiries", "I already registered") | 2 long calls (1 angry) | Acknowledging privacy limits calmly (one call) | Pitching the same benefit again after the seller was angry → ended "not interested" and "don't call this number again" |
| **Deflection** ("busy", "owner is away", "on leave tomorrow", "call after 2 days") | 5 calls | Offering a callback and forwarding the message to the owner | A loop: the bot asked for a time **6 times** in one call while the seller talked about his stock |

**Long calls are not better calls.** They are long because of one of three things: the seller is negotiating (price, trial) and then agrees; the seller keeps asking what this is; or the bot loops on the same ask. 3 of 10 long calls ended in a fixed meeting; 2 were not interested.

---

## 3. Things in the flow that matter for personas

1. **One persona for everyone.** Same name, voice, script and Hinglish regardless of seller. The only adaptation in the sample is language: one call switched correctly into Tamil. This is what PS04 wants to improve.
2. **The moment of choice is the first 20 seconds.** The hook and the ask arrive together, before the seller has said anything. Sellers who did not follow the hook (confused, "who is this?") needed 3–5 extra turns.
3. **Seller state shows up in the first reply.** "Samajh nahi aaya" (confusion), "abhi busy hoon" (rush), "AI ho kya?" (bot question), "pehle bhi aaye the" (history) all appear in the first 1–2 seller turns and the bot's next line did not change in response.
4. **The bot's long first turn.** Openings run to 50–70 words in a single sentence (arrowhead); sellers frequently answered "hello?" or "ji" and nothing else.
5. **Callee.** Sellers often are not the owner ("owner kitta kettu solren", "my son handles"). The bot asks for the person by company name only. One seller forwarded the pitch to the owner and asked for a call in two days.
6. **Sellers ask for proof, not benefits.** "Pehle buyer se milwaiye", "give me the number of a seller who uses it". The persona that works here cites a concrete enquiry (product, buyer city) rather than a count.

---

## 4. Problems found in the calls

| Problem | Where | How common | Note |
|---|---|---|---|
| **Dead air at the start**: the seller says "hello" 2–3 times before the bot speaks | call 9 (bot first spoke at 13 s), call 1, call 4 | seen in 3 of 20 | QA matrix: dead air > 5 s is fatal |
| **Repeating the same ask** with the same words | calls 4, 9, 14 | the meeting rate does not rise after the 2nd ask in the full data (39% at 2 asks, 32% at 5+). This is correlational, not causal | the bot has no way to change tactic |
| **Canned clarification that does not fit** ("Are you talking about the meeting time or something else?") | calls 12, 14 | rare: **0.1%** of all calls | the seller gave a clear answer ("I am on leave tomorrow", "nothing") |
| **Possible denial of being an AI** ("Nahi main AI nahi hoon") | call 17 (seller asked "AI ho kya?", bot denied) | a seller mentions AI / bot / machine in **1.8%** of calls (227); a denial-like phrase appears in 70 of those (pattern match, needs reading) | compliance: the bot must be honest it is an AI assistant |
| **Price inconsistency** | calls 5 and 6 | 2 of 2 calls where price was discussed | FAQ Q5 guardrail |
| **Merged / duplicated turns** | call 10 (every turn appears twice, with overlapping timestamps) | one call in the sample | the data holds two audio channels merged; count turns carefully when computing speech style |
| **Truncated bot turns** ("…") at the end | most calls | very common | the bot's last turn is cut off when the call ends |
| **Outcome labels do not match the transcript** | call 7 (labelled Call Later / Busy, meeting actually fixed for tomorrow 12–2); call 13 (labelled Not Interested, seller only said "haan" and "hello"); call 20 (General, seller said "not interested"); call 6 (General, seller asked to consult the owner) | **4 of 20** | the outcome labels are noisy; counts built on them (outcome mix, "not interested" share) are approximate |
| **Night-time call** angered a seller | call 18 | one | scheduling is another agent's job, but it shows in the data |

---

## 5. What this means for our data and prompts

1. **Opening data to use:** the seller's business name (identity check), the city, and a **specific enquiry or product** as the hook. The data we already extract covers these (A02, B01, D05, E02, E01).
2. **State signals to surface to the LLM, early:** confusion, rush ("busy"), bot-question, "already met an executive", "owner decides", "already registered", "past experience with executives". Per-call signal rows (G11) cover rush, confusion, frustration, bot-question, not-decision-maker. **Missing from G11:** an `objection_type` label (price / trial / past experience / bogus enquiries / already registered). The evaluator `objections` output has this, but only for ~3% of sellers; the transcripts show it appears in most long calls.
3. **The persona levers visible in the flow:** brevity of the first turn, whether the hook is a count or a concrete enquiry, formality ("sir / ji" vs "ma'am"), language (Hindi, English, Tamil), whether to offer a lighter meeting format (phone / virtual), and when to stop pushing (angry seller, "don't call again").
4. **Guardrails the prompt must hold:** never claim to be human; one consistent price statement (or none); respect "don't call this number again"; do not loop the same question; say what the meeting is in one sentence.
5. **Evidence caution:** meeting rate by number of asks and the outcome labels are noisy; don't build persona claims on them without reading calls.

## 6. Open items

- Read 20–30 more calls with a **fixed objection taxonomy** to see which objection is most common and which reply works.
- Decide whether `objection_type` and "meeting format offered" become fields in the seller context (they come from calls, not from a seller profile).
- Pull the audio for the same calls (PS07 recording sample) to check dead air and interruptions, which transcripts cannot show.
