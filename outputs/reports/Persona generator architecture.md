# Let rules decide and Sarvam speak

**The persona pipeline is five blocks. Code does almost all of it. The LLM touches seller data only to write the spoken wording, and no block needs a runtime agent.** Block 1 (data refinement) is a deterministic script. It turns one seller's rows, plus what was mined from all sellers, into one refined `seller_context.json`. **RAG is not warranted**: the inputs are structured, the evidence is aggregate rule rows with ids, and the approved library is small enough to pass whole. Block 2 generates the persona and the call plan **together, as one spec**. Rules choose every setting, and one Sarvam `sarvam-105b` call writes only the spoken lines. On six synthetic sellers this option (A) passed validation **6/6 on the first try**. The single-LLM-call option (B) passed **0/6**. Draft-plus-revise (C) reached **4/6 after revisions** and still made confident wrong rule decisions (PROVEN) ([options test](../research_notes/Persona%20generator%20architecture/vani_options_test.md)). Block 3 validates the spec and compiles it into what Sarvam actually accepts. Sarvam's inputs, not taste, decide the split: a fixed bundle at call start, then only an overwritable per-turn variable. That is why our measured spikes force one design change. **The plan must be re-sent every turn or held in a separate, non-overwritten variable.** Re-sent each turn it held **20/20** checks under hostile and Gujarati sellers. Passed only at call start it held **23/28**, losing personalisation and the playbook (PROVEN) ([plan-stress spike](../../raw/research/2026-10-08-plan-stress-spike.md)). Block 4 switches live: the lexicon acts on the current turn, Jev corrects the next one, and a code policy has the final say. Block 5 learns between runs by editing rules, the library and per-seller memory, never model weights. Agents earn a place only offline, in authoring rules and the library and in post-call review, where real external feedback exists.

Tags: **PROVEN** = measured by us, in the spikes or on PS07 aggregates. **DOCUMENTED** = a vendor doc, paper or `raw/` source says it. **ASSUMED** = our design or inference. No real seller data was used in any test cited here.

> **The team lead's framing, which structures this report:** "persona generation becomes one of the blocks and then inside it we decide how — an agent or a script; how the agent or script will be made is one layer beneath. Then what the input is: the whole one seller's data, and how it will learn from other sellers. If we get one refined JSON then data refinement becomes one more block; there we decide how to do the refinement (RAG or something proven), what kind of data, how it gets it, and what the output is. Then decide whether persona and plan are created simultaneously — that depends on how Sarvam takes input. Then the switches: how, why and what (input, output)."

The binding constraints are these:

- **No model is trained.** What learns is our logic: rules, memory, cues and thresholds.
- **Voice gender is a persona setting**, fixed for the whole call.
- **The call plan, including personalisation, is required.** "Personalisation" is our reading of an undefined PS04 term.
- **The core voice agent is Sarvam.**
- **No customer data leaves the premises.**
- **All build work happens during the two days.**

([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md); [persona requirements](../../wiki/projects/vani-hackathon/persona-requirements.md); [learning loops](../../wiki/projects/vani-hackathon/learning-loops.md))

## Five blocks, and Sarvam's inputs decide where they split

Each seam between blocks follows a platform fact. At call start, Sarvam accepts four things per SDK session: `initial_bot_message`, `initial_language_name`, `text_to_speech_config{speaker, speech_settings{pace, pitch}}` and `agent_variables`. The phone path, Instant Outbound, accepts variables and app overrides but **no TTS override**. There the voice comes from a published `app_version` (DOCUMENTED) ([spike log](../../raw/research/2026-10-07-spike-log.md)).

Once the call starts, the only channel we control is our tool's response, which the agent's LLM calls on most seller turns. That response overwrites `persona_directive` (PROVEN) ([plan-following spike](../../raw/research/2026-10-08-plan-following-spike.md)). The voice is "assigned per language at call start and will not change mid-conversation", so voice and pace are pre-call decisions only (DOCUMENTED) ([system design](../../wiki/projects/vani-hackathon/system-design.md)).

Everything below follows from those facts. Delivery and plan are decided once, before the dial. The compiler splits them into a call-start bundle and a per-turn payload. The switcher writes into the per-turn payload.

```
 ┌────────────────────────── OFFLINE / BETWEEN RUNS ──────────────────────────┐
 │ PS07 all-seller aggregates ─► rule miner (script; n, CI, time split, tier) │
 │      ─► rules_vN.json   library_vN.json (openings, objection moves, steps) │
 │ traces ─► B5 reviewer (LLM on gateway/Sarvam) ─► 2-key filter ─► gate      │
 │      ─► rules_vN+1 · library_vN+1 · lexicon/θ_vN+1 · seller memory         │
 └───────────────┬────────────────────────────────────────────▲──────────────┘
                 │                                            │ trace
 PRE-CALL        ▼                                            │
 seller rows ─► B1 DATA REFINEMENT (script) ─► seller_context.json
   + memory_vN          features · history · memory · segment priors · missing[] · completeness
                 ▼
 B2 PERSONA + PLAN (rules choose; 1 Sarvam call writes wording; template fallback)
                 ─► persona_spec.json  (8 delivery + 5 plan fields; value·reason·cited_fields·rule_id·tier·confidence)
                 ▼
 B3 VALIDATE + COMPILE (code; 1 repair call, then template)
     ├─► call-start bundle: initial_bot_message · initial_language_name ·
     │     text_to_speech_config (SDK) | app_version (phone) · agent_variables
     └─► call config to signal server: plan_prefix · base levels · escalation · max_switches · rule_trace
                 ▼
 IN-CALL   Sarvam Voice Agent (speaks every word) ──tool call(utterance, call_key)──►
           B4 SWITCHER: lexicon (now) · Jev (next turn, async) · policy (hysteresis, max 2)
           ◄── persona_directive = plan_prefix + "| Right now: <mode>"   (EVERY turn)
           ─► switch log row (signal, change, reason, source, plan step, versions)
           language switch: Sarvam built-in; logged from transcript language field
                 ▼
           trace (turns, tool calls, switch log, spec_version, outcome) ─► B5
```

| Block | Input | Output | Feeds | Build type |
|---|---|---|---|---|
| B1 Data refinement | One seller's rows (profile, business type, turnover, categories, engagement, past outcomes and objections); per-seller memory vN; segment priors and rule table from all sellers | `seller_context.json` | B2 | Script |
| B2 Persona + plan | `seller_context.json`, `rules_vN`, `library_vN`, voice catalogue | `persona_spec.json`: delivery and plan, one reason, rule id, tier and confidence per field | B3; deliverable 2 | Rules + one Sarvam wording call |
| B3 Validate + compile | `persona_spec.json` | Sarvam SDK or Outbound payload; signal-server call config | Sarvam agent, B4 | Code (+1 repair call) |
| B4 In-call switcher | Tool-call utterance (Devanagari), call key, call config, transcript language field | Per-turn `persona_directive` (plan + mode); switch-log rows | Sarvam agent; deliverable 4; B5 | Code + async Jev |
| B5 Between-run learning | Traces, reviewer labels, frozen gold set | Versioned rules, library, lexicon, thresholds, memory | B1, B2, B4 next run | Script + offline LLM reviewer + gate |

## Block 1 refines one seller into one JSON and borrows from other sellers through mined rules, not retrieval

**Why it exists.** PS04 deliverable 1 is "working code that takes a seller file as input and outputs a persona". FAQ Q6 requires lower confidence wherever fields are missing ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)). A separate refinement block makes both properties mechanical. Every downstream reason can cite a path in one JSON, and the validator can check whether that path is present. The block is also where "learning from other sellers" enters, and the data says that matters. **Memory beats profile on a time split**: next-meeting AUC is 0.71 vs 0.58, and next-Not-Interested AUC is 0.78 vs 0.54. **40.5% of sellers have two or more calls, and they hold 71.3% of all calls** (PROVEN, aggregate) ([between-run report](Between%20run%20learning%20loops.md)). The seller's own history is the strongest signal. Other sellers supply the prior that tells you what that history means.

**How, one layer beneath.** There are four candidates:

- **A plain script** (DuckDB or pandas over the `data/` files). Deterministic, millisecond-fast, and the data never leaves the machine.
- **An LLM summariser over each seller's transcripts.** It adds nothing the structured columns lack, since past outcomes, objection categories and evaluator flags already exist. It also sends seller text to a model.
- **Classic RAG over past transcripts.** Rejected for three reasons. It would put raw seller text into prompts, which breaks "only aggregates". The evidence PS04 asks for is *rule-level* ("sellers who object on price respond better to…"), which is a set-membership check on rule ids, not passage retrieval ([LLM architecture notes](../research_notes/Persona%20generator%20architecture/llm_architectures.md)). And the "retrieve similar sellers first" variant was never tested, so its gain is unmeasured.
- **Similar-seller aggregates.** We take this one, but as a **deterministic segment-cell lookup**, not vector retrieval. A coarse five-feature grid over PS07 has **285 populated cells, 181 of them with 50 or more sellers** (PROVEN) ([self-improving loops report](Self%20improving%20persona%20and%20switch%20loops.md)). The seller's cell supplies base rates and a Beta prior. The seller's own history then updates that prior.

Industry practice agrees. Every voice platform checked (Bolna, Retell, Vapi, ElevenLabs, Synthflow, Sarvam) fills `{{variables}}` from CRM fields pulled by code before the dial (DOCUMENTED) ([industry notes](../research_notes/Persona%20generator%20architecture/industry_practice.md); [Retell](https://docs.retellai.com/build/dynamic-variables); [Sarvam variables](https://docs.sarvam.ai/conversations/build/variables-personalization)). Only the sales-prep products use retrieval, and they retrieve from a curated *library* (Octave), not raw history (DOCUMENTED) ([Octave docs](https://docs.octavehq.com/concepts/agents)).

**Choose the script.** It has two parts. The first runs offline once over all sellers: the **rule miner**. A rule survives only with n ≥ 200, a CI that excludes zero, and a direction that holds on a time split (mine Apr–Jul, check Aug–Sep). It is then tiered STRONG, MODERATE, WEAK or GUESS (DOCUMENTED design) ([learning loops](../../wiki/projects/vani-hackathon/learning-loops.md)). The second runs per seller: the **context builder**. It computes features and completeness from the core fields, applies memory decay, and attaches the segment priors.

Memory decay works as follows. **State** facts, such as the last outcome, decay with weight exp(−gap/28) and reach a half-life of about 20 days. **Trait** facts, such as rush, terse or English-heavy, are kept as a Beta posterior shrunk toward the segment rate (PROVEN counts, ASSUMED fit) ([between-run report](Between%20run%20learning%20loops.md)). Write the context builder fresh at the event, because spike code counts as research, not submission.

**What it emits.**

| Field group | Contents | Source |
|---|---|---|
| `profile` | business_type, turnover_band, categories, city, state; each may be null | Seller file |
| `engagement` | logins and activity bands | Seller file |
| `history` | last_outcome, gap_days, last_objection, signals {rush, confusion, frustration, bot_question, …}, last_language, prior-to-last outcome | Seller's past calls |
| `memory` | trait posteriors (rush, terse, English-heavy), state weight, per-seller overrides (e.g. a voice remark), dnc | Per-seller memory vN (B5) |
| `segment` | cell id, segment base rates and priors | All-seller aggregates |
| `quality` | missing[], completeness (share of 8 core fields present) | Computed |
| `versions` | context_version, rules_version, memory_version | Manifest |

The companion artefact is `rules_vN.json`. Each row holds rule_id, predicate, setting, level, n, effect, CI, time_split_holds and tier. That table is the "evidence table" deliverable and the 15% evidence criterion in one file.

## Block 2 builds persona and plan in one pass: rules choose, one Sarvam call writes the words

**Why it exists.** It produces deliverable 2: a spec per seller covering voice, language, tone and conversation plan, with a reason per choice. Scoring rewards fit (25%), distinctness (20%) and evidence (15%), so 60% of the problem score depends on this block's output ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)).

**How, one layer beneath: the measured comparison.** We prototyped the options on six synthetic sellers shaped like PS07 files. They ranged from a confused Marathi retailer to a seller with 62% of fields missing, scored against a 12-rule toy evidence table and 23 hand-labelled key decisions (PROVEN) ([options test](../research_notes/Persona%20generator%20architecture/vani_options_test.md)):

| Option | First-try validator pass | Key rule decisions correct | Latency per seller | Cost per seller |
|---|---|---|---|---|
| **A: rules choose every setting; one Sarvam call writes only the wording** | **6/6** | **23/23** (by construction) | ~1.0 s | ~₹0.017 |
| B: one structured Sarvam call writes the whole spec | 0/6 (json_schema strict: 1/6; 4/6 invalid JSON from whitespace loops) | 16/23 | ~4.2 s | ~₹0.16 |
| C: B's draft plus up to two validator-driven revisions | 0/6, then **4/6 after 2 revisions** | 17/23 | ~7.6 s | ~₹0.30 |
| Claude Code headless with a skill (2 sellers) | 2/2 | 9/9 | ~24 s | ~$0.18 |

**The decisive finding is not the pass rate. It is the error that validators cannot see.** B and C produced well-formed specs with wrong decisions and false reasons. One example is pace "normal" for a seller confused two days ago, with the reason "no specific pace rule was triggered". C's repair loop fixed *form* errors but moved judgement only from 16 to 17 of 23.

That matches the literature. Self-correction works when feedback comes from outside the model and fails when the critique is intrinsic. **"LLMs cannot self-correct reasoning yet"**, and sometimes performance degrades after self-correction (DOCUMENTED) ([Huang et al.](https://arxiv.org/abs/2310.01798); [Kamoi et al.](https://arxiv.org/abs/2406.01297)). Verifier loops work because tools do the checking (DOCUMENTED) ([CRITIC](https://arxiv.org/abs/2305.11738)). Nothing outside the model can check "did you apply rule R04" except running the rules again. So put the rules in code from the start.

A also tracks seller differences better. Persona distance correlated with seller-feature distance at **ρ 0.82 in A, against about 0.5 in B and C** (PROVEN, 15 pairs). The LLM options looked more "distinct" on raw counts partly through noise, and noise is what the 20% distinctness criterion should *not* reward. Free-text generation is also documented to collapse toward stereotyped personas (DOCUMENTED) ([arXiv 2604.24698](https://arxiv.org/abs/2604.24698)).

**Claude Code got 9/9 decisions but is the wrong runtime.** It sends seller files to an outside vendor, so it is off premises. At ~$0.18 and ~24 s per seller it does not scale. And "the logic is a prompt to a general agent" invites the pre-built and "core must be Sarvam" objections (ASSUMED risk). Anthropic's own guidance is to start with single optimised calls and "add multi-step agentic systems only when simpler solutions fall short" (DOCUMENTED) ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)). Simple baselines beat complex agents at equal cost (DOCUMENTED) ([Kapoor et al.](https://arxiv.org/abs/2407.01502)).

**Where an agent is useful.** Agents fit three offline places where real external signal exists:

1. **Authoring rules and the library.** Claude Code reads only aggregates, proposes candidate rules, runs the stats scripts and revises. The statistics are the external check. Code still computes n, effect and tier.
2. **Writing and debugging `rules()` and the validators** during the build.
3. **Post-call review in B5.** The reviewer runs on the internal gateway or Sarvam, not Claude, when it sees real transcripts.

Industry converged on the same split. 11x dropped a free ReAct agent ("infinite loops", wrong tools) for fixed specialist structure. Octave pins playbooks "for deterministic results" (DOCUMENTED) ([11x write-up](https://zenml.io/llmops-database/rebuilding-an-ai-sdr-agent-with-multi-agent-architecture-for-enterprise-sales-automation); [Octave](https://docs.octavehq.com/concepts/agents)). If the slide wants an "agentic" trace, log A's steps (context → rules → wording → validate → repair → final) instead of building an agent.

**Field ownership inside A.**

| Spec field | Owner | Note |
|---|---|---|
| Voice gender, speaker id, pace, pitch | Rules → voice resolver over the v4 catalogue | Gender order: language coverage → timbre target from warmth and pace → explicit seller evidence. Always GUESS tier. Pitch only once proven audible. |
| Language, Hinglish mix, formality, warmth, brevity | Rules | Classification-like; strong data signals |
| tier, confidence, rule_id, missing-field defaults | Code only | confidence ≤ min(tier cap, completeness); the LLM may never upgrade it |
| Plan steps, objection order, escalation | Rules choose ids from the library | Last objection first (WEAK); "already in touch" escalation (STRONG) |
| Guardrails | Code constant | FAQ Q5: delivery, never facts, price or compliance |
| Opening line, personalisation lines | One Sarvam call, 2-key JSON | Must cite present fields only; native script |
| Reason sentences | Code skeleton, optionally reworded | "R04: confusion on last call (2 days) → pace slow" |

A's measured weaknesses are all fixable in code or in the prompt:

- **Gender collapsed to female for every language.** The coverage rule was too blunt.
- **One internal label leaked** ("bot_question"); a new validator now catches it.
- **Hinglish came out in Roman script 3/3** despite instructions to use Devanagari.

Spelled-out number words ("do minute") slip past the digit check, so price-context number words belong on the banned list (PROVEN observations, ASSUMED fixes) ([options test](../research_notes/Persona%20generator%20architecture/vani_options_test.md)). Do not use Sarvam's strict json_schema mode on nested schemas: it looped on whitespace in 4 of 6 calls. A's flat two-key wording schema never failed (PROVEN).

**Generate persona and plan together or separately? Together, and Sarvam's inputs settle it.** Sarvam takes one bundle at call start: opening, language, voice and variables. After that it accepts only per-turn variable writes. Persona and plan both depend on the same features and the same rules. A rush trait drives fast pace, high brevity, a time-boxed opening and a callback-first escalation. A confusion state drives slow pace, low formality and a confirm-understanding step. Generating them separately duplicates the logic and invites contradictions, such as a formal tone paired with a casual opening.

So B2 emits **one `persona_spec.json`** with two sections, `delivery` (8 fields) and `plan` (opening, personalisation, steps, objection order, escalation, guardrails). B3 then splits it by *delivery channel*, not by generation step:

- **Fixed for the call:** voice, pace, language and opening.
- **Re-sent on every turn:** plan steps, personalisation, playbook, escalation, and the tone and brevity levels.

The one LLM call writes the opening and personalisation lines inside the same pass. At ~1 s and ₹0.017 per seller, A covers all 149K sellers for about ₹2.5K and roughly 2 h at 20-way concurrency (PROVEN tokens × DOCUMENTED price, ASSUMED concurrency). Generate in batch before the campaign, never at dial time. Vapi, for example, caps call-setup generation at 7.5 s (DOCUMENTED) ([Vapi](https://docs.vapi.ai/server-url/events)).

**B2 I/O.** Input: `seller_context.json`, `rules_vN.json`, `library_vN.json` and the v4 voice catalogue. Output: `persona_spec.json` = `{seller_id, spec_version, delivery{voice_gender, speaker, language, pace, pitch, formality, warmth, brevity}, plan{opening{move_id, text}, personalisation[{field, line}], steps[], objection_order[], escalation[], guardrails[]}}`. Every field is `{value, reason, cited_fields[], rule_id, tier, confidence}`. A DNC seller gets no spec.

## Block 3 validates the spec, then compiles it for a platform that forgets the plan after one turn

**Why it exists.** Validation is the only quality gate that is reliable and cheap. Compilation is where our abstract spec meets Sarvam's concrete and partly lossy inputs. The new spike results make compilation a design problem in its own right.

**Validators.** About 150 lines of Python, run in this order (PROVEN that they run; [options test](../research_notes/Persona%20generator%20architecture/vani_options_test.md)):

1. Schema and enums.
2. Every cited field resolves to a non-null field; a missing field forces rule DEFAULT.
3. The rule_id exists, and its tier equals the rule table's tier, so tiers cannot be inflated.
4. Spoken text contains no digits in any script, no price or discount words, and no internal labels.
5. Gates: steps start with greet-and-confirm-owner and end with confirm or callback; escalation includes "human on request"; guardrails equal the fixed set.
6. The speaker is a v4 voice for that language, and its gender matches.
7. confidence ≤ min(tier cap, completeness).

On failure, make **one repair call** that passes the validator's error text, which is CRITIC-style external feedback. If that also fails, fall back to the per-language template, so the demo never breaks. DSPy Assertions report up to **164% more constraint passes** from exactly this constraint-plus-retry pattern (DOCUMENTED) ([Singhvi et al.](https://arxiv.org/abs/2312.13382)). Add one **rule-consistency re-check** that re-evaluates each cited rule's predicate on the seller. That is the only validator able to catch B and C's class of error, and in A it guards against bugs in our own code (ASSUMED).

**Compiler, SDK path.** The mapping is:

- `initial_bot_message` = the opening text.
- `initial_language_name` = the language, with Hinglish mapped to Hindi.
- `text_to_speech_config{speaker_name, speech_settings{pace: 0.9 / 1.0 / 1.1}}`, with pitch omitted until it is shown to be audible.
- `agent_variables{seller_mode, persona_directive, plan_steps, objection_order, formality, warmth, brevity, call_key}`.
- A **signal-server call config**: `{seller_id, spec_version, plan_prefix, base{language, formality, warmth, brevity, pace}, escalation[], max_switches: 2, rule_trace{field: rule/tier}}`.

Sarvam has not yet been shown to accept every field (PROVEN that it runs; acceptance untested). Whether per-session pace and pitch are honoured on v4 is test T9 and still unproven. If they are not, pace has to be carried by wording.

**Phone path limits.** Instant Outbound takes `app_version`, `agent_variables` and app overrides (opening, language, state), but no TTS override (DOCUMENTED) ([spike log](../../raw/research/2026-10-07-spike-log.md)). Each (speaker × pace) pair therefore needs its own published version. A gave six different speakers to six sellers, so for phone, collapse to about 3–4 voice profiles per language and keep full per-seller voice on the SDK demo (ASSUMED). The catalogue constrains this further. v4 has 2 female and 1 male Gujarati voices, 6 female and 3 male Marathi, and **Tamil has only 3 male voices** (PROVEN, catalogue).

**The new constraint: the plan has to ride every turn.** Under cooperative sellers the agent followed a passed plan in **15/16** checks. The scripted opening was spoken word for word, confirmed by recording and transcription, because the transcript stream omits it (PROVEN) ([plan-following spike](../../raw/research/2026-10-08-plan-following-spike.md)).

The stress test separated two delivery routes over 10 calls and 46 seller turns (PROVEN) ([plan-stress spike](../../raw/research/2026-10-08-plan-stress-spike.md)):

- **Plan re-sent inside every per-turn `persona_directive`: 20/20.** This covered hostile and off-plan sellers: the agent answered "who are you" and steered back, asked when the owner would return, quoted **no amount on any of 8 price-demand turns**, and gave a 10-word callback ask under rush. It also covered a Gujarati switch, where the agent kept the meeting ask in Gujarati.
- **Plan only in the initial `agent_variables`: 23/28.** Personalisation dropped to **0/2** (a generic "more buyer enquiries"). The "already have leads" playbook dropped to **0/2**. Price replies grew from 22–26 to 31–37 words. One off-plan line appeared: "I'm only an AI assistant and don't know exact prices." Safety held mostly because it also lives in the base prompt.

The mechanism is simple: **our tool response overwrites `persona_directive`, and the plan goes with it.** B3 therefore compiles the plan into a `plan_prefix` that the signal server prepends to every directive (`<plan> | Right now: <mode>`), keyed by `call_key`.

The cleaner alternative is a separate `@call_plan` agent variable that the tool never writes. That needs an agent-config change, and possibly Sarvam's "available on request" Code Tools. Ask on Day 1. Until then the re-send route is the proven one. Its per-turn token and latency cost has not been measured (ASSUMED small at plan sizes of a few hundred tokens).

**B3 I/O.** Input: `persona_spec.json`. Output: either the SDK `InteractionConfig` overrides or the Instant Outbound body, plus the signal-server call config. Every output is stamped with `spec_version`, so the switch log and B5 can attribute behaviour to a version.

## Block 4 switches live in code, because no LLM is fast enough to steer the current reply

**Why.** Switches are 25% of the score. FAQ Q3 says "a pre-scripted switch that cannot respond to what the seller says will score lower" ([PS04 doc](../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)). Timing is the hard part:

- **After the first rush cue only about two seller turns remain**, and 17.2% of first rush cues fall on the seller's last turn (PROVEN, PS07 lexicon proxy) ([between-run report](Between%20run%20learning%20loops.md)).
- **A synchronous Jev call would push replies to ~2.6 s typical, with 3.5–4.9 s tails** (PROVEN) ([system design](../../wiki/projects/vani-hackathon/system-design.md)).

**How.** The switcher has three layers, all frozen for the duration of a call:

- **Lexicon now.** A Devanagari-plus-romanised lexicon with NFD normalisation decides the directive for the current reply in under 5 ms.
- **Jev next turn.** Jev runs asynchronously, one decision per signal, and its verdict applies at the next tool call. It agreed with labels on 49/51 romanised items at ~480 ms (PROVEN, romanised only).
- **Policy in code.** A pure function with hysteresis, priority and **at most two switches** per call owns every switch decision.

Nothing learns mid-call, and no LLM decides a switch (team decision, DOCUMENTED) ([learning loops](../../wiki/projects/vani-hackathon/learning-loops.md)). Voice and pace cannot change mid-call. Live switches therefore act on wording, brevity, tone, language and *the plan*. A rush switch cuts the remaining plan to the callback offer. A confusion switch replays the current step in simpler words.

**What the new spikes change in B4.** Four measured facts reshape it (all PROVEN, [plan-stress spike](../../raw/research/2026-10-08-plan-stress-spike.md)):

1. **Sarvam's built-in language switch works (6/6 turns), but our tool is not called on the switch turn (tools = [] on 4/4).** The switch log must capture language switches from the transcript's language or script field, with source `sarvam_builtin`. We cannot rely on the tool for this. That means a trace-side detector, which B5 also needs.
2. **The lexicon produced a real false positive.** "Phir se pooch raha hoon, price batao…" ("I'm asking again, tell me the price") was tagged *confused* on the cue "phir se" in 4/4 runs, and the agent added "is this clear?". In context, "phir se" (again) is insistence, not confusion. The cue needs a context guard, for example when it co-occurs with a price demand. It is also exactly the kind of negative example the B5 reviewer should feed back.
3. **About 17% of turns (≈8 of 46) show restarted or duplicated replies.** On these turns a tool call often arrived *before* the seller finished speaking (−0.7 s, −2.0 s), and 2–4 separate agent speech bursts followed. It also happened on a turn with no tool call at all. Our working hypothesis is that Sarvam closes the seller's turn early at a mid-utterance pause and then restarts. The double tool call would be a symptom, not the cause. This is unconfirmed: there has been no audio review and endpointing settings are untested.
4. **The tool fires 6–7 times per call for 4 seller turns** (partial plus full utterance) ([plan-following spike](../../raw/research/2026-10-08-plan-following-spike.md)).

B4 must therefore be **idempotent per utterance**. The same turn arriving twice must not count as two signals or spend two of the switch budget. Make the decision on the longest utterance seen for that turn (ASSUMED design). The restart artefact is a voice-experience risk (the deck scores 20% on voice experience), not only a switching one.

**B4 I/O.**

| | Contents |
|---|---|
| Input per tool call | Seller utterance (Devanagari ASR), `call_key`, the timestamp; call config from B3; cached Jev verdict for the previous turn |
| Input per turn (trace side) | Transcript language or script field, for built-in language switches |
| Output to Sarvam | `persona_directive` = `plan_prefix` + "| Right now: <mode directive>", plus `seller_mode`. Sent on every tool call, switch or not. |
| Output to log | Switch-log row `{call_id, turn, signal, source: lexicon/jev/sarvam_builtin, change, reason, plan_step, switch_no, versions}` (deliverable 4) |

## Block 5 learns between runs by editing our tables, never model weights

**Why.** PS04 never scores "learning", but learning feeds three scored criteria: switches (better cues and thresholds), fit (per-seller memory) and evidence (tiered rules with n). The deck's robustness criterion asks for validation on real data. PS07's **12,788 transcribed calls** replay as runs for detection and timing. Replay cannot show that a switch *caused* a better outcome, because PS07 used one voice and one style (PROVEN counts) ([between-run report](Between%20run%20learning%20loops.md)).

**How.** Every run produces a trace: turns, tool calls, switch log, `spec_version` and outcome. An offline reviewer LLM then labels three things:

- the true signal and its onset on each turn;
- each switch, as correct, late, missed or false;
- each persona and plan element, as fit, misfit or no-evidence. Voice gender defaults to `no_evidence`.

A label is accepted only on **two keys**: the reviewer and Jev agree, or a human confirms. Corrections land in four places:

| Store | What changes | Gate |
|---|---|---|
| `lexicon` and `θ` | Lexicon cues (e.g. a context guard on "phir se") and per-signal, per-script thresholds | No per-signal regression on the frozen gold set; empty flip list |
| `rules` | Re-tiered or new rows | n ≥ 200 and the time split; human approval |
| `library` | Opening and objection moves added or retired | Supported by the switch log and outcomes |
| Per-seller memory | Enumerated tags only (e.g. `rushed`, `lang=gu`) | Applies to that seller's next call; no global gate |

Every edit bumps a version recorded in the manifest, and rollback is a repoint. The reviewer sees real transcripts, so it runs on the **internal LiteLLM gateway or the Sarvam LLM, with numbers and names masked**, and needs an organiser ruling first (ASSUMED, flagged).

The honest arithmetic is that two event days yield 30–60 reviewed runs. **No never-varied setting, voice gender included, can leave GUESS tier in that time.** Most of the real learning comes from PS07 replays, and the pitch should say so ([between-run report](Between%20run%20learning%20loops.md)).

**B5 I/O.** Input: traces, reviewer JSON, the frozen gold set and canaries. Output: `rules_vN+1`, `library_vN+1`, `lexicon_vN+1`, `thresholds_vN+1`, the updated memory store and a manifest that includes rejected diffs. B1 reads the new rules and memory on the next run, B2 the new library, and B4 the new lexicon and thresholds.

## Devil's advocate: where this design is weakest

**"A is just a lookup table. Where's the AI?"** The steelman is real. Judges may read a rules engine as unsophisticated, and the team lead was right that generation leaders do not ship pure code. But leaders also do not ship free agents. The industry pattern is code for structure and safety, an LLM grounded in a library for wording, and a check before use (DOCUMENTED) ([industry notes](../research_notes/Persona%20generator%20architecture/industry_practice.md)). The answer on the slide: the rules are *mined* from past calls with tiers, the LLM writes native-language openings, memory makes each persona unique, and the tables improve between runs.

**A's 23/23 is circular.** The decision labels came from the same toy rule table A implements. It proves the code is correct, not that the rules are good. **The real rule table does not exist yet**; it must be mined from PS07 before the slide claims "evidence-backed". The test set was 6 synthetic sellers at one temperature, so there is no variance estimate.

**Gender distinctness is in tension with fit.** The fix proposed for A's all-female output includes alternating gender by a seller hash. That gives *identical* sellers different voices, which is manufactured distinctness, and it breaks "identical sellers get identical levels". Prefer a timbre target derived from warmth and pace, which varies with real features, and use a hash only as a tie-break. Keep every gender choice at GUESS. Never infer the seller's gender, and never tie voice gender to category, region or turnover ([learning loops](../../wiki/projects/vani-hackathon/learning-loops.md)).

**The plan re-send makes the signal server a single point of failure.** If the server is down or slow, the agent loses the plan on the first tool call, as condition V showed. A separate non-overwritten `@call_plan` variable removes that dependency and is worth a Day-1 ask.

**Off-premises data is not solved by choosing Sarvam.** Claude Code and OpenRouter on real seller files are clearly off premises. Even the Sarvam LLM wording call and in-call Jev (on OpenRouter) send text out. In the live demo the "seller" is a teammate, but PS07 replays through Jev or a reviewer would ship real seller text. Use synthetic or masked data until organisers rule.

**Personalisation may not pay.** IndiaMART's three static-personalisation trials did not beat control (PROVEN) ([between-run report](Between%20run%20learning%20loops.md)). Deliver it because PS04 requires it, keep it short, and claim no meeting lift.

**The 17% restart rate could undercut the voice demo** more than any persona choice. If it is endpointing, the fix belongs in Sarvam settings, not in our blocks.

**Over-scope, in cut order:** an LLM-judge critique loop, similar-seller vector retrieval, GEPA prompt evolution, Claude as the production generator, and a dashboard. None maps to a PS04 deliverable that A plus the rule miner does not already cover.

## Day-1 open questions

| # | Question | Decides |
|---|---|---|
| 1 | Can a separate agent variable (e.g. `@call_plan`) persist untouched by the tool response, or can Code Tools be enabled? | Whether the plan re-send through the signal server stays mandatory |
| 2 | What are Sarvam's endpointing and interruption settings, and do they explain the ~17% restarted replies? | Voice-experience risk; B4 deduplication |
| 3 | Does sending seller data to the Sarvam LLM, the internal gateway, OpenRouter (Jev) or Claude count as leaving premises? | Whether B2's wording call, B5's reviewer and replay-through-Jev may touch real data |
| 4 | Are per-session pace and pitch honoured on v4 speakers (T9), and is pitch audible? | Whether pace and pitch are settings at all, or wording only |
| 5 | Can one committed `app_version` per voice profile be dialled via Instant Outbound? | Phone-path voice distinctness |
| 6 | Which sellers are "every sample seller"? | B2 batch size; test split |
| 7 | Does "personalisation" mean tailoring plan content with this seller's data, as we read it? | Plan field design |
| 8 | Is a third-party agent runtime, or libraries such as IndicXlit or GEPA, acceptable under "no pre-built"? | Whether any agent appears in the build story |
| 9 | Does Bulbul pronounce Hinglish better in Devanagari or Roman script? | The wording script rule; one validator |
| 10 | Did any historical VANI version use a different voice gender? | Whether gender can ever leave GUESS tier |

## Conclusion

Each block is easiest to justify by what Sarvam does with its inputs. Sarvam fixes voice at call start, so delivery is decided once, before the dial. It overwrites the directive each turn, so the plan has to ride every turn. It switches language on its own without calling us, so the switch log has to read the transcript. It cannot let us bring our own LLM, so our "intelligence" has to live in what we feed it. That moves the agent-or-script question away from the generator and onto the platform boundary. The generator is the easy part: rules plus one call, measured, cheap and auditable. The risks that remain are integration risks: plan persistence, endpointing restarts, phone-path voice limits and data-residency rulings.

The second shift is about where "learning from other sellers" lives. It is not a retrieval step at generation time. It is a table mined offline from every seller, tiered by evidence and versioned by the between-run loop. That one table serves the evidence criterion, the reasons in every spec and the gate that stops the loop from drifting. A judge who asks why a seller got a slow pace should be shown a rule id, its n and its tier. Retrieved neighbours or an agent's chain of thought would not answer the question as well.
