# Teach the switcher and persona generator between calls

**VANI can learn between runs without any model learning anything. Build it as a deterministic offline pipeline:** every finished run (a live call, a simulated call, or a replayed PS07 call) produces a trace. An offline LLM reviewer labels that trace. A gated updater then writes a new version of two pieces of our own logic. The first is the frozen in-call switcher (lexicon cues, per-signal Jev thresholds, Jev question wording, optionally a tiny classifier). The second is the persona generator (per-seller memory plus global rules with evidence tiers). The data supports this unevenly. **Per-seller memory is the strongest lever.** 40.5% of sellers have two or more answered calls and those sellers hold 71.3% of calls. The previous call predicts the next far better than the profile does: next-call Not Interested AUC is 0.78 from memory vs 0.54 from profile. The switcher loop has the most objective labels: replaying **12,788 transcribed PS07 calls** measures detection precision, recall and timing. Replay cannot show that a switch or a persona *causes* a better outcome. PS07 used one voice and one style, so the honest claim is better detection and better-justified pre-call settings, not more meetings. PS04 never scores "learning". The loop earns points only through switches (25%), fit (25%) and evidence (15%), so it gets about six build hours. Its demo is one story: the same seller, call 1 → review → call 2, plus one held-out v0→v1 table with n and confidence intervals ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md); [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md); [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)).

> **Two binding clarifications from the team lead, applied throughout.**
> 1. **We are not training any model. We are training persona creation and call switches.** Sarvam, Jev and every LLM stay as they are: no fine-tuning, no retraining. What changes between runs is our own logic: persona-generation rules, per-seller memory, evidence tiers, and switch logic (lexicon cues, thresholds, Jev question wording). The optional TF-IDF classifier is part of our switch logic, not model training. Its trade-off is flagged where it appears. Vendors that retrain weights (Coval × Phonely) are context only, not our approach.
> 2. **Voice gender is a persona setting** (PS04 §3.2: voice = gender, accent, pitch, pace). It is chosen before the call for each seller, with a reason and an evidence tier, and it stays fixed for the whole call on Sarvam. Its evidence status and the way review can move it are treated explicitly below.
>
> **Corrections carried in from the notes:** drop the "Coval 70% → 88%" figure, which could not be found in the announcement or by search. Treat the Cekura five-category failure taxonomy as unconfirmed. The transcribed-call count is **12,788** (12,354 of them have an outcome; earlier memory and validation stats used an 11,834-call subset). The wiki's "rush 30.8% vs 21.1%" reads 30.8% vs **20.8%** on the 954-pair recomputation, and its "4.1% after Not Interested" is **4.4%** on the full Apr–Sep data ([industry notes](../research_notes/Between%20run%20learning%20loops/industry_and_research.md); [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md)).

Tags used throughout: **PROVEN** means computed by us on PS07 or in our spikes (aggregates only). **DOCUMENTED** means a published or raw/ source says it. **ASSUMED** means our design or inference.

## One frozen run, one offline review, one gated version bump

The binding team decision sets five rules ([team decision](../../raw/hackathon/2026-10-08-team-decision-between-run-learning.md)) (DOCUMENTED):

- Nothing learns during a call.
- Only the frozen switcher decides switches live.
- An LLM never decides a switch; it only reviews a finished call.
- Review corrections improve both the switcher and the generator.
- PS07 calls count as past runs.

The cycle below makes that concrete. Every arrow after "trace" happens offline, after the call has ended (ASSUMED design, extending the [learning-loops wiki](../../wiki/projects/vani-hackathon/learning-loops.md)):

```
  seller file + per-seller memory(vN) + global rules(vN)
        │
        ▼
  persona generator vN ──► persona spec (voice gender/timbre, language, pace, pitch,
        │                   formality, warmth, opening, playbook, escalation; reason + tier each)
        ▼
  RUN  (live Sarvam call │ simulated call │ replayed PS07 call)
        │   in-call: lexicon decides turn k (<5 ms) · Jev corrects turn k+1 · code policy
        │            (hysteresis, priority, max 2 switches) · NO learning, NO LLM decision
        ▼
  TRACE: turns, switch log (signal, change, reason, source), persona used, versions, outcome
        │
        ▼  (offline, after the call)
  REVIEWER LLM (internal gateway or Sarvam; masked text)
        │   per turn: true signal + onset · per switch: correct/late/missed/false/wrong_type
        │   per setting: fit / misfit / no_evidence · candidate corrections · uncertain → human
        ▼
  TWO-KEY FILTER: reviewer ∧ Jev agree, or a human confirms
        │
        ├──► per-seller memory: append call record (enumerated tags only), recompute summary
        │        └─ applies to that seller's NEXT run with no global gate (delivery only)
        │
        └──► candidate diffs: lexicon cues · θ bands · Jev wording · (opt.) classifier · rule counts
                 │
                 ▼
           GATE on frozen gold set + canaries (per signal, per script; flip list; human approval
           for global rules) ──pass──► switcher vN+1 / generator vN+1 (manifest, rollback = repoint)
                                ──fail──► rejected diff, logged and shown
```

Three kinds of run feed the same pipeline, and they carry different information (ASSUMED, from [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)):

| Run type | What it can teach | What it cannot teach |
|---|---|---|
| **Replayed PS07 call** | Detection and timing on real seller language. Per-seller memory and recurrence. Persona "expectation mismatch". | Whether our switch or persona changed the seller's behaviour. The recorded bot never received our directives. |
| **Simulated call** | Switch timing on paired v0/v1 runs with fixed seeds | Outcome or fit claims. Simulators under-express resistance, and a text-driven seller cannot perceive voice gender or timbre at all. |
| **Live hackathon call** | Real effect of a switch on the next seller turn (qualitative). Guardrail compliance. | Statistics, because there are only a few dozen calls. |

**Replay protocol.** Feed seller turns one at a time with no lookahead. The lexicon decision applies to the bot reply for turn *i*, and the cached Jev verdict to reply *i+1*, mirroring live. Write a switch-log row per decision. Two rules keep replay honest (ASSUMED):

- **Counterfactual cut.** After our first switch, later seller turns were reactions to the *original* bot. Score signal onsets and our first switch, but never "did it work".
- **Two script views.** Run every call twice, once as-is in Latin script and once transliterated to Devanagari. Report the views separately: 99.6% of PS07 turns are Latin script, while live Sarvam ASR emits Devanagari (PROVEN).

Cache Jev responses keyed by (switcher version, call, turn), so that re-running the gate is cheap and deterministic ([replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)).

**Where the reviewer runs.** The reviewer sees whole real transcripts. PS07 text is not masked, and the disposition JSON carries `alternate_number` and `alternate_person_name` fields in a minority of rows (PROVEN field presence). The reviewer should therefore run on the **internal LiteLLM gateway or the Sarvam LLM, not OpenRouter**. Before review, regex-mask 10-digit numbers and replace seller and company names with placeholders. Get an organiser ruling on Day 1 ([PS07 data dictionary](../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md); [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)).

Use a **different model family for the reviewer than for Jev**, so their errors do not correlate. That keeps the two-key filter meaningful (ASSUMED).

### Reviewer JSON essentials

The reviewer emits labels and *candidate* corrections, never directives or spoken text. It labels each seller turn for {frustration, confusion, interest, language_switch, rush, none} with an onset (the first turn a careful listener would act on). It then matches each onset against the switch log. Two settings need care (ASSUMED rubric, [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)):

- **`causal_claim_allowed` is hard-coded `false` on replays.**
- **Voice gender defaults to `no_evidence`.** A transcript rarely says anything about it.

```json
{
  "run_id": "replay:<attempt_id>:switcher_v1:persona_v1",
  "run_type": "replay | simulated | live",
  "switcher_version": "v1", "persona_version": "v1", "reviewer_model": "<id>", "prompt_version": "r1",
  "text_view": "latin | devanagari",
  "turn_labels": [{"turn_idx": 5, "signals": [{"type": "rush", "onset": true, "confidence": "high"}], "uncertain": false}],
  "switch_review": [{"signal": "rush", "true_onset_turn": 5, "switch_turn": 7, "source": "jev",
                     "verdict": "correct|late|missed|false|wrong_type|suppressed_ok|suppressed_bad",
                     "delay_turns": 2, "missed_cue_turn": 5}],
  "persona_fit": [
    {"setting": "language", "value": "hinglish", "verdict": "misfit", "evidence_turns": [2, 4], "suggested_value": "english_heavy"},
    {"setting": "pace", "value": 1.0, "verdict": "misfit", "evidence_turns": [2, 3], "suggested_value": 1.1},
    {"setting": "voice_gender", "value": "F", "verdict": "no_evidence", "evidence_turns": []}
  ],
  "outcome_link": {"disposition": "Call Later / Busy", "who_ended": "SELLER", "causal_claim_allowed": false},
  "weak_label_checks": {"seller_had_to_repeat_turns": [3], "evaluator_gap_types": ["Misunderstood Intent"]},
  "corrections": [
    {"target": "lexicon", "op": "add_cue", "signal": "rush", "pattern_hash": "...", "scripts": ["latin", "devanagari"]},
    {"target": "seller_memory", "op": "set_tags", "tags": ["rushed", "lang=en_heavy"]},
    {"target": "persona_rule", "op": "count", "key": "segment×pace=1.0", "finding": "misfit:rushed"}
  ],
  "needs_human": false
}
```

Store hashes and turn indices, not raw text, in anything that leaves `data/`. Memory stores enumerated tags, never free text. Free text is the poisoning path that AgentPoison-style attacks exploit ([AgentPoison, arXiv 2407.12784](https://arxiv.org/abs/2407.12784)) (DOCUMENTED, not re-fetched).

## PS07 bootstraps both loops with 12,788 replayable calls, for detection only

Only `ps07_call_turns.csv` replays turn by turn. It holds **12,788 calls and 139,555 turns** from Jul–Sep 2026, with a median of 9 turns and 4 seller turns per call and a median length of 52 s. There are **no Apr–Jun transcripts** (PROVEN, [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)).

The turn text is an LLM transcription produced by the `latency_repetition` evaluator, not our ASR ([data dictionary](../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)) (DOCUMENTED). Timestamps are coarse: the median seller response gap is 0.0 s. **Rush must therefore be learned from text, not timing.**

Transcribed calls are biased toward engaged sellers: 22.4% are Meeting Fixed, against 11.5% overall (PROVEN).

Using the romanized lexicon as a noisy proxy, required-signal coverage is uneven. Rush and interest have about 2K positive calls each. Frustration (~440) and language switch (~300, concentrated in Tamil Nadu) are thin (PROVEN, lexicon counts):

| Signal | Calls with cue | % of transcribed calls | Median seller turns left after first cue | Meeting-fixed with vs without cue |
|---|---|---|---|---|
| Rush | 2,497 | 20.8% | 2 | 13.6% vs 26.0% |
| Interest | 1,997 | 16.6% | 3 | 22.5% vs 23.6% |
| Confusion | 766 | 6.4% | 3 | 20.0% vs 23.7% |
| Frustration | 442 | 3.7% | 1 | 12.8% vs 23.8% |
| Language switch | 296 | 2.5% | 3 | 30.4% vs 23.3% |

The "turns left" column is why timing matters. **After the first rush cue only about two seller turns remain**, and 17.2% of first rush cues fall on the seller's last turn. A switch that arrives one turn late is often a switch that never applies ([switcher notes](../research_notes/Between%20run%20learning%20loops/switcher_updates.md)) (PROVEN).

The existing evaluators give useful weak labels: `seller_had_to_repeat` indexed by seller turn, Misunderstood Intent and Complaint gaps, who ended the call, and drop sub-dispositions. They **barely agree with our lexicon**, though. Cohen's kappa is 0.027 for confusion vs `seller_had_to_repeat` and 0.034 for confusion vs Misunderstood Intent, and the evaluators are themselves LLM outputs (PROVEN). They are useful only for disagreement mining, where reviewer, lexicon, Jev and evaluator disagreements go to a human queue. They are not gold.

The richest emotion labels sit on calls with **no** transcript: Frustrated User 140 and Clarification 934, in the older questions schema. 94% of those calls have audio, so Sarvam STT on about 100 of them is the only independent positive source for frustration and confusion. **Executive calls contain no text, audio or language field.** They cannot show how humans adapt; they serve only to flag a confound (a human touched the seller between two bot calls) ([replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)) (PROVEN).

One finding complicates the "PS07 never switched" story. In Tamil Nadu the production bot spoke Tamil in 177 of 210 transcribed calls but started in Tamil in only about 6. **Roughly 170 calls contain a mid-call language switch by the production bot**, through an undocumented mechanism. Language-switch outcomes in Tamil Nadu are therefore already partly treated (PROVEN counts, ASSUMED mechanism).

## Switcher updates rank by value per hour: lexicon cues first, Jev wording last

After each review batch, one deterministic updater script proposes a new switcher version, and it writes the version only if the gate passes. Each component below is our own logic. No vendor model changes: Jev's only inputs are `state`, `instructions` and `criteria`, and it cannot be trained ([learning-loops wiki](../../wiki/projects/vani-hackathon/learning-loops.md)) (DOCUMENTED). Ranked by value per hour (ASSUMED estimates, [switcher notes](../research_notes/Between%20run%20learning%20loops/switcher_updates.md)):

| Rank | Update | What it writes | Live latency | Build | Moves which part of switch delay *d* | Main risk |
|---|---|---|---|---|---|---|
| 1 | **Lexicon cue mining** (weighted log-odds, IndicXlit Devanagari variants, per-cue negation) | `lexicon_vN.json` | 0 (still <5 ms) | 3–4 h | d=1/∞ → d=0, the only path that acts on the current turn | Overfits scripted sim cards; transliteration junk |
| 2 | **Per-signal, per-script threshold band** (Clopper-Pearson / Learn-then-Test) | `thresholds_vN.json` | 0 | 1–2 h | ∞ → 1 | Romanized-fitted θ fails on Devanagari |
| 3 | **Gate + manifest + flip list** (prerequisite for all of the above) | `manifest_vN.json` | 0 | 2 h | — | Gold set too small for subtle regressions |
| 4 | *Optional* char_wb 2–5-gram TF-IDF + logistic regression (one per signal) | `clf_vN.joblib` | ~0.4 ms per turn | 3–4 h | ∞ → 0 on Devanagari | Reviewer errors baked into weights |
| 5 | Jev criteria wording A/B, **at most once** | `jev_questions_vN.json` | ~0 | 2–3 h | d=1 only | A tuned policy cut Jev accuracy 3.67 pts |

**Lexicon mining** uses Monroe et al.'s "Fightin' Words" weighted log-odds with an informative Dirichlet prior from the full PS07 corpus. Plain log-odds explodes on counts of one or two, and chi-square over-ranks rare tokens ([tidylo manual](https://juliasilge.r-universe.dev/tidylo/doc/manual.html)) (DOCUMENTED).

The four review verdicts map onto the training data (ASSUMED):

- **Missed:** the turn becomes a positive for that signal.
- **False:** the turn becomes a negative, attributed to the cue that fired.
- **Late:** turns between the true onset and the actual switch become positives. This is where the earliest cues come from, and so the highest-value update for rush.

A candidate cue must clear five filters:

- z ≥ 2.5–3;
- support in ≥5 distinct calls and ≥3 sellers;
- no hit inside a negation window (each cue is flagged `polarity_sensitive`, because "samajh nahi aaya" *is* the confusion cue);
- a cap on hits against gold negatives;
- at most about 10 new cues per signal per round.

Mine on romanized PS07 text, then generate Devanagari variants with IndicXlit, which converts both ways across 21 Indic languages, is MIT-licensed, and has about 11M parameters ([AI4Bharat/IndicXlit](https://github.com/AI4Bharat/IndicXlit)) (DOCUMENTED). A human approves each batch in about ten minutes. One canonicalisation runs at both mining time and run time:

1. NFD normalisation.
2. Nukta stripping.
3. ँ→ं.
4. Lowercasing.
5. Repeated-letter collapse.

The spike already showed live ASR rendering "busy" as "जी", so Devanagari matching needs this canonical form ([spike log](../../raw/research/2026-10-07-spike-log.md)) (PROVEN).

**Thresholds** should not use isotonic regression. scikit-learn says isotonic needs more than about 1,000 samples, and sigmoid scaling is for small n ([scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html)) (DOCUMENTED). Instead, scan θ from the top down per signal and per script, and stop before the first θ whose one-sided 95% Clopper-Pearson lower bound on precision falls below target. Learn-then-Test formalises this rule ([arXiv 2110.01052](https://arxiv.org/pdf/2110.01052)) (DOCUMENTED). Suggested targets are 0.85 for rush, confusion and frustration and 0.75 for interest (ASSUMED). The bounds set the label budget (PROVEN, computed):

| Correct / predicted | One-sided 95% lower bound on precision |
|---|---|
| 30/30 | 0.905 |
| 27/30 | 0.761 |
| 45/50 | 0.801 |
| 90/100 | 0.836 |
| 180/200 | 0.858 |

Any precision claim needs at least 30 confirmed positives above θ, and separating a 0.90 band from a 0.80 band needs about 100. Keep **separate Devanagari thresholds**, and replace the Devanagari default only after 30 or more Devanagari positives (ASSUMED).

**The optional classifier, framed under clarification 1.** A char-n-gram TF-IDF + logistic regression trained in 0.26 s on 6,000 synthetic turns and scored about 0.37 ms per turn on a laptop (PROVEN, synthetic data only). That makes it fast enough to sit beside the lexicon as a second instant voter: a lexicon hit fires immediately, otherwise the classifier fires at p ≥ θ_high, otherwise the decision defers to Jev on the next turn.

It is our own switch logic, a few thousand weights fitted to our labels. **It is not training Sarvam, Jev or any LLM.** It is the one component whose "learning" is parameter fitting rather than an editable rule, though, and that carries costs:

- It is harder to show judges as a diff than "these 14 cues were added".
- Reviewer label errors get baked into its weights. Models trained on LLM labels show more instability and early plateaus ([arXiv 2504.15432](https://arxiv.org/html/2504.15432v1)) (DOCUMENTED).
- It needs both scripts in its training data to help on live Devanagari.

Keep it only if the gold set shows recall gaps that lexicon cues cannot close. Otherwise drop it and keep the story purely rule-based.

**Jev wording** is the riskiest update. Jev's own docs warn that accuracy falls as unrelated state grows and that it reads negation literally ([Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)) (DOCUMENTED). A third-party benchmark found a tuned policy cut Jev accuracy from 86.20% to 82.53% ([Red Hat Developer](https://developers.redhat.com/articles/2026/10/02/benchmarking-ai-decision-models-against-traditional-guardrails)) (DOCUMENTED).

If attempted, run the A/B this way (ASSUMED):

1. Write at most three candidate wordings per signal, taken from the reviewer's error clusters.
2. Score each on the gold set by AUROC, with a paired bootstrap over calls.
3. Accept a wording only if the 90% CI of the gain excludes zero and no other signal drops more than one point.
4. Recalibrate θ afterwards.

**The timing metric.** Measure switch delay *d* in seller turns from the first true cue: d=0 is on time, d=1 is Jev's next turn, d≥2 is late, and ∞ is missed. Report it before and after the hysteresis policy, so detector lateness is not confused with policy lateness. Keep policy code frozen during the event, so gains can be attributed. The headline is the **d=0 rate for rush on Devanagari gold turns, v0 → v1, with false switches unchanged** ([switcher notes](../research_notes/Between%20run%20learning%20loops/switcher_updates.md)) (ASSUMED).

## Per-seller memory carries the evidence; global rules move slowly

### Memory is the strongest lever, and it decays in a measured way

The base is large. Of 130,129 sellers, **52,757 (40.5%) have two or more answered calls, and they account for 71.3% of calls.** The median gap between a seller's consecutive calls is **1.02 days**, with p75 at 13.1 days. 87.4% of consecutive pairs used the same bot version, so historical persona barely varied between a seller's calls (PROVEN, [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md)).

On a time split (train on pairs before 1 Aug, test on Aug–Sep, 93,417 test pairs), memory beats profile clearly (PROVEN):

| Target | Profile-only AUC | Memory-only AUC |
|---|---|---|
| Next meeting | 0.579 | 0.710 |
| Next Not Interested | 0.540 | 0.776 |
| Next terse (transcribed) | 0.525 | 0.619 |
| Next rush (transcribed) | 0.510 | 0.566 |

Two calls back still adds information. When the last call was Not Interested, the next-call meeting rate is **2.3% if the call before was also Not Interested and 9.5% if it was Meeting Fixed** (PROVEN).

Memory splits into **state**, which decays, and **traits**, which persist:

- **State decays.** Not Interested repeating Not Interested runs **78.3% within 3 days, 65.5% at 4–14 days, 54.7% at 15–45 days and 41.3% beyond 45 days**, which is back to the 41.1% first-call base. An exponential fit gives τ ≈ 28 days and a **half-life of about 20 days** (PROVEN counts, ASSUMED fit).
- **Traits do not decay.** Rush, terse and English-heavy recur at every gap up to and beyond 30 days. Terse sellers repeat 38.5% vs 24.3% even after 30 days (PROVEN, small n).

State should therefore be weighted by `w = exp(−gap/28)` and fall back to profile defaults after about 45–60 days. Traits should be estimated as a per-seller Beta posterior shrunk to the segment rate, so one call moves the estimate partway and two consistent calls move it most of the way (ASSUMED).

Signal recurrence on the 954 transcribed same-seller pairs is real but thin (PROVEN, lexicon labels):

| Signal on call N | P(on N+1 \| on N) | P(on N+1 \| not on N) | n with prior | 95% CI of difference (pts) |
|---|---|---|---|---|
| Rush | 30.8% | 20.8% | 276 | [3.8, 16.2] |
| Terse (≤3 words/turn) | 41.0% | 17.8% | 183 | [15.6, 30.8] |
| Interest | 29.2% | 17.3% | 185 | [4.8, 19.0] |
| Confusion | 25.0% | 7.0% | 68 | [7.6, 28.4] |
| English-heavy | 13.8% | 4.3% | 65 | [1.1, 18.1] |
| Bot-question | 22.9% | 3.5% | 35 | [5.4, 33.3] |
| Frustration | 17.9% | 8.2% | 39 | [−2.4, 21.9] n.s. |
| Regional-language markers | 5.3% | 2.2% | 19 | [−7.1, 13.1] n.s. |

**These numbers show who will rush again, not that a faster pace helps them.** That is the evidence-tier discipline PS04 §3.4 asks for ("be clear about how strong the evidence is and where the generator is making an informed guess") ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)).

Memory also has a property no live switch has. Sarvam fixes the speaker for the call: "The assigned speaker then remains consistent for the duration of the call, even if the caller switches languages mid-conversation" ([Sarvam platform docs check](../../raw/research/2026-10-07-sarvam-platform-docs-check.md)) (DOCUMENTED). Pace is likewise a per-call setting. **A wrong pre-call voice or pace stays wrong for the whole call, and memory is the only lever that fixes it, on the next call.**

### Global rules: Beta-Binomial counts promoted through four tiers

Each generator rule is a (segment bucket × setting × level) cell with an empirical-Bayes Beta prior. For outcome and propensity rules, the prior is fitted from PS07, which makes it huge. For settings PS07 never varied (formality, pace, voice gender, timbre), the prior is weak, with α0+β0 ≈ 2–5. Reviewer findings add misfit counts (ASSUMED pipeline, [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md)). Empirical-Bayes shrinkage typically cuts error 20–50% against raw rates ([MetricGate](https://metricgate.com/docs/empirical-bayes/)) (DOCUMENTED).

A rule changes only when all of these hold (ASSUMED):

- the posterior probability of the claimed direction is at least 0.95;
- effective n is at least 200 (MODERATE) or 2,000 (STRONG);
- it holds on the time split;
- a human approves it.

If reviewer–human κ falls below 0.6, reviewer findings may only *lower* confidence, never change a rule.

| Tier | Condition | Example today |
|---|---|---|
| GUESS | No data; design prior only | Voice gender; "confused sellers prefer lower formality" |
| WEAK | n < 200, or CI includes 0, or literature only | Prior frustration recurs (n=39); objection-type memory (n=20–67) |
| MODERATE | n ≥ 200, P ≥ 0.95, holds on time split | Prior rush recurs (n=276, CI [3.8, 16.2]) |
| STRONG | n ≥ 2,000, time split holds, level stable | P(meeting \| prev Not Interested): 4.5% vs 4.4% across split |
| DEMOTED (drifting) | Direction holds, level drifts | P(Not Interested again \| prev Not Interested): 75.8% Apr–Jul vs 63.4% Aug–Sep |

The drift row matters. A 12-point level shift on a rule with tens of thousands of observations justifies a monthly forgetting factor (λ ≈ 0.8, ASSUMED). It also shows why the time split is part of the gate (PROVEN drift).

**Honest arithmetic.** Two hackathon days yield perhaps 30–60 reviewed live or simulated runs. **No never-varied setting can reach MODERATE.** The visible "learning" on the slide is a few GUESS → WEAK badges and interval-narrowing charts like the monthly series already computed: P(meeting | prev Not Interested) narrows from 2.7% [1.9, 3.7] in April to 4.4% [4.2, 4.6] by September (PROVEN).

### The persona spec, setting by setting

Every setting carries a reason and a tier. The table records what memory and review can move, and what is fixed per call (ASSUMED mapping; tiers per [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md) and the [earlier report](Self%20improving%20persona%20and%20switch%20loops.md)):

| Setting | Pre-call driver | Changes mid-call? | PS07 evidence tier | Per-seller memory can move it when… | Global rule can move it when… |
|---|---|---|---|---|---|
| **Voice gender** | Language catalogue coverage → timbre target → explicit seller evidence | **No** (speaker fixed per call) | **GUESS** | Explicit seller remark about the voice, or repeated audibility misfit across ≥2 calls | Deliberately varied live runs reach n ≥ 200 per cell (not feasible in 2 days) |
| Voice timbre / accent | Warmth and pace level; language | No | GUESS | Audibility misfit (`seller_had_to_repeat` after bot turns), weak | Same as gender |
| Pitch | Carried by voice choice; slider only if audible on v4 | No | GUESS; unmeasured | — | Not a lever until audio-tested |
| Pace | Prior rush/terse (1.1), prior confusion (0.9), call-length band | No (per call) | MODERATE propensity / GUESS helpfulness | Rush or terse trait posterior | Reviewer misfit counts by segment |
| Language start + Hinglish mix | State proxy; prior English-heavy or regional switch | Yes (language switch) | WEAK (n=65 English-heavy, n=19 regional) | Supersede-on-conflict: the latest observed language wins | Pooled misfit by state |
| Formality | Turnover, company type | Yes (wording) | GUESS | Confusion state (≤3 days) → plainer | Reviewer misfit counts |
| Warmth / empathy | Prior Not Interested, frustration, call-later | Yes (tone) | WEAK–MODERATE | Frustration or bot-question tags | Reviewer misfit counts |
| Opening | Last outcome and gap; rush trait | — (first turn) | STRONG for outcome state (n=30,490 Not Interested pairs) | Last outcome, decayed by gap | Rarely; prior is huge |
| Objection playbook order | Last objection category | Yes (directive) | WEAK (n=20–67) | Last objection goes first | Pooled recurrence |
| Escalation | Already in touch with IndiaMART (STRONG, 20.4% vs 1.7%); DNC | Yes | STRONG / fixed gate | Supersede-on-conflict | Never for DNC or AI disclosure |
| Guardrails (facts, price, compliance) | Fixed by FAQ Q5 | Never | — | Never | Never (locked section) |

### Voice gender is a GUESS-tier setting fixed for the whole call

**How it is chosen before the call.** Gender comes out of a deterministic voice resolver; nobody asks the LLM for it. The resolver applies three steps in order:

1. **Language coverage.** The voice must cover the start language. The Bulbul v4 catalogue has 176 voices (112 female, 64 male), but only 3 Gujarati-tagged and 3 Tamil-tagged voices, and Tamil has no conversational or sales voice (PROVEN, [distinctness notes](../research_notes/Self%20improving%20persona%20and%20switch%20loops/distinctness.md)). For a Gujarati start, the choice is effectively Bhavik (male, "calm and flat") or Pooja (female, "warm, slow and expressive") ([persona block notes](../research_notes/VANI%20problem%20choice%20and%20system%20design/persona_block.md)).
2. **Timbre target.** The warmth and pace levels pick between, for example, a "crisp" sales voice and a "warm" one.
3. **Explicit per-seller evidence**, if any exists.

The resulting spec line reads like this example: *"Voice gender: female (Ritu – Sales Agent). Reason: warmth = high and pace = 0.95 call for a warm, lively Hindi sales voice; no PS07 evidence links bot gender to outcomes. Tier: GUESS. Fixed for the whole call."* Per FAQ Q6, a GUESS-tier setting is marked low confidence.

**What PS07 can and cannot say.** PS07 has no bot-voice column and no seller-gender column ([data dictionary](../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)). PS04 states VANI "talks to every seller in one voice and one style" ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)). With no variation in the treatment, no outcome comparison by voice gender is possible, so **gender is GUESS tier** (DOCUMENTED absence). The recordings, 88.3% of bot calls with URLs, could at most confirm which voice each bot version used. Whether any version used a different voice is a Day-1 question.

**What between-run review can move.**

- **Per seller:** the reviewer can rarely find gender evidence in a transcript, so the default verdict is `no_evidence`. Memory changes a seller's voice gender only on an explicit remark about the voice, or on repeated audibility misfit across at least two calls. Even then it is mostly a *timbre* change, and gender changes only if the catalogue forces it. Otherwise gender stays stable across calls, because a consistent caller is the safer default (ASSUMED).
- **Globally:** a gender rule can rise from GUESS to WEAK only on reviewed *live human* calls where gender was deliberately varied within a segment. Simulated sellers hear our voice as ASR text, so **sim runs carry zero information about gender**. A few dozen live calls cannot reach n ≥ 200 per cell, so for the hackathon gender stays GUESS, and the slide should say so (ASSUMED).

**Stereotyping risk.** Persona generators collapse toward stereotypes. The models with the best per-persona fidelity "consistently produce the most stereotyped populations" ([arXiv 2604.24698](https://arxiv.org/abs/2604.24698)) (DOCUMENTED). Score-driven memory evolution erodes fairness constraints even when the task is benign ([TAME, arXiv 2602.03224](https://arxiv.org/html/2602.03224)) (DOCUMENTED). Three hard rules follow (ASSUMED):

- The gender rule may key only on catalogue coverage, the timbre target, and explicit per-seller evidence. It may never key on business category, region-as-culture, or turnover.
- **Never infer a seller's gender** from names or any other field. That is both stereotyping and personal-data processing.
- Run a deterministic audit that flags any segment where voice gender is more than ~80% one way unless the language catalogue forces it.

Gender still contributes to distinctness among demo sellers, through farthest-point selection with "both genders" as a constraint. Present that honestly as a distinctness choice, not an evidenced fit choice.

## A gate that outranks the reviewer: gold set, canaries, two keys

The research is blunt about self-improving loops judged by an LLM. In one self-improving agent, a 100% pass rate concealed 68% true capability, and corrupted ground truth led an optimiser to **delete correct rules**. A judge calibrated on 15 items hit 80% agreement but only 51.9% on the full 54. The documented remedies are frozen holdouts, canary cases, capability-disjoint roles, and acceptance checks that outrank the judge ([Wahi, arXiv 2609.02246](https://arxiv.org/abs/2609.02246)) (DOCUMENTED). Cekura reports that an intermediate "100% on the subset" hid two regressions that only a full-set sweep caught ([Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)) (DOCUMENTED). VANI's design already maps onto three of those remedies:

| Remedy | VANI equivalent |
|---|---|
| Frozen holdout | The frozen gold set |
| Acceptance checks that outrank the judge | Two-key labels plus deterministic switch-log checks |
| Capability-disjoint roles | The reviewer is not the live decider |

**Canaries were missing, and are added below.**

**Gold set recipe** (ASSUMED, [replay notes](../research_notes/Between%20run%20learning%20loops/ps07_replay_and_review.md)):

1. **Source.** About 350–400 **August** transcribed calls, about 1,800 seller turns. Mining and tuning use July only, and the gold sellers are disjoint from tuning sellers.
2. **Strata.** 60 calls each for rush, interest, confusion, frustration and language switch, plus 50 hard negatives (the lexicon fired but was likely wrong) and 50 random calls for prevalence. All 24 Devanagari calls go in automatically, and every call gets a transliterated Devanagari twin. Frustration and confusion strata are enriched from evaluator flags, so the set is not limited to what our lexicon already sees.
3. **Labelling.** The LLM pre-labels; two humans confirm each turn, about 3 person-hours in total; 50 calls are double-labelled for κ.
4. **Freezing.** Hash the call list and labels, and never mine cues from the set.

About 60 positives per signal gives recall CIs of about ±12 points. **Gains smaller than ~15–20 points will not be distinguishable**, and κ at n=30 is only ±0.26 ([learning-loops wiki](../../wiki/projects/vani-hackathon/learning-loops.md)) (PROVEN arithmetic).

**Canaries** (ASSUMED). Add 5–10 replay calls with a planted, known signal and 5 with none. A reviewer or updater that "improves" by labelling everything as a signal fails the no-signal canaries, and a perfect score on the planted ones signals leakage. For the generator, add about 6 canary sellers: all fields missing, DNC=1, contradictory fields, price-heavy objections. These check FAQ Q5 and Q6 behaviour on every version.

**Gate rule** (ASSUMED):

- **Labels.** A label enters training only on two keys: the reviewer (blind to Jev) and Jev agree beyond θ, or a human confirms. "The switch fired" is never a label.
- **Switcher versions.** vN+1 ships only if, per signal and per script, precision and recall at the operating point drop by no more than 1 point, macro-F1 improves, false switches on gold calls do not rise, and every canary passes.
- **Flip list.** Every gold turn that was correct in vN and becomes a false switch in vN+1 needs human sign-off, because ~300 turns can only catch large regressions statistically.
- **One component per version.** Each version changes one component, so gains are attributable.
- **Manifest and rollback.** A manifest records parent version, label batches, gold hash, metrics and verdict. Rollback repoints `current`.
- **Approval levels.** Per-seller memory auto-applies enumerated tags. Global rules and lexicon batches need human approval, mirroring SquadStack's "every change … reviewed by a human" and its locked compliance sections ([SquadStack Lift](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)) (DOCUMENTED).

**Checking the reviewer.** Report reviewer-vs-human precision, recall and κ per signal on gold before any of its corrections count. Use chance-corrected agreement, not percent agreement ([Judging the Judges, arXiv 2406.12624](https://arxiv.org/html/2406.12624)) (DOCUMENTED). Re-review a random 5% with the prompt order swapped to measure self-consistency (ASSUMED).

**The proof plan, stated as claims.** The plan has two halves (ASSUMED).

*What the loop can claim:*

- **Switcher:** per-signal precision, recall and d=0 rate, v0 → v1, on frozen gold, reported for both scripts, with paired-bootstrap CIs over calls.
- **Generator, predictive validity:** each spec declares expected signals and outcome propensities, scored by AUC/Brier against held-out sellers' *next real call*. Today's PROVEN baseline is profile → profile + memory: meeting 0.58 → 0.71, Not Interested 0.54 → 0.78, terse 0.53 → 0.62.
- **Generator, expectation-mismatch rate:** on replays, how often the seller's real behaviour contradicted the spec.
- **Generator, deterministic checks and a fit judge:** the judge counts only if κ ≥ 0.6 against 30–50 human-labelled specs.

*What the loop cannot claim:*

- Any meeting or conversion uplift. Off-policy evaluation needs overlap, and PS07 has one style ([DOLCE, arXiv 2505.00961](https://arxiv.org/html/2505.00961v3)) (DOCUMENTED). IndiaMART's own three static-personalisation trials all failed to beat control ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)) (PROVEN).
- "It learned from our demo calls."

## The demo is one seller: call 1, review, call 2

The learning segment should take 60–90 seconds of a 5–7 minute slot (ASSUMED script combining [industry notes](../research_notes/Between%20run%20learning%20loops/industry_and_research.md) and [persona learning notes](../research_notes/Between%20run%20learning%20loops/persona_learning.md)). All numbers on screen must be real results; the figures in the notes are placeholders.

1. **Call 1 (simulated or live, persona v0).** A seller with no history gets defaults at LOW confidence: Hinglish, pace 1.0, a relationship opener, voice gender GUESS. In turn 2 the seller says a Devanagari rush phrase ("jaldi bolo, meeting hai"). The v0 lexicon has only the romanized cue, so it misses. Jev fires on turn 3 (d=1). In turn 4 the seller switches to English, and the language switch fires correctly. The switch log shows both rows.
2. **Review card (≤10 s on screen).** Rush: *late*, onset turn 2, missed cue at turn 2. Language switch: *correct*. Persona fit: pace *misfit* and language *misfit*, both citing turns; voice gender *no_evidence*. Jev agreed on the rush label, so the two-key filter accepts it. Corrections: one Devanagari rush cue (candidate), and memory tags `rushed`, `lang=en_heavy`.
3. **Gate.** The cue batch runs on the frozen gold set: rush d=0 rate and recall on Devanagari gold turns go up, other signals hold within CI, the flip list is empty, and canaries pass. **Show one rejected diff alongside.** For example, a candidate cue that raised false rush switches on hard negatives was dropped. The rejection proves the gate is real.
4. **Call 2 (same seller, persona v1, switcher v1).** The spec diff is on screen. Pace 1.1, reason: "rushed last call (gap N days); rush recurs 30.8% vs 20.8% (MODERATE)". Language starts English-leaning, reason: "switched to English last call (WEAK)". The opening is time-boxed. **Voice gender is unchanged**, reason: "no evidence from call 1 (GUESS)". The rush cue now fires on the same turn (d=0).
5. **One table.** v0 vs v1 per-signal P/R/d=0 on held-out gold, n per signal, CIs, both scripts. Underneath, one line: "learning came from N PS07 replays + M event calls". Next to it, a different held-out seller improving or honestly not improving, which answers "is call 2 just memorised?"

Judges will probe five points, and each has a prepared answer:

| Probe | Answer |
|---|---|
| Who checks the checker? | κ vs humans, canaries, the flip list |
| Did anything get worse? | The full per-signal table, not just the fixed signal |
| Would this lift meetings? | Not shown, and past trials failed |
| Is an LLM deciding live? | No; Jev p95 is ~1.4 s and Sarvam replies take ~2.1 s, so the live path is lexicon + code ([spike log](../../raw/research/2026-10-07-spike-log.md)) (PROVEN) |
| Is this pre-built? | The loop code was written at the event |

## Scope check against PS04: about six loop hours, cut in this order

PS04's deliverables are generator code, a spec per seller with reasons, a Sarvam demo with at least one live switch, a switch log, and one slide. Its criteria are fit 25, switches 25, distinctness 20, voice 15 and evidence 15. **None mentions learning across runs** ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)) (DOCUMENTED). Core deliverables already cost about 20–30 dev-hours against about 18–24 usable hours, so loop work is capped at about 6 hours ([learning-loops wiki](../../wiki/projects/vani-hackathon/learning-loops.md)).

The full design below is about 15 hours of loop-specific work. **The six-hour version keeps four pieces:**

- the reviewer (rows 2–3);
- the gold set and gate (rows 4–5);
- a lite replay harness;
- reviewer-proposed cues approved by hand, instead of full statistical mining.

Per-seller memory sits inside the core generator budget, because it *is* fit and evidence. Hours are ASSUMED estimates.

| # | Piece | Serves | Est. hours | Cut order (1 = first cut) |
|---|---|---|---|---|
| 1 | Trace + switch log with version fields | D4 switch log; switches 25 | 0.5 | never |
| 2 | Per-seller memory store (rebuilt as of time *t*, no leakage) → pre-call settings with reasons and tiers, including gender | D2; fit 25, evidence 15, distinctness 20 | 1.5–2 (core) | never |
| 3 | Reviewer prompt + JSON schema + masking on gateway/Sarvam | All loops | 1.5–2 | never |
| 4 | Gold set + Devanagari twin + canaries | Switches 25; robustness | 1 dev + ~3 labelling (non-tech) | never (shrink to ~150 calls if behind) |
| 5 | Gate + manifest + flip list | All loops | 1.5–2 | never |
| 6 | PS07 replay harness (no lookahead, Jev cache, two script views) | Switches 25 | 2–3 | 8 (shrink to gold-only replay) |
| 7 | Lexicon mining (log-odds + IndicXlit + negation) | Switches 25 | 3–4 | 7 (fall back to hand-approved reviewer cues, ~1 h) |
| 8 | Per-signal, per-script threshold band | Switches 25 | 1–2 | 6 (keep defaults) |
| 9 | Rule tier cards with Beta intervals by month | Evidence 15 | 1 | 5 |
| 10 | Predictive-validity metric on next real call | Evidence 15, fit 25 | 1–2 | 4 |
| 11 | Char-n-gram classifier (optional switch logic) | Switches 25 (marginal) | 3–4 | 3 |
| 12 | STT of ~100 questions-schema calls for independent positives | Gold quality | 2 | 2 |
| 13 | Jev criteria A/B (once) | Switches 25 (marginal) | 2–3 | 2 |
| 14 | Failure-clustering dashboard | Nothing scored | 2–4 | **1** (use a static chart) |

**Out of scope, flagged.** Five items are out:

- Fine-tuning or retraining any model, per clarification 1 and with no GPU.
- Weight-level self-improvement in the Coval × Phonely style. Coval says its findings "inform ongoing updates to the customer's model" ([Coval](https://www.coval.ai/blog/new-self-improving-agents/)) (DOCUMENTED). That is context only, and it publishes no controlled results.
- Live A/B ramps in the SquadStack style, bandits, GEPA prompt evolution and RL from dials. None is scored, and all need traffic we do not have.
- Post-call *quality scoring* of the agent's replies, which drifts toward the Quality Audit problem.
- Any learning that changes facts, prices or compliance text (FAQ Q5).

Vendor uplift figures stay out of the pitch. Cekura's 75% → 100% and SquadStack's 1.5% → 2.7% bookings are uncontrolled vendor claims ([industry notes](../research_notes/Between%20run%20learning%20loops/industry_and_research.md)). Their *patterns* are legitimate prior art for each guard, since VANI writes its own loop: full-set sweeps, failed call → regression case, one change at a time, locked sections and human approval ([Hamming runbook](https://hamming.ai/blog/failed-production-call-regression-test-runbook)) (DOCUMENTED).

## Risks and the Day-1 questions that decide scope

| Risk | Mechanism | Guard |
|---|---|---|
| **Script mismatch** | Gains mined on 99.6% Latin replays do not transfer to live Devanagari ASR | Devanagari twin in gold; per-script thresholds; headline on Devanagari |
| **Judge drift / hacking** | The reviewer labels every slow reply "confusion"; reference-free judges inflated pass rate 0.72 → 0.94 at flat true accuracy ([arXiv 2607.05904](https://www.alphaxiv.org/abs/2607.05904)) | κ on gold, canaries, two keys, cross-family reviewer |
| **Recency overfitting** | One bad event call rewrites a global rule | Event calls enter per-seller memory only; global rules need n ≥ 200 + time split |
| **Forgetting** | A Gujarati cue causes Hindi false positives | Full-suite per-signal gate and flip list |
| **Memorisation** | Scripted sim cards supply both cues and tests | Sim cards excluded from mining and gold; seller-disjoint July → August split |
| **Self-fulfilling memory** | "Not Interested → short exit" makes Not Interested recur and "confirms" itself | Report it as a limitation; mean-reversion check against matched sellers |
| **Stale or poisoned memory** | Models handle implicit memory invalidation poorly (best 55.2% on STALE) ([arXiv 2605.06527](https://arxiv.org/abs/2605.06527)) | Supersede-on-conflict and expiry in code; enumerated tags only |
| **Safety and fairness erosion** | Memory evolution erodes constraints ([TAME](https://arxiv.org/html/2602.03224)); gender stereotyping | Locked guardrail sections; gender rule features restricted; segment audit |
| **Data leaving premises** | Reviewer sends full transcripts | Gateway/Sarvam only, masking, organiser ruling |
| **Time** | The loop displaces the live switch or voice demo | If the demo and live switch are not working by Day-1 evening, keep only rows 1–5 |

Ask these on Day 1:

1. Does sending masked PS07 transcripts to the internal LiteLLM gateway or the Sarvam LLM count as leaving premises? What does the gateway forward upstream?
2. Which sellers are "every sample seller", and will judges accept a "same seller, second call" demo framing?
3. Are the PS04 weights final, and is cross-run learning rewarded inside "switches" or "evidence" at all?
4. Did any historical bot version use a different voice or gender? This is the only way voice gender could leave GUESS tier.
5. Can 20–50 executive-call recordings be shared? They are the only source of human-adaptation evidence.
6. What mechanism made the production bot switch to Tamil mid-call?
7. Is IndicXlit acceptable as an open-source framework under the no-pre-built rule? How fast is it on our CPU?
8. How accurate is Jev on transliterated Devanagari, and how many positives per signal does the enriched gold set actually yield?
9. Do per-session pace and pitch take effect on Bulbul v4 speakers? This decides whether pitch is a setting at all.

## Conclusion

The two clarifications sharpen the design rather than weaken it. Every component that changes is an inspectable artefact: a cue list, a threshold band, a question wording, a memory record, a rule with a tier. Each "learning step" can therefore be shown as a diff with its evidence, which no weight update allows. The data adds one asymmetry. The switcher loop has near-objective labels and a measurable timing target, but little data on the rare signals. The generator loop has abundant data on *who* behaves *how*, but no data at all on whether a delivery choice helps. Voice gender is the extreme case: it is audible, fixed for the call and a real distinctness lever, and it has no evidence behind it.

The implication for judging is that the most defensible "self-improving" artefact is the gate and the per-seller diff, not a curve. A judge who sees one rejected edit, a GUESS badge left honestly on gender, and a call-2 spec whose every changed field cites call 1 has seen a team that knows the difference between learning and drifting. That earns more fit, switch and evidence points than any claim of a system that keeps getting better.

## Addendum: the conversation plan (including personalisation) is required, and it learns too

**Yes, we need it.** PS04 §3.3 requires every persona to carry a conversation plan: opening, personalisation, objection playbook, escalation rules and guardrails, "every element must be tied to seller data". Deliverable 2 is a spec per seller "covering voice, language, tone **and conversation plan**". The deck's build item #3 repeats this ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md); [persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md)) (DOCUMENTED). The fit criterion (25%) scores "voice, language, tone *and plan*". Dropping the plan loses part of fit and fails a deliverable.

**What changes because of it:**

- **The persona is not only "how it sounds".** Each seller's spec gets five plan fields alongside the 8 delivery settings: voice gender, language, pace, pitch, formality, warmth, opening style and objection playbook. Each plan field carries a reason, an evidence tier and a confidence level.
- **What "personalisation" means here is not defined in PS04, so this is our reading.** It appears as one *element of the conversation plan*, listed between "opening" and "objection playbook", with the rule "every element must be tied to seller data". "One persona per seller" is a separate requirement: the title "a persona built for each seller" and FAQ Q1. So personalisation most likely means tailoring what the call says to this seller. Either reading is met if each plan element uses this seller's data. Confirm with organisers on Day 1. Also note that "lift from the personalised opening" is a success metric of **Problem 2 (Global Context)**, not PS04. PS04 does not score personalisation lift.
- **In practice, personalisation means referencing the seller's own data, not changing facts.** Examples are their category, city, how long they've been on IndiaMART, the last call ("you asked us to call back"), or their last objection. FAQ Q5 still applies: no change to product facts, prices or compliance text. Every personalisation line must cite a field that is actually present in the seller file. If the field is missing, use a generic line marked LOW confidence (FAQ Q6).
- **Risk, not a reason to skip.** IndiaMART's three static-personalisation trials didn't beat control. One of them kept sellers talking (Not Interested fell from 13.1% to 5.5%) but didn't close ([persona data validation](../../wiki/projects/vani-hackathon/persona-data-validation.md)) (PROVEN). So deliver personalisation, keep it short, and don't claim meeting lift from it.
- **Per-seller memory feeds the plan directly.** It sets the opening (from the last outcome and gap, STRONG), the playbook order (last objection first, WEAK), escalation ("already in touch with IndiaMART", STRONG) and the personalisation line (what happened last time).
- **The plan is learnable between runs, with no model training:**
  - The reviewer marks per plan element: did the opening land or did the seller cut it off? Was the personalisation line wrong or unwelcome? Did the playbook order match the objection that actually came? Should escalation have fired?
  - These become rule edits: opening variant per segment, playbook order, which seller fact to use for personalisation, escalation triggers. They follow the same tiers and the same gate as the delivery settings.
- **Live switches act on the plan too.** A rush switch cuts the remaining plan to the callback offer. A confusion switch replays the current plan step in simpler words. The switch log records which plan step changed.
- **Effort.** The plan adds maybe 2–3 hours to the generator: templates for 3 openings × 3 playbooks, a personalisation slot filler with a field-presence validator, escalation rules. The Sarvam LLM phrases inside fixed slots. It belongs in the core budget, not the loop budget.
