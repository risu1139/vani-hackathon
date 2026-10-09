# VANI Persona Design (PS04): high-level architecture plan v4

As of 2026-10-09 (hackathon day 1). Written for the team lead first, then an external reviewer. Method: top-down blocks, each with WHY / HOW (one layer beneath) / WHAT (input → output) / FEEDS (`.claude/skills/design-architecture/SKILL.md`). Architecture level only. Supersedes [v3](VANI%20persona%20architecture%20plan%20v3.md). Binding decisions: [team decisions 2026-10-09](../../raw/hackathon/2026-10-09-team-decisions-persona-agent.md). Decision-design research: [Let the agent decide, let code guard](../reports/Agent%20decides%20VANI%20persona.md).

**Evidence tags.** **PROVEN** = measured by us (spike or PS07 aggregate). **DOCUMENTED** = official doc, the PS04 brief, a paper, or a `raw/` source. **ASSUMED** = our design choice or arithmetic, not yet tested.

**Binding intent (team lead, 2026-10-09).** The agent composes each seller's VANI persona with tools. Library personas are starting points, not a menu. Code checks only guardrails and what the platform can play. The agent suggests new library personas; a human adds them. The decider runs on a frontier model; Sarvam runs the voice agent.

## 0. Summary in simple words

1. VANI is the bot that calls sellers. This plan gives VANI a persona for each seller.
2. A VANI persona is VANI's voice, speed, pitch, language, tone and call plan.
3. Seller data is the input. It is not the persona.
4. We describe each seller with traits and states. A trait changes slowly. A state changes from call to call.
5. We keep a small library of VANI personas. Each library persona is a starting point.
6. Each night, an AI agent reads the data of each seller who gets a call the next day.
7. The agent composes that seller's own VANI persona. It sets each part and gives a reason with evidence for each part.
8. The agent can mix library personas. It can also make a new combination.
9. The agent runs three times. Code joins the three results part by part.
10. Code checks the facts, the prices, the compliance text and the do-not-call list. Code checks each reason against the real data.
11. Code also finds the nearest voice that Sarvam can play. Code records what we asked for and what played.
12. Sometimes code changes one part on purpose, to learn. Code records the exact probability.
13. If the checks fail, code makes the persona without the agent. Code records this.
14. If the agent's persona is far from all library personas, code records it as a suggestion.
15. Each week, a job groups the suggestions. A person approves each new library persona.
16. During the call, our signal server changes VANI's mode when the seller is rushed, confused, frustrated or interested.
17. After each call, two learning loops update our tables. No model is trained.
18. We do not use a rule table. Rules only give starting values.

---

## 1. Changes from v3

| # | v3 said | v4 says | Why |
|---|---|---|---|
| 1 | Fence = **eligible persona list**; agent scores each 1–5 and **selects** one | Fence = **context only** (library personas as starting points with evidence, estimates, scoreboard, voice options). Agent **composes** the persona across all dimensions, may mix or create, cites evidence per setting | Team decision 3 (binding) |
| 2 | Agreement = ≥ 2/3 runs pick the same persona | Agreement = ≥ 2/3 runs agree on the **audible bundle + key plan choices**; other dimensions settled by majority/median; else fallback | Composed specs have no single id to vote on |
| 3 | Draw over agent scores per persona; propensity per persona | Code-sampled exploration **perturbs one dimension at a time** from the agent's composition; propensity logged **per dimension** + exploration flag | Keeps exact p with a composed spec |
| 4 | Computed **no-fit** (reason-code agreement × seller distance × outcome gap) | Primary signal = **suggestion**: composed persona far from every library persona in **persona-dimension space** → `suggestion_row` with full spec + reasons | Team decision 4 (binding) |
| 5 | Weekly job clusters no-fit reasons | Weekly job clusters **suggestions** (same TnT-LLM / Clio pattern and gates; outcome evidence when available); human approves | Single suggestions are noisy (DOCUMENTED) |
| 6 | Validators incl. "levels within persona bounds" | B5c checks **only** guardrails (FAQ Q5 facts/prices/compliance, DNC, FAQ Q6 confidence vs missing data, citations) and **platform playability** | Team decision 3 |
| 7 | Voice = 5 published versions; per-language voice route | Preferred = Sarvam **Code Tools on-start tool** per call (requested 2026-10-09); demo = **versions built to match the agent's recommended personas** + proven per-language route; playability maps requested → nearest playable, logs both | Team decision 6 |
| 8 | Decider = Sarvam-105b | Decider = **frontier-model agent** (Claude Code-style agent + skill) on a **Daytona sandbox**, via OpenRouter or internal LiteLLM; Sarvam-105b fallback; model id logged | Team decision 5 |
| 9 | Scoreboard per seller type × persona | Scoreboard **per seller type × dimension × level** (Aampe decomposition) plus a library-persona view | Composed personas rarely repeat as whole bundles |
| 10 | Loop 2 feeds memory, scoreboard, library | Loop 2 feeds **suggestions**, scoreboard and memory into the agent's tools | Team decision 4 |
| 11 | §9.2 open measurement | Placeholder §9.2 "Free-text share in PS07": **running**; D-1 depends on it | Team-lead request |

Everything else in v3 holds: persona = VANI's persona; seller traits/states and the 7 seller types are input and explanation; three translation layers; control P0 with holdout; voice facts; live switches with Jev; cook-ahead with staleness and code-only dial fallback; 3-run agreement; citation validator; two loops; day-one data; contracts and fixtures.

**Rules, said once.** There is no rule table anywhere as a component. Rules only seed starting values: the shrinkage weight α and 28-day decay in the estimator, the starting levels on library cards, and 10–25 pseudo-call priors in scoreboard cells. Data overrides all of them.

---

## 2. End-to-end diagram

```
 SELLER DATA (input)                               B3 VANI PERSONA LIBRARY (versioned; STARTING POINTS)
 profile · call log · evaluator outputs ·          P0 control + P1..P4 = levels on shared dimensions
 masked free-text summaries/objections · memory    + evidence + plan moves/branches (native script)
        │                                                          │
        ▼                                                          │        B4 Scoreboard (per dimension × level,
 B1 Seller context ─► B2 Trait/state estimator + seller type       │           + library view; n, effect, CI)
        │                         │                                │                   │
 ┌──────┴─ NIGHTLY BATCH: sellers due a call tomorrow (+ event re-cook) ─────────────────┴────────────────┐
 │ B5a CONTEXT (code): DNC → no call · pre-fetch estimates, library personas + evidence, scoreboard,       │
 │                     voice options, playable versions, free-text index                                   │
 │ B5b AGENT COMPOSER (frontier model on Daytona, ×3 runs; Sarvam-105b fallback): read-only tools ─►      │
 │     composed persona spec: every dimension = {value, citations, confidence, origin}                    │
 │     + plan (native script) + branches + sensitivity + optional suggestion_reason                       │
 │ B5c GUARD + SETTLE (code): citations · FAQ Q5/Q6 · DNC · schema                                        │
 │     agree ≥2/3 on audible bundle + key plan choices → settle rest by majority/median                    │
 │     playability: requested bundle → nearest playable version/voice (log requested vs played)           │
 │     explore: holdout→P0, or perturb ONE dimension (ε) → LOG per-dimension p + flag · path=agent        │
 │     fail ─► code-only spec (library start point + scoreboard) ─► LOG p · path=fallback                  │
 │     far from every library persona (persona-dimension distance) ─► suggestion_row                      │
 │ B6 Spec store ─► dial time: stale? ──yes──► fast code-only path (no LLM)                               │
 └──────────────────────────────┬────────────────────────────────────────────────────────────────────────┘
                                ▼ fresh
 B7 Compile ─► Sarvam start: [Code Tools on-start: speaker, pace, pitch, opening, variables]  (preferred)
                             [else: matching published version + initial_language_name (selects voice)] (demo)
                             + initial_bot_message (native) + agent_variables{decision_id, persona_directive, seller_mode}
 LIVE:  seller ◄─voice─► Sarvam agent ──tool call each seller turn──► B8 SIGNAL SERVER
                            ▲      lexicon now (<5 ms) · Jev next turn (~480 ms) · code policy
                            └── {seller_mode, persona_directive = <plan> | Right now: <mode>} ◄┘
 POST-CALL: trace + outcome ─► B9 reviewer + outcome join
     ├─ LOOP 1 (switch) ─► B10 lexicon · thresholds · Jev wording ── frozen gold gate ──► B8
     └─ LOOP 2 (persona) ─► B11 memory · per-dimension scoreboard · suggestions ──► B2, B4 = AGENT'S TOOLS ─► B5b
                              └─ weekly: cluster suggestions ── code gates ── human ──► library persona in B3
                                                                                    (+ Sarvam version if audible)
 B12 DATA LAYER (append-only, on premises): snapshot · decision (3 runs, per-dimension values, citations, model id,
     per-dimension p, explore flag, path) · call · voice requested vs played vs observed · switch log · outcome ·
     review · suggestion · manifest
```

## 3. Block table

| Block | Why (PS04) | How (choice; rejected) | Input → Output | Feeds | Status |
|---|---|---|---|---|---|
| B1 Seller context | D1; FAQ Q6 | Script, as-of rebuild; masked free text with span ids; *rej.* seller-file history columns (leak future) | seller rows, as_of → `seller_context` | B2, B5b tools | Leakage-free build PROVEN |
| B2 Trait/state estimator + seller type | Fit 25 | Beta posteriors, exp(−gap/28 d), nearest of 7 types + distance; *rej.* history label as identity | `seller_context` → `seller_estimates` | B5a/b, B4 key | Recurrence + K=7 PROVEN; estimator ASSUMED |
| B3 VANI persona library | Distinctness 20; voice 15 | Archetypes on shared dimensions = **starting points with evidence**; grows only via approved suggestions; *rej.* fixed menu, factorial | cards, auditions, approved suggestions → `persona_library_vN` | B5a/b, B5c distance, B7 | Shape DOCUMENTED; levels ASSUMED |
| B4 Scoreboard | Evidence 15; fit 25 | Beta counts per seller type × **dimension × level** + library view; weak priors; *rej.* rule table, whole-bundle cells only | decisions ⨝ outcomes → `scoreboard_vN` | B5a/b, B11 | ASSUMED; prior-only today |
| **B5a Context** | D2; FAQ Q5 | Code pre-fetch of evidence; DNC stops the call; *rej.* eligible-list fence | estimates, library, scoreboard, voices → `agent_input` | B5b | ASSUMED |
| **B5b Agent composer** | D2 reasons; fit 25 | Frontier model + skill on Daytona, read-only tools, flat JSON, k = 3; Sarvam-105b fallback; *rej.* select-only, unguarded agent | `agent_input` (+ tools) → `agent_output` ×3 | B5c | ASSUMED; flat schema PROVEN |
| **B5c Guard, settle, explore** | Evidence 15; learning | Guardrail + citation validators; per-dimension agreement; playability map; one-dimension exploration with exact p; code-only fallback; suggestion by distance; *rej.* agent self-confidence as gate, "levels within bounds" fence | 3 × `agent_output` → `persona_decision`, `suggestion_row` | B6, B12, B11 | ASSUMED |
| B6 Cook scheduler + spec store | Fresh spec at dial | Nightly for due sellers; event re-cook; staleness check | dial list, events → ready spec | B7 | ASSUMED |
| B7 Compile + Sarvam agent | D3; voice 15 | Code Tools on-start (preferred) or matching version + per-language voice (demo); native script | spec → start payload + `call_config` | Sarvam, B8 | Per-language route PROVEN; Code Tools pending |
| B8 Signal / switch server | Switches 25; D4 | Lexicon + Jev + code policy + per-seller thresholds; plan re-sent each turn | utterance + `call_config` → tool response + switch row | Sarvam, B12, B9 | Components PROVEN |
| B9 Reviewer + outcome join | Evidence; loops | Offline LLM, masked; two-key labels; declared reward | trace + events → `review`, `outcome` | B10, B11 | ASSUMED |
| B10 Loop 1: switch | Switches 25 | Edit cues, thresholds, Jev wording; frozen gold gate | reviews → `switcher_vN+1` | B8 | ASSUMED |
| B11 Loop 2: persona | Fit, evidence, distinctness | Memory + per-dimension scoreboard; weekly suggestion clustering; human | outcomes, reviews, suggestions → memory, scoreboard, library | B2, B4, B3 → B5b tools | ASSUMED |
| B12 Data layer | Evidence; learning | Append-only JSONL → Parquet + DuckDB, on premises | all writes → views | all | ASSUMED |

---

## 4. Seller side: B1 and B2 (unchanged from v3, condensed)

**B1.** A deterministic script; counts only events before `as_of`; rebuilds history from call rows because seller-file history columns leak Apr–Sep (PROVEN). Attaches masked free-text summaries and objection notes with span ids so the agent can cite them and code can re-read them. Output `seller_context = {snapshot_id, as_of, source_watermark, profile{…}, history{n_prior_calls, last_outcome, gap_days, outcome_shares}, objections{family: share}, signals{rush, terse, confusion, frustration, english_heavy, bot_question, interest: {k, n}}, observed_language, free_text[{span_id, call_id, kind, text_masked}], flags{dnc}, missing_fields[], completeness}`.

**B2.** History sets odds, not identity: rush recurs 30.8% vs 20.8% base (n = 276); terse 41.0% vs 17.8%; English-heavy 13.8% vs 4.3%; not-interested decays with τ ≈ 28 d (PROVEN counts; fits ASSUMED). Pre-call data predicts in-call signals at AUC 0.52–0.58, except English-heavy 0.68 (PROVEN). Seller type = nearest of 7 PS07 warm types (bootstrap ARI 0.868, PROVEN) with distance; `cold` where no stable structure. Output `seller_estimates = {snapshot_id, seller_type{id, distance, distance_pct, fit}, traits{…}, states{…}, language{start_guess, english_lean, source}, code_confidence}`. Seller types are input and explanation (FAQ Q1), never personas.

---

## 5. VANI side: B3 library and B4 scoreboard

### 5.1 Persona dimensions (the shared space)

Every VANI persona, library or composed, is one point on the same dimensions over a fixed fact and compliance layer (Alexa+ pattern, DOCUMENTED).

| Group | Dimension | Values (ASSUMED levels) | Audible? |
|---|---|---|---|
| Voice | voice gender; style voice (Bulbul voice id per language) | from 222 Bulbul v4 voices, auditioned (DOCUMENTED) | yes |
| Delivery | pace; pitch | pace 0.9–1.15 in 5 bands; pitch −0.5…+0.5 in 3 bands | yes |
| Language | start language; English lean | Sarvam languages with a voice | yes (selects voice today) |
| Tone | formality; warmth; brevity | 1–5 each | no (prompt) |
| Plan | opening move; plan steps; personalisation facts; objection order; escalation | moves from library cards or new, native script | no |
| Adaptation | contingency branches (promoted/dormant); live-switch sensitivity per signal | per signal | no |

### 5.2 B3 library = starting points

| Id | Archetype | Audible bundle | Per-call levels | First hypothesised for (ASSUMED) |
|---|---|---|---|---|
| P0 | Current VANI default | today's voice and pace | today's | Control/holdout; fallback |
| P1 | Crisp closer | brisk (≈ 1.05–1.1), lower pitch | brevity, directness high | Rush, terse, call-me-later |
| P2 | Patient guide | moderate (1.0; never slower on a confusion prior), warm | one idea per turn | Confusion, thin history, bot-question |
| P3 | Respectful advisor | moderate, measured | formality high, evidence-led | Meeting revisit, larger business |
| P4 | Warm re-engager | moderate, expressive | warmth high, easy exit | Short-call refuser, recent NI |

Each card carries its **evidence** (scoreboard view, n, source) so the agent can weigh it. The agent may take a card whole, mix two (e.g. P1 pace + P4 warmth), or set a new combination. Five cards remain the right size to learn from (≈ 2,000 calls per arm per segment for a 3-point lift; ≈ 1,500 answered calls/day in PS07; PROVEN volume, ASSUMED arithmetic). The library grows only through approved suggestions (§6.5).

**Voice facts.** Per-call SDK `text_to_speech_config` override is ignored (PROVEN, re-checked 2026-10-09). Per-language voices + `initial_language_name` select the voice per call (PROVEN: Hindi → female 286 Hz; English → male 140 Hz); limit one voice per language per version. Pace and pitch work on Bulbul v3/v4 via the TTS API (PROVEN). Native script for all spoken text (DOCUMENTED). Code Tools on-start context carries `speaker_id`, pace, pitch, `initial_bot_message`, `initial_language_name`, `set_agent_variable` (DOCUMENTED, SDK), but is **not enabled for our account**; requested by email 2026-10-09.

### 5.3 B4 scoreboard, per dimension

**WHY.** A composed persona rarely repeats as a whole bundle, so per-bundle cells would starve. Aampe learns each dimension separately per segment (DOCUMENTED, vendor paper); 3 voices × 3 paces × 3 tones = 27 joint arms, each starved (ASSUMED arithmetic). **HOW.** Beta counts per (seller type × dimension × level), weak priors of 10–25 pseudo-calls (Pega, DOCUMENTED), forgetting λ ≈ 0.8/month (ASSUMED); a library view aggregates calls whose spec is nearest each library persona. Per-dimension learning assumes little interaction; a pairwise cell is added only where traffic fills it (ASSUMED). Only explored and holdout traffic supports a "works better" claim. Voice gender is a data-driven dimension: no quotas, no alarms; seller gender and age are never inferred (team decision 7). **WHAT.** Tool view: `{seller_type, dimension, level, n, effect_vs_p0, ci90, p_best, source: prior|explored|holdout}`. Every cell is prior-only today (PS07 had one VANI style).

---

## 6. B5 Persona decision: the agent composes, code guards

### 6.1 Three translation layers (unchanged)

| Layer | When set | Carries | Example (prior rusher) |
|---|---|---|---|
| (a) Pre-call settings | Before dial; fixed for the call | voice, pace, pitch, start language, tone levels | brisk pace; never slowed for confusion |
| (b) Contingency branches | Before dial; re-sent every turn | `on_rush`, `on_confusion`, `on_language`, `on_busy`, `on_frustration`; high prior promotes a branch into the opening | time-box in line 1 |
| (c) Live-switch sensitivity | Before dial; used by B8 | per-signal threshold | 1 rush cue switches instead of 2 |

Live evidence always wins over the prior. The agent sets all three layers.

### 6.2 B5a Context (code)

**WHY.** The agent needs the evidence in hand; it does not need a menu. **HOW.** DNC → no call at all (no agent run). Code pre-fetches what the agent nearly always needs into the first prompt (Salesforce pre-reasoning context gathering, DOCUMENTED): estimates; library personas as starting points with their evidence; per-dimension scoreboard cells for this seller type; voice options and playable versions; the free-text index. **WHAT.**
```
agent_input = {decision_id, snapshot_id, seller_estimates,
  library[{persona_id, card_ref, levels{…}, evidence{n, effect_vs_p0, ci90, source}}],
  scoreboard[{dimension, level, n, effect_vs_p0, ci90, p_best, source}],
  voice_options[{language, voice_id, gender, playable_now: bool, route: code_tool|version}],
  free_text_index[{span_id, kind, call_date}], missing_fields[], guardrail_ref, versions{…}}
```

### 6.3 B5b Agent composer

**WHY.** D2 (a spec with a reason per choice) and fit (25). Free-text history ("my son handles this now", repeated price objections) is the input most likely to change the right persona and only an LLM reads it (BCG NBA 2026; Netflix LLM ranker; DOCUMENTED). Etsy runs one LLM call per buyer in a nightly batch (DOCUMENTED).

**HOW.** A frontier-model agent (Claude Code-style agent with a persona-composition **skill**: rubric, dimension list, citation format, guardrail summary) running in a **Daytona sandbox**, reaching the model via **OpenRouter or the internal LiteLLM gateway**. **Sarvam-105b is the fallback model.** The model id is logged per run. Runs only for sellers due a call tomorrow.

Read-only tools: `get_seller_context`, `get_free_text(span_ids)`, `get_seller_memory`, `get_scoreboard(seller_type, dimension?)`, `get_persona_library`, `get_voice_options`, `get_similar_sellers(k)` (counts only), terminal `submit_spec`.

The agent (1) reads the evidence; (2) composes every dimension of §5.1, starting from any library persona(s) or none; (3) cites evidence and gives a confidence per setting; (4) writes the plan in native script, personalising only from fields that exist; (5) when its spec departs from every library persona, writes why none fits (`suggestion_reason`). Flat JSON is mandatory (nested strict schema looped 4/6; flat never failed, PROVEN). Self-confidence is logged, never a gate (DOCUMENTED).

**Blockers (open, owner M):**
- Daytona egress **35.234.211.110 is not on the OpenRouter allowlist (403)** (PROVEN, spike log 2026-10-07). Fix: allowlist request, or run the decider from the VPN laptop.
- **LiteLLM reachability from Daytona is untested.**
- **Seller data leaving premises** to a frontier model needs a ruling. Until then the decider sees **synthetic or masked data only**.
- **Native-script plan quality** of the frontier model is unchecked (Devanagari opening, objection lines). Check on the experiment batch; Sarvam-105b fallback if worse.

**WHAT (per run).**
```
agent_output = {decision_id, run_no, model_id, route: openrouter|litellm|sarvam_fallback, skill_version, prompt_version,
  spec{ <dimension>: {value, citations[{kind: field|span|scoreboard|library, ref, quoted_value}],
                      confidence: 0..1, origin: {library_ids[] | "new"}} for each dimension in §5.1 },
  plan{opening_native, steps[], personalisation[{field, line}], objection_order[], escalation[]},
  branches{on_rush: promoted|dormant, …}, sensitivity{rush, confusion, frustration, interest},
  suggestion_reason?, self_confidence, tool_calls[]}
```

### 6.4 B5c Guard, settle, explore (code)

**WHY.** Learning needs an exact logged probability; an agent's composition has none (LLM exploration fails without algorithmic support; wrong probabilities gave up to 3.0× error in Decision Service; DOCUMENTED). Guardrails and citations are checkable; confidence is not.

**HOW.**
1. **Guard each run.** Schema. Citation validator: every cited field, span or cell exists and the quoted value matches on re-read. FAQ Q5: no digits, price words, product claims or internal labels in spoken text; greet-and-confirm-owner first; human-on-request kept; fixed fact/compliance layer untouched. FAQ Q6: per-setting confidence ≤ data completeness; personalisation only from present fields. DNC and gates re-checked. One repair call, then the run fails. **No other limits on the composition.**
2. **Agree.** Audible bundle = {voice gender, style voice, pace band, pitch band, start language}; key plan choices = {opening move, first objection handled, promoted branches}. Accept when ≥ 2 of the passing runs match on the whole audible bundle and on ≥ 2 of 3 key plan choices. Then **settle** every other dimension: categorical by majority, ordinal (tone 1–5, sensitivity) by median; plan text from the run closest to the settled spec (medoid). If no ≥ 2/3 majority on any audible dimension → fallback.
3. **Make it playable.** With Code Tools: speaker, pace, pitch and opening are set per call (gap ≈ 0). Without (demo): map the settled audible bundle to the **nearest published version/voice** (same start language first, then gender, style voice, pace band, pitch band). Log `requested`, `played` and the mapping distance. This is a platform gap, not a design limit.
4. **Explore (code, logged).** Holdout: share h (e.g. 10%) gets P0 whole; p = h. Otherwise, with probability ε (e.g. 10%) code perturbs **exactly one** explorable dimension, picked uniformly from the D dimensions that are playable now, to one of its K_d − 1 alternative levels uniformly. Logged per dimension: `agent_value`, `played_value`, `explored: bool`, and propensity **P(agent value) = (1 − h)(1 − ε/D)**, **P(a given alternative) = (1 − h)·ε / (D·(K_d − 1))**; whole-spec propensity = (1 − h)(1 − ε) unperturbed, (1 − h)·ε/(D(K_d − 1)) perturbed. Propensities are conditional on the settled composition (treated as context). Seed logged. Off for judged demo sellers, logged as such.
5. **Fall back.** On no agreement or all runs failing: code-only spec = library persona with the highest scoreboard draw for this seller type (Thompson, exact p) + card default plan + field personalisation; `path: fallback`.
6. **Suggest.** Compute the distance from the settled spec to every library persona in persona-dimension space (ordinal levels scaled 0–1, categorical mismatch = 1, audible dimensions weighted ×2; ASSUMED). If the minimum exceeds a threshold (e.g. 0.35, or ≥ 2 audible dimensions differ; ASSUMED), write a `suggestion_row` with the full spec and the agent's reasons. The seller still gets the composed spec.

**WHAT.**
```
persona_decision = {decision_id, seller_key, snapshot_id, path: agent|fallback|dial_fallback,
  versions{library, scoreboard, estimator, skill, prompt, validators, git_sha}, model_ids[3],
  runs[agent_output_ref ×3], validator_results[], agreement{audible_match, plan_match, n_agree},
  spec{<dimension>: {agent_value, played_value, explored, propensity, citations[], confidence, origin}},
  spec_propensity, arm: agent|explored|holdout, seed,
  voice{requested{voice_id, gender, pace, pitch}, played{agent_version|code_tool, voice_id}, map_distance},
  plan{…}, branches{…}, sensitivity{…}, nearest_library{persona_id, distance}, missing_fields[]}
suggestion_row = {decision_id, seller_key, spec{…}, nearest_library{persona_id, distance}, distance_by_dimension{},
  suggestion_reason[3 runs], seller_type, distance_pct, model_id, later: outcome_ref}
```
**FEEDS** B6; B12; `suggestion_row` → B11 weekly job.

### 6.5 Suggestions → new library personas (weekly, human-approved)

**WHY.** A composed persona far from the library may reveal a missing VANI persona. Single suggestions are noisy; LLM "none fits" answers fail in both directions (30–50% drop, abstention inflation; DOCUMENTED). Every production category-expansion system aggregates first (TnT-LLM, Clio; DOCUMENTED). **HOW.** Embed specs + reasons; cluster within audible-bundle groups; LLM names each cluster and drafts a card. Code gates (ASSUMED config): support ≥ max(500, 0.5% of active) distinct sellers; stable across 2 windows (ARI/Jaccard ≥ 0.7; PS07 buffer reached 0.54 Aug→Sep, PROVEN); outcome evidence when available (explored/holdout calls near the cluster beat the nearest library persona); audible difference from the nearest persona; freeze if a model/skill change moves the suggestion rate by > 2 pp. A human approves with a rubric card; N auditions the voice. Approved → library persona; **if audible, a new Sarvam agent version** (until Code Tools). Rejections go to a "known non-gap" register.

### 6.6 Volume and cost (ASSUMED; open decision D-1)

Frontier-model cost per run is **not measured**; with tool loops it is likely well above Sarvam-105b's ≈ ₹0.16 / 4.2 s per structured call (PROVEN). At an assumed 40K due sellers × 3 runs, cost and rate limits matter. Reductions: reuse a decision when snapshot, memory, library and scoreboard versions are unchanged (plus 1–2% audit re-runs); gate the agent to sellers with decision-changing free text or low code confidence. **D-1 (team lead): agent on all due sellers vs gated.** It depends on §9.2.

### 6.7 B6 Cook-ahead, re-cook, dial-time check (unchanged)

40.5% of sellers have ≥ 2 calls and hold 71.3% of calls; median gap ≈ 1 day (PROVEN). Nightly cook; event re-cook after each outcome or memory update; dial-time staleness (event after watermark, version change, age > 72 h, unpublished version) → fast code-only path (no LLM, p95 < 1 s, ASSUMED). DNC → no call. Each call logs `spec_freshness`.

---

## 7. Live call: B7 and B8

### 7.1 What the Sarvam agent gets

| Sarvam input | Preferred (Code Tools on-start) | Demo now | Evidence |
|---|---|---|---|
| Voice, pace, pitch | `speaker_id`, `speech_settings` per call | published version matching the agent's recommended bundle; voice via `initial_language_name` | SDK context DOCUMENTED; per-language route PROVEN; SDK override ignored PROVEN |
| Start language | `initial_language_name` | same | PROVEN |
| Opening | `initial_bot_message` (native script) | same | spoken verbatim PROVEN |
| Variables | `set_agent_variable` | `agent_variables{decision_id, persona_directive, seller_mode}` | PROVEN; `decision_id` echo untested |
| Per turn | `{seller_mode, persona_directive = <plan> \| Right now: <mode>}` | same | plan re-send 20/20 vs 23/28 PROVEN |

**Demo versions.** Run the composer on the 2–3 demo sellers first; S builds Sarvam versions matching their settled audible bundles, plus P0. The fixed base prompt holds pitch goal, product facts, prices and compliance; nothing the agent writes can change them (FAQ Q5; 0/8 price-demand turns quoted an amount with plan re-send, PROVEN). `call_config = {decision_id, plan_prefix, base_mode, branches, sensitivity, priority, max_switches: 2, versions}`.

### 7.2 B8 Signal / switch server (unchanged)

Seller utterance arrives by tool call (Devanagari ASR; 6–7 calls per 4 turns, idempotent, PROVEN) → lexicon now (< 5 ms) → Jev next turn (~480 ms p50, 49/51 romanised, PROVEN; Devanagari untested; sync LLM ~2.6 s rejected) → code policy (frustration > confusion > rush > interest; hysteresis; max 2 switches; per-seller thresholds from `sensitivity`) → `persona_directive = <plan> | Right now: <mode>`. Language switch is Sarvam built-in (6/6), logged from transcript as `sarvam_builtin`. Known issues: false confusion on "phir se pooch raha hoon, price batao"; ~17% restarted replies. Switch row: `{decision_id, turn, signal, source, confidence, threshold_used, change, reason, plan_step, switch_no, versions}`.

---

## 8. Between runs: B9 and the two loops

No model is trained. Only tables, lexicon, thresholds, memory and library change.

**B9.** Offline LLM (masked) labels signal onsets, switch verdicts and per-dimension fit; two-key labels (lexicon vs PS07 evaluator κ ≈ 0.03, PROVEN); declared reward and join window.

**B10 Loop 1, switch.** Missed → new cue; false → negative cue or guard; late → earlier cues; Jev wording at most once. Gate: frozen gold set (≈ 350–400 August calls + canaries), no per-signal regression, flip list signed off.

**B11 Loop 2, persona = the agent's evidence.** Outcomes and fit labels update **seller memory** (triggers re-cook) and the **per-dimension scoreboard**; suggestion rows go to the weekly job (§6.5). These are exactly what `get_seller_memory`, `get_scoreboard` and `get_persona_library` return, so each loop turn changes what the agent sees tomorrow.

| Loop | Learns from | Changes | Gate | Feeds |
|---|---|---|---|---|
| 1 Switch | reviewer switch verdicts | lexicon, thresholds, Jev wording | frozen gold + canaries + flip list | B8 |
| 2 Persona | outcomes, per-dimension fit labels, **suggestions** | memory, per-dimension scoreboard, library | two-key labels; clustering gates + human | B2, B4, B3 → **B5b tools**, B6 |

## 9. Validation block

### 9.1 Pre-registered fair 2-day experiment

**Set.** ≈ 40 synthetic sellers from aggregate patterns, 4 groups: (a) structured-signal only; (b) free text that changes the right persona; (c) distractor free text; (d) a genuine gap (e.g. Tamil-preferring, no Tamil style voice) where a suggestion is the right output. Scoreboard prior-only, identical for all arms.

**Labels first.** Before any arm runs, two non-builders (team lead + N) write the expected audible bundle, 2–3 critical plan elements, "suggest new" where expected, and a one-line rationale; a third adjudicates; agreement reported; file hashed and committed.

**Arms.** Code-only · ungated composer · select-only (v3) · **compose + guard (v4)**. Same snapshots, 5 reps per seller per arm; frontier model and Sarvam-105b fallback both logged.

**Metrics.** Audible-bundle and plan-element accuracy per group; free-text sensitivity (b); distractor robustness (c); suggestion precision/recall (d); confident-wrong rate; consistency over 5 reps; citation validity; guardrail failures; fallback rate; distinctness (mean pairwise spec distance across sellers); cost; latency; native-script quality (N rates openings blind).

**Adoption rule.** Keep compose + guard if it beats select-only on (b) by ≥ 15 pp, is not worse than select-only or code-only by > 5 pp on (a) and (c), has confident-wrong ≤ select-only and fallback rate ≤ 30%. Otherwise run select-only framing with the same guards. Power is low (≈ 30 pp at n = 10); analyse paired (McNemar).

### 9.2 Free-text share in PS07 (placeholder)

**Status: measurement running; results will be inserted here.** It computes (i) the share of PS07 calls/sellers with a non-empty summary or objection note (upper bound) and (ii) from a masked sample, the share where the free text would change the composed persona. **D-1 depends on it:** small share → gate the agent; large share → run it on all due sellers.

| Measure | Value | Source |
|---|---|---|
| Share with any free text | *pending* | *pending* |
| Share where free text changes the persona | *pending* | *pending* |

---

## 10. B12 Data created from day one (cannot be backfilled)

| Record | Key | Must hold |
|---|---|---|
| `seller_snapshot` | snapshot_id | exact B1 output incl. span ids; missing fields |
| `decision` | decision_id (in `agent_variables`, on every switch row) | all versions; **model id per run**; all 3 runs (per-dimension values, citations, origin); validator results; agreement; **per-dimension agent vs played value, explore flag, propensity**; seed; arm; path |
| `suggestion_row` | decision_id | full spec; nearest library + distance; reasons; later outcome |
| `call` | call_id, decision_id | **voice requested vs played vs observed** (median F0, PROVEN technique); switch log; latency |
| `outcome` / `review` | decision_id | declared reward; two-key labels |
| manifest | version id | hashes: library, scoreboard, skill, prompts, validators, lexicon |

Append-only JSONL → Parquet + DuckDB in git-ignored `data/`. Backfilled PS07 rows: `propensity = null`, `causal_claim_allowed = false`.

## 11. Work split for 3 people

**Hour 0–2, all three:** contracts in `app/contracts/` (JSON Schema + example): `seller_context`, `seller_estimates`, `persona_library` (with dimension space), `scoreboard` (per dimension), **`agent_input`, `agent_output` (composed spec), `persona_decision`, `suggestion_row`**, `call_config`, `sarvam_start_payload`, `tool_turn`, `switch_log_row`, `call_record`, `review`, `outcome`. Fixtures: 6 synthetic sellers with masked spans, a 2-persona mini library, a **mock composer** returning 3 fixed outputs (two agree on audible bundle, one with a bad citation, one far from the library).

| Member | Owns | Tests alone with | Done when |
|---|---|---|---|
| **S — strong dev** (live path) | B7, **playability mapper**, demo Sarvam versions matching recommended bundles + per-language voices, Code Tools on-start tool (when enabled), B8, F0 check, call/switch records | fixture `persona_decision`; utterance lists | Live call follows the composed plan; one live switch logged; voice requested = played = observed |
| **M — second member** (decision path) | B1, B2, B4 (per dimension), **B5a, B5b composer on Daytona (skill, tools, k = 3, model routing + fallback), B5c guard/settle/explore/suggest**, B6, decision records; experiment harness; §9.2 measurement; blockers in §6.3 | fixture sellers; mock composer first, frontier model second | One command turns sample seller files into validated `persona_decision` JSON with 3 runs, citations, per-dimension p; fallback proven by bad-citation fixture; suggestion row from far fixture |
| **N — non-tech member** | B3 cards with evidence, plan moves and branches in native script, voice auditions; suggestion-review rubric; B9 gold labels; experiment labels with team lead; native-script quality rating; demo, slide, skills.md | library JSON via M's schema check | Library v1 approved; labels committed; ≥ 150 gold calls; demo recorded |

**Integration order.** (1) Contracts + fixtures. (2) Parallel: S live call from a fixture decision; M guard/settle/explore on the mock composer; N library v1 + labels. (3) M swaps in the frontier model (allowlist or VPN laptop; synthetic data); experiment tonight. (4) Composer runs on demo sellers → S builds matching versions → real decisions drive live calls. (5) Adopt per §9.1. (6) Switch log + 2–3 contrasting demo sellers in 2 languages. (7) Loops as recorded artefacts: one reviewed call, one gated lexicon diff (one rejected), one per-dimension scoreboard update, one suggestion clustering run (expected to propose nothing on real-pattern data). **Cut order if late:** weekly clustering, Jev wording, k = 3 (→ k = 1 + guards, labelled), frontier model (→ Sarvam-105b fallback). Code-only path alone still meets D1/D2.

## 12. How PS04 is met

| PS04 item | Met by | Shown as |
|---|---|---|
| D1 generator on sample files | B1 → B2 → B5a/b/c (→ B6) | `persona_decision` per seller |
| D2 spec with reasons | per-dimension values with cited, re-checked evidence | spec + "why" panel |
| D3 live demo, ≥ 1 switch | B7 + B8 | recording + agent id |
| D4 switch log | B8 rows incl. `sarvam_builtin` | table |
| D5 one slide | sample composed spec + evidence + diagram | slide |
| Fit 25 | traits/states, memory (AUC 0.71 vs 0.58, PROVEN), agent reading free text | per-seller reasons |
| Switches 25 | lexicon now, Jev next turn, per-seller thresholds | live switch + log |
| Distinctness 20 | composed per-seller specs; distance metric reported; library grows only on evidence | A/B audio + distance table |
| Voice 2+ languages 15 | per-language voices, native script, built-in switch | demo |
| Evidence 15 | PS07-backed seller side; per-dimension logged p; pre-registered experiment | evidence table |

## 13. Devil's advocate

1. **Composing increases variance.** More free dimensions → runs disagree more → more fallbacks. Defence: agreement is required only on the audible bundle + key plan choices; the rest is settled by majority/median. Report fallback rate; > 30% means an unclear skill rubric.
2. **Validator load grows.** Every dimension carries citations; more citations to re-read, more chances to fail. Defence: citation checks are cheap code; one repair call; flat schema.
3. **Composed personas are harder to learn from.** Whole bundles rarely repeat, so per-bundle evidence never accrues. Mitigation: the per-dimension scoreboard (Aampe decomposition, DOCUMENTED) and one-dimension exploration, so each explored call teaches about exactly one dimension. Cost: interactions between dimensions are assumed small (ASSUMED; known simplification).
4. **Distinctness should improve, but may not.** Composition can spread personas apart; it can also collapse every seller to the same "safe" mix. Measure mean pairwise spec distance in §9.1; collapse is a skill problem.
5. **Agreement ≠ correctness.** 28% of cases were confidently wrong across all runners tested (DOCUMENTED). Defence: citations, pre-registered labels, holdout.
6. **Propensity is conditional.** Logged p covers code's perturbation and holdout, not the agent's own randomness. Causal claims come only from explored-vs-unexplored and holdout contrasts.
7. **Playability gap hides the design.** Until Code Tools, a few versions play many requested bundles. The requested-vs-played log keeps the gap visible; claims are about played bundles.
8. **Suggestions on PS07 data will likely be empty.** p95 misfits were coverage artefacts with normal outcomes (PROVEN). "Propose nothing" is the guard working. Single suggestions and LLM "none fits" are unreliable (DOCUMENTED), hence aggregation + human.
9. **Frontier model vs "core agent must be Sarvam" (AGENTS.md).** Team decision 5 reads "core agent" as the voice agent. Confirm with organisers; Sarvam-105b fallback keeps a Sarvam-only path.
10. **Data off premises.** The frontier model, reviewer and Jev see seller text. Synthetic/masked data until a ruling (§6.3).
11. **Cost unmeasured.** Frontier-model runs × 3 at scale may cost far more than Sarvam-105b. D-1 waits on §9.2 and measured cost.
12. **Scoreboard is empty today.** Claim fit, distinctness and live switching, not lift, until ≈ 2,000 calls per arm per segment.
13. **FAQ Q1 fixed library.** Output is a per-seller composed spec; the library is starting points. Lead the demo with that.
14. **Thresholds are invented.** Distance weights and threshold, ε, h, 500 sellers, ARI 0.7, 2 pp, 15 pp, 30% are config, not findings.

## 14. Open questions

| # | Question | Who | Decides |
|---|---|---|---|
| D-1 | Run the agent on all due sellers, or gated? | Team lead (after §9.2 + cost) | Cost; fallback share |
| 2 | Compose + guard vs select-only framing | §9.1 rule | Skill framing |
| 3 | OpenRouter allowlist for 35.234.211.110, or decider on VPN laptop? | Key owner / M | Decider host |
| 4 | Is LiteLLM reachable from Daytona? | Test (M) | Model route |
| 5 | Can seller data go to a frontier model, reviewer and Jev? | Organisers | Real vs synthetic data |
| 6 | Does "core agent must be Sarvam" allow a frontier-model decider? | Organisers | Decider model |
| 7 | When will Sarvam enable Code Tools? | Sarvam (emailed 2026-10-09) | Playability gap; version count |
| 8 | Frontier-model native-script plan quality vs Sarvam-105b | §9.1 (N rates) | Fallback order |
| 9 | Distance weights and suggestion threshold | Team lead after §9.1 | Suggestion volume |
| 10 | Daily due-seller count (40K ASSUMED) and model rate limits | Business / providers | Batch window, k |
| 11 | Does Sarvam echo `decision_id` per tool payload? Agent-UI pitch audible on v4? | Test | Join key; pitch |
| 12 | May we explore and hold out on real sellers? Reward and window? | Business | Scoreboard learning |

## 15. Evidence index

| Claim | Tag | Source |
|---|---|---|
| Team decisions (compose, suggest, frontier decider, voice route, voice gender) | DOCUMENTED | `raw/hackathon/2026-10-09-team-decisions-persona-agent.md` |
| Trait/state recurrence; NI τ ≈ 28 d | PROVEN (fits ASSUMED) | `outputs/reports/VANI persona translation and library.md`; `outputs/reports/Between run learning loops.md` |
| K=7 ARI 0.868; 11.2% far; buffer ARI 0.54; misfits = coverage | PROVEN | `outputs/research_notes/Data derived persona library/ps07_library_prototype.md` |
| Memory AUC 0.71 vs 0.58; median gap 1.02 d; 40.5% / 71.3% | PROVEN | `outputs/reports/Between run learning loops.md` |
| Plan re-send, language switch, 0/8 price, restarts | PROVEN | `raw/research/2026-10-08-plan-stress-spike.md`, `…plan-following-spike.md` |
| SDK override ignored; per-language voices; pace/pitch v3/v4 | PROVEN | `raw/research/2026-10-08-voice-override-spike.md`, `2026-10-09-sarvam-voice-recheck.md`, `2026-10-09-per-language-voice-spike.md` |
| Code Tools on-start fields; not enabled for us | DOCUMENTED / PROVEN | `raw/research/2026-10-08-sarvam-on-start-options-check.md` |
| OpenRouter 403 from Daytona 35.234.211.110 | PROVEN | `raw/research/2026-10-07-spike-log.md` |
| Per-dimension learning (Aampe); logged randomisation | DOCUMENTED / ASSUMED | `outputs/research_notes/Data driven persona agent/industry_architectures.md` |
| Jev 49/51 ~480 ms; Sarvam-105b ₹0.16 / 4.2 s; flat schema | PROVEN | `outputs/reports/Persona generator architecture.md`; `outputs/research_notes/Agent decides VANI persona/agent_as_decider.md` |
| Guards around agents; 3-run agreement; confidence inflation; NOTA; LLM exploration; propensity error | DOCUMENTED | `outputs/reports/Agent decides VANI persona.md` |
| Suggestion clustering (TnT-LLM, Clio) | DOCUMENTED | `outputs/research_notes/Agent decides VANI persona/new_persona_signals.md` |
| Etsy nightly per-buyer LLM | DOCUMENTED | `raw/research/2026-10-09-last30days-agents-refine-personas-segments.md` |
| Dimension levels, distance metric, ε/h, costs, all thresholds | ASSUMED | this plan |
