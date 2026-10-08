# Pre-call Persona and Seller-Context Block (VANI PS07)

As of 2026-10-08. Aggregates only: no seller names, messages or transcripts appear here. Evidence tags:
- **PROVEN**: computed by us on local data, or tested hands-on in a spike.
- **DOCUMENTED**: vendor docs or a published source.
- **ASSUMED**: our inference.

Internal sources:
- **[INT-A]**: the new aggregate run for this note. The scripts are `persona_block_analysis.py` and `a2.py`–`a5.py` in the session scratchpad. They run over `data/Persona Files/...` (269,455 answered bot calls Apr–Sep 2026; 149,363 sellers; 11,834 transcribed calls; 150,821 disposition, 4,126 objection and 2,826 seller-question evaluator outputs) and over `data/Global Context - Seller Dataset/gc_*` (5,000 sellers, 9,657 bot calls).
- **[INT-VAL]**: [persona-data-validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md).
- **[SPIKE]**: [2026-10-07 spike log](../../../raw/research/2026-10-07-spike-log.md).
- **[CAT]**: [voice catalogue](../../../raw/research/2026-10-07-sarvam-voice-catalogue.json).
- **[PRIOR]**: [persona_generator_language.md](../VANI%20adaptive%20persona%20architecture/persona_generator_language.md).

Signals (rush/frustration/confusion/bot-question) come from the same romanized keyword lexicon as INT-VAL (`app/validate/profile_persona.py`), standing in for Jev labels.

---

## Q1. Which seller features best predict mid-call signals and outcomes?

### Takeaway
The strongest pre-call predictor by far is **call history with VANI**, i.e. the previous call's disposition and how many times the seller has been dialled. Static profile traits come next: turnover, GST age, business type and nature of business each move meeting rate by 2–5 pts. Language zone barely moves outcomes, though it matters for language fit. Archetypes should therefore be cut first on *history state* and then on *business size/maturity*, with language as a separate overlay rather than an archetype.

### Cited Findings
**Previous-call disposition → next call (PROVEN [INT-A])**
- Data: 269,455 answered calls, each seller's calls ordered by time; strictly earlier calls only, so no leakage.

| previous call | calls | meeting-fixed % | not-interested % | call-later % |
|---|---|---|---|---|
| none (first call) | 130,129 | 17.4 | 41.1 | 17.2 |
| Meeting Fixed | 8,258 | 21.7 | 34.5 | 17.9 |
| Call Later / Busy | 29,213 | 8.1 | 43.8 | 27.7 |
| Not Interested | 57,440 | 4.4 | 67.1 | 11.9 |
| General (talked) | 44,415 | 3.7 | 19.6 | 10.8 |

- Reweighting to a common lead-type mix (`redis_bucket`) or bot-version mix leaves these within ±0.7 pt (e.g. first call 17.4→17.5, prev-NI 4.4→4.5).

**Repeat dialling (PROVEN [INT-A])**
- Meeting rate falls with the number of earlier answered bot calls: 0 → 17.4%, 1 → 8.6%, 2–3 → 5.7%, 4+ → 2.9%.
- Not-interested rises over the same steps: 41.1 → 44.1 → 44.9 → 46.8%.

**Shallow decision trees (depth 4) (PROVEN [INT-A])**
- On all calls:
  - Meeting-fixed: previous disposition carries 0.74 of feature importance, turnover 0.15, GST age 0.07.
  - Not-interested: previous disposition 0.85, zone 0.07, hour 0.05.
- On the 11,834 transcribed calls:
  - Rush: previous disposition 0.52, zone 0.13, GST age 0.13, business type 0.09.
  - Any negative signal: previous disposition 0.33, product count 0.24, zone 0.23.

**Mid-call signals by history (PROVEN [INT-A], transcribed calls)**
- Frustration is 7.6% after a "General" previous call and 4.7–5.0% after NI or Call-Later, vs 2.3% on first calls.
- Rush is 25.8% after Call-Later and 27.3% after Meeting-Fixed, vs 20.5% on first calls.
- Bot-question is 5.1% after "General" vs 3.8% on first calls.

**Persistence of a seller's own past signal into their next transcribed call (PROVEN [INT-A]; 954 sellers with ≥2 transcribed calls, small n)**

| signal | next call: prior signal present | next call: prior signal absent | n with prior signal |
|---|---|---|---|
| rush | 30.8% | 21.1% | 276 |
| frustration | 17.5% | 8.4% | 40 |
| confusion | 25.0% | 7.0% | 68 |
| bot-question | 22.9% | 3.5% | 35 |

- Meeting rate after a prior bot-question was 5.7% vs 15.1%.

**Profile traits, meeting-fixed % (PROVEN [INT-A]; bucket-adjusted values nearly identical)**
- Turnover: <40 L 11.4, 40 L–1.5 Cr 9.5, ≥1.5 Cr 8.8, unknown 18.4.
- GST age: 0–2 y 14.2, 3–5 y 10.7, 6–10 y 9.4.
- Business type: Proprietorship 11.7, Partnership 10.4, Ltd 10.0.
- Nature of business: Service 12.6, Retailer 11.5, Manufacturer 10.8, Wholesaler 10.0.
- Product count: ≤5 → 14.5, >100 → 7.2.

**Profile traits vs mid-call signals (PROVEN [INT-A])**
- Signals vary only ±2 pts across profile traits. Rush is 17.6% (Ltd) to 21.7% (<40 L); frustration 2.8% (Service) to 4.4% (Ltd).
- Profile traits predict *outcome level* better than *signal type*.

**Language zone (PROVEN [INT-A])**
- Meeting rate is flat across zones (Hindi 11.5, GJ 11.5, MH 11.3, East 12.0, South-other 11.1).
- Tamil Nadu reads 13.6% with 0.6% NI, but **97% of TN calls ran on the `arrowhead` bot version**, so TN outcome and signal figures are confounded. The rush lexicon is Hinglish, so TN's 5.3% rush is likely under-detected.
- Tamil markers appear in 49.5% of transcribed TN calls (vs 46.6% in INT-VAL with a different lexicon). Gujarati markers appear in only 1.6% of GJ calls (thin lexicon).
- Median seller words per call: TN 17.5, South-other 20, Hindi 26, GJ 28. Shorter engagement in the South is consistent with a language-fit gap.

**Time of day (PROVEN [INT-A], adjusted for lead bucket and version)**
- 11:00–14:00 calls convert 8.2% vs 12.7–13.5% at other times, with NI 48.5%.
- Transcribed frustration in that window is 5.6% vs 2.4–3.5%.

**Signal → outcome (PROVEN [INT-A])**
- With rush, the call ends Call-Later 49.5% of the time vs 20.7% without, and meeting-fixed is 13.6% vs 26.0%. Rush mostly converts into callbacks rather than refusals.

### Inferences
- (ASSUMED) Pre-call persona should key on *history state* first. A seller who said NI/"general" last time needs a different opening, with a permission ask, identity first and short turns, than a first-call seller. This is the largest, most defensible separation in the data, and it also avoids the "personalised content" trap that failed 3 trials.
- (ASSUMED) Pre-call pace and brevity defaults:
  - Prior rush/frustration/confusion flags, and the 11–14h window, justify starting crisp. The signal recurs 1.5–6× more often on later calls.
  - Live adaptation still has to handle most cases, because 68–99% of signals first appear mid-call (INT-VAL).
- (ASSUMED) The do-not-call flag must be a hard pre-call gate. 5,719 answered calls in the window went to sellers whose aggregate flag is `do_not_call_requested=1`. The flag is window-aggregated, so some of those calls preceded the request.

### Gaps
- The lexicon is keyword-based; re-run with Jev labels.
- TN and Gujarati signal rates are lexicon-limited.
- The seller-level persistence analysis has small n (35–276 per signal).
- No randomized test exists for any persona dimension; all of the above is correlational.

---

## Q2. What do past objections and seller questions say per segment?

### Takeaway
Objection mix is **nearly identical across turnover, business type and zone**, varying only ±5 pts. It shifts with **history** and, for questions, with **size**: large and repeat-called sellers ask "who is this / why" far more. So the playbook should be a shared core plus a small number of segment-specific *first moves*, not 6 distinct playbooks.

### Cited Findings
**Objection categories, % of 4,126 calls with objection output (PROVEN [INT-A])**

| category | % of calls | meeting-fixed % when raised |
|---|---|---|
| Seller Unavailability & Scheduling | 32.5 | 5.7 |
| Callback / Deferred Engagement | 29.5 | 5.7 |
| Call Quality / Technical Failures | 25.5 | 2.6 |
| No Response / Engagement Drop | 20.0 | 1.8 |
| Explicit Disinterest / Refusal | 19.3 | 2.3 |
| Call Handling / Executive Gaps | 15.2 | 5.7 |
| Existing Engagement / Past Experience | 9.0 | 4.9 |
| Wrong Contact | 4.9 | — |
| Not Ready / Early-Stage | 4.8 | 8.1 |
| Product/Business Mismatch | 3.2 | — |
| Trust/Privacy | 1.2 | — |

- The seller-file `past_objections` (3,979 sellers) gives the same ranking: 32.6 / 28.5 / 25.9 / 20.2 / 19.3%.

**Objections by segment (PROVEN [INT-A])**
- ≥1.5 Cr turnover: Explicit Disinterest 24.1% vs 19.8% for <40 L, and Scheduling 29.4% vs 35.8%.
- Gujarat: Explicit Disinterest 25.9% vs Hindi belt 18.1%.
- Previously-NI/"general" sellers: Call Quality/Technical 31.8% vs 20.3% first-call, and Scheduling only 24.0%.
- Previously Call-Later/MF sellers: "Call Handling / Executive Gaps" 20.6% vs 14.6%.

**Seller questions, % of 2,826 calls (PROVEN [INT-A])**

| question category | % of calls | meeting-fixed % when asked |
|---|---|---|
| Meeting Visit | 53.4 | 55.4 |
| Identity Confirmation | 38.9 | 18.4 |
| Clarification | 38.7 | 39.1 |
| Purpose/Reason | 29.6 | 23.2 |
| Service/Product Info | 26.2 | — |
| Pricing/Payment | 14.3 | 23.1 |
| Callback | 13.3 | 15.2 |
| Frustrated User | 6.1 | 9.6 |
| AI-Bot Confirmation | 5.8 | 18.5 |

**Seller questions by segment (PROVEN [INT-A])**
- Identity Confirmation rises with size: 38.0% (<40 L) → 40.9% (40 L–1.5 Cr) → **47.2% (≥1.5 Cr)**. It is **49.4%** for previously-NI/"general" sellers vs 36.0% first-call.
- Meeting Visit falls in the same groups: 40.3% for ≥1.5 Cr and 30.8% for prev-NI, vs 55.6% for <40 L.
- Pricing/Payment is highest in the East (21.4%) and <40 L (15.9%).

**Detailed dispositions, 150,538 calls (PROVEN [INT-A])**
- Shares: call_dropped/no_response 25.2%; dropped mid-pitch 11.5%; dropped after "IndiaMART" identity 10.0%; dropped after seller-identity check 7.3%; callback with datetime 6.3%; already in touch/met exec 3.0%.
- Previously-NI/"general" sellers: no_response 35.3%, dropped after IndiaMART identity 11.5%.
- TN: dropped mid-pitch **25.7%** vs 10–12% elsewhere. This is consistent with a language mismatch but confounded by the `arrowhead` bot.
- ≥1.5 Cr sellers: dropped after IndiaMART identity 11.1%.

**External benchmark (DOCUMENTED)**
- Gong's 300M cold calls split objections into dismissive 49.5%, situational 42.6% and existing-solution 7.9%. Handling is to agree, ask a question, and sell a low-commitment next step. — [Gong Labs](https://www.gong.io/resources/labs/we-found-the-top-objections-across-300m-cold-calls-heres-how-to-handle-them-all/) (via PRIOR)

### Inferences
- (ASSUMED) Use a **core playbook** for all archetypes covering Scheduling, Callback, Disinterest, Existing engagement, Executive gaps, Identity and Bot-question. Each archetype then reorders the playbook and sets a *first move*:
  - **Established/large:** identity and credibility first (who, why, what's in it for you in one line), then a no-commitment meeting.
  - **Re-engage:** acknowledge the earlier call, ask permission, identity first, offer a callback slot or WhatsApp. Never re-pitch.
  - **Callback follow-up:** reference the agreed callback and time-box it ("2 minute").
  - **Micro/new:** a simple value story plus handling price/payment questions.
- (ASSUMED) "Call Quality / Technical" (25.5%) and "No response" (20%) are not persona problems. They point at the latency and voice-quality work in other blocks, so don't claim the persona fixes them.

### Gaps
- Objection evaluator coverage is mostly Apr–Jun (4,994 of 5,233 calls). Seller-question coverage is 2,826 calls with category output.
- Category taxonomies are evaluator-defined. The reasons/quotes text was not analysed, to respect the aggregates-only rule.

---

## Q3. Communication accommodation evidence (pace and language matching) for Indian B2B tele-sales

### Takeaway
There is good evidence that *how* you speak matters: slightly slower speech raises satisfaction, and prosodic similarity/mimicry correlates with sales. The language-matching evidence is mostly industry claims, and one credible practitioner says naive regional campaigns *underperform* Hinglish unless the dialogue sounds native. Internal data says language fit is needed in TN and likely Gujarat. Choose the start language deterministically, and keep Hinglish as a safe fallback.

### Cited Findings
- **Speech rate (DOCUMENTED):** slowing from 5.22 to 4.63 syllables/s, still a normal rate, raised customer satisfaction by 7.1%. The evidence is hundreds of service calls plus 5 experiments; extremely slow speech signals hesitation. — [Knowledge at Wharton (Berger & Cascio Rizzo, 2025)](https://knowledge.wharton.upenn.edu/article/how-speaking-slower-influences-consumer-behavior/)
- **Prosody mimicry (DOCUMENTED):** in 351 sales calls by 99 reps, base prosody patterns, prosodic similarity and the rep's mimicry of the customer were associated with sales success. Customer prosody was more predictive than rep prosody. — [Reeves, Oldroyd & Nissen, AOM 2023, BYU ScholarsArchive](https://scholarsarchive.byu.edu/facpub/7401)
- **Regional-language voice bots (DOCUMENTED, practitioner, Jul 2026):**
  - "Regional language campaigns see higher drop-off rates, shorter call durations, and lower conversion than Hinglish" until the dialogue sounds native.
  - Naturalness splits "roughly 20/80 between TTS configuration and dialogue engineering".
  - They test voices on real 8 kHz lines and "write every line by hand and hardcode it" rather than LLM-generate.
  - After that work, redBus regional campaigns held 75–85% engagement.
  — [SquadStack, Apurv Agrawal](https://www.squadstack.ai/blog/supporting-vernacular-is-easy-sounding-native-is-the-hard-part)
- **Vendor marketing (DOCUMENTED, low quality, no method):** about 3.5× higher ROI for regional voice vs static English text. — [Haptik blog](https://www.haptik.ai/blog/vernacular-voice-ai-for-tier-2-tier-3-india)
- **Internal language evidence (PROVEN):**
  - Tamil markers appear in 46.6–49.5% of TN calls; the bot speaks Hinglish (INT-VAL, INT-A).
  - Regional-marker calls have a 31.4% vs 23.2% meeting rate (INT-VAL; correlational).
  - TN calls are shortest: median seller words 17.5 vs 26 in the Hindi belt, and dropped mid-pitch 25.7% (INT-A).
- **PNS buyer–seller call extractions, a seller-language proxy (PROVEN [INT-A]; 5,411 calls, 1,388 sellers):**

| seller state | PNS calls | Hindi | English | regional language |
|---|---|---|---|---|
| Gujarat | 1,210 | 75% | 72% | Gujarati 48% |
| Tamil Nadu | 89 | 52% | 94% | Tamil 43% |
| Maharashtra | 844 | 91% | 89% | Marathi 15% |
| West Bengal | 186 | 89% | 90% | Bengali 14% |
| Punjab | 48 | 100% | 90% | Punjabi 12% |
| UP / Delhi | — | ≥98% | ≥94% | — |

### Inferences
- (ASSUMED) Language policy:
  - **TN → start in Tamil or English** with Hinglish on switch. TN sellers use English in 94% of PNS calls, and no Tamil conversational v4 voice exists (see Q4).
  - **GJ → start in Hinglish with a Gujarati greeting phrase**, and switch on the first Gujarati reply. Gujarati appears in 48% of PNS calls, but Hindi is still used in 75%.
  - **MH/WB/PB → Hinglish start**, with the regional language allowed on auto-switch.
  - Override any of these with the seller's own PNS language when present (28% coverage in GC).
- (ASSUMED) Pace: default about 1.0, crisp archetypes about 1.1, and warm archetypes 0.9–0.95, never below about 0.85. That matches "slightly slower" without sounding hesitant. Mimicry evidence supports live pace matching, but the hosted agent fixes pace per agent version (Q6), so live "pace" has to be emulated with brevity and turn length.

### Gaps
- No peer-reviewed study was found on language-matching uplift for Indian outbound B2B voice bots.
- The Reeves et al. paper is a conference abstract; effect sizes were not available.

---

## Q4. Archetype → voice / pace / pitch / language / opening / playbook mapping (objectives a, b)

### Takeaway
**5 calling archetypes + 1 suppression gate + a language overlay.** The archetypes are cut on history first, then on size/maturity. They map to **3 voice styles**, so there are only **3 published agent versions** for phone (crisp-fast, warm-patient, formal-professional). Each version uses per-language voices for the language overlay.

### Cited Findings
**Archetype profile (PROVEN [INT-A]; rules below; all 269,455 answered calls; rush and frustration from transcribed calls)**

| # | archetype (rule) | share of calls | meeting-fixed % | NI % | call-later % | median sec | rush % | frustration % |
|---|---|---|---|---|---|---|---|---|
| A0 | Suppress: `do_not_call_requested=1` (1,178 sellers) | gate | — | — | — | — | — | — |
| A1 | Re-engage: previous call NI or General | 37.8 | 4.1 | 46.4 | 11.5 | 13 | 19.0 | 5.8 |
| A2 | Callback follow-up: previous call Call-Later/Busy | 10.8 | 8.1 | 43.8 | 27.7 | 22 | 25.8 | 5.0 |
| A3 | Meeting follow-up: previous call Meeting-Fixed | 3.1 | 21.7 | 34.5 | 17.9 | 39 | 27.3 | 2.6 |
| A4 | Established first call: turnover ≥40 L or Ltd/Partnership | 19.5 | 14.3 | 43.3 | 17.1 | 27 | 19.9 | 2.3 |
| A5 | Micro/new first call: everyone else, mostly <40 L proprietorships | 28.8 | 19.5 | 39.6 | 17.3 | 34 | 20.8 | 2.4 |

- Within first calls, GST age 0–2 y converts 24.0% (A5) and 20.3% (A4), vs 15.2% and 12.3% for 6–10 y (PROVEN).
- The language overlay (TN/GJ/MH/East/South) covers **43% of calls** (PROVEN [INT-A]).

**Voice catalogue (PROVEN by UI scrape [CAT]/[SPIKE])**
- 176 Bulbul v4 voices, tagged by best language: Hindi 89, English 56, Marathi 9, Punjabi/Kannada/Telugu 4 each, Tamil/Gujarati 3 each, Bengali/Assamese 2 each.
- Tamil has no conversational/sales v4 voice: only Aravind (ad), Gokul and Vijay (narrators).
- Sales-tagged Hindi v4 voices:
  - Aditya – Sales Agent: "confident, low and fast", M
  - Aditya – Conversational: "persuasive, lively and slow", M
  - Tarun – Sales Agent: "confident, fast and expressive", M
  - Tarun – Conversational: "persuasive, high, soft-spoken", M
  - Ritu – Sales Agent: "warm, high and lively", F
  - Simran – Hindi Sales Agent: "engaging, low and brisk", F
  - Simran – English Sales Agent, F
- Regional conversational voices:

| language | voices |
|---|---|
| Gujarati | Bhavik ("calm and flat", M); Pooja – Gujarati Conversational ("warm, slow and expressive", F) |
| Marathi | Nilesh (M); Ishita (F, "friendly, slow") |
| Bengali | Arnab (M); Roopa – Bengali (F) |
| Kannada | Chetan (M); Chaitra (F) |
| Telugu | Kavitha (F); Pooja – Telugu (F) |
| Punjabi | Anand (M) |

**Platform settings (DOCUMENTED, Sarvam platform docs check, 2026-10-07)**
- Voice settings: model Bulbul V3/V4, speaking-speed slider, pitch slider, per-language voices.
- "The assigned speaker then remains consistent for the duration of the call, even if the caller switches languages mid-conversation."
- REST docs list pace 0.5–2.0. Pitch and loudness are documented for v2 only, not v3. — [Sarvam TTS API](https://docs.sarvam.ai/api-reference-docs/text-to-speech/convert.md). The v4 pitch range is undocumented in public docs (PRIOR).

### Proposed mapping (ASSUMED; voices to be confirmed by ear on 8 kHz)

| archetype | voice style → agent version | Hindi voice, pace | pitch | start language | opening style (template; ≤1 context fact) | playbook first moves | live-rule bias |
|---|---|---|---|---|---|---|---|
| A1 Re-engage | **crisp** (v-crisp) | Aditya – Sales Agent, 1.10 | 0 | overlay | Permission + identity: "Namaste, IndiaMART se [name], pichli baar baat adhuri reh gayi thi, 30 second milenge?" | Identity/purpose in one line; callback slot or WhatsApp; exit gracefully on 2nd no | shortest turns; early human/callback offer; up-front AI disclosure if prior bot-question |
| A2 Callback follow-up | **crisp** (v-crisp) | Aditya – Sales Agent, 1.10 | 0 | overlay | "Aapne is time call karne ko kaha tha; 2 minute ki baat hai" | Scheduling → fixed slot; time-box | rush likely (25.8%): skip small talk |
| A3 Meeting follow-up | **warm** (v-warm) | Ritu – Sales Agent, 0.95 | 0 | overlay | Confirm or reschedule the existing meeting | Executive gaps (20.6%): name the exec, confirm the slot | rush (27.3%): confirm fast |
| A4 Established first call | **formal** (v-formal) | Simran – Hindi Sales Agent, 1.00 (English: Simran – English Sales Agent) | 0 | overlay; English-heavy Hinglish | Credibility first: who, why and one benefit in ≤20 words | Identity (47%) and Disinterest (24%): agree, ask one question, offer a no-commitment meeting | formal "aap"; avoid "bhai-ji" |
| A5 Micro/new first call | **warm** (v-warm) | Ritu – Sales Agent, 0.95 | 0 | overlay | Friendly, simple value line | Pricing/payment and clarification; patient explanation | confusion → one idea per turn |
| Language overlay | per-language voice inside each version | GJ: Pooja-Gujarati (warm) or Bhavik (crisp/formal); MR: Ishita/Nilesh; BN: Roopa/Arnab; TE: Kavitha/Pooja-Telugu; KN: Chaitra/Chetan; PA: Anand; TA: test Gokul/Vijay vs English-start | — | rule table (Q3) | native greeting phrase | same | language switch allowed: start + hi + en |

- (ASSUMED) Keep pitch at 0 and let **voice choice carry pitch/timbre**, because catalogue tags already encode "high/low". This avoids depending on an undocumented v4 pitch range.
- (ASSUMED) Gender is a side effect of the voice choice, not a targeted variable. No evidence links bot gender to outcomes in this data.

### Inferences
- (ASSUMED) 5 archetypes are distinct on *outcomes* (meeting-fixed 4–22%, NI 35–46%, call-later 12–28%, median call length 13–39 s, frustration 2.3–5.8%), which is exactly what the deck's "distinctness across seller types" asks for.
- (ASSUMED) **Distinctness is real on the history axis. On the size axis it is mostly *style*:** A4 and A5 have the same signal rates but a 5-pt meeting gap and different question mixes.

### Gaps
- No ear test has been done of v4 voices on 8 kHz telephony.
- No evidence that the voice choice itself changes outcomes. The demo should frame voice as fit and consistency, not lift.

---

## Q5. Should a compact "seller.md" (problem #2) feed the opening and objection handling? (objective c)

### Takeaway
**Yes for objection handling and language; mostly no for the opening.** Three personalised-opening trials lost, and Global-Context activity facts correlate *negatively* with meetings. Fold a ≤8-line seller.md into agent variables for *answers* (identity, "what have I got from IndiaMART", existing exec, preferred channel), and use at most one neutral fact in the opening.

### Cited Findings
- **Personalised scripts went 0 for 3 (PROVEN, INT-VAL):**
  - `personalis`: 14.8% vs 17.8% (p=0.13), but NI was 5.5% vs 13.1%.
  - `last_met_d`: 11.1% vs 15.8%.
  - `summary_va`: 3.3% vs 18.4%.
- **GC coverage across the 5,000 sellers (PROVEN [INT-A]):**

| source | sellers covered |
|---|---|
| bot calls | 88% |
| WhatsApp messages | 74% |
| WhatsApp chatbot | 60% |
| enquiries | 55% |
| buyer calls | 41% |
| PNS extractions | 28% |
| buy-leads | 5% |

- 51% of bot calls had *any* enquiry, buyer-call or WhatsApp activity in the 30 days before the call.
- **Pre-call 30-day activity vs meeting-fixed on GC bot calls (PROVEN [INT-A], 9,657 calls; correlational):**

| 30-day activity | meeting-fixed % by level |
|---|---|
| Enquiries 0 / 1–3 / 4–15 / >15 | 12.3 / 9.1 / 5.8 / 3.7 |
| Buyer calls 0 / 1–3 / 4–15 / >15 | 11.9 / 8.9 / 5.0 / 2.0 |
| WhatsApp messages sent by the seller 0 / 1–3 / 4–15 / >15 | 10.8 / 9.6 / 13.9 / 19.7 |

- **Other GC fields (PROVEN [INT-A]):**
  - WhatsApp chatbot intents are dominated by buy-lead flows (`Msite_BL*` about 56K turns), photo upload/product issues (about 9K) and call feedback/callback (about 5K).
  - About 93% of profiled sellers are on free FCP-type plans (customer_type), with is_paid=0 for 4,747 of 5,000.
- **Platform delivery (DOCUMENTED):** Sarvam agents take input variables from an on-start hook, from campaign CSV columns mapped to agent variables, or from telephony metadata. Variables are inserted into greetings and instructions with `@`. — [Sarvam variables & personalization](https://docs.sarvam.ai/conversations/build/variables-personalization.md)

### Inferences
- (ASSUMED) The negative enquiry-volume link suggests already-active sellers see less need for a meeting, or have already been served. Leading with "you got 12 enquiries" is unlikely to help. Those facts are better used when the seller objects "IndiaMART se kuch nahi milta" (Disinterest/Existing-engagement) or asks Purpose/Benefit.
- (ASSUMED) WhatsApp-active sellers convert higher, so `preferred_followup=whatsapp` belongs in seller.md and drives the callback/WhatsApp offer in A1/A2.
- (ASSUMED) Proposed seller.md as agent variables, built deterministically from gc_* and the PS07 seller file, ≤8 lines and ≤600 chars:
  1. archetype + reason
  2. start language + evidence (state, PNS languages)
  3. top category (one name, for identity)
  4. last VANI outcome + date + follow-up promised
  5. exec contact status
  6. 30-day enquiries/buyer calls (counts, plus unread or missed share)
  7. WhatsApp-active yes/no
  8. prior signals (rush/frustration/bot-question)

  Buyer names and message text are never included.
- (ASSUMED) Demo framing: "context makes answers correct; it doesn't script the opening". This is consistent with the one positive trial signal, lower NI.

### Gaps
- GC is a 5,000-seller sample with no randomized context arm, so we can't show context causes lift.
- The overlap with problem #2's own seller.md design is unknown; align the field names with that team.

---

## Q6. Delivery mechanism per channel (objective d)

### Takeaway
- **Web/SDK demo:** a full per-call persona (voice, pace, pitch, opening, language, variables) via `InteractionConfig`.
- **Phone (Instant Outbound / Campaigns):** pick one of **3 published app_versions** (crisp / warm / formal), each with per-language voices, and pass `agent_variables` + `initial_bot_message` + `initial_language_name` per call.
- **Neither channel can change voice or pace mid-call.** Live adaptation goes through variables written by tools (persona directive, brevity).

### Cited Findings
- **SDK (DOCUMENTED from SDK classes; CALL mode with version=1 PROVEN [SPIKE]):**
  - `InteractionConfig` takes org_id, workspace_id, app_id, interaction_type, user_identifier and sample_rate.
  - Optional fields: `agent_variables`, `initial_language_name`, `initial_bot_message`, `initial_state_name`, `speech_hotwords`, `text_to_speech_config{speaker_id|speaker_name, speech_settings{pitch, pace, volume}}` and `version`.
  - The per-session TTS override itself was **not yet exercised live**.
- **Instant Outbound (DOCUMENTED [SPIKE]):**
  - Body: `app_config{app_id, app_version (required), agent_variables, app_overrides{initial_bot_message, initial_state_name, initial_language_name}}` + `user_config{user_phone_number}` + `webhook_config`.
  - **No TTS override.**
- **Code-tool contexts (DOCUMENTED [SPIKE]):**
  - On-start can set agent variables, initial message, language and state.
  - In-call can `change_language`, `change_state` and `set_agent_variable`.
  - Neither can change voice. The UI states "Voice is assigned per language at call start and will not change mid-conversation."
  - A Code Tool must be requested from Sarvam; it isn't offered in the UI.
- **In-call API tool → variables (PROVEN [SPIKE]):** the `read_seller_signal` tool wrote `seller_mode`/`persona_directive` variables each turn (12/12, 6/6, 6/6 turns), and the agent followed the directives.
- **Campaigns (DOCUMENTED):** CSV columns map to agent variables, and a webhook returns outcome and output variables (changelog 2026-08-20, via the platform docs check).

### Inferences
- (ASSUMED) Pipeline: persona generator (offline, our server) → `persona.json` + `seller.md` → channel adapter.
  - **SDK adapter:** speaker, pace and pitch from the archetype table; opening rendered from a template; `initial_language_name` from the language rule; variables = persona fields + seller.md lines.
  - **Phone adapter:** `app_version = {crisp, warm, formal}[archetype]` and the same variables and opening.
  - Both use the same `persona.json`, so the demo can show identical persona logic across channels.
- (ASSUMED) Use an on-start hook (API) as a fallback when calls are triggered from a campaign rather than our dialer. The hook returns variables, which keeps one source of truth.
- (ASSUMED) The version count stays small: 3 versions × per-language voices. Adding an archetype that needs a new *voice style* costs a new published version. Adding one that only needs new *wording* costs nothing.

### Gaps
- Not yet verified:
  - that per-session `text_to_speech_config` actually takes effect with v4 speakers;
  - the v4 pitch range;
  - whether on-start hooks can set `initial_language_name` on telephony.

  Test in the next spike.

---

## Q7. Rules vs LLM generation, LLM choice, evidence fields and archetype count (objective e)

### Takeaway
- **Deterministic:** everything with compliance or measurement stakes (DNC gate, AI disclosure, archetype, language, voice/version, pace, playbook order, evidence).
- **LLM:** only wording (opening variants within a template, the rationale sentence), validated against a JSON schema.
- **Archetype count:** 5 archetypes + gate, 3 voices, and a demo of 4 contrasting sellers suits a 2-day build.

### Cited Findings
- SquadStack hand-writes and hardcodes every regional line rather than LLM-generating it (DOCUMENTED). — [SquadStack](https://www.squadstack.ai/blog/supporting-vernacular-is-easy-sounding-native-is-the-hard-part)
- The deck asks for a "persona spec per seller with reason for each choice", "support from past-call evidence", and distinctness across seller types (task brief; PRIOR Q9).
- Sarvam 105B (conversational) reported 82.1 on voice-call, 63.4 on instruction-following and 78.8 on tool calling, at $0.80/M tokens (vendor-reported, DOCUMENTED via PRIOR). — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)
- Infra constraint (AGENTS.md): the core agent must be Sarvam; OpenRouter and the internal LiteLLM gateway are allowed.

### Inferences
**Rules vs LLM per field (ASSUMED)**

| field | method | evidence pointer |
|---|---|---|
| suppress (DNC) | rule | `do_not_call_requested` |
| AI disclosure up front | rule: `asked_if_talking_to_bot=1` or prior bot-question | 22.9% recurrence |
| archetype | rule (table in Q4) | history and size stats |
| language | rule: PNS language > state table > default Hinglish | Q3 table |
| voice/version, pace, pitch | lookup from archetype × language | catalogue tags |
| playbook order | rule: segment first moves + seller's own `past_objections` top-3 | Q2 |
| seller.md | deterministic aggregation | gc_* |
| opening wording | Sarvam LLM fills one of ≤3 templates per archetype × language, schema-validated, ≤25 words, no numbers unless from seller.md | — |
| rationale text | LLM summarises the evidence fields | — |

**LLM choice (ASSUMED)**
- Use the Sarvam LLM API (sarvam-m / 105B) for Indic wording, so the Sarvam-core story holds and native-script output works.
- Use an OpenRouter/LiteLLM model only as an offline LLM-as-judge for fit and distinctness.
- Persona generation is pre-call, so latency doesn't matter. Cache per seller.

**Evidence schema (ASSUMED)**
```json
{"field":"voice_style","value":"crisp","rule":"R-HIST-2",
 "inputs":{"prev_disposition":"Call Later / Busy"},
 "stat":"prev Call-Later → rush 25.8% vs 20.5%, call-later 27.7% vs 17.2% (n=29,213)",
 "source":"INT-A 2026-10-08","tag":"PROVEN-correlational"}
```
- Every persona carries one such record per field, plus `archetype_reason` and `persona_version`. A distinctness report shows archetype × field matrix, outcome profile per archetype (Q4 table) and pairwise field differences.

**Demo set (ASSUMED)**
- Four sellers that differ audibly and in logic:
  1. A1 Hindi-belt re-engage (crisp)
  2. A4 Gujarat manufacturer (formal + Gujarati greeting)
  3. A5 new micro retailer (warm)
  4. TN seller (English/Tamil start)
- Each persona card shows its evidence lines.
- Show live adaptation on top: rush → callback.

### Gaps
- No outcome data exists for LLM-written vs template openings in our setting.
- Sarvam-m vs 105B quality for Gujarati/Tamil sales wording is untested.
- The deck's exact rubric wording was not re-verified in this pass.
