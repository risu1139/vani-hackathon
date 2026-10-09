# Per-seller context file layout for the decider agent: one big markdown or many files? (2026-10-10)

**Question.** The persona-decider (a Claude Code agent running our skill in an offline sandbox) reads a per-seller context before it decides. The context holds profile, catalogue, buy leads, enquiries, account, full past-call history with transcripts, peer stats and candidate leads, 30–100 KB per seller. We want all of it available, a short summary first, and deeper probing on demand. Should it be one markdown file (stable headings plus an index at the top) or several files (index plus one file per section or per call), plus JSON?

**Method.** Desk research, 2025–2026 sources, WebSearch and WebFetch. Official Anthropic and Claude Code docs were fetched directly and quoted. We also measured our own current builder output (`data/contexts/<glid>.md` from `app/persona/seller_context_builder.py`), aggregates only: sizes, line counts and bytes per section. No seller content is recorded here.

Tags: **DOCUMENTED** = official vendor docs or vendor engineering posts · **RESEARCH** = papers or benchmark reports · **PRACTITIONER** = blogs, community posts, third-party write-ups · **MEASURED** = our own numbers.

## Bottom line

- **Use several files in one folder per seller, with a mandatory `INDEX.md` the agent reads first.** Do not use one big file. The deciding facts:
  1. Claude Code's Read tool returns only a first page with a `PARTIAL view` notice once a whole-file read passes its token limit (25,000 tokens by default). Our biggest current file is already 86.8 KB, about 22k tokens, *before* full call transcripts are added. At 100 KB a single file will be cut off.
  2. Anthropic's skill guidance says to split content by domain, keep references one level deep, name files descriptively, and add a table of contents to any file over 100 lines, because Claude previews files with `head -100`-style partial reads.
  3. Recall falls as context grows and when the fact sits in the middle (context rot, lost in the middle, NoLiMa). The cure is to load less, not to load one long file more carefully.
- **Keep `context.json` beside the markdown as the machine copy.** Scripts (validator, citation checker, aggregations) use it. The agent reads the markdown and uses `jq` only for a targeted lookup.
- **Put the essentials in the index itself.** This is passive context: identity, the K block (this call), the key numbers, the call table and a file map with sizes. Vercel's evals show that context the agent must choose to open is often never opened, while an index that is always present wins.
- **Cite by stable record ID, not by line number.** Every record and transcript turn gets an ID (`L-…`, `ENQ-…`, `C03.T12`). Evidence rows cite `file#ID`, and a script greps for the ID to check that it exists.

## 1. Findings

### 1.1 Anthropic: Agent Skills docs and best practices (DOCUMENTED)

- **Three loading levels.** Metadata (~100 tokens) is always loaded. The SKILL.md body is loaded on trigger, "Under 5k tokens". Resources cost "None until accessed. … Reference files load into context when read." "There's no context penalty for bundled content that isn't used." <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>
- **Size.** "Keep SKILL.md body under 500 lines for optimal performance. Split content into separate files when approaching this limit." <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- **One level deep.** "Claude may partially read files when they're referenced from other referenced files. When encountering nested references, Claude might use commands like `head -100` to preview content rather than reading entire files, resulting in incomplete information. **Keep references one level deep from SKILL.md**." (same page)
- **TOC for long files.** "For reference files longer than 100 lines, include a table of contents at the top. This ensures Claude can see the full scope of available information even when previewing with partial reads." (same page)
- **Domain split.** "For Skills with multiple domains, organize content by domain to avoid loading irrelevant context. … Claude only needs to read sales-related schemas." The example index lists each file with a one-line description and gives grep commands (`grep -i "revenue" reference/finance.md`). (same page)
- **Naming and discovery.** "Name files descriptively: … `form_validation_rules.md`, not `doc2.md`". "Organize for discovery: Structure directories by domain or feature". "Bundle comprehensive resources: Include complete API docs, extensive examples, large datasets; no context penalty until accessed". "Prefer scripts for deterministic operations". "Test file access patterns". (same page)
- **Observe navigation.** Watch for "Ignored content: If Claude never accesses a bundled file, it might be unnecessary or poorly signaled" and "Overreliance on certain sections: … consider whether that content should be in the main SKILL.md". (same page)

### 1.2 Anthropic: context engineering and tools (DOCUMENTED)

- **Just in time.** "agents built with the 'just in time' approach maintain lightweight identifiers (file paths, stored queries, web links, etc.) and use these references to dynamically load data into context at runtime using tools." <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- **Hybrid.** "the most effective agents might employ a hybrid strategy, retrieving some data up front for speed, and pursuing further autonomous exploration at its discretion." Claude Code: "CLAUDE.md files are naively dropped into context up front, while primitives like glob and grep allow it to navigate its environment and retrieve files just-in-time." (same post)
- **Metadata as signal.** "Folder hierarchies, naming conventions, and timestamps all provide important signals that help both humans and agents understand how and when to utilize information." (same post)
- **Context rot.** "as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases." (same post)
- **Large data.** Claude Code can "leverage Bash commands like head and tail to analyze large volumes of data without ever loading the full data objects into context." (same post)
- **Tool output cap.** "For Claude Code, we restrict tool responses to 25,000 tokens by default." Natural-language identifiers work better than cryptic ones. "Even your tool response structure—for example XML, JSON, or Markdown—can have an impact on evaluation performance", so choose by eval. <https://www.anthropic.com/engineering/writing-tools-for-agents>
- **Long documents in a prompt.** For 20k+ token inputs: put long data at the top and the query at the end ("up to 30 percent" better). Wrap each document with `<source>` metadata. "Ground responses in quotes". <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> (long-context section)

### 1.3 Claude Code file reading and memory (DOCUMENTED)

- **Read tool.** "When a whole-file read exceeds the token limit, Read returns the first page with a `PARTIAL view` notice that tells Claude how much of the file it received and how to read more with `offset` and `limit`. A read that passes an explicit `offset` or `limit` and still exceeds the token limit returns an error." <https://code.claude.com/docs/en/tools-reference> (Read tool behavior)
- **Override.** The limit can be raised with `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` ("Override the default token limit for file reads"). The docs page gives no default. <https://code.claude.com/docs/en/env-vars>. PRACTITIONER reports and GitHub issues put the default at 25,000 tokens (about 256 KB on the byte side). <https://github.com/anthropics/claude-code/issues/22506>, <https://www.morphllm.com/claude-code-token-limit>
- **Bash output.** Inline up to about 30,000 characters. Past that, it is saved to a file with a 2,000-character preview. So `cat` of a big file does not get around the limit either. (tools-reference)
- **Grep.** Grep gives `file:line` hits, has `content` / `count` / `files_with_matches` modes, and supports `head_limit` / `offset` paging. (tools-reference)
- **Memory pattern.** Auto memory is a `MEMORY.md` *index* ("one line per memory, loaded into every session") plus topic files that are not loaded at startup: "Claude reads them on demand using its standard file tools". Only "The first 200 lines of `MEMORY.md`, or the first 25KB" load. CLAUDE.md should target "under 200 lines … Longer files consume more context and reduce adherence". "Imports … don't reduce its context cost". <https://code.claude.com/docs/en/memory>

### 1.4 Index-file conventions (DOCUMENTED / PRACTITIONER)

- **llms.txt** (Jeremy Howard, 2024; v2 2026). An H1 (required), a blockquote summary, then H2 sections of `[name](url): notes` file lists. An `## Optional` section marks "links an agent can skip when a shorter context is needed". A `llms-full.txt` holds the concatenated corpus: "llms.txt is the index. llms-full.txt is the corpus." <https://llmstxt.org/> (DOCUMENTED, spec), <https://www.agentpatterns.ai/geo/llms-txt/> (PRACTITIONER)
- **Vercel, AGENTS.md vs skills evals (Jan 2026).** Baseline 53%. Skill left to the agent 53% (the skill was never invoked in 56% of cases). Skill with explicit instructions 79%. A compressed 8 KB docs **index** placed in AGENTS.md that points to files in `.next-docs/` scored 100%. The index format is pipe-delimited paths. It was cut from 40 KB to 8 KB. Its instruction: "Prefer retrieval-led reasoning over pre-training-led reasoning". <https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals> (PRACTITIONER, vendor eval)
- **Karpathy LLM-wiki pattern.** `raw/` → `wiki/`, with `index.md` (a catalogue with one-line summaries) and `log.md`, and the agent navigates from the index. Our own repo uses this pattern. <https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide> (PRACTITIONER)
- **Manus.** "File system as the ultimate context". Compression must be *restorable*: drop content but keep its path or URL so it can be re-read. Retrieval is done with glob, grep and cat, without vectors. <https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus> (PRACTITIONER, vendor)
- **ETH Zurich, "Evaluating AGENTS.md" (arXiv 2602.11988, Feb 2026).** LLM-generated context files *lowered* success and raised cost by over 20%. Human-written ones gave about +4% at up to +19% cost. Lesson for us: the index should hold facts and a map, not generic advice. <https://arxiviq.substack.com/p/evaluating-agentsmd-are-repository> (RESEARCH, via summary)

### 1.5 Long-context retrieval research (RESEARCH)

- **Lost in the Middle** (Liu et al., 2023; TACL 2024). U-shaped accuracy: facts at the start and end are recalled well, the middle sags. This holds across models, including long-context ones. <https://arxiv.org/abs/2307.03172>
- **Chroma "Context Rot"** (14 Jul 2025, 18 models incl. Claude 4, GPT-4.1, Gemini 2.5). Performance drops as input grows even on simple tasks. Semantically similar distractors hurt, and a single distractor gives a measurable drop. <https://trychroma.com/research/context-rot>. Third-party summaries put the NIAH drop at 20–50% from 10k to 100k+ tokens (<https://www.morphllm.com/context-rot>, PRACTITIONER).
- **NoLiMa** (ICML 2025). When needle and question share no words, 11 models fall below 50% of their short-context baseline **at 32K**. GPT-4o goes from 99.3% to 69.7%. <https://arxiv.org/abs/2502.05167>. This matters for us: 30–100 KB is about 8–30k tokens, which is exactly this range, and our questions ("is this seller price-sensitive?") rarely share words with the evidence.
- **Recursive Language Models** (Zhang, Kraska, Khattab, MIT, arXiv 2512.24601). Treat the long input as a variable in a REPL and let the model peek, grep and slice. This beats base LLMs even on prompts that fit the window. <https://arxiv.org/abs/2512.24601>
- **Letta, "Is a filesystem all you need?"** (12 Aug 2025). Conversation history was put in files. An agent with grep / search_files / open scored 74.0% on LoCoMo using gpt-4o-mini, against 68.5% for Mem0, because "Agents today are extremely effective at using filesystem tools". <https://www.letta.com/blog/benchmarking-ai-agent-memory> (RESEARCH-ish vendor benchmark)
- **Claude Code chose agentic grep over RAG.** Boris Cherny: early Claude Code tried a local vector DB, and glob plus grep "outperformed everything by a lot". <https://smartscope.blog/en/ai-development/practices/rag-debate-agentic-search-code-exploration/> (PRACTITIONER, second-hand quote)

### 1.6 Formats: markdown vs JSON (DOCUMENTED / PRACTITIONER)

- Anthropic says the format (XML / JSON / Markdown) affects results and should be chosen by eval. There is no universal winner (writing-tools post above).
- Practitioner consensus (2026): markdown is the token-cheap, readable agent view. JSON is for programs and `jq` slices. Large raw JSON costs more tokens because of repeated keys and quotes. <https://buildwithfern.com/post/how-to-write-llm-friendly-documentation> (PRACTITIONER)

### 1.7 Our own files (MEASURED, aggregates only)

10 current files in `data/contexts/`: **26.9–86.8 KB, 571–825 lines, 13 H2 sections (A–K), almost all ASCII** (≤ 783 non-ASCII bytes). That works out to about 4 chars/token, so 7k–22k tokens. Bytes per section in the biggest file (85.6 KB):

- D Categories/products: 21.0 KB
- E Buyer demand/buyleads: 34.4 KB
- J Other channels: 10.7 KB
- C Business profile: 5.8 KB
- the other 9 sections: 0.6–2.2 KB each

So two sections make up 64% of the bytes. The decision-critical blocks (identity, language, timing, past calls, relationship, risk, this call) are small. These files hold no full transcripts yet. Adding transcripts (often 3–10 KB per call, Devanagari tokenises worse) will push heavy sellers past 25k tokens.

## 2. Tradeoffs

| | One big `.md` (index on top, stable headings) | Folder: `INDEX.md` + per-section / per-call files (+ `context.json`) |
|---|---|---|
| Fits Read limit | No at about 100 KB. A whole read gives a `PARTIAL view`, and the agent must page with offset/limit | Yes. Each file is well under the limit and every read is whole |
| What lands in context | Whole file (8–30k tokens) if read in full. Lost-in-the-middle and distractors apply | Only the files the task needs. Smaller, more relevant context |
| Navigation | `grep -n "^## "`, then offset/limit by line number. Line numbers shift when content changes | `ls` plus the file map. File names carry meaning (Anthropic: "Name files descriptively") |
| Grep | Works, but hits are only `line N` of one file | `grep -rn` returns `file:line`, so the hit already says which domain it is in |
| Risk of missing info | Low if the agent reads it all, high if it stops after the first page | The agent may not open a file it needs (Vercel: skills unused 56%). Mitigate with an index that holds the key facts plus explicit "open when" rules |
| Builder complexity | Simplest (what we have now) | Slightly more: split on existing H2 boundaries and write a manifest |
| Human review / demo | One scroll | Folder. A concatenated `all.md` can still be emitted for humans |
| Citations | `§E` or line numbers (fragile) | `file#ID`. Script-checkable |
| Per-call transcripts | Bloat the single file | One file per call. Opened only when a past call matters |

**JSON.** Good for scripts: validation, counting, the "candidate lead ranking" maths. It is a poor primary agent view because of token overhead and repeated keys. Keep both, generated from the same build: JSON is the source of truth, markdown is the rendering.

**Counter-view.** Vercel's result says passive context beats on-demand context. Doesn't that argue for one file? Only up to a size. Their winning index was 8 KB, and it *pointed to* files. At 100 KB the passive file no longer fits one read and loses recall in the middle. So we take their lesson as "the index plus the essentials are passive, the rest is on demand".

## 3. Recommendation for our case

### 3.1 Layout and naming

```
data/contexts/<glid>/
├── INDEX.md                 # READ FIRST. ≤ 150 lines, ≤ 8 KB (~2k tokens)
├── core.md                  # A,B,F,H,I,K: identity, language, timing, relationship, risk, this call (~8 KB)
├── business.md              # C business profile + E09/E10 value and AOV
├── catalogue.md             # D categories and products (largest; TOC at top)
├── buyleads.md              # E buyer demand and buy leads (large; TOC at top)
├── enquiries.md             # buyer enquiries / PNS
├── channels.md              # J other channels
├── peers.md                 # peer statistic + fallback level used
├── candidate_leads.md       # ranked showcase leads for the money hook
├── calls/
│   ├── C01_2026-08-14.md    # one file per past call: header + turn-numbered transcript
│   └── C02_2026-09-12.md
├── context.json             # full machine copy (same IDs), for scripts and jq
└── all.md                   # optional: concatenation for humans; agent told not to read it whole
```

- **Naming.** Use fixed, descriptive, lowercase names that are the same for every seller, so the skill text can name them. Call files are `C<nn>_<YYYY-MM-DD>.md`, sorted by time.
- **Depth.** Only `calls/` is a subfolder. INDEX.md links **every** file directly, including each call file, so all references stay one level deep from the index.
- **Size per file.** Target ≤ 30 KB, hard cap ≈ 60 KB / 15k tokens, so a whole read always fits under the 25k-token Read limit with margin for Devanagari. If `catalogue.md` or `buyleads.md` passes the cap, the builder splits it (`buyleads_live.md`, `buyleads_expired.md`) and lists both in the index. Any file over 100 lines starts with a `## Contents` list.
- **Lifecycle.** The builder writes the folder from `context.json`. It never hand-edits it, and the files are regenerated whole each run, so record IDs are stable within a run.

### 3.2 INDEX.md format (llms.txt style)

```markdown
# Seller <glid-hash> context (built 2026-10-10T06:00, as-of 2026-10-09)
> One-paragraph factual summary: who, what they sell, language, plan, call count, last outcome.

## Key facts (passive; cite as INDEX#Kn)
- K1 Language: Hindi (recorded) · K2 Best slot: 11:00–13:00 (n=6 answered) · K3 Plan: …
- … ≤ 25 facts, each with a source pointer, e.g. "(core.md#F2)"

## Past calls (one row per call; open the file only if the row matters)
| ID | Date | Dur | Outcome | One-line gist | File |
|---|---|---|---|---|---|
| C01 | 2026-08-14 | 2:10 | callback | asked for price list on WhatsApp | [calls/C01_2026-08-14.md](calls/C01_2026-08-14.md) |

## Files (open when…)
- [core.md](core.md) (8 KB): identity, language, timing, relationship, risk, this call. **Always read.**
- [buyleads.md](buyleads.md) (34 KB): leads seen/bought, by MCAT. Open when choosing the money hook or judging demand.
- [candidate_leads.md](candidate_leads.md) (3 KB): ranked live/expired leads. Open for board item 6.
- [peers.md](peers.md) (2 KB): peer statistic + fallback level. Open before any social-proof line.
- [catalogue.md](catalogue.md) (21 KB): products/categories. Open for profile-gap or product questions.
- …

## Optional (skip unless needed)
- [all.md](all.md): everything concatenated, for humans.
- [context.json](context.json): machine copy; use `jq`, never read whole.

## Missing / not available
- e.g. "no enquiries in 90 days", "peer cell < 5 → national fallback"
```

The index states each file's size, so the agent knows the cost before it opens a file. The "Missing" block stops the agent hunting for data that does not exist.

### 3.3 How the agent is told what to open when (in SKILL.md)

1. **Always** read `INDEX.md` and `core.md` in full (about 4k tokens together). This is the passive layer.
2. For each decision the skill makes (voice and gender, language, opening hook, money lead, peer line, objection playbook), SKILL.md names the file(s) to open, in a small "decision → files" table. That table is a reading map, not a rule table for the decision.
3. Open a call transcript only when the index's call row is relevant (same objection, a promise made, a complaint, a callback). Otherwise the row's gist is enough.
4. Search before reading. Use `grep -rn -i "<term>" data/contexts/<glid>/` across the folder, then read the hit file whole (or with offset/limit if it is the rare oversize file). Use `jq` on `context.json` for counts and filters.
5. Never read `all.md` or `context.json` whole.
6. Enforcement (from our peer-skill review). A PostToolUse/Stop hook or `validate_persona.py` checks that every evidence row cites an ID that exists, and that the file holding it was actually Read in this session. A decision that cites only INDEX facts for a field marked "open X" is flagged.

### 3.4 Citations

- **Record IDs, written by the builder:** `K1…` (index facts), `F2` (core facts), `P-<n>` (products), `L-<lead id hash>` (buy leads), `ENQ-<n>`, `PEER-1`, `CL-<n>` (candidate leads), `C03.T12` (call 3, turn 12). Each ID appears once, at the start of its line or table row, so `grep -n "C03.T12" -r` finds it uniquely.
- **Evidence row format** (written by the agent to its evidence file): `{"claim": "...", "cite": "calls/C03_2026-09-20.md#C03.T12", "quote": "<≤ 20 words>"}`. A short quote follows Anthropic's "ground responses in quotes" advice and lets the validator string-match the quote against the cited file.
- Do not cite by line number (it shifts between builds) or by section letter alone (too coarse).
- Data policy is unchanged. GST/PAN/ID numbers are left out of every file the frontier model sees. Names and addresses go only into `core.md`, and only when a task needs them (team decision 2026-10-09).

### 3.5 What to measure next (cheap eval)

Use 5 sellers × 10 probe questions whose answers sit deep in the data (a lead from 3 weeks ago, an objection in call 2), each answered with a cited ID. Compare (a) the current single file, (b) the folder layout. Score correct answers, correct citations, tokens read, and files opened vs files needed. Anthropic says to choose formats by eval, and "Observe how Claude navigates" (ignored files mean the map or names need fixing).
