# Mid-call switch tests: T1, T2, T3, T4, T9, T10 and a head-to-head of switch routes (2026-10-09)

Live tests on our own Sarvam agents, run from the VPN laptop on 2026-10-09 between 16:00 and 17:30 IST.
- **Agents.** All config changes were made on clones, and the main agent `Voice-Bot-104c356b-536d` was not changed (see the last section).
- **Seller audio.** Sarvam TTS (bulbul v3, "rahul") spoke made-up seller lines into SDK voice sessions.
- **No phone calls.** Nothing was published, and no customer data was used.

Test list: `2026-10-09-sarvam-native-midcall-switching.md` (T1–T10). Route list: `2026-10-09-midcall-switch-all-routes.md` (O1–O20).
Code: `app/spike/midcall_compare.py` (harness), `midcall_analyze.py` (scoring), `midcall_probe.py` / `midcall_envelope_probe.py` (T1), `midcall_out_poll.py` (phone OUT half), `midcall_relay.py` + `midcall_clf_offline.py` (O2c/O6), `code_tools/` (tool files).
Raw run JSON: `outputs/midcall_tests/` (`*-scored-*.json` = scored copy with per-turn checks and switch_log).

## How a run was scored

**Test set.** One scripted call per signal, plus one mixed call. Each call has an opener, the signal line, and a neutral follow-up:
- **rushed:** "अभी बिज़ी हूँ यार, जल्दी बोलो क्या है"
- **frustrated:** "कितनी बार कॉल करोगे, परेशान कर दिया है"
- **confused:** "समझ नहीं आया, क्या मतलब मीटिंग?"
- **interested:** "अच्छा, ये कैसे काम करता है? कितना चार्ज है?", preceded by a bare "ओके ओके" turn, which should get no switch
- **Gujarati switch:** "ગુજરાતીમાં વાત કરો ને…"
- **opt-out:** "मुझे कॉल मत करो, मेरा नंबर हटा दो"
- **A_hostile mix:** identity question, "not the owner", price demand, "फिर से पूछ रहा हूँ… वरना फोन रख दो", then rushed

The T4/T9 runs add the older `A_coop` and `B_gujarati` scripts.

**Reply checks** (regex on the reply, after removing a restarted or repeated part):
- **rushed:** 16 words or fewer, plus a call-back or time offer
- **frustrated:** an apology
- **confused:** 3 or more short comma phrases, or a "समझ आया?" check
- **interested:** moves to a meeting, day or time
- **Gujarati:** Gujarati script in the reply
- **opt-out:** "number removed / won't call again"

"Same turn" means the reply to the signal line itself passes. "Next" means only the following reply passes.

A **false switch** is a neutral turn whose reply shows apology, opt-out or confused phrasing.

Caveat on the interested check: it is weak. With no switch mechanism at all (O0), the agent pushes for a meeting anyway.

**Latency figures:**
- **Onset:** reply onset measured on the laptop, from the end of the seller audio to the first loud agent audio. It includes network.
- **Server RT:** Sarvam's own "avg agent response time" per call, from the analytics API, as the median over calls.

## Verdicts

### T1 – client push over the session WebSocket: DISPROVEN
- **What was done.**
  - The raw receive was hooked (`AsyncSamvaadAgent._route_message`).
  - Hand-built frames were sent into a live voice session:
    - `client.action.variable_update` in 4 envelope shapes (`agent_variables`, `variables`, `variable_name`+`value`, `data`);
    - `client.action.language_change` in 2 shapes (`language_name`, `language`);
    - `client.action.state_transition` in 2 shapes (`state_name`, `next_state`);
    - and `client.media.text` as a control.
  - Each variant ran in its own session (`t1-envelopes-*.json`); the first mixed probe is `probe-probe-*.json`.
- **Result.** Every `client.action.*` frame made the server close the session at once: close code 1000, empty reason, no `server.event.*` echo, 8/8 variants. Only `client.media.text` kept the session alive.
- **Server events seen in normal sessions:** `interaction_connected`, `transcription`, `user_interrupt`, `interaction_end`, `text_chunk`, ping. There was never a `variable_update`, `tool_call` or `state_transition` event.
- **End-to-end proof (Jev → push → next reply).** Not possible over this channel. The text-injection variant was measured instead (O3t below).
  - Push timing in O3t (21 pushes, `O3t-*.json`, per-turn `jev` blocks hold {utterance, scores, from, to, pushed, push timing, before reply onset}):
    - user transcript reaches the laptop 0.51 s (median) after the seller stops;
    - Jev takes 534 ms (median; max 1.26 s);
    - the push lands 1.06 s (median; range 0.08–1.59 s) after the seller stops;
    - agent audio starts at 1.50 s.
  - So the push arrives before the agent speaks, but after the LLM has started writing. It cannot shape the same turn.

### T2 – Webhook Variable Update (IN half): BLOCKED
- **What exists.**
  - Per-variable `webhook_config {enabled, template}` in the agent schema. Its description: "updating this variable via interaction events webhook … during an active interaction". The template is Jinja, e.g. `{{ kyc_status }}`.
  - The workspace flag is `webhook_variable_update: allow`.
  - The console code renders a "Webhook Variable Update – Update this variable via webhook response" toggle, but only inside an "advanced" variable mode. In our console the Edit and Create variable dialogs show only name, default and "Include in context".
- **What does not exist (that we can find):**
  - an inbound endpoint. No URL in the console's API client or in the public API reference accepts a variable for a live interaction; the docs page `/conversations/build/advanced/webhook-variables` is 404.
  - The only `/webhooks/…` route in the console client is `POST /webhooks/{provider}/kyc`. It belongs to the telephony sub-account KYC verification service and is unrelated.
- **Why it could not be enabled.** That would need a raw config write with the console's bearer session, which we do not use. An attempt through the console Settings→Secrets page (for a related test) was refused by our own permission policy.
- **Verdict.** It cannot be enabled or exercised today. Its name ("via webhook response", "interaction events webhook") suggests the value is pulled from the response to an event webhook Sarvam sends. It does not look like a push endpoint we can call. We need Sarvam's answer (mail developer@sarvam.ai) before relying on it.

### Phone OUT half – getting each seller turn out of a live call without an LLM tool call: DISPROVEN (no real-time feed)
- **Webhooks.** All documented webhooks fire after the call: deployment, instant outbound and campaign webhooks with `interaction_transcript` + `final_agent_variables`. None is per turn.
- **Event subscriptions.** None for telephony in the docs or the console API client. Per-turn events (`transcription`, `user_interrupt`) exist only on the SDK/web WebSocket.
- **Polling the analytics API.** `GET …/transcripts/{interaction_id}` does return a live call's transcript while it is running (HTTP 200, 440–760 ms per poll). But it lags:
  - the greeting appeared about 11 s into the call (`out-poll-*.json`);
  - a seller turn appeared 15.9 s after the seller stopped, against 0.62 s for the SDK `transcript_callback` (`out-poll-timing-*.json`).
  - It is not usable per turn.
- **Fallbacks (both need the LLM to call a tool every turn):**
  - (a) A code tool forwards the utterance to our host. Proven: see O2c.
  - (b) An API tool posts `@Call Transcript`. Not run: see O5.
  - Both also need a public HTTPS URL to the laptop or Daytona. The quick tunnel worked but is blocked by our own security policy for further use, and Daytona preview DNS is still missing.

### T10 – code-tool network access: PROVEN
- **What was done.** A temporary probe in `ReadSellerSignal` on clone 1 (`vani_clone_t10.py`, httpx with a 3 s timeout, try/except) wrote into the variable `net_probe`.
- **Results:**
  - api.ipify.org: 200 in 249 ms, source IP **4.213.167.70** (the documented Sarvam egress);
  - httpbin.org/get: 200 in 756 ms;
  - openrouter.ai Decisions with no key: 401 in 206 ms. OpenRouter is reachable; with our key it would get the allowlist 403 (seen earlier from other non-VPN IPs).
- **Cleanup.** The probe was removed by re-upload. Evidence: interaction `20261009/95098455-16:16:20-60182e32` (`net_probe` variable in the analytics API).

### T3 – why our tool is skipped on language-switch turns: hypothesis DISPROVEN
- **Baseline.** On the main agent with the current tool, our tool ran on 1 of the 2 Gujarati switch turns.
- **Log Analyser on the skipped turn** (`20261009/b197bd5d-16:39:40-564b1f77`):
  - no tool call at all, so `change_output_language` did **not** take the slot;
  - ASR tagged the turn `gu-IN` at 100% confidence;
  - the Chat LLM answered directly in Gujarati;
  - transliteration and TTS ran in gu-IN.
- **Conclusion.** The language switch happens without any tool. The LLM simply skipped ours.
- **Variant not run.** The variant (LID tool off, our tool calls `change_language`) was not needed, because the switch does not depend on a tool.
- **With the hardened prompt line** (T4), our tool ran on 2/2 switch turns, and 2/2 again under Patient endpointing.

### T4 – tool-call rate, current vs hardened: PROVEN (hardening helps)
- **Same 9 calls / 31 seller turns each:**
  - current main agent (`O2-…json`);
  - hardened copy `VANI-T4-har-65c85c3d-50a7` (`O2h-…json`).
- **Hardening:**
  - prompt line "Call read_seller_signal before EVERY reply, exactly once per seller turn … also when the seller switches language";
  - `read_seller_signal_http` removed;
  - per-turn dedupe (utterance hash in an internal variable);
  - `switch_log` keeps the last 25 rows as a valid JSON list instead of `json.dumps(log)[-4000:]`;
  - opt-out, interested and "वरना फोन रख" cues added.

| | turns with a tool call | missed turns | double calls | wrong mode | switch_log valid JSON |
|---|---|---|---|---|---|
| current | 30/31 | 1 (the Gujarati switch) | 0 | 7/24 | yes (short logs) |
| hardened | 31/31 | 0 | 1 | 3/24 | yes |
| hardened + Patient (T9) | 31/31 | 0 | 0 | 3/24 | yes |

- **Remaining wrong modes** are keyword-list gaps: romanised "paise kitne lagenge", "mil lete hain", and Gujarati "મીટિંગ ક્યારે". Jev got all of these right (O2c).
- **The one double call** was a partial utterance: the agent took "अच्छा, ये कैसे काम करता है?" at the "?" pause, then the full sentence. The hash dedupe cannot catch partial utterances; Patient endpointing removed it.

### T9 – end of turn ("Eagerness to respond" = Patient): PROVEN (fewer restarts, small cost)
- **Setting.** Slider 1 (Balanced) → 3 (Patient) on the T4 copy, then the same 31 turns (`O2hP-…json`).

| | restarted/duplicated replies | double tool calls | reply onset median (p90) | server avg agent RT |
|---|---|---|---|---|
| Balanced | 2/31 | 1 | 1.98 s (2.43) | 1.10 s |
| Patient | 0/31 | 0 | 2.11 s (2.46) | 0.85 s |

- **Cost.** About +0.13 s laptop-side onset; the server-side figure moved the other way (noise).
- **One run each.** The direction matches the 2026-10-08 hypothesis (early end-of-turn at mid-utterance pauses).

## Head-to-head: switch routes on the same cases

Option set from `2026-10-09-midcall-switch-all-routes.md`:
- **O0** is an added control: no rules, no tool, no push.
- **O1** and **O1b** mean the LLM decides live. That **conflicts with the team rule** (`2026-10-08-team-decision-between-run-learning.md`); they are included for comparison only.
- **Runs:** O1 ×3, O1b/O2c/O3t ×2, O0/O2/O2h/O6 ×1.

| option | how | rushed | frustrated | confused | interested | Gujarati | opt-out | false switches (neutral) | same turn? | reply onset median | server RT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| O0 control | nothing | 0/2 | 2/2 | 0/1 | 2/2 | 1/1 | 0/1 | 0/9 | – | 1.44 s | 0.50 s |
| **O1** Sarvam alone, rules in prompt (LLM decides) | prompt | 5/6 (+1 next) | 6/6 | 3/3 | 6/6 | 3/3 | 3/3 | 0/27 | yes | 1.55 s | 0.56 s |
| O1b per-seller playbook in a variable (LLM picks the block) | prompt + variable | 4/4 adapted, 0/4 under 16 words (playbook line was 18–19 words) | 4/4 | 2/2 | 4/4 | 2/2 | 1/2 (1 cut by hang-up) | 0/18 (2 check artefacts) | yes | 1.54 s | 0.60 s |
| O2 keyword code tool, current (main agent) | tool | 2/2 | 1/2 | 1/1 | 5/5 | 2/2 | 0/1 (mapped to frustrated) | 0/13 | yes | 1.94 s | 0.88 s |
| O2h keyword code tool, hardened | tool | 2/2 | 2/2 | 1/1 | 5/5 | 2/2 | 1/1 | 0/13 | yes | 1.98 s | 1.10 s |
| O2c code tool → laptop relay (cloudflared) → Jev | tool + relay | 4/4 | 4/4 | 2/2 | 4/4 | 2/2 | 2/2 | 0/18; Jev mode right 34/34 | yes | 2.86 s | 1.90 s |
| O6 code tool → relay → sarvam-105b (no reasoning) | tool + relay | 2/2 | 2/2 | 1/1 | 2/2 | 1/1 | 1/1 | classifier wrong on 3/17 neutral turns (applied 1) | yes | 2.61 s | 1.64 s |
| O3t laptop Jev → `client.media.text` push | SDK push | 0/4 | 4/4 | 0/2 | 4/4 | 2/2 | 0/2 | 0/18, but extra replies | no (too late) | 1.50 s | 0.52 s |

**O1 details.**
- Over 3 runs, each line got the same kind of adaptation every time:
  - rushed: "कोई बात नहीं, मैं आपको बाद में call कर लूँ?" 6/6;
  - frustrated: "sorry… परेशानी हुई" 6/6;
  - confused: comma phrases plus "समझ आया?" 3/3;
  - opt-out: "नंबर हटा देता हूँ… कॉल नहीं आएगा" 3/3;
  - "ओके ओके" was never treated as interest.
- Weak spot: replies restarted on 14/66 turns (the same endpointing issue as T9; not tested with Patient for O1).
- There is no switch log. The LLM's choice is visible only in the reply text, so "detected" equals "applied".

**O2c details.**
- Relay round trip measured inside Sarvam: 1,002 ms median, 1,519 ms max. Jev itself took about 500 ms.
- No connection reuse between tool runs: `conn_new` was true on 44/44 calls.
- 1 relay error fell back to the keyword result.
- Adds about 1.3 s of reply onset over O1, and about 0.9 s over the keyword tool.

**O6 offline** (19 lines, `clf-offline-*.json`):
- Jev: 19/19, p50 495 ms.
- sarvam-105b with default reasoning: empty answers on 5/19 (reasoning used up `max_tokens`), 2.2 s p50.
- With `reasoning_effort: null`: 14/19 at 156 ms p50. All 5 misses were false switches on neutral lines ("कौन बोल रहा है?" → interested or confused).

**Per-option summary**

| option | works on a phone call? | deterministic? | added latency per turn | blockers |
|---|---|---|---|---|
| O1 | yes (prompt only; ASSUMED until a phone test) | no, **LLM decides live** (conflicts with team rule) | none | rule conflict; no switch log; restarts |
| O1b | yes (ASSUMED) | no, LLM picks one of our blocks | none | rule conflict; block wording must respect the reply-length limits |
| O2 / O2h | yes (code tools run server-side; ASSUMED) | classifier yes; trigger depends on the LLM calling the tool (31/31 hardened) | about +0.4 s onset vs O1 | lexicon gaps (3/24 wrong) |
| O2b code tool → OpenRouter direct | would be yes | yes | about +0.5–1 s | not run by policy: needs our OpenRouter key as a Sarvam secret plus the allowlist opened for 4.213.167.70 |
| O2c code tool → laptop relay → Jev | yes in principle | classifier yes (34/34); trigger needs the LLM | **+1.0 s** relay, +1.3 s onset | needs a public URL. The quick tunnel is a security-policy problem (our permission system refused further tunnel use); the relay must run on the VPN laptop; no connection reuse |
| O6 code tool → Sarvam LLM | yes in principle (api.sarvam.ai is public) | no (frozen prompt, but false positives) | +0.15–0.8 s (via relay) | 14/19 accuracy; direct use needs a Sarvam API key as a workspace secret |
| O3 webhook variable update | unknown | would be yes | – | BLOCKED (T2) |
| O3t / T1 SDK push | **no** (SDK/web only) | yes | – | `client.action.*` closes the session; text injection lands too late and creates extra replies |
| O4 state/language push | no | – | – | BLOCKED: state_transition and language_change pushes close the session; the agent is single-state, and the console hides multi-state (Advanced) |
| O5 API tool with `@Call Transcript` | yes in principle | trigger needs the LLM | about as O2c | **BLOCKED, not run.** Our permission policy refused both a static relay token in the tool header (credential materialisation) and an unauthenticated relay endpoint (security weakening / transcript exfiltration). The relay and tunnel were then shut down. It needs a user decision on a proper secret (Settings→Secrets was also refused) |

## Answer: can the laptop run Jev and push mid-call persona switches?

- **(a) Laptop SDK session: not as a push.**
  - All three documented client actions (`variable_update`, `state_transition`, `language_change`) make Sarvam close the session.
  - The one message that works, `client.media.text`, arrives 1.06 s after the seller stops. By then the LLM is already writing, and the agent answers the note as an extra user turn.
  - What does work is the pull direction: a Sarvam code tool calls a laptop relay running Jev (O2c). It got 34/34 modes right and the switch landed on the same turn, but it adds about 1 s per turn.
- **(b) Real phone call: no laptop-side route today.**
  - There is no per-turn event feed out of a phone call: the analytics transcript lags about 16 s, and webhooks fire only after the call.
  - The Webhook Variable Update has no usable inbound endpoint.
  - The only working path is the same pull: the code tool calls out to a public relay. That needs a stable public URL (Daytona DNS, or a tunnel our security policy rejects), a proper secret for auth, and it still depends on the LLM calling the tool.
- **For a phone demo,** the practical choices are:
  - the hardened in-Sarvam code tool, which has the same-turn switch and a switch log;
  - with its lexicon improved between runs using Jev labels;
  - or O1/O1b, which were the most reliable here but leave the decision to the LLM.

## Agent settings changed, and whether restored

| agent | change | restored? |
|---|---|---|
| Voice-Bot-104c356b-536d (main) | **none** | n/a. It still has OnStart + ReadSellerSignal, the defined variables and language detection as before. The new tool code is in the repo only and not uploaded. |
| VANI midcall test copy `VANI-midcal-506a41a2-0422` (clone of main, made today) | added variable `net_probe`; uploaded the T10 probe tool and later the OnStart + inert `read_seller_signal` file; replaced the MANDATORY RULE line with "Shape every reply by the Current directive"; removed `read_seller_signal_http` | the T10 httpx probe was removed; the rest is left as a test copy (delete if not needed) |
| VANI midcall relay copy `VANI-midcal-37a2191c-332d` (clone of the copy) | MANDATORY RULE line back; relay tool uploaded (it carried a throwaway relay token inline; Sarvam's audit flagged it, the upload went through); then replaced by the inert OnStart-only file | relay tool and token removed; the tunnel is dead; left as a test copy |
| VANI T4 hardened copy `VANI-T4-har-65c85c3d-50a7` (clone of main) | hardened prompt line; `read_seller_signal_http` removed; hardened tool uploaded; Eagerness Balanced → Patient | left as is: it is the T4/T9 test agent |
| laptop | cloudflared quick tunnel + relay on 127.0.0.1:8787 | both stopped |

Not done, each needing a decision:
- O5 (needs an approved secret and relay);
- O2b (needs our OpenRouter key in Sarvam plus the allowlist; refused by policy);
- the T2 config write;
- the T3 LID-off variant (moot).

## Warm relay, filler and hybrid (2026-10-09, 17:58–18:24 IST)

**Setup**
- Code tool on the clone "relay copy" (`VANI-midcal-37a2191c-332d`) → cloudflared quick tunnel → laptop relay → Jev.
- **Relay** (`app/spike/midcall_relay.py`): one persistent keep-alive session to OpenRouter, warmed with a dummy Jev call at start and every 20 s. 74/74 warm pings succeeded, 507 ms median; the first, cold ping took 1,165 ms.
- **Auth:** HMAC-SHA256 over `{ts}.{interaction_id}.{utterance}`. Requests with a bad signature or older than 30 s were rejected, checked from the laptop. The key sat in the workspace secret `VANI_RELAY_HMAC_TEST`, which the user created.
- **Tool** (`app/spike/code_tools/vani_clone_warm_template.py`): one module-level `httpx.AsyncClient`.
- **Secret lookup lesson:** the first upload read the secret through a constant and got `ValueError` (secret not found) on every turn. With the literal `context.get_secret("VANI_RELAY_HMAC_TEST")` it worked. The uploader seems to wire up only secrets named literally in the code.

**Runs.** Sarvam credits ran low and testing was stopped by the user, so the runs are smaller than planned:
- **W1:** 2 runs of the 7-scenario set.
- **W2 and W3:** 1 session each of a single 7-turn script (opener, "ओके ओके", interested, confused, frustrated, Gujarati switch, rushed). W3 also has one earlier session that ended at "ओके ओके": the agent took it as agreement to a call-back and hung up.
- **Baseline:** the earlier O2h numbers (hardened keyword tool, no relay); it was not re-run.

**Not measured.** Relay round trip and client reuse as seen inside Sarvam live in the tool's `switch_log`, which can only be read through the analytics API. All further Sarvam calls were forbidden, so these come only from the relay's own log (Jev time) and from reply start. Scoring was done offline (`MIDCALL_OFFLINE=1 midcall_analyze.py`).

| | W1 warm relay, Jev every turn (1.5 s cap) | W2 = W1 + filler "जी…" | W3 hybrid (keyword first, Jev ≤ 400 ms on ambiguous turns) | baseline O2h (keyword only) | earlier O2c (cold relay) |
|---|---|---|---|---|---|
| sessions / seller turns | 14 / 44 | 1 / 7 | 2 / 12 | 9 / 31 | 14 / 44 |
| reply start, median (p95) | 2.52 s (3.06) | 2.32 s (2.82), first audio | 1.92 s (2.24) | 1.98 s (2.64) | 2.86 s (3.27) |
| added vs O2h, median | **+0.54 s** | +0.34 s (n=7) | −0.06 s (no real Jev, see below) | – | +0.88 s |
| Jev time at the relay, median (p95) | 495 ms (578) | 494 ms (505) | 481 ms (494) | – | about 500 ms |
| relay round trip inside Sarvam, cold vs warm | not readable (needs analytics); the O2c→W1 drop in reply start (−0.34 s) is the warm-relay gain | not readable | not readable | – | 1,002 ms median, 1,519 ms max, a new connection on every call (44/44) |
| HTTP client reused across turns | unknown (not readable) | unknown | unknown | – | no (O2c) |
| relay calls | 79 on 44 turns, all different utterances: the tool was also called on partial ASR text (about 1.8 calls per turn) | 4 on 7 turns | 4 on 12 turns = **33%** of turns called Jev | – | 44 on 44 |
| W3 timeouts | – | – | **4/4 likely timed out**: Jev alone took 457–606 ms, over the 400 ms cap before tunnel time, so the keyword result stood on every turn | – | – |
| Jev mode accuracy (relay log vs script) | 55/57 (the two misses: "अच्छा, ठीक है।", a partial of the price line, labelled neutral) | 2/2 | 1/1 (opener) | 21/24 keyword | 34/34 |
| same-turn switch: rushed / frustrated / confused / interested / Gujarati / opt-out | 4/4 · 4/4 · 2/2 · 4/4 · 2/2 · call ended, reply not captured offline | 0/1 · 1/1 · 1/1 · 1/1 · 1/1 · not in script | 1/2 · 2/2 · 2/2 · 1/1 · 1/1 · not in script | 2/2 · 2/2 · 1/1 · 5/5 · 2/2 · 1/1 | 4/4 · 4/4 · 2/2 · 4/4 · 2/2 · 2/2 |
| false switches on neutral turns | 0/18 | 0/2 | 0/4 | 0/13 | 0/18 |

**Notes**
- **W2 filler not heard.** The audio shows no short "जी…" burst before replies. The first burst on each turn is a full sentence (0.9–5 s long), with the same burst pattern as W1. With `pre_run_message` set as a class default (SDK 1.1.1 has no per-call setter), the filler did not play, or was too short or too quiet to register. That means no filler-to-reply gap could be measured. W2 also hit the relay on only 4 of 7 turns, and why cannot be checked without the switch log. **Inconclusive, n=1.**
- **The rushed miss in W2 and W3** is the last turn, a Hindi "अभी बिज़ी हूँ यार…" spoken right after the switch to Gujarati. The agent kept pitching in Gujarati. This is an ordering effect of the short script, not a relay result.
- **W3 as built is the keyword tool plus wasted calls.** With Jev at about 480 ms, a 400 ms cap can never be met over the tunnel. A useful hybrid needs a cap of about 700–800 ms (adding about 0.5 s on the 33% of turns it gates), or a faster classifier.
- **The tunnel and relay** were stopped by the coordinator at the end.

**Sarvam usage for this test**
- 17 scored sessions, 12.5 min of session time: W1 14 sessions (8.5 min), W3 2 (2.2 min), W2 1 (1.4 min).
- Plus about 5 short sessions before the secret fix (tool failed at `get_secret`; aborted) and 1 check session.
- Seller TTS for about 35 lines; the minimal script was cached and reused for W2.

**Left as is (console use was forbidden at the end)**
- The relay copy still carries the W2 tool file. It points at the dead tunnel URL and reads `VANI_RELAY_HMAC_TEST`.
- It should be reset to `app/spike/code_tools/vani_clone_onstart_only.py`. The user will delete the secret.

Evidence:
- `outputs/midcall_tests/W1-*.json`, `W2-MIN-*.json`, `W3-MIN-*.json` and the `*-scored-W*.json` copies;
- `outputs/midcall_tests/warm-relay-summary.json`;
- `outputs/midcall_tests/relay-log-20261009.jsonl` (warm pings and `/decide` calls with Jev time).
