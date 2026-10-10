# Persona enforcement: build plan (for review before the build)

Written 2026-10-10 in ASD-STE100.

**Purpose.** This plan makes the persona rules compulsory through the skill's hooks and scripts. The rules are the user's decisions and are written in `references/hierarchy.json` (v2-draft-3, commit 91d6c29).

**Standard.** We copy the patterns of the Redash skill (`redash-dashboard-automation/snapshot`), which passed many review rounds.

## 1. The rules to enforce

1. The script gives the top-2 personas. The agent selects 1 of them. The selected persona is the base.
2. Each field must have a reason type, in this order:
   - `seller_evidence`: cites, with quotes, from the gated search;
   - `hierarchy`: data for similar sellers (level, value group, number of calls, rate). Only when the search found no evidence;
   - `start_persona`: the field keeps the value of the selected persona. Only when there is no evidence and no hierarchy data.
3. The search is compulsory and comes before each decision. Only the probe script records the search. The read log does not count.
4. A claim "no evidence" is not trusted. The validator does the search again. Each match must be used, or rejected with a reason.

## 2. The flow in one run

```
launcher (run_persona.py)
  1. facts.py, prior.py -> 01_facts.json, 03_prior.json (copies + hashes, before the agent starts)
  2. hash: skill folder, hierarchy.json, facts, prior (to find changes later)
  3. claude -p (settings outside the run dir, no other settings, no MCP, sandbox CLAUDE.md added)
agent (the skill steps)
  4. probe.py select --persona P2      -> refused unless P2 is in 03_prior top-2
  5. probe.py --field <f>  (each field) -> hits with cite-ready ids, logged by the script
     probe.py --hook <h>   (each eligible hook)
  6. probe.py seal                     -> refused while a field or hook has no probe row;
                                          writes probe_checklist.json: per field the hits, the allowed
                                          reason types, the start value, the range
  7. write 02_review.json, 04_persona.json
hooks
  8. PreToolUse (order gate): refuses the write of 04_persona.json until "probes_sealed" exists
  9. Stop gate: runs the validator; collects ALL failures in 1 message; 1 retry only
launcher, after the agent
 10. validates again (does not trust the agent's status); compares the hashes;
     if there is a failure: status = error, and no Sarvam variables
 11. compile_vars -> Sarvam variables, only after a pass
```

## 3. What changes, file by file

| File | Change | Reason (snapshot lesson) |
|---|---|---|
| `scripts/probe.py` | Add the sub-commands `select`, `--field`, `--hook` and `seal`. Hit ids are cite-ready (`calls/C02#C02.T3`, `core.md#B03`). Read errors are replaced, not fatal. Section headings such as `### B01:` also match. | A script records the evidence, so the gates do not parse Bash for reads. The ids must pass the cite check. |
| `gates/pre_gate.py` | The order gate looks for the `probes_sealed` row. It refuses when the row is missing. It allows only when the gate cannot understand its input. Windows path compare with normcase. Every refusal gives the exact command to run. | Refuse on missing evidence; allow on gate confusion. |
| `gates/stop_gate.py` | Collect all failures and give 1 numbered message with the fix for each. On the 2nd stop, exit at once. Add try/except. | 1 refusal only; no loop. |
| `scripts/validate_persona.py` | Add the rules of section 1, per field from hierarchy.json:<br>- reason type;<br>- checklist agreement;<br>- the search done again, and each hit used or rejected;<br>- hierarchy data must agree with the brief;<br>- start_persona = the value of the selected card;<br>- ranges and value groups.<br>Hooks use the probe log only; the read-log rule goes. Facts and prior come from the launcher copies (01, 03). `chosen` is checked against 03_prior. | The validator must not trust what the agent writes. |
| `run_persona.py` | Settings file outside the run dir and read-only. `--setting-sources ''`, `--strict-mcp-config` (empty), no web tools, `--append-system-prompt-file sandbox/CLAUDE.md`, hook timeouts. Write `as_of` and `VANI_PY` (this Python). Delete any old status.json at the start. Run claude without a shell, and stop the whole process tree on timeout. Hashes before and after. Validate again after the run, and never skip it because the agent wrote "do_not_call". | The agent must not be able to switch the hooks off. Status on every path. |
| `gates/log_read.py` | Also record each probe.py command and a hash of its output. | The probe log must agree with the tool log, so it cannot be forged. |
| `SKILL.md`, `sandbox/CLAUDE.md` | New steps: select, probe, seal, decide with a reason type. Absolute script paths with `$VANI_PY`. A table: which reference to read, and when. Remove the old "fixed change list" and "do not run scripts" lines. | The skill text must not disagree with the gates. |
| `references/formats/persona.json` | Each field: value, reason_type, reason, cites, searched, hits_rejected, hierarchy {level, value_group, n, rate}, confidence, evidence. | |
| `tests/` | Order gate: refuse and allow cases. Bash commands that MUST pass. Stop-gate scenes, with 2 faults at the same time. The command in each refusal must really run. 3–5 cases from bad personas (evals). | Test both directions. |

## 4. Points to check against hierarchy.json (v2-draft-3)

1. The fields `hook` and `opening` have text, not lists, in `probe_files`. Hooks use the top-level `hooks{}`. Opening uses `calls/` with no value groups. The validator treats them as special cases.
2. `language_start` and `voice_id` have text "ranges". The validator applies only number ranges. `compile_vars.py` already refuses an unsupported language.
3. The brief for `hierarchy` reasons (level, n, rate) comes from `prior.py`. That is the other session's part, after your approval. Until then the scoreboards are empty, so no field can use `hierarchy`. Each field is `seller_evidence` or `start_persona`.

## 5. Order of work

1. The other session's `prior.py` / `loop2_update.py` change (after your approval of hierarchy.json).
2. Mine: `probe.py`, then the validator, then the gates, then `run_persona.py`, then SKILL.md and the format, then the tests.
3. 1 end-to-end run with Opus 5.5 on the CSD demo seller, then the cold seller and the do-not-call seller.
4. Peer review by the Redash session (bash-quoting-testing-analysis).

## 5a. Revision after the critical review by the Redash peer (2026-10-10). This section replaces sections 2-3 where they differ.

1. **A script writes the persona.** The agent never writes `04_persona.json` or `02_review.json` itself. Tool: `scripts/persona_tool.py`.
   - `select --persona P2`: refused unless P2 is in the top-2 of 03_prior.
   - `probe --field f` and `probe --hook h`: hits with cite-ready ids, ranked by the script.
   - `decide --field f --value v --type seller_evidence --cite <id> --quote "..." --reason "..."`. It is checked at write time:
     - the selection was done, and the probe ran;
     - the cite is one of that field's hits, and the quote is in the cited file (normalised);
     - the range and the value group are correct;
     - the type is allowed: seller_evidence first; hierarchy only with matching brief data; start_persona = the card value;
     - for hierarchy or start_persona, the script's top-3 hits each have a one-line answer (`--answer <hit id>="..."`).
   - `hook --id h --decision primary|backup|rejected --reason "..." --cite ... --quote ...`: the same checks as today's hook rules.
   - `text --file draft.json`: the spoken parts only (opening, identity line, call plan, objections, escalation, guardrails, verified facts, personalisation). The tool refuses fields in it.
   - `finalize`: refused while a field or hook has no decision. It joins the decisions and the text, runs the full validator, and writes `02_review.json` and `04_persona.json` with a sha256.
2. **Gates become simple.**
   - The PreToolUse gate denies every direct Write, Edit or MultiEdit of `04_persona.json`, `02_review.json` and the decisions log.
   - Bash bypasses are caught after the turn: the file sha must equal the sha that finalize recorded, and the validator runs again.
   - The PostToolUse read log, the output hashes, the Edit simulation and the Bash regex guard are dropped.
3. **Fixed inputs.** The launcher copies the seller folder into `<run>/seller/`, hashes it, and gives the agent only that copy. The validator searches the same copy.
4. **Hits: the top-3, not all.** "Each hit rejected" is replaced by 2 rules:
   - the cited evidence must be one of that field's hits;
   - for hierarchy or start_persona, the script's top-3 hits each have an answer.
   Too many hits is fixed by tighter search terms (other session).
5. **Quotes are normalised on both sides.** Case is folded, curly quotes become straight, spaces collapse, and line breaks are ignored.
6. **The launcher:**
   - a unique run dir, with every gate input cleared at the start;
   - status.json on every exit path (try/finally);
   - the validator runs from the launcher's own copy, and its hash is checked before it runs;
   - CLI version pinned and logged;
   - a **self-test** launch that must show a Stop refusal;
   - the model is checked in the run log;
   - one retry only if no assistant message came;
   - the exit code means "the launcher finished", and is separate from the result.
7. **Windows limit.** Read-only files and hashes show tampering but do not stop it, because the agent runs as the same user. The launcher fails closed on any hash mismatch. The real boundary is Daytona Linux, with root-owned hooks and settings under /etc.
8. **Evals in both directions.** Bad personas must fail. Good personas with little evidence (cold seller) must pass.
9. **Refusal messages.** They list up to 6 problems per message, each with the exact command that fixes it.
10. **Bypass test** (requested by the reviewer). In an eval, a stub agent writes `04_persona.json` with Bash and does not use persona_tool.py. The test passes only when:
    - the launcher's check after the turn (the sha against the finalize sha, and the validator) gives status=error;
    - **no** Sarvam variables are written.
    This proves that the backstop catches the one path the gate cannot see.
11. **Fail-closed tests** (requested by the reviewer). Each step fails in turn:
    - persona_tool.py exits non-zero;
    - the validator crashes;
    - the hash file is missing;
    - the seller copy changes;
    - claude exits with no output;
    - the launcher is stopped during the turn.
    Each of these runs must end with status=error, a reason, and no variables. A half-written success must never occur.

## 5b. Review log

| Date | Reviewer | Result |
|---|---|---|
| 2026-10-10 | Redash peer (bash-quoting-testing-analysis), 1st review | Gate bypassable through Bash; hits_rejected noise; over-built logging. Changes in 5a items 1-9. |
| 2026-10-10 | Redash peer, 2nd review | "Revised plan looks sound." It added items 10 and 11. Waiting for explicit approval of the plan with 10-11. |

## 6. Questions for you

1. Do you approve `hierarchy.json` v2-draft-3? The other session waits for this before it changes `prior.py`.
2. Do you approve the launcher changes in section 3? They remove your Gmail/Drive tools, and the project and user settings, from the agent's run.
3. Can I start the build in the order of section 5?

## 5c. Start values (user decision 2026-10-10, after the review)

1. A "start_persona" value is deterministic: the selected card's value, changed only by the state rules in `01_facts.json` → `start_rules`. There is no random draw and there are no ad-hoc defaults.
2. Every card defines `voice_gender` (F, the team default) and `empathy`. `language_start` comes only from the rules.
3. Rules, in fixed priority (first match wins), each with an id and an evidence grade:
   - **Voice:** `voice.female_seller` (WEAK), then `voice.tense` (WEAK), then `voice.rural_hindi_belt` (GUESS).
   - **Language:** `lang.high_value` → English (GUESS), then `lang.regional` (WEAK).
   - **Empathy additions:** `emp.grievance` (WEAK), `emp.frustrated` (GUESS), `emp.rushed` (GUESS).
4. A fired rule wins over the card. The persona records the rule ids in `dimensions[field].start_rule_ids`, so learning can report results by rule.
5. **Known limit (accepted for the demo):** the voice question cannot be learned while every card is F and the rules point only to F. Male outcomes come only from agent decisions with seller evidence.
