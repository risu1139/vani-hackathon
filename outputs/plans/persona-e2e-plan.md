# VANI persona: end-to-end plan (from seller data to the Sarvam call, the learning loops, and the tests)

Date: 2026-10-10. Status: DRAFT for your approval. Language: ASD-STE100.

It builds on these files:
- `outputs/plans/persona-skill-design.md`: facts, guards, gates, the hierarchy and the loops;
- `.claude/skills/vani-persona/references/`: the formats, the evidence, voice and language;
- the team decisions in `raw/hackathon/2026-10-09…10-*.md`.

Rule for this plan: we build nothing before you approve it. A Sarvam call (credits) needs your approval each time.

## 0. The chain, from one end to the other

```
GLID
 └─ S0 builder (laptop, VPN)          → data/contexts/<glid>/ (INDEX, core, topic files, calls/, context.json)
     └─ S1 facts.py (script)          → facts.json Part A: traits, states, hooks (eligibility), guards
         └─ S2 prior.py (script)      → prior.json: top-2 personas (scoreboard A) + voice prior (scoreboard B), with probabilities
             └─ S3 agent (skill, Daytona) → review Part B + persona.json (persona spec with cited reasons)
                 └─ S4 validate_persona.py (gate) → pass / list of failures
                     └─ S5 compile_vars.py (script) → sarvam_vars.json (only from a validated persona)
                         └─ S6 Sarvam call (OnStart sets voice/pace/pitch/opening; prompt sections read variables)
                             └─ S7 in-call switch (keyword tool + prompt rules) → switch_log
                                 └─ S8 records + review → Loop 2 (scoreboards) and Loop 1 (switch)
```

## 1. From traits, states and hooks to the persona (S1 → S3)

**1.1 The script calculates (S1).** It produces traits, states, hook eligibility and guards, each with evidence ids (see the design file, sections 3–5a). The division goes into the INDEX key facts. The agent opens only its division reference (`division_nsd.md` or `division_csd.md`). TMW and KCD use CSD until you decide.

**1.2 The script gives a starting point (S2).**
- Scoreboard A gives the top-2 personas for the seller's path: division → turnover band → AOV tier → zone → state → category group.
- Scoreboard B gives the voice gender prior: seller gender → city tier → Hindi belt → tension.
- Both use Thompson sampling. `prior.json` stores the draw and the probability of each option, so that the loops can give credit correctly.

**1.3 The agent decides (S3, gated).** In this order:
1. Read INDEX.md and core.md. Deal with every true guard (do-not-call stops the run).
2. Review the traits and states that matter (Part B: accepted or corrected, relevance, implication), with cites.
3. Decide each eligible hook: primary / backup / rejected. Read its probe files; give at least 3 cites from at least 2 files, and counter-evidence.
4. Select one of the top-2 personas.
5. Amend dimensions only with cited reasons. Example: "pace 1.0 → 1.1 because `state.call_mood.rushed` (calls/C02.T3)".
6. Write the opening, the call plan and the objection order from the division reference and the facts.
7. If no persona fits: compose one and write a "new persona suggestion" for a human.

**1.4 The persona spec (`persona.json`): one value + reason + cites for each dimension.**

```json
{"decision_id": "...", "glid": "...", "division": "NSD", "prior": {"top2": ["P2", "P4"], "chosen": "P2", "draw_prob": 0.63},
 "voice": {"gender": "F", "voice_id": "...", "reason": "...", "cites": ["core.md#A07", "calls/C02#C02.T3"]},
 "pace": {"value": 1.1, "reason": "...", "cites": [...]}, "pitch": {...}, "language": {"start": "hi", "code_mix": "light", ...},
 "formality": {...}, "warmth": {...}, "sophistication": {...},
 "hook": {"id": "hook.money_lead", "claim": "...", "fact_ids": ["candidate_leads.md#CL-1"]},
 "opening": "...", "call_plan": [{"step": 1, "say": "...", "goal": "..."}],
 "objection_order": [...], "switch_sensitivity": {"rushed": "high", ...},
 "amendments": [{"dimension": "pace", "from": 1.0, "to": 1.1, "reason": "...", "cites": [...]}],
 "guards_ack": [...], "new_persona_suggestion": null}
```

## 2. From the persona to the Sarvam prompt (S5 → S6)

**2.1 One fixed Sarvam template, filled by variables.** It is built from the "Ananya" template (`wiki/projects/vani-hackathon/sarvam-prompt-template.md`) and the buyer-side VANI prompt pattern. The sections are:
- Greeting;
- Persona;
- Environment;
- Objective;
- Speaking Style;
- Facts;
- Phases;
- Live adaptation;
- Guardrails;
- Date resolution.

Division-specific text is inside `{% if division == "NSD" %}` blocks.

**2.2 Variable map (`sarvam_vars.json`): written by a script from the validated persona.**

| Variable | Filled from | Used by |
|---|---|---|
| `persona_voice_id`, `persona_pace`, `persona_pitch` | persona.voice / pace / pitch | OnStart tool (call start): voice gender + voice, pace, pitch (PROVEN) |
| `persona_voice_gender` | persona.voice.gender | template blocks for gendered Hindi grammar ("kar rahi / raha hoon") |
| `persona_language` | persona.language.start (regional unless high value) | OnStart `set_initial_language_name` (seen in the SDK; to test). Sarvam's built-in switch handles mid-call changes |
| `persona_opening` | persona.opening | OnStart → first line |
| `persona_style` | persona formality, warmth, sophistication, language, words per turn | Speaking Style section (never changed by the switch tool) |
| `call_plan` | persona.call_plan + objection_order | Phases section |
| `verified_facts` | the hook claim + the fact values the agent may say | Facts section |
| `division`, `seller_name`, `company_name`, `city` | facts | Greeting / Environment |
| `switch_sensitivity` | persona.switch_sensitivity | switch tool |
| `seller_mode`, `persona_directive`, `switch_log` | the switch tool, during the call | Live adaptation section |
| `decision_id` | the run | every log row |

**2.3 Every decided persona dimension stays per seller.** The template is fixed only as text structure. Voice gender, voice, pace, pitch, starting language, gendered grammar, formality, warmth, sophistication, code-mix, salutation, opening, hook, call plan and switch wording all change per call through the variables above. This follows the team decision "per-call persona values go through agent variables only" and the production buyer-side prompt pattern (variable-switched sections).

**2.4** A new persona never needs a new prompt. Only the variables change. The template changes only in a new version that a human approves.

## 3. In-call switching (S7)

- **Now (proven):**
  - the keyword code tool `ReadSellerSignal` sets `seller_mode` and `persona_directive` and writes `switch_log`;
  - the prompt has rules for each signal;
  - Sarvam's built-in language switch is on;
  - endpointing is set to "Patient";
  - pace changes through phrasing.
- **Per persona:** the directive text has a variant for each style. Example: "rushed" for a formal persona = one short polite sentence; for a warm local persona = one short friendly sentence. `persona_style` stays the same. The directive changes only how much VANI says and how.
- **Per seller:** `switch_sensitivity` from the states. Example: a seller who is often rushed switches on the first cue.

## 4. What we store (for training and for the loops)

`data/runs/<decision_id>/` (git-ignored; PII rules apply):

| File | Content | Used by |
|---|---|---|
| `00_input.json` | glid, as_of, the context folder hash, the builder version | reproducibility |
| `01_facts.json` | Part A (script) | audit, tests |
| `02_review.json` | Part B (agent), the read log | gates, Loop 2 (amendments) |
| `03_prior.json` | the scoreboard path, top-2, draw probabilities, the library version | Loop 2 credit |
| `04_persona.json` | the persona spec | Sarvam vars, slide, review |
| `05_sarvam_vars.json` | the variables sent | reproducibility |
| `06_call.json` | Sarvam interaction id, transcript, switch_log, duration, ended_by (from the Analytics API) | review, Loop 1 |
| `07_outcome.json` | meeting fixed (yes/no); later meeting held | Loop 2 |
| `08_review.json` | the QA review (Fatal / Non-Fatal), switch correctness, persona fit | both loops |
| `status.json` | always written: done / do_not_call / error / awaiting_input | the orchestrator |

Only aggregates go to `raw/` and `wiki/`.

## 5. The learning loops (between runs, never during a call)

- **Loop 2 (persona).** After each outcome, a script adds the result to every level of the path in scoreboards A and B. It scores against the default persona (uplift). It counts the amendments by outcome and suggests winners to a human. The library and the template change only with human approval.
- **Loop 1 (switch).**
  1. The review labels each seller turn.
  2. The script finds missed and wrong switches, and proposes keyword and directive-text changes.
  3. Each proposal runs on the gold set; it must not be worse.
  4. A human approves.
  5. A new tool and prompt-rules version is uploaded to Sarvam.

## 6. Test plan: test cases first, then build, at every stage

| Stage | What we test | Test cases (written before the code) | Pass criterion | Sarvam credits? |
|---|---|---|---|---|
| T0 builder | Folder complete; no PII; same output on rebuild | The 10 demo sellers + 2 synthetic fixtures (cold seller, seller with DNC) | All files present; PII scan clean; rebuild is byte-stable except timestamps | No |
| T1 facts.py | Each trait, state, hook and guard is correct | About 30 hand-made fixtures (for example: lapsed credits → `bl_usage=lapsed`; 3 calls in 7 d → `call_fatigue`; exec met 2 d ago → guard). Expected values are written first | 100% on the fixtures; a manual check of 3 demo sellers | No |
| T2 prior.py | The hierarchy and Thompson sampling behave | Synthetic scoreboards: empty → uses L0; a strong cell → wins; close cells → both get calls | Expected top-2 and probabilities within tolerance | No |
| T3 gates | Gates refuse bad output and stay quiet on good output | Stub agent outputs: missing cite, fake cite, unread probe file, no counter-evidence, a guard not acknowledged, a good one | Each bad case refused with the correct message; the good case passes | No |
| T4 skill on the laptop (`claude -p`) | The agent follows the steps; the persona is good | 3 contrasting sellers (NSD small rural, CSD lapsed credits, cold seller) + 1 DNC seller | Gates pass; DNC stops; a judge rubric (fit to facts, cited reasons, distinctness) ≥ 4/5; your review | No |
| T5 skill on Daytona | The same as T4 in the sandbox; status.json always written | All 10 demo sellers | 10/10 runs complete; personas distinct across sellers; your review of 3 | No |
| T6 Sarvam text/SDK session | The variables reach Sarvam; the opening and call plan are followed; the hook is used; switches fire | 3 sellers × scripted seller lines (cooperative, rushed, irate, language switch) | Variables applied (voice/pace verified); phases followed; ≥ 1 correct switch per call; switch_log complete | **Yes: ask first** (~3–6 short sessions) |
| T7 Sarvam audio quality | It sounds like a real executive; natural Hinglish; the hook lands | The T6 recordings | Human listening rubric: naturalness, pace, executive tone, hook clarity, no robotic lines; Sarvam STT check of what was said | **Yes: ask first** |
| T8 Loop demo | The loops change things | Replay 50 logged decisions with simulated outcomes into the scoreboards; one Loop 1 proposal through the gold set | The scoreboards move as expected; the proposal is accepted or rejected by the gold-set rule | No |
| T9 phone demo | The real call | 2–3 contrasting sellers on a rented number | A live mid-call switch; the switch_log is shown | **Yes: ask first** |

## 7. Build order (after your approval and the adversarial review)

1. Test cases for T0–T3.
2. `facts.py`, `prior.py` (scoreboards with L0 seeds from the evidence), `validate_persona.py`, `compile_vars.py`, plus the gate hooks.
3. Persona library v0 (about 6 personas with evidence grades) and the division references.
4. CLAUDE.md, then SKILL.md.
5. T4 on the laptop.
6. Daytona (T5).
7. Sarvam template + variables (T6–T7, with your approval).
8. Loops (T8).
9. Phone demo (T9).

## 8. Open items for you
1. Is the scoreboard score "meeting fixed" now, with "meeting held" added later?
2. Who approves library and template versions: you, or Rishav?
3. Are the thresholds in the design file (scale tier, profile strength, bl_usage, enquiry trend) OK as a start?

## 9. Resolution of the adversarial review (2026-10-10)

Review: `outputs/plans/persona-e2e-plan - adversarial review.md`. Each finding has a fix. Status: TODO / DONE / ACCEPTED-RISK.

| # | Fix (what we do) | Where | Status |
|---|---|---|---|
| B1 | Critical path with time boxes; the full loops are reduced to a working demo of each loop; one standing Sarvam test budget (user: "don't ask") | §10 below | TODO |
| B2 | Submission section: one slide, skills.md, README/approach note, agent ID, video script; owners | §11 below | TODO |
| B3 | Primary demo = live SDK/web session (a person as the seller); switch_log through the analytics API; the phone number is optional | T6 | TODO |
| B4 | persona.json adds accent, empathy, personalisation, escalation rules, guardrails, objection playbook with responses, per-choice confidence and evidence grade; the validator refuses without them; render `persona_spec.md` | scripts/validate_persona.py, render | TODO |
| B5 | Content validator on all spoken text: identity line, banned words (AI, bot, branch manager, account manager, personally), raha/rahi agreement with the voice, numbers only from verified_facts, no buyer identity. Clean the NSD reference and the template | validate_persona.py, compile_vars.py, references | TODO |
| M1 | switch_log rows add the matched cue, directive id, change made, reason | Sarvam tool | TODO |
| M2 | T6 tests all 5 signals (same turn, 2/2) + 0 false switches on ≥ 10 neutral turns | tests | TODO |
| M3 | Keyword list extended from Jev labels and PS07 turns; frozen; re-scored offline on the gold set | Sarvam tool + gold set | TODO |
| M4 | The tool reads `persona_style_id` and `switch_sensitivity`; per-style directive variants; hard word caps | Sarvam tool | TODO |
| M5 | No Jinja dependency: division text and gendered forms go in variables (`division_block`, `persona_style`); mid-call changes only through the tool's message_to_llm | template | TODO |
| M6 | Create every variable in the agent; `persona_language` → OnStart `set_initial_language_name`; T6 reads every variable back | Sarvam agent + OnStart | TODO |
| M7 | One regional-start demo seller (Gujarat); `trait.high_value` defined; identity line per language; STT round-trip check | facts.py, template, T6 | TODO |
| M8 | hook_priors significance flags regenerated from the CI (61 rows were wrong; 13 of 73 significant); evidence grade per row | references/evidence | DONE |
| M9 | Each cite has a quote of ≤ 20 words that must match the file text; counter_evidence must cite; Bash reads of the seller folder are logged too; padded-cite stub test | validate_persona.py, gates | TODO |
| M10 | The script's Thompson draw fixes the arm; P(best) by Monte Carlo is the propensity; the agent's amendments come from a fixed menu and are logged as factors; a full override is logged as a separate arm | prior.py, persona format | TODO |
| M11 | Holdout: 15% of decisions use P0 (current production style) as the measurement baseline (not a fallback; it is a normal persona arm) | prior.py | TODO |
| M12 | Hierarchy reduced: all → division → turnover band, plus additive offsets for zone and AOV tier; κ = 20 | prior.py, design §9.2 | TODO |
| M13 | Voice scoreboard V0 prior asymmetric (female mean 0.6 vs male 0.4) plus tension and rural/Hindi-belt offsets; test asserts P(F) > 0.5 | prior.py | TODO |
| M14 | money_lead must be in the call plan when eligible, unless a guard is cited | validate_persona.py | TODO |
| M15 | Peer ladder: ±1-band rungs never "allowed" for a claim; same 30-day window for the seller and the peers; optional AOV 0.5–2× filter | builder peer_stat, key_facts | TODO |
| M16 | Outcome capture: a `book_meeting` code tool sets `meeting_fixed` + slot; `collect_call.py` pulls the interaction (analytics); `loop2_update.py` CLI | Sarvam tool, scripts | TODO |
| M17 | Gold set: the scored turns of 2026-10-09 + ~150 PS07 seller turns labelled by Jev and spot-checked; Loop 2 demo replays real PS07 bot-version outcomes | data/gold, scripts | TODO |
| M18 | Builder `--as-of`: drop records after as_of; API values flagged as_of_unsafe; leakage fixture | builder | TODO |
| M19 | `export_for_agent.py`: HMAC pseudonym folder; seller, contact and company names → tokens; competitor names → tokens; hard PII gate (export refuses on any hit); tokens filled on-prem in compile_vars | builder/export | TODO |
| M20 | First-hour smoke tests (Daytona reach, Claude login, Sarvam agent, Redash, AK expiry); pre-cache the demo contexts; laptop → Daytona transfer = copy the exported folder; disclosed laptop cut-over if Daytona fails | §10 | TODO |
| M21 | facts.py fixtures written and run; distinctness = ≥ 3 audible dimensions differ between sample sellers; anchored 1–5 audio rubric with 2 raters | tests | TODO |
| M22 | Tests added: reply-start latency (median ≤ 2.1 s), DNC and asked-stop end to end, idempotent retry (no double dial), destination allowlist, bot question, gender agreement, Daytona pre-flight | tests | TODO |
| M23 | Submit only code written on 9–10 Oct for the core (app/persona, the skill); skills.md states the timeline honestly; earlier spikes listed as research | skills.md | TODO |
| m1 | One script name list (this file is the source) | — | TODO |
| m2 | Seller-gender name guess confidence lowered to 0.4; used only for the voice | facts.py | TODO |
| m3 | Range and catalogue checks for pace, pitch, voice id, language in compile_vars | compile_vars.py | TODO |
| m4 | Slide shows evidence and cited reasons, never a mapping table | slide | TODO |
| m5 | switch_log is never put into the LLM context; read through analytics | Sarvam tool | TODO |
| m6 | Clean up old clones and the relay secret; publish one demo version | Sarvam console | TODO |
| m7 | Rebuild is stable when the cache is fixed; the cache hash goes into 00_input | builder | TODO |
| m8 | Business impact: 11.6% baseline + hook CIs; uplift only from the holdout | slide, skills.md | TODO |
