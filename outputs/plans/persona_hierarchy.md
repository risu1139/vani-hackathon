---
title: "VANI persona hierarchy: review document for Product"
---

**Status:** DRAFT for product review. Describes the code at commit `a8f2e06` (2026-10-10) and the approved design (`persona-skill-design.md` §9.2/9.3). Nothing in this document changes the code.
**Audience:** product manager. Technical names are in brackets for reference.

# 1. Decisions we need from you

| # | Question | Why it matters | Our recommendation |
|---|---|---|---|
| 1 | **What is the reward?** "Meeting fixed" on the call, or "meeting held" later? | The hierarchy learns from this one number. A fixed meeting is quick to count but can be soft. | Start with "meeting fixed"; add "meeting held" when it is available |
| 2 | **Build the deeper levels (state, category group) now, or wait for data?** | The scoreboards are empty. Deep levels need hundreds of calls per cell before they say anything. | Wait. Keep the three levels that exist; revisit after the first few hundred real calls |
| 3 | If we build it: **which field is "category group"?** | The seller's top category group, or the group of the category in the call hook? | The seller's top category group (one stable value per seller) |
| 4 | **Is a 15% holdout on the current default style (P0) acceptable?** | About one call in seven uses the old style so we can measure uplift honestly. | Yes. This is the only clean baseline we have |
| 5 | **Voice: keep the female-first default?** | Team decision plus weak outside evidence. Our own data has none yet. | Keep, with a small extra lean for tense or rural calls, and let data change it |
| 6 | **Who approves persona-library versions?** | The library (7 personas) is v0, approval pending. | One named owner (product or Rishav) |
| 7 | **Are the 7 personas the right set?** | Each persona is a starting point, not a rule. Too many personas splits thin data. | Keep 7 for the demo; prune after data |

# 2. What the hierarchy does, in plain words

Before every call, VANI must choose a **persona** (how it speaks) and a **voice** (female or male). We do not hardcode the answer. Two **scoreboards** hold the results of past calls and suggest a starting point:

- **Scoreboard A: persona.** For this seller, which of the 7 personas (P0 to P6) has worked best for similar sellers?
- **Scoreboard B: voice.** Which voice works best for similar sellers?

"Similar sellers" is defined by a **hierarchy** of groups, from the whole base down to narrow segments. A narrow group with few calls borrows strength from the wider group above it. This is called **partial pooling**: the more calls a group has, the more its own results count.

The persona agent (Claude) then takes the top two suggestions, picks one, and may adjust it from a fixed menu (for example "a little faster" or "more formal"), each adjustment justified by the seller's own data. The scoreboard never decides alone.

**Starting point each time:** with empty scoreboards, every pick is the starting leans plus a random draw. This is expected at the beginning.

# 3. Persona hierarchy: levels

Each level narrows the group. A level with too few calls falls back to the level above it.

| Level | Group | Fed by (seller fact) | Why this level exists | Status |
|---|---|---|---|---|
| **L0** | All sellers | none | A safe fallback; always has data | Built |
| **L1** | Division | Division: NSD (free) or CSD (paid) [`trait.division`] | The two divisions have different goals and objections | Built, nested |
| **L2** | Turnover band | Annual turnover band [`trait.business_scale`] | Small and large sellers respond to different styles | Built, nested under division |
| **L3** | AOV tier | Seller's average order value vs the category: low, mid, high [`trait.business_scale`, AOV tier] | Order size shows how much a seller cares about big deals | Partly built: a flat adjustment, not nested |
| **L4** | Zone | Region from the seller's state: North, West, South, East, Central [`trait.city_tier`, state] | Language and style differ by region | Partly built: a flat adjustment, not nested |
| **L5** | State | The seller's state | Finer regional behaviour; falls back to its zone | **Not built** |
| **L6** | Category group | Seller's top category group [catalogue point D01] | Industries talk differently; falls back to division | **Not built** |

**Fallback rule:** a group with few calls uses the parent level's result; as calls arrive, its own result takes over. The strength of this pull is **κ = 20** (a group counts as 20 imaginary calls of the parent's average before its own calls outweigh them).

**Why L5 and L6 are not built.** The design needs them, but a review item (M12) cut them for the hackathon: with 7 personas and a baseline meeting rate of about 11 to 22 percent, a narrow group needs hundreds of calls before its result means anything. Today we have none.

# 4. Persona selection: how a choice is made

1. **Score** each persona: start from the baseline (0.12 meeting rate), add the weak starting leans below, then update with real outcomes level by level.
2. **Draw** with Thompson sampling: a random draw weighted by how well each persona has done. This keeps exploring promising personas while using the best one. The chance each persona is best is recorded for every decision, so credit can be given correctly later.
3. **Holdout:** 15% of the time, use **P0** (the current production style) to measure uplift.
4. **Hand the top two** to the persona agent, which picks one and may amend it with cited reasons.

**Starting leans** (weak, from a seed table; the loop overrides them): NSD leans P2/P3; CSD leans P1/P5; turnover 0–40 L leans P2/P4; 40 L–1.5 Cr leans P1/P4; 1.5–5 Cr leans P1; 5 Cr+ leans P6/P1; high AOV leans P1/P6; low AOV leans P2; North leans P4; South and East lean P2. These are guesses marked as such; they are not rules.

# 5. The seven personas (library v0, approval pending)

| ID | Name | Fits | Style in one line |
|---|---|---|---|
| P0 | VANI default (control) | Baseline for measurement | Natural Hinglish, polite, direct, two sentences |
| P1 | Numbers-first advisor | Mid/large turnover, active buy-lead users | Leads with one concrete number; confident, specific |
| P2 | Warm local helper | Small sellers, small towns, regional language | Speaks in the seller's language; simple words; frames the meeting as help |
| P3 | Patient guide | Previously confused, low digital use, first contact | Short phrases, one idea at a time, checks understanding |
| P4 | Brief and busy-friendly | Often rushed, high call fatigue | One short sentence; value first; offers a callback at once |
| P5 | Respectful problem-solver | Open grievance, frustration (mostly paid sellers) | Acknowledges the problem once; never repeats the old pitch |
| P6 | Respectful senior advisor | 5 Cr+ sellers, high order value | Business-like, mostly English, brief, never pushy |

# 6. Voice hierarchy (female or male)

| Level | Fed by | Role |
|---|---|---|
| **V0** base | Team decision | Female-first starting prior (female 0.13 vs male 0.11) |
| **V1** seller gender | Recorded gender, else a weak name-based guess | Small adjustment. Used only to choose the voice; never mentioned on the call |
| **V2** city tier | Metro, tier-2, small town or village | Small adjustment; rural leans female |
| **V3** tension | Recent call mood: frustrated, rushed, open complaint | Tense calls lean female (weak outside evidence) |
| Hindi belt | State in the Hindi belt and rural | Fixed lean today; **not yet learned** from data |

Voice has **no outcome data of our own yet**, so these are starting priors that the loop will test.

# 7. What the system learns, and what it does not yet

| Learning step | Status |
|---|---|
| Add each call's outcome to the built levels (all, division, band, zone, AOV, voice keys) | Built |
| Draw with exploration and record the chance each persona is best | Built |
| Measure uplift against the P0 holdout | **Not built** |
| Suggest winning amendments (adjustments that correlate with meetings) | **Not built** (amendments are only logged) |
| Learn which hook works for which segment | **Not built** (the hook is not logged in the loop) |
| Deeper levels: state and category group | **Not built** |

# 8. Evidence strength: what to trust

- **Hook style (PS07 bot-version experiment):** the default "enquiry-count" opening beats the "interest" and "discovery" openings by a small but significant margin overall. Only 13 of 73 segment rows are statistically significant. Treat most segment preferences as weak.
- **Voice, pitch, formality:** no data of ours; outside field studies only (weak).
- **Persona starting leans:** guesses until the scoreboards fill.
- **The baseline meeting rate** in past bot calls is **11.5%** over all 269,455 answered calls (22.4% among the 12,354 calls that have transcripts).

# 9. Proposed change for review

We propose to keep the hierarchy in **one reviewable file** (`references/hierarchy.json`) that both the prior and the learning step read, so no level list lives only in code. The file would hold the seven persona levels with their fact sources and bucket rules, the voice levels, the pooling strength, the holdout rate, the base means, a version, an approval field and a changes log. A test would check that the keys the loop writes equal the keys the prior reads. **No code change happens until you review this document.**

*Sources: `persona-skill-design.md` §9.2/9.3, `persona-e2e-plan.md` §9 (M10 to M13), `references/persona_library.json`, `references/evidence/hook_priors.json`, `scripts/prior.py` and the persona session's status report of 2026-10-10.*
