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
  - Address the seller by name only: no honorific (ji, garu, avare, saheb, sir).
- Data is pseudonymised (`{SELLER_NAME}`, `{COMPANY}`). Keep the tokens. No other data, no internet.
- Always absolute paths: `"$VANI_PY" "$VANI_SKILL/scripts/persona_tool.py" ...`, files under `$VANI_RUN/`.
