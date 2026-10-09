# Team decisions: VANI persona agent (2026-10-09)

Source: the team lead (Rishav Kumar) in the Claude Code planning session on 2026-10-09. Verbatim quotes are kept where they define the decision.

1. **"Persona" means VANI's persona.** Seller data (traits and states) is the input. Seller types (e.g. "Rusher") are input and explanation only. "Rusher" is a state that can change from call to call.
2. **No rule table in the plan.** "use rule table for just inference it should be based on data rule we can start with but it should never be in our plan or something we will build on or present in presentation".
3. **The agent decides and composes.** "we give seller traits and state and possible mapping vani persona and let it decide with tools to refine the vani persona". The agent must not only select from a list. Library personas are starting points. The agent composes each seller's VANI persona (it can mix or create new combinations). Code checks only the guardrails (facts, prices, compliance, DNC, cited evidence) and what the platform can play.
4. **The agent suggests new personas; a human adds them.** "why can't be let agent create persona but not add it but suggest that the library needs different persona". Suggestions are aggregated weekly, then a human approves.
5. **The decider runs on a frontier model.** "i will use advanced frontier models agent built on daytona sandbox". Sarvam is required only for the voice agent.
6. **Voice per call.** "we will take code tool option or will create different agents based on recommendation for demo later anyway we will get it". Use Sarvam Code Tools when they are enabled (requested by email on 2026-10-09). Until then, create Sarvam agent versions that match the agent's recommended personas for the demo.
7. **Voice gender is chosen from data.** If a voice gender works better, use it more. There are no quotas or skew alarms. The seller's gender and age are never inferred.
