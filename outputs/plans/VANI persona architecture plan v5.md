# VANI Persona Design (PS04): high-level architecture plan v5

As of 2026-10-09 (hackathon day 1). Written for the team lead first, then an external reviewer. Method: top-down blocks, each with WHY / HOW / WHAT (input → output) / FEEDS (`.claude/skills/design-architecture/SKILL.md`). Supersedes [v4](VANI%20persona%20architecture%20plan%20v4.md) by applying the [adversarial review of v4](VANI%20persona%20architecture%20plan%20v4%20-%20adversarial%20review.md). Binding decisions: [team decisions 2026-10-09](../../raw/hackathon/2026-10-09-team-decisions-persona-agent.md). Free-text numbers: [freetext_share_ps07](../research_notes/Agent%20decides%20VANI%20persona/freetext_share_ps07.md).

**Evidence tags.** **PROVEN** = measured by us (spike or PS07 aggregate). **DOCUMENTED** = official doc, PS04 brief, deck, a paper or a `raw/` source. **ASSUMED** = our design choice or arithmetic, not yet tested. **WEAK** = DOCUMENTED but from a weak source (social scrape, other-domain benchmark).

**Binding intent (team lead).** The agent composes each seller's VANI persona with tools. Library personas are starting points, not a menu. Code checks only guardrails and what the platform can play. The agent suggests new library personas; a human adds them. The decider runs on a frontier model; Sarvam runs the voice agent. Voice gender comes from data, with no quotas.

## 0. Summary (ASD-STE100)

1. VANI is the bot that calls sellers. This plan gives VANI a persona for each seller.
2. A VANI persona is VANI's voice, speed, pitch, language, tone and call plan.
3. Seller data is the input. It is not the persona.
4. An AI agent reads the data of each seller who gets a call. The agent composes that seller's persona and gives a reason for each part.
5. The agent runs on a frontier model. If the data ruling or the network path is not ready by 17:00 today, we run the same agent skill on Sarvam-105b. Then the deliverables do not stop.
6. The agent runs only for sellers with useful free text or with low code confidence. Code makes the persona for all other sellers. About 3 in 10 returning sellers have useful free text.
7. Most useful free text is about time: "call me after Diwali", "I am travelling". Only about 1 in 10 sellers has a fact that lasts, such as "my son handles this".
8. Code checks facts, prices, compliance, the do-not-call list, native script and number words. Code checks each reason against the real data.
9. Code gives each setting an evidence label: measured, observed, literature or informed guess.
10. During the call, VANI cannot change its voice, speed or pitch. The platform does not allow it. VANI changes its words: shorter sentences, a check question, an apology or a callback offer. We measure this change.
11. The word list (lexicon) makes the switch decision. Jev only adds a signal.
12. We freeze the demo personas and Sarvam versions at 12:00 on day 2. We record a backup video by 16:00 on day 2.
13. After each call, two learning loops update tables and memory. No model is trained. There is no rule table.

---

## 1. Review fixes applied

### 1.1 Applied

| Finding | Change made | Section |
|---|---|---|
| C1 (part) | Frontier decider kept. Dated fallback trigger: Sarvam-105b runs the same skill on real sample files if rulings or the network path are open at 17:00 day 1. Both organiser rulings requested at the 15:30 day-1 check-in. Masking defined as a tested code step. Table of every off-premises flow. | §6.3, §6.4, §14 |
| C2 | B8 host decision with options and deadline; Jev reachability test from that host; lexicon = switch of record, Jev additive; "phir se" cue fix; Jev Devanagari test; B8 re-tagged | §7.3, §3, §9.3 |
| C3 | States plainly: voice, pace and pitch are fixed per call. Per-signal text-level change with a measured metric, written to the switch row | §7.4 |
| C4 | Per-call published-version selection proven today (F0); demo channel chosen by 18:00 day 1 and rehearsed; circular dependency broken with a day-1 base version set; demo freeze 12:00 day 2; backup video by 16:00 day 2 | §7.1, §11 |
| M1 | Deck rubric mapping; business-impact paragraph; submission checklist with owners and times | §12, §11.3 |
| M2 | Code-computed `evidence_tier` per setting; PS07 personalisation trials cited (0 for 3); observational mining of PS07 VANI variation | §5.4 |
| M3 | Fallback seeded from card seed hypotheses per seller type; reasons generated from the driving fields; cold-seller path; fallback rate measured on fixtures today | §6.7, §4.3 |
| M4 | §9.2 filled with numbers; D-1 closed as GATED, with the cost effect; rolling memory; text overrides NI label | §9.2, §6.2, §4 |
| M5 | Agreement on bucketed audible bundle; code picks the concrete style voice; opening move categorical; ≥ 2 passing runs required; plan text from the majority, re-validated | §6.5 |
| M6 | Native-script ratio validator; number-word list in the FAQ Q5 guard; neither model PROVEN on native script | §6.5 |
| M7 | New block B7a directive compiler (owner S): tone, empathy, English lean, branches, sensitivity → per-turn text; length budget; 3 golden examples. Accent mapped to voice language tag. Empathy added | §5.1, §7.2 |
| M8 | S owns latency and restarted replies: timeboxed endpointing test, scripted demo lines, measured numbers in skills.md | §7.6, §11 |
| M9 | ~60-utterance Devanagari/Hinglish test; precision/recall per signal for lexicon and Jev; demo gate ≥ 0.8 precision | §9.3 |
| M10 | B4 and B6 move to S after B8 works; experiment 2 arms × 2 reps × 20 sellers; gold ≈ 40 calls; external adjudicator; N's load cut | §9.1, §11 |
| M11 | Protect-and-cut order adopted | §11.4 |
| M12 | Production P0 pace read first; agent-level pace/pitch measured on 2 versions; bands defined relative to P0; demo contrast widened | §5.2, §9.4 |
| M13 | Not applied as proposed: team lead decided (2026-10-09) the **agent chooses voice gender** like any other dimension; no code draw, no flag or collapse alarm | §5.3 |
| M14 | Explicit cold-seller path; one cold seller in the demo | §4.3 |
| M15 | Manifest holds version tool URL + base-prompt hash; stable B8 hostname; re-cook off for frozen demo sellers; pre-demo checklist | §7.1, §10 |
| M16 | Failure-behaviour table for live dependencies; Sept relabelling handled (NI prior from Aug only; reward = meeting booked) | §7.5, §4.2 |
| M17 | Adoption rule never reverts to select-only: on failure, tighten rubric/bucketed agreement and gate the agent to free-text sellers | §9.1 |
| m1 | Propensity formula corrected for holdout mass; general ε sampler is design-only during the event (log fields kept) | §6.6 |
| m2 | 40K/day dropped; volume from ≈ 1,500 answered calls/day | §6.8 |
| m3 | Tags tightened (WEAK tag; scope notes on 20/20, 0/8, 28%) | §15 |
| m4 | One suggestion trigger only | §6.6 |
| m5 | 6 priority contracts in hours 0–2; dimension enum frozen; plan duplication removed; mock composer outputs specified | §11.1 |
| m6 | Tamil out of the demo; stated as a gap | §12, §13 |
| m7 | Second demo language picked by audition; voice after switch noted | §7.4, §9.4 |
| m8 | Library column renamed "seed hypotheses" | §5.2 |
| m9 | Holdout and exploration on real sellers = design only | §6.6 |
| m10 | Glossary; demo-path diagram | §2, §15 |

### 1.2 Not applied / needs team-lead decision

1. **C1: "make Sarvam-105b the default decider from hour 0".** Reviewer's argument: the frontier decider is barred from real seller data until a ruling, and its network route is blocked (OpenRouter 403 from Daytona; LiteLLM untested), so D1/D2 on the real sample files would come from a non-chosen path; Sarvam is sanctioned, cheap (₹0.16, 4.2 s) and PROVEN on the flat schema. **Conflicts with binding decision 5** (decider runs on a frontier model). v5 keeps the frontier decider and adds only the dated 17:00 fallback trigger (§6.4). Team lead to decide whether to go further.
2. **C5: pre-event spike code and the "all build during the 2 days / pre-built" rules.** Not addressed in this plan, on the team lead's instruction. Not in fixes or the work split.
3. **M17 / §9.1 / §5 of the review: "select-only" as a fallback framing.** Reviewer's fix already avoids this; any variant that makes the agent select-only **conflicts with binding decision 3** (agent composes). v5 never reverts to select-only. A select-only arm is not run (cut with the 4-arm experiment).

---

## 2. Diagrams

### 2.1 End to end

```
 SELLER DATA (input)                                  B3 LIBRARY (versioned STARTING POINTS)
 profile · call log · evaluator JSON · summaries ·    P0 control + P1..P4 on shared dimensions
 transcripts (masked) · rolling memory facts          + seed hypotheses + evidence + native-script moves
        │                                                          │       B4 Scoreboard (type × dimension × level)
        ▼                                                          │                │
 B1 Seller context + memory facts ─► B2 Estimator + seller type (cold path)         │
 ┌──────┴─ BATCH: sellers due a call ──────────────────────────────┴────────────────┴────────────┐
 │ B5a CONTEXT + GATE (code): DNC → no call · free-text fact OR low code confidence → agent;    │
 │                      else → code path · pre-fetch evidence, library, scoreboard, voices       │
 │ B5b AGENT COMPOSER: frontier model on Daytona ×3 (Sarvam-105b if 17:00 trigger fires)        │
 │     → composed spec: each dimension {value, citations, confidence, origin}                   │
 │ B5c GUARD + SETTLE (code): schema · citations · FAQ Q5 (digits, number words, prices) ·      │
 │     FAQ Q6 · native-script ratio · DNC → ≥2 runs pass, agree on BUCKETED audible bundle      │
 │     → settle rest; code picks style voice; evidence_tier                                     │
 │     playability: requested → nearest playable version (log both)                             │
 │     fail → seeded code path with real reasons · far from library → suggestion_row            │
 │ B6 Spec store (frozen for demo sellers)                                                       │
 └──────────────────────────────┬──────────────────────────────────────────────────────────────┘
                                ▼
 B7a Directive compiler ─► B7 Sarvam start: published version (per-call selection) + initial_language_name
                           + initial_bot_message (native) + agent_variables{decision_id, persona_directive}
 LIVE: seller ◄─voice─► Sarvam agent (voice/pace/pitch FIXED for the call)
                          └─tool call per turn─► B8 SIGNAL SERVER (stable host)
                               lexicon = switch of record (<5 ms) · Jev additive · code policy
                          ◄── persona_directive = <plan> | Right now: <text-level change> ┘
 POST-CALL ─► B9 review + outcome (meeting booked)
     ├─ LOOP 1 ─► B10 lexicon · thresholds ── gold gate ──► B8
     └─ LOOP 2 ─► B11 rolling memory · scoreboard · suggestions ──► B1/B2/B4 = AGENT'S TOOLS
                                └─ weekly cluster → human → B3 (+ Sarvam version if audible)
 B12 DATA (append-only, on premises): snapshot · decision · call (requested vs played vs observed) ·
     switch log · outcome · suggestion · manifest (incl. version tool URL + base-prompt hash)
```

### 2.2 Demo path only (what judges see)

```
3 demo sellers (1 cold) ─► composer or fallback ─► FROZEN spec 12:00 d2 ─► published version + opening
   ─► live call ─► seller says "samajh nahi aaya" ─► lexicon ─► shorter sentences + check question
   ─► switch log row (words/reply before vs after) ─► "why" panel with evidence tiers
```

## 3. Block table

| Block | Why | How (choice; rejected) | Input → Output | Feeds | Status |
|---|---|---|---|---|---|
| B1 Seller context + memory | D1; FAQ Q6 | As-of script; masked free text from summary **and** evaluator JSON (+ transcript); rolling memory facts; *rej.* last-call memory, seller-file history columns | rows, as_of → `seller_context` | B2, B5 | Leakage-free PROVEN; memory ASSUMED |
| B2 Estimator + seller type | Fit 25 | Beta posteriors, decay, nearest of 7 types; cold path; NI prior from Aug only | → `seller_estimates` | B5, B4 | Recurrence PROVEN; estimator ASSUMED |
| B3 Library | Distinct 20; voice | Starting points + seed hypotheses + evidence; grows via approved suggestions; *rej.* fixed menu | → `persona_library_vN` | B5, B7 | Levels ASSUMED |
| B4 Scoreboard | Evidence 15 | Beta per type × dimension × level; *rej.* rule table | → `scoreboard_vN` | B5 | Prior-only |
| B5a Context + gate | D2; cost | DNC; gate agent to free-text or low-confidence sellers | → `agent_input` / code path | B5b, B5c | Gate share PROVEN; rule ASSUMED |
| B5b Agent composer | D2; fit | Frontier + skill on Daytona, k = 3, read-only tools; Sarvam-105b on trigger; *rej.* select-only | → `agent_output` ×3 | B5c | Route blocked; flat schema PROVEN |
| B5c Guard, settle | Evidence; FAQ Q5/Q6 | Validators; bucketed agreement; code voice pick; evidence tier; seeded fallback; suggestion | → `persona_decision`, `suggestion_row` | B6, B11, B12 | ASSUMED |
| B6 Spec store | Fresh spec | Batch + freeze for demo; staleness check | → ready spec | B7a | ASSUMED |
| **B7a Directive compiler** | Distinct 20; fit | Template, length budget, golden examples | `persona_decision` → `call_config`, directive strings | B7, B8 | ASSUMED |
| B7 Compile + Sarvam | D3; voice | Published version per call + per-language voice; native opening | → start payload | Sarvam | Per-language route PROVEN; version selection untested |
| B8 Signal server | Switches 25; D4 | Lexicon of record + Jev additive + code policy | utterance → directive + switch row | Sarvam, B12 | Lexicon + tool path PROVEN; Jev from host, Jev Devanagari, thresholds ASSUMED |
| B9–B11 Review, loops | Evidence; learning | Offline review; gated lexicon edits; memory, scoreboard, suggestions | → updated tables | B8, B1–B4 | ASSUMED; one artefact each |
| B12 Data | Evidence | Append-only JSONL → Parquet + DuckDB, on premises | all → views | all | ASSUMED |

---

## 4. Seller side: B1 and B2

### 4.1 B1 context and rolling memory

Deterministic, counts only events before `as_of`, rebuilds history from call rows (seller-file `past_*` columns leak Apr–Sep, PROVEN). Free text comes from three sources, because **the summary alone misses about a third** (9.9% of due sellers have facts only in evaluator JSON or transcripts, mostly `disposition.followup_when`; PROVEN).

A typed memory-fact extractor runs per finished call: `callback_when, contact_person_role/alt_contact, language_pref, competitor_or_paid, need, complaint_type, constraint, price_detail`, each with span id and date. Regex baseline today (precision 70–95% per family, PROVEN); LLM extractor later (ASSUMED).

**Rolling memory, not last-call.** 49.5% of fact-holding sellers have the fact only in an **older** call (PROVEN). Memory keeps all prior facts; timing facts decay fast (median age 7 d), durable facts slowly (ASSUMED half-lives).

**Text overrides a Not-Interested label** when the text shows a specific need (38% of such calls are labelled NI), another contact person (16%) or a temporary constraint (8%) (PROVEN). Then the NI label does not drive the NI prior; the fact drives the plan (who, when, which line). This affects 3.0% of due sellers (PROVEN).

`seller_context = {snapshot_id, as_of, profile{…}, history{n_prior_calls, last_outcome, gap_days, outcome_shares}, signals{…: {k, n}}, observed_language, memory_facts[{family, value, span_id, call_date, durable: bool}], free_text[{span_id, source: S|E|T, text_masked}], flags{dnc, ni_overridden_by_text}, missing_fields[], completeness}`.

### 4.2 B2 estimator

History sets odds, not identity: rush recurs 30.8% vs 20.8% base; terse 41.0% vs 17.8%; English-heavy 13.8% vs 4.3% (PROVEN). Pre-call prediction AUC 0.52–0.58, English-heavy 0.68 (PROVEN). **NI decay and any NI prior are fit on August only**, because September relabelled NI 51% → 19% (PROVEN). Seller type = nearest of 7 warm types (ARI 0.868, PROVEN), with distance. Output `seller_estimates = {seller_type{id, distance, fit}, traits, states, language{start_guess, source}, code_confidence}`.

### 4.3 Cold-seller path (M14)

59.5% of sellers have < 2 calls; profile-only AUC 0.52–0.58; cold ARI ≤ 0.44 (PROVEN). A cold seller gets: start language from state + profile (with the known caveat that ~¼ of stated non-Hindi preferences come from Hindi-belt states, PROVEN); formality from business size; every other setting at P0 or the seed level, `confidence ≤ completeness`, `evidence_tier = informed guess`; contingency branches all **dormant but armed**; live-switch sensitivity at default. The honest message: "for a new seller VANI starts neutral and adapts live" (FAQ Q6). Cold sellers go to the code path unless they have free text. One of the 3 demo sellers is cold.

---

## 5. VANI side: B3 library, B4 scoreboard, evidence tiers

### 5.1 Persona dimensions

| Group | Dimension | Values (ASSUMED) | Audible? |
|---|---|---|---|
| Voice | gender; style voice (Bulbul id); **accent = voice language tag** (`_hi_`, `_enhi_`) | auditioned subset of 222 Bulbul v4 voices | yes |
| Delivery | pace band; pitch band | bands **relative to P0** (§5.2) | yes, fixed per call |
| Language | start language; English lean | languages with an auditioned voice | yes |
| Tone | formality; warmth; **empathy**; brevity | 1–5 | via B7a text |
| Plan | opening move (library id or `new:<family>`); steps; personalisation; objection order; escalation | native script | via B7a text |
| Adaptation | branches (promoted/dormant); sensitivity per signal | per signal | via B8 |

The dimension enumeration is frozen in the hour 0–2 contract. Plan dimensions live only in `plan{}` (no duplicate under `spec`).

### 5.2 B3 library (starting points)

| Id | Archetype | Audible bundle | Seed hypotheses (starting values; data overrides) |
|---|---|---|---|
| P0 | Current VANI | production pace/voice (read first, M12) | control; cold default |
| P1 | Crisp closer | pace ≥ P0 + 0.1, lower pitch | rush, terse, call-me-later |
| P2 | Patient guide | pace ≤ P0 − 0.1, warm | confusion prior, thin history |
| P3 | Respectful advisor | P0 pace, measured | meeting revisit, larger business |
| P4 | Warm re-engager | P0 pace, expressive | short-call refuser, recent NI |

**Pace bands are relative to P0.** The spike agent's stored pace is 1.15 (PROVEN); if production P0 is also 1.15, an absolute "brisk 1.05" is slower than control. Bands are re-set once production pace is read and agent-level pace is measured (§9.4). For the demo, contrast is widened: e.g. 0.9 vs 1.2, plus a gender change and a language change (ASSUMED, to be heard).

**Voice facts.** SDK per-call TTS override is ignored (PROVEN). Per-language voices + `initial_language_name` select the voice per call (PROVEN). Pace/pitch PROVEN only via the TTS API; agent-level pace and pitch are **untested**. Code Tools on-start is not enabled for us (requested 2026-10-09). Native script for all spoken text (DOCUMENTED).

### 5.3 B4 scoreboard

Beta counts per seller type × dimension × level, 10–25 pseudo-call priors (seeded from the seed hypotheses, which decision 2 allows as starting values), forgetting λ ≈ 0.8/month (ASSUMED). Only explored and holdout traffic supports a "works better" claim. Every cell is prior-only today.

**Voice gender (decision 7, team lead 2026-10-09).** The agent chooses voice gender like any other dimension, from the seller's data and the scoreboard. There is no code draw, no quota and no flag or alarm. When outcome data arrives, the agent reads it through the scoreboard tool and uses the better-working gender more. Seller gender and age are never inferred.

### 5.4 Evidence tier per setting (M2)

Code (not the agent) sets `evidence_tier` per setting:

| Tier | Meaning | Today |
|---|---|---|
| `ps07_measured` | outcome contrast from a PS07 trial or explored/holdout traffic | personalisation trials only |
| `ps07_observational` | PS07 association, not randomised | rush/frustration vs meetings; natural variation in VANI reply length, language, call time vs outcome (to mine, labelled observational) |
| `literature` | DOCUMENTED external | e.g. pace for confusion |
| `informed_guess` | seed hypothesis, no data | most persona settings |

**Honest citation of PS07 trials:** three internal script-personalisation trials went 0 for 3. `personalis` vs `base_vani` (30 Sep, 452 vs 289 calls): meeting-fixed 14.8% vs 17.8% (p = 0.13); Not Interested 5.5% vs 13.1% (PROVEN, `wiki/projects/vani-hackathon/persona-data-validation.md`). Reading: personalisation kept sellers talking but did not lift meetings. The tier appears in the "why" panel and on the slide.

---

## 6. B5 Persona decision

### 6.1 Three translation layers (unchanged)

(a) Pre-call settings, fixed for the call; (b) contingency branches, re-sent each turn; (c) live-switch sensitivity used by B8. Live evidence wins over the prior.

### 6.2 B5a Context and gate — D-1 closed as GATED

**Rule.** DNC → no call. The agent runs for a due seller if **(a) any memory fact exists** (free text, §9.2) **or (b) `code_confidence` is low** (seller-type distance above p90, or conflicting signals; ASSUMED cut). All other sellers go to the seeded code path (§6.7). The decision to gate is final (D-1 closed); the confidence cut is config.

**Why.** 30.8% of due sellers have any decision-changing fact (~28.8% precision-adjusted); only 9.7% have durable facts (PROVEN). For the other ~70% the agent would read structured data that code already handles.

**Cost effect.** Agent share ≈ 31% + low-confidence share (ASSUMED ≈ 10%) ≈ 40% of due sellers instead of 100%: about 2.5× fewer frontier runs. Decision reuse when nothing changed cuts more (§6.8).

`agent_input = {decision_id, snapshot_id, gate_reason: free_text|low_confidence, seller_estimates, memory_facts[], library[{persona_id, levels, evidence{n, effect, ci90, tier}}], scoreboard[…], voice_options[{language, bucket, voice_id, gender, playable_now}], missing_fields[], guardrail_ref, versions{…}}`.

### 6.3 B5b Agent composer

Frontier model (Claude Code-style agent + persona-composition skill) on a Daytona sandbox via OpenRouter or internal LiteLLM; model id logged. Read-only tools: `get_seller_context`, `get_free_text(span_ids)`, `get_seller_memory`, `get_scoreboard`, `get_persona_library`, `get_voice_options`, `get_similar_sellers(k)` (counts only), terminal `submit_spec`. The agent composes every dimension of §5.1 from any library persona(s) or none, cites evidence, gives a confidence, writes the plan in native script, and writes `suggestion_reason` when far from the library. Flat JSON mandatory (nested failed 4/6, flat never failed; PROVEN). Self-confidence logged, never a gate.

**Honest headline.** On PS07 data the agent's main added value is a **scheduling and opening-line memory** ("you asked me to call after Diwali", "is your son available") rather than new persona traits. Language (0.26%) and competitor (0.56%) facts are too rare for their own branches; they are plan-level flags (PROVEN shares; ASSUMED reading).

### 6.4 Rulings, fallback trigger, masking, off-premises flows (C1)

**Rulings.** At the **15:30 day-1 mentor check-in** we ask the organisers two questions: (1) may masked seller data go to a frontier model (and to the reviewer and Jev); (2) does "core agent must be Sarvam" allow a frontier-model decider. Answers are filed in `raw/hackathon/`. Owner: team lead.

**Fallback trigger (dated).** If **at 17:00 on day 1** either ruling is open, or the Daytona → model path (OpenRouter allowlist for 35.234.211.110, or LiteLLM from Daytona) does not work, M runs **the same agent skill with Sarvam-105b** on the real sample files, so D1/D2 are not blocked. The frontier model stays the decider of record; once both clear, it re-runs and its outputs replace the Sarvam ones (both logged, `model_id` per run). Until the ruling, the frontier model sees synthetic or masked data only.

**Masking = code step with a test.** Replace phone numbers, GLIDs, emails, seller and company names from profile fields (Latin and Devanagari forms), and contact names after role words, with typed tokens. Test: a fixture file with planted identifiers; zero may survive. Regex alone is not trusted for names in Hinglish text (ASSUMED risk; tested).

| Off-premises flow | Data | Until ruling |
|---|---|---|
| Frontier decider (OpenRouter / LiteLLM) | masked context + free text | synthetic/masked only |
| Sarvam-105b decider, Sarvam voice agent | masked context; live audio | sanctioned platform |
| Jev (live) | single seller utterance | lexicon of record; Jev additive only if allowed |
| B9 reviewer LLM | masked transcript | manual review of 1 call |
| B8 tunnel, if used | tool payloads | see §7.3 |

### 6.5 B5c Guard and settle

1. **Guard each run.** Schema. Citation validator (cited field/span/cell exists, quoted value matches on re-read). **FAQ Q5:** no digits, **no number words** (Hindi, English, Gujarati list, e.g. "do", "teen", "paanch", "hazaar", "two", "be" near price or time context), no price words, product claims or internal labels; greet-and-confirm-owner first; human-on-request kept; fixed fact layer untouched. **FAQ Q6:** confidence ≤ completeness; personalisation only from present fields. **Native-script ratio** of spoken text ≥ 0.9 for Indic languages (ASSUMED cut); one repair call, else the run fails. Sarvam-105b produced Hinglish in Roman script 3/3 (PROVEN); neither model is PROVEN on native script.
2. **Agree.** At least **2 runs must pass**, else fallback. Accept when ≥ 2 passing runs match on the **bucketed audible bundle** {gender, pace band, pitch band, start language} and on ≥ 2 of 3 key plan choices {opening move id or `new:<family>`, first objection, promoted branches}. Gender is the agent's choice.
3. **Settle.** Categorical by majority, ordinal by median. **Code picks the style voice** deterministically from the playable set for the bucket (best audition rank). Plan text comes from a run **inside the agreeing majority**, then is re-validated against the settled values.
4. **Playability.** Map the bucket to the nearest published version (language first, then gender, pace band, pitch band); log `requested`, `played`, distance.
5. **Evidence tier** per setting (§5.4).

### 6.6 Explore and suggest

**Exploration during the event is design only** (m1, m9): no real traffic, demo sellers excluded, real-seller holdout needs business approval. The log fields stay (`agent_value, played_value, explored, propensity, seed`). Corrected formula for later: P(agent value on dimension d) = (1 − h)(1 − ε/D) + h·1[P0_d = agent_d]. No dimension is drawn by code during the event.

**Suggest (one trigger).** Write a `suggestion_row` when **≥ 2 audible dimensions differ** from the nearest library persona (an audible gap is what needs a new Sarvam version; ASSUMED). The distance score is logged, not a trigger. Weekly clustering (TnT-LLM/Clio pattern) + human approval is kept as design; during the event one clustering run is a recorded artefact, expected to propose nothing on PS07 patterns.

### 6.7 Seeded fallback with real reasons (M3)

On no agreement, < 2 passing runs, or a gated-out seller: code takes the library persona whose **seed hypotheses** best match this seller's estimates (e.g. rush in 2 of last 3 calls → P1), adds memory-fact personalisation, and writes reasons from the fields that drove the choice ("rush in 2 of last 3 calls → P1 pace band"; "callback asked for after Diwali → opening references it"). Empty scoreboard → seed, not a random draw. Cold → §4.3. `path: fallback | code_gated`. **The fallback rate is measured on the 6 fixtures today**; > 40% means the skill rubric is unclear.

### 6.8 Volume, cost, freshness

Volume: ≈ 1,500 answered calls/day in PS07 (PROVEN); the 40K/day figure is dropped. Gated at ~40% → ~600 agent sellers/day × 3 runs (ASSUMED). Frontier cost per run is unmeasured; measure on the fixture run. Sarvam-105b ≈ ₹0.16 / 4.2 s per call (PROVEN). Reuse a decision when snapshot, memory and versions are unchanged. Event re-cook and the 72 h staleness engine are design only; one batch run during the event; **demo sellers' decisions are frozen** with re-cook off.

---

## 7. Live call: B7a, B7, B8

### 7.1 B7 start payload and demo versions (C4, M15)

| Sarvam input | Demo route | Evidence |
|---|---|---|
| Voice, pace, pitch | published version per bundle; voice via `initial_language_name` | per-language route PROVEN; **per-call version selection untested** |
| Opening | `initial_bot_message` (native) | spoken verbatim PROVEN |
| Variables | `agent_variables{decision_id, persona_directive}` | PROVEN; `decision_id` echo untested |
| Per turn | `{persona_directive = <plan> \| Right now: <change>}` | plan re-send 20/20 (10 calls, hand-written plans) |

**Breaking the cycle.** Day 1: S publishes a **base set of 3–4 versions** from the library audible bundles (P0, crisp, patient, plus one second-language voice). The composer chooses within these `voice_options`. After the composer (or fallback) runs on the demo sellers, S adds or adjusts versions to match their recommended bundles (decision 6) until the freeze. Code Tools replaces this when enabled.

**Today (S):** publish 2 versions and prove per-call `version`/`app_version` selection changes the voice (median F0, as before). **Demo channel chosen by 18:00 day 1**: (i) human on a phone via Instant Outbound, or (ii) SDK call harness with a laptop mic; pick the one that passed version selection and gives a transcript for the switch log; rehearse end to end with a fixture decision.

**Freeze at 12:00 day 2:** demo decisions (from whichever path works) and versions pinned in the manifest with each version's **tool URL and base-prompt hash**; re-cook off. Pre-demo checklist: B8 health check, one call per version, F0 check. **Backup video recorded by 16:00 day 2.**

### 7.2 B7a Directive compiler (M7; owner S)

Input `persona_decision`; output `call_config` + the per-turn `persona_directive` string. Template, all in native script where spoken:

```
PERSONA: formality <1–5 → word>, warmth <…>, empathy <…>, brevity <max words/sentence>, Hinglish mix <low|mid|high>
PLAN: <opening id> → <steps> · personalise: <field lines> · objections: <order>
IF rush/confusion/frustration/interest: <promoted branch text>
Right now: <mode change from B8>
```

Length budget ≤ 600 characters per turn (ASSUMED; check Sarvam's variable limit today). Three golden examples (rusher, confused cold seller, son-handles-it seller) in `app/contracts/` and part of hour 0–2. Fixed base prompt keeps product facts, prices and compliance; nothing compiled can change them. 0/8 price-demand turns quoted an amount, on hand-written plans only (PROVEN); re-test with compiled text.

### 7.3 B8 host and Jev (C2)

**Host decided by 17:00 day 1 and recorded.** Options: (a) Daytona with admin wildcard DNS + TLS (no auto-stop); (b) VPN laptop with a tunnel, accepting the tunnel's vendor risk and changing URL explicitly; (c) an IndiaMART-hosted box Sarvam can reach. The chosen host gets a stable hostname so version tool URLs do not change.

**Jev reachability from that host** is tested the same day. Today the Daytona IP is not allowlisted ("the in-call server cannot call Jev yet") and the LiteLLM Jev route showed 8/8 failures (PROVEN, spike log). Jev 49/51 and ~480 ms were measured on **romanised** text from the VPN laptop; **Devanagari is untested** — tested in §9.3.

**The lexicon is the switch of record** for the demo. Jev is an additive signal: it can raise confidence or catch a missed cue, never block a lexicon switch. Fix before the demo: "phir se pooch raha hoon, price batao" fired false confusion 4/4 (PROVEN) → "phir se" counts as confusion only without a price/request verb in the same turn. Policy: frustration > confusion > rush > interest; hysteresis; max 2 switches; per-seller thresholds (untested; tested on the §9.3 set).

### 7.4 What a switch can change (C3)

**Voice, pace and pitch are fixed for the whole call.** Sarvam assigns voice per language at call start and does not change it mid-conversation; in-call tools expose no TTS control (DOCUMENTED UI text; PROVEN spike). So every live switch is a **text-level change**, and we show it with a number:

| Signal | Text-level change (written to switch row `change`) | Measured on the demo call |
|---|---|---|
| Confusion | ≤ 8 words per sentence, one idea per turn, a check question, commas / "…" for pauses (test whether Bulbul pauses on punctuation) | words/sentence and speech seconds per idea, before vs after |
| Rush | ≤ 12 words per reply + a fixed callback slot | words/reply; time to callback offer |
| Frustration | apology + exit or human offer, no pitch | turns to exit offer |
| Interest | skip remaining steps, go to the meeting ask | turns to meeting ask |
| Language | Sarvam built-in switch (6/6 PROVEN) + next directive in that language; Hinglish mix raised or lowered | language of next reply; voice stays the start-language voice (m7) |

The slide says it once: "voice is fixed per call by the platform; VANI adapts what and how much it says."

### 7.5 Failure behaviour (M16)

| Failure | Behaviour |
|---|---|
| B8 down or slow (tool max wait 2 s) | Base prompt holds a safe plan summary; test what the variable holds after a tool error; health check before each demo call |
| Jev unreachable | Lexicon only; log `source=lexicon, jev=unavailable` |
| Decider route blocked | 17:00 trigger → Sarvam-105b (§6.4) |
| `decision_id` not echoed | Map the agent variable to a tool-body field ("Agent variable" option); fallback: single active-call registry for the demo |
| Runs disagree | Seeded fallback with real reasons (§6.7) |
| Sarvam ignores composed plan | Plan re-sent every turn; re-test with **compiled** text, not hand-written |
| Language turn skips the tool (0/4) | Log from the channel's transcript; next directive follows the new language |
| Daytona auto-stop | Disable for B8 sandbox or host elsewhere |
| Sept NI relabelling | NI prior from Aug only; reward = meeting booked |

### 7.6 Latency and restarted replies (M8; owner S, timebox 2 h on day 1)

~17% of replies restarted (≈ 8/46 turns, including the Gujarati switch turn) and median reply latency ≈ 2.1 s (1.2–3.5 s) without Jev (PROVEN). S tests endpointing settings ("Switch after", eagerness, interruption), scripts the demo seller's lines without mid-sentence pauses, measures restart rate and latency on the final demo versions, and reports both in skills.md.

---

## 8. Between runs: two loops (condensed)

No model is trained. B9 labels switch verdicts and per-dimension fit offline (masked); during the event, **one manually reviewed call**. Two-key labels (lexicon vs evaluator κ ≈ 0.03, PROVEN).

| Loop | Learns from | Changes | Gate | Feeds | Event artefact |
|---|---|---|---|---|---|
| 1 Switch | switch verdicts, §9.3 errors | lexicon, thresholds (Jev wording cut) | frozen gold (≈ 40 calls) + flip list | B8 | one gated lexicon diff, one rejected |
| 2 Persona | outcomes (meeting booked), memory facts, suggestions | rolling memory, per-dimension scoreboard, library | two-key labels; clustering gates + human | B1/B2/B4 → agent tools | one memory update, one scoreboard update, one clustering run |

---

## 9. Validation

### 9.1 Experiment (cut to fit; pre-registered)

**Set.** 20 synthetic sellers in proportion to §9.2: 8 structured-signal only; 6 with timing/contact free text that should change the plan; 3 with distractor text; 2 with a durable fact (e.g. son handles it, specific need on an NI label); 1 cold. No Tamil case (0.26%).

**Labels first.** Team lead (if not S or M) and N write the expected bucketed bundle, 2–3 plan elements and "suggest new" where expected; a **mentor or another team's member** adjudicates; file hashed and committed before any arm runs.

**Arms.** Code-only (seeded fallback) vs compose + guard. 2 reps each; model logged (frontier or Sarvam-105b by the trigger). ≈ 20 × 2 × 2 × 3 runs ≈ 240 agent runs (ASSUMED).

**Metrics.** Bundle and plan accuracy per group; free-text sensitivity; distractor robustness; confident-wrong; fallback rate; citation validity; guard failures; native-script quality (N rates blind); distinctness (pairwise spec distance); cost; latency.

**Adoption rule (never select-only).** Compose + guard stays. If it loses to code-only on the structured group by > 5 pp, or confident-wrong is higher, or fallback > 40%: (1) tighten the skill rubric and agreement buckets; (2) narrow the gate to sellers with memory facts only. The agent always composes when it runs. Power is low; analyse paired.

### 9.2 Free-text share in PS07 (filled; PROVEN, regex, aggregates only)

Due proxy = latest call in Aug/Sep with ≥ 1 earlier call (35,794 sellers; median 2 prior calls).

| Measure | Due sellers |
|---|---|
| Any decision-changing fact | **30.8%** (~28.8% precision-adjusted) |
| Durable facts (contact, language, competitor, need, complaint, price) | **9.7%** (~8.5%) |
| Callback time | 18.8% |
| Personal constraint (travelling, driving, unwell, meeting) | 14.0% |
| Complaint | 3.8% |
| Different contact person | 3.4% |
| Price detail | 2.3% |
| Competitor / already paid | 0.56% |
| Specific need | 0.51% |
| Language | 0.26% |
| Fact only in an older call (not the last) | 49.5% of fact-holders |
| Text contradicts structured data | 3.0% (mostly NI label vs need/contact/constraint) |
| Facts only in evaluator JSON / transcript | 9.9% |

**Consequences applied.** D-1 closed as gated (§6.2). Rolling memory (§4.1). Text overrides an NI label for need/contact/constraint (§4.1). Language and competitor = plan flags, not branches (§6.3). Experiment groups reweighted (§9.1). Still open: the share where text changes the **composed persona** (not only the plan); the durable 9.7% bounds it from above for trait-like changes. Regex recall unmeasured → shares are lower bounds.

### 9.3 Switch detection test (M9; before the demo)

≈ 60 Devanagari and Hinglish utterances: ≈ 12 per signal (frustration, confusion, rush, interest, language) plus hard negatives ("phir se … price batao", polite "baad mein"). Report precision and recall per signal for the lexicon and for Jev (Jev called from the B8 host). **Demo gate:** frustration, confusion, rush, interest each ≥ 0.8 precision on the lexicon. Same set tests per-seller thresholds and hysteresis.

### 9.4 Audibility tests (M12, m7; S + N, day 1)

Read production VANI pace. On 2 published versions measure agent-level pace (speech seconds per word) and pitch (median F0). Set bands relative to P0. N auditions voices for the second demo language (Hindi + English via `_enhi_`, or Gujarati if a voice passes audition).

---

## 10. B12 data created from day one

| Record | Key | Must hold |
|---|---|---|
| `seller_snapshot` | snapshot_id | B1 output incl. span ids, memory facts, missing fields |
| `decision` | decision_id | versions; model id per run; gate reason; 3 runs; validator results; agreement; per-dimension agent vs played value, `evidence_tier`, explored, propensity; path; frozen flag |
| `suggestion_row` | decision_id | spec; nearest library; audible diffs; reasons |
| `call` | call_id | voice requested vs played vs observed (F0); switch log incl. `change` metric; latency; restarts |
| `outcome` / `review` | decision_id | meeting booked; two-key labels |
| manifest | version id | hashes: library, scoreboard, skill, prompts, validators, lexicon; **each Sarvam version's tool URL + base-prompt hash** |

Backfilled PS07 rows: `propensity = null`, `causal_claim_allowed = false`.

---

## 11. Work split, timeline, submission

### 11.1 Hours 0–2 (all three)

Six priority contracts in `app/contracts/` (JSON Schema + example): `seller_context`, `persona_decision` (with frozen dimension enum), `call_config`, `tool_turn`, `switch_log_row`, `call_record`. Others (`agent_input`, `agent_output`, `suggestion_row`, `review`, `outcome`) follow by end of day 1. Fixtures: 6 synthetic sellers (1 cold, 2 with memory facts); a 2-persona mini library; a mock composer with two sets of 3 outputs: **set A** = runs 1 and 2 agree on the bucket and run 3 has a bad citation (→ run 3 fails guard, runs 1–2 settle); **set B** = runs 1 and 2 agree on a bundle ≥ 2 audible dimensions from every library persona (→ suggestion row) and run 3 has a bad citation; a set-A variant with run 2's citation also broken (→ < 2 passing → fallback); 3 golden directive strings.

### 11.2 Owners

| Member | Owns | Done when |
|---|---|---|
| **S — strong dev** (live path) | B7, B7a compiler, version base set + per-call selection test, demo channel, B8 host + Jev test, lexicon fixes, §9.3 test, latency/restart timebox, §9.4 audibility; **after B8 works: B4, B6/freeze** | Live call on a frozen version with ≥ 1 measured text-level switch; requested = played = observed voice |
| **M — second member** (decision path) | B1 (+ memory extractor, masking + test), B2, B5a gate, B5b on Daytona + 17:00 trigger, B5c, seeded fallback, decision records, §9.1 harness | One command turns sample seller files into validated `persona_decision` JSON; fallback and suggestion proven on fixtures; fallback rate reported |
| **N — non-tech member** | Library cards in native script with seed hypotheses; voice auditions; experiment labels; ≈ 40 gold calls; native-script rating; skills.md draft; demo script | Library v1; labels committed; demo script with lines that avoid mid-sentence pauses |
| **Team lead** | 15:30 rulings; 17:00 trigger call; adjudicator recruited; final sign-off on freeze | Rulings filed in `raw/hackathon/` |

### 11.3 Timeline and submission checklist (deck)

| When | What | Owner |
|---|---|---|
| D1 15:30 | Both organiser rulings asked | Team lead |
| D1 17:00 | Decider trigger check; B8 host decided | Team lead, M, S |
| D1 18:00 | Demo channel chosen; per-call version selection proven | S |
| D1 night | Experiment (240 runs); §9.3 test | M, S |
| D2 12:00 | **Freeze** demo decisions + versions | S, team lead |
| D2 16:00 | **Backup video** recorded | N + S |
| D2 by 22:00 | 5–7 min demo video final | N + S |
| D2 by 22:00 | Approach note | M |
| D2 by 22:00 | Agent ID / live link | S |
| D2 by 22:00 | Code folder + README; sample outputs (specs for every sample seller) | M |
| D2 by 22:00 | skills.md (incl. latency, restart rate, switch precision) | N with S, M |
| D2 23:59 | Submit | Team lead |

### 11.4 Protect and cut order

**Protect:** (1) live demo call on frozen versions with ≥ 1 lexicon switch; (2) switch log; (3) specs for every sample seller with real reasons and evidence tiers; (4) natural voice in 2 auditioned languages; (5) video, slide, README, skills.md, Agent ID; (6) switch precision table; (7) frontier composer on real data if rulings allow.

**Cut first:** (1) weekly clustering (one artefact); (2) propensity sampler and holdout (log fields only); (3) experiment beyond 2 arms × 2 reps; (4) gold calls beyond ~40; (5) Jev wording loop; (6) B9 automation (one manual review); (7) k = 3 → k = 1 + guards, labelled; (8) frontier → Sarvam-105b run of the same skill (already the 17:00 trigger).

---

## 12. How the scores are met

### 12.1 PS04

| Item | Met by |
|---|---|
| D1 generator on sample files | B1 → B5 on real files (frontier, or Sarvam-105b by trigger; code path for gated-out sellers) |
| D2 spec + reasons | per-dimension values, re-checked citations, evidence tier; fallback reasons from fields |
| D3 live demo, ≥ 1 switch, 2–3 sellers | frozen versions; lexicon switch with measured change; 1 cold seller |
| D4 switch log | B8 rows incl. `change` metric and `sarvam_builtin` language turns |
| D5 slide | sample spec + evidence tiers + requested-vs-played + "voice fixed, words adapt" + chosen LLM (per ruling) |
| Fit 25 | traits/states, rolling memory (AUC 0.71 vs 0.58, PROVEN), NI override, cold path |
| Switches 25 | lexicon of record, per-signal precision ≥ 0.8, measured text change |
| Distinctness 20 | bucketed audible contrast widened for demo; B7a text differences; distance table |
| Voice 2+ languages 15 | auditioned voices, native script, built-in switch, latency/restart numbers |
| Evidence 15 | evidence tiers; PS07 trials cited; §9.2 numbers |

### 12.2 Deck jury rubric (M1)

| Criterion (weight) | Our answer |
|---|---|
| Business Impact 25 | paragraph below; projection labelled |
| Solution Completeness 20 | D1–D5 all on real sample files; submission checklist owned (§11.3) |
| Technical Robustness 20 | guards, citation re-read, seeded fallback, failure table (§7.5), validation on real data, switch precision table |
| Voice Experience 20 | latency + restart work (§7.6), native script, auditioned voices, audible demo contrast |
| Demo & skills.md 15 | frozen demo, backup video, skills.md with measured numbers |

**Business impact.** In PS07, rush shows up in about 1 in 5 transcribed calls and those calls book meetings at 13.6% vs 26.0% (PROVEN, observational). About 3 in 10 returning sellers carry a free-text fact our structured data lacks, mostly *when* to call and *why* they deferred; about 1 in 10 carry one that still matters next time; about 3% would be mis-handled from structured labels alone (PROVEN). VANI today uses one voice and style for all of them. Projection (ASSUMED, not a result): at ≈ 1,500 answered calls/day, ≈ 300 are rush calls; if crisp handling closed even a quarter of the rush meeting gap, that is ≈ 9 extra meetings/day, before any memory-timed callback gains. Caution, stated on the slide: three script-personalisation trials did not lift meetings (§5.4), so lift is to be proven by holdout after the event. Tamil: 46.6% of TN calls carry Tamil markers and there is no Tamil conversational voice — a gap we name, not demo.

---

## 13. Devil's advocate

1. **The frontier decider may never touch real data during the event.** Then D1/D2 ship from Sarvam-105b running our skill. That is acceptable; the slide says which model produced the shown specs.
2. **The agent may favour one voice gender.** An earlier test chose female for every language (PROVEN). By team-lead decision the agent still chooses gender with no flag; the scoreboard will show over time whether the choice works.
3. **Gating means the agent touches only ~40% of sellers.** That is the honest size of its value on PS07; the rest gets a seeded code persona with real reasons.
4. **Composing still increases variance.** Bucketed agreement reduces it; the fallback rate is measured today, not assumed.
5. **Text-level switches may not sound like a switch.** Measured words/reply and pause tests make the change visible; if punctuation does not create pauses, confusion relies on shorter sentences and a check question only.
6. **The lexicon has κ ≈ 0.03 with the evaluator.** Hence the 60-utterance precision gate; demo only on signals that pass.
7. **Widened demo contrast is not the production design.** Say so: demo bands show the space; production bands come from data.
8. **Evidence is mostly informed guesses.** The evidence tier says so per setting.
9. **Free-text shares are regex lower bounds** with ~40–60 manual reads per family; Sep evaluator coverage drop under-observes recent history.
10. **Personalisation lost 0 for 3 in PS07.** Our memory openings are personalisation; they may not lift meetings either. Claim fit and adaptation, not lift.
11. **Agreement ≠ correctness** (28% confident-wrong, GPQA benchmark, other domain: WEAK). Citations and pre-registered labels are the defence.
12. **Thresholds are invented:** gate cut, native-script 0.9, 600 chars, 0.8 precision, 40% fallback, 5 pp, half-lives.

## 14. Open questions

| # | Question | Who | By |
|---|---|---|---|
| 1 | May masked seller data go to a frontier model, reviewer and Jev? | Organisers | D1 15:30 |
| 2 | Does "core agent must be Sarvam" allow a frontier decider? | Organisers | D1 15:30 |
| 3 | Go beyond the 17:00 trigger and make Sarvam-105b default (review C1)? | Team lead | D1 17:00 |
| 4 | OpenRouter allowlist for 35.234.211.110, or LiteLLM from Daytona? | Key owner / M | D1 17:00 |
| 5 | B8 host: Daytona DNS/TLS, laptop + tunnel, or internal box? | S + team lead | D1 17:00 |
| 6 | Does per-call published-version selection work? Agent-level pace/pitch audible? | S (test) | D1 18:00 |
| 7 | Does Sarvam echo `decision_id`; variable length limit? | S (test) | D1 |
| 8 | Low-confidence cut for the gate | M after fixtures | D1 night |
| 9 | When will Sarvam enable Code Tools? | Sarvam (emailed) | — |
| 10 | Holdout/exploration on real sellers; reward window | Business | after event |

## 15. Glossary and evidence index

**Glossary.** *Cook* = compute a seller's spec before the call. *Gate* = rule deciding which sellers the agent runs on. *Bucketed bundle* = gender, pace band, pitch band, start language. *Propensity* = logged probability that code chose a value (needed for fair learning). *ε / h* = exploration / holdout share. *Thompson draw* = pick by sampling each option's success estimate. *Medoid* = the run closest to the others. *Aampe / Pega* = vendors whose per-dimension learning and weak-prior patterns we copy. *TnT-LLM / Clio* = published LLM clustering pipelines. *Evidence tier* = how strong the evidence is for one setting. *D-1* = the gating decision (closed).

| Claim | Tag | Source |
|---|---|---|
| Team decisions 1–7 | DOCUMENTED | `raw/hackathon/2026-10-09-team-decisions-persona-agent.md` |
| Review findings | DOCUMENTED | `outputs/plans/VANI persona architecture plan v4 - adversarial review.md` |
| Free-text shares, recency, NI conflicts, source split | PROVEN (regex lower bounds) | `outputs/research_notes/Agent decides VANI persona/freetext_share_ps07.md` |
| Rush 21%, 13.6% vs 26.0%; personalisation 0/3; 14.8% vs 17.8%; Tamil 46.6% | PROVEN (observational / trial) | `wiki/projects/vani-hackathon/persona-data-validation.md` |
| Recurrence, AUC, K=7, memory AUC 0.71 | PROVEN | `outputs/reports/Between run learning loops.md`; `outputs/research_notes/Data derived persona library/ps07_library_prototype.md` |
| Plan re-send 20/20 (10 calls, hand-written plans, scripted sellers); 0/8 price (hand-written); restarts ~17%; latency 2.1 s; language switch 6/6; tool skipped 0/4; "phir se" 4/4 | PROVEN (narrow scope) | `raw/research/2026-10-08-plan-stress-spike.md`, `…plan-following-spike.md` |
| SDK override ignored; per-language voices; pace/pitch via TTS API only | PROVEN | `raw/research/2026-10-08-voice-override-spike.md`, `2026-10-09-sarvam-voice-recheck.md`, `2026-10-09-per-language-voice-spike.md` |
| Voice fixed per call; no in-call TTS tool; Code Tools not enabled | DOCUMENTED / PROVEN | spike log; `raw/research/2026-10-08-sarvam-on-start-options-check.md` |
| OpenRouter 403 from Daytona; Jev not reachable from server; LiteLLM Jev 8/8 fail | PROVEN | `raw/research/2026-10-07-spike-log.md` |
| Gender collapse; Roman-script Hinglish 3/3; number words slip | PROVEN | `outputs/reports/Persona generator architecture.md` |
| Jev 49/51 (romanised, VPN laptop); Sarvam-105b ₹0.16 / 4.2 s; flat schema | PROVEN | `outputs/reports/Persona generator architecture.md`; `outputs/research_notes/Agent decides VANI persona/agent_as_decider.md` |
| Guards around agents; confidence inflation; propensity error | DOCUMENTED | `outputs/reports/Agent decides VANI persona.md` |
| 28% confident-wrong (GPQA); Etsy nightly per-buyer LLM (social scrape) | WEAK | same report; `raw/research/2026-10-09-last30days-agents-refine-personas-segments.md` |
| Gate cut, bands, thresholds, costs, projection | ASSUMED | this plan |
