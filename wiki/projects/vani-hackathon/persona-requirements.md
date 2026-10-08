# Persona Design: what the deck requires and how we're judged

Sources: [[2026-10-08-ps04-persona-design-problem-doc]] · [[2026-10-08-deep-research-between-run-learning-loops]] · [[2026-10-07-hackathon-deck-problem-statements]] · [[2026-10-07-spike-log]] · [[2026-10-08-deep-research-vani-problem-choice-system-design]]

**Answer:** there are two scoring layers. The **PS04 problem doc** scores fit 25%, switches 25%, distinctness 20%, natural voice in 2+ languages 15%, evidence 15% (indicative). The **deck's general rubric** scores impact 25%, completeness 20%, robustness 20%, voice experience 20%, demo + skills.md 15%. The doc adds a **5th deliverable: a one-slide presentation**, plus per-field reasons, confidence for missing data, a strict "delivery not facts" guardrail, and "a pre-scripted switch scores lower". The one real gap is still the mid-call **voice/pace** change: Sarvam fixes the voice per call, and the doc's own example ("slows down and simplifies when confused") needs pace. Everything here is read from the doc and deck, not from IndiaMART's past trial results.

## PS04 problem doc: extra requirements (2026-10-08)

**Problem-specific scoring (indicative weights):**

| Weight | Criterion | What it rewards |
|---|---|---|
| 25% | Fit of each persona to its seller | voice, language, tone *and plan* suit the seller's data |
| 25% | Correct, well-timed mid-call switches | right signal detected, change at the right moment |
| 20% | Distinctness across seller types | clearly different personas, not minor variations |
| 15% | Natural voice in 2+ languages | quality/naturalness of the demo across languages |
| 15% | Support from past-call evidence | choices backed by transcripts, summaries, outcomes |

**Additions vs the deck:**

- **Deliverable 5: one-slide presentation** with a sample persona spec, the past-call evidence behind it, and a workflow (chosen LLM, Sarvam, data flow, live signal detection, integration logic).
- **Generator I/O:** working code, seller file in → persona out; **one spec for every sample seller** covering voice, language, tone and conversation plan.
- **Reason per setting**, tied to seller data so a reviewer can see why.
- **Evidence:** link each major rule to past-call evidence (e.g. price objectors → a particular opening and pace), and **state evidence strength vs informed guess**.
- **Guardrail:** personas change delivery and approach, never facts, pricing or compliance statements (FAQ Q5).
- **Live adaptation changes "relevant persona settings":** slow down + simplify when confused, shorten when rushed, switch language when the seller does. Every switch goes to the switch log.
- **FAQ Q1:** no fixed persona library. Output is a persona *per seller*; grouping into types is allowed only to explain the logic.
- **FAQ Q3:** the switch must happen **live** and respond to what the seller says; a pre-scripted switch scores lower, so use a human speaking live (phone/browser), not only the scripted simulator.
- **FAQ Q4:** required signals are frustration, confusion, interest, language switch and rush; others optional.
- **FAQ Q6:** missing fields → sensible defaults, marked **lower confidence**, with live adaptation correcting them.
- Sarvam access/credits: "to be confirmed by organisers".

## The brief (slide 13)

- **Problem:** VANI talks to every seller in one voice and one style for the whole call. Sellers differ in pace, patience, language and how they object. An irritated, confused or rushed seller still gets the same delivery.
- **Challenge:** before each call, build the persona that fits the seller from seller data, and **adapt it live** as the call unfolds.

## What to build (slide 14) → our coverage

| # | Deck item | Our block | Status |
|---|---|---|---|
| 1 | Seller data as input: profile, business type, turnover, categories, engagement, past call outcomes and objections | B1 + PS07 data | Data PROVEN available |
| 2 | **Persona generator:** voice (gender, accent, pitch, pace), language (Hinglish mix, formality), tone (warmth, empathy) | B2 | Rules designed; 176 tagged v4 voices; pitch/pace per session DOCUMENTED |
| 3 | **Conversation plan:** opening, personalisation, objection playbook, escalation rules, guardrails, *each tied to seller data* | B2 → agent variables + instructions | Designed; opening/personalisation must be a real deliverable |
| 4 | **Evidence from past calls:** which persona choices work for which seller types (transcripts, summaries, outcomes) | B2 evidence fields + analysis | Aggregates exist; needs a clear "evidence table" artefact |
| 5 | **Live adaptation:** spot frustration, confusion, interest, a language switch or a rush; *change the persona mid-call* | B4 + B5 + B6 | Detection + tone/directive change PROVEN; language switch built in; **voice/pace change NOT possible** |
| 6 | **Voice demo on Sarvam:** same scenario, 2–3 contrasting sellers, ≥1 live mid-call switch | B3 + B7 (+ phone) | SDK demo PROVEN; phone path pending |

## Hand-ins (slide 15)

1. Persona generator running on sample seller files.
2. Persona spec per seller **with the reason for each choice**.
3. Live demo with at least one mid-call switch.
4. **Switch log:** signal detected, change made, reason. B5's log already has this shape.

## Success metrics (slide 15)

1. **Fit** of each persona to its seller.
2. **Correct, well-timed** mid-call switches.
3. **Distinctness** of personas across seller types.
4. **Natural voice in 2+ languages.**
5. **Support from past-call evidence.**

## Judging (slide 25, every juror scores 1–5)

| Weight | Criterion | What it means for Persona |
|---|---|---|
| 25% | Business Impact | lift on the 5 success metrics; scale of benefit for VANI and sellers |
| 20% | Solution Completeness | share of the 6 build items + 4 hand-ins delivered, working end to end |
| 20% | Technical Robustness | sound logic, **validation on real data**, edge cases and failures handled |
| 20% | Voice Experience | natural, **low-latency**, multilingual + Hinglish |
| 15% | Demo & skills.md | clear 5–7 min video + documented build journey |

## Submission and rules (slides 22, 30)

- Window: Day 2 (10 Oct), 2:00 PM to 11:59 PM; one submission per team.
- Checklist: demo video 5–7 min; problem statement + approach note; **Sarvam Agent ID / live link**; code + README; **skills.md** (build journey, tools used); team details.
- Process: jury screens video + folder + skills.md, then a live demo with Q&A.
- Rules: team of 3 with ≥1 non-tech member; **"all build work happens during the 2 days"**; **"plagiarised or pre-built solutions are disqualified"**; data used responsibly, no customer data leaves the premises.

## Gaps and risks against the deck

- **Mid-call voice switch.** Sarvam pins the voice per call (UI: "Voice is assigned per language at call start and will not change mid-conversation"). What *can* change live: tone/empathy/formality/brevity (proven via directives) and language (built-in switch, same voice). Pace can only be approximated through wording. Ask the Sarvam floor team on Day 1 whether Code Tools or anything else allows a speaker or pace change mid-call.
- **Pre-built risk.** Spike code (`app/spike/`, `app/signal_server/`) was written before the event. Treat it as research; write the submission code during the 2 days and say so in skills.md.
- **Personalisation is a required item** (#3 "opening, personalisation"), but PS04 doesn't define it. Our reading: plan content tailored with this seller's data. Confirm on Day 1. "Lift from the personalised opening" is a **Problem 2** metric, not PS04. Design of the plan: [[learning-loops]].
- **Real-data validation** (Robustness) needs the persona choices and the switch detection evaluated on PS07 data, not only on simulated sellers.
- **2+ languages, natural:** pick and ear-test voices in at least Hindi/Hinglish plus one regional language (Gujarati and Marathi have conversational v4 voices; Tamil does not).
