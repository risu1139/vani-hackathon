# Seller context (B1): data catalogue and implementation plan

As of 2026-10-09 (hackathon day 1). Block **B1 Seller context builder** of [plan v5](VANI%20persona%20architecture%20plan%20v5.md) §4.1. It feeds B2 (estimator) and B5 (persona decision).
Background: [seller-data-sources.md](../seller-data-sources.md) (all sources compared, callee §2b) · [seller-context-apis.md](../seller-context-apis.md) (every API) · [aids-data-overview.md](../aids-data-overview.md).

**How to use this document.** §1 is a catalogue of every data point with its file source and API source. Put **Y / N** in the `Use` column. My recommendation is in `Rec`: **P0** = must have for the demo, **P1** = adds clear fit, **P2** = nice to have. Points marked ★ are new suggestions that weren't in your list. §3 is the build plan; it starts from your selection. §4 shows what we hold per seller.

**Coverage key.** `PS07 %` = share of the 149,363 PS07 sellers, `GC %` = share of the 5,000 Global Context sellers (proposed demo and eval pool). For counts, the percentage is the **non-zero** share. All numbers were counted by us from `data/` (PROVEN). API sources are DOCUMENTED (never called).
**Source codes.** Files: `ps07/*` (persona dataset), `gc/*` (Global Context), `btc/*` (Best-Time-to-Call), `so/*` (Seller Onboarding, only 151 PS07 sellers). APIs: **A1** `getContext` (exchange.intermesh.net), **A2** Customer Scorecard (imdwh), **A3** other imdwh DWH APIs, **A4** users.imutils.com, **A5** leads.imutils.com, **A6** product APIs, **A7** enquiry / LMS / Bizfeed, **A8** Category-ML, **A9** MERP / BI-SOA.

---

## 1. Data point catalogue

### A. Identity and callee (who we are talking to)

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| A01 | Seller GLID | join key | all files | 100 · 100 | all | no | P0 | |
| A02 | Company name | greeting, personalisation | `gc/gc_seller_profile.company_name`; `so/so_sellers.company_name` | 3 · 100 | A1 `kycdetails.company_name`; A4 `users/minidetail`, `users/detail` | yes | P0 | |
| A03 | Contact person name | "{name} ji" greeting | — (removed from all files) | 0 · 0 | A4 `users/minidetail` first/last name; A1 `first_name` / `last_name` | yes | P1 | |
| A04 | Account contact designation (Proprietor, Director …) | formality, DM check | `so/so_sellers.contact_designation` | 0.1 · ~0 | A4 `users/detail` `others=ALL` (column unverified) | no | P1 | |
| A05 | Numbers on the account + type / office-hours status | which number, callee | — | 0 · 0 | A4 `users/pnssetting` (`pns_type`, `pns_status`); A4 `users/detail` `all_contact_info=1`; A4 `users/otherdetail` `ContactDetails` | yes (store count and type only) | P2 | |
| A06 ★ | **Past pickup role**: DM / family / staff / wrong number | opening check, gatekeeper mode | `ps07` evaluator `disposition`: `alternate_number_or_not_dm` (1,634 sellers), `wrong_number`, `alternate_person_designation` (953 sellers; family 48%, owner/boss 44%) | ~1.1 · ~1 | — | designation no; alt name / number yes | P1 | |
| A07 | Gender of the contact | — | — | 0 · 0 | — | — | GAP (don't infer from names) | |

### B. Location and language

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| B01 | City, district, state | default language, accent, local references | `ps07` seller file; `btc` sellers; `gc` profile | 100 · 100 | A1 `kycdetails.city`; A4 `users/minidetail` | no | P0 | |
| B02 | Pincode, locality, lat/long | hyperlocal hook | `ps07` pincode 100, locality 37; `btc` lat/long 44; `so/so_seller_locations` | 100 · 100 | A4 `users/detail` | coarsen | P2 | |
| B03 ★ | **Language spoken on real calls** | start language, Hinglish mix | `gc/gc_buyer_call_extractions.languages` | 0.9 · 28 | — | no | P0 | |
| B04 ★ | Seller's own Hinglish / English / script share on VANI calls | Hinglish mix, formality | `ps07/ps07_call_turns.text` (speaker = seller) | 7.8 · 8.4 | — | text yes | P1 | |
| B05 | Preferred language ID | language | `so/so_sellers.preferred_language_id` (mapping unknown) | 0.1 · ~0 | A4 `users/detail` `others=ALL`? | no | P2 | |

### C. Business profile

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| C01 | Business type (proprietorship / partnership / company) | formality | `ps07` / `btc` / `gc` `business_type` | 98 · 99 | A1 `company_type`; A4 `users/otherdetail` GST | no | P0 | |
| C02 | Annual turnover slab | formality, pitch tier | `annual_turnover` | 89 · 90 | A1 `gst_turnover`; A4 `otherdetail.GLUSR_GST_ANNUAL_TURNOVER` | no | P0 | |
| C03 | Nature of business (+ secondary) | vocabulary, playbook | `nature_of_business` / `_secondary` | 89 / 98 · 89 / 98 | A1 `gst_nature_of_business` | no | P0 | |
| C04 | Business vintage (GST year, member since) | respect / tenure framing | `gst_registration_year`; `so.member_since` | 98 · 99 | A1 `customer_vintage`, `registered_since_with_indiamart` | no | P1 | |
| C05 | Customer type, paid flag, plan | existing client vs prospect, tone | `gc.customer_type` 100, `gc.is_paid` (5% paid) | 3 · 100 | A1 `highest_service`, `customer_type`; A2 `service`; A9 `Listing/ActiveServices` | no | P0 | |
| C06 | Listing status, KYC / verification flags | trust, readiness | `gc` flags | 3 · 100 | A1; A4 `users/detail` | no | P2 | |
| C07 | Employees, year established | size cue | `so/so_sellers` | 0.1 · ~0 | A4 `users/detail` `others=ALL` | no | P2 | |

### D. Categories and products

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| D01 | Top 3 categories + parent + group | personalisation, vocabulary | `top_category_1/2/3`, `top_parent_category`, `top_category_group` | 97 / 94 / 88 · 98 / 96 / 90 | A5 `user_selling_mcat`; A8 `top_mcat/prod_count`; A1 `top3mcat_data` | no | P0 | |
| D02 | Number of categories | breadth | `num_categories` | 97 · 98 | A3 `category_dtls` | no | P2 | |
| D03 | All categories with rank A/B/C/D, negative, D-rank | precise hook | `so/so_seller_categories` | 0.1 · ~0 | A5 `user_selling_mcat`, `negative_mcat_details`, `drankmcats` | no | P1 | |
| D04 | Product count; products modified in 90 d / 1 y | catalogue care, engagement | `eng_product_count`, `eng_products_modified_90d` | 70 / 41 · 72 / 44 | A3 `prd_mapping_api`; A6 `productfiltercount`; A2 `live_prd_cnt` | no | P1 | |
| D05 | Product list (names, price) | "aapke {product} ke liye …" | `so/so_products` (latest 50) | 0.1 · ~0 | A3 `prd_mapping_api` (top 50); A6 `products/userlisting` | no | P1 | |
| D06 | Catalogue quality score and gaps (no photo / price …) | improvement hook | `eng_cqs`; `so/so_catalog_health` | 61 · 65 | A2 `cqs`, `prd_no_prices` …; A1 `last_month.prd_without_photo` … | no | P1 | |
| D07 ★ | Active / approved / rejected / deactivated products | catalogue hook | `so/so_products.approval_status` | 0.1 · ~0 | A6 `productfiltercount`; A2 `deactivated_prd`; A9 approved count | no | P2 | |

### E. Buyer demand and buyleads

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| E01 | Enquiries received (90 d / 1 y) | value hook "X enquiries aayi" | `eng_enq_received_90d / _1yr` | 19 / 30 · 25 / 37 | A1 `enq_last_30/90_days`; A3 `gettopbarsmry`, `queryChartSum` | no | P1 | |
| E02 ★ | Latest enquiry details (product, buyer city) | specific hook | `gc/gc_enquiries_received` | 1.8 · 55 | A1 `LAST_ENQUIRY`; A3 `queryChartDtls` | buyer company yes | P1 | |
| E03 ★ | **Responsiveness**: reply rate, time to first read, reply delay | patience / pace prior | `eng_enq_replies_*`; `gc` `first_read_date`; `gc/gc_enquiry_messages` | 26 · 32 / 55 / 29 | A2 `replies`, `lms_active_days` | no | P1 | |
| E04 | Buyleads bought (count, MCAT, keyword) | BL pitch | `gc/gc_buyleads_bought` (16 Aug – 1 Oct only) | 0.2 · 5 | A5 `seller_bl_count` (per MCAT, 3 months), `purchasedcount`; A3 `glusr_bl_summaryv2`; A2 `bl_cons` | no | P1 | |
| E05 ★ | BL credits lapsed / balance | pain point | — | 0 · 0 | A2 `bl_credit_lapsed`, `current_balance`; A1 | no | P2 | |
| E06 ★ | BL consumption speed (0–4 h …) | eagerness | — | 0 · 0 | A2 `cons_0_4_hrs` …; A1 | no | P2 | |
| E07 ★ | BL not-interested reasons (location / spec / product) | anticipate objection | — | 0 · 0 | A2 `blni_*`; A9 `Listing/Blnireport` | no | P2 | |
| E08 ★ | Local competition, BLs available, top-3 competitors | value hook | — | 0 · 0 | A3 `nsdprepplus`; A1 `BLdetails`, `top3mcat_competitors` | no | P2 | |

### F. Phone behaviour and timing

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| F01 | PNS (buyer) calls received / answered | pickup habit | `eng_pns_received_90d`, `eng_pns_answered_90d` | 14 / 9 · 18 / 13 | A3 `pns_chart_api`, `glmisccount`; A2 `pns_*` | no | P1 | |
| F02 ★ | Buyer calls one by one: hour, talk seconds | patience (talk length), busy hours | `gc/gc_buyer_calls_received` | 1.4 · 41 | A3 `pns_chart_api` (avg talk time 7/30/90 d) | no | P1 | |
| F03 | Pickup ratio, long/short calls, callbacks | rush / patience | `eng_pickup_ratio_90d`, `eng_short_calls_90d`, `eng_callback_90d` | 25 / 20 / 17 · 28 / 22 / 22 | A2 `callbacks` | no | P1 | |
| F04 ★ | **Best time to call**: pickup by hour from all VANI attempts | call timing, short opener at busy hours | `btc` attempts (`call_start_time`, `lead_call_status`) | 100 · 100 | — | no | P0 | |
| F05 ★ | Unanswered attempts, retry count (fatigue) | apology / brevity on re-tries | `btc` unanswered | 55 · 56 | — | no | P1 | |
| F06 ★ | **Promised callback slot** | opening "aapne {time} bola tha" | `btc.lead_tbro_time`; evaluator `disposition.followup_when` | 70% of attempts; disposition 51 · 53 | — | no | P0 | |
| F07 ★ | Do-not-call hours (PNS off-hours) | timing guardrail | — | 0 · 0 | A4 `users/pnssetting` `pns_status` | no | P2 | |
| F08 ★ | Last seen on IndiaMART | recency | — | 0 · 0 | A7 Bizfeed `MyActivity/GetActivityStatus` | no | P2 | |

### G. VANI call history (strongest persona evidence)

Leakage rule (PROVEN, plan v5): the seller-file `past_*` and `calls_*` columns cover all of Apr–Sep. Rebuild these values **from call rows dated before `as_of`**.

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| G01 | Attempts, answered, answer rate, average call seconds | rush / patience prior, cold-seller flag | `ps07/ps07_bot_calls` (rebuild); `btc` attempts | 87 · 88 (13% cold) | A1 `last_call_details` | no | P0 | |
| G02 | Outcome history (meeting / NI / general / call later) | prior, plan | `ps07_bot_calls.disposition_label`; `past_dispositions_detailed` | 87 · 88 | — | no | P0 | |
| G03 | Last call summary, outcome, days since | memory, opening | `ps07_bot_calls.lead_call_summary` | 85 · 87 | A1 `connectdetails.last_call_summary` | text yes | P0 | |
| G04 | Past objections and questions | objection playbook | evaluator `objections`, `seller_questions`; seller file `past_objections` | 3.3 / 14 · 3.4 / 15 | — | text yes | P0 | |
| G05 | Frustration, asked-if-bot, DNC, already-with-executive | guardrails, tone | seller file flags (139 / 125 / 1,178 / 4,205 sellers); evaluator `se_contact`, `execdrop` | <1–3 · <1–3 | — | no | P0 | |
| G06 | **Memory facts**: callback time, contact person, language, competitor, need, constraint | plan, opening | summaries + evaluator JSON + turns (regex extractor, plan v5 §4.1) | ~30% of returning sellers | — | text yes | P0 | |
| G07 ★ | **Speech style**: words per turn, speech rate (words/sec), terse, interruptions | pace, brevity | `ps07_call_turns` (`start_sec`, `end_sec`, `text`); evaluator `latency_repetition` | 7.8 · 8.4 | — | no (derived) | P1 | |
| G08 ★ | How past calls ended (drop after identity / mid-pitch, who hung up) | opener design | evaluator `disposition.sub_disposition`, `execdrop.who_ended_call` | 51 / 11 · 53 / 12 | — | no | P1 | |
| G09 ★ | Bot version heard, trigger bucket | trial-arm evidence; reason for the call | `ps07_bot_calls.lead_bot_version`, `redis_bucket` | 87 · 88 | — | no | P1 | |
| G10 | Recordings | voice audition, pace check | `call_recording_url` | 78 · 79 | — | audio yes | P2 | |

### H. Human relationship

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| H01 | Executive calls (count, last, duration) | "already in touch", don't conflict | `ps07/ps07_executive_calls`; `gc/gc_executive_calls` | 4.6 · 5.4 | A3 `getgldsrcount`; A9 `/go/api/v1/dsr/dsrdetails`, `/api/v1/call-data` | no | P1 | |
| H02 ★ | Account manager assigned | escalation target | — | 0 · 0 | A4 `users/AccountManager`; A1 `account_manager_bd/fsf` | yes | P2 | |
| H03 | Meetings done / last meeting | skip the pitch, follow up | evaluator `se_contact` (`meeting_done`) | 11 · 11 | A9 `CSDMeeting/CSDMeetingCondition`; A2 `video_meet`, `physical_meet` | no | P1 | |

### I. Account health and risk

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| I01 ★ | Open complaints / tickets / dissatisfied feedback | empathy first, avoid upsell | — | 0 · 0 | A1 `ticketsdetails`, `ticket_count`; A2 `cmplnts_cnt`, `fdbk_nt_satisfied`; A9 `viewsegmentation` | no | P1 (if API) | |
| I02 ★ | Renewal date / status, NACH, payment plan | sensitivity | — | 0 · 0 | A1 `kycdetails` | no | P2 | |
| I03 ★ | High churn, high risk suspected | tone, escalation | — | 0 · 0 | A1 `high_churn`, `high_risk_suspected` | no | P2 | |
| I04 ★ | Ratings (avg, count) | compliment hook | — | 0 · 0 | A2 `avg_ratings`, `ratings_cnt`; A4 `users/supplierrating` | buyer names yes | P2 | |

### J. Other channels

| ID | Data point | Persona use | File source | PS07 % · GC % | API source | PII | Rec | Use |
|---|---|---|---|---|---|---|---|---|
| J01 ★ | WhatsApp read / response rate | offer a WhatsApp follow-up | `gc/gc_whatsapp_messages` | 2.5 · 74 | A1 `LAST_WA8181_CHAT`, `LAST_WA9696_CHAT` | no | P2 | |
| J02 ★ | WhatsApp chatbot: recent intents, concerns | recent context | `gc/gc_whatsapp_chatbot_conversations` | 2.0 · 60 | A3 `getwaconv` | text yes | P2 | |
| J03 ★ | Buyer-call extraction: products, prices, B2B or not | business reality | `gc/gc_buyer_call_extractions` | 0.9 · 28 | — | no | P2 | |

### K. This call's own context (not seller data, but B1 must carry it)

| ID | Data point | Persona use | Source | Rec | Use |
|---|---|---|---|---|---|
| K01 ★ | **Call trigger** (hot-lead bucket: PIM, PUA, UA, PNSM …) | the reason for calling = the opening line | dialler / `redis_bucket` in `btc` and `ps07` | P0 | |
| K02 ★ | Attempt number for this lead | retry tone | `btc.call_attempt_count` | P1 | |
| K03 ★ | Local time, weekday, festival / season | opener, timing | derived | P1 | |
| K04 ★ | Dialled number type | callee | dialler (not in data) | P2 | |

---

## 2. Source summary (who provides what)

| Source | Type | Coverage | Strength | Limits |
|---|---|---|---|---|
| `ps07` persona files | file | 149,363 sellers | call history, transcripts, evaluator JSON, flags | seller-file history columns leak; no names |
| `gc` Global Context | file | 5,000 (all in PS07) | enquiries, buyer calls, WhatsApp, call languages, company and plan | 5K sellers only |
| `btc` Best-Time-to-Call | file | 149,363 | every dial incl. unanswered, callback slots | timing only |
| `so` Seller Onboarding | file | 151 PS07 sellers | designation, all categories, products, catalogue health | tiny overlap |
| A1 `getContext` | API | any seller | nearly everything current, in one call | access unknown; PII |
| A2–A9 | API | any seller | current metrics, trends, products, MCATs, PNS, accounts | auth (`AK` JWT) and reachability unknown; never called |

---

## 3. Implementation plan

### 3.1 Block design

```
selection.yaml (your Y/N from §1)
        │
        ▼
 ┌──────────── B1 SELLER CONTEXT BUILDER (app/context/) ─────────────┐
 │ 1 SOURCE REGISTRY  data-point ID → file loader | API fetcher       │
 │ 2 OFFLINE LOADERS  data/ files, indexed by GLID (seller_inventory) │
 │ 3 API ADAPTERS     A1 or A2/A5/A3/A4 → same field names; cache     │
 │ 4 AS-OF FILTER     keep events < as_of; rebuild history from rows  │
 │ 5 DERIVERS         pickup-by-hour, responsiveness, speech style,   │
 │                    callee role, cold flag, trigger reason          │
 │ 6 MEMORY FACTS     regex extractor over summary / eval / turns     │
 │ 7 MASKER           names, numbers, buyer details → tokens (tested) │
 │ 8 ASSEMBLER        seller_context.json + per-field source & date   │
 │                    + missing_fields + completeness                 │
 └───────────────────────────────┬────────────────────────────────────┘
                                 ▼
          B2 estimator · B5a gate (free-text / low-confidence) · B5b composer
                                 ▼
          B12 seller_snapshot (append-only, on premises)
```

| Step | Why | How (chosen; rejected) | Input → output | Status |
|---|---|---|---|---|
| 1 Registry | lets your selection drive the build | one Python dict per data-point ID: `{file: loader, api: fetcher, pii, rec}`; *rej.* hard-coded builder | `selection.yaml` → active fields | ASSUMED |
| 2 Offline loaders | D1 "generator on sample seller files" | stream CSVs once into per-GLID Parquet/SQLite (`data/index/`); *rej.* re-scan per seller (30 s) | `data/*` → per-GLID rows | index PROVEN (`seller_inventory.py`) |
| 3 API adapters | fresh values for the live demo | `requests` with timeout and cache to `data/api_cache/`; A1 first if granted; *rej.* calling APIs inside the call | GLID → JSON → same field names | DOCUMENTED, untested |
| 4 As-of filter | no leakage; fair evaluation | drop rows ≥ `as_of`; recompute G01/G02/G05 from call rows | rows → as-of rows | rule PROVEN |
| 5 Derivers | turn raw rows into persona signals | deterministic code (§3.3) | rows → features | ASSUMED |
| 6 Memory facts | free text holds the plan's best facts | regex families from plan v5 (precision 70–95%); LLM later | text → `memory_facts[]` | PROVEN (baseline) |
| 7 Masker | data rule + off-premises LLM | dictionary of known names (company, contact, buyer) from the same row + regex for phone and email; unit test | text → masked text | ASSUMED |
| 8 Assembler | one contract for B2 and B5 | JSON Schema in `app/contracts/seller_context.schema.json` | → `seller_context` | ASSUMED |

### 3.2 Output contract (extends plan v5 §4.1)

```json
{
  "snapshot_id": "…", "glid": "…", "as_of": "2026-09-01T10:00",
  "call": {"trigger_bucket": "PNSM", "attempt_no": 2, "local_time": "11:20", "weekday": "Tue", "festival_window": null},
  "callee": {"account_contact_designation": "Proprietor|unknown", "past_pickup_role": "decision_maker|family|staff|wrong_number|unknown",
             "referred_dm_designation": "owner|husband|…|none", "alternate_number_known": false},
  "profile": {"company_name_token": "<COMPANY>", "city": "…", "state": "…", "business_type": "…", "turnover": "…",
              "nature_of_business": "…", "vintage_years": 8, "customer_type": "…", "is_paid": false},
  "catalogue": {"top_categories": ["…"], "category_group": "…", "product_count": 40, "cqs": 62, "top_products": ["…"]},
  "demand": {"enq_90d": 12, "last_enquiry": {"product": "…", "buyer_city": "…", "days_ago": 3},
             "reply_rate": 0.4, "median_first_read_hours": 5.2, "bl_bought_90d": 0},
  "phone": {"pickup_by_hour": {"9": [3, 5]}, "best_hours": [15, 16], "pns_answer_rate_90d": 0.6,
            "median_talk_sec": 48, "unanswered_streak": 2, "promised_callback": "2026-09-02T16:00"},
  "language": {"observed": ["Hindi", "English"], "source": "gc_extraction|transcript|state", "english_share": 0.18},
  "history": {"n_prior_calls": 3, "answered": 2, "last_outcome": "Call Later", "gap_days": 6,
              "outcome_shares": {}, "avg_call_sec": 42, "end_pattern": "dropped_after_indiamart_identity"},
  "signals": {"rush": {"k": 1, "n": 2}, "frustration": {"k": 0, "n": 2}, "asked_if_bot": {"k": 0, "n": 2}, "terse": {"k": 1, "n": 2}},
  "speech_style": {"words_per_turn": 4.1, "words_per_sec": 2.6, "interruptions": 1},
  "relationship": {"exec_calls_90d": 0, "meeting_done": false, "already_with_exec": false},
  "memory_facts": [{"family": "callback_when", "value": "after Diwali", "span_id": "S:…", "call_date": "…", "durable": false}],
  "free_text": [{"span_id": "S:…", "source": "S|E|T", "text_masked": "…"}],
  "flags": {"dnc": false, "ni_overridden_by_text": false, "cold": false},
  "field_sources": {"profile.turnover": {"src": "file:ps07_seller_file|api:A1", "as_of": "…"}},
  "missing_fields": ["callee.account_contact_designation"], "completeness": 0.72
}
```

Every field records its source and date in `field_sources`. B5 cites these as the "reason" behind each persona choice (D2 deliverable).

### 3.3 Derivations (code, deterministic)

| Feature | Rule | From |
|---|---|---|
| `best_hours`, `pickup_by_hour` | answered / attempts per hour, attempts before `as_of`, Beta-smoothed toward the global hour curve | `btc` attempts |
| `promised_callback` | latest `lead_tbro_time` after a Call Later, or `followup_when` | `btc`, evaluator |
| `unanswered_streak` | consecutive NotAnswered attempts up to `as_of` | `btc` |
| `reply_rate`, `median_first_read_hours` | replies / enquiries; `first_read_date − enquiry_date` | `gc` |
| `median_talk_sec`, `pns_answer_rate_90d` | over buyer calls in the 90 d before `as_of` | `gc` buyer calls |
| `english_share`, `words_per_turn`, `words_per_sec` | seller turns: Latin-script English tokens / all tokens; words / (end − start) | `ps07` turns |
| `past_pickup_role` | latest disposition with not-DM or wrong number → map `alternate_person_designation` to family / owner-boss / staff | evaluator |
| `signals.*` (k of n) | lexicon hits on seller turns + evaluator labels, per call | turns, evaluator |
| `cold` | 0 prior answered calls before `as_of` | `ps07` bot calls |
| `vintage_years` | `as_of` year − `gst_registration_year` | profile |

### 3.4 Field precedence

1. **Evaluation and evidence** (PS07 replays, experiment): **files only**, as-of. These are reproducible and leakage-free.
2. **Live demo call:** files for history (G, F04–F06, E02–E03), and **API for current state** (A1, or A2 / A5 / A3) where you selected an API source. On API failure or timeout, fall back to the file value and mark it `stale`.
3. Conflicts: API wins for current-state fields (plan, products, enquiries 30 d); files win for history.

### 3.5 Work order (owner M, per plan v5 §11.2; S helps on the API)

| # | Step | Done when | When |
|---|---|---|---|
| 0 | **You select data points** (fill `Use`) → `app/context/selection.yaml` | file committed | D1 now |
| 1 | `seller_context` JSON Schema + 3 example fixtures (rich, average, cold) | schema validates fixtures | D1 +1 h |
| 2 | Offline loaders → per-GLID store (extend `seller_inventory.py`) | `build_context.py --glid X --as-of T` returns P0 fields | D1 +3 h |
| 3 | As-of filter + **leakage test** (no field uses an event ≥ `as_of`) | test passes on 200 random sellers | D1 +4 h |
| 4 | Derivers (§3.3) + callee resolver | unit tests on fixtures | D1 night |
| 5 | Memory-fact extractor (port regex families) | precision table reproduced | D1 night |
| 6 | Masker + PII test (no digits ≥ 7, no known names in `text_masked`) | test passes on all GC sellers | D1 night |
| 7 | API adapter: reachability test from laptop / Daytona; A1 if granted, else A2 + A5 `seller_bl_count` + A3 `pns_chart_api` / `prd_mapping_api` | 3 demo GLIDs fetched and cached | D2 09:00 |
| 8 | Batch build: all sample sellers (D1 deliverable) + demo sellers frozen | `data/contexts/*.json` + coverage report | D2 11:00 (freeze 12:00) |
| 9 | Completeness report per field (feeds the slide and skills.md) | table of fill % per selected field | D2 12:00 |

**Demo seller choice:** use the GC pool. Of the 5,000: 5 sellers have all 8 rich sources, 67 have 7, 244 have 6, 489 have 5. Pick 2–3 contrasting sellers from the ≥ 5 group, plus one **cold** seller (12.9% of PS07 sellers have no bot call).

### 3.6 Devil's advocate

- **API access may not arrive in 2 days.** Every P0 point has a file source, so the build doesn't depend on APIs. APIs are an upgrade for freshness.
- **Pre-built rule.** A1 `getContext` is an internal *data* API. Field selection, derivations, persona logic and switching remain ours. State this in skills.md.
- **Data on premises.** Raw text and PII stay in `data/`. Only masked `free_text` and non-PII fields reach any off-premises model, pending the organiser ruling (plan v5 §6.4).
- **Sparse flags.** Frustration and asked-if-bot are set for under 0.1% of sellers. Derive them from turns and evaluator per call instead (G05 / G07), and accept that most sellers carry only priors.
- **GC pool bias.** These 5,000 were sampled because they are active on several channels, so they are richer than average. Report coverage on all PS07 sellers too.

### 3.7 Decisions needed from you

1. `Use` column in §1.
2. Demo pool = GC 5,000? (recommended)
3. Should we chase API access now (A1 owner; `AK` JWT for A4), or go files-only for the demo?

---

## 4. What we hold per seller (files)

### 4.1 Lookup tool

```
python app/context/seller_inventory.py build              # once, ~30 s → data/index/seller_coverage.csv
python app/context/seller_inventory.py show --glid <GLID>  # sources, row counts, date ranges, profile fields filled
python app/context/seller_inventory.py show --glid <GLID> --values   # also prints values (may be PII; local only)
python app/context/seller_inventory.py summary            # coverage table below
```

Example `show` output (one GC seller, values hidden): ps07 bot calls 4 (Jun–Aug), call turns 5, evaluator 7 (disposition 3, seller_questions 1, execdrop 1, se_contact 1, latency_repetition 1), enquiries 50 (Apr–Sep), enquiry replies 3, buyer calls 71, WhatsApp 15, chatbot 4, buyer-call extraction 1, VANI dial attempts 8 (4 unanswered); profile fields filled: ps07 29, gc 40, btc 18; missing: executive calls, buyleads, onboarding files.

### 4.2 Coverage by source (sellers with ≥ 1 row)

| Source | Sellers | % of PS07 | % of GC 5k |
|---|---|---|---|
| ps07 seller file | 149,363 | 100 | 100 |
| ps07 bot calls | 130,129 | 87.1 | 87.9 |
| … with summary | 127,476 | 85.3 | 86.5 |
| … with recording | 115,881 | 77.6 | 78.6 |
| ps07 call turns (transcripts) | 11,652 | 7.8 | 8.4 |
| ps07 evaluator (any) | 89,163 | 59.7 | 61.7 |
| — disposition | 76,189 | 51.0 | 53.2 |
| — seller_questions | 21,342 | 14.3 | 14.9 |
| — incorrect_mf | 18,558 | 12.4 | 12.5 |
| — execdrop | 17,003 | 11.4 | 11.6 |
| — se_contact | 16,153 | 10.8 | 11.2 |
| — location_confirmation | 14,490 | 9.7 | 10.9 |
| — latency_repetition | 11,652 | 7.8 | 8.4 |
| — topics | 6,102 | 4.1 | 4.0 |
| — objections | 5,001 | 3.3 | 3.4 |
| — ivr | 4,772 | 3.2 | 3.2 |
| ps07 executive calls | 6,933 | 4.6 | 5.4 |
| ps07 recording sample | 4,511 | 3.0 | 3.1 |
| btc sellers / attempts | 149,363 | 100 | 100 |
| btc unanswered attempts | 82,003 | 54.9 | 55.5 |
| gc profile | 5,000 | 3.3 | 100 |
| gc enquiries | 2,749 | 1.8 | 55.0 |
| gc enquiry messages | 1,468 | 1.0 | 29.4 |
| gc buyer calls | 2,063 | 1.4 | 41.3 |
| gc buyleads bought | 254 | 0.2 | 5.1 |
| gc WhatsApp messages | 3,681 | 2.5 | 73.6 |
| gc WhatsApp chatbot | 3,002 | 2.0 | 60.0 |
| gc buyer-call extractions | 1,388 | 0.9 | 27.8 |
| gc executive calls | 271 | 0.2 | 5.4 |
| so onboarding (any) | ≤ 5,000 (151 in PS07) | 0.1 | ~0 |
| LEAP call logs | 825 (2 in PS07) | 0.0 | 0 |

### 4.3 Data per seller, by type

| Seller type | Count | What files give |
|---|---|---|
| **Any PS07 seller** | 149,363 | profile (B01, C01–C04, D01–D02, D04, D06), engagement counts (E01, E03, F01, F03), every VANI dial attempt (F04–F06, K01–K02) |
| + called and answered before | 130,129 (87%) | history, last summary, outcomes (G01–G03, G09); 51% have disposition JSON (A06, F06, G08); 14% questions; 3% objections |
| + transcript | 11,652 (7.8%) | speech style and English share (B04, G07), lexicon signals |
| **Cold** (never answered) | 19,234 (12.9%) | profile + dial-attempt timing only → cold-seller path (plan v5 §4.3) |
| **GC seller** | 5,000 | all of the above + company, plan (A02, C05–C06) + by availability: enquiries 55%, WhatsApp 74%, chatbot 60%, buyer calls 41%, call languages 28%, BLs 5% |
| GC richness (of 8 rich sources) | 0: 162 · 1: 788 · 2: 1,308 · 3: 1,143 · 4: 794 · 5: 489 · 6: 244 · 7: 67 · 8: 5 | demo picks from ≥ 5 (805 sellers) |
| Onboarding overlap | 151 | + designation (A04), all categories, products, catalogue health |
