# Industry practice: how per-customer personas and call plans are built before an AI voice or sales call (as of 2026-10-08)

Tags: **DOCUMENTED** = vendor docs or an engineering write-up describe the mechanism. **VENDOR CLAIM** = marketing or self-reported numbers, not verified. **ASSUMED** = my inference, or from memory without a fetched source this session.

Builds on `raw/research/2026-10-08-last30days-per-customer-persona-call-plan-generation.md` (Bolna, Synthflow/Smallest, Octave, MarketBetter/Relevance summary lines 1072–1075). The rest of that scan was mostly off-topic noise.

## Q1. Voice platforms: how is the per-customer persona or plan produced?

### Takeaway
Every voice platform checked does per-customer personalisation the same way. Code fetches CRM or CSV fields before the dial and puts them into `{{variables}}` in a fixed, human-written prompt. Some platforms also let you override the whole prompt, first message or voice for each call. None of them has a built-in LLM step that writes a persona for each customer. If generation happens at all, the customer's own backend does it and pushes the result in through the override or variable API.

### Cited Findings
- **Bolna — rules plus template (DOCUMENTED).** In the "pre-call journey", data from a CRM, CSV, Google Sheet or internal API is loaded into variables before the call connects. The script uses placeholders such as `{name}`, `{plan}` and `{due_amount}`. Values go in through `user_data` on the API or as CSV rows for batch calls. If a value is missing, Bolna "naturally rephrases or removes that part". The mechanism behind that is not documented. — [Bolna blog](https://www.bolna.ai/blog/setting-up-pre-call-journey); [Bolna docs: using context](https://www.bolna.ai/docs/using-context)
- **Retell — template plus variables, with layered precedence (DOCUMENTED).** `{{var}}` works in prompts, the opening message, tool parameters, flow conditions and transfers. Values are passed as `retell_llm_dynamic_variables` (strings only) on the create-call request, or as CSV columns for batch calls. Precedence, lowest to highest: agent defaults < environment < contact fields < request values < values collected during the call. Variables can be overridden mid-call with Update Live Call. A variable with no value stays as raw `{{x}}`, so defaults are required. — [Retell docs](https://docs.retellai.com/build/dynamic-variables)
- **Vapi — variables plus a full per-call "transient assistant" (DOCUMENTED).** `assistantOverrides.variableValues` fills `{{var}}`. For inbound calls, an `assistant-request` webhook lets your server return a complete transient assistant per call (firstMessage, model, system prompt). It must answer within **7.5 s**, a fixed limit. Vapi's advice is to return a minimal assistant fast and "enrich context asynchronously after the call starts". — [Vapi dynamic variables](https://docs.vapi.ai/assistants/dynamic-variables); [Vapi server events](https://docs.vapi.ai/server-url/events); [Transient vs permanent](https://docs.vapi.ai/assistants/concepts/transient-vs-permanent-configurations)
- **ElevenLabs Agents — variables plus whitelisted overrides (DOCUMENTED).** `conversation_initiation_client_data` carries `dynamic_variables` and a `conversation_config_override`. These can override the system prompt, first message, language, voice ID, LLM, stability, speed and similarity, but only fields enabled in the agent's security settings. ElevenLabs recommends dynamic variables over full overrides "for better maintainability". — [ElevenLabs overrides](https://elevenlabs.io/docs/eleven-agents/customization/personalization/overrides); [ElevenLabs personalization](https://elevenlabs.io/docs/eleven-agents/customization/personalization)
- **Synthflow — variables plus "dynamic prompt injection" (DOCUMENTED).** Values in `custom_variables` can be used in prompts, actions, transfers, SIP headers and webhooks. A separate feature accepts a custom prompt in each API request, to change the "approach or tone" for that conversation. — [Synthflow dynamic prompt injection](https://docs.synthflow.ai/dynamic-prompt-injection); [Synthflow custom variables](https://docs.synthflow.ai/custom-variables)
- **Smallest.ai — similar dynamic prompt injection (DOCUMENTED in the prior scan only).** — raw scan line 1073 (docs.smallest.ai; not re-fetched this session)
- **Sarvam Conversations / Samvaad, our core agent — template plus variables plus an on-start hook (DOCUMENTED).**
  - Variables are inserted with `@` into greetings, instructions and tool prompts.
  - Input variables come from three sources: telephony metadata; an **on-start hook**, "an API call fired at call start that returns CRM profiles, account details, or eligibility flags… mapped into agent variables before the agent speaks"; or campaign CSV columns.
  - Each variable has a toggle that controls whether the LLM sees it, which saves context tokens.
  - Output variables are extracted after the call with natural-language prompts (String or Enum), plus a "Successful when" rule.
  - This section of the docs does not mention per-call overrides of prompt, voice or language.
  - — [Sarvam docs: variables & personalization](https://docs.sarvam.ai/conversations/build/variables-personalization); [MoEngage x Sarvam Conversations](https://moengage.com/docs/partner-guide/messaging-channels/voice/sarvam-conversations)
- **Bland (ASSUMED, not fetched).** "Pathways" are node-based conversation graphs with `request_data` variables for each call. Same pattern.
- **SquadStack, Gnani, Haptik (GAP).** No public documentation of the generation mechanism was found this session.

### Inferences
- **ASSUMED:** The industry splits the work in two. The platform provides a fixed, reviewed agent (prompt, flow, guardrails). Per-customer variation is small structured data: variables, and sometimes a voice or language switch. That keeps behaviour testable, because the prompt surface stays fixed. For any LLM-written per-customer text, the platform hands responsibility to your backend.
- **ASSUMED:** Vapi's 7.5 s limit and its "enrich asynchronously" advice imply that any heavy generation should run *before* the dial (batch), not inside the call-setup webhook.
- **ASSUMED, relevant to us:** Sarvam's on-start hook plus input variables is exactly where our generator's output should go. Our generator becomes the backend that fills those variables. A per-call voice or speed override on Sarvam is unconfirmed and needs checking.

### Gaps
- Whether Sarvam allows a full per-call prompt or voice override (only variables were confirmed).
- SquadStack, Gnani and Haptik internals are not public.
- No voice vendor published evidence that per-customer *generated* scripts beat templates with variables.

## Q2. Sales AI: how are per-account call plans and briefs generated?

### Takeaway
On the sales side, LLMs do the generation. Every serious product grounds that generation in a curated library: approved messaging, personas, playbooks and proof points. The range runs from one LLM call that summarises CRM history (Gong) to a library-grounded agent (Octave) to a hierarchical multi-agent system (11x). Their output is a brief for a human, or text, not a live voice agent's behaviour.

### Cited Findings
- **Octave — Call Prep Agent: retrieval-grounded LLM agent (DOCUMENTED).**
  - It produces "call-prep notes with talking points and objection handling", discovery questions and a call script.
  - "Every agent run pulls context from your Library at execution time".
  - It auto-selects a **Motion** (playbook) by matching the offering and the prospect's persona or segment against Motion ICPs. The Motion supplies the "narrative, learnings, and recommended evidence (proof points, references, objections, alternatives)".
  - `customContext` can pin a playbook or persona "for deterministic results".
  - It runs synchronously, or asynchronously for batches. Saved agents are versioned. No built-in approval step is documented.
  - — [Octave docs: agents](https://docs.octavehq.com/concepts/agents)
- **Gong — AI meeting prep: one summarisation step over CRM and activity history (DOCUMENTED).** It outputs meeting objectives, key topics, highlights of prior discussions, action items, suggested questions and reminders. It becomes available **15 min before** the meeting, and the summary is generated only when the account has prior tracked activity (calls or emails). — [Gong help](https://help.gong.io/docs/get-ready-for-meetings-with-ai-powered-meeting-prep)
- **11x Alice 2.0 — hierarchical multi-agent system on LangGraph (DOCUMENTED engineering write-up).**
  - **ReAct with 10–20 tools was dropped:** it picked the wrong tools, got stuck in "infinite loops", and "a single agent with one set of prompts couldn't excel at any particular aspect".
  - **A 15-node workflow was dropped:** quality was better, but it was rigid and users could not move between steps.
  - **Final design:** a supervisor with sub-agents for research, a positioning report, a LinkedIn writer and an email writer. The design rule was "tools over skills".
  - **VENDOR CLAIM:** about 2M leads, about 3M messages, about 21k replies, and a reply rate of about 2% "matching human SDRs".
  - — [ZenML LLMOps DB summary of 11x talk](https://zenml.io/llmops-database/rebuilding-an-ai-sdr-agent-with-multi-agent-architecture-for-enterprise-sales-automation)
- **Salesforce Agentforce SDR — grounding in CRM and Data Cloud plus a governance layer (secondary sources, partly VENDOR CLAIM).** It personalises from fields on the Salesforce record (merge fields such as industry and product interest), grounded in Data Cloud. The Einstein Trust Layer enforces the same permissions and sharing model. These are partner blogs, not Salesforce docs. — [eesel.ai guide](https://www.eesel.ai/blog/agentforce-sales-development); [SalesforceBen](https://www.salesforceben.com/nurture-leads-24-7-with-agentforce-for-sales/)
- **Relevance AI and MarketBetter script generators — single LLM call per account (VENDOR CLAIM).** The input is minimal (company, URL, role, offering), plus signals such as competitor evaluation, hiring, stalled deals and pricing-page visits. They output "a complete personalized script in under 60 seconds". MarketBetter claims 36% higher meeting conversion and pre-generation overnight; both are unverified. — [Relevance AI cold-call script](https://relevanceai.com/tools/cold-call-script); [MarketBetter blog](https://marketbetter.ai/blog/tags/personalization/); raw scan line 1075
- **Artisan, Regie, Clay, Outreach, Salesloft, HubSpot Breeze (GAP).** No mechanism-level documentation was fetched this session. ASSUMED: Clay is a spreadsheet of enrichment columns, each an LLM or API call, which is a step-by-step research-then-write pipeline.

### Inferences
- **ASSUMED:** Even the most agentic system (11x) went back to *structure*: fixed specialist roles and tools, not a free agent. Octave makes the library the source of truth and lets you pin playbooks for determinism. The lesson is that "LLM plus curated library plus a constrained structure" beats both "pure code" and "free agent".
- **ASSUMED:** None of these show a separate "critique" agent in public. Quality control comes from the grounding library, human review (the rep reads the brief), and versioning.

### Gaps
- No public A/B evidence comparing a single LLM call with a multi-step agent for call-plan quality.
- No independent verification of 11x, MarketBetter or Relevance results.

## Q3. Contact centre: how are behaviour, guardrails and per-customer adaptation controlled?

### Takeaway
Enterprise customer-experience platforms (Sierra, Decagon, Cresta) put control in **declarative procedures and supervisors**, not in a generated persona. Natural-language SOPs are compiled into structured logic, hard guardrails are written as rules, and a supervisor model checks every response. Per-customer adaptation happens inside those rails.

### Cited Findings
- **Sierra (DOCUMENTED, product pages).**
  - The Agent SDK declares goals and guardrails, for example "orders can only be returned within 30 days".
  - It sets "the degree of flexibility… for each workflow, allowing for varying levels of creativity and determinism".
  - Supervisor agents audit "every action and response". For high-risk topics they "switch from observe to intercept".
  - — [Sierra Agent SDK](https://sierra.ai/product/agent-sdk); [Sierra: enterprise-grade agents](https://sierra.ai/uk/blog/enterprise-grade-agents)
- **Decagon Agent Operating Procedures (AOPs) (DOCUMENTED, vendor blog).**
  - Natural-language instructions are "compiled into structured logic". One artifact bundles prompts, logic, actions and rules.
  - AOP Copilot (Sep 2025) turns rough SOPs into AOPs.
  - **VENDOR CLAIM:** 3–6 weeks from kickoff to production.
  - — [Decagon: AOPs](https://decagon.ai/blog/aop-the-future-of-cx); [Decagon: from SOPs to AOPs](https://decagon.ai/blog/from-sops-to-agent-operating-procedures); [Fin comparison](https://fin.ai/learn/ai-agent-procedures-aops-journeys)
- **Cresta (VENDOR CLAIM, product page).** Live hints, checklists and workflows for human agents. It "automatically identifies the right procedure" and nudges objection responses so agents "stick to approved playbooks". Live Assist escalates to a supervisor. — [Cresta Behavioral Guidance](https://cresta.com/cresta-behavioral-guidance)
- **Observe.AI (GAP).** Not fetched.
- **Adapting voice or tone per customer (DOCUMENTED, mechanism only).**
  - ElevenLabs exposes per-conversation voice ID, speed, stability and language overrides.
  - Synthflow's per-call prompt injection is pitched for changing "approach or tone".
  - No vendor publishes a *policy* for choosing voice or tone per customer; it is left to the integrator.
  - — sources above

### Inferences
- **ASSUMED:** For "safe and grounded", industry pattern is (1) deterministic hard rules outside the LLM, (2) an approved content library the LLM may only choose from or paraphrase, and (3) a checker or supervisor pass. Pre-call, that means validating generated plans against a schema and the playbook before they reach the dialler.

### Gaps
- No public detail on how Sierra or Decagon personalise each customer beyond tools and CRM lookups.

## Q4. Synthesis: dominant patterns, when each is used, and what a hackathon team should copy

### Takeaway
There are four patterns, and they stack rather than compete:

| # | Pattern | Used by | Typical use | Timing |
|---|---|---|---|---|
| P1 | Rules plus template variables | Every voice platform | Production calls at volume | At dial, milliseconds |
| P2 | One LLM call that writes a brief or script from CRM data | Gong, Relevance, MarketBetter | Human-read briefs | Pre-generated or about 60 s |
| P3 | Retrieval-grounded LLM agent over an approved library, with a pinnable playbook | Octave | Grounded generation | Sync or batch |
| P4 | Hierarchical multi-agent system (research → positioning → writer) | 11x | Research-heavy outbound | Batch |

Contact-centre platforms add P5: declarative procedures plus a supervisor or checker (Sierra, Decagon). The team lead is right that pure code (P1) is not what generation leaders use. But leaders also do not use a free agent: they settled on **code for structure and safety, an LLM grounded in a library for wording, and a check before use**. Our draft is roughly P1 plus P2. The cheap, credible upgrade is P1 plus P3 plus a light P5 checker.

### Cited Findings
- P1 evidence: Bolna, Retell, Vapi, ElevenLabs, Synthflow, Sarvam (Q1 citations).
- P2 evidence: Gong, Relevance (Q2).
- P3 evidence: Octave Motions and the pinnable `customContext` (Q2).
- P4 evidence: 11x, including the failures of free ReAct and rigid workflows (Q2).
- P5 evidence: Sierra supervisors, Decagon AOPs (Q3).
- Latency evidence: Vapi's 7.5 s call-setup limit (Q1); Gong generates up to 15 min before (Q2); MarketBetter generates overnight (VENDOR CLAIM).

### Inferences: what to copy (all ASSUMED)
1. **Keep code for the delivery settings and hard rules.** Language, speed, formality, consent and "never promise X" stay deterministic, as Sierra guardrails do. This is what platforms trust, and judges can audit it.
2. **Replace "one free LLM call" with a library-grounded call (the Octave pattern).**
   - Build a small approved library from aggregates in `data/`: opening lines, value points per seller segment, objection → response pairs, escalation triggers.
   - Rules pick the segment or "motion". The Sarvam LLM *selects and adapts* entries and must cite their IDs.
   - Pin by rule for determinism.
3. **Return structured output.** Use a JSON schema: `opening`, `personalisation_hooks[]` (each tied to a data field), `talking_points[]` (each with a library ID), `objections[]` with responses, `escalation_triggers[]`, `do_not_say[]`. Validate the output in code.
4. **Add one critique or check pass (light P5), not a multi-agent system.**
   - Use code checks: every hook maps to a real field, every claim maps to a library ID, plus banned phrases and length or language limits.
   - Optionally a second Sarvam call as judge.
   - On failure, regenerate once, then fall back to the P1 template. The fallback means the demo never breaks.
5. **Pre-generate in batch before the campaign; never generate at dial time.** Write the plan into Sarvam input variables via campaign CSV columns or the on-start hook response. Vapi's 7.5 s limit shows why.
6. **Skip P4 (multi-agent research).** 11x needed months, and their research step was web-scraping, which we don't need because IndiaMART data is already structured. ReAct-style loops are the documented failure mode. Mention P4 only as future work.
7. **Tie the learning loop to the library, not the prompt.** Post-call output variables (Sarvam's extraction plus the "Successful when" rule) update which library entries or motions win. This mirrors Octave "learnings" and is what makes "code + LLM" more than a script.
8. **Pitch line:** "Same architecture as the industry: deterministic rails (Retell, Sierra), a library-grounded generator (Octave), a checker (Sierra supervisor), pre-computed and injected as Sarvam variables."

### Gaps
- No public head-to-head evidence that P3 or P4 beats P2 on conversion. Every result number found is a VENDOR CLAIM.
- Per-call voice or speed override on Sarvam is unconfirmed; check the Sarvam docs or ask Sarvam at the event.
- Not covered this session: SquadStack, Gnani, Haptik, Observe.AI, Outreach, Salesloft, HubSpot Breeze, Regie, Artisan, Clay.
