# VANI persona skill: design, step 1 (deterministic facts)

Date: 2026-10-10. Status: draft for your review. Language: ASD-STE100.
Pattern source: the peer's Redash sandbox (`redash-dashboard-automation/snapshot`) and their review (`raw/hackathon/2026-10-10-peer-skill-pattern-review.md`).

## 1. Layers of the skill (the plan)

| Layer | File | Content | Always loaded? |
|---|---|---|---|
| 1 | `CLAUDE.md` (the "agent.md") | Short. It points to the skill. It gives the rules that the agent must never miss. | Yes |
| 2 | `skill/vani-persona/SKILL.md` | The need, the role, the input, the output, and the numbered steps. | When the skill loads |
| 3 | `skill/vani-persona/references/*.md` | Judgement guidance: hook guide, persona library, objection playbook, voice and tone guide, Sarvam template. | On demand, at a named step |
| 4 | `skill/vani-persona/scripts/*.py` | Deterministic tools: `facts.py`, `peer_stat.py`, `showcase_lead.py`, `validate_persona.py`, `write_sarvam_vars.py`. | The agent runs them |
| 5 | `data/contexts/<glid>/` | The seller folder: INDEX.md, core.md, topic files, calls/, context.json. | INDEX.md and core.md always; the others on demand |
| 6 | Gates | A stop gate and a pre-gate. They make sure that the required steps happened. | Not visible to the agent |

**This document decides step 1 only:** which facts a script calculates before the agent starts. The agent then uses its time on judgement, not on arithmetic.

## 2. The principle

- **A script calculates a fact** if the fact has one correct answer from the data. Examples: credits lapsed, VANI calls in 7 days, the turnover band, whether a hook's precondition is true.
- **The agent decides** a choice that needs judgement. Examples: which hook to use first, the tone, the opening line, the call plan.
- Each calculated fact has: `value`, `evidence` (field id + value + date + source), and `confidence`.
- The script **does not select** the hook. It tells the agent which hooks are **eligible**, and why. The agent selects.

The script is `scripts/facts.py`. It reads `context.json` and writes `facts.json` in the seller folder. It also adds a short **"Facts"** block at the top of INDEX.md.

## 3. Traits (stable): what the script calculates

| Trait | Calculated value | Fields used | Rule (proposed, can be tuned) |
|---|---|---|---|
| `division` | NSD / CSD / TMW / KCD / other | H02.vertical_name | Text match on the vertical name |
| `plan` | free / paid + plan name | C05.paid_free, byr_custtype | Copy |
| `years_on_im` | number | C04.member_since | Today minus member_since |
| `scale_tier` | small / mid / large | C02.annual_turnover, E10 seller AOV, E10 category AOV | small: below 40 L; mid: 40 L–5 Cr; large: above 5 Cr. Move one step up if seller AOV is higher than 2 × category AOV. |
| `seller_type` | manufacturer / trader / service / mixed | C01.primary_biz_type, C03 | Text match |
| `seller_gender` | M / F / unknown + source + confidence | A07 recorded; otherwise the first name in A03 | Recorded value: confidence 1.0. Name list: 0.7. Otherwise: unknown. |
| `language` | main language + Hinglish/English share | B03, B04, call transcripts | The language most seen. If no data: the state default language (B01). |
| `im_profile_strength` | weak / ok / strong | D06.scorecard.cqs, photo and price gaps, C08 sections, C06 flags | weak: CQS below 40, or more than 20% of products without a photo or a price. strong: CQS 70 or more and no gaps. |
| `online_presence` | own website yes/no; other platforms named | users_detail website field; platform names in calls and WhatsApp text | Pattern match on JustDial, TradeIndia, Amazon and similar names |
| `call_behaviour` | answer rate, busy rate, who answers | G00 outcome counts, F03, A06 | busy_rate = "Call Later / Busy" calls ÷ answered calls |
| `service_history` | complaints, not satisfied, executive meetings, past grievance themes | I01, H01, H03, G00 objections | Counts. Themes come from the objection categories. |

## 4. States (change with time): what the script calculates

| State | Calculated value | Fields used | Rule (proposed) |
|---|---|---|---|
| `bl_usage` | active / low_use / unused / lapsed / none + numbers | E05 (allotted, lapsed, balance, last_cons_date), E06, E04 | lapsed: lapsed > 0. unused: allotted > 0 and no consumption in 30 d. low_use: consumed < 30% of allotted. none: no credits. |
| `bl_value` | below / same / above category + numbers | E10 seller AOV vs category AOV | below: seller median < 0.7 × category median. above: > 1.3 ×. |
| `bl_quality_issue` | yes/no + top reasons | E07.scorecard (blni_loc, blni_spec, blni_wrng_product…), G00 "leads not good" | yes: rejected leads ≥ 3, or a call says that the leads are bad |
| `enquiry_flow` | rising / flat / falling + numbers | E01.topbar (last week, last month, last quarter) | falling: last month < 0.7 × (last quarter ÷ 3) |
| `reply_gap` | replied share + speed | E03 (replies, read time) | Share of enquiries with a reply |
| `pns_flow` | calls, answered share | F01.scorecard / topbar | Copy, plus answered % |
| `call_mood` | rushed / irate / confused / asked_bot counts, with the date of the last call | G00 signals | Weight each call by age (half-life 30 d) |
| `intent` | problem / wants_upgrade / not_interested / unknown | G00 outcomes and objections, J02 chatbot intents | Last 90 days. "Not Interested" outcome → not_interested. Upgrade or plan words → wants_upgrade. Complaint words → problem. |
| `recent_exec_contact` | days since an executive met or called | H01.last, H03, G00 exec contact | Copy and calculate the days |
| `call_fatigue` | VANI calls in 7 d / 30 d; asked to stop calling | G00 | Count. "stop calling" / "don't call" in the summaries → asked_stop = yes. |
| `open_grievance` | yes/no + theme | I01 (open complaints = count − closed), G00 grievance signal | yes: open complaint, or a grievance signal in the last 60 d |
| `category_demand` | local buy leads, bulk share, price band | E08 counts, E09 | Copy |
| `peer_position` | rung + seller vs peer median | E11 | First allowed rung. ahead / level / behind against the peer median. |
| `showcase_lead` | best lead + backup | E12 | First two rows by fit score |

## 5. Hooks: the script calculates eligibility, the agent selects

For each hook, the script writes `eligible: true/false`, `because` (the facts and their ids), and `blockers` (the reasons not to use it now). It does not rank the hooks for the agent.

| Hook | Eligible when (script rule) | Blockers (script) |
|---|---|---|
| `profile_gap` | im_profile_strength = weak | none |
| `money_lead` | showcase_lead has an order value | none |
| `category_demand` | category_demand has local buy leads > 0 | none |
| `unused_credits` | bl_usage = lapsed / unused / low_use | open_grievance about billing; call_fatigue.asked_stop |
| `lead_quality_fix` | bl_quality_issue = yes | none |
| `enquiry_drop` | enquiry_flow = falling | none |
| `peer_usage` | peer_position has an allowed rung | the seller is "ahead" (then only the line "you are ahead of sellers your size" is permitted) |
| `resolve_grievance` | open_grievance = yes | none |

**Call-level guard facts (script):** `do_not_call` (DNC flag), `asked_stop_calling`, `met_exec_in_last_3_days`, `vani_calls_last_7d ≥ 3`. If one of these is true, the skill tells the agent first. The agent can then decide not to pitch, or to only apologise and close.

## 5a. The four call-level guards (explained)

A guard is a fact that can make a pitch wrong for this call. The script sets each guard to true or false, with its evidence. If a guard is true, the agent must deal with it before it chooses a hook.

| Guard | What it means | Where the data comes from | What the agent must do |
|---|---|---|---|
| 1. `do_not_call` | The seller asked IndiaMART not to call (the DNC flag). | ps07 seller file `do_not_call_requested`; a "stop calling" request in calls | Stop. The skill writes status "do_not_call", and no persona and no Sarvam variables. This is a compliance rule, not a choice. |
| 2. `asked_stop_calling` | On a past VANI call, the seller said "don't call" or "update your system", but no DNC flag is set. | Summaries and quotes in calls/ | Default: no pitch. The persona is only "apologise, confirm, close". The agent can override only with a newer call where the seller agreed to be called. |
| 3. `met_exec_recently` | An IndiaMART executive met or called the seller in the last 3 days. | H01.last, H03, executive contact in calls/ | Do not ask for a new meeting. Example: seller 93557756 met an executive, and then VANI called 7 times in one week. The agent can change the objective to "follow up on the meeting" or decide not to call. |
| 4. `call_fatigue` | VANI called the seller 3 or more times in the last 7 days. | Call dates in calls/ | Make the call short and acknowledge the earlier calls. Never repeat the last pitch. The agent can recommend "skip this call". |

## 5b. The agent's choice is gated (it must probe; it cannot just pick)

Each hook has `probe_files` (written by the script). Before the agent decides about a hook, it must read those files. A gate checks the following. If a check fails, the turn does not end and the agent gets one message with all the failures.

1. **Every eligible hook has a decision** in Part B: primary, backup or rejected, with a reason. A "rejected" hook also needs a reason.
2. **The probe happened.** For each decision, the files in `probe_files` appear in the read log. A PostToolUse hook records every file that the agent reads. The agent cannot write this log.
3. **The citations are real.** Each cite (e.g. `buyleads.md#E05`, `calls/C01#C01.T4`) exists in the folder.
4. **There is enough evidence.** The primary hook has at least 3 cites, and these come from at least 2 different files. One cite must come from calls/ if the seller had a VANI call in the last 90 days.
5. **Counter-evidence is considered.** The primary hook has a `counter_evidence` text that is not empty.
6. **The guards are acknowledged.** Each true guard has an agent note before any hook decision.
7. **The traits and states that the agent uses are reviewed.** A trait or a state that the persona cites must have a Part B with `relevance` and `implication_for_persona`.

The gate checks that the agent probed and cited. It does not check that the choice is "right": that is the agent's judgement.

## 5c. Where the three formats are stored

In the skill: `.claude/skills/vani-persona/references/formats/`:
- `trait.json`: Part A (script: value, detail, evidence, confidence, rule, missing inputs) and Part B (agent: accepted or corrected, probe, note, relevance, implication for the persona).
- `state.json`: the same, plus `as_of`, `half_life_days` and `weight`, and the agent's `still_true_now`.
- `hook.json`: Part A (script: eligible, because, blockers, division fit, probe_files, facts for the claim) and Part B (agent: decision, reason, probe, counter-evidence, claim draft, claim fact ids).

`scripts/facts.py` writes Part A of every trait, state and hook into `facts.json`. The agent fills Part B. The next design step is how Part B becomes the persona.

## 6. What the agent decides (judgement)

- Which eligible hook to use first, and the backup hook.
- The persona: voice gender, voice, pace, pitch, language mix, formality, warmth, sophistication.
- The opening line, the call plan, and the order of the objections.
- When the facts disagree (example: the seller is "ahead" of peers but has lapsed credits), the agent decides which fact matters.
- Each decision must cite the fact ids (K, A03, E11, CL-1, C03.T5) as evidence.

## 7. Questions for you

1. Do you agree with the split: the script calculates the facts and the hook eligibility; the agent selects?
2. Do you agree with the proposed thresholds (scale tier, profile strength, bl_usage, enquiry trend)? They are a start. We tune them with data later.
3. Are the call-level guards correct? See 5a.
4. After you agree, the next step is CLAUDE.md (the rules that must never be missed). Then SKILL.md.

## 9. The hierarchy and the learning loops (draft, 2026-10-10)

### 9.1 Two scoreboards, not one
- **Scoreboard A: persona bundle.** It holds the tone, pace, formality, warmth, sophistication, opening style and hook style. The arms are the personas in the library (about 6).
- **Scoreboard B: voice gender.** The arms are female and male. It is separate because the evidence says that the best voice depends on the callee's gender, the city tier and the tension, not on the category.

Each scoreboard has its own hierarchy. This keeps each hierarchy small.

### 9.2 Levels of scoreboard A (persona) - revised 2026-10-10 after user review
| Level | Key | Example | Why |
|---|---|---|---|
| L0 | all sellers | — | The base |
| L1 | division (NSD / CSD; TMW and KCD as CSD until decided) | NSD | It changes the objective, the hook set and the starting point |
| L2 | + turnover band (0–40 L / 40 L–1.5 Cr / 1.5–5 Cr / 5 Cr+) | NSD, 40 L–1.5 Cr | Turnover sets the sophistication (formality, numbers vs simple words) |
| L3 | + AOV tier (seller AOV, else category AOV: low / mid / high, by category percentiles) | NSD, 40 L–1.5 Cr, high AOV | AOV is the price tier. The field evidence shows that the price tier changes which voice and style work |
| L4 | + zone (North / West / South / East / Central) | … North | The parent of the state, so that small states can use the zone's data |
| L5 | + state | … Uttar Pradesh | The user wants state-level detail. PS07 shows region effects |
| L6 | + category group | … textiles | The most specific level, with the least data |

Each level starts from the level above it (partial pooling). A state with few calls uses its zone's score. A zone with few calls uses the score of its AOV tier, and so on up the hierarchy.

**Division in the facts, not only in the hierarchy.** `facts.py` writes `trait.division` into the INDEX key facts, together with the division's objective and its eligible hooks. The agent does not need to read other sections to know the division. The skill has **separate references for each division** (`references/division_nsd.md`, `references/division_csd.md`: objective, hook guide, objection playbook, pitch examples). The **steps in SKILL.md are the same** for both divisions; only the reference that the agent opens changes.

### 9.3 Levels of scoreboard B (voice gender)
| Level | Key |
|---|---|
| V0 | all sellers (start: female) |
| V1 | seller gender (recorded or guessed, with confidence) |
| V2 | + city tier (metro / tier-2 / small town or rural) |
| V2b | + state (Hindi belt or not) |
| V3 | + call tension (calm / tense, from the states) |

### 9.4 What each cell stores
`{"path": [...], "arm": "P3", "calls": 42, "meetings": 7, "prior_mean": 0.12, "prior_weight": 20, "score_mean": ..., "score_low": ..., "score_high": ..., "updated": "..."}`

### 9.5 How learning happens (after each call)
1. The skill logs the decision: the segment path, the top 2 with their probabilities, the chosen persona, the amendments, the voice, the hook, and the guards.
2. The call result arrives: meeting fixed (yes/no), and later "meeting held" when the executive confirms it.
3. The script adds the result to the cell at every level of the path.
4. The score of a cell = its own results + the score of the level above, weighted as `prior_weight` calls (Beta with partial pooling). With few calls, the level above decides. With many calls, the cell decides.
5. The next time, Thompson sampling draws from each persona's score. The highest draw is the first choice. A close second gets calls sometimes.
6. The script scores each persona against the default persona (uplift), not only on raw meetings.

### 9.6 What learning changes, and what it does not
| Item | Changes automatically? | Who changes it |
|---|---|---|
| Scoreboard numbers (A and B) | Yes, after each call | Script |
| The persona definitions (the library) | No | The agent suggests; a human approves a new version |
| The amendments that the agent makes | The script counts which amendments go with good results. If one wins many times, it is suggested as a library change | Human approval |
| The Sarvam prompt template | No. A persona fills **variables** in a fixed template. A new persona needs no prompt edit | Only when a human approves a new template version |
| Mid-call switch (Loop 1): keyword list, switch directive text, sensitivity | Not automatically | See 9.7 |

### 9.7 Loop 1 (mid-call switching) learning
1. After each call, the reviewer (frontier model + human) labels each seller turn with the correct signal and compares it with the switch log.
2. The result: missed signals (no switch) and false switches.
3. The script proposes changes: new keywords, removed keywords, and changed switch directive text in the prompt-rules section.
4. A gold set of labelled turns tests each proposal. The change must not make the gold-set score worse.
5. A human approves. The switch tool and the prompt-rules section get a new version number.
6. Per-seller sensitivity comes from the states: a seller who is often rushed gets a faster "rushed" switch. This needs no learning step.

So Loop 1 does change the prompt, but only the prompt-rules section, only in a new version, and only after the gold-set test and human approval. Loop 2 changes only the scoreboard numbers automatically. The library and the template change only with human approval.
