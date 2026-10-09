# Traits and states library: draft v0 (for your review)

Date: 2026-10-10. Status: draft. You make the decision.
Language: ASD-STE100 (Simplified Technical English).

## 1. Purpose

This library gives the persona agent a fixed set of seller facts.
The facts come from the seller context file.
A script (block B2) calculates the facts. The agent (block B4) reads them.

There are two types of facts:
- A **trait** is stable. It changes in months. It tells "who the seller is".
- A **state** changes in days or weeks. It tells "what is true for the seller now".

Each state has a date. The weight of a state decreases with time.

## 2. Check against your whiteboard

| Board item | What you wrote | Library item | Status |
|---|---|---|---|
| 1 | Online presence | `trait.online_presence` | Covered |
| 2 | Name / City / Gender | `trait.identity`, `trait.seller_gender` | Covered |
| 3 | Product | `trait.product_focus` | Covered |
| 4 | Call pattern: problem / wants to upgrade | `state.intent` | Covered |
| 4 | Call pattern: busy, irate | `state.call_mood` | Covered |
| 4 | Call pattern: M/F | `trait.seller_gender` | **Check.** I think "M/F" means the seller gender. Tell me if it means a different thing. |
| 5 | Past / available business: BL, AoV | `state.bl_usage`, `trait.business_scale` | Covered |
| 5 | Past / available business: Enq | `state.enquiry_flow` | Covered |
| 5 | Past / available business: PNS | `state.pns_flow` | Covered |
| 6 | BL: live / expired | `state.bl_usage` (credits active, unused or lapsed) | **Check.** I think "live / expired" means the seller's BL credits. It can also mean live buy leads in the category. Tell me which. |
| 6 | BL: high value | `state.bl_value` (new) | Added now. It was missing in the first draft. |
| 7 | Similar seller: local, turnover below / above 1.5 Cr | `state.peer_position`, `trait.business_scale.scale_tier` | Covered. The peer data is in research. |
| 8 | Past service experience | `trait.service_history`, `state.open_grievance` | Covered |

**Items that I added. They are not on your whiteboard.** Remove them if you do not want them:
- `trait.language_style`: the seller's language mix. PS04 asks for language fit.
- `trait.account_relationship`: the division (NSD / CSD / TMW / KCD) and the plan. The pitch type comes from this.
- `trait.call_behaviour`: the answer rate, the busy rate, and the person who answers.
- `state.recent_exec_contact`: an executive met the seller recently. Example: seller 93557756 met an executive. After that, VANI called the seller 7 times in one week.
- `state.call_fatigue`: the number of VANI calls in the last 7 and 30 days, and a "stop calling" request.
- `state.category_demand_now`: the number of local buy leads, and the price range in the category.

## 3. Format of one library entry

Each trait and each state has one entry with these keys.

```json
{
  "id": "state.bl_usage",
  "kind": "trait | state",
  "board_item": 5,
  "label": "Buy-lead credits not used",
  "definition": "The seller got credits in the last 90 days and used less than 30% of them, or the credits lapsed.",
  "computed_from": ["E05.bl_credits_alctd", "E05.bl_credit_lapsed", "E06.cons_*", "E04.gc_bought"],
  "values": {"type": "enum", "allowed": ["active", "low_use", "unused", "lapsed", "none"]},
  "confidence_rule": "High if the API data is less than 7 days old. Low if the data is from files only.",
  "decay_half_life_days": 30,
  "evidence": {"strength": "data | ps07_observational | assumed", "note": "..."},
  "applies_to_division": ["CSD", "TMW", "KCD"],
  "feeds": ["hook.unused_credits", "persona.formality", "plan.objective_line"],
  "version": "v0"
}
```

Meaning of the keys:
- `id`: the name of the item.
- `kind`: "trait" or "state".
- `board_item`: the number on your whiteboard.
- `computed_from`: the fields in the seller context that the script uses.
- `values`: the permitted values.
- `confidence_rule`: how the script sets the confidence.
- `decay_half_life_days`: for states only. After this number of days, the weight is half.
- `applies_to_division`: the divisions that use this item.
- `feeds`: the parts of the persona and the hooks that use this item.

## 4. Format of the seller profile (the script output)

The script makes one profile for each seller before each call.

```json
{
  "glid": "...", "as_of": "...", "library_version": "v0", "division": "NSD | CSD | TMW | KCD",
  "traits": [{"id": "trait.business_scale", "value": "mid", "confidence": 0.8,
              "evidence": [{"field": "C02.annual_turnover", "value": "40 L - 1.5 Cr", "source": "ps07_seller_file", "date": "..."}]}],
  "states": [{"id": "state.bl_usage", "value": "lapsed", "as_of": "...", "weight": 0.9,
              "evidence": [{"field": "E05.bl_credit_lapsed", "value": 200, "source": "api:byr_supply", "date": "..."}]}],
  "missing": ["trait.seller_gender"],
  "completeness": 0.82
}
```

Each value has its evidence: the field, the value, the source and the date.
The agent must give this evidence as the reason for each persona choice.

## 5. Traits (stable)

| id | Board | Value keys | Data source |
|---|---|---|---|
| `trait.online_presence` | 1 | `own_website`, `social_links`, `other_platforms[]`, `im_profile_strength` (weak / ok / strong) | Website and social fields (users_detail). Other platforms that the seller named in old calls or WhatsApp (G00, J). CQS, photos, prices (D06). Profile sections (C08). |
| `trait.identity` | 2 | `name`, `city`, `district`, `state`, `region_language` | A03, B01. The name goes to Sarvam only for the greeting. |
| `trait.seller_gender` | 2, 4 | `value` (M / F / unknown), `source` (recorded / name / voice), `confidence` | A07 (recorded). If A07 is empty: a guess from the first name or the voice. Use it only to select VANI's voice. |
| `trait.product_focus` | 3 | `top_mcats[]`, `seller_type` (manufacturer / trader / service), `product_count`, `price_band` | D01–D05, C03, E09 |
| `trait.business_scale` | 5, 7 | `turnover_band`, `seller_aov`, `category_aov`, `scale_tier` (small / mid / large) | C02, E10, C07 (employees), C04 (years) |
| `trait.language_style` | added | `languages[]`, `hinglish_share`, `english_share`, `words_per_turn` | B03, B04, transcripts in G00 |
| `trait.account_relationship` | added | `division`, `plan` (free / paid / type), `member_since`, `years_on_im` | H02 vertical_name, C05, C04 |
| `trait.call_behaviour` | added | `answer_rate`, `avg_call_sec`, `busy_rate`, `who_picks_up` (DM / family / staff) | G00 counts, F03, A06 |
| `trait.service_history` | 8 | `complaints`, `not_satisfied`, `rating`, `exec_meetings`, `past_grievance_themes[]` | I01–I04, H01, H03, objections and summaries in G00 |

## 6. States (change with time)

| id | Board | Value keys | Data source | Half-life |
|---|---|---|---|---|
| `state.bl_usage` | 5, 6 | `credits_balance`, `lapsed`, `bought_90d`, `consumed_pct`, `speed`; summary value: active / low_use / unused / lapsed / none | E04–E06 | 30 d |
| `state.bl_value` | 6 (new) | `seller_aov`, `category_aov`, `high_value_share` (share of bought leads above the category top quarter), `position` (below / same / above the category) | E10 | 30 d |
| `state.bl_quality_issue` | 4, 6 | `top_ni_reasons[]`, `rejected_share` | E07, "leads not good" in G00 | 30 d |
| `state.enquiry_flow` | 5 | `enq_30d`, `enq_90d_avg`, `trend` (rising / flat / falling), `reply_rate` | E01–E03 | 30 d |
| `state.pns_flow` | 5 | `pns_30d`, `answered_pct`, `avg_talk_sec` | F01–F02 | 30 d |
| `state.call_mood` | 4 | `rushed`, `irate`, `confused`, `asked_bot`, each with the date of the last call | Signals in G00 | 30 d |
| `state.intent` | 4 | `problem` / `wants_upgrade` / `not_interested` / `unknown` | Summaries and objections in G00. Chatbot intents (J02). | 45 d |
| `state.recent_exec_contact` | added | `met_exec_days_ago`, `exec_calls_30d` | H01, H03, executive contact in G00 | 14 d |
| `state.call_fatigue` | added | `vani_calls_7d`, `vani_calls_30d`, `asked_stop_calling` | G00 | 7 d |
| `state.open_grievance` | 8 | `latest_complaint`, `theme`, `resolved` (yes / no / unknown) | I01, grievance signal in G00 | 60 d |
| `state.category_demand_now` | added | `local_bl`, `hyperlocal_bl`, `bulk_share`, `price_band` | E08, E09 | 30 d |
| `state.peer_position` | 7 | `peer_cell` (MCAT, turnover band, AOV band, area), `peer_count`, `peer_median_bl_bought`, `seller_vs_peers` | Peer statistic (in research) | 30 d |

## 7. Hooks: the agent selects the hook for each seller

A hook is the reason that VANI gives for the meeting.
For one seller, many hooks can be true at the same time.
The agent selects the best one or two hooks for that seller.
The other hooks stay as backups for objections.

A hook has rules. The agent can use a hook only when its data is present and true.

```json
{
  "id": "hook.unused_credits",
  "division": ["CSD", "TMW", "KCD"],
  "requires": {"state.bl_usage": ["unused", "lapsed", "low_use"]},
  "claim_template": "Aapke {lapsed} credits lapse ho gaye ...",
  "facts_from": ["E05", "E06"],
  "avoid_if": ["state.open_grievance = billing", "state.call_fatigue.asked_stop_calling"],
  "meeting_reason": "show you how to select and use leads"
}
```

| Hook | Division | Rule (the hook needs this) |
|---|---|---|
| `hook.profile_gap` | NSD | `trait.online_presence.im_profile_strength` = weak |
| `hook.category_demand` | NSD, CSD | `state.category_demand_now` is high |
| `hook.unused_credits` | CSD | `state.bl_usage` = unused, lapsed or low_use |
| `hook.lead_quality_fix` | CSD | `state.bl_quality_issue` is present |
| `hook.enquiry_drop` | CSD | `state.enquiry_flow.trend` = falling |
| `hook.peer_usage` | NSD, CSD | `state.peer_position` has enough peers **of the same size** |
| `hook.resolve_grievance` | CSD | `state.open_grievance` is not resolved. VANI first accepts the problem. Then VANI asks for the meeting to fix it. |

How the agent selects:
1. Find the hooks whose rules are true.
2. Give each hook a rank. Use the fit to the division and the intent, the strength of the evidence, and the age of the data.
3. Select one primary hook and one backup hook.
4. A script then checks the selection. The hook rules must be true. The facts in the hook must be in `verified_facts`.

Example: a CSD seller has lapsed credits and an open complaint. The agent selects `hook.resolve_grievance` first, not `hook.unused_credits`.

## 8. Questions for you

1. Is this set of traits and states correct? Tell me the items to merge, remove or add.
2. Board item 4, "M/F": is it the seller gender, or a different thing?
3. Board item 6, "live / expired": is it the seller's BL credits, or the live buy leads in the category?
4. For `scale_tier`, do we use your board split (turnover below or above 1.5 Cr) together with AOV?
5. Do TMW and KCD sellers get the CSD hooks?
6. Do the hooks go in the VANI persona library, or in a third library?
