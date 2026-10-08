---
name: wiki-file
description: File research, notes, docs or chat findings into this project's raw/ → wiki/ knowledge base. Use whenever the user says "file this", "dump to raw", "add to wiki", "save this research", drops a file in raw/, or after any research worth keeping.
---

# Filing into the wiki

Follow the constraints in `AGENTS.md`. This skill is only the procedure.

## Steps

1. Read the source.
2. Read `wiki/index.md`. Prefer updating an existing article over creating one.
3. Dump the source into `raw/<category>/` **unchanged** (categories so far: `research/`, `hackathon/`; create others on demand).
   - Research dumps: `<YYYY-MM-DD>-<tool>-<slug>.md`. Manual drops/extracts: `<YYYY-MM-DD>-<short-slug>.<ext>`.
4. Write/update the article:
   - `wiki/concepts/` → evergreen (tools, models, techniques).
   - `wiki/projects/vani-hackathon/` → hackathon-scoped (choice, plan, decisions).
5. Update `wiki/index.md` in the same pass.
6. Reply in 2–3 lines: what was filed, where, what was updated.

## Article rules

- Filename: lowercase-hyphenated `.md`.
- Line 1 after the title: `Sources: [[raw-stem]] · [[raw-stem]]`. It marks the raw file as filed, so never omit it.
- Lead with the answer. No preamble.
- `[[wikilinks]]` liberally; dangling links are intentional (future articles).
- Date-stamp time-sensitive claims ("as of 2026-10-07").
- Images: `wiki/concepts/foo-images/…` next to the note.

## Index format (exact)

One section per wiki subfolder, one line per article:

```
- [[article-slug]] — one-sentence decision aid (≤140 chars).
```

The summary answers "should I open the full article?", not a digest. Past ~3K tokens, split into sub-indexes (`wiki/concepts/index.md`) and keep root as a map of maps.
