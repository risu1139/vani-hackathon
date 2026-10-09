# VANI Persona Design (PS04): high-level architecture plan v2

As of 2026-10-09 (hackathon day 1). For the team lead first, then an external reviewer. Method: top-down blocks, each with WHY / HOW (one layer beneath) / WHAT (input → output) / FEEDS (`.claude/skills/design-architecture/SKILL.md`). Architecture level only. Supersedes [v1](VANI%20persona%20architecture%20plan%20v1.md).

**Evidence tags.** **PROVEN** = measured by us (spike or PS07 aggregate). **DOCUMENTED** = official doc, the PS04 brief, a paper, or a `raw/` source. **ASSUMED** = our design choice or arithmetic, not yet tested.

## 0. Summary in simple words

1. VANI is the bot that calls sellers. This plan gives VANI a persona for each seller.
2. A VANI persona is VANI's voice, speed, pitch, language, tone and call plan.
3. Seller data is the input. It is not the persona.
4. We describe each seller with traits and states. A trait changes slowly. A state changes from call to call.
5. We keep a small library of VANI personas. Each persona is one Sarvam agent version.
6. Each night, a program and an AI agent select a persona for each seller who gets a call the next day. The agent also writes the call plan for that seller.
7. Code checks every result. Code can stop a wrong result. Code records every decision.
8. During the call, our signal server watches what the seller says. It changes VANI's mode when the seller is rushed, confused, frustrated or interested.
9. Sarvam changes the language itself when the seller changes language.
10. After each call, two learning loops update our tables. One loop improves the switches. One loop improves the personas.
11. No model is trained. Nothing learns during a call.
12. Each team member can build one part alone, because each part has a fixed input and output.

---

## 1. Changes from v1

| # | v1 said | v2 says | Why |
|---|---|---|---|
| 1 | "Persona library" = 7 seller clusters (k-means); persona = seller type | **Persona = VANI's persona.** The 7 PS07 clusters are **seller types**: input and explanation only (FAQ Q1) | Team-lead correction; PS04 §2 "build the VANI persona" (DOCUMENTED) |
| 2 | Seller history as one feature vector | Seller described as **traits** (stable leans) and **states** (decaying), each with its own estimator | Rush recurs only 30.8% vs 20.8%; confusion fades within days; NI decays with τ ≈ 28 d (PROVEN) |
| 3 | Precedence stack + tiered rule table decides settings | **No rule table component.** Rules only seed early priors. Decision = trait/state estimates + seller-type × VANI-persona **scoreboard** + nightly **agent** | Rule table cannot learn which VANI persona works; the earlier 23/23 vs 16/23 test had circular labels and no free text, so it is not evidence against an agent |
| 4 | "No LLM per seller" | **Agent Task A** nightly, only for sellers due a call; code validators + logged fallback | Etsy runs one LLM call per buyer for 90M buyers in nightly batch (DOCUMENTED); free-text call summaries need an LLM to read |
| 5 | Misfit buffer → promotion | **Agent Task B** weekly proposes new / merged / split / retired VANI personas; code checks; human approves | TnT-LLM pattern: LLM proposes categories, cheap code assigns (DOCUMENTED) |
| 6 | Per-call voice blocked | Per-call voice **works via Per-language voices + `initial_language_name`** (one voice per language per version); pace and pitch work on Bulbul v3/v4 via TTS API | Spikes 2026-10-09 (PROVEN) |
| 7 | Library = 6 archetypes asserted | Starting count **derived** (§5.3): 1 control + 4 archetypes, method shown | Binding correction |
| 8 | Voice gender GUESS, balanced rotation, 80% skew alarm | Voice gender is a **data-driven persona dimension**: the scoreboard sends more calls to the gender that works; no quotas, no alarms; seller gender/age never inferred | Binding correction |
| 9 | One switch threshold for all | **Three translation layers**: robust pre-call default, contingency branches re-sent every turn, per-seller live thresholds | Self-fulfilling risk is handled live |
| 10 | One learning updater | **Two named loops** (switch, persona) shown on the diagram | Binding correction |
| 11 | — | **Contracts + work split** for 3 people | Parallel build in 2 days |

---

## 2. End-to-end diagram

```
 SELLER DATA (input)                          B3 VANI PERSONA LIBRARY (versioned)
 profile · call log · evaluator outputs ·     P0 control + P1..P4 archetypes = dimension levels
 free-text call summaries · seller memory     + plan moves & contingency branches (native script)
        │                                     + voice bundle per language → 1 Sarvam agent version
        ▼                                                  │
 B1 Seller context (script, as-of) ─► B2 Trait/state estimator + seller type
                                               │
 ┌─ NIGHTLY COOK (sellers due tomorrow) + EVENT RE-COOK (after every call) ───────────────────┐
 │ B5 Persona decision:                                                                       │
 │   code candidates (B2 + B4 scoreboard + B3) ─► AGENT TASK A (read-only tools; refines      │
 │   persona + call plan + reasons) ─► code validators · gates · logged arm draw ─► decision  │
 │ B6 Spec store ─► dial time: stale? ──yes──► fast code-only path (no LLM)                   │
 └────────────────────────────┬───────────────────────────────────────────────────────────────┘
                              ▼ no
 B7 Compile ─► Sarvam call start: agent version · initial_language_name (selects voice) ·
               initial_bot_message (native script) · agent_variables{decision_id, persona_directive, seller_mode}
 LIVE:  seller ◄─voice─► Sarvam agent ──tool call each seller turn (Devanagari)──► B8 SIGNAL SERVER
                            ▲          lexicon now (<5 ms) · Jev next turn (~480 ms) · code policy
                            └── {seller_mode, persona_directive = <plan> | Right now: <mode>} ◄┘
                                language switch: Sarvam built-in; logged from transcript ─► switch log
 POST-CALL: trace + outcome ─► B9 reviewer + outcome join
     ├─ LOOP 1 (switch) ─► B10 lexicon cues · per-signal thresholds · Jev wording
     │                       ── gate on frozen gold set ──► B8 (next call)
     └─ LOOP 2 (persona) ─► B11 seller memory ─► B2 · scoreboard ─► B4 · re-cook ─► B6
                              └─ weekly AGENT TASK B: propose new/merge/split/retire
                                 ── code checks ── human approval ──► B3
 B12 DATA LAYER (append-only, on premises): snapshot · decision · call · switch log ·
     voice requested vs observed · outcome · review · versions manifest
```

## 3. Block table

| Block | Why (PS04) | How (choice; rejected) | Input → Output | Feeds | Status |
|---|---|---|---|---|---|
| B1 Seller context | D1 "seller file in"; FAQ Q6 | Script, as-of rebuild from call rows; *rej.* seller-file history columns (leak future), LLM summariser | seller rows, as_of → `seller_context` | B2, B5 tools | Leakage-free build PROVEN |
| B2 Trait/state estimator + seller type | Fit 25 | Beta posteriors for traits, exp(−gap/28 d) for states, nearest of 7 seller types + no-fit flag; *rej.* treating a history label as identity | `seller_context` → `seller_estimates` | B5, B4 keys | Recurrence + K=7 PROVEN; estimator ASSUMED |
| B3 VANI persona library | Distinctness 20; voice 15 | Designer-led archetypes on shared dimensions over a fixed fact layer; refined by data; *rej.* fixed 6, factorial of 486 cells | cards, auditions → `persona_library_vN` + published versions | B5, B7, B11 | Shape DOCUMENTED (Alexa+); levels ASSUMED |
| B4 Scoreboard | Evidence 15; fit 25 | Beta counts per seller type × VANI persona (× voice gender), weak priors (10–25 pseudo-calls); *rej.* rule table, PS07 outcome mining for style (one style) | decisions ⨝ outcomes → `scoreboard_vN` | B5, B11 Task B | ASSUMED; empty of real data today |
| B5 Persona decision | D2 spec + reasons; fit, distinctness | Code candidates → Agent Task A → code gates + logged draw; code-only fallback; *rej.* rules only, agent unchecked | estimates + library + scoreboard + free text → `persona_decision` | B6, B12 | ASSUMED |
| B6 Cook scheduler + spec store | Fresh spec at dial | Nightly for due sellers; event re-cook after each call; dial-time staleness check | dial list, events → ready spec | B7 | ASSUMED |
| B7 Compile + Sarvam agent | D3 demo; voice 15 | Version per persona; voice by `initial_language_name`; native-script opening; *rej.* per-call `text_to_speech_config` (ignored) | spec → Sarvam start payload + `call_config` | Sarvam, B8 | Voice route PROVEN |
| B8 Signal / switch server | Switches 25; D4 log | Lexicon now + Jev next turn + code policy + per-seller thresholds; plan re-sent each turn; *rej.* synchronous LLM | utterance + `call_config` → tool response + switch-log row | Sarvam, B12, B9 | Components PROVEN |
| B9 Reviewer + outcome join | Evidence; both loops | Offline LLM on internal gateway/Sarvam, masked; two-key labels; declared reward | trace + later events → `review`, `outcome` | B10, B11 | ASSUMED |
| B10 Loop 1: switch updater | Switches 25 | Edit cues, thresholds, Jev wording; gate on frozen gold | reviews → `switcher_vN+1` | B8 | ASSUMED |
| B11 Loop 2: persona updater + Task B | Fit, evidence, distinctness | Memory + scoreboard update; weekly agent proposals; code checks; human | outcomes + reviews → memory, `scoreboard_vN+1`, library proposals | B2, B4, B6, B3 | ASSUMED |
| B12 Data layer | Evidence; all learning | Append-only JSONL → Parquet + DuckDB, on premises | all writes → views | all | ASSUMED |

---

## 4. Seller side: B1 and B2

### B1 Seller context builder (script)

**WHY.** PS04 deliverable 1 is "a seller file in, a persona out". FAQ Q6 requires missing fields to be flagged (DOCUMENTED).

**HOW.** A deterministic script. It makes no decision. It counts only events before `as_of`. Seller-file history columns cover all of Apr–Sep and leak the future, so history is rebuilt from call rows (PROVEN, PS07 prototype). It also attaches **masked free-text call summaries and objection notes** for the agent (names and 10-digit numbers removed).

**WHAT.** `{seller_key, as_of}` → `seller_context = {snapshot_id, as_of, source_watermark, profile{zone, state, turnover_band, business_type, top_category}, engagement{}, history{n_prior_calls, last_outcome, gap_days, outcome_shares, short_call_share}, objections{family: share}, signals{rush, terse, confusion, frustration, english_heavy, bot_question, interest: {k, n}}, observed_language, summaries_ref[], flags{dnc}, missing_fields[], completeness}`. **FEEDS** B2; B5 tools; B12 as an immutable snapshot.

### B2 Trait / state estimator + seller type

**WHY.** Fit (25). The key fact: **seller history sets odds, not identity.** Rush recurs in 30.8% of next calls against a 20.8% base (n = 276), so about 7 in 10 prior rushers arrive calm. Terse (41.0% vs 17.8%) and English-heavy (13.8% vs 4.3%) also behave as weak traits. Confusion is a short state (34.3% vs 7.7% within 3 days, 14.3% vs 5.5% at 4–30 days). Not-interested decays to base with τ ≈ 28 days (PROVEN counts; fit ASSUMED). Pre-call data predicts in-call signals only at AUC 0.52–0.58, except English-heavy at 0.68 from profile (PROVEN).

**HOW.**
- **Traits** (rush, terse, English-heavy, bot-question): per-seller Beta posterior shrunk to the seller-type rate, `p = (k + α·m_type)/(n + α)`, α ≈ 4–10 (ASSUMED).
- **States** (confusion, last outcome, callback request, frustration): weight `exp(−gap/28 d)`; drop to default after 45–60 days (ASSUMED, sized from PROVEN decay).
- **Seller type**: nearest of the 7 PS07 warm types (K=7, bootstrap ARI 0.868; PROVEN) as an explanation and scoreboard key. **Cold sellers** (46–70% of anchors; no stable structure, ARI ≤ 0.44, PROVEN) get type `cold`. A seller beyond the p95 distance gets `no_fit` (11.2% of held-out warm sellers, PROVEN).
- Rules appear here only as **seed priors** (e.g. α, the 28-day constant). They are not a decision table.

**WHAT.** `seller_context` → `seller_estimates = {snapshot_id, seller_type{id, distance, fit: ok|ambiguous|no_fit|cold}, traits{name: {mean, n, ci}}, states{name: {value, gap_days, weight}}, language{start_guess, english_lean, source}, confidence}`. **FEEDS** B5; B4 (segment key).

---

## 5. VANI side: B3 library and B4 scoreboard

### 5.1 B3 VANI persona library

**WHY.** Distinctness (20) and natural voice (15). Sarvam fixes voice, pace and pitch per call (DOCUMENTED; PROVEN that per-call SDK override is ignored, re-checked 2026-10-09). Audible choices are therefore few and must be well chosen.

**HOW.** A **library of VANI personas**. Each persona is a bundle of levels on shared dimensions over one fixed fact and compliance layer. Alexa+ ships named styles defined this way in 2026 (DOCUMENTED). Designers build it first; data refines it (B4, B11).
- **Dimensions:** voice per language (gender, timbre), pace, pitch, default language mix, formality, warmth, brevity, directness, plan style.
- **Fixed per version** (audible): voice per language, pace, pitch. Set in the Sarvam agent UI (pace 0.9–1.4, pitch ±0.2; DOCUMENTED). The agent-level pitch slider is untested; pitch via the TTS API works on v3/v4 despite the docs (PROVEN: v4 aditya_hi_sales 104 / 150 / 162 Hz at pitch −0.5 / 0 / +0.5).
- **Per call** (variables): formality, warmth, brevity, plan.
- **Voice per language:** Sarvam "Per-language voices" maps one voice to each starting language in a version. `initial_language_name` then selects it per call (PROVEN 2026-10-09: Hindi → female, 286 Hz; English → male, 140 Hz). Limit: one voice per language per version.
- **Voices:** 222 Bulbul v4 persona voices named `name_lang_style` (DOCUMENTED). The non-tech member auditions them against each card's adjectives. The audition records F0 and words per second.
- **Plan content** per persona: openings, steps, objection moves and contingency branches (`on_rush`, `on_confusion`, `on_language`, `on_busy`, `on_frustration`), all in **native script**. Sarvam docs say romanised Indic input degrades TTS (DOCUMENTED).

**WHAT.** `persona_library_vN = {version, personas[{persona_id, name, adjectives[], levels{pace, pitch, formality, warmth, brevity, directness, plan_style}, voices{lang: {voice_id, gender, f0_hz, wps}}, sarvam_agent_version, plan_moves{opening[], steps[], objection[], branches{on_rush…}}, status: active|candidate|retired, parent_ids[]}], fact_layer_hash}`. **FEEDS** B5, B7, B11.

### 5.2 Starting archetypes (designer hypotheses, every mapping ASSUMED)

| Id | Archetype | Audible bundle | Per-call levels | First hypothesised for (seller types / traits) |
|---|---|---|---|---|
| P0 | Current VANI default | today's voice and pace | today's | Control/holdout; cold fallback |
| P1 | Crisp closer | brisk (≈1.05–1.1), lower pitch | brevity high, directness high, time-boxed opening | Rush, terse, call-me-later, mid-pitch dropper |
| P2 | Patient guide | moderate (1.0; never slower on a confusion prior), warm voice | one idea per turn, yes/no checks, low formality | Confusion state, thin history, bot-question |
| P3 | Respectful advisor | moderate, measured voice | formality high, evidence-led | Meeting-fixed revisit, talked-no-outcome, large business |
| P4 | Warm re-engager | moderate, expressive voice | warmth high, one new value point, easy exit | Short-call refuser, recent not-interested |

Language is **not** a persona. English-heavy and regional sellers get the same archetypes; `initial_language_name` picks that persona's voice for the language.

### 5.3 How we chose the starting count (ASSUMED method)

1. **Only audible bundles need a version.** Formality, warmth, brevity and plan travel per call. A new version is justified only by a different voice / pace / pitch bundle.
2. **Bundles the seller side asks for.** The trait/state evidence points to four delivery directions: shorter-and-earlier-ask (rush, terse, call-later), simpler-and-chunked (confusion, thin history), formal-and-evidence-led (meeting revisit, larger business), warm-acknowledge-and-exit (recent NI, refusers). Plus P0 as control. **= 5.** Language bundles collapse into per-language voice maps (PROVEN route), which removes the separate English and Tamil archetypes of the earlier draft.
3. **Learning cost.** A 3-point meeting lift (≈13% → 16%) needs ≈ 2,000 calls per arm per segment (ASSUMED arithmetic, α 0.05, power 0.8). With 8 segments (7 types + cold) and 3 plausible personas each: 8 × 3 × 2,000 ≈ 48,000 explored calls. PS07 averages ≈ 1,500 answered calls a day (269,455 over Apr–Sep). So 5 personas give a first read in roughly a month; every extra persona adds ≈ 2,000 × (segments it is tried in) calls.
4. **Voices per language.** Each version needs one voice per supported language. Thin languages limit distinctness to pace, pitch and wording. A gender twin of a persona doubles its version count, so twins are added only where traffic can fill them.

**Start: 5 versions.** Grow only through Task B with scoreboard support.

### 5.4 B4 Scoreboard

**WHY.** Evidence (15) and fit (25). PS07 had **one VANI style**, so it contains no style → outcome evidence (DOCUMENTED). The scoreboard is where that evidence will be created.

**HOW.** Beta counts per (seller type × VANI persona × voice gender where a twin exists), under a reward declared in advance (proposal: meeting fixed in call, or positive next call within 14 days, and no DNC; fixed join window; default 0). Each designer hypothesis enters as a weak prior worth 10–25 pseudo-calls (Pega StartingEvidence = 25, DOCUMENTED). Forgetting λ ≈ 0.8 per month (ASSUMED; NI level drifted 75.8% → 63.4%, PROVEN). Only explored and holdout traffic may support a "works better" claim. **Voice gender:** if a gender wins in a segment, the draw sends it more traffic. There are no quotas or alarms. Seller gender and age are never inputs and never inferred.

**WHAT.** `scoreboard_vN = {reward_def_id, cells[{seller_type, persona_id, voice_gender?, alpha, beta, n_eff, p_best, source: prior|explored|holdout}]}`. **FEEDS** B5 (candidates, probabilities), B11 Task B.

---

## 6. B5 Persona decision (nightly) and B6 cook

### 6.1 Three translation layers

| Layer | When set | What it carries | Example (prior rusher) |
|---|---|---|---|
| (a) Pre-call settings | Before dial; fixed for the call | Persona version (voice, pace, pitch), start language, robust default levels | P1 or a moderate persona; pace never slowed for confusion |
| (b) Plan contingency branches | Before dial; **re-sent every turn** | `on_rush`, `on_confusion`, `on_language`, `on_busy`; high prior **promotes** a branch into the opening, low prior keeps it dormant | Time-box in line 1; `on_rush` = one-line value + slot |
| (c) Live-switch sensitivity | Before dial; used by B8 | Per-signal threshold lowered when the prior is high | 1 rush cue switches instead of 2 |

Layer (c) handles the self-fulfilling risk: VANI starts safe and moves only when the seller confirms the state in this call. Live evidence always wins over the prior. One prior call may move at most two settings off default (ASSUMED).

### 6.2 HOW: code candidates → Agent Task A → code gates

1. **Code candidates.** From B2 and B4: eligible personas (DNC removed; version published; voice exists for the start language), each with a scoreboard probability (Thompson). This alone is the **code-only path**.
2. **Agent Task A** (only for sellers due a call tomorrow). An LLM agent on Sarvam or the internal LiteLLM gateway, with **read-only tools**:

| Tool | Returns |
|---|---|
| `get_seller_context` | snapshot + missing fields |
| `get_call_summaries` | masked free-text summaries and objections (last N calls) |
| `get_seller_memory` | traits, states, language preference, past persona and fit labels |
| `get_scoreboard` | cells for this seller type: n, rate, interval, p_best |
| `get_persona_library` | cards, levels, plan moves, branches |
| `get_voice_options` | versions × languages × voice gender |
| `propose_decision` (terminal) | the output below |

   The agent ranks personas with reasons, writes this seller's plan (opening in native script, personalisation facts that exist in the file, objection order, which branches to promote, escalation), proposes threshold shifts within fixed bounds, and flags `no_good_fit` with a short description. This mirrors Etsy (one LLM call per buyer, nightly batch; 10M buyers in 3 days instead of 21, 94% lower cost per million, DOCUMENTED secondary) and PersonaAgent (persona refined from per-user memory, DOCUMENTED). Volume: VANI's daily dial list, not the whole base.
3. **Code gates.** Validators: schema; cited fields exist; no digits, price words or internal labels in spoken text (FAQ Q5); plan starts with greet-and-confirm-owner and keeps human-on-request; guardrails equal the fixed set; confidence ≤ completeness (FAQ Q6). If the scoreboard is decisive (p_best ≥ 0.95 in that segment) and the agent disagrees, code follows the scoreboard and logs the override. On failure: one repair call, then the code-only path.
4. **Logged draw.** Code turns the ranking into a distribution: holdout share to P0 (e.g. 10%), an exploration floor per eligible persona, the rest to the agent's top choice. Code draws and logs the **exact probability**. Exploration and holdout are off for the judged demo sellers and logged as such.

**WHAT.**
```
persona_decision = {decision_id, seller_key, snapshot_id, path: agent|code_only|fallback,
  versions{library, scoreboard, estimator, agent_prompt, model, validators, git_sha},
  candidates[{persona_id, p_scoreboard, p_agent, reason}], chosen{persona_id, sarvam_agent_version,
  propensity, arm: agent|explored|holdout}, start_language, voice{voice_id, gender},
  levels{formality, warmth, brevity}, plan{opening_native, steps[], personalisation[{field, line}],
  objection_order[], branches{on_rush: promoted|dormant, …}, escalation[], guardrails_ref},
  sensitivity{rush: θ, confusion: θ, frustration: θ, interest: θ}, fit: ok|weak|no_good_fit,
  no_fit_note?, reasons[{field, text, cited_fields[]}], confidence, missing_fields[],
  tool_trace_ref, overrides[]}
```
**FEEDS** B6; B12 (decision record); `no_good_fit` rows → B11 Task B.

### 6.3 B6 Cook-ahead, re-cook, dial-time check

**WHY.** The spec must be current when the phone rings. 40.5% of sellers have ≥ 2 calls and hold 71.3% of calls; the median gap between calls is ~1 day (PROVEN). A nightly cook alone would often be stale.

**HOW.** (i) Nightly cook for tomorrow's dial list. (ii) **Event re-cook** after each call's outcome and after an accepted reviewer memory update (Etsy also times refresh by activity, DOCUMENTED). (iii) **Dial-time check**: stale if any seller event after `source_watermark`, a library/scoreboard/validator version change, spec age > TTL (proposed 72 h), or the version is unpublished. Stale → **fast code-only path** (no LLM; target p95 < 1 s, ASSUMED). DNC → no call. The call is never blocked otherwise.

**WHAT.** Store row `{seller_key, decision_id, cooked_at, source_watermark, versions, path, scheduled_dial_at}`; each call logs `spec_freshness: nightly|event|dial_fallback|default`. **FEEDS** B7.

---

## 7. Live call: B7 and B8

### 7.1 B7 Compile + Sarvam voice agent: what Sarvam gets

**WHY.** D3 live demo; voice in 2+ languages (15). The core agent must be Sarvam.

**At call start** (per call):

| Sarvam input | Value | Evidence |
|---|---|---|
| Agent version | the chosen persona's published version (voice map, pace, pitch) | Version route DOCUMENTED; per-call SDK `text_to_speech_config` ignored (PROVEN, re-checked 2026-10-09) |
| `initial_language_name` | start language; **also selects the voice** via Per-language voices | PROVEN 2026-10-09 |
| `initial_bot_message` | opening in **native script** | Spoken verbatim (PROVEN); romanised input degrades TTS (DOCUMENTED) |
| `agent_variables` | `decision_id`, `persona_directive` (= plan + base mode), `seller_mode` (base) | Works (PROVEN); `decision_id` echo per tool call untested |

The fixed base prompt holds the pitch goal, product facts, prices and compliance text. No persona can change them (FAQ Q5). With the plan re-sent, 0/8 price-demand turns quoted an amount (PROVEN). Code Tools, which would allow a per-call voice inside a language, were requested from Sarvam by email on 2026-10-09.

**Per turn:** the agent calls our tool on seller turns and receives `{seller_mode, persona_directive}`.

**WHAT.** `persona_decision` → `{sarvam_start_payload, call_config}`; `call_config = {decision_id, plan_prefix, base_mode, branches, sensitivity, priority, max_switches: 2, versions}`. **FEEDS** Sarvam; B8.

### 7.2 B8 Signal / switch server (live switches with Jev)

**WHY.** Switches (25), D4 switch log, FAQ Q3 (live) and Q4 (five signals). After the first rush cue only about 2 seller turns remain (PROVEN), so the switch must act on the current turn.

**HOW.**
1. **Input.** Each seller utterance arrives by Sarvam tool call, in Devanagari ASR text. The tool fires 6–7 times per 4 seller turns (partial + full), so decisions are **idempotent per utterance** (PROVEN behaviour).
2. **Decide now.** A lexicon (romanised + Devanagari, normalised) decides in < 5 ms.
3. **Correct next turn.** Jev (TypeSafe decision model via the OpenRouter Decisions API) runs asynchronously, ~480 ms p50, 49/51 agreement on a romanised smoke set (PROVEN; Devanagari untested). Its verdict applies at the next tool call.
4. **Code policy.** Priority (frustration > confusion > rush > interest; ASSUMED), hysteresis (crisp stays until ≥ 2 long engaged answers), max 2 switches, and **per-seller thresholds** from `call_config.sensitivity` (Bayes: a prior rusher at p0 = 0.31 needs a cue ~1.7× weaker than a base seller; ASSUMED arithmetic; detector likelihood ratios unmeasured).
5. **Output every turn, switch or not:** `persona_directive = <call plan> | Right now: <mode directive>`. The plan must ride every turn: 20/20 plan checks with re-send vs 23/28 without, personalisation 0/2 (PROVEN). A synchronous LLM was rejected: ~2.6 s replies (PROVEN).
6. **Language switch:** Sarvam's built-in switch works (6/6, PROVEN), but our tool is not called on that turn (4/4). B8 logs it from the transcript language/script field with `source: sarvam_builtin`.
7. **Known issues.** Lexicon false positive: "phir se pooch raha hoon, price batao" read as confusion (4/4); needs a context guard (Loop 1). About 17% of turns show restarted replies; hypothesis: early end-of-turn at a mid-utterance pause (unconfirmed). This risks voice quality more than any persona choice.

**WHAT.** In: `{decision_id, call_id, turn_id, utterance, is_final, ts}` + `call_config`. Out to Sarvam: `{seller_mode, persona_directive}`. Out to log: `{decision_id, turn, signal, source: lexicon|jev|sarvam_builtin, confidence, threshold_used, change, reason, plan_step, switch_no, versions}`. **FEEDS** Sarvam; B12; B9.

---

## 8. Between runs: B9 and the two loops

Learning happens only between calls. No model is trained. Only our tables, lexicon, thresholds, memory and library change (DOCUMENTED team decision).

**B9 Reviewer + outcome join.** An offline LLM on the internal gateway or Sarvam, with names and numbers masked, labels each call: true signal and onset per turn; each switch as correct, late, missed or false; each persona dimension and plan element as fit, misfit or no evidence. A label counts only with **two keys** (reviewer and Jev agree, or a human confirms), because lexicon vs PS07 evaluator agreement is κ ≈ 0.03 (PROVEN). The outcome joiner applies the declared reward and join window. Out: `review{decision_id, turn_labels[], switch_verdicts[], persona_fit[], plan_fit[], reviewer_model, prompt_version}`, `outcome{decision_id, kind, value, observed_at}`.

**B10 LOOP 1, switch loop.** Missed → positive cue; false → negative or context guard; late → earlier cues. It writes lexicon cues (romanised + Devanagari), per-signal per-script thresholds, and Jev question wording (at most once). **Gate:** a frozen hand-labelled gold set (≈ 350–400 August calls with Devanagari twins + canaries); no per-signal regression; flip list signed off; one component per version. Feeds **B8 on the next call**. Headline metric: rush switched on the same turn (d = 0) on Devanagari gold, false switches unchanged.

**B11 LOOP 2, persona loop.** Outcomes and reviewer fit labels update **seller memory** (enumerated tags only; auto-applied to that seller; triggers a B6 re-cook) and the **scoreboard** (counts with forgetting). **Agent Task B** runs weekly. It reads `no_good_fit` sellers with their notes, the scoreboard and failure reviews. It **proposes** new, merged, split or retired VANI personas as draft cards. Code checks each proposal: support (≥ ~500 sellers), stability across two time windows (ARI ≥ ~0.7; PS07 buffer reached only 0.54 between Aug and Sep, PROVEN), and an audible delivery difference from existing personas. A human approves; the non-tech owner auditions the voice; a new version is published with a weak prior. Retired personas stay in the registry. Feeds B2, B4, B6 and B3.

| Loop | Learns from | Changes | Gate | Feeds |
|---|---|---|---|---|
| 1 Switch | reviewer switch verdicts | lexicon, thresholds, Jev wording | frozen gold + canaries + flip list | B8 |
| 2 Persona | outcomes, fit labels, no-fit notes | memory, scoreboard, library | two-key labels; code checks + human for library | B2, B4, B6, B3 |

## 9. B12 Data created from day one (cannot be backfilled)

| Record | Key | Must hold |
|---|---|---|
| `seller_snapshot` | snapshot_id, as_of | exact B1 output used; extract_version; missing fields |
| `decision` | **decision_id** (minted at decision, passed in `agent_variables`, written on every switch row) | all versions; candidates with p_scoreboard and p_agent; chosen; **propensity**; arm (agent/explored/holdout); path; **agent tool-call trace**; validator results; overrides |
| `call` | call_id, decision_id | **voice requested** (version + language) vs **voice observed** (median F0: male ~85–155 Hz, female ~165–255 Hz, PROVEN technique); turns; switch log; duplicate tool calls; latency |
| `outcome` | decision_id, kind | **declared reward definition id**, fixed join window, default 0 |
| `review` | decision_id | reviewer and human labels; gold-set hash; splits fixed before data |
| manifest | version id | content hashes for library, scoreboard, lexicon, thresholds, prompts |

Storage: append-only JSONL → Parquet + DuckDB views in git-ignored `data/`. Backfilled PS07 rows carry `propensity = null`, `causal_claim_allowed = false`.

---

## 10. Work split for 3 people

**Hour 0–2, all three:** agree the contract files in `app/contracts/` (JSON Schema + one example each): `seller_context`, `seller_estimates`, `persona_library`, `scoreboard`, `persona_decision`, `call_config`, `sarvam_start_payload`, `tool_turn` (request/response), `switch_log_row`, `call_record`, `review`, `outcome`. Plus fixtures: 6 synthetic seller files (no PS07 text), a 2-persona mini library, recorded utterance lists per signal.

| Member | Owns | Tests alone with | Done when |
|---|---|---|---|
| **S — strong dev** (critical live path) | B7 compile, Sarvam versions + per-language voices, B8 signal server, switch log, F0 voice check | fixture `persona_decision` + `call_config`; scripted utterance lists; Sarvam SDK test calls | A live call follows the plan, one live switch is logged, voice requested = observed |
| **M — second member** (offline path) | B1, B2, B4, B5 (code-only first, then Agent Task A), B6, B12 records | fixture seller files; stub library and scoreboard; mock agent that returns a fixed `propose_decision` | One command turns sample seller files into validated `persona_decision` JSON with reasons; agent path falls back cleanly |
| **N — non-tech member** | B3 content: persona cards, plan moves and branches in native script, voice auditions (S's script measures F0 / wps); B9 gold labels; demo script and video; one slide; skills.md | library JSON validated by M's schema check; labelling sheet | Library v1 approved; ≥ 150 gold calls labelled; demo recorded |

**Integration order.** (1) Contracts + fixtures. (2) In parallel: S runs a live call from a fixture decision; M produces decisions from fixture sellers on the code-only path; N fills library v1. (3) Join M → S: real decisions drive live calls. (4) Switch log + 2–3 contrasting demo sellers in 2 languages. (5) Agent Task A on top of the code-only path. (6) Loops shown as recorded artefacts: one reviewed call, one gated lexicon diff (including one rejected diff), one scoreboard update, one Task B proposal. Cut order if late: Task B, Jev wording A/B, Task A (code-only path still meets D1/D2).

---

## 11. How PS04 is met

| PS04 item | Met by | Shown as |
|---|---|---|
| D1 generator on sample files | B1 → B2 → B5 (→ B6) | `persona_decision` per seller |
| D2 spec with reason per choice | B5 reasons, cited fields, confidence, missing fields | spec + "why" panel |
| D3 live demo, ≥ 1 live switch | B7 + B8; a human speaks; contrasting personas and languages | recording + agent id |
| D4 switch log | B8 rows incl. `sarvam_builtin` language switches | table |
| D5 one slide | sample spec + seller evidence (traits/states with n) + this diagram | slide |
| Fit 25 | traits/states + memory (memory predicts next meeting at AUC 0.71 vs 0.58 for profile, PROVEN) + agent reading summaries | per-seller reasons |
| Switches 25 | lexicon now, Jev next turn, per-seller thresholds, plan kept | live switch + log |
| Distinctness 20 | audible persona versions + per-seller plan | A/B audio of 2–3 sellers |
| Voice 2+ languages 15 | per-language voices; native-script text; built-in switch | demo |
| Evidence 15 | seller-side evidence is PS07-backed; VANI-side mapping honestly marked hypothesis + scoreboard | evidence table |

## 12. Devil's advocate

1. **"A persona library is the fixed library FAQ Q1 forbids."** Q1 forbids a fixed library as *output*. Our output is a per-seller persona: version + language + levels + plan + thresholds. Residual: judges may read "seller → P1" as fixed. Lead the demo with the per-seller spec and plan; ask organisers on day 1.
2. **The agent may be decorative or wrong.** No valid test compares the agent with code: the earlier 23/23 vs 16/23 used circular labels and no free text. Guard: validators, logged code-only path, and a side-by-side on held-out sellers (predictive validity on the next real call, reviewer fit). If the agent does not beat code-only, ship code-only for decisions and keep the agent for plan wording.
3. **The VANI-side mapping has no evidence today.** PS07 had one style. Every seller-type → persona link is a hypothesis until ≈ 2,000 calls per arm per segment. A real effect may be ~1 point, which needs ~9× more traffic. IndiaMART's three static-personalisation trials did not beat control (PROVEN). Claim fit, distinctness and live switching, not lift.
4. **Self-fulfilling plans.** "NI history → easy exit" can cause the next NI. Mitigation: robust defaults, dormant branches, live confirmation; only the holdout can detect it.
5. **Data on premises.** Task A reads free-text summaries; Jev (OpenRouter) receives live utterances. Use masking, the internal gateway or Sarvam for the agent and reviewer, and synthetic sellers until an organiser ruling.
6. **Cold sellers (about half)** have no stable type. They get P0 or a robust default at low confidence; live switches do most of the work.
7. **September relabelling** (NI 49–57% → 19.1%) and rising evaluator coverage distort types and scoreboard priors. Report NI on August only; refit types on the newest data.
8. **Voice limits.** One voice per language per version; Code Tools pending; agent-level pitch untested; thin catalogues in some languages limit audible distinctness.
9. **Live-path risks.** Jev untested on Devanagari; ~17% restarted replies; signal server is a single point of failure for plan re-send.
10. **2-day and pre-built rules.** Spike code is research; submission code is written at the event and disclosed in skills.md. Loops ship as recorded artefacts, not full automation.

## 13. Open questions

| # | Question | Who | Decides |
|---|---|---|---|
| 1 | **Team lead's alternative:** the agent *decides* with tools and emits new-persona signals at decision time, vs v2 (agent proposes, code draws and logs; new personas only via weekly Task B + human). Being researched separately. Compare on: exact propensity logging, validator coverage, cost per seller, what "new persona" means when audible changes need a published version | Team lead | B5 ownership; B11 timing |
| 2 | Does Sarvam echo `decision_id` in every tool payload? | Test | Join key |
| 3 | Will Sarvam enable Code Tools (per-call voice within a language), or a non-overwritten `@call_plan` variable? | Sarvam (emailed 2026-10-09) | Version count; plan re-send |
| 4 | Is the agent-UI pitch slider audible on v4, as the TTS API is? | Test | Pitch as a persona dimension |
| 5 | Can seller text go to the agent model, the reviewer and Jev? | Organisers | Task A on real data |
| 6 | May we explore and hold out on real sellers? | Business | Scoreboard learning start |
| 7 | Reward definition and join window | Business | B4, B9 |
| 8 | Does a library + per-seller spec satisfy FAQ Q1? | Organisers | Demo framing |
| 9 | Staleness TTL and fallback latency budget | Team lead | B6 |
| 10 | Will live VANI traffic run through this after the event? | Business | Whether the loops ever see volume |

## 14. Evidence index

| Claim | Tag | Source |
|---|---|---|
| Rush 30.8% vs 20.8%; terse, English, confusion recurrence; NI τ ≈ 28 d | PROVEN (fit ASSUMED) | `outputs/reports/VANI persona translation and library.md`; `outputs/reports/Between run learning loops.md` |
| 7 seller types K=7 ARI 0.868; cold ARI ≤ 0.44; 11.2% no-fit; buffer ARI 0.54 across months; Sept relabelling | PROVEN | `outputs/research_notes/Data derived persona library/ps07_library_prototype.md` |
| Memory AUC 0.71 vs 0.58; median gap 1.02 d; 40.5% / 71.3% | PROVEN | `outputs/reports/Between run learning loops.md` |
| Plan re-send 20/20 vs 23/28; built-in language switch 6/6, tool absent 4/4; "phir se" false positive; ~17% restarts; 0/8 price | PROVEN | `raw/research/2026-10-08-plan-stress-spike.md`, `…plan-following-spike.md` |
| Per-call SDK TTS override ignored | PROVEN | `raw/research/2026-10-08-voice-override-spike.md`, `2026-10-09-sarvam-voice-recheck.md` |
| Per-language voices select voice per call | PROVEN | `raw/research/2026-10-09-per-language-voice-spike.md` |
| Pace and pitch work on v3/v4 via TTS API; 222 v4 voices; native script required | PROVEN / DOCUMENTED | `raw/research/2026-10-09-sarvam-voice-recheck.md` |
| Jev 49/51 at ~480 ms; synchronous LLM ~2.6 s | PROVEN (romanised) | `outputs/reports/Persona generator architecture.md` |
| Etsy nightly per-buyer LLM profiles; PersonaAgent; TnT-LLM | DOCUMENTED | `raw/research/2026-10-09-last30days-agents-refine-personas-segments.md` |
| Alexa+ styles on shared dimensions; Pega StartingEvidence 25; ≈ 2,000 calls/arm | DOCUMENTED / ASSUMED arithmetic | `outputs/reports/VANI persona translation and library.md` |
| Starting count of 5; every seller-type → persona mapping; thresholds; TTL | ASSUMED | this plan |
| 23/23 vs 16/23 rules vs LLM | Not used as evidence (circular labels, no free text) | `outputs/reports/Persona generator architecture.md` |
