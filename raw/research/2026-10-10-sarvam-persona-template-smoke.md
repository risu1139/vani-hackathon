# Sarvam persona template: build, clone setup and smoke test (2026-10-10)

Build of the Sarvam side of the VANI persona system (plan `outputs/plans/persona-e2e-plan.md` §2, §3, §9; review findings B3, B5, M1–M7, M16, m5, m6). Code: `app/sarvam/`. Contract: `app/contracts/sarvam_vars.contract.json` (unchanged).

**Live smoke test (step 5): DEFERRED.** The user ruled that no test may use the main Sarvam key or org (low credits). The only allowed key, `SARVAM_STT_API_KEY`, returned HTTP 402 "No credits available" earlier the same day. So no agent SDK session, TTS, STT or analytics call ran. **Sarvam usage for this work: 0 sessions, 0 minutes, 0 TTS/STT calls.**

## What was built

| File | What it does |
|---|---|
| `app/sarvam/vani_prompt.md` | Global prompt, Ananya-style sections: Persona, Environment, Objective, Speaking Style, Facts, Phases, Live adaptation, Guardrails, Date resolution. The first line makes `read_seller_signal` mandatory before every reply. Only `@variable` placeholders from the contract (11 of them); division text comes through `division_block`, with no Jinja (M5). Identity rules from `raw/hackathon/2026-10-10-team-decision-vani-identity-line.md`: never volunteer AI, sidestep once, "virtual assistant" if pressed, never claim to be human, no branch/account manager, no "personally". Numbers only from `verified_facts`; no buyer identity; no package price. Escalation: DND/opt-out → end; hostile → short; legal → close. |
| `app/sarvam/vani_tools.py` | `OnStart`: voice, pace (clamped 0.85–1.25), pitch (clamped −0.3–0.3), `set_initial_language_name` from `persona_language` (M6), opening from `persona_opening`. `ReadSellerSignal` (`read_seller_signal`): see below. `BookMeeting` (`book_meeting`): sets `meeting_fixed=yes` and `meeting_slot`, returns a confirmation text, and refuses when the slot is empty (M16). |
| `app/sarvam/collect_call.py` | `--interaction-id X` or `--since T`. Pulls interactions from the Analytics API (`X-API-Key` = agents key), plus `/transcripts/{id}`. Writes `data/runs/<decision_id>/06_call.json` (metadata, audio_url, transcript, agent_variables, parsed switch_log) and `07_outcome.json` (meeting_fixed, slot, ended_by, opted_out; `meeting_held` = null, future work). Tested offline only. |
| `app/sarvam/tests/` | 150 pytest cases, all pass, no network. |
| `app/sarvam/agent.json` | Clone app id and settings (no secrets). |
| `app/sarvam/smoke_vars.example.json` | Hand-filled persona for the deferred smoke test. It is a made-up seller: female voice (Aarti), Gujarati start, style P2, NSD block. |

### read_seller_signal: what changed from the 2026-10-09 hardened tool
- **Signals:** rushed, frustrated, confused, interested, bot_question, opt_out, language_switch. Opt-out ends the call: `set_end_conversation()` plus a fixed apology line in the current language through `message_to_user`.
- **Classifier:** a strong cue beats a weak cue, then priority runs opt_out > frustrated > bot_question > rushed > confused > interested. It returns the matched cue (M1).
- **Interest is strict.** Bare ok, haan, hmm, achha or "theek hai" never count. "nahi chahiye" cancels an interest cue.
- **Normalisation:** NFD; nukta, anusvara and chandrabindu are dropped (Devanagari and Gujarati), so बिज़ी = बिजी and नहीं = नही. Romanised variants are mapped (nahin/nhi → nahi, mein → me, hoon → hu). Latin cues match whole words.
- **Lexicon v1 (`lex-v1-20261010`, M3).** Sources:
  - the 2026-10-09 test set;
  - the Jev-labelled ASR variants from the O2c/W1 relay log, for example "अबे बिजी", "एग्जैक्ट प्राइस … कितने का प्लान", "कैसे बोलिए" (weak confused);
  - the three T4 gaps: "paise kitne lagenge", "mil lete hain", "મીટિંગ ક્યારે";
  - frequent PS07 seller n-grams (counts only, 64,625 seller turns), e.g. "abhi nahi" 1,023, "baad mein" 870, "time nahi" 603, "busy hoon" 449, "baar baar" 130, "call mat" 76, "phone mat" 55, "aap insaan" 14, "aap robot" 12.
- **PS07 lessons encoded:**
  - "samajh gaya" and "matlab nahi hai" are not confusion;
  - "finished recording" is voicemail, not a bot question;
  - "machine" alone is usually the seller's product, so only "aap machine ho" / "machine se baat" count;
  - "abhi call mat karo, shaam ko karna" is a callback (rushed), not an opt-out.
- **Language switch:** detected when the dominant script changes from the last seller turn, or from the persona's start language at the first turn. Latin counts only with at least 3 words and at least 70% Latin letters. The tool calls `change_language` when the target language is allowed. A language note is added to any other mode.
- **Sensitivity (M4).** Per signal, from `switch_sensitivity` JSON:
  - **high:** the first cue switches;
  - **normal:** a strong cue switches at once, and a weak cue needs a second cue of the same signal within 3 turns;
  - **low:** every cue needs a second cue.

  opt_out, frustrated and bot_question always switch at once.
- **Directives (M4).**
  - **Variants:** each mode has variants keyed by `persona_style_id` (P0–P6 from `.claude/skills/vani-persona/references/persona_library.json`; COMPOSED or unknown → base). Every variant states a hard "Max N words".
  - **Caps:** rushed ≤ 12 (P3/P4: 10); frustrated ≤ 18; confused ≤ 20; interested ≤ 20 (P4: 12); neutral = the style's words per turn.
  - **Bot question:** it has two steps. The first sidesteps; the second gives the "virtual assistant" line and offers a human callback.
- **switch_log rows (M1):** {t, turn, utt, lang, script, from, to, cue [strength], directive_id, change, reason, sens, dup, ms, decision_id, lex}. The last 25 rows are kept as valid JSON, and the per-utterance hash dedupe is kept. switch_log is never in `message_to_llm`, and "Include in context" is off for it (m5).

## Offline results (no credits)
- **pytest: 150/150 pass.** The suite covers:
  - 23 gold lines and 18 neutral lines (fillers, "samajh gaya", "matlab nahi hai", "CNC machine", the voicemail line, the Gujarati "સારું, આગળ બોલો");
  - sensitivity rules;
  - every directive variant × 10 style ids (cap ≤ mode limit, "Max N words" present, ≤ 45 words, no banned words, AI only as a prohibition);
  - the tools on a fake SDK context: row fields, the weak-cue wait, dedupe, 25-row cap, bot sidestep → pressed, Gujarati script switch with `change_language`, the Gujarati start then Hindi reply, opt-out ending the call, book_meeting, OnStart language/clamp, only contract variables used;
  - collect_call build/write.
- **Re-score on the recorded 2026-10-09 ASR text** (87 unique seller utterances from `outputs/midcall_tests/*-scored-*.json`, Gujarati switch lines excluded): 76 agree with the scripted label. The 11 differences:
  - 6 are ASR fragments or bare fillers, which strict interest correctly leaves neutral ("अच्छा।", "सारुं.", "अच्छा हाँ, याद आया।", "अच्छा ठीक है, पर एग्जैक्ट।", "अच्छा, ठीक है।", "સારું બલ્ક બાયર્સ જોઈએ છે.");
  - 2 are the scripted "neutral" slot acceptances "कल शाम 5 बजे आ जाइए", which the tool labels interested (acceptable: the reply moves to the slot);
  - 2 are the fragment "फिर से पूछ रहा हूँ" without its "वरना फोन रख दो" tail;
  - 1 is the weak cue "कैसे बोलिए?", which does not switch under normal sensitivity.

  Against the T4 baseline (3/24 wrong modes), all three T4 gaps are now fixed. A fresh gold set (M17) is still needed for a held-out score.

## Clone setup (console; configuration only, no credits)
- **Clone:** "VANI persona demo", app id **`VANI-person-b8c173ff-b272`**, v1 draft. It is a clone of "Voice Bot" (`Voice-Bot-104c356b-536d`); the main agent was not edited.
- **Variables:** all 23 contract variables are defined (18 set before the call + 5 set by tools). Defaults: `persona_style_id`=COMPOSED, `switch_sensitivity`={}, `meeting_fixed`=no, `switch_log`=[], `seller_mode`=neutral. The legacy `user_name` was kept. "Include in context" is off for `switch_log` and `switch_sensitivity` (and was toggled for `decision_id`; not re-checked).
- **Instructions:** `vani_prompt.md` replaced the old prompt.
  - The console editor is Tiptap. Variables are `mention` nodes (`{id, label, mentionSuggestionChar:"@", kind:"value"}`), so the prompt was set as editor JSON with 11 mention nodes.
  - After a reload, it persisted: 3,824 characters, 11 mentions.
  - The Greeting field still holds the old masculine fallback line, which OnStart overrides when `persona_opening` is set.
- **Tools:** `vani_tools.py` was uploaded; it replaces all Python tools.
  - The first upload's audit flagged 2 × "getattr() with dynamic attr name". Both were removed and the file was re-uploaded. Audit passed: Book Meeting + Read Seller Signal (During call · Python); OnStart is not listed, as before.
  - There is no HTTP tool on the clone.
- **Settings:**
  - Eagerness to respond: Balanced → **Patient** (persisted after a reload);
  - language switch during the call and auto-detected switch: on;
  - 11 languages allowed, including Gujarati; starting language Hindi (OnStart overrides it).
  - **"Per-language voices" turned OFF** (user rule: persona config goes through the SDK code tools only). It was inherited from the main agent (Hindi/Bengali → Shubh) and could compete with OnStart. Turning it off persisted after the page was reloaded.
  - Voice, pace, pitch and starting language come only from `OnStart` reading `persona_voice_id`, `persona_pace`, `persona_pitch` and `persona_language`. The UI values left in place (default voice Shubh, speed 1.15, pitch 0, starting language Hindi) are only the fallback when those variables are empty.

## Deferred live checks (run when credits exist; ≤ 4 SDK sessions planned, about 1 min each)
Use `smoke_vars.example.json` as the agent_variables, then pull the result with `python app/sarvam/collect_call.py --interaction-id <id>`.

| # | Check | Pass criterion | Status |
|---|---|---|---|
| a | Every variable read back in analytics `agent_variables` | all 23 keys present; inputs equal the sent values | DEFERRED |
| b | Voice and language start | female F0 (> 200 Hz); opening spoken in Gujarati; first reply in Gujarati | DEFERRED |
| c | Scripted rushed line and confused line | each switches on the same turn; switch_log rows have cue + reason + directive_id | DEFERRED |
| d | "aap bot ho?" | sidestep reply with no "AI"/"bot"; a second ask → "virtual assistant" | DEFERRED |
| e | book_meeting | after "kal shaam 5 baje theek hai", `meeting_fixed=yes` and the slot is set in analytics | DEFERRED |
| f | Reply-start latency | median ≤ 2.1 s (M22) | DEFERRED |
| g | (extra) opt-out end | the fixed line is spoken, then the call ends | DEFERRED |

Open risks to watch in the live run:
- whether `@persona_opening` and the other long variables render inside the prompt (the 2026-10-09 test proved `@call_plan` only);
- whether internal variables set in OnStart (`start_script`) reach the during-call tool (the tool falls back to `persona_language`);
- whether `message_to_user` + `set_end_conversation` speaks before hanging up;
- whether `change_language` conflicts with Sarvam's own language detection;
- STT round trip of the Gujarati opening (M7).
