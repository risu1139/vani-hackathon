"""Plan stress spike: off-plan sellers, plan delivery route, and the double-tool-call / restarted-reply question.

Conditions:
  P = plan in initial agent_variables AND prefixed by the signal server to every per-turn directive
  V = plan ONLY in initial agent_variables (server returns plain directives, which overwrite persona_directive)
Scenarios use made-up sellers. Per turn we log: tool calls (time, utterance), agent speech onset, reply text,
regex checks, and whether the reply restarts itself.

Usage: python app/spike/plan_stress.py --runs 2 --conds P,V --scen A_hostile,B_gujarati,A_coop
"""
import argparse
import array
import asyncio
import base64
import io
import json
import os
import re
import time
import wave

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

from call_spike import ROOT, SPEECH_RMS, SR, Line, server_log
from plan_spike import SELLERS, set_plan

NO_PRICE = r"\d|₹|rupay|रुपये|रुपए|हज़ार|हजार|लाख|રૂપિયા|હજાર"
SCEN = {
    "A_coop": ("A", [(t, "hi-IN", n, m, x) for t, n, m, x in SELLERS["A"]["turns"]]),
    "A_hostile": ("A", [
        ("Pehle yeh batao aap kaun ho aur kahan se bol rahe ho?", "hi-IN", "offplan_answer_and_return",
         r"indiamart|इंडिया ?मार्ट|इंडियामार्ट", None),
        ("Main owner nahi hoon, manager hoon. Owner bahar gaye hain.", "hi-IN", "not_owner_adapts",
         r"owner|ओनर|मालिक|कब|kab|बाद|baad|call|कॉल|आप(से)? ही|manager|मैनेजर", None),
        ("Achha theek hai, par exact price batao, kitne ka plan hai?", "hi-IN", "price_no_amount",
         r"meeting|मीटिंग|executive|एग्जीक्यूटिव|एक्सीक्यूटिव|मिल", NO_PRICE),
        ("Phir se pooch raha hoon, price batao warna phone rakh do.", "hi-IN", "price_again_no_amount", r".", NO_PRICE),
        ("Abhi busy hoon yaar, baad mein baat karte hain.", "hi-IN", "rush_short_callback",
         r"बाद|baad|call|कॉल|समय|time|कब|kab|बजे", None),
    ]),
    "B_gujarati": ("B", [
        ("Leads ki zarurat nahi hai, pehle se bahut aa rahi hain.", "hi-IN", "early_objection_playbook",
         r"quality|क्वालिटी|बेहतर|अच्छे|सही|bulk|बल्क|बड़े|serious|सीरियस", None),
        ("Aur aapka plan mehnga bhi hai.", "hi-IN", "price_no_amount",
         r"meeting|मीटिंग|executive|एग्जीक्यूटिव|मिल", NO_PRICE),
        ("ગુજરાતીમાં વાત કરો ને, મને હિન્દી ઓછું ફાવે છે.", "gu-IN", "switch_to_gujarati", r"[઀-૿]", None),
        ("સારું, બલ્ક બાયર્સ જોઈએ છે. મીટિંગ ક્યારે કરશો?", "gu-IN", "meeting_time_in_gujarati",
         r"[઀-૿].*(મીટિંગ|સમય|ક્યારે|વાગ્યે|દિવસ|meeting)", None),
        ("કાલે સવારે દસ વાગ્યે.", "gu-IN", "confirm_in_gujarati", r"[઀-૿].*(આભાર|ધન્યવાદ|દસ|10|કાલે)", None),
    ]),
}


def tts(text, lang, speaker="rahul"):
    r = requests.post("https://api.sarvam.ai/text-to-speech", timeout=60,
                      headers={"api-subscription-key": os.environ["SARVAM_API_KEY"]},
                      json={"text": text, "target_language_code": lang, "model": "bulbul:v3",
                            "speaker": speaker, "speech_sample_rate": SR})
    r.raise_for_status()
    with wave.open(io.BytesIO(base64.b64decode(r.json()["audios"][0]))) as w:
        return w.readframes(w.getnframes())


def restarts(reply):
    """True if the reply visibly restarts: an early 1-3 word phrase repeats shortly after."""
    w = re.findall(r"\w+", reply)
    for n in (3, 2):
        for i in range(0, min(4, len(w) - n)):
            g = w[i:i + n]
            for j in range(i + n, min(i + n + 12, len(w) - n + 1)):
                if w[j:j + n] == g and not all(x in ("जी", "है", "हैं", "के", "की", "का") for x in g):
                    return True
    return False


async def run_call(scen, cond, idx, audio):
    key, turns = SCEN[scen]
    s = SELLERS[key]
    set_plan(s["plan"] if cond == "P" else "")
    events, onsets = [], []
    state = {"last": 0.0, "speaking": False}

    async def on_audio(msg):
        pcm = array.array("h", base64.b64decode(msg.audio_base64 or ""))
        loud = bool(pcm) and (sum(x * x for x in pcm) / len(pcm)) ** 0.5 > SPEECH_RMS
        now = time.time()
        if loud:
            if now - state["last"] > 0.6:
                onsets.append(now)  # new burst of agent speech
            state["last"] = now

    async def on_transcript(msg):
        events.append((time.time(), str(getattr(msg.role, "value", msg.role)), msg.content))

    cfg = InteractionConfig(
        org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"],
        app_id=os.environ["SARVAM_AGENT_APP_ID"], version=1, interaction_type=InteractionType.CALL,
        user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"stress-{scen}-{cond}-{int(time.time())}-{idx}",
        sample_rate=SR, initial_bot_message=s["opening"],
        agent_variables={"seller_mode": "neutral", "persona_directive": s["plan"] + " | Right now: Continue normally."})
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              audio_callback=on_audio, transcript_callback=on_transcript)
    await agent.start()
    await agent.wait_for_connect()
    line = Line(agent)
    streamer = asyncio.create_task(line.run())

    async def wait_done(after, timeout=30, quiet=1.8):
        t0, first = time.time(), None
        while time.time() - t0 < timeout and agent.is_connected():
            if state["last"] > after and first is None:
                first = state["last"]
            if first and time.time() - state["last"] > quiet:
                return first
            await asyncio.sleep(0.05)
        return first

    t_start = time.time()
    await wait_done(t_start - 1, timeout=20)
    marks, ends = [time.time()], []
    for pcm in audio:
        if not agent.is_connected():
            break
        line.speaking_until = 0
        line.queue.put_nowait(pcm)
        while line.speaking_until == 0 and agent.is_connected():
            await asyncio.sleep(0.02)
        ends.append(line.speaking_until)
        await wait_done(line.speaking_until)
        marks.append(time.time())
    await asyncio.sleep(1)
    await agent.stop()
    streamer.cancel()

    log = [e for e in server_log(400) if e["ts"] >= t_start - 1]
    out = {"scen": scen, "cond": cond, "run": idx, "turns": [], "ended_early": len(marks) - 1 < len(turns)}
    for k, (text, lang, name, must, must_not) in enumerate(turns):
        if k + 1 >= len(marks):
            out["turns"].append({"check": name, "seller": text, "reply": "", "pass": False, "note": "call ended"})
            continue
        a, b = marks[k] + 0.3, marks[k + 1] + 0.3
        reply = " ".join(c for ts, r, c in events if "user" not in r.lower() and a <= ts < b)
        heard = [c for ts, r, c in events if "user" in r.lower() and a <= ts < b]
        hits = [e for e in log if a <= e["ts"] < b]
        on = [round(o - ends[k], 2) for o in onsets if ends[k] - 0.5 <= o < b]
        ok = bool(re.search(must, reply, re.I | re.S)) and not (must_not and re.search(must_not, reply, re.I))
        out["turns"].append({
            "check": name, "seller": text, "reply": reply, "pass": ok, "words": len(reply.split()),
            "restart": restarts(reply), "asr_events": heard,
            "tool": [{"t": round(h["ts"] - ends[k], 2), "utt": h["body"].get("seller_utterance"), "mode": h.get("mode")}
                     for h in hits],
            "speech_onsets": on})
    return out


async def main(runs, conds, scens):
    res = []
    for scen in scens:
        audio = [tts(t, lang) for t, lang, *_ in SCEN[scen][1]]
        for cond in conds:
            for i in range(runs):
                r = await run_call(scen, cond, i, audio)
                res.append(r)
                print(f"\n=== {scen} cond={cond} run={i}{' (ENDED EARLY)' if r['ended_early'] else ''}")
                for t in r["turns"]:
                    print(f"  [{'PASS' if t['pass'] else 'FAIL'}] {t['check']:<26} w={t.get('words')} "
                          f"restart={t.get('restart')} tools={[(x['t'], x['mode']) for x in t.get('tool', [])]} "
                          f"onsets={t.get('speech_onsets')}\n      reply: {t['reply'][:170]}")
                await asyncio.sleep(2)
    set_plan("")
    path = ROOT / "outputs" / f"spike-plan-stress-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nSaved {path.name}")
    for cond in conds:
        ts = [t for r in res if r["cond"] == cond for t in r["turns"]]
        print(f"cond {cond}: checks {sum(t['pass'] for t in ts)}/{len(ts)}, restarts {sum(bool(t.get('restart')) for t in ts)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--conds", default="P,V")
    ap.add_argument("--scen", default="A_hostile,B_gujarati,A_coop")
    a = ap.parse_args()
    asyncio.run(main(a.runs, a.conds.split(","), a.scen.split(",")))
