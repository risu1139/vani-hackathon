# First look: 5 "AI Roleplay" sales-call recordings (2026-10-10)

**Source.** Drive folder "AI Roleplay - Call Recordings": 30 files, about 2.5 h. Local copy in git-ignored `data/roleplay_recordings/`.
- Transcribed and translated with the Sarvam real-time STT and STT-translate endpoints on the new key (`saarika:v2.5`, `saaras:v2.5`), in 25-second pieces. Script: `app/spike/transcribe_chunks.py`.
- 5 recordings were done (about 26 min of audio, 66 pieces, about 4 min wall time). One per scenario code (RA, RS, MM, SV) plus one without a code.
- Executive and customer names are left out. The customers look like simulated personas.

## What the recordings are
**Seller-side meeting-setting calls.** In every call an IndiaMART executive calls a seller business (machinery, T-shirts, air coolers and LEDs, steel/TMT, a "company listed on IndiaMART"). The goal of each call is a 5–30 minute meeting, physical or online. The customer is a skeptical, pushy persona that keeps asking for specifics. This looks like role-play training: executives practising against an AI customer.

## Two pitch types seen
| | Profile-gap pitch (NSD-like) | Buy-lead / grievance pitch (CSD-like) |
|---|---|---|
| Recordings | RS, SV, uncoded (free sellers: "I'm registered, it's free"; "profile same for 2 years") | RA (seller already consumes leads); MM (seller says no enquiry in 2 months, and asks what changed since executives visited before) |
| Hook | Profile incomplete: photos, products, location, GST not verified, so buyers can't see you; demand in your category | Lead consumption and quality: "I check enquiries but many are irrelevant / price-only / far away / not serious"; teach shortlisting so the platform recommends better leads; verified buyers |
| Ask | "5–10 min, I'll come and complete your profile + portal overview" (fallback: online meeting) | "5 min meeting, I'll show you how to consume / shortlist leads" |

## Seller objections (all 5 calls)
1. "Tell me on the phone, why a meeting?" Seen in every call, often repeated.
2. "I'm busy."
3. "What's different this time / what changed since your executive came?" This is the past-grievance case.
4. "Prove it: which buyers, from where, which product; numbers; ROI; a named example."
5. "Are the buyers/leads verified, or just general enquiries? Many leads are poor quality."
6. "Nothing is free" / "I'm already on other platforms; it didn't help."

## What the executives did badly (to avoid in VANI)
- Vague claims: "buyers ready with advance payment", "20 buyers become 50". The seller pushes back each time.
- Numbers that the seller can't check: a platform-size claim; a named "example company" with "2–3 customers a month".
- They repeat "5 minutes" without answering the actual question. Calls stall in loops on "why a meeting".
- They mention plans and pricing early ("I will also tell you about the plan"), against "never say sales".

## What this means for VANI
- **The CSD-type hook needs the seller's buy-lead data.** That means leads bought and consumed, credits lapsed, not-interested reasons, buy-lead AOV vs category AOV, and enquiry response. All of these are in our seller context (E04–E07, E10).
- **Every specific claim must come from `verified_facts`.** The persona's objection playbook must answer "why a meeting" with a concrete, true reason: a profile gap, a lead-quality fix, or a category-demand number.
- Objection order to prepare: why meeting → busy → what's different / past grievance → proof → lead quality → cost.
