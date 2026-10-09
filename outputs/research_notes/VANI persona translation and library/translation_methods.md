# Translating seller data and seller state into VANI's persona (voice, pace, formality, warmth, brevity, language mix, plan)

As of 2026-10-09. No customer data; PS07 numbers are aggregates already in [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md) [MEM] and [ps07_library_prototype.md](../Data%20derived%20persona%20library/ps07_library_prototype.md) [LIB].
Tags: **DOCUMENTED** = published source (URL given) · **PROVEN** = our PS07 aggregate · **ASSUMED** = our inference or design · **BACKGROUND** = well-known practitioner or theory content I did not re-fetch this session (treat as unverified).
Binding framing: "persona" means **VANI's** persona. Seller data and state are the **input** ([PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)). Platform constraint from [MEM]: voice and pace are fixed per call (Sarvam). Wording, brevity, tone, language and plan can switch live, and the plan is re-sent each turn.

---

## 1. Theory and expert methods: how practitioners turn "customer is X" into "agent does Y"

### Takeaway
The theory gives clear **directions**: converge on rate, register and language mix; cut effort for time-poor people; simplify and chunk for confused people; use moderate pace with natural pauses. It also gives a clear **warning**: accommodation helps only when it is subtle and in the right feature. Over-accommodation, obvious mimicry, or convergence on the wrong feature backfires, and effects found between humans often fail to replicate with agents. Expert playbooks are condition→action tables built from theory and top-performer observation. They are rarely validated causally.

### Cited Findings
**Communication Accommodation Theory (CAT) and entrainment**
- CAT (Giles 1973; Giles, Coupland & Coupland 1991): speakers **converge** toward a partner to gain approval and make the exchange work, or **diverge** to mark distance. Over-accommodation (for example over-simplifying to older listeners) is a recognised miscommunication — [Giles, Coupland & Coupland, "Accommodation theory" chapter (PDF)](https://people.cs.pitt.edu/%7Elitman/courses/cs3710/gilescouplandcoupland.pdf); summarised in [Frontiers in Comp. Sci. 2023](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2023.1204211/pdf) — DOCUMENTED
- Speech-rate convergence is weaker than early CAT claimed. Some studies find perceptual convergence but none on rate. Others find rate convergence at session level that falls below significance when measured turn by turn — [Schweitzer & Walsh 2016](https://www.ims.uni-stuttgart.de/documents/team/schweitz/docs/SchweitzerWalsh2016.pdf) (via search summary) — DOCUMENTED
- Voice systems "speak in exactly the same manner to all users", which leaves a human–computer accommodation gap — [Raveh et al., Interspeech 2019](https://www.coli.uni-saarland.de/~moebius/documents/raveh_etal_is2019.pdf); [Raveh PhD 2021](https://publikationen.sulb.uni-saarland.de/bitstream/20.500.11880/31960/3/PhD_Dissertation_Eran_Raveh.pdf) — DOCUMENTED
- Users adapt their own speaking rate to a system's rate without noticing (16-subject experiment) — [KTH, ICPhS 2003](https://www.speech.kth.se/~jocke/publications/ICPhS03.pdf) (via search summary) — DOCUMENTED. Implication: VANI's pace also *drives* the seller's pace, not only follows it.
- Entrainment's effect on trust **depends on the feature, the language and the voice**. In English, users trusted a male avatar that entrained on intensity and rate more than a random-variation baseline. In Spanish and Slovak, a female avatar entraining *only on rate* was trusted slightly *less* than a disentraining baseline — [Levitan, Columbia thesis](https://www.cs.columbia.edu/speech/ThesisFiles/rivka_levitan.pdf); [Levitan et al. NSF PAR](https://par.nsf.gov/servlets/purl/10213787) — DOCUMENTED
- Users change their speech rate with an Alexa socialbot as well — [Frontiers in Communication 2021](https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2021.671429/pdf) — DOCUMENTED (rate details not extracted)

**Linguistic style matching (LSM)**
- In 9 hostage negotiations, success was associated with higher aggregate LSM. The driver was **stability**: unsuccessful negotiations showed large swings in LSM. Successful ones had more coordinated turn-taking, reciprocated positive affect, a present-focus and talk of alternatives — [Taylor & Thomas 2008, NCMR](https://ncmr.lps.library.cmu.edu/article/id/93/); [Lancaster eprint](https://eprints.lancs.ac.uk/id/eprint/26912) — DOCUMENTED (n=9, correlational). Implication: keep a stable, matched style rather than oscillating. This supports hysteresis on live switches (ASSUMED).

**Mimicry limits**
- Subtle mimicry helps interpersonal outcomes; too much backfires. Several human–human mimicry benefits **did not replicate** with virtual agents — [EGVE 2023, "Subtle Mimicry in Human-Agent Interaction"](https://diglib.eg.org/items/70e4bdde-687a-46c9-9cb7-9ffc92b4bb70/full) — DOCUMENTED
- Voicebots with non-standard accents get anthropomorphised and can be preferred. The effect disappears when the bot also has dehumanising cues, when the human wait is short, or when users dislike AI — [EMAC 2025 proceedings](https://proceedings.emac-online.org/pdfs/A2025-124238.pdf) — DOCUMENTED
- Commercial accent "neutralisation/matching" is criticised as accentism — [UBC News, May 2026](https://news.ubc.ca/2026/05/accentism-for-profit-what-telus-is-getting-wrong-about-accents/) — DOCUMENTED (opinion piece)

**Hinglish code-switching accommodation (most directly relevant)**
- In a Wizard-of-Oz Hindi–English chatbot study, bilingual users preferred bots that code-switch, and preferred bots that **mimicked their own code-switching pattern**. Among users with a positive attitude to code-mixing, ratings correlated with how natural the code-switching was and how accommodating the bot was — search summary of Bawa et al. (CSCW 2020) via [UW sociolab](https://depts.washington.edu/sociolab/labmembers/documents/eahn_sociolab_201030.pdf) and [NSF PAR](https://par.nsf.gov/servlets/purl/10379220) — DOCUMENTED (secondary summary; primary not fetched)
- CommonDost: 439 Hindi–English human–machine conversations under different agent code-switching strategies, built to measure how users accommodate *to the agent* — [Parekh, Ahn, Tsvetkov, Black, CoNLL 2020](https://aclanthology.org/2020.conll-1.46) — DOCUMENTED (strategy-level numbers not on the abstract page)
- Code-switching works as a style marker with social meaning; survey for language technologies — [Doğruöz et al., arXiv 2301.01967](https://arxiv.org/pdf/2301.01967) — DOCUMENTED

**Prosody and compliance on phone calls**
- In 1,380 survey-introduction calls by 100 interviewers, a moderately fast rate (**~3.5 words/s**) won the most agreement. Very fast and very slow both did worse. Frequent short pauses beat perfectly fluent delivery ("too scripted"). Deeper male voices helped, but pitch made no difference for female interviewers — [U. Michigan news, 2011 (Benki, Conrad et al.)](https://news.umich.edu/persuasive-speech-the-way-we-um-talk-sways-our-listeners) — DOCUMENTED. This is a US English survey context, not an Indian B2B one.
- "Speed of Speech and Persuasion: Evidence for Multiple Effects" (Smith & Shaffer 1995): rate affects persuasion through more than one route — [record](https://scholarhub.vn/publication/Speed-of-Speech-and-Persuasion-Evidence-for-Multiple-Effects/d70dd17b-51bb-4d0d-a6ce-d40067433c42) — DOCUMENTED (title and record only)

**Cognitive load and plain language for confused users**
- A dialog system for seniors adds pauses to slow speech, gives information step by step, and confirms understanding — [CMU GetGoing, arXiv 1909.01322](https://arxiv.org/pdf/1909.01322) — DOCUMENTED
- Slow speech is **not** reliably better. It helped only listeners with well-preserved working memory, did nothing for moderate impairment, and *hurt* those with severe impairment. "Clear speech" (slower, more pauses, enhanced acoustics) improved learning and memory of medical instructions — [Frontiers in Psychology 2023](https://www.frontiersin.org/articles/10.3389/fpsyg.2023.1119355) — DOCUMENTED
- Slower speech plus segmented responses improved chatbot performance compared with dense one-shot delivery (preliminary) — [ACIS 2025](https://aisel.aisnet.org/acis2025/275) — DOCUMENTED (preliminary)

**Time-poor customers and effort**
- *The Effortless Experience* (CEB, 97,000 customers): exceeding expectations has almost no relationship with loyalty, while reducing effort does. Low-effort service was 31% more likely to win repeat business — [Salesforce summary](https://www.salesforce.com/ca/blog/making-effortless-customer-service-a-reality/); [book summary](https://pulserevops.com/knowledge/bs0124) — DOCUMENTED (secondary)

**Users already talk differently to bots**
- Users are 14.5% more polite and formal and 5.3% more grammatically fluent with human agents than with LLM assistants. Training on stylistically diverse data beat inference-time reformulation of user messages — [Zhang & Yu (Amazon), arXiv 2510.02645](https://arxiv.org/html/2510.02645v1) — DOCUMENTED. Implication: a seller's terseness toward VANI is partly a *bot-directed* register, not a fixed personal trait (ASSUMED).

### Inferences
- **Playbook format practitioners use** (BACKGROUND + ASSUMED): `IF observable cue (words, rate, interruptions, "busy", "kya?") THEN delivery move (shorten, slow, re-explain, switch language, offer callback) + plan move (skip discovery, jump to ask, schedule)`. Each row is justified by a principle: CAT for rate and language, effort for rush, cognitive load for confusion, politeness for formality.
- **Politeness theory** (Brown & Levinson; BACKGROUND, not fetched): face-threatening acts such as asking for a meeting need redress. Redress costs words, and time-poor sellers penalise words. So for rushed sellers, keep one short polite token ("ji", "sorry for disturbing") and drop elaborate hedges. For first contact and older or formal sellers, keep the negative-politeness formality.
- **Sales methods** (BACKGROUND): SPIN (Rackham) uses Situation → Problem → Implication → Need-payoff questions, from studies of large sales. Challenger (CEB) is teach–tailor–take control. Consultative selling is listen-first. Gong's call analytics put top performers at about a **43:57 talk:listen** ratio against a 60:40 average; reps who talk more than 65% convert worse; winners ask about 15–16 questions against about 20 for losers — [Gong Labs](https://www.gong.io/resources/labs/talk-to-listen-conversion-ratio/) (DOCUMENTED, vendor, correlational, US B2B). For VANI's 30–60 s outbound calls, SPIN-depth discovery does not fit. A cut-down "one situation question → one need-payoff" plan fits better (ASSUMED).
- **Hinglish (ASSUMED from the DOCUMENTED preference result):** match the seller's *mix ratio* (more English if they use more English), but do **not** imitate regional accent or dialect markers. Accent mimicry carries the over-accommodation and accentism risks above.

### Gaps
- No primary source fetched for SPIN, Challenger or Brown & Levinson. Their content is BACKGROUND.
- No study found of rate or formality accommodation in **Indian B2B phone calls** or with Indian-language TTS.
- Bawa et al. effect sizes not extracted (primary not fetched).

---

## 2. Data-driven methods: learning the translation from outcomes

### Takeaway
Industry learns "which style works for which customer" in three ways. (a) **Mining top human performers' behaviour** against KPIs, as Cresta, Gong and Observe.AI do. (b) **Pairing or uplift on randomised assignment**, as Afiniti does. (c) **Bandits or RL over strategies**, which is research-stage for LLM dialogue. All three need **variation in the treatment**: different agents or styles across comparable customers. PS07 has one VANI style (87.4% of consecutive same-seller calls used the same bot version, PROVEN [MEM]), so none of them can be run on PS07 for VANI's style. They are a roadmap, not a hackathon result.

### Cited Findings
- **Cresta Behavior Discovery** uses LLMs to find behaviours in unstructured conversations that correlate with KPIs or with known top performers, "situationally-specific best practices", then coaches agents in real time. Vendor claim: agents who follow the behaviours earn 2.1× more revenue and convert 1.8× better; one telecom reported a 300% sales lift — [Cresta blog](https://cresta.com/blog/4-sales-behaviors-proven-to-increase-revenue-and-drive-conversions); [Cresta solution page](https://cresta.com/?p=26431) — DOCUMENTED (vendor, selection bias: good agents both follow the behaviours and sell more)
- **Gong**, 326K B2B calls: 43:57 talk:listen in top performers — [Gong Labs](https://www.gong.io/blog/talk-to-listen-conversion-ratio) — DOCUMENTED (vendor, correlational)
- **Brynjolfsson, Li & Raymond** (NBER w31161), 5,179 support agents with staggered roll-out of an AI assistant trained on top agents' conversations: +14% issues resolved per hour, +34% for novices, almost nothing for experts; customer sentiment improved. Suggestive evidence that the AI spreads top workers' practices — [NBER](https://www.nber.org/papers/w31161); [arXiv 2304.11771](https://arxiv.org/abs/2304.11771v1) — DOCUMENTED (quasi-experimental). This is the best peer-reviewed evidence that "copy what top agents do" transfers.
- **Afiniti behavioural pairing**: matches each customer to an agent by predicted pair outcome, and measures lift by cycling the pairing on and off (benchmarking patents). Afiniti says it is "validated through rigorous randomized testing" — [Afiniti](https://www.afiniti.com/?p=18902); [patent US9692899, benchmarking pairing strategies](https://patents.google.com/patent/US9692899); [US9888121, model evaluation](https://patents.google.com/patent/US9888121) — DOCUMENTED. **No peer-reviewed RCT found** (see Gaps). The design lesson is the **ON/OFF interleaving** used to measure lift. VANI can do the same between "adaptive persona" and "default persona" calls.
- **Contextual bandits + LLM**: a bandit picks which value or message frame to target from user demographics, and the LLM writes the message. The bandit is the interpretable, expert-adjustable part — [arXiv 2410.23371 (EV adoption)](https://arxiv.org/pdf/2410.23371) — DOCUMENTED
- Personality-aware RL for persuasion: estimates user state turn by turn and conditions a DQN policy on it. Q-learning strategy selection for high-stakes dialogue. Conversational-sales agents with simulators grounded in behavioural data — [arXiv 2601.06877](https://arxiv.org/html/2601.06877v1); [papers.cool 2504.08754](https://papers.cool/arxiv/2504.08754); [arXiv 2607.01557](https://arxiv.org/abs/2607.01557) — DOCUMENTED (search summaries; simulation-evaluated)
- **Affect-adaptive spoken dialogue** (foundational): a tutoring SDS that detected and adapted to disengagement and uncertainty raised motivation, task success and satisfaction compared with non-adaptive baselines (Forbes-Riley & Litman) — [SIGDIAL 2012 talk](https://www.superlectures.com/sigdial2012/adapting-to-multiple-affective-states-in-spoken-dialogue); [paperswithcode](https://paperswithcode.com/paper/evaluating-a-spoken-dialogue-system-that) — DOCUMENTED. An affect-sensitive domotic agent reduced frustration and improved satisfaction — [Sensors 2013, PMC3812615](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812615/) — DOCUMENTED
- **LLM style drift**: LLM chatbots shift Agreeableness, Extraversion and Conscientiousness toward simulated user personas over a conversation. Emotional Stability and Intellect stay stable — [Xing, Niu, Srivastava, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.875/) — DOCUMENTED. Risk: an LLM agent "accommodates" without being told, so the persona spec must pin the settings.
- Off-policy evaluation needs overlap. PS07 lacks it — [MEM Q3](../Between%20run%20learning%20loops/persona_learning.md) citing [arXiv 2505.00961](https://arxiv.org/html/2505.00961v3) — DOCUMENTED / PROVEN

### Inferences
- **What we can mine from PS07 now (ASSUMED method, PROVEN data availability):** PS07 cannot show *VANI* styles that work. It can show *seller-side* moments that preceded good or bad outcomes, for example "turn where seller said busy → bot continued pitching → hang-up" against "→ bot offered slot → Call Later". That is a Cresta-style behaviour mine over **bot moves inside the single script**. Bot moves vary across calls even within one bot version (scripted branches, LLM wording), so there is *some* within-script treatment variation. Confounding is heavy: good sellers get good branches.
- **Production path (ASSUMED):** (1) launch the rule table in §4 as policy v0; (2) Afiniti-style interleaving, randomising a small share (5–10%) of calls to the default persona to measure lift per segment; (3) a contextual bandit over 3–4 discrete style arms per trait cell, context = pre-call prior, reward = meeting or callback with a guardrail on hang-up ≤30 s. At 12 lakh sellers that gives enough volume per arm within weeks. Nothing here is feasible in the 2-day hackathon. Present it as the roadmap.
- **Top-human-agent mining** (Brynjolfsson-style) is the fastest real-world source of priors *if* IndiaMART tele-sales human call recordings exist with outcomes. Internal data, allowed by AGENTS.md.

### Gaps
- No peer-reviewed or independently audited Afiniti RCT found. Only vendor claims and patents.
- Cresta and Gong lifts are vendor-reported and correlational. Observe.AI not checked.
- No 2024–2026 paper found that tests affect-adaptive **TTS prosody** in a sales call with an outcome metric.

---

## 3. Trait vs state: combining a pre-call prior with live detection

### Takeaway
Treat each delivery dimension as a probability: **prior from history (trait, Beta-shrunk) + recency-weighted state → pre-call settings; live evidence updates it; the switch threshold falls as the prior rises**. Voice and pace can't change mid-call, so the pre-call choice should be a **robust default** for the uncertain middle range. Strong priors should change only *cheap-to-reverse* things: the plan's contingency branches, live thresholds and the opening line. Most of the evidence for this design is our PS07 recurrence data plus decision-theory arithmetic. I found no published study of this exact pattern in voice agents.

### Cited Findings
- Recurrence: rush 30.8% vs 20.8% base; terse 41.0% vs 17.8%; English-heavy 13.8% vs 4.3%; confusion 25.0% vs 7.0% (34.3% vs 7.7% at ≤3 d, 14.3% vs 5.5% at 4–30 d); NI repeats 67.1% vs 41.1%, decaying to base by >45 d (half-life ≈ 20 d) — PROVEN [MEM]
- Rush, terse and English-heavy recur at every gap length (trait-like). Confusion is short-term (state-like) — PROVEN [MEM], small n (35–276)
- Pre-call prediction of in-call signals is weak: AUC 0.52–0.58 for rush, terse, confusion and interest. English-heavy from **profile** reaches 0.68 — PROVEN [LIB]
- Prior rush carries no outcome penalty (next meeting 14.1% vs 15.0%). Prior frustration and bot-question do (5.1% and 5.7% vs ~15%) — PROVEN [MEM]
- Users entrain to the system's speech rate without noticing — [KTH ICPhS 2003](https://www.speech.kth.se/~jocke/publications/ICPhS03.pdf) — DOCUMENTED. A brisk-but-moderate default therefore pulls slower sellers along somewhat (ASSUMED).
- LSM stability beats oscillation — [Taylor & Thomas 2008](https://ncmr.lps.library.cmu.edu/article/id/93/) — DOCUMENTED → hysteresis
- Users talk to bots more tersely and less politely than to humans — [arXiv 2510.02645](https://arxiv.org/html/2510.02645v1) — DOCUMENTED → part of "terse" is register, not trait

### Inferences (design; ASSUMED unless noted)
1. **Prior per dimension** `p_trait = (k + α·m_seg) / (n + α)` with segment mean `m_seg` and α≈4–10 (from [MEM]). **State weight** `w = exp(−gap/28 d)` for confusion, NI, frustration and callback. Combined prior `p0 = p_trait` for trait-type signals; `p0 = base + w·(p_last − base)` for state-type signals.
2. **Pre-call setting rule (robust default):** voice and pace are irreversible within a call, so move them only when `p0` is high *and* the cost of a mismatch is low. A pace of 1.05–1.1 for a non-rushed seller costs little, because ~3.5 w/s is optimal anyway (DOCUMENTED Michigan). Pace 0.9 for a rushed seller costs a lot (effort, DOCUMENTED CEB). **Asymmetry:** lean pace slightly brisk by default, and never slow the base pace on a confusion prior. Handle confusion with *wording* (shorter sentences, repetition, pauses through punctuation), which can switch live. This also follows the Frontiers 2023 finding that slow rate is not reliably better.
3. **Threshold lowering:** with a calibrated live detector score s, switch when posterior `P(state | s, p0) > τ`. Bayes gives `posterior odds = prior odds × LR(s)`, so a seller with p0 = 0.31 (prior rush) needs a likelihood ratio about 1.7× smaller than a base-rate seller (p0 = 0.21) to reach the same posterior. Practical form: **1 cue triggers crisp mode when the prior is high; 2 cues are needed at base rate** (for example "busy hoon" once vs "busy" + a 2-word reply). The decision-theoretic τ is `cost(false switch) / (cost(false switch) + cost(missed switch))`. Missing a rush means a hang-up; a false crisp switch only means slightly short turns. So τ_rush should be low (~0.35–0.4). τ for an *English* switch should be higher (~0.6), because a wrong language switch is jarring.
4. **Contingency plans in the call plan** (re-sent each turn, so cheap): every plan carries pre-written branches `on_rush: [one-line value + slot offer]`, `on_confusion: [re-state identity + purpose in ≤8 words, ask yes/no]`, `on_english: [switch to English-leaning Hinglish]`. Prior-high branches are **promoted**: for example, the opening already contains the time-box ("2 minute"). Low-prior branches stay dormant.
5. **Hysteresis / no ping-pong:** once crisp, stay crisp unless ≥2 turns of long, engaged answers (LSM-stability argument). Language: switch at most once per call unless the seller switches back explicitly.
6. **Decay:** state priors decay (τ≈28 d, PROVEN fit on NI). Trait priors don't decay but are shrunk, and any newer contradicting observation supersedes language preference (from [MEM]).
7. **Live evidence wins over the prior** within the call. The prior only sets the starting point and thresholds. Never refuse to switch *back* because "the prior says rushed".

### Gaps
- No published system found that documents prior-dependent switch thresholds for voice agents. The design rests on Bayes arithmetic and our data.
- Detector likelihood ratios are unmeasured. The lexicon's κ vs the evaluator is ≈0.03 ([LIB]), so LRs must be estimated on Jev labels before the thresholds mean anything.
- No evidence that crisp mode *improves* outcomes for rushed sellers in VANI's setting. Prior rush has no outcome penalty under the current single style.

---

## 4. Translation table proposal for VANI

Columns: pre-call settings (voice/pace/language start are irreversible per call) · plan contingencies (in the re-sent plan) · live-switch adjustments · evidence. "Default" = Hinglish (zone-based), mid formality, mid warmth, standard brevity, pace 1.0–1.05, female or male voice per default (**voice gender: no evidence**, PS07 had one voice [LIB]).

| Seller trait/state (input) | Pre-call persona settings | Plan contingencies | Live-switch adjustments | Evidence |
|---|---|---|---|---|
| **High rush propensity** (prior rush, trait-like) | pace 1.1; brevity short; warmth mid (one courtesy token, no small talk); opening with time-box "2 minute ka kaam hai" | value-first in sentence 1; ask early; `on_rush` → one-line value + offer slot/callback; drop SPIN discovery | lower rush threshold (1 cue); crisp mode stays (hysteresis); if seller then elaborates ≥2 turns → relax | recurrence 30.8 vs 20.8% PROVEN (n=276); effort reduction DOCUMENTED (CEB); ~3.5 w/s optimum DOCUMENTED (Michigan, US); that crisp helps VANI: **ASSUMED** |
| **High confusion propensity** (≤30 d, state-like) | pace **unchanged** 1.0 (not slower); formality low, plain Hindi/Hinglish; warmth high; short sentences | identity + purpose first ("IndiaMART se, aapke buyer enquiries ke liye"); one idea per turn; confirm-understanding yes/no step; repeat key point | lower confusion threshold; `on_confusion` re-explain in ≤8 words, no jargon ("BuyLead" → "kharidaar ki enquiry"); never repeat the same sentence verbatim | recurrence 25 vs 7% PROVEN (n=68), decays (state); chunking + confirmation DOCUMENTED (GetGoing, ACIS 2025); slow rate not reliably helpful DOCUMENTED (Frontiers 2023); mapping ASSUMED |
| **Terse** (≤3 words/turn history) | brevity short; closed or choice questions ("haan/na", "kal ya parson?"); pace 1.05 | skip open discovery; binary-choice ask | treat short answers as normal (don't trigger "disengaged"); if seller opens up → expand | recurrence 41 vs 17.8% PROVEN (n=183); partly bot-directed register DOCUMENTED (Zhang & Yu 2025); terse held-out higher in W4 PROVEN [LIB]; mapping ASSUMED |
| **English-heavy** | language start English-leaning Hinglish (more English nouns/verbs, Hindi glue); formality mid-high | — | switch to fuller English on 1 clear English turn (prior high) vs 2 at base; never switch back unprompted | recurrence 13.8 vs 4.3% PROVEN (n=65); profile predicts English AUC 0.68 PROVEN [LIB]; users prefer bots mirroring their code-mix DOCUMENTED (Bawa et al., secondary) |
| **Regional language** (zone/PNS language, prior regional switch) | start in that language if the voice supports it; else Hinglish with an offer ("Aap Gujarati mein baat karna chahenge?") | `on_regional` → switch language once | regional threshold moderate; no accent imitation | prior regional recurrence n.s. PROVEN (n=19); zone as language proxy PROVEN [LIB]; accent mimicry risk DOCUMENTED (EGVE 2023, UBC 2026); mapping ASSUMED |
| **Call-later history** (W0) | warmth mid-high; brevity standard; pace 1.0 | callback acknowledgement opening ("aapne kaha tha baad mein call karein"); time-box; `on_busy` → fix specific slot | lower rush/busy threshold modestly | CL 22.6 vs 14.6% PROVEN (n=5,717); time objection 80% PROVEN; mapping ASSUMED |
| **Not-interested history** (≤14 d strong, decays to base >45 d) | brevity short; warmth mid; formality mid-high (respectful); pace 1.05 | acknowledge last call, one new value point, easy exit; no repeat of the same pitch; respect a second "no" → close politely | lower NI/rejection threshold → graceful exit; avoid self-fulfilling short call by giving the value point *before* the exit offer | NI repeats 67.1% (78.3% ≤3 d) PROVEN (n=57,440); half-life ≈20 d PROVEN; prev2 MF → 9.5% meeting PROVEN; mapping ASSUMED |
| **Meeting-fixed history** (W3) | warmth high; detail allowed; pace 1.0 | recap/confirm meeting; follow-up logistics | normal thresholds | MF 41.2% (3.6×) PROVEN (n=2,151); mapping ASSUMED |
| **High turnover / Limited company** | formality mid-high; English-leaning if English-heavy prior; brevity standard | business-value framing (ROI, buyer quality) rather than basics | normal | turnover barely separates personas PROVEN [LIB]; profile AUC low; **ASSUMED** (weak) |
| **No history (cold)** | robust default: Hinglish by zone, mid formality, mid warmth, pace 1.0–1.05, standard brevity; confidence LOW | all contingencies dormant but present | base thresholds (2 cues); live detection carries the adaptation | cold profile clusters unstable (ARI ≤0.44) PROVEN [LIB]; PS04 FAQ Q6 default + lower confidence DOCUMENTED |
| **Prior frustration / bot-question** (cross-cutting) | AI disclosure up front; warmth high, formality mid-high; brevity short | apology/acknowledge early; offer human/exec route | lower frustration threshold → de-escalate (acknowledge, slow *wording*, offer exit) | next meeting 5.1% / 5.7% vs ~15% PROVEN (n=39/35, weak); affect-adaptive SDS DOCUMENTED (Forbes-Riley & Litman; Sensors 2013) |

Conflict rule (ASSUMED): state outranks trait for plan (for example NI-recent + English-heavy → NI plan in English-leaning Hinglish), and live evidence outranks both. Cap: a single prior call can move at most two settings off default (anti-over-personalisation, [MEM] Q4).

### Devil's advocate
- **No style evidence in PS07.** Every "→ setting" mapping above is ASSUMED. PS07 shows *who* recurs, not *what works*, because VANI had one style (PROVEN [MEM]). Tag every mapping GUESS for helpfulness on the slide.
- **Over-accommodation / mimicry:** obvious mirroring backfires, and human–human mimicry gains often fail to replicate with agents (DOCUMENTED EGVE 2023). Rate entrainment can even *lower* trust in some languages and voices (DOCUMENTED Levitan). Match code-mix ratio and brevity; don't mirror accent, slang or curtness.
- **Stereotyping:** zone→language and turnover→formality are group-level guesses (English-heavy AUC 0.68 still misclassifies many sellers). Always offer the switch, never force it. Treat regional start as an *offer*, not an assumption.
- **Self-fulfilling loops:** "NI → short + easy exit" may cause the next NI. "Rushed → crisp" may teach the seller that VANI calls are throwaway. Needs Afiniti-style ON/OFF interleaving to detect.
- **Trait or register?** Terseness toward a bot is partly bot-directed (DOCUMENTED Zhang & Yu). Calling it a seller trait may overfit.
- **LLM drift:** LLMs drift toward the user's personality anyway (DOCUMENTED EMNLP 2025). Without pinned settings, "adaptation" may be uncontrolled sycophancy.
- **Small n:** confusion, English and regional priors rest on n=19–68 transcribed pairs and lexicon labels with κ≈0.03 vs the evaluator. They can flip under Jev labels.
- **Out of PS04 scope (flag):** bandits, uplift modelling and Afiniti-style pairing need live traffic and randomisation. They are roadmap only.

### Gaps
- The table's pace and threshold numbers are unsized design choices.
- No Indian-B2B evidence for any delivery → outcome effect. The nearest are a US survey call study (rate) and a Hinglish chatbot WoZ study (code-mix).
