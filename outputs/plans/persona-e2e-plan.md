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
