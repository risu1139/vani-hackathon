# AGENTS.md

Knowledge base + build for the VANI Voice AI Hackathon 2.0 (IndiaMART, 9–10 Oct 2026).
Start every task by reading `wiki/index.md`.

## Layout — no other top-level dirs (except build code, e.g. `app/`, `.claude/`, and git-ignored `data/`)

- `raw/` — source dumps. Append-only: never edit, move, or delete.
- `wiki/` — compiled articles derived from `raw/`. Index: `wiki/index.md`.
- `outputs/` — derived artifacts (persona specs, demo scripts, skills.md drafts).

## Hard constraints

- Every wiki claim must trace to `raw/` or another wiki article.
- Every wiki article starts with `Sources: [[<raw-stem>]]`, and every wiki write updates `wiki/index.md`.
- Hackathon data (Drive `1gT2J-2vLgp_dNMkm_ClcoXNhKKbyiGAK`) lives only in git-ignored `data/`. Only aggregates go into `raw/`/`wiki/`, never real seller names, messages, or recordings. Keys live in git-ignored `.env`.
- Build with what IndiaMART infra gives us access to (Sarvam, OpenRouter, internal LiteLLM gateway incl. Jev, self-hosted Daytona, internal data sources) plus open source. No new outside vendors. The core agent must be Sarvam.
- No pre-built solutions (deck rule: disqualification). Frameworks are fine; the core logic must be ours.

## Workflows

- Filing anything into raw/wiki → `wiki-file` skill.
- Designing or changing any architecture block → `design-architecture` skill.
