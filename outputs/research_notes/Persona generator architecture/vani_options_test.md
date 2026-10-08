# VANI persona generator (B2): options A / B / C prototype test (as of 2026-10-08)

Tags: **PROVEN** = measured in this session on 6 made-up sellers. **DOCUMENTED** = vendor docs or earlier in-repo notes. **ASSUMED** = my inference.
No real seller data was used. All 6 sellers, the evidence table and the playbook library are synthetic. Code and every raw output are in the session scratchpad: `C:\Users\Imart\AppData\Local\Temp\claude\c--Users-Imart-Voice-ai-hakethon\7fe43865-4d71-4384-8f55-50d061623b41\scratchpad\pg\` (`data.py`, `validators.py`, `gen.py`, `metrics.py`, `expected.py`, `compile_payload.py`, `out/*.json`, `cc/*`). Hereafter "[pg]" = that folder.

**Bottom line:** build **A**. Rules (code) choose every setting, with its rule id, tier and confidence. One Sarvam `sarvam-105b` call (reasoning off) writes only the spoken wording. Code validators run on the result. One bounded repair call runs only when wording fails a check. On the same 6 sellers:

| Option | First-try pass | Rule decisions applied correctly | Latency per seller | Cost per seller |
|---|---|---|---|---|
| A | 6/6 | 23/23 (matches by construction) | ~1.0 s | ~₹0.017 |
| B | 0/6 | 16/23 | ~4.2 s | ~₹0.16 |
| C | 4/6 after ≤2 revisions | still 17/23 | ~7.6 s | ~₹0.30 |

The LLM in B and C wrote validator-clean specs with *wrong* rule decisions and false reasons, and no code validator can catch that. Claude Code headless got 9/9 decisions on 2 sellers, but it costs ~$0.18 per seller, takes ~24 s, and sends seller data to an outside vendor.

## Q1. Sarvam LLM and Claude Code: what is available

### Takeaway
On the chat API, `sarvam-105b` is the only Sarvam model ID plus its `-conversations` variant. It offers strict json_schema, tool calling and 128K context. In practice its strict json_schema mode fell into whitespace loops on our nested schema in 4 of 6 calls. `claude` 2.1.292 is installed on this machine, and headless `claude -p --output-format json` works.

### Cited Findings
- **Models (DOCUMENTED):**
  - V1 `/v1/chat/completions` lists `sarvam-105b`, described as "Flagship model … 128K token context length". It also lists `sarvam-105b-conversations`, a "conversational variant post-trained for real-time dialogue and voice-agent workloads" with 32K context.
  - "Sarvam-M (24B) has been deprecated".
  - V2 (beta) lists `sarvam-105b`, `glm5.3`, `gemma4` and `deepseekv4-flash`.
  - Source: [Sarvam chat completion overview](https://docs.sarvam.ai/api/chat-completion/overview).
- **sarvam-30b and pricing (DOCUMENTED, earlier in-repo note citing the changelog):** sarvam-30b was deprecated on 2026-08-18. Price is ₹29.28 per 1M input tokens, ₹10.98 per 1M cached input and ₹73.2 per 1M output. — [sarvam_platform_internals.md](../VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md); [Changelog 2026-08-18](https://docs.sarvam.ai/changelog/2026/8/18)
- **Structured output (DOCUMENTED):** `response_format` json_schema with `strict`: "output is constrained to match the JSON Schema you supply". `json_object` mode also exists. Tool calling is supported (`tool_choice` auto/none/required/named). Thinking is "on by default"; pass `reasoning_effort: null` to disable it. Usage returns `prompt_tokens`, `completion_tokens` and `reasoning_tokens`. — [Sarvam overview](https://docs.sarvam.ai/api/chat-completion/overview); [Chat completions v2 reference](https://docs.sarvam.ai/api-reference/chat/chat-completions-v2.md)
- **Strict json_schema in practice (PROVEN):**
  - Setup: our full spec schema (14 fields × 6 meta keys, nested, `additionalProperties:false`), with `reasoning_effort: null`, temperature 0.2 and max_tokens 4000.
  - 4 of 6 calls hit the 4000-token limit by emitting blank lines after the `delivery` block, so the JSON was invalid.
  - One inspected failure took 16.7 s and used 4,000 completion tokens.
  - The 2 calls that parsed took ~2.5 s each. One passed all validators; the other failed one gate.
  - Source: [pg] `out/Bstrict_*.json`, `out/raw_B_SYN-06.txt`.
- **json_object mode (PROVEN):** the JSON always parsed (6/6), but without the schema the model drifted from the shape:
  - With no output skeleton in the prompt, it invented its own shape (`{"persona_spec": {"seller_id": {...}, "company_name": {...}}}`).
  - With a skeleton, it dropped the per-field reason/rule/tier wrapper on plan fields in 6/6 cases.
  - Source: [pg] `out/raw_var_json_object.txt`, `out/B_*.json`.
- **Latency with reasoning off (PROVEN):** wording-only calls (A) took 0.89–1.21 s (mean 1.05 s), with ~218 prompt and ~145 completion tokens. Full-spec calls (B) took 3.9–4.6 s, with ~3,016 prompt and ~951 completion tokens. `reasoning_tokens` was 0 in every call. Source: [pg] `out/A_*.json`, `out/B_*.json`.
- **Claude Code (PROVEN):**
  - `claude --version` reports `2.1.292 (Claude Code)`.
  - Two headless runs (`claude -p … --output-format json --max-turns 14 --allowedTools Read Write Bash(python:*)`) each completed in 4 turns, ~24 s wall time and $0.183–0.187, using model `claude-sonnet-5-5` (plus a tiny `claude-haiku-4-5` side call).
  - Source: [pg] `cc/cc_SYN-03.json`, `cc/cc_SYN-06.json`.

### Inferences
- ASSUMED: Sarvam strict mode looks like it doesn't constrain whitespace between tokens. A flatter schema, a lower max_tokens or `json_object` plus code validation is safer. Option A's small 2-key wording schema never failed (6/6).
- ASSUMED: `sarvam-105b-conversations` has a 32K context, and B's ~3K-token prompt fits, but there's no reason to use it for offline generation.

### Gaps
- Sarvam API rate limits and concurrency for batch generation weren't found on the overview page (it links to a Rate Limits page I didn't fetch).
- Whether Sarvam strict mode is true grammar-constrained decoding is still undocumented. The behaviour I saw suggests it is partial.

## Q2. persona_spec.json schema and code validators

### Takeaway
A flat, two-section spec in which every field carries the same six meta keys can be checked with ~150 lines of Python, and the checks are useful. They caught wrong shapes, digits in spoken text, invalid speakers, citations of fields the seller file doesn't have, and inflated confidence. They **cannot** catch a wrong rule decision that is well-formed, such as "pace normal (DEFAULT)" for a seller who was confused 2 days ago. That needs a rule-consistency check, which is just the rules engine again.

### Cited Findings (PROVEN, [pg] `validators.py`, `data.py`)
- **Spec shape.**
  - `{seller_id, delivery{voice_gender, speaker, language, pace, pitch, formality, warmth, brevity}, plan{opening{move_id,text}, steps[], personalisation[{field,line}], objection_order[], escalation[], guardrails[]}}`.
  - Every field is `{value, reason, cited_fields[], rule_id, tier, confidence}`.
  - Levels: pace slow/normal/fast; pitch, formality and warmth low/medium/high (pitch normal/low/high); brevity short/medium/long.
  - Language is one of Hindi, Hinglish, Gujarati, Marathi, English, Tamil.
  - Move, step and escalation IDs come from the approved library.
- **Validators.**
  1. Schema and enums.
  2. Every `cited_fields` path resolves to a non-null field in the seller file (a missing field must use rule `DEFAULT`).
  3. `rule_id` exists in the rule table, and `tier` equals that rule's tier, so tiers can't be inflated.
  4. Spoken text (opening and personalisation lines) has no digits in Latin, Devanagari, Gujarati or Tamil script, and no ₹/Rs/lakh/crore/%/discount/free/guarantee (or their Hindi equivalents).
  5. No internal labels such as `bot_question` in spoken text. I added this after A produced "Earlier, we received a bot_question."
  6. Gates: steps start with GREET_CONFIRM_OWNER and end with CONFIRM_AND_THANK or OFFER_CALLBACK; escalation includes E_HUMAN_ON_REQUEST; guardrails equal exactly {GATE_DNC, GATE_AI_DISCLOSURE_ON_ASK, GATE_DELIVERY_NOT_FACTS, GATE_NO_PRICE_QUOTE}; DNC sellers get no spec.
  7. `speaker` is a Bulbul v4 voice tagged for the chosen language (Hinglish uses Hindi voices), and its gender matches `voice_gender`. The voice list is built from the 176 v4 entries in [voice catalogue](../../../raw/research/2026-10-07-sarvam-voice-catalogue.json).
  8. `confidence ≤ min(tier cap, completeness)`, with tier caps STRONG 0.9, MODERATE 0.7, WEAK 0.5, GUESS 0.3. Completeness is the share of 8 core fields present (GATE fields are exempt). The tier ladder follows [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md).
- **Extra metrics (not pass/fail).**
  - *Invented facts:* banned tokens in speech, history references for a seller with no history, another seller's city or category, personalisation on an absent field.
  - *Rule misattribution:* the rule cited for a field doesn't set that field (e.g. formality ← R03 "rush").
  - *Decision hits:* 23 hand-labelled key decisions across the 6 sellers, taken from the rule table's text (e.g. SYN-03 confused 2 days ago → pace slow, CONFIRM_UNDERSTANDING step).
- **Voice-catalogue fact (PROVEN, from the catalogue file).** v4 has 57 female and 32 male Hindi voices; 38 female and 18 male English; 6 female and 3 male Marathi; 2 female and 1 male Gujarati; Tamil has 3 male and no female.

### Inferences
- ASSUMED: words for numbers slip through the digit check (A wrote "do minute", i.e. "two minutes"). That's harmless for a time ask, but a price in words would also pass. Add number words in Hindi, Gujarati, Marathi and English to the banned list for price contexts, or let only the library hold any number.
- ASSUMED: add a script check, e.g. Hinglish must be in Devanagari if Bulbul pronounces it better. A wrote Hinglish in Roman script in 3 of 3 cases despite being told to use Devanagari. B and Claude used Devanagari.

### Gaps
- How Bulbul v4 handles Romanised versus Devanagari Hinglish wasn't ear-tested here.
- The Bulbul v4 speaker ID format is ASSUMED to be the lower-cased catalogue name; two catalogue entries share the name "Aditya".

## Q3. Prototype results: A vs B vs C (6 synthetic sellers)

### Takeaway
A is the only option that is valid on the first try, correct on rule decisions and cheap. B and C reach validity only through repair, and they make ~30% wrong rule decisions with confident wrong reasons. A's weakness is distinctness on **voice gender**: the coverage rule picks Female for every language. Code should fix that, not an LLM.

### The test sellers (all made up, shaped like PS07 seller files)

| ID | Profile | History | Language | Missing |
|---|---|---|---|---|
| SYN-01 | Manufacturer, ₹5–25 Cr, Indore | 3 days ago: Not Interested, price objection, rushed | Hindi | none |
| SYN-02 | Wholesaler, Surat | 10 days ago: Meeting Fixed, interest | Gujarati | none |
| SYN-03 | Retailer, under ₹40 L, Nashik | 2 days ago: callback, "already have leads", confused | Marathi | none |
| SYN-04 | Exporter, ₹25–100 Cr, Chennai | asked "is this a bot", switched to English; older trust objection | English | none |
| SYN-05 | Trader, Lucknow, zero logins | first call | Hindi | none |
| SYN-06 | Manufacturer | 60 days ago: Not Interested, busy | — | turnover, city, state, language, engagement (completeness 0.38) |

The evidence table has 12 rules (R01–R12) plus DEFAULT and GATE, each with a tier and a toy n. The library has 5 opening moves, 6 objection moves, 9 step IDs and 4 escalation IDs. Source: [pg] `data.py`.

### Results (PROVEN, [pg] `metrics.py`, `expected.py`, `out/`)

| Metric | A: rules + 1 wording call | B: 1 structured call (json_object + skeleton) | B-strict (json_schema strict) | C: B draft + ≤2 validator-driven revisions | C via Claude Code `-p` (2 sellers) |
|---|---|---|---|---|---|
| Validator pass, first try | **6/6** | 0/6 | 1/6 (4/6 invalid JSON) | 0/6 (same drafts as B) | 2/2 (4 turns; ASSUMED one validate pass) |
| Pass after revision | — | — | — | 3/6 after 1, **4/6 after 2** | 2/2 |
| Remaining failures | — | plan fields missing meta (6/6), "2 मिनट" digit, speaker given as "pooja (Female)" | — | speaker string "pooja (Female): A warm…"; steps gate | — |
| Invented facts (detector) | 0 | 1 (digit in opening) | 0 | 0 | 0 |
| Rule misattributions | 4 (my rules code cites R03/R04/R12 for steps/escalation) | 2 | 1 | 1 | 6 (cites R12 for pace/brevity/steps) |
| **Key rule decisions correct** | **23/23** (matches by construction: labels and rules come from the same table) | 16/23 | 7/9 | 17/23 | **9/9** |
| Wrong decisions | — | SYN-03 pace normal and formality medium (confused 2 days ago); SYN-04 opening "follow-up meeting" (never had one) instead of AI disclosure, formality medium; SYN-06 "re-engage" for a 60-day-old NI; SYN-02 warmth medium; SYN-06 confidence not low | SYN-04 Hinglish (last call English), re-engage opening | same as B except SYN-06 confidence fixed | — |
| Mean audible settings differing per pair (of 8) | 3.93 | 4.47 | — | 4.20 | — |
| Minimum per pair / pairs with <2 differences | 2 / 0 | 2 / 0 | — | 2 / 0 | — |
| Plan elements differing per pair (of 4) | 2.80 | 2.87 | — | 2.80 | — |
| Distinct voice genders / speakers | **Female only** / 6 | M+F / 4 ("aayan" ×3) | — | M+F / 4 ("aayan" ×3) | — |
| Spearman: seller-feature distance vs persona distance (15 pairs) | **0.82** | 0.48 | — | 0.52 | — |
| LLM calls per seller | 1 | 1 | 1 | 1.5 | 1 session (4 turns) |
| Latency per seller | 1.05 s | 4.19 s | ~2.5 s when it parsed; 16.7 s on a whitespace loop | 7.6 s | ~24 s |
| Tokens per seller (in / out) | 218 / 145 | 3,016 / 951 | 921 / 532 (parsed only) | 6,230 / 1,616 | ~164K cache-read+write / ~2.9K out |
| Cost per seller | ₹0.017 | ₹0.158 | — | ₹0.30 | $0.18 |

- **Example of a false reason the validators can't catch (B and C, SYN-03):** pace `normal`, with the reason "No specific pace rule was triggered by the past call outcome or signals" and rule DEFAULT. The seller file says confusion on a call 2 days ago, so R04 should apply. Source: [pg] `out/C_SYN-03.json`.
- **A wording quality:** openings were natural and named the right company in all 6 cases, in Hindi, Gujarati, Marathi and English. Defects:
  - One leaked label ("Earlier, we received a bot_question.").
  - One grammar slip ("kya aap … se baat kar rahi hoon").
  - Hinglish in Roman script.
  - Source: [pg] `out/A_*.json`.
- **Claude Code wording (SYN-03, SYN-06):** native Devanagari Marathi and Hindi. On SYN-06 it acknowledged the earlier "busy" correctly without inventing anything. Source: [pg] `cc/spec_*.json`.

### Inferences
- ASSUMED: putting the decisions in code is what makes A both correct and *tracking*. Persona distance follows seller distance at ρ 0.82 in A versus ~0.5 in B and C. That is the property PS04's 20% distinctness and 25% fit criteria reward, and FAQ Q1 ("persona per seller") is still met, because the levels come from each seller's own fields.
- ASSUMED: the LLM options look more distinct on raw differences (4.47 vs 3.93 settings per pair) partly through noise, e.g. a random pitch of "high" or "low". Their distinctness doesn't follow seller differences as well.
- ASSUMED: C's repair loop fixes *form* errors and doesn't fix *judgement* errors (16 → 17 of 23). That matches the earlier literature note: repair works when there is a reliable external check ([llm_architectures.md](llm_architectures.md)). There is no such check for "did you apply R04", short of re-running the rules.
- ASSUMED: Claude (Sonnet 5.5) applied the rule table correctly on the 2 hardest sellers, where Sarvam-105B did not. With n=2 that is suggestive only.
- **Fix for A's gender collapse (ASSUMED design):** choose gender by a deterministic rule that varies with seller data and catalogue coverage. Examples: for languages with both genders, alternate by a seller-data hash; keep a per-seller memory override; Tamil is male-only. Tag every gender choice GUESS, as [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md) already says.

### Gaps
- n=6 synthetic sellers, one run each, temperature 0.2. There's no variance estimate.
- C's "retrieve similar sellers first" variant wasn't tested.
- The decision labels come from the same rule table A implements, so A's 23/23 confirms the code is correct; it isn't independent evidence that the rules are good.
- No audio was generated, so audible distinctness is inferred from settings, not ear-tested.

## Q4. Recommendation, scale and cost, Sarvam payload, between-run learning

### Takeaway
Build A, with a repair call only for wording that fails validation, and fall back to a hand-written template when the repair also fails. Run it in batch. It costs ~₹2.5K and ~2 h at 20-way concurrency for 149K sellers, against ~₹45K and ~16 h for C. A spec compiles mechanically into the Sarvam SDK overrides and the signal-server config. Learning between runs edits the rule table, the library and per-seller memory; it never edits the LLM.

### Cited Findings
- **Cost and time at scale (PROVEN tokens × DOCUMENTED price; concurrency ASSUMED):**
  - A: ₹0.017 per seller, ~₹2.5K for 149K sellers, 43.5 h serial or ~2.2 h at 20-way concurrency.
  - B: ₹0.158, ~₹23.5K, ~8.7 h at 20-way.
  - C: ₹0.30, ~₹45K, ~15.7 h at 20-way.
  - Claude Code: $0.18 per seller, ~$27.6K for 149K, ~51 h at 20-way.
  - The demo sample (2–3 contrasting sellers, plus "one spec per sample seller") is a few dozen calls for any option.
  - Source: [pg] `metrics.py` output; [sarvam_platform_internals.md](../VANI%20adaptive%20persona%20architecture/sarvam_platform_internals.md) for price.
- **SDK per-session overrides (DOCUMENTED, spike log):** `text_to_speech_config{speaker_id|speaker_name, speech_settings{pitch,pace,volume}}`, `initial_bot_message`, `initial_language_name`, `agent_variables`. Instant Outbound has **no TTS override**, so on the phone the voice comes from `app_version`. — [2026-10-07-spike-log](../../../raw/research/2026-10-07-spike-log.md)
- **The agent follows a plan passed in (DOCUMENTED, earlier spike):** 15/16 plan checks passed, and the scripted opening was spoken word for word. — [plan-following spike](../../../raw/research/2026-10-08-plan-following-spike.md)
- **Compile step (PROVEN that it runs; acceptance by Sarvam not tested):** `compile_payload.py` maps a spec to:
  - `initial_bot_message` = opening text;
  - `initial_language_name` (Hinglish → Hindi);
  - `text_to_speech_config{speaker_name, speech_settings{pace: slow 0.9 / normal 1.0 / fast 1.1}}`, with pitch left out until it's shown to be audible;
  - `agent_variables{seller_mode, persona_directive = plan text + "| Right now: …", plan_steps, objection_order, formality, warmth, brevity}`;
  - plus a signal-server config `{seller_id, spec_version, plan_prefix, base{language,formality,warmth,brevity,pace}, escalation[], max_switches: 2, rule_trace{field: rule/tier}}`.
  - Source: [pg] `compile_payload.py`, run on `out/A_SYN-01.json`.
- **Learning levers (DOCUMENTED design):** per-seller memory has the strongest evidence (next-call meeting AUC 0.71 vs 0.58 for profile). Rules are tiered by n, CI and a time split, and no model is trained. — [learning-loops](../../../wiki/projects/vani-hackathon/learning-loops.md); [persona_learning.md](../Between%20run%20learning%20loops/persona_learning.md)

### Inferences (ASSUMED design)
- **Build order (about 6–8 dev-hours):**
  1. `features(seller_file)` and completeness.
  2. `rules()` → levels plus rule_id, tier and confidence, as in [pg] `gen.py::rules`, ~150 lines.
  3. A templated wording fallback per language (a demoable spec with no LLM).
  4. The Sarvam wording call with a 2-key schema.
  5. Validators.
  6. One repair call on failure, then the template.
  7. `compile_payload`.
  8. A distinctness report (ρ plus pairwise differences) for the slide.
- **Where an LLM may still decide something:** nowhere in the per-seller path. If the team wants "agentic" on the slide, use the LLM *offline* to propose candidate rules from aggregates, with code computing n, effect and tier ([llm_architectures.md](llm_architectures.md) Q3).
- **How learning edits the generator (no training):**
  1. *Rule table:* a reviewer finding pooled across runs adds a row, re-tiers one or retires one, gated on the frozen test set.
  2. *Library:* add or retire opening and objection moves that the switch log and outcomes support.
  3. *Per-seller memory:* last-call outcome, signals and language become inputs to `rules()` with a recency weight. Rush, confusion and language are already wired as R03, R04 and R07 on the toy table.
  4. *Wording prompt:* optionally keep the best-scoring exemplar per language. Each edit bumps `spec_version`, which lands in the signal-server `rule_trace` and the switch log, so v0→v1 diffs are visible per seller.
- **Phone path:** A gave 6 different speakers across 6 sellers. On Instant Outbound each (speaker × pace) needs its own `app_version`, so collapse to ~3–4 published voice profiles per language for phone, and keep full per-seller voice on the SDK demo.

### Gaps
- Whether Sarvam honours `speech_settings.pace` and pitch on v4 per session (test T9 in the system design) is still unproven. If pace isn't honoured, pace has to come from wording.
- Sarvam API concurrency limits for a 149K batch are unknown.

## Q5. Devil's advocate: the 2-day build and PS04 scope

### Takeaway
PS04 deliverable 1 is "working code that takes a seller file as input and outputs a persona". A satisfies it with the least moving parts. Claude Code as the generator runtime is a scope and compliance risk, not a quality win worth its cost.

### Cited Findings
- Deliverable 1 requires "working code that takes a seller file as input and outputs a persona". Deliverable 2 requires "one spec for every sample seller" with "the reason for each choice". FAQ Q6 requires lower confidence for missing fields. — [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)
- Rules: no customer data may leave the premises; pre-built solutions are disqualified; the core agent must be Sarvam; no new outside vendors. — [persona-requirements](../../../wiki/projects/vani-hackathon/persona-requirements.md); [AGENTS.md](../../../AGENTS.md)
- Distinctness 20%, fit 25% and evidence 15% are scored. Switches (25%) and voice (15%) are the live demo. — [PS04 problem doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md)

### Inferences (ASSUMED)
- **Claude Code / Agent SDK as the runtime generator.** It was the best decision-maker here (9/9), but:
  1. Real seller files would go to Anthropic, an outside vendor and off premises. Use it only with synthetic data or an organiser ruling.
  2. "Working code: seller file in → persona out" is weaker if the core is a prompt to a general agent. Judges may read the Claude-skill route as "the logic is the model's", which brushes against the pre-built rule.
  3. At $0.18 and 24 s per seller it doesn't scale to 149K.
  4. Claude Code is a fine **build tool** (writing `rules()`, mining rules, reviewing runs). It shouldn't be the per-seller runtime.
- **OpenRouter as the wording LLM:** permitted infra, but seller data off premises has the same issue. Sarvam keeps the "core is Sarvam" story and stays in-infra.
- **"A is just a lookup table, so where's the AI?"** Answer on the slide: the evidence-tiered rules are mined from past calls (the 15% evidence criterion), the LLM writes native-language openings, per-seller memory makes each persona unique, and the rule table updates between runs. Distinctness tracks seller differences (ρ 0.82 on the synthetic set).
- **Don't build C for the hackathon.** It added ~6.5 s and ~₹0.28 per seller for +1 correct decision out of 23. A bounded repair on A's wording call keeps the useful part of C.
- **Over-scope flags:** a similar-seller retrieval step, an LLM critic, GEPA prompt evolution, and Claude-as-generator in production are all outside what PS04 scores. Cut them first.
- **Risk in A:** the hand-written rules are only as good as the evidence table. The toy table here is made up, and the real one must be mined from PS07 aggregates with tiers before the slide claims "evidence-backed".

### Gaps
- No organiser ruling yet on sending real seller data to any LLM, including Sarvam.
- Pace and voice audibility haven't been ear-tested, so the demo's distinctness may be smaller than the settings suggest.
