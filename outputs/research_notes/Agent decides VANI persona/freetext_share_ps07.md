# How often does free-text call history change a VANI persona or call-plan decision? (PS07)

As of 2026-10-09. **Aggregates only.** No seller names, IDs, phone numbers, messages, or summary or transcript text appear here. Everything ran locally with Python regex and keyword rules. No LLM or API call touched the data.

Tags: **PROVEN** = computed by me on the local PS07 files on 2026-10-09. **DOCUMENTED** = stated in [raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md) or the earlier aggregate notes in `outputs/research_notes/Between run learning loops/`. **ASSUMED** = my definition or inference.

The scripts were throwaway and live in the session scratchpad (`.../scratchpad/freetext/`: `pats.py`, `extract.py`, `validate.py`, `analyze.py`, `extra.py`). They save only boolean flags per call, never text.

---

## Takeaway

- **About 3 in 10 "due" sellers (30.8%) have at least one decision-changing free-text fact in their earlier calls.** Adjusting for precision gives about 28.8%. Across all 130K sellers with an answered call the figure is 21.4%. PROVEN
- **Most of this is timing.** Callback-time requests (18.8% of due sellers) and personal constraints such as travelling, driving, out of station, in a meeting or unwell (14.0%) account for most of it. Structured fields already flag these calls as deferred: 85% and 77% of them carry a Call Later label or a `callback_requested` disposition. What the free text adds is *when* to call and *why* the seller deferred. PROVEN
- **"Durable" persona facts are rarer: 9.7% of due sellers (about 8.5% after precision).** These are facts that should still hold at the next run: another contact person, language, competitor or already-paid status, a specific business need, a complaint, or price and budget detail. PROVEN
- **Text rarely contradicts structured data: 3.0% of due sellers (9.9% of those with any fact).** The main contradiction is a Not Interested label on a call where the text shows a specific need (38% of specific-need calls are labelled NI), another contact person (16%), or a temporary constraint (8%). PROVEN
- **Summaries alone miss about a third of it.** 9.9% of due sellers have facts only in evaluator JSON or transcripts, not in the call summary. The evaluator `disposition.followup_when` field carries most of the extra timing facts. PROVEN
- Implication (ASSUMED): a free-text memory step is worth building, but its value is mostly a **scheduling and opening-line memory** ("you asked me to call after X", "is your son/partner available"). It is not a persona-trait signal. Durable trait-like facts reach about 1 in 10 due sellers. Language (0.26%) and competitor (0.56%) are too sparse to justify their own persona branches.

---

## 1. Method

### Sources per call (PROVEN coverage)
| Source | What I read (seller side only) | Coverage of answered calls |
|---|---|---|
| **S** summary | `lead_call_summary`, split into sentences. Sentences led by the agent are kept only from the first "lead/seller … said/asked/…" clause onward. | 95–99.6% every month |
| **E** evaluator JSON | `disposition` (reason, action_item, plus the structured-in-JSON fields `followup_when` and `alternate_number/person_name/designation`); `objections` (reasons + seller quotes); `execdrop` explanation; `seller_questions` (question context/dialogue, gap seller turns); `incorrect_mf` (summary, initial reaction, seller statements); `se_contact` (summary, seller quote). Bot dialogue, topics and location were excluded. | Apr 11.7%, May 18.8%, Jun 21.6%, Jul 62.0%, **Aug 99.3%**, Sep 63.8% |
| **T** transcript | `ps07_call_turns.csv`, seller turns only | Jul 9.0%, Aug 9.4%, Sep 0.2%, Apr–Jun 0% |

A matched unit is one sentence (S/E) or one seller turn (T). If the 90 characters before a match end in an agent speech verb ("the executive pitched / mentioned / offered …"), the match is dropped.

### Fact families (ASSUMED definitions; a fact counts only if the *specific detail* is in the text)
| # | Family | Rule (Hinglish / English / Devanagari) | Not counted (structured already has it) |
|---|---|---|---|
| f1 | Callback timing | a time expression (clock time, *kal/parso/shaam*, weekday, date, "next week", "after N days", festival names such as Diwali/Navratri/Raksha Bandhan) plus callback context in the same unit. Also `followup_when` with a specific value on non-meeting dispositions. | a bare "Call Later" label; meeting slots |
| f2 | Different contact | another/alternate/different number; a third-party role (son, brother, partner, owner, manager, accountant, staff, *malik*, *mera bhai*…) with handles / not available / talk-to context; non-NA `alternate_*` JSON fields. "No alternate number" negations, wrong-number calls and IndiaMART staff are excluded. | the `alternate_number_or_not_dm` category alone |
| f3 | Language | a non-Hindi language named with a speak/understand/prefer context, or "don't understand Hindi / Hindi nahi aati". A plain "spoke in Hindi" is excluded. | — (no structured language field) |
| f4 | Competitor / already paid | TradeIndia, JustDial, ExportersIndia, Alibaba, Amazon, Flipkart, Meesho, own website, other platform/company, "already paid/subscribed/has a plan" | `already_in_touch_with_im` alone |
| f5 | Specific need | export/import/international, bulk/wholesale/large orders, tenders/government, dealers/distributors wanted, "leads/buyers for <product>". Company-name uses ("X Exports"), the bot's "bulk or retail" question and negations are excluded. | — |
| f6 | Complaint | too many/repeated calls, "already told you", fake/irrelevant leads, no business from IndiaMART, bad past experience, fraud, *pareshan/bekar/faltu*, bot repeating | `do_not_call` / frustration flags alone |
| f7 | Personal constraint | driving, travelling, out of town/station, *bahar hoon*, hospital/unwell/accident, wedding/death, in a meeting, with customers, lunch/sleeping, shop closed, holiday | a bare Busy / Call Later label |
| f8 | Price detail | too expensive / high charges, can't afford, budget, financial difficulty, wants free plan only, not willing to pay, discount/EMI, rupee amounts | the `budget_issue_denial` category alone |

### Precision check (PROVEN by manual reading; text was read in the terminal only and not saved)
I read random matches per family across S, E and T, in 2–4 rounds of about 20 per family, tightening the rules between rounds. The figures below are for the final rules:

| Family | Est. precision | Main residual false positives |
|---|---|---|
| f1 callback time | ~90% | meeting slot read as callback; *kal* = yesterday |
| f2 other contact | ~85% (S/E/JSON ~95%, T ~65%) | seller asking for the bot's or an IndiaMART person's number; address terms in transcripts |
| f3 language | ~90% | place names ("Tamil Nadu"), company names |
| f4 competitor/paid | ~75% | "thought you were Meesho/Amazon" confusion; "other company" = the seller's own second firm |
| f5 specific need | ~70% | company names, seller is actually a buyer, bot speech mislabelled as seller turn |
| f6 complaint | ~88% | non-IndiaMART complaints, friend's experience |
| f7 personal constraint | ~95% | rare company names (e.g. "Surgery") |
| f8 price detail | ~93% | ambiguous rupee amounts |

Recall was **not** measured, so these shares are lower bounds for what an LLM extractor would find. ASSUMED

---

## 2. Results

### 2a. Share of calls and sellers (PROVEN)
| Family | % of all 269,455 calls | % of 130,129 sellers with ≥1 answered call | % of **due** sellers (35,794) | due %, precision-adjusted |
|---|---|---|---|---|
| f1 callback time | 6.45 | 11.44 | **18.76** | 16.9 |
| f2 other contact | 1.23 | 2.20 | 3.38 | 2.9 |
| f3 language | 0.11 | 0.21 | 0.26 | 0.23 |
| f4 competitor/paid | 0.23 | 0.46 | 0.56 | 0.42 |
| f5 specific need | 0.20 | 0.37 | 0.51 | 0.36 |
| f6 complaint | 1.60 | 2.94 | 3.84 | 3.4 |
| f7 personal constraint | 5.40 | 9.63 | **13.99** | 13.3 |
| f8 price detail | 0.79 | 1.51 | 2.26 | 2.1 |
| **any** | **13.24** | **21.43** | **30.76** | **~28.8** |
| durable (f2–f6, f8) | — | 6.97 | **9.68** | ~8.5 |

**Due proxy:** the seller's latest call is in Aug or Sep and the seller has ≥1 earlier call. History = calls before that latest call. The median is 2 prior calls. Restricting to targets at least 1 day after the last prior call (n = 17,700) gives nearly the same result: any 32.2%, durable 9.7%. PROVEN

Among due sellers with a fact, 65% have one family, 29% have two and 6% have three or more. PROVEN

### 2b. By source (due sellers, % with the fact found via that source; PROVEN)
| Family | S summary | E evaluator | T transcript | only E/T (not in S) | only S |
|---|---|---|---|---|---|
| f1 | 8.5 | 15.5 | 1.4 | 10.2 | 2.9 |
| f2 | 1.7 | 2.5 | 0.4 | 1.7 | 0.7 |
| f3 | 0.20 | 0.11 | 0.04 | 0.06 | 0.13 |
| f4 | 0.39 | 0.23 | 0.11 | 0.18 | 0.28 |
| f5 | 0.40 | 0.15 | 0.05 | 0.11 | 0.33 |
| f6 | 2.6 | 2.1 | 0.3 | 1.3 | 1.6 |
| f7 | 10.1 | 10.0 | 1.4 | 3.9 | 3.6 |
| f8 | 1.7 | 1.2 | 0.2 | 0.6 | 1.0 |
| any | 20.9 | 23.3 | 3.3 | **9.9** | 6.9 |

The hit rate per call with the source present (any family) is S 9.0%, E 13.6%, T 21.3%. Transcripts are the richest per call, but they cover only about 9% of Jul–Aug calls. PROVEN

### 2c. By month (% of calls with any fact; PROVEN)
Apr 8.6, May 10.1, Jun 12.9, Jul 14.2, **Aug 15.4**, Sep 12.0. The summary-only rate is flat (8.1–10.4%), so the rise tracks evaluator coverage (Aug 99%) and transcripts (Jul–Aug). The Sep drop follows evaluator coverage falling to 64% and transcripts disappearing (0.2%). A due seller's share is the same for Aug and Sep targets (30.8% vs 30.7%).

**Sep relabelling** (PROVEN): the Not Interested share of answered calls fell from 51% (Aug) to 19% (Sep), and General rose from 24% to 55%. The "NI label vs text" conflict rates by month therefore move with the relabelling, not with seller behaviour. For example, f5-on-NI was 55.5% in Aug and 30.7% in Sep.

### 2d. Recency (due sellers with the fact; PROVEN)
| Family | n sellers | % with fact in the **last** prior call | median age of newest fact (days) | % ≤30 d | % >60 d |
|---|---|---|---|---|---|
| f1 | 6,714 | 47.8 | 7 | 74.8 | 8.9 |
| f2 | 1,209 | 45.0 | 5 | 73.3 | 9.3 |
| f3 | 93 | 36.6 | 12 | 63.4 | 19.4 |
| f4 | 202 | 34.7 | 16.5 | 64.4 | 18.8 |
| f5 | 182 | 39.6 | 6 | 72.5 | 12.1 |
| f6 | 1,376 | 37.4 | 12 | 67.4 | 12.2 |
| f7 | 5,008 | 43.7 | 11 | 68.8 | 12.9 |
| f8 | 810 | 31.2 | 24 | 57.3 | 19.3 |
| any | 11,010 | 49.5 | 6.5 | 73.0 | 10.5 |

About half of fact-holding sellers have the fact only in an *older* call. A memory that keeps just the last call would lose it. Price, competitor and language facts are older (median 12–24 days) than timing facts. The gap between the last prior call and the target call has a median of 0 days (p75 18 days), so many "due" calls are same-day or next-day callbacks. "Fresh timing" (f1 or f7 in the last prior call and ≤14 days old) applies to 10.0% of due sellers. Durable facts or fresh timing together cover 18.4%. PROVEN

### 2e. Overlap and conflict with structured data (PROVEN)
Call level, among calls carrying the fact:
| Family | Structured already hints the category | Conflict with structured |
|---|---|---|
| f1 | 85.2% carry a Call Later label or `callback_requested` (the time itself is new) | **5.6% labelled Not Interested** |
| f2 | 50.9% carry `alternate_number_or_not_dm` (person/number new); at seller level, 40.7% of due f2 sellers lack it in `past_dispositions_detailed` | **15.9% labelled NI** (NI recorded from a non-decision-maker) |
| f3 | none; 23.7% of due language-fact sellers (26.4% of all) are in Hindi-belt states where a state default would choose Hindi | **state default wrong for about a quarter** |
| f4 | 7.5% carry `already_in_touch_with_im`; 31.8% NI | not a contradiction |
| f5 | none | **38.1% labelled NI**; 83% of due f5 sellers have `calls_not_interested>0` in the seller file |
| f6 | 9.1% carry `do_not_call`; 86.6% of due f6 sellers have `showed_frustration=0` and `do_not_call_requested=0` | structured mostly silent, not a contradiction |
| f7 | 76.8% Call Later / `callback_requested` | **8.1% labelled NI** (a temporary constraint recorded as disinterest) |
| f8 | 15.7% carry `budget_issue_denial`; 79% of due f8 sellers lack it in the seller file | structured mostly silent |

The seller-file `past_objections` column is filled for only 2.7% of sellers. Only 2.9% of due f1/f7 sellers show an "Unavailability / Callback" objection category, so the seller file almost never carries this information. PROVEN

**Any conflict at the due-seller level** (NI label on a call whose text has a callback time, another contact, a specific need or a constraint, or a Hindi-belt state plus a non-Hindi request): **3.0% of due sellers, 9.9% of due sellers with any fact.** PROVEN

---

## 3. What this means for the design (ASSUMED)
- **Build a typed "memory facts" extractor** for each finished call, with fields `callback_when`, `contact_person_role` / `alt_contact`, `language_pref`, `competitor_or_paid`, `need`, `complaint_type`, `constraint`, `price_detail`. Feed it summary + evaluator JSON (+ transcript when present). The summary alone loses about a third of what is found. In production the extractor would be the Sarvam/Jev LLM, but these regexes give a cheap baseline and a recall floor.
- **Keep a rolling history, not just the last call.** Half of fact-holding sellers would lose the fact if only the last call were kept. Decay timing facts fast (median age 7 days) and keep durable facts longer.
- **Let durable facts override structured labels.** Examples: an NI label followed by "son handles it" should go to the contact person, and an NI label on a "travelling" call is a reschedule. Do not let these facts change the persona *traits*. They change the plan (who, when, the opening reference, which objection to pre-empt).
- **Language and competitor facts are too rare to build persona branches on** (0.26% and 0.56% of due sellers). Handle them as plan-level flags. For language, state is a weak default: about a quarter of stated non-Hindi preferences come from Hindi-belt sellers, mostly English requests.
- Pitch for the slide: "about 30% of returning sellers carry a free-text fact our structured data doesn't; about 10% carry one that should still matter at the next run; about 3% would be mis-handled from structured data alone."

## 4. Limits
- Regex recall is unknown, so the shares are lower bounds. Precision comes from about 40–60 manual reads per family, not a labelled set.
- Evaluator coverage is uneven by month (Apr–Jun 12–22%), so older history is under-observed. Transcripts exist only for Jul–Aug (about 9% of calls) and include some bot turns mislabelled as seller.
- The "due" proxy is my definition. It includes many same-day callbacks (median gap 0 days).
- The Sep disposition relabelling distorts NI-based conflict rates by month.
- Seller-file aggregates (`past_*`) cover Apr–Sep and so leak the target call. I used them only to describe overlap, not to predict.
