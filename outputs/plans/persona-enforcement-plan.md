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
| 2026-10-10 | Redash peer, review of 5d | Not approved yet: number sources, trimming order, adjacency and coverage of names, the year, a leak check before upload. Fixed in 5d item 7. |

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

## 5d. What VANI knows during the call (user decisions 2026-10-10)

The problem (phone call 2026-10-10): the seller asked about the hook and about VANI, and VANI could not answer. Sarvam got one hook, 3 facts and the phases. It got no states, no traits, no other hooks, no handler and no IndiaMART reference content.

1. **Short seller block.** It is a new per-call variable, `prompt_seller` (`@prompt_seller` in the skeleton, under Facts). `compile_vars` builds it from `01_facts.json` and `04_persona.json` with code. No LLM writes it. The cap is 2,500 characters, and `compile_vars` fails when the block is longer. It holds:
   - **States:** the value and the "as of" date of each state that has evidence. For example: last call busy, 3 days ago; no executive contact in 60 days; an open complaint.
   - **Traits:** division, plan, years on IndiaMART, seller type and city tier.
   - **Main hook:** the main hook (as now) with its details: each cited fact from `facts_for_claim`, in the call's language.
   - **Other hooks:** each other eligible hook gets one pointer line with its cited fact. VANI uses a pointer only when the seller asks, or after the main hook fails twice.
   - **Handler:** the handler fact (see item 3).

   Every number in the block comes from `verified_facts`. The validator check on numbers covers this block too.
2. **Similar sellers by name (user rule, replaces "peers only as aggregates").** VANI may name a nearby seller of the same category: the company name, that it is a paid IndiaMART seller, its city, and since when it has been on IndiaMART. VANI may not give any other detail of that seller: no phone, no person, no catalogue address, no lead data.
   - The data has no figures (earnings, leads used) for one named competitor. Figures come only from the peer aggregates (E08 local paid-seller count, E11 same-size median leads), and VANI says them as aggregates. It never puts a number on a named seller.
   - The agent writes the peer fact with the `{COMPETITOR_n}` token and the cite `peers.md#E08`. `compile_vars` fills the name on the laptop only.
   - The validator rule `OTHER_SELLER` changes. It now allows `{COMPETITOR_n}` in a `verified_facts` line that cites `E08` and holds no number. It still refuses `{BUYER_COMPANY}`, `{COMPETITOR_n_ID}` and `{EXEC_NAME}`.
   - Who else must do something:
     - **Data session:** add the paid flag for each competitor (the `custtype` table: `custtype_name` → `paid`).
     - **Data session:** fix one token leak. One competitor `catalog_url` still holds the plain name.
3. **Handler (proposal from the data session, accepted).**
   - A new state `state.handler` with the detail `{sales: person|pool, tele: person|pool|same}`, from `core.md#H02`.
   - It gives one allowed fact in the call's language: "hamare IndiaMART executive {SALES_EXEC}", or for a pool, "hamari IndiaMART team".
   - `compile_vars` and `review_call` learn the tokens `{SALES_EXEC}` and `{TELE_EXEC}`.
   - The prompt rule: when the seller asks who handles the account, VANI uses that fact only. If there is no fact, VANI offers a callback. VANI never says a phone number, an email or a designation, and never says "account manager".
4. **IndiaMART knowledge base (shared, one for all sellers).** It is one Sarvam KB, "IndiaMART reference", attached to the agent once. It is not changed for each call.
   - **Contents:** what buy-leads and credits are; how leads are filtered and used; enquiries and PNS calls; the catalogue and profile; what the meeting with the executive is; who VANI is; the plan types without prices.
   - **Sources:** the files in `raw/` and the hackathon documents. Each section names its source. The file is `outputs/kb/indiamart-reference.md`.
   - **The KB description tells the agent:** search it for questions about IndiaMART services. Do not search it for this seller's own data (that data is in `prompt_seller`).
   - **Uploading:** the KB API works only with the console login (our API key gets 401). The upload is done once, in the browser.
5. **Meeting.** (Done: commit 44b0cab.)
   - VANI asks for a day and a time.
   - If the seller gives none, VANI asks once for a time on the next day.
   - If there is still none, VANI says that an IndiaMART executive will call the seller to set the time.
   - `book_meeting` refuses a slot outside 9 AM-6 PM.
   - When the seller says a time, VANI is pushed to call `book_meeting`.
6. **Tests.**
   - The cap on `prompt_seller`.
   - The numbers check on the block.
   - The peer-name rule: a name with no number is allowed. A name with a number is refused. `{BUYER_COMPANY}` is refused.
   - The fill of the handler tokens.
   - Re-run all the tests in the skill and in `app/`.

7. **Changes after the Redash peer's review (2026-10-10).** These replace items 1-4 where they differ.
   - **Where the numbers come from.** A number in the seller block must come from `verified_facts` or from a state or trait value in the frozen `01_facts.json`. Dates such as "3 days ago" and counts such as "60 days" therefore pass. The check records the source of each number.
   - **Trimming.** `compile_vars` cuts the block in a fixed order. First it drops the pointers to the other hooks (the last one first). Then it drops the trait lines. It fails only when the main hook, the states and the handler are longer than 2,500 characters by themselves. It counts the characters after the names and the language are filled in.
   - **Values only.** The block holds values and a fixed label for each state, for example "open complaint: yes". It never holds free text from the seller (complaint wording, catalogue text). Free text could inject instructions into the voice agent.
   - **Year of a named seller.** VANI says it only in words, for example "kai saalon se IndiaMART par", and never as a number. The rule "no number about a named seller" therefore has no exception.
   - **Adjacency.** A spoken unit is one sentence, one call-plan step or one objection response. A unit that holds `{COMPETITOR_n}` holds no number. No aggregate follows it in the same step. An aggregate is always said about the group, for example "aapke sheher ke paid sellers average mein ...". The same rule goes into the prompt, for what VANI says that is not in the script.
   - **Coverage.** `{COMPETITOR_n}` is refused everywhere: call plan, objections, opening, hook text. The one exception is a step that cites the E08 fact. In that step the adjacency rule applies.
   - **One switch.** `references/policy.json` holds `peer_naming: on`, the user's decision of 2026-10-10. Set to `off`, it turns the naming of peers (and the word "paid") off, with no code change.
   - **Leak check before upload.** `deploy.py` scans the pseudonymised seller folder before the upload. It looks for every real name in the laptop's token map, and it uses a regex for email addresses and phone numbers. It refuses the upload if it finds one. After the fetch, every `{TOKEN}` in the outputs must be a token that `compile_vars` knows. An unknown token fails the run and is never spoken.
   - **Simpler.** The rule "use another hook when the main hook fails" is only one prompt instruction, with no code. The handler detail is only "person" or "pool". The phone handler `{TELE_EXEC}` stays in the map, but the persona does not say it.
   - **Knowledge base.** It is uploaded by hand, one time. The uploaded file, its sha and the upload date are committed in `outputs/kb/`. They show which KB version a call used.

## 5f. Call-behaviour rules: one file, used by every layer, checked before and after the call (2026-10-10)

The problem. Three phone calls on 2026-10-10 (free seller, run e2e-20261010-174118-480222) show faults that no file holds and no check catches:
- VANI asked for the meeting in 8 of 13 replies, even right after the seller asked a question. The seller said: "बार-बार मिलने के लिए पूछे जा रहे हो, पहला मेरी इंफॉर्मेशन तो बताओ".
- VANI said the same fact ("26 requirements") 3 to 4 times.
- The seller asked for his executive's name 3 times. VANI gave the same dodge each time. For this seller the data has no person (H02 is a pool), so the true answer is: "our IndiaMART team handles your account; the executive's name comes with the meeting".
- VANI ended the call right after booking. It did not ask "anything else?".

Today the push to the meeting comes from 3 layers, and none of them limits it:
- the agent's call plan (each step ends with an ask);
- the fixed phases in `render_prompt.py` (Phase 3, the backup hook);
- the directives of `read_seller_signal` (interested → "move to the meeting day"; declined → "ask if another day suits").

### What changes

1. **One rules file: `references/call_rules.json`** in the skill.
   - Each rule has: `id`, `say` (the text VANI gets), `layers` (agent text, phases, live tool), `pre_check` (a validator check id, or none), `post_check` (a review check id), `evidence` (the call and the turn that showed the fault), and `added` (the date).
   - New rules are added only to this file.
   - First rules:
     - **R1 answer-first.** When the seller asks something, answer it fully. Do not add a meeting ask to that reply.
     - **R2 meeting-pace.** Ask for the meeting at most once in 3 VANI turns. Never ask twice in a row. Exception: the seller has just shown interest or given a time.
     - **R3 no-repeat.** Say each fact once. Repeat a fact only if the seller asks for it again.
     - **R4 straight-answer.** Answer a direct question once, with the true answer from the facts or the seller block (for example, "no name on record, our team handles your account"). Never give the same dodge twice.
     - **R5 close-with-care.** After booking, or before any end, ask "anything else I can help with?". End only after the seller says no or goodbye, or after the nudges get no answer.
2. **The prompt is made from the file.**
   - `render_prompt.py` writes every rule's `say` text into a "Call rules" part of `prompt_phases`. It also removes the ask-pushing lines it has now (Phase 3, the backup line) or makes them follow R1 and R2.
   - SKILL.md tells the agent to read `call_rules.json` and to write a call plan that follows it.
3. **Check before the call: the validator, which is the agent's hook.**
   - It refuses a call plan with a meeting ask in 2 steps in a row (R2).
   - It refuses a plan with the same fact in 2 steps (R3).
   - It refuses a plan with no closing "anything else" step (R5).
   - Each refusal names the rule id, so `finalize` fails until the agent fixes the plan.
4. **The live tool keeps count.**
   - `read_seller_signal` counts VANI's meeting asks and the turns since the last one. It does this through an internal variable that the model sets by a new tool argument, `asked_meeting_last_turn`.
   - When the seller asks a question (question words or a "?"), the directive says: "answer it fully; no meeting ask in this reply" (R1 and R2).
   - The declined and interested directives drop the ask that is built into them now.
5. **Check after the call: `review_call` plus a check script.**
   - A script, `app/loops/rule_checks.py`, scores R2, R3 and R5 on the transcript. It needs no LLM: it counts meeting asks per VANI turn, finds the same fact said twice, and checks whether "anything else" came before the end.
   - The Opus review scores R1 and R4, which need judgement.
   - The results go to `08_review.json → rules{id: pass|fail, turns}`. Loop 2 counts the failures per rule, so we can see which rules break most.
6. **Tests.**
   - A transcript from the 171 s call must fail R2, R3 and R4.
   - A corrected transcript must pass.
   - The validator refuses a call plan with asks in steps 3 and 4, and accepts the plan once it is fixed.

### Not changed
The persona decisions, the hierarchy, the gates, Daytona, the template slots, and the TTS volume (user decision: no change).

### 5f item 7: changes after the enforcement review (Redash dashboard peer, 2026-10-10). These replace items 1-5 where they differ.

1. **The live tool GRANTS the ask; it does not count asks.**
   - `read_seller_signal` keeps an internal variable, `ask_ok_turn`. Each directive ends with either "You may ask for the meeting in this reply." or "Do NOT ask for the meeting in this reply."
   - An ask is allowed only when:
     - (turn − last allowed turn) ≥ 3; or
     - the mode is interested; or
     - `time_mention()` fired.
   - The asks that are built into the directives now are removed (interested, the P1/P4 variants, declined).
   - No argument from the model is used. The SDK tool context has no transcript or last reply (checked 2026-10-10: only variables, language, state, user id, secret). So R2 is enforced by our code, and the post-call R2 check measures how often VANI obeyed.
2. **A "question" mode for R1.**
   - It is found by question words for each language, for example:
     - Hindi: kya, kaun, kab, kitna, kaise, kyun;
     - Marathi: काय, कोण, कधी, किती;
     - Telugu: ఏమి, ఎవరు, ఎప్పుడు, ఎంత;
     - Tamil: என்ன, யார், எப்போது, எவ்வளவு;
     - Kannada, Malayalam, Gujarati, Bengali, Punjabi, English.

     A "?" is not used: STT output often has no punctuation.
   - Its directive is "answer the question fully, from the facts or the seller block; no meeting ask". Its word cap is 30.
3. **R4 is enforced live.**
   - A cue class, `ask_handler`, fires on "who is my executive", "executive kaun", "naam batao", "कौन आएगा" and the same in other languages.
   - Its directive carries the handler sentence word for word, from a new per-call variable `handler_line`.
   - `compile_vars` sets `handler_line` from `state.handler`: the person's name, or "our IndiaMART team handles your account; the executive's name comes with the meeting confirmation".
   - The Opus review still scores R4.
4. **The checks before the call are structural.**
   - Each call-plan step gets `kind: info|question|ask|close` and `fact_ids[]`.
   - **R2:** no two steps of kind `ask` in a row.
   - **R3:** no fact id in two steps.
   - **Cross-check:** a step of kind `info` that holds meeting or time words (`time_mention()` or meeting/मीटिंग/executive) is refused as labelled wrongly.
   - R5 is the same for every seller. It moves into the fixed phases in `render_prompt` (a closing step), and there is no validator rule for it.
5. **The exceptions to R5 are written in `call_rules.json` and in the check.** These ends never ask "anything else?":
   - opt-out, DND or remove-my-number (`set_end_conversation` + `OPT_OUT_LINE`);
   - a hostile seller, or a legal threat;
   - the seller's explicit end request;
   - the end of the nudges.
6. **The checks after the call write `pass|fail|unknown` and the language.**
   - **R5 by events:** after `book_meeting` there must be at least one more VANI turn AND at least one seller turn before the end, unless it was an opt-out. This works in every language.
   - **R3 by verified fact:** the same number in 2 or more VANI turns. Number words are matched with a table for hi, mr, te, ta, gu. For other languages the result is "unknown", never "pass".
   - **R2 by words:** meeting|मीटिंग|executive plus `time_mention()`. The result is "unknown" for a language the lexicon does not cover.
   - Before Loop 2 counts any of it, it is calibrated on today's 3 calls and on the role-play transcripts.
7. **Tests in both directions, in Hindi AND in Telugu or Tamil.** Each check must fire on a bad transcript and stay silent on a good one.
8. **`call_rules.json` keeps:** `id`, `say`, `pre_check`, `post_check`, `exceptions`, `evidence`, `added`. `layers` is dropped: `render_prompt` and the tool read the same `say`.
