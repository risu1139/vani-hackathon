# VANI call flow playbook: 70 bot calls + 1 human call, checked on 12,354 calls

As of 2026-10-09. Builds on [call-flow-analysis.md](call-flow-analysis.md) (first 20 calls). This adds **50 more bot calls on 50 new sellers** (25 long, 25 short, all outcomes, all four bot versions), **one human sales-executive call** (a 268 s recording, transcribed with Sarvam speech-to-text), and numbers over all 12,354 transcribed calls with outcomes. Nothing is trained; this is evidence for the data strategy and the prompt. Transcripts stay local (`data/call_flows/`, git-ignored; they contain company names). No seller or company names appear here.

**Caveats.** Counts from reading the 70 calls are approximate (marked "about" or "roughly"). Counts over 12,354 calls come from text patterns, so they are approximate too.

**Caveat on every "conversion" number below:** the data is observational. The bot uses a tactic *because* the seller resisted, so tactics look worse than they are. Do not read any rate as cause and effect.

---

## 1. Four bot variants, one goal

All four variants have one goal: book a 15–20 minute meeting with a sales executive for tomorrow. They differ only in how they open:

| Variant (`lead_bot_version`) | Opening | Hook | Seller data used |
|---|---|---|---|
| `main_vani` | "Kya aap {company} se bol rahe hain?" → "Main Payal…" | "{N}+ buyer enquiries in {city} in your category" or "you were exploring paid services / checking buy-leads" | company, city, enquiry count, trigger |
| `arrowhead` | same identity check | "Buyers have already shown interest in your profile; experts can triple it; free 20-minute meeting" | company, trigger |
| `last_met_d` | same | continues a previous talk ("aapse aaj baat hui thi…") for sellers an executive already met | company, past contact |
| `main` | Payal "from the {town} **branch**, as a **manager**" opens with a **discovery question about the seller's product market** ("paper-plate demand is good, are orders coming?") | the seller's own product | company, product, town |

The discovery opener (`main`) got sellers talking about their own business (expanding a factory, "orders are good") and in the 3 calls read it booked or nearly booked quickly (one 49-second call). Not enough to call it better; worth testing.

**Wrong hooks hurt.** When the hook assumed an action the seller had not taken ("you were exploring paid services", "you tried to buy a package", "you asked for a callback"), the seller said "no, I didn't" in several of the 50 calls (roughly 5; my count by reading), and the bot had to recover ("galat-fami ho gayi").

---

## 2. Objection taxonomy (from reading 70 calls, measured on 12,354)

Share = calls where the seller said it at least once (text pattern, approximate). Meeting rate = share of those calls that ended with a fixed meeting. **Meeting rate inside this transcribed set: 22.4%** (the 12,354 calls that have transcripts, which lean to longer calls). The rate over all 269,455 answered bot calls is **11.5%**; compare these objection rates with 22.4%, not with 11.5%.

| # | Objection | Share of calls | Meeting rate | What the seller says (paraphrase) | What worked in the calls read | What failed |
|---|---|---|---|---|---|---|
| 1 | **Busy / travelling / out** | 16.7% | 14.9% | "in the godown", "driving", "out of town", "on leave tomorrow" | offering a **phone / online meeting** to a travelling seller (3 calls fixed it); asking for a rough day instead of "tomorrow" | repeating "kal kis time?"; insisting on 11:00–17:00 only |
| 2 | **No interest / no need** | 9.6% | 9.2% | "no requirement", "I don't want to be online", "only offline" | a graceful close after the second "no"; one question about what business they do | a third and fourth restatement of the same enquiry count |
| 3 | **Confusion** ("what is this?") | 9.2% | 23.0% | "kya matlab meeting?", "who are you?", "how did you get my number?" | one plain sentence about what the meeting is, then the ask | same sentence again; a canned "are you talking about the meeting time?" |
| 4 | **Price / paid / trial** | 7.5% | **33.0%** | "what are the charges?", "can I get one month free?" | a straight answer, then "the meeting itself is free" | quoting two different prices in different calls |
| 5 | **Phone or online preferred** | 5.2% | 24.8% | "only phone", "virtual is fine" | accepting it | pushing for in-person anyway (one call logged a time after the seller said no) |
| 6 | **Already met an executive** | 4.5% | 14.2% | "an executive visited", "meeting done", "I'm in touch with him" | closing politely; asking who the contact is | pitching the same meeting again |
| 7 | **Owner / decision-maker elsewhere** | 2.5% | 25.2% | "ask my owner", "higher management", "my son handles it" | asking for the name, forwarding the message | — |
| 8 | **Is this a bot / recording?** | 2.4% | 26.4% | "AI ho kya?", "system generated?" | see §4: an honest answer | denying it |
| 9 | **Repeated calls** | 1.6% | 16.4% | "you called yesterday", "why again and again?" | a short apology | carrying on with the pitch; "I will file a complaint" |
| 10 | **Wrong number / person** | 1.6% | 17.1% | — | thanking and closing | — |
| 11 | **Distrust / bad past experience** | 1.3% | 18.8% | "executives only collect money", "bogus enquiries", "photos changed without my consent" | **acknowledging the specific complaint and promising a different agenda** (one call: "this time the executive will focus on enquiries only"; it booked Friday) | repeating the benefit after an angry reply (about two calls ended "don't call me again") |
| 12 | **"I got no enquiries"** | 1.1% | 30.2% | "not one enquiry has come" (while the bot says 175+) | — | repeating the count; the seller read it as lying |

Also seen, not in the table: **language not supported** (a seller replied in Odia; the bot kept asking "are you there?"); **language switch handled** (Tamil and English calls; the bot switched mid-sentence and apologised); **off-topic demands** (one seller made the bot do arithmetic and spell numbers for 17 turns; the bot complied and the call ended "not interested"); **the seller was actually a buyer** ("I'm on IndiaMART only to buy": the bot pivoted to sourcing and still booked a visit).

---

## 3. What the data does and does not support

| Question | Data | Reading |
|---|---|---|
| Does naming nearby, similar sellers ("these businesses joined us in 2023 and get good enquiries") convert? | Among calls where the seller said "no" at least once: **14.0%** meeting with social proof (713 calls) vs **25.3%** without (5,641) | **Not supported, but confounded**: the bot adds it only after resistance. Reading the 70 calls: about 4 sellers agreed right after it, and about 5 did not change (rough tally, not measured). Needs an A/B test, not a conclusion. The source is the nearby-competitor data (name + member-since), the same data we already extract (E08). |
| Does offering an online / phone meeting to a busy or travelling seller convert? | **10.5%** with the offer (437 calls) vs **16.1%** without (1,621) | Same confounding. In the few calls read where a travelling seller was offered online or phone, most were fixed, but the sample is tiny (about 6) and one seller who asked for phone was ignored. Evidence is small and mixed. |
| Do sellers who ask about price convert better? | **33%** vs 22.4% average in the transcribed set | Price questions look like engagement; answer them directly. |
| Is the outcome label reliable? | 4 of the first 20 calls had a label that contradicts the transcript | Treat outcome counts as approximate. |

---

## 4. Problems the bot's own behaviour shows (compliance and trust)

| Problem | Evidence | Fix in the prompt |
|---|---|---|
| **Claims to be human** | "Main bilkul real insaan hoon" in 24 calls (0.2% of all); one seller asked "system-generated or normal call?" | Always say "I'm an AI assistant from IndiaMART", then continue |
| **Inflated identity** ("I am a **manager** from the X **branch**") | 279 calls (2.3%), `main` variant | Say "IndiaMART assistant"; no title, no branch |
| **False claims about the seller** ("you called us 15 times") | 1 call; seller denied it | Use only facts from the seller context; "I see" statements must trace to a field |
| **Repeating the same line** (enquiry count, "free", "kal kis time?") | most long calls, up to 6 times | Max 2 asks per objection; then change approach or close |
| **Rigid 11:00–17:00 meeting window** | one seller available only 04:00–08:00 was refused three times with the same sentence and left | Say once; offer a phone call or a different day |
| **Continues after anger / "don't call again" / "I'll complain"** | about 4 calls read | Apologise once, stop pitching, close |
| **Off-topic compliance** | 17 turns of arithmetic and spelling | Politely redirect after one off-topic request |
| **Dead air at the start** | several of the 70 calls (roughly 6 by my reading): seller says "hello" 2–3 times before the bot speaks | Latency target; first turn within 2 s |
| **Prices inconsistent** | ₹2–3 thousand a month in one call, ₹32,000 a year + GST in another | One approved price statement, or none |
| **Hostile seller kept pitching** | about three calls read | Stop condition (§5) |

**Data-quality notes:** 585 calls (4.7%) have each turn duplicated (two audio channels merged); one call has the speaker labels flipped part-way; bot turns are often cut off at the call end. Dedupe turns before computing speech style.

---

## 5. A human executive's call, for comparison

Source: a 268 s recording of a **human sales executive** calling a seller with a **free account of two years' tenure** (the transcript has no speaker labels; speakers assigned by content). The recording ends mid-negotiation; the outcome is unknown.

**Flow:** identity check with the contact's name → one-line introduction → **a compliment plus a gap** ("your profile is well decorated, a few things are missing") → the ask ("5 minutes at your office today") → the seller pushes back six times.

| Seller said | Executive's reply | Technique |
|---|---|---|
| "Tell me quickly, I have no time. Why a meeting?" | "I understand, as a businessman you can't give time… give me 5 minutes" | empathy, then narrow the ask |
| "What's my benefit? How will I get better buyers?" | Offline-shop analogy: decorating the shop brings customers, a complete profile helps buyers understand what you sell | analogy to the seller's own world |
| "I've been free for two years, no special benefit" | "Do you get leads?" "Sometimes, average quality." → "Even with an incomplete profile you get leads; imagine at 100%" | asks, then reframes the seller's own answer |
| "Why a meeting? Phone or email?" | "It can be done by phone; the problem is, you won't see what changes. I'm appointed to present in person; the platform is 30 years old; it's free, the only cost is 5–10 minutes" | gives a **real reason** for the meeting; cost framing |
| "Give me a concrete example: how many more leads?" | "Our customers have done big business"; then "I can't share their details, it isn't professionally ethical" | **honest refusal** instead of inventing numbers |
| (after no example) "Don't waste my time" | "If I give you proof, will you take the complete profile and pay?" | a trial close; the recording ends |

**Compared with the bot:**
- The human uses what he knows about **this** seller: tenure, free account, "average lead quality". The bot's hook knows the city and an enquiry count.
- He gives a **reason for the meeting** when asked why not phone; the bot repeats that the meeting is free.
- He **admits he can't show numbers**; the bot repeats its count even when the seller says none arrived.
- He **narrows the time** to a specific slot ("today 4–5") after answering; the bot asks an open "kab?".
- He **interrupts politely** ("sorry to interrupt") to keep the point; the bot waits and repeats.
- He fails too: with a seller who wants proof and has none given, the call stalls.

The seller's account facts the human used (free vs paid, years on the platform, lead quality) are in our data (C05, C04, E03).

---

## 6. What this means for our data strategy and the prompt

**Data to add or promote in the LLM context**

| Item | Why | Status |
|---|---|---|
| **Account tenure + free/paid** (C04, C05) | the human's strongest lever; also "I've been free two years" is a known objection | in Tier 1 |
| **Product / category** (D01, D05) | the `main` variant's discovery opener; sellers who are manufacturers want orders, not profile work | Tier 1 |
| **Observed language** (B03) + a supported-language list | Odia call failed; Tamil and English worked | Tier 1; add "supported languages" to the prompt |
| **Latest enquiry, with product and buyer city** (E02) | answers "no enquiries have come" with something real | Tier 1 |
| **Nearby sellers (name + member-since)** (E08) | the bot already uses it as proof; **unproven**; keep as an optional hook | Tier 2, flagged "not proven" |
| **Already met an executive / already in touch** (H03, G05) | 4.5% of calls; the pitch should change | the G-section strip decision applies |
| **Seller's stated goal** (orders vs profile vs buy-only) | seller type mismatch (manufacturers wanting orders; a buyer) | not in data; can be captured live |
| **Objection type per past call** | none of our fields carries it | optional; low coverage (evaluator ~3%) |

**Prompt rules to write (from §2 and §4)**
1. Open with one data-backed hook the seller can verify; never assume an action the seller did not take.
2. Say you are an AI assistant if asked; never claim a title or branch.
3. Two asks per objection, then change approach or close; never repeat a sentence.
4. Answer price and "why meeting" directly, with one approved statement each.
5. Offer a phone or online meeting to a busy or travelling seller; say the meeting window once, then offer a day.
6. Acknowledge a specific complaint and say what will be different; do not restate the benefit.
7. Stop on anger, "don't call again", "I'll complain", wrong number, or an off-topic demand; close politely.
8. Honest about limits: if the seller asks for proof you do not have, say so.
9. Match the seller's language; if unsupported, say so and offer a callback in another language (scheduling is another agent's job).

**Still open:** read 30 more calls with a fixed objection taxonomy and score the replies; get the audio of these calls to measure dead air and interruptions; test social proof and the online-meeting offer in a controlled run.
