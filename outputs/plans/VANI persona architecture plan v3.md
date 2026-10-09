# VANI Persona Design (PS04): high-level architecture plan v3

As of 2026-10-09 (hackathon day 1). For the team lead first, then an external reviewer. Method: top-down blocks, each with WHY / HOW (one layer beneath) / WHAT (input → output) / FEEDS (`.claude/skills/design-architecture/SKILL.md`). Architecture level only. Supersedes [v2](VANI%20persona%20architecture%20plan%20v2.md). The decision design comes from [Let the agent decide, let code guard](../reports/Agent%20decides%20VANI%20persona.md).

**Evidence tags.** **PROVEN** = measured by us (spike or PS07 aggregate). **DOCUMENTED** = official doc, the PS04 brief, a paper, or a `raw/` source. **ASSUMED** = our design choice or arithmetic, not yet tested.

**Binding intent (team lead).** The agent decides the VANI persona with tools. Code builds the fence around that decision.

## 0. Summary in simple words

1. VANI is the bot that calls sellers. This plan gives VANI a persona for each seller.
2. A VANI persona is VANI's voice, speed, pitch, language, tone and call plan.
3. Seller data is the input. It is not the persona.
4. We describe each seller with traits and states. A trait changes slowly. A state changes from call to call.
5. We keep a small library of VANI personas. Each persona is one published Sarvam agent version.
6. Each night, code makes a list of the allowed personas for each seller who gets a call the next day.
7. Then an AI agent reads the seller's data with tools. The agent gives each allowed persona a score. The agent selects one persona and writes the call plan.
8. The agent runs three times. Two of the three runs must agree.
9. Code checks each reason against the real data. Code rejects a reason that it cannot find.
10. Code, not the agent, makes the final draw. Code records the exact probability.
11. If the runs disagree or a check fails, code selects the persona and records this.
12. Code computes "no good fit". The agent does not decide it alone.
13. Each week, a job groups the "no good fit" reasons. A person approves each new persona.
14. During the call, our signal server changes VANI's mode when the seller is rushed, confused, frustrated or interested.
15. After each call, two learning loops update our tables. No model is trained.
16. We do not use a rule table. Rules only give starting values.

---

## 1. Changes from v2

| # | v2 said | v3 says | Why |
|---|---|---|---|
| 1 | Code candidates → agent **proposes** a ranking → code draws | **Agent decides**: scores every eligible persona 1–5 with cited evidence, chooses one, adapts settings within bounds, writes the plan. Code executes it unless a gate fails | Team-lead intent (binding); free text is the one input that changes a persona and only an LLM reads it (BCG NBA 2026, DOCUMENTED) |
| 2 | Agent sees code candidates with scoreboard probabilities | Code computes the **eligible set** (the fence) and pre-fetches estimates + scoreboard (n, effect, CI) as tool results; scoreboard leader is one candidate, not "the answer" | Avoids anchoring the agent on a baseline (ASSUMED effect, measured in §9) |
| 3 | One agent run; schema and guardrail validators | **3 runs, accept at ≥ 2/3**; 3/3 to override a decisive scoreboard cell; **citation validator** re-reads every cited field or free-text span; FAQ Q5/Q6 validators kept | 3-run agreement: 87–88% accuracy at 54–62% coverage (ICML 2026, DOCUMENTED); verbalised confidence inflated |
| 4 | Agent self-flags `no_good_fit` | **No-fit is computed**: reason-code agreement across runs + distance from known seller types + (later) outcome gap; checkable `missing_capability` bypasses distance | NOTA answers fail in both directions (30–50% drop; abstention inflation; DOCUMENTED) |
| 5 | Weekly Task B proposes personas | Weekly job **clusters no-fit reasons** (TnT-LLM / Clio pattern) with gates: support, two-window stability, coverage check, audible difference, drift freeze; human approves | Every production category-expansion system aggregates first (DOCUMENTED) |
| 6 | Agent cost "nightly, due sellers" | Explicit cost (ASSUMED ≈ ₹40–80K/day at 40K due sellers × 3 runs, unrouted) and an **open decision**: run on all due sellers vs only those with free text or low code confidence | Throughput and money now matter at k = 3 |
| 7 | Agent vs code: "side-by-side later" | **Pre-registered 2-day experiment** (≈ 40 synthetic sellers, 4 groups, 4 arms, labels by non-builders first) + open measurement of decision-changing free text | Earlier 23/23 vs 16/23 test was circular |
| 8 | B5 one block | B5 split: **B5a Fence (code) · B5b Agent decider · B5c Gates, draw, no-fit (code)** | Ownership and contracts per sub-block |
| 9 | Loop 2 feeds memory, scoreboard, library | Loop 2 also **feeds the agent's tools** (scoreboard, memory, library) | The agent's evidence is only as good as these tables |

Everything else in v2 holds: persona = VANI's persona; seller traits/states and the 7 seller types are input and explanation; three translation layers; 5 published versions incl. control; the voice facts; live switches with Jev; cook-ahead with staleness and fallback; two loops; day-one data; contracts and fixtures.

**Rules, said once.** There is no rule table anywhere as a component. Rules only seed starting values: the shrinkage weight α and the 28-day decay in the trait/state estimator, and 10–25 pseudo-call priors in scoreboard cells. Data overrides all of them.

---

## 2. End-to-end diagram

```
 SELLER DATA (input)                              B3 VANI PERSONA LIBRARY (versioned)
 profile · call log · evaluator outputs ·         P0 control + P1..P4 = levels on shared dimensions
 masked free-text summaries/objections · memory   + plan moves & branches (native script)
        │                                         + voice per language → 1 published Sarvam version
        ▼                                                          │
 B1 Seller context ─► B2 Trait/state estimator + seller type (distance)        B4 Scoreboard (n, effect, CI)
        │                         │                                                   │
 ┌──────┴─ NIGHTLY BATCH: only sellers due a call tomorrow (+ event re-cook) ────────┴──────────────┐
 │ B5a FENCE (code): eligible personas = published ∩ voice for start language ∩ guardrails ∩ not DNC │
 │                   + pre-fetched tool results (estimates, scoreboard cells, library, voices)        │
 │ B5b AGENT DECIDER (×3 runs): read-only tools (context+free text, memory, scoreboard, library,      │
 │     voices, similar sellers) → score every eligible persona 1–5 + cited evidence + reason_code    │
 │     → choose → settings within bounds → call plan (native script)                                 │
 │ B5c GATES (code): agree ≥2/3 (3/3 vs decisive cell) · citation check · FAQ Q5/Q6 · schema         │
 │     pass ─► draw over agent scores (exploration floor + P0 holdout) ─► LOG exact p · path=agent    │
 │     fail ─► code-only draw over eligible set ─► LOG exact p · path=fallback                        │
 │     no-fit computed: reason-code agreement × distance (× outcome gap later) ─► no-fit log         │
 │ B6 Spec store ─► dial time: stale? ──yes──► fast code-only path (no LLM)                          │
 └──────────────────────────────┬──────────────────────────────────────────────────────────────────┘
                                ▼ fresh
 B7 Compile ─► Sarvam call start: agent version · initial_language_name (selects voice) ·
               initial_bot_message (native script) · agent_variables{decision_id, persona_directive, seller_mode}
 LIVE:  seller ◄─voice─► Sarvam agent ──tool call each seller turn──► B8 SIGNAL SERVER
                            ▲        lexicon now (<5 ms) · Jev next turn (~480 ms) · code policy
                            └── {seller_mode, persona_directive = <plan> | Right now: <mode>} ◄┘
                                language switch: Sarvam built-in; logged from transcript
 POST-CALL: trace + outcome ─► B9 reviewer + outcome join
     ├─ LOOP 1 (switch) ─► B10 lexicon · thresholds · Jev wording ── frozen gold gate ──► B8
     └─ LOOP 2 (persona) ─► B11 memory · scoreboard · library ──► B2, B4, B3 = THE AGENT'S TOOLS ─► B5b
                              └─ weekly: cluster no-fit reasons ── code gates ── human ──► new version in B3
 B12 DATA LAYER (append-only, on premises): snapshot · decision (k runs, scores, citations, p, path) ·
     call · switch log · voice requested vs observed · outcome · review · no-fit · manifest
```

## 3. Block table

| Block | Why (PS04) | How (choice; rejected) | Input → Output | Feeds | Status |
|---|---|---|---|---|---|
| B1 Seller context | D1 "seller file in"; FAQ Q6 | Script, as-of rebuild; masked free text with span ids; *rej.* seller-file history columns (leak future) | seller rows, as_of → `seller_context` | B2, B5b tools | Leakage-free build PROVEN |
| B2 Trait/state estimator + seller type | Fit 25 | Beta posteriors (traits), exp(−gap/28 d) (states), nearest of 7 seller types + distance; *rej.* history label as identity | `seller_context` → `seller_estimates` | B5a/b, B4 key, B5c no-fit | Recurrence + K=7 PROVEN; estimator ASSUMED |
| B3 VANI persona library | Distinctness 20; voice 15 | Designer archetypes on shared dimensions; 5 versions; *rej.* fixed 6, factorial | cards, auditions → `persona_library_vN` | B5a/b, B7, B11 | Shape DOCUMENTED; levels ASSUMED |
| B4 Scoreboard | Evidence 15; fit 25 | Beta counts per seller type × persona (× voice gender); weak priors; *rej.* rule table | decisions ⨝ outcomes → `scoreboard_vN` | B5a/b/c, B11 | ASSUMED; empty of real data today |
| **B5a Fence** | D2; FAQ Q5 | Code eligible set + pre-fetched tool results; *rej.* agent sees full library incl. ineligible | estimates, library, scoreboard, flags → `agent_input` | B5b, B5c | ASSUMED |
| **B5b Agent decider** | D2 reasons; fit 25 | Sarvam-105b (or internal LiteLLM gateway) with read-only tools; per-candidate 1–5 scores; flat JSON; *rej.* "pick one or NONE", baseline-plus-delta framing, unguarded agent | `agent_input` (+ tool calls) → `agent_output` ×3 | B5c | ASSUMED; flat schema PROVEN reliable |
| **B5c Gates, draw, no-fit** | Evidence 15; learning | Agreement, citation, guardrail validators; code draw with exact p; code-only fallback; computed no-fit; *rej.* agent self-confidence as gate | 3 × `agent_output` → `persona_decision`, `nofit_row` | B6, B12, B11 | ASSUMED |
| B6 Cook scheduler + spec store | Fresh spec at dial | Nightly for due sellers; event re-cook; staleness check; reuse when inputs unchanged | dial list, events → ready spec | B7 | ASSUMED |
| B7 Compile + Sarvam agent | D3; voice 15 | Version per persona; voice by `initial_language_name`; native-script opening | spec → start payload + `call_config` | Sarvam, B8 | Voice route PROVEN |
| B8 Signal / switch server | Switches 25; D4 | Lexicon + Jev + code policy + per-seller thresholds; plan re-sent each turn | utterance + `call_config` → tool response + switch row | Sarvam, B12, B9 | Components PROVEN |
| B9 Reviewer + outcome join | Evidence; loops | Offline LLM, masked; two-key labels; declared reward | trace + events → `review`, `outcome` | B10, B11 | ASSUMED |
| B10 Loop 1: switch | Switches 25 | Edit cues, thresholds, Jev wording; frozen gold gate | reviews → `switcher_vN+1` | B8 | ASSUMED |
| B11 Loop 2: persona | Fit, evidence, distinctness | Memory + scoreboard update; weekly no-fit clustering; human | outcomes, reviews, no-fit rows → memory, scoreboard, library proposals | B2, B4, B3 → B5b tools | ASSUMED |
| B12 Data layer | Evidence; learning | Append-only JSONL → Parquet + DuckDB, on premises | all writes → views | all | ASSUMED |

---

## 4. Seller side: B1 and B2 (unchanged from v2, condensed)

**B1 Seller context.** A deterministic script that makes no decision and counts only events before `as_of`. Seller-file history columns cover all of Apr–Sep and leak the future, so history is rebuilt from call rows (PROVEN). It attaches **masked free-text summaries and objection notes, each with a span id**, so the agent can cite them and code can re-read them. Output: `seller_context = {snapshot_id, as_of, source_watermark, profile{…}, history{n_prior_calls, last_outcome, gap_days, outcome_shares}, objections{family: share}, signals{rush, terse, confusion, frustration, english_heavy, bot_question, interest: {k, n}}, observed_language, free_text[{span_id, call_id, kind, text_masked}], flags{dnc}, missing_fields[], completeness}`.

**B2 Trait/state estimator + seller type.** Seller history sets odds, not identity: rush recurs in 30.8% of next calls against a 20.8% base (n = 276); terse 41.0% vs 17.8%; English-heavy 13.8% vs 4.3%; confusion is a short state; not-interested decays with τ ≈ 28 d (PROVEN counts; fits ASSUMED). Pre-call data predicts in-call signals only at AUC 0.52–0.58, except English-heavy 0.68 (PROVEN). Traits use a Beta posterior shrunk to the seller-type rate; states use `exp(−gap/28 d)`; seller type = nearest of the 7 PS07 warm types (K=7, bootstrap ARI 0.868, PROVEN) with its **distance**, `cold` for sellers without stable structure (46–70% of anchors, PROVEN), and beyond-p95 distance marked far (11.2% of held-out warm sellers, PROVEN). Output: `seller_estimates = {snapshot_id, seller_type{id, distance, distance_pct, fit: ok|ambiguous|far|cold}, traits{name: {mean, n, ci}}, states{name: {value, gap_days, weight}}, language{start_guess, english_lean, source}, code_confidence}`.

The 7 seller types are input and explanation (FAQ Q1). They are never personas.

---

## 5. VANI side: B3 library and B4 scoreboard (unchanged from v2, condensed)

**B3 library.** Each VANI persona is a bundle of levels on shared dimensions over one fixed fact and compliance layer (Alexa+ pattern, DOCUMENTED). Audible levels (voice per language, pace, pitch) are fixed per published Sarvam version; formality, warmth, brevity and plan travel per call.

| Id | Archetype | Audible bundle | Per-call levels | First hypothesised for (ASSUMED) |
|---|---|---|---|---|
| P0 | Current VANI default | today's voice and pace | today's | Control/holdout; cold fallback |
| P1 | Crisp closer | brisk (≈ 1.05–1.1), lower pitch | brevity, directness high | Rush, terse, call-me-later |
| P2 | Patient guide | moderate (1.0; never slower on a confusion prior), warm | one idea per turn, yes/no checks | Confusion state, thin history, bot-question |
| P3 | Respectful advisor | moderate, measured | formality high, evidence-led | Meeting revisit, larger business |
| P4 | Warm re-engager | moderate, expressive | warmth high, easy exit | Short-call refuser, recent NI |

**Derivation of 5 (ASSUMED method).** (1) Only audible bundles need a version. (2) The trait/state evidence points to four delivery directions, plus P0 as control = 5; language collapses into per-language voice maps. (3) Learning cost: a 3-point meeting lift (≈ 13% → 16%) needs ≈ 2,000 calls per arm per segment; 8 segments × 3 plausible personas ≈ 48,000 explored calls against ≈ 1,500 answered calls a day in PS07 (PROVEN volume, ASSUMED arithmetic), so 5 personas give a first read in about a month. (4) Each version needs a voice per supported language; a gender twin doubles versions and is added only where traffic fills it. **Grow only through the weekly no-fit job (§8).**

**Voice facts.**
- Per-call SDK `text_to_speech_config` override is **ignored** (PROVEN, re-checked 2026-10-09).
- **Per-language voices + `initial_language_name` select the voice per call** (PROVEN 2026-10-09: Hindi → female 286 Hz; English → male 140 Hz). Limit: one voice per language per version.
- **Pace and pitch work on Bulbul v3/v4 via the TTS API** despite the docs (PROVEN: v4 aditya_hi_sales 104/150/162 Hz at pitch −0.5/0/+0.5). The agent-UI pitch slider is untested.
- **Native script** for all spoken text; romanised Indic input degrades TTS (DOCUMENTED). 222 Bulbul v4 voices to audition (DOCUMENTED).
- **Code Tools** (per-call voice within a language) requested from Sarvam by email 2026-10-09.

**B4 scoreboard.** Beta counts per (seller type × persona × voice gender where a twin exists), under a reward declared in advance; designer hypotheses enter as weak priors of 10–25 pseudo-calls (Pega StartingEvidence 25, DOCUMENTED); forgetting λ ≈ 0.8/month (ASSUMED). Only explored and holdout traffic may support a "works better" claim. Voice gender is a data-driven dimension: no quotas, no alarms; seller gender and age are never inferred. The tool view gives the agent **n, effect vs P0, 90% CI, p_best, source (prior|explored|holdout)**, never raw rows. PS07 had one VANI style, so **every cell is prior-only today** (DOCUMENTED).

---

## 6. B5 Persona decision: the agent decides inside a code fence

### 6.1 Three translation layers (unchanged)

| Layer | When set | What it carries | Example (prior rusher) |
|---|---|---|---|
| (a) Pre-call settings | Before dial; fixed for the call | Persona version (voice, pace, pitch), start language, robust default levels | P1 or a moderate persona; pace never slowed for confusion |
| (b) Plan contingency branches | Before dial; **re-sent every turn** | `on_rush`, `on_confusion`, `on_language`, `on_busy`, `on_frustration`; high prior promotes a branch into the opening | Time-box in line 1 |
| (c) Live-switch sensitivity | Before dial; used by B8 | Per-signal threshold lowered when the prior is high | 1 rush cue switches instead of 2 |

Live evidence always wins over the prior. One prior call may move at most two settings off default (ASSUMED). In v3 the **agent** sets (a) levels, (b) promotions and (c) sensitivity, all inside bounds that code enforces.

### 6.2 B5a Fence (code)

**WHY.** The agent must never choose something that cannot be dialled or that breaks a guardrail. Production agents run inside non-model checks (Salesforce Agent Script, Sierra, BCG NBA stack; DOCUMENTED).

**HOW.** Eligible set = personas with status `active` ∩ published Sarvam version ∩ a voice for the start language ∩ fixed guardrail set; DNC → no call at all. Code then **pre-fetches** the tool results the agent nearly always needs into the first prompt (Salesforce "pre-reasoning context gathering", DOCUMENTED): estimates, scoreboard cells for this seller type, eligible persona cards with their bounds, voice options. This cuts tool turns and cost.

**WHAT.** `agent_input = {decision_id, snapshot_id, seller_estimates, eligible[{persona_id, card_ref, bounds{formality, warmth, brevity, sensitivity}, voices{lang: gender}}], scoreboard[{persona_id, n, effect_vs_p0, ci90, p_best, source}], decisive_cell?: persona_id, free_text_index[{span_id, kind, call_date}], missing_fields[], versions{…}}`.

### 6.3 B5b Agent decider

**WHY.** D2 (spec with a reason per choice) and fit (25). Free-text history ("my son handles this now", repeated price objections) is the only input that can change the right persona and that code cannot read (DOCUMENTED, BCG 2026; Netflix LLM ranker over verbalised histories). Etsy runs one LLM call per buyer in a nightly batch (DOCUMENTED).

**HOW.** Sarvam-105b (internal LiteLLM gateway as fallback model), run **only for sellers due a call tomorrow** (Etsy pattern). Read-only tools beyond the pre-fetch:

| Tool | Returns |
|---|---|
| `get_seller_context` | snapshot, missing fields |
| `get_free_text(span_ids)` | masked summaries and objection notes, with span ids |
| `get_seller_memory` | traits, states, language preference, past personas, fit labels |
| `get_scoreboard(seller_type)` | n, effect, CI, p_best per persona |
| `get_persona_library` | cards, levels, bounds, plan moves, branches |
| `get_voice_options` | versions × languages × voice gender |
| `get_similar_sellers(k)` | aggregate outcomes of the nearest sellers by persona (counts only) |
| `submit_decision` (terminal) | `agent_output` below |

The agent (1) scores **every** eligible persona 1–5 on a fixed rubric, each with a `reason_code` and citations; (2) chooses one; (3) sets levels, branch promotions and sensitivity within the persona's bounds; (4) writes the call plan: opening in native script, personalisation only from fields that exist, objection order, escalation. The scoreboard leader appears as one candidate, not as "the answer". A flat JSON schema is mandatory (strict nested `json_schema` looped in 4/6 calls; flat never failed, PROVEN). Self-confidence is logged but never used as a gate (confidence ≥ 0.8 was wrong 48% of the time on GPQA, DOCUMENTED).

**WHAT (per run).**
```
agent_output = {decision_id, run_no, model, prompt_version,
  scores[{persona_id, score: 1..5, reason_code: fit|style_gap|missing_capability|conflicting_signals|insufficient_data,
          reason_text, citations[{kind: field|span, ref, quoted_value}]}],
  chosen_persona_id, start_language, levels{formality, warmth, brevity},
  plan{opening_native, steps[], personalisation[{field, line}], objection_order[], branches{on_rush: promoted|dormant, …}, escalation[]},
  sensitivity{rush, confusion, frustration, interest},
  missing_capability?{kind: language|voice_style|pace|other, detail}, self_confidence, tool_calls[]}
```

### 6.4 B5c Gates, draw and computed no-fit (code)

**WHY.** Learning needs an exact logged probability; an agent's pick has none (LLM exploration fails without algorithmic support; Decision Service saw up to 3.0× error from wrong probabilities; DOCUMENTED). Agreement and citations are checkable; confidence is not.

**HOW.**
1. **Agree.** Run B5b three times. Accept when ≥ 2 of 3 runs choose the same persona. If a decisive scoreboard cell exists (p_best ≥ 0.95 in this segment; none exist today) and the agent disagrees with it, require 3 of 3.
2. **Validate.** Citation validator: every cited field or span id must exist and the quoted value must match on re-read. Guardrails: schema; no digits, price words or internal labels in spoken text (FAQ Q5); greet-and-confirm-owner first; human-on-request kept; levels within bounds; confidence ≤ completeness (FAQ Q6). One repair call, then fail.
3. **Draw.** On pass: holdout share to P0 (e.g. 10%), exploration floor per eligible persona (e.g. 5%), the rest by softmax over the **median** agent scores. Code draws with a logged seed and logs the **exact probability**. The plan comes from the majority run. Exploration and holdout are off for judged demo sellers and logged as such.
4. **Fall back.** On disagreement or validation failure: code-only Thompson draw over the eligible set from the scoreboard; plan from the persona card's default moves plus field personalisation; logged `path: fallback` with its exact p.
5. **Compute no-fit** (never self-reported). Flag a seller when the agent's maximum score is ≤ 2 in ≥ 2 of 3 runs **with the same reason_code**, AND the B2 distance is beyond p95. A `missing_capability` the catalogue can confirm (e.g. Tamil preferred, no Tamil voice style in any version) bypasses the distance leg. Once persona-varied traffic exists, add the outcome-gap leg: the seller's group does worse under every persona than comparable sellers under their best. `insufficient_data` never counts as a vote. The seller still gets the best eligible persona at low confidence.

**WHAT.**
```
persona_decision = {decision_id, seller_key, snapshot_id, path: agent|fallback|dial_fallback,
  versions{library, scoreboard, estimator, prompt, model, validators, git_sha},
  runs[agent_output_ref ×3], agreement{n_agree, chosen_by_runs[]}, validator_results[],
  eligible[], weights[{persona_id, median_score, p}], chosen{persona_id, sarvam_agent_version, propensity, arm: agent|explored|holdout, seed},
  start_language, voice{voice_id, gender}, levels{…}, plan{…}, sensitivity{…},
  reasons[{persona_id, text, citations[]}], confidence, missing_fields[], overrides[]}
nofit_row = {decision_id, seller_key, max_scores[3], reason_codes[3], reason_text, distance_pct, missing_capability?, legs_met[]}
```
**FEEDS** B6; B12; `nofit_row` → B11 weekly job.

### 6.5 Volume and cost (ASSUMED; open decision)

Measured Sarvam-105b cost: ≈ ₹0.16 and 4.2 s for one structured call (PROVEN). At an **assumed** 40K sellers due per day (not a measured cadence), 3 runs per seller with tool loops cost **≈ ₹40–80K per day** and 5–8 h of batch at 20-way concurrency (ASSUMED). With pre-fetched tools in one call per run, ≈ ₹0.5 per seller (≈ ₹20K/day). Two reductions: (i) **reuse** a decision when snapshot, memory, library and scoreboard versions are unchanged, plus a 1–2% random audit re-run and always re-run distance-far sellers; (ii) **gate** the agent to sellers with free text or low code confidence; others take the code-only draw.

**Open decision D-1 (team lead):** run the agent on **all due sellers** (clean "agent decides" story, full cost) **or only on those with free text or low code confidence** (cost scales with that share, which is not yet measured; see §9.2). Throughput and rate limits, not money, may bind first.

### 6.6 B6 Cook-ahead, re-cook, dial-time check (unchanged)

40.5% of sellers have ≥ 2 calls and hold 71.3% of calls; median gap ≈ 1 day (PROVEN), so a nightly cook alone goes stale. (i) Nightly cook for tomorrow's dial list. (ii) Event re-cook after each outcome or accepted memory update (agent re-run if batch capacity allows; else code-only). (iii) Dial-time check: stale if any seller event after `source_watermark`, a version change, age > TTL (proposed 72 h), or an unpublished version → **fast code-only path** (no LLM, p95 < 1 s target, ASSUMED). DNC → no call. Store row `{seller_key, decision_id, cooked_at, source_watermark, versions, path, scheduled_dial_at}`; each call logs `spec_freshness: nightly|event|dial_fallback|default`.

---

## 7. Live call: B7 and B8 (unchanged)

### 7.1 Exactly what the Sarvam agent gets

| Sarvam input | Value | Evidence |
|---|---|---|
| Agent version | chosen persona's published version (voice map, pace, pitch) | Version route DOCUMENTED; per-call SDK override ignored (PROVEN) |
| `initial_language_name` | start language; **also selects the voice** | PROVEN 2026-10-09 |
| `initial_bot_message` | opening in **native script** (agent-written, validated) | Spoken verbatim (PROVEN) |
| `agent_variables` | `decision_id`, `persona_directive` (= plan + base mode), `seller_mode` | Works (PROVEN); `decision_id` echo per tool call untested |
| Per turn (tool response) | `{seller_mode, persona_directive = <plan> \| Right now: <mode>}` | Plan re-send 20/20 vs 23/28 (PROVEN) |

The fixed base prompt holds the pitch goal, product facts, prices and compliance text; no persona and no agent decision can change them (FAQ Q5). With the plan re-sent, 0/8 price-demand turns quoted an amount (PROVEN). `call_config = {decision_id, plan_prefix, base_mode, branches, sensitivity, priority, max_switches: 2, versions}`.

### 7.2 B8 Signal / switch server (live switches with Jev)

1. Each seller utterance arrives by Sarvam tool call in Devanagari ASR text; the tool fires 6–7 times per 4 turns, so decisions are idempotent per utterance (PROVEN).
2. **Decide now:** lexicon (romanised + Devanagari) < 5 ms.
3. **Correct next turn:** Jev (TypeSafe decision model, OpenRouter Decisions API) async, ~480 ms p50, 49/51 on a romanised smoke set (PROVEN; Devanagari untested). A synchronous LLM was rejected (~2.6 s, PROVEN).
4. **Code policy:** priority frustration > confusion > rush > interest; hysteresis; max 2 switches; per-seller thresholds from `sensitivity` (a prior rusher at p0 = 0.31 needs a cue ~1.7× weaker; ASSUMED arithmetic).
5. **Output every turn:** `persona_directive = <call plan> | Right now: <mode>`.
6. **Language switch:** Sarvam built-in (6/6, PROVEN); our tool is not called on that turn (4/4), so B8 logs it from the transcript with `source: sarvam_builtin`.
7. Known issues: "phir se pooch raha hoon, price batao" false confusion (4/4); ~17% restarted replies (hypothesis: early end-of-turn).

Switch row: `{decision_id, turn, signal, source: lexicon|jev|sarvam_builtin, confidence, threshold_used, change, reason, plan_step, switch_no, versions}`.

---

## 8. Between runs: B9 and the two loops

No model is trained. Only tables, lexicon, thresholds, memory and library change.

**B9 Reviewer + outcome join.** Offline LLM (internal gateway or Sarvam, masked) labels signal onsets, switch verdicts (correct/late/missed/false), and persona and plan fit. A label counts only with two keys (lexicon vs PS07 evaluator κ ≈ 0.03, PROVEN). Outcome join uses a declared reward and window.

**B10 LOOP 1, switch.** Missed → new cue; false → negative cue or context guard; late → earlier cues; Jev wording at most once. Gate: frozen gold set (≈ 350–400 August calls with Devanagari twins + canaries), no per-signal regression, flip list signed off. Feeds B8 on the next call.

**B11 LOOP 2, persona — now also the agent's evidence.** Outcomes and fit labels update **seller memory** (enumerated tags; triggers a B6 re-cook) and the **scoreboard** (counts with forgetting). These are exactly what `get_seller_memory` and `get_scoreboard` return, so each loop turn changes what the agent sees tomorrow. **Weekly no-fit job** (TnT-LLM / Clio pattern, DOCUMENTED): embed `reason_text` of flagged `nofit_row`s, cluster within each `reason_code`, cross-tab with distance and outcome gaps, LLM names each cluster and drafts a card. Code gates (ASSUMED values, shipped as config): support ≥ max(500, 0.5% of active) distinct sellers; stable across 2 windows (ARI or Jaccard ≥ 0.7; PS07 buffer reached only 0.54 Aug→Sep, PROVEN); coverage-matched misfit rate ≥ 2× base (so data sparsity is not mistaken for need); audible difference from the nearest persona; freeze if a prompt/model change moves the audit-sample no-fit rate by > 2 pp. A human approves with a rubric card; the non-tech member auditions the voice; **a new audible persona = a new published Sarvam version** entering with a weak prior as an explored arm. Rejections go to a "known non-gap" register.

| Loop | Learns from | Changes | Gate | Feeds |
|---|---|---|---|---|
| 1 Switch | reviewer switch verdicts | lexicon, thresholds, Jev wording | frozen gold + canaries + flip list | B8 |
| 2 Persona | outcomes, fit labels, no-fit rows | memory, scoreboard, library | two-key labels; clustering gates + human for library | B2, B4, B3 → **B5b tools**, B6 |

## 9. Validation block

### 9.1 Pre-registered fair 2-day experiment

**Set.** ≈ 40 synthetic sellers from aggregate patterns (no real text), 4 groups: (a) 10 structured-signal only (does the agent harm?); (b) 10 with free text that **changes** the right persona (the agent's edge); (c) 10 with distractor free text (over-reading); (d) 8–10 genuine no-fit (e.g. Tamil-preferring, no Tamil voice style). Scoreboard seeded prior-only, identical for all arms.

**Labels first.** Before any arm runs, two people who did not build the harness (team lead + non-tech member) write the expected `persona_id` or "no fit", 2–3 critical plan elements and a one-line rationale; a third adjudicates; inter-rater agreement reported; file hashed and committed. Labels must not come from estimator seed values.

**Arms.** Code-only · Design L (agent decides, self-reported no-fit, no gates) · V2 (baseline + bounded change) · **merged (this plan)**. Same model, same tool snapshots, 5 repetitions per seller per arm (≈ 800 runs, ≈ ₹250–500, ASSUMED). One harness with switches: anchor on/off, gates on/off, k = 1/3.

**Metrics.** Accuracy per group; free-text sensitivity (b); distractor robustness (c); no-fit precision/recall; confident-wrong rate; consistency over 5 reps; citation validity; fallback rate, cost, latency. A judge model scores plan wording only, from a different family, blind to arm.

**Adoption rule (written into the label file).** Keep the merged design if it beats V2 on (b) by ≥ 15 pp, is not worse than V2 or code-only by > 5 pp on (a) and (c), has confident-wrong ≤ V2, and no-fit F1 ≥ Design L. Otherwise switch to the V2 framing with the same safeguards. If ungated L beats merged on (b) and loses nothing on (c), report that gates cost accuracy. Power is low (≈ 30 pp detectable at n = 10); analyse paired (McNemar). Schedule: labels this afternoon, batch tonight, analysis by 10:00 day 2, before integration step 5.

### 9.2 Open measurement

**Share of due sellers with decision-changing free text.** M computes from PS07 aggregates the share of calls with a non-empty objection or summary (upper bound), then from group (b)-style review of a masked sample the share where it changes the persona. Small share → the agent's edge applies to few sellers, and D-1 leans to gating.

---

## 10. B12 Data created from day one (cannot be backfilled)

| Record | Key | Must hold |
|---|---|---|
| `seller_snapshot` | snapshot_id | exact B1 output incl. span ids; extract_version; missing fields |
| `decision` | **decision_id** (passed in `agent_variables`, written on every switch row) | all versions; eligible set; **all 3 runs** (scores, reason codes, citations, tool trace); agreement; validator results; weights; **propensity**, seed, arm, path |
| `nofit_row` | decision_id | per-run max scores, reason codes, reason text, distance pct, legs met |
| `call` | call_id, decision_id | **voice requested vs observed** (median F0: male ~85–155 Hz, female ~165–255 Hz, PROVEN technique); switch log; latency |
| `outcome` | decision_id, kind | declared reward id, join window, default 0 |
| `review` | decision_id | reviewer and human labels; gold-set hash |
| manifest | version id | hashes for library, scoreboard, lexicon, thresholds, prompts, validators |

Append-only JSONL → Parquet + DuckDB in git-ignored `data/`. Backfilled PS07 rows: `propensity = null`, `causal_claim_allowed = false`.

## 11. Work split for 3 people

**Hour 0–2, all three:** contract files in `app/contracts/` (JSON Schema + one example each): `seller_context`, `seller_estimates`, `persona_library`, `scoreboard`, **`agent_input`, `agent_output`** (scores, citations, chosen persona, settings, plan, reason codes, missing capability), `persona_decision`, `nofit_row`, `call_config`, `sarvam_start_payload`, `tool_turn`, `switch_log_row`, `call_record`, `review`, `outcome`. Fixtures: 6 synthetic seller files with masked free-text spans, a 2-persona mini library, a **mock agent** returning 3 fixed `agent_output`s (one agreeing pair, one bad citation), recorded utterance lists per signal.

| Member | Owns | Tests alone with | Done when |
|---|---|---|---|
| **S — strong dev** (live path) | B7, Sarvam versions + per-language voices, B8, switch log, F0 check, B12 call/switch records | fixture `persona_decision` + `call_config`; utterance lists | Live call follows the plan, one live switch logged, voice requested = observed |
| **M — second member** (decision path) | B1, B2, B4, **B5a fence, B5b agent decider (prompt, tools, k = 3), B5c gates/draw/no-fit**, B6, decision records; experiment harness; §9.2 measurement | fixture sellers; stub library/scoreboard; mock agent first, real Sarvam-105b second | One command turns sample seller files into validated `persona_decision` JSON with 3 runs, citations, exact p; fallback path proven by the bad-citation fixture |
| **N — non-tech member** | B3 cards, plan moves and branches in native script, voice auditions; B9 gold labels; **experiment labels with team lead (before any run)**; demo, slide, skills.md | library JSON via M's schema check; labelling sheet | Library v1 approved; experiment labels committed; ≥ 150 gold calls labelled; demo recorded |

**Integration order.** (1) Contracts + fixtures. (2) Parallel: S live call from a fixture decision; M fence + gates + draw on the mock agent; N library v1 and experiment labels. (3) M swaps in the real agent; experiment runs tonight. (4) Join M → S: real decisions drive live calls. (5) Adopt merged or V2 framing per §9.1 rule. (6) Switch log + 2–3 contrasting demo sellers in 2 languages. (7) Loops as recorded artefacts: one reviewed call, one gated lexicon diff (one rejected), one scoreboard update, one no-fit clustering run (expected to propose nothing). Cut order if late: weekly clustering, Jev wording, k = 3 (drop to k = 1 + citation check, labelled as such); the code-only path alone still meets D1/D2.

## 12. How PS04 is met

| PS04 item | Met by | Shown as |
|---|---|---|
| D1 generator on sample files | B1 → B2 → B5a/b/c (→ B6) | `persona_decision` per seller |
| D2 spec with reasons | agent per-persona scores with cited, re-checked evidence | spec + "why" panel |
| D3 live demo, ≥ 1 switch | B7 + B8 | recording + agent id |
| D4 switch log | B8 rows incl. `sarvam_builtin` | table |
| D5 one slide | sample spec + seller evidence + diagram | slide |
| Fit 25 | traits/states, memory (AUC 0.71 vs 0.58, PROVEN), agent reading free text | per-seller reasons |
| Switches 25 | lexicon now, Jev next turn, per-seller thresholds, plan kept | live switch + log |
| Distinctness 20 | audible versions + per-seller plan; library grows only on evidence | A/B audio |
| Voice 2+ languages 15 | per-language voices, native script, built-in switch | demo |
| Evidence 15 | PS07-backed seller side; logged p; experiment with pre-registered labels | evidence table |

## 13. Devil's advocate

1. **Agreement ≠ correctness.** 28% of cases were confidently wrong across every runner tested (DOCUMENTED). Three agreeing runs can be wrong together. Defence: citation validator, pre-registered labels, holdout. Agreement is a gate, not truth.
2. **The 3-run gate means code decides for ~40% of sellers.** At 54–62% coverage (DOCUMENTED, open benchmarks) the fallback fires often, which weakens "the agent decides". A 5-persona choice should agree more (ASSUMED). Report fallback rate; above ~30% means an unclear rubric or overlapping personas, a library problem.
3. **Cost.** ≈ ₹40–80K/day ungated at 40K due sellers (ASSUMED). This is a recurring cost for an edge that is unmeasured (§9.2). D-1 must be decided on data.
4. **The scoreboard is empty today.** PS07 had one style, so every VANI-side cell is a designer prior. The agent decides on seller-side evidence and free text. Claim fit, distinctness and live switching, not lift, until ≈ 2,000 calls per arm per segment.
5. **PS07 shows no new persona.** p95 misfits are coverage artefacts with normal outcomes (64.8% vs 8.1% transcript signals; MF 9.9% vs 11.4%, PROVEN). "Propose nothing" is the correct output on real data; present it as the guard working. The one demonstrable gap (e.g. no Tamil voice style) a SQL query also finds; the agent's added value is reasons for gaps no query anticipates.
6. **Free text is evidence-like.** Evidence tools induce overconfidence (DOCUMENTED); the one input that justifies the agent is the one most likely to be over-read. Group (c) measures this.
7. **"Merged = V2 renamed."** With the same fence, they differ only in default and anchoring. If group (b) shows no gain, switch framing and say so.
8. **FAQ Q1 fixed library.** Output is a per-seller spec (version + language + levels + plan + thresholds), not a library pick. Lead the demo with it; ask organisers.
9. **Data on premises.** The agent reads masked free text; Jev receives live utterances. Use the internal gateway or Sarvam, synthetic sellers until an organiser ruling.
10. **Voice and live-path limits.** One voice per language per version; Code Tools pending; agent-UI pitch untested; Jev untested on Devanagari; ~17% restarts; signal server single point of failure for plan re-send.
11. **Thresholds are invented.** 500 sellers, ARI 0.7, 2 pp drift, p_best 0.95, 15 pp margin, floors and holdout share are config, not findings.

## 14. Open questions

| # | Question | Who | Decides |
|---|---|---|---|
| D-1 | **Run the agent on all due sellers, or only those with free text or low code confidence?** | Team lead (after §9.2) | Cost; fallback share |
| 2 | Experiment result: agent selects (merged) vs agent edits baseline (V2 framing) | §9.1 rule | B5b prompt framing |
| 3 | Daily due-seller count (40K is ASSUMED) and Sarvam-105b rate limits | Business / Sarvam | Batch window, k |
| 4 | Does Sarvam echo `decision_id` in every tool payload? | Test | Join key |
| 5 | Will Sarvam enable Code Tools or a non-overwritten plan variable? | Sarvam (emailed 2026-10-09) | Version count |
| 6 | Is the agent-UI pitch slider audible on v4? | Test | Pitch dimension |
| 7 | Can seller free text go to the agent model, reviewer and Jev? | Organisers | Agent on real data |
| 8 | May we explore and hold out on real sellers? Reward and join window? | Business | Scoreboard learning |
| 9 | Does a library + per-seller spec satisfy FAQ Q1? | Organisers | Demo framing |
| 10 | Staleness TTL and fallback latency budget | Team lead | B6 |

## 15. Evidence index

| Claim | Tag | Source |
|---|---|---|
| Trait/state recurrence; NI τ ≈ 28 d | PROVEN (fits ASSUMED) | `outputs/reports/VANI persona translation and library.md`; `outputs/reports/Between run learning loops.md` |
| K=7 ARI 0.868; cold ARI ≤ 0.44; 11.2% far; buffer ARI 0.54; misfits = coverage | PROVEN | `outputs/research_notes/Data derived persona library/ps07_library_prototype.md` |
| Memory AUC 0.71 vs 0.58; median gap 1.02 d; 40.5% / 71.3% | PROVEN | `outputs/reports/Between run learning loops.md` |
| Plan re-send, language switch, 0/8 price, restarts | PROVEN | `raw/research/2026-10-08-plan-stress-spike.md`, `…plan-following-spike.md` |
| SDK override ignored; per-language voices; pace/pitch v3/v4; native script | PROVEN / DOCUMENTED | `raw/research/2026-10-08-voice-override-spike.md`, `2026-10-09-sarvam-voice-recheck.md`, `2026-10-09-per-language-voice-spike.md` |
| Jev 49/51 ~480 ms; sync LLM ~2.6 s; Sarvam-105b ₹0.16 / 4.2 s; flat schema | PROVEN | `outputs/reports/Persona generator architecture.md`; `outputs/research_notes/Agent decides VANI persona/agent_as_decider.md` |
| Guards around agents; 3-run agreement; confidence inflation; NOTA; LLM exploration; propensity error | DOCUMENTED | `outputs/reports/Agent decides VANI persona.md` |
| No-fit clustering (TnT-LLM, Clio); computed no-fit legs | DOCUMENTED / ASSUMED | `outputs/research_notes/Agent decides VANI persona/new_persona_signals.md` |
| Etsy nightly per-buyer LLM; PersonaAgent | DOCUMENTED | `raw/research/2026-10-09-last30days-agents-refine-personas-segments.md` |
| 5 versions; mappings; costs at 40K; all thresholds | ASSUMED | this plan |
| 23/23 vs 16/23 rules vs LLM | Not evidence (circular labels, no free text) | `outputs/reports/Persona generator architecture.md` |
