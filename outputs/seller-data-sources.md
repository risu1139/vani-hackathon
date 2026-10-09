# Seller data sources: what each one provides

As of 2026-10-09. This is the master list for **B1 Seller context builder**. Details: [seller-context-apis.md](seller-context-apis.md) (every API, by need) · [aids-data-overview.md](aids-data-overview.md) (organiser folder, schema, aggregates).

**Rules.** Only schema and counts appear here: no seller names, messages or recordings. Offline files stay in git-ignored `data/`. Fields marked PII are masked before any off-premises LLM.
**Join key everywhere:** seller GLID (`fk_glusr_usr_id` / `seller_glid` / `glid` / `GLUSR_ID`).
**Evidence:** offline files were opened and counted by us (PROVEN). APIs come from docs and the master sheet only, never called (DOCUMENTED).

---

## 1. Source inventory

### 1.1 Offline files (organiser Drive)

| # | Source | Rows · sellers | In PS07 (149,363)? | Window | What it provides |
|---|---|---|---|---|---|
| O1 | **PS07 Persona dataset** (seller files, bot calls, evaluator outputs, call turns, recording sample, executive calls) | 149,363 sellers · 269,455 answered bot calls · 278,332 evaluator rows · 12,788 transcribed calls · 67,151 exec calls | — (is PS07) | 1 Apr – 30 Sep 2026 | Profile, turnover, categories, 90-day/1-year engagement counts, bot-call outcomes, past objections and questions, frustration / bot-question / DNC / already-with-executive flags, call summaries, recording URLs, turn-by-turn transcripts with timings, evaluator JSON (disposition, objections, seller questions, topics, latency/repetition, IVR …), bot version (trial arms) |
| O2 | **Global Context – Seller Dataset** (11 files) | 5,000 sellers | **5,000 / 5,000** | 1 Apr – 2 Oct 2026 | O1 profile **plus** company name, customer type, paid flag, listing status, KYC flags; enquiries with text, buyer details and read times; enquiry reply threads; buyer phone calls (per call); buyleads bought (per purchase); WhatsApp delivery/read events; WhatsApp chatbot text with intents; AI-extracted buyer-call details incl. **languages**; VANI calls and turns; executive calls |
| O3 | **Best-Time-to-Call** (attempts + sellers) | 530,748 attempts · 149,363 sellers | **149,363 / 149,363** | 1 Apr – 30 Sep 2026 | **Every dial attempt incl. unanswered**: lead-sent time, dial time, vendor response time, answered or not, duration, outcome, attempt number, hot-lead bucket, callback / next-retry time (`lead_tbro_time`); seller lat/long |
| O4 | **Seller Onboarding / Enrichment** (PS06) | 5,000 verified sellers | 151 | pulled 8 Oct 2026 | Verified profile incl. **`preferred_language_id`**, `contact_designation`, year established, employee band, GST partner names / legal status / turnover, member since; all categories with tree and rank flags; latest 50 products with price/specs; catalogue-health gaps; KYC documents + AI extraction; KYC field checks; seller locations. Reference: **category taxonomy (106,619 MCATs)** and category specs |
| O5 | `Call_Logs_Hackathon.csv` | 1,000 rows · 825 sellers | 2 | 5–8 Oct 2026 | LEAP BL-enrichment calls: disposition reason and remarks, answered flag, recording URL |
| O6 | `call_recordings.zip` | 714 MP3s | not checked | — | Bot-call audio (pace, tone, accent reference) |
| O7 | `Sarvam Prompt - Buyer Side VANI.docx` | ~1,600 lines | — | — | Production Sarvam prompt: role, language limits, per-turn procedure, instruction priority, ask limits, intent list, guardrails, Jinja variables |
| O8 | Call Quality Matrix (PNG) | 18 parameters | — | — | VANI QA rubric: looping (irritates the caller → fatal), dead air >5 s (8 s with noise), WER, outcome accuracy |
| O9 | Buyer-side Kibana logs (CSV) | 392 rows | 0 | Oct 2026 | Full response schema of the `getContext` API (A1) |

### 1.2 Live APIs (internal, keyed by GLID)

| # | Source | Domain | What it provides |
|---|---|---|---|
| A1 | **Global Context API** `getContext` | `exchange.intermesh.net/go/api/globalcontext/v1/x/` | One call, the whole seller picture. KYC / GST / plan / renewal / NACH / churn and risk flags / account managers; BL, catalogue and PNS metrics over week, 4-week, month and 3-month windows; last enquiry, last lead, last WhatsApp chats; last call summary; tickets; top-3 MCAT competitors. **PII.** Owner, auth and GLID input unknown |
| A2 | Customer Scorecard v1 / v2 | `imdwh.intermesh.net/api/go/` | About 90 monthly metrics (12 months): plan, PNS, BL credits and lapsed credits, BL speed, BLNI reasons, enquiries, lead-manager activity, ratings, complaints, catalogue quality, MCAT ranks, executive connects and meetings |
| A3 | Other DWH APIs | `imdwh.intermesh.net/api/go/` | BL summary/details, PNS chart (18 months + talk time), C2C chart, product mapping (top 50), MCAT/product details, enquiry charts, WhatsApp conversations, Prep Plus (local competition), DSR counts, pre-renewal |
| A4 | User SOA | `users.imutils.com/wservce/` | Name, city, company (PII), GST and other details, profile, ratings, PNS settings with off-hours, disposition log, account manager, TrustSeal |
| A5 | Buyleads SOA | `leads.imutils.com/wservce/` | Selling MCATs ranked A–D, negative and D-rank MCATs, BLs bought per MCAT (3 months), BL status, credits, transaction history, preferred cities, alert frequency |
| A6 | Product SOA | `seller.imutils.com`, `users.imutils.com/.../products/` | Full product listing; counts of approved / rejected / with image, price, ISQ; category data; RAG score |
| A7 | Enquiry / LMS / Bizfeed / Recommendation | `enq2.intermesh.net`, `lms.imutils.com`, `dev-bizfeed.imutils.com`, `dev-recommend.imutils.com` | Enquiries, conversations, contact counts, **last-seen time**, recent searches and categories |
| A8 | Category-ML | `top_mcat.intermesh.net`, `relatedmcat.intermesh.net`, raw IPs | Active categories of a seller ("for GPT industry knowledge"), MCAT recommendations |
| A9 | MERP / BI-SOA (no base URL in sheet) | ask MERP SOA | PNS details, call history, DSR call rows, welcome call, last meeting, active services, MCAT summary, complaints / tickets, BLNI report |

---

## 2. Context field × source

✔ = provides it · ~ = partial / proxy · — = no

| Context field | O1 PS07 | O2 GC | O3 BTC | O4 Onboard | APIs |
|---|---|---|---|---|---|
| City / state / pincode | ✔ | ✔ | ✔ + lat/long | ✔ + locations | A1, A4 |
| Seller / company name (PII) | — | ✔ company | — | ✔ company, GST partners | A1, A4 |
| Gender | — | — | — | ~ (`contact_designation`) | — (none found) |
| **Callee: designation of the account contact** | — | — | — | ✔ `contact_designation` (151 sellers) | ~ A4 `users/detail/` with `others=ALL` (column unverified) |
| **Callee: all numbers on the account + type** | — | — | — | — | ✔ A4 `users/pnssetting/` (primary / mobile / alternate / toll-free, PNS office-hours status); A4 `users/detail/` `all_contact_info=1`; A4 `users/otherdetail/` `Type=ContactDetails` (additional contacts) |
| **Callee: who actually picks up (role on past calls)** | ✔ evaluator `alternate_person_designation`, `alternate_number_or_not_dm`, `wrong_number`; transcripts | ✔ same for 5K sellers | — | — | — |
| **Callee: designation per number** | — | — | — | — | — (none found) |
| Business type, nature, GST year | ✔ | ✔ | ✔ | ✔ + year est., employees | A1, A4 |
| Annual turnover | ✔ slab | ✔ slab | ✔ slab | ✔ declared + GST | A1 (`gst_turnover`) |
| Plan / paid / customer type | — | ✔ | — | ✔ | A1, A2 (`service`) |
| Preferred language | — | ~ (`languages` from buyer calls, 1,388 sellers) | — | ✔ `preferred_language_id` (151 sellers) | — |
| Top categories (MCAT) | ✔ top 3 | ✔ top 3 | ✔ top 3 | ✔ all, with rank flags | A5 (A–D ranks), A8, A3 |
| Products | ~ count | ~ count | — | ✔ latest 50 + price/specs | A3 (top 50), A6 (all) |
| Active / approved / rejected products | — | — | — | ✔ catalogue health | A6 counts, A2 `live_prd_cnt` / `deactivated_prd` |
| BLs bought / BL types | — | ✔ per purchase (Aug–Oct, 254 sellers) | — | — | A5 per MCAT, A3 summary, A2 |
| BL credits lapsed / expired | — | — | — | — | A2 `bl_credit_lapsed`, A9 `showblreport` |
| Enquiries received | ~ counts | ✔ per enquiry + text + read time | — | — | A3, A7 (counts / summaries) |
| Buyer calls on PNS | ~ counts | ✔ per call + talk time | — | — | A3 PNS chart, A1 |
| VANI call history | ✔ full | ✔ (5K sellers) | ✔ all attempts | — | ~ A1 last call summary only |
| VANI unanswered attempts / timing | — | — | ✔ | — | — |
| Objections, questions, frustration, bot question, DNC | ✔ | ✔ | — | — | — |
| Executive (human) calls | ✔ | ✔ | — | — | A3 DSR count, A9 DSR rows, A4 account manager |
| WhatsApp | — | ✔ events + chatbot text | — | — | A1 last chats, A3 `getwaconv` |
| Complaints / tickets / ratings | — | — | — | — | A1, A2, A9, A4 |
| Renewal / NACH / churn risk | — | — | — | — | A1 |
| Last seen on IndiaMART | — | — | — | — | A7 Bizfeed |
| Local competition | — | — | — | — | A3 Prep Plus, A1 top-3 competitors |

---

## 2b. The callee: who we are calling and their designation

The seller (GLID) is a business account. **The person who answers** may be the owner, a family member or staff, and an account can have several numbers. VANI's opening, formality and pitch should fit that person, not just the business.

### What each source gives

| Need | Source | What we found | Status |
|---|---|---|---|
| Designation of the account's main contact | O4 `so_sellers.contact_designation` (e.g. Proprietor, Director) | Only 151 PS07 sellers | PROVEN (file) |
| Same, live | A4 `users/detail/` (tables `glusr_usr`, `glusr_usr_ext`, `GLUSR_USR_SOCIAL_CONTACT`). `others=ALL` returns all extra columns | A designation column is likely, since O4 got it from the warehouse, but it isn't shown in the docs. Needs an `AK` JWT | DOCUMENTED, field unverified |
| All numbers on the account | A4 `users/pnssetting/` (tables `iil_pns_setting`, `glusr_usr`, `glusr_usr_addt_contact`) | Every mapped number with `pns_type` and `pns_status` (office / non-office hours). **No name or designation per number** | DOCUMENTED |
| | A4 `users/detail/` `all_contact_info=1` | Every mobile, landline and fax number | DOCUMENTED |
| Additional contacts | A4 `users/otherdetail/` `Type=ContactDetails` / `CompRgst_AddtContactDetails` (`GLUSR_USR_ADDT_CONTACT`) | "Additional mobile number, email and address". Whether it has a person name or designation isn't shown | DOCUMENTED, fields unverified |
| Which number VANI dialled | — | Not in PS07, O2 or O3 (phone numbers removed) | GAP |
| **Who picked up on past VANI calls** | O1/O2 evaluator `disposition` JSON | See below | PROVEN (aggregate) |

**Conclusion.** No source gives a designation per number. We can get (a) the account contact's designation (O4 / A4, partly) and (b) the numbers with their type and office-hours status (A4). Who actually answers has to come from **past-call evidence** plus a **live check in the first turn**.

### Past-call evidence (PS07 evaluator, 150,821 disposition outputs)

- `disposition = alternate_number_or_not_dm` ("not the decision-maker / try another number"): **1,936 calls · 1,634 sellers**.
- `disposition = wrong_number`: **5,328 calls**.
- `alternate_person_designation` filled (the picker named someone else to talk to): **1,071 calls · 953 sellers**. Most common: owner 177, sir 120, husband 73, bhaiya 65, son 59, bhai 57, brother 45, boss 41, papa 40, beta 34, father 30, ladka 26, partner 24, malik 23, manager 18.
  - Grouped: **family member 48% · owner / boss / senior 44%** · staff 1% · other 6%.
  - Reading: when the DM is someone else, the person answering is **a family member** (the DM is husband / son / papa) or **staff** (the DM is owner / sir / malik / seth) about equally often.
- `alternate_person_name` filled 275 · `alternate_number` filled 267 (**PII**, stays in `data/`).

### Proposed `callee` block in seller context (B1)

```yaml
callee:
  account_contact_designation: Proprietor | Director | … | unknown   # O4 / A4 (others=ALL)
  numbers_on_account: 3                                               # A4 pnssetting (count only, no digits)
  dialled_number_type: primary | mobile | alternate | unknown        # needs the dialler to pass it
  past_pickup_role: decision_maker | family | staff | wrong_number | unknown   # from evaluator history
  referred_dm_designation: owner | husband | son | … | none          # last alternate_person_designation
  alternate_number_known: true | false                               # never the number itself
  evidence: [attempt_ids …]
```

### How the persona uses it

- **Opening:** if `past_pickup_role` is family or staff, open by checking who is speaking ("Kya meri baat {owner/malik} ji se ho rahi hai?") instead of pitching straight away.
- **Live switch (B8):** a cue such as "main unka beta bol raha hoon", "sir nahi hain", "owner se baat karo" or "wrong number" → a **gatekeeper mode** directive. This means: short, polite, no pitch; ask for the DM's callback time, or ask for permission to call the DM's number; log `alternate_person_designation`. This adds a sixth live signal to the five in PS04.
- **Formality:** the DM is addressed with "ji / sir" and a business pitch. Family and staff get a short message to pass on.

---

## 3. Extra data found only in the offline files

Checked against every API in the master sheet and the Big-Data docs: none of them returns these. They might exist in the warehouse; ask the BI team if one is needed live.

### 3.1 From PS07 (O1)

1. **Full VANI call history per call**: outcome, duration, summary, recording URL, hot-lead bucket, attempt number. The APIs give only the last call summary (A1).
2. **Turn-by-turn transcripts with timings** (12,788 calls). These are needed to build and test the mid-call switch lexicon and to measure pace and interruptions.
3. **Evaluator JSON per call**: disposition, objections, seller questions, topics, latency/repetition, IVR, incorrect meeting-fixed, executive drop, location confirmation.
4. **Seller-level past-call flags**: `past_objections`, `past_questions_asked`, `showed_frustration`, `asked_if_talking_to_bot`, `already_in_touch_with_executive`, `do_not_call_requested`, `past_dispositions_detailed`.
5. **Bot version / trial arms** (`main_vani`, `arrowhead`, `personalis` …). This is the only evidence of which persona choices worked.
6. **Executive calls per call** (status, duration, ring time).
7. **Who picked up on past calls** (evaluator `disposition`): `alternate_number_or_not_dm`, `wrong_number`, `alternate_person_designation` / `_name` / `alternate_number` (see §2b).

### 3.2 From Global Context (O2)

7. **Language spoken on real calls** (`gc_buyer_call_extractions.languages`, 1,388 sellers), plus products discussed, prices quoted, specs, stock status, intent.
8. **Enquiry text and buyer details**: product, keyword, buyer city/state/company/designation, source module; **time to first read** (responsiveness).
9. **Enquiry reply threads**: seller's reply text, template use, reply delay.
10. **Buyer phone calls one by one**: time, talk seconds, connected or not, caller circle, operator, MCAT. This gives the seller's own call-pickup pattern by hour.
11. **BLs bought one by one**: keyword, list position, MCAT rank, preferred location, distance (16 Aug – 1 Oct only).
12. **WhatsApp delivery and read timing** per message and campaign.
13. **WhatsApp chatbot conversations**: seller's own words, intent and confidence, feedback.

### 3.3 From Best-Time-to-Call (O3)

14. **Unanswered dial attempts** (261,293). PS07 has answered calls only.
15. **Dial timing chain**: lead sent → dialled → vendor response (trigger delay, retry gaps).
16. **Callback / next-retry time** (`lead_tbro_time`) and attempt sequence per hot lead.
17. Seller **latitude / longitude** (48% filled).

### 3.4 From Seller Onboarding (O4, only 151 PS07 sellers)

18. **`preferred_language_id`** (the mapping to language names is not documented).
19. `contact_designation` (Proprietor, Director …), `year_established`, `employees_id`, `member_since`.
20. GST partner names (PII), GST legal status and turnover from the government record.
21. All listed categories with tree, top-5, A-rank and primary-mapping flags.
22. Catalogue-health gaps (22 counters) and the latest 50 products with price, unit, MOQ, specs.
23. KYC documents with accept/reject labels and AI extraction; KYC field checks; Video KYC GPS vs GST address.
24. **Reference:** full category taxonomy (106,619 MCATs → 9,193 parent → 696 categories → 58 groups) and category spec fields with common options.

### 3.5 Other aids

25. Bot-call audio (O6), LEAP enrichment call remarks (O5), the production Sarvam prompt (O7), and the VANI QA rubric (O8).

---

## 4. Extra data found only in the APIs

- **Freshness:** values at call time, and any seller outside the samples.
- **12–18 month monthly trends:** scorecard, PNS chart, C2C chart.
- **BL credits** allocated, lapsed and current balance; BL consumption speed; BLNI reasons.
- **Ratings, complaints, tickets, CLM feedback.**
- **Account managers, renewal / NACH / payment plan, high-churn and high-risk flags.**
- **PNS settings incl. off-hours** (when not to call), **last seen** on IndiaMART.
- **Full product list**, approved/rejected counts, MCAT ranks A–D, negative / D-rank MCATs, preferred cities.
- **Competition:** local BL and seller counts, top-3 MCAT competitors.

## 5. How we use them

| Phase | Source | Why |
|---|---|---|
| Build, evidence, evaluation | O1 + O2 + O3 (offline) | Fixed as-of snapshot, no leakage, past outcomes known; demo and eval pool = the **5,000 O2 sellers** (all in O1 and O3) |
| Language choice | O2 `languages` → O4 `preferred_language_id` → state | Measured signal first |
| Opening timing cue | O3 per-seller pickup by hour | e.g. a short opener at busy hours |
| Live demo / freshness | A1 if access is granted; else A2 + A5 + A3 (PNS, products) + A7 (last seen) | Current values at call time |
| Name in greeting | A4 `minidetail` / A1 | PII: spoken only, masked before any LLM |

## 6. Open questions

1. A1 `getContext`: owner, auth, GLID → `mapping_id`, permission to use.
2. Mapping of `preferred_language_id` to language names (O4).
3. BI-SOA / MERP base URL; auth for the `imutils` / `imdwh` hosts; prod vs dev during the event.
4. API reachability from Daytona vs the VPN laptop.
5. Callee: does `users/detail/` `others=ALL` include a designation column? Does `otherdetail` `ContactDetails` carry a name or designation per extra number? Can the dialler (Sarvam outbound or our harness) pass **which number** is being dialled? Who issues the `AK` JWT for the users APIs?
