# Team decision: self-improvement happens between runs (2026-10-08)

Source: team lead (lakshay.neem) in the Claude Code planning session, 2026-10-08. This corrects how [[2026-10-08-deep-research-self-improving-persona-switch-loops]] framed the loops.

## Verbatim

> Do we need to build a fixed library of personas? Answer: No. The persona is generated for each seller from their data. You may group sellers into types to explain your logic, but the output is a persona per seller. this is important think so keep this in consideration i told u different. so better would be how do we make the persona generation loop better after creating some base persona.

> u are confusing i am not saying any self improvement for the same run but after that run so that it does not do the same mistake llm willl not be used for deciding switches. do we not have call data already. i am saying our model will improve at switching and also creating personal persona based on runs

## Decisions

1. Personas are generated per seller from that seller's data (PS04 FAQ Q1). Types are only for explaining the logic.
2. Nothing learns during a call. During a call, only our switcher (lexicon + Jev, frozen) decides switches.
3. An LLM never decides a switch live. It is used only after a run, to review the finished call and label mistakes.
4. After each run, those corrections improve both the switcher and the persona generator, so the next run doesn't repeat the mistake.
5. Existing PS07 call data counts as past runs and bootstraps both loops.
