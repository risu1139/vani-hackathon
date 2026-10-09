# Seller data: full awareness for the next LLM / session

As of 2026-10-09 (evening). Generated from `app/context/extraction_map.py`, `SCRUBBER.py` and the 100-seller test set. Read this first, then [`seller-data-README.md`](seller-data-README.md) and the [final plan](plans/Seller%20context%20final%20plan.md). **Our side delivers DATA; it does not compose the persona.** Real seller files are in git-ignored `data/` (PII) and are **not** in the repo; the repo has code, docs and a synthetic example.

## 1. What exists and where

| What | Where | In git? |
|---|---|---|
| Per-seller context, human readable | `data/contexts/<glid>.md` (all data points, with sources) | no (PII) |
| Per-seller context, machine readable | `data/contexts/<glid>.points.json` = `{ID: {value, source}}`; GST/PAN/Aadhaar/IFSC/account numbers scrubbed | no |
| Raw API responses (cache) | `data/api_cache/<endpoint>/<glid>.json` | no |
| 100-seller test set (rich 45, medium 25, sparse 15, cold 10, onboarding 5) | `data/testset/` (`glids.csv` + one CSV per source) | no |
| Code that builds all of it | `app/context/` (`SCRUBBER.py`, `extraction_map.py`, `make_testset.py`, `seller_inventory.py`) | yes |
| Synthetic example of the output | `app/context/examples/example_seller.points.json` | yes |

**Build one seller:** `VANI_AK=<ak> VANI_USERS_TOKEN=<token> VANI_USERS_MODID=GLADMIN python app/context/SCRUBBER.py --glid <GLID>` (`--all` for the test set, `--refresh` to ignore the cache, `--no-api` for files only). Secrets come from environment variables only and are never written.

## 2. Data points emitted (53), with source and as_of safety

Coverage = sellers (of 100) with a non-empty value. **as_of-safe = yes** only for dated file history; live API values are today's numbers and must not be used to replay past calls.

| ID | Data point | Source (file and / or API) | as_of-safe | Coverage | Note |
|---|---|---|---|---|---|
| A01 | Seller GLID | file: all files (key) | yes (dated file history) | 100 |  |
| A02 | Company name | file: gc_seller_profile.company_name (5K sellers) · API: users_detail (glusr_usr_companyname) | file part yes; API part NO | 99 |  |
| A03 | Contact person name | API: users_detail (glusr_usr_firstname/lastname, glusr_usr_cfirstname/clastname) | NO (live value, fetched now) | 100 |  |
| A04 | Contact designation | file: so_sellers.contact_designation (151) · API: users_detail (glusr_usr_designation) | file part yes; API part NO | 43 |  |
| A05 | Numbers on the account (type, office-hours status, pickup) | API: users_pnssetting (GSM/M1/M2/L1/L2: number, pns_type, pns_status); users_contacts (all numbers); pns_chart_12w (pns_no_summ: per-number success 7/30/90 d); byr_supply (number_wise_pns) | NO (live value, fetched now) | 99 |  |
| A06 | Past pickup role (DM / family / staff / wrong number) | file: ps07 evaluator disposition (alternate_person_designation, not_dm, wrong_number) | yes (dated file history) | 51 |  |
| A07 | Gender / salutation | API: users_detail (glusr_usr_gender, glusr_usr_salute, glusr_usr_csalute) | NO (live value, fetched now) | 2 | fields exist but often empty |
| B01 | City, district, state | file: ps07 / btc / gc profile | yes (dated file history) | 100 |  |
| B02 | Pincode, locality, lat/long | file: ps07 pincode/locality; btc lat/long | yes (dated file history) | 100 |  |
| B03 | Languages spoken on real calls | file: gc_buyer_call_extractions.languages | yes (dated file history) | 28 |  |
| B04 | Seller's script / Hinglish mix on VANI calls | file: ps07_call_turns.text | yes (dated file history) | 11 |  |
| B05 | Preferred language id | file: so_sellers.preferred_language_id (151) · API: users_detail (gl_pref_language_id) | file part yes; API part NO | 7 | often empty |
| C01 | Business type | file: business_type | yes (dated file history) | 100 |  |
| C02 | Annual turnover | file: annual_turnover | yes (dated file history) | 90 |  |
| C03 | Nature of business | file: nature_of_business(_secondary) | yes (dated file history) | 99 |  |
| C04 | Business vintage | file: gst_registration_year · API: byr_supply (GL_DTL.member_since); query_sum (summ.cust_to_serv_startdate) | file part yes; API part NO | 100 |  |
| C05 | Customer type / plan / paid | file: gc customer_type / is_paid (5K) · API: scorecard_m (service); byr_supply (GL_DTL.custtype_name, ENQALL.supp_paid_free); query_sum (summ.service_shortname, generic_service_name) | file part yes; API part NO | 100 | API covers every seller |
| C06 | Listing status, KYC flags | file: gc listing / KYC flags (5K) | yes (dated file history) | 100 |  |
| C07 | Employees, year established | file: so_sellers (151) · API: users_detail (glusr_noof_emp_val, glusr_usr_year_of_estb) | file part yes; API part NO | 32 | often empty |
| C08 | Business profile content (about us, infrastructure, quality, awards …) | API: users_profile (Response.Data[]: GLUSR_PROFILE_TITLE, GLUSR_PROFILE_DESCRIPTION, dates, approval status, per section type) | NO (live value, fetched now) | 25 | sparse; free text the seller wrote |
| C09 | Company page on IndiaMART (showroom: facts, products, ratings) | API: company_detail (DATA.COMPANYDETAIL, HOMETOPTEXT, FACTSHEET (Basic), PRDSERV, PRDNAV, SUPPLIER_RATING, URL_DETAIL) | NO (live value, fetched now) | 38 | what the seller published on their IndiaMART page |
| D01 | Top categories | file: top_category_1/2/3, group · API: mcat_names (mname, mid, sbl) | file part yes; API part NO | 98 |  |
| D02 | Number of categories | file: num_categories · API: mcat_rank (cnt_mcatid by rank) | file part yes; API part NO | 95 |  |
| D03 | Categories by rank, negative, D-rank | file: so_seller_categories (151) · API: category_dtls (A/B/C/D rank, negative MCATs, negative districts); scorecard_m (a_rank_mcats … d_rank_mcats) | NO (live value, fetched now) | 100 |  |
| D04 | Product count and recent changes | file: eng_product_count, eng_products_modified_* · API: prd_mapping (Count.product_count); topbar (prd_add_lw/lm/lq, prd_deac_lw/lm/lq) | file part yes; API part NO | 100 |  |
| D05 | Product list | file: so_products (151) · API: prd_mapping (prd_dtls: pc_item_name, pc_item_fob_price, pc_item_date) | NO (live value, fetched now) | 99 |  |
| D06 | Catalogue quality and gaps | file: eng_cqs · API: scorecard_m (cqs, prd_no_prices …); query_sum (prd_smry); byr_supply (curr_prd: without image/price/video/doc) | file part yes; API part NO | 100 |  |
| D07 | Active / approved / deactivated products | API: prd_mapping (Count.approved_products, name_only_products); scorecard_m (live_prd_cnt, deactivated_prd) | NO (live value, fetched now) | 100 |  |
| E01 | Enquiries received | file: eng_enq_received_* · API: topbar (enq_lw/lm/lq); query_dtls (ENQ by month and source); byr_supply (ENQALL.enq_all, total_enq_recv) | file part yes; API part NO | 96 |  |
| E02 | Latest enquiries | file: gc_enquiries_received (5K) · API: getContext (LAST_ENQUIRY) | yes (dated file history) | 59 | no per-enquiry detail via API |
| E03 | Responsiveness | file: eng_enq_replies_*; gc first_read_date · API: scorecard_m (replies, buyer_reply_pct, callbacks); scorecard_v2 (callback_0to1_hrs … callback_gt_1day); byr_supply (enq_reply_cnt, callback_count, thumbs_up_responsiveness_percent) | file part yes; API part NO | 90 | API adds callback speed and buyer-rated responsiveness |
| E04 | Buyleads bought | file: gc_buyleads_bought (5K, Aug–Oct) · API: bl_summary (bl_pur, bl_pur_str); bl_chart (bl_pur); scorecard_m (bl_cons, bl_cons_i/f); byr_supply (bl_pur_total) | file part yes; API part NO | 14 | BLs per MCAT (seller_bl_count) BLOCKED (leads DNS) |
| E05 | BL credits and lapsed credits | API: scorecard_m (bl_credit_lapsed, current_balance, bl_credits_alctd) | NO (live value, fetched now) | 13 |  |
| E06 | BL consumption speed | API: scorecard_m (bl_pur_0to15mins/0to4hrs… frm_appr); byr_supply (bl_pur_0to4hrs_per …) | NO (live value, fetched now) | 13 |  |
| E07 | BL not-interested reasons | API: scorecard_m (blni, blni_loc, blni_spec, blni_wrng_product); bl_summary (BLNI_REASON_WISE_MONTH) | NO (live value, fetched now) | 1 |  |
| E08 | Local competition | API: prepplus_counts (local/hyperlocal BL + paid sellers); prepplus_competitors (competitors) | NO (live value, fetched now) | 95 |  |
| F01 | Buyer (PNS) calls received / answered | file: eng_pns_received/answered_* · API: glmisccount (PNS 7/30/90 d); scorecard_m (pns_calls_recd, pns_calls_ans); topbar (pns_lw/lm/lq) | file part yes; API part NO | 54 |  |
| F02 | Buyer-call talk time | file: gc_buyer_calls_received (5K) · API: pns_chart_12w (pns_avg.avg_talktime_7/30/90days); pns_chart_12m (pns_report: failed by hour band per number) | file part yes; API part NO | 55 |  |
| F03 | Pickup ratio and callbacks | file: eng_pickup_ratio_*, eng_callback_* · API: scorecard_v2 (callbacks + speed buckets) | file part yes; API part NO | 100 |  |
| F08 | Last seen on IndiaMART | API: users_detail (glusr_usr_lastlogin) | NO (live value, fetched now) | 100 |  |
| H01 | Executive calls | file: ps07/gc executive calls · API: dsr_count (total/success connect, calls, meet by month) | file part yes; API part NO | 100 |  |
| H02 | Account managers | API: byr_supply (GL_DTL.assignedto_*, teleassignedto_* (PII)) | NO (live value, fetched now) | 99 | PII: mask |
| H03 | Meetings | file: evaluator se_contact · API: dsr_count (success_meet, success_video, success_phy); scorecard_m (video_meet, physical_meet, last_video_meet_dt) | file part yes; API part NO | 13 |  |
| I01 | Complaints | API: scorecard_m (cmplnts_cnt, closed_cmplnts, fdbk_nt_satisfied) | NO (live value, fetched now) | 1 | counts only; ticket detail needs getContext (BLOCKED) |
| I02 | Renewal / payment | API: getContext (renewal_date, nach); prerenewal () | n/a | 14 | partial: query_sum.summ.cust_to_serv_startdate |
| I03 | Churn / risk | API: getContext (high_churn, high_risk_suspected) | n/a | 100 | partial: scorecard defaulter_flag, pns_defaulter_count |
| I04 | Ratings | API: scorecard_m (avg_ratings, ratings_cnt); byr_supply (cumulative ratings, thumbs up delivery/quality/responsiveness %) | NO (live value, fetched now) | 35 |  |
| J01 | WhatsApp delivery and reads | file: gc_whatsapp_messages (5K) | yes (dated file history) | 71 |  |
| J02 | WhatsApp chatbot conversations | file: gc_whatsapp_chatbot_conversations (5K) · API: wa_conv (out_wa_conv: msg, intent, reply (PII)) | file part yes; API part NO | 77 |  |
| J03 | Buyer-call extractions | file: gc_buyer_call_extractions (5K) | yes (dated file history) | 28 |  |
| K01 | Call trigger | file: redis_bucket (btc / ps07); dialler at call time | yes (dated file history) | 100 |  |
| K03 | Local time / season | file: clock / calendar | n/a | 0 |  |
| K04 | Dialled number type | file: dialler (not in data) | n/a | 0 |  |

**New this evening:** **C08** business-profile sections the seller wrote (`users/profile`, 11 section types) and **C09** the seller's company page on IndiaMART (`company/detail`: facts, products, categories, ratings). C09 coverage above is understated: 53 of 100 sellers were not fetched yet because the company service returned HTTP 429; re-running `SCRUBBER.py --all` refills them (about 1 s per call).

**Not emitted (by decision):**
- **G01-G11, old VANI call history.** Our user's decision is that G stays out of the seller context. The persona session asked for it as a raw export; **that decision is still open with our user.** Where the data lives and what to know: section 5.
- **Scheduling:** F04 best time, F05 unanswered attempts, F06 promised callback, F07 office / do-not-call hours, K02 attempt number, clock time.
- **PII not needed for personalisation:** phone numbers, pincode, lat/long, recordings (full `.md` only).

## 3. APIs we call (production hosts only)

Auth: **imdwh** needs none. The **users** services need `modid` + a service `token` + `AK` (an employee JWT, valid about 24 h); the company-page service needs the same `token`. The company and users services use **path-segment GETs** (the pattern in `consumer_maxi_hero.go`): `.../glid/{g}/modid/{m}/token/{t}/type/{x}/AK/{a}`.

| Endpoint | What it returns | PII |
|---|---|---|
| `scorecard_m` | ~270 monthly metrics, 12 months | no |
| `scorecard_w` | same metrics, weekly | no |
| `scorecard_v2` | 12 months + catalogue views 7/30/90 d, callback speed buckets | no |
| `pns_chart_12w` | PNS by week, avg talk time 7/30/90 d, per-number success | masked/hashed numbers |
| `pns_chart_12m` | PNS by month per number, failed calls by hour band | masked/hashed numbers |
| `glmisccount` | PNS total/success 7/30/90 d, BL DAU, review count | no |
| `prd_mapping` | product counts + top products (name, price, date) | no |
| `topbar` | last week/month/quarter: BL, enquiries, PNS, C2C, products added/deactivated | no |
| `bl_summary` | BL purchases, credits, rejections, BLNI reasons by month (send body exactly) | no |
| `bl_chart` | BL purchase / credit chart, 30 days | no |
| `prepplus_counts` | local / hyperlocal BLs and paid sellers per MCAT | no |
| `prepplus_competitors` | nearby competitors (company, city, distance) | competitor company names |
| `dsr_count` | executive connects / calls / meetings by month | no |
| `mcat_rank` | MCAT counts by rank | no |
| `mcat_names` | MCAT names and products mapped per MCAT | no |
| `category_dtls` | A/B/C/D-rank, negative MCATs, negative districts, premium | no |
| `wa_conv` | WhatsApp chatbot conversation: message, intent, reply | free text (PII) |
| `query_sum` | 18-month enquiry/BL graph, plan + service start date, catalogue gaps | no |
| `query_dtls` | enquiries and PNS by month and source, 18 months | no |
| `byr_supply` | account managers, plan, member since, ratings + thumbs, BL speed, PNS failed by hour, per-number PNS | account-manager name/email/mobile; masked numbers |
| `users_detail` | 267 GLUSR_USR fields: names, contact person, designation, gender/salute, pref language, member since, last login, custtype, turnover, employees, address, email | yes |
| `users_contacts` | all phone numbers (mobile, alt, landline, fax) | yes |
| `users_pnssetting` | numbers mapped to PNS (GSM/M1/M2/L1/L2) with pns_type, pns_status (office hours), contact_id | yes |
| `products_filtercount` | product counts: visible / without photo, price, spec, category, video … | no |
| `users_profile` | seller-written profile sections (title, description, dates); company-API path-segment GET (pattern from consumer_maxi_hero.go); sparse: about 3 of 12 test sellers have any | free text (PII) |
| `company_detail` | company showroom page: resolve alias with glusrid + empty alias, then home with empty glusrid + alias (pattern from consumer_maxi_hero.go); base URL via VANI_COMPANY_BASE, token = users token | free text, contact person, address |

**Reachable but not usable:**

| Endpoint | Status | Why |
|---|---|---|
| `bl_details` | BROKEN | keeps returning 'infr is mandatory'; no matching doc |
| `supplier_perf` | BROKEN | needs MCAT + district lists per call |
| `c2cchart` | BROKEN | 404 on prod |
| `glactivity` | BROKEN | 404 on prod |
| `prerenewal` | BROKEN | 404 on prod |
| `pageviews` | BROKEN | 404 on prod |
| `wa_enq` | BROKEN | 404 on prod |
| `getContext` | BLOCKED | needs MappingID or source_uid; GLID gives 'Mapping Not Found' |
| `users_minidetail` | BLOCKED | 'Authentication Failed - This AK is not allowed' (users_detail covers it) |
| `users_accountmanager` | BROKEN | 404 (byr_supply GL_DTL covers account managers) |
| `users_supplierrating` | BROKEN | needs Supplier_id/Buyer_id format (scorecard + byr_supply cover ratings) |
| `users_otherdetail` | BROKEN | type=ContactDetails → 'No data Found' for test seller |
| `products_soa` | BROKEN | 404 over HTTP, HTTPS times out (prd_mapping covers top products) |
| `leads_soa` | BLOCKED | DNS does not resolve from this laptop |
| `lms_bizfeed_topmcat` | BLOCKED | DNS does not resolve from this laptop |
| `mapi_gateway` | BLOCKED | app authentication failed |
| `merp_soa` | BLOCKED | no base URL in the sheet |

**Operational notes**
- The **company service rate-limits** (HTTP 429). `SCRUBBER.py` sleeps `VANI_COMPANY_SLEEP` seconds (default 1.0) before each call, retries with backoff, and never caches a failed response.
- `users.imutils.com` is **HTTP only** (HTTPS times out). `leads`, `lms`, `bizfeed` and `top_mcat` hosts do not resolve from this laptop.
- API values carry no as_of date. For evaluation on past calls use `--no-api` (files only).

## 4. Offline files (all keyed by seller GLID)

| Source | Holds | Window |
|---|---|---|
| **PS07 persona dataset** | seller file (149,363 sellers: profile, engagement counts, bot-call totals, flags); bot calls (269,455 answered calls: date, outcome, bot version, trigger bucket, summary, recording URL); evaluator outputs (278,332 JSON rows, 10 agent types); call turns (139,555 turns, 12,788 calls); executive calls (67,151) | 1 Apr - 30 Sep 2026 |
| **Global Context** (5,000 sellers, all in PS07) | company and plan, enquiries with text, enquiry replies, buyer calls, buyleads bought, WhatsApp events and chatbot text, buyer-call extractions with languages | 1 Apr - 2 Oct 2026 |
| **Best-Time-to-Call** | 530,748 dial attempts (answered and not), trigger bucket, attempt number, callback slot | 1 Apr - 30 Sep 2026 |
| **Seller Onboarding** (5,000 sellers, 151 in PS07) | designation, languages id, all categories, products, catalogue health, KYC, category taxonomy | pulled 8 Oct 2026 |

Details: [`seller-data-sources.md`](seller-data-sources.md), [`aids-data-overview.md`](aids-data-overview.md), [`seller-context-apis.md`](seller-context-apis.md).

## 5. Old call history (G): where it is and what to watch for

Not in our output, but the raw data is in PS07 and you can build it as_of-clean yourselves:
- **Per call:** `ps07_bot_calls_*.csv` (`attempt_id`, `call_start_time`, `lead_call_duration`, `disposition_label`, `meeting_fixed`, `lead_bot_version`, `redis_bucket`, `lead_call_summary`, `call_recording_url`).
- **Evaluator labels:** `ps07_evaluator_outputs_*.csv`, agents `disposition` (incl. alternate person / designation, follow-up, sub-disposition), `objections`, `seller_questions`, `execdrop` (who ended the call), `se_contact`, `incorrect_mf`, `latency_repetition`, `topics`, `location_confirmation`, `ivr`.
- **Seller turns:** `ps07_call_turns.csv` (`turn_no`, `speaker`, `start_sec`, `end_sec`, `text`); 12,788 calls, about 8% of sellers.
- **Pitfalls we measured:** the seller-file `past_*` and `calls_*` columns cover the whole window and **leak the future**; rebuild from dated call rows. Outcome labels are noisy (4 of the first 20 calls contradicted the transcript). 585 transcripts have every turn duplicated (two audio channels merged). The last bot turn is often cut off. One call had speaker labels flipped. September relabelled "Not Interested" (51% to 19%): fit NI priors on August only.

## 6. What the calls teach (for the persona side)

[`call-flow-playbook.md`](call-flow-playbook.md) and [`call-flow-analysis.md`](call-flow-analysis.md): the standard flow, 12 objections with prevalence and meeting rates over 12,354 transcribed calls, compliance findings (the bot claimed to be human in 24 calls and "a branch manager" in 279), and prompt rules. A human executive's call is analysed there too. The playbook content as data (`playbook.json`) is planned but not built.

## 7. Rules we follow

1. Data, not persona: we do not compose VANI's persona or call plan.
2. Scheduling stays out of persona inputs.
3. GST / PAN / Aadhaar / IFSC / account numbers are scrubbed from `points.json` (the full `.md` is local only; PII handling is the legal team's).
4. LLM = Claude; Sarvam API = voice only (Bulbul, Voice AI agent, speech-to-text for recordings).
5. Production hosts only; no dev / stg.

## 8. Not built yet / open decisions

| Item | State |
|---|---|
| `verified_facts` (statements the LLM may say, each with its source and exact phrasing) | planned |
| Compact `.llm.md` (8 KB or less) | planned |
| `playbook.json` (objections, stop rules, AI-disclosure line, trigger to hook table, seller-type hints) | planned |
| Dated trait / state inputs with as_of_safe flags | partly: file fields are dated; API fields carry `fetched_at` only |
| Raw G export for the persona side | **decision pending** with our user |
| Persona prompt | our user's scope vs the persona session's: **decision pending** |
| One approved price statement; supported voice languages; trigger bucket meanings (UA, PAM, SCHD, NUR, OLP); DNC as a dialler gate | owners outside our side |
