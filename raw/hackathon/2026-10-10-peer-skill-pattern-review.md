# Peer review of the VANI persona skill pattern (2026-10-10)

Source: the peer session "bash-quoting-testing-analysis" (the Redash dashboard bot, one skill end to end). It answered our question about the design (short ordered initial context + big seller file read on demand + agent-callable scripts + validators). Paraphrased from their message; their verdict is quoted.

**Verdict:** "Your design fits the pattern well; my changes are about making the important steps enforced rather than suggested."

1. **Initial context + on-demand file + scripts:** the right pattern. But agents under-read more often than they over-read: in their runs, resumed turns skipped an on-demand reference and silently skipped a step.
   - Anything that must happen goes in the always-loaded text or in a gate, never only in an on-demand file.
   - Give each big-file section a stable heading, and say exactly when to open which ("before choosing a hook, read §Enquiries").
   - For proof of reading, make the agent cite the section id and the fact in the persona JSON. A validator checks that the citation exists.
2. **Facts by script before the agent; judgement in reference prose.** Compute traits, states, evidence and dates in code: deterministic, testable and cheap. Keep the judgement rules (which hook fits which state, tone) in a reference file, and re-check the hard constraints in a validator. Rule of thumb: whatever can be a pass/fail check belongs in code.
3. **Making the agent call scripts:**
   - Scripts append their own evidence rows (to `checks.jsonl`). A Stop hook refuses to end the turn without the required rows (e.g. a peer_stat row, or "skipped: <reason>").
   - A PreToolUse hook blocks the downstream action (writing Sarvam variables) until the prerequisites are recorded.
   - The Stop hook gets only one forced continuation per turn, so collect all refusals into one message.
   - Gates must apply the consumer's exact rules.
   - Hooks are root-owned, outside the agent's writable paths, and wired through managed settings.
4. **Changes they recommend:**
   - Make the persona JSON schema a script (`validate_persona.py`) that the Stop hook runs. Write the Sarvam variables only from a script that refuses an unvalidated file.
   - Cache peer_stat / showcase_lead results per GLID, and record "called" or "skipped with reason".
   - Use absolute paths everywhere: the Read tool expands neither `~` nor `$VARS`.
   - Always write one status file, even on failure.
   - Pin the Claude Code version, and re-verify the hooks after an upgrade.
   - Test the gates with stubs in both directions: they must refuse the bad case and stay quiet on the good one.

Their repo pointers (branch live-stable): `snapshot/stop-gate.py`, `snapshot/pre-gate.py`, `snapshot/skill/redash-dashboard/scripts/requirements.py`, `snapshot/test/stop-gate.py`.
