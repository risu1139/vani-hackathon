# VANI Persona Design (PS04): high-level architecture plan v1

As of 2026-10-09. For the team lead first, then an external reviewer. Method: top-down blocks, each with why / how / what / feeds (`.claude/skills/design-architecture/SKILL.md`). Architecture level only, no code.

**Evidence tags.** **PROVEN** = measured by us (spike or PS07 data run). **DOCUMENTED** = stated by an official doc, the PS04 brief or a cited paper. **ASSUMED** = our design choice or inference, not yet tested.

**Terms used.**
- **VANI**: IndiaMART's outbound voice bot that calls sellers.
- **PS04**: the hackathon problem "Persona Design".
- **PS07 data**: the past VANI call data the organisers shared: 149,363 sellers and 269,455 answered calls (Apr–Sep 2026), of which ~12K are transcribed. It is held on premises in a git-ignored folder, and only aggregates appear here.
- **Warm / cold seller**: a seller with at least one earlier answered call / a seller with none.
- **Sarvam agent**: the voice agent platform that speaks every word (core agent, mandated).
- **Jev**: an OpenRouter "decision" endpoint available through IndiaMART. It answers a yes/no question about a text. It is not a chat model.
- **Persona library**: a versioned set of seller *types* mined from data. It is not the output.
- **Persona spec**: the per-seller output.
- **Cook**: build and store a seller's spec ahead of the call.
- **Beta table**: for each persona × segment × setting, a count of successes and failures, giving a rate with an uncertainty interval.
- **Propensity**: the probability with which the system chose the action it executed. It is needed to evaluate other policies later.
- **lakh** = 100,000. 12 lakh = 1.2 million sellers.

---

## 1. Summary

1. **What.** For every seller we produce a persona spec before the call: voice, language, tone, pace, and a conversation plan, with a reason, evidence tier and confidence on every field. During the call the spec adapts live to frustration, confusion, interest, a language switch or rush, and every switch is logged.
2. **How (offline).** A persona library is **mined from past-call data**, not from team hypotheses. Each night, code **cooks** a spec for every seller due to be called. It ranks the library personas for that seller and adapts the best fit with the seller's own history, language and personalisation facts. A seller who fits no persona gets a low-confidence default and goes to a misfit buffer, from which new personas are promoted offline after human approval. No LLM runs per seller at runtime.
3. **How (live).** The Sarvam agent speaks. Our signal server decides each live switch in code: a keyword lexicon decides now, Jev confirms on the next turn, and a code policy owns the decision. The server re-sends the call plan with every directive, because Sarvam overwrites it each turn.
4. **How (learning).** Learning happens only **between runs**, by editing data: evidence tables, seller memory and library versions. No model is trained. The records that make later learning possible are written from day one.
5. **Why it scores.**
   - Fit (25) comes from seller history, which beats profile at predicting outcomes (AUC 0.677 vs 0.595).
   - Switches (25) are live and logged.
   - Distinctness (20) comes from data-separated personas plus per-seller deltas.
   - Voice in 2+ languages (15) uses Sarvam's built-in switch.
   - Evidence (15): every rule carries n, rate and tier from PS07.

## 2. End-to-end diagram

```
 ┌──────────────────────── OFFLINE PLANE (weekly / on demand) ─────────────────────────┐
 │  PS07 + live call records ─► B1 (bulk, as-of) ─► B2 Library builder ─► library_vN    │
 │                                                     ▲   (clusters, cards, tiers,     │
 │                    misfit buffer ──(promotion gate, │    plan moves, wording cache)  │
 │                                    human approval)──┘                                │
 └──────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────── NIGHTLY COOK PLANE (night before dial) ──────────────────────┐
 │ dial list ─► B5 scheduler ─► B1 context ─► B3 assign (rank / no-fit) ─► B4 adapt +    │
 │                               builder          │                        compose plan  │
 │                                                └─► misfit buffer            │         │
 │                                     B6 validate ◄───────────────────────────┘         │
 │                                         │                                             │
 │                                         └─► spec store (spec + versions + watermark)  │
 └──────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────── DIAL-TIME PLANE (seconds before the call) ───────────────────┐
 │ B5: fetch spec ─► stale? ─yes─► fast re-cook (B1→B3→B4→B6, code only, cached words)  │
 │                    │no                                                               │
 │                    └─► B6 compile ─► Sarvam payload + signal-server call config      │
 │                         mint decision_id, write decision record                      │
 └──────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────── IN-CALL PLANE (live) ────────────────────────────────────────┐
 │ seller ◄─voice─► B7 Sarvam agent ──tool call each turn──► B8 signal/switch server    │
 │                     ▲                                       lexicon now · Jev next   │
 │                     └──── plan + "Right now: <directive>" ──┘ turn · code policy     │
 │                                                              └─► switch log          │
 └──────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────── POST-CALL LEARNING PLANE (between runs) ─────────────────────┐
 │ call trace + outcome ─► B9 reviewer ─► B10 updater + gate ─► Beta tables, seller     │
 │        │                                                     memory, lexicon/thresh, │
 │        └──► re-cook event for this seller's next call (B5)   library candidates      │
 └──────────────────────────────────────────────────────────────────────────────────────┘
 B11 DATA LAYER (append-only, on premises): seller_snapshot · library_vN · spec · decision
   · call (+ switch log, voice requested vs observed) · outcome · review · stats tables · manifest
```

## 3. Block table

| Block | Why (PS04) | How (choice; rejected) | Input → Output | Feeds | Status |
|---|---|---|---|---|---|
| B1 Seller context builder | D1 "seller file in"; FAQ Q6; fit | Deterministic script; *rejected:* LLM summariser, using seller-file history columns (they leak the future) | seller_key, as_of → `seller_context` | B2, B3, B4 | Leakage-free build PROVEN on PS07 |
| B2 Persona library builder | Distinctness, evidence; FAQ Q1 "types to explain" | Offline k-means on warm sellers, K=7, picked by stability; LLM only names and drafts cards, a human approves; *rejected:* team-hypothesis personas, GMM, trees, clustering cold sellers | contexts (bulk) → `library_vN` | B3, B4 | K=7 stable PROVEN |
| B3 Assigner (rank or no-fit) | Fit; FAQ Q6 | Nearest-centroid distance → top-3 + soft weights; novelty threshold; *rejected:* softmax classifier (over-confident on misfits), per-seller LLM | context + library → `assignment` | B4, buffer | PROVEN (11.2% misfit, 4.19 s / 12 lakh) |
| B4 Adapter + plan composer | D2 spec with reasons; fit, distinctness, FAQ Q1/Q5 | Precedence stack in code + approved plan moves + cached LLM wording, slot-filled; *rejected:* LLM writes the whole spec (16/23 vs 23/23) | assignment + context → `persona_spec` | B6 | Design ASSUMED; rules-vs-LLM PROVEN |
| B5 Spec store + cook scheduler | Scale; fresh fit | Nightly batch cook + staleness check + fast fallback + post-call re-cook; *rejected:* cook at dial time only, never re-cook | dial list, events → stored spec | B6 | ASSUMED |
| B6 Validator + compiler | Robustness; FAQ Q5 | 7 code validators + compile to Sarvam inputs; voice via a published agent version per voice profile; *rejected:* per-call TTS override (ignored) | spec → Sarvam payload + call config | B7, B8 | Validators PROVEN; override ignored PROVEN |
| B7 Sarvam voice agent | D3 demo; natural voice in 2+ languages | Sarvam agent, one state + variables; facts and prices only in the fixed base prompt | payload → speech, tool calls | B8, B11 | Plan followed 20/20 PROVEN |
| B8 Signal / switch server | D4 switch log; switches 25 | Lexicon now + Jev next turn + code policy; re-send plan every turn; *rejected:* synchronous LLM (~2.6 s replies) | utterance + call config → directive + log row | B7, B11 | Directives PROVEN; Jev 49/51 PROVEN |
| B9 Post-call reviewer | Evidence; switch quality | Offline LLM on internal gateway/Sarvam; two-key acceptance | trace + outcome → `review` | B10, B5 | ASSUMED |
| B10 Learning updater + gate | All criteria, indirectly | Edit tables (Beta, memory, lexicon, library), gated on a frozen test set + human; *rejected:* model training, mid-call learning | reviews, outcomes → new versions | B1–B4, B8 | ASSUMED |
| B11 Data layer | Evidence, robustness | Append-only JSONL → Parquet + DuckDB views, on premises; *rejected:* feature-store product (overkill) | all writes → views | all | ASSUMED |

---

## 4. Blocks, one layer beneath

### B1 Seller context builder (script; makes no decisions)

**Why.** PS04 deliverable 1 is "a seller file in, a persona out". FAQ Q6 requires missing fields to be flagged. Fit depends on history being correct *as of the call*.

**How.** A pure deterministic script with no LLM. It **makes no decisions**: no persona, no setting, no score. It only describes the seller.

The leakage rule is that only events strictly before `as_of` count. The seller-file history columns cover all of Apr–Sep, so they would leak the future. History is therefore rebuilt from the call-level records instead (PROVEN, PS07). The same script runs in bulk for B2, per seller for the nightly cook, and per seller for the dial-time fallback.

**What.**
- Input: `{seller_key, as_of, sources: seller_profile, call_log, evaluator_outputs, transcripts, seller_memory}`.
- Output `seller_context` (immutable, written to B11 as `seller_snapshot`):

```
{snapshot_id, seller_key, as_of, extract_version, source_watermark (last event ts seen),
 profile:   {zone→language proxy, state, turnover_band, business_type, nature, top_category, city},
 engagement:{pickup_ratio, enquiries, cqs},
 history:   {warm: bool, n_prior_calls, last_outcome, last_call_days_ago, outcome_shares,
             short_call_share, avg_answered_s},
 objections:{time, no_need, already_engaged, drop_after_identity, drop_mid_pitch, wrong_contact, dnc},
 signals:   {rush, terse, interest, english_heavy, regional, confusion, frustration: {k, n}},
 language_evidence: {observed_lang?, script?, source},
 flags:     {dnc, personalisation_fields_present[]},
 missing_fields[], completeness (0–1)}
```

**Feeds.** B3 and B4, per seller. B2 in bulk. The `source_watermark` lets B5 detect staleness.

### B2 Persona library builder (offline)

**Why.** Distinctness (20) and evidence (15). FAQ Q1 allows grouping sellers into types "to explain your logic". The library is that explanation layer, and every type carries measured rates.

**How.**
- **Warm sellers.** We run k-means on history, objection and signal features, with profile features down-weighted. **K=7 is the most stable choice.** Its bootstrap ARI is 0.868 (min 0.816), against 0.75–0.84 for other K. Silhouette is 0.271 (PROVEN). ARI measures agreement between clusterings fitted on different resamples (1 = identical). Silhouette measures separation: 0.27 means the personas are dense regions of a continuum, not islands.
- **The seven personas.** Call-me-later, short-call refuser, talked-no-outcome, meeting-fixed revisit, mid-pitch dropper, rusher and confused. On held-out Aug–Sep sellers they differ sharply in outcome. For example, meeting-fixed is 41.2% for the revisit persona against 11.3% overall, and not-interested is 56.2% for the refuser (PROVEN).
- **Cold sellers have no stable structure.** ARI is 0.16–0.44 and silhouette ≤ 0.11 at every K (PROVEN). We do not invent cold personas. Cold sellers get rule-based defaults from profile, with language from zone, at low confidence.
- **Language comes from a separate rule, not from clusters.** Zone mix is flat across the personas (PROVEN). Profile predicts English-heavy speech at AUC 0.682, against 0.539 for persona (PROVEN).
- **Each card** holds:
  - centroid and novelty radius;
  - setting levels (brevity, pace, simplicity, opening move, objection order), each with its driving statistic, n, rate vs base, interval and tier;
  - approved plan-move ids;
  - a wording cache per (persona, move, language), written offline by a Sarvam or internal-gateway LLM with slots such as `{business_name}`, `{category}` and `{last_call_days}`, and reviewed by a human.
- **The LLM's role.** It only names, describes and drafts. It sees only cluster aggregates and never seller text. This is the "algorithm groups, LLM summarises" split that the persona literature recommends (DOCUMENTED).
- **Library version.** `library_vN` is content-hashed. Surviving personas keep their ids, and merges and splits record parent ids.
- **Promotion from the misfit buffer** (offline, weekly). A new persona is admitted only if (i) it is stable across two time windows (ARI ≥ ~0.7), (ii) it lies beyond the novelty threshold, (iii) it changes at least one delivery setting, (iv) it has enough support (≥ ~500 sellers), and (v) a human approves the LLM-drafted card. It then enters with tier GUESS and a weak prior worth ~10–25 pseudo-calls (ASSUMED thresholds).
- **Rejected options.**
  - Team-hypothesis personas: untestable, and they risk stereotypes such as "rural → female voice".
  - GMM: K=7 ARI 0.751, less stable.
  - Outcome decision trees: leaves are not compact in feature space.
  - Clustering warm and cold sellers together: it only splits "has history" from "has none".

**What.** Input: bulk `seller_context` rows (train window) and `misfit_buffer`. Output: `library_vN = {personas[{id, name, centroid, radius, settings{level, stat, n, tier, reason_template}, plan_moves[], wording_cache_ref}], cold_rules, language_rules, calibration{p95_distance}, version, parent_ids}`.

**Feeds.** B3 (centroids, radius), B4 (settings, moves, wording) and B10 (stats keyed by persona id).

### B3 Assigner: rank, or flag "no good fit"

**Why.** Fit (25). FAQ Q6 (low confidence when unsure). It also supplies the "create" path.

**How.** Code only.
- **Ranking.** We compute the distance from the seller to every centroid and keep the top 3 with soft weights `w ∝ exp(−d²/τ)`. Score = −distance + β·(Thompson draw from the Beta table). **β = 0 now**, because PS07 used one voice and style, so there are no outcome differences between personas to rank on (DOCUMENTED). A softmax classifier was rejected because it assigns misfits confidently (open-set risk, DOCUMENTED).
- **No good fit.** If the nearest distance is above the calibrated p95 (2.42 on the train window), the seller is flagged. **11.2% of held-out warm sellers are flagged** (PROVEN). They still get a spec: the soft blend or the population default, ordinal settings pulled to neutral, confidence low, and higher live-switch sensitivity. The seller is written to the misfit buffer. **Runtime never creates a persona.**
- **Cold sellers** go to `cold_rules` directly, flagged `cold`, not to the buffer. They would flood the buffer, and they become warm after their first call.
- **Cost.** 12 lakh assignments take **4.19 s** end to end on a laptop (PROVEN). Feature building upstream will dominate (ASSUMED).

**What.** Output `assignment = {seller_key, snapshot_id, library_version, candidates[{persona_id, distance, weight}], top1, fit: ok|ambiguous|no_fit|cold, novelty_distance, propensity (1.0 now), features_used: 9/14}`.

**Feeds.** B4. The misfit buffer feeds B2.

### B4 Per-seller adapter + plan composer

**Why.** Deliverable 2 is one spec per seller with a reason per choice. Together with fit, distinctness, FAQ Q1 (the output is per seller), FAQ Q5 (delivery, not facts) and FAQ Q6, this block carries 60% of the problem score.

**How.** Code applies a **precedence stack** to every setting, and records which layer won:
1. **Hard gates**: DNC (no call), and "this language has no catalogue voice".
2. **The seller's own evidence**: trait posteriors such as rush, terse or confusion, shrunk toward the persona rate by n; observed language; last objection.
3. **The blended library-persona value.**
4. **Segment or cold-rule default.**
5. **Global default.**

Layers 4–5, or any missing input, set `confidence: low` (FAQ Q6).

**Language** comes from observed language, else the zone rule. **Voice gender and timbre** come from catalogue coverage for that language and are always tier GUESS. PS07 had one voice, so there is no evidence either way. Voice gender is never tied to region, turnover or category.

**The plan** is built from approved moves:
- Opening (e.g. a value hook before identity for the refuser; a callback acknowledgement for call-me-later).
- Personalisation lines, using only fields that are present.
- Objection order, with the seller's last objection first.
- Escalation (human on request, callback on rush).
- Fixed guardrails.

**Wording** comes from the B2 cache for (persona, move, language) and is slot-filled with this seller's facts. There is **no LLM call per seller**. Rules in code with one wording call scored **23/23** key decisions against **16/23** when one LLM call decided the settings, and the LLM's errors came with plausible false reasons that no validator caught (PROVEN, 6 synthetic sellers; the labels are circular, see §10).

`persona_delta` lists every field where this seller differs from the base persona, with the reason. This makes "a persona per seller" visible.

**What.**
```
persona_spec = {spec_id, seller_key, snapshot_id, versions{library, rules, plan_lib, wording, catalogue},
 base_persona{id, weight, fit}, persona_delta[{field, from, to, reason}],
 delivery{voice_profile, language, hinglish_mix, formality, warmth, brevity, pace, simplicity},
 plan{opening{move_id, text}, personalisation[{field, line}], steps[], objection_order[],
      escalation[], guardrails[fixed]},
 each field: {value, reason, cited_fields[], rule_id, tier STRONG|MODERATE|WEAK|GUESS, confidence, source_layer}}
```

**Feeds.** B6.

### B5 Spec store, nightly cook scheduler, dial-time fallback

**Why.** Twelve lakh sellers cannot each get a live LLM agent, and the spec has to be current when the phone rings.

**How.**
- **Nightly cook.** For tomorrow's dial list, run B1 → B3 → B4 → B6 (validate only), with `as_of` set to the cook time. Store the spec with its `source_watermark` and versions. This is a batch job of seconds to minutes (PROVEN assignment cost; feature-build cost not yet measured).
- **Dial-time check.** Fetch the spec and test the staleness rules below (ASSUMED rules and thresholds):

| # | Stale if… | Action |
|---|---|---|
| S1 | Any seller event after `source_watermark`: answered call, outcome, DNC, language change, accepted reviewer memory update, or a change to a decision-relevant profile field | Re-cook (DNC → no call) |
| S2 | A major version changed since cooking: library, rules, plan library, voice catalogue, compiler | Re-cook. A wording-only change → reuse the spec and re-render the text |
| S3 | Spec age > TTL (proposed 72 h; recency features shift, outcome memory has a ~20-day half-life) | Re-cook |
| S4 | The chosen voice profile or app version is unpublished, or the channel changed | Re-cook delivery only |
| S5 | Spec missing, or failed validation | Re-cook; if that fails → global default spec at low confidence |

- **Fast fallback.** The fallback is the same code path for one seller, using cached wording only. Target p95 < 1 s (ASSUMED, since there is no LLM in the path). If the wording cache misses, a per-language template is used. The call is never blocked except for DNC.
- **Event-triggered re-cook.** When a call ends and its outcome is written, re-cook for the seller's next scheduled call. If a later reviewer label changes seller memory, re-cook again. This matters because repeat sellers are typical: 40.5% of sellers have ≥ 2 calls and hold 71.3% of calls, with a **median gap of 1 day** (PROVEN). A pure nightly cook would be stale for many of them.

**What.** Spec-store row: `{seller_key, spec_id, cooked_at, as_of, source_watermark, versions, validated, scheduled_dial_at}`. Each call logs `spec_freshness: fresh|recooked_event|recooked_dial|default`.

**Feeds.** B6 compile.

### B6 Validator + compiler to the Sarvam payload

**Why.** Robustness, and FAQ Q5 (facts and price never change). This is where our spec meets Sarvam's partly lossy inputs.

**How.**
- **Seven code validators.** They check the schema; that cited fields exist; that the rule tier equals the table tier; that spoken text has no digits, price words or internal labels; plan gates (greet-and-confirm-owner first, human on request); that the voice exists for the language; and confidence ≤ min(tier cap, completeness). On failure: one repair, then the template (PROVEN that the validators run).
- **Compiler mapping.**
  - `initial_bot_message` = opening (PROVEN: spoken verbatim).
  - `initial_language_name` (PROVEN: works).
  - Voice = **one published agent version per voice profile**, selected per call. Per-call `text_to_speech_config` passed through the SDK was **ignored**: a female voice and pace 0.85 or 1.25 all came out as the default male voice (PROVEN). A per-call override needs Sarvam's on-start Code Tools, which are "on request" and not enabled for us (DOCUMENTED).
  - `agent_variables{decision_id, persona_directive = plan_prefix + base mode, seller_mode, …}`.
  - A signal-server call config: `{decision_id, plan_prefix, base levels, escalation, max_switches: 2, rule_trace}`.
- **Decision record.** The compiler mints `decision_id` and writes the immutable decision record (B11).

**What.** spec → `{sarvam_payload, call_config, decision_record}`. **Feeds.** B7 and B8.

### B7 Sarvam voice agent

**Why.** Deliverable 3 (live demo on Sarvam), and natural voice in 2+ languages (15). The core agent must be Sarvam.

**How.** One agent state plus variables (multi-state agents are legacy). The fixed base prompt holds the pitch goal, product facts, prices and compliance text, so a persona cannot change them (FAQ Q5). The agent calls our tool on every seller turn (24/24 PROVEN), sometimes twice, for a partial and then a full utterance. Sarvam's built-in language switch works (6/6 PROVEN), but our tool is *not* called on the switch turn. Language switches are therefore logged from the transcript's language field.

**What.** Payload → speech, a tool call per turn, and the transcript. **Feeds.** B8 (tool calls) and B11 (trace).

### B8 Signal / switch server

**Why.** Switches (25). Deliverable 4 (switch log). FAQ Q3 (the switch must be live) and Q4 (the five signals).

**How.**
- **Three layers, all frozen for the call.**
  - The **lexicon** (Devanagari + romanised keywords) decides the current reply in < 5 ms.
  - **Jev** runs asynchronously and corrects at the next turn (49/51 agreement, ~480 ms, PROVEN on romanised text only).
  - A **code policy** owns the decision: hysteresis, priority and at most 2 switches per call.
- A synchronous LLM was rejected. Replies would rise to ~2.6 s typical with 3.5–4.9 s tails, and after the first rush cue only ~2 seller turns remain (PROVEN).
- **The server re-sends the plan in every directive** (`<plan> | Right now: <mode>`). With the re-send the agent followed the plan **20/20** on hostile and Gujarati scenarios. With the plan only at call start it scored **23/28**, and personalisation dropped to 0/2 (PROVEN).
- Decisions are **idempotent per utterance**, so a doubled tool call does not count twice.
- **What a switch can change.** Voice and pace are fixed per call (DOCUMENTED, Sarvam UI). A switch changes wording, brevity, simplicity, tone, plan (cut to the callback offer on rush; replay the current step simply on confusion) and language. "Slow down" is approximated by shorter sentences.

**What.**
- Input: `{decision_id, utterance, ts}` plus the call config.
- Output to Sarvam: `persona_directive`.
- Output to the switch log: `{decision_id, turn, signal, source: lexicon|jev|sarvam_builtin, change, reason, plan_step, switch_no, versions}`.

**Feeds.** B7 (every turn) and B11.

### B9 Post-call reviewer

**Why.** Evidence (15), and better switches over time.

**How.** An offline LLM on the internal LiteLLM gateway or Sarvam, with names and numbers masked. Data handling needs an organiser ruling. Per call it labels the true signal and onset per turn; each switch as right, late, missed or false; and each spec field as fit, misfit or no evidence. A label is accepted only with **two keys**: the reviewer and Jev agree, or a human confirms. The lexicon agreed with the PS07 evaluator at κ ≈ 0.03 (PROVEN), so single-source labels are not trusted.

**What.** Trace + outcome → `review{decision_id, signals[], switch_verdicts[], field_fit[], reviewer_model, prompt_version}`. **Feeds.** B10, and a B5 re-cook if memory changes.

### B10 Learning updater + gate (between runs only)

**Why.** It improves fit, switches and evidence. PS04 does not score learning directly, so the scope is capped.

**How.** Nothing changes mid-call and no model is trained. What changes is data:

| Store | Update | Gate |
|---|---|---|
| Beta tables per persona × segment × setting | add (success, failure) from `decision ⨝ outcome` under the declared reward, with forgetting | Only explored traffic may drive structural or causal claims |
| Seller memory | enumerated tags (rushed, lang=gu, last objection), bi-temporal, ~20-day decay for state | Applies to that seller only |
| Lexicon + thresholds | missed → positive cue; false → context guard (e.g. "phir se" with a price demand is insistence, not confusion, PROVEN false positive) | No per-signal regression on the frozen gold set |
| Rules / tiers | re-tier with n, CI, time split | n ≥ 200, CI excludes 0, holds Apr–Jul → Aug–Sep, human |
| Library | promote, split, merge or retire (B2 criteria) | Stability + human approval |

Every edit bumps a version in the manifest, and rollback is a repoint. **Feeds** B1 (memory), B2 (buffer and refit), B3 (Beta tables), B4 (rules) and B8 (lexicon).

### B11 Data layer and records

**Why.** The evidence criterion, robustness, and every later learning stage. Some of these facts cannot be backfilled; PS07 itself shows the cost.

**How.** Append-only JSONL, compacted to Parquet, with DuckDB views (`v_seller_features_asof`, `v_seller_memory_asof`, `v_decision_outcome`). It lives on premises in git-ignored `data/`. Anything leaving that folder uses a salted seller hash and aggregates only. Records are listed in §6.

---

## 5. How each PS04 deliverable and criterion is met

| PS04 item | Met by | Evidence shown to judges |
|---|---|---|
| D1 Generator runs on sample seller files | B1 → B3 → B4 → B6 as one command over the sample files | Spec JSON per seller |
| D2 Spec per seller with a reason per choice | B4: reason, cited fields, rule id, tier and confidence per field; `persona_delta` | Spec + "why" panel |
| D3 Live demo, 2–3 contrasting sellers, ≥ 1 live switch | B6 → B7 → B8; a human speaks live (FAQ Q3); contrasting sellers from different personas and languages | Recording + Agent ID |
| D4 Switch log | B8 log, plus Sarvam built-in language switches read from the transcript | Log table |
| D5 One slide | Sample spec + its evidence card (n, rate vs base, tier) + this diagram | Slide |
| Fit 25 | Seller history drives the persona; persona predicts meeting at AUC 0.677 vs 0.595 for profile only (PROVEN) | AUC table |
| Switches 25 | Lexicon now + Jev next turn + policy; plan kept on switch (20/20) | Live switch + log |
| Distinctness 20 | 7 data-separated personas, whose setting vectors differ on 2–5 of 5 dimensions (PROVEN by construction; mapping ASSUMED) + language rule + per-seller deltas | Persona-vs-seller distance correlation |
| Natural voice, 2+ languages 15 | Hindi/Hinglish + Gujarati or Marathi v4 voices; built-in switch 6/6 | Demo |
| Evidence 15 | Every setting rule carries its PS07 statistic and an honest tier; GUESS where none exists (voice gender) | Evidence table |
| FAQ Q1 | Library = explanation layer; output = per-seller spec + delta | §8 risk 2 |
| FAQ Q5 | Facts and prices only in the base prompt; validators ban digits and price words | 0/8 price turns quoted an amount (PROVEN) |
| FAQ Q6 | `missing_fields`, completeness, low-confidence defaults, higher switch sensitivity | Spec fields |

## 6. Data created from day one (cannot be backfilled)

| Record | Key | Must hold |
|---|---|---|
| `seller_snapshot` | snapshot_id, seller_key, as_of | Exactly the B1 output the decision saw; extract_version; missing_fields |
| `spec` | spec_id | Full persona_spec, versions, cooked_at, source_watermark |
| `decision` | **decision_id** (minted at compile, passed in `agent_variables`, echoed on every tool call) | spec_id, spec_freshness, versions {library, rules, plan_lib, wording, catalogue, compiler, switcher, git_sha}, candidates + weights, fit flag, final action, **propensity** (1.0 now; real values once exploration is approved), arm_type (default / explored / holdout) |
| `call` | call_id, decision_id | **voice requested** (app version) vs **voice observed** (pitch check: male ~85–155 Hz vs female ~165–255 Hz, PROVEN technique), turns, switch log, duplicate tool calls, latency, plan-followed checks |
| `outcome` | decision_id, kind | **Declared reward, fixed in advance** (proposal: meeting fixed in call, or a positive next call within 14 days, and no DNC), a fixed join window, default 0 |
| `review` | review_id, decision_id | Reviewer labels + human labels on a sample; frozen gold set; seller-hash and time splits defined before the data |
| stats + manifest | version id | Beta tables, hypothesis register (GUESS priors with predicted direction), content hashes |

Backfilled PS07 rows carry `run_type=ps07_replay`, `propensity=null` and `causal_claim_allowed=false`.

## 7. Learning stages, now → later

| Stage | When | What it can learn | What it cannot |
|---|---|---|---|
| 0 Priors | Hackathon | Library, seller-side rules (language, brevity after rush, objection order), seller memory, from PS07 | Any effect of voice, tone or pace (PS07 had one voice) |
| 1 Evidence + memory | First weeks live | Per-seller adaptation, plan and wording, switch cues and thresholds, Beta rates per persona × setting | Causal persona effects while choices stay deterministic |
| 2 Exploration + off-policy evaluation | Months 1–6, if approved | Which setting works for which persona; scoring a new library offline. Needs ~680 calls per arm to tell 10% from 15% (ASSUMED arithmetic) | Arms never tried |
| 3 Distillation | 6+ months | A small learned ranking policy from logged, propensity-weighted data | Anything outside logged support |

## 8. Devil's advocate

1. **Cook-ahead staleness.** The median gap between calls is 1 day, so a nightly spec is often stale for repeat sellers. *Answer:* S1 plus the post-call re-cook make the event path the primary path for repeat sellers, and nightly is only the bulk path. *Residual:* reviewer labels may arrive after the next dial. The fast fallback is unmeasured at scale.
2. **"This is the fixed library FAQ Q1 forbids."** *Answer:* the library is the explanation layer Q1 explicitly allows. The output is a per-seller spec with its own memory, language, personalisation and `persona_delta`, and the library grows through promotion. *Residual:* judges may still read "Seller A → Persona 3" as a fixed library. Lead the demo with the spec and the delta, and show the persona only in the "why" panel. Ask the organisers on Day 1.
3. **One voice in PS07.** Every number is a propensity under the existing bot, which is correlational. Nothing shows that a different setting *helps*. Voice gender stays GUESS. Bot-version assignment was non-random (97% of Tamil Nadu sellers on one version). We claim "this type behaves like X; we infer Y", never "Y works".
4. **Cold sellers have no stable structure** (46–70% of anchors). They get rules plus defaults at low confidence, which is an honest limit. Live adaptation does most of the work for them.
5. **September relabelling and coverage drift.** In September the not-interested share fell from 49–57% to 19.1% and "General" rose to 54.8%, which is a labelling change, not seller behaviour. Evaluator and transcript coverage also rose over the period. Much of the 11.2% misfit rate is *new observation*, not new kinds of seller. The promoted candidates were stable on structure (ARI 0.967) but not across time (0.54 between Aug and Sep), so **promote nothing yet**. Refit periodically on the newest data, report NI results on August only, and monitor label and coverage drift.
6. **Per-call voice is blocked.** The SDK override was ignored (PROVEN). Published agent versions per voice profile bundle voice with pace, and Tamil has only 3 male v4 voices. Voice distinctness on the phone path is limited until Code Tools are enabled.
7. **In-call signals are not predictable from the persona** (AUC 0.52–0.58). The persona sets the starting point, and live adaptation is still required. This is consistent with PS04 but limits what pre-call fit can claim.
8. **Exploration on real sellers** needs an organiser or business ruling. Until then propensity is 1.0, nothing causal can be learned, and exploration stays off for the judged seller.
9. **Data on premises.** Jev (OpenRouter) receives live utterances, and the reviewer and the offline wording LLM see text. Mask the text, use the internal gateway or Sarvam for review, and use synthetic or teammate sellers until there is a ruling.
10. **Scope against the 2-day build rule.** PS04 does not score learning. Build B1, B3, B4, B6, B8 and minimal B11 records. Show B2 promotion and B10 as a recorded offline artefact and roadmap. Spike code written before the event is research, and the submission code must be written during the event and disclosed in skills.md.
11. **About 17% of turns have restarted replies** (likely Sarvam endpointing). This risks the voice-quality score more than any persona choice does.
12. **The 23/23 result is circular**, because the labels came from the same toy rule table. The real tiered rule table must be mined from PS07 before the slide claims "evidence-backed".

## 9. Decisions needed / open questions

| # | Question | Who | Decides |
|---|---|---|---|
| 1 | Does a library used as the explanation layer + per-seller spec satisfy FAQ Q1? | Organisers | Demo framing |
| 2 | Can Code Tools (on-start) be enabled, or a separate `@call_plan` variable that the tool never overwrites? | Sarvam | Per-call voice and pace; whether the plan re-send stays mandatory |
| 3 | How many agent versions per language can be published and dialled via Instant Outbound? | Sarvam | Voice action space |
| 4 | Does Sarvam echo `decision_id` in every tool payload? | Test | The join key |
| 5 | Can seller text go to Jev, the gateway reviewer or the Sarvam LLM? | Organisers | B8 and B9 on real data |
| 6 | May we explore and hold out on real sellers? | Business | Stage 2 start |
| 7 | Staleness TTL (72 h?) and the fallback latency budget | Team lead | B5 rules |
| 8 | Reward definition and join window | Business | B10 reward |
| 9 | Promotion thresholds (support, stability across windows) | Team lead | Library growth |
| 10 | Does live VANI traffic route through this after the event? | Business | Whether Stages 1–3 happen |

## 10. Status of evidence

| Claim | Tag | Source |
|---|---|---|
| Warm library K=7, ARI 0.868, silhouette 0.27; distinct held-out outcome rates | PROVEN | `outputs/research_notes/Data derived persona library/ps07_library_prototype.md` |
| Cold sellers have no stable clusters | PROVEN | same |
| Persona beats profile for outcomes (meeting AUC 0.677 vs 0.595) but not for in-call signals | PROVEN | same |
| 11.2% misfit at p95; buffer K=4 ARI 0.967, but only 0.54 across months | PROVEN | same |
| 12 lakh assignments in 4.19 s | PROVEN (laptop) | same |
| Rules + cached wording beat an LLM deciding settings (23/23 vs 16/23) | PROVEN, circular labels | `outputs/reports/Persona generator architecture.md` |
| Plan followed 15/16; 20/20 with re-send, 23/28 without | PROVEN, n = 4–10 calls | `raw/research/2026-10-08-plan-following-spike.md`, `…plan-stress-spike.md` |
| Per-call voice/pace override ignored; opening and language work | PROVEN | `raw/research/2026-10-08-voice-override-spike.md` |
| Code Tools on request, not enabled | DOCUMENTED | `raw/research/2026-10-08-sarvam-on-start-options-check.md` |
| Jev 49/51 at ~480 ms; synchronous LLM too slow | PROVEN (romanised only) | `wiki/projects/vani-hackathon/system-design.md` |
| Median 1 day between calls; memory AUC 0.71 vs 0.58 | PROVEN | `wiki/projects/vani-hackathon/learning-loops.md` |
| Setting mapping per persona (brevity, pace, opening…) actually helps | ASSUMED / GUESS | prototype note, settings table |
| Staleness rules, TTL, fallback < 1 s, promotion thresholds | ASSUMED | this plan |
| Reviewer two-key acceptance; Beta-table learning; stage plan | ASSUMED (literature-backed) | `outputs/reports/Data driven persona agent.md` |
| Voice gender choice | GUESS by construction | PS07 has one voice |
