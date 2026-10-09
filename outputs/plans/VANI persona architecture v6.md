# VANI Persona Design (PS04): whole-system architecture v6

As of 2026-10-09 (hackathon day 1). For the team lead, then an external reviewer. **Block level only**: each block's WHY / HOW / WHAT / FEEDS / STATUS. Component internals are designed later, one block at a time. Method: `.claude/skills/design-architecture/SKILL.md`. Supersedes [plan v5](VANI%20persona%20architecture%20plan%20v5.md) (what still holds is kept; component detail is dropped).

**Status tags.** **PROVEN** = measured by us (spike or PS07 aggregate). **DOCUMENTED** = PS04 doc, deck, official doc, team decision or a `raw/` source. **ASSUMED** = our design choice, not yet tested. **OPEN** = a decision or test still to make.

**Binding inputs.** Team decisions: [between-run learning](../../raw/hackathon/2026-10-08-team-decision-between-run-learning.md), [persona agent 1–7](../../raw/hackathon/2026-10-09-team-decisions-persona-agent.md), [data sharing](../../raw/hackathon/2026-10-09-team-decision-data-sharing.md), [one skill end to end](../../raw/hackathon/2026-10-09-team-decision-one-skill-e2e.md). Requirements: [PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md).

---

## 0. Summary (ASD-STE100)

1. VANI is the bot that calls sellers. This architecture gives VANI a persona for each seller.
2. A VANI persona is VANI's voice, speed, pitch, language, tone and call plan.
3. Seller data is the input. It is not the persona.
4. A peer data agent makes one context file for each seller. We use this file. We do not make it.
5. Code reads the context file and makes the seller's traits and states. Traits stay the same for a long time. States change from call to call.
6. One Claude Code skill does all the work with one trigger. It reads the seller, composes the persona and the call plan, fills the Sarvam variables and starts the call.
7. The skill runs on a frontier model. The skill uses two libraries as starting points: traits and states, and VANI personas. The agent composes. It does not only select.
8. Code checks the agent's output. Code checks facts, prices, compliance and ID numbers. The agent cannot change these checks.
9. Sarvam sets the voice, speed, pitch and opening at the start of each call. We proved this on 2026-10-09.
10. During the call, VANI adapts on the same turn. Prompt rules tell it how to answer each signal. Our keyword tool inside Sarvam runs on every seller turn. It sets the mode of record, ends the call on an opt-out, and writes the switch log. Sarvam's built-in switch handles language. After the call, a frontier model reviews the call.
11. After the call, a reviewer labels mistakes. Two learning loops then improve the switches and the personas. No model is trained.
12. We record every decision and every call from day one.
13. A nightly batch for all sellers is for production later. It is not part of the hackathon build.

---

## 1. What changed from v5

| v5 | v6 | Why |
|---|---|---|
| We build seller context (B1) and an estimator (B2) | Peer data agent supplies `seller_context`; we add a **Traits & States library + builder** | Decision one-skill §3; team lead brief |
| Batch cook, gate (agent only for ~40% of sellers), spec store, freeze engine | **One skill, one trigger** per seller, end to end; nightly batch = production section only | Decision one-skill §1–2 |
| Published Sarvam version per audible bundle; per-call version selection untested | **OnStart code tool + defined agent variables** sets voice, pace, pitch, opening per call | PROVEN 2026-10-09 |
| Separate directive-compiler block | "Compile Sarvam variables" is one step of the skill; prompt uses **variable-switched sections** (production pattern) | New buyer-side prompt evidence |
| Code seeded fallback from seed hypotheses | No fallback persona (team lead, 2026-10-09). A failed or disagreeing spec is repaired by re-running the agent with the validator errors | No rule table; agent stays the decider |
| Jev Devanagari untested | Jev native script **49/51, tricky 10/10, ~500 ms** | PROVEN 2026-10-09 |
| Review format undefined | **Fatal / Non-Fatal** labels mirroring the VANI QA matrix | New data file |

Kept from v5: frontier decider; agent composes, library = starting points; voice gender chosen from data, no quotas (update 2026-10-09: seller gender, recorded or else a name/voice guess with confidence, may pick VANI's voice gender only; raw/hackathon/2026-10-09-team-decision-seller-gender.md); code guards only guardrails and playability; ≥ 2 of 3 runs agree on the audible bundle; lexicon = switch of record; text-level live switches; two between-run loops; data-sharing policy and ID scrub; evidence tier per setting; freeze 12:00 D2 and backup video 16:00 D2.

---

## 2. End-to-end diagram

```
                      ONE TRIGGER: /vani-call <glid>   (Claude Code skill, frontier model, Daytona sandbox)
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ B0 SELLER CONTEXT (peer data agent; we consume)  data/contexts/<glid>_<as_of>.json                    │
 │        │                                                                                              │
 │ S1  fetch + ID-number scrub (code) ──► 01_context.json                                               │
 │ S2  B2 TRAITS & STATES BUILDER (code) ◄── B1 TRAITS & STATES LIBRARY ──► 02_seller_profile.json      │
 │ S3  B4 COMPOSER (agent ×3, tools) ◄── B3 VANI PERSONA LIBRARY (starting points) + scoreboard + memory│
 │        └► B5 GUARD + SETTLE (code; hooks agent cannot edit) ──► 04_persona_decision.json            │
 │ S4  B6 COMPILE SARVAM VARIABLES (code) ──► 05_sarvam_vars.json                                       │
 │ S5  B7 PLACE CALL (SDK session now · Instant Outbound after number rental) ──► 06_call_started.json  │
 │ S6  write status / decision record ──► 07_status.json (the one output contract)                      │
 └───────────────────────────────┬──────────────────────────────────────────────────────────────────────┘
                                 ▼
 SARVAM VOICE AGENT ── OnStart tool reads persona_voice_id/pace/pitch/opening → TTS + opening (fixed for call)
   seller ◄─voice─► agent  (base prompt: facts, prices, compliance; sections switched by variables)
        └── tool call per turn ──► B8 IN-CALL SWITCHER (in Sarvam): prompt rules + keyword tool + Patient endpointing
                                   ◄── persona_directive (+ call_plan, seller_mode) · switch log row
                                 ▼
 B9 REVIEW (Fatal / Non-Fatal; switch correctness; persona fit) ──► B10 LOOPS (between runs)
     LOOP 1 switch: keyword list · prompt rules (from frontier review) ── frozen gold gate ──► B8
     LOOP 2 persona: seller memory · trait/state + persona scoreboard · suggestions ── human ──► B1, B3, B4 tools
 B11 DATA RECORDS (from day one): snapshot ref · decision · call · switch log · outcome · review · manifest
```

---

## 3. Block table

| Block | Why (PS04 / rubric) | How (choice; rejected) | What: input → output | Feeds | Status |
|---|---|---|---|---|---|
| **B0 Seller context** (peer) | §3.1 seller data; FAQ Q6 | Peer agent joins PS07 + Global Context (5,000) + Best-Time-to-Call + onboarding, as-of; *rej.* building our own | GLID, as_of → `seller_context` | B2, B4 tools | DOCUMENTED (decision). Peer publishes its own output format doc in outputs/; WE own the adapter + `seller_context` schema. Peer decisions: busy kept as per-call rushed signal + call_later_busy count (no times); no GST/PAN/ID in LLM-facing output; history age-weighted (30 d full, 31–90 d short). **Update 2026-10-09 (later):** peer dropped G (old call history) and ships DATA only (points.json, ≤ 8 KB .llm.md, verified_facts, playbook as data); **peer supplies ALL data incl. raw old call history (G)**; we compute per-call signals, speech style and memory facts (as_of-clean) in our adapter/B2; persona + call plan stay with our B4 |
| **B1 Traits & States library** | Fit 25; Evidence 15 | Versioned JSON vocabulary; agent suggests, human adds; *rej.* seller-type clusters as the input, rule table | → `trait_state_library_vN` | B2, B4 | ASSUMED; recurrence evidence PROVEN |
| **B2 Profile builder** | Fit 25; FAQ Q6 | Deterministic script applying B1 definitions; *rej.* LLM builder (not repeatable, not checkable) | `seller_context` → `seller_profile` | B4, B8 | ASSUMED |
| **B3 VANI persona library** | Distinct 20; FAQ Q1 | Starting-point bundles over persona dimensions, native-script plan moves; *rej.* fixed menu, rule table | → `persona_library_vN` | B4, B6 | ASSUMED (levels); pace audibility PROVEN |
| **B4 Composer** | D1, D2; Fit 25 | Frontier agent in the skill, read-only tools, 3 runs; *rej.* select-only, single call without tools, Sarvam-105b as default | `seller_profile` + tools → `agent_run` ×3 | B5 | Flat-schema output PROVEN; frontier in skill ASSUMED |
| **B5 Guard + settle** | D2; FAQ Q5/Q6; Robustness 20 | Code validators + ≥ 2-of-3 agreement + evidence tier, enforced by hooks; *rej.* LLM self-check, agent confidence as gate | `agent_run` ×3 → `persona_decision` (+ `suggestion_row`) | B6, B11, B10 | ASSUMED |
| **B6 Compile variables** | D3; Voice 20 | Template to Sarvam agent variables + placeholders filled from context; *rej.* free-form prompt per call | `persona_decision` → `sarvam_call_vars` | B7, B8 | Variables → voice/pace PROVEN; template ASSUMED |
| **B7 Place call** | D3 live demo | SDK session now; Instant Outbound after number rental; *rej.* scripted simulator only (FAQ Q3) | `sarvam_call_vars` → `call_started` | Sarvam, B11 | SDK PROVEN; phone DOCUMENTED, blocked |
| **Sarvam agent** (platform) | D3; Voice 20 | OnStart code tool + base prompt with variable-switched sections | vars → live call | B8, B9 | OnStart PROVEN |
| **B8 In-call switcher** | Switches 25; D4 | Prompt rules (same-turn reply) + hardened keyword code tool (mode of record, opt-out, switch log) + Patient endpointing, all inside Sarvam; *rej. for now* live Jev (+0.54 s/turn warm, ~450 ms floor), webhook/client push (blocked/disproven), external host | utterance → `seller_mode` + `persona_directive` + `switch_log_row` | Sarvam, B11 | PROVEN (tests 2026-10-09); live Jev re-test last |
| **B9 Review** | Robustness 20; Evidence 15 | Frontier model (Claude in Daytona) reviews each call per turn, QA-matrix format, explains misses, proposes keyword/prompt diffs; human confirms; Jev optional cheap second labeller; *rej.* Jev as main reviewer (no reasons, turn-only), free-text notes | call record + switch_log → `review` | B10 | ASSUMED |
| **B10 Learning loops** | Evidence 15; Switches 25 | Loop 1 switch: keyword list + prompt-rule diffs from B9 (gated); Loop 2 persona (memory, scoreboard, suggestions → human); no training | reviews, outcomes → library/lexicon/prompt diffs | B8, B1, B3, B4 | ASSUMED |
| **B11 Data records** | Evidence 15; Robustness 20 | Append-only JSONL keyed by `decision_id`, on premises | all → records | B9, B10, slide | ASSUMED |

---

## 4. Blocks, one layer down

### B0 Seller context (input; peer-owned)

**Why.** PS04 §3.1: the persona starts from seller data. **How.** The peer data agent writes one JSON per seller at `data/contexts/<glid>_<as_of>.json`, schema `app/contracts/seller_context.schema.json`, key GLID. Sources: PS07, Global Context (5,000 sellers), Best-Time-to-Call, onboarding. Cold seller = no prior bot call (12.9%). Demo pool = Global Context sellers. We do not build or change it. **What.**

```json
{"glid":"…","as_of":"2026-10-09","profile":{…},"engagement":{…},
 "history":{"calls":[…],"outcomes":{…}},"timing":{"best_slot":"…"},
 "memory_facts":[{"family":"callback_when","value":"…","call_date":"…","source":"…"}],
 "observed_language":"…","speech_style":{…},"callee":{…},
 "field_sources":{…},"missing_fields":[…],"completeness":0.0}
```

**Status.** DOCUMENTED (team brief). OPEN: the schema file is not yet in `app/contracts/`; we freeze on the peer's version and test with fixtures until it lands. History must be as-of (no leakage) — v5 proved the seller-file `past_*` columns leak; we check that the peer rebuilds history from calls.

### B1 Traits & States library

**Why.** Fit 25 and Evidence 15: the persona must trace to the seller's data with stated evidence strength. **How.** A versioned JSON vocabulary. **Traits** are stable: language mix, terse, English-heavy, outcome history, business size. **States** change: rush, confusion, frustration, not-interested; gatekeeper / not-decision-maker optional. History sets odds, not identity: rush recurs 30.8% vs 20.8% base, terse 41.0% vs 17.8%, English-heavy 13.8% vs 4.3% (PROVEN, PS07). The agent can suggest a new trait or state; a human adds it. **What** (one entry):

```json
{"id":"state.rush","kind":"state","definition":"…",
 "computed_from":["speech_style.…","history.calls[].…"],"decay_half_life_days":30,
 "evidence":{"strength":"ps07_observational","note":"recurs 30.8% vs 20.8%"},
 "usual_levers":["pace","brevity","opening_move","switch_sensitivity.rush"]}
```

`usual_levers` is a hint to the agent, not a rule. **Status.** ASSUMED (content); evidence PROVEN for the listed recurrences.

### B2 Profile builder

**Why.** The agent should reason over a checkable, repeatable profile, not raw rows. FAQ Q6 needs confidence tied to missing data. **How.** Deterministic script that applies each B1 definition to `seller_context`. **What.**

```json
{"glid":"…","as_of":"…","library_version":"…",
 "traits":[{"id":"trait.terse","value":0.7,"evidence_strength":"…","from_fields":["…"]}],
 "states":[{"id":"state.rush","value":0.6,"last_seen":"…","decayed":0.4,"from_fields":["…"]}],
 "memory_facts":[…],"cold":false,"completeness":0.0,"missing_fields":[…]}
```

States also set per-seller switch sensitivity in B8. **Status.** ASSUMED.

### B3 VANI persona library (starting points)

**Why.** Distinctness 20, and FAQ Q1 (no fixed library: output is per seller). **How.** A few bundles (P0 = current VANI control, plus 3–4 archetypes such as crisp closer, patient guide, respectful advisor, warm re-engager) over shared dimensions: voice gender + style voice, pace, pitch, language, formality, warmth, empathy, brevity, accent (= voice language tag), and plan moves in native script. The agent **composes** from them per seller; the agent suggests new personas; a human adds them. No rule table. **What.**

```json
{"persona_id":"P1","version":"v1","dimensions":{"voice_id":"…","gender":"…","pace":1.25,
 "pitch":0.0,"language":"hi","formality":3,"warmth":3,"empathy":2,"brevity":4,"accent":"_hi_"},
 "plan_moves":{"opening":"…native…","objections":[…],"escalation":[…]},
 "evidence":{"tier":"informed_guess","note":"…"}}
```

**Status.** Levels ASSUMED. Pace 0.9 vs 1.3 is ≈ 21% faster and audible, repeatable (PROVEN). SDK ranges pace 0.85–2.0, pitch −0.5–0.5 (DOCUMENTED). Pitch audibility via OnStart not yet measured (OPEN test).

### B4 Composer (the agent)

**Why.** D1 (generator on sample files), D2 (spec with a reason per choice); Fit 25. Decision 3: the agent decides and composes. **How.** Step S3 of the skill on a frontier model. Read-only tools: seller profile, context fields, memory, both libraries, scoreboard, voice options, similar sellers (counts only). Three independent runs. Flat JSON output (nested failed 4/6, flat never failed: PROVEN). Spoken text in native script. Personal lines use placeholders (`{seller_name}`, `{city}`) that B6 fills, so names need not reach the model (ASSUMED; meets the data policy). **What.**

```json
{"run":1,"model":"…","dimensions":{"pace":{"value":1.2,"reason":"…","cites":["states.rush"],"confidence":0.6},…},
 "plan":{"opening":"…{seller_name}…","steps":[…],"personalisation":[…],"objections":[…],"escalation":[…]},
 "start_persona":["P1"],"suggest_new":{"flag":false,"reason":""}}
```

**Status.** Frontier model inside Claude Code in Daytona: ASSUMED (team lead sets access; peer Redash bot runs Claude Code login in Daytona, DOCUMENTED; OpenRouter blocked from Daytona, PROVEN).

### B5 Guard + settle

**Why.** FAQ Q5 (delivery, never facts/prices/compliance), FAQ Q6 (confidence ≤ completeness), Robustness 20, Evidence 15. **How.** Code only, enforced by hooks the agent cannot edit: schema; citation exists and matches; no digits / number words / prices / product claims in spoken text; native-script ratio; DNC; ID-number scrub verified; ≥ 2 runs pass and agree on the bucketed audible bundle {gender, pace band, pitch band, language}; code sets `evidence_tier` per setting; playability (voice exists for the language). Far from every library persona → `suggestion_row`. Failure → the agent re-runs once with the validator errors. If runs still disagree, the per-dimension majority of the agent's own runs is used and flagged. There is no fallback persona, and the call is placed only with a valid spec. **What.**

```json
{"decision_id":"…","glid":"…","snapshot_ref":"…","versions":{"skill":"…","libraries":"…","validators":"…"},
 "persona":{"<dimension>":{"value":…,"reason":"…","cites":[…],"confidence":0.0,"evidence_tier":"…"}},
 "plan":{…},"switch_sensitivity":{"rush":0.0,"confusion":0.0,…},
 "path":"composed|repaired","runs":[{"run":1,"passed":true,"fails":[]}],"propensity":null}
```

**Status.** ASSUMED. Number-word slips and Roman-script Hinglish seen earlier (PROVEN) are why these checks exist.

### B6 Compile Sarvam variables

**Why.** D3; Voice 20; the next block (Sarvam) decides the shape. **How.** Code template from `persona_decision` to the defined agent variables (§5), placeholders filled from context, spoken text in native script. **What.** `sarvam_call_vars` (§5). **Status.** Variables reaching OnStart: PROVEN. Template: ASSUMED.

### B7 Place call

**Why.** D3: live demo with a live human (FAQ Q3: a pre-scripted switch scores lower). **How.** Now: Sarvam SDK session with a team member speaking live (PROVEN path). Later: Instant Outbound API with `agent_variables` (DOCUMENTED; blocked until a Sarvam number is rented with KYC). **What.** `sarvam_call_vars` → `{"decision_id","channel":"sdk|outbound","session_id|attempt_id","started_at"}`. **Status.** SDK PROVEN; phone OPEN.

### B8 In-call switcher (live switches, inside Sarvam)

**Why.** Switches 25; D4 switch log; PS04 §3.5 and FAQ Q4.

**How.** Three parts, all inside the Sarvam agent; no external host in the call path:
1. **Prompt rules (same turn).** The base prompt names each signal and VANI's response:
   - rushed → one short sentence and a callback offer;
   - frustrated → apologise once and stop pitching;
   - confused → short comma-separated phrases, then check understanding;
   - interested → move to the meeting ask;
   - opt-out → apologise and end the call.

   This makes the reply change on the same turn with 0 added latency. Tested (O1, 3 runs): every signal 3/3–6/6, rushed 5/6 same turn, 0/27 false switches, same response across runs.
2. **Hardened keyword code tool `ReadSellerSignal`, called every seller turn.** It is the frozen decider of record.
   - It sets `seller_mode` + `persona_directive` and ends the call on opt-out (`set_end_conversation`).
   - It appends the D4 log row: signal, cue matched, change, source.
   - A first prompt line makes the LLM call it before every reply.
   - Tests (T4/O2h): called on 31/31 turns (was 30/31); 2/2 on language-switch turns (was 0/4); wrong mode 3/24, all from keyword-list gaps that Loop 1 fixes; switch_log valid JSON; about +0.4 s reply start over prompt-only.
3. **Patient endpointing** (console "Eagerness to respond" = Patient): restarted replies 2/31 → 0/31, double calls 1 → 0, at +0.13 s (T9).

**Language.** Sarvam's built-in detection switches language. The persona voice stays the same, because all v4 voices are multilingual.

**Voice, pace and pitch.** These are fixed per call through OnStart. Mid-call "slow down" is done through phrasing.

**Live Jev is deferred to a final re-test.**
- The warm relay adds +0.54 s per turn: reply start 2.52 s vs 1.98 s.
- Jev's own floor is about 450–500 ms. Network is 26 ms, and 1 call, 6 questions or 6 parallel calls make no difference.
- The filler did not play.
- A webhook or client push from the laptop is BLOCKED or DISPROVEN (T1/T2), and no live transcript leaves a phone call.

Evidence: `raw/research/2026-10-09-midcall-switch-tests.md`, `-jev-latency-floor.md`, `-midcall-switch-all-routes.md`.

**What.**

```json
// in:  {"decision_id","turn","utterance","language"}
// out: {"persona_directive":"…native…","seller_mode":"confused"}
// log: {"decision_id","turn","signal","cue","source":"keyword|transcript","change","ts"}
```

**Status.** PROVEN on scripted SDK sessions (2026-10-09). Not yet run on a real phone call (number rental).

### B9 Review

**Why.** Robustness 20, Evidence 15; feeds both loops. **How.** After each call a **frontier model** (Claude Code in Daytona, the same access as the B4 decider) reviews the transcript plus the switch log. It uses the **Fatal / Non-Fatal** format of the production VANI QA matrix (looping, dead air > 5 s, missed opportunity) and adds:
- per-turn signal labels;
- switch correctness: right signal, right turn;
- persona fit per dimension;
- the **reason** for each miss;
- a proposed diff to the keyword list or prompt rules.

A human confirms. Speed doesn't matter after the call, so the frontier model beats Jev here: it reads the whole call, explains its verdicts and proposes fixes. Jev (about $0.00002 per call, calibrated scores) is an optional cheap second labeller. **What.** `{"decision_id","overall":"pass|non_fatal|fatal","items":[{"param","verdict","turn","note"}],"switch_verdicts":[…],"fit":{"<dimension>":"ok|wrong"},"reviewer"}`. **Status.** Format DOCUMENTED (QA matrix); process ASSUMED.

### B10 Learning loops (between runs)

**Why.** Decision between-run: the system improves after each run; nothing learns during a call. **How.** No model training; only libraries, memory, lexicon and thresholds change.

| Loop | Learns from | Changes | Gate | Feeds |
|---|---|---|---|---|
| 1 Switch | B9 switch verdicts + proposed diffs | keyword list, prompt rules | frozen gold set must not regress; human approves | B8 |
| 2 Persona | outcomes (meeting booked), reviews, suggestions | seller memory; trait/state + persona scoreboard; new traits/states/personas | human approval | B1, B3, B4 tools |

**Status.** ASSUMED. PS07 calls bootstrap both loops (DOCUMENTED decision).

### B11 Data records (from day one)

**Why.** Evidence 15 and later learning need logged decisions. **How.** Append-only JSONL under git-ignored `data/`, keyed by `decision_id`. Records: snapshot ref (context path + hash); decision (versions, all agent runs, candidates, validator results, propensity); call (voice requested vs observed F0, latency, restarts, switch log); outcome; review; manifest (hashes of skill, libraries, lexicon, validators, base prompt, OnStart tool). **Status.** ASSUMED.

### Production later (one section only)

At scale, a nightly batch runs S1–S5 for sellers due a call, reuses unchanged decisions, and may gate the agent to sellers with free-text facts (~31% of due sellers carry one: PROVEN). Not built for the hackathon.

---

## 5. Sarvam interface (contract)

| Variable | Set by | Read by | Status |
|---|---|---|---|
| `persona_voice_id`, `persona_pace`, `persona_pitch`, `persona_opening` | B6 | OnStart tool (class named exactly `OnStart`) → `text_to_speech_config` + opening | PROVEN: female 269 Hz vs male 94 Hz; pace 0.9 vs 1.3 ≈ 21% faster |
| `initial_language_name` | B6 | Sarvam start | PROVEN |
| `decision_id` | B6 | B8 (tool body), records | Echo to tool OPEN (test) |
| `persona_directive` | B6 initial; B8 each turn | prompt | PROVEN (overwritten by tool response) |
| `seller_mode` | B8 | prompt sections | ASSUMED |
| `call_plan` | B6 only (never in tool response) | prompt | **OPEN**: proposed to replace "re-send plan every turn" (re-send: 20/20 PROVEN; plan only at start degraded 23/28) |
| `call_step` | prompt / B8 | loop guard | DOCUMENTED pattern (production buyer-side prompt) |

**Base prompt** holds facts, prices and compliance (FAQ Q5); persona sections, plan branches and loop guards are **variable-switched sections** with **hard per-field ask limits** that set `call_step = LOOP_DETECTED` (pattern DOCUMENTED in the production buyer-side VANI prompt). Whether sections re-render when a tool changes a variable mid-call: OPEN test. All spoken text in native script.

Rule: only variables **defined in the agent** reach the tool (undefined SDK variables were dropped: PROVEN).

---

## 6. Skill pattern and data policy

**Skill pattern** (from the peer Redash bot; DOCUMENTED by team brief): numbered steps in `SKILL.md`; each step is a deterministic script except S3; steps pass data only through files in `data/runs/<decision_id>/0N_*.json`; one output contract file (`07_status.json`); hooks the agent cannot edit block (a) writes to validators, contracts and libraries, and (b) S5 unless `04_persona_decision.json` has passed B5; pinned Claude Code CLI version.

**Data policy** (team decision): GST, PAN and other ID numbers never reach the frontier model (S1 scrub, tested with planted IDs: zero may survive). Names and address only when a task needs them (B4 uses placeholders; B6 fills them). Sarvam gets personalisation data. Key→seller map stays on IndiaMART infrastructure.

---

## 7. Requirements map

| PS04 deliverable / criterion | Blocks | Evidence shown |
|---|---|---|
| D1 Generator on sample seller files | B0 → B5 (skill S1–S3) | one command per GLID → `persona_decision` |
| D2 Spec per seller with reason per choice | B4, B5 | reason + cites + confidence + evidence tier per dimension |
| D3 Live demo, 2–3 contrasting sellers, ≥ 1 live switch | B6, B7, Sarvam, B8 | audible voice/pace contrast (PROVEN levers); 1 cold seller |
| D4 Switch log | B8, B11 | row per switch: signal, change, reason, source |
| D5 One slide | B11 + all | sample spec, evidence tiers, workflow (frontier LLM, Sarvam, data flow, signals, integration) |
| Fit 25 | B1, B2, B4 | traits/states from data, memory facts, cold path |
| Switches 25 | B8, B10 L1 | per-signal table (prompt rules + keyword tool); switch log; Loop 1 before/after |
| Distinctness 20 | B3, B4, B6 | different voice, pace, language and plan per seller |
| Natural voice 2+ languages 15 | B3, B6, Sarvam | per-call voice, native script, built-in language switch (6/6 PROVEN) |
| Evidence 15 | B1, B5, B9, B10, B11 | evidence tier; PS07 recurrence; PS07 personalisation trials 0 for 3 cited honestly |
| Deck: Business Impact 25 | slide | rush calls book 13.6% vs 26.0% (PROVEN, observational); projection labelled |
| Deck: Completeness 20 | all | D1–D5 end to end from one trigger |
| Deck: Robustness 20 | B5, B8, B9 | hooks, validators, repair re-run, Fatal/Non-Fatal review, real-data validation |
| Deck: Voice Experience 20 | Sarvam, B8 | latency (~2.1 s) and restart rate (~17%) measured and worked on |
| Deck: Demo & skills.md 15 | all | frozen demo, backup video, skills.md with numbers |

---

## 8. Open decisions and tests (architecture level)

| # | Item | Owner | Blocks |
|---|---|---|---|
| 1 | ~~Signal-server host~~ CLOSED 2026-10-09: switcher runs inside Sarvam (prompt rules + keyword tool); live Jev re-test is the last item | S | B8 |
| 2 | **`call_plan` variable**: not overwritten by tool response; plan followed as well as re-send | S | B6, B8 |
| 3 | **Phone number rental** (Sarvam/Vobiz KYC) for Instant Outbound; until then SDK demo | Team lead | B7 |
| 4 | **Organiser confirmations**: frontier decider vs "core agent must be Sarvam"; data policy vs "no customer data leaves the premises" | Team lead | B4, policy |
| 5 | `decision_id` echo to tool; do variable-switched sections re-render mid-call? | S | B6, B8 |
| 6 | Pitch audible via OnStart; can a during-call tool change TTS (would allow a real "slow down" switch)? | S | B3, B8 |
| 7 | Peer `seller_context` schema file landed and as-of clean | M with peer | B0 |

**Parked (not in the hackathon build).** Nightly batch and agent gate; exploration/holdout traffic and propensity sampling (fields logged only); weekly suggestion clustering (one recorded run); Tamil (no conversational voice); model training of any kind.

---

## 9. Devil's advocate (top 6 risks)

1. **The live switch may not sound like a persona change.** Voice and pace are fixed per call; PS04's own example is "slows down when confused". Mitigation: text-level change with a measured number (words per sentence before/after); test #6 might allow a real pace change.
2. **"Core agent must be Sarvam" vs frontier decider.** If organisers object, B4 runs Sarvam-105b with the same skill and guards (flat schema PROVEN, Roman-script slips PROVEN, so guards matter). The slide states which model produced each spec.
3. **The peer data agent is a dependency we do not control.** Late or changed schema blocks B2. Mitigation: freeze the contract early; fixtures; B2 tolerates missing fields (FAQ Q6).
4. **Composing adds variance; agreement is not correctness.** Mitigation: 2-of-3 bucketed agreement, citation checks, labelled fixtures; disagreement and repair rates measured, not assumed.
5. **Personalisation may not lift meetings.** Three PS07 script-personalisation trials went 0 for 3 (PROVEN). Claim fit and adaptation, not lift; lift needs holdout after the event.
6. **Live path fragility**: restarted replies (0/31 with Patient endpointing), ~2.0 s reply start, LLM must call the tool (31/31 with the hardened prompt line). Mitigation: prompt rules adapt even if a tool call is missed; health check before each demo call; freeze 12:00 D2; backup video 16:00 D2.

---

## 10. Work split (3 members) and the contracts that decouple them

| Member | Owns blocks | Done when |
|---|---|---|
| **S** (strong dev, live path) | B6, B7, Sarvam agent (OnStart, base prompt sections, variables), B8, switch log; open tests 1, 2, 5, 6 | Live call from `sarvam_call_vars` with ≥ 1 logged switch; voice requested = observed |
| **M** (second dev, decision path) | Skill shell + hooks, S1 scrub, B2, B4, B5, B11 records, `07_status.json` | `/vani-call <glid>` yields a valid `persona_decision` on fixtures and real contexts |
| **N** (non-tech) | B1 and B3 content (definitions, native-script persona cards), voice auditions, B9 labels + gold set, demo script, skills.md | Libraries v1 committed; ≥ 1 reviewed call; demo script |
| **Team lead** | Model access in Daytona, number rental, organiser confirmations, approvals in B10, freeze sign-off | Rulings filed in `raw/hackathon/` |

**Contract files** in `app/contracts/` (JSON Schema + one example each), frozen in hours 0–2 so each member can build against fixtures: `seller_context.schema.json` (peer), `trait_state_library.schema.json`, `seller_profile.schema.json`, `persona_library.schema.json`, `persona_decision.schema.json`, `sarvam_call_vars.schema.json`, `tool_turn.schema.json` (B8 in/out), `switch_log_row.schema.json`, `call_record.schema.json`, `review.schema.json`, `status.schema.json`. M and S meet only at `persona_decision` → `sarvam_call_vars`; N meets both only through the two library files and `review`.

---

## 11. Evidence index

| Claim | Tag | Source |
|---|---|---|
| OnStart class + defined variables set voice and opening; 269 vs 94 Hz | PROVEN | `raw/research/2026-10-09-onstart-code-tool-spike.md` |
| Pace 0.9 vs 1.3 ≈ 21% faster, repeatable; Instant Outbound accepts `agent_variables`; no telephony connection | PROVEN / DOCUMENTED | `raw/research/2026-10-09-onstart-pace-and-phone-check.md` |
| Per-language voice via `initial_language_name` | PROVEN | `raw/research/2026-10-09-per-language-voice-spike.md` |
| Jev native script 49/51, tricky 10/10, ~500 ms | PROVEN (36 hand-written sentences) | `raw/research/2026-10-09-jev-devanagari-spike.md` |
| Plan re-send 20/20 vs start-only 23/28; 0/8 prices; tool skipped on language turns 0/4; ~17% restarts | PROVEN (narrow) | `raw/research/2026-10-08-plan-stress-spike.md` |
| OpenRouter blocked from Daytona; Daytona preview lacks wildcard DNS/TLS | PROVEN | `raw/research/2026-10-07-spike-log.md` |
| Variable-switched prompt sections, ask limits, `call_step`; QA matrix Fatal/Non-Fatal | DOCUMENTED | `raw/hackathon/2026-10-09-new-data-files-buyer-side.md` |
| Recurrence, free-text shares, personalisation 0 for 3, rush 13.6% vs 26.0% | PROVEN | plan v5 §4, §5.4, §9.2, §12 and the sources it cites |
| Team decisions; data policy; one skill end to end | DOCUMENTED | `raw/hackathon/2026-10-0{8,9}-team-decision*.md` |
| Peer data agent sources, cold 12.9%, demo pool, peer skill pattern | DOCUMENTED (team brief 2026-10-09; not yet filed in `raw/`) | team lead |
| Thresholds, levels, placeholders, `call_plan`, review process | ASSUMED / OPEN | this document |

---

## Update 2026-10-09: open items closed (see raw/research/2026-10-09-open-items-closure.md)

| Open item | Result | Effect on architecture |
|---|---|---|
| Signal-server host | Daytona preview has no DNS; the sandbox was found stopped; the quick tunnel was dead. **Switcher moved inside Sarvam** as a during-call Python code tool (`ReadSellerSignal`): keyword list + policy, writes `seller_mode` / `persona_directive` / `switch_log` variables. PROVEN. | No external host in the call path. Jev becomes optional in-call (needs Sarvam egress 4.213.167.70 allowlisted) or runs offline in the review loop. |
| Separate `call_plan` variable | Plan only in `call_plan` (referenced in the instructions) + in-Sarvam switcher: 19/20 (effectively 20/20) on the hostile + Gujarati scenarios. PROVEN. | Plan re-sending every turn is dropped. |
| Pitch via OnStart | 239 / 267 / 286 Hz at −0.3 / 0 / +0.3. PROVEN. | Pitch is a usable persona dimension. |
| During-call voice/pace change | Not possible: the during-call tool context has no TTS config (SDK 1.1.1). DOCUMENTED. | Live "slow down when confused" = wording change only; say so in the demo. |
| Phone number | Parked (rent from Sarvam later). | — |
| Data agent schema | `app/contracts/seller_context.schema.json` v0.1 drafted and shared; the data agent owns it. | B1 contract fixed for parallel work. |
| Peer facts in raw/ | Filed: raw/hackathon/2026-10-09-peer-briefs.md. | Citations available. |

---

## What can change during the call, and fit with PS04 and the deck (2026-10-09)

**Before the call (OnStart, per seller): all PROVEN**
- voice (gender + style voice): female 269 Hz vs male 94 Hz;
- pace: 0.9 vs 1.3, about 21% faster;
- pitch: 239 / 267 / 286 Hz;
- starting language;
- opening line (spoken verbatim);
- call plan (`call_plan` variable).

**During the call:**

| Change | Possible? | How | Evidence |
|---|---|---|---|
| Wording, tone, warmth, empathy, formality | Yes | `persona_directive` set by the in-Sarvam switcher each turn | PROVEN: rushed → ≤ 12 words + callback; confused → simple + check; bot question → honest |
| Brevity / length of replies | Yes | directive ("ONE short sentence") | PROVEN (10–13 words when rushed) |
| Plan step / branch (callback, escalate, skip pitch) | Yes | directive + `call_plan` branches | PROVEN (plan followed 19/20) |
| Language | Yes | Sarvam built-in switch (and `change_language` in a code tool) | PROVEN 6/6 + 5/5 with the female persona voice. The voice stays the same; all v4 voices support 12 languages; the agent uses gender-consistent grammar |
| End the call / speak an exact line | Yes | code tool `set_end_conversation`, `message_to_user` | DOCUMENTED (SDK) |
| Voice (speaker) | **No** | fixed at call start; per-language voices are also fixed at start | DOCUMENTED (UI text, SDK) |
| Pace setting | **No** (setting fixed per call) | the during-call tool context has no TTS config | DOCUMENTED (SDK 1.1.1) |
| **Perceived pace (slow down)** | **Yes** | the confused directive makes the LLM write 3–4-word phrases with commas, and Bulbul speaks those 17–33% slower | PROVEN 2026-10-09 |
| Pitch | **No** | same as pace | DOCUMENTED (SDK 1.1.1) |

**Alignment check against the PS04 doc and deck slides 13–15:**

| Requirement (verbatim source) | Our design | Status |
|---|---|---|
| "Before each call, build the VANI persona that fits that seller from their seller data" (§2, slide 13) | agent composes per seller from the seller-context JSON + traits/states | Meets |
| Voice: "gender, accent, pitch and pace" (§3.2, slide 14) | set per call via OnStart: gender + style voice, accent = voice language tag, pitch, pace | Meets (all four PROVEN pre-call) |
| Language "Hinglish mix and formality"; tone "warmth and empathy" (§3.2) | composed dimensions → prompt sections + directive | Meets |
| "Reason for each choice … tied to the seller data" (§3.2, deliverable 2) | per-setting citation to seller-context fields, checked by validators | Meets (design) |
| Conversation plan "opening; personalisation; objection playbook; escalation rules; guardrails" (§3.3) | `persona_opening` + `call_plan` + base-prompt guardrails | Meets |
| Evidence from past calls, "be clear about how strong the evidence is" (§3.4) | evidence tier per setting; scoreboard; PS07 aggregates | Meets (design) |
| Live adaptation for frustration, confusion, interest, language switch, rush (§3.5, FAQ Q4) | in-Sarvam switcher + built-in language switch | Meets (all 5 detected; Jev native-script 49/51) |
| "slows down and simplifies when confused" (§3.5 example) | **simplifies: yes; slows down: wording only** (shorter sentences, one idea, check understanding); TTS pace cannot change mid-call | **Meets.** Slows via directive-driven phrasing (3 words/phrase, +17–33% delivery time, PROVEN); the TTS setting itself stays fixed |
| "shortens and gets to the point when rushed" (§3.5) | directive: ≤ 12 words + callback | Meets (PROVEN) |
| "switches language when the seller does" (§3.5) | built-in switch | Meets (PROVEN) |
| "Every switch is written to a switch log: the signal detected, the change made and the reason" (§3.5, deliverable 4) | `switch_log` variable written by the in-Sarvam tool (signal, from → to, utterance) | Meets: read back after the call via the Analytics API (`X-API-Key`) → `agent_variables.switch_log` (PROVEN) |
| Voice demo on Sarvam, 2–3 contrasting sellers, ≥ 1 live switch, natural in 2+ languages (§3.6, deliverable 3, FAQ Q3) | OnStart sets contrasting voice/pace/pitch/language; a live human speaker; Hindi + Gujarati shown | Meets on SDK/web now; the phone path waits for a rented number |
| Persona per seller, no fixed library (FAQ Q1) | library = starting points; agent composes per seller | Meets |
| Personas never change facts/pricing/compliance (FAQ Q5) | facts in the base prompt; no-price / no-number validators | Meets (PROVEN: no amounts in 0/16 price turns) |
| Missing fields → defaults, lower confidence (FAQ Q6) | missing_fields / completeness → confidence per setting | Meets (design) |
| One-slide presentation (deliverable 5) | from this architecture | To do |
| Deck rules: Sarvam Agent ID; all build in 2 days; no pre-built | the voice agent is Sarvam; the skill and code are written in the event | Meets / process |

**No gap remains vs PS04 §3 and the deck's PS04 slides.** "Slows down when confused" is met through phrasing (the TTS pace setting stays fixed per call). Still to do: the one-slide presentation and the phone path (rent a number).
