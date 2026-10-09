# NSD vs CSD: two different VANI pitches

Sources: [[2026-10-10-nsd-csd-pitch-input]] · [[2026-10-10-sarvam-prompt-template-example]]

**Answer.** VANI's Objective and phases depend on which division owns the seller (as of 2026-10-10, from the user):
- **NSD (new sales):** free sellers. The goal is a meeting that leads to a package sale. VANI never asks for the meeting directly. It opens with a profile-based **hook**: "this is your MCAT / product", "your competitors earn a lot here". The meeting is framed as profile help, not sales.
- **CSD (customers):** sellers who already bought a package. The call checks whether they use buy leads and whether their profile is good; a profile score helps to connect. **The call's goal is also a meeting, not an upsell** (user, 2026-10-10). The upsell happens in the meeting. The CSD pitch script is pending (the user will share CSD call recordings).
- **Both divisions:** VANI's call objective is to get a meeting. Selling or upselling is never VANI's job on the call.

## How we know the division

The seller-context `vertical_name` / `tele_vertical` fields (H02) name the owning team. On the 10 demo sellers: NSD (Top Cities, Emerging Markets, Registered Supplier) ×5, all free; CSD ×1; Tele-Monthly Welcome ×3 and KCD ×1, all paid. Which pitch TMW and KCD get is open.

## NSD objective: the enrichment-meeting pattern

1. **Opening:** greet by name with "ji", say it's IndiaMART, give the reason (profile update + portal overview), and name one concrete gap seen in their catalogue (for example missing product or shop photos means fewer buyer calls).
2. **Agenda:** a selective initiative ("only N selected profiles this month"), plus three help items: profile setup (photos, category, keywords), portal training (enquiries, which are genuine, how to reply), visibility (verify and improve).
3. **Commitment:** a short face-to-face meeting (about 30 min) at a proposed slot.
4. **Objections:** "no package / no spending" → only fixing the free profile; "busy, tell me on the phone" → it has to be shown, not told, so fix a time; "I'll add photos myself" → we know the algorithm's keywords, plus the portal overview.
5. **Language rule:** never say "sales". Say service, verification, profile update, support, cataloguing.
6. The meeting itself (done by the executive, not VANI): free value first, portal overview, show competition, pivot to a paid feature, let them ask.

## Changes needed before VANI can use it

- **VANI is an AI.** It can't say "main aapka dedicated Account Manager hoon" or "main personally aakar". It must say an IndiaMART executive or account manager will visit. The AI disclosure and the "never claim human" rules stay ([[sarvam-prompt-template]]).
- **Every claim must be true for this seller.** The catalogue gap, "only 500 selected companies", and competitors' years and amounts must come from `verified_facts`, or be dropped. The data for gaps exists: CQS, catalogue health, missing photos/prices, profile sections (C08), category value and AOV (E09/E10), nearby competitors (E08).
- **"Sir" is hard-coded.** Use "ji" unless a salutation is recorded.
- **Meeting time:** VANI may propose a slot, but scheduling belongs to the scheduling agent.
