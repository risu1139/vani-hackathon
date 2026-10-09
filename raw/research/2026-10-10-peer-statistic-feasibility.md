# Peer statistic for the social-proof hook: feasibility (2026-10-10)

**Question.** Can VANI truthfully say "N sellers like you (same MCAT, same turnover band, similar AOV, your city/region) bought M buy leads last month"? This is the precondition set in `raw/hackathon/2026-10-10-team-decision-peer-comparison.md`.

**Method.** Read-only. Local offline index `data/index/sellers.sqlite` (PS07 seller file), cached imdwh API responses in `data/api_cache/` (E08 `nsdprepplus`), and small ad-hoc Redash queries on report/replica sources (pg-imblr ds 16; Redshift ds 8 tried once). Scratch scripts were kept outside the repo. Only aggregates are recorded here. No seller names, phone numbers, emails or GLIDs. The two demo sellers are referred to by row: Demo A is row 1 and Demo B is row 5 of `data/demo_glids.csv`.

## Bottom line
- **Feasible today, live, from one replica DB (pg-imblr, ds 16).** That DB holds the per-seller purchase log (`eto_lead_pur_hist`), the seller's GST turnover band (`glusr_gst_details`, the same bands as PS07 `annual_turnover`), city and state ids plus plan (`glusr_usr`), the seller-to-MCAT mapping (`glusr_usr_mcat_prd_count`), and the lead "Probable Order Value" (`eto_attribute`). Peer group, outcome and AOV can all be joined in one SQL query per seller, in roughly 10–60 s.
- **The PS07 file alone cannot do it.** It is a sample of about 149K sellers, and in it only 6.8% of sellers have 5 or more peers in the same MCAT × band × city. It also has no lead-purchase column.
- **City-level peers are usually too few.** National, same-band peers are plentiful. The usable sentence is therefore mostly "in your category and turnover band across India", and "in your city/state" only when the cell has at least 5 peers.

## 1. Data sources and status
| Source | What it gives | Status |
|---|---|---|
| `ps07_seller_file` (local, 149,363 sellers) | annual_turnover (GST band), top_category_1..3 (**names, not MCAT ids**), city/state, nature_of_business, eng_* (enquiries, PNS, meetings, sample only) | works, but it is a sample and has no purchase data |
| `gc_buyleads_bought` (local) | bought lead ids with dates | works, but covers only Global Context sellers (14,852 rows) |
| pg-imblr `weberp.eto_lead_pur_hist` (view) | one row per lead purchase: seller id (`fk_glusr_usr_id`), lead id (`fk_eto_ofr_id`, joins to `eto_attribute.fk_eto_ofr_display_id`), `eto_pur_date`, `eto_ofr_prime_mcat_id`, `user_matched_mcat_id`, `search_top_mcat_id`, type (B/C/T), mode (WEB/APP/Notif/MAIL), `eto_credits_used` | **works**. It is a rolling window: the earliest row seen was 2026-06-12, so about 4 months. A filter by seller id is fast. A 7-day all-India aggregate timed out; 1 day works |
| pg-imblr `glusr_gst_details.glusr_gst_annual_turnover` | GST turnover band: 0–40 L / 40 L–1.5 Cr / 1.5–5 Cr / 5–25 Cr / 25–100 Cr / 100–500 Cr / >500 Cr / NA | **works**. These are the same labels as PS07 `annual_turnover` |
| pg-imblr `glusr_usr` | `fk_gl_city_id`, `fk_gl_state_id`, `glusr_usr_custtype_name` (plan), `fk_glusr_turnover_id` (self-declared, a different scale from GST: 50 = up to 50 L … 600 = >500 Cr) | works |
| pg-imblr `glusr_usr_mcat_prd_count` | seller × MCAT mapping (product counts). This is the peer **denominator**: every seller in an MCAT, buyer or not | works |
| pg-imblr `eto_attribute` (Probable Order Value) | value range per lead, about 3-month window | works. On peer purchases in the last 30 days, 81% (Demo A MCAT) and 88% (Demo B MCAT) of buyers had at least one valued lead |
| pg-imblr `eto_ofr_purchase_analysis` | purchases with mcat/city/order_value_flag | works, but the value flag is almost always empty (4 of 509 demo rows). Not useful |
| pg-imblr `iil_supp_90day_lead_pur_count` | supplier_id → india_count | works, but **does not reconcile** with `eto_lead_pur_hist` (one demo seller: 5 vs 88). Its definition is unknown, so do not use it |
| pg-imblr `city_mcat_consumption` | supplier × MCAT × city count | no rows for any of the 10 demo sellers. Unclear, not used |
| Redshift `im_dwh_rpt` (ds 8: `fact_eto_lead_pur`, `dim_glusr_usr`) | DWH purchase fact | **blocked**: "could not send SSL negotiation packet: Resource temporarily unavailable" (tried once on 2026-10-10) |
| imdwh `nsdprepplus` (E08) | per MCAT group: total_bl, local_bl, hyperlocal_bl, local/hyperlocal/total paid sellers. Competitors: up to 10, each with competitor glusr id, company, custtype_name, member-since, city, distance_city | works (cached for the 10 demo sellers). **No turnover, AOV or purchases per competitor**, but the competitor ids join to pg-imblr (see §4) |
| Call Insights / PNS connector | PNS calls per seller/MCAT | not tested (connector needs OAuth; not available in this session) |

## 2. Proposed peer definition
**Peer of seller S** means another seller who:
1. is mapped to S's **main MCAT** (in `glusr_usr_mcat_prd_count`). Use the MCAT where S bought the most leads in the last 90 days, else S's top mapped MCAT. Sibling MCATs of one product family may be pooled (Demo A: Awnings + Retractable Awning);
2. has the **same GST turnover band** (`glusr_gst_details`). Sellers with band NA are excluded on both sides;
3. optionally has a **similar AOV**: peer median Probable Order Value within 0.5–2× of S's own (both computed from bought leads). Apply this only when S has at least about 10 valued leads;
4. is in the **same city**, if the cell allows (see the ladder).

**Fallback ladder** (stop at the first rung with at least 5 peers; the sentence names the rung's geography honestly):
1. same MCAT + same band + same city
2. same MCAT + same band + same state ("in <state>")
3. same MCAT + same band, national ("across India")
4. same MCAT + band ±1 step + same state
5. same MCAT + band ±1 step, national
6. otherwise: no peer line.

Geography is widened before the band, because the team decision makes the same band mandatory and the city only "preferably". Rung 4/5 must never cross into a band the seller would call "big distributors". In practice, cap the ±1 step at 5–25 Cr for small sellers, so a 0–40 L seller is never compared with anyone above 1.5 Cr.

**Outcome window.** Purchases with `eto_pur_date >= current_date - 30`. "Last month" in the spoken line means the last 30 days.

## 3. Coverage numbers
**PS07 sample (local, 129,473 sellers with both a category and a turnover band, out of 149,363).** The share of sellers with at least 5 peers in their cell is:
| Cell | cells | 0 peers | 1–4 | 5–19 | 20+ | ≥5 |
|---|---|---|---|---|---|---|
| top_category_1 × band × city | 105,911 | 72.9% | 20.4% | 4.9% | 1.9% | **6.8%** |
| × band × state | 86,289 | 53.0% | 31.0% | 12.3% | 3.7% | 15.9% |
| × band, national | 46,446 | 21.9% | 29.5% | 26.5% | 22.0% | **48.6%** |
| × city (no size) | 94,618 | 61.4% | 26.7% | 8.3% | 3.6% | 11.8% |
| category national (no size) | 27,891 | 10.0% | 22.6% | 29.1% | 38.3% | 67.4% |

- Ladder on a random sample of 5,000 PS07 sellers (peer if the category appears in the peer's top 3). The first rung reaching 5 peers was: city 12.3%, state 16.1%, national 39.0%, state ±1 1.5%, national ±1 9.8%, **none 21.4%**.
- **Bigger sellers have the thinnest cells.** National same-band coverage (≥5) is 60.4% for 0–40 L, 32.4% for 40 L–1.5 Cr, 25.4% for 1.5–5 Cr, 16.5% for 5–25 Cr, 3.7% for 25–100 Cr, and 0% above 100 Cr. Same-city coverage is 8.9% for 0–40 L and 3% or less for every other band.
- Turnover is blank for 16,005 (10.7%) and top_category_1 for 4,693 (3.1%). Category names: 29,376 distinct; cities: 978.
- PS07 is a sample. The live base is far larger: for Demo A's MCAT, `glusr_usr_mcat_prd_count` maps 2,272 sellers against 2 in PS07 at national same-band level. **So production must use the live tables, not PS07.**

**Live (pg-imblr), one day of purchases (yesterday).** There were 546,280 purchase rows by 196,492 distinct sellers, across 30,383 lead MCATs.
- `eto_ofr_prime_mcat_id` is NULL on 64% of rows (almost all WEB-mode purchases).
- Using `coalesce(eto_ofr_prime_mcat_id, user_matched_mcat_id, search_top_mcat_id)` leaves about 24% unattributed. Those are mostly WEB.
- **A per-MCAT count therefore undercounts, unless it uses the coalesce or the lead's own MCAT from the lead master table (not tested).**

## 4. Sample peer statistics (aggregates only)
All counts are for the last 30 days, run on 2026-10-10. The MCAT filter uses the coalesce above.

**Demo A.** Telangana service provider, GST band 0–40 L, CATALOG plan. Main MCAT: Awnings + Retractable Awning (by own purchases). Own figures: 25 leads in this MCAT in 30 days (70 leads in all MCATs); own AOV median about Rs 20,750 (36 valued leads, 90 days).

Peers = sellers mapped to the MCAT, same band. "Bought" means at least one lead in any MCAT:

| Rung | peers | bought | leads | median per buyer |
|---|---|---|---|---|
| city | 15 | 5 | 293 | 40 |
| state | 23 | 5 | 293 | 40 |
| national | 867 | 182 | 11,834 | 51.5 |

Buyers of leads in this MCAT, same band:

| Rung | sellers | leads | median per seller | peer AOV median |
|---|---|---|---|---|
| city | 4 | 29 | 6 | about Rs 23,000 (n=3) |
| national | 94 | 667 | 5 | about Rs 14,500 |
| national + AOV 0.5–2× | 46 | 449 | 7 | about Rs 19,750 |

- Band mix of all 180 buyers of this MCAT: 94 at 0–40 L, 52 at 40 L–1.5 Cr, 15 at 1.5–5 Cr, 7 at 5–25 Cr, 3 at 25–100 Cr, 9 NA.
- **Truthful line (rung 1, city, mapped peers):** "Your city has 15 sellers in awnings with a business size like yours; 5 of them bought buy leads in the last 30 days." The category-specific city cell (4 buyers) is below 5. So, for leads in this MCAT, use the national line: "94 sellers of your size across India bought 667 awning leads last month; a typical one bought 5." Demo A already bought 25, so the honest framing is "you're already ahead of most sellers your size", not "others are using it".

**Demo B.** West Bengal wholesale trader, GST band 40 L–1.5 Cr, CATALOG plan. Main MCAT: Dolomite Powder. Own figures: 11 leads in this MCAT in 30 days; own AOV median about Rs 1,900 (21 valued leads).

Mapped peers, same band:

| Rung | peers | bought | leads | median per buyer |
|---|---|---|---|---|
| city | 1 | 0 | – | – |
| state | 14 | 3 | 153 | 42 |
| national | 379 | 117 | 9,317 | 52 |

Buyers of leads in this MCAT:

| Rung | sellers | leads | median per seller | peer AOV median |
|---|---|---|---|---|
| city, same band | 0 | – | – | – |
| state, same band | 0 | – | – | – |
| state, band ±1 | 4 | – | – | – |
| national, same band | 49 | 390 | 4 | about Rs 10,750 |
| national + AOV 0.5–2× | 9 | 32 | 3 | about Rs 1,575 |

- Band mix of the 238 buyers: 32 / 49 / 78 / 57 / 15 / 4 / 1 / 2 (0–40 L … >500 Cr, NA). 41% are above Demo B's band, which is exactly the "big distributor" risk.
- **Truthful line:** the national rung only: "Across India, 49 dolomite-powder sellers of your size bought 390 leads last month." The AOV-matched group (9 sellers) is the closest like-for-like match. A state or city line is not allowed.

**E08 competitors for the same two demo sellers.** The ids were joined to pg-imblr:
- Demo A: 10 competitors, 7 in the same band and 3 one band up. All 10 bought leads in the last 30 days (about 1,100 leads in total, all MCATs).
- Demo B: 6 competitors: 3 at 0–40 L, 2 in the same band, 1 at 5–25 Cr.

So the E08 list is a nearby **heavy-buyer** set with mixed bands. It is useful only after filtering by band, and too small to be a statistic on its own.

## 5. What we can truthfully state
- The number of same-band sellers in the seller's MCAT (and city/state/India) who bought at least one buy lead in the last 30 days, and the total and median leads they bought. Purchases may be counted in this MCAT (purchasers of the MCAT's leads) or in any MCAT (mapped peers).
- The share of same-band sellers in the MCAT who bought any lead (Demo A national: 182/867 = 21%).
- The typical peer AOV (median Probable Order Value of leads peers bought), and the seller's own AOV against it.
- The seller's own position against peers (above or below the median).
- **Paid vs free: only coarse.** The plan name comes from `glusr_usr_custtype_name` (e.g. CATALOG vs FCP variants). `eto_credits_used` is a flat 200 per lead in the sample, so it says nothing about money spent. `eto_cust_purchase_hist` (amount paid for credit packs) exists but was not tested.

## 6. What is impossible or not supported
- **What peers earned, or which orders closed.** No order or revenue data per lead. "Probable Order Value" is the buyer's stated range, not a sale.
- **"Leads consumed / replied / converted" for peers.** `eto_lead_pur_read_status` / read_date were empty on all demo rows. Enquiries, PNS calls and meetings per peer exist only in PS07 `eng_*` (a sample: 18.8% of PS07 sellers have non-zero 90-day enquiries, 3.3% have meetings in the past year). There is no live per-peer source in the tested replicas. The PNS connector is untested.
- **"Last calendar month" beyond about 4 months.** The `eto_lead_pur_hist` replica keeps a rolling window from mid-June. Longer trends need the Redshift DWH, which is blocked.
- **City-level claims for most sellers.** Even on the live base, same-band city cells are tiny (Demo B: 1 peer). At 25 Cr and above, even national same-band cells are thin.
- **All-India precomputation in one query.** A 7-day all-seller aggregate timed out on the replica. A nightly per-MCAT batch (or per-seller on-demand queries, about 10–60 s each) is the workable pattern.
- **Naming individual competitors' purchase counts.** We can, technically, but we should not. Say only aggregates of at least 5 sellers in the call.
