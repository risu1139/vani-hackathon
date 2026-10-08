---
name: design-architecture
description: Design or revise the VANI hackathon system architecture top-down, block by block, answering why / how / what (input, output) for each block. Use when designing, reviewing or changing any block (persona generation, data refinement, compiler, switching, learning loop), or when the user asks "how should we build X" or "what goes in and out of X".
---

# Designing the architecture, top-down

The team lead's method for VANI. Follow `AGENTS.md` constraints; requirements live in `wiki/projects/vani-hackathon/persona-requirements.md`. Read `wiki/index.md` first.

## Steps

1. **Top level first.** Draw the whole system as a chain of high-level blocks, from seller data through the live Sarvam call and back. One fixed role per block. Don't design any block's internals yet.
2. **For each block, answer three questions:**
   - **Why:** which PS04 deliverable or scoring criterion it serves. If none, say so and flag it as out of scope (devil's advocate).
   - **How:** the implementation, decided one layer beneath. Compare script vs single LLM call vs agent (and named methods such as RAG), with evidence. Pick one and say why.
   - **What:** its exact input and output, preferably as a JSON shape, and which named block consumes the output.
3. **Let inputs create blocks.** If a block's input needs preparing (e.g. refining one seller's data, or learning from other sellers), that preparation becomes its own block. Apply step 2 to it: which proven method, what kind of data, how it is fetched, what it outputs.
4. **Let downstream shape upstream.** Check what the next block, ultimately Sarvam, accepts before fixing a block's output. Example: Sarvam's call inputs (`initial_bot_message`, `agent_variables`, `text_to_speech_config`, per-turn tool response) decide whether persona and plan are produced together and how they are delivered.
5. **Close every loop.** Every output feeds a named next block. The between-run learning loop feeds back into the earliest block it improves. No model training; only our rules, libraries, memory and switch logic change.
6. **Tag and challenge.** Mark every choice PROVEN (our spike or data), DOCUMENTED (source) or ASSUMED. Play devil's advocate against PS04, the 2-day build rule, the pre-built rule and data-on-premises. List what to test next. If something proposed is ASSUMED and cheap to test, test it.

## Output format

- One end-to-end diagram.
- One table: block | why | how (choice + rejected options) | input | output | feeds | status.
- Per block, a short section going one layer beneath.
- A devil's-advocate section and the open questions.

## Filing

Write designs to `outputs/` or `wiki/projects/vani-hackathon/` (via the `wiki-file` skill). Current design: [[system-design]].
