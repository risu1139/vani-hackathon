# Seller data strategy for the LLM call

As of 2026-10-09. Owner: the seller-data session. Scope: which seller data goes to the LLM that writes VANI's persona and call plan, how it is shaped, and what never goes in. Extraction: `app/context/SCRUBBER.py` (sources in `app/context/extraction_map.py`). Data points: [catalogue](plans/Seller%20context%20B1%20data%20catalogue.xlsx) (A01–K04 + G11).

**Who reads what**

| Reader | Gets | Never gets |
|---|---|---|
| **LLM (Claude**; locally via the Claude Code CLI, later inside the Daytona sandbox) | Compact seller context (≤ 8 KB, ~2–3K tokens): Tier 1 + as much Tier 2 as fits | Tier 3, scheduling data, ID numbers |
| **Sarvam** (Bulbul voice / Voice AI agent) | Only the short call variables the persona side compiles (opening, call plan, voice/pace/pitch, a few personalisation facts) | Any seller-context file |
| **Persona side, B2 builder** (peer) | Our JSON / `points.json`, mapped by their adapter | — |
| **Humans / debugging** | Full `.md` (everything, unmasked, local `data/` only) | — |

Coverage = % of the 100-seller test set (45 rich, 25 medium, 15 sparse, 10 cold, 5 onboarding) with a non-empty value, from `data/contexts/*.points.json`.
**as_of-safe** = `yes` for history from the offline files (dated, rebuilt before `as_of`); `no` for live API values (rolling "current" windows; exclude them when replaying past calls).

---

## 1. Principles

1. **Ground every persona choice.** Each value carries a data-point ID and a source; the LLM must cite IDs. An empty field means *unknown*, never zero or a guess.
2. **Previous calls are already known, and recent beats old.** Last 30 days: full discussion. 31–90 days: 300-character summary. Older than 90 days: content is ignored, but counts stay (n_prior_calls, outcome counts over all history).
3. **Scheduling is not a persona input.** No best time, pickup by hour, retries, callback slots or do-not-call hours (F04–F07, K02 are excluded). **Busy / call-later stays as evidence:** the outcome `call_later_busy` and a per-call `rushed` signal, with no times. Times inside summaries are replaced with `[time]`.
4. **States are dated evidence, not labels.** Per-call signal rows (G11) give counts and dates; the consumer decays them (≈ 30-day half-life) and decides the label.
5. **No government / bank ID numbers in any LLM input.** GSTIN, PAN, Aadhaar, IFSC and account numbers are scrubbed at write time (`scrub_ids`); flags and years stay. Names, business name and city stay, because they're needed for personalisation.
6. **Small and dense.** The compact context is ≤ 8 KB. Lists are capped (top 5 products, latest 2 enquiries, last 3 calls). Monthly series become one number or one trend.

---

## 2. Tiers

### Tier 1: must go to the LLM (persona-deciding)

| ID | Data point | Drives | Source | as_of-safe | Coverage |
|---|---|---|---|---|---|
| G03 | Last call + recent conversations (what was discussed) | continuity, do-not-re-ask, opening | ps07_bot_calls summaries | yes | 56% |
| G11 | Per-call signal rows (rushed, confused, frustrated, asked_if_bot, not_interested, not_decision_maker, wrong_number; dated) | pace, brevity, warmth, switch sensitivity | bot calls + evaluator + turns | yes | 56% |
| G01 | Call volume (90 d, 30 d, all-history count, cold flag) | cold vs warm opening, apology for repeat calls | ps07_bot_calls | yes | 89% |
| G02 | Outcome counts (all history + 90 d; call_later_busy kept) | objection plan, persistence | ps07_bot_calls | yes | 89% |
| G04 | Past objections and questions (90 d) | objection playbook | evaluator | yes | 0% in window* |
| G05 | Already met / in touch with executive, incorrect meeting; undated frustration / bot / DNC flags | guardrails, skip the pitch | evaluator; seller file | yes | 54% |
| G06 | Memory facts (contact person, language, competitor / paid, need) | personalisation, plan | summaries + evaluator + turns | yes | 7% |
| G07 | Speech style (words per turn, words/sec, repeats) | pace, brevity | turns; evaluator | yes | 11% |
| A02, A03 | Company name; contact name | greeting | users_detail (API); gc_profile | no / yes | 99%, 100% |
| A04 | Contact designation (Owner, Proprietor …) | formality, decision-maker check | users_detail; so_sellers | no | 43% |
| A06 | Past pickup role (decision maker / family / staff / wrong number) | callee check, gatekeeper handling | evaluator | yes | 51% |
| B01 | City, state | language default, local references | seller file | yes | 100% |
| B03 | Languages spoken on real calls | start language, Hinglish mix | gc_buyer_call_extractions | yes | 28% |
| B04 | Seller's script / English share on VANI calls | Hinglish mix, formality | turns | yes | 11% |
| C01–C03 | Business type, turnover slab, nature of business | formality, vocabulary, pitch tier | seller file | yes | 90–100% |
| C05 | Customer type / plan / paid | existing client vs prospect, tone | users_detail, scorecard, gc | no / yes | 100% |
| D01 | Top categories | vocabulary, personalisation | seller file; blsummarydetails | yes / no | 98% |
| D05 | Top products (name, price) | specific hooks | prd_mapping_api | no | 99% |
| E02 | Latest enquiries (product, buyer city, read or not) | strongest value hook | gc_enquiries | yes | 59% |
| H01, H03 | Executive calls (90 d), meetings done | don't conflict with the executive; follow-up | exec calls; dsr API; evaluator | yes / no | 100%, 13% |
| K01 | Call trigger bucket (why VANI is calling) | opening reason | btc / dialler | yes | 100% |

\*Objection and question labels exist for ~3% / ~14% of PS07 sellers, and none of the test set's fall inside the 90-day window. Keep the slot; it fills on live data.

### Tier 2: useful if space allows (fit, hooks, guardrails)

| ID | Data point | Drives | Source | as_of-safe | Coverage |
|---|---|---|---|---|---|
| E01 | Enquiries received (week / month / quarter) | value hook | topbar; seller file | no / yes | 96% |
| E03 | Responsiveness (callback speed, reply %, buyer-rated responsiveness, hours to first read) | patience prior | scorecard, byr, gc | no / yes | 90% |
| E04, E05 | Buyleads bought; credits lapsed | buylead pitch, pain point | gc; scorecard | yes / no | 14%, 13% |
| E07 | BL not-interested reasons | anticipate objection | scorecard | no | 1% |
| E08 | Local competition (counts only) | value hook | nsdprepplus | no | 95% |
| D02–D04, D06, D07 | Category ranks, product counts, catalogue gaps, approved / deactivated | catalogue hook | APIs; seller file | no / yes | 95–100% |
| C04 | Vintage (GST year, member since) | respect / tenure framing | seller file; users_detail | yes / no | 100% |
| C06 | Listing / KYC flags (booleans) | trust | gc; users_detail | yes / no | 100% |
| F01–F03 | Buyer-call (PNS) answer rate, talk time, pickup ratio (no hours) | patience, phone habit | glmisccount, pns_chart, seller file | no / yes | 54–100% |
| F08 | Last seen on IndiaMART | recency of engagement | users_detail | no | 100% |
| G08 | How calls ended (labels, who ended) | opener design | evaluator | yes | 51% |
| H02 | Account manager assigned (role only) | escalation target | byrsupplyapi | no | 99% |
| I01, I04 | Complaints; ratings and thumbs-up | empathy first; compliment hook | scorecard; byr | no | 1%, 35% |
| J01–J03 | WhatsApp read rate; chatbot intents; buyer-call extractions | channel offer, recent concerns | gc | yes | 71%, 77%, 28% |
| A07, B05, C07 | Salutation / gender as recorded; preferred language id; employees | — (only if present; never inferred) | users_detail | no | 2%, 7%, 32% |
| K03 | Festive-season flag | greeting | calendar | yes | — |

### Tier 3: full `.md` only (not sent to the LLM)

A01 (key), A05 (phone numbers and per-number stats: dialler use), B02 (pincode, lat/long, address), E06 (BL purchase speed detail), G09 (bot versions: evaluation, not persona), G10 (recording URLs), I02 / I03 (gaps with proxies only).

### Never in any LLM input

| What | Why |
|---|---|
| F04 best time, F05 unanswered attempts, F06 promised callback, F07 do-not-call hours, K02 attempt number, callback / time sentences | Scheduling is owned by another agent |
| GST, PAN, Aadhaar, IFSC, bank account and other ID numbers | Team data policy (`raw/hackathon/2026-10-09-team-decision-data-sharing.md`); scrubbed at write time |
| Calls older than 90 days (content) | Stale; counts only |

---

## 3. Signal definitions (G11, per answered call, last 90 days)

Each signal is a **count** of evidence hits, with `signal_sources` saying where the hits came from (`turns:n`, `summary:n`, `outcome:…`, `evaluator:…`) and the call's `date` / `days_ago`. Counts, not scores; the consumer decides thresholds and decay.

| Signal | Evidence | Test-set result (150 calls, 100 sellers) |
|---|---|---|
| `rushed` | outcome `call_later_busy`; evaluator sub-disposition busy / callback / dropped_mid_pitch; lexicon in seller turns (बिज़ी, जल्दी, अभी नहीं, बाद में, गाड़ी …) and summaries (busy, call later, not free, in a hurry) | 55 calls / 29 sellers |
| `not_interested` | outcome Not Interested; evaluator `not_interested` | 69 / 35 |
| `wrong_number` | evaluator `wrong_number` | 9 / 7 |
| `asked_if_bot` | lexicon (bot, robot, मशीन, recorded, इंसान …); summary "asked if … bot / automated" | 6 / 5 |
| `frustrated` | lexicon (परेशान, बार बार, मत करो, फालतू …); summary (agitated, angry, harassed, "not to call") | 5 / 4 |
| `confused` | lexicon (समझ नहीं, क्या मतलब, कौन सा, फिर से …); summary (confused, didn't understand) | 1 / 1 |
| `not_decision_maker` | evaluator `alternate_number_or_not_dm` or an alternate person named | 0 in test set (1,634 sellers in PS07 have it) |

Turns exist for only ~8% of sellers, so turn-based signals (confused, frustrated) are sparse. Summaries and evaluator labels carry most of the evidence.

---

## 4. Persona dimension → data

| Persona dimension | Primary data | Fallback when missing |
|---|---|---|
| Start language, Hinglish mix | B03 observed languages → B04 script share → B01 state | Hindi + medium mix |
| Formality, form of address | A04 designation, C01–C02 size, C04 vintage | "ji" + medium formality |
| Pace, brevity | G11 rushed (recent, decayed), G07 words per turn / sec, F02 talk time | normal pace, short replies |
| Warmth, empathy | G11 frustrated, G05 flags, I01 complaints, G02 repeat not-interested | medium warmth |
| Callee check | A06 past pickup role, A04 designation | ask once "kya meri baat {name} ji se ho rahi hai?" |
| Opening | K01 trigger, G03 last call, E02 latest enquiry, D05 product | trigger-based generic opener |
| Call plan / hooks | E02, D05, E01, E08, D06, H01 / H03 (executive, meeting) | category-level hook from D01 |
| Objection playbook | G04, G02 outcome mix, E07 BLNI reasons, G06 competitor / paid | standard IndiaMART objections |
| Guardrails | G05 (DNC / don't-call, already with executive), I01 complaints, G11 frustrated | default compliance rules |

---

## 5. Size budget for the compact context (≤ 8 KB)

| Block | Budget | Cap |
|---|---|---|
| Header (seller, trigger, data coverage, missing list) | 0.5 KB | — |
| Previous conversations (G03 / G11 / G02 / G05) | 3 KB | last call in full; 2 earlier calls at 300 characters each; signals as one line per call |
| Seller and callee (A, B, C) | 1.5 KB | one line per field |
| Products and demand (D, E) | 2 KB | top 5 products, latest 2 enquiries, counts as single numbers |
| Account and channels (F, H, I, J) | 1 KB | numbers only |

Measured today: the full `.md` is 22–98 KB (median 37 KB); the compact target is ≤ 8 KB.

---

## 6. Known gaps

- **Gender:** recorded for 2% only. Never inferred from names.
- **Observed language:** 28% (Global Context sellers only); otherwise the state default.
- **Transcripts:** ~8% of sellers, so speech style and turn signals are sparse.
- **Objections / questions:** rare and old in the test set.
- **Renewal, churn risk, which number is dialled:** no working source.
- **API values are "today"**, not as-of; they're marked `as_of-safe = no`.
