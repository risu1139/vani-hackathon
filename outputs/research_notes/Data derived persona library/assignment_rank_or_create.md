# Per-seller assignment layer: rank library personas, adapt, or create a new one

Scope: given a seller's refined snapshot, code (no per-seller LLM at runtime) (a) ranks/selects persona(s) from a data-derived library, (b) adapts the chosen persona into that seller's own spec, (c) decides when no persona fits and a new one should be created, and (d) learns from outcomes. As of 2026-10-09. Tags: **DOCUMENTED** = paper / official doc / project `raw/` or earlier report says it; **ASSUMED** = our design or inference. No customer data used.

Binding context from project sources:
- PS04 FAQ Q1: "No [fixed library]. The persona is generated for each seller from their data. You may group sellers into types to explain your logic, but the output is a persona per seller." FAQ Q6: missing fields → sensible defaults, marked lower confidence, corrected by live adaptation. Distinctness across seller types is 20 % of the score; fit 25 %; evidence 15 % (DOCUMENTED) — `raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md`.
- Earlier finding: rules in code + one Sarvam wording call scored 23/23 key decisions vs 16/23 for one LLM call deciding settings (DOCUMENTED, own test) — `outputs/reports/Persona generator architecture.md`, `outputs/reports/Data driven persona agent.md`.
- Earlier finding: the learning lives in versioned stats tables, every decision row logs candidates + final action + propensity; PS07 has 149,363 sellers / 269,455 answered calls with **one voice and one style**, so it cannot show which persona works for which seller; memory beats profile for next-call prediction (AUC 0.71 vs 0.58) (DOCUMENTED) — `outputs/reports/Data driven persona agent.md`.
- Implication: a library of personas is legitimate only as the *intermediate* "types" layer; the per-seller adaptation step (section 2) is what makes the output "a persona per seller" (ASSUMED reading of Q1).

## 1. Ranking / selection methods over library personas, and their cost at ~12 lakh sellers

### Takeaway
Use a two-stage "retrieve then score" shape: nearest-prototype distance in a standardised feature space gives a ranked shortlist and a free novelty signal; a per-(persona × segment) Beta/Thompson score (later LinUCB) re-ranks it from outcomes, with the executed choice's propensity logged. Everything is cheap enough to run as a nightly batch for all 12 lakh sellers, with a sub-millisecond lookup (plus a small same-day delta for changed sellers) at dial time.

### Cited Findings
- **Nearest-prototype / centroid assignment**: DP-means (Kulis & Jordan, ICML 2012) is k-means plus a penalty λ per cluster; a point opens a new cluster when its squared distance to every existing centroid exceeds λ, and the algorithm monotonically converges to a local optimum of the penalised objective (DOCUMENTED) — [Kulis & Jordan, arXiv 1111.0352](https://arxiv.org/pdf/1111.0352); [ICML'12 PDF](https://people.bu.edu/bkulis/pubs/dpmeans_icml12.pdf). Larger λ → fewer clusters (DOCUMENTED) — [R dpmeans docs](https://search.r-project.org/CRAN/refmans/T4cluster/html/dpmeans.html). This gives assignment and the "create" rule in one distance computation.
- **Class-conditional Gaussian / Mahalanobis scoring**: fit per-class means and a shared covariance, score = −min Mahalanobis distance across classes; reported robust with noisy labels or few samples (DOCUMENTED) — [Lee et al., NeurIPS 2018, arXiv 1807.03888](https://arxiv.org/abs/1807.03888v2); [AWS Fortuna OOD docs](https://aws-fortuna.readthedocs.io/en/stable/references/ood_classifier.html). Same quantity serves as persona-ranking score and as OOD score (section 3).
- **Retrieval + rerank (two-stage)**: YouTube's recommender splits into a candidate-generation model and a separate ranking model (DOCUMENTED) — [Covington et al., RecSys 2016](https://research.google/pubs/pub45530). For VANI the "corpus" is tiny (tens of personas), so retrieval is just top-k by distance; the pattern matters only because the reranker can use outcome data the distance cannot (ASSUMED).
- **Contextual bandits over library personas**: LinUCB models persona choice as a contextual bandit; Yahoo! Front Page Today Module, 33M+ events, reported 12.5 % click lift vs context-free bandit (DOCUMENTED) — [Li, Chu, Langford, Schapire, WWW 2010, arXiv 1003.0146](https://arxiv.org/pdf/1003.0146). Thompson sampling is "highly competitive", easy to implement and should be a standard baseline; evaluated on display ads and news recommendation (DOCUMENTED) — [Chapelle & Li, NIPS 2011](https://proceedings.nips.cc/paper_files/paper/2011/file/e53a0a2978c28872a4505bdb51db06dc-Paper.pdf).
- **Decomposed (per-dimension) bandits rather than per-whole-persona**: Aampe groups "tone-of-voice, emoji use, value propositions, recommendations, and promotional incentives into smaller and manageable action sets" to avoid "combinatorial explosion of modelling every unique combination"; cold start uses "an empirical Bayes prior … imputing the distribution's parameters based on behaviour from similar users—inspired by user-based collaborative filtering"; 150M users, main experiment 6.4M users over three weeks (DOCUMENTED, vendor-authored) — [Aampe, arXiv 2506.16429](https://arxiv.org/html/2506.16429v1). Update cadence and how new actions join the catalogue are **not stated** in the paper (DOCUMENTED absence).
- **CRM next-best-action**: Pega backs every action with an adaptive model whose output is a propensity; new actions' propensities "are not reliable as they would have too few or no customer responses", so Thompson sampling is used during cold start (DOCUMENTED) — [Pega docs: model learning for new actions](https://docs-previous.pega.com/node/2307541). Earlier report: StartingPropensity weight 1, StartingEvidence 25 pseudo-responses (DOCUMENTED) — `outputs/reports/Data driven persona agent.md` citing [Pega Academy](https://academy.pega.com/node/47811). A Pega patent describes "one statistical model … generated per cluster by applying a multi arm bandit technique during a cold start period" (DOCUMENTED, patent) — [USPTO 11151467](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11151467). This is the closest documented precedent for "bandit per persona-cluster".
- **Mixture / soft assignment**: Archetypal analysis (Cutler & Breiman 1994) represents each individual as a convex mixture of "pure type" archetypes, which are themselves mixtures of real data points; in customer segmentation it describes extremes at the periphery rather than the average member (DOCUMENTED) — [Cutler & Breiman, Technometrics 1994](https://www.stat.cmu.edu/technometrics/90-00/vol-36-04/v3604338.pdf); [Survey, arXiv 2504.12392](https://arxiv.org/html/2504.12392v2). Directly supports "this seller = 0.7 × Price-objector + 0.3 × Busy-owner", blended per dimension.
- **Decision logging requirement**: logging probability must be nonzero wherever a new policy acts for off-policy evaluation; deterministic choice ⇒ propensity 1 ⇒ no OPE (DOCUMENTED) — `outputs/reports/Data driven persona agent.md` citing [Bottou et al. arXiv 1209.2355](https://arxiv.org/abs/1209.2355) and [Decision Service arXiv 1606.03966](https://arxiv.org/abs/1606.03966).

### Inferences
- **Method comparison (ASSUMED, our synthesis):**

| Method | Needs outcome labels? | Gives novelty signal? | Interpretable to judges | Hackathon-feasible | Production role |
|---|---|---|---|---|---|
| Nearest prototype (Euclid/Mahalanobis on standardised features) | No | Yes (distance) | High ("closest to Price-objector, d=1.2") | Yes | Stage 0 ranker + OOD |
| Classifier over personas (multinomial LR / GBM on cluster labels) | No (labels = cluster ids) | Weak (softmax over-confident on OOD; see Scheirer open-space risk, §3) | Medium | Yes but adds little over distance | Distilled fast assigner if features grow |
| Retrieval + rerank | Rerank does | Yes (stage 1) | Medium | Retrieval yes, rerank no data yet | Default production shape |
| Learning-to-rank (LambdaMART etc.) | Yes, many graded outcomes per persona × context | No | Low | No (PS07 has one persona only) | Only after months of randomised logs |
| Thompson per (persona × segment), Beta posteriors | Yes, but works from zero with priors | No | High (rate ± interval) | Yes as prior-only, logs propensity | Stage 1–2 reranker |
| LinUCB / linear TS with seller features | Yes | No | Medium | No | Stage 2 once thousands of calls/persona |
| Soft mixture (softmax over −distance / archetypal weights) | No | Yes (max weight low) | High per dimension | Yes | Blending layer before adaptation |

- **Recommended shape (ASSUMED):** score_p(seller) = −d_Mahalanobis(x, μ_p) [fit] + β·TS_draw(persona p, segment) [outcomes; β=0 at hackathon] ; take top-3; softmax weights w_p ∝ exp(−d_p²/τ); per-dimension blend: categorical settings (voice app_version, language) take argmax persona's value; ordinal settings (pace, formality, warmth, brevity) take Σ w_p · level_p rounded to the catalogue's discrete level. Log candidates, weights, and propensity of the executed choice.
- Blending per dimension mirrors Aampe's decomposition and avoids a combinatorial persona space; it also means "personas" are really bundles of priors per dimension, which is the honest reading under FAQ Q1 (ASSUMED).
- **Cost at 12 lakh sellers (ASSUMED arithmetic):** K≈20–50 personas, d≈15–30 features. Distance matrix 1.2M × 50 × 30 ≈ 1.8 × 10⁹ multiply-adds — seconds on one CPU core with NumPy/DuckDB; no ANN index (FAISS) needed at K this small. Per-persona Beta tables are K × segments rows. LinUCB with d=30 keeps one 30×30 matrix per arm — trivial. So: **nightly batch** recompute of all assignments into a `persona_assignment` table (seller_key, as_of, top-k, weights, distance, ood_flag, versions); **at dial time** only a key lookup plus the Thompson draw (microseconds) plus template filling. A per-seller LLM at dial time would be 12 lakh calls/night — the thing the brief excludes and the earlier 16/23 result argues against.
- Dial-time re-scoring is needed only for sellers whose snapshot changed today (new call outcome, DNC, language switch); handle as an intraday delta job (ASSUMED).

### Gaps
- No public source reports persona-library assignment for outbound *voice* calls specifically; analogues are recommenders, NBA and Aampe.
- Aampe's update cadence and new-action onboarding are not stated in its paper.
- No source found quantifying how many library personas are "enough" for B2B seller calls; K must come from our own clustering + stability (§4).

## 2. Per-seller adaptation on top of the chosen persona(s)

### Takeaway
The library supplies priors; the seller's own spec is produced deterministically by layering seller memory, hard facts and slot-filled plan content on top, with field-level provenance and confidence, so two sellers assigned the same persona still get visibly different specs with seller-specific reasons.

### Cited Findings
- FAQ Q6: missing fields → "fall back to sensible defaults, mark the affected choices as lower confidence in the spec, and let live adaptation correct them"; §3.2: "every setting … comes with a short explanation tied to the seller data"; §3.3: every plan element tied to seller data; guardrails: delivery only, never facts/pricing/compliance (DOCUMENTED) — `raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md`.
- Seller's own history is the strongest PS07 lever: next-call meeting AUC 0.71 memory vs 0.58 profile; next-NI 0.78 vs 0.54 (DOCUMENTED, own measurement) — `outputs/reports/Data driven persona agent.md`.
- Seller memory as bi-temporal derived view; traits as Beta posteriors shrunk to segment rate; state facts decay (~20-day half-life) (DOCUMENTED design in earlier report) — `outputs/reports/Data driven persona agent.md`.
- Retrieving a user's *own* past items helps every LaMP personalisation task (DOCUMENTED) — [LaMP, arXiv 2304.11406](https://arxiv.org/abs/2304.11406) (cited in earlier report).
- Case-based reasoning "Reuse" + "Revise" steps: reuse the retrieved case's solution, revise it for the new problem (DOCUMENTED) — [Aamodt & Plaza 1994, AI Communications 7(1)](https://www.doi.org/10.3233/AIC-1994-7104). The persona is the retrieved case; adaptation is the revise step.
- Empirical-Bayes shrinkage to similar users for sparse individuals (DOCUMENTED) — [Aampe](https://arxiv.org/html/2506.16429v1).

### Inferences
- **Precedence stack per setting (ASSUMED design):** (1) hard gates/guardrails (DNC, language with no catalogue voice) → (2) seller's own evidence (memory: preferred language, rushed on ≥2 past calls, objection history) when n ≥ threshold → (3) blended library-persona value (§1) → (4) segment default → (5) global default. Record which layer won as `source` and set `confidence = f(layer, n, persona weight, distance)`; layers 4–5 or missing inputs → `confidence: low` (satisfies Q6 literally).
- Shrinkage formula for traits: p̂_seller = (k + m·p_persona)/(n + m) with m≈5–25 pseudo-calls (Pega StartingEvidence=25 as a reference point). A seller with 0 calls inherits the persona; a seller with 10 rushed-of-12 calls overrides it (ASSUMED).
- **Personalisation slots** (filled by code from snapshot, reviewed templates only): name/business name, top category, city/language, last-call outcome and date, last objection, pending action (e.g. catalogue incomplete), engagement trend. Each slot carries its source field for the reason string.
- **Conversation-plan facts**: plan moves come from an approved plan library keyed by persona (opening, objection order, escalation); seller facts choose ordering (e.g. last objection "price" → price-objection move first). One optional offline-or-batch wording pass may polish phrasing, but the decision of *which* move is code (consistent with 23/23 vs 16/23 result).
- **Distinctness guarantee (ASSUMED):** a "persona_delta" field lists every setting where the seller's spec differs from its base persona and why; judges then see a per-seller spec, with the type only as explanation — the exact framing FAQ Q1 permits.
- Missing-field defaults should *also* shrink persona weights toward the population centroid (use only observed dimensions in the distance, renormalised), and flag `distance_computed_on: 9/14 features` (ASSUMED).

### Gaps
- No source found on optimal shrinkage strength m for sales-call traits; needs fitting on PS07 memory features.
- Whether Sarvam can apply per-call pace/voice is outside this note (earlier spike: session-level TTS override ignored; voice varies only via published `app_version`) — `outputs/reports/Data driven persona agent.md`.

## 3. The "create a new persona" decision

### Takeaway
At runtime, code never creates a persona; it only flags misfits (distance / density / conformal p-value below threshold) and still serves them a nearest-or-population-default spec marked low-confidence. Misfits accumulate in a buffer; offline, once a dense, stable group of misfits reaches minimum support, re-clustering proposes a candidate persona, an LLM drafts its name/description/plan entries, a human approves, and it enters the bandit with a Pega-style starting prior.

### Cited Findings
- **Open set recognition**: classifiers trained on known classes label everything as a known class; "open space risk" is feature space far from training data that still gets a known label; Scheirer et al. 2013 bound it with a 1-vs-Set machine (DOCUMENTED) — [Scheirer, Rocha, Sapkota, Boult, IEEE TPAMI 35(7) 2013](https://bv.fapesp.br/en/publicacao/68968/toward-open-set-recognition); [explainer in arXiv 2110.11013](https://ar5iv.labs.arxiv.org/html/2110.11013). Implication: a softmax classifier over personas will confidently assign a misfit; use distance.
- **Reject option**: Chow (1970) — the Bayes-optimal rejector abstains when max posterior < 1 − λ_r, trading error rate against reject rate (DOCUMENTED) — [Reject-option survey, arXiv 2107.11277](https://arxiv.org/pdf/2107.11277).
- **Distance-based OOD**: Mahalanobis score to nearest class-conditional Gaussian (DOCUMENTED) — [Lee et al. 2018](https://arxiv.org/abs/1807.03888v2).
- **Conformal novelty detection**: conformal p-values from a held-out calibration set of inliers test whether a new point is an outlier; with Benjamini–Hochberg, split-conformal p-values give exact FDR control across many test points (DOCUMENTED) — [Bates et al., "Testing for outliers with conformal p-values" (NSF PAR)](https://par.nsf.gov/biblio/10485260); [Bashari et al., arXiv 2302.07294](https://arxiv.org/pdf/2302.07294); [Liang et al., arXiv 2208.11111](https://ar5iv.labs.arxiv.org/html/2208.11111). Practical: p = (1 + #{calibration sellers with score ≥ s}) / (n_cal + 1); flag if p < α. This gives a defensible "x % of normal sellers would be falsely flagged" number.
- **DP-means**: new cluster when distance to all centroids > λ (DOCUMENTED) — [Kulis & Jordan](https://arxiv.org/pdf/1111.0352). Online variants used for streaming.
- **BIRCH**: CF-tree; a sample merges into the nearest subcluster only if the merged radius < threshold, otherwise starts a new subcluster; supports `partial_fit` for batches (DOCUMENTED) — [scikit-learn Birch](https://scikit-learn.org/1.5/modules/generated/sklearn.cluster.Birch.html).
- **Streaming k-means**: Spark MLlib update c_new = (c·n·a + x̄·m)/(n·a + m), with decay factor a or half-life in batches/points (DOCUMENTED) — [PySpark StreamingKMeans](https://spark.apache.org/docs/3.5.8/api/python/reference/api/pyspark.mllib.clustering.StreamingKMeans.html); [Databricks blog 2015](https://databricks.com/blog/2015/01/28/introducing-streaming-k-means-in-spark-1-2.html). Lets persona centroids drift with the population.
- **Minimum support before admission — DenStream**: keeps potential micro-clusters (weight ≥ β·μ) and outlier micro-clusters (weight < β·μ); outlier micro-clusters keep absorbing points and are **promoted** when their weight crosses the threshold; weights decay with λ so stale misfit groups die (DOCUMENTED) — [streamMOA manual](https://mhahsler.r-universe.dev/streamMOA/doc/manual.html); [outlierdenstream docs](https://outlierdenstream.readthedocs.io/en/latest/modules.html). This is the textbook form of "misfit buffer → admit when supported".
- **Case-based reasoning cycle**: Retrieve the most similar past case, Reuse its knowledge, Revise the proposed solution, Retain the part of the experience useful later (DOCUMENTED) — [Aamodt & Plaza 1994](https://www.doi.org/10.3233/AIC-1994-7104); [overview, arXiv 1401.0802](https://arxiv.org/pdf/1401.0802). Retain = adding a new case/persona to the library.
- **LLM offline for naming/taxonomy, cheap model online**: TnT-LLM (Microsoft, Bing Copilot logs) uses an LLM to generate and iteratively refine a taxonomy, then LLM pseudo-labels train a "lightweight, scalable supervised classifier" that labels the full corpus offline and can serve online (DOCUMENTED) — [TnT-LLM summary, HackerNoon reprint of paper](https://hackernoon.com/tnt-llm-automating-text-taxonomy-generation-and-classification-with-large-language-models). Anthropic Clio: extract facets → embed → k-means → LLM writes a title and summary per cluster → hierarchy; humans see only cluster-level output (DOCUMENTED) — [Clio, arXiv 2412.13678](https://arxiv.org/pdf/2412.13678); [Anthropic post](https://anthropic.com/news/clio). Both put the LLM at *description* time, not per-item assignment time.
- **Cold-starting the new persona's arm**: Pega Thompson sampling + StartingEvidence for new actions (DOCUMENTED) — [Pega](https://docs-previous.pega.com/node/2307541).

### Inferences
- **Runtime rule (ASSUMED):** for seller x with nearest persona p*: `fit = conformal_p(d_Mahalanobis(x, μ_p*))` calibrated on held-out *assigned* sellers. If p ≥ α (e.g. 0.05): rank/adapt (§1–2). If p < α: `ood_flag=true`; still produce a spec from the soft blend or the population-default persona, all ordinal settings pulled toward neutral, confidence low, live adaptation trusted more (higher switch sensitivity); write seller into `misfit_buffer`. Never block the call.
- **Admission criteria (ASSUMED, numbers to tune):** offline (weekly) run HDBSCAN/DP-means on buffer ∪ small sample of assigned sellers; candidate group admitted only if (a) support ≥ N_min (e.g. ≥ 0.5 % of active sellers or ≥ 500 sellers, whichever larger — enough for a ~700-calls-per-arm test later), (b) bootstrap Jaccard stability ≥ 0.75 (Hennig rule, §4), (c) separation: its centroid's own conformal p under existing personas < α for most members, (d) it would change at least one *delivery* setting vs nearest persona (otherwise it's a segment, not a persona — prevents library bloat and protects the distinctness criterion), (e) human approves the LLM-drafted card.
- **What the LLM drafts offline (ASSUMED):** persona name, one-paragraph description from aggregate feature profile (means, top categories, objection mix — no seller text), proposed per-dimension settings with reasons citing aggregates, draft opening/objection plan entries from the approved move library; human reviewer edits; persona enters with `tier=GUESS`, Beta prior of ~10–25 pseudo-calls centred on nearest parent's rates, exploration floor. Clio-style privacy: LLM sees only cluster aggregates.
- **Removal/merging mirrors creation:** DenStream-style decay — a persona whose assigned weight falls below threshold for N cycles is retired or merged (§4).
- **Why not online DP-means at dial time:** creates personas from single outliers (λ is a hard threshold, no support requirement), makes assignment order-dependent, and creates arms with no plan library or human review. DenStream's two-tier (outlier → potential) design is the right analogue: buffer first, promote later.

### Gaps
- No public production case found of a voice-call or CRM system that auto-proposes *new personas/segments* from misfit buffers; Pega/Aampe document adding new *actions* manually, not discovering them. The pipeline above is assembled from clustering/OOD literature (ASSUMED composition).
- Calibration α and N_min values have no outside source for this domain.
- TnT-LLM details seen via a reprint, not the arXiv original; claims kept at summary level.

## 4. Outcome feedback, library evolution, and evaluation

### Takeaway
Outcomes update per-(persona × segment × setting) Beta tables that re-rank candidates; structural changes (split, merge, retire, admit) happen only in a gated offline job judged by stability, fit, separation and — once randomised logs exist — off-policy outcome lift. Assignment quality is evaluated on held-out sellers and time-split snapshots, with stability as a first-class metric.

### Cited Findings
- Bootstrap cluster stability (Hennig, `fpc::clusterboot`): resample, recluster, mean Jaccard to best-matching cluster; ≥ 0.85 "highly stable", ≥ 0.75 valid, 0.6–0.75 "patterns … doubtful membership", ≤ 0.5 "dissolved" (DOCUMENTED) — [clusterboot docs](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html).
- Streaming centroid drift with explicit half-life (DOCUMENTED) — [PySpark StreamingKMeans](https://spark.apache.org/docs/3.5.8/api/python/reference/api/pyspark.mllib.clustering.StreamingKMeans.html).
- Statsig contextual bandit retrains hourly, prefers explore data for training, monitors random vs targeted traffic (DOCUMENTED) — cited in `outputs/reports/Data driven persona agent.md` ([Statsig](https://docs.statsig.com/autotune/contextual/methodology)).
- Off-policy evaluation of a real LLM coaching agent found a policy raising average value harmed specific subgroups; recommend per-archetype metrics (DOCUMENTED) — earlier report citing [arXiv 2510.17173](https://arxiv.org/abs/2510.17173).
- Feedback loops in recommenders homogenise behaviour without raising utility (DOCUMENTED) — earlier report citing [Chaney et al. arXiv 1710.11214](https://arxiv.org/abs/1710.11214).
- Power: distinguishing 10 % vs 15 % meeting rate needs ≈ 680 calls per arm; 10 % vs 13 % ≈ 1,770 (ASSUMED arithmetic in earlier report) — `outputs/reports/Data driven persona agent.md`.
- Aampe effects in a 6.4M-user RCT were small (+0.07 % to +0.48 % conversion) (DOCUMENTED) — [Aampe](https://arxiv.org/html/2506.16429v1).
- TnT-LLM pattern: re-derive taxonomy periodically with LLM, distill to cheap classifier for full-corpus labelling (DOCUMENTED) — [TnT-LLM](https://hackernoon.com/tnt-llm-automating-text-taxonomy-generation-and-classification-with-large-language-models).

### Inferences
- **Feedback tables (ASSUMED):** `persona_stats(persona_id, segment, setting, level, alpha, beta, n_eff, version)` updated nightly from `decision ⨝ outcome`, with forgetting; reranker score uses Thompson draws from these; soft-assigned calls credit each persona by its weight w_p (fractional counts) — but only the *executed* settings get credit, keyed by propensity.
- **Split rule:** a persona splits when (a) within-persona outcome heterogeneity is significant on a pre-registered feature (e.g. turnover band shows different best pace with CI excluding 0 after ≥ N calls each side), or (b) re-clustering finds a stable (Jaccard ≥ 0.75) sub-cluster with a different best setting. **Merge rule:** two personas whose settings converge (same level on all delivery dimensions) or whose clusters fail separation (bootstrap Jaccard < 0.6 when re-clustered with K−1). **Retire:** assigned share below floor for N cycles (DenStream-style decay). All changes create a new `library_version`; old assignments are remapped and the remap is logged so stats carry over by weighted inheritance.
- **Evaluation (ASSUMED protocol):**
  1. *Held-out sellers* (seller-hash split): assignment fit = mean distance / conformal p of held-out sellers; OOD rate should be ≈ α on in-distribution hold-out (calibration check).
  2. *Time split*: build library on snapshots ≤ T, assign at T+30d — measures drift and assignment churn.
  3. *Assignment stability*: % sellers whose top-1 persona changes between consecutive nightly runs without a material data change (target < a few %); bootstrap Jaccard per persona.
  4. *Distinctness*: pairwise distance between persona setting vectors; min number of delivery dimensions differing (maps to the 20 % criterion).
  5. *Predictive fit proxy (pre-randomisation)*: does persona membership + memory predict next-call outcome/rush/language better than profile alone? (PS07 can answer this; it cannot answer which persona *causes* better outcomes.)
  6. *Causal (post-launch only)*: OPE (IPS/DR) of new library version vs logged policy; holdout lift; per-persona subgroup reports.
- Guard against self-reinforcement: outcome stats must come from randomised/explored traffic when used for structural changes; deterministic-assignment data only supports predictive, not causal, claims (consistent with earlier report).

### Gaps
- No source found that reports assignment-churn targets for customer segmentation systems in production.
- No public evidence on whether persona-level (vs per-dimension) bandits learn faster in sales calls; Aampe's decomposition is the only documented production choice.

## Devil's advocate: over-engineering for a 2-day hackathon, and the minimum convincing version

### Takeaway
Judges score fit, switches, distinctness, voice and evidence — not the learning loop. The minimum version that convincingly demonstrates "rank-or-create" is ~150 lines of code: standardised features → k-means/DP-means library with LLM-named cards (offline, reviewed) → Mahalanobis ranking + softmax blend → per-seller adaptation with provenance → conformal-threshold misfit flag that routes one deliberately unusual demo seller to the buffer and a pre-computed "candidate new persona" card.

### Cited Findings
- Evaluation weights: fit 25, switches 25, distinctness 20, natural voice 15, evidence 15; FAQ Q1 forbids presenting a fixed library as the output (DOCUMENTED) — `raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md`.
- Build budget already tight: ~20–30 dev-hours of core work vs ~18–24 usable (DOCUMENTED, earlier report) — `outputs/reports/Data driven persona agent.md`.
- PS07 has zero persona variation, so no outcome-based reranking can be validated during the event (DOCUMENTED) — same report.
- Thompson sampling is easy to implement and a strong baseline (DOCUMENTED) — [Chapelle & Li 2011](https://proceedings.nips.cc/paper_files/paper/2011/file/e53a0a2978c28872a4505bdb51db06dc-Paper.pdf).

### Inferences
- **Risk 1 — the library undercuts FAQ Q1.** If the demo shows "Seller A → Persona 3", judges may read it as the forbidden fixed library. Mitigation: lead with the per-seller spec and its `persona_delta`; show the library only in the "why" panel (ASSUMED).
- **Risk 2 — "create new persona" is unfalsifiable in 2 days.** No outcomes, so admission can be shown only on structure (support, stability, separation). Pre-compute it offline on PS07 aggregates; show the buffer → candidate card → human-approve step as a recorded artefact, not live (ASSUMED).
- **Risk 3 — bandits/LinUCB/LTR add zero demo value now** (no outcome variation). Keep the Beta tables and propensity column (cheap, from the earlier report's day-one list); skip LinUCB, LTR, streaming clustering, conformal FDR across batches.
- **Risk 4 — distance in mixed categorical/numeric space is fragile.** Standardisation choices dominate assignments; a rules table (earlier 23/23 approach) may give better per-seller fit than clusters for the 6–10 sample sellers. Steelman: skip clustering and use rules + memory; the library is optional explanation sugar. Counter: rules don't produce a "create new" path, and clusters supply the "types" explanation Q1 allows plus the distinctness evidence (ASSUMED).
- **Risk 5 — conformal thresholds on few hundred PS07 sellers are noisy;** use simple percentile-of-calibration-distance (equivalent to split-conformal) and state α.
- **Minimum version checklist (ASSUMED):**
  1. Offline: features from PS07 aggregates (turnover band, engagement, objection mix, language share, rush/confusion rates, past outcome mix), standardise, k-means K≈6–10 (or DP-means with λ chosen so K is in range); bootstrap Jaccard per cluster reported; Sarvam/LLM names each cluster and drafts its card from aggregates; human edits. Save `persona_library_v1.json` with centroids, covariance, settings, evidence tier.
  2. Runtime (code only): distance to all centroids → top-3 + softmax weights → per-dimension blend → precedence stack with seller memory and slots → spec with reasons, `source`, `confidence`, `persona_delta`.
  3. Novelty: calibration distances from held-out sellers → threshold at 95th percentile → `ood_flag`, low-confidence default spec, buffer row.
  4. Show one contrasting trio for the voice demo, plus one OOD seller whose spec says "no persona fits (p=0.02); conservative defaults; flagged for library review".
  5. Log decision row with candidates, weights, final settings, propensity=1 (or ε-explore off for judged sellers), library_version.
- Everything in §1 bandits, §3 DenStream/BIRCH streaming, §4 split/merge and OPE goes on the "production roadmap" slide, not in code.

### Gaps
- Organiser view on whether a persona library (even as intermediate layer) is acceptable beyond FAQ Q1's wording is unknown.
- Whether PS07 feature aggregates produce stable clusters (Jaccard ≥ 0.75) is untested; must be measured before relying on clustering for the demo.
