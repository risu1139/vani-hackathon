"""Mid-call push probe (T1) + live-transcript polling probe (phone OUT half).

Opens an SDK session (chat or call) on an agent, logs EVERY raw server frame (incl. the ones the SDK parser
drops), sends hand-built client actions (variable_update / state_transition / language_change) mid-session,
and polls the analytics transcript/interactions endpoints during the session to see whether an in-progress
interaction is visible from outside.

Made-up seller lines only. Usage:
  python app/spike/midcall_probe.py --mode chat --app VANI-midcal-506a41a2-0422
"""
import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

from call_spike import ROOT  # loads .env

ANALYTICS = "https://apps.sarvam.ai/api/analytics/v1/{org}/{ws}/{app}"


def hook_raw(agent, frames, t0):
    """Wrap _route_message so every raw frame is logged before the SDK parser (which drops event types)."""
    orig = agent._route_message

    async def route(message):
        typ = message.get("type", "?")
        if typ != "server.media.audio_chunk":
            frames.append({"t": round(time.time() - t0, 3), "dir": "in", "type": typ,
                           "msg": {k: v for k, v in message.items() if k not in ("audio_base64",)}})
        else:
            frames.append({"t": round(time.time() - t0, 3), "dir": "in", "type": typ})
        await orig(message)

    agent._route_message = route


async def push_raw(agent, frames, t0, payload):
    msg = {"origin": "client", "timestamp": time.time(), **payload}
    await agent._ws.send(json.dumps(msg, ensure_ascii=False))
    frames.append({"t": round(time.time() - t0, 3), "dir": "out", "type": payload["type"], "msg": msg})


def poll_analytics(app, interaction_id):
    org, ws = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
    base = ANALYTICS.format(org=org, ws=ws, app=app)
    h = {"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]}
    out = {}
    t = time.time()
    r = requests.get(f"{base}/transcripts/{interaction_id}", headers=h, timeout=10)
    out["transcript"] = {"status": r.status_code, "ms": round((time.time() - t) * 1000), "body": r.text[:600]}
    now = datetime.now(timezone.utc)
    t = time.time()
    r = requests.get(f"{base}/interactions", headers=h, timeout=10, params={
        "start_datetime": (now - timedelta(minutes=10)).isoformat(), "end_datetime": (now + timedelta(minutes=1)).isoformat(),
        "limit": 5, "sort_by": "start_datetime", "sort_order": "desc"})
    ids = []
    try:
        ids = [i.get("interaction_id") for i in r.json().get("items", [])]
    except Exception:
        pass
    out["interactions"] = {"status": r.status_code, "ms": round((time.time() - t) * 1000), "ours_listed": interaction_id in ids}
    return out


async def chat_turn(agent, replies, text, wait=12):
    replies.clear()
    agent_send = agent.send_text(text)
    if asyncio.iscoroutine(agent_send):
        await agent_send
    t0 = time.time()
    last = None
    while time.time() - t0 < wait:
        await asyncio.sleep(0.2)
        if replies and last == len(replies) and time.time() - replies[-1][0] > 1.5:
            break
        last = len(replies)
    return " ".join(t for _, t in replies)


async def main(mode, app, version):
    frames, replies, transcripts = [], [], []
    t0 = time.time()

    async def on_text(msg):
        replies.append((time.time(), msg.text))

    async def on_transcript(msg):
        transcripts.append((round(time.time() - t0, 3), str(getattr(msg.role, "value", msg.role)), msg.content))

    cfg = InteractionConfig(
        org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"], app_id=app, version=version or None,
        interaction_type=InteractionType.CHAT, user_identifier_type=UserIdentifierType.CUSTOM,
        user_identifier=f"probe-{int(time.time())}", sample_rate=16000,
        agent_variables={"seller_mode": "neutral", "persona_directive": "Continue normally."})
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              text_callback=on_text, transcript_callback=on_transcript)
    hook_raw(agent, frames, t0)
    await agent.start()
    await agent.wait_for_connect(timeout=15)
    await asyncio.sleep(4)
    iid = agent.get_interaction_id()
    res = {"interaction_id": iid, "steps": []}

    def step(name, **kw):
        res["steps"].append({"step": name, "t": round(time.time() - t0, 3), **kw})
        print(f"[{name}] " + json.dumps(kw, ensure_ascii=False)[:400])

    step("baseline", reply=await chat_turn(agent, replies, "Haan boliye, kya kaam hai?"))
    step("poll_during_call", **poll_analytics(app, iid))

    directive = "Reply in exactly 5 words and end with 'ठीक है?'"
    for key in ("agent_variables", "variables", "data"):
        await push_raw(agent, frames, t0, {"type": "client.action.variable_update",
                                           key: {"persona_directive": directive, "seller_mode": "rushed"}})
    await asyncio.sleep(1.5)
    step("after_variable_update", reply=await chat_turn(agent, replies, "Achha, aur batao, kya offer hai?"))

    for key in ("language_name", "language", "new_language"):
        await push_raw(agent, frames, t0, {"type": "client.action.language_change", key: "English"})
    await asyncio.sleep(1.5)
    step("after_language_change", reply=await chat_turn(agent, replies, "Theek hai, meeting kab hogi?"))

    for key in ("state_name", "next_state", "state"):
        await push_raw(agent, frames, t0, {"type": "client.action.state_transition", key: "start"})
    await asyncio.sleep(1.5)
    step("after_state_transition", reply=await chat_turn(agent, replies, "Kal subah das baje theek hai."))
    step("poll_during_call_2", **poll_analytics(app, iid))

    await agent.stop()
    await asyncio.sleep(3)
    step("poll_after_end", **poll_analytics(app, iid))
    res["frames"] = [f for f in frames if f["type"] != "server.media.audio_chunk"]
    res["transcripts"] = transcripts
    out = ROOT / "outputs" / "midcall_tests" / f"t1-probe-{mode}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    types = {}
    for f in frames:
        types[(f["dir"], f["type"])] = types.get((f["dir"], f["type"]), 0) + 1
    print("frame types:", types)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="chat")
    ap.add_argument("--app", default="VANI-midcal-506a41a2-0422")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args()
    asyncio.run(main(a.mode, a.app, a.version))
