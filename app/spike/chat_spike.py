"""Spikes 2+3 in CHAT mode: does the agent call read_seller_signal every turn, and does the returned
directive change the reply? Sends scripted seller turns, records replies + latency, then joins the
signal-server log to see which turns triggered a tool call.

Usage: python app/spike/chat_spike.py [--runs N]
"""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

ROOT = Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

SCRIPT = [  # (seller turn, expected stub mode)
    ("Haan boliye, kaun bol raha hai?", "neutral"),
    ("Achha IndiaMART se. Kya kaam hai?", "neutral"),
    ("Abhi busy hoon yaar, jaldi bolo kya hai", "rushed"),
    ("Samajh nahi aaya, kya matlab meeting?", "confused"),
    ("Aap bot ho kya? Recorded call hai?", "bot_question"),
    ("Theek hai, kal 11 baje aa jaiye", "neutral"),
]


def server_log(n=200):
    r = requests.get(os.environ["SIGNAL_SERVER_URL"] + f"/log?n={n}",
                     headers={"x-signal-token": os.environ["SIGNAL_TOKEN"]}, timeout=20)
    return r.json()


async def run_once(idx):
    replies, cur, done = [], [], asyncio.Event()

    async def on_text(msg):
        if getattr(msg, "status", None) is None or type(msg).__name__ == "ServerTextMsg":
            cur.append(msg.text)
            done.set()
        else:
            cur.append(msg.text)
            if str(getattr(msg, "status", "")).lower().endswith("complete"):
                done.set()

    transcript = []

    async def on_transcript(msg):
        transcript.append((round(time.time(), 2), str(msg.role), msg.content))

    cfg = InteractionConfig(
        org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"],
        app_id=os.environ["SARVAM_AGENT_APP_ID"], interaction_type=InteractionType.CHAT,
        user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"spike-{int(time.time())}-{idx}",
        sample_rate=16000)
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ.get("SARVAM_AGENTS_API_KEY") or os.environ["SARVAM_API_KEY"]), config=cfg,
                              text_callback=on_text, transcript_callback=on_transcript)
    await agent.start()
    await agent.wait_for_connect()
    await asyncio.sleep(4)  # greeting
    greeting = " ".join(cur); cur.clear()
    t_start = time.time()
    for turn, expected in SCRIPT:
        done.clear(); cur.clear()
        t0 = time.time()
        agent.send_text(turn)
        try:
            await asyncio.wait_for(done.wait(), timeout=25)
            await asyncio.sleep(1.5)  # let chunks finish
        except asyncio.TimeoutError:
            pass
        replies.append({"seller": turn, "expected": expected, "t_sent": t0,
                        "first_reply_s": None, "reply": " ".join(cur).strip()})
    await agent.stop()
    return {"interaction_id": agent.get_interaction_id(), "greeting": greeting, "t_start": t_start,
            "turns": replies, "transcript": transcript}


async def main(runs):
    out = []
    for i in range(runs):
        res = await run_once(i)
        await asyncio.sleep(2)
        log = [e for e in server_log() if e["ts"] >= res["t_start"] - 1]
        for k, t in enumerate(res["turns"]):
            t_next = res["turns"][k + 1]["t_sent"] if k + 1 < len(res["turns"]) else 1e18
            hits = [e for e in log if t["t_sent"] <= e["ts"] < t_next]
            t["tool_calls"] = len(hits)
            t["tool_lag_s"] = round(hits[0]["ts"] - t["t_sent"], 2) if hits else None
            t["mode"] = hits[0].get("mode") if hits else None
            t["sent_utterance"] = hits[0]["body"].get("seller_utterance") if hits else None
        out.append(res)
        for t in res["turns"]:
            print(f"[run {i}] {t['expected']:>12} | tool={t['tool_calls']} lag={t['tool_lag_s']} mode={t['mode']} "
                  f"| words={len(t['reply'].split())} | {t['reply'][:110]}")
    path = ROOT / "outputs" / f"spike-chat-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    turns = [t for r in out for t in r["turns"]]
    called = sum(1 for t in turns if t["tool_calls"] > 0)
    print(f"\nTool called on {called}/{len(turns)} seller turns (skip rate {100 * (1 - called / len(turns)):.0f}%). Saved {path.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    asyncio.run(main(ap.parse_args().runs))
