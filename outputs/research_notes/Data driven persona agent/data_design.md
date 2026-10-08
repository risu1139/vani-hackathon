# Data layer for a persona-deciding agent (VANI PS04): what to log from day one, how to store it, how each learning stage uses it

As of 2026-10-08. Aggregates only: no seller names, numbers, messages or transcript text. Tags: **PROVEN** = computed on local PS07 data or in our spikes (cited from in-repo notes); **DOCUMENTED** = stated in a published source or a raw/wiki file; **ASSUMED** = our design or inference.

Pipeline under design (from the brief): seller-data extract script → LLM agent with tools decides persona (voice gender/timbre, language, pace, tone) + call plan → compiler → Sarvam voice agent (switch log from our signal server B5) → post-call LLM review (B10) → accumulated data improves rules / evidence / memory (B11) → later possibly bandits and training.

In-repo sources used: [PS07 data dictionary](../../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md) [DICT] · [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md) [LOOPS] · [system-design](../../../wiki/projects/vani-hackathon/system-design.md) [SYS] · [ps07_replay_and_review.md](../Between%20run%20learning%20loops/ps07_replay_and_review.md) [REPLAY] · [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md) [MEM] · [vani_options_test.md](../Persona%20generator%20architecture/vani_options_test.md) [SPEC].

---

## 1. Entity / event model: which records must exist from day one

### Takeaway
Six append-only record types, all keyed by one `decision_id` minted **before** the call: `seller_snapshot` (features as of decision time), `decision` (what the agent saw, could choose, chose, why, under which versions, with what probability), `call` (Sarvam ids, turns, switch log, latency), `outcome` (in-call disposition, joined later events, reviewer labels, human ratings), `review` (B10 JSON), plus two derived/mutable stores, `seller_memory` and `rule_table`. The single most important rule, from Microsoft's Decision Service, is to log (context, action, probability) **at the point of decision** and join the reward later, never to reconstruct context or action afterwards.

### Cited Findings
- Decision Service (Agarwal et al., 2016): the system "must record (x,a,p) at the time of decision and match the appropriate reward r to it". Named failure modes: features "stored as references to database entries that are updated by a separate process", so learning-time values differ from decision-time values; actions "overridden by downstream business logic" so the logged probability belongs to a different action; and probabilities "included as an action feature by accident". DOCUMENTED — [Decision Service, arXiv 1606.03966](https://arxiv.org/abs/1606.03966)
- In the same paper, simulated data-collection errors made training-time performance estimates diverge from test by: reward delay bias 1.3×, incorrect probability 3.0×, decision-as-feature 8.7×, modified feature 1.2×, deleted feature 2.4× ("undermines the entire value of a counterfactually accurate system"). DOCUMENTED — [arXiv 1606.03966](https://arxiv.org/abs/1606.03966) Table 3
- Its four abstractions are explore, log, learn, deploy; the log stage joins decision and reward events that share a key within a time window. DOCUMENTED — [arXiv 1606.03966](https://arxiv.org/abs/1606.03966)
- Azure Personalizer (productised Decision Service): each Rank call is an "event" with a unique `eventId`, used to associate the later Reward call with that decision; offline evaluation replays logged Rank/Reward data against candidate policies. DOCUMENTED — [Azure.AI.Personalizer namespace](https://learn.microsoft.com/en-us/dotnet/api/azure.ai.personalizer); [Personalizer offline evaluation](https://learn.microsoft.com/en-my/Azure/ai-services/personalizer/concepts-offline-evaluation)
- Vowpal Wabbit contextual-bandit format logs `action:cost:probability | features`; the ADF (action-dependent features) variant has one `shared` line of context features (never a label) plus one line per available action, with the label on the chosen action's line. Probability is logged so learners can correct for the bias of the logging policy. DOCUMENTED — [VW contextual bandits tutorial](https://vowpalwabbit.org/docs/vowpal_wabbit/python/latest/tutorials/python_Contextual_bandits_and_Vowpal_Wabbit.html)
- Existing in-repo pieces to reuse: persona spec shape `{seller_id, delivery{voice_gender, speaker, language, pace, pitch, formality, warmth, brevity}, plan{opening, steps[], personalisation[], objection_order[], escalation[], guardrails[]}}`, every field `{value, reason, cited_fields[], rule_id, tier, confidence}` (PROVEN validators) — [SPEC]; per-call memory record and derived per-seller summary (ASSUMED schema) — [MEM] Q1; reviewer output JSON with `switch_review`, `persona_fit`, `corrections`, `causal_claim_allowed` (ASSUMED) — [REPLAY] §2; compiler output incl. signal-server config with `spec_version` and `rule_trace` (PROVEN runs) — [SPEC] Q4.
- Platform facts that shape the call record: voice and pace are fixed per call; the per-session TTS override was ignored in the SDK spike, so the voice actually spoken can differ from the voice requested (PROVEN); our server only runs when the agent calls our tool (24/24 turns, sometimes twice) — [SYS].

### Inferences (ASSUMED schema; JSON shown, one row per record)

**IDs.** `decision_id` (UUIDv7, time-ordered) minted by the agent wrapper before compile; passed into Sarvam as an `agent_variables` field so every tool call to B5 carries it back (the Personalizer `eventId` pattern). `call_id` = Sarvam interaction/session id; `attempt_id` for PS07 replays. `seller_key` = salted hash of GLID in anything that leaves `data/`; raw GLID only inside IndiaMART infra.

**(a) `seller_snapshot`** — immutable, written at decision time (fixes Decision Service "modified feature").
```json
{"snapshot_id":"…","seller_key":"h(glid)","as_of":"2026-10-09T10:58:00+05:30",
 "extract_version":"x-2026-10-08a","source_tables":{"seller_files":"ps07@2026-10-07","calls":"through 2026-10-09T10:00"},
 "profile":{"state":"GJ","business_type":"…","turnover_band":"…","top_category_group":"…","gst_age_band":"…","num_categories":3,"cqs":62},
 "engagement":{"pickup_ratio_90d":0.4,"meetings_1y":1,"eng_present":true},
 "history_as_of_t":{"n_calls":3,"last_disposition":"Not Interested","last_gap_days":2.1,"prev2_disposition":"General",
                    "signals_last":{"rush":true,"terse":true},"objections_last":["callback_deferred"],"lang_last":"hi-Latn"},
 "flags":{"dnc":false,"already_in_touch_exec":false},
 "missing_fields":["eng_*"], "completeness":0.75}
```
History must be rebuilt from call-level rows up to `as_of`; the seller-file history columns cover all of Apr–Sep and leak the future (PROVEN in [MEM] Q1).

**(b) `seller_memory`** — derived, recomputed from (c)–(e), never hand-edited; bi-temporal (`valid_from`, `invalid_at`) so a newer language switch supersedes rather than averages (Zep pattern cited in [MEM] Q4). Holds state (last outcome, last objection, callback slot; decay half-life ~20 d, PROVEN-sized) and traits (rush/terse/English-heavy as Beta posteriors shrunk to segment rates) — [MEM] Q1.

**(c) `decision`** — the core record; the thing a bandit, OPE or distillation pipeline needs and cannot reconstruct later.
```json
{"decision_id":"…","snapshot_id":"…","seller_key":"…","ts":"…","run_type":"live|sim|ps07_replay",
 "versions":{"agent_model":"sarvam-105b","agent_prompt":"p-007","tool_schema":"t-003","rule_table":"rt-012",
             "voice_catalogue":"bulbul-v4@2026-10-07","compiler":"c-004","switcher":"sw-v1","code_git_sha":"…"},
 "features_used":["history.last_disposition","history.signals_last.rush","profile.state"],
 "tool_calls":[{"tool":"get_seller_context","args_hash":"…","result_hash":"…","ms":40},
               {"tool":"get_rule_table","args":{"setting":"pace","segment":"prior_rush"},"result_ref":"rt-012#R03"}],
 "candidates":{"pace":[{"value":"fast","score":0.62,"rule_id":"R03","tier":"MODERATE"},{"value":"normal","score":0.38}],
               "voice_profile":[{"value":"hi_f_crisp","score":0.5},{"value":"hi_m_warm","score":0.5}],
               "opening":[…], "lang_start":[…]},
 "gates_applied":["GATE_DNC","GATE_AI_DISCLOSURE_ON_ASK","GATE_DELIVERY_NOT_FACTS"],
 "agent_choice":{"pace":"fast","voice_profile":"hi_f_crisp", …},
 "explore":{"policy":"eps_greedy_per_setting","epsilon":0.15,"seed":"…","explored_settings":["voice_profile"]},
 "final_action":{"pace":"fast","voice_profile":"hi_m_warm","lang_start":"hinglish","opening":"time_boxed",
                 "plan":{"steps":[…],"objection_order":[…],"escalation":[…]}},
 "propensity":{"pace":0.925,"voice_profile":0.5,"joint":0.4625},
 "spec_ref":"specs/…json","spec_hash":"…","reasoning_summary":"≤300 chars, no seller text",
 "validator":{"passed":true,"repairs":0}}
```
Key points: `final_action` is what was actually **sent to Sarvam after all gates**, and `propensity` is P(final_action | snapshot) under the logged policy (the Decision Service override failure). `candidates` = the action set (needed for ADF-style logging and for any later policy that could have chosen differently). Agent chain-of-thought is stored as a short summary plus tool-call trace, not raw text.

**(d) `call`** — from Sarvam + B5.
```json
{"call_id":"<sarvam interaction id>","decision_id":"…","channel":"sdk|instant_outbound","app_version":"…",
 "voice_requested":"hi_m_warm","voice_observed":"default_m|…","pace_requested":1.1,"pace_observed":null,
 "start":"…","end":"…","duration_s":63,"answered":true,"ivr":false,
 "turns_ref":"turns/…parquet",            // turn_no, speaker, start_s, end_s, text, script(latin|deva), asr_conf
 "switch_log":[{"turn":3,"signal":"rush","src":"lexicon|jev","change":"brevity→short","directive_hash":"…","rule":"S-R2"}],
 "tool_calls":{"n":11,"dupes":2,"skipped_turns":0},
 "latency":{"reply_p50_s":2.1,"reply_p95_s":3.4,"jev_p50_s":0.5},
 "plan_followed":{"opening_verbatim":true,"steps_hit":["GREET_CONFIRM_OWNER",…]}}
```
`voice_observed` exists because the SDK spike showed the requested voice can be silently ignored (PROVEN, [SYS]); logging only the request would be the "logged action ≠ executed action" failure.

**(e) `outcome`** — several rows per decision, appended as they arrive.
```json
{"decision_id":"…","kind":"in_call|next_call|exec_contact|reviewer|human","observed_at":"…",
 "in_call":{"disposition":"Call Later / Busy","meeting_fixed":false,"who_ended":"SELLER","dnc_requested":false},
 "next_call":{"within_days":14,"disposition":"General","gap_days":3.0},
 "confounds":{"exec_contact_7d":true,"redial_count":1},
 "reviewer":{"review_id":"…","persona_fit":{"pace":"fit","language":"misfit"},"signals_true":{"rush":3}},
 "human":{"rater":"r1","fit_1to5":4,"natural_voice_1to5":3,"agrees_with_reviewer":true}}
```
Reward for any learner is a **declared function** over these rows with a fixed join window (e.g. "meeting fixed in call OR next call within 14 d"; default 0 if nothing arrives), matching the Decision Service "experimental unit" rule.

**(f) `review`** — B10 output verbatim as in [REPLAY] §2, plus `reviewer_model`, `prompt_version`, `text_view`, `causal_claim_allowed:false` for replays.

**(g) `rule_table`** — versioned; one row per (rule_id, segment key, setting, level) with `alpha`, `beta`, `n_eff`, `tier` (GUESS/WEAK/MODERATE/STRONG/DEMOTED), `source` (ps07_mined | reviewer_pooled | design_prior), `time_split_ok`, `created_in_version`, `retired_in_version`. Tier ladder and Beta-Binomial update as in [MEM] Q2.

### Gaps
- Whether the Sarvam session/interaction id is returned to us synchronously at call start, and whether `agent_variables` are echoed in every tool payload, is not verified here (tool payload contents were seen in spikes, the `decision_id` echo was not tested).
- No source found that defines logging for an **LLM-agent** policy specifically (all cited systems log a parametric policy's probabilities); the "agent proposes, code randomises" split below is our design.

---

## 2. Storage and the tools the agent calls

### Takeaway
DuckDB over append-only Parquet in git-ignored `data/` (on the VPN laptop / self-hosted Daytona) is enough for the hackathon and the next few months: raw events as Parquet partitions, all "views" (features as-of, segment stats, memory) as SQL over them. Point-in-time correctness (the feature-store idea) is the non-negotiable property; a feature store product is not needed. Move to the internal Postgres/warehouse only when multiple writers or live traffic arrive.

### Cited Findings
- Feature stores exist mainly to give "point-in-time correct" training sets: for each (entity, timestamp) retrieve the latest feature value valid at or before that timestamp, ignoring later updates, to prevent future leakage. DOCUMENTED — [Feast docs](https://docs.feast.dev/v0.22-branch); [Feast quickstart](https://docs.feast.dev/v0.12-branch/getting-started/quickstart)
- Trace store B8 is already planned as "one append-only record per run (JSONL + SQLite/DuckDB)". DOCUMENTED (ASSUMED build) — [SYS]
- PS07 volumes that the store must hold: 149,363 sellers; 269,455 answered bot calls; 278,332 evaluator rows; 139,555 turns / 12,788 calls. DOCUMENTED — [DICT]
- Bot-call history volume relevant to memory: 52,757 sellers (40.5%) with ≥2 answered calls hold 71.3% of calls; median gap ~1 d. PROVEN — [MEM]
- Sarvam LLM supports tool calling and strict json_schema, but strict mode fell into whitespace loops on a nested schema in 4/6 calls; `json_object` + code validation always parsed (6/6). PROVEN — [SPEC] Q1

### Inferences (ASSUMED design)

**Layout**
```
data/vani_store/
  raw/ps07/…csv                         (as delivered; read-only)
  events/decision/date=YYYY-MM-DD/*.parquet
  events/call/…   events/turns/…   events/outcome/…   events/review/…
  specs/<decision_id>.json              (full persona spec + compiled payload)
  versions/rule_table/rt-012.parquet    versions/prompts/p-007.txt   versions/manifest.jsonl
  vani.duckdb                           (views only; can be rebuilt from events/)
```
Writes: one JSONL line per event first (crash-safe), compacted to Parquet in batches. DuckDB views: `v_seller_features_asof(seller_key, ts)`, `v_seller_memory_asof`, `v_segment_stats(segment, setting, level)`, `v_decision_outcome` (decision ⨝ call ⨝ outcome with the reward window), `v_training_examples`.

**Agent tools (all read-only, all return provenance: `as_of`, `source_version`, `n`)**

| tool | input | output | notes |
|---|---|---|---|
| `get_seller_context` | `seller_key`, `as_of` | snapshot (a) + `missing_fields` + `completeness` | writes the snapshot row; the agent may only cite fields returned here (validator 2 in [SPEC]) |
| `get_seller_memory` | `seller_key`, `as_of` | state items with recency weight, trait posteriors (mean, n), `lang_pref`, `dnc` | stale-memory logic in code, not LLM ([MEM] Q4) |
| `get_segment_stats` | `segment` (dict of bucketed features), `metric` (`meeting`, `ni`, `rush`, …) | rate, Beta interval, n, time-split check, tier | coarse buckets (≤ ~30 keys per setting) so counts accumulate |
| `find_similar_sellers` | `seller_key`, `as_of`, `k` (≤20), `filter` (e.g. has_review) | list of `{seller_key, distance, last_persona_summary, outcome_summary, review_fit}` | k-NN over numeric/bucketed features + memory; returns aggregates, never transcripts; only rows with `ts < as_of` |
| `get_rule_table` | `setting`, `segment` | rules `{rule_id, level, tier, alpha, beta, n_eff, reason_template}`, `rule_table_version` | tier copied into spec; validator 3 prevents inflation |
| `get_voice_options` | `language`, `gender?`, `channel` | allowed voice profiles `{profile_id, speaker, gender, timbre_tag, app_version_for_phone}` | from the v4 catalogue (57 F / 32 M Hindi; Tamil 0 F) [SPEC]; on Instant Outbound only published `app_version`s count |
| `get_plan_library` | `move_type` | approved opening/step/objection/escalation ids + templates | the agent picks ids; wording via Sarvam |
| `propose_persona` (terminal) | per setting: ranked `candidates` with scores + reasons | — | the wrapper (code) applies gates, then exploration, then logs (c) |

The agent never writes to the store. Only the wrapper writes `decision`; only B5 writes `call`; only the reviewer/joins write `outcome`/`review`.

### Gaps
- Daytona disk persistence and whether a DuckDB file there survives restarts is unverified.
- Internal Postgres / warehouse write access for the team is unknown; ask on Day 1.

---

## 3. How each learning stage consumes the data

### Takeaway
Every later stage needs something only day-one logging can provide: evidence updates need per-segment counts with reviewer labels; retrieval needs time-stamped decision→outcome pairs; bandits and off-policy evaluation need the **probability of the action actually executed** and the set of alternatives; uplift needs randomised variation; distillation needs (snapshot, tool trace, final spec, quality label, versions). An LLM agent that deterministically picks one persona logs propensity = 1 for everything, which makes IPS/DR evaluation of any other policy impossible; so exploration must be an explicit, code-side randomisation step after the agent proposes candidates.

### Cited Findings
- Counterfactual estimation by importance sampling reweights each logged sample by P*(action|context)/P(action|context) and requires the logging probability to be nonzero where the new policy acts; clipped weights keep confidence intervals valid when support is limited, and the clipped part "ignores the domains poorly explored", i.e. it tells you when you need more exploration. Bottou et al. also note that randomising more dimensions needs more data. DOCUMENTED — [Bottou et al., JMLR 2013 (arXiv 1209.2355)](https://arxiv.org/abs/1209.2355) §4.2–4.7
- Doubly robust estimation combines a reward model with the logged propensities and is accurate if either the reward model or the logging-policy model is good; empirically lower variance than IPS. DOCUMENTED — [Dudík, Langford, Li, ICML 2011, arXiv 1103.4601](https://arxiv.org/abs/1103.4601)
- OPE needs overlap/positivity; weights explode as overlap shrinks, and violations preclude IPS/DR. DOCUMENTED — cited in [MEM] Q3 ([DOLCE, arXiv 2505.00961](https://arxiv.org/html/2505.00961v3))
- Netflix artwork personalisation uses contextual bandits and evaluates offline by "replay", which is unbiased only when it accounts for the probability of each image shown during exploration. DOCUMENTED (secondary summary of the Netflix tech blog; primary page returned 403) — [QCon SF 2018 slides](https://qconsf.com/sf2018/system/files/presentation-slides/2018-11_-_qcon_artwork_personalization_talk.pdf); [Reforge summary](https://www.reforge.com/blog/brief-netflix-artwork-personalization-through-multi-armed-bandit-testing)
- Spotify BaRT ("Bandits for Recommendations as Treatments", RecSys 2018) learns satisfaction for item × explanation × context with explore-exploit and uses inverse propensity scoring for off-policy training. DOCUMENTED (search summary; PDF host unreachable) — [McInerney et al. 2018 (patent family)](https://patents.google.com/patent/US11301513)
- The Open Bandit Dataset (ZOZOTOWN, NeurIPS 2021) is the reference public example of a properly logged bandit dataset: two policies (Bernoulli Thompson sampling and uniform random) run in an A/B test on the same platform, with logged action probabilities enabling OPE benchmarking. DOCUMENTED — [Saito et al., arXiv 2008.07146](https://arxiv.org/abs/2008.07146)
- Decision Service: reward-delay differences across actions bias learning; fix by a fixed join window and default reward. DOCUMENTED — [arXiv 1606.03966](https://arxiv.org/abs/1606.03966)
- In-repo learning decisions: no model trained during the hackathon; bandits and fine-tuning are "Out: no live traffic, no GPU, no time"; rules need n ≥ 200, CI excluding zero, holding on a time split (mine Apr–Jul, check Aug–Sep). DOCUMENTED — [LOOPS]
- Drift exists: P(NI again | prev NI) 75.8% Apr–Jul vs 63.4% Aug–Sep. PROVEN — [MEM] Q2
- Predictive-validity baseline: next-call meeting AUC 0.58 profile vs 0.71 memory; NI 0.54 vs 0.78 (time split). PROVEN — [MEM] Q1/Q3

### Inferences (ASSUMED design), stage by stage

1. **Evidence / rule updates (hackathon, Loop B2).** Input: `v_segment_stats` from `outcome.reviewer.persona_fit` grouped by (segment × setting × level). Update Beta(α0+k, β0+n−k); forgetting factor for drift; tier change only via the gate. Requires: segment features in the snapshot, `final_action` per setting, reviewer labels with `reviewer_model`/`prompt_version` (to re-weight if the reviewer changes), and the frozen gold set ids.
2. **Per-seller memory (hackathon, Loop B1).** Input: `call` + `review` + `outcome` for that seller, ordered by time; recomputed into `seller_memory` with `valid_from/invalid_at`. Requires nothing beyond (c)–(f).
3. **Retrieval of similar cases (cheap, day 2 or later).** `find_similar_sellers` reads `v_decision_outcome` restricted to `ts < as_of`. Useful as evidence text for the agent ("8 similar sellers given time-boxed opening: 6 fit per reviewer"). Requires snapshots (not current features) so neighbours are compared as they were.
4. **Bandits (later, live traffic).** Action space = a few discrete settings that are actually audible and controllable per call (voice profile, pace, opening move, objection order), not the full spec. Recommended logging policy: the agent proposes per-setting ranked candidates; code applies gates, then ε-greedy or Thompson sampling per setting with a floor probability; log `candidates`, `final_action`, `propensity`. VW ADF lines can be emitted directly from `decision` (`shared` = snapshot features; one line per candidate; label `0:cost:prob` on the chosen line). Reward from the declared window.
5. **Off-policy evaluation (later).** IPS / clipped IPS (Bottou) / DR (Dudík) over `decision ⨝ outcome` to compare "rule table rt-012" vs "rt-015" or agent prompt p-007 vs p-009 without a new A/B. Only valid on settings that were explored (propensity < 1 for alternatives). Report effective sample size and the clipped mass as a "need more exploration" flag.
6. **Uplift (later).** Needs randomised variation of the treatment of interest (e.g. memory-driven opening ON vs OFF) logged with its probability; then per-segment uplift (T-learner or DR-learner style; method choice not sourced here). PS07 cannot support it (one style).
7. **Distillation / fine-tuning (later; needs GPU or provider fine-tune, not available now).** One training example =
```json
{"input":{"snapshot":{…as of t…},"memory":{…as of t…},"rule_table_version":"rt-012","voice_options":[…],"tool_results":[…]},
 "target":{"persona_spec":{…final validated spec…},"reasoning_summary":"…"},
 "weight":1.0, "labels":{"reviewer_fit":0.86,"human_fit":4,"reward":0,"propensity":0.4625},
 "provenance":{"decision_id":"…","agent_model":"sarvam-105b","prompt":"p-007","split":"train|val|test_time"}}
```
   Filter: validator passed, reviewer fit ≥ threshold, human-agreed subset for eval. For reward-weighted distillation, weight by reward/propensity (IPS-weighted imitation; ASSUMED). Never train on PS07-era "personas" as targets: they were one style, not decisions.
8. **Held-out and time splits.** Fix at day one: (i) frozen hand-labelled gold set (ids in `versions/manifest`); (ii) seller-level split (hash(seller_key) mod 10 = 0 held out) so the same seller never appears in train and test; (iii) time split (mine before date D, test after; Apr–Jul vs Aug–Sep for PS07); (iv) never let a decision's own outcome or later calls appear in its snapshot.

### Gaps
- Uplift and DR-learner methods are named from general knowledge; I did not fetch a primary source for them in this session.
- Hackathon volume (~30–60 reviewed live/sim calls, [MEM] Q2) is far too small for bandit learning or OPE; these stages are justified only by the logging format, not by results in 2 days.

---

## 4. Bootstrapping from PS07: what can be backfilled and what cannot

### Takeaway
PS07 backfills snapshots (as-of rebuilt), memory, outcome/next-call outcome, turn-level replays for 12.8K calls, and rule priors for propensity-type rules ("who rushes again", "who says NI again"). It cannot backfill decisions with alternatives or propensities: VANI used one voice and one style, bot-version assignment was non-random, so there is no voice/pace/formality comparison and no OPE. Backfilled rows must be marked `run_type=ps07_replay`, `propensity=null`, `causal_claim_allowed=false`.

### Cited Findings
- PS07 contents and join keys (`fk_glusr_usr_id`, `attempt_id`); seller-file history columns summarise Apr–Sep. DOCUMENTED — [DICT]
- Turn transcripts exist only Jul–Sep (Jul 5,229; Aug 6,966; Sep 159 calls); 99.6% Latin script; they are LLM transcriptions from the `latency_repetition` evaluator, not our ASR. PROVEN/DOCUMENTED — [REPLAY] §1
- Bot versions: main_vani 208,605; arrowhead 30,676; last_met_d 23,046; personalis 452 (personalised-script trial, audio only, zero in turn transcripts). PROVEN — [REPLAY] §1
- 87.4% of a seller's consecutive calls used the same `lead_bot_version`; assignment non-random (97% of Tamil Nadu on arrowhead). PROVEN — [MEM] Q1, Q3
- "PS07 has no bot-voice or seller-gender column, and VANI used one voice, so nothing compares genders"; every gender choice tagged GUESS. DOCUMENTED — [LOOPS]
- Personalisation trials did not beat control (0 for 3). DOCUMENTED — cited in [REPLAY] §4
- Executive calls cover Aug–Sep only, metadata only (no text/audio), usable as a confound flag. DOCUMENTED — [DICT]; [REPLAY] §3
- Evaluator outputs are LLM outputs with low agreement with our lexicon (κ ≈ 0.03); disposition confidence "high" 99.9% (uninformative). PROVEN — [REPLAY] §1, §3

### Inferences (ASSUMED)

| record | backfill from PS07? | how / caveat |
|---|---|---|
| `seller_snapshot` | Yes, as of each historical call | rebuild history from call-level files up to t; don't use seller-file history columns |
| `seller_memory` | Yes | from bot calls + evaluators; signal memory only on 954 transcribed same-seller pairs |
| `call` + turns | Partly | 12,788 calls replayable; no switch log (our switcher replays produce one, flagged counterfactual after first switch) |
| `outcome` in-call / next-call | Yes | disposition, meeting_fixed, who_ended, next call + gap; exec_contact_7d as confound (Aug–Sep only) |
| `review` | Yes, by running B10 on replays | costs LLM calls on internal gateway; label as replay |
| `decision.candidates/propensity` | **No** | historical policy is unknown and essentially deterministic per segment |
| `decision.final_action` (persona) | Only as "style = bot_version" | not our settings; voice/pace/formality never varied |
| voice-gender / timbre evidence | **No** | stays GUESS until live calls deliberately vary it |
| rule priors | Yes for propensity rules (STRONG/MODERATE); weak priors for never-varied settings | e.g. P(meeting \| prev NI) 4.5% vs 4.4% time split |
| OPE / uplift on PS07 | **No** | no overlap; the personalis trial (452) might be an exception only if its assignment was randomised — unknown |

### Gaps
- Whether the `personalis` trial or `last_met_*` versions were randomly assigned (which would give a tiny natural experiment with known propensity) is undocumented; ask the data owner.
- No PS07 field records which TTS voice or pace was used per call.

---

## 5. Data quality, privacy (DPDP), versioning/lineage, and why propensities + versions from day one

### Takeaway
Treat every record as evidence that must be reproducible: same snapshot + same versions ⇒ same decision (modulo the logged random seed). Version everything the decision depended on (model, prompt, tool schema, rule table, voice catalogue, compiler, switcher, extract script) as ids in the decision row, using an OpenLineage-style job/run/dataset model if a standard is wanted. Keep personal data inside IndiaMART infra, pseudonymise outward, store category ids not quotes, and design for erasure. Logging propensities and versions is the one thing that cannot be added retroactively: Decision Service measured up to 3× (wrong probability) and 8.7× (decision leaked as feature) estimation error from logging mistakes.

### Cited Findings
- Reproducibility: "the ability to reproduce an online run offline is key to debugging a learning system, but rarely supported in full"; most systems "lack the ability to ask 'what if'". DOCUMENTED — [arXiv 1606.03966](https://arxiv.org/abs/1606.03966) (F4)
- Non-stationarity (F3): input distributions and downstream rules change over time. DOCUMENTED — same; PROVEN locally as 12-pt drift on NI recurrence — [MEM] Q2
- OpenLineage models lineage as Job (a process), Run (one occurrence of a job) and Dataset entities, with extensible "facets" (schema, quality, custom metadata) attached at event time. DOCUMENTED — [OpenLineage docs](https://openlineage.io/docs/); [OpenLineage facets](https://openlineage.io/docs/guides/facets)
- DPDP Act 2023 s.8(7): erase personal data when the specified purpose is no longer served or consent is withdrawn, unless another law requires retention; processors must be instructed likewise; storage limitation. DOCUMENTED — [DPDPA s.8 text](https://dpdpa.com/dpdpa2023/chapter-2/section8.html); [KS&K note](https://ksandk.com/data-protection-and-data-privacy/data-retention-and-storage-obligations-under-the-dpdp-act-2023/). DPDP Rules notified 14 Nov 2025; processing logs ≥1 year; retention/erasure provisions in force 13 May 2027 — cited in [MEM] Q4 ([SCC Online](https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/))
- Project rules: hackathon data only in git-ignored `data/`; only aggregates in raw/wiki; post-call review sending seller text to an LLM must use Sarvam or the internal gateway, with an organiser ruling on Day 1. DOCUMENTED — [AGENTS.md](../../../AGENTS.md); [LOOPS]
- PS07 is not masked (real names in summaries/transcripts/quotes), recordings are public MP3 links. DOCUMENTED — [DICT]
- Data-quality facts to check on ingest: coarse turn timestamps (5.7% overlap, `timestamp_suspect` 2.5%), 434 turn calls with no bot-call row, Devanagari vs Latin script mismatch between history and live ASR. PROVEN — [REPLAY] §1

### Inferences (ASSUMED)

**Quality checks (run on every write/compaction)**
- Schema + enum validation (reuse [SPEC] validators); `decision_id` uniqueness; every `call` has a `decision` (orphan rate), every `decision` has a `call` or an explicit `not_dialled` reason.
- `snapshot.as_of < call.start`; no snapshot field derived from rows with `ts ≥ as_of` (leakage test on a sample).
- `sum(propensity over candidates) = 1` per explored setting; `final_action ∈ candidates`; propensity ≥ floor.
- `voice_observed` vs `voice_requested` mismatch rate (the SDK override bug made this real).
- Reviewer drift: re-review 5% with swapped prompt order; κ vs gold set per `prompt_version` ([REPLAY] §3).
- Script tag per turn (Latin/Devanagari) so switcher metrics are split by script.

**Versioning / lineage**
- `versions/manifest.jsonl`: each version id → content hash + git sha + created_at + author + gate result. Decision rows reference ids, not copies.
- Rule table and prompts are immutable once used; edits create new ids (rt-012 → rt-013), which is also what makes "v0 → v1 → v2" visible to judges.
- Every derived table carries `built_from` (input version ids + max event ts); OpenLineage events optional.

**Privacy**
- Inside `data/` only: GLID, transcripts, recordings links. Outward (notes, wiki, dashboards, slides): `seller_key` hash, category ids, aggregates with n ≥ ~20 per cell (threshold ASSUMED).
- Memory stores categories/flags, not quotes; agent tools return no free text from transcripts.
- Erasure: `seller_key` → delete across events and recompute views (DuckDB rebuild from Parquet makes this practical); DNC is a permanent gate, retained as a minimal suppression flag (legal-basis question for IndiaMART legal, not decided here).
- LLM calls carrying seller text (agent, reviewer) only via Sarvam or internal LiteLLM gateway; log the endpoint used in `versions`.

**Why from day one**
- Propensities, candidate sets, as-of snapshots and versions are facts about the moment of decision; none can be recomputed later from outcomes. PS07 itself demonstrates the cost: 269K calls but no way to compare voices or styles.
- Adding them costs a few columns and one sampling step now; omitting them makes every future evaluation observational.

### Gaps
- No IndiaMART-internal guidance on DPDP retention periods for call transcripts was found; cell-size threshold for aggregates is unsized.
- Whether OpenLineage tooling is available internally is unknown; a manifest file is enough for now.

---

## 6. Devil's advocate: overkill for 2 days vs must-exist from day one

### Takeaway
PS04 scores fit, switches, distinctness, voice and evidence; it never scores learning across runs. With ~30–60 calls, no bandit, OPE, uplift or fine-tune will produce a result. What must exist is cheap: the `decision_id` thread, as-of snapshots, final action + candidates + propensity (even if ε = 0 for most settings), version ids, and the reward/join definition. Everything else is a view that can be built later from those rows.

### Cited Findings
- Scoring: fit 25, switches 25, distinctness 20, natural voice 15, evidence 15; no criterion for cross-run improvement. DOCUMENTED — cited in [MEM] Q5
- Budget: core deliverables ≈ 20–30 dev-hours vs ~18–24 usable; cap loop work at ~6 h; bandits/fine-tuning out. DOCUMENTED — [LOOPS]
- Small samples: with ~25–30 positives per signal only ~20-point gains are distinguishable; κ ±0.26 at n=30. DOCUMENTED — [LOOPS]
- Bottou: the more dimensions randomised, the more data is needed. DOCUMENTED — [arXiv 1209.2355](https://arxiv.org/abs/1209.2355) §4.7
- No pre-built solutions; Sarvam must be the core agent; no new outside vendors. DOCUMENTED — [AGENTS.md](../../../AGENTS.md)

### Inferences (ASSUMED)

| item | verdict for 9–10 Oct | why |
|---|---|---|
| `decision_id` minted pre-call, echoed via `agent_variables`, written in B5 switch log | **Must** | without it nothing joins; 15 min |
| As-of `seller_snapshot` + `missing_fields` | **Must** | needed for fit reasons, FAQ Q6 and leakage-free replay |
| `decision` row with versions, candidates, final_action, propensity | **Must** (columns) | cannot be backfilled; propensity = 1.0 is fine where not explored, but log it |
| Exploration on 1–2 settings (voice profile, opening move) at ε ≈ 0.1–0.2 | Optional, cheap | creates the first ever voice variation; honest GUESS→data story; risks a worse demo call, so turn off for the judged demo seller |
| `voice_observed` field | **Must** | the override bug means request ≠ reality |
| Outcome rows + declared reward window | **Must** (definition), next-call join later | |
| Reviewer JSON + human ratings on ~30 calls | **Must** for evidence tiers/κ | |
| JSONL → Parquet + DuckDB views | **Must** (simple) | 1–2 h |
| `get_seller_context`, `get_seller_memory`, `get_rule_table`, `get_voice_options` tools | **Must** if the agent is tool-using | they are thin SQL wrappers |
| `find_similar_sellers` | Nice-to-have | adds evidence text; easy to cut |
| `get_segment_stats` live in agent loop | Nice-to-have | precomputed tiers in rule table are enough |
| VW ADF export, OPE notebook | Later | no traffic to evaluate |
| Bandit learner, uplift models, distillation/fine-tune | **Out** | no traffic, no GPU, team decision |
| Feature store product, OpenLineage server, Postgres | **Out** for hackathon | DuckDB + manifest covers it |
| Free LLM persona reasoning as the source of truth | Risky | deterministic propensity 1; collapse to similar personas ([LOOPS]); keep rules + code sampling as the decider, LLM for candidates/wording |

- **Flag (out of PS04 scope):** claiming "the agent learned to book more meetings" from hackathon data. Say instead: "the data layer now logs what is needed for that claim once VANI runs live".
- **Tension to raise with the team lead:** an "LLM agent decides persona" design and a "logged propensity" design pull against each other. The resolution proposed here (agent ranks candidates with reasons; code gates, samples and logs) keeps the agent explainable for judges and keeps the data usable for later learning.

### Gaps
- Organiser rules on running exploratory (deliberately non-optimal) personas on real sellers during the event are unknown; ask Day 1.
- Whether IndiaMART will route live VANI traffic through this agent after the hackathon (the only way the later stages pay off) is undecided.
