# Success metrics: data collection (for the animation after the demo)

Status: draft 2, 2026-10-10. Part A comes from the code; part B from the persona session's run data and the committed mid-call test files. Aggregates only, no seller names.

## A. How we decide persona and hook from seller data

The rule is: **scripts compute facts, the agent judges, the validator checks**. The tables below are the facts and the starting rules. The agent may depart from a starting rule only with a cited reason.

### A1. Seller facts (traits = stable, states = changing) | `scripts/facts.py`

| Fact | How it is read from seller data | Used for |
|---|---|---|
| Business scale | Turnover: small below 40 L, mid 40 L to 5 Cr, large above 5 Cr; one step up if the seller's order value is more than 2× the category's | Sophistication, formality, persona fit |
| High value | Turnover 5 Cr+ **or** seller order value in the category's top quarter | English start, senior advisor (P6) |
| Division / plan | custtype paid = -1 → paid (CSD path; TMW and KCD too), else free (NSD) | Allowed hooks, seed lean |
| Catalogue strength | Weak: quality score below 40 or over 20% of products without photo or price. Strong: score 70+ with no gaps | Profile-gap hook |
| City tier | Metro, tier-2, small town, village; Hindi belt flag | Voice gender, language, warmth |
| Language | Seller's state (and GST state), languages heard on past calls | Start language, code mix |
| Seller gender | Recorded value, else a guess with confidence (never said aloud) | Voice gender |
| Buy-lead use (state) | Lapsed if any credits lapsed; unused if none used in 30 days; low use if under 30% of allotted | Unused-credits hook (paid only) |
| Order value vs category (state) | Below if under 0.7×, above if over 1.3× | Numbers-first style, money hook |
| Lead quality (state) | Issue if 3+ rejected leads or a call says the leads are bad | Lead-quality hook (paid only) |
| Enquiry flow (state) | Falling if last month is under 0.7× the monthly average of the last quarter; rising if over 1.3× | Enquiry-drop hook |
| Call mood (state) | Signals from past calls (rushed, frustrated, confused, irate), weighted by age, half after 30 days | Pace, brevity, empathy, voice gender |
| Call fatigue (state) | VANI calls in the last 7 and 30 days; 3+ in 7 days is a guard | Short call, skip recommendation |
| Open grievance (state) | Open complaint, or a grievance in a call in the last 60 days | Problem-solver persona, grievance hook first |
| Peer position (state) | First peer group with 5+ same-size sellers who bought leads; ahead, level or behind | Peer-usage hook |
| Showcase lead (state) | Best live or recent buy lead with an order value | Money-lead hook (used first) |

### A2. Start rules (first match wins; the agent may override with evidence) | `facts.py start_rules`

| Field | Rule | Evidence grade |
|---|---|---|
| Voice gender | Female if the seller is female; female if the seller is tense (frustrated on calls, or open grievance); female for a rural Hindi-belt seller; default female | WEAK (outside field studies + team decision) |
| Language start | **High value (5 Cr+ or top-quarter order value) → English with light Hindi**; otherwise the regional language of the seller's state | Team decision, WEAK |
| Empathy | Add an acknowledgement line for an open grievance, frustration (score 0.5+), or rush / call fatigue | Team decision |

### A3. Personas and who they fit | `references/persona_library.json`

| Persona | Fits (from the data) | Sophistication | Code mix | Words per reply | Pace |
|---|---|---|---|---|---|
| P0 VANI default (control, 15% of calls) | Baseline | practical | Hinglish | 20 | 1.0 |
| P1 Numbers-first advisor | Mid or large turnover, mid or high order value, active buy-lead users | numbers first | Hinglish | 18 | 1.05 |
| P2 Warm local helper | Small sellers, small towns, regional language, free sellers needing profile help | simple | regional only | 15 | 0.95 |
| P3 Patient guide | Confused before, low digital use, first contact | simple | light Hinglish | 14 | 0.9 |
| P4 Brief and busy-friendly | Often rushed, call fatigue, short past calls | practical | Hinglish | 10 | 1.15 |
| P5 Respectful problem-solver | Open grievance, frustration, poor-lead complaints (mostly paid) | practical | light Hinglish | 16 | 0.95 |
| P6 Respectful senior advisor | **5 Cr+**, high order value, English-comfortable owners | numbers first | English heavy | 20 | 1.0 (pitch -0.1, formality high) |

Starting leans (prior only, overridden by outcomes): free sellers (NSD) lean to P2 and P3; paid sellers (CSD) lean to P1 and P5. Leans by turnover, order value and zone were dropped (no evidence); the loop learns them.

### A4. Hook eligibility (script) and choice (agent)

| Hook | Eligible when | Division |
|---|---|---|
| Money lead | A live or recent buy lead with an order value exists (used first) | Free and paid |
| Profile gap | Catalogue strength is weak | Free and paid (mainly free) |
| Category demand | Local or total buy leads in the seller's category > 0 | Free and paid |
| Unused credits | Buy-lead use is lapsed, unused or low; blocked by an open grievance or a stop request | Paid only |
| Lead quality fix | 3+ rejected leads or bad-lead talk | Paid only |
| Enquiry drop | Enquiry flow is falling | Free and paid |
| Peer usage | A peer group with 5+ same-size buyers exists | Free and paid |
| Resolve grievance | Open grievance (said first) | Free and paid |

Agent rules: a primary hook needs 3+ cites from 2+ files and a counter-evidence check; money first when a money lead exists.

### A5. Guards (script; the agent plans around them)
Do not call (no persona); asked to stop calling (apologise, close); met an executive in the last 3 days (no new meeting); call fatigue, 3+ calls in 7 days (short call, may skip).

### A6. Evidence behind the hook style | `references/evidence/hook_priors.json` (PS07 natural experiment)
The enquiry-count opening beat the "interest" opening by 0.52 points (n = 30,670, significant) and the "discovery" opening by 2.46 points (n = 5,571, significant). Only 13 of 73 segment rows are significant, so most hook preferences are starting points.

## B. Evidence per judging criterion

Source for B1 to B5: the persona session (seller-data-rebuild-redshift), 2026-10-10, computed from `data/runs_daytona/*/` (04_persona, 01_facts, ledger, validation) and 20 collected calls (06_call switch logs), template v12 or earlier. Sellers are labelled A to H; no names or ids.

### B1. Fit of each persona to its seller
9 current persona runs for 8 sellers. **Validator 9 of 9 pass**, in the sandbox and again outside it.

| Seller | Division | Turnover | Order value | City tier | State | Persona (top 2 offered) | Hook / backup | Language | Sophistication | Code mix | Words/turn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (2 runs) | Paid (CSD) | 0-40 L | mid | metro | Telangana | P2 (P3, P2) | unused credits / money lead | Telugu | simple | regional only | 15, 12 |
| B | Free (NSD) | 0-40 L | – | small town | Maharashtra | P0 control arm | category demand / money lead | Marathi | practical | Hinglish | 20 |
| C | Free (NSD) | 25-100 Cr | high | small town | Punjab | P6 (P2, P6) | money lead / profile gap | English | numbers first | English heavy | 20 |
| D | Paid (CSD) | 0-40 L | high | tier 2 | Gujarat | P1 (P6, P1) | money lead / unused credits | Hindi | numbers first | Hinglish | 18 |
| E | Paid (TMW) | 0-40 L | high | metro | Delhi | P4 (P4, P2) | profile gap / money lead | Hindi | practical | Hinglish | 10 |
| F | Free (NSD) | 0-40 L | mid | metro | Telangana | P3 (P3, P1) | category demand / money lead | Telugu | simple | light Hinglish | 12 |
| G | Free (NSD) | – | mid | – | Delhi | P4 (P2, P4) | money lead / category demand | Hindi | practical | Hinglish | 10 |
| H | Paid (CSD) | – | mid | – | Rajasthan | P3 (P2, P3) | category demand / money lead | Hindi | practical | light Hinglish | 11 |

- All 9 runs chose a female voice.
- Field reasons over the 9 runs: **33 from seller evidence**, 57 from the persona card, 0 from earlier-call data (the scoreboards are empty). Every field carries a reason. Cites per run: 13 to 24.
- Rule in action: seller C (25-100 Cr, high order value) → P6 senior advisor, English, numbers first. The agent overrides a start rule only with evidence: one high-value seller started in Hindi because past calls were answered in Hindi.

### B2. Correct, well-timed mid-call switches
- **15 scripted scenario calls: every intended switch fired on the same seller turn.** One miss was found and fixed: a Marathi "ho" (yes) was read as Hindi; fixed in template v10 and covered by unit tests.
- Separate earlier suite (W1, 14 calls, 42 turns): 16 of 16 same turn, 0 of 18 false switches on neutral turns (`outputs/midcall_tests/`).
- Signal-tool rows over 20 calls: neutral 39, language switch 12, question 9, rushed 4, ask handler 4, frustrated 2, declined 2, bot question 2, opt-out 2, interested 2, ask more 2, confused 1, end now 1.
- Speed: signal tool median **0.91 ms** (p95 1.44 ms, n = 82, code time); agent response per turn average **0.92 s** (0.71 to 1.14 s, Sarvam analytics, n = 20 calls).
- Do not claim a "next turn vs missed" count for the real calls: none is labelled.

### B3. Distinctness across seller types (the 5 demo sellers D, E, F, G, H)
- Personas P1, P4, P3, P4, P3. Hooks: money lead, profile gap, category demand, money lead, category demand.
- Languages: Hindi ×4, Telugu ×1. Words per reply 18 / 10 / 12 / 10 / 11. Sophistication numbers first / practical / simple / practical / practical.
- Handler named for 3, team (pool) for 2.
- Across all 8 sellers: 6 different personas (P0, P1, P2, P3, P4, P6), 4 languages, words per reply 10 to 20.

### B4. Natural voice in 2+ languages
- 20 collected calls by start language: Marathi 12 (scripted tests), Hindi 3, English 2, Telugu 2.
- Mid-call switches tested into Hindi, English and Telugu (and Gujarati in the W1 suite).
- Voices: female Aarti (19 calls), male Anand (1 test), Sarvam Bulbul v4.

### B5. Support from past-call evidence
- **19 decisions or hooks cite a past call** across the 9 runs. Paraphrased examples:
  - the seller was busy in an earlier call and the next call dropped after seconds → a slightly brisker pace;
  - the seller declined last time because they saw no enquiries → open with category demand;
  - an earlier call engaged on buy leads → the lapsed-credits hook.
- Population evidence: 12,354 transcribed calls measured (a rush signal: meetings about 26% → 14%); hook-style evidence from the PS07 bot versions (A6).

### B6. One-line metrics for the animation (candidates)
| Criterion | Headline |
|---|---|
| Fit | 9 of 9 personas passed the validator; every field has a reason |
| Switches | Every scripted switch on the same turn; 0.9 ms to decide |
| Distinctness | 8 sellers → 6 personas, 4 languages |
| Languages | Marathi, Hindi, English, Telugu (+ Gujarati switch) |
| Past calls | 19 decisions cite a seller's own past call |

## C. Notes and gaps
- Size bands differ between files: `facts.py` uses three tiers (small, mid, large at 5 Cr+); doc v6 lists four bands (small, medium, medium-high, high). The "5 Cr+ → senior, English" rule is the same in both.
- Scoreboards are empty today: no learned uplift numbers exist yet. The animation should show what we measure, not claim uplift.
- Mid-call results are scripted test calls, not live sellers.
- New today (persona session): division falls back to the plan class (free = NSD, paid = CSD) when the vertical name gives none.
- Voice-agent TTS for calls is Bulbul v4 (Aarti); the video voice-over is Bulbul v3 (aditya).
