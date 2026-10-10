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

## 6. Questions for you

1. Do you approve `hierarchy.json` v2-draft-3? The other session waits for this before it changes `prior.py`.
2. Do you approve the launcher changes in section 3? They remove your Gmail/Drive tools, and the project and user settings, from the agent's run.
3. Can I start the build in the order of section 5?
