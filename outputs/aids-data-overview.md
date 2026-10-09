# "Aids to solve Problems" folder: what it gives PS04

As of 2026-10-09. All sources (offline + API) compared: [seller-data-sources.md](seller-data-sources.md). Source: the organiser folder `Aids to solve Problems` (Drive download, kept outside the repo). Only aggregates and schema are recorded here; no seller names, messages or recordings.

**Join key everywhere:** seller GLID (`fk_glusr_usr_id` / `seller_glid` / `glid` / `GLUSR_ID`).

## Files and relevance

| Item | Rows · sellers | Overlap with PS07 sellers (149,363) | Use for PS04 | Relevance |
|---|---|---|---|---|
| **Global Context – Seller Dataset** (11 CSVs + dictionary) | 5,000 sellers; 1 Apr – 2 Oct 2026 | **5,000 / 5,000** | Built for "a `seller.md` VANI loads before a call", which is our B1 seller context | **HIGH** |
| **Best-Time-to-Call** (attempts + sellers + dictionary) | 530,748 dial attempts · 149,363 sellers | **149,363 / 149,363** | Call patterns, **including unanswered attempts** (PS07 has answered calls only): pickup by hour, retry gaps, callback (`lead_tbro_time`) | **HIGH** |
| **Global_Context_Problem_Statement_Buyer Side.csv** | 392 log rows · 301 GLIDs | 0 | Kibana logs of an **existing internal context API** (see below), showing its full response schema | **HIGH** (for the API) |
| `Persona Files-…zip` | — | — | Same PS07 data we already have | duplicate |
| `call_recordings.zip` | 714 MP3s | not checked | Audio of bot calls (file names: `<n>_<id>_<code>.mp3`). Could be used to audition pace and tone | MEDIUM |
| `Sarvam Prompt - Buyer Side VANI.docx` | ~1,600 lines | — | A real production Sarvam prompt (buyer side): role, language limits, per-turn decision procedure, instruction priority, ask limits, intent list (TALKING_TO_AI, COMPLAINT, AMBIGUOUS …), state guardrails, Jinja `{% if %}` blocks on variables | MEDIUM: template for our base prompt and variable style |
| `Current Definitions of Call Quality Matrix being used in VANI.png` | 18 parameters | — | VANI QA rubric: Looping Behaviour (irritated buyer → fatal), Dead air (>5 s, or >8 s with noise), WER, outcome accuracy, missed opportunity | MEDIUM: guardrails and eval metrics for switches |
| `Call_Logs_Hackathon.csv` | 1,000 rows · 825 sellers | 2 | LEAP BL-enrichment call logs (disposition, recording URL) | LOW |
| `Seller Enrichment/` (Seller Onboarding, PS06) | 5,000 verified sellers + reference tables | 151 | `ref_category_taxonomy.csv` (106,619 MCATs with tree), `ref_category_specs.csv`; products and categories for only 151 of our sellers | LOW (taxonomy is useful) |

## Global Context dataset (per seller, 5,000 sellers)

| File | Rows | Sellers | Gives |
|---|---|---|---|
| `gc_seller_profile` | 5,000 | 5,000 | PS07 seller-file columns **plus** `company_name`, `customer_type`, `is_paid`, `listing_status`, KYC flags |
| `gc_enquiries_received` | 33,006 | 2,749 | Buyer enquiries: product, keyword, buyer city/state, read status, first-read time (responsiveness) |
| `gc_enquiry_messages` | 17,633 | 1,468 | Enquiry thread replies (buyer and seller) |
| `gc_buyer_calls_received` | 19,238 | 2,063 | **PNS buyer calls: time, duration, talk time, connected or not** (call pattern) |
| `gc_buyleads_bought` | 14,852 | 254 | BL purchases: MCAT rank, keyword, preferred location (16 Aug – 1 Oct only) |
| `gc_whatsapp_messages` | 130,897 | 3,681 | WhatsApp delivery/read status (engagement, no text) |
| `gc_whatsapp_chatbot_conversations` | 83,280 | 3,002 | Seller's WhatsApp chatbot messages with intent labels |
| `gc_buyer_call_extractions` | 5,417 | 1,388 | AI-extracted call details: **`languages`**, products, prices, specs |
| `gc_bot_calls` / `gc_bot_call_turns` | 9,657 / 4,920 | 4,395 / 420 | VANI calls (same structure as PS07) |
| `gc_executive_calls` | 2,580 | 271 | Executive calls, Aug–Sep |

`gc_buyer_call_extractions.languages` is a **measured** language signal for 1,388 sellers. It is better evidence for the language and Hinglish choice than state alone.

## Existing internal API: `exchange.intermesh.net/go/api/globalcontext/v1/x/getContext`

Seen in the buyer-side logs: `GET …/getContext?mapping_id=<uuid>`, host `leap_models_kube_gke`, mostly HTTP 200. Call parameters for a GLID are unknown (the logs use `mapping_id`). Response `data` blocks:

- **`kycdetails`**:
  - Profile: company, first and last name, city, `customer_type`, `highest_service`, `customer_vintage`, `registered_since_with_indiamart`.
  - GST: status, turnover, nature of business, last filing.
  - Account: `account_manager_bd` / `_fsf`, renewal date and status, NACH status, payment plan.
  - Risk: `high_churn`, `high_risk_suspected`.
  - Activity and support: `rating_count`, `approved_product_count`, `bl_active_dau_30`, last call details, last 10 supplier activities, last tickets and CLM feedback, `ticket_count`, `vertical_name`.
  - **PII:** name, email, address, account-manager contacts.
- **`activitydetails`**:
  - Windows: `last_week` / `last_4_week` / `last_month` / `last_3_month`.
  - BL behaviour: BL consumed, BL credits, BLNI reasons, consumption speed (0–4 h / 4–24 h / >1 day), app / desktop / mobile split.
  - Catalogue: approved products, products without photo / price / category, A-rank and negative MCATs.
  - Other: PNS received and picked, notifications clicked, CQS, `top3mcat_data`, `top3mcat_competitors`.
  - Last items: `LAST_ENQUIRY`, `LAST_LEAD`, `LAST_WA8181_CHAT`, `LAST_WA9696_CHAT`.
  - Counts: `enq_last_30/90_days`, `pns_received_30/90_days`.
- **`BLdetails`**: BLs available (in the seller's city, A-rank, preferred city), `active_bl_details`.
- **`connectdetails`**: `last_call_summary`, connects over 7 and 30 days, proposals sent, SMS and email outbound.
- **`ticketsdetails`**: current, last 7 days, WIP legal and ops tickets.
- **`duplicate_glids_details`**: duplicate and paid IDs.

This is close to a ready-made `seller.md` and covers most of `seller-context-apis.md` §2 in one call. To use it, B1 still has to pick, cite and mask fields; the persona logic stays ours. **Ask:** who owns it (LEAP models team?), how to call it by GLID, and whether we're allowed to use it.

## Best-Time-to-Call: aggregate check (all 530,748 attempts)

| Hour | Attempts | Answered % | Meeting % of answered |
|---|---|---|---|
| 09 | 48,342 | 53.9 | 13.9 |
| 10 | 56,689 | **38.0** | 11.7 |
| 11 | 82,630 | 49.3 | **6.3** |
| 12 | 56,053 | 49.6 | 8.2 |
| 13 | 39,260 | 52.7 | 11.8 |
| 14–17 | 169,777 | 53.7–56.0 | 12.6–13.6 |
| 18–20 | 73,960 | 51.2–53.8 | 12.9–13.8 |

- Late morning is the worst window: 10:00 has the lowest pickup and 11:00 the lowest meeting rate.
- Of 72,301 sellers with ≥3 attempts, 13,694 (19%) never answered.
- These numbers are raw, not adjusted for seller mix (hot-lead buckets are dialled at different hours). Treat them as a per-seller "best time to call" feature and an opening cue (e.g. a busy-hour call gets a short opener), not as a causal claim.
