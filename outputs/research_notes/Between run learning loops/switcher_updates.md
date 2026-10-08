# Between-run updates for the frozen seller-signal switcher

As of 2026-10-08. Tags: **PROVEN** = measured by us (spike log, local benchmark, or local aggregates); **DOCUMENTED** = stated in vendor docs, papers or third-party write-ups; **ASSUMED** = our inference or an untested design value. No customer text appears here. Only aggregates are quoted, taken from earlier notes.

Binding design (not re-argued here): [team decision](../../../raw/hackathon/2026-10-08-team-decision-between-run-learning.md), [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md), [system-design](../../../wiki/projects/vani-hackathon/system-design.md).
- **In-call:** the lexicon (romanized + Devanagari, NFD) decides the current turn in under 5 ms. Jev runs in the background and corrects the next turn. A code policy applies hysteresis, priority and a cap of 2 switches. No LLM sits in the live path.
- **After each run:** an offline LLM reviewer labels the true signal for each turn and marks each switch as missed, false or late.

These notes **extend** [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md). That file covered Jev knobs, the conformal band, the teacher choice and a comparison of mechanisms, and assumed the teacher ran live. The team decision moves all learning **between runs**, so live-teacher and kNN-in-state ideas are reused here only as offline tools.

## Q0. Recommended update mechanics, one line per component

### Takeaway
After each review batch, run one deterministic "updater" script. It writes a new switcher version only if the gate passes. Steps, in order of value per hour:
1. Mine and add lexicon cues, with Devanagari variants generated automatically.
2. Recalibrate the per-signal Jev threshold band with a binomial bound.
3. Retrain the char-n-gram classifier.
4. At most once, run a small offline A/B of Jev criteria wordings.

Everything is gated on a frozen, hand-labelled gold set that contains both Devanagari and romanized turns, with a per-signal non-regression rule. Labels count only when two keys agree.

### Cited Findings
- PROVEN: Jev via OpenRouter has p50 491 ms on keep-alive. Under 4 concurrent calls, p50 is 1,033 ms and p95 1,406 ms. Agreement was 49/51 on romanized turns only. The tool payload is Devanagari with ASR errors, and nukta handling needs NFD. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- PROVEN (aggregate): ps07 has 64,625 seller turns, 99.37% in Latin script and 0.18% in Devanagari. The median call has 5 seller turns. After the first rushed cue, a median of 2 seller turns remain. — [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md) (from decision_block.md)
- DOCUMENTED: Cekura's loop is "Run thousands of synthetic conversations against every release. Gate every deploy on the suite", then "flags issues → reproduces in simulation → suggests fixes". — [cekura.ai](https://www.cekura.ai/)
- DOCUMENTED: Cekura validates a proposed fix "against a frozen held-out regression suite before shipping" and scans for prompt overfitting. Coval clusters recurring failures from real calls and feeds them back (vendor claims). — [last30days voice-agent dump](../../../raw/research/2026-10-08-last30days-voice-agents-learning-from-past-calls.md)

### Inferences
- ASSUMED **component table.** "Live latency" is what the component adds to the in-call path. "Build" means hackathon hours after the gold set exists.

| # | Component | What the update writes | Live latency | Build | Evidence strength | Main risk |
|---|---|---|---|---|---|---|
| 1 | Lexicon mining | `lexicon_vN.json` (cue, signal, script, weight, provenance) | 0 (still under 5 ms) | 3–4 h | Fightin' Words is a standard method; char n-grams are robust to Hinglish spelling | Overfits to scripted sim-seller cards; negation false alarms |
| 2 | Jev criteria A/B | `jev_questions_vN.json` | 0 (token count barely moves) | 2–3 h for one pass | Weak and mixed: the Red Hat tuned policy lost 3.67 points | Wording overfits; criteria and instructions drift apart |
| 3 | Threshold band per signal | `thresholds_vN.json` (θ_high, θ_low per signal, per script) | 0 | 1–2 h | Strong method (Clopper-Pearson / LTT); small n gives loose bounds | Romanized→Devanagari shift breaks exchangeability |
| 4 | Char-n-gram classifier | `clf_vN.joblib` | ~0.4 ms per turn (PROVEN, synthetic) | 3–4 h | Char TF-IDF beats word n-grams on code-mixed text (DOCUMENTED) | Teacher errors get baked into weights |
| 5 | Gate + versioning | `manifest_vN.json` + gold-set report | 0 | 2 h | Industry practice (Cekura); LTT for the statistics | Gold set too small to detect regressions |
| 6 | Timing metric | Report only | 0 | 1 h | Our own definition | Depends on cue-onset labels |

### Gaps
- No published system does exactly this: between-run updates of a cue lexicon plus Jev thresholds for voice switching. All of the evidence is borrowed from text classification and eval practice.

## Q1. Lexicon learning from reviewer-labelled misses and false alarms

### Takeaway
Use **weighted log-odds with an informative Dirichlet prior** (Monroe et al. "Fightin' Words"). The positive class is turns the reviewer labelled with signal S, the negative class is all other seller turns, and the prior is the full ps07 turn corpus.
- Candidates: word 1–3-grams, after NFD normalisation and transliteration into **one canonical script**.
- Keep a candidate only if it passes all four checks:
  - z ≥ ~2.5–3.
  - Support ≥ 5 distinct calls.
  - Not inside a negation window.
  - Never fires on more than a fixed share of gold negatives.
- False alarms run the same machinery in reverse. Cues that fire mainly on negatives get demoted or get an exception pattern.

Generate the Devanagari↔romanized variants of each accepted cue with **IndicXlit** (roman→native). Do not hand-write variants. A human approves the list in about 10 minutes per batch.

### Cited Findings
- DOCUMENTED: Monroe, Colaresi & Quinn (2008), "Fightin' Words", *Political Analysis* 16:372–403. It weights log-odds ratios by a prior. The default empirical-Bayes prior inflates each group's counts by the total counts across groups, a moment-based Dirichlet estimate. The method addresses the fact that "the log odds ratio alone does not account for sampling variability". — [tidylo manual](https://juliasilge.r-universe.dev/tidylo/doc/manual.html); [JHU lecture notes](https://nlp-css-601-672.cs.jhu.edu/sp2024/files/0124.LogOdds.pdf); [tidy text mining](https://bookdown.org/Maxine/tidy-text-mining/weighted-log-odds-ratio.html)
- DOCUMENTED: IndicXlit converts both ways, "Roman to native script and native to Roman script", across 21 Indic languages including Hindi. It is ~11M parameters, MIT licensed, and on pip as `ai4bharat-transliteration`. Aksharantar English→Indic accuracy ranges from 28.76% (Kashmiri) to 84.69% (Telugu). The README gives **no** CPU latency. — [AI4Bharat/IndicXlit](https://github.com/AI4Bharat/IndicXlit)
- DOCUMENTED: `indic_transliteration` (MIT, pip `indic_transliteration`) handles **formal** schemes: ITRANS, IAST, HK, OPTITRANS. Its "lay Indian search terms" feature simplifies formal romanizations, for example "kRShNa"→"krishna". It is deterministic, but it is not a model of informal Hinglish spellings such as "nahi/nai/nhi". — [indic_transliteration_py](https://github.com/indic-transliteration/indic_transliteration_py)
- DOCUMENTED: Character-level models handle spelling variants such as "nahi", "nahin", "nah" and "nai". Code-mixed text has no spelling standard. Char n-gram TF-IDF outperforms word n-grams for code-mixed sentiment. — [search summary of arXiv 1808.03299](https://arxiv.org/pdf/1808.03299); [HIT, arXiv 2105.14600](https://arxiv.org/pdf/2105.14600)
- DOCUMENTED: Hinglish speakers "switch to Hindi when expressing negative emotions and to English when expressing positive emotions", and models "overgeneralise this heuristic". Script and language choice is itself a signal, and it can mislead. — [arXiv 2402.03137 (SIGTYP 2024)](https://arxiv.org/abs/2402.03137)
- PROVEN: Live ASR produced "अभी जी हूं यार" for "अभी बिजी हूँ यार". Cue matching needs Devanagari plus NFD (nukta ज़). — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences
- ASSUMED **canonical form.** Before matching, at mining time and at run time, apply this pipeline to each text:
  1. NFD normalisation.
  2. Strip nukta (U+093C) and chandrabindu/anusvara variants. For example, map ँ→ं, so "हूँ" and "हूं" match.
  3. Lowercase the Latin text.
  4. Collapse repeated letters ("jaldiii"→"jaldi").
  5. Strip ZWJ/ZWNJ.

  Then keep **two cue tables**:
  - a Devanagari table, which is what live sees;
  - a romanized table, used for replaying ps07.

  Mine on ps07 romanized text, transliterate with IndicXlit to Devanagari, and test on Devanagari. The reverse (native→roman) creates romanized variants for replay.
- ASSUMED **transliteration choice.** Use IndicXlit for informal romanized Hinglish→Devanagari. It is a learned model and gives top-k candidates, so keep the top 2–3 per cue word. Use `indic_transliteration` only for deterministic Devanagari→ITRANS-ish keys. Do a **CPU timing check** for IndicXlit: it runs offline, so even 50–100 ms per word is fine, but ~5K turns × ~8 words could take minutes. Cache results per unique token.
- ASSUMED **scoring recipe** (about 60 lines of numpy):
  - δ_w = log((y_w+α_w)/(n_pos+α_0−y_w−α_w)) − log((x_w+α_w)/(n_neg+α_0−x_w−α_w)).
  - Var ≈ 1/(y_w+α_w) + 1/(x_w+α_w).
  - z = δ/√Var, with α_w = prior count of w in the full ps07 corpus × a scale such as 0.01–0.1.

  Prefer this to chi-square. Chi-square over-ranks rare tokens and has no notion of a prior. Plain log-odds explodes on counts of 1–2.
- ASSUMED **min support.** A cue must appear in ≥5 distinct positive calls and ≥3 distinct sellers or cards. This stops one talkative seller or one scripted sim card from creating a cue. Cap new cues at ~10 per signal per round.
- ASSUMED **negation handling.** Add a 3-token scope check before a cue.
  - Negators: nahi/nahin/nhi/na/mat/नहीं/ना/मत/not/no/don't.
  - Also check the after-cue form common in Hindi ("जल्दी नहीं है").

  Examples: "busy nahi hoon" must not fire rush, and "samajh aa gaya" must not fire confusion. The positive form "samajh nahi aaya" **is** the confusion cue, so negation must be handled **per cue**: each cue carries `polarity_sensitive: true/false`. Mine negated bigrams as their own candidates rather than stripping negators globally. The Jev jaggedness doc also says Jev reads negation literally, which makes negation a known ambiguity zone. — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) (via switch_loop.md)
- ASSUMED **how review labels map to mining.**
  - Missed switch: add the turn to the positive class for that signal.
  - False switch: add it to the negative class, and attribute it to the cue that fired. Demote that cue if its gold precision falls below the threshold.
  - Late switch: take turns between the true cue onset and the actual switch as positives. This is where the earliest cues come from.
- ASSUMED **build time:** 3–4 h (scorer + transliteration cache + negation check + review CSV). **Latency:** unchanged, because the lexicon stays a dict or regex lookup.
- ASSUMED **risks:**
  - The sim seller is **scripted**. Mining on hackathon sim calls learns the cards' phrasing. Mine on ps07 plus live runs, and keep sim cards out of the gold set or out of the training data.
  - IndicXlit errors produce nonsense Devanagari cues. A human approves each cue.
  - Language-switch cues are script- and language-ID features ("English bolo", a Gujarati turn), not n-grams. Use a separate rule.

### Gaps
- No published Hindi/Hinglish-specific accuracy for IndicXlit was retrieved. Only the range across 21 languages was shown, so Hindi roman→native accuracy is unknown.
- No CPU latency for IndicXlit was found.
- No paper was found that uses Fightin' Words specifically for dialogue cue mining in Hinglish.

## Q2. Jev criteria/instruction updates: what helps, what hurts, how to A/B offline

### Takeaway
Treat criteria edits as the **riskiest** update and do them **at most once**, offline. Allowed edits:
- Keep one Noul per signal.
- Keep `instructions` and `criteria` aligned.
- Add short, concrete true/false descriptions written from the reviewer's error clusters, for example "a request to be brief or to call back later counts as rush".
- Remove unrelated state.

Score each candidate wording on the frozen gold set by AUROC and by precision at the current θ_high, per signal and per script. Accept a candidate only if it beats the incumbent by more than the paired-bootstrap noise and no signal regresses. Otherwise keep v0 criteria and let thresholds and lexicon do the learning.

### Cited Findings
- DOCUMENTED: Noul returns "a single number representing the probability that the answer is yes". Criteria should use `true`/`false` with unambiguous language. Threshold advice: start at 0.5; raise it when false positives are costly; use a middle range for review, e.g. `YES = 0.8`, `NO = 0.2`. "If reviewers see too many messages, narrow the gap; if wrong routes slip through, widen it." — [TypeSafe Noul](https://docs.typesafe.ai/primitives/noul.md)
- DOCUMENTED: "Break down complex or ill-defined questions into separate questions that each evaluate one property." "Keep questions short." "One primitive's result does not become hidden context that changes another primitive's result." — [TypeSafe how to build](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- DOCUMENTED (jev-1.13 jaggedness):
  - "Accuracy falls as the state grows with content unrelated to the decision."
  - When `instructions` and `criteria` "ask for different things, jev-1.13 might get confused".
  - It reads negation literally.
  - It has a first-option bias in Choice.
  - Score levels are "weak in numerical calibration".

  — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) (via [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md))
- DOCUMENTED (third party): a tuned prompt policy cut Jev accuracy from 86.20% to 82.53% (−3.67 points) on content safety. The benchmark was English-only. — [Red Hat Developer, 2026-10-02](https://developers.redhat.com/articles/2026/10/02/benchmarking-ai-decision-models-against-traditional-guardrails) (via switch_loop.md)
- DOCUMENTED: shrewd found that prompt-optimisation gains on dev "vanish on test". — [sshah03/shrewd](https://github.com/sshah03/shrewd) (via switch_loop.md)
- PROVEN: 6 questions vs 1 question gives p50 482 vs 491 ms. Adding criteria text costs almost no latency. — [spike log](../../../raw/research/2026-10-07-spike-log.md)

### Inferences
- ASSUMED **helps:**
  - Criteria that name the boundary cases the reviewer saw. Example: "asking the price is interest, not rush".
  - Moving per-turn context into **named state fields**, such as `last_seller_turn` and `prev_agent_turn`.
  - Removing the transcript tail beyond 2–3 turns.
- ASSUMED **hurts:**
  - Long policy text. This is what the Red Hat tuned policy was.
  - Criteria that contradict instructions.
  - Packing several signals into one Choice.
  - Adding the lexicon's verdict into state, which anchors Jev and destroys the independence the cascade needs.
  - Few-shot examples in state, which are untested and a distractor risk.
- ASSUMED **offline A/B protocol:**
  1. Write ≤3 candidate wordings per signal from the reviewer's error clusters. An LLM can draft them; a human picks.
  2. Run each against the gold set: ~300 turns × 5 signals, about $0.02 per pass at ~$0.00004 per call.
  3. Compute AUROC per signal, plus precision and recall at the current band.
  4. Run a paired bootstrap over **calls**, not turns, for 1,000 resamples. Accept a candidate only if the 90% CI of the AUROC delta excludes 0 and no other signal drops more than 1 point.
  5. Freeze the winner as `jev_questions_v1`. Because criteria change Jev's score distribution, **recalibrate θ after any criteria change** (Q3).
- ASSUMED **build:** 2–3 h. **Latency:** about +0 ms.

### Gaps
- No published Jev accuracy on Devanagari or code-mixed text. The "Other languages … not equally well" caveat is the only statement.
- No evidence on how much criteria rewording moves Jev on any non-English task.

## Q3. Per-signal threshold calibration from accumulated labels

### Takeaway
Don't fit isotonic regression. Our n is far below the ~1,000 samples scikit-learn says isotonic needs. Instead, set a **two-sided band per signal and per script** with an **LTT / Clopper-Pearson** rule:
- θ_high is the lowest threshold whose one-sided 95% lower bound on precision is ≥ the target.
- θ_low is set the same way for miss rate.
- The middle band defers to the lexicon or classifier vote.

Platt (sigmoid) scaling is only for the classifier, and only as a nicety. The bound math says a rare signal needs **≥30 confirmed positives above θ** before any precision claim is meaningful.

### Cited Findings
- DOCUMENTED: "'isotonic' will perform as well as or better than 'sigmoid' when there is enough data (greater than ~ 1000 samples)". Sigmoid is "most effective for small sample sizes". For a fitted model, `CalibratedClassifierCV(estimator=FrozenEstimator(...))`; "It is up to the user to make sure that the data used for fitting the classifier is disjoint". — [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html)
- DOCUMENTED: Learn-then-Test (Angelopoulos, Bates, Candès, Jordan, Lei) recasts risk control as multiple testing. It scans thresholds along a monotone path and "stops immediately before the first 'unsafe' threshold where the risk upper confidence bound exceeds the target". It is model-agnostic, needs no refitting, and MAPIE ships it as `BinaryClassificationController`. — [arXiv 2110.01052](https://arxiv.org/pdf/2110.01052); [MAPIE risk control](https://mapie.readthedocs.io/en/latest/theory/risk-control/)
- DOCUMENTED: Conformal Cascade needs roughly n ≥ 200 and exchangeability, and "covariate-shift deployment needs online recalibration". shrewd's bounded routing needs "about a thousand judged documents". Naive thresholds failed in 4–7 of 10 draws. — via [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)
- PROVEN (computed, scipy beta quantiles): one-sided 95% Clopper-Pearson lower bound on precision:

  | Correct / predicted | Lower bound |
  |---|---|
  | 30/30 | 0.905 |
  | 27/30 | 0.761 |
  | 45/50 | 0.801 |
  | 90/100 | 0.836 |
  | 180/200 | 0.858 |

  Zero errors in n gives an upper error bound of 9.5% (n=30), 5.8% (n=50), 3.0% (n=100), 1.0% (n=300).
- PROVEN (aggregate): calls with a cue were frustrated in 1.7%, confused in 4.8% and rushed in 31.6%. — [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)

### Inferences
- ASSUMED **labels needed, per signal and per script:**
  - ≥30 positives to state any bound at all.
  - ~100 positives to separate a 0.90 from a 0.80 precision band.
  - Rush is easy: it is common, so enrich it from ps07.
  - Frustration (1.7% of calls) needs **enriched sampling**, meaning lexicon and Jev high-score candidates sent to human labelling. Expect its bound to stay loose, and say so.
- ASSUMED **procedure per round:**
  1. Pool the gold set with two-key-confirmed review labels (Q5) for calibration only, never the frozen gold test split.
  2. For each signal and script, scan θ ∈ {0.5, 0.55, …, 0.95} from the top down. Stop before the first θ whose CP lower bound on precision < target. A suggested target is 0.85 for frustration, rush and confusion, where a false switch costs a turn, and 0.75 for interest.
  3. Set θ_low from the miss-rate bound the same way.
  4. Apply a Bonferroni split: δ/number of signals.
- ASSUMED **conformal**: with ≥200 calibration turns per script, split conformal on the Jev noul gives the same band with a coverage statement. It adds no build value over LTT at our n. Mention it but don't build it.
- ASSUMED **Platt** applies only to the char-n-gram classifier's scores, so they combine sensibly with the Jev noul. Logistic regression is already roughly calibrated, so this is optional.
- ASSUMED **build:** 1–2 h. **Latency:** 0.
- ASSUMED **risk:** thresholds fitted on romanized replay won't transfer to live Devanagari. Keep **per-script thresholds**, and require ≥30 Devanagari positives before replacing the Devanagari default.

### Gaps
- No published calibration data for Jev noul on any Indic data.
- Actual positive counts per signal in an enriched gold set are unknown until it is built.

## Q4. Small classifier retrained each round

### Takeaway
Build **char_wb 2–5-gram TF-IDF + logistic regression**, one model per signal with `class_weight='balanced'`. It is trained on romanized ps07 turns **plus their IndicXlit Devanagari copies** plus review-confirmed live turns. Training takes under a second and inference ~0.4 ms per turn, so it can sit **next to the lexicon in the instant path**:
- Lexicon hit fires immediately.
- If there is no hit but the classifier probability is ≥ its θ_high, fire.
- Otherwise defer to Jev on the next turn.

Skip fastText unless time remains. It adds a dependency and offers no clear gain over char TF-IDF at our data size. Skip MuRIL/IndicBERT: no GPU, no measured CPU latency, and too little data to fine-tune.

### Cited Findings
- PROVEN (local laptop, 12 logical CPUs, **synthetic** mixed-script strings, no real data): `TfidfVectorizer(analyzer='char_wb', ngram_range=(2,5))` + `LogisticRegression` on 6,000 turns trained in **0.26 s**. Single-turn `predict_proba` averaged **~0.37 ms**. The synthetic vocabulary is small, so real feature counts will be larger, but timings should stay in the ms range (ASSUMED). — local benchmark, 2026-10-08
- DOCUMENTED: shrewd TF-IDF student runs at ~0.35 ms per document, under 10 MB, and trains in seconds. An encoder fine-tune needs "~11 GB RAM" and "~25 min on a GPU". — [sshah03/shrewd](https://github.com/sshah03/shrewd) (via switch_loop.md)
- DOCUMENTED: On SemEval-2020 Task 9 (SentiMix Hinglish), TueMix's logistic regression on TF-IDF n-grams + lexicons + surface features reached weighted F1 0.685. Another system got 0.65. — [TueMix, ACL Anthology 2020.semeval-1.178](https://aclanthology.org/2020.semeval-1.178); [LT3, arXiv 2010.11019](https://arxiv.org/pdf/2010.11019)
- DOCUMENTED: a 2026 domain-adaptive multitask BERT (CDMG-BERT) reached F1 84.8% on a 12K-sample IIT Bombay Hinglish set, beating mBERT and XLM-R. This is GPU-trained heavy machinery. — [ETASR 16589](https://etasr.com/index.php/ETASR/article/view/16589)
- DOCUMENTED: IndicBERT v2 covers Devanagari Hindi only, while HingRoBERTa is pre-trained on romanized code-mixed text. The script choice of the encoder matters. — [search summary, arXiv 2402.03137](https://arxiv.org/pdf/2402.03137)
- DOCUMENTED: Red Hat found small pre-trained classifiers fastest (deberta-v3-base median 54.1 ms on an M1) at near-top accuracy. — via [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)
- DOCUMENTED: No published CPU/ONNX latency for MuRIL or IndicBERT was found in the earlier research. — [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)

### Inferences
- ASSUMED **why char n-grams fit:**
  - They absorb informal spelling ("nahi/nai/nhi") and ASR damage ("जी" for "बिजी").
  - Both scripts can share one model if each training turn appears in both scripts.
  - No tokenizer is needed.
- ASSUMED **cascade slot.** The classifier is a *second instant voter*, not a replacement for Jev. Its output also gives an uncertainty score that drives active learning (Q5). Policy priority stays in code.
- ASSUMED **training data per round:**
  - Gold-free pool: ps07 sample with reviewer or Jev labels.
  - Two-key labels from the latest runs.
  - Weighting: confirmed live Devanagari turns ×3, because they match the live distribution.
  - Never train on the gold test split.
- ASSUMED **expected quality:** SentiMix-level F1 (~0.65–0.7) is for 3-way sentiment on tweets. Our per-signal binary cues (rush, confusion) are more lexical, so they should do better. Implicit frustration and interest will be weak, and Jev stays primary there.
- ASSUMED **fastText:** the original paper reports training on ~1B words in under 10 minutes on CPU. It is fast enough, but its benefit over sklearn char TF-IDF at ~5K examples is unproven, and it adds a build step. Leave it out. — [fastText "Bag of Tricks", arXiv 1607.01759](https://arxiv.org/abs/1607.01759)
- ASSUMED **build:** 3–4 h including the transliteration cache. **Latency:** about +0.4 ms.

### Gaps
- No Hinglish **Devanagari-ASR** classification benchmark was found. Every code-mixed benchmark found is romanized social-media text.
- No CPU latency numbers for MuRIL or IndicBERT inference.
- Daytona sandbox CPU is still unmeasured.

## Q5. Update gating, versioning, rollback, feedback-loop safety, active learning

### Takeaway
1. **Freeze a gold set before the first update:** ~300 hand-labelled seller turns, ≥30 positives per signal where possible, at least 1/3 Devanagari live-like turns, and no sim-card text used in training.
2. **Ship vN+1 only if all of these hold:**
   - Per signal and per script, precision and recall at the operating point don't drop by more than 1 point.
   - Macro-F1 improves.
   - False-switch count on the gold calls doesn't rise.
3. **Admit a label for training only with two keys:** the reviewer and Jev agree, or a human confirms.
4. **Spend human labelling time on the most uncertain turns:** classifier p near 0.5, or reviewer–Jev disagreement.
5. **Version every artifact** in one manifest. Rollback means pointing `current` to the previous manifest.

### Cited Findings
- DOCUMENTED: Cekura says "Gate every deploy on the suite", and validation is against a frozen held-out regression suite. — [cekura.ai](https://www.cekura.ai/); [last30days dump](../../../raw/research/2026-10-08-last30days-voice-agents-learning-from-past-calls.md)
- DOCUMENTED: Confident learning finds label errors by estimating the joint distribution of noisy and true labels from out-of-sample predicted probabilities, then prunes and ranks examples. It is model-agnostic, has been applied to text (Amazon Reviews), and ships as open-source `cleanlab`. — [Northcutt et al., arXiv 1911.00068](https://arxiv.org/pdf/1911.00068)
- DOCUMENTED: The standard uncertainty-sampling strategies are least confidence, margin and entropy (Settles 2009). In a cold start, uncertainty estimates are unreliable, so coverage or diversity sampling is advised. — [Zhang et al. survey, arXiv 2210.10109](https://arxiv.org/pdf/2210.10109); [Schröder & Niekler, arXiv 2008.07267](https://arxiv.org/pdf/2008.07267)
- DOCUMENTED: shrewd found that "Better teacher labels didn't always improve students", that teacher errors propagate, and that uncertainty sampling cut teacher calls 2.0–2.3×. — via [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)
- DOCUMENTED: PoisonedEvolution embedded target behaviour in 91.0% of trials at 10% attacker support in self-evolving skill systems. — [arXiv 2608.05563](https://arxiv.org/pdf/2608.05563) (via switch_loop.md)
- PROVEN (wiki): at ~25–30 positives per signal, only gains of about 20 points or more are distinguishable, and kappa is ±0.26 at n=30. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences
- ASSUMED **two-key rule, in detail:**
  - The reviewer (Sarvam LLM, run blind to Jev scores) and Jev (noul ≥ θ_high or ≤ θ_low) agree: admit the label.
  - They disagree: put the turn in the human queue. If a human labels it, admit it at weight ×2.
  - The reviewer labels `late` or `missed` and the lexicon or classifier never fired: admit it only for lexicon *candidate mining*, which has human approval anyway.

  This blocks the main feedback loop: the switcher's own output becoming its training label. Never use "the switch fired" as a label.
- ASSUMED **cleanlab check:** before each retrain, run `find_label_issues` on cross-validated classifier probabilities. Send the top 20 suspects to human review. This takes 30 minutes to add and is optional.
- ASSUMED **active learning budget:** about 30 human labels per round, chosen in this order:
  1. Reviewer–Jev disagreements.
  2. Classifier |p−0.5| < 0.15.
  3. A random 5 as a sanity check against sampling bias.

  At round 0 (cold start), use stratified random plus lexicon-hit enrichment rather than uncertainty.
- ASSUMED **versioning.** `switcher/vN/` holds:
  - `lexicon.json`, `thresholds.json`, `jev_questions.json`, `clf.joblib`;
  - `manifest.json`, recording the parent version, label-batch ids, gold-set hash, metrics and the gate verdict.

  Each trace line records `switcher_version`. Rollback swaps a symlink or env var with no redeploy. Change **one component per version**, or a paired ablation, so any gain can be attributed.
- ASSUMED **statistics of the gate:** run a paired bootstrap over gold *calls*. With ~300 turns the gate can only catch big regressions, so pair it with a rule that **no gold turn that was correct in vN becomes a false switch in vN+1** without a human sign-off. This is a "flip list" review.
- ASSUMED **leakage:** the gold set must contain no turns from cards or sellers used to mine cues. Otherwise v1>v0 is memorisation.

### Gaps
- No published two-key or teacher-agreement filtering result for this exact setting. Reviewer (Sarvam) accuracy on Devanagari seller turns is unmeasured.
- The gold set does not exist yet, so the statistical power numbers are projections.

## Q6. Timing: the "late switch" metric and how updates reduce it

### Takeaway
Define **switch delay** per gold signal episode as `d = turn_index(switch) − turn_index(first true cue)`, counted in seller turns.
- d = 0: on-time (lexicon or classifier caught it on the same turn).
- d = 1: Jev-next-turn.
- d ≥ 2: late.
- No switch before the call ends: missed (d = ∞).

Report the share at d = 0, d ≤ 1 and missed, per signal. Lexicon and classifier updates move mass from d = 1/∞ to d = 0. Threshold updates move it from ∞ to 1. Criteria updates affect only d = 1.

### Cited Findings
- PROVEN (aggregate): after the first rushed cue a median of 2 seller turns remain, and 17.2% of first rushed cues fall on the last seller turn. A d = 1 switch is worthless on those calls. — [switch_loop.md](../Self%20improving%20persona%20and%20switch%20loops/switch_loop.md)
- PROVEN: Sarvam reply latency is ~2.1 s median. Jev p95 is ~1.4 s under load. Jev can only correct turn k+1. — [spike log](../../../raw/research/2026-10-07-spike-log.md)
- DOCUMENTED (wiki design): the planned proof is per-signal precision, recall and timing ("turns from cue to switch"), v0 vs v1 on held-out turns. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences
- ASSUMED **metric details:**
  - "First true cue" comes from the reviewer label, confirmed by two keys. Only seller turns count.
  - Hysteresis is part of the system, so a policy that needs 2 cues has d ≥ 1 by design. Report d both before and after the policy, to separate detector lateness from policy lateness.
  - Also report **time-weighted lateness**: the share of the call's remaining seller turns spent in the wrong mode.
- ASSUMED **which update reduces which part of d:**
  - Cues mined from `late` labels (the turn before the switch carried the cue) shift d=1→0. This is the **highest-value update for rush**, because a d=1 rush switch often lands after the seller has left.
  - Classifier recall on Devanagari shifts ∞→0.
  - Lowering θ_high for Jev, within the precision bound, shifts ∞→1.
  - Policy hysteresis changes are code, not learning. Keep them frozen during the event, or the learning attribution gets confounded.
- ASSUMED **headline:** "On-time (d=0) rate for rush on Devanagari gold turns: v0 X% → v1 Y%, false switches unchanged", with paired bootstrap CIs.

### Gaps
- No external standard metric for switch timing in voice agents was found. This definition is ours.

## Q7. Devil's advocate: overkill, biggest gain, scope

### Takeaway
For two days, **lexicon mining + IndicXlit variants + per-script thresholds, gated on a frozen gold set**, is the whole worthwhile loop. It gives the biggest measurable gain: on-time detection on Devanagari, where v0 is weakest because it was built from romanized data.
- The char-n-gram classifier is a reasonable add-on, worth it only if the gold set shows recall gaps that the lexicon can't close.
- Criteria A/B, conformal, isotonic, cleanlab, fastText, MuRIL and IndicBERT are overkill.
- Active learning beyond "label the disagreements" is overkill too.

### Cited Findings
- PROVEN: past turns are 99.4% Latin script and live ASR is Devanagari. The Jev agreement figure (49/51) is romanized-only. — [spike log](../../../raw/research/2026-10-07-spike-log.md); [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)
- PROVEN (wiki): loop work is capped at ~6 h, and core deliverables are ≈20–30 dev-hours against ~18–24 usable hours. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md)
- DOCUMENTED: a tuned Jev policy regressed 3.67 points (Red Hat). Isotonic needs >~1,000 samples (scikit-learn). Bounded routing needs ~1,000 judged documents (shrewd). — sources above
- DOCUMENTED (anecdote, low weight): "self improving agents improve every loop right up until the live demo, then regress to the mean". — [last30days dump](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md)

### Inferences
- ASSUMED **overkill for the hackathon:**
  - Conformal prediction: LTT with Clopper-Pearson is the same idea in 30 lines.
  - Isotonic calibration: n is too small.
  - Repeated criteria optimisation or GEPA: the regression risk is documented.
  - fastText, MuRIL or IndicBERT: no GPU, no latency data, no data volume.
  - cleanlab: nice to have.
  - Full active-learning strategies.
  - Separate per-signal models for interest. Interest is mostly a persona and opening matter, not a live switch.
- ASSUMED **biggest single measurable gain:** **Devanagari-aware lexicon v1**, mined from ps07 with Fightin' Words, transliterated with IndicXlit, NFD-canonicalised, with per-cue negation. Measure it as the d=0 rate and recall on Devanagari gold turns at equal false switches. Reasons:
  - It attacks the known script gap directly.
  - It moves the timing metric, since only the instant path can act on the current turn.
  - It is explainable to judges as a diff ("these 14 cues were added because the reviewer flagged these misses").
- ASSUMED **honesty points for Q&A:**
  - With ~25–30 positives per signal, only gains of about 20 points or more are statistically visible.
  - Most learning comes from replaying ps07, not from demo calls.
  - Sim cards are scripted, so gains on them can be memorisation. Report gold-set numbers, not demo-call numbers.
- ASSUMED **outside PS04 scope, or risky:**
  - Post-call *quality scoring* of the agent's replies drifts toward the Quality Audit problem. Keep the reviewer's output limited to signal and switch labels.
  - Fine-tuning any model.
  - A generic self-improving platform.
  - An LLM deciding switches live (excluded by the team decision).
  - Sending real seller text to non-Sarvam reviewers without an organiser ruling.
  - Any outside vendor (Cekura or Coval as products are out; only their *pattern* is used).
  - Language-switch detection on Devanagari vs Gujarati script is cheap and in scope. Building multilingual cue lexicons for many languages is not: start with Hindi/Hinglish only.

### Gaps
- Judges' weighting of "learning" inside the 25% switch criterion is unknown. The rubric names correctness and timing.
- Until the gold set is built, the size of the Devanagari recall gap in v0 is unknown, and with it the ceiling on the headline gain.
