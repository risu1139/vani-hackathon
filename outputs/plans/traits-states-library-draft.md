# Traits & states library: DRAFT v0 for decision (2026-10-10)

Built from the user's whiteboard (8 items) and the data we have (seller context A–K, E09/E10, G00). Status: **for the user to decide**. Nothing here is final.

- **Traits** are stable for months. They describe *who the seller is*.
- **States** change from week to week. They describe *where the seller is now*. Each state carries a date and decays.

The deterministic builder (B2) computes both from the seller context. The persona agent (B4) reads them.

## 1. Library entry (one per trait / state)

```json
{
  "id": "state.bl_unused",
  "kind": "trait | state",
  "board_item": 5,
  "label": "Buy-lead credits not being used",
  "definition": "Credits allotted in the last 90 d but < 30% consumed, or credits lapsed",
  "computed_from": ["E05.bl_credits_alctd", "E05.bl_credit_lapsed", "E06.cons_*", "E04.gc_bought"],
  "values": {"type": "enum", "allowed": ["none", "low_use", "unused", "lapsed"]},
  "confidence_rule": "high if E05 from API in last 7 d; low if file-only or as_of_safe=false",
  "decay_half_life_days": 30,
  "evidence": {"strength": "data | ps07_observational | assumed", "note": "…"},
  "applies_to_division": ["CSD", "TMW", "KCD"],
  "feeds": ["hook.unused_credits", "persona.formality", "plan.objective_line"],
  "version": "v0"
}
```

## 2. Seller profile (B2 output, one per seller per call)

```json
{
  "glid": "…", "as_of": "…", "library_version": "v0", "division": "NSD | CSD | TMW | KCD",
  "traits": [{"id": "trait.business_scale", "value": "mid", "confidence": 0.8,
              "evidence": [{"field": "C02.annual_turnover", "value": "40 L - 1.5 Cr", "source": "ps07_seller_file", "date": "…"}]}],
  "states": [{"id": "state.bl_unused", "value": "lapsed", "as_of": "…", "weight": 0.9,
              "evidence": [{"field": "E05.bl_credit_lapsed", "value": 200, "source": "api:byr_supply", "date": "…"}]}],
  "missing": ["trait.seller_gender"], "completeness": 0.82
}
```

## 3. TRAITS (stable)

| id | Board | Value | Computed from |
|---|---|---|---|
| `trait.online_presence` | 1 | `{own_website, social, other_platforms[], im_profile_strength: weak/ok/strong}` | users_detail URLs; other-platform mentions in calls/WhatsApp (G00, J); CQS + photos/prices (D06) + profile sections (C08) |
| `trait.identity` | 2 | `{name, city, district, state, region_language}` | A03, B01 (name is passed to Sarvam only for the greeting) |
| `trait.seller_gender` | 2 | `{value: M/F/unknown, source: recorded/name/voice, confidence}` | A07 recorded; else name/voice guess (decision 2026-10-10) |
| `trait.product_focus` | 3 | `{top_mcats[], seller_type: manufacturer/trader/service, product_count, price_band}` | D01–D05, C03, E09 |
| `trait.business_scale` | 5, 7 | `{turnover_band, seller_aov, category_aov, scale_tier: small/mid/large}` | C02, E10, C07 (employees), C04 (vintage) |
| `trait.language_style` | 2, 4 | `{languages[], hinglish_share, english_share, words_per_turn}` | B03, B04, G00 transcripts |
| `trait.account_relationship` | — | `{division, plan: free/paid/type, member_since, years_on_im}` | H02 vertical_name, C05, C04 |
| `trait.call_behaviour` | 4 | `{answer_rate, avg_call_sec, busy_rate, who_picks_up: DM/family/staff}` | G00 counts, F03, A06 |
| `trait.service_history` | 8 | `{complaints, not_satisfied, rating, exec_meetings, past_grievance_themes[]}` | I01–I04, H01/H03, G00 objections/summaries |

## 4. STATES (changing, dated, decay)

| id | Board | Value | Computed from | Half-life |
|---|---|---|---|---|
| `state.bl_usage` | 5, 6 | `{credits_balance, lapsed, bought_90d, consumed_pct, speed}` → `none/low_use/unused/lapsed/active` | E04–E06 | 30 d |
| `state.bl_quality_issue` | 4, 6 | top not-interested reasons, share rejected | E07, G00 "leads irrelevant" | 30 d |
| `state.enquiry_flow` | 5 | `{enq_30d, enq_90d_avg, trend: rising/flat/falling, reply_rate}` | E01–E03 | 30 d |
| `state.pns_flow` | 5 | `{pns_30d, answered_pct, avg_talk_sec}` | F01–F02 | 30 d |
| `state.call_mood` | 4 | last-call signals: `rushed / irate / confused / asked_bot` with dates | G00 signals | 30 d |
| `state.intent` | 4 | `problem / wants_upgrade / not_interested / unknown` | G00 summaries + objections, J02 chatbot intents | 45 d |
| `state.recent_exec_contact` | 8 | `{met_exec_days_ago, exec_calls_30d}` | H01, H03, G00 exec_contact | 14 d |
| `state.call_fatigue` | 4 | `{vani_calls_7d, vani_calls_30d, asked_stop_calling}` | G00 | 7 d |
| `state.open_grievance` | 8 | latest complaint / grievance not resolved | I01, G00 grievance signal | 60 d |
| `state.category_demand_now` | 5, 7 | `{local_bl, hyperlocal_bl, bulk_share, price_band}` | E08 counts, E09 | 30 d |
| `state.peer_position` | 7 | where the seller stands vs **same-size peers** (bought/used leads vs peer median) | peer statistic (being researched) | 30 d |

## 5. Hooks are chosen, not fixed (the user's point)

A hook is a candidate reason for the meeting. Many can be true for one seller at the same time. The agent **picks the best one or two for this seller**, and the others stay as backups for objections. Each hook has eligibility rules: it may only be used when its data is present and true.

```json
{
  "id": "hook.unused_credits",
  "division": ["CSD", "TMW", "KCD"],
  "requires": {"state.bl_usage": ["unused", "lapsed", "low_use"]},
  "claim_template": "Aapke {lapsed} credits lapse ho gaye / {balance} credits abhi bache hain…",
  "facts_from": ["E05", "E06"],
  "strength": "how strong and how fresh the evidence is",
  "avoid_if": ["state.open_grievance=billing", "state.call_fatigue.asked_stop_calling"],
  "meeting_reason": "show you how to pick and use leads"
}
```

| Hook | For | Needs |
|---|---|---|
| `hook.profile_gap` | NSD | weak IM profile (D06/C08/C06) |
| `hook.category_demand` | NSD, CSD | high local BLs / enquiries in their MCAT (E08/E09) |
| `hook.unused_credits` | CSD | `state.bl_usage` unused / lapsed |
| `hook.lead_quality_fix` | CSD | `state.bl_quality_issue` |
| `hook.enquiry_drop` | CSD | `state.enquiry_flow` falling |
| `hook.peer_usage` | NSD, CSD | `state.peer_position` with a big-enough peer cell **of the same size** |
| `hook.resolve_grievance` | CSD | `state.open_grievance` (acknowledge first, then meeting to fix) |

Selection, done by the agent and checked by code: eligible hooks → rank by (relevance to division + intent) × (evidence strength) × (freshness) → pick primary + backup. Code validates that the chosen hook's `requires` are met and that its facts are in `verified_facts`.

## Open questions for the user
1. Are the 9 traits and 11 states the right set? Anything to merge, drop or add?
2. `scale_tier` cut-offs: turnover < 1.5 Cr = small? Or use the board's split (< 1.5 Cr / > 1.5 Cr) plus AOV?
3. Do TMW and KCD sellers use the CSD hooks?
4. Should hooks live in the persona library, or in a third "hook library"?
