# Seller context: extraction plan and API access test

As of 2026-10-09. Decision: **use every data point** in the catalogue ([sheet](Seller%20context%20B1%20data%20catalogue.xlsx), `Use` = Y for all 66). This plan says where each point is extracted from, which APIs that needs, and what happened when we called them.

**Single source of truth:** [`app/context/extraction_map.py`](../../app/context/extraction_map.py). It holds `ENDPOINTS` (URL, working request body, status) and `DATA_POINTS` (ID → file source, API endpoint + fields, status). The sheet's new columns and its `API endpoints` tab are generated from it.

**How we tested:**
- Production hosts only (no dev/stg), one seller GLID from the Global Context pool, read-only calls, run from this laptop.
- Raw responses are in `data/api_cache/probe/` (git-ignored; some contain PII).
- The AK was passed through an environment variable and never written to disk.
- Probe code: `app/context/api_probe.py`, `app/context/http_util.py`.

---

## 1. Result in one table

| | Count | Data points |
|---|---|---|
| From files only | 31 | profile, language, VANI call history (G01–G10), dial timing, callee evidence, GC channels |
| From files **and** API | 16 | API adds current values and covers every seller, not just the 5K / 151 file subsets |
| From API only | 11 | D03, D05, D07, E05–E08, H02, I01, I04, A05 |
| Derived | 1 | K03 (time / festival) |
| **Gap: no working source** | **7** | A03 contact name, A07 gender, F07 do-not-call hours, F08 last seen, I02 renewal, I03 churn/risk, K04 dialled-number type |

APIs tested: **20 calls work**, 7 reachable but broken, 7 blocked.

---

## 2. APIs we need (all work on prod, no auth)

All on `https://imdwh.intermesh.net/api/go/<endpoint>`, `POST`, JSON body. No AK was needed. Latency 90–230 ms.

| # | Endpoint (name in map) | Body | Feeds data points | PII |
|---|---|---|---|---|
| 1 | `cust_scorecard_api` (`scorecard_m`) | `in_glusr_usr_id`, `in_rpt_type=1` | C05, D03, D06, D07, E03–E07, F01, H03, I01, I04 (~270 monthly metrics) | no |
| 2 | `cust_wh_apiv2` (`scorecard_v2`) | same | E03, F03 (**callback speed 0–1 h … >1 day**), catalogue views 7/30/90 d | no |
| 3 | `pns_chart_api` rpt 1 (`pns_chart_12w`) | `in_rpt_type=1` | A05 (per-number success 7/30/90 d), F02 (avg talk time 7/30/90 d) | masked/hashed numbers |
| 4 | `pns_chart_api` rpt 3 (`pns_chart_12m`) | `in_rpt_type=3` | F02, **F04: failed buyer calls by hour band (0–9, 9–12, 12–16, 16–20, 20–24) per number** | masked/hashed numbers |
| 5 | `glmisccount` | `inglusrusrid`, `rptflag=1` | F01 | no |
| 6 | `prd_mapping_api` (`prd_mapping`) | `in_glusr_usr_id` | D04, D05 (product name, price, date), D07 | no |
| 7 | `gettopbarsmry` (`topbar`) | `glUsrId` | D04, E01, F01 (last week / month / quarter) | no |
| 8 | `glusr_bl_summaryv2` (`bl_summary`) | send the documented body **exactly** (incl. `in_reason_list_id: null`) | E04, E07 (BLNI reasons by month) | no |
| 9 | `nsdprepplus` comp 2 (`prepplus_counts`) | `comp_flag=2` | E08 local / hyperlocal BLs and paid sellers | no |
| 10 | `nsdprepplus` comp 1 (`prepplus_competitors`) | `comp_flag=1` | E08 nearby competitors | competitor company names |
| 11 | `getgldsrcount` (`dsr_count`) | `in_glid` | H01, H03 (executive connects, calls, meetings by month) | no |
| 12 | `blsummarydetails` (`mcat_names`) | `glusr_id` | D01 MCAT names + products per MCAT | no |
| 13 | `category_dtls` | `in_glusr_usr_id` | D03 rank A–D, negative MCATs and districts | no |
| 14 | `getwaconv` (`wa_conv`) | `glid`, `page_id=0` | J02 WhatsApp chatbot messages + intents | **free text** |
| 15 | `queryChartSum` (`query_sum`) | `in_glusr_usr_id` | C04, C05 (plan, service start), D06 | no |
| 16 | `queryChartDtls` (`query_dtls`) | `in_flag=1` | E01 enquiries + PNS by month and source, 18 months | no |
| 17 | `byrsupplyapi` (`byr_supply`) | `insuppglid`, `rptflag=2` | **H02 account managers**, C04 member since, C05, I04 ratings + thumbs-up (delivery / quality / **responsiveness**), E06, F04 PNS failed by hour, A05 per-number PNS | **AM name / email / mobile**, masked numbers |

Optional (same data, other cuts): `cust_scorecard_api` rpt 2 (weekly), `blchartresponse`, `gl_mcats_prdts_dtls`.

**Load:** 17 calls per seller × ~150 ms ≈ 2.5–3 s per seller sequentially. For the 5,000 GC sellers that's ~4 h sequential, or **~30 min with 8 workers**. Demo sellers: seconds.

### New fields the APIs give that the catalogue didn't have (worth using)

- **Callback speed** (`callback_0to1_hrs` … `callback_gt_1day`) is a direct patience / responsiveness signal.
- **Buyer-rated responsiveness** (`thumbs_up_responsiveness_percent`).
- **Buyer-call pickup by hour band, per phone number.** This is the closest thing we have to "which number, when" for the callee.
- `buyer_reply_pct`, `pns_defaulter_count`, `seller_initiated_connects_*`, `total_whatsapp_enq_recv`.

---

## 3. Issues found (needs your help)

| # | API / host | What happened | Data points affected | Ask / workaround |
|---|---|---|---|---|
| 1 | **users.imutils.com** (`users/detail`, `minidetail`, `pnssetting`, `AccountManager`, `supplierrating`, `products/productfiltercount`) | HTTPS **times out**; over **HTTP** it answers but returns **403 "Token is Compulsory"**. With `token=1/2` or token = AK it returns "Invalid Token". **The employee AK is not enough**: these services need a **per-module service token** (`modid` + `token`). | A03 contact name, A04 designation, B05 language id, C07, F07 do-not-call hours, A05 number type | Ask the User SOA team (swagger SPOC: rahul.chowdhary@) for a `modid` + `token` pair for read access. Fallback: account managers from `byrsupplyapi` (works); names stay a gap |
| 2 | **leads.imutils.com**, **lms.imutils.com**, **bizfeed.imutils.com**, **top_mcat.intermesh.net** | **DNS does not resolve** from this laptop (the imdwh / users / mapi hosts do) | E04 BLs per MCAT (`seller_bl_count`), D03 (`user_selling_mcat`), F08 last seen, D01 active categories | Need internal DNS (office network / VPN DNS) or IPs. Fallback: `category_dtls`, `blsummarydetails`, `bl_summary` (all work) |
| 3 | **getContext** (exchange.intermesh.net) | Reachable, but keyed by `MappingID` / `source_uid`. A GLID gives **"Mapping Not Found"** | I02 renewal / NACH, I03 churn / risk, E02 last enquiry, G03 last call summary, ticket details | Ask the owner (LEAP models team?) how to look up by GLID. Fallback: scorecard complaint counts, files for last enquiry and last call |
| 4 | imdwh `c2cchart`, `getglactivitydata`, `prerenewal_api`, `prdtpageviewcnt`, `whatsapp_enq` | **404 on prod** (GET and POST); the sheet lists them, so they were probably renamed or retired | renewal (I02), page views, C2C chart | Ask the BI DWH team (swagger SPOC: shailendras@) for current paths. Not needed for P0 |
| 5 | imdwh `glusr_bl_detailsv2` | Always "The infr is mandatory", even when `infr` is sent; no matching doc | BL purchase per MCAT rank (18 months) | Ask the BI team for the body; `bl_summary` + scorecard cover most of it |
| 6 | imdwh `supplierperformance` | Needs an MCAT list + district list per call | — | Not needed |
| 7 | mapi.indiamart.com gateway | "Authentication Failed" (app auth) | — | Not needed (direct hosts are used instead) |
| 8 | MERP / BI-SOA | No base URL in the master sheet | DSR rows, meetings, VOC tickets | Not needed: `getgldsrcount` covers DSR |
| 9 | AK | JWT valid ~24 h (issued and expiring within a day). imdwh didn't need it | — | Don't store it; pass it per run through an env var (as done) |

---

## 4. Rules for using API data

1. **No as-of dates.** APIs return today's rolling windows (last week / month / 12 months). They **must not** be used to evaluate past calls (leakage). Use API values only for the **live demo / current context**. Files stay the source for evaluation and evidence (as-of rebuild, plan v5).
2. **PII:**
   - `byrsupplyapi.GL_DTL` (account-manager name / email / mobile), `nsdprepplus` competitor names, `getwaconv` free text, masked / hashed phone numbers.
   - Keep raw JSON in `data/api_cache/` only.
   - The normaliser keeps counts, rates and categories, and **tokenises** names.
   - **No GST / PAN / ID numbers** to any off-premises model (persona-team policy).
3. **Precedence:** current-state fields (plan, products, enquiries, PNS, ratings) → API. History (VANI calls, objections, memory facts, dial timing) → files. Every field records `src` and `fetched_at` in `field_sources`.
4. **Politeness:** ≤ 8 concurrent calls, 15 s timeout, 2 retries with backoff, resumable cache (skip GLIDs already fetched today).

---

## 5. Extraction pipeline

```
GLID list (demo sellers → GC 5,000 → all sample sellers)
   │
   ├─ FILE EXTRACT  (data/ → per-GLID rows, as-of filter)            app/context/seller_inventory.py → build_context.py
   │
   ├─ API FETCH     17 imdwh calls / GLID → data/api_cache/<endpoint>/<glid>.json  app/context/fetch_api.py (next)
   │                (bodies from extraction_map.ENDPOINTS; retries; cache; fetched_at)
   │
   ├─ NORMALISE     JSON → catalogue fields (DATA_POINTS), drop / tokenise PII
   │
   └─ MERGE         file fields + API fields → seller_context.json (+ field_sources, missing_fields)
```

| Step | Output | Owner | When |
|---|---|---|---|
| 1 | `fetch_api.py`: concurrent fetcher with cache + resume | M / S | D1 night |
| 2 | Fetch demo sellers (3–5), check shapes | M | D1 night |
| 3 | Normaliser per endpoint → catalogue fields (unit test on cached JSON) | M | D1 night |
| 4 | Merge into `build_context.py` with precedence and PII rules | M | D2 09:00 |
| 5 | Batch fetch for the GC 5,000 (8 workers, ~30 min) | M | D2 10:00 |
| 6 | Freeze demo contexts | team | D2 12:00 |
| 7 | Chase asks #1–#3 (token, DNS, getContext). If they arrive, add the endpoints to the map, re-fetch, and fill the gaps | team lead | D1–D2 |

## 6. Open asks (summary)

1. **User SOA service token** (`modid` + `token`) → unlocks contact name, designation, number types, do-not-call hours.
2. **Internal DNS / IPs** for `leads.imutils.com`, `lms.imutils.com`, `bizfeed.imutils.com`, `top_mcat.intermesh.net`.
3. **getContext by GLID**: owner and parameter.
4. Current paths for the five imdwh endpoints returning 404, and the `glusr_bl_detailsv2` body.
