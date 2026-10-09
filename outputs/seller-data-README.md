# Seller-data side: hand-off for the persona session

As of 2026-10-09 (evening). Written by the seller-data session. Everything here is on `origin/main`; start at the **final plan**. Our scope: data extraction, data strategy, what goes to the LLM, and the LLM prompt. We do **not** edit `app/contracts/*` or the v6 plan; you map our output into your schema.

## Read in this order

| # | File | What it is |
|---|---|---|
| 1 | [`outputs/plans/Seller context final plan.md`](plans/Seller%20context%20final%20plan.md) | **The plan of record on our side**: what we learned, what to drop / add / keep, the 8 KB LLM context, the prompt, build order to the D2 12:00 freeze, open items |
| 2 | [`outputs/llm-data-strategy.md`](llm-data-strategy.md) | which data points go to the LLM (tiers), why, coverage, as_of-safe flag per field |
| 3 | [`outputs/call-flow-playbook.md`](call-flow-playbook.md) + [`call-flow-analysis.md`](call-flow-analysis.md) | what 70 real VANI calls + 1 human call show: flow, 12 objections with conversion, compliance problems, prompt rules |
| 4 | [`outputs/seller-data-sources.md`](seller-data-sources.md), [`seller-context-apis.md`](seller-context-apis.md), [`aids-data-overview.md`](aids-data-overview.md) | every offline file and internal API, what each provides |
| 5 | [`outputs/plans/Seller context B1 data catalogue.xlsx`](plans/Seller%20context%20B1%20data%20catalogue.xlsx), [`outputs/seller-md-field-inventory.xlsx`](seller-md-field-inventory.xlsx) | data points A01-K04, source, API status, coverage |
| 6 | [`app/context/examples/example_seller.points.json`](../app/context/examples/example_seller.points.json) | **synthetic** example of our per-seller output |

## Code (`app/context/`)

| File | Purpose |
|---|---|
| `SCRUBBER.py` | builds `data/contexts/<glid>.md` and `<glid>.points.json` per seller from files + production APIs. **G (old VANI call history) and scheduling points are not emitted.** ID numbers (GST / PAN / Aadhaar / IFSC / account) are scrubbed from `points.json` |
| `extraction_map.py` | single source of truth: each data point -> file source, API endpoint + fields, status, plus every API we tested with the request body that worked |
| `make_testset.py`, `seller_inventory.py` | the 100-GLID test set; per-seller coverage index |
| `api_probe.py`, `http_util.py` | API reachability probe and HTTP helper |
| `transcribe_call.py`, `call_transcribe.py` | Sarvam speech-to-text for call recordings (key from env) |
| `voice_call_sim.py`, `sarvam_context_test.py` | earlier tests with the Sarvam chat model; **to be replaced** by Claude (Sarvam = voice only) |

Run (secrets from env vars, never in files): `VANI_AK=... VANI_USERS_TOKEN=... VANI_USERS_MODID=GLADMIN python app/context/SCRUBBER.py --glid <GLID>` or `--all`. Source data lives in git-ignored `data/` (real seller PII), so **you cannot rebuild contexts from the repo alone**; use the synthetic example for the shape and ask us for the demo files.

## Output shape (what you map)

`data/contexts/<glid>.points.json` = `{ "<ID>": {"value": ..., "source": "..."} }`, one entry per data point (A01-K04 minus G and the scheduling set). Sources and as_of safety are in `extraction_map.py` and `llm-data-strategy.md`: **file history is as_of-safe; live API values (users, scorecard, topbar, prepplus, byr_supply ...) are not**.

## What changed since our earlier messages

1. **G (old VANI call history) is out of scope** (user decision). That includes the per-call signal rows (G11) and G01-G10 we told you about earlier. We will not emit them. If your trait / state builder (B2) needs rushed / confused / frustrated / asked-if-bot per call, compute it on your side from PS07, or drop those states.
2. **Scheduling stays out** (best time, retries, callback slots, do-not-call hours, attempt number).
3. **New in the plan, not built yet:** `verified_facts` (statements the LLM may say, each with a source), a trigger -> hook table, executive-contact status, a compact 8 KB `.llm.md`, a versioned prompt (`prompts/seller_persona_v1.md`), a replay test on real seller lines.
4. **LLM = Claude** (CLI now, Daytona later). **Sarvam API = voice only.**
5. We use production hosts only; the AK (about 24 h) and the users service token come from env vars.

## Open items (owners are not ours)

1. One approved price statement, or a rule to say none.
2. Supported voice languages (Hindi, English and a Tamil switch worked in calls; Odia failed).
3. Meanings of trigger buckets UA, PAM, SCHD, NUR, OLP (our inference from calls is in the plan).
4. DNC is a hard gate in the dialler, outside the LLM.

## What we need from you

- Whether you want the compact `.llm.md`, the prompt, or both as an input to your composer (we will not edit your files).
- Confirmation that dropping G is acceptable for your B2.
