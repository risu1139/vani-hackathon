# Building and maintaining a data-derived persona library for VANI (PS04)

As of 2026-10-09. Tags: **DOCUMENTED** (a primary or secondary source, or a `raw/`/wiki file, says so), **PROVEN** (measured by us on PS07 aggregates or in a spike, as already reported in our own notes), **ASSUMED** (our design inference, untested).
Binding requirements: [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md). FAQ Q1: "Fixed library of personas? No. The persona is generated for each seller from their data. You may group sellers into types to explain your logic, but the output is a persona per seller." FAQ Q6: missing fields → sensible defaults, lower confidence, let live adaptation correct.
Context read: [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md), [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md). No customer data appears here; all PS07 numbers are aggregates already reported in those files.
Scope note: the [deep-research researcher brief](C:/Users/Imart/.claude/skills/.trash/1791477575408-31924-4v9nGl/deep-research/references/researcher.md) was found only in the skills trash folder, not at the synced path given; its format was followed.

## Q1. What does research and practice say about generating personas from data (APG, NMF, k-means, LCA, mixtures, archetypal analysis, CRM segmentation, LLM synthesis, evaluation)?

### Takeaway
Data-driven persona generation is a mature line of work (QCRI/Jansen–Salminen, 2005–2025): **algorithm finds segments → segments are "humanised" into personas**. The consistent lessons are (a) behavioural segments come first and demographics are attached after, (b) personas drift measurably month to month, (c) "how many" is a representativeness trade-off and is usually set far too low, and (d) LLMs are good at *summarising pre-grouped data* and bad at *finding the groups*. Evaluation remains the field's weakest point.

### Cited Findings
- **APG (Automatic Persona Generation, QCRI).** Uses **non-negative matrix factorization (NMF) first to find behavioural segments** (from interactions with content), then to find demographic segments (gender, age, location), then auto-adds names, photos and attributes to make "rich persona descriptions". Validated on >30M interactions, 198 countries, >4,200 videos; evaluated by accuracy of predicting a persona's content preference, **stability over time**, and generalisability to other datasets — DOCUMENTED — [An, Kwak, Salminen, Jung, Jansen 2018 (UTU record)](https://research.utu.fi/converis/portal/detail/Publication/42818979?lang=en_US); [QCRI blog](https://persona.qcri.org/blog/imaginary-people-representing-real-numbers-generating-data-driven-personas-using-the-apg-system/). (The blog and abstract do not give the accuracy numbers; full paper not read.)
- **Personas drift.** Same algorithm re-run monthly for 24 months, 15 personas per month: **18.7% average monthly change, 23.3% yearly, 47% over two years**; 35 unique personas over the period. Authors' implication: personas need continuous data collection and refresh — DOCUMENTED — [Jung, Jansen, Salminen, CHI EA 2019](https://pure.psu.edu/en/publications/personas-changing-over-time-analyzing-variations-of-data-driven-p/); [QCRI search summary](https://persona.qcri.org/blog/persona-analytics-research/)
- **How many personas.** On 250M YouTube views, persona sets from 5 to 160 were compared against baseline user data. More personas covered more age groups and countries and matched the raw data better; **relative diversity gain was maximal at 40 personas**, >4× the usual "fewer than ten" practice — DOCUMENTED — [Salminen et al., "Creating more personas improves representation…"](https://persona.qcri.org/blog/creating-more-personas-improves-representation-of-demographically-diverse-populations-implications-towards-interactive-persona-systems/)
- **Too many personas.** On 26M airline user records, "thin personas" (key behaviours + demographics) were collapsed with an algorithmic cost function from **1,593 to 493 (−69%)** while keeping the whole population represented — DOCUMENTED — [Jansen, Jung, Salminen, CHI EA 2019](https://persona.qcri.org/blog/too-many-personas/)
- **Survey of 77 data-driven persona papers (2005–2020):** periods Quantification → Diversification → Digitalization; named gaps are **evaluation methods, standardisation, shared resources, inclusivity, and loss of in-depth user insight** — DOCUMENTED — [Salminen, Guan, Jung, Jansen, IJHCI 2021](https://persona.qcri.org/blog/a-survey-of-15-years-of-data-driven-persona-development/). (Per-algorithm counts not visible on the summary page.)
- An earlier comparison of persona clustering methods found **factor/principal-component analysis outperformed LSA and multivariate cluster analysis** for identifying personas — DOCUMENTED (search summary) — [USF, comparative analysis of persona clustering methods](https://pure.lib.usf.edu/en/publications/a-comparative-analysis-of-persona-clustering-methods-2/)
- **Archetypal analysis vs k-means.** k-means describes a segment by its *average* member and optimises homogeneity; archetypal analysis finds *extreme exemplars on the periphery* and optimises contrast, which practitioners report gives "richer and more actionable" and better-separated segments — DOCUMENTED (practitioner sources) — [Sawtooth 2023 session](https://events.sawtoothsoftware.com/analytics-and-insights-summit/2023/session/finding-contrastive-market-segments-with-archetypal-analysis); [R-bloggers](https://www.r-bloggers.com/2012/07/archetypal-analysis/)
- **Latent class / mixture models** are the standard model-based clustering for mixed data (within-class independence assumption); class count is chosen with BIC and classification **entropy** (separation); partially missing cases enter via FIML, though multiple imputation has been reported to recover profiles better — DOCUMENTED — [Marbac & Sedki, variable selection for mixed data, arXiv 1703.02293](https://arxiv.org/pdf/1703.02293); [tidySEM LCA vignette](https://cran.nics.utk.edu/cran/web/packages/tidySEM/vignettes/lca_confirmatory.Rmd); [entropy-based LCA for incomplete data](https://researchconnect.suny.edu/en/publications/latent-class-analysis-of-incomplete-data-via-an-entropy-based-cri/)
- **LLM-assisted synthesis.**
  - Human–AI workflow study: LLMs alone are **"not good at capturing key characteristics of user data"**; best results came from **humans (or an algorithm) grouping the data and LLMs summarising the pre-grouped data**, which was more representative than humans or LLMs alone — DOCUMENTED — [Shin et al., DIS 2024](https://users.aalto.fi/~luceroa1/publications/2024/shin24_persona.pdf); [Aalto record](https://research.aalto.fi/en/publications/understanding-humanai-workflows-for-generating-personas/)
  - PersonaCraft (IJHCS 2025): LLM system turning survey segments into personas; rated high on clarity, completeness, fluency, consistency, credibility by general users (n=127) and UX professionals (n=21). Note: these are *perception* criteria, not predictive validity — DOCUMENTED — [Jung, Salminen, Aldous, Jansen 2025](https://qcai.qcri.org/publications/personacraft-leveraging-language-models-for-data-driven-persona-development)
  - Systematic review of 52 GenAI-persona papers (2022–2024): GPT in 82.7%; real user data in 53.8%; **~44% had no clear evaluation**; humans involved in segmentation in only **1.9%** vs enrichment 71.2%; JSON persona format in 9.6%; 69.2% discuss ethics/stereotyping — DOCUMENTED — [Amin, Salminen et al. 2025, arXiv 2504.04927](https://arxiv.org/html/2504.04927v1)
  - "Cluster persona" = centroid of a group of collaborative-filtering embeddings used to steer an LLM, explicitly instead of demographic personas — DOCUMENTED — [Li et al., steerability toward data-driven personas, arXiv 2311.04978](https://arxiv.org/html/2311.04978v2)
  - Review of 63 synthetic-persona LLM studies (2023–2025): task and population often underspecified; **only 35% discuss representativeness**; proposes a transparency checklist (representative sampling, empirical grounding) — DOCUMENTED — [Whose Personae?, AIES](https://ojs.aaai.org/index.php/AIES/article/view/36553)
  - Persona collapse: high per-persona fidelity co-occurs with the most stereotyped populations — DOCUMENTED — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698) (via [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md))
- **Evaluation dimensions found in the literature:** predictive accuracy of persona preferences, stability over time, generalisability (APG); representativeness vs raw data distribution ("how many"); perception scales (clarity, completeness, consistency, credibility; PersonaCraft); population coverage/uniformity/pairwise distance (persona collapse / Persona Generators) — DOCUMENTED (sources above)
- **Cluster stability standard:** Hennig's `clusterboot` resamples (bootstrap, subsetting, jitter, noise) and takes per-cluster mean Jaccard to the best-matching resampled cluster. **≥0.75 = valid, stable; 0.6–0.75 = pattern exists but membership doubtful; ≤0.5 = "dissolved"** — DOCUMENTED — [fpc::clusterboot docs](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html)

### Inferences
- ASSUMED: the APG recipe maps cleanly onto VANI: **behavioural/outcome segmentation (APG's "behavioural NMF") → attach descriptive profile fields (turnover, business type, region) after → deterministic spec mapping → LLM writes only the prose**. This is the Shin et al. split (algorithm groups, LLM summarises) and avoids the 1.9%-human-in-segmentation trap.
- ASSUMED: for "clearly different" personas (distinctness 20%), archetypal analysis or a contrast-seeking method is a better fit than k-means centroids, which pull every type toward the average seller. Practical compromise: cluster with LCA/k-prototypes, then describe each type by its most extreme *driving* features, not by the centroid.
- ASSUMED: the field's evaluation methods (perception scales) do not fit PS04. Our evaluation must be **stability (Jaccard), coverage, distinctness (Mantel/Hamming, already designed), and per-type outcome differences** (which is the "evidence" 15%).

### Gaps
- Full texts of APG (2018), "how many personas", and PersonaCraft were not read; their exact algorithms (e.g., NMF rank selection, PersonaCraft's segmentation step) and accuracy numbers are unconfirmed.
- No source found applying data-driven persona generation to **voice/telephony sales agents** or to B2B sellers in India.
- The classic Chapman & Milham "personas' new clothes" argument (multi-attribute personas describe a vanishing share of the population) could not be retrieved; not cited.

## Q2. Which features, how many personas, and how to handle mixed and missing data?

### Takeaway
Segment on **behaviour and outcomes** (engagement, call duration, pickup, past dispositions, objection type, call-later history), not on profile fields. Our own PS07 numbers already show this: seller history predicts next-call outcomes far better than profile. Choose k by **stability first** (bootstrap Jaccard ≥0.75 per type), then BIC/silhouette as tie-breakers, then a **business-usability cap**: every type must change at least one deliverable setting. Use mixed-data methods (LCA, k-prototypes, Gower+PAM) and treat missingness as information plus a confidence flag (FAQ Q6).

### Cited Findings
- **Behaviour beats profile, in our data:** next-call meeting AUC **0.71 for seller memory/history vs 0.58 for profile**; next-NI AUC 0.78 vs 0.54 — PROVEN — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md) citing [learning loops](../../../wiki/projects/vani-hackathon/learning-loops.md)
- Industry analogue: Netflix found demographics "almost useless" for predicting behaviour ("Geography, age, and gender? We put that in the garbage heap"), using ~2,000 behaviour-defined "taste communities"; within-group variation exceeds between-group differences — DOCUMENTED (press interviews; executive statement, not a study) — [Fortune 2016](https://fortune.com/2016/03/27/netflix-predicts-taste); [Adweek](https://www.adweek.com/tv-video/netflix-thrives-by-programming-to-taste-communities-not-demographics/)
- Marketing response-modelling literature tends to find **RFM (behaviour) plus demographics** beats either alone; few studies integrate demographics *during* clustering rather than post hoc — DOCUMENTED (secondary, weak) — [preprints.org 202504.1434](https://www.preprints.org/manuscript/202504.1434/v1)
- APG segments on behaviour first and attaches demographics second — DOCUMENTED — [APG](https://research.utu.fi/converis/portal/detail/Publication/42818979?lang=en_US)
- Industry routing systems that pair callers with agents exclude protected attributes (no gender/nationality) — DOCUMENTED — via [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md) ([Genesys](https://help.genesys.cloud/articles/use-of-ai-in-predictive-routing/), [Afiniti](https://www.afiniti.com/responsible-ai/how-it-works/))
- **Mixed data:** k-prototypes = k-means distance on numerics + simple matching on categoricals with a hand-set weight; Gower distance (handles ordinal too) + PAM is the common alternative; a convergent Gower-based k-prototypes variant exists for large data. Known pitfalls: the numeric/categorical balance must be hand-picked and **high-cardinality categoricals dominate the distance** — DOCUMENTED — [clustMixType::kproto](https://search.r-project.org/CRAN/refmans/clustMixType/html/kproto.html); [Springer ADAC 2024 (Gower k-prototypes)](https://link.springer.com/10.1007/s11634-024-00595-5); [mixdist](https://pypi.org/project/mixdist/)
- **Missing data:** LCA uses FIML for partially missing cases; multiple imputation reported better at recovering profiles; entropy-based criteria exist for incomplete data — DOCUMENTED — [tidySEM](https://cran.nics.utk.edu/cran/web/packages/tidySEM/vignettes/lca_confirmatory.Rmd); [SUNY entropy LCA](https://researchconnect.suny.edu/en/publications/latent-class-analysis-of-incomplete-data-via-an-entropy-based-cri/)
- **Number of personas:** representativeness keeps improving up to ~40 (diversity gain peak) — [QCRI](https://persona.qcri.org/blog/creating-more-personas-improves-representation-of-demographically-diverse-populations-implications-towards-interactive-persona-systems/); an algorithmic cost function can prune a large set by 69% without losing coverage — [QCRI](https://persona.qcri.org/blog/too-many-personas/); per-cluster stability via bootstrap Jaccard ≥0.75 — [clusterboot](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html); BIC/entropy for LCA — [tidySEM](https://cran.nics.utk.edu/cran/web/packages/tidySEM/vignettes/lca_confirmatory.Rmd) — DOCUMENTED
- **PS07 feature facts (aggregate):** 149,363 sellers; turnover missing 11%, nature of business missing 11%, avg answered call missing 13%; free-text `past_objections` present for only **2.7%**; `showed_frustration`=1 for only 139 sellers; no language-preference column (state is the proxy). A coarse 5-feature grid has 285 populated cells, 181 with ≥50 sellers, top 10 cells = 41.7% — PROVEN — [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md)
- Seller-file history columns leak future (Apr–Sep) information; history must be rebuilt as-of the decision time — PROVEN — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)

### Inferences
- ASSUMED feature set, in three roles:
  1. **Segmentation features (behaviour/outcome, as-of t):** answered-call duration band, short-call share, pickup ratio, call-later count, NI count, meeting/positive count, objection-type mix (where present), language observed in past calls (if transcripts exist), recency.
  2. **Descriptive overlay (attached after, APG-style):** turnover band, nature of business, region/state, category. Used for language default, formality and personalisation, and to *explain* types; not to define them.
  3. **Confidence features:** `missing_fields[]`, `n_past_calls`, completeness score.
- ASSUMED: encode missingness as its own level ("no history") rather than imputing behaviour. A seller with zero answered calls is a real, large type (cold start) and should map to the default persona with low confidence (FAQ Q6), not be imputed into a confident type.
- ASSUMED: drop or bucket high-cardinality fields (city, category id) before Gower/k-prototypes, or they dominate distance; use them only in the personalisation slot.
- ASSUMED k-selection procedure: sweep k (e.g., 4–20); keep k where **every type has bootstrap Jaccard ≥0.75 and ≥~1–2% of sellers**; prefer lower BIC/higher entropy (LCA) or silhouette (k-prototypes) as a tie-break; then apply the **actionability test**: merge any two types that map to the same deliverable settings. Expect a library of roughly 6–15 *behavioural* types; the per-seller layer (Q5) creates many more distinct personas than types.
- ASSUMED: the "40 personas" result is about *demographic representation* for designers, not about delivery differences. For VANI, more types than distinct settings combinations is wasted; the cap is the number of distinguishable delivery/plan configurations.
- ASSUMED: LCA is attractive for the hackathon because it outputs a **posterior membership probability** per seller, which becomes the "evidence strength / confidence" field directly, and it handles mixed + missing data natively.

### Gaps
- No published study found comparing behavioural vs demographic segmentation specifically for **outbound call outcomes**; the strongest evidence is our own PS07 AUC result.
- Silhouette/BIC disagreement rates on mixed data were not researched; no source found for a principled minimum cluster share.

## Q3. How does a cluster become a persona spec with evidence, and which settings can and cannot be derived from data?

### Takeaway
A cluster can justify settings that describe **seller behaviour we observed** (rushed → brief; long engaged calls → richer plan; repeated NI → objection-first playbook; call-later → time-first opener; region/past language → language). It **cannot** justify voice gender, timbre or pitch, because PS07 used one voice and style, so there is zero variation to learn from. Those must be labelled GUESS/low-confidence, kept gender-neutral in rule form, and learned later by logged variation.

### Cited Findings
- PS07: **269,455 answered calls with one voice and one style**; zero variation in voice, tone and pace, so it can show which sellers convert and which signals predict outcomes, but **never which persona works for which segment** (positivity) — PROVEN/DOCUMENTED — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)
- Bot-version assignment in PS07 was non-random: 87.4% of a seller's consecutive calls used the same version; 97% of Tamil Nadu sellers got one version — PROVEN — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)
- PS04 requires each setting with a reason tied to seller data and an honest statement of evidence strength vs informed guess (§3.2, §3.4) — DOCUMENTED — [PS04](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Live adaptation examples PS04 itself gives: slow down and simplify when confused; shorten when rushed; switch language when the seller does (§3.5) — DOCUMENTED — [PS04](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Outside voice evidence is thin and not Indian: tone mattered most and gender×age had only a small effect (335 US participants, synthetic voices); moderate rate (~3.5 words/s) and lower pitch favoured in 1,380 survey introductions — DOCUMENTED — via [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md) ([arXiv 2405.04791](https://ar5iv.labs.arxiv.org/html/2405.04791))
- Personalisation by demographics gave negligible persuasion gains at scale (76,977 participants) — DOCUMENTED — via the same report ([arXiv 2507.13919](https://arxiv.org/abs/2507.13919))
- IndiaMART's own three static-personalisation trials did not beat control — PROVEN — via [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md)
- Session-start voice override was ignored in our SDK spike; voice/pace vary only via published `app_version`s for now — PROVEN — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)

### Inferences (ASSUMED derivation table)

| Persona setting | Derivable from cluster behaviour? | Driving evidence (cluster statistic) | Evidence tier |
|---|---|---|---|
| Brevity / opening length | Yes | short-call share, median answered duration, hang-up-early rate | MODERATE if the type's outcome rate differs with n ≥ 200 and a time split holds; otherwise WEAK |
| Pace (within safe range) | Partly | same rush signals; confusion proxies (repeat/clarification turns in transcripts) → slower | WEAK (direction inferred from behaviour; pace itself never varied in PS07) |
| Simplicity / formality | Partly | confusion proxies, turnover band, entity type | WEAK / GUESS |
| Objection playbook order | Yes | type's objection mix (price / trust / time / already-in-touch / not-interested) from dispositions and the 2.7% free-text | MODERATE where counts allow; GUESS where objection text is absent |
| Opener move (value-first / time-first / relationship) | Yes | call-later history, NI history, past meeting rate | MODERATE (behavioural) |
| Escalation rules | Yes | DNC, already-in-touch, repeated NI | STRONG (rule/compliance-driven) |
| Language start + Hinglish mix | Yes | past observed call language (if available), else state proxy | MODERATE (state proxy) / STRONG (observed) |
| Warmth / empathy | Partly | frustration flags (sparse: 139), NI count | WEAK |
| Voice gender | **No** | none: one voice in PS07 | GUESS by construction; assign by catalogue coverage/rotation, never by seller demographics |
| Timbre / pitch | **No** | none; pitch may not even be honoured on v4 | GUESS; learn via exploration |

- ASSUMED spec-assembly step per type: for each setting, store `{level, driving_statistic, n, rate_in_type, rate_overall, interval, tier, reason_template}`. The reason is generated from these numbers ("sellers like this hung up within 20 s in 41% of answered calls vs 31% overall → brief opener"), so every reason traces to a statistic. Numbers here are illustrative, not measured.
- ASSUMED: "descriptive" differences between types are not the same as "this setting works better for them". Behavioural statistics justify *what the seller does*; only outcome differences across varied delivery would justify *what works*. In PS07 the honest claim is: "type X rushes; we infer brevity helps (inferred, not tested)". Tier it WEAK unless a natural experiment exists (e.g., the `personalis` bot version, 452 calls, if randomly assigned — an open question in the agent report).
- ASSUMED: voice gender/timbre should come from a separate, explicit **exploration policy** (balanced rotation among published voices per language, logged with propensity), so later data can learn it. This matches the agent report's decision layer.

### Gaps
- Whether PS07 transcripts allow a reliable "confusion" proxy (clarification requests, repeats) is untested.
- No natural experiment on delivery variation in PS07 is confirmed; without it no delivery setting reaches STRONG from past calls.

## Q4. How should the library be maintained (versioning, drift, merge/split/retire, governance)?

### Takeaway
Treat the library as a **versioned model artifact** re-fitted on a schedule, with cluster-lineage tracking (survive / merge / split / disappear / emerge), stability gates before any change ships, and a human approval step. Persona drift is large enough (≈19% monthly in QCRI's data) that a static library goes stale; but each refresh must keep IDs stable for surviving types so that logged outcomes remain joinable.

### Cited Findings
- Persona sets change 18.7% monthly, 23.3% yearly, 47% over two years when re-generated with the same algorithm; authors recommend continuous data collection — DOCUMENTED — [Jung, Jansen, Salminen 2019](https://pure.psu.edu/en/publications/personas-changing-over-time-analyzing-variations-of-data-driven-p/)
- **MONIC** (Spiliopoulou, Ntoutsi, Theodoridis, Schult 2006) classifies cluster transitions between snapshots: external = **survived, merged, split, disappeared, emerged**; internal = changes in location and cohesion of survivors. Implemented in R `clusTransition` — DOCUMENTED — [clusTransition docs](https://www.rdocumentation.org/packages/clusTransition/versions/1.0/topics/Transition); [CRAN](https://www.stats.bris.ac.uk/R/web/packages/clusTransition/index.html)
- Cluster validity per type: bootstrap Jaccard ≥0.75 stable; ≤0.5 dissolved — DOCUMENTED — [clusterboot](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html)
- Pruning a large persona set with a cost function while keeping representation (1,593 → 493) — DOCUMENTED — [QCRI](https://persona.qcri.org/blog/too-many-personas/)
- Production analogues retrain on fixed cadences (Afiniti nightly, Genesys weekly with A/B) and keep promotion human-gated (NVIDIA data flywheel: "a flashlight, not an autopilot") — DOCUMENTED — via [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)
- Pega cold-starts a new action with a starting propensity weighted as 25 pseudo-responses, plus Thompson noise — DOCUMENTED — via the same report ([Pega Academy](https://academy.pega.com/node/47811))
- Decision logs must record versions in play (`rule_table`, etc.) at decision time; this cannot be backfilled — DOCUMENTED — via the same report ([Decision Service, arXiv 1606.03966](https://arxiv.org/abs/1606.03966))

### Inferences (ASSUMED maintenance protocol)
- **Artifacts:** `persona_library_vN` = {type_id, definition (centroid/archetype + feature ranges), membership model (LCA posteriors or nearest-prototype rule), per-setting levels + statistics + tier, stability Jaccard, size share, created_from, parent_ids}. Content-hashed and listed in the version manifest the agent report already proposes.
- **Assignment at runtime (no LLM):** score the seller against all types (posterior or distance), take top-1 (and top-2 for blending, Q5). If max posterior < threshold or distance > the type's radius, mark **"novel"**.
- **New-type creation from novels (not per seller):** novels accumulate in a buffer; a batch job re-clusters the buffer; a candidate type is promoted only if it has ≥ N sellers (e.g., ≥0.5–1% or a few hundred), Jaccard ≥0.75, and its derived settings differ from every existing type on ≥1 deliverable setting. Otherwise the novel sellers keep the nearest type plus the per-seller adaptation layer. This answers the team lead's "create a new persona when none fits" without letting one odd seller create a library entry.
- **Refresh cadence:** monthly re-fit (QCRI drift) or when assignment confidence drops / novel share rises above a threshold (e.g., >10%). Match new clusters to old by membership overlap (MONIC); survivors keep their `type_id`, merges/splits create new IDs with `parent_ids`, disappearances are **retired** (kept in the registry, not deleted, so old decisions still resolve).
- **Gates before shipping vN+1:** per-type Jaccard ≥0.75; no type <1% share; distinctness metrics (Mantel r, per-dimension entropy from the distinctness notes) not worse than vN; reassignment churn for unchanged sellers below a threshold; human approval (product + compliance) for any new type's settings.
- **Evidence carry-over:** posteriors (Beta) for settings are keyed by `type_id`; on split, children inherit the parent's posterior down-weighted (Pega-style pseudo-count); on merge, pool counts.
- **Governance:** hypothesis register for every GUESS setting; audit voice-gender allocation per type (alarm at >80% one-gender skew, as in the agent report); no protected attributes as features.

### Gaps
- No source found on persona-library versioning specifically for conversational agents; the protocol is an analogy from cluster-evolution and decisioning systems.
- Thresholds (novel share 10%, min size) are ASSUMED and need calibration on PS07.

## Q5. How do we reconcile a library with FAQ Q1 ("no fixed library; persona per seller")?

### Takeaway
Use the library as **building blocks and evidence**, not as the output. Each seller gets a **composed** persona: type-derived defaults (soft-weighted across their top types) + **per-seller overrides** from their own history + data-quality confidence + personalisation slots + live adaptation. FAQ Q1 explicitly allows "group sellers into types to explain your logic", so the types are the explanation layer and the per-seller spec is the output. The library also grows, so it is not "fixed".

### Cited Findings
- FAQ Q1 text (verbatim above) allows types for explanation; output must be per seller — DOCUMENTED — [PS04](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- FAQ Q6: missing fields → defaults, lower confidence, live correction — DOCUMENTED — [PS04](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Per-seller history (memory) is the strongest predictor (AUC 0.71 vs 0.58) — PROVEN — [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)
- Aampe learns per user per *dimension* (tone, value prop, etc.) with priors from similar users (empirical Bayes) — DOCUMENTED — via the same report ([arXiv 2506.16429](https://arxiv.org/html/2506.16429v1))
- Rules-in-code + one LLM wording call scored 23/23 vs 16/23 for LLM-decided settings on synthetic sellers — PROVEN (circular labels) — via the same report
- A cluster persona can be the centroid of a group, while an individual persona is the individual's own embedding; both can steer an LLM — DOCUMENTED — [arXiv 2311.04978](https://arxiv.org/html/2311.04978v2)

### Inferences (ASSUMED composition, all code, no per-seller LLM)
1. **Refine** seller data as-of t → feature vector + `missing_fields` + completeness.
2. **Soft-assign** to types: posterior weights w_k (LCA) or softmax over distances; keep top-2.
3. **Type defaults**: each setting's level = weighted vote/average of top types' levels (ordinal settings such as pace average; categorical settings take the max weight unless the margin is small, in which case pick the more conservative level).
4. **Per-seller overrides** (the empirical-Bayes idea): where the seller has enough own history, the seller's own statistic overrides the type (e.g., this seller personally hung up early in 3/3 calls → brief, even if the type is "engaged"). Shrink seller rate toward type rate by n.
5. **Profile overlay**: language from observed/state; formality from entity/turnover; personalisation slots (category, city, last interaction).
6. **Confidence**: per setting = f(type posterior, own-history n, missing fields, tier). Low confidence → conservative default + flagged for live adaptation (FAQ Q6).
7. **Novel handling**: if no type fits, use nearest type + overrides + "novel" flag; seller enters the buffer for the next library refit (Q4).
8. **Output**: one spec per seller with each setting's reason citing (type statistic and/or own statistic), tier, and `library_version`; LLM (Sarvam) only phrases opener/playbook text under fixed levels (single batched or templated call, or cached per type×slot for scale).

- ASSUMED framing for judges: "Types explain; the seller's own data decides." Show the per-seller spec, then the type it most resembles as the evidence card.
- ASSUMED scale note: at ~12 lakh sellers, steps 1–7 are vectorised table operations (DuckDB/pandas), milliseconds per seller. LLM text can be cached per (type, language, opener move) and slot-filled, keeping the "no per-seller LLM at runtime" constraint while still giving per-seller wording via slots.

### Gaps
- Whether judges will read type-defaults-plus-overrides as "per seller" or as "a fixed library in disguise" is unknown; ask organisers on Day 1.

## Q6. Devil's advocate: collapse, stereotyping, non-actionable clusters

### Takeaway
The main risks are not algorithmic. They are (1) clusters that differ on paper but map to the same delivery, (2) a library that hides per-seller variation and looks like the "fixed library" FAQ Q1 rejects, (3) stereotyped voice choices dressed up as data, and (4) instability that makes "evidence" an artefact of the random seed.

### Cited Findings
- Persona collapse: most faithful models produce the most stereotyped populations — DOCUMENTED — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)
- GenAI persona review: 69.2% of papers raise stereotyping/bias; ~44% have no clear evaluation — DOCUMENTED — [arXiv 2504.04927](https://arxiv.org/html/2504.04927v1)
- Only 35% of synthetic-persona studies discuss representativeness — DOCUMENTED — [AIES, Whose Personae?](https://ojs.aaai.org/index.php/AIES/article/view/36553)
- k-means tends to find "average" segments that may not be well separated — DOCUMENTED (practitioner) — [Sawtooth 2023](https://events.sawtoothsoftware.com/analytics-and-insights-summit/2023/session/finding-contrastive-market-segments-with-archetypal-analysis)
- Personas drift ~19% per month — DOCUMENTED — [Jung et al. 2019](https://pure.psu.edu/en/publications/personas-changing-over-time-analyzing-variations-of-data-driven-p/)
- Static personalisation trials at IndiaMART did not beat control — PROVEN — via [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md)
- PS07 grid: top 10 cells hold 41.7% of sellers; objection text sparse (2.7%) — PROVEN — [distinctness notes](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md)
- UNESCO criticism of female-by-default "obliging, docile" assistants — DOCUMENTED — via [Data driven persona agent report](../../reports/Data%20driven%20persona%20agent.md)

### Inferences (ASSUMED)
- **Non-actionable clusters.** A cluster on turnover × region may be stable and still change nothing audible. Rule: a type exists only if it changes ≥1 deliverable setting; otherwise merge. Run the actionability test *before* naming types.
- **Collapse via the library.** If 40% of sellers fall into 2–3 big types and overrides rarely fire, most sellers get identical specs — exactly "minor variations of one". Monitor largest-spec share (target <~10%, per distinctness notes) and the share of sellers whose spec differs from their type default.
- **Stereotyping.** Clustering can launder demographic stereotypes if profile fields drive the clusters ("rural/small → female warm voice"). Keep profile fields out of segmentation; keep voice gender out of rules; audit allocation.
- **Evidence illusion.** Types describe behaviour, not effect of delivery. Claiming "type X responds better to brief openers" from PS07 is unsupported unless delivery varied. Label it inferred.
- **Instability.** If Jaccard <0.75, the "evidence" behind a type is seed noise. Report stability per type on the slide.
- **Over-engineering.** For a 2-day hackathon, LCA/k-prototypes + bootstrap stability + a derivation table + composition code is enough. MONIC lineage, novel buffers and monthly refits are production design to describe, not to build. Steelman for skipping clustering entirely: per-seller rules on raw features already give per-seller output (the existing B2 rules design) — clusters then serve only as the explanation and evidence layer, which FAQ Q1 explicitly permits. This may be the simpler, safer path.
- **Sparse signals.** Frustration (139 sellers) and objection text (2.7%) are too sparse to define types; use them only as per-seller overrides.
- **Out of scope:** LLM-generated persona narratives (names, photos, backstories), as in APG/PersonaCraft — PS04 scores delivery settings and evidence, not empathy-evoking descriptions.

### Gaps
- No source found measuring whether behavioural clusters in sales-call data correspond to differential response to delivery (treatment-effect heterogeneity); that needs randomised live traffic.
