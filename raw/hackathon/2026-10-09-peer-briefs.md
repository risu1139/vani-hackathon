# Peer session briefs received on 2026-10-09 (aggregates only)

Two peer Claude sessions answered our questions on 2026-10-09 over Remote Control. They are recorded here so the plans can cite them.

## 1. seller-data-coverage-demo (the data agent, block B1 seller context)

The field selection was still pending their user's approval: "available + recommended", not final. Their detailed files are in the voice-ai-hakethon repo, branch lakshay_dev:
- outputs/plans/Seller context B1 implementation plan.md;
- outputs/seller-data-sources.md;
- outputs/seller-context-apis.md.

**Sources** (offline snapshots copied into git-ignored data/; static, no refresh):
- **PS07 persona files**, 1 Apr–30 Sep 2026: 149,363 sellers; 269,455 answered bot calls; 278,332 evaluator JSON rows (10 evaluators); 12,788 transcribed calls (139,555 turns); 67,151 executive calls.
- **Global Context**, 1 Apr–2 Oct: 5,000 sellers, all also in PS07. Adds company and plan, enquiries with text and read time, enquiry reply threads, buyer PNS calls with talk seconds, buyleads bought (16 Aug–1 Oct), WhatsApp delivery/read events, WhatsApp chatbot text with intents, and AI-extracted buyer-call details including the languages spoken.
- **Best-Time-to-Call**, Apr–Sep: 530,748 dial attempts (261,293 unanswered) covering all PS07 sellers. Gives dial time, outcome, attempt number, hot-lead bucket, callback/next-retry slot and lat/long.
- **Seller Onboarding (PS06)**: 5,000 verified sellers, 151 overlapping PS07. Gives contact_designation, all categories, products, catalogue health and the 106,619-MCAT taxonomy.
- **Internal APIs**: documented only, never called. They are getContext (exchange.intermesh.net), imdwh Customer Scorecard / PNS chart / product mapping, leads.imutils and users.imutils. Auth and reachability are unknown. Plan: use files for history; use APIs only for current state in the live demo, falling back to files.

**Coverage** (% of 149,363 PS07 sellers · % of the 5,000 Global Context sellers):

| Item | PS07 | GC |
|---|---|---|
| bot calls | 87.1 | 87.9 |
| summaries | 85 | 87 |
| recordings | 78 | 79 |
| evaluator (any) | 60 | 62 |
| transcripts | 7.8 | 8.4 |
| executive calls | 4.6 | 5.4 |

- **Cold sellers** (no bot call): **19,234 (12.9%)**.
- **Evaluator detail:** disposition 51%, seller_questions 14%, objections 3.3%.
- **Profile fill:** city 100; business type 98; turnover 89; nature of business 89; top categories 97/94/88.
- **Non-zero engagement:** cqs 61; enquiries (90 days) 19; PNS received (90 days) 14.
- **Global Context only:** enquiries 55, WhatsApp 74, chatbot 60, buyer calls 41, call languages 28, BLs bought 5.
- **Sparse flags:** showed_frustration 139 sellers; asked_if_bot 125; DNC 1,178; already_with_exec 4,205.

**Callee:**
- The disposition shows "not decision maker" on 1,936 calls (1,634 sellers) and wrong_number on 5,328.
- alternate_person_designation is filled for 953 sellers: family 48% (husband/son/papa), owner/boss 44%.
- No source gives a designation per phone number.

**Gaps:**
- seller gender: none anywhere;
- language: measured for only 28% of Global Context sellers (0.9% of PS07), so the rest fall back to state;
- per-number designation: none;
- the September relabelling (fit Not Interested priors on August only);
- the Global Context pool is biased toward multi-channel-active sellers.

**Demo pool:** the Global Context 5,000; **805 have ≥5 of 8 rich sources**; add one cold seller.

**Output contract:**
- One JSON per seller per as_of: `data/contexts/<glid>_<as_of>.json`, built by `app/context/build_context.py --glid --as-of` (to build).
- Schema: `app/contracts/seller_context.schema.json` (to build).
- Fields: profile, engagement, as-of history (rebuilt from bot-call rows; the past_* columns leak), timing, free-text memory facts, language, speech style, callee, demand, phone, plus field_sources (source + date per field), missing_fields and completeness.
- Join key: GLID.
- Already built: `app/context/seller_inventory.py`, indexing 31 sources into data/index/seller_coverage.csv.

**Data handling:**
- Raw data stays in data/.
- Off-premises models get non-PII fields plus masked free text.
- No GST/PAN/ID numbers.
- Contact name is sent only as a token for the greeting; address is coarsened to city/state.

## 2. bash-quoting-testing-analysis (Redash dashboard bot, one skill end to end)

Repo on this machine: `/mnt/c/Users/Imart/redash-dashboard-automation`, branch live-stable (remote scm.intermesh.net indiamart/redash-dashboard-automation).

- **Skill layout:**
  - One SKILL.md (~500 lines) with a numbered procedure.
  - One reference file per decision point, loaded on demand.
  - scripts/ for the deterministic parts (find tables, verify SQL, verify dashboard with screenshots, sealed append-only requirements list, knowledge store).
- **Data flow:** steps chain through files in a per-thread session directory. Input is turn.json, evidence goes to output/checks.jsonl, and the only output read back is **output/status.json**, a fixed contract (status done|answered|awaiting_input|error, …).
- **Enforcement** is by root-owned hooks the agent cannot edit, wired through managed-settings:
  - a Stop hook refuses to end the turn without the required outputs, and collects all refusals into one message;
  - a PreToolUse hook blocks creation before requirements are sealed.
- **Trigger:**
  - email → n8n → a reconciler runs run-turn.sh in the sandbox;
  - `claude -p` runs headless under `script` (a PTY; without it, plain non-TTY exec blocks);
  - flags: --dangerously-skip-permissions, --strict-mcp-config with an explicit MCP config, --settings <managed> --setting-sources '', and an explicit --model;
  - follow-up mails resume with --resume.
- **Credentials:**
  - a per-requester key is passed in turn.json, stripped by the run script, and exported as an env var;
  - a status.json is always written via trap;
  - one retry if there is no assistant message;
  - external writes are recorded before and after the action, so a retry doesn't duplicate them.
- **Where:**
  - one Daytona sandbox built from a custom snapshot: Dockerfile with a pinned CLI version, root-owned hooks, the skill as a plugin dir;
  - Claude login via SSH once per rebuild. **The Anthropic API is reachable from the sandbox**; OpenRouter is not needed;
  - pin the CLI: an upgrade once silently dropped all hooks.
- **Lessons:** enforce with hooks from day one; use absolute paths; test stubs must not read stdin under `script`; keep one owner for side effects; make the agent's only output a file.
