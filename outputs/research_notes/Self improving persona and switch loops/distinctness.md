# Persona distinctness for PS04: guarantee it, measure it, keep it fit-aligned

As of 2026-10-08. Tags: **PROVEN** (we ran it or the data shows it), **DOCUMENTED** (a primary source says so), **ASSUMED** (our design inference, untested).
Binding requirements: [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md), [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md). Distinctness = 20% ("clearly different personas, not minor variations of one"). Fit = 25%. FAQ Q1: no fixed library, output is per seller, grouping into types is allowed to explain the logic.
Local data analysed in aggregate only (PS07 seller files, 149,363 rows, 58 columns). No seller names, IDs or messages appear here.

## Q1. What research quantifies LLM persona homogenization, and which fixes worked?

### Takeaway
"Persona collapse" is a measured, current failure mode (2025–2026). Agents given distinct profiles converge on a few behaviour modes, and the most faithful-looking models produce the *most* stereotyped populations. The fixes that worked share one idea: **diversity is an explicit, measured objective over a defined attribute space** (questionnaire axes, MAP-Elites grids, dedup thresholds, evolved generators). Asking the model to "be diverse" is not enough.

### Cited Findings
- **Persona collapse** (Xiao et al., 2026): agents with distinct profiles "converge into narrow behavioral modes, producing homogeneous simulated populations". Measured with three population-level metrics, **coverage, uniformity and complexity**, across 10 LLMs on BFI-44 personality, moral reasoning and self-introductions. "The models achieving the highest per-persona fidelity consistently produce the most stereotyped populations." Variation "tracks coarse demographic stereotypes rather than fine-grained individual differences". The abstract proposes no mitigation; the authors release a toolkit — DOCUMENTED — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)
- **Artificial Hivemind** (NeurIPS 2025 Best Paper): strong **intra-model repetition** (one model gives similar answers to repeated prompts) and stronger **inter-model homogeneity** (different models give strikingly similar outputs). Built on Infinity-Chat: 26K open-ended queries, 31,250 human annotations — DOCUMENTED — [arXiv 2510.22954](https://arxiv.org/abs/2510.22954); [NeurIPS](https://neurips.cc/virtual/2025/oral/121422)
- LLM responses are more similar to each other than human responses are, even after controlling for structure ("We're Different, We're the Same") — DOCUMENTED — [arXiv 2501.19361](https://arxiv.org/html/2501.19361v1). Group-level homogenization rises even when individual idea counts rise — DOCUMENTED — [Homogenization Effects of LLMs, arXiv 2402.01536](https://arxiv.org/html/2402.01536v2)
- A study of 69 models from 12 provider families (2023–2026 releases) found a statistically significant **decline** in output diversity over time. It names alignment (RLHF/DPO) as a known amplifier — DOCUMENTED (secondary summary via search; not fully read) — [arXiv 2604.01504](https://arxiv.org/pdf/2604.01504)
- LLM-generated personas follow stereotypes and flatten identity (PersonaWeaver; Lazik et al. 2025; Bombieri & Rospocher 2025) — DOCUMENTED (search-summary level) — [PersonaWeaver arXiv 2609.26629](https://arxiv.org/pdf/2609.26629)
- **Fix 1: explicit diversity axes plus an evolved generator.** DeepMind's *Persona Generators* separate "density matching" from "support coverage". The method generates questionnaires with **diversity axes**, uses a two-stage generator (Stage 1 makes population-level diversity decisions autoregressively, Stage 2 expands each persona in parallel), and evolves the generator code with **AlphaEvolve** (LLM-as-mutation). Metrics: Monte-Carlo coverage, convex-hull volume, min and average pairwise distance, dispersion, and KL to a quasi-random reference. Coverage was **>80% on held-out questionnaires**, beating Nemotron Personas and other baselines on every metric — DOCUMENTED — [arXiv 2602.03545](https://arxiv.org/html/2602.03545v1)
- **Fix 2: quality-diversity (QDAIF).** MAP-Elites with LM mutation and **AI feedback that scores both quality and the diversity attribute**. Each grid cell keeps its best solution. It covered more of the target space with high-quality samples than non-QD controls, and humans broadly agreed with the AI scores (ICLR 2024) — DOCUMENTED — [arXiv 2310.13032](https://arxiv.org/pdf/2310.13032)
- **Fix 3: dedup thresholds.** Persona Hub (1B personas) dedups with MinHash (1-gram, 128-signature, sim 0.9) and embedding cosine > 0.9 — DOCUMENTED — [arXiv 2406.20094](https://arxiv.org/html/2406.20094v1)
- **Fix 4: distribution alignment.** Population-aligned persona generation filters low-fidelity personas, then uses importance sampling to match reference distributions (Big Five) — DOCUMENTED — [arXiv 2509.10127](https://arxiv.org/abs/2509.10127v2)
- **Fix 5: DPP / determinant-based selection.** The determinant of a similarity kernel measures the volume spanned by the items, so maximising it picks diverse, low-redundancy subsets. Used in determinantal beam search and in instruction-data subset selection — DOCUMENTED — [Determinantal Beam Search, arXiv 2106.07400](https://ar5iv.labs.arxiv.org/html/2106.07400); [Reliability-aware DPP, arXiv 2602.00885](https://arxiv.org/html/2602.00885v1)
- Our own spike: prompt-only behaviour is inconsistent (one neutral run gave a callback, another a 30-word pitch) — PROVEN — [deep-research system design](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)

### Inferences
- ASSUMED: if one LLM generates the whole spec from free text, PS04 personas will collapse to "polite, warm, medium pace, Hinglish" with reworded reasons. That is the "minor variations of one" judges penalise. The Chameleon finding warns that the most *fluent* spec writer is the most at risk.
- ASSUMED: the transferable fix is the Persona Generators pattern scaled down. **Stage 1 = deterministic rules** that put each seller on discrete attribute levels from seller features (our existing B2 rules design). **Stage 2 = LLM** that only writes the prose (opening line, playbook wording, reasons) under those levels. This makes distinctness structural, not stylistic, and it matches the [persona-architecture](../../../wiki/projects/vani-hackathon/persona-architecture.md) direction ("rules for hard fields; LLM writes only the prose").
- ASSUMED: QD, DPP and AlphaEvolve are built for *generating populations*. PS04 instead needs a *function of the seller*. They are useful as (a) a **coverage check** (did the grid get used?) and (b) a **demo-seller picker**, not as the generator.

### Gaps
- No paper found on persona distinctness in **voice/sales-agent** personas specifically. All evidence comes from social simulation and creative text.
- The 69-model diversity-decline paper and PersonaWeaver were seen only at search-summary level.

## Q2. How do we define a persona attribute space that maps to Sarvam-controllable settings and plan variants?

### Takeaway
Use a **small, discrete, explicit grid** of about 8 dimensions with 2–4 levels each. Every level maps to a concrete Sarvam knob (speaker id, pace, pitch, language) or to a scripted plan variant (opening style, objection playbook, escalation). Every level is chosen by a rule on seller features and carries a reason. The seller data has enough populated variety to fill such a grid without inventing noise.

### Cited Findings
- **Sarvam knobs per call:** v4 voices in our catalogue = **176** (112 female, 64 male). Use-case tags: Customer Support 45, Conversational 32, Narration 22, Social Media 15, Advertisement 14, Educational 12, Collections & Recovery 10, Sales 7, Companion 7, Storytelling 7, Assistant & IVR 4. Best-language tags: Hindi 89, English 56, Marathi 9, Punjabi/Kannada/Telugu 4 each, Tamil 3, Gujarati 3, Bengali/Assamese 2 each. Descriptor words in the descriptions: high 70, warm 33, soft 32, slow 23, friendly 20, fast 8, measured 8, confident/calm/energetic 4 each, deep 2 — PROVEN (counted from [catalogue](../../../raw/research/2026-10-07-sarvam-voice-catalogue.json))
- Per-session SDK `text_to_speech_config` (speaker, pace, pitch) override is DOCUMENTED but **not yet exercised** (test T9) — [system-design deep research](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md); [Sarvam Python SDK](https://docs.sarvam.ai/conversations/deploy/sdks/python) (the fetched SDK page did not list the field ranges)
- **Conflict on pitch:** public Bulbul docs say **v3 has no pitch or loudness**, pace 0.5–2.0. v2 had pitch −1..1 (suitable −0.75..0.75), loudness 0.1–3.0, pace 0.3–3.0. The public page does not mention v4 — DOCUMENTED — [Sarvam Bulbul docs](https://docs.sarvam.ai/api/models/bulbul). The brief's "pace 0.9–1.4 in UI, pitch ±0.2" comes from the agent UI and is not in public docs. Whether **pitch is honoured on v4 must be measured from audio** (Q3).
- The voice is fixed per call: "Voice is assigned per language at call start and will not change mid-conversation". Tone, formality, brevity and language can change live — DOCUMENTED/PROVEN — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md)
- Pace anchors: crisp ~1.1, warm 0.9–0.95, floor ~0.85, based on "slightly slower raises satisfaction 7.1%" — DOCUMENTED evidence, ASSUMED mapping — [Knowledge at Wharton](https://knowledge.wharton.upenn.edu/article/how-speaking-slower-influences-consumer-behavior/) via [deep research](../../../raw/research/2026-10-08-deep-research-vani-problem-choice-system-design.md)
- **Seller-feature variety (aggregate, PROVEN, PS07 seller files n=149,363):**
  - turnover: 58% "0–40 L", 25% 40 L–5 Cr, 6% >5 Cr, 11% missing
  - nature of business: Manufacturer 23%, Trader-Retailer 20%, Wholesaler/Distributor 17%, Service 17%, missing 11%
  - state region: Hindi belt 52%, West (GJ/MH/Goa) 34%, South 4%, other 10%. Top states: Gujarat 18%, UP 17%, Maharashtra 16%, Delhi 15%
  - past outcome: ≥1 "not interested" 48%, call-later only 11%, neither 42%
  - avg answered call: short (≤20 s) 31%, mid 38%, long (>60 s) 18%, missing 13%
  - free-text `past_objections` present for only **2.7%**; `showed_frustration`=1 for only 139 sellers
  - No explicit language-preference column was found (state is the proxy)
- **Grid occupancy (PROVEN, aggregate):** a coarse 5-feature grid (size 4 × region 4 × bot-answer band 3 × past-outcome 3 × call-duration band 4 = 576 cells) has **285 populated cells, 181 with ≥50 sellers**. The largest cell holds 7.6% and the top 10 hold 41.7%. Joint entropy is 6.28 bits against a max of 8.15 for the populated cells. Normalised per-feature entropy: size 0.78, region 0.77, engagement 0.60, outcome 0.87, duration 0.94, nature of business 0.89.

### Inferences
- ASSUMED proposed persona space. Each level is rule-chosen, and each rule cites a seller field.

| Dim | Levels | Sarvam / plan knob | Driving seller features |
|---|---|---|---|
| D1 voice gender+timbre | F-warm/soft, F-bright/fast, M-measured/deep, M-energetic | `speaker` id from catalogue tags | business type, size, nature of business (ASSUMED mapping; evidence from past-call outcomes if any) |
| D2 language | Hindi-heavy Hinglish, English-heavy Hinglish, regional (Gujarati/Marathi) + Hindi fallback | `initial_language_name` + speaker's best-language tag | state/region |
| D3 pace | 0.9 / 1.0 / 1.15 (stay inside the UI-safe range) | `pace` | avg answered-call seconds, short-call share, call-later history |
| D4 pitch | −0.15 / 0 / +0.15 (only if audible on v4) | `pitch` | pairs with D1; drop it if not measurable |
| D5 formality | aap-formal / neutral / casual-trade | prompt variable | turnover, Limited Company vs Proprietorship |
| D6 warmth/empathy | high / medium / low-and-brisk | prompt variable | NI count, frustration flag, call-later |
| D7 brevity + opening | value-first 1-liner / relationship opener / question-led | `initial_bot_message` variant | duration band, pickup ratio, engagement |
| D8 objection playbook + escalation | price-first / trust-first / time-first; escalate to exec when already-in-touch or DNC | playbook variable | past_objections, already_in_touch, do_not_call, NI count |

- ASSUMED **guarantee mechanism:** distinctness is a property of the mapping, not the LLM. If two sellers differ on a driving feature, they land on different levels on at least one *audible* dimension (D1–D3, D7). The LLM may not override levels; it only phrases them. "Similar data gives a similar persona" is built in, because identical feature vectors produce identical levels and differ only in personalisation slots (category, city).
- ASSUMED **voice spreading:** within each (gender, language) bucket, pre-pick 2–3 maximally different catalogue voices (descriptor tags "slow/measured" vs "fast/energetic" vs "warm/soft"). Assign them by rule, never at random. 89 Hindi-tagged voices leave room. The 3 Gujarati, 9 Marathi and 3 Tamil voices are a bottleneck for regional spread.
- ASSUMED: rough level product = 4×3×3×3×3×3×3 ≈ 2.9k combinations. With 285 populated feature cells we can avoid any single persona level-vector covering >~10% of sellers. Check that on the full sample.

### Gaps
- Real v4 pace/pitch ranges, and whether pitch is honoured, are unconfirmed in public docs. Run the T9 ear-and-meter test.
- Which seller files are the official PS04 "sample sellers" (all 149k or a subset) is unclear. "One spec for every sample seller" may mean a small set.
- No past-call evidence yet links voice gender or timbre to outcome. D1 is an informed guess until analysed; mark it lower confidence per FAQ Q6.

## Q3. Which distinctness metrics are defensible and easy to visualise?

### Takeaway
Lead with **attribute-level** metrics on the discrete grid: per-dimension entropy/coverage, distinct-persona ratio, and pairwise Hamming. Add a **Mantel correlation between seller-feature distance and persona distance** as the single "distinctness that tracks data" number. Back the demo with **audio-measured** pace, pitch and speaker-embedding distances. Use text embeddings only as a secondary "the prose isn't templated" check, because embedding similarity of specs is dominated by shared boilerplate.

### Cited Findings
- Population metrics used in the literature: coverage, uniformity, complexity ([Chameleon's Limit](https://arxiv.org/abs/2604.24698)); coverage, convex-hull volume, **min and average pairwise distance**, dispersion, KL to a uniform reference ([Persona Generators](https://arxiv.org/html/2602.03545v1)) — DOCUMENTED
- Near-duplicate threshold precedent: cosine > 0.9 or MinHash 0.9 counts as a duplicate — DOCUMENTED — [Persona Hub](https://arxiv.org/html/2406.20094v1)
- **Mantel test:** correlation between two pairwise distance matrices over the same objects. Significance comes from a permutation test that shuffles row/col identities together, because the n(n−1)/2 distances aren't independent. Distance measures may differ between the matrices. Python package `mantel` exists — DOCUMENTED — [Applied Multivariate Statistics (UW)](https://uw.pressbooks.pub/appliedmultivariatestatistics/chapter/mantel-test/); [PyPI mantel](https://pypi.org/project/mantel)
- DPP log-determinant is a set-diversity score (volume of the spanned vectors) — DOCUMENTED — [arXiv 2602.00885](https://arxiv.org/html/2602.00885v1)

### Inferences (metric set, all ASSUMED design; compute on all sample sellers)
1. **Per-dimension normalised entropy and coverage** (levels used / levels defined). One small bar per dimension D1–D8. Fail if any dimension has >80% of sellers on one level, unless the data itself is that skewed. Show the seller-feature entropy next to it (e.g. region 0.77).
2. **Distinct-persona ratio**: unique level-vectors / sellers, plus the **largest-cluster share**. Gives the "not one persona" headline number.
3. **Pairwise Hamming distance** over D1–D8 (0–8). Histogram, with mean and **min over seller pairs in different feature cells**. Target: zero pairs with different driving features but Hamming 0. Audible-dimension Hamming (D1–D3, D7) is shown separately.
4. **Fit-aligned distinctness = Mantel r** between seller-feature distance (Gower on turnover band, nature of business, region, engagement band, outcome history) and persona Hamming distance. Run 999 permutations. Positive, significant r means "different sellers get different personas, and similar ones get similar personas". This answers the noise objection directly. **Show the scatter/hexbin on one slide.** Also show the inverse check: same-cell sellers have mean Hamming ≈ 0–1 (only personalisation slots differ).
5. **Text-level check (secondary):** embedding cosine between spec prose (opening + playbook), with boilerplate and guardrail text removed. Report the share of different-cell pairs above 0.9 (Persona Hub's dup line). Expect high raw similarity from shared guardrails; don't headline it.
6. **Audio-level distinctness (demo sellers):** synthesize the same scenario line per persona and measure:
   - speaking rate (syllables or words per second from STT timestamps)
   - median F0 and F0 range (e.g. librosa pyin)
   - speaker-embedding cosine between voices (any open-source speaker-verification model)
   - Present as a 3-column table, or radar per seller. This also **verifies** that pace/pitch knobs actually changed the audio, which matters given the v3/v4 pitch ambiguity.
- One-slide visual (ASSUMED): left, a heatmap of sellers × D1–D8 levels sorted by feature cluster (block structure reads as "different but data-driven"); right, the Mantel scatter with r and p; bottom, an audio table for the 3 demo sellers.

### Gaps
- Mantel r size depends on the feature-distance choice. No benchmark exists for a "good" r here, so report r with its permutation p and say so.
- Audio metrics on 8 kHz telephony vs 24 kHz SDK audio may differ. Measure on the actual demo channel.
- No source found for measured-pitch accuracy of Bulbul v4.

## Q4. Can distinctness be part of the generator's improvement loop (multi-objective fit + diversity, GEPA-style Pareto)?

### Takeaway
Yes, as a **constraint or secondary objective with fit as primary**. Keep the Pareto front over (fit score, Mantel r / coverage), and reject any generator revision that raises fit but collapses distinctness. Don't optimise raw diversity; that rewards noise.

### Cited Findings
- GEPA keeps a **Pareto frontier of candidate prompts across task instances** (non-dominated per instance), reflects on trajectories in natural language, and mutates. It beats GRPO by 6% on average (up to 20%) with up to 35× fewer rollouts, and beats MIPROv2 by >10% — DOCUMENTED — [arXiv 2507.19457](https://arxiv.org/abs/2507.19457)
- QDAIF scores quality and the diversity attribute separately and keeps the best per cell — DOCUMENTED — [arXiv 2310.13032](https://arxiv.org/pdf/2310.13032)
- Persona Generators optimise the generator *code* against population diversity metrics with AlphaEvolve, and it generalised to held-out questionnaires — DOCUMENTED — [arXiv 2602.03545](https://arxiv.org/html/2602.03545v1)
- High per-item fidelity can co-occur with population collapse — DOCUMENTED — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698)

### Inferences
- ASSUMED loop: the candidate is a rules table plus a prose prompt. Score on the sample sellers:
  - **fit**: LLM-judge or rubric per spec, and agreement with past-call evidence (e.g. short-call sellers get brief openers)
  - **fit-aligned distinctness**: Mantel r, min per-dimension entropy, and largest-cluster share
  - Keep the Pareto set. Choose the final candidate as the best fit subject to r ≥ baseline and no dimension collapsed.
- ASSUMED guard: compute distinctness **only over rule-driven levels**. Text-embedding diversity is a guardrail ("not templated"), never a reward, or the LLM learns to vary wording randomly.
- ASSUMED hackathon-scale: one or two manual iterations with these metrics printed per run is enough. A full GEPA/AlphaEvolve loop is optional.

### Gaps
- No published example of GEPA with a population-level (set) objective. GEPA's Pareto is per-instance, so the set metric would be our addition.

## Q5. How do we choose the 2–3 demo sellers to maximise audible contrast while staying real sample sellers?

### Takeaway
Pick by **max-min (farthest-point) selection on the persona's audible dimensions**, restricted to real sellers whose files are complete (high-confidence specs) and to well-populated feature cells. Then confirm contrast with audio metrics. This reduces to a tiny DPP/max-min problem over real rows.

### Cited Findings
- Determinant/volume-maximising selection picks low-redundancy subsets — DOCUMENTED — [Determinantal Beam Search](https://ar5iv.labs.arxiv.org/html/2106.07400)
- PS04 requires the same scenario for 2–3 contrasting sellers, ≥1 live mid-call switch, and natural voice in ≥2 languages — DOCUMENTED — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Gujarati and Marathi have conversational v4 voices; Tamil does not — DOCUMENTED — [persona requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md). Catalogue Gujarati-tagged voices: 3; Marathi: 9 — PROVEN (catalogue count)
- Aggregate data: West sellers are 34% and Gujarat is the top state at 18%. Hindi belt is 52% — PROVEN (aggregate)

### Inferences (selection logic, ASSUMED)
1. Filter to sellers with non-missing turnover, nature of business, engagement and ≥1 past call outcome, so specs are high-confidence (FAQ Q6), and to feature cells with ≥50 sellers (representative, not outliers).
2. Compute the persona vector on audible dims: gender, voice timbre tag, language, pace level, opening/brevity style.
3. Greedy farthest-point: seed with the most populous cell's seller, then add the seller maximising the min distance to those already chosen. Constraints: at least 2 languages (e.g. Hindi-heavy Hinglish + Gujarati or Marathi), both genders, and pace spanning low and high levels.
4. Illustrative archetype contrast, not real sellers:
   - (A) micro trader-retailer in the Hindi belt, short calls, NI history → brisk, value-first, pace ~1.15, casual Hinglish
   - (B) larger manufacturer / Limited Company in the West, long calls → formal, relationship opener, pace ~0.9, measured male voice, Gujarati/Marathi
   - (C) call-later-heavy, low-pickup seller → warm female, empathetic, time-first playbook, mid pace
5. Verify with audio metrics (Q3 item 6). If the measured speaking-rate gap is under ~15% or the speaker-embedding cosine is high, swap a voice. Plant the live switch (rush or language) on seller A or B, where the swing is largest.
6. In the deck, state that demo sellers were chosen by a documented rule on aggregate feature cells, and show their position on the Mantel scatter, so judges see they aren't cherry-picked outliers.

### Gaps
- Whether organisers expect a specific set of "sample sellers" for the demo is unknown. Confirm on Day 1.

## Q6. Devil's advocate: over-engineering and out-of-scope risks

### Takeaway
The minimum winning version is **rules table → discrete levels → LLM prose → 3 metrics (entropy bars, distinct ratio, Mantel scatter) → audio table for 3 demo sellers**. MAP-Elites, DPP sampling and GEPA loops are mostly slideware here. They are also risky for "fit" if they push personas apart for diversity's sake.

### Cited Findings
- PS04 scores distinctness *across seller types* and explicitly allows grouping sellers into types to explain the logic. It does not ask for population-coverage optimisation — DOCUMENTED — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- A static personalised opening was tried 3 times at IndiaMART and none beat control — DOCUMENTED — [persona data validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md)
- Persona Generators and QDAIF optimise *coverage of a space*. PS04 needs a *function of seller data* — DOCUMENTED (contrast from [arXiv 2602.03545](https://arxiv.org/html/2602.03545v1), [arXiv 2310.13032](https://arxiv.org/pdf/2310.13032))
- Sparse evidence: free-text past objections exist for only 2.7% of sellers, and frustration flags for 139 — PROVEN (aggregate)

### Inferences
- ASSUMED risks:
  - **Manufactured distinctness.** Spreading voices to maximise coverage (MAP-Elites style) would give two near-identical sellers different voices with no data reason. That hurts fit (25%) and evidence (15%) to buy distinctness (20%). Always tie each level to a feature and a reason.
  - **Pitch as a distinctness lever** may be inaudible or unsupported on v4 (v3 docs: no pitch). Don't promise it until audio is measured.
  - **Voice dimension evidence is thin.** Gender and timbre choices are mostly informed guesses. Say so (PS04 §3.4 rewards honesty about evidence strength).
  - **Live switches can't change voice or pace** on Sarvam. Distinctness has to come mainly from pre-call voice/pace/language and the live tone/brevity directives. Don't market mid-call voice change.
  - **Time:** GEPA or AlphaEvolve loops on Day 1–2 compete with the live-switch build (25%). Budget at most a scripted metrics report.
  - **"All build work during the 2 days" / no pre-built solutions:** the metric scripts are small and should be written at the event.
  - **Data handling:** dashboards must show only aggregates and anonymised seller indices. Demo seller files are real, so avoid speaking real business names in recorded audio where possible (ASSUMED caution per AGENTS.md).
  - **Out of scope:** population-alignment to psychometric distributions (Big Five), creative-diversity benchmarks, and training/fine-tuning for diversity.

### Gaps
- No source quantifies how judges perceive "clearly different" audio. The ~15% speaking-rate threshold above is ASSUMED. It should be ear-tested by a non-tech team member.
