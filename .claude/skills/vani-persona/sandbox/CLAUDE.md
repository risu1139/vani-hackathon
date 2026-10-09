# This sandbox: VANI persona builder

Small on purpose. This file is always in context; everything task-specific lives in the `vani-persona` skill.

- **Persona work has a skill: `vani-persona`.** Use it for every request to build a VANI persona, a seller persona spec or Sarvam call variables. Follow its numbered steps exactly.
- **Never miss these:**
  - `guard.do_not_call` true → write status `do_not_call` and stop.
  - Every eligible hook gets a decision after its probe files are read.
  - Money first: if `hook.money_lead` is eligible, use it as the hook, as the backup, or in verified_facts.
  - VANI never says AI, bot, branch manager, account manager or "personally". If asked: sidestep once, then "virtual assistant". Never claim to be human.
  - Numbers VANI says come only from `verified_facts`. Never name a buyer.
  - First-person verbs match the voice gender.
- Data in the seller folder is pseudonymised (`{SELLER_NAME}`, `{COMPANY}`). Keep the tokens. Use no other data, and no internet.
- `python3`, never `python`. Absolute paths. Run scripts synchronously.
- Whatever happens, `status.json` is written in the run directory. It is the only thing read back.
- Model: Opus 5.5 (`claude-opus-5-5`), pinned by the run script.
