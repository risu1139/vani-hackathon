# VANI Persona Design: Detailed Demo Document (v6)

**Problem 4 of 6 | Voice AI Hackathon 2.0 | IndiaMART | October 2026**

Companion to the demo deck (`outputs/plans/VANI_Persona_Design_Deck_v2_visual.pptx`, 18 slides). Numbers are aggregates; no seller names, ids or call text appear in this document. Version 6 adds: the agent picks the persona and hook from the data (not a rule table), the skill it follows, and the self-learning loop (technical view). Mood layers: keyword tool in the call, Jev between calls.

## 1. Summary

VANI is IndiaMART's outbound voice agent. On this call type its job is one thing: **get a meeting between the seller and an IndiaMART executive**. Today it uses one voice, one style and one script for every seller. We built a system that, before each call, **has an agent design a persona and call plan for that one seller from the seller's own data**, hands them to a Sarvam voice agent, adapts the call live, then reviews the call and learns from it.

- **The agent decides.** The persona and the hook are not picked by a fixed rule table. A Claude agent reads the seller's data and decides the persona, the hook and 12 fields, with a cited quote for every choice. A validator refuses anything uncited.
- **Data the current VANI does not use, now supplied:** 62 data points per seller from about 60 IndiaMART sources: similar sellers, live buy leads and order values, category value, catalogue quality, plan and credit use, enquiry trend, top categories, the assigned executive, location and language, past-call mood and objections.
- **Live adaptation:** a signal tool runs on every seller turn and changes how VANI speaks on the same turn. In the call a fast keyword tool decides the mood; between calls the Jev decision model judges the same turns and its labels improve the keyword tool.
- **Self-learning:** every call updates scoreboards for the persona, the hook, each field value, the reason behind it and our default rules. The next agent reads what worked for similar sellers. 15% of calls use a control persona so uplift is measured.
- **Safety first:** VANI never claims to be human and never says AI, bot or manager; every number it says traces to a verified fact; personal data is removed before the model sees it; compliance rules are checked before and after each call.

## 2. The problem

**The problem today.** The Voice Bot talks to every seller in one voice and one style, and keeps it for the whole call. Sellers differ in pace, patience, language and how they object. A seller who gets irritated, confused or rushed mid-call still gets the same delivery.

**The challenge.** Before each call, build the Voice Bot persona that fits that seller from their seller data, and adapt it live as the call unfolds.

### What the data says about today's calls

- PS07 dataset: 149,363 sellers, 269,455 answered bot calls (1 Apr to 30 Sep 2026), of which 12,354 have turn transcripts; 21 role-play executive calls analysed.
- **Meeting rate: 11.5% of all 269,455 answered bot calls ended with a meeting.** Among the 12,354 calls that have transcripts the rate is 22.4%, because that set leans to longer and more engaged calls. The objection figures below are measured inside the transcribed set, so compare them with 22.4%, not 11.5%. Outcome labels are noisy (about 4 of the first 20 calls read had a label that contradicted the transcript).
- **A rushed seller roughly halves the chance of a meeting.** In transcribed calls (11,834 calls, base rate 23.4%), a rush signal in the seller's words appears in about 21% of calls; those calls end with a meeting about 14% of the time against about 26% when no rush signal appears (keyword method, approximate). Read this effect inside the transcribed set, not against the 11.5% overall base.
- The opening rests on an enquiry count and the city. The old bot variants claimed to be human in 0.2% of calls and gave an inflated identity ("a manager from the branch") in 2.3%.
- Objections inside the transcribed set (share of calls; meeting rate): busy 16.7% (14.9%), no interest 9.6% (9.2%), confusion 9.2% (23.0%), price 7.5% (33.0%), phone or online preferred 5.2%, already met an executive 4.5%, owner elsewhere 2.5%, bot or recording question 2.4%, repeated calls 1.6%, wrong number 1.6%, distrust 1.3%, "I got no enquiries" 1.1%. Shares are keyword-based and approximate.

## 3. What current VANI does not use, and what we add

| Seller information | Current VANI | Our system |
|---|---|---|
| Similar sellers (same size, same category, same city) | Not in the call | Peer statistic ladder and a competitor list with plan; VANI may name a similar paid seller with city and "for many years", never a figure next to a name |
| Live buy-lead data and order values | Not used | Showcase leads (live and recent) with order value, quantity, city; buy leads bought, credits, lapse, rejection reasons |
| Order value (AOV) and category value | Not used | Seller AOV vs the category; unit price spread and bulk share |
| Catalogue quality | Not used | Quality score, photo and price gaps, product counts, top five categories by active products |
| Plan | Not used | Free or paid plan class (free = NSD, paid = CSD, TMW, KCD and others), checked against the vertical name |
| Enquiries and phone behaviour | Enquiry count only | Enquiry trend (rising, flat, falling), phone, WhatsApp and chatbot behaviour |
| Handler | Not used | The sales handler's name when one exists; the meeting is booked with that person; for a team or pool, "our IndiaMART team handles your account" |
| Location and language | City | City, state, GST state, onboarding cities, languages heard on calls; start language suggested from location |
| Past calls | Not used for style | Call history by age (30 days full weight, 90 days short, older ignored); mood signals, objections, grievances |

## 4. How we solve it: the flow

1. **Seller data.** 62 data points from about 60 IndiaMART sources: offline PS07 and Global Context files, internal APIs (data warehouse, user service, company page) and read-only queries on the buy-lead and catalogue databases.
2. **Context builder.** One folder per seller: an index with key facts, then topic files (identity, business, catalogue, buy leads, enquiries, channels, peers, candidate leads) and numbered past-call files.
3. **Safe export.** Personal data is removed before the model sees it. Names become tokens, a hard PII check refuses any export that still holds a leak, source names and internal notes are stripped. Phone, GST and PAN numbers never leave IndiaMART. The real names stay inside IndiaMART.
4. **Persona design (Claude, in a sandbox).** Scripts compute traits, states, guards and hook eligibility; the scoreboards give the top two personas; **the agent selects one and decides every field and the hook with a checkable reason**; gates and a validator refuse anything uncited.
5. **Compile.** The validated persona becomes the Sarvam agent's per-call variables and prompt sections; names are filled in only now, at call time.
6. **The call (Sarvam voice agent).** A start tool sets voice, pace, pitch, language and the opening; a signal tool reads each seller turn and returns a directive; a booking tool records the meeting.
7. **Review and learning.** Claude reviews the call against compliance rules and call-rule checks; Jev labels the seller turns; the outcome updates the scoreboards; the next agent reads the result.

## 5. Data points we consider

**For each seller we collect 62 data points from about 60 IndiaMART sources** (the count of sources is approximate; about 53 of the 62 are filled for an average seller). Their business. Their catalogue gaps. Live buy leads. Their competitors. How past calls went. Each data point can give VANI a reason for the meeting.

**Before the model sees the data, all personal data is removed.** Names become tokens. Phone, GST and PAN numbers never leave IndiaMART. A hard check refuses any export that still holds one; real names are put back only at call time, for the voice.

| Group | Examples |
|---|---|
| Identity | Company, contact person, designation, recorded gender (used only to choose the voice, never said) |
| Location and language | City, state, GST state, onboarding cities, city tier (metro, tier-2, small town, village), Hindi belt, languages heard on calls |
| Business | Plan (free or paid), member since, turnover band, nature of business, legal status, profile text, company page |
| Catalogue | Top categories, product counts, quality score, products without photo, price or category, top five categories by active products |
| Demand and money | Buy leads bought, credits and lapse, rejection reasons, category value, seller order value, same-size peers, showcase leads, competitor list with their plan |
| Enquiries and channels | Enquiries received and trend, phone behaviour, WhatsApp and chatbot, buyer-call extractions |
| Relationship | Assigned sales handler, complaints, executive contact, do-not-call and frustration flags |
| Past VANI calls | Date, outcome, duration, mood signals (rushed, frustrated, confused, bot question, grievance), objections raised |

## 6. Main seller factors

| Factor | How it is read | What it changes |
|---|---|---|
| Plan | Free (NSD) or paid (CSD) | Division reference, objective, which hooks are allowed |
| Size | Turnover: below 40 lakh small; 40 lakh to 1.5 crore medium; 1.5 to 5 crore medium-high; 5 crore and above high | Sophistication, formality, language suggestion (English for high) |
| Order value tier | Seller AOV vs the category (low, mid, high) | Numbers-first style, money hook |
| Location | State, city tier, GST state | Start language, pace |
| Catalogue strength | Weak when score is below 40 or over 20% of products miss a photo or price | Profile-gap hook |
| Buy-lead usage | Lapsed, unused, low use, active; rejected leads | Unused-credits and lead-quality hooks |
| Enquiry flow | Last month vs last quarter | Enquiry-drop hook |
| Past-call mood | Signals weighted by age (half-life 30 days) | Pace, brevity, empathy, switch sensitivity |
| Grievance and fatigue | Open complaint; 3 or more VANI calls in 7 days | Acknowledge first; short call; guards |

These factors are **evidence for the agent, not a lookup**. The scripts compute them as facts; the agent decides what they mean for this seller (section 9).

## 7. Personas

The persona library has seven starting points. They are information for the agent, not limits: the agent decides every field with a reason. P0 is the control arm used to measure uplift.

| ID | Name | Fits | Style |
|---|---|---|---|
| P0 | VANI default (control) | Baseline | Natural Hinglish, polite, direct, two sentences |
| P1 | Numbers-first advisor | Mid or large turnover, active buy-lead users | Leads with one concrete number; confident, specific |
| P2 | Warm local helper | Small sellers, small towns, regional language | Seller's language, simple words, help framing |
| P3 | Patient guide | Previously confused, low digital use, first contact | Short phrases, one idea, checks understanding |
| P4 | Brief and busy-friendly | Often rushed, high call fatigue | One short sentence, value first, callback at once |
| P5 | Respectful problem-solver | Open grievance, frustration (mostly paid) | Acknowledges the problem once; never repeats the old pitch |
| P6 | Senior advisor | High turnover, English-comfortable owners | Business-like, mostly English, brief, never pushy |

### How a persona is chosen

- Scoreboards by seller segment (all sellers, division, turnover band, order value tier, zone, state, category group) give the top two personas with a **weighted random draw** (Thompson sampling, so the system keeps exploring); 15% of calls use the control P0 so uplift can be measured.
- **The agent selects one and decides each field** (voice gender, pace, pitch, language start, language mix, formality, sophistication, warmth, empathy, words per reply, hook, opening). The reason for each field is chosen in this order: seller evidence with a cited quote; earlier-call data (only if the search found no evidence); otherwise the persona's own value.
- The agent may change the drawn persona's values when the data says so. If it overrides the draw completely, the call is logged to a separate arm named COMPOSED.
- Start rules: female voice by default, with extra lean for tense calls and rural Hindi-belt sellers; English for high-turnover sellers, otherwise the regional language; empathy lines added for grievance, frustration and rush. VANI introduces itself with its own name (a female voice and a male voice are available).

## 8. Hooks

A hook is the one reason VANI gives for the meeting. **The agent picks one main hook plus a backup**, each with cites; eligibility is computed by script from the data, the choice is the agent's. Every number VANI says comes from a verified fact. Money first: a live or recent order with its value is used first when one exists.

| Hook | Division | When it fits | Never says |
|---|---|---|---|
| Money lead | Both | A live or recent buy lead with an order value | Buyer name; "this order is yours" |
| Profile gap | Free mainly | Weak catalogue: products without photo or price | A gap not in the data |
| Category demand | Both | Buy requirements in the seller's category | Seasonal or "good demand" claims without a number |
| Unused credits | Paid only | Credits lapsed or unused | That credits come back; "you wasted money" |
| Lead quality fix | Paid only | Many rejected leads | That quality will improve |
| Enquiry drop | Both | Enquiries fell vs last quarter | A cause not in the data |
| Peer usage | Both | At least 5 same-size peers in the same category bought leads | A figure next to a named seller |
| Resolve grievance | Both | Open complaint or grievance in a recent call (said first) | Blaming the earlier executive |

Evidence note: in the old bot experiment, the enquiry-count opening beat the "interest" and "discovery" openings; only 13 of 73 segment rows are statistically significant, so most hook preferences are starting points that the learning loop will update.

## 9. The agent decides: not a rule table, and the skill it follows

**A rule table** gives the same output for the same input ("if small and free then persona 2"). **Our agent** reads this seller's own data and judges.

The chain: 62 data points of this seller → scripts compute facts (traits, states, hook eligibility, guards) → scoreboards offer the top two personas by weighted draw → **the agent judges** (persona, hook, 12 fields) → a validator refuses anything uncited, a wrong value or a number that is not a verified fact.

Two sellers with the same plan and size can therefore get different personas and hooks, because the agent reads what each one's data says. The scripts decide what is eligible and what is a guard (do-not-call, open grievance, call fatigue); the agent chooses inside those safe limits.

### The skill

The skill is a file the agent follows, and a single writer tool plus a validator enforce it: the agent cannot write a persona any other way, and a persona written another way is rejected so no call is made. Steps:

1. **Read** the seller's index and core files and the computed facts and prior. If the seller is do-not-call, stop with no persona.
2. **Select the base persona** from the scoreboard's top two, with a reason.
3. **Search** the seller's files for every field and every eligible hook before deciding.
4. **Decide every field** with a reason in this order:
   1. *Seller evidence:* an exact quote of at most 20 words from a hit of that field's search.
   2. *Earlier calls:* what got meetings for similar sellers; only if no hit is evidence, and with a written reason for each top hit that was rejected.
   3. *Persona default:* the selected persona's own value as changed by the start rules.
5. **Decide every eligible hook:** a primary hook needs at least three cites from at least two files and a counter-evidence check; money first when a live or recent order exists.
6. **Write the spoken text:** opening, hook claim, call plan, objection playbook, verified facts. Call-plan rules (R1 to R6) are checked by the validator.
7. **Finalize:** the validator checks every decision and every number and writes the validated persona.

## 10. Objections and responses

Each division has a reply playbook built from the 21 role-play calls and the measured objections. Rules for every reply: answer in one sentence with a fact from the seller's data, ask twice at most then offer a callback, never promise results, never name a plan or a price on the call. Examples:

- **"Tell me on the phone, why a meeting?"** Name the exact gap or the lead settings that need the seller's own products or account open.
- **"The executive came before, nothing changed."** Agree, then name the specific fact (unused credits, rejected leads, fewer enquiries) the meeting is about.
- **"Are you a bot?"** First time: do not answer it, say it is calling from IndiaMART about the profile and continue. If pressed: "IndiaMART's virtual assistant" and offer a callback. Never claim to be human.
- **Price question** (highest meeting rate inside the transcribed set, 33%): a straight answer that the meeting itself is free.
- **"Nahi chahiye":** stays on the line and restates the hook; one topic per "no".

## 11. One call: start, mid-call, end

### Start of call
The start tool applies the persona before the first word: voice, pace, pitch, start language and the opening line. One fixed prompt template is filled by per-call variables.

### Mid-call
A signal tool runs on every seller turn and returns the seller's mode and a directive that overrides the speaking style for that reply only.

| Mode | What VANI does |
|---|---|
| Rushed | One short sentence, offer a callback |
| Frustrated | Brief apology, stop the pitch, one yes or no question |
| Confused | One idea, short phrases, check understanding |
| Interested | Answer briefly, ask for the day and time |
| Declined | Keeps the call open politely, restates the hook |
| Bot question | Sidestep once, then "virtual assistant" if pressed |
| Opt-out | Apologise, confirm no more calls, end (explicit end only) |
| Language switch | Reply in the seller's language from then on |
| Question and handler questions | One-turn overlays: answer from verified facts; with a handler name say it and book with that person; with a team say "our IndiaMART team handles your account; the executive will introduce themselves when they call"; never a made-up name |

**Switch log** row: turn, utterance, from mode, to mode, cue, directive id, change made, reason, whether asking for the meeting is allowed, milliseconds. Voice, pace and pitch are set at call start and cannot change mid-call (a Sarvam platform limit); tone changes through the words VANI uses.

### How mood is decided: keyword tool in the call, Jev between calls

- **Instant keyword tool (in the call).** Reads each seller turn in Hindi, Hinglish, Marathi, Telugu and other scripts and answers in well under a millisecond, so the directive applies on the same turn. Measured accuracy is about 0.60 on a small reviewed set; we present it as a measurement, not a production figure.
- **Jev decision model (between calls, on real calls).** Jev (typesafe jev-1.13, reached through OpenRouter) is a decision model, not a chat model: it answers six mood questions at once (rushed, frustrated, confused, bot question, interested, language) with a probability for each, about 0.5 seconds at the median and a tiny fraction of a cent per turn. In tests it scored 49 of 51 on a native-script set and 10 of 10 on a tricky set, and it catches cases the keywords miss. Jev labels real call turns; the labels form a gold set that scores the keyword tool and proposes keyword fixes (each checked against the gold set and approved by a person). We also tested Jev in live scripted calls through a relay.
- **Why Jev is not in the live loop yet.** A web call to Jev adds about 0.5 seconds to a spoken reply, so in the live call the instant keyword tool decides; a hybrid that asks Jev only on unclear turns within a strict time budget is the next step.
- **Problem-solving path.** We also evaluated a Sarvam chat model, a small trained classifier and a hosted fast model as alternatives, and measured each option's latency before choosing the keyword-first design.

### End of call
The booking tool records the meeting with the sales handler when a name exists (for a team: "our IndiaMART executive"), or a callback. After booking VANI asks "anything else?" and ends only on the seller's no or goodbye. The call ends early only on an explicit request (stop calling, cut the call, do not call); "not interested" keeps the line open (the hook again, then one topic per "no").

## 12. The self-learning loop

The loop runs between calls, never during one. It is how the agent's picks get better with no retraining and no hand-tuning.

### The cycle (technical view)

1. **Call.** The persona and the hook the agent chose are logged as a decision: the seller's segment path, the arm drawn, and for each field its value group and reason type.
2. **Review.** Claude reviews the call against the compliance rubric (7 fatal and 13 non-fatal items) and the call-rule checks R1 to R6 (pass, fail or unknown per language), and judges whether the persona fitted and the hook landed.
3. **Outcome.** Meeting fixed or not (and held, when known).
4. **Update** (`loop2_update.py`). The outcome is added to the scoreboard cells on the seller's path: persona by segment, voice, hook per segment, each field's value group, reason type and start rule. Reports: meeting rate by reason type and by start rule, and uplift of each persona against the control.
5. **Brief** (`prior.py`). Before the next call, the brief tells the agent, per field, which value groups got meetings for similar sellers at the deepest level with enough calls. Partial pooling makes a thin segment fall back to its parent until it has enough calls. A weighted random draw (Thompson sampling) picks the top two personas, so the system keeps exploring. 15% of calls use the control persona P0 so uplift is measured against today's style.
6. **The agent decides again**, with more evidence, following the skill (section 9).

### What the loop learns

Every call credits six things:

| What | Question it answers |
|---|---|
| Persona (arm), by seller segment | Which persona works for which sellers |
| Hook, by seller segment | Which hook works for which sellers |
| Each field's value group | Which pace, language, empathy, words per reply work |
| Reason type (seller evidence, earlier calls, persona default) | Do decisions grounded in the seller's own words beat the default? |
| Start rule | Do our own defaults (voice lean, English for high turnover, empathy lines) help? |
| Uplift against the control persona P0 | Is the whole system better than today's style? |

Segments run from all sellers through division, turnover band, order value tier, zone and state, plus category group.

### A second loop, on the mood tool

Jev labels real call turns; the labels build a gold set that scores the keyword tool, and missed or wrong switches become proposals for keyword and directive changes. Each proposal must not be worse on the gold set and needs a person's approval. New persona library versions also need a person's approval.

### Honest state today

The scoreboards start empty. Until real calls arrive, every pick is a division-based lean plus a random draw. Outcome labels in the old call data are noisy, so early signals are weak; gains smaller than about 15 to 20 points will not be distinguishable with the call counts we can expect.

## 13. Architecture

| Stage | What runs | Where |
|---|---|---|
| Context builder | Reads offline files, internal APIs and read-only database queries; writes one folder per seller | IndiaMART network (VPN) |
| Safe export | Name tokens, hard PII check, sources stripped | IndiaMART network |
| Persona design | Scripts for facts and prior, then Claude Opus 5.5 with a skill; a single writer tool, read log, stop gate, validator | Isolated Daytona sandbox |
| Compile | Variables and prompt sections; names filled in | IndiaMART network |
| Voice call | Sarvam voice agent: speech to text, language model, text to speech; start, signal and booking tools; one fixed prompt template with per-call variables; IndiaMART knowledge base attached | Sarvam |
| Review and learning | Claude reviews each call; Jev labels real turns; scoreboards update by seller segment; the brief feeds the next agent | IndiaMART network |

The agent in the sandbox never sees real names, sources, or unmasked data; it works only from the pseudonymised folder.

## 14. Safety and compliance

- **Identity:** never "AI", "bot", "branch manager" or "account manager"; never claims to be human; if pressed, "IndiaMART's virtual assistant".
- **Verified facts only:** every spoken number traces to a fact in the seller's data; no unverified claims; no figures next to named sellers.
- **No selling on the call:** no plan or price; the call is about the meeting.
- **Privacy:** no real seller, buyer, competitor or staff name, phone number, email, GSTIN, PAN, Aadhaar, IFSC, pincode, address or GPS location reaches the persona model; the export refuses on any leak; real names are filled in at call time, for the Sarvam voice only.
- **Compliance rubric:** 7 fatal items (claims human, banned identity words, unverified number, pushing after opt-out, naming a buyer or competitor, quoting a price or plan, false claim about the seller) and 13 non-fatal items, checked before the call and after it.
- **Human approval:** new persona library versions and keyword changes need a person's approval.

## 15. Progress and evidence to date

- Full persona runs on the sandbox: 7 done and 1 running, about 2 to 3 minutes and $1 to $1.5 each; validation passed in the sandbox and again outside the sandbox every time.
- About 7 real phone tests and about 16 scripted voice test calls: in every scripted call all 21 to 22 per-call variables arrived, checked against Sarvam's own record.
- Every switch type fired on the same turn in scripted calls: rushed, frustrated, confused, bot question, declined, explicit end, and language switch (Marathi to Hindi to English). Languages tested: Marathi, Hindi, English, Telugu.
- Review of the reviewed call: 0 fatal items.
- Sarvam agent response time averages about 0.8 to 1.6 seconds per turn.
- Persona spec per seller with reasons and cited quotes, validated before any call.

## 16. Limits we state openly

- Voice, pace and pitch cannot change mid-call; tone changes through wording.
- The keyword switch tool is a baseline; its measured accuracy is about 0.60 on a small reviewed set.
- Jev runs between calls; its network round trip of about 0.5 seconds keeps it out of the live loop for now.
- The voice question (female or male) cannot be learned while the start rules point to the female voice.
- Live values (order value, peers, GST state, top categories) are not safe for replaying past calls.
- Objection and meeting rates come from old bot calls with noisy outcome labels; the transcribed subset leans to longer, more engaged calls.
- The count of about 60 sources is approximate.
- Production calls to real sellers need a telephony connection and Sarvam's outbound service; today's phone route reaches only whitelisted test numbers.

## 17. Scoring criteria mapping

| Criterion | Our evidence |
|---|---|
| Fit of each persona to its seller | Evidence-cited persona per seller, decided by the agent from the data; reasons per field |
| Correct, well-timed mid-call switches | Same-turn switches proven in scripted calls, with the switch log; Jev-labelled gold set to score the mood tool |
| Distinctness across seller types | Seven personas plus per-seller fields; contrasting demo sellers (free and paid, regional and English, small and high turnover) |
| Natural voice in 2 or more languages | Marathi, Hindi, English and Telugu tested on the Sarvam voice agent |
| Support from past-call evidence | 12,354 transcripts measured; the persona cites earlier calls; the self-learning loop updates picks from every new call |

## 18. Future goals

- **Now: meeting arrangement.** The right persona and hook per seller to book the executive meeting, with live adaptation.
- **Next: seller enrichment.** Catalogue improvement calls (photos, prices, categories) with suggestions drawn from top categories and similar sellers; a top-category hook; profile completion with the seller on the call.
- **Personalised objective per seller.** The goal of the call is chosen per seller: meeting, enrichment or NPS (net promoter score).
- **Preferred call time per seller.** To improve the share of calls that are answered (scheduling is handled outside the persona today).
- **Preferred or suggested language per seller.** From the seller's location, GST state and the languages heard on earlier calls.
- **Faster mood decisions.** A hybrid that asks the Jev decision model only on unclear turns, within a strict time budget.
- **Platform:** learning from real calls, more languages and voices, production telephony at scale.

## 19. Demo videos

The demo videos of calls will be added at the end of the deck: contrasting sellers in different languages, each with a live mid-call switch and the switch log. Recordings contain real seller details and are shared only with approval.

## Appendix: glossary

- **NSD / CSD:** free-seller sales division / paid-seller division (TMW, KCD and other paid divisions follow the paid path).
- **AOV:** average order value of a seller's buy leads.
- **Hook:** the reason given for the meeting.
- **Directive:** the short instruction the signal tool returns for the next reply.
- **Verified fact:** a statement VANI may say, tied to a source field in the seller's data.
- **Thompson sampling:** a weighted random draw that favours what worked but keeps trying alternatives.
- **Control arm (P0):** today's VANI style, used on 15% of calls to measure uplift.
- **NPS:** net promoter score, a customer satisfaction measure.
- **Jev:** a decision model that returns a probability for each yes or no question about a seller's turn; used here to judge mood on real call turns between calls.
