# Adversarial review: VANI persona architecture plan v4

Reviewer stance: external, hostile. I am a senior ML and voice-systems architect who also judges hackathons. Reviewed on 2026-10-09 (hackathon day 1). The plan was not edited.

**What I checked against.** The PS04 brief (`raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md`). The deck (`raw/hackathon/2026-10-07-hackathon-deck-problem-statements.md`: jury rubric, submission checklist, rules). The team decisions (`raw/hackathon/2026-10-09-team-decisions-persona-agent.md`, treated as binding choices). The spikes in `raw/research/`: spike log 10-07, plan-following and plan-stress 10-08, voice override 10-08, on-start options 10-08, voice recheck 10-09, per-language voice 10-09. The reports `outputs/reports/Agent decides VANI persona.md`, `Persona generator architecture.md` and `Between run learning loops.md`. The research note `outputs/research_notes/Agent decides VANI persona/freetext_share_ps07.md`. The wiki article `wiki/projects/vani-hackathon/persona-data-validation.md`.

**What I did not attack.** These choices are binding: the agent composes the persona with tools; the agent suggests and a human adds; the decider is a frontier model on Daytona; voice comes via Code Tools or demo agent versions; there is no rule table; voice gender is chosen from data. I only attack how well the plan carries them out and what they put at risk.

Severity: **CRITICAL** = can lose a deliverable, a disqualification, or most of a scoring criterion. **MAJOR** = costs real points or a day of work. **MINOR** = clarity or correctness that a judge or reviewer will notice.

---

## 0. Verdict in one paragraph

The design direction is sound and unusually honest about its evidence. The execution plan for a 2-day, 3-person build is not.

The plan puts the most blocked component on the critical path to every deliverable: the frontier decider, which faces an OpenRouter 403, untested LiteLLM reachability, a pending data ruling and a pending "core agent" ruling. The live path has blockers of its own that the plan does not list: where the signal server runs, Jev reachability from that host, and the untested `decision_id` echo. It also never says that nothing audible can change mid-call. It maps itself only to the PS04 weights and ignores the deck's jury rubric and submission checklist.

It marks as "pending" a measurement that already exists in the repo. It also carries learning machinery that cannot be exercised in two days: exploration propensities, weekly clustering, a 4-arm experiment and 150 gold calls. Meanwhile the parts judges will actually hear are under-specified: tone-to-prompt compilation, restarted replies and latency.

**Verdict: PASS WITH FIXES.** Without the minimum fixes in §9 it is a FAIL, because D1/D2 on the real sample files, D3 and D4 each depend on an unresolved blocker with no committed fallback date.

---

## 1. Coverage scorecard

### 1.1 PS04 deliverables

| Deliverable | Plan's answer | Reviewer finding | Risk |
|---|---|---|---|
| D1 Generator on **sample seller files** | B1→B5c→B6 | §6.3 restricts the decider to "synthetic or masked data only" until a ruling. D1 on the real sample files then runs on the fallback or code-only path, which is not the chosen decider. No date is set for the ruling (C1). | CRITICAL |
| D2 Spec per seller with a reason for each choice | Cited per-dimension values | The fallback path's "reason" is a Thompson draw over an empty scoreboard, which is not tied to seller data (M3). Sarvam-105b fallback output is known to come out in Roman script (M6). PS04 §3.4 asks for an explicit evidence-strength label; the plan has none (M2). | MAJOR |
| D3 Live demo, ≥ 1 mid-call switch, 2–3 contrasting sellers | B7 + B8 | No demo channel is defined. No host is chosen for B8. Jev cannot be reached from Daytona. Demo versions are built only after the blocked composer runs. Version selection per call is untested (C2, C4). | CRITICAL |
| D4 Switch log | B8 rows + `sarvam_builtin` | Language-switch turns do not hit the tool (0/4). The transcript source for a live log is not defined per channel (m7). | MAJOR |
| D5 One slide incl. "chosen LLM" | Sample spec + diagram | The "chosen LLM" depends on two open organiser rulings (Q5, Q6). The slide cannot be finalised until then. | MINOR |

### 1.2 PS04 scoring

| Criterion (weight) | Plan's claim | Reviewer finding |
|---|---|---|
| Fit 25 | Traits and states, memory AUC 0.71, agent reads free text | About 60% of sellers have 0–1 prior calls, and profile-only prediction is near chance (AUC 0.52–0.58). The plan has no explicit cold-seller story (M14). The free text that justifies the agent is durable for only 9.7% of due sellers (M4). |
| Switches 25 | Lexicon now, Jev next turn, per-seller thresholds | Voice, pace and pitch cannot change mid-call, so switches are text-only, and the plan never says so (C3). Jev is unreachable from the server host, and Jev on Devanagari is untested (C2). Detection precision has not been measured (M9). |
| Distinctness 20 | Composed specs, distance metric | Distance mixes inaudible dimensions. Pace bands of 0.9–1.15 are barely audible, and P0 may already sit at 1.15 (M12). An LLM can collapse to a "safe" mix (earlier test: gender collapsed to female for every language) (M13). |
| Natural voice 2+ languages 15 | Per-language voices, native script, built-in switch | About 17% of replies restart, and median reply latency is about 2.1 s; neither is mitigated (M8). No voice was auditioned for the second language. A switched language keeps the first language's voice (m7). |
| Evidence 15 | PS07-backed seller side, logged p, experiment | Evidence covers the seller side, not "which persona choices work". The plan ignores the internal PS07 trial arms, the only real persona-choice evidence (M2). |

### 1.3 Deck jury rubric (the score the jury actually enters): **not mapped anywhere in the plan**

The deck says the jury scores 1–5 on **Business Impact 25 · Solution Completeness 20 · Technical Robustness 20 · Voice Experience 20 · Demo & skills.md 15**. The submission checklist is: a 5–7 min demo video, an approach note, the Agent ID or live link, a code folder with README, skills.md, and sample outputs. §12 of the plan maps only the PS04 weights. See M1.

---

## 2. CRITICAL findings

### C1. The chosen decider is barred from the data the deliverables are graded on (§6.3 blockers, §11 step 3, §14 Q5/Q6)

- **Issue.** The deck rule says "no customer data leaves the premises". The plan therefore restricts the frontier decider to "synthetic or masked data only" until a ruling arrives. D1 is literally "generator running on sample seller files", and D2 is "one spec for every sample seller". On the plan as written, the official specs come either from synthetic sellers or from the Sarvam-105b fallback and code-only path. Neither is the chosen decider.
- **Two rulings are still open.** One is whether data may go to a frontier model. The other is whether "core agent must be Sarvam" permits a frontier decider. Neither has an owner deadline.
- **Masking is undefined.** Seller names in Devanagari and Hinglish free text defeat simple regex masks.
- **Other off-premises flows are not covered.** The plan does not address the off-premises flows of the B9 reviewer, Jev (live utterances via OpenRouter), and the cloudflared tunnel (see C2).
- **Why it matters.** It can lose D1/D2, cost Technical Robustness ("validation on real data"), and in the worst case breach a rule.
- **Fix.**
  1. Ask the organisers for both rulings at the 3:30 PM mentor check-in today. Write the answer into `raw/hackathon/`.
  2. Make **Sarvam-105b the default decider** for D1/D2 on the real sample files from hour 0. Sarvam is the sanctioned platform. Its cost (₹0.16, 4.2 s) and flat schema are PROVEN.
  3. Treat the frontier model as an upgrade, used only if the ruling allows it, or only on synthetic sellers for the §9.1 experiment.
  4. Define masking as a code step with a test (phone numbers, GLIDs, names from profile fields replaced by tokens), and list every off-premises flow in one table.

### C2. The live switch path has unlisted blockers, and B8 is mis-tagged "Components PROVEN" (§3 B8, §7.2, §6.3)

- **No host is chosen for B8.** The spike log shows the Daytona preview URL has no wildcard DNS or TLS. The live spike only worked through a **cloudflared quick tunnel**. That tunnel's URL changes on every restart, and it is arguably a new outside vendor (trycloudflare.com) under AGENTS.md.
- **The live server cannot call Jev.** The spike log says verbatim: "the Daytona sandbox (35.234.211.110) is still not allowlisted, so **the in-call server cannot call Jev yet**." The LiteLLM Jev route showed **8/8 failures** in gateway logs. The plan lists the 403 only as a *decider* blocker.
- **The tested inputs do not match live inputs.** Jev's 49/51 is on **romanised** text, but the tool delivers **Devanagari** ASR. Its "~480 ms" was measured from the VPN laptop, not from the B8 host.
- **Per-seller thresholds, hysteresis and `max_switches` are untested.**
- **Why it matters.** Switches are worth 25 points, and D3/D4 depend on them. If Jev is down on demo day, the switch rests on a lexicon with an observed false-confusion bug ("phir se pooch raha hoon, price batao", 4/4).
- **Fix.**
  1. Decide B8's host today and record it. Options: (a) Daytona with the admin's wildcard DNS and cert; (b) the VPN laptop with a tunnel, accepting the vendor risk explicitly; (c) any IndiaMART-hosted box Sarvam can reach.
  2. Make the **lexicon the switch of record** for the demo, and use Jev only as an additive signal.
  3. Re-tag B8 as "lexicon + tool path PROVEN; Jev from host, Jev on Devanagari, thresholds ASSUMED".
  4. Fix the "phir se" cue before the demo.

### C3. Nothing audible can change mid-call, and the plan never says so (§6.1 layer c, §7.2, §12 "Switches")

- **Evidence.** The Sarvam UI says verbatim: "Voice is assigned per language at call start and will not change mid-conversation". The in-call code-tool context exposes only `change_language`, `change_state`, `set_agent_variable` and `set_end_conversation`, with **no TTS control** (spike log). PS04 §3.5 example: "slows down and simplifies when confused".
- **Issue.** The plan's live switch can only change *what VANI says*: wording, length, a callback offer. It cannot change pace, pitch or voice. P2's note "never slower on a confusion prior" makes it worse. A judge who hears no slow-down after "samajh nahi aaya" will mark the switch as weak.
- **Fix.**
  1. State the platform limit in §7.2 and on the slide.
  2. Specify an **audible text-level change per signal**:
     - Confusion: sentences of ≤ 8 words, one idea per turn, a check question, and commas or "…" to force pauses. Test whether Bulbul pauses on punctuation.
     - Rush: ≤ 12 words plus a callback slot.
     - Frustration: apology plus an exit offer.
     - Interest: move straight to the meeting ask.
     - Language: a lower or higher Hinglish mix.
  3. Write that change into `change` in the switch row.
  4. Measure words per reply and speech seconds before and after the switch on the demo call, so the change is shown, not claimed.

### C4. The demo chain runs through the most-blocked component, and the demo channel is undefined (§11 integration step 4, §7.1)

- **Issue.** Integration step 4 is "Composer runs on demo sellers → S builds matching versions → real decisions drive live calls". The voice route therefore waits on the frontier model (C1) before S can build anything real. There is also a cycle: `agent_input.voice_options.playable_now` needs the versions, and the versions are built from the composer's output.
- **Version selection is untested.** Selecting a **published version per call** (SDK `version` or `app_version`) has never been tried; every spike used `version=1` draft.
- **The demo channel is not stated.** It could be a human on a phone through Instant Outbound (which has no TTS override), or the SDK CALL harness with a laptop mic. These have different logging, latency and failure modes.
- **Why it matters.** D3 is pass or fail, and the deck needs the 5–7 min video **before 11:59 PM on day 2**.
- **Fix.**
  1. Today: publish 2 versions and prove that per-call `version` selection changes the voice (measure F0, as already done).
  2. Pick the demo channel and rehearse it end to end with a fixture decision.
  3. Freeze the demo sellers' decisions by about **12:00 on day 2** from whatever path works. Code-only or Sarvam-105b is acceptable. Pin them in the manifest and turn off re-cook for them.
  4. Record a backup demo video by about 16:00 on day 2.

### C5. Exposure to the "pre-built" and "all build work during the 2 days" rules (§3 Status column, §15)

- **Issue.** `app/signal_server/main.py`, `app/spike/*` and the spike results are dated 2026-10-07 and 10-08, before day 1 (09-Oct). The plan builds B8 on "Components PROVEN" from that code. The deck says "all build work happens during the 2 days" and "pre-built solutions are disqualified".
- **Why it matters.** This is disqualification risk. It is low probability but unbounded in cost.
- **Fix.**
  1. Ask the organisers at check-in whether pre-event *spikes and research* are allowed.
  2. Whatever the answer, write the production code fresh in the event repo, with git history starting on day 1. Treat the spikes as learnings only.
  3. Disclose the pre-event research in skills.md.

---

## 3. MAJOR findings

### M1. The deck rubric and submission checklist are missing (§12)
- **Why it matters.** The jury scores Business Impact (25), Completeness (20), Robustness (20), Voice Experience (20, explicitly "low-latency") and Demo & skills.md (15). The plan has no business-impact story; §13.12 says "claim no lift". Nothing addresses latency. The 5–7 min video, approach note, README and Agent ID have no owner or time slot.
- **Fix.**
  1. Add a second mapping table for the deck rubric.
  2. Build a business-impact paragraph from PROVEN aggregates. Rush appears in about 1 in 5 calls and halves the meeting rate. 30.8% of due sellers carry callback or constraint facts that a memory-driven opening can use. Give a scale estimate at VANI volume, labelled as a projection.
  3. Assign the submission checklist items to owners with times on day 2.

### M2. The "evidence" criterion is answered with seller-side evidence only, and the PS07 trial arms are ignored (§5.3, §12, §13.12)
- **Issue.** The plan says "Every cell is prior-only today (PS07 had one VANI style)". The wiki records **three internal personalisation trials, 0 for 3**: `personalis` vs `base_vani` gave a meeting rate of 14.8% vs 17.8% (p = 0.13), and an NI rate of 5.5% vs 13.1%. That is the only real "persona choice → outcome" evidence the team has. PS04 §3.4 also requires saying "how strong the evidence is and where the generator is making an informed guess". The plan's per-setting `confidence` is the agent's own and is capped by completeness, not by evidence strength.
- **Fix.**
  1. Add a **code-computed `evidence_tier`** per setting: PS07-measured / PS07-observational / literature / informed guess. Show it in the "why" panel and on the slide.
  2. Cite the trial arms honestly: personalisation keeps sellers talking (lower NI) but does not lift meetings.
  3. Mine natural variation in PS07 VANI behaviour (reply length, language used, call time) against outcome, labelled observational.

### M3. The fallback and code-only path is not a credible D1/D2 (§6.4 step 5, §11 "Code-only path alone still meets D1/D2")
- **Issue.** The fallback picks the library persona with the highest scoreboard draw. The scoreboard is prior-only, so with flat priors that is a **uniform random persona**, and its "reason" is "scoreboard draw". The agreement evidence the plan itself cites (3-run agreement gives 54–62% coverage) predicts about **40% fallback**. Composing about 20 dimensions instead of picking 1 of 5 should be worse, yet the plan's "healthy" ceiling is 30%. Many sellers may therefore get random personas with non-reasons.
- **Fix.**
  1. Seed per-seller-type priors on each card from its "first hypothesised for" column. This is allowed as starting values under decision 2.
  2. Generate code reasons from the seller fields that drove the seed (for example, "rush in 2 of last 3 calls → P1 pace").
  3. Measure the fallback rate on the 6 fixtures today, not after the experiment.

### M4. §9.2 is marked "pending", but the measurement exists, and it changes D-1 and the experiment (§9.2, §6.6, §9.1)
- **Evidence.** `outputs/research_notes/Agent decides VANI persona/freetext_share_ps07.md` (10:41 today, local regex, no LLM) found:
  - **30.8%** of due sellers have a decision-changing free-text fact, mostly callback timing (18.8%) and personal constraints (14.0%).
  - **Durable persona facts: 9.7%.**
  - Text contradicts structured data for **3.0%**.
  - Language facts: **0.26%**.
- **Why it matters.**
  - D-1 can be decided now: gate the agent to roughly 10–30% of sellers.
  - The agent's added value is mainly a scheduling and opening-line memory, not persona composition. That should be the honest headline.
  - Group (d) "Tamil-preferring" is a 0.26% case and should not be a quarter of the experiment set.
- **Fix.**
  1. Insert the numbers and close D-1 as "gated".
  2. Reweight the §9.1 groups to match.
  3. Note that the plan's metric (ii), "share where free text changes the composed persona", is still open, but (i) and the durable share bound it.

### M5. The agreement and settle rule is internally inconsistent and fragile (§6.4 step 2)
- **The text contradicts itself.** "Accept when ≥ 2 of the passing runs match on the **whole** audible bundle" conflicts with "If no ≥ 2/3 majority on **any** audible dimension → fallback". Those are different rules.
- **Style voice will rarely match.** Exact style-voice-id agreement across runs, drawn from 222 voices, will rarely happen.
- **New opening moves cannot be compared.** "Opening move" can be "new" free text, and two new moves cannot be compared.
- **Too few passing runs is undefined.** "≥ 2 of the passing runs" says nothing about the case where only 1 run passes.
- **The settled plan can contradict itself.** Medoid plan text from one run can contradict tone or branches settled by majority from the other two.
- **Fix.**
  1. Agree on the **bucketed** audible bundle (gender, pace band, pitch band, start language). Code then picks the style voice deterministically from the playable set for that bucket.
  2. Make opening moves categorical (a library move id or `new:<family>`).
  3. Define the rule as: at least 2 runs must pass; otherwise fall back.
  4. Take the plan text only from a run inside the agreeing majority, then re-validate it against the settled values.

### M6. The native-script fallback is known to be bad, and the FAQ Q5 guard has a known hole (§6.3 blockers, §6.4 step 1)
- **Evidence.** The plan says "Sarvam-105b fallback if [frontier] worse". `Persona generator architecture.md` records Sarvam output **"Hinglish came out in Roman script 3/3"**, and Bulbul docs say romanised Indic input degrades quality. The same report records number words ("do minute") slipping past the digit check. The v4 guard lists only "digits, price words".
- **Fix.**
  1. Add a validator for the native-script ratio of spoken text, with repair or reject.
  2. Add a number-word list (Hindi, English and Gujarati number words near price or time context) to the FAQ Q5 guard.
  3. State that neither model is yet PROVEN on native script.

### M7. The compile step that makes distinctness audible is unspecified (§5.1 "Tone… no (prompt)", §7.1, §11 ownership)
- **Issue.** Nowhere does the plan say how formality, warmth and brevity (1–5), English lean or Hinglish mix, branches and sensitivity become the `persona_directive` text. It also does not say who owns that template, M (B5) or S (B7), or what length limit the agent variables have.
- **PS04 dimensions are missing.** PS04 names **accent** (voice) and **empathy** (tone), and neither appears in the dimension table.
- **Why it matters.** Within one version (same voice), every non-audible difference between sellers lives in this template. It decides distinctness (20) and fit (25).
- **Fix.**
  1. Add a block "B7a Directive compiler" with an owner (S), input `persona_decision`, output the per-turn string, a length budget, and 3 golden examples. Include it in the hour 0–2 contracts.
  2. Map accent to the voice's language tag (`_hi_`, `_enhi_`).
  3. Add empathy, or state that warmth covers it.

### M8. Restarted replies (~17%) and latency (~2.1 s median) are noted but not owned (§7.2)
- **Evidence.** In plan-stress, about 8 of 46 turns had restarted or duplicated segments, including on the Gujarati switch turn. Reply latency had a median of about 2.1 s (range 1.2–3.5 s) **without Jev**. The tool has a 2 s max wait.
- **Why it matters.** These directly cost Natural voice (15) and Voice Experience (20, "low-latency"). A restarted reply on the judged switch turn is exactly what judges remember.
- **Fix.** Give S a timeboxed task today:
  1. Test the endpointing settings ("Switch after", eagerness to respond, interruption).
  2. Script the demo seller's lines without mid-sentence pauses.
  3. Measure the restart rate and latency on the final demo version.
  4. Report both numbers in skills.md.

### M9. Switch detection quality has not been measured (§7.2, §8)
- **Evidence.**
  - Lexicon vs PS07 evaluator agreement is κ ≈ 0.03.
  - False confusion on "phir se" occurred 4/4.
  - Jev agreed with labels on 49/51 romanised items; it has not been tested on Devanagari.
  - "Interested" scored 5/6.
  - All 5 PS04 signals must work (FAQ Q4), and "well-timed" is scored.
- **Fix.** Before the demo, build about 60 Devanagari and Hinglish test utterances (≈ 12 per signal plus hard negatives). Report precision and recall per signal for the lexicon and for Jev. Gate the demo on frustration, confusion, rush and interest each ≥ 0.8 precision.

### M10. Workload is not buildable by 1 strong dev + 2 others in about 18 working hours (§11)
- **M is on the critical path for everything.** M owns B1, B2, B4, B5a, B5b (Daytona, skill, tools, k = 3, routing), B5c, B6, the records, the experiment harness, the §9.2 measurement and all of the blockers.
- **N is overloaded.** N, the non-technical member, owns the native-script cards, voice auditions, 40-seller labels, the suggestion rubric, **≥ 150 gold calls**, native-script rating, the demo, the slide and skills.md.
- **The labelling is not independent.** "Team lead + N" label as non-builders, but the team has 3 people. If the team lead is S or M, the labels are not by non-builders, and the "third adjudicator" does not exist.
- **The experiment is huge.** 40 sellers × 5 reps × 4 arms, with k = 3 inside the compose arms, comes to roughly 1,600+ agent runs with tool loops, "tonight", on a blocked route.
- **Fix.**
  1. Move B4 and B6 to S once B8 works.
  2. Cut the experiment to 2 arms (code-only vs compose + guard) × 2 reps on 20 sellers.
  3. Cut gold calls to about 40.
  4. Name the team lead's role, and use a mentor or another team's member as the adjudicator.

### M11. The cut order protects the wrong things (§11)
- **Issue.** The current cuts (weekly clustering, Jev wording, k = 3, frontier model) remove almost no work. They keep the expensive and invisible parts: exploration and propensity, holdout, suggestion distance, the 4-arm experiment, 150 gold calls, B9, and loops "as recorded artefacts".
- **Fix.** Use the protect and cut order in §7 of this review.

### M12. Agent-level pace and pitch are untested, the bands are too narrow, and P0 may be faster than the "crisp closer" (§5.1, §5.2, §5.2 voice facts)
- **Evidence.** Pace and pitch are PROVEN only through the **TTS API**. The agent-level pitch slider is untested (§14 Q11), and agent-level pace changes were never measured. The spike agent's stored pace is **1.15**. If production P0 is also 1.15, then P1 "brisk ≈ 1.05–1.1" is *slower* than the control.
- **Why it matters.** A pace gap of 1.0 vs 1.1 is hard to hear, and judges need "clearly audible" differences.
- **Fix.**
  1. Read production VANI's pace.
  2. Measure agent-level pace and pitch on 2 versions (speech seconds and F0).
  3. For the demo, widen the contrast (for example 0.9 vs 1.2, plus a gender change and a language change).

### M13. "Voice gender from data" has no data, and the LLM's prior fills the gap (§5.3, team decision 7)
- **Evidence.** The scoreboard is empty, so the composer picks gender from its own prior. An earlier test found "**gender collapsed to female for every language**" (`Persona generator architecture.md`).
- **Fix.** While the gender cells are prior-only, code sets gender from the seeded prior or the exploration draw, not from the LLM. Log it as an `informed guess` evidence tier. This honours decision 7, since data decides once it exists, and it avoids an unexplained skew.

### M14. Cold sellers have no path (§4 B2, §6.3)
- **Issue.** About 59.5% of sellers have fewer than 2 calls. Profile-only prediction is AUC 0.52–0.58, and cold-segment ARI is ≤ 0.44. The plan says "`cold` where no stable structure" and nothing else. What does the agent get, what is the confidence, and how does a cold seller differ from P0?
- **Fix.**
  1. Write an explicit cold path: profile-led language and formality, all settings `confidence ≤ completeness`, live adaptation emphasised (FAQ Q6).
  2. Include 1 cold seller among the 2–3 demo sellers to show the honest version.

### M15. Stale specs and version skew in the demo window (§6.7, §7.1)
- **Issue.** S builds versions to match the composer's bundles. Any re-cook (event, version change, 72 h) can change a bundle, and then the version no longer matches. Every cloudflared restart changes the tool URL, which must then be edited in **every** demo version. A tool-response format change (B8) out of step with the base prompt (versions) is not covered by the manifest.
- **Fix.**
  1. Freeze the demo decisions (C4).
  2. Add the versions' tool URL and base-prompt hash to the manifest.
  3. Use a stable B8 hostname.
  4. Run a pre-demo checklist that calls each version once.

### M16. Failure behaviour is not specified for live dependencies (§7.2, §6.3)

| Failure | What happens today (spike evidence) | Required behaviour |
|---|---|---|
| Signal server down or slow | Tool waits up to 2 s; `persona_directive` keeps its last value or its default | Base prompt holds a safe plan summary. Test what the variable holds after a tool error. Health check before each demo call. |
| Jev unreachable (403 from Daytona; LiteLLM Jev 8/8 failures) | Not handled | Lexicon only; log `source=lexicon, jev=unavailable` |
| OpenRouter 403 for the decider | Listed | Sarvam-105b is the default (C1) |
| LiteLLM unreachable from Daytona | Untested | Test now; decider on the VPN laptop |
| `decision_id` not echoed in tool payload | Untested (§14 Q11) | Map the agent variable to a tool body field ("Agent variable" option exists in the UI). Fallback: a single active-call registry for the demo |
| Agent runs disagree | Expected ~40% from cited evidence | Seeded fallback with real reasons (M3) |
| Sarvam ignores the plan | V condition 23/28; P 20/20 on hand-written plans only | Re-send the plan every turn; test with **composed** plan text, not just hand-written |
| Language-switch turn skips the tool (0/4) | Logged from transcript | Define the transcript source per channel; the next turn's directive must follow the new language |
| Daytona sandbox auto-stop (ASSUMED Daytona default behaviour) | Unknown | Disable auto-stop for the B8 sandbox, or host elsewhere |
| Sept relabelling (NI 51% → 19%) | Mentioned in v2, **dropped in v4** | Fit the NI decay and any NI-based prior on Aug only; reward = meeting booked, not NI |

### M17. The §9.1 adoption rule can force a breach of a binding decision (§9.1)
- **Issue.** "Otherwise run select-only framing with the same guards." Team decision 3 says the agent "must not only select". Given M3's expected disagreement, the 30% fallback ceiling is likely to trip. The plan's own rule would then switch to a design the team lead ruled out.
- **Fix.** Change the fallback to "compose + guard with a tighter rubric and bucketed agreement (M5)". Report select-only only as a comparison arm.

---

## 4. MINOR findings

- **m1. Propensity formula (§6.4 step 4).** P(agent value) omits holdout mass where P0's level equals the agent's value. The correct form is (1 − h)(1 − ε/D) + h·1[P0_d = agent_d]. More importantly, exploration is "off for judged demo sellers", and there is no real traffic in 2 days. Keep the log fields and drop the sampler from the build.
- **m2. Volume figures are inconsistent.** §6.6 assumes "40K due sellers" per day, while §5.2 cites ≈ 1,500 answered calls/day. Reconcile them or drop the cost arithmetic.
- **m3. Evidence tags are too generous.**
  - "Etsy nightly per-buyer LLM" comes from a last30days social scrape; tag it as weak.
  - "28% confidently wrong" is a GPQA benchmark result, not persona composition.
  - "plan re-send 20/20" covers 10 calls with hand-written plans and scripted sellers.
  - "0/8 price turns" is on hand-written plans, not on agent-written text.
  - B7's "Per-language route PROVEN" is true, but published-version selection is not.
- **m4. Suggestion threshold.** "min > 0.35, **or** ≥ 2 audible dimensions differ": the "or" doubles the trigger. State which one applies, and why.
- **m5. Contracts.** Fifteen schemas in hours 0–2 is too many.
  - Freeze the dimension enumeration.
  - Resolve the duplication of `spec.<plan dims>` vs `plan{}`.
  - The mock composer says "two agree, one bad citation, one far" for 3 outputs. Specify which output carries which property.
  - Prioritise 6 schemas: `seller_context`, `persona_decision`, `call_config`, `tool_turn`, `switch_log_row`, `call_record`.
- **m6. Tamil.** There is no Tamil conversational voice. Keep Tamil out of the demo, and say so on the slide (46.6% of TN calls carry Tamil markers, which is a business-impact gap worth stating).
- **m7. Language switch and naturalness.** After a switch, the voice stays on the starting language's voice. A Hindi-tuned voice speaking Gujarati has not been auditioned. Pick the demo's second language from an audition, and use `_enhi_` voices if English is the second language.
- **m8. "No rule table".** §5.2's "First hypothesised for" column reads like a rule table to a judge. Label it "seed hypotheses (starting values; data overrides)", consistent with decision 2.
- **m9. Holdout and exploration on real sellers** need business approval (§14 Q12) that cannot arrive during the event. Present them as design only.
- **m10. Jargon a reviewer will not follow.** Aampe, Pega, Clio, TnT-LLM, Thompson, medoid, propensity, ε/h, "cook", "fence", D-1. Add a 10-line glossary, and a one-screen diagram with just the demo path.

---

## 5. Can 3 people build independently with fixtures?

| Seam | Contract clear? | Problem | Fix |
|---|---|---|---|
| M → S: `persona_decision` → B7 | Partly | No directive template (M7); demo playable set is circular (C4) | B7a template + 3 golden strings; a fixed playable set of 3–4 versions decided first, which the composer must choose from |
| S ↔ Sarvam: tool payload → B8 | No | `decision_id` echo untested (M16) | Test today; registry fallback |
| B8 → B12 switch row | Yes | Language-switch rows need a transcript source | Define it per channel |
| N → M: library JSON | Yes | Native-script check not in schema check | Add a script-ratio check |
| N/team lead → experiment labels | No | Non-builder labellers do not exist in a team of 3 | External adjudicator, smaller set |
| M → B5b on Daytona | No | Route blocked; data ruling | Sarvam-105b default (C1) |

Verdict on independence: S and N can start on fixtures. M cannot finish anything real until C1 is resolved, and S cannot finish D3 until C2 and C4 are resolved. The fixtures hide the two hardest integrations.

---

## 6. Over-engineering for a 2-day build

These are not wrong designs. They are wrong for 18 working hours, and none of them is visible to judges in the demo:

1. Per-dimension propensity sampler and holdout (no traffic; off for demo sellers).
2. Weekly suggestion clustering, ARI or Jaccard gates, 2 pp freeze (expected to propose nothing).
3. A 4-arm × 5-rep experiment (~1,600+ runs).
4. A per-dimension scoreboard with Pega priors and λ forgetting (every cell prior-only).
5. B9 reviewer + B10/B11 loops + ≥ 150 gold calls.
6. Event re-cook and a 72 h staleness engine (one nightly batch is never run during the event).

Keep each as a **contract plus one recorded artefact** (one row or one diff), as §11 step 7 already suggests, and spend the time on C2–C4, M7–M9.

---

## 7. Recommended protect and cut order

**Protect, in this order:**
1. The live demo call on the frozen versions with ≥ 1 lexicon-driven switch.
2. The switch log.
3. Specs for every sample seller (Sarvam-105b or code path, with real reasons and evidence tiers).
4. Natural voice in 2 auditioned languages.
5. The 5–7 min video, slide, README, skills.md and Agent ID.
6. Detection precision table (M9).
7. The composer upgrade (frontier model) if the rulings allow it.

**Cut first:**
1. Weekly clustering.
2. Propensity sampler and holdout.
3. 4-arm experiment, reduced to 2 arms × 2 reps.
4. Gold-call target, reduced to about 40.
5. Jev wording loop.
6. B9 automation, replaced by one manual review.
7. k = 3 → k = 1 + guards (labelled).
8. Frontier model → Sarvam-105b (already the default under C1).

---

## 8. What an external reviewer will not understand without help

- Why a "composed" persona plays as one of 3–4 pre-built versions. The playability gap needs one sentence and a requested-vs-played example on the slide.
- That mid-call switches change only words, not voice (C3). Say it before the judges discover it.
- That "evidence" today is about sellers, not about which VANI persona works. Use the evidence tiers (M2).
- Why there are 3 runs, a citation re-read and a fallback. Show one example where a bad citation fell back.
- The name "VANI persona" vs "seller type". §0 explains it well; keep that framing on the slide.

---

## 9. Verdict and minimum fixes to pass

**PASS WITH FIXES.** The plan is a FAIL until these 10 fixes are made:

1. **(C1)** Obtain both organiser rulings (data to a frontier model; frontier decider vs "core agent Sarvam") by the day-1 mentor check-in. Make Sarvam-105b the default decider for D1/D2 on the real sample files. Define masking and list all off-premises flows.
2. **(C2)** Choose and test B8's host so Sarvam can reach it and it can reach Jev. Make the lexicon the switch of record. Re-tag B8's evidence. Fix the "phir se" false confusion.
3. **(C3)** State that voice, pace and pitch are fixed for the call. Specify and measure an audible text-level change for each of the 5 signals.
4. **(C4)** Prove per-call version selection today. Fix the demo channel. Freeze the demo decisions and versions by midday on day 2. Record a backup video by about 16:00 on day 2.
5. **(C5)** Confirm the pre-event spikes are allowed. Rebuild in the event repo and disclose the research in skills.md.
6. **(M1, M2)** Add the deck-rubric mapping, a business-impact paragraph, owners for the submission checklist, and a code-computed `evidence_tier` per setting that cites the PS07 trial arms.
7. **(M3, M5, M17)** Seed per-type priors so the fallback is sensible, with code reasons. Use bucketed audible agreement with code-picked style voice. Replace "select-only" as the adoption fallback.
8. **(M4)** Insert the existing §9.2 numbers and close D-1 as gated.
9. **(M7, M6)** Specify the directive compiler (owner, template, length, golden examples). Add the native-script and number-word validators.
10. **(M8, M9, M10/M11)** Run timeboxed endpointing and latency work and a per-signal precision test before the demo. Rebalance M and N. Adopt the protect and cut order in §7.
