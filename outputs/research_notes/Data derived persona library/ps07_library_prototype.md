# PS07 data-derived persona library + rank-or-create: prototype results

As of 2026-10-09. **Aggregates only.** No seller names, ids, phone numbers, messages or transcript text were copied. Tags: **PROVEN** = computed this session on local PS07 data; **DOCUMENTED** = stated in a raw/ or earlier research note; **ASSUMED** = design inference.

**Sources used**
- [DATA] local, git-ignored `data/Persona Files/Persona Files/`: `ps07_bot_calls_*.csv` (269,455 answered calls, Apr–Sep 2026), `ps07_call_turns.csv` (11,834 transcribed calls with an outcome), `ps07_evaluator_outputs_*.csv` (disposition, objections, seller_questions agents), `ps07_seller_files_part1/2.csv` (149,363 sellers). Field meanings: [data dictionary](../../../raw/hackathon/2026-10-07-ps07-persona-data-dictionary.md).
- [LEX] signal labels come from the romanized-Hinglish keyword lexicon in [`app/validate/profile_persona.py`](../../../app/validate/profile_persona.py). `terse` means ≤3 seller words per turn; `english_heavy` means ≥50% English function words. Both are taken from [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md). The lexicon is a noisy proxy (kappa vs evaluator ≈ 0.03 per [ps07_replay_and_review.md](../Between%20run%20learning%20loops/ps07_replay_and_review.md)).
- [CODE] the scripts are in the session scratchpad `lib/`: `build_eval.py`, `feats.py`, `enc.py`, `select_k.py`, `select_k2.py`, `profile_k.py`, `main.py`. Python 3.12, pandas 3.0.6, scikit-learn 1.9.1 (already installed).
- Prior findings reused: [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md) [MEM], [ps07_replay_and_review.md](../Between%20run%20learning%20loops/ps07_replay_and_review.md) [REPLAY], [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md) [DIST].

**Set-up (leakage control).** Seller-file history columns cover all of Apr–Sep, so they leak the future. They were **not** used. All history was rebuilt from the call-level files.
- **Train:** for every seller with a call before 1 Aug, the *anchor* is the last call before 1 Aug. That gives 80,149 sellers: 24,018 "warm" (≥1 earlier call) and 56,131 "cold" (anchor was the first call).
- **Test (held out by time):** for every seller with an Aug–Sep call, the anchor is the latest call. That gives 66,360 sellers: 35,794 warm and 30,566 cold. 49,980 of them are not in train.
- Features come only from calls strictly **before** the anchor, plus static profile. Targets are the anchor call's outcome and its signals (when transcribed). The `eng_*` engagement fields are a single snapshot of unknown date. They may leak mildly, and they are used equally in the "profile" and "persona" models — ASSUMED risk.

---

## Q1. Can a per-seller feature table be built without leakage, and what does it contain?

### Takeaway
Yes. The table has profile, rebuilt call history, transcript signals and objection mix, all computed as of before the anchor. History and objections are available for most warm sellers. Transcript signals are available for very few: 2,771 of 80,149 train sellers (3.5%) and 5,159 of 66,360 test sellers (7.8%). So signal-defined personas can only ever be small.

### Cited Findings
- Feature blocks (PROVEN, [CODE] `feats.py`, `enc.py`):
  - **profile**: zone as a language proxy (Hindi belt / GJ / MH / East / Punjab / South-other / TN), turnover band, nature of business, business type, top-10 category group, engagement pickup ratio, enquiries, CQS
  - **history**: n prior calls, last outcome, outcome shares, short-call (≤30 s) share, average answered duration, days since last call
  - **objection mix**: share of prior evaluated calls in each objection family, mapped from `disposition`/`sub_disposition`/`objections` categories. Families: time/scheduling, no-need, already-engaged/trust, drop-after-identity, drop-mid-pitch, wrong contact, DNC.
  - **signals**: rush, terse, interest, English-heavy, regional, plus confusion, frustration and bot-question (lexicon OR `seller_questions` category Clarification / Frustrated User / AI Bot Confirmation)
- Coverage of evaluator tags: 57.7% of answered calls have at least one of the three evaluators parsed. Rates among evaluated calls: drop-after-identity 16.8%, time 13.1%, drop-mid-pitch 11.6%, no-need 11.4%, wrong contact 5.3%, already-engaged 3.5%, DNC 0.8% — PROVEN [DATA]
- History depth: 30% of train anchors and 53.9% of test anchors have ≥1 prior call. Prior evaluator history: 8.9% train vs 44.1% test. Prior transcript history: 1,628 train vs 4,631 test sellers. Evaluator and transcript coverage rose sharply in Jul–Sep, and this drift shows up again in Q4 — PROVEN [DATA]
- **Disposition label drift in September:** the Not Interested share was 49–57% per month Apr–Aug, then 19.1% in Sep. "General (talked)" went from 23.5% in Aug to 54.8% in Sep. MF stayed at 10–15%. This is a labelling-regime change, not seller behaviour — PROVEN [DATA]. NI results are therefore also reported on Aug-only test anchors (29,023).

### Inferences
- ASSUMED: any library fitted on Apr–Jul and applied on Aug–Sep sees two drifts: (a) richer observation of signals and objections, and (b) NI→General relabelling. Both must be monitored at runtime. Neither is a change in sellers.

### Gaps
- Signal labels are lexicon-based, not Jev or human labels.
- `eng_*` snapshot date unknown.

## Q2. Which personas does the data support (methods, K, sizes, definitions, rates)?

### Takeaway
Two populations need different treatment.
- **Cold sellers (no prior call):** profile alone has **no stable cluster structure**. Bootstrap ARI is 0.16–0.44 and silhouette ≤0.11 at every K tried.
- **Warm sellers:** a stable library exists. **K-means with K=7** gives bootstrap ARI 0.868 (min 0.816) and silhouette 0.271. The seven personas are organised mainly by last outcome and objection family, plus two small signal-defined personas (rush, confusion).

Turnover and zone hardly differ between warm personas: Hindi belt is 50–63% and <40 L turnover is 60–64% in every persona. So **language has to come from a separate rule, not from the clusters**.

### Cited Findings
**Method and K selection (all PROVEN, [CODE] `select_k.py`/`select_k2.py`; ARI = mean adjusted Rand between models fitted on two independent half/bootstrap samples, scored on all train sellers; silhouette on a 10K sample)**

| Run | Method | K | Silhouette | Bootstrap ARI (mean / min) | Notes |
|---|---|---|---|---|---|
| All train (warm + cold together), profile/hist/obj/sig weights 1/1/0.7/0.7 | k-means | 3–5 | 0.35–0.36 | 0.70–0.75 | One cluster holds **70%** (the cold sellers), so it just splits "has history" vs "not". Not actionable. |
| same | k-means | 6–14 | 0.10–0.12 | 0.39–0.56 | unstable |
| Cold only (profile block) | k-means | 3–12 | 0.065–0.112 | 0.16–0.44 | **no stable structure** |
| Cold only | GMM (diag, PCA-15) | 3–12 | <0 to −0.003 | 0.21–0.53 | unstable |
| Cold only | decision tree on outcomes | 3 | 0.138 | 1.00 | trivially stable 3-leaf split; 4–12 leaves 0.35–0.81 |
| Warm, final weights (hist 1.0, obj 1.0, sig 1.2, profile 0.5; z-scores clipped ±6; block-normalised) | **k-means** | 5 / 6 / **7** / 8 / 9 / 10 | 0.227 / 0.258 / **0.271** / 0.278 / 0.276 / 0.296 | 0.754 / 0.791 / **0.868 (0.816)** / 0.837 (0.781) / 0.826 / 0.768 | K=7 is the most stable |
| Warm, final weights | GMM (diag, PCA-15) | 5–10 | 0.175–0.240 | 0.535–0.852 (K=7: 0.751) | BIC keeps falling up to K=10 (−371K → −641K); no elbow |
| Warm, final weights | decision tree (multi-output on anchor MF/NI/CL/short, min leaf 400) | 5–10 | 0.032–0.086 | 0.52–0.86 | leaves are outcome-pure but not compact in feature space |
| Warm, earlier weights with missing-data flags | k-means | 8 | 0.155 | 0.748 | split "call-later with/without evaluator", a coverage artefact, so flags were dropped |

- The weights are a design choice (ASSUMED). Silhouette values are comparable only within a single weighting. A silhouette of about 0.27 means weak-to-moderate separation: the personas are dense regions of a continuum, not islands.

**Final warm library, K=7 (PROVEN, [CODE] `profile_k.py`, `main.py`). Sizes are train / held-out test assignment. Defining features are the means in each persona.**

| ID | Working name | Train n (%) | Test n (%) | Defining features (pre-anchor) |
|---|---|---|---|---|
| W0 | Call-me-later, engaged | 7,894 (32.9) | 5,717 (16.0) | last outcome Call Later 99%; median prior call 51 s; median gap 1.7 d; objection mix time/scheduling 80% |
| W1 | Short-call refuser | 7,626 (31.8) | 10,184 (28.5) | last NI 99%; short-call share 78%; median prior call 17 s; median gap 17 d; drop-after-identity 19% |
| W2 | Talked, no outcome | 5,244 (21.8) | 12,335 (34.5) | last General 99%; median gap 1 d; objections no-need 41%, already-engaged 23% |
| W3 | Meeting-fixed revisit | 1,694 (7.1) | 2,151 (6.0) | last MF 100%; median prior call 61 s; median gap 22 d |
| W4 | Mid-pitch dropper | 586 (2.4) | 3,819 (10.7) | drop-mid-pitch 90% of evaluated calls; last NI 77%; median 2 prior calls |
| W5 | Rusher | 524 (2.2) | 1,150 (3.2) | prior rush signal 95%; time objection 57%; prior interest 19%; last Call Later 64% |
| W6 | Confused | 450 (1.9) | 438 (1.2) | prior confusion signal 96%; frustration 7%; bot-question 6%; time objection 40% |

- Test-share shifts come from the drifts in Q1. W2 grew because of Sep "General" relabelling. W4 grew because evaluator coverage now reveals mid-pitch drops — PROVEN (counts) / ASSUMED (cause).

**Held-out (Aug–Sep) anchor-call rates by persona, 95% Wilson CI (PROVEN, `main.py`). Base rates are warm test.**

| Target | Base | W0 | W1 | W2 | W3 | W4 | W5 | W6 | χ² p |
|---|---|---|---|---|---|---|---|---|---|
| Meeting fixed | 11.3% | 13.4 [12.5,14.3] | 9.7 [9.2,10.3] | 7.1 [6.7,7.6] | **41.2 [39.1,43.3]** | 7.7 | 13.1 | 16.0 | ≈0 |
| Not interested | 34.1% | 36.9 | **56.2 [55.2,57.2]** | 16.0* | 20.6 | 35.6 | 39.5 | 33.1 | ≈0 |
| Call later/busy | 14.6% | **22.6 [21.6,23.7]** | 12.8 | 12.7 | 15.7 | 11.3 | 18.5 | 18.9 | 8.5e-86 |
| Short call ≤30 s | 64.4% | 54.2 | 68.3 | 70.7 | **30.0 [28.1,32.0]** | **73.0** | 55.6 | 46.8 | ≈0 |
| Terse (transcribed, n=1,288) | 25.1% | **16.4 [12.4,21.2]** n=269 | 28.7 n=425 | 25.7 | 24.2 | **36.7 [27.4,47.0]** n=90 | 22.7 | 16.7 n=18 | 1.6e-3 |
| Rush | 17.0% | 20.1 | 13.4 | 17.1 | 17.2 | 18.9 | 22.7 [14.3,34.2] n=66 | 22.2 | **0.25 (n.s.)** |
| English-heavy | 6.1% | 5.9 | 5.9 | 8.6 | 8.6 | **1.1** | 1.5 | 0.0 | 0.063 |
| Confusion | 6.7% | 6.3 | 4.9 | 8.2 | 5.5 | 4.4 | 13.6 [7.3,23.9] | **22.2 [9.0,45.2]** n=18 | 0.012 |
| Frustration | 6.1% | 4.5 | 6.6 | 7.2 | 3.1 | 3.3 | 9.1 | **27.8 [12.5,50.9]** n=18 | 1.9e-3 |
| Interest | 17.9% | 14.1 | 18.6 | 21.2 | 14.8 | 13.3 | **28.8 [19.3,40.6]** | 11.1 | 0.045 |

\*W2 NI is depressed by the Sep relabelling.

**Cold-seller profile clusters (k-means K=4, ARI ≤0.44, so unstable; listed for completeness), PROVEN:**
- C0: Limited Company (7.1%)
- C1: proprietorship with engagement data (42.7%)
- C2: proprietorship with no engagement data (38.0%)
- C3: partnership (12.3%)

**Implied persona settings and evidence strength.** The propensity numbers are PROVEN above. The mapping from propensity to setting is ASSUMED. That a setting *helps* is untested (GUESS) for every row.

| ID | Brevity | Pace | Simplicity | Opening style | Objection playbook order | Evidence for the underlying propensity |
|---|---|---|---|---|---|---|
| W0 | standard | 1.0 | normal | callback acknowledgement + time-box ("you asked us to call back…") | time/scheduling → no-need → wrong contact | **STRONG**: CL 22.6% vs 14.6%, n=5,717; time objection 80%. **MODERATE**: low terse (16% vs 25%, n=269). |
| W1 | short, value-first in first sentence | 1.0–1.1 | simple | value hook before company identity | drop-after-identity rescue → no-need → time | **STRONG**: NI 56% vs 34%, short 68%, n=10,184. Terse 28.7% is MODERATE/n.s. |
| W2 | standard | 1.0 | normal | recap of last conversation | no-need → already-engaged (acknowledge exec) → time | **MODERATE**: objection mix (n=1,781 evaluated). Outcomes distorted by label drift. |
| W3 | detailed allowed | 1.0 | normal | meeting recap/confirmation | logistics/visit → already-engaged | **STRONG**: MF 41.2% (3.6×), short 30%, n=2,151 |
| W4 | ultra-short, ask early | 1.1 | simple | direct ask before pitch | compress pitch → no-need | **MODERATE**: short 73%, n=3,819. Terse 36.7% (n=90, CI excludes base). Hindi-leaning (English 1.1%, n=90): WEAK. |
| W5 | short, time-boxed | 1.1 | normal | "2-minute" time-box, offer a slot | time → no-need | **WEAK** on held-out rush (n=66, n.s.). Prior [MEM] shows rush recurs 30.8% vs 20.8% (MODERATE). Interest 28.8% vs 17.9% (WEAK). |
| W6 | standard, slower | 0.9 | **high** (short sentences, repeat key point) | identity + purpose first | clarify → time | **WEAK**: n=18 transcribed. Confusion and frustration both higher (χ² p 0.012 / 0.002). |
| Cold | default | 1.0 | normal | standard intro | global order (drop-after-identity, time, no-need) | no persona evidence. Rely on rules and zone. |
| *All* | — | — | — | — | — | **Language:** from zone/state rule, not from the persona (see Q5). **Voice gender: no evidence.** One voice in PS07. |

### Inferences
- ASSUMED: the data-derived library is mostly a **"state" library** (what happened last time + objection family). Delivery **traits** (rush, terse, English, confusion) form only small personas because they are observed for <8% of sellers. The workable product is persona = state cluster + trait overlays (Beta-shrunk per seller, as in [MEM]) + language rule from zone.
- ASSUMED: K=7 balances stability (highest ARI) and actionability (every persona maps to a distinct opening/playbook). K=8 adds an "already-engaged" persona at ARI 0.837 if escalation-to-exec needs its own opening.

### Gaps
- GMM and tree segmentations were compared on stability and silhouette only. Their personas were not profiled in full.
- No k-prototypes package was installed. One-hot k-means with block weights stands in for it.

## Q3. Do personas differ on actionable delivery dimensions?

### Takeaway
On held-out data, yes for **brevity-relevant behaviour** (short call, terse) and **outcome-driven opening/playbook**: χ² p ≈ 0 for MF, NI, CL and short; terse p = 0.0016. Simplicity has weak, small-n support (confusion p = 0.012, frustration p = 0.002, driven by W5/W6 with n = 18–66). **Not** for rush/pace (p = 0.25) and only marginally for English-heavy (p = 0.063). The implied settings vectors differ pairwise on 2–5 of the 5 dimensions.

### Cited Findings
- χ² across the 7 warm personas on held-out anchors is in the Q2 table — PROVEN
- Settings-vector Hamming over (brevity, pace, simplicity, opening, playbook) from the Q2 settings table: minimum 2 (W0 vs W2: opening and playbook), maximum 5 (e.g. W3 vs W6). No two personas share a vector — PROVEN (by construction from the table; the mapping itself is ASSUMED)
- Zone mix is nearly flat across personas (Hindi 46–63%, GJ 13–26%), and so is turnover (<40 L 59–64%) — PROVEN. Data-driven personas therefore do not separate on language or size.

### Inferences
- ASSUMED: pace is the weakest data-backed dimension. A rush trait observed on a past call is better used as a per-seller overlay (pace 1.1 when rush posterior is high) than as a persona-wide setting.
- ASSUMED: the [DIST] grid (285 populated cells on 5 coarse features) and this K=7 library are complementary. The grid supplies profile/language distinctness; the library supplies outcome-history distinctness.

### Gaps
- No causal evidence that any setting change improves outcomes. All differences are correlational, from one PS07 voice/script.

## Q4. Rank-or-create: how many held-out sellers fit no persona, what do they look like, and is a new persona stable?

### Takeaway
With a novelty threshold at the 95th percentile of train nearest-centroid distances, **11.2% of held-out warm sellers (4,013)** are flagged "no good fit": 12.4% in Aug and 10.4% in Sep. Cold sellers flag 7.5% on profile distance. Misfits are mostly sellers with **richer observed history**: 64.8% have transcript or question signals vs 8.1% of fitting sellers. They look like new *observation*, not new kinds of seller. Re-clustering the misfit buffer gives a **stable K=4 split (bootstrap ARI 0.967, min 0.720)**. Two of those four centroids lie beyond the novelty threshold, so they qualify as new personas. Their outcome rates match the fitting sellers, and Aug-built vs Sep-built buffers agree only moderately (ARI 0.54).

### Cited Findings (all PROVEN, `main.py`)
- Nearest-centroid distance, train: p50 0.788, p95 **2.425**, p99 3.291. Test: p50 1.212, p95 2.832. There is a whole-distribution shift to the right.
- Flagged above p95: 11.2%; above p99: 2.0%. Flag rate by nearest persona: W0 7.4%, W1 9.1%, W2 12.5%, W3 8.1%, W4 6.5%, **W5 44.4%, W6 43.6%**. The small signal personas fit loosely.
- Ambiguous assignment (second-nearest centroid within 10%): test 26.1% vs train 7.2%.
- What misfits look like (test means, misfit vs fit):
  - terse history 0.31 vs 0.00
  - drop-after-identity 0.31 vs 0.12
  - interest 0.18 vs 0.00
  - English-heavy 0.07 vs 0.00
  - wrong-contact 0.11 vs 0.03
  - median prior calls 3 vs 2
  - evaluator history 98.7% vs 79.7%
- Share of misfit squared distance: terse 23%, drop-after-identity 19%, interest 13%, wrong-contact 7%, English 5%.
- Misfit outcomes vs fit: MF 9.9% vs 11.4%, NI 35.4% vs 33.9%, CL 14.5% vs 14.6%, short 65.3% vs 64.3%.
- Re-clustering the buffer (n = 4,013):
  - K=2: ARI 0.846
  - K=3: ARI 0.771
  - **K=4: ARI 0.967**. Centroid distances to the existing library: 2.27, 2.74, 2.74, 1.34 (threshold 2.42).
  - K=5: ARI 0.875
- K=4 new clusters:
  - (a) **identity-droppers**, n = 983: drop-after-identity 86%, TN 10% (+1.4 sd), short 89%. Outcomes MF 5.9%, short 78%.
  - (b) **terse repeat callers**, n = 1,271: terse 96%, more prior calls. NI 40%.
  - (c) **interested-but-rushed**, n = 698: interest 94%, rush 31%, frustration 11%, bot-question 10%. MF 12.6%.
  - (d) **wrong-contact / English / regional**, n = 1,061: wrong contact 30%, English 17%, regional 5%, DNC 4%. CL 20%.
- Temporal stability of the new personas: K=3 fitted on Aug misfits vs K=3 fitted on Sep misfits gives ARI 0.540 on the Sep misfits (n Aug 1,772, Sep 2,241).

### Inferences
- ASSUMED: rank-or-create works mechanically, and the "create" step finds a stable, interpretable buffer. In PS07, though, most novelty is caused by **coverage drift**: train had little signal/evaluator history, so the library never learned trait-rich sellers. The right operational rule is: create a persona only when the buffer cluster is (i) stable across two time windows (ARI ≥ ~0.7, not met here at 0.54), (ii) beyond the novelty threshold, and (iii) different on at least one delivery-relevant rate. As a cheaper first step, refit the library periodically on the newest data.
- ASSUMED: the identity-dropper and terse-repeater clusters are the best candidates for promotion, because they map to clear delivery changes (value-before-identity opening; ultra-short turns).

### Gaps
- The new clusters' held-out delivery-signal rates were not measured on a later window (no data after Sep).
- The p95 threshold is a convention. A different quantile changes the flag rate (p99 → 2.0%).

## Q5. Does persona membership predict the next call better than profile-only?

### Takeaway
Yes for outcomes and call length. Training on Apr–Jul anchors and testing on Aug–Sep, persona one-hot (7 warm + 4 cold labels) beats profile-only on every outcome AUC and gets close to the full-feature upper bound:
- MF: 0.677 vs 0.595 (full 0.690)
- NI: 0.618 vs 0.555; Aug-only 0.627 vs 0.584
- short call: 0.645 vs 0.573
- CL: 0.549 vs 0.531

For in-call signals it does **not**:
- English-heavy is predicted by **profile** (0.682) far better than persona (0.539), which confirms that language should come from a profile rule.
- Rush, terse, confusion and interest are near chance for every model (0.52–0.58). Frustration is the exception: persona 0.626 vs profile 0.575, with overlapping CIs.

### Cited Findings (PROVEN, `main.py`; logistic regression C=0.5; AUC with bootstrap 95% CI; outcome n_train 80,149 / n_test 66,360; signal targets on transcribed anchors, n_train 3,239 / n_test 3,226)

| Target (test base) | Profile | Persona | Profile + persona | Full features | Warm-only: profile / persona / full |
|---|---|---|---|---|---|
| Meeting fixed (17.8%) | 0.595 [0.590,0.600] | **0.677 [0.673,0.682]** | 0.685 | 0.690 | 0.561 / 0.646 / 0.681 |
| Not interested (32.0%) | 0.555 | **0.618** | 0.627 | 0.648 | 0.525 / 0.697 / 0.691 |
| NI, Aug only (47.2%) | 0.584 | **0.627** | 0.651 | 0.666 | 0.551 / 0.689 / 0.686 |
| Call later (13.9%) | 0.531 | 0.549 | 0.562 | 0.582 | 0.520 / 0.568 / 0.606 |
| Short ≤30 s (54.9%) | 0.573 | **0.645** | 0.653 | 0.672 | 0.548 / 0.598 / 0.669 |
| Rush (17.7%) | 0.542 | 0.530 | 0.539 | 0.525 | — |
| Terse (25.3%) | 0.539 | 0.534 | 0.555 | 0.564 | 0.530 / 0.578 / 0.596 |
| English-heavy (7.5%) | **0.682 [0.636,0.720]** | 0.539 | 0.667 | 0.676 | 0.669 / 0.517 / 0.662 |
| Confusion (6.6%) | 0.568 | 0.550 | 0.583 | 0.571 | — |
| Frustration (3.9%) | 0.575 | 0.626 [0.574,0.669] | 0.630 | 0.660 | — |
| Interest (16.9%) | 0.576 | 0.520 | 0.563 | 0.571 | — |

- Consistent with [MEM]: on consecutive-call pairs, the previous call predicts meeting at AUC 0.71 vs 0.58 for profile, and NI at 0.78 vs 0.54 — DOCUMENTED. Persona labels keep most, but not all, of that signal.

### Inferences
- ASSUMED: a persona label compresses history well enough for outcome expectations, at about −0.01 to −0.03 AUC vs full features. It does **not** forecast in-call delivery signals, so live adaptation (Jev/lexicon) stays necessary.
- ASSUMED: the persona model gets part of its lift from the warm/cold split itself, i.e. whether the seller has been called before.

### Gaps
- Signal-target n is small (3.2K per side), and the labels are lexicon-based.
- The decision-tree segmentation was not scored on AUC.

## Q6. Runtime: how fast is assignment at scale?

### Takeaway
Assignment is trivial at scale. Encoding plus nearest-centroid takes **0.36 s per 1 lakh rows** on this laptop, single process. **12 lakh rows measured end to end: 4.19 s**, against 4.3 s extrapolated.

### Cited Findings
- 1 lakh synthetic rows (resampled from test features): encode 0.33 s, nearest-centroid 0.032 s — PROVEN, `main.py`
- 12 lakh rows: encode 3.73 s, assign 0.46 s in 2-lakh chunks — PROVEN

### Inferences
- ASSUMED: feature building from raw call logs, which is a groupby over all calls, will dominate production cost, not assignment. Re-clustering (k-means K=7 on ~24K rows) takes seconds, so a nightly refit is cheap.

### Gaps
- No timing of the upstream feature build on a 12-lakh seller base, and no timing on server hardware.

## Limits (apply to every number above)
- **One voice, one script family in PS07.** All rates are propensities under the existing bot. None shows that a different setting would help — correlational only. Bot-version assignment is non-random ([MEM]: 97% of Tamil Nadu on arrowhead).
- **Transcripts cover only ~12.8K calls** (11,834 with outcome, Jul–Sep only, biased toward engaged calls: 22.4% MF vs 11.5% overall, [REPLAY]). Signal personas W5/W6 and all signal AUCs rest on small n.
- **Label drift**: Sep NI→General relabelling (Q1), and evaluator/transcript coverage grew over time (Q1, Q4).
- **Lexicon labels** are noisy proxies (kappa ≈ 0.03 vs evaluator, [REPLAY]).
- Personas come from a weighted one-hot k-means; the weights were chosen by the analyst (ASSUMED) and change the silhouette and the clusters.
