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

## 6. What the agent decides (judgement)

- Which eligible hook to use first, and the backup hook.
- The persona: voice gender, voice, pace, pitch, language mix, formality, warmth, sophistication.
- The opening line, the call plan, and the order of the objections.
- When the facts disagree (example: the seller is "ahead" of peers but has lapsed credits), the agent decides which fact matters.
- Each decision must cite the fact ids (K, A03, E11, CL-1, C03.T5) as evidence.

## 7. Questions for you

1. Do you agree with the split: the script calculates the facts and the hook eligibility; the agent selects?
2. Do you agree with the proposed thresholds (scale tier, profile strength, bl_usage, enquiry trend)? They are a start. We tune them with data later.
3. Are the call-level guards correct (DNC, "stop calling", executive met in the last 3 days, 3 or more VANI calls in 7 days)?
4. After you agree, the next step is CLAUDE.md (the rules that must never be missed). Then SKILL.md.
