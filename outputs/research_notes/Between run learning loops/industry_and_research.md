# Between-run learning loops for voice agents: industry practice and research (as of 2026-10-08)

Scope: how production voice/conversational AI and 2024–2026 research do learning between conversations (post-call evaluation → fix → regression-gated redeploy). The goal is to calibrate VANI PS04: a frozen live switcher (lexicon + Jev), and a per-seller persona generator; an offline LLM reviews each finished call; nothing learns mid-call ([team decision](../../../raw/hackathon/2026-10-08-team-decision-between-run-learning.md), [learning-loops wiki](../../../wiki/projects/vani-hackathon/learning-loops.md)).

Tags: **DOCUMENTED** = a primary source (vendor page, paper abstract) says it; we have not verified it. **VENDOR CLAIM** = marketing result with no published method, data or control; treat it as unverified. **ASSUMED** = our inference. **NOT RE-FETCHED** = cited from well-known papers without fetching them in this session; check the number before putting it on a slide.

---

## Q1. Vendor loops in detail: what is evaluated, how failures are clustered, what changes, gating, human approval, cadence, results

### Takeaway
Almost every production "self-improving" voice product runs the same offline loop: score 100% of finished calls with an LLM judge and fixed metrics, group failures into ranked categories, propose a **small prompt/config/knowledge diff**, replay it against a regression suite (and sometimes a live A/B slice), and have a **human approve before deploy**. Only Coval×Phonely claims to change **model weights** (per customer). None of them publishes a controlled evaluation, so every reported uplift is a vendor claim.

### Cited Findings

**Cekura (evaluation/QA platform)**
- Failures are shown as "recurring ways the agent fails, grouped into categories and ranked by how often they occur", e.g. "fails to confirm the appointment date in 18% of booking calls, here are the transcripts". DOCUMENTED — [Cekura blog](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- The optimiser proposes "prompt and config edits" as "reviewable diffs", and "you approve the change before anything touches the agent". The heavy multi-phase agentic work runs in a server-side sandbox. DOCUMENTED — [Cekura blog](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- Key gating lesson: "an intermediate '100% on the subset' hid two silent regressions that only a sweep across the entire test set caught before anything shipped." DOCUMENTED — [Cekura blog](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- Reported: healthcare booking POC "75% → 100%"; "60K+ voice AI calls evaluated daily"; test runs take 5–10 minutes. VENDOR CLAIM (no n, no held-out split stated) — [Cekura blog](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- The last30days scan summarised Cekura as five stages (capture, auto-evaluate on fixed metrics, cluster into Gap/Conflict/Ambiguity/CodeBug/Upstream, propose fix, validate on a frozen held-out regression suite) plus a prompt-overfitting scan. The page fetched here did **not** list those five stages or the five-way taxonomy explicitly, so treat that taxonomy as unconfirmed. DOCUMENTED (scan summary only) — [last30days scan](../../../raw/research/2026-10-08-last30days-voice-agents-learning-from-past-calls.md)

**Coval × Phonely (Alma), announced 1 Sep 2026**
- "Coval evaluates real production conversations, identifying where an agent is performing well and where it's falling short." Findings "inform ongoing updates to the customer's model". So this is **weight-level retraining** of Phonely's Alma voice LLM, not prompt edits. DOCUMENTED — [Coval blog](https://www.coval.ai/blog/new-self-improving-agents/)
- Per-customer isolation: "Customer data is used exclusively to improve that customer's own model and is never used to train or improve other customers' agents." DOCUMENTED — [Coval blog](https://www.coval.ai/blog/new-self-improving-agents/)
- The loop is stated as "Build → deploy → evaluate → auto-improve → validate → redeploy → repeat". The gating criteria, human approval and cadence are **not described**. DOCUMENTED — [Coval blog](https://www.coval.ai/blog/new-self-improving-agents/)
- Alma is said to be trained on 10M+ phone conversations, 61% faster than GPT-5.2 and >80% cheaper than OpenAI GPT-5 models. VENDOR CLAIM — [SiliconANGLE](https://siliconangle.com/2026/09/01/phonely-launches-alma-a-voice-ai-model-trained-on-over-10-million-phone-conversations/); [destinationCRM](https://www.destinationcrm.com/Articles/CRM-News/CRM-Across-the-Wire/Coval-Partners-with-Phonely-for-Self-Improving-Agents-176413.aspx)
- The scan's "70% at launch → 88% at 12 months vs static 65%" Coval figure **could not be found** in the announcement or by search. Do not cite it. UNVERIFIED — [Coval blog](https://www.coval.ai/blog/new-self-improving-agents/) (absent)

**SquadStack Lift (India, outbound sales/lending; 2026-07-09)**
- Evaluates live calls on conversion and conversation quality, looking for "near-misses where the customer almost booked, the early drop-offs where something broke in the first thirty seconds, the conversions that closed but took a clumsy path". DOCUMENTED — [SquadStack Lift](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)
- Changes are small and one at a time ("Lift changes one thing at a time rather than reworking the whole script"). Examples: capping how often the agent repeats an interest rate; a cleaner way to confirm a misheard loan amount; tightening the reply to "EMI is too high". DOCUMENTED — same
- Gating is **live traffic**, not just replay: "climbing from a small share to a quarter to half to the whole campaign", so that "if a change hurts something that was already working, it gets caught while it's still on that small slice". DOCUMENTED — same
- "Every change Lift proposes is reviewed by a human before it reaches production traffic." "Compliance language, product rules, pricing guardrails, and identity parameters live in protected sections that Lift cannot touch." DOCUMENTED — same
- Reported: appointment booking 2.7% vs 1.5% baseline on 12,000+ leads; gold-loan branch visits 2.2% → 4.3%; a digital-lending campaign fully migrated; a jobs platform scaled to half the campaign. VENDOR CLAIM (no CI, no description of how arms were split) — same

**Vogent ("self-learning")**
- Two stages: Auto-Create ("Create your agent from recordings and talk tracks") and Optimize ("Auto-improve your agent's performance based on historical dials and simulations"). DOCUMENTED — [Vogent docs](https://docs.vogent.ai/platform-overview/self-learning/overview)
- The YC launch describes RL-style methods: agents "design themselves given call recordings, and improve themselves by evaluating every single dial and correcting bad behaviors". The docs page does not say whether prompts or weights change, nor how changes are gated. VENDOR CLAIM — [YC launch](https://www.ycombinator.com/launches/N1x-vogent-self-learning-voice-ai)
- Dial History has a **Counterfactuals** feature "to test how different versions of your agent would have handled past conversations". This is the same idea as VANI's v0-vs-v1 replay of PS07 calls. DOCUMENTED (via search snippet of docs) — [Vogent docs search result](https://docs.vogent.ai/platform-overview/agents/evaluation/dial-history.md)

**Hamming (voice agent QA)**
- A runbook for turning failed production calls into regression tests: (1) freeze an evidence packet (call id, agent version, caller goal, sanitised transcript, tool traces, state before/after); (2) classify **one primary failure type** (intent miss, tool selection, tool arguments, tool ordering, side effect, handoff, safety/policy, latency); (3) recreate with sanitised fixtures; (4) write assertions (tool guardrails, side effects, "must-not-include" transcript phrases); (5) promote to **blocking / scheduled / manual**. DOCUMENTED — [Hamming runbook](https://hamming.ai/blog/failed-production-call-regression-test-runbook)
- "A failed call is test-worthy when it teaches you something the existing suite did not know." "Never use raw production data as the fixture in CI. Use production to learn the pattern. Use sanitized fixtures to reproduce it." "A monitoring alert is not a regression test… A saved recording is not a regression test." DOCUMENTED — same
- Multilingual variants go in the *scheduled* (nightly/weekly) tier, not the blocking tier. DOCUMENTED — same
- Scale claims: 10M+ minutes, 10K+ agents tested. VENDOR CLAIM — same

**Retell / Vapi (platform post-call analytics; the "evaluate" half only)**
- Retell post-call analysis: LLM-extracted Boolean/Text/Number/Enum categories after each call, delivered by dashboard, webhook or API within seconds. DOCUMENTED — [Retell docs](https://docs.retellai.com/features/post-call-analysis-overview); [Retell](https://www.retellai.com/post-call-analysis)
- Vapi `analysisPlan`: summary prompt, structured-data prompt and schema, and a success-evaluation prompt. It uses Claude Sonnet with GPT-4o as fallback, and completes in a few seconds. DOCUMENTED — [Vapi docs](https://docs.vapi.ai/call-analysis)
- Neither ships an automatic fix step; the loop is closed by a human (or a third-party tool such as Cekura/Hamming). ASSUMED (from docs scope)

**Sierra / Decagon (enterprise CX agents)**
- Sierra Insights 2.0: **Explorer** answers natural-language questions over conversations and "generates specific, actionable improvements" with one-click handoff to Ghostwriter. **Expert Answers** finds how human agents resolved similar cases and drafts "a grounded, review-ready article". "Teams can edit, approve, and publish directly from Insights." What changes is mostly **knowledge**, not weights. DOCUMENTED — [Sierra Insights](https://sierra.ai/blog/insights)
- Decagon: Agent Versioning (every guideline, AOP or tool change tested, validated and rolled out), batch **Simulations** with **Watchtower** automated QA, and **Experiments** (live A/B with traffic routing). The cycle: fix AOP/knowledge → re-run simulations to validate → deploy. Watchtower reviews 100% of conversations. DOCUMENTED — [Decagon simulations](https://decagon.ai/blog/decagon-simulations); [Decagon versioning](https://decagon.ai/blog/decagon-agent-versioning)
- Decagon on GEPA in production: 20–100 examples work best; watch for overfitting and prompt bloat; use a length cap and a frontier reflection model. DOCUMENTED (from earlier notes) — [Decagon GEPA](https://decagon.ai/blog/optimizing-gepa-for-production); [generator_loop notes](../Self%20improving%20persona%20and%20switch%20loops/generator_loop.md)

**LangSmith / Langfuse / Arize (LLMOps feedback loops)**
- LangSmith: online LLM evaluators score production runs in near real time; "Add to Annotation Queue" routes runs to subject-matter experts; "Add to Dataset" turns runs into test/few-shot/fine-tune data. Recommended pattern: sample problematic production traces → bootstrap labels with an LLM judge → refine with human annotation → use them to calibrate the judge, improve prompts or extend datasets. DOCUMENTED — [LangSmith automations](https://www.langchain.com/blog/langsmith-production-logging-automations); [LangSmith evaluation](https://www.langchain.com/langsmith/evaluation)
- Langfuse/Arize offer equivalent trace → dataset → eval flows (a Langfuse "self-improving OSS agent" item appeared in the earlier scan). Not re-checked here. GAP

**Others from the scan (not fetched here)**
- 800.com builds agents from existing call transcriptions (detects call types, FAQs, tone, recurring scenarios → editable prompts). Telnyx runs "post-conversation processing" after the call with full context and no real-time latency limit. DOCUMENTED (scan summary only) — [last30days scan](../../../raw/research/2026-10-08-last30days-voice-agents-learning-from-past-calls.md)

### Inferences
- **The industry consensus loop is exactly VANI's design** (ASSUMED): offline judge → failure categories ranked by frequency → small diff → full-suite regression → human approve → versioned deploy. VANI can cite Cekura (full-set sweep), Hamming (failed call → regression case), SquadStack (locked compliance/pricing sections, one change at a time) as prior art for each guard. That is design legitimacy, not a pre-built solution, since VANI writes its own loop.
- **What changes, by vendor:** prompt/config (Cekura, SquadStack, Decagon AOPs), knowledge (Sierra), recordings → prompt (Vogent, 800.com), weights (Coval×Phonely only). VANI's levers (lexicon cues, Jev criteria, thresholds, per-seller memory, generator rules) belong to the prompt/config/knowledge class. That is the right class for 2 days with no GPU.
- **Gating comes in two strengths:** replay/simulation only (Cekura, Hamming, Decagon simulations) vs live A/B ramp (SquadStack, Decagon Experiments). VANI can only do replay-gating, because it has no live traffic. It should say so, and not borrow SquadStack's conversion uplifts as if they apply.
- **Hamming's "one primary failure type per failed call" maps directly onto switch errors:** missed / false / late / wrong-signal for the switcher, and a persona-setting mismatch for the generator.

### Gaps
- No vendor publishes held-out methodology, CIs or a no-change control for its uplift figures. Cekura's 75%→100% and SquadStack's 1.5%→2.7% cannot be verified.
- Coval×Phonely cadence and gating, and whether retraining is fine-tuning or RL, are not disclosed.
- Vogent's mechanics (prompt vs weights, how RL is run) are not on the public docs page.
- Bland AI was not researched (out of budget).

---

## Q2. Research 2024–2026 on learning from deployment feedback between sessions, and documented failure modes

### Takeaway
Research supports **non-parametric, between-episode learning**: extracting natural-language insights, rules or workflows from past successes and failures and feeding them back into the prompt or memory (ExpeL, AWM, Reflexion, GEPA). It also documents that these loops reliably fool themselves when the only signal is an LLM judge. Frozen holdouts, canary cases and deterministic acceptance checks are the documented remedy. Distilling LLM labels into a small classifier is a well-supported, cheap way to make the switcher "learn".

### Cited Findings

**Experience / skill libraries (learn between episodes, no weight updates)**
- ExpeL: (1) collect success and failure trajectories, (2) extract cross-task natural-language insights, (3) recall insights plus similar past successes at inference. Performance improves as experience accumulates; there are no parameter updates, so it works with closed models; it shows forward transfer. DOCUMENTED — [ExpeL, arXiv 2308.10144 (AAAI 2024)](https://arxiv.org/html/2308.10144v3)
- Agent Workflow Memory: induces reusable workflows from past trajectories (offline from training examples or online from test queries). +24.6% and +51.1% relative success on Mind2Web and WebArena; online AWM beats baselines by 8.9–14.0 absolute points as the train/test gap widens. ICML 2025. DOCUMENTED — [AWM, arXiv 2409.07429](https://arxiv.org/abs/2409.07429)
- Reflexion: verbal self-reflection after a failed episode is stored in episodic memory and used on the next trial (reported 91% pass@1 on HumanEval vs 80% for GPT-4 at the time). NOT RE-FETCHED — [Reflexion, arXiv 2303.11366](https://arxiv.org/abs/2303.11366)
- Voyager: an ever-growing skill library of verified code, added only after an environment check confirms success. NOT RE-FETCHED — [Voyager, arXiv 2305.16291](https://arxiv.org/abs/2305.16291)

**Prompt optimisation from traces**
- GEPA: reflective prompt evolution from execution traces plus textual feedback. Beats GRPO by 6% on average (up to 20%) with up to 35× fewer rollouts, and beats MIPROv2 by >10%; gains are reported on a held-out test set. DOCUMENTED — [GEPA, arXiv 2507.19457](https://arxiv.org/html/2507.19457v1)
- DSPy guidance: about 20% train / 80% validation for prompt optimisers; ~30 examples give "substantial value", but aim for ≥300. DOCUMENTED (from earlier notes) — [DSPy optimization overview](https://dspy.ai/learn/optimization/overview)
- TextGrad ("automatic differentiation via text") is the same family: an LLM critique acts as a gradient on prompt text. NOT RE-FETCHED — [TextGrad, arXiv 2406.07496](https://arxiv.org/abs/2406.07496)

**LLM-as-judge post-hoc labelling**
- GPT-4-class judges reach >80% agreement with humans, about the human–human level, but show position, verbosity and self-enhancement bias. DOCUMENTED — [MT-Bench, arXiv 2306.05685](https://arxiv.org/html/2306.05685v4)
- Percent agreement hides judge differences; use chance-corrected agreement (Scott's π or kappa). DOCUMENTED — [Judging the Judges, arXiv 2406.12624](https://arxiv.org/html/2406.12624)
- Criteria drift: grading outputs changes the criteria, so fix the rubric after a short look at outputs and before final scoring. DOCUMENTED — [Shankar et al., arXiv 2404.12272](https://arxiv.org/pdf/2404.12272)

**Distilling LLM labels into small models (the switcher's "learning" path)**
- Classifiers fine-tuned on GPT-4 labels "perform comparably to models fine-tuned with labels from human annotators" across 14 replicated classification tasks. DOCUMENTED — [Pangakis & Wolken, arXiv 2406.17633](https://arxiv.org/abs/2406.17633)
- Counter-evidence: models trained on LLM labels show lower accuracy/F1, **more instability across training runs and early plateaus**. DOCUMENTED — [Feeding LLM Annotations to BERT Classifiers at Your Own Risk, arXiv 2504.15432](https://arxiv.org/html/2504.15432v1)
- CanDist: let the LLM output **candidate label sets** when it is uncertain, then distil them into a small model; this is more robust to the LLM's wrong labels on hard cases. DOCUMENTED — [CanDist, arXiv 2506.03857](https://arxiv.org/html/2506.03857v1)

**Documented failure modes**
- *Judge is not an oracle* (2 Sep 2026): eleven ways the evaluation signal failed in a self-improving agent, in four classes: judge bias, harness/metric failures, ground-truth errors, reward hacking. Examples: "a 100% pass rate concealing 68% true capability"; corrupted ground-truth labels led the optimiser to **delete correct rules**; syntactically broken prompts promoted through silent parser fallbacks. Remedy (PROCTOR): hermetic sandboxes, capability-disjoint roles, acceptance checks that outrank the judge, **frozen holdouts**, **canary cases** (where a perfect score signals cheating). DOCUMENTED — [Wahi, arXiv 2609.02246](https://arxiv.org/abs/2609.02246)
- Same paper (from earlier notes): a judge calibrated on 15 items hit 80% agreement but only 51.9% on the full 54. DOCUMENTED — [arXiv 2609.02246](https://arxiv.org/pdf/2609.02246)
- *Reward hacking of reference-free judges:* under self-play, the judge pass rate went 0.72 → 0.94 while true accuracy stayed at 0.20. DOCUMENTED (search snippet) — [More Convincing, Not More Correct, arXiv 2607.05904](https://www.alphaxiv.org/abs/2607.05904)
- *"Master key" attacks:* superficial tokens (reasoning openers, symbols) make LLM judges give false positives. DOCUMENTED — [One Token to Fool LLM-as-a-Judge, arXiv 2507.08794](https://arxiv.org/pdf/2507.08794)
- *Misevolution:* self-evolving agents degrade along model, memory, tool and workflow paths. Accumulated memory alone can erode safety alignment. DOCUMENTED — [Your Agent May Misevolve, arXiv 2509.26354](https://arxiv.org/pdf/2509.26354)
- *Utility up, trust down:* even in benign task evolution, score-driven memory evolution erodes initial safety constraints (safety, privacy, fairness). DOCUMENTED — [TAME, arXiv 2602.03224](https://arxiv.org/html/2602.03224)
- *Unfaithful use of experience:* agents often ignore or misuse condensed experience; there is a gap between utility and faithfulness. DOCUMENTED — [arXiv 2601.22436](https://arxiv.org/html/2601.22436v2)
- *Brittleness under drift:* memory updated from interaction outcomes is brittle under true distribution shift and continuous feedback. DOCUMENTED — [Live-Evo, arXiv 2602.02369](https://www.emergentmind.com/papers/2602.02369)
- *Poisoning:* AgentPoison shows that poisoned memory/knowledge-base entries can backdoor retrieval-based agents. NOT RE-FETCHED — [AgentPoison, arXiv 2407.12784](https://arxiv.org/abs/2407.12784)
- *Feedback loops / model collapse* from training on model-generated data. NOT RE-FETCHED — [Shumailov et al., Nature 2024](https://www.nature.com/articles/s41586-024-07566-y)

### Inferences
- **Map to VANI (ASSUMED):**
  - Loop B per-seller memory is ExpeL/Reflexion-style episodic memory.
  - Loop B global rules are ExpeL "insights" or AWM "workflows", gated by n ≥ 200 + CI + time split. That is stricter than either paper and a good answer to "how do you stop it learning noise".
  - Loop A lexicon/classifier updates are LLM-label distillation; CanDist-style "uncertain → candidate set / abstain" fits the existing rule "accept only if Jev and reviewer agree, or a human confirms".
- **The guards VANI already plans match PROCTOR almost one-for-one (ASSUMED):**
  - frozen hand-labelled test set = frozen holdout;
  - Jev/reviewer agreement + deterministic switch-log checks = acceptance checks that outrank the judge;
  - reviewer (offline LLM) ≠ live decider (lexicon + Jev) = capability-disjoint roles.
  - **Missing: canary cases.** Add 5–10 replay calls with a planted, known signal (and some with none), so a reviewer or loop that "improves" by labelling everything as a signal is caught.
- **Specific failure modes to name and guard in VANI (ASSUMED):**
  - *recency overfitting:* one bad hackathon call rewrites a global rule. Guard: the n ≥ 200 + time-split gate; demo-call corrections only enter per-seller memory.
  - *judge-label drift:* the reviewer marks every slow reply as "confusion". Guard: kappa vs human on 20–30 calls; canaries.
  - *forgetting:* fixing a Gujarati miss adds a cue that causes Hindi false positives. Guard: full-suite per-signal precision/recall, not a subset (the Cekura lesson).
  - *safety erosion:* the generator edges toward pricing or claims. Guard: SquadStack-style locked sections plus PS04 FAQ Q5.
  - *poisoning:* seller text in memory steers the generator. Guard: memory stores enumerated tags (rushed, price-objection, language = gu), never free text.

### Gaps
- No 2024–2026 paper found that evaluates a between-call learning loop **on real phone calls** with a held-out control. Research evidence is from web navigation, coding, QA and benchmarks.
- No numbers found for how many LLM-labelled turns a char-n-gram or small classifier needs to match a lexicon for code-mixed Hinglish/Gujarati signal detection.

---

## Q3. Patterns specific to sales/outbound calling and Indian multilingual voice

### Takeaway
The only concrete Indian evidence of learning from calls is **SquadStack Lift** (outbound lending, booking and jobs campaigns; vendor-reported uplifts; human-gated; locked compliance sections; live ramp). Gnani, Haptik and Sarvam publicly show analytics, not closed improvement loops. Sales loops optimise **conversion near-misses and early drop-offs**, which matches VANI's outcome-backed per-seller memory.

### Cited Findings
- SquadStack's improvement examples are Indian lending/sales objection handling: repeated interest-rate mentions, confirming a misheard loan amount, the "EMI too high" reply. The targets are bookings and branch visits. VENDOR CLAIM — [SquadStack Lift](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent)
- Gnani.ai markets Automate365/Assist365/Armour365/Aura365 (omnichannel analytics). Search found no public description of an automatic post-call → fix loop. DOCUMENTED (absence in search) — [Gnani](https://www.gnani.ai/?p=17393)
- Haptik documents an Intelligent Analytics tool (message and word analysis) for a human to analyse bot performance; there is no automated fix step. DOCUMENTED — [Haptik docs](https://docs.haptik.ai/intelligent-analytics-/introduction-to-haptiks-analytics-tool)
- Hamming puts **multilingual variants** in the scheduled (nightly/weekly) regression tier. This implies that vendors treat language coverage as a drift risk rather than a blocking gate. DOCUMENTED — [Hamming runbook](https://hamming.ai/blog/failed-production-call-regression-test-runbook)
- VANI internal facts:
  - prior-call outcome predicts meetings (4.1% after Not Interested vs 21.7% after Meeting Fixed);
  - a seller's own signals recur (rush 30.8% vs 21.1%; confusion 25.0% vs 7.0%);
  - past turns are 99.4% Latin script, but live ASR emits Devanagari;
  - three static-personalisation trials failed to beat control.
  PROVEN (aggregate) — [learning-loops wiki](../../../wiki/projects/vani-hackathon/learning-loops.md); [proof_and_scope](../Self%20improving%20persona%20and%20switch%20loops/proof_and_scope.md)

### Inferences
- **Script mismatch is the India-specific trap (ASSUMED).** Learning from PS07 (Latin-script Hinglish) can improve replay metrics while doing nothing for live Devanagari ASR. Every v0→v1 claim should be reported on both scripts, or on transliterated replays.
- **Indian outbound practice keeps humans in the loop and locks compliance text.** IndiaMART judges will likely expect the same. Saying "the reviewer proposes; a human approves global-rule changes; per-seller memory auto-applies only enumerated tags" aligns with SquadStack and with PS04 FAQ Q5.
- The failed static-personalisation trials are the strongest reason **not** to claim conversion uplift. Claim switch precision/recall and persona-fit improvements on held-out replays instead.

### Gaps
- No public Sarvam material found on post-call learning loops (not searched in depth; Sarvam's own agent platform docs may cover analytics).
- No independent (non-vendor) evaluation of any Indian voice-agent learning loop exists that we could find.

---

## Q4. What a convincing 5–7 minute between-run learning demo looks like, and what judges will probe; plus devil's advocate and PS04 scope

### Takeaway
Show **one concrete mistake → the reviewer's label → the diff → the gate passing on a frozen holdout → the same situation handled correctly on run 2**, then one aggregate v0→v1 table on held-out replays with n and CIs. Judges will probe the holdout, judge reliability, sample size, live vs replay, and whether learning matters for PS04's scored criteria at all. Between-run learning is **not a PS04 deliverable or criterion**. It earns points only through switches (25%), fit (25%) and evidence (15%), so it should take ≤1 minute of a 5–7 minute slot, or ~6 build hours at most.

### Cited Findings
- PS04 deliverables: generator code, a spec per seller with reasons, a live Sarvam demo with ≥1 mid-call switch for 2–3 contrasting sellers, a switch log, a one-slide presentation. Criteria: fit 25%, switches 25%, distinctness 20%, voice 15%, evidence 15%. None mentions learning across runs. DOCUMENTED — [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- PS04 FAQ Q3: a pre-scripted switch "that cannot respond to what the seller says will score lower". FAQ Q6: missing fields → defaults, lower confidence, "let live adaptation correct them". DOCUMENTED — same
- Vendor demos frame the story as diff + evidence + side-by-side: SquadStack shows "exactly what changed, why the system proposed it, and how it performed against the existing agent in a side-by-side comparison"; Cekura shows the failure category with its % and transcripts. DOCUMENTED — [SquadStack](https://www.squadstack.ai/blog/introducing-lift-self-improvement-for-your-voice-ai-agent); [Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- Vogent's "Counterfactuals" (how a different agent version would have handled past calls) is the industry name for v0-vs-v1 replay. DOCUMENTED — [Vogent docs](https://docs.vogent.ai/platform-overview/agents/evaluation/dial-history.md)
- Wahi: a subset pass can hide a large true-capability gap; frozen holdouts and canaries are needed. Cekura: a subset "100%" hid two regressions. DOCUMENTED — [arXiv 2609.02246](https://arxiv.org/abs/2609.02246); [Cekura](https://www.cekura.ai/blogs/shipping-self-improving-voice-agent-to-customers)
- VANI sample-size facts: with ~25–30 positives per signal only gains of ~20 points or more are distinguishable; kappa is ±0.26 at n = 30. PROVEN (internal calc) — [learning-loops wiki](../../../wiki/projects/vani-hackathon/learning-loops.md)

### Inferences

**Demo script for the learning segment (≈60–90 s inside the 5–7 min; ASSUMED)**
1. *Run 1 (replayed or live):* the seller says "haan haan jaldi bolo, mujhe meeting hai" in Devanagari, and v0 misses the **rush** signal (the switch log has no entry).
2. *Post-call review card (≤10 s on screen):* the reviewer labels the turn "rush — missed". Jev agrees, so the label is accepted. Proposed diff: add the cue `जल्दी बोलो`/`jaldi bolo` to the rush lexicon; the per-seller memory for this seller gets `rushed=true`, so the next persona opens short.
3. *Gate:* frozen holdout (never seen by the loop) shows rush recall 0.52→0.71 and precision 0.80→0.79 (illustrative placeholders, not results), the other four signals unchanged within the CI, and canaries pass. Status: "accepted → switcher v1, generator v1".
4. *Run 2, same seller:* the persona now opens short (spec diff on screen: opening = time-boxed, reason = "rushed on last call"), and the rush cue fires on the right turn and is logged.
5. *One table:* v0 vs v1 per-signal P/R/latency on held-out replays, n per signal, CIs, both scripts. One line under it: "learning came from N PS07 replays + M hackathon calls".

**Likely judge probes and good answers (ASSUMED)**
- "Is run 2 just memorised?" → the holdout and other sellers are never shown to the loop; show a *different* held-out seller also improving, or honestly not improving.
- "Who checks the checker?" → reviewer–human kappa on 20–30 calls with its CI; canaries; deterministic switch-log checks.
- "Did anything get worse?" → full-suite per-signal table, not just the fixed signal (the Cekura lesson).
- "Would this lift meetings?" → "Not shown. Past personalisation trials failed to beat control. We claim detection and fit, not conversion."
- "Is an LLM deciding switches live?" → no; latency figures (Jev p95 ~1.4 s) plus the frozen switcher.
- "Data on premises?" → the review runs on Sarvam or the internal gateway; memory holds enumerated tags only.
- "Pre-built?" → the loop code was written at the event; frameworks are named in skills.md.

**Devil's advocate: hype vs evidence**
- "Self-improving" in vendor marketing usually means **LLM-scored analytics + suggested prompt diffs + human approval**. Only Coval×Phonely changes weights, and it publishes no numbers. Every uplift figure (Cekura 75→100%, SquadStack 1.5→2.7%, 2.2→4.3%) is an uncontrolled vendor claim. The unsourced "70→88% vs static 65%" should be dropped entirely.
- Research gains (AWM +51% relative, GEPA +6–20%) come from benchmarks with ground-truth success signals. VANI's signal is an LLM reviewer with no ground truth, which is exactly where the documented judge-hacking and misevolution failures happen.
- **Credible hackathon claims:**
  - (a) a working offline review → diff → gated redeploy pipeline;
  - (b) v0→v1 gains on held-out replays for the specific signals fixed, with n and CIs;
  - (c) per-seller memory visibly changing the next persona, with a reason.
- **Not credible:** "the agent learns from every call and keeps getting better"; any conversion or meeting uplift; "learned from our 10 demo calls"; "no human in the loop".
- **Small-n reality:** with 25–30 positives per signal, a single-signal fix must move recall by ~20 points to be visible. Pick the demo fix where the effect is that large, or show the effect is within noise and say so.

**Outside PS04 scope (flag; ASSUMED)**
- Live A/B ramps (SquadStack), weight retraining (Coval×Phonely), RL from dials (Vogent), bandits, GEPA prompt evolution: none is scored, and all are infeasible without traffic or GPU in 2 days.
- Any learning that changes **what** VANI says (prices, facts, compliance) violates FAQ Q5; lock those sections.
- A failure-clustering dashboard (Cekura/Sierra-style) is nice to show but unscored. Keep it to one switch-log/review view.
- The learning loop must not displace the required items: the live Sarvam mid-call switch, 2–3 audibly distinct personas, 2+ languages, the switch log, the one slide.

### Gaps
- Final weightings are "indicative"; whether judges will reward between-run learning at all is unknown until the organisers confirm.
- The real v0→v1 numbers do not exist yet; the figures in the demo script are placeholders.
- No public hackathon-judging guidance specific to "self-improving" claims was found.
