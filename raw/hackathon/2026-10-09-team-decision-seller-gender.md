# Team decision: seller gender may be used to choose VANI's voice gender (2026-10-09)

Source: the user, in the Claude Code planning session on 2026-10-09 (late evening). It updates item 7 of `2026-10-09-team-decisions-persona-agent.md`, which said "the seller's gender and age are never inferred".

## What was said (paraphrase of the user's words)
- Seller gender matters because many women sellers are wary of calls from men ("how did they get my number?"). A call from a female voice is the better case for them.
- Gender only picks **VANI's own voice** (male or female). The seller is not treated differently in any other way. "Most of the sales callees is a girl, so we are not doing anything wrong."
- Asked whether to keep "never infer", the user chose to change the rule: the agent may use a **name- or voice-based guess** of the seller's gender.

## Rule now
1. The recorded account gender/salutation (`glusr_usr_gender`, `glusr_usr_salute`) is used first when present. It was filled for 1 of 10 demo sellers.
2. Otherwise a guess from the first name, or from the voice in a past call recording, is allowed. It is stored with its source and a confidence.
3. It is used **only** to choose VANI's voice gender. It never changes content, offers, price talk or tone toward the seller, and it is never said aloud.
4. Age is still not inferred (not discussed).
