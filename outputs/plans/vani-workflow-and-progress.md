# VANI persona system: high-level workflow and progress

As of commit `4cdf93d` (2026-10-10). Written from the repo, the commit log and the cross-session messages. Items marked *not verified* are things the code says it does that I have not run myself.

## 1. The workflow in one picture

```
 SELLER GLID
     |
 [1] CONTEXT (laptop, VPN)         builder: offline files + APIs + Redash  ->  data/contexts/<glid>/   (INDEX, core, business, catalogue (D08 top MCATs), buyleads, enquiries, channels, peers, candidate_leads, calls/, context.json)
     |
 [2] EXPORT (laptop)               pseudonymise names/competitors, PII gate, strip sources and gap notes  ->  data/agent_export/<pseudo>/  (+ name map stays on the laptop)
     |
 [3] PERSONA DESIGN (Daytona sandbox, Claude Opus 5.5, skill "vani-persona")
        facts.py      traits, states, guards, hook eligibility, start rules (script)
        prior.py      top-2 personas (weighted draw), voice prior, per-field brief (script; reads references/hierarchy.json)
        persona_tool  probe (search files per field), decide, finalize (script writes the persona)
        agent         selects 1 of the top-2, decides each field: seller_evidence > hierarchy > start_persona, each with a searched note
        gates         read log, pre/stop gates, validator (cites, quotes, ranges, banned words, brief match)
     |
 [4] COMPILE (laptop)              fill names back, Sarvam variables + final prompt  ->  05_sarvam_vars.json, 06_sarvam_prompt.md
     |
 [5] CALL (Sarvam Voice Agent "VANI-person" v2+)
        OnStart tool            voice, pace, pitch, start language, opening line
        read_seller_signal      keyword classifier lex-v2 -> mood + directive each turn (Jev dropped: too slow)
        book_meeting            meeting_fixed + slot
        test routes             SDK voice session; real phone call to a whitelisted test number (place_call.py)
     |
 [6] COLLECT + REVIEW              analytics API -> 06_call.json, 07_outcome.json -> Claude review 08_review.json (fatal / non-fatal QA)
     |
 [7] LEARN (between calls)         loop2: scoreboards (persona, voice, fields, reasons, hooks, start rules; test calls to a test board)
                                   loop1: switch keyword proposals checked on a gold set, human approves
```

One command runs steps 1 to 6 and the test-mode loops: `python app/e2e/vani_e2e.py --glid <GLID> [--phone +91...] [--no-call]`.

## 2. Who owns what

| Area | Owner | Main files |
|---|---|---|
| Data extraction, builder, export, D08/X06 fields | Our session (Lakshay) | `app/persona/seller_context_builder.py`, `export_for_agent.py`, `app/context/` |
| Hierarchy file, prior, learning step, review documents, objections, compliance rubric | Our session | `references/hierarchy.json`, `scripts/{hierarchy,prior,loop2_update}.py`, `outputs/` |
| Skill enforcement, validator, persona tool, launcher, start rules, Daytona deployment, e2e, Sarvam tools and calls | Persona/Sarvam session (Rishav's side) | `.claude/skills/vani-persona/`, `app/daytona/`, `app/e2e/`, `app/sarvam/`, `app/loops/` |

## 3. Progress by stage

| Stage | State | Evidence |
|---|---|---|
| 1 Context builder | **Done** (offline and live modes) | 10 demo folders rebuilt; D08 and X06 added; no source lines in `.md`; tests pass |
| 2 Export + PII gate | **Done** | sources, gap notes, `all.md` stripped; hard gate refuses on any hit |
| 3 Persona design | **Built, hardened** | enforcement plan reviewed; probe/decide/finalize; gates; forged-ledger and bypass tests; reasons per field |
| 3b Hierarchy v2.0 | **Done and pushed** (`0adbc66`, `b36a28f`) | L0 to L6 nested, brief in `03_prior.json`, start rules with grades |
| 3c Daytona sandbox | **Deployed** (commits `3571cb6`, `99ecf27`) | root-owned install, separate agent user, pinned CLI, per-run isolation; checks reported passing (pytest 106, good, bypass, forged, hang). *Not verified by me.* |
| 4 Compile | **Done** | `compile_vars.py`, city fix for Daytona runs |
| 5 Sarvam call | **Working on test routes** | agent v2 published; labels list includes my 6 objection categories; SDK voice session; phone call by API to a whitelisted number (`place_call.py`); first real voice call went through both loops earlier |
| 6 Collect + review | **Done** | `collect_call.py` retries until analytics lists the call; rubric file ready to wire (`outputs/compliance-rubric.json`) |
| 7 Learning | **Built; no real data yet** | scoreboards are empty; test calls go to `data/scoreboards_test` |
| E2E one command | **Code present** (`cf97e3e`, `4cdf93d`) | live run results across all 10 demo sellers *not verified by me* |

Test status on my machine: 146 tests pass (skill tests, persona tests, collect-call tests). The Sarvam-SDK tests (`app/loops`, `app/sarvam/tests/test_vani_tools.py`, `test_regional_lexicon.py`) need the SDK installed and were not run here.

## 4. What is left

**Before the demo freeze (D2 12:00)**
- Run the other demo sellers end to end (cold seller, do-not-call seller, rural NSD seller were still open), then pick 3 to 4 for the demo.
- Wire the compliance rubric into the call review (the persona session said they will).
- Re-check the tightened search terms with the persona session's probe, and fix any that over- or under-match.
- Slide, `skills.md`, video script; honest timeline of what was built on 9 to 10 Oct.
- A native speaker to check the 84 South-Indian test labels.

**Open decisions (need a person)**
- Approve the persona library v0 (still pending Rishav) and keep or change the 15% P0 holdout (decided: keep).
- Mid-call mood classifier: keep the keyword tool (`lex-v2`, 0.60 accuracy on the test set) or add the Sarvam chat model for unclear turns, or a small trained classifier. Cowork is not usable (no API).
- Sarvam MCP sign-in (server added locally, needs your SSO login) so agent changes can be made from files instead of the console.
- A Sarvam Voice Agents key was pasted into the chat; rotate it if the transcript leaves your machine.

**Known limits (accepted for the demo)**
- Voice stays female by default; male voice results come only from agent decisions with seller evidence, so the voice question cannot be learned yet.
- Scoreboards start empty: every persona pick is the division lean plus a random draw until real calls arrive.
- Live values (AOV, peers, GST state, top MCATs) are not safe for replaying past calls.
- NSD/CSD split of objection rates: done with the rule is_catalog = -1 for paid (CSD), `outputs/objections_split.json`; CSD has only 546 calls.
- Production calls to real sellers need a telephony connection and the outbound API; the current phone route only reaches whitelisted test numbers.

**Later**
- A hook based on the seller's top category (D08 data is ready).
- Independent check of AOV figures; Telugu, Tamil, Kannada, Malayalam turns from real calls for the gold set.
- Delete the pasted-key exposure risk by rotating the key; never store keys in files.

## 5. Constraints that stay fixed

- Never say AI, bot, branch manager or account manager; sidestep once, say "virtual assistant" if pressed; never claim to be human.
- Numbers only from verified facts; no plan, price or guarantee on the call; never name a buyer or competitor.
- The agent sees only the pseudonymised folder with no source information; names are filled back on the laptop.
- Real seller data and secrets stay in git-ignored `data/` and `.env`; only aggregates go into `raw/` and `wiki/`.
- Sarvam is the core voice agent; Claude designs and reviews; the Sarvam chat model is not used for persona decisions.
