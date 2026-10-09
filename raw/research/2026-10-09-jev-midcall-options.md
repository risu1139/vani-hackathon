# Jev for PS04 mid-call switching: live vs between runs (2026-10-09)

Tags: PROVEN = we ran it. DOCUMENTED = vendor docs. ASSUMED = inference, not tested.

## 1. What Jev is

- **What it is.** A decision model, not a chat model. You send a `state` (any JSON) and a map of named `questions`. It returns one probability or choice per question, with no text output. The model ID is `typesafe/jev-1.13`; the response names the snapshot `typesafe/jev-1.13-20260917`. (PROVEN)
- **Request.** `POST https://openrouter.ai/api/alpha/decisions` with body `{model, state, questions}`. (PROVEN)
  - Question types: `noul` (yes/no), `choice` (up to 255 options), `score` (2 to 10 ordered levels).
  - Each question has `instructions` and `criteria`. Both can be a string, an object or an array.
  - Optional request fields: `provider`, `session_id`, `trace`, `user`.
  - (DOCUMENTED: OpenRouter Python SDK reference; TypeSafe API and Advanced pages)
- **Response.** (PROVEN)
  - `answers.{name}.noul` gives P(yes). There is no confidence field for noul.
  - A choice answer gives `choice`, `confidence` and `probabilities`.
  - The response also has `usage.input_tokens` and `usage.cost`.
- **Several signals in one call: yes.** We already send 6 questions (rushed, frustrated, confused, bot_question, interested, language) in one request. (PROVEN)
  - The questions are answered in parallel and cannot see each other's answers. (DOCUMENTED)
  - Going from 1 to 6 questions barely changed latency: 491 ms vs 482 ms p50. (PROVEN, 2026-10-07)
- **Several turns in one call: no batch field.** The SDK reference documents one `state` per request. For offline labelling, send parallel requests instead. TypeSafe's own pattern is one question per record, all in one call, which is possible but unnecessary. (DOCUMENTED)
- **Cost.** $0.042 per million input tokens; output tokens are free. One 6-question decision is about 1,000 tokens, or about $0.00004. Labelling 64K turns once costs about $3. (PROVEN per call; DOCUMENTED price)
- **Limits.**
  - Context: 32K tokens for the state plus the longest question (64K per request on TypeSafe direct).
  - TypeSafe direct rate limit: 80 requests/s and 100K tokens/s, adjusted dynamically.
  - No Decisions-specific rate limit is published for OpenRouter. Its general limits page covers only free-model caps and 402/429 handling.
  - (DOCUMENTED)
- **Tuning.**
  - There is no fine-tuning: "Jev is not fine-tuned … per customer". The only levers are `state`, `instructions` and `criteria`, plus our own thresholds on `noul`. (DOCUMENTED)
  - So the between-run loop tunes:
    - (a) criteria wording;
    - (b) per-signal enter/exit thresholds;
    - (c) optional Platt or isotonic calibration on the noul values.
  - Pin the snapshot so calibration stays valid.
  - Criteria wording matters a lot. Today one probe with a vague 1-line criterion scored "अभी बिज़ी हूँ, बाद में कॉल करो" as rushed at only 0.38. The spike criteria score the same kind of sentence at 0.95. (PROVEN, n=1)
- **Accuracy so far.**
  - Native script: 49/51 on the main set and 10/10 on the tricky set, at about 500 ms p50. The misses are "ok ok" read as interested, and one Hindi/Hinglish label dispute.
  - It catches "फिर से पूछ रहा हूँ, प्राइस बताओ वरना फोन रख दो" as frustrated. The keyword list misses this.
  - Caveat: 36 hand-written sentences, one run, no real ASR noise. (PROVEN)

## 2. Can a Sarvam cloud code tool reach Jev during a call?

**Why it is VPN/IPv4-only today: an IP allowlist on the OpenRouter account, not internal DNS.** (PROVEN)
- openrouter.ai is a public Cloudflare host (104.18.2.115 / .3.115). It resolves the same on 8.8.8.8.
- No key: 401. Key from the VPN IPv4 egress 121.241.109.212: 200, rushed answered in 1.09 s with a fresh connection (curl).
- Key from Wi-Fi IPv6, or from Daytona (35.234.211.110): 403 "IP address is not in the allowlist for this account" (2026-10-07). Today the IPv6 path did not connect at all.
- The VPN is a full IPv4 tunnel (0.0.0.0/1 and 128.0.0.0/1 routes go to 10.1.0.1).

**Can a code tool make HTTP calls at all?** Yes. Sarvam's code-tool example uses `httpx.AsyncClient`. (DOCUMENTED)
- The documented egress IP is 4.213.167.70. We saw API-tool traffic come from it (PROVEN). That code tools use the same IP is ASSUMED.
- Sarvam documents no limits on packages, size, memory or timeout for code tools ("available on request"). The API tool's max wait is configurable up to 30 s. (DOCUMENTED)

**Internal LiteLLM gateway (`imllm.intermesh.net`).** (PROVEN today)
- It is public: 34.49.227.141 on public DNS, and `/health/liveliness` returns 200 from both the VPN laptop and Daytona.
- It cannot serve Jev today:
  - From the VPN, `/typesafe/v1/systemone` returns 404 (pass-through route not configured).
  - From Daytona the same path returns a load-balancer 403 HTML page, so it is path-blocked for outside IPs.
  - Our available key can only access `no-default-models`, and `typesafe/jev-1.13` returns 403 `key_model_access_denied`.
  - The gateway's earlier 8 Jev requests all failed (spike log).
  - Jev cannot run through `/chat/completions` at all; it needs the Decisions/SystemOne shape. (DOCUMENTED)
- Making it usable needs a gateway admin: configure the TypeSafe pass-through, unblock the path for 4.213.167.70, and issue a key with Jev access.

### Bridge options

| option | live or offline | latency added per seller turn | what it needs | risk | evidence |
|---|---|---|---|---|---|
| A. Code tool calls OpenRouter Decisions directly (httpx) | live | ~500 ms p50 on keep-alive, ~760 ms to 1.1 s on a new TLS connection per tool run; p95 ~950 ms | Add Sarvam egress 4.213.167.70 to the OpenRouter account IP allowlist; key stored as a code-tool secret | Allowlist owner may refuse a shared Sarvam IP (any Sarvam customer then shares it, though our key is still required). Connection reuse across tool runs is unknown. Adds directly to the 2.1 s turn | Allowlist cause PROVEN; httpx in code tool DOCUMENTED; latency from Sarvam ASSUMED |
| B. Code tool calls the LiteLLM gateway TypeSafe pass-through | live | Probably like A, or a bit lower (direct to TypeSafe, no OpenRouter hop: OpenRouter overhead ~150 ms) | Gateway admin: configure the pass-through, allow the path for 4.213.167.70, issue a Jev key | Not working today (404/403); depends on an admin; gateway reliability is unknown | Gateway state PROVEN; LiteLLM pass-through DOCUMENTED; latency ASSUMED |
| C. Relay on Daytona (our server calls Jev; Sarvam HTTP or code tool calls the relay) | live | A + one extra hop (~20 to 100 ms) | Daytona IP 35.234.211.110 allowlisted on OpenRouter, AND a working inbound URL: preview DNS `*.proxy-daytona.intermesh.net` plus a wildcard cert from the Daytona admin | Preview URL has no DNS (PROVEN twice). Sandbox found stopped despite autoStop 0. Two admin asks, two failure points | PROVEN blockers |
| D. cloudflared quick tunnel into Daytona or the laptop | live | A + Cloudflare hop (~0.1 s measured to health) | Nothing from admins; on the laptop it reuses the VPN allowlist | Random URL changes on every restart, so the agent config must be edited each time. The earlier tunnel died. No SLA. Laptop-hosted means the demo depends on the laptop and VPN staying up | PROVEN works once, PROVEN died |
| E. Sarvam HTTP API tool to a relay (instead of a code tool) | live | Same as C/D + an extra LLM step to fill tool args | Same hosting as C or D | No gain over a code tool; we moved away from it | PROVEN (spike 2/3) |
| F. Keyword lexicon in the code tool (today) | live | ~0.07 ms | Nothing | Misses phrases, has false positives | PROVEN |
| G. Distilled small classifier in the code tool (Jev-labelled char n-gram logistic regression, pure Python, weights inlined) | live | <5 ms (ASSUMED) | A Jev-labelled training set; packages/size limits allow inlined weights | Sarvam code-tool size and dependency limits are undocumented; numpy/sklearn availability unknown, so write pure Python. Quality is bounded by Jev labels and the training data | Limits undocumented; pydantic/json/unicodedata imports PROVEN to work |
| H. Jev offline: label past PS07 seller turns into a gold set (with human spot check) | offline | n/a | VPN laptop (works today); data stays in git-ignored data/ | Jev is weaker outside English; needs human gold on ~300 turns | Route PROVEN; cost DOCUMENTED |
| I. Jev between runs: tune lexicon, criteria and thresholds against the gold set | offline | n/a | H | Overfitting to a small set: keep a held-out split | ASSUMED design |
| J. Jev post-call relabel of switch_log (analytics API returns switch_log per call) | offline | n/a | Agents API key + VPN laptop | Utterances are truncated to 120 chars and the log is capped at 4,000 chars | switch_log readback PROVEN |

## 3. Latency budget

- **Today's numbers.** Reply latency after the seller stops is ~2.1 s median (1.2 to 3.5 s) with a stub classifier (PROVEN). The in-Sarvam keyword tool removed the network hop, but the tool-call LLM step remains.
- **Synchronous Jev.** It would add ~0.5 s p50 and ~1 s p95. The median turn would rise to ~2.6 s and the worst case to ~4.5 s (ASSUMED arithmetic). That is noticeable on a phone call, and our own research set a sync budget of p95 < 250 ms. Jev via OpenRouter from India is about 2 to 4x over that. Do not run Jev synchronously on every turn.
- **Async / next-turn.** Classify turn N, apply at N+1.
  - A code tool has to finish before it returns: variables cannot be set after return, and background tasks surviving after return is unknown (ASSUMED). So true async needs a relay host (C/D): the tool posts turn N fire-and-forget and reads the turn N-1 result.
  - That brings back all the hosting risk.
  - It also applies switches one turn late. That is wrong for rushed and frustrated, which need the very next reply to change.
  - Verdict: weak.
- **Hybrid inside the code tool.** The keyword list decides instantly. Jev is called only on some turns, with a hard ~400 ms timeout; on timeout the keyword result stands.
  - "Jev only when keywords found nothing" runs on most turns, because most turns are neutral. It saves little latency.
  - A better gate is "keywords found nothing AND the turn is long or ambiguous" (e.g. ≥5 words, or a known risky token such as फिर से, ok, हाँ). Or use Jev to veto a keyword hit before switching.
  - Still needs option A or B to be unblocked. The latency cost then falls only on the gated turns.
  - Verdict: feasible only after the allowlist change. Measure p95 from inside Sarvam first.

## 4. Using Jev without the live call

- **Gold set.** Label PS07 seller turns offline from the VPN laptop.
  - Use the frozen 6-question set and the pinned snapshot.
  - Stratify: random turns plus turns where keywords or a first Jev pass flag rare signals.
  - Have a human spot-check ~300 turns.
  - Cost is about $3 for 64K turns. (cost DOCUMENTED; route PROVEN)
  - Only aggregates go into raw/ and wiki/.
- **Between-run tuning** (the team's "tune, don't train" rule fits exactly):
  - (a) Add or remove lexicon cues where keywords disagree with Jev or gold.
  - (b) Set per-signal Jev thresholds. For example, raise "interested" above 0.7 to stop "ok ok" firing.
  - (c) Rewrite criteria and re-score on a held-out split.
  - The classifier stays frozen within a run.
- **Post-call relabel.** Pull switch_log through the analytics API. Jev labels each logged utterance. Diff Jev against the lexicon decision to get misses and false positives per run, which feeds the next lexicon version.
- **Distillation into the code tool.**
  - Train a small char n-gram (1 to 4 chars, NFD-normalised, covering Devanagari, Tamil, Gujarati and Latin) logistic regression per signal on Jev labels.
  - Export the weights as a dict and run it in pure Python: no numpy, sub-ms.
  - Unknown: Sarvam's code-tool size and import limits, which are not documented. Test with a ~100 to 500 KB weight dict.
  - This is our own logic (allowed) and frozen per run. It could replace or back up the lexicon.

## Recommendation

- **Live (in-call): do not put Jev in the turn path for the demo.**
  - Keep the frozen in-Sarvam classifier: lexicon now, and a distilled n-gram model if it beats the lexicon on the held-out gold.
  - Language switching stays with Sarvam's native auto-detect.
- **Optional live upgrade, only if two things happen early:**
  - (1) The OpenRouter admin allowlists 4.213.167.70 (or the gateway admin enables the TypeSafe pass-through for it).
  - (2) A measured p95 from inside a Sarvam code tool is ≤ ~400 ms.
  - Then use the hybrid: lexicon first, Jev on gated ambiguous turns with a 400 ms timeout, lexicon as fallback.
  - Do not build the async relay; hosting is unproven and late switches defeat the purpose.
- **Between runs: Jev is the frozen teacher.**
  - It labels the PS07 gold set and relabels every run's switch_log.
  - It drives lexicon, criteria and threshold changes, and supplies training labels for the distilled model.
  - This uses the path that already works (VPN laptop, IPv4) and keeps the in-call decision deterministic, satisfying the "frozen classifier decides" rule.

## Asks to unblock live Jev (if wanted)
1. OpenRouter account owner: add 4.213.167.70 to the IP allowlist.
2. Or LiteLLM admin: enable `/typesafe` pass-through, allow it for 4.213.167.70, and issue a key with `typesafe/jev-1.13`.
3. Sarvam: code-tool limits (max code size, available packages, timeout, whether the HTTP client persists between runs).
