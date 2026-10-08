# PS07 call data as "past runs": replay through the switcher and post-call review

As of 2026-10-08. Everything below is aggregates only: no seller names, numbers, messages or transcript text. Tags: **PROVEN** = computed by me from the local PS07 files on 2026-10-08 (pandas, Python 3.12; scripts were throwaway, in the session scratchpad). **DOCUMENTED** = stated in a raw/ or wiki/ file. **ASSUMED** = my design or inference.

Source keys used below:
- [DATA-turns] = `data/Persona Files/Persona Files/...Dataset 1 of 3/ps07_call_turns.csv` (file:///C:/Users/Imart/Voice%20ai%20hakethon/data/Persona%20Files/Persona%20Files/)
- [DATA-bot] = `...Dataset 2 of 3/ps07_bot_calls_*.csv` (4 files stacked)
- [DATA-eval] = `...Dataset 3 of 3/ps07_evaluator_outputs_*.csv` (7 files stacked)
- [DATA-exec] = `...Dataset 1 of 3/ps07_executive_calls.csv`; [DATA-seller] = `ps07_seller_files_part1/2.csv`; [DATA-rec] = `ps07_recording_sample_5000.csv`
- [DICT] = [raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)
- [DECISION] = [raw/hackathon/2026-10-08-team-decision-between-run-learning.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/raw/hackathon/2026-10-08-team-decision-between-run-learning.md)
- [REQ] = [wiki/projects/vani-hackathon/persona-requirements.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/wiki/projects/vani-hackathon/persona-requirements.md)
- [LOOPS] = [wiki/projects/vani-hackathon/learning-loops.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/wiki/projects/vani-hackathon/learning-loops.md); [SYS] = [wiki/.../system-design.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/wiki/projects/vani-hackathon/system-design.md); [VALID] = [wiki/.../persona-data-validation.md](file:///C:/Users/Imart/Voice%20ai%20hakethon/wiki/projects/vani-hackathon/persona-data-validation.md)
- [LEX] = the keyword lexicon in `app/validate/profile_persona.py` (romanized Hinglish stand-in for Jev). For language switch I extended it with phrases like "english mein", "tamil", "gujarati" etc. All signal counts below are lexicon counts, i.e. a noisy proxy, not ground truth.

---

## 1. What each PS07 table offers as a replayable "run"

### Takeaway
Only `ps07_call_turns.csv` is directly replayable turn by turn: 12,788 calls / 139,555 turns, Jul–Aug 2026, 99.6% Latin script, with coarse LLM-derived timestamps. Every transcribed call also has a `latency_repetition` record (turn-indexed "seller had to repeat", loops) and a `seller_questions` record (in the newer "gaps" schema only), and 92.5% have `execdrop` and `se_contact`. The richest per-call labels (Frustrated User, Clarification, AI-bot question, objections, topics) sit on calls that have **no** turn transcript, but 94% of those calls do have a recording URL.

### Cited Findings
**Table inventory and linkage**
- Join keys: `attempt_id` links a bot call across bot_calls, evaluator outputs, call_turns and recording sample; `fk_glusr_usr_id` links to the seller and to executive calls. DOCUMENTED — [DICT]
- Bot calls: 269,455 answered calls, all unique `attempt_id`, 130,129 sellers. Dispositions: Not Interested 116,364 (43.2%), General 78,365 (29.1%), Call Later/Busy 43,672 (16.2%), Meeting Fixed 31,054 (11.5%). Calls per month: Apr 9.8K, May 23.3K, Jun 34.8K, Jul 58.1K, Aug 74.0K, Sep 69.4K. 88.3% have a recording URL. PROVEN — [DATA-bot]
- Bot versions: main_vani 208,605; arrowhead 30,676; last_met_d 23,046; main 5,573; last_met_a 723; personalis 452; base_vani 289; summary_va 91. PROVEN — [DATA-bot]
- Evaluator outputs: 278,332 rows over 170,282 calls; 98.4% of those attempt_ids are in the bot-call files. Rows per agent: disposition 150,821; seller_questions 24,694; incorrect_mf 19,617; execdrop 18,768; se_contact 17,716; location_confirmation 15,640; latency_repetition 13,681; topics 7,179; objections 5,233; ivr 4,983. All JSON parsed without error on 3,000-row samples per agent. PROVEN — [DATA-eval]

**call_turns (the replayable runs)**
- 139,555 turns, 12,788 calls, 11,652 sellers. Speakers: bot 74,460; seller 64,625; unknown 470. Turns per call: median 9, p90 20, max 148. Seller turns per call: median 4, p90 10. Call length (last `end_sec`): median 52 s, p90 158 s. PROVEN — [DATA-turns]
- 12,354 of the 12,788 turn calls are in the bot-call files (= exactly the calls with `has_turn_transcript=1`); 434 are not (no disposition/outcome for those). PROVEN — [DATA-turns], [DATA-bot]
- Months of turn calls: Jul 5,229; Aug 6,966; Sep 159; **none from Apr–Jun**. Bot versions: main_vani 9,252; arrowhead 2,000; last_met_d 995; main 107; **zero** personalis / base_vani / summary_va calls. PROVEN — [DATA-turns]×[DATA-bot]
- Outcome mix is biased toward engaged calls: Not Interested 31.1%, Call Later 25.7%, Meeting Fixed 22.4%, General 20.8% (vs 11.5% MF overall). PROVEN — same
- Turn text is not ASR from our stack: it was "extracted from the `latency_repetition` evaluator", i.e. an LLM transcription of the audio. DOCUMENTED — [DICT]
- Script per turn: Latin 139,003 (99.6%), Devanagari 257 (bot 137, seller 120), no letters 295. Only 0.19% of calls (24) contain any Devanagari turn; no Tamil/Gujarati/Bengali/Telugu/Kannada script at all. PROVEN — [DATA-turns]
- Timestamps are coarse: seller response gap after a bot turn has median 0.0 s, p10 0.0 s, p90 1.1 s; 5.7% of turns start >0.5 s before the previous turn ends; 0.07% have end < start. The evaluator itself flags `timestamp_suspect` on 2.5% of calls. PROVEN — [DATA-turns], [DATA-eval]
- Words per turn: bot median 22 (mean 25), seller median 4 (mean 8.4). PROVEN — [DATA-turns]

**Evaluator coverage on the 12,788 turn calls**
- latency_repetition 100%; seller_questions 99.96%; se_contact 92.6%; execdrop 92.5%; disposition 83.3%; incorrect_mf 19.9%; location_confirmation 17.4%; **objections 0, topics 0, ivr 0**. PROVEN — [DATA-eval]
- `latency_repetition` fields (per call): `turns[]` (speaker/start/end/text), `latency.measurements[]` with `seller_turn_idx`, `next_bot_turn_idx`, `latency_sec`, `seller_had_to_repeat` (turn-level boolean), `timestamp_suspect`; `repetition.bot/seller.semantic_repeats[]` with `turn_indices`, `theme`, `category` (true_loop / commitment_blindness); `is_loopy`; p50/p95 latency. PROVEN (schema) — [DATA-eval]
- On turn calls: seller_had_to_repeat ≥1 in 15.9% of calls; is_loopy 12.9%; seller semantic repeat 28.7%; median bot-latency p95 1.0 s. PROVEN — [DATA-eval]
- On turn calls `seller_questions` uses only the "gaps" schema (`has_gaps`, `gaps[]` with `gap_type` Misunderstood Intent / Complete Miss / Factually Incorrect / Ignored Complaint…, `seller_turn_type` Objection/Question/Request/Complaint, plus the seller and bot dialogue). Misunderstood Intent appears in 2,790 calls; Complaint turn type in 223. **No question categories (Frustrated User, Clarification, AI Bot Confirmation) exist on any turn call.** PROVEN — [DATA-eval]
- `execdrop.who_ended_call` on turn calls: EXEC (bot) 55.9%, SYSTEM 34.0%, SELLER 10.1%. PROVEN — [DATA-eval]
- `disposition` evaluator on turn calls: call_dropped 2,482; meeting_fixed 2,394; callback_requested 2,168; not_interested 1,729; already_in_touch_with_im 674; online_meeting_fixed 436; do_not_call 134; sub-dispositions include dropped_mid_pitch 951, dropped_after_indiamart_identity 501, flat_refusal 1,572, bad_past_experience 82. Confidence is "high" on 99.9% of a 3K sample (uninformative). PROVEN — [DATA-eval]

**Where the "emotion" labels actually live (not replayable yet)**
- `seller_questions` in the older "questions" schema: 6,504 calls (Apr 59, May 1,345, Jun 3,523, Jul 1,204), categories Frustrated User 140, Clarification 934, AI Bot Confirmation 126, Pricing Payment 272. 0 of them have turn transcripts; 94.3% have a recording URL. PROVEN — [DATA-eval]×[DATA-bot]
- `objections` (5,182 calls; categories e.g. Call Quality/Technical 587, Explicit Disinterest 474, No Seller Response 469, Existing Engagement 211; with evidence quotes) and `topics` (7,179 calls, 32 predefined topic ids with sequence numbers): 0 overlap with turn calls. PROVEN — [DATA-eval]
- Seller-file flags: showed_frustration = 139 sellers, asked_if_talking_to_bot = 125, do_not_call_requested = 1,178, already_in_touch_with_executive = 4,205 (of 149,363). The first two look derived from the question categories above (similar counts). PROVEN (counts) / ASSUMED (derivation) — [DATA-seller]
- Recording sample: 5,000 calls, 2,494 overlap with turns; includes all 452 personalis calls (audio only). PROVEN — [DATA-rec]

**Coverage per required signal (FAQ Q4) on turn calls, lexicon proxy**
| signal | seller turns hit | calls | % calls | first cue at seller turn 0 | median seller turns left after first cue |
|---|---|---|---|---|---|
| rush | 3,405 | 2,497 | 20.8% | 1% | 2 |
| interest | 2,823 | 1,997 | 16.6% | 20% | 3 |
| confusion | 918 | 766 | 6.4% | 32% | 3 |
| frustration | 567 | 442 | 3.7% | 4% | 1 |
| language switch | 528 | 296 | 2.5% | 10% | 3 |
- PROVEN (lexicon counts) — [DATA-turns] + [LEX]. Any signal: 39.1% of calls; two or more: 9.2%. PROVEN.
- 114 of the 296 language-switch calls are from southern states; only 12 frustration and 30 confusion calls come from southern states. PROVEN.
- Meeting-fixed rate with vs without cue: rush 13.6% vs 26.0%; frustration 12.8% vs 23.8%; confusion 20.0% vs 23.7%; interest 22.5% vs 23.6%; language switch 30.4% vs 23.3%. Matches [VALID] (which used 11,834 calls; I count 12,788 turn calls, 12,354 with outcome). PROVEN.
- Seller states of turn calls: Gujarat 2,676; UP 2,306; Maharashtra 1,996; Delhi 1,376; Rajasthan 969; West Bengal 633; Haryana 623; Telangana 301; **Tamil Nadu 210; Karnataka 3; Kerala/AP 0**. PROVEN — [DATA-turns]×[DATA-seller]

### Inferences
- The "run" unit for replay = one `attempt_id` in call_turns, joined to bot_calls (outcome), latency_repetition (turn-indexed repeat flags), seller_questions-gaps, execdrop, disposition, and the seller file (persona inputs). ASSUMED
- Rush and interest have enough positives (~2K calls each); frustration (~440) and language switch (~300) are thin, and language switch is concentrated in Tamil Nadu. ASSUMED
- Timing-based rush detection (short gaps, interruptions) cannot be learned from this data: timestamps are LLM-estimated and mostly 0-gap. Rush must be learned from text. ASSUMED
- The 6,504 "questions-schema" calls with Frustrated User / Clarification / AI-bot labels are the best weak-label pool, but they need STT (Sarvam) from the recording URLs to become replayable. ASSUMED

### Gaps
- Exact lexicon precision is unknown; no human labels exist yet.
- Why turn transcripts exist only for Jul–Sep (the evaluator was presumably introduced then) is not documented.
- Whether recording URLs still open today for the questions-schema calls was not re-tested (dictionary says 60/60 opened, DOCUMENTED).

---

## 2. Replaying a past call through our switcher, and how the reviewer labels it

### Takeaway
Replay = feed seller turns one at a time with no lookahead into the frozen switcher (lexicon decides on the current turn; Jev's verdict applies from the next turn), log every decision, then give the reviewer the whole call plus the switch log. Because the recorded bot never received our directives, everything after our first switch is counterfactual, so scoring must be per signal onset and "up to the first switch", not "did the call end well".

### Cited Findings
- Live architecture being replayed: lexicon (Devanagari + romanized, NFD) decides on the current turn; Jev runs in the background and corrects the next turn; policy has hysteresis, priority, max 2 switches; every switch goes to a switch log (signal, change, reason). DOCUMENTED — [SYS], [REQ]
- Jev inputs are only `state`, `instructions`, `criteria`; it can't be fine-tuned. Jev p50 ~0.5 s, p95 ~1.4 s. DOCUMENTED — [LOOPS]
- The LLM never decides a switch live; the review happens after the run and labels true signals and right/missed/false/late switches. DOCUMENTED — [DECISION], [LOOPS]
- After the first rush cue only ~2 seller turns remain (median); frustration 1; confusion/interest/language 3. PROVEN — [DATA-turns]+[LEX]. So "late by one turn" can mean "never applied".
- The recorded bot's next reply after a cue is barely shorter: median 23 words after rush and after frustration, vs 25 baseline; 26 after confusion; 29 after interest. PROVEN — [DATA-turns]. The PS07 bot did not visibly adapt brevity.
- `latency_repetition.latency.measurements[].seller_had_to_repeat` is indexed by `seller_turn_idx`, so it can be aligned to a turn (turn-level weak label). PROVEN (schema) — [DATA-eval]

### Inferences: replay protocol (ASSUMED design)
1. **Input**: call_turns rows for one attempt_id sorted by `turn_no`; seller context from the seller file; persona v(n) generated for that seller (so the persona loop gets tested on the same run).
2. **Two text views**: replay each call twice, once as-is (Latin) and once transliterated to Devanagari (live tool payload is Devanagari, [SYS]); report metrics separately. Without this, past-data gains may not transfer (99.6% Latin, PROVEN).
3. **Step loop**: for seller turn i: `lex = lexicon(turn_i, history<i)`; `jev_i = jev(state, history≤i)` cached offline; the lexicon decision applies to bot reply i, the Jev decision to reply i+1 (mirrors live). Policy (hysteresis, priority, max 2) applied exactly as live. Write a switch-log row per decision: `turn_idx, signal, source (lex|jev), mode_before, mode_after, directive, cue_text_hash`.
4. **Counterfactual cut**: after the first switch, later seller turns were produced in reaction to the *original* bot, not our directive. Score each signal's first onset and our first switch; ignore what happens after for "did it work". Later onsets of a *different* signal can still be scored for detection (detection doesn't depend on our reply), but not for effect.
5. **Cache Jev** responses keyed by (switcher version, call, turn) so re-runs of the gate are cheap and deterministic.

### Inferences: review rubric (ASSUMED design)
Per seller turn, the reviewer labels which of {frustration, confusion, interest, language_switch, rush, none} are present, with onset = first turn where a careful listener would act. Then each (signal, onset) is matched against the switch log:
- **correct**: a switch for that signal fires at onset turn (lexicon) or onset+1 (Jev window).
- **late**: fires at onset+2 or later; record `delay_turns`; flag the earlier turn's cue as a missed lexicon cue.
- **missed**: no switch for that signal before call end.
- **false**: a switch fires with no true onset of that signal at turn j or j−1.
- **wrong_type**: a switch fires at a true onset but for another signal (e.g. confusion labelled rush).
- **suppressed_ok / suppressed_bad**: policy blocked a correct signal (max 2 switches, priority); judge whether blocking was right.
- **persona_fit**: for each persona setting (language, pace, formality, warmth, opening, objection playbook), was there evidence in the call that it fit or misfit (e.g. seller switched to Tamil in turn 2 → language setting misfit)? Each verdict cites turn indices.
- **guardrail**: did any directive change facts, pricing or compliance (FAQ Q5)? (Only checkable on live/simulated runs where our bot spoke.)
- **abstain**: reviewer must output `uncertain` rather than guess when ASR text is garbled; these go to human queue.

### Inferences: reviewer output JSON (ASSUMED design)
```json
{
  "run_id": "replay:<attempt_id>:switcher_v1:persona_v1",
  "run_type": "replay | simulated | live",
  "switcher_version": "v1", "persona_version": "v1", "reviewer_model": "<id>", "prompt_version": "r1",
  "text_view": "latin | devanagari",
  "turn_labels": [
    {"turn_idx": 5, "speaker": "seller",
     "signals": [{"type": "rush", "onset": true, "confidence": "high|med|low", "evidence_span": [12, 31]}],
     "uncertain": false}
  ],
  "switch_review": [
    {"signal": "rush", "true_onset_turn": 5, "switch_turn": 7, "source": "jev",
     "verdict": "correct|late|missed|false|wrong_type|suppressed_ok|suppressed_bad",
     "delay_turns": 2, "missed_cue_turn": 5, "note": "short"}
  ],
  "persona_fit": [
    {"setting": "language", "value": "hinglish", "verdict": "fit|misfit|no_evidence",
     "evidence_turns": [2, 4], "suggested_value": "tamil"}
  ],
  "outcome_link": {"disposition": "Call Later / Busy", "who_ended": "SELLER", "next_call_disposition": "Not Interested",
                   "causal_claim_allowed": false},
  "weak_label_checks": {"seller_had_to_repeat_turns": [3], "evaluator_gap_types": ["Misunderstood Intent"], "agrees_with_reviewer": true},
  "corrections": [
    {"target": "lexicon", "op": "add_cue", "signal": "rush", "pattern_hash": "...", "scripts": ["latin", "devanagari"]},
    {"target": "jev_criteria", "op": "edit", "signal": "confusion", "text": "..."},
    {"target": "persona_rule", "op": "candidate", "rule": "state=Tamil Nadu -> open in Tamil", "evidence_runs": 1}
  ],
  "needs_human": false
}
```
- Corrections are candidates only; the gate ([LOOPS]) accepts them only if Jev and reviewer agree or a human confirms, and the frozen test set does not regress. DOCUMENTED — [LOOPS]
- Store `cue_text_hash`/spans rather than raw text in any file that might leave `data/` (aggregates-only rule). ASSUMED, follows AGENTS.md.

### Gaps
- No measurement yet of how often Jev and the lexicon disagree on PS07 turns (Jev spike was 49/51 on romanized test items, [SYS]).
- Exact Jev cost/latency for bulk offline replay of ~65K seller turns is unknown; caching needed.

---

## 3. Can existing evaluator outputs or human executive calls check the LLM reviewer?

### Takeaway
The evaluators give a few useful **weak, partly turn-level** labels (seller_had_to_repeat, Misunderstood Intent gaps, Complaint turns, who ended the call, drop sub-dispositions), but they barely agree with our lexicon (kappa ≈ 0.03) and they are themselves LLM outputs, so they are cross-checks for disagreement mining, not gold. The executive calls contain no text, no audio and no language field, so they cannot show how a human adapted; they are only metadata and a confound for next-call outcomes.

### Cited Findings
- Lexicon confusion vs `seller_had_to_repeat`: both 164 calls, lexicon-only 602, evaluator-only 1,866, Cohen's kappa 0.027. Lexicon confusion vs Misunderstood Intent gap: both 230, lexicon-only 536, evaluator-only 2,537, kappa 0.034. PROVEN — [DATA-turns]+[DATA-eval]
- Lexicon frustration/confusion vs Frustrated User/Clarification can't be compared: zero overlap (labels exist only on non-transcribed calls). PROVEN
- Rush-cue calls end by the seller more often: SELLER-ended 15.4% with rush vs 9.5% without; SYSTEM-ended 20.7% vs 35.2%. PROVEN — [DATA-eval]
- Frustrated User (questions schema) calls: meeting-fixed 11.0% vs 23.3%; Clarification 38.5% vs 20.3% (clarifying questions mark engaged sellers); AI Bot Confirmation 18.4% vs 23.1%. PROVEN — [DATA-eval]×[DATA-bot]
- is_loopy calls have 44.8% meeting-fixed vs 20.0%; seller_had_to_repeat 28.6% vs 22.4% (both mark longer, engaged calls, not failures). PROVEN
- Evaluator `disposition.confidence` = "high" on 99.9% of a 3K sample, so it's useless as a confidence weight. PROVEN
- Executive calls: 67,151 calls (Answered 35,600, NotAnswered 31,400), 6,933 sellers, 1,891 employees, modules DSR 57,971 / MERP 7,355 / others small. Dates actually span 2026-07-21 to 2026-09-30, while the dictionary says Aug–Sep only (conflict). Columns are only ids, module, status, start time, durations, ring duration; no recording links. PROVEN — [DATA-exec]; DOCUMENTED — [DICT]
- Answered exec call length: median 91 s (customer leg 76 s), p75 265 s, p90 658 s. PROVEN
- 87.8% of exec-call rows are for sellers who also have bot calls; 787 exec sellers have a transcribed bot call; 219 transcribed Aug–Sep bot calls were followed by an exec call within 7 days. An exec call within 7 days follows 4.3% of Meeting Fixed bot calls vs 1.5–2.0% of others. PROVEN — [DATA-exec]×[DATA-bot]

### Inferences
- **How to check the reviewer instead of trusting it** (ASSUMED): (a) a human-labelled frozen gold set (section 5) is the only true check: report reviewer precision/recall and kappa per signal against it before using its corrections; (b) on all other runs, compute agreement between reviewer and three independent weak sources (lexicon, Jev, evaluator flags: seller_had_to_repeat for confusion/hearing, Misunderstood Intent/Complaint gaps, SELLER-ended + dropped_mid_pitch for rush/frustration) and send the disagreements to a human queue (cheap active learning); (c) use a different model for reviewer than for Jev so errors aren't correlated; (d) re-review a random 5% with a swapped prompt order to measure self-consistency.
- seller_had_to_repeat is a better weak label for "seller didn't hear / ASR-latency issue" than for confusion; treat it as its own optional signal ("audibility") rather than as confusion. ASSUMED
- Executive calls: usable only to (1) flag that a human touched the seller between two bot calls (exclude or control for those in next-call analysis), and (2) give a duration baseline. Any "human adaptation" rules (slow down, switch language, shorten) must be justified from the problem doc and from the PS07 bot transcripts, not from exec calls. ASSUMED
- Human adaptation evidence would need exec-call recordings, which require Airtel authentication and "won't play outside IndiaMART's systems". DOCUMENTED — [DICT]. Asking organisers on Day 1 for 20–50 exec-call recordings is the only route. ASSUMED

### Gaps
- No human-adaptation data in PS07 at all; no source found for what executives say differently.
- No inter-annotator data for any evaluator.

---

## 4. What the reviewer can say about persona fit from outcomes, and the limits

### Takeaway
Outcomes support descriptive, per-seller memory statements ("this seller was rushed and dropped; next time open short") and pooled correlations, but cannot tell whether a persona choice *caused* a better outcome: the PS07 bot used one style, so there is no variation in our persona settings to compare, and next-call outcomes are confounded by redials, executive contact and time.

### Cited Findings
- Next-call transitions (all bot calls, sorted per seller): next-call meeting-fixed after Meeting Fixed 21.7% (n=8,258), after Call Later 8.1% (29,213), after Not Interested 4.4% (57,440), after General 3.7% (44,415). 52,757 sellers have ≥2 answered calls; 139,326 calls have a next call; gap median 1.0 day (p25 0.5 d, p75 13 d). PROVEN — [DATA-bot]. Matches [LOOPS] 4.1% vs 21.7% figures approximately.
- After Not Interested, the next call is also Not Interested 33.1% of the time; after Meeting Fixed, 73.4% of calls have no later answered call. PROVEN
- Transcribed calls with a next call: 6,338. Next-call meeting-fixed by lexicon signal on the current call: frustration 6.0% (n=249) vs 9.8%; confusion 8.6% (432) vs 9.8%; rush 8.6% (1,595) vs 10.1%; interest 9.3% (1,077) vs 9.8%; language switch 8.3% (120) vs 9.7%; loopy 15.0% (755) vs 9.0%. PROVEN — differences are mostly 1–4 points on small n.
- Only 929 sellers have ≥2 transcribed calls (1,985 calls): the content-level per-seller memory test set is small. PROVEN
- Personalisation trials did not beat control (0 for 3). DOCUMENTED — [VALID]
- Correlations are not proof that adapting helps; causal evidence must come from the demo or simulation. DOCUMENTED — [VALID]

### Inferences
- The reviewer may assert: (a) **signal recurrence** per seller (memory input); (b) **misfit evidence inside the call** (seller spoke Tamil while persona was Hinglish; seller asked to repeat after long bot turns); (c) **pooled associations** tagged by evidence tier with n and CI, per [LOOPS] gate (n ≥ 200, CI excludes 0, holds on time split). ASSUMED
- The reviewer may NOT assert that a persona setting caused the outcome, nor that our switch "would have saved" a call. `causal_claim_allowed: false` should be hard-coded for replay runs. ASSUMED
- Outcome labels to attach per run: bot disposition, evaluator sub_disposition, who_ended_call, next-call disposition and gap, exec-contact-within-7-days flag (confound). ASSUMED
- Mean-reversion trap: sellers picked because they were rushed/frustrated will look "better" on the next call regardless. Compare against matched sellers with the same signal and no change, not against themselves. ASSUMED

### Gaps
- No counterfactual data for any persona setting except the trial arms (opening scripts), which are not in the transcribed subset.

---

## 5. Sample sizes per signal and a recommended frozen gold set

### Takeaway
Build a ~350-call, human-labelled, turn-level gold set from **August** turn calls (time split: mine and tune on July, freeze August), seller-disjoint from training, stratified by signal and by Tamil Nadu, with hard negatives, and a Devanagari-transliterated twin. Expect ~60 positives per signal, which gives recall CIs of roughly ±12 points; smaller gains than ~15–20 points won't be distinguishable.

### Cited Findings
- Available positives (lexicon, calls): rush 2,497; interest 1,997; confusion 766; frustration 442; language switch 296 (Tamil Nadu 210 calls total). PROVEN — section 1
- Turn calls by month: Jul 5,229, Aug 6,966, Sep 159. PROVEN
- Devanagari: 24 calls with any Devanagari turn. PROVEN
- [LOOPS] already notes: with ~25–30 positives per signal only ~20-point gains are distinguishable; kappa ±0.26 at n=30. DOCUMENTED
- 95% CI half-width for a proportion p=0.7: n=30 → ±16.4 pts; n=60 → ±11.6 pts; n=100 → ±9.0 pts (normal approximation, 1.96·√(p(1−p)/n)). Arithmetic.

### Inferences: gold set recipe (ASSUMED)
1. **Pool**: Aug 2026 turn calls with an outcome (≈6.9K). Exclude any seller who appears in July tuning data (seller-disjoint), and all 24 Devanagari calls go in automatically.
2. **Strata** (target calls): rush 60, interest 60, confusion 60, frustration 60, language switch 60 (most from Tamil Nadu; add West Bengal/Gujarat/Maharashtra lexicon hits), **hard negatives** 50 (lexicon fired but likely wrong, e.g. "baad mein" in a scheduling context), random 50 (calibration of prevalence). ≈ 350–400 calls, ~1,800 seller turns.
3. **Enrich frustration/confusion** with evaluator weak flags (Misunderstood Intent, Complaint, seller_had_to_repeat, SELLER-ended + dropped_mid_pitch) so the gold set isn't only what our lexicon can already see; otherwise recall is measured on lexicon-biased positives. If time allows, STT ~100 of the questions-schema calls tagged Frustrated User/Clarification (Apr–Jul, 94% with audio) for an independent positive source.
4. **Labelling**: LLM pre-label (reviewer prompt) → two humans confirm/correct per turn using the rubric; 50 calls double-labelled for kappa. Budget ~30 s/call confirmation ≈ 3 hours across two people.
5. **Freeze**: hash the id list and labels; never use it to mine lexicon cues; version it (`gold_v1`). Report per-signal precision, recall, onset delay, both Latin and Devanagari views.
6. **Second split for Loop B**: the 929 sellers with ≥2 transcribed calls — use July call to build memory, check the Aug call for signal recurrence.

### Gaps
- Hand-labelling time at the event is unknown; the 3-hour estimate is a guess.
- Devanagari twin needs a transliteration step (Sarvam transliteration or LLM); not tested on this data.

---

## 6. Reviewer LLM choice under the data-on-premises constraint

### Takeaway
Run the post-call reviewer on the **internal LiteLLM gateway** (VPN) or the **Sarvam LLM**, not OpenRouter, because review sends whole real transcripts; mask phone numbers and names first, and get an organiser ruling on Day 1. OpenRouter stays limited to Jev's short per-turn decisions, which the design already requires.

### Cited Findings
- Hackathon rule: "data used responsibly, no customer data leaves the premises". DOCUMENTED — [REQ]
- Allowed infra: Sarvam, OpenRouter, internal LiteLLM gateway incl. Jev, self-hosted Daytona; core agent must be Sarvam; no new outside vendors. DOCUMENTED — AGENTS.md
- [LOOPS] already says: post-call review sends real seller text to an LLM; use the Sarvam LLM or the internal gateway and get an organiser ruling on Day 1. DOCUMENTED
- OpenRouter key works only from office IPv4 (VPN laptop). DOCUMENTED — [SYS]
- PS07 text is not masked: summaries, transcripts and evaluator quotes contain real seller and company names. DOCUMENTED — [DICT]. The disposition evaluator JSON also carries `alternate_number` and `alternate_person_name` fields with real values in a minority of rows. PROVEN (field presence; values not copied)

### Inferences
- **Internal LiteLLM gateway (preferred for bulk replay review)**: traffic stays inside IndiaMART's routing and logging; can pick a strong model for long-context review; offline, so latency doesn't matter. Risk: what the gateway forwards to upstream providers is not documented here. ASSUMED
- **Sarvam LLM (preferred for the story and for Indic text)**: core vendor already approved, good for Hinglish/Tamil; usable as the second opinion for agreement checks. Risk: weaker long-JSON adherence is unverified. ASSUMED
- **OpenRouter**: third-party routing to several providers; highest exposure for full transcripts; keep it to Jev's per-turn decision and to synthetic/simulated runs. ASSUMED
- **Pre-processing for any reviewer**: regex-mask 10-digit numbers, replace seller/company names from the seller file with placeholders, send `turn_idx` + text only. ASSUMED
- Using two different model families (e.g. gateway model as reviewer, Sarvam as checker, Jev as the switcher) reduces correlated errors in the agreement gate. ASSUMED

### Gaps
- No documented statement of the LiteLLM gateway's model list, data-retention or upstream routing was found in raw/ or wiki/.
- No organiser ruling yet.

---

## 7. Devil's advocate: what replay cannot show

### Takeaway
Replay tests **detection and timing** on real seller language. It cannot test whether our switch changes the seller's next turn or the outcome, it overweights Latin script and Hinglish, and it partly rests on LLM-generated transcripts and labels.

### Cited Findings
- No effect measurement: in PS07 the bot's replies ignore our directives; its reply length barely changes after rush (23 vs 25 words). PROVEN — [DATA-turns]
- But "the PS07 bot never switched" is **not fully true**: in Tamil Nadu, the bot spoke Tamil in 177 of 210 transcribed calls, starting in Tamil in only ~6, i.e. a mid-call language switch happened in ~170 calls; in 35 of the 65 calls where both had Tamil markers, the seller's Tamil came first. So language-switch outcomes in TN already reflect *some* switching by the production bot, probably state- or reaction-driven (mechanism undocumented). PROVEN (counts) / ASSUMED (mechanism) — [DATA-turns]×[DATA-seller]
- Script mismatch: 99.6% Latin in replay vs Devanagari tool payloads live. PROVEN / DOCUMENTED — [SYS]
- Coverage holes: no Apr–Jun transcripts; no personalis/base_vani/summary_va transcripts; Karnataka 3 calls, Kerala/AP 0; Gujarati/Bengali/Marathi seller lexicon hits are small (≤300 calls) and noisy (common Hindi words such as "aapne", "apni" collide with the Gujarati/Bengali markers I first tried). PROVEN
- Transcript text and evaluator labels are LLM outputs of the audio, not human transcripts. DOCUMENTED — [DICT]
- Selection bias: transcribed calls have 22.4% meeting-fixed vs 11.5% overall. PROVEN
- Timing signals (barge-in, silence, speech rate) are not reliable in the turn timestamps; pace/voice can't change mid-call on Sarvam anyway ("Voice is assigned per language at call start"). PROVEN / DOCUMENTED — [SYS]

### Inferences
- Claim honestly: "Replay measured detection precision/recall/onset delay on N real calls; effect on sellers was shown only in simulated/live demo runs." ASSUMED
- Overfitting risk: mining lexicon cues and testing on the same months will inflate gains; enforce the July→August split and seller-disjointness. ASSUMED
- Reviewer circularity: if the same model family writes transcripts (evaluator), labels the gold pre-pass, and reviews, errors agree with each other; human confirmation on gold is non-negotiable. ASSUMED
- Signal definitions drift: "interest" lexicon fires on "kitna/chahiye" which also appear in objections; rubric must define interest as buying/meeting intent, not any question. ASSUMED
- Over-switching: with 39% of calls showing at least one cue and max 2 switches per call, false switches may cost more than misses on short calls (median 4 seller turns). Gate on precision as well as recall. ASSUMED

### Gaps
- Mechanism of the production bot's Tamil switch (rule vs Sarvam language detection) is undocumented.
- No way to estimate the outcome effect of our switches from PS07 alone.
