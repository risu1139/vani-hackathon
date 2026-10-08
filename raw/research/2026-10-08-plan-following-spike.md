# Spike: does the Sarvam agent follow a per-call conversation plan? (2026-10-08)

Code: `app/spike/plan_spike.py` (+ `/plan` endpoint in `app/signal_server/main.py`). Results JSON: `outputs/spike-plan-20261008-035005.json`. Sellers are made up (no PS07 data).

## Setup
- Sarvam agent Voice-Bot v1 (draft), SDK CALL mode, simulated seller = Sarvam TTS (bulbul:v3, hi-IN), scripted 4 turns.
- Per call we passed: `initial_bot_message` (scripted personalised opening), `agent_variables.persona_directive` = call plan (4 ordered steps + personalisation facts + objection playbook order + "never quote price/invent facts").
- The signal server held the active plan and prefixed it to every per-turn directive ("<plan> | Right now: <mode directive>"), because the tool response overwrites `persona_directive` each turn.
- 2 sellers × 2 runs = 4 calls, 16 plan checks (regex on the agent's reply per turn) + 1 extra call to verify the opening by recording greeting audio and transcribing it (saarika:v2.5).

## Results
- Plan checks passed 15/16.
  - Step 2 personalisation (seller-specific facts from the plan: "last week you asked us to call back about more PVC buyers in Indore"; "last time you said you get enough leads — bulk or retail?") 4/4.
  - Objection playbook 4/4: price objection → "executive will explain all options in the meeting" + meeting ask, no amount quoted (0 digits/price words); "already have leads" → "not more leads, better quality buyers" + meeting.
  - Step 3 (meeting/time) 3/4. The one fail: after the playbook reply had already asked for the meeting, the agent re-asked for the meeting instead of asking for a time (repeat, not skip/out-of-order).
  - Step 4 confirm + thanks 4/4, with the seller's stated time echoed back.
- Opening: the transcript callback does not emit the initial bot message (so the automated check read 0/4). Recorded audio of the greeting, transcribed: "नमस्ते, मैं इंडिया मार्ट से बोल रहा हूँ। क्या मेरी बात श्री गणेश पाइप्स के ओनर से हो रही है?" = the scripted opening, verbatim. In all 4 calls the seller's ASR'd reply and the agent's step 2 are consistent with the opening having been spoken.
- Tool called 6–7 times per call (4 seller turns; partial + full utterances again).
- Artifacts: two replies contained a restarted phrase ("देखिए, इसके सारे options के देखिए, ...") — likely the partial-then-full double tool call; worth checking in T2.
- Caveats: n=4 calls, cooperative scripted seller, same seller lines per run; plan delivered via the server prefix (real design: plan via agent_variables at start + server keyed by call).
