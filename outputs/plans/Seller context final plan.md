# Seller context and LLM prompt: final plan

As of 2026-10-09 (hackathon day 1, evening). Owner: the seller-data session. Supersedes [B1 implementation plan](Seller%20context%20B1%20implementation%20plan.md) and [extraction plan](Seller%20context%20extraction%20plan.md) where they differ. Evidence: [call-flow-analysis](../call-flow-analysis.md), [call-flow-playbook](../call-flow-playbook.md), [llm-data-strategy](../llm-data-strategy.md), our tests this session.

**Scope (unchanged):** data extraction, data strategy, what data goes to the LLM, and the LLM prompt. The persona composer, the Sarvam call variables and the live switcher belong to the persona session (plan v6). LLM = Claude (Claude Code CLI now, inside the Daytona sandbox later). Sarvam API = voice only (Bulbul, Voice AI agent).

---

## 1. What we learned

**About the calls (70 bot calls + 1 human call read; patterns checked on 12,354 transcribed calls)**
1. **Only 22% of calls end in a meeting.** The bot has one goal and one script; the four variants differ only in the opening hook.
2. **The first 20 seconds decide the call.** Identity check, introduction, a data hook and the meeting ask all arrive before the seller has spoken. Sellers who did not follow the hook needed 3–5 extra turns.
3. **Hooks must be true.** When the hook assumed something the seller had not done ("you were exploring paid services"), the seller said "no" and the bot had to recover. One call told a seller "you called us 15 times"; the seller denied it.
4. **Most failures are behaviour, not missing data:** repeating the same line up to 6 times, refusing a seller who was only free at 4–8 AM because "meetings are 11–5", carrying on after anger, doing 17 turns of arithmetic on request, claiming to be human (24 calls) or "a branch manager" (279 calls).
5. **Sellers raise 12 recurring objections** (busy 17%, no interest 10%, confusion 9%, price 8%, phone-only 5%, already met an executive 4.5%, owner decides 2.5%, bot question 2.4%, …). Sellers who ask about price convert best (33%).
6. **A human executive used account facts** (two years on a free account, average lead quality), gave a real reason for meeting in person, and honestly refused to invent proof. The bot knows the city and an enquiry count only.
7. **Social proof (naming nearby sellers) and offering an online meeting are unproven.** The numbers look worse, but the bot uses both only after resistance; this needs an A/B test.
8. **Outcome labels are noisy** (4 of the first 20 contradicted the transcript); 585 transcripts have duplicated turns; transcripts exist for only ~8% of sellers.

**About our data and tooling**
9. **Most of our 66 data points never appear in a real call.** The bot and the human use: business name, contact name, city, product / category, enquiry counts, account tenure and free-or-paid, profile gaps, past executive contact.
10. **Old VANI call history was the heaviest and weakest part** to build (sparse transcripts, noisy labels, dated). It is out of scope (your decision).
11. **APIs:** the data-warehouse APIs (imdwh) work on production with no auth; the users APIs need a service token (works with `modid=GLADMIN`); the leads, LMS and Bizfeed hosts do not resolve; five imdwh endpoints return 404. We call 24 APIs per seller; 8 of them feed everything we need.
12. **LLM tests:** Sarvam's chat model needed reasoning switched off, cited data-point IDs that do not exist, and mixed script. Claude is the LLM. A 20K-token context is too large; 8 KB (2–3K tokens) is enough.
13. **Verifiable claims are the safest design:** if the LLM may only state facts from a pre-computed list, with the source of each, it cannot say "you called us 15 times".

---

## 2. Decisions: add, drop, keep

### 2.1 Drop

| What | Why |
|---|---|
| **G01–G11: all old VANI call history** (summaries, outcomes, objections, per-call signal rows, speech style, endings, bot versions, recordings) | your decision; heaviest and weakest data; it also pulled scheduling-adjacent content back in |
| Scheduling: F04–F07, K02, clock time, callback / busy as outcome | another agent's job |
| Full `.md` appendices (done); full 62-point `.md` as the LLM input | too large; replaced by the compact context |
| A05 numbers and per-number pickup, F07 office hours, B02 address / lat-long / pincode, G10 recordings | PII and scheduling; not used in calls |
| J02 WhatsApp chatbot text, J03 buyer-call extractions (except languages → B03), I02 / I03 empty gaps, A07 gender (2% filled, never inferred), B05, E07, I01 (1% each) | low coverage, no observed use |
| F01–F03 buyer-call (PNS) answer rate, talk time, pickup ratio | phone habit; scheduling-adjacent; not used in calls |
| 16 of the 24 API calls (pns_chart ×2, glmisccount, bl_summary, bl_chart, mcat_rank, mcat_names, category_dtls, wa_conv, query_dtls, query_sum, users_contacts, users_pnssetting, products_filtercount, scorecard weekly) | nothing in the compact context needs them |
| Sarvam chat LLM tests (`sarvam_context_test.py`, the LLM turn in `voice_call_sim.py`) | Sarvam is voice-only; Claude is the LLM |
| Social proof as a default hook | unproven; keep as an optional, flagged hook |

### 2.2 Keep (Tier 1: must reach the LLM)

| ID | Data | Used for |
|---|---|---|
| A02, A03, A04 | company name, contact name, designation | identity check ("kya aap {name} se…"), form of address |
| B01 | city, state | hook; language default |
| B03 | languages seen on real calls (28% of the demo pool) | start language; Hinglish mix |
| C01–C03 | business type, turnover slab, nature of business (manufacturer / trader …) | formality; manufacturers want orders, not profile work |
| **C04 + C05** | **account tenure + free or paid + plan** | the human's strongest lever; "I've been free two years" is a known objection |
| D01, D05 | category, top products (name, price) | personalised hook; discovery question |
| **D06** | **profile gaps** (photos, price, description missing; quality score) | this is the actual pitch ("a few things are missing") |
| E01 | enquiries received (week / month / quarter) | answers "no enquiries have come"; a seller with 0 must not hear "you got N" |
| **E08 counts** | local / hyperlocal buylead counts and paid-seller counts in the seller's category | the verifiable source of the "N+ enquiries in {city}" hook |
| E02 | latest enquiry (product, buyer city) | concrete hook (demo-pool sellers only) |
| **H01, H03** | executive calls, meetings done | "already met an executive" (4.5% of calls) |
| K01 | call trigger bucket | decides which hook is **true** |
| DNC flag (seller file `do_not_call_requested`) | compliance | a **hard gate before the call**, outside the LLM |

### 2.3 Keep (Tier 2: if space allows) and Tier 3 (full `.md` only)

**Tier 2:** C04 vintage detail, C06 KYC flags, D02–D04, D07 catalogue counts, E03 responsiveness, E04 / E05 buylead purchases and lapsed credits, E08 competitor names (flagged "not proven"), F08 last seen, H02 account manager role, I04 ratings, J01 WhatsApp read rate.
**Tier 3 (full `.md` only, never sent to the LLM):** all PII not needed for personalisation, A01 key, raw API fields.

### 2.4 Add

| New item | Why | Source |
|---|---|---|
| **`verified_facts`**: a pre-computed list of statements the LLM may say, each with its source and a "safe to say" rule. Example fields: "{N} buyer enquiries in {city}, category {X}" (E08 counts); "{n} of your {m} products have no photo" (D06); "you have a free account since {year}" (C04, C05); "you received {n} enquiries in the last 30 days" (E01) | prevents invented or false claims (the "15 calls" call); the LLM may not state anything outside this list | built by SCRUBBER |
| **Trigger → hook table** (K01): PIM = explored paid services; PUA = checked buy leads; PAM = tried to pay, not completed; SCHD = booked a demo; NUR = recently registered; OLP = tried to buy a lead; UA = unknown, use enquiry hook | hooks must be true; the table says which hook each trigger may use | PS07 bucket meanings + our data dictionary; **confirm with the business** |
| **Executive-contact status** (derived): none / met / in touch | one of the 12 objections; changes the opener | H01, H03 |
| **Seller-type hints** (derived): manufacturer / trader / service; "mostly a buyer" | the pitch for a manufacturer is orders, for a buyer sourcing | C03 |
| **Prompt-side content** (not seller data): the 12-objection playbook, the stop rules, the AI-disclosure line, the supported-language list, one approved price statement | the largest failures are behaviours | from the playbook; **price statement and languages need an owner** |

---

## 3. The compact LLM context (≤ 8 KB, about 2–3K tokens)

Built per seller by SCRUBBER as `<glid>.llm.md`. Order is the order the LLM needs it:

| Block | Content | Budget |
|---|---|---|
| 1. Call | trigger bucket and the hook it allows; executive-contact status; DNC gate result | 0.5 KB |
| 2. Seller | company, contact name + designation, city / state, business type, turnover slab, nature of business, seller-type hint | 1 KB |
| 3. Account | free or paid + plan, tenure, ratings, account-manager role | 0.5 KB |
| 4. Business | category, top 5 products (name, price) | 1 KB |
| 5. **Verified facts** | the list described in §2.4 (each fact, its source, the exact phrasing allowed) | 2 KB |
| 6. Language | languages seen, state default, supported languages | 0.5 KB |
| 7. Demand | enquiries received (week / month / quarter), latest enquiry (if any) | 1 KB |
| 8. Missing | fields not available (so the LLM says "unknown") | 0.5 KB |
| Spare | tier 2 items that fit | 1 KB |

IDs scrubbed (GST, PAN, Aadhaar, IFSC, account numbers). The full unmasked `.md` stays local.

---

## 4. The LLM prompt (versioned file `prompts/seller_persona_v1.md`)

**One LLM call per seller:** `claude -p` with the prompt and the compact context, JSON out. Output = the persona and call plan (language, formality, brevity, opening line, hook, objection handling, stop rules), every choice citing a context block and a verified fact.

**Prompt sections**
1. **Role and honesty:** you plan how VANI speaks; VANI is an AI assistant and must say so when asked; no titles, no branch, no claim of being human.
2. **Facts rule:** state only what is in `verified_facts`; if a fact is not there, ask or say it is unknown.
3. **Hook rule:** use the hook the trigger allows; never assume an action the seller did not take.
4. **Opening:** identity check by company or contact name; one hook; at most one ask; short first turn.
5. **Objection playbook:** the 12 objections with the move that worked and the move that failed (from the playbook). Max two asks per objection, then change approach or close.
6. **Stop rules:** anger, "don't call again", "I'll complain", wrong number, off-topic demand → apologise once and close.
7. **Meeting format and window:** state the window once; offer a phone or online meeting to a busy or travelling seller; never fix the time (scheduling is another agent's job).
8. **Language:** match the seller's language; if unsupported, say so.
9. **Output schema:** JSON with citations; native script for spoken text.

**Output checks (code, not the LLM):** valid JSON; every cited ID exists in the context and is filled; no statement outside `verified_facts`; no time words; no human-claim or title phrases; Devanagari for Hindi lines; opening ≤ 30 words.

---

## 5. Build order

| # | Step | Output | Done when |
|---|---|---|---|
| 1 | **Apply the drops:** remove G and the dropped points from SCRUBBER's output; cut the API fetch to the 8 needed calls (users_detail, byr_supply, scorecard_m, prd_mapping, topbar, prepplus counts + competitors, dsr_count) | `app/context/SCRUBBER.py` | rebuild on the 100 test sellers; 8 API calls per seller; no G in `.md` or `points.json` |
| 2 | **Add `verified_facts`, trigger→hook, executive status, seller-type hint** | SCRUBBER | each fact has a source; spot-check 10 sellers against raw data |
| 3 | **Compact `.llm.md` builder** (≤ 8 KB) | `<glid>.llm.md` | all 100 within 8 KB; rich and cold sellers both read well |
| 4 | **Prompt v1** | `prompts/seller_persona_v1.md` | passes the output checks on 5 sellers |
| 5 | **Replay test:** feed the *real seller lines* from the 70 read calls to the prompt, turn by turn (Claude plays VANI), and compare with what the old bot said | `outputs/replay-results.md` | zero human-claims, zero denials, no repeated asks beyond two, stop rules fire on the angry calls |
| 6 | **5 demo sellers** (3 rich, 1 sparse, 1 cold) + 1 with an executive already met | list + their `.llm.md` | the persona session has the paths |
| 7 | **Output-format doc** for the persona session: every field, source, as_of-safe flag | `outputs/seller-context-format.md` | sent to the peer |
| 8 | **Voice demo** (Bulbul only): voice the Claude replies for the 2–3 contrasting sellers | `data/calls/` audio | one mid-call adaptation heard |
| 9 | **Freeze** | tagged commit | **D2 12:00** |

Order for tonight: 1 → 4. Tomorrow morning: 5 → 8. Freeze at 12:00.

**Test criteria for the whole thing**
- **Groundedness:** 100% of stated facts are in `verified_facts`.
- **Behaviour:** on the 70 replayed calls, 0 human-claims, 0 AI denials, ≤ 2 repeated asks per objection, stop rule fires on every anger case.
- **Coverage:** Tier 1 filled for ≥ 90% of the demo pool except B03 (28%) and E02 (59%), which fall back to state and enquiry counts.
- **Size:** compact context ≤ 8 KB, prompt + context ≤ 3.5K tokens.

---

## 6. Interface with the persona session

| Item | What changes for them | Action |
|---|---|---|
| **G11 per-call signal rows are dropped** (your decision) | their trait / state builder (B2) was going to read them for rushed, confused, frustrated, asked-if-bot | **tell them**; they can compute states themselves from PS07 on their side, or drop those states. I will not decide for them |
| Scheduling fields dropped | already agreed | none |
| New: `verified_facts`, trigger→hook table, executive status | optional inputs for their composer | send the format doc (step 7) |
| Compact `.llm.md` and 5 demo GLIDs | they asked for both | send when ready |
| Prompt `seller_persona_v1.md` | they may reuse or replace it in their composer | offer; do not edit their files |

---

## 7. Risks and open items

| # | Item | Owner | Needed by |
|---|---|---|---|
| 1 | **One approved price statement** (or a rule to say none) | business / team lead | D2 morning |
| 2 | **Supported voice languages** (Hindi and English work; Tamil switch worked; Odia failed) | Sarvam voice config / team lead | D2 morning |
| 3 | **Trigger bucket meanings** (UA, PAM, SCHD, NUR, OLP) confirmed | business | D2 morning |
| 4 | The **DNC gate** is enforced by the dialler, outside the LLM | persona / dialler side | demo |
| 5 | The **AK is valid ~24 h**; the users service token is shared; both come from env vars | us | each run |
| 6 | Social proof and the online-meeting offer stay **unproven**: use as options, not defaults, until A/B tested | — | after the event |
| 7 | API values are "today", not as-of: evaluation on past calls must use the file-only mode | us | — |
| 8 | If data access for any API fails on demo day: the file-only `.llm.md` still has Tier 1 except account and tenure | us | demo |

**Decisions I need from you:** (a) approve the drops in §2.1 (especially G, and cutting the API calls from 24 to 8); (b) who owns items 1–3 above; (c) OK to tell the persona session about the G11 change.
