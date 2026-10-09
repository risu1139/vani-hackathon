# VANI Persona Design: VANI Voice AI Hackathon 2.0

IndiaMART, 9–10 Oct 2026 · **Problem 4 of 6: Persona Design** · Voice platform: [Sarvam AI](https://docs.sarvam.ai/)

## Problem statement

**The problem today.** VANI (the Voice Bot) talks to every seller in one voice and one style, and keeps that voice and style for the whole call. Sellers differ in pace, patience, language and how they object. A seller who gets irritated, confused or rushed mid-call still gets the same delivery.

**The challenge.** Before each call, build the VANI persona that fits the seller from their seller data. Then adapt it live as the call unfolds.

### What we build

| # | Part | What it does |
|---|---|---|
| 1 | Seller data as input | Profile, business type, turnover, categories, engagement, past call outcomes and objections (provided) |
| 2 | Persona generator | Sets the voice (gender, accent, pitch, pace), the language (Hinglish mix, formality) and the tone (warmth, empathy) |
| 3 | Conversation plan | Opening, personalisation, objection playbook, escalation rules and guardrails, each tied to seller data |
| 4 | Evidence from past calls | Which persona choices work for which seller types, taken from transcripts, summaries and outcomes |
| 5 | Live adaptation | Spots frustration, confusion, interest, a language switch or a rush, and changes the persona mid-call |
| 6 | Voice demo on Sarvam | The same scenario for 2–3 contrasting sellers, with at least one live mid-call switch |

### Expected outputs

- A persona generator running on the sample seller files
- A persona spec for each seller, with the reason for each choice
- A live demo with at least one mid-call switch
- A switch log: the signal detected, the change made, and the reason

### Success metrics

- Fit of each persona to its seller
- Correct, well-timed mid-call switches
- Distinct personas across seller types
- Natural voice in 2+ languages
- Support from past-call evidence

Full requirements, weights and FAQs: [`wiki/projects/vani-hackathon/persona-requirements.md`](wiki/projects/vani-hackathon/persona-requirements.md).

## Approach in one paragraph

Before the call, code builds a context for each seller from their data and past calls. An agent then composes that seller's VANI persona (voice, language, tone, call plan), with a cited reason and an evidence label for each setting. Code checks guardrails and what Sarvam can actually play. During the call, the Sarvam voice agent calls our **signal server** on every seller turn. A lexicon (Devanagari + romanized) detects rush, confusion, frustration, interest or a language switch, and returns a text-level directive (shorter sentences, a check question, an apology, a callback offer). Each switch is written to the switch log. After each call, a review updates the lexicon and the per-seller memory. No model is trained.

**Platform limit (proven):** Sarvam fixes the voice, pace and pitch for the whole call. Mid-call switches can change only the wording, length, tone and language.

Current design: [`wiki/projects/vani-hackathon/system-design.md`](wiki/projects/vani-hackathon/system-design.md) · latest plan: [`outputs/plans/VANI persona architecture plan v5.md`](outputs/plans/VANI%20persona%20architecture%20plan%20v5.md).

## Repository layout

| Path | What is in it |
|---|---|
| `raw/` | Source dumps: organiser deck, PS04 doc, data dictionary, team decisions, research and spike logs. Append-only. Catalogue: [`raw/README.md`](raw/README.md) |
| `wiki/` | Articles compiled from `raw/`. Start at [`wiki/index.md`](wiki/index.md) |
| `outputs/` | Plans (v1–v5 + adversarial review), research reports, spike results, voice checks |
| `app/signal_server/` | FastAPI signal server that the Sarvam agent calls each turn (spike version) |
| `app/spike/` | Spikes: Sarvam call/chat harness, plan-following and stress tests, voice override, Jev, Daytona deploy and egress |
| `app/validate/` | `profile_persona.py`: PS07 data validation (aggregates only) |
| `.claude/skills/` | Team workflows: `wiki-file`, `design-architecture` |
| `data/` | Hackathon seller data from Drive. **Git-ignored**, never committed |

## Setup

Keys go in a git-ignored `.env` at the repo root:

```env
SARVAM_API_KEY=
SARVAM_AGENTS_API_KEY=
OPENROUTER_API_KEY=      # Jev; works only from office IPv4
JEV_MODEL=typesafe/jev-1.13
DAYTONA_API_URL=
DAYTONA_API_KEY=
SIGNAL_TOKEN=            # shared secret between Sarvam tool and signal server
SIGNAL_LOG=calls.jsonl
```

Run the signal server locally:

```bash
cd app/signal_server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Status (as of 2026-10-09, day 1)

### Done and proven

- **Problem chosen** (#4) and requirements mapped to the PS04 scoring and the deck jury rubric.
- **PS07 data validation:** live signals matter (a rush appears in 21% of calls, and meeting rate halves when it does). Script personalisation failed in 3 internal trials. Only about 1 in 10 sellers has durable free text.
- **Sarvam tool path:** the agent calls our tool on 24/24 turns, and our directive steers the reply.
- **Plan following:** the agent follows a passed conversation plan 15/16.
- **Voice:** per-call TTS override from the SDK is **ignored**. Per-language voices + `initial_language_name` **works** (Hindi → female, English → male). `initial_bot_message` works.
- **Jev:** 49/51 correct, about 480 ms, on romanized text from the VPN laptop.
- **Architecture plan v5**, with the adversarial review fixes applied.

### Open, owner, deadline (plan v5 §14)

| Item | Owner | By |
|---|---|---|
| Organiser rulings: may masked seller data go to a frontier model? Does "core agent must be Sarvam" allow a frontier decider? | Team lead | D1 15:30 |
| Decider route (frontier vs. Sarvam-105b fallback); OpenRouter 403 from Daytona / LiteLLM route | Team lead, M | D1 17:00 |
| Signal server host (Daytona DNS/TLS, laptop + tunnel, or internal box) | S, team lead | D1 17:00 |
| Per-call published-version selection; demo channel chosen | S | D1 18:00 |
| `decision_id` echo and variable length limit | S | D1 |
| Sarvam Code Tools enablement (emailed) | Sarvam | — |

### Not built yet

Data contracts (`app/contracts/`), seller context builder, persona composer + guard, directive compiler, production signal server with policy and switch log, the switch-detection precision test, the demo sellers and frozen specs.

### Submission checklist (deck, due D2 23:59)

- [ ] 5–7 min demo video (backup recorded by D2 16:00)
- [ ] Approach note
- [ ] Agent ID / live link
- [ ] Code folder + this README
- [ ] `skills.md`
- [ ] Sample outputs: a persona spec for every sample seller + the switch log

## Rules we follow

- The core voice agent is **Sarvam**. Only IndiaMART infra (Sarvam, OpenRouter, internal LiteLLM incl. Jev, self-hosted Daytona) plus open source. No new outside vendors.
- No pre-built solutions. The core logic is ours.
- Seller data stays in `data/`. Only aggregates go into `raw/` and `wiki/`: never seller names, messages or recordings.

## Links

- Sarvam docs: https://docs.sarvam.ai/
- Sarvam platform notes we verified: [`raw/research/2026-10-07-sarvam-platform-docs-check.md`](raw/research/2026-10-07-sarvam-platform-docs-check.md), [`raw/research/2026-10-07-sarvam-deploy-sdk-docs-check.md`](raw/research/2026-10-07-sarvam-deploy-sdk-docs-check.md)
