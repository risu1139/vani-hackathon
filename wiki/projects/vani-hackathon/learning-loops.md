# Learning loops: personas and switches improve after every run

Sources: [[2026-10-08-team-decision-between-run-learning]] · [[2026-10-08-plan-following-spike]] · [[2026-10-08-deep-research-between-run-learning-loops]] · [[2026-10-08-last30days-voice-agents-learning-from-past-calls]] · [[2026-10-08-deep-research-self-improving-persona-switch-loops]] · [[2026-10-08-last30days-self-improving-agent-loops]] · [[2026-10-07-persona-data-validation-run]] · [[2026-10-07-spike-log]]

**Answer (decided 2026-10-08):** nothing learns during a call. During a call, our frozen switcher (lexicon + [[jev]]) makes every switch decision, and no LLM decides switches. **After each run**, an LLM reviews the finished call (transcript, switch log, outcome) and labels the mistakes. Those corrections update two things before the next run: the **switcher** and the **persona generator** (per-seller memory + global rules). The existing PS07 calls (269K) count as past runs and bootstrap both loops. Hackathon calls are just more runs. **No model is trained**: Sarvam, Jev and every LLM stay as they are. What learns is our own logic: persona rules, per-seller memory, evidence tiers, lexicon cues, thresholds and Jev question wording.

## The cycle

```
run (call, or a replayed PS07 call)
  → trace: turns, switches fired, persona used, outcome
  → post-call review (LLM, offline): per turn, the true signal; per switch, right / missed / false / late;
                                     per persona setting, did it fit what happened?
  → candidate corrections
  → gate: accept only if the frozen hand-labelled test set does not get worse
  → new version of switcher and generator (v0 → v1 → v2 …), used by the next run
```

## Loop A: the switcher

- **What changes:** lexicon cues (romanized + Devanagari), Jev question criteria, per-signal confidence thresholds, and optionally a small char-n-gram classifier that retrains in seconds. Jev itself can't be trained: its only inputs are `state`, `instructions` and `criteria` (DOCUMENTED).
- **What the review produces:** a missed signal becomes a positive example; a false switch becomes a negative; a late switch flags the cue that should have fired earlier.
- **Gate:** a label is used only if Jev and the reviewer agree or a human confirms it. A new version ships only if precision/recall on the frozen test set doesn't drop.
- **Proof:** per-signal precision, recall and timing (turns from cue to switch), v0 vs v1 on held-out turns.
- **Why not decide with the LLM live:** latency. Sarvam already takes ~2.1 s per reply, and Jev via OpenRouter adds p50 ~0.5 s and p95 ~1.4 s under load (PROVEN, [[2026-10-07-spike-log]]).

## Loop B: the persona generator

1. **Per-seller memory.** What happened on seller X's last call shapes their next persona. Rushed → open short. Objected on price → price playbook first. Switched to Gujarati → start in Gujarati. This is the best-supported lever: the prior call outcome predicts meetings far better than profile does (4.4% after Not Interested vs 21.7% after Meeting Fixed; memory AUC 0.71 vs profile 0.58 for next-call meeting). A seller's own signals recur (rush 30.8% vs 20.8%, confusion 25.0% vs 7.0%), but on only 954 same-seller transcript pairs. 40.5% of sellers have ≥2 calls and hold 71.3% of calls; median gap 1 day. Outcome memory fades (half-life ~20 days); rush/terse behaviour doesn't (PROVEN, aggregate).
2. **Global rules.** Review findings pooled across runs change generator rules, e.g. "sellers like this kept getting confused at this formality level". A rule needs n ≥ 200, a CI excluding zero, and must hold on a time split (mine Apr–Jul, check Aug–Sep). Each rule is tagged STRONG / MODERATE / WEAK / GUESS for the evidence criterion.
3. **Proof:** on held-out sellers, before vs after the update: fit, plus whether the persona's expected signals matched what actually happened on that seller's next call.

## Voice gender

- Chosen pre-call per seller and fixed for the whole call (Sarvam). Rule order: voice-catalogue coverage for the seller's language, then timbre, then explicit seller evidence. Every gender choice is tagged **GUESS** for now: PS07 has no bot-voice or seller-gender column, and VANI used one voice, so nothing compares genders.
- Per-seller change only on an explicit remark about the voice, or poor audibility repeated across ≥2 calls. A global change needs live human calls with gender deliberately varied. Simulated sellers can't judge it, because they only see transcribed text.
- Guards: never infer the seller's gender; never tie voice gender to category, region or turnover; audit segments for a gender skew above ~80%.

## Conversation plan (required)

- PS04 requires it: deck build item 3, doc §3.3, deliverable 2 ("covering voice, language, tone **and conversation plan**"), and fit scoring ("voice, language, tone and plan"). Elements: opening, personalisation, objection playbook, escalation rules, guardrails, each tied to seller data.
- **Who makes the plan:** our persona generator (B2) builds it before the call as part of each seller's persona spec. The generator is rules plus one Sarvam LLM call for wording. The Sarvam voice agent then runs the call with it.
- **We decide what the call covers, Sarvam decides the words.** Sarvam agents don't let us bring our own LLM, so we can't script every turn.

| Part of the call | Who decides | How |
|---|---|---|
| Exact first line (opening) | Us | `initial_bot_message` per call. Fully scripted, so personalisation can go here. |
| What to cover, in what order (plan steps, objection playbook order) | Us | Per-call variables passed to the agent |
| Personalisation facts (category, city, last call, last objection) | Us | Per-call variables. Only fields present in the seller file. |
| When to escalate or offer a callback | Us | Escalation rules in variables + the live directive from our switcher |
| Live changes (shorter, simpler, switch language) | Us | `persona_directive` from our switcher each turn |
| Pitch goal, product facts, prices, compliance text | Fixed, same for every seller | The agent's base instructions (FAQ Q5) |
| Every word after the first line | Sarvam's LLM | Phrases its replies inside the plan and directives |

- **PROVEN (spike, 2026-10-08, [[2026-10-08-plan-following-spike]]):**
  - The scripted opening is spoken word for word. Confirmed by recording and transcribing the greeting; the transcript stream doesn't include it.
  - The agent followed the plan in **15/16** checks across 2 made-up sellers × 2 calls:
    - personalisation facts used: 4/4;
    - objection playbook followed with no price quoted: 4/4;
    - confirmation step: 4/4;
    - meeting/time step: 3/4. The miss was a repeated meeting ask, not a skipped or out-of-order step.
  - Directives also changed replies in the earlier spike: "rushed" gave 11–13 words plus a callback offer.
  - Caveats: n=4, a cooperative scripted seller, and the plan was carried through the server's directive prefix.
- **Still to test:** a seller who goes off-plan or raises objections out of order, a plan passed only through `agent_variables` at call start, and phone (Instant Outbound).
- **"Personalisation" is undefined in PS04.** Our reading: tailor what the call says using this seller's data (category, city, last call, last objection), citing only fields that are present. Confirm with organisers. "Lift from the personalised opening" is a Problem 2 metric, not PS04.
- The plan learns between runs like the delivery settings. The reviewer marks whether the opening landed, whether the personalisation line was right, whether the playbook order matched the actual objection, and whether escalation should have fired. These become gated rule edits.

## What the generator is (base version)

Rules put each seller on discrete levels across 8 settings: voice (gender + timbre), language, pace, pitch, formality, warmth, opening, and objection playbook + escalation. The Sarvam LLM only writes the wording inside those levels. Every setting has a reason tied to a seller field, plus a confidence level. A missing field keeps the default value at LOW confidence (FAQ Q6). See [[system-design]] B2.

- **Distinctness comes from the mapping.** Sellers who differ on a driving feature must differ on something audible; identical sellers get identical levels. Free-text LLM generation collapses to near-identical personas (DOCUMENTED: "persona collapse", arXiv 2604.24698).
- **Show it with one number:** how closely the distance between sellers matches the distance between their personas (Mantel test).
- **Pitch is not a lever until measured.** Public Bulbul docs show no pitch control; check it from the audio first.

## Scope check (devil's advocate)

| Piece | Serves | Verdict |
|---|---|---|
| Base generator with reasons + confidence | D1, D2; fit 25%, evidence 15% | Required |
| Rules mined from PS07 with tiers | evidence 15%, robustness 20% | In scope |
| Per-seller memory from the last call | fit 25% | In scope, strongest data |
| Post-call review → switcher v1 | switches 25%, robustness | In scope |
| Replaying PS07 calls as runs | robustness ("validation on real data") | In scope; it's where most learning comes from |
| GEPA prompt evolution | indirect | Stretch; cut first |
| LLM deciding switches live, learning mid-call | — | Out (team decision) |
| Bandits, fine-tuning a model | — | Out: no live traffic, no GPU, no time |

## Rules that still bite

- **Honest claim:** most learning comes from replayed PS07 calls, not the few dozen hackathon calls. Say so; "it learned from our 10 demo calls" won't survive Q&A.
- **Script mismatch:** past turns are 99.4% Latin script, but live ASR sends Devanagari. Test the switcher on both, or past-data gains won't carry over.
- **Data on premises:** post-call review sends real seller text to an LLM. Use the Sarvam LLM or the internal gateway, and get an organiser ruling on Day 1.
- **Small samples:** with ~25–30 positives per signal, only gains of ~20 points or more are distinguishable. Kappa is ±0.26 at n=30.
- **Pre-built rule:** write the loop code during the event and disclose spike code as research in skills.md.
- **Budget:** core deliverables ≈ 20–30 dev-hours against ~18–24 usable hours. Cap loop work at ~6 hours.
