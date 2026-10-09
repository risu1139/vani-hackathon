# Team decision: one skill runs the whole flow (2026-10-09)

Source: the team lead (Rishav Kumar) in the Claude Code planning session on 2026-10-09.

## Verbatim

> there will be one skill that will do everything getting and create the vani persona and then can do a call as well ... idea was with one trigger it does everything and calll the customer. the idea of nightly cook is for production later when we will do it at scale.

> so we willl just use the data that agent gives and based on that we will create the state and one more other [traits]

> should we also have library of traits and states and give it as starting point

## Decisions

1. **One skill, one trigger, end to end.** A single Claude Code skill does the whole flow:
   1. Get the seller data from the data agent.
   2. Build the seller's traits and states.
   3. Compose the VANI persona and call plan.
   4. Fill the Sarvam variables (`persona_voice_id`, `persona_pace`, `persona_pitch`, `persona_opening`, plan).
   5. Place the call.
2. **Nightly batch cooking is for production at scale later**, not for the hackathon flow.
3. **Seller input is the data agent's per-seller context JSON.** Traits and states are derived from it.
4. **Proposed:** a library of traits and states as a starting point for the agent (alongside the VANI persona library). Open; see the plan.
5. **Constraint (team lead):** OpenRouter is not available from the Daytona sandbox, so the skill's model access there is set up by the team lead.
