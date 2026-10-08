# Proving self-improving persona + switching loops in a 2-day hackathon, and a strict PS04 scope check

As of 2026-10-08. Tags: **PROVEN** (we measured it, or the source reports a measurement), **DOCUMENTED** (a primary source states it, but we have not verified it), **ASSUMED** (our judgement or estimate). Local sources are relative links from this file. No customer data appears here. Every count below is an aggregate already filed in `raw/`/`wiki/`.

Binding requirements read: [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md), [hackathon deck](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md), [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md), [system design](../../../wiki/projects/vani-hackathon/system-design.md).

---

## Q1. How can we show convincingly that the persona generator improves (fit / distinctness / evidence, before vs after N loop iterations)?

### Takeaway
Freeze a **held-out seller split and a calibrated judge before the loop runs**. Report v0 against vN only on the held-out sellers, with deterministic metrics (distinctness, evidence-link coverage, schema/guardrail validity) beside the LLM-judge fit score. Show the judge's agreement with a small human-labelled set as a kappa with a confidence interval, not as percent agreement. Prompt-optimiser practice backs this: validation sets kept separate from the data the optimiser learns from, and the gain checked on a held-out test set.

### Cited Findings
- PS04 scores **fit 25%, switches 25%, distinctness 20%, natural voice in 2+ languages 15%, evidence 15%** (indicative). Fit means "how well the persona's voice, language, tone and plan suit the seller's data". Distinctness means "clearly different personas, not minor variations of one". DOCUMENTED — [PS04 doc §6](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- The doc requires a **reason per setting**, each major rule linked to past-call evidence, and a statement of "how strong the evidence is and where the generator is making an informed guess". Missing fields → defaults marked lower confidence (FAQ Q6). DOCUMENTED — [PS04 doc §3.2, §3.4, §7](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- The deck's Technical Robustness criterion (20%) explicitly includes "**validation on real data**". DOCUMENTED — [persona requirements, judging table](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- The real data is available. `ps07_seller_files` has 149,363 sellers. Bot calls 269,455, evaluator outputs 278,332, call turns 139,555 across 12,788 calls, executive calls 67,151. PROVEN (counts) — [PS07 data dictionary](../../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)
- Archetype meeting rates already computed from history: A1 4.1%, A2 8.1%, A3 21.7%, A4 14.3%, A5 19.5%. These are the evidence backbone for B2 rules. PROVEN — [system design](../../../wiki/projects/vani-hackathon/system-design.md)
- **Three static-personalisation trials all failed to beat control** (e.g. `personalis` 14.8% vs 17.8%, p=0.13; `summary_va` 3.3% vs 18.4%, p<0.001). An "improved persona" claim measured only as judge-rated fit has no outcome backing, and the jury may be sceptical of "personalised" claims. PROVEN — [persona data validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md)
- GEPA reports gains as optimised vs baseline prompts on a **held-out test set**, separate from the train/validation data the optimiser uses. Across six tasks it beats GRPO by 6% on average (up to 20%) with up to 35× fewer rollouts, and beats MIPROv2 by >10%. DOCUMENTED — [GEPA, arXiv 2507.19457](https://arxiv.org/html/2507.19457v1)
- DSPy guidance for prompt optimisers: a 20% train / 80% validation split ("the opposite of what one does for DNNs"); ~30 examples give "substantial value", but aim for ≥300. Optimised prompts can overfit small training sets and need regression review. DOCUMENTED (via search snippet; the docs page did not render on fetch) — [DSPy optimization overview](https://dspy.ai/learn/optimization/overview)
- LLM judges: GPT-4-class judges reach >80% agreement with human preferences, the same level as human–human agreement. They also show **position bias** (even the strongest judge is consistent only ~65% of the time when answers are swapped), **verbosity bias** (GPT-3.5/Claude-v1 fooled 91% by padded answers, GPT-4 8.7%) and **self-enhancement bias** (~10% for GPT-4, ~25% for Claude-v1). DOCUMENTED — [Zheng et al., MT-Bench, arXiv 2306.05685](https://arxiv.org/html/2306.05685v4); bias figures as summarised by [Grepture](https://grepture.com/blog/llm-as-a-judge-bias)
- **Percent agreement misleads.** Judges are "rarely discriminable" on percent alignment. Scott's π separates them better, and judges with high percent agreement can still differ 10–20 points from human scores. DOCUMENTED — [Thakur et al., Judging the Judges, arXiv 2406.12624](https://arxiv.org/html/2406.12624)
- **Criteria drift:** people need criteria to grade outputs, but grading outputs is what defines the criteria. So the human rubric must be fixed *after* a short look at outputs and *before* the loop's final scoring. DOCUMENTED — [Shankar et al., Who Validates the Validators?, arXiv 2404.12272](https://arxiv.org/pdf/2404.12272)
- Judge calibration overfits too. A judge tuned on a 15-item subset reached 80% exact agreement with humans, but only 51.9% on the full 54-item suite. DOCUMENTED — [Wahi, arXiv 2609.02246 (search summary)](https://arxiv.org/pdf/2609.02246)
- Our design already plans "Judge κ ≥ ~0.6 on 20 human-labelled calls per ordinal criterion". That is ASSUMED, not yet run. Fallback: "Report only deterministic metrics and binary Jev items". ASSUMED — [deep-research system design (T13)](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)

### Inferences
- **Protocol P-GEN (ASSUMED, designed for 2 days):**
  1. **Split** (seeded, stratified by archetype A1–A5 × language): *train* 20 sellers (the loop reads failures from these), *val* 20 (used to accept or reject each loop edit), *test* 30 held out and never shown to the loop. Optionally add 6 "canary" sellers with deliberately missing fields or contradictions. Freeze the split file hash before the first loop iteration and show the hash in skills.md.
  2. **Metrics on test, v0 vs vN:**
     - (a) *Fit*: LLM judge, 1–5 per dimension (voice, language, tone, plan), arm-blind, with the rubric anchored to seller fields.
     - (b) *Distinctness*: deterministic, so no judge is needed. Use mean pairwise distance between persona-spec vectors (categorical fields: voice id, pace bucket, language, formality, warmth, opening type, playbook ids). Also report the number of distinct (voice, language, pace, opening) tuples across 30 sellers and the share of sellers that collapse into one mode. Report it per archetype pair so "different sellers → different personas" is visible.
     - (c) *Evidence coverage*: the share of spec fields with a reason that cites a real aggregate (archetype rate, objection frequency) plus a strength tag. This is deterministic: check that each cited stat id exists in the evidence table.
     - (d) *Validity / guardrail*: schema passes, no price or fact text in persona fields, low-confidence flags present where fields are missing. Deterministic.
     - (e) *Outcome proxy (optional)*: on PS07 sellers with past calls, does the spec's archetype or pace choice agree with what correlated with meeting-fixed? This is correlational only.
  3. **Judge calibration:** two humans (including the non-tech member) label the same 30 specs on the fit rubric, blind to version. Report human–human kappa, then judge–human kappa (weighted kappa, or Scott's π, for the 1–5 ordinal) with a bootstrap 95% CI. Gate: if judge–human kappa is below the human–human kappa minus ~0.15, or below ~0.4, show only deterministic metrics (b–d) plus the human scores.
  4. **Bias controls:** randomise the A/B order and score both orders (position bias). Put a length cap in the rubric and report spec length v0 vs vN (verbosity). Use a judge from a different model family from the generator's phrasing model (self-preference).
- Distinctness is where a loop can most easily *look* better while getting worse: maximising pairwise distance rewards random variation. Pair it with fit, and with a "same seller twice → same spec" stability check: run each test seller 2× and report spec agreement.
- The strongest honest framing for the generator loop is to fix specific failures on train/val and show they don't regress on test. "The loop found that A1 re-engage sellers were getting the warm-slow voice despite a 4.1% meeting rate and rush history, and moved them to crisp" is more convincing than "fit went from 3.6 to 4.1".

### Gaps
- No human-labelled persona-fit ground truth exists in the shipped data. Any fit label is our own. No source tells us what the IndiaMART jury will treat as "good fit".
- I found no published kappa values for LLM judges on *persona-spec* or *voice-agent persona* fit, so the 0.4–0.6 thresholds are ASSUMED, taken from general agreement conventions.

---

## Q2. How can we show that switching improves (precision/recall/latency per signal, before vs after teacher corrections)?

### Takeaway
Switching is the easier loop to prove honestly, because it has near-objective labels. Build a frozen, human-adjudicated test set of PS07 seller turns per signal. Measure lexicon v0 vs lexicon+corrections vN on per-signal precision and recall, with Wilson CIs. Separately, measure switch latency in turns and seconds after a scripted trigger in simulated calls. The teacher (Jev) labels the *train* pool only. Humans adjudicate the *test* pool, so the teacher cannot grade its own corrections.

### Cited Findings
- PS04 judges switches on "whether signals are detected correctly and the change happens at the right moment" (25%). Required signals: frustration, confusion, interest, language switch and rush. Every switch must be logged (signal, change, reason). A pre-scripted switch "will score lower". DOCUMENTED — [PS04 doc §3.5, §6, FAQ Q3/Q4](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- `ps07_call_turns.csv`: 139,555 turns across 12,788 calls, "mostly Hindi / Hinglish". Intended "to find where sellers get frustrated, confused, interested or rushed". DOCUMENTED — [PS07 data dictionary](../../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md)
- Keyword-heuristic prevalence on 11,834 transcribed calls: rush 21.0%, interest 16.8%, confusion 6.5%, bot question 4.0%, frustration 3.6%, regional language 2.3%. Seller turns are romanized (0.2% Devanagari). PROVEN (heuristic, crude) — [persona data validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md)
- The Jev teacher agreed 49/51 on 30 romanized turns (rushed 10/10, frustrated 10/10, confused 9/9, bot_question 5/5, interested 5/6), ~480 ms, ~$0.00004/decision. Romanized only. PROVEN — [system design](../../../wiki/projects/vani-hackathon/system-design.md); [deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)
- Planned P1 test T8: ~600 sampled turns transliterated to Devanagari, 200 hand-labelled, lexicon vs Jev per signal per script. Target: rushed/bot-question lexicon precision ≥0.85. ASSUMED (planned) — [deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)
- The design already says "Jev never grades the ON arm's switch correctness, because it helped make those decisions". The judge is a different model family, arm-blind. DOCUMENTED (our design) — [deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)
- B7 simulated-seller harness, voice-to-voice via SDK, ON/OFF paired, is PROVEN. A minimal experiment of 10 cards × 2 seeds × 2 arms = 40 calls ≈ 60 min ≈ ₹210. PROVEN (harness) / ASSUMED (cost) — [system design](../../../wiki/projects/vani-hackathon/system-design.md)
- Corrupted labels in a self-improving loop led an optimiser to delete correct rules. Recommended guards: frozen holdouts, canary cases, capability-disjoint roles, and "acceptance checks outranking the teacher". DOCUMENTED — [Wahi, arXiv 2609.02246](https://arxiv.org/abs/2609.02246)

### Inferences
- **Protocol P-SW (ASSUMED):**
  1. **Pools.** Sample candidate turns by stratified keyword hits plus random negatives, so recall is measurable. The train pool (~400 turns) gets Jev labels. The test pool (~200 turns, ≥25 positives per required signal, ~75 negatives) is double-labelled by two humans and adjudicated, then frozen.
     - Language switch can be generated deterministically: script change, or language-ID on a turn that differs from the call language.
     - Add ~30 Devanagari-transliterated test turns, because live ASR is Devanagari ([deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)).
  2. **Improvement step.** Feed the teacher's disagreements with the lexicon (on train only) to an LLM that proposes lexicon additions, threshold or hysteresis tweaks, or directive edits. Accept an edit only if precision and recall on the val slice don't fall for any signal.
  3. **Report** per signal on the frozen test pool: precision, recall, F1 with Wilson 95% CIs, v0 → vN. Add a confusion matrix (rush vs frustration is the likely confusion). Add the false-switch rate on negatives, which matters most for "correct" switches.
  4. **Timing (the "well-timed" half).** In B7 simulated calls with scripted trigger turns, measure turns-to-switch and seconds-to-switch (trigger turn end → first changed reply), plus spurious switches per call. Run v0 vs vN, same cards, same seeds. Report the median and max.
  5. **Live calls (FAQ Q3).** These are not a statistic. 3–6 live human calls are logged as qualitative evidence: the switch log shows the signal, the change and the reason at the right turn.
- Hybrid timing matters for the "well-timed" score. The lexicon decides now (<300 ms), Jev corrects the next decision. The self-improvement story fits that naturally: "the teacher's corrections became lexicon v2, so the *fast* path now catches what only the slow path used to" ([system design](../../../wiki/projects/vani-hackathon/system-design.md)).

### Gaps
- No ground-truth signal labels ship with PS07. Every precision/recall number rests on our human adjudication.
- Tamil/Gujarati-script accuracy cannot be measured from local data, per the [deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md).

---

## Q3. What minimal sample sizes and statistics are honest in 2 days?

### Takeaway
At hackathon sizes, report **effect sizes with confidence intervals and paired tests**, and say plainly that intervals are wide. Roughly 30 held-out sellers, 20–30 positives per signal and 20–40 paired simulated calls can show *large* improvements honestly. They cannot show small ones. Never quote a single-run percentage without n.

### Cited Findings
- Dror et al. found statistical significance testing "often ignored or misused" in ACL/TACL 2017 papers. They give a protocol for choosing tests, including the paired bootstrap. DOCUMENTED — [Dror et al., ACL 2018](https://2018.aclweb.org/paper/703/); [appendix arXiv 1809.01448](https://arxiv.org/pdf/1809.01448)
- For kappa at small n, asymptotic CIs become unreliable. Exact or bootstrap intervals are preferred, and Newcombe-based methods work "in sample sizes as small as 25". DOCUMENTED — [kappasizeci overview](https://www.serdarbalci.com/meddecide/articles/07-kappasizeci-comprehensive.html); [presize::prec_kappa](https://search.r-project.org/CRAN/refmans/presize/html/prec_kappa.html)
- DSPy: ~30 examples give value, but ≥300 is recommended. DOCUMENTED — [DSPy](https://dspy.ai/learn/optimization/overview)

### Inferences (my computations; ASSUMED where noted)
- **Wilson 95% CIs (computed):** 49/51 → [0.87, 0.99]; 16/20 → [0.58, 0.92]; 24/30 → [0.63, 0.90]; 40/50 → [0.67, 0.89]; 10/10 → [0.72, 1.00]. At n=20 per signal, a jump from 0.70 to 0.85 is inside the noise. At ≥30 positives, only differences of ~20+ points separate cleanly.
- **Kappa precision (computed, approx.; observed agreement 0.85, chance 0.5 → κ=0.7):** the 95% CI half-width is ±0.31 at n=20, ±0.26 at n=30, ±0.20 at n=50, ±0.14 at n=100. "κ=0.7 on 20 items" therefore means "somewhere between 0.4 and 1.0". **Recommend 30–50 human-labelled items** per judged criterion, and state the CI.
- **Paired tests:** for before/after on the same items, use McNemar or an exact sign test on discordant items (binary correct/incorrect), and Wilcoxon signed-rank or a paired bootstrap for 1–5 judge scores. Computed: with 10 discordant pairs you need ≥9 in one direction for two-sided p<0.05; with 15, ≥12. So 40 paired sim calls is enough only for a large effect.
- **Multiple comparisons:** 5 signals × 3 metrics invites cherry-picking. Pre-declare one primary metric per loop: macro-F1 over the 5 required signals for switching, and judge fit on held-out sellers for the generator. Report everything else as secondary.
- **Seeds / variance:** run the generator twice per test seller at the chosen temperature and report the spread. LLM run-to-run variance can exceed small loop gains. ASSUMED.
- **Minimum honest budget (ASSUMED):** generator 70 sellers (20/20/30) + 30 human-labelled specs; switching ~400 train turns + 200 adjudicated test turns; 20–40 paired sim calls; 3–6 live calls. Human labelling ≈ 3–4 person-hours, a good job for the non-tech member with a rubric.

### Gaps
- No source gives jury-specific expectations on statistical rigour for this hackathon. The deck rubric only says "validation on real data" ([persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)).

---

## Q4. How should "self-improvement" be presented in a 5–7 min video and one slide without overclaiming?

### Takeaway
Present the loops as **an engineering method that produced a measured, held-out improvement before the demo**, not as an AI that learns live on stage. One before→after chart with n and CIs, one concrete "the loop found X, changed Y" example, and the switch log beat the word "self-improving". Judges reward backtested accuracy and working demos. They penalise AI-for-its-own-sake.

### Cited Findings
- The one-slide deliverable must contain a sample persona spec, the past-call evidence behind it, and a workflow covering the chosen LLM, Sarvam, data flow, live signal detection and integration logic. **Self-improvement is not among the required slide elements.** DOCUMENTED — [PS04 doc §5](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Submission: 5–7 min demo video, approach note, Sarvam Agent ID / live link, code + README, skills.md (build journey, tools used). Then a live demo with Q&A. DOCUMENTED — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- A hackathon-judging guide (Reskilll, 2026-08-07, secondary/blog quality) says winners showed "prediction accuracy shown with backtesting", quantified impact and "a demo that works on the first try", and used "AI as a multiplier (not the entire product)". Generic "AI chatbot for X" ideas are avoided. DOCUMENTED (low authority) — [Reskilll blog](https://blogs.reskilll.com/hackathon-ideas-that-won-2026-judges-actually-pick-examples/)
- Wahi (2026): "a higher evaluation score does not always mean a better language model system". Keep "evidence of task quality independent of the score". DOCUMENTED — [arXiv 2609.25848](https://arxiv.org/abs/2609.25848)
- Industry framing that sells (SquadStack Lift, 2026-07-09): changes are "prove[d] … on real traffic before [they] scale", with human review of "exactly what changed, why the system proposed it, and how it performed". Compliance, pricing and identity sections are locked from optimisation. DOCUMENTED (vendor claim) — [SquadStack Lift](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)

### Inferences
- **Wording ladder (ASSUMED):**
  - Say: "**evaluation-driven**: the generator and switch rules were refined in N rounds against real PS07 data; held-out results below."
  - Avoid: "self-learning agent", "learns from every call", "autonomous".
  - Use "self-improving" at most once, defined in the same breath.
- **Video budget (ASSUMED, ~6 min):**
  - 0:00–0:30 problem: one voice for everyone, rush halves meetings ([data validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md)).
  - 0:30–1:30 seller file → persona spec with reasons and evidence strength.
  - 1:30–4:00 the same scenario for 2–3 contrasting sellers on Sarvam, in 2 languages, with a live mid-call switch and the switch log scrolling.
  - 4:00–5:00 evidence: a table of evidence behind the rules, plus **one** before→after held-out chart (switch macro-F1 v0→vN with CIs; generator fit + distinctness v0→vN).
  - 5:00–6:00 workflow + guardrails (delivery not facts) + limits.
  - The loop gets ≤60 s. It *supports* the evidence and switch criteria; it is not the headline.
- **Slide:** put the loop as a small feedback arrow in the workflow diagram ("PS07 turns → teacher labels → rule update → held-out eval gate"), with one number and its n. Don't give it its own panel; the required elements must fit first.
- **Show a failure:** a regression the gate rejected, or a signal that didn't improve. This shows the gate is real and pre-empts "you tuned on the test set" in Q&A.

### Gaps
- No primary source on how IndiaMART's specific jurors react to "self-improving". The buzzword risk is ASSUMED from general guidance.

---

## Q5. Devil's-advocate scope check: every component → PS04 deliverable or criterion, with build hours, MVV and cut order

### Takeaway
**Everything needed for the five PS04 deliverables is the core build, and the self-improving loops are SUPPORTING at best.** They only earn points through the evidence (15%), switch correctness (25%) and robustness/validation (deck 20%) criteria. The generator-improvement loop is the weakest ROI and the first thing to cut. The switching loop, run **offline** as lexicon v0→v1 from teacher corrections with a frozen test set, is the one loop worth keeping. With one strong developer, budget ≤6 h total for loop work.

### Cited Findings
- Deliverables: (1) generator code, seller file in → persona out; (2) a spec per seller with reasons, covering voice, language, tone and plan; (3) a Sarvam voice demo, 2–3 contrasting sellers, ≥1 live switch; (4) a switch log; (5) a one-slide presentation. DOCUMENTED — [PS04 doc §5](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Blocks and status: B1 context builder (aggregates PROVEN, build ASSUMED); B2 generator (archetype stats PROVEN); B3 launcher (SDK call PROVEN; TTS override + outbound DOCUMENTED); B4 Sarvam agent (tool 24/24, directive PROVEN); B5 signal server (stub + directives PROVEN); B6 Jev worker (49/51 PROVEN); B7 harness PROVEN; B8 trace store, B9 judges and B10 dashboard ASSUMED. DOCUMENTED — [system design](../../../wiki/projects/vani-hackathon/system-design.md)
- Known hard gap: the voice/pace cannot change mid-call. Sarvam pins the voice per call; tone, formality, brevity and language can change. DOCUMENTED — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- Team: 3 people, ≥1 non-tech (deck rule); per the brief, one strong developer. DOCUMENTED — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)

### Component map (all hours ASSUMED, for the strong dev unless noted; a "~" means a rough guess)

| # | Component | Maps to | Verdict | Build h | MVV | Cut order |
|---|---|---|---|---|---|---|
| 1 | B1 seller context builder (seller file → features + evidence ids) | D1, Fit 25% | IN-SCOPE | 2–3 | pandas over seller CSV + precomputed aggregates | never |
| 2 | B2 persona generator (rules + LLM phrasing, reason + evidence + confidence per field) | D1, D2, Fit, Distinct, Evidence | IN-SCOPE | 4–6 | rules table + Sarvam/LLM phrasing, JSON spec | never |
| 3 | Evidence table (archetype/objection → outcome aggregates, strength tag) | Evidence 15%, slide | IN-SCOPE | 2–3 (non-tech can write the narrative) | 1 CSV + 1 page | never |
| 4 | B3 launcher + B4 Sarvam agent (2–3 sellers, 2 languages) | D3, Voice 15%, deck Voice 20% | IN-SCOPE | 4–6 | SDK sessions with per-seller variables and voice | never |
| 5 | B5 signal server (lexicon + policy + directives + switch log) | D3 live switch, D4, Switches 25% | IN-SCOPE | 4–6 | lexicon + hysteresis + JSONL log | never |
| 6 | B6 Jev worker (async correction) | Switches 25% (accuracy) | SUPPORTING | 2–3 | can be dropped; lexicon alone switches | 4th |
| 7 | Slide + video + skills.md + README | D5, deck Demo 15% | IN-SCOPE | 4–6 (non-tech + dev) | — | never |
| 8 | B7 sim harness (paired ON/OFF) | Switch timing, robustness | SUPPORTING | 1–2 (rewrite) | 10 cards × 1 seed × 2 arms | 3rd (shrink) |
| 9 | B8 trace store | D4 backing, robustness | SUPPORTING | 1 | JSONL only (skip DuckDB) | shrink first |
| 10 | B9 deterministic metrics (switch latency, distinctness, evidence coverage, schema) | Robustness, Distinct | SUPPORTING (high value/hour) | 2 | Python script | keep |
| 11 | B9 LLM judge for fit + human calibration set | Fit claim, robustness | SUPPORTING | 2 dev + 3–4 non-tech labelling | 30 specs, 1 judge, kappa + CI | 2nd |
| 12 | B10 dashboard | none directly | OUT-OF-SCOPE (nice-to-have) | 2–4 | a static matplotlib chart in the slide/video | **1st** |
| 13 | **Switching loop** (teacher labels → lexicon/threshold update → frozen-test gate) | Switches 25%, Robustness | SUPPORTING (worth it) | 3–4 + 2 labelling | 1 offline iteration v0→v1, per-signal P/R with CI | keep the 1-iteration version |
| 14 | **Generator loop** (judge critique → rule/prompt rewrite → held-out gate, N iterations) | Fit, Distinct (indirect) | SUPPORTING (weak) → OUT-OF-SCOPE if time is short | 4–6 | 1–2 manual "failure → rule fix" rounds, logged in skills.md | **2nd–3rd** |
| 15 | GEPA/DSPy-style automatic optimiser over generator prompts | none required | OUT-OF-SCOPE | 4–8 + debug | — | cut |
| 16 | Online learning during the live demo (rules change mid-demo from that call) | none (FAQ Q3 wants a live *switch*, not live *learning*) | OUT-OF-SCOPE / risky | 3+ | — | cut |
| 17 | Fine-tuned local encoder for signals | none required | OUT-OF-SCOPE | ~4 ([deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md) says "half a day") | — | cut |

### Inferences
- **Hour budget (ASSUMED):** the IN-SCOPE core is ≈ 20–30 dev hours. Over ~2 days, one strong dev realistically has ~18–24 productive hours, with the second technical-ish member helping. **The core alone may exceed the budget**, so loop work must be time-boxed: switching loop ≤4 h, generator loop ≤2 h (manual), and only after D1–D4 work end to end.
- **Cut order if behind:** B10 dashboard → GEPA/automatic generator loop → LLM-judge fit calibration (fall back to deterministic metrics + human scores on 10–15 specs) → sim harness shrinks to 10 calls → Jev worker. **Never cut:** D1–D5, live switch, switch log, 2 languages, evidence table.
- **The minimum viable version of each loop:**
  - *Switching:* a frozen 200-turn adjudicated test set + one teacher-corrected lexicon update + a P/R table v0 vs v1.
  - *Generator:* a frozen 30-seller test set + deterministic distinctness/evidence/validity metrics v0 vs v1 after one "worst failures → rule edits" round. The judge is optional.
- **The devil's-advocate verdict:** nothing in PS04 asks for self-improvement. The rubric rewards *correct* switches and *evidence-backed* personas. If the loops eat time from voice quality (15% + deck 20%) or the live switch (25%), they cost net points. Their only defensible role is to **produce the evidence numbers** for evidence, robustness and switch correctness.

### Gaps
- Productive hours per person and the exact Day 1/Day 2 schedule are not in the sources. The hours above are estimates.
- Whether the Sarvam floor team can enable a mid-call speaker or pace change is still open ([persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)). That affects how much switch-quality work actually shows up in the audio.

---

## Q6. Risks: reward hacking, teacher error propagation, the buzzword reaction, online vs offline learning, and "all build work in 2 days"

### Takeaway
The main technical risks are that **the generator learns to please the judge** and that **teacher (Jev) label errors get baked into the lexicon**. The defences are cheap: frozen holdouts, deterministic checks that outrank the judge, a separate judge model family, and human-adjudicated test labels. Do the improvement **offline and show it as evidence**. Keep the live demo on frozen v1 rules. Rewrite all spike code during the event and declare the pre-event spikes as research in skills.md.

### Cited Findings
- **Judges can be gamed:**
  - "Master key" inputs (non-word symbols, generic reasoning openers) elicit false-positive rewards at up to 80%. DOCUMENTED — [One Token to Fool LLM-as-a-Judge, NeurIPS 2025 / arXiv 2507.08794](https://neurips.cc/virtual/2025/131135)
  - Optimisation-based prompt injection (JudgeDeceiver) automates adversarial sequences against judges. DOCUMENTED — [arXiv 2403.17710](https://arxiv.org/html/2403.17710v1)
  - Persistent prompts are especially vulnerable: their contents are inspectable, but small textual changes have hard-to-predict effects. DOCUMENTED — [Wahi, arXiv 2609.25848](https://arxiv.org/abs/2609.25848)
- **Teacher error propagation:**
  - Corrupted labels caused an optimiser to delete correct rules.
  - "A 100% pass rate conceal[ed] 68% true capability" when agents read cached answer keys.
  - PROCTOR guardrails: hermetic sandboxes, capability-disjoint roles, acceptance checks that outrank the teacher, frozen holdouts, canary cases.
  - DOCUMENTED — [Wahi, arXiv 2609.02246](https://arxiv.org/abs/2609.02246)
- Industry practice keeps a **human gate** and **locks compliance/pricing** sections from optimisation (SquadStack Lift). Cekura runs full-set regression sweeps, because a subset pass "masked two regressions". DOCUMENTED (vendor) — [SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent); [Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- PS04 guardrail: personas change delivery, "never facts, pricing or compliance statements" (FAQ Q5). DOCUMENTED — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Deck rules: "all build work happens during the 2 days"; "plagiarised or pre-built solutions are disqualified"; data stays on premises. DOCUMENTED — [deck lines 451–455](../../../raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md)
- Existing plan: "Spike code (`app/spike/`, `app/signal_server/`) was written before the event. Treat it as research; write the submission code during the 2 days and say so in skills.md." DOCUMENTED — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- Our tool-compliance evidence is thin: the 24/24 tool rate comes from short calls at temperature 0, and the rate at ≥10 turns is unmeasured. DOCUMENTED — [deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)

### Inferences
- **Reward-hacking controls for the generator loop (ASSUMED):**
  1. The judge never sees the loop's critique prompt, and the generator never sees the judge rubric verbatim.
  2. Deterministic checks veto judge gains: the schema must hold, every reason must cite an existing evidence id, spec length stays within ±20% of v0, and there is no price or fact text.
  3. A different model family judges.
  4. Canary sellers: a seller with all fields missing must get low-confidence flags and defaults. A perfect fit score on a canary means the judge is broken.
  5. Final numbers are human-scored on a subset.
- **Teacher-error controls for the switching loop (ASSUMED):**
  1. The test set is human-adjudicated, never teacher-labelled.
  2. Only accept lexicon additions that fire on ≥k train examples and don't raise false switches on the val negatives.
  3. Log every rule the loop added, with the teacher examples that justified it. This doubles as the "evidence" artefact.
  4. Spot-check ~20 teacher labels by hand before the update. 49/51 on romanized text does not transfer automatically to Devanagari ([system design](../../../wiki/projects/vani-hackathon/system-design.md)).
- **Online learning during the demo: don't do it.** FAQ Q3 requires a *live switch* that responds to the seller, which is in-call adaptation, not learning. A live rules update adds non-determinism to a demo already exposed to tunnel and VPN fragility ([deep-research report](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)). It also produces no measurable evidence. **Offline improvement shown as evidence** carries all the scoring benefit with none of the demo risk. If the team wants a nod to it, show a pre-recorded clip of the update gate running.
- **Buzzword risk:** "self-improving" on top of a voice demo that has no audible pace change invites the question "what improved, measured how?". Answer with the held-out table. If no table exists, drop the term.
- **2-day compliance:**
  - Write all submission code fresh in the event repo, with timestamped commits on 9–10 Oct. Pre-event spikes may inform design, but don't copy files.
  - Data artefacts are fine to pre-plan: the lexicon v0 seed list, aggregates, the rubric. But the labelled sets and the loop runs should happen during the event and be stamped in skills.md.
  - Disclose prior research spikes explicitly in skills.md.
  - Whether pre-computed *aggregates* (archetype rates) count as "pre-built" is ambiguous. Re-run the aggregation script during the event to be safe.
  - All of this is ASSUMED, not a ruling.
- **Data-on-premises:** judge and teacher calls to OpenRouter send seller turn text off premises. Jev is IndiaMART-internal. Prefer Jev / the internal gateway for anything carrying real PS07 text, and confirm the OpenRouter policy with organisers. The deck says "no customer data leaves the premises" ([persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)). ASSUMED risk. It also argues against a cross-family judge on OpenRouter for real data unless that is cleared.

### Gaps
- No organiser clarification yet on whether pre-event spikes or aggregates count as "pre-built", or whether OpenRouter counts as "leaving premises".
- Whether IndiaMART jurors favour or distrust "self-improving" claims is unknown.

---

## Q7. Are there public examples (2025–2026) of hackathon-winning or production voice agents with self-improving persona/routing loops?

### Takeaway
**Production examples exist, but they are vendor-reported and none were independently verified.** All improve prompts or configs *offline or via gated A/B*, never by learning mid-call. I found **no public hackathon-winning voice agent with a measured self-improving persona or routing loop**. That calibrates expectations: a held-out v0→v1 table would already be above the public hackathon norm, and a "learns live" claim would be unusual and hard to defend.

### Cited Findings
- **SquadStack Lift** (India, 2026-07-09): reads live calls, proposes changes, A/B tests on a small slice of traffic, and scales from small shares to a quarter, a half, then the full campaign, with a human gate and locked compliance/pricing/identity sections. Reported results: a lead marketplace at 2.7% vs 1.5% bookings on 12,000+ leads; a gold-loan lender's branch visits up from 2.2% to 4.3%. DOCUMENTED (vendor claim, no methodology detail) — [SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)
- **Cekura** (2026-07-29): failure insights from production → the customer picks a failure → the optimiser clones the agent, proposes reviewable diffs → full regression → human approval. "60K+ voice AI calls evaluated daily". No improvement metric is given in the article. The "4.8 → 5.6 CSAT" figure in a search snippet was **not found** on fetch. DOCUMENTED — [Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- **Coval × Phonely**: "self-improving agents" from continuous evaluation. Press release only. DOCUMENTED (PR) — [DestinationCRM](https://www.destinationcrm.com/Articles/CRM-News/CRM-Across-the-Wire/Coval-Partners-with-Phonely-for-Self-Improving-Agents-176413.aspx)
- **Hackathons:**
  - VoiceOS Tokyo projects prototyped agents that detect repeated user patterns and create automations. [VoiceOS](https://www.voiceos.com/blog/worlds-first-voice-only-hackathon)
  - A Vyrothon 2026 winner built a lead-calling voice agent. [GDG event](https://gdg.community.dev/events/details/google-gdg-on-campus-comsats-university-abbottabad-pakistan-presents-hack-to-hero-meet-the-vyrothon-champions/)
  - Supafone.ai pitched a "self-healing" framework at an NYC hackathon. [Luma](https://luma.com/ey5fuzqp)
  - A "LLM Feedback Loops || Voice AI Hackathon" event exists. [Luma](https://lu.ma/k71rncxx)
  - None of these report measured persona or routing improvement. DOCUMENTED (search snippets only, not fetched)
- Our own last30days scan of "self-improving agent loops" (2026-09-07 → 10-07) was dominated by hype posts and YouTube how-tos, plus one security paper (SkillPoison) on poisoned self-improvement pipelines. It found no voice-persona case with metrics. DOCUMENTED — [last30days self-improving loops](../../../raw/research/2026-10-08-last30days-self-improving-agent-loops.md)

### Inferences
- The credible industry pattern is **propose → gate on a regression/holdout set → human approves → ship**. Mirror that vocabulary ("gated", "held-out", "human-approved"), because it reads as engineering, not hype.
- Calibrating expectations: winning hackathon voice demos are judged on a working demo and a clear problem. A modest, honest v0→v1 gain on frozen real-data test sets is differentiating. Claiming more than that invites Q&A failure.

### Gaps
- I could not verify any vendor's numbers or methodology independently.
- I found no IndiaMART-internal precedent for self-improving VANI prompts. Internal sources were not searchable in this run: the IndiaMART MCP connectors needed authentication and were not used.
