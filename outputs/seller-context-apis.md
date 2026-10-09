# Seller pre-context: internal APIs we can use

As of 2026-10-09. Feeds block **B1 Seller context builder** (plan v5 §4.1). All sources (offline + API) compared: [seller-data-sources.md](seller-data-sources.md).

**Sources.** The "TOTAL APIs DETAIL (Master Sheet)" Google Sheet (`16u3u3HiqJXrkY9t5nsc3pteB4EOgNYvAbq8z7Sz_jb4`, all 35 tabs read). The Big-Data list on apidocs.intermesh.net (doc_Category/Big-Data). The swagger pages for Customer Scorecard v1 and v2.

**Status.** Every API below is **DOCUMENTED** only. None has been called by us yet. "Hits/day" and "p95" are copied from the sheet.

**Key.** Almost every API takes the seller's GLID (`glusr_usr_id` / `glid`), which is the same key as `fk_glusr_usr_id` in the PS07 data. **PII** = the sheet says the response has personal data. Such fields stay in `data/`, are masked before any off-premises LLM, and never go into `raw/` or `wiki/`.

---

## 1. Domains

| Domain | Owner / system | What lives there | Env prefixes seen |
|---|---|---|---|
| `imdwh.intermesh.net/api/go/*` | BI / DWH team (SPOC in swagger: `shailendras@`). Code: `scm.intermesh.net/indiamart-bi/bi-db-team/dwh-apis` | Seller analytics: scorecard, BL, PNS, products, MCATs, enquiries. Read-only PostgreSQL replica (`erpreport-replica`, stored procedures) | `dev-imdwh.intermesh.net` (dev), `imdwh.intermesh.net` (prod) |
| `users.imutils.com/wservce/*` | User / Marketplace SOA | Profile, ratings, PNS settings, dispositions, account manager | `dev-`, `stg-` |
| `seller.imutils.com/wservce/products/*` | Product SOA | Product listing, category data, category report | `dev-` |
| `users.imutils.com/wservce/products/*` | Product SOA | Product filter counts, product detail, MCAT listing, RAG score | `dev-` |
| `leads.imutils.com/wservce/*` | Buyleads SOA | Selling MCATs, BL purchase counts per MCAT, BL detail/status, credits, preferred cities | — |
| `enq2.intermesh.net/enquiry/*` | Enquiry SOA | Enquiries, call enquiries (click-to-call), C2C↔PNS link | — |
| `lms.imutils.com/*` | Lead Manager (LMS) | Buyer conversations, contact counts, labels, reply templates | — |
| `mapi.indiamart.com/wservce/*` | API Gateway (public-facing wrapper of the SOAs) | Same services via gateway, incl. `addressbook/callLogs`, `enquiry/pnsCallerDetail` | prod |
| `dev-bizfeed.imutils.com/*` | Bizfeed | Last-seen timestamp, buyer-side activity | `dev-` |
| `dev-recommend.imutils.com/*` | Recommendation | Recent searches/categories, recommended MCATs | `dev-` |
| `top_mcat.intermesh.net`, `relatedmcat.intermesh.net`, raw IPs | Category-ML | Active categories of a seller, MCAT recommendations | — |
| `glrapi.imutils.com/r/*` | Gladmin read API (Approval PG) | Table reads, incl. `click_to_call` | — |
| `leap.imutils.com/*` | LEAP (lead approval) | Dialer responses, LEAP lead queues | — |
| BI-SOA / MERP (relative paths like `PnsSummary/pnsdetails`, `/api/v1/call-data`) | MERP SOA team | Sales-side views: PNS details, call history, MCAT summary, active services. **The sheet gives no base URL**; ask MERP SOA | — |

**Network.** All hosts are internal. They should be reachable from the VPN laptop. Reachability from the Daytona sandbox is **untested**: it could not reach the OpenRouter key either. Plan to run B1 on the VPN laptop.

---

## 1b. Existing one-call context API (found 2026-10-09)

`GET https://exchange.intermesh.net/go/api/globalcontext/v1/x/getContext?mapping_id=<uuid>`. Seen in organiser logs (`leap_models_kube_gke`). It returns these blocks: `kycdetails`, `activitydetails` (week / 4-week / month / 3-month BL, catalogue and PNS metrics, last enquiry, last lead, last WhatsApp chats), `BLdetails`, `connectdetails` (incl. `last_call_summary`), `ticketsdetails`. Full schema: [aids-data-overview.md](aids-data-overview.md). **If we can call it by GLID, it replaces most of §2.** Owner, auth and GLID→`mapping_id` are unknown. PII: names, email, address.

## 2. APIs by context need

### 2.1 Profile: name, city, company, business (⚠ PII)

| API | Domain | Gives | Hits/day · p95 |
|---|---|---|---|
| `users/minidetail/` | users.imutils.com | First and last name, company, city, logo | 866K · 17 ms · **PII: name** |
| `users/detail/` | users.imutils.com | Main GLUSR_USR record | 2.0M · 18 ms · **PII** |
| `users/otherdetail/` | users.imutils.com | GST, contacts, franchise | 1.0M · 25 ms · **PII** |
| `users/profile/` | users.imutils.com | All profile sections in one call | 46K · 17 ms |
| `vcard/display/` | users.imutils.com | Visiting card | 812K · 15 ms |
| `users/TSDetails/`, `users/tsmiscdetails/` | users.imutils.com | TrustSeal, certifications, trade affiliations | 45K / 0.6K |
| `users/AccountManager/` | users.imutils.com | Assigned sales and tele reps (shows whether a human already owns the seller) | 53K · 61 ms · **PII: rep name/contact** |
| `Listing/ActiveServices` | BI-SOA | Services and campaigns active for the GLID | — |
| `ServiceDetails/getServiceDetails` | BI-SOA | Services taken, plus sales/tele executive details | — |

**Callee (the person we call) and their designation.** Checked against the swagger pages on 2026-10-09:
- `users/detail/`: tables `glusr_usr`, `glusr_usr_ext`, `GLUSR_USR_SOCIAL_CONTACT`. Params: `glusrid`, `modid`, **`AK` (JWT, required)**, `others=ALL` (all extra columns; a designation column is likely but not shown), `all_contact_info=1` (all mobile, landline and fax numbers). Prod host `users.imutils.com`.
- `users/pnssetting/`: tables `iil_pns_setting`, `glusr_usr`, `glusr_usr_addt_contact`. Returns every number on the account with `pns_type` and `pns_status` (office / non-office hours). No name or designation per number.
- `users/otherdetail/`: `Type=ContactDetails` or `CompRgst_AddtContactDetails` (`GLUSR_USR_ADDT_CONTACT`). Returns additional mobile, email and address. Name / designation fields aren't shown in the docs.
- **No API gives a designation per number.** Past-call evidence of who answers (PS07 evaluator `alternate_person_designation`) and the design: [seller-data-sources.md §2b](seller-data-sources.md).

**Gender.** No listed API returns a gender field. `users/detail/` might have a salutation (Mr/Ms); this is unverified. **Don't infer gender from first names.** If it's missing, record it as unknown.

### 2.2 Turnover, business health, problems: **Customer Scorecard (best single source)**

| API | Domain | Gives | Hits/day · p95 |
|---|---|---|---|
| `POST /api/go/cust_scorecard_api` | imdwh | About 90 monthly metrics. Body: `{"in_glusr_usr_id","in_rpt_type": 1 monthly / 2 weekly PNS / 3 daily}` | 2.2K · 19 ms · no PII |
| `POST /api/go/cust_wh_apiv2` (V2) | imdwh | 12-month version: summary keys plus 7/30/90-day catalogue views, callbacks, replies, buyers contacted | 23 · 34 ms |
| `/api/go/byrsupplyapi` | imdwh | Seller performance scorecard (seller panel) | 183K · 31 ms |
| `/api/go/supplierperformance` | imdwh | Supplier performance, parameterised | 3.3K · 68 ms |
| `/api/go/prerenewal_api` | imdwh | BL daily active use, catalogue quality score etc. for sellers with a renewal pending | 3K · 4 ms |
| `/api/go/priority_score` · `dtlspriorityscore` | imdwh | L1 priority score plus details | 0.8K |
| `/api/go/nsdprepplus` (Prep Plus) | imdwh | Local and hyperlocal BL counts, competing seller counts | 978K · 8 ms |

Scorecard fields that matter for persona context:
- **Plan:** `service` (highest package, e.g. Leader / Featured Leader).
- **Pain points:** `cmplnts_cnt`, `closed_cmplnts`, `fdbk_nt_satisfied`, `blni_loc` / `blni_spec` / `blni_wrng_product` / `blni` (BL marked not-interested and why), `bl_credit_lapsed`, `pns_defaulter_count`, `defaulter_flag`.
- **Responsiveness:** `cons_0_4_hrs` / `cons_4_24_hrs` / `cons_grter_1day` (how fast leads are bought), `replies`, `callbacks`, `lms_active_days`, `bl_active_days`.
- **Reputation:** `ratings_cnt`, `avg_ratings`.
- **Catalogue:** `cqs`, `live_prd_cnt`, `deactivated_prd`, `prd_no_prices`, `name_only_prd`, MCAT rank counts (`a_rank_mcats` … `d_rank_mcats`).
- **Human contact:** `success_connect`, `connect_duration`, `video_meet`, `physical_meet`, `succ_connect_bd`.

Other problem signals:

| API | Domain | Gives |
|---|---|---|
| `users/attrdispositions/` | users.imutils.com | Past disposition log for the seller (118K/day) |
| `Listing/Blnireport` | BI-SOA | Customer-voice view: why the seller marked BLs not-interested (a ticket opens after 5) |
| `Userlist/viewsegmentation`, `/go/api/v1/voc/ticketinfo` | BI-SOA | Complaint count, tickets, ticket category |
| `Customerfeedback/customerfeedbackdata` | BI-SOA | C2C call feedback and post-ticket satisfaction |
| `users/supplierrating/` | users.imutils.com | Buyer reviews and ratings (**PII: buyer name**) |
| `/api/go/ni_transaction` | imdwh | NI counts by reason (wrong location, wrong product …) |

### 2.3 Buyleads: purchased, active, expired, lapsed

| API | Domain | Gives |
|---|---|---|
| `/api/go/glusr_bl_summaryv2` (BL Summary) | imdwh | BL purchased, BL credits, BL rejected (58K/day · 60 ms) |
| `/api/go/glusr_bl_detailsv2` (BL Details) | imdwh | BL details, parameterised (50K/day · 261 ms) |
| `/api/go/blchartresponse` | imdwh | BL activity chart: Indian vs foreign |
| `/api/go/bl_consumed_fm_bizfeed` | imdwh | BLs consumed from the Bizfeed page |
| `buyleads/seller_bl_count/` | leads.imutils.com | **Per MCAT: rank, total BLs purchased, primary-MCAT BLs purchased in the last 3 months** (= the kinds of BL they work on) |
| `buyleads/purchasedcount/` | leads.imutils.com | Count of BLs and tenders purchased |
| `buyleads/transactionhistory/` | leads.imutils.com | Balance, credits used and bought, leads purchased, purchase date and mode (p95 1.6 s) · **may hold buyer name** |
| `users/credit/` | leads.imutils.com | Credits credited and debited |
| `User/showblreport` | BI-SOA | **Last 20 BLs consumed in the past year, plus BLs available now** by location |
| `buyleads/detail/` | leads.imutils.com | One offer's status: **valid / expired / rejected / purchased** (by offer ID, not GLID) |
| `leap/expiredLeads/`, `leap/liveLeads/` | leads.imutils.com | Expired (`eto_ofr_expired`) and live (`eto_ofr`) BLs, 10 rows per call. These are LEAP queues, not filtered per seller, and get 0 hits/day |
| `Userlist/localBuyleadCt` | BI-SOA | Local BL count for the GLID |
| `buyleads/blalertfrequency/` | leads.imutils.com | SMS / mail / notification alert frequency |
| `buyleads/preferredcities/`, `DynamicLocationPreference/` | leads.imutils.com | Preferred cities and location score |
| Customer Scorecard | imdwh | `bl_credits_alctd`, **`bl_credit_lapsed`** (expired unused credits), `current_balance`, `last_cons_date` |

**"Expired BL" per seller.** No API lists the BLs a seller let expire. The closest proxies are `bl_credit_lapsed` (scorecard), `showblreport` (available vs consumed) and BL Summary (rejected).

### 2.4 Products: active, deactivated, approved, rejected

| API | Domain | Gives |
|---|---|---|
| `/api/go/prd_mapping_api` (Product Mapping) | imdwh | **Product count plus details of the top 50 products** (643K/day · 6 ms) |
| `products/userlisting/` | seller.imutils.com | All products: name, price, groups, docs, video, images, ISQs (p95 529 ms) |
| `products/productfiltercount/` | users.imutils.com | **Counts: approved, rejected, with images/price/groups, ISQs** (522K/day) |
| `Userlist/GetAprrovedAndNameOnlyProductCount` | BI-SOA | Approved vs name-only product count |
| `Companydashboard/OverviewScreenExt` | BI-SOA | Approved product count, qFCP, email/mobile verified |
| `products/categorydata/`, `products/categoryreport/` | seller.imutils.com | Category and group of every product; category-mapping report |
| `products/detail/` | users.imutils.com | Product, user and prime-MCAT detail by display ID / item ID |
| `products/RAGScore` | users.imutils.com | RAG (red/amber/green) score of the GLID |
| `/api/go/prdtpageviewcnt` | imdwh | Product page views plus product details |
| `/api/go/ecom_rej_prd_dtls` | imdwh | Products by approval status, plus rejected products with reasons (ecom) |
| `/api/go/getmcatglprd` | imdwh | Product counts by type for an MCAT |
| Customer Scorecard | imdwh | `live_prd_cnt`, `prd_added`, **`deactivated_prd`**, `prod_wo_image`, `prd_no_prices` |

### 2.5 MCATs (categories) of the seller

| API | Domain | Gives |
|---|---|---|
| `buyleads/user_selling_mcat/` | leads.imutils.com | **All positive MCATs grouped by rank A/B/C/D** (897K/day · 27 ms) |
| `buyleads/negative_mcat_details/` | leads.imutils.com | MCATs the seller marked negative |
| `buyleads/drankmcats/` | leads.imutils.com | D-rank MCATs: buys BLs there but has no products mapped |
| `top_mcat.intermesh.net/prod_count?glid=` | Category-ML | **Active categories of the seller**, built to give "industry knowledge of the seller to GPT" |
| `/api/go/gl_mcats_prdts_dtls` | imdwh | MCAT-related data for the GLID |
| `/api/go/blsummarydetails` | imdwh | Products mapped in each MCAT of the GLID |
| `/api/go/category_dtls` | imdwh | Counts per MCAT |
| `Mcat/mcatSummary` | BI-SOA | MCAT ID, alert rank, sum |
| `Userlist/fetchMCATList` | BI-SOA | MCAT list (Star/Leader from BigData, others from Leads) |
| `McatDetails/FetchMcatDetails` | BI-SOA | Category owner of the GLID |
| `GLAdmin/focusmcat` | BI-SOA | Focus MCAT group and process name |
| `products/McatCategoryListing/` | users.imutils.com | MCATs the seller chose to list on top in DIR |
| `65.2.28.204/glid_mcat/?glid=&mcat_id=` | Category-ML | GLID × MCAT lookup (undocumented) |
| `Mcat_Recommendation`, `free_seller_recommendation` | Category-ML (raw IPs) | MCATs the seller likely deals in (paid / free) |

### 2.6 Call patterns

| API | Domain | Gives |
|---|---|---|
| `/api/go/pns_chart_api` (PNS Chart) | imdwh | **18 months and 12 weeks of PNS calls; average talk time over 90/30/7 days**; service data (30K/day · 25 ms) |
| `/api/go/glmisccount` | imdwh | PNS total and success count over 7/30/90 days |
| `/api/go/c2cchart` | imdwh | 18 months of incoming and outgoing C2C calls (in-house vs vendor) |
| Customer Scorecard `in_rpt_type=2` | imdwh | **Weekly** PNS count |
| `/api/go/getgldsrcount` | imdwh | Sales-executive (DSR) call count; matches `ps07_executive_calls.csv` |
| `/go/api/v1/dsr/dsrdetails` · `/api/v1/call-data` | BI-SOA | DSR call rows: `CALL_ENTRYDATE`, `CALL_PURPOSE` |
| `/api/v1/welcome-call-details` | BI-SOA | Welcome-call details for the GLID |
| `Calldetails/callhistory` | BI-SOA | Call history and call report (9696 CRM) |
| `PnsSummary/pnsdetails`, `User/pnsquery` | BI-SOA | PNS details (wrappers over Big Data) |
| `CSDMeeting/CSDMeetingCondition` | BI-SOA | Last meeting date and purpose |
| `glrapi.imutils.com/r/clicktocall` | Gladmin | Reads the `click_to_call` table |
| `mapi…/v1/addressbook/callLogs/` | API Gateway | LMS call logs |
| `mapi…/v1/enquiry/pnsCallerDetail/` | API Gateway | PNS caller detail (**likely PII**) |
| `users/pnssetting/` | users.imutils.com | Numbers mapped to PNS, off-hours (**PII: numbers**). Off-hours tells us when not to call |
| `MyActivity/GetActivityStatus` | dev-bizfeed.imutils.com | **Last-seen timestamp** on IndiaMART (9M/day) |
| `CallDisposition/getDispositions` | BI-SOA | Master list of call dispositions (for mapping labels) |

### 2.7 Enquiries, engagement and conversations

| API | Domain | Gives |
|---|---|---|
| `/api/go/gettopbarsmry` (Top Bar Summary) | imdwh | BL consumption, enquiries, replies, C2C calls (565K/day · 4 ms) |
| `/api/go/queryChartSum`, `/api/go/queryChartDtls` | imdwh | Enquiry summary and details |
| `/api/go/getglactivitydata` | imdwh | GLID activity data, parameterised |
| `/api/go/mcatenqsmry`, `mcatwiseenqsmry` | imdwh | Indian/foreign enquiries per MCAT over 18 months |
| `/api/go/whatsapp_enq`, `/api/go/getwaconv` | imdwh | WhatsApp enquiries; full WhatsApp conversation history with IndiaMART (p95 3 s) |
| `lms…/addressbook/conversationList` | lms.imutils.com | Conversation between the GLID and a contact |
| `lms…/addressbook/contactCount/` | lms.imutils.com | Counts of contacts by type |
| `Precallrca/precalldetails` | BI-SOA | Purchased and consumed leads, host date, reply count, NACH date (pre-welcome-call view) |
| `UserAttributes/GetAttributes/` | dev-recommend.imutils.com | Recent products, categories and searches by the user (**PII: supplier contact**) |

---

## 3. Suggested B1 call set (one seller, about 8 calls)

1. `cust_wh_apiv2` (or `cust_scorecard_api`, `rpt_type=1`): plan, problems, responsiveness, catalogue, 12-month trend.
2. `buyleads/seller_bl_count/` + `buyleads/user_selling_mcat/`: what they buy and sell, by MCAT rank.
3. `prd_mapping_api` + `products/productfiltercount/`: top products; active, approved and rejected counts.
4. `pns_chart_api` + `glmisccount`: call volume, answer rate, talk time, weekly pattern.
5. `MyActivity/GetActivityStatus`: last seen.
6. `users/minidetail/`: name and city, for the spoken greeting only (masked before any LLM).

All except #6 are free of PII according to the sheet.

## 4. Open questions

1. Auth: the imdwh swagger shows no auth header. Do the SOA hosts need a token or an IP allowlist?
2. Base URL for the BI-SOA / MERP paths.
3. Is calling prod `imdwh` allowed during the event, or only `dev-imdwh`?
4. Does `users/detail/` return a salutation field?
5. Reachability from Daytona (35.234.211.110) vs the VPN laptop.
