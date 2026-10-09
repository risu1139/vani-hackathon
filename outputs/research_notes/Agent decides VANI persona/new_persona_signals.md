# Detecting the need for a new VANI persona: agent "no good fit" signals vs offline distance buffers

As of 2026-10-09. Tags: **DOCUMENTED** = paper, official doc, or project `raw/`/earlier report says it. **PROVEN** = our own PS07 measurement. **ASSUMED** = our design or inference. No customer data: only aggregate numbers from earlier notes are used.

Design under review:
- **Lead's design:** a nightly tool-using agent picks each seller's VANI persona (voice, style, pace, plan) from a candidate library. It can emit "no good fit, because …", and those signals drive creation of new personas.
- **Our draft V2:** a weekly agent reviews offline misfit sellers and an outcome scoreboard, then proposes new, merge, split or retire. Code checks support, stability and delivery difference, and a human approves.

Internal baseline (PROVEN, `outputs/research_notes/Data derived persona library/ps07_library_prototype.md`):
- A p95 nearest-centroid threshold flags 11.2% of held-out warm sellers (4,013); a p99 threshold flags 2.0%.
- 64.8% of misfits have transcript or question signals, against 8.1% of fitting sellers. The misfits reflect new *observation* (evaluator and transcript coverage grew in Jul–Sep), not new kinds of seller.
- Re-clustering the misfit buffer is stable within one month (K=4, bootstrap ARI 0.967) but not across months (Aug vs Sep K=3, ARI 0.540).
- Misfit outcomes are almost the same as fitting sellers': MF 9.9% vs 11.4%, NI 35.4% vs 33.9%.
- The small signal personas W5 and W6 fit loosely (flag rate about 44%).

---

## 1. How reliable are LLMs at saying "no category fits"? (open-set, abstention, NOTA)

### Takeaway
LLM "no fit" judgements are unreliable in *both* directions, and the error depends on how the prompt is written:
- **Over-assignment:** models pick the closest label even when "none of the above" is correct. Accuracy drops 30–50%, and the drop gets worse as the label set grows.
- **Abstention inflation:** adding an explicit "Unknown/None" option can make models refuse cases they could answer.

So the raw rate at which an agent says "no fit" is not a usable signal by itself. It needs an explicit, structured NONE option, several samples, and calibration against planted fit and no-fit cases.

### Cited Findings
- On MMLU, across 28 LLMs, making "None of the Above" the correct answer causes a consistent 30–50% performance drop regardless of model scale. The drop is 14.6% in maths and 48.1% in business ethics. The authors read this as LLMs lacking the ability to reject all given options (DOCUMENTED) — [None of the Above, Less of the Right, arXiv 2503.01550 (2025)](https://www.arxiv.org/abs/2503.01550)
- "Abstention Inflation": an extra "Unknown" option triggers refusals on questions the model can solve. Reasoning traces and mid-layer representations still hold the correct answer, and the refusal is a later-layer override. The effect is systematic rather than noise: it emerges through instruction tuning and grows with problem difficulty (DOCUMENTED) — [Ling et al., arXiv 2507.16199 (2025)](https://arxiv.org/abs/2507.16199)
- Even with explicit no-valid-option instructions and penalty scoring, models still give invalid forced-choice answers on a subset of items they had answered correctly. High MCQA accuracy does not guarantee reliable abstention (DOCUMENTED, very recent preprint) — [Penalty-Framed No-Valid-Option MCQA, arXiv 2610.08153](https://arxiv.org/html/2610.08153)
- Explicit abstention options raise model uncertainty and safe abstention far more than input perturbations do. Scaling model size or using advanced prompting brings little improvement (DOCUMENTED, search-snippet summary of the COLING 2025 paper) — [Do LLMs Know When to NOT Answer?, COLING 2025](https://aclanthology.org/2025.coling-main.627.pdf); survey context: [Wen et al., "Know Your Limits", TACL 2025](https://aclanthology.org/2025.tacl-1.26.pdf)
- Intent detection (Amazon / IIT Jammu, 2024):
  - LLMs are better at in-scope intent detection than at out-of-scope (OOS) detection.
  - OOS detection gets worse as the number of intents grows, and with broader intent scopes.
  - A SetFit + LLM router that sends only uncertain queries to the LLM comes within 2% of LLM-only accuracy at 50% less latency.
  - Using distances between internal representations improves OOS detection by more than 5%.
  
  (DOCUMENTED) — [Intent Detection in the Age of LLMs, arXiv 2410.01627](https://www.alphaxiv.org/abs/2410.01627)
- Verbalised confidence is overconfident: LLMs "tend to be overconfident, potentially imitating human patterns". Consistency across multiple sampled responses and better aggregation reduce this (DOCUMENTED) — [Xiong et al., arXiv 2306.13063 (ICLR 2024)](https://arxiv.org/abs/2306.13063)
- GPT-3, GPT-3.5 and Vicuna show average ECE above 0.377 for verbalised confidence, with predictions clustered at 90–100% whatever the accuracy. Well-designed prompting can bring large models to an ECE of about 0.07 (DOCUMENTED, search-snippet summary; secondary) — [Groot & Valdenegro-Toro, TrustNLP 2024, arXiv 2405.02917](https://arxiv.org/html/2405.02917v1); [Yang et al., arXiv 2412.14737](https://alphaxiv.org/overview/2412.14737v1)
- Conformal prediction on top of LLM label scores (inductive conformal, binary relevance) gives valid marginal coverage and can abstain on ambiguous inputs through **empty prediction sets** (DOCUMENTED) — [Örnbratt et al., PMLR v266 (COPA 2025)](https://proceedings.mlr.press/v266/ornbratt25a.html)
- Project precedent: rules in code plus one Sarvam wording call scored 23/23 key decisions, against 16/23 when one LLM call decided the settings (DOCUMENTED, own test) — `outputs/reports/Persona generator architecture.md`, cited in `assignment_rank_or_create.md`

### Inferences
- ASSUMED: a nightly agent with 20–50 candidate personas sits in the hard zone the intent paper describes: many labels with broad, overlapping scopes. Expect it to **under-report** no-fit for truly novel sellers and to pick the closest persona. If the prompt stresses the NONE option, expect it to **over-report** no-fit for sellers with sparse or odd data (this is the abstention-inflation pattern). The no-fit rate will move with prompt wording and model version, so a prompt tweak can look like "novelty drift".
- ASSUMED, mitigations in order of value:
  1. Score each candidate separately (persona × seller → fit 1–5 against a rubric), then declare no-fit in code when max fit is below a threshold, instead of asking an open "pick one or NONE" question. This avoids the NOTA framing that the 2025 papers show is brittle.
  2. Require a **structured reason**: `reason_code` from an enum (e.g. missing language/voice, plan mismatch, pace outside range, contradictory signals, insufficient data), plus `missing_capability` and free text.
  3. Self-consistency: use k=3 samples and count no-fit only when at least 2 of 3 agree.
  4. Treat "insufficient data" as a separate code, never as a new-persona vote. This directly blocks the PS07 failure mode, where misfit tracked data coverage.
- ASSUMED: calibrate the agent before trusting its rate. Plant about 30 synthetic "known-novel" profiles (e.g. Tamil-preferring sellers when the catalogue has no Tamil persona; the Tamil gap is noted in `wiki/projects/vani-hackathon/persona-data-validation.md`) and about 100 "known-fit" profiles. Report recall and the false no-fit rate per prompt version.

### Gaps
- I found no study of LLM no-fit or abstention reliability on **persona or segment assignment** specifically. All evidence comes from MCQA, intent and QA benchmarks.
- I found no published measurement of Sarvam models' NOTA or abstention behaviour; it has to be measured in-house.
- I could not read the full text of 2507.16199 or 2306.13063 (the PDFs would not parse), so the per-model numbers from those papers are not included.

---

## 2. Taxonomy and category expansion driven by classification failures

### Takeaway
The production-grade pattern (TnT-LLM, Clio, Lex missed utterances, intent-discovery research) has four steps:
1. **Summarise or extract a short facet per item** with an LLM.
2. **Embed and cluster** the failures or residuals.
3. **Have an LLM name and describe the clusters**.
4. **Gate on minimum support and human review.**

None of these systems lets a single per-item LLM decision create a category. Signals are always aggregated and denoised first.

### Cited Findings
- **TnT-LLM** (Microsoft, applied to Bing Copilot intents):
  - Phase 1 summarises each document to a short use-case-specific blurb (e.g. 20 words). It then builds the taxonomy over minibatches of 200 with three prompts: generate, then update (evaluate the taxonomy on new data, find issues, modify it), then review.
  - The authors frame this as SGD over prompts and pick the best of 10 trials on a validation set.
  - Label assignment includes an "Other/Undefined" category by design, to measure coverage.
  - Both LLM systems reached more than 99.5% coverage. Human inter-rater Fleiss' κ was only 0.38–0.48.
  - Phase 2 uses the LLM as labeller to train cheap classifiers for scale.
  
  (DOCUMENTED) — [Wan et al., TnT-LLM, arXiv 2403.12173 (KDD 2024)](https://arxiv.org/html/2403.12173); [Microsoft Research page](https://www.microsoft.com/en-us/research/publication/tnt-llm-text-mining-at-scale-with-large-language-models/)
- **Clio** (Anthropic, Dec 2024):
  - Extracts per-conversation "facets" (topic, language, turns), embeds natural-language facets, and runs k-means. An LLM titles and summarises each cluster from samples, and clusters are organised into a multi-level hierarchy.
  - A minimum threshold of unique users or conversations applies before a cluster is shown; one write-up cites "no cluster which represents less than 1,000 underlying individual users".
  - Agreement with the Trust & Safety classifier was r = 0.71.
  - It was used to find over-refusal clusters, i.e. clusters defined by *system failure*, not only by topic.
  
  (DOCUMENTED) — [Tamkin et al., Clio, arXiv 2412.13678](https://arxiv.org/pdf/2412.13678); [Anthropic research page](https://www.anthropic.com/research/clio); [Simon Willison summary](https://simonwillison.net/2024/Dec/12/clio/)
- **Industry new-intent loops:** Amazon Lex exposes "missed utterances" (inputs no intent matched) for bot owners to review. Its automated chatbot designer mines contact-centre transcripts to propose intents, sample phrases and slots, and a human then accepts or edits them (DOCUMENTED) — [Amazon Lex FAQ](https://aws.amazon.com/lex/faqs/); [TechCrunch 2021](https://techcrunch.com/2021/12/01/amazon-lex-brings-automated-call-transcript-review-to-chatbot-building)
- **LLM-guided clustering with feedback:**
  - ClusterLLM asks an LLM hard triplet questions ("does A correspond better to B than C") to fine-tune a small embedder, and pairwise questions to choose granularity from a hierarchy. It improved clustering on 14 datasets, including intent discovery, at low API cost via entropy-based sampling.
  - IDAS uses in-context LLM labels as descriptive summaries before embedding.
  
  (DOCUMENTED) — [Zhang et al., ClusterLLM, EMNLP 2023, arXiv 2305.14871](https://export.arxiv.org/abs/2305.14871)
- LLM-assisted new intent discovery (LANID, LREC-COLING 2024) and a hybrid BERT + LLM approach for intents and OOS in multi-party conversations (SIGDIAL 2025) continue the "known-class model + LLM on the residual" pattern (DOCUMENTED, abstract level only) — [LANID](https://www.researchgate.net/publication/401317714_LANID_LLM-assisted_New_Intent_Discovery); [arXiv 2507.22289](https://arxiv.org/abs/2507.22289)
- Persona literature (from our earlier note): LLMs alone are "not good at capturing key characteristics of user data". The best results came from an algorithm or human grouping the data and the LLM summarising the groups (DOCUMENTED) — [Shin et al., DIS 2024](https://users.aalto.fi/~luceroa1/publications/2024/shin24_persona.pdf), via `library_construction.md`
- Data-driven personas drift 18.7% per month (re-run monthly over 24 months) (DOCUMENTED) — [Jung, Jansen, Salminen, CHI EA 2019](https://pure.psu.edu/en/publications/personas-changing-over-time-analyzing-variations-of-data-driven-p/), via `library_construction.md`
- Minimum-support admission with decay (DenStream outlier micro-clusters promoted once weight crosses β·μ; stale ones fade) is already chosen in our earlier note (DOCUMENTED) — `assignment_rank_or_create.md` §3

### Inferences
- ASSUMED: the agent's "no fit, because …" text maps directly onto Clio's **facet** and TnT-LLM's **summary**. Short, use-case-specific text is the right input to clustering. So the lead's idea is well supported **as a source of facets to aggregate**, not as a trigger. Each nightly no-fit becomes a row of `(seller_id, date, prompt_version, reason_code, missing_capability, reason_text, nearest_persona, fit_scores)`, and a weekly job clusters `reason_text` embeddings within each `reason_code`.
- ASSUMED: the denoising recipe borrowed from these systems:
  1. Minimum support in distinct sellers, not in signals, because one seller can emit a no-fit every night.
  2. Persistence across at least 2 windows.
  3. LLM names each cluster from samples.
  4. A human accepts, edits or rejects.
  5. Every rejection is logged as a "known non-gap" so it is not proposed again.

  The last step mirrors TnT-LLM's review prompt and Lex's human-in-the-loop.
- ASSUMED: TnT-LLM's κ of about 0.4 between humans is a warning that "is this a real new category?" is itself subjective. Human approval needs a written rubric (§4), not taste.

### Gaps
- No public case found of category creation triggered *only* by per-item LLM "no-fit" votes with measured false-alarm rates. Every system found clusters the residual first.
- I did not find Dialogflow's or Rasa's own documentation on unhandled-intent mining in this pass; only Amazon Lex is cited. Rasa X/Studio conversation review exists in my training knowledge, but I did not verify it here.
- Clio's exact production thresholds are not public beyond the 1,000-users figure quoted in secondary coverage.

---

## 3. Decision-time agent signals vs offline distance buffers vs hybrid

### Takeaway
Neither signal alone finds "genuinely new segments":
- **Distance buffers** flag a fixed share by construction (at least 5% at p95, and 11.2% on PS07 test because of coverage drift). They find *new observation*, not new needs.
- **Agent no-fit signals** are prompt-sensitive and biased toward the closest label (§1), but they carry the *reason*, which distance cannot give.

A hybrid that requires agreement between independent signals (reason cluster ∩ distance misfit ∩ outcome gap), plus a coverage-drift guard, is the defensible design.

### Cited Findings
- Distance buffer on PS07:
  - Flag rate is 11.2% at the p95 threshold. The test distance distribution shifted right as a whole (p50 0.788 → 1.212).
  - Misfits are driven by richer history (64.8% vs 8.1% with transcript or question signals).
  - Outcomes for misfits are about the same as for fitting sellers.
  - Buffer clusters are stable within a month (ARI 0.967) but drift across months (ARI 0.540).
  
  (PROVEN) — `ps07_library_prototype.md`
- Labelling drift is also present: the Not Interested share fell from 49–57% to 19.1% in September because of a relabelling regime, not seller behaviour (PROVEN) — same file. A distance or outcome detector would read this as a "new segment".
- Distance and representation methods give measurable gains for OOS (>5% from representation distances), and uncertainty routing lets a cheap model handle most items (DOCUMENTED) — [arXiv 2410.01627](https://www.alphaxiv.org/abs/2410.01627)
- LLM OOS detection degrades with label-set size and scope breadth (DOCUMENTED, same source), and NOTA selection drops 30–50% (DOCUMENTED, [2503.01550](https://www.arxiv.org/abs/2503.01550))
- Conformal p-values with Benjamini–Hochberg give exact FDR control for outlier flags (DOCUMENTED) — [Bates et al.](https://par.nsf.gov/biblio/10485260), via `assignment_rank_or_create.md`

| Property | Agent no-fit (decision-time) | Distance buffer (offline) | Outcome gap (scoreboard) |
|---|---|---|---|
| What it sees | Reasons, delivery capabilities (e.g. "needs Tamil + slow pace, none offered") | Feature-space novelty | Results under every persona |
| Main false alarm | Abstention inflation on sparse or odd data; prompt or model version changes (DOCUMENTED pattern) | Coverage or label drift; a fixed quantile always flags (PROVEN) | Noise; confounding from non-random assignment (ASSUMED) |
| Main miss | Closest-label over-assignment (DOCUMENTED) | Novel *need* in a familiar-looking profile (ASSUMED) | Groups too small to power (≈680 calls per arm for 10% vs 15%; ASSUMED arithmetic, earlier report) |
| Cost at 12 lakh nightly | High if every seller gets an LLM call (ASSUMED) | Seconds (ASSUMED arithmetic, earlier note) | Cheap, but needs persona variation |
| Available in 2 days | Yes | Yes (done) | **No**: PS07 has one voice and one style (DOCUMENTED) |

### Inferences
- ASSUMED: the two detectors have mostly *independent* error sources. Distance errors come from data drift; agent errors come from prompts and models. Requiring both to agree should cut false alarms sharply, at the cost of missing novel needs that look familiar in the features. Recover those through a third path: agent reasons of type `missing_capability` (a delivery bundle the library lacks) can be admitted on agent signal plus support alone, because that need is checkable (does any persona offer Tamil?).
- ASSUMED, the **coverage-drift guard**, the key lesson from PS07. Before proposing, re-score the candidate cluster on *coverage-matched* sellers: restrict to sellers whose data-availability flags (transcript present, evaluator present, history depth) match train. If the misfit rate falls back to about 5%, the cluster is a coverage artefact. Apply the same check to agent reasons: drop clusters whose dominant code is "insufficient data".
- ASSUMED: the agent nightly is affordable only on a routed subset. Run it on sellers whose features changed, sellers in the distance buffer, and a random 1–2% audit sample. This follows the SetFit + LLM routing result. The random audit sample is what lets us estimate the agent's no-fit base rate and spot prompt drift.

### Gaps
- No published head-to-head of LLM-reason-driven vs distance-driven category discovery with false-alarm rates was found. The comparison table above is our synthesis.
- We have **no agent no-fit data yet**. The overlap between agent no-fit and distance misfit on PS07 is unmeasured.

---

## 4. What "need for a new VANI persona" should mean, and the data required

### Takeaway
"Doesn't look like existing clusters" is not a need. A new persona is justified only when a stable, supported seller group either:
- **(A) needs a delivery bundle no persona offers** (a capability gap: language, voice, pace range, plan or opener), checkable now; or
- **(B) does measurably worse under every existing persona than comparable sellers do under their best persona** (an outcome gap), which needs persona variation that PS07 does not have.

### Cited Findings
- PS04 FAQ Q1: "No [fixed library]… the output is a persona per seller." Distinctness across seller types is 20% of the score, fit 25%, evidence 15% (DOCUMENTED) — `raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md`, via `assignment_rank_or_create.md`
- PS07: 269,455 answered calls with one voice and one style. It cannot show which persona works for which seller, so voice-gender and timbre choices are GUESS by construction (DOCUMENTED) — `library_construction.md`
- Power: 10% vs 15% meeting rate needs about 680 calls per arm; 10% vs 13% needs about 1,770 (ASSUMED arithmetic, earlier report) — `assignment_rank_or_create.md`
- Structural changes must use outcome stats from randomised or explored traffic; deterministic assignment supports only predictive claims (ASSUMED, earlier design) — same file
- Misfit outcomes in PS07 differ from fitting sellers' by only about 1–1.5 percentage points (PROVEN), so there is no outcome evidence of an unserved segment in current data.

### Inferences
- ASSUMED definition, with three admissible triggers:
  - **A. Capability gap.** At least N_min sellers share a `missing_capability` that no library persona offers on that axis, *and* the deck/PS04 items treat that axis as persona-relevant (language, pace, plan, opener; voice only from the catalogue). Data needed: catalogue of deliverable settings per persona (Sarvam voices/languages per published `app_version`), seller language and signal features, agent reason codes.
  - **B. Outcome gap.** For a stable group G: max over personas p of the outcome under p (MF, meeting rate, or 1−NI) is below the best-persona outcome of matched comparison sellers by at least δ (e.g. 3 percentage points), with CI excluding 0, using explored traffic with at least about 700 calls per arm. Data needed: persona-varied calls with logged propensity, and the outcome scoreboard per (group, persona).
  - **C. Within-persona split.** Re-clustering a persona finds a sub-group whose best setting differs (already the split rule in `assignment_rank_or_create.md`).
- ASSUMED, explicit non-triggers:
  - feature novelty alone
  - "insufficient data"
  - groups explained by coverage or label drift
  - groups whose proposed delivery equals an existing persona on every setting. This is the "delivery-difference" check in V2; if the bundle is identical, it is a segment, not a persona.

### Gaps
- No outcome data with persona variation exists, so trigger B is not demonstrable at the hackathon. It is a design commitment only.
- The δ and N_min values are not validated on our data.

---

## 5. Recommended mechanism, thresholds, 2-day demo, devil's advocate

### Takeaway
Keep the lead's agent no-fit signal, but treat it as a **structured facet**, not a trigger, and keep V2's weekly proposer plus human gate. A candidate becomes a proposal only when:
- it has enough distinct-seller support,
- it persists across two windows,
- it passes the coverage-drift guard,
- it is backed by a capability gap (A) or an outcome gap (B),
- and either the agent reasons agree with the distance buffer, or the case is a checkable capability gap.

### Cited Findings
- Aggregate, then name, then gate on support, then human review: TnT-LLM, Clio, Lex (DOCUMENTED, §2 sources)
- Calibrated NONE handling needs explicit structure plus sampling consistency; raw verbalised confidence is overconfident (DOCUMENTED, §1 sources)
- Cross-window stability was not met in PS07 (ARI 0.54 < 0.7) (PROVEN) — `ps07_library_prototype.md`

### Inferences
**Mechanism (ASSUMED).**
1. *Nightly, routed.* Code ranks personas for all sellers. The agent runs only on changed sellers, distance-flagged sellers, and a random 1–2% audit sample.
   - The agent scores each candidate 1–5 against a rubric, with k=3 samples.
   - No-fit is declared in code when the median of max fit is 2 or less in at least 2 of 3 samples.
   - It emits `reason_code` (enum), `missing_capability`, `reason_text` and `prompt_version`. The seller still gets the nearest persona, marked low-confidence.
2. *Weekly proposer.*
   - Pool no-fit rows and distance-buffer rows per distinct seller.
   - Embed `reason_text`, cluster within `reason_code` (k-means or HDBSCAN), and cross-tab clusters against distance misfit and outcome gaps.
   - An LLM names each candidate and drafts its delivery bundle.
3. *Code gates (initial thresholds, ASSUMED).*
   - Support of at least max(500 sellers, 0.5% of active), counted in distinct sellers.
   - Present in 2 consecutive windows, with cross-window ARI or Jaccard at least 0.7.
   - Coverage guard: misfit rate on coverage-matched sellers at least 2× the base rate.
   - Agent-signal precision on the audit sample: a no-fit rate on known-fit planted profiles of 5% or less for this `prompt_version`. If a prompt or model change moves the audit no-fit rate by more than 2 percentage points, freeze proposals for that window.
   - Trigger A or B satisfied, and the delivery bundle differs from the nearest persona on at least 1 deck-relevant setting.
4. *Human approves*, with a rubric card showing support, stability, coverage check, reasons sample, delivery diff and expected test size. The new persona enters as an explored arm (Thompson sampling with starting evidence, per the earlier note). Rejections are stored as known non-gaps.
5. *Retire or merge* follows the same scoreboard, mirroring creation (earlier note).

**2-day demonstrable version (ASSUMED).**
1. Take about 200 aggregate-derived seller profiles (no real names) plus about 30 planted novel profiles (e.g. Tamil-preferring sellers when the library has no Tamil persona, and very-rushed sellers beyond the pace range) and about 30 planted clearly-fitting profiles.
2. Run the agent (Sarvam as core) with per-candidate scoring, k=3, and structured reasons.
3. Show three things:
   - recall on planted-novel profiles and false no-fit on planted-fit profiles, for one prompt version, plus a variant prompt to *show* prompt sensitivity honestly;
   - a cross-tab of agent no-fit vs the existing p95 distance flag;
   - reason-text clusters, one candidate card (the "Tamil capability gap"), and the human approve step.
4. State outright that trigger B (outcome gap) cannot be shown, because PS07 has one voice and style.

About 150–250 lines on top of the existing prototype.

**Devil's advocate (ASSUMED).**
- *"The agent signal adds nothing distance can't."* Partly true for *profile* novelty. But distance cannot express capability gaps ("needs Tamil"), and those are the only gaps we can verify without outcomes. Counter-risk: capability gaps can be found with a SQL rule (language demand vs catalogue) with no LLM at all. If the demo's only real gap is Tamil, a rule beats the agent, and judges may see the agent as decoration.
- *"Nightly LLM over 12 lakh sellers."* Expensive and unnecessary. Most sellers' state does not change nightly, and the earlier test had rules beating an LLM decider 23/23 vs 16/23. Routing is mandatory, not optional.
- *"No-fit votes are self-fulfilling."* If the agent knows its reasons create personas, prompt and rubric changes will create personas. Freezing on audit-rate shifts is the guard, but it adds process.
- *"Creating personas at all may conflict with PS04 Q1"* (a persona per seller, no fixed library). A per-seller adaptation layer already covers most "misfits" by tuning settings within a persona. Arguably a new *library* persona is needed only when per-seller adaptation cannot reach the required setting, i.e. trigger A. That argues for dropping B and C from hackathon scope entirely.
- *"PS07 says there's nothing new."* Our only evidence is that misfits are coverage artefacts with normal outcomes. A mechanism that proposes nothing on real data is the *correct* result. Present it as "the guard worked" rather than forcing a new persona for the demo.
- *"Thresholds are made up."* Yes: 500 sellers, ARI 0.7, ≤5% false no-fit and δ = 3 percentage points are untested priors. State them as config values to tune, not findings.

### Gaps
- No measured agent no-fit precision or recall yet. All agent thresholds are priors until the planted-profile test runs.
- Sarvam per-call voice and pace control is unclear (an earlier spike found session-level TTS override ignored). A capability gap may need a new published `app_version`, not just a persona row — `assignment_rank_or_create.md`.
