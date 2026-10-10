---
title: "VANI persona design v2: evidence-first fields (proposal for review)"
---

**Status:** PROPOSAL for product review. No code has changed. Consolidates the redesign messages from the persona session (2026-10-10), in their final order. Compared with the current design (commit `a8f2e06`, see `persona_hierarchy.pdf`).
**Audience:** product manager and the persona/Sarvam owner.

# 1. Review questions (please answer these first)

| # | Question | Why it matters | Our suggestion |
|---|---|---|---|
| 1 | **Value groups per field.** Are the ranges in section 5 right (for example pace 0.85–0.95, 0.95–1.05, 1.05–1.25)? | The brief and the learning step count calls per range. Too many ranges means too few calls in each. | Three ranges per numeric field, two to four labels per text field |
| 2 | **15% holdout on the current default persona (P0).** DECIDED by the persona session's user: keep. | It is the only clean comparison group. About one call in seven is a deliberate baseline. | Keep (decided) |
| 3 | **Random draw for the top-2 personas.** DECIDED: the weighted draw stays only for picking the top-2; field values are never drawn. | The draw is the propensity the learning step needs. | Keep (decided) |
| 4 | **Does the hook brief per segment use the same hierarchy?** | Hooks could be learned per segment, like persona values. | Yes, same levels, separate counts |
| 5 | **Is the read-all-probe-files rule acceptable for run time?** Every field must prove its files were opened. | The persona run takes about 6 minutes now. More mandatory reading adds time, and the demo deadline is tight. | Keep the rule for the gated fields; measure run time on three sellers before enforcing it everywhere |
| 6 | **Is a persona with all fields "start_persona" acceptable?** | With empty scoreboards and thin seller data, many fields will stay unchanged. | Yes: it is honest, and it is learned as its own group |
| 7 | **Who approves a new persona-library version?** | The script may suggest card changes; a human approves. | One named owner |

# 1b. Seller size bands (new)

The turnover band (level L2) now carries a plain size label:

| Annual turnover | Size label |
|---|---|
| below 40 lakh | **small** |
| 40 lakh to 1.5 crore | **medium** |
| 1.5 to 5 crore | **medium-high** |
| 5 crore and above | **high** |

**Language suggestion by size:** for **high (5 crore and above)** sellers the suggested starting language is **English** (with light Hindi). For all other sizes the language is suggested from the seller's location (profile state and city, GST state, onboarding cities, languages heard on calls), read by the language model, **not from a fixed table**. Both are suggestions only: seller evidence with cited quotes can change them.

# 1c. New seller fact: top 5 product categories (D08)

The seller context now lists the seller's **top 5 categories by number of active products** (most first, with counts), read from the product database through Redash (approved products only). The agent receives it in the catalogue file and in the INDEX key facts. A hook based on the top category will be added later.

# 2. What changes, in one paragraph

Today the script gives Claude the **top-2 persona cards** and a fixed menu of adjustments. In v2 Claude **sets every persona field itself**, but starts from the **one persona it selects** out of the top-2. For each field it keeps that persona's value unless it can prove a reason to change it. The reason must come first from **the seller's own data** (cited quotes) and only then from **learned results for similar sellers** (the hierarchy). If neither exists, the value stays and is recorded as "start_persona". Persona cards become information, not limits. The fixed adjustment menu goes.

# 3. The flow

1. **Script (no LLM):** from the seller's facts it computes the path through the hierarchy (division, turnover band, AOV tier, zone, state, category group) and picks the **top-2 personas** for that path.
2. **Script writes the brief:** for each field, at each level of the path, the value ranges that got meetings, with call counts and meeting rates. A level with few calls falls back to its parent level (κ = 20 pseudo-calls, as today). The cards are listed as examples.
3. **Claude selects one of the top-2**, with a reason and cites. That persona is the base.
4. **Claude decides every field.** Each field is a decision: value + reason + reason type (section 4).
5. **Validator (gate)** checks the proof of search, the cites, and the ranges. A failure returns one message listing all problems.
6. **Compile and call** as today; after the call the outcome is logged per field (section 7).

# 4. Reason types per field, in order of priority

| Order | Reason type | When it is allowed | What it needs |
|---|---|---|---|
| 1 | **seller_evidence** | The seller's own files support a different value | Cites with quotes (at most 20 words each), as today |
| 2 | **hierarchy** | The search of the seller's files found **no** evidence, and the brief has data for the path | The level used (for example L4), the value range, number of calls, meeting rate, **and** the "searched" note and read-log proof |
| 3 | **start_persona** | No seller evidence and no hierarchy data | The value stays unchanged; the "searched" note is still required, so we know the agent looked |

If seller evidence **was** available but the agent used the hierarchy, it must say why the evidence does not apply. No random values and no random test fields.

# 5. Fields, search files, and ranges (draft, to finalise)

The "probe files" are the files the agent must open, and the read log must show it, before it may use "hierarchy" or "start_persona" for that field. For the call files this means every call the INDEX lists in the last 90 days.

| Field | Probe files | Facts it looks for | Draft value ranges | Hard range check |
|---|---|---|---|---|
| Voice gender | `core.md` (A07 gender), call files | Recorded gender, past calls with a woman or man | F / M | — |
| Pace | call files, `core.md` (B03 languages) | Rushed or slow-speech cues, languages spoken | 0.85–0.95 / 0.95–1.05 / 1.05–1.25 | 0.85 to 1.25 |
| Pitch | call files | Seller reaction to voice | −0.3–−0.1 / −0.1–0.1 / 0.1–0.3 | −0.3 to 0.3 |
| Language start | `core.md` (B01 location, X06 GST state, X02 onboarding, B03 call languages) | Where the seller is, what they spoke | any Sarvam-supported language | allowed language list |
| Formality | `business.md`, `buyleads.md`, `core.md` (A04 designation) | Business size, order values, designation | low / medium / high | — |
| Sophistication | `business.md`, `buyleads.md`, `core.md` | Turnover, AOV | simple / practical / numbers-first | — |
| Warmth | call files, complaints data (I01) | Grievances, tone in past calls | medium / high | — |
| Empathy | call files, complaints data (I01) | Open complaint, frustration | a short phrase, free text | — |
| Language mix (code mix) | `core.md`, call files | Hinglish in past calls | regional only / light Hinglish / Hinglish / English-heavy | — |
| Words per reply | call files | Short or long past answers | 8–12 / 13–18 / 19–25 | 8 to 25 |
| Hook | as today (hook probe files) | Money lead, profile gap, credits, grievance | existing hook ids | eligible hooks only |
| Opening | call files, hook facts | Value statement, then one question | free text | validator rules for wording |

# 6. Value groups: why a few

Each numeric field uses about three ranges and each text field two to four labels. This keeps enough calls in every group to mean something. A new range structure can be added only as a versioned change to `hierarchy.json`.

# 7. What the learning step records

For each call: the seller's path, **each field's final value group, its reason type, and the call outcome**. Counts are kept per field × value group × hierarchy level.

- **Report 1:** meeting rate split by reason type (seller_evidence, hierarchy, start_persona). This answers "is the agent's own evidence better than the learned averages?"
- **Report 2:** uplift against the P0 holdout (needs real calls).
- **Card suggestions:** the script suggests changes to persona cards; a human approves a new library version.
- **Test calls** go to a separate test scoreboard and never to the real one.

# 8. The reviewable file

`references/hierarchy.json` (proposed) would be the single source of truth, read by the prior and the learning step. It holds: the seven persona levels (L0 all, L1 division, L2 turnover band, L3 AOV tier, L4 zone, L5 state, L6 category group), each with its parent, the seller fact that feeds it and its bucket rules; the voice levels (V0 to V3); κ; the holdout share; base means; the field list with probe files and value ranges (section 5); a version; "approved_by: pending"; and a changes log. A test would check that the keys the learning step writes are exactly the keys the prior reads.

# 9. Tests required before release

1. Hierarchy used while a probe file was **not** opened: the persona fails.
2. Hierarchy used with **no "searched" note**: fails.
3. Seller evidence was available but hierarchy was used, with no explanation: fails.
4. "start_persona" without a searched note: fails.
5. Values outside the hard ranges: fail.
6. Learning keys written equal the prior's keys, both read from the file.

# 10. Risks and costs

| Risk | Effect | Mitigation |
|---|---|---|
| Deeper levels (state, category group) have no data | Brief is empty at those levels; fallback to parents | Expected; show counts in the brief so the agent can see it |
| Longer persona runs | More files to open per field | Measure on three sellers; limit mandatory reading to the gated fields |
| Sparse real calls | Almost every field ends as "start_persona" | Honest and counted separately; do not read it as a failure |
| Many field values can drift from persona cards | Persona becomes hard to name | Log the selected persona and every change; keep P0 holdout for comparison |
| Design changed several times in one day | Risk of building the wrong version | This document is the single reviewed version; code waits for approval |

# 11. What does not change

Identity rules (never "AI", "bot" or "branch manager"), the validator's banned words and gender agreement, numbers only from verified facts, the pseudonymised folder, Sarvam receiving the persona only as variables, the in-call switch, the post-call review and the human approval of library changes.

# 12. Next step

After review: (1) write `hierarchy.json`; (2) update `prior.py` and the learning step to read it; (3) update the skill, the validator and the formats; (4) add the tests in section 9; (5) rerun one demo seller end to end. **No code changes until this proposal is approved.**

*Sources: persona session messages of 2026-10-10 (reason-per-field design, search proof, start-persona rule, top-2 correction); `persona-skill-design.md` §9.2/9.3; `persona-e2e-plan.md` §9 (M10 to M13); `references/persona_library.json`; `scripts/prior.py`; `scripts/validate_persona.py`.*
