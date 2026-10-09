# raw/ catalogue

What each source dump is for, and whether its conclusions are still current. Raw files are never edited, so when a later decision overrides one, this table says so. Append new rows; to change a status, add a dated note rather than rewriting history.

Status key: **current** = still the basis for the wiki · **reference** = facts still valid, conclusions superseded · **history** = kept only as a record of how we got here.

## hackathon/ (organiser material and team decisions)

| File | What it is for | Status |
|---|---|---|
| 2026-10-07-hackathon-deck-problem-statements.md | Deck text: all 6 problems, rules, judging rubric | current |
| 2026-10-07-ps07-persona-data-dictionary.md | Column meanings for the PS07 persona data in `data/` | current |
| 2026-10-08-ps04-persona-design-problem-doc.md | PS04 doc: deliverables, scoring, FAQs. The binding requirements | current |
| 2026-10-08-team-decision-between-run-learning.md | Team lead's ruling: per-seller personas; learning happens between runs, never mid-call; LLM never decides switches live | current |

## research/ (our research runs)

| File | What it is for | Status |
|---|---|---|
| 2026-10-07-last30days-open-source-voice-ai-agents.md | Landscape scan: which voice stack and problem to pick | reference (Pipecat/Dograh path dropped; Sarvam agent is compulsory) |
| 2026-10-07-voice-ai-research-synthesis.md | Summary of the scan above, first problem ranking | history |
| 2026-10-07-last30days-voice-agent-live-persona-adaptation.md | How other agents switch persona mid-call | reference |
| 2026-10-07-sarvam-platform-docs-check.md | Sarvam agent capabilities: states, tools, voice per call | reference |
| 2026-10-07-sarvam-deploy-sdk-docs-check.md | Sarvam SDK / outbound / per-session TTS override | current |
| 2026-10-07-sarvam-voice-catalogue.json | All 176 Bulbul v4 voices with tags | current |
| 2026-10-07-deep-research-vani-adaptive-persona-architecture.md | First architecture: one Samvaad agent + Jev sidecar | history (superseded by 2026-10-08 system design) |
| 2026-10-07-persona-data-validation-run.md | Aggregate analysis of PS07 data: signals, outcomes, language | current |
| 2026-10-07-spike-log.md | Measured spike results (tool calls, latency, Jev, Daytona) | current |
| 2026-10-08-last30days-outbound-voice-agent-architecture.md | Scan used to confirm the problem choice and outer architecture | reference |
| 2026-10-08-deep-research-vani-problem-choice-system-design.md | Problem choice (#4) + 10-block system design | current, except "5 archetypes as output" (overridden by PS04 FAQ Q1: one persona per seller) |
| 2026-10-08-last30days-self-improving-agent-loops.md | Scan on self-improving loops: GEPA, cascades, simple-jev, shrewd | reference |
| 2026-10-08-deep-research-self-improving-persona-switch-loops.md | Deep research on persona + switch improvement loops | reference: generator rules, distinctness, proof protocol and scope table still hold. **Overridden by the team decision above:** the live "LLM teacher on uncertain turns" tier and any in-call learning. The LLM only reviews finished runs |
| 2026-10-08-last30days-voice-agents-learning-from-past-calls.md | Scan: how voice-agent vendors learn from past calls (Coval×Phonely, Cekura, Vogent) | reference; the "Coval 70%→88%" figure in its web appendix could not be verified, so don't use it |
| 2026-10-08-deep-research-between-run-learning-loops.md | Deep research: learning between runs, applied to the switcher and per-seller persona (incl. gender and conversation plan); no model training | current; "personalisation" meaning is our reading, pending organiser confirmation |
| 2026-10-08-plan-following-spike.md | Measured: Sarvam agent follows a per-call plan (opening, steps, personalisation, playbook) passed as variables | current |
| 2026-10-08-plan-stress-spike.md | Measured: plan under hostile/off-plan sellers, plan-delivery route (every turn vs start only), Gujarati switch, restarted replies | current |
| 2026-10-08-voice-override-spike.md | Measured: per-call voice/pace/pitch override via SDK is ignored; initial_language_name works; voice UUIDs + on_start route | current |
| 2026-10-08-sarvam-on-start-options-check.md | Console + docs check: on-start HTTP hook is self-serve (variables only); Python Code Tools (needed for per-call voice) are on request | current |
| 2026-10-09-last30days-agents-refine-personas-segments.md | Scan: 2026 agents that build/refine personas and segments; Etsy LLM profiles at 90M scale; PersonaAgent; TnT-LLM | reference |
| 2026-10-09-last30days-voice-persona-expressive-tech.md | Scan: 2026 expressive/steerable voice tech; Sarvam Bulbul v4 persona voices (pace only, pitch v2 only); ElevenLabs/LiveKit expressive mode | current |
| 2026-10-09-sarvam-voice-recheck.md | Day-1 re-check: pace+pitch work on v3/v4 (API); per-call SDK override still ignored; per-language voices route; native script advice | current |
| 2026-10-09-per-language-voice-spike.md | Measured: per-call voice via Per-language voices + initial_language_name works (Hindi→female 286 Hz, English→male 140 Hz); reverted | current |
| 2026-10-09-last30days-agent-decider-vs-guardrails.md | Scan: agent as decider vs deterministic harness (2026 practitioner view: hybrid; agent decides once, code executes) | reference |
| 2026-10-09-team-decisions-persona-agent.md | Team lead's decisions: agent composes VANI persona with tools, suggests new personas (human adds), frontier-model decider, voice via Code Tools or demo agent versions, no rule table in plan | current |
| 2026-10-09-freetext-share-ps07.md | Measured (local regex, aggregates): 30.8% of due sellers have a decision-changing free-text fact (mostly callback time/constraint); 9.7% durable (contact, language, competitor, need, complaint, price); 3% conflict with structured labels; ~1/3 only outside summaries | current |
| 2026-10-09-team-decision-data-sharing.md | Team lead's data policy: no GST/PAN/ID numbers to frontier model; names/address only when a task needs them; Sarvam gets what personalisation needs | current |
| 2026-10-09-onstart-code-tool-spike.md | Measured: per-call voice/pace/opening via OnStart code tool + defined agent variables works (female 269 Hz vs male 94 Hz, openings verbatim) | current |
| 2026-10-09-onstart-pace-and-phone-check.md | Measured: pace via OnStart variables audible (0.9 vs 1.3: ~21% faster); phone path API accepts agent_variables but workspace has no telephony connection (needs KYC rent or BYO provider) | current |
| 2026-10-09-jev-devanagari-spike.md | Measured: Jev on native-script turns 49/51 vs romanised 50/51; tricky cases 10/10 incl. 'phir se' insistence; ~500 ms | current |
