# VANI Hackathon 2.0: which problem statement to choose (as of 2026-10-08)

Evidence tags used throughout: **[PROVEN]** = spiked hands-on with real keys; **[DATA]** = aggregate computed from the provided datasets on 2026-10-08 (no names, messages, transcripts or numbers copied); **[DOC]** = stated in the deck, data dictionaries or vendor docs; **[ASSUMED]** = inference/judgement.

Source shorthand (all local, project root `C:\Users\Imart\Voice ai hakethon\`):
- Deck = [raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- PS07 dict = [raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md](../../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)
- BTC dict = `data/BesTime to Call/BesTime to Call/Best-Time-to-Call - Data Dictionary.md` (git-ignored)
- GC dict = `data/Global Context - Seller Dataset/Global_Context_DATA_DICTIONARY.md` (git-ignored)
- Validation = [wiki/projects/vani-hackathon/persona-data-validation.md](../../../wiki/projects/vani-hackathon/persona-data-validation.md)
- Architecture = [wiki/projects/vani-hackathon/persona-architecture.md](../../../wiki/projects/vani-hackathon/persona-architecture.md)
- Spike log = [raw/research/2026-10-07-spike-log.md](../../../raw/research/2026-10-07-spike-log.md)
- Report = [outputs/reports/VANI adaptive persona architecture.md](../../reports/VANI%20adaptive%20persona%20architecture.md)
- Landscape = [wiki/projects/vani-hackathon/voice-ai-landscape-2026-10.md](../../../wiki/projects/vani-hackathon/voice-ai-landscape-2026-10.md)
- Aggregates = computed 2026-10-08 with pandas over `data/Persona Files/*/ps07_evaluator_outputs_*.csv` (278,332 rows), `ps07_bot_calls_*.csv` (269,455 rows), and `Best-Time-to-Call - Call Attempts Apr-Sep 2026.csv` (530,748 rows). Cited below as "Aggregates (2026-10-08)"; not filed in raw/ yet.

# Problem selection for VANI Voice AI Hackathon 2.0

## Q1. What each problem requires, whether the provided data is sufficient, and what the Sarvam voice demo would look like

### Takeaway
Only #4 (Persona) has a voice demo that *is* the deliverable; #1, #3, #5 have rich, labelled data but their voice component is a bolt-on; #2 has a 5,000-seller multi-channel set that suits it well; #7 has no dataset at all and depends on external web data. Data is sufficient for #1, #3, #4, #5; adequate for #2; missing for #7.

### Cited Findings
**Deck-wide rules**
- Scoring: Business Impact 25%, Solution Completeness 20% ("share of the expected outputs delivered and working end to end"), Technical Robustness 20% ("validation on real data; edge cases"), Voice Experience 20% ("natural, low-latency conversation; multilingual and Hinglish handling"), Demo & skills.md 15%; each juror scores 1–5 — [Deck, slide 25](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- Submission checklist requires an "Agent ID / live link on Sarvam platform" and a 5–7 min demo video, for every problem — [Deck, slide 23]
- "Each team picks one of the 7 problem statements"; "Plagiarised or pre-built solutions are disqualified"; teams of 3 with at least 1 non-tech member — [Deck, slide 30]
- Deck numbering is inconsistent: slide 3 says "Seven Problems" but lists six; Seller Enrichment is "Problem 7 of 6"; the persona dataset is named PS07 while the deck calls Persona problem 4 — [Deck, slides 3, 19]; [PS07 dict]

**#1 Quality Audit & Fix Loop**
- Expected outputs: audit-to-fix pipeline on real call data; dashboard with audit→issue→fix→test trail; risk-flag queue. Metrics: agreement with human auditors, share of calls audited, root-cause grouping quality, drop in failure rate after a tested fix, time from issue to fix tested — [Deck, slides 5–6]
- Data: 10 existing evaluator agents already run on VANI calls: disposition 150,821; seller_questions 24,694; incorrect_mf 19,617; execdrop 18,768; se_contact 17,716; location_confirmation 15,640; latency_repetition 13,681; topics 7,179; objections 5,233; ivr 4,983 — [DATA, Aggregates (2026-10-08)], matching [PS07 dict §3]
- Turn-level transcripts: 139,555 turns over 12,788 calls; 5,000-call recording sample (2,494 with transcripts); 713 local mp3s — [PS07 dict §4–5]; local `data/call_recordings` listing
- No human-auditor labels (the "spreadsheet sample") are in any provided file, so "agreement with human auditors" cannot be measured from provided data — [PS07 dict] (absence of such a file); [GC dict]
- Voice demo: none is inherent. A credible one would re-run a failing scenario on a Sarvam agent before and after the suggested prompt fix (simulated seller over `sarvam-conv-ai-sdk`) — [ASSUMED], harness feasibility [PROVEN] in [Spike log, "Voice Agents SDK, CALL mode"]

**#2 Global Context**
- Expected outputs: buyer.md/seller.md for sample GLIDs; demo resuming a conversation across two channels; note on sources/lookback/refresh. Metrics include "Lift from the personalised opening" and "Conversations resumed without re-asking" — [Deck, slides 8–9]
- Data: 5,000 sellers, 11 files (enquiries 33,006; WhatsApp messages 130,897; WhatsApp chatbot turns 83,280; bot calls 9,657; bot call turns only 4,920 rows over 420 sellers; buyer-call extractions 5,417), window 1 Apr–2 Oct 2026; seller-side only (no buyer.md dataset) — [GC dict]
- Voice demo: Sarvam agent opens with a personalised line after a WhatsApp chat; Sarvam Voice Agents supports "telephony, WhatsApp, web widget and API" — [Deck, slide 22]

**#3 Best Time to Call**
- Expected outputs: trained model with per-seller window and retry predictions; backtest vs current rule; recommendation on the 15-minute rule. Metrics: lift in meetings fixed on held-out data, connect rate, calls per meeting, validation soundness — [Deck, slides 11–12]
- Data: 530,748 attempts, 149,363 sellers, 1 Apr–30 Sep 2026; answer rate 50.8%; meetings per attempt 5.84%; meetings per answered call 11.51% — [DATA, Aggregates (2026-10-08)]; [BTC dict]
- Raw meeting-fixed rate per attempt by dial hour ranges from 3.1% (11:00) to 7.5% (09:00, 15:00); answer rate is lowest at 10:00 (38.0%) — [DATA] (unadjusted; confounded by lead type and attempt number)
- Attempt 1: answer 61.0%, MF 9.9%; attempt 2: 48.4% / 4.6%; attempt 3: 43.4% / 3.1% — [DATA]
- Observed retry gaps (time since the seller's previous attempt, attempt ≥2): median ~180 min, 10th pct ~58 min; only ~14.8K of ~318K retries fall within 20 min. Retries at 10–20 min: answer 61.3% but MF 1.7%; at 40–120 min: answer 40.2%, MF 4.4% — [DATA] (shows connect rate and meetings diverge, as the deck warns; may reflect callback-driven retries, not the 15-min rule)
- No randomised schedule exists in the data, so any backtest is observational — [BTC dict] (field list; no assignment field) [ASSUMED inference]
- Voice demo: none inherent; at most a Sarvam agent that books a callback slot from the model — [ASSUMED]

**#4 Persona Design**
- Expected outputs: persona generator on sample seller files; persona spec per seller with reasons; live demo with ≥1 mid-call switch; switch log. Demo must be "on Sarvam: the same scenario for 2 to 3 contrasting sellers" — [Deck, slides 14–15]
- Data: 149,363 seller files (persona input incl. past objections, frustration, bot-question flags); 269,455 answered bot calls; evaluator outputs; turns — [PS07 dict]
- Voice demo is the deliverable; voice is fixed per call on Sarvam ("Voice is assigned per language at call start and will not change mid-conversation"), so the live switch is wording/brevity/tone + language — [PROVEN, Spike log, "Voice switching"]

**#5 Agent A/B Testing & Auto-Rollout**
- Expected outputs: end-to-end A/B workflow; run report with split, goal-disposition share, significance, decision; demo of auto-promotion and early stop. Metrics include "Accuracy of auto-disposition vs. labelled calls" and "Right winner on a known-difference test"; test bed = "simulated sellers built with Sarvam voice agents" — [Deck, slides 17–18]
- Labels exist for auto-disposition validation: the disposition evaluator output joins to 150,770 bot calls with a human/system `disposition_label`. Evaluator `meeting_fixed` → label Meeting Fixed in 14,374 of 15,235 (94.3% precision); 14,374 of 16,128 labelled Meeting Fixed calls are caught as `meeting_fixed` (89.1% recall; +90 as `online_meeting_fixed`) — [DATA, Aggregates (2026-10-08)]
- Historical "variants" exist in `lead_bot_version`: main_vani 208,605; arrowhead 30,676; last_met_d 23,046; main 5,573; last_met_a 723; personalis 452; base_vani 289; summary_va 91 — [DATA]
- Voice demo: simulated sellers on Sarvam calling variant agents; voice is present but the judged artefact is the statistics/report — [ASSUMED]

**#7 Seller Enrichment**
- Expected outputs: minimal input → pre-filled profile; JSON aligned to IM fields with confidence; write-up on sources and accuracy. Inputs come from "website, Google listing, social pages, catalogs, GST records" — [Deck, slides 19–21]
- No Seller Enrichment dataset is in the provided Drive folder (local `data/` has only Persona, Global Context, Best Time to Call, call recordings) — [DATA, local listing]
- Voice demo: possible as a voice onboarding agent that confirms fields, but not required by the expected outputs — [Deck, slide 21] / [ASSUMED]

### Inferences
- Voice Experience (20%) will be judged on whatever voice the team shows. #4 is the only problem where the expected outputs force a multi-language, multi-seller live voice demo, so it has the highest ceiling on this criterion; #3 and #7 have the lowest.
- #1 and #5 have the best *labelled* data for Technical Robustness (real evaluator outputs, real dispositions, real trial arms); #4's causal claim must come from simulation.
- #7's data gap plus the "no new outside vendors" constraint (web search/Google listing APIs would be outside vendors) makes it the weakest fit for this team.

### Gaps
- No human-audit labels for #1's headline metric; the team would need to hand-label ~50 calls on day 1 or use existing evaluator outputs as a proxy.
- Could not confirm whether the 15-minute rule applies only to certain redis buckets; the observed retry-gap distribution does not show it as the dominant pattern.
- Did not check whether a Seller Enrichment dataset exists elsewhere on the Drive folder (only the local copy was inspected).

## Q2. Business impact estimates for VANI from the provided data

### Takeaway
The largest quantifiable pools are: call drops / bot-ended calls and loops (#1), the attempt/hour schedule (#3), the rush segment (#4), and bad prompt rollouts (#5, one trial alone cost ~1,000 meetings). #4's pool is real but its lift is unproven; #1 and #3 can show measured effects on real data.

### Cited Findings
- Base rate: 11.51% meeting-fixed on 269,455 answered bot calls Apr–Sep 2026 (Not Interested 43.2%, General 29.1%, Call Later/Busy 16.2%) — [DATA, Aggregates (2026-10-08)]; Validation cites 11.5% — [Validation]
- **#4 rush segment:** keyword "rush" signal in 21.0% of 11,834 transcribed calls; meeting-fixed 13.6% when present vs 26.0% absent; 99% first seen mid-call. Frustration 3.6% (12.8% vs 23.8%). Transcript subset is biased (23.4% MF vs 11.5% overall). Correlational only — [Validation]
- **#4 script personalisation failed 3 internal trials:** personalis 14.8% vs base_vani 17.8% (p=0.13); last_met_d 11.1% vs main_vani 15.8% (lower on 22 of 23 paired days); summary_va 3.3% vs 18.4% (p<0.001) — [Validation]
- **#4 language fit:** 46.6% of Tamil Nadu calls carry Tamil markers while the bot speaks Hinglish — [Validation]
- **#1 fatal-issue candidates:** disposition evaluator labels 55.1% (83,101/150,821) of evaluated calls `call_dropped`; execdrop evaluator: bot/exec side ended 55.6%, system 34.9%, seller 9.5% of 18,768 calls, and the seller tried to continue after closure in 14.8% (2,775); latency_repetition: 12.8% of 13,681 calls loopy, 15.8% had a seller repeat, 26% loopy or repeat, 17.8% of calls with per-call p95 bot latency > 3 s (median per-call p50 0.4 s); incorrect_mf: 2.4% (469/19,617) of meeting-fixed calls were explicitly rejected by the seller; location_confirmation: 7.5% rejected_and_corrected — [DATA, Aggregates (2026-10-08)]
- **#3 schedule:** 530,748 attempts → 31,054 meetings; meetings per attempt fall from 9.9% (attempt 1) to 1.9% (attempt 5); 27% of sellers receive ≥5 attempts; unadjusted MF per attempt varies 2.4× by hour (3.1% at 11:00 vs 7.5% at 09:00) — [DATA]; outcome mix — [BTC dict]
- **#5 cost of unguarded rollouts:** last_met_d ran on 23,046 calls at 11.1% vs 15.8% for main_vani — [Validation]; call count [DATA]
- **#2:** "Lift from the personalised opening" is a deck metric, but IndiaMART's three personalised-script trials all lost to control — [Deck, slide 9]; [Validation]

### Inferences
- #5: had an early-stop guardrail run on last_met_d, roughly 4.7 pts × 23,046 ≈ 1,080 meetings might not have been lost (assumes main_vani's rate is the right counterfactual; Validation notes time-of-day/lead-mix confounds). This is the strongest single "business story" number in the data.
- #4: illustratively, 21% of ~269K answered calls ≈ 56K rush calls per six months; recovering 1 pt of meeting rate on them ≈ 570 meetings per six months (vs ~31K total). The *size* is credible; the *lift* is not yet shown anywhere.
- #1: "call_dropped" is the majority disposition and maps mostly to Not Interested/General labels, and 14.8% of execdrop-evaluated calls show the seller trying to continue after the bot closed. That is a large, concrete, already-measured failure pool a judge can verify.
- #3: the hour and attempt effects are big but confounded (lead type, callback scheduling); the honest lift will be smaller than raw spreads.
- #2's headline metric runs against IndiaMART's own negative trial evidence.

### Gaps
- No call-volume or revenue-per-meeting figure to convert meetings into ₹.
- Rush/frustration rates come from a crude keyword lexicon on a biased subset; not re-run with Jev labels yet.
- Fatal vs Non-Fatal severity is not defined in the data; the #1 numbers above are candidates, not graded fatals.

## Q3. Which problems other teams are likely to pick

### Takeaway
No data on team choices exists; by reasoning from the deck, #4 Persona and #1 Quality Audit are the most likely crowded choices, #3 attracts data-science teams, #7 and #2 attract non-voice/product teams. Standing out on #4 requires evidence (paired simulation, switch log, data-backed personas), not just a nicer voice.

### Cited Findings
- The deck's Sarvam slide pitches Bulbul "control over speaker, pitch and pace" and Voice Agents — the most visible features map directly onto #4 — [Deck, slide 22]
- #4 is the only problem whose deliverable is "Voice demo on Sarvam … with at least one live mid-call switch" — [Deck, slide 14]
- Teams must include ≥1 non-tech member — [Deck, slide 30]
- Judging rubrics drive most outcome variance; winners re-read the rubric before scoping decisions — [JetBrains, "How to win a hackathon: notes from the judging table"](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)

### Inferences
- In a voice hackathon sponsored by a voice vendor, the persona problem is the most "on-theme" and will likely draw the most teams; many will ship a pre-call persona plus a prompt-only "adapt if the seller is rushed" instruction. The spike log already shows prompt-only behaviour is inconsistent, so a measured ON/OFF comparison is a real differentiator.
- #1 is the second most familiar pattern (LLM-as-judge dashboards). Because IndiaMART already runs 10 evaluators, a #1 entry must go beyond grading into clustering, fix generation and tested fixes to look new.
- Fewer teams will pick #5 (statistics-heavy, abstract demo) and #3 (no voice), which lowers competition but also caps Voice Experience.

### Gaps
- No registration or problem-choice data; the competition estimate is purely inferential.
- Jury composition (product vs engineering vs Sarvam) unknown; it affects how much Voice Experience vs Business Impact is felt in practice.

## Q4. Which problems combine well, and do judges reward combination or depth

### Takeaway
Go deep on one problem and use pieces of others as *evidence* for it. Completeness is scored against the chosen problem's expected outputs, and each team picks one problem, so a combined pitch earns credit only where it feeds the chosen problem's metrics.

### Cited Findings
- "Each team picks one of the 7 problem statements"; Completeness = "share of the expected outputs delivered and working end to end" — [Deck, slides 25, 30]
- The persona trace store + typed judges + paired simulator is the same engine #1 (judges on real calls, Fatal/Non-Fatal, fix validated ON/OFF) and #5 (variants = app_versions; early stop; Fatal-rate guardrail) need — [Architecture, "Reuse"]; [Report, "The same trace-and-judge spine becomes Quality Audit and A/B testing"]
- Paired simulated sellers, ON vs OFF, ~120–180 calls; control arm must still call the tool so latency does not confound lift — [Architecture, "Proving lift"]; [Report]
- Hackathon advice: "The best projects do one thing really well rather than five things halfway"; the hardest claim must actually work — [JetBrains judging notes](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/); [Push to Prod, "How To Win Hackathons"](https://getpushtoprod.substack.com/p/how-to-win-hackathons)

### Inferences
- Best combination within 2 days: **#4 as the problem**, with (a) a mini-#5 harness (paired ON/OFF simulated sellers, significance) as the "Support from past-call evidence"/robustness story, and (b) #1-style typed judges scoring persona fit and switch timing. Neither needs its own dashboard or rollout logic.
- The reverse (#1 as problem with a persona fix) is also coherent: a root cause like "bot ignores rush" yields a prompt fix tested ON/OFF on the same harness.
- Building full #1 or #5 deliverables alongside #4 would exceed one strong developer's 2-day capacity [ASSUMED].

### Gaps
- No statement from organisers on whether cross-problem features earn bonus credit.

## Q5. Risks: unproven dependencies, Sarvam constraints, disqualification

### Takeaway
#4 carries the most platform risk (extra LLM pass per turn, tool skip, Jev latency/allowlist, no Tamil sales voice, no mid-call voice change), but the core loop is already proven with a stub. #1/#3/#5 are low platform risk but weaker on voice. Disqualification risk is low for all if the core logic is the team's own; highest for #1 if it looks like a re-skin of IndiaMART's existing evaluators.

### Cited Findings
- [PROVEN] Tool called on every seller turn 24/24 over 4 SDK calls (often twice per turn); directives change replies (rushed → 11–13 words + callback); tool receives Devanagari verbatim; reply latency median ~2.1 s (range 1.2–3.5 s) before adding Jev; Sarvam → our server via cloudflared on Daytona works — [Spike log]; [Architecture, "Spike status"]
- [PROVEN] Jev accuracy 49/51 on a smoke set; via OpenRouter from India ~480–491 ms p50 on keep-alive (760 ms new connection); works only over IPv4 via VPN; Daytona egress IP not allowlisted; IndiaMART LiteLLM gateway shows 8 Jev requests, all failures — [Spike log]
- [PROVEN] Voice fixed per call; no Code Tool option in UI (must be requested); Workflows enterprise-only; no Tamil conversational/sales Bulbul v4 voice — [Spike log]
- [DOC] Tool runs only if the routed LLM calls it; no BYO LLM on Sarvam Voice Agents; States legacy — [Architecture, "Premise corrections"]
- [DOC] Prompt-only adaptation is inconsistent, so attribution needs ON/OFF — [Spike log, Spike 3 caveat]
- [DOC] Cost: ~₹3.50/min quoted for Indus Voice Agents; ~₹1,900 for 180 three-minute simulated calls; new accounts ₹100 credit — [Report, risks paragraph]; deck promises "API keys / credits" per team — [Deck, slide 22]
- [DOC] Public evidence that mid-call persona switching lifts outcomes is vendor marketing only — [Report, risks paragraph]
- [DOC] Jev as a blocking turn gate raised median reply 2.1 s → 4.6 s in one benchmark — [Landscape]
- "Plagiarised or pre-built solutions are disqualified" — [Deck, slide 30]

### Inferences
- #4's worst plausible case: Jev unreachable from the in-call server → fall back to an in-server lexicon/OpenRouter-LLM classifier (already working as the stub). The demo still works; robustness claim weakens.
- If reply latency with the sidecar exceeds ~3 s, Voice Experience suffers; the "checkpoint" or "next-turn async" modes in Architecture cap the damage.
- #1 risk: the deck's #1 brief overlaps IndiaMART's existing evaluator stack; judges may see grading as "already exists" unless the team owns the clustering/fix/test loop.
- #7 carries compliance/consent and outside-vendor risk (Google listing, social scraping).

### Gaps
- Tool skip rate at scale and p95 added latency with real Jev in-loop not yet measured (day-1 spikes 2, 5).
- Hackathon Sarvam credit size unknown.

## Q6. Scored comparison, ranked recommendation, and flip conditions

### Takeaway
Rank: **#4 Persona (≈4.0) > #1 Quality Audit (≈3.7) > #3 Best Time to Call (≈3.5) ≈ #5 A/B (≈3.5) > #2 Global Context (≈3.3) > #7 Enrichment (≈2.7)**. Choose #4, built as live adaptation + language fit with a paired ON/OFF simulation as evidence; keep #1 as the fallback because it reuses the same judge/simulator spine and has the strongest real-data story.

### Cited Findings
- Criterion weights and 1–5 scale — [Deck, slide 25]
- Prior internal ranking: Persona > Quality Audit > A/B ≫ Memory, Best Time, Enrichment — [Landscape, "Why this pick"]
- Evidence for each score is in Q1–Q5 above (data counts [DATA]; spikes [PROVEN]; deck requirements [DOC]).

### Inferences
Scores are [ASSUMED] team estimates (1–5), weighted by the deck's criteria.

| Problem | Business Impact 25% | Completeness 20% | Robustness 20% | Voice Exp. 20% | Demo & skills.md 15% | **Weighted** | 2-day feasibility | Data readiness | Reuse of spiked work | Main risk |
|---|---|---|---|---|---|---|---|---|---|---|
| #4 Persona | 3.5 (rush 21%, Tamil gap; lift unproven, personalisation 0/3) | 4 | 3.5 (sim-only causal) | 5 | 4.5 | **4.05** | Medium-high (core loop proven) | Good | High: agent, tool, directives, Jev, harness, voice catalogue | Latency/tool skip; no lift |
| #1 Quality Audit | 4 (55% call_dropped; 26% loopy/repeat; 14.8% bot closes on a still-talking seller) | 4 | 4 (real 13.7K turn-level calls) | 2.5 (bolt-on before/after replay) | 4 | **3.70** | High | Good, but no human-audit labels | Medium: judges, simulator, trace store | "Already exists" perception |
| #3 Best Time | 4 (530K attempts; 2.4× hour spread; attempt decay) | 4.5 | 4 (observational backtest) | 2 | 3 | **3.55** | High (pure ML) | Excellent | Low | Confounding; weak voice |
| #5 A/B | 3.5 (~1,080 meetings lost to one trial) | 3.5 | 4 (auto-disposition 94% precision vs labels) | 3 | 3.5 | **3.50** | Medium | Good (labels + historical arms) | Medium-high: simulator, app_versions | Simulated-only test bed; abstract demo |
| #2 Global Context | 3 (personalised-opening metric contradicts 3 failed trials) | 3.5 | 3 | 3.5 | 3.5 | **3.28** | Medium | Adequate (5K sellers, seller-side only) | Low-medium | Weak lift story |
| #7 Enrichment | 3 | 2.5 | 2.5 | 2 | 3.5 | **2.68** | Low | None provided | None | Outside-vendor/consent rule |

- **Recommendation:** #4, scoped to: pre-call persona from seller data (rules + archetypes + LLM prose, evidence per field); live switch on rush/frustration/confusion/bot-question/language via the tool + classifier + hysteresis; 2–3 contrasting simulated sellers (incl. a Tamil Nadu seller) with a switch log; a paired ON/OFF simulation reporting switch latency and judged outcome. Do not lead with the personalised opening.
- **Flip conditions:**
  1. Day-1 spike shows tool skip >10% or added p95 >~800 ms such that replies routinely exceed ~3 s → #4's Voice/Robustness drop to ~3.5/3 → weighted ~3.6; **#1 becomes first** (same harness, real-data robustness).
  2. Paired simulation shows no ON vs OFF lift → #4 Business Impact drops to ~2.5 → weighted ~3.8; still marginally ahead of #1 because the deck scores "correct, well-timed switches" and voice, not lift alone. Pivot the pitch to "switch correctness + language fit", not "more meetings".
  3. Sarvam credits too small for ~150 simulated calls, or SDK CALL mode unavailable at the venue → #4 loses its evidence leg; #1 (offline on real data) or #3 become safer.
  4. Jury signals a business/data emphasis over voice, or many teams visibly pick #4 → #1 rises; with "one dropped-call root cause → tested fix → measured drop" it has the strongest verifiable impact. #5 overtakes #1 only if the team can demo a convincing known-difference test on Sarvam simulated sellers (it can reuse the #4 harness and the 94%-precision auto-disposition).
  5. If the team lacked the proven Sarvam/Jev spikes (it doesn't), #3 would be the lowest-risk pick, capped by Voice Experience.

### Gaps
- Scores are judgement, not jury data; a ±0.5 change on any 20–25% criterion can swap #1/#3/#5.
- Jev-labelled re-run of signal rates and the ON/OFF simulation result are not yet available; both directly move #4's Business Impact score.
