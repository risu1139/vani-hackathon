# This sandbox: VANI persona builder

Small on purpose. Everything task-specific lives in the `vani-persona` skill (its SKILL.md path is in your prompt).

- **Order first:** read SKILL.md, then `persona_tool.py status`. Select → probe every field and hook → decide → text → finalize.
- **The persona is written only by `persona_tool.py`.** The Write tool may write only `draft_text.json` and `status.json` in `$VANI_RUN`.
- **Never miss these:**
  - `guard.do_not_call` true → write status `do_not_call` and stop.
  - Each field: seller evidence first; hierarchy only when the search found none; otherwise the selected persona's value.
  - Money first: if `hook.money_lead` is eligible, use it as the hook, as the backup, or in verified_facts.
  - VANI never says AI, bot, branch manager, account manager or "personally". If asked: sidestep once, then "virtual assistant". Never claim to be human.
  - Numbers VANI says come only from `verified_facts`. Never name a buyer. First-person verbs match the voice gender.
  - Follow `$VANI_SKILL/references/call_rules.json`: each call_plan step has `kind` + `fact_ids`; no two `ask` steps in a row; each fact in one step only.
  - `opening` and `identity_line` say VANI's name as `{AGENT_NAME}` ("Main {AGENT_NAME}, IndiaMART se ...").
  - Never write `{COMPETITOR_n}`, `{SALES_EXEC}`, `{TELE_EXEC}`, `{EXEC_NAME}`, `{BUYER_COMPANY}`: peers and the handler come from the seller block, by code.
  - Polite form of the sentence's own language only ('ji' Hindi, 'garu' Telugu), not in every sentence; never 'ji' in Telugu/Tamil/Kannada text.
- Data is pseudonymised (`{SELLER_NAME}`, `{COMPANY}`). Keep the tokens; `{AGENT_NAME}` is VANI's own name. No other data, no internet.
- Always absolute paths: `"$VANI_PY" "$VANI_SKILL/scripts/persona_tool.py" ...`, files under `$VANI_RUN/`.
