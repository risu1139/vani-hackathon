"""Plan spike: does the Sarvam agent follow a per-call conversation plan we pass in?

For two made-up sellers (no real data) we pass a scripted opening (initial_bot_message), and a plan
(steps in order + objection playbook order + personalisation facts) via agent_variables persona_directive.
The signal server keeps the plan in front of every per-turn directive. A simulated seller (Sarvam TTS)
replies; per turn we check the agent's reply against what the plan says should happen at that step.

Usage: python app/spike/plan_spike.py [--runs N]
"""
import argparse
import array
import asyncio
import base64
import json
import os
import re
import time

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

from call_spike import ROOT, SPEECH_RMS, SR, Line, server_log, tts_pcm

RULES = "Follow the steps in order, one step per reply, short replies. Never quote any price or amount, never invent facts."
SELLERS = {
    "A": {
        "opening": "Namaste! Main IndiaMART se bol raha hoon. Kya meri baat Shree Ganesh Pipes ke owner se ho rahi hai?",
        "plan": ("CALL PLAN for Shree Ganesh Pipes (PVC pipes, Indore). " + RULES +
                 " Step 1: confirm you are speaking with the owner. Step 2: remind them they asked us last week to call back"
                 " about getting more PVC pipe buyers in Indore. Step 3: ask for a 15-minute meeting with a local IndiaMART"
                 " executive. Step 4: confirm the day and time, thank them, end. OBJECTION PLAYBOOK in this order:"
                 " (1) price or cost: say the executive will explain all options in the meeting, mention no amount, go to Step 3;"
                 " (2) not interested: ask what kind of buyers they want, then Step 3."),
        # (seller line, check name, regex the agent's reply must match, regex it must NOT match)
        "turns": [
            ("Haan ji, main hi owner hoon. Boliye.", "step2_personalised",
             r"pvc|पीवीसी|indore|इंदौर|call ?back|कॉल ?बैक|पिछले|pichhle|बात हुई", None),
            ("Achha haan yaad aaya. Par paise kitne lagenge? Aapka plan bahut mehnga hai.", "playbook_price",
             r"meeting|मीटिंग|executive|एग्जीक्यूटिव|एक्सीक्यूटिव|मिल", r"\d|₹|rupay|रुपये|रुपए|हज़ार|हजार|लाख"),
            ("Theek hai, mil lete hain.", "step3_ask_time", r"समय|time|kab|कब|baje|बजे|दिन|din", None),
            ("Kal shaam paanch baje aa jaiye.", "step4_confirm", r"धन्यवाद|shukriya|thank|शुक्रिया|कल|पांच|पाँच|5", None),
        ],
    },
    "B": {
        "opening": "Namaste! IndiaMART se baat kar raha hoon. Kya yeh Kaveri Textiles hai?",
        "plan": ("CALL PLAN for Kaveri Textiles (cotton sarees, Surat). " + RULES +
                 " Step 1: confirm it is Kaveri Textiles. Step 2: acknowledge that last time they said they already get"
                 " enough leads, and ask what kind of buyers they want more of, bulk or retail. Step 3: offer a meeting to"
                 " show how to get more bulk buyers. Step 4: confirm the day and time, thank them, end. OBJECTION PLAYBOOK"
                 " in this order: (1) already have enough leads: talk about better quality buyers, not more leads, then"
                 " Step 3; (2) price or cost: say the executive will explain options in the meeting, mention no amount."),
        "turns": [
            ("Haan, Kaveri Textiles. Boliye.", "step2_personalised",
             r"leads?|लीड|bulk|बल्क|retail|रिटेल|खरीदार|buyer|बायर", None),
            ("Leads toh pehle se bahut aa rahi hain, zarurat nahi hai.", "playbook_leads",
             r"quality|क्वालिटी|अच्छे|achhe|सही|bulk|बल्क|बड़े|serious|सीरियस", r"\d|₹|rupay|रुपये|रुपए"),
            ("Haan bulk buyers chahiye actually.", "step3_meeting", r"meeting|मीटिंग|मिल|executive|एग्जीक्यूटिव|समय|kab|कब", None),
            ("Parso subah das baje theek rahega.", "step4_confirm", r"धन्यवाद|shukriya|thank|शुक्रिया|परसों|दस|10", None),
        ],
    },
}


def set_plan(text):
    requests.post(os.environ["SIGNAL_SERVER_URL"] + "/plan", json={"plan": text}, timeout=20,
                  headers={"x-signal-token": os.environ["SIGNAL_TOKEN"]}).raise_for_status()


async def run_once(key, idx, audio):
    s = SELLERS[key]
    set_plan(s["plan"])
    events, last = [], {"t": 0.0}

    async def on_audio(msg):
        pcm = array.array("h", base64.b64decode(msg.audio_base64 or ""))
        if pcm and (sum(x * x for x in pcm) / len(pcm)) ** 0.5 > SPEECH_RMS:
            last["t"] = time.time()

    async def on_transcript(msg):
        events.append((time.time(), str(getattr(msg.role, "value", msg.role)), msg.content))

    cfg = InteractionConfig(
        org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"],
        app_id=os.environ["SARVAM_AGENT_APP_ID"], version=1, interaction_type=InteractionType.CALL,
        user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"plan-{key}-{int(time.time())}-{idx}",
        sample_rate=SR, initial_bot_message=s["opening"],
        agent_variables={"seller_mode": "neutral", "persona_directive": s["plan"] + " | Right now: Continue normally."})
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              audio_callback=on_audio, transcript_callback=on_transcript)
    await agent.start()
    await agent.wait_for_connect()
    line = Line(agent)
    streamer = asyncio.create_task(line.run())

    async def wait_done(after, timeout=30, quiet=1.6):
        t0, first = time.time(), None
        while time.time() - t0 < timeout and agent.is_connected():
            if last["t"] > after and first is None:
                first = last["t"]
            if first and time.time() - last["t"] > quiet:
                return first
            await asyncio.sleep(0.05)
        return first

    t_start = time.time()
    await wait_done(t_start - 1, timeout=20)
    marks = [time.time()]
    for pcm in audio:
        if not agent.is_connected():
            break
        line.speaking_until = 0
        line.queue.put_nowait(pcm)
        while line.speaking_until == 0 and agent.is_connected():
            await asyncio.sleep(0.02)
        await wait_done(line.speaking_until)
        marks.append(time.time())
    await asyncio.sleep(1)
    await agent.stop()
    streamer.cancel()

    def said(a, b):
        return " ".join(c for ts, r, c in events if "user" not in r.lower() and a <= ts < b)

    opening = said(0, marks[0] + 0.5)
    res = {"seller": key, "run": idx, "opening_said": opening,
           "opening_exact": s["opening"].split("!")[0].lower() in opening.lower() or "shree ganesh" in opening.lower()
           or "kaveri" in opening.lower() or "गणेश" in opening or "कावेरी" in opening, "turns": []}
    for k, (text, name, must, must_not) in enumerate(s["turns"]):
        reply = said(marks[k] + 0.5, marks[k + 1] + 0.5) if k + 1 < len(marks) else ""
        ok = bool(re.search(must, reply, re.I)) and not (must_not and re.search(must_not, reply, re.I))
        res["turns"].append({"check": name, "seller": text, "reply": reply, "pass": ok})
    log = [e for e in server_log() if e["ts"] >= t_start - 1]
    res["tool_calls"] = len(log)
    res["events"] = [(round(ts - t_start, 2), r, c) for ts, r, c in events]
    return res


async def main(runs):
    out = []
    for key in SELLERS:
        audio = [tts_pcm(t) for t, *_ in SELLERS[key]["turns"]]
        for i in range(runs):
            r = await run_once(key, i, audio)
            out.append(r)
            print(f"\n=== seller {key} run {i} | tool calls {r['tool_calls']} | opening ok={r['opening_exact']}: {r['opening_said'][:120]}")
            for t in r["turns"]:
                print(f"  [{'PASS' if t['pass'] else 'FAIL'}] {t['check']:<20} reply: {t['reply'][:160]}")
            await asyncio.sleep(2)
    set_plan("")
    path = ROOT / "outputs" / f"spike-plan-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(r["turns"]) for r in out)
    p = sum(t["pass"] for r in out for t in r["turns"])
    print(f"\nPlan checks passed {p}/{n}; openings ok {sum(r['opening_exact'] for r in out)}/{len(out)}. Saved {path.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    asyncio.run(main(ap.parse_args().runs))
